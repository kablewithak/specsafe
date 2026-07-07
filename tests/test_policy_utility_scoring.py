"""Regression tests for non-comparative synthetic policy-utility scoring."""

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
    PolicyUtilityScore,
    PolicyUtilityScoringConfig,
    PolicyUtilityScoringError,
    PolicyUtilityScoringErrorCode,
    score_valid_policy_replay,
)
from specsafe.scheduling import (
    FixedLengthPolicyConfig,
    FixedLengthVerificationPolicy,
    StaticThresholdPolicyConfig,
    StaticThresholdVerificationPolicy,
)
from specsafe.trace_replay import run_valid_policy_replay

_PROFILE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_capacity_profiles" / "v1"
)


def make_fixture_set(
    *,
    split: TraceSplit = TraceSplit.DEVELOPMENT,
    profile_id: str = "synthetic-light-load-v1",
    confidences: tuple[float, float, float] = (0.9, 0.8, 0.7),
) -> SyntheticTraceFixtureSet:
    contexts = tuple(
        CausalSchedulerContext(
            trace_id="utility-score-trace-001",
            request_id="utility-score-request-001",
            workload_type=WorkloadType.CODE,
            decode_round=0,
            block_position_index=position,
            visible_prefix_token_ids=tuple(range(100, 100 + position - 1)),
            conditional_survival_confidence=confidence,
            capacity_snapshot=CapacitySnapshot(
                profile_id=profile_id,
                source=CapacityProfileSource.SYNTHETIC,
                active_request_count=2,
                verification_batch_tokens=position - 1,
            ),
        )
        for position, confidence in enumerate(confidences, start=1)
    )
    runtime_input = SyntheticTraceRuntimeInput(
        schema_version="synthetic-policy-utility-test-v1",
        fixture_id="utility-score-fixture-001",
        case_id="UTILITY-001",
        trace_id="utility-score-trace-001",
        request_id="utility-score-request-001",
        split=split,
        data_role=TraceDataRole.SYNTHETIC_FIXTURE,
        source_type=TraceSourceType.SYNTHETIC,
        generation_note="Self-authored synthetic policy-utility scorer test fixture.",
        contexts=contexts,
    )
    outcomes = SyntheticTraceExpectedOutcomes(
        schema_version="synthetic-policy-utility-test-v1",
        fixture_id="utility-score-fixture-001",
        case_id="UTILITY-001",
        trace_id="utility-score-trace-001",
        split=split,
        data_role=TraceDataRole.SYNTHETIC_FIXTURE,
        source_type=TraceSourceType.SYNTHETIC,
        outcomes=(
            SyntheticTraceExpectedOutcome(
                trace_id="utility-score-trace-001",
                decode_round=0,
                block_position_index=1,
                candidate_token_id=100,
                observed_acceptance=True,
                prefix_survival_label=True,
            ),
            SyntheticTraceExpectedOutcome(
                trace_id="utility-score-trace-001",
                decode_round=0,
                block_position_index=2,
                candidate_token_id=101,
                observed_acceptance=True,
                prefix_survival_label=True,
            ),
            SyntheticTraceExpectedOutcome(
                trace_id="utility-score-trace-001",
                decode_round=0,
                block_position_index=3,
                candidate_token_id=102,
                observed_acceptance=False,
                prefix_survival_label=False,
            ),
        ),
    )
    case = SyntheticTraceReplayCase(
        runtime_input=runtime_input,
        expected_outcomes=outcomes,
    )
    manifest = SyntheticTraceFixtureManifest(
        schema_version="synthetic-policy-utility-manifest-v1",
        fixture_set_id="synthetic-policy-utility-scorer-tests-v1",
        fixture_set_version="v1",
        source_type=TraceSourceType.SYNTHETIC,
        generation_note="In-memory test fixture for deterministic policy-utility scoring.",
        case_count=1,
        split_counts=(FixtureSplitCount(split=split, case_count=1),),
        entries=(
            SyntheticTraceFixtureManifestEntry(
                artifact_kind=TraceArtifactKind.RUNTIME_INPUT,
                relative_path="inputs/UTILITY-001.json",
                case_id="UTILITY-001",
                split=split,
                data_role=TraceDataRole.SYNTHETIC_FIXTURE,
                source_type=TraceSourceType.SYNTHETIC,
                sha256="1" * 64,
                byte_count=1,
            ),
            SyntheticTraceFixtureManifestEntry(
                artifact_kind=TraceArtifactKind.EXPECTED_OUTCOMES,
                relative_path="expected_outcomes/UTILITY-001.json",
                case_id="UTILITY-001",
                split=split,
                data_role=TraceDataRole.SYNTHETIC_FIXTURE,
                source_type=TraceSourceType.SYNTHETIC,
                sha256="2" * 64,
                byte_count=1,
            ),
        ),
    )
    return SyntheticTraceFixtureSet(manifest=manifest, cases=(case,))


def make_scoring_config() -> PolicyUtilityScoringConfig:
    return PolicyUtilityScoringConfig(
        scoring_id="synthetic-policy-utility-v1",
        accepted_admission_value_units=1.0,
        marginal_verification_cost_weight=1.0,
    )


def load_light_profile():
    return load_synthetic_capacity_profile_fixture_set(_PROFILE_ROOT).profile_for_kind(
        CapacityProfileKind.LIGHT_LOAD
    )


