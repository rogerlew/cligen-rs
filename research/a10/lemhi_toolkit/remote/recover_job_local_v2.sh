#!/bin/sh
set -eu

target=$1
expected_uid=$2
expected_device=$3
marker_sha256=$4

case "$target" in /*) ;; *) exit 64 ;; esac
[ "$target" != / ] && [ -d "$target" ] && [ ! -L "$target" ] || exit 64
canonical=$(cd "$target" && pwd -P)
[ "$canonical" = "$target" ] || exit 65
[ "$(stat -c %u "$target")" = "$expected_uid" ] || exit 65
[ "$(stat -c %d "$target")" = "$expected_device" ] || exit 65
marker=$target/.lemhi-toolkit-owner.json
[ -f "$marker" ] && [ ! -L "$marker" ] || exit 65
[ "$(sha256sum "$marker" | awk '{print $1}')" = "$marker_sha256" ] || exit 65

# The controller validates settled squeue/sacct state and exact-node placement
# before dispatching this script. Revalidate every local identity immediately
# before the one bounded deletion.
[ "$(cd "$target" && pwd -P)" = "$canonical" ] || exit 65
[ "$(sha256sum "$marker" | awk '{print $1}')" = "$marker_sha256" ] || exit 65
rm -rf -- "$target"
[ ! -e "$target" ] || exit 74
printf '%s\n' JOB_LOCAL_ABSENT
