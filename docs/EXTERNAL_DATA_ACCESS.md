# Permohonan Akses Data Eksternal

## Prinsip

Jangan memakai kredensial akun pegawai, scraping endpoint login, atau data pribadi tanpa dasar hukum dan persetujuan tertulis. Simpan kredensial yang diterbitkan instansi hanya di `backend/.env`.

## Paket permohonan standar

Kirim surat resmi (kop organisasi) dan lampirkan:

1. Nama organisasi, penanggung jawab, PIC teknis, serta kontak keamanan.
2. Tujuan penggunaan dan modul Lex-DSS yang menerima data.
3. Dataset/field minimum, frekuensi sinkronisasi, volume, dan masa retensi.
4. Arsitektur keamanan: TLS, enkripsi at-rest, RBAC, audit log, dan prosedur penghapusan.
5. Dasar pemrosesan data, DPA/PKS bila dibutuhkan, serta SOP insiden.
6. Permintaan sandbox, dokumentasi API, rate limit, mekanisme OAuth/API key, dan SLA.

## Tujuan per instansi

| Instansi | Permintaan minimum | Modul |
|---|---|---|
| MA / SIPP | Metadata putusan publik, URL dokumen, pembaruan status perkara; API/sandbox resmi | Putusan Pengadilan, Case Law |
| BPHN / JDIHN | Metadata dan dokumen regulasi publik, perubahan/penarikan dokumen | Regulatory Impact Analysis |
| BKPM / OSS | Status perizinan milik badan usaha yang memberi kuasa, melalui client credential resmi | Compliance Checker |
| DJP | Validasi NPWP/NIK hanya dalam skema ILAP/otorisasi yang berlaku | Compliance Checker |
| Kemenperin | Data izin/registrasi industri yang berwenang diakses | Compliance Checker |
| DPR / DPRD | Metadata RUU/Raperda, tahapan pembahasan, agenda, dan dokumen publik | Legislative Tracker |

## Setelah disetujui

Masukkan endpoint dan kredensial pada `backend/.env`, lalu verifikasi status tanpa membocorkan rahasia:

```text
GET /api/v1/integration/sources
```

Endpoint ini hanya tersedia untuk admin dan hanya menampilkan apakah konfigurasi lengkap.

JDIHN menyebut proses integrasi anggotanya melibatkan pendaftaran, verifikasi, konfigurasi API, dan sinkronisasi dengan Pusat JDIHN. Untuk akses perpajakan, gunakan jalur dan otorisasi DJP yang ditetapkan, bukan data akun wajib pajak.
