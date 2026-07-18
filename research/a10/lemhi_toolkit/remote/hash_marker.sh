#!/bin/sh
set -eu
base=$1
relative=$2
case "$base" in /*) ;; *) exit 64 ;; esac
case "$relative" in ''|/*|*'..'*|*'//'*) exit 64 ;; esac
target=$base/$relative
[ -d "$target" ] && [ ! -L "$target" ] || exit 64
marker=$target/.lemhi-toolkit-owner.json
[ -f "$marker" ] && [ ! -L "$marker" ] || exit 65
sha256sum "$marker" | awk '{print $1}'
