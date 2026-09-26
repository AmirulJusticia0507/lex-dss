"""Idempotently import the curated starter law corpus.

Run from backend/: python scripts/seed_core_laws.py [--apply]
Without --apply this only validates the JSON and prints the planned changes.
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
CORPUS_PATH = BACKEND_DIR / "data" / "legal-seed" / "core-laws.json"


def load_corpus() -> list[dict]:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    documents = corpus["documents"]
    seen: set[tuple[str, str]] = set()
    for item in documents:
        for field in ("document_title", "article_number", "content", "hierarchy_type"):
            if not item.get(field):
                raise ValueError(f"Missing {field!r} on corpus record {item!r}")
        key = (item["document_title"], str(item["article_number"]))
        if key in seen:
            raise ValueError(f"Duplicate document/article key: {key}")
        seen.add(key)
    return documents


async def run(apply: bool) -> None:
    documents = load_corpus()
    if not apply:
        print(f"Validated {len(documents)} records in {CORPUS_PATH}")
        print("Dry run only. Pass --apply to write these records to the configured database.")
        return

    sys.path.insert(0, str(BACKEND_DIR))
    from sqlalchemy import select

    from app.core.database import async_session_maker
    from app.models.legal import LegalArticle, LegalHierarchy

    created = updated = unchanged = 0
    async with async_session_maker() as session:
        hierarchy_names = {row["hierarchy_type"] for row in documents}
        hierarchy_result = await session.execute(
            select(LegalHierarchy).where(LegalHierarchy.type_name.in_(hierarchy_names))
        )
        hierarchies = {row.type_name: row.id for row in hierarchy_result.scalars()}
        missing = hierarchy_names - hierarchies.keys()
        if missing:
            raise RuntimeError(
                "Missing legal_hierarchy rows: " + ", ".join(sorted(missing))
                + ". Apply the project's initial migration first."
            )

        for item in documents:
            result = await session.execute(
                select(LegalArticle).where(
                    LegalArticle.document_title == item["document_title"],
                    LegalArticle.article_number == str(item["article_number"]),
                )
            )
            article = result.scalar_one_or_none()
            values = {
                "content": item["content"],
                "domain": item.get("domain"),
                "hierarchy_id": hierarchies[item["hierarchy_type"]],
                "meta_data": item.get("meta_data", {}),
            }
            if article is None:
                session.add(LegalArticle(
                    document_title=item["document_title"],
                    article_number=str(item["article_number"]),
                    **values,
                ))
                created += 1
            elif any(getattr(article, key) != value for key, value in values.items()):
                content_changed = article.content != values["content"]
                for key, value in values.items():
                    setattr(article, key, value)
                if content_changed:
                    article.embedding = None
                updated += 1
            else:
                unchanged += 1

        await session.commit()

    print(f"Seed complete: {created} created, {updated} updated, {unchanged} unchanged.")
    print("New or changed article text has no embedding; run the project's embedding/indexing workflow afterward.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write records to the configured database")
    args = parser.parse_args()
    asyncio.run(run(args.apply))


if __name__ == "__main__":
    main()
