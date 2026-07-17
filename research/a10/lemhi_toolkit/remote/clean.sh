#!/bin/sh
set -eu
base=$1
relative=$2
run_id=$3
package_id=$4
source_commit=$5
plan_sha=$6
case "$base" in /*) ;; *) exit 64 ;; esac
case "$relative" in ''|/*|*'..'*|*'//'*) exit 64 ;; esac
target=$base/$relative
[ "$target" != / ] && [ "$target" != "$base" ] && [ -d "$target" ] && [ ! -L "$target" ] || exit 64
canonical_base=$(cd "$base" && pwd -P)
canonical_target=$(cd "$target" && pwd -P)
[ "$canonical_target" = "$canonical_base/$relative" ] || exit 64
marker=$target/.lemhi-toolkit-owner.json
[ -f "$marker" ] && [ ! -L "$marker" ] || exit 64
expected=$(printf '{"canonical_root":"%s","package_id":"%s","plan_sha256":"%s","remote_run_root":"%s","run_id":"%s","source_commit":"%s"}' "$canonical_target" "$package_id" "$plan_sha" "$relative" "$run_id" "$source_commit")
actual=$(tr -d '\n' < "$marker")
[ "$actual" = "$expected" ] || exit 65
actual_again=$(tr -d '\n' < "$marker")
[ "$actual_again" = "$expected" ] || exit 65
canonical_again=$(cd "$target" && pwd -P)
[ "$canonical_again" = "$canonical_target" ] || exit 65
rm -rf -- "$target"
[ ! -e "$target" ] || exit 74
printf 'REMOTE_ABSENT\n'
