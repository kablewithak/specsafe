"""Regression tests for governed case-level matched policy comparison."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.capacity_profiles import (
    CapacityProfileKind,
    load_synthetic_capacity_profile_fixture_set,
)
from specsafe.contracts import (
    CapacityProfileSource,
    CapacitySnapshot,
    CausalSchedulerContext,
    FixtureSplitCount,
    SyntheticTraceExpectedOutcome,
    SyntheticTraceExpectedOutcomes,
    SyntheticTraceFixtureManifest,
    SyntheticTraceFixtureManifestEntry,
    SyntheticTraceFixtureSet,
    SyntheticTraceReplayCase,
    SyntheticTraceRuntimeInput,
    TraceArtifactKind,
    TraceDataRole,
    TraceSourceType,
    TraceSplit,
    WorkloadType,
)
from specsafe.eval_harness import (
    MatchedPolicyComparisonConfig,
    MatchedPolicyComparisonError,
    MatchedPolicyComparisonErrorCode,
    MatchedPolicyComparisonOutcome,
    PolicyUtilityScoringConfig,
    run_matched_policy_comparison,
)
from specsafe.heldout_calibration.v5_final_assessment import (
    V5BoundedMonotoneBetaCalibrationArtifact,
)
from specsafe.scheduling import (
    CalibratedCausalLoadAwarePolicy,
    CalibratedCausalLoadAwarePolicyConfig,
    FixedLengthPolicyConfig,
    FixedLengthVerificationPolicy,
    StaticThresholdPolicyConfig,
    StaticThresholdVerificationPolicy,
    SyntheticCapacityProfileReference,
    UnsafeRetrospectiveLookaheadPolicy,
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


def load_profile(profile_kind: CapacityProfileKind):
    return load_synthetic_capacity_profile_fixture_set(_PROFILE_ROOT).profile_for_kind(profile_kind)


def load_artifact() -> V5BoundedMonotoneBetaCalibrationArtifact:
    return V5BoundedMonotoneBetaCalibrationArtifact.model_validate_json(
        _ARTIFACT_PATH.read_text(encoding="utf-8")
    )


def make_fixture_set(
    *,
    profile_id: str,
    split: TraceSplit = TraceSplit.DEVELOPMENT,
    active_request_count: int = 16,
    verification_batch_tokens: int = 64,
) -> SyntheticTraceFixtureSet:
    confidences = (0.9, 0.6, 0.4)
    contexts = tuple(
        CausalSchedulerContext(
            trace_id="matched-comparison-trace-001",
            request_id="matched-comparison-request-001",
            workload_type=WorkloadType.CODE,
            decode_round=0,
            block_position_index=position,
            visible_prefix_token_ids=tuple(range(100, 100 + position - 1)),
            conditional_survival_confidence=confidence,
            capacity_snapshot=CapacitySnapshot(
                profile_id=profile_id,
                source=CapacityProfileSource.SYNTHETIC,
                active_request_count=active_request_count,
                verification_batch_tokens=verification_batch_tokens,
            ),
        )
        for position, confidence in enumerate(confidences, start=1)
    )
    runtime_input = SyntheticTraceRuntimeInput(
        schema_version="matched-policy-comparison-test-v1",
        fixture_id="matched-comparison-fixture-001",
        case_id="MATCHED-001",
        trace_id="matched-comparison-trace-001",
        request_id="matched-comparison-request-001",
        split=split,
        data_role=TraceDataRole.SYNTHETIC_FIXTURE,
        source_type=TraceSourceType.SYNTHETIC,
        generation_note="Self-authored fixture for governed matched policy comparison tests.",
        contexts=contexts,
    )
    outcomes = SyntheticTraceExpectedOutcomes(
        schema_version="matched-policy-comparison-test-v1",
        fixture_id="matched-comparison-fixture-001",
        case_id="MATCHED-001",
        trace_id="matched-comparison-trace-001",
        split=split,
        data_role=TraceDataRole.SYNTHETIC_FIXTURE,
        source_type=TraceSourceType.SYNTHETIC,
        outcomes=(
            SyntheticTraceExpectedOutcome(
                trace_id="matched-comparison-trace-001",
                decode_round=0,
                block_position_index=1,
                candidate_token_id=100,
                observed_acceptance=True,
                prefix_survival_label=True,
            ),
            SyntheticTraceExpectedOutcome(
                trace_id="matched-comparison-trace-001",
                decode_round=0,
                block_position_index=2,
                candidate_token_id=101,
                observed_acceptance=True,
                prefix_survival_label=True,
            ),
            SyntheticTraceExpectedOutcome(
                trace_id="matched-comparison-trace-001",
                decode_round=0,
                block_position_index=3,
                candidate_token_id=102,
                observed_acceptance=False,
                prefix_survival_label=False,
            ),
        ),
    )
    case = SyntheticTraceReplayCase(runtime_input=runtime_input, expected_outcomes=outcomes)
    manifest = SyntheticTraceFixtureManifest(
        schema_version="matched-policy-comparison-manifest-v1",
        fixture_set_id="matched-policy-comparison-tests-v1",
        fixture_set_version="v1",
        source_type=TraceSourceType.SYNTHETIC,
        generation_note="In-memory immutable fixture for matched comparison regression tests.",
        case_count=1,
        split_counts=(FixtureSplitCount(split=split, case_count=1),),
        entries=(
            SyntheticTraceFixtureManifestEntry(
                artifact_kind=TraceArtifactKind.RUNTIME_INPUT,
                relative_path="inputs/MATCHED-001.json",
                case_id="MATCHED-001",
                split=split,
                data_role=TraceDataRole.SYNTHETIC_FIXTURE,
                source_type=TraceSourceType.SYNTHETIC,
                sha256="1" * 64,
                byte_count=1,
            ),
            SyntheticTraceFixtureManifestEntry(
                artifact_kind=TraceArtifactKind.EXPECTED_OUTCOMES,
                relative_path="expected_outcomes/MATCHED-001.json",
                case_id="MATCHED-001",
                split=split,
                data_role=TraceDataRole.SYNTHETIC_FIXTURE,
                source_type=TraceSourceType.SYNTHETIC,
                sha256="2" * 64,
                byte_count=1,
            ),
        ),
    )
    return SyntheticTraceFixtureSet(manifest=manifest, cases=(case,))


def make_policies(profile_kind: CapacityProfileKind):
    profile = load_profile(profile_kind)
    fixed = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(
            policy_id="fixed-matched-v1",
            maximum_verification_length=3,
        )
    )
    threshold = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(
            policy_id="threshold-matched-v1",
            minimum_conditional_survival_confidence=0.6,
        )
    )
    adaptive = CalibratedCausalLoadAwarePolicy(
        CalibratedCausalLoadAwarePolicyConfig(
            policy_id="adaptive-matched-v1",
            accepted_admission_value_units=1.0,
            marginal_verification_cost_weight=1.0,
            minimum_expected_marginal_utility=0.0,
            calibration_authorization=V5RetainedCalibrationAuthorization(),
            capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
        ),
        calibration_artifact=load_artifact(),
        capacity_profile=profile,
    )
    return profile, fixed, threshold, adaptive, UnsafeRetrospectiveLookaheadPolicy()


def make_scoring_config() -> PolicyUtilityScoringConfig:
    return PolicyUtilityScoringConfig(
        scoring_id="matched-policy-utility-v1",
        accepted_admission_value_units=1.0,
        marginal_verification_cost_weight=1.0,
    )


def make_comparison_config() -> MatchedPolicyComparisonConfig:
    return MatchedPolicyComparisonConfig(comparison_id="matched-policy-comparison-v1")


def test_case_level_comparison_separates_valid_neutral_losing_and_invalid_results() -> None:
    profile, fixed, threshold, adaptive, unsafe = make_policies(CapacityProfileKind.LIGHT_LOAD)
    result = run_matched_policy_comparison(
        make_fixture_set(profile_id=profile.profile_id),
        case_id="MATCHED-001",
        comparison_config=make_comparison_config(),
        run_id="matched-comparison-run-v1",
        capacity_profile=profile,
        scoring_config=make_scoring_config(),
        fixed_length_policy=fixed,
        static_threshold_policy=threshold,
        adaptive_policy=adaptive,
        unsafe_retrospective_policy=unsafe,
    )

    assert result.validity_status == "valid_matched_synthetic_comparison"
    assert result.claim_status == "case_level_comparison_only_no_promotion_claim"
    assert result.fixed_length_score.policy_utility_units == pytest.approx(1.55)
    assert result.static_threshold_score.policy_utility_units == pytest.approx(1.7)
    assert result.adaptive_score.policy_utility_units == pytest.approx(1.55)
    assert result.adaptive_vs_fixed_length.outcome is MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL
    assert (
        result.adaptive_vs_static_threshold.outcome
        is MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY
    )
    assert result.unsafe_retrospective_control.exclusion_reason == (
        "causal_safety_failure_excluded_from_valid_comparison"
    )
    assert result.unsafe_retrospective_control.replay_result.evaluation_only is True
    assert result.unsafe_retrospective_control.replay_result.causal_safety_status.value == "fail"
    assert result.fixed_length_score.capacity_profile_configuration_sha256 == (
        result.adaptive_score.capacity_profile_configuration_sha256
    )


def test_saturated_case_can_show_higher_adaptive_utility_without_promotion() -> None:
    profile, fixed, threshold, adaptive, unsafe = make_policies(CapacityProfileKind.SATURATED_LOAD)
    result = run_matched_policy_comparison(
        make_fixture_set(profile_id=profile.profile_id),
        case_id="MATCHED-001",
        comparison_config=make_comparison_config(),
        run_id="matched-saturated-run-v1",
        capacity_profile=profile,
        scoring_config=make_scoring_config(),
        fixed_length_policy=fixed,
        static_threshold_policy=threshold,
        adaptive_policy=adaptive,
        unsafe_retrospective_policy=unsafe,
    )

    assert result.adaptive_score.policy_utility_units == pytest.approx(0.0)
    assert (
        result.adaptive_vs_fixed_length.outcome
        is MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY
    )
    assert (
        result.adaptive_vs_static_threshold.outcome
        is MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY
    )
    assert result.claim_status == "case_level_comparison_only_no_promotion_claim"


def test_comparison_is_deterministic_for_identical_controlled_inputs() -> None:
    profile, fixed, threshold, adaptive, unsafe = make_policies(CapacityProfileKind.LIGHT_LOAD)
    fixture_set = make_fixture_set(profile_id=profile.profile_id)
    kwargs = {
        "fixture_set": fixture_set,
        "case_id": "MATCHED-001",
        "comparison_config": make_comparison_config(),
        "run_id": "matched-deterministic-run-v1",
        "capacity_profile": profile,
        "scoring_config": make_scoring_config(),
        "fixed_length_policy": fixed,
        "static_threshold_policy": threshold,
        "adaptive_policy": adaptive,
        "unsafe_retrospective_policy": unsafe,
    }

    first = run_matched_policy_comparison(**kwargs)
    second = run_matched_policy_comparison(**kwargs)

    assert first == second


def test_comparison_rejects_final_evaluation_before_a_governed_final_protocol_exists() -> None:
    profile, fixed, threshold, adaptive, unsafe = make_policies(CapacityProfileKind.LIGHT_LOAD)

    with pytest.raises(MatchedPolicyComparisonError) as error:
        run_matched_policy_comparison(
            make_fixture_set(profile_id=profile.profile_id, split=TraceSplit.FINAL_EVALUATION),
            case_id="MATCHED-001",
            comparison_config=make_comparison_config(),
            run_id="matched-final-run-v1",
            capacity_profile=profile,
            scoring_config=make_scoring_config(),
            fixed_length_policy=fixed,
            static_threshold_policy=threshold,
            adaptive_policy=adaptive,
            unsafe_retrospective_policy=unsafe,
        )

    assert error.value.code is MatchedPolicyComparisonErrorCode.SPLIT_NOT_AUTHORIZED


def test_comparison_rejects_fixture_capacity_profile_mismatch_before_replay() -> None:
    profile, fixed, threshold, adaptive, unsafe = make_policies(CapacityProfileKind.LIGHT_LOAD)

    with pytest.raises(MatchedPolicyComparisonError) as error:
        run_matched_policy_comparison(
            make_fixture_set(profile_id="synthetic-saturated-load-v1"),
            case_id="MATCHED-001",
            comparison_config=make_comparison_config(),
            run_id="matched-profile-mismatch-run-v1",
            capacity_profile=profile,
            scoring_config=make_scoring_config(),
            fixed_length_policy=fixed,
            static_threshold_policy=threshold,
            adaptive_policy=adaptive,
            unsafe_retrospective_policy=unsafe,
        )

    assert error.value.code is MatchedPolicyComparisonErrorCode.CAPACITY_PROFILE_MISMATCH


def test_comparison_rejects_adaptive_weights_that_differ_from_shared_scorer() -> None:
    profile = load_profile(CapacityProfileKind.LIGHT_LOAD)
    _, fixed, threshold, _, unsafe = make_policies(CapacityProfileKind.LIGHT_LOAD)
    adaptive = CalibratedCausalLoadAwarePolicy(
        CalibratedCausalLoadAwarePolicyConfig(
            policy_id="adaptive-mismatched-formula-v1",
            accepted_admission_value_units=2.0,
            marginal_verification_cost_weight=1.0,
            calibration_authorization=V5RetainedCalibrationAuthorization(),
            capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
        ),
        calibration_artifact=load_artifact(),
        capacity_profile=profile,
    )

    with pytest.raises(MatchedPolicyComparisonError) as error:
        run_matched_policy_comparison(
            make_fixture_set(profile_id=profile.profile_id),
            case_id="MATCHED-001",
            comparison_config=make_comparison_config(),
            run_id="matched-formula-mismatch-run-v1",
            capacity_profile=profile,
            scoring_config=make_scoring_config(),
            fixed_length_policy=fixed,
            static_threshold_policy=threshold,
            adaptive_policy=adaptive,
            unsafe_retrospective_policy=unsafe,
        )

    assert error.value.code is MatchedPolicyComparisonErrorCode.ADAPTIVE_SCORING_CONFIG_MISMATCH


def test_comparison_config_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MatchedPolicyComparisonConfig.model_validate(
            {
                "comparison_id": "matched-policy-comparison-v1",
                "winner_policy_id": "adaptive-matched-v1",
            }
        )
