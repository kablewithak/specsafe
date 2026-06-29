"""Evaluate raw confidence only on governed calibration fixtures."""

from __future__ import annotations

from dataclasses import dataclass

from specsafe.confidence_fitness.models import (
    ConfidenceCalibrationBin,
    ConfidenceFitnessErrorCode,
    ConfidenceFitnessProtocolConfig,
    ConfidenceFitnessResult,
    RawConfidenceFitnessStatus,
)
from specsafe.contracts import (
    SyntheticTraceFixtureSet,
    SyntheticTraceReplayCase,
    TraceSplit,
)


@dataclass(frozen=True, slots=True)
class _CalibrationObservation:
    """Internal post-hoc calibration observation; never a policy input."""

    confidence: float
    observed_acceptance: bool


class ConfidenceFitnessEvaluationError(ValueError):
    """Raised when a confidence diagnostic cannot preserve its split boundary."""

    def __init__(self, code: ConfidenceFitnessErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def evaluate_raw_confidence_fitness(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    protocol: ConfidenceFitnessProtocolConfig | None = None,
) -> ConfidenceFitnessResult:
    """Compute diagnostic-only raw-confidence evidence from calibration cases alone.

    This function reads scheduler-visible confidence and post-hoc acceptance labels only
    after a fixture set has been hash-verified and structurally composed. It does not
    fit a calibrator, select runtime thresholds, or authorize automated scheduling.
    """

    if type(fixture_set) is not SyntheticTraceFixtureSet:
        raise ConfidenceFitnessEvaluationError(
            ConfidenceFitnessErrorCode.INVALID_FIXTURE_SET,
            "confidence fitness requires the exact SyntheticTraceFixtureSet contract",
        )

    active_protocol = protocol or ConfidenceFitnessProtocolConfig()
    calibration_cases = tuple(
        case
        for case in fixture_set.cases
        if case.runtime_input.split is TraceSplit.CALIBRATION
    )
    if not calibration_cases:
        raise ConfidenceFitnessEvaluationError(
            ConfidenceFitnessErrorCode.NO_CALIBRATION_CASES,
            "confidence fitness requires at least one calibration-split fixture case",
        )

    observations = _collect_calibration_observations(calibration_cases)
    brier_score = sum(
        (observation.confidence - float(observation.observed_acceptance)) ** 2
        for observation in observations
    ) / len(observations)
    bin_summaries = _build_bin_summaries(observations, active_protocol.bin_count)
    expected_calibration_error = sum(
        (bin_summary.observation_count / len(observations))
        * (bin_summary.absolute_calibration_gap or 0.0)
        for bin_summary in bin_summaries
    )
    status = _derive_status(
        observation_count=len(observations),
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        protocol=active_protocol,
    )

    return ConfidenceFitnessResult(
        protocol=active_protocol,
        fixture_set_id=fixture_set.manifest.fixture_set_id,
        fixture_set_version=fixture_set.manifest.fixture_set_version,
        calibration_case_ids=tuple(
            case.runtime_input.case_id for case in calibration_cases
        ),
        calibration_trace_ids=tuple(
            case.runtime_input.trace_id for case in calibration_cases
        ),
        observation_count=len(observations),
        mean_confidence=sum(observation.confidence for observation in observations)
        / len(observations),
        observed_acceptance_rate=sum(
            observation.observed_acceptance for observation in observations
        )
        / len(observations),
        brier_score=brier_score,
        expected_calibration_error=expected_calibration_error,
        bins=bin_summaries,
        status=status,
    )


def _collect_calibration_observations(
    calibration_cases: tuple[SyntheticTraceReplayCase, ...],
) -> tuple[_CalibrationObservation, ...]:
    """Join confidence and labels post-hoc from already aligned replay cases."""

    observations: list[_CalibrationObservation] = []
    for case in calibration_cases:
        outcomes_by_key = {
            (outcome.decode_round, outcome.block_position_index): outcome
            for outcome in case.expected_outcomes.outcomes
        }
        for context in case.runtime_input.contexts:
            outcome = outcomes_by_key[(context.decode_round, context.block_position_index)]
            observations.append(
                _CalibrationObservation(
                    confidence=context.conditional_survival_confidence,
                    observed_acceptance=outcome.observed_acceptance,
                )
            )
    return tuple(observations)


def _build_bin_summaries(
    observations: tuple[_CalibrationObservation, ...],
    bin_count: int,
) -> tuple[ConfidenceCalibrationBin, ...]:
    """Build fixed equal-width bins without adaptive binning or threshold selection."""

    grouped: list[list[_CalibrationObservation]] = [[] for _ in range(bin_count)]
    for observation in observations:
        bin_index = min(int(observation.confidence * bin_count), bin_count - 1)
        grouped[bin_index].append(observation)

    summaries: list[ConfidenceCalibrationBin] = []
    for bin_index, bin_observations in enumerate(grouped):
        lower_bound = bin_index / bin_count
        upper_bound = (bin_index + 1) / bin_count
        if not bin_observations:
            summaries.append(
                ConfidenceCalibrationBin(
                    bin_index=bin_index,
                    lower_confidence_bound=lower_bound,
                    upper_confidence_bound=upper_bound,
                    observation_count=0,
                )
            )
            continue

        observation_count = len(bin_observations)
        mean_confidence = sum(
            observation.confidence for observation in bin_observations
        ) / observation_count
        observed_acceptance_rate = sum(
            observation.observed_acceptance for observation in bin_observations
        ) / observation_count
        summaries.append(
            ConfidenceCalibrationBin(
                bin_index=bin_index,
                lower_confidence_bound=lower_bound,
                upper_confidence_bound=upper_bound,
                observation_count=observation_count,
                mean_confidence=mean_confidence,
                observed_acceptance_rate=observed_acceptance_rate,
                absolute_calibration_gap=abs(
                    mean_confidence - observed_acceptance_rate
                ),
            )
        )
    return tuple(summaries)


def _derive_status(
    *,
    observation_count: int,
    brier_score: float,
    expected_calibration_error: float,
    protocol: ConfidenceFitnessProtocolConfig,
) -> RawConfidenceFitnessStatus:
    """Apply only the predeclared diagnostic thresholds; do not tune from results."""

    if observation_count < protocol.minimum_observation_count:
        return RawConfidenceFitnessStatus.INSUFFICIENT_CALIBRATION_DATA
    if (
        brier_score <= protocol.maximum_brier_score
        and expected_calibration_error <= protocol.maximum_expected_calibration_error
    ):
        return RawConfidenceFitnessStatus.PASSES_PRECALIBRATION_SCREEN
    return RawConfidenceFitnessStatus.FAILS_PRECALIBRATION_SCREEN
