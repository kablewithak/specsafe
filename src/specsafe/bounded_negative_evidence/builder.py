from __future__ import annotations

import hashlib
import json
import re
from enum import StrEnum
from math import isclose
from pathlib import Path

from pydantic import ValidationError

from specsafe.bounded_negative_evidence.models import (
    BoundedNegativeEvidenceReleaseManifest,
    BoundedNegativeEvidenceReleaseSummary,
    ReleaseArtifactReference,
    ReleaseGateChecks,
    ReleaseManifestEntry,
    ReleaseMetricSummary,
)
from specsafe.candidate_calibrator_closeout.models import (
    CandidateCalibratorPromotionCloseoutDecision,
)
from specsafe.independent_holdout_replay.models import IndependentHoldoutReplayReport

RELEASE_ID = "specsafe-bounded-negative-evidence-v1"
RELEASE_RELATIVE_DIRECTORY = (
    "release/bounded-negative-evidence/specsafe-bounded-negative-evidence-v1"
)
REPLAY_REPORT_RELATIVE_PATH = (
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/"
    "candidate_calibrator_holdout_replay_report.json"
)
CLOSEOUT_DECISION_RELATIVE_PATH = (
    "evidence/kaggle-trace-collection/"
    "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4/"
    "candidate_calibrator_promotion_closeout_decision.json"
)
EXPECTED_REPLAY_REPORT_SHA256 = (
    "402df4475b05eead800a5ba7f6b4ae96587fd5bfbe83f20966ac180888e1467f"
)
EXPECTED_CLOSEOUT_DECISION_SHA256 = (
    "e91047e78f8992e252d3f313943ff8e86aafd2c1c77b3683058d2406a29266bc"
)
EXPECTED_RELEASE_FILENAMES = {
    "README.md",
    "evidence_boundary.md",
    "release_summary.json",
    "release_manifest.json",
}
_PRE_MANIFEST_FILENAMES = {
    "README.md",
    "evidence_boundary.md",
    "release_summary.json",
}
_FORBIDDEN_CONTENT_MARKERS = (
    b'"prompt_text"',
    b'"raw_prompt_text"',
    b".jsonl",
    b".zip",
    b"api_key",
    b"access_token",
    b"hf_token",
    b"raw_logits",
    b"environment_variables",
    b"authorization: bearer",
    b"/home/",
    b"/Users/",
)
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(rb"[A-Za-z]:\\")


class BoundedNegativeEvidenceReleaseErrorCode(StrEnum):
    INVALID_PROJECT_ROOT = "bounded_release_invalid_project_root"
    SOURCE_MISSING = "bounded_release_source_missing"
    SOURCE_HASH_MISMATCH = "bounded_release_source_hash_mismatch"
    SOURCE_SCHEMA_INVALID = "bounded_release_source_schema_invalid"
    SOURCE_STATE_INVALID = "bounded_release_source_state_invalid"
    OUTPUT_OUTSIDE_REPOSITORY = "bounded_release_output_outside_repository"
    OUTPUT_ALREADY_EXISTS = "bounded_release_output_already_exists"
    COMMITTED_PACK_MISMATCH = "bounded_release_committed_pack_mismatch"
    SANITIZATION_FAILED = "bounded_release_sanitization_failed"


