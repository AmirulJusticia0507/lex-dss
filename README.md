
# Lex Decision Support System (Lex-DSS)

Sistem Pendukung Keputusan Berbasis AI untuk Analisis Harmonisasi, Kontradiksi, dan Rekomendasi Legal Opinion Hukum Indonesia.

---

## 🏛️ Latar Belakang & Konsep Hukum

Sistem ini memadukan modul **Lex Integrity** (pendeteksi kontradiksi internal/eksternal norma hukum) ke dalam platform AI Decision Support System. Penilaian dan rekomendasi keputusan AI didasarkan pada tiga sistem hukum utama di Indonesia:

1. **Hukum Tata Negara & Administrasi:**
   - Evaluasi hierarki perundang-undangan sesuai **Pasal 7 UU No. 12/2011** (*Lex Superior Derogat Legi Inferiori*).
   - Penilaian asas *Lex Specialis Derogat Legi Generali* dan *Lex Posterior Derogat Legi Priori*.
2. **Hukum Pidana:**
   - Evaluasi asas legalitas (**Pasal 1 ayat 1 KUHP / KUHP Baru UU No. 1/2023**).
   - Analisis kontradiksi unsur-unsur tindak pidana dan sanksi (*overlapping penalty*).
3. **Hukum Perdata:**
   - Analisis keabsahan syarat sah perjanjian (**Pasal 1320 KUHPerdata**).
   - Deteksi klausula baku atau pasal perundangan yang bertentangan dengan ketertiban umum/kesusilaan (**Pasal 1337 KUHPerdata**).

---

## 🏗️ Arsitektur Teknologi

- **Frontend:** Vue.js 3 (Options/Composition API, Pinia, TailwindCSS/Element Plus)
- **Backend:** Python (FastAPI / LangChain / LlamaIndex / PyTorch)
- **Vector & relational Store:** PostgreSQL + `pgvector`
- **AI Engine:** Retrieval-Augmented Generation (RAG) + LLM Fine-Tuned / Prompted for Indonesian Law

---

## 📁 Struktur Direktori Project

```text
lex-dss/
├── docs/
│   ├── ARCHITECTURE.md       # Dokumentasi Arsitektur Sistem & Alur AI
│   ├── LEGAL_ONTOLOGY.md     # Taksonomi & Ontologi Hukum Indonesia
│   └── API_SPECIFICATION.md  # Spesifikasi Endpoint API
├── backend/
│   ├── app/
│   │   ├── api/              # Route & Handlers FastAPI
│   │   ├── core/             # Configuration, Security, DB
│   │   ├── engine/           # AI Core, RAG, & Lex Integrity Rules Engine
│   │   ├── models/           # ORM SQLAlchemy & Pydantic Schemas
│   │   └── services/         # Business Logic (Pidana, Perdata, HTN)
│   ├── alembic/              # Database Migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/       # UI Components (Analysis Viewer, Matrix)
│   │   ├── stores/           # Pinia Stores
│   │   ├── views/            # Dashboard, Conflict Checker, DSS Panel
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.js
└── README.md
```
