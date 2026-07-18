#!/bin/sh
#SBATCH --export=NONE
set -eu
umask 077

PATH=/usr/bin:/bin
export PATH
run_root=$PWD
evidence=$run_root/evidence.json
application_status=$run_root/supervisor-application.json
signal_status=$run_root/supervisor-signal.json
uid=$(id -u)
base=/tmp/lemhi-toolkit-$uid
claim=a10-canonical-v2-$SLURM_JOB_ID
attempt_root=$base/$claim

fail_receipt()
{
  status=$?
  trap - EXIT
  if [ ! -f "$evidence" ]; then
    printf '{"configuration_semantic_sha256":"5addee9c5db3592ee247eab2b5266ed5567fd9aaf24ed78dcb321ecbb001e22d","exit_code":%s,"gates":{"job_completed":false,"job_local_cleanup":false},"verdict":"FAIL"}\n' "$status" >"$evidence.part"
    mv -- "$evidence.part" "$evidence"
  fi
  exit "$status"
}
trap fail_receipt EXIT

test -z "${PYTHONPATH+x}" -a -z "${PYTHONHOME+x}" -a -z "${LD_LIBRARY_PATH+x}"
mkdir -p -m 700 -- "$base"
test "$(stat -c %u "$base")" = "$uid"
case "$(stat -c %a "$base")" in 700) ;; *) exit 72 ;; esac

required_bytes=15000000000
minimum_free_bytes=1073741824
free_kib=$(df -Pk "$base" | awk 'NR == 2 {print $4}')
test "$((free_kib * 1024))" -ge "$((required_bytes + minimum_free_bytes))"
free_inodes=$(df -Pi "$base" | awk 'NR == 2 {print $4}')
test "$free_inodes" -ge 200000

mkdir -m 700 -- "$attempt_root"
marker=$attempt_root/.lemhi-toolkit-owner.json
printf '{"authority_id":"a10-canonical-v2-smoke-authority","attempt":0,"base":"%s","job_id":"%s","node":"%s","package_id":"a10-lemhi-canonical-v2-smoke","run_id":"a10-canonical-v2-smoke-r1","target":"%s","uid":%s}\n' \
  "$base" "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$attempt_root" "$uid" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{print $1}')

set +e
"$run_root/supervise-v2.sh" "$attempt_root" "$marker_sha" "$application_status" \
  "$run_root/smoke-app.sh" "$attempt_root" "$run_root"
application_exit=$?
set -e
test "$application_exit" -eq 0
test ! -e "$attempt_root"

signal_root=$base/$claim-signal
mkdir -m 700 -- "$signal_root"
signal_marker=$signal_root/.lemhi-toolkit-owner.json
printf '{"attempt":"signal","job_id":"%s","run_id":"a10-canonical-v2-smoke-r1","target":"%s","uid":%s}\n' \
  "$SLURM_JOB_ID" "$signal_root" "$uid" >"$signal_marker"
signal_sha=$(sha256sum "$signal_marker" | awk '{print $1}')
set +e
"$run_root/supervise-v2.sh" "$signal_root" "$signal_sha" "$signal_status" \
  /bin/sh -c 'trap "exit 23" TERM; while :; do sleep 1; done' &
supervisor_pid=$!
sleep 1
kill -TERM "$supervisor_pid"
wait "$supervisor_pid"
signal_exit=$?
set -e
test "$signal_exit" -eq 23 -o "$signal_exit" -eq 143
test ! -e "$signal_root"

runtime_python=$run_root/runtime/environment/bin/python
"$runtime_python" - "$run_root/app-evidence.json" "$evidence" "$application_status" "$signal_status" <<'PY'
import json, os, sys
app, final, application_status, signal_status = sys.argv[1:]
with open(app, encoding="utf-8") as stream:
    value = json.load(stream)
with open(application_status, encoding="utf-8") as stream:
    application = json.load(stream)
with open(signal_status, encoding="utf-8") as stream:
    signal = json.load(stream)
value["gates"].update({
    "application_supervisor": application.get("application_exit") == 0,
    "catchable_signal_supervisor": signal.get("application_exit") in (23, 143),
    "job_local_capacity": True,
    "job_local_cleanup": True,
    "job_completed": True,
})
value["verdict"] = "PASS" if all(value["gates"].values()) else "FAIL"
temporary = final + ".part"
with open(temporary, "w", encoding="utf-8") as stream:
    json.dump(value, stream, sort_keys=True); stream.write("\n")
os.replace(temporary, final)
if value["verdict"] != "PASS":
    raise SystemExit(1)
PY
rm -f -- "$run_root/app-evidence.json"
rmdir -- "$base"
trap - EXIT
printf '%s\n' A10-LEMHI-CANONICAL-V2-SMOKE-PASS
