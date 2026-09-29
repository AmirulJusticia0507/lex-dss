import uuid
from datetime import datetime
from typing import Optional

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
    remote_topic_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    region_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    opens_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closes_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    options: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    legal_audit: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    source: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    submitted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    total_registered: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    participation_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    options: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    evidence_root: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    voided: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    correction_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    superseded_by_event_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_updated_at: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("event_id", "revision", name="uq_civic_poll_results_event_revision"),
        Index("idx_civic_poll_results_event", "event_id"),
        Index("idx_civic_poll_results_collected", "collected_at"),
    )

    def __repr__(self):
        return f"<CivicPollResult(event_id='{self.event_id}', revision={self.revision}, responses={self.total_responses})>"
