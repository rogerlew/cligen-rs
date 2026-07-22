#!/usr/bin/env python3
"""A10M5R15R2 corpus identity overlay for the inherited loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inherited_r15_legacy_core import *  # noqa: F403
import inherited_r15_legacy_core as inherited


EXPECTED_AGGREGATE_BYTES = 223_729_862
EXPECTED_MANIFEST_ID = "a10m5r15r1-offline-transfer-v1"
EXPECTED_NORMALIZED_ID = "a10m5r15r1-normalized-manifest-v1"


def verify_corpus(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    artifacts = root / "artifacts"
    transfer = json.loads((artifacts / "offline-transfer-manifest-v1.json").read_text())
    normalized = json.loads((artifacts / "normalized-manifest-v1.json").read_text())
    normalization = json.loads((artifacts / "normalization-statistics-v1.json").read_text())
    observed = 0
    for record in transfer.get("objects", []):
        path = root / record["path"]
        if not path.is_file() or path.stat().st_size != record["bytes"] or inherited.sha256(path) != record["sha256"]:
            raise RuntimeError(f"successor transfer identity mismatch: {record['path']}")
        observed += record["bytes"]
    if (
        transfer.get("manifest_id") != EXPECTED_MANIFEST_ID
        or normalized.get("manifest_id") != EXPECTED_NORMALIZED_ID
        or len(transfer.get("objects", [])) != 98
        or observed != EXPECTED_AGGREGATE_BYTES
        or transfer.get("aggregate_bytes") != EXPECTED_AGGREGATE_BYTES
        or normalization.get("fit_role_only") != "candidate_fit"
        or any(normalized.get("leakage_audit", {}).values())
    ):
        raise RuntimeError("A10M5R15R1 corpus contract drift")
    return transfer, normalized, normalization
