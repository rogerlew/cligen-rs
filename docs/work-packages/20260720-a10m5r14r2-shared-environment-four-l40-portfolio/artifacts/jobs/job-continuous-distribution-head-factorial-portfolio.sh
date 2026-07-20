#!/bin/sh
#SBATCH --nodelist=node03
#SBATCH --nodes=1
set -eu
umask 077

role=continuous-distribution-head-factorial-portfolio
run_root=$PWD
run_id=$(basename "$run_root")
output=$run_root/results/$role
admission=$run_root/admissions/$role.json
target=${TMPDIR:-/tmp}/a10m5r14r2-portfolio-$SLURM_JOB_ID
mkdir -p -- "$output" "$target" "$run_root/slurm"
chmod 700 "$target"
marker=$target/.lemhi-toolkit-owner.json
printf '{"attempt_index":0,"job_id":"%s","node":"%s","role":"%s","run_id":"%s"}\n' \
  "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$role" "$run_id" >"$marker"
marker_sha=$(sha256sum "$marker" | awk '{print $1}')
device=$(stat -c %d "$target")
uid=$(id -u)

set +e
./supervise-v2.sh "$target" "$marker_sha" "$output/supervisor.json" \
  ./run_portfolio.sh "$target" "$run_id" "$SLURM_JOB_ID" \
  "$SLURMD_NODENAME" "$marker_sha" "$admission"
status=$?
set -e
cleanup=false
[ ! -e "$target" ] && cleanup=true

# Host-Python finalization is intentionally compatible with the compute image's
# older interpreter and retains all role directories on every terminal path.
/usr/bin/python3 - "$run_root" "$output" "$status" "$cleanup" "$target" \
  "$SLURM_JOB_ID" "$SLURMD_NODENAME" "$run_id" "$uid" "$device" "$marker_sha" <<'PY'
import hashlib, json, os, sys
run_root, output, status, cleanup, target, job, node, run_id, uid, device, marker_sha = sys.argv[1:]
roles = (
    'continuous-location-ou-k2',
    'continuous-location-ou-smooth-climatology-k2',
    'continuous-location-scale-ou-k2',
    'continuous-location-scale-ou-smooth-climatology-k2',
)
for role in roles:
    root = os.path.join(run_root, 'results', role)
    os.makedirs(root, exist_ok=True)
    for name in ('process.json', 'evidence.json'):
        path = os.path.join(root, name)
        if not os.path.exists(path):
            value = {'absent_reason': 'portfolio exited before role publication', 'exit_code': int(status), 'role': role, 'schema_version': 1, 'valid': False}
            temporary = path + '.promote'
            with open(temporary, 'w', encoding='utf-8') as stream:
                json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
            os.replace(temporary, path)
def load(name):
    path = os.path.join(output, name)
    if not os.path.exists(path): return {}
    with open(path, encoding='utf-8') as stream: return json.load(stream)
def authenticated(value):
    semantic = dict(value)
    recorded = semantic.pop('record_sha256', None)
    return recorded == hashlib.sha256(json.dumps(semantic, separators=(',', ':'), sort_keys=True).encode()).hexdigest()
