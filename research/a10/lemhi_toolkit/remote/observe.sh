#!/bin/sh
set -eu
job_id=$1
line=$(sacct -n -X -j "$job_id" --format=State,ExitCode,ElapsedRaw -P | awk -F '|' 'NF >= 3 {print; exit}')
[ -n "$line" ] || exit 69
state=$(printf '%s\n' "$line" | awk -F '|' '{print $1}')
exit_pair=$(printf '%s\n' "$line" | awk -F '|' '{print $2}')
elapsed=$(printf '%s\n' "$line" | awk -F '|' '{print $3}')
exit_code=${exit_pair%%:*}
case "$state" in CANCELLED*) state=CANCELLED ;; esac
case "$state" in COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED|BOOT_FAIL|DEADLINE|REVOKED) terminal=true ;; *) terminal=false ;; esac
printf '{"accounting":"available","actual_gpu_minutes":null,"exit_code":%s,"gates":{"scheduler_terminal":%s},"state":"%s","terminal":%s}\n' \
  "$exit_code" "$terminal" "$state" "$terminal"
