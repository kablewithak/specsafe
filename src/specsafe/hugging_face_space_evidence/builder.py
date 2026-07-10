from __future__ import annotations

import hashlib
import json
import math
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from specsafe.hugging_face_dataset_publication.models import PublicationReceipt

from .models import (
    CalibrationGateEvidence,
    CalibrationMetric,
    CaseEvidence,
    DatasetPublicationEvidence,
    EvidenceSection,
    GeneratedArtifact,
    HuggingFaceSpaceEvidenceIndex,
    HuggingFaceSpaceEvidenceManifest,
    OutcomeCounts,
    PolicyDefinition,
    SourceArtifact,
)

OUTPUT_RELATIVE_DIRECTORY = "release/hugging-face-space/specsafe-reliability-lab"
INDEX_FILENAME = "evidence_index.json"
MANIFEST_FILENAME = "evidence_manifest.json"

COMPARISON_RELATIVE_PATH = (
    "evidence/matched-policy-comparison/v5-controlled-synthetic-comparison-v1/result.json"
)
RELEASE_SUMMARY_RELATIVE_PATH = (
    "release/hugging-face/specsafe-bounded-negative-evidence-v1/release_summary.json"
)
DATASET_RECEIPT_RELATIVE_PATH = (
    "evidence/publication-receipts/specsafe-bounded-negative-evidence-v1/"
    "hugging_face_dataset_publication_receipt.json"
)

EXPECTED_COMPARISON_SHA256 = "e82e21853526e687b068cd8a0b3abb4bb390da755be977bf5f3045148a7d17f4"
EXPECTED_RELEASE_SUMMARY_SHA256 = "264886c6bb6d2490bb95b43a29506b04437972e5a42c6688db7dc7d124f8df90"
EXPECTED_DATASET_RECEIPT_SHA256 = "a63cd76cefa376fc4baa108f4d0fa06b66ed2c4561cea29f3ac2280837e525b7"

EXPECTED_CASES = {
    "MPC5-101": ("development", "flat_capacity_control", 3.6, 3.6, 3.6),
    "MPC5-102": ("development", "light_load", 3.6, 3.6, 3.6),
    "MPC5-103": ("development", "moderate_load", 1.0, 1.0, 0.0),
    "MPC5-104": ("development", "saturated_load", -13.0, -13.0, 0.0),
    "MPC5-105": ("development", "jagged_capacity", -7.8, -7.8, 0.0),
    "MPC5-106": ("adversarial_regression", "flat_capacity_control", 1.6, 0.0, 1.6),
}


class HuggingFaceSpaceEvidenceErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "hf_space_evidence_invalid_project_root"
    SOURCE_MISSING = "hf_space_evidence_source_missing"
    SOURCE_HASH_MISMATCH = "hf_space_evidence_source_hash_mismatch"
    SOURCE_SCHEMA_INVALID = "hf_space_evidence_source_schema_invalid"
    SOURCE_STATE_INVALID = "hf_space_evidence_source_state_invalid"
    OUTPUT_OUTSIDE_REPOSITORY = "hf_space_evidence_output_outside_repository"
    OUTPUT_ALREADY_EXISTS = "hf_space_evidence_output_already_exists"
    COMMITTED_OUTPUT_MISMATCH = "hf_space_evidence_committed_output_mismatch"


