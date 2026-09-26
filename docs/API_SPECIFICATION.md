# Spesifikasi Endpoint API — Lex-DSS

Dokumen ini adalah kontrak teknis (technical contract) antara backend FastAPI (`backend/app`) dan frontend Vue 3 (`frontend/src`). Seluruh endpoint mengikuti konvensi yang sudah ditetapkan pada `backend/app/main.py` dan `backend/app/core/config.py`.

---

## 0. Ringkasan Konvensi

| Aspek | Nilai |
| :--- | :--- |
| Base URL Produksi | `https://api.lex-dss.go.id/api/v1` |
| Base URL Development | `http://localhost:8000/api/v1` |
| Prefix | `settings.API_V1_STR` = `/api/v1` |
| Format | `application/json` (kecuali unggah dokumen: `multipart/form-data`) |
| Autentikasi | OAuth2 Password Bearer (JWT HS256), header `Authorization: Bearer <access_token>` |
| Auth URL | `POST /api/v1/auth/login` (form-encoded, sesuai `OAuth2PasswordBearer(tokenUrl=...)` di `app/core/security.py`) |
| Dokumentasi Interaktif | `/docs` (Swagger UI), `/redoc`, `/openapi.json` |
| Health Check | `GET /health` (tanpa prefix, tanpa auth) |
| Zona Waktu | Asia/Jakarta (WIB) untuk seluruh field `*_at` pada response |
| Encoder | UTF-8 |

### 0.1 Struktur Router (Implementasi Referensi)

```text
backend/app/api/v1/
├── router.py                    # include_router api_router
└── endpoints/
    ├── auth.py                   # /auth
    ├── articles.py               # /legal/articles
    ├── analysis.py               # /analysis  (Lex Integrity: kontradiksi & hierarki)
    ├── rag.py                    # /rag      (retrieval + legal opinion)
    ├── deviation.py              # /deviation (DAS: deviation scoring)
    └── audit.py                  # /audit    (decision audit log)
```

### 0.2 Role-Based Access Control (RBAC)

| Role | Hak Akses |
| :--- | :--- |
| `user` | Menjalankan analisis, RAG query, membaca hasil milik sendiri |
| `auditor` | `user` + membaca seluruh audit log dan laporan deviasi |
| `admin` | Akses penuh, termasuk ingest korpus, manajemen artikel, flagging KY |

Endpoint yang diwajibkankan (wajib) ditandai **[AUTH]**; endpoint **[PUBLIC]** tidak memerlukan token.

### 0.3 Format Error (Envelope Seragam)

Seluruh error mengikuti `HTTPValidationError`/custom handler berikut:

```json
{
  "error": {
    "code": "CONFLICT_UNSUPPORTED_DOMAIN",
    "message": "Domain 'EKONOMI' belum memiliki rules engine aktif.",
    "details": {
      "supported_domains": ["HTN", "PIDANA", "PERDATA"]
    },
    "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21",
    "timestamp": "2026-09-26T15:32:10+07:00"
  }
}
```

| HTTP Code | `error.code` | Keterangan |
| :--- | :--- | :--- |
| 400 | `VALIDATION_ERROR` | Input tidak valid secara logika bisnis |
| 401 | `UNAUTHORIZED` | Token hilang / kedaluwarsa / tidak valid |
| 403 | `FORBIDDEN_ROLE` | Role pengguna tidak berhak mengakses endpoint |
| 404 | `NOT_FOUND` | Resource (pasal, analisis, laporan) tidak ditemukan |
| 409 | `CONFLICT` | Duplikasi data (mis. email, dokumen dengan nomor pasal sama) |
| 413 | `PAYLOAD_TOO_LARGE` | Dokumen melebihi batas ukuran unggahan |
| 422 | `VALIDATION_ERROR` | Gagal validasi skema Pydantic |
| 429 | `RATE_LIMIT_EXCEEDED` | Melebihi kuota endpoint (lihat §6) |
| 500 | `INTERNAL_ERROR` | Kesalahan server tak terduga (trace dicatat, bukan dikembalikan) |
| 503 | `AI_ENGINE_UNAVAILABLE` | LLM/embedding atau vector store sedang tidak dapat diakses |

### 0.4 Paginasi

Endpoint `GET` berbasis daftar memakai query parameter:

| Parameter | Tipe | Default | Keterangan |
| :--- | :--- | :--- | :--- |
| `page` | int | `1` | Nomor halaman (1-based) |
| `page_size` | int | `20` | Jumlah item per halaman (maks. 100) |

