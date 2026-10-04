#!/usr/bin/env python3
"""Bedah daftar file sampah MediaStore: hitung sebaran folder, ukuran, dan waktu.

Masukan: berkas hasil `inventory.sh` (baris `UKURAN|MTIME|PATH`).

Pemakaian:
    python decode-expiry.py inv_raw.txt

Yang ditampilkan: jumlah dan total ukuran, sebaran per folder, sebaran jenis file,
serta perkiraan waktu file dipindahkan ke sampah dan kapan kedaluarsa
(berdasarkan AOSP: dateExpires = waktu_dipindahkan + 30 hari).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import os
import re

WIB = dt.timezone(dt.timedelta(hours=7))
POLA = re.compile(r"^\.(trashed|pending)-(\d+)-(.+)$")


def wib(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, WIB).strftime("%d %b %Y %H:%M")


def baca(path: str) -> list[tuple[int, int, str]]:
    baris = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            bagian = line.rstrip("\n").split("|", 2)
            if len(bagian) == 3 and bagian[0].isdigit() and bagian[1].isdigit():
                baris.append((int(bagian[0]), int(bagian[1]), bagian[2]))
    return baris


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inventaris", help="berkas hasil inventory.sh")
    ap.add_argument("--root", default="/storage/emulated/0", help="akar yang dibuang dari label folder")
    args = ap.parse_args()

    data = baca(args.inventaris)
    if not data:
        print("tidak ada baris valid di", args.inventaris)
        return 1

    total = sum(d[0] for d in data)
    print(f"jumlah file sampah : {len(data)}")
    print(f"total ukuran       : {total / 1024 ** 3:.2f} GB")

    folder = collections.Counter()
    jenis = collections.Counter()
    for size, _, path in data:
        label = os.path.dirname(path).replace(args.root + "/", "")
        folder[label or "(akar)"] += 1
        jenis[os.path.splitext(path)[1].lower() or "(tanpa ekstensi)"] += 1

    print("\n-- per folder --")
    for f, c in folder.most_common():
        print(f"{c:>7}  {f}")

    print("\n-- per jenis file --")
    for e, c in jenis.most_common():
        print(f"{c:>7}  {e}")

    expiry, tanpa_pola = [], []
    for _, _, path in data:
        m = POLA.match(path.rsplit("/", 1)[-1])
        if m:
            expiry.append((int(m.group(2)), m.group(1), path))
        else:
            tanpa_pola.append(path)

    if expiry:
        expiry.sort()
        print("\n-- jendela waktu --")
        print("kedaluarsa tercepat :", wib(expiry[0][0]))
        print("kedaluarsa terakhir :", wib(expiry[-1][0]))
        tanggal = sorted({(e - 30 * 86400) // 86400 for e, _, _ in expiry})
        print("perkiraan tanggal dipindahkan ke sampah: " + ", ".join(wib(t * 86400)[:11] for t in tanggal))
        print("jumlah file sudah lewat batas 30 hari:",
              sum(1 for e, _, _ in expiry if e < dt.datetime.now(dt.timezone.utc).timestamp()))
    if tanpa_pola:
        print(f"\n{len(tanpa_pola)} nama file tidak mengikuti pola trashed/pending (perlu dicek manual)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
