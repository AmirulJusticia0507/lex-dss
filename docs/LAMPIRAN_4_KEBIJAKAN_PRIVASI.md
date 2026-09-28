# Lampiran 4: Kebijakan Privasi, Keamanan, Retensi, dan Penghapusan Data

---

## 1. Kebijakan Privasi

### 1.1 Ruang Lingkup

Kebijakan ini berlaku untuk seluruh data yang diproses oleh Lex-DSS, khususnya data LHKPN yang digunakan dalam pilot riset.

### 1.2 Prinsip Pemrosesan Data

| Prinsip | Implementasi |
|---------|-------------|
| **Lawfulness** | Hanya memproses data publik yang diumumkan KPK |
| **Purpose Limitation** | Hanya untuk riset dan pengembangan sistem |
| **Data Minimization** | Hanya data agregat, tidak ada data individu |
| **Accuracy** | Validasi silang dengan sumber resmi |
| **Storage Limitation** | Maksimal 6 bulan, lalu dihapus |
| **Integrity** | Enkripsi AES-256, access control |
| **Accountability** | Audit log untuk setiap akses |

### 1.3 Hak Subjek Data

Meskipun hanya menggunakan data agregat, Lex-DSS menghormati hak subjek data:

- **Right to Information** — subjek dapat meminta informasi tentang data yang diproses
- **Right to Access** — subjek dapat meminta salinan data mereka
- **Right to Rectification** — subjek dapat meminta koreksi data yang salah
- **Right to Erasure** — subjek dapat meminta penghapusan data mereka
- **Right to Object** — subjek dapat menolak pemrosesan data mereka

---

## 2. Keamanan Data

### 2.1 Keamanan Teknis

| Aspek | Implementasi |
|-------|-------------|
| **Encryption at Rest** | AES-256 untuk database |
| **Encryption in Transit** | TLS 1.3 untuk semua koneksi |
| **Access Control** | Role-Based Access Control (RBAC) |
| **Authentication** | JWT dengan refresh token |
| **Authorization** | Middleware untuk setiap endpoint |
| **Input Validation** | Schema validation (Pydantic) |
| **SQL Injection Prevention** | Parameterized queries (SQLAlchemy) |
| **XSS Prevention** | Output encoding, CSP headers |
| **CSRF Protection** | SameSite cookies, CSRF tokens |

### 2.2 Keamanan Operasional

| Aspek | Implementasi |
|-------|-------------|
| **Audit Log** | Semua akses data dicatat |
| **Monitoring** | Real-time alert untuk aktivitas mencurigakan |
| **Backup** | Daily backup dengan enkripsi |
| **Disaster Recovery** | RPO 24 jam, RTO 4 jam |
| **Vulnerability Management** | Regular security scan |
| **Patch Management** | Update berkala |

### 2.3 Access Control Matrix

| Role | Data LHKPN | Data Internal | Audit Log | System Config |
|------|-----------|---------------|-----------|---------------|
| **Admin** | Full | Full | Full | Full |
| **Researcher** | Read | Read | None | None |
| **Analyst** | Read (aggregated) | Read | None | None |
| **Auditor** | None | None | Read | None |

---

## 3. Retensi Data

### 3.1 Jadwal Retensi

| Jenis Data | Periode Retensi | Alasan |
|-----------|-----------------|--------|
| Data LHKPN mentah | 6 bulan | Periode pilot |
| Data LHKPN agregat | 12 bulan | Analisis tren |
| Analysis result | 6 bulan | Evaluasi model |
| Audit log | 12 bulan | Compliance |
| User account | Selama akun aktif | Kebutuhan operasional |
| Session token | 24 jam | Security |

### 3.2 Prosedur Retensi

```
┌─────────────────┐
│  Data Created   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Active Period  │
│  (Processing)   │
└────────┬────────┘
         │
         ▼ (After 6 months)
┌─────────────────┐
│  Archive Period │
│  (Cold Storage) │
└────────┬────────┘
         │
         ▼ (After 12 months)
┌─────────────────┐
│  Deletion       │
│  (Permanent)    │
└─────────────────┘
```

---

## 4. Penghapusan Data

### 4.1 Metode Penghapusan

| Level | Metode | Verifikasi |
|-------|--------|------------|
| **Database** | Hard delete (DELETE query) | Row count verification |
| **Backup** | Crypto-shredding | Key destruction verification |
| **Cache** | Flush Redis | Cache miss verification |
| **Log** | Anonymize (remove PII) | Log review |

### 4.2 Prosedur Penghapusan

1. **Request** — Permintaan penghapusan dari subjek data atau admin
2. **Verification** — Verifikasi identitas pemohon
3. **Execution** — Eksekusi penghapusan di semua storage
4. **Verification** — Verifikasi penghapusan berhasil
5. **Logging** — Catat penghapusan di audit log
6. **Notification** — Notifikasi ke subjek data (jika diminta)

### 4.3 SLA Penghapusan

| Tahap | SLA |
|-------|-----|
| Request diterima | Hari 0 |
| Verification selesai | Hari 1-2 |
| Penghapusan dieksekusi | Hari 3-5 |
| Verifikasi selesai | Hari 6-7 |
| Notifikasi dikirim | Hari 7-10 |

---

## 5. Incident Response

### 5.1 Klasifikasi Insiden

| Level | Contoh | Response Time |
|-------|--------|---------------|
| **Critical** | Data breach, unauthorized access | 1 jam |
| **High** | System compromise, malware | 4 jam |
| **Medium** | Policy violation, misconfiguration | 24 jam |
| **Low** | Minor security event | 72 jam |

### 5.2 Prosedur Incident Response

```
┌─────────────────┐
│  Detection      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Containment    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Eradication    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Recovery       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Lessons       │
│  Learned        │
└─────────────────┘
```

### 5.3 Notifikasi Breach

Jika terjadi data breach:
1. **Internal**: Notifikasi ke tim dalam 1 jam
2. **KPK**: Notifikasi ke KPK dalam 24 jam
3. **Subjek Data**: Notifikasi dalam 72 jam (jika diperlukan)
4. **Publik**: Notifikasi dalam 7 hari (jika diperlukan)

---

## 6. Compliance

### 6.1 Regulasi yang Dipatuhi

| Regulasi | Keterangan |
|----------|------------|
| UU No. 27 Tahun 2022 | Pelindungan Data Pribadi |
| Perka KPK No. 03 Tahun 2024 | Tata Cara LHKPN |
| ISO 27001 | Information Security Management |

### 6.2 Audit

| Jenis Audit | Frekuensi | Auditor |
|-------------|-----------|---------|
| Internal Audit | Quarterly | Tim internal |
| External Audit | Annual | Auditor independen |
| Security Audit | Semi-annual | Security vendor |

---

## 7. Kontak

Untuk pertanyaan terkait kebijakan ini:

| Item | Keterangan |
|------|-----------|
| **Nama** | Amirul Putra Justicia |
| **Email** | amirulputra0507@gmail.com |
| **Telepon** | +6282134402383 |

---

**Dokumen ini terakhir diperbarui**: 28 September 2026
