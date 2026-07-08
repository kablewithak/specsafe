from __future__ import annotations

import hashlib
import json
from pathlib import Path

from specsafe.kaggle_trace_replay import build_trace_replay_report, write_trace_replay_report
from specsafe.kaggle_trace_replay.models import KaggleTraceReplayReport

ARCHIVE_PATH = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-governed-trace-collection-v1/"
    "attempt-001-t4/"
    "specsafe_v5_qwen_trace_collection_v1_attempt_001.zip"
)
TRACE_ANALYSIS_REPORT_PATH = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-governed-trace-collection-v1/"
    "attempt-001-t4/"
    "trace_analysis_report.json"
)
TRACE_REPLAY_REPORT_PATH = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-governed-trace-collection-v1/"
    "attempt-001-t4/"
    "trace_replay_report.json"
)
EXPECTED_TRACE_REPLAY_REPORT_SHA256 = (
    "f536120982a616bbae9daf5d9b946469e70348dc52dd5d23af430bd9a5a5ba0f"
)
EXPECTED_TRACE_ANALYSIS_REPORT_SHA256 = (
    "1d31f0f0e2ae3e825878289780c4754185d2bd936c4f31eb3de4feda3a385885"
)
EXPECTED_ARCHIVE_SHA256 = "03059b5ed15fdde07faff92cb9485cb89793e03e010fd8f43b8f674d17fdb81c"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_retained_trace_replay_report_is_valid_and_hash_locked() -> None:
    report = KaggleTraceReplayReport.model_validate_json(
        TRACE_REPLAY_REPORT_PATH.read_text(encoding="utf-8")
    )

    assert sha256_file(TRACE_REPLAY_REPORT_PATH) == EXPECTED_TRACE_REPLAY_REPORT_SHA256
    assert report.archive_sha256 == EXPECTED_ARCHIVE_SHA256
    assert report.trace_analysis_report_sha256 == EXPECTED_TRACE_ANALYSIS_REPORT_SHA256
    assert report.runtime_record_count == 24
    assert report.target_argmax_match_count == 15
    assert report.target_argmax_nonmatch_count == 9
    assert report.replay_gate_status == "passes_diagnostic_trace_replay_gate"


def test_trace_replay_report_regenerates_deterministically(tmp_path: Path) -> None:
    report = build_trace_replay_report(
        archive_path=ARCHIVE_PATH,
        trace_analysis_report_path=TRACE_ANALYSIS_REPORT_PATH,
    )
    output_path = tmp_path / "trace_replay_report.json"

    write_trace_replay_report(report, output_path)

    assert output_path.read_bytes() == TRACE_REPLAY_REPORT_PATH.read_bytes()


def test_threshold_replay_captures_confidence_tradeoff() -> None:
    report = KaggleTraceReplayReport.model_validate_json(
        TRACE_REPLAY_REPORT_PATH.read_text(encoding="utf-8")
    )
    by_threshold = {item.raw_draft_probability_threshold: item for item in report.threshold_replay}

    assert by_threshold[0.0].selected_record_count == 24
    assert by_threshold[0.0].selected_nonmatch_count == 9
    assert by_threshold[0.5].selected_record_count == 13
    assert by_threshold[0.5].selected_nonmatch_count == 1
    assert by_threshold[0.5].selected_match_rate == 12 / 13
    assert by_threshold[0.6].selected_record_count == 9
    assert by_threshold[0.6].selected_nonmatch_count == 0
    assert by_threshold[0.6].selected_match_rate == 1.0
    assert report.high_confidence_zero_mismatch_thresholds == (0.6, 0.7, 0.8, 0.9)


def test_utility_proxy_is_penalty_sensitive_without_selecting_policy() -> None:
    report = KaggleTraceReplayReport.model_validate_json(
        TRACE_REPLAY_REPORT_PATH.read_text(encoding="utf-8")
    )
    by_threshold = {item.raw_draft_probability_threshold: item for item in report.threshold_replay}

    threshold_03_utilities = {
        item.mismatch_penalty: item.diagnostic_utility_units
        for item in by_threshold[0.3].utility_diagnostics
    }
    threshold_06_utilities = {
        item.mismatch_penalty: item.diagnostic_utility_units
        for item in by_threshold[0.6].utility_diagnostics
    }

    assert threshold_03_utilities == {1.0: 13.0, 2.0: 10.0, 4.0: 4.0, 8.0: -8.0}
    assert threshold_06_utilities == {1.0: 9.0, 2.0: 9.0, 4.0: 9.0, 8.0: 9.0}
    assert report.interpretation_boundary.threshold_policy_selected is False
    assert report.interpretation_boundary.policy_utility_promotion_authorized is False


def test_trace_replay_report_contains_no_runtime_forbidden_payloads() -> None:
    payload = json.loads(TRACE_REPLAY_REPORT_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(payload, sort_keys=True)

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
        assert marker not in serialized.lower()
