"""Deterministic exhaustive optimizer and prospective resource governance."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .canonical import canonical_bytes, sha256_bytes
from .errors import HarnessError, require
from .log import AttemptLog


@dataclass(frozen=True)
class ResourceLimits:
    evaluations: int
    wall_seconds: float
    memory_bytes: int
    retained_bytes: int
    workers: int = 8

    def validate(self) -> None:
        require(0 < self.evaluations <= 4096, "RESOURCE_EVALUATIONS", str(self.evaluations))
        require(0.0 < self.wall_seconds <= 86400.0, "RESOURCE_WALL", str(self.wall_seconds))
        require(0 < self.memory_bytes <= 12 * 1024**3, "RESOURCE_MEMORY", str(self.memory_bytes))
        require(0 < self.retained_bytes <= 50 * 1024**3, "RESOURCE_STORAGE", str(self.retained_bytes))
        require(1 <= self.workers <= 8, "RESOURCE_WORKERS", str(self.workers))


class RetryRegistry:
    def __init__(self) -> None:
        self._retries: set[str] = set()

    def allow_infrastructure_retry(self, proposal: dict[str, Any]) -> bool:
        digest = sha256_bytes(canonical_bytes(proposal))
        if digest in self._retries:
            return False
        self._retries.add(digest)
        return True


class ExhaustiveOptimizer:
    """A deterministic proposal-order reference optimizer for harness tests."""

    optimizer_id = "a9b_deterministic_exhaustive_v1"

    def run(
        self,
        proposals: Iterable[dict[str, Any]],
        evaluator: Callable[[dict[str, Any]], dict[str, Any]],
        log: AttemptLog,
        limits: ResourceLimits,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> list[dict[str, Any]]:
        limits.validate()
        start = monotonic()
        results: list[dict[str, Any]] = []
        for index, proposal in enumerate(proposals):
            proposal_hash = sha256_bytes(canonical_bytes(proposal))
            if index >= limits.evaluations:
                record = log.append({"proposal_sha256": proposal_hash, "state": "evaluation_incomplete", "reason": "evaluation_budget_exhausted"})
                results.append(record)
                continue
            if monotonic() - start > limits.wall_seconds:
                record = log.append({"proposal_sha256": proposal_hash, "state": "evaluation_incomplete", "reason": "wall_time_exhausted"})
                results.append(record)
                continue
            try:
                evaluation = evaluator(proposal)
                require(isinstance(evaluation, dict), "EVALUATOR_RESULT_TYPE", type(evaluation).__name__)
                memory = int(evaluation.pop("memory_bytes", 0))
                retained = int(evaluation.pop("retained_bytes", 0))
                if monotonic() - start > limits.wall_seconds:
                    payload = {"proposal_sha256": proposal_hash, "state": "evaluation_incomplete", "reason": "wall_time_exhausted"}
                elif memory > limits.memory_bytes:
                    payload = {"proposal_sha256": proposal_hash, "state": "evaluation_incomplete", "reason": "memory_exhausted"}
                elif retained > limits.retained_bytes:
                    payload = {"proposal_sha256": proposal_hash, "state": "evaluation_incomplete", "reason": "storage_exhausted"}
                else:
                    state = str(evaluation.pop("state", "evaluation_complete"))
                    require(state in {"hard_infeasible", "evaluation_complete", "evaluation_incomplete", "dominated"}, "ATTEMPT_STATE", state)
                    payload = {"proposal_sha256": proposal_hash, "state": state, **evaluation}
            except HarnessError as error:
                payload = {"proposal_sha256": proposal_hash, "state": "evaluation_incomplete", "reason": error.code}
            except Exception as error:  # unexpected plugin failures are still durable typed attempts
                payload = {
                    "proposal_sha256": proposal_hash,
                    "state": "evaluation_incomplete",
                    "reason": f"unexpected_{type(error).__name__}",
                }
            record = log.append(payload)
            results.append(record)
        return results


@dataclass(frozen=True)
class RetentionDecision:
    retain_raw: bool
    require_lfs: bool
    reason: str


def retention_decision(
    *, artifact_bytes: int, artifact_kind: str, pareto_replay: bool = False
) -> RetentionDecision:
    require(artifact_bytes >= 0, "ARTIFACT_SIZE", str(artifact_bytes))
    retain = artifact_kind in {"fixture", "failure"} or pareto_replay
    reason = "registered raw evidence" if retain else "derived metrics and hashes only"
    return RetentionDecision(retain, retain and artifact_bytes >= 10 * 1024**2, reason)


def require_lfs_coverage(repo_root: Path | str, artifact_path: Path | str, decision: RetentionDecision) -> None:
    if not decision.require_lfs:
        return
    relative = Path(artifact_path).resolve().relative_to(Path(repo_root).resolve()).as_posix()
    attributes = (Path(repo_root) / ".gitattributes").read_text(encoding="utf-8")
    require(
        relative.startswith("docs/work-packages/20260715-a9b-calibration-harness/artifacts/large/")
        and "docs/work-packages/20260715-a9b-calibration-harness/artifacts/large/** filter=lfs" in attributes,
        "LFS_COVERAGE_MISSING",
        relative,
    )


def record_scratch_deletion(path: Path | str, object_sha256: str) -> dict[str, Any]:
    target = Path(path)
    existed = target.exists()
    target.unlink(missing_ok=True)
    # Evidence stores the registered logical name, not a nondeterministic
    # temporary-directory prefix from the executing host.
    return {"path": target.name, "object_sha256": object_sha256, "existed": existed, "deleted": not target.exists()}
