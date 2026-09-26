from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import logging

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.legal import LegalArticle, LegalHierarchy
from app.models.audit import DecisionAuditLog, JudicialDeviationReport
from app.models.user import User
from app.engine.rag import hybrid_search, generate_llm_response
from app.engine.deviation import calculate_deviation_score, DeviationScoreRequest
from app.engine.lex_integrity import lex_integrity_engine, LegalNorm

logger = logging.getLogger(__name__)

router = APIRouter()


class LegalOpinionRequest(BaseModel):
    draft_text: str = Field(..., min_length=50)
    analysis_type: str = Field(default="comprehensive", pattern="^(comprehensive|risk-only|opinion-only|comparative)$")
    domain: Optional[str] = Field(None, max_length=50)
    jurisdiction: str = Field(default="indonesia")
    include_risk_assessment: bool = True
    include_recommendations: bool = True
    include_citations: bool = True
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    max_references: int = Field(10, ge=5, le=50)
    language: str = Field(default="id", pattern="^(id|en)$")


class LegalOpinionResponse(BaseModel):
    summary: str
    risk_level: str
    confidence_score: float
    legal_basis: List[Dict[str, Any]]
    ratio_decidendi: str
    recommendations: List[str]
    references: List[Dict[str, Any]]
    risk_assessment: Optional[Dict[str, Any]] = None


class RiskAssessmentRequest(BaseModel):
    draft_text: str = Field(..., min_length=50)
    analysis_type: str = Field(default="comprehensive")
    domain: Optional[str] = None
    jurisdiction: str = Field(default="indonesia")


class RiskAssessmentResponse(BaseModel):
    score: int
    level: str
    factors: List[Dict[str, Any]]
    mitigation: List[str]


class RecommendationsRequest(BaseModel):
    draft_text: str = Field(..., min_length=50)
    analysis_type: str = Field(default="comprehensive")
    domain: Optional[str] = None
    risk_level: Optional[str] = None


class RecommendationsResponse(BaseModel):
    recommendations: List[Dict[str, Any]]


class HistoryItem(BaseModel):
    id: str
    title: str
    type: str
    risk_score: int
    risk_level: str
    date: str
    status: str


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int
    page: int
    page_size: int


