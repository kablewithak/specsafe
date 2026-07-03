"""Regression coverage for the first V3 calibration curve-coverage fixture family."""

from __future__ import annotations

import json
from pathlib import Path

from specsafe.contracts.models import TraceDataRole, TraceSplit, WorkloadType
from specsafe.traces.calibration_redesign_v3_cases import (
    load_calibration_redesign_v3_replay_case,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V3_FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
CASE_IDS = tuple(f"CRV3-{number:03d}" for number in range(101, 113))


def test_v3_curve_coverage_cases_are_separate_fresh_calibration_assets() -> None:
    observations: list[tuple[float, bool]] = []
    workload_counts: dict[WorkloadType, int] = {}

    for case_id in CASE_IDS:
        runtime_payload = json.loads(
            (V3_FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json").read_text(encoding="utf-8")
        )
        replay_case = load_calibration_redesign_v3_replay_case(V3_FIXTURE_ROOT, case_id)
        runtime = replay_case.runtime_input
        outcomes = replay_case.expected_outcomes

        assert runtime.scenario_family_id == "CRV3-CAL-CURVE-COVERAGE"
        assert runtime.split is TraceSplit.CALIBRATION
        assert runtime.data_role is TraceDataRole.CALIBRATION
        assert len(runtime.contexts) == 4
        assert len(outcomes.outcomes) == 4
        assert "candidate_token_id" not in runtime_payload
        assert "observed_acceptance" not in runtime_payload
        assert "prefix_survival_label" not in runtime_payload
        assert "CRV1-" not in (V3_FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json").read_text(
            encoding="utf-8"
        )
        assert "CRV2-" not in (V3_FIXTURE_ROOT / "inputs" / "cases" / f"{case_id}.json").read_text(
            encoding="utf-8"
        )

        workload = runtime.contexts[0].workload_type
        workload_counts[workload] = workload_counts.get(workload, 0) + 1
        observations.extend(
            (context.conditional_survival_confidence, outcome.observed_acceptance)
            for context, outcome in zip(runtime.contexts, outcomes.outcomes, strict=True)
        )

    assert workload_counts == {
        WorkloadType.STRUCTURED_TEXT: 4,
        WorkloadType.CODE: 4,
        WorkloadType.OPEN_ENDED_CHAT: 4,
    }
    assert len(observations) == 48
    assert min(confidence for confidence, _ in observations) == 0.10
    assert max(confidence for confidence, _ in observations) == 0.87
    assert not (V3_FIXTURE_ROOT / "calibration_manifest.json").exists()
    assert not (V3_FIXTURE_ROOT / "final_evaluation_manifest.json").exists()
    assert not (V3_FIXTURE_ROOT / "adversarial_regression_manifest.json").exists()


def test_v3_curve_coverage_has_declared_monotonic_non_linear_band_shape() -> None:
    observations: list[tuple[float, bool]] = []

    for case_id in CASE_IDS:
        replay_case = load_calibration_redesign_v3_replay_case(V3_FIXTURE_ROOT, case_id)
        observations.extend(
            (context.conditional_survival_confidence, outcome.observed_acceptance)
            for context, outcome in zip(
                replay_case.runtime_input.contexts,
                replay_case.expected_outcomes.outcomes,
                strict=True,
            )
        )

    band_acceptance_counts = {
        "low": sum(accepted for confidence, accepted in observations if confidence <= 0.21),
        "lower_middle": sum(
            accepted for confidence, accepted in observations if 0.30 <= confidence <= 0.41
        ),
        "upper_middle": sum(
            accepted for confidence, accepted in observations if 0.52 <= confidence <= 0.63
        ),
        "high": sum(
            accepted for confidence, accepted in observations if 0.76 <= confidence <= 0.87
        ),
    }

    assert band_acceptance_counts == {
        "low": 1,
        "lower_middle": 4,
        "upper_middle": 7,
        "high": 9,
    }
