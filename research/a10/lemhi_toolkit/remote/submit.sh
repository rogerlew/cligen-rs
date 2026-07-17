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
stdout=$1
stderr=$2
root=$base/$run
[ -f "$root/.lemhi-toolkit-owner.json" ] && [ -f "$root/$script" ] || exit 66
mkdir -p -- "$root/slurm"
exec sbatch --parsable --no-requeue --job-name="ltk-$token" --partition="$partition" \
  --gres="$gres" --cpus-per-task="$cpus" --mem="${memory_mb}M" --time="$minutes" \
  --chdir="$root" --output="$root/$stdout" --error="$root/$stderr" -- "$root/$script"
