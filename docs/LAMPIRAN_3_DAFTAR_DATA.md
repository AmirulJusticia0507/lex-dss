# Lampiran 3: Daftar Data yang Diproses

---

## 1. Data LHKPN (Pilot)

| No | Jenis Data | Sumber | Tujuan Pemrosesan | Retensi | Metode Penghapusan |
|----|-----------|--------|-------------------|---------|-------------------|
| 1 | Nama Pejabat Publik | e-Announcement KPK | Identifikasi subjek analisis | 6 bulan | Hard delete dari database |
| 2 | Jabatan | e-Announcement KPK | Kategorisasi peer group | 6 bulan | Hard delete dari database |
| 3 | Unit Kerja/Instansi | e-Announcement KPK | Analisis kepatuhan instansi | 6 bulan | Hard delete dari database |
| 4 | Total Harta Kekayaan | e-Announcement KPK | Perhitungan anomaly score | 6 bulan | Hard delete dari database |
| 5 | Tanggal Lapor | e-Announcement KPK | Analisis temporal | 6 bulan | Hard delete dari database |
| 6 | Tahun Lapor | e-Announcement KPK | Analisis tren tahunan | 6 bulan | Hard delete dari database |

---

## 2. Data yang TIDAK Diproses

| No | Jenis Data | Alasan |
|----|-----------|--------|
| 1 | NIK (Nomor Induk Kependudukan) | Data sensitif, tidak diperlukan untuk analisis agregat |
| 2 | Alamat Rumah | Data sensitif, tidak relevan untuk analisis |
| 3 | Nomor Rekening | Data sensitif, tidak diperlukan |
| 4 | Data Keluarga | Di luar scope pilot |
| 5 | Rincian Harta per Item | Hanya total agregat yang digunakan |
| 6 | Penerimaan/Pengeluaran Detail | Hanya data agregat yang digunakan |

---

## 3. Data Internal Lex-DSS

| No | Jenis Data | Sumber | Tujuan | Retensi | Metode Penghapusan |
|----|-----------|--------|--------|---------|-------------------|
| 1 | User Account | Registrasi | Autentikasi sistem | Selama akun aktif | Soft delete + anonymize |
| 2 | Audit Log | Sistem | Tracking aktivitas | 1 tahun | Hard delete |
| 3 | Analysis Result | Sistem | Output analisis | 6 bulan | Hard delete |
| 4 | Session Token | Sistem | Autentikasi | 24 jam | Auto-expire |

---

## 4. Data Flow Diagram

```
┌─────────────────┐
│  e-LHKPN KPK    │
│  (Data Source)  │
└────────┬────────┘
         │
         │ (Manual Input / API - dengan persetujuan)
         ▼
┌─────────────────┐
│  Staging Area   │
│  (Validation)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Processing     │
│  (Anonymization)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Storage        │
│  (Encrypted)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Analysis       │
│  (Aggregated)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Output         │
│  (Anonymized)   │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Deletion       │
│  (After 6 mo)   │
└─────────────────┘
```

---

## 5. Klasifikasi Data

| Level | Contoh | Handling |
|-------|--------|----------|
| **Public** | Nama pejabat, jabatan, total harta (agregat) | Bisa diproses dengan persetujuan |
| **Internal** | User account, analysis result | Akses terbatas tim |
| **Confidential** | Audit log, system config | Enkripsi + access control |
| **Restricted** | NIK, alamat, data keluarga | TIDAK DIPROSES |

---

## 6. Retensi & Penghapusan

```
Timeline:
─────────────────────────────────────────────────────────►
0         1         2         3         4         5         6 (bulan)
│         │         │         │         │         │         │
│◄─────── Active Processing ───────►│         │         │
│                                   │         │         │
│                                   ◄── Archive ──►│         │
│                                             │         │
│                                             ◄─ Delete ─►│
```

**Prosedur Penghapusan:**
1. Hard delete dari database utama
2. Hard delete dari backup (maks 30 hari setelah penghapusan)
3. Verifikasi penghapusan oleh admin
4. Log penghapusan disimpan untuk audit
