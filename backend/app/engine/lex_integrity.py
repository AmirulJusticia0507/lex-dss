"""Lex Integrity Engine — rules engine deteksi kontradiksi norma.

Engine ini murni deterministik (tanpa LLM) sehingga hasilnya dapat diaudit dan
dipertanggungjawabkan. Orchestration tingkat database (pengambilan kandidat,
persistensi temuan) ada di `app/services/lex_integrity_service.py`.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Set
from enum import Enum
import re


class ConflictType(str, Enum):
    LEX_SUPERIOR = "LEX_SUPERIOR"
    LEX_SPECIALIS = "LEX_SPECIALIS"
    LEX_POSTERIOR = "LEX_POSTERIOR"
    DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"
    ANATOMIE_DELICT_OVERLAP = "ANATOMIE_DELICT_OVERLAP"
    KLAUSULA_BAKU_TIDAK_SAH = "KLAUSULA_BAKU_TIDAK_SAH"
    SYARAT_PERJANJIAN_TIDAK_TERPENUHI = "SYARAT_PERJANJIAN_TIDAK_TERPENUHI"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


SEVERITY_ORDER: Dict[str, int] = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

LEGAL_BASIS: Dict[str, List[str]] = {
    ConflictType.LEX_SUPERIOR.value: [
        "Pasal 7 ayat (1) UU No. 12 Tahun 2011 (Lex Superior Derogat Legi Inferiori)",
    ],
    ConflictType.LEX_SPECIALIS.value: [
        "Pasal 1 ayat (1) UU No. 12 Tahun 2011 (Lex Specialis Derogat Legi Generali)",
    ],
    ConflictType.LEX_POSTERIOR.value: [
        "Pasal 7 ayat (2) UU No. 12 Tahun 2011 (Lex Posterior Derogat Legi Priori)",
    ],
    ConflictType.DIRECT_CONTRADICTION.value: [
        "Asas kepastian hukum dan ketertiban umum dalam pembentukan peraturan perundang-undangan",
    ],
    ConflictType.ANATOMIE_DELICT_OVERLAP.value: [
        "Pasal 1 ayat (1) UU No. 1 Tahun 2023 (asas legalitas)",
        "Asas ne bis in idem dalam hukum acara pidana",
    ],
    ConflictType.KLAUSULA_BAKU_TIDAK_SAH.value: [
        "Pasal 1337 KUHPerdata (perjanjian yang bertentangan dengan ketertiban umum/kesusilaan)",
    ],
    ConflictType.SYARAT_PERJANJIAN_TIDAK_TERPENUHI.value: [
        "Pasal 1320 KUHPerdata (syarat sah perjanjian)",
    ],
}

DEFAULT_HIERARCHY_RANKS: Dict[str, int] = {
    "UUD": 1,
    "TAP MPR": 2,
    "PUTUSAN MPR": 2,
    "UU": 3,
    "PERPPU": 3,
    "PP": 4,
    "PERPRES": 5,
    "PERBIDAN": 5,
    "PERMEN": 6,
    "PERGUB": 7,
    "PERDA": 7,
    "PERBUP": 8,
    "PERWALI": 9,
}

# Alias bentuk nama resmi peraturan (dipakai untuk memetakan "Peraturan Presiden",
# "Peraturan Menteri", dan sejenisnya ke rank yang sama).
HIERARCHY_ALIASES: List[tuple] = [
    ("UNDANG-UNDANG DASAR", 1),
    ("TAP MPR", 2),
    ("PUTUSAN MPR", 2),
    ("UNDANG-UNDANG", 3),
    ("PERATURAN PEMERINTAH", 4),
    ("PERATURAN PRESIDEN", 5),
    ("KEPUTUSAN PRESIDEN", 5),
    ("PERATURAN MENTERI", 6),
    ("PERATURAN DAERAH KHUSUS", 7),
    ("PERATURAN DAERAH ISTIMEWA", 7),
    ("PERATURAN DAERAH", 7),
    ("PERATURAN GUBERNUR", 7),
    ("PERATURAN BUPATI", 8),
    ("PERATURAN WALIKOTA", 9),
]

PROHIBITION_MARKERS: Set[str] = {
    "dilarang",
    "dilarangi",
    "melarang",
    "terlarang",
    "terlarangi",
    "tidak boleh",
    "tidak diperbolehkan",
    "tidak diizinkan",
    "tidak diperkenankan",
    "tidak sah",
    "dibatalkan",
}

PERMISSION_MARKERS: Set[str] = {
    "boleh",
    "dapat",
    "dibolehkan",
    "diizinkan",
    "diperbolehkan",
    "wajib",
    "harus",
    "berhak",
}

REPEAL_MARKERS: Set[str] = {
    "dicabut",
    "dihapus",
    "tidak berlaku",
    "diganti",
    "diubah",
    "dinyatakan tidak berlaku",
}

SPECIFIC_MARKERS = ("khusus", "tertentu", "spesifik", "terinci", "rinci")
GENERAL_MARKERS = ("umum", "lazim", "pada umumnya", "secara umum")

STOPWORDS: Set[str] = {
    "yang", "untuk", "dengan", "dari", "pada", "adalah", "akan", "dapat", "tidak",
    "dalam", "oleh", "atau", "dan", "itu", "ini", "agar", "bagi", "jika", "ketika",
    "telah", "harus", "boleh", "yaitu", "sebagai", "bahwa", "maka", "serta",
}


class LegalNorm(BaseModel):
    id: str
    document_title: str
    article_number: str
    content: str
    domain: Optional[str] = None
    hierarchy_rank: Optional[int] = None
    hierarchy_type: Optional[str] = None
    effective_date: Optional[str] = None
    source_url: Optional[str] = None


class ConflictResult(BaseModel):
    source_norm: LegalNorm
    target_norm: LegalNorm
    conflict_type: ConflictType
    severity: Severity
    description: str
    meta_data: Optional[Dict] = None
    legal_basis: List[str] = []
    recommended_action: str = ""
    confidence: float = 0.0
    evidence: List[str] = []
    persisted_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.persisted_id,
            "source": {
                "id": self.source_norm.id,
                "document_title": self.source_norm.document_title,
                "article_number": self.source_norm.article_number,
                "hierarchy_type": self.source_norm.hierarchy_type,
                "hierarchy_rank": self.source_norm.hierarchy_rank,
            },
            "target": {
                "id": self.target_norm.id,
                "document_title": self.target_norm.document_title,
                "article_number": self.target_norm.article_number,
                "hierarchy_type": self.target_norm.hierarchy_type,
                "hierarchy_rank": self.target_norm.hierarchy_rank,
            },
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "legal_basis": self.legal_basis,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "meta_data": self.meta_data or {},
        }


class LexIntegrityEngine:
    """Aturan kontradiksi norma:

    - `check_lex_superior`        : norma lebih rendah bentrok dengan norma lebih tinggi
    - `check_lex_specialis`       : norma khusus bentrok dengan norma umum
    - `check_lex_posterior`       : norma lebih baru mencabut/menyimpangi norma lama
    - `check_direct_contradiction`: larangan vs permission pada objek yang sama
    """

    def __init__(
        self,
        hierarchy_ranks: Optional[Dict[str, int]] = None,
        topic_overlap_threshold: float = 0.18,
    ):
        self.hierarchy_ranks: Dict[str, int] = dict(hierarchy_ranks or DEFAULT_HIERARCHY_RANKS)
        self.topic_overlap_threshold = topic_overlap_threshold

    # ------------------------------------------------------------------ #
    # Hierarki
    # ------------------------------------------------------------------ #

    def get_hierarchy_rank(
        self,
        hierarchy_type: Optional[str],
        rank: Optional[int] = None,
    ) -> Optional[int]:
        """Rank dari database (jika tersedia) lebih diprioritaskan daripada peta bawaan."""
        if rank is not None:
            return rank
        if not hierarchy_type:
            return None

        token = hierarchy_type.upper()
        for alias, rank in HIERARCHY_ALIASES:
            if re.search(rf"(?<![A-Z]){re.escape(alias)}(?![A-Z])", token):
                return rank
        for label, value in self.hierarchy_ranks.items():
            if re.search(rf"(?<![A-Z]){re.escape(label)}(?![A-Z])", token):
                return value
        return None

    def rank_of(self, norm: LegalNorm) -> Optional[int]:
        return self.get_hierarchy_rank(norm.hierarchy_type, norm.hierarchy_rank)

    # ------------------------------------------------------------------ #
    # Aturan kontradiksi
    # ------------------------------------------------------------------ #

    def check_lex_superior(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        rank_a = self.rank_of(norm_a)
        rank_b = self.rank_of(norm_b)

        if rank_a is None or rank_b is None or rank_a >= rank_b:
            return None
        if not self.has_contradiction(norm_a.content, norm_b.content):
            return None

        return self._build(
            source=norm_a,
            target=norm_b,
            conflict_type=ConflictType.LEX_SUPERIOR,
            severity=Severity.HIGH,
            description=(
                f"{norm_a.hierarchy_type or 'Norma tingkat lebih tinggi'} "
                f"({norm_a.document_title} Pasal {norm_a.article_number}) mengalahkan aturan "
                f"{norm_b.hierarchy_type or 'norma tingkat lebih rendah'} "
                f"({norm_b.document_title} Pasal {norm_b.article_number})"
            ),
            recommended_action=(
                f"Cabut atau selaraskan Pasal {norm_b.article_number} {norm_b.document_title} "
                f"dengan ketentuan {norm_a.document_title} Pasal {norm_a.article_number}."
            ),
            evidence=[f"rank {norm_a.hierarchy_type}={rank_a} lebih tinggi dari {norm_b.hierarchy_type}={rank_b}"],
            meta_data={"rank_a": rank_a, "rank_b": rank_b},
        )

    def check_lex_specialis(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        if norm_a.domain != norm_b.domain:
            return None
        if not self.is_special_vs_general(norm_a, norm_b):
            return None
        # Penyimpangan kaidah khusus tidak selalu berupa kata negasi, cukup
        # Penyimpangan kaidah khusus tidak selalu berupa kata negasi; cukup
        if self.topic_overlap(norm_a.content, norm_b.content) < self.topic_overlap_threshold:
            return None

        return self._build(
            source=norm_a,
            target=norm_b,
            conflict_type=ConflictType.LEX_SPECIALIS,
            severity=Severity.MEDIUM,
            description=(
                f"Aturan khusus ({norm_a.document_title} Pasal {norm_a.article_number}) "
                f"menyimpangi aturan umum ({norm_b.document_title} Pasal {norm_b.article_number})"
            ),
            recommended_action=(
                "Tambahkan rujukan eksplisit pada aturan khusus yang menjadi pengecualian "
                "agar tidak terjadi tafsir ganda."
            ),
            meta_data={"domain": norm_a.domain},
        )

    def check_lex_posterior(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        date_a = self._parse_date(norm_a.effective_date)
        date_b = self._parse_date(norm_b.effective_date)
        if date_a is None or date_b is None or date_a <= date_b:
            return None

        rank_a = self.rank_of(norm_a)
        rank_b = self.rank_of(norm_b)
        if rank_a is not None and rank_b is not None and rank_a != rank_b:
            return None

        repealed = bool(self.marker_hits(norm_a.content, REPEAL_MARKERS))
        if not repealed and not self.has_contradiction(norm_a.content, norm_b.content):
            return None

        return self._build(
            source=norm_a,
            target=norm_b,
            conflict_type=ConflictType.LEX_POSTERIOR,
            severity=Severity.MEDIUM if repealed else Severity.HIGH,
            description=(
                f"Aturan yang lebih baru ({norm_a.document_title} Pasal {norm_a.article_number}, "
                f"berlaku {norm_a.effective_date}) menggantikan atau menyimpangi aturan lama "
                f"({norm_b.document_title} Pasal {norm_b.article_number}, "
                f"berlaku {norm_b.effective_date})"
            ),
            recommended_action=(
                f"Verifikasi dan cantumkan status berlaku Pasal {norm_b.article_number} "
                f"{norm_b.document_title} pada konsideran dan rujukan putusan."
            ),
            evidence=[f"tanggal berlaku {norm_a.effective_date} lebih baru dari {norm_b.effective_date}"],
            meta_data={
                "effective_date_a": norm_a.effective_date,
                "effective_date_b": norm_b.effective_date,
                "repeal_marker": repealed,
            },
        )

    def check_direct_contradiction(self, norm_a: LegalNorm, norm_b: LegalNorm) -> Optional[ConflictResult]:
        score = self.contradiction_score(norm_a.content, norm_b.content)
        if score < 0.45:
            return None

        return self._build(
            source=norm_a,
            target=norm_b,
            conflict_type=ConflictType.DIRECT_CONTRADICTION,
            severity=Severity.HIGH,
            description=(
                f"Bunyi Pasal {norm_a.article_number} {norm_a.document_title} saling meniadakan "
                f"dengan Pasal {norm_b.article_number} {norm_b.document_title}"
            ),
            recommended_action=(
                "Selaraskan redaksi kedua pasal atau nyatakan secara tegas mana yang berlaku."
            ),
            evidence=[f"contradiction_score={round(score, 2)}"],
        )

    # ------------------------------------------------------------------ #
    # Orkestrasi tingkat engine
    # ------------------------------------------------------------------ #

    def analyze_conflicts(
        self,
        new_norm: LegalNorm,
        existing_norms: List[LegalNorm],
    ) -> List[ConflictResult]:
        """Bandingkan satu norma baru dengan korpus.

        Satu pasang pasal menghasilkan maksimal satu temuan (berkeprioritas
        severity tertinggi) agar Conflict Matrix tidak berduplikasi.
        """
        results: Dict[str, ConflictResult] = {}

        for existing_norm in existing_norms:
            if existing_norm.id == new_norm.id:
                continue

            pair_conflicts: List[ConflictResult] = []
            for check_method in (self.check_lex_superior, self.check_lex_posterior):
                # Aturan hierarkis bersifat dua arah: draf bisa berada di atas
                # maupun di bawah kandidat, jadi keduanya diuji.
                conflict = check_method(new_norm, existing_norm) or check_method(
                    existing_norm, new_norm
                )
                if conflict:
                    pair_conflicts.append(conflict)

            for check_method in (self.check_lex_specialis, self.check_direct_contradiction):
                conflict = check_method(new_norm, existing_norm)
                if conflict:
                    pair_conflicts.append(conflict)

            if not pair_conflicts:
                continue

            pair_conflicts.sort(
                key=lambda item: SEVERITY_ORDER[item.severity.value],
                reverse=True,
            )
            best = pair_conflicts[0]
            if len(pair_conflicts) > 1:
                best.evidence = list(best.evidence) + [
                    f"temuan tambahan: {item.conflict_type.value}" for item in pair_conflicts[1:]
                ]

            key = self._pair_key(new_norm, existing_norm)
            current = results.get(key)
            if current is None or SEVERITY_ORDER[best.severity.value] > SEVERITY_ORDER[current.severity.value]:
                results[key] = best

        return sorted(
            results.values(),
            key=lambda item: SEVERITY_ORDER[item.severity.value],
            reverse=True,
        )

    # ------------------------------------------------------------------ #
    # Utilitas analisis teks (dipakai juga oleh domain services)
    # ------------------------------------------------------------------ #

    def marker_hits(self, text: str, markers: Set[str]) -> Set[str]:
        lowered = self._normalize(text)
        return {marker for marker in markers if marker in lowered}

    def has_prohibition(self, text: str) -> bool:
        return bool(self.marker_hits(text, PROHIBITION_MARKERS))

    def has_permission(self, text: str) -> bool:
        return bool(self.marker_hits(text, PERMISSION_MARKERS))

    def topic_overlap(self, text_a: str, text_b: str) -> float:
        set_a = set(self._extract_keywords(text_a))
        set_b = set(self._extract_keywords(text_b))
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def keywords(self, text: str, limit: int = 12) -> List[str]:
        """Kata kunci bermakna untuk pencarian keyword-based (fallback retrieval)."""
        return self._extract_keywords(text)[:limit]

    def has_contradiction(self, text_a: str, text_b: str) -> bool:
        """Kontradiksi lemah: topical overlap + benturan polaritas.

        Tanpa gerbang overlap, dua pasal yang tidak berkaitan yang kebetulan
        sama-sama memuat kata "tidak" akan dianggap bertentangan.
        """
        return self.contradiction_score(text_a, text_b) > 0.0

    def contradiction_score(self, text_a: str, text_b: str) -> float:
        overlap = self.topic_overlap(text_a, text_b)
        if overlap < self.topic_overlap_threshold:
            return 0.0

        prohibition_a, permission_a = self.has_prohibition(text_a), self.has_permission(text_a)
        prohibition_b, permission_b = self.has_prohibition(text_b), self.has_permission(text_b)

        score = 0.0
        if (prohibition_a and permission_b) or (permission_a and prohibition_b):
            score += 0.5
        if self.marker_hits(text_a, REPEAL_MARKERS) and not self.marker_hits(text_b, REPEAL_MARKERS):
            score += 0.3
        if score == 0.0:
            return 0.0
        return min(1.0, score + min(0.4, overlap))

    def is_special_vs_general(self, norm_a: LegalNorm, norm_b: LegalNorm) -> bool:
        content_a = self._normalize(norm_a.content)
        content_b = self._normalize(norm_b.content)
        specific = any(marker in content_a for marker in SPECIFIC_MARKERS)
        general = any(marker in content_b for marker in GENERAL_MARKERS)
        return specific and general

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #

    def _build(
        self,
        source: LegalNorm,
        target: LegalNorm,
        conflict_type: ConflictType,
        severity: Severity,
        description: str,
        recommended_action: str = "",
        evidence: Optional[List[str]] = None,
        meta_data: Optional[Dict] = None,
    ) -> ConflictResult:
        return ConflictResult(
            source_norm=source,
            target_norm=target,
            conflict_type=conflict_type,
            severity=severity,
            description=description,
            legal_basis=list(LEGAL_BASIS.get(conflict_type.value, [])),
            recommended_action=recommended_action,
            confidence=self.confidence(conflict_type, source, target),
            evidence=list(evidence or []),
            meta_data=meta_data or {},
        )

    def confidence(
        self,
        conflict_type: ConflictType,
        source: LegalNorm,
        target: LegalNorm,
    ) -> float:
        """Keyakinan rules-based: Lex Superior berdasar rank eksplisit paling tinggi."""
        if conflict_type == ConflictType.LEX_SUPERIOR and self.rank_of(source) is not None:
            return 0.9
        if conflict_type == ConflictType.LEX_POSTERIOR and source.effective_date and target.effective_date:
            return 0.85
        if conflict_type == ConflictType.DIRECT_CONTRADICTION:
            return 0.6
        return 0.5

    def _pair_key(self, norm_a: LegalNorm, norm_b: LegalNorm) -> str:
        return "|".join(sorted([str(norm_a.id), str(norm_b.id)]))

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").lower()).strip()

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r"\b\w+\b", self._normalize(text))
        return [word for word in words if len(word) > 3 and word not in STOPWORDS]

    def _parse_date(self, date_str: Optional[str]):
        if not date_str:
            return None
        from datetime import datetime

        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None


lex_integrity_engine = LexIntegrityEngine()