async def _generate_full_legal_opinion(
    db: AsyncSession,
    draft_text: str,
    analysis_type: str,
    domain: Optional[str],
    include_risk: bool,
    include_recs: bool,
    include_citations: bool,
    confidence_threshold: float,
    max_refs: int,
) -> LegalOpinionResponse:
    legal_articles = await hybrid_search(
        db=db,
        query=draft_text[:2000],
        domain=domain,
        top_k=max_refs,
        alpha=0.6,
    )
    
    conflicts = []
    for i, (article, _) in enumerate(legal_articles):
        for other_article, _ in legal_articles[i+1:]:
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
                        conflicts.append({
                            "type": conflict.conflict_type.value,
                            "severity": conflict.severity.value,
                            "description": conflict.description,
                            "source": conflict.source_norm.document_title,
                            "target": conflict.target_norm.document_title,
                        })
    
    high_conflicts = [c for c in conflicts if c["severity"] == "HIGH"]
    medium_conflicts = [c for c in conflicts if c["severity"] == "MEDIUM"]
    
    if high_conflicts:
        risk_level = "HIGH"
    elif medium_conflicts:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    references = []
    for i, (article, score) in enumerate(legal_articles[:max_refs]):
        if score >= confidence_threshold:
            references.append({
                "id": f"REF-{i+1:03d}",
                "document_title": article.document_title,
                "article_number": article.article_number,
                "content": article.content[:500],
                "domain": article.domain or "UMUM",
                "hierarchy_rank": article.hierarchy.rank if article.hierarchy else 99,
                "similarity_score": round(score, 2),
            })
    
    conflict_summary = "; ".join([f"{c['type']} ({c['severity']})" for c in conflicts[:5]])
    
    prompt = f"""Analisis draf hukum berikut dan berikan opini hukum menyeluruh sesuai standar hukum Indonesia.

DRAFT TEKS:
{draft_text[:3000]}

KONTRADIKSI TERDETEKSI ({len(conflicts)} total):
{chr(10).join([f"- {c['type']} ({c['severity']}): {c['description']}" for c in conflicts[:5]])}

REFERENSI HUKUM RELEVAN ({len(references)} ditemukan):
{chr(10).join([f"- {r['document_title']} {r['article_number']}: {r['content'][:300]}..." for r in references[:8]])}

JENIS ANALISIS: {analysis_type}
DOMAIN: {domain or 'UMUM'}

TUGAS: Berikan opini hukum komprehensif dalam Bahasa Indonesia:
1. Ringkasan eksekutif (3-4 kalimat)
2. Ratio decidendi (penalaran hukum bertahap, 3-5 paragraf)
3. Dasar hukum (pasal-pasal spesifik dengan penjelasan)
4. Rekomendasi perbaikan konkret (7-10 poin, prioritas)
5. Tingkat risiko (HIGH/MEDIUM/LOW) dan confidence score (0.0-1.0)

Kembalikan HANYA JSON valid:
{{
  "summary": "...",
  "risk_level": "HIGH|MEDIUM|LOW",
  "confidence_score": 0.0-1.0,
  "legal_basis": [{{"id": 1, "article_reference": "...", "explanation": "..."}}],
  "ratio_decidendi": "...",
  "recommendations": ["...", "..."]
}}"""
    
    llm_response = await generate_llm_response(
        prompt=prompt,
        format_json=True,
        temperature=0.2,
    )
    
    try:
        import json
        ai_data = json.loads(llm_response)
        
        legal_basis = ai_data.get("legal_basis", [])
        if include_citations and legal_basis:
            formatted_legal_basis = [
                {"id": lb.get("id", i+1), "article_reference": lb.get("article_reference", ""), "explanation": lb.get("explanation", "")}
                for i, lb in enumerate(legal_basis[:10])
            ]
        else:
            formatted_legal_basis = []
        
        risk_assessment = None
        if include_risk:
            base_score = min(len(high_conflicts) * 25 + len(medium_conflicts) * 15 + len(conflicts) * 5, 95)
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
            if high_conflicts:
                factors.append({
                    "id": 1,
                    "title": "Pelanggaran Hierarki Perundangan",
                    "description": f"{len(high_conflicts)} kontradiksi HIGH: norma level rendah mengatur hal yang dilarang level tinggi",
                    "severity": "HIGH",
                })
            if medium_conflicts:
                factors.append({
                    "id": 2,
                    "title": "Tumpang Tindih / Ketidaksesuaian Norma",
                    "description": f"{len(medium_conflicts)} kontradiksi MEDIUM",
                    "severity": "MEDIUM",
                })
            if analysis_type == "criminal":
                factors.append({
                    "id": len(factors) + 1,
                    "title": "Asas Legalitas & Ne Bis In Idem",
                    "description": "Perlu verifikasi pidana memiliki dasar UU & tidak ada tumpang tindih sanksi",
                    "severity": "HIGH",
                })
            elif analysis_type == "civil":
                factors.append({
                    "id": len(factors) + 1,
                    "title": "Syarat Sah Perjanjian & Klausula Baku",
                    "description": "Perlu verifikasi Pasal 1320 & 1337 KUHPerdata",
                    "severity": "MEDIUM",
                })
            
            factors.append({
                "id": len(factors) + 1,
                "title": "Ketidaksesuaian Prosedur Pembentukan",
                "description": "Verifikasi mengikuti UU No. 12/2011 (akademik, RIA, musyawarah)",
                "severity": "LOW",
            })
            
            mitigation = [
                "Identifikasi semua pasal bermasalah",
                "Revisi pelanggaran hierarki (Lex Superior)",
                "Harmonisasi norma tumpang tindih (Lex Specialis/Posterior)",
                "Konsultasi Kemenkumham & stakeholder",
                "Lakukan RIA jika diperlukan",
            ]
            
            risk_assessment = {
                "score": base_score,
                "level": level,
                "factors": factors,
                "mitigation": mitigation,
            }
        
        return LegalOpinionResponse(
            summary=ai_data.get("summary", "Analisis tidak tersedia"),
            risk_level=risk_level,
            confidence_score=ai_data.get("confidence_score", 0.8),
            legal_basis=formatted_legal_basis if include_citations else [],
            ratio_decidendi=ai_data.get("ratio_decidendi", "Ratio decidendi tidak tersedia"),
            recommendations=ai_data.get("recommendations", []) if include_recs else [],
            references=references if include_citations else [],
            risk_assessment=risk_assessment,
        )
    except Exception as e:
        logger.warning(f"LLM response parsing failed: {e}, using fallback")
        
        legal_basis = []
        for i, ref in enumerate(references[:8]):
            legal_basis.append({
                "id": i+1,
                "article_reference": f"{ref['document_title']} - {ref['article_number']}",
                "explanation": f"Dasar hukum untuk analisis: {ref['content'][:200]}...",
            })
        
        ratio_parts = [
            f"Berdasarkan analisis Lex Integrity Engine dan RAG pipeline terhadap draf yang disediakan:",
            "",
        ]
        
        if conflicts:
            ratio_parts.append(f"Terdeteksi {len(conflicts)} kontradiksi norma: {conflict_summary}.")
            ratio_parts.append("")
        
        for conflict in conflicts[:3]:
            ratio_parts.append(f"- {conflict['type']}: {conflict['description']}")
            ratio_parts.append("")
        
        if analysis_type == "criminal":
            ratio_parts.append("Analisis hukum pidana: Memeriksa asas legalitas (Pasal 1 KUHP), unsur-unsur delik (Anatomie Van Delict), dan tumpang tindih sanksi (ne bis in idem).")
        elif analysis_type == "civil":
            ratio_parts.append("Analisis hukum perdata: Memeriksa syarat sah perjanjian (Pasal 1320 KUHPerdata), klausula baku (Pasal 1337 KUHPerdata), dan kepatutan isi perjanjian.")
        elif analysis_type == "hierarchy":
            ratio_parts.append("Analisis hierarki: Memeriksa keselarasan dengan Pasal 7 UU No. 12/2011 tentang hierarki perundang-undangan.")
        else:
            ratio_parts.append("Analisis komprehensif: Menggabungkan pemeriksaan hierarki, kontradiksi, hukum pidana, dan hukum perdata.")
        
        ratio_parts.append("")
        ratio_parts.append("Kesimpulan: " + (
            "Draf memerlukan revisi substansial sebelum disahkan." if high_conflicts else
            "Draf memerlukan perbaikan pada beberapa pasal." if medium_conflicts else
            "Draf secara umum selaras dengan kerangka hukum yang berlaku."
        ))
        
        recommendations = []
        if include_recs:
            recommendations = [
                "Lakukan review menyeluruh terhadap pasal yang bermasalah",
                "Koordinasi dengan Kemenkumham untuk harmonisasi",
                "Sesuaikan dengan hierarki perundang-undangan (Pasal 7 UU No. 12/2011)",
            ]
            
            for conflict in conflicts[:3]:
                if conflict["type"] == "LEX_SUPERIOR":
                    recommendations.append(
                        f"Revisi norma level rendah yang bertentangan dengan {conflict['source']}"
                    )
                elif conflict["type"] == "DIRECT_CONTRADICTION":
                    recommendations.append(
                        f"Harmonisasi {conflict['target']} dengan {conflict['source']}"
                    )
        
        summary = f"Analisis {analysis_type} pada draf hukum mengidentifikasi {len(high_conflicts)} kontradiksi HIGH dan {len(medium_conflicts)} MEDIUM. "
        if high_conflicts:
            summary += "Rekomendasi: revisi substansial diperlukan. "
        elif medium_conflicts:
            summary += "Rekomendasi: perbaikan parsial diperlukan. "
        else:
            summary += "Draf relatif selaras dengan kerangka hukum. "
        
        risk_assessment = None
        if include_risk:
            base_score = min(len(high_conflicts) * 25 + len(medium_conflicts) * 15 + len(conflicts) * 5, 95)
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
            if high_conflicts:
                factors.append({
                    "id": 1,
                    "title": "Pelanggaran Hierarki Perundangan",
                    "description": f"{len(high_conflicts)} kontradiksi HIGH: norma level rendah mengatur hal yang dilarang level tinggi",
                    "severity": "HIGH",
                })
            if medium_conflicts:
                factors.append({
                    "id": 2,
                    "title": "Tumpang Tindih / Ketidaksesuaian Norma",
                    "description": f"{len(medium_conflicts)} kontradiksi MEDIUM",
                    "severity": "MEDIUM",
                })
            
            mitigation = [
                "Identifikasi semua pasal bermasalah",
                "Revisi pelanggaran hierarki (Lex Superior)",
                "Harmonisasi norma tumpang tindih (Lex Specialis/Posterior)",
                "Konsultasi Kemenkumham & stakeholder",
                "Lakukan RIA jika diperlukan",
            ]
            
            risk_assessment = {
                "score": base_score,
                "level": level,
                "factors": factors,
                "mitigation": mitigation,
            }
        
        return LegalOpinionResponse(
            summary=summary,
            risk_level=risk_level,
            confidence_score=0.8,
            legal_basis=legal_basis if include_citations else [],
            ratio_decidendi="\n".join(ratio_parts),
            recommendations=recommendations,
            references=references if include_citations else [],
            risk_assessment=risk_assessment,
        )


