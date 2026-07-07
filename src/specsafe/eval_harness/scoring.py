"""Deterministic scoring for already-recorded valid policy replays.

The scorer reads runtime capacity snapshots and post-hoc replay summaries only after a
valid replay has completed. It is intentionally separate from policy execution: labels
and score results never flow into a scheduler decision.
"""

from __future__ import annotations

import hashlib
import json

from specsafe.capacity_profiles import CapacityProfileError, SyntheticCapacityProfile
from specsafe.contracts import SyntheticTraceFixtureSet, TraceSplit, VerificationAction
from specsafe.eval_harness.models import (
    AdmittedPositionCost,
    PolicyUtilityScore,
    PolicyUtilityScoringConfig,
    PolicyUtilityScoringErrorCode,
)
from specsafe.trace_replay import ValidPolicyReplayResult

_ALLOWED_SPLITS = frozenset({TraceSplit.DEVELOPMENT, TraceSplit.ADVERSARIAL_REGRESSION})


class PolicyUtilityScoringError(ValueError):
    """Raised when a policy utility score would cross an evidence boundary."""

    def __init__(self, code: PolicyUtilityScoringErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def score_valid_policy_replay(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    replay_result: ValidPolicyReplayResult,
    capacity_profile: SyntheticCapacityProfile,
    scoring_config: PolicyUtilityScoringConfig,
    policy_configuration_sha256: str,
) -> PolicyUtilityScore:
    """Score one valid replay using a declared synthetic capacity profile.

    The scorer accepts only development or adversarial-regression replays in this
    contract slice. Calibration and final-evaluation material remain outside the scoring
    path until a later governed comparison protocol is explicitly introduced.
    """

    _require_exact_types(
        fixture_set=fixture_set,
        replay_result=replay_result,
        capacity_profile=capacity_profile,
        scoring_config=scoring_config,
    )
    if len(policy_configuration_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in policy_configuration_sha256
    ):
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.INVALID_REPLAY_RESULT,
            "policy_configuration_sha256 must be a lowercase SHA-256 hex digest",
        )

    replay_case = _resolve_replay_case(fixture_set, replay_result)
    if replay_result.split not in _ALLOWED_SPLITS:
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.SPLIT_NOT_AUTHORIZED,
            "policy utility scoring currently permits development and adversarial "
            "regression replays only",
        )

    processed_contexts = replay_case.runtime_input.contexts[: len(replay_result.position_results)]
    _validate_replay_context_alignment(replay_result, processed_contexts)

    admitted_costs: list[AdmittedPositionCost] = []
    for context, position_result in zip(
        processed_contexts,
        replay_result.position_results,
        strict=True,
    ):
        if position_result.decision.action is not VerificationAction.ADMIT:
            continue
        try:
            evaluation = capacity_profile.evaluate(context.capacity_snapshot)
        except CapacityProfileError as error:
            raise PolicyUtilityScoringError(
                PolicyUtilityScoringErrorCode.CAPACITY_PROFILE_MISMATCH,
                str(error),
            ) from error
        weighted_cost = (
            evaluation.marginal_verification_cost_units
            * scoring_config.marginal_verification_cost_weight
        )
        admitted_costs.append(
            AdmittedPositionCost(
                decode_round=context.decode_round,
                block_position_index=context.block_position_index,
                request_token_load=evaluation.request_token_load,
                selected_maximum_request_token_load=evaluation.selected_maximum_request_token_load,
                marginal_verification_cost_units=evaluation.marginal_verification_cost_units,
                weighted_verification_cost_units=weighted_cost,
            )
        )

    accepted_work_value = (
        replay_result.accepted_admission_count * scoring_config.accepted_admission_value_units
    )
    verification_cost = sum(item.weighted_verification_cost_units for item in admitted_costs)

    return PolicyUtilityScore(
        scoring_id=scoring_config.scoring_id,
        scoring_config_sha256=scoring_config.configuration_sha256(),
        policy_id=replay_result.policy_id,
        policy_configuration_sha256=policy_configuration_sha256,
        replay_run_id=replay_result.run_id,
        replay_result_sha256=_canonical_sha256(replay_result.model_dump(mode="json")),
        fixture_set_id=replay_result.fixture_set_id,
        fixture_set_version=replay_result.fixture_set_version,
        fixture_id=replay_result.fixture_id,
        case_id=replay_result.case_id,
        trace_id=replay_result.trace_id,
        split=replay_result.split,
        capacity_profile_id=capacity_profile.profile_id,
        capacity_profile_version=capacity_profile.profile_version,
        capacity_profile_kind=capacity_profile.profile_kind,
        capacity_profile_configuration_sha256=capacity_profile.configuration_sha256(),
        processed_position_count=len(replay_result.position_results),
        admitted_position_count=replay_result.admitted_position_count,
        accepted_admission_count=replay_result.accepted_admission_count,
        rejected_admission_count=replay_result.rejected_admission_count,
        accepted_work_value_units=accepted_work_value,
        verification_cost_units=verification_cost,
        policy_utility_units=accepted_work_value - verification_cost,
        admitted_position_costs=tuple(admitted_costs),
    )


