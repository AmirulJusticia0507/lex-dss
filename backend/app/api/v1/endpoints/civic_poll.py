from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user, require_roles
from app.models.civic_poll import CivicPollEvent, CivicPollResult
from app.models.user import User
from app.services.civic_poll_client import (
    CivicPollClient,
    CivicPollError,
    build_envelope,
    canonical_body,
    content_fingerprint,
    normalize_aggregate,
    payload_hash,
)
from app.services.transcript import parse_transcript

router = APIRouter()


@router.post("/transcripts/preview")
async def preview_transcript(
    file: UploadFile = File(...),
    source_url: str = Form(""),
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    filename = file.filename or ""
    if not filename.lower().endswith((".txt", ".srt", ".vtt")):
        raise HTTPException(status_code=400, detail="Gunakan berkas TXT, SRT, atau VTT")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ukuran transkrip maksimal 5 MB")
    try:
        segments = parse_transcript(content.decode("utf-8-sig"), filename)
    except (UnicodeDecodeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "filename": filename,
        "source_url": source_url or None,
        "segment_count": len(segments),
        "duration_seconds": segments[-1]["end_seconds"],
        "segments": segments,
    }


class PollOptionInput(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    label: str = Field(..., min_length=1, max_length=200)


class PollDraftRequest(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=100)
    question: str = Field(..., min_length=1, max_length=200)
    options: List[PollOptionInput] = Field(..., min_length=2)
    description: str = ""
    disclaimer: str = ""
    region_code: str = Field("", max_length=20)
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None
    legal_audit: Optional[Dict[str, Any]] = None
    source: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_window(self):
        if self.opens_at and self.closes_at and self.closes_at <= self.opens_at:
            raise ValueError("closes_at harus setelah opens_at")
        return self


class CivicPollEventResponse(BaseModel):
    event_id: str
    question: str
    status: str
    revision: int
    remote_topic_id: Optional[int]
    region_code: Optional[str]
    opens_at: Optional[datetime]
    closes_at: Optional[datetime]
    options: Optional[list]
    legal_audit: Optional[dict]
    submitted_at: datetime

    class Config:
        from_attributes = True


class CivicPollResultResponse(BaseModel):
    event_id: str
    revision: int
    status: str
    total_responses: int
    total_registered: Optional[int]
    participation_percent: Optional[float]
    options: Optional[list]
    evidence_root: Optional[str]
    voided: bool
    correction_reason: Optional[str]
    superseded_by_event_id: Optional[str]
    source_updated_at: Optional[str]
    collected_at: datetime

    class Config:
        from_attributes = True


class CollectResponse(BaseModel):
    event_id: str
    stored_revision: int
    stored: bool
    status: str
    total_responses: int
    participation_percent: Optional[float]
    voided: bool
    message: str


def _content_hash(snapshot: Dict[str, Any]) -> str:
    """Hash isi agregat supaya snapshot identik tidak menambah histori."""
    return payload_hash(canonical_body(snapshot))


async def _get_event(event_id: str, db: AsyncSession) -> CivicPollEvent:
    event = await db.scalar(select(CivicPollEvent).where(CivicPollEvent.event_id == event_id))
    if event is None:
        raise HTTPException(status_code=404, detail="Civic poll event not found")
    return event


def _latest_result(event_id: str, db: AsyncSession):
    return db.scalar(
        select(CivicPollResult)
        .where(CivicPollResult.event_id == event_id)
        .order_by(CivicPollResult.revision.desc())
        .limit(1)
    )


@router.post("/drafts", response_model=CivicPollEventResponse, status_code=201)
async def submit_civic_poll_draft(
    payload: PollDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Kirim polling publik ke E-Netizen sebagai draf yang menunggu review.

    Idempoten terhadap ``event_id``: mengirim ulang draf yang identik tidak
    membuat duplikat, sedangkan draf yang berubah isinya ditolak agar
    koreksi lewat jalur yang tercatat, bukan diam-diam menimpa.
    """
    envelope = build_envelope(
        event_id=payload.event_id,
        question=payload.question,
        options=[item.model_dump() for item in payload.options],
        legal_audit=payload.legal_audit,
        source=payload.source,
        description=payload.description,
        disclaimer=payload.disclaimer,
        region_code=payload.region_code,
        opens_at=payload.opens_at,
        closes_at=payload.closes_at,
    )
    digest = content_fingerprint(envelope)

    event = await db.scalar(
        select(CivicPollEvent).where(CivicPollEvent.event_id == payload.event_id)
    )
    if event is not None:
        if event.payload_hash == digest:
            return CivicPollEventResponse.model_validate(event)
        raise HTTPException(
            status_code=409,
            detail=(
                "Draf dengan event_id ini sudah terkirim dengan isi berbeda. "
                "Kirim koreksi sebagai event_id baru agar histori tetap dapat diaudit."
            ),
        )

    client = CivicPollClient()
    try:
        remote = await client.submit_draft(envelope)
    except CivicPollError as error:
        raise HTTPException(
            status_code=502, detail=f"Gagal mengirim draf ke E-Netizen: {error}"
        ) from error

    poll_draft = envelope["poll_draft"]
    event = CivicPollEvent(
        event_id=payload.event_id,
        question=payload.question,
        payload_hash=digest,
        revision=1,
        status=remote["status"],
        remote_topic_id=remote["remote_topic_id"],
        region_code=payload.region_code or None,
        opens_at=payload.opens_at,
        closes_at=payload.closes_at,
        options=poll_draft["options"],
        legal_audit=envelope.get("legal_audit"),
        source=envelope.get("source"),
        submitted_by_id=current_user.id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return CivicPollEventResponse.model_validate(event)


@router.post("/events/{event_id}/collect", response_model=CollectResponse)
async def collect_civic_poll_aggregate(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Tarik agregat suara publik dari E-Netizen dan simpan sebagai snapshot.

    Snapshot bersifat append-only: agregat yang isinya tidak berubah tidak
    menambah histori, sedangkan koreksi hasil di sisi E-Netizen otomatis
    terekam sebagai revisi baru.
    """
    event = await _get_event(event_id, db)
    if event.remote_topic_id is None:
        raise HTTPException(
            status_code=409, detail="Polling belum pernah berhasil dikirim ke E-Netizen"
        )

    client = CivicPollClient()
    try:
        raw = await client.fetch_aggregate(event.remote_topic_id)
        snapshot = normalize_aggregate(raw, event_id)
    except CivicPollError as error:
        status_code = 404 if error.status_code == 404 else 502
        raise HTTPException(status_code=status_code, detail=str(error)) from error

    digest = _content_hash(
        {
            "status": snapshot["status"],
            "total_responses": snapshot["total_responses"],
            "total_registered": snapshot["total_registered"],
            "options": snapshot["options"],
            "evidence_root": snapshot["evidence_root"],
            "voided": snapshot["voided"],
        }
    )

    latest = await _latest_result(event_id, db)
    if latest is not None and latest.content_hash == digest:
        return CollectResponse(
            event_id=event_id,
            stored_revision=latest.revision,
            stored=False,
            status=latest.status,
            total_responses=latest.total_responses,
            participation_percent=latest.participation_percent,
            voided=latest.voided,
            message="Agregat tidak berubah sejak penarikan terakhir.",
        )

    revision = (latest.revision + 1) if latest is not None else 1
    result = CivicPollResult(
        event_id=event_id,
        revision=revision,
        status=snapshot["status"],
        total_responses=snapshot["total_responses"],
        total_registered=snapshot["total_registered"],
        participation_percent=snapshot["participation_percent"],
        options=snapshot["options"],
        evidence_root=snapshot["evidence_root"],
        voided=snapshot["voided"],
        correction_reason=snapshot["correction_reason"],
        superseded_by_event_id=snapshot["superseded_by_event_id"],
        content_hash=digest,
        source_updated_at=snapshot["source_updated_at"],
    )
    db.add(result)
    event.status = snapshot["status"]
    await db.commit()
    await db.refresh(result)

    return CollectResponse(
        event_id=event_id,
        stored_revision=result.revision,
        stored=True,
        status=result.status,
        total_responses=result.total_responses,
        participation_percent=result.participation_percent,
        voided=result.voided,
        message=f"Agregat disimpan sebagai revisi {result.revision}.",
    )


@router.get("/events", response_model=List[CivicPollEventResponse])
async def list_civic_poll_events(
    status: Optional[str] = Query(None, max_length=20),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(CivicPollEvent)
    if status:
        query = query.where(CivicPollEvent.status == status.lower())
    items = (
        (
            await db.execute(
                query.order_by(CivicPollEvent.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )
    return [CivicPollEventResponse.model_validate(item) for item in items]


@router.get("/events/{event_id}", response_model=CivicPollEventResponse)
async def get_civic_poll_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return CivicPollEventResponse.model_validate(await _get_event(event_id, db))


@router.get("/events/{event_id}/results", response_model=List[CivicPollResultResponse])
async def list_civic_poll_results(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _get_event(event_id, db)
    results = (
        (
            await db.execute(
                select(CivicPollResult)
                .where(CivicPollResult.event_id == event_id)
                .order_by(CivicPollResult.revision.desc())
            )
        )
        .scalars()
        .all()
    )
    return [CivicPollResultResponse.model_validate(item) for item in results]


@router.get("/results/latest")
async def latest_civic_poll_results(
    limit: int = Query(20, ge=1, le=100),
    include_voided: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Agregat terbaru per polling untuk dipakai sebagai bobot suara publik.

    Setiap item diberi ``evidence_grade`` agar DSS bisa membedakan polling
    yang punya bukti integritas dan sampel memadai dari polling yang
    sekadar berisi angka mentah tanpa jejak verifikasi.
    """
    latest_ids = (
        select(CivicPollResult.event_id, func.max(CivicPollResult.revision).label("revision"))
        .group_by(CivicPollResult.event_id)
        .subquery()
    )
    query = select(CivicPollResult).join(
        latest_ids,
        (CivicPollResult.event_id == latest_ids.c.event_id)
        & (CivicPollResult.revision == latest_ids.c.revision),
    )
    if not include_voided:
        query = query.where(CivicPollResult.voided.is_(False))
    results = (
        (await db.execute(query.order_by(CivicPollResult.collected_at.desc()).limit(limit)))
        .scalars()
        .all()
    )

    return {
        "total": len(results),
        "items": [
            {
                **CivicPollResultResponse.model_validate(item).model_dump(mode="json"),
                "evidence_grade": _evidence_grade(item),
            }
            for item in results
        ],
    }


def _evidence_grade(result: CivicPollResult) -> str:
    if result.voided:
        return "VOIDED"
    if not result.evidence_root:
        return "UNVERIFIED"
    if result.participation_percent is None:
        return "PARTIAL"
    if result.participation_percent < 5:
        return "LOW_PARTICIPATION"
    return "VERIFIED"
