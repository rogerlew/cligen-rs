#!/usr/bin/env python3
"""Verify canonical v2 designation without external state."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from research.a10.lemhi_toolkit.core import canonical_bytes, read_json, sha256_bytes


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(f"canonical v2 designation: FAIL: {detail}")


def semantic_hash(value: dict, field: str) -> str:
    copy = dict(value)
    recorded = copy.pop(field)
    require(recorded == sha256_bytes(canonical_bytes(copy)), field)
    return recorded


def main() -> None:
    index = read_json(ROOT / "research/a10/lemhi_toolkit/configurations/lemhi-canonical-designation-index-v1.json")
    candidate = read_json(ROOT / index["current"]["configuration_path"])
    attestation = read_json(ROOT / index["current"]["attestation_path"])
    prior = read_json(ROOT / index["superseded"][0]["configuration_path"])
    designation = semantic_hash(index, "designation_sha256")
    candidate_hash = semantic_hash(candidate, "configuration_semantic_sha256")
    attestation_hash = semantic_hash(attestation, "attestation_sha256")
    prior_hash = semantic_hash(prior, "configuration_semantic_sha256")
    require(index["schema_version"] == "lemhi-canonical-designation-index-1", "schema")
    require(index["current"]["status"] == "current" and index["current"]["configuration_semantic_sha256"] == candidate_hash, "current")
    require(index["current"]["attestation_sha256"] == attestation_hash and attestation["verdict"] == "PASS", "attestation")
    require(attestation["configuration_semantic_sha256"] == candidate_hash, "attested candidate")
    require(index["superseded"][0]["status"] == "superseded" and index["superseded"][0]["configuration_semantic_sha256"] == prior_hash, "prior")
    require(prior["configuration_status"] == "current-canonical", "v1 status-at-issuance mutation")
    print(f"canonical v2 designation: PASS designation={designation}")


if __name__ == "__main__":
    main()
