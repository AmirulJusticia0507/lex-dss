# Analisis Integrasi lex-dss + lex-integrity

## Perbandingan Arsitektur

| Aspek | lex-dss (Python/FastAPI) | lex-integrity (Node.js/Express) |
|-------|--------------------------|--------------------------------|
| **DB** | PostgreSQL + pgvector | PostgreSQL + pgvector |
| **Embedding** | 1536-dim (OpenAI) | 768-dim (Ollama nomic) |
| **Tabel Utama** | `legal_articles`, `norm_conflicts` | `rules`, `rule_chunks` |
| **Fokus** | Conflict detection, deviation audit | RAG, multi-hop reasoning, scraping |
| **KUHAP** | Tidak ada | Hanya di `guardrails.js` (referensi legal boundary) |

## Peluang Integrasi

### 1. Database Schema Alignment
Kedua proyek sama-sama pakai pgvector, tapi dimensi embedding berbeda. Perlu standardisasi.

### 2. Seed KUHAP ke lex-dss
`lex-integrity` punya infrastruktur scraping & AI analysis (RAG pipeline, multi-hop agent) yang bisa dijadikan sumber data KUHAP untuk `legal_articles` di lex-dss.

### 3. API Delegation
lex-dss bisa panggil `/api/chat` atau `/api/rules/:code/conflicts` di lex-integrity untuk analisis loophole & conflict.

### 4. Embedding Dimension Conflict
1536 vs 768. Solusi: pilih satu provider (misal OpenAI 1536 atau Ollama 768) untuk keduanya.

## Rekomendasi Prioritas

1. **Prioritas 1:** Standardisasi embedding dimension (pilih 1536 atau 768)
2. **Prioritas 2:** Buat endpoint di lex-dss untuk ingest data dari lex-integrity (KUHAP, KUHP, KUHPer, dll)
3. **Prioritas 3:** Gunakan `MultiHopAgent` lex-integrity sebagai legal reasoning engine untuk lex-dss