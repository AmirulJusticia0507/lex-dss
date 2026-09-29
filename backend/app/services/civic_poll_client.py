"""Kanal keluar ke E-Netizen (e-voting-system-netizen).

E-Netizen memverifikasi setiap request lewat HMAC-SHA256 atas
``timestamp + "." + body`` (lihat ``topics/permissions.py``). Karena tanda
tangan dihitung atas byte body, service ini menandatangani byte yang persis
sama dengan yang dikirim — bukan rely pada serialisasi ulang httpx.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.core.config import settings

CIVIC_POLL_SCHEMA_VERSION = "1.0"
CIVIC_POLL_IMPORT_PATH = "/api/topics/import-civic-draft/"
CIVIC_POLL_AGGREGATE_PATH = "/api/votes/public/civic/{topic_id}/"
DEFAULT_DISCLAIMER = (
    "Jajak pendapat konsultatif; hasilnya bukan keputusan hukum yang mengikat."
)


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"detail": response.text[:500]}


class CivicPollError(RuntimeError):
    """Kegagalan komunikasi atau kontrak dengan E-Netizen."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def canonical_body(payload: dict[str, Any]) -> bytes:
    """Serialisasi body yang sama persis dengan yang akan dikirim.

    Separator padat dipilih agar tidak ada ruang liar yang berbeda antara byte
    yang ditandatangani dan byte yang diterima E-Netizen.
    """
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True).encode("utf-8")


def sign_body(body: bytes, secret: str, timestamp: Optional[int] = None) -> dict[str, str]:
    """Bangun header HMAC yang dipahami ``LexDSSImportPermission``."""
    if not secret:
        raise CivicPollError("ENETIZEN_HMAC_SECRET belum dikonfigurasi")
    stamp = str(int(time.time()) if timestamp is None else timestamp)
    digest = hmac.new(secret.encode("utf-8"), stamp.encode("utf-8") + b"." + body, hashlib.sha256).hexdigest()
    return {
        "Content-Type": "application/json",
        "X-Lex-Timestamp": stamp,
        "X-Lex-Signature": f"sha256={digest}",
    }


