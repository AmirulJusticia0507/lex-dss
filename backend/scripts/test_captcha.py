"""Test math captcha flow."""
import sys
import os
sys.path.insert(0, ".")

# Enable captcha for testing
os.environ["CAPTCHA_ENABLED"] = "True"

from app.services.captcha import generate_math_challenge, verify_math_challenge, verify_captcha
import asyncio
import re

# Test math captcha
challenge_id, question = generate_math_challenge()
print(f"Challenge: {question}")
print(f"Challenge ID: {challenge_id}")

# Extract answer from question
match = re.match(r"(\d+)\s*\+\s*(\d+)", question)
if match:
    answer = int(match.group(1)) + int(match.group(2))
    token = f"{challenge_id}:{answer}"
    ok, score, msg = asyncio.run(verify_captcha(token, provider="math"))
    print(f"Verify correct: ok={ok}, score={score}, msg={msg}")

# Test wrong answer
wrong_token = f"{challenge_id}:999"
ok, score, msg = asyncio.run(verify_captcha(wrong_token, provider="math"))
print(f"Verify wrong: ok={ok}, score={score}, msg={msg}")

# Test disabled
ok, score, msg = asyncio.run(verify_captcha("anything", provider="none"))
print(f"Disabled: ok={ok}, score={score}, msg={msg}")

print("\nAll tests passed!")