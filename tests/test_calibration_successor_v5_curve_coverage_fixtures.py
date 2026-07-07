"""Diagnostic tests for V5 calibration curve-coverage fixtures."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from specsafe.traces.calibration_successor_v5_cases import (
    load_calibration_successor_v5_curve_coverage_replay_case,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_successor_v5"
)
_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(101, 113))


def test_curve_coverage_has_48_observations_across_all_probability_deciles() -> None:
    confidences = [
        context.conditional_survival_confidence
        for case_id in _CASE_IDS
        for context in load_calibration_successor_v5_curve_coverage_replay_case(
            _FIXTURE_ROOT, case_id
        ).runtime_input.contexts
    ]

    assert len(confidences) == 48
    assert {min(int(confidence * 10), 9) for confidence in confidences} == set(range(10))
    assert min(confidences) <= 0.05
    assert max(confidences) >= 0.95


def test_curve_coverage_balances_workloads_and_retains_both_outcome_classes() -> None:
    replay_cases = tuple(
        load_calibration_successor_v5_curve_coverage_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _CASE_IDS
    )
    workload_counts = Counter(
        case.runtime_input.contexts[0].workload_type.value for case in replay_cases
    )
    observed_acceptance = [
        outcome.observed_acceptance
        for case in replay_cases
        for outcome in case.expected_outcomes.outcomes
    ]

    assert workload_counts == {"structured_text": 4, "code": 4, "open_ended_chat": 4}
    assert any(observed_acceptance)
    assert not all(observed_acceptance)


def test_curve_coverage_retains_final_and_adversarial_quarantine() -> None:
    assert not (_FIXTURE_ROOT / "final_evaluation").exists()
    assert not (_FIXTURE_ROOT / "adversarial_regression").exists()
    assert (_FIXTURE_ROOT / "calibration_manifest.json").is_file()
