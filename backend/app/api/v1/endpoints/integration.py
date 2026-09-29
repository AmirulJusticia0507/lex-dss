import secrets
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.analysis import (
    ConflictAnalyzeRequest,
    ConflictAnalyzeResponse,
    _validate_domain,
    _validate_severity,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.legal import LegalArticle, LegalHierarchy
from app.models.user import User
from app.services.lex_integrity_client import LexIntegrityClient
from app.services.lex_integrity_service import LexIntegrityService

router = APIRouter()


@router.get("/sources")
async def external_source_status(
    current_user: User = Depends(require_roles("admin")),
):
    """Show readiness without ever returning integration credentials."""
    sources = {
        "sipp": (settings.SIPP_API_BASE_URL, settings.SIPP_API_KEY),
        "jdihn_bphn": (settings.JDIHN_API_BASE_URL, settings.JDIHN_API_KEY),
        "oss": (settings.OSS_API_BASE_URL, settings.OSS_API_CLIENT_ID, settings.OSS_API_CLIENT_SECRET),
        "djp": (settings.DJP_API_BASE_URL, settings.DJP_API_CLIENT_ID, settings.DJP_API_CLIENT_SECRET),
        "kemenperin": (settings.KEMENPERIN_API_BASE_URL, settings.KEMENPERIN_API_KEY),
        "dpr": (settings.DPR_API_BASE_URL, settings.DPR_API_KEY),
    }
    return {
        "sources": [
            {"name": name, "configured": all(values), "missing": sum(value is None or value == "" for value in values)}
            for name, values in sources.items()
        ]
    }


class DelegateRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=20000)
    max_hops: int = Field(4, ge=1, le=6)


class SyncRequest(BaseModel):
    max_pages: int = Field(20, ge=1, le=100)
    page_size: int = Field(100, ge=1, le=500)


def require_internal_key(x_internal_api_key: Optional[str] = Header(None)) -> None:
    expected = settings.INTERNAL_API_KEY or ""
    if not expected or not x_internal_api_key or not secrets.compare_digest(x_internal_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid internal API key")


def infer_domain(rule: dict) -> str:
    text = f"{rule.get('category', '')} {rule.get('title', '')}".lower()
    if any(value in text for value in ("pidana", "kuhp", "kuhap")):
        return "PIDANA"
    if any(value in text for value in ("perdata", "kuhper", "perjanjian")):
        return "PERDATA"
    return "HTN"


def infer_hierarchy(rule: dict) -> str:
    text = f"{rule.get('category', '')} {rule.get('rule_code', '')}".upper()
    for hierarchy in ("PERWALI", "PERBUP", "PERDA", "PERMEN", "PERPRES", "PERPPU", "TAP MPR", "UUD 1945", "PP", "UU"):
        if hierarchy in text:
            return hierarchy
    return "UU"


@router.post("/delegate")
async def delegate_to_lex_integrity(
    payload: DelegateRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await LexIntegrityClient().analyze(payload.query, payload.max_hops)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Lex Integrity unavailable: {exc}") from exc


@router.post("/sync", dependencies=[Depends(require_internal_key)])
async def sync_lex_integrity_rules(
    payload: SyncRequest,
    db: AsyncSession = Depends(get_db),
):
    hierarchy_rows = (await db.execute(select(LegalHierarchy))).scalars().all()
    hierarchies = {row.type_name: row.id for row in hierarchy_rows}
    created = updated = unchanged = fetched = 0
    client = LexIntegrityClient()

    try:
        for page in range(1, payload.max_pages + 1):
            response = await client.rules(page, payload.page_size)
            rules = response.get("data") or []
            if not rules:
                break
            fetched += len(rules)

            for rule in rules:
                rule_code = str(rule.get("rule_code") or rule.get("id"))
                title = f"{rule_code} - {rule.get('title') or 'Peraturan'}"[:255]
                result = await db.execute(
                    select(LegalArticle).where(
                        LegalArticle.document_title == title,
                        LegalArticle.article_number == "NASKAH",
                    )
                )
                article = result.scalars().first()
                values = {
                    "content": rule.get("content") or title,
                    "domain": infer_domain(rule),
                    "hierarchy_id": hierarchies.get(infer_hierarchy(rule)),
                    "meta_data": {
                        "source": "lex-integrity",
                        "external_id": rule.get("id"),
                        "rule_code": rule_code,
                        "source_url": rule.get("source_url"),
                        "publish_date": rule.get("publish_date"),
                        "synced": True,
                    },
                }
                if article is None:
                    db.add(LegalArticle(document_title=title, article_number="NASKAH", **values))
                    created += 1
                elif any(getattr(article, key) != value for key, value in values.items()):
                    content_changed = article.content != values["content"]
                    for key, value in values.items():
                        setattr(article, key, value)
                    if content_changed:
                        article.embedding = None
                    updated += 1
                else:
                    unchanged += 1

            if page >= int(response.get("pagination", {}).get("pages", page)):
                break
        await db.commit()
    except httpx.HTTPError as exc:
        await db.rollback()
        raise HTTPException(status_code=502, detail=f"Lex Integrity unavailable: {exc}") from exc

    return {"fetched": fetched, "created": created, "updated": updated, "unchanged": unchanged}


@router.post("/conflict", response_model=ConflictAnalyzeResponse, dependencies=[Depends(require_internal_key)])
async def internal_conflict_analysis(
    payload: ConflictAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    outcome = await LexIntegrityService(db).analyze_text(
        text=payload.input_text,
        domain=_validate_domain(payload.domain),
        input_article_id=payload.input_article_id,
        draft_type=payload.hierarchy_context.draft_type if payload.hierarchy_context else None,
        draft_label=(payload.hierarchy_context.draft_number or payload.hierarchy_context.draft_title) if payload.hierarchy_context else None,
        target_article_ids=payload.target_article_ids,
        min_severity=_validate_severity(payload.min_severity),
        top_k=payload.top_k,
        save_result=payload.save_result,
    )
    return ConflictAnalyzeResponse(**outcome.to_dict())
