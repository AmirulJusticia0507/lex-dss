from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.legal import LegalHierarchy, LegalArticle
from app.models.user import User

router = APIRouter()


class LegalHierarchyCreate(BaseModel):
    type_name: str = Field(..., max_length=50)
    rank: int
    description: Optional[str] = None


class LegalHierarchyResponse(BaseModel):
    id: int
    type_name: str
    rank: int
    description: Optional[str]
    
    class Config:
        from_attributes = True


class LegalArticleCreate(BaseModel):
    document_title: str = Field(..., max_length=255)
    article_number: str = Field(..., max_length=50)
    content: str
    domain: Optional[str] = Field(None, max_length=50)
    hierarchy_id: Optional[int] = None
    meta_data: Optional[dict] = None


class LegalArticleUpdate(BaseModel):
    document_title: Optional[str] = Field(None, max_length=255)
    article_number: Optional[str] = Field(None, max_length=50)
    content: Optional[str] = None
    domain: Optional[str] = Field(None, max_length=50)
    hierarchy_id: Optional[int] = None
    meta_data: Optional[dict] = None


class LegalArticleResponse(BaseModel):
    id: uuid.UUID
    document_title: str
    article_number: str
    content: str
    domain: Optional[str]
    hierarchy_id: Optional[int]
    hierarchy: Optional[LegalHierarchyResponse]
    meta_data: Optional[dict]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class LegalArticleList(BaseModel):
    items: List[LegalArticleResponse]
    total: int
    page: int
    page_size: int


@router.post("/hierarchy", response_model=LegalHierarchyResponse, status_code=status.HTTP_201_CREATED)
async def create_hierarchy(
    hierarchy_in: LegalHierarchyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    hierarchy = LegalHierarchy(**hierarchy_in.model_dump())
    db.add(hierarchy)
    await db.commit()
    await db.refresh(hierarchy)
    return hierarchy


@router.get("/hierarchy", response_model=List[LegalHierarchyResponse])
async def list_hierarchy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(LegalHierarchy).order_by(LegalHierarchy.rank))
    return result.scalars().all()


@router.post("/", response_model=LegalArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    article_in: LegalArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    article = LegalArticle(**article_in.model_dump())
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article


@router.get("/", response_model=LegalArticleList)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[str] = Query(None),
    hierarchy_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(LegalArticle).options(selectinload(LegalArticle.hierarchy))
    
    if domain:
        query = query.where(LegalArticle.domain == domain)
    if hierarchy_id:
        query = query.where(LegalArticle.hierarchy_id == hierarchy_id)
    if search:
        query = query.where(
            LegalArticle.document_title.ilike(f"%{search}%") |
            LegalArticle.content.ilike(f"%{search}%")
        )
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(LegalArticle.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return LegalArticleList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{article_id}", response_model=LegalArticleResponse)
async def get_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(LegalArticle)
        .options(selectinload(LegalArticle.hierarchy))
        .where(LegalArticle.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=LegalArticleResponse)
async def update_article(
    article_id: uuid.UUID,
    article_in: LegalArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(LegalArticle).where(LegalArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    update_data = article_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)
    
    await db.commit()
    await db.refresh(article)
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(LegalArticle).where(LegalArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    await db.delete(article)
    await db.commit()