from typing import List, Tuple, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, or_
from pgvector.sqlalchemy import Vector
from app.core.config import settings
from app.core.llm_clients import ollama_client, gemini_client
from app.models.legal import LegalArticle, LegalHierarchy

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> List[float]:
    if settings.EMBEDDING_PROVIDER == "ollama":
        try:
            return await ollama_client.embeddings(text[:8000])
        except Exception as e:
            logger.warning(f"Ollama embedding failed: {e}, trying fallback")
    
    if settings.EMBEDDING_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            import openai
            client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE != "https://api.openai.com/v1" else None,
            )
            response = await client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text[:8000],
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding failed: {e}")
    
    logger.warning("All embedding providers failed, returning zero vector")
    return [0.0] * settings.EMBEDDING_DIMENSION


async def generate_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    format_json: bool = False,
    temperature: Optional[float] = None,
    model: Optional[str] = None,
) -> str:
    system = system_prompt or settings.SYSTEM_PROMPT
    
    if settings.LLM_PROVIDER == "ollama":
        try:
            response = await ollama_client.generate(
                prompt=prompt,
                model=model or settings.OLLAMA_MODEL,
                format="json" if format_json else None,
                system=system,
                options={"temperature": temperature or settings.OLLAMA_TEMPERATURE},
            )
            return response.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
    
    if settings.LLM_PROVIDER == "gemini" and gemini_client.has_key():
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await gemini_client.generate(
                system_prompt=system,
                messages=messages,
                temperature=temperature or 0.2,
            )
            return response.get("text", "").strip()
        except Exception as e:
            logger.warning(f"Gemini generation failed: {e}")
    
    if settings.LLM_PROVIDER == "bazaarlink" and settings.OPENAI_API_KEY:
        try:
            import openai
            client = openai.AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE,
            )
            messages = [{"role": "system", "content": system}]
            if format_json:
                messages.append({"role": "user", "content": prompt + "\n\nKembalikan HANYA JSON valid."})
            else:
                messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=model or settings.LLM_MODEL,
                messages=messages,
                temperature=temperature or settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                response_format={"type": "json_object"} if format_json else None,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Bazaarlink/OpenAI generation failed: {e}")
    
    return ""


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
        logger.warning("Zero embedding returned, falling back to keyword search")
        return await keyword_search(db, query, domain, hierarchy_ids, top_k)
    
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
    keywords = [w for w in query.lower().split() if len(w) > 2]
    
    stmt = (
        select(LegalArticle, LegalHierarchy)
        .outerjoin(LegalHierarchy, LegalArticle.hierarchy_id == LegalHierarchy.id)
    )
    
    conditions = []
    for keyword in keywords[:10]:
        conditions.append(LegalArticle.content.ilike(f"%{keyword}%"))
    
    if conditions:
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
        content_lower = article.content.lower()
        score = sum(1 for kw in keywords if kw in content_lower) / max(len(keywords), 1)
        scored_results.append((article, score))
    
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    return scored_results[:top_k]


async def bm25_search(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
) -> List[Tuple[LegalArticle, float]]:
    terms = [w for w in query.split() if len(w) > 2][:10]
    if not terms:
        return []
    
    ts_query = " | ".join(f"{t}:*" for t in terms)
    
    sql = text("""
        SELECT la.*, lh.type_name, lh.rank,
               ts_rank_cd(
                   to_tsvector('indonesian', COALESCE(la.title,'') || ' ' || COALESCE(la.content,'')),
                   to_tsquery('indonesian', :ts_query)
               ) AS similarity
        FROM legal_articles la
        LEFT JOIN legal_hierarchy lh ON la.hierarchy_id = lh.id
        WHERE to_tsvector('indonesian', COALESCE(la.title,'') || ' ' || COALESCE(la.content,''))
              @@ to_tsquery('indonesian', :ts_query)
        ORDER BY similarity DESC LIMIT :top_k
    """)
    
    result = await db.execute(sql, {"ts_query": ts_query, "top_k": top_k})
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


async def reciprocal_rank_fusion(
    vec_results: List[Tuple[LegalArticle, float]],
    bm25_results: List[Tuple[LegalArticle, float]],
    k: int = 60,
) -> List[Tuple[LegalArticle, float]]:
    scores = {}
    
    for i, (article, _) in enumerate(vec_results):
        key = str(article.id)
        prev = scores.get(key, {"doc": article, "score": 0.0, "vRank": None, "bRank": None})
        prev["vRank"] = i + 1
        prev["score"] += 1 / (k + i + 1)
        scores[key] = prev
    
    for i, (article, _) in enumerate(bm25_results):
        key = str(article.id)
        prev = scores.get(key, {"doc": article, "score": 0.0, "vRank": None, "bRank": None})
        prev["bRank"] = i + 1
        prev["score"] += 1 / (k + i + 1)
        scores[key] = prev
    
    fused = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return [(item["doc"], item["score"]) for item in fused]


async def hybrid_search_bm25(
    db: AsyncSession,
    query: str,
    domain: Optional[str] = None,
    hierarchy_ids: Optional[List[int]] = None,
    top_k: int = 10,
) -> List[Tuple[LegalArticle, float]]:
    vec_results = await search_similar_articles(
        db=db,
        query=query,
        domain=domain,
        hierarchy_ids=hierarchy_ids,
        top_k=top_k * 2,
        similarity_threshold=0.0,
    )
    
    bm25_results = await bm25_search(db, query, top_k * 2)
    
    fused = await reciprocal_rank_fusion(vec_results, bm25_results)
    
    if domain:
        fused = [(a, s) for a, s in fused if not domain or a.domain == domain]
    if hierarchy_ids:
        fused = [(a, s) for a, s in fused if a.hierarchy_id in hierarchy_ids]
    
    return fused[:top_k]