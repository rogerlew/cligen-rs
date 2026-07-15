"""Append-only hash-chained attempt records and content-addressed checkpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .canonical import canonical_bytes, finalize_self_hash, read_json, sha256_bytes, verify_self_hash, write_canonical
from .errors import HarnessError, require

ZERO_HASH = "0" * 64


class AttemptLog:
    """One immutable canonical JSON file per append-only attempt."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _paths(self) -> list[Path]:
        paths = sorted(self.directory.glob("[0-9][0-9][0-9][0-9][0-9][0-9].json"))
        unexpected = sorted(
            path.name
            for path in self.directory.iterdir()
            if path not in paths
        )
        require(not unexpected, "LOG_UNEXPECTED_ENTRY", repr(unexpected))
        return paths

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        paths = self._paths()
        sequence = len(paths)
        previous = ZERO_HASH if not paths else str(read_json(paths[-1])["record_sha256"])
        record = finalize_self_hash(
            {
                "sequence": sequence,
                "previous_sha256": previous,
                "payload": payload,
                "record_sha256": ZERO_HASH,
            },
            "record_sha256",
        )
        write_canonical(self.directory / f"{sequence:06d}.json", record, immutable=True)
        return record

    def verify(self) -> list[dict[str, Any]]:
        records = []
        previous = ZERO_HASH
        for sequence, path in enumerate(self._paths()):
            record = read_json(path)
            require(record["sequence"] == sequence, "LOG_SEQUENCE", str(path))
            require(record["previous_sha256"] == previous, "LOG_CHAIN_CORRUPT", str(path))
            verify_self_hash(record, "record_sha256")
            previous = record["record_sha256"]
            records.append(record)
        return records

    def checkpoint(self, state: dict[str, Any], checkpoint_directory: Path | str) -> Path:
        records = self.verify()
        checkpoint = {
            "attempt_count": len(records),
            "log_head_sha256": records[-1]["record_sha256"] if records else ZERO_HASH,
            "state": state,
        }
        digest = sha256_bytes(canonical_bytes(checkpoint))
        path = Path(checkpoint_directory) / f"{digest}.json"
        write_canonical(path, checkpoint, immutable=True)
        return path

    def verify_checkpoint(self, path: Path | str) -> dict[str, Any]:
        checkpoint = read_json(path)
        expected_name = f"{sha256_bytes(canonical_bytes(checkpoint))}.json"
        require(Path(path).name == expected_name, "CHECKPOINT_HASH_MISMATCH", str(path))
        records = self.verify()
        require(checkpoint["attempt_count"] == len(records), "CHECKPOINT_LOG_COUNT", str(path))
        head = records[-1]["record_sha256"] if records else ZERO_HASH
        require(checkpoint["log_head_sha256"] == head, "CHECKPOINT_LOG_HEAD", str(path))
        return checkpoint


def all_attempt_states(records: Iterable[dict[str, Any]]) -> set[str]:
    return {str(record["payload"]["state"]) for record in records}
