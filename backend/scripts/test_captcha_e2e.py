"""End-to-end test: math captcha flow with login."""
import sys
import os
sys.path.insert(0, ".")

# Enable captcha for testing
os.environ["CAPTCHA_ENABLED"] = "True"
os.environ["CAPTCHA_PROVIDER"] = "math"

from app.services.captcha import generate_math_challenge, verify_captcha
import asyncio
import re

print("=== Math Captcha Flow Test ===\n")

# Step 1: Generate challenge (like GET /auth/captcha/challenge)
challenge_id, question = generate_math_challenge()
print(f"Step 1 - Generate challenge:")
print(f"  challenge_id: {challenge_id}")
print(f"  question: {question}")

# Step 2: User solves (extract answer)
match = re.match(r"(\d+)\s*\+\s*(\d+)", question)
answer = int(match.group(1)) + int(match.group(2))
print(f"\nStep 2 - User solves:")
print(f"  answer: {answer}")

# Step 3: Frontend sends "challenge_id:answer" as recaptcha_token
token = f"{challenge_id}:{answer}"
print(f"\nStep 3 - Frontend sends token: {token}")

# Step 4: Backend verifies (like login endpoint does)
ok, score, msg = asyncio.run(verify_captcha(token, provider="math"))
print(f"\nStep 4 - Backend verify:")
print(f"  ok={ok}, score={score}, msg={msg}")

if ok:
    print("\n[PASS] Captcha flow PASSED")
else:
    print(f"\n[FAIL] Captcha flow FAILED: {msg}")
    sys.exit(1)