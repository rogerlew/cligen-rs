#!/bin/sh
set -eu

attempt_root=$1
marker_sha256=$2
durable_status=$3
shift 3

case "$attempt_root" in /*) ;; *) exit 64 ;; esac
[ -d "$attempt_root" ] && [ ! -L "$attempt_root" ] || exit 64
marker=$attempt_root/.lemhi-toolkit-owner.json
[ -f "$marker" ] && [ ! -L "$marker" ] || exit 64
[ "$(sha256sum "$marker" | awk '{print $1}')" = "$marker_sha256" ] || exit 65

child=
forward()
{
  signal_name=$1
  [ -z "$child" ] || kill -"$signal_name" -- "-$child" 2>/dev/null || true
}
trap 'forward TERM' TERM
trap 'forward INT' INT
trap 'forward HUP' HUP

# setsid makes the application and its descendants one process group owned by
# this supervisor. Environment closure is performed by the committed job
# script before invoking this wrapper.
setsid "$@" &
child=$!
set +e
wait "$child"
application_status=$?
set -e

status_ok=true
temporary=${durable_status}.part.$$
if ! (umask 077; printf '{"application_exit":%s}\n' "$application_status" > "$temporary" && mv -- "$temporary" "$durable_status"); then
  status_ok=false
  rm -f -- "$temporary"
fi

cleanup_ok=false
if [ "$(sha256sum "$marker" | awk '{print $1}')" = "$marker_sha256" ]; then
  rm -rf -- "$attempt_root"
  [ ! -e "$attempt_root" ] && cleanup_ok=true
fi

[ "$status_ok" = true ] && [ "$cleanup_ok" = true ] || exit 75
exit "$application_status"
