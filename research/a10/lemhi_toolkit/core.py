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
SCHEMA_VERSION_V2 = "lemhi-toolkit-record-2"
PRODUCER_VERSION = "lemhi-toolkit-foundation-1"
PRODUCER_VERSION_V2 = "lemhi-toolkit-hardening-2"
SAFE_INTEGER = 9_007_199_254_740_991
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._+=-]{0,254}$")
HEX64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
TYPED_GRES_PATTERN = re.compile(
    r"^(?P<resource>[A-Za-z0-9_]+):(?P<model>[A-Za-z0-9_]+):(?P<count>[1-9][0-9]*)$"
)


class ToolkitError(Exception):
    """A stable fail-closed toolkit error."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def require(condition: bool, code: str, detail: str) -> None:
    if not condition:
        raise ToolkitError(code, detail)


def parse_typed_gres(value: Any, field: str) -> tuple[str, str, int]:
    """Return a typed GRES resource, model, and positive count."""

    require(isinstance(value, str), "PLAN_DRIFT", field)
    match = TYPED_GRES_PATTERN.fullmatch(value)
    require(match is not None, "PLAN_DRIFT", field)
    return match["resource"], match["model"], int(match["count"])


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
    """Read and authenticate a supported publication record without rewriting it."""

    value = read_json(path)
    require(value.get("schema_version") in {SCHEMA_VERSION, SCHEMA_VERSION_V2}, "EVIDENCE_INCOMPLETE", "unsupported record major version")
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
    max_file_bytes: int | None = None,
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
                if max_file_bytes is not None:
                    require(
                        member.size <= max_file_bytes,
                        "ARCHIVE_UNSAFE",
                        "archive member byte ceiling",
                    )
                total += member.size
                require(total <= max_bytes, "ARCHIVE_UNSAFE", "archive expansion ceiling")
        return members


def extract_validated_archive(
    path: Path,
    destination: Path,
    *,
    max_files: int,
    max_bytes: int,
    max_file_bytes: int | None = None,
    allowed_members: set[str] | None = None,
) -> list[str]:
    """Extract only members already accepted by :func:`validate_archive`."""

    members = validate_archive(
        path,
        max_files=max_files,
        max_bytes=max_bytes,
        max_file_bytes=max_file_bytes,
        allowed_members=allowed_members,
    )
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
    return [member.name for member in members]


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
    def reconcile_authority(self, profile: dict[str, Any], authority_token: str) -> list[str]: ...
    def observe(self, profile: dict[str, Any], plan: dict[str, Any], job: dict[str, Any], job_id: str) -> dict[str, Any]: ...
    def recover(self, profile: dict[str, Any], plan: dict[str, Any], attempt: dict[str, Any], token: str) -> str: ...
    def observe_recovery(self, profile: dict[str, Any], plan: dict[str, Any], recovery: dict[str, Any]) -> dict[str, Any]: ...
    def cancel(self, profile: dict[str, Any], job_id: str) -> dict[str, Any]: ...
    def collect(self, profile: dict[str, Any], plan: dict[str, Any], quarantine: Path) -> dict[str, Any]: ...
    def clean(
        self,
        profile: dict[str, Any],
        plan: dict[str, Any],
        recovery: dict[str, Any] | None = None,
        stopped_roles: set[str] | None = None,
    ) -> dict[str, Any]: ...
    def abort(self, profile: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]: ...


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
    "ABORTED",
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
        self.record_schema_version = profile.get("record_schema_version", SCHEMA_VERSION)
        require(self.record_schema_version in {SCHEMA_VERSION, SCHEMA_VERSION_V2}, "AUTHORITY_INVALID", "record schema version")
        self.producer_version = PRODUCER_VERSION_V2 if self.record_schema_version == SCHEMA_VERSION_V2 else PRODUCER_VERSION
        self.provider_api_version = profile.get("provider_api_version", 1)
        require(self.provider_api_version in {1, 2}, "PROVIDER_UNAVAILABLE", "provider API version")
        if self.provider_api_version == 2:
            anchor = authority.get("ledger_anchor")
            require(isinstance(anchor, str) and Path(anchor).is_absolute(), "AUTHORITY_INVALID", "v2 ledger anchor")
            require(Path(anchor).resolve() == self.ledger_path, "AUTHORITY_INVALID", "state root differs from authority ledger anchor")
            revision_hash = authority.get("authority_revision_sha256")
            require(isinstance(revision_hash, str) and HEX64_PATTERN.fullmatch(revision_hash) is not None, "AUTHORITY_INVALID", "authority revision hash")

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
            "schema_version": self.record_schema_version,
            "record_type": record_type,
            "authority_id": self.authority_id,
            "run_id": self.run_id,
            "package_id": self.package_id,
            "source_commit": self.source_commit,
            "created_at": self.clock(),
            "producer_version": self.producer_version,
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
        state = read_json(self.private_path)
        require(
            state.get("authority_sha256") == self.authority_sha256
            and state.get("cluster_profile_sha256") == self.profile_sha256,
            "PLAN_DRIFT",
            "runtime authority/profile differs from frozen run identity",
        )
        current = state.get("current_plan_id")
        if current is not None:
            matches = [
                revision.get("semantic")
                for revision in state.get("plan_revisions", [])
                if isinstance(revision, dict) and revision.get("plan_id") == current
            ]
            require(
                len(matches) == 1
                and isinstance(matches[0], dict)
                and matches[0].get("cluster_profile_sha256")
                == self.profile_sha256,
                "PLAN_DRIFT",
                "current plan/profile identity differs from runtime profile",
            )
        return state

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
        if scope in {"attempt", "recovery"}:
            event.update({"job_role": job_role, "attempt_index": attempt_index})
        elif scope == "role":
            event["job_role"] = job_role
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
            if self.provider_api_version == 2:
                self._load_ledger()
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
            require(provider.get("provider_api_version") == self.provider_api_version, "PROVIDER_UNAVAILABLE", str(path))
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
            allowed_classes = {"runtime", "framework", "transport", "scheduler", "storage", "accelerator"}
            if self.provider_api_version == 2:
                allowed_classes.add("toolchain")
                require(provider.get("executes_provider_code") is False, "PROVIDER_UNAVAILABLE", "v2 providers are declarative")
            require(provider.get("provider_class") in allowed_classes, "PROVIDER_UNAVAILABLE", str(path))
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

    def _validate_admission_materialization(
        self, plan_input: dict[str, Any], roles: set[str]
    ) -> None:
        contract = plan_input.get("admission_materialization")
        if contract is None:
            return
        require(
            self.provider_api_version == 2 and isinstance(contract, dict),
            "PLAN_DRIFT",
            "submission admission requires provider revision 2",
        )

        legacy_fields = {
            "asset",
            "receipt_directory",
            "record_type",
            "required_before_each_submit",
            "required_roles",
            "snapshot",
            "toolkit_submit_invokes_package_checker",
        }
        composed_fields = legacy_fields | {"checker_assets"}
        require(
            frozenset(contract)
            in {frozenset(legacy_fields), frozenset(composed_fields)},
            "PLAN_DRIFT",
            "submission admission contract shape",
        )
        require(
            contract.get("required_before_each_submit") is True
            and contract.get("toolkit_submit_invokes_package_checker") is False,
            "PLAN_DRIFT",
            "submission admission invocation semantics",
        )
        require(
            contract.get("snapshot")
            == "exact private toolkit state plus authenticated job receipts",
            "PLAN_DRIFT",
            "submission admission snapshot",
        )
        validate_relative_path(contract.get("asset"), "submission admission asset")
        require(
            contract["asset"]
            in {
                item.get("logical_name")
                for item in plan_input.get("assets", [])
                if isinstance(item, dict) and item.get("executable") is True
            },
            "PLAN_DRIFT",
            "submission admission materializer is not a frozen executable asset",
        )
        if "checker_assets" in contract:
            self._admission_checker_identities(plan_input, contract)
        validate_id(contract.get("record_type"), "submission admission record type")
        required_roles = contract.get("required_roles")
        require(
            isinstance(required_roles, list)
            and len(required_roles) == len(set(required_roles))
            and set(required_roles) == roles,
            "PLAN_DRIFT",
            "submission admission role matrix",
        )
        receipt_directory = contract.get("receipt_directory")
        require(
            isinstance(receipt_directory, str)
            and Path(receipt_directory).is_absolute(),
            "ALLOWLIST_VIOLATION",
            "submission admission receipt directory",
        )
        receipt_root = Path(receipt_directory)
        try:
            resolved = receipt_root.resolve(strict=True)
        except OSError as error:
            raise ToolkitError(
                "ALLOWLIST_VIOLATION",
                f"submission admission receipt directory: {error}",
            ) from error
        require(
            resolved.is_dir()
            and not receipt_root.is_symlink()
            and any(
                _is_relative_to(resolved, root.resolve())
                for root in self.allowed_roots
            ),
            "ALLOWLIST_VIOLATION",
            "submission admission receipt directory",
        )

    @staticmethod
    def _admission_checker_identities(
        plan: dict[str, Any], contract: dict[str, Any]
    ) -> list[dict[str, Any]]:
        checker_contract = contract.get("checker_assets")
        require(
            isinstance(checker_contract, dict)
            and set(checker_contract) == {"logical_names", "protocol"}
            and checker_contract.get("protocol") == "ordered-plan-assets-v1",
            "PLAN_DRIFT",
            "submission admission checker identity protocol",
        )
        checker_assets = checker_contract.get("logical_names")
        require(
            isinstance(checker_assets, list)
            and bool(checker_assets)
            and all(isinstance(item, str) for item in checker_assets)
            and len(checker_assets) == len(set(checker_assets)),
            "PLAN_DRIFT",
            "submission admission checker asset chain",
        )
        require(
            contract.get("asset") not in checker_assets,
            "PLAN_DRIFT",
            "submission admission materializer/checker separation",
        )
        assets = {
            item.get("logical_name"): item
            for item in plan.get("assets", [])
            if isinstance(item, dict)
        }
        identities: list[dict[str, Any]] = []
        for logical_name in checker_assets:
            validate_relative_path(logical_name, "submission admission checker asset")
            asset = assets.get(logical_name)
            require(
                isinstance(asset, dict)
                and asset.get("executable") is True
                and asset.get("source_class") == "repository-owned",
                "PLAN_DRIFT",
                "submission admission checker is not a frozen repository executable asset",
            )
            identities.append(
                {
                    "bytes": asset.get("bytes"),
                    "logical_name": logical_name,
                    "sha256": asset.get("sha256"),
                }
            )
        return identities

    def _validate_evidence_volume(
        self, plan_input: dict[str, Any], allowlist: set[str]
    ) -> None:
        contract = plan_input.get("evidence_volume")
        if contract is None:
            return
        require(
            isinstance(contract, dict)
            and set(contract)
            == {
                "maximum_expanded_bytes",
                "maximum_file_bytes",
                "maximum_files",
            },
            "PLAN_DRIFT",
            "evidence volume contract shape",
        )
        limits = {
            "maximum_expanded_bytes": self.profile.get(
                "max_evidence_expanded_bytes", 50_000_000
            ),
            "maximum_file_bytes": self.profile.get(
                "max_evidence_file_bytes", 10_000_000
            ),
            "maximum_files": self.profile.get("max_evidence_files", 1000),
        }
        require(
            all(
                type(contract.get(name)) is int
                and 0 < contract[name] <= limit
                for name, limit in limits.items()
            ),
            "PLAN_DRIFT",
            "evidence volume exceeds cluster profile",
        )
        require(
            len(allowlist) <= contract["maximum_files"],
            "PLAN_DRIFT",
            "evidence allowlist exceeds declared file ceiling",
        )

    def _submission_admission_hash(
        self,
        plan: dict[str, Any],
        state: dict[str, Any],
        job_role: str,
        attempt_index: int,
    ) -> str | None:
        contract = plan.get("admission_materialization")
        if contract is None:
            return None
        require(
            isinstance(contract, dict)
            and job_role in contract.get("required_roles", []),
            "PLAN_DRIFT",
            "submission admission role",
        )
        receipt_path = Path(contract["receipt_directory"]) / f"{job_role}.json"
        validated_path = validate_allowed_file(receipt_path, self.allowed_roots)
        receipt = read_record(validated_path)
        gates = receipt.get("gates")
        input_identities = receipt.get("input_identities", {})
        require(
            isinstance(input_identities, dict),
            "PLAN_DRIFT",
            "submission admission input identities",
        )
        checker_identities_match = True
        if "checker_assets" in contract:
            checker_identities = self._admission_checker_identities(plan, contract)
            checker_names = [item["logical_name"] for item in checker_identities]
            prepared_identities = self._project_checker_identities(
                state.get("prepared_assets"), checker_names
            )
            transfer_identities = self._project_checker_identities(
                state.get("transfer_receipts"),
                checker_names,
                require_promoted_transfer=True,
            )
            local_identities = []
            plan_assets = {
                item.get("logical_name"): item
                for item in plan.get("assets", [])
                if isinstance(item, dict)
            }
            for logical_name in checker_names:
                local_path = validate_allowed_file(
                    Path(plan_assets[logical_name].get("local_path", "")),
                    self.allowed_roots,
                )
                local_identities.append(
                    {
                        "bytes": local_path.stat().st_size,
                        "logical_name": logical_name,
                        "sha256": sha256_file(local_path),
                    }
                )
            checker_identities_match = (
                checker_identities
                == prepared_identities
                == transfer_identities
                == local_identities
                and input_identities.get("checker_assets")
                == {
                    "assets": checker_identities,
                    "protocol": "ordered-plan-assets-v1",
                }
            )
        require(
            receipt.get("record_type") == contract.get("record_type")
            and receipt.get("authority_id") == self.authority_id
            and receipt.get("package_id") == self.package_id
            and receipt.get("run_id") == self.run_id
            and receipt.get("source_commit") == self.source_commit
            and receipt.get("plan_id") == state.get("current_plan_id")
            and receipt.get("role") == job_role
            and receipt.get("attempt_index") == attempt_index
            and receipt.get("decision") == "PASS"
            and receipt.get("valid") is True
            and isinstance(gates, dict)
            and bool(gates)
            and all(value is True for value in gates.values())
            and input_identities.get("toolkit_state_sha256")
            == sha256_file(self.private_path)
            and checker_identities_match,
            "PLAN_DRIFT",
            "submission admission receipt is stale or invalid",
        )
        return receipt["record_sha256"]

    @staticmethod
    def _project_checker_identities(
        records: Any,
        logical_names: list[str],
        *,
        require_promoted_transfer: bool = False,
    ) -> list[dict[str, Any]]:
        require(
            isinstance(records, list)
            and all(isinstance(item, dict) for item in records),
            "PLAN_DRIFT",
            "submission admission staged checker identities",
        )
        by_name = {item.get("logical_name"): item for item in records}
        require(
            len(by_name) == len(records),
            "PLAN_DRIFT",
            "submission admission staged checker identity uniqueness",
        )
        projected = []
        for logical_name in logical_names:
            item = by_name.get(logical_name)
            require(
                isinstance(item, dict),
                "PLAN_DRIFT",
                "submission admission staged checker identity missing",
            )
            if require_promoted_transfer:
                require(
                    item.get("promoted") is True
                    and item.get("identity_sha256") == item.get("sha256")
                    and item.get("remote_revalidated") is True
                    and item.get("state")
                    in {"uploaded", "resumed", "already_verified"},
                    "PLAN_DRIFT",
                    "submission admission checker transfer is not promoted and revalidated",
                )
            projected.append(
                {
                    "bytes": item.get("bytes"),
                    "logical_name": logical_name,
                    "sha256": item.get("sha256"),
                }
            )
        return projected

    @staticmethod
    def _accelerator_contract(providers: list[dict[str, Any]]) -> tuple[str, int]:
        accelerator = next(
            (provider for provider in providers if provider.get("provider_class") == "accelerator"),
            None,
        )
        require(accelerator is not None, "PROVIDER_UNAVAILABLE", "accelerator provider required")
        provides = accelerator.get("provides", {})
        request = provides.get("accelerator_request")
        maximum = provides.get("accelerator_maximum_devices", 1)
        require(isinstance(request, str), "PROVIDER_UNAVAILABLE", "accelerator request")
        resource, model = request.split(":", 1) if request.count(":") == 1 else ("", "")
        require(resource == "gpu" and bool(model), "PROVIDER_UNAVAILABLE", "typed accelerator request")
        require(isinstance(maximum, int) and maximum > 0, "PROVIDER_UNAVAILABLE", "accelerator maximum")
        return request, maximum

    @staticmethod
    def _validate_jobs(
        jobs: Any,
        logical_assets: set[str],
        evidence_allowlist: set[str],
        accelerator_request: str,
        maximum_gpus: int,
        additional_slurm_streams: tuple[str, ...] = (),
        additional_gate_receipts: set[str] | None = None,
    ) -> set[str]:
        require(isinstance(jobs, list) and jobs, "PLAN_DRIFT", "jobs")
        roles: set[str] = set()
        slurm_streams = list(additional_slurm_streams)
        gate_receipts = set(additional_gate_receipts or set())
        for job in jobs:
            require(isinstance(job, dict), "PLAN_DRIFT", "job")
            role = validate_id(job.get("role"), "job role")
            require(role not in roles, "PLAN_DRIFT", f"duplicate role {role}")
            roles.add(role)
            validate_relative_path(job.get("script"), "job script")
            require(job["script"] in logical_assets, "PLAN_DRIFT", "job script is not a frozen asset")
            validate_id(job.get("partition"), "partition")
            for field in ("cpus", "memory_mb", "gpus", "time_limit_minutes"):
                require(isinstance(job.get(field), int) and job[field] > 0, "PLAN_DRIFT", f"job {field}")
            resource, model, count = parse_typed_gres(job.get("gres"), "job gres")
            require(f"{resource}:{model}" == accelerator_request, "PLAN_DRIFT", "job gres provider mismatch")
            require(count == job["gpus"], "PLAN_DRIFT", "job gpus and gres count mismatch")
            require(count <= maximum_gpus, "PLAN_DRIFT", "job gpu count exceeds provider maximum")
            require(isinstance(job.get("max_attempts"), int) and job["max_attempts"] > 0, "PLAN_DRIFT", "job max_attempts")
            require(isinstance(job.get("expected_exit_code", 0), int) and 0 <= job.get("expected_exit_code", 0) <= 255, "PLAN_DRIFT", "expected exit code")
            retry_on = job.get("retry_on", [])
            require(isinstance(retry_on, list) and all(isinstance(item, str) for item in retry_on), "PLAN_DRIFT", "retry classes")
            require(len(set(retry_on)) == len(retry_on), "PLAN_DRIFT", "duplicate retry classes")
            require(set(retry_on) <= {"cancelled", "gate-failed", "scheduler-failure"}, "PLAN_DRIFT", "retry classes")
            require(job["max_attempts"] == 1 or retry_on, "PLAN_DRIFT", "retries require classes")
            gate_receipt = validate_relative_path(job.get("gate_receipt"), "gate receipt")
            require(gate_receipt in evidence_allowlist, "PLAN_DRIFT", "gate receipt is not evidence-allowlisted")
            gate_receipts.add(gate_receipt)
            slurm_streams.extend(
                f"slurm/{role}.{attempt_index}.{suffix}"
                for attempt_index in range(job["max_attempts"])
                for suffix in ("out", "err")
            )
        require(
            len(slurm_streams) == len(set(slurm_streams)),
            "PLAN_DRIFT",
            "Slurm stream has multiple owners",
        )
        require(
            not gate_receipts & set(slurm_streams),
            "PLAN_DRIFT",
            "gate receipt collides with Slurm stream",
        )
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
            accelerator_request, maximum_gpus = self._accelerator_contract(providers)
            additional_slurm_streams: list[str] = []
            additional_gate_receipts: set[str] = set()
            if self.provider_api_version == 2:
                from .hardening import (
                    close_job_environment,
                    validate_evidence_replacements,
                    validate_v2_provider_stack,
                )

                validate_v2_provider_stack(providers)
                require(plan_input.get("authority_revision_sha256") == self.authority["authority_revision_sha256"], "AUTHORITY_INVALID", "authority revision")
                require(plan_input.get("scheduler_authority_token") == self.authority["scheduler_authority_token"], "AUTHORITY_INVALID", "scheduler authority token")
                require(plan_input.get("job_local_cleanup") == "toolkit_recoverable", "PLAN_DRIFT", "v2 job-local cleanup")
                recovery = plan_input.get("recovery_contingency")
                require(isinstance(recovery, dict), "PLAN_DRIFT", "recovery contingency")
                for field in ("gpu_minutes", "max_attempts", "time_limit_minutes"):
                    require(isinstance(recovery.get(field), int) and recovery[field] > 0, "PLAN_DRIFT", f"recovery {field}")
                require(recovery.get("exact_node_only") is True and recovery.get("ambiguity") == "retain-reserve", "PLAN_DRIFT", "recovery stop rules")
                for field in ("cpus", "memory_mb", "gpus"):
                    require(isinstance(recovery.get(field), int) and recovery[field] > 0, "PLAN_DRIFT", f"recovery {field}")
                require(recovery["gpu_minutes"] == recovery["gpus"] * recovery["time_limit_minutes"], "PLAN_DRIFT", "recovery charge")
                require(recovery["max_attempts"] == 1, "PLAN_DRIFT", "exactly one recovery attempt")
                validate_id(recovery.get("partition"), "recovery partition")
                resource, model, count = parse_typed_gres(recovery.get("gres"), "recovery gres")
                require(f"{resource}:{model}" == accelerator_request, "PLAN_DRIFT", "recovery gres provider mismatch")
                require(count == recovery["gpus"], "PLAN_DRIFT", "recovery gpus and gres count mismatch")
                require(count <= maximum_gpus, "PLAN_DRIFT", "recovery gpu count exceeds provider maximum")
                recovery_script = validate_relative_path(recovery.get("script"), "recovery script")
                require(recovery_script in {asset["logical_name"] for asset in plan_input.get("assets", []) if isinstance(asset, dict) and asset.get("executable") is True}, "PLAN_DRIFT", "recovery script must be an executable frozen asset")
                recovery_gate = validate_relative_path(recovery.get("gate_receipt"), "recovery gate receipt")
                require(recovery_gate in plan_input.get("evidence_allowlist", []), "PLAN_DRIFT", "recovery gate receipt is not evidence-allowlisted")
                additional_gate_receipts.add(recovery_gate)
                for stream in ("slurm/toolkit-recovery.0.out", "slurm/toolkit-recovery.0.err"):
                    require(stream in plan_input.get("evidence_allowlist", []), "PLAN_DRIFT", "recovery logs are not evidence-allowlisted")
                    additional_slurm_streams.append(stream)
                capacity = plan_input.get("job_local_capacity")
                require(isinstance(capacity, dict), "PLAN_DRIFT", "job-local capacity")
                for field in ("expanded_asset_bytes", "product_bytes", "checkpoint_bytes", "margin_bytes", "minimum_free_bytes", "required_inodes"):
                    require(isinstance(capacity.get(field), int) and capacity[field] >= 0, "PLAN_DRIFT", f"capacity {field}")
                required_environment = plan_input.get("required_job_environment")
                require(isinstance(required_environment, dict), "PLAN_DRIFT", "required job environment")
                require({"PATH", "TMPDIR"} <= required_environment.keys(), "PLAN_DRIFT", "exact PATH and TMPDIR required")
                close_job_environment(required_environment, {}, {}, deterministic_cuda=plan_input.get("deterministic_cuda") is True)
                validate_evidence_replacements(plan_input.get("evidence_replacements", []))
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
                require(isinstance(asset.get("executable", False), bool), "PLAN_DRIFT", "asset executable intent")
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
            roles = self._validate_jobs(
                jobs,
                logical_assets,
                set(validated_evidence),
                accelerator_request,
                maximum_gpus,
                tuple(additional_slurm_streams),
                additional_gate_receipts,
            )
            self._validate_admission_materialization(plan_input, roles)
            self._validate_evidence_volume(plan_input, set(validated_evidence))
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
        matches = [
            revision
            for revision in state.get("plan_revisions", [])
            if isinstance(revision, dict) and revision.get("plan_id") == current
        ]
        require(len(matches) == 1, "PLAN_DRIFT", "current plan missing or ambiguous")
        semantic = matches[0].get("semantic")
        require(
            isinstance(semantic, dict)
            and sha256_bytes(canonical_bytes(semantic)) == current,
            "PLAN_DRIFT",
            "current plan identity mismatch",
        )
        return semantic

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
                "recovery_contingency",
                "admission_materialization",
                "submission_mode",
                "stop_rules",
            ):
                require(replacement.get(field) == prior.get(field), "PLAN_DRIFT", f"immutable field changed: {field}")
            providers = self._load_providers(replacement)
            accelerator_request, maximum_gpus = self._accelerator_contract(providers)
            additional_slurm_streams: tuple[str, ...] = ()
            additional_gate_receipts: set[str] = set()
            if self.provider_api_version == 2:
                recovery = prior.get("recovery_contingency")
                require(isinstance(recovery, dict), "PLAN_DRIFT", "recovery contingency")
                additional_slurm_streams = (
                    "slurm/toolkit-recovery.0.out",
                    "slurm/toolkit-recovery.0.err",
                )
                additional_gate_receipts.add(
                    validate_relative_path(
                        recovery.get("gate_receipt"), "recovery gate receipt"
                    )
                )
            self._validate_jobs(
                replacement.get("jobs"),
                {asset["logical_name"] for asset in prior["assets"]},
                set(prior["evidence_allowlist"]),
                accelerator_request,
                maximum_gpus,
                additional_slurm_streams,
                additional_gate_receipts,
            )
            self._validate_evidence_volume(
                replacement, set(prior["evidence_allowlist"])
            )
            attempts = state.get("attempts", {})
            started_roles = {item["job_role"] for item in attempts.values() if item.get("state") != "REGISTERED"}
            prior_jobs = {item["role"]: item for item in prior.get("jobs", [])}
            next_jobs = {item["role"]: item for item in replacement.get("jobs", [])}
            for role in started_roles:
                require(prior_jobs.get(role) == next_jobs.get(role), "PLAN_DRIFT", f"started role changed: {role}")
            if self.provider_api_version == 2:
                from .hardening import validate_evidence_replacements

                validate_evidence_replacements(replacement.get("evidence_replacements", []))
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
                executable = asset.get("executable", False)
                require(not executable or os.access(path, os.X_OK), "ASSET_IDENTITY_MISMATCH", f"{logical} is not executable")
                prepared.append({
                    "logical_name": logical,
                    "local_path": str(path),
                    "bytes": size,
                    "sha256": digest,
                    "source_class": asset["source_class"],
                    "license_provenance": validate_record_text(asset["license_provenance"], "license provenance"),
                    "executable": executable,
                })
            self._event(state, "PLANNED", "PREPARED", plan_id=state["current_plan_id"])
            state["run_state"] = "PREPARED"
            state["prepared_assets"] = prepared
            self._save_state(state)
            receipt = self._common("prepare_receipt", plan_id=state["current_plan_id"])
            receipt["assets"] = [
                {key: item[key] for key in ("logical_name", "bytes", "sha256", "source_class", "license_provenance", "executable")}
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
                if self.provider_api_version == 2:
                    require(isinstance(receipt.get("elapsed_ns"), int) and receipt["elapsed_ns"] > 0, "TRANSFER_INCOMPLETE", "integer telemetry")
                    require(receipt.get("state") in {"uploaded", "resumed", "already_verified"}, "TRANSFER_INCOMPLETE", "transfer state")
                    require(receipt.get("identity_sha256") == prepared["sha256"], "TRANSFER_INCOMPLETE", "v2 identity")
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
        if self.provider_api_version == 2:
            from .hardening import LedgerAnchor

            checkpoint = self.authority.get("ledger_head_checkpoint")
            return LedgerAnchor(self.ledger_path, self.authority_id, self.budget_id, self.authority["resource_ceiling_gpu_minutes"]).load(checkpoint=checkpoint)
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
            if "token" in item:
                latest[item["token"]] = item
        return sum(item["requested_gpu_minutes"] for item in latest.values() if item["status"] in {"reserved", "submitted", "settled", "ambiguous"})

    def _append_ledger_transition(self, ledger: dict[str, Any], token: str, status: str, **updates: Any) -> None:
        prior = next((item for item in reversed(ledger["entries"]) if item.get("token") == token), None)
        require(prior is not None, "AUTHORITY_INVALID", "ledger token missing")
        event = dict(prior)
        event.update(updates)
        event["status"] = status
        event["sequence"] = len(ledger["entries"])
        if self.provider_api_version == 2:
            event.pop("event_sha256", None)
            event["predecessor_sha256"] = ledger["head_sha256"]
            event["event_sha256"] = sha256_bytes(canonical_bytes(event))
            ledger["head_sha256"] = event["event_sha256"]
        ledger["entries"].append(event)

    def submit(self, job_role: str, attempt_index: int) -> str:
        job_role = validate_id(job_role, "job role")
        require(isinstance(attempt_index, int) and attempt_index >= 0, "PLAN_DRIFT", "attempt index")
        self.adapter.check_masters(self.profile)
        with directory_lock(self.budget_lock):
            if self.provider_api_version == 2:
                ledger_for_reconciliation = self._load_ledger()
                observed_job_ids = self.adapter.reconcile_authority(self.profile, self.authority["scheduler_authority_token"])
                require(isinstance(observed_job_ids, list) and all(isinstance(item, str) and item.isdigit() for item in observed_job_ids), "AUTHORITY_RECONCILIATION_REQUIRED", "invalid scheduler accounting")
                registered_job_ids = {
                    item["job_id"]
                    for item in ledger_for_reconciliation["entries"]
                    if isinstance(item.get("job_id"), str)
                }
                observed = set(observed_job_ids)
                require(observed == registered_job_ids, "AUTHORITY_RECONCILIATION_REQUIRED", "scheduler and ledger job identities differ")
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
                admission_sha256 = self._submission_admission_hash(
                    plan, state, job_role, attempt_index
                )
                requested = job["gpus"] * job["time_limit_minutes"]
                ledger = self._load_ledger()
                recovery_requested = 0
                recovery_token = None
                if self.provider_api_version == 2 and not state.get("recovery_token"):
                    recovery_requested = plan["recovery_contingency"]["gpu_minutes"]
                    recovery_token = sha256_bytes(f"{self.authority_id}:{self.run_id}:recovery".encode())[:32]
                require(self._reserved_total(ledger) + requested + recovery_requested <= ledger["ceiling_gpu_minutes"], "RESOURCE_CEILING", key)
                if recovery_token is not None:
                    recovery_entry = {
                        "authority_id": self.authority_id,
                        "run_id": self.run_id,
                        "plan_id": state["current_plan_id"],
                        "job_role": "toolkit-recovery",
                        "attempt_index": 0,
                        "token": recovery_token,
                        "requested_gpu_minutes": recovery_requested,
                        "status": "reserved",
                        "sequence": len(ledger["entries"]),
                        "predecessor_sha256": ledger["head_sha256"],
                    }
                    recovery_entry["event_sha256"] = sha256_bytes(canonical_bytes(recovery_entry))
                    ledger["head_sha256"] = recovery_entry["event_sha256"]
                    ledger["entries"].append(recovery_entry)
                    state["recovery_token"] = recovery_token
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
                if self.provider_api_version == 2:
                    entry["predecessor_sha256"] = ledger["head_sha256"]
                    entry["event_sha256"] = sha256_bytes(canonical_bytes(entry))
                    ledger["head_sha256"] = entry["event_sha256"]
                ledger["entries"].append(entry)
                self._save_ledger(ledger)
                prior = state["run_state"]
                attempts[key] = {"job_role": job_role, "attempt_index": attempt_index, "state": "REGISTERED", "token": token, "plan_id": state["current_plan_id"]}
                if admission_sha256 is not None:
                    attempts[key]["submission_admission_record_sha256"] = admission_sha256
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

    @staticmethod
    def _role_outcomes(
        state: dict[str, Any], plan: dict[str, Any]
    ) -> tuple[set[str], set[str]]:
        attempts = state.get("attempts", {}).values()
        passed_roles = {
            item["job_role"]
            for item in attempts
            if item.get("state") == "RESULT_VALIDATED" and item.get("passed")
        }
        exhausted_roles = {
            planned["role"]
            for planned in plan["jobs"]
            if len(
                [
                    item
                    for item in state.get("attempts", {}).values()
                    if item.get("job_role") == planned["role"]
                    and item.get("state") == "RESULT_VALIDATED"
                ]
            )
            >= planned["max_attempts"]
        }
        return passed_roles, exhausted_roles

    def _settle_matrix_if_complete(
        self, state: dict[str, Any], plan: dict[str, Any]
    ) -> None:
        required_roles = {item["role"] for item in plan["jobs"]}
        passed_roles, exhausted_roles = self._role_outcomes(state, plan)
        matrix_stop = state.get("matrix_stop", {})
        stopped_roles = set(matrix_stop.get("stopped_roles", []))
        if required_roles <= passed_roles | exhausted_roles | stopped_roles:
            self._event(
                state,
                "MATRIX_ACTIVE",
                "MATRIX_SETTLED",
                plan_id=state["current_plan_id"],
            )
            state["run_state"] = "MATRIX_SETTLED"

    def observe(self, job_role: str, attempt_index: int) -> dict[str, Any]:
        key = f"{validate_id(job_role, 'job role')}.{attempt_index}"
        self.adapter.check_masters(self.profile)
        with directory_lock(self.budget_lock):
            with directory_lock(self.run_lock):
                state = self._load_state()
                attempt = state.get("attempts", {}).get(key)
                require(isinstance(attempt, dict), "PLAN_DRIFT", key)
                if attempt.get("state") == "RESULT_VALIDATED":
                    result = attempt.get("result", {})
                    correction_path = self.publication_dir / f"cancellation-correction-{key}.json"
                    if attempt.get("passed") is False and correction_path.exists():
                        return read_record(correction_path)
                    require(
                        attempt.get("passed") is True
                        and result.get("state") == "CANCELLED"
                        and attempt.get("cancel_acknowledgement", {}).get("job_id")
                        == attempt.get("job_id"),
                        "PLAN_DRIFT",
                        "only a misclassified exact cancellation can be corrected",
                    )
                    prior = read_record(self.publication_dir / f"job-{key}.json")
                    require(
                        prior.get("passed") is True
                        and prior.get("result", {}).get("state") == "CANCELLED",
                        "EVIDENCE_INCOMPLETE",
                        "published cancellation misclassification missing",
                    )
                    attempt["passed"] = False
                    correction = self._common(
                        "cancellation_correction_receipt",
                        plan_id=attempt["plan_id"],
                    )
                    correction.update(
                        {
                            "attempt_index": attempt_index,
                            "corrected_passed": False,
                            "job_id": attempt["job_id"],
                            "job_role": job_role,
                            "prior_job_receipt_sha256": prior["record_sha256"],
                            "reason": "scheduler cancellation cannot pass science",
                        }
                    )
                    attempt["cancellation_correction"] = correction
                    self._save_state(state)
                    self._write_publication(
                        f"cancellation-correction-{key}.json", correction
                    )
                    return read_record(correction_path)
                require(attempt.get("state") == "SUBMITTED", "PLAN_DRIFT", key)
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
                passed = (
                    result.get("state") == "COMPLETED"
                    and result.get("exit_code") == job.get("expected_exit_code", 0)
                    and isinstance(gates, dict)
                    and bool(gates)
                    and all(value is True for value in gates.values())
                )
                attempt.update({"state": "RESULT_VALIDATED", "result": result, "passed": passed})
                self._event(state, "TERMINAL_OBSERVED", "RESULT_VALIDATED", scope="attempt", plan_id=attempt["plan_id"], job_role=job_role, attempt_index=attempt_index)
                ledger = self._load_ledger()
                self._append_ledger_transition(
                    ledger,
                    attempt["token"],
                    "settled",
                    actual_gpu_minutes=result.get("actual_gpu_minutes"),
                )
                self._settle_matrix_if_complete(state, plan)
                self._save_ledger(ledger)
                self._save_state(state)
                receipt = self._common("job_receipt", plan_id=attempt["plan_id"])
                receipt.update({"job_role": job_role, "attempt_index": attempt_index, "job_id": attempt["job_id"], "passed": passed, "result": result})
                self._write_publication(f"job-{key}.json", receipt)
                return receipt

    def stop_matrix(self, trigger_job_role: str, reason_code: str) -> dict[str, Any]:
        """Settle all never-submitted roles after an exhausted upstream failure."""

        trigger_job_role = validate_id(trigger_job_role, "trigger job role")
        require(
            reason_code == "upstream-role-exhausted",
            "PLAN_DRIFT",
            "unsupported matrix stop reason",
        )
        require(
            self.provider_api_version == 2,
            "PLAN_DRIFT",
            "matrix stop requires provider revision 2",
        )
        with directory_lock(self.budget_lock):
            with directory_lock(self.run_lock):
                state = self._load_state()
                existing_stop = state.get("matrix_stop")
                if existing_stop is not None:
                    require(
                        existing_stop.get("trigger_job_role") == trigger_job_role
                        and existing_stop.get("reason_code") == reason_code,
                        "PLAN_DRIFT",
                        "matrix already stopped differently",
                    )
                    receipt_path = self.publication_dir / "matrix-stop.json"
                    expected_receipt = self._finalize(existing_stop["receipt"])
                    if not receipt_path.exists():
                        self._write_publication(
                            "matrix-stop.json", existing_stop["receipt"]
                        )
                    published_receipt = read_record(receipt_path)
                    require(
                        published_receipt == expected_receipt,
                        "EVIDENCE_INCOMPLETE",
                        "persisted matrix stop receipt differs",
                    )
                    return published_receipt

                self._require_state(state, {"MATRIX_ACTIVE"})
                self.adapter.check_masters(self.profile)
                ledger = self._load_ledger()
                observed_job_ids = self.adapter.reconcile_authority(
                    self.profile, self.authority["scheduler_authority_token"]
                )
                registered_job_ids = {
                    item["job_id"]
                    for item in ledger["entries"]
                    if isinstance(item.get("job_id"), str)
                }
                require(
                    set(observed_job_ids) == registered_job_ids,
                    "AUTHORITY_RECONCILIATION_REQUIRED",
                    "scheduler and ledger job identities differ",
                )
                plan = self._current_plan(state)
                jobs = {item["role"]: item for item in plan["jobs"]}
                require(
                    trigger_job_role in jobs,
                    "PLAN_DRIFT",
                    "unknown matrix stop trigger",
                )
                attempts = state.get("attempts", {})
                require(
                    attempts
                    and all(
                        item.get("state") == "RESULT_VALIDATED"
                        for item in attempts.values()
                    ),
                    "PLAN_DRIFT",
                    "matrix stop requires every attempt settled",
                )
                trigger_attempts = [
                    (key, item)
                    for key, item in attempts.items()
                    if item.get("job_role") == trigger_job_role
                ]
                require(
                    len(trigger_attempts) >= jobs[trigger_job_role]["max_attempts"]
                    and all(item.get("passed") is False for _, item in trigger_attempts),
                    "PLAN_DRIFT",
                    "matrix stop trigger is not exhausted and failed",
                )
                passed_roles, exhausted_roles = self._role_outcomes(state, plan)
                attempted_roles = {
                    item["job_role"] for item in attempts.values()
                }
                require(
                    attempted_roles <= passed_roles | exhausted_roles,
                    "PLAN_DRIFT",
                    "matrix stop cannot abandon retry-eligible attempts",
                )
                stopped_roles = sorted(set(jobs) - attempted_roles)
                require(stopped_roles, "PLAN_DRIFT", "matrix has no unstarted roles")

                trigger_receipts = []
                for key, item in sorted(trigger_attempts):
                    receipt_path = self.publication_dir / f"job-{key}.json"
                    require(
                        receipt_path.is_file(),
                        "EVIDENCE_INCOMPLETE",
                        "trigger job receipt missing",
                    )
                    trigger_receipt = read_record(receipt_path)
                    require(
                        trigger_receipt.get("authority_id") == self.authority_id
                        and trigger_receipt.get("run_id") == self.run_id
                        and trigger_receipt.get("package_id") == self.package_id
                        and trigger_receipt.get("source_commit") == self.source_commit
                        and trigger_receipt.get("plan_id") == item["plan_id"]
                        and trigger_receipt.get("job_role") == trigger_job_role
                        and trigger_receipt.get("attempt_index")
                        == item["attempt_index"]
                        and trigger_receipt.get("job_id") == item["job_id"]
                        and trigger_receipt.get("passed") is False
                        and trigger_receipt.get("result") == item.get("result"),
                        "EVIDENCE_INCOMPLETE",
                        "trigger job receipt identity mismatch",
                    )
                    trigger_receipts.append(
                        {
                            "attempt_index": item["attempt_index"],
                            "job_id": item["job_id"],
                            "sha256": sha256_file(receipt_path),
                        }
                    )
                receipt = self._common(
                    "matrix_stop_receipt", plan_id=state["current_plan_id"]
                )
                receipt.update(
                    {
                        "classification": "NOT_EXECUTED_UPSTREAM_FAILURE",
                        "ledger_head_sha256": ledger.get("head_sha256"),
                        "reason_code": reason_code,
                        "stopped_roles": stopped_roles,
                        "trigger_job_receipts": trigger_receipts,
                        "trigger_job_role": trigger_job_role,
                    }
                )
                require(
                    isinstance(receipt["ledger_head_sha256"], str)
                    and HEX64_PATTERN.fullmatch(receipt["ledger_head_sha256"])
                    is not None,
                    "AUTHORITY_INVALID",
                    "matrix stop ledger head",
                )
                for role in stopped_roles:
                    self._event(
                        state,
                        "UNREGISTERED",
                        "NOT_EXECUTED_UPSTREAM_FAILURE",
                        scope="role",
                        plan_id=state["current_plan_id"],
                        job_role=role,
                    )
                state["matrix_stop"] = {
                    "reason_code": reason_code,
                    "receipt": receipt,
                    "stopped_roles": stopped_roles,
                    "trigger_job_role": trigger_job_role,
                }
                self._settle_matrix_if_complete(state, plan)
                require(
                    state["run_state"] == "MATRIX_SETTLED",
                    "PLAN_DRIFT",
                    "matrix stop did not settle complete matrix",
                )
                self._save_state(state)
                self._write_publication("matrix-stop.json", receipt)
                return read_record(self.publication_dir / "matrix-stop.json")

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

    def register_cancelled_recovery(
        self, job_role: str, attempt_index: int, declaration: dict[str, Any]
    ) -> dict[str, Any]:
        """Bind a canceled attempt's recovery target from collected evidence."""
        key = f"{validate_id(job_role, 'job role')}.{attempt_index}"
        self.adapter.check_masters(self.profile)
        require(
            self.provider_api_version == 2,
            "PLAN_DRIFT",
            "cancellation recovery requires provider revision 2",
        )
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"COLLECTED"})
            attempt = state.get("attempts", {}).get(key)
            require(
                isinstance(attempt, dict)
                and attempt.get("state") == "RESULT_VALIDATED"
                and attempt.get("passed") is False,
                "PLAN_DRIFT",
                "cancellation recovery source is not a failed settled attempt",
            )
            result = attempt.get("result")
            require(
                isinstance(result, dict) and result.get("state") == "CANCELLED",
                "PLAN_DRIFT",
                "cancellation recovery requires scheduler cancellation",
            )
            prior_job = read_record(self.publication_dir / f"job-{key}.json")
            if prior_job.get("passed") is True:
                correction = read_record(
                    self.publication_dir / f"cancellation-correction-{key}.json"
                )
                require(
                    correction.get("corrected_passed") is False
                    and correction.get("prior_job_receipt_sha256")
                    == prior_job["record_sha256"],
                    "EVIDENCE_INCOMPLETE",
                    "cancellation correction lineage",
                )
            require(
                attempt.get("cancel_acknowledgement", {}).get("job_id")
                == attempt.get("job_id"),
                "EVIDENCE_INCOMPLETE",
                "cancellation acknowledgement",
            )
            require(
                "cancelled_recovery" not in attempt and "recovery" not in state,
                "PLAN_DRIFT",
                "cancellation recovery already registered",
            )

            evidence_path = validate_relative_path(
                declaration.get("binding_evidence_path"), "binding evidence"
            )
            require(
                evidence_path.startswith("results/") and evidence_path.endswith("/setup.json"),
                "EVIDENCE_INCOMPLETE",
                "cancellation recovery requires collected setup evidence",
            )
            evidence_file = self.publication_dir / "evidence" / evidence_path
            require(
                evidence_file.is_file() and not evidence_file.is_symlink(),
                "EVIDENCE_INCOMPLETE",
                "binding evidence is unavailable",
            )
            evidence_sha256 = declaration.get("binding_evidence_sha256")
            collection = read_record(self.publication_dir / "collection.json")
            collected_identity = next(
                (
                    item
                    for item in collection.get("sanitized_files", [])
                    if item.get("logical_name") == evidence_path
                ),
                None,
            )
            require(
                isinstance(evidence_sha256, str)
                and HEX64_PATTERN.fullmatch(evidence_sha256) is not None
                and isinstance(collected_identity, dict)
                and collected_identity.get("sha256") == evidence_sha256
                and sha256_file(evidence_file) == evidence_sha256,
                "EVIDENCE_INCOMPLETE",
                "binding evidence is not authenticated by prior collection",
            )
            evidence = read_json(evidence_file)
            evidence_record_sha256 = evidence.get("record_sha256")
            evidence_semantic = dict(evidence)
            evidence_semantic.pop("record_sha256", None)
            authentication = evidence.get("authentication")
            require(
                evidence.get("valid") is True
                and isinstance(authentication, dict)
                and authentication.get("execution_identity_authenticated") is True
                and authentication.get("asset_identities_authenticated") is True
                and isinstance(evidence_record_sha256, str)
                and HEX64_PATTERN.fullmatch(evidence_record_sha256) is not None
                and sha256_bytes(canonical_bytes(evidence_semantic))
                == evidence_record_sha256,
                "EVIDENCE_INCOMPLETE",
                "collected setup record authentication",
            )
            execution = evidence.get("execution_identity")
            require(
                isinstance(execution, dict)
                and execution.get("job_id") == attempt.get("job_id")
                and execution.get("node") == result.get("node")
                and execution.get("role") == job_role
                and execution.get("run_id") == self.run_id
                and execution.get("source_commit") == self.source_commit,
                "CLEANUP_TARGET_INVALID",
                "collected setup and scheduler identity differ",
            )

            target = declaration.get("target")
            require(isinstance(target, str), "CLEANUP_TARGET_INVALID", "recovery target")
            validate_shell_scalar(target, "recovery target")
            target_path = Path(target)
            derivation_asset = declaration.get("target_derivation_asset")
            plan = self._current_plan(state)
            asset = next(
                (
                    item
                    for item in plan.get("assets", [])
                    if item.get("logical_name") == derivation_asset
                ),
                None,
            )
            require(
                isinstance(asset, dict) and asset.get("executable") is True,
                "CLEANUP_TARGET_INVALID",
                "target derivation asset",
            )
            asset_path = Path(asset["local_path"])
            require(
                asset_path.is_file()
                and not asset_path.is_symlink()
                and sha256_file(asset_path) == asset.get("sha256"),
                "ASSET_IDENTITY_MISMATCH",
                "target derivation asset identity",
            )
            derivations = re.findall(
                r"^target=\$\{TMPDIR:-/tmp\}/([A-Za-z0-9._-]+)-\$role-\$SLURM_JOB_ID$",
                asset_path.read_text(encoding="utf-8"),
                flags=re.MULTILINE,
            )
            require(
                len(derivations) == 1,
                "CLEANUP_TARGET_INVALID",
                "target derivation is not uniquely frozen",
            )
            expected_target = f"/tmp/{derivations[0]}-{job_role}-{attempt['job_id']}"
            require(
                target_path == Path(expected_target),
                "CLEANUP_TARGET_INVALID",
                "recovery target differs from the frozen job derivation",
            )
            marker_sha256 = declaration.get("marker_sha256")
            require(
                isinstance(marker_sha256, str)
                and HEX64_PATTERN.fullmatch(marker_sha256) is not None
                and execution.get("owner_marker_sha256") == marker_sha256,
                "CLEANUP_TARGET_INVALID",
                "collected setup marker identity",
            )
            uid = declaration.get("uid")
            device = declaration.get("device")
            require(
                isinstance(uid, int)
                and uid >= 0
                and isinstance(device, int)
                and device >= 0,
                "CLEANUP_TARGET_INVALID",
                "recovery ownership",
            )
            recovery_target = {
                "device": device,
                "job_id": attempt["job_id"],
                "marker_sha256": marker_sha256,
                "node": result["node"],
                "target": target,
                "uid": uid,
            }
            receipt = self._common(
                "cancelled_recovery_registration_receipt",
                plan_id=state["current_plan_id"],
            )
            receipt.update(
                {
                    "attempt_index": attempt_index,
                    "binding_evidence_path": evidence_path,
                    "binding_evidence_sha256": evidence_sha256,
                    "job_id": attempt["job_id"],
                    "job_role": job_role,
                    "recovery_target": recovery_target,
                    "target_derivation_asset": derivation_asset,
                }
            )
            publication_name = f"cancelled-recovery-registration-{key}.json"
            record_sha256 = self._write_publication(publication_name, receipt)
            attempt["cancelled_recovery"] = {
                **receipt,
                "record_sha256": record_sha256,
            }
            prior_collection = self.publication_dir / "collection.json"
            require(prior_collection.is_file(), "EVIDENCE_INCOMPLETE", "prior collection receipt")
            atomic_write(
                self.publication_dir / "collection-pre-recovery.json",
                read_json(prior_collection),
            )
            state["pre_recovery_collection"] = state["collection"]
            self._event(
                state,
                "COLLECTED",
                "MATRIX_SETTLED",
                plan_id=state["current_plan_id"],
            )
            state["run_state"] = "MATRIX_SETTLED"
            self._save_state(state)
            return read_record(self.publication_dir / publication_name)

    def recover(self, job_role: str, attempt_index: int) -> str:
        """Submit the one reserved marker-bound recovery on the original node."""
        key = f"{validate_id(job_role, 'job role')}.{attempt_index}"
        self.adapter.check_masters(self.profile)
        require(self.provider_api_version == 2, "PLAN_DRIFT", "recovery requires provider revision 2")
        with directory_lock(self.budget_lock):
            ledger = self._load_ledger()
            observed_job_ids = self.adapter.reconcile_authority(
                self.profile, self.authority["scheduler_authority_token"]
            )
            registered_job_ids = {
                item["job_id"]
                for item in ledger["entries"]
                if isinstance(item.get("job_id"), str)
            }
            require(
                set(observed_job_ids) == registered_job_ids,
                "AUTHORITY_RECONCILIATION_REQUIRED",
                "scheduler and ledger job identities differ",
            )
            with directory_lock(self.run_lock):
                state = self._load_state()
                self._require_state(state, {"MATRIX_SETTLED"})
                require("recovery" not in state, "PLAN_DRIFT", "recovery already registered")
                attempt = state.get("attempts", {}).get(key)
                require(
                    isinstance(attempt, dict)
                    and attempt.get("state") == "RESULT_VALIDATED",
                    "PLAN_DRIFT",
                    "recovery source is not settled",
                )
                result = attempt.get("result")
                require(isinstance(result, dict), "EVIDENCE_INCOMPLETE", "recovery source result")
                gates = result.get("gates")
                cancelled_recovery = attempt.get("cancelled_recovery")
                if isinstance(cancelled_recovery, dict):
                    require(
                        result.get("state") == "CANCELLED"
                        and attempt.get("passed") is False,
                        "PLAN_DRIFT",
                        "registered cancellation recovery source",
                    )
                    recovery_target = cancelled_recovery.get("recovery_target")
                else:
                    require(
                        isinstance(gates, dict)
                        and gates.get("job_local_cleanup") is False,
                        "PLAN_DRIFT",
                        "recovery requires unresolved job-local cleanup",
                    )
                    recovery_target = result.get("recovery_target")
                require(isinstance(recovery_target, dict), "EVIDENCE_INCOMPLETE", "recovery target")
                require(
                    recovery_target.get("job_id") == attempt.get("job_id")
                    and recovery_target.get("node") == result.get("node"),
                    "CLEANUP_TARGET_INVALID",
                    "scheduler and marker recovery identity differ",
                )
                recovery_token = state.get("recovery_token")
                require(isinstance(recovery_token, str), "RESOURCE_CEILING", "recovery reserve missing")
                latest = next(
                    (item for item in reversed(ledger["entries"]) if item.get("token") == recovery_token),
                    None,
                )
                require(
                    isinstance(latest, dict) and latest.get("status") == "reserved",
                    "RESOURCE_CEILING",
                    "recovery reserve is not available",
                )
                try:
                    recovery_attempt = dict(attempt)
                    recovery_attempt["result"] = {**result, "recovery_target": recovery_target}
                    job_id = self.adapter.recover(
                        self.profile,
                        self._current_plan(state),
                        recovery_attempt,
                        recovery_token,
                    )
                except ToolkitError as error:
                    if error.code != "SUBMISSION_OUTCOME_UNKNOWN":
                        raise
                    matches = self.adapter.reconcile(self.profile, recovery_token)
                    require(
                        len(matches) == 1,
                        "SUBMISSION_OUTCOME_UNKNOWN",
                        "recovery submission token is ambiguous",
                    )
                    job_id = matches[0]
                require(job_id.isdigit(), "SUBMISSION_OUTCOME_UNKNOWN", "recovery job ID")
                self._append_ledger_transition(ledger, recovery_token, "submitted", job_id=job_id)
                state["recovery"] = {
                    "attempt_index": 0,
                    "job_id": job_id,
                    "job_role": "toolkit-recovery",
                    "original_attempt_index": attempt_index,
                    "original_job_id": attempt["job_id"],
                    "original_job_role": job_role,
                    "original_node": recovery_target["node"],
                    "state": "SUBMITTED",
                    "target_sha256": sha256_bytes(recovery_target["target"].encode()),
                    "token": recovery_token,
                }
                self._event(
                    state,
                    "RESERVED",
                    "SUBMITTED",
                    scope="recovery",
                    plan_id=state["current_plan_id"],
                    job_role="toolkit-recovery",
                    attempt_index=0,
                )
                self._save_ledger(ledger)
                self._save_state(state)
                return job_id

    def observe_recovery(self) -> dict[str, Any]:
        """Settle and authenticate the registered exact-node recovery job."""
        self.adapter.check_masters(self.profile)
        require(self.provider_api_version == 2, "PLAN_DRIFT", "recovery requires provider revision 2")
        with directory_lock(self.budget_lock):
            with directory_lock(self.run_lock):
                state = self._load_state()
                self._require_state(state, {"MATRIX_SETTLED"})
                recovery = state.get("recovery")
                require(
                    isinstance(recovery, dict) and recovery.get("state") == "SUBMITTED",
                    "PLAN_DRIFT",
                    "recovery is not submitted",
                )
                result = self.adapter.observe_recovery(
                    self.profile, self._current_plan(state), recovery
                )
                require(
                    result.get("terminal") is True
                    and result.get("state") in TERMINAL_JOB_STATES,
                    "JOB_TERMINAL_MISMATCH",
                    "recovery",
                )
                require(
                    isinstance(result.get("actual_gpu_minutes"), int)
                    and result["actual_gpu_minutes"] >= 0,
                    "EVIDENCE_INCOMPLETE",
                    "recovery accounting",
                )
                gates = result.get("gates")
                passed = (
                    result.get("exit_code") == 0
                    and isinstance(gates, dict)
                    and bool(gates)
                    and all(value is True for value in gates.values())
                )
                require(passed, "CLEANUP_INCOMPLETE", "exact-node recovery did not prove absence")
                recovery.update({"state": "RESULT_VALIDATED", "passed": True, "result": result})
                self._event(
                    state,
                    "SUBMITTED",
                    "RESULT_VALIDATED",
                    scope="recovery",
                    plan_id=state["current_plan_id"],
                    job_role="toolkit-recovery",
                    attempt_index=0,
                )
                ledger = self._load_ledger()
                self._append_ledger_transition(
                    ledger,
                    recovery["token"],
                    "settled",
                    actual_gpu_minutes=result["actual_gpu_minutes"],
                    absence_proof="JOB_LOCAL_ABSENT",
                )
                self._save_ledger(ledger)
                self._save_state(state)
                receipt = self._common("recovery_receipt", plan_id=state["current_plan_id"])
                receipt.update({"job_id": recovery["job_id"], "passed": True, "result": result})
                self._write_publication("recovery.json", receipt)
                return receipt

    def collect(self) -> dict[str, Any]:
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"MATRIX_SETTLED"})
            plan = self._current_plan(state)
            recovery = state.get("recovery")
            recovery_result: dict[str, Any] | None = None
            recovery_evidence: tuple[str, str] | None = None
            if self.provider_api_version == 2 and recovery is not None:
                require(
                    isinstance(recovery, dict)
                    and recovery.get("state") == "RESULT_VALIDATED",
                    "EVIDENCE_INCOMPLETE",
                    "collection requires settled recovery",
                )
                recovery_result = recovery.get("result")
                require(
                    isinstance(recovery_result, dict),
                    "EVIDENCE_INCOMPLETE",
                    "observed recovery result missing",
                )
                recovery_gate_sha256 = recovery_result.get(
                    "gate_receipt_sha256"
                )
                require(
                    isinstance(recovery_gate_sha256, str)
                    and HEX64_PATTERN.fullmatch(recovery_gate_sha256) is not None,
                    "EVIDENCE_INCOMPLETE",
                    "observed recovery gate receipt identity missing",
                )
                recovery_plan = plan.get("recovery_contingency")
                require(
                    isinstance(recovery_plan, dict),
                    "EVIDENCE_INCOMPLETE",
                    "configured recovery contingency missing",
                )
                recovery_evidence = (
                    validate_relative_path(
                        recovery_plan.get("gate_receipt"),
                        "recovery gate receipt",
                    ),
                    recovery_gate_sha256,
                )
            quarantine = self.run_dir / "private" / "quarantine"
            if quarantine.exists() and any(quarantine.iterdir()):
                suffix = 1
                retained = quarantine.with_name(f"quarantine.failed-{suffix}")
                while retained.exists():
                    suffix += 1
                    retained = quarantine.with_name(f"quarantine.failed-{suffix}")
                os.replace(quarantine, retained)
            quarantine.mkdir(parents=True, exist_ok=True, mode=0o700)
            result = self.adapter.collect(self.profile, plan, quarantine)
            require(result.get("download_promoted") is True, "TRANSFER_INCOMPLETE", "download not promoted")
            allowed_evidence = set(plan["evidence_allowlist"])
            logical_name = result.get("logical_name")
            if self.provider_api_version == 2:
                require(
                    isinstance(logical_name, str)
                    and logical_name.endswith(".tar"),
                    "EVIDENCE_INCOMPLETE",
                    "v2 collection requires sparse archive metadata",
                )
            if isinstance(logical_name, str) and logical_name.endswith(".tar"):
                archive_path = quarantine / validate_relative_path(logical_name, "evidence archive")
                evidence_volume = plan.get("evidence_volume", {})
                present = result.get("present")
                absent = result.get("absent")
                require(
                    isinstance(present, list)
                    and isinstance(absent, list)
                    and all(isinstance(item, str) for item in present + absent),
                    "EVIDENCE_INCOMPLETE",
                    "evidence present/absent partition",
                )
                require(
                    present == sorted(set(present))
                    and absent == sorted(set(absent))
                    and not set(present) & set(absent)
                    and set(present) | set(absent) == allowed_evidence,
                    "EVIDENCE_INCOMPLETE",
                    "evidence partition differs from allowlist",
                )
                extracted_members = extract_validated_archive(
                    archive_path,
                    quarantine / "extracted",
                    max_files=evidence_volume.get(
                        "maximum_files",
                        self.profile.get("max_evidence_files", 1000),
                    ),
                    max_bytes=evidence_volume.get(
                        "maximum_expanded_bytes",
                        self.profile.get(
                            "max_evidence_expanded_bytes", 50_000_000
                        ),
                    ),
                    max_file_bytes=evidence_volume.get(
                        "maximum_file_bytes",
                        self.profile.get("max_evidence_file_bytes", 10_000_000),
                    ),
                    allowed_members=allowed_evidence,
                )
                require(
                    set(extracted_members) == set(present)
                    and len(extracted_members) == len(present),
                    "EVIDENCE_INCOMPLETE",
                    "archive members differ from reported present evidence",
                )
                extracted_regular_files = {
                    str(path.relative_to(quarantine / "extracted"))
                    for path in (quarantine / "extracted").rglob("*")
                    if path.is_file()
                }
                require(
                    extracted_regular_files == set(present),
                    "EVIDENCE_INCOMPLETE",
                    "reported present evidence includes a nonregular member",
                )
                archive_path.unlink()
                required_attempt_paths: set[str] = set()
                gate_identities: dict[str, str] = {}
                for attempt in state.get("attempts", {}).values():
                    require(
                        attempt.get("state") == "RESULT_VALIDATED",
                        "EVIDENCE_INCOMPLETE",
                        "collection requires settled attempts",
                    )
                    job = next(
                        item
                        for item in plan["jobs"]
                        if item["role"] == attempt["job_role"]
                    )
                    attempt_id = f"{attempt['job_role']}.{attempt['attempt_index']}"
                    required_attempt_paths.update(
                        {
                            f"slurm/{attempt_id}.out",
                            f"slurm/{attempt_id}.err",
                        }
                    )
                    if attempt.get("result", {}).get("state") != "CANCELLED":
                        gate_sha256 = attempt.get("result", {}).get(
                            "gate_receipt_sha256"
                        )
                        require(
                            isinstance(gate_sha256, str)
                            and HEX64_PATTERN.fullmatch(gate_sha256) is not None,
                            "EVIDENCE_INCOMPLETE",
                            "observed gate receipt identity missing",
                        )
                        existing_gate_sha256 = gate_identities.get(
                            job["gate_receipt"]
                        )
                        require(
                            existing_gate_sha256 in {None, gate_sha256},
                            "EVIDENCE_INCOMPLETE",
                            "attempts sharing a gate path have conflicting identities",
                        )
                        gate_identities[job["gate_receipt"]] = gate_sha256
                        required_attempt_paths.add(job["gate_receipt"])
                if recovery_evidence is not None:
                    recovery_gate_path, recovery_gate_sha256 = recovery_evidence
                    recovery_paths = {
                        recovery_gate_path,
                        "slurm/toolkit-recovery.0.out",
                        "slurm/toolkit-recovery.0.err",
                    }
                    require(
                        recovery_paths <= set(present),
                        "EVIDENCE_INCOMPLETE",
                        "recovery evidence missing",
                    )
                    existing_gate_sha256 = gate_identities.get(
                        recovery_gate_path
                    )
                    require(
                        existing_gate_sha256 in {None, recovery_gate_sha256},
                        "EVIDENCE_INCOMPLETE",
                        "recovery gate path has a conflicting identity",
                    )
                    gate_identities[recovery_gate_path] = recovery_gate_sha256
                    required_attempt_paths.update(recovery_paths)
                require(
                    required_attempt_paths <= set(present),
                    "EVIDENCE_INCOMPLETE",
                    "submitted attempt evidence missing",
                )
                if recovery_evidence is not None:
                    recovery_gate_path, recovery_gate_sha256 = recovery_evidence
                    require(
                        sha256_file(
                            quarantine / "extracted" / recovery_gate_path
                        )
                        == recovery_gate_sha256,
                        "EVIDENCE_INCOMPLETE",
                        "collected recovery gate receipt changed after observation",
                    )
                for required_path, expected_sha256 in gate_identities.items():
                    require(
                        sha256_file(quarantine / "extracted" / required_path)
                        == expected_sha256,
                        "EVIDENCE_INCOMPLETE",
                        "collected gate receipt changed after observation",
                    )
            forbidden = tuple(self.profile.get("forbidden_publication_substrings", []))
            evidence_paths = [path for path in quarantine.rglob("*") if path.is_file()]
            logical_paths: list[tuple[Path, str]] = []
            for path in evidence_paths:
                if logical_name and str(path.relative_to(quarantine)) == logical_name:
                    logical = logical_name
                elif _is_relative_to(path, quarantine / "extracted"):
                    logical = str(path.relative_to(quarantine / "extracted"))
                else:
                    logical = str(path.relative_to(quarantine))
                require(logical in allowed_evidence, "ALLOWLIST_VIOLATION", f"unregistered evidence: {logical}")
                evidence_volume = plan.get("evidence_volume", {})
                require(
                    path.stat().st_size
                    <= evidence_volume.get(
                        "maximum_file_bytes",
                        self.profile.get("max_evidence_file_bytes", 10_000_000),
                    ),
                    "EVIDENCE_INCOMPLETE",
                    str(path),
                )
                logical_paths.append((path, logical))
            if self.provider_api_version == 2:
                from .hardening import create_raw_collected

                cleanup_marker_sha256 = result.get("cleanup_marker_sha256")
                gates = {
                    f"{attempt['job_role']}.{name}": passed
                    for attempt in state.get("attempts", {}).values()
                    if isinstance(attempt.get("result", {}).get("gates"), dict)
                    for name, passed in attempt["result"]["gates"].items()
                }
                if isinstance(recovery_result, dict) and isinstance(
                    recovery_result.get("gates"), dict
                ):
                    gates.update(
                        {
                            f"toolkit-recovery.{name}": passed
                            for name, passed in recovery_result["gates"].items()
                        }
                    )
                raw = create_raw_collected(
                    self.authority_id,
                    self.run_id,
                    state["current_plan_id"],
                    [{"logical_name": logical, "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path, logical in logical_paths],
                    gates,
                    cleanup_marker_sha256,
                )
                state["raw_collected"] = raw
                state["collection"] = result
                self._save_state(state)
            sanitized_files: list[dict[str, Any]] = []
            projection_receipts: list[dict[str, Any]] = []
            for path, logical in logical_paths:
                if self.provider_api_version == 2:
                    from .hardening import project_evidence

                    if path.suffix == ".json":
                        media_type = "application/json"
                    elif path.suffix in {".npz", ".pt"}:
                        media_type = "application/octet-stream"
                    else:
                        media_type = "text/plain"
                    projected, projection = project_evidence(
                        path.read_bytes(),
                        media_type=media_type,
                        replacements=plan.get("evidence_replacements", []),
                        forbidden=forbidden,
                        raw_parent_sha256=sha256_file(path),
                    )
                    projection_receipts.append({"logical_name": logical, **projection})
                else:
                    try:
                        text = path.read_text(encoding="utf-8")
                    except UnicodeDecodeError as error:
                        raise ToolkitError("SANITIZATION_FAILED", f"non-text evidence: {path.name}") from error
                    require(not any(item and item in text for item in forbidden), "SANITIZATION_FAILED", path.name)
                    projected = text.encode("utf-8")
                destination = self.publication_dir / "evidence" / logical
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = destination.with_name(f".{destination.name}.part")
                if self.provider_api_version == 2:
                    temporary.write_bytes(projected)
                else:
                    temporary.write_text(text, encoding="utf-8")
                os.replace(temporary, destination)
                sanitized_files.append({"logical_name": logical, "bytes": destination.stat().st_size, "sha256": sha256_file(destination)})
            self._event(state, "MATRIX_SETTLED", "COLLECTED", plan_id=state["current_plan_id"])
            state["run_state"] = "COLLECTED"
            state["collection"] = result
            if projection_receipts:
                state["projection_receipts"] = projection_receipts
            self._save_state(state)
            receipt = self._common("collection_receipt", plan_id=state["current_plan_id"])
            receipt.update(result)
            receipt["sanitized_files"] = sorted(sanitized_files, key=lambda item: item["logical_name"])
            self._write_publication("collection.json", receipt)
            return receipt

    def _clean_locked(self) -> dict[str, Any]:
        state = self._load_state()
        self._require_state(state, {"COLLECTED"})
        recovery = state.get("recovery")
        if recovery is not None:
            require(
                isinstance(recovery, dict) and recovery.get("state") == "RESULT_VALIDATED",
                "CLEANUP_INCOMPLETE",
                "recovery is not settled",
            )
        stopped_roles = set(state.get("matrix_stop", {}).get("stopped_roles", []))
        result = self.adapter.clean(
            self.profile,
            self._current_plan(state),
            recovery,
            stopped_roles,
        )
        require(result.get("remote_absent") is True, "CLEANUP_INCOMPLETE", "remote run remains")
        allowed_cleanup = {"verified_absent"} if self.provider_api_version == 2 else {"scheduler_purged", "verified_absent"}
        require(result.get("job_local_cleanup") in allowed_cleanup, "CLEANUP_INCOMPLETE", "job-local cleanup")
        if self.provider_api_version == 2:
            recovery_token = state.get("recovery_token")
            require(isinstance(recovery_token, str), "CLEANUP_INCOMPLETE", "recovery reserve missing")
            ledger = self._load_ledger()
            if recovery is None:
                self._append_ledger_transition(ledger, recovery_token, "released", release_reason="verified-cleanup")
            self._save_ledger(ledger)
        self._event(state, "COLLECTED", "CLEANED", plan_id=state["current_plan_id"])
        state["run_state"] = "CLEANED"
        state["cleanup"] = result
        self._save_state(state)
        receipt = self._common("cleanup_receipt", plan_id=state["current_plan_id"])
        receipt.update({"remote_root_hash": sha256_bytes(self._current_plan(state)["remote_run_root"].encode()), **result})
        self._write_publication("cleanup.json", receipt)
        return receipt

    def clean(self) -> dict[str, Any]:
        self.adapter.check_masters(self.profile)
        if self.provider_api_version == 2:
            with directory_lock(self.budget_lock):
                with directory_lock(self.run_lock):
                    return self._clean_locked()
        with directory_lock(self.run_lock):
            return self._clean_locked()

    def abort(self) -> dict[str, Any]:
        """Close a run before submission using its exact registered root."""
        self.adapter.check_masters(self.profile)
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"PREPARED", "STAGED", "VERIFIED"})
            require(not state.get("attempts"), "PLAN_DRIFT", "abort is pre-submission only")
            prior = state["run_state"]
            if prior == "PREPARED":
                result = {"remote_absent": True, "job_local_cleanup": "not_started"}
            else:
                result = self.adapter.abort(self.profile, self._current_plan(state))
            require(result.get("remote_absent") is True, "CLEANUP_INCOMPLETE", "remote run remains")
            require(result.get("job_local_cleanup") == "not_started", "CLEANUP_INCOMPLETE", "pre-submission cleanup classification")
            self._event(state, prior, "ABORTED", plan_id=state["current_plan_id"])
            state["run_state"] = "ABORTED"
            state["abort"] = result
            self._save_state(state)
            receipt = self._common("abort_receipt", plan_id=state["current_plan_id"])
            receipt.update({"terminal": "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION", **result})
            self._write_publication("abort.json", receipt)
            return receipt

    def close(self) -> dict[str, Any]:
        with directory_lock(self.run_lock):
            state = self._load_state()
            self._require_state(state, {"CLEANED"})
            receipt = self._common("terminal_receipt", plan_id=state["current_plan_id"])
            receipt.update({"terminal": "LEMHI-TOOLKIT-RUN-CLOSED", "attempt_count": len(state.get("attempts", {})), "stopped_role_count": len(state.get("matrix_stop", {}).get("stopped_roles", [])), "cleanup": state["cleanup"]})
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
