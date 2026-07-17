#!/bin/sh
set -eu
token=$1
name=ltk-$token
{ squeue -h -n "$name" -o '%A' 2>/dev/null || true
  sacct -n -X --name "$name" --format=JobIDRaw 2>/dev/null || true
} | awk '/^[0-9]+$/ { seen[$1]=1 } END { for (id in seen) print id }'
