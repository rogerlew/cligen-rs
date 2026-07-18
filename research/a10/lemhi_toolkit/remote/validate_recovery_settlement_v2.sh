#!/bin/sh
set -eu

job_id=$1
expected_node=$2
case "$job_id" in ''|*[!0-9]*) exit 64 ;; esac
case "$expected_node" in ''|*[!A-Za-z0-9._-]*) exit 64 ;; esac

[ -z "$(squeue -h -j "$job_id" -o '%A')" ] || exit 74
records=$(sacct -D -n -j "$job_id" --format=JobIDRaw,State,NodeList -P)
[ -n "$records" ] || exit 69
printf '%s\n' "$records" | awk -F '|' -v job="$job_id" -v node="$expected_node" '
  function terminal(state) {
    sub(/[ +].*$/, "", state)
    return state ~ /^(BOOT_FAIL|CANCELLED|COMPLETED|DEADLINE|FAILED|NODE_FAIL|OUT_OF_MEMORY|PREEMPTED|REVOKED|TIMEOUT)$/
  }
  $1 == job {
    seen++
    if ($3 != node || !terminal($2)) bad=1
  }
  $1 ~ ("^" job "\\.") && !terminal($2) { bad=1 }
  END { exit !(seen >= 1 && !bad) }
' || exit 74
printf '%s\n' ORIGINAL_JOB_SETTLED
