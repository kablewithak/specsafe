"""Diagnostic tests for V5 calibration mixed-reliability contrast fixtures."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from specsafe.traces.calibration_successor_v5_cases import (
    load_calibration_successor_v5_mixed_reliability_contrast_replay_case,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_successor_v5"
)
_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(137, 149))
_HIGH_CONFIDENCE_CASE_IDS = {
    "CSV5-137",
    "CSV5-138",
    "CSV5-141",
    "CSV5-142",
    "CSV5-145",
    "CSV5-146",
}
_LOW_CONFIDENCE_CASE_IDS = set(_CASE_IDS) - _HIGH_CONFIDENCE_CASE_IDS


def test_mixed_reliability_inventory_is_exact_and_physically_separated() -> None:
    expected_names = {f"{case_id}.json" for case_id in _CASE_IDS}
    input_names = {path.name for path in (_FIXTURE_ROOT / "inputs" / "cases").iterdir()}
    outcome_names = {
        path.name for path in (_FIXTURE_ROOT / "expected_outcomes" / "cases").iterdir()
    }

    assert expected_names.issubset(input_names)
    assert expected_names.issubset(outcome_names)
    assert len(input_names) == 48
    assert len(outcome_names) == 48


def test_mixed_reliability_balances_workloads_and_candidate_positions() -> None:
    replay_cases = tuple(
        load_calibration_successor_v5_mixed_reliability_contrast_replay_case(
            _FIXTURE_ROOT,
            case_id,
        )
        for case_id in _CASE_IDS
    )
    workloads = Counter(case.runtime_input.contexts[0].workload_type.value for case in replay_cases)
    positions = Counter(
        context.block_position_index
        for case in replay_cases
        for context in case.runtime_input.contexts
    )

    assert workloads == {"structured_text": 4, "code": 4, "open_ended_chat": 4}
    assert positions == Counter({1: 12, 2: 12, 3: 12, 4: 12})


def test_mixed_reliability_exposes_over_and_under_confident_regions_without_leakage() -> None:
    mean_confidence_by_case: dict[str, float] = {}
    accepted_count_by_case: dict[str, int] = {}

    for case_id in _CASE_IDS:
        runtime_path = _FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json"
        runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        rendered = json.dumps(runtime_payload, sort_keys=True)

        assert runtime_payload["scenario_family_id"] == "CSV5-CAL-MIXED-RELIABILITY-CONTRAST"
        assert "candidate_token_id" not in rendered
        assert "observed_acceptance" not in rendered
        assert "prefix_survival_label" not in rendered

        replay_case = load_calibration_successor_v5_mixed_reliability_contrast_replay_case(
            _FIXTURE_ROOT,
            case_id,
        )
        confidences = [
            context.conditional_survival_confidence
            for context in replay_case.runtime_input.contexts
        ]
        outcomes = [
            outcome.observed_acceptance for outcome in replay_case.expected_outcomes.outcomes
        ]
        mean_confidence_by_case[case_id] = sum(confidences) / len(confidences)
        accepted_count_by_case[case_id] = sum(outcomes)

    high_confidence_mean = sum(
        mean_confidence_by_case[case_id] for case_id in _HIGH_CONFIDENCE_CASE_IDS
    )
    low_confidence_mean = sum(
        mean_confidence_by_case[case_id] for case_id in _LOW_CONFIDENCE_CASE_IDS
    )

    assert high_confidence_mean > low_confidence_mean
    assert all(accepted_count_by_case[case_id] <= 2 for case_id in _HIGH_CONFIDENCE_CASE_IDS)
    assert all(accepted_count_by_case[case_id] >= 3 for case_id in _LOW_CONFIDENCE_CASE_IDS)


def test_mixed_reliability_retains_heldout_containment_and_adversarial_quarantine() -> None:
    final_inputs = _FIXTURE_ROOT / "final_evaluation" / "inputs" / "cases"
    final_outcomes = _FIXTURE_ROOT / "final_evaluation" / "expected_outcomes" / "cases"

    assert tuple(sorted(path.stem for path in final_inputs.glob("*.json"))) == tuple(
        f"CSV5-{number:03d}" for number in range(201, 237)
    )
    assert tuple(sorted(path.stem for path in final_outcomes.glob("*.json"))) == tuple(
        f"CSV5-{number:03d}" for number in range(201, 237)
    )
    assert not (_FIXTURE_ROOT / "adversarial_regression").exists()
    assert (_FIXTURE_ROOT / "final_evaluation_manifest.json").is_file()
    assert (_FIXTURE_ROOT / "final_evidence_index.json").is_file()
    assert (_FIXTURE_ROOT / "calibration_manifest.json").is_file()
