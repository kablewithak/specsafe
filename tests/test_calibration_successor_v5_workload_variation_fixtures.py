"""Diagnostic tests for V5 calibration workload-variation fixtures."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from specsafe.traces.calibration_successor_v5_cases import (
    load_calibration_successor_v5_workload_variation_replay_case,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_successor_v5"
)
_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(125, 137))


def test_workload_variation_inventory_is_exact_and_physically_separated() -> None:
    expected_names = {f"{case_id}.json" for case_id in _CASE_IDS}
    input_names = {path.name for path in (_FIXTURE_ROOT / "inputs" / "cases").iterdir()}
    outcome_names = {
        path.name for path in (_FIXTURE_ROOT / "expected_outcomes" / "cases").iterdir()
    }

    assert expected_names.issubset(input_names)
    assert expected_names.issubset(outcome_names)
    assert len(input_names) == 48
    assert len(outcome_names) == 48


def test_workload_variation_balances_workloads_and_candidate_positions() -> None:
    replay_cases = tuple(
        load_calibration_successor_v5_workload_variation_replay_case(
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


def test_workload_variation_retains_distinct_workload_signals_without_runtime_leakage() -> None:
    confidence_by_workload: dict[str, list[float]] = defaultdict(list)
    outcomes_by_workload: dict[str, list[bool]] = defaultdict(list)
    accepted_by_position: dict[int, list[bool]] = {1: [], 2: [], 3: [], 4: []}

    for case_id in _CASE_IDS:
        runtime_path = _FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json"
        runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        rendered = json.dumps(runtime_payload, sort_keys=True)

        assert runtime_payload["scenario_family_id"] == "CSV5-CAL-WORKLOAD-VARIATION"
        assert "candidate_token_id" not in rendered
        assert "observed_acceptance" not in rendered
        assert "prefix_survival_label" not in rendered

        replay_case = load_calibration_successor_v5_workload_variation_replay_case(
            _FIXTURE_ROOT,
            case_id,
        )
        workload = replay_case.runtime_input.contexts[0].workload_type.value
        confidence_by_workload[workload].extend(
            context.conditional_survival_confidence
            for context in replay_case.runtime_input.contexts
        )
        for outcome in replay_case.expected_outcomes.outcomes:
            outcomes_by_workload[workload].append(outcome.observed_acceptance)
            accepted_by_position[outcome.block_position_index].append(outcome.observed_acceptance)

    assert all(any(values) and not all(values) for values in outcomes_by_workload.values())
    assert all(any(values) and not all(values) for values in accepted_by_position.values())
    assert (
        sum(confidence_by_workload["structured_text"])
        > sum(confidence_by_workload["code"])
        > sum(confidence_by_workload["open_ended_chat"])
    )
    assert sum(outcomes_by_workload["open_ended_chat"]) < sum(
        outcomes_by_workload["structured_text"]
    )


def test_workload_variation_retains_heldout_containment_and_adversarial_quarantine() -> None:
    final_inputs = _FIXTURE_ROOT / "final_evaluation" / "inputs" / "cases"
    final_outcomes = _FIXTURE_ROOT / "final_evaluation" / "expected_outcomes" / "cases"

    assert tuple(sorted(path.stem for path in final_inputs.glob("*.json"))) == tuple(
        f"CSV5-{number:03d}" for number in range(201, 237)
    )
    assert tuple(sorted(path.stem for path in final_outcomes.glob("*.json"))) == tuple(
        f"CSV5-{number:03d}" for number in range(201, 237)
    )
    assert not (_FIXTURE_ROOT / "adversarial_regression").exists()
    assert not (_FIXTURE_ROOT / "final_evaluation_manifest.json").exists()
    assert (_FIXTURE_ROOT / "calibration_manifest.json").is_file()
