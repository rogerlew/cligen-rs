#!/bin/sh
set -eu
umask 077
set -f
base=$1
run=$2
shift 2
root=$base/$run
[ -d "$base" ] && [ ! -L "$base" ] || exit 64
[ -d "$root" ] && [ ! -L "$root" ] || exit 64
canonical_base=$(cd "$base" && pwd -P)
canonical_root=$(cd "$root" && pwd -P)
[ "$canonical_root" = "$canonical_base/$run" ] || exit 64
marker=$root/.lemhi-toolkit-owner.json
[ -f "$marker" ] && [ ! -L "$marker" ] && \
  [ "$(stat -c %h "$marker" 2>/dev/null || stat -f %l "$marker")" -eq 1 ] || exit 66
[ "$#" -gt 0 ] || exit 64
temporary_root=$root/.evidence-pack.$$
mkdir -- "$temporary_root" || exit 65
[ -d "$temporary_root" ] && [ ! -L "$temporary_root" ] || exit 65
present_list=$temporary_root/present
absent_list=$temporary_root/absent
archive_temporary=$temporary_root/archive
cleanup_lists() {
  rm -f -- "$present_list" "$absent_list" "$archive_temporary"
  rmdir -- "$temporary_root" 2>/dev/null || true
}
trap cleanup_lists EXIT HUP INT TERM
: >"$present_list"
: >"$absent_list"
: >"$archive_temporary"
for item in "$@"; do
  cursor=$root
  old_ifs=$IFS
  IFS=/
  set -- $item
  IFS=$old_ifs
  for component in "$@"; do
    cursor=$cursor/$component
    [ ! -L "$cursor" ] || exit 65
  done
  if [ -e "$root/$item" ]; then
    [ -f "$root/$item" ] && \
      [ "$(stat -c %h "$root/$item" 2>/dev/null || stat -f %l "$root/$item")" -eq 1 ] || exit 65
    printf '%s\n' "$item" >>"$present_list"
  else
    printf '%s\n' "$item" >>"$absent_list"
  fi
done
LC_ALL=C sort -u -o "$present_list" "$present_list"
LC_ALL=C sort -u -o "$absent_list" "$absent_list"
[ -s "$present_list" ] || exit 66
archive=$root/evidence.tar
if [ -e "$archive" ] || [ -L "$archive" ]; then
  [ -f "$archive" ] && [ ! -L "$archive" ] && \
    [ "$(stat -c %h "$archive" 2>/dev/null || stat -f %l "$archive")" -eq 1 ] || exit 65
fi
tar --format=ustar --owner=0 --group=0 --numeric-owner \
  -cf "$archive_temporary" -C "$root" -T "$present_list"
mv -f -- "$archive_temporary" "$archive"
bytes=$(wc -c < "$archive" | tr -d ' ')
sha=$(sha256sum "$archive" | awk '{print $1}')
json_array() {
  awk 'BEGIN { printf "[" } { if (NR > 1) printf ","; printf "\"%s\"", $0 } END { printf "]" }' "$1"
}
printf '{"absent":'
json_array "$absent_list"
printf ',"bytes":%s,"logical_name":"evidence.tar","present":' "$bytes"
json_array "$present_list"
printf ',"sha256":"%s"}\n' "$sha"
