#!/usr/bin/env python3
"""Q3/Q4 matrix runner (pre-registration `Matrix` + the Q4 comparison).

{faithful, off} x {30, 100 yr} x 17 stations (Q3, 68 runs) plus
fast_batch_v0 x {30, 100 yr} x 17 (Q4 comparison, 34 runs). Each run:
write a runspec against the synced us-2015 cache, `cligen run`, record
wall-clock, keep the quality sidecar, hash the `.cli`.

Usage: run-matrix.py <cligen-binary> <us2015-cache> <out-dir>
Writes <out-dir>/runs.json; sidecars stay under <out-dir> (evidence
tree; the committed record is the analysis summary + hashes).
"""

import hashlib
import json
import os
import subprocess
import sys
import time

CORPUS = [
    "ca042319", "az029654", "ut429382", "ca042257",
    "az022664", "az028619", "nm294426", "tx412797",
    "al015478", "ms227840", "fl086997", "fl083909",
    "co051660", "wy485345", "mn214026", "ak505769",
    "id106388",
]

CONFIGS = [
    ("faithful", "faithful_5_32_3", "faithful"),
    ("qc-off", "faithful_5_32_3", "off"),
    ("fast-v0", "fast_batch_v0", None),
]


def main(binary, cache, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    runs = []
    for station in CORPUS:
        par = os.path.abspath(os.path.join(cache, f"{station}.par"))
        assert os.path.isfile(par), par
        for tag, profile, qc in CONFIGS:
            for years in (30, 100):
                name = f"{station}-{tag}-{years}yr"
                cli = os.path.abspath(os.path.join(out_dir, f"{name}.cli"))
                spec = os.path.join(out_dir, f"{name}.yaml")
                lines = [
                    "cligen_runspec: 1",
                    f"station: {{ par: {par} }}",
                    "mode: continuous",
                    f"simulation: {{ begin_year: 1, years: {years} }}",
                    f"generation_profile: {profile}",
                ]
                if qc is not None:
                    lines.append(f"qc_filter: {qc}")
                lines.append(f"output: {{ cli: {cli}, overwrite: true }}")
                with open(spec, "w") as handle:
                    handle.write("\n".join(lines) + "\n")
                start = time.monotonic()
                result = subprocess.run(
                    [binary, "run", spec], capture_output=True, text=True
                )
                wall = time.monotonic() - start
                assert result.returncode == 0, (name, result.stderr)
                cli_bytes = open(cli, "rb").read()
                runs.append(
                    {
                        "station": station,
                        "config": tag,
                        "years": years,
                        "wall_s": round(wall, 4),
                        "cli_sha256": hashlib.sha256(cli_bytes).hexdigest(),
                        "cli_bytes": len(cli_bytes),
                        "report": f"{name}.cli.quality.json",
                    }
                )
                os.remove(cli)  # reports are the measurement
                print(name, f"{wall:.2f}s", flush=True)
    with open(os.path.join(out_dir, "runs.json"), "w") as handle:
        json.dump(runs, handle, indent=1)
    print("runs:", len(runs))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
