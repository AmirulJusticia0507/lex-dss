import pytest

from app.services.transcript import parse_transcript


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
