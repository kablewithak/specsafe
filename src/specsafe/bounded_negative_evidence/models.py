from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictReleaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ReleaseArtifactReference(StrictReleaseModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReleaseMetricSummary(StrictReleaseModel):
    raw_brier_score: float = Field(ge=0.0, le=1.0)
    calibrated_brier_score: float = Field(ge=0.0, le=1.0)
    brier_improvement: float
    raw_fixed_bin_ece: float = Field(ge=0.0, le=1.0)
    calibrated_fixed_bin_ece: float = Field(ge=0.0, le=1.0)
    fixed_bin_ece_improvement: float
    raw_auroc: float = Field(ge=0.0, le=1.0)
    calibrated_auroc: float = Field(ge=0.0, le=1.0)
    auroc_delta: float
    maximum_allowed_auroc_degradation: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_metric_direction(self) -> ReleaseMetricSummary:
        if self.brier_improvement <= 0.0:
            raise ValueError("release requires retained aggregate Brier improvement")
        if self.fixed_bin_ece_improvement <= 0.0:
            raise ValueError(
                "release requires retained aggregate fixed-bin ECE improvement"
            )
        if self.auroc_delta >= -self.maximum_allowed_auroc_degradation:
            raise ValueError("release requires the retained ranking-safety regression")
        return self


class ReleaseGateChecks(StrictReleaseModel):
    source_integrity_passed: Literal[True] = True
    source_schema_validation_passed: Literal[True] = True
    source_identity_alignment_passed: Literal[True] = True
    no_refit_boundary_passed: Literal[True] = True
    ranking_safety_failure_retained: Literal[True] = True
    non_promotion_boundary_passed: Literal[True] = True
    conservative_fallback_retained: Literal[True] = True
    canonical_build_passed: Literal[True] = True
    sanitization_passed: Literal[True] = True
    claims_boundary_passed: Literal[True] = True


class BoundedNegativeEvidenceReleaseSummary(StrictReleaseModel):
    schema_version: Literal["specsafe_bounded_negative_evidence_release_summary_v1"]
    release_id: Literal["specsafe-bounded-negative-evidence-v1"]
    release_type: Literal["bounded_negative_evidence"]
    validity_marker: Literal["CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"]
    publication_status: Literal["local_pack_only"]
    source_commit: Literal["8e3c176"]
    source_replay_report: ReleaseArtifactReference
    source_closeout_decision: ReleaseArtifactReference
    candidate_artifact_id: Literal["v5-qwen-combined-fixed-bin-isotonic-calibrator-v1"]
    candidate_artifact_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_trace_archive_id: Literal[
        "v5-qwen-candidate-calibrator-independent-holdout-v1/attempt-001-t4"
    ]
    holdout_trace_archive_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_record_count: Literal[192]
    holdout_positive_count: Literal[136]
    holdout_negative_count: Literal[56]
    metrics: ReleaseMetricSummary
    failure_labels: tuple[Literal["ranking_safety_regression"], ...]
    decision_outcome: Literal["KEEP_DIAGNOSTIC_ONLY"]
    candidate_disposition: Literal["retained_diagnostic_negative_evidence"]
    promotion_attempt_status: Literal["closed_not_promoted"]
    calibrator_promotion_status: Literal[
        "not_authorized_closed_ranking_safety_regression"
    ]
    automated_scheduling_confidence_status: Literal["unfit_use_conservative_fallback"]
    candidate_not_promoted: Literal[True]
    threshold_promotion_authorized: Literal[False]
    scheduler_promotion_authorized: Literal[False]
    production_claim_authorized: Literal[False]
    holdout_reuse_policy: tuple[str, ...] = Field(min_length=4)
    claims_permitted: tuple[str, ...] = Field(min_length=1)
    claims_forbidden: tuple[str, ...] = Field(min_length=1)
    privacy_controls: tuple[str, ...] = Field(min_length=1)
    publication_controls: tuple[str, ...] = Field(min_length=1)
    gate_checks: ReleaseGateChecks
    next_authorized_step: Literal["publication_readiness_review_and_license_decision"]

    @model_validator(mode="after")
    def validate_release_boundary(self) -> BoundedNegativeEvidenceReleaseSummary:
        if (
            self.holdout_positive_count + self.holdout_negative_count
            != self.holdout_record_count
        ):
            raise ValueError("holdout counts must sum to holdout_record_count")
        if self.failure_labels != ("ranking_safety_regression",):
            raise ValueError("release must retain exactly the ranking-safety failure")
        required_reuse_controls = {
            "do_not_refit_current_candidate_from_holdout",
            "do_not_tune_thresholds_from_holdout",
            "do_not_merge_holdout_into_future_fit_pool",
            "preserve_holdout_as_consumed_promotion_evidence",
        }
        if set(self.holdout_reuse_policy) != required_reuse_controls:
            raise ValueError("release must retain every consumed-holdout control")
        return self


class ReleaseManifestEntry(StrictReleaseModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)


class BoundedNegativeEvidenceReleaseManifest(StrictReleaseModel):
    schema_version: Literal["specsafe_bounded_negative_evidence_release_manifest_v1"]
    release_id: Literal["specsafe-bounded-negative-evidence-v1"]
    validity_marker: Literal["CALIBRATION_UNFIT_FOR_ADAPTIVE_POLICY"]
    publication_status: Literal["local_pack_only"]
    manifest_scope: Literal["all_release_files_except_manifest_itself"]
    file_count: Literal[3]
    entries: tuple[ReleaseManifestEntry, ...] = Field(min_length=3, max_length=3)
    source_integrity_passed: Literal[True]
    canonical_build_passed: Literal[True]
    sanitization_passed: Literal[True]
    claims_boundary_passed: Literal[True]

    @model_validator(mode="after")
    def validate_manifest_entries(self) -> BoundedNegativeEvidenceReleaseManifest:
        paths = tuple(entry.relative_path for entry in self.entries)
        if paths != tuple(sorted(paths)):
            raise ValueError("manifest entries must be sorted by relative_path")
        if set(paths) != {"README.md", "evidence_boundary.md", "release_summary.json"}:
            raise ValueError(
                "manifest must cover the exact three pre-manifest release files"
            )
        return self
