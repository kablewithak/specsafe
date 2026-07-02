"""Regression tests for frozen temperature-scaling held-out fitness assessment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsafe.traces import (
    DEFAULT_HELD_OUT_TEMPERATURE_SCALING_ASSESSMENT_PROTOCOL,
    HeldOutTemperatureScalingAdaptivePolicyResearchEligibility,
    HeldOutTemperatureScalingAssessmentError,
    HeldOutTemperatureScalingAssessmentProtocol,
    HeldOutTemperatureScalingAssessmentStatus,
    HeldOutTemperatureScalingAssessmentViolationCode,
    HeldOutTemperatureScalingPromotionDecision,
    assess_logit_temperature_scaling_heldout,
    load_calibration_redesign_final_evaluation_manifested_fixture_set,
    load_logit_temperature_scaling_artifact,
    write_logit_temperature_scaling_heldout_assessment,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign"
ARTIFACT_PATH = (
    PROJECT_ROOT
    / "evidence"
    / "calibration"
    / "logit-temperature-scaling-v1"
    / "artifact.json"
)


def _load_assessment_inputs():
    fixture_set = load_calibration_redesign_final_evaluation_manifested_fixture_set(
        FIXTURE_ROOT
    )
    artifact = load_logit_temperature_scaling_artifact(ARTIFACT_PATH)
    return fixture_set, artifact


def test_frozen_artifact_is_assessed_once_against_all_final_cases() -> None:
    fixture_set, artifact = _load_assessment_inputs()

    result = assess_logit_temperature_scaling_heldout(fixture_set, artifact)

    assert result.observation_count == 18
    assert result.assessed_case_ids == (
        "CRV1-009",
        "CRV1-010",
        "CRV1-011",
        "CRV1-012",
    )
    assert result.assessed_scenario_family_ids == (
        "CRV1-FINAL-ABRUPT-SUFFIX",
        "CRV1-FINAL-MIXED-RELIABILITY",
    )
    assert (
        result.status is HeldOutTemperatureScalingAssessmentStatus.CALIBRATOR_REGRESSION
    )
    assert (
        result.promotion_decision
        is HeldOutTemperatureScalingPromotionDecision.NOT_PROMOTED_CALIBRATOR_REGRESSION
    )
    assert (
        result.adaptive_policy_research_eligibility
        is (
            HeldOutTemperatureScalingAdaptivePolicyResearchEligibility
            .BLOCKED_HELD_OUT_CALIBRATION_REGRESSION
        )
    )
    assert result.brier_improvement < 0.0
    assert result.expected_calibration_error_improvement > 0.0
    assert result.final_evaluation_accessed is True
    assert result.artifact_refit is False
    assert result.artifact_mutated is False
    assert artifact.final_evaluation_accessed is False
    assert artifact.runtime_control_eligible is False
    assert sum(bin.observation_count for bin in result.raw_metrics.bins) == 18
    assert sum(bin.observation_count for bin in result.calibrated_metrics.bins) == 18


def test_final_evaluation_case_cannot_be_added_to_frozen_fit_inventory() -> None:
    fixture_set, artifact = _load_assessment_inputs()
    contaminated_artifact = artifact.model_copy(
        update={"fitted_case_ids": (*artifact.fitted_case_ids, "CRV1-009")}
    )

    with pytest.raises(HeldOutTemperatureScalingAssessmentError) as error:
        assess_logit_temperature_scaling_heldout(fixture_set, contaminated_artifact)

    assert (
        error.value.code
        is HeldOutTemperatureScalingAssessmentViolationCode.ARTIFACT_PROVENANCE_MISMATCH
    )


def test_assessment_rejects_non_final_fixture_set_type() -> None:
    _, artifact = _load_assessment_inputs()

    with pytest.raises(HeldOutTemperatureScalingAssessmentError) as error:
        assess_logit_temperature_scaling_heldout(object(), artifact)  # type: ignore[arg-type]

    assert (
        error.value.code
        is HeldOutTemperatureScalingAssessmentViolationCode.UNTRUSTED_FINAL_FIXTURE_SET
    )


def test_minimum_observation_gate_blocks_without_refitting() -> None:
    fixture_set, artifact = _load_assessment_inputs()
    protocol = HeldOutTemperatureScalingAssessmentProtocol(
        schema_version="heldout-temperature-scaling-assessment-protocol-v1",
        protocol_id="logit-temperature-scaling-heldout-fitness-v1",
        minimum_observation_count=19,
        equal_width_bin_count=10,
        minimum_brier_improvement=0.0,
        minimum_expected_calibration_error_improvement=0.0,
    )

    result = assess_logit_temperature_scaling_heldout(fixture_set, artifact, protocol)

    assert (
        result.status
        is HeldOutTemperatureScalingAssessmentStatus.INSUFFICIENT_HELD_OUT_DATA
    )
    assert result.artifact_refit is False
    assert result.artifact_mutated is False


def test_writer_retains_machine_readable_non_promotion_result(tmp_path: Path) -> None:
    fixture_set, artifact = _load_assessment_inputs()
    output_path = tmp_path / "heldout_assessment.json"

    result = write_logit_temperature_scaling_heldout_assessment(
        fixture_root=FIXTURE_ROOT,
        artifact_path=ARTIFACT_PATH,
        output_path=output_path,
        protocol=DEFAULT_HELD_OUT_TEMPERATURE_SCALING_ASSESSMENT_PROTOCOL,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert payload["status"] == result.status.value
    assert payload["promotion_decision"] == result.promotion_decision.value
    assert payload["artifact_refit"] is False
    assert payload["artifact_mutated"] is False
    assert set(payload["assessed_case_ids"]) == {
        case.runtime_input.case_id for case in fixture_set.cases
    }
    assert payload["artifact"]["fitted_case_ids"] == list(artifact.fitted_case_ids)
