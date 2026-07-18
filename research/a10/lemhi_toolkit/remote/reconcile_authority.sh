#!/bin/sh
set -eu

authority_token=$1

# The v2 scheduler provider places the immutable authority token in the Slurm
# comment field. Refuse reconciliation when either live or accounting queries
# are unavailable, then return the exact union of authority-tagged job IDs.
command -v squeue >/dev/null 2>&1
command -v sacct >/dev/null 2>&1
case "$authority_token" in
  *[!A-Za-z0-9._-]*|'') exit 2 ;;
esac

{
  squeue -h -o '%A|%k'
  sacct -n -X --parsable2 -o JobIDRaw,Comment
} | awk -F '|' -v token="$authority_token" '$2 == token && $1 ~ /^[0-9]+$/ { seen[$1] = 1 } END { for (job in seen) print job }' | sort -n
