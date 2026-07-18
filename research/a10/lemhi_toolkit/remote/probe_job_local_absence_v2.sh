#!/bin/sh
set -eu

target=$1
case "$target" in
  /tmp/lemhi-toolkit-[0-9]*/a10-canonical-v2-[0-9]*) ;;
  *) exit 64 ;;
esac

if [ -e "$target" ] || [ -L "$target" ]; then
  printf '%s\n' JOB_LOCAL_PRESENT
  exit 74
fi
printf '%s\n' JOB_LOCAL_ABSENT
