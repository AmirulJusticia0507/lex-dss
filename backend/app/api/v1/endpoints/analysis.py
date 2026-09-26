"""Endpoint Lex Integrity: analisis kontradiksi, validasi hierarki, dan graf konflik.

Rujukan: `docs/API_SPECIFICATION.md` §4.
"""

import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.legal import LegalArticle, NormConflict
from app.models.user import User
from app.services.lex_integrity_service import LexIntegrityService

router = APIRouter()

DOMAINS = ("HTN", "PIDANA", "PERDATA")
SEVERITIES = ("LOW", "MEDIUM", "HIGH")
RESOLUTION_STATUSES = ("OPEN", "REVIEWED", "RESOLVED", "DISMISSED")


# --------------------------------------------------------------------------- #
# Skema
# --------------------------------------------------------------------------- #

class HierarchyContext(BaseModel):
    draft_type: Optional[str] = Field(None, description="Jenis draf, mis. PERDA/PERPRES")
    draft_number: Optional[str] = Field(None, description="Nomor draf, mis. Perda DKI Jakarta No. 2/2025")
    draft_title: Optional[str] = Field(None, description="Judul draf yang ditampilkan")


class ConflictAnalyzeRequest(BaseModel):
    input_text: str = Field(..., min_length=10, max_length=20000)
    input_article_id: Optional[uuid.UUID] = None
    domain: str = Field("HTN")
    target_article_ids: Optional[List[uuid.UUID]] = None
    hierarchy_context: Optional[HierarchyContext] = None
    min_severity: str = Field("LOW")
    top_k: int = Field(20, ge=1, le=50)
    save_result: bool = True


class ConflictResponse(BaseModel):
    id: Optional[str] = None
    conflict_type: str
    severity: str
    description: str
    legal_basis: List[str] = []
    recommended_action: str = ""
    confidence: float = 0.0
    evidence: List[str] = []
    source: Dict
    target: Dict


class ConflictAnalyzeResponse(BaseModel):
    analysis_id: str
    domain: str
    source_article_id: str
    has_conflict: bool
    conflict_count: int
    highest_severity: Optional[str] = None
    conflicts: List[ConflictResponse]
    engine_trace: Dict
    persisted_conflict_ids: List[str] = []
    created_at: str


class NormRefRequest(BaseModel):
    type: Optional[str] = Field(None, description="Jenis norma, mis. UU/PERDA")
    document_title: str = Field(..., min_length=3, max_length=255)
    article_number: str = Field(..., min_length=1, max_length=50)


class HierarchyValidationRequest(BaseModel):
    lower_norm: NormRefRequest
    upper_norm: NormRefRequest


class ResolveConflictRequest(BaseModel):
    status: str = Field("RESOLVED")
    resolution_note: Optional[str] = Field(None, max_length=4000)
    resolved_article_id: Optional[uuid.UUID] = None


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #

def _validate_domain(domain: str) -> str:
    normalized = (domain or "").upper()
    if normalized not in DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNSUPPORTED_DOMAIN",
                "message": f"Domain '{domain}' belum memiliki rules engine aktif.",
                "details": {"supported_domains": list(DOMAINS)},
            },
        )
    return normalized


def _validate_severity(severity: str) -> str:
    normalized = (severity or "LOW").upper()
    if normalized not in SEVERITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNSUPPORTED_SEVERITY",
                "message": f"Severity '{severity}' tidak dikenal.",
                "details": {"supported": list(SEVERITIES)},
            },
        )
    return normalized


async def _resolve_norm_article(db: AsyncSession, ref: NormRefRequest) -> LegalArticle:
    statement = select(LegalArticle).where(
        LegalArticle.document_title.ilike(ref.document_title),
        LegalArticle.article_number == ref.article_number,
    )
    result = await db.execute(statement)
    article = result.scalars().first()
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Pasal '{ref.article_number}' pada '{ref.document_title}' tidak ditemukan dalam korpus.",
            },
        )
    return article


# --------------------------------------------------------------------------- #
# Endpoint
# --------------------------------------------------------------------------- #

