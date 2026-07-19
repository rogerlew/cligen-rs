#!/usr/bin/env python3
"""Verify the committed A10M5O2D1 result record."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load(name: str) -> dict:
    return json.loads((ROOT / "live" / name).read_text(encoding="utf-8"))


operational = load("operational-summary.json")
bandwidth = load("bandwidth-summary.json")
package = (ROOT.parent / "package.md").read_text(encoding="utf-8")
analysis = (ROOT / "analysis.md").read_text(encoding="utf-8")
disposition = (ROOT / "execution-disposition.md").read_text(encoding="utf-8")

assert operational["state"] == "COMPLETED"
assert operational["exit_code"] == 0
assert operational["actual_gpu_seconds"] == 656
assert operational["actual_gpu_minutes"] == 11
assert operational["requested_gpu_minutes"] == 40
assert operational["unused_recovery_gpu_minutes_released"] == 5
assert operational["all_thirteen_gates_passed"] is True
assert bandwidth["environment"]["gpu_count"] == 4
assert bandwidth["environment"]["gpu_model"] == "NVIDIA L40"
assert bandwidth["p2p_driver_matrix"]["read"].endswith("OK")
assert bandwidth["p2p_driver_matrix"]["write"].endswith("OK")

rows = {row["group"]: row for row in bandwidth["results_128_mib"]}
assert set(rows) == {"0-1", "0-2", "0-3", "1-2", "1-3", "2-3", "0-1-2-3"}
for group in ("0-1", "0-2", "0-3", "1-2", "1-3", "2-3"):
    assert rows[group]["default_transport"] == "P2P/CUMEM"
    assert rows[group]["default_bus_gbps"] > rows[group]["p2p_disabled_bus_gbps"]
quad = rows["0-1-2-3"]
assert quad["default_transport"] == "SHM/direct/direct"
assert abs(quad["default_bus_gbps"] - quad["p2p_disabled_bus_gbps"]) < 0.02

terminal = "A10M5O2D1-L40-INTERCONNECT-CHARACTERIZED"
assert "Status: `EXECUTED-COMPLETE`" in package
assert terminal in package
assert terminal in disposition
assert "not caused by an external network hop" in analysis

print("A10M5O2D1_RESULT_PASS")
