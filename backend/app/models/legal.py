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
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class LegalHierarchy(Base):
    __tablename__ = "legal_hierarchy"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    articles: Mapped[List["LegalArticle"]] = relationship("LegalArticle", back_populates="hierarchy")
    
    def __repr__(self):
        return f"<LegalHierarchy(type_name='{self.type_name}', rank={self.rank})>"


class LegalArticle(Base):
    __tablename__ = "legal_articles"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_title: Mapped[str] = mapped_column(String(255), nullable=False)
    article_number: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hierarchy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("legal_hierarchy.id"), nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    hierarchy: Mapped[Optional["LegalHierarchy"]] = relationship("LegalHierarchy", back_populates="articles")
    source_conflicts: Mapped[List["NormConflict"]] = relationship("NormConflict", foreign_keys="NormConflict.source_article_id", back_populates="source_article")
    target_conflicts: Mapped[List["NormConflict"]] = relationship("NormConflict", foreign_keys="NormConflict.target_article_id", back_populates="target_article")
    
    __table_args__ = (
        Index("ix_legal_articles_domain", "domain"),
        Index("ix_legal_articles_hierarchy_id", "hierarchy_id"),
        Index("ix_legal_articles_document_title", "document_title"),
    )
    
    def __repr__(self):
        return f"<LegalArticle(document_title='{self.document_title}', article_number='{self.article_number}')>"


class NormConflict(Base):
    __tablename__ = "norm_conflicts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_article_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("legal_articles.id"), nullable=False)
    target_article_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("legal_articles.id"), nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_article_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("legal_articles.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    source_article: Mapped["LegalArticle"] = relationship("LegalArticle", foreign_keys=[source_article_id], back_populates="source_conflicts")
    target_article: Mapped["LegalArticle"] = relationship("LegalArticle", foreign_keys=[target_article_id], back_populates="target_conflicts")
    resolved_article: Mapped[Optional["LegalArticle"]] = relationship("LegalArticle", foreign_keys=[resolved_article_id])
    
    __table_args__ = (
        Index("ix_norm_conflicts_source", "source_article_id"),
        Index("ix_norm_conflicts_target", "target_article_id"),
        Index("ix_norm_conflicts_type", "conflict_type"),
        Index("ix_norm_conflicts_severity", "severity"),
        Index("ix_norm_conflicts_status", "status"),
    )
    
    def __repr__(self):
        return f"<NormConflict(type='{self.conflict_type}', severity='{self.severity}')>"