@router.post("/conflict", response_model=ConflictAnalyzeResponse)
async def analyze_conflict(
    payload: ConflictAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Uji klausa terhadap korpus norma dan deteksi pertentangan (Lex Integrity)."""
    domain = _validate_domain(payload.domain)
    min_severity = _validate_severity(payload.min_severity)
    context = payload.hierarchy_context or HierarchyContext()

    service = LexIntegrityService(db)
    outcome = await service.analyze_text(
        text=payload.input_text,
        domain=domain,
        input_article_id=payload.input_article_id,
        draft_type=context.draft_type,
        draft_label=context.draft_number or context.draft_title,
        target_article_ids=payload.target_article_ids,
        min_severity=min_severity,
        top_k=payload.top_k,
        save_result=payload.save_result,
    )

    return ConflictAnalyzeResponse(**outcome.to_dict())


@router.post("/articles/{article_id}/analyze", response_model=ConflictAnalyzeResponse)
async def analyze_stored_article(
    article_id: uuid.UUID,
    domain: Optional[str] = Query(None),
    min_severity: str = Query("LOW"),
    top_k: int = Query(20, ge=1, le=50),
    save_result: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Jalankan analisis Lex Integrity terhadap pasal yang sudah tersimpan."""
    service = LexIntegrityService(db)
    article = await service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Pasal tidak ditemukan."})

    outcome = await service.analyze_article(
        article=article,
        domain=_validate_domain(domain) if domain else None,
        min_severity=_validate_severity(min_severity),
        top_k=top_k,
        save_result=save_result,
    )

    return ConflictAnalyzeResponse(**outcome.to_dict())


@router.post("/hierarchy")
async def validate_hierarchy(
    payload: HierarchyValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Validasi Perda/Perpres terhadap norma yang berada di atas hierarkinya."""
    lower = await _resolve_norm_article(db, payload.lower_norm)
    upper = await _resolve_norm_article(db, payload.upper_norm)

    service = LexIntegrityService(db)
    return await service.validate_hierarchy(lower=lower, upper=upper)


@router.get("/articles/{article_id}/conflicts")
async def article_conflict_graph(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Graph relasi konflik untuk satu pasal (feed Conflict Matrix)."""
    service = LexIntegrityService(db)
    article = await service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Pasal tidak ditemukan."})
    return await service.conflict_graph(article_id)


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: uuid.UUID,
    payload: ResolveConflictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "auditor")),
):
    """Tandai temuan kontradiksi sebagai ditinjau/diatasi (audit trail)."""
    resolution_status = (payload.status or "").upper()
    if resolution_status not in RESOLUTION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UNSUPPORTED_STATUS",
                "message": f"Status '{payload.status}' tidak dikenal.",
                "details": {"supported": list(RESOLUTION_STATUSES)},
            },
        )
    if resolution_status in {"RESOLVED", "DISMISSED"} and not payload.resolution_note:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "RESOLUTION_NOTE_REQUIRED",
                "message": "resolution_note wajib diisi untuk status RESOLVED/DISMISSED.",
            },
        )

    result = await db.execute(
        select(NormConflict)
        .options(
            selectinload(NormConflict.source_article),
            selectinload(NormConflict.target_article),
        )
        .where(NormConflict.id == conflict_id)
    )
    conflict = result.scalars().first()
    if not conflict:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Konflik tidak ditemukan."})

    from datetime import datetime

    conflict.status = resolution_status
    conflict.resolution_note = payload.resolution_note
    conflict.resolved_article_id = payload.resolved_article_id
    conflict.resolved_at = datetime.utcnow() if resolution_status in {"RESOLVED", "DISMISSED"} else None

    meta = dict(conflict.meta_data or {})
    meta["resolution"] = {
        "by_user_id": str(current_user.id),
        "status": resolution_status,
        "at": conflict.resolved_at.isoformat() if conflict.resolved_at else None,
    }
    conflict.meta_data = meta

    return {
        "id": str(conflict.id),
        "status": conflict.status,
        "resolution_note": conflict.resolution_note,
        "resolved_article_id": str(conflict.resolved_article_id) if conflict.resolved_article_id else None,
        "resolved_at": conflict.resolved_at.isoformat() if conflict.resolved_at else None,
    }
