"""Raw-confidence diagnostic contracts for the governed calibration split."""

from specsafe.confidence_fitness.evaluator import (
    ConfidenceFitnessEvaluationError,
    evaluate_raw_confidence_fitness,
)
from specsafe.confidence_fitness.models import (
    AutomationControlEligibility,
    ConfidenceCalibrationBin,
    ConfidenceFitnessErrorCode,
    ConfidenceFitnessProtocolConfig,
    ConfidenceFitnessResult,
    RawConfidenceFitnessStatus,
)

__all__ = [
    "AutomationControlEligibility",
    "ConfidenceCalibrationBin",
    "ConfidenceFitnessErrorCode",
    "ConfidenceFitnessEvaluationError",
    "ConfidenceFitnessProtocolConfig",
    "ConfidenceFitnessResult",
    "RawConfidenceFitnessStatus",
    "evaluate_raw_confidence_fitness",
]
