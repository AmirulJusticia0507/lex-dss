
# Deviation Alert System (DAS) - Framework Pengawasan Peradilan

Sistem Penilaian Deviasi Putusan (DAS) adalah modul analisis kecerdasan buatan yang bertindak sebagai *Early Warning System* untuk mengidentifikasi indikasi anomali hukum, pertimbangan fiktif, atau penyalahgunaan wewenang (*abuse of power*) pada putusan pengadilan.

---

## 1. Metrik Penilaian Deviasi (Deviation Scoring Index)

Penilaian dilakukan menggunakan kalkulasi bobot komposit dari 4 indikator utama:

$$
Score_{Deviasi} = (w_1 \times I_{Hierarchy}) + (w_2 \times I_{Precedent}) + (w_3 \times I_{Evidence}) + (w_4 \times I_{Procedural})
$$

| Kode Indikator               | Nama Indikator                             | Deskripsi Analisis Hukum                                                                                                       | Bobot ($w$) |
| :--------------------------- | :----------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- | :------------ |
| **$I_{Hierarchy}$**  | **Normative Hierarchy Violation**    | Menguji apakah putusan mengabaikan aturan yang lebih tinggi (*Lex Superior*) atau aturan khusus (*Lex Specialis*).         | **35%** |
| **$I_{Precedent}$**  | **Jurisprudence Anomaly**            | Mengukur seberapa jauh amar putusan menyimpang dari konsistensi Putusan Landmark MA/MK untuk kasus serupa (*Stare Decisis*). | **25%** |
| **$I_{Evidence}$**   | **Anatomie Delict / Legal Fact Gap** | Membandingkan pembuktian unsur pidana/perdata di pertimbangan hukum (*Ratio Decidendi*) dengan amar akhir.                   | **25%** |
| **$I_{Procedural}$** | **AUPB / Procedural Flaw**           | Mendeteksi pelanggaran Asas-Asas Umum Pemerintahan yang Baik atau cacat formil hukum acara.                                    | **15%** |

---

## 2. Klasifikasi Risk Level & Ambang Batas (Threshold)

```text
[Skor Deviasi 0 - 100]
 ├── 0  - 29 : GREEN  (Low Risk / In Line with Pure Legal Logic)
 ├── 30 - 59 : YELLOW (Moderate Anomaly / Requires Internal Audit Note)
 └── 60 - 100: RED    (HIGH RISK DEVIATION / Trigger Automated Flagging to KY)
```


GREEN (0-29): Putusan selaras dengan logika hukum murni, pertimbangan norma konsisten.

YELLOW (30-59): Terdapat diskresi hakim yang cukup lebar atau terdapat perbedaan penafsiran pasal minor. Membutuhkan catatan pengawasan biasa.

RED (60-100): Anomali Berat. Putusan secara terang-terangan menabrak norma dasar, mengabaikan pasal kunci, atau bertentangan 180° dengan yurisprudensi tetap tanpa argumentasi hukum (Ratio Decidendi) yang memadai. Sistem otomatis menerbitkan tiket investigasi ke Komisi Yudisial.

3. Alur Sistem Pemrosesan (Pipeline Architecture)
   Plaintext
   [Dokumen Putusan Hakim (PDF/Word)]
   │
   ▼
   ┌───────────────────────────────────┐
   │  Parsing & Text Segmentation      │ ──> Pemisahan: Duduk Perkara, Pertimbangan Hukum,
   └─────────────────┬─────────────────┘      dan Amar Putusan
   │
   ▼
   ┌───────────────────────────────────┐
   │  Lex Integrity Evaluation Engine  │ ──> Ekstraksi Norma & Uji Kontradiksi
   └─────────────────┬─────────────────┘      (Lex Superior, Specialis, Posterior)
   │
   ▼
   ┌───────────────────────────────────┐
   │  Vector Store & RAG Comparison    │ ──> Benchmarking dengan Database Putusan Landmark
   └─────────────────┬─────────────────┘      & Yurisprudensi MA/MK
   │
   ▼
   ┌───────────────────────────────────┐
   │  Deviation Scoring Calculator     │ ──> Kalkulasi Skor 0 - 100 & Matriks Anomali
   └─────────────────┬─────────────────┘
   │
   ▼
   ┌───────────────────────────────────┐
   │ KY / Bawas Dashboard & Alerting   │ ──> Peringatan Otomatis jika Skor >= 60
   └───────────────────────────────────┘
