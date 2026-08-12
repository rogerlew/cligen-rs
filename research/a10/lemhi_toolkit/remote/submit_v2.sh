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
shift
stdout=$1
stderr=$2
mode=${3:-none}
root=$base/$run
[ -f "$root/.lemhi-toolkit-owner.json" ] && [ -f "$root/$script" ] || exit 66
mkdir -p -- "$root/slurm"
case "$mode" in
  none)
    exec sbatch --parsable --no-requeue --export=NONE --job-name="ltk-$token" \
      --comment="$authority_token" --partition="$partition" --gres="$gres" \
      --cpus-per-task="$cpus" --mem="${memory_mb}M" --time="$minutes" \
      --chdir="$root" --output="$root/$stdout" --error="$root/$stderr" \
      -- "$root/$script"
    ;;
  scheduler-pending-start-recheck-v1)
    case "$gres" in gpu:l40:[1-4]) ;; *) exit 64 ;; esac
    expected=${gres##*:}
    wrapper='actual=${CUDA_VISIBLE_DEVICES:-}; [ -n "$actual" ] || exit 65; count=$(printf "%s" "$actual" | awk -F, "{print NF}"); [ "$count" -eq "$1" ] || exit 65; exec "$2"'
    exec sbatch --parsable --no-requeue --export=NONE --job-name="ltk-$token" \
      --comment="$authority_token" --partition="$partition" --gres="$gres" \
      --cpus-per-task="$cpus" --mem="${memory_mb}M" --time="$minutes" \
      --chdir="$root" --output="$root/$stdout" --error="$root/$stderr" \
      --wrap "/bin/sh -c '$wrapper' -- '$expected' '$root/$script'"
    ;;
  *) exit 64 ;;
esac
