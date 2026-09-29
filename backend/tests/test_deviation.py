import os

os.environ["DEBUG"] = "true"

from app.engine.deviation import DeviationScoreRequest, calculate_deviation_score


def test_score_exposes_each_indicator_and_public_anomaly_fields():
    result = calculate_deviation_score(DeviationScoreRequest(
        verdict_number="1491 K/Pid/2023",
        court_name="Mahkamah Agung",
        ratio_decidendi_text="Pertimbangan unsur pidana dan perbuatan.",
        verdict_amar_text="Menjatuhkan pidana.",
        referenced_articles=["KUHP Pasal 53"],
    ))

    assert set(result.indicators) == {
        "hierarchy_violation_score", "precedent_anomaly_score",
        "evidence_gap_score", "procedural_flaw_score",
    }
    assert all("code" in anomaly and "finding" in anomaly for anomaly in result.anomalies)