class HuggingFaceSpaceEvidenceError(ValueError):
    def __init__(self, code: HuggingFaceSpaceEvidenceErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def build_space_evidence_index(
    project_root: Path | str,
) -> HuggingFaceSpaceEvidenceIndex:
    root = _require_project_root(Path(project_root))
    comparison = _load_hash_bound_json(
        root / COMPARISON_RELATIVE_PATH,
        EXPECTED_COMPARISON_SHA256,
    )
    release_summary = _load_hash_bound_json(
        root / RELEASE_SUMMARY_RELATIVE_PATH,
        EXPECTED_RELEASE_SUMMARY_SHA256,
    )
    receipt_payload = _load_hash_bound_bytes(
        root / DATASET_RECEIPT_RELATIVE_PATH,
        EXPECTED_DATASET_RECEIPT_SHA256,
    )
    try:
        receipt = PublicationReceipt.model_validate_json(receipt_payload)
    except ValidationError as error:
        raise HuggingFaceSpaceEvidenceError(
            HuggingFaceSpaceEvidenceErrorCode.SOURCE_SCHEMA_INVALID,
            f"Dataset publication receipt failed strict validation: {error}",
        ) from error

    cases = _build_cases(comparison)
    adaptive_vs_fixed = _build_outcome_counts(
        comparison,
        "adaptive_vs_fixed_length_outcome_counts",
    )
    adaptive_vs_threshold = _build_outcome_counts(
        comparison,
        "adaptive_vs_static_threshold_outcome_counts",
    )
    calibration_gate = _build_calibration_gate(release_summary)
    dataset_publication = _build_dataset_publication(receipt)
    source_artifacts = _source_artifacts()

    return HuggingFaceSpaceEvidenceIndex(
        schema_version="specsafe_hugging_face_space_evidence_index_v1",
        space_id="specsafe-reliability-lab-v1",
        space_repository_name="specsafe-reliability-lab",
        source_commit="ec70bba",
        title="SpecSafe — When Should AI Spend More Compute?",
        short_description="AI reliability case study on adaptive verification.",
        quick_summary=(
            "Adaptive verification helped under some conditions, was neutral under others, "
            "and lost in one. When the real confidence signal failed its safety gate, "
            "SpecSafe blocked activation."
        ),
        tested_question=(
            "Can an AI verification policy spend limited compute more intelligently than fixed "
            "rules without using forbidden future information?"
        ),
        final_interpretation=(
            "Adaptive scheduling can be useful, but it is not universally better. Its value "
            "depends on trustworthy confidence signals and hard activation gates."
        ),
        policies=_policy_definitions(),
        adaptive_vs_fixed=adaptive_vs_fixed,
        adaptive_vs_threshold=adaptive_vs_threshold,
        cases=cases,
        valid_causal_comparisons=6,
        unsafe_retrospective_controls_excluded=6,
        unsafe_controls_failed_causal_safety=True,
        calibration_gate=calibration_gate,
        dataset_publication=dataset_publication,
        maturity_labels=(
            "controlled synthetic policy evidence",
            "small-model confidence evidence",
            "not production serving evidence",
        ),
        supported_claims=(
            "The controlled synthetic corpus contains adaptive wins, neutral cases, and one loss.",
            "Unsafe retrospective controls failed causal safety and were excluded.",
            "Probability calibration improved on the independent holdout.",
            "Ranking safety regressed beyond tolerance, so activation was blocked.",
            "The public Dataset preserves the exact governed negative-evidence release.",
        ),
        non_claims=(
            "No global policy winner is established.",
            "No scheduler or confidence candidate is promoted for runtime control.",
            "No production throughput, latency, cost, or serving result is established.",
        ),
        sections=_sections(),
        source_artifacts=source_artifacts,
        read_only=True,
        live_inference=False,
        user_input_collection=False,
    )


def build_space_evidence_payloads(project_root: Path | str) -> dict[str, bytes]:
    index = build_space_evidence_index(project_root)
    index_bytes = _canonical_json_bytes(index.model_dump(mode="json"))
    manifest = HuggingFaceSpaceEvidenceManifest(
        schema_version="specsafe_hugging_face_space_evidence_manifest_v1",
        space_id=index.space_id,
        source_commit=index.source_commit,
        generated_artifact=GeneratedArtifact(
            relative_path=INDEX_FILENAME,
            sha256=_sha256_bytes(index_bytes),
            byte_count=len(index_bytes),
        ),
        source_artifacts=index.source_artifacts,
        exact_output_file_count=2,
        evidence_frozen=True,
        ui_implementation_started=False,
        next_authorized_step="build_visually_polished_read_only_space_shell",
    )
    return {
        INDEX_FILENAME: index_bytes,
        MANIFEST_FILENAME: _canonical_json_bytes(manifest.model_dump(mode="json")),
    }


def write_space_evidence_index(
    project_root: Path | str,
    *,
    output_directory: Path | str | None = None,
) -> Path:
    root = _require_project_root(Path(project_root))
    output = _resolve_output_directory(root, output_directory)
    if output.exists():
        raise HuggingFaceSpaceEvidenceError(
            HuggingFaceSpaceEvidenceErrorCode.OUTPUT_ALREADY_EXISTS,
            "Space evidence output already exists; use check mode for committed artifacts",
        )
    payloads = build_space_evidence_payloads(root)
    output.mkdir(parents=True)
    for filename, payload in payloads.items():
        (output / filename).write_bytes(payload)
    return output


def check_committed_space_evidence_index(project_root: Path | str) -> None:
    root = _require_project_root(Path(project_root))
    output = _resolve_output_directory(root, None)
    expected = build_space_evidence_payloads(root)
    if not output.is_dir():
        _raise_output_mismatch("committed Space evidence directory is missing")
    entries = tuple(output.iterdir())
    actual_files = {path.name for path in entries if path.is_file() and not path.is_symlink()}
    if actual_files != {INDEX_FILENAME, MANIFEST_FILENAME}:
        _raise_output_mismatch("committed Space evidence file allowlist does not match")
    if any(path.is_dir() or path.is_symlink() for path in entries):
        _raise_output_mismatch("committed Space evidence contains nested or linked content")
    for filename, payload in expected.items():
        if (output / filename).read_bytes() != payload:
            _raise_output_mismatch(f"committed Space evidence is not canonical: {filename}")


def _build_cases(comparison: dict[str, Any]) -> tuple[CaseEvidence, ...]:
    case_results = comparison.get("case_results")
    if not isinstance(case_results, list) or len(case_results) != 6:
        _raise_source_state("comparison must contain exactly six case results")
    by_id: dict[str, dict[str, Any]] = {}
    for item in case_results:
        if not isinstance(item, dict) or not isinstance(item.get("case_id"), str):
            _raise_source_state("comparison case result is malformed")
        by_id[item["case_id"]] = item
    if set(by_id) != set(EXPECTED_CASES):
        _raise_source_state("comparison case IDs do not match the governed corpus")

    explanations = {
        "MPC5-101": "All three policies performed the same under flat capacity.",
        "MPC5-102": "All three policies performed the same under light load.",
        "MPC5-103": "The adaptive policy was too conservative under moderate load.",
        "MPC5-104": "The adaptive policy avoided large losses under saturated load.",
        "MPC5-105": "The adaptive policy avoided losses under jagged capacity.",
        "MPC5-106": "The adaptive policy matched fixed length and beat the threshold baseline.",
    }
    output: list[CaseEvidence] = []
    for case_id, expected in EXPECTED_CASES.items():
        item = by_id[case_id]
        split, capacity_profile, fixed, threshold, adaptive = expected
        actual_utilities = (
            _nested_number(item, "fixed_length_score", "policy_utility_units"),
            _nested_number(item, "static_threshold_score", "policy_utility_units"),
            _nested_number(item, "adaptive_score", "policy_utility_units"),
        )
        expected_utilities = (fixed, threshold, adaptive)
        identity_matches = (
            item.get("split") == split and item.get("capacity_profile_kind") == capacity_profile
        )
        utilities_match = all(
            _utility_matches(actual, expected_value)
            for actual, expected_value in zip(
                actual_utilities,
                expected_utilities,
                strict=True,
            )
        )
        if not identity_matches or not utilities_match:
            _raise_source_state(f"comparison case drifted from retained result: {case_id}")
        output.append(
            CaseEvidence(
                case_id=case_id,
                split=split,
                capacity_profile=capacity_profile,
                fixed_utility=fixed,
                threshold_utility=threshold,
                adaptive_utility=adaptive,
                adaptive_vs_fixed=_nested_string(
                    item,
                    "adaptive_vs_fixed_length",
                    "outcome",
                ),
                adaptive_vs_threshold=_nested_string(
                    item,
                    "adaptive_vs_static_threshold",
                    "outcome",
                ),
                plain_language_result=explanations[case_id],
            )
        )
    return tuple(output)


def _build_outcome_counts(comparison: dict[str, Any], key: str) -> OutcomeCounts:
    values = comparison.get(key)
    if not isinstance(values, list):
        _raise_source_state(f"comparison outcome counts are missing: {key}")
    counts: dict[str, int] = {}
    for item in values:
        if not isinstance(item, dict):
            _raise_source_state(f"comparison outcome count is malformed: {key}")
        outcome = item.get("outcome")
        count = item.get("case_count")
        if not isinstance(outcome, str) or not isinstance(count, int):
            _raise_source_state(f"comparison outcome count is malformed: {key}")
        counts[outcome] = count
    return OutcomeCounts(
        adaptive_higher=counts.get("adaptive_higher_utility", -1),
        neutral=counts.get("utility_neutral", -1),
        adaptive_lower=counts.get("adaptive_lower_utility", -1),
    )


def _build_calibration_gate(release_summary: dict[str, Any]) -> CalibrationGateEvidence:
    metrics = release_summary.get("metrics")
    if not isinstance(metrics, dict):
        _raise_source_state("release summary metrics are missing")
    expected_state = (
        release_summary.get("holdout_record_count") == 192,
        release_summary.get("holdout_positive_count") == 136,
        release_summary.get("holdout_negative_count") == 56,
        release_summary.get("decision_outcome") == "KEEP_DIAGNOSTIC_ONLY",
        release_summary.get("promotion_attempt_status") == "closed_not_promoted",
        release_summary.get("automated_scheduling_confidence_status")
        == "unfit_use_conservative_fallback",
        release_summary.get("failure_labels") == ["ranking_safety_regression"],
    )
    if not all(expected_state):
        _raise_source_state("release summary lost the governed non-promotion state")

    raw_brier = _number(metrics, "raw_brier_score")
    calibrated_brier = _number(metrics, "calibrated_brier_score")
    brier_improvement = _number(metrics, "brier_improvement")
    raw_ece = _number(metrics, "raw_fixed_bin_ece")
    calibrated_ece = _number(metrics, "calibrated_fixed_bin_ece")
    ece_improvement = _number(metrics, "fixed_bin_ece_improvement")
    raw_auroc = _number(metrics, "raw_auroc")
    calibrated_auroc = _number(metrics, "calibrated_auroc")
    auroc_delta = _number(metrics, "auroc_delta")
    allowed = _number(metrics, "maximum_allowed_auroc_degradation")
    if allowed != 0.001:
        _raise_source_state("ranking-safety tolerance drifted")

    return CalibrationGateEvidence(
        holdout_record_count=192,
        holdout_positive_count=136,
        holdout_negative_count=56,
        metrics=(
            CalibrationMetric(
                metric_key="brier_score",
                display_name="Brier score",
                raw_value=raw_brier,
                calibrated_value=calibrated_brier,
                movement=brier_improvement,
                lower_is_better=True,
                gate_result="improved",
            ),
            CalibrationMetric(
                metric_key="fixed_bin_ece",
                display_name="Calibration error",
                raw_value=raw_ece,
                calibrated_value=calibrated_ece,
                movement=ece_improvement,
                lower_is_better=True,
                gate_result="improved",
            ),
            CalibrationMetric(
                metric_key="auroc",
                display_name="Ranking safety",
                raw_value=raw_auroc,
                calibrated_value=calibrated_auroc,
                movement=auroc_delta,
                lower_is_better=False,
                gate_result="failed_ranking_safety",
            ),
        ),
        maximum_allowed_auroc_degradation=0.001,
        observed_auroc_delta=auroc_delta,
        degradation_multiple_of_limit=abs(auroc_delta) / allowed,
        failure_label="ranking_safety_regression",
        decision_outcome="KEEP_DIAGNOSTIC_ONLY",
        promotion_attempt_status="closed_not_promoted",
        confidence_status="unfit_use_conservative_fallback",
        plain_language_result=(
            "Probability estimates improved, but ranking quality worsened far beyond the "
            "allowed limit. SpecSafe therefore blocked automated use."
        ),
    )


def _build_dataset_publication(
    receipt: PublicationReceipt,
) -> DatasetPublicationEvidence:
    expected = (
        receipt.repository_id == "KaboKableMolefe/specsafe-bounded-negative-evidence-v1",
        receipt.final_visibility == "public",
        receipt.gated is False,
        receipt.remote_file_count == 9,
        receipt.anonymous_public_verification_passed is True,
        receipt.rollback_triggered is False,
    )
    if not all(expected):
        _raise_source_state("Dataset receipt is not at the verified public boundary")
    return DatasetPublicationEvidence(
        repository_id=receipt.repository_id,
        repository_url=receipt.repository_url,
        published_revision=receipt.published_revision,
        publication_manifest_sha256=receipt.publication_manifest_sha256,
        public=True,
        gated=False,
        exact_file_count=9,
        anonymous_verification_passed=True,
    )


def _policy_definitions() -> tuple[PolicyDefinition, ...]:
    return (
        PolicyDefinition(
            policy_key="fixed_length",
            display_name="Fixed length",
            plain_language_description="Always verifies the same amount of work.",
            capacity_aware=False,
        ),
        PolicyDefinition(
            policy_key="static_threshold",
            display_name="Static threshold",
            plain_language_description="Uses one confidence cutoff in every condition.",
            capacity_aware=False,
        ),
        PolicyDefinition(
            policy_key="adaptive",
            display_name="Adaptive",
            plain_language_description=(
                "Changes verification effort using calibrated confidence and available capacity."
            ),
            capacity_aware=True,
        ),
    )


def _sections() -> tuple[EvidenceSection, ...]:
    return (
        EvidenceSection(
            section_id="overview",
            title="Quick summary",
            purpose="Explain the main result in under twenty seconds.",
        ),
        EvidenceSection(
            section_id="what_was_tested",
            title="What SpecSafe tested",
            purpose="Introduce the three policies in plain language.",
        ),
        EvidenceSection(
            section_id="policy_results",
            title="Wins, draws, and losses",
            purpose="Show the mixed aggregate comparison without implying a global winner.",
        ),
        EvidenceSection(
            section_id="capacity_conditions",
            title="Where adaptive scheduling helped",
            purpose="Compare policy utility across each governed capacity condition.",
        ),
        EvidenceSection(
            section_id="confidence_gate",
            title="Why activation was blocked",
            purpose="Show the favorable calibration movement and failed ranking-safety gate.",
        ),
        EvidenceSection(
            section_id="what_it_means",
            title="What this means",
            purpose="Translate the evidence into broader AI reliability behavior.",
        ),
        EvidenceSection(
            section_id="evidence",
            title="Explore the evidence",
            purpose="Expose exact values, artifact identities, and reproduction details.",
        ),
    )


def _source_artifacts() -> tuple[SourceArtifact, ...]:
    return (
        SourceArtifact(
            relative_path=COMPARISON_RELATIVE_PATH,
            sha256=EXPECTED_COMPARISON_SHA256,
        ),
        SourceArtifact(
            relative_path=RELEASE_SUMMARY_RELATIVE_PATH,
            sha256=EXPECTED_RELEASE_SUMMARY_SHA256,
        ),
        SourceArtifact(
            relative_path=DATASET_RECEIPT_RELATIVE_PATH,
            sha256=EXPECTED_DATASET_RECEIPT_SHA256,
        ),
    )


def _load_hash_bound_json(path: Path, expected_sha256: str) -> dict[str, Any]:
    payload = _load_hash_bound_bytes(path, expected_sha256)
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise HuggingFaceSpaceEvidenceError(
            HuggingFaceSpaceEvidenceErrorCode.SOURCE_SCHEMA_INVALID,
            f"Space evidence source is not valid JSON: {path}",
        ) from error
    if not isinstance(value, dict):
        _raise_source_state(f"Space evidence source must be an object: {path}")
    return value


def _load_hash_bound_bytes(path: Path, expected_sha256: str) -> bytes:
    if not path.is_file():
        raise HuggingFaceSpaceEvidenceError(
            HuggingFaceSpaceEvidenceErrorCode.SOURCE_MISSING,
            f"required Space evidence source is missing: {path}",
        )
    payload = path.read_bytes()
    if _sha256_bytes(payload) != expected_sha256:
        raise HuggingFaceSpaceEvidenceError(
            HuggingFaceSpaceEvidenceErrorCode.SOURCE_HASH_MISMATCH,
            f"Space evidence source SHA-256 mismatch: {path}",
        )
    return payload


def _nested_number(value: dict[str, Any], parent: str, child: str) -> float:
    nested = value.get(parent)
    if not isinstance(nested, dict):
        _raise_source_state(f"comparison field is missing: {parent}")
    return _number(nested, child)


def _nested_string(value: dict[str, Any], parent: str, child: str) -> str:
    nested = value.get(parent)
    if not isinstance(nested, dict) or not isinstance(nested.get(child), str):
        _raise_source_state(f"comparison field is missing: {parent}.{child}")
    return nested[child]


def _utility_matches(actual: float, expected: float) -> bool:
    return math.isclose(
        actual,
        expected,
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def _number(value: dict[str, Any], key: str) -> float:
    item = value.get(key)
    if not isinstance(item, (int, float)) or isinstance(item, bool):
        _raise_source_state(f"numeric Space evidence field is missing: {key}")
    return float(item)


def _require_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise HuggingFaceSpaceEvidenceError(
            HuggingFaceSpaceEvidenceErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return root


def _resolve_output_directory(root: Path, output_directory: Path | str | None) -> Path:
    if output_directory is None:
        output = root / OUTPUT_RELATIVE_DIRECTORY
    else:
        candidate = Path(output_directory).expanduser()
        output = candidate if candidate.is_absolute() else root / candidate
    resolved = output.resolve()
    if not resolved.is_relative_to(root):
        raise HuggingFaceSpaceEvidenceError(
            HuggingFaceSpaceEvidenceErrorCode.OUTPUT_OUTSIDE_REPOSITORY,
            "Space evidence output must remain inside the repository",
        )
    return resolved


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _raise_source_state(message: str) -> None:
    raise HuggingFaceSpaceEvidenceError(
        HuggingFaceSpaceEvidenceErrorCode.SOURCE_STATE_INVALID,
        message,
    )


def _raise_output_mismatch(message: str) -> None:
    raise HuggingFaceSpaceEvidenceError(
        HuggingFaceSpaceEvidenceErrorCode.COMMITTED_OUTPUT_MISMATCH,
        message,
    )
