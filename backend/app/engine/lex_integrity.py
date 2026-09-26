from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum
import re


class ConflictType(str, Enum):
    LEX_SUPERIOR = "LEX_SUPERIOR"
    LEX_SPECIALIS = "LEX_SPECIALIS"
    LEX_POSTERIOR = "LEX_POSTERIOR"
    DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class LegalNorm(BaseModel):
    id: str
    document_title: str
    article_number: str
    content: str
    domain: Optional[str] = None
    hierarchy_rank: Optional[int] = None
    hierarchy_type: Optional[str] = None
    effective_date: Optional[str] = None


class ConflictResult(BaseModel):
    source_norm: LegalNorm
    target_norm: LegalNorm
    conflict_type: ConflictType
    severity: Severity
    description: str
    meta_data: Optional[Dict] = None


class LexIntegrityEngine:
    def __init__(self):
        self.hierarchy_order = {
            "UUD 1945": 1,
            "TAP MPR": 2,
            "UU": 3,
            "PERPPU": 3,
            "PP": 4,
            "PERPRES": 5,
            "PERMEN": 6,
            "PERDA": 7,
            "PERBUP": 8,
            "PERWALI": 9,
        }
    
    def get_hierarchy_rank(self, hierarchy_type: str) -> int:
        for key, rank in self.hierarchy_order.items():
            if key.lower() in hierarchy_type.lower():
                return rank
        return 99
    
    def check_lex_superior(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        rank_a = self.get_hierarchy_rank(norm_a.hierarchy_type or "")
        rank_b = self.get_hierarchy_rank(norm_b.hierarchy_type or "")
        
        if rank_a < rank_b and self._has_contradiction(norm_a.content, norm_b.content):
            return ConflictResult(
                source_norm=norm_a,
                target_norm=norm_b,
                conflict_type=ConflictType.LEX_SUPERIOR,
                severity=Severity.HIGH,
                description=f"{norm_a.hierarchy_type} ({norm_a.document_title} Pasal {norm_a.article_number}) "
                            f"mengalahkan {norm_b.hierarchy_type} ({norm_b.document_title} Pasal {norm_b.article_number}) "
                            f"berdasarkan asas Lex Superior Derogat Legi Inferiori (Pasal 7 UU 12/2011)",
            )
        return None
    
    def check_lex_specialis(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        if norm_a.domain == norm_b.domain and self._is_special_vs_general(norm_a, norm_b):
            if self._has_contradiction(norm_a.content, norm_b.content):
                return ConflictResult(
                    source_norm=norm_a,
                    target_norm=norm_b,
                    conflict_type=ConflictType.LEX_SPECIALIS,
                    severity=Severity.MEDIUM,
                    description=f"Aturan khusus ({norm_a.document_title} Pasal {norm_a.article_number}) "
                                f"mengalahkan aturan umum ({norm_b.document_title} Pasal {norm_b.article_number}) "
                                f"berdasarkan asas Lex Specialis Derogat Legi Generali",
                )
        return None
    
    def check_lex_posterior(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        date_a = self._parse_date(norm_a.effective_date)
        date_b = self._parse_date(norm_b.effective_date)
        
        if date_a and date_b and date_a > date_b:
            if self._has_contradiction(norm_a.content, norm_b.content):
                if self.get_hierarchy_rank(norm_a.hierarchy_type or "") == self.get_hierarchy_rank(norm_b.hierarchy_type or ""):
                    return ConflictResult(
                        source_norm=norm_a,
                        target_norm=norm_b,
                        conflict_type=ConflictType.LEX_POSTERIOR,
                        severity=Severity.MEDIUM,
                        description=f"Aturan yang lebih baru ({norm_a.document_title} Pasal {norm_a.article_number}, "
                                    f"tgl berlaku: {norm_a.effective_date}) mengalahkan aturan yang lebih lama "
                                    f"({norm_b.document_title} Pasal {norm_b.article_number}, "
                                    f"tgl berlaku: {norm_b.effective_date}) berdasarkan asas Lex Posterior Derogat Legi Priori",
                    )
        return None
    
    def check_direct_contradiction(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        if self._has_strong_contradiction(norm_a.content, norm_b.content):
            return ConflictResult(
                source_norm=norm_a,
                target_norm=norm_b,
                conflict_type=ConflictType.DIRECT_CONTRADICTION,
                severity=Severity.HIGH,
                description=f"Kontradiksi langsung terdeteksi antara {norm_a.document_title} Pasal {norm_a.article_number} "
                            f"dan {norm_b.document_title} Pasal {norm_b.article_number}",
            )
        return None
    
    def analyze_conflicts(self, new_norm: LegalNorm, existing_norms: List[LegalNorm]) -> List[ConflictResult]:
        conflicts = []
        
        for existing_norm in existing_norms:
            if existing_norm.id == new_norm.id:
                continue
            
            for check_method in [
                self.check_lex_superior,
                self.check_lex_specialis,
                self.check_lex_posterior,
                self.check_direct_contradiction,
            ]:
                conflict = check_method(new_norm, existing_norm)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _has_contradiction(self, content_a: str, content_b: str) -> bool:
        keywords_a = set(self._extract_keywords(content_a.lower()))
        keywords_b = set(self._extract_keywords(content_b.lower()))
        
        negation_words = {"tidak", "bukan", "dilarang", "melarang", "terlarang", "harus", "wajib", "diwajibkan"}
        
        for word in negation_words:
            if word in keywords_a and word not in keywords_b:
                return True
            if word in keywords_b and word not in keywords_a:
                return True
        
        return False
    
    def _has_strong_contradiction(self, content_a: str, content_b: str) -> bool:
        return self._has_contradiction(content_a, content_b)
    
    def _is_special_vs_general(self, norm_a: LegalNorm, norm_b: LegalNorm) -> bool:
        specific_indicators = ["khusus", "tertentu", "spesifik", "detail", "ransel"]
        general_indicators = ["umum", "general", "common", "biasa"]
        
        content_a_lower = norm_a.content.lower()
        content_b_lower = norm_b.content.lower()
        
        a_is_specific = any(ind in content_a_lower for ind in specific_indicators)
        b_is_general = any(ind in content_b_lower for ind in general_indicators)
        
        return a_is_specific and b_is_general
    
    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'\b\w+\b', text)
        stopwords = {"dan", "atau", "yang", "di", "ke", "dari", "untuk", "dengan", "pada", "adalah", "ini", "itu"}
        return [w for w in words if len(w) > 3 and w not in stopwords]
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[int]:
        if not date_str:
            return None
        try:
            import datetime
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%Y"]:
                try:
                    return int(datetime.datetime.strptime(date_str, fmt).timestamp())
                except ValueError:
                    continue
        except Exception:
            pass
        return None


lex_integrity_engine = LexIntegrityEngine()