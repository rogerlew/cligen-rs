#!/usr/bin/env python3
"""Emit a compact, hash-bound station/source/period coverage ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from corpus_common import sha256

PERIODS = ("full", "fit", "evaluation")
SOURCES = ("daymet", "ghcn")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    corpus_path = args.corpus or here / "observed-target-corpus-v1.json"
    source_path = args.source_manifest or here / "source-manifest-v1.json"
    output = args.output or here / "coverage-evidence-v1.md"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    source_manifest = json.loads(source_path.read_text(encoding="utf-8"))
    source_hash = sha256(source_path.read_bytes())
    if corpus.get("source_manifest_sha256") != source_hash:
        raise ValueError("target corpus does not bind the supplied source manifest")
    if corpus.get("fixed_periods") != source_manifest.get("fixed_periods"):
        raise ValueError("target and source-manifest periods differ")

    rows = []
    available = 0
    for station in corpus["stations"]:
        for source_name in SOURCES:
            source = station["sources"][source_name]
            if source.get("availability") != "available":
                for period in PERIODS:
                    rows.append(
                        (
                            station["station_id"],
                            station["regime"],
                            source_name,
                            period,
                            "unavailable",
                            "—",
                            "—",
                            "—",
                            "—",
                        )
                    )
                continue
            for period in PERIODS:
                coverage = source["periods"][period]["precipitation_structure"][
                    "coverage"
                ]
                expected = coverage["expected_days"]
                observed = coverage["observed_precip_days"]
                missing = coverage["missing_days"]
                gaps = coverage["missing_gap_runs"]
                if observed + missing != expected:
                    raise ValueError(
                        f"coverage arithmetic failed: {station['station_id']}/"
                        f"{source_name}/{period}"
                    )
                rows.append(
                    (
                        station["station_id"],
                        station["regime"],
                        source_name,
                        period,
                        "available",
                        str(expected),
                        str(observed),
                        str(missing),
                        str(gaps),
                    )
                )
                available += 1

    tool_path = Path(__file__).resolve()
    target_hash = sha256(corpus_path.read_bytes())
    lines = [
        "# A5a observed-corpus coverage evidence",
        "",
        "This ledger is derived; the archived sources and target corpus remain authority.",
        "A missing-gap run is a maximal contiguous interval of missing expected",
        "source-calendar dates, including an interval touching a period boundary.",
        "",
        f"- Target corpus SHA-256: `{target_hash}`",
        f"- Source manifest SHA-256: `{source_hash}`",
        f"- Target builder SHA-256: `{sha256((here / 'build_targets.py').read_bytes())}`",
        f"- Coverage derivation tool SHA-256: `{sha256(tool_path.read_bytes())}`",
        f"- Rows: {len(rows)} ({available} available; {len(rows) - available} unavailable)",
        "",
        "| station | regime | source | period | status | expected | observed P | missing | gap runs |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    print(output)


if __name__ == "__main__":
    main()
