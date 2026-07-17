#!/bin/bash

set -euo pipefail
umask 077

program=${0##*/}
package_rel=docs/work-packages/20260716-a10m2d2-rmm-lemhi-scp-characterization
output_dir=
logical_ceiling=5368709120
command_timeout=1800

fail() {
    printf '%s: %s\n' "$program" "$*" >&2
    exit 1
}

usage() {
    printf 'Usage: %s [--output NEW_DIRECTORY]\n' "$program"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --output)
            [ "$#" -ge 2 ] || fail "--output requires a value"
            output_dir=$2
            shift 2
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            fail "unknown argument: $1"
            ;;
    esac
done

for tool in git ssh scp python3 shasum dd split tar stat awk cmp sed; do
    command -v "$tool" >/dev/null 2>&1 || fail "missing tool: $tool"
done
[ "$(uname -s)" = Darwin ] || fail "stage 1 must run on rmm/macOS"

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
[ -z "$(git status --porcelain)" ] || fail "working tree is not clean"
source_commit=$(git rev-parse HEAD)
[ "${#source_commit}" -eq 40 ] || fail "unexpected source commit length"
case "$source_commit" in *[!0-9a-f]*) fail "unexpected source commit" ;; esac
source_short=${source_commit:0:12}
remote_run="a10m2d2-${source_short}"
case "$remote_run" in
    a10m2d2-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
    *) fail "unsafe remote run name" ;;
esac

package_root="$repo_root/$package_rel"
measure="$package_root/artifacts/jobs/measure_command.py"
[ -f "$measure" ] || fail "missing command timer"
if [ -z "$output_dir" ]; then
    output_dir="$package_root/artifacts/execution"
fi
[ ! -e "$output_dir" ] || fail "output directory already exists: $output_dir"

ssh_opts=(-o BatchMode=yes -o ConnectTimeout=10)
for alias in login-ui lemhi; do
    ssh -O check "$alias" >/dev/null 2>&1 ||
        fail "control master unavailable: $alias; operator bootstrap required"
done
ssh "${ssh_opts[@]}" lemhi true || fail "noninteractive Lemhi probe failed"

tmp_parent=${TMPDIR:-/tmp}
local_tmp=$(mktemp -d "${tmp_parent%/}/a10m2d2.XXXXXX")
case "$local_tmp" in
    "${tmp_parent%/}"/a10m2d2.*) ;;
    *) fail "unsafe local temporary directory" ;;
esac
remote_created=false
run_started=$SECONDS

cleanup() {
    status=$?
    trap - EXIT INT TERM
    if [ "$remote_created" = true ]; then
        ssh "${ssh_opts[@]}" lemhi \
            "rm -rf -- '$remote_run'; test ! -e '$remote_run'" >/dev/null 2>&1 || true
    fi
    case "$local_tmp" in
        "${tmp_parent%/}"/a10m2d2.*) rm -rf -- "$local_tmp" ;;
    esac
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

mkdir -p "$output_dir/logs" "$local_tmp/fixtures" "$local_tmp/downloads"
{
    printf 'source_commit=%s\n' "$source_commit"
    printf 'remote_run=%s\n' "$remote_run"
    printf 'logical_ceiling_bytes=%s\n' "$logical_ceiling"
    sw_vers
    uname -m
    ssh -V 2>&1
} >"$output_dir/dispatch.txt"
for alias in login-ui lemhi; do
    ssh -O check "$alias"
done >"$output_dir/control-masters.txt"

ssh "${ssh_opts[@]}" lemhi \
    "umask 077; test ! -e '$remote_run'; command -v sha256sum; df -Pk .; mkdir -p '$remote_run/files'" \
    >"$output_dir/remote-preflight.txt"
remote_created=true
ssh "${ssh_opts[@]}" lemhi \
    'if command -v quota >/dev/null 2>&1; then quota -s 2>&1 | sed "s/${USER}/<user>/g"; else printf "quota_command=absent\n"; fi' \
    >>"$output_dir/remote-preflight.txt"

