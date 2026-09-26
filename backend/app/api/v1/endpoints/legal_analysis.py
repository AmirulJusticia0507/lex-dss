from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.legal import LegalArticle, LegalHierarchy, NormConflict
from app.models.audit import DecisionAuditLog, JudicialDeviationReport
from app.models.user import User
from app.engine.lex_integrity import lex_integrity_engine, LegalNorm
from app.engine.rag import search_similar_articles, hybrid_search
from app.engine.deviation import calculate_deviation_score, DeviationScoreRequest

router = APIRouter()


class AnalyzeConflictRequest(BaseModel):
    draft_text: str = Field(..., min_length=50)
    analysis_type: str = Field(default="comprehensive", pattern="^(comprehensive|hierarchy|contradiction|criminal|civil)$")
    domain: Optional[str] = Field(None, max_length=50)
    jurisdiction: str = Field(default="indonesia")


class ConflictItem(BaseModel):
    id: str
    conflict_type: str
    severity: str
    description: str
    source_article: Dict[str, Any]
    target_article: Dict[str, Any]
    created_at: str


class ReferenceItem(BaseModel):
    id: str
    document_title: str
    article_number: str
    content: str
    domain: str
    hierarchy_rank: int
    similarity_score: float


class LegalBasisItem(BaseModel):
    id: int
    article_reference: str
    explanation: str


class AIRecommendationResponse(BaseModel):
    summary: str
    risk_level: str
    confidence_score: float
    legal_basis: List[LegalBasisItem]
    ratio_decidendi: str
    recommendations: List[str]


class RiskFactor(BaseModel):
    id: int
    title: str
    description: str
    severity: str


class RiskAssessmentResponse(BaseModel):
    score: int
    level: str
    factors: List[RiskFactor]
    mitigation: List[str]


class AnalyzeConflictResponse(BaseModel):
    conflicts: List[ConflictItem]
    references: List[ReferenceItem]
    ai_recommendation: AIRecommendationResponse
    risk_assessment: RiskAssessmentResponse
    analysis_id: str


