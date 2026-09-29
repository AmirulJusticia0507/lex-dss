import csv
import io
import json
import re
import uuid
import zipfile
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker, get_db
from app.core.security import get_current_active_user, require_roles
from app.engine.deviation import DeviationScoreRequest, DeviationScoreResponse, calculate_deviation_score
from app.models.audit import JudicialDeviationReport
from app.models.user import User

router = APIRouter()
# ponytail: process-local job state; replace with a durable queue when multiple workers are deployed.
document_jobs: Dict[str, Dict[str, str]] = {}


class KYFlagRequest(BaseModel):
    action: Literal["SUBMIT", "DISMISS", "ESCALATE"]
    notes: Optional[str] = Field(None, max_length=2000)
    escalate_to: Optional[str] = Field(None, max_length=100)

    @model_validator(mode="after")
    def validate_action(self):
        if self.action == "DISMISS" and not self.notes:
            raise ValueError("notes wajib diisi saat action DISMISS")
        if self.action == "ESCALATE" and not self.escalate_to:
            raise ValueError("escalate_to wajib diisi saat action ESCALATE")
        return self


class JudicialDeviationReportResponse(BaseModel):
    id: uuid.UUID
    verdict_number: str
    court_name: str
    judge_panel: Dict[str, Any]
    hierarchy_violation_score: Optional[float]
    precedent_anomaly_score: Optional[float]
    evidence_gap_score: Optional[float]
    procedural_flaw_score: Optional[float]
    total_deviation_score: float
    risk_level: str
    anomaly_summary: str
    flagged_for_ky: bool
    meta_data: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class JudicialDeviationReportList(BaseModel):
    items: List[JudicialDeviationReportResponse]
    total: int
    page: int
    page_size: int


def _report_from_score(score: DeviationScoreResponse) -> JudicialDeviationReport:
    return JudicialDeviationReport(
        id=uuid.UUID(score.report_id), verdict_number=score.verdict_number, court_name=score.court_name,
        judge_panel={"members": score.judge_panel}, hierarchy_violation_score=score.indicators["hierarchy_violation_score"],
        precedent_anomaly_score=score.indicators["precedent_anomaly_score"], evidence_gap_score=score.indicators["evidence_gap_score"],
        procedural_flaw_score=score.indicators["procedural_flaw_score"], total_deviation_score=score.total_deviation_score,
        risk_level=score.risk_level, anomaly_summary=score.anomaly_summary, flagged_for_ky=score.flagged_for_ky,
        meta_data={"anomalies": score.anomalies, "weights": score.weights, "recommended_action": score.recommended_action},
    )


async def _get_report(report_id: uuid.UUID, db: AsyncSession) -> JudicialDeviationReport:
    report = await db.scalar(select(JudicialDeviationReport).where(JudicialDeviationReport.id == report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Deviation report not found")
    return report


def _document_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".docx"):
        with zipfile.ZipFile(io.BytesIO(content)) as document:
            xml = document.read("word/document.xml").decode("utf-8")
        return re.sub(r"<[^>]+>", " ", xml).replace("&amp;", "&")
    return " ".join(match.decode("latin-1", "ignore") for match in re.findall(rb"\(([^()]*)\)\s*Tj", content))


async def _score_document_job(job_id: str, filename: str, content: bytes, court_name: str, domain: str, verdict_number: Optional[str]):
    document_jobs[job_id]["status"] = "PROCESSING"
    try:
        text = _document_text(filename, content).strip()
        if not text:
            raise ValueError("Teks putusan tidak dapat diekstrak dari dokumen")
        score = calculate_deviation_score(DeviationScoreRequest(
            verdict_number=verdict_number or filename, court_name=court_name, ratio_decidendi_text=text,
            verdict_amar_text=text, referenced_articles=[], domain=domain,
        ))
        async with async_session_maker() as db:
            db.add(_report_from_score(score))
            await db.commit()
        document_jobs[job_id].update(status="COMPLETED", report_id=score.report_id)
    except Exception as error:
        document_jobs[job_id].update(status="FAILED", error=str(error))


@router.post("/score", response_model=DeviationScoreResponse, status_code=status.HTTP_201_CREATED)
async def score_deviation(request: DeviationScoreRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    score = calculate_deviation_score(request)
    if request.save_report:
        db.add(_report_from_score(score))
        await db.commit()
    return score


@router.post("/score/document", status_code=status.HTTP_202_ACCEPTED)
async def score_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), court_name: str = Form(...), domain: str = Form("HTN"), verdict_number: Optional[str] = Form(None), current_user: User = Depends(get_current_active_user)):
    if not (file.filename or "").lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Gunakan berkas PDF atau DOCX")
    job_id = str(uuid.uuid4())
    document_jobs[job_id] = {"status": "QUEUED"}
    background_tasks.add_task(_score_document_job, job_id, file.filename, await file.read(), court_name, domain, verdict_number)
    return {"job_id": job_id, "status": "QUEUED", "filename": file.filename, "court_name": court_name, "domain": domain, "verdict_number": verdict_number}


