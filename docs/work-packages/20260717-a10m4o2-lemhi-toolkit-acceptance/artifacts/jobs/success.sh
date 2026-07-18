#!/bin/sh
set -eu

device_name=$(/usr/bin/nvidia-smi --query-gpu=name --format=csv,noheader | /usr/bin/head -n 1)
case "$device_name" in *L40*) l40_visible=true ;; *) l40_visible=false ;; esac
/bin/sleep 3
temporary=success.json.part.$$
umask 077
printf '{"device_name":"%s","gates":{"job_local_cleanup":true,"l40_visible":%s,"registered_success":true}}\n' \
  "$device_name" "$l40_visible" > "$temporary"
/bin/mv -- "$temporary" success.json
[ "$l40_visible" = true ]
