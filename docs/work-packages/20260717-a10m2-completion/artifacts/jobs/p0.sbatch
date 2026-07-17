#!/bin/bash
#SBATCH --job-name=a10m2c-p0
#SBATCH --partition=gpu-icrews
#SBATCH --nodelist=node03
#SBATCH --gres=gpu:l40:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -u
set -o pipefail
umask 077

record_executable() {
    label=$1
    path=$2
    if [ -x "$path" ]; then
        printf '%s\t0\t%s\n' "$label" "$path"
    else
        printf '%s\t1\tmissing\n' "$label"
    fi
}

printf 'check\tstatus\tdetail\n'
record_executable python-frozen /opt/modules/devel/python/3.11.11/bin/python
record_executable cuda-frozen /usr/local/cuda-12.8/bin/nvcc
record_executable compiler-frozen /usr/bin/g++
record_executable python-system /usr/bin/python3
if [ -x /usr/bin/python3 ]; then
    /usr/bin/python3 --version
fi
if [ -d /opt/modules/devel/python ]; then
    printf 'python-prefix\t0\tpresent\n'
    find /opt/modules/devel/python -maxdepth 4 -type f \
        \( -name python -o -name 'python3*' \) -perm -111 -print 2>/dev/null |
        sort
else
    printf 'python-prefix\t1\tmissing\n'
fi
local_root=${SLURM_TMPDIR:-${TMPDIR:-/tmp}}
local_root=${local_root%/}
candidate="$local_root/a10m2c-c1-${SLURM_JOB_ID}"
if [ -d "$local_root" ] && [ -w "$local_root" ]; then
    printf 'local-root\t0\twritable\n'
else
    printf 'local-root\t1\tunavailable\n'
fi
if [ -e "$candidate" ]; then
    printf 'local-candidate\t1\tcollision\n'
else
    printf 'local-candidate\t0\tabsent\n'
fi
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
printf 'p0=complete\n'
