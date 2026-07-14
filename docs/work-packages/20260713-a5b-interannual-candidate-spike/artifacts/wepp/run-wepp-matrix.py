#!/usr/bin/env python3
"""Execute and seal the frozen A5b WEPP response matrix.

Production usage:
  run-wepp-matrix.py CANDIDATE_MANIFEST CANDIDATE_CLI_DIR \
      CLIGEN_BINARY OUTPUT_DIR [--wepp-repo PATH] [--workers 1..4]

Self-test usage:
  run-wepp-matrix.py --self-test [--wepp-repo PATH]

The production path is intentionally all-or-nothing.  It verifies the accepted
A5a faithful-off evidence and sealed A5b candidate evidence, builds the exact
pinned WEPP executable from a fresh Git archive, executes 2,176 isolated runs,
validates every response through the frozen schema and semantic validator,
publishes canonical archives and an index, and only then performs the
rollback-safe candidate-CLI removal transition.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
from typing import Any, BinaryIO, Iterable

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
PACKAGE = ROOT / "docs/work-packages/20260713-a5b-interannual-candidate-spike"
A5A_PACKAGE = ROOT / "docs/work-packages/20260712-a5a-quality-v3-observed-corpus"

RUNNER = Path(__file__).resolve()
CAMPAIGN = RUNNER.with_name("wepp-campaign-v1.md")
RESPONSE_SCHEMA = ROOT / "docs/specifications/a5-wepp-response-v1.schema.json"
RESPONSE_PROTOCOL = A5A_PACKAGE / "artifacts/wepp-response-protocol.md"
RESPONSE_VERIFIER = A5A_PACKAGE / "artifacts/verify-wepp-response-schema.py"
CANDIDATE_VERIFIER = PACKAGE / "artifacts/runtime/verify-a5b-evidence.py"
BASELINE_VERIFIER = PACKAGE / "artifacts/freeze/verify-accepted-a5a-baseline.py"
BASELINE_MANIFEST = A5A_PACKAGE / "artifacts/baseline-run-manifest-v1.json"
BASELINE_ARCHIVE = A5A_PACKAGE / "artifacts/baseline-evidence-v1.tar.gz"
PRE_CANDIDATE_FREEZE = PACKAGE / "artifacts/freeze/pre-candidate-freeze-v1.json"

DEFAULT_WEPP_REPO = Path("/Users/roger/src/wepp-forest")
BASELINE_TARGET = ROOT / "target/a5a-baseline-v1"

SOURCE_COMMIT = "c3a082e2eee00ab010f0eb1cb33d01114bdc0216"
WEPP_SHA256 = "dccb55f3980e287ada5541b7801f9b9fa79b4b1d65addb97d6914317bc4a4527"
WEPP_BYTES = 818_952
LIBGFORTRAN_SHA256 = "624e083bf9ebdcd8c6713ef8adaf1aa49ec2a1756cd0dbaed553fd48fc3e6950"
LIBQUADMATH_SHA256 = "773034db811835ca98358409e647c46a97cb9dc3f4fbb6956c858e5a31cdf580"
GFORTRAN_VERSION = "GNU Fortran (Homebrew GCC 15.2.0_1) 15.2.0"
SYSTEM_LINKER = Path("/usr/bin/ld")
SYSTEM_LINKER_SHA256 = "12bed4523661307059b879b9b54e77a73176e9d27d27a0e40363271d8f0668ba"
SYSTEM_LINKER_VERSION = "@(#)PROGRAM:ld PROJECT:ld-1266.8"
LINK_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
COMPILE_FLAGS = (
    "-c",
    "-fno-align-commons",
    "-O2",
    "-ffixed-form",
    "-ffixed-line-length-72",
    "-ffpe-trap=invalid,zero,overflow",
    "-finit-local-zero",
)
WEPP_VERSION_OUTPUT = "VERSION 2020.500"
SUCCESS_BANNER = "WEPP COMPLETED HILLSLOPE SIMULATION SUCCESSFULLY"

SCHEMA_SHA256 = "7d006023684f2079ce09e5ab1af21e1154a417eb4295ebf1a02c40d7f7a2e70d"
PROTOCOL_SHA256 = "9cd770d18c04dfde877c91e03304697b107d117bf2e52cc94f1f83e3d99c5800"
VALIDATOR_SHA256 = "05e7a085f146e264c3b34e3f7c04f498f0f4d3dd0c9b0cd17a0f8176221b683b"
BASELINE_MANIFEST_SHA256 = "e6e12a08b7d552edd45481b929271af87530d2821b9b51d5cec066dc76867cbc"
BASELINE_MANIFEST_BYTES = 1_421_606
BASELINE_ARCHIVE_SHA256 = "2fca565b8c3f83632e73050984dce0c619352ac4bb76deed86fb3928f8de15fe"
BASELINE_ARCHIVE_BYTES = 55_928_355

FIXTURE_PREFIX = "tests/fixtures/srivas42_claustrophobic_shortcut_p326/runs"
FIXTURE_HASHES = {
    "p326.man": "dd5cb34c1361a2f543cc5b1a7c7de3027621a2c9437a1c023d8f96b7bbaed60b",
    "p326.slp": "5df68111b44cbb8b8b4b9bd8086fb76d86e19cd592f9995adace2a0354f12ec2",
    "p326.sol": "aa79cae424a79f1991c2995738b48f0367d1eea13c3f287eff7843772516ad88",
    "p326.run": "2bd5161b13b968973be9338bc23bc272faac8f58faea2ff1232a4ac72da4c929",
}
MANAGEMENT_SHA256 = "43ae1f0df3df5d13fe6fe7892fc20792027820c45327ccf9c259d26445d4e0f6"
RUN_HASHES = {
    (30, "general"): "46feaab6a1c3cd6153e289a68c4b47d40268481529a163245f97da6d18fb2a4f",
    (30, "cold_snow"): "dc8b7c661a1f4b9319bb1223f746f0b72817b6c0b0a9447459c924de01ef825c",
    (100, "general"): "79bf8daaa2351b8465f54c977e3502a19dfef39344f64401a373795a11e0333a",
    (100, "cold_snow"): "f30d5a19d00a789a05ce6bb9fbfb7bf951cc33bee3b6b964477d858fbf780ef0",
}

HORIZONS = (30, 100)
REPLICATES = (
    (0, 0, "0x0c8862ed55f21e2e"),
    (1, 17, "0x0c268832683959b1"),
    (2, 101, "0x1a237b2016b95a3f"),
    (3, 503, "0x91328e5fa9a0e916"),
    (4, 1009, "0x0ee45605e7d362c3"),
    (5, 5003, "0xc59c065475f321a3"),
    (6, 10007, "0x9d9ef1d097f866ab"),
    (7, 50021, "0x50984769b3e59a89"),
)
CANDIDATES = (
    ("rank_one_monthly_sd", "interannual_rank_one_monthly_sd_v1", "a5b_rank_one_monthly_sd_v1"),
    ("full_monthly_covariance", "interannual_full_monthly_covariance_v1", "a5b_full_monthly_covariance_v1"),
    ("fourier_eof", "interannual_fourier_eof_v1", "a5b_fourier_eof_v1"),
    ("vector_ar", "interannual_fourier_eof_var1_v1", "a5b_vector_ar_v1"),
    ("gaussian_hmm", "interannual_fourier_eof_hmm2_v1", "a5b_gaussian_hmm_v1"),
    ("spectral_random_phase", "interannual_fourier_eof_spectral_v1", "a5b_spectral_random_phase_v1"),
    (
        "precip_counterfactual",
        "interannual_fourier_eof_precip_counterfactual_v1",
        "a5b_fourier_eof_precip_counterfactual_v1",
    ),
)
CANDIDATE_BY_ID = {row[0]: row for row in CANDIDATES}
COLD_STATIONS = {"co051660", "wy485345", "mn214026", "ak505769", "id106388"}
EXPECTED_STATIONS = (
    "ak505769", "al015478", "az022664", "az028619", "az029654", "ca042257",
    "ca042319", "co051660", "fl083909", "fl086997", "id106388", "mn214026",
    "ms227840", "nm294426", "tx412797", "ut429382", "wy485345",
)
EXPECTED_PROFILES = ("faithful_off", *(candidate[0] for candidate in CANDIDATES))
EXPECTED_COORDINATES = tuple(
    (profile, station, horizon, replicate)
    for profile in EXPECTED_PROFILES
    for station in EXPECTED_STATIONS
    for horizon in HORIZONS
    for replicate, _burn, _seed in REPLICATES
)
EXPECTED_RUNS = 2_176
SELF_TEST_MATRIX_SHA256 = "93c163f85b9de61c48fe97a16c343e1ab50debb22fc39add24aef39fa67eaee1"
SELF_TEST_PUBLICATION_SHA256 = "0d8239949857032dc91781b816575ca7a7fdc2c3af302592c253978592b612e1"
STATISTICS = ("mean", "sd", "p95", "max")
GENERAL_METRICS = ("annual_runoff", "annual_peak_runoff", "annual_soil_loss")
COLD_METRICS = (
    "annual_max_snow_water_state", "annual_snowmelt", "rain_on_snow_runoff",
    "winter_runoff", "winter_soil_loss",
)

MANAGEMENT_ADAPTER_ID = "a5b_wepp_p326_management_repeat_v1"
RUN_ADAPTER_ID = "a5b_wepp_p326_run_v2"
CLIMATE_ADAPTER_ID = "a5b_wepp_cli_install_v1"
EXTRACTION_ADAPTER_ID = "a5b_wepp_p326_response_extractor_v4"
ELEMENT_FIXED_WIDTH_OVERFLOW_POLICY_ID = "a5b_wepp_element_sm_f7_3_overflow_v1"
ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID = "a5b_wepp_element_same_day_aggregation_v1"
ELEMENT_PEAK_RECOVERY_POLICY_ID = "a5b_wepp_element_peakro_f7_3_recovery_v1"
ELEMENT_SM_NUMERIC_INDEX = 7
ELEMENT_SM_HEADER_FIELD = "Sm"
ELEMENT_PEAK_NUMERIC_INDEX = 3
ELEMENT_PEAK_HEADER_FIELD = "PeakRO"
ELEMENT_SM_OVERFLOW_TOKEN = "*******"
ELEMENT_SM_FORTRAN_FORMAT = "F7.3"
ELEMENT_SM_NUMERIC_TOKEN = re.compile(r"-?(?:0|[1-9]\d*)\.\d{3}")
ELEMENT_PEAK_NUMERIC_TOKEN = re.compile(r"(?:0|[1-9]\d*)\.\d{3}")
EVENT_HYDROLOGY_HEADER = "Event-by-event; abbreviated (Metric Units)"
EVENT_HYDROLOGY_PEAK_FORMAT = "F8.2"
EVENT_PEAK_CROSSCHECK_TOLERANCE = 0.006
EVENT_PREAMBLE_TEMPLATE: tuple[str | None, ...] = (
    " Event-by-event; abbreviated (Metric Units)",
    "",
    "",
    "          USDA WATER EROSION PREDICTION PROJECT",
    "          -------------------------------------",
    "",
    "          HILLSLOPE PROFILE AND WATERSHED MODEL",
    "                     VERSION  2020.500",
    "           May 1,           2020",
    "",
    "",
    "               TO REPORT PROBLEMS OR TO BE PUT ON THE MAILING",
    "               LIST FOR FUTURE WEPP MODEL RELEASES, PLEASE CONTACT:",
    "",
    "                    WEPP TECHNICAL SUPPORT",
    "                    USDA-AGRICULTURAL RESEARCH SERVICE",
    "                    NATIONAL SOIL EROSION RESEARCH LABORATORY",
    "                    275 SOUTH RUSSELL STREET",
    "                    WEST LAFAYETTE, IN 47907-2077  USA",
    "",
    "                    PHONE: (765) 494-8673",
    "                      FAX: (765) 494-5948",
    "                    email:  wepp@ecn.purdue.edu",
    "                      URL:  http://topsoil.nserl.purdue.edu",
    "",
    "",
    "     HILLSLOPE INPUT DATA FILES - VERSION  2020.500",
    "      May 1,           2020",
    "",
    "",
    "    MANAGEMENT: a5b.man",
    " MAN. PRACTICE: description 1",
    "                description 2",
    "                description 3",
    "         SLOPE: a5b.slp",
    "       CLIMATE: a5b.cli",
    None,
    "          SOIL: a5b.sol",
    "",
    " *** CAUTION ***",
    " SOIL FILE FORMAT IS NON-STANDARD WEPP",
    " User is solely responsible for entering CORRECT",
    " values for BD, SSC, THETFC, THETDR",
    " *** CAUTION ***",
    "",
    "      PLANE  1 Dutchoven-Kinney comGRV-SIL",
    "",
    "",
    "",
    "HILLSLOPE          1 RESULTS",
    "-------------------",
    "",
    "I.   ABBREVIATED EVENT-BY-EVENT HYDROLOGY",
    "     ----------- -------------- ---------",
    "",
)
EVENT_STATION_LINE = re.compile(
    r"^      Station:  .+CLIGEN VER\. 5\.32 5\.32$"
)
ELEMENT_HEADER_FIELDS = (
    "OFE", "DD", "MM", "YYYY", "Precip", "Runoff", "EffInt", "PeakRO",
    "EffDur", "Enrich", "Keff", "Sm", "LeafArea", "CanHgt", "Cancov",
    "IntCov", "RilCov", "LivBio", "DeadBio", "Ki", "Kr", "Tcrit",
    "RilWid", "SedLeave", "QRain", "QSnow",
)
ELEMENT_UNITS_FIELDS = (
    "na", "na", "na", "na", "mm", "mm", "mm/h", "mm/h", "h", "Ratio",
    "mm/h", "mm", "Index", "m", "%", "%", "%", "Kg/m^2", "Kg/m^2",
    "na", "na", "na", "m", "kg/m", "mm", "mm",
)
GZIP_LEVEL = 9
FIXED_MTIME = 0
CANONICAL_GZIP_HEADER = bytes((0x1F, 0x8B, 8, 0, 0, 0, 0, 0, 2, 255))


class CampaignError(RuntimeError):
    """A fail-closed source, input, execution, parsing, or evidence error."""


@dataclass(frozen=True)
class Artifact:
    sha256: str
    bytes: int


@dataclass(frozen=True)
class BuiltWepp:
    executable: Path
    build_root: Path
    compiler: Path
    compiler_version: str
    linker: Artifact
    linker_version: str
    makefile_sha256: str
    libraries: dict[str, Artifact]
    fixture: dict[str, bytes]


@dataclass(frozen=True)
class ClimateIdentity:
    station_id: str
    profile_id: str
    generation_profile: str
    station_model: str
    horizon: int
    replicate: int
    burn: int
    extension_seed: str | None
    parameter_schema: str
    fit_period: tuple[int, int]
    parameter_sha256: str
    runspec_sha256: str
    cli_sha256: str
    cli_bytes: int
    provenance_sha256: str
    quality_sha256: str
    source_cli: Path | None
    baseline_provenance: dict[str, Any] | None
    baseline_record: dict[str, Any] | None
    candidate_record_raw: bytes | None
    candidate_record: dict[str, Any] | None


@dataclass(frozen=True)
class Job:
    sequence: int
    climate: ClimateIdentity
    domain: str

    @property
    def record_id(self) -> str:
        climate = self.climate
        return (
            f"a5b-wepp-{climate.station_id}-{climate.profile_id}-"
            f"{climate.horizon}yr-rep{climate.replicate}"
        )


@dataclass(frozen=True)
class CalendarAudit:
    source: Artifact
    installed: Artifact
    relabeled_rows: int
    non_year_bytes_identical: bool


@dataclass
class ParsedElement:
    yearly: dict[str, dict[int, float]]
    rows: dict[tuple[int, int, int], dict[str, float]]
    ordinals: set[tuple[int, int, int]]
    has_qrain: bool
    record_count: int
    same_day_duplicate_rows: int
    same_day_duplicate_first_key: tuple[int, int, int] | None
    sm_fixed_width_overflow_count: int
    sm_fixed_width_overflow_first_key: tuple[int, int, int] | None
    peak_fixed_width_recovery_count: int
    peak_fixed_width_recovery_first_key: tuple[int, int, int] | None
    event_hydrology_record_count: int
    event_hydrology_unique_keys: int
    event_hydrology_duplicate_rows: int
    event_peak_crosscheck_count: int


@dataclass
class ParsedEventHydrology:
    peaks: dict[tuple[int, int, int], float]
    peak_thousandths: dict[tuple[int, int, int], int]
    record_count: int
    duplicate_rows: int


@dataclass
class ParsedWinter:
    yearly: dict[str, dict[int, float]]
    rain_on_snow_dates: set[tuple[int, int, int]]
    covered_dates: set[tuple[int, int, int]]


@dataclass(frozen=True)
class RunResult:
    sequence: int
    profile_id: str
    record_id: str
    response_path: Path
    execution_path: Path
    raw_outputs: tuple[tuple[str, Artifact], ...]
    response_artifact: Artifact
    execution_artifact: Artifact
    same_day_duplicate_rows: int
    sm_fixed_width_overflow_count: int
    peak_fixed_width_recovery_count: int


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CampaignError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def reject_constant(token: str) -> None:
    raise CampaignError(f"nonfinite JSON token is forbidden: {token}")


def parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise CampaignError(f"JSON number overflows binary64: {token}")
    return value


def strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_constant,
            parse_float=parse_finite_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CampaignError(f"{label}: invalid strict JSON: {error}") from error


def strict_json(path: Path) -> Any:
    try:
        return strict_json_bytes(path.read_bytes(), str(path))
    except OSError as error:
        raise CampaignError(f"cannot read {path}: {error}") from error


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CampaignError(f"cannot canonicalize JSON: {error}") from error


def compact_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_path(path: Path) -> Artifact:
    return Artifact(sha256_path(path), path.stat().st_size)


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CampaignError(f"{label} must be an object")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CampaignError(f"{label} must be an array")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CampaignError(f"{label} must be a nonempty string")
    return value


def require_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CampaignError(f"{label} must be an integer")
    return value


def require_sha256(value: Any, label: str) -> str:
    text = require_string(value, label)
    if re.fullmatch(r"[0-9a-f]{64}", text) is None:
        raise CampaignError(f"{label} is not a lowercase SHA-256")
    return text


def assert_artifact(path: Path, expected_sha256: str, expected_bytes: int | None, label: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise CampaignError(f"{label} is missing, not regular, or a symlink: {path}")
    actual_bytes = path.stat().st_size
    if expected_bytes is not None and actual_bytes != expected_bytes:
        raise CampaignError(f"{label} byte count differs: {actual_bytes} != {expected_bytes}")
    actual_sha256 = sha256_path(path)
    if actual_sha256 != expected_sha256:
        raise CampaignError(f"{label} SHA-256 differs: {actual_sha256} != {expected_sha256}")


def run_checked(
    command: list[str], *, cwd: Path | None = None, stdin: BinaryIO | None = None,
    stdout: BinaryIO | int | None = subprocess.PIPE,
    stderr: BinaryIO | int | None = subprocess.PIPE,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command, cwd=cwd, stdin=stdin, stdout=stdout, stderr=stderr, env=env, check=False
    )
    if result.returncode != 0:
        out = result.stdout.decode("utf-8", "replace")[-4000:] if isinstance(result.stdout, bytes) else ""
        err = result.stderr.decode("utf-8", "replace")[-4000:] if isinstance(result.stderr, bytes) else ""
        raise CampaignError(
            f"command failed ({result.returncode}): {command!r}\nstdout tail:\n{out}\nstderr tail:\n{err}"
        )
    return result


def verify_normative_hashes() -> None:
    expected = (
        (RESPONSE_SCHEMA, SCHEMA_SHA256, "WEPP response schema"),
        (RESPONSE_PROTOCOL, PROTOCOL_SHA256, "WEPP response protocol"),
        (RESPONSE_VERIFIER, VALIDATOR_SHA256, "WEPP semantic validator"),
    )
    for path, digest, label in expected:
        assert_artifact(path, digest, None, label)


def safe_extract_git_archive(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, mode="r:") as archive:
        members = archive.getmembers()
        for member in members:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or not member.isfile():
                if member.isdir() and not name.is_absolute() and ".." not in name.parts:
                    continue
                raise CampaignError(f"unsafe/nonregular Git archive member: {member.name!r}")
        archive.extractall(destination, filter="data")


def parse_otool_libraries(executable: Path) -> dict[str, Path]:
    result = run_checked(["otool", "-L", str(executable)])
    libraries: dict[str, Path] = {}
    for line in result.stdout.decode("utf-8", "strict").splitlines()[1:]:
        lexical = line.strip().split(" (", 1)[0]
        basename = Path(lexical).name
        if basename in ("libgfortran.5.dylib", "libquadmath.0.dylib"):
            path = Path(lexical).resolve(strict=True)
            libraries[basename] = path
    if set(libraries) != {"libgfortran.5.dylib", "libquadmath.0.dylib"}:
        raise CampaignError(f"pinned WEPP runtime libraries are incomplete: {libraries}")
    return libraries


def build_wepp(wepp_repo: Path, build_parent: Path) -> BuiltWepp:
    """Build the exact pinned arm64 executable from a fresh Git archive.

    The executable pin was derived with the commit's Apple-arm64 makefile.
    The generic ``src/makefile`` selects ``-mcmodel=medium``, which GNU
    Fortran 15 rejects on Apple arm64 and cannot produce the frozen Mach-O.
    The arm64 makefile plus the frozen override, explicit omitted observe
    object, and lexical object linkage is therefore the only recipe admitted
    here; the final size/hash remains the controlling fail-closed authority.
    """

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise CampaignError("pinned WEPP build requires macOS arm64")
    repo = wepp_repo.resolve(strict=True)
    if not (repo / ".git").exists():
        raise CampaignError(f"WEPP source is not a Git worktree: {repo}")
    run_checked(["git", "-C", str(repo), "cat-file", "-e", f"{SOURCE_COMMIT}^{{commit}}"])

    compiler_text = run_checked(["gfortran", "--version"]).stdout.decode("utf-8", "strict")
    compiler_version = compiler_text.splitlines()[0]
    if compiler_version != GFORTRAN_VERSION:
        raise CampaignError(
            f"gfortran identity differs: {compiler_version!r} != {GFORTRAN_VERSION!r}"
        )
    compiler = Path(shutil.which("gfortran") or "").resolve(strict=True)

    build_parent.mkdir(parents=True, exist_ok=True)
    build_root = build_parent / "wepp-source"
    build_root.mkdir()
    archive_path = build_parent / "wepp-source.tar"
    run_checked(
        [
            "git", "-C", str(repo), "archive", "--format=tar",
            f"--output={archive_path}", SOURCE_COMMIT, "src",
            f"{FIXTURE_PREFIX}",
        ]
    )
    safe_extract_git_archive(archive_path, build_root)
    archive_path.unlink()
    source = build_root / "src"
    makefile = source / "makefile.arm64.mac"
    if not makefile.is_file():
        raise CampaignError("pinned commit lacks src/makefile.arm64.mac")

    make_result = subprocess.run(
        [
            "make",
            "-f",
            makefile.name,
            f"FC={compiler}",
            f"LINKER={compiler}",
            f"FFLAGS={' '.join(COMPILE_FLAGS)}",
            "wepp",
        ],
        cwd=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    # That makefile intentionally omits wepp_observe.o.  Its final link must
    # fail for that symbol after all listed objects compile; any earlier or
    # different failure is inadmissible.
    make_log = make_result.stdout + make_result.stderr
    if make_result.returncode == 0 or b"wepp_observe" not in make_log:
        raise CampaignError(
            "arm64 make phase did not end only at the documented omitted "
            f"wepp_observe link seam (rc={make_result.returncode})"
        )
    run_checked([str(compiler), *COMPILE_FLAGS, "wepp_observe.for"], cwd=source)
    objects = sorted(source.glob("*.o"), key=lambda path: path.name)
    if len(objects) < 150 or not (source / "wepp_observe.o").is_file():
        raise CampaignError(f"unexpected WEPP object closure ({len(objects)} objects)")
    executable = source / "wepp"
    if executable.exists():
        executable.unlink()
    assert_artifact(SYSTEM_LINKER, SYSTEM_LINKER_SHA256, None, "pinned system linker")
    linker_result = run_checked([str(SYSTEM_LINKER), "-v"])
    linker_text = (linker_result.stdout + linker_result.stderr).decode("utf-8", "strict")
    linker_version = linker_text.splitlines()[0]
    if linker_version != SYSTEM_LINKER_VERSION:
        raise CampaignError(
            f"system linker identity differs: {linker_version!r} != {SYSTEM_LINKER_VERSION!r}"
        )
    # GCC collect2 searches PATH for ``ld``.  Conda may prepend its historical
    # ld64-530, which links the exact same object set into different bytes.
    # The frozen artifact was linked with Apple's /usr/bin/ld-1266.8.  Pin its
    # content above and make selection unambiguous with a minimal system PATH.
    link_environment = os.environ.copy()
    link_environment["PATH"] = LINK_PATH
    run_checked(
        [str(compiler), *[path.name for path in objects], "-o", "wepp"],
        cwd=source,
        env=link_environment,
    )
    assert_artifact(executable, WEPP_SHA256, WEPP_BYTES, "source-built WEPP")

    library_paths = parse_otool_libraries(executable)
    expected_libraries = {
        "libgfortran.5.dylib": LIBGFORTRAN_SHA256,
        "libquadmath.0.dylib": LIBQUADMATH_SHA256,
    }
    libraries: dict[str, Artifact] = {}
    for name, digest in expected_libraries.items():
        path = library_paths[name]
        assert_artifact(path, digest, None, name)
        libraries[name] = artifact_path(path)

    fixture: dict[str, bytes] = {}
    fixture_root = build_root / FIXTURE_PREFIX
    for name, digest in FIXTURE_HASHES.items():
        path = fixture_root / name
        assert_artifact(path, digest, None, f"reviewed fixture {name}")
        fixture[name] = path.read_bytes()

    return BuiltWepp(
        executable=executable,
        build_root=build_root,
        compiler=compiler,
        compiler_version=compiler_version,
        linker=artifact_path(SYSTEM_LINKER),
        linker_version=linker_version,
        makefile_sha256=sha256_path(makefile),
        libraries=libraries,
        fixture=fixture,
    )


def derive_management(source: bytes) -> bytes:
    try:
        lines = source.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError as error:
        raise CampaignError("reviewed management is not UTF-8") from error
    if len(lines) != 106 or lines[2] != "6 # sim_years\n":
        raise CampaignError("reviewed management prologue differs from p326 revision 1")
    if lines[90] != "1 # number of times the rotation is repeated (nrots)\n":
        raise CampaignError("reviewed management rotation marker differs")
    if lines[91] != "6 # number of years in a single rotation\n":
        raise CampaignError("reviewed management rotation length differs")
    if lines[92] != "   1 \t# plants/year; <Year: 1 - OFE: 1>  (nycrop)\n":
        raise CampaignError("reviewed management sole annual entry differs")
    if lines[93] != "      1 \t# yearly index <Year 1>\n":
        raise CampaignError("reviewed management yearly index differs")
    for year in range(1, 7):
        index = 92 + (year - 1) * 2
        expected = f"   1 \t# plants/year; <Year: {year} - OFE: 1>  (nycrop)\n"
        if lines[index] != expected or lines[index + 1] != lines[93]:
            raise CampaignError(f"reviewed management year {year} differs")
    output = lines[:92]
    output[2] = "100 # sim_years\n"
    output[91] = "100 # number of years in a single rotation\n"
    for year in range(1, 101):
        output.append(f"   1 \t# plants/year; <Year: {year} - OFE: 1>  (nycrop)\n")
        output.append(lines[93])
    output.extend(lines[104:])
    raw = "".join(output).encode("utf-8")
    if sha256_bytes(raw) != MANAGEMENT_SHA256:
        raise CampaignError("derived 100-year management hash differs from frozen contract")
    return raw


def run_file(horizon: int, domain: str) -> bytes:
    if horizon not in HORIZONS or domain not in ("general", "cold_snow"):
        raise CampaignError(f"invalid run adapter request: {horizon}/{domain}")
    lines = [
        "m", "Yes", "1", "1", "No", "3", "No", "../output/a5b.loss.dat",
        "No", "No", "No", "No", "No", "No", "Yes",
        "../output/a5b.element.dat", "No",
    ]
    if domain == "cold_snow":
        lines.extend(("Yes", "../output/a5b.winter.dat"))
    else:
        lines.append("No")
    lines.extend((
        "No", "a5b.man", "a5b.slp", "a5b.cli", "a5b.sol", "0",
        str(horizon), "0",
    ))
    raw = ("\n".join(lines) + "\n").encode("ascii")
    expected = RUN_HASHES.get((horizon, domain))
    if expected is not None and sha256_bytes(raw) != expected:
        raise CampaignError(f"run adapter hash differs for {horizon}/{domain}")
    return raw


CLI_ROW = re.compile(rb"^(\s*\d{1,2}\s+\d{1,2}\s+)(\d{1,3})(\s+.*(?:\n|\r\n)?)$")
CLI_TERMINATOR = b"  \n"


def is_gregorian_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def month_days(year: int, month: int) -> int:
    days = (31, 28 + int(is_gregorian_leap(year)), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not 1 <= month <= 12:
        raise CampaignError(f"month outside 1..12: {month}")
    return days[month - 1]


def ordinal_day(year: int, month: int, day: int) -> int:
    if not 1 <= day <= month_days(year, month):
        raise CampaignError(f"invalid Gregorian date: {year}-{month}-{day}")
    return sum(month_days(year, value) for value in range(1, month)) + day


def wepp_ordinal_day(simulation_year: int, month: int, day: int) -> int:
    days = (31, 28 + int(simulation_year % 4 == 0), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not 1 <= month <= 12 or not 1 <= day <= days[month - 1]:
        raise CampaignError(
            f"invalid WEPP internal date: simulation year {simulation_year}, {month}-{day}"
        )
    return sum(days[: month - 1]) + day


def install_climate(source: Path, destination: Path, horizon: int) -> CalendarAudit:
    raw = source.read_bytes()
    lines = raw.splitlines(keepends=True)
    if len(lines) < 17 or b" da mo year  prcp" not in lines[13]:
        raise CampaignError(f"{source}: CLIGEN header/data seam differs")
    if lines[-1] != CLI_TERMINATOR:
        raise CampaignError(f"{source}: canonical CLIGEN run-end terminator is absent")
    rows = 0
    relabeled = 0
    seen: set[tuple[int, int, int]] = set()
    output = list(lines[:15])
    for line_number, line in enumerate(lines[15:-1], 16):
        match = CLI_ROW.fullmatch(line)
        if match is None:
            raise CampaignError(f"{source}:{line_number}: unexpected CLIGEN daily row")
        tokens = line.split()
        if len(tokens) != 13:
            raise CampaignError(f"{source}:{line_number}: expected 13 CLI fields")
        try:
            day, month, year = map(int, tokens[:3])
            numeric = [float(token) for token in tokens[3:]]
        except ValueError as error:
            raise CampaignError(f"{source}:{line_number}: invalid CLI field") from error
        if not all(math.isfinite(value) for value in numeric):
            raise CampaignError(f"{source}:{line_number}: nonfinite CLI field")
        ordinal_day(year, month, day)
        key = (year, month, day)
        if key in seen:
            raise CampaignError(f"{source}:{line_number}: duplicate CLI date {key}")
        seen.add(key)
        if not 1 <= year <= horizon:
            raise CampaignError(f"{source}:{line_number}: year outside horizon")
        if horizon == 100 and year == 100:
            replacement = b"101"
            if len(match.group(2)) != len(replacement):
                raise CampaignError("year-field width changed during calendar adaptation")
            adapted = match.group(1) + replacement + match.group(3)
            if adapted.replace(replacement, match.group(2), 1) != line:
                raise CampaignError("calendar adapter changed non-year bytes")
            output.append(adapted)
            relabeled += 1
        else:
            output.append(line)
        rows += 1
    output.append(CLI_TERMINATOR)
    expected_rows = sum(366 if is_gregorian_leap(year) else 365 for year in range(1, horizon + 1))
    if rows != expected_rows or len(seen) != expected_rows:
        raise CampaignError(f"{source}: expected {expected_rows} complete rows, got {rows}")
    expected_relabels = 365 if horizon == 100 else 0
    if relabeled != expected_relabels:
        raise CampaignError(f"{source}: expected {expected_relabels} relabels, got {relabeled}")
    installed = b"".join(output)
    if horizon == 30 and installed != raw:
        raise CampaignError("30-year climate adapter changed bytes")
    destination.write_bytes(installed)
    return CalendarAudit(
        source=Artifact(sha256_bytes(raw), len(raw)),
        installed=Artifact(sha256_bytes(installed), len(installed)),
        relabeled_rows=relabeled,
        non_year_bytes_identical=True,
    )


def map_output_year(label: int, horizon: int) -> int:
    if horizon == 100 and label == 101:
        return 100
    if 1 <= label <= horizon and not (horizon == 100 and label == 100):
        return label
    raise CampaignError(f"unexpected WEPP output year label {label} for {horizon}-year run")


def finite_float(token: str, label: str) -> float:
    try:
        value = float(token)
    except ValueError as error:
        raise CampaignError(f"{label}: invalid floating field {token!r}") from error
    if not math.isfinite(value):
        raise CampaignError(f"{label}: nonfinite floating field")
    return value


EVENT_OFE_LINE = re.compile(r"^\s*Overland flow element number:\s+(\d+)\s*$")
EVENT_VERSION_LINE = re.compile(r"^\s*VERSION\s+2020\.500\s*$")
EVENT_DATE_LINE = re.compile(
    r"^\s*Event date:\s+([a-z]{3})\s+(\d{1,2}), year\s+(\d+)\s*$"
)
EVENT_VALUE_PAIR_LINE = re.compile(
    r"^\s*([a-z/ ]+?)\s+((?:0|[1-9]\d*)\.\d{2})\s+"
    r"([a-z/ ]+?)\s+((?:0|[1-9]\d*)\.\d{2})\s*$"
)
EVENT_MONTHS = {
    name: index
    for index, name in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"),
        1,
    )
}


def parse_event_hydrology(path: Path, horizon: int) -> ParsedEventHydrology:
    """Parse the pinned event hydrology blocks used for PeakRO recovery."""

    lines = path.read_text(encoding="ascii", errors="strict").splitlines()
    if (
        not lines
        or lines[0].strip() != EVENT_HYDROLOGY_HEADER
        or sum(line.strip() == EVENT_HYDROLOGY_HEADER for line in lines) != 1
    ):
        raise CampaignError(f"{path}: event hydrology header differs")
    if len(lines) < len(EVENT_PREAMBLE_TEMPLATE):
        raise CampaignError(f"{path}: event hydrology preamble is truncated")
    for index, expected in enumerate(EVENT_PREAMBLE_TEMPLATE):
        observed = lines[index].rstrip()
        if expected is None:
            if EVENT_STATION_LINE.fullmatch(observed) is None:
                raise CampaignError(f"{path}:{index + 1}: event station line differs")
        elif observed != expected:
            raise CampaignError(f"{path}:{index + 1}: event hydrology preamble differs")
    standalone_versions = [
        line for line in lines if re.match(r"^\s*VERSION\b", line) is not None
    ]
    if (
        len(standalone_versions) != 1
        or EVENT_VERSION_LINE.fullmatch(standalone_versions[0]) is None
    ):
        raise CampaignError(f"{path}: event hydrology WEPP version count differs")
    annual_markers = [
        index
        for index, line in enumerate(lines)
        if line.rstrip() == "     ANNUAL AVERAGE SUMMARIES"
    ]
    if len(annual_markers) != 1:
        raise CampaignError(f"{path}: event hydrology annual-summary boundary differs")
    annual_index = annual_markers[0]
    peaks: dict[tuple[int, int, int], float] = {}
    peak_thousandths: dict[tuple[int, int, int], int] = {}
    record_count = 0
    duplicate_rows = 0
    parsed_phrase_lines: set[int] = set()
    for index, line in enumerate(lines):
        ofe_match = EVENT_OFE_LINE.fullmatch(line)
        if ofe_match is None:
            continue
        if index < len(EVENT_PREAMBLE_TEMPLATE) or index >= annual_index:
            raise CampaignError(f"{path}:{index + 1}: event block is outside its section")
        if index + 8 >= len(lines):
            raise CampaignError(f"{path}:{index + 1}: truncated event hydrology block")
        ofe = int(ofe_match.group(1))
        date_match = EVENT_DATE_LINE.fullmatch(lines[index + 1])
        value_matches = [
            EVENT_VALUE_PAIR_LINE.fullmatch(lines[index + offset])
            for offset in range(3, 7)
        ]
        if (
            ofe != 1
            or date_match is None
            or lines[index + 2].strip()
            or any(match is None for match in value_matches)
            or lines[index + 7].strip()
            or lines[index + 8].strip()
            != "note: amounts = mm, durations = min, rates = mm/hr, length = meters"
        ):
            raise CampaignError(f"{path}:{index + 1}: malformed event hydrology block")
        assert date_match is not None
        month_name, day_token, output_year_token = date_match.groups()
        month = EVENT_MONTHS.get(month_name)
        if month is None:
            raise CampaignError(f"{path}:{index + 2}: invalid event month")
        year = map_output_year(int(output_year_token), horizon)
        ordinal = wepp_ordinal_day(year, month, int(day_token))
        expected_labels = (
            ("precipitation amount", "rainfall amount"),
            ("snow melt amount", "runoff amount"),
            ("rain/melt duration", "effective duration"),
            ("peak runoff rate", "effective length"),
        )
        values: list[tuple[float, float]] = []
        for offset, (match, labels) in enumerate(zip(value_matches, expected_labels), 3):
            assert match is not None
            left_label, left_token, right_label, right_token = match.groups()
            if (left_label.strip(), right_label.strip()) != labels:
                raise CampaignError(
                    f"{path}:{index + offset + 1}: event hydrology labels differ"
                )
            if len(left_token) > 8 or len(right_token) > 8:
                raise CampaignError(
                    f"{path}:{index + offset + 1}: event hydrology F8.2 field over-width"
                )
            left = finite_float(left_token, f"{path}:{index + offset + 1}")
            right = finite_float(right_token, f"{path}:{index + offset + 1}")
            if left < 0.0 or right < 0.0:
                raise CampaignError(
                    f"{path}:{index + offset + 1}: negative event hydrology value"
                )
            values.append((left, right))
        peak = values[3][0]
        peak_milli = int(value_matches[3].group(2).replace(".", "")) * 10
        key = (year, ordinal, ofe)
        record_count += 1
        if key in peaks:
            duplicate_rows += 1
            peaks[key] = max(peaks[key], peak)
            peak_thousandths[key] = max(peak_thousandths[key], peak_milli)
        else:
            peaks[key] = peak
            peak_thousandths[key] = peak_milli
        parsed_phrase_lines.update((index, index + 1, index + 6))
    phrase_checks = (
        "Overland flow element number:",
        "Event date:",
        "peak runoff rate",
    )
    for phrase in phrase_checks:
        occurrences = {
            index for index, line in enumerate(lines) if phrase in line
        }
        if not occurrences.issubset(parsed_phrase_lines):
            first = min(occurrences - parsed_phrase_lines)
            raise CampaignError(f"{path}:{first + 1}: unparsed event hydrology phrase")
    if record_count <= 0 or record_count - len(peaks) != duplicate_rows:
        raise CampaignError(f"{path}: event hydrology record counts do not close")
    first_block = next(
        index for index, line in enumerate(lines) if EVENT_OFE_LINE.fullmatch(line)
    )
    if first_block != len(EVENT_PREAMBLE_TEMPLATE):
        raise CampaignError(f"{path}: first event hydrology block is displaced")
    return ParsedEventHydrology(peaks, peak_thousandths, record_count, duplicate_rows)


def element_sm_token_is_overflow(token: str, label: str) -> bool:
    """Validate, but never parse or impute, the nonresponse ``Sm`` field."""

    if token == ELEMENT_SM_OVERFLOW_TOKEN:
        return True
    if len(token) > 7 or ELEMENT_SM_NUMERIC_TOKEN.fullmatch(token) is None:
        raise CampaignError(
            f"{label}: invalid {ELEMENT_SM_HEADER_FIELD} "
            f"{ELEMENT_SM_FORTRAN_FORMAT} field {token!r}"
        )
    return False


def element_peak_token_is_overflow(token: str, label: str) -> bool:
    """Validate the source F7.3 PeakRO token or identify its exact overflow."""

    if token == ELEMENT_SM_OVERFLOW_TOKEN:
        return True
    if len(token) > 7 or ELEMENT_PEAK_NUMERIC_TOKEN.fullmatch(token) is None:
        raise CampaignError(
            f"{label}: invalid {ELEMENT_PEAK_HEADER_FIELD} "
            f"{ELEMENT_SM_FORTRAN_FORMAT} field {token!r}"
        )
    return False


def element_fixed_width_overflow_audit(
    element: ParsedElement, source_element_sha256: str
) -> dict[str, Any]:
    count = element.sm_fixed_width_overflow_count
    first_key = element.sm_fixed_width_overflow_first_key
    if count < 0 or (count == 0) != (first_key is None):
        raise CampaignError("inconsistent parsed Sm fixed-width overflow state")
    observed: dict[str, Any] = {}
    if first_key is not None:
        year, ordinal, ofe = first_key
        observed = {
            "count": count,
            "first_mapped_key": {
                "simulation_year": year,
                "ordinal_day": ordinal,
                "ofe": ofe,
            },
        }
    return {
        "policy_id": ELEMENT_FIXED_WIDTH_OVERFLOW_POLICY_ID,
        "source_element_sha256": source_element_sha256,
        "allowed": {
            "field": ELEMENT_SM_HEADER_FIELD,
            "numeric_index_after_key": ELEMENT_SM_NUMERIC_INDEX,
            "token": ELEMENT_SM_OVERFLOW_TOKEN,
            "fortran_format": ELEMENT_SM_FORTRAN_FORMAT,
            "response_status": "not_consumed_by_a5b_response",
        },
        "total_element_rows": element.record_count,
        "observed": observed,
    }


def validate_element_fixed_width_overflow_audit(
    value: Any, label: str, expected_source_sha256: str
) -> int:
    audit = require_dict(value, label)
    if set(audit) != {
        "policy_id", "source_element_sha256", "allowed",
        "total_element_rows", "observed",
    }:
        raise CampaignError(f"{label}: fixed-width overflow audit is not closed")
    if audit.get("policy_id") != ELEMENT_FIXED_WIDTH_OVERFLOW_POLICY_ID:
        raise CampaignError(f"{label}: fixed-width overflow policy differs")
    if require_sha256(audit.get("source_element_sha256"), f"{label}.source") != expected_source_sha256:
        raise CampaignError(f"{label}: source element SHA-256 differs")
    expected_allowed = {
        "field": ELEMENT_SM_HEADER_FIELD,
        "numeric_index_after_key": ELEMENT_SM_NUMERIC_INDEX,
        "token": ELEMENT_SM_OVERFLOW_TOKEN,
        "fortran_format": ELEMENT_SM_FORTRAN_FORMAT,
        "response_status": "not_consumed_by_a5b_response",
    }
    if audit.get("allowed") != expected_allowed:
        raise CampaignError(f"{label}: allowed fixed-width overflow surface differs")
    total = require_integer(audit.get("total_element_rows"), f"{label}.total_element_rows")
    if total <= 0:
        raise CampaignError(f"{label}: total element rows must be positive")
    observed = require_dict(audit.get("observed"), f"{label}.observed")
    if not observed:
        return 0
    if set(observed) != {"count", "first_mapped_key"}:
        raise CampaignError(f"{label}: observed fixed-width overflow audit is not closed")
    count = require_integer(observed.get("count"), f"{label}.observed.count")
    if not 1 <= count <= total:
        raise CampaignError(f"{label}: observed fixed-width overflow count is invalid")
    key = require_dict(observed.get("first_mapped_key"), f"{label}.first_mapped_key")
    if set(key) != {"simulation_year", "ordinal_day", "ofe"}:
        raise CampaignError(f"{label}: first mapped key is not closed")
    year = require_integer(key.get("simulation_year"), f"{label}.first_mapped_key.year")
    ordinal = require_integer(key.get("ordinal_day"), f"{label}.first_mapped_key.ordinal")
    ofe = require_integer(key.get("ofe"), f"{label}.first_mapped_key.ofe")
    if year <= 0 or not 1 <= ordinal <= 366 or ofe != 1:
        raise CampaignError(f"{label}: first mapped key is invalid")
    return count


def element_same_day_aggregation_audit(
    element: ParsedElement, source_element_sha256: str
) -> dict[str, Any]:
    duplicate_rows = element.same_day_duplicate_rows
    first_key = element.same_day_duplicate_first_key
    if duplicate_rows < 0 or (duplicate_rows == 0) != (first_key is None):
        raise CampaignError("inconsistent parsed same-day element aggregation state")
    if element.record_count - len(element.rows) != duplicate_rows:
        raise CampaignError("same-day element aggregation counts do not close")
    observed: dict[str, Any] = {}
    if first_key is not None:
        year, ordinal, ofe = first_key
        observed = {
            "duplicate_rows": duplicate_rows,
            "first_mapped_key": {
                "simulation_year": year,
                "ordinal_day": ordinal,
                "ofe": ofe,
            },
        }
    return {
        "policy_id": ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID,
        "source_element_sha256": source_element_sha256,
        "key": ["simulation_year", "ordinal_day", "ofe"],
        "aggregation": {
            "runoff": "sum",
            "peak_runoff": "max",
            "sediment_leave": "sum",
            "qrain": "sum_before_daily_rain_on_snow_join",
        },
        "total_element_rows": element.record_count,
        "unique_date_ofe_keys": len(element.rows),
        "observed": observed,
    }


def validate_element_same_day_aggregation_audit(
    value: Any,
    label: str,
    expected_source_sha256: str,
    expected_rows: int,
    expected_unique_keys: int,
) -> int:
    audit = require_dict(value, label)
    if set(audit) != {
        "policy_id",
        "source_element_sha256",
        "key",
        "aggregation",
        "total_element_rows",
        "unique_date_ofe_keys",
        "observed",
    }:
        raise CampaignError(f"{label}: same-day aggregation audit is not closed")
    if audit.get("policy_id") != ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID:
        raise CampaignError(f"{label}: same-day aggregation policy differs")
    if (
        require_sha256(audit.get("source_element_sha256"), f"{label}.source")
        != expected_source_sha256
    ):
        raise CampaignError(f"{label}: source element SHA-256 differs")
    if audit.get("key") != ["simulation_year", "ordinal_day", "ofe"]:
        raise CampaignError(f"{label}: same-day aggregation key differs")
    expected_aggregation = {
        "runoff": "sum",
        "peak_runoff": "max",
        "sediment_leave": "sum",
        "qrain": "sum_before_daily_rain_on_snow_join",
    }
    if audit.get("aggregation") != expected_aggregation:
        raise CampaignError(f"{label}: same-day aggregation rules differ")
    if (
        audit.get("total_element_rows") != expected_rows
        or audit.get("unique_date_ofe_keys") != expected_unique_keys
        or expected_rows < expected_unique_keys
    ):
        raise CampaignError(f"{label}: same-day aggregation counts differ")
    duplicate_rows = expected_rows - expected_unique_keys
    observed = require_dict(audit.get("observed"), f"{label}.observed")
    if duplicate_rows == 0:
        if observed:
            raise CampaignError(f"{label}: unexpected same-day aggregation observation")
        return 0
    if set(observed) != {"duplicate_rows", "first_mapped_key"}:
        raise CampaignError(f"{label}: same-day aggregation observation is not closed")
    if observed.get("duplicate_rows") != duplicate_rows:
        raise CampaignError(f"{label}: duplicate element-row count differs")
    key = require_dict(observed.get("first_mapped_key"), f"{label}.first_mapped_key")
    if set(key) != {"simulation_year", "ordinal_day", "ofe"}:
        raise CampaignError(f"{label}: first duplicate mapped key is not closed")
    year = require_integer(key.get("simulation_year"), f"{label}.first_mapped_key.year")
    ordinal = require_integer(key.get("ordinal_day"), f"{label}.first_mapped_key.ordinal")
    ofe = require_integer(key.get("ofe"), f"{label}.first_mapped_key.ofe")
    if year <= 0 or not 1 <= ordinal <= 366 or ofe != 1:
        raise CampaignError(f"{label}: first duplicate mapped key is invalid")
    return duplicate_rows


def element_peak_recovery_audit(
    element: ParsedElement,
    source_element_sha256: str,
    source_event_hydrology_sha256: str,
) -> dict[str, Any]:
    count = element.peak_fixed_width_recovery_count
    first_key = element.peak_fixed_width_recovery_first_key
    if count < 0 or (count == 0) != (first_key is None):
        raise CampaignError("inconsistent parsed PeakRO recovery state")
    observed: dict[str, Any] = {}
    if first_key is not None:
        year, ordinal, ofe = first_key
        observed = {
            "count": count,
            "first_mapped_key": {
                "simulation_year": year,
                "ordinal_day": ordinal,
                "ofe": ofe,
            },
        }
    return {
        "policy_id": ELEMENT_PEAK_RECOVERY_POLICY_ID,
        "source_element_sha256": source_element_sha256,
        "source_event_hydrology_sha256": source_event_hydrology_sha256,
        "element_overflow": {
            "field": ELEMENT_PEAK_HEADER_FIELD,
            "numeric_index_after_key": ELEMENT_PEAK_NUMERIC_INDEX,
            "token": ELEMENT_SM_OVERFLOW_TOKEN,
            "fortran_format": ELEMENT_SM_FORTRAN_FORMAT,
            "numeric_lexical": "canonical_space_padded_fortran_without_zero_padding",
        },
        "recovery": {
            "run_output_option": 3,
            "header": EVENT_HYDROLOGY_HEADER,
            "preamble": "pinned_wepp_p326_event_output_55_lines_station_text_only_variable",
            "field": "peak runoff rate",
            "fortran_format": EVENT_HYDROLOGY_PEAK_FORMAT,
            "numeric_lexical": "canonical_space_padded_fortran_without_zero_padding",
            "aggregation": "maximum_by_mapped_simulation_year_ordinal_day_ofe",
            "crosscheck_absolute_tolerance_mm_per_hour": EVENT_PEAK_CROSSCHECK_TOLERANCE,
            "crosscheck_arithmetic": "integer_thousandths",
            "non_hydrology_sections": "hash_bound_not_response_parsed_hydrology_phrases_block_bound",
        },
        "event_hydrology_records": element.event_hydrology_record_count,
        "event_hydrology_unique_keys": element.event_hydrology_unique_keys,
        "event_hydrology_duplicate_rows": element.event_hydrology_duplicate_rows,
        "crosschecked_unique_keys": element.event_peak_crosscheck_count,
        "observed": observed,
    }


def validate_element_peak_recovery_audit(
    value: Any,
    label: str,
    expected_element_sha256: str,
    expected_event_hydrology_sha256: str,
    expected_element_rows: int,
    expected_element_keys: int,
) -> int:
    audit = require_dict(value, label)
    if set(audit) != {
        "policy_id",
        "source_element_sha256",
        "source_event_hydrology_sha256",
        "element_overflow",
        "recovery",
        "event_hydrology_records",
        "event_hydrology_unique_keys",
        "event_hydrology_duplicate_rows",
        "crosschecked_unique_keys",
        "observed",
    }:
        raise CampaignError(f"{label}: PeakRO recovery audit is not closed")
    if audit.get("policy_id") != ELEMENT_PEAK_RECOVERY_POLICY_ID:
        raise CampaignError(f"{label}: PeakRO recovery policy differs")
    if (
        require_sha256(audit.get("source_element_sha256"), f"{label}.element_source")
        != expected_element_sha256
        or require_sha256(
            audit.get("source_event_hydrology_sha256"), f"{label}.event_source"
        )
        != expected_event_hydrology_sha256
    ):
        raise CampaignError(f"{label}: PeakRO recovery source differs")
    expected_overflow = {
        "field": ELEMENT_PEAK_HEADER_FIELD,
        "numeric_index_after_key": ELEMENT_PEAK_NUMERIC_INDEX,
        "token": ELEMENT_SM_OVERFLOW_TOKEN,
        "fortran_format": ELEMENT_SM_FORTRAN_FORMAT,
        "numeric_lexical": "canonical_space_padded_fortran_without_zero_padding",
    }
    expected_recovery = {
        "run_output_option": 3,
        "header": EVENT_HYDROLOGY_HEADER,
        "preamble": "pinned_wepp_p326_event_output_55_lines_station_text_only_variable",
        "field": "peak runoff rate",
        "fortran_format": EVENT_HYDROLOGY_PEAK_FORMAT,
        "numeric_lexical": "canonical_space_padded_fortran_without_zero_padding",
        "aggregation": "maximum_by_mapped_simulation_year_ordinal_day_ofe",
        "crosscheck_absolute_tolerance_mm_per_hour": EVENT_PEAK_CROSSCHECK_TOLERANCE,
        "crosscheck_arithmetic": "integer_thousandths",
        "non_hydrology_sections": "hash_bound_not_response_parsed_hydrology_phrases_block_bound",
    }
    if audit.get("element_overflow") != expected_overflow or audit.get("recovery") != expected_recovery:
        raise CampaignError(f"{label}: PeakRO recovery declaration differs")
    records = require_integer(audit.get("event_hydrology_records"), f"{label}.records")
    keys = require_integer(audit.get("event_hydrology_unique_keys"), f"{label}.keys")
    duplicates = require_integer(
        audit.get("event_hydrology_duplicate_rows"), f"{label}.duplicates"
    )
    crosschecked = require_integer(
        audit.get("crosschecked_unique_keys"), f"{label}.crosschecked"
    )
    if (
        expected_element_rows < 1
        or not 1 <= expected_element_keys <= expected_element_rows
        or records <= 0
        or not 1 <= keys <= min(records, expected_element_keys)
        or duplicates != records - keys
        or crosschecked != keys
    ):
        raise CampaignError(f"{label}: PeakRO recovery counts differ")
    observed = require_dict(audit.get("observed"), f"{label}.observed")
    if not observed:
        return 0
    if set(observed) != {"count", "first_mapped_key"}:
        raise CampaignError(f"{label}: PeakRO recovery observation is not closed")
    count = require_integer(observed.get("count"), f"{label}.observed.count")
    if not 1 <= count <= min(records, expected_element_rows):
        raise CampaignError(f"{label}: PeakRO recovery count is invalid")
    key = require_dict(observed.get("first_mapped_key"), f"{label}.first_mapped_key")
    if set(key) != {"simulation_year", "ordinal_day", "ofe"}:
        raise CampaignError(f"{label}: PeakRO recovery key is not closed")
    year = require_integer(key.get("simulation_year"), f"{label}.first_mapped_key.year")
    ordinal = require_integer(key.get("ordinal_day"), f"{label}.first_mapped_key.ordinal")
    ofe = require_integer(key.get("ofe"), f"{label}.first_mapped_key.ofe")
    if year <= 0 or not 1 <= ordinal <= 366 or ofe != 1:
        raise CampaignError(f"{label}: PeakRO recovery key is invalid")
    return count


def parse_element(
    path: Path, horizon: int, event_hydrology: ParsedEventHydrology
) -> ParsedElement:
    yearly = {
        metric: {year: 0.0 for year in range(1, horizon + 1)}
        for metric in ("annual_runoff", "annual_peak_runoff", "annual_soil_loss", "winter_runoff", "winter_soil_loss")
    }
    rows: dict[tuple[int, int, int], dict[str, float]] = {}
    ordinals: set[tuple[int, int, int]] = set()
    header_seen = False
    units_seen = False
    data_seen = False
    has_qrain = True
    years_seen: set[int] = set()
    record_count = 0
    same_day_duplicate_rows = 0
    same_day_duplicate_first_key: tuple[int, int, int] | None = None
    sm_overflow_count = 0
    sm_overflow_first_key: tuple[int, int, int] | None = None
    peak_recovery_count = 0
    peak_recovery_first_key: tuple[int, int, int] | None = None
    with path.open("r", encoding="ascii", errors="strict", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not header_seen:
                if tuple(line.split()) != ELEMENT_HEADER_FIELDS:
                    raise CampaignError(f"{path}:{line_number}: unexpected element header")
                header_seen = True
                continue
            if not units_seen:
                if tuple(line.split()) != ELEMENT_UNITS_FIELDS:
                    raise CampaignError(f"{path}:{line_number}: unexpected element units row")
                units_seen = True
                continue
            tokens = line.split()
            if not tokens:
                continue
            if tokens[0] == "na":
                raise CampaignError(f"{path}:{line_number}: unexpected post-header na row")
            expected_fields = len(ELEMENT_HEADER_FIELDS)
            if len(tokens) != expected_fields:
                raise CampaignError(
                    f"{path}:{line_number}: expected {expected_fields} element fields, got {len(tokens)}"
                )
            try:
                ofe, day, month, output_year = map(int, tokens[:4])
            except ValueError as error:
                raise CampaignError(f"{path}:{line_number}: invalid element key") from error
            if ofe != 1:
                raise CampaignError(f"{path}:{line_number}: unexpected OFE {ofe}")
            year = map_output_year(output_year, horizon)
            ordinal = wepp_ordinal_day(year, month, day)
            key = (year, ordinal, ofe)
            value_tokens = tokens[4:]
            sm_overflow = element_sm_token_is_overflow(
                value_tokens[ELEMENT_SM_NUMERIC_INDEX], f"{path}:{line_number}"
            )
            peak_overflow = element_peak_token_is_overflow(
                value_tokens[ELEMENT_PEAK_NUMERIC_INDEX], f"{path}:{line_number}"
            )
            values = {
                index: finite_float(token, f"{path}:{line_number}")
                for index, token in enumerate(value_tokens)
                if index != ELEMENT_SM_NUMERIC_INDEX
                and not (index == ELEMENT_PEAK_NUMERIC_INDEX and peak_overflow)
            }
            runoff = values[1]
            if peak_overflow:
                peak = event_hydrology.peaks.get(key, -1.0)
                peak_milli = event_hydrology.peak_thousandths.get(key, -1)
                if peak < 0.0 or peak_milli < 0:
                    raise CampaignError(
                        f"{path}:{line_number}: PeakRO overflow lacks event-hydrology recovery"
                    )
                peak_recovery_count += 1
                if peak_recovery_first_key is None:
                    peak_recovery_first_key = key
            else:
                peak = values[3]
                peak_milli = int(
                    value_tokens[ELEMENT_PEAK_NUMERIC_INDEX].replace(".", "")
                )
            sediment = values[19]
            qrain = values[20] if has_qrain else 0.0
            for name, value in (("Runoff", runoff), ("PeakRO", peak), ("SedLeave", sediment), ("QRain", qrain)):
                if value < 0.0:
                    raise CampaignError(f"{path}:{line_number}: negative {name}")
            row = {
                "runoff": runoff,
                "peak": peak,
                "peak_milli": peak_milli,
                "sediment": sediment,
                "qrain": qrain,
            }
            record_count += 1
            if key in rows:
                same_day_duplicate_rows += 1
                if same_day_duplicate_first_key is None:
                    same_day_duplicate_first_key = key
                aggregate = rows[key]
                aggregate["runoff"] += runoff
                aggregate["peak"] = max(aggregate["peak"], peak)
                aggregate["peak_milli"] = max(
                    aggregate["peak_milli"], peak_milli
                )
                aggregate["sediment"] += sediment
                aggregate["qrain"] += qrain
            else:
                rows[key] = row
            ordinals.add(key)
            years_seen.add(year)
            if sm_overflow:
                sm_overflow_count += 1
                if sm_overflow_first_key is None:
                    sm_overflow_first_key = key
            yearly["annual_runoff"][year] += runoff
            yearly["annual_peak_runoff"][year] = max(yearly["annual_peak_runoff"][year], peak)
            yearly["annual_soil_loss"][year] += sediment
            if month in (12, 1, 2):
                yearly["winter_runoff"][year] += runoff
                yearly["winter_soil_loss"][year] += sediment
            data_seen = True
    if not header_seen or not units_seen or not data_seen:
        raise CampaignError(f"{path}: element header/data is incomplete")
    expected_years = set(range(1, horizon + 1))
    if years_seen != expected_years:
        raise CampaignError(f"{path}: incomplete mapped element years: {sorted(expected_years - years_seen)}")
    for key, event_peak_milli in event_hydrology.peak_thousandths.items():
        element_row = rows.get(key)
        if element_row is None:
            raise CampaignError(f"{path}: event hydrology key is absent from element output: {key}")
        if abs(element_row["peak_milli"] - event_peak_milli) > 6:
            raise CampaignError(f"{path}: event/element PeakRO crosscheck differs for {key}")
    return ParsedElement(
        yearly,
        rows,
        ordinals,
        has_qrain,
        record_count,
        same_day_duplicate_rows,
        same_day_duplicate_first_key,
        sm_overflow_count,
        sm_overflow_first_key,
        peak_recovery_count,
        peak_recovery_first_key,
        event_hydrology.record_count,
        len(event_hydrology.peaks),
        event_hydrology.duplicate_rows,
        len(event_hydrology.peaks),
    )


def parse_winter(path: Path, horizon: int) -> ParsedWinter:
    yearly = {
        "annual_max_snow_water_state": {year: 0.0 for year in range(1, horizon + 1)},
        "annual_snowmelt": {year: 0.0 for year in range(1, horizon + 1)},
    }
    eligible: set[tuple[int, int, int]] = set()
    covered: set[tuple[int, int, int]] = set()
    keys: set[tuple[int, int, int, int]] = set()
    years_seen: set[int] = set()
    header_seen = False
    density_header_seen = False
    data_seen = False
    with path.open("r", encoding="ascii", errors="strict", newline="") as handle:
        for line_number, line in enumerate(handle, 1):
            if not header_seen:
                if line.lstrip().startswith("date hr year"):
                    required = ("rain", "melt", "snow")
                    if any(word not in line.lower() for word in required):
                        raise CampaignError(f"{path}:{line_number}: hourly winter header lacks required fields")
                    header_seen = True
                    density_header_seen = "density" in line.lower()
                continue
            tokens = line.split()
            if not tokens:
                continue
            if tokens[0].startswith("(") or tokens[0] in ("fall", "(mm)"):
                density_header_seen = density_header_seen or "density" in line.lower()
                continue
            if len(tokens) != 16:
                # The two wrapped header/unit lines follow the marker.
                if not data_seen and any(ch.isalpha() for ch in line):
                    density_header_seen = density_header_seen or "density" in line.lower()
                    continue
                raise CampaignError(f"{path}:{line_number}: expected 16 hourly fields, got {len(tokens)}")
            try:
                day_of_year, hour, output_year = map(int, tokens[:3])
                cycle, ofe = map(int, tokens[14:])
            except ValueError as error:
                raise CampaignError(f"{path}:{line_number}: invalid hourly key") from error
            _ = cycle
            if not density_header_seen:
                raise CampaignError(f"{path}:{line_number}: wrapped winter header lacks density")
            year = map_output_year(output_year, horizon)
            if ofe != 1 or not 1 <= hour <= 24:
                raise CampaignError(f"{path}:{line_number}: invalid hourly OFE/hour")
            # This is WEPP's internal ordinal clock, which treats every fourth
            # simulation year as leap.  The climate adapter prevents a civil
            # year-100 input row mismatch by relabeling its 365 rows to 101,
            # but hourly state output still exposes internal simulation-year
            # 100 with ordinal day 366; retain that state and map it to year 100.
            max_day = 366 if year % 4 == 0 else 365
            if not 1 <= day_of_year <= max_day:
                raise CampaignError(f"{path}:{line_number}: invalid ordinal day {day_of_year}")
            key = (year, day_of_year, hour, ofe)
            if key in keys:
                raise CampaignError(f"{path}:{line_number}: duplicate hourly record {key}")
            keys.add(key)
            values = [finite_float(token, f"{path}:{line_number}") for token in tokens[3:14]]
            snow_fall, rain_fall, ground_drift, falling_drift, melt_water = values[:5]
            snow_depth, snow_density = values[5:7]
            _ = snow_fall, ground_drift, falling_drift
            for name, value in (
                ("rain_fall", rain_fall), ("melt_water", melt_water),
                ("snow_depth", snow_depth), ("snow_density", snow_density),
            ):
                if value < 0.0:
                    raise CampaignError(f"{path}:{line_number}: negative {name}")
            state = snow_depth * snow_density / 1000.0
            yearly["annual_max_snow_water_state"][year] = max(
                yearly["annual_max_snow_water_state"][year], state
            )
            yearly["annual_snowmelt"][year] += melt_water
            date_key = (year, day_of_year, ofe)
            covered.add(date_key)
            if rain_fall > 0.0 and snow_depth > 0.0 and snow_density > 0.0:
                eligible.add(date_key)
            years_seen.add(year)
            data_seen = True
    if not header_seen or not data_seen:
        raise CampaignError(f"{path}: hourly winter header/data is incomplete")
    expected_years = set(range(1, horizon + 1))
    if years_seen != expected_years:
        raise CampaignError(f"{path}: incomplete mapped winter years: {sorted(expected_years - years_seen)}")
    return ParsedWinter(yearly, eligible, covered)


def join_rain_on_snow(element: ParsedElement, winter: ParsedWinter, horizon: int) -> dict[int, float] | None:
    if not element.has_qrain:
        return None
    result = {year: 0.0 for year in range(1, horizon + 1)}
    # QRain is a daily element-output field, not an hourly field.  The hourly
    # file supplies only the eligibility state.  Same-day element event rows
    # have already been reduced to one date/OFE value by summing QRain.  That
    # aggregate is joined once when any matching hourly row reports rain and a
    # positive snowpack.  Element dates outside the winter trace cannot be
    # eligible and contribute nothing; no hourly QRain is invented.
    for key, row in element.rows.items():
        if key in winter.rain_on_snow_dates:
            result[key[0]] += row["qrain"]
    return result


def summaries(values: dict[int, float], horizon: int) -> dict[str, float]:
    if sorted(values) != list(range(1, horizon + 1)):
        raise CampaignError("response summary does not cover every mapped year")
    ordered = [values[year] for year in range(1, horizon + 1)]
    if any(not math.isfinite(value) or value < 0.0 for value in ordered):
        raise CampaignError("response summary contains a nonfinite/negative year")
    sorted_values = sorted(ordered)
    p95_index = max(0, math.ceil(0.95 * horizon) - 1)
    return {
        "mean": math.fsum(ordered) / horizon,
        "sd": statistics.stdev(ordered),
        "p95": sorted_values[p95_index],
        "max": sorted_values[-1],
    }


METRIC_UNITS = {
    "annual_runoff": "mm",
    "annual_peak_runoff": "mm_per_hour",
    "annual_soil_loss": "kg_per_m",
    "annual_max_snow_water_state": "mm_water_equivalent",
    "annual_snowmelt": "mm",
    "rain_on_snow_runoff": "mm",
    "winter_runoff": "mm",
    "winter_soil_loss": "kg_per_m",
}


def artifact_json(artifact: Artifact) -> dict[str, Any]:
    return {"sha256": artifact.sha256, "bytes": artifact.bytes}


def response_source(metric: str, output_sha256: str, winter_sha256: str | None) -> dict[str, str]:
    if metric == "annual_runoff":
        return {
            "output_sha256": output_sha256,
            "selector": "element output Runoff grouped by mapped simulation year",
            "record_meaning": "annual runoff depth from explicit element-output records",
            "aggregation": "sum Runoff across the complete mapped simulation year and OFE 1",
            "missing_value_rule": (
                "reduce same-day element-event rows under "
                f"{ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID}; reject nonfinite, negative, "
                "malformed, or incomplete-year output"
            ),
        }
    if metric == "annual_peak_runoff":
        return {
            "output_sha256": output_sha256,
            "selector": (
                "element output PeakRO grouped by mapped simulation year; exact F7.3 "
                "overflow tokens recovered from the hash-bound event-by-event hydrology "
                f"companion under {ELEMENT_PEAK_RECOVERY_POLICY_ID}"
            ),
            "record_meaning": "annual maximum element-output peak runoff rate",
            "aggregation": (
                "maximum PeakRO across the complete mapped simulation year and OFE 1; "
                "same-day and companion event records reduced by maximum"
            ),
            "missing_value_rule": (
                "reduce same-day element-event rows under "
                f"{ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID}; recover only exact PeakRO "
                f"F7.3 overflow under {ELEMENT_PEAK_RECOVERY_POLICY_ID}; reject nonfinite, "
                "negative, malformed, unbound, or incomplete-year output"
            ),
        }
    if metric == "annual_soil_loss":
        return {
            "output_sha256": output_sha256,
            "selector": "element output SedLeave grouped by mapped simulation year",
            "record_meaning": "annual soil loss leaving the reviewed one-OFE hillslope",
            "aggregation": "sum SedLeave across the complete mapped simulation year and OFE 1",
            "missing_value_rule": (
                "reduce same-day element-event rows under "
                f"{ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID}; reject nonfinite, negative, "
                "malformed, or incomplete-year output"
            ),
        }
    if metric == "winter_runoff":
        return {
            "output_sha256": output_sha256,
            "selector": "element output Runoff where calendar month is December, January, or February",
            "record_meaning": "DJF runoff depth assigned to each mapped simulation year",
            "aggregation": "sum explicit DJF Runoff records in mapped year and OFE 1",
            "missing_value_rule": (
                "reduce same-day element-event rows under "
                f"{ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID}; reject nonfinite, negative, "
                "malformed, or incomplete-year output"
            ),
        }
    if metric == "winter_soil_loss":
        return {
            "output_sha256": output_sha256,
            "selector": "element output SedLeave where calendar month is December, January, or February",
            "record_meaning": "DJF soil loss assigned to each mapped simulation year",
            "aggregation": "sum explicit DJF SedLeave records in mapped year and OFE 1",
            "missing_value_rule": (
                "reduce same-day element-event rows under "
                f"{ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID}; reject nonfinite, negative, "
                "malformed, or incomplete-year output"
            ),
        }
    if winter_sha256 is None:
        raise CampaignError(f"{metric}: hourly winter output identity is absent")
    if metric == "annual_max_snow_water_state":
        return {
            "output_sha256": winter_sha256,
            "selector": "hourly winter snow_depth * snow_density / 1000 grouped by mapped year",
            "record_meaning": "pinned-WEPP snow-water-state analogue, not an observed SWE estimate",
            "aggregation": "maximum hourly state in each complete mapped simulation year and OFE 1",
            "missing_value_rule": "reject duplicate, nonfinite, negative, malformed, or incomplete-year output",
        }
    if metric == "annual_snowmelt":
        return {
            "output_sha256": winter_sha256,
            "selector": "hourly winter melt_water grouped by mapped simulation year",
            "record_meaning": "annual sum of explicit hourly melt-water records",
            "aggregation": "sum melt_water across each complete mapped simulation year and OFE 1",
            "missing_value_rule": "reject duplicate, nonfinite, negative, malformed, or incomplete-year output",
        }
    if metric == "rain_on_snow_runoff":
        return {
            # The schema admits one output hash.  Bind the quantity-bearing
            # element file here and bind the eligibility file in the selector;
            # both raw artifacts are independently declared in outputs[].
            "output_sha256": output_sha256,
            "selector": (
                "element QRain joined by mapped (year, ordinal day, OFE) to hourly winter "
                f"SHA-256 {winter_sha256}; eligible when any hour has rain_fall>0, "
                "snow_depth>0, and snow_density>0"
            ),
            "record_meaning": "rain-on-snow response analogue; no hourly QRain or causal partition is inferred",
            "aggregation": (
                "sum each eligible daily/OFE QRain aggregate once per mapped year under "
                f"{ELEMENT_SAME_DAY_AGGREGATION_POLICY_ID}"
            ),
            "missing_value_rule": (
                "unavailable if element QRain is absent; reduce same-day element-event "
                "rows under the versioned policy and reject malformed join keys"
            ),
        }
    raise CampaignError(f"unknown response metric: {metric}")


def available_family(
    metric: str,
    values: dict[int, float],
    horizon: int,
    element_sha256: str,
    winter_sha256: str | None,
) -> list[dict[str, Any]]:
    summary = summaries(values, horizon)
    source = response_source(metric, element_sha256, winter_sha256)
    return [
        {
            "status": "available",
            "metric_id": metric,
            "statistic": statistic,
            "value": summary[statistic],
            "units": METRIC_UNITS[metric],
            "n_years": horizon,
            "source": source,
        }
        for statistic in STATISTICS
    ]


def unavailable_family(metric: str, reason: str, audit: str) -> dict[str, str]:
    return {
        "status": "unavailable",
        "metric_id": metric,
        "reason": reason,
        "source_audit": audit,
    }


def response_validator() -> tuple[Draft202012Validator, Any]:
    schema = require_dict(strict_json(RESPONSE_SCHEMA), "WEPP response schema")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    module_spec = importlib.util.spec_from_file_location("a5_wepp_semantic_v1", RESPONSE_VERIFIER)
    if module_spec is None or module_spec.loader is None:
        raise CampaignError("cannot load pinned WEPP semantic validator")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return validator, module


def validate_response(validator: Draft202012Validator, semantic: Any, value: dict[str, Any]) -> None:
    try:
        semantic.validate_contract(validator, value)
    except Exception as error:
        raise CampaignError(f"WEPP response validation failed: {error}") from error


def climate_json(climate: ClimateIdentity) -> dict[str, Any]:
    return {
        "station_id": climate.station_id,
        "generation_profile": climate.generation_profile,
        "forcing_label": "synthetic",
        "horizon_years": climate.horizon,
        "replicate": {
            "key": f"replicate-{climate.replicate}",
            "legacy_burn_offset": climate.burn,
            "extension_seed_u64_hex": climate.extension_seed,
        },
        "parameter_fit": {
            "schema_id": climate.parameter_schema,
            "model_id": climate.station_model,
            "fit_period": list(climate.fit_period),
            "content_sha256": climate.parameter_sha256,
        },
        "runspec_sha256": climate.runspec_sha256,
        "cli_sha256": climate.cli_sha256,
        "provenance_sha256": climate.provenance_sha256,
        "quality_report_sha256": climate.quality_sha256,
        "quality_report_schema_version": 2,
        "metrics_version": 3,
    }


def compose_response(
    job: Job,
    built: BuiltWepp,
    runner_sha256: str,
    calendar: CalendarAudit,
    input_artifacts: dict[str, Artifact],
    output_artifacts: dict[str, Artifact],
    element: ParsedElement,
    winter: ParsedWinter | None,
) -> dict[str, Any]:
    expected_input_roles = {"run", "management", "soil", "slope"}
    if set(input_artifacts) != expected_input_roles:
        raise CampaignError(f"{job.record_id}: execution input-artifact roles differ")
    element_artifact = output_artifacts["element"]
    winter_artifact = output_artifacts.get("hourly_winter")
    responses: list[dict[str, Any]] = []
    for metric in GENERAL_METRICS:
        responses.extend(
            available_family(metric, element.yearly[metric], job.climate.horizon, element_artifact.sha256, None)
        )
    if job.domain == "cold_snow":
        if winter is None or winter_artifact is None:
            for metric in COLD_METRICS:
                responses.append(
                    unavailable_family(
                        metric,
                        "pinned hourly winter output was not available",
                        "run adapter and requested output set were inspected; no substitute value was emitted",
                    )
                )
        else:
            for metric in ("annual_max_snow_water_state", "annual_snowmelt"):
                responses.extend(
                    available_family(
                        metric,
                        winter.yearly[metric],
                        job.climate.horizon,
                        element_artifact.sha256,
                        winter_artifact.sha256,
                    )
                )
            rain_on_snow = join_rain_on_snow(element, winter, job.climate.horizon)
            if rain_on_snow is None:
                responses.append(
                    unavailable_family(
                        "rain_on_snow_runoff",
                        "pinned element output lacks the explicit QRain field",
                        (
                            "the complete element header and hourly winter surface were inspected; "
                            "hourly winter output does not contain QRain and no value was inferred"
                        ),
                    )
                )
            else:
                responses.extend(
                    available_family(
                        "rain_on_snow_runoff",
                        rain_on_snow,
                        job.climate.horizon,
                        element_artifact.sha256,
                        winter_artifact.sha256,
                    )
                )
            for metric in ("winter_runoff", "winter_soil_loss"):
                responses.extend(
                    available_family(
                        metric,
                        element.yearly[metric],
                        job.climate.horizon,
                        element_artifact.sha256,
                        winter_artifact.sha256,
                    )
                )

    outputs = [
        {"role": role, "content": artifact_json(output_artifacts[role])}
        for role in ("element", "soil_loss", "hourly_winter")
        if role in output_artifacts
    ]
    if len({row["content"]["sha256"] for row in outputs}) != len(outputs):
        raise CampaignError(f"{job.record_id}: WEPP output hashes are not unique")
    return {
        "wepp_response_schema_version": 1,
        "validation_contract": {
            "schema_id": "cligen-a5-wepp-response-v1",
            "schema_sha256": SCHEMA_SHA256,
            "protocol_id": "cligen-a5-wepp-response-protocol-v1",
            "protocol_sha256": PROTOCOL_SHA256,
            "semantic_validator_id": "cligen-a5-wepp-response-semantic-v1",
            "semantic_validator_sha256": VALIDATOR_SHA256,
        },
        "record_id": job.record_id,
        "domain": job.domain,
        "climate": climate_json(job.climate),
        "wepp_execution": {
            "executable": {"sha256": WEPP_SHA256, "bytes": WEPP_BYTES},
            "version_output": WEPP_VERSION_OUTPUT,
            "platform": f"macOS arm64; {built.compiler_version}",
            "invocation": ["wepp", "<", "a5b.run"],
            "inputs": [
                {"role": role, "content": artifact_json(input_artifacts[role])}
                for role in ("run", "management", "soil", "slope")
            ],
            "climate_installation": {
                "method_id": CLIMATE_ADAPTER_ID,
                "description": (
                    f"source {calendar.source.sha256}/{calendar.source.bytes} bytes installed as "
                    f"{calendar.installed.sha256}/{calendar.installed.bytes} bytes; "
                    f"relabeled {calendar.relabeled_rows} year-100 daily rows to 101; "
                    "all non-year bytes proved identical"
                ),
            },
            "extraction_adapter": {
                "adapter_id": EXTRACTION_ADAPTER_ID,
                "content_sha256": runner_sha256,
            },
        },
        "outputs": outputs,
        "responses": responses,
    }


def compose_execution_record(
    job: Job,
    exit_code: int,
    success_banner_count: int,
    calendar: CalendarAudit,
    input_artifacts: dict[str, Artifact],
    raw_identities: list[tuple[str, Artifact]],
    runner_sha256: str,
    element: ParsedElement,
    winter: ParsedWinter | None,
    output_artifacts: dict[str, Artifact],
) -> dict[str, Any]:
    expected_input_roles = {"run", "management", "soil", "slope"}
    if set(input_artifacts) != expected_input_roles:
        raise CampaignError(f"{job.record_id}: execution input-artifact roles differ")
    element_artifact = output_artifacts["element"]
    return {
        "wepp_execution_record_version": 1,
        "record_id": job.record_id,
        "sequence": job.sequence,
        "process": {
            "exit_code": exit_code,
            "success_banner_count": success_banner_count,
            "warning_tokens": 0,
        },
        "calendar_adapter": {
            "adapter_id": CLIMATE_ADAPTER_ID,
            "source": artifact_json(calendar.source),
            "installed": artifact_json(calendar.installed),
            "relabeled_rows": calendar.relabeled_rows,
            "non_year_bytes_identical": calendar.non_year_bytes_identical,
        },
        "input_artifacts": {
            role: artifact_json(artifact)
            for role, artifact in sorted(input_artifacts.items())
        },
        "raw_output_audit": [
            {
                "role": role,
                "content": artifact_json(raw_artifact),
                "retained": False,
                "source_audit": (
                    "hashed after successful execution and strict parsing; raw bytes removed "
                    "with the isolated run directory and not redistributed"
                ),
            }
            for role, raw_artifact in raw_identities
        ],
        "parser": {
            "adapter_id": EXTRACTION_ADAPTER_ID,
            "adapter_sha256": runner_sha256,
            "element_record_rows": element.record_count,
            "element_record_keys": len(element.rows),
            "element_same_day_aggregation": element_same_day_aggregation_audit(
                element, element_artifact.sha256
            ),
            "element_fixed_width_overflow": element_fixed_width_overflow_audit(
                element, element_artifact.sha256
            ),
            "element_peakro_recovery": element_peak_recovery_audit(
                element,
                element_artifact.sha256,
                output_artifacts["soil_loss"].sha256,
            ),
            "hourly_record_dates": len(winter.covered_dates) if winter is not None else 0,
            "rain_on_snow_eligible_dates": (
                len(winter.rain_on_snow_dates) if winter is not None else 0
            ),
            "rain_on_snow_join": (
                "daily element QRain summed once for each mapped (year, ordinal day, OFE) "
                "having any hourly rain_fall>0 and positive snow_depth and snow_density"
            ),
            "rain_on_snow_units": "element QRain millimetres",
        },
        "climate_lineage": climate_json(job.climate),
    }


def deterministic_tar_gzip(members: list[tuple[str, Path]], destination: Path) -> Artifact:
    names = [name for name, _ in members]
    if len(names) != len(set(names)) or names != sorted(names):
        raise CampaignError("archive members must be unique and lexicographically sorted")
    temporary = destination.with_name(destination.name + ".part")
    with temporary.open("wb") as raw_output:
        with gzip.GzipFile(
            filename="", mode="wb", compresslevel=GZIP_LEVEL,
            mtime=FIXED_MTIME, fileobj=raw_output,
        ) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.USTAR_FORMAT) as archive:
                for name, path in members:
                    pure = PurePosixPath(name)
                    if pure.is_absolute() or ".." in pure.parts or not path.is_file():
                        raise CampaignError(f"unsafe archive member: {name}")
                    info = tarfile.TarInfo(name)
                    info.size = path.stat().st_size
                    info.mode = 0o644
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)
        raw_output.flush()
        os.fsync(raw_output.fileno())
    with temporary.open("rb") as handle:
        if handle.read(10) != CANONICAL_GZIP_HEADER:
            raise CampaignError("campaign archive gzip header is not canonical")
    os.replace(temporary, destination)
    return artifact_path(destination)


def resolve_repo_artifact(record: dict[str, Any], label: str) -> Path:
    relative = PurePosixPath(require_string(record.get("path"), f"{label}.path"))
    if relative.is_absolute() or ".." in relative.parts:
        raise CampaignError(f"{label}: unsafe repository-relative path")
    path = (ROOT / relative).resolve(strict=False)
    if not path.is_relative_to(ROOT.resolve(strict=True)):
        raise CampaignError(f"{label}: escapes repository root")
    assert_artifact(
        path,
        require_sha256(record.get("sha256"), f"{label}.sha256"),
        require_integer(record.get("bytes"), f"{label}.bytes"),
        label,
    )
    return path


def baseline_runspec_text(par: Path, cli: Path, years: int, burn: int) -> str:
    return "\n".join(
        [
            "cligen_runspec: 1",
            "station:",
            f"  par: {json.dumps(str(par))}",
            "mode: continuous",
            "simulation:",
            "  begin_year: 1",
            f"  years: {years}",
            "  interpolation: none",
            "rng:",
            f"  burn: {burn}",
            "generation_profile: faithful_5_32_3",
            "qc_filter: off",
            "output:",
            f"  cli: {json.dumps(str(cli))}",
            "  overwrite: true",
            "  quality: true",
            "",
        ]
    )


def run_external_verifier(command: list[str], label: str) -> str:
    result = run_checked(command, cwd=ROOT)
    stdout = result.stdout.decode("utf-8", "strict")
    if "passed" not in stdout.lower():
        raise CampaignError(f"{label} did not report a passing result: {stdout[-2000:]}")
    return stdout


def load_baseline_inputs() -> tuple[dict[tuple[str, int, int], ClimateIdentity], dict[str, bytes], dict[str, Any]]:
    freeze = require_dict(strict_json(PRE_CANDIDATE_FREEZE), "pre-candidate freeze")
    if freeze.get("status") != "passed" or freeze.get("candidate_output_absent") is not True:
        raise CampaignError("pre-candidate freeze is not a passing prospective freeze")
    frozen = require_dict(freeze.get("a5b_frozen_artifacts"), "pre-freeze A5b pins")
    for path in (CAMPAIGN, RUNNER, BASELINE_VERIFIER):
        relative = path.relative_to(ROOT).as_posix()
        if frozen.get(relative) != sha256_path(path):
            raise CampaignError(f"pre-candidate freeze identity differs for {relative}")
    pinned = require_dict(freeze.get("a5a_pinned_artifacts"), "pre-freeze A5a pins")
    baseline_relative = BASELINE_MANIFEST.relative_to(ROOT).as_posix()
    archive_relative = BASELINE_ARCHIVE.relative_to(ROOT).as_posix()
    if (
        pinned.get(baseline_relative) != BASELINE_MANIFEST_SHA256
        or pinned.get(archive_relative) != BASELINE_ARCHIVE_SHA256
    ):
        raise CampaignError("pre-candidate freeze does not carry the exact accepted A5a baseline pins")
    assert_artifact(
        BASELINE_MANIFEST,
        BASELINE_MANIFEST_SHA256,
        BASELINE_MANIFEST_BYTES,
        "exact accepted A5a baseline manifest",
    )
    assert_artifact(
        BASELINE_ARCHIVE,
        BASELINE_ARCHIVE_SHA256,
        BASELINE_ARCHIVE_BYTES,
        "exact accepted A5a baseline archive",
    )
    verifier_output = run_external_verifier(
        [sys.executable, str(BASELINE_VERIFIER)],
        "accepted A5a historical-evidence verifier",
    )
    manifest_raw = BASELINE_MANIFEST.read_bytes()
    manifest = require_dict(strict_json_bytes(manifest_raw, str(BASELINE_MANIFEST)), "A5a manifest")
    archive_record = require_dict(manifest.get("archive"), "A5a manifest.archive")
    assert_artifact(
        BASELINE_ARCHIVE,
        require_sha256(archive_record.get("sha256"), "A5a archive SHA-256"),
        require_integer(archive_record.get("bytes"), "A5a archive bytes"),
        "accepted A5a archive",
    )
    rows = [
        require_dict(row, "A5a run")
        for row in require_list(manifest.get("runs"), "A5a runs")
        if require_dict(row, "A5a run").get("qc_filter") == "off"
    ]
    if len(rows) != 272:
        raise CampaignError(f"accepted faithful-off baseline must contain 272 runs, got {len(rows)}")
    station_rows = require_list(manifest["inputs"].get("station_parameters"), "A5a stations")
    par_by_member = {row["par_file"]: row for row in station_rows}
    wanted = set(par_by_member)
    wanted.update(row["provenance"] for row in rows)
    documents: dict[str, bytes] = {}
    with tarfile.open(BASELINE_ARCHIVE, mode="r:gz") as archive:
        members = {member.name: member for member in archive.getmembers()}
        if not wanted.issubset(members):
            raise CampaignError("accepted A5a archive lacks a selected baseline member")
        for name in sorted(wanted):
            member = members[name]
            if not member.isfile():
                raise CampaignError(f"accepted A5a member is not regular: {name}")
            handle = archive.extractfile(member)
            if handle is None:
                raise CampaignError(f"cannot read accepted A5a member: {name}")
            documents[name] = handle.read()
    par_bytes: dict[str, bytes] = {}
    for row in station_rows:
        station = require_string(row.get("station"), "A5a station")
        raw = documents[row["par_file"]]
        if sha256_bytes(raw) != row["par_sha256"] or len(raw) != row["par_bytes"]:
            raise CampaignError(f"{station}: accepted station .par identity differs")
        par_bytes[station] = raw
    identities: dict[tuple[str, int, int], ClimateIdentity] = {}
    for row in rows:
        station = require_string(row.get("station"), "A5a run station")
        horizon = require_integer(row.get("years"), "A5a run years")
        burn = require_integer(row.get("burn"), "A5a run burn")
        replicate = next((rep for rep, item_burn, _ in REPLICATES if item_burn == burn), None)
        if replicate is None:
            raise CampaignError(f"A5a run has unexpected burn offset: {burn}")
        provenance_raw = documents[row["provenance"]]
        if (
            sha256_bytes(provenance_raw) != row["provenance_sha256"]
            or len(provenance_raw) != row["provenance_bytes"]
        ):
            raise CampaignError(f"{station}/{horizon}/{burn}: accepted provenance identity differs")
        provenance = require_dict(
            strict_json_bytes(provenance_raw, row["provenance"]), "A5a provenance"
        )
        if (
            provenance["generation"]["profile"] != "faithful_5_32_3"
            or provenance["generation"]["qc_policy"] != "off"
            or provenance["artifact"]["content_sha256"] != row["cli_sha256"]
        ):
            raise CampaignError(f"{station}/{horizon}/{burn}: accepted faithful-off lineage differs")
        key = (station, horizon, replicate)
        if key in identities:
            raise CampaignError(f"duplicate A5a faithful-off key: {key}")
        identities[key] = ClimateIdentity(
            station_id=station,
            profile_id="faithful_off",
            generation_profile="faithful_5_32_3",
            station_model="fixed_monthly_5_32_3",
            horizon=horizon,
            replicate=replicate,
            burn=burn,
            extension_seed=None,
            parameter_schema="cligen_par_5_32_3",
            fit_period=(1980, 2009),
            parameter_sha256=provenance["station"]["parameter_set_sha256"],
            runspec_sha256=provenance["effective_runspec_sha256"],
            cli_sha256=row["cli_sha256"],
            cli_bytes=row["cli_bytes"],
            provenance_sha256=row["provenance_sha256"],
            quality_sha256=row["quality_report_sha256"],
            source_cli=None,
            baseline_provenance=provenance,
            baseline_record=row,
            candidate_record_raw=None,
            candidate_record=None,
        )
    if set(station for station, _, _ in identities) != set(EXPECTED_STATIONS):
        raise CampaignError("accepted baseline station set differs")
    return identities, par_bytes, {
        "pre_candidate_freeze": artifact_path(PRE_CANDIDATE_FREEZE),
        "manifest": Artifact(sha256_bytes(manifest_raw), len(manifest_raw)),
        "archive": artifact_path(BASELINE_ARCHIVE),
        "verifier": artifact_path(BASELINE_VERIFIER),
        "verifier_stdout_sha256": sha256_bytes(verifier_output.encode("utf-8")),
    }


def candidate_cli_path(directory: Path, row: dict[str, Any]) -> Path:
    stem = (
        f"{row['station_id']}-{row['candidate_id']}-{row['horizon_years']}yr-"
        f"rep{row['replicate']}-burn{row['legacy_burn']}"
    )
    return directory / row["candidate_id"] / f"{stem}.cli"


def load_candidate_inputs(
    manifest_path: Path,
    candidate_cli_dir: Path,
    cligen_binary: Path,
) -> tuple[dict[tuple[str, str, int, int], ClimateIdentity], dict[str, Any], bytes, str]:
    verifier_output = run_external_verifier(
        [
            sys.executable, str(CANDIDATE_VERIFIER), str(manifest_path),
            "--candidate-cli-dir", str(candidate_cli_dir),
        ],
        "A5b candidate verifier",
    )
    manifest_raw = manifest_path.read_bytes()
    manifest = require_dict(strict_json_bytes(manifest_raw, str(manifest_path)), "candidate manifest")
    if manifest["execution"]["candidate_cli_bytes_removed_after_wepp"] is not False:
        raise CampaignError("candidate manifest must retain CLI bytes before WEPP")
    binary_record = require_dict(manifest["build"].get("cligen_binary"), "candidate cligen binary")
    binary_path = resolve_repo_artifact(binary_record, "candidate cligen binary")
    if cligen_binary.resolve(strict=True) != binary_path.resolve(strict=True):
        raise CampaignError("supplied CLIGEN binary path differs from sealed candidate build")
    archives = {row["candidate_id"]: row for row in manifest["archives"]}
    rows_by_candidate: dict[str, list[dict[str, Any]]] = {candidate[0]: [] for candidate in CANDIDATES}
    for value in manifest["runs"]:
        row = require_dict(value, "candidate run index")
        rows_by_candidate[row["candidate_id"]].append(row)
    raw_records: dict[tuple[str, str, int, int], bytes] = {}
    for candidate_id, _, _ in CANDIDATES:
        archive_path = resolve_repo_artifact(
            require_dict(archives[candidate_id]["artifact"], f"{candidate_id} archive"),
            f"{candidate_id} archive",
        )
        wanted = {row["run_record"]["member"]: row for row in rows_by_candidate[candidate_id]}
        with tarfile.open(archive_path, mode="r:gz") as archive:
            members = {member.name: member for member in archive.getmembers()}
            if not set(wanted).issubset(members):
                raise CampaignError(f"{candidate_id}: archive lacks a run record")
            for name, row in wanted.items():
                member = members[name]
                handle = archive.extractfile(member)
                if handle is None or not member.isfile():
                    raise CampaignError(f"{candidate_id}: unreadable run record {name}")
                raw = handle.read()
                binding = row["run_record"]
                if sha256_bytes(raw) != binding["sha256"] or len(raw) != binding["bytes"]:
                    raise CampaignError(f"{candidate_id}: run-record binding differs: {name}")
                key = (candidate_id, row["station_id"], row["horizon_years"], row["replicate"])
                raw_records[key] = raw
    identities: dict[tuple[str, str, int, int], ClimateIdentity] = {}
    for row in manifest["runs"]:
        key = (row["candidate_id"], row["station_id"], row["horizon_years"], row["replicate"])
        record_raw = raw_records[key]
        record = require_dict(strict_json_bytes(record_raw, row["run_record"]["member"]), "A5b run record")
        matrix = record["matrix"]
        expected_candidate = CANDIDATE_BY_ID[row["candidate_id"]]
        expected_replicate = REPLICATES[row["replicate"]]
        if (
            matrix["station_model"] != expected_candidate[1]
            or matrix["generation_profile"] != expected_candidate[2]
            or (matrix["replicate"], matrix["legacy_burn"], matrix["extension_seed"])
            != expected_replicate
        ):
            raise CampaignError(f"{key}: candidate matrix identity differs")
        cli_path = candidate_cli_path(candidate_cli_dir, row)
        assert_artifact(cli_path, row["candidate_cli_sha256"], row["candidate_cli_bytes"], f"{key} CLI")
        identities[key] = ClimateIdentity(
            station_id=row["station_id"],
            profile_id=row["candidate_id"],
            generation_profile=matrix["generation_profile"],
            station_model=matrix["station_model"],
            horizon=row["horizon_years"],
            replicate=row["replicate"],
            burn=row["legacy_burn"],
            extension_seed=row["extension_seed"],
            parameter_schema="a5b_interannual_coefficients_v1",
            fit_period=(1980, 2009),
            parameter_sha256=record["inputs"]["coefficient_payload_sha256"],
            runspec_sha256=record["inputs"]["base_runspec_sha256"],
            cli_sha256=row["candidate_cli_sha256"],
            cli_bytes=row["candidate_cli_bytes"],
            provenance_sha256=row["run_record"]["sha256"],
            quality_sha256=row["quality_report"]["sha256"],
            source_cli=cli_path,
            baseline_provenance=None,
            baseline_record=None,
            candidate_record_raw=record_raw,
            candidate_record=record,
        )
    if len(identities) != 1_904:
        raise CampaignError(f"candidate identity count differs: {len(identities)}")
    return identities, manifest, manifest_raw, verifier_output


def matrix_jobs(
    baseline: dict[tuple[str, int, int], ClimateIdentity],
    candidates: dict[tuple[str, str, int, int], ClimateIdentity],
) -> list[Job]:
    jobs: list[Job] = []
    profiles = ("faithful_off", *(candidate[0] for candidate in CANDIDATES))
    sequence = 0
    for profile in profiles:
        for station in EXPECTED_STATIONS:
            domain = "cold_snow" if station in COLD_STATIONS else "general"
            for horizon in HORIZONS:
                for replicate, _, _ in REPLICATES:
                    if profile == "faithful_off":
                        climate = baseline[(station, horizon, replicate)]
                    else:
                        climate = candidates[(profile, station, horizon, replicate)]
                    jobs.append(Job(sequence, climate, domain))
                    sequence += 1
    if len(jobs) != EXPECTED_RUNS or len({job.record_id for job in jobs}) != EXPECTED_RUNS:
        raise CampaignError("WEPP matrix is not exactly 2,176 unique runs")
    return jobs


def matrix_projection(jobs: Iterable[Job]) -> list[dict[str, Any]]:
    return [
        {
            "sequence": job.sequence,
            "record_id": job.record_id,
            "station_id": job.climate.station_id,
            "profile_id": job.climate.profile_id,
            "generation_profile": job.climate.generation_profile,
            "horizon_years": job.climate.horizon,
            "replicate": job.climate.replicate,
            "legacy_burn": job.climate.burn,
            "extension_seed": job.climate.extension_seed,
            "domain": job.domain,
        }
        for job in jobs
    ]


def prepare_baseline_target(par_bytes: dict[str, bytes]) -> None:
    if BASELINE_TARGET.exists() or BASELINE_TARGET.is_symlink():
        raise CampaignError(
            f"exact A5a regeneration target must be absent before campaign: {BASELINE_TARGET}"
        )
    stations = BASELINE_TARGET / ".a5a-input-snapshot/stations"
    stations.mkdir(parents=True)
    for station in EXPECTED_STATIONS:
        path = stations / f"{station}.par"
        path.write_bytes(par_bytes[station])


def regenerate_baseline_cli(climate: ClimateIdentity, cligen_binary: Path) -> Path:
    if climate.baseline_record is None or climate.baseline_provenance is None:
        raise CampaignError("baseline climate lacks accepted lineage")
    stem = f"{climate.station_id}-{climate.horizon}yr-burn{climate.burn}-qc-off"
    cli = BASELINE_TARGET / f"{stem}.cli"
    quality = BASELINE_TARGET / f"{stem}.cli.quality.json"
    provenance = BASELINE_TARGET / f"{stem}.cli.provenance.json"
    runspec = BASELINE_TARGET / f"{stem}.yaml"
    par = BASELINE_TARGET / ".a5a-input-snapshot/stations" / f"{climate.station_id}.par"
    expected_lexical = climate.baseline_provenance["effective_runspec"]["station"]["lexical_path"]
    if str(par) != expected_lexical:
        raise CampaignError(
            "accepted A5a lexical station path cannot be reproduced from this repository location"
        )
    runspec.write_text(
        baseline_runspec_text(par, cli, climate.horizon, climate.burn), encoding="utf-8"
    )
    try:
        result = subprocess.run(
            [str(cligen_binary), "run", str(runspec)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise CampaignError(
                f"{stem}: baseline regeneration failed ({result.returncode}): "
                f"{result.stderr.decode('utf-8', 'replace')[-2000:]}"
            )
        record = climate.baseline_record
        assert_artifact(cli, record["cli_sha256"], record["cli_bytes"], f"{stem} regenerated CLI")
        assert_artifact(
            quality,
            record["quality_report_sha256"],
            record["quality_report_bytes"],
            f"{stem} regenerated quality report",
        )
        assert_artifact(
            provenance,
            record["provenance_sha256"],
            record["provenance_bytes"],
            f"{stem} regenerated provenance",
        )
        return cli
    except Exception:
        for path in (cli, quality, provenance, runspec):
            path.unlink(missing_ok=True)
        raise


def remove_regenerated_baseline(climate: ClimateIdentity) -> None:
    stem = f"{climate.station_id}-{climate.horizon}yr-burn{climate.burn}-qc-off"
    for suffix in (".cli", ".cli.quality.json", ".cli.provenance.json", ".yaml"):
        (BASELINE_TARGET / f"{stem}{suffix}").unlink(missing_ok=True)


def write_canonical(path: Path, value: Any) -> Artifact:
    raw = canonical_json_bytes(value)
    path.write_bytes(raw)
    return Artifact(sha256_bytes(raw), len(raw))


def execute_job(
    job: Job,
    built: BuiltWepp,
    cligen_binary: Path,
    management: bytes,
    staging_root: Path,
    validator: Draft202012Validator,
    semantic: Any,
    runner_sha256: str,
) -> RunResult:
    profile_stage = staging_root / job.climate.profile_id
    record_stage = profile_stage / job.record_id
    record_stage.mkdir(parents=True, exist_ok=False)
    baseline_generated = False
    try:
        source_cli = job.climate.source_cli
        if source_cli is None:
            source_cli = regenerate_baseline_cli(job.climate, cligen_binary)
            baseline_generated = True
        assert_artifact(
            source_cli,
            job.climate.cli_sha256,
            job.climate.cli_bytes,
            f"{job.record_id} source climate",
        )
        with tempfile.TemporaryDirectory(prefix=f"{job.record_id}-", dir=staging_root) as raw_tmp:
            workspace = Path(raw_tmp)
            runs = workspace / "runs"
            output = workspace / "output"
            runs.mkdir()
            output.mkdir()
            input_paths = {
                "run": runs / "a5b.run",
                "management": runs / "a5b.man",
                "soil": runs / "a5b.sol",
                "slope": runs / "a5b.slp",
            }
            input_paths["run"].write_bytes(run_file(job.climate.horizon, job.domain))
            input_paths["management"].write_bytes(management)
            input_paths["soil"].write_bytes(built.fixture["p326.sol"])
            input_paths["slope"].write_bytes(built.fixture["p326.slp"])
            climate_path = runs / "a5b.cli"
            calendar = install_climate(source_cli, climate_path, job.climate.horizon)
            input_artifacts = {role: artifact_path(path) for role, path in input_paths.items()}
            if input_artifacts["management"].sha256 != MANAGEMENT_SHA256:
                raise CampaignError(f"{job.record_id}: installed management differs")

            stdout_path = output / "stdout.txt"
            stderr_path = output / "stderr.txt"
            with input_paths["run"].open("rb") as stdin_handle, stdout_path.open("wb") as out_handle, stderr_path.open("wb") as err_handle:
                process = subprocess.run(
                    [str(built.executable)],
                    cwd=runs,
                    stdin=stdin_handle,
                    stdout=out_handle,
                    stderr=err_handle,
                    check=False,
                )
            stdout_raw = stdout_path.read_bytes()
            stderr_raw = stderr_path.read_bytes()
            try:
                stdout_text = stdout_raw.decode("ascii", "strict")
                stderr_text = stderr_raw.decode("ascii", "strict")
            except UnicodeDecodeError as error:
                raise CampaignError(f"{job.record_id}: WEPP log is not ASCII") from error
            if process.returncode != 0:
                raise CampaignError(f"{job.record_id}: WEPP exited {process.returncode}")
            if stdout_text.count(SUCCESS_BANNER) != 1:
                raise CampaignError(f"{job.record_id}: exact WEPP success banner count is not one")
            if stdout_text.count(WEPP_VERSION_OUTPUT) != 1:
                raise CampaignError(f"{job.record_id}: exact WEPP version output count is not one")
            if stderr_text:
                raise CampaignError(f"{job.record_id}: WEPP stderr is nonempty: {stderr_text[-1000:]}")
            warning = re.search(r"\b(?:warning|caution|note)\b", stdout_text, flags=re.IGNORECASE)
            if warning is not None:
                raise CampaignError(f"{job.record_id}: WEPP emitted a warning token: {warning.group(0)}")

            raw_outputs = {
                "element": output / "a5b.element.dat",
                "soil_loss": output / "a5b.loss.dat",
            }
            if job.domain == "cold_snow":
                raw_outputs["hourly_winter"] = output / "a5b.winter.dat"
            for role, path in raw_outputs.items():
                if not path.is_file() or path.stat().st_size == 0:
                    raise CampaignError(f"{job.record_id}: requested {role} output is missing/empty")
            event_hydrology = parse_event_hydrology(
                raw_outputs["soil_loss"], job.climate.horizon
            )
            element = parse_element(
                raw_outputs["element"], job.climate.horizon, event_hydrology
            )
            winter = (
                parse_winter(raw_outputs["hourly_winter"], job.climate.horizon)
                if "hourly_winter" in raw_outputs else None
            )
            output_artifacts = {role: artifact_path(path) for role, path in raw_outputs.items()}
            response = compose_response(
                job,
                built,
                runner_sha256,
                calendar,
                input_artifacts,
                output_artifacts,
                element,
                winter,
            )
            validate_response(validator, semantic, response)

            raw_identities = [
                (role, artifact_path(raw_path))
                for role, raw_path in (
                    *raw_outputs.items(),
                    ("stdout", stdout_path),
                    ("stderr", stderr_path),
                )
            ]
            for role, raw_artifact in raw_identities:
                if role in output_artifacts and raw_artifact != output_artifacts[role]:
                    raise CampaignError(f"{job.record_id}: output changed between parsing and sealing")
            execution = compose_execution_record(
                job,
                process.returncode,
                stdout_text.count(SUCCESS_BANNER),
                calendar,
                input_artifacts,
                raw_identities,
                runner_sha256,
                element,
                winter,
                output_artifacts,
            )
            response_path = record_stage / "response.json"
            execution_path = record_stage / "execution.json"
            response_artifact = write_canonical(response_path, response)
            execution_artifact = write_canonical(execution_path, execution)
            return RunResult(
                sequence=job.sequence,
                profile_id=job.climate.profile_id,
                record_id=job.record_id,
                response_path=response_path,
                execution_path=execution_path,
                raw_outputs=tuple(raw_identities),
                response_artifact=response_artifact,
                execution_artifact=execution_artifact,
                same_day_duplicate_rows=element.same_day_duplicate_rows,
                sm_fixed_width_overflow_count=element.sm_fixed_width_overflow_count,
                peak_fixed_width_recovery_count=element.peak_fixed_width_recovery_count,
            )
    except Exception:
        shutil.rmtree(record_stage, ignore_errors=True)
        raise
    finally:
        if baseline_generated:
            remove_regenerated_baseline(job.climate)


def archive_results(
    results: list[RunResult], publication: Path, final_output: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    archives: list[dict[str, Any]] = []
    run_index: list[dict[str, Any]] = []
    by_profile: dict[str, list[RunResult]] = {}
    for result in sorted(results, key=lambda item: item.sequence):
        by_profile.setdefault(result.profile_id, []).append(result)
    for profile_id in ("faithful_off", *(candidate[0] for candidate in CANDIDATES)):
        profile_results = by_profile.get(profile_id, [])
        if len(profile_results) != 272:
            raise CampaignError(f"{profile_id}: expected 272 WEPP results, got {len(profile_results)}")
        members: list[tuple[str, Path]] = []
        archive_name = f"wepp-response-{profile_id}-v1.tar.gz"
        for result in profile_results:
            response_member = f"runs/{result.record_id}/response.json"
            execution_member = f"runs/{result.record_id}/execution.json"
            members.extend(((response_member, result.response_path), (execution_member, result.execution_path)))
            run_index.append(
                {
                    "sequence": result.sequence,
                    "record_id": result.record_id,
                    "profile_id": result.profile_id,
                    "archive": archive_name,
                    "response": {
                        "member": response_member,
                        **artifact_json(result.response_artifact),
                    },
                    "execution": {
                        "member": execution_member,
                        **artifact_json(result.execution_artifact),
                    },
                    "raw_output_audit": [
                        {
                            "role": role,
                            "content": artifact_json(artifact),
                            "retained": False,
                        }
                        for role, artifact in result.raw_outputs
                    ],
                }
            )
        members.sort(key=lambda item: item[0])
        archive_artifact = deterministic_tar_gzip(members, publication / archive_name)
        final_path = final_output / archive_name
        archives.append(
            {
                "profile_id": profile_id,
                "format": "tar+gzip-canonical-v1",
                "member_count": len(members),
                "artifact": {
                    "path": final_path.relative_to(ROOT).as_posix(),
                    **artifact_json(archive_artifact),
                },
            }
        )
    return archives, sorted(run_index, key=lambda row: row["sequence"])


def atomic_write(path: Path, raw: bytes) -> None:
    temporary = path.with_name(path.name + ".a5b-wepp-part")
    if temporary.exists():
        raise CampaignError(f"atomic-write temporary path already exists: {temporary}")
    with temporary.open("wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    directory_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def plan_candidate_cli_lifecycle(
    manifest_path: Path,
    candidate_cli_dir: Path,
    manifest_raw: bytes,
    candidate_identities: dict[tuple[str, str, int, int], ClimateIdentity],
) -> tuple[dict[str, Any], bytes, Path]:
    root = ROOT.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    candidate_cli_dir = candidate_cli_dir.resolve(strict=True)
    if not manifest_path.is_relative_to(root) or not candidate_cli_dir.is_relative_to(root):
        raise CampaignError("candidate lifecycle paths must remain inside the repository")
    if candidate_cli_dir.is_symlink():
        raise CampaignError("candidate CLI root may not be a symlink")
    expected_files = {
        climate.source_cli.resolve(strict=True)
        for climate in candidate_identities.values()
        if climate.source_cli is not None
    }
    if len(expected_files) != 1_904:
        raise CampaignError("candidate CLI removal inventory is not exactly 1,904 files")
    actual_files: set[Path] = set()
    expected_directories = {candidate_cli_dir.resolve(strict=True)}
    expected_directories.update(path.parent for path in expected_files)
    for path in candidate_cli_dir.rglob("*"):
        if path.is_symlink():
            raise CampaignError(f"candidate CLI removal tree contains a symlink: {path}")
        if path.is_file():
            actual_files.add(path.resolve(strict=True))
        elif path.is_dir():
            if path.resolve(strict=True) not in expected_directories:
                raise CampaignError(f"candidate CLI removal tree has an unexpected directory: {path}")
        else:
            raise CampaignError(f"candidate CLI removal tree has a nonregular entry: {path}")
    if actual_files != expected_files:
        raise CampaignError("candidate CLI removal tree differs from the sealed 1,904-file inventory")

    pattern = re.compile(rb'("candidate_cli_bytes_removed_after_wepp"\s*:\s*)false')
    matches = list(pattern.finditer(manifest_raw))
    if len(matches) != 1:
        raise CampaignError("candidate manifest does not contain exactly one false lifecycle token")
    post_raw = pattern.sub(rb"\1true", manifest_raw, count=1)
    before = require_dict(strict_json_bytes(manifest_raw, "pre-WEPP candidate manifest"), "pre manifest")
    after = require_dict(strict_json_bytes(post_raw, "post-WEPP candidate manifest"), "post manifest")
    expected = json.loads(json.dumps(before))
    expected["execution"]["candidate_cli_bytes_removed_after_wepp"] = True
    if after != expected:
        raise CampaignError("candidate manifest transition changes more than the lifecycle boolean")

    quarantine = candidate_cli_dir.with_name(candidate_cli_dir.name + ".a5b-wepp-quarantine")
    if quarantine.exists() or quarantine.is_symlink():
        raise CampaignError(f"candidate CLI quarantine path already exists: {quarantine}")
    proof = {
        "pre_manifest": Artifact(sha256_bytes(manifest_raw), len(manifest_raw)),
        "post_manifest": Artifact(sha256_bytes(post_raw), len(post_raw)),
        "only_value_change": "execution.candidate_cli_bytes_removed_after_wepp: false -> true",
        "byte_edit": "the sole lexical false token was replaced by true; all other bytes retained",
        "candidate_cli_file_count_removed": len(expected_files),
        "transition_order": (
            "validated campaign staged; CLI root atomically quarantined; manifest atomically flipped; "
            "candidate and campaign evidence revalidated; campaign atomically published; quarantine deleted"
        ),
        "rollback_before_publication": True,
    }
    return proof, post_raw, quarantine


def activate_candidate_cli_lifecycle(
    manifest_path: Path,
    candidate_cli_dir: Path,
    quarantine: Path,
    post_raw: bytes,
) -> None:
    if quarantine.exists() or not candidate_cli_dir.is_dir():
        raise CampaignError("candidate lifecycle activation paths changed after planning")
    os.replace(candidate_cli_dir, quarantine)
    try:
        atomic_write(manifest_path, post_raw)
    except Exception:
        if candidate_cli_dir.exists():
            raise CampaignError("cannot roll back candidate quarantine: original path was recreated")
        os.replace(quarantine, candidate_cli_dir)
        raise


def rollback_candidate_cli_lifecycle(
    manifest_path: Path,
    candidate_cli_dir: Path,
    quarantine: Path,
    manifest_raw: bytes,
) -> None:
    atomic_write(manifest_path, manifest_raw)
    if candidate_cli_dir.exists():
        raise CampaignError("cannot roll back candidate quarantine: original path was recreated")
    if not quarantine.is_dir():
        raise CampaignError("cannot roll back candidate quarantine: quarantine is missing")
    os.replace(quarantine, candidate_cli_dir)


def expected_quarantine_files(
    candidate_cli_dir: Path,
    quarantine: Path,
    manifest: dict[str, Any],
) -> dict[Path, Artifact]:
    rows = require_list(manifest.get("runs"), "candidate manifest runs")
    expected: dict[Path, Artifact] = {}
    for value in rows:
        row = require_dict(value, "candidate manifest run")
        source = candidate_cli_path(candidate_cli_dir, row)
        try:
            relative = source.relative_to(candidate_cli_dir)
        except ValueError as error:
            raise CampaignError("candidate CLI inventory path escapes its root") from error
        destination = quarantine / relative
        if destination in expected:
            raise CampaignError(f"duplicate candidate CLI recovery path: {relative}")
        expected[destination] = Artifact(
            require_string(row.get("candidate_cli_sha256"), "candidate CLI SHA-256"),
            require_integer(row.get("candidate_cli_bytes"), "candidate CLI bytes"),
        )
    if len(expected) != 1_904:
        raise CampaignError("candidate CLI recovery inventory is not exactly 1,904 files")
    return expected


def finalize_candidate_cli_lifecycle(
    candidate_cli_dir: Path,
    quarantine: Path,
    manifest: dict[str, Any],
) -> None:
    if candidate_cli_dir.exists() or candidate_cli_dir.is_symlink():
        raise CampaignError("candidate CLI root exists during lifecycle finalization")
    if quarantine.is_symlink() or not quarantine.is_dir():
        raise CampaignError("candidate CLI quarantine is not a regular directory")
    expected = expected_quarantine_files(candidate_cli_dir, quarantine, manifest)
    expected_directories = {quarantine}
    for path in expected:
        expected_directories.update(path.parents)
    for path in quarantine.rglob("*"):
        if path.is_symlink():
            raise CampaignError(f"candidate CLI quarantine contains a symlink: {path}")
        if path.is_file():
            artifact = expected.get(path)
            if artifact is None:
                raise CampaignError(f"candidate CLI quarantine contains an unknown file: {path}")
            assert_artifact(path, artifact.sha256, artifact.bytes, "quarantined candidate CLI")
        elif path.is_dir():
            if path not in expected_directories:
                raise CampaignError(
                    f"candidate CLI quarantine contains an unknown directory: {path}"
                )
        else:
            raise CampaignError(f"candidate CLI quarantine has a nonregular entry: {path}")
    # A failed recursive deletion can leave a strict subset of the validated
    # inventory.  That subset remains safe to validate and delete on rerun.
    shutil.rmtree(quarantine)
    directory_fd = os.open(quarantine.parent, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    if quarantine.exists() or quarantine.is_symlink() or candidate_cli_dir.exists():
        raise CampaignError("candidate CLI bytes remain after lifecycle finalization")


def validate_campaign_extraction_identity(index: dict[str, Any]) -> str:
    contracts = require_dict(index.get("contracts"), "campaign contracts")
    runner_contract = require_dict(contracts.get("runner"), "campaign runner contract")
    if set(runner_contract) != {"path", "sha256"}:
        raise CampaignError("campaign runner contract is not closed")
    expected_path = RUNNER.relative_to(ROOT).as_posix()
    if require_string(
        runner_contract.get("path"), "campaign runner contract path"
    ) != expected_path:
        raise CampaignError("campaign runner contract path differs")
    runner_sha256 = require_sha256(
        runner_contract.get("sha256"), "campaign runner contract SHA-256"
    )
    if runner_sha256 != sha256_path(RUNNER):
        raise CampaignError("campaign runner contract SHA-256 differs")
    campaign_wepp = require_dict(index.get("wepp"), "campaign WEPP identity")
    if campaign_wepp.get("extraction_adapter_id") != EXTRACTION_ADAPTER_ID:
        raise CampaignError("campaign extraction adapter ID differs")
    return runner_sha256


def validate_response_extraction_adapter(
    response: dict[str, Any], runner_sha256: str, label: str
) -> None:
    response_execution = require_dict(
        response.get("wepp_execution"), f"{label}: WEPP execution"
    )
    response_adapter = require_dict(
        response_execution.get("extraction_adapter"), f"{label}: extraction adapter"
    )
    expected = {
        "adapter_id": EXTRACTION_ADAPTER_ID,
        "content_sha256": runner_sha256,
    }
    if response_adapter != expected:
        raise CampaignError(f"{label}: extraction adapter binding differs")


def validate_execution_extraction_adapter(
    parser: dict[str, Any], runner_sha256: str, label: str
) -> None:
    if (
        parser.get("adapter_id") != EXTRACTION_ADAPTER_ID
        or parser.get("adapter_sha256") != runner_sha256
    ):
        raise CampaignError(f"{label}: execution parser adapter binding differs")


def artifact_identity_map(
    value: Any,
    label: str,
    required_row_keys: set[str],
) -> dict[str, Artifact]:
    rows = require_list(value, label)
    identities: dict[str, Artifact] = {}
    for index, value_row in enumerate(rows):
        row = require_dict(value_row, f"{label}[{index}]")
        if set(row) != required_row_keys:
            raise CampaignError(f"{label}[{index}]: artifact row is not closed")
        role = require_string(row.get("role"), f"{label}[{index}].role")
        if role in identities:
            raise CampaignError(f"{label}: duplicate artifact role {role}")
        content = require_dict(row.get("content"), f"{label}[{index}].content")
        if set(content) != {"sha256", "bytes"}:
            raise CampaignError(f"{label}[{index}]: artifact content is not closed")
        size = require_integer(content.get("bytes"), f"{label}[{index}].bytes")
        if size < 0:
            raise CampaignError(f"{label}[{index}]: artifact byte count is negative")
        identities[role] = Artifact(
            require_sha256(content.get("sha256"), f"{label}[{index}].sha256"),
            size,
        )
    return identities


def validate_raw_output_bindings(
    indexed_audit: Any,
    response: dict[str, Any],
    execution: dict[str, Any],
    expected_station: str,
    expected_domain: str,
    label: str,
) -> None:
    domain = response.get("domain")
    climate = require_dict(response.get("climate"), f"{label}: response climate")
    station = require_string(climate.get("station_id"), f"{label}: response station")
    if (
        expected_station not in EXPECTED_STATIONS
        or expected_domain
        != ("cold_snow" if expected_station in COLD_STATIONS else "general")
        or station != expected_station
        or domain != expected_domain
    ):
        raise CampaignError(f"{label}: response domain differs")
    output_roles = {"element", "soil_loss"}
    if expected_domain == "cold_snow":
        output_roles.add("hourly_winter")
    raw_roles = output_roles | {"stdout", "stderr"}
    indexed = artifact_identity_map(
        indexed_audit,
        f"{label}: indexed raw outputs",
        {"role", "content", "retained"},
    )
    for index, row in enumerate(require_list(indexed_audit, f"{label}: indexed raw outputs")):
        if require_dict(row, f"{label}: indexed raw outputs[{index}]").get("retained") is not False:
            raise CampaignError(f"{label}: indexed raw output was retained")
    execution_audit = execution.get("raw_output_audit")
    executed = artifact_identity_map(
        execution_audit,
        f"{label}: execution raw outputs",
        {"role", "content", "retained", "source_audit"},
    )
    for index, row in enumerate(
        require_list(execution_audit, f"{label}: execution raw outputs")
    ):
        checked = require_dict(row, f"{label}: execution raw outputs[{index}]")
        if checked.get("retained") is not False or not require_string(
            checked.get("source_audit"), f"{label}: execution source audit"
        ):
            raise CampaignError(f"{label}: execution raw-output audit differs")
    response_outputs = artifact_identity_map(
        response.get("outputs"),
        f"{label}: response outputs",
        {"role", "content"},
    )
    if (
        set(indexed) != raw_roles
        or executed != indexed
        or set(response_outputs) != output_roles
        or response_outputs != {role: indexed[role] for role in output_roles}
    ):
        raise CampaignError(f"{label}: raw-output identities are not cross-bound")


def validate_staged_campaign(
    index: dict[str, Any],
    publication: Path,
    validator: Draft202012Validator,
    semantic: Any,
    expected_manifest: Artifact,
    manifest_path: Path | None = None,
) -> None:
    if index.get("status") != "sealed" or index.get("wepp_response_campaign_version") != 1:
        raise CampaignError("staged campaign index is not sealed revision 1")
    runner_sha256 = validate_campaign_extraction_identity(index)
    matrix = require_dict(index.get("matrix"), "campaign matrix")
    if matrix.get("expected_runs") != EXPECTED_RUNS or matrix.get("actual_runs") != EXPECTED_RUNS:
        raise CampaignError("staged campaign matrix count differs")
    lifecycle = index["candidate"]["lifecycle"]
    if lifecycle["post_manifest"] != artifact_json(expected_manifest):
        raise CampaignError("staged lifecycle does not bind the planned post manifest")
    if manifest_path is not None:
        assert_artifact(
            manifest_path,
            expected_manifest.sha256,
            expected_manifest.bytes,
            "post-WEPP candidate manifest",
        )
    runs = require_list(index.get("runs"), "campaign runs")
    if len(runs) != EXPECTED_RUNS:
        raise CampaignError("staged campaign run index count differs")
    campaign_execution = require_dict(index.get("execution"), "campaign execution")
    overflow_counts = require_dict(
        campaign_execution.get("element_fixed_width_overflow_counts"),
        "campaign element fixed-width overflow counts",
    )
    if set(overflow_counts) != {ELEMENT_SM_HEADER_FIELD}:
        raise CampaignError("campaign element fixed-width overflow counts are not closed")
    expected_sm_overflow_count = require_integer(
        overflow_counts.get(ELEMENT_SM_HEADER_FIELD),
        "campaign Sm fixed-width overflow count",
    )
    if expected_sm_overflow_count < 0:
        raise CampaignError("campaign Sm fixed-width overflow count is negative")
    expected_same_day_duplicate_rows = require_integer(
        campaign_execution.get("element_same_day_duplicate_rows"),
        "campaign same-day duplicate element rows",
    )
    if expected_same_day_duplicate_rows < 0:
        raise CampaignError("campaign same-day duplicate element rows are negative")
    recovery_counts = require_dict(
        campaign_execution.get("element_response_recovery_counts"),
        "campaign element response recovery counts",
    )
    if set(recovery_counts) != {ELEMENT_PEAK_HEADER_FIELD}:
        raise CampaignError("campaign element response recovery counts are not closed")
    expected_peak_recovery_count = require_integer(
        recovery_counts.get(ELEMENT_PEAK_HEADER_FIELD),
        "campaign PeakRO recovery count",
    )
    if expected_peak_recovery_count < 0:
        raise CampaignError("campaign PeakRO recovery count is negative")
    observed_sm_overflow_count = 0
    observed_same_day_duplicate_rows = 0
    observed_peak_recovery_count = 0
    indexed_by_archive: dict[str, list[dict[str, Any]]] = {}
    if len(EXPECTED_COORDINATES) != EXPECTED_RUNS:
        raise CampaignError("staged campaign coordinate projection differs")
    for expected_sequence, row in enumerate(runs):
        profile, station, horizon, replicate = EXPECTED_COORDINATES[expected_sequence]
        expected_record_id = (
            f"a5b-wepp-{station}-{profile}-{horizon}yr-rep{replicate}"
        )
        if (
            row.get("sequence") != expected_sequence
            or row.get("profile_id") != profile
            or row.get("record_id") != expected_record_id
        ):
            raise CampaignError("staged campaign run coordinate differs")
        indexed_by_archive.setdefault(row["archive"], []).append(row)
        if any(audit.get("retained") is not False for audit in row["raw_output_audit"]):
            raise CampaignError(f"{row['record_id']}: raw-output retention claim differs")
    for archive_row in index["archives"]:
        name = Path(archive_row["artifact"]["path"]).name
        path = publication / name
        assert_artifact(
            path,
            archive_row["artifact"]["sha256"],
            archive_row["artifact"]["bytes"],
            f"staged {name}",
        )
        if path.read_bytes()[:10] != CANONICAL_GZIP_HEADER:
            raise CampaignError(f"{name}: noncanonical gzip header")
        rows = indexed_by_archive.get(name, [])
        expected_members: dict[str, tuple[str, int, str]] = {}
        for row in rows:
            for role in ("response", "execution"):
                binding = row[role]
                expected_members[binding["member"]] = (
                    binding["sha256"], binding["bytes"], role
                )
        if len(expected_members) != 544 or archive_row["member_count"] != 544:
            raise CampaignError(f"{name}: expected exactly 544 response/execution members")
        documents: dict[str, dict[str, Any]] = {}
        with tarfile.open(path, mode="r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            if names != sorted(expected_members) or set(names) != set(expected_members):
                raise CampaignError(f"{name}: archive member set/order differs")
            for member in members:
                if (
                    not member.isfile()
                    or member.mode != 0o644
                    or member.mtime != 0
                    or member.uid != 0
                    or member.gid != 0
                    or member.uname != ""
                    or member.gname != ""
                    or member.pax_headers
                ):
                    raise CampaignError(f"{name}: noncanonical metadata for {member.name}")
                handle = archive.extractfile(member)
                if handle is None:
                    raise CampaignError(f"{name}: cannot read {member.name}")
                raw = handle.read()
                expected_sha, expected_bytes, role = expected_members[member.name]
                if sha256_bytes(raw) != expected_sha or len(raw) != expected_bytes:
                    raise CampaignError(f"{name}: member binding differs for {member.name}")
                document = require_dict(strict_json_bytes(raw, member.name), member.name)
                documents[member.name] = document
                if role == "response":
                    validate_response_extraction_adapter(
                        document, runner_sha256, member.name
                    )
                    validate_response(validator, semantic, document)
                else:
                    audit = require_list(document.get("raw_output_audit"), "execution raw audit")
                    if not audit or any(row.get("retained") is not False for row in audit):
                        raise CampaignError(f"{member.name}: raw-output audit differs")
                    element_audits = [row for row in audit if row.get("role") == "element"]
                    if len(element_audits) != 1:
                        raise CampaignError(f"{member.name}: element raw-output audit differs")
                    event_audits = [row for row in audit if row.get("role") == "soil_loss"]
                    if len(event_audits) != 1:
                        raise CampaignError(
                            f"{member.name}: event-hydrology raw-output audit differs"
                        )
                    element_content = require_dict(
                        element_audits[0].get("content"), f"{member.name}: element content"
                    )
                    element_sha256 = require_sha256(
                        element_content.get("sha256"), f"{member.name}: element SHA-256"
                    )
                    event_content = require_dict(
                        event_audits[0].get("content"),
                        f"{member.name}: event-hydrology content",
                    )
                    event_sha256 = require_sha256(
                        event_content.get("sha256"),
                        f"{member.name}: event-hydrology SHA-256",
                    )
                    parser_audit = require_dict(document.get("parser"), f"{member.name}: parser")
                    validate_execution_extraction_adapter(
                        parser_audit, runner_sha256, member.name
                    )
                    element_record_keys = require_integer(
                        parser_audit.get("element_record_keys"),
                        f"{member.name}: element record keys",
                    )
                    element_record_rows = require_integer(
                        parser_audit.get("element_record_rows"),
                        f"{member.name}: element record rows",
                    )
                    fixed_width_audit = require_dict(
                        parser_audit.get("element_fixed_width_overflow"),
                        f"{member.name}: element fixed-width overflow",
                    )
                    if fixed_width_audit.get("total_element_rows") != element_record_rows:
                        raise CampaignError(
                            f"{member.name}: fixed-width audit element row count differs"
                        )
                    observed_sm_overflow_count += validate_element_fixed_width_overflow_audit(
                        fixed_width_audit,
                        f"{member.name}: element fixed-width overflow",
                        element_sha256,
                    )
                    observed_same_day_duplicate_rows += (
                        validate_element_same_day_aggregation_audit(
                            parser_audit.get("element_same_day_aggregation"),
                            f"{member.name}: element same-day aggregation",
                            element_sha256,
                            element_record_rows,
                            element_record_keys,
                        )
                    )
                    observed_peak_recovery_count += validate_element_peak_recovery_audit(
                        parser_audit.get("element_peakro_recovery"),
                        f"{member.name}: element PeakRO recovery",
                        element_sha256,
                        event_sha256,
                        element_record_rows,
                        element_record_keys,
                    )
        for row in rows:
            response_document = documents.get(row["response"]["member"])
            execution_document = documents.get(row["execution"]["member"])
            if response_document is None or execution_document is None:
                raise CampaignError(f"{row['record_id']}: paired archive member is missing")
            if (
                response_document.get("record_id") != row["record_id"]
                or execution_document.get("record_id") != row["record_id"]
                or execution_document.get("sequence") != row["sequence"]
            ):
                raise CampaignError(f"{row['record_id']}: paired record identity differs")
            validate_raw_output_bindings(
                row.get("raw_output_audit"),
                response_document,
                execution_document,
                EXPECTED_COORDINATES[row["sequence"]][1],
                (
                    "cold_snow"
                    if EXPECTED_COORDINATES[row["sequence"]][1] in COLD_STATIONS
                    else "general"
                ),
                row["record_id"],
            )
    if observed_sm_overflow_count != expected_sm_overflow_count:
        raise CampaignError(
            "campaign Sm fixed-width overflow aggregate differs: "
            f"{observed_sm_overflow_count} != {expected_sm_overflow_count}"
        )
    if observed_same_day_duplicate_rows != expected_same_day_duplicate_rows:
        raise CampaignError(
            "campaign same-day duplicate element-row aggregate differs: "
            f"{observed_same_day_duplicate_rows} != {expected_same_day_duplicate_rows}"
        )
    if observed_peak_recovery_count != expected_peak_recovery_count:
        raise CampaignError(
            "campaign PeakRO recovery aggregate differs: "
            f"{observed_peak_recovery_count} != {expected_peak_recovery_count}"
        )
    index_path = publication / "wepp-response-campaign-v1.json"
    parsed = require_dict(strict_json(index_path), "staged campaign index")
    if parsed != index:
        raise CampaignError("staged campaign index bytes do not decode to the validated value")


def recover_published_lifecycle(
    candidate_manifest_path: Path,
    candidate_cli_dir: Path,
    output_dir: Path,
) -> dict[str, Any] | None:
    if not output_dir.exists() and not output_dir.is_symlink():
        return None
    if output_dir.is_symlink() or not output_dir.is_dir():
        raise CampaignError(f"output path is not a regular directory: {output_dir}")
    root = ROOT.resolve(strict=True)
    publication = output_dir.resolve(strict=True)
    if not publication.is_relative_to(root):
        raise CampaignError("published recovery output must remain inside the repository")
    manifest_path = candidate_manifest_path.resolve(strict=True)
    manifest_raw = manifest_path.read_bytes()
    manifest = require_dict(
        strict_json_bytes(manifest_raw, "published candidate manifest"),
        "published candidate manifest",
    )
    execution = require_dict(manifest.get("execution"), "candidate manifest execution")
    if execution.get("candidate_cli_bytes_removed_after_wepp") is not True:
        raise CampaignError(f"output directory already exists: {output_dir}")
    candidate_root = candidate_cli_dir.resolve(strict=False)
    if not candidate_root.is_relative_to(root):
        raise CampaignError("candidate recovery root must remain inside the repository")
    if candidate_root.exists() or candidate_root.is_symlink():
        raise CampaignError("published campaign conflicts with a present candidate CLI root")
    quarantine = candidate_root.with_name(candidate_root.name + ".a5b-wepp-quarantine")

    verifier_output = run_external_verifier(
        [
            sys.executable,
            str(CANDIDATE_VERIFIER),
            str(manifest_path),
            "--candidate-cli-dir",
            str(candidate_root),
        ],
        "published A5b lifecycle verifier",
    )
    index_path = publication / "wepp-response-campaign-v1.json"
    index = require_dict(strict_json(index_path), "published WEPP campaign index")
    expected_stdout = require_string(
        require_dict(index.get("candidate"), "campaign candidate").get(
            "post_removal_verifier_stdout_sha256"
        ),
        "post-removal verifier stdout SHA-256",
    )
    if sha256_bytes(verifier_output.encode("utf-8")) != expected_stdout:
        raise CampaignError("published candidate verifier output identity differs")
    validator, semantic = response_validator()
    manifest_artifact = Artifact(sha256_bytes(manifest_raw), len(manifest_raw))
    validate_staged_campaign(
        index,
        publication,
        validator,
        semantic,
        manifest_artifact,
        manifest_path,
    )
    if quarantine.exists() or quarantine.is_symlink():
        finalize_candidate_cli_lifecycle(candidate_root, quarantine, manifest)
    if quarantine.exists() or quarantine.is_symlink() or candidate_root.exists():
        raise CampaignError("published candidate lifecycle recovery is incomplete")
    return index


def execute_campaign(
    candidate_manifest_path: Path,
    candidate_cli_dir: Path,
    cligen_binary: Path,
    output_dir: Path,
    wepp_repo: Path,
    workers: int,
) -> dict[str, Any]:
    verify_normative_hashes()
    if not 1 <= workers <= 4:
        raise CampaignError("worker count must be in 1..4")
    recovered = recover_published_lifecycle(
        candidate_manifest_path,
        candidate_cli_dir,
        output_dir,
    )
    if recovered is not None:
        return recovered
    if output_dir.exists() or output_dir.is_symlink():
        raise CampaignError(f"output directory must not exist: {output_dir}")
    final_output = output_dir.resolve(strict=False)
    if not final_output.is_relative_to(ROOT.resolve(strict=True)):
        raise CampaignError("output directory must remain inside the repository")
    candidate_manifest_path = candidate_manifest_path.resolve(strict=True)
    candidate_cli_dir = candidate_cli_dir.resolve(strict=True)
    cligen_binary = cligen_binary.resolve(strict=True)
    baseline, par_bytes, baseline_evidence = load_baseline_inputs()
    candidates, candidate_manifest, manifest_raw, pre_verifier_output = load_candidate_inputs(
        candidate_manifest_path, candidate_cli_dir, cligen_binary
    )
    lifecycle, post_manifest_raw, quarantine = plan_candidate_cli_lifecycle(
        candidate_manifest_path, candidate_cli_dir, manifest_raw, candidates
    )
    post_manifest = Artifact(sha256_bytes(post_manifest_raw), len(post_manifest_raw))
    jobs = matrix_jobs(baseline, candidates)
    matrix_sha256 = sha256_bytes(compact_json_bytes(matrix_projection(jobs)))
    prepare_baseline_target(par_bytes)
    validator, semantic = response_validator()
    management: bytes | None = None
    publication = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.publication-", dir=output_dir.parent)
    )
    staging = publication / ".staging"
    staging.mkdir()
    results: list[RunResult] = []
    lifecycle_activated = False
    campaign_published = False
    try:
        with tempfile.TemporaryDirectory(prefix="a5b-wepp-build-", dir=ROOT / "target") as build_tmp:
            built = build_wepp(wepp_repo, Path(build_tmp))
            management = derive_management(built.fixture["p326.man"])
            runner_sha256 = sha256_path(RUNNER)
            failures: list[str] = []
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="a5b-wepp") as executor:
                futures = {
                    executor.submit(
                        execute_job,
                        job,
                        built,
                        cligen_binary,
                        management,
                        staging,
                        validator,
                        semantic,
                        runner_sha256,
                    ): job
                    for job in jobs
                }
                for future in as_completed(futures):
                    job = futures[future]
                    try:
                        results.append(future.result())
                    except Exception as error:
                        failures.append(f"{job.record_id}: {error}")
                        for pending in futures:
                            pending.cancel()
                        break
            if failures:
                raise CampaignError("WEPP campaign failed:\n" + "\n".join(failures))
            if len(results) != EXPECTED_RUNS:
                raise CampaignError(f"WEPP result count differs: {len(results)}")
            sm_fixed_width_overflow_count = sum(
                result.sm_fixed_width_overflow_count for result in results
            )
            same_day_duplicate_rows = sum(
                result.same_day_duplicate_rows for result in results
            )
            peak_fixed_width_recovery_count = sum(
                result.peak_fixed_width_recovery_count for result in results
            )
            archives, run_index = archive_results(results, publication, final_output)
            # The public archives contain only validated response/execution
            # records.  Every raw stream is hash-bound as retained=false and is
            # removed with the isolated workspace or this staging tree.
            shutil.rmtree(staging)
            if BASELINE_TARGET.exists():
                shutil.rmtree(BASELINE_TARGET)
            if BASELINE_TARGET.exists():
                raise CampaignError("baseline regeneration target remains after sealing")

            index = {
                "wepp_response_campaign_version": 1,
                "status": "sealed",
                "contracts": {
                    "campaign": {
                        "path": CAMPAIGN.relative_to(ROOT).as_posix(),
                        "sha256": sha256_path(CAMPAIGN),
                    },
                    "response_schema": {
                        "path": RESPONSE_SCHEMA.relative_to(ROOT).as_posix(),
                        "sha256": SCHEMA_SHA256,
                    },
                    "response_protocol": {
                        "path": RESPONSE_PROTOCOL.relative_to(ROOT).as_posix(),
                        "sha256": PROTOCOL_SHA256,
                    },
                    "response_verifier": {
                        "path": RESPONSE_VERIFIER.relative_to(ROOT).as_posix(),
                        "sha256": VALIDATOR_SHA256,
                    },
                    "runner": {
                        "path": RUNNER.relative_to(ROOT).as_posix(),
                        "sha256": runner_sha256,
                    },
                },
                "matrix": {
                    "stations": list(EXPECTED_STATIONS),
                    "horizons_years": list(HORIZONS),
                    "replicates": [
                        {"replicate": rep, "legacy_burn": burn, "extension_seed": seed}
                        for rep, burn, seed in REPLICATES
                    ],
                    "profiles": ["faithful_off", *(candidate[0] for candidate in CANDIDATES)],
                    "expected_runs": EXPECTED_RUNS,
                    "actual_runs": len(run_index),
                    "projection_sha256": matrix_sha256,
                },
                "wepp": {
                    "source_commit": SOURCE_COMMIT,
                    "source_extraction": "fresh git archive",
                    "compiler_path": str(built.compiler),
                    "compiler_version": built.compiler_version,
                    "linker": artifact_json(built.linker),
                    "linker_version": built.linker_version,
                    "link_path": LINK_PATH,
                    "compile_flags": list(COMPILE_FLAGS),
                    "build_recipe": (
                        "make -f makefile.arm64.mac with frozen FFLAGS through omitted-observe "
                        "link seam; explicit wepp_observe.for; lexical gfortran *.o -o wepp "
                        "under the pinned system-only PATH"
                    ),
                    "makefile_sha256": built.makefile_sha256,
                    "executable": {"sha256": WEPP_SHA256, "bytes": WEPP_BYTES},
                    "runtime_libraries": {
                        name: artifact_json(artifact) for name, artifact in sorted(built.libraries.items())
                    },
                    "reviewed_fixture": {
                        name: {"sha256": FIXTURE_HASHES[name], "bytes": len(raw)}
                        for name, raw in sorted(built.fixture.items())
                    },
                    "derived_management": {
                        "adapter_id": MANAGEMENT_ADAPTER_ID,
                        "sha256": MANAGEMENT_SHA256,
                        "bytes": len(management),
                    },
                    "run_adapter_id": RUN_ADAPTER_ID,
                    "climate_adapter_id": CLIMATE_ADAPTER_ID,
                    "extraction_adapter_id": EXTRACTION_ADAPTER_ID,
                },
                "baseline": {
                    key: artifact_json(value) if isinstance(value, Artifact) else value
                    for key, value in baseline_evidence.items()
                },
                "candidate": {
                    "pre_verifier_stdout_sha256": sha256_bytes(pre_verifier_output.encode("utf-8")),
                    "manifest_values_before_transition_sha256": sha256_bytes(compact_json_bytes(candidate_manifest)),
                    "lifecycle": {
                        key: artifact_json(value) if isinstance(value, Artifact) else value
                        for key, value in lifecycle.items()
                    },
                },
                "archives": archives,
                "runs": run_index,
                "execution": {
                    "workers": workers,
                    "failures": [],
                    "element_same_day_duplicate_rows": same_day_duplicate_rows,
                    "element_fixed_width_overflow_counts": {
                        ELEMENT_SM_HEADER_FIELD: sm_fixed_width_overflow_count,
                    },
                    "element_response_recovery_counts": {
                        ELEMENT_PEAK_HEADER_FIELD: peak_fixed_width_recovery_count,
                    },
                    "candidate_cli_bytes_removed_after_wepp": True,
                    "baseline_regenerations_removed": True,
                    "raw_wepp_outputs_removed": True,
                    "raw_wepp_outputs_redistributed": False,
                    "deterministic_compression": {
                        "gzip_level": GZIP_LEVEL,
                        "gzip_mtime": FIXED_MTIME,
                        "gzip_header_hex": CANONICAL_GZIP_HEADER.hex(),
                        "tar_format": "ustar",
                        "member_order": "lexicographic",
                    },
                },
            }
            write_canonical(publication / "wepp-response-campaign-v1.json", index)
            # Validate a complete, publishable campaign while the candidate
            # manifest and CLI directory remain untouched.
            validate_staged_campaign(
                index, publication, validator, semantic, post_manifest
            )

            rechecked_lifecycle, rechecked_post_raw, rechecked_quarantine = (
                plan_candidate_cli_lifecycle(
                    candidate_manifest_path,
                    candidate_cli_dir,
                    manifest_raw,
                    candidates,
                )
            )
            if (
                rechecked_lifecycle != lifecycle
                or rechecked_post_raw != post_manifest_raw
                or rechecked_quarantine != quarantine
            ):
                raise CampaignError("candidate lifecycle changed after preflight")

            activate_candidate_cli_lifecycle(
                candidate_manifest_path,
                candidate_cli_dir,
                quarantine,
                post_manifest_raw,
            )
            lifecycle_activated = True
            try:
                post_verifier_output = run_external_verifier(
                    [
                        sys.executable,
                        str(CANDIDATE_VERIFIER),
                        str(candidate_manifest_path),
                        "--candidate-cli-dir",
                        str(candidate_cli_dir),
                    ],
                    "post-removal A5b verifier",
                )
                index["candidate"]["post_removal_verifier_stdout_sha256"] = sha256_bytes(
                    post_verifier_output.encode("utf-8")
                )
                write_canonical(publication / "wepp-response-campaign-v1.json", index)
                validate_staged_campaign(
                    index,
                    publication,
                    validator,
                    semantic,
                    post_manifest,
                    candidate_manifest_path,
                )
                os.replace(publication, final_output)
                campaign_published = True
            except Exception:
                rollback_candidate_cli_lifecycle(
                    candidate_manifest_path,
                    candidate_cli_dir,
                    quarantine,
                    manifest_raw,
                )
                lifecycle_activated = False
                raise

            # The quarantine remains a byte-complete rollback source until the
            # validated campaign has been atomically published.  Only now are
            # the deprecated candidate CLI payload bytes irreversibly removed.
            # A deletion failure leaves a validated published campaign plus a
            # strict inventory subset that a same-command rerun can finalize.
            finalize_candidate_cli_lifecycle(candidate_cli_dir, quarantine, candidate_manifest)
            lifecycle_activated = False
            return index
    finally:
        if BASELINE_TARGET.exists():
            shutil.rmtree(BASELINE_TARGET, ignore_errors=True)
        if lifecycle_activated and not campaign_published and quarantine is not None:
            rollback_candidate_cli_lifecycle(
                candidate_manifest_path,
                candidate_cli_dir,
                quarantine,
                manifest_raw,
            )
        if publication.exists():
            shutil.rmtree(publication, ignore_errors=True)


def synthetic_cli(path: Path, horizon: int) -> None:
    header = [f"synthetic self-test header {index}\n" for index in range(13)]
    header.extend(
        (
            " da mo year  prcp  dur   tp     ip  tmax  tmin  rad  w-vl w-dir  tdew\n",
            " -- -- ---- ----- ----- ----- ----- ----- ----- ----- ----- ----- -----\n",
        )
    )
    rows: list[str] = []
    for year in range(1, horizon + 1):
        for month in range(1, 13):
            for day in range(1, month_days(year, month) + 1):
                rows.append(
                    f"{day:2d} {month:2d} {year:3d}  1.00  1.00  0.50  1.00 "
                    "20.00 10.00 100.00  2.00 180.00  5.00\n"
                )
    path.write_bytes("".join((*header, *rows)).encode("ascii") + CLI_TERMINATOR)


def synthetic_element(path: Path, horizon: int) -> None:
    lines = [
        " " + " ".join(ELEMENT_HEADER_FIELDS) + "\n",
        " " + " ".join(ELEMENT_UNITS_FIELDS) + "\n",
    ]
    for year in range(1, horizon + 1):
        values = [0.0] * 22
        values[0] = 1.0
        values[1] = float(year)
        values[3] = float(year) / 10.0
        values[19] = float(year) / 100.0
        values[20] = 0.25
        values[21] = 0.0
        tokens = [f"{value:.6f}" for value in values]
        tokens[ELEMENT_PEAK_NUMERIC_INDEX] = f"{values[ELEMENT_PEAK_NUMERIC_INDEX]:.3f}"
        tokens[ELEMENT_SM_NUMERIC_INDEX] = (
            ELEMENT_SM_OVERFLOW_TOKEN if year == 1 else "123.456"
        )
        if year == 1:
            tokens[ELEMENT_PEAK_NUMERIC_INDEX] = ELEMENT_SM_OVERFLOW_TOKEN
        lines.append(f"1 1 1 {year} " + " ".join(tokens) + "\n")
        if year == 1:
            duplicate = [0.0] * 22
            duplicate[1] = 0.5
            duplicate[3] = 0.2
            duplicate[19] = 0.005
            duplicate[20] = 0.125
            duplicate_tokens = [f"{value:.6f}" for value in duplicate]
            duplicate_tokens[ELEMENT_PEAK_NUMERIC_INDEX] = (
                f"{duplicate[ELEMENT_PEAK_NUMERIC_INDEX]:.3f}"
            )
            duplicate_tokens[ELEMENT_SM_NUMERIC_INDEX] = "100.000"
            lines.append("1 1 1 1 " + " ".join(duplicate_tokens) + "\n")
    path.write_text("".join(lines), encoding="ascii")


def synthetic_event_hydrology(path: Path, horizon: int) -> None:
    station_line = (
        "      Station:  SYNTHETIC SELF TEST                              "
        "CLIGEN VER. 5.32 5.32"
    )
    lines = [
        f"{station_line if value is None else value}\n"
        for value in EVENT_PREAMBLE_TEMPLATE
    ]
    for year in range(1, horizon + 1):
        peak = 1000.25 if year == 1 else float(year) / 10.0
        lines.extend(
            (
                "       Overland flow element number:  1\n",
                f"       Event date:  jan  1, year {year:4d}\n",
                "\n",
                "       precipitation amount    1.00       rainfall amount        1.00\n",
                "       snow melt amount        0.00       runoff amount          1.00\n",
                "       rain/melt duration      1.00       effective duration     1.00\n",
                f"       peak runoff rate    {peak:8.2f}       effective length       1.00\n",
                "\n",
                "       note: amounts = mm, durations = min, rates = mm/hr, length = meters\n",
            )
        )
    lines.extend(("\n", "     ANNUAL AVERAGE SUMMARIES\n"))
    path.write_text("".join(lines), encoding="ascii")


def synthetic_winter(path: Path, horizon: int) -> None:
    lines = [
        " date hr year snow fall rain fall ground drift falling drift melt water "
        "snow depth snow density frost depth thaw depth frost thickness residue cycle OFE\n"
    ]
    for year in range(1, horizon + 1):
        values = (1.0, 1.0, 0.0, 0.0, 0.5, 10.0, 100.0, 0.0, 0.0, 0.0, 0.0)
        lines.append(
            f"1 1 {year} " + " ".join(f"{value:.6f}" for value in values) + " 1 1\n"
        )
    path.write_text("".join(lines), encoding="ascii")


def fake_climate(
    station: str,
    profile: str,
    horizon: int,
    replicate: int,
) -> ClimateIdentity:
    rep, burn, seed = REPLICATES[replicate]
    if profile == "faithful_off":
        generation_profile = "faithful_5_32_3"
        station_model = "fixed_monthly_5_32_3"
        extension_seed = None
    else:
        _, station_model, generation_profile = CANDIDATE_BY_ID[profile]
        extension_seed = seed
    digest = sha256_bytes(f"{station}/{profile}/{horizon}/{replicate}".encode("ascii"))
    return ClimateIdentity(
        station_id=station,
        profile_id=profile,
        generation_profile=generation_profile,
        station_model=station_model,
        horizon=horizon,
        replicate=rep,
        burn=burn,
        extension_seed=extension_seed,
        parameter_schema="self_test",
        fit_period=(1980, 2009),
        parameter_sha256=digest,
        runspec_sha256=digest,
        cli_sha256=digest,
        cli_bytes=1,
        provenance_sha256=digest,
        quality_sha256=digest,
        source_cli=None,
        baseline_provenance=None,
        baseline_record=None,
        candidate_record_raw=None,
        candidate_record=None,
    )


def self_test(wepp_repo: Path) -> dict[str, Any]:
    verify_normative_hashes()
    target_root = ROOT / "target"
    target_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="a5b-wepp-self-test-", dir=target_root) as temporary:
        work = Path(temporary)
        built = build_wepp(wepp_repo, work / "build")
        management = derive_management(built.fixture["p326.man"])
        if Artifact(sha256_bytes(management), len(management)).sha256 != MANAGEMENT_SHA256:
            raise CampaignError("self-test management identity differs")
        for horizon in HORIZONS:
            for domain in ("general", "cold_snow"):
                raw = run_file(horizon, domain)
                if sha256_bytes(raw) != RUN_HASHES[(horizon, domain)]:
                    raise CampaignError(f"self-test run adapter differs for {horizon}/{domain}")

        integration = work / "pinned-event-integration"
        integration_runs = integration / "runs"
        integration_output = integration / "output"
        integration_runs.mkdir(parents=True)
        integration_output.mkdir()
        (integration_runs / "a5b.run").write_bytes(run_file(30, "general"))
        (integration_runs / "a5b.man").write_bytes(management)
        (integration_runs / "a5b.slp").write_bytes(built.fixture["p326.slp"])
        (integration_runs / "a5b.sol").write_bytes(built.fixture["p326.sol"])
        integration_climate = (
            ROOT
            / "docs/work-packages/20260709-golden-fixture-harness/artifacts/goldens/new-meadows-id-seed0.cli"
        )
        (integration_runs / "a5b.cli").write_bytes(integration_climate.read_bytes())
        integration_process = subprocess.run(
            [str(built.executable)],
            cwd=integration_runs,
            input=(integration_runs / "a5b.run").read_bytes(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if (
            integration_process.returncode != 0
            or integration_process.stderr
            or integration_process.stdout.count(SUCCESS_BANNER.encode("ascii")) != 1
        ):
            raise CampaignError("self-test pinned event-output integration run failed")
        integration_loss = integration_output / "a5b.loss.dat"
        integration_element = integration_output / "a5b.element.dat"
        if artifact_path(integration_loss) != Artifact(
            "09458763768f5cd300bdb5e7f5b7fb8ee3213a37cf5376be7dc0b6ab82224954",
            6_456,
        ):
            raise CampaignError("self-test pinned event-output identity differs")
        integration_event = parse_event_hydrology(integration_loss, 30)
        integration_parsed_element = parse_element(
            integration_element, 30, integration_event
        )
        if (
            integration_event.record_count != 1
            or integration_event.peaks != {(3, 196, 1): 0.19}
            or integration_parsed_element.event_peak_crosscheck_count != 1
        ):
            raise CampaignError("self-test pinned event-output parse differs")
        integration_lines = integration_loss.read_text(encoding="ascii").splitlines()
        integration_lines.insert(2, "THIS IS UNEXPECTED GARBAGE")
        integration_mutation = integration / "mutated-preamble.loss.dat"
        integration_mutation.write_text(
            "\n".join(integration_lines) + "\n", encoding="ascii"
        )
        try:
            parse_event_hydrology(integration_mutation, 30)
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted mutated pinned event preamble")

        cli_30 = work / "synthetic-30.cli"
        cli_100 = work / "synthetic-100.cli"
        installed_30 = work / "installed-30.cli"
        installed_100 = work / "installed-100.cli"
        synthetic_cli(cli_30, 30)
        synthetic_cli(cli_100, 100)
        audit_30 = install_climate(cli_30, installed_30, 30)
        audit_100 = install_climate(cli_100, installed_100, 100)
        if audit_30.source != audit_30.installed or audit_30.relabeled_rows != 0:
            raise CampaignError("self-test 30-year calendar adapter is not byte-identical")
        if audit_100.relabeled_rows != 365 or audit_100.source == audit_100.installed:
            raise CampaignError("self-test 100-year calendar adapter did not relabel exactly 365 rows")
        if b" 101 " not in installed_100.read_bytes():
            raise CampaignError("self-test installed 100-year climate lacks year label 101")
        if not installed_100.read_bytes().endswith(CLI_TERMINATOR):
            raise CampaignError("self-test installed climate lacks the exact run-end terminator")
        malformed_terminators = {
            "missing": cli_30.read_bytes()[: -len(CLI_TERMINATOR)],
            "duplicate": cli_30.read_bytes() + CLI_TERMINATOR,
            "noncanonical": cli_30.read_bytes()[: -len(CLI_TERMINATOR)] + b" \n",
            "trailing-content": cli_30.read_bytes() + b"x\n",
        }
        for label, malformed in malformed_terminators.items():
            malformed_path = work / f"malformed-terminator-{label}.cli"
            malformed_path.write_bytes(malformed)
            try:
                install_climate(malformed_path, work / f"installed-malformed-{label}.cli", 30)
            except CampaignError:
                pass
            else:
                raise CampaignError(f"self-test accepted {label} CLIGEN terminator mutation")

        element_path = work / "synthetic.element.dat"
        winter_path = work / "synthetic.winter.dat"
        loss_path = work / "synthetic.loss.dat"
        synthetic_element(element_path, 30)
        synthetic_winter(winter_path, 30)
        synthetic_event_hydrology(loss_path, 30)
        event_hydrology = parse_event_hydrology(loss_path, 30)
        element = parse_element(element_path, 30, event_hydrology)
        if (
            element.sm_fixed_width_overflow_count != 1
            or element.sm_fixed_width_overflow_first_key != (1, 1, 1)
            or element.record_count != 31
            or len(element.rows) != 30
            or element.same_day_duplicate_rows != 1
            or element.same_day_duplicate_first_key != (1, 1, 1)
            or element.peak_fixed_width_recovery_count != 1
            or element.peak_fixed_width_recovery_first_key != (1, 1, 1)
            or element.event_hydrology_record_count != 30
            or element.event_hydrology_unique_keys != 30
            or element.event_peak_crosscheck_count != 30
            or element.rows[(1, 1, 1)]
            != {
                "runoff": 1.5,
                "peak": 1000.25,
                "peak_milli": 1_000_250,
                "sediment": 0.015,
                "qrain": 0.375,
            }
        ):
            raise CampaignError("self-test parsed element audit/aggregation differs")
        element_artifact = artifact_path(element_path)
        overflow_audit = element_fixed_width_overflow_audit(
            element, element_artifact.sha256
        )
        if (
            validate_element_fixed_width_overflow_audit(
                overflow_audit, "self-test Sm overflow", element_artifact.sha256
            )
            != 1
        ):
            raise CampaignError("self-test Sm overflow closed audit differs")
        same_day_audit = element_same_day_aggregation_audit(
            element, element_artifact.sha256
        )
        if (
            validate_element_same_day_aggregation_audit(
                same_day_audit,
                "self-test same-day element aggregation",
                element_artifact.sha256,
                31,
                30,
            )
            != 1
        ):
            raise CampaignError("self-test same-day element aggregation audit differs")
        peak_audit = element_peak_recovery_audit(
            element, element_artifact.sha256, artifact_path(loss_path).sha256
        )
        if (
            validate_element_peak_recovery_audit(
                peak_audit,
                "self-test PeakRO recovery",
                element_artifact.sha256,
                artifact_path(loss_path).sha256,
                element.record_count,
                len(element.rows),
            )
            != 1
        ):
            raise CampaignError("self-test PeakRO recovery audit differs")

        excessive_event_keys = json.loads(json.dumps(peak_audit))
        excessive_event_keys["event_hydrology_records"] = 31
        excessive_event_keys["event_hydrology_unique_keys"] = 31
        excessive_event_keys["event_hydrology_duplicate_rows"] = 0
        excessive_event_keys["crosschecked_unique_keys"] = 31
        excessive_event_keys["observed"]["count"] = 31
        try:
            validate_element_peak_recovery_audit(
                excessive_event_keys,
                "self-test excessive event keys",
                element_artifact.sha256,
                artifact_path(loss_path).sha256,
                element.record_count,
                len(element.rows),
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted more event keys than element keys")

        excessive_recoveries = json.loads(json.dumps(peak_audit))
        excessive_recoveries["event_hydrology_records"] = 32
        excessive_recoveries["event_hydrology_duplicate_rows"] = 2
        excessive_recoveries["observed"]["count"] = 32
        try:
            validate_element_peak_recovery_audit(
                excessive_recoveries,
                "self-test excessive PeakRO recoveries",
                element_artifact.sha256,
                artifact_path(loss_path).sha256,
                element.record_count,
                len(element.rows),
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted more PeakRO recoveries than element rows")

        source_event_lines = loss_path.read_text(encoding="ascii").splitlines()

        def write_event_mutation(label: str, lines: list[str]) -> Path:
            mutation_path = work / f"synthetic-event-{label}.dat"
            mutation_path.write_text("\n".join(lines) + "\n", encoding="ascii")
            return mutation_path

        changed_event_header = list(source_event_lines)
        changed_event_header[0] += " changed"
        try:
            parse_event_hydrology(
                write_event_mutation("changed-header", changed_event_header), 30
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted changed event-hydrology header")

        duplicate_event_header = list(source_event_lines)
        duplicate_event_header.append(f" {EVENT_HYDROLOGY_HEADER}")
        try:
            parse_event_hydrology(
                write_event_mutation("duplicate-header", duplicate_event_header), 30
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted duplicate event-hydrology header")

        changed_event_version = list(source_event_lines)
        changed_event_version[7] = "                     VERSION  2020.501"
        try:
            parse_event_hydrology(
                write_event_mutation("changed-version", changed_event_version), 30
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted changed event-hydrology version")

        duplicate_event_version = list(source_event_lines)
        duplicate_event_version.append(source_event_lines[7])
        try:
            parse_event_hydrology(
                write_event_mutation("duplicate-version", duplicate_event_version), 30
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted duplicate event-hydrology version")

        duplicate_event_block = list(source_event_lines)
        annual_marker = duplicate_event_block.pop()
        trailing_blank = duplicate_event_block.pop()
        repeated_block = list(
            source_event_lines[
                len(EVENT_PREAMBLE_TEMPLATE) : len(EVENT_PREAMBLE_TEMPLATE) + 9
            ]
        )
        repeated_peak = next(
            index for index, line in enumerate(repeated_block) if "peak runoff rate" in line
        )
        repeated_block[repeated_peak] = repeated_block[repeated_peak].replace(
            " 1000.25", "  999.99"
        )
        duplicate_event_block.extend((*repeated_block, trailing_blank, annual_marker))
        duplicate_event = parse_event_hydrology(
            write_event_mutation("duplicate-block", duplicate_event_block), 30
        )
        if (
            duplicate_event.record_count != 31
            or duplicate_event.duplicate_rows != 1
            or duplicate_event.peaks[(1, 1, 1)] != 1000.25
        ):
            raise CampaignError("self-test event-hydrology maximum reduction differs")

        starred_event_peak = list(source_event_lines)
        first_event_peak = next(
            index
            for index, line in enumerate(starred_event_peak)
            if "peak runoff rate" in line
        )
        starred_event_peak[first_event_peak] = starred_event_peak[
            first_event_peak
        ].replace(" 1000.25", " *******")
        try:
            parse_event_hydrology(
                write_event_mutation("starred-peak", starred_event_peak), 30
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted starred event-hydrology PeakRO")

        zero_padded_event_peak = list(source_event_lines)
        zero_padded_event_peak[first_event_peak] = zero_padded_event_peak[
            first_event_peak
        ].replace(" 1000.25", " 01000.25")
        try:
            parse_event_hydrology(
                write_event_mutation("zero-padded-peak", zero_padded_event_peak), 30
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted zero-padded event-hydrology PeakRO")

        overwidth_event_peak = list(source_event_lines)
        overwidth_event_peak[first_event_peak] = overwidth_event_peak[
            first_event_peak
        ].replace(" 1000.25", " 100000.00")
        try:
            parse_event_hydrology(
                write_event_mutation("overwidth-peak", overwidth_event_peak), 30
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted over-width event-hydrology PeakRO")

        missing_peak_recovery = (
            source_event_lines[: len(EVENT_PREAMBLE_TEMPLATE)]
            + source_event_lines[len(EVENT_PREAMBLE_TEMPLATE) + 9 :]
        )
        missing_event = parse_event_hydrology(
            write_event_mutation("missing-recovery", missing_peak_recovery), 30
        )
        try:
            parse_element(element_path, 30, missing_event)
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted missing event PeakRO recovery")

        changed_crosscheck_peak = list(source_event_lines)
        event_peak_lines = [
            index
            for index, line in enumerate(changed_crosscheck_peak)
            if "peak runoff rate" in line
        ]
        changed_crosscheck_peak[event_peak_lines[1]] = changed_crosscheck_peak[
            event_peak_lines[1]
        ].replace("    0.20", "  999.00")
        changed_event = parse_event_hydrology(
            write_event_mutation("crosscheck", changed_crosscheck_peak), 30
        )
        try:
            parse_element(element_path, 30, changed_event)
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted inconsistent event/element PeakRO")

        boundary_element_lines = element_path.read_text(encoding="ascii").splitlines()
        boundary_tokens = boundary_element_lines[4].split()
        boundary_tokens[4 + ELEMENT_PEAK_NUMERIC_INDEX] = "0.194"
        boundary_element_lines[4] = " ".join(boundary_tokens)
        boundary_element = work / "synthetic-element-crosscheck-boundary.dat"
        boundary_element.write_text(
            "\n".join(boundary_element_lines) + "\n", encoding="ascii"
        )
        parse_element(boundary_element, 30, event_hydrology)

        try:
            element_peak_token_is_overflow("000.200", "self-test zero-padded PeakRO")
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted zero-padded element PeakRO")
        if element_sm_token_is_overflow("-0.000", "self-test signed Sm"):
            raise CampaignError("self-test signed numeric Sm was treated as overflow")
        try:
            element_sm_token_is_overflow("000.200", "self-test zero-padded Sm")
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted zero-padded element Sm")
        try:
            element_peak_token_is_overflow("-0.000", "self-test signed PeakRO")
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted signed element PeakRO")

        def mutate_element_token(label: str, numeric_index: int, token: str) -> Path:
            lines = element_path.read_text(encoding="ascii").splitlines()
            fields = lines[2].split()
            fields[4 + numeric_index] = token
            lines[2] = " ".join(fields)
            mutation_path = work / f"synthetic-element-{label}.dat"
            mutation_path.write_text("\n".join(lines) + "\n", encoding="ascii")
            return mutation_path

        def write_element_mutation(label: str, lines: list[str]) -> Path:
            mutation_path = work / f"synthetic-element-{label}.dat"
            mutation_path.write_text("\n".join(lines) + "\n", encoding="ascii")
            return mutation_path

        source_element_lines = element_path.read_text(encoding="ascii").splitlines()
        structural_mutations: dict[str, list[str]] = {}

        swapped_header = list(source_element_lines)
        swapped_header_fields = swapped_header[0].split()
        swapped_header_fields[23], swapped_header_fields[24] = (
            swapped_header_fields[24], swapped_header_fields[23]
        )
        swapped_header[0] = " " + " ".join(swapped_header_fields)
        structural_mutations["swapped-response-headers"] = swapped_header

        changed_sm_header = list(source_element_lines)
        changed_sm_fields = changed_sm_header[0].split()
        changed_sm_fields[4 + ELEMENT_SM_NUMERIC_INDEX] = "SoilMoisture"
        changed_sm_header[0] = " " + " ".join(changed_sm_fields)
        structural_mutations["changed-sm-header"] = changed_sm_header

        prepended_changed_header = list(source_element_lines)
        prepended_header_fields = prepended_changed_header[0].split()
        prepended_header_fields[0] = "XFE"
        prepended_changed_header.insert(0, " " + " ".join(prepended_header_fields))
        structural_mutations["prepended-changed-header"] = prepended_changed_header

        malformed_units = list(source_element_lines)
        malformed_units_fields = malformed_units[1].split()
        malformed_units_fields[4 + ELEMENT_SM_NUMERIC_INDEX] = "cm"
        malformed_units[1] = " " + " ".join(malformed_units_fields)
        structural_mutations["malformed-units"] = malformed_units

        missing_units = list(source_element_lines)
        del missing_units[1]
        structural_mutations["missing-units"] = missing_units

        duplicate_units = list(source_element_lines)
        duplicate_units.insert(2, duplicate_units[1])
        structural_mutations["duplicate-units"] = duplicate_units

        post_header_na = list(source_element_lines)
        post_header_na.insert(3, "na arbitrary post-header row")
        structural_mutations["post-header-na"] = post_header_na

        for label, lines in structural_mutations.items():
            mutation_path = write_element_mutation(label, lines)
            try:
                parse_element(mutation_path, 30, event_hydrology)
            except CampaignError:
                pass
            else:
                raise CampaignError(f"self-test accepted {label} element mutation")

        normal_sm_path = mutate_element_token(
            "numeric-sm", ELEMENT_SM_NUMERIC_INDEX, "123.456"
        )
        normal_sm = parse_element(normal_sm_path, 30, event_hydrology)
        normal_sm_artifact = artifact_path(normal_sm_path)
        normal_sm_audit = element_fixed_width_overflow_audit(
            normal_sm, normal_sm_artifact.sha256
        )
        if (
            normal_sm.sm_fixed_width_overflow_count != 0
            or normal_sm.sm_fixed_width_overflow_first_key is not None
            or normal_sm_audit["observed"] != {}
            or validate_element_fixed_width_overflow_audit(
                normal_sm_audit, "self-test numeric Sm", normal_sm_artifact.sha256
            )
            != 0
        ):
            raise CampaignError("self-test zero Sm overflow audit differs")

        element_mutations = {
            "runoff-star": (1, ELEMENT_SM_OVERFLOW_TOKEN),
            "peak-runoff-wrong-star": (3, "******"),
            "peak-runoff-overwidth": (3, "1000.250"),
            "sediment-star": (19, ELEMENT_SM_OVERFLOW_TOKEN),
            "qrain-star": (20, ELEMENT_SM_OVERFLOW_TOKEN),
            "wrong-sm-star": (ELEMENT_SM_NUMERIC_INDEX, "******"),
            "other-column-star": (6, ELEMENT_SM_OVERFLOW_TOKEN),
        }
        for label, (numeric_index, token) in element_mutations.items():
            mutation_path = mutate_element_token(label, numeric_index, token)
            try:
                parse_element(mutation_path, 30, event_hydrology)
            except CampaignError:
                pass
            else:
                raise CampaignError(f"self-test accepted {label} element mutation")

        winter = parse_winter(winter_path, 30)
        rain_on_snow = join_rain_on_snow(element, winter, 30)
        expected_rain_on_snow = {year: 0.25 for year in range(1, 31)}
        expected_rain_on_snow[1] = 0.375
        if rain_on_snow != expected_rain_on_snow:
            raise CampaignError("self-test daily/hourly rain-on-snow join differs")
        runoff_summary = summaries(element.yearly["annual_runoff"], 30)
        if runoff_summary["max"] != 30.0 or runoff_summary["p95"] != 29.0:
            raise CampaignError("self-test nearest-rank summary differs")

        climate = fake_climate("id106388", "fourier_eof", 30, 0)
        climate = ClimateIdentity(
            **{
                **climate.__dict__,
                "cli_sha256": audit_30.source.sha256,
                "cli_bytes": audit_30.source.bytes,
                "source_cli": cli_30,
            }
        )
        job = Job(0, climate, "cold_snow")
        input_paths = {}
        for index, role in enumerate(("run", "management", "soil", "slope"), 1):
            path = work / f"input-{role}"
            path.write_bytes(bytes((index,)) * index)
            input_paths[role] = artifact_path(path)
        output_artifacts = {
            "element": element_artifact,
            "soil_loss": artifact_path(loss_path),
            "hourly_winter": artifact_path(winter_path),
        }
        stdout_artifact = Artifact(sha256_bytes(b"synthetic stdout\n"), 17)
        stderr_artifact = Artifact(sha256_bytes(b""), 0)
        raw_identities = sorted(
            (
                *output_artifacts.items(),
                ("stdout", stdout_artifact),
                ("stderr", stderr_artifact),
            )
        )
        runner_sha256 = sha256_path(RUNNER)
        response = compose_response(
            job,
            built,
            runner_sha256,
            audit_30,
            input_paths,
            output_artifacts,
            element,
            winter,
        )
        validator, semantic = response_validator()
        validate_response(validator, semantic, response)
        validate_response_extraction_adapter(response, runner_sha256, "self-test response")
        identity_index = {
            "contracts": {
                "runner": {
                    "path": RUNNER.relative_to(ROOT).as_posix(),
                    "sha256": runner_sha256,
                }
            },
            "wepp": {"extraction_adapter_id": EXTRACTION_ADAPTER_ID},
        }
        if validate_campaign_extraction_identity(identity_index) != runner_sha256:
            raise CampaignError("self-test campaign extraction identity differs")
        for field, replacement in (
            ("adapter_id", "contradictory_extractor_v1"),
            ("content_sha256", "f" * 64),
        ):
            mutation = json.loads(json.dumps(response))
            mutation["wepp_execution"]["extraction_adapter"][field] = replacement
            try:
                validate_response_extraction_adapter(
                    mutation, runner_sha256, f"self-test response {field}"
                )
            except CampaignError:
                pass
            else:
                raise CampaignError(
                    f"self-test accepted contradictory response extractor {field}"
                )
        adapter_mutation = json.loads(json.dumps(identity_index))
        adapter_mutation["wepp"]["extraction_adapter_id"] = (
            "contradictory_extractor_v1"
        )
        runner_path_mutation = json.loads(json.dumps(identity_index))
        runner_path_mutation["contracts"]["runner"]["path"] = (
            "docs/work-packages/contradictory-runner.py"
        )
        runner_hash_mutation = json.loads(json.dumps(identity_index))
        runner_hash_mutation["contracts"]["runner"]["sha256"] = "f" * 64
        for mutation in (
            adapter_mutation,
            runner_path_mutation,
            runner_hash_mutation,
        ):
            try:
                validated_sha256 = validate_campaign_extraction_identity(mutation)
                validate_response_extraction_adapter(
                    response, validated_sha256, "self-test campaign mutation"
                )
            except CampaignError:
                pass
            else:
                raise CampaignError("self-test accepted contradictory campaign extractor")
        parser_identity = {
            "adapter_id": EXTRACTION_ADAPTER_ID,
            "adapter_sha256": runner_sha256,
        }
        validate_execution_extraction_adapter(
            parser_identity, runner_sha256, "self-test execution"
        )
        for field, replacement in (
            ("adapter_id", "contradictory_extractor_v1"),
            ("adapter_sha256", "f" * 64),
        ):
            mutation = dict(parser_identity)
            mutation[field] = replacement
            try:
                validate_execution_extraction_adapter(
                    mutation, runner_sha256, f"self-test execution {field}"
                )
            except CampaignError:
                pass
            else:
                raise CampaignError(
                    f"self-test accepted contradictory execution extractor {field}"
                )
        response_path = work / "response.json"
        response_artifact = write_canonical(response_path, response)

        execution_path = work / "execution.json"
        self_test_execution = compose_execution_record(
            job,
            0,
            1,
            audit_30,
            input_paths,
            raw_identities,
            runner_sha256,
            element,
            winter,
            output_artifacts,
        )
        if (
            self_test_execution["parser"]["element_fixed_width_overflow"]
            != overflow_audit
            or self_test_execution["parser"]["element_same_day_aggregation"]
            != same_day_audit
            or self_test_execution["parser"]["element_peakro_recovery"]
            != peak_audit
        ):
            raise CampaignError("self-test production execution-record element audit differs")
        if set(self_test_execution["input_artifacts"]) != {
            "run",
            "management",
            "soil",
            "slope",
        }:
            raise CampaignError("self-test production execution-record input roles differ")
        indexed_raw_audit = [
            {
                "role": role,
                "content": artifact_json(artifact),
                "retained": False,
            }
            for role, artifact in raw_identities
        ]
        validate_raw_output_bindings(
            indexed_raw_audit,
            response,
            self_test_execution,
            job.climate.station_id,
            job.domain,
            "self-test raw-output binding",
        )
        for surface in ("index", "response", "execution"):
            mutated_index = json.loads(json.dumps(indexed_raw_audit))
            mutated_response = json.loads(json.dumps(response))
            mutated_execution = json.loads(json.dumps(self_test_execution))
            if surface == "index":
                next(row for row in mutated_index if row["role"] == "soil_loss")[
                    "content"
                ]["sha256"] = "f" * 64
            elif surface == "response":
                next(
                    row for row in mutated_response["outputs"] if row["role"] == "soil_loss"
                )["content"]["sha256"] = "f" * 64
            else:
                next(
                    row
                    for row in mutated_execution["raw_output_audit"]
                    if row["role"] == "soil_loss"
                )["content"]["sha256"] = "f" * 64
            try:
                validate_raw_output_bindings(
                    mutated_index,
                    mutated_response,
                    mutated_execution,
                    job.climate.station_id,
                    job.domain,
                    f"self-test {surface} raw-output mutation",
                )
            except CampaignError:
                pass
            else:
                raise CampaignError(
                    f"self-test accepted contradictory {surface} raw-output identity"
                )
        changed_domain_index = [
            row for row in json.loads(json.dumps(indexed_raw_audit))
            if row["role"] != "hourly_winter"
        ]
        changed_domain_response = json.loads(json.dumps(response))
        changed_domain_response["domain"] = "general"
        changed_domain_response["climate"]["station_id"] = "bogus000"
        changed_domain_response["outputs"] = [
            row
            for row in changed_domain_response["outputs"]
            if row["role"] != "hourly_winter"
        ]
        changed_domain_execution = json.loads(json.dumps(self_test_execution))
        changed_domain_execution["raw_output_audit"] = [
            row
            for row in changed_domain_execution["raw_output_audit"]
            if row["role"] != "hourly_winter"
        ]
        try:
            validate_raw_output_bindings(
                changed_domain_index,
                changed_domain_response,
                changed_domain_execution,
                job.climate.station_id,
                job.domain,
                "self-test cold-to-general raw-output mutation",
            )
        except CampaignError:
            pass
        else:
            raise CampaignError(
                "self-test accepted a cold station as general without winter output"
            )
        try:
            compose_execution_record(
                job,
                0,
                1,
                audit_30,
                output_artifacts,
                raw_identities,
                runner_sha256,
                element,
                winter,
                output_artifacts,
            )
        except CampaignError:
            pass
        else:
            raise CampaignError("self-test accepted invalid execution-record input roles")
        execution_artifact = write_canonical(execution_path, self_test_execution)
        tar_one = work / "one.tar.gz"
        tar_two = work / "two.tar.gz"
        members = [("a/execution.json", execution_path), ("b/response.json", response_path)]
        tar_one_artifact = deterministic_tar_gzip(members, tar_one)
        tar_two_artifact = deterministic_tar_gzip(members, tar_two)
        if tar_one_artifact != tar_two_artifact:
            raise CampaignError("self-test deterministic tar+gzip differs across writes")

        baseline = {
            (station, horizon, replicate): fake_climate(
                station, "faithful_off", horizon, replicate
            )
            for station in EXPECTED_STATIONS
            for horizon in HORIZONS
            for replicate, _, _ in REPLICATES
        }
        candidates = {
            (candidate_id, station, horizon, replicate): fake_climate(
                station, candidate_id, horizon, replicate
            )
            for candidate_id, _, _ in CANDIDATES
            for station in EXPECTED_STATIONS
            for horizon in HORIZONS
            for replicate, _, _ in REPLICATES
        }
        jobs = matrix_jobs(baseline, candidates)
        matrix_sha256 = sha256_bytes(compact_json_bytes(matrix_projection(jobs)))
        if matrix_sha256 != SELF_TEST_MATRIX_SHA256:
            raise CampaignError(
                f"self-test matrix golden differs: {matrix_sha256} != {SELF_TEST_MATRIX_SHA256}"
            )
        publication_response_path = work / "publication-response.json"
        publication_execution_path = work / "publication-execution.json"
        publication_response_artifact = write_canonical(
            publication_response_path, {"self_test": "fixed response member"}
        )
        publication_execution_artifact = write_canonical(
            publication_execution_path, {"self_test": "fixed execution member"}
        )
        synthetic_results = [
            RunResult(
                sequence=matrix_job.sequence,
                profile_id=matrix_job.climate.profile_id,
                record_id=matrix_job.record_id,
                response_path=publication_response_path,
                execution_path=publication_execution_path,
                raw_outputs=(("element", output_artifacts["element"]),),
                response_artifact=publication_response_artifact,
                execution_artifact=publication_execution_artifact,
                same_day_duplicate_rows=element.same_day_duplicate_rows,
                sm_fixed_width_overflow_count=element.sm_fixed_width_overflow_count,
                peak_fixed_width_recovery_count=element.peak_fixed_width_recovery_count,
            )
            for matrix_job in jobs
        ]
        publication_one = work / "publication-one"
        publication_two = work / "publication-two"
        publication_one.mkdir()
        publication_two.mkdir()
        archives_one, runs_one = archive_results(
            synthetic_results, publication_one, work / "final-one"
        )
        archives_two, runs_two = archive_results(
            synthetic_results, publication_two, work / "final-two"
        )
        archive_identities_one = [row["artifact"] | {"path": Path(row["artifact"]["path"]).name} for row in archives_one]
        archive_identities_two = [row["artifact"] | {"path": Path(row["artifact"]["path"]).name} for row in archives_two]
        publication_projection = {
            "archives": archive_identities_one,
            "runs": runs_one,
            "element_same_day_duplicate_rows": sum(
                result.same_day_duplicate_rows for result in synthetic_results
            ),
            "element_fixed_width_overflow_counts": {
                ELEMENT_SM_HEADER_FIELD: sum(
                    result.sm_fixed_width_overflow_count for result in synthetic_results
                )
            },
            "element_response_recovery_counts": {
                ELEMENT_PEAK_HEADER_FIELD: sum(
                    result.peak_fixed_width_recovery_count
                    for result in synthetic_results
                )
            },
        }
        publication_sha256 = sha256_bytes(compact_json_bytes(publication_projection))
        if archive_identities_one != archive_identities_two or runs_one != runs_two:
            raise CampaignError("self-test 2,176-run evidence publication is not deterministic")
        if publication_sha256 != SELF_TEST_PUBLICATION_SHA256:
            raise CampaignError(
                "self-test publication golden differs: "
                f"{publication_sha256} != {SELF_TEST_PUBLICATION_SHA256}"
            )

        lifecycle_root = work / "candidate-cli-lifecycle"
        lifecycle_root.mkdir()
        lifecycle_identities: dict[tuple[str, str, int, int], ClimateIdentity] = {}
        lifecycle_rows: list[dict[str, Any]] = []
        for key, identity in candidates.items():
            row = {
                "candidate_id": identity.profile_id,
                "station_id": identity.station_id,
                "horizon_years": identity.horizon,
                "replicate": identity.replicate,
                "legacy_burn": identity.burn,
                "candidate_cli_sha256": sha256_bytes(b"x"),
                "candidate_cli_bytes": 1,
            }
            cli_path = candidate_cli_path(lifecycle_root, row)
            cli_path.parent.mkdir(exist_ok=True)
            cli_path.write_bytes(b"x")
            lifecycle_rows.append(row)
            lifecycle_identities[key] = ClimateIdentity(
                **{**identity.__dict__, "source_cli": cli_path}
            )
        lifecycle_manifest = work / "candidate-manifest.json"
        lifecycle_raw = canonical_json_bytes(
            {
                "execution": {"candidate_cli_bytes_removed_after_wepp": False},
                "runs": lifecycle_rows,
            }
        )
        lifecycle_manifest.write_bytes(lifecycle_raw)
        lifecycle_proof, lifecycle_post, lifecycle_quarantine = plan_candidate_cli_lifecycle(
            lifecycle_manifest,
            lifecycle_root,
            lifecycle_raw,
            lifecycle_identities,
        )
        activate_candidate_cli_lifecycle(
            lifecycle_manifest,
            lifecycle_root,
            lifecycle_quarantine,
            lifecycle_post,
        )
        if lifecycle_root.exists() or not lifecycle_quarantine.is_dir():
            raise CampaignError("self-test lifecycle quarantine did not activate")
        rollback_candidate_cli_lifecycle(
            lifecycle_manifest,
            lifecycle_root,
            lifecycle_quarantine,
            lifecycle_raw,
        )
        if not lifecycle_root.is_dir() or lifecycle_manifest.read_bytes() != lifecycle_raw:
            raise CampaignError("self-test lifecycle rollback did not restore exact bytes")
        activate_candidate_cli_lifecycle(
            lifecycle_manifest,
            lifecycle_root,
            lifecycle_quarantine,
            lifecycle_post,
        )
        partial_file = next(path for path in lifecycle_quarantine.rglob("*") if path.is_file())
        partial_file.unlink()
        lifecycle_document = require_dict(
            strict_json_bytes(lifecycle_post, "self-test lifecycle post manifest"),
            "self-test lifecycle post manifest",
        )
        finalize_candidate_cli_lifecycle(
            lifecycle_root,
            lifecycle_quarantine,
            lifecycle_document,
        )
        if lifecycle_root.exists() or lifecycle_quarantine.exists():
            raise CampaignError("self-test lifecycle finalization left candidate bytes")
        return {
            "status": "passed",
            "source_commit": SOURCE_COMMIT,
            "wepp": {"sha256": WEPP_SHA256, "bytes": WEPP_BYTES},
            "linker": {
                **artifact_json(built.linker),
                "version": built.linker_version,
                "path": LINK_PATH,
            },
            "runtime_libraries": {
                name: artifact_json(artifact) for name, artifact in sorted(built.libraries.items())
            },
            "management": {"sha256": MANAGEMENT_SHA256, "bytes": len(management)},
            "run_adapter_hashes": {
                f"{horizon}/{domain}": RUN_HASHES[(horizon, domain)]
                for horizon in HORIZONS
                for domain in ("general", "cold_snow")
            },
            "calendar": {
                "30_year_relabeled_rows": audit_30.relabeled_rows,
                "100_year_relabeled_rows": audit_100.relabeled_rows,
            },
            "response": artifact_json(response_artifact),
            "execution": artifact_json(execution_artifact),
            "publication": {
                "tar_gzip": artifact_json(tar_one_artifact),
                "raw_streams_retained": False,
                "runs": len(runs_one),
                "projection_sha256": publication_sha256,
                "element_same_day_duplicate_rows": publication_projection[
                    "element_same_day_duplicate_rows"
                ],
                "element_fixed_width_overflow_counts": publication_projection[
                    "element_fixed_width_overflow_counts"
                ],
                "element_response_recovery_counts": publication_projection[
                    "element_response_recovery_counts"
                ],
            },
            "lifecycle": {
                key: artifact_json(value) if isinstance(value, Artifact) else value
                for key, value in lifecycle_proof.items()
            },
            "matrix": {"runs": len(jobs), "projection_sha256": matrix_sha256},
        }


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_manifest", nargs="?", type=Path)
    parser.add_argument("candidate_cli_dir", nargs="?", type=Path)
    parser.add_argument("cligen_binary", nargs="?", type=Path)
    parser.add_argument("output_dir", nargs="?", type=Path)
    parser.add_argument("--wepp-repo", type=Path, default=DEFAULT_WEPP_REPO)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--self-test", action="store_true")
    return parser


def main() -> None:
    args = argument_parser().parse_args()
    production = (
        args.candidate_manifest,
        args.candidate_cli_dir,
        args.cligen_binary,
        args.output_dir,
    )
    try:
        if args.self_test:
            if any(value is not None for value in production):
                raise CampaignError("--self-test does not accept production positional arguments")
            if args.workers != 4:
                raise CampaignError("--workers is not meaningful with --self-test")
            result = self_test(args.wepp_repo)
        else:
            if any(value is None for value in production):
                raise CampaignError(
                    "production requires CANDIDATE_MANIFEST CANDIDATE_CLI_DIR "
                    "CLIGEN_BINARY OUTPUT_DIR"
                )
            result = execute_campaign(
                args.candidate_manifest,
                args.candidate_cli_dir,
                args.cligen_binary,
                args.output_dir,
                args.wepp_repo,
                args.workers,
            )
        print(canonical_json_bytes(result).decode("utf-8"), end="")
    except (CampaignError, OSError, tarfile.TarError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
