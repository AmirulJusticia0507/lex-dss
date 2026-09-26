"""Orkestrator Lex Integrity yang terhubung ke database.

Tanggung jawab:
1. Mengubah baris `legal_articles` menjadi `LegalNorm` (rank/type dari `legal_hierarchy`).
2. Mengumpulkan kandidat kandidat perbandingan (hybrid search bila embedding tersedia,
   keyword search bila tidak).
3. Menjalankan rules engine + aturan spesifik domain (HTN/Pidana/Perdata).
4. Menyimpan temuan ke tabel `norm_conflicts` agar dapat divisualisasikan sebagai Conflict Matrix.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.engine.lex_integrity import (
    ConflictResult,
    ConflictType,
    LegalNorm,
    LexIntegrityEngine,
    SEVERITY_ORDER,
    lex_integrity_engine,
)
from app.models.legal import LegalArticle, LegalHierarchy, NormConflict
from app.services.legal_domains import CivilLawService, CriminalLawService, HTNService


DOMAIN_RULES = {
    "HTN": ["RANK_COMPARISON", "DIRECT_CONTRADICTION_DETECTION", "EXPLICIT_REPEAL_CHECK"],
    "PIDANA": [
        "RANK_COMPARISON",
        "DIRECT_CONTRADICTION_DETECTION",
        "EXPLICIT_REPEAL_CHECK",
        "ANATOMIE_DELICT_OVERLAP",
        "LEGALITY_SANCTION_CHECK",
    ],
    "PERDATA": [
        "RANK_COMPARISON",
        "DIRECT_CONTRADICTION_DETECTION",
        "EXPLICIT_REPEAL_CHECK",
        "STANDARD_CLAUSE_CHECK",
        "AGREEMENT_VALIDITY_CHECK",
    ],
}


@dataclass
class AnalysisOutcome:
    analysis_id: str
    domain: str
    source_article_id: str
    conflicts: List[ConflictResult] = field(default_factory=list)
    candidates_evaluated: int = 0
    candidate_count: int = 0
    rules_applied: List[str] = field(default_factory=list)
    retrieval_mode: str = "none"
    latency_ms: int = 0
    persisted_conflict_ids: List[str] = field(default_factory=list)

    @property
    def has_conflict(self) -> bool:
        return bool(self.conflicts)

    @property
    def highest_severity(self) -> Optional[str]:
        if not self.conflicts:
            return None
        return self.conflicts[0].severity.value

    def to_dict(self) -> Dict:
        return {
            "analysis_id": self.analysis_id,
            "domain": self.domain,
            "source_article_id": self.source_article_id,
            "has_conflict": self.has_conflict,
            "conflict_count": len(self.conflicts),
            "highest_severity": self.highest_severity,
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
            "engine_trace": {
                "candidates_evaluated": self.candidates_evaluated,
                "candidate_count": self.candidate_count,
                "retrieval_mode": self.retrieval_mode,
                "rules_applied": self.rules_applied,
                "latency_ms": self.latency_ms,
            },
            "persisted_conflict_ids": self.persisted_conflict_ids,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


class LexIntegrityService:
    def __init__(
        self,
        db: AsyncSession,
        engine: Optional[LexIntegrityEngine] = None,
    ):
        self.db = db
        self.engine = engine or lex_integrity_engine
        self.htn = HTNService(db)
        self.criminal = CriminalLawService(db)
        self.civil = CivilLawService(db)

    # ------------------------------------------------------------------ #
    # Konversi & referensi
    # ------------------------------------------------------------------ #

    async def hierarchy_map(self) -> Dict[int, LegalHierarchy]:
        result = await self.db.execute(select(LegalHierarchy))
        return {row.id: row for row in result.scalars().all()}

    def article_to_norm(
        self,
        article: LegalArticle,
        hierarchy_map: Optional[Dict[int, LegalHierarchy]] = None,
    ) -> LegalNorm:
        meta = article.meta_data or {}
        hierarchy = None
        if article.hierarchy_id and hierarchy_map is not None:
            hierarchy = hierarchy_map.get(article.hierarchy_id)

        return LegalNorm(
            id=str(article.id),
            document_title=article.document_title,
            article_number=article.article_number,
            content=article.content,
            domain=article.domain,
            hierarchy_rank=hierarchy.rank if hierarchy else None,
            hierarchy_type=hierarchy.type_name if hierarchy else None,
            effective_date=meta.get("effective_date") or meta.get("berlaku"),
            source_url=meta.get("source_url"),
        )

    async def get_article(self, article_id: uuid.UUID) -> Optional[LegalArticle]:
        result = await self.db.execute(
            select(LegalArticle)
            .options(selectinload(LegalArticle.hierarchy))
            .where(LegalArticle.id == article_id)
        )
        return result.scalars().first()

    # ------------------------------------------------------------------ #
    # Draft / sumber analisis
    # ------------------------------------------------------------------ #

    async def ensure_source_article(
        self,
        text: str,
        domain: str,
        article_id: Optional[uuid.UUID] = None,
        draft_type: Optional[str] = None,
        draft_label: Optional[str] = None,
    ) -> LegalArticle:
        """Untuk analisis teks bebas, draf disimpan sebagai `legal_articles` agar
        hasilnya dapat ditelusuri lewat Conflict Matrix dan audit trail."""
        if article_id:
            article = await self.get_article(article_id)
            if article:
                return article

        hierarchy_id = None
        if draft_type:
            result = await self.db.execute(
                select(LegalHierarchy).where(
                    LegalHierarchy.type_name.ilike(f"%{draft_type}%")
                )
            )
            hierarchy = result.scalars().first()
            hierarchy_id = hierarchy.id if hierarchy else None

        title = draft_label or f"Draf Analisis Lex Integrity {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        meta_data = {
            "is_draft": True,
            "draft_type": draft_type,
            "status": "DRAFT_ANALYSIS",
            "source": "lex-dss.analysis.conflict",
        }

        article = LegalArticle(
            document_title=title,
            article_number="DRAFT",
            content=text,
            domain=domain,
            hierarchy_id=hierarchy_id,
            meta_data=meta_data,
        )
        self.db.add(article)
        await self.db.flush()
        return article

    # ------------------------------------------------------------------ #
    # Retrieval kandidat
    # ------------------------------------------------------------------ #

    async def collect_candidates(
        self,
        text: str,
        domain: str,
        top_k: int = 20,
        target_article_ids: Optional[List[uuid.UUID]] = None,
    ) -> Tuple[List[LegalArticle], str]:
        """Hybrid search (embedding) dengan fallback keyword search."""
        if target_article_ids:
            result = await self.db.execute(
                select(LegalArticle).where(LegalArticle.id.in_(target_article_ids))
            )
            articles = list(result.scalars().all())
            if articles:
                return articles, "explicit_ids"

        from app.engine.rag import hybrid_search

        try:
            pairs = await hybrid_search(
                db=self.db,
                query=text,
                domain=domain,
                top_k=top_k,
            )
            if pairs:
                return [article for article, _ in pairs], "hybrid_vector_keyword"
        except Exception:
            pass

        keywords = self.engine.keywords(text, limit=8)
        if not keywords:
            return [], "none"

        conditions = [
            LegalArticle.content.ilike(f"%{keyword}%") for keyword in keywords
        ]
        conditions.append(
            or_(*[LegalArticle.document_title.ilike(f"%{keyword}%") for keyword in keywords])
        )
        statement = select(LegalArticle).where(or_(*conditions))
        if domain:
            statement = statement.where(LegalArticle.domain == domain)
        statement = statement.limit(top_k)

        result = await self.db.execute(statement)
        return list(result.scalars().all()), "keyword"

    # ------------------------------------------------------------------ #
    # Analisis
    # ------------------------------------------------------------------ #

    async def analyze_text(
        self,
        text: str,
        domain: str,
        input_article_id: Optional[uuid.UUID] = None,
        draft_type: Optional[str] = None,
        draft_label: Optional[str] = None,
        target_article_ids: Optional[List[uuid.UUID]] = None,
        min_severity: str = "LOW",
        top_k: int = 20,
        save_result: bool = True,
    ) -> AnalysisOutcome:
        started = time.perf_counter()

        domain = (domain or "HTN").upper()
        source_article = await self.ensure_source_article(
            text=text,
            domain=domain,
            article_id=input_article_id,
            draft_type=draft_type,
            draft_label=draft_label,
        )

        hierarchy_map = await self.hierarchy_map()
        new_norm = self.article_to_norm(source_article, hierarchy_map)

        candidates, retrieval_mode = await self.collect_candidates(
            text=text,
            domain=domain,
            top_k=top_k,
            target_article_ids=target_article_ids,
        )

        candidate_norms = [
            self.article_to_norm(article, hierarchy_map)
            for article in candidates
            if str(article.id) != str(source_article.id)
        ]

        conflicts = self.engine.analyze_conflicts(new_norm, candidate_norms)
        conflicts = self._apply_domain_rules(new_norm, candidate_norms, conflicts, domain)
        conflicts = self._filter_and_sort(conflicts, min_severity)

        outcome = AnalysisOutcome(
            analysis_id=str(uuid.uuid4()),
            domain=domain,
            source_article_id=str(source_article.id),
            conflicts=conflicts,
            candidates_evaluated=len(candidate_norms),
            candidate_count=len(candidates),
            rules_applied=DOMAIN_RULES.get(domain, []),
            retrieval_mode=retrieval_mode,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

        if save_result and conflicts:
            outcome.persisted_conflict_ids = await self.persist(source_article, conflicts)

        return outcome

    async def analyze_article(
        self,
        article: LegalArticle,
        domain: Optional[str] = None,
        min_severity: str = "LOW",
        top_k: int = 20,
        save_result: bool = True,
    ) -> AnalysisOutcome:
        return await self.analyze_text(
            text=article.content,
            domain=domain or article.domain or "HTN",
            input_article_id=article.id,
            min_severity=min_severity,
            top_k=top_k,
            save_result=save_result,
        )

    def _apply_domain_rules(
        self,
        new_norm: LegalNorm,
        candidate_norms: List[LegalNorm],
        base_conflicts: List[ConflictResult],
        domain: str,
    ) -> List[ConflictResult]:
        if domain == "PIDANA":
            base_conflicts = base_conflicts + self.criminal.detect_delict_overlap(
                new_norm, candidate_norms
            )
        elif domain == "PERDATA":
            base_conflicts = base_conflicts + self.civil.detect_standard_clause_conflicts(new_norm)
            base_conflicts = base_conflicts + self.civil.detect_agreement_validity_conflicts(new_norm)

        unique: Dict[tuple, ConflictResult] = {}
        for conflict in base_conflicts:
            key = (
                conflict.source_norm.id,
                conflict.target_norm.id,
                conflict.conflict_type.value,
            )
            current = unique.get(key)
            if current is None or SEVERITY_ORDER[conflict.severity.value] > SEVERITY_ORDER[current.severity.value]:
                unique[key] = conflict

        return list(unique.values())

    def _filter_and_sort(
        self,
        conflicts: List[ConflictResult],
        min_severity: str,
    ) -> List[ConflictResult]:
        threshold = SEVERITY_ORDER.get((min_severity or "LOW").upper(), 1)
        filtered = [
            conflict
            for conflict in conflicts
            if SEVERITY_ORDER[conflict.severity.value] >= threshold
        ]
        return sorted(
            filtered,
            key=lambda item: SEVERITY_ORDER[item.severity.value],
            reverse=True,
        )

    # ------------------------------------------------------------------ #
    # Persistensi
    # ------------------------------------------------------------------ #

    async def _ensure_statute_article(self, norm: LegalNorm) -> uuid.UUID:
        """Norma acuan dari domain rule (mis. KUHPerdata Pasal 1337) disimpan sebagai
        `legal_articles` agar Conflict Matrix tetap punya node yang valid."""
        result = await self.db.execute(
            select(LegalArticle).where(
                LegalArticle.document_title == norm.document_title,
                LegalArticle.article_number == norm.article_number,
            )
        )
        article = result.scalars().first()
        if article:
            return article.id

        article = LegalArticle(
            document_title=norm.document_title,
            article_number=norm.article_number,
            content=norm.content,
            domain=norm.domain,
            meta_data={"is_statute_reference": True, "source": "lex-dss.domain_rules"},
        )
        self.db.add(article)
        await self.db.flush()
        return article.id

    async def _resolve_article_id(self, norm: LegalNorm) -> uuid.UUID:
        try:
            return uuid.UUID(str(norm.id))
        except (AttributeError, TypeError, ValueError):
            return await self._ensure_statute_article(norm)

    async def persist(
        self,
        source_article: LegalArticle,
        conflicts: List[ConflictResult],
    ) -> List[str]:
        saved: List[str] = []

        for conflict in conflicts:
            payload = conflict.to_dict()
            row = NormConflict(
                source_article_id=await self._resolve_article_id(conflict.source_norm),
                target_article_id=await self._resolve_article_id(conflict.target_norm),
                conflict_type=conflict.conflict_type.value,
                severity=conflict.severity.value,
                description=conflict.description,
                status="OPEN",
                meta_data={
                    "legal_basis": payload["legal_basis"],
                    "recommended_action": payload["recommended_action"],
                    "confidence": payload["confidence"],
                    "evidence": payload["evidence"],
                    "analysis": payload["meta_data"],
                },
            )
            self.db.add(row)
            await self.db.flush()
            conflict.persisted_id = str(row.id)
            saved.append(str(row.id))

        return saved

    # ------------------------------------------------------------------ #
    # Validasi hierarki eksplisit
    # ------------------------------------------------------------------ #

    async def validate_hierarchy(
        self,
        lower: LegalArticle,
        upper: LegalArticle,
    ) -> Dict:
        hierarchy_map = await self.hierarchy_map()
        lower_norm = self.article_to_norm(lower, hierarchy_map)
        upper_norm = self.article_to_norm(upper, hierarchy_map)

        conflict = self.engine.check_lex_superior(upper_norm, lower_norm)
        if not conflict:
            conflict = self.engine.check_direct_contradiction(upper_norm, lower_norm)

        rank_lower = self.engine.rank_of(lower_norm)
        rank_upper = self.engine.rank_of(upper_norm)

        if conflict:
            return {
                "valid": False,
                "hierarchy_relation": "CONTRADICTS_SUPERIOR",
                "rank_lower": rank_lower,
                "rank_upper": rank_upper,
                "violations": [
                    {
                        "code": conflict.conflict_type.value,
                        "severity": conflict.severity.value,
                        "explanation": conflict.description,
                        "legal_basis": conflict.legal_basis,
                    }
                ],
                "recommendation": conflict.recommended_action,
            }

        if rank_lower is None or rank_upper is None:
            relation = "UNKNOWN_HIERARCHY"
        elif rank_upper < rank_lower:
            relation = "COMPATIBLE"
        elif rank_upper == rank_lower:
            relation = "SAME_LEVEL"
        else:
            relation = "INVERTED_HIERARCHY"

        return {
            "valid": relation == "COMPATIBLE",
            "hierarchy_relation": relation,
            "rank_lower": rank_lower,
            "rank_upper": rank_upper,
            "violations": [],
            "recommendation": (
                "Tidak ditemukan pertentangan bunyi antara kedua norma pada analisis otomatis."
            ),
        }

    # ------------------------------------------------------------------ #
    # Graph Conflict Matrix
    # ------------------------------------------------------------------ #

    async def conflict_graph(self, article_id: uuid.UUID) -> Dict:
        incoming_result = await self.db.execute(
            select(NormConflict)
            .options(selectinload(NormConflict.target_article))
            .where(NormConflict.source_article_id == article_id)
        )
        outgoing_result = await self.db.execute(
            select(NormConflict)
            .options(selectinload(NormConflict.source_article))
            .where(NormConflict.target_article_id == article_id)
        )

        incoming_rows = list(incoming_result.scalars().all())
        outgoing_rows = list(outgoing_result.scalars().all())

        nodes: Dict[str, Dict] = {}
        edges: List[Dict] = []

        def add_node(article: Optional[LegalArticle], relation: str) -> None:
            if article is None:
                return
            node_id = str(article.id)
            nodes[node_id] = {
                "id": node_id,
                "label": f"{article.document_title} Pasal {article.article_number}",
                "relation": relation,
            }

        for row in incoming_rows:
            add_node(row.target_article, "incoming")
            edges.append(self._edge(row))

        for row in outgoing_rows:
            add_node(row.source_article, "outgoing")
            edges.append(self._edge(row))

        severities = [edge["severity"] for edge in edges]
        highest = max(severities, key=lambda item: SEVERITY_ORDER[item]) if severities else None

        return {
            "article_id": str(article_id),
            "nodes": list(nodes.values()),
            "edges": edges,
            "summary": {
                "incoming": len(incoming_rows),
                "outgoing": len(outgoing_rows),
                "highest_severity": highest,
            },
        }

    def _edge(self, row: NormConflict) -> Dict:
        return {
            "id": str(row.id),
            "source": str(row.source_article_id),
            "target": str(row.target_article_id),
            "conflict_type": row.conflict_type,
            "severity": row.severity,
            "status": row.status,
            "description": row.description,
        }
