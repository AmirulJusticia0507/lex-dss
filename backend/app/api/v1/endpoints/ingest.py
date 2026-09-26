from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import json

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.legal import LegalArticle, LegalHierarchy
from app.models.user import User
from app.engine.rag import generate_embedding

router = APIRouter()


class DocumentIngestRequest(BaseModel):
    document_title: str = Field(..., max_length=255)
    content: str = Field(..., min_length=10)
    domain: Optional[str] = Field(None, max_length=50)
    hierarchy_id: Optional[int] = None
    article_number: Optional[str] = Field(None, max_length=50)
    meta_data: Optional[Dict[str, Any]] = None


class DocumentIngestResponse(BaseModel):
    message: str
    articles_created: int
    article_ids: List[str]


class BatchIngestRequest(BaseModel):
    documents: List[DocumentIngestRequest]


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    request: DocumentIngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    articles_created = 0
    article_ids = []
    
    if "\n\nPasal " in request.content or "\nPasal " in request.content:
        articles = _parse_articles_from_text(request.content, request.document_title)
        for article_data in articles:
            article = LegalArticle(
                document_title=request.document_title,
                article_number=article_data["article_number"],
                content=article_data["content"],
                domain=request.domain,
                hierarchy_id=request.hierarchy_id,
                meta_data=request.meta_data,
            )
            db.add(article)
            await db.flush()
            
            embedding = await generate_embedding(article.content)
            article.embedding = embedding
            
            article_ids.append(str(article.id))
            articles_created += 1
    else:
        article_number = request.article_number or "1"
        article = LegalArticle(
            document_title=request.document_title,
            article_number=article_number,
            content=request.content,
            domain=request.domain,
            hierarchy_id=request.hierarchy_id,
            meta_data=request.meta_data,
        )
        db.add(article)
        await db.flush()
        
        embedding = await generate_embedding(article.content)
        article.embedding = embedding
        
        article_ids.append(str(article.id))
        articles_created = 1
    
    await db.commit()
    
    return DocumentIngestResponse(
        message=f"Successfully ingested {articles_created} article(s)",
        articles_created=articles_created,
        article_ids=article_ids,
    )


@router.post("/ingest/batch", response_model=DocumentIngestResponse)
async def ingest_batch(
    request: BatchIngestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    total_created = 0
    all_ids = []
    
    for doc in request.documents:
        if "\n\nPasal " in doc.content or "\nPasal " in doc.content:
            articles = _parse_articles_from_text(doc.content, doc.document_title)
            for article_data in articles:
                article = LegalArticle(
                    document_title=doc.document_title,
                    article_number=article_data["article_number"],
                    content=article_data["content"],
                    domain=doc.domain,
                    hierarchy_id=doc.hierarchy_id,
                    meta_data=doc.meta_data,
                )
                db.add(article)
                await db.flush()
                
                embedding = await generate_embedding(article.content)
                article.embedding = embedding
                
                all_ids.append(str(article.id))
                total_created += 1
        else:
            article_number = doc.article_number or "1"
            article = LegalArticle(
                document_title=doc.document_title,
                article_number=article_number,
                content=doc.content,
                domain=doc.domain,
                hierarchy_id=doc.hierarchy_id,
                meta_data=doc.meta_data,
            )
            db.add(article)
            await db.flush()
            
            embedding = await generate_embedding(article.content)
            article.embedding = embedding
            
            all_ids.append(str(article.id))
            total_created += 1
    
    await db.commit()
    
    return DocumentIngestResponse(
        message=f"Successfully batch ingested {total_created} article(s)",
        articles_created=total_created,
        article_ids=all_ids,
    )


@router.post("/ingest/file")
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_title: str = Form(...),
    domain: Optional[str] = Form(None),
    hierarchy_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    content = await file.read()
    
    try:
        if file.filename.endswith(".json"):
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                docs = [DocumentIngestRequest(**d) for d in data]
            else:
                docs = [DocumentIngestRequest(**data)]
        elif file.filename.endswith(".txt") or file.filename.endswith(".md"):
            text = content.decode("utf-8")
            docs = [DocumentIngestRequest(
                document_title=document_title,
                content=text,
                domain=domain,
                hierarchy_id=hierarchy_id,
            )]
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Use .json, .txt, or .md"
            )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")
    
    total_created = 0
    all_ids = []
    
    for doc in docs:
        if "\n\nPasal " in doc.content or "\nPasal " in doc.content:
            articles = _parse_articles_from_text(doc.content, doc.document_title)
            for article_data in articles:
                article = LegalArticle(
                    document_title=doc.document_title,
                    article_number=article_data["article_number"],
                    content=article_data["content"],
                    domain=doc.domain,
                    hierarchy_id=doc.hierarchy_id,
                    meta_data=doc.meta_data,
                )
                db.add(article)
                await db.flush()
                
                embedding = await generate_embedding(article.content)
                article.embedding = embedding
                
                all_ids.append(str(article.id))
                total_created += 1
        else:
            article_number = doc.article_number or "1"
            article = LegalArticle(
                document_title=doc.document_title,
                article_number=article_number,
                content=doc.content,
                domain=doc.domain,
                hierarchy_id=doc.hierarchy_id,
                meta_data=doc.meta_data,
            )
            db.add(article)
            await db.flush()
            
            embedding = await generate_embedding(article.content)
            article.embedding = embedding
            
            all_ids.append(str(article.id))
            total_created += 1
    
    await db.commit()
    
    return DocumentIngestResponse(
        message=f"Successfully ingested {total_created} article(s) from file",
        articles_created=total_created,
        article_ids=all_ids,
    )


def _parse_articles_from_text(content: str, document_title: str) -> List[Dict[str, str]]:
    articles = []
    lines = content.split("\n")
    
    current_article = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.lower().startswith("pasal "):
            if current_article is not None:
                articles.append({
                    "article_number": current_article,
                    "content": "\n".join(current_content).strip(),
                })
            current_article = line_stripped
            current_content = [line]
        else:
            if current_article is not None:
                current_content.append(line)
    
    if current_article is not None:
        articles.append({
            "article_number": current_article,
            "content": "\n".join(current_content).strip(),
        })
    
    if not articles:
        articles.append({
            "article_number": "1",
            "content": content.strip(),
        })
    
    return articles


@router.post("/embeddings/update/{article_id}")
async def update_single_embedding(
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
    
    return {"message": "Embedding updated", "article_id": str(article_id)}


@router.post("/embeddings/update-batch")
async def update_batch_embeddings(
    article_ids: List[uuid.UUID],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    updated = 0
    for aid in article_ids:
        result = await db.execute(select(LegalArticle).where(LegalArticle.id == aid))
        article = result.scalar_one_or_none()
        if article and article.content:
            embedding = await generate_embedding(article.content)
            article.embedding = embedding
            updated += 1
    
    await db.commit()
    return {"message": f"Updated {updated} embeddings", "updated_count": updated}