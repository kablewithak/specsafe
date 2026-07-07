"""Regression tests for the research-only calibrated causal load-aware policy."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.capacity_profiles import load_synthetic_capacity_profile_fixture_set
from specsafe.causal_safety import ForbiddenInformationAccessError
from specsafe.causal_safety.unsafe_controls import RetrospectiveEvaluationContext
from specsafe.contracts import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSafetyStatus,
    CausalSchedulerContext,
    VerificationAction,
    WorkloadType,
)
from specsafe.heldout_calibration.v5_final_assessment import (
    V5BoundedMonotoneBetaCalibrationArtifact,
)
from specsafe.scheduling import (
    AdaptivePolicyKind,
    CalibratedCausalLoadAwarePolicy,
    CalibratedCausalLoadAwarePolicyConfig,
    CalibratedCausalLoadAwarePolicyError,
    CalibratedCausalLoadAwarePolicyErrorCode,
    CalibratedPolicyControlMode,
    PolicyCapacitySensitivity,
    PolicyClassification,
    PolicyPromotionEligibility,
    SyntheticCapacityProfileReference,
    V5RetainedCalibrationAuthorization,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROFILE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_capacity_profiles" / "v1"
_ARTIFACT_PATH = (
    _PROJECT_ROOT
    / "data"
    / "fixtures"
    / "synthetic_calibration_successor_v5"
    / "bounded_monotone_beta_calibration_artifact.json"
)


def load_artifact() -> V5BoundedMonotoneBetaCalibrationArtifact:
    return V5BoundedMonotoneBetaCalibrationArtifact.model_validate_json(
        _ARTIFACT_PATH.read_text(encoding="utf-8")
    )


def load_profile(profile_id: str):
    fixture_set = load_synthetic_capacity_profile_fixture_set(_PROFILE_ROOT)
    return fixture_set.profile_for_id(profile_id)


def make_context(
    *,
    profile_id: str,
    active_request_count: int,
    verification_batch_tokens: int,
    confidence: float = 0.7,
) -> CausalSchedulerContext:
    return CausalSchedulerContext(
        trace_id="calibrated-policy-trace-001",
        request_id="calibrated-policy-request-001",
        workload_type=WorkloadType.CODE,
        decode_round=0,
        block_position_index=2,
        visible_prefix_token_ids=(41,),
        conditional_survival_confidence=confidence,
        capacity_snapshot=CapacitySnapshot(
            profile_id=profile_id,
            source=CapacityProfileSource.SYNTHETIC,
            active_request_count=active_request_count,
            verification_batch_tokens=verification_batch_tokens,
        ),
    )


def make_calibrated_policy(profile_id: str) -> CalibratedCausalLoadAwarePolicy:
    profile = load_profile(profile_id)
    config = CalibratedCausalLoadAwarePolicyConfig(
        calibration_authorization=V5RetainedCalibrationAuthorization(),
        capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
    )
    return CalibratedCausalLoadAwarePolicy(
        config,
        calibration_artifact=load_artifact(),
        capacity_profile=profile,
    )


def test_descriptor_retains_research_only_adaptive_policy_identity() -> None:
    policy = make_calibrated_policy("synthetic-light-load-v1")

    descriptor = policy.descriptor

    assert descriptor.policy_kind is AdaptivePolicyKind.CALIBRATED_CAUSAL_LOAD_AWARE
    assert descriptor.classification is PolicyClassification.VALID_ADAPTIVE_POLICY
    assert descriptor.capacity_sensitivity is PolicyCapacitySensitivity.CAPACITY_AWARE
    assert descriptor.promotion_eligibility is PolicyPromotionEligibility.REPLAY_EVALUATION_ONLY
    assert descriptor.control_mode is CalibratedPolicyControlMode.CALIBRATED_RESEARCH_ONLY
    assert descriptor.calibration_artifact_sha256 == (
        "a3baeb2db94221d68a69fc757c8865e384e3ac92ca05585919188fe1c744cd14"
    )
    assert descriptor.configuration_sha256 == policy.config.configuration_sha256()


def test_calibrated_policy_admits_under_light_load_and_stops_under_saturation() -> None:
    light_policy = make_calibrated_policy("synthetic-light-load-v1")
    saturated_policy = make_calibrated_policy("synthetic-saturated-load-v1")

    light_decision = light_policy.decide(
        make_context(
            profile_id="synthetic-light-load-v1",
            active_request_count=16,
            verification_batch_tokens=128,
        )
    )
    saturated_decision = saturated_policy.decide(
        make_context(
            profile_id="synthetic-saturated-load-v1",
            active_request_count=16,
            verification_batch_tokens=128,
        )
    )

    assert light_decision.action is VerificationAction.ADMIT
    assert light_decision.reason_code == "calibrated_expected_marginal_utility_met"
    assert light_decision.expected_marginal_utility == pytest.approx(0.349817610714192)
    assert saturated_decision.action is VerificationAction.STOP
    assert saturated_decision.reason_code == "calibrated_expected_marginal_utility_below_minimum"
    assert saturated_decision.expected_marginal_utility == pytest.approx(-2.900182389285808)
    assert light_decision.causal_safety_status is CausalSafetyStatus.PASS
    assert saturated_decision.causal_safety_status is CausalSafetyStatus.PASS


def test_calibrated_policy_rejects_test_only_retrospective_context() -> None:
    policy = make_calibrated_policy("synthetic-light-load-v1")
    runtime_context = make_context(
        profile_id="synthetic-light-load-v1",
        active_request_count=2,
        verification_batch_tokens=64,
    )
    unsafe_context = RetrospectiveEvaluationContext(
        runtime_context=runtime_context,
        future_candidate_token_ids=(901,),
        future_acceptance_outcomes=(True,),
    )

    with pytest.raises(ForbiddenInformationAccessError):
        policy.decide(unsafe_context)


def test_conservative_fallback_is_causal_and_has_no_active_dependencies() -> None:
    policy = CalibratedCausalLoadAwarePolicy(
        CalibratedCausalLoadAwarePolicyConfig(
            control_mode=CalibratedPolicyControlMode.CONSERVATIVE_FALLBACK,
        )
    )
    decision = policy.decide(
        make_context(
            profile_id="any-synthetic-profile-id-is-ignored-in-fallback",
            active_request_count=2,
            verification_batch_tokens=64,
        )
    )

    assert decision.action is VerificationAction.CONSERVATIVE_FALLBACK
    assert decision.reason_code == "configured_conservative_fallback"
    assert decision.expected_marginal_utility is None
    assert decision.causal_safety_status is CausalSafetyStatus.PASS
    assert policy.descriptor.calibration_artifact_sha256 is None
    assert policy.descriptor.capacity_profile_configuration_sha256 is None


def test_constructor_rejects_non_retained_calibration_artifact() -> None:
    profile = load_profile("synthetic-light-load-v1")
    artifact_payload = load_artifact().model_dump(mode="json")
    artifact_payload["parameters"]["c"] = 0.2
    altered_artifact = V5BoundedMonotoneBetaCalibrationArtifact.model_validate(artifact_payload)
    config = CalibratedCausalLoadAwarePolicyConfig(
        calibration_authorization=V5RetainedCalibrationAuthorization(),
        capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
    )

    with pytest.raises(CalibratedCausalLoadAwarePolicyError) as error:
        CalibratedCausalLoadAwarePolicy(
            config,
            calibration_artifact=altered_artifact,
            capacity_profile=profile,
        )

    assert (
        error.value.code is CalibratedCausalLoadAwarePolicyErrorCode.CALIBRATION_ARTIFACT_MISMATCH
    )


def test_constructor_rejects_capacity_profile_reference_drift() -> None:
    light_profile = load_profile("synthetic-light-load-v1")
    saturated_profile = load_profile("synthetic-saturated-load-v1")
    config = CalibratedCausalLoadAwarePolicyConfig(
        calibration_authorization=V5RetainedCalibrationAuthorization(),
        capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(light_profile),
    )

    with pytest.raises(CalibratedCausalLoadAwarePolicyError) as error:
        CalibratedCausalLoadAwarePolicy(
            config,
            calibration_artifact=load_artifact(),
            capacity_profile=saturated_profile,
        )

    assert error.value.code is CalibratedCausalLoadAwarePolicyErrorCode.CAPACITY_PROFILE_MISMATCH


def test_policy_configuration_rejects_unknown_fields_and_mixed_fallback_dependencies() -> None:
    light_profile = load_profile("synthetic-light-load-v1")

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CalibratedCausalLoadAwarePolicyConfig.model_validate(
            {
                "calibration_authorization": V5RetainedCalibrationAuthorization().model_dump(),
                "capacity_profile_reference": SyntheticCapacityProfileReference.from_profile(
                    light_profile
                ).model_dump(),
                "winner_policy_id": "calibrated-causal-load-aware-v5",
            }
        )

    with pytest.raises(ValidationError, match="conservative fallback mode"):
        CalibratedCausalLoadAwarePolicyConfig(
            control_mode=CalibratedPolicyControlMode.CONSERVATIVE_FALLBACK,
            calibration_authorization=V5RetainedCalibrationAuthorization(),
        )


def test_configuration_hash_is_deterministic_and_content_sensitive() -> None:
    profile = load_profile("synthetic-light-load-v1")
    first = CalibratedCausalLoadAwarePolicyConfig(
        calibration_authorization=V5RetainedCalibrationAuthorization(),
        capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
    )
    same = CalibratedCausalLoadAwarePolicyConfig(
        calibration_authorization=V5RetainedCalibrationAuthorization(),
        capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
    )
    changed = CalibratedCausalLoadAwarePolicyConfig(
        calibration_authorization=V5RetainedCalibrationAuthorization(),
        capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
        marginal_verification_cost_weight=2.0,
    )

    assert first.configuration_sha256() == same.configuration_sha256()
    assert first.configuration_sha256() != changed.configuration_sha256()
