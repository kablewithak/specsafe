"""Fit, freeze, apply, and persist a calibration-only histogram artifact."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from specsafe.calibration.models import (
    CalibrationFitErrorCode,
    FrozenCalibratorArtifact,
    FrozenCalibratorBin,
    FrozenCalibratorFitProtocol,
)
from specsafe.contracts import (
    SyntheticTraceFixtureSet,
    SyntheticTraceReplayCase,
)


@dataclass(frozen=True, slots=True)
class _CalibrationObservation:
    """Post-hoc fit observation that is never made available to a runtime policy."""

    confidence: float
    observed_acceptance: bool


class CalibrationFitError(ValueError):
    """Raised when fitting cannot preserve calibration-only source provenance."""

    def __init__(self, code: CalibrationFitErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CalibrationArtifactPersistenceError(CalibrationFitError):
    """Raised when a frozen artifact cannot be written as a local JSON evidence file."""


def fit_frozen_histogram_calibrator(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    protocol: FrozenCalibratorFitProtocol | None = None,
) -> FrozenCalibratorArtifact:
    """Fit one deterministic histogram artifact using calibration-split fixtures only.

    The fitter never reads, selects, scores, or retains development, adversarial-regression,
    or final-evaluation observations. Its output remains ineligible for runtime control until
    a later held-out fitness boundary evaluates it.
    """

    if type(fixture_set) is not SyntheticTraceFixtureSet:
        raise CalibrationFitError(
            CalibrationFitErrorCode.INVALID_FIXTURE_SET,
            "frozen calibrator fitting requires the exact SyntheticTraceFixtureSet contract",
        )

    active_protocol = protocol or FrozenCalibratorFitProtocol()
    calibration_cases = tuple(
        case
        for case in fixture_set.cases
        if case.runtime_input.split is active_protocol.calibration_split
    )
    if not calibration_cases:
        raise CalibrationFitError(
            CalibrationFitErrorCode.NO_CALIBRATION_CASES,
            "frozen calibrator fitting requires at least one calibration-split fixture case",
        )

    observations = _collect_calibration_observations(calibration_cases)
    if len(observations) < active_protocol.minimum_observation_count:
        raise CalibrationFitError(
            CalibrationFitErrorCode.INSUFFICIENT_CALIBRATION_OBSERVATIONS,
            "frozen calibrator source observations are below protocol minimum_observation_count",
        )

    global_acceptance_rate = sum(
        observation.observed_acceptance for observation in observations
    ) / len(observations)
    return FrozenCalibratorArtifact(
        protocol=active_protocol,
        fixture_set_id=fixture_set.manifest.fixture_set_id,
        fixture_set_version=fixture_set.manifest.fixture_set_version,
        calibration_case_ids=tuple(
            case.runtime_input.case_id for case in calibration_cases
        ),
        calibration_trace_ids=tuple(
            case.runtime_input.trace_id for case in calibration_cases
        ),
        source_observation_count=len(observations),
        global_observed_acceptance_rate=global_acceptance_rate,
        bins=_build_frozen_bins(
            observations,
            bin_count=active_protocol.bin_count,
            global_acceptance_rate=global_acceptance_rate,
        ),
    )


def apply_frozen_calibrator(
    artifact: FrozenCalibratorArtifact,
    *,
    raw_confidence: float,
) -> float:
    """Map a raw confidence to the frozen bin value without authorizing a policy action."""

    if type(artifact) is not FrozenCalibratorArtifact:
        raise CalibrationFitError(
            CalibrationFitErrorCode.INVALID_ARTIFACT,
            "calibration application requires the exact FrozenCalibratorArtifact contract",
        )
    if not 0.0 <= raw_confidence <= 1.0:
        raise ValueError("raw_confidence must be between zero and one")
    bin_index = min(
        int(raw_confidence * artifact.protocol.bin_count),
        artifact.protocol.bin_count - 1,
    )
    return artifact.bins[bin_index].applied_calibrated_probability


def write_frozen_calibrator_artifact(
    artifact: FrozenCalibratorArtifact,
    destination: Path,
) -> Path:
    """Persist an exact frozen artifact as deterministic UTF-8 JSON at a local path."""

    if type(artifact) is not FrozenCalibratorArtifact:
        raise CalibrationArtifactPersistenceError(
            CalibrationFitErrorCode.INVALID_ARTIFACT,
            "artifact persistence requires the exact FrozenCalibratorArtifact contract",
        )
    if destination.suffix != ".json":
        raise CalibrationArtifactPersistenceError(
            CalibrationFitErrorCode.INVALID_DESTINATION,
            "frozen calibrator destination must use a .json suffix",
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise CalibrationArtifactPersistenceError(
            CalibrationFitErrorCode.INVALID_DESTINATION,
            f"unable to persist frozen calibrator artifact: {destination}",
        ) from error
    return destination


def _collect_calibration_observations(
    calibration_cases: tuple[SyntheticTraceReplayCase, ...],
) -> tuple[_CalibrationObservation, ...]:
    """Join confidence and outcomes only from calibration cases that already align."""

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


def _build_frozen_bins(
    observations: tuple[_CalibrationObservation, ...],
    *,
    bin_count: int,
    global_acceptance_rate: float,
) -> tuple[FrozenCalibratorBin, ...]:
    """Freeze equal-width bins, using the stored global rate only for empty-bin fallback."""

    grouped: list[list[_CalibrationObservation]] = [[] for _ in range(bin_count)]
    for observation in observations:
        bin_index = min(int(observation.confidence * bin_count), bin_count - 1)
        grouped[bin_index].append(observation)

    bins: list[FrozenCalibratorBin] = []
    for bin_index, bin_observations in enumerate(grouped):
        lower_bound = bin_index / bin_count
        upper_bound = (bin_index + 1) / bin_count
        observation_count = len(bin_observations)
        if observation_count == 0:
            bins.append(
                FrozenCalibratorBin(
                    bin_index=bin_index,
                    lower_confidence_bound=lower_bound,
                    upper_confidence_bound=upper_bound,
                    source_observation_count=0,
                    applied_calibrated_probability=global_acceptance_rate,
                )
            )
            continue

        observed_acceptance_rate = sum(
            observation.observed_acceptance for observation in bin_observations
        ) / observation_count
        bins.append(
            FrozenCalibratorBin(
                bin_index=bin_index,
                lower_confidence_bound=lower_bound,
                upper_confidence_bound=upper_bound,
                source_observation_count=observation_count,
                observed_acceptance_rate=observed_acceptance_rate,
                applied_calibrated_probability=observed_acceptance_rate,
            )
        )
    return tuple(bins)
