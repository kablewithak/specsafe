"""Run one governed matched comparison over a single immutable synthetic replay case."""

from __future__ import annotations

import hashlib
import math

from specsafe.capacity_profiles import CapacityProfileError, SyntheticCapacityProfile
from specsafe.contracts import (
    CapacityProfileSource,
    SyntheticTraceFixtureSet,
    TraceSplit,
)
from specsafe.eval_harness.comparison_models import (
    AdaptiveBaselineUtilityComparison,
    MatchedPolicyComparisonConfig,
    MatchedPolicyComparisonErrorCode,
    MatchedPolicyComparisonOutcome,
    MatchedPolicyComparisonResult,
    UnsafeRetrospectiveControlExclusion,
)
from specsafe.eval_harness.models import PolicyUtilityScoringConfig
from specsafe.eval_harness.scoring import PolicyUtilityScoringError, score_valid_policy_replay
from specsafe.scheduling import (
    CalibratedCausalLoadAwarePolicy,
    FixedLengthVerificationPolicy,
    StaticThresholdVerificationPolicy,
    UnsafeRetrospectiveLookaheadPolicy,
)
from specsafe.trace_replay import (
    DeterministicReplayExecutionError,
    run_unsafe_retrospective_replay,
    run_valid_policy_replay,
)

_ALLOWED_SPLITS = frozenset({TraceSplit.DEVELOPMENT, TraceSplit.ADVERSARIAL_REGRESSION})


