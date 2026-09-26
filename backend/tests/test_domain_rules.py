"""Unit tests untuk aturan domain (Hukum Tata Negara, Pidana, Perdata)
yang diperkuat dengan aturan domain dari engine Lex Integrity.

Jalankan dari folder backend:
    pytest tests/test_domain_rules.py -q
"""

import pytest

from app.engine.lex_integrity import (
    ConflictType,
    LegalNorm,
    Severity,
    lex_integrity_engine,
)
from app.services.legal_domains import CivilLawService, CriminalLawService, HTNService
from app.services.lex_integrity_service import AnalysisOutcome, LexIntegrityService


def make_norm(**overrides) -> LegalNorm:
    base = {
        "id": "00000000-0000-0000-0000-0000000000aa",
        "document_title": "UU No. 1 Tahun 2023",
        "article_number": "1",
        "content": "Tiada suatu tindak pidana yang tidak dipidana.",
        "domain": "PIDANA",
        "hierarchy_type": "UU",
        "hierarchy_rank": 3,
    }
    base.update(overrides)
    return LegalNorm(**base)


class TestCriminalDelictOverlap:
    def setup_method(self):
        self.service = CriminalLawService(db=None)

    def test_no_penalty_provision_returns_empty(self):
        norm = make_norm(content="Ketentuan ini mengatur prosedur pengajuan berkas.")
        assert self.service.detect_delict_overlap(norm, []) == []

    def test_overlapping_penalty_detected(self):
        norm = make_norm(
            content="Setiap orang yang menyalahgunakan wewenang, dipidana dengan pidana lima tahun.",
        )
        candidate = make_norm(
            id="00000000-0000-0000-0000-0000000000bb",
            document_title="Perda Criminal",
            content="Menyalahgunakan wewenang, dipidana dengan pidana lima tahun.",
        )
        results = self.service.detect_delict_overlap(norm, [candidate])
        assert len(results) == 1
        assert results[0].conflict_type == ConflictType.ANATOMIE_DELICT_OVERLAP
        assert results[0].severity in (Severity.MEDIUM, Severity.HIGH)
        assert results[0].legal_basis

    def test_unrelated_candidate_skipped(self):
        norm = make_norm(content="Memberikan upeti dipidana dengan pidana satu tahun.")
        candidate = make_norm(
            id="00000000-0000-0000-0000-0000000000cc",
            content="Pengaturan tarif pada persetujuan importir tidak berkaitan dengan pidana.",
        )
        assert self.service.detect_delict_overlap(norm, [candidate]) == []

    def test_candidate_without_penalty_skipped(self):
        norm = make_norm(content="Menyalahgunakan wewenang, dipidana dengan pidana lima tahun.")
        candidate = make_norm(
            id="00000000-0000-0000-0000-0000000000dd",
            content="Penyusunan pedoman teknis administratif pemerintahan daerah.",
        )
        assert self.service.detect_delict_overlap(norm, [candidate]) == []


class TestCivilStandardClause:
    def setup_method(self):
        self.service = CivilLawService(db=None)

    def test_exoneration_clause_detected(self):
        norm = make_norm(
            domain="PERDATA",
            content="Penyedia bebas tanggung jawab atas kerusakan barang yang rusak.",
        )
        results = self.service.detect_standard_clause_conflicts(norm)
        assert len(results) == 1
        conflict = results[0]
        assert conflict.conflict_type == ConflictType.KLAUSULA_BAKU_TIDAK_SAH
        assert conflict.severity == Severity.HIGH
        assert conflict.target_norm.document_title == "KUHPerdata"
        assert conflict.target_norm.article_number == "1337"
        assert conflict.target_norm.id.startswith("statute:")

    def test_unilateral_termination_detected(self):
        norm = make_norm(
            domain="PERDATA",
            content="Para pihak bebas membatalkan perjanjian ini kapan saja tanpa pemberitahuan.",
        )
        results = self.service.detect_standard_clause_conflicts(norm)
        assert results[0].conflict_type == ConflictType.KLAUSULA_BAKU_TIDAK_SAH
        assert results[0].meta_data["issue_type"] == "pembatalan_sepihak"

    def test_clean_clause_returns_empty(self):
        norm = make_norm(
            domain="PERDATA",
            content="Para pihak wajib melaksanakan pembayaran pada tanggal yang telah disepakati.",
        )
        assert self.service.detect_standard_clause_conflicts(norm) == []