```json
{
  "items": [ /* ... */ ],
  "pagination": { "page": 1, "page_size": 20, "total": 137, "total_pages": 7 },
  "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21"
}
```

### 0.5 Pola Proses Asinkron (Long-Running Job)

Analisis dokumen utuh (RUU/Raperda/putusan) dapat melampaui batas waktu request. Endpoint tersebut mengembalikan **HTTP 202 Accepted** dengan `job_id`, dan klien melakukan polling ke `GET /jobs/{job_id}`.

```json
{
  "job_id": "b7a0f3c2-9b41-4f0e-8b6a-1c2d3e4f5a6b",
  "status": "PENDING",
  "status_url": "/api/v1/jobs/b7a0f3c2-9b41-4f0e-8b6a-1c2d3e4f5a6b",
  "estimated_seconds": 45,
  "created_at": "2026-09-26T15:32:10+07:00"
}
```

Nilai `status`: `PENDING` → `PROCESSING` → `COMPLETED` | `FAILED`.

---

## 1. Health & Metadata

### 1.1 `GET /` **[PUBLIC]**

```json
{ "name": "Lex-DSS", "version": "0.1.0", "status": "running" }
```

### 1.2 `GET /health` **[PUBLIC]**

```json
{ "status": "healthy" }
```

### 1.3 `GET /api/v1/system/status` **[AUTH]**

Status komponen engine (LLM, embedding, vector store, database) untuk keperluan dashboard operasional.

```json
{
  "database": "UP",
  "vector_store": "UP",
  "embedding_model": "text-embedding-3-small",
  "llm_model": "gpt-4-turbo-preview",
  "corpus_articles": 12840,
  "api_version": "0.1.0",
  "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21"
}
```

---

## 2. Authentication & User

### 2.1 `POST /api/v1/auth/register`

Request Body:

```json
{
  "email": "hakim@pn-jakarta.go.id",
  "password": "RahasiaKuat123!",
  "full_name": "Rina Kartika, S.H.",
  "institution": "Pengadilan Negeri Jakarta Pusat",
  "role": "user"
}
```

| Field | Tipe | Wajib | Validasi |
| :--- | :--- | :--- | :--- |
| `email` | `EmailStr` | Ya | Unik pada tabel `users` |
| `password` | str | Ya | Min. 8 karakter, mengandung huruf & angka |
| `full_name` | str | Tidak | Maks. 255 |
| `institution` | str | Tidak | Maks. 255 |
| `role` | enum | Tidak | Default `user`; `admin` hanya dapat dibuat lewat seed/bootstrap |

Response `201`:

```json
{
  "id": "9c1f2a30-6b6d-4a2e-9f31-7b8c9d0e1f20",
  "email": "hakim@pn-jakarta.go.id",
  "full_name": "Rina Kartika, S.H.",
  "role": "user",
  "institution": "Pengadilan Negeri Jakarta Pusat",
  "is_active": true,
  "created_at": "2026-09-26T15:30:00+07:00"
}
```

Error: `409 CONFLICT` bila email sudah terdaftar.

### 2.2 `POST /api/v1/auth/login`

Request Body (`application/x-www-form-urlencoded`):

```
username=hakim@pn-jakarta.go.id&password=RahasiaKuat123!
```

