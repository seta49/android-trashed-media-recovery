# Analisis Teknis: Membaca Nama File Sampah MediaStore

Catatan pendalaman untuk kasus pemulihan media yang dipindahkan ke tempat sampah sistem Android 11+.

## 1. Format nama

```text
.trashed-<dateExpires>-<namaAsli>
```

Definisi resmi (AOSP `MediaProvider` → `util/FileUtils.java`):

```java
PATTERN_EXPIRES_FILE = (?i)^\.(pending|trashed)-(\d+)-([^/]+)$
DEFAULT_DURATION_TRASHED = 30 hari
DEFAULT_DURATION_PENDING  = 7 hari
```

- `<dateExpires>` dalam **detik** (bukan milidetik).
- `<namaAsli>` adalah seluruh sisa setelah tanda hubung **kedua**, jadi nama asli boleh mengandung `-` dan `.`.
- Prefiks dicocokkan tanpa peduli huruf besar/kecil; huruf pada nama asli dipertahankan.
- `.pending-` adalah mekanisme 7 hari (file yang belum selesai ditulis/ditahan), `.trashed-` adalah sampah 30 hari.
- Keuntungan desain ini: nama file saja sudah cukup untuk memulihkan nama asli **dan** waktu kedaluarsa, meski basis data MediaStore terhapus.

## 2. Menghitung waktu kedaluarsa dan perkiraan waktu dipindahkan

```python
import datetime as dt

expiry = dt.datetime.fromtimestamp(1793714007, dt.timezone(dt.timedelta(hours=7)))  # WIB
trashed = expiry - dt.timedelta(days=30)
print(expiry.strftime("%d %b %Y %H:%M"))   # 03 Nov 2026 20:53
print(trashed.strftime("%d %b %Y %H:%M"))  # 04 Oct 2026 20:53
```

Skrip lengkap untuk membedah seluruh daftar file: lihat `scripts/decode-expiry.py`.

## 3. Temuan pada kasus nyata

2.085 file, total 56,29 GB, tersebar di 12 folder:

- Waktu pemindahan ke sampah yang terbaca (dari nama file) **tidak** satu tanggal: terkumpul di **5 hari berbeda antara 5 Sep dan 4 Okt 2026**. Artinya pemindahan tidak terjadi sekali dalam satu peristiwa yang seragam — ada perilaku berulang. Ini penting dicatat ketika hendak melaporkan kasus ke dukungan penyedia cloud.
- File yang paling cepat kedaluarsa jatuh persis pada **hari pengerjaan pemulihan** (5 Okt 2026, 10:09). Jika ditunda beberapa hari, sebagian file akan dihapus permanen oleh sistem.
- Ukuran file yang paling besar adalah video: 2,1 GB, 1,7 GB, 1,4 GB, 1,3 GB.
- Semua file sampel yang diuji (JPEG, HEIC, PNG, MP4, WebP) memiliki header valid dan ukuran yang identik dengan sebelum pemulihan → datanya tidak rusak, murni hanya berganti nama.

## 4. Kenapa galeri menampilkan entri "error"

Karena galeri masih menyimpan **entri lama** (thumbnail/cache) untuk file yang sekarang berstatus `IS_TRASHED=1` dan namanya diawali titik. Entri tersebut tidak lagi punya file yang bisa dibuka — sesuai dengan gejala yang dilaporkan: "ada, tapi tidak bisa dibuka". Setelah nama dikembalikan dan galeri mengindeks ulang (perintah `content call ... scan_volume` atau restart), entri itu kembali normal.

## 5. Perbandingan jalur pemulihan

| Jalur | Butuh kuota cloud | Butuh root | Kelengkapan | Catatan |
|---|---|---|---|---|
| Restore dari Sampah Google Photos | **Ya** | Tidak | Tergantung kuota | Mengembalikan salinan ke cloud; gagal jika kuota penuh |
| Rename nama file (metode dokumen ini) | Tidak | Tidak | Lengkap | Langsung pada file lokal yang sudah ada |
| Copy via Windows Explorer/MTP | Tidak | Tidak | **Tidak lengkap** | Item bertanda sampah disembunyikan MediaStore |
| Aplikasi "photo recovery" | Tidak | Umumnya ya | Tidak pasti | Tidak diperlukan untuk kasus ini |

## 6. Batas metode ini

- Hanya berlaku jika file **masih ada** di penyimpanan (masih ada entri `.trashed-`/`.pending-`).
- Tidak membantu untuk file yang sudah benar-benar terhapus: namanya sudah bukan pola `.trashed-`, dan pemulihan di penyimpanan internal Android modern (terenkripsi) praktis tidak mungkin tanpa root.
- Jika file berada di kartu SD, perilaku MediaStore berbeda — item di kartu SD tidak selalu benar-benar ditandai sampah.
