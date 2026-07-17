#!/bin/sh
set -eu
base=$1
run=$2
logical=$3
expected_bytes=$4
expected_sha=$5
root=$base/$run
file=$root/$logical
[ -f "$root/.lemhi-toolkit-owner.json" ] && [ -f "$file" ] && [ ! -L "$file" ] || exit 66
actual_bytes=$(wc -c < "$file" | tr -d ' ')
actual_sha=$(sha256sum "$file" | awk '{print $1}')
[ "$actual_bytes" = "$expected_bytes" ] && [ "$actual_sha" = "$expected_sha" ]
