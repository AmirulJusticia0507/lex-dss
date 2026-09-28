#!/usr/bin/env python3
"""Import every national law listed by Ditjen PP into ``legal_articles``.

The importer stores each source PDF article separately, including its official
catalog/PDF URL and the catalog status. It intentionally does not try to merge
amending laws into a consolidated text.

Usage (from backend/):
    python scripts/import_national_laws.py                 # catalog dry run
    python scripts/import_national_laws.py --apply         # import all laws
    python scripts/import_national_laws.py --apply --limit 5
"""

import argparse
import asyncio
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import httpx

BACKEND_DIR = Path(__file__).resolve().parents[1]
BASE_URL = "https://peraturan.go.id"
LIST_URL = f"{BASE_URL}/uu?page={{page}}"
FALLBACK_PATH = BACKEND_DIR / "data" / "legal-seed" / "national-law-fallbacks.json"
ARTICLE_PATTERN = re.compile(r"(?im)^\s*Pasal\s+(\d+[A-Z]?)\s*(?=\n|$)")
TOTAL_PATTERN = re.compile(r"data dari\s+([\d.]+)\s+Peraturan", re.IGNORECASE)
CARD_PATTERN = re.compile(
    r'<p style="padding-top: -2;">(?P<label>.*?)</p>\s*'
    r'<p><a href="(?P<detail>/id/uu-[^"]+)"[^>]*>(?P<title>.*?)</a></p>',
    re.DOTALL | re.IGNORECASE,
)
PDF_PATTERN = re.compile(r'Dokumen :\s*<a href="(?P<pdf>/files/[^"]+\.pdf)"', re.IGNORECASE)


@dataclass(frozen=True)
class Law:
    title: str
    catalog_url: str
    pdf_url: str | None
    status: str


