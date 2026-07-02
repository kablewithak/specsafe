"""Regression tests for V2 in-memory runtime and outcome case contracts."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.contracts.models import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSchedulerContext,
    SyntheticTraceExpectedOutcome,
    TraceDataRole,
    TraceSplit,
    WorkloadType,
)
from specsafe.traces.calibration_redesign_v2 import (
    build_calibration_redesign_v2_scenario_family_registry,
    load_calibration_redesign_v2_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v2_cases import (
    CalibrationRedesignV2CaseContractError,
    CalibrationRedesignV2CaseViolationCode,
    CalibrationRedesignV2ExpectedOutcomes,
    CalibrationRedesignV2ReplayCase,
    CalibrationRedesignV2RuntimeInput,
    validate_calibration_redesign_v2_replay_case_membership,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v2"


def _contexts() -> tuple[CausalSchedulerContext, ...]:
    candidate_prefixes = ((), (7101,), (7101, 7102), (7101, 7102, 7103))
    confidences = (0.22, 0.41, 0.67, 0.83)
    return tuple(
        CausalSchedulerContext(
            trace_id="crv2-contract-trace-101",
            request_id="crv2-contract-request-101",
            workload_type=WorkloadType.STRUCTURED_TEXT,
            decode_round=0,
            block_position_index=index,
            visible_prefix_token_ids=prefix,
            conditional_survival_confidence=confidence,
            capacity_snapshot=CapacitySnapshot(
                profile_id="synthetic-v2-contract",
                source=CapacityProfileSource.SYNTHETIC,
                active_request_count=2,
                verification_batch_tokens=index - 1,
            ),
        )
        for index, (prefix, confidence) in enumerate(
            zip(candidate_prefixes, confidences, strict=True),
            start=1,
        )
    )


def _outcomes() -> tuple[SyntheticTraceExpectedOutcome, ...]:
    labels = (True, False, True, True)
    candidate_ids = (7101, 7102, 7103, 7104)
    prefix_labels = (True, False, False, False)
    return tuple(
        SyntheticTraceExpectedOutcome(
            trace_id="crv2-contract-trace-101",
            decode_round=0,
            block_position_index=index,
            candidate_token_id=candidate_id,
            observed_acceptance=accepted,
            prefix_survival_label=prefix_label,
        )
        for index, (candidate_id, accepted, prefix_label) in enumerate(
            zip(candidate_ids, labels, prefix_labels, strict=True),
            start=1,
        )
    )


def _finalized_registry(tmp_path: Path):
    root = tmp_path / "synthetic_calibration_redesign_v2"
    shutil.copytree(V2_FIXTURE_ROOT, root)
    generated_registry = root / "scenario_family_registry.json"
    generated_registry.unlink(missing_ok=True)
    registry_path = build_calibration_redesign_v2_scenario_family_registry(root)
    return load_calibration_redesign_v2_scenario_family_registry(registry_path)


def _runtime_payload() -> dict[str, object]:
    return {
        "schema_version": "calibration-redesign-v2-case-v1",
        "fixture_set_id": "synthetic-calibration-redesign-v2",
        "fixture_set_version": "1.0.0",
        "fixture_id": "CRV2-101-runtime",
        "case_id": "CRV2-101",
        "trace_id": "crv2-contract-trace-101",
        "request_id": "crv2-contract-request-101",
        "scenario_family_id": "CRV2-CAL-GLOBAL-ORDINAL",
        "split": TraceSplit.CALIBRATION,
        "data_role": TraceDataRole.CALIBRATION,
        "source_type": "synthetic",
        "generation_note": "Synthetic contract test only; not a committed fixture asset.",
        "contexts": _contexts(),
    }


def _outcome_payload() -> dict[str, object]:
    return {
        "schema_version": "calibration-redesign-v2-case-v1",
        "fixture_set_id": "synthetic-calibration-redesign-v2",
        "fixture_set_version": "1.0.0",
        "fixture_id": "CRV2-101-runtime",
        "case_id": "CRV2-101",
        "trace_id": "crv2-contract-trace-101",
        "scenario_family_id": "CRV2-CAL-GLOBAL-ORDINAL",
        "split": TraceSplit.CALIBRATION,
        "data_role": TraceDataRole.CALIBRATION,
        "source_type": "synthetic",
        "outcomes": _outcomes(),
    }


def _replay_case() -> CalibrationRedesignV2ReplayCase:
    return CalibrationRedesignV2ReplayCase(
        runtime_input=CalibrationRedesignV2RuntimeInput.model_validate(_runtime_payload()),
        expected_outcomes=CalibrationRedesignV2ExpectedOutcomes.model_validate(_outcome_payload()),
    )


def test_v2_case_contracts_join_only_after_runtime_and_outcome_alignment() -> None:
    replay_case = _replay_case()

    assert replay_case.runtime_input.case_id == "CRV2-101"
    assert len(replay_case.runtime_input.contexts) == 4
    assert len(replay_case.expected_outcomes.outcomes) == 4


def test_v2_runtime_contract_rejects_evaluation_only_label() -> None:
    payload = _runtime_payload()
    payload["observed_acceptance"] = True

    with pytest.raises(ValidationError):
        CalibrationRedesignV2RuntimeInput.model_validate(payload)


def test_v2_runtime_contract_requires_four_contexts() -> None:
    payload = _runtime_payload()
    payload["contexts"] = _contexts()[:3]

    with pytest.raises(ValidationError):
        CalibrationRedesignV2RuntimeInput.model_validate(payload)


def test_v2_replay_contract_rejects_visible_prefix_not_derived_from_outcomes() -> None:
    payload = _runtime_payload()
    contexts = list(_contexts())
    contexts[1] = contexts[1].model_copy(update={"visible_prefix_token_ids": (9999,)})
    payload["contexts"] = tuple(contexts)

    with pytest.raises(ValidationError):
        CalibrationRedesignV2ReplayCase(
            runtime_input=CalibrationRedesignV2RuntimeInput.model_validate(payload),
            expected_outcomes=CalibrationRedesignV2ExpectedOutcomes.model_validate(
                _outcome_payload()
            ),
        )


def test_v2_replay_case_membership_accepts_reserved_finalized_case(
    tmp_path: Path,
) -> None:
    registry = _finalized_registry(tmp_path)

    validate_calibration_redesign_v2_replay_case_membership(_replay_case(), registry)


def test_v2_replay_case_membership_rejects_unreserved_case_id(tmp_path: Path) -> None:
    runtime_payload = _runtime_payload()
    outcome_payload = _outcome_payload()
    runtime_payload["case_id"] = "CRV2-999"
    outcome_payload["case_id"] = "CRV2-999"
    replay_case = CalibrationRedesignV2ReplayCase(
        runtime_input=CalibrationRedesignV2RuntimeInput.model_validate(runtime_payload),
        expected_outcomes=CalibrationRedesignV2ExpectedOutcomes.model_validate(outcome_payload),
    )
    registry = _finalized_registry(tmp_path)

    with pytest.raises(CalibrationRedesignV2CaseContractError) as error_info:
        validate_calibration_redesign_v2_replay_case_membership(replay_case, registry)

    assert error_info.value.code is CalibrationRedesignV2CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR


def test_v2_replay_case_membership_rejects_untrusted_registry_type() -> None:
    with pytest.raises(CalibrationRedesignV2CaseContractError) as error_info:
        validate_calibration_redesign_v2_replay_case_membership(_replay_case(), object())

    assert error_info.value.code is CalibrationRedesignV2CaseViolationCode.UNTRUSTED_REGISTRY