setup, launcher = load('setup.json'), load('launcher.json')
cleanup_permissions = load('cleanup-permissions.json')
manifest_path = os.path.join(run_root, 'asset-manifest.json')
admission_path = os.path.join(run_root, 'admissions', 'continuous-distribution-head-factorial-portfolio.json')
control_path = os.path.join(run_root, 'results', 'control-materialization', 'evidence.json')
with open(manifest_path, encoding='utf-8') as stream: manifest = json.load(stream)
with open(admission_path, encoding='utf-8') as stream: admission = json.load(stream)
with open(control_path, encoding='utf-8') as stream: control = json.load(stream)
manifest_sha = hashlib.sha256(open(manifest_path, 'rb').read()).hexdigest()
admission_sha = hashlib.sha256(open(admission_path, 'rb').read()).hexdigest()
control_sha = hashlib.sha256(open(control_path, 'rb').read()).hexdigest()
execution = setup.get('execution_identity', {})
identities = setup.get('identities', {})
admission_ok = (
    authenticated(admission)
    and admission.get('record_type') == 'a10m5r14r2-submission-admission'
    and admission.get('run_id') == run_id
    and admission.get('role') == 'continuous-distribution-head-factorial-portfolio'
    and admission.get('source_commit') == manifest.get('source_commit')
    and admission.get('asset_manifest_sha256') == manifest_sha
    and admission.get('valid') is True
    and admission.get('decision') == 'PASS'
    and bool(admission.get('gates')) and all(admission['gates'].values())
    and admission.get('input_identities', {}).get('control_gate_receipt_sha256') == control_sha
)
setup_ok = (
    authenticated(setup) and setup.get('valid') is True
    and setup.get('ready_for_science') is True
    and bool(setup.get('authentication')) and all(setup['authentication'].values())
    and execution.get('asset_manifest_sha256') == manifest_sha
    and execution.get('run_id') == run_id
    and execution.get('role') == 'continuous-distribution-head-factorial-portfolio'
    and execution.get('job_id') == job and execution.get('node') == node
    and execution.get('source_commit') == manifest.get('source_commit')
    and execution.get('submission_admission_record_sha256') == admission.get('record_sha256')
    and identities.get('submission_admission', {}).get('sha256') == admission_sha
)
launcher_ok = (
    authenticated(launcher) and launcher.get('valid') is True
    and launcher.get('protected_roles_opened') == []
    and launcher.get('role') == 'continuous-distribution-head-factorial-portfolio'
    and launcher.get('publication_identity', {}).get('asset_manifest_sha256') == manifest_sha
    and launcher.get('publication_identity', {}).get('run_id') == run_id
    and launcher.get('publication_identity', {}).get('source_commit') == manifest.get('source_commit')
    and launcher.get('publication_identity', {}).get('submission_admission_record_sha256') == admission.get('record_sha256')
)
child_records_ok = True
for child_role in roles:
    evidence_path = os.path.join(run_root, 'results', child_role, 'evidence.json')
    with open(evidence_path, encoding='utf-8') as stream: child_evidence = json.load(stream)
    child_evidence.pop('record_sha256', None)
    child_evidence.setdefault('gates', {})['job_local_cleanup'] = cleanup == 'true'
    child_evidence['gates']['submission_admission_authenticated'] = admission_ok
    child_evidence['run_id'] = run_id
    child_evidence['source_commit'] = manifest.get('source_commit')
    child_evidence['valid'] = (
        child_evidence.get('exit_code') == 0 and bool(child_evidence['gates'])
        and all(child_evidence['gates'].values())
    )
    child_evidence['verdict'] = 'PASS' if child_evidence['valid'] else 'FAIL'
    child_evidence['record_sha256'] = hashlib.sha256(json.dumps(child_evidence, separators=(',', ':'), sort_keys=True).encode()).hexdigest()
    temporary = evidence_path + '.promote'
    with open(temporary, 'w', encoding='utf-8') as stream:
        json.dump(child_evidence, stream, indent=2, sort_keys=True); stream.write('\n')
    os.replace(temporary, evidence_path)
    child_admission = {
        'admission_sequence': {'kind': 'portfolio-child', 'portfolio_role': 'continuous-distribution-head-factorial-portfolio'},
        'asset_manifest_sha256': manifest_sha,
        'attempt_index': 0,
        'gates': {
            'parent_portfolio_admission_authenticated': admission_ok,
            'portfolio_launcher_authenticated': launcher_ok,
            'shared_job_local_cleanup': cleanup == 'true',
        },
        'input_identities': {
            'parent_portfolio_admission_record_sha256': admission.get('record_sha256'),
            'portfolio_launcher_record_sha256': launcher.get('record_sha256'),
        },
        'package_id': '20260720-a10m5r14r2-shared-environment-four-l40-portfolio',
        'record_type': 'a10m5r14r2-submission-admission',
        'role': child_role,
        'run_id': run_id,
        'schema_version': 'lemhi-toolkit-record-2',
        'source_commit': manifest.get('source_commit'),
    }
    child_admission['valid'] = bool(child_admission['gates']) and all(child_admission['gates'].values())
    child_admission['decision'] = 'PASS' if child_admission['valid'] else 'FAIL'
    child_admission['record_sha256'] = hashlib.sha256(json.dumps(child_admission, separators=(',', ':'), sort_keys=True).encode()).hexdigest()
    child_records_ok = child_records_ok and authenticated(child_evidence) and authenticated(child_admission) and child_evidence['valid'] is True and child_admission['valid'] is True
    child_path = os.path.join(run_root, 'admissions', child_role + '.json')
    os.makedirs(os.path.dirname(child_path), exist_ok=True)
    temporary = child_path + '.promote'
    with open(temporary, 'w', encoding='utf-8') as stream:
        json.dump(child_admission, stream, indent=2, sort_keys=True); stream.write('\n')
    os.replace(temporary, child_path)
gates = {
    'all_role_directories_retained': all(os.path.isdir(os.path.join(run_root, 'results', role)) for role in roles),
    'all_role_records_authenticated': child_records_ok,
    'cleanup_permissions_restored': cleanup_permissions.get('valid') is True,
    'control_evidence_bound': control.get('valid') is True and control_sha == admission.get('input_identities', {}).get('control_gate_receipt_sha256'),
    'job_local_cleanup': cleanup == 'true',
    'launcher_authenticated': launcher_ok,
    'portfolio_admission_authenticated': admission_ok,
    'shared_environment_setup_authenticated': setup_ok,
}
value = {
    'exit_code': int(status), 'gates': gates, 'job_id': job, 'node': node,
    'protected_roles_opened': [], 'role': 'continuous-distribution-head-factorial-portfolio',
    'run_id': run_id, 'schema_version': 1, 'source_commit': manifest.get('source_commit'),
    'asset_manifest_sha256': manifest_sha,
    'submission_admission_record_sha256': admission.get('record_sha256'),
}
value['valid'] = int(status) == 0 and all(gates.values())
value['verdict'] = 'PASS' if value['valid'] else 'FAIL'
if cleanup != 'true':
    value['recovery_target'] = {'device': int(device), 'job_id': job, 'marker_sha256': marker_sha, 'node': node, 'target': target, 'uid': int(uid)}
value['record_sha256'] = hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()
temporary = os.path.join(output, 'evidence.json.promote')
with open(temporary, 'w', encoding='utf-8') as stream:
    json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')
os.replace(temporary, os.path.join(output, 'evidence.json'))
PY
exit "$status"
