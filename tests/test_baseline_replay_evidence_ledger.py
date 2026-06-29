from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.evidence_ledger import (
    BaselineLedgerBuildError,
    LedgerBuildErrorCode,
    LedgerClaimStatus,
    build_baseline_replay_evidence_ledger,
    write_baseline_replay_evidence_ledger_json,
)
from specsafe.scheduling import (
    FixedLengthPolicyConfig,
    FixedLengthVerificationPolicy,
    StaticThresholdPolicyConfig,
    StaticThresholdVerificationPolicy,
    UnsafeRetrospectiveLookaheadPolicy,
)
from specsafe.traces import load_synthetic_trace_fixture_set

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_trace_baselines"
)


def make_policies() -> tuple[object, ...]:
    return (
        FixedLengthVerificationPolicy(
            FixedLengthPolicyConfig(
                policy_id="fixed-length-ledger-v1",
                maximum_verification_length=3,
            )
        ),
        StaticThresholdVerificationPolicy(
            StaticThresholdPolicyConfig(
                policy_id="static-threshold-ledger-v1",
                minimum_conditional_survival_confidence=0.4,
            )
        ),
    )


def test_ledger_replays_all_governed_cases_for_each_baseline() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)

    ledger = build_baseline_replay_evidence_ledger(
        fixture_set,
        ledger_id="synthetic-baseline-ledger-v1",
        run_id="baseline-ledger-test-run-v1",
        policies=make_policies(),
    )

    assert ledger.claim_status is LedgerClaimStatus.NO_CROSS_POLICY_WINNER_CLAIM
    assert tuple(descriptor.config.policy_id for descriptor in ledger.policies) == (
        "fixed-length-ledger-v1",
        "static-threshold-ledger-v1",
    )
    assert tuple(entry.case_id for entry in ledger.entries) == (
        "STF-001",
        "STF-002",
        "STF-003",
        "STF-001",
        "STF-002",
        "STF-003",
    )
    assert {entry.split.value for entry in ledger.entries} == {
        "development",
        "adversarial_regression",
    }
    assert "STF-004" not in {entry.case_id for entry in ledger.entries}


def test_ledger_is_deterministic_for_fixed_inputs_and_run_identity() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)

    first = build_baseline_replay_evidence_ledger(
        fixture_set,
        ledger_id="synthetic-baseline-ledger-v1",
        run_id="baseline-ledger-test-run-v1",
        policies=make_policies(),
    )
    second = build_baseline_replay_evidence_ledger(
        fixture_set,
        ledger_id="synthetic-baseline-ledger-v1",
        run_id="baseline-ledger-test-run-v1",
        policies=make_policies(),
    )

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_ledger_rejects_unsafe_retrospective_policy() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)

    with pytest.raises(BaselineLedgerBuildError) as error:
        build_baseline_replay_evidence_ledger(
            fixture_set,
            ledger_id="synthetic-baseline-ledger-v1",
            run_id="baseline-ledger-test-run-v1",
            policies=(UnsafeRetrospectiveLookaheadPolicy(),),
        )

    assert error.value.code is LedgerBuildErrorCode.EVALUATION_ONLY_POLICY


def test_ledger_rejects_duplicate_policy_ids() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)
    duplicate_policy_id = "duplicate-policy-id"
    policies = (
        FixedLengthVerificationPolicy(
            FixedLengthPolicyConfig(
                policy_id=duplicate_policy_id,
                maximum_verification_length=2,
            )
        ),
        StaticThresholdVerificationPolicy(
            StaticThresholdPolicyConfig(
                policy_id=duplicate_policy_id,
                minimum_conditional_survival_confidence=0.4,
            )
        ),
    )

    with pytest.raises(BaselineLedgerBuildError) as error:
        build_baseline_replay_evidence_ledger(
            fixture_set,
            ledger_id="synthetic-baseline-ledger-v1",
            run_id="baseline-ledger-test-run-v1",
            policies=policies,
        )

    assert error.value.code is LedgerBuildErrorCode.DUPLICATE_POLICY_ID


def test_ledger_json_writer_preserves_machine_readable_content(tmp_path: Path) -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)
    ledger = build_baseline_replay_evidence_ledger(
        fixture_set,
        ledger_id="synthetic-baseline-ledger-v1",
        run_id="baseline-ledger-test-run-v1",
        policies=make_policies(),
    )
    destination = tmp_path / "baseline-replay-ledger.json"

    written_path = write_baseline_replay_evidence_ledger_json(ledger, destination)

    assert written_path == destination
    assert json.loads(destination.read_text(encoding="utf-8")) == ledger.model_dump(mode="json")


def test_ledger_json_writer_rejects_non_json_destination(tmp_path: Path) -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)
    ledger = build_baseline_replay_evidence_ledger(
        fixture_set,
        ledger_id="synthetic-baseline-ledger-v1",
        run_id="baseline-ledger-test-run-v1",
        policies=make_policies(),
    )

    with pytest.raises(BaselineLedgerBuildError) as error:
        write_baseline_replay_evidence_ledger_json(ledger, tmp_path / "ledger.txt")

    assert error.value.code is LedgerBuildErrorCode.INVALID_DESTINATION


def test_ledger_contract_has_no_winner_policy_field() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)
    ledger = build_baseline_replay_evidence_ledger(
        fixture_set,
        ledger_id="synthetic-baseline-ledger-v1",
        run_id="baseline-ledger-test-run-v1",
        policies=make_policies(),
    )

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        type(ledger).model_validate(
            {
                **ledger.model_dump(mode="json"),
                "winner_policy_id": "fixed-length-ledger-v1",
            }
        )
