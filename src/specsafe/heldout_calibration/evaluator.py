"""Assess a frozen calibrator once on final-evaluation fixtures and retain the gate result."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from specsafe.calibration import FrozenCalibratorArtifact, apply_frozen_calibrator
from specsafe.contracts import SyntheticTraceFixtureSet, SyntheticTraceReplayCase
from specsafe.heldout_calibration.models import (
    AdaptivePolicyResearchEligibility,
    CalibrationPromotionDecision,
    HeldOutCalibrationBin,
    HeldOutCalibrationFitnessProtocol,
    HeldOutCalibrationFitnessResult,
    HeldOutCalibrationFitnessStatus,
    HeldOutFitnessErrorCode,
    ProbabilityFitnessMetrics,
)


@dataclass(frozen=True, slots=True)
class _HeldOutObservation:
    """One post-hoc final-evaluation observation, never exposed to runtime policy code."""

    raw_probability: float
    calibrated_probability: float
    observed_acceptance: bool


class HeldOutCalibrationFitnessError(ValueError):
    """Raised when held-out assessment or report persistence violates a hard boundary."""

    def __init__(self, code: HeldOutFitnessErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class HeldOutCalibrationReportPersistenceError(HeldOutCalibrationFitnessError):
    """Raised when a held-out report cannot be persisted as local JSON evidence."""


def evaluate_heldout_calibration_fitness(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    calibrator_artifact: FrozenCalibratorArtifact,
    protocol: HeldOutCalibrationFitnessProtocol | None = None,
) -> HeldOutCalibrationFitnessResult:
    """Compare raw and frozen-calibrated probabilities on final evaluation only.

    This is a final-evaluation boundary. The artifact is already frozen. The function does
    not fit, retune, mutate, or replace that artifact, and it never exposes held-out labels
    to a runtime scheduler.
    """

    if type(fixture_set) is not SyntheticTraceFixtureSet:
        raise HeldOutCalibrationFitnessError(
            HeldOutFitnessErrorCode.INVALID_FIXTURE_SET,
            "held-out calibration fitness requires the exact SyntheticTraceFixtureSet contract",
        )
    if type(calibrator_artifact) is not FrozenCalibratorArtifact:
        raise HeldOutCalibrationFitnessError(
            HeldOutFitnessErrorCode.INVALID_CALIBRATOR_ARTIFACT,
            "held-out calibration fitness requires the exact FrozenCalibratorArtifact contract",
        )
    if (
        fixture_set.manifest.fixture_set_id != calibrator_artifact.fixture_set_id
        or fixture_set.manifest.fixture_set_version != calibrator_artifact.fixture_set_version
    ):
        raise HeldOutCalibrationFitnessError(
            HeldOutFitnessErrorCode.ARTIFACT_FIXTURE_MISMATCH,
            "frozen calibrator artifact must match the assessed fixture-set identity and version",
        )

    active_protocol = protocol or HeldOutCalibrationFitnessProtocol()
    assessment_cases = tuple(
        case
        for case in fixture_set.cases
        if case.runtime_input.split is active_protocol.assessment_split
    )
    if not assessment_cases:
        raise HeldOutCalibrationFitnessError(
            HeldOutFitnessErrorCode.NO_FINAL_EVALUATION_CASES,
            "held-out calibration fitness requires at least one final-evaluation fixture case",
        )

    observations = _collect_final_evaluation_observations(
        assessment_cases,
        calibrator_artifact=calibrator_artifact,
    )
    raw_metrics = _build_probability_metrics(
        probabilities=tuple(observation.raw_probability for observation in observations),
        labels=tuple(observation.observed_acceptance for observation in observations),
        bin_count=active_protocol.diagnostic_bin_count,
    )
    calibrated_metrics = _build_probability_metrics(
        probabilities=tuple(observation.calibrated_probability for observation in observations),
        labels=tuple(observation.observed_acceptance for observation in observations),
        bin_count=active_protocol.diagnostic_bin_count,
    )
    brier_improvement = raw_metrics.brier_score - calibrated_metrics.brier_score
    ece_improvement = (
        raw_metrics.expected_calibration_error - calibrated_metrics.expected_calibration_error
    )
    status, promotion_decision, research_eligibility = _derive_gate_outcome(
        observation_count=len(observations),
        brier_improvement=brier_improvement,
        expected_calibration_error_improvement=ece_improvement,
        protocol=active_protocol,
    )

    return HeldOutCalibrationFitnessResult(
        protocol=active_protocol,
        calibrator_artifact=calibrator_artifact,
        fixture_set_id=fixture_set.manifest.fixture_set_id,
        fixture_set_version=fixture_set.manifest.fixture_set_version,
        assessment_case_ids=tuple(
            case.runtime_input.case_id for case in assessment_cases
        ),
        assessment_trace_ids=tuple(
            case.runtime_input.trace_id for case in assessment_cases
        ),
        observation_count=len(observations),
        raw_metrics=raw_metrics,
        calibrated_metrics=calibrated_metrics,
        brier_score_improvement=brier_improvement,
        expected_calibration_error_improvement=ece_improvement,
        status=status,
        promotion_decision=promotion_decision,
        adaptive_policy_research_eligibility=research_eligibility,
    )


def write_heldout_calibration_fitness_report(
    result: HeldOutCalibrationFitnessResult,
    destination: Path,
) -> Path:
    """Persist exact held-out assessment evidence as deterministic local JSON."""

    if type(result) is not HeldOutCalibrationFitnessResult:
        raise HeldOutCalibrationReportPersistenceError(
            HeldOutFitnessErrorCode.INVALID_CALIBRATOR_ARTIFACT,
            "held-out report persistence requires the exact result contract",
        )
    if destination.suffix != ".json":
        raise HeldOutCalibrationReportPersistenceError(
            HeldOutFitnessErrorCode.INVALID_DESTINATION,
            "held-out calibration report destination must use a .json suffix",
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise HeldOutCalibrationReportPersistenceError(
            HeldOutFitnessErrorCode.INVALID_DESTINATION,
            f"unable to persist held-out calibration report: {destination}",
        ) from error
    return destination


def _collect_final_evaluation_observations(
    assessment_cases: tuple[SyntheticTraceReplayCase, ...],
    *,
    calibrator_artifact: FrozenCalibratorArtifact,
) -> tuple[_HeldOutObservation, ...]:
    """Join only held-out confidence and labels after the frozen artifact is fixed."""

    observations: list[_HeldOutObservation] = []
    for case in assessment_cases:
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in case.expected_outcomes.outcomes
        }
        for context in case.runtime_input.contexts:
            outcome = outcomes_by_key[(context.decode_round, context.block_position_index)]
            raw_probability = context.conditional_survival_confidence
            observations.append(
                _HeldOutObservation(
                    raw_probability=raw_probability,
                    calibrated_probability=apply_frozen_calibrator(
                        calibrator_artifact,
                        raw_confidence=raw_probability,
                    ),
                    observed_acceptance=outcome.observed_acceptance,
                )
            )
    return tuple(observations)


def _build_probability_metrics(
    *,
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
    bin_count: int,
) -> ProbabilityFitnessMetrics:
    """Compute Brier, ECE, and fixed bins without data-dependent threshold selection."""

    if len(probabilities) != len(labels):
        raise ValueError("held-out probabilities and labels must have equal lengths")
    if not probabilities:
        raise ValueError("held-out probability metrics require at least one observation")

    brier_score = sum(
        (probability - float(label)) ** 2
        for probability, label in zip(probabilities, labels, strict=True)
    ) / len(probabilities)
    bins = _build_bins(probabilities=probabilities, labels=labels, bin_count=bin_count)
    expected_calibration_error = sum(
        (bin_summary.observation_count / len(probabilities))
        * (bin_summary.absolute_calibration_gap or 0.0)
        for bin_summary in bins
    )
    return ProbabilityFitnessMetrics(
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        bins=bins,
    )


def _build_bins(
    *,
    probabilities: tuple[float, ...],
    labels: tuple[bool, ...],
    bin_count: int,
) -> tuple[HeldOutCalibrationBin, ...]:
    """Build equal-width diagnostic bins with no adaptive rebinning."""

    grouped: list[list[tuple[float, bool]]] = [[] for _ in range(bin_count)]
    for probability, label in zip(probabilities, labels, strict=True):
        bin_index = min(int(probability * bin_count), bin_count - 1)
        grouped[bin_index].append((probability, label))

    bins: list[HeldOutCalibrationBin] = []
    for bin_index, observations in enumerate(grouped):
        lower_bound = bin_index / bin_count
        upper_bound = (bin_index + 1) / bin_count
        if not observations:
            bins.append(
                HeldOutCalibrationBin(
                    bin_index=bin_index,
                    lower_probability_bound=lower_bound,
                    upper_probability_bound=upper_bound,
                    observation_count=0,
                )
            )
            continue
        observation_count = len(observations)
        mean_probability = sum(probability for probability, _ in observations) / observation_count
        observed_acceptance_rate = sum(label for _, label in observations) / observation_count
        bins.append(
            HeldOutCalibrationBin(
                bin_index=bin_index,
                lower_probability_bound=lower_bound,
                upper_probability_bound=upper_bound,
                observation_count=observation_count,
                mean_probability=mean_probability,
                observed_acceptance_rate=observed_acceptance_rate,
                absolute_calibration_gap=abs(mean_probability - observed_acceptance_rate),
            )
        )
    return tuple(bins)


def _derive_gate_outcome(
    *,
    observation_count: int,
    brier_improvement: float,
    expected_calibration_error_improvement: float,
    protocol: HeldOutCalibrationFitnessProtocol,
) -> tuple[
    HeldOutCalibrationFitnessStatus,
    CalibrationPromotionDecision,
    AdaptivePolicyResearchEligibility,
]:
    """Apply predeclared calibration promotion logic without retuning against held-out data."""

    if observation_count < protocol.minimum_observation_count:
        return (
            HeldOutCalibrationFitnessStatus.INSUFFICIENT_HELD_OUT_DATA,
            CalibrationPromotionDecision.NOT_PROMOTED_INSUFFICIENT_HELD_OUT_DATA,
            AdaptivePolicyResearchEligibility.BLOCKED_INSUFFICIENT_HELD_OUT_FITNESS,
        )
    if brier_improvement < 0.0 or expected_calibration_error_improvement < 0.0:
        return (
            HeldOutCalibrationFitnessStatus.CALIBRATOR_REGRESSION,
            CalibrationPromotionDecision.NOT_PROMOTED_CALIBRATOR_REGRESSION,
            AdaptivePolicyResearchEligibility.BLOCKED_HELD_OUT_CALIBRATION_REGRESSION,
        )
    if (
        brier_improvement <= protocol.minimum_brier_score_improvement
        or expected_calibration_error_improvement
        <= protocol.minimum_expected_calibration_error_improvement
    ):
        return (
            HeldOutCalibrationFitnessStatus.NO_MATERIAL_HELD_OUT_IMPROVEMENT,
            CalibrationPromotionDecision.NOT_PROMOTED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
            AdaptivePolicyResearchEligibility.BLOCKED_NO_MATERIAL_HELD_OUT_IMPROVEMENT,
        )
    return (
        HeldOutCalibrationFitnessStatus.PASSES_HELD_OUT_FITNESS,
        CalibrationPromotionDecision.PROMOTED_TO_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
        AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CAUSAL_ADAPTIVE_POLICY_RESEARCH,
    )
