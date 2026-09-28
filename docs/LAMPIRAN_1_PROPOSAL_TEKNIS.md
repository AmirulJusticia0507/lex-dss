# Lampiran 1: Proposal Teknis Ringkas Lex-DSS

---

## 1. Identitas Pengembang

| Item | Keterangan |
|------|-----------|
| Nama | Amirul Putra Justicia |
| Status | Pelaku Usaha Perseorangan |
| NIB | 0612220049872 |
| Email | amirulputra0507@gmail.com |
| Telepon | +6282134402383 |

---

## 2. Tentang Lex-DSS

**Lex-DSS (Lex Decision Support System)** adalah sistem pendukung keputusan hukum berbasis kecerdasan buatan yang dirancang untuk:

- **Deteksi Konflik Norma Hukum** — menganalisis kontradiksi antar peraturan perundang-undangan (Lex Superior, Lex Specialis, Lex Posterior)
- **Deviation Alert System** — mendeteksi penyimpangan putusan pengadilan dari logika hukum murni
- **AI Legal Assistant** — memberikan opini hukum berbasis RAG (Retrieval-Augmented Generation) dengan anti-hallucination
- **Wealth Anomaly Detection** *(baru)* — mendeteksi indikasi penyalahgunaan wewenang berbasis data kekayaan

---

## 3. Masalah yang Dipecahkan

Indonesia memiliki lebih dari **44.570 aturan hukum** yang saling tumpang tindih. Akibatnya:

- Konflik norma sulit dideteksi secara manual
- Putusan pengadilan kadang menyimpang dari logika hukum murni
- Penyalahgunaan wewenang oleh pejabat publik sulit dideteksi secara dini
- Data kekayaan pejabat tidak terintegrasi dengan analisis risiko

---

## 4. Metode Pengembangan

### 4.1 Teknologi AI

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| LLM | Ollama (deepseek-r1:8b) | Reasoning engine |
| Embedding | nomic-embed-text (768-dim) | Semantic search |
| Vector DB | PostgreSQL + pgvector | Penyimpanan & pencarian vektor |
| RAG Pipeline | LangChain | Retrieval-Augmented Generation |
| Rules Engine | Custom (Lex Integrity) | Deteksi konflik norma |

### 4.2 Metode Analisis Data LHKPN

```
Input: Data LHKPN publik (agregat/anonim)
    ↓
Preprocessing: Normalisasi, cleaning, validasi
    ↓
Feature Engineering:
  - Wealth Velocity Score (perubahan harta tahunan)
  - Income-to-Wealth Ratio
  - Peer Comparison Score (z-score jabatan serupa)
  - Asset Composition Anomaly
    ↓
Model: Rule-based + Statistical Anomaly Detection
    ↓
Output: Risk Score (0-100) + Flag untuk review manusia
```

---

## 5. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                    Lex-DSS Platform                      │
├─────────────────────────────────────────────────────────┤
│  Frontend (Vue.js)  │  Backend (FastAPI)  │  AI Engine  │
│                     │                      │             │
│  - Dashboard        │  - REST API          │  - RAG      │
│  - Conflict Checker │  - Auth (JWT)        │  - Deviation│
│  - DSS Panel        │  - Integration       │  - Anomaly  │
│  - Legal Library    │  - Audit Log         │  - Rules    │
└─────────────────────┴──────────────────────┴─────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   PostgreSQL      │
                    │   + pgvector      │
                    └───────────────────┘
```

---

## 6. Timeline Pilot

| Fase | Aktivitas | Durasi |
|------|-----------|--------|
| 1 | Persiapan infrastruktur & dataset | 2 minggu |
| 2 | Development Wealth Anomaly Engine | 3 minggu |
| 3 | Integration & Testing | 2 minggu |
| 4 | Pilot Testing & Evaluasi | 2 minggu |
| 5 | Laporan & Rekomendasi | 1 minggu |
| **Total** | | **10 minggu** |

---

## 7. Expected Output

1. **Wealth Anomaly Detection Engine** — mampu mendeteksi anomali kekayaan dengan akurasi >80%
2. **Dashboard Monitoring** — visualisasi kepatuhan LHKPN per instansi
3. **Laporan Pilot** — evaluasi performa dan rekomendasi kebijakan
4. **Publikasi Ilmiah** — jurnal/conference paper tentang deteksi anomali kekayaan berbasis AI

---

## 8. Keberlanjutan

Setelah pilot, Lex-DSS akan:
- Diintegrasikan dengan sistem monitoring KPK
- Dikembangkan menjadi tools open-source untuk akademisi
- Diterapkan di instansi pemerintah untuk monitoring kepatuhan

---

**Amirul Putra Justicia**
Pengembang Lex-DSS