class BoundedNegativeEvidenceReleaseError(ValueError):
    def __init__(
        self,
        code: BoundedNegativeEvidenceReleaseErrorCode,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code


def build_release_summary(
    project_root: Path | str,
) -> BoundedNegativeEvidenceReleaseSummary:
    root = _require_project_root(Path(project_root))
    replay, closeout = _load_verified_sources(root)
    _validate_source_alignment(replay, closeout)

    return BoundedNegativeEvidenceReleaseSummary(
        schema_version="specsafe_bounded_negative_evidence_release_summary_v1",
        release_id=RELEASE_ID,
        release_type="bounded_negative_evidence",
        validity_marker="CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
        publication_status="local_pack_only",
        source_commit="8e3c176",
        source_replay_report=ReleaseArtifactReference(
            relative_path=REPLAY_REPORT_RELATIVE_PATH,
            sha256=EXPECTED_REPLAY_REPORT_SHA256,
        ),
        source_closeout_decision=ReleaseArtifactReference(
            relative_path=CLOSEOUT_DECISION_RELATIVE_PATH,
            sha256=EXPECTED_CLOSEOUT_DECISION_SHA256,
        ),
        candidate_artifact_id=closeout.calibrator_artifact_id,
        candidate_artifact_hash=closeout.calibrator_artifact_hash,
        holdout_trace_archive_id=closeout.holdout_trace_archive_id,
        holdout_trace_archive_hash=closeout.holdout_trace_archive_hash,
        holdout_record_count=closeout.holdout_record_count,
        holdout_positive_count=closeout.holdout_positive_count,
        holdout_negative_count=closeout.holdout_negative_count,
        metrics=ReleaseMetricSummary(
            raw_brier_score=closeout.metrics.raw_brier_score,
            calibrated_brier_score=closeout.metrics.calibrated_brier_score,
            brier_improvement=closeout.metrics.brier_improvement,
            raw_fixed_bin_ece=closeout.metrics.raw_fixed_bin_ece,
            calibrated_fixed_bin_ece=closeout.metrics.calibrated_fixed_bin_ece,
            fixed_bin_ece_improvement=closeout.metrics.fixed_bin_ece_improvement,
            raw_auroc=closeout.metrics.raw_auroc,
            calibrated_auroc=closeout.metrics.calibrated_auroc,
            auroc_delta=closeout.metrics.auroc_delta,
            maximum_allowed_auroc_degradation=(
                closeout.metrics.maximum_allowed_auroc_degradation
            ),
        ),
        failure_labels=tuple(str(label) for label in closeout.failure_labels),
        decision_outcome=str(closeout.decision_outcome),
        candidate_disposition=str(closeout.candidate_disposition),
        promotion_attempt_status=str(closeout.promotion_attempt_status),
        calibrator_promotion_status=closeout.calibrator_promotion_status,
        automated_scheduling_confidence_status=(
            closeout.automated_scheduling_confidence_status
        ),
        candidate_not_promoted=True,
        threshold_promotion_authorized=False,
        scheduler_promotion_authorized=False,
        production_claim_authorized=False,
        holdout_reuse_policy=closeout.holdout_reuse_policy,
        claims_permitted=closeout.claims_permitted,
        claims_forbidden=closeout.claims_forbidden,
        privacy_controls=(
            "aggregate_metrics_only",
            "no_prompt_content",
            "no_private_or_customer_data",
            "no_secrets_or_credentials",
            "no_raw_logs_or_environment_dumps",
            "no_user_input_collection",
            "no_live_inference",
        ),
        publication_controls=(
            "local_pack_only",
            "license_selection_pending",
            "final_hash_review_required",
            "dataset_card_review_required",
            "explicit_publication_authorization_required",
            "rollback_or_unpublish_procedure_required",
        ),
        gate_checks=ReleaseGateChecks(),
        next_authorized_step="publication_readiness_review_and_license_decision",
    )


def canonical_release_summary_json(
    summary: BoundedNegativeEvidenceReleaseSummary,
) -> bytes:
    return _canonical_json_bytes(summary.model_dump(mode="json"))


def render_dataset_card(summary: BoundedNegativeEvidenceReleaseSummary) -> bytes:
    metrics = summary.metrics
    lines = [
        "# SpecSafe Bounded Negative-Evidence Release",
        "",
        "## Validity marker",
        "",
        "```text",
        summary.validity_marker,
        "```",
        "",
        "## Release status",
        "",
        "```text",
        f"release_id={summary.release_id}",
        f"release_type={summary.release_type}",
        f"publication_status={summary.publication_status}",
        f"candidate_not_promoted={str(summary.candidate_not_promoted).lower()}",
        "threshold_promotion_authorized=false",
        "scheduler_promotion_authorized=false",
        "production_claim_authorized=false",
        "```",
        "",
        "This local pack presents a governed negative result. It does not present the retained "
        "candidate as a successful calibrator or as trusted input for automated scheduling.",
        "",
        "## What was evaluated",
        "",
        f"- Candidate artifact: `{summary.candidate_artifact_id}`.",
        f"- Independent holdout records: `{summary.holdout_record_count}`.",
        f"- Positive outcomes: `{summary.holdout_positive_count}`.",
        f"- Negative outcomes: `{summary.holdout_negative_count}`.",
        "- Replay mode: frozen candidate applied without refit.",
        "",
        "## Aggregate holdout metrics",
        "",
        "| Metric | Raw | Calibrated | Movement |",
        "|---|---:|---:|---:|",
        _metric_row(
            "Brier score",
            metrics.raw_brier_score,
            metrics.calibrated_brier_score,
            metrics.brier_improvement,
        ),
        _metric_row(
            "Fixed-bin ECE",
            metrics.raw_fixed_bin_ece,
            metrics.calibrated_fixed_bin_ece,
            metrics.fixed_bin_ece_improvement,
        ),
        _metric_row(
            "AUROC",
            metrics.raw_auroc,
            metrics.calibrated_auroc,
            metrics.auroc_delta,
        ),
        "",
        "Brier score and fixed-bin ECE improved. AUROC decreased by more than the declared "
        "ranking-safety tolerance, so the higher-priority gate blocked promotion.",
        "",
        "## Decision",
        "",
        "```text",
        f"decision_outcome={summary.decision_outcome}",
        f"promotion_attempt_status={summary.promotion_attempt_status}",
        f"candidate_disposition={summary.candidate_disposition}",
        f"failure_label={summary.failure_labels[0]}",
        "conservative_fallback_required=true",
        "```",
        "",
        "## Supported claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in summary.claims_permitted)
    lines.extend(["", "## Forbidden claims", ""])
    lines.extend(f"- {claim}" for claim in summary.claims_forbidden)
    lines.extend(
        [
            "",
            "## Data and privacy",
            "",
            "This pack contains aggregate metrics and governed decision metadata only. It "
            "contains no raw prompts, private or customer records, secrets, raw model outputs, "
            "environment dumps, user-input collection, or live inference.",
            "",
            "## Reproduction",
            "",
            "From the SpecSafe repository root:",
            "",
            "```powershell",
            "python .\\scripts\\build_bounded_negative_evidence_release.py --check",
            "```",
            "",
            "The command verifies source hashes, strict source schemas, cross-report identity, "
            "canonical release bytes, the manifest, sanitization, and claim boundaries.",
            "",
            "## Publication boundary",
            "",
            "This directory is a local release candidate only. Public publication requires a "
            "separate license, hash, sanitization, dataset-card, visibility, and rollback review.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def render_evidence_boundary(summary: BoundedNegativeEvidenceReleaseSummary) -> bytes:
    lines = [
        "# Evidence Boundary",
        "",
        "## Interpretation",
        "",
        "```text",
        f"validity_marker={summary.validity_marker}",
        "probability_quality_improved=true",
        "ranking_safety_passed=false",
        "promotion_blocked=true",
        "conservative_fallback_required=true",
        "```",
        "",
        "The retained candidate improved aggregate probability-quality metrics but failed the "
        "predeclared ranking-safety gate. The correct outcome is rejection for automated "
        "probability-driven control, not selective reporting of the favorable metrics.",
        "",
        "## Included",
        "",
        "- Aggregate holdout counts and probability metrics.",
        "- Candidate, holdout, replay-report, and closeout-decision identities and hashes.",
        "- The retained failure label and non-promotion decision.",
        "- Consumed-holdout rules, supported claims, and forbidden claims.",
        "",
        "## Excluded",
        "",
        "- Raw prompt or trace content.",
        "- Raw model outputs, notebook outputs, credentials, or environment dumps.",
        "- Private, client, or customer records.",
        "- Threshold selection, scheduler configuration, or live model inference.",
        "- Production speed, latency, throughput, cost, or serving-readiness evidence.",
        "",
        "## Holdout consumption",
        "",
    ]
    lines.extend(f"- `{rule}`" for rule in summary.holdout_reuse_policy)
    lines.extend(
        [
            "",
            "The consumed holdout cannot be used to select a replacement method, refit the "
            "current candidate, tune thresholds, tune a scheduler, or augment a future fit pool.",
            "",
            "## Publication status",
            "",
            "```text",
            "publication_status=local_pack_only",
            "license_selection_pending=true",
            "explicit_publication_authorization_required=true",
            "```",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def build_release_payloads(project_root: Path | str) -> dict[str, bytes]:
    summary = build_release_summary(project_root)
    payloads = {
        "README.md": render_dataset_card(summary),
        "evidence_boundary.md": render_evidence_boundary(summary),
        "release_summary.json": canonical_release_summary_json(summary),
    }
    _validate_sanitized_payloads(payloads)
    manifest = _build_manifest(payloads)
    payloads["release_manifest.json"] = _canonical_json_bytes(
        manifest.model_dump(mode="json")
    )
    return payloads


def write_release_pack(
    project_root: Path | str,
    *,
    output_directory: Path | str | None = None,
) -> Path:
    root = _require_project_root(Path(project_root))
    output = _resolve_output_directory(root, output_directory)
    if output.exists():
        raise BoundedNegativeEvidenceReleaseError(
            BoundedNegativeEvidenceReleaseErrorCode.OUTPUT_ALREADY_EXISTS,
            "release output already exists; use check mode for committed artifacts",
        )

    payloads = build_release_payloads(root)
    output.mkdir(parents=True)
    for filename in sorted(_PRE_MANIFEST_FILENAMES):
        (output / filename).write_bytes(payloads[filename])
    (output / "release_manifest.json").write_bytes(payloads["release_manifest.json"])
    return output


def check_committed_release_pack(project_root: Path | str) -> None:
    root = _require_project_root(Path(project_root))
    output = _resolve_output_directory(root, None)
    expected = build_release_payloads(root)
    if not output.is_dir():
        _raise_committed_mismatch("committed release directory is missing")

    actual_files = {
        path.name
        for path in output.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    if actual_files != EXPECTED_RELEASE_FILENAMES:
        _raise_committed_mismatch("committed release file allowlist does not match")
    if any(path.is_dir() or path.is_symlink() for path in output.iterdir()):
        _raise_committed_mismatch(
            "committed release directory contains nested or linked content"
        )

    for filename, expected_bytes in expected.items():
        path = output / filename
        if path.read_bytes() != expected_bytes:
            _raise_committed_mismatch(
                f"committed release file is not canonical: {filename}"
            )


def _load_verified_sources(
    root: Path,
) -> tuple[
    IndependentHoldoutReplayReport, CandidateCalibratorPromotionCloseoutDecision
]:
    replay_bytes = _require_source_bytes(
        root / REPLAY_REPORT_RELATIVE_PATH,
        EXPECTED_REPLAY_REPORT_SHA256,
    )
    closeout_bytes = _require_source_bytes(
        root / CLOSEOUT_DECISION_RELATIVE_PATH,
        EXPECTED_CLOSEOUT_DECISION_SHA256,
    )
    try:
        replay = IndependentHoldoutReplayReport.model_validate_json(replay_bytes)
        closeout = CandidateCalibratorPromotionCloseoutDecision.model_validate_json(
            closeout_bytes
        )
    except ValidationError as error:
        raise BoundedNegativeEvidenceReleaseError(
            BoundedNegativeEvidenceReleaseErrorCode.SOURCE_SCHEMA_INVALID,
            f"retained source artifact failed strict schema validation: {error}",
        ) from error
    return replay, closeout


def _validate_source_alignment(
    replay: IndependentHoldoutReplayReport,
    closeout: CandidateCalibratorPromotionCloseoutDecision,
) -> None:
    conditions = (
        closeout.source_replay_report == REPLAY_REPORT_RELATIVE_PATH,
        closeout.source_replay_report_sha256 == EXPECTED_REPLAY_REPORT_SHA256,
        closeout.source_replay_report_id == replay.report_id,
        closeout.source_replay_run_id == replay.run_id,
        closeout.calibrator_artifact_id == replay.calibrator_artifact_id,
        closeout.calibrator_artifact_hash == replay.calibrator_artifact_hash,
        closeout.holdout_trace_archive_id == replay.holdout_trace_archive_id,
        closeout.holdout_trace_archive_hash == replay.holdout_trace_archive_hash,
        closeout.holdout_record_count == replay.holdout_record_count,
        closeout.holdout_positive_count == replay.holdout_positive_count,
        closeout.holdout_negative_count == replay.holdout_negative_count,
        str(closeout.decision_outcome) == "KEEP_DIAGNOSTIC_ONLY",
        str(closeout.promotion_attempt_status) == "closed_not_promoted",
        closeout.automated_scheduling_confidence_status
        == "unfit_use_conservative_fallback",
        closeout.gate_checks.ranking_safety_failed is True,
        replay.gate_checks.ranking_safety_passed is False,
        tuple(str(label) for label in closeout.failure_labels)
        == ("ranking_safety_regression",),
    )
    if not all(conditions):
        _raise_source_state("replay and closeout evidence are not aligned")

    metric_pairs = (
        (closeout.metrics.raw_brier_score, replay.raw_metrics.brier_score),
        (
            closeout.metrics.calibrated_brier_score,
            replay.calibrated_metrics.brier_score,
        ),
        (closeout.metrics.brier_improvement, replay.brier_delta),
        (closeout.metrics.raw_fixed_bin_ece, replay.raw_metrics.fixed_bin_ece),
        (
            closeout.metrics.calibrated_fixed_bin_ece,
            replay.calibrated_metrics.fixed_bin_ece,
        ),
        (closeout.metrics.fixed_bin_ece_improvement, replay.fixed_bin_ece_delta),
        (closeout.metrics.raw_auroc, replay.raw_metrics.auroc),
        (closeout.metrics.calibrated_auroc, replay.calibrated_metrics.auroc),
        (closeout.metrics.auroc_delta, replay.auroc_delta),
        (
            closeout.metrics.maximum_allowed_auroc_degradation,
            replay.protocol.maximum_auroc_degradation,
        ),
    )
    if not all(
        isclose(left, right, rel_tol=0.0, abs_tol=1e-12) for left, right in metric_pairs
    ):
        _raise_source_state("replay and closeout metrics are not aligned")


def _build_manifest(
    payloads: dict[str, bytes],
) -> BoundedNegativeEvidenceReleaseManifest:
    entries = tuple(
        ReleaseManifestEntry(
            relative_path=filename,
            sha256=_sha256_bytes(payload),
            byte_count=len(payload),
        )
        for filename, payload in sorted(payloads.items())
    )
    return BoundedNegativeEvidenceReleaseManifest(
        schema_version="specsafe_bounded_negative_evidence_release_manifest_v1",
        release_id=RELEASE_ID,
        validity_marker="CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY",
        publication_status="local_pack_only",
        manifest_scope="all_release_files_except_manifest_itself",
        file_count=3,
        entries=entries,
        source_integrity_passed=True,
        canonical_build_passed=True,
        sanitization_passed=True,
        claims_boundary_passed=True,
    )


def _validate_sanitized_payloads(payloads: dict[str, bytes]) -> None:
    if set(payloads) != _PRE_MANIFEST_FILENAMES:
        _raise_sanitization("pre-manifest release file allowlist does not match")
    for filename, payload in payloads.items():
        lowered = payload.lower()
        for marker in _FORBIDDEN_CONTENT_MARKERS:
            if marker.lower() in lowered:
                _raise_sanitization(
                    f"forbidden content marker in {filename}: {marker!r}"
                )
        if _WINDOWS_ABSOLUTE_PATH_PATTERN.search(payload):
            _raise_sanitization(f"local absolute path detected in {filename}")


def _require_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir() or not (root / "pyproject.toml").is_file():
        raise BoundedNegativeEvidenceReleaseError(
            BoundedNegativeEvidenceReleaseErrorCode.INVALID_PROJECT_ROOT,
            "project_root must resolve to the SpecSafe repository root",
        )
    return root


def _resolve_output_directory(
    root: Path,
    output_directory: Path | str | None,
) -> Path:
    if output_directory is None:
        output = root / RELEASE_RELATIVE_DIRECTORY
    else:
        candidate = Path(output_directory).expanduser()
        output = candidate if candidate.is_absolute() else root / candidate
    output = output.resolve()
    if not output.is_relative_to(root):
        raise BoundedNegativeEvidenceReleaseError(
            BoundedNegativeEvidenceReleaseErrorCode.OUTPUT_OUTSIDE_REPOSITORY,
            "release output must remain inside the repository root",
        )
    return output


def _require_source_bytes(path: Path, expected_sha256: str) -> bytes:
    if not path.is_file():
        raise BoundedNegativeEvidenceReleaseError(
            BoundedNegativeEvidenceReleaseErrorCode.SOURCE_MISSING,
            f"required retained source artifact is missing: {path}",
        )
    payload = path.read_bytes()
    if _sha256_bytes(payload) != expected_sha256:
        raise BoundedNegativeEvidenceReleaseError(
            BoundedNegativeEvidenceReleaseErrorCode.SOURCE_HASH_MISMATCH,
            f"retained source artifact SHA-256 mismatch: {path}",
        )
    return payload


def _metric_row(label: str, raw: float, calibrated: float, movement: float) -> str:
    return (
        f"| {label} | {_format_number(raw)} | {_format_number(calibrated)} | "
        f"{_format_number(movement)} |"
    )


def _format_number(value: float) -> str:
    return f"{value:.12g}"


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _raise_source_state(message: str) -> None:
    raise BoundedNegativeEvidenceReleaseError(
        BoundedNegativeEvidenceReleaseErrorCode.SOURCE_STATE_INVALID,
        message,
    )


def _raise_committed_mismatch(message: str) -> None:
    raise BoundedNegativeEvidenceReleaseError(
        BoundedNegativeEvidenceReleaseErrorCode.COMMITTED_PACK_MISMATCH,
        message,
    )


def _raise_sanitization(message: str) -> None:
    raise BoundedNegativeEvidenceReleaseError(
        BoundedNegativeEvidenceReleaseErrorCode.SANITIZATION_FAILED,
        message,
    )
