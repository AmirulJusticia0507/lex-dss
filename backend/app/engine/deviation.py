from pydantic import BaseModel
from typing import List, Dict, Optional
from dataclasses import dataclass


class DeviationScoreRequest(BaseModel):
    verdict_id: str
    ratio_decidendi_text: str
    verdict_amar_text: str
    referenced_articles: List[str]


class DeviationScoreResponse(BaseModel):
    verdict_id: str
    total_score: float
    risk_level: str
    anomalies: List[Dict[str, str]]
    flagged_to_ky: bool


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
    
    total_score = (
        0.35 * hierarchy_score +
        0.25 * precedent_score +
        0.25 * evidence_score +
        0.15 * procedural_score
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
    
    all_anomalies = hierarchy_logs + precedent_logs + evidence_logs + procedural_logs
    
    return DeviationScoreResponse(
        verdict_id=data.verdict_id,
        total_score=round(total_score, 2),
        risk_level=risk_level,
        anomalies=all_anomalies,
        flagged_to_ky=flagged,
    )