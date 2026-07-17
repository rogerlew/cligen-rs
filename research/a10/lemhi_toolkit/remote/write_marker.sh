#!/bin/sh
set -eu
base=$1
relative=$2
run_id=$3
package_id=$4
source_commit=$5
plan_sha=$6
target=$base/$relative
[ -d "$target" ] && [ ! -L "$target" ] || exit 64
canonical_root=$(cd "$target" && pwd -P)
marker=$target/.lemhi-toolkit-owner.json
partial=$marker.part
(set -C; umask 077; : > "$partial") || exit 73
printf '{"canonical_root":"%s","package_id":"%s","plan_sha256":"%s","remote_run_root":"%s","run_id":"%s","source_commit":"%s"}\n' \
  "$canonical_root" "$package_id" "$plan_sha" "$relative" "$run_id" "$source_commit" > "$partial"
mv -- "$partial" "$marker"
