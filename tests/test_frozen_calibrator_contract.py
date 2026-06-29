from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.calibration import (
    CalibrationArtifactStatus,
    CalibrationControlEligibility,
    CalibrationFitError,
    CalibrationFitErrorCode,
    FrozenCalibratorFitProtocol,
    apply_frozen_calibrator,
    fit_frozen_histogram_calibrator,
    write_frozen_calibrator_artifact,
)
from specsafe.contracts import SyntheticTraceFixtureSet, TraceSplit
from specsafe.traces import load_synthetic_trace_fixture_set

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_trace_baselines"
)


def load_fixture_set() -> SyntheticTraceFixtureSet:
    return load_synthetic_trace_fixture_set(FIXTURE_ROOT)


def test_frozen_calibrator_uses_only_calibration_fixture_provenance() -> None:
    artifact = fit_frozen_histogram_calibrator(load_fixture_set())

    assert artifact.source_split is TraceSplit.CALIBRATION
    assert artifact.calibration_case_ids == ("STF-005", "STF-006")
    assert artifact.calibration_trace_ids == ("synthetic-trace-005", "synthetic-trace-006")
    assert artifact.source_observation_count == 8
    assert artifact.status is CalibrationArtifactStatus.FROZEN_PENDING_HELD_OUT_FITNESS
    assert (
        artifact.automation_control_eligibility
        is CalibrationControlEligibility.NOT_ELIGIBLE_PENDING_HELD_OUT_FITNESS
    )
    assert sum(bin_summary.source_observation_count for bin_summary in artifact.bins) == 8


def test_frozen_calibrator_fit_is_deterministic_and_final_outcomes_do_not_change_it() -> None:
    fixture_set = load_fixture_set()
    original = fit_frozen_histogram_calibrator(fixture_set)
    final_case_index = next(
        index
        for index, case in enumerate(fixture_set.cases)
        if case.runtime_input.split is TraceSplit.FINAL_EVALUATION
    )
    final_case = fixture_set.cases[final_case_index]
    altered_outcomes = tuple(
        outcome.model_copy(update={"observed_acceptance": not outcome.observed_acceptance})
        for outcome in final_case.expected_outcomes.outcomes
    )
    altered_final_case = final_case.model_copy(
        update={"expected_outcomes": final_case.expected_outcomes.model_copy(
            update={"outcomes": altered_outcomes}
        )}
    )
    altered_cases = list(fixture_set.cases)
    altered_cases[final_case_index] = altered_final_case
    fixture_with_altered_final = fixture_set.model_copy(update={"cases": tuple(altered_cases)})

    repeated = fit_frozen_histogram_calibrator(fixture_set)
    unaffected = fit_frozen_histogram_calibrator(fixture_with_altered_final)

    assert repeated == original
    assert unaffected == original


def test_frozen_calibrator_application_maps_one_to_the_final_bin() -> None:
    artifact = fit_frozen_histogram_calibrator(load_fixture_set())

    assert apply_frozen_calibrator(artifact, raw_confidence=1.0) == (
        artifact.bins[-1].applied_calibrated_probability
    )
    assert apply_frozen_calibrator(artifact, raw_confidence=0.0) == (
        artifact.bins[0].applied_calibrated_probability
    )
    with pytest.raises(ValueError, match="raw_confidence"):
        apply_frozen_calibrator(artifact, raw_confidence=1.01)


def test_frozen_calibrator_rejects_non_fixture_inputs_and_insufficient_data() -> None:
    with pytest.raises(CalibrationFitError) as invalid_fixture_error:
        fit_frozen_histogram_calibrator(object())
    assert invalid_fixture_error.value.code is CalibrationFitErrorCode.INVALID_FIXTURE_SET

    with pytest.raises(CalibrationFitError) as insufficient_error:
        fit_frozen_histogram_calibrator(
            load_fixture_set(),
            protocol=FrozenCalibratorFitProtocol(minimum_observation_count=9),
        )
    assert (
        insufficient_error.value.code
        is CalibrationFitErrorCode.INSUFFICIENT_CALIBRATION_OBSERVATIONS
    )


def test_frozen_calibrator_protocol_is_schema_strict() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        FrozenCalibratorFitProtocol(unapproved_final_evaluation=True)


def test_frozen_calibrator_artifact_persistence_is_deterministic(tmp_path: Path) -> None:
    artifact = fit_frozen_histogram_calibrator(load_fixture_set())
    first_path = write_frozen_calibrator_artifact(artifact, tmp_path / "first.json")
    second_path = write_frozen_calibrator_artifact(artifact, tmp_path / "second.json")

    assert first_path.read_bytes() == second_path.read_bytes()
    assert '"source_split": "calibration"' in first_path.read_text(encoding="utf-8")


def test_frozen_calibrator_artifact_requires_json_destination(tmp_path: Path) -> None:
    artifact = fit_frozen_histogram_calibrator(load_fixture_set())

    with pytest.raises(CalibrationFitError) as error:
        write_frozen_calibrator_artifact(artifact, tmp_path / "artifact.txt")
    assert error.value.code is CalibrationFitErrorCode.INVALID_DESTINATION