alternatives="$output_dir/alternative-transports.txt"
if command -v rsync >/dev/null 2>&1; then
    printf 'local_rsync=present\n' >>"$alternatives"
    rsync --version | sed -n '1p' >>"$alternatives"
else
    printf 'local_rsync=absent\n' >>"$alternatives"
fi
if ssh "${ssh_opts[@]}" lemhi 'command -v rsync >/dev/null 2>&1'; then
    printf 'remote_rsync=present\n' >>"$alternatives"
    ssh "${ssh_opts[@]}" lemhi 'rsync --version | sed -n "1p"' >>"$alternatives"
else
    printf 'remote_rsync=absent\n' >>"$alternatives"
fi
for side in local remote; do
    if [ "$side" = local ]; then
        if command -v globus >/dev/null 2>&1; then state=present; else state=absent; fi
    else
        if ssh "${ssh_opts[@]}" lemhi 'command -v globus >/dev/null 2>&1'; then state=present; else state=absent; fi
    fi
    printf '%s_globus_cli=%s\n' "$side" "$state" >>"$alternatives"
done

fixtures="$local_tmp/fixtures"
downloads="$local_tmp/downloads"
dd if=/dev/urandom of="$fixtures/random-1024m.bin" bs=1048576 count=1024 2>/dev/null
for size in 256 64 16; do
    dd if="$fixtures/random-1024m.bin" of="$fixtures/random-${size}m.bin" \
        bs=1048576 count="$size" 2>/dev/null
done
dd if=/dev/zero of="$fixtures/zero-64m.bin" bs=1048576 count=64 2>/dev/null
mkdir "$fixtures/small-files"
split -b 65536 -a 4 "$fixtures/random-64m.bin" "$fixtures/small-files/chunk-"
[ "$(find "$fixtures/small-files" -type f | wc -l | tr -d ' ')" -eq 1024 ] ||
    fail "small-file fixture count mismatch"
tar -cf "$fixtures/small-files.tar" -C "$fixtures" small-files

(
    cd "$fixtures"
    shasum -a 256 random-16m.bin random-64m.bin random-256m.bin \
        random-1024m.bin zero-64m.bin small-files.tar
    find small-files -type f -print | LC_ALL=C sort | xargs shasum -a 256
) >"$output_dir/fixture-manifest.sha256"

results="$output_dir/transfer-results.tsv"
integrity="$output_dir/integrity.tsv"
printf 'label\tdirection\ttrial\texpected_sha256\tobserved_sha256\tverdict\n' >"$integrity"

file_size() {
    stat -f %z "$1"
}

local_hash() {
    shasum -a 256 "$1" | awk '{print $1}'
}

remote_hash() {
    ssh "${ssh_opts[@]}" lemhi \
        "sha256sum '$remote_run/files/$1'" | awk '{print $1}'
}

measure_command() {
    label=$1
    direction=$2
    bytes=$3
    trial=$4
    compression=$5
    shift 5
    [ $((SECONDS - run_started)) -lt 7200 ] || fail "two-hour launch bound reached"
    python3 "$measure" \
        --label "$label" --direction "$direction" --bytes "$bytes" \
        --trial "$trial" --compression "$compression" \
        --results "$results" --log "$output_dir/logs/${label}-${direction}-${trial}-${compression}.log" \
        --timeout "$command_timeout" -- "$@"
}

record_integrity() {
    label=$1
    direction=$2
    trial=$3
    expected=$4
    observed=$5
    [ "$expected" = "$observed" ] || fail "integrity mismatch: $label $direction $trial"
    printf '%s\t%s\t%s\t%s\t%s\tpass\n' \
        "$label" "$direction" "$trial" "$expected" "$observed" >>"$integrity"
}

