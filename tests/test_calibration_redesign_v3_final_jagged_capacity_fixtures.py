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
CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(219, 225))
EXPECTED_PRESSURE_BY_CASE = {
    "CRV3-219": ((3, 1), (11, 10), (4, 2), (12, 11)),
    "CRV3-220": ((11, 10), (4, 2), (12, 11), (3, 1)),
    "CRV3-221": ((5, 3), (12, 11), (3, 1), (10, 9)),
    "CRV3-222": ((12, 11), (5, 3), (10, 9), (4, 2)),
    "CRV3-223": ((4, 2), (10, 8), (3, 1), (12, 10)),
    "CRV3-224": ((10, 8), (3, 1), (12, 10), (5, 3)),
}


def test_final_jagged_capacity_cases_are_quarantined_balanced_and_unscored() -> None:
    workload_counts: Counter[WorkloadType] = Counter()

    for case_id in CASE_IDS:
        runtime_path = FIXTURE_ROOT / "final_evaluation" / "inputs" / "cases" / f"{case_id}.json"
        runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        replay_case = load_calibration_redesign_v3_final_evaluation_replay_case(
            FIXTURE_ROOT, case_id
        )

        assert replay_case.runtime_input.scenario_family_id == "CRV3-FINAL-JAGGED-CAPACITY"
        assert replay_case.runtime_input.split is TraceSplit.FINAL_EVALUATION
        assert replay_case.runtime_input.data_role is TraceDataRole.HELD_OUT_EVALUATION
        assert len(replay_case.runtime_input.contexts) == 4
        assert len(replay_case.expected_outcomes.outcomes) == 4
        assert "candidate_token_id" not in runtime_payload
        assert "observed_acceptance" not in runtime_payload
        assert "prefix_survival_label" not in runtime_payload
        assert all(
            context.capacity_snapshot.profile_id == "synthetic-v3-final-jagged-capacity"
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


def test_final_jagged_capacity_keeps_frozen_calibration_manifest_loadable() -> None:
    fixture_set = load_calibration_redesign_v3_calibration_manifested_fixture_set(FIXTURE_ROOT)

    assert fixture_set.manifest.case_count == 36
    assert len(fixture_set.cases) == 36


def test_final_jagged_capacity_inputs_use_declared_non_monotonic_pressure() -> None:
    for case_id, expected_pressure in EXPECTED_PRESSURE_BY_CASE.items():
        replay_case = load_calibration_redesign_v3_final_evaluation_replay_case(
            FIXTURE_ROOT, case_id
        )
        observed_pressure = tuple(
            (
                context.capacity_snapshot.active_request_count,
                context.capacity_snapshot.verification_batch_tokens,
            )
            for context in replay_case.runtime_input.contexts
        )

        assert observed_pressure == expected_pressure
        active_requests = tuple(active for active, _ in observed_pressure)
        batch_tokens = tuple(batch for _, batch in observed_pressure)
        assert any(
            later > earlier
            for earlier, later in zip(active_requests, active_requests[1:], strict=True)
        )
        assert any(
            later < earlier
            for earlier, later in zip(active_requests, active_requests[1:], strict=True)
        )
        assert any(
            later > earlier for earlier, later in zip(batch_tokens, batch_tokens[1:], strict=True)
        )
        assert any(
            later < earlier for earlier, later in zip(batch_tokens, batch_tokens[1:], strict=True)
        )
