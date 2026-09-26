"""Build a reviewable metadata catalog from a Lex-Integrity PostgreSQL dump.

This deliberately does not write to the Lex-DSS database or treat scraped
metadata as legal article text. The resulting CSV is an intake queue for
source-document retrieval and validation.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterator


DEFAULT_DUMP = Path(r"C:\laragon\www\lex-integrity\dump.sql")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "lex-integrity-pilot"
COPY_START = re.compile(r"^COPY public\.rules \((.+)\) FROM stdin;$")

ESCAPES = {
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "\\": "\\",
}


def decode_copy_field(value: str) -> str | None:
    if value == r"\N":
        return None

    decoded: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\" or index + 1 >= len(value):
            decoded.append(char)
            index += 1
            continue

        next_char = value[index + 1]
        if next_char in ESCAPES:
            decoded.append(ESCAPES[next_char])
            index += 2
        elif next_char in "01234567":
            end = index + 2
            while end < min(index + 4, len(value)) and value[end] in "01234567":
                end += 1
            decoded.append(chr(int(value[index + 1 : end], 8)))
            index = end
        elif next_char == "x":
            end = index + 2
            while end < min(index + 4, len(value)) and value[end] in "0123456789abcdefABCDEF":
                end += 1
            if end == index + 2:
                decoded.append("\\x")
                index += 2
            else:
                decoded.append(chr(int(value[index + 2 : end], 16)))
                index = end
        else:
            decoded.append(next_char)
            index += 2

    return "".join(decoded)


def iter_rules(dump_path: Path) -> Iterator[dict[str, str | None]]:
    with dump_path.open("rb") as source:
        byte_order_mark = source.read(2)
        source.seek(0)
        encoding = "utf-16" if byte_order_mark in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
        dump = io.TextIOWrapper(source, encoding=encoding, errors="replace")
        columns: list[str] | None = None
        for line in dump:
            if columns is None:
                match = COPY_START.match(line.rstrip("\r\n"))
                if match:
                    columns = [column.strip() for column in match.group(1).split(",")]
                continue

            row = line.rstrip("\r\n")
            if row == r"\.":
                return

            values = row.split("\t")
            if len(values) != len(columns):
                raise ValueError(
                    f"Malformed rules row: expected {len(columns)} columns, got {len(values)}"
                )
            yield dict(zip(columns, (decode_copy_field(value) for value in values)))

    if columns is None:
        raise ValueError("COPY public.rules section was not found in the input dump")


def build_catalog(dump_path: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = output_dir / "lex-integrity-catalog.csv"
    columns = [
        "rule_code",
        "title",
        "regime",
        "category_raw",
        "publish_date",
        "source",
        "source_url",
        "pdf_url",
        "legacy_content",
        "content_characters",
        "has_article_text_candidate",
        "has_pdf_candidate",
        "embedding_present",
        "ingest_status",
    ]
    total = 0
    candidate_text = 0
    pdf_count = 0
    embeddings = 0
    sources: Counter[str] = Counter()
    categories: Counter[str] = Counter()

    with catalog_path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in iter_rules(dump_path):
            total += 1
            content = row.get("content") or ""
            has_text = len(content.strip()) > 300
            has_pdf = bool(row.get("pdf_url"))
            has_embedding = bool(row.get("embedding"))
            candidate_text += int(has_text)
            pdf_count += int(has_pdf)
            embeddings += int(has_embedding)
            sources[row.get("source") or "(kosong)"] += 1
            categories[row.get("category") or "(kosong)"] += 1

            writer.writerow(
                {
                    "rule_code": row.get("rule_code"),
                    "title": row.get("title"),
                    "regime": row.get("regime"),
                    "category_raw": row.get("category"),
                    "publish_date": row.get("publish_date"),
                    "source": row.get("source"),
                    "source_url": row.get("source_url"),
                    "pdf_url": row.get("pdf_url"),
                    "legacy_content": content,
                    "content_characters": len(content),
                    "has_article_text_candidate": has_text,
                    "has_pdf_candidate": has_pdf,
                    "embedding_present": has_embedding,
                    "ingest_status": "metadata_only_pending_source_extraction",
                }
            )

    summary: dict[str, object] = {
        "input_dump": str(dump_path),
        "catalog_csv": str(catalog_path),
        "records": total,
        "records_with_content_over_300_chars": candidate_text,
        "records_with_pdf_url": pdf_count,
        "records_with_embedding": embeddings,
        "sources": dict(sources),
        "raw_categories": dict(categories),
        "note": (
            "This is a metadata catalog only. PDF extraction, article segmentation, "
            "legal-type mapping, and source validation are still required."
        ),
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dump", nargs="?", type=Path, default=DEFAULT_DUMP)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    summary = build_catalog(args.dump, args.output_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
