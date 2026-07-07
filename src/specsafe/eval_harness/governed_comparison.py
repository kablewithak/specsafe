"""Governed, write-once execution for V5 controlled synthetic policy comparison.

This boundary executes the already-frozen matched-comparison fixture corpus under fixed
policy, scoring, and capacity-profile configuration. It is deliberately not a report or
promotion gate: it retains case-level valid, neutral, losing, and causally invalid control
results without selecting a global winner or accessing V5 final-evaluation labels.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from specsafe.capacity_profiles import load_synthetic_capacity_profile_fixture_set
from specsafe.contracts.models import StrictContract
from specsafe.eval_harness.comparison import run_matched_policy_comparison
from specsafe.eval_harness.comparison_models import (
    MatchedPolicyComparisonConfig,
    MatchedPolicyComparisonOutcome,
    MatchedPolicyComparisonResult,
)
from specsafe.eval_harness.models import PolicyUtilityScoringConfig
from specsafe.heldout_calibration import (
    V5AdaptivePolicyResearchEligibility,
    V5BoundedMonotoneBetaCalibrationArtifact,
    V5FinalHeldOutAssessmentResult,
    V5FinalHeldOutAssessmentStatus,
)
from specsafe.scheduling import (
    CalibratedCausalLoadAwarePolicy,
    CalibratedCausalLoadAwarePolicyConfig,
    FixedLengthPolicyConfig,
    FixedLengthVerificationPolicy,
    StaticThresholdPolicyConfig,
    StaticThresholdVerificationPolicy,
    SyntheticCapacityProfileReference,
    UnsafeRetrospectiveLookaheadPolicy,
    V5RetainedCalibrationAuthorization,
)
from specsafe.traces import load_synthetic_trace_fixture_set

_PROTOCOL_ID = "v5_controlled_synthetic_matched_policy_comparison_protocol_v1"
_RESULT_SCHEMA_VERSION = "v5-controlled-synthetic-policy-comparison-result-v1"
_DEFAULT_RUN_ID = "v5-controlled-synthetic-policy-comparison-run-1"
_FIXTURE_RELATIVE_PATH = "data/fixtures/synthetic_matched_policy_comparison_v1"
_CAPACITY_RELATIVE_PATH = "data/fixtures/synthetic_capacity_profiles/v1"
_CALIBRATION_ARTIFACT_RELATIVE_PATH = (
    "data/fixtures/synthetic_calibration_successor_v5/"
    "bounded_monotone_beta_calibration_artifact.json"
)
_V5_ELIGIBILITY_RESULT_RELATIVE_PATH = (
    "evidence/heldout-calibration/v5-final-heldout-calibration-assessment-v1/result.json"
)
_DEFAULT_RESULT_RELATIVE_PATH = (
    "evidence/matched-policy-comparison/v5-controlled-synthetic-comparison-v1/result.json"
)
_EXPECTED_FIXTURE_MANIFEST_SHA256 = (
    "d4ea55d7e4fee04b60af949f1cd26189c48233eac5770ec852c5b69066b8d31c"
)
_EXPECTED_CAPACITY_MANIFEST_SHA256 = (
    "3a7c56e56804c82ce87173a291cef0a1577a788ff461b9f56bc2e51d725dfe0d"
)
_EXPECTED_CALIBRATION_ARTIFACT_SHA256 = (
    "a3baeb2db94221d68a69fc757c8865e384e3ac92ca05585919188fe1c744cd14"
)
_EXPECTED_V5_ELIGIBILITY_RESULT_SHA256 = (
    "f985ef8df30a5d920194a05f7d5115431420f8ed40a1252d33af62f5d0882ab9"
)
_EXPECTED_CASE_IDS = (
    "MPC5-101",
    "MPC5-102",
    "MPC5-103",
    "MPC5-104",
    "MPC5-105",
    "MPC5-106",
)


class GovernedMatchedPolicyComparisonErrorCode(StrEnum):
    """Machine-readable failures for controlled synthetic comparison execution."""

    INVALID_PROJECT_ROOT = "governed_comparison_invalid_project_root"
    INVALID_PROTOCOL = "governed_comparison_invalid_protocol"
    FIXTURE_PROVENANCE_MISMATCH = "governed_comparison_fixture_provenance_mismatch"
    CAPACITY_PROVENANCE_MISMATCH = "governed_comparison_capacity_provenance_mismatch"
    CALIBRATION_ARTIFACT_MISMATCH = "governed_comparison_calibration_artifact_mismatch"
    V5_ELIGIBILITY_MISMATCH = "governed_comparison_v5_eligibility_mismatch"
    COMPARISON_EXECUTION_FAILED = "governed_comparison_execution_failed"
    DESTINATION_ALREADY_EXISTS = "governed_comparison_destination_already_exists"
    INVALID_DESTINATION = "governed_comparison_invalid_destination"
    CANONICAL_SERIALIZATION_FAILED = "governed_comparison_canonical_serialization_failed"


class GovernedMatchedPolicyComparisonError(ValueError):
    """Raised when the governed runner cannot retain trustworthy comparison evidence."""

    def __init__(self, code: GovernedMatchedPolicyComparisonErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class GovernedMatchedPolicyComparisonProtocol(StrictContract):
    """Fixed execution semantics for one controlled synthetic comparison corpus."""

    protocol_id: Literal["v5_controlled_synthetic_matched_policy_comparison_protocol_v1"] = (
        _PROTOCOL_ID
    )
    fixture_set_id: Literal["synthetic-matched-policy-comparison-v1"] = (
        "synthetic-matched-policy-comparison-v1"
    )
    fixture_set_version: Literal["1.0.0"] = "1.0.0"
    expected_case_ids: tuple[str, ...] = _EXPECTED_CASE_IDS
    expected_case_count: Literal[6] = 6
    comparison_id: Literal["v5-controlled-synthetic-comparison-v1"] = (
        "v5-controlled-synthetic-comparison-v1"
    )
    scoring_id: Literal["matched-corpus-utility-v1"] = "matched-corpus-utility-v1"
    fixed_length_policy_id: Literal["fixed-matched-corpus-v1"] = "fixed-matched-corpus-v1"
    static_threshold_policy_id: Literal["threshold-matched-corpus-v1"] = (
        "threshold-matched-corpus-v1"
    )
    adaptive_policy_id: Literal["adaptive-matched-corpus-v1"] = "adaptive-matched-corpus-v1"
    unsafe_policy_id: Literal["unsafe-retrospective-lookahead-v1"] = (
        "unsafe-retrospective-lookahead-v1"
    )
    accepted_admission_value_units: Literal[1.0] = 1.0
    marginal_verification_cost_weight: Literal[1.0] = 1.0
    static_threshold: Literal[0.6] = 0.6
    fixed_length: Literal[4] = 4
    utility_neutral_tolerance: Literal[0.000000000001] = 0.000000000001
    evidence_class: Literal["synthetic_controlled"] = "synthetic_controlled"
    calibration_refit_performed: Literal[False] = False
    final_evaluation_accessed: Literal[False] = False
    runtime_control_eligible: Literal[False] = False
    promotion_eligible: Literal[False] = False
    write_mode: Literal["write_once"] = "write_once"

    @model_validator(mode="after")
    def validate_predeclared_case_namespace(
        self,
    ) -> GovernedMatchedPolicyComparisonProtocol:
        """Prevent a post-hoc case selection from silently changing governed coverage."""

        if self.expected_case_ids != _EXPECTED_CASE_IDS:
            raise ValueError("expected_case_ids must retain the governed six-case corpus order")
        if len(set(self.expected_case_ids)) != self.expected_case_count:
            raise ValueError("expected_case_ids must be unique and match expected_case_count")
        return self

    def configuration_sha256(self) -> str:
        """Return the stable hash of fixed runner semantics."""

        return _sha256_bytes(_canonical_json_bytes(self.model_dump(mode="json")))


DEFAULT_GOVERNED_MATCHED_POLICY_COMPARISON_PROTOCOL = GovernedMatchedPolicyComparisonProtocol()


class GovernedArtifactReference(StrictContract):
    """Hash-addressed local input used by the controlled comparison runner."""

    relative_path: str = Field(min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_safe_relative_path(self) -> GovernedArtifactReference:
        """Reject absolute paths and parent traversal in retained evidence."""

        if (
            self.relative_path.startswith("/")
            or "\\" in self.relative_path
            or ".." in self.relative_path.split("/")
        ):
            raise ValueError("relative_path must be a safe POSIX project-relative path")
        return self


class GovernedOutcomeCount(StrictContract):
    """Count one retained case-level comparison outcome without selecting a winner."""

    outcome: MatchedPolicyComparisonOutcome
    case_count: int = Field(ge=0)


class GovernedMatchedPolicyComparisonResult(StrictContract):
    """Write-once controlled synthetic comparison evidence, without report promotion."""

    schema_version: Literal["v5-controlled-synthetic-policy-comparison-result-v1"] = (
        _RESULT_SCHEMA_VERSION
    )
    protocol: GovernedMatchedPolicyComparisonProtocol
    protocol_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    run_id: str = Field(min_length=1, max_length=128)
    fixture_manifest: GovernedArtifactReference
    capacity_profile_manifest: GovernedArtifactReference
    calibration_artifact: GovernedArtifactReference
    v5_calibration_eligibility_assessment: GovernedArtifactReference
    case_results: tuple[MatchedPolicyComparisonResult, ...] = Field(min_length=1)
    case_count: int = Field(ge=1)
    valid_matched_comparison_count: int = Field(ge=0)
    unsafe_control_exclusion_count: int = Field(ge=0)
    adaptive_vs_fixed_length_outcome_counts: tuple[GovernedOutcomeCount, ...]
    adaptive_vs_static_threshold_outcome_counts: tuple[GovernedOutcomeCount, ...]
    execution_status: Literal["retained_controlled_synthetic_case_level_results"] = (
        "retained_controlled_synthetic_case_level_results"
    )
    claim_status: Literal["no_global_winner_or_runtime_promotion_claim"] = (
        "no_global_winner_or_runtime_promotion_claim"
    )
    calibration_refit_performed: Literal[False] = False
    final_evaluation_accessed: Literal[False] = False
    runtime_control_eligible: Literal[False] = False
    promotion_eligible: Literal[False] = False
    write_mode: Literal["write_once"] = "write_once"

    @model_validator(mode="after")
    def validate_retained_comparison_integrity(
        self,
    ) -> GovernedMatchedPolicyComparisonResult:
        """Require complete fixed coverage and truthful count summaries."""

        if type(self.protocol) is not GovernedMatchedPolicyComparisonProtocol:
            raise ValueError("result requires the exact governed comparison protocol")
        if self.protocol_configuration_sha256 != self.protocol.configuration_sha256():
            raise ValueError("protocol_configuration_sha256 must match the retained protocol")
        case_ids = tuple(case.case_id for case in self.case_results)
        if case_ids != self.protocol.expected_case_ids:
            raise ValueError("case_results must retain the complete governed case order")
        if self.case_count != len(self.case_results):
            raise ValueError("case_count must match retained case_results")
        if self.valid_matched_comparison_count != self.case_count:
            raise ValueError("every governed corpus case must retain one valid matched comparison")
        if self.unsafe_control_exclusion_count != self.case_count:
            raise ValueError("every governed corpus case must retain one unsafe-control exclusion")
        for case in self.case_results:
            if case.comparison_id != self.protocol.comparison_id:
                raise ValueError("every case result must use the protocol comparison_id")
            if case.validity_status != "valid_matched_synthetic_comparison":
                raise ValueError("every retained case must remain a valid matched comparison")
            if case.claim_status != "case_level_comparison_only_no_promotion_claim":
                raise ValueError("case result claim status must remain non-promotional")
            if case.fixed_length_policy.policy_id != self.protocol.fixed_length_policy_id:
                raise ValueError("fixed policy identity drifted from the predeclared protocol")
            if case.static_threshold_policy.policy_id != self.protocol.static_threshold_policy_id:
                raise ValueError("threshold policy identity drifted from the predeclared protocol")
            if case.adaptive_policy.policy_id != self.protocol.adaptive_policy_id:
                raise ValueError("adaptive policy identity drifted from the predeclared protocol")
            if case.unsafe_retrospective_control.policy_id != self.protocol.unsafe_policy_id:
                raise ValueError("unsafe policy identity drifted from the predeclared protocol")
        _validate_outcome_counts(
            self.adaptive_vs_fixed_length_outcome_counts,
            self.case_results,
            comparison_name="adaptive_vs_fixed_length",
        )
        _validate_outcome_counts(
            self.adaptive_vs_static_threshold_outcome_counts,
            self.case_results,
            comparison_name="adaptive_vs_static_threshold",
        )
        return self


def build_governed_matched_policy_comparison_result(
    project_root: Path,
    *,
    protocol: GovernedMatchedPolicyComparisonProtocol = (
        DEFAULT_GOVERNED_MATCHED_POLICY_COMPARISON_PROTOCOL
    ),
    run_id: str = _DEFAULT_RUN_ID,
) -> GovernedMatchedPolicyComparisonResult:
    """Execute the six-case controlled corpus without persistence or report generation."""

    if type(protocol) is not GovernedMatchedPolicyComparisonProtocol:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.INVALID_PROTOCOL,
            "governed comparison requires the exact predeclared protocol",
        )
    if not run_id or len(run_id) > 128:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.INVALID_PROTOCOL,
            "run_id must contain between 1 and 128 characters",
        )

    root = _require_project_root(project_root)
    fixture_manifest = _require_artifact_hash(
        root,
        f"{_FIXTURE_RELATIVE_PATH}/manifest.json",
        _EXPECTED_FIXTURE_MANIFEST_SHA256,
        GovernedMatchedPolicyComparisonErrorCode.FIXTURE_PROVENANCE_MISMATCH,
    )
    capacity_manifest = _require_artifact_hash(
        root,
        f"{_CAPACITY_RELATIVE_PATH}/manifest.json",
        _EXPECTED_CAPACITY_MANIFEST_SHA256,
        GovernedMatchedPolicyComparisonErrorCode.CAPACITY_PROVENANCE_MISMATCH,
    )
    calibration_artifact_reference = _require_artifact_hash(
        root,
        _CALIBRATION_ARTIFACT_RELATIVE_PATH,
        _EXPECTED_CALIBRATION_ARTIFACT_SHA256,
        GovernedMatchedPolicyComparisonErrorCode.CALIBRATION_ARTIFACT_MISMATCH,
    )
    v5_assessment_reference = _require_artifact_hash(
        root,
        _V5_ELIGIBILITY_RESULT_RELATIVE_PATH,
        _EXPECTED_V5_ELIGIBILITY_RESULT_SHA256,
        GovernedMatchedPolicyComparisonErrorCode.V5_ELIGIBILITY_MISMATCH,
    )

    fixture_set = _load_fixture_set(root)
    _validate_fixture_set(fixture_set, protocol)
    profile_set = _load_profile_set(root)
    artifact = _load_calibration_artifact(root)
    _validate_v5_eligibility_assessment(root)

    comparison_config = MatchedPolicyComparisonConfig(
        comparison_id=protocol.comparison_id,
        utility_neutral_tolerance=protocol.utility_neutral_tolerance,
    )
    scoring_config = PolicyUtilityScoringConfig(
        scoring_id=protocol.scoring_id,
        accepted_admission_value_units=protocol.accepted_admission_value_units,
        marginal_verification_cost_weight=protocol.marginal_verification_cost_weight,
    )

    case_results: list[MatchedPolicyComparisonResult] = []
    for case_id in protocol.expected_case_ids:
        profile_id = _profile_id_for_case(fixture_set, case_id)
        profile = profile_set.profile_for_id(profile_id)
        fixed_policy, threshold_policy, adaptive_policy, unsafe_policy = _build_policies(
            protocol=protocol,
            artifact=artifact,
            profile=profile,
        )
        try:
            case_result = run_matched_policy_comparison(
                fixture_set,
                case_id=case_id,
                comparison_config=comparison_config,
                run_id=f"{run_id}-{case_id.lower()}",
                capacity_profile=profile,
                scoring_config=scoring_config,
                fixed_length_policy=fixed_policy,
                static_threshold_policy=threshold_policy,
                adaptive_policy=adaptive_policy,
                unsafe_retrospective_policy=unsafe_policy,
            )
        except Exception as error:
            raise GovernedMatchedPolicyComparisonError(
                GovernedMatchedPolicyComparisonErrorCode.COMPARISON_EXECUTION_FAILED,
                f"governed matched comparison failed for {case_id}: {error}",
            ) from error
        case_results.append(case_result)

    retained_cases = tuple(case_results)
    return GovernedMatchedPolicyComparisonResult(
        protocol=protocol,
        protocol_configuration_sha256=protocol.configuration_sha256(),
        run_id=run_id,
        fixture_manifest=fixture_manifest,
        capacity_profile_manifest=capacity_manifest,
        calibration_artifact=calibration_artifact_reference,
        v5_calibration_eligibility_assessment=v5_assessment_reference,
        case_results=retained_cases,
        case_count=len(retained_cases),
        valid_matched_comparison_count=len(retained_cases),
        unsafe_control_exclusion_count=len(retained_cases),
        adaptive_vs_fixed_length_outcome_counts=_outcome_counts(
            retained_cases,
            comparison_name="adaptive_vs_fixed_length",
        ),
        adaptive_vs_static_threshold_outcome_counts=_outcome_counts(
            retained_cases,
            comparison_name="adaptive_vs_static_threshold",
        ),
    )


def run_governed_matched_policy_comparison_once(
    project_root: Path,
    destination: Path,
) -> tuple[GovernedMatchedPolicyComparisonResult, Path]:
    """Build and persist one canonical comparison result; reject overwrite attempts."""

    root = _require_project_root(project_root)
    resolved_destination = destination.resolve()
    try:
        resolved_destination.relative_to(root)
    except ValueError as error:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.INVALID_DESTINATION,
            "comparison destination must remain inside the project root",
        ) from error
    if resolved_destination.exists():
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.DESTINATION_ALREADY_EXISTS,
            f"governed comparison is write-once and already exists: {resolved_destination}",
        )

    result = build_governed_matched_policy_comparison_result(root)
    try:
        write_governed_matched_policy_comparison_result(result, resolved_destination)
    except Exception:
        try:
            resolved_destination.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return result, resolved_destination


def write_governed_matched_policy_comparison_result(
    result: GovernedMatchedPolicyComparisonResult,
    destination: Path,
) -> Path:
    """Persist a canonical write-once result without producing a public report."""

    if type(result) is not GovernedMatchedPolicyComparisonResult:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.INVALID_PROTOCOL,
            "write requires the exact governed comparison result contract",
        )
    if destination.exists():
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.DESTINATION_ALREADY_EXISTS,
            f"governed comparison is write-once and already exists: {destination}",
        )
    try:
        payload = canonical_governed_matched_policy_comparison_json(result)
    except (TypeError, ValueError) as error:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.CANONICAL_SERIALIZATION_FAILED,
            f"unable to serialize governed comparison result canonically: {error}",
        ) from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    except FileExistsError as error:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.DESTINATION_ALREADY_EXISTS,
            f"governed comparison is write-once and already exists: {destination}",
        ) from error
    return destination


def canonical_governed_matched_policy_comparison_json(
    result: GovernedMatchedPolicyComparisonResult,
) -> str:
    """Return deterministic JSON for content hashing and repository evidence retention."""

    if type(result) is not GovernedMatchedPolicyComparisonResult:
        raise TypeError("canonical serialization requires GovernedMatchedPolicyComparisonResult")
    return _canonical_json_bytes(result.model_dump(mode="json")).decode("ascii")


def default_governed_comparison_result_path(project_root: Path) -> Path:
    """Return the one repository path reserved for retained controlled comparison evidence."""

    return _require_project_root(project_root) / _DEFAULT_RESULT_RELATIVE_PATH


def _require_project_root(project_root: Path) -> Path:
    root = project_root.resolve()
    if not (root / "pyproject.toml").is_file():
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.INVALID_PROJECT_ROOT,
            "project_root must contain pyproject.toml",
        )
    return root


def _require_artifact_hash(
    root: Path,
    relative_path: str,
    expected_sha256: str,
    error_code: GovernedMatchedPolicyComparisonErrorCode,
) -> GovernedArtifactReference:
    path = root / relative_path
    if not path.is_file():
        raise GovernedMatchedPolicyComparisonError(
            error_code,
            f"required governed artifact is missing: {relative_path}",
        )
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise GovernedMatchedPolicyComparisonError(
            error_code,
            f"governed artifact hash mismatch for {relative_path}",
        )
    return GovernedArtifactReference(relative_path=relative_path, sha256=actual_sha256)


def _load_fixture_set(root: Path):
    try:
        return load_synthetic_trace_fixture_set(root / _FIXTURE_RELATIVE_PATH)
    except Exception as error:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.FIXTURE_PROVENANCE_MISMATCH,
            f"unable to load governed comparison fixture set: {error}",
        ) from error


def _validate_fixture_set(fixture_set, protocol: GovernedMatchedPolicyComparisonProtocol) -> None:
    if (
        fixture_set.manifest.fixture_set_id != protocol.fixture_set_id
        or fixture_set.manifest.fixture_set_version != protocol.fixture_set_version
    ):
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.FIXTURE_PROVENANCE_MISMATCH,
            "fixture set identity does not match the governed protocol",
        )
    case_ids = tuple(case.runtime_input.case_id for case in fixture_set.cases)
    if case_ids != protocol.expected_case_ids:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.FIXTURE_PROVENANCE_MISMATCH,
            "fixture set case order does not match the governed protocol",
        )


def _load_profile_set(root: Path):
    try:
        return load_synthetic_capacity_profile_fixture_set(root / _CAPACITY_RELATIVE_PATH)
    except Exception as error:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.CAPACITY_PROVENANCE_MISMATCH,
            f"unable to load governed synthetic capacity profiles: {error}",
        ) from error


def _load_calibration_artifact(root: Path) -> V5BoundedMonotoneBetaCalibrationArtifact:
    try:
        return V5BoundedMonotoneBetaCalibrationArtifact.model_validate_json(
            (root / _CALIBRATION_ARTIFACT_RELATIVE_PATH).read_text(encoding="utf-8")
        )
    except Exception as error:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.CALIBRATION_ARTIFACT_MISMATCH,
            f"unable to load the retained V5 calibration artifact: {error}",
        ) from error


def _validate_v5_eligibility_assessment(root: Path) -> None:
    try:
        assessment = V5FinalHeldOutAssessmentResult.model_validate_json(
            (root / _V5_ELIGIBILITY_RESULT_RELATIVE_PATH).read_text(encoding="utf-8")
        )
    except Exception as error:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.V5_ELIGIBILITY_MISMATCH,
            f"unable to load the retained V5 eligibility assessment: {error}",
        ) from error
    if (
        assessment.status
        is not V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
    ):
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.V5_ELIGIBILITY_MISMATCH,
            "governed comparison requires a passing retained V5 calibration assessment",
        )
    if (
        assessment.adaptive_policy_research_eligibility
        is not V5AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
    ):
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.V5_ELIGIBILITY_MISMATCH,
            "retained V5 assessment does not authorize controlled policy research",
        )
    if assessment.calibration_refit_performed or assessment.policy_or_replay_execution_performed:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.V5_ELIGIBILITY_MISMATCH,
            "retained V5 assessment must remain calibration-only evidence",
        )


def _profile_id_for_case(fixture_set, case_id: str) -> str:
    matching = tuple(case for case in fixture_set.cases if case.runtime_input.case_id == case_id)
    if len(matching) != 1:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.FIXTURE_PROVENANCE_MISMATCH,
            f"fixture set must contain exactly one case for {case_id}",
        )
    profile_ids = {
        context.capacity_snapshot.profile_id for context in matching[0].runtime_input.contexts
    }
    if len(profile_ids) != 1:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.CAPACITY_PROVENANCE_MISMATCH,
            f"case {case_id} must declare exactly one synthetic capacity profile",
        )
    return next(iter(profile_ids))


def _build_policies(
    *,
    protocol: GovernedMatchedPolicyComparisonProtocol,
    artifact: V5BoundedMonotoneBetaCalibrationArtifact,
    profile,
) -> tuple[
    FixedLengthVerificationPolicy,
    StaticThresholdVerificationPolicy,
    CalibratedCausalLoadAwarePolicy,
    UnsafeRetrospectiveLookaheadPolicy,
]:
    fixed = FixedLengthVerificationPolicy(
        FixedLengthPolicyConfig(
            policy_id=protocol.fixed_length_policy_id,
            maximum_verification_length=protocol.fixed_length,
        )
    )
    threshold = StaticThresholdVerificationPolicy(
        StaticThresholdPolicyConfig(
            policy_id=protocol.static_threshold_policy_id,
            minimum_conditional_survival_confidence=protocol.static_threshold,
        )
    )
    adaptive = CalibratedCausalLoadAwarePolicy(
        CalibratedCausalLoadAwarePolicyConfig(
            policy_id=protocol.adaptive_policy_id,
            accepted_admission_value_units=protocol.accepted_admission_value_units,
            marginal_verification_cost_weight=protocol.marginal_verification_cost_weight,
            minimum_expected_marginal_utility=0.0,
            calibration_authorization=V5RetainedCalibrationAuthorization(),
            capacity_profile_reference=SyntheticCapacityProfileReference.from_profile(profile),
        ),
        calibration_artifact=artifact,
        capacity_profile=profile,
    )
    unsafe = UnsafeRetrospectiveLookaheadPolicy()
    if unsafe.config.policy_id != protocol.unsafe_policy_id:
        raise GovernedMatchedPolicyComparisonError(
            GovernedMatchedPolicyComparisonErrorCode.COMPARISON_EXECUTION_FAILED,
            "unsafe policy default identity drifted from the predeclared protocol",
        )
    return fixed, threshold, adaptive, unsafe


def _outcome_counts(
    case_results: tuple[MatchedPolicyComparisonResult, ...],
    *,
    comparison_name: Literal["adaptive_vs_fixed_length", "adaptive_vs_static_threshold"],
) -> tuple[GovernedOutcomeCount, ...]:
    outcomes = tuple(MatchedPolicyComparisonOutcome)
    values = tuple(getattr(case, comparison_name).outcome for case in case_results)
    return tuple(
        GovernedOutcomeCount(outcome=outcome, case_count=values.count(outcome))
        for outcome in outcomes
    )


def _validate_outcome_counts(
    counts: tuple[GovernedOutcomeCount, ...],
    case_results: tuple[MatchedPolicyComparisonResult, ...],
    *,
    comparison_name: Literal["adaptive_vs_fixed_length", "adaptive_vs_static_threshold"],
) -> None:
    if tuple(item.outcome for item in counts) != tuple(MatchedPolicyComparisonOutcome):
        raise ValueError("outcome count records must retain every comparison outcome in enum order")
    if sum(item.case_count for item in counts) != len(case_results):
        raise ValueError("outcome counts must sum to the retained case count")
    expected = _outcome_counts(case_results, comparison_name=comparison_name)
    if counts != expected:
        raise ValueError("outcome counts must match retained case-level comparison outcomes")


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
        + b"\n"
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())
