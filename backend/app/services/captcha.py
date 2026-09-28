"""reCAPTCHA verification service."""
import httpx
from typing import Optional

from app.core.config import settings

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


async def verify_recaptcha(token: str, remote_ip: Optional[str] = None) -> tuple[bool, float, str]:
    """Verify reCAPTCHA token with Google.

    Returns (success, score, message).
    If RECAPTCHA_ENABLED is False, always returns (True, 1.0, "disabled").
    """
    if not settings.RECAPTCHA_ENABLED or not settings.RECAPTCHA_SECRET:
        return True, 1.0, "reCAPTCHA disabled"

    if not token:
        return False, 0.0, "reCAPTCHA token required"

    async with httpx.AsyncClient(timeout=10) as client:
        data = {
            "secret": settings.RECAPTCHA_SECRET,
            "response": token,
        }
        if remote_ip:
            data["remoteip"] = remote_ip
        try:
            resp = await client.post(RECAPTCHA_VERIFY_URL, data=data)
            body = resp.json()
        except Exception as exc:
            return False, 0.0, f"reCAPTCHA verification failed: {exc}"

    if not body.get("success"):
        return False, 0.0, body.get("error-codes", ["unknown_error"])

    score = float(body.get("score", 0.0))
    if score < settings.RECAPTCHA_THRESHOLD:
        return False, score, f"reCAPTCHA score too low: {score}"

    return True, score, "ok"