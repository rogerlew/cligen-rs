#!/usr/bin/env python3
"""Fail-closed structural verifier for the A10M5R4R1 scaffold."""

from __future__ import annotations

from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
DOCS = PACKAGE.parents[1]


def require(path: Path, phrases: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    for phrase in phrases:
        assert phrase in text, f"{path}: missing {phrase!r}"


def main() -> None:
    require(
        PACKAGE / "package.md",
        (
            "Status: `SCAFFOLDED`",
            "longitude, latitude, and number of years",
            "Redistributing the normals maps is acceptable",
            "A10M5R4R1-STOCHASTIC-PRISM-READY",
        ),
    )
    require(
        DOCS / "specifications/SPEC-A10-STOCHASTIC-PRISM-COMPARATOR.md",
        (
            "stochastic_prism_localized_par_v1",
            "faithful_5_32_3",
            "Generation never performs network I/O",
            "P(W/W)",
            "MX .5 P",
        ),
    )
    require(
        PACKAGE / "artifacts/wepppy-sanity-review.md",
        ("ADOPT-WITH-CORRECTIONS", "negative temperature", "mandatory"),
    )
    require(
        PACKAGE / "artifacts/prism-distribution-plan.md",
        ("Redistribute", "external payload", "explicit sync"),
    )
    print("A10M5R4R1-SCAFFOLD-VERIFIED")


if __name__ == "__main__":
    main()