class TestCivilAgreementValidity:
    def setup_method(self):
        self.service = CivilLawService(db=None)

    def test_missing_requirements_detected(self):
        norm = make_norm(
            domain="PERDATA",
            content="Perjanjian dibuat dengan para pihak menyepakati jangka waktu tiga tahun.",
        )
        results = self.service.detect_agreement_validity_conflicts(norm)
        assert len(results) == 1
        assert results[0].conflict_type == ConflictType.SYARAT_PERJANJIAN_TIDAK_TERPENUHI
        assert results[0].target_norm.article_number == "1320"
        assert "cakap_hukum" in results[0].meta_data["missing_requirements"]

    def test_complete_agreement_returns_empty(self):
        norm = make_norm(
            domain="PERDATA",
            content=(
                "Perjanjian kerja yang dibuat setelah para pihak sepakat, para pihak cakap hukum, "
                "memuat hal tertentu dan tidak bertentangan dengan ketertiban umum."
            ),
        )
        assert self.service.detect_agreement_validity_conflicts(norm) == []

    def test_non_agreement_text_returns_empty(self):
        norm = make_norm(domain="PERDATA", content="Pengaturan sistem informasi pada server internal.")
        assert self.service.detect_agreement_validity_conflicts(norm) == []


class TestHTNService:
    def test_validate_hierarchy_uses_engine(self):
        service = HTNService(db=None)
        lower = make_norm(
            domain="HTN",
            document_title="Perda No. 1 Tahun 2026",
            hierarchy_type="PERDA",
            hierarchy_rank=7,
            content="Gubernur dapat membatalkan peraturan kepala daerah yang lebih tinggi.",
        )
        higher = make_norm(
            domain="HTN",
            document_title="UU No. 12 Tahun 2011",
            article_number="7",
            content="Gubernur dilarang membatalkan peraturan yang lebih tinggi tanpa dasar hukum.",
        )
        engine_result = service.engine.check_lex_superior(higher, lower)
        assert engine_result is not None
        assert engine_result.conflict_type == ConflictType.LEX_SUPERIOR


class TestServiceComposition:
    def setup_method(self):
        self.service = LexIntegrityService(db=None)

    def test_filter_and_sort_by_severity(self):
        conflicts = self.service.engine.analyze_conflicts(
            make_norm(
                id="00000000-0000-0000-0000-0000000000ee",
                document_title="Perda No. 2 Tahun 2026",
                hierarchy_type="PERDA",
                hierarchy_rank=7,
                content="Gubernur dapat membatalkan peraturan yang lebih tinggi tanpa dasar hukum.",
            ),
            [
                make_norm(
                    domain="HTN",
                    document_title="UU No. 12 Tahun 2011",
                    article_number="7",
                    hierarchy_type="UU",
                    hierarchy_rank=3,
                    content="Gubernur dilarang membatalkan peraturan yang lebih tinggi tanpa dasar hukum.",
                )
            ],
        )
        assert conflicts
        filtered = self.service._filter_and_sort(conflicts, "HIGH")
        assert all(item.severity == Severity.HIGH for item in filtered)
        assert [item.severity for item in filtered] == sorted(
            [item.severity for item in filtered],
            key=lambda item: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[item.value],
            reverse=True,
        )

    def test_filter_by_low_keeps_all(self):
        conflicts = self.service.engine.analyze_conflicts(
            make_norm(
                id="00000000-0000-0000-0000-0000000000ff",
                document_title="Perda No. 3 Tahun 2026",
                hierarchy_type="PERDA",
                hierarchy_rank=7,
                content="Gubernur dapat membatalkan peraturan yang lebih tinggi tanpa dasar hukum.",
            ),
            [
                make_norm(
                    domain="HTN",
                    document_title="UU No. 12 Tahun 2011",
                    article_number="7",
                    hierarchy_type="UU",
                    hierarchy_rank=3,
                    content="Gubernur dilarang membatalkan peraturan yang lebih tinggi tanpa dasar hukum.",
                )
            ],
        )
        assert len(self.service._filter_and_sort(conflicts, "LOW")) == len(conflicts)

    def test_domain_rules_appended_for_perdata(self):
        norm = make_norm(
            domain="PERDATA",
            content="Perjanjian ini dimulai dengan klausula bebas tanggung jawab atas kerusakan.",
        )
        result = self.service._apply_domain_rules(norm, [], [], "PERDATA")
        assert any(
            item.conflict_type == ConflictType.KLAUSULA_BAKU_TIDAK_SAH for item in result
        )

    def test_domain_rules_not_applied_for_htn(self):
        norm = make_norm(domain="HTN", content="Ketentuan mengenai tata kelola dokumen.")
        result = self.service._apply_domain_rules(norm, [], [], "HTN")
        assert result == []

    def test_outcome_to_dict_shape(self):
        outcome = AnalysisOutcome(
            analysis_id="11111111-1111-1111-1111-111111111111",
            domain="HTN",
            source_article_id="22222222-2222-2222-2222-222222222222",
            candidates_evaluated=5,
            candidate_count=5,
            retrieval_mode="keyword",
            latency_ms=12,
        )
        payload = outcome.to_dict()
        assert payload["has_conflict"] is False
        assert payload["highest_severity"] is None
        assert payload["engine_trace"]["retrieval_mode"] == "keyword"
        assert payload["engine_trace"]["candidates_evaluated"] == 5
