import hashlib
import json
from pathlib import Path

import pytest

from specsafe.kaggle_trace_calibration.fit_combined_calibrator import (
    CALIBRATOR_FIT_REPORT_PATH,
    CALIBRATOR_MODEL_PATH,
    DIAGNOSTIC_REPORT_PATH,
    MODEL_ID,
    build_combined_calibrator_fit,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(payload: dict) -> str:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def test_combined_diagnostic_authorized_only_fit_attempt() -> None:
    diagnostic = _read_json(REPO_ROOT / DIAGNOSTIC_REPORT_PATH)
    readiness = diagnostic["calibration_fit_readiness"]

    assert readiness["calibration_fit_authorized"] is True
    assert readiness["calibration_fit_readiness_status"] == (
        "sample_and_signal_ready_for_calibration_fit"
    )
    assert readiness["next_authorized_step"] == (
        "fit_kaggle_derived_calibrator_under_separate_gate"
    )


def test_fit_report_regenerates_deterministically() -> None:
    regenerated = build_combined_calibrator_fit(root=REPO_ROOT, write_outputs=False)
    retained_report = _read_json(REPO_ROOT / CALIBRATOR_FIT_REPORT_PATH)

    assert regenerated["calibrator_fit_report"] == retained_report


def test_calibrator_model_regenerates_deterministically() -> None:
    regenerated = build_combined_calibrator_fit(root=REPO_ROOT, write_outputs=False)
    retained_model = _read_json(REPO_ROOT / CALIBRATOR_MODEL_PATH)

    assert regenerated["calibrator_model"] == retained_model


def test_model_hash_matches_fit_report() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_FIT_REPORT_PATH)
    model = _read_json(REPO_ROOT / CALIBRATOR_MODEL_PATH)

    assert model["model_id"] == MODEL_ID
    assert report["calibrator_model_sha256"] == _sha256_json(model)


def test_fit_counts_match_combined_evidence_pool() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_FIT_REPORT_PATH)
    model = _read_json(REPO_ROOT / CALIBRATOR_MODEL_PATH)

    assert report["fit_record_count"] == 184
    assert report["fit_positive_count"] == 148
    assert report["fit_negative_count"] == 36
    assert model["fit_record_count"] == 184
    assert model["fit_positive_count"] == 148
    assert model["fit_negative_count"] == 36


def test_source_archive_summaries_preserved() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_FIT_REPORT_PATH)
    summaries = report["source_archive_summaries"]

    v2_summary = summaries["v5-qwen-governed-trace-collection-v2/attempt-001-t4"]
    negative_summary = summaries["v5-qwen-negative-case-expansion-v1/attempt-001-t4"]

    assert v2_summary["record_count"] == 120
    assert v2_summary["match_count"] == 97
    assert v2_summary["nonmatch_count"] == 23
    assert negative_summary["record_count"] == 64
    assert negative_summary["match_count"] == 51
    assert negative_summary["nonmatch_count"] == 13


def test_calibrator_blocks_are_monotonic_and_cover_observed_bins() -> None:
    model = _read_json(REPO_ROOT / CALIBRATOR_MODEL_PATH)
    blocks = model["calibrator_blocks"]

    assert len(blocks) == 6
    assert blocks[0]["lower_bound"] == 0.0
    assert blocks[-1]["upper_bound"] > 1.0
    assert sum(block["record_count"] for block in blocks) == 184

    probabilities = [block["calibrated_probability"] for block in blocks]
    assert probabilities == sorted(probabilities)
    assert all(0.0 <= probability <= 1.0 for probability in probabilities)


def test_non_monotonic_fixed_bins_are_pooled() -> None:
    model = _read_json(REPO_ROOT / CALIBRATOR_MODEL_PATH)
    pooled_blocks = [
        block for block in model["calibrator_blocks"] if len(block["source_bin_indexes"]) > 1
    ]

    assert pooled_blocks == [
        {
            "lower_bound": 0.2,
            "upper_bound": 0.4,
            "record_count": 45,
            "match_count": 31,
            "nonmatch_count": 14,
            "calibrated_probability": pytest.approx(0.6808510638297872),
            "source_bin_indexes": [1, 2],
        }
    ]


def test_in_sample_diagnostics_improve_but_do_not_promote() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_FIT_REPORT_PATH)

    assert report["calibrated_brier_in_sample_diagnostic"] < report["raw_brier_diagnostic"]
    assert (
        report["calibrated_fixed_bin_ece_in_sample_diagnostic"]
        < (report["raw_fixed_bin_ece_diagnostic"])
    )
    assert report["in_sample_brier_delta"] > 0
    assert report["in_sample_ece_delta"] > 0

    assert report["calibrator_fit_status"] == "fit_retained"
    assert report["calibrator_promotion_status"] == "not_authorized"
    assert report["threshold_promotion_status"] == "not_authorized"
    assert report["scheduler_promotion_status"] == "not_authorized"
    assert report["public_release_status"] == "not_authorized"
    assert report["production_claim_status"] == "not_authorized"


def test_model_boundary_blocks_promotion_claims() -> None:
    model = _read_json(REPO_ROOT / CALIBRATOR_MODEL_PATH)

    assert model["calibrator_fit_status"] == "fit_retained"
    assert model["calibrator_promotion_status"] == "not_authorized"
    assert model["threshold_promotion_status"] == "not_authorized"
    assert model["scheduler_promotion_status"] == "not_authorized"
    assert model["public_release_status"] == "not_authorized"
    assert model["production_claim_status"] == "not_authorized"
    assert model["missing_or_out_of_range_input_policy"] == "fail_closed"


def test_fixed_bin_summaries_preserve_negative_coverage() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_FIT_REPORT_PATH)
    fixed_bins = report["fixed_bin_summaries"]

    assert len(fixed_bins) == 7
    assert sum(bin_summary["record_count"] for bin_summary in fixed_bins) == 184
    assert sum(bin_summary["nonmatch_count"] for bin_summary in fixed_bins) == 36
    assert fixed_bins[0]["nonmatch_count"] == 20
    assert fixed_bins[1]["nonmatch_count"] == 4
    assert fixed_bins[2]["nonmatch_count"] == 10
    assert fixed_bins[3]["nonmatch_count"] == 2


def test_report_points_to_retained_combined_diagnostic() -> None:
    report = _read_json(REPO_ROOT / CALIBRATOR_FIT_REPORT_PATH)

    assert report["source_combined_diagnostic_report"] == (
        "evidence/kaggle-trace-calibration/v5-qwen-combined-v2-negative-case/"
        "combined_calibration_diagnostic_report.json"
    )
    assert report["source_combined_diagnostic_sha256"]
