"""Regression coverage for the governed matched synthetic comparison corpus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsafe.capacity_profiles import load_synthetic_capacity_profile_fixture_set
from specsafe.contracts import CausalSafetyStatus, TraceSplit
from specsafe.eval_harness import (
    MatchedPolicyComparisonConfig,
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
from specsafe.traces import load_synthetic_trace_fixture_set

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_matched_policy_comparison_v1"
_PROFILE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_capacity_profiles" / "v1"
_ARTIFACT_PATH = (
    _PROJECT_ROOT
    / "data"
    / "fixtures"
    / "synthetic_calibration_successor_v5"
    / "bounded_monotone_beta_calibration_artifact.json"
)

_EXPECTED_CASES = {
    "MPC5-101": {
        "split": TraceSplit.DEVELOPMENT,
        "profile_id": "synthetic-flat-capacity-control-v1",
        "fixed_outcome": MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL,
        "threshold_outcome": MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL,
    },
    "MPC5-102": {
        "split": TraceSplit.DEVELOPMENT,
        "profile_id": "synthetic-light-load-v1",
        "fixed_outcome": MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL,
        "threshold_outcome": MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL,
    },
    "MPC5-103": {
        "split": TraceSplit.DEVELOPMENT,
        "profile_id": "synthetic-moderate-load-v1",
        "fixed_outcome": MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY,
        "threshold_outcome": MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY,
    },
    "MPC5-104": {
        "split": TraceSplit.DEVELOPMENT,
        "profile_id": "synthetic-saturated-load-v1",
        "fixed_outcome": MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY,
        "threshold_outcome": MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY,
    },
    "MPC5-105": {
        "split": TraceSplit.DEVELOPMENT,
        "profile_id": "synthetic-jagged-capacity-v1",
        "fixed_outcome": MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY,
        "threshold_outcome": MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY,
    },
    "MPC5-106": {
        "split": TraceSplit.ADVERSARIAL_REGRESSION,
        "profile_id": "synthetic-flat-capacity-control-v1",
        "fixed_outcome": MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL,
        "threshold_outcome": MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY,
    },
}


def load_fixture_set():
    return load_synthetic_trace_fixture_set(_FIXTURE_ROOT)


def load_artifact() -> V5BoundedMonotoneBetaCalibrationArtifact:
    return V5BoundedMonotoneBetaCalibrationArtifact.model_validate_json(
        _ARTIFACT_PATH.read_text(encoding="utf-8")
    )


def make_policies(profile_id: str):
    profile = load_synthetic_capacity_profile_fixture_set(_PROFILE_ROOT).profile_for_id(profile_id)
    return (
        profile,
        FixedLengthVerificationPolicy(
            FixedLengthPolicyConfig(
                policy_id="fixed-matched-corpus-v1",
                maximum_verification_length=4,
            )
        ),
        StaticThresholdVerificationPolicy(
            StaticThresholdPolicyConfig(
                policy_id="threshold-matched-corpus-v1",
                minimum_conditional_survival_confidence=0.6,
            )
        ),
        CalibratedCausalLoadAwarePolicy(
            CalibratedCausalLoadAwarePolicyConfig(
                policy_id="adaptive-matched-corpus-v1",
                accepted_admission_value_units=1.0,
                marginal_verification_cost_weight=1.0,
                minimum_expected_marginal_utility=0.0,
                calibration_authorization=V5RetainedCalibrationAuthorization(),
                capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
            ),
            calibration_artifact=load_artifact(),
            capacity_profile=profile,
        ),
        UnsafeRetrospectiveLookaheadPolicy(),
    )


def make_scoring_config() -> PolicyUtilityScoringConfig:
    return PolicyUtilityScoringConfig(
        scoring_id="matched-corpus-utility-v1",
        accepted_admission_value_units=1.0,
        marginal_verification_cost_weight=1.0,
    )


def test_fixture_manifest_loads_all_predeclared_cases_with_allowed_splits() -> None:
    fixture_set = load_fixture_set()

    assert fixture_set.manifest.fixture_set_id == "synthetic-matched-policy-comparison-v1"
    assert fixture_set.manifest.fixture_set_version == "1.0.0"
    assert fixture_set.manifest.case_count == 6
    assert {case.runtime_input.case_id for case in fixture_set.cases} == set(_EXPECTED_CASES)
    assert {
        split_count.split: split_count.case_count
        for split_count in fixture_set.manifest.split_counts
    } == {
        TraceSplit.DEVELOPMENT: 5,
        TraceSplit.ADVERSARIAL_REGRESSION: 1,
    }

    for replay_case in fixture_set.cases:
        runtime = replay_case.runtime_input
        expected = _EXPECTED_CASES[runtime.case_id]
        assert runtime.split is expected["split"]
        assert runtime.data_role.value == "synthetic_fixture"
        assert runtime.source_type.value == "synthetic"
        assert {context.capacity_snapshot.profile_id for context in runtime.contexts} == {
            expected["profile_id"]
        }


def test_runtime_artifacts_remain_label_free() -> None:
    for runtime_path in sorted((_FIXTURE_ROOT / "inputs" / "cases").glob("*.json")):
        payload = json.loads(runtime_path.read_text(encoding="utf-8"))
        serialized = json.dumps(payload, sort_keys=True)

        assert "candidate_token_id" not in serialized
        assert "observed_acceptance" not in serialized
        assert "prefix_survival_label" not in serialized


@pytest.mark.parametrize("case_id", sorted(_EXPECTED_CASES))
def test_corpus_retains_predeclared_case_level_diagnostic_outcomes(case_id: str) -> None:
    fixture_set = load_fixture_set()
    expected = _EXPECTED_CASES[case_id]
    profile, fixed, threshold, adaptive, unsafe = make_policies(expected["profile_id"])

    result = run_matched_policy_comparison(
        fixture_set,
        case_id=case_id,
        comparison_config=MatchedPolicyComparisonConfig(
            comparison_id="matched-corpus-comparison-v1"
        ),
        run_id=f"matched-corpus-{case_id.lower()}-v1",
        capacity_profile=profile,
        scoring_config=make_scoring_config(),
        fixed_length_policy=fixed,
        static_threshold_policy=threshold,
        adaptive_policy=adaptive,
        unsafe_retrospective_policy=unsafe,
    )

    assert result.validity_status == "valid_matched_synthetic_comparison"
    assert result.claim_status == "case_level_comparison_only_no_promotion_claim"
    assert result.adaptive_vs_fixed_length.outcome is expected["fixed_outcome"]
    assert result.adaptive_vs_static_threshold.outcome is expected["threshold_outcome"]
    unsafe_replay = result.unsafe_retrospective_control.replay_result
    assert unsafe_replay.causal_safety_status is CausalSafetyStatus.FAIL
    assert unsafe_replay.evaluation_only is True
    assert result.unsafe_retrospective_control.exclusion_reason == (
        "causal_safety_failure_excluded_from_valid_comparison"
    )


def test_adversarial_unsafe_control_is_retained_but_excluded_from_valid_scoring() -> None:
    fixture_set = load_fixture_set()
    profile, fixed, threshold, adaptive, unsafe = make_policies(
        "synthetic-flat-capacity-control-v1"
    )

    result = run_matched_policy_comparison(
        fixture_set,
        case_id="MPC5-106",
        comparison_config=MatchedPolicyComparisonConfig(
            comparison_id="matched-corpus-adversarial-comparison-v1"
        ),
        run_id="matched-corpus-adversarial-run-v1",
        capacity_profile=profile,
        scoring_config=make_scoring_config(),
        fixed_length_policy=fixed,
        static_threshold_policy=threshold,
        adaptive_policy=adaptive,
        unsafe_retrospective_policy=unsafe,
    )

    unsafe_replay = result.unsafe_retrospective_control.replay_result
    assert unsafe_replay.position_results[0].decision.action.value == "admit"
    assert unsafe_replay.causal_safety_status is CausalSafetyStatus.FAIL
    assert result.unsafe_retrospective_control.exclusion_reason == (
        "causal_safety_failure_excluded_from_valid_comparison"
    )
