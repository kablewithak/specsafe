"""Blunt baselines, controlled adaptive policy, and isolated unsafe controls.

Valid policies accept an object only so the causal gate can reject accidental non-causal
inputs. After the gate passes, each valid policy uses the exact CausalSchedulerContext
and never consumes replay outcomes, sampled candidate tokens, or later decision state.

The calibrated causal load-aware policy is explicitly research-only. It may use the one
retained V5 calibration artifact and one declared synthetic capacity profile. It cannot
fit calibration, read held-out labels, choose a comparison winner, claim runtime control,
or bypass conservative fallback.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import Field, model_validator

from specsafe.capacity_profiles import CapacityProfileError, SyntheticCapacityProfile
from specsafe.causal_safety import require_causal_runtime_context
from specsafe.causal_safety.unsafe_controls import RetrospectiveEvaluationContext
from specsafe.contracts import (
    CausalSafetyStatus,
    CausalSchedulerContext,
    VerificationAction,
    VerificationDecision,
)
from specsafe.contracts.models import StrictContract
from specsafe.heldout_calibration.v5_final_assessment import (
    V5BoundedMonotoneBetaCalibrationArtifact,
    calculate_v5_bounded_monotone_beta_probability,
)
from specsafe.scheduling.models import (
    BaselinePolicyDescriptor,
    BaselinePolicyKind,
    CalibratedCausalLoadAwarePolicyDescriptor,
    CalibratedCausalLoadAwarePolicyErrorCode,
    CalibratedPolicyControlMode,
    SyntheticCapacityProfileReference,
    V5RetainedCalibrationAuthorization,
    configuration_sha256,
)
from specsafe.traces.bounded_monotone_beta_calibration_v5 import (
    canonical_v5_bounded_monotone_beta_artifact_json,
)


class FixedLengthPolicyConfig(StrictContract):
    """Configuration for the capacity-blind fixed verification-length baseline."""

    policy_id: str = Field(default="fixed-length-v1", min_length=1, max_length=128)
    maximum_verification_length: int = Field(ge=1)

    def configuration_sha256(self) -> str:
        """Return a stable hash for this immutable baseline configuration."""

        return configuration_sha256(self)


class StaticThresholdPolicyConfig(StrictContract):
    """Configuration for the causal but capacity-blind threshold baseline."""

    policy_id: str = Field(default="static-threshold-v1", min_length=1, max_length=128)
    minimum_conditional_survival_confidence: float = Field(ge=0.0, le=1.0)

    def configuration_sha256(self) -> str:
        """Return a stable hash for this immutable baseline configuration."""

        return configuration_sha256(self)


class CalibratedCausalLoadAwarePolicyConfig(StrictContract):
    """Research-only configuration for the controlled adaptive policy.

    In calibrated mode, the configuration must reference the exact retained V5
    authorization and one hash-addressed synthetic capacity profile. In fallback mode,
    no calibrated-control dependency may be supplied and the policy will emit only a
    causal conservative-fallback decision.
    """

    policy_id: str = Field(
        default="calibrated-causal-load-aware-v5",
        min_length=1,
        max_length=128,
    )
    control_mode: CalibratedPolicyControlMode = CalibratedPolicyControlMode.CALIBRATED_RESEARCH_ONLY
    accepted_admission_value_units: float = Field(default=1.0, gt=0.0)
    marginal_verification_cost_weight: float = Field(default=1.0, gt=0.0)
    minimum_expected_marginal_utility: float = Field(default=0.0)
    calibration_authorization: V5RetainedCalibrationAuthorization | None = None
    capacity_profile_reference: SyntheticCapacityProfileReference | None = None

    @model_validator(mode="after")
    def validate_control_dependencies(self) -> CalibratedCausalLoadAwarePolicyConfig:
        """Prevent fallback and calibrated-control inputs from being mixed."""

        if self.control_mode is CalibratedPolicyControlMode.CALIBRATED_RESEARCH_ONLY:
            if type(self.calibration_authorization) is not V5RetainedCalibrationAuthorization:
                raise ValueError(
                    "calibrated research mode requires the exact retained V5 calibration "
                    "authorization"
                )
            if type(self.capacity_profile_reference) is not SyntheticCapacityProfileReference:
                raise ValueError(
                    "calibrated research mode requires an exact synthetic capacity-profile "
                    "reference"
                )
        elif (
            self.calibration_authorization is not None
            or self.capacity_profile_reference is not None
        ):
            raise ValueError(
                "conservative fallback mode must not retain calibrated-control dependencies"
            )
        return self

    def configuration_sha256(self) -> str:
        """Return a stable hash for the full adaptive-policy decision configuration."""

        return configuration_sha256(self)


class UnsafeRetrospectivePolicyConfig(StrictContract):
    """Configuration that permanently labels a look-ahead control as test-only."""

    policy_id: str = Field(
        default="unsafe-retrospective-lookahead-v1",
        min_length=1,
        max_length=128,
    )
    evaluation_only: Literal[True] = True


class CalibratedCausalLoadAwarePolicyError(ValueError):
    """Raised when an adaptive policy dependency cannot preserve V5 provenance."""

    def __init__(
        self,
        code: CalibratedCausalLoadAwarePolicyErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class FixedLengthVerificationPolicy:
    """Admit positions at or below a configured fixed verification budget."""

    def __init__(self, config: FixedLengthPolicyConfig) -> None:
        self._config = config

    @property
    def config(self) -> FixedLengthPolicyConfig:
        """Return the immutable policy configuration for evidence retention."""

        return self._config

    @property
    def descriptor(self) -> BaselinePolicyDescriptor:
        """Return normalized provenance without changing the capacity-blind rule."""

        return BaselinePolicyDescriptor(
            policy_id=self._config.policy_id,
            policy_kind=BaselinePolicyKind.FIXED_LENGTH,
            configuration_sha256=self._config.configuration_sha256(),
        )

    def decide(self, context: object) -> VerificationDecision:
        """Make a causal fixed-budget decision from the exact runtime contract."""

        approved_context = require_causal_runtime_context(context)
        if approved_context.block_position_index <= self._config.maximum_verification_length:
            return _valid_decision(
                policy_id=self._config.policy_id,
                context=approved_context,
                action=VerificationAction.ADMIT,
                reason_code="fixed_length_within_budget",
            )
        return _valid_decision(
            policy_id=self._config.policy_id,
            context=approved_context,
            action=VerificationAction.STOP,
            reason_code="fixed_length_budget_exhausted",
        )


class StaticThresholdVerificationPolicy:
    """Admit positions only when their lawful confidence meets a static threshold."""

    def __init__(self, config: StaticThresholdPolicyConfig) -> None:
        self._config = config

    @property
    def config(self) -> StaticThresholdPolicyConfig:
        """Return the immutable policy configuration for evidence retention."""

        return self._config

    @property
    def descriptor(self) -> BaselinePolicyDescriptor:
        """Return normalized provenance without changing the capacity-blind rule."""

        return BaselinePolicyDescriptor(
            policy_id=self._config.policy_id,
            policy_kind=BaselinePolicyKind.STATIC_THRESHOLD,
            configuration_sha256=self._config.configuration_sha256(),
        )

    def decide(self, context: object) -> VerificationDecision:
        """Make a causal threshold decision without looking at capacity or outcomes."""

        approved_context = require_causal_runtime_context(context)
        if (
            approved_context.conditional_survival_confidence
            >= self._config.minimum_conditional_survival_confidence
        ):
            return _valid_decision(
                policy_id=self._config.policy_id,
                context=approved_context,
                action=VerificationAction.ADMIT,
                reason_code="static_threshold_met",
            )
        return _valid_decision(
            policy_id=self._config.policy_id,
            context=approved_context,
            action=VerificationAction.STOP,
            reason_code="static_threshold_below_minimum",
        )


class CalibratedCausalLoadAwarePolicy:
    """Research-only adaptive policy using lawful confidence and synthetic capacity.

    The policy consumes only the exact causal runtime context at decision time. It applies
    the frozen V5 bounded-monotone-beta transform to the lawful confidence, evaluates the
    declared synthetic capacity profile, and admits only when the configured expected
    marginal utility clears the declared minimum. It is replay-evaluation only.
    """

    def __init__(
        self,
        config: CalibratedCausalLoadAwarePolicyConfig,
        *,
        calibration_artifact: V5BoundedMonotoneBetaCalibrationArtifact | None = None,
        capacity_profile: SyntheticCapacityProfile | None = None,
    ) -> None:
        if type(config) is not CalibratedCausalLoadAwarePolicyConfig:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.INVALID_POLICY_CONFIG,
                "calibrated causal load-aware policy requires the exact configuration contract",
            )
        self._config = config
        self._calibration_artifact = calibration_artifact
        self._capacity_profile = capacity_profile
        self._validate_dependencies()

    @property
    def config(self) -> CalibratedCausalLoadAwarePolicyConfig:
        """Return the immutable policy configuration for replay evidence retention."""

        return self._config

    @property
    def descriptor(self) -> CalibratedCausalLoadAwarePolicyDescriptor:
        """Return a non-promotable descriptor for the controlled adaptive policy."""

        authorization = self._config.calibration_authorization
        profile_reference = self._config.capacity_profile_reference
        return CalibratedCausalLoadAwarePolicyDescriptor(
            policy_id=self._config.policy_id,
            control_mode=self._config.control_mode,
            configuration_sha256=self._config.configuration_sha256(),
            calibration_artifact_sha256=(
                authorization.calibration_artifact_sha256 if authorization is not None else None
            ),
            capacity_profile_configuration_sha256=(
                profile_reference.configuration_sha256 if profile_reference is not None else None
            ),
        )

    def decide(self, context: object) -> VerificationDecision:
        """Make one causal adaptive decision without accessing replay outcomes or labels."""

        approved_context = require_causal_runtime_context(context)
        if self._config.control_mode is CalibratedPolicyControlMode.CONSERVATIVE_FALLBACK:
            return _valid_decision(
                policy_id=self._config.policy_id,
                context=approved_context,
                action=VerificationAction.CONSERVATIVE_FALLBACK,
                reason_code="configured_conservative_fallback",
            )

        artifact = self._require_calibration_artifact()
        profile = self._require_capacity_profile()
        calibrated_confidence = calculate_v5_bounded_monotone_beta_probability(
            approved_context.conditional_survival_confidence,
            artifact.parameters,
        )
        try:
            capacity_evaluation = profile.evaluate(approved_context.capacity_snapshot)
        except CapacityProfileError as error:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.CAPACITY_PROFILE_MISMATCH,
                str(error),
            ) from error

        expected_marginal_utility = (
            calibrated_confidence * self._config.accepted_admission_value_units
            - capacity_evaluation.marginal_verification_cost_units
            * self._config.marginal_verification_cost_weight
        )
        if expected_marginal_utility >= self._config.minimum_expected_marginal_utility:
            return _valid_decision(
                policy_id=self._config.policy_id,
                context=approved_context,
                action=VerificationAction.ADMIT,
                reason_code="calibrated_expected_marginal_utility_met",
                expected_marginal_utility=expected_marginal_utility,
            )
        return _valid_decision(
            policy_id=self._config.policy_id,
            context=approved_context,
            action=VerificationAction.STOP,
            reason_code="calibrated_expected_marginal_utility_below_minimum",
            expected_marginal_utility=expected_marginal_utility,
        )

    def _validate_dependencies(self) -> None:
        """Validate provenance once, before any runtime decision can occur."""

        if self._config.control_mode is CalibratedPolicyControlMode.CONSERVATIVE_FALLBACK:
            if self._calibration_artifact is not None or self._capacity_profile is not None:
                raise CalibratedCausalLoadAwarePolicyError(
                    CalibratedCausalLoadAwarePolicyErrorCode.INVALID_POLICY_CONFIG,
                    "conservative fallback mode must not accept active calibrated-control "
                    "dependencies",
                )
            return

        authorization = self._config.calibration_authorization
        profile_reference = self._config.capacity_profile_reference
        if type(authorization) is not V5RetainedCalibrationAuthorization:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.INVALID_POLICY_CONFIG,
                "calibrated research mode requires the exact retained V5 authorization",
            )
        if type(self._calibration_artifact) is not V5BoundedMonotoneBetaCalibrationArtifact:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.INVALID_CALIBRATION_ARTIFACT,
                "calibrated research mode requires the exact retained V5 artifact contract",
            )
        artifact_sha256 = hashlib.sha256(
            canonical_v5_bounded_monotone_beta_artifact_json(self._calibration_artifact)
        ).hexdigest()
        if artifact_sha256 != authorization.calibration_artifact_sha256:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.CALIBRATION_ARTIFACT_MISMATCH,
                "calibrated research mode requires the retained V5 calibration artifact hash",
            )
        if type(profile_reference) is not SyntheticCapacityProfileReference:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.INVALID_POLICY_CONFIG,
                "calibrated research mode requires an exact capacity-profile reference",
            )
        if type(self._capacity_profile) is not SyntheticCapacityProfile:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.INVALID_CAPACITY_PROFILE,
                "calibrated research mode requires the exact synthetic capacity profile",
            )
        actual_reference = SyntheticCapacityProfileReference.from_profile(self._capacity_profile)
        if actual_reference != profile_reference:
            raise CalibratedCausalLoadAwarePolicyError(
                CalibratedCausalLoadAwarePolicyErrorCode.CAPACITY_PROFILE_MISMATCH,
                "capacity profile does not match the configuration reference",
            )

    def _require_calibration_artifact(self) -> V5BoundedMonotoneBetaCalibrationArtifact:
        """Return the constructor-verified artifact for one calibrated decision."""

        if type(self._calibration_artifact) is not V5BoundedMonotoneBetaCalibrationArtifact:
            raise AssertionError("validated calibrated policy is missing its V5 artifact")
        return self._calibration_artifact

    def _require_capacity_profile(self) -> SyntheticCapacityProfile:
        """Return the constructor-verified profile for one capacity-aware decision."""

        if type(self._capacity_profile) is not SyntheticCapacityProfile:
            raise AssertionError("validated calibrated policy is missing its capacity profile")
        return self._capacity_profile


class UnsafeRetrospectiveLookaheadPolicy:
    """Evaluation-only negative control that deliberately reads future outcomes.

    This class does not satisfy the valid-policy boundary. Its decisions are marked FAIL
    even where it appears to make a favorable choice from unavailable future evidence.
    """

    def __init__(self, config: UnsafeRetrospectivePolicyConfig | None = None) -> None:
        self._config = config or UnsafeRetrospectivePolicyConfig()

    @property
    def config(self) -> UnsafeRetrospectivePolicyConfig:
        """Return the immutable configuration proving this control is test-only."""

        return self._config

    def decide(self, context: object) -> VerificationDecision:
        """Use forbidden future outcomes only to demonstrate an invalid control path."""

        if type(context) is not RetrospectiveEvaluationContext:
            raise TypeError(
                "unsafe retrospective policy requires the exact "
                "RetrospectiveEvaluationContext test-only contract"
            )

        runtime_context = context.runtime_context
        if not context.future_acceptance_outcomes:
            return _unsafe_decision(
                policy_id=self._config.policy_id,
                context=runtime_context,
                action=VerificationAction.STOP,
                reason_code="unsafe_no_future_outcome",
            )

        next_outcome = context.future_acceptance_outcomes[0]
        action = VerificationAction.ADMIT if next_outcome else VerificationAction.STOP
        reason_code = (
            "unsafe_future_outcome_admit" if next_outcome else "unsafe_future_outcome_stop"
        )
        return _unsafe_decision(
            policy_id=self._config.policy_id,
            context=runtime_context,
            action=action,
            reason_code=reason_code,
        )


def _valid_decision(
    *,
    policy_id: str,
    context: CausalSchedulerContext,
    action: VerificationAction,
    reason_code: str,
    expected_marginal_utility: float | None = None,
) -> VerificationDecision:
    """Build a decision whose causal status is valid by construction."""

    return VerificationDecision(
        policy_id=policy_id,
        trace_id=context.trace_id,
        decode_round=context.decode_round,
        block_position_index=context.block_position_index,
        action=action,
        reason_code=reason_code,
        expected_marginal_utility=expected_marginal_utility,
        causal_safety_status=CausalSafetyStatus.PASS,
    )


def _unsafe_decision(
    *,
    policy_id: str,
    context: CausalSchedulerContext,
    action: VerificationAction,
    reason_code: str,
) -> VerificationDecision:
    """Build a decision that cannot be mistaken for a valid policy result."""

    return VerificationDecision(
        policy_id=policy_id,
        trace_id=context.trace_id,
        decode_round=context.decode_round,
        block_position_index=context.block_position_index,
        action=action,
        reason_code=reason_code,
        causal_safety_status=CausalSafetyStatus.FAIL,
    )
