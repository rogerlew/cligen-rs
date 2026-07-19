#!/usr/bin/env python3
"""Verify the A10M5O1R1 evidence-token projection repair."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
hardening = (ROOT / "research/a10/lemhi_toolkit/hardening.py").read_text(encoding="utf-8")
tests = (ROOT / "research/a10/lemhi_toolkit/tests/test_hardening.py").read_text(encoding="utf-8")
adapters = (ROOT / "research/a10/lemhi_toolkit/adapters.py").read_text(encoding="utf-8")
spec = (ROOT / "docs/specifications/SPEC-LEMHI-AGENT-TOOLKIT.md").read_text(encoding="utf-8")

for fragment in (
    'SANITIZER_VERSION = "lemhi-evidence-projection-4"',
    "[[RAW_RESERVED_TOKEN:{name}]]",
    '"escaped_reserved_token_counts"',
):
    if fragment not in hardening:
        raise SystemExit(f"missing projection invariant: {fragment}")
if "test_projection_escapes_raw_reserved_tokens_before_replacement" not in tests:
    raise SystemExit("missing raw-token regression test")
if 'result["sanitization_policy"] = SANITIZER_VERSION' not in adapters:
    raise SystemExit("adapter policy label is not bound to projector version")
if "third-party placeholders" not in spec:
    raise SystemExit("missing normative third-party-placeholder rule")
print("A10M5O1R1_VERIFY_PASS")
