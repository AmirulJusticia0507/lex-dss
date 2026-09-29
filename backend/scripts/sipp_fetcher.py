#!/usr/bin/env python3
"""SIPP (Sistem Informasi Putusan Pengadilan) data fetcher.

Fetches court decisions from the Mahkamah Agung SIPP system for
deviation analysis and case law search.

Usage:
    python scripts/sipp_fetcher.py --help
"""
import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import httpx

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

SIPP_BASE_URL = "https://sipp.mahkamahagung.go.id"
SIPP_SEARCH_URL = f"{SIPP_BASE_URL}/api/search"
SIPP_VERDICT_URL = f"{SIPP_BASE_URL}/api/verdict"


@dataclass
class CourtDecision:
    verdict_number: str
    case_number: str
    court_name: str
    judge: Optional[str] = None
    date: Optional[str] = None
    date_decided: Optional[str] = None
    summary: Optional[str] = None
    ratio_decidendi: Optional[str] = None
    verdict_amar: Optional[str] = None
    referenced_articles: List[str] = field(default_factory=list)
    content: Optional[str] = None
    meta_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SIPPSearchResult:
    total: int
    page: int
    decisions: List[CourtDecision] = field(default_factory=list)


async def search_decisions(
    query: str,
    page: int = 1,
    per_page: int = 20,
    court_filter: Optional[str] = None,
) -> SIPPSearchResult:
    """Search for court decisions using SIPP API."""
    async with httpx.AsyncClient(
        timeout=60.0,
        follow_redirects=True,
        headers={"User-Agent": "Lex-DSS-SIPP-Importer/1.0"},
    ) as client:
        params = {
            "query": query,
            "page": page,
            "per_page": per_page,
        }
        if court_filter:
            params["court"] = court_filter

        try:
            response = await client.get(SIPP_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.warning(f"SIPP search API failed: {e}, falling back to mock data")
            return SIPPSearchResult(total=0, page=page, decisions=[])

        total = data.get("total", 0)
        decisions_data = data.get("decisions", [])

        decisions = []
        for item in decisions_data:
            decision = CourtDecision(
                verdict_number=item.get("verdict_number", ""),
                case_number=item.get("case_number", ""),
                court_name=item.get("court_name", ""),
                judge=item.get("judge"),
                date=item.get("date"),
                date_decided=item.get("date_decided"),
                summary=item.get("summary"),
                ratio_decidendi=item.get("ratio_decidendi"),
                verdict_amar=item.get("verdict_amar"),
                referenced_articles=item.get("referenced_articles", []),
                content=item.get("content"),
                meta_data=item.get("meta_data", {}),
            )
            decisions.append(decision)

        return SIPPSearchResult(total=total, page=page, decisions=decisions)


async def fetch_verdict_detail(verdict_number: str) -> Optional[CourtDecision]:
    """Fetch detailed verdict data from SIPP using verdict number."""
    async with httpx.AsyncClient(
        timeout=60.0,
        follow_redirects=True,
        headers={"User-Agent": "Lex-DSS-SIPP-Importer/1.0"},
    ) as client:
        params = {"verdict_number": verdict_number}

        try:
            response = await client.get(SIPP_VERDICT_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.warning(f"SIPP verdict detail API failed for {verdict_number}: {e}")
            return None

        decision = CourtDecision(
            verdict_number=data.get("verdict_number", verdict_number),
            case_number=data.get("case_number", ""),
            court_name=data.get("court_name", ""),
            judge=data.get("judge"),
            date=data.get("date"),
            date_decided=data.get("date_decided"),
            summary=data.get("summary"),
            ratio_decidendi=data.get("ratio_decidendi"),
            verdict_amar=data.get("verdict_amar"),
            referenced_articles=data.get("referenced_articles", []),
            content=data.get("content"),
            meta_data=data.get("meta_data", {}),
        )
        return decision


async def batch_fetch_decisions(verdict_numbers: List[str]) -> List[Optional[CourtDecision]]:
    """Fetch multiple verdict details in batch."""
    results: List[Optional[CourtDecision]] = []

    async with httpx.AsyncClient(
        timeout=60.0,
        follow_redirects=True,
        headers={"User-Agent": "Lex-DSS-SIPP-Importer/1.0"},
    ) as client:
        for verdict_number in verdict_numbers:
            params = {"verdict_number": verdict_number}

            try:
                response = await client.get(SIPP_VERDICT_URL, params=params)
                response.raise_for_status()
                data = response.json()

                decision = CourtDecision(
                    verdict_number=data.get("verdict_number", verdict_number),
                    case_number=data.get("case_number", ""),
                    court_name=data.get("court_name", ""),
                    judge=data.get("judge"),
                    date=data.get("date"),
                    date_decided=data.get("date_decided"),
                    summary=data.get("summary"),
                    ratio_decidendi=data.get("ratio_decidendi"),
                    verdict_amar=data.get("verdict_amar"),
                    referenced_articles=data.get("referenced_articles", []),
                    content=data.get("content"),
                    meta_data=data.get("meta_data", {}),
                )
                results.append(decision)
            except Exception as e:
                logger = __import__("logging").getLogger(__name__)
                logger.warning(f"Failed to fetch {verdict_number}: {e}")
                results.append(None)

    return results


def extract_legal_elements(text: str) -> Dict[str, any]:
    """Extract legal elements from verdict text for deviation analysis."""
    if not text:
        return {
            "hierarchy_keywords": [],
            "precedent_indicators": [],
            "detected_domains": [],
        }

    hierarchy_keywords = {
        "UUD": ["UUD 1945", "undang-undang dasar", "konstitusi"],
        "UU": ["undang-undang", "UU No."],
        "PP": ["peraturan pemerintah", "PP No."],
        "PERPRES": ["peraturan presiden", "Perpres No."],
        "PERMEN": ["peraturan menteri", "Permen No."],
        "PERDA": ["peraturan daerah", "Perda No."],
    }

    mentioned_hierarchies = []
    for level, keywords in hierarchy_keywords.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                mentioned_hierarchies.append(level)
                break

    precedent_indicators = [
        "putusan mahkamah agung",
        "putusan mahkamah konstitusi",
        "yurisprudensi",
        "precedent",
        "stare decisis",
        "putusan nomor",
        "putusan mk",
        "putusan ma",
    ]
    has_precedent = any(ind in text.lower() for ind in precedent_indicators)

    element_keywords = {
        "pidana": ["unsur", "dolus", "culpa", "opzet", "schuld", "anschuldig", "kejahatan", "pidana"],
        "perdata": ["wanprestasi", "force majeure", "kewajiban", "hak", "perjanjian", "kontrak"],
        "htn": ["kewenangan", "wewenang", "asas", "aadb", "auupb", "detournement"],
    }

    detected_domains = []
    for domain, keywords in element_keywords.items():
        if any(kw in text.lower() for kw in keywords):
            detected_domains.append(domain)

    return {
        "hierarchy_keywords": mentioned_hierarchies,
        "precedent_indicators": has_precedent,
        "detected_domains": detected_domains,
    }


async def import_sipp_decisions(
    query: str,
    per_page: int = 50,
    max_pages: int = 5,
    db_session=None,
) -> int:
    """Import SIPP decisions into the database for deviation analysis."""
    from sqlalchemy import select
    from app.core.database import async_session_maker
    from app.models.legal import LegalArticle, LegalHierarchy
    from app.engine.deviation import calculate_deviation_score, DeviationScoreRequest

    total_imported = 0

    async with httpx.AsyncClient(
        timeout=60.0,
        follow_redirects=True,
        headers={"User-Agent": "Lex-DSS-SIPP-Importer/1.0"},
    ) as client:
        for page in range(1, max_pages + 1):
            search_result = await search_decisions(
                query=query,
                page=page,
                per_page=per_page,
            )

            if not search_result.decisions:
                break

            async with async_session_maker() as session:
                # Ensure hierarchy types exist
                hierarchy_result = await session.execute(
                    select(LegalHierarchy).where(
                        LegalHierarchy.type_name.in_(["UU", "PERDA", "PERMEN", "PP", "UUD"])
                    )
                )
                hierarchies = {h.type_name: h for h in hierarchy_result.scalars().all()}

                for decision in search_result.decisions:
                    # Check if already exists
                    result = await session.execute(
                        select(LegalArticle).where(
                            LegalArticle.verdict_number == decision.verdict_number
                        )
                    )
                    existing = result.scalar_one_or_none()
                    if existing:
                        continue

                    # Extract legal elements
                    legal_elements = extract_legal_elements(
                        decision.content or "" or decision.summary or ""
                    )

                    # Determine hierarchy
                    hierarchy_id = None
                    if decision.ratio_decidendi:
                        ratio_text = decision.ratio_decidendi.lower()
                        hierarchy_markers = {
                            "UUD": ["uud 1945", "undang-undang dasar", "konstitusi"],
                            "UU": ["uu no.", "undang-undang"],
                            "PP": ["pp no.", "peraturan pemerintah"],
                            "PERMEN": ["permen no.", "peraturan menteri"],
                            "PERDA": ["perda no.", "peraturan daerah"],
                        }
                        for level, hierarchy_id_val in hierarchies.items():
                            if any(marker in ratio_text for marker in hierarchy_markers.get(level, [])):
                                hierarchy_id = hierarchy_id_val.id
                                break

                    # Create legal article from SIPP decision
                    article = LegalArticle(
                        id=uuid4(),
                        document_title=f"Putusan Pengadilan - {decision.verdict_number}",
                        article_number=decision.verdict_number,
                        content=decision.content or decision.summary or "",
                        domain="PIDANA",  # Will be refined based on content
                        hierarchy_id=hierarchy_id,
                        meta_data={
                            "source": "SIPP_MK",
                            "verdict_number": decision.verdict_number,
                            "case_number": decision.case_number,
                            "court_name": decision.court_name,
                            "judge": decision.judge,
                            "date_decided": decision.date_decided,
                            "sipp_data": True,
                        },
                    )
                    session.add(article)
                    await session.flush()
                    total_imported += 1

                await session.commit()
                print(f"Page {page}: imported {len(search_result.decisions)} decisions")

    print(f"Total imported: {total_imported} decisions from SIPP")
    return total_imported


def uuid4():
    import uuid
    return uuid.uuid4()


def main():
    parser = argparse.ArgumentParser(description="SIPP data fetcher for Lex-DSS")
    parser.add_argument("--query", type=str, help="Search query for SIPP")
    parser.add_argument("--per-page", type=int, default=50, help="Results per page")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum pages to fetch")
    parser.add_argument("--import-to-db", action="store_true", help="Import to database")
    parser.add_argument("--verdict-numbers", type=str, nargs="+", help="Specific verdict numbers to fetch")

    args = parser.parse_args()

    if args.query:
        if args.import_to_db:
            asyncio.run(
                import_sipp_decisions(
                    query=args.query,
                    per_page=args.per_page,
                    max_pages=args.max_pages,
                )
            )
        else:
            result = asyncio.run(search_decisions(query=args.query))
            print(f"SIPP Search results for '{args.query}':")
            print(f"Total: {result.total}")
            for d in result.decisions[:5]:
                print(f"  - {d.verdict_number} | {d.court_name} | {d.date_decided}")

    if args.verdict_numbers:
        results = asyncio.run(batch_fetch_decisions(args.verdict_numbers))
        for i, decision in enumerate(results):
            if decision:
                print(f"[{i+1}] {decision.verdict_number}")
                print(f"    Court: {decision.court_name}")
                print(f"    Date: {decision.date_decided}")
                print(f"    Summary: {decision.summary[:200] if decision.summary else 'N/A'}...")
            else:
                print(f"[{i+1}] FAILED to fetch")


if __name__ == "__main__":
    main()
