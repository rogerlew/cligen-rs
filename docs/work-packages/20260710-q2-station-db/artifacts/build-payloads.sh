#!/usr/bin/env bash
# Q2 payload build: one deterministic .tar.gz per collection —
# verbatim tree + its python-produced SQLite catalog at the payload
# root. Deterministic tar (sorted names, fixed owner/mtime) so a
# rebuild from the same tree reproduces the same hash.
set -euo pipefail

DB=/workdir/jimf-cligen532/db
OUT=${1:?usage: build-payloads.sh <output-dir>}
VERSION=2026.07
mkdir -p "$OUT"

# name  tree  catalog
build() {
  local name=$1 tree=$2 catalog=$3
  local stage archive
  stage=$(mktemp -d)
  cp -a "$DB/$tree/." "$stage/"
  cp -a "$DB/$catalog" "$stage/$catalog"
  archive="$OUT/$name-$VERSION.tar.gz"
  tar --sort=name --owner=0 --group=0 --numeric-owner \
      --mtime='2026-07-10 00:00Z' \
      -C "$stage" -cf - . | gzip -n > "$archive"
  rm -rf "$stage"
  echo "$name $(sha256sum "$archive" | cut -d' ' -f1) $(stat -c%s "$archive")"
}

build us-legacy stations           stations.db
build us-2015   2015_par_files     2015_stations.db
build ghcn-intl GHCN_Intl_Stations ghcn_stations.db
build au        au_par_files       au_stations.db
build chile     chile              chile.db
