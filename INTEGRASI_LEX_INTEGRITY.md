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

1. **Selesai:** Embedding tetap terpisah (Lex-DSS 1536, Lex Integrity 768) karena kedua database tidak mencampur vector.
2. **Selesai:** Endpoint `/api/v1/integration/sync` mengimpor aturan Lex Integrity ke `legal_articles` secara idempoten.
3. **Selesai:** Endpoint `/api/v1/integration/delegate` memakai `MultiHopAgent` Lex Integrity sebagai reasoning engine.
4. **Selesai:** Lex Integrity memanggil analisis konflik Lex-DSS melalui `/api/integration/dss/conflict`.

## Status Produksi

- Kedua backend berada dalam satu Railway project dan berkomunikasi melalui private network.
- Endpoint internal dilindungi shared `INTERNAL_API_KEY`.
- Sinkronisasi awal memuat 44.570 aturan aktif dari Lex Integrity.
- Multi-Hop menggunakan Gemini ketika Ollama tidak tersedia dan tetap memakai full-text retrieval ketika embedding offline.
