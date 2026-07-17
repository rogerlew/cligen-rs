#!/bin/sh
set -eu
base=$1
relative=$2
case "$base" in /*) ;; *) exit 64 ;; esac
case "$relative" in ''|/*|*'..'*|*'//'*) exit 64 ;; esac
target=$base/$relative
[ "$relative" = "runs/${relative#runs/}" ] && [ "${relative#runs/}" != "$relative" ] || exit 64
[ -e "$base" ] || mkdir -m 700 -- "$base"
[ -d "$base" ] && [ ! -L "$base" ] || exit 64
[ -e "$base/runs" ] || mkdir -m 700 -- "$base/runs"
[ -d "$base/runs" ] && [ ! -L "$base/runs" ] || exit 64
[ ! -e "$target" ] || exit 73
mkdir -m 700 -- "$target"
