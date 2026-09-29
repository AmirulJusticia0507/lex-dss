
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

Berikut adalah struktur JSON yang dialirkan antar-sistem dari **Lex Integrity/DSS** ke  **e-Netizen Voting** :

**JSON**

```
{
  "source_metadata": {
    "youtube_url": "https://www.youtube.com/watch?v=example_dprd_diy",
    "session_title": "Rapat Paripurna Pembahasan Raperda Retribusi Daerah",
    "timestamp_marker": "01:14:20 - 01:45:10"
  },
  "legal_audit": {
    "topic": "Kenaikan Retribusi Pedagang Pasar Tradisional",
    "affected_jurisdiction": "Pemprov DIY / Pemkab Sleman",
    "referenced_rules": ["UU No. 1 Tahun 2022", "PERDA-SLEMAN-2023-04"],
    "detected_loopholes": "Diskresi kenaikan tarif hingga 20% dapat ditentukan sepihak oleh Perbup tanpa persetujuan DPRD.",
    "humanitarian_impact": "Dapat menekan pendapatan pedagang mikro/kecil hingga 12% di tengah inflasi bahan pokok."
  },
  "micro_poll_payload": {
    "poll_id": "POLL-2026-SLM-008",
    "simplified_question": "DPRD sedang membahas wacana kenaikan retribusi pasar sebesar 15% untuk perbaikan fasilitas. Bagaimana pendapatmu?",
    "options": [
      { "id": "A", "label": "Setuju (Fasilitas pasar harus diperbaiki)" },
      { "id": "B", "label": "Setuju dengan Syarat (Kenaikan maksimal 5%)" },
      { "id": "C", "label": "Tolak (Mencabut pasal diskresi Perbup)" }
    ],
    "voting_guard": {
      "require_face_match": true,
      "require_valid_nik": true
    }
  }
}
```

## 📈 Impact Matrix Integrasi

| **Parameter**           | **Metode Lama (YouTube/JDIH Konvensional)** | **Metode Integrasi (Lex Suite + e-Netizen)** |
| ----------------------------- | ------------------------------------------------- | -------------------------------------------------- |
| **Format Informasi**    | Video 3 jam / PDF 200 Halaman                     | Ringkasan Teks 1 Menit (*Micro-Digest* )         |
| **Bahasa**              | Hukum Kaku / Birokrasi                            | Bahasa Awam Berbasis Dampak Sosial                 |
| **Tingkat Partisipasi** | Rendah (<1% Warga Awam)                           | Tinggi (Satu-Klik Polling dari HP)                 |
| **Keamanan Data**       | Tanpa Validasi (Rentan Bot Sosial Media)          | Anti-Fraud via Face Recognition / NIK              |
| **Output Akhir**        | Dokumen Sepihak tanpa Feedback                    | Data Agregat Suara Publik (*Evidence-Based* )    |
