# Lex-DSS Feature Status

**Terakhir diperbarui**: 28 September 2026

---

## Modul & Status

| Modul | Fungsi | Data Source | Status |
|-------|--------|-------------|--------|
| **Case Law Search** | Pencarian yurisprudensi | MA, PTUN | ✅ On Progress |
| **Contract Analyzer** | Review kontrak otomatis | Upload dokumen | ✅ On Progress |
| **Putusan Pengadilan** | Analisis deviasi putusan hakim | Mahkamah Agung (SIPP) | ⏳ Waiting |
| **Regulatory Impact Analysis** | Dampak regulasi baru | BPHN, Kemenkumham | ⏳ Waiting |
| **Compliance Checker** | Cek kepatuhan perusahaan | OSS, DJP, Kemenperin | ⏳ Waiting |
| **Legislative Tracker** | Monitoring RUU/RPerda | DPR, DPRD | ⏳ Waiting |
| **Legal Risk Scoring** | Skor risiko hukum perusahaan | Integrasi semua modul | ⏳ Waiting |

---

## Keterangan Status

| Icon | Status | Arti |
|------|--------|------|
| ✅ | **On Progress** | Sudah dibuat, sedang development/testing |
| ⏳ | **Waiting** | Belum dimulai, menunggu data source atau prioritas |

---

## Urutan Prioritas (High → Low)

1. **Case Law Search** — data MA sudah publik, langsung bisa dipakai
2. **Contract Analyzer** — tidak butuh API eksternal, cepat selesai
3. **Putusan Pengadilan** — integrasi dengan SIPP
4. **Legislative Tracker** — monitoring RUU dari DPR/DPRD
5. **Regulatory Impact Analysis** — butuh data dari BPHN
6. **Compliance Checker** — butuh integrasi banyak API
7. **Legal Risk Scoring** — integrasi semua modul (terakhir)

---

## Next Steps

1. Selesaikan Case Law Search (tambah data dari SIPP)
2. Testing Contract Analyzer dengan sample kontrak
3. Putus akses ke database putusan pengadilan untuk Putusan Pengadilan