def text_only(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def parse_law_page(page_html: str) -> list[Law]:
    """Parse the stable, server-rendered cards on the official UU catalog."""
    laws: list[Law] = []
    for match in CARD_PATTERN.finditer(page_html):
        card_end = page_html.find('<div class="col-md-12">', match.end())
        card = page_html[match.start() : card_end if card_end != -1 else None]
        pdf = PDF_PATTERN.search(card)
        laws.append(
            Law(
                title=text_only(match.group("label")) + " tentang " + text_only(match.group("title")),
                catalog_url=urljoin(BASE_URL, match.group("detail")),
                pdf_url=urljoin(BASE_URL, pdf.group("pdf")) if pdf else None,
                status="tidak_berlaku" if "Tidak Berlaku" in card else "berlaku",
            )
        )
    return laws


def parse_total(page_html: str) -> int:
    match = TOTAL_PATTERN.search(page_html)
    if not match:
        raise ValueError("Could not find the total law count in the Ditjen PP catalog.")
    return int(match.group(1).replace(".", ""))


def parse_articles(pdf_text: str) -> list[tuple[str, str]]:
    """Return article number/text pairs from an official PDF text extraction."""
    body = re.split(r"(?im)^\s*PENJELASAN\s*$", pdf_text, maxsplit=1)[0]
    matches = list(ARTICLE_PATTERN.finditer(body))
    articles: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        content = body[match.end() : end].strip()
        if content:
            articles.append((match.group(1), content))
    return articles


def load_fallbacks() -> dict[str, list[dict[str, str]]]:
    """Load manually verified JDIHN/BPK PDF URLs keyed by Ditjen PP catalog URL."""
    if not FALLBACK_PATH.exists():
        return {}
    fallbacks = json.loads(FALLBACK_PATH.read_text(encoding="utf-8"))["sources"]
    for catalog_url, sources in fallbacks.items():
        if not catalog_url.startswith(BASE_URL) or not isinstance(sources, list):
            raise ValueError(f"Invalid fallback entry: {catalog_url}")
        for source in sources:
            if set(source) != {"name", "url"} or not source["url"].startswith("https://"):
                raise ValueError(f"Invalid fallback source for {catalog_url}")
    return fallbacks


async def fetch(client: httpx.AsyncClient, url: str) -> httpx.Response:
    for attempt in range(3):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response
        except httpx.HTTPError:
            if attempt == 2:
                raise
            await asyncio.sleep(attempt + 1)
    raise AssertionError("unreachable")


async def fetch_articles(
    law: Law, fallbacks: dict[str, list[dict[str, str]]], client: httpx.AsyncClient
) -> tuple[list[tuple[str, str]], str, str, int]:
    sources: list[dict[str, str]] = []
    if law.pdf_url:
        sources.append({"name": "Ditjen PP", "url": law.pdf_url})
    sources.extend(fallbacks.get(law.catalog_url, []))
    errors: list[str] = []
    for priority, source in enumerate(sources, start=1):
        try:
            articles = extract_pdf_articles((await fetch(client, source["url"])).content)
            if articles:
                return articles, source["name"], source["url"], priority
            errors.append(f"{source['name']}: no Pasal headings")
        except Exception as error:
            errors.append(f"{source['name']}: {error}")
    raise ValueError("; ".join(errors) or "No official PDF or configured fallback source.")


async def discover_laws(client: httpx.AsyncClient) -> list[Law]:
    first_page = (await fetch(client, LIST_URL.format(page=1))).text
    total = parse_total(first_page)
    pages = (total + 19) // 20
    laws = parse_law_page(first_page)
    for page in range(2, pages + 1):
        laws.extend(parse_law_page((await fetch(client, LIST_URL.format(page=page))).text))
    return list(dict.fromkeys(laws))


def extract_pdf_articles(pdf_bytes: bytes) -> list[tuple[str, str]]:
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is required. Install Poppler and put it on PATH.")
    with tempfile.TemporaryDirectory() as directory:
        pdf_path = Path(directory) / "law.pdf"
        text_path = Path(directory) / "law.txt"
        pdf_path.write_bytes(pdf_bytes)
        subprocess.run(
            ["pdftotext", "-raw", str(pdf_path), str(text_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return parse_articles(text_path.read_text(encoding="utf-8", errors="replace"))


async def import_laws(
    laws: list[Law], fallbacks: dict[str, list[dict[str, str]]], client: httpx.AsyncClient
) -> None:
    sys.path.insert(0, str(BACKEND_DIR))
    from sqlalchemy import select, text

    from app.core.database import async_session_maker
    from app.models.legal import LegalArticle, LegalHierarchy

    async with async_session_maker() as session:
        await session.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_legal_articles_document_article "
                "ON legal_articles (document_title, article_number)"
            )
        )
        hierarchy_id = await session.scalar(
            select(LegalHierarchy.id).where(LegalHierarchy.type_name == "UU")
        )
        if hierarchy_id is None:
            raise RuntimeError("Missing UU hierarchy. Run alembic upgrade head first.")
        await session.commit()

        created = updated = skipped = failed = 0
        for number, law in enumerate(laws, start=1):
            try:
                articles, source_name, source_url, source_priority = await fetch_articles(
                    law, fallbacks, client
                )

                result = await session.execute(
                    select(LegalArticle).where(LegalArticle.document_title == law.title)
                )
                existing = {item.article_number: item for item in result.scalars()}
                for article_number, content in articles:
                    metadata = {
                        "source": source_name,
                        "catalog_url": law.catalog_url,
                        "source_url": source_url,
                        "source_priority": source_priority,
                        "status": law.status,
                        "transcription_status": "extracted_from_official_pdf",
                        "verification_status": "requires_legal_review",
                    }
                    article = existing.get(article_number)
                    if article is None:
                        session.add(
                            LegalArticle(
                                document_title=law.title[:255],
                                article_number=article_number,
                                content=content,
                                domain=None,
                                hierarchy_id=hierarchy_id,
                                meta_data=metadata,
                            )
                        )
                        created += 1
                    elif article.content != content or article.meta_data != metadata:
                        article.content = content
                        article.hierarchy_id = hierarchy_id
                        article.meta_data = metadata
                        article.embedding = None
                        updated += 1
                    else:
                        skipped += 1
                await session.commit()
                print(f"[{number}/{len(laws)}] {law.title}: {len(articles)} pasal")
            except Exception as error:
                await session.rollback()
                failed += 1
                print(f"[{number}/{len(laws)}] FAILED {law.catalog_url}: {error}", file=sys.stderr)

    print(f"Import complete: {created} created, {updated} updated, {skipped} unchanged, {failed} failed.")


async def run(apply: bool, limit: int | None) -> None:
    async with httpx.AsyncClient(
        timeout=60,
        follow_redirects=True,
        headers={"User-Agent": "Lex-DSS legal corpus importer/1.0"},
    ) as client:
        laws = await discover_laws(client)
        fallbacks = load_fallbacks()
        if limit is not None:
            laws = laws[:limit]
        print(f"Discovered {len(laws)} national laws from {BASE_URL}/uu.")
        if not apply:
            print("Dry run only. Pass --apply to download PDFs and write the database.")
            return
        await import_laws(laws, fallbacks, client)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="download and import every discovered law")
    parser.add_argument("--limit", type=int, help="process only the first N catalog laws")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    asyncio.run(run(args.apply, args.limit))


if __name__ == "__main__":
    main()
