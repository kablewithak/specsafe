"""Regression coverage for the V2 cross-context calibration fixture family."""

from __future__ import annotations

import json
from pathlib import Path

from specsafe.contracts.models import TraceDataRole, TraceSplit, WorkloadType
from specsafe.traces.calibration_redesign_v2_cases import (
    load_calibration_redesign_v2_replay_case,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"


def test_v2_case_loader_reads_authored_cross_context_assets() -> None:
    case_ids = ("CRV2-105", "CRV2-106", "CRV2-107", "CRV2-108")
    workload_types: set[WorkloadType] = set()
    capacity_profile_ids: set[str] = set()
    observed_outcome_count = 0

    for case_id in case_ids:
        runtime_payload = json.loads(
            (V2_FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json").read_text(encoding="utf-8")
        )
        replay_case = load_calibration_redesign_v2_replay_case(V2_FIXTURE_ROOT, case_id)
        runtime = replay_case.runtime_input
        outcomes = replay_case.expected_outcomes

        assert runtime.scenario_family_id == "CRV2-CAL-CROSS-CONTEXT"
        assert runtime.split is TraceSplit.CALIBRATION
        assert runtime.data_role is TraceDataRole.CALIBRATION
        assert len(runtime.contexts) == 4
        assert len(outcomes.outcomes) == 4
        assert "observed_acceptance" not in runtime_payload
        assert "candidate_token_id" not in runtime_payload
        assert "prefix_survival_label" not in runtime_payload
        assert "workload_specific_calibration_parameter" not in runtime_payload
        assert "capacity_conditioned_calibration_parameter" not in runtime_payload

        workload_types.add(runtime.contexts[0].workload_type)
        capacity_profile_ids.add(runtime.contexts[0].capacity_snapshot.profile_id)
        observed_outcome_count += len(outcomes.outcomes)

    assert workload_types == {
        WorkloadType.STRUCTURED_TEXT,
        WorkloadType.CODE,
        WorkloadType.OPEN_ENDED_CHAT,
    }
    assert len(capacity_profile_ids) == 4
    assert observed_outcome_count == 16
    assert (V2_FIXTURE_ROOT / "calibration_manifest.json").is_file()