transfer_file_pair() {
    label=$1
    source=$2
    repetitions=$3
    compression=$4
    remote_name=$5
    bytes=$(file_size "$source")
    expected=$(local_hash "$source")
    scp_command=(scp -q "${ssh_opts[@]}")
    [ "$compression" = enabled ] && scp_command+=(-C)
    trial=1
    while [ "$trial" -le "$repetitions" ]; do
        measure_command "$label" upload "$bytes" "$trial" "$compression" \
            "${scp_command[@]}" "$source" \
            "lemhi:$remote_run/files/$remote_name"
        observed=$(remote_hash "$remote_name")
        record_integrity "$label" upload "$trial" "$expected" "$observed"

        destination="$downloads/${remote_name}-${trial}-${compression}"
        measure_command "$label" download "$bytes" "$trial" "$compression" \
            "${scp_command[@]}" \
            "lemhi:$remote_run/files/$remote_name" "$destination"
        observed=$(local_hash "$destination")
        record_integrity "$label" download "$trial" "$expected" "$observed"
        rm -f -- "$destination"
        trial=$((trial + 1))
    done
}

trial=1
while [ "$trial" -le 10 ]; do
    measure_command L0 control 0 "$trial" default \
        ssh "${ssh_opts[@]}" lemhi true
    trial=$((trial + 1))
done

transfer_file_pair S16 "$fixtures/random-16m.bin" 3 default random-16m.bin
transfer_file_pair S256 "$fixtures/random-256m.bin" 3 default random-256m.bin
transfer_file_pair S1024 "$fixtures/random-1024m.bin" 1 default random-1024m.bin

small_bytes=67108864
measure_command F1024 upload "$small_bytes" 1 default \
    scp -rq "${ssh_opts[@]}" "$fixtures/small-files" "lemhi:$remote_run/files/"
(
    cd "$fixtures/small-files"
    find . -type f -print | LC_ALL=C sort | xargs shasum -a 256
) >"$output_dir/small-local.sha256"
ssh "${ssh_opts[@]}" lemhi \
    "cd '$remote_run/files/small-files'; find . -type f -print | LC_ALL=C sort | xargs sha256sum" \
    >"$output_dir/small-remote.sha256"
cmp "$output_dir/small-local.sha256" "$output_dir/small-remote.sha256" ||
    fail "small-file upload manifest mismatch"
printf 'F1024\tupload\t1\tmanifest\tmanifest\tpass\n' >>"$integrity"

mkdir "$downloads/small-direct"
measure_command F1024 download "$small_bytes" 1 default \
    scp -rq "${ssh_opts[@]}" "lemhi:$remote_run/files/small-files" \
    "$downloads/small-direct/"
(
    cd "$downloads/small-direct/small-files"
    find . -type f -print | LC_ALL=C sort | xargs shasum -a 256
) >"$output_dir/small-download.sha256"
cmp "$output_dir/small-local.sha256" "$output_dir/small-download.sha256" ||
    fail "small-file download manifest mismatch"
printf 'F1024\tdownload\t1\tmanifest\tmanifest\tpass\n' >>"$integrity"
rm -rf -- "$downloads/small-direct"

transfer_file_pair TAR "$fixtures/small-files.tar" 1 default small-files.tar
transfer_file_pair CR64 "$fixtures/random-64m.bin" 1 default random-64m-default.bin
transfer_file_pair CR64 "$fixtures/random-64m.bin" 1 enabled random-64m-compressed.bin
transfer_file_pair CZ64 "$fixtures/zero-64m.bin" 1 default zero-64m-default.bin
transfer_file_pair CZ64 "$fixtures/zero-64m.bin" 1 enabled zero-64m-compressed.bin

[ $((SECONDS - run_started)) -lt 7200 ] || fail "two-hour launch bound reached"
interrupt_source="$fixtures/random-256m.bin"
interrupt_bytes=$(file_size "$interrupt_source")
interrupt_hash=$(local_hash "$interrupt_source")
set +e
python3 "$measure" \
    --label I256 --direction upload --bytes "$interrupt_bytes" \
    --trial 1 --compression default --results "$results" \
    --log "$output_dir/logs/I256-upload-1-default.log" --timeout 10 -- \
    scp -q -l 8192 "${ssh_opts[@]}" "$interrupt_source" \
    "lemhi:$remote_run/files/interrupted-256m.bin"
