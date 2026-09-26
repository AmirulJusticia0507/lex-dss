from typing import List, Tuple, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pgvector.sqlalchemy import Vector
import openai
from app.core.config import settings
from app.models.legal import LegalArticle, LegalHierarchy


async def generate_embedding(text: str) -> List[float]:
    if not settings.OPENAI_API_KEY:
        return [0.0] * settings.EMBEDDING_DIMENSION
    
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text[:8000],
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [0.0] * settings.EMBEDDING_DIMENSION


async def search_similar_articles(
    db: AsyncSession,
    query: str,
    domain: Optional[str] = None,
    hierarchy_ids: Optional[List[int]] = None,
    top_k: int = 5,
    similarity_threshold: float = 0.7,
) -> List[Tuple[LegalArticle, float]]:
    query_embedding = await generate_embedding(query)
    
    if all(v == 0.0 for v in query_embedding):
        return []
    
    stmt = (
        select(LegalArticle, LegalHierarchy)
        .outerjoin(LegalHierarchy, LegalArticle.hierarchy_id == LegalHierarchy.id)
        .where(LegalArticle.embedding.is_not(None))
    )
    
    if domain:
        stmt = stmt.where(LegalArticle.domain == domain)
    
    if hierarchy_ids:
        stmt = stmt.where(LegalHierarchy.id.in_(hierarchy_ids))
    
    result = await db.execute(stmt)
    articles_with_hierarchy = result.all()
    
    if not articles_with_hierarchy:
        return []
    
    similarities = []
    for article, hierarchy in articles_with_hierarchy:
        if article.embedding:
            similarity = cosine_similarity(query_embedding, article.embedding)
            if similarity >= similarity_threshold:
                similarities.append((article, similarity, hierarchy))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return [(article, sim) for article, sim, _ in similarities[:top_k]]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    import math
    
    if len(vec_a) != len(vec_b):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


async def search_articles_pgvector(
    db: AsyncSession,
    query_embedding: List[float],
    domain: Optional[str] = None,
    hierarchy_ids: Optional[List[int]] = None,
    top_k: int = 5,
) -> List[Tuple[LegalArticle, float]]:
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    query = text("""
        SELECT la.*, lh.type_name, lh.rank,
               1 - (la.embedding <=> :embedding) as similarity
        FROM legal_articles la
        LEFT JOIN legal_hierarchy lh ON la.hierarchy_id = lh.id
        WHERE la.embedding IS NOT NULL
    """)
    
    params = {"embedding": embedding_str}
    
    if domain:
        query = text(str(query) + " AND la.domain = :domain")
        params["domain"] = domain
    
    if hierarchy_ids:
        query = text(str(query) + " AND lh.id IN :hierarchy_ids")
        params["hierarchy_ids"] = tuple(hierarchy_ids)
    
    query = text(str(query) + " ORDER BY similarity DESC LIMIT :top_k")
    params["top_k"] = top_k
    
    result = await db.execute(query, params)
    rows = result.mappings().all()
    
    results = []
    for row in rows:
        article = LegalArticle(
            id=row["id"],
            document_title=row["document_title"],
            article_number=row["article_number"],
            content=row["content"],
            domain=row["domain"],
            hierarchy_id=row["hierarchy_id"],
            embedding=row["embedding"],
            meta_data=row["meta_data"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        results.append((article, row["similarity"]))
    
    return results


async def hybrid_search(
    db: AsyncSession,
    query: str,
    domain: Optional[str] = None,
    hierarchy_ids: Optional[List[int]] = None,
    top_k: int = 10,
    alpha: float = 0.5,
) -> List[Tuple[LegalArticle, float]]:
    vector_results = await search_similar_articles(
        db=db,
        query=query,
        domain=domain,
        hierarchy_ids=hierarchy_ids,
        top_k=top_k * 2,
        similarity_threshold=0.0,
    )
    
    keyword_results = await keyword_search(
        db=db,
        query=query,
        domain=domain,
        hierarchy_ids=hierarchy_ids,
        top_k=top_k * 2,
    )
    
    combined_scores = {}
    
    for article, score in vector_results:
        combined_scores[article.id] = combined_scores.get(article.id, 0) + alpha * score
    
    for article, score in keyword_results:
        combined_scores[article.id] = combined_scores.get(article.id, 0) + (1 - alpha) * score
    
    sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
    
    final_results = []
    for article_id in sorted_ids[:top_k]:
        for article, score in vector_results:
            if article.id == article_id:
                final_results.append((article, combined_scores[article_id]))
                break
        else:
            for article, score in keyword_results:
                if article.id == article_id:
                    final_results.append((article, combined_scores[article_id]))
                    break
    
    return final_results


async def keyword_search(
    db: AsyncSession,
    query: str,
    domain: Optional[str] = None,
    hierarchy_ids: Optional[List[int]] = None,
    top_k: int = 5,
) -> List[Tuple[LegalArticle, float]]:
    keywords = query.lower().split()
    
    stmt = (
        select(LegalArticle, LegalHierarchy)
        .outerjoin(LegalHierarchy, LegalArticle.hierarchy_id == LegalHierarchy.id)
    )
    
    conditions = []
    for keyword in keywords:
        if len(keyword) > 2:
            conditions.append(LegalArticle.content.ilike(f"%{keyword}%"))
    
    if conditions:
        from sqlalchemy import or_
        stmt = stmt.where(or_(*conditions))
    
    if domain:
        stmt = stmt.where(LegalArticle.domain == domain)
    
    if hierarchy_ids:
        stmt = stmt.where(LegalHierarchy.id.in_(hierarchy_ids))
    
    stmt = stmt.limit(top_k)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    scored_results = []
    for article, hierarchy in rows:
        score = sum(1 for kw in keywords if kw in article.content.lower()) / len(keywords)
        scored_results.append((article, score))
    
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    return scored_results[:top_k]