import uuid
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from dataclasses import dataclass


class DeviationScoreRequest(BaseModel):
    verdict_number: str
    court_name: str
    judge_panel: List[str] = []
    ratio_decidendi_text: str
    verdict_amar_text: str
    referenced_articles: List[str]
    domain: str = "HTN"
    save_report: bool = True


class DeviationScoreResponse(BaseModel):
    report_id: str
    verdict_number: str
    court_name: str
    judge_panel: List[str] = []
    total_deviation_score: float
    risk_level: str
    flagged_for_ky: bool
    indicators: Dict[str, float] = {}
    weights: Dict[str, float] = {}
    anomalies: List[Dict] = []
    anomaly_summary: str = ""
    recommended_action: str = ""
    created_at: str = ""
    request_id: str = ""


@dataclass
class IndicatorScore:
    name: str
    score: float
    weight: float
    details: List[Dict[str, str]]


def evaluate_norm_hierarchy(referenced_articles: List[str], ratio_decidendi: str) -> tuple[float, List[Dict[str, str]]]:
    logs = []
    
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
            if kw.lower() in ratio_decidendi.lower():
                mentioned_hierarchies.append(level)
                break
    
    if not mentioned_hierarchies:
        logs.append({
            "indicator": "hierarchy",
            "message": "Tidak ditemukan referensi hierarki norma dalam pertimbangan hukum",
            "severity": "MEDIUM",
        })
        return 50.0, logs
    
    if "UUD" in mentioned_hierarchies and ("PERDA" in mentioned_hierarchies or "PERMEN" in mentioned_hierarchies):
        logs.append({
            "indicator": "hierarchy",
            "message": "Potensi pelanggaran Lex Superior: Perda/Permen dirujuk tanpa analisis keselarasan dengan UUD/UU",
            "severity": "HIGH",
        })
        return 80.0, logs
    
    if "UU" in mentioned_hierarchies and "PERDA" in mentioned_hierarchies:
        logs.append({
            "indicator": "hierarchy",
            "message": "Perlu verifikasi keselarasan Perda dengan UU di atasnya (Pasal 7 UU 12/2011)",
            "severity": "MEDIUM",
        })
        return 40.0, logs
    
    logs.append({
        "indicator": "hierarchy",
        "message": "Hierarki norma teridentifikasi, perlu verifikasi mendalam",
        "severity": "LOW",
    })
    return 20.0, logs


def evaluate_jurisprudence_gap(ratio_decidendi: str, verdict_amar: str) -> tuple[float, List[Dict[str, str]]]:
    logs = []
    
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
    
    has_precedent = any(ind in ratio_decidendi.lower() for ind in precedent_indicators)
    
    if not has_precedent:
        logs.append({
            "indicator": "precedent",
            "message": "Tidak ditemukan rujukan yurisprudensi/putusan terdahulu dalam pertimbangan hukum",
            "severity": "MEDIUM",
        })
        return 60.0, logs
    
    if "berbeda" in ratio_decidendi.lower() or "menyimpang" in ratio_decidendi.lower():
        if not any(kw in ratio_decidendi.lower() for kw in ["alasan", "karena", "dengan pertimbangan", "berdasarkan"]):
            logs.append({
                "indicator": "precedent",
                "message": "Terdeteksi pernyataan penyimpangan dari yurisprudensi tanpa argumentasi hukum yang memadai",
                "severity": "HIGH",
            })
            return 85.0, logs
    
    logs.append({
        "indicator": "precedent",
        "message": "Rujukan yurisprudensi ditemukan, konsistensi perlu diverifikasi",
        "severity": "LOW",
    })
    return 15.0, logs


def evaluate_element_match(ratio_decidendi: str, verdict_amar: str) -> tuple[float, List[Dict[str, str]]]:
    logs = []
    
    element_keywords = {
        "pidana": ["unsur", "dolus", "culpa", "opzet", "schuld", "anschuldig", "kejahatan", "pidana"],
        "perdata": ["wanprestasi", "force majeure", "kewajiban", "hak", "perjanjian", "kontrak"],
        "htn": ["kewenangan", "wewenang", "asas", "aadb", "auupb", "detournement"],
    }
    
    detected_domains = []
    for domain, keywords in element_keywords.items():
        if any(kw in ratio_decidendi.lower() for kw in keywords):
            detected_domains.append(domain)
    
    if not detected_domains:
        logs.append({
            "indicator": "evidence",
            "message": "Tidak teridentifikasi domain hukum spesifik (pidana/perdata/HTN) dalam pertimbangan",
            "severity": "MEDIUM",
        })
        return 50.0, logs
    
    if "pidana" in detected_domains:
        has_obektif = any(kw in ratio_decidendi.lower() for kw in ["perbuatan", "hasil", "kausalitas"])
        has_subjektif = any(kw in ratio_decidendi.lower() for kw in ["dolus", "culpa", "keajaiban", "kesengajaan"])
        
        if not has_obektif or not has_subjektif:
            logs.append({
                "indicator": "evidence",
                "message": "Anatomie Van Delict tidak lengkap: unsur obyektif/subyektif tidak terpenuhi dalam pertimbangan",
                "severity": "HIGH",
            })
            return 75.0, logs
    
    if "perdata" in detected_domains:
        has_wanprestasi = "wanprestasi" in ratio_decidendi.lower()
        has_force_majeure = "force majeure" in ratio_decidendi.lower()
        
        if "pembatalan" in verdict_amar.lower() and not has_wanprestasi and not has_force_majeure:
            logs.append({
                "indicator": "evidence",
                "message": "Putusan pembatalan perjanjian tanpa analisis wanprestasi/force majeure yang memadai",
                "severity": "HIGH",
            })
            return 70.0, logs
    
    logs.append({
        "indicator": "evidence",
        "message": f"Elemen hukum domain {', '.join(detected_domains)} teridentifikasi",
        "severity": "LOW",
    })
    return 20.0, logs


def calculate_deviation_score(data: DeviationScoreRequest) -> DeviationScoreResponse:
    hierarchy_score, hierarchy_logs = evaluate_norm_hierarchy(data.referenced_articles, data.ratio_decidendi_text)
    precedent_score, precedent_logs = evaluate_jurisprudence_gap(data.ratio_decidendi_text, data.verdict_amar_text)
    evidence_score, evidence_logs = evaluate_element_match(data.ratio_decidendi_text, data.verdict_amar_text)

    procedural_score = 0.0
    procedural_logs = [{
        "indicator": "procedural",
        "message": "Analisis prosedural memerlukan parsing dokumen putusan lengkap",
        "severity": "LOW",
    }]

    weights = {"hierarchy": 0.35, "precedent": 0.25, "evidence": 0.25, "procedural": 0.15}
    total_score = (
        weights["hierarchy"] * hierarchy_score +
        weights["precedent"] * precedent_score +
        weights["evidence"] * evidence_score +
        weights["procedural"] * procedural_score
    )

    if total_score >= 60.0:
        risk_level = "RED"
        flagged = True
    elif total_score >= 30.0:
        risk_level = "YELLOW"
        flagged = False
    else:
        risk_level = "GREEN"
        flagged = False

    all_anomalies = _enrich_anomalies(hierarchy_logs + precedent_logs + evidence_logs + procedural_logs)

    anomaly_summary = _build_anomaly_summary(all_anomalies)
    recommended_action = _build_recommended_action(risk_level, all_anomalies)

    return DeviationScoreResponse(
        report_id=str(uuid.uuid4()),
        verdict_number=data.verdict_number,
        court_name=data.court_name,
        judge_panel=data.judge_panel,
        total_deviation_score=round(total_score, 2),
        risk_level=risk_level,
        flagged_for_ky=flagged,
        indicators={
            "hierarchy_violation_score": hierarchy_score,
            "precedent_anomaly_score": precedent_score,
            "evidence_gap_score": evidence_score,
            "procedural_flaw_score": procedural_score,
        },
        weights=weights,
        anomalies=all_anomalies,
        anomaly_summary=anomaly_summary,
        recommended_action=recommended_action,
        created_at=datetime.now(timezone(timedelta(hours=7))).isoformat(),
        request_id=str(uuid.uuid4()),
    )


def _build_anomaly_summary(anomalies: List[Dict[str, str]]) -> str:
    high = [a for a in anomalies if a.get("severity") == "HIGH"]
    medium = [a for a in anomalies if a.get("severity") == "MEDIUM"]
    low = [a for a in anomalies if a.get("severity") == "LOW"]
    parts = [f"Teridentifikasi {len(anomalies)} anomali"]
    if high:
        parts.append(f"({len(high)} HIGH")
    if medium:
        parts.append(f", {len(medium)} MEDIUM")
    if low:
        parts.append(f", {len(low)} LOW")
    parts.append(")")
    return "".join(parts)


def _enrich_anomalies(anomalies: List[Dict[str, str]]) -> List[Dict]:
    """Expose the evidence needed by clients without changing engine heuristics."""
    metadata = {
        "hierarchy": ("I_Hierarchy", "NORM_NOT_ENFORCED", "Pasal 7 UU 12/2011"),
        "precedent": ("I_Precedent", "PRECEDENT_INCONSISTENCY", "Yurisprudensi Mahkamah Agung"),
        "evidence": ("I_Evidence", "EVIDENCE_GAP", "KUHAP dan asas pembuktian"),
        "procedural": ("I_Procedural", "PROCEDURAL_REVIEW_REQUIRED", "Hukum acara yang berlaku"),
    }
    return [{
        **item,
        "indicator": metadata[item["indicator"]][0],
        "code": metadata[item["indicator"]][1],
        "finding": item["message"],
        "evidence": item["message"],
        "legal_basis": [metadata[item["indicator"]][2]],
        "recommendation": "Verifikasi kembali temuan ini terhadap berkas putusan lengkap.",
    } for item in anomalies]


def _build_recommended_action(risk_level: str, anomalies: List[Dict[str, str]]) -> str:
    high_anomalies = [a for a in anomalies if a.get("severity") == "HIGH"]
    if risk_level == "RED":
        return "Kirim ke tim verifikasi KY dalam 7 hari kerja."
    if risk_level == "YELLOW":
        return "Catat sebagai temuan pengawasan internal; lakukan review mendalam."
    if high_anomalies:
        return "Perlu audit internal untuk memverifikasi temuan HIGH."
    return "Tidak memerlukan tindakan segera; pantau secara berkala."
