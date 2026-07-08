"""Regression tests for retained Kaggle trace calibration diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

from specsafe.kaggle_trace_calibration import (
    KaggleTraceCalibrationDiagnosticReport,
    build_trace_calibration_diagnostic_report,
    sha256_file,
    write_trace_calibration_diagnostic_report,
)

ATTEMPT_DIR = Path(
    "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v1/attempt-001-t4"
)
ARCHIVE_PATH = ATTEMPT_DIR / "specsafe_v5_qwen_trace_collection_v1_attempt_001.zip"
TRACE_ANALYSIS_REPORT_PATH = ATTEMPT_DIR / "trace_analysis_report.json"
TRACE_REPLAY_REPORT_PATH = ATTEMPT_DIR / "trace_replay_report.json"
CALIBRATION_REPORT_PATH = ATTEMPT_DIR / "trace_calibration_diagnostic_report.json"


def test_retained_calibration_diagnostic_report_is_valid() -> None:
    report = KaggleTraceCalibrationDiagnosticReport.model_validate_json(
        CALIBRATION_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert report.archive_sha256 == sha256_file(ARCHIVE_PATH)
    assert report.trace_analysis_report_sha256 == sha256_file(TRACE_ANALYSIS_REPORT_PATH)
    assert report.trace_replay_report_sha256 == sha256_file(TRACE_REPLAY_REPORT_PATH)
    assert report.runtime_record_count == 24
    assert report.target_argmax_match_count == 15
    assert report.target_argmax_nonmatch_count == 9
    assert report.readiness_gate.signal_diagnostic_passed is True
    assert (
        report.readiness_gate.calibration_fit_readiness_status
        == "insufficient_sample_for_calibration_fit_signal_supportive"
    )


def test_calibration_report_regenerates_deterministically(tmp_path: Path) -> None:
    report = build_trace_calibration_diagnostic_report(
        archive_path=ARCHIVE_PATH,
        trace_analysis_report_path=TRACE_ANALYSIS_REPORT_PATH,
        trace_replay_report_path=TRACE_REPLAY_REPORT_PATH,
    )
    regenerated_path = tmp_path / "trace_calibration_diagnostic_report.json"
    write_trace_calibration_diagnostic_report(report, regenerated_path)

    assert json.loads(regenerated_path.read_text(encoding="utf-8")) == json.loads(
        CALIBRATION_REPORT_PATH.read_text(encoding="utf-8")
    )


def test_fixed_bin_calibration_diagnostics_are_expected() -> None:
    report = KaggleTraceCalibrationDiagnosticReport.model_validate_json(
        CALIBRATION_REPORT_PATH.read_text(encoding="utf-8")
    )
    bins = {item.bin_id: item for item in report.fixed_probability_bins}

    assert report.raw_draft_probability_brier_diagnostic == 0.13062574344890066
    assert report.fixed_bin_expected_calibration_error == 0.11310045979917047
    assert report.fixed_bin_maximum_calibration_error == 0.2314736247062683

    assert bins["raw_prob_0.0_0.2"].record_count == 4
    assert bins["raw_prob_0.0_0.2"].match_count == 1
    assert bins["raw_prob_0.2_0.4"].record_count == 5
    assert bins["raw_prob_0.2_0.4"].match_count == 1
    assert bins["raw_prob_0.4_0.6"].record_count == 6
    assert bins["raw_prob_0.4_0.6"].match_count == 4
    assert bins["raw_prob_0.6_0.8"].record_count == 1
    assert bins["raw_prob_0.6_0.8"].match_count == 1
    assert bins["raw_prob_0.8_1.0"].record_count == 8
    assert bins["raw_prob_0.8_1.0"].match_count == 8


def test_calibration_boundary_blocks_overclaims() -> None:
    report = KaggleTraceCalibrationDiagnosticReport.model_validate_json(
        CALIBRATION_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert report.interpretation_boundary.calibration_fit_performed is False
    assert report.interpretation_boundary.calibration_model_retained is False
    assert report.interpretation_boundary.threshold_policy_selected is False
    assert report.interpretation_boundary.policy_utility_promotion_authorized is False
    assert report.interpretation_boundary.public_dataset_release_authorized is False
    assert report.interpretation_boundary.production_readiness_claimed is False


def test_calibration_report_contains_no_forbidden_payloads() -> None:
    payload = json.loads(CALIBRATION_REPORT_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True).lower()

    forbidden_markers = (
        "prompt_text",
        "decoded_candidate",
        "raw_logits",
        "private_data",
        "secret",
        "api_key",
        "hf_token",
    )
    for marker in forbidden_markers:
        assert marker not in serialized
