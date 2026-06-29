"""Held-out calibration fitness evidence and promotion-gate contracts."""

from specsafe.heldout_calibration.evaluator import (
    HeldOutCalibrationFitnessError,
    HeldOutCalibrationReportPersistenceError,
    evaluate_heldout_calibration_fitness,
    write_heldout_calibration_fitness_report,
)
from specsafe.heldout_calibration.models import (
    AdaptivePolicyResearchEligibility,
    CalibrationPromotionDecision,
    HeldOutCalibrationBin,
    HeldOutCalibrationFitnessProtocol,
    HeldOutCalibrationFitnessResult,
    HeldOutCalibrationFitnessStatus,
    HeldOutFitnessErrorCode,
    ProbabilityFitnessMetrics,
    RuntimeControlEligibility,
)

__all__ = [
    "AdaptivePolicyResearchEligibility",
    "CalibrationPromotionDecision",
    "HeldOutCalibrationBin",
    "HeldOutCalibrationFitnessError",
    "HeldOutCalibrationFitnessProtocol",
    "HeldOutCalibrationFitnessResult",
    "HeldOutCalibrationFitnessStatus",
    "HeldOutCalibrationReportPersistenceError",
    "HeldOutFitnessErrorCode",
    "ProbabilityFitnessMetrics",
    "RuntimeControlEligibility",
    "evaluate_heldout_calibration_fitness",
    "write_heldout_calibration_fitness_report",
]
