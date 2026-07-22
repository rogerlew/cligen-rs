#!/bin/sh
set -eu

job_id=$1
expected_node=$2
expected_command=$3
expected_stdout=$4
expected_stderr=$5

case "$job_id" in ''|*[!0-9]*) exit 64 ;; esac
row=$(sacct -n -X -P -j "$job_id" --format=JobIDRaw,State,NodeList,ElapsedRaw,ExitCode | sed -n '1p')
IFS='|' read -r observed_job state node elapsed exit_code <<EOF
$row
EOF
[ "$observed_job" = "$job_id" ] || exit 65
[ "$state" = COMPLETED ] || exit 65
[ "$node" = "$expected_node" ] || exit 65
[ "$exit_code" = 0:0 ] || exit 65
case "$elapsed" in ''|*[!0-9]*) exit 65 ;; esac

control=$(scontrol show job -o "$job_id")
case " $control " in *' Partition=gpu-icrews '*) ;; *) exit 65 ;; esac
case " $control " in *' TimeLimit=00:05:00 '*) ;; *) exit 65 ;; esac
case " $control " in *' TresPerNode=gres/gpu:l40:1 '*) ;; *) exit 65 ;; esac
case " $control " in *" Command=$expected_command "*) ;; *) exit 65 ;; esac
case " $control " in *" StdOut=$expected_stdout "*) ;; *) exit 65 ;; esac
case " $control " in *" StdErr=$expected_stderr "*) ;; *) exit 65 ;; esac
[ -f "$expected_command" ] && [ ! -L "$expected_command" ] || exit 65
[ -f "$expected_stdout" ] && [ ! -L "$expected_stdout" ] || exit 65
[ -f "$expected_stderr" ] && [ ! -L "$expected_stderr" ] || exit 65
script_sha256=$(sha256sum "$expected_command" | awk '{print $1}')
stdout_sha256=$(sha256sum "$expected_stdout" | awk '{print $1}')
stderr_sha256=$(sha256sum "$expected_stderr" | awk '{print $1}')
minutes=$(( (elapsed + 59) / 60 ))
printf '{"actual_gpu_minutes":%s,"elapsed_seconds":%s,"exit_code":"0:0","job_id":"%s","node":"%s","script_sha256":"%s","state":"COMPLETED","stderr_sha256":"%s","stdout_sha256":"%s"}\n' \
  "$minutes" "$elapsed" "$job_id" "$node" "$script_sha256" \
  "$stderr_sha256" "$stdout_sha256"
