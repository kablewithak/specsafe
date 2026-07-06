from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from specsafe.contracts.models import TraceDataRole, TraceSplit, WorkloadType
from specsafe.traces.calibration_redesign_v3_final_evidence import (
    load_calibration_redesign_v3_final_evaluation_replay_case,
)
from specsafe.traces.calibration_redesign_v3_manifest import (
    load_calibration_redesign_v3_calibration_manifested_fixture_set,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(201, 207))


def test_final_light_capacity_cases_are_quarantined_balanced_and_unscored() -> None:
    workload_counts: Counter[WorkloadType] = Counter()

    for case_id in CASE_IDS:
        runtime_path = FIXTURE_ROOT / "final_evaluation" / "inputs" / "cases" / f"{case_id}.json"
        runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        replay_case = load_calibration_redesign_v3_final_evaluation_replay_case(
            FIXTURE_ROOT, case_id
        )

        assert replay_case.runtime_input.scenario_family_id == "CRV3-FINAL-LIGHT-CAPACITY"
        assert replay_case.runtime_input.split is TraceSplit.FINAL_EVALUATION
        assert replay_case.runtime_input.data_role is TraceDataRole.HELD_OUT_EVALUATION
        assert len(replay_case.runtime_input.contexts) == 4
        assert len(replay_case.expected_outcomes.outcomes) == 4
        assert "candidate_token_id" not in runtime_payload
        assert "observed_acceptance" not in runtime_payload
        assert "prefix_survival_label" not in runtime_payload
        assert all(
            context.capacity_snapshot.profile_id == "synthetic-v3-final-light-capacity"
            for context in replay_case.runtime_input.contexts
        )
        workload_counts[replay_case.runtime_input.contexts[0].workload_type] += 1

    assert workload_counts == Counter(
        {
            WorkloadType.STRUCTURED_TEXT: 2,
            WorkloadType.CODE: 2,
            WorkloadType.OPEN_ENDED_CHAT: 2,
        }
    )
    assert (FIXTURE_ROOT / "final_evaluation_manifest.json").is_file()
    assert not (FIXTURE_ROOT / "heldout_assessment.json").exists()
    assert not (FIXTURE_ROOT / "adversarial_regression_manifest.json").exists()


def test_final_light_capacity_keeps_frozen_calibration_manifest_loadable() -> None:
    fixture_set = load_calibration_redesign_v3_calibration_manifested_fixture_set(FIXTURE_ROOT)

    assert fixture_set.manifest.case_count == 36
    assert len(fixture_set.cases) == 36


def test_final_light_capacity_inputs_use_light_request_pressure() -> None:
    for case_id in CASE_IDS:
        replay_case = load_calibration_redesign_v3_final_evaluation_replay_case(
            FIXTURE_ROOT, case_id
        )
        assert {
            context.capacity_snapshot.active_request_count
            for context in replay_case.runtime_input.contexts
        } <= {1, 2}
        assert [
            context.capacity_snapshot.verification_batch_tokens
            for context in replay_case.runtime_input.contexts
        ] == [0, 1, 2, 3]
