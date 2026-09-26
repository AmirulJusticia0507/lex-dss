"""Unit tests untuk Lex Integrity rules engine.

Jalankan dari folder backend:
    pytest tests/test_lex_integrity.py -q
"""

import pytest

from app.engine.lex_integrity import (
    ConflictType,
    LegalNorm,
    LexIntegrityEngine,
    Severity,
    lex_integrity_engine,
)


def make_norm(**overrides) -> LegalNorm:
    base = {
        "id": "00000000-0000-0000-0000-000000000001",
        "document_title": "UU No. 12 Tahun 2011",
        "article_number": "7",
        "content": "Peraturan perundang-undangan yang lebih rendah tidak boleh bertentangan.",
        "domain": "HTN",
        "hierarchy_type": "UU",
        "hierarchy_rank": 3,
    }
    base.update(overrides)
    return LegalNorm(**base)


class TestHierarchyRank:
    def test_rank_from_database_wins(self):
        engine = LexIntegrityEngine()
        assert engine.get_hierarchy_rank("PERDA", 7) == 7
        assert engine.get_hierarchy_rank(None, 4) == 4

    def test_rank_from_type_name(self):
        engine = LexIntegrityEngine()
        assert engine.get_hierarchy_rank("UU") == 3
        assert engine.get_hierarchy_rank("Perda Provinsi") == 7
        assert engine.get_hierarchy_rank("Peraturan Presiden") == 5

    def test_rank_does_not_match_inside_word(self):
        engine = LexIntegrityEngine()
        # "PERWALI" tidak boleh tertukar dengan label lain, dan label acak tidak
        # boleh cocok hanya karena substring.
        assert engine.get_hierarchy_rank("PERWALI") == 9
        assert engine.get_hierarchy_rank("PERATURAN MENTERI KEHUTANAN") == 6
        assert engine.get_hierarchy_rank("XYZ") is None
        assert engine.get_hierarchy_rank(None) is None

    def test_custom_rank_map(self):
        engine = LexIntegrityEngine(hierarchy_ranks={"AKTA": 1})
        assert engine.get_hierarchy_rank("AKTA KOTA") == 1


class TestContradictionDetection:
    def test_overlap_gate_blocks_unrelated_text(self):
        engine = lex_integrity_engine
        unrelated_a = "Ketentuan mengenai pencatatan energi listrik."
        unrelated_b = "Prosedur pengajuan perizinan usaha melalui OSS."
        assert engine.has_contradiction(unrelated_a, unrelated_b) is False
        assert engine.contradiction_score(unrelated_a, unrelated_b) == 0.0

    def test_prohibition_versus_permission(self):
        engine = lex_integrity_engine
        a = "Gubernur dilarang membatalkan peraturan kepala daerah kabupaten dan kota."
        b = "Gubernur dapat membatalkan peraturan kepala daerah kabupaten dan kota."
        assert engine.has_contradiction(a, b) is True
        assert engine.contradiction_score(a, b) >= 0.5

    def test_repeal_marker_counts_as_contradiction(self):
        engine = lex_integrity_engine
        a = "Pasal ini dicabut dan tidak berlaku sejak tanggal_Status xx."
        b = "Pasal ini masih berlaku dan mengatur perizinan berusaha."
        assert engine.has_contradiction(a, b) is True

    def test_topic_overlap_range(self):
        engine = lex_integrity_engine
        assert engine.topic_overlap("izin usaha", "") == 0.0
        assert engine.topic_overlap("izin usaha", "izin usaha") == 1.0

    def test_keywords_excludes_stopwords(self):
        engine = lex_integrity_engine
        keywords = engine.keywords("yang tidak dapat dengan dari pada usaha dagang", limit=5)
        assert "yang" not in keywords
        assert "dengan" not in keywords


class TestLexSuperior:
    def test_lower_norm_contradicting_higher_norm(self):
        engine = lex_integrity_engine
        higher = make_norm(
            id="11111111-1111-1111-1111-111111111111",
            document_title="UU No. 12 Tahun 2011",
            article_number="7",
            content="Peraturan yang lebih rendah tidak boleh bertentangan dengan peraturan yang lebih tinggi.",
        )
        lower = make_norm(
            id="22222222-2222-2222-2222-222222222222",
            document_title="Perda Kota Bandung No. 3 Tahun 2024",
            article_number="24",
            hierarchy_type="PERDA",
            hierarchy_rank=7,
            content="Gubernur dapat membatalkan peraturan yang lebih tinggi tanpa persetujuan menteri.",
        )

        result = engine.check_lex_superior(higher, lower)
        assert result is not None
        assert result.conflict_type == ConflictType.LEX_SUPERIOR
        assert result.severity == Severity.HIGH
        assert result.confidence == 0.9
        assert result.legal_basis
        assert "Pasal 7 ayat (1)" in result.legal_basis[0]

    def test_same_rank_is_not_superior(self):
        engine = lex_integrity_engine
        a = make_norm(content="Gubernur dapat mencabut peraturan daerah.")
        b = make_norm(id="33333333-3333-3333-3333-333333333333", content="Gubernur tidak boleh mencabut peraturan daerah.")
        assert engine.check_lex_superior(a, b) is None

    def test_missing_rank_is_skipped(self):
        engine = lex_integrity_engine
        a = make_norm(hierarchy_rank=None, hierarchy_type="DOKUMEN INTERN")
        b = make_norm(id="44444444-4444-4444-4444-444444444444", hierarchy_type="PERDA", hierarchy_rank=7)
        assert engine.check_lex_superior(a, b) is None


