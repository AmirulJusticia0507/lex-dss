import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    Boolean,
    JSON,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DecisionAuditLog(Base):
    __tablename__ = "decision_audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_title: Mapped[str] = mapped_column(String(255), nullable=False)
    ai_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    ai_risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    human_decision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deviated: Mapped[bool] = mapped_column(Boolean, default=False)
    deviation_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_audit_deviated", "is_deviated"),
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<DecisionAuditLog(case_title='{self.case_title}', is_deviated={self.is_deviated})>"


class JudicialDeviationReport(Base):
    __tablename__ = "judicial_deviation_reports"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verdict_number: Mapped[str] = mapped_column(String(100), nullable=False)
    court_name: Mapped[str] = mapped_column(String(150), nullable=False)
    judge_panel: Mapped[dict] = mapped_column(JSONB, nullable=False)
    hierarchy_violation_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    precedent_anomaly_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    evidence_gap_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    procedural_flaw_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    total_deviation_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    anomaly_summary: Mapped[str] = mapped_column(Text, nullable=False)
    flagged_for_ky: Mapped[bool] = mapped_column(Boolean, default=False)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_deviation_risk", "risk_level", "flagged_for_ky"),
        Index("idx_deviation_verdict", "verdict_number"),
        Index("idx_deviation_court", "court_name"),
        Index("idx_deviation_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<JudicialDeviationReport(verdict='{self.verdict_number}', risk='{self.risk_level}', score={self.total_deviation_score})>"