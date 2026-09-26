
# Arsitektur Transparansi & Antirasuah (Integrity & Anti-Corruption Framework)

## 1. Problematika Hukum: Subjektivitas & Transaksi Celah Hukum

Pengambil keputusan sering memanfaatkan tiga celah utama:

1. **Interpretasi Pilihan (*Cherry-picking* Pasal):** Menggunakan pasal yang menguntungkan pihak tertentu dan mengabaikan pasal/peraturan yang lebih tinggi (*Lex Superior*) atau lebih baru (*Lex Posterior*).
2. **Kaburnya Rasio Decidendi:** Keputusan dikeluarkan tanpa argumentasi logis yang terukur, sehingga sulit diuji obyektivitasnya.
3. **Opasitas Rekam Sanggah:** Mengubah konsideran atau draf aturan secara diam-diam tanpa analisis dampak konflik norma.

---

## 2. Fitur Kunci Lex Decision Support System (Anti-Corruption Engine)

### A. Immutable Audit Trail & Decision Lineage

- Setiap rekomendasi keputusannya **mencatat jejak argumen (Chain of Thought)** secara otomatis.
- Menggunakan skema log yang tidak dapat diubah (*tamper-proof / append-only*) untuk mencatat *siapa* yang menyetujui, mengabaikan, atau mengubah rekomendasi AI, beserta alasannya.

### B. Conflict Severity & Deviation Index (Indeks Penyimpangan Legal)

- Jika pengambil keputusan manusia mengambil kebijakan yang bertentangan dengan rekomendasi AI/Lex Integrity, sistem akan menghasilkan **Deviated Risk Score (0-100%)**.
- Skor ini secara otomatis menandai (*flagging*) potensi penyalahgunaan wewenang (*abuse of power* / Pasal 3 UU Tipikor).

### C. Open Data & Public Verification API

- Menyediakan output berupa **Matriks Komparasi Hukum (JSON/PDF)** yang dapat diverifikasi oleh publik, akademisi, atau lembaga pengawas (seperti KPK / Ombudman).

---

## 3. Skema Database Tambahan untuk Transparansi (PostgreSQL)

```sql
-- Tabel untuk mencatat Jejak Keputusan Manusia vs AI (Audit Log)
CREATE TABLE decision_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_title VARCHAR(255) NOT NULL,
    ai_recommendation TEXT NOT NULL,         -- Rekomendasi murni dari AI
    ai_risk_score INT NOT NULL,              -- Skor risiko dari Lex Integrity (0-100)
    human_decision TEXT,                     -- Keputusan akhir yang diambil manusia
    is_deviated BOOLEAN DEFAULT FALSE,       -- True jika manusia menyimpang dari analisis norma
    deviation_justification TEXT,           -- Alasan manusia jika menyimpang
    user_id UUID NOT NULL,                   -- ID Pejabat / Pengambil keputusan
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexing untuk kecepatan pencarian kasus audit
CREATE INDEX idx_audit_deviated ON decision_audit_logs(is_deviated);
```



---

### Peran AI sebagai "Hukum Murni" (Pure Legal Logic)

Dalam sistem ini, AI tidak menggantikan hakim atau pejabat secara yuridis (karena secara HTN dan Administrasi Negara, wewenang tetap ada pada subjek hukum manusia), tetapi **membatasi ruang gerak korupsi** dengan cara:

1. **Mematok Standar Logika Hukum:** Ketika AI menunjukkan bahwa *Pasal A membatalkan Perda B*, pejabat tidak bisa lagi berargumen "tidak tahu" (*ignorantia juris non excusat*).
2. **Transparency by Design:** Jika seorang pejabat nekat menyetujui keputusan yang menabrak norma dasar, sistem langsung memberi status **"HIGH RISK: POTENTIAL NORMATIVE VIOLATION"**.
3. **Mencegah Pasal Pesanan:** Modul *Lex Integrity* dapat membandingkan draf RUU/Raperda baru dengan seluruh basis data hukum Indonesia untuk mendeteksi apakah ada pasal selundupan yang mematikan asas legalitas atau menguntungkan oligarki tertentu.

<ElicitationsGroup message="Bagaimana Anda ingin memperkuat aspek transparansi dan keandalan sistem ini?">      </ElicitationsGroup>