@router.post("/analyze-conflict", response_model=AnalyzeConflictResponse)
async def analyze_conflict(
    request: AnalyzeConflictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    analysis_id = f"ANL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    legal_articles = await _extract_articles_from_draft(db, request.draft_text, request.domain)
    
    conflicts = await _detect_conflicts(db, legal_articles, request.analysis_type)
    
    references = await _find_relevant_references(db, request.draft_text, request.domain, legal_articles)
    
    ai_recommendation = await _generate_ai_recommendation(
        request.draft_text, conflicts, references, request.analysis_type
    )
    
    risk_assessment = _generate_risk_assessment(conflicts, references, request.analysis_type)
    
    await _save_audit_log(db, current_user, request.draft_text, ai_recommendation, risk_assessment)
    
    return AnalyzeConflictResponse(
        conflicts=conflicts,
        references=references,
        ai_recommendation=ai_recommendation,
        risk_assessment=risk_assessment,
        analysis_id=analysis_id,
    )


async def _extract_articles_from_draft(
    db: AsyncSession, 
    draft_text: str, 
    domain: Optional[str]
) -> List[LegalArticle]:
    results = await hybrid_search(
        db=db,
        query=draft_text[:2000],
        domain=domain,
        top_k=20,
        alpha=0.6,
    )
    return [article for article, _ in results]


async def _detect_conflicts(
    db: AsyncSession,
    legal_articles: List[LegalArticle],
    analysis_type: str,
) -> List[ConflictItem]:
    conflicts = []
    
    for i, article in enumerate(legal_articles):
        for other_article in legal_articles[i+1:]:
            if article.hierarchy_id and other_article.hierarchy_id:
                article_norm = LegalNorm(
                    id=str(article.id),
                    document_title=article.document_title,
                    article_number=article.article_number,
                    content=article.content,
                    domain=article.domain,
                    hierarchy_rank=article.hierarchy.rank if article.hierarchy else None,
                    hierarchy_type=article.hierarchy.type_name if article.hierarchy else None,
                )
                other_norm = LegalNorm(
                    id=str(other_article.id),
                    document_title=other_article.document_title,
                    article_number=other_article.article_number,
                    content=other_article.content,
                    domain=other_article.domain,
                    hierarchy_rank=other_article.hierarchy.rank if other_article.hierarchy else None,
                    hierarchy_type=other_article.hierarchy.type_name if other_article.hierarchy else None,
                )
                
                for check_method in [
                    lex_integrity_engine.check_lex_superior,
                    lex_integrity_engine.check_lex_specialis,
                    lex_integrity_engine.check_lex_posterior,
                    lex_integrity_engine.check_direct_contradiction,
                ]:
                    conflict = check_method(article_norm, other_norm)
                    if conflict:
                        conflicts.append(ConflictItem(
                            id=f"CONF-{len(conflicts)+1:03d}",
                            conflict_type=conflict.conflict_type.value,
                            severity=conflict.severity.value,
                            description=conflict.description,
                            source_article={
                                "id": str(conflict.source_norm.id),
                                "document_title": conflict.source_norm.document_title,
                                "article_number": conflict.source_norm.article_number,
                                "content": conflict.source_norm.content[:300],
                                "domain": conflict.source_norm.domain,
                                "hierarchy_rank": conflict.source_norm.hierarchy_rank,
                            },
                            target_article={
                                "id": str(conflict.target_norm.id),
                                "document_title": conflict.target_norm.document_title,
                                "article_number": conflict.target_norm.article_number,
                                "content": conflict.target_norm.content[:300],
                                "domain": conflict.target_norm.domain,
                                "hierarchy_rank": conflict.target_norm.hierarchy_rank,
                            },
                            created_at=datetime.utcnow().isoformat(),
                        ))
    
    return conflicts[:10]


async def _find_relevant_references(
    db: AsyncSession,
    draft_text: str,
    domain: Optional[str],
    legal_articles: List[LegalArticle],
) -> List[ReferenceItem]:
    references = []
    used_ids = set()
    
    for article in legal_articles[:5]:
        if article.id not in used_ids:
            references.append(ReferenceItem(
                id=f"REF-{len(references)+1:03d}",
                document_title=article.document_title,
                article_number=article.article_number,
                content=article.content[:500],
                domain=article.domain or "UMUM",
                hierarchy_rank=article.hierarchy.rank if article.hierarchy else 99,
                similarity_score=0.85,
            ))
            used_ids.add(article.id)
    
    search_results = await hybrid_search(
        db=db,
        query=draft_text[:2000],
        domain=domain,
        top_k=10,
        alpha=0.7,
    )
    
    for article, similarity in search_results:
        if article.id not in used_ids and len(references) < 8:
            references.append(ReferenceItem(
                id=f"REF-{len(references)+1:03d}",
                document_title=article.document_title,
                article_number=article.article_number,
                content=article.content[:500],
                domain=article.domain or "UMUM",
                hierarchy_rank=article.hierarchy.rank if article.hierarchy else 99,
                similarity_score=round(similarity, 2),
            ))
            used_ids.add(article.id)
    
    return references


async def _generate_ai_recommendation(
    draft_text: str,
    conflicts: List[ConflictItem],
    references: List[ReferenceItem],
    analysis_type: str,
) -> AIRecommendationResponse:
    high_conflicts = [c for c in conflicts if c.severity == "HIGH"]
    medium_conflicts = [c for c in conflicts if c.severity == "MEDIUM"]
    
    if high_conflicts:
        risk_level = "HIGH"
        confidence = 0.9
    elif medium_conflicts:
        risk_level = "MEDIUM"
        confidence = 0.75
    else:
        risk_level = "LOW"
        confidence = 0.6
    
    legal_basis = []
    for i, ref in enumerate(references[:5]):
        legal_basis.append(LegalBasisItem(
            id=i+1,
            article_reference=f"{ref.document_title} - {ref.article_number}",
            explanation=f"Relevan untuk analisis {analysis_type}: {ref.content[:200]}...",
        ))
    
    conflict_summary = "; ".join([f"{c.conflict_type} ({c.severity})" for c in conflicts[:3]])
    
    ratio_parts = [
        f"Berdasarkan analisis Lex Integrity Engine terdeteksi {len(conflicts)} kontradiksi norma: {conflict_summary}.",
    ]
    
    for conflict in conflicts[:3]:
        ratio_parts.append(
            f"{conflict.conflict_type}: {conflict.description}"
        )
    
    ratio_parts.append(
        "Rekomendasi: Perbaiki draf sesuai hierarki perundang-undangan dan asas-asas hukum yang berlaku."
    )
    
    recommendations = [
        "Lakukan review menyeluruh terhadap pasal yang bermasalah",
        "Koordinasi dengan Kemenkumham untuk harmonisasi",
        "Sesuaikan dengan hierarki perundang-undangan (Pasal 7 UU No. 12/2011)",
    ]
    
    for conflict in conflicts[:2]:
        if conflict.conflict_type == "LEX_SUPERIOR":
            recommendations.append(
                f"Hapus/revisi {conflict.target_article['article_number']} {conflict.target_article['document_title']} "
                f"yang bertentangan dengan {conflict.source_article['article_number']} {conflict.source_article['document_title']}"
            )
        elif conflict.conflict_type == "DIRECT_CONTRADICTION":
            recommendations.append(
                f"Harmonisasi {conflict.target_article['article_number']} dengan {conflict.source_article['article_number']}"
            )
    
    summary = f"Draf mengandung {len(high_conflicts)} kontradiksi HIGH, {len(medium_conflicts)} MEDIUM. "
    if high_conflicts:
        summary += "Perlu revisi substansial sebelum disahkan. "
    summary += "Detail lihat ratio decidendi."
    
    return AIRecommendationResponse(
        summary=summary,
        risk_level=risk_level,
        confidence_score=confidence,
        legal_basis=legal_basis,
        ratio_decidendi="\n\n".join(ratio_parts),
        recommendations=recommendations,
    )


def _generate_risk_assessment(
    conflicts: List[ConflictItem],
    references: List[ReferenceItem],
    analysis_type: str,
) -> RiskAssessmentResponse:
    high_count = len([c for c in conflicts if c.severity == "HIGH"])
    medium_count = len([c for c in conflicts if c.severity == "MEDIUM"])
    low_count = len([c for c in conflicts if c.severity == "LOW"])
    
    base_score = min(high_count * 25 + medium_count * 15 + low_count * 5, 95)
    if base_score == 0:
        base_score = 10
    
    if base_score >= 75:
        level = "TINGGI"
    elif base_score >= 50:
        level = "SEDANG"
    elif base_score >= 25:
        level = "RENDAH"
    else:
        level = "SANGAT RENDAH"
    
    factors = []
    factor_id = 1
    
    if high_count > 0:
        factors.append(RiskFactor(
            id=factor_id,
            title="Pelanggaran Hierarki Perundangan (Lex Superior)",
            description=f"{high_count} kontradiksi tingkat HIGH: norma level lebih rendah mengatur hal yang dilarang oleh norma level lebih tinggi",
            severity="HIGH",
        ))
        factor_id += 1
    
    if medium_count > 0:
        factors.append(RiskFactor(
            id=factor_id,
            title="Tumpang Tindih / Ketidaksesuaian Norma",
            description=f"{medium_count} kontradiksi tingkat MEDIUM: lex specialis, lex posterior, atau kontradiksi langsung",
            severity="MEDIUM",
        ))
        factor_id += 1
    
    type_specific = {
        "criminal": ("Pelanggaran Asas Legalitas", "Pidana diatur tanpa dasar undang-undang atau tumpang tindih sanksi (ne bis in idem)"),
        "civil": ("Klausula Tidak Sah Perjanjian", "Waiver hak, force majeure tidak adil, atau denda tanpa batas maksimum"),
        "hierarchy": ("Ketidaksesuaian Hierarki", "Peraturan level rendah mengatur kewenangan level tinggi"),
    }
    
    if analysis_type in type_specific:
        title, desc = type_specific[analysis_type]
        factors.append(RiskFactor(
            id=factor_id,
            title=title,
            description=desc,
            severity="HIGH" if analysis_type in ["criminal", "hierarchy"] else "MEDIUM",
        ))
        factor_id += 1
    
    factors.append(RiskFactor(
        id=factor_id,
        title="Ketidaksesuaian Prosedur Pembentukan",
        description="Proses pembentukan peraturan tidak mengikuti UU No. 12/2011 (akademik, RIA, musyawarah)",
        severity="LOW",
    ))
    
    mitigation = [
        "Identifikasi semua pasal bermasalah dari hasil analisis",
        "Revisi pasal yang melanggar hierarki (Lex Superior)",
        "Harmonisasi norma yang tumpang tindih (Lex Specialis/Posterior)",
        "Konsultasi dengan Kemenkumham dan stakeholder terkait",
        "Lakukan Regulatory Impact Assessment (RIA) jika diperlukan",
    ]
    
    return RiskAssessmentResponse(
        score=base_score,
        level=level,
        factors=factors,
        mitigation=mitigation,
    )


async def _save_audit_log(
    db: AsyncSession,
    user: User,
    draft_text: str,
    ai_recommendation: AIRecommendationResponse,
    risk_assessment: RiskAssessmentResponse,
):
    log = DecisionAuditLog(
        case_title=f"Analisis Draf - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        ai_recommendation=ai_recommendation.ratio_decidendi,
        ai_risk_score=risk_assessment.score,
        human_decision=None,
        is_deviated=False,
        deviation_justification=None,
        user_id=user.id,
        meta_data={
            "analysis_type": "conflict_analysis",
            "conflicts_count": len(ai_recommendation.recommendations),
            "risk_level": risk_assessment.level,
        },
    )
    db.add(log)
    await db.commit()


class StatsResponse(BaseModel):
    total_conflicts: int
    high_severity: int
    medium_severity: int
    low_severity: int
    total_articles: int
    analyzed_documents: int
    by_domain: Dict[str, int]
    by_hierarchy: Dict[str, int]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    total_conflicts = await db.scalar(select(func.count(NormConflict.id)))
    high_severity = await db.scalar(select(func.count(NormConflict.id)).where(NormConflict.severity == "HIGH"))
    medium_severity = await db.scalar(select(func.count(NormConflict.id)).where(NormConflict.severity == "MEDIUM"))
    low_severity = await db.scalar(select(func.count(NormConflict.id)).where(NormConflict.severity == "LOW"))
    
    total_articles = await db.scalar(select(func.count(LegalArticle.id)))
    
    audit_count = await db.scalar(select(func.count(DecisionAuditLog.id)))
    
    domain_result = await db.execute(
        select(LegalArticle.domain, func.count(LegalArticle.id))
        .where(LegalArticle.domain.is_not(None))
        .group_by(LegalArticle.domain)
    )
    by_domain = {row[0]: row[1] for row in domain_result.all()}
    
    hierarchy_result = await db.execute(
        select(LegalHierarchy.type_name, func.count(LegalArticle.id))
        .join(LegalArticle, LegalArticle.hierarchy_id == LegalHierarchy.id)
        .group_by(LegalHierarchy.type_name)
    )
    by_hierarchy = {row[0]: row[1] for row in hierarchy_result.all()}
    
    return StatsResponse(
        total_conflicts=total_conflicts or 0,
        high_severity=high_severity or 0,
        medium_severity=medium_severity or 0,
        low_severity=low_severity or 0,
        total_articles=total_articles or 0,
        analyzed_documents=audit_count or 0,
        by_domain=by_domain,
        by_hierarchy=by_hierarchy,
    )


class ArticleSearchRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    hierarchy_ids: Optional[List[int]] = None
    top_k: int = Field(10, ge=1, le=50)
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0)
    search_mode: str = Field("hybrid", pattern="^(vector|keyword|hybrid)$")


