from typing import Any

import httpx

from app.core.config import settings


class LexIntegrityClient:
    def __init__(self) -> None:
        self.base_url = settings.LEX_INTEGRITY_URL.rstrip("/")
        self.headers = {"X-Internal-Api-Key": settings.INTERNAL_API_KEY or ""}

    async def analyze(self, query: str, max_hops: int = 4) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/api/analyze/multi-hop",
                json={"userQuery": query, "maxHops": max_hops},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def rules(self, page: int, limit: int = 100) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/api/rules",
                params={"page": page, "limit": limit, "is_active": "true"},
            )
            response.raise_for_status()
            return response.json()
