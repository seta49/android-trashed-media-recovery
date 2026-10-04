#!/system/bin/sh
# Kembalikan nama file bertanda sampah sistem:
#   ".trashed-<angka>-NAMAASLI"  ->  "NAMAASLI"
# File TIDAK dipindahkan antar folder; hanya namanya yang dibersihkan.
#
# Pemakaian di komputer:
#   adb push restore.sh /data/local/tmp/restore.sh
#   adb shell sh /data/local/tmp/restore.sh
#   adb pull /data/local/tmp/rename_log.txt ./rename_log.txt
#
# Daftar file diambil dari /data/local/tmp/trashed_list.txt
# (dihasilkan oleh inventory.sh — jalankan itu lebih dulu).

ROOT=/storage/emulated/0
L=/data/local/tmp/trashed_list.txt
LOG=/data/local/tmp/rename_log.txt

: > "$LOG"
ok=0; skip=0; fail=0

while IFS= read -r p; do
  d=${p%/*}
  b=${p##*/}
  n=${b#.trashed-}
  n=${n#*-}
  if [ -z "$n" ]; then
    printf 'SKIP-EMPTY|%s\n' "$p" >> "$LOG"; skip=$((skip+1)); continue
  fi
  if [ -e "$d/$n" ]; then
    printf 'EXISTS|%s|%s\n' "$p" "$d/$n" >> "$LOG"; skip=$((skip+1)); continue
  fi
  if mv "$p" "$d/$n" 2>>"$LOG"; then
    printf 'OK|%s|%s\n' "$p" "$d/$n" >> "$LOG"; ok=$((ok+1))
  else
    printf 'FAIL|%s\n' "$p" >> "$LOG"; fail=$((fail+1))
  fi
done < "$L"

echo "OK=$ok SKIP=$skip FAIL=$fail"
echo "REMAINING_TRASHED $(find $ROOT -name '.trashed-*' -type f 2>/dev/null | wc -l)"
