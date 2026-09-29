import os

os.environ.setdefault("DEBUG", "true")

import hashlib
import hmac

from app.services.civic_poll_client import (
    CivicPollError,
    build_envelope,
    canonical_body,
    content_fingerprint,
    normalize_aggregate,
    payload_hash,
    sign_body,
)


# ── Oracle: salinan persis dari topics/permissions.py::LexDSSImportPermission
# di e-voting-system-netizen. Jika kedua sisi berbeda, import ditolak 401.
def enetizen_verifies(secret: str, timestamp: str, signature_header: str, body: bytes) -> bool:
    message = timestamp.encode() + b"." + body
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header.removeprefix("sha256="), expected)


SECRET = "shared-test-secret"


def test_signature_is_accepted_by_enetizen_verifier():
    body = canonical_body({"event_id": "POLL-1", "question": "Setuju?"})
    headers = sign_body(body, SECRET, timestamp=1_780_000_000)

    assert headers["X-Lex-Timestamp"] == "1780000000"
    assert headers["X-Lex-Signature"].startswith("sha256=")
    assert enetizen_verifies(SECRET, headers["X-Lex-Timestamp"], headers["X-Lex-Signature"], body)


def test_signature_still_verifies_for_non_ascii_payload():
    """Ekspektasi byte harus identik; ensure_ascii/separator yang meleset
    membuat HMAC gagal meski payload-nya sama secara semantik."""
    envelope = build_envelope(
        event_id="POLL-SLM-008",
        question="Retribusi pasar naik 15% — bagaimana pendapatmu?",
        options=[{"code": "A", "label": "Setuju"}, {"code": "B", "label": "Tolak"}],
    )
    body = canonical_body(envelope)
    headers = sign_body(body, SECRET)

    assert b"\\u" not in body  # teks non-ASCII dikirim apa adanya
    assert b"Retribusi pasar naik 15%" in body
    assert enetizen_verifies(SECRET, headers["X-Lex-Timestamp"], headers["X-Lex-Signature"], body)


def test_signature_rejects_a_tampered_body():
    body = canonical_body({"event_id": "POLL-1", "question": "Setuju?"})
    headers = sign_body(body, SECRET)
    tampered = body.replace(b"Setuju?", b"Tolak?")

    assert not enetizen_verifies(SECRET, headers["X-Lex-Timestamp"], headers["X-Lex-Signature"], tampered)


def test_missing_secret_is_rejected_before_any_request():
    try:
        sign_body(b"{}", "")
    except CivicPollError as error:
        assert "ENETIZEN_HMAC_SECRET" in str(error)
    else:
        raise AssertionError("secrets kosong harus ditolak")


def test_envelope_matches_enetizen_v1_schema():
    envelope = build_envelope(
        event_id="POLL-2026-SLM-008",
        question="Bagaimana pendapatmu?",
        options=[{"code": "A", "label": "Setuju"}, {"code": "B", "label": "Tolak"}],
        region_code="ID-SL",
        source={"type": "youtube_video", "url": "https://youtu.be/x", "title": "Rapat DPRD"},
        legal_audit={"summary": "Isu retribusi", "confidence": 0.78},
    )

    assert envelope["schema_version"] == "1.0"
    assert envelope["event_id"] == "POLL-2026-SLM-008"
    assert envelope["generated_at"].endswith("+00:00")
    assert envelope["source"]["type"] == "youtube_video"
    assert envelope["legal_audit"]["confidence"] == 0.78

    draft = envelope["poll_draft"]
    assert draft["question"] == "Bagaimana pendapatmu?"
    assert draft["options"] == [
        {"code": "A", "label": "Setuju"},
        {"code": "B", "label": "Tolak"},
    ]
    assert draft["region_code"] == "ID-SL"
    assert draft["disclaimer"]  # default selalu diisi karena wajib di sisi E-Netizen
    assert "region_code" not in envelope  # tidak di luar poll_draft


def test_envelope_omits_optional_fields_when_not_supplied():
    envelope = build_envelope(
        event_id="POLL-MIN",
        question="Q?",
        options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}],
    )

    assert "source" not in envelope
    assert "legal_audit" not in envelope
    assert "region_code" not in envelope["poll_draft"]
    assert "opens_at" not in envelope["poll_draft"]


