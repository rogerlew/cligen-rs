#!/usr/bin/env python3
"""Materialize and authenticate a pre-submit A10M5R12R1 admission receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260719-a10m5r12r1-admission-materialization-remedy"
RUN_ID = "a10m5r12r1-admission-materialization-remedy-r0"
REMOTE_ROOT = f"/ceph/home/rogerlew.ui/.cligen-rs-a10/runs/{RUN_ID}"
REMOTE_HOST = "lemhi"
ROLES = {
    "control-materialization",
    "continuous-medium-latent-process-k2",
    "continuous-hierarchical-latent-process-k2",
}


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return value


def authenticated(value: dict[str, Any]) -> bool:
    recorded = value.get("record_sha256")
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    return isinstance(recorded, str) and recorded == hashlib.sha256(
        canonical(semantic)
    ).hexdigest()


def run(arguments: list[str], *, input_bytes: bytes | None = None) -> None:
    subprocess.run(arguments, input=input_bytes, check=True)


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def verify_published_source(source_commit: str) -> None:
    identities = {
        subprocess.run(
            ("git", "rev-parse", name),
            cwd=REPO,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        for name in ("HEAD", "origin/main")
    }
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    branch = subprocess.run(
        ("git", "branch", "--show-current"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if (
        identities != {source_commit}
        or branch != "main"
        or Path(__file__).read_bytes() != git_bytes(source_commit, relative)
    ):
        raise RuntimeError("admission materializer is not exact published main")


def parse_setups(values: list[str]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in values:
        role, separator, path = item.partition("=")
        if (
            not separator
            or not role
            or role in seen
            or role not in ROLES
            or path != f"{REMOTE_ROOT}/results/{role}/setup.json"
        ):
            raise RuntimeError(f"invalid setup binding: {item}")
        seen.add(role)
        result.append((role, path))
    return result


def verify_local_paths(
    state_path: Path, publication_dir: Path, source_commit: str
) -> dict[str, Any]:
    expected_run_root = state_path.resolve().parents[1]
    if (
        state_path.resolve() != expected_run_root / "private/state.json"
        or publication_dir.resolve() != expected_run_root / "publication"
        or expected_run_root.name != RUN_ID
    ):
        raise RuntimeError("local toolkit state/publication paths are not exact")
    state = read(state_path)
    if (
        state.get("package_id") != PACKAGE_ID
        or state.get("run_id") != RUN_ID
        or state.get("source_commit") != source_commit
        or state.get("run_state") not in {"VERIFIED", "MATRIX_ACTIVE"}
    ):
        raise RuntimeError("local toolkit state is ineligible for admission")
    return state


def current_plan(state: dict[str, Any]) -> dict[str, Any]:
    plan_id = state.get("current_plan_id")
    matches = [
        item.get("semantic")
        for item in state.get("plan_revisions", [])
        if isinstance(item, dict) and item.get("plan_id") == plan_id
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise RuntimeError("current toolkit plan is absent or ambiguous")
    return matches[0]


def verify_output_path(
    state: dict[str, Any], output: Path, role: str
) -> None:
    contract = current_plan(state).get("admission_materialization")
    expected = (
        Path(contract.get("receipt_directory", "")) / f"{role}.json"
        if isinstance(contract, dict)
        else Path("")
    )
    if not expected.is_absolute() or output.resolve() != expected.resolve():
        raise RuntimeError("local admission output path differs from frozen plan")


def reset_remote_snapshot() -> None:
    script = b"""set -eu
root=$1
expected=$2
[ "$root" = "$expected" ]
[ -d "$root" ]
snapshot=$root/admission-input
[ ! -L "$snapshot" ]
if [ -e "$snapshot" ]; then
  find "$snapshot" -mindepth 1 -delete
else
  mkdir -m 700 -- "$snapshot"
