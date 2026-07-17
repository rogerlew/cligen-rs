#!/bin/sh
set -eu
base=$1
run=$2
logical=$3
expected_bytes=$4
expected_sha=$5
root=$base/$run
[ -f "$root/.lemhi-toolkit-owner.json" ] && [ ! -L "$root" ] || exit 64
partial=$root/$logical.part
final=$root/$logical
[ -f "$partial" ] && [ ! -L "$partial" ] || exit 66
actual_bytes=$(wc -c < "$partial" | tr -d ' ')
actual_sha=$(sha256sum "$partial" | awk '{print $1}')
[ "$actual_bytes" = "$expected_bytes" ] && [ "$actual_sha" = "$expected_sha" ] || exit 65
[ ! -e "$final" ] || exit 73
mv -- "$partial" "$final"
