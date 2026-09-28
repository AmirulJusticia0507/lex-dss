"""Multi-provider CAPTCHA verification service.

Supports:
- hCaptcha (primary, privacy-focused, API mirip reCAPTCHA)
- Self-hosted math captcha (fallback, no external dependency)

Provider dipilih via CAPTCHA_PROVIDER env var:
- "hcaptcha" (default) - butuh HCAPTCHA_SECRET_KEY
- "math" - self-hosted, tidak perlu external service
- "none" - disable captcha
"""
import httpx
import random
import string
import time
from typing import Optional

from app.core.config import settings

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"


# In-memory store for math captcha challenges (use Redis in production)
_math_challenges: dict[str, dict] = {}
_MATH_CHALLENGE_TTL = 300  # 5 minutes


def generate_math_challenge() -> tuple[str, str]:
    """Generate a simple math challenge.

    Returns (challenge_id, question_text).
    Example: "12 + 7 = ?"
    """
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    answer = a + b
    challenge_id = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    question = f"{a} + {b} = ?"

    _math_challenges[challenge_id] = {
        "answer": answer,
        "created_at": time.time(),
    }
    return challenge_id, question


def verify_math_challenge(challenge_id: str, user_answer: str) -> tuple[bool, str]:
    """Verify a math captcha answer. Challenge persists until correct or expired."""
    if not challenge_id or not user_answer:
        return False, "Math captcha required"

    record = _math_challenges.get(challenge_id)
    if not record:
        return False, "Invalid or expired challenge"

    if time.time() - record["created_at"] > _MATH_CHALLENGE_TTL:
        _math_challenges.pop(challenge_id, None)
        return False, "Challenge expired"

    try:
        answer = int(user_answer.strip())
    except ValueError:
        return False, "Invalid answer format"

    if answer != record["answer"]:
        return False, "Incorrect answer"

    # Correct answer - consume the challenge
    _math_challenges.pop(challenge_id, None)
    return True, "ok"


async def verify_hcaptcha(token: str, remote_ip: Optional[str] = None) -> tuple[bool, float, str]:
    """Verify hCaptcha token with hCaptcha API.

    Returns (success, score, message).
    """
    if not settings.HCAPTCHA_SECRET_KEY:
        return False, 0.0, "hCaptcha secret key not configured"

    if not token:
        return False, 0.0, "hCaptcha token required"

    async with httpx.AsyncClient(timeout=10) as client:
        data = {
            "secret": settings.HCAPTCHA_SECRET_KEY,
            "response": token,
        }
        if remote_ip:
            data["remoteip"] = remote_ip
        try:
            resp = await client.post(HCAPTCHA_VERIFY_URL, data=data)
            body = resp.json()
        except Exception as exc:
            return False, 0.0, f"hCaptcha verification failed: {exc}"

    if not body.get("success"):
        codes = body.get("error-codes", [])
        return False, 0.0, f"hCaptcha failed: {codes}"

    score = float(body.get("score", 1.0))
    if score < settings.CAPTCHA_THRESHOLD:
        return False, score, f"hCaptcha score too low: {score}"

    return True, score, "ok"


async def verify_captcha(
    token: str,
    remote_ip: Optional[str] = None,
    provider: Optional[str] = None,
) -> tuple[bool, float, str]:
    """Verify captcha token using configured provider.

    Args:
        token: Captcha token (hcaptcha token or math challenge_id)
        remote_ip: Client IP address
        provider: Override provider ("hcaptcha", "math", "none")

    Returns:
        (success, score, message)
    """
    provider = provider or settings.CAPTCHA_PROVIDER

    if provider == "none" or not settings.CAPTCHA_ENABLED:
        return True, 1.0, "captcha disabled"

    if provider == "hcaptcha":
        return await verify_hcaptcha(token, remote_ip)

    if provider == "math":
        # token berisi "challenge_id:answer"
        parts = token.split(":", 1)
        if len(parts) != 2:
            return False, 0.0, "Invalid math captcha format"
        challenge_id, answer = parts
        ok, msg = verify_math_challenge(challenge_id, answer)
        return ok, 1.0 if ok else 0.0, msg

    return False, 0.0, f"Unknown captcha provider: {provider}"