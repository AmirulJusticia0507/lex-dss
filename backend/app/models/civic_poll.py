import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CivicPollEvent(Base):
    """Satu polling publik yang Lex-DSS kirim ke E-Netizen.

    ``event_id`` adalah idempotency key yang sama dengan
    ``Topic.external_event_id`` di sisi E-Netizen, jadi kedua sistem bisa
    mengkorelasikan diri tanpa bergantung pada integer primary key lokal.
    """

    __tablename__ = "civic_poll_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    question: Mapped[str] = mapped_column(String(200), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    remote_topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    opens_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closes_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    legal_audit: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    submitted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_civic_poll_events_status", "status"),
        Index("idx_civic_poll_events_remote_topic", "remote_topic_id"),
    )

    def __repr__(self):
        return f"<CivicPollEvent(event_id='{self.event_id}', status='{self.status}', revision={self.revision})>"


class CivicPollResult(Base):
    """Satu snapshot agregat hasil polling publik yang ditarik dari E-Netizen.

    Baris tidak pernah di-update: setiap perubahan substantif menghasilkan
    ``revision`` baru sehingga histori bobot suara publik tetap dapat diaudit.
    """

    __tablename__ = "civic_poll_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    total_responses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_registered: Mapped[int | None] = mapped_column(Integer, nullable=True)
    participation_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    evidence_root: Mapped[str | None] = mapped_column(String(128), nullable=True)
    voided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    superseded_by_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_updated_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("event_id", "revision", name="uq_civic_poll_results_event_revision"),
        Index("idx_civic_poll_results_event", "event_id"),
        Index("idx_civic_poll_results_collected", "collected_at"),
    )

    def __repr__(self):
        return f"<CivicPollResult(event_id='{self.event_id}', revision={self.revision}, responses={self.total_responses})>"


class CivicTranscriptCandidate(Base):
    """Potongan transkrip yang menunggu keputusan moderator."""

    __tablename__ = "civic_transcript_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    candidate_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    end_seconds: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    moderator_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    promoted_event_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_civic_transcript_candidates_status", "status"),
        Index("idx_civic_transcript_candidates_created", "created_at"),
    )


class CivicTranscriptionJob(Base):
    """Durable status and output for one batch STT upload."""

    __tablename__ = "civic_transcription_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="id")
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    segments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_civic_transcription_jobs_status", "status"),
        Index("idx_civic_transcription_jobs_created", "created_at"),
    )
