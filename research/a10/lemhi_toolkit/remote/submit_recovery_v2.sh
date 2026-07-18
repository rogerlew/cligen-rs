#!/bin/sh
set -eu

base=$1
run=$2
script=$3
partition=$4
gres=$5
cpus=$6
memory_mb=$7
minutes=$8
token=$9
shift 9
authority_token=$1
node=$2
target=$3
uid=$4
device=$5
marker_sha256=$6
receipt=$7
original_job_id=$8
target_sha256=$9
shift 9
stdout=$1
stderr=$2
root=$base/$run

[ -f "$root/.lemhi-toolkit-owner.json" ] && [ -x "$root/$script" ] || exit 66
mkdir -p -- "$root/slurm"
exec sbatch --parsable --no-requeue --export=NONE --job-name="ltk-$token" \
  --comment="$authority_token" --partition="$partition" --gres="$gres" \
  --cpus-per-task="$cpus" --mem="${memory_mb}M" --time="$minutes" \
  --nodelist="$node" --chdir="$root" --output="$root/$stdout" \
  --error="$root/$stderr" -- "$root/$script" "$target" "$uid" \
  "$device" "$marker_sha256" "$receipt" "$original_job_id" "$node" \
  "$target_sha256"
