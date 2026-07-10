import json
from pathlib import Path

from specsafe.kaggle_trace_calibration.replay_combined_calibrator import (
    CALIBRATOR_MODEL_PATH,
    CALIBRATOR_REPLAY_REPORT_PATH,
    MODEL_ID,
    build_combined_calibrator_replay,
    sha256_json,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_replay_report_regenerates_deterministically() -> None:
    regenerated = build_combined_calibrator_replay(root=REPO_ROOT, write_outputs=False)
    retained = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)

    assert regenerated == retained


def test_replay_uses_retained_candidate_model_hash() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)
    model = _read_json(REPO_ROOT / CALIBRATOR_MODEL_PATH)

    assert model["model_id"] == MODEL_ID
    assert report["calibrator_model_id"] == MODEL_ID
    assert report["calibrator_model_sha256"] == sha256_json(model)


def test_fit_pool_counts_are_preserved() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)

    assert report["fit_pool_replay_record_count"] == 184
    assert report["fit_pool_replay_positive_count"] == 148
    assert report["fit_pool_replay_negative_count"] == 36


def test_fit_pool_replay_improves_brier_but_does_not_authorize_promotion() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)

    assert report["raw_brier_diagnostic"] == 0.2315717785677341
    assert report["calibrated_brier_fit_pool_replay_diagnostic"] == 0.11977357092886388
    assert report["fit_pool_brier_delta"] == 0.1117982076388702
    assert report["calibrator_replay_status"] == "fit_pool_replay_passed"
    assert report["holdout_status"] == "not_available_fit_pool_replay_only"
    assert report["calibrator_promotion_status"] == "not_authorized_no_holdout"


def test_source_stratified_replay_keeps_both_archives_visible() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)
    summaries = report["source_archive_replay_summaries"]

    v2 = summaries["v5-qwen-governed-trace-collection-v2/attempt-001-t4"]
    negative_case = summaries["v5-qwen-negative-case-expansion-v1/attempt-001-t4"]

    assert v2["record_count"] == 120
    assert v2["match_count"] == 97
    assert v2["nonmatch_count"] == 23
    assert v2["calibrated_brier_fit_pool_replay_diagnostic"] < v2["raw_brier_diagnostic"]

    assert negative_case["record_count"] == 64
    assert negative_case["match_count"] == 51
    assert negative_case["nonmatch_count"] == 13
    assert (
        negative_case["calibrated_brier_fit_pool_replay_diagnostic"]
        < negative_case["raw_brier_diagnostic"]
    )


def test_calibrated_block_replay_matches_model_blocks() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)
    blocks = report["calibrated_block_replay"]

    assert len(blocks) == 6
    assert blocks[0]["record_count"] == 42
    assert blocks[0]["match_count"] == 22
    assert blocks[0]["nonmatch_count"] == 20
    assert blocks[0]["calibrated_probability"] == 0.5227272727272727
    assert blocks[-1]["record_count"] == 45
    assert blocks[-1]["match_count"] == 45
    assert blocks[-1]["nonmatch_count"] == 0
    assert blocks[-1]["calibrated_probability"] == 0.9787234042553191


def test_calibrated_threshold_replay_is_monotonic() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)
    thresholds = report["calibrated_threshold_replay"]
    selected_counts = [item["selected_count"] for item in thresholds]
    selected_nonmatches = [item["selected_nonmatch_count"] for item in thresholds]

    assert selected_counts == sorted(selected_counts, reverse=True)
    assert selected_nonmatches == sorted(selected_nonmatches, reverse=True)


def test_calibrated_threshold_replay_counts_are_retained() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)
    by_threshold = {item["threshold"]: item for item in report["calibrated_threshold_replay"]}

    assert by_threshold[0.5]["selected_count"] == 184
    assert by_threshold[0.5]["selected_nonmatch_count"] == 36
    assert by_threshold[0.6]["selected_count"] == 142
    assert by_threshold[0.6]["selected_nonmatch_count"] == 16
    assert by_threshold[0.7]["selected_count"] == 97
    assert by_threshold[0.7]["selected_nonmatch_count"] == 2
    assert by_threshold[0.9]["selected_count"] == 74
    assert by_threshold[0.9]["selected_nonmatch_count"] == 0


def test_split_and_workload_counts_are_preserved() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)

    assert report["split_counts"] == {
        "adversarial_regression": 12,
        "calibration": 36,
        "development": 36,
        "final_evaluation": 36,
        "negative_probe_calibration_candidate": 32,
        "negative_probe_holdout": 32,
    }
    assert report["workload_counts"] == {
        "code": 64,
        "open_ended_chat": 64,
        "structured_text": 56,
    }


def test_non_claim_boundaries_remain_blocked() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_REPLAY_REPORT_PATH)

    assert report["threshold_promotion_status"] == "not_authorized"
    assert report["scheduler_promotion_status"] == "not_authorized"
    assert report["public_release_status"] == "not_authorized"
    assert report["production_claim_status"] == "not_authorized"
    assert "does_not_promote_calibrator" in report["non_claims"]
    assert "does_not_claim_production_speedup_or_readiness" in report["non_claims"]
