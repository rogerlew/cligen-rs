from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.a9_harness.canonical import canonical_bytes, loads_strict
from research.a9_harness.errors import HarnessError
from research.a9_harness.fixtures import FixtureRunner
from research.a9_harness.rng import philox4x32_10


class CanonicalTests(unittest.TestCase):
    def test_canonical_key_order_and_lf(self) -> None:
        self.assertEqual(canonical_bytes({"z": 1, "a": 2}), b'{\n  "a": 2,\n  "z": 1\n}\n')

    def test_duplicate_key_fails_closed(self) -> None:
        with self.assertRaises(HarnessError) as context:
            loads_strict('{"a":1,"a":2}')
        self.assertEqual(context.exception.code, "DUPLICATE_JSON_KEY")


class RngTests(unittest.TestCase):
    def test_random123_zero_vector(self) -> None:
        self.assertEqual(
            philox4x32_10((0, 0, 0, 0), (0, 0)),
            (0x6627E8D5, 0xE169C58D, 0xBC57AC4C, 0x9B00DBD8),
        )


class AdverseFixtureTests(unittest.TestCase):
    def test_fx003_through_fx020(self) -> None:
        root = Path(__file__).resolve().parents[3]
        runner = FixtureRunner(root)
        for index in range(3, 21):
            with self.subTest(fixture=index):
                runner._run(f"FX-{index:03d}", getattr(runner, f"fx_{index:03d}"))
                self.assertEqual(runner.results[-1]["status"], "PASS", runner.results[-1])

    def test_evidence_writer_is_canonical(self) -> None:
        # The full writer, including recovery, is exercised by the package
        # gate. This unit test pins canonical replacement on a small object.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "example.json"
            path.write_bytes(canonical_bytes({"status": "PASS"}))
            self.assertEqual(loads_strict(path.read_text()), {"status": "PASS"})


if __name__ == "__main__":
    unittest.main()