def test_scores_recorded_fixed_policy_replay_with_declared_formula() -> None:
    fixture_set = make_fixture_set()
    policy = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(
            policy_id="fixed-policy-utility-v1",
            maximum_verification_length=3,
        )
    )
    replay_result = run_valid_policy_replay(
        fixture_set,
        case_id="UTILITY-001",
        policy=policy,
        run_id="fixed-policy-utility-run-v1",
    )

    first_score = score_valid_policy_replay(
        fixture_set,
        replay_result=replay_result,
        capacity_profile=load_light_profile(),
        scoring_config=make_scoring_config(),
        policy_configuration_sha256=policy.config.configuration_sha256(),
    )
    second_score = score_valid_policy_replay(
        fixture_set,
        replay_result=replay_result,
        capacity_profile=load_light_profile(),
        scoring_config=make_scoring_config(),
        policy_configuration_sha256=policy.config.configuration_sha256(),
    )

    assert first_score == second_score
    assert first_score.policy_id == "fixed-policy-utility-v1"
    assert first_score.accepted_admission_count == 2
    assert first_score.rejected_admission_count == 1
    assert first_score.accepted_work_value_units == pytest.approx(2.0)
    assert first_score.verification_cost_units == pytest.approx(0.3)
    assert first_score.policy_utility_units == pytest.approx(1.7)
    assert len(first_score.admitted_position_costs) == 3
    assert first_score.comparison_claim_status == "no_cross_policy_winner_claim"


def test_terminal_threshold_stop_has_no_cost_for_the_stop_decision() -> None:
    fixture_set = make_fixture_set(confidences=(0.9, 0.1, 0.9))
    policy = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(
            policy_id="threshold-policy-utility-v1",
            minimum_conditional_survival_confidence=0.5,
        )
    )
    replay_result = run_valid_policy_replay(
        fixture_set,
        case_id="UTILITY-001",
        policy=policy,
        run_id="threshold-policy-utility-run-v1",
    )

    score = score_valid_policy_replay(
        fixture_set,
        replay_result=replay_result,
        capacity_profile=load_light_profile(),
        scoring_config=make_scoring_config(),
        policy_configuration_sha256=policy.config.configuration_sha256(),
    )

    assert replay_result.admitted_position_count == 1
    assert score.accepted_admission_count == 1
    assert score.verification_cost_units == pytest.approx(0.1)
    assert score.policy_utility_units == pytest.approx(0.9)
    assert tuple(item.block_position_index for item in score.admitted_position_costs) == (1,)


def test_scoring_rejects_final_evaluation_before_a_governed_comparison_protocol() -> None:
    fixture_set = make_fixture_set(split=TraceSplit.FINAL_EVALUATION)
    policy = FixedLengthVerificationPolicy(FixedLengthPolicyConfig(maximum_verification_length=3))
    replay_result = run_valid_policy_replay(
        fixture_set,
        case_id="UTILITY-001",
        policy=policy,
        run_id="final-policy-utility-run-v1",
    )

    with pytest.raises(PolicyUtilityScoringError) as error:
        score_valid_policy_replay(
            fixture_set,
            replay_result=replay_result,
            capacity_profile=load_light_profile(),
            scoring_config=make_scoring_config(),
            policy_configuration_sha256=policy.config.configuration_sha256(),
        )

    assert error.value.code is PolicyUtilityScoringErrorCode.SPLIT_NOT_AUTHORIZED


def test_scoring_rejects_capacity_profile_mismatch() -> None:
    fixture_set = make_fixture_set(profile_id="synthetic-saturated-load-v1")
    policy = FixedLengthVerificationPolicy(FixedLengthPolicyConfig(maximum_verification_length=3))
    replay_result = run_valid_policy_replay(
        fixture_set,
        case_id="UTILITY-001",
        policy=policy,
        run_id="mismatched-profile-utility-run-v1",
    )

    with pytest.raises(PolicyUtilityScoringError) as error:
        score_valid_policy_replay(
            fixture_set,
            replay_result=replay_result,
            capacity_profile=load_light_profile(),
            scoring_config=make_scoring_config(),
            policy_configuration_sha256=policy.config.configuration_sha256(),
        )

    assert error.value.code is PolicyUtilityScoringErrorCode.CAPACITY_PROFILE_MISMATCH


def test_score_contract_rejects_winner_claim_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        PolicyUtilityScore.model_validate(
            {
                "scoring_id": "score-contract-v1",
                "scoring_config_sha256": "0" * 64,
                "policy_id": "fixed-score-contract-v1",
                "policy_configuration_sha256": "1" * 64,
                "replay_run_id": "score-contract-run-v1",
                "replay_result_sha256": "2" * 64,
                "fixture_set_id": "fixture-set-v1",
                "fixture_set_version": "v1",
                "fixture_id": "fixture-v1",
                "case_id": "case-v1",
                "trace_id": "trace-v1",
                "split": "development",
                "capacity_profile_id": "profile-v1",
                "capacity_profile_version": "v1",
                "capacity_profile_kind": "light_load",
                "capacity_profile_configuration_sha256": "3" * 64,
                "processed_position_count": 1,
                "admitted_position_count": 0,
                "accepted_admission_count": 0,
                "rejected_admission_count": 0,
                "accepted_work_value_units": 0.0,
                "verification_cost_units": 0.0,
                "policy_utility_units": 0.0,
                "admitted_position_costs": [],
                "winner_policy_id": "fixed-score-contract-v1",
            }
        )


def test_scoring_configuration_hash_is_deterministic_and_content_sensitive() -> None:
    first = make_scoring_config()
    same = make_scoring_config()
    changed = PolicyUtilityScoringConfig(
        scoring_id="synthetic-policy-utility-v1",
        accepted_admission_value_units=1.0,
        marginal_verification_cost_weight=2.0,
    )

    assert first.configuration_sha256() == same.configuration_sha256()
    assert first.configuration_sha256() != changed.configuration_sha256()
