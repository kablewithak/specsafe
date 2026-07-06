"""Calibration-only diagnostic tests for V4 workload-mix fixtures."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from specsafe.traces.calibration_redesign_v4_cases import (
    load_calibration_redesign_v4_replay_case,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_calibration_redesign_v4"
)
_CASE_IDS = tuple(f"CRV4-{number:03d}" for number in range(125, 137))


def test_workload_mix_inventory_is_present_in_both_physical_asset_trees() -> None:
    expected_names = {f"{case_id}.json" for case_id in _CASE_IDS}
    input_names = {path.name for path in (_FIXTURE_ROOT / "inputs" / "cases").iterdir()}
    outcome_names = {
        path.name for path in (_FIXTURE_ROOT / "expected_outcomes" / "cases").iterdir()
    }

    assert expected_names.issubset(input_names)
    assert expected_names.issubset(outcome_names)


def test_workload_mix_balances_workload_types_and_positions() -> None:
    replay_cases = tuple(
        load_calibration_redesign_v4_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _CASE_IDS
    )

    workloads = Counter(
        replay_case.runtime_input.contexts[0].workload_type.value
        for replay_case in replay_cases
    )
    positions = Counter(
        context.block_position_index
        for replay_case in replay_cases
        for context in replay_case.runtime_input.contexts
    )

    assert workloads == Counter(
        {
            "structured_text": 4,
            "code": 4,
            "open_ended_chat": 4,
        }
    )
    assert positions == Counter({1: 12, 2: 12, 3: 12, 4: 12})


def test_workload_mix_runtime_assets_are_label_free_and_confidence_diverse() -> None:
    confidence_sequences = set()
    for case_id in _CASE_IDS:
        runtime_path = _FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json"
        payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        confidences = tuple(
            context["conditional_survival_confidence"]
            for context in payload["contexts"]
        )
        confidence_sequences.add(confidences)

        assert payload["scenario_family_id"] == "CRV4-CAL-WORKLOAD-MIX"
        assert confidences == tuple(sorted(confidences, reverse=True))
        rendered = json.dumps(payload, sort_keys=True)
        assert "candidate_token_id" not in rendered
        assert "observed_acceptance" not in rendered
        assert "prefix_survival_label" not in rendered

    assert len(confidence_sequences) == len(_CASE_IDS)


def test_workload_mix_retains_both_outcome_classes_and_no_final_result_assets() -> None:
    replay_cases = tuple(
        load_calibration_redesign_v4_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _CASE_IDS
    )
    observed_acceptance = [
        outcome.observed_acceptance
        for replay_case in replay_cases
        for outcome in replay_case.expected_outcomes.outcomes
    ]

    assert any(observed_acceptance)
    assert not all(observed_acceptance)
    assert not (_FIXTURE_ROOT / "adversarial_regression").exists()
    assert not (_FIXTURE_ROOT / "final_evaluation_manifest.json").exists()
    assert not (_FIXTURE_ROOT / "final_evidence_index.json").exists()
    assert not (_FIXTURE_ROOT / "heldout_assessment.json").exists()
