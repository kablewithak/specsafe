from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictSpaceEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceArtifact(StrictSpaceEvidenceModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class PolicyDefinition(StrictSpaceEvidenceModel):
    policy_key: Literal["fixed_length", "static_threshold", "adaptive"]
    display_name: str = Field(min_length=1)
    plain_language_description: str = Field(min_length=1)
    capacity_aware: bool


class OutcomeCounts(StrictSpaceEvidenceModel):
    adaptive_higher: int = Field(ge=0)
    neutral: int = Field(ge=0)
    adaptive_lower: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_total(self) -> OutcomeCounts:
        if self.adaptive_higher + self.neutral + self.adaptive_lower != 6:
            raise ValueError("comparison outcome counts must cover exactly six cases")
        return self


class CaseEvidence(StrictSpaceEvidenceModel):
    case_id: Literal["MPC5-101", "MPC5-102", "MPC5-103", "MPC5-104", "MPC5-105", "MPC5-106"]
    split: Literal["development", "adversarial_regression"]
    capacity_profile: Literal[
        "flat_capacity_control",
        "light_load",
        "moderate_load",
        "saturated_load",
        "jagged_capacity",
    ]
    fixed_utility: float
    threshold_utility: float
    adaptive_utility: float
    adaptive_vs_fixed: Literal[
        "adaptive_higher_utility",
        "utility_neutral",
        "adaptive_lower_utility",
    ]
    adaptive_vs_threshold: Literal[
        "adaptive_higher_utility",
        "utility_neutral",
        "adaptive_lower_utility",
    ]
    plain_language_result: str = Field(min_length=1)


class CalibrationMetric(StrictSpaceEvidenceModel):
    metric_key: Literal["brier_score", "fixed_bin_ece", "auroc"]
    display_name: str = Field(min_length=1)
    raw_value: float
    calibrated_value: float
    movement: float
    lower_is_better: bool
    gate_result: Literal["improved", "failed_ranking_safety"]


class CalibrationGateEvidence(StrictSpaceEvidenceModel):
    holdout_record_count: Literal[192]
    holdout_positive_count: Literal[136]
    holdout_negative_count: Literal[56]
    metrics: tuple[CalibrationMetric, ...] = Field(min_length=3, max_length=3)
    maximum_allowed_auroc_degradation: Literal[0.001]
    observed_auroc_delta: float
    degradation_multiple_of_limit: float = Field(gt=1.0)
    failure_label: Literal["ranking_safety_regression"]
    decision_outcome: Literal["KEEP_DIAGNOSTIC_ONLY"]
    promotion_attempt_status: Literal["closed_not_promoted"]
    confidence_status: Literal["unfit_use_conservative_fallback"]
    plain_language_result: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_counts_and_metrics(self) -> CalibrationGateEvidence:
        if self.holdout_positive_count + self.holdout_negative_count != self.holdout_record_count:
            raise ValueError("holdout counts must sum to the retained record count")
        keys = tuple(metric.metric_key for metric in self.metrics)
        if keys != ("brier_score", "fixed_bin_ece", "auroc"):
            raise ValueError("calibration metrics must retain the declared display order")
        if self.observed_auroc_delta >= -self.maximum_allowed_auroc_degradation:
            raise ValueError("calibration evidence must retain the ranking-safety failure")
        return self


class DatasetPublicationEvidence(StrictSpaceEvidenceModel):
    repository_id: Literal["KaboKableMolefe/specsafe-bounded-negative-evidence-v1"]
    repository_url: Literal[
        "https://huggingface.co/datasets/KaboKableMolefe/specsafe-bounded-negative-evidence-v1"
    ]
    published_revision: Literal["1ff151fc0646102f6e7b107d1bceb9a18e50098a"]
    publication_manifest_sha256: Literal[
        "6dbc1c200b936a6f04e7a757886b7bf6c62e5d28a5ba5214f10036ae135a45d6"
    ]
    public: Literal[True]
    gated: Literal[False]
    exact_file_count: Literal[9]
    anonymous_verification_passed: Literal[True]


class EvidenceSection(StrictSpaceEvidenceModel):
    section_id: Literal[
        "overview",
        "what_was_tested",
        "policy_results",
        "capacity_conditions",
        "confidence_gate",
        "what_it_means",
        "evidence",
    ]
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)


class HuggingFaceSpaceEvidenceIndex(StrictSpaceEvidenceModel):
    schema_version: Literal["specsafe_hugging_face_space_evidence_index_v1"]
    space_id: Literal["specsafe-reliability-lab-v1"]
    space_repository_name: Literal["specsafe-reliability-lab"]
    source_commit: Literal["ec70bba"]
    title: Literal["SpecSafe — When Should AI Spend More Compute?"]
    short_description: Literal["AI reliability case study on adaptive verification."]
    quick_summary: str = Field(min_length=1)
    tested_question: str = Field(min_length=1)
    final_interpretation: str = Field(min_length=1)
    policies: tuple[PolicyDefinition, ...] = Field(min_length=3, max_length=3)
    adaptive_vs_fixed: OutcomeCounts
    adaptive_vs_threshold: OutcomeCounts
    cases: tuple[CaseEvidence, ...] = Field(min_length=6, max_length=6)
    valid_causal_comparisons: Literal[6]
    unsafe_retrospective_controls_excluded: Literal[6]
    unsafe_controls_failed_causal_safety: Literal[True]
    calibration_gate: CalibrationGateEvidence
    dataset_publication: DatasetPublicationEvidence
    maturity_labels: tuple[str, ...] = Field(min_length=3, max_length=3)
    supported_claims: tuple[str, ...] = Field(min_length=4)
    non_claims: tuple[str, ...] = Field(min_length=3)
    sections: tuple[EvidenceSection, ...] = Field(min_length=7, max_length=7)
    source_artifacts: tuple[SourceArtifact, ...] = Field(min_length=3, max_length=3)
    read_only: Literal[True]
    live_inference: Literal[False]
    user_input_collection: Literal[False]

    @model_validator(mode="after")
    def validate_index(self) -> HuggingFaceSpaceEvidenceIndex:
        expected_cases = (
            "MPC5-101",
            "MPC5-102",
            "MPC5-103",
            "MPC5-104",
            "MPC5-105",
            "MPC5-106",
        )
        if tuple(case.case_id for case in self.cases) != expected_cases:
            raise ValueError("case evidence must retain the governed deterministic order")
        expected_policies = ("fixed_length", "static_threshold", "adaptive")
        if tuple(policy.policy_key for policy in self.policies) != expected_policies:
            raise ValueError("policy definitions must retain the declared display order")
        if self.calibration_gate.decision_outcome != "KEEP_DIAGNOSTIC_ONLY":
            raise ValueError("Space evidence must retain the calibrator non-promotion decision")
        return self


class GeneratedArtifact(StrictSpaceEvidenceModel):
    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)


class HuggingFaceSpaceEvidenceManifest(StrictSpaceEvidenceModel):
    schema_version: Literal["specsafe_hugging_face_space_evidence_manifest_v1"]
    space_id: Literal["specsafe-reliability-lab-v1"]
    source_commit: Literal["ec70bba"]
    generated_artifact: GeneratedArtifact
    source_artifacts: tuple[SourceArtifact, ...] = Field(min_length=3, max_length=3)
    exact_output_file_count: Literal[2]
    evidence_frozen: Literal[True]
    ui_implementation_started: Literal[False]
    next_authorized_step: Literal["build_visually_polished_read_only_space_shell"]
