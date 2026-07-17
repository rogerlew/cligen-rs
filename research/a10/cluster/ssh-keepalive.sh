#!/bin/sh

set -eu

PROGRAM=${0##*/}
INTERVAL_SECONDS=${A10_SSH_KEEPALIVE_INTERVAL_SECONDS:-300}
RUN_ONCE=false

usage() {
    cat <<EOF
Usage: $PROGRAM [--interval SECONDS] [--once] [SSH_ALIAS ...]

Keep existing A10 SSH control masters alive without initiating a cold login.
The default aliases are: login-ui lemhi

Environment:
  A10_SSH_KEEPALIVE_INTERVAL_SECONDS  Default interval (default: 300)
EOF
}

fail() {
    printf '%s: %s\n' "$PROGRAM" "$*" >&2
    exit 1
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --interval)
            [ "$#" -ge 2 ] || fail "--interval requires a value"
            INTERVAL_SECONDS=$2
            shift 2
            ;;
        --once)
            RUN_ONCE=true
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            fail "unknown option: $1"
            ;;
        *)
            break
            ;;
    esac
done

case "$INTERVAL_SECONDS" in
    '' | *[!0-9]*)
        fail "interval must be a positive integer"
        ;;
    0)
        fail "interval must be greater than zero"
        ;;
esac

if [ "$#" -eq 0 ]; then
    set -- login-ui lemhi
fi

for host in "$@"; do
    case "$host" in
        '' | -*)
            fail "invalid SSH alias: $host"
            ;;
    esac
done

timestamp() {
    date -u '+%Y-%m-%dT%H:%M:%SZ'
}

check_masters() {
    for host in "$@"; do
        if output=$(ssh -O check "$host" 2>&1); then
            printf '%s %s: %s\n' "$(timestamp)" "$host" "$output"
        else
            printf '%s %s: control master unavailable: %s\n' \
                "$(timestamp)" "$host" "$output" >&2
            printf '%s: run the supervised SSH bootstrap again\n' \
                "$PROGRAM" >&2
            return 1
        fi
    done
}

check_masters "$@"

if [ "$RUN_ONCE" = true ]; then
    exit 0
fi

printf '%s %s: checking every %s seconds; stop with Ctrl-C\n' \
    "$(timestamp)" "$PROGRAM" "$INTERVAL_SECONDS"

while sleep "$INTERVAL_SECONDS"; do
    check_masters "$@" || exit 1
done
