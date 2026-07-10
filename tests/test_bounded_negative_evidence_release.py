from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.bounded_negative_evidence import (
    BoundedNegativeEvidenceReleaseError,
    BoundedNegativeEvidenceReleaseSummary,
    build_release_payloads,
    build_release_summary,
    check_committed_release_pack,
    write_release_pack,
)
from specsafe.bounded_negative_evidence.builder import (
    CLOSEOUT_DECISION_RELATIVE_PATH,
    EXPECTED_CLOSEOUT_DECISION_SHA256,
    EXPECTED_RELEASE_FILENAMES,
    EXPECTED_REPLAY_REPORT_SHA256,
    RELEASE_RELATIVE_DIRECTORY,
    REPLAY_REPORT_RELATIVE_PATH,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT = PROJECT_ROOT / RELEASE_RELATIVE_DIRECTORY


def test_release_summary_rebuild_is_byte_deterministic() -> None:
    payloads = build_release_payloads(PROJECT_ROOT)
    assert (
        payloads["release_summary.json"]
        == (RELEASE_ROOT / "release_summary.json").read_bytes()
    )
    assert payloads["README.md"] == (RELEASE_ROOT / "README.md").read_bytes()
    assert (
        payloads["evidence_boundary.md"]
        == (RELEASE_ROOT / "evidence_boundary.md").read_bytes()
    )
    assert (
        payloads["release_manifest.json"]
        == (RELEASE_ROOT / "release_manifest.json").read_bytes()
    )


def test_release_summary_retains_negative_result_and_blocks_promotion() -> None:
    summary = build_release_summary(PROJECT_ROOT)
    assert summary.validity_marker == "CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"
    assert summary.decision_outcome == "KEEP_DIAGNOSTIC_ONLY"
    assert summary.promotion_attempt_status == "closed_not_promoted"
    assert summary.failure_labels == ("ranking_safety_regression",)
    assert summary.candidate_not_promoted is True
    assert summary.threshold_promotion_authorized is False
    assert summary.scheduler_promotion_authorized is False
    assert summary.production_claim_authorized is False
    assert summary.automated_scheduling_confidence_status == (
        "unfit_use_conservative_fallback"
    )


def test_release_summary_retains_exact_source_and_metric_evidence() -> None:
    summary = build_release_summary(PROJECT_ROOT)
    assert summary.source_replay_report.sha256 == EXPECTED_REPLAY_REPORT_SHA256
    assert summary.source_closeout_decision.sha256 == EXPECTED_CLOSEOUT_DECISION_SHA256
    assert summary.holdout_record_count == 192
    assert summary.holdout_positive_count == 136
    assert summary.holdout_negative_count == 56
    assert summary.metrics.brier_improvement == pytest.approx(0.03811936896716564)
    assert summary.metrics.fixed_bin_ece_improvement == pytest.approx(
        0.10713044469407718
    )
    assert summary.metrics.auroc_delta == pytest.approx(-0.024356617647058765)
    assert summary.metrics.maximum_allowed_auroc_degradation == pytest.approx(0.001)


def test_release_manifest_matches_exact_allowlisted_files() -> None:
    payloads = build_release_payloads(PROJECT_ROOT)
    manifest = json.loads(payloads["release_manifest.json"])
    assert set(payloads) == EXPECTED_RELEASE_FILENAMES
    assert manifest["manifest_scope"] == "all_release_files_except_manifest_itself"
    assert manifest["file_count"] == 3
    assert [entry["relative_path"] for entry in manifest["entries"]] == [
        "README.md",
        "evidence_boundary.md",
        "release_summary.json",
    ]
    for entry in manifest["entries"]:
        payload = payloads[entry["relative_path"]]
        assert entry["byte_count"] == len(payload)
        assert entry["sha256"] == hashlib.sha256(payload).hexdigest()


def test_release_pack_is_sanitized_and_contains_no_nested_assets() -> None:
    check_committed_release_pack(PROJECT_ROOT)
    assert {path.name for path in RELEASE_ROOT.iterdir()} == EXPECTED_RELEASE_FILENAMES
    assert all(
        path.is_file() and not path.is_symlink() for path in RELEASE_ROOT.iterdir()
    )
    combined = b"\n".join(path.read_bytes().lower() for path in RELEASE_ROOT.iterdir())
    for marker in (
        b'"prompt_text"',
        b'"raw_prompt_text"',
        b".jsonl",
        b".zip",
        b"api_key",
        b"access_token",
        b"hf_token",
        b"raw_logits",
        b"authorization: bearer",
        b"/home/",
        b"/users/",
    ):
        assert marker not in combined


def test_release_summary_contract_rejects_positive_promotion_state() -> None:
    summary = build_release_summary(PROJECT_ROOT)
    payload = summary.model_dump(mode="json")
    payload["candidate_not_promoted"] = False
    with pytest.raises(ValidationError):
        BoundedNegativeEvidenceReleaseSummary.model_validate(payload)


def test_builder_fails_closed_when_closeout_source_changes(tmp_path: Path) -> None:
    project = _copy_minimum_source_project(tmp_path)
    target = project / CLOSEOUT_DECISION_RELATIVE_PATH
    value = json.loads(target.read_text(encoding="utf-8"))
    value["decision_outcome"] = "PROMOTE_CANDIDATE_CALIBRATOR"
    target.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    with pytest.raises(BoundedNegativeEvidenceReleaseError, match="SHA-256 mismatch"):
        build_release_summary(project)


def test_builder_rejects_output_outside_repository(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        "[project]\nname='specsafe'\n", encoding="utf-8"
    )
    outside = tmp_path / "outside-release"
    with pytest.raises(
        BoundedNegativeEvidenceReleaseError, match="inside the repository"
    ):
        write_release_pack(project, output_directory=outside)


def _copy_minimum_source_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        "[project]\nname='specsafe'\n", encoding="utf-8"
    )
    for relative_path in (REPLAY_REPORT_RELATIVE_PATH, CLOSEOUT_DECISION_RELATIVE_PATH):
        source = PROJECT_ROOT / relative_path
        target = project / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return project