class MatchedPolicyComparisonError(ValueError):
    """Raised when a case cannot satisfy the governed comparison contract."""

    def __init__(self, code: MatchedPolicyComparisonErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def run_matched_policy_comparison(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    case_id: str,
    comparison_config: MatchedPolicyComparisonConfig,
    run_id: str,
    capacity_profile: SyntheticCapacityProfile,
    scoring_config: PolicyUtilityScoringConfig,
    fixed_length_policy: FixedLengthVerificationPolicy,
    static_threshold_policy: StaticThresholdVerificationPolicy,
    adaptive_policy: CalibratedCausalLoadAwarePolicy,
    unsafe_retrospective_policy: UnsafeRetrospectiveLookaheadPolicy,
) -> MatchedPolicyComparisonResult:
    """Replay and compare three valid policies plus one invalid retrospective control.

    The function is deliberately case-level and side-effect free. Every valid policy sees
    the same immutable fixture case and declared capacity profile. The unsafe control is
    replayed against the same case, retained as causal-fail evidence, and excluded from
    valid scoring and all adaptive-versus-baseline deltas.
    """

    _require_exact_inputs(
        fixture_set=fixture_set,
        comparison_config=comparison_config,
        capacity_profile=capacity_profile,
        scoring_config=scoring_config,
        fixed_length_policy=fixed_length_policy,
        static_threshold_policy=static_threshold_policy,
        adaptive_policy=adaptive_policy,
        unsafe_retrospective_policy=unsafe_retrospective_policy,
    )
    if not run_id or len(run_id) > 128:
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.INVALID_COMPARISON_CONFIG,
            "matched comparison run_id must contain between 1 and 128 characters",
        )

    replay_case = _select_case(fixture_set, case_id)
    if replay_case.runtime_input.split not in _ALLOWED_SPLITS:
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.SPLIT_NOT_AUTHORIZED,
            "matched comparison permits development and adversarial regression cases only",
        )
    _validate_case_capacity_profile(replay_case.runtime_input.contexts, capacity_profile)
    _validate_policy_identity_and_formula(
        fixed_length_policy=fixed_length_policy,
        static_threshold_policy=static_threshold_policy,
        adaptive_policy=adaptive_policy,
        unsafe_retrospective_policy=unsafe_retrospective_policy,
        capacity_profile=capacity_profile,
        scoring_config=scoring_config,
    )

    fixed_replay = _run_valid_replay(
        fixture_set,
        case_id=case_id,
        policy=fixed_length_policy,
        run_id=_derived_replay_run_id(run_id, fixed_length_policy.config.policy_id),
    )
    threshold_replay = _run_valid_replay(
        fixture_set,
        case_id=case_id,
        policy=static_threshold_policy,
        run_id=_derived_replay_run_id(run_id, static_threshold_policy.config.policy_id),
    )
    adaptive_replay = _run_valid_replay(
        fixture_set,
        case_id=case_id,
        policy=adaptive_policy,
        run_id=_derived_replay_run_id(run_id, adaptive_policy.config.policy_id),
    )

    fixed_score = _score_replay(
        fixture_set,
        replay_result=fixed_replay,
        capacity_profile=capacity_profile,
        scoring_config=scoring_config,
        policy_configuration_sha256=fixed_length_policy.config.configuration_sha256(),
    )
    threshold_score = _score_replay(
        fixture_set,
        replay_result=threshold_replay,
        capacity_profile=capacity_profile,
        scoring_config=scoring_config,
        policy_configuration_sha256=static_threshold_policy.config.configuration_sha256(),
    )
    adaptive_score = _score_replay(
        fixture_set,
        replay_result=adaptive_replay,
        capacity_profile=capacity_profile,
        scoring_config=scoring_config,
        policy_configuration_sha256=adaptive_policy.config.configuration_sha256(),
    )

    try:
        unsafe_replay = run_unsafe_retrospective_replay(
            fixture_set,
            case_id=case_id,
            policy=unsafe_retrospective_policy,
            run_id=_derived_replay_run_id(run_id, unsafe_retrospective_policy.config.policy_id),
        )
    except DeterministicReplayExecutionError as error:
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.REPLAY_EXECUTION_FAILED,
            f"unsafe retrospective replay failed: {error}",
        ) from error

    runtime = replay_case.runtime_input
    return MatchedPolicyComparisonResult(
        comparison_id=comparison_config.comparison_id,
        comparison_config_sha256=comparison_config.configuration_sha256(),
        run_id=run_id,
        fixture_set_id=fixture_set.manifest.fixture_set_id,
        fixture_set_version=fixture_set.manifest.fixture_set_version,
        fixture_id=runtime.fixture_id,
        case_id=runtime.case_id,
        trace_id=runtime.trace_id,
        split=runtime.split,
        capacity_profile_id=capacity_profile.profile_id,
        capacity_profile_version=capacity_profile.profile_version,
        capacity_profile_kind=capacity_profile.profile_kind,
        capacity_profile_configuration_sha256=capacity_profile.configuration_sha256(),
        scoring_id=scoring_config.scoring_id,
        scoring_config_sha256=scoring_config.configuration_sha256(),
        utility_neutral_tolerance=comparison_config.utility_neutral_tolerance,
        fixed_length_policy=fixed_length_policy.descriptor,
        static_threshold_policy=static_threshold_policy.descriptor,
        adaptive_policy=adaptive_policy.descriptor,
        fixed_length_replay=fixed_replay,
        static_threshold_replay=threshold_replay,
        adaptive_replay=adaptive_replay,
        fixed_length_score=fixed_score,
        static_threshold_score=threshold_score,
        adaptive_score=adaptive_score,
        adaptive_vs_fixed_length=_build_utility_comparison(
            baseline_score=fixed_score,
            adaptive_score=adaptive_score,
            utility_neutral_tolerance=comparison_config.utility_neutral_tolerance,
        ),
        adaptive_vs_static_threshold=_build_utility_comparison(
            baseline_score=threshold_score,
            adaptive_score=adaptive_score,
            utility_neutral_tolerance=comparison_config.utility_neutral_tolerance,
        ),
        unsafe_retrospective_control=UnsafeRetrospectiveControlExclusion(
            policy_id=unsafe_replay.policy_id,
            replay_result=unsafe_replay,
        ),
    )