4. Skema Schema Database Audit (PostgreSQL + pgvector)
   SQL
   -- Tabel Scoring Deviasi Putusan untuk Pengawasan KY
   CREATE TABLE judicial_deviation_reports (
   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
   verdict_number VARCHAR(100) NOT NULL,      -- Nomor Perkara / Putusan
   court_name VARCHAR(150) NOT NULL,          -- PN / PT / MA / MK
   judge_panel JSONB NOT NULL,                 -- Nama Susunan Majelis Hakim
   hierarchy_violation_score NUMERIC(5,2),     -- Skor I_Hierarchy
   precedent_anomaly_score NUMERIC(5,2),       -- Skor I_Precedent
   evidence_gap_score NUMERIC(5,2),            -- Skor I_Evidence
   total_deviation_score NUMERIC(5,2) NOT NULL,-- Skor Akumulasi (0-100)
   risk_level VARCHAR(20) NOT NULL,            -- GREEN, YELLOW, RED
   anomaly_summary TEXT NOT NULL,              -- Ringkasan temuan anomali oleh AI
   flagged_for_ky BOOLEAN DEFAULT FALSE,       -- Flag otomatis jika RED
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

CREATE INDEX idx_deviation_risk ON judicial_deviation_reports(risk_level, flagged_for_ky);
5. Algoritma Backend (Python / FastAPI Service)
Python
from pydantic import BaseModel
from typing import List, Dict

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

def calculate_deviation_score(data: DeviationScoreRequest) -> DeviationScoreResponse:
    # 1. Uji Kontradiksi Norma via Lex Integrity Engine
    hierarchy_score, hierarchy_logs = evaluate_norm_hierarchy(data.referenced_articles, data.ratio_decidendi_text)

    # 2. Uji Konsistensi Yurisprudensi via Vector Search (RAG)
    precedent_score, precedent_logs = evaluate_jurisprudence_gap(data.ratio_decidendi_text, data.verdict_amar_text)

    # 3. Uji Kesesuaian Unsur Hukum (Ratio vs Amar)
    evidence_score, evidence_logs = evaluate_element_match(data.ratio_decidendi_text, data.verdict_amar_text)

    # 4. Hitung Bobot Komposit
    total_score = (0.35 * hierarchy_score) + (0.25 * precedent_score) + (0.25 * evidence_score) + (0.15 * 0.0)

    # 5. Tentukan Risk Level
    if total_score >= 60.0:
        risk_level = "RED"
        flagged = True
    elif total_score >= 30.0:
        risk_level = "YELLOW"
        flagged = False
    else:
        risk_level = "GREEN"
        flagged = False

    anomalies = hierarchy_logs + precedent_logs + evidence_logs

    return DeviationScoreResponse(
        verdict_id=data.verdict_id,
        total_score=round(total_score, 2),
        risk_level=risk_level,
        anomalies=anomalies,
        flagged_to_ky=flagged
    )

---

### Keunggulan Alur Ini untuk Lembaga Pengawas:

1. **Objektivitas 100% Berbasis Logika Hukum:** KY tidak perlu ragu dituduh melakukan intervensi politik, karena laporan awal berbasis data kuantitatif (*Scoring Matrix*).
2. **Efisien & Terarah:** Dari puluhan ribu putusan per tahun, Komisi Yudisial dapat langsung memfokuskan tim verifikasinya hanya pada perkara berlabel **RED (High Risk Deviation)**.
3. **Mencegah "Putusan Selundupan":** Hakim nakal tidak bisa lagi menyembunyikan kekeliruan pertimbangan hukum di balik tebalnya berkas perkara, karena parser AI langsung mengekstrak *Ratio Decidendi* dan menyandingkannya dengan norma dasar.

<ElicitationsGroup message="Komponen atau fitur pendukung mana yang ingin Anda kembangkan selanjutnya?">    </ElicitationsGroup>
