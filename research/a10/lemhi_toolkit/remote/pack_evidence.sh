#!/bin/sh
set -eu
base=$1
run=$2
shift 2
root=$base/$run
[ -f "$root/.lemhi-toolkit-owner.json" ] || exit 66
[ "$#" -gt 0 ] || exit 64
archive=$root/evidence.tar
tar --format=ustar --owner=0 --group=0 --numeric-owner -cf "$archive.part" -C "$root" -- "$@"
mv -- "$archive.part" "$archive"
bytes=$(wc -c < "$archive" | tr -d ' ')
sha=$(sha256sum "$archive" | awk '{print $1}')
printf '{"bytes":%s,"logical_name":"evidence.tar","sha256":"%s"}\n' "$bytes" "$sha"
