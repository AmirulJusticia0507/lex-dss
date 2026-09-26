from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.legal import LegalArticle, LegalHierarchy
from app.engine.lex_integrity import (
    LexIntegrityEngine,
    LegalNorm,
    ConflictType,
    Severity,
    ConflictResult,
    lex_integrity_engine,
)


class HTNService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = lex_integrity_engine
    
    async def get_hierarchy_types(self) -> List[LegalHierarchy]:
        result = await self.db.execute(select(LegalHierarchy).order_by(LegalHierarchy.rank))
        return result.scalars().all()
    
    async def validate_hierarchy(self, new_article: LegalArticle, existing_articles: List[LegalArticle]) -> List[ConflictResult]:
        new_norm = self._article_to_norm(new_article)
        existing_norms = [self._article_to_norm(a) for a in existing_articles]
        
        return self.engine.analyze_conflicts(new_norm, existing_norms)
    
    async def check_lex_superior(self, lower_norm: LegalArticle, higher_norm: LegalArticle) -> Optional[ConflictResult]:
        lower = self._article_to_norm(lower_norm)
        higher = self._article_to_norm(higher_norm)
        
        return self.engine.check_lex_superior(higher, lower)
    
    def _article_to_norm(self, article: LegalArticle) -> LegalNorm:
        hierarchy = None
        if article.hierarchy_id:
            hierarchy = article.hierarchy
        
        return LegalNorm(
            id=str(article.id),
            document_title=article.document_title,
            article_number=article.article_number,
            content=article.content,
            domain=article.domain,
            hierarchy_rank=hierarchy.rank if hierarchy else None,
            hierarchy_type=hierarchy.type_name if hierarchy else None,
        )
    
    async def get_articles_by_hierarchy(self, hierarchy_type: str) -> List[LegalArticle]:
        result = await self.db.execute(
            select(LegalArticle)
            .join(LegalHierarchy, LegalArticle.hierarchy_id == LegalHierarchy.id)
            .where(LegalHierarchy.type_name.ilike(f"%{hierarchy_type}%"))
        )
        return result.scalars().all()


class CriminalLawService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def analyze_delict_elements(self, article_content: str) -> Dict:
        elements = {
            "objective_elements": [],
            "subjective_elements": [],
            "penalty_provisions": [],
            "issues": [],
        }
        
        content_lower = article_content.lower()
        
        objective_keywords = {
            "perbuatan": ["perbuatan", "melakukan", "menyebabkan"],
            "hasil": ["hasil", "akibat", "menimbulkan"],
            "kausalitas": ["kausalitas", "kausal", "sebab-akibat"],
        }
        
        subjective_keywords = {
            "dolus": ["dolus", "kesengajaan", "sengaja", "opzet"],
            "culpa": ["culpa", "kelalaian", "lalai", "schuld"],
        }
        
        penalty_keywords = ["pidana", "denda", "penjara", "kurungan", "mati", "perdata"]
        
        for elem, keywords in objective_keywords.items():
            if any(kw in content_lower for kw in keywords):
                elements["objective_elements"].append(elem)
        
        for elem, keywords in subjective_keywords.items():
            if any(kw in content_lower for kw in keywords):
                elements["subjective_elements"].append(elem)
        
        if any(kw in content_lower for kw in penalty_keywords):
            elements["penalty_provisions"].append("ditemukan")
        else:
            elements["issues"].append("Tidak ditemukan ketentuan sanksi/pidana yang jelas (pelanggaran asas legalitas)")
        
        if not elements["objective_elements"]:
            elements["issues"].append("Unsur obyektif (perbuatan/hasil/kausalitas) tidak teridentifikasi")
        
        if not elements["subjective_elements"]:
            elements["issues"].append("Unsur subyektif (dolus/culpa) tidak teridentifikasi")
        
        return elements
    
    async def check_overlapping_penalties(self, articles: List[LegalArticle]) -> List[Dict]:
        overlapping = []
        
        for i, art1 in enumerate(articles):
            for art2 in articles[i+1:]:
                similarity = self._calculate_similarity(art1.content, art2.content)
                
                if similarity > 0.7:
                    overlapping.append({
                        "article_1": {"id": str(art1.id), "title": art1.document_title, "article": art1.article_number},
                        "article_2": {"id": str(art2.id), "title": art2.document_title, "article": art2.article_number},
                        "similarity": similarity,
                        "risk": "POTENTIAL_NE_BIS_IN_IDEM" if similarity > 0.85 else "OVERLAPPING_SCOPE",
                    })
        
        return overlapping
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)


