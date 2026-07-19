#!/bin/sh
set -eu
umask 077

role=interconnect-diagnostic
run_root=$PWD
run_id=$(basename "$run_root")
output=$run_root/results/$role
target=${TMPDIR:-/tmp}/a10m5o2d1-$SLURM_JOB_ID
mkdir -p -- "$output" "$target" "$run_root/slurm"
: >"$run_root/slurm/toolkit-recovery.0.out"
: >"$run_root/slurm/toolkit-recovery.0.err"
chmod 700 "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{"attempt_index":0,"job_id":"%s","node":"%s","role":"%s","run_id":"%s"}\n' \
  "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{print $1}')
device=$(stat -c %d "$target")
uid=$(id -u)
started=$(date +%s)
set +e
./supervise-v2.sh "$target" "$marker_sha" "$output/supervisor.json" \
  ./run-diagnostic.sh "$target" "$output"
status=$?
set -e
finished=$(date +%s)
cleanup=false
[ ! -e "$target" ] && cleanup=true
/usr/bin/python3 - "$output/evidence.json.part" "$output/evidence.json" \
  "$status" "$cleanup" "$target" "$SLURM_JOB_ID" "$SLURMD_NODENAME" \
  "$role" "$run_id" "$uid" "$device" "$marker_sha" "$started" "$finished" <<'PY'
import json, os, sys
partial, final, status, cleanup, target, job, node, role, run_id, uid, device, marker_sha, started, finished = sys.argv[1:]
if os.path.exists(partial):
    with open(partial, encoding='utf-8') as stream:
        value=json.load(stream)
else:
    value={'classification':'a10m5o2d1-missing-primary-evidence','gates':{'primary_evidence_written':False}}
gates=value.setdefault('gates',{})
gates['job_local_cleanup']=cleanup=='true'
gates['launcher_zero']=int(status)==0
value.update({'application_status':int(status),'elapsed_wall_seconds':int(finished)-int(started),'job_id':job,'node':node,'role':role,'run_id':run_id})
value['valid']=int(status)==0 and bool(gates) and all(gates.values())
value['verdict']='PASS' if value['valid'] else 'FAIL'
if cleanup!='true':
    value['recovery_target']={'device':int(device),'job_id':job,'marker_sha256':marker_sha,'node':node,'target':target,'uid':int(uid)}
temporary=final+'.promote'
with open(temporary,'w',encoding='utf-8') as stream:
    json.dump(value,stream,indent=2,sort_keys=True); stream.write('\n')
os.replace(temporary,final)
if os.path.exists(partial): os.unlink(partial)
PY
exit "$status"
