from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid


class CaseLaw(Base):
    __tablename__ = "case_law"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(255), nullable=False, unique=True)
    case_title = Column(String(500), nullable=False)
    court_name = Column(String(255), nullable=False)
    case_type = Column(String(100), nullable=False)
    verdict_date = Column(DateTime, nullable=True)
    judge_name = Column(String(255), nullable=True)
    legal_articles = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ContractAnalysis(Base):
    __tablename__ = "contract_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_title = Column(String(500), nullable=False)
    contract_type = Column(String(100), nullable=False)
    parties = Column(JSON, default=list)
    content = Column(Text, nullable=True)
    analysis_result = Column(JSON, nullable=True)
    risk_score = Column(String(20), nullable=True)
    risk_level = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False)