def _require_exact_inputs(
    *,
    fixture_set: object,
    comparison_config: object,
    capacity_profile: object,
    scoring_config: object,
    fixed_length_policy: object,
    static_threshold_policy: object,
    adaptive_policy: object,
    unsafe_retrospective_policy: object,
) -> None:
    """Reject structurally similar objects before any policy or scoring work starts."""

    expected = (
        (
            fixture_set,
            SyntheticTraceFixtureSet,
            MatchedPolicyComparisonErrorCode.INVALID_FIXTURE_SET,
        ),
        (
            comparison_config,
            MatchedPolicyComparisonConfig,
            MatchedPolicyComparisonErrorCode.INVALID_COMPARISON_CONFIG,
        ),
        (
            capacity_profile,
            SyntheticCapacityProfile,
            MatchedPolicyComparisonErrorCode.INVALID_CAPACITY_PROFILE,
        ),
        (
            scoring_config,
            PolicyUtilityScoringConfig,
            MatchedPolicyComparisonErrorCode.INVALID_SCORING_CONFIG,
        ),
        (
            fixed_length_policy,
            FixedLengthVerificationPolicy,
            MatchedPolicyComparisonErrorCode.INVALID_FIXED_LENGTH_POLICY,
        ),
        (
            static_threshold_policy,
            StaticThresholdVerificationPolicy,
            MatchedPolicyComparisonErrorCode.INVALID_STATIC_THRESHOLD_POLICY,
        ),
        (
            adaptive_policy,
            CalibratedCausalLoadAwarePolicy,
            MatchedPolicyComparisonErrorCode.INVALID_ADAPTIVE_POLICY,
        ),
        (
            unsafe_retrospective_policy,
            UnsafeRetrospectiveLookaheadPolicy,
            MatchedPolicyComparisonErrorCode.INVALID_UNSAFE_POLICY,
        ),
    )
    for value, expected_type, error_code in expected:
        if type(value) is not expected_type:
            raise MatchedPolicyComparisonError(
                error_code,
                f"matched comparison requires the exact {expected_type.__name__} type",
            )


def _select_case(fixture_set: SyntheticTraceFixtureSet, case_id: str):
    """Resolve exactly one immutable replay case by its governed case ID."""

    matching_cases = tuple(
        case for case in fixture_set.cases if case.runtime_input.case_id == case_id
    )
    if len(matching_cases) != 1:
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.CASE_NOT_FOUND,
            "matched comparison requires exactly one fixture case for case_id",
        )
    return matching_cases[0]


def _validate_case_capacity_profile(
    contexts: tuple, capacity_profile: SyntheticCapacityProfile
) -> None:
    """Require every decision-time snapshot to name the exact declared synthetic profile."""

    for context in contexts:
        snapshot = context.capacity_snapshot
        if (
            snapshot.source is not CapacityProfileSource.SYNTHETIC
            or snapshot.profile_id != capacity_profile.profile_id
        ):
            raise MatchedPolicyComparisonError(
                MatchedPolicyComparisonErrorCode.CAPACITY_PROFILE_MISMATCH,
                "every comparison runtime context must name the exact declared synthetic "
                "capacity profile",
            )
        try:
            capacity_profile.evaluate(snapshot)
        except CapacityProfileError as error:
            raise MatchedPolicyComparisonError(
                MatchedPolicyComparisonErrorCode.CAPACITY_PROFILE_MISMATCH,
                str(error),
            ) from error


