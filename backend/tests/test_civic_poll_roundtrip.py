"""Uji bolak-balik Lex-DSS <-> E-Netizen lewat HTTP sungguhan.

Server tiruan di bawah sengaja menyalin ``LexDSSImportPermission`` dan
``civic_aggregate`` dari e-voting-system-netizen apa adanya, termasuk
verifikasi HMAC atas byte body. Tujuannya membuktikan bahwa yang ditandatangani
Lex-DSS persis yang dibaca E-Netizen — termasuk untuk teks non-ASCII — bukan
sekali proxy mocks yang bisa menutupi ketidakcocokan serialisasi.
"""

import hashlib
import hmac
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

os.environ.setdefault("DEBUG", "true")

import pytest

from app.services.civic_poll_client import (
    CivicPollClient,
    CivicPollError,
    build_envelope,
)

SECRET = "roundtrip-shared-secret"
TOPIC_ID = 42


class FakeENetizen(BaseHTTPRequestHandler):
    """Tiruan ``topics/views.py::import_civic_draft`` dan ``votes/views.py::civic_aggregate``."""

    received: dict = {}

    def log_message(self, *args):  # silence stderr noise
        return

    def _reply(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self, raw: bytes) -> bool:
        timestamp = self.headers.get("X-Lex-Timestamp", "")
        signature = self.headers.get("X-Lex-Signature", "")
        try:
            if abs(time.time() - int(timestamp)) > 300:
                return False
        except ValueError:
            return False
        message = timestamp.encode() + b"." + raw
        expected = hmac.new(SECRET.encode(), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.removeprefix("sha256="), expected)

    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if not self._authorized(raw):
            self._reply(401, {"detail": "Signature Lex-DSS tidak valid."})
            return

        payload = json.loads(raw.decode("utf-8"))
        if payload.get("schema_version") != "1.0":
            self._reply(400, {"schema_version": ["Versi schema yang didukung hanya 1.0."]})
            return
        if len(payload["poll_draft"]["options"]) < 2:
            self._reply(400, {"poll_draft": {"options": ["min 2 opsi"]}})
            return

        FakeENetizen.received = payload
        self._reply(
            201,
            {
                "id": TOPIC_ID,
                "external_event_id": payload["event_id"],
                "title": payload["poll_draft"]["question"],
                "publication_status": "draft",
                "is_active": False,
            },
        )

    def do_GET(self) -> None:
        if self.path == f"/api/votes/public/civic/{TOPIC_ID}/":
            self._reply(
                200,
                {
                    "topic_id": TOPIC_ID,
                    "question": "Bagaimana pendapatmu?",
                    "status": "published",
                    "total_responses": 30,
                    "options": [
                        {"code": "A", "label": "Setuju", "votes": 18, "percentage": 60.0},
                        {"code": "B", "label": "Tolak", "votes": 12, "percentage": 40.0},
                    ],
                    "updated_at": "2026-09-29T10:00:00+07:00",
                },
            )
        else:
            self._reply(404, {"detail": "civic_poll_not_found"})


@pytest.fixture
def enetizen_url():
    server = HTTPServer(("127.0.0.1", 0), FakeENetizen)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.asyncio
async def test_signed_draft_is_accepted_and_aggregate_can_be_pulled(enetizen_url):
    client = CivicPollClient(base_url=enetizen_url, secret=SECRET)
    assert client.configured

    envelope = build_envelope(
        event_id="POLL-2026-SLM-008",
        question="Retribusi pasar naik 15% — bagaimana pendapatmu?",
        options=[
            {"code": "A", "label": "Setuju (Fasilitas harus diperbaiki)"},
            {"code": "B", "label": "Tolak (Mencabut pasal diskresi)"},
        ],
        region_code="ID-SL",
        source={"type": "youtube_video", "url": "https://youtu.be/x", "title": "Rapat DPRD Sleman"},
        legal_audit={"summary": "Kenaikan retribusi", "referenced_rules": ["UU No. 1 Tahun 2022"]},
    )

    result = await client.submit_draft(envelope)

    assert result["remote_topic_id"] == TOPIC_ID
    assert result["status"] == "draft"
    # Yang benar-benar tiba di server sama persis dengan yang ingin dikirim.
    received = FakeENetizen.received
    assert received["event_id"] == "POLL-2026-SLM-008"
    assert received["poll_draft"]["question"] == "Retribusi pasar naik 15% — bagaimana pendapatmu?"
    assert received["poll_draft"]["region_code"] == "ID-SL"
    assert [item["code"] for item in received["poll_draft"]["options"]] == ["A", "B"]
    assert received["legal_audit"]["referenced_rules"] == ["UU No. 1 Tahun 2022"]

    aggregate = await client.fetch_aggregate(TOPIC_ID)
    assert aggregate["total_responses"] == 30
    assert aggregate["options"][0]["votes"] == 18


@pytest.mark.asyncio
async def test_wrong_secret_is_rejected_by_enetizen(enetizen_url):
    client = CivicPollClient(base_url=enetizen_url, secret="wrong-secret")
    envelope = build_envelope(
        event_id="POLL-BAD",
        question="Q?",
        options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}],
    )

    with pytest.raises(CivicPollError) as raised:
        await client.submit_draft(envelope)

    assert raised.value.status_code == 401


@pytest.mark.asyncio
async def test_schema_violation_surfaces_the_remote_validation_error(enetizen_url):
    client = CivicPollClient(base_url=enetizen_url, secret=SECRET)
    envelope = build_envelope(
        event_id="POLL-BAD-VER",
        question="Q?",
        options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}],
    )
    envelope["schema_version"] = "2.0"

    with pytest.raises(CivicPollError) as raised:
        await client.submit_draft(envelope)

    assert raised.value.status_code == 400
    assert "schema_version" in raised.value.payload


@pytest.mark.asyncio
async def test_missing_aggregate_is_reported_as_not_found(enetizen_url):
    client = CivicPollClient(base_url=enetizen_url, secret=SECRET)

    with pytest.raises(CivicPollError) as raised:
        await client.fetch_aggregate(9999)

    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_unreachable_enetizen_raises_instead_of_leaking_transport_error():
    client = CivicPollClient(base_url="http://127.0.0.1:1", secret=SECRET)

    with pytest.raises(CivicPollError) as raised:
        await client.fetch_aggregate(1)

    assert "tidak dapat dihubungi" in str(raised.value)
