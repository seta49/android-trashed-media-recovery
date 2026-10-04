#!/usr/bin/env python3
"""Uji cepat integritas file media hasil pemulihan.

Memeriksa header (magic bytes) tiap file dan — kalau diberi daftar ukuran asli —
membandingkan ukurannya, supaya kita tidak cuma percaya pada "namanya sudah kembali".

Pemakaian:
    python verify.py ./verify                 # folder berisi file hasil tarik dari HP
    python verify.py ./verify --sizes inv.txt # bandingkan ukuran dgn inventaris
                                              # (format: UKURAN|MTIME|PATH dari inventory.sh)

Kode keluar 0 kalau semua file dikenali, 1 kalau ada yang tidak.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

# (ekstensi, offset, magic, keterangan)
MAGIC = [
    (".jpg", 0, b"\xff\xd8\xff", "JPEG"),
    (".jpeg", 0, b"\xff\xd8\xff", "JPEG"),
    (".png", 0, b"\x89PNG\r\n\x1a\n", "PNG"),
    (".gif", 0, b"GIF8", "GIF"),
    (".webp", 0, b"RIFF", "WebP/RIFF"),
    (".mp4", 4, b"ftyp", "ISO-BMFF (MP4/MOV)"),
    (".mov", 4, b"ftyp", "ISO-BMFF (MP4/MOV)"),
    (".heic", 4, b"ftyp", "HEIF/HEIC"),
    (".dng", 0, b"II", "TIFF/DNG (little-endian)"),
    (".dng", 0, b"MM", "TIFF/DNG (big-endian)"),
]


def kenali(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as f:
        head = f.read(16)
    for e, off, magic, label in MAGIC:
        if e == ext and head[off:off + len(magic)] == magic:
            return label
    return "TIDAK DIKENALI (" + head.hex() + ")"


def baca_ukuran_inventaris(path: str) -> dict[str, int]:
    """Peta nama-asli -> ukuran. Nama file di inventaris masih berawalan
    `.trashed-<angka>-`, jadi prefiksnya dibuang supaya cocok dengan nama
    hasil pemulihan."""
    hasil: dict[str, int] = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            bagian = line.rstrip("\n").split("|", 2)
            if len(bagian) == 3 and bagian[0].isdigit():
                nama = os.path.basename(bagian[2])
                m = re.match(r"^\.(?:trashed|pending)-\d+-(.+)$", nama)
                hasil[m.group(1) if m else nama] = int(bagian[0])
    return hasil


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="folder berisi file yang mau diuji")
    ap.add_argument("--sizes", help="file inventaris (UKURAN|MTIME|PATH) untuk bandingkan ukuran")
    ap.add_argument("--only", help="hanya uji file yang namanya mengandung teks ini")
    args = ap.parse_args()

    size_asli = baca_ukuran_inventaris(args.sizes) if args.sizes else {}
    nama_ke_ukuran = {os.path.basename(k): v for k, v in size_asli.items()}

    file_list = []
    for akar, _, files in os.walk(args.folder):
        for fn in files:
            if args.only and args.only not in fn:
                continue
            file_list.append(os.path.join(akar, fn))
    file_list.sort()

    kalau_kosong = not file_list
    print(f"{'file':<55}{'jenis':<26}{'ukuran':>12}  hasil")
    rusak = 0
    for p in file_list:
        label = kenali(p)
        ukuran = os.path.getsize(p)
        ukuran_asli = nama_ke_ukuran.get(os.path.basename(p))
        if ukuran_asli is None:
            catatan = "ukuran tidak ada pembanding"
        elif ukuran_asli == ukuran:
            catatan = "ukuran cocok"
        else:
            catatan = f"UKURAN BEDA (asli {ukuran_asli})"
            rusak += 1
        if label.startswith("TIDAK DIKENALI"):
            rusak += 1
        print(f"{os.path.basename(p)[:53]:<55}{label:<26}{ukuran:>12}  {catatan}")

    print(f"\n{len(file_list)} file diuji, {rusak} bermasalah")
    if kalau_kosong:
        print("tidak ada file untuk diuji", file=sys.stderr)
        return 1
    return 1 if rusak else 0


if __name__ == "__main__":
    raise SystemExit(main())
