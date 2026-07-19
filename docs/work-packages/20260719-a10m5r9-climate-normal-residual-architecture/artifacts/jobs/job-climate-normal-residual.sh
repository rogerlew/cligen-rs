#!/bin/sh
set -eu
umask 077
role=climate-normal-residual
run_root=$PWD
run_id=$(basename "$run_root")
output=$run_root/results/$role
target=${TMPDIR:-/tmp}/a10m5r9-$role-$SLURM_JOB_ID
mkdir -p -- "$output" "$target"
chmod 700 "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{"attempt_index":0,"job_id":"%s","node":"%s","role":"%s","run_id":"%s"}\n' \
  "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{print $1}')
device=$(stat -c %d "$target")
uid=$(id -u)
set +e
./supervise-v2.sh "$target" "$marker_sha" "$output/supervisor.json" ./run_experiment.sh "$target"
status=$?
set -e
cleanup=false
[ ! -e "$target" ] && cleanup=true
/usr/bin/python3 - "$output" "$status" <<'PY'
import json, os, sys
root, status = sys.argv[1:]
for name in ('baseline-training.json', 'calendar-preflight.json', 'comparison.json', 'control-identity.json', 'decision.json', 'residual-training.json'):
    path = os.path.join(root, name)
    if not os.path.exists(path):
        value = {'absent_reason': 'experiment exited before publication', 'exit_code': int(status), 'schema_version': 1, 'valid': False}
        temporary = path + '.promote'
        with open(temporary, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
        os.replace(temporary, path)
PY
/usr/bin/python3 - "$output/evidence.json.part" "$output/evidence.json" "$status" "$cleanup" "$target" "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" "$uid" "$device" "$marker_sha" <<'PY'
import json, os, sys
partial, final, status, cleanup, target, job, node, role, run_id, uid, device, marker_sha = sys.argv[1:]
if os.path.exists(partial):
    with open(partial, encoding='utf-8') as stream: value = json.load(stream)
else:
    value = {'classification': 'a10m5r9-development-only-climate-normal-residual-architecture', 'gates': {'experiment_published': False}, 'protected_roles_opened': []}
value.setdefault('gates', {})['job_local_cleanup'] = cleanup == 'true'
value['exit_code'] = int(status)
value['valid'] = int(status) == 0 and bool(value['gates']) and all(value['gates'].values())
value['verdict'] = 'PASS' if value['valid'] else 'FAIL'
if cleanup != 'true':
    value['recovery_target'] = {'device': int(device), 'job_id': job, 'marker_sha256': marker_sha, 'node': node, 'target': target, 'uid': int(uid)}
temporary = final + '.promote'
with open(temporary, 'w', encoding='utf-8') as stream:
    json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
os.replace(temporary, final)
if os.path.exists(partial): os.unlink(partial)
PY
exit "$status"
