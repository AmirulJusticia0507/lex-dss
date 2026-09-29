import pytest

from app.services.transcript import (
    group_topic_candidates,
    parse_transcript,
    validate_promotion,
    validate_review_transition,
)


def test_parse_srt_preserves_timestamps_and_text():
    segments = parse_transcript(
        """1
00:01:02,500 --> 00:01:05,000
Pembahasan kenaikan retribusi.

2
00:01:06,000 --> 00:01:08,250
Anggota meminta kajian dampak.
""",
        "rapat.srt",
    )

    assert segments == [
        {
            "start_seconds": 62.5,
            "end_seconds": 65.0,
            "text": "Pembahasan kenaikan retribusi.",
        },
        {
            "start_seconds": 66.0,
            "end_seconds": 68.25,
            "text": "Anggota meminta kajian dampak.",
        },
    ]


def test_rejects_caption_without_timestamps():
    with pytest.raises(ValueError, match="Timestamp"):
        parse_transcript("teks tanpa timestamp", "rapat.vtt")


def test_topic_candidates_split_on_long_silence():
    candidates = group_topic_candidates(
        [
            {"start_seconds": 0.0, "end_seconds": 10.0, "text": "Usulan retribusi dibahas."},
            {"start_seconds": 12.0, "end_seconds": 20.0, "text": "Anggota memberi tanggapan."},
            {
                "start_seconds": 90.0,
                "end_seconds": 100.0,
                "text": "Pembahasan beralih ke transportasi.",
            },
        ]
    )

    assert len(candidates) == 2
    assert candidates[0]["start_seconds"] == 0.0
    assert candidates[0]["end_seconds"] == 20.0
    assert candidates[1]["title"] == "Pembahasan beralih ke transportasi"


def test_review_transition_requires_pending_and_rejection_reason():
    validate_review_transition("PENDING", "APPROVED", None)

    with pytest.raises(ValueError, match="Alasan"):
        validate_review_transition("PENDING", "REJECTED", "")
    with pytest.raises(ValueError, match="sudah diproses"):
        validate_review_transition("APPROVED", "REJECTED", "Duplikat")


def test_only_unpromoted_approved_candidate_can_be_promoted():
    validate_promotion("APPROVED", None)

    with pytest.raises(ValueError, match="APPROVED"):
        validate_promotion("PENDING", None)
    with pytest.raises(ValueError, match="sudah dipromosikan"):
        validate_promotion("APPROVED", "POLL-001")
