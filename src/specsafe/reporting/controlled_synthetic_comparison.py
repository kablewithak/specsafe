"""Deterministic report and Phase 5 gate for retained controlled synthetic evidence.

This module reads the already-retained governed result. It never reruns a comparison,
refits calibration, changes policy configuration, or accesses final-evaluation labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts.models import CausalSafetyStatus, StrictContract, TraceSplit
from specsafe.eval_harness import (
    GovernedArtifactReference,
    GovernedMatchedPolicyComparisonResult,
)
from specsafe.eval_harness.comparison_models import MatchedPolicyComparisonOutcome

CONTROLLED_SYNTHETIC_COMPARISON_RESULT_RELATIVE_PATH = (
    "evidence/matched-policy-comparison/v5-controlled-synthetic-comparison-v1/result.json"
)
CONTROLLED_SYNTHETIC_PHASE5_GATE_RELATIVE_PATH = (
    "evidence/matched-policy-comparison/v5-controlled-synthetic-comparison-v1/phase5_gate.json"
)
CONTROLLED_SYNTHETIC_COMPARISON_REPORT_RELATIVE_PATH = (
    "docs/reports/v5-controlled-synthetic-policy-comparison.md"
)
_EXPECTED_RESULT_SHA256 = "e82e21853526e687b068cd8a0b3abb4bb390da755be977bf5f3045148a7d17f4"
_PHASE5_GATE_SCHEMA_VERSION = "v5-controlled-synthetic-phase5-gate-v1"


class ControlledSyntheticComparisonReportErrorCode(StrEnum):
    """Machine-readable failures for report derivation and Phase 5 gating."""

    INVALID_PROJECT_ROOT = "controlled_synthetic_report_invalid_project_root"
    RESULT_PROVENANCE_MISMATCH = "controlled_synthetic_report_result_provenance_mismatch"
    RESULT_SCHEMA_ERROR = "controlled_synthetic_report_result_schema_error"
    PHASE5_GATE_FAILED = "controlled_synthetic_report_phase5_gate_failed"
    COMMITTED_GATE_MISMATCH = "controlled_synthetic_report_committed_gate_mismatch"
    COMMITTED_REPORT_MISMATCH = "controlled_synthetic_report_committed_report_mismatch"


class ControlledSyntheticComparisonReportError(ValueError):
    """Raised when retained evidence cannot support a deterministic bounded report."""

    def __init__(
        self,
        code: ControlledSyntheticComparisonReportErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


class ControlledSyntheticOutcomeCount(StrictContract):
    """One outcome count retained in a controlled synthetic Phase 5 gate."""

    outcome: MatchedPolicyComparisonOutcome
    case_count: int = Field(ge=0)


class ControlledSyntheticPhase5Gate(StrictContract):
    """Bounded gate for ending local controlled synthetic Phase 5 work."""

    schema_version: Literal["v5-controlled-synthetic-phase5-gate-v1"] = _PHASE5_GATE_SCHEMA_VERSION
    result_artifact: GovernedArtifactReference
    result_schema_version: Literal["v5-controlled-synthetic-policy-comparison-result-v1"] = (
        "v5-controlled-synthetic-policy-comparison-result-v1"
    )
    validity_marker: Literal["VALID_COMPARISON"] = "VALID_COMPARISON"
    evidence_class: Literal["synthetic_controlled"] = "synthetic_controlled"
    evidence_maturity_label: Literal["synthetic_fixture_validated"] = "synthetic_fixture_validated"
    phase5_gate_status: Literal["passes_controlled_synthetic_phase5_gate"] = (
        "passes_controlled_synthetic_phase5_gate"
    )
    case_count: Literal[6] = 6
    valid_matched_comparison_count: Literal[6] = 6
    unsafe_control_exclusion_count: Literal[6] = 6
    adaptive_vs_fixed_length_outcome_counts: tuple[ControlledSyntheticOutcomeCount, ...]
    adaptive_vs_static_threshold_outcome_counts: tuple[ControlledSyntheticOutcomeCount, ...]
    calibration_refit_performed: Literal[False] = False
    final_evaluation_accessed: Literal[False] = False
    runtime_control_eligible: Literal[False] = False
    promotion_eligible: Literal[False] = False
    kaggle_experiment_authorized: Literal[True] = True
    public_replay_release_authorized: Literal[False] = False
    result_reexecution_performed: Literal[False] = False
    claim_status: Literal["bounded_controlled_synthetic_evidence_only"] = (
        "bounded_controlled_synthetic_evidence_only"
    )

    @model_validator(mode="after")
    def validate_mixed_outcome_evidence(self) -> ControlledSyntheticPhase5Gate:
        """Require both negative and non-negative evidence before Phase 6 starts."""

        for counts in (
            self.adaptive_vs_fixed_length_outcome_counts,
            self.adaptive_vs_static_threshold_outcome_counts,
        ):
            values = {item.outcome: item.case_count for item in counts}
            if set(values) != set(MatchedPolicyComparisonOutcome):
                raise ValueError("outcome counts must retain every comparison outcome")
            if sum(values.values()) != self.case_count:
                raise ValueError("outcome counts must sum to the governed case count")
            if values[MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY] < 1:
                raise ValueError("Phase 5 requires at least one retained adaptive-loss case")
            if values[MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL] < 1:
                raise ValueError("Phase 5 requires at least one retained neutral case")
            if values[MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY] < 1:
                raise ValueError("Phase 5 requires at least one retained higher-utility case")
        return self


def build_controlled_synthetic_phase5_gate(project_root: Path) -> ControlledSyntheticPhase5Gate:
    """Validate retained evidence and derive the bounded Phase 5 gate without rerunning it."""

    root = _require_project_root(project_root)
    result_path = root / CONTROLLED_SYNTHETIC_COMPARISON_RESULT_RELATIVE_PATH
    result_bytes = _require_result_bytes(result_path)

    try:
        result = GovernedMatchedPolicyComparisonResult.model_validate_json(result_bytes)
    except ValueError as error:
        raise ControlledSyntheticComparisonReportError(
            ControlledSyntheticComparisonReportErrorCode.RESULT_SCHEMA_ERROR,
            f"retained governed comparison result is invalid: {error}",
        ) from error

    _validate_phase5_inputs(result)
    return ControlledSyntheticPhase5Gate(
        result_artifact=GovernedArtifactReference(
            relative_path=CONTROLLED_SYNTHETIC_COMPARISON_RESULT_RELATIVE_PATH,
            sha256=_sha256_bytes(result_bytes),
        ),
        adaptive_vs_fixed_length_outcome_counts=_convert_outcome_counts(
            result.adaptive_vs_fixed_length_outcome_counts
        ),
        adaptive_vs_static_threshold_outcome_counts=_convert_outcome_counts(
            result.adaptive_vs_static_threshold_outcome_counts
        ),
    )


def canonical_controlled_synthetic_phase5_gate_json(
    gate: ControlledSyntheticPhase5Gate,
) -> str:
    """Serialize a gate deterministically for committed evidence validation."""

    return (
        json.dumps(
            gate.model_dump(mode="json"),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def default_controlled_synthetic_phase5_gate_path(project_root: Path) -> Path:
    """Return the required repository-local path for the committed Phase 5 gate."""

    return _require_project_root(project_root) / CONTROLLED_SYNTHETIC_PHASE5_GATE_RELATIVE_PATH


def default_controlled_synthetic_comparison_report_path(project_root: Path) -> Path:
    """Return the required repository-local path for the committed Markdown report."""

    return (
        _require_project_root(project_root) / CONTROLLED_SYNTHETIC_COMPARISON_REPORT_RELATIVE_PATH
    )


def render_controlled_synthetic_comparison_report(project_root: Path) -> str:
    """Render a deterministic Markdown report from one already-retained result."""

    root = _require_project_root(project_root)
    gate = build_controlled_synthetic_phase5_gate(root)
    result = _load_result(root)

    fixed_counts = _count_map(result.adaptive_vs_fixed_length_outcome_counts)
    threshold_counts = _count_map(result.adaptive_vs_static_threshold_outcome_counts)

    lines = [
        "# V5 Controlled Synthetic Policy Comparison",
        "",
        "## Validity marker",
        "",
        "```text",
        "VALID_COMPARISON",
        "```",
        "",
        "## Objective",
        "",
        "Evaluate fixed-length, static-threshold, and calibrated causal load-aware "
        "verification policies on one immutable synthetic corpus using identical trace "
        "inputs, declared synthetic capacity profiles, and one shared utility scorer.",
        "",
        "## Evidence class and maturity",
        "",
        "```text",
        "evidence_class=synthetic_controlled",
        "evidence_maturity_label=synthetic_fixture_validated",
        "phase5_gate_status=passes_controlled_synthetic_phase5_gate",
        "```",
        "",
        "This is controlled synthetic replay evidence. It is not final held-out policy "
        "evaluation, Kaggle measurement, live-serving evidence, or production evidence.",
        "",
        "## Governed inputs",
        "",
        "| Input | Relative path | SHA-256 |",
        "|---|---|---|",
        _artifact_row("Matched comparison result", gate.result_artifact),
        _artifact_row("Matched comparison fixture manifest", result.fixture_manifest),
        _artifact_row("Synthetic capacity-profile manifest", result.capacity_profile_manifest),
        _artifact_row("Retained V5 calibration artifact", result.calibration_artifact),
        _artifact_row(
            "Retained V5 calibration eligibility assessment",
            result.v5_calibration_eligibility_assessment,
        ),
        "",
        "## Predeclared policy and scoring configuration",
        "",
        "```text",
        f"comparison_id={result.protocol.comparison_id}",
        f"fixed_length_policy_id={result.protocol.fixed_length_policy_id}",
        f"static_threshold_policy_id={result.protocol.static_threshold_policy_id}",
        f"adaptive_policy_id={result.protocol.adaptive_policy_id}",
        f"unsafe_policy_id={result.protocol.unsafe_policy_id}",
        f"fixed_length={result.protocol.fixed_length}",
        f"static_threshold={_format_number(result.protocol.static_threshold)}",
        "policy_utility=accepted_admission_count × 1.0 "
        "− Σ(admitted marginal verification cost × 1.0)",
        f"protocol_configuration_sha256={result.protocol_configuration_sha256}",
        "```",
        "",
        "## Aggregate case-level outcomes",
        "",
        "| Comparator | Adaptive higher utility | Neutral | Adaptive lower utility |",
        "|---|---:|---:|---:|",
        _outcome_row("Fixed-length", fixed_counts),
        _outcome_row("Static threshold", threshold_counts),
        "",
        "The retained corpus includes higher, neutral, and lower adaptive-policy outcomes. "
        "This mixed result is required evidence, not a defect to hide.",
        "",
        "## Case-level results",
        "",
        "| Case | Split | Capacity profile | Fixed utility | Threshold utility | "
        "Adaptive utility | Adaptive vs fixed | Adaptive vs threshold |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]

    for case in result.case_results:
        lines.append(
            "| "
            f"{case.case_id} | {case.split.value} | {case.capacity_profile_kind.value} | "
            f"{_format_number(case.fixed_length_score.policy_utility_units)} | "
            f"{_format_number(case.static_threshold_score.policy_utility_units)} | "
            f"{_format_number(case.adaptive_score.policy_utility_units)} | "
            f"{case.adaptive_vs_fixed_length.outcome.value} | "
            f"{case.adaptive_vs_static_threshold.outcome.value} |"
        )

    lines.extend(
        [
            "",
            "## Causal safety and unsafe control",
            "",
            f"- Valid matched comparisons retained: `{result.valid_matched_comparison_count}`.",
            f"- Unsafe retrospective controls excluded: `{result.unsafe_control_exclusion_count}`.",
            "- Every unsafe control is `causal_safety_status=fail` and remains excluded "
            "from valid scores and adaptive-versus-baseline deltas.",
            "",
            "## Phase 5 gate decision",
            "",
            "```text",
            f"phase5_gate_status={gate.phase5_gate_status}",
            f"kaggle_experiment_authorized={str(gate.kaggle_experiment_authorized).lower()}",
            f"public_replay_release_authorized={str(gate.public_replay_release_authorized).lower()}",
            f"runtime_control_eligible={str(gate.runtime_control_eligible).lower()}",
            f"promotion_eligible={str(gate.promotion_eligible).lower()}",
            "```",
            "",
            "The local controlled-synthetic proof is complete enough to begin the separately "
            "labelled Kaggle evidence-acquisition phase. This authorization does not elevate "
            "the maturity label or permit public replay, runtime control, or production claims.",
            "",
            "## Supported claims",
            "",
            "- Under this six-case controlled synthetic corpus, the calibrated causal policy "
            "had mixed case-level utility relative to both valid baselines.",
            "- The retained corpus preserves adaptive-policy higher, neutral, and "
            "lower utility cases.",
            "- Unsafe retrospective control results failed causal safety and were excluded.",
            "- The local core evidence is sufficient to start a separately labelled "
            "Kaggle experiment.",
            "",
            "## Non-claims",
            "",
            "- No global policy winner is established.",
            "- No final held-out policy comparison has been performed.",
            "- No production throughput, latency, cost-saving, or serving-capacity "
            "result is established.",
            "- No runtime-control, promotion, public replay release, or "
            "production-readiness claim is established.",
            "",
            "## Reproduction",
            "",
            "```powershell",
            "python -m specsafe.reporting.controlled_synthetic_comparison --project-root . --check",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def check_committed_controlled_synthetic_comparison_report(project_root: Path) -> None:
    """Raise when committed gate/report artifacts differ from deterministic derivation."""

    root = _require_project_root(project_root)
    gate = build_controlled_synthetic_phase5_gate(root)
    gate_path = default_controlled_synthetic_phase5_gate_path(root)
    report_path = default_controlled_synthetic_comparison_report_path(root)
    expected_gate = canonical_controlled_synthetic_phase5_gate_json(gate)
    expected_report = render_controlled_synthetic_comparison_report(root)

    if gate_path.read_text(encoding="utf-8") != expected_gate:
        raise ControlledSyntheticComparisonReportError(
            ControlledSyntheticComparisonReportErrorCode.COMMITTED_GATE_MISMATCH,
            "committed Phase 5 gate does not match deterministic retained evidence",
        )
    if report_path.read_text(encoding="utf-8") != expected_report:
        raise ControlledSyntheticComparisonReportError(
            ControlledSyntheticComparisonReportErrorCode.COMMITTED_REPORT_MISMATCH,
            "committed controlled synthetic report does not match deterministic retained evidence",
        )


def _load_result(project_root: Path) -> GovernedMatchedPolicyComparisonResult:
    result_bytes = _require_result_bytes(
        project_root / CONTROLLED_SYNTHETIC_COMPARISON_RESULT_RELATIVE_PATH
    )
    try:
        return GovernedMatchedPolicyComparisonResult.model_validate_json(result_bytes)
    except ValueError as error:
        raise ControlledSyntheticComparisonReportError(
            ControlledSyntheticComparisonReportErrorCode.RESULT_SCHEMA_ERROR,
            f"retained governed comparison result is invalid: {error}",
        ) from error


def _require_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise ControlledSyntheticComparisonReportError(
            ControlledSyntheticComparisonReportErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return root


def _require_result_bytes(result_path: Path) -> bytes:
    if not result_path.is_file():
        raise ControlledSyntheticComparisonReportError(
            ControlledSyntheticComparisonReportErrorCode.RESULT_PROVENANCE_MISMATCH,
            "retained governed comparison result is missing",
        )
    result_bytes = result_path.read_bytes()
    if _sha256_bytes(result_bytes) != _EXPECTED_RESULT_SHA256:
        raise ControlledSyntheticComparisonReportError(
            ControlledSyntheticComparisonReportErrorCode.RESULT_PROVENANCE_MISMATCH,
            "retained governed comparison result SHA-256 does not match the governed artifact",
        )
    return result_bytes


def _validate_phase5_inputs(result: GovernedMatchedPolicyComparisonResult) -> None:
    if result.execution_status != "retained_controlled_synthetic_case_level_results":
        _raise_gate_failure("retained result has an unexpected execution status")
    if result.claim_status != "no_global_winner_or_runtime_promotion_claim":
        _raise_gate_failure("retained result has an unexpected claim status")
    if result.calibration_refit_performed or result.final_evaluation_accessed:
        _raise_gate_failure("retained result must not refit calibration or access final evaluation")
    if result.runtime_control_eligible or result.promotion_eligible:
        _raise_gate_failure("retained result must not authorize runtime control or promotion")
    if result.case_count != 6 or result.valid_matched_comparison_count != 6:
        _raise_gate_failure("retained result must include all six valid matched cases")
    if result.unsafe_control_exclusion_count != 6:
        _raise_gate_failure("retained result must exclude every unsafe control")

    allowed_splits = {TraceSplit.DEVELOPMENT, TraceSplit.ADVERSARIAL_REGRESSION}
    for case in result.case_results:
        if case.split not in allowed_splits:
            _raise_gate_failure("retained result may use only development or adversarial cases")
        if case.validity_status != "valid_matched_synthetic_comparison":
            _raise_gate_failure("retained case is not a valid matched synthetic comparison")
        unsafe = case.unsafe_retrospective_control
        if unsafe.replay_result.causal_safety_status is not CausalSafetyStatus.FAIL:
            _raise_gate_failure("unsafe retrospective control must remain causal-fail")
        if unsafe.exclusion_reason != "causal_safety_failure_excluded_from_valid_comparison":
            _raise_gate_failure("unsafe retrospective control must remain excluded")

    for counts in (
        result.adaptive_vs_fixed_length_outcome_counts,
        result.adaptive_vs_static_threshold_outcome_counts,
    ):
        values = _count_map(counts)
        if values[MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY] < 1:
            _raise_gate_failure("retained result must include a higher-utility case")
        if values[MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL] < 1:
            _raise_gate_failure("retained result must include a neutral case")
        if values[MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY] < 1:
            _raise_gate_failure("retained result must include a lower-utility case")


def _convert_outcome_counts(counts) -> tuple[ControlledSyntheticOutcomeCount, ...]:
    return tuple(
        ControlledSyntheticOutcomeCount(outcome=item.outcome, case_count=item.case_count)
        for item in counts
    )


def _count_map(counts) -> dict[MatchedPolicyComparisonOutcome, int]:
    return {item.outcome: item.case_count for item in counts}


def _artifact_row(label: str, artifact: GovernedArtifactReference) -> str:
    return f"| {label} | `{artifact.relative_path}` | `{artifact.sha256}` |"


def _outcome_row(
    label: str,
    counts: dict[MatchedPolicyComparisonOutcome, int],
) -> str:
    return (
        f"| {label} | "
        f"{counts[MatchedPolicyComparisonOutcome.ADAPTIVE_HIGHER_UTILITY]} | "
        f"{counts[MatchedPolicyComparisonOutcome.UTILITY_NEUTRAL]} | "
        f"{counts[MatchedPolicyComparisonOutcome.ADAPTIVE_LOWER_UTILITY]} |"
    )


def _format_number(value: float) -> str:
    return f"{value:.12g}"


def _raise_gate_failure(message: str) -> None:
    raise ControlledSyntheticComparisonReportError(
        ControlledSyntheticComparisonReportErrorCode.PHASE5_GATE_FAILED,
        message,
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    """Check that committed gate/report artifacts match retained controlled evidence."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not args.check:
        parser.error("only --check is supported; report generation is governed in source control")

    check_committed_controlled_synthetic_comparison_report(Path(args.project_root))
    print("Controlled synthetic Phase 5 gate and report are canonical.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