@router.post("/articles/search")
async def search_articles_endpoint(
    request: ArticleSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from app.engine.rag import search_similar_articles, keyword_search
    
    if request.search_mode == "vector":
        results = await search_similar_articles(
            db=db,
            query=request.query,
            domain=request.domain,
            hierarchy_ids=request.hierarchy_ids,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )
    elif request.search_mode == "keyword":
        results = await keyword_search(
            db=db,
            query=request.query,
            domain=request.domain,
            hierarchy_ids=request.hierarchy_ids,
            top_k=request.top_k,
        )
    else:
        results = await hybrid_search(
            db=db,
            query=request.query,
            domain=request.domain,
            hierarchy_ids=request.hierarchy_ids,
            top_k=request.top_k,
        )
    
    return {
        "query": request.query,
        "results": [
            {
                "id": str(article.id),
                "document_title": article.document_title,
                "article_number": article.article_number,
                "content": article.content[:500] + ("..." if len(article.content) > 500 else ""),
                "domain": article.domain,
                "hierarchy_type": article.hierarchy.type_name if article.hierarchy else None,
                "hierarchy_rank": article.hierarchy.rank if article.hierarchy else None,
                "similarity": round(score, 4),
            }
            for article, score in results
        ],
        "total_found": len(results),
        "search_mode": request.search_mode,
    }


@router.get("/conflicts")
async def get_conflicts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conflict_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
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
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(NormConflict.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    conflicts = result.scalars().all()
    
    return {
        "data": [
            {
                "id": str(c.id),
                "conflict_type": c.conflict_type,
                "severity": c.severity,
                "description": c.description,
                "source_article": {
                    "id": str(c.source_article.id) if c.source_article else None,
                    "document_title": c.source_article.document_title if c.source_article else None,
                    "article_number": c.source_article.article_number if c.source_article else None,
                },
                "target_article": {
                    "id": str(c.target_article.id) if c.target_article else None,
                    "document_title": c.target_article.document_title if c.target_article else None,
                    "article_number": c.target_article.article_number if c.target_article else None,
                },
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in conflicts
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/conflicts/{conflict_id}")
async def get_conflict_detail(
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
    
    return {
        "data": {
            "id": str(conflict.id),
            "conflict_type": conflict.conflict_type,
            "severity": conflict.severity,
            "description": conflict.description,
            "source_article": {
                "id": str(conflict.source_article.id) if conflict.source_article else None,
                "document_title": conflict.source_article.document_title if conflict.source_article else None,
                "article_number": conflict.source_article.article_number if conflict.source_article else None,
                "content": conflict.source_article.content if conflict.source_article else None,
                "domain": conflict.source_article.domain if conflict.source_article else None,
            },
            "target_article": {
                "id": str(conflict.target_article.id) if conflict.target_article else None,
                "document_title": conflict.target_article.document_title if conflict.target_article else None,
                "article_number": conflict.target_article.article_number if conflict.target_article else None,
                "content": conflict.target_article.content if conflict.target_article else None,
                "domain": conflict.target_article.domain if conflict.target_article else None,
            },
            "created_at": conflict.created_at.isoformat() if conflict.created_at else None,
        }
    }


@router.get("/articles")
async def get_legal_articles(
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
    articles = result.scalars().all()
    
    return {
        "data": [
            {
                "id": str(a.id),
                "document_title": a.document_title,
                "article_number": a.article_number,
                "content": a.content,
                "domain": a.domain,
                "hierarchy_id": a.hierarchy_id,
                "hierarchy": {
                    "id": a.hierarchy.id,
                    "type_name": a.hierarchy.type_name,
                    "rank": a.hierarchy.rank,
                } if a.hierarchy else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in articles
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/articles/{article_id}")
async def get_article_detail(
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
    
    return {
        "data": {
            "id": str(article.id),
            "document_title": article.document_title,
            "article_number": article.article_number,
            "content": article.content,
            "domain": article.domain,
            "hierarchy_id": article.hierarchy_id,
            "hierarchy": {
                "id": article.hierarchy.id,
                "type_name": article.hierarchy.type_name,
                "rank": article.hierarchy.rank,
            } if article.hierarchy else None,
            "created_at": article.created_at.isoformat() if article.created_at else None,
            "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        }
    }


@router.get("/hierarchy")
async def get_hierarchy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(LegalHierarchy).order_by(LegalHierarchy.rank))
    hierarchy = result.scalars().all()
    
    return {
        "data": [
            {
                "id": h.id,
                "type_name": h.type_name,
                "rank": h.rank,
                "description": h.description,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in hierarchy
        ]
    }