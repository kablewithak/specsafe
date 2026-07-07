"""Typed, descriptive-only evidence ledger contracts for baseline policy replay."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from specsafe.contracts import CausalSafetyStatus, TraceSplit
from specsafe.contracts.models import StrictContract
from specsafe.scheduling import (
    BaselinePolicyDescriptor,
    BaselinePolicyKind,
    FixedLengthPolicyConfig,
    StaticThresholdPolicyConfig,
)
from specsafe.trace_replay import ValidPolicyReplayResult


class LedgerEvidenceClass(StrEnum):
    """Evidence class carried by this local synthetic replay ledger."""

    SYNTHETIC_CONTROLLED = "synthetic_controlled"


class LedgerClaimStatus(StrEnum):
    """Claim posture enforced by this descriptive evidence boundary."""

    NO_CROSS_POLICY_WINNER_CLAIM = "no_cross_policy_winner_claim"


class LedgerBuildErrorCode(StrEnum):
    """Machine-readable failures for baseline-ledger construction and persistence."""

    INVALID_FIXTURE_SET = "invalid_fixture_set"
    INVALID_LEDGER = "invalid_ledger"
    NO_ELIGIBLE_CASES = "no_eligible_cases"
    UNSUPPORTED_POLICY = "unsupported_policy"
    EVALUATION_ONLY_POLICY = "evaluation_only_policy"
    DUPLICATE_POLICY_ID = "duplicate_policy_id"
    INVALID_DESTINATION = "invalid_destination"


class FixedLengthPolicyLedgerDescriptor(StrictContract):
    """Normalized fixed-length provenance retained with every ledger run."""

    policy_descriptor: BaselinePolicyDescriptor
    config: FixedLengthPolicyConfig

    @model_validator(mode="after")
    def validate_fixed_length_descriptor(self) -> FixedLengthPolicyLedgerDescriptor:
        """Require the standardized descriptor to match the exact fixed-length config."""

        descriptor = self.policy_descriptor
        if descriptor.policy_kind is not BaselinePolicyKind.FIXED_LENGTH:
            raise ValueError("fixed-length ledger descriptor must use policy_kind=fixed_length")
        if descriptor.policy_id != self.config.policy_id:
            raise ValueError("fixed-length ledger descriptor policy_id must match config")
        if descriptor.configuration_sha256 != self.config.configuration_sha256():
            raise ValueError("fixed-length ledger descriptor configuration hash must match config")
        return self


class StaticThresholdPolicyLedgerDescriptor(StrictContract):
    """Normalized static-threshold provenance retained with every ledger run."""

    policy_descriptor: BaselinePolicyDescriptor
    config: StaticThresholdPolicyConfig

    @model_validator(mode="after")
    def validate_static_threshold_descriptor(self) -> StaticThresholdPolicyLedgerDescriptor:
        """Require the standardized descriptor to match the exact threshold config."""

        descriptor = self.policy_descriptor
        if descriptor.policy_kind is not BaselinePolicyKind.STATIC_THRESHOLD:
            raise ValueError(
                "static-threshold ledger descriptor must use policy_kind=static_threshold"
            )
        if descriptor.policy_id != self.config.policy_id:
            raise ValueError("static-threshold ledger descriptor policy_id must match config")
        if descriptor.configuration_sha256 != self.config.configuration_sha256():
            raise ValueError(
                "static-threshold ledger descriptor configuration hash must match config"
            )
        return self


BaselinePolicyLedgerDescriptor = (
    FixedLengthPolicyLedgerDescriptor | StaticThresholdPolicyLedgerDescriptor
)


class BaselineReplayLedgerEntry(StrictContract):
    """One valid replay result retained under its policy and governed fixture identity."""

    policy_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    trace_id: str = Field(min_length=1, max_length=128)
    split: TraceSplit
    replay_result: ValidPolicyReplayResult

    @model_validator(mode="after")
    def validate_entry_identity(self) -> BaselineReplayLedgerEntry:
        """Prevent duplicate outer labels from drifting from the retained replay result."""

        result = self.replay_result
        if self.policy_id != result.policy_id:
            raise ValueError("ledger policy_id must match replay_result.policy_id")
        if self.case_id != result.case_id:
            raise ValueError("ledger case_id must match replay_result.case_id")
        if self.trace_id != result.trace_id:
            raise ValueError("ledger trace_id must match replay_result.trace_id")
        if self.split is not result.split:
            raise ValueError("ledger split must match replay_result.split")
        if result.causal_safety_status is not CausalSafetyStatus.PASS:
            raise ValueError("baseline ledger entries require causal-pass replay results")
        return self


class BaselineReplayEvidenceLedger(StrictContract):
    """Versioned, descriptive-only ledger for valid baseline replays.

    The ledger intentionally has no utility, ranking, score, or winner field. It preserves
    raw causal replay summaries and normalized configuration provenance for later governed
    comparison work only.
    """

    schema_version: Literal["baseline-replay-ledger-v1"] = "baseline-replay-ledger-v1"
    ledger_id: str = Field(min_length=1, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    evidence_class: Literal[LedgerEvidenceClass.SYNTHETIC_CONTROLLED] = (
        LedgerEvidenceClass.SYNTHETIC_CONTROLLED
    )
    claim_status: Literal[LedgerClaimStatus.NO_CROSS_POLICY_WINNER_CLAIM] = (
        LedgerClaimStatus.NO_CROSS_POLICY_WINNER_CLAIM
    )
    included_splits: tuple[TraceSplit, ...] = Field(min_length=1)
    policies: tuple[BaselinePolicyLedgerDescriptor, ...] = Field(min_length=1)
    entries: tuple[BaselineReplayLedgerEntry, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ledger_coverage_and_boundaries(self) -> BaselineReplayEvidenceLedger:
        """Require complete, causal, non-held-out coverage without comparative claims."""

        allowed_splits = {
            TraceSplit.DEVELOPMENT,
            TraceSplit.ADVERSARIAL_REGRESSION,
        }
        if set(self.included_splits) != allowed_splits:
            raise ValueError(
                "baseline ledger must include exactly development and adversarial_regression splits"
            )
        if len(set(self.included_splits)) != len(self.included_splits):
            raise ValueError("included_splits must not contain duplicates")

        policy_ids = tuple(descriptor.config.policy_id for descriptor in self.policies)
        if len(set(policy_ids)) != len(policy_ids):
            raise ValueError("ledger policies must have unique policy_id values")

        case_keys = {(entry.case_id, entry.trace_id, entry.split) for entry in self.entries}
        selected_cases = {(entry.case_id, entry.trace_id, entry.split) for entry in self.entries}
        if any(split not in allowed_splits for _, _, split in case_keys):
            raise ValueError("baseline ledger entries may not include calibration or final splits")

        expected_entry_keys = {
            (policy_id, case_id, trace_id, split)
            for policy_id in policy_ids
            for case_id, trace_id, split in selected_cases
        }
        actual_entry_keys = {
            (entry.policy_id, entry.case_id, entry.trace_id, entry.split) for entry in self.entries
        }
        if len(actual_entry_keys) != len(self.entries):
            raise ValueError("baseline ledger must not repeat a policy/case replay entry")
        if actual_entry_keys != expected_entry_keys:
            raise ValueError(
                "baseline ledger entries must cover every selected case for every policy"
            )
        return self
