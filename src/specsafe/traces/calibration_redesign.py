"""Governed scenario-family registry validation for calibration-redesign fixtures."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import Field, ValidationError, field_validator, model_validator

from specsafe.contracts.models import (
    StrictContract,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)


class CalibrationRedesignFixtureViolationCode(StrEnum):
    """Machine-readable reasons a fresh calibration registry cannot be trusted."""

    REGISTRY_SCHEMA_ERROR = "calibration_redesign_registry_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = "calibration_redesign_registry_provenance_mismatch"
    HISTORICAL_HELDOUT_REUSE = "historical_heldout_reuse"


class CalibrationRedesignFixtureLoadError(ValueError):
    """Typed error raised when a scenario-family registry violates its evidence boundary."""

    def __init__(self, code: CalibrationRedesignFixtureViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.DEVELOPMENT: TraceDataRole.SYNTHETIC_FIXTURE,
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}


class ScenarioFamilyRecord(StrictContract):
    """One governed scenario family with split ownership and lineage metadata."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    parent_scenario_family_id: str | None = Field(default=None, max_length=128)
    source_template_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    is_final_evaluation_quarantined: bool

    @field_validator("case_ids")
    @classmethod
    def validate_unique_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        """Reject duplicate case identifiers inside a single scenario family."""

        if len(set(case_ids)) != len(case_ids):
            raise ValueError("scenario-family case IDs must be unique")
        return case_ids

    @model_validator(mode="after")
    def validate_split_role_and_quarantine(self) -> ScenarioFamilyRecord:
        """Bind role and quarantine behavior to the declared split."""

        expected_data_role = _EXPECTED_DATA_ROLE_BY_SPLIT[self.split]
        if self.primary_data_role is not expected_data_role:
            raise ValueError(
                "primary_data_role must match the governed data role for the declared split"
            )

        expected_quarantine = self.split is TraceSplit.FINAL_EVALUATION
        if self.is_final_evaluation_quarantined is not expected_quarantine:
            raise ValueError(
                "is_final_evaluation_quarantined must be true only for final-evaluation families"
            )
        return self


class ScenarioFamilyRegistry(StrictContract):
    """Immutable registry for fresh calibration fixture lineage and split isolation."""

    schema_version: str = Field(min_length=1, max_length=64)
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    source_type: TraceSourceType
    authoring_protocol_version: str = Field(min_length=1, max_length=64)
    excluded_historical_case_ids: tuple[str, ...] = Field(min_length=1)
    families: tuple[ScenarioFamilyRecord, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_registry_governance(self) -> ScenarioFamilyRegistry:
        """Enforce fresh evidence, split isolation, lineage, and authoring-floor controls."""

        if self.source_type is not TraceSourceType.SYNTHETIC:
            raise ValueError("calibration-redesign registry source_type must be synthetic")
        if "STF-004" not in self.excluded_historical_case_ids:
            raise ValueError("STF-004 must remain declared as an excluded historical case")

        family_ids = [family.scenario_family_id for family in self.families]
        if len(set(family_ids)) != len(family_ids):
            raise ValueError("scenario_family_id values must be unique")

        case_to_family: dict[str, str] = {}
        family_by_id = {family.scenario_family_id: family for family in self.families}
        for family in self.families:
            for case_id in family.case_ids:
                if case_id in self.excluded_historical_case_ids:
                    raise ValueError(
                        "historical excluded case IDs must not appear in fresh families"
                    )
                if case_id in case_to_family:
                    raise ValueError("case IDs must not repeat across scenario families")
                case_to_family[case_id] = family.scenario_family_id

            if family.parent_scenario_family_id is not None:
                parent = family_by_id.get(family.parent_scenario_family_id)
                if parent is None:
                    raise ValueError("parent_scenario_family_id must reference an existing family")
                if parent.split is not family.split:
                    raise ValueError("parent scenario family must remain in the same split")

        calibration_fingerprints = {
            family.source_template_fingerprint
            for family in self.families
            if family.split is TraceSplit.CALIBRATION
        }
        final_evaluation_fingerprints = {
            family.source_template_fingerprint
            for family in self.families
            if family.split is TraceSplit.FINAL_EVALUATION
        }
        if calibration_fingerprints & final_evaluation_fingerprints:
            raise ValueError(
                "source_template_fingerprint must not repeat across calibration and "
                "final evaluation"
            )

        families_by_split = {
            split: tuple(family for family in self.families if family.split is split)
            for split in TraceSplit
        }
        if len(families_by_split[TraceSplit.CALIBRATION]) < 2:
            raise ValueError("registry requires at least two calibration scenario families")
        if len(families_by_split[TraceSplit.FINAL_EVALUATION]) < 2:
            raise ValueError("registry requires at least two final-evaluation scenario families")
        if not families_by_split[TraceSplit.DEVELOPMENT]:
            raise ValueError("registry requires at least one development scenario family")
        if not families_by_split[TraceSplit.ADVERSARIAL_REGRESSION]:
            raise ValueError("registry requires at least one adversarial-regression family")

        calibration_case_count = sum(
            len(family.case_ids) for family in families_by_split[TraceSplit.CALIBRATION]
        )
        final_evaluation_case_count = sum(
            len(family.case_ids) for family in families_by_split[TraceSplit.FINAL_EVALUATION]
        )
        if calibration_case_count < 6:
            raise ValueError("registry requires at least six calibration cases")
        if final_evaluation_case_count < 4:
            raise ValueError("registry requires at least four final-evaluation cases")
        return self


def load_calibration_redesign_scenario_family_registry(path: Path) -> ScenarioFamilyRegistry:
    """Load a strict scenario-family registry without falling back on malformed evidence."""

    try:
        payload: Any = json.loads(path.read_bytes())
    except OSError as error:
        raise CalibrationRedesignFixtureLoadError(
            CalibrationRedesignFixtureViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            f"unable to read scenario-family registry: {path}",
        ) from error
    except json.JSONDecodeError as error:
        raise CalibrationRedesignFixtureLoadError(
            CalibrationRedesignFixtureViolationCode.REGISTRY_SCHEMA_ERROR,
            f"invalid JSON in scenario-family registry: {error.msg}",
        ) from error

    try:
        return ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        error_text = str(error)
        violation_code = (
            CalibrationRedesignFixtureViolationCode.HISTORICAL_HELDOUT_REUSE
            if "historical excluded case" in error_text
            else CalibrationRedesignFixtureViolationCode.REGISTRY_SCHEMA_ERROR
        )
        raise CalibrationRedesignFixtureLoadError(
            violation_code,
            f"scenario-family registry validation failed: {error_text}",
        ) from error
