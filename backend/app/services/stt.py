import io
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from openai import AsyncOpenAI

from app.core.config import settings

SUPPORTED_MEDIA_EXTENSIONS = {
    ".flac",
    ".m4a",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".wav",
    ".webm",
}


def validate_media_upload(filename: str, content: bytes, max_upload_mb: int) -> None:
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in SUPPORTED_MEDIA_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_MEDIA_EXTENSIONS))
        raise ValueError(f"Format media tidak didukung. Gunakan: {supported}")
    if not content:
        raise ValueError("Berkas media kosong")
    if len(content) > max_upload_mb * 1024 * 1024:
        raise ValueError(f"Ukuran media maksimal {max_upload_mb} MB")


def _value(item: Any, key: str, default=None):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


async def transcribe_media(
    content: bytes,
    filename: str,
    language: str = "id",
    *,
    client: "AsyncOpenAI | None" = None,
) -> dict[str, Any]:
    if client is None:
        from openai import AsyncOpenAI

        if not settings.STT_API_KEY:
            raise RuntimeError("STT_API_KEY belum dikonfigurasi")
        client = AsyncOpenAI(api_key=settings.STT_API_KEY, base_url=settings.STT_API_BASE)

    media = io.BytesIO(content)
    media.name = filename
    response = await client.audio.transcriptions.create(
        model=settings.STT_MODEL,
        file=media,
        language=language,
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )
    text = str(_value(response, "text", "")).strip()
    segments = [
        {
            "start_seconds": float(_value(segment, "start", 0)),
            "end_seconds": float(_value(segment, "end", 0)),
            "text": str(_value(segment, "text", "")).strip(),
        }
        for segment in (_value(response, "segments", []) or [])
        if str(_value(segment, "text", "")).strip()
    ]
    if not text or not segments:
        raise RuntimeError("Provider STT tidak mengembalikan transkrip bertimestamp")
    return {"text": text, "segments": segments}
