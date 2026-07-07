"""Shared evaluation contracts for controlled, synthetic SpecSafe policy evidence."""

from specsafe.eval_harness.comparison import (
    MatchedPolicyComparisonError,
    run_matched_policy_comparison,
)
from specsafe.eval_harness.comparison_models import (
    AdaptiveBaselineUtilityComparison,
    MatchedPolicyComparisonConfig,
    MatchedPolicyComparisonErrorCode,
    MatchedPolicyComparisonEvidenceClass,
    MatchedPolicyComparisonOutcome,
    MatchedPolicyComparisonResult,
    UnsafeRetrospectiveControlExclusion,
)
from specsafe.eval_harness.models import (
    AdmittedPositionCost,
    PolicyUtilityScore,
    PolicyUtilityScoringConfig,
    PolicyUtilityScoringErrorCode,
    PolicyUtilityUnit,
)
from specsafe.eval_harness.scoring import (
    PolicyUtilityScoringError,
    score_valid_policy_replay,
)

__all__ = [
    "AdaptiveBaselineUtilityComparison",
    "AdmittedPositionCost",
    "MatchedPolicyComparisonConfig",
    "MatchedPolicyComparisonError",
    "MatchedPolicyComparisonErrorCode",
    "MatchedPolicyComparisonEvidenceClass",
    "MatchedPolicyComparisonOutcome",
    "MatchedPolicyComparisonResult",
    "PolicyUtilityScore",
    "PolicyUtilityScoringConfig",
    "PolicyUtilityScoringError",
    "PolicyUtilityScoringErrorCode",
    "PolicyUtilityUnit",
    "UnsafeRetrospectiveControlExclusion",
    "run_matched_policy_comparison",
    "score_valid_policy_replay",
]
