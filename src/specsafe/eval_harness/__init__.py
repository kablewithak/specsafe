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
from specsafe.eval_harness.governed_comparison import (
    DEFAULT_GOVERNED_MATCHED_POLICY_COMPARISON_PROTOCOL,
    GovernedArtifactReference,
    GovernedMatchedPolicyComparisonError,
    GovernedMatchedPolicyComparisonErrorCode,
    GovernedMatchedPolicyComparisonProtocol,
    GovernedMatchedPolicyComparisonResult,
    GovernedOutcomeCount,
    build_governed_matched_policy_comparison_result,
    canonical_governed_matched_policy_comparison_json,
    default_governed_comparison_result_path,
    run_governed_matched_policy_comparison_once,
    write_governed_matched_policy_comparison_result,
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
    "DEFAULT_GOVERNED_MATCHED_POLICY_COMPARISON_PROTOCOL",
    "GovernedArtifactReference",
    "GovernedMatchedPolicyComparisonError",
    "GovernedMatchedPolicyComparisonErrorCode",
    "GovernedMatchedPolicyComparisonProtocol",
    "GovernedMatchedPolicyComparisonResult",
    "GovernedOutcomeCount",
    "build_governed_matched_policy_comparison_result",
    "canonical_governed_matched_policy_comparison_json",
    "default_governed_comparison_result_path",
    "run_governed_matched_policy_comparison_once",
    "write_governed_matched_policy_comparison_result",
]
