"""Regression coverage for the V5 governed controlled-comparison execution boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsafe.eval_harness import (
    DEFAULT_GOVERNED_MATCHED_POLICY_COMPARISON_PROTOCOL,
    GovernedMatchedPolicyComparisonError,
    GovernedMatchedPolicyComparisonErrorCode,
    GovernedMatchedPolicyComparisonResult,
    build_governed_matched_policy_comparison_result,
    canonical_governed_matched_policy_comparison_json,
    default_governed_comparison_result_path,
    run_governed_matched_policy_comparison_once,
)
from specsafe.eval_harness.comparison_models import MatchedPolicyComparisonOutcome

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_RESULT_PATH = (
    _PROJECT_ROOT
    / "evidence"
    / "matched-policy-comparison"
    / "v5-controlled-synthetic-comparison-v1"
    / "result.json"
)


def test_governed_runner_retains_complete_case_level_results_without_promotion() -> None:
    result = build_governed_matched_policy_comparison_result(_PROJECT_ROOT)

    assert result.protocol is DEFAULT_GOVERNED_MATCHED_POLICY_COMPARISON_PROTOCOL
    assert result.case_count == 6
    assert result.valid_matched_comparison_count == 6
    assert result.unsafe_control_exclusion_count == 6
    assert tuple(case.case_id for case in result.case_results) == (
        "MPC5-101",
        "MPC5-102",
        "MPC5-103",
        "MPC5-104",
        "MPC5-105",
        "MPC5-106",
    )
    assert result.execution_status == "retained_controlled_synthetic_case_level_results"
    assert result.claim_status == "no_global_winner_or_runtime_promotion_claim"
    assert result.calibration_refit_performed is False
    assert result.final_evaluation_accessed is False
    assert result.runtime_control_eligible is False
    assert result.promotion_eligible is False
    unsafe_control_statuses = {
        case.unsafe_retrospective_control.replay_result.causal_safety_status.value
        for case in result.case_results
    }
    assert unsafe_control_statuses == {"fail"}

    fixed_counts = {
        item.outcome: item.case_count for item in result.adaptive_vs_fixed_length_outcome_counts
    }
    threshold_counts = {
        item.outcome: item.case_count for item in result.adaptive_vs_static_threshold_outcome_counts
    }
    assert sum(fixed_counts.values()) == result.case_count
    assert sum(threshold_counts.values()) == result.case_count
    assert fixed_counts[MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY] >= 1
    assert fixed_counts[MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL] >= 1
    assert fixed_counts[MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY] >= 1


def test_committed_result_is_canonical_and_matches_current_governed_execution() -> None:
    committed = GovernedMatchedPolicyComparisonResult.model_validate_json(
        _RESULT_PATH.read_text(encoding="utf-8")
    )
    rebuilt = build_governed_matched_policy_comparison_result(_PROJECT_ROOT)

    assert canonical_governed_matched_policy_comparison_json(committed) == _RESULT_PATH.read_text(
        encoding="utf-8"
    )
    assert committed == rebuilt
    assert default_governed_comparison_result_path(_PROJECT_ROOT) == _RESULT_PATH


def test_governed_runner_is_write_once() -> None:
    destination = _PROJECT_ROOT / ".pytest-governed-comparison-result.json"
    destination.unlink(missing_ok=True)
    try:
        result, persisted = run_governed_matched_policy_comparison_once(_PROJECT_ROOT, destination)

        assert persisted == destination.resolve()
        assert destination.is_file()
        assert (
            GovernedMatchedPolicyComparisonResult.model_validate_json(
                destination.read_text(encoding="utf-8")
            )
            == result
        )

        with pytest.raises(GovernedMatchedPolicyComparisonError) as error_info:
            run_governed_matched_policy_comparison_once(_PROJECT_ROOT, destination)

        assert (
            error_info.value.code
            is GovernedMatchedPolicyComparisonErrorCode.DESTINATION_ALREADY_EXISTS
        )
    finally:
        destination.unlink(missing_ok=True)


def test_governed_runner_rejects_destination_outside_project_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(GovernedMatchedPolicyComparisonError) as error_info:
        run_governed_matched_policy_comparison_once(_PROJECT_ROOT, tmp_path / "outside.json")

    assert error_info.value.code is GovernedMatchedPolicyComparisonErrorCode.INVALID_DESTINATION
