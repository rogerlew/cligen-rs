#!/usr/bin/env python3
"""Verify current PRISM authority surfaces against the frozen audit contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
ARTIFACTS = PACKAGE / "artifacts"
CONTRACT = json.loads((ARTIFACTS / "audit-contract.json").read_text())
WORD = re.compile(r"[a-z]+")
DOI = re.compile(r"10\.[0-9a-z./_-]+")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def text_files(path: Path):
    candidates = [path] if path.is_file() else sorted(path.rglob("*"))
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        yield candidate, text


def scan(path: Path) -> None:
    fingerprints = {
        (item["kind"], item["length"], item["sha256"])
        for item in CONTRACT["prohibited_token_fingerprints"]
    }
    for candidate, text in text_files(path):
        tokens = (("word", match.group()) for match in WORD.finditer(text))
        dois = (("doi", match.group().rstrip(".,;:)")) for match in DOI.finditer(text))
        for kind, token in (*tokens, *dois):
            identity = (kind, len(token), sha256_bytes(token.encode()))
            if identity in fingerprints:
                raise AssertionError(f"prohibited attribution token in {candidate}")


def verify_method() -> None:
    embedded = REPO / "crates/cligen/src/prism/method.json"
    frozen = (
        REPO
        / "docs/work-packages/20260718-prism-mode-bundle-pedigree/artifacts"
        / "method-record-contract.json"
    )
    assert embedded.read_bytes() == frozen.read_bytes()
    assert sha256_bytes(embedded.read_bytes()) == CONTRACT["canonical_method_sha256"]
    record = json.loads(embedded.read_text())
    assert [item["stage"] for item in record["pedigree"]] == CONTRACT[
        "canonical_pedigree_stages"
    ]
    assert len(record["limitations"]) == 9


def verify_history() -> None:
    history = CONTRACT["history"]
    for commit in (history["superseded_commit"], history["correcting_commit"]):
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=REPO,
            check=True,
        )
    subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            history["superseded_commit"],
            history["correcting_commit"],
        ],
        cwd=REPO,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            history["correcting_commit"],
            "HEAD",
        ],
        cwd=REPO,
        check=True,
    )


def verify_cargo_inventory() -> None:
    inventory = ARTIFACTS / "cargo-package-files.txt"
    if not inventory.is_file():
        return
    paths = inventory.read_text().splitlines()
    for required in CONTRACT["cargo_required_paths"]:
        assert required in paths
    for path in paths:
        assert not any(
            path.endswith(suffix) for suffix in CONTRACT["cargo_prohibited_suffixes"]
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "extra_text_surface",
        nargs="*",
        type=Path,
        help="additional extracted Cargo or release text surface",
    )
    args = parser.parse_args()
    verify_method()
    verify_history()
    for relative in CONTRACT["current_surface_paths"]:
        scan(REPO / relative)
    for path in args.extra_text_surface:
        scan(path)
    verify_cargo_inventory()
    print("PRISM-RESIDUAL-ATTRIBUTION-CLEAR")


if __name__ == "__main__":
    main()
