"""Normative records, state transitions, and safety invariants."""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import stat
import tarfile
from pathlib import Path
from typing import Any, Callable, Iterator, Protocol

SCHEMA_VERSION = "lemhi-toolkit-record-1"
PRODUCER_VERSION = "lemhi-toolkit-foundation-1"
SAFE_INTEGER = 9_007_199_254_740_991
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._+=-]{0,254}$")
HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ToolkitError(Exception):
    """A stable fail-closed toolkit error."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def require(condition: bool, code: str, detail: str) -> None:
    if not condition:
        raise ToolkitError(code, detail)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        require(key not in value, "INVALID_JSON", f"duplicate key {key!r}")
        value[key] = item
    return value


def loads_strict(text: str) -> Any:
    """Parse I-JSON while rejecting duplicate keys, floats, and constants."""

    def reject_float(value: str) -> None:
        raise ToolkitError("INVALID_JSON", f"floating number prohibited: {value}")

    def reject_constant(value: str) -> None:
        raise ToolkitError("INVALID_JSON", f"constant prohibited: {value}")

    try:
        result = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except ToolkitError:
        raise
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ToolkitError("INVALID_JSON", str(error)) from error
    validate_json_value(result)
    return result


def validate_json_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, (bool, str)):
        return
    if isinstance(value, int):
        require(abs(value) <= SAFE_INTEGER, "INVALID_JSON", f"unsafe integer at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            require(isinstance(key, str), "INVALID_JSON", f"non-string key at {path}")
            validate_json_value(item, f"{path}.{key}")
        return
    raise ToolkitError("INVALID_JSON", f"unsupported {type(value).__name__} at {path}")


def _utf16_key(value: str) -> bytes:
    return value.encode("utf-16-be", "surrogatepass")


def _jcs_text(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_jcs_text(item) for item in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda item: _utf16_key(item[0]))
        return "{" + ",".join(f"{_jcs_text(key)}:{_jcs_text(item)}" for key, item in items) + "}"
    raise ToolkitError("INVALID_JSON", f"unsupported {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return RFC-8785 bytes for the specification's integer-only I-JSON subset."""

    validate_json_value(value)
    try:
        return _jcs_text(value).encode("utf-8")
    except UnicodeEncodeError as error:
        raise ToolkitError("INVALID_JSON", "unpaired Unicode surrogate") from error


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise ToolkitError("ASSET_IDENTITY_MISMATCH", f"{path}: {error}") from error
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = loads_strict(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ToolkitError("EVIDENCE_INCOMPLETE", f"{path}: {error}") from error
    require(isinstance(value, dict), "INVALID_JSON", f"{path}: object required")
    return value


def read_record(path: Path) -> dict[str, Any]:
    """Read and authenticate a revision-1 publication record without rewriting it."""

    value = read_json(path)
    require(value.get("schema_version") == SCHEMA_VERSION, "EVIDENCE_INCOMPLETE", "unsupported record major version")
    recorded = value.get("record_sha256")
    require(isinstance(recorded, str) and HEX64_PATTERN.fullmatch(recorded) is not None, "EVIDENCE_INCOMPLETE", "record hash missing")
    semantic = dict(value)
    semantic.pop("record_sha256")
    require(sha256_bytes(canonical_bytes(semantic)) == recorded, "EVIDENCE_INCOMPLETE", "record hash mismatch")
    return value


def atomic_write(path: Path, value: Any, *, private: bool = False) -> str:
    data = canonical_bytes(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700 if private else 0o755)
    require(not path.parent.is_symlink(), "ALLOWLIST_VIOLATION", f"symlink state directory: {path.parent}")
    if private:
        os.chmod(path.parent, 0o700)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("xb") as stream:
            if private:
                os.chmod(temporary, 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise ToolkitError("EVIDENCE_INCOMPLETE", f"cannot write {path}: {error}") from error
    return sha256_bytes(data)


def validate_id(value: Any, field: str) -> str:
    require(isinstance(value, str), "AUTHORITY_INVALID", f"{field} must be a string")
    require(ID_PATTERN.fullmatch(value) is not None, "AUTHORITY_INVALID", f"unsafe {field}")
    return value


def validate_relative_path(value: Any, field: str) -> str:
    require(isinstance(value, str) and value, "ALLOWLIST_VIOLATION", f"{field} missing")
    require(not value.startswith("/"), "ALLOWLIST_VIOLATION", f"absolute {field}")
    parts = value.split("/")
    require(
        all(SEGMENT_PATTERN.fullmatch(part) is not None and part not in {".", ".."} for part in parts),
        "ALLOWLIST_VIOLATION",
        f"unsafe {field}",
    )
    return value


def validate_shell_scalar(value: Any, field: str) -> str:
    require(isinstance(value, str) and value, "ALLOWLIST_VIOLATION", f"{field} missing")
    require(not value.startswith("-"), "ALLOWLIST_VIOLATION", f"option-like {field}")
    require(not any(ord(char) < 32 or ord(char) == 127 for char in value), "ALLOWLIST_VIOLATION", field)
    require(re.fullmatch(r"[A-Za-z0-9_./+=:@,-]+", value) is not None, "ALLOWLIST_VIOLATION", field)
    return value


def validate_record_text(value: Any, field: str, *, maximum_length: int = 500) -> str:
    require(isinstance(value, str) and 0 < len(value) <= maximum_length, "AUTHORITY_INVALID", field)
    require(not any(ord(char) < 32 or ord(char) == 127 for char in value), "AUTHORITY_INVALID", field)
    return value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_allowed_file(path: Path, allowed_roots: list[Path]) -> Path:
    require(path.is_absolute(), "ALLOWLIST_VIOLATION", "asset path must be absolute")
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as error:
        raise ToolkitError("ASSET_IDENTITY_MISMATCH", f"{path}: {error}") from error
    matching = [root for root in allowed_roots if _is_relative_to(resolved, root.resolve())]
    require(matching, "ALLOWLIST_VIOLATION", str(path))
    allowed = matching[0]
    try:
        relative = path.relative_to(allowed)
        cursor = allowed
    except ValueError:
        relative = resolved.relative_to(allowed.resolve())
        cursor = allowed.resolve()
    for part in relative.parts:
        cursor = cursor / part
        require(not cursor.is_symlink(), "ALLOWLIST_VIOLATION", f"symlink component: {path}")
    require(stat.S_ISREG(metadata.st_mode), "ALLOWLIST_VIOLATION", f"nonregular asset: {path}")
    require(metadata.st_nlink == 1, "ALLOWLIST_VIOLATION", f"hardlinked asset: {path}")
    return resolved


def validate_archive(
    path: Path,
    *,
    max_files: int,
    max_bytes: int,
    allowed_members: set[str] | None = None,
) -> list[tarfile.TarInfo]:
    """Inspect an archive without extracting or observing member content."""

    try:
        archive = tarfile.open(path, mode="r:*")
    except (OSError, tarfile.TarError) as error:
        raise ToolkitError("ARCHIVE_UNSAFE", f"cannot inspect {path.name}") from error
    with archive:
        members = archive.getmembers()
        require(len(members) <= max_files, "ARCHIVE_UNSAFE", "archive file ceiling")
        total = 0
        for member in members:
            name = member.name
            require(not name.startswith("/"), "ARCHIVE_UNSAFE", "absolute member")
            try:
                validate_relative_path(name.rstrip("/"), "archive member")
            except ToolkitError as error:
                raise ToolkitError("ARCHIVE_UNSAFE", "unsafe member path") from error
            if member.isfile() and allowed_members is not None:
                require(name in allowed_members, "ARCHIVE_UNSAFE", "member is not allowlisted")
            require(member.isfile() or member.isdir(), "ARCHIVE_UNSAFE", "nonregular member")
            require(member.uid == 0 and member.gid == 0, "ARCHIVE_UNSAFE", "unexpected ownership")
            require(member.mode & 0o6000 == 0, "ARCHIVE_UNSAFE", "setid member")
            if member.isfile():
                total += member.size
                require(total <= max_bytes, "ARCHIVE_UNSAFE", "archive expansion ceiling")
        return members


def extract_validated_archive(
    path: Path,
    destination: Path,
    *,
    max_files: int,
    max_bytes: int,
    allowed_members: set[str] | None = None,
) -> None:
    """Extract only members already accepted by :func:`validate_archive`."""

    members = validate_archive(path, max_files=max_files, max_bytes=max_bytes, allowed_members=allowed_members)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    with tarfile.open(path, mode="r:*") as archive:
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o700)
                continue
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            source = archive.extractfile(member)
            require(source is not None, "ARCHIVE_UNSAFE", "missing member content")
            with source, target.open("xb") as stream:
                os.chmod(target, 0o600)
                shutil.copyfileobj(source, stream)


@contextlib.contextmanager
def directory_lock(path: Path) -> Iterator[None]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.mkdir(mode=0o700)
    except FileExistsError as error:
        raise ToolkitError("RUN_LOCKED", str(path)) from error
    try:
        yield
    finally:
        try:
            path.rmdir()
        except FileNotFoundError:
            pass


class Adapter(Protocol):
    def check_masters(self, profile: dict[str, Any]) -> None: ...
    def probe(self, profile: dict[str, Any]) -> dict[str, Any]: ...
    def stage(self, profile: dict[str, Any], plan: dict[str, Any], assets: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
    def verify(self, profile: dict[str, Any], plan: dict[str, Any], assets: list[dict[str, Any]]) -> None: ...
    def submit(self, profile: dict[str, Any], plan: dict[str, Any], job: dict[str, Any], token: str) -> str: ...
    def reconcile(self, profile: dict[str, Any], token: str) -> list[str]: ...
    def observe(self, profile: dict[str, Any], plan: dict[str, Any], job: dict[str, Any], job_id: str) -> dict[str, Any]: ...
    def cancel(self, profile: dict[str, Any], job_id: str) -> dict[str, Any]: ...
    def collect(self, profile: dict[str, Any], plan: dict[str, Any], quarantine: Path) -> dict[str, Any]: ...
    def clean(self, profile: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]: ...


RUN_STATES = [
    "AUTHORITY_CHECKED",
    "DISCOVERED",
    "PLANNED",
    "PREPARED",
    "STAGED",
    "VERIFIED",
    "MATRIX_ACTIVE",
    "MATRIX_SETTLED",
    "COLLECTED",
    "CLEANED",
    "CLOSED",
]
TERMINAL_JOB_STATES = {
    "BOOT_FAIL",
    "CANCELLED",
    "COMPLETED",
    "DEADLINE",
    "FAILED",
    "NODE_FAIL",
    "OUT_OF_MEMORY",
    "PREEMPTED",
    "REVOKED",
    "TIMEOUT",
}


class Toolkit:
    """Stateful controller whose side effects are delegated to an adapter."""

    def __init__(
        self,
        state_root: Path,
        authority: dict[str, Any],
        profile: dict[str, Any],
        run_id: str,
        adapter: Adapter,
        *,
        clock: Callable[[], str] | None = None,
        provider_root: Path | None = None,
    ):
        self.state_root = state_root.resolve()
        self.authority = authority
        self.profile = profile
        self.run_id = validate_id(run_id, "run_id")
        self.adapter = adapter
        self.clock = clock or (lambda: dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"))
        self.provider_root = (provider_root or Path.cwd()).resolve()
        require(not _is_relative_to(self.state_root, self.provider_root), "AUTHORITY_INVALID", "private state root must be outside repository")
        self.authority_id = validate_id(authority.get("authority_id"), "authority_id")
        self.budget_id = validate_id(authority.get("resource_budget_id"), "resource_budget_id")
        self.package_id = validate_id(authority.get("package_id"), "package_id")
        self.source_commit = validate_shell_scalar(authority.get("source_commit"), "source_commit")
        require(re.fullmatch(r"[0-9a-f]{7,40}", self.source_commit) is not None, "AUTHORITY_INVALID", "source_commit")
        ceiling = authority.get("resource_ceiling_gpu_minutes")
        require(isinstance(ceiling, int) and ceiling >= 0, "AUTHORITY_INVALID", "resource ceiling")
        allowlist = authority.get("allowed_roots")
        require(isinstance(allowlist, list) and allowlist, "AUTHORITY_INVALID", "allowed_roots")
        self.allowed_roots = [Path(item).absolute() for item in allowlist if isinstance(item, str)]
        require(len(self.allowed_roots) == len(allowlist), "AUTHORITY_INVALID", "allowed_roots")
        for root in self.allowed_roots:
            resolved_root = root.resolve()
            require(resolved_root != Path(resolved_root.anchor), "AUTHORITY_INVALID", "filesystem root cannot be allowlisted")
        self.authority_sha256 = sha256_bytes(canonical_bytes(authority))
        self.profile_sha256 = sha256_bytes(canonical_bytes(profile))

    @property
    def run_dir(self) -> Path:
        return self.state_root / "runs" / self.run_id

    @property
    def private_path(self) -> Path:
        return self.run_dir / "private" / "state.json"

    @property
    def publication_dir(self) -> Path:
        return self.run_dir / "publication"

    @property
    def run_lock(self) -> Path:
        return self.run_dir / ".run.lock"

    @property
    def budget_dir(self) -> Path:
        return self.state_root / "authorities" / self.budget_id

    @property
    def budget_lock(self) -> Path:
        return self.budget_dir / ".budget.lock"

    @property
    def ledger_path(self) -> Path:
        return self.budget_dir / "ledger.json"

    def _common(self, record_type: str, *, plan_id: str | None = None) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "record_type": record_type,
            "authority_id": self.authority_id,
            "run_id": self.run_id,
            "package_id": self.package_id,
            "source_commit": self.source_commit,
            "created_at": self.clock(),
            "producer_version": PRODUCER_VERSION,
        }
        if plan_id is not None:
            value["plan_id"] = plan_id
        return value

    def _finalize(self, value: dict[str, Any]) -> dict[str, Any]:
        result = dict(value)
        result["record_sha256"] = sha256_bytes(canonical_bytes(result))
        return result

    def _write_publication(self, name: str, value: dict[str, Any]) -> str:
        return atomic_write(self.publication_dir / name, self._finalize(value))

    def _load_state(self) -> dict[str, Any]:
        require(self.private_path.exists(), "AUTHORITY_INVALID", "run is not initialized")
        return read_json(self.private_path)

    def _save_state(self, state: dict[str, Any]) -> None:
        atomic_write(self.private_path, state, private=True)

    def _event(
        self,
        state: dict[str, Any],
        from_state: str,
        to_state: str,
        *,
        scope: str = "run",
        plan_id: str | None = None,
        job_role: str | None = None,
        attempt_index: int | None = None,
    ) -> None:
        events = state.setdefault("events", [])
        event = self._common("transition_event", plan_id=plan_id)
        input_hashes = [self.authority_sha256, self.profile_sha256]
        capability = state.get("capability_receipt")
        if isinstance(capability, dict) and isinstance(capability.get("record_sha256"), str):
            input_hashes.append(capability["record_sha256"])
        if plan_id is not None:
            input_hashes.append(plan_id)
        event.update({
            "transition_scope": scope,
            "from_state": from_state,
            "to_state": to_state,
            "input_record_hashes": sorted(set(input_hashes)),
            "result_record_hashes": [],
        })
        if scope == "attempt":
            event.update({"job_role": job_role, "attempt_index": attempt_index})
        events.append(self._finalize(event))

    def _require_state(self, state: dict[str, Any], expected: set[str]) -> None:
        require(state.get("run_state") in expected, "PLAN_DRIFT", f"state {state.get('run_state')} not in {sorted(expected)}")

    def doctor(self) -> dict[str, Any]:
        with directory_lock(self.run_lock):
            if self.private_path.exists():
                state = self._load_state()
                require(state.get("run_state") == "AUTHORITY_CHECKED", "PLAN_DRIFT", "doctor already passed")
                return state
            self.adapter.check_masters(self.profile)
            state = {
                "authority_id": self.authority_id,
                "resource_budget_id": self.budget_id,
                "run_id": self.run_id,
                "package_id": self.package_id,
                "source_commit": self.source_commit,
                "authority_sha256": self.authority_sha256,
                "cluster_profile_sha256": self.profile_sha256,
                "run_state": "AUTHORITY_CHECKED",
                "plan_revisions": [],
                "attempts": {},
                "events": [],
            }
            self._event(state, "UNINITIALIZED", "AUTHORITY_CHECKED")
            self._save_state(state)
            receipt = self._common("doctor_receipt")
            receipt["status"] = "PASS"
            self._write_publication("doctor.json", receipt)
            return state

    def probe(self) -> dict[str, Any]:
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"AUTHORITY_CHECKED", "DISCOVERED"})
            prior = state["run_state"]
            facts = self.adapter.probe(self.profile)
            require(facts.get("scope") in {"control", "login"}, "CAPABILITY_SCOPE_MISMATCH", "probe must not allocate")
            receipt = self._common("capability_receipt")
            receipt.update(facts)
            receipt["maximum_planning_age_seconds"] = self.profile.get("capability_max_age_seconds", 300)
            self._event(state, prior, "DISCOVERED")
            state["run_state"] = "DISCOVERED"
            state["capability_receipt"] = self._finalize(receipt)
            self._save_state(state)
            self._write_publication("capability.json", receipt)
            return receipt

    def _load_providers(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        providers = plan.get("providers")
        require(isinstance(providers, list) and providers, "PROVIDER_UNAVAILABLE", "providers")
        loaded: list[dict[str, Any]] = []
        capabilities = dict(self.profile.get("provides", {}))
        for relative in providers:
            relative_path = validate_relative_path(relative, "provider path")
            path = validate_allowed_file(self.provider_root / relative_path, [self.provider_root])
            provider = read_json(path)
            require(provider.get("provider_api_version") == 1, "PROVIDER_UNAVAILABLE", str(path))
            required_fields = {
                "provider_class",
                "name",
                "implementation_version",
                "supported_platforms",
                "required_commands",
                "network_phase",
                "consumes_probe_fields",
                "emits_probe_fields",
                "operations",
                "side_effect_classes",
                "failure_codes",
                "does_not_establish",
            }
            require(required_fields <= provider.keys(), "PROVIDER_UNAVAILABLE", f"incomplete provider {path}")
            validate_id(provider.get("name"), "provider name")
            require(provider.get("provider_class") in {"runtime", "framework", "transport", "scheduler", "storage", "accelerator"}, "PROVIDER_UNAVAILABLE", str(path))
            require(isinstance(provider.get("supported_platforms"), list) and self.profile.get("platform") in provider["supported_platforms"], "PLATFORM_MISMATCH", str(path))
            requirements = provider.get("requires", {})
            provides = provider.get("provides", {})
            require(isinstance(requirements, dict) and isinstance(provides, dict), "PROVIDER_UNAVAILABLE", str(path))
            for key, required in requirements.items():
                require(capabilities.get(key) == required, "PLATFORM_MISMATCH", f"{provider.get('name')} requires {key}={required}")
            for key, provided in provides.items():
                require(key not in capabilities or capabilities[key] == provided, "PLATFORM_MISMATCH", f"{provider.get('name')} conflicts on {key}")
            capabilities.update(provides)
            loaded.append(provider)
            loaded[-1]["definition_sha256"] = sha256_file(path)
        return loaded

    def _semantic_plan(self, plan_input: dict[str, Any], providers: list[dict[str, Any]]) -> dict[str, Any]:
        semantic = dict(plan_input)
        semantic.pop("created_at", None)
        semantic["cluster_profile_sha256"] = self.profile_sha256
        semantic["provider_stack"] = [
            {
                "name": provider["name"],
                "provider_api_version": provider["provider_api_version"],
                "implementation_version": provider["implementation_version"],
                "definition_sha256": provider["definition_sha256"],
                "selection_reason": "explicit-plan-order",
            }
            for provider in providers
        ]
        return semantic

    @staticmethod
    def _validate_jobs(jobs: Any, logical_assets: set[str], evidence_allowlist: set[str]) -> set[str]:
        require(isinstance(jobs, list) and jobs, "PLAN_DRIFT", "jobs")
        roles: set[str] = set()
        for job in jobs:
            require(isinstance(job, dict), "PLAN_DRIFT", "job")
            role = validate_id(job.get("role"), "job role")
            require(role not in roles, "PLAN_DRIFT", f"duplicate role {role}")
            roles.add(role)
            validate_relative_path(job.get("script"), "job script")
            require(job["script"] in logical_assets, "PLAN_DRIFT", "job script is not a frozen asset")
            validate_id(job.get("partition"), "partition")
            require(isinstance(job.get("gres"), str) and re.fullmatch(r"[A-Za-z0-9_]+:[A-Za-z0-9_]+:[1-9][0-9]*", job["gres"]) is not None, "PLAN_DRIFT", "job gres")
            for field in ("cpus", "memory_mb", "gpus", "time_limit_minutes"):
                require(isinstance(job.get(field), int) and job[field] > 0, "PLAN_DRIFT", f"job {field}")
            require(isinstance(job.get("max_attempts"), int) and job["max_attempts"] > 0, "PLAN_DRIFT", "job max_attempts")
            require(isinstance(job.get("expected_exit_code", 0), int) and 0 <= job.get("expected_exit_code", 0) <= 255, "PLAN_DRIFT", "expected exit code")
            retry_on = job.get("retry_on", [])
            require(isinstance(retry_on, list) and all(isinstance(item, str) for item in retry_on), "PLAN_DRIFT", "retry classes")
            require(len(set(retry_on)) == len(retry_on), "PLAN_DRIFT", "duplicate retry classes")
            require(set(retry_on) <= {"cancelled", "gate-failed", "scheduler-failure"}, "PLAN_DRIFT", "retry classes")
            require(job["max_attempts"] == 1 or retry_on, "PLAN_DRIFT", "retries require classes")
            gate_receipt = validate_relative_path(job.get("gate_receipt"), "gate receipt")
            require(gate_receipt in evidence_allowlist, "PLAN_DRIFT", "gate receipt is not evidence-allowlisted")
        return roles

    def plan(self, plan_input: dict[str, Any]) -> str:
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"DISCOVERED"})
            require(plan_input.get("authority_id") == self.authority_id, "AUTHORITY_INVALID", "authority_id")
            require(plan_input.get("resource_budget_id") == self.budget_id, "AUTHORITY_INVALID", "resource_budget_id")
            require(plan_input.get("run_id") == self.run_id, "AUTHORITY_INVALID", "run_id")
            require(plan_input.get("package_id") == self.package_id, "AUTHORITY_INVALID", "package_id")
            require(plan_input.get("source_commit") == self.source_commit, "AUTHORITY_INVALID", "source_commit")
            require(plan_input.get("required_capability_scope", "login") == "login", "CAPABILITY_SCOPE_MISMATCH", "compute proof requires a planned job")
            receipt = state.get("capability_receipt")
            require(isinstance(receipt, dict), "CAPABILITY_STALE", "capability receipt missing")
            try:
                captured = dt.datetime.fromisoformat(str(receipt["created_at"]).replace("Z", "+00:00"))
                now = dt.datetime.fromisoformat(self.clock().replace("Z", "+00:00"))
            except (KeyError, TypeError, ValueError) as error:
                raise ToolkitError("CAPABILITY_STALE", "invalid capability timestamp") from error
            age = (now - captured).total_seconds()
            require(0 <= age <= receipt["maximum_planning_age_seconds"], "CAPABILITY_STALE", "probe again")
            confirmation = plan_input.get("confirmation_classification")
            require(confirmation in {"none", "development-only", "confirmation-authorized"}, "AUTHORITY_INVALID", "confirmation")
            require(confirmation == self.authority.get("confirmation_classification"), "AUTHORITY_INVALID", "confirmation authority")
            target_platform = plan_input.get("target_platform")
            require(target_platform == receipt.get("platform"), "PLATFORM_MISMATCH", "live login platform differs from plan")
            require(target_platform == self.profile.get("platform"), "PLATFORM_MISMATCH", "cluster profile differs from plan")
            validate_relative_path(plan_input.get("remote_run_root"), "remote_run_root")
            require(plan_input["remote_run_root"] == f"runs/{self.run_id}", "CLEANUP_TARGET_INVALID", "run root must be runs/<run_id>")
            providers = self._load_providers(plan_input)
            evidence_allowlist = plan_input.get("evidence_allowlist")
            require(isinstance(evidence_allowlist, list) and evidence_allowlist, "AUTHORITY_INVALID", "evidence allowlist")
            validated_evidence = [validate_relative_path(item, "evidence allowlist") for item in evidence_allowlist]
            require(len(set(validated_evidence)) == len(validated_evidence), "AUTHORITY_INVALID", "duplicate evidence allowlist")
            assets = plan_input.get("assets")
            require(isinstance(assets, list) and assets, "PLAN_DRIFT", "assets")
            logical_assets: set[str] = set()
            for asset in assets:
                require(isinstance(asset, dict), "PLAN_DRIFT", "asset")
                logical = validate_relative_path(asset.get("logical_name"), "asset logical_name")
                require(logical not in logical_assets, "PLAN_DRIFT", "duplicate asset logical name")
                logical_assets.add(logical)
                require(isinstance(asset.get("local_path"), str) and Path(asset["local_path"]).is_absolute(), "ALLOWLIST_VIOLATION", "asset path must be absolute")
                require(isinstance(asset.get("bytes"), int) and asset["bytes"] >= 0, "ASSET_IDENTITY_MISMATCH", logical)
                require(isinstance(asset.get("sha256"), str) and HEX64_PATTERN.fullmatch(asset["sha256"]) is not None, "ASSET_IDENTITY_MISMATCH", logical)
                require(asset.get("source_class") in {"repository-owned", "external-redistributable"}, "AUTHORITY_INVALID", "asset source class")
                require(isinstance(asset.get("license_provenance"), str) and asset["license_provenance"], "AUTHORITY_INVALID", "asset license provenance")
                require(asset.get("target_platform", target_platform) == target_platform, "PLATFORM_MISMATCH", "asset target platform")
            jobs = plan_input.get("jobs")
            require(plan_input.get("job_local_cleanup") in {"scheduler_purged", "toolkit_recoverable"}, "PLAN_DRIFT", "job-local cleanup contract")
            require(plan_input.get("submission_mode") == "operator-explicit", "PLAN_DRIFT", "submission mode")
            require(
                plan_input.get("stop_rules") == {
                    "ambiguity": "stop",
                    "gate_failure": "authorized-retry-only",
                    "resource_ceiling": "stop",
                },
                "PLAN_DRIFT",
                "stop rules",
            )
            roles = self._validate_jobs(jobs, logical_assets, set(validated_evidence))
            semantic = self._semantic_plan(plan_input, providers)
            plan_id = sha256_bytes(canonical_bytes(semantic))
            revision = {"revision": 0, "plan_id": plan_id, "semantic": semantic}
            self._event(state, "DISCOVERED", "PLANNED", plan_id=plan_id)
            state["run_state"] = "PLANNED"
            state["current_plan_id"] = plan_id
            state["plan_revisions"] = [revision]
            self._save_state(state)
            public = self._common("run_plan_receipt", plan_id=plan_id)
            public.update({
                "revision": 0,
                "provider_ids": [provider["name"] for provider in providers],
                "job_roles": sorted(roles),
                "confirmation_classification": confirmation,
                "remote_run_root_hash": sha256_bytes(plan_input["remote_run_root"].encode()),
                "cluster_profile_sha256": self.profile_sha256,
                "provider_stack": semantic["provider_stack"],
            })
            self._write_publication("plan.json", public)
            return plan_id

    def _current_plan(self, state: dict[str, Any]) -> dict[str, Any]:
        current = state.get("current_plan_id")
        for revision in state.get("plan_revisions", []):
            if revision.get("plan_id") == current:
                return revision["semantic"]
        raise ToolkitError("PLAN_DRIFT", "current plan missing")

    def amend(self, replacement: dict[str, Any], reason: str, changed_fields: list[str]) -> str:
        require(isinstance(reason, str) and 0 < len(reason) <= 500 and not any(ord(char) < 32 for char in reason), "AUTHORITY_INVALID", "amendment reason")
        authorized_fields = {validate_id(field, "changed field") for field in changed_fields}
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"VERIFIED", "MATRIX_ACTIVE"})
            prior = self._current_plan(state)
            require(replacement.get("authority_id") == self.authority_id, "AUTHORITY_INVALID", "amend authority")
            require(replacement.get("resource_budget_id") == self.budget_id, "AUTHORITY_INVALID", "amend budget")
            for field in (
                "run_id",
                "package_id",
                "source_commit",
                "confirmation_classification",
                "remote_run_root",
                "assets",
                "target_platform",
                "required_capability_scope",
                "evidence_allowlist",
                "job_local_cleanup",
                "submission_mode",
                "stop_rules",
            ):
                require(replacement.get(field) == prior.get(field), "PLAN_DRIFT", f"immutable field changed: {field}")
            self._validate_jobs(
                replacement.get("jobs"),
                {asset["logical_name"] for asset in prior["assets"]},
                set(prior["evidence_allowlist"]),
            )
            attempts = state.get("attempts", {})
            started_roles = {item["job_role"] for item in attempts.values() if item.get("state") != "REGISTERED"}
            prior_jobs = {item["role"]: item for item in prior.get("jobs", [])}
            next_jobs = {item["role"]: item for item in replacement.get("jobs", [])}
            for role in started_roles:
                require(prior_jobs.get(role) == next_jobs.get(role), "PLAN_DRIFT", f"started role changed: {role}")
            providers = self._load_providers(replacement)
            semantic = self._semantic_plan(replacement, providers)
            actual_changes = {key for key in set(prior) | set(semantic) if prior.get(key) != semantic.get(key)}
            actual_changes.discard("provider_stack")
            require(actual_changes and actual_changes <= authorized_fields, "PLAN_DRIFT", "amendment changed unauthorized fields")
            plan_id = sha256_bytes(canonical_bytes(semantic))
            require(plan_id != state["current_plan_id"], "PLAN_DRIFT", "amendment has no semantic change")
            revision = {
                "revision": len(state["plan_revisions"]),
                "plan_id": plan_id,
                "supersedes_plan_id": state["current_plan_id"],
                "reason": reason,
                "authorized_changed_fields": sorted(authorized_fields),
                "retained_attempt_keys": sorted(attempts),
                "retained_record_hashes": sorted(
                    value["record_sha256"]
                    for path in self.publication_dir.glob("job-*.json")
                    for value in [read_record(path)]
                ),
                "semantic": semantic,
            }
            state["plan_revisions"].append(revision)
            state["current_plan_id"] = plan_id
            self._save_state(state)
            receipt = self._common("plan_amendment_receipt", plan_id=plan_id)
            receipt.update({key: revision[key] for key in revision if key != "semantic"})
            self._write_publication(f"plan-amendment-{revision['revision']}.json", receipt)
            return plan_id

    def prepare(self) -> list[dict[str, Any]]:
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"PLANNED"})
            plan = self._current_plan(state)
            prepared: list[dict[str, Any]] = []
            for asset in plan.get("assets", []):
                require(isinstance(asset, dict), "PLAN_DRIFT", "asset")
                logical = validate_relative_path(asset.get("logical_name"), "asset logical_name")
                path = validate_allowed_file(Path(asset.get("local_path", "")), self.allowed_roots)
                size = path.stat().st_size
                digest = sha256_file(path)
                require(asset["bytes"] == size and asset["sha256"] == digest, "ASSET_IDENTITY_MISMATCH", logical)
                prepared.append({
                    "logical_name": logical,
                    "local_path": str(path),
                    "bytes": size,
                    "sha256": digest,
                    "source_class": asset["source_class"],
                    "license_provenance": validate_record_text(asset["license_provenance"], "license provenance"),
                })
            self._event(state, "PLANNED", "PREPARED", plan_id=state["current_plan_id"])
            state["run_state"] = "PREPARED"
            state["prepared_assets"] = prepared
            self._save_state(state)
            receipt = self._common("prepare_receipt", plan_id=state["current_plan_id"])
            receipt["assets"] = [
                {key: item[key] for key in ("logical_name", "bytes", "sha256", "source_class", "license_provenance")}
                for item in prepared
            ]
            self._write_publication("prepare.json", receipt)
            return prepared

    def stage(self) -> list[dict[str, Any]]:
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"PREPARED"})
            receipts = self.adapter.stage(self.profile, self._current_plan(state), state["prepared_assets"])
            require(isinstance(receipts, list) and len(receipts) == len(state["prepared_assets"]), "TRANSFER_INCOMPLETE", "receipt count")
            for prepared, receipt in zip(state["prepared_assets"], receipts):
                require(receipt.get("logical_name") == prepared["logical_name"], "TRANSFER_INCOMPLETE", "logical identity")
                require(receipt.get("bytes") == prepared["bytes"], "TRANSFER_INCOMPLETE", "byte identity")
                require(receipt.get("sha256") == prepared["sha256"], "TRANSFER_INCOMPLETE", "hash identity")
                require(receipt.get("promoted") is True, "TRANSFER_INCOMPLETE", "partial not promoted")
            self._event(state, "PREPARED", "STAGED", plan_id=state["current_plan_id"])
            state["run_state"] = "STAGED"
            state["transfer_receipts"] = receipts
            self._save_state(state)
            receipt = self._common("stage_receipt", plan_id=state["current_plan_id"])
            receipt["assets"] = receipts
            self._write_publication("stage.json", receipt)
            return receipts

    def verify(self) -> None:
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"STAGED"})
            self.adapter.verify(self.profile, self._current_plan(state), state["prepared_assets"])
            self._event(state, "STAGED", "VERIFIED", plan_id=state["current_plan_id"])
            state["run_state"] = "VERIFIED"
            self._save_state(state)
            receipt = self._common("verify_receipt", plan_id=state["current_plan_id"])
            receipt["status"] = "PASS"
            self._write_publication("verify.json", receipt)

    def _load_ledger(self) -> dict[str, Any]:
        if self.ledger_path.exists():
            ledger = read_json(self.ledger_path)
            require(ledger.get("resource_budget_id") == self.budget_id, "AUTHORITY_INVALID", "ledger budget identity")
            require(ledger.get("authority_id") == self.authority_id, "AUTHORITY_INVALID", "ledger authority identity")
            require(ledger.get("ceiling_gpu_minutes") == self.authority["resource_ceiling_gpu_minutes"], "AUTHORITY_INVALID", "ledger ceiling drift")
            return ledger
        return {
            "authority_id": self.authority_id,
            "resource_budget_id": self.budget_id,
            "ceiling_gpu_minutes": self.authority["resource_ceiling_gpu_minutes"],
            "entries": [],
        }

    def _save_ledger(self, ledger: dict[str, Any]) -> None:
        atomic_write(self.ledger_path, ledger, private=True)

    @staticmethod
    def _reserved_total(ledger: dict[str, Any]) -> int:
        latest: dict[str, dict[str, Any]] = {}
        for item in ledger["entries"]:
            latest[item["token"]] = item
        return sum(item["requested_gpu_minutes"] for item in latest.values() if item["status"] in {"reserved", "submitted", "settled", "ambiguous"})

    @staticmethod
    def _append_ledger_transition(ledger: dict[str, Any], token: str, status: str, **updates: Any) -> None:
        prior = next((item for item in reversed(ledger["entries"]) if item["token"] == token), None)
        require(prior is not None, "AUTHORITY_INVALID", "ledger token missing")
        event = dict(prior)
        event.update(updates)
        event["status"] = status
        event["sequence"] = len(ledger["entries"])
        ledger["entries"].append(event)

    def submit(self, job_role: str, attempt_index: int) -> str:
        job_role = validate_id(job_role, "job role")
        require(isinstance(attempt_index, int) and attempt_index >= 0, "PLAN_DRIFT", "attempt index")
        self.adapter.check_masters(self.profile)
        with directory_lock(self.budget_lock):
            with directory_lock(self.run_lock):
                state = self._load_state()
                self._require_state(state, {"VERIFIED", "MATRIX_ACTIVE"})
                plan = self._current_plan(state)
                jobs = {item["role"]: item for item in plan.get("jobs", [])}
                require(job_role in jobs, "PLAN_DRIFT", f"unknown role {job_role}")
                job = jobs[job_role]
                require(attempt_index < job["max_attempts"], "RESOURCE_CEILING", "attempt not authorized")
                key = f"{job_role}.{attempt_index}"
                attempts = state.setdefault("attempts", {})
                require(key not in attempts, "PLAN_DRIFT", f"attempt exists: {key}")
                if attempt_index > 0:
                    prior_attempt = attempts.get(f"{job_role}.{attempt_index - 1}")
                    require(isinstance(prior_attempt, dict) and prior_attempt.get("state") == "RESULT_VALIDATED", "PLAN_DRIFT", "retry predecessor is not settled")
                    require(prior_attempt.get("passed") is False, "PLAN_DRIFT", "successful attempt cannot retry")
                    prior_result = prior_attempt["result"]
                    if prior_result.get("state") == "CANCELLED":
                        retry_class = "cancelled"
                    elif prior_result.get("state") != "COMPLETED":
                        retry_class = "scheduler-failure"
                    else:
                        retry_class = "gate-failed"
                    require(retry_class in job.get("retry_on", []), "PLAN_DRIFT", f"retry class not authorized: {retry_class}")
                requested = job["gpus"] * job["time_limit_minutes"]
                ledger = self._load_ledger()
                require(self._reserved_total(ledger) + requested <= ledger["ceiling_gpu_minutes"], "RESOURCE_CEILING", key)
                token = sha256_bytes(f"{self.authority_id}:{state['current_plan_id']}:{job_role}:{attempt_index}".encode())[:32]
                entry = {
                    "authority_id": self.authority_id,
                    "run_id": self.run_id,
                    "plan_id": state["current_plan_id"],
                    "job_role": job_role,
                    "attempt_index": attempt_index,
                    "token": token,
                    "requested_gpu_minutes": requested,
                    "status": "reserved",
                    "sequence": len(ledger["entries"]),
                }
                ledger["entries"].append(entry)
                self._save_ledger(ledger)
                prior = state["run_state"]
                attempts[key] = {"job_role": job_role, "attempt_index": attempt_index, "state": "REGISTERED", "token": token, "plan_id": state["current_plan_id"]}
                self._event(state, "UNREGISTERED", "REGISTERED", scope="attempt", plan_id=state["current_plan_id"], job_role=job_role, attempt_index=attempt_index)
                attempts[key]["state"] = "RESERVED"
                self._event(state, "REGISTERED", "RESERVED", scope="attempt", plan_id=state["current_plan_id"], job_role=job_role, attempt_index=attempt_index)
                state["run_state"] = "MATRIX_ACTIVE"
                if prior == "VERIFIED":
                    self._event(state, "VERIFIED", "MATRIX_ACTIVE", plan_id=state["current_plan_id"])
                self._save_state(state)
                try:
                    job_request = dict(job)
                    job_request["attempt_index"] = attempt_index
                    job_id = self.adapter.submit(self.profile, plan, job_request, token)
                except ToolkitError as error:
                    if error.code != "SUBMISSION_OUTCOME_UNKNOWN":
                        self._append_ledger_transition(ledger, token, "not_submitted")
                        attempts[key]["state"] = "SUBMISSION_FAILED"
                        self._save_ledger(ledger)
                        self._save_state(state)
                        raise
                    matches = self.adapter.reconcile(self.profile, token)
                    if len(matches) != 1:
                        self._append_ledger_transition(ledger, token, "ambiguous")
                        self._save_ledger(ledger)
                        self._save_state(state)
                        raise
                    job_id = matches[0]
                validate_shell_scalar(job_id, "job_id")
                require(job_id.isdigit(), "SUBMISSION_OUTCOME_UNKNOWN", "non-numeric Slurm job ID")
                self._append_ledger_transition(ledger, token, "submitted", job_id=job_id)
                attempts[key].update({"state": "SUBMITTED", "job_id": job_id})
                self._event(state, "RESERVED", "SUBMITTED", scope="attempt", plan_id=state["current_plan_id"], job_role=job_role, attempt_index=attempt_index)
                self._save_ledger(ledger)
                self._save_state(state)
                return job_id

    def observe(self, job_role: str, attempt_index: int) -> dict[str, Any]:
        key = f"{validate_id(job_role, 'job role')}.{attempt_index}"
        self.adapter.check_masters(self.profile)
        with directory_lock(self.budget_lock):
            with directory_lock(self.run_lock):
                state = self._load_state()
                attempt = state.get("attempts", {}).get(key)
                require(isinstance(attempt, dict) and attempt.get("state") == "SUBMITTED", "PLAN_DRIFT", key)
                plan = self._current_plan(state)
                job = next(item for item in plan["jobs"] if item["role"] == job_role)
                result = self.adapter.observe(self.profile, plan, job, attempt["job_id"])
                require(result.get("terminal") is True, "JOB_TERMINAL_MISMATCH", key)
                require(result.get("state") in TERMINAL_JOB_STATES, "JOB_TERMINAL_MISMATCH", key)
                require("actual_gpu_minutes" in result, "EVIDENCE_INCOMPLETE", "accounting availability must be explicit")
                require(result["actual_gpu_minutes"] is None or (isinstance(result["actual_gpu_minutes"], int) and result["actual_gpu_minutes"] >= 0), "EVIDENCE_INCOMPLETE", "accounting")
                attempt["state"] = "TERMINAL_OBSERVED"
                self._event(state, "SUBMITTED", "TERMINAL_OBSERVED", scope="attempt", plan_id=attempt["plan_id"], job_role=job_role, attempt_index=attempt_index)
                gates = result.get("gates")
                passed = result.get("exit_code") == job.get("expected_exit_code", 0) and isinstance(gates, dict) and bool(gates) and all(value is True for value in gates.values())
                attempt.update({"state": "RESULT_VALIDATED", "result": result, "passed": passed})
                self._event(state, "TERMINAL_OBSERVED", "RESULT_VALIDATED", scope="attempt", plan_id=attempt["plan_id"], job_role=job_role, attempt_index=attempt_index)
                ledger = self._load_ledger()
                self._append_ledger_transition(
                    ledger,
                    attempt["token"],
                    "settled",
                    actual_gpu_minutes=result.get("actual_gpu_minutes"),
                )
                required_roles = {item["role"] for item in plan["jobs"]}
                passed_roles = {item["job_role"] for item in state["attempts"].values() if item.get("state") == "RESULT_VALIDATED" and item.get("passed")}
                exhausted_roles = {
                    planned["role"]
                    for planned in plan["jobs"]
                    if len([
                        item
                        for item in state["attempts"].values()
                        if item.get("job_role") == planned["role"] and item.get("state") == "RESULT_VALIDATED"
                    ]) >= planned["max_attempts"]
                }
                if required_roles <= passed_roles | exhausted_roles:
                    self._event(state, "MATRIX_ACTIVE", "MATRIX_SETTLED", plan_id=state["current_plan_id"])
                    state["run_state"] = "MATRIX_SETTLED"
                self._save_ledger(ledger)
                self._save_state(state)
                receipt = self._common("job_receipt", plan_id=attempt["plan_id"])
                receipt.update({"job_role": job_role, "attempt_index": attempt_index, "job_id": attempt["job_id"], "passed": passed, "result": result})
                self._write_publication(f"job-{key}.json", receipt)
                return receipt

    def cancel(self, job_role: str, attempt_index: int) -> dict[str, Any]:
        key = f"{validate_id(job_role, 'job role')}.{attempt_index}"
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            attempt = state.get("attempts", {}).get(key)
            require(isinstance(attempt, dict) and attempt.get("state") == "SUBMITTED", "PLAN_DRIFT", key)
            result = self.adapter.cancel(self.profile, attempt["job_id"])
            require(result.get("job_id") == attempt["job_id"], "JOB_TERMINAL_MISMATCH", key)
            attempt["cancel_acknowledgement"] = result
            self._save_state(state)
            receipt = self._common("cancel_receipt", plan_id=attempt["plan_id"])
            receipt.update({"job_role": job_role, "attempt_index": attempt_index, **result})
            self._write_publication(f"cancel-{key}.json", receipt)
            return result

    def collect(self) -> dict[str, Any]:
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"MATRIX_SETTLED"})
            quarantine = self.run_dir / "private" / "quarantine"
            quarantine.mkdir(parents=True, exist_ok=True, mode=0o700)
            result = self.adapter.collect(self.profile, self._current_plan(state), quarantine)
            require(result.get("download_promoted") is True, "TRANSFER_INCOMPLETE", "download not promoted")
            plan = self._current_plan(state)
            allowed_evidence = set(plan["evidence_allowlist"])
            logical_name = result.get("logical_name")
            if isinstance(logical_name, str) and logical_name.endswith(".tar"):
                archive_path = quarantine / validate_relative_path(logical_name, "evidence archive")
                extract_validated_archive(
                    archive_path,
                    quarantine / "extracted",
                    max_files=self.profile.get("max_evidence_files", 1000),
                    max_bytes=self.profile.get("max_evidence_expanded_bytes", 50_000_000),
                    allowed_members=allowed_evidence,
                )
                archive_path.unlink()
            forbidden = tuple(self.profile.get("forbidden_publication_substrings", []))
            sanitized_files: list[dict[str, Any]] = []
            for path in quarantine.rglob("*"):
                if path.is_file():
                    if logical_name and str(path.relative_to(quarantine)) == logical_name:
                        logical = logical_name
                    elif _is_relative_to(path, quarantine / "extracted"):
                        logical = str(path.relative_to(quarantine / "extracted"))
                    else:
                        logical = str(path.relative_to(quarantine))
                    require(logical in allowed_evidence, "ALLOWLIST_VIOLATION", f"unregistered evidence: {logical}")
                    require(path.stat().st_size <= self.profile.get("max_evidence_file_bytes", 10_000_000), "EVIDENCE_INCOMPLETE", str(path))
                    try:
                        text = path.read_text(encoding="utf-8")
                    except UnicodeDecodeError as error:
                        raise ToolkitError("SANITIZATION_FAILED", f"non-text evidence: {path.name}") from error
                    require(not any(item and item in text for item in forbidden), "SANITIZATION_FAILED", path.name)
                    destination = self.publication_dir / "evidence" / logical
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    temporary = destination.with_name(f".{destination.name}.part")
                    temporary.write_text(text, encoding="utf-8")
                    os.replace(temporary, destination)
                    sanitized_files.append({"logical_name": logical, "bytes": destination.stat().st_size, "sha256": sha256_file(destination)})
            self._event(state, "MATRIX_SETTLED", "COLLECTED", plan_id=state["current_plan_id"])
            state["run_state"] = "COLLECTED"
            state["collection"] = result
            self._save_state(state)
            receipt = self._common("collection_receipt", plan_id=state["current_plan_id"])
            receipt.update(result)
            receipt["sanitized_files"] = sorted(sanitized_files, key=lambda item: item["logical_name"])
            self._write_publication("collection.json", receipt)
            return receipt

    def clean(self) -> dict[str, Any]:
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"COLLECTED"})
            result = self.adapter.clean(self.profile, self._current_plan(state))
            require(result.get("remote_absent") is True, "CLEANUP_INCOMPLETE", "remote run remains")
            require(result.get("job_local_cleanup") in {"scheduler_purged", "verified_absent"}, "CLEANUP_INCOMPLETE", "job-local cleanup")
            self._event(state, "COLLECTED", "CLEANED", plan_id=state["current_plan_id"])
            state["run_state"] = "CLEANED"
            state["cleanup"] = result
            self._save_state(state)
            receipt = self._common("cleanup_receipt", plan_id=state["current_plan_id"])
            receipt.update({"remote_root_hash": sha256_bytes(self._current_plan(state)["remote_run_root"].encode()), **result})
            self._write_publication("cleanup.json", receipt)
            return receipt

    def close(self) -> dict[str, Any]:
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"CLEANED"})
            receipt = self._common("terminal_receipt", plan_id=state["current_plan_id"])
            receipt.update({"terminal": "LEMHI-TOOLKIT-RUN-CLOSED", "attempt_count": len(state.get("attempts", {})), "cleanup": state["cleanup"]})
            self._write_publication("terminal.json", receipt)
            private_dir = self.private_path.parent
            for child in list(private_dir.iterdir()):
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        require(not self.private_path.parent.exists() or not any(self.private_path.parent.iterdir()), "CLEANUP_INCOMPLETE", "private state remains")
        self.private_path.parent.rmdir()
        return receipt
