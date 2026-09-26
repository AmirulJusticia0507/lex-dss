from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.audit import DecisionAuditLog
from app.models.user import User

router = APIRouter()


class DecisionAuditLogCreate(BaseModel):
    case_title: str = Field(..., max_length=255)
    ai_recommendation: str
    ai_risk_score: int = Field(..., ge=0, le=100)
    human_decision: Optional[str] = None
    is_deviated: bool = False
    deviation_justification: Optional[str] = None
    meta_data: Optional[dict] = None


class DecisionAuditLogResponse(BaseModel):
    id: uuid.UUID
    case_title: str
    ai_recommendation: str
    ai_risk_score: int
    human_decision: Optional[str]
    is_deviated: bool
    deviation_justification: Optional[str]
    user_id: uuid.UUID
    meta_data: Optional[dict]
    timestamp: str
    
    class Config:
        from_attributes = True


class DecisionAuditLogList(BaseModel):
    items: List[DecisionAuditLogResponse]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=DecisionAuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    log_in: DecisionAuditLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    log = DecisionAuditLog(
        **log_in.model_dump(),
        user_id=current_user.id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/", response_model=DecisionAuditLogList)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_deviated: Optional[bool] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(DecisionAuditLog)
    
    if is_deviated is not None:
        query = query.where(DecisionAuditLog.is_deviated == is_deviated)
    if user_id:
        query = query.where(DecisionAuditLog.user_id == user_id)
    if start_date:
        query = query.where(DecisionAuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(DecisionAuditLog.timestamp <= end_date)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    query = query.order_by(DecisionAuditLog.timestamp.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return DecisionAuditLogList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}", response_model=DecisionAuditLogResponse)
async def get_audit_log(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(DecisionAuditLog).where(DecisionAuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log


@router.get("/deviations/summary", response_model=dict)
async def get_deviation_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    total_result = await db.execute(select(func.count(DecisionAuditLog.id)))
    total = total_result.scalar()
    
    deviated_result = await db.execute(
        select(func.count(DecisionAuditLog.id)).where(DecisionAuditLog.is_deviated == True)
    )
    deviated = deviated_result.scalar()
    
    return {
        "total_decisions": total,
        "deviated_decisions": deviated,
        "deviation_rate": round(deviated / total * 100, 2) if total > 0 else 0,
    }