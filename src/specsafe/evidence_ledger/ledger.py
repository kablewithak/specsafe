"""Build and persist descriptive-only evidence ledgers for causal baseline replay."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from specsafe.contracts import SyntheticTraceFixtureSet, TraceSplit
from specsafe.evidence_ledger.models import (
    BaselinePolicyLedgerDescriptor,
    BaselineReplayEvidenceLedger,
    BaselineReplayLedgerEntry,
    FixedLengthPolicyLedgerDescriptor,
    LedgerBuildErrorCode,
    StaticThresholdPolicyLedgerDescriptor,
)
from specsafe.scheduling import (
    FixedLengthVerificationPolicy,
    StaticThresholdVerificationPolicy,
)
from specsafe.trace_replay import run_valid_policy_replay

_ALLOWED_SPLITS = (
    TraceSplit.DEVELOPMENT,
    TraceSplit.ADVERSARIAL_REGRESSION,
)


class BaselineLedgerBuildError(ValueError):
    """Raised when a baseline replay ledger would weaken its evidence boundary."""

    def __init__(self, code: LedgerBuildErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


def build_baseline_replay_evidence_ledger(
    fixture_set: SyntheticTraceFixtureSet,
    *,
    ledger_id: str,
    run_id: str,
    policies: Sequence[object],
) -> BaselineReplayEvidenceLedger:
    """Replay valid baseline policies on development and adversarial cases only.

    This is a descriptive record, not a utility comparison. It excludes calibration and
    final-evaluation cases, requires typed baseline configurations, and delegates each
    policy/case execution to the existing causal valid-replay path.
    """

    if type(fixture_set) is not SyntheticTraceFixtureSet:
        raise BaselineLedgerBuildError(
            LedgerBuildErrorCode.INVALID_FIXTURE_SET,
            "baseline ledger requires the exact SyntheticTraceFixtureSet contract",
        )

    policy_pairs = tuple(_describe_baseline_policy(policy) for policy in policies)
    policy_ids = tuple(descriptor.config.policy_id for descriptor, _ in policy_pairs)
    if len(set(policy_ids)) != len(policy_ids):
        raise BaselineLedgerBuildError(
            LedgerBuildErrorCode.DUPLICATE_POLICY_ID,
            "baseline ledger policies must have unique policy_id values",
        )

    selected_cases = tuple(
        case
        for case in fixture_set.cases
        if case.runtime_input.split in _ALLOWED_SPLITS
    )
    if not selected_cases:
        raise BaselineLedgerBuildError(
            LedgerBuildErrorCode.NO_ELIGIBLE_CASES,
            "baseline ledger requires development or adversarial regression cases",
        )

    entries: list[BaselineReplayLedgerEntry] = []
    for descriptor, policy in policy_pairs:
        for case in selected_cases:
            result = run_valid_policy_replay(
                fixture_set,
                case_id=case.runtime_input.case_id,
                policy=policy,
                run_id=run_id,
            )
            entries.append(
                BaselineReplayLedgerEntry(
                    policy_id=descriptor.config.policy_id,
                    case_id=result.case_id,
                    trace_id=result.trace_id,
                    split=result.split,
                    replay_result=result,
                )
            )

    return BaselineReplayEvidenceLedger(
        ledger_id=ledger_id,
        run_id=run_id,
        fixture_set_id=fixture_set.manifest.fixture_set_id,
        fixture_set_version=fixture_set.manifest.fixture_set_version,
        included_splits=_ALLOWED_SPLITS,
        policies=tuple(descriptor for descriptor, _ in policy_pairs),
        entries=tuple(entries),
    )


def write_baseline_replay_evidence_ledger_json(
    ledger: BaselineReplayEvidenceLedger,
    destination: Path,
) -> Path:
    """Write one explicit local JSON evidence artifact without changing source fixtures."""

    if type(ledger) is not BaselineReplayEvidenceLedger:
        raise BaselineLedgerBuildError(
            LedgerBuildErrorCode.INVALID_LEDGER,
            "ledger persistence requires the exact BaselineReplayEvidenceLedger contract",
        )
    if destination.suffix.lower() != ".json":
        raise BaselineLedgerBuildError(
            LedgerBuildErrorCode.INVALID_DESTINATION,
            "baseline ledger destination must use a .json suffix",
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_destination = destination.with_name(f"{destination.name}.tmp")
    temporary_destination.write_text(
        f"{ledger.model_dump_json(indent=2)}\n",
        encoding="utf-8",
    )
    temporary_destination.replace(destination)
    return destination


def _describe_baseline_policy(
    policy: object,
) -> tuple[BaselinePolicyLedgerDescriptor, object]:
    """Accept only typed causal baselines and retain their exact configurations."""

    if type(policy) is FixedLengthVerificationPolicy:
        return FixedLengthPolicyLedgerDescriptor(config=policy.config), policy
    if type(policy) is StaticThresholdVerificationPolicy:
        return StaticThresholdPolicyLedgerDescriptor(config=policy.config), policy

    config = getattr(policy, "config", None)
    if getattr(config, "evaluation_only", False) is True:
        raise BaselineLedgerBuildError(
            LedgerBuildErrorCode.EVALUATION_ONLY_POLICY,
            "evaluation-only policies cannot enter the baseline evidence ledger",
        )
    raise BaselineLedgerBuildError(
        LedgerBuildErrorCode.UNSUPPORTED_POLICY,
        "baseline ledger supports only fixed-length and static-threshold policies",
    )