interrupt_status=$?
set -e
[ "$interrupt_status" -eq 124 ] || fail "intentional SCP interruption did not time out"
partial_listing=$(ssh "${ssh_opts[@]}" lemhi \
    "find '$remote_run/files' -maxdepth 1 -type f -name 'interrupted-256m.bin*' -printf '%f\\t%s\\n'")
[ "$(printf '%s\n' "$partial_listing" | awk 'NF { count += 1 } END { print count + 0 }')" -eq 1 ] ||
    fail "intentional SCP interruption did not leave exactly one partial"
partial_name=$(printf '%s\n' "$partial_listing" | awk -F '\t' 'NF { print $1 }')
partial_size=$(printf '%s\n' "$partial_listing" | awk -F '\t' 'NF { print $2 }')
case "$partial_name" in interrupted-256m.bin*) ;; *) fail "unsafe partial name" ;; esac
[ "$partial_size" -gt 0 ] && [ "$partial_size" -lt "$interrupt_bytes" ] ||
    fail "intentional SCP partial size is outside bounds"
{
    printf 'scp_interrupt_status=%s\n' "$interrupt_status"
    printf 'scp_partial_name=%s\n' "$partial_name"
    printf 'scp_partial_bytes=%s\n' "$partial_size"
} >"$output_dir/interruption-resume.txt"

if command -v rsync >/dev/null 2>&1 &&
    ssh "${ssh_opts[@]}" lemhi 'command -v rsync >/dev/null 2>&1'; then
    set +e
    python3 "$measure" \
        --label R256 --direction resume --bytes "$interrupt_bytes" \
        --trial 1 --compression default --results "$results" \
        --log "$output_dir/logs/R256-resume-1-default.log" \
        --timeout "$command_timeout" -- \
        rsync --partial --append-verify \
        -e "ssh -o BatchMode=yes -o ConnectTimeout=10" \
        "$interrupt_source" "lemhi:$remote_run/files/$partial_name"
    resume_status=$?
    set -e
    printf 'rsync_resume_status=%s\n' "$resume_status" >>"$output_dir/interruption-resume.txt"
    if [ "$resume_status" -eq 0 ]; then
        observed=$(remote_hash "$partial_name")
        record_integrity R256 resume 1 "$interrupt_hash" "$observed"
        printf 'rsync_resume_integrity=pass\n' >>"$output_dir/interruption-resume.txt"
    else
        printf 'rsync_resume_integrity=not_reached\n' >>"$output_dir/interruption-resume.txt"
    fi
else
    printf 'rsync_resume_status=unavailable\n' >>"$output_dir/interruption-resume.txt"
fi
ssh "${ssh_opts[@]}" lemhi "rm -f -- '$remote_run/files/$partial_name'"

logical_total=$(awk -F '\t' 'NR > 1 { total += $3 } END { printf "%.0f", total }' "$results")
[ "$logical_total" -le "$logical_ceiling" ] || fail "logical transfer ceiling exceeded"
printf 'logical_transferred_bytes=%s\n' "$logical_total" >"$output_dir/traffic-ledger.txt"

ssh "${ssh_opts[@]}" lemhi \
    "rm -rf -- '$remote_run'; test ! -e '$remote_run'; printf 'remote_run=absent\\n'" \
    >"$output_dir/cleanup.txt"
remote_created=false
case "$local_tmp" in
    "${tmp_parent%/}"/a10m2d2.*)
        rm -rf -- "$local_tmp"
        [ ! -e "$local_tmp" ] || fail "local fixture cleanup failed"
        local_tmp=
        ;;
    *)
        fail "unsafe local cleanup target"
        ;;
esac
printf 'local_fixtures=absent\n' >>"$output_dir/cleanup.txt"
printf 'stage1=complete\n'
