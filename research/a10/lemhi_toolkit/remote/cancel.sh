#!/bin/sh
set -eu
job_id=$1
case "$job_id" in *[!0-9]*|'') exit 64 ;; esac
exec scancel -- "$job_id"
