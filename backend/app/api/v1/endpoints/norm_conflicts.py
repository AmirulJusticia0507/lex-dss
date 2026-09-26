from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.legal import NormConflict, LegalArticle
from app.models.user import User

router = APIRouter()


class NormConflictCreate(BaseModel):
    source_article_id: uuid.UUID
    target_article_id: uuid.UUID
    conflict_type: str = Field(..., pattern="^(LEX_SUPERIOR|LEX_SPECIALIS|LEX_POSTERIOR|DIRECT_CONTRADICTION)$")
    severity: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")
    description: str
    meta_data: Optional[dict] = None


class NormConflictResponse(BaseModel):
    id: uuid.UUID
    source_article_id: uuid.UUID
    target_article_id: uuid.UUID
    conflict_type: str
    severity: str
    description: str
    meta_data: Optional[dict]
    created_at: str
    source_article: Optional[dict] = None
    target_article: Optional[dict] = None
    
    class Config:
        from_attributes = True


class NormConflictList(BaseModel):
    items: List[NormConflictResponse]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=NormConflictResponse, status_code=status.HTTP_201_CREATED)
async def create_conflict(
    conflict_in: NormConflictCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    source_result = await db.execute(select(LegalArticle).where(LegalArticle.id == conflict_in.source_article_id))
    source_article = source_result.scalar_one_or_none()
    if not source_article:
        raise HTTPException(status_code=404, detail="Source article not found")
    
    target_result = await db.execute(select(LegalArticle).where(LegalArticle.id == conflict_in.target_article_id))
    target_article = target_result.scalar_one_or_none()
    if not target_article:
        raise HTTPException(status_code=404, detail="Target article not found")
    
    conflict = NormConflict(**conflict_in.model_dump())
    db.add(conflict)
    await db.commit()
    await db.refresh(conflict)
    
    conflict_response = NormConflictResponse.model_validate(conflict)
    conflict_response.source_article = {
        "id": str(source_article.id),
        "document_title": source_article.document_title,
        "article_number": source_article.article_number,
    }
    conflict_response.target_article = {
        "id": str(target_article.id),
        "document_title": target_article.document_title,
        "article_number": target_article.article_number,
    }
    return conflict_response


@router.get("/", response_model=NormConflictList)
async def list_conflicts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conflict_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    source_article_id: Optional[uuid.UUID] = Query(None),
    target_article_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(NormConflict).options(
        selectinload(NormConflict.source_article),
        selectinload(NormConflict.target_article),
    )
    
    if conflict_type:
        query = query.where(NormConflict.conflict_type == conflict_type)
    if severity:
        query = query.where(NormConflict.severity == severity)
    if source_article_id:
        query = query.where(NormConflict.source_article_id == source_article_id)
    if target_article_id:
        query = query.where(NormConflict.target_article_id == target_article_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(NormConflict.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return NormConflictList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{conflict_id}", response_model=NormConflictResponse)
async def get_conflict(
    conflict_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(NormConflict)
        .options(
            selectinload(NormConflict.source_article),
            selectinload(NormConflict.target_article),
        )
        .where(NormConflict.id == conflict_id)
    )
    conflict = result.scalar_one_or_none()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    return conflict


@router.delete("/{conflict_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conflict(
    conflict_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(NormConflict).where(NormConflict.id == conflict_id))
    conflict = result.scalar_one_or_none()
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    await db.delete(conflict)
    await db.commit()