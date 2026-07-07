"""V5 governed fixture registry and staged evidence-root boundaries.

The V5 programme authors calibration evidence family by family. This module keeps the
final and adversarial reservations quarantined and rejects manifests, fit artefacts,
policy work, and final evidence until their separately authorised stages.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from specsafe.contracts.models import (
    StrictContract,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
)

_V5_REGISTRY_FILENAME = "scenario_family_registry.json"
_V5_PROPOSAL_MANIFEST_FILENAME = "PROPOSAL_MANIFEST.md"
_V5_AUTHORING_LEDGER_FILENAME = "authoring_ledger.md"
_V5_CALIBRATION_MANIFEST_FILENAME = "calibration_manifest.json"
_V5_ROOT_METADATA_FILENAMES = {
    _V5_REGISTRY_FILENAME,
    _V5_PROPOSAL_MANIFEST_FILENAME,
    _V5_AUTHORING_LEDGER_FILENAME,
}
_V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(101, 113))
_V5_CALIBRATION_POSITION_SPREAD_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(113, 125))
_V5_CALIBRATION_WORKLOAD_VARIATION_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(125, 137)
)
_V5_CALIBRATION_MIXED_RELIABILITY_CONTRAST_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(137, 149)
)
_V5_FINAL_CURVE_COVERAGE_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(201, 210))
_V5_FINAL_POSITION_SPREAD_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(210, 219))
_V5_FINAL_WORKLOAD_VARIATION_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(219, 228))
_V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS = tuple(
    f"CSV5-{number:03d}" for number in range(228, 237)
)
_V5_ADVERSARIAL_CAUSAL_GUARD_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(301, 307))
_V5_ADVERSARIAL_PROVENANCE_GATE_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(307, 313))
_V5_EXPECTED_CASE_IDS_BY_FAMILY = {
    "CSV5-CAL-CURVE-COVERAGE": _V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
    "CSV5-CAL-POSITION-SPREAD": _V5_CALIBRATION_POSITION_SPREAD_CASE_IDS,
    "CSV5-CAL-WORKLOAD-VARIATION": _V5_CALIBRATION_WORKLOAD_VARIATION_CASE_IDS,
    "CSV5-CAL-MIXED-RELIABILITY-CONTRAST": (_V5_CALIBRATION_MIXED_RELIABILITY_CONTRAST_CASE_IDS),
    "CSV5-FINAL-CURVE-COVERAGE": _V5_FINAL_CURVE_COVERAGE_CASE_IDS,
    "CSV5-FINAL-POSITION-SPREAD": _V5_FINAL_POSITION_SPREAD_CASE_IDS,
    "CSV5-FINAL-WORKLOAD-VARIATION": _V5_FINAL_WORKLOAD_VARIATION_CASE_IDS,
    "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST": (_V5_FINAL_MIXED_RELIABILITY_CONTRAST_CASE_IDS),
    "CSV5-ADV-CAUSAL-GUARD": _V5_ADVERSARIAL_CAUSAL_GUARD_CASE_IDS,
    "CSV5-ADV-PROVENANCE-GATE": _V5_ADVERSARIAL_PROVENANCE_GATE_CASE_IDS,
}
_V5_EXPECTED_FAMILY_IDS = frozenset(_V5_EXPECTED_CASE_IDS_BY_FAMILY)
_EXPECTED_DATA_ROLE_BY_SPLIT = {
    TraceSplit.CALIBRATION: TraceDataRole.CALIBRATION,
    TraceSplit.FINAL_EVALUATION: TraceDataRole.HELD_OUT_EVALUATION,
    TraceSplit.ADVERSARIAL_REGRESSION: TraceDataRole.SYNTHETIC_FIXTURE,
}
_HISTORICAL_DATA_BEARING_MARKERS = (
    b"crv1-",
    b"crv2-",
    b"crv3-",
    b"crv4-",
    b"synthetic-calibration-redesign-v4",
    b"bounded-platt-scaling-v1",
    b"regularized-isotonic-calibration-v4",
)


class CalibrationSuccessorV5RegistryViolationCode(StrEnum):
    """Machine-readable V5 fixture-governance violations."""

    REGISTRY_SCHEMA_ERROR = "calibration_successor_v5_registry_schema_error"
    REGISTRY_PROVENANCE_MISMATCH = "calibration_successor_v5_registry_provenance_mismatch"
    HISTORICAL_EVIDENCE_REFERENCE = "calibration_successor_v5_historical_evidence_reference"
    SCHEMA_ONLY_BOUNDARY_VIOLATION = "calibration_successor_v5_schema_only_boundary_violation"
    CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION = (
        "calibration_successor_v5_calibration_curve_coverage_boundary_violation"
    )
    CALIBRATION_POSITION_SPREAD_BOUNDARY_VIOLATION = (
        "calibration_successor_v5_calibration_position_spread_boundary_violation"
    )
    CALIBRATION_WORKLOAD_VARIATION_BOUNDARY_VIOLATION = (
        "calibration_successor_v5_calibration_workload_variation_boundary_violation"
    )
    CALIBRATION_MIXED_RELIABILITY_CONTRAST_BOUNDARY_VIOLATION = (
        "calibration_successor_v5_calibration_mixed_reliability_contrast_boundary_violation"
    )
    CALIBRATION_MANIFEST_BOUNDARY_VIOLATION = (
        "calibration_successor_v5_calibration_manifest_boundary_violation"
    )


class CalibrationSuccessorV5RegistryLoadError(ValueError):
    """Raised when V5 registry metadata or an active fixture root is invalid."""

    def __init__(
        self,
        code: CalibrationSuccessorV5RegistryViolationCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class CalibrationSuccessorV5ObservationBudget(StrictContract):
    """Predeclared V5 corpus sizes, fixed before any final evidence exists."""

    calibration_case_count: Literal[48]
    final_evaluation_case_count: Literal[36]
    adversarial_regression_case_count: Literal[12]
    candidate_positions_per_case: Literal[4]
    calibration_observation_count: Literal[192]
    final_evaluation_observation_count: Literal[144]
    adversarial_regression_observation_count: Literal[48]


class CalibrationSuccessorV5WorkloadAllocation(StrictContract):
    """Fixed workload balance required for each future final-evaluation family."""

    structured_text_case_count: Literal[3]
    code_case_count: Literal[3]
    open_ended_chat_case_count: Literal[3]


class CalibrationSuccessorV5ScenarioFamilyRecord(StrictContract):
    """A V5 family reservation and its currently authorised authoring state."""

    scenario_family_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    primary_data_role: TraceDataRole
    reserved_case_ids: tuple[str, ...] = Field(min_length=1)
    rationale: str = Field(min_length=1, max_length=500)
    target_failure_modes: tuple[str, ...] = Field(min_length=1)
    is_final_evaluation_quarantined: bool
    is_adversarial_regression_quarantined: bool
    workload_allocation: CalibrationSuccessorV5WorkloadAllocation | None = None
    authoring_status: Literal[
        "reserved_for_v5_case_authoring",
        "calibration_curve_coverage_authored",
        "calibration_position_spread_authored",
        "calibration_workload_variation_authored",
        "calibration_mixed_reliability_contrast_authored",
        "calibration_manifest_frozen",
    ]

    @field_validator("reserved_case_ids")
    @classmethod
    def validate_reserved_case_ids(cls, case_ids: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("V5 case IDs must be unique within one family")
        if any(not case_id.startswith("CSV5-") for case_id in case_ids):
            raise ValueError("V5 case IDs must use the CSV5 namespace")
        return case_ids

    @field_validator("target_failure_modes")
    @classmethod
    def validate_target_failure_modes(
        cls,
        failure_modes: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(set(failure_modes)) != len(failure_modes):
            raise ValueError("V5 target failure modes must be unique within one family")
        return failure_modes

    @model_validator(mode="after")
    def validate_family_governance(
        self,
    ) -> CalibrationSuccessorV5ScenarioFamilyRecord:
        if not self.scenario_family_id.startswith("CSV5-"):
            raise ValueError("V5 scenario-family IDs must use the CSV5 namespace")
        if self.primary_data_role is not _EXPECTED_DATA_ROLE_BY_SPLIT[self.split]:
            raise ValueError("primary_data_role must match the governed V5 split role")
        if self.is_final_evaluation_quarantined is not (self.split is TraceSplit.FINAL_EVALUATION):
            raise ValueError("final-evaluation quarantine must match the V5 split")
        if self.is_adversarial_regression_quarantined is not (
            self.split is TraceSplit.ADVERSARIAL_REGRESSION
        ):
            raise ValueError("adversarial-regression quarantine must match the V5 split")
        if (self.workload_allocation is not None) is not (
            self.split is TraceSplit.FINAL_EVALUATION
        ):
            raise ValueError("only final-evaluation families may declare workload allocation")
        return self


class CalibrationSuccessorV5ScenarioFamilyRegistry(StrictContract):
    """V5 registry with a fail-closed progression from schema-only to curve coverage."""

    schema_version: Literal["calibration-successor-v5-scenario-family-registry-v1"]
    registry_status: Literal[
        "schema_only",
        "calibration_curve_coverage_authored",
        "calibration_position_spread_authored",
        "calibration_workload_variation_authored",
        "calibration_mixed_reliability_contrast_authored",
        "calibration_manifest_frozen",
    ]
    fixture_set_id: Literal["synthetic-calibration-successor-v5"]
    fixture_set_version: Literal["1.0.0"]
    source_type: Literal[TraceSourceType.SYNTHETIC]
    method_constitution_version: Literal[
        "v5-bounded-monotone-beta-calibration-eligibility-charter-v1"
    ]
    calibration_method_id: Literal["bounded-monotone-beta-calibration-v5"]
    maximum_candidate_positions: Literal[4]
    historical_data_bearing_evidence_used: Literal[False]
    v5_runtime_or_outcome_assets_authored: bool
    v5_calibration_manifest_authored: bool
    frozen_calibration_manifest_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    frozen_calibration_pre_freeze_registry_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )
    v5_calibration_artifact_authored: Literal[False]
    v5_calibration_fit_diagnostics_authored: Literal[False]
    v5_final_evaluation_runtime_or_outcome_assets_authored: Literal[False]
    v5_final_evaluation_manifest_authored: Literal[False]
    v5_final_assessment_contract_merged: Literal[True]
    v5_final_heldout_calibration_assessment_authored: Literal[False]
    observation_budget: CalibrationSuccessorV5ObservationBudget
    families: tuple[CalibrationSuccessorV5ScenarioFamilyRecord, ...] = Field(
        min_length=10,
        max_length=10,
    )
    explicit_exclusions: tuple[str, ...] = Field(min_length=8)
    next_authorized_artifact: Literal[
        "v5-calibration-curve-coverage-fixtures",
        "v5-calibration-position-spread-fixtures",
        "v5-calibration-workload-variation-fixtures",
        "v5-calibration-mixed-reliability-contrast-fixtures",
        "v5-calibration-manifest-freeze",
        "v5-bounded-monotone-beta-fit-diagnostics",
    ]

    @model_validator(mode="after")
    def validate_registry_governance(
        self,
    ) -> CalibrationSuccessorV5ScenarioFamilyRegistry:
        if self.historical_data_bearing_evidence_used:
            raise ValueError("historical data-bearing evidence is prohibited in V5")
        if (
            self.registry_status != "calibration_manifest_frozen"
            and self.v5_calibration_manifest_authored
        ):
            raise ValueError("only the V5 manifest stage may claim a calibration manifest")
        if self.v5_calibration_artifact_authored:
            raise ValueError("V5-3b does not author a calibration artifact")
        if self.v5_calibration_fit_diagnostics_authored:
            raise ValueError("V5-3b does not author fit diagnostics")
        if self.v5_final_evaluation_runtime_or_outcome_assets_authored:
            raise ValueError("V5-3b does not author final-evaluation assets")
        if self.v5_final_evaluation_manifest_authored:
            raise ValueError("V5-3b does not author a final-evaluation manifest")
        if self.v5_final_heldout_calibration_assessment_authored:
            raise ValueError("V5-3b does not author a final held-out assessment")

        family_ids = tuple(family.scenario_family_id for family in self.families)
        if len(set(family_ids)) != len(family_ids) or set(family_ids) != _V5_EXPECTED_FAMILY_IDS:
            raise ValueError("V5 scenario-family IDs must match the complete reserved plan")
        all_case_ids = tuple(
            case_id for family in self.families for case_id in family.reserved_case_ids
        )
        if len(set(all_case_ids)) != len(all_case_ids):
            raise ValueError("V5 case IDs must be unique across all families")
        for family in self.families:
            if (
                family.reserved_case_ids
                != _V5_EXPECTED_CASE_IDS_BY_FAMILY[family.scenario_family_id]
            ):
                raise ValueError("V5 family case IDs must match fixed reservation ranges")

        split_case_counts = {
            split: sum(
                len(family.reserved_case_ids) for family in self.families if family.split is split
            )
            for split in _EXPECTED_DATA_ROLE_BY_SPLIT
        }
        if split_case_counts != {
            TraceSplit.CALIBRATION: 48,
            TraceSplit.FINAL_EVALUATION: 36,
            TraceSplit.ADVERSARIAL_REGRESSION: 12,
        }:
            raise ValueError("V5 split case counts must match the fixed corpus budget")

        final_families = tuple(
            family for family in self.families if family.split is TraceSplit.FINAL_EVALUATION
        )
        if len(final_families) != 4 or any(
            len(family.reserved_case_ids) != 9 for family in final_families
        ):
            raise ValueError("each V5 final family must reserve exactly nine cases")
        if any(family.workload_allocation is None for family in final_families):
            raise ValueError("each V5 final family requires fixed workload allocation")

        curve_family = next(
            family
            for family in self.families
            if family.scenario_family_id == "CSV5-CAL-CURVE-COVERAGE"
        )
        base_exclusions = {
            "No V5 calibration artifact, fit diagnostic, or final assessment result is present.",
            "No V5 fitter, threshold selection, or parameter mutation is authorized.",
            "No V5 scheduler, baseline comparison, capacity profile, utility scorer, "
            "or runtime control is authorized.",
            "No historical data-bearing evidence influenced V5 fixture reservations.",
            "V5 final-evaluation and adversarial reservations remain quarantined.",
            (
                "The V5 final-assessment contract does not authorize evidence loading "
                "or assessment execution."
            ),
        }
        if not base_exclusions.issubset(set(self.explicit_exclusions)):
            raise ValueError("V5 registry must retain its stage exclusions")
        if self.registry_status != "calibration_manifest_frozen" and (
            "No V5 calibration or final-evaluation manifest is present."
            not in self.explicit_exclusions
        ):
            raise ValueError("pre-freeze V5 must state that no manifest exists")

        position_family = next(
            family
            for family in self.families
            if family.scenario_family_id == "CSV5-CAL-POSITION-SPREAD"
        )
        workload_family = next(
            family
            for family in self.families
            if family.scenario_family_id == "CSV5-CAL-WORKLOAD-VARIATION"
        )
        mixed_reliability_family = next(
            family
            for family in self.families
            if family.scenario_family_id == "CSV5-CAL-MIXED-RELIABILITY-CONTRAST"
        )
        remaining_families = tuple(
            family
            for family in self.families
            if family
            not in (
                curve_family,
                position_family,
                workload_family,
                mixed_reliability_family,
            )
        )

        if self.registry_status == "schema_only":
            if self.v5_runtime_or_outcome_assets_authored:
                raise ValueError("schema-only V5 cannot claim authored case assets")
            if curve_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("schema-only V5 must retain curve coverage as reserved")
            if position_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("schema-only V5 must retain position spread as reserved")
            if workload_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("schema-only V5 must retain workload variation as reserved")
            if mixed_reliability_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("schema-only V5 must retain mixed reliability as reserved")
            if any(
                family.authoring_status != "reserved_for_v5_case_authoring"
                for family in remaining_families
            ):
                raise ValueError("schema-only V5 cannot claim any authored family")
            if self.next_authorized_artifact != "v5-calibration-curve-coverage-fixtures":
                raise ValueError("schema-only V5 must authorize curve coverage next")
            if (
                "No V5 runtime-input or expected-outcome assets are present."
                not in self.explicit_exclusions
            ):
                raise ValueError("schema-only V5 must state that no case assets exist")
            return self

        if not self.v5_runtime_or_outcome_assets_authored:
            raise ValueError("authored V5 stages require runtime and outcome case pairs")
        if curve_family.authoring_status != "calibration_curve_coverage_authored":
            raise ValueError("curve-coverage family must remain marked authored")

        if self.registry_status == "calibration_curve_coverage_authored":
            if position_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("V5-3b must retain position spread as reserved")
            if workload_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("V5-3b must retain workload variation as reserved")
            if mixed_reliability_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("V5-3b must retain mixed reliability as reserved")
            if any(
                family.authoring_status != "reserved_for_v5_case_authoring"
                for family in remaining_families
            ):
                raise ValueError("only curve coverage may be authored at V5-3b")
            if self.next_authorized_artifact != "v5-calibration-position-spread-fixtures":
                raise ValueError("V5-3b must authorize position-spread fixtures next")
            if (
                "Only CSV5-101..CSV5-112 runtime-input and expected-outcome case pairs "
                "are authored." not in self.explicit_exclusions
            ):
                raise ValueError("V5-3b must state its exact authored-case boundary")
            return self

        if position_family.authoring_status != "calibration_position_spread_authored":
            raise ValueError("position-spread family must remain marked authored")

        if self.registry_status == "calibration_position_spread_authored":
            if workload_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("V5-3c must retain workload variation as reserved")
            if mixed_reliability_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("V5-3c must retain mixed reliability as reserved")
            if any(
                family.authoring_status != "reserved_for_v5_case_authoring"
                for family in remaining_families
            ):
                raise ValueError("only curve coverage and position spread may be authored at V5-3c")
            if self.next_authorized_artifact != "v5-calibration-workload-variation-fixtures":
                raise ValueError("V5-3c must authorize workload-variation fixtures next")
            if (
                "Only CSV5-101..CSV5-124 runtime-input and expected-outcome case pairs "
                "are authored." not in self.explicit_exclusions
            ):
                raise ValueError("V5-3c must state its exact authored-case boundary")
            return self

        if workload_family.authoring_status != "calibration_workload_variation_authored":
            raise ValueError("workload-variation family must be marked authored at V5-3d")

        if self.registry_status == "calibration_workload_variation_authored":
            if mixed_reliability_family.authoring_status != "reserved_for_v5_case_authoring":
                raise ValueError("V5-3d must retain mixed reliability as reserved")
            if any(
                family.authoring_status != "reserved_for_v5_case_authoring"
                for family in remaining_families
            ):
                raise ValueError(
                    "only curve coverage, position spread, and workload variation may be authored "
                    "at V5-3d"
                )
            if (
                self.next_authorized_artifact
                != "v5-calibration-mixed-reliability-contrast-fixtures"
            ):
                raise ValueError("V5-3d must authorize mixed-reliability fixtures next")
            if (
                "Only CSV5-101..CSV5-136 runtime-input and expected-outcome case pairs "
                "are authored." not in self.explicit_exclusions
            ):
                raise ValueError("V5-3d must state its exact authored-case boundary")
            return self

        if (
            mixed_reliability_family.authoring_status
            != "calibration_mixed_reliability_contrast_authored"
        ):
            raise ValueError("mixed-reliability family must be marked authored at V5-3e")
        if any(
            family.authoring_status != "reserved_for_v5_case_authoring"
            for family in remaining_families
        ):
            raise ValueError("only calibration families may be authored at V5")
        if (
            "Only CSV5-101..CSV5-148 runtime-input and expected-outcome case pairs "
            "are authored." not in self.explicit_exclusions
        ):
            raise ValueError("V5 must state its exact authored-case boundary")

        if self.registry_status == "calibration_mixed_reliability_contrast_authored":
            if self.next_authorized_artifact != "v5-calibration-manifest-freeze":
                raise ValueError("V5-3e must authorize calibration-manifest freeze next")
            if self.v5_calibration_manifest_authored:
                raise ValueError("V5-3e must not claim a frozen calibration manifest")
            if (
                self.frozen_calibration_manifest_sha256 is not None
                or self.frozen_calibration_pre_freeze_registry_sha256 is not None
            ):
                raise ValueError("V5-3e must not carry manifest provenance hashes")
            return self

        if self.registry_status != "calibration_manifest_frozen":
            raise ValueError("V5 registry status is not authorised")
        if not self.v5_calibration_manifest_authored:
            raise ValueError("V5 manifest stage requires a frozen calibration manifest")
        if self.frozen_calibration_manifest_sha256 is None:
            raise ValueError("V5 manifest stage requires the manifest SHA-256")
        if self.frozen_calibration_pre_freeze_registry_sha256 is None:
            raise ValueError("V5 manifest stage requires pre-freeze registry provenance")
        if self.next_authorized_artifact != "v5-bounded-monotone-beta-fit-diagnostics":
            raise ValueError("V5 manifest stage must authorize fit diagnostics next")
        if (
            "V5 calibration manifest is frozen and hash-addressed; final-evaluation "
            "and adversarial reservations remain quarantined." not in self.explicit_exclusions
        ):
            raise ValueError("V5 manifest stage must state its frozen calibration boundary")
        return self


def load_calibration_successor_v5_scenario_family_registry(
    path: Path,
    *,
    allow_calibration_curve_coverage_assets: bool = False,
    allow_calibration_position_spread_assets: bool = False,
    allow_calibration_workload_variation_assets: bool = False,
    allow_calibration_mixed_reliability_contrast_assets: bool = False,
    allow_calibration_manifest_assets: bool = False,
) -> CalibrationSuccessorV5ScenarioFamilyRegistry:
    """Load V5 registry only through one explicit active evidence boundary."""

    active_boundary_count = sum(
        (
            allow_calibration_curve_coverage_assets,
            allow_calibration_position_spread_assets,
            allow_calibration_workload_variation_assets,
            allow_calibration_mixed_reliability_contrast_assets,
            allow_calibration_manifest_assets,
        )
    )
    if active_boundary_count > 1:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 registry loading must select exactly one authored evidence boundary",
        )

    root = path.parent.resolve()
    if allow_calibration_manifest_assets:
        assert_calibration_successor_v5_calibration_manifest_fixture_root(root)
    elif allow_calibration_mixed_reliability_contrast_assets:
        assert_calibration_successor_v5_calibration_mixed_reliability_contrast_fixture_root(root)
    elif allow_calibration_workload_variation_assets:
        assert_calibration_successor_v5_calibration_workload_variation_fixture_root(root)
    elif allow_calibration_position_spread_assets:
        assert_calibration_successor_v5_calibration_position_spread_fixture_root(root)
    elif allow_calibration_curve_coverage_assets:
        assert_calibration_successor_v5_calibration_curve_coverage_fixture_root(root)
    else:
        assert_calibration_successor_v5_schema_only_fixture_root(root)
    if path.resolve() != root / _V5_REGISTRY_FILENAME:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 registry must be loaded from scenario_family_registry.json at its fixture root",
        )
    try:
        raw_bytes = path.read_bytes()
    except OSError as error:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            f"unable to read V5 scenario-family registry: {error}",
        ) from error
    _reject_historical_data_bearing_reference(raw_bytes)
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
            f"V5 scenario-family registry is not valid UTF-8 JSON: {error}",
        ) from error
    try:
        registry = CalibrationSuccessorV5ScenarioFamilyRegistry.model_validate(payload)
    except ValidationError as error:
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_SCHEMA_ERROR,
            f"V5 scenario-family registry validation failed: {error}",
        ) from error
    if allow_calibration_manifest_assets:
        if registry.registry_status != "calibration_manifest_frozen":
            raise CalibrationSuccessorV5RegistryLoadError(
                CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_MANIFEST_BOUNDARY_VIOLATION,
                "V5 registry has not reached the calibration-manifest boundary",
            )
        return registry
    if allow_calibration_mixed_reliability_contrast_assets:
        if registry.registry_status != "calibration_mixed_reliability_contrast_authored":
            raise CalibrationSuccessorV5RegistryLoadError(
                (
                    CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_MIXED_RELIABILITY_CONTRAST_BOUNDARY_VIOLATION
                ),
                "V5 registry has not reached the mixed-reliability evidence boundary",
            )
        return registry
    if allow_calibration_workload_variation_assets:
        if registry.registry_status != "calibration_workload_variation_authored":
            raise CalibrationSuccessorV5RegistryLoadError(
                (
                    CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_WORKLOAD_VARIATION_BOUNDARY_VIOLATION
                ),
                "V5 registry has not reached the workload-variation evidence boundary",
            )
        return registry
    if allow_calibration_position_spread_assets:
        if registry.registry_status != "calibration_position_spread_authored":
            raise CalibrationSuccessorV5RegistryLoadError(
                (
                    CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_POSITION_SPREAD_BOUNDARY_VIOLATION
                ),
                "V5 registry has not reached the position-spread evidence boundary",
            )
        return registry
    if allow_calibration_curve_coverage_assets:
        if registry.registry_status != "calibration_curve_coverage_authored":
            raise CalibrationSuccessorV5RegistryLoadError(
                (
                    CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION
                ),
                "V5 registry has advanced beyond the curve-coverage evidence boundary",
            )
        return registry
    raise CalibrationSuccessorV5RegistryLoadError(
        CalibrationSuccessorV5RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION,
        "V5 registry has advanced beyond the schema-only boundary",
    )


def assert_calibration_successor_v5_schema_only_fixture_root(root: Path) -> None:
    """Reject case-bearing assets when a caller requests the obsolete schema-only stage."""

    _assert_root_layout(
        root,
        allowed_root_names=_V5_ROOT_METADATA_FILENAMES,
        expected_case_ids=(),
        violation_code=CalibrationSuccessorV5RegistryViolationCode.SCHEMA_ONLY_BOUNDARY_VIOLATION,
        boundary_name="schema-only",
    )


def assert_calibration_successor_v5_calibration_curve_coverage_fixture_root(
    root: Path,
) -> None:
    """Validate exactly the first twelve calibration case pairs and no later assets."""

    _assert_root_layout(
        root,
        allowed_root_names=_V5_ROOT_METADATA_FILENAMES,
        expected_case_ids=_V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
        violation_code=(
            CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_CURVE_COVERAGE_BOUNDARY_VIOLATION
        ),
        boundary_name="calibration curve coverage",
    )


def assert_calibration_successor_v5_calibration_position_spread_fixture_root(
    root: Path,
) -> None:
    """Validate the first twenty-four V5 calibration case pairs and no later assets."""

    _assert_root_layout(
        root,
        allowed_root_names=_V5_ROOT_METADATA_FILENAMES,
        expected_case_ids=(
            *_V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
            *_V5_CALIBRATION_POSITION_SPREAD_CASE_IDS,
        ),
        violation_code=(
            CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_POSITION_SPREAD_BOUNDARY_VIOLATION
        ),
        boundary_name="calibration position spread",
    )


def assert_calibration_successor_v5_calibration_workload_variation_fixture_root(
    root: Path,
) -> None:
    """Validate the first thirty-six V5 calibration pairs and no later assets."""

    _assert_root_layout(
        root,
        allowed_root_names=_V5_ROOT_METADATA_FILENAMES,
        expected_case_ids=(
            *_V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
            *_V5_CALIBRATION_POSITION_SPREAD_CASE_IDS,
            *_V5_CALIBRATION_WORKLOAD_VARIATION_CASE_IDS,
        ),
        violation_code=(
            CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_WORKLOAD_VARIATION_BOUNDARY_VIOLATION
        ),
        boundary_name="calibration workload variation",
    )


def assert_calibration_successor_v5_calibration_mixed_reliability_contrast_fixture_root(
    root: Path,
) -> None:
    """Validate all forty-eight V5 calibration pairs and no later assets."""

    _assert_root_layout(
        root,
        allowed_root_names=_V5_ROOT_METADATA_FILENAMES,
        expected_case_ids=(
            *_V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
            *_V5_CALIBRATION_POSITION_SPREAD_CASE_IDS,
            *_V5_CALIBRATION_WORKLOAD_VARIATION_CASE_IDS,
            *_V5_CALIBRATION_MIXED_RELIABILITY_CONTRAST_CASE_IDS,
        ),
        violation_code=(
            CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_MIXED_RELIABILITY_CONTRAST_BOUNDARY_VIOLATION
        ),
        boundary_name="calibration mixed reliability contrast",
    )


def assert_calibration_successor_v5_calibration_manifest_fixture_root(
    root: Path,
) -> None:
    """Validate all calibration assets plus one immutable V5 calibration manifest."""

    _assert_root_layout(
        root,
        allowed_root_names={
            *_V5_ROOT_METADATA_FILENAMES,
            _V5_CALIBRATION_MANIFEST_FILENAME,
        },
        expected_case_ids=(
            *_V5_CALIBRATION_CURVE_COVERAGE_CASE_IDS,
            *_V5_CALIBRATION_POSITION_SPREAD_CASE_IDS,
            *_V5_CALIBRATION_WORKLOAD_VARIATION_CASE_IDS,
            *_V5_CALIBRATION_MIXED_RELIABILITY_CONTRAST_CASE_IDS,
        ),
        violation_code=(
            CalibrationSuccessorV5RegistryViolationCode.CALIBRATION_MANIFEST_BOUNDARY_VIOLATION
        ),
        boundary_name="calibration manifest",
    )


def _assert_root_layout(
    root: Path,
    *,
    allowed_root_names: set[str],
    expected_case_ids: tuple[str, ...],
    violation_code: CalibrationSuccessorV5RegistryViolationCode,
    boundary_name: str,
) -> None:
    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
            "V5 fixture root must be an existing directory",
        )
    expected_root_names = set(allowed_root_names)
    if expected_case_ids:
        expected_root_names.update({"inputs", "expected_outcomes"})
    present_names = {child.name for child in resolved_root.iterdir()}
    unexpected_names = present_names ^ expected_root_names
    if unexpected_names:
        raise CalibrationSuccessorV5RegistryLoadError(
            violation_code,
            f"V5 {boundary_name} root has unexpected or missing paths: "
            + ", ".join(sorted(unexpected_names)),
        )
    for filename in sorted(allowed_root_names):
        try:
            _reject_historical_data_bearing_reference((resolved_root / filename).read_bytes())
        except OSError as error:
            raise CalibrationSuccessorV5RegistryLoadError(
                CalibrationSuccessorV5RegistryViolationCode.REGISTRY_PROVENANCE_MISMATCH,
                f"unable to read V5 metadata {filename}: {error}",
            ) from error
    if not expected_case_ids:
        return
    _assert_case_directory(
        resolved_root / "inputs" / "cases",
        expected_case_ids,
        violation_code,
        boundary_name,
    )
    _assert_case_directory(
        resolved_root / "expected_outcomes" / "cases",
        expected_case_ids,
        violation_code,
        boundary_name,
    )
    for container in (resolved_root / "inputs", resolved_root / "expected_outcomes"):
        if {child.name for child in container.iterdir()} != {"cases"}:
            raise CalibrationSuccessorV5RegistryLoadError(
                violation_code,
                f"V5 {boundary_name} asset container has unexpected paths",
            )


def _assert_case_directory(
    path: Path,
    expected_case_ids: tuple[str, ...],
    violation_code: CalibrationSuccessorV5RegistryViolationCode,
    boundary_name: str,
) -> None:
    if not path.is_dir():
        raise CalibrationSuccessorV5RegistryLoadError(
            violation_code,
            f"V5 {boundary_name} case directory is missing: {path}",
        )
    expected_filenames = {f"{case_id}.json" for case_id in expected_case_ids}
    actual_filenames = {child.name for child in path.iterdir() if child.is_file()}
    if actual_filenames != expected_filenames or any(child.is_dir() for child in path.iterdir()):
        raise CalibrationSuccessorV5RegistryLoadError(
            violation_code,
            f"V5 {boundary_name} case IDs do not match the active reservation",
        )


def _reject_historical_data_bearing_reference(raw_bytes: bytes) -> None:
    normalized = raw_bytes.lower()
    if any(marker in normalized for marker in _HISTORICAL_DATA_BEARING_MARKERS):
        raise CalibrationSuccessorV5RegistryLoadError(
            CalibrationSuccessorV5RegistryViolationCode.HISTORICAL_EVIDENCE_REFERENCE,
            "V5 assets must not reference historical data-bearing evidence",
        )