@router.post("/legal-opinion", response_model=LegalOpinionResponse)
async def generate_legal_opinion(
    request: LegalOpinionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    opinion = await _generate_full_legal_opinion(
        db=db,
        draft_text=request.draft_text,
        analysis_type=request.analysis_type,
        domain=request.domain,
        include_risk=request.include_risk_assessment,
        include_recs=request.include_recommendations,
        include_citations=request.include_citations,
        confidence_threshold=request.confidence_threshold,
        max_refs=request.max_references,
    )
    
    log = DecisionAuditLog(
        case_title=f"Legal Opinion - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        ai_recommendation=opinion.ratio_decidendi,
        ai_risk_score=opinion.risk_assessment["score"] if opinion.risk_assessment else 0,
        human_decision=None,
        is_deviated=False,
        deviation_justification=None,
        user_id=current_user.id,
        meta_data={
            "analysis_type": request.analysis_type,
            "domain": request.domain,
            "risk_level": opinion.risk_level,
            "confidence": opinion.confidence_score,
        },
    )
    db.add(log)
    await db.commit()
    
    return opinion


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risk(
    request: RiskAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    legal_articles = await hybrid_search(
        db=db,
        query=request.draft_text[:2000],
        domain=request.domain,
        top_k=15,
        alpha=0.6,
    )
    
    conflicts = []
    for i, (article, _) in enumerate(legal_articles):
        for other_article, _ in legal_articles[i+1:]:
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
                        conflicts.append({
                            "type": conflict.conflict_type.value,
                            "severity": conflict.severity.value,
                        })
    
    high_count = len([c for c in conflicts if c["severity"] == "HIGH"])
    medium_count = len([c for c in conflicts if c["severity"] == "MEDIUM"])
    low_count = len([c for c in conflicts if c["severity"] == "LOW"])
    
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
    if high_count > 0:
        factors.append({
            "id": 1,
            "title": "Pelanggaran Hierarki Perundangan (Lex Superior)",
            "description": f"{high_count} kontradiksi HIGH terdeteksi",
            "severity": "HIGH",
        })
    if medium_count > 0:
        factors.append({
            "id": 2,
            "title": "Tumpang Tindih / Ketidaksesuaian Norma",
            "description": f"{medium_count} kontradiksi MEDIUM terdeteksi",
            "severity": "MEDIUM",
        })
    if request.analysis_type == "criminal":
        factors.append({
            "id": 3,
            "title": "Asas Legalitas & Ne Bis In Idem",
            "description": "Perlu verifikasi pidana memiliki dasar UU & tidak ada tumpang tindih sanksi",
            "severity": "HIGH",
        })
    elif request.analysis_type == "civil":
        factors.append({
            "id": 3,
            "title": "Syarat Sah Perjanjian & Klausula Baku",
            "description": "Perlu verifikasi Pasal 1320 & 1337 KUHPerdata",
            "severity": "MEDIUM",
        })
    
    factors.append({
        "id": len(factors) + 1,
        "title": "Ketidaksesuaian Prosedur Pembentukan",
        "description": "Verifikasi mengikuti UU No. 12/2011 (akademik, RIA, musyawarah)",
        "severity": "LOW",
    })
    
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


@router.post("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    request: RecommendationsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    legal_articles = await hybrid_search(
        db=db,
        query=request.draft_text[:2000],
        domain=request.domain,
        top_k=10,
        alpha=0.6,
    )
    
    conflicts = []
    for i, (article, _) in enumerate(legal_articles):
        for other_article, _ in legal_articles[i+1:]:
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
                        conflicts.append(conflict)
    
    recommendations = []
    rec_id = 1
    
    recommendations.append({
        "id": rec_id,
        "category": "IMMEDIATE",
        "title": "Aksi Segera Diperlukan",
        "items": ["Hapus/revisi pasal yang melanggar hierarki perundang-undangan"],
    })
    rec_id += 1
    
    if request.risk_level in ["HIGH", "TINGGI"]:
        recommendations[0]["items"].append("Konsultasi Kemenkumham sebelum sidang plenary")
        recommendations[0]["items"].append("Lakukan RIA (Regulatory Impact Assessment)")
    
    recommendations.append({
        "id": rec_id,
        "category": "CONTRACTUAL",
        "title": "Revisi Kontraktual",
        "items": [
            "Perbaiki klausula force majeure sesuai standar",
            "Batasi denda keterlambatan dengan cap maksimal",
            "Tambahkan mediasi/arbitrase sebelum pengadilan",
        ],
    })
    rec_id += 1
    
    recommendations.append({
        "id": rec_id,
        "category": "PROCESS",
        "title": "Kepatuhan Proses",
        "items": [
            "Harmonisasi naskah akademik",
            "Musyawarah dengan DPRD/DPR",
            "Sinkronisasi dengan peraturan level atas",
        ],
    })
    rec_id += 1
    
    for conflict in conflicts[:3]:
        if conflict.conflict_type.value == "LEX_SUPERIOR":
            recommendations.append({
                "id": rec_id,
                "category": "SPECIFIC",
                "title": f"Perbaiki {conflict.target_norm.document_title} {conflict.target_norm.article_number}",
                "items": [
                    f"Bertentangan dengan {conflict.source_norm.document_title} {conflict.source_norm.article_number}",
                    "Opsi: hapus pasal, ganti sanksi administratif, atau naikkan ke level UU",
                ],
            })
            rec_id += 1
    
    return RecommendationsResponse(recommendations=recommendations)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(DecisionAuditLog).where(DecisionAuditLog.user_id == current_user.id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(desc(DecisionAuditLog.timestamp))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    items = []
    for log in logs:
        meta = log.meta_data or {}
        risk_score = log.ai_risk_score
        if risk_score >= 75:
            risk_level = "HIGH"
        elif risk_score >= 50:
            risk_level = "MEDIUM"
        elif risk_score >= 25:
            risk_level = "LOW"
        else:
            risk_level = "VERY_LOW"
        
        items.append(HistoryItem(
            id=str(log.id),
            title=log.case_title,
            type=meta.get("analysis_type", "unknown"),
            risk_score=risk_score,
            risk_level=risk_level,
            date=log.timestamp.isoformat(),
            status="completed",
        ))
    
    return HistoryResponse(
        items=items,
        total=total or 0,
        page=page,
        page_size=page_size,
    )