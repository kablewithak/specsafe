"""Regression tests for normalized causal capacity-blind baseline provenance."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from specsafe.contracts import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSchedulerContext,
    VerificationAction,
    WorkloadType,
)
from specsafe.evidence_ledger.models import FixedLengthPolicyLedgerDescriptor
from specsafe.scheduling import (
    BaselinePolicyDescriptor,
    BaselinePolicyKind,
    FixedLengthPolicyConfig,
    FixedLengthVerificationPolicy,
    PolicyCapacitySensitivity,
    PolicyClassification,
    StaticThresholdPolicyConfig,
    StaticThresholdVerificationPolicy,
)


def make_context(
    *,
    active_request_count: int,
    verification_batch_tokens: int,
) -> CausalSchedulerContext:
    return CausalSchedulerContext(
        trace_id="baseline-normalization-trace",
        request_id="baseline-normalization-request",
        workload_type=WorkloadType.OPEN_ENDED_CHAT,
        decode_round=0,
        block_position_index=2,
        visible_prefix_token_ids=(17,),
        conditional_survival_confidence=0.7,
        capacity_snapshot=CapacitySnapshot(
            profile_id="synthetic-profile-for-baseline-invariance-v1",
            source=CapacityProfileSource.SYNTHETIC,
            active_request_count=active_request_count,
            verification_batch_tokens=verification_batch_tokens,
        ),
    )


def test_fixed_length_descriptor_retains_normalized_baseline_identity() -> None:
    policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(
            policy_id="fixed-normalized-v1",
            maximum_verification_length=2,
        )
    )

    descriptor = policy.descriptor

    assert descriptor.policy_id == "fixed-normalized-v1"
    assert descriptor.policy_kind is BaselinePolicyKind.FIXED_LENGTH
    assert descriptor.classification is PolicyClassification.VALID_BASELINE
    assert descriptor.capacity_sensitivity is PolicyCapacitySensitivity.CAPACITY_BLIND
    assert descriptor.configuration_sha256 == policy.config.configuration_sha256()


def test_static_threshold_descriptor_retains_normalized_baseline_identity() -> None:
    policy = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(
            policy_id="threshold-normalized-v1",
            minimum_conditional_survival_confidence=0.7,
        )
    )

    descriptor = policy.descriptor

    assert descriptor.policy_id == "threshold-normalized-v1"
    assert descriptor.policy_kind is BaselinePolicyKind.STATIC_THRESHOLD
    assert descriptor.classification is PolicyClassification.VALID_BASELINE
    assert descriptor.capacity_sensitivity is PolicyCapacitySensitivity.CAPACITY_BLIND
    assert descriptor.configuration_sha256 == policy.config.configuration_sha256()


def test_baseline_configuration_hashes_are_deterministic_and_content_sensitive() -> None:
    fixed_first = FixedLengthPolicyConfig(
        policy_id="fixed-hash-v1",
        maximum_verification_length=3,
    )
    fixed_same = FixedLengthPolicyConfig(
        policy_id="fixed-hash-v1",
        maximum_verification_length=3,
    )
    fixed_changed = FixedLengthPolicyConfig(
        policy_id="fixed-hash-v1",
        maximum_verification_length=4,
    )

    assert fixed_first.configuration_sha256() == fixed_same.configuration_sha256()
    assert fixed_first.configuration_sha256() != fixed_changed.configuration_sha256()


def test_fixed_and_threshold_baselines_are_capacity_blind_at_decision_time() -> None:
    low_load_context = make_context(active_request_count=1, verification_batch_tokens=1)
    saturated_context = make_context(active_request_count=64, verification_batch_tokens=256)
    fixed_policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(maximum_verification_length=2)
    )
    threshold_policy = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(minimum_conditional_survival_confidence=0.7)
    )

    fixed_low = fixed_policy.decide(low_load_context)
    fixed_saturated = fixed_policy.decide(saturated_context)
    threshold_low = threshold_policy.decide(low_load_context)
    threshold_saturated = threshold_policy.decide(saturated_context)

    assert fixed_low.action is VerificationAction.ADMIT
    assert fixed_saturated.action is VerificationAction.ADMIT
    assert fixed_low.reason_code == fixed_saturated.reason_code
    assert threshold_low.action is VerificationAction.ADMIT
    assert threshold_saturated.action is VerificationAction.ADMIT
    assert threshold_low.reason_code == threshold_saturated.reason_code


def test_normalized_descriptor_rejects_unknown_or_invalid_claim_fields() -> None:
    fixed_config = FixedLengthPolicyConfig(maximum_verification_length=2)

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BaselinePolicyDescriptor.model_validate(
            {
                "policy_id": fixed_config.policy_id,
                "policy_kind": "fixed_length",
                "configuration_sha256": fixed_config.configuration_sha256(),
                "winner_policy_id": fixed_config.policy_id,
            }
        )


def test_ledger_descriptor_rejects_configuration_hash_drift() -> None:
    config = FixedLengthPolicyConfig(
        policy_id="fixed-ledger-drift-v1",
        maximum_verification_length=2,
    )
    policy = FixedLengthVerificationPolicy(config)
    tampered_descriptor = BaselinePolicyDescriptor(
        policy_id=config.policy_id,
        policy_kind=BaselinePolicyKind.FIXED_LENGTH,
        configuration_sha256="0" * 64,
    )

    with pytest.raises(ValidationError, match="configuration hash must match config"):
        FixedLengthPolicyLedgerDescriptor(
            policy_descriptor=tampered_descriptor,
            config=config,
        )

    retained = FixedLengthPolicyLedgerDescriptor(
        policy_descriptor=policy.descriptor,
        config=config,
    )

    assert retained.policy_descriptor.configuration_sha256 == config.configuration_sha256()