class TestLexPosterior:
    def test_newer_norm_with_repeal(self):
        engine = lex_integrity_engine
        newer = make_norm(
            id="55555555-5555-5555-5555-555555555555",
            document_title="Perppu No. 2 Tahun 2025",
            hierarchy_type="PERPPU",
            effective_date="2025-01-10",
            content="Peraturan yang sebelumnya mengatur perizinan usaha dicabut.",
        )
        older = make_norm(
            id="66666666-6666-6666-6666-666666666666",
            hierarchy_type="PERPPU",
            effective_date="2020-05-01",
            content="Perizinan usaha tersebut masih berlaku dan wajib dipenuhi.",
        )

        result = engine.check_lex_posterior(newer, older)
        assert result is not None
        assert result.conflict_type == ConflictType.LEX_POSTERIOR
        assert result.severity == Severity.MEDIUM
        assert result.confidence == 0.85

    def test_older_norm_does_not_win(self):
        engine = lex_integrity_engine
        newer = make_norm(
            id="77777777-7777-7777-7777-777777777777",
            effective_date="2020-01-01",
        )
        older = make_norm(
            id="88888888-8888-8888-8888-888888888888",
            effective_date="2024-01-01",
        )
        assert engine.check_lex_posterior(newer, older) is None

    def test_different_rank_is_handled_by_superior(self):
        engine = lex_integrity_engine
        newer_lower = make_norm(
            id="99999999-9999-9999-9999-999999999999",
            hierarchy_type="PERDA",
            hierarchy_rank=7,
            effective_date="2025-01-01",
            content="Perda baru mengatur perizinan yang berbeda dari peraturan lama.",
        )
        older_higher = make_norm(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            hierarchy_type="UU",
            hierarchy_rank=3,
            effective_date="2020-01-01",
            content="Peraturan lama mengatur perizinan yang tidak boleh diubah.",
        )
        assert engine.check_lex_posterior(newer_lower, older_higher) is None


class TestLexSpecialis:
    def test_specific_versus_general(self):
        engine = lex_integrity_engine
        specific = make_norm(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            content="Perda ini berlaku khusus untuk perizinan pertambangan.",
        )
        general = make_norm(
            id="cccccccc-cccc-cccc-cccc-cccccccccccc",
            content="Secara umum, pengaturan perizinan berlaku bagi semua pihak.",
        )
        result = engine.check_lex_specialis(specific, general)
        assert result is not None
        assert result.conflict_type == ConflictType.LEX_SPECIALIS
        assert result.severity == Severity.MEDIUM

    def test_different_domain_is_skipped(self):
        engine = lex_integrity_engine
        specific = make_norm(id="dddddddd-dddd-dddd-dddd-dddddddddddd", domain="PIDANA", content="Ketentuan khusus yang berlaku bagi semua pihak.")
        general = make_norm(id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", domain="PERDATA", content="Secara umum ketentuan ini berlaku.")
        assert engine.check_lex_specialis(specific, general) is None


class TestDirectContradiction:
    def test_strong_contradiction_detected(self):
        engine = lex_integrity_engine
        a = make_norm(id="ffffffff-ffff-ffff-ffff-ffffffffffff", content="Penyetoran retribusi pajak dilarang bagi setiap wajib pajak.")
        b = make_norm(
            id="12121212-1212-1212-1212-121212121212",
            document_title="Perda ketentuan umum",
            content="Penyetoran retribusi pajak dapat dilakukan oleh setiap wajib pajak.",
        )
        result = engine.check_direct_contradiction(a, b)
        assert result is not None
        assert result.conflict_type == ConflictType.DIRECT_CONTRADICTION
        assert result.severity == Severity.HIGH
        assert result.confidence == 0.6


class TestAnalyzeConflicts:
    def test_dedupe_per_pair_and_sort_by_severity(self):
        engine = lex_integrity_engine
        new_norm = make_norm(
            id="13131313-1313-1313-1313-131313131313",
            document_title="Perda No. 1 Tahun 2026",
            hierarchy_type="PERDA",
            hierarchy_rank=7,
            content="Gubernur dapat membatalkan peraturan kepala daerah yang lebih tinggi tanpa persetujuan.",
        )
        candidates = [
            make_norm(
                id="14141414-1414-1414-1414-141414141414",
                content="Gubernur dilarang membatalkan peraturan kepala daerah yang lebih tinggi.",
            ),
            make_norm(
                id="15151515-1515-1515-1515-151515151515",
                document_title="Perda_No_Relevan",
                content="Pengaturan tarif energi tidak berkaitan dengan pembatalan peraturan.",
            ),
        ]

        results = engine.analyze_conflicts(new_norm, candidates)
        assert len(results) == 1
        assert results[0].conflict_type == ConflictType.LEX_SUPERIOR
        assert results[0].severity == Severity.HIGH

    def test_skips_self_comparison(self):
        engine = lex_integrity_engine
        norm = make_norm()
        assert engine.analyze_conflicts(norm, [norm]) == []

    def test_to_dict_shape(self):
        engine = lex_integrity_engine
        a = make_norm(id="16161616-1616-1616-1616-161616161616", hierarchy_type="UU", hierarchy_rank=3)
        b = make_norm(id="17171717-1717-1717-1717-171717171717", hierarchy_type="PERDA", hierarchy_rank=7)
        result = engine.check_lex_superior(a, b)
        payload = result.to_dict()
        assert payload["source"]["hierarchy_rank"] == 3
        assert payload["target"]["hierarchy_rank"] == 7
        assert payload["conflict_type"] == "LEX_SUPERIOR"
        assert isinstance(payload["legal_basis"], list)