def test_envelope_rejects_ambiguous_or_underspecified_polls():
    invalid_options = [
        [{"code": "A", "label": "Ya"}],
        [{"code": "A", "label": "Ya"}, {"code": "A", "label": "Tidak"}],
    ]
    for bad_options in invalid_options:
        try:
            build_envelope(event_id="P", question="Q?", options=bad_options)
        except CivicPollError:
            pass
        else:
            raise AssertionError("opsi polling tidak valid harus ditolak")


def test_aggregate_normalises_the_current_enetizen_payload():
    snapshot = normalize_aggregate(
        {
            "topic_id": 7,
            "question": "Q?",
            "status": "published",
            "total_responses": 30,
            "options": [
                {"code": "A", "label": "Setuju", "votes": 18, "percentage": 60.0},
                {"code": "B", "label": "Tolak", "votes": 12, "percentage": 40.0},
            ],
            "updated_at": "2026-09-29T10:00:00+07:00",
        },
        "POLL-1",
    )

    assert snapshot["event_id"] == "POLL-1"
    assert snapshot["status"] == "published"
    assert snapshot["total_responses"] == 30
    assert snapshot["options"][0] == {"code": "A", "label": "Setuju", "votes": 18, "percentage": 60.0}
    # E-Netizen 1.0 belum mengirim jejak legitimasi; jangan dikarang.
    assert snapshot["total_registered"] is None
    assert snapshot["participation_percent"] is None
    assert snapshot["evidence_root"] is None
    assert snapshot["voided"] is False
    assert snapshot["source_updated_at"] == "2026-09-29T10:00:00+07:00"


def test_aggregate_computes_participation_when_registrations_are_known():
    snapshot = normalize_aggregate(
        {
            "status": "closed",
            "total_responses": 120,
            "total_registered": 3000,
            "options": [],
            "evidence_root": "abc123",
        },
        "POLL-1",
    )

    assert snapshot["participation_percent"] == 4.0
    assert snapshot["evidence_root"] == "abc123"
    assert snapshot["options"] == []


def test_aggregate_marks_voided_polls():
    assert normalize_aggregate({"status": "voided", "total_responses": 0}, "P")["voided"] is True
    assert (
        normalize_aggregate({"status": "published", "voided": True, "total_responses": 5}, "P")["voided"]
        is True
    )


def test_aggregate_rejects_mismatched_event_id():
    try:
        normalize_aggregate({"external_event_id": "POLL-OTHER", "total_responses": 1}, "POLL-1")
    except CivicPollError as error:
        assert "tidak cocok" in str(error)
    else:
        raise AssertionError("event_id yang tidak cocok harus ditolak")


def test_aggregate_tolerates_missing_counters():
    snapshot = normalize_aggregate({"options": [{"code": "A", "label": "Ya", "votes": None}]}, "P")

    assert snapshot["status"] == "unknown"
    assert snapshot["total_responses"] == 0
    assert snapshot["options"] == [{"code": "A", "label": "Ya", "votes": 0, "percentage": None}]


def test_content_fingerprint_ignores_generated_at():
    """Two draf yang identik tetap harus dianggap sama walau dikirim pada
    detik berbeda — inilah yang menjaga idempotensi import."""
    first = build_envelope(
        event_id="P", question="Q?", options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}]
    )
    second = build_envelope(
        event_id="P", question="Q?", options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}]
    )

    assert first["generated_at"] != second["generated_at"]  # transport metadata memang berbeda
    assert content_fingerprint(first) == content_fingerprint(second)
    # ...tetapi body yang ditandatangani tetap berbeda, sesuai kontrak E-Netizen.
    assert payload_hash(canonical_body(first)) != payload_hash(canonical_body(second))


def test_content_fingerprint_detects_real_edits():
    base = build_envelope(
        event_id="P", question="Q?", options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}]
    )
    edited_question = build_envelope(
        event_id="P", question="Q baru?", options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}]
    )
    edited_options = build_envelope(
        event_id="P",
        question="Q?",
        options=[{"code": "A", "label": "Ya"}, {"code": "B", "label": "Tidak"}, {"code": "C", "label": "Abstain"}],
    )

    assert content_fingerprint(base) != content_fingerprint(edited_question)
    assert content_fingerprint(base) != content_fingerprint(edited_options)
