#!/bin/sh
set -eu
umask 077

role=${1:?role required}
candidate=${2:?candidate required}
capacity=${3:?capacity required}
run_root=$PWD
run_id=$(basename "$run_root")
output=$run_root/results/$role
admission=$run_root/admissions/$role.json
asset_manifest=$run_root/asset-manifest.json
target=${TMPDIR:-/tmp}/a10m5r11r1-$role-$SLURM_JOB_ID
mkdir -p -- "$output/seeds" "$target"
chmod 700 "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{"attempt_index":0,"job_id":"%s","node":"%s","role":"%s","run_id":"%s"}\n' \
  "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{print $1}')
device=$(stat -c %d "$target")
uid=$(id -u)

set +e
./supervise-v2.sh "$target" "$marker_sha" "$output/supervisor.json" \
  ./run_temporal_candidate.sh "$target" "$role" "$candidate" "$capacity" "$run_id" \
  "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$marker_sha" "$admission"
status=$?
set -e
cleanup=false
[ ! -e "$target" ] && cleanup=true

if [ ! -f "$output/setup.log" ]; then
  printf '%s\n' 'setup did not start before supervised command failure' \
    >"$output/setup.log"
fi
# The compute image guarantees only Python 3.6 here. This terminal-only
# finalizer deliberately uses no future annotations or Python 3.7+ syntax.
/usr/bin/python3 - "$output" "$status" <<'PY'
import json, os, sys
root, status = sys.argv[1:]
names = (
    'calendar-preflight.json',
    'candidate-summary.json',
    'control-identity.json',
    'streams.json',
    'training.json',
    'seeds/147031.json',
    'seeds/271828.json',
    'seeds/314159.json',
)
for name in names:
    path = os.path.join(root, name)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        value = {
            'absent_reason': 'candidate experiment exited before publication',
            'exit_code': int(status),
            'schema_version': 1,
            'valid': False,
        }
        temporary = path + '.promote'
        with open(temporary, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write('\n')
        os.replace(temporary, path)
setup_path = os.path.join(root, 'setup.json')
if not os.path.exists(setup_path):
    value = {
        'authentication': {},
        'cleanup': {
            'pip_cache_deleted_before_science': False,
            'wheelhouse_deleted_before_science': False,
        },
        'containment': {},
        'execution_identity': {},
        'exit_codes': {'host_python_version': 125, 'pip_check': 125, 'pip_install': 125, 'runtime_version': 125},
        'identities': {},
        'job_local_storage': {},
        'ready_for_science': False,
        'schema_version': 1,
        'stage': 'setup-not-started',
        'valid': False,
    }
    temporary = setup_path + '.promote'
    with open(temporary, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
    os.replace(temporary, setup_path)
PY
/usr/bin/python3 - "$output/evidence.json.part" "$output/evidence.json" \
  "$output/setup.json" "$admission" "$asset_manifest" "$status" "$cleanup" \
  "$target" "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" \
  "$uid" "$device" "$marker_sha" "$candidate" "$capacity" <<'PY'
import hashlib, json, os, re, sys
partial, final, setup_path, admission_path, manifest_path, status, cleanup, target, job, node, role, run_id, uid, device, marker_sha, candidate, capacity = sys.argv[1:]
def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')
def digest(path):
    value = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()
def authenticated(value):
    recorded = value.get('record_sha256')
    semantic = dict(value)
    semantic.pop('record_sha256', None)
    return isinstance(recorded, str) and re.fullmatch(r'[0-9a-f]{64}', recorded) is not None and recorded == hashlib.sha256(canonical(semantic)).hexdigest()
if os.path.exists(partial):
    with open(partial, encoding='utf-8') as stream:
        value = json.load(stream)
else:
    value = {
        'classification': 'a10m5r11-development-only-retained-temporal',
        'gates': {'candidate_evidence_published': False},
        'protected_roles_opened': [],
    }
with open(setup_path, encoding='utf-8') as stream:
    setup = json.load(stream)
with open(manifest_path, encoding='utf-8') as stream:
    manifest = json.load(stream)
admission = {}
if os.path.exists(admission_path):
    with open(admission_path, encoding='utf-8') as stream:
        admission = json.load(stream)
setup_cleanup = setup.get('cleanup', {})
setup_exits = setup.get('exit_codes', {})
setup_execution = setup.get('execution_identity', {})
setup_identities = setup.get('identities', {})
manifest_sha = digest(manifest_path)
admission_file_sha = digest(admission_path) if os.path.exists(admission_path) else None
admission_file_bytes = os.path.getsize(admission_path) if os.path.exists(admission_path) else None
expected_assets = {
    'runtime_archive': manifest.get('assets', {}).get('runtime.tar.gz', {}),
    'wheelhouse_archive': manifest.get('assets', {}).get('wheelhouse.tar', {}),
    'requirements_lock': manifest.get('assets', {}).get('requirements.lock', {}),
}
asset_identity_ok = all(
    setup_identities.get(name, {}).get('bytes') == expected.get('bytes')
    and setup_identities.get(name, {}).get('sha256') == expected.get('sha256')
    for name, expected in expected_assets.items()
) and setup_identities.get('asset_manifest', {}).get('bytes') == os.path.getsize(manifest_path) \
    and setup_identities.get('asset_manifest', {}).get('sha256') == manifest_sha \
    and setup_identities.get('submission_admission', {}).get('bytes') == admission_file_bytes \
    and setup_identities.get('submission_admission', {}).get('sha256') == admission_file_sha
admission_ok = (
    authenticated(admission)
    and admission.get('record_type') == 'a10m5r11r1-submission-admission'
    and admission.get('decision') == 'PASS'
    and admission.get('valid') is True
    and admission.get('run_id') == run_id
    and admission.get('role') == role
    and admission.get('source_commit') == manifest.get('source_commit')
    and admission.get('asset_manifest_sha256') == manifest_sha
    and isinstance(admission.get('gates'), dict)
    and bool(admission['gates'])
    and all(item is True for item in admission['gates'].values())
)
execution_identity_ok = (
    authenticated(setup)
    and setup_execution.get('run_id') == run_id
    and setup_execution.get('role') == role
    and setup_execution.get('job_id') == job
    and setup_execution.get('node') == node
    and setup_execution.get('owner_marker_sha256') == marker_sha
    and setup_execution.get('source_commit') == manifest.get('source_commit')
    and setup_execution.get('asset_manifest_sha256') == manifest_sha
    and setup_execution.get('submission_admission_authenticated') is True
    and setup_execution.get('submission_admission_record_sha256') == admission.get('record_sha256')
)
gates = value.setdefault('gates', {})
gates.update({
    'environment_setup': setup.get('valid') is True and setup_exits.get('pip_install') == 0 and setup_exits.get('pip_check') == 0,
    'job_local_cleanup': cleanup == 'true',
    'portable_runtime_available': setup_exits.get('runtime_version') == 0,
    'setup_diagnostics_published': setup.get('schema_version') == 1 and bool(setup.get('identities')) and bool(setup.get('job_local_storage')),
    'setup_asset_identities_authenticated': asset_identity_ok,
    'setup_execution_identity_authenticated': execution_identity_ok,
    'submission_admission_authenticated': admission_ok,
    'wheelhouse_deleted_before_science': setup_cleanup.get('wheelhouse_deleted_before_science') is True and setup_cleanup.get('pip_cache_deleted_before_science') is True,
})
value.update({
    'candidate_id': candidate,
    'capacity_id': capacity,
    'exit_code': int(status),
    'failure_stage': setup.get('stage'),
    'job_id': job,
    'node': node,
    'role': role,
    'run_id': run_id,
    'operational_identities': {
        'asset_manifest_sha256': manifest_sha,
        'setup_record_sha256': setup.get('record_sha256'),
        'submission_admission_record_sha256': admission.get('record_sha256'),
    },
})
value['valid'] = int(status) == 0 and bool(gates) and all(gates.values())
value['verdict'] = 'PASS' if value['valid'] else 'FAIL'
if cleanup != 'true':
    value['recovery_target'] = {
        'device': int(device), 'job_id': job, 'marker_sha256': marker_sha,
        'node': node, 'target': target, 'uid': int(uid),
    }
temporary = final + '.promote'
with open(temporary, 'w', encoding='utf-8') as stream:
    json.dump(value, stream, indent=2, sort_keys=True)
    stream.write('\n')
os.replace(temporary, final)
if os.path.exists(partial):
    os.unlink(partial)
PY
exit "$status"
