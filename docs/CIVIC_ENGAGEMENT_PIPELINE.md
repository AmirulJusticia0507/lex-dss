
# 📜 Architecture Scenario: Civic Engagement Pipeline

Skenario ini merancang *pipeline* otomatisasi yang mengubah rekaman rapat/siaran YouTube DPRD/Pemda yang panjang dan kaku menjadi poin isu ringkas yang dapat di-vote oleh masyarakat sipil secara  *real-time* .

## 🔄 Sequence Workflow Diagram

**Plaintext**

```
[ Video / Live Stream YouTube DPRD / Pemda ]
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 1. STT ENGINE (Ingestion & Speech)  │
  │    • Download audio Stream / Video  │
  │    • Transkripsi Audio to Text      │
  └──────────────────┬──────────────────┘
                     │ (Raw Transcript)
                     ▼
  ┌─────────────────────────────────────┐
  │ 2. LEX INTEGRITY (Legal Auditor)    │
  │    • Extract Key Issues & Pasal     │
  │    • Matchmaking vs 24k Postgres DB │
  │    • Detect Loophole / Contradiction│
  └──────────────────┬──────────────────┘
                     │ (Audited Legal Risks & Context)
                     ▼
  ┌─────────────────────────────────────┐
  │ 3. LEX DSS (Decision Support System)│
  │    • Calculate Policy Options       │
  │    • Trade-off Analysis             │
  │    • Generate Micro-Poll Questions  │
  └──────────────────┬──────────────────┘
                     │ (Simplified Poll Payload)
                     ▼
  ┌─────────────────────────────────────┐
  │ 4. E-NETIZEN VOTING (Public Action) │
  │    • Authentication (Face ID / NIK) │
  │    • Citizen Voting & Feedback      │
  │    • Aggregate Real-Time Analytics  │
  └─────────────────────────────────────┘
```

## 🛠️ Step-by-Step Scenario Specification

 **1.1. Ingestion & Transkripsi Audio (STT Engine):** **Mengubah siaran YouTube DPRD/Pemda menjadi teks transkrip.**Sistem menarik *stream* audio dari URL YouTube kanal resmi Pemda/DPRD secara otomatis saat rapat paripurna/pembahasan Raperda berlangsung.

* **Process:** Audio di-chunk per 30-60 detik dan dikirim ke  **STT Engine** .
* **Output:** Teks transkrip pembicaraan rapat secara *real-time* lengkap dengan  *timestamp* .

 **2.2. Ekstraksi Isu & Audit Hukum (Lex Integrity):** **Membedah teks transkrip ke dalam konteks 24.000 data regulasi.**Transkrip mentah dianalisis oleh **`lex-integrity-agent`** berbasis RAG PostgreSQL (`pgvector`).

* **Process:**

  1. Identifikasi topik pembahasan (misal: Retribusi Pasar, Izin Bangunan, Kebijakan Lahan).
  2. Pencocokan ke basis data UU Pusat/Kovenan PBB di PostgreSQL.
  3. Mendeteksi potensi pasal karet, celah diskresi, atau dampak buruk bagi masyarakat rentan.
* **Output:** JSON Risiko Hukum berisi ringkasan isu, pasal terkait, dan  *Humanitarian Impact Rating* .

 **3.3. Pemodelan Opsi Kebijakan (Lex DSS):** **Mengubah analisis kaku menjadi pilihan kebijakan & pertanyaan polling.**Decision Support System mengolah hasil audit dari Lex Integrity menjadi skenario kebijakan yang objektif dan mudah dipahami warga awam.

* **Process:**

  1. Menghitung pembobotan *trade-off* (Manfaat vs. Mudharat).
  2. Menyusun 2–3 Opsi Kebijakan Alternatif.
  3. Menyusun 1 pertanyaan polling mikro dengan bahasa sehari-hari.
* **Output:** Payload Polling Publik untuk e-Netizen Voting.

 **4.4. Uji Publik & E-Voting Warga (e-Netizen Voting):** **Menjaring aspirasi publik secara valid dan transparan.**Polling dipublikasikan ke *dashboard* warga atau bot notifikasi (WhatsApp/Telegram).

* **Process:**

  1. Warga *login* menggunakan **Face Recognition / NIK Verification** (mencegah bot/buzzer).
  2. Warga membaca ringkasan 1 menit dan memberikan suara (*Vote* Pro/Kontra + Komentar).
  3. Hasil *voting* di-agregasi dan dikembalikan ( *feedback loop* ) ke **Lex DSS** sebagai bobot suara publik resmi.

## 📊 Data Payload Standard (JSON)

Berikut adalah struktur JSON yang dialirkan dari **Lex DSS** ke **e-Netizen Voting**.
Bentuk di bawah adalah **kontrak v1.0** yang sudah diimplementasikan di
`app/services/civic_poll_client.py` dan divalidasi `CivicPollImportSerializer`
di sisi e-Netizen.

> Skema ini menggantikan draf `source_metadata` / `micro_poll_payload` yang
> pernah ada di dokumen ini. Field `voting_guard` juga dihapus: e-Netizen
> menegakkan verifikasi OTP dan DPT secara tidak kondisional, sehingga tidak
> ada tempat untuk menyetelnya per-polling.

**JSON**

