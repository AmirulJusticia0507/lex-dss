from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.legal import LegalArticle
from app.models.user import User
from app.engine.rag import search_similar_articles, generate_embedding

router = APIRouter()


class RAGSearchRequest(BaseModel):
    query: str
    domain: Optional[str] = Field(None, max_length=50)
    hierarchy_ids: Optional[List[int]] = None
    top_k: int = Field(5, ge=1, le=50)
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)


class RAGSearchResult(BaseModel):
    id: uuid.UUID
    document_title: str
    article_number: str
    content: str
    domain: Optional[str]
    similarity: float
    hierarchy_type: Optional[str] = None
    hierarchy_rank: Optional[int] = None


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResult]
    total_found: int


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int


@router.post("/search", response_model=RAGSearchResponse)
async def search_articles(
    request: RAGSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    results = await search_similar_articles(
        db=db,
        query=request.query,
        domain=request.domain,
        hierarchy_ids=request.hierarchy_ids,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )
    
    search_results = [
        RAGSearchResult(
            id=article.id,
            document_title=article.document_title,
            article_number=article.article_number,
            content=article.content[:500] + "..." if len(article.content) > 500 else article.content,
            domain=article.domain,
            similarity=similarity,
            hierarchy_type=article.hierarchy.type_name if article.hierarchy else None,
            hierarchy_rank=article.hierarchy.rank if article.hierarchy else None,
        )
        for article, similarity in results
    ]
    
    return RAGSearchResponse(
        query=request.query,
        results=search_results,
        total_found=len(search_results),
    )


@router.post("/embedding", response_model=EmbeddingResponse)
async def create_embedding(
    request: EmbeddingRequest,
    current_user: User = Depends(get_current_active_user),
):
    embedding = await generate_embedding(request.text)
    return EmbeddingResponse(
        embedding=embedding,
        dimension=len(embedding),
    )


@router.post("/articles/{article_id}/embedding", status_code=status.HTTP_200_OK)
async def update_article_embedding(
    article_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(LegalArticle).where(LegalArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    embedding = await generate_embedding(article.content)
    article.embedding = embedding
    await db.commit()
    
    return {"message": "Embedding updated successfully", "article_id": str(article_id)}


@router.post("/articles/batch-embeddings", status_code=status.HTTP_200_OK)
async def batch_update_embeddings(
    article_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    updated = 0
    for article_id in article_ids:
        result = await db.execute(select(LegalArticle).where(LegalArticle.id == article_id))
        article = result.scalar_one_or_none()
        if article and article.content:
            embedding = await generate_embedding(article.content)
            article.embedding = embedding
            updated += 1
    
    await db.commit()
    return {"message": f"Updated {updated} article embeddings", "updated_count": updated}