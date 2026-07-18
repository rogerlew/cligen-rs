#!/bin/sh
set -eu

target=$1
expected_uid=$2
expected_device=$3
marker_sha256=$4
receipt=$5
original_job_id=$6
expected_node=$7
target_sha256=$8

case "$target" in /*) ;; *) exit 64 ;; esac
case "$receipt" in ''|/*|*..*|*//*|*'|'*) exit 64 ;; esac
case "$original_job_id" in ''|*[!0-9]*) exit 64 ;; esac
[ "$(hostname -s)" = "$expected_node" ] || exit 65
[ "$(printf '%s' "$target" | sha256sum | awk '{print $1}')" = "$target_sha256" ] || exit 65
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
temporary=${receipt}.part.$$
umask 077
printf '{"gates":{"job_local_cleanup":true,"marker_revalidated":true,"original_job_settled":true,"recovery_exact_node":true},"recovery_result":{"node":"%s","original_job_id":"%s","target_sha256":"%s"}}\n' \
  "$expected_node" "$original_job_id" "$target_sha256" > "$temporary"
mv -- "$temporary" "$receipt"
printf '%s\n' JOB_LOCAL_ABSENT
