#!/usr/bin/env python3
"""Seed legal articles into database.

Usage:
    python scripts/seed_legal.py [--count N] [--real] [--synthetic]
"""
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.models.legal import LegalArticle, LegalHierarchy
from app.models.user import User

print("seed_legal.py loaded")