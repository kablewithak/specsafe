from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ARCHIVE_DIR = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/"
    "attempt-001-t4"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _jsonl_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())


def test_independent_holdout_archive_retention_report_matches_files() -> None:
    report_path = ARCHIVE_DIR / "archive_retention_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["collection_id"] == "v5-qwen-candidate-calibrator-independent-holdout-v1"
    assert report["attempt_id"] == "attempt-001-t4"
    assert report["data_role"] == "independent_holdout_trace_collection"
    assert report["runtime_record_count"] == 192
    assert report["expected_outcome_record_count"] == 192
    assert report["timing_record_count"] == 192
    assert report["target_argmax_match_count"] == 136
    assert report["target_argmax_nonmatch_count"] == 56
    assert report["raw_prompt_text_retained"] is False

    archive_path = ARCHIVE_DIR / report["archive_filename"]
    assert archive_path.exists()
    assert _sha256(archive_path) == report["archive_sha256"]
    assert archive_path.stat().st_size == report["archive_byte_count"]

    for filename, expected in report["file_hashes"].items():
        path = ARCHIVE_DIR / filename
        assert path.exists(), filename
        assert _sha256(path) == expected["sha256"]
        assert path.stat().st_size == expected["byte_count"]


def test_independent_holdout_archive_counts_are_consistent() -> None:
    summary = json.loads((ARCHIVE_DIR / "trace_summary.json").read_text(encoding="utf-8"))
    manifest = json.loads((ARCHIVE_DIR / "retention_manifest.json").read_text(encoding="utf-8"))

    assert _jsonl_count(ARCHIVE_DIR / "runtime_records.jsonl") == 192
    assert _jsonl_count(ARCHIVE_DIR / "expected_outcome_records.jsonl") == 192
    assert _jsonl_count(ARCHIVE_DIR / "timing_records.jsonl") == 192

    assert summary["runtime_record_count"] == manifest["runtime_record_count"] == 192
    assert summary["expected_outcome_record_count"] == 192
    assert manifest["expected_outcome_record_count"] == 192
    assert summary["planned_runtime_records"] == 192
    assert summary["case_count"] == manifest["case_count"] == 48


def test_independent_holdout_archive_preserves_non_promotion_boundary() -> None:
    report = json.loads((ARCHIVE_DIR / "archive_retention_report.json").read_text(encoding="utf-8"))

    assert report["calibration_fit_status"] == "not_authorized"
    assert (
        report["calibrator_promotion_status"] == "not_authorized_pending_independent_holdout_replay"
    )
    assert report["threshold_promotion_status"] == "not_authorized"
    assert report["scheduler_promotion_status"] == "not_authorized"
    assert report["production_claim_status"] == "not_authorized"

    forbidden = set(report["forbidden_downstream_actions"])
    assert "refit_candidate_calibrator_from_holdout_archive" in forbidden
    assert "tune_thresholds_from_holdout_archive" in forbidden
    assert "tune_scheduler_from_holdout_archive" in forbidden


def test_retained_raw_archive_contains_expected_files() -> None:
    archive_path = ARCHIVE_DIR / "specsafe_v5_qwen_candidate_calibrator_holdout_attempt_001_t4.zip"
    expected_names = {
        (ARCHIVE_DIR / "environment_report.json").as_posix(),
        (ARCHIVE_DIR / "expected_outcome_records.jsonl").as_posix(),
        (ARCHIVE_DIR / "retention_manifest.json").as_posix(),
        (ARCHIVE_DIR / "runtime_records.jsonl").as_posix(),
        (ARCHIVE_DIR / "timing_records.jsonl").as_posix(),
        (ARCHIVE_DIR / "trace_summary.json").as_posix(),
    }

    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == expected_names