def _require_exact_types(
    *,
    fixture_set: object,
    replay_result: object,
    capacity_profile: object,
    scoring_config: object,
) -> None:
    """Reject structurally similar objects at the central scoring boundary."""

    if type(fixture_set) is not SyntheticTraceFixtureSet:
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.INVALID_FIXTURE_SET,
            "policy utility scoring requires the exact SyntheticTraceFixtureSet contract",
        )
    if type(replay_result) is not ValidPolicyReplayResult:
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.INVALID_REPLAY_RESULT,
            "policy utility scoring requires the exact ValidPolicyReplayResult contract",
        )
    if type(capacity_profile) is not SyntheticCapacityProfile:
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.INVALID_CAPACITY_PROFILE,
            "policy utility scoring requires the exact SyntheticCapacityProfile contract",
        )
    if type(scoring_config) is not PolicyUtilityScoringConfig:
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.INVALID_SCORING_CONFIG,
            "policy utility scoring requires the exact PolicyUtilityScoringConfig contract",
        )


def _resolve_replay_case(
    fixture_set: SyntheticTraceFixtureSet,
    replay_result: ValidPolicyReplayResult,
):
    """Resolve and cross-check the single immutable case named by a replay result."""

    manifest = fixture_set.manifest
    if (
        replay_result.fixture_set_id != manifest.fixture_set_id
        or replay_result.fixture_set_version != manifest.fixture_set_version
    ):
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.REPLAY_FIXTURE_SET_MISMATCH,
            "replay result fixture-set identity does not match the scorer fixture set",
        )

    matching_cases = tuple(
        case for case in fixture_set.cases if case.runtime_input.case_id == replay_result.case_id
    )
    if len(matching_cases) != 1:
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.REPLAY_CASE_NOT_FOUND,
            "scorer fixture set does not contain exactly one replay case for the result",
        )

    replay_case = matching_cases[0]
    runtime = replay_case.runtime_input
    if (
        replay_result.fixture_id != runtime.fixture_id
        or replay_result.trace_id != runtime.trace_id
        or replay_result.split is not runtime.split
    ):
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.REPLAY_CASE_IDENTITY_MISMATCH,
            "replay result identity does not match the selected immutable replay case",
        )
    return replay_case


def _validate_replay_context_alignment(
    replay_result: ValidPolicyReplayResult,
    processed_contexts: tuple,
) -> None:
    """Ensure scoreable decisions are the exact sequential prefix of fixture contexts."""

    if len(processed_contexts) != len(replay_result.position_results):
        raise PolicyUtilityScoringError(
            PolicyUtilityScoringErrorCode.REPLAY_CONTEXT_MISMATCH,
            "replay result processed more positions than the immutable runtime case contains",
        )

    for context, position_result in zip(
        processed_contexts,
        replay_result.position_results,
        strict=True,
    ):
        decision = position_result.decision
        if (
            decision.trace_id != context.trace_id
            or decision.decode_round != context.decode_round
            or decision.block_position_index != context.block_position_index
        ):
            raise PolicyUtilityScoringError(
                PolicyUtilityScoringErrorCode.REPLAY_CONTEXT_MISMATCH,
                "replay decisions must align with the sequential runtime-context prefix",
            )


def _canonical_sha256(payload: object) -> str:
    """Return a stable hash for persisted result provenance."""

    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(f"{canonical_json}\n".encode()).hexdigest()
