# Pilot Pemanfaatan Data Lex-Integrity di Lex-DSS

## Hasil

Dump lokal `C:\laragon\www\lex-integrity\dump.sql` berhasil dibaca tanpa memulihkan atau mengubah database. Skrip membuat katalog metadata untuk pemeriksaan awal di:

- `backend/data/lex-integrity-pilot/lex-integrity-catalog.csv`
- `backend/data/lex-integrity-pilot/summary.json`

Folder hasil dikecualikan dari Git karena berisi salinan data dari dump.

| Pemeriksaan | Hasil |
| --- | ---: |
| Baris `rules` | 17.001 |
| Sumber `jogja.prov.go.id` | 17.001 |
| Kategori mentah `Peraturan Daerah` | 17.001 |
| Tautan PDF | 8.005 |
| Isi lebih dari 300 karakter | 0 |
| Embedding pada `rules` | 0 |
| Baris pada `rule_chunks` | 0 |

Nilai `content` pada contoh baris berisi catatan metadata seperti tema, jumlah unduhan, atau judul lama. Nilai tersebut bukan isi norma dan tidak boleh dipakai sebagai teks dasar analisis.

## Uji sumber PDF

Satu permintaan header ke URL PDF dari record pertama menerima status HTTP 200 dan tipe `application/pdf`. Pengunduhan isi PDF berikutnya mengalami timeout koneksi dari lingkungan kerja ini. Karena itu, ekstraksi dan pemeriksaan kualitas PDF belum berhasil dilakukan. Tidak ada PDF yang diunduh atau teks hasil ekstraksi yang disimpan.

## Aturan pemetaan yang aman

- `title` dapat menjadi kandidat `document_title`, setelah dibersihkan dan dicek duplikat.
- `rule_code`, `source`, `publish_date`, `pdf_url`, `source_url`, `regime`, dan kategori asli perlu disimpan sebagai metadata sumber.
- Jangan memakai `category` mentah sebagai jenis peraturan final: dump memakai label Peraturan Daerah untuk judul yang mencakup Peraturan Gubernur dan Keputusan Gubernur.
- Jangan menyimpulkan `domain` hukum dari jenis instrumen. Domain perlu diklasifikasikan dari isi dokumen.
- Setelah PDF dapat diambil, ekstrak teks, segmentasikan pasal, validasi teks terhadap dokumen sumber, baru kirim pasal yang lolos ke endpoint ingest Lex-DSS. Embedding harus dibuat ulang di Lex-DSS.

## Menghasilkan ulang katalog

```powershell
cd C:\laragon\www\lex-dss
python backend/scripts/build_lex_integrity_catalog.py C:\laragon\www\lex-integrity\dump.sql
```

Skrip hanya membaca dump dan menulis katalog lokal. Skrip tidak menghubungi database dan tidak mengirim data ke API Lex-DSS.
