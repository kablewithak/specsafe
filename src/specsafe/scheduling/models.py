"""Policy provenance and control contracts for SpecSafe replay.

These contracts preserve the distinction between capacity-blind baselines and the
research-only calibrated causal load-aware policy. They retain immutable policy identity,
configuration provenance, retained V5 calibration authorization, and declared synthetic
capacity-profile identity without making a policy-comparison or promotion claim.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from pydantic import Field, model_validator

from specsafe.capacity_profiles import CapacityProfileKind, SyntheticCapacityProfile
from specsafe.contracts.models import StrictContract

if TYPE_CHECKING:
    from specsafe.scheduling.policies import (
        CalibratedCausalLoadAwarePolicyConfig,
        FixedLengthPolicyConfig,
        StaticThresholdPolicyConfig,
    )


class BaselinePolicyKind(StrEnum):
    """Valid baseline families currently authorized for controlled replay."""

    FIXED_LENGTH = "fixed_length"
    STATIC_THRESHOLD = "static_threshold"


class AdaptivePolicyKind(StrEnum):
    """The controlled adaptive-policy family authorized after the V5 gate."""

    CALIBRATED_CAUSAL_LOAD_AWARE = "calibrated_causal_load_aware"


class PolicyClassification(StrEnum):
    """Promotion classification for a retained policy descriptor."""

    VALID_BASELINE = "valid_baseline"
    VALID_ADAPTIVE_POLICY = "valid_adaptive_policy"


class PolicyCapacitySensitivity(StrEnum):
    """Whether a policy rule changes its decision from capacity conditions."""

    CAPACITY_BLIND = "capacity_blind"
    CAPACITY_AWARE = "capacity_aware"


class PolicyPromotionEligibility(StrEnum):
    """The strongest promotion boundary for the policy contract in this slice."""

    REPLAY_EVALUATION_ONLY = "replay_evaluation_only"


class CalibratedPolicyControlMode(StrEnum):
    """Whether a policy may use the retained V5 calibrator or must fall back."""

    CALIBRATED_RESEARCH_ONLY = "calibrated_research_only"
    CONSERVATIVE_FALLBACK = "conservative_fallback"


class CalibratedCausalLoadAwarePolicyErrorCode(StrEnum):
    """Machine-readable failures at the adaptive-policy dependency boundary."""

    INVALID_POLICY_CONFIG = "invalid_calibrated_policy_config"
    INVALID_CALIBRATION_ARTIFACT = "invalid_calibration_artifact"
    CALIBRATION_ARTIFACT_MISMATCH = "calibration_artifact_mismatch"
    INVALID_CAPACITY_PROFILE = "invalid_capacity_profile"
    CAPACITY_PROFILE_MISMATCH = "capacity_profile_mismatch"


class BaselinePolicyDescriptor(StrictContract):
    """Immutable normalized identity for one causal capacity-blind baseline.

    The descriptor deliberately does not include utility, capacity outcome, or winner
    fields. It records only a valid baseline's declared behavior and exact configuration
    identity for later governed comparison work.
    """

    policy_id: str = Field(min_length=1, max_length=128)
    policy_kind: BaselinePolicyKind
    classification: Literal[PolicyClassification.VALID_BASELINE] = (
        PolicyClassification.VALID_BASELINE
    )
    capacity_sensitivity: Literal[PolicyCapacitySensitivity.CAPACITY_BLIND] = (
        PolicyCapacitySensitivity.CAPACITY_BLIND
    )
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class V5RetainedCalibrationAuthorization(StrictContract):
    """Minimal label-free authorization for controlled V5 policy research.

    This contract intentionally retains only immutable assessment provenance and the
    retained artifact identity. It does not contain held-out trace labels, outcomes,
    utility results, or policy-comparison fields.
    """

    authorization_id: Literal["v5-controlled-policy-research-authorization-v1"] = (
        "v5-controlled-policy-research-authorization-v1"
    )
    assessment_result_relative_path: Literal[
        "evidence/heldout-calibration/v5-final-heldout-calibration-assessment-v1/result.json"
    ] = "evidence/heldout-calibration/v5-final-heldout-calibration-assessment-v1/result.json"
    assessment_result_sha256: Literal[
        "f985ef8df30a5d920194a05f7d5115431420f8ed40a1252d33af62f5d0882ab9"
    ] = "f985ef8df30a5d920194a05f7d5115431420f8ed40a1252d33af62f5d0882ab9"
    calibration_artifact_sha256: Literal[
        "a3baeb2db94221d68a69fc757c8865e384e3ac92ca05585919188fe1c744cd14"
    ] = "a3baeb2db94221d68a69fc757c8865e384e3ac92ca05585919188fe1c744cd14"
    assessment_status: Literal["PASSES_V5_CALIBRATION_ELIGIBILITY_GATE"] = (
        "PASSES_V5_CALIBRATION_ELIGIBILITY_GATE"
    )
    adaptive_policy_research_eligibility: Literal["eligible_for_controlled_policy_research"] = (
        "eligible_for_controlled_policy_research"
    )
    runtime_control_eligible: Literal[False] = False
    calibration_refit_performed: Literal[False] = False
    assessment_policy_or_replay_execution_performed: Literal[False] = False


class SyntheticCapacityProfileReference(StrictContract):
    """Hash-addressed identity for one declared synthetic policy input profile."""

    profile_id: str = Field(min_length=1, max_length=128)
    profile_version: str = Field(min_length=1, max_length=64)
    profile_kind: CapacityProfileKind
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @classmethod
    def from_profile(cls, profile: SyntheticCapacityProfile) -> SyntheticCapacityProfileReference:
        """Derive an exact retained reference from a validated synthetic profile."""

        if type(profile) is not SyntheticCapacityProfile:
            raise TypeError(
                "synthetic capacity-profile reference requires the exact "
                "SyntheticCapacityProfile contract"
            )
        return cls(
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            profile_kind=profile.profile_kind,
            configuration_sha256=profile.configuration_sha256(),
        )


class CalibratedCausalLoadAwarePolicyDescriptor(StrictContract):
    """Inspectable identity for the research-only valid adaptive policy.

    It records no observed outcomes, cross-policy result, winner, capacity claim, or
    promotion beyond replay evaluation. A valid decision remains governed separately by
    the causal runtime guard.
    """

    policy_id: str = Field(min_length=1, max_length=128)
    policy_kind: Literal[AdaptivePolicyKind.CALIBRATED_CAUSAL_LOAD_AWARE] = (
        AdaptivePolicyKind.CALIBRATED_CAUSAL_LOAD_AWARE
    )
    classification: Literal[PolicyClassification.VALID_ADAPTIVE_POLICY] = (
        PolicyClassification.VALID_ADAPTIVE_POLICY
    )
    capacity_sensitivity: Literal[PolicyCapacitySensitivity.CAPACITY_AWARE] = (
        PolicyCapacitySensitivity.CAPACITY_AWARE
    )
    promotion_eligibility: Literal[PolicyPromotionEligibility.REPLAY_EVALUATION_ONLY] = (
        PolicyPromotionEligibility.REPLAY_EVALUATION_ONLY
    )
    control_mode: CalibratedPolicyControlMode
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_artifact_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    capacity_profile_configuration_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-f0-9]{64}$",
    )

    @model_validator(mode="after")
    def validate_descriptor_control_mode(self) -> CalibratedCausalLoadAwarePolicyDescriptor:
        """Ensure a fallback descriptor cannot masquerade as calibrated control."""

        if self.control_mode is CalibratedPolicyControlMode.CALIBRATED_RESEARCH_ONLY:
            if (
                self.calibration_artifact_sha256 is None
                or self.capacity_profile_configuration_sha256 is None
            ):
                raise ValueError(
                    "calibrated research descriptor requires retained calibration and "
                    "capacity-profile hashes"
                )
        elif (
            self.calibration_artifact_sha256 is not None
            or self.capacity_profile_configuration_sha256 is not None
        ):
            raise ValueError(
                "conservative fallback descriptor must not retain active calibrated-control "
                "dependencies"
            )
        return self


def configuration_sha256(
    config: FixedLengthPolicyConfig
    | StaticThresholdPolicyConfig
    | CalibratedCausalLoadAwarePolicyConfig,
) -> str:
    """Return the stable evidence hash for one immutable policy configuration."""

    canonical_json = json.dumps(
        config.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(f"{canonical_json}\n".encode()).hexdigest()
