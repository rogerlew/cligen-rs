#!/usr/bin/env python3
"""Verify a scientific-report manifest and its repository-bound artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote


REQUIRED_SECTIONS = [
    "Abstract",
    "Introduction",
    "Hypotheses",
    "Methods",
    "Analysis",
    "Results",
    "Limitations and validity",
    "Conclusions",
    "Reproducibility and data availability",
    "References",
]
REQUIRED_METADATA = [
    "Report ID",
    "Status",
    "Date",
    "Revision",
    "Authors",
    "Evidence mode",
    "Experiment record",
    "Evidence snapshot",
    "Review record",
]


class VerificationError(ValueError):
    """A deterministic report-contract failure."""


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise VerificationError(f"nonfinite JSON token: {value}")


def require_finite_json(value: Any, where: str = "manifest") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise VerificationError(f"nonfinite JSON number in {where}")
    if isinstance(value, dict):
        for key, child in value.items():
            require_finite_json(child, f"{where}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            require_finite_json(child, f"{where}[{index}]")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=strict_object,
            parse_constant=reject_constant,
        )
    except (OSError, json.JSONDecodeError, VerificationError) as error:
        raise VerificationError(f"cannot read strict JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise VerificationError("manifest root must be an object")
    require_finite_json(value)
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_keys(value: dict[str, Any], keys: set[str], where: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise VerificationError(f"{where} missing keys: {', '.join(missing)}")


def resolve(repo: Path, relative: str) -> Path:
    candidate = (repo / relative).resolve()
    try:
        candidate.relative_to(repo.resolve())
    except ValueError as error:
        raise VerificationError(f"path escapes repository: {relative}") from error
    if not candidate.is_file():
        raise VerificationError(f"missing file: {relative}")
    return candidate


def metadata(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in REQUIRED_METADATA:
        matches = re.findall(rf"(?m)^{re.escape(field)}:\s*(.+?)\s*$", text)
        if len(matches) != 1:
            raise VerificationError(f"metadata {field!r} must occur exactly once")
        result[field] = matches[0]
    return result


def local_links(report: Path, text: str) -> None:
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = target.strip().strip("<>")
        if not target or target.startswith(("#", "https://", "http://", "mailto:")):
            continue
        local = target.split("#", 1)[0]
        if not (report.parent / local).resolve().exists():
            raise VerificationError(f"broken local Markdown link: {target}")


def cited_ids(text: str, prefix: str) -> set[str]:
    digits = r"\d+" if prefix == "H" else r"\d{2}"
    return set(re.findall(rf"\b{prefix}{digits}\b", text))


def fact_display(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(item, (str, int, float)) for item in value):
        return ", ".join(fact_display(item) for item in value)
    raise VerificationError("study fact values must be scalar or scalar arrays")


def fact_label(key: str) -> str:
    words = key.split("_")
    rendered = ["WEPP" if word == "wepp" else word for word in words]
    label = " ".join(rendered)
    return label[0].upper() + label[1:]


def hypothesis_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        if not re.match(r"^\| H\d+ \|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            raise VerificationError(f"hypothesis row must have six cells: {line}")
        hypothesis_id, provenance, _, _, outcome, _ = cells
        if hypothesis_id in rows:
            raise VerificationError(f"duplicate report hypothesis row: {hypothesis_id}")
        rows[hypothesis_id] = (provenance, outcome)
    return rows


def verify(repo: Path, manifest_path: Path, internal_review: bool = False) -> None:
    manifest = read_json(manifest_path)
    require_keys(
        manifest,
        {
            "report_manifest_version",
            "report_id",
            "report_revision",
            "status",
            "report",
            "governance",
            "required_sections",
            "study_facts",
            "hypotheses",
            "evidence",
            "references",
            "reviews",
        },
        "manifest",
    )
    if manifest["report_manifest_version"] != 1:
        raise VerificationError("report_manifest_version must be 1")
    if (
        isinstance(manifest["report_revision"], bool)
        or not isinstance(manifest["report_revision"], int)
        or manifest["report_revision"] < 1
    ):
        raise VerificationError("report_revision must be a positive integer")
    required_status = "INTERNAL-REVIEW" if internal_review else "ACCEPTED"
    if manifest["status"] != required_status:
        raise VerificationError(f"verification requires status {required_status}")
    if manifest["required_sections"] != REQUIRED_SECTIONS:
        raise VerificationError("required_sections does not match standard version 1")

    report_info = manifest["report"]
    if not isinstance(report_info, dict):
        raise VerificationError("report must be an object")
    require_keys(report_info, {"path", "sha256"}, "report")
    report = resolve(repo, report_info["path"])
    expected_name = f"{manifest['report_id']}-report.md"
    if report.name != expected_name:
        raise VerificationError(f"report filename must be {expected_name}")
    if sha256(report) != report_info["sha256"]:
        raise VerificationError("report SHA-256 mismatch")

    governance = manifest["governance"]
    if not isinstance(governance, list) or len(governance) != 3:
        raise VerificationError("governance must identify standard, protocol, and template")
    governance_roles: set[str] = set()
    for index, item in enumerate(governance):
        if not isinstance(item, dict):
            raise VerificationError(f"governance[{index}] must be an object")
        require_keys(item, {"role", "path", "sha256"}, f"governance[{index}]")
        path = resolve(repo, item["path"])
        if sha256(path) != item["sha256"]:
            raise VerificationError(f"governance hash mismatch: {item['role']}")
        governance_roles.add(item["role"])
    if governance_roles != {"standard", "protocol", "template"}:
        raise VerificationError("governance roles must be standard, protocol, and template")

    text = report.read_text(encoding="utf-8")
    fields = metadata(text)
    h1_headings = re.findall(r"(?m)^# ([^#\n].*?)\s*$", text)
    if len(h1_headings) != 1:
        raise VerificationError("report must contain exactly one H1 heading")
    if fields["Report ID"].strip("`") != manifest["report_id"]:
        raise VerificationError("report ID does not match manifest")
    if fields["Status"].strip("`") != manifest["status"]:
        raise VerificationError("report status does not match manifest")
    if fields["Revision"] != str(manifest["report_revision"]):
        raise VerificationError("report revision does not match manifest")
    if fields["Evidence mode"] not in {"Ran", "Static", "Derived", "Mixed"}:
        raise VerificationError("invalid Evidence mode")
    placeholder_pattern = (
        r"\b(TODO|TBD|FIXME|XXX)\b|"
        r"<(stable-id|experiment title|lead author|person or role|repository-relative link)>|"
        r"YYYYMMDD|YYYY-MM-DD"
    )
    if re.search(placeholder_pattern, text, re.IGNORECASE):
        raise VerificationError("report contains a drafting placeholder")

    headings = re.findall(r"(?m)^## ([^#\n].*?)\s*$", text)
    required_positions: list[int] = []
    for section in REQUIRED_SECTIONS:
        count = headings.count(section)
        if count != 1:
            raise VerificationError(f"section {section!r} must occur exactly once")
        required_positions.append(headings.index(section))
    if required_positions != sorted(required_positions):
        raise VerificationError("required sections are out of order")
    local_links(report, text)

    study_facts = manifest["study_facts"]
    if not isinstance(study_facts, dict) or not study_facts:
        raise VerificationError("study_facts must be a nonempty object")
    for key, value in study_facts.items():
        row = f"| {fact_label(key)} | {fact_display(value)} |"
        if text.count(row) != 1:
            raise VerificationError(f"study fact row missing or duplicated: {key}")
    arithmetic_keys = {
        "stations",
        "candidates",
        "horizons_years",
        "replicate_records_per_cell",
        "candidate_horizon_rows",
        "candidate_climates",
        "wepp_response_records",
        "wepp_execution_records",
    }
    if arithmetic_keys.issubset(study_facts):
        horizon_count = len(study_facts["horizons_years"])
        expected_rows = study_facts["candidates"] * horizon_count
        expected_climates = (
            expected_rows
            * study_facts["stations"]
            * study_facts["replicate_records_per_cell"]
        )
        expected_wepp = (
            (study_facts["candidates"] + 1)
            * horizon_count
            * study_facts["stations"]
            * study_facts["replicate_records_per_cell"]
        )
        if study_facts["candidate_horizon_rows"] != expected_rows:
            raise VerificationError("candidate_horizon_rows arithmetic mismatch")
        if study_facts["candidate_climates"] != expected_climates:
            raise VerificationError("candidate_climates arithmetic mismatch")
        if study_facts["wepp_response_records"] != expected_wepp:
            raise VerificationError("wepp_response_records arithmetic mismatch")
        if study_facts["wepp_execution_records"] != expected_wepp:
            raise VerificationError("wepp_execution_records arithmetic mismatch")

    hypotheses = manifest["hypotheses"]
    if not isinstance(hypotheses, list) or not hypotheses:
        raise VerificationError("hypotheses must be a nonempty array")
    hypothesis_ids: list[str] = []
    for index, item in enumerate(hypotheses):
        if not isinstance(item, dict):
            raise VerificationError(f"hypotheses[{index}] must be an object")
        require_keys(item, {"id", "provenance", "outcome", "evidence_ids"}, f"hypotheses[{index}]")
        if item["outcome"] in ("", "pending", None):
            raise VerificationError(f"hypothesis {item['id']} has no final outcome")
        hypothesis_ids.append(item["id"])
    if len(hypothesis_ids) != len(set(hypothesis_ids)):
        raise VerificationError("duplicate hypothesis ID")
    if cited_ids(text, "H") != set(hypothesis_ids):
        raise VerificationError("report/manifest hypothesis IDs differ")
    rows = hypothesis_rows(text)
    if set(rows) != set(hypothesis_ids):
        raise VerificationError("hypothesis registry rows do not match manifest")
    for hypothesis in hypotheses:
        provenance, outcome = rows[hypothesis["id"]]
        if provenance != hypothesis["provenance"]:
            raise VerificationError(f"hypothesis provenance mismatch: {hypothesis['id']}")
        if outcome != hypothesis["outcome"]:
            raise VerificationError(f"hypothesis outcome mismatch: {hypothesis['id']}")

    evidence = manifest["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise VerificationError("evidence must be a nonempty array")
    evidence_ids: list[str] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise VerificationError(f"evidence[{index}] must be an object")
        require_keys(item, {"id", "path", "sha256", "role"}, f"evidence[{index}]")
        path = resolve(repo, item["path"])
        if sha256(path) != item["sha256"]:
            raise VerificationError(f"evidence hash mismatch: {item['id']}")
        evidence_ids.append(item["id"])
    if len(evidence_ids) != len(set(evidence_ids)):
        raise VerificationError("duplicate evidence ID")
    body_text = text.split("\n## References\n", 1)[0]
    if cited_ids(body_text, "E") != set(evidence_ids):
        raise VerificationError("report/manifest evidence IDs differ")
    known_evidence = set(evidence_ids)
    for hypothesis in hypotheses:
        if not set(hypothesis["evidence_ids"]).issubset(known_evidence):
            raise VerificationError(f"hypothesis {hypothesis['id']} cites unknown evidence")

    references = manifest["references"]
    if not isinstance(references, list) or not references:
        raise VerificationError("references must be a nonempty array")
    reference_ids: list[str] = []
    dois: list[str] = []
    for index, item in enumerate(references):
        if not isinstance(item, dict):
            raise VerificationError(f"references[{index}] must be an object")
        require_keys(item, {"id", "citation", "doi_or_no_doi", "url"}, f"references[{index}]")
        reference_ids.append(item["id"])
        doi = item["doi_or_no_doi"]
        if doi != "No DOI":
            dois.append(doi.lower())
            canonical_url = f"https://doi.org/{quote(doi, safe='/:;()')}"
            if item["url"] != canonical_url:
                raise VerificationError(f"reference {item['id']} DOI URL mismatch")
    if len(reference_ids) != len(set(reference_ids)):
        raise VerificationError("duplicate reference ID")
    if len(dois) != len(set(dois)):
        raise VerificationError("duplicate DOI")
    if cited_ids(body_text, "R") != set(reference_ids):
        raise VerificationError("report/manifest reference IDs differ")

    reviews = manifest["reviews"]
    required_lenses = {"accuracy", "scientific-validity", "consistency-public-safety"}
    found_lenses: set[str] = set()
    for index, item in enumerate(reviews):
        if not isinstance(item, dict):
            raise VerificationError(f"reviews[{index}] must be an object")
        require_keys(item, {"lens", "path", "sha256", "verdict"}, f"reviews[{index}]")
        found_lenses.add(item["lens"])
        if internal_review:
            if item["verdict"] != "PENDING" or item["sha256"] != "PENDING":
                raise VerificationError(f"internal-review lens {item['lens']} must be PENDING")
            continue
        if item["verdict"] != "ACCEPT":
            raise VerificationError(f"review lens {item['lens']} is not accepted")
        review_path = resolve(repo, item["path"])
        if sha256(review_path) != item["sha256"]:
            raise VerificationError(f"review hash mismatch: {item['path']}")
        review_text = review_path.read_text(encoding="utf-8")
        verdicts = re.findall(r"(?m)^Final verdict: \*\*([^*]+)\*\*$", review_text)
        open_p1 = re.findall(r"(?m)^Open P1:\s*(\d+)\s*$", review_text)
        open_p2 = re.findall(r"(?m)^Open P2:\s*(\d+)\s*$", review_text)
        if verdicts != ["ACCEPT"] or open_p1 != ["0"] or open_p2 != ["0"]:
            raise VerificationError(f"review terminal block is not uniquely accepted: {item['path']}")
    if found_lenses != required_lenses:
        raise VerificationError("review lenses do not match the required set")

    catalog = resolve(repo, "docs/reports/README.md").read_text(encoding="utf-8")
    if report.name not in catalog:
        raise VerificationError("report is absent from docs/reports/README.md")
    catalog_rows = [line for line in catalog.splitlines() if f"({report.name})" in line]
    expected_catalog_status = "INTERNAL-REVIEW" if internal_review else "ACCEPTED"
    if len(catalog_rows) != 1 or f"| {expected_catalog_status} |" not in catalog_rows[0]:
        raise VerificationError(f"report catalog status must be uniquely {expected_catalog_status}")


def write_self_test_fixture(repo: Path) -> Path:
    (repo / "docs/reports").mkdir(parents=True)
    (repo / "evidence").mkdir()
    (repo / "review").mkdir()
    evidence = repo / "evidence/result.txt"
    evidence.write_text("42\n", encoding="utf-8")
    review = repo / "review/review.md"
    review.write_text(
        "# Review\n\nFinal verdict: **ACCEPT**\n\nOpen P1: 0\nOpen P2: 0\n",
        encoding="utf-8",
    )
    section_text = {
        "Introduction": "Claim [E01] [R01].",
        "Hypotheses": (
            "| ID | Provenance | Scope | Rule | Outcome | Result |\n"
            "|---|---|---|---|---|---|\n"
            "| H1 | preregistered | Scope | Rule | Not supported | Results |"
        ),
        "Methods": (
            "### Study identity\n\n"
            "| Fact | Registered value |\n"
            "|---|---|\n"
            "| Answer | 42 |"
        ),
        "References": "R01 publication. E01 evidence.",
    }
    body = "\n\n".join(
        f"## {heading}\n\n{section_text.get(heading, 'Text.')}"
        for heading in REQUIRED_SECTIONS
    )
    report = repo / "docs/reports/example-report.md"
    report.write_text(
        "# Example\n\n"
        "Report ID: `example`\nStatus: `ACCEPTED`\nDate: 2026-07-14\nRevision: 1\n"
        "Authors: Test\nEvidence mode: Mixed\nExperiment record: [evidence](../../evidence/result.txt)\n"
        "Evidence snapshot: manifest.json\nReview record: [review](../../review/review.md)\n\n"
        f"{body}\n",
        encoding="utf-8",
    )
    (repo / "docs/reports/README.md").write_text(
        "| Report | Status |\n|---|---|\n| [Report](example-report.md) | ACCEPTED |\n",
        encoding="utf-8",
    )
    manifest = {
        "report_manifest_version": 1,
        "report_id": "example",
        "report_revision": 1,
        "status": "ACCEPTED",
        "report": {"path": "docs/reports/example-report.md", "sha256": sha256(report)},
        "governance": [
            {"role": role, "path": "evidence/result.txt", "sha256": sha256(evidence)}
            for role in ("standard", "protocol", "template")
        ],
        "required_sections": REQUIRED_SECTIONS,
        "study_facts": {"answer": 42},
        "hypotheses": [{"id": "H1", "provenance": "preregistered", "outcome": "Not supported", "evidence_ids": ["E01"]}],
        "evidence": [{"id": "E01", "path": "evidence/result.txt", "sha256": sha256(evidence), "role": "result"}],
        "references": [{"id": "R01", "citation": "Example", "doi_or_no_doi": "10.1/example", "url": "https://doi.org/10.1/example"}],
        "reviews": [
            {
                "lens": lens,
                "path": "review/review.md",
                "sha256": sha256(review),
                "verdict": "ACCEPT",
            }
            for lens in ("accuracy", "scientific-validity", "consistency-public-safety")
        ],
    }
    manifest_path = repo / "docs/reports/manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def self_test() -> None:
    with tempfile.TemporaryDirectory() as directory:
        repo = Path(directory)
        manifest_path = write_self_test_fixture(repo)
        verify(repo, manifest_path)
        report = repo / "docs/reports/example-report.md"
        review = repo / "review/review.md"
        clean_manifest = manifest_path.read_text(encoding="utf-8")
        clean_report = report.read_text(encoding="utf-8")
        clean_review = review.read_text(encoding="utf-8")

        def expect_failure(label: str) -> None:
            try:
                verify(repo, manifest_path)
            except VerificationError:
                return
            raise AssertionError(f"{label} mutation was accepted")

        manifest_path.write_text(
            clean_manifest.replace(
                '"report_id": "example"',
                '"report_id": "example",\n  "report_id": "duplicate"',
            ),
            encoding="utf-8",
        )
        expect_failure("duplicate-key")
        manifest_path.write_text(clean_manifest, encoding="utf-8")

        manifest_path.write_text(
            clean_manifest.replace('"answer": 42', '"answer": NaN'),
            encoding="utf-8",
        )
        expect_failure("nonfinite")
        manifest_path.write_text(clean_manifest, encoding="utf-8")

        manifest = read_json(manifest_path)
        manifest["study_facts"]["answer"] = 43
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        expect_failure("contradictory-study-fact")
        manifest_path.write_text(clean_manifest, encoding="utf-8")

        for label, mutated_report in (
            ("missing-section", clean_report.replace("## Results", "## Result")),
            ("invalid-evidence-mode", clean_report.replace("Evidence mode: Mixed", "Evidence mode: Banana")),
            ("second-h1", f"# Extra\n\n{clean_report}"),
            ("body-citation", clean_report.replace("Claim [E01] [R01].", "Claim [E01].")),
        ):
            report.write_text(mutated_report, encoding="utf-8")
            manifest = read_json(manifest_path)
            manifest["report"]["sha256"] = sha256(report)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            expect_failure(label)
            report.write_text(clean_report, encoding="utf-8")
            manifest_path.write_text(clean_manifest, encoding="utf-8")

        manifest = read_json(manifest_path)
        manifest["hypotheses"][0]["outcome"] = "Supported"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        expect_failure("hypothesis-outcome")
        manifest_path.write_text(clean_manifest, encoding="utf-8")

        manifest = read_json(manifest_path)
        manifest["report_revision"] = 2
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        expect_failure("report-revision")
        manifest_path.write_text(clean_manifest, encoding="utf-8")

        review.write_text(f"{clean_review}Open P2: 1\n", encoding="utf-8")
        manifest = read_json(manifest_path)
        for item in manifest["reviews"]:
            item["sha256"] = sha256(review)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        expect_failure("contradictory-review-count")
        review.write_text(clean_review, encoding="utf-8")
        manifest_path.write_text(clean_manifest, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--internal-review", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            print("PASS: report verifier self-test")
            return 0
        if args.manifest is None:
            parser.error("manifest is required unless --self-test is used")
        repo = Path(__file__).resolve().parents[2]
        manifest_path = args.manifest if args.manifest.is_absolute() else repo / args.manifest
        verify(repo, manifest_path, internal_review=args.internal_review)
        print(f"PASS: {manifest_path.relative_to(repo)}")
        return 0
    except VerificationError as error:
        print(f"FAIL: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
