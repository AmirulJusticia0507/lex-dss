from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.audit import JudicialDeviationReport
from app.models.user import User
from app.engine.deviation import calculate_deviation_score, DeviationScoreRequest

router = APIRouter()


class DeviationScoreRequestModel(BaseModel):
    verdict_id: str
    ratio_decidendi_text: str
    verdict_amar_text: str
    referenced_articles: List[str]


class DeviationScoreResponseModel(BaseModel):
    verdict_id: str
    total_score: float
    risk_level: str
    anomalies: List[Dict[str, str]]
    flagged_to_ky: bool


class JudicialDeviationReportCreate(BaseModel):
    verdict_number: str = Field(..., max_length=100)
    court_name: str = Field(..., max_length=150)
    judge_panel: Dict
    hierarchy_violation_score: Optional[float] = None
    precedent_anomaly_score: Optional[float] = None
    evidence_gap_score: Optional[float] = None
    procedural_flaw_score: Optional[float] = None
    total_deviation_score: float
    risk_level: str = Field(..., pattern="^(GREEN|YELLOW|RED)$")
    anomaly_summary: str
    flagged_for_ky: bool = False
    meta_data: Optional[dict] = None


class JudicialDeviationReportResponse(BaseModel):
    id: uuid.UUID
    verdict_number: str
    court_name: str
    judge_panel: Dict
    hierarchy_violation_score: Optional[float]
    precedent_anomaly_score: Optional[float]
    evidence_gap_score: Optional[float]
    procedural_flaw_score: Optional[float]
    total_deviation_score: float
    risk_level: str
    anomaly_summary: str
    flagged_for_ky: bool
    meta_data: Optional[dict]
    created_at: str
    
    class Config:
        from_attributes = True


class JudicialDeviationReportList(BaseModel):
    items: List[JudicialDeviationReportResponse]
    total: int
    page: int
    page_size: int


@router.post("/score", response_model=DeviationScoreResponseModel)
async def score_deviation(
    request: DeviationScoreRequestModel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    engine_request = DeviationScoreRequest(
        verdict_id=request.verdict_id,
        ratio_decidendi_text=request.ratio_decidendi_text,
        verdict_amar_text=request.verdict_amar_text,
        referenced_articles=request.referenced_articles,
    )
    response = calculate_deviation_score(engine_request)
    return response


@router.post("/reports", response_model=JudicialDeviationReportResponse, status_code=status.HTTP_201_CREATED)
async def create_deviation_report(
    report_in: JudicialDeviationReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    report = JudicialDeviationReport(**report_in.model_dump())
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/reports", response_model=JudicialDeviationReportList)
async def list_deviation_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_level: Optional[str] = Query(None),
    court_name: Optional[str] = Query(None),
    flagged_for_ky: Optional[bool] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(JudicialDeviationReport)
    
    if risk_level:
        query = query.where(JudicialDeviationReport.risk_level == risk_level)
    if court_name:
        query = query.where(JudicialDeviationReport.court_name.ilike(f"%{court_name}%"))
    if flagged_for_ky is not None:
        query = query.where(JudicialDeviationReport.flagged_for_ky == flagged_for_ky)
    if start_date:
        query = query.where(JudicialDeviationReport.created_at >= start_date)
    if end_date:
        query = query.where(JudicialDeviationReport.created_at <= end_date)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(JudicialDeviationReport.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return JudicialDeviationReportList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/reports/{report_id}", response_model=JudicialDeviationReportResponse)
async def get_deviation_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(JudicialDeviationReport).where(JudicialDeviationReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Deviation report not found")
    return report


@router.get("/reports/stats/summary", response_model=dict)
async def get_deviation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    total_result = await db.execute(select(func.count(JudicialDeviationReport.id)))
    total = total_result.scalar()
    
    red_result = await db.execute(
        select(func.count(JudicialDeviationReport.id)).where(JudicialDeviationReport.risk_level == "RED")
    )
    red_count = red_result.scalar()
    
    yellow_result = await db.execute(
        select(func.count(JudicialDeviationReport.id)).where(JudicialDeviationReport.risk_level == "YELLOW")
    )
    yellow_count = yellow_result.scalar()
    
    green_result = await db.execute(
        select(func.count(JudicialDeviationReport.id)).where(JudicialDeviationReport.risk_level == "GREEN")
    )
    green_count = green_result.scalar()
    
    flagged_result = await db.execute(
        select(func.count(JudicialDeviationReport.id)).where(JudicialDeviationReport.flagged_for_ky == True)
    )
    flagged_count = flagged_result.scalar()
    
    return {
        "total_reports": total,
        "red": red_count,
        "yellow": yellow_count,
        "green": green_count,
        "flagged_for_ky": flagged_count,
    }