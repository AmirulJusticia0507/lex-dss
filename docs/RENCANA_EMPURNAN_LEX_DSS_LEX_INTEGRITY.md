# Rencana Penyempurnaan Lex-DSS & Lex Integrity
## Integrasi dengan Sistem e-LHKPN KPK

**Tanggal**: 28 September 2026  
**Status**: Draft untuk Analisis  
**Sumber Referensi**: https://elhkpn.kpk.go.id/portal/user/login

---

## 1. Analisis e-LHKPN (Sistem Pelaporan Harta Kekayaan)

### 1.1 Fitur Utama e-LHKPN

| Modul | Fungsi | Potensi Integrasi |
|-------|--------|-------------------|
| **e-Announcement** | Pencarian publik LHKPN berdasarkan NIK/Nama/Tahun/Instansi | Data enrichment untuk analisis kekayaan |
| **e-Filing** | Pelaporan harta kekayaan oleh Penyelenggara negara | Validasi silang dengan data publik |
| **e-Registration** | Manajemen wajib lapor oleh Unit Pengelola (UPL) | Monitoring kepatuhan instansi |
| **Monitoring Implementasi** | Dashboard kepatuhan pelaporan | Integrasi dengan deviation alert system |
| **Peta Kepatuhan** | Visualisasi geografis kepatuhan | Analisis regional korupsi |
| **WL Belum Lapor/Lengkap** | Daftar yang tidak patuh | Flagging sistem |

### 1.2 Data yang Tersedia via e-Announcement

Berdasarkan halaman publik e-LHKPN, data yang dapat diakses:

```
- Nama Penyelenggara Negara
- Lembaga/Instansi
- Unit Kerja
- Jabatan
- Tanggal Lapor
- Jenis Laporan (Periodik/Khusus)
- Total Harta Kekayaan (dalam Rupiah)
- Tahun Lapor (mulai 2017)
```

### 1.3 Regulasi Terkait

| Regulasi | Keterangan |
|----------|------------|
| UU No. 28 Tahun 1999 | Penyelenggara Negara yang Bebas dari KKN |
| UU No. 30 Tahun 2002 (jo. UU 19/2019) | Komisi Pemberantasan Korupsi |
| Perka KPK No. 07 Tahun 2016 (jo. Perka KPK No. 03 Tahun 2024) | Tata Cara Pendaftaran, Pengumuman, Pemeriksaan LHKPN |

---

## 2. Gap Analysis: Lex-DSS & Lex Integrity Saat Ini

### 2.1 Lex-DSS (Python/FastAPI)

**Yang sudah ada:**
- Cross-norm conflict detection (Lex Superior, Lex Specialis, Lex Posterior)
- RAG pipeline dengan pgvector semantic search
- Deviation Alert System (skor 0-100)
- Legal domain services (HTN, Pidana, Perdata)
- Integrasi dengan Lex Integrity (44.570 rules)

**Yang belum ada:**
- Integrasi data LHKPN untuk analisis kekayaan
- Deteksi anomaly kekayaan (wealth anomaly detection)
- Cross-reference antara jabatan publik dan harta kekayaan
- Monitoring kepatuhan LHKPN per instansi
- Analisis temporal (perkembangan harta dari tahun ke tahun)

### 2.2 Lex Integrity (Node.js/Express)

**Yang sudah ada:**
- Rules engine untuk deteksi kontradiksi norma
- Multi-hop reasoning agent
- RAG dengan Ollama nomic-embed (768-dim)
- Scraping regulasi

**Yang belum ada:**
- Integrasi dengan data LHKPN
- Analisis pola kekayaan tidak wajar
- Deteksi indikasi penyalahgunaan wewenang berbasis data kekayaan

---

## 3. Rencana Pengembangan

### Fase 1: Data Integration Layer (2-3 minggu)

#### 1.1 Integrasi Data LHKPN — Pendekatan Realistis

**Temuan penting**: e-Announcement **bukan API terbuka**. Form resmi KPK ("Formulir Permohonan Aktivasi Tautan e-Announcement LHKPN") hanya untuk **instansi pemerintah** yang ingin menampilkan tautan pengumuman di website resmi mereka. Lex-DSS sebagai proyek non-instansi **tidak bisa langsung mengajukan**.

**Opsi integrasi yang tersedia:**

| Opsi | Kelebihan | Kekurangan | Rekomendasi |
|------|-----------|------------|-------------|
| **A. Scraping halaman publik** | Data langsung dari sumber resmi | Legal grey area, rate limit, fragile | ⚠️ Hati-hati |
| **B. Partner dengan instansi** | Akses legal, data lengkap | Perlu negosiasi, lambat | ✅ Ideal jangka panjang |
| **C. Input manual pilot** | Cepat untuk mulai, legal | Tidak scalable | ✅ Untuk Fase 1 |
| **D. Data alternatif (DPR, dll)** | Lebih mudah diakses | Tidak sekomprehensif LHKPN | ✅ Pelengkap |

**Rekomendasi strategi:**
1. **Fase 1 (Pilot)**: Input manual + scraping terbatas untuk validasi konsep
2. **Fase 2**: Ajukan kerjasama resmi dengan instansi/KPK untuk akses data
3. **Fase 3**: Integrasi penuh setelah MoU ditandatangani

#### Opsi A: Scraping (Untuk Pilot)
```
Target: https://elhkpn.kpk.go.id/portal/user/pengumuman_lhkpn/
Data yang bisa di-scrape:
- Nama, Jabatan, Unit Kerja, Tanggal Lapor, Total Harta Kekayaan

Langkah:
- [ ] Buat scraper dengan rate limit (max 1 request/5 detik)
- [ ] Respect robots.txt dan terms of service
- [ ] Cache hasil scrape ke database lokal
- [ ] Implementasi incremental update (hanya data baru)
```

#### Opsi C: Input Manual (Untuk Validasi)
```
Langkah:
- [ ] Buat form input manual di admin panel
- [ ] Definikan minimal dataset untuk pilot (50-100 pejabat)
- [ ] Validasi konsep anomaly detection dengan data terbatas
```

#### 1.2 Database Schema Extension
```sql
-- Tabel baru untuk data LHKPN
CREATE TABLE lhkpn_reports (
    id UUID PRIMARY KEY,
    nik VARCHAR(16) UNIQUE NOT NULL,
    nama VARCHAR(255),
    lembaga VARCHAR(255),
    unit_kerja VARCHAR(255),
    jabatan VARCHAR(255),
    tahun_lapor INTEGER,
    jenis_laporan VARCHAR(50), -- Periodik/Khusus
    total_harta DECIMAL(18,2),
    tanggal_lapor DATE,
    status VARCHAR(50), -- Terverifikasi/Tidak Lengkap
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index untuk pencarian
CREATE INDEX idx_lhkpn_nik ON lhkpn_reports(nik);
CREATE INDEX idx_lhkpn_lembaga ON lhkpn_reports(lembaga);
CREATE INDEX idx_lhkpn_tahun ON lhkpn_reports(tahun_lapor);
```

### Fase 2: Wealth Anomaly Detection Engine (3-4 minggu)

#### 2.1 Algoritma Deteksi Anomali
```
Indikator Anomali:
1. Wealth Velocity Score
   - Perhitungan: (Harta tahun N - Harta tahun N-1) / Harta tahun N-1
   - Threshold: >100% kenaikan dalam 1 tahun = FLAG

2. Income-to-Wealth Ratio
   - Perbandingan total harta vs penghasilan yang dilaporkan
   - Threshold: Rasio > 5x = Review lebih lanjut

3. Peer Comparison Score
   - Perbandingan dengan jabatan/sektor yang sama
   - Z-score terhadap distribusi harta jabatan serupa

4. Asset Composition Anomaly
   - Deteksi pola harta yang tidak wajar
   - Contoh: tiba-tiba memiliki properti besar tanpa riwayat usaha
```

#### 2.2 Integrasi dengan Deviation Alert System
```
Skema Integrasi:
- Deviation Score existing (0-100) tetap untuk analisis putusan
- Wealth Anomaly Score (0-100) sebagai dimensi baru
- Combined Risk Score = weighted average keduanya

Formula:
Combined Risk = (0.6 × Deviation Score) + (0.4 × Wealth Anomaly Score)
```

### Fase 3: Conflict of Interest Detection (2-3 mingku)

#### 3.1 Cross-Reference Engine
```
Skenario Deteksi:
1. Hakim vs Kasus
   - Apakah hakim memiliki hubungan usaha dengan pihak dalam kasus?
   - Cross-ref: jabatan + lokasi + jenis harta

2. Pejabat vs Kontraktor
   - Apakah pejabat memiliki saham di perusahaan yang dikontrakan?
   - Cross-ref: jabatan + lembaga + aset perusahaan

3. Politisi vs Regulasi
   - Apakah ada perubahan regulasi yang menguntungkan bisnis pribadi?
   - Cross-ref: jabatan + timeline regulasi + perubahan harta
```

### Fase 4: Compliance Monitoring Dashboard (2 minggu)

#### 4.1 Monitoring per Instansi
```
Metrics:
- Tingkat kepatuhan pelaporan (%)
- Rata-rata keterlambatan pelaporan (hari)
- Jumlah WL belum lapor
- Jumlah WL belum lengkap
- Tren kepatuhan tahunan

Visualisasi:
- Peta kepatuhan per provinsi
- Bar chart per instansi
- Line chart tren temporal
```

### Fase 5: Enhancement Lex Integrity (2-3 minggu)

#### 5.1 New Rules untuk LHKPN
```
Rules baru yang ditambahkan ke Lex Integrity:

1. Rule: LHKPN Compliance Check
   - IF jabatan = "Penyelenggara Negara" AND status_lhkpn = "Belum Lapor"
   - THEN flag = "Non-Compliant"

2. Rule: Wealth-Jabatan Mismatch
   - IF total_harta > 3x rata_rata_jabatan AND sumber_harta = "Tidak Jelas"
   - THEN flag = "Anomali Kekayaan"

3. Rule: Rapid Wealth Accumulation
   - IF kenaikan_harta_tahunan > 100% AND jabatan = "Pejabat Publik"
   - THEN flag = "Investigasi Lanjut"
```

---

## 4. Arsitektur yang Diusulkan

```
┌─────────────────────────────────────────────────────────────┐
│                    Lex-DSS (Enhanced)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Existing   │  │   LHKPN      │  │   Wealth         │  │
│  │   Engines    │  │   Service    │  │   Anomaly        │  │
│  │              │  │   Layer      │  │   Engine         │  │
│  │ - RAG        │  │              │  │                  │  │
│  │ - Deviation  │  │ - API Client │  │ - Velocity Score │  │
│  │ - Conflict   │  │ - Cache      │  │ - Peer Compare   │  │
│  │   Detection  │  │ - Normalizer │  │ - Composition   │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │            │
│         └─────────────────┼────────────────────┘            │
│                           │                                 │
│                    ┌──────┴───────┐                         │
│                    │  Combined    │                         │
│                    │  Risk Score  │                         │
│                    │  Engine      │                         │
│                    └──────┬───────┘                         │
│                           │                                 │
│                    ┌──────┴───────┐                         │
│                    │  PostgreSQL  │                         │
│                    │  + pgvector  │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  e-LHKPN KPK     │
                    │  (External API)  │
                    └──────────────────┘
```

---

## 5. Timeline Implementasi

| Fase | Durasi | Deliverable | Ketergantungan |
|------|--------|-------------|---------------|
| Fase 1 | 2-3 minggu | DB Schema + Scraper/Input Manual | — |
| Fase 2 | 3-4 minggu | Wealth Anomaly Engine (pilot) | Fase 1 |
| Fase 3 | 2-3 minggu | Conflict of Interest Detection | Fase 2 |
| Fase 4 | 2 minggu | Compliance Dashboard | Fase 1-3 |
| Fase 5 | 2-3 minggu | Lex Integrity Enhancement | Fase 2 |
| Fase 6 | 2-4 minggu | Negosiasi MoU dengan KPK/Instansi | Fase 2 (hasil pilot) |
| **Total** | **13-19 minggu** | **Sistem Terintegrasi** | — |

---

## 6. Kebutuhan Resource

### 6.1 Tim
- 1x Backend Developer (Python/FastAPI)
- 1x Frontend Developer (Vue.js)
- 1x Data Engineer (untuk ETL & anomaly detection)
- 1x Legal Expert (untuk validasi rules)

### 6.2 Infrastruktur
- Server dengan akses internet untuk API KPK
- PostgreSQL + pgvector (existing)
- Redis cache (existing)
- Ollama untuk LLM (existing)

### 6.3 Perizinan & Legal
- **TIDAK BISA** mengajukan permohonan API e-Announcement (khusus instansi pemerintah)
- **ALTERNATIF**: Ajukan surat kerjasama resmi ke KPK untuk akses data
- **Kontak KPK**: elhkpn@kpk.go.id / Call Center 198
- **Perlu**: MoU atau surat resmi dari instansi yang berwenang

---

## 7. Risk & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API KPK lambat/tidak stabil | Medium | High | Implementasi retry + cache lokal |
| Data LHKPN tidak lengkap | Medium | Medium | Fallback ke manual verification |
| False positive anomaly | High | Medium | Human-in-the-loop validation |
| Perubahan format API KPK | Low | High | Abstract API layer + versioning |
| Legal/compliance issue | Low | High | Konsultasi dengan legal team KPK |

---

## 8. Next Steps

1. **Review rencana ini** dengan stakeholder
2. **Tentukan opsi integrasi**: scraping terbatas vs input manual untuk pilot
3. **Setup development environment** untuk Fase 1 (DB Schema + Scraper)
4. **Kumpulkan dataset pilot** (50-100 pejabat) untuk validasi konsep
5. **Buat surat kerjasama** ke KPK/instansi untuk akses data resmi
6. **Weekly progress review** setiap Jumat

---

## Referensi

- [e-LHKPN Portal](https://elhkpn.kpk.go.id/portal/user/login)
- [Perka KPK No. 03 Tahun 2024](https://elhkpn.kpk.go.id/download/Peraturan%20KPK%20Nomor%2003%20Tahun%202024%20-%20Tentang%20LHKPN.pdf)
- [Form Permohonan API e-Announcement](https://elhkpn.kpk.go.id/download/Form_Permohonan_Link_API_e-Announcement.pdf)
- [Lex-DSS Architecture](./ARCHITECTURE.md)
- [Lex Integrity Integration](./INTEGRASI_LEX_INTEGRITY.md)
