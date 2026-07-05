from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.traces.calibration_redesign_v3 import (
    load_calibration_redesign_v3_scenario_family_registry,
)
from specsafe.traces.calibration_redesign_v3_cases import (
    CalibrationRedesignV3CaseContractError,
    CalibrationRedesignV3CaseViolationCode,
    CalibrationRedesignV3ExpectedOutcomes,
    CalibrationRedesignV3ReplayCase,
    CalibrationRedesignV3RuntimeInput,
    load_calibration_redesign_v3_replay_case,
    validate_calibration_redesign_v3_replay_case_membership,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"


def _runtime_payload() -> dict[str, object]:
    return json.loads(
        (FIXTURE_ROOT / "inputs" / "cases" / "CRV3-101.json").read_text(encoding="utf-8")
    )


def _outcome_payload() -> dict[str, object]:
    return json.loads(
        (FIXTURE_ROOT / "expected_outcomes" / "cases" / "CRV3-101.json").read_text(encoding="utf-8")
    )


def _replay_case() -> CalibrationRedesignV3ReplayCase:
    return CalibrationRedesignV3ReplayCase(
        runtime_input=CalibrationRedesignV3RuntimeInput.model_validate(_runtime_payload()),
        expected_outcomes=CalibrationRedesignV3ExpectedOutcomes.model_validate(_outcome_payload()),
    )


def _registry():
    return load_calibration_redesign_v3_scenario_family_registry(
        FIXTURE_ROOT / "scenario_family_registry.json",
        allow_calibration_manifest_assets=True,
    )


def test_v3_runtime_contract_rejects_evaluation_only_label() -> None:
    payload = _runtime_payload()
    payload["observed_acceptance"] = True

    with pytest.raises(ValidationError):
        CalibrationRedesignV3RuntimeInput.model_validate(payload)


def test_v3_runtime_contract_requires_exactly_four_contexts() -> None:
    payload = _runtime_payload()
    payload["contexts"] = payload["contexts"][:3]

    with pytest.raises(ValidationError):
        CalibrationRedesignV3RuntimeInput.model_validate(payload)


def test_v3_replay_contract_rejects_visible_prefix_not_derived_from_outcomes() -> None:
    runtime_payload = _runtime_payload()
    runtime_payload["contexts"][1]["visible_prefix_token_ids"] = [9999]

    with pytest.raises(ValidationError):
        CalibrationRedesignV3ReplayCase(
            runtime_input=CalibrationRedesignV3RuntimeInput.model_validate(runtime_payload),
            expected_outcomes=CalibrationRedesignV3ExpectedOutcomes.model_validate(
                _outcome_payload()
            ),
        )


def test_v3_replay_case_membership_accepts_authorised_curve_case() -> None:
    validate_calibration_redesign_v3_replay_case_membership(_replay_case(), _registry())


def test_v3_replay_case_membership_accepts_authorised_position_spread_case() -> None:
    replay_case = load_calibration_redesign_v3_replay_case(FIXTURE_ROOT, "CRV3-113")

    validate_calibration_redesign_v3_replay_case_membership(replay_case, _registry())


def test_v3_replay_case_membership_accepts_authorised_workload_mix_case() -> None:
    replay_case = load_calibration_redesign_v3_replay_case(FIXTURE_ROOT, "CRV3-125")

    validate_calibration_redesign_v3_replay_case_membership(replay_case, _registry())


def test_v3_replay_case_membership_rejects_unreserved_case_id() -> None:
    runtime_payload = _runtime_payload()
    outcome_payload = _outcome_payload()
    runtime_payload["case_id"] = "CRV3-999"
    outcome_payload["case_id"] = "CRV3-999"
    replay_case = CalibrationRedesignV3ReplayCase(
        runtime_input=CalibrationRedesignV3RuntimeInput.model_validate(runtime_payload),
        expected_outcomes=CalibrationRedesignV3ExpectedOutcomes.model_validate(outcome_payload),
    )

    with pytest.raises(CalibrationRedesignV3CaseContractError) as error_info:
        validate_calibration_redesign_v3_replay_case_membership(replay_case, _registry())

    assert error_info.value.code is CalibrationRedesignV3CaseViolationCode.REGISTRY_MEMBERSHIP_ERROR


def test_v3_replay_case_membership_rejects_untrusted_registry_type() -> None:
    with pytest.raises(CalibrationRedesignV3CaseContractError) as error_info:
        validate_calibration_redesign_v3_replay_case_membership(_replay_case(), object())

    assert error_info.value.code is CalibrationRedesignV3CaseViolationCode.UNTRUSTED_REGISTRY


def test_v3_case_loader_rejects_missing_expected_outcome_asset(tmp_path: Path) -> None:
    copied_root = tmp_path / "synthetic_calibration_redesign_v3"
    shutil.copytree(FIXTURE_ROOT, copied_root)
    (copied_root / "expected_outcomes" / "cases" / "CRV3-101.json").unlink()

    with pytest.raises(CalibrationRedesignV3CaseContractError) as error_info:
        load_calibration_redesign_v3_replay_case(copied_root, "CRV3-101")

    assert error_info.value.code is CalibrationRedesignV3CaseViolationCode.CASE_ASSET_LAYOUT_ERROR
