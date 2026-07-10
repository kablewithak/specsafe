from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AnalysisStatus(StrEnum):
    REPLAY_READY = "replay_ready"
    REPLAY_BLOCKED = "replay_blocked"


class PromotionStatus(StrEnum):
    NOT_AUTHORIZED = "not_authorized_pending_independent_holdout_replay"


class CoverageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_count: int = Field(ge=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    positive_rate: float = Field(ge=0.0, le=1.0)
    mean_raw_confidence: float = Field(ge=0.0, le=1.0)


class ReplayFieldMap(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    join_key: tuple[str, ...]
    calibrator_input_field: str
    diagnostic_label_field: str
    workload_field: str
    position_field: str
    provenance_fields: tuple[str, ...]
    forbidden_fit_actions: tuple[str, ...]


class IndependentHoldoutAnalysisReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    report_id: str
    source_commit: str
    collection_id: str
    attempt_id: str
    data_role: str
    evidence_class: str
    trace_schema_version: str
    runtime_record_count: int = Field(ge=0)
    expected_outcome_record_count: int = Field(ge=0)
    timing_record_count: int = Field(ge=0)
    unique_trace_count: int = Field(ge=0)
    case_count: int = Field(ge=0)
    joined_record_count: int = Field(ge=0)
    duplicate_join_key_count: int = Field(ge=0)
    missing_runtime_outcome_count: int = Field(ge=0)
    missing_runtime_timing_count: int = Field(ge=0)
    raw_prompt_text_retained: bool
    raw_brier_diagnostic: float = Field(ge=0.0, le=1.0)
    raw_discrimination_auc: float = Field(ge=0.0, le=1.0)
    raw_confidence_min: float = Field(ge=0.0, le=1.0)
    raw_confidence_max: float = Field(ge=0.0, le=1.0)
    coverage_by_workload: dict[str, CoverageSummary]
    coverage_by_position: dict[str, CoverageSummary]
    replay_field_map: ReplayFieldMap
    required_runtime_fields_present: tuple[str, ...]
    required_outcome_fields_present: tuple[str, ...]
    analysis_status: AnalysisStatus
    replay_blockers: tuple[str, ...]
    calibrator_promotion_status: PromotionStatus
    threshold_promotion_status: str
    scheduler_promotion_status: str
    claims_permitted: tuple[str, ...]
    claims_forbidden: tuple[str, ...]
