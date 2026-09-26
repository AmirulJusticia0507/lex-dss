"""Smoke test konektivitas LLM provider (hanya memakai stdlib).

Jalankan dari root backend:
    python scripts/check_llm.py

Script ini memuat backend/.env secara manual (tanpa dependensi tambahan),
memeriksa daftar model, lalu mengirim satu chat completion.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def load_env(path: Path = ENV_PATH) -> None:
    """Memuat backend/.env. Nilai dari .env menggantikan variabel ambient,
    karena mesin development sering sudah punya OPENAI_API_KEY dari provider lain."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in os.environ:
            print(f"  catatan: {key} dari environment ditimpa oleh backend/.env")
        os.environ[key] = value.strip()


def request(method: str, url: str, payload: dict | None = None, timeout: int = 60):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {os.environ.get('OPENAI_API_KEY', '')}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        return err.code, body


def chat_completion(base: str, model: str, retries: int = 3) -> tuple[int, object]:
    """Kirim chat completion; model gratis sering kena rate limit (429)."""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Sebutkan tiga asas hukum umum dalam satu kalimat pendek.",
            }
        ],
        "max_tokens": 200,
    }
    timeout = int(os.environ.get("LLM_TIMEOUT_SECONDS", "120"))
    for attempt in range(1, retries + 1):
        status, result = request("POST", f"{base}/chat/completions", payload, timeout=timeout)
        if status != 429 or attempt == retries:
            return status, result
        wait = 5 * attempt
        print(f"  429 rate limited; retry {attempt}/{retries} dalam {wait} detik...")
        time.sleep(wait)
    return status, result


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    load_env()
    base = os.environ.get("OPENAI_API_BASE", "").rstrip("/")
    model = os.environ.get("LLM_MODEL", "auto:free")
    if not base or not os.environ.get("OPENAI_API_KEY"):
        print("KONFIGURASI BELUM LENGKAP: OPENAI_API_BASE / OPENAI_API_KEY")
        return 1

    print(f"Base URL : {base}")
    print(f"Model    : {model}\n")

    status, models = request("GET", f"{base}/models")
    print(f"[GET /models] HTTP {status}")
    if status == 200:
        ids = sorted(item["id"] for item in models.get("data", []))
        print(f"  {len(ids)} model tersedia; contoh: {', '.join(ids[:8])}")
        if model not in ids:
            print(f"  PERINGATAN: '{model}' tidak ada di daftar model.")
    else:
        print(f"  {models}")
        return 1

    status, result = chat_completion(base, model)
    print(f"\n[POST /chat/completions] HTTP {status}")
    if status == 200:
        print(f"  balasan: {result['choices'][0]['message']['content'][:300]}")
        print(f"  usage  : {result.get('usage')}")
        print("\nHASIL: LLM SIAP DIPAKAI.")
        return 0

    print(f"  {result}")
    if status == 402:
        print("\nHASIL: KEY VALID tetapi saldo 0. Gunakan model gratis (contoh: auto:free) atau top up.")
    elif status == 401:
        print("\nHASIL: API key ditolak. Periksa OPENAI_API_KEY pada backend/.env.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