```
{
  "schema_version": "1.0",
  "event_id": "POLL-2026-SLM-008",
  "generated_at": "2026-09-29T10:00:00+07:00",
  "source": {
    "type": "youtube_video",
    "url": "https://www.youtube.com/watch?v=example_dprd_diy",
    "publisher": "DPRD Kabupaten Sleman",
    "title": "Rapat Paripurna Pembahasan Raperda Retribusi Daerah",
    "segment_start_seconds": 4460,
    "segment_end_seconds": 6310
  },
  "legal_audit": {
    "summary": "Kenaikan retribusi pedagang pasar tradisional",
    "jurisdiction": "Pemprov DIY / Pemkab Sleman",
    "references": [
      { "title": "UU No. 1 Tahun 2022", "article": "Pasal ...", "quote": "..." }
    ],
    "risks": [
      "Diskresi kenaikan tarif hingga 20% dapat ditentukan sepihak oleh Perbup tanpa persetujuan DPRD."
    ],
    "limitations": [],
    "confidence": 0.78
  },
  "poll_draft": {
    "question": "DPRD sedang membahas kenaikan retribusi pasar sebesar 15%. Bagaimana pendapatmu?",
    "description": "Ringkasan isu satu menit untuk warga.",
    "disclaimer": "Jajak pendapat konsultatif; hasilnya bukan keputusan hukum yang mengikat.",
    "options": [
      { "code": "A", "label": "Setuju (Fasilitas pasar harus diperbaiki)" },
      { "code": "B", "label": "Setuju dengan Syarat (Kenaikan maksimal 5%)" },
      { "code": "C", "label": "Tolak (Mencabut pasal diskresi Perbup)" }
    ],
    "opens_at": "2026-09-29T12:00:00+07:00",
    "closes_at": "2026-10-06T12:00:00+07:00",
    "region_code": "ID-SL"
  }
}
```

## 🔐 Autentikasi Request

Setiap request ditandatangani HMAC-SHA256 atas `timestamp + "." + body`:

| Header | Nilai |
| ------ | ----- |
| `X-Lex-Timestamp` | epoch detik (e-Netizen menolak selisih > 300 detik) |
| `X-Lex-Signature` | `sha256=` + HMAC-SHA256(`ENETIZEN_HMAC_SECRET`, `timestamp + "." + body`) |

`ENETIZEN_HMAC_SECRET` di Lex-DSS harus sama dengan `LEX_DSS_HMAC_SECRET` di
backend e-Netizen. Karena tanda tangan dihitung atas byte body, body wajib
dikirim apa adanya tanpa serialisasi ulang — itulah sebabnya `canonical_body()`
menggunakan separator padat. Kesiakan integrasi dapat dicek tanpa membocorkan
rahasia lewat `GET /api/v1/integration/sources`.

## 🔁 Alur Agregat Balik (Feedback Loop)

Hasil agregat ditarik Lex-DSS dari `GET /api/votes/public/civic/{topic_id}/`
lalu disimpan sebagai snapshot **append-only** pada tabel `civic_poll_results`.
Setiap perubahan substantif menghasilkan `revision` baru, sehingga histori bobot
suara publik tetap dapat diaudit dan polling yang dikoreksi tidak menghapus
jejak angka lamanya.

| Endpoint Lex-DSS | Fungsi |
| ---------------- | ------ |
| `POST /api/v1/civic-poll/drafts` | Kirim draf polling bertanda tangan HMAC; idempoten terhadap `event_id` |
| `POST /api/v1/civic-poll/events/{event_id}/collect` | Tarik agregat dari e-Netizen |
| `GET /api/v1/civic-poll/events/{event_id}/results` | Riwayat seluruh revisi agregat |
| `GET /api/v1/civic-poll/results/latest` | Agregat terbaru per polling + `evidence_grade` |

Field `evidence_grade` memastikan DSS tidak memperlakukan polling tanpa jejak
verifikasi setara dengan jajak pendapat bersampel memadai:

| Grade | Arti |
| ----- | ---- |
| `VERIFIED` | Punya `evidence_root` dan partisipasi ≥ 5% |
| `PARTIAL` | Punya `evidence_root`, data partisipasi belum tersedia |
| `LOW_PARTICIPATION` | Bukti ada, tapi sampel terlalu kecil untuk burden pembuktian tinggi |
| `UNVERIFIED` | Angka tanpa bukti integritas — jangan dipakai sebagai bobot |
| `VOIDED` | Polling dibatalkan atau dikoreksi di sisi e-Netizen |

## 📈 Impact Matrix Integrasi

| **Parameter**           | **Metode Lama (YouTube/JDIH Konvensional)** | **Metode Integrasi (Lex Suite + e-Netizen)** |
| ----------------------------- | ------------------------------------------------- | -------------------------------------------------- |
| **Format Informasi**    | Video 3 jam / PDF 200 Halaman                     | Ringkasan Teks 1 Menit (*Micro-Digest* )         |
| **Bahasa**              | Hukum Kaku / Birokrasi                            | Bahasa Awam Berbasis Dampak Sosial                 |
| **Tingkat Partisipasi** | Rendah (<1% Warga Awam)                           | Tinggi (Satu-Klik Polling dari HP)                 |
| **Keamanan Data**       | Tanpa Validasi (Rentan Bot Sosial Media)          | Anti-Fraud via Face Recognition / NIK              |
| **Output Akhir**        | Dokumen Sepihak tanpa Feedback                    | Data Agregat Suara Publik (*Evidence-Based* )    |
