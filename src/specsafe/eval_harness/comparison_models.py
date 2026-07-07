"""Strict contracts for matched synthetic policy comparison.

This boundary compares already-recorded causal policy replays under identical immutable
fixture, capacity-profile, and utility-scoring inputs. It is case-level only: it records
whether the adaptive policy is higher, neutral, or lower than each baseline for one
controlled case. It cannot promote a policy, aggregate a portfolio-wide winner, or turn
synthetic evidence into a serving claim.
"""

from __future__ import annotations

import hashlib
import json
import math
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.capacity_profiles import CapacityProfileKind
from specsafe.contracts import CausalSafetyStatus, TraceSplit
from specsafe.contracts.models import StrictContract
from specsafe.eval_harness.models import PolicyUtilityScore
from specsafe.scheduling import (
    BaselinePolicyDescriptor,
    CalibratedCausalLoadAwarePolicyDescriptor,
)
from specsafe.trace_replay import UnsafeRetrospectiveReplayResult, ValidPolicyReplayResult


class MatchedPolicyComparisonEvidenceClass(StrEnum):
    """Evidence class for the first governed matched-comparison boundary."""

    SYNTHETIC_CONTROLLED = "synthetic_controlled"


class MatchedPolicyComparisonOutcome(StrEnum):
    """Case-level adaptive-versus-baseline result under one declared formula."""

    ADAPTIVE_HIGHER_UTILITY = "adaptive_higher_utility"
    UTILITY_NEUTRAL = "utility_neutral"
    ADAPTIVE_LOWER_UTILITY = "adaptive_lower_utility"


class MatchedPolicyComparisonErrorCode(StrEnum):
    """Machine-readable failures at the governed matched-comparison boundary."""

    INVALID_FIXTURE_SET = "invalid_comparison_fixture_set"
    INVALID_COMPARISON_CONFIG = "invalid_matched_comparison_config"
    INVALID_CAPACITY_PROFILE = "invalid_comparison_capacity_profile"
    INVALID_SCORING_CONFIG = "invalid_comparison_scoring_config"
    INVALID_FIXED_LENGTH_POLICY = "invalid_fixed_length_comparison_policy"
    INVALID_STATIC_THRESHOLD_POLICY = "invalid_static_threshold_comparison_policy"
    INVALID_ADAPTIVE_POLICY = "invalid_adaptive_comparison_policy"
    INVALID_UNSAFE_POLICY = "invalid_unsafe_comparison_policy"
    DUPLICATE_POLICY_ID = "duplicate_comparison_policy_id"
    CASE_NOT_FOUND = "comparison_case_not_found"
    SPLIT_NOT_AUTHORIZED = "comparison_split_not_authorized"
    CAPACITY_PROFILE_MISMATCH = "comparison_capacity_profile_mismatch"
    ADAPTIVE_SCORING_CONFIG_MISMATCH = "adaptive_scoring_config_mismatch"
    REPLAY_EXECUTION_FAILED = "matched_replay_execution_failed"
    SCORING_FAILED = "matched_policy_scoring_failed"


class MatchedPolicyComparisonConfig(StrictContract):
    """Predeclared semantics for one case-level matched policy comparison.

    ``utility_neutral_tolerance`` is fixed before execution and is used only to classify
    floating-point-equivalent score deltas. It is not a tuning knob for selecting a
    preferred policy.
    """

    schema_version: Literal["matched-policy-comparison-v1"] = "matched-policy-comparison-v1"
    comparison_id: str = Field(min_length=1, max_length=128)
    utility_neutral_tolerance: float = Field(default=1e-12, ge=0.0, le=1e-6)

    def configuration_sha256(self) -> str:
        """Return a stable provenance hash for the declared comparison semantics."""

        canonical_json = json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(f"{canonical_json}\n".encode()).hexdigest()


class AdaptiveBaselineUtilityComparison(StrictContract):
    """One inspectable adaptive-versus-baseline case-level utility delta."""

    baseline_policy_id: str = Field(min_length=1, max_length=128)
    baseline_policy_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    adaptive_policy_id: str = Field(min_length=1, max_length=128)
    adaptive_policy_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    baseline_policy_utility_units: float
    adaptive_policy_utility_units: float
    utility_delta_units: float
    utility_neutral_tolerance: float = Field(ge=0.0, le=1e-6)
    outcome: MatchedPolicyComparisonOutcome

    @model_validator(mode="after")
    def validate_delta_and_outcome(self) -> AdaptiveBaselineUtilityComparison:
        """Ensure the retained delta and category derive from the retained scores."""

        expected_delta = self.adaptive_policy_utility_units - self.baseline_policy_utility_units
        if not math.isclose(self.utility_delta_units, expected_delta, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("utility_delta_units must equal adaptive minus baseline utility")

        if math.isclose(
            self.utility_delta_units,
            0.0,
            rel_tol=0.0,
            abs_tol=self.utility_neutral_tolerance,
        ):
            expected_outcome = MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL
        elif self.utility_delta_units > 0.0:
            expected_outcome = MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY
        else:
            expected_outcome = MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY

        if self.outcome is not expected_outcome:
            raise ValueError(
                "comparison outcome must match the declared utility delta and tolerance"
            )
        return self


class UnsafeRetrospectiveControlExclusion(StrictContract):
    """Retained invalid control evidence that is structurally excluded from scoring."""

    policy_id: str = Field(min_length=1, max_length=128)
    replay_result: UnsafeRetrospectiveReplayResult
    exclusion_reason: Literal["causal_safety_failure_excluded_from_valid_comparison"] = (
        "causal_safety_failure_excluded_from_valid_comparison"
    )

    @model_validator(mode="after")
    def validate_unsafe_control(self) -> UnsafeRetrospectiveControlExclusion:
        """Keep the retrospective control visibly invalid and non-promotable."""

        if self.policy_id != self.replay_result.policy_id:
            raise ValueError("unsafe control policy_id must match the replay result")
        if self.replay_result.causal_safety_status is not CausalSafetyStatus.FAIL:
            raise ValueError("unsafe control must retain causal safety failure")
        if self.replay_result.evaluation_only is not True:
            raise ValueError("unsafe control must remain evaluation-only")
        return self


class MatchedPolicyComparisonResult(StrictContract):
    """One valid, case-level comparison across identical controlled inputs.

    This result deliberately does not have an aggregate winner, promotion field, runtime
    control status, or performance claim. It is an inspectable replay artifact for one
    immutable development or adversarial-regression case.
    """

    schema_version: Literal["matched-policy-comparison-result-v1"] = (
        "matched-policy-comparison-result-v1"
    )
    comparison_id: str = Field(min_length=1, max_length=128)
    comparison_config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    run_id: str = Field(min_length=1, max_length=128)
    evidence_class: Literal[MatchedPolicyComparisonEvidenceClass.SYNTHETIC_CONTROLLED] = (
        MatchedPolicyComparisonEvidenceClass.SYNTHETIC_CONTROLLED
    )
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    fixture_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    split: Literal[TraceSplit.DEVELOPMENT, TraceSplit.ADVERSARIAL_REGRESSION]
    capacity_profile_id: str = Field(min_length=1, max_length=128)
    capacity_profile_version: str = Field(min_length=1, max_length=64)
    capacity_profile_kind: CapacityProfileKind
    capacity_profile_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scoring_id: str = Field(min_length=1, max_length=128)
    scoring_config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    utility_neutral_tolerance: float = Field(ge=0.0, le=1e-6)
    fixed_length_policy: BaselinePolicyDescriptor
    static_threshold_policy: BaselinePolicyDescriptor
    adaptive_policy: CalibratedCausalLoadAwarePolicyDescriptor
    fixed_length_replay: ValidPolicyReplayResult
    static_threshold_replay: ValidPolicyReplayResult
    adaptive_replay: ValidPolicyReplayResult
    fixed_length_score: PolicyUtilityScore
    static_threshold_score: PolicyUtilityScore
    adaptive_score: PolicyUtilityScore
    adaptive_vs_fixed_length: AdaptiveBaselineUtilityComparison
    adaptive_vs_static_threshold: AdaptiveBaselineUtilityComparison
    unsafe_retrospective_control: UnsafeRetrospectiveControlExclusion
    validity_status: Literal["valid_matched_synthetic_comparison"] = (
        "valid_matched_synthetic_comparison"
    )
    claim_status: Literal["case_level_comparison_only_no_promotion_claim"] = (
        "case_level_comparison_only_no_promotion_claim"
    )

    @model_validator(mode="after")
    def validate_matched_comparison_integrity(self) -> MatchedPolicyComparisonResult:
        """Enforce same-input provenance and strict unsafe-control exclusion."""

        descriptors = (
            self.fixed_length_policy,
            self.static_threshold_policy,
            self.adaptive_policy,
        )
        descriptor_ids = tuple(item.policy_id for item in descriptors)
        if len(set(descriptor_ids)) != len(descriptor_ids):
            raise ValueError("matched comparison policy descriptors must use unique policy IDs")

        replays = (
            self.fixed_length_replay,
            self.static_threshold_replay,
            self.adaptive_replay,
        )
        replay_ids = tuple(item.policy_id for item in replays)
        if replay_ids != descriptor_ids:
            raise ValueError("valid replay order and policy descriptor order must match")

        scores = (
            self.fixed_length_score,
            self.static_threshold_score,
            self.adaptive_score,
        )
        for replay, score, descriptor in zip(replays, scores, descriptors, strict=True):
            if replay.policy_id != descriptor.policy_id or score.policy_id != descriptor.policy_id:
                raise ValueError("replay and score policy IDs must match their descriptor")
            if score.policy_configuration_sha256 != descriptor.configuration_sha256:
                raise ValueError("score configuration hash must match the policy descriptor")
            if score.replay_run_id != replay.run_id:
                raise ValueError("score replay run ID must match the retained replay")
            if (
                score.fixture_set_id != self.fixture_set_id
                or score.fixture_set_version != self.fixture_set_version
                or score.fixture_id != self.fixture_id
                or score.case_id != self.case_id
                or score.trace_id != self.trace_id
                or score.split is not self.split
            ):
                raise ValueError("every valid score must use the enclosing fixture identity")
            if (
                replay.fixture_set_id != self.fixture_set_id
                or replay.fixture_set_version != self.fixture_set_version
                or replay.fixture_id != self.fixture_id
                or replay.case_id != self.case_id
                or replay.trace_id != self.trace_id
                or replay.split is not self.split
            ):
                raise ValueError("every valid replay must use the enclosing fixture identity")
            if replay.causal_safety_status is not CausalSafetyStatus.PASS:
                raise ValueError("valid comparison replays must retain causal pass")
            if (
                score.capacity_profile_id != self.capacity_profile_id
                or score.capacity_profile_version != self.capacity_profile_version
                or score.capacity_profile_kind is not self.capacity_profile_kind
                or score.capacity_profile_configuration_sha256
                != self.capacity_profile_configuration_sha256
            ):
                raise ValueError("every valid score must use the enclosing capacity profile")
            if (
                score.scoring_id != self.scoring_id
                or score.scoring_config_sha256 != self.scoring_config_sha256
            ):
                raise ValueError("every valid score must use the enclosing scoring configuration")

        if self.adaptive_policy.capacity_profile_configuration_sha256 != (
            self.capacity_profile_configuration_sha256
        ):
            raise ValueError("adaptive descriptor must retain the enclosing capacity profile hash")

        comparisons = (
            (self.fixed_length_score, self.adaptive_vs_fixed_length),
            (self.static_threshold_score, self.adaptive_vs_static_threshold),
        )
        for baseline_score, comparison in comparisons:
            if comparison.baseline_policy_id != baseline_score.policy_id:
                raise ValueError("comparison baseline policy ID must match the baseline score")
            if (
                comparison.baseline_policy_configuration_sha256
                != baseline_score.policy_configuration_sha256
            ):
                raise ValueError("comparison baseline configuration must match the baseline score")
            if comparison.adaptive_policy_id != self.adaptive_score.policy_id:
                raise ValueError("comparison adaptive policy ID must match the adaptive score")
            if (
                comparison.adaptive_policy_configuration_sha256
                != self.adaptive_score.policy_configuration_sha256
            ):
                raise ValueError("comparison adaptive configuration must match the adaptive score")
            if not math.isclose(
                comparison.baseline_policy_utility_units,
                baseline_score.policy_utility_units,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError("comparison baseline utility must match the baseline score")
            if not math.isclose(
                comparison.adaptive_policy_utility_units,
                self.adaptive_score.policy_utility_units,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError("comparison adaptive utility must match the adaptive score")
            if not math.isclose(
                comparison.utility_neutral_tolerance,
                self.utility_neutral_tolerance,
                rel_tol=0.0,
                abs_tol=0.0,
            ):
                raise ValueError("comparison tolerance must match the enclosing configuration")

        unsafe = self.unsafe_retrospective_control.replay_result
        if (
            unsafe.fixture_set_id != self.fixture_set_id
            or unsafe.fixture_set_version != self.fixture_set_version
            or unsafe.fixture_id != self.fixture_id
            or unsafe.case_id != self.case_id
            or unsafe.trace_id != self.trace_id
            or unsafe.split is not self.split
        ):
            raise ValueError("unsafe control must use the same immutable replay case")
        return self