@router.get("/score/document/{job_id}")
async def get_document_score_job(job_id: str, current_user: User = Depends(get_current_active_user)):
    job = document_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Document scoring job not found")
    return {"job_id": job_id, **job}


@router.get("/reports", response_model=JudicialDeviationReportList)
async def list_deviation_reports(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    risk_level: Optional[Literal["GREEN", "YELLOW", "RED"]] = None, court_name: Optional[str] = None,
    flagged_for_ky: Optional[bool] = None, min_score: Optional[float] = Query(None, ge=0, le=100), max_score: Optional[float] = Query(None, ge=0, le=100),
    date_from: Optional[datetime] = None, date_to: Optional[datetime] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("admin", "auditor")),
):
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(status_code=422, detail="min_score tidak boleh lebih besar dari max_score")
    query = select(JudicialDeviationReport)
    conditions = [JudicialDeviationReport.risk_level == risk_level if risk_level else None, JudicialDeviationReport.court_name.ilike(f"%{court_name}%") if court_name else None, JudicialDeviationReport.flagged_for_ky == flagged_for_ky if flagged_for_ky is not None else None, JudicialDeviationReport.total_deviation_score >= min_score if min_score is not None else None, JudicialDeviationReport.total_deviation_score <= max_score if max_score is not None else None, JudicialDeviationReport.created_at >= date_from if date_from else None, JudicialDeviationReport.created_at <= date_to if date_to else None]
    for condition in conditions:
        if condition is not None: query = query.where(condition)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    items = (await db.execute(query.order_by(JudicialDeviationReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return JudicialDeviationReportList(items=items, total=total or 0, page=page, page_size=page_size)


@router.get("/statistics")
async def get_deviation_statistics(date_from: Optional[date] = None, date_to: Optional[date] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    query = select(JudicialDeviationReport)
    if date_from: query = query.where(JudicialDeviationReport.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to: query = query.where(JudicialDeviationReport.created_at <= datetime.combine(date_to, datetime.max.time()))
    reports = (await db.execute(query)).scalars().all()
    risks = {level: sum(report.risk_level == level for report in reports) for level in ("GREEN", "YELLOW", "RED")}
    courts: Dict[str, Dict[str, Any]] = {}; codes: Dict[str, int] = {}
    for report in reports:
        court = courts.setdefault(report.court_name, {"court_name": report.court_name, "red": 0, "yellow": 0, "green": 0}); court[report.risk_level.lower()] += 1
        for anomaly in (report.meta_data or {}).get("anomalies", []):
            code = anomaly.get("code", anomaly.get("indicator", "UNKNOWN")); codes[code] = codes.get(code, 0) + 1
    return {"period": {"from": str(date_from or ""), "to": str(date_to or "")}, "total_reports": len(reports), "by_risk_level": risks, "flagged_for_ky": sum(report.flagged_for_ky for report in reports), "top_anomaly_codes": [{"code": code, "count": count} for code, count in sorted(codes.items(), key=lambda item: item[1], reverse=True)[:10]], "by_court": list(courts.values())}


@router.get("/reports/{report_id}", response_model=JudicialDeviationReportResponse)
async def get_deviation_report(report_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("admin", "auditor"))):
    return await _get_report(report_id, db)


@router.post("/reports/{report_id}/ky-flag")
async def update_ky_flag(report_id: uuid.UUID, request: KYFlagRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("admin", "auditor"))):
    report = await _get_report(report_id, db)
    report.flagged_for_ky = request.action != "DISMISS"
    report.meta_data = {**(report.meta_data or {}), "ky_flag": {"action": request.action, "notes": request.notes, "escalate_to": request.escalate_to, "updated_at": datetime.utcnow().isoformat()}}
    await db.commit()
    return {"report_id": str(report.id), "flagged_for_ky": report.flagged_for_ky, "action": request.action}


@router.get("/reports/{report_id}/export")
async def export_deviation_report(report_id: uuid.UUID, format: Literal["json", "csv", "pdf"] = "json", db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("admin", "auditor"))):
    report = await _get_report(report_id, db)
    payload = JudicialDeviationReportResponse.model_validate(report).model_dump(mode="json")
    if format == "json": return JSONResponse(payload, headers={"Content-Disposition": f'attachment; filename="deviation-{report_id}.json"'})
    if format == "csv":
        output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=payload.keys()); writer.writeheader(); writer.writerow({key: json.dumps(value) if isinstance(value, (dict, list)) else value for key, value in payload.items()})
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="deviation-{report_id}.csv"'})
    pdf_text = f"Deviation Report - {report.verdict_number} | Score: {report.total_deviation_score} ({report.risk_level})".replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({pdf_text}) Tj ET"; pdf = f"%PDF-1.4\\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\\n4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\\n5 0 obj<</Length {len(stream)}>>stream\\n{stream}\\nendstream endobj\\ntrailer<</Root 1 0 R>>\\n%%EOF".encode()
    return StreamingResponse(iter([pdf]), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="deviation-{report_id}.pdf"'})