fi
mkdir -m 700 -- "$snapshot/publication"
"""
    run(
        [
            "ssh",
            "-oBatchMode=yes",
            REMOTE_HOST,
            "/bin/sh",
            "-s",
            "--",
            REMOTE_ROOT,
            REMOTE_ROOT,
        ],
        input_bytes=script,
    )


def upload_snapshot(snapshot: Path, publication_files: list[Path]) -> None:
    run(
        [
            "scp",
            "-oBatchMode=yes",
            str(snapshot / "state.json"),
            f"{REMOTE_HOST}:{REMOTE_ROOT}/admission-input/state.json",
        ]
    )
    for path in publication_files:
        run(
            [
                "scp",
                "-oBatchMode=yes",
                str(path),
                f"{REMOTE_HOST}:{REMOTE_ROOT}/admission-input/publication/{path.name}",
            ]
        )


def invoke_checker(role: str, setups: list[tuple[str, str]]) -> None:
    output = f"{REMOTE_ROOT}/admissions/{role}.json"
    absent = subprocess.run(
        [
            "ssh",
            "-oBatchMode=yes",
            REMOTE_HOST,
            "/bin/test",
            "!",
            "-e",
            output,
        ],
        check=False,
    ).returncode == 0
    if not absent:
        return
    command = [
        "ssh",
        "-oBatchMode=yes",
        REMOTE_HOST,
        "/usr/bin/python3.11",
        f"{REMOTE_ROOT}/admission_checker.py",
        "--contract",
        f"{REMOTE_ROOT}/job-local-capacity-contract.json",
        "--asset-manifest",
        f"{REMOTE_ROOT}/asset-manifest.json",
        "--toolkit-state",
        f"{REMOTE_ROOT}/admission-input/state.json",
        "--publication-dir",
        f"{REMOTE_ROOT}/admission-input/publication",
        "--remote-run-root",
        REMOTE_ROOT,
        "--role",
        role,
        "--output",
        output,
    ]
    for setup_role, setup_path in setups:
        command.extend(("--setup", f"{setup_role}={setup_path}"))
    run(command)


def fetch_and_verify(
    target: Path,
    *,
    role: str,
    state_sha256: str,
    source_commit: str,
) -> dict[str, Any]:
    run(
        [
            "scp",
            "-oBatchMode=yes",
            f"{REMOTE_HOST}:{REMOTE_ROOT}/admissions/{role}.json",
            str(target),
        ]
    )
    receipt = read(target)
    if not (
        authenticated(receipt)
        and receipt.get("schema_version") == "lemhi-toolkit-record-2"
        and receipt.get("record_type") == "a10m5r12-submission-admission"
        and isinstance(receipt.get("authority_id"), str)
        and receipt.get("package_id") == PACKAGE_ID
        and receipt.get("run_id") == RUN_ID
        and receipt.get("role") == role
        and receipt.get("attempt_index") == 0
        and receipt.get("source_commit") == source_commit
        and receipt.get("decision") == "PASS"
        and receipt.get("valid") is True
        and receipt.get("input_identities", {}).get("toolkit_state_sha256")
        == state_sha256
        and isinstance(receipt.get("gates"), dict)
        and receipt["gates"]
        and all(value is True for value in receipt["gates"].values())
    ):
        raise RuntimeError("materialized admission receipt failed authentication")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--publication-dir", type=Path, required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--setup", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    verify_published_source(options.source_commit)
    if options.role not in ROLES:
        raise RuntimeError("admission target is outside the frozen role matrix")
    state = verify_local_paths(
        options.state, options.publication_dir, options.source_commit
    )
    verify_output_path(state, options.output, options.role)
    setups = parse_setups(options.setup)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a10m5r12r1-admission-") as raw:
        snapshot = Path(raw)
        shutil.copyfile(options.state, snapshot / "state.json")
        state_sha256 = digest(snapshot / "state.json")
        publication_files: list[Path] = []
        publication_root = snapshot / "publication"
        publication_root.mkdir()
        for source in sorted(options.publication_dir.glob("job-*.json")):
            target = publication_root / source.name
            shutil.copyfile(source, target)
            publication_files.append(target)
        reset_remote_snapshot()
        upload_snapshot(snapshot, publication_files)
        if digest(options.state) != state_sha256:
            raise RuntimeError("toolkit state changed during admission snapshot")
        invoke_checker(options.role, setups)
        fetched = snapshot / "admission.json"
        receipt = fetch_and_verify(
            fetched,
            role=options.role,
            state_sha256=state_sha256,
            source_commit=options.source_commit,
        )
        if digest(options.state) != state_sha256:
            raise RuntimeError("toolkit state changed while admission was checked")
        temporary = options.output.with_name(
            f".{options.output.name}.promote-{os.getpid()}"
        )
        try:
            with temporary.open("xb") as stream:
                stream.write(fetched.read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, options.output)
        finally:
            temporary.unlink(missing_ok=True)
    print(receipt["record_sha256"])


if __name__ == "__main__":
    main()
