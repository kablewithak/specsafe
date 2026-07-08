from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from specsafe.kaggle_trace_analysis import (
    KaggleTraceAnalysisReport,
    analyze_trace_archive,
    join_trace_records,
    load_trace_archive,
)

ATTEMPT_DIR = Path(
    "evidence/kaggle-trace-collection/v5-qwen-governed-trace-collection-v1/attempt-001-t4"
)
ARCHIVE_PATH = ATTEMPT_DIR / "specsafe_v5_qwen_trace_collection_v1_attempt_001.zip"
REPORT_PATH = ATTEMPT_DIR / "trace_analysis_report.json"

EXPECTED_ARCHIVE_SHA256 = "03059b5ed15fdde07faff92cb9485cb89793e03e010fd8f43b8f674d17fdb81c"
EXPECTED_REPORT_SHA256 = "1d31f0f0e2ae3e825878289780c4754185d2bd936c4f31eb3de4feda3a385885"


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_trace_analysis_report_is_retained_and_valid() -> None:
    report = KaggleTraceAnalysisReport.model_validate_json(REPORT_PATH.read_text(encoding="utf-8"))

    assert sha256_text(REPORT_PATH) == EXPECTED_REPORT_SHA256
    assert report.schema_version == "specsafe-kaggle-trace-analysis-report-v1"
    assert report.archive_sha256 == EXPECTED_ARCHIVE_SHA256
    assert report.collection_id == "v5-qwen-governed-trace-collection-v1"
    assert report.collection_attempt_id == "attempt-001-t4"
    assert report.runtime_record_count == 24
    assert report.expected_outcome_record_count == 24
    assert report.target_argmax_match_count == 15
    assert report.target_argmax_nonmatch_count == 9
    assert report.target_argmax_match_rate == pytest.approx(0.625)


def test_trace_analysis_is_reproducible_from_archive() -> None:
    retained_report = KaggleTraceAnalysisReport.model_validate_json(
        REPORT_PATH.read_text(encoding="utf-8")
    )
    computed_report = analyze_trace_archive(ARCHIVE_PATH)

    assert computed_report == retained_report


def test_trace_analysis_validates_join_keys_and_record_counts() -> None:
    (
        archive_sha256,
        _payloads,
        manifest,
        _manifest_payload,
        runtime_records,
        expected_outcomes,
    ) = load_trace_archive(ARCHIVE_PATH)
    pairs = join_trace_records(runtime_records, expected_outcomes)

    assert archive_sha256 == EXPECTED_ARCHIVE_SHA256
    assert manifest.collection_id == "v5-qwen-governed-trace-collection-v1"
    assert manifest.collection_attempt_id == "attempt-001-t4"
    assert len(runtime_records) == len(expected_outcomes) == len(pairs) == 24
    assert {runtime.trace_id for runtime, _ in pairs} == {
        "KTC5-001-trace",
        "KTC5-002-trace",
        "KTC5-003-trace",
        "KTC5-004-trace",
        "KTC5-005-trace",
        "KTC5-006-trace",
    }


def test_trace_analysis_signal_diagnostics_are_directionally_supportive_only() -> None:
    report = analyze_trace_archive(ARCHIVE_PATH)

    signal = report.signal_diagnostics

    assert signal.raw_draft_probability_pairwise_separation_rate == pytest.approx(
        0.9037037037037037
    )
    assert signal.raw_draft_entropy_pairwise_lower_for_match_rate == pytest.approx(
        0.9111111111111111
    )
    assert signal.raw_draft_probability_brier_diagnostic == pytest.approx(0.13062574344890066)
    assert (
        signal.support_interpretation
        == "directionally_supportive_small_sample_not_calibration_claim"
    )


def test_trace_analysis_keeps_interpretation_boundary_closed() -> None:
    report_payload = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    boundary = report_payload["interpretation_boundary"]

    assert boundary == {
        "analysis_scope": "local_retained_archive_diagnostics",
        "calibration_fit_performed": False,
        "policy_threshold_selected": False,
        "policy_utility_evaluation_performed": False,
        "throughput_or_latency_measurement_performed": False,
        "public_dataset_release_authorized": False,
        "production_readiness_claimed": False,
    }


def test_threshold_sweep_does_not_select_policy_threshold() -> None:
    report = analyze_trace_archive(ARCHIVE_PATH)
    threshold_rows = {
        row.raw_draft_probability_threshold: row
        for row in report.raw_draft_probability_threshold_sensitivity
    }

    assert threshold_rows[0.5].selected_record_count == 13
    assert threshold_rows[0.5].selected_match_count == 12
    assert threshold_rows[0.5].selected_nonmatch_count == 1
    assert threshold_rows[0.5].selected_match_rate == pytest.approx(12 / 13)
    assert threshold_rows[0.7].selected_record_count == 9
    assert threshold_rows[0.7].selected_match_rate == pytest.approx(1.0)
    assert report.interpretation_boundary.policy_threshold_selected is False
