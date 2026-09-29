from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.stt import transcribe_media, validate_media_upload


class FakeTranscriptions:
    async def create(self, **kwargs):
        assert kwargs["file"].name == "rapat.mp4"
        assert kwargs["language"] == "id"
        assert kwargs["response_format"] == "verbose_json"
        return SimpleNamespace(
            text="Pembahasan dimulai. Anggota menyampaikan tanggapan.",
            segments=[
                SimpleNamespace(start=0.0, end=4.5, text=" Pembahasan dimulai. "),
                SimpleNamespace(start=4.5, end=9.0, text="Anggota menyampaikan tanggapan."),
            ],
        )


class FakeClient:
    audio = SimpleNamespace(transcriptions=FakeTranscriptions())


@pytest.mark.asyncio
async def test_transcribe_media_normalizes_timestamped_segments(monkeypatch):
    monkeypatch.setattr(settings, "STT_MODEL", "whisper-test")

    result = await transcribe_media(b"fake-media", "rapat.mp4", client=FakeClient())

    assert result["text"].startswith("Pembahasan")
    assert result["segments"] == [
        {"start_seconds": 0.0, "end_seconds": 4.5, "text": "Pembahasan dimulai."},
        {
            "start_seconds": 4.5,
            "end_seconds": 9.0,
            "text": "Anggota menyampaikan tanggapan.",
        },
    ]


def test_validate_media_upload_rejects_unsupported_or_oversized_files():
    with pytest.raises(ValueError, match="Format media"):
        validate_media_upload("rapat.pdf", b"content", 25)
    with pytest.raises(ValueError, match="maksimal"):
        validate_media_upload("rapat.wav", b"12", 0)


def test_validate_media_upload_accepts_audio_and_video():
    validate_media_upload("rapat.wav", b"audio", 25)
    validate_media_upload("rapat.mp4", b"video", 25)