def payload_hash(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


#: Bagian envelope yang tidak memengaruhi isi polling. `generated_at` ikut
#: dikecualikan karena ia transport metadata: membawanya masuk fingerprint
#: membuat draf yang identik selalu terlihat berbeda dan merusak idempotensi.
NON_SEMANTIC_ENVELOPE_KEYS = frozenset({"generated_at"})


def content_fingerprint(envelope: dict[str, Any]) -> str:
    """Hash isi polling saja, tanpa timestamp transport."""
    stable = {key: value for key, value in envelope.items() if key not in NON_SEMANTIC_ENVELOPE_KEYS}
    return payload_hash(canonical_body(stable))


def _iso(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return moment.isoformat()
    return str(value)


def build_envelope(
    *,
    event_id: str,
    question: str,
    options: list[dict[str, str]],
    legal_audit: Optional[dict[str, Any]] = None,
    source: Optional[dict[str, Any]] = None,
    description: str = "",
    disclaimer: str = DEFAULT_DISCLAIMER,
    region_code: str = "",
    opens_at: Optional[datetime] = None,
    closes_at: Optional[datetime] = None,
    generated_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Rakit envelope v1.0 yang diterima ``CivicPollImportSerializer``.

    ``source`` dan ``legal_audit`` opsional; E-Netizen menyimpan keduanya apa
    adanya sebagai jejak audit, jadi bentuknya sengaja tidak divalidasi di
    sini agar analisis Lex Integrity bisa berkembang tanpa breaking change.
    """
    if not event_id:
        raise CivicPollError("event_id wajib diisi")
    if not question:
        raise CivicPollError("question wajib diisi")
    normalized = [{"code": str(item["code"]), "label": str(item["label"])} for item in options]
    if len(normalized) < 2:
        raise CivicPollError("polling membutuhkan minimal dua opsi")
    if len({item["code"] for item in normalized}) != len(normalized):
        raise CivicPollError("kode opsi harus unik")

    poll_draft: dict[str, Any] = {
        "question": question,
        "options": normalized,
        "disclaimer": disclaimer or DEFAULT_DISCLAIMER,
    }
    if description:
        poll_draft["description"] = description
    if region_code:
        poll_draft["region_code"] = region_code
    if opens_at is not None:
        poll_draft["opens_at"] = _iso(opens_at)
    if closes_at is not None:
        poll_draft["closes_at"] = _iso(closes_at)

    envelope: dict[str, Any] = {
        "schema_version": CIVIC_POLL_SCHEMA_VERSION,
        "event_id": event_id,
        "generated_at": _iso(generated_at or datetime.now(timezone.utc)),
        "poll_draft": poll_draft,
    }
    if source:
        envelope["source"] = {"type": source.get("type", "other"), **source}
    if legal_audit:
        envelope["legal_audit"] = legal_audit
    return envelope


def normalize_aggregate(raw: dict[str, Any], event_id: str) -> dict[str, Any]:
    """Rapikan respons ``/api/votes/public/civic/<id>/`` menjadi bentuk stabil.

    E-Netizen 1.0 hanya mengirim jumlah suara per opsi. Field legitimasi
    (``total_registered``, ``participation_percent``) dan bukti integritas
    (``evidence_root``, ``revision``) bersifat opsional di sini supaya
    Lex-DSS tetap bisa memakai agregat yang lebih lengkap begitu sisi
    E-Netizen mengirimkannya.
    """
    if not isinstance(raw, dict):
        raise CivicPollError("Respons agregat bukan objek JSON")

    remote_event_id = raw.get("external_event_id") or raw.get("event_id")
    if remote_event_id and remote_event_id != event_id:
        raise CivicPollError(
            "event_id agregat tidak cocok dengan polling yang diminta",
            payload={"expected": event_id, "received": remote_event_id},
        )

    options: list[dict[str, Any]] = []
    for item in raw.get("options") or []:
        votes = int(item.get("votes") or 0)
        percentage = item.get("percentage")
        options.append(
            {
                "code": str(item.get("code") or ""),
                "label": str(item.get("label") or ""),
                "votes": votes,
                "percentage": round(float(percentage), 2) if percentage is not None else None,
            }
        )

    total_responses = int(raw.get("total_responses") or 0)
    total_registered = raw.get("total_registered")
    total_registered = int(total_registered) if total_registered is not None else None

    participation = raw.get("participation_percent")
    if participation is None and total_registered:
        participation = round(total_responses * 100 / total_registered, 2)
    participation = round(float(participation), 2) if participation is not None else None

    status = str(raw.get("status") or "UNKNOWN").lower()
    return {
        "event_id": event_id,
        "status": status,
        "remote_revision": int(raw["revision"]) if raw.get("revision") is not None else None,
        "total_responses": total_responses,
        "total_registered": total_registered,
        "participation_percent": participation,
        "options": options,
        "evidence_root": raw.get("evidence_root"),
        "voided": bool(raw.get("voided")) or status == "voided",
        "correction_reason": raw.get("correction_reason"),
        "superseded_by_event_id": raw.get("superseded_by_event_id"),
        "source_updated_at": raw.get("updated_at"),
    }


class CivicPollClient:
    """Klien HTTP tipis untuk API polling E-Netizen."""

    def __init__(self, base_url: Optional[str] = None, secret: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.ENETIZEN_URL).rstrip("/")
        self.secret = settings.ENETIZEN_HMAC_SECRET if secret is None else secret

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.secret)

    async def submit_draft(self, envelope: dict[str, Any]) -> dict[str, Any]:
        """Kirim draf polling; E-Netizen membalas 201 (baru) atau 200 (idempoten)."""
        body = canonical_body(envelope)
        response = await self._request(
            "POST", CIVIC_POLL_IMPORT_PATH, body=body, signed=True, timeout=30
        )
        return {
            "remote_topic_id": response.get("id"),
            "event_id": response.get("external_event_id") or envelope["event_id"],
            "status": str(response.get("publication_status") or "UNKNOWN").lower(),
            "created": response.get("publication_status") == "draft",
            "payload_hash": payload_hash(body),
        }

    async def fetch_aggregate(self, remote_topic_id: int) -> dict[str, Any]:
        """Tarik agregat anonim untuk satu polling publik."""
        response = await self._request(
            "GET", CIVIC_POLL_AGGREGATE_PATH.format(topic_id=remote_topic_id), timeout=30
        )
        return response

    async def _request(
        self, method: str, path: str, *, body: Optional[bytes] = None, signed: bool = False, timeout: float = 30
    ) -> dict[str, Any]:
        if not self.configured:
            raise CivicPollError("Integrasi E-Netizen belum dikonfigurasi")
        headers = sign_body(body, self.secret) if (signed and body is not None) else {}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, f"{self.base_url}{path}", content=body, headers=headers)
        except httpx.HTTPError as error:
            raise CivicPollError(f"E-Netizen tidak dapat dihubungi: {error}") from error

        if response.status_code >= 400:
            raise CivicPollError(
                f"E-Netizen menolak request dengan status {response.status_code}",
                status_code=response.status_code,
                payload=_safe_json(response),
            )
        return _safe_json(response) or {}
