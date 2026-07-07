"""Strict contracts for non-comparative synthetic policy-utility scoring.

The contracts in this module retain a declared scoring formula and its inputs after a
causal replay already exists. They do not choose a policy, change a policy decision, or
permit a winner claim.
"""

from __future__ import annotations

import hashlib
import json
import math
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.capacity_profiles import CapacityProfileKind
from specsafe.contracts import TraceSplit
from specsafe.contracts.models import StrictContract


class PolicyUtilityUnit(StrEnum):
    """Synthetic units used by the predeclared utility formula."""

    NORMALIZED_POLICY_UTILITY_UNITS = "normalized_policy_utility_units"


class PolicyUtilityScoringErrorCode(StrEnum):
    """Machine-readable failures for the shared policy-utility scorer."""

    INVALID_FIXTURE_SET = "invalid_fixture_set"
    INVALID_REPLAY_RESULT = "invalid_replay_result"
    INVALID_CAPACITY_PROFILE = "invalid_capacity_profile"
    INVALID_SCORING_CONFIG = "invalid_scoring_config"
    REPLAY_FIXTURE_SET_MISMATCH = "replay_fixture_set_mismatch"
    REPLAY_CASE_NOT_FOUND = "replay_case_not_found"
    REPLAY_CASE_IDENTITY_MISMATCH = "replay_case_identity_mismatch"
    SPLIT_NOT_AUTHORIZED = "policy_utility_split_not_authorized"
    REPLAY_CONTEXT_MISMATCH = "replay_context_mismatch"
    CAPACITY_PROFILE_MISMATCH = "policy_utility_capacity_profile_mismatch"


class PolicyUtilityScoringConfig(StrictContract):
    """Predeclared synthetic formula for one non-comparative policy score.

    Formula::

        policy_utility = accepted_admission_count * accepted_admission_value_units
                         - sum(admitted marginal cost * marginal_cost_weight)

    The values are governed synthetic proxy units. They are not latency, cost, or
    throughput measurements.
    """

    schema_version: Literal["policy-utility-scoring-v1"] = "policy-utility-scoring-v1"
    scoring_id: str = Field(min_length=1, max_length=128)
    utility_unit: Literal[PolicyUtilityUnit.NORMALIZED_POLICY_UTILITY_UNITS] = (
        PolicyUtilityUnit.NORMALIZED_POLICY_UTILITY_UNITS
    )
    accepted_admission_value_units: float = Field(gt=0.0)
    marginal_verification_cost_weight: float = Field(gt=0.0)

    def configuration_sha256(self) -> str:
        """Return the stable hash for the full declared scoring configuration."""

        canonical_json = json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(f"{canonical_json}\n".encode()).hexdigest()


class AdmittedPositionCost(StrictContract):
    """One post-hoc admitted-position cost derived from a declared profile."""

    decode_round: int = Field(ge=0)
    block_position_index: int = Field(ge=1)
    request_token_load: int = Field(ge=0)
    selected_maximum_request_token_load: int | None = Field(default=None, ge=0)
    marginal_verification_cost_units: float = Field(ge=0.0)
    weighted_verification_cost_units: float = Field(ge=0.0)


class PolicyUtilityScore(StrictContract):
    """One synthetic score for an already-valid causal policy replay.

    This score is intentionally non-comparative. Its presence does not mean a policy
    won, should be promoted, or is valid on held-out evidence.
    """

    schema_version: Literal["policy-utility-score-v1"] = "policy-utility-score-v1"
    scoring_id: str = Field(min_length=1, max_length=128)
    scoring_config_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    utility_unit: Literal[PolicyUtilityUnit.NORMALIZED_POLICY_UTILITY_UNITS] = (
        PolicyUtilityUnit.NORMALIZED_POLICY_UTILITY_UNITS
    )
    policy_id: str = Field(min_length=1, max_length=128)
    policy_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    replay_run_id: str = Field(min_length=1, max_length=128)
    replay_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
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
    processed_position_count: int = Field(ge=1)
    admitted_position_count: int = Field(ge=0)
    accepted_admission_count: int = Field(ge=0)
    rejected_admission_count: int = Field(ge=0)
    accepted_work_value_units: float = Field(ge=0.0)
    verification_cost_units: float = Field(ge=0.0)
    policy_utility_units: float
    admitted_position_costs: tuple[AdmittedPositionCost, ...]
    comparison_claim_status: Literal["no_cross_policy_winner_claim"] = (
        "no_cross_policy_winner_claim"
    )

    @model_validator(mode="after")
    def validate_score_summary(self) -> PolicyUtilityScore:
        """Keep retained aggregate fields aligned with inspected position costs."""

        if self.accepted_admission_count > self.admitted_position_count:
            raise ValueError("accepted admissions cannot exceed admitted positions")
        if self.rejected_admission_count != (
            self.admitted_position_count - self.accepted_admission_count
        ):
            raise ValueError("rejected admissions must equal admitted minus accepted")
        if len(self.admitted_position_costs) != self.admitted_position_count:
            raise ValueError("admitted position costs must match admitted position count")

        retained_cost = sum(
            item.weighted_verification_cost_units for item in self.admitted_position_costs
        )
        if not math.isclose(
            self.verification_cost_units,
            retained_cost,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("verification cost must match retained admitted-position costs")
        return self
