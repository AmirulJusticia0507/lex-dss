from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


class CaseLawBase(BaseModel):
    case_number: str
    case_title: str
    court_name: str
    case_type: str
    verdict_date: Optional[str] = None
    judge_name: Optional[str] = None
    legal_articles: Optional[list] = []
    summary: Optional[str] = None
    full_text: Optional[str] = None
    source_url: Optional[str] = None


class CaseLawCreate(CaseLawBase):
    pass


class CaseLawResponse(CaseLawBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/case-law/", response_model=dict)
async def list_case_law(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = "",
    court_name: str = "",
    case_type: str = "",
    db: AsyncSession = Depends(get_db),
):
    from app.models.legal import CaseLaw

    query = select(CaseLaw)
    count_query = select(func.count(CaseLaw.id))

    if search:
        query = query.where(
            (CaseLaw.case_title.ilike(f"%{search}%")) |
            (CaseLaw.case_number.ilike(f"%{search}%")) |
            (CaseLaw.summary.ilike(f"%{search}%"))
        )
        count_query = count_query.where(
            (CaseLaw.case_title.ilike(f"%{search}%")) |
            (CaseLaw.case_number.ilike(f"%{search}%")) |
            (CaseLaw.summary.ilike(f"%{search}%"))
        )

    if court_name:
        query = query.where(CaseLaw.court_name == court_name)
        count_query = count_query.where(CaseLaw.court_name == court_name)

    if case_type:
        query = query.where(CaseLaw.case_type == case_type)
        count_query = count_query.where(CaseLaw.case_type == case_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(CaseLaw.verdict_date.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    cases = result.scalars().all()

    return {
        "items": [
            {
                "id": str(c.id),
                "case_number": c.case_number,
                "case_title": c.case_title,
                "court_name": c.court_name,
                "case_type": c.case_type,
                "verdict_date": c.verdict_date.isoformat() if c.verdict_date else None,
                "judge_name": c.judge_name,
                "legal_articles": c.legal_articles or [],
                "summary": c.summary,
                "source_url": c.source_url,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cases
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


@router.get("/case-law/{case_id}", response_model=CaseLawResponse)
async def get_case_law(case_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.legal import CaseLaw

    result = await db.execute(select(CaseLaw).where(CaseLaw.id == case_id))
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return CaseLawResponse.model_validate(case)


@router.post("/case-law/", response_model=CaseLawResponse, status_code=201)
async def create_case_law(case: CaseLawCreate, db: AsyncSession = Depends(get_db)):
    from app.models.legal import CaseLaw

    db_case = CaseLaw(
        id=str(uuid.uuid4()),
        **case.model_dump(),
        created_at=datetime.utcnow(),
    )
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)
    return db_case


@router.get("/case-law/stats/summary")
async def get_case_law_stats(db: AsyncSession = Depends(get_db)):
    from app.models.legal import CaseLaw

    total_result = await db.execute(select(func.count(CaseLaw.id)))
    total = total_result.scalar()

    court_result = await db.execute(
        select(CaseLaw.court_name, func.count(CaseLaw.id))
        .group_by(CaseLaw.court_name)
        .order_by(func.count(CaseLaw.id).desc())
        .limit(10)
    )
    courts = [{"name": row[0], "count": row[1]} for row in court_result.fetchall()]

    type_result = await db.execute(
        select(CaseLaw.case_type, func.count(CaseLaw.id))
        .group_by(CaseLaw.case_type)
    )
    types = [{"name": row[0], "count": row[1]} for row in type_result.fetchall()]

    return {
        "total_cases": total,
        "by_court": courts,
        "by_type": types,
    }


from fastapi import HTTPException
