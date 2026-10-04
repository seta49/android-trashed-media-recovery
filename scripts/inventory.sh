#!/system/bin/sh
# Inventaris file bertanda sampah sistem (MediaStore) di penyimpanan internal.
#
# Pemakaian di komputer:
#   adb push inventory.sh /data/local/tmp/inventory.sh
#   adb shell sh /data/local/tmp/inventory.sh > inv_raw.txt
#
# Keluaran: dua baris ringkasan lalu daftar "UKURAN|MTIME|PATH" di antara penanda.
# Catatan penting: JANGAN pakai /sdcard — symlink, dan toybox find tidak
# menelusuri argumen awal berupa symlink sehingga hasilnya kosong.

ROOT=/storage/emulated/0
L=/data/local/tmp/trashed_list.txt
P=/data/local/tmp/pending_list.txt

find $ROOT -name '.trashed-*' -type f 2>/dev/null > "$L"
find $ROOT -name '.pending-*' -type f 2>/dev/null > "$P"

echo "TRASHED_COUNT $(wc -l < "$L")"
echo "PENDING_COUNT $(wc -l < "$P")"
echo "--- BEGIN ---"
while IFS= read -r p; do
  st=$(stat -c '%s|%Y' "$p" 2>/dev/null)
  printf '%s|%s\n' "${st:-0|0}" "$p"
done < "$L"
echo "--- END ---"
