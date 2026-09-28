from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


class ContractAnalysisBase(BaseModel):
    contract_title: str
    contract_type: str
    parties: Optional[list] = []
    content: Optional[str] = None
    analysis_result: Optional[dict] = None


class ContractAnalysisCreate(ContractAnalysisBase):
    pass


class ContractAnalysisResponse(ContractAnalysisBase):
    id: str
    created_at: str
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/contract-analyzer/analyze", response_model=dict)
async def analyze_contract(
    contract_type: str = "general",
    contract_title: str = "Untitled Contract",
    content: str = "",
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    analysis = _perform_contract_analysis(contract_type, content)

    return {
        "contract_title": contract_title,
        "contract_type": contract_type,
        "risk_score": analysis["risk_score"],
        "risk_level": analysis["risk_level"],
        "risk_factors": analysis["risk_factors"],
        "suggestions": analysis["suggestions"],
        "clauses_analyzed": analysis["clauses_analyzed"],
        "legal_references": analysis["legal_references"],
    }


@router.get("/contract-analyzer/", response_model=dict)
async def list_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    contract_type: str = "",
    db: AsyncSession = Depends(get_db),
):
    from app.models.legal import ContractAnalysis

    query = select(ContractAnalysis)
    if contract_type:
        query = query.where(ContractAnalysis.contract_type == contract_type)

    query = query.order_by(ContractAnalysis.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    analyses = result.scalars().all()

    return {
        "items": [
            {
                "id": str(a.id),
                "contract_title": a.contract_title,
                "contract_type": a.contract_type,
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "parties": a.parties or [],
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analyses
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": len(analyses),
            "total_pages": max(1, (len(analyses) + page_size - 1) // page_size),
        },
    }


def _perform_contract_analysis(contract_type: str, content: str) -> dict:
    risk_factors = []
    suggestions = []
    legal_references = []
    clauses_analyzed = 0

    risk_keywords = {
        "high": [
            "tidak dapat dicabut", "kekal", "tidak dapat diganggu gugat",
            "menyerahkan hak", "bebas dari tanggung jawab", "tidak bertanggung jawab",
            "hak sepenuhnya", "tanpa persetujuan", "sepihak",
        ],
        "medium": [
            "pemberitahuan tertulis", "jangka waktu", "denda", "ganti rugi",
            "kerahasiaan", "non-kompetisi", "force majeure", "arbitrase",
        ],
    }

    content_lower = content.lower() if content else ""

    for keyword in risk_keywords["high"]:
        if keyword in content_lower:
            risk_factors.append({
                "type": "HIGH",
                "keyword": keyword,
                "description": f"Klausula berisiko tinggi terdeteksi: '{keyword}'",
            })

    for keyword in risk_keywords["medium"]:
        if keyword in content_lower:
            risk_factors.append({
                "type": "MEDIUM",
                "keyword": keyword,
                "description": f"Klausula perlu review: '{keyword}'",
            })

    if not content:
        risk_factors.append({
            "type": "LOW",
            "keyword": "-",
            "description": "Tidak ada konten kontrak untuk dianalisis",
        })
        suggestions.append("Upload atau paste kontrak untuk analisis lebih detail")

    clauses_analyzed = max(1, len(content.split(".")) if content else 0)

    risk_score = min(100, len([f for f in risk_factors if f["type"] == "HIGH"]) * 25 +
                        len([f for f in risk_factors if f["type"] == "MEDIUM"]) * 10)

    if risk_score >= 75:
        risk_level = "TINGGI"
    elif risk_score >= 50:
        risk_level = "SEDANG"
    elif risk_score >= 25:
        risk_level = "RENDAH"
    else:
        risk_level = "SANGAT RENDAH"

    if contract_type == "employment":
        legal_references = [
            {"law": "UU No. 13/2003", "article": "Pasal 59", "description": "PKWT dan PKWTT"},
            {"law": "UU No. 6/2023", "article": "Pasal 42", "description": "Perjanjian Kerja"},
        ]
    elif contract_type == "nda":
        legal_references = [
            {"law": "UU No. 30/2002", "article": "Pasal 15", "description": "Kerahasiaan Dagang"},
            {"law": "KUHPerdata", "article": "Pasal 1320", "description": "Syarat Sahnya Perjanjian"},
        ]
    elif contract_type == "lease":
        legal_references = [
            {"law": "KUHPerdata", "article": "Pasal 1571", "description": "Perjanjian Sewa Menyewa"},
        ]
    else:
        legal_references = [
            {"law": "KUHPerdata", "article": "Pasal 1320", "description": "Syarat Sahnya Perjanjian"},
            {"law": "UU No. 12/2011", "article": "Pasal 7", "description": "Hierarki Peraturan"},
        ]

    if risk_factors:
        suggestions.append("Review klausula berisiko tinggi dengan legal counsel")
        suggestions.append("Pastikan klausula tidak bertentangan dengan hukum yang berlaku")
        suggestions.append("Verifikasi kewajiban dan hak kedua bel pihak seimbang")

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "suggestions": suggestions,
        "clauses_analyzed": clauses_analyzed,
        "legal_references": legal_references,
    }


from sqlalchemy import select, func
