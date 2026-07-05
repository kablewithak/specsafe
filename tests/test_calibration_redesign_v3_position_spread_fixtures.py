"""Regression coverage for the second V3 calibration position-spread fixture family."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from specsafe.contracts.models import TraceDataRole, TraceSplit, WorkloadType
from specsafe.traces.calibration_redesign_v3_cases import (
    load_calibration_redesign_v3_replay_case,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V3_FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(113, 125))


def test_v3_position_spread_cases_are_separate_fresh_calibration_assets() -> None:
    workload_counts: dict[WorkloadType, int] = {}
    observation_count_by_position: dict[int, int] = defaultdict(int)
    accepted_count_by_position: dict[int, int] = defaultdict(int)

    for case_id in CASE_IDS:
        runtime_path = V3_FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json"
        runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        replay_case = load_calibration_redesign_v3_replay_case(V3_FIXTURE_ROOT, case_id)
        runtime = replay_case.runtime_input
        outcomes = replay_case.expected_outcomes

        assert runtime.scenario_family_id == "CRV3-CAL-POSITION-SPREAD"
        assert runtime.split is TraceSplit.CALIBRATION
        assert runtime.data_role is TraceDataRole.CALIBRATION
        assert len(runtime.contexts) == 4
        assert len(outcomes.outcomes) == 4
        assert "candidate_token_id" not in runtime_payload
        assert "observed_acceptance" not in runtime_payload
        assert "prefix_survival_label" not in runtime_payload
        assert "CRV1-" not in runtime_path.read_text(encoding="utf-8")
        assert "CRV2-" not in runtime_path.read_text(encoding="utf-8")

        workload = runtime.contexts[0].workload_type
        workload_counts[workload] = workload_counts.get(workload, 0) + 1
        for context, outcome in zip(runtime.contexts, outcomes.outcomes, strict=True):
            observation_count_by_position[context.block_position_index] += 1
            accepted_count_by_position[context.block_position_index] += outcome.observed_acceptance

    assert workload_counts == {
        WorkloadType.STRUCTURED_TEXT: 4,
        WorkloadType.CODE: 4,
        WorkloadType.OPEN_ENDED_CHAT: 4,
    }
    assert dict(observation_count_by_position) == {1: 12, 2: 12, 3: 12, 4: 12}
    assert dict(accepted_count_by_position) == {1: 10, 2: 8, 3: 6, 4: 3}
    assert (V3_FIXTURE_ROOT / "calibration_manifest.json").is_file()
    assert not (V3_FIXTURE_ROOT / "final_evaluation_manifest.json").exists()
    assert not (V3_FIXTURE_ROOT / "final_evaluation_manifest.json").exists()
    assert not (V3_FIXTURE_ROOT / "adversarial_regression_manifest.json").exists()


def test_v3_position_spread_has_declared_declining_position_shape() -> None:
    confidence_by_position: dict[int, list[float]] = defaultdict(list)
    accepted_count_by_position: dict[int, int] = defaultdict(int)

    for case_id in CASE_IDS:
        replay_case = load_calibration_redesign_v3_replay_case(V3_FIXTURE_ROOT, case_id)
        for context, outcome in zip(
            replay_case.runtime_input.contexts,
            replay_case.expected_outcomes.outcomes,
            strict=True,
        ):
            position = context.block_position_index
            confidence_by_position[position].append(context.conditional_survival_confidence)
            accepted_count_by_position[position] += outcome.observed_acceptance

    mean_confidence_by_position = {
        position: sum(confidences) / len(confidences)
        for position, confidences in confidence_by_position.items()
    }

    assert mean_confidence_by_position[1] > mean_confidence_by_position[2]
    assert mean_confidence_by_position[2] > mean_confidence_by_position[3]
    assert mean_confidence_by_position[3] > mean_confidence_by_position[4]
    assert [accepted_count_by_position[position] for position in range(1, 5)] == [10, 8, 6, 3]