class CivilLawService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def analyze_agreement_validity(self, article_content: str) -> Dict:
        analysis = {
            "syarat_sah": {
                "sepakat": False,
                "cakap_hukum": False,
                "hal_tertentu": False,
                "halal": False,
            },
            "elements_found": [],
            "potential_issues": [],
            "exoneration_clauses": [],
        }
        
        content_lower = article_content.lower()
        
        if any(kw in content_lower for kw in ["sepakat", "kesepakatan", "consensus", "akad"]):
            analysis["syarat_sah"]["sepakat"] = True
            analysis["elements_found"].append("Kesepakatan (Pasal 1320 KUHPerdata)")
        
        if any(kw in content_lower for kw in ["cakap", "dewasa", "berhak", "kompeten", "capable"]):
            analysis["syarat_sah"]["cakap_hukum"] = True
            analysis["elements_found"].append("Cakap hukum (Pasal 1320 KUHPerdata)")
        
        if any(kw in content_lower for kw in ["tertentu", "spesifik", "jelas", "definite", "certain"]):
            analysis["syarat_sah"]["hal_tertentu"] = True
            analysis["elements_found"].append("Hal tertentu (Pasal 1320 KUHPerdata)")
        
        if any(kw in content_lower for kw in ["halal", "sah", "tidak melanggar", "ketertiban umum", "kesusilaan"]):
            analysis["syarat_sah"]["halal"] = True
            analysis["elements_found"].append("Halal/tidak melanggar hukum (Pasal 1320 & 1337 KUHPerdata)")
        
        missing = [k for k, v in analysis["syarat_sah"].items() if not v]
        if missing:
            analysis["potential_issues"].append(f"Syarat sah tidak lengkap: {', '.join(missing)}")
        
        exoneration_patterns = [
            "bebas tanggung jawab",
            "tidak bertanggung jawab",
            "dibebaskan dari",
            "exoneration",
            "liability waiver",
            "pengecualian kewajiban",
        ]
        
        for pattern in exoneration_patterns:
            if pattern in content_lower:
                analysis["exoneration_clauses"].append(pattern)
        
        if analysis["exoneration_clauses"]:
            analysis["potential_issues"].append(
                "Terdeteksi klausula pelepasan tanggung jawab (exoneration clause) - "
                "perlu diperiksa kelayakannya sesuai Pasal 1337 KUHPerdata"
            )
        
        return analysis
    
    async def check_standard_terms(self, articles: List[LegalArticle]) -> List[Dict]:
        issues = []
        
        for article in articles:
            content_lower = article.content.lower()
            
            unfair_patterns = {
                "satu_pihak": ["hak satu pihak", "kewajiban satu pihak", "unilateral"],
                "denda_berlebih": ["denda besar", "denda tidak wajar", "excessive penalty"],
                "pembatalan_sepihak": ["pembatalan sepihak", "unilateral termination", "bebas membatalkan"],
                "perubahan_sepihak": ["perubahan sepihak", "unilateral amendment", "berhak mengubah kapan saja"],
            }
            
            for issue_type, patterns in unfair_patterns.items():
                if any(p in content_lower for p in patterns):
                    issues.append({
                        "article_id": str(article.id),
                        "article_title": article.document_title,
                        "article_number": article.article_number,
                        "issue_type": issue_type,
                        "description": f"Terdeteksi klausula bermasalah: {issue_type}",
                        "reference": "Pasal 1337 KUHPerdata / UU Perlindungan Konsumen",
                    })
        
        return issues