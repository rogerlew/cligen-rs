#!/bin/sh
set -eu
umask 077

target=/tmp/a10m5r12-control-materialization-1058096
expected_node=node03
expected_uid=10102
expected_device=64769
expected_marker_sha256=836549c3e3312f57ca9c08c6c24b4add5c9b61caec2a4d1ec0563870708e26e7
expected_target_sha256=abca5715cfdac0df808d1f24cf601d101979bc18a336b4149e2356cf1775147d

[ "$(hostname -s)" = "$expected_node" ] || exit 65
[ "$(printf '%s' "$target" | sha256sum | awk '{print $1}')" = "$expected_target_sha256" ] || exit 65
if [ ! -e "$target" ]; then
  printf '{"gates":{"exact_node":true,"job_local_cleanup":true,"original_job_settled":true},"job_id":"1058096","node":"node03","result":"already-absent","target_sha256":"%s"}\n' \
    "$expected_target_sha256"
  exit 0
fi

[ -d "$target" ] && [ ! -L "$target" ] || exit 64
canonical=$(cd "$target" && pwd -P)
[ "$canonical" = "$target" ] || exit 65
[ "$(stat -c %u "$target")" = "$expected_uid" ] || exit 65
[ "$(stat -c %d "$target")" = "$expected_device" ] || exit 65
marker=$target/.lemhi-toolkit-owner.json
[ -f "$marker" ] && [ ! -L "$marker" ] || exit 65
[ "$(sha256sum "$marker" | awk '{print $1}')" = "$expected_marker_sha256" ] || exit 65
[ "$(cd "$target" && pwd -P)" = "$canonical" ] || exit 65
[ "$(sha256sum "$marker" | awk '{print $1}')" = "$expected_marker_sha256" ] || exit 65
rm -rf -- "$target"
[ ! -e "$target" ] || exit 74
printf '{"gates":{"exact_node":true,"job_local_cleanup":true,"marker_revalidated":true,"original_job_settled":true},"job_id":"1058096","node":"node03","result":"validated-delete","target_sha256":"%s"}\n' \
  "$expected_target_sha256"