Response `200`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": "9c1f2a30-6b6d-4a2e-9f31-7b8c9d0e1f20",
    "email": "hakim@pn-jakarta.go.id",
    "role": "user"
  }
}
```

Implementasi: `create_access_token(data={"sub": str(user.id)}, ...)` + pembaruan `users.last_login`.

### 2.3 `GET /api/v1/auth/me` **[AUTH]**

```json
{
  "id": "9c1f2a30-6b6d-4a2e-9f31-7b8c9d0e1f20",
  "email": "hakim@pn-jakarta.go.id",
  "full_name": "Rina Kartika, S.H.",
  "role": "auditor",
  "institution": "Komisi Yudisial RI",
  "is_active": true,
  "last_login": "2026-09-26T08:12:44+07:00"
}
```

---

## 3. Korpus Hukum (Legal Articles)

### 3.1 `POST /api/v1/legal/articles` **[AUTH] — admin**

Menyimpan satu pasal ke `legal_articles` dan mengindeksnya ke `pgvector` (embedding `text-embedding-3-small`, dimensi 1536).

Request Body:

```json
{
  "document_title": "Undang-Undang Nomor 12 Tahun 2011 tentang Pembentukan Peraturan Perundang-undangan",
  "article_number": "7",
  "content": "Peraturan perundang-undangan yang lebih rendah tidak boleh bertentangan dengan peraturan perundang-undangan yang lebih tinggi.",
  "domain": "HTN",
  "hierarchy_id": 2,
  "meta_data": { "source_url": "https://peraturan.bpk.go.id/...", "status": "BERLAKU" }
}
```

Field khusus: `domain` ∈ `HTN` | `PIDANA` | `PERDATA` (lihat `app/models/legal.py`).

Response `201`: objek artikel lengkap beserta `id` (UUID) dan `created_at`.

### 3.2 `POST /api/v1/legal/articles/bulk` **[AUTH] — admin**

Ingest korpus massal (hasil ETLUU). Maksimal 500 pasal per request.

```json
{
  "articles": [
    {
      "document_title": "UU No. 1 Tahun 2023 (KUHP)",
      "article_number": "1",
      "content": "Tiada suatu tindak pidana yang tidak dipidana kecuali setiap tindak pidana yang ditegaskan dalam undang-undang.",
      "domain": "PIDANA"
    }
  ],
  "skip_duplicates": true
}
```

Response `202` dengan `job_id` (proses embedding berjalan di background). Laporan duplikat dikembalikan pada `GET /jobs/{job_id} → result`.

### 3.3 `GET /api/v1/legal/articles` **[AUTH]**

Query: `domain`, `hierarchy_id`, `document_title` (pencarian parsial), `page`, `page_size`.

### 3.4 `GET /api/v1/legal/articles/{article_id}` **[AUTH]**

Mengembalikan detail pasal, relasi `hierarchy`, dan ringkasan konflik yang melekat (`source_conflicts` / `target_conflicts`).

### 3.5 `GET /api/v1/legal/hierarchy` **[AUTH]**

Daftar jenjang norma beserta `rank` (1 = UUD, 2 = TAP MPR, 3 = UU/Perppu, dst.) untuk dropdown filter dan visualisasi matriks.

```json
{
  "items": [
    { "id": 1, "type_name": "UUD_NRI_1945", "rank": 1, "description": "Undang-Undang Dasar Negara Republik Indonesia Tahun 1945" },
    { "id": 3, "type_name": "UU", "rank": 3, "description": "Undang-Undang" }
  ]
}
```

---

## 4. Analisis Kontradiksi & Lex Integrity (Endpoint Inti)

### 4.1 `POST /api/v1/analysis/conflict` **[AUTH]**

Menguji sebuah klausa terhadap basis data norma untuk mendeteksi kontradiksi. Pipeline: ekstraksi pasal → retrieval kandidat via embedding → Rules Engine Lex Integrity → filter severity.

Request Body:

```json
{
  "input_text": "Gubernur dapat membatalkan peraturan kepala daerah kabupaten dan kota atas rekomendasi komite.",
  "input_article_id": null,
  "domain": "HTN",
  "target_article_ids": ["8f2b0c1d-2e3f-4a5b-8c9d-0e1f2a3b4c5d", "1a9c8b7a-6d5e-4f3a-2b1c-0d9e8f7a6b5c"],
  "hierarchy_context": { "draft_type": "PERDA", "draft_number": "Perda DKI Jakarta No. 2/2025" },
  "min_severity": "MEDIUM",
  "save_result": true
}
```

| Field | Tipe | Wajib | Keterangan |
| :--- | :--- | :--- | :--- |
| `input_text` | str | Ya | klausa yang diuji (maks. 20.000 karakter) |
| `input_article_id` | UUID | Tidak | Jika dianalisis dari pasal yang sudah tersimpan |
| `domain` | enum | Ya | `HTN` \| `PIDANA` \| `PERDATA` |
| `target_article_ids` | list[UUID] | Tidak | Batasi kandidat perbandingan; kosong = seluruh korpus |
| `hierarchy_context` | object | Tidak | Untuk uji *Lex Superior* jika klausa berasal dari draf Perda/Perpres |
| `min_severity` | enum | Tidak | `LOW` (default) \| `MEDIUM` \| `HIGH` |
| `save_result` | bool | Tidak | Simpan ke `norm_conflicts` (default `true`) |

Response `200`:

```json
{
  "analysis_id": "5d1e7a90-2b3c-4d5e-9f60-7a8b9c0d1e2f",
  "domain": "HTN",
  "has_conflict": true,
  "conflict_count": 2,
  "highest_severity": "HIGH",
  "conflicts": [
    {
      "id": "0c1d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
      "conflict_type": "LEX_SUPERIOR",
      "severity": "HIGH",
      "description": "Klausula memberikan kewenangan membatalkan Perda kepada gubernur, padahal kewenangan tersebut melekat pada Mendagri.",
      "source_article": {
        "id": "8f2b0c1d-2e3f-4a5b-8c9d-0e1f2a3b4c5d",
        "document_title": "Perda DKI Jakarta No. 2 Tahun 2025",
        "article_number": "12",
        "hierarchy": { "type_name": "PERDA", "rank": 6 }
      },
      "target_article": {
        "id": "1a9c8b7a-6d5e-4f3a-2b1c-0d9e8f7a6b5c",
        "document_title": "UU No. 12 Tahun 2011",
        "article_number": "7",
        "hierarchy": { "type_name": "UU", "rank": 3 }
      },
      "legal_basis": ["Pasal 7 ayat (1) UU No. 12 Tahun 2011"],
      "recommended_action": "Hapus delegasi pembatalan Perda; fungsi pembatalan berada pada Mendagri/gubernur sesuai Pasal 251 UU 23/2014."
    }
  ],
  "unrelated_articles": ["c4d5e6f7-..."],
  "engine_trace": {
    "retrieval_top_k": 20,
    "embedding_model": "text-embedding-3-small",
    "rules_applied": ["RANK_COMPARISON", "DIRECT_CONTRADICTION_DETECTION", "EXPLICIT_REPEAL_CHECK"],
    "latency_ms": 1840
  },
  "created_at": "2026-09-26T15:32:10+07:00",
  "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21"
}
```

Klasifikasi `conflict_type` (sesuai `docs/ARCHITECTURE.md` dan kolom `norm_conflicts.conflict_type`):

| Kode | Makna | Dasar Hukum |
| :--- | :--- | :--- |
| `LEX_SUPERIOR` | Norma yang lebih rendah bertentangan dengan norma yang lebih tinggi | Pasal 7 UU 12/2011 |
| `LEX_SPECIALIS` | Norma umum vs. norma khusus | Pasal 1 ayat (1) UU 12/2011 |
| `LEX_POSTERIOR` | Norma baru vs. norma lama | Pasal 7 ayat (2) UU 12/2011 |
| `DIRECT_CONTRADICTION` | Bunyi pasal saling meniadakan | Analisis semantik |
| `ANATOMIE_DELICT_OVERLAP` | Unsur pidana/sanksi tumpang tindih | Asas legalitas, KUHP |
| `KLAUSULA_BAKU_TIDAK_SAH` | Klausula bertentangan ketertiban umum/kesusilaan | Pasal 1337 KUHPerdata |
| `SYARAT_PERJANJIAN_TIDAK_TERPENUHI` | Syarat sah perjanjian tidak terpenuhi | Pasal 1320 KUHPerdata |

Tingkat `severity`: `HIGH` (menabrak norma fundamental) \| `MEDIUM` (memerlukan revisi) \| `LOW` (perlu dicermati).

### 4.2 `POST /api/v1/analysis/conflict/document` **[AUTH]**

Analisis dokumen draf utuh (RUU/Raperda/Perpres) secara asinkron.

Request Body (`multipart/form-data`):

| Field | Tipe | Wajib |
| :--- | :--- | :--- |
| `file` | file | Ya (`.pdf`, `.docx`, `.txt`, maks. 25 MB) |
| `domain` | form | Ya |
| `document_label` | form | Tidak (jika kosong, nama file digunakan) |

Response `202`: objek **Job** (§0.5). `result` pada job yang selesai berisi array hasil `conflict` untuk setiap klausa/pasal yang dianalisis.

### 4.3 `POST /api/v1/analysis/hierarchy` **[AUTH]**

Menguji secara eksplisit hierarki satu norma terhadap norma lain — dipakai untuk validasi Perda/Perpres terhadap UU di atasnya.

Request Body:

```json
{
  "lower_norm": { "type": "PERDA", "document_title": "Perda Kota Bandung No. 3 Tahun 2024", "article_number": "24" },
  "upper_norm": { "type": "UU", "document_title": "UU No. 23 Tahun 2014", "article_number": "251" }
}
```

Response `200`:

```json
{
  "valid": false,
  "hierarchy_relation": "CONTRADICTS_SUPERIOR",
  "rank_lower": 6,
  "rank_upper": 4,
  "violations": [
    {
      "code": "LEX_SUPERIOR",
      "severity": "HIGH",
      "explanation": "Perda mengatur bahwa gubernur dapat membatalkan Perkada, padahal kewenangan ini milik Mendagri.",
      "legal_basis": ["Pasal 7 UU No. 12 Tahun 2011", "Pasal 251 UU No. 23 Tahun 2014"]
    }
  ],
  "recommendation": "Cabut Pasal 24 Perda tersebut atau ubah menjadi delegasi.",
  "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21"
}
```

### 4.4 `GET /api/v1/analysis/conflicts` **[AUTH]**

Riwayat konflik yang tersimpan pada tabel `norm_conflicts`.

Query: `conflict_type`, `severity`, `source_article_id`, `target_article_id`, `min_severity`, `page`, `page_size`, `sort` (`created_at:desc` default).

### 4.5 `GET /api/v1/analysis/conflicts/{conflict_id}` **[AUTH]**

Detail satu konflik beserta metadata kedua pasal sumber dan target.

### 4.6 `GET /api/v1/analysis/articles/{article_id}/conflicts` **[AUTH]**

Graf relasi untuk satu pasal (feed `Conflict Matrix` di frontend): daftar konflik keluar, masuk, dan ringkasan (`summary`: `{ "incoming": 4, "outgoing": 1, "highest_severity": "HIGH" }`).

### 4.7 `POST /api/v1/analysis/conflicts/{conflict_id}/resolve` **[AUTH]**

Menandai konflik sebagai ditinjau/diatasi beserta catatan tindakan korektif.

```json
{
  "status": "RESOLVED",
  "resolution_note": "Pasal 24 dicabut; kewenangan pembatalan dikembalikan kepada Mendagri.",
  "resolved_article_id": "e5f6a7b8-..."
}
```

`status` ∈ `OPEN` \| `REVIEWED` \| `RESOLVED` \| `DISMISSED` (dismissed wajib menyertakan `resolution_note`).

---

## 5. RAG & Legal Opinion

### 5.1 `POST /api/v1/rag/query` **[AUTH]**

Retrieval-Augmented Generation dengan jaminan kutipan (anti-*hallucination*). Setiap kalimat output harus terpetakan pada `citations`.

Request Body:

```json
{
  "query": "Apakah pemutusan hubungan kerja secara sepihak tetap sah menurut Pasal 1320 KUHPerdata?",
  "domain": "PERDATA",
  "top_k": 8,
  "similarity_threshold": 0.72,
  "include_jurisprudence": true,
  "stream": false
}
```

| Field | Tipe | Default | Keterangan |
| :--- | :--- | :--- | :--- |
| `query` | str | — | Pertanyaan hukum berbahasa Indonesia |
| `domain` | enum | `null` | Filter corpus: `HTN`/`PIDANA`/`PERDATA` |
| `top_k` | int | `8` | Maks. 20 |
| `similarity_threshold` | float | `0.72` | Ambang cosine similarity |
| `include_jurisprudence` | bool | `true` | Sertakan hasil dari korpus putusan MA/MK |
| `stream` | bool | `false` | `true` → SSE (`text/event-stream`) dengan token `data:` |

Response `200`:

```json
{
  "answer": "Berdasarkan Pasal 1320 KUHPerdata, perjanjian yang dibuat tidak sah apabila tidak memenuhi empat syarat subjektif dan tiga syarat objektif...",
  "confidence": 0.84,
  "citations": [
    {
      "article_id": "1a9c8b7a-6d5e-4f3a-2b1c-0d9e8f7a6b5c",
      "document_title": "Kitab Undang-Undang Hukum Perdata",
      "article_number": "1320",
      "content": "Perjanjian yang dibuat dengan tidak memenuhi syarat-syarat dalam ketentuan Pasal 1320...",
      "similarity": 0.91,
      "domain": "PERDATA",
      "quote_span": { "start": 42, "end": 118 }
    },
    {
      "case_id": "MA-1491-PK-PID-2023",
      "court_name": "Mahkamah Agung",
      "verdict_number": "1491 K/Pid/2023",
      "ratio_decidendi": "Perjanjian kerja yang tidak memuat klausul jangka waktu tidak sah...",
      "similarity": 0.78,
      "source_type": "JURISPRUDENCE"
    }
  ],
  "grounded": true,
  "ungrounded_segments": [],
  "engine": {
    "llm_model": "gpt-4-turbo-preview",
    "embedding_model": "text-embedding-3-small",
    "rerank_applied": true,
    "prompt_version": "legal-opinion-v1.3",
    "tokens_used": 1840
  },
  "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21"
}
```

>`grounded: false` berarti ada segmen jawaban tanpa dukungan retrieval; UI wajib menandai bagian tersebut sebagai **belum terverifikasi** (lihat `docs/TRANSPARENCY_AUDIT.md`).

### 5.2 `POST /api/v1/rag/opinion` **[AUTH]**

Menghasilkan **Legal Opinion** lengkap untuk satu kasus/draf, mencakup: ringkasan fakta, dasar hukum, analisis kontradiksi, dan rekomendasi.

Request Body:

```json
{
  "case_context": {
    "case_title": "Sengketa Perjanjian Kerja PKWT",
    "facts": "Pekerja dengan PKWT tetap berstatus PKWT meski sudah 2 tahun bekerja.",
    "legal_issue": "Apakah klasifikasi status hubungan kerja dapat diubah sepihak oleh pemberi kerja?",
    "domain": "PIDANA",
    "draft_text": null,
    "reference_conflict_ids": ["0c1d2e3f-4a5b-6c7d-8e9f-0a1b2c3d4e5f"]
  },
  "options": { "include_precedent": true, "max_citations": 15, "language": "id" }
}
```

Response `200`:

```json
{
  "opinion_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "case_title": "Sengketa Perjanjian Kerja PKWT",
  "executive_summary": "...",
  "legal_basis": [
    { "article_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c", "document_title": "UU No. 13 Tahun 2003 tentang Ketenagakerjaan", "article_number": "1 ayat (1) huruf (a)" }
  ],
  "conflict_summary": { "total": 1, "highest_severity": "HIGH" },
  "recommendation": { "text": "...", "risk_score": 72, "risk_level": "RED" },
  "citations": [],
  "disclaimer": "Rekomendasi AI merupakan sistem pendukung keputusan dan tidak memiliki kekuatan hukum mengikat. Keputusan akhir tetap menjadi wewenang manusia.",
  "created_at": "2026-09-26T15:40:00+07:00"
}
```

### 5.3 `POST /api/v1/rag/ingest` **[AUTH] — admin**

Menjalankan pipeline re-index korpus (embedding + chunking) secara asinkron.

```json
{
  "source": "PUTUSAN_MA",         // UU | PUTUSAN_MA | PUTUSAN_MK | YURISPRUDENSI_LAIN | DOKUMEN_INTERNAL
  "domain": "PIDANA",
  "file_url": "https://putusan3.mahkamahagung.go.id/direktori/...",
  "chunk_size": 800,
  "chunk_overlap": 120,
  "force_reindex": false
}
```

Response `202` (Job).

### 5.4 `GET /api/v1/rag/jobs/{job_id}` **[AUTH]**

Status proses re-index beserta statistik: `documents_processed`, `chunks_created`, `chunks_failed`, `duration_seconds`.

### 5.5 `GET /api/v1/rag/similarity` **[AUTH]**

Matriks kemiripan antar pasal (heatmap/ECharts pada Conflict Matrix).

Query: `article_ids` (wajib, 2–20 UUID, dipisah koma), `metric` (`cosine` | `euclidean`).

```json
{
  "article_ids": ["8f2b0c1d-...", "1a9c8b7a-...", "c4d5e6f7-..."],
  "matrix": [[1.0, 0.91, 0.34], [0.91, 1.0, 0.12], [0.34, 0.12, 1.0]],
  "threshold": 0.72,
  "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21"
}
```

### 5.6 `DELETE /api/v1/rag/citations/{citation_id}` **[AUTH] — admin**

Meniadakan/mengoreksi rujukan yang keliru. `204 No Content`, atau `409 CONFLICT` bila sudah dipakai oleh audit log yang telah diverifikasi.

---

## 6. Deviation Scoring (DAS)

Mengikuti formula dan ambang batas pada `docs/DEVIATION_ALERT_SYSTEM.md`:

$$
Score_{Deviasi} = 0{,}35\,I_{Hierarchy} + 0{,}25\,I_{Precedent} + 0{,}25\,I_{Evidence} + 0{,}15\,I_{Procedural}
$$

Ambang: `0–29` GREEN, `30–59` YELLOW, `≥60` RED (flag otomatis ke KY).

### 6.1 `POST /api/v1/deviation/score` **[AUTH]**

Request Body:

```json
{
  "verdict_number": "1491 K/Pid/2023",
  "court_name": "Mahkamah Agung",
  "judge_panel": ["H. Rahmat, S.H. (Ketua)", "Dr. S. Wulandari, S.H., M.H."],
  "ratio_decidendi_text": "Berdasarkan alat bukti yang tersimpan, putusan menyatakan semua unsur tindak pidana telah terbukti secara sahih.",
  "verdict_amar_text": "Menguatkan putusan tingkat pertama dan menjatuhkan penjara lima tahun.",
  "referenced_articles": ["UU 1/2023 Pasal 1", "KUHP Pasal 53"],
  "domain": "PIDANA",
  "save_report": true
}
```

Response `201`:

```json
{
  "report_id": "c7d8e9f0-1a2b-3c4d-5e6f-7a8b-9c0d1e2f3a4b",
  "verdict_number": "1491 K/Pid/2023",
  "court_name": "Mahkamah Agung",
  "total_deviation_score": 64.35,
  "risk_level": "RED",
  "flagged_for_ky": true,
  "indicators": {
    "hierarchy_violation_score": 72.0,
    "precedent_anomaly_score": 65.0,
    "evidence_gap_score": 58.0,
    "procedural_flaw_score": 40.0
  },
  "weights": { "hierarchy": 0.35, "precedent": 0.25, "evidence": 0.25, "procedural": 0.15 },
  "anomalies": [
    {
      "indicator": "I_Hierarchy",
      "code": "NORM_NOT_ENFORCED",
      "severity": "HIGH",
      "finding": "Pertimbangan hukum tidak menguji keabsahan norma terkait Pasal 1 UU 1/2023.",
      "evidence": "Pertimbangan hukum tidak menyinggung Pasal 1 ayat (1) tersebut secara eksplisit.",
      "legal_basis": ["Pasal 1 ayat (1) UU No. 1 Tahun 2023"],
      "recommendation": "Verifikasi kembali kepatuhan pada asas legalitas."
    }
  ],
  "anomaly_summary": "Teridentifikasi 3 anomali: 1 pelanggaran hierarki norma, 1 penyimpangan jurisprudensi, 1 kesenjangan pembuktian.",
  "recommended_action": "Kirim ke tim verifikasi KY dalam 7 hari kerja.",
  "created_at": "2026-09-26T16:02:41+07:00",
  "request_id": "3f6c1b9e-7c1a-4a1a-9b2f-0b8f7c1d4e21"
}
```

### 6.2 `POST /api/v1/deviation/score/document` **[AUTH]**

Menilai berkas putusan lengkap (PDF/DOCX) secara asinkron. Field multipart: `file`, `court_name`, `domain`, `verdict_number` (opsional). Response `202` (Job); parsing memisahkan Duduk Perkara, Pertimbangan Hukum, dan Amar Putusan.

### 6.3 `GET /api/v1/deviation/reports` **[AUTH]** — `auditor`, `admin`

Query: `risk_level` (`GREEN`/`YELLOW`/`RED`), `court_name`, `flagged_for_ky` (bool), `min_score`, `max_score`, `date_from`, `date_to`, `page`, `page_size`.

### 6.4 `GET /api/v1/deviation/reports/{report_id}` **[AUTH]**

Detail satu laporan lengkap dengan daftar anomali per indikator.

### 6.5 `POST /api/v1/deviation/reports/{report_id}/ky-flag` **[AUTH]** — `auditor`, `admin`

Konfirmasi penerusan laporan ke tiket KY.

```json
{
  "action": "SUBMIT",          // SUBMIT | DISMISS | ESCALATE
  "notes": "Diteruskan ke Divisi Pengawasan Internal KY",
  "escalate_to": "KY-2026-09-0001"
}
```

`action: DISMISS` wajib menyertakan `notes` (alasan penolakan anomali).

### 6.6 `GET /api/v1/deviation/reports/{report_id}/export` **[AUTH]**

`format` ∈ `json` | `pdf` | `csv`. Default `json`. Menghasilkan matriks perbandingan yang dapat diverifikasi publik.

### 6.7 `GET /api/v1/deviation/statistics` **[AUTH]**

Agregat untuk dashboard KY/Bawas.

```json
{
  "period": { "from": "2026-01-01", "to": "2026-09-26" },
  "total_reports": 1482,
  "by_risk_level": { "GREEN": 1190, "YELLOW": 246, "RED": 46 },
  "flagged_for_ky": 46,
  "top_anomaly_codes": [
    { "code": "NORM_NOT_ENFORCED", "count": 118 },
    { "code": "PRECEDENT_INCONSISTENCY", "count": 97 }
  ],
  "by_court": [
    { "court_name": "PN Jakarta Pusat", "red": 7, "yellow": 22, "green": 134 }
  ]
}
```

---

## 7. Audit & Decision Lineage

### 7.1 `POST /api/v1/audit/decision` **[AUTH]**

Mencatat keputusan manusia terhadap rekomendasi AI (tabel `decision_audit_logs`, append-only).

Request Body:

```json
{
  "case_title": "Penetapan tarif iuran parkir",
  "ai_recommendation": "Menetapkan tarif baru yang bertentangan dengan Perda sebelumnya.",
  "ai_risk_score": 78,
  "human_decision": "Tarif ditetapkan penuh sesuai draf yang diajukan.",
  "is_deviated": true,
  "deviation_justification": "Ada dasar hukum khusus dari Perpres No. 66 Tahun 2023 yang belum ada dalam korpus sistem.",
  "meta_data": { "opinion_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d" }
}
```

Response `201` (menampilkan `deviation_risk_score` jika `is_deviated = true`).

### 7.2 `GET /api/v1/audit/decisions` **[AUTH]** — `auditor`, `admin`

Query: `case_title`, `is_deviated`, `user_id`, `date_from`, `date_to`, `page`, `page_size`, `sort`.

### 7.3 `GET /api/v1/audit/export` **[AUTH]** — `admin`

`format` ∈ `json` | `csv` | `pdf`. Header `X-Export-Token` (one-time token dari `GET /api/v1/audit/export-token`) wajib untuk ekspor massal (> 1.000 baris) guna mencegah penyalahgunaan data.

### 7.4 `GET /api/v1/audit/lineage/{opinion_id}` **[AUTH]**

Rekonstruksi *decision lineage*: opinion → analisis kontradiksi yang dipakai → kutipan RAG → skor deviasi → keputusan manusia.

```json
{
  "opinion_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "chain": [
    { "step": 1, "actor": "system", "action": "RAG_RETRIEVAL", "ref": "rag_query_9b8a" },
    { "step": 2, "actor": "system", "action": "CONFLICT_ANALYSIS", "ref": "5d1e7a90-..." },
    { "step": 3, "actor": "system", "action": "DEVIATION_SCORE", "ref": "c7d8e9f0-..." },
    { "step": 4, "actor": "9c1f2a30-...", "action": "HUMAN_DECISION", "ref": "audit_..." }
  ],
  "hash": "sha256:9f2b...c1",
  "generated_at": "2026-09-26T16:10:00+07:00"
}
```

---

## 8. Job Asinkron

### 8.1 `GET /api/v1/jobs/{job_id}` **[AUTH]**

```json
{
  "job_id": "b7a0f3c2-9b41-4f0e-8b6a-1c2d3e4f5a6b",
  "type": "CONFLICT_ANALYSIS_DOCUMENT",
  "status": "PROCESSING",
  "progress": 65,
  "stage": "MENGHITUNG_SKOR_DEViasi",
  "result": null,
  "error": null,
  "created_at": "2026-09-26T15:32:10+07:00",
  "estimated_completion_at": "2026-09-26T15:33:10+07:00"
}
```

Jenis `type`: `CONFLICT_ANALYSIS_DOCUMENT` | `BULK_ARTICLE_INGEST` | `RAG_REINDEX` | `DEVIATION_SCORE_DOCUMENT`.

---

## 9. Kuota & Batas (Rate Limit)

| Endpoint | Kuota |
| :--- | :--- |
| `/auth/login` | 5 permintaan/menit per IP |
| `/analysis/conflict` | 60 permintaan/menit per pengguna |
| `/analysis/*`, `/deviation/*` (berat) | 20 permintaan/menit |
| `/rag/query` | 30 permintaan/menit |
| Endpoint lain | 120 permintaan/menit |

Header respons: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` (saat 429).

Batas ukuran: unggahan dokumen 25 MB; `input_text` 20.000 karakter; `top_k` 20; `page_size` 100.

---

## 10. Catatan Implementasi

1. **Prefix & routers:** seluruh router di-`include` pada `api_router` dengan prefix `settings.API_V1_STR` (lihat `app/main.py`).
2. **Dependency auth:** gunakan `get_current_active_user` dari `app/core/security.py`; untuk endpoint spesifik role tambahkan `require_role(["admin"])` berbasis `users.role`.
3. **Session DB:** gunakan `Depends(get_db)`; handler tidak melakukan `commit` manual karena `get_db` sudah melakukan commit/rollback otomatis.
4. **Idempotensi:** endpoint yang memicu job menerima header `Idempotency-Key`; kunci yang sama mengembalikan `job_id` sebelumnya (maks. 24 jam).
5. **Field waktu:** seluruh kolom waktu pada model memakai `datetime.utcnow`; response API dikonversi ke UTC dengan offset `+07:00` agar konsisten dengan zona waktu operasional.
6. **Nilai enum** yang dipakai API (`conflict_type`, `severity`, `risk_level`, `domain`, `status`) harus sama persis dengan nilai yang disimpan di `app/models/legal.py` dan `app/models/audit.py`.
7. **`request_id` wajib ada** pada setiap response API agar output AI dapat ditelusuri pada `docs/TRANSPARENCY_AUDIT.md` (append-only audit trail).