def _validate_policy_identity_and_formula(
    *,
    fixed_length_policy: FixedLengthVerificationPolicy,
    static_threshold_policy: StaticThresholdVerificationPolicy,
    adaptive_policy: CalibratedCausalLoadAwarePolicy,
    unsafe_retrospective_policy: UnsafeRetrospectiveLookaheadPolicy,
    capacity_profile: SyntheticCapacityProfile,
    scoring_config: PolicyUtilityScoringConfig,
) -> None:
    """Prevent identity, profile, or utility semantics from drifting across policies."""

    policy_ids = (
        fixed_length_policy.config.policy_id,
        static_threshold_policy.config.policy_id,
        adaptive_policy.config.policy_id,
        unsafe_retrospective_policy.config.policy_id,
    )
    if len(set(policy_ids)) != len(policy_ids):
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.DUPLICATE_POLICY_ID,
            "matched comparison policy IDs must be unique",
        )

    adaptive_descriptor = adaptive_policy.descriptor
    if adaptive_descriptor.capacity_profile_configuration_sha256 != (
        capacity_profile.configuration_sha256()
    ):
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.CAPACITY_PROFILE_MISMATCH,
            "adaptive policy descriptor does not retain the declared comparison profile hash",
        )

    adaptive_config = adaptive_policy.config
    if not math.isclose(
        adaptive_config.accepted_admission_value_units,
        scoring_config.accepted_admission_value_units,
        rel_tol=0.0,
        abs_tol=1e-12,
    ) or not math.isclose(
        adaptive_config.marginal_verification_cost_weight,
        scoring_config.marginal_verification_cost_weight,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.ADAPTIVE_SCORING_CONFIG_MISMATCH,
            "adaptive policy utility weights must exactly match the shared scoring configuration",
        )


def _run_valid_replay(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    case_id: str,
    policy: FixedLengthVerificationPolicy
    | StaticThresholdVerificationPolicy
    | CalibratedCausalLoadAwarePolicy,
    run_id: str,
):
    """Run one valid policy while retaining a comparison-specific typed failure."""

    try:
        return run_valid_policy_replay(
            fixture_set,
            case_id=case_id,
            policy=policy,
            run_id=run_id,
        )
    except DeterministicReplayExecutionError as error:
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.REPLAY_EXECUTION_FAILED,
            f"valid policy replay failed: {error}",
        ) from error


def _score_replay(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    replay_result,
    capacity_profile: SyntheticCapacityProfile,
    scoring_config: PolicyUtilityScoringConfig,
    policy_configuration_sha256: str,
):
    """Score one valid replay without allowing scoring failures to become silent."""

    try:
        return score_valid_policy_replay(
            fixture_set,
            replay_result=replay_result,
            capacity_profile=capacity_profile,
            scoring_config=scoring_config,
            policy_configuration_sha256=policy_configuration_sha256,
        )
    except PolicyUtilityScoringError as error:
        raise MatchedPolicyComparisonError(
            MatchedPolicyComparisonErrorCode.SCORING_FAILED,
            f"matched policy scoring failed: {error}",
        ) from error


def _build_utility_comparison(
    *,
    baseline_score,
    adaptive_score,
    utility_neutral_tolerance: float,
) -> AdaptiveBaselineUtilityComparison:
    """Classify one adaptive-versus-baseline score delta without global promotion."""

    delta = adaptive_score.policy_utility_units - baseline_score.policy_utility_units
    if math.isclose(delta, 0.0, rel_tol=0.0, abs_tol=utility_neutral_tolerance):
        outcome = MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL
    elif delta > 0.0:
        outcome = MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY
    else:
        outcome = MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY

    return AdaptiveBaselineUtilityComparison(
        baseline_policy_id=baseline_score.policy_id,
        baseline_policy_configuration_sha256=baseline_score.policy_configuration_sha256,
        adaptive_policy_id=adaptive_score.policy_id,
        adaptive_policy_configuration_sha256=adaptive_score.policy_configuration_sha256,
        baseline_policy_utility_units=baseline_score.policy_utility_units,
        adaptive_policy_utility_units=adaptive_score.policy_utility_units,
        utility_delta_units=delta,
        utility_neutral_tolerance=utility_neutral_tolerance,
        outcome=outcome,
    )


def _derived_replay_run_id(comparison_run_id: str, policy_id: str) -> str:
    """Return a compact deterministic replay identity without exceeding field limits."""

    digest = hashlib.sha256(f"{comparison_run_id}:{policy_id}\n".encode()).hexdigest()[:24]
    return f"matched-replay-{digest}"
