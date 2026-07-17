#!/bin/sh
set -eu

remote_base=$1
run_root=$2
gate_receipt=$3
case "$remote_base/$run_root/$gate_receipt" in
  *..*|*//*|*' '*|*'*'*|*'?'*) exit 64 ;;
esac
root="$remote_base/$run_root"
marker="$root/.lemhi-toolkit-owner.json"
receipt="$root/$gate_receipt"
test -d "$root"
test ! -L "$root"
test -f "$marker"
test ! -L "$marker"
test -f "$receipt"
test ! -L "$receipt"
cat "$receipt"
