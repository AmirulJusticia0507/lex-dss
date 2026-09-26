
---
### File 2: `docs/ARCHITECTURE.md`

```markdown
# Dokumentasi Arsitektur Sistem Lex-DSS & AI Integration

Dokumen ini menjelaskan alur kerja pengintegrasian modul **Lex Integrity** ke dalam **Sistem Pengambil Keputusan (DSS) Berbasis AI**.
---
## 1. Alur Pemrosesan Keputusan (Decision Flow)

```text
[Input Dokumen / Draf Hukum]
           │
           ▼
┌─────────────────────────┐
│   Lex Integrity Engine  │  ──> Evaluasi Pertentangan Norma
└──────────┬──────────────┘      (Lex Superior, Specialis, Posterior)
           │
           ▼ (Hasil Konflik & Matriks Kontradiksi)
┌─────────────────────────┐
│   Vector DB + RAG       │  ──> Retrieval Yurisprudensi & Doktrin Hukum
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  AI Legal Decision Engine│ ──> Sintesis Reasoning Pidana/Perdata/HTN
└──────────┬──────────────┘
           │
           ▼
[Output: Legal Opinion & Score Rekomendasi Risk]
2. Modul Pemrosesan Hukum Indonesia
A. Modul Hukum Tata Negara (HTN) & Admin
Fungsi: Menguji derajat/hierarki perundang-undangan.

Logika Sistem: Jika Peraturan_A.hierarki < Peraturan_B.hierarki dan isi norma berbenturan, tandai CONFLICT_LEX_SUPERIOR.

B. Modul Hukum Perdata
Fungsi: Menguji ketaatan syarat obyektif/subyektif perjanjian (Pasal 1320 KUHPerdata).

Logika Sistem: Ekstraksi hak, kewajiban, wanprestasi, dan force majeure. Deteksi potensi frasa exoneration clause yang merugikan.

C. Modul Hukum Pidana
Fungsi: Ekstraksi Anatomie Van Delict (Unsur Obyektif & Subyektif).

Logika Sistem: Memastikan norma larangan memiliki sanksi yang jelas, menguji adanya tumpang tindih (ne bis in idem / pasal berlapis).

3. Skema Data PostgreSQL (pgvector)
SQL
-- Tabel Hirarki Produk Hukum
CREATE TABLE legal_hierarchy (
    id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL, -- UU, PP, PERPRES, PERDA, dll.
    rank INT NOT NULL                -- 1: UUD, 2: TAP MPR, 3: UU/PERPPU, dst.
);

-- Tabel Dokumen / Pasal Hukum
CREATE TABLE legal_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_title VARCHAR(255) NOT NULL,
    article_number VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    domain VARCHAR(50),              -- HTN, PIDANA, PERDATA
    embedding vector(1536),           -- Vector untuk RAG
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Konflik Norma (Output Lex Integrity)
CREATE TABLE norm_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_article_id UUID REFERENCES legal_articles(id),
    target_article_id UUID REFERENCES legal_articles(id),
    conflict_type VARCHAR(50),       -- LEX_SUPERIOR, LEX_SPECIALIS, LEX_POSTERIOR, DIRECT_CONTRADICTION
    severity VARCHAR(20),            -- HIGH, MEDIUM, LOW
    description TEXT
);
4. Rencana Interaksi Komponen Frontend (Vue 3)
Dashboard Conflict Matrix: Visualisasi grafik hubungan inter-pasal menggunakan network graph (D3.js / ECharts).

Legal Opinion Panel: Tampilan split-screen antara draf asli, referensi hukum terkait, dan rekomendasi AI.

Risk Score Card: Penilaian dampak risiko hukum (Skala 1–100) jika draf/kebijakan diterbitkan.


---

<ElicitationsGroup message="Bagaimana Anda ingin melanjutkan pengembangan konsep sistem ini?">
  <Elicitation label="Buat draf API Specification (Endpoints FastAPI)" query="Tolong buatkan draf docs/API_SPECIFICATION.md untuk FastAPI mencakup endpoint analisis kontradiksi dan RAG AI."/>
  <Elicitation label="Buat struktur komponen Vue 3 untuk Conflict Viewer" query="Tolong buatkan draf struktur komponen Vue 3 (Composition API) untuk menampilkan matriks dan grafik kontradiksi norma hukum."/>
  <Elicitation label="Detailkan logika Prompt Engineering untuk AI Hukum" query="Tolong buatkan panduan Prompt Engineering dan guardrails AI agar LLM tidak melakukan ilusi hukum (hallucination) pada pasal Indonesia."/>
```
