#!/usr/bin/env python3
"""Generate seed_legal.py with full content."""
import os

path = 'C:/laragon/www/lex-dss/backend/scripts/seed_legal.py'
lines = []
lines.append("#!/usr/bin/env python3")
lines.append('"""Seed legal articles into database."""')
lines.append("import asyncio")
lines.append("import sys")
lines.append("from pathlib import Path")
lines.append("BACKEND_DIR = Path(__file__).resolve().parents[1]")
lines.append("sys.path.insert(0, str(BACKEND_DIR))")
lines.append("from sqlalchemy import select")
lines.append("from sqlalchemy.ext.asyncio import AsyncSession")
lines.append("from app.core.database import async_session_maker")
lines.append("from app.models.legal import LegalArticle, LegalHierarchy")
lines.append("from app.models.user import User")
lines.append("")
lines.append("print('seed_legal.py loaded')")

content = "\n".join(lines) + "\n"
with open(path, 'w') as f:
    f.write(content)
print('OK')