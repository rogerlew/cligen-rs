#!/bin/sh
set -eu

uid=$(/usr/bin/id -u)
node=${SLURMD_NODENAME:?}
job_id=${SLURM_JOB_ID:?}
target=/tmp/lemhi-toolkit-$uid/a10m4o2-live-failure-0-$job_id
/bin/mkdir -p -- "/tmp/lemhi-toolkit-$uid" "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{"attempt_index":0,"job_id":"%s","node":"%s","role":"failure","run_id":"a10m4o2-live"}\n' \
  "$job_id" "$node" > "$marker"
device=$(/usr/bin/stat -c %d "$target")
marker_sha256=$(/usr/bin/sha256sum "$marker" | /usr/bin/awk '{print $1}')
temporary=failure.json.part.$$
umask 077
printf '{"gates":{"job_local_cleanup":false,"registered_failure":true},"recovery_target":{"device":%s,"job_id":"%s","marker_sha256":"%s","node":"%s","target":"%s","uid":%s}}\n' \
  "$device" "$job_id" "$marker_sha256" "$node" "$target" "$uid" > "$temporary"
/bin/mv -- "$temporary" failure.json
exit 7
