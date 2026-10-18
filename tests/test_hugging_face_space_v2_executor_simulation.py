from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from specsafe.hugging_face_space_publication_v2.executor_simulation import (
    SIMULATED_CONCURRENT_REVISION,
    SIMULATED_ROLLBACK_REVISION,
    SIMULATED_V2_REVISION,
    FailureScenario,
    InMemoryExistingSpaceGateway,
    SimulatedCasConflict,
    SimulationIntegrityError,
    SimulationOutcome,
    V2ExecutorSimulationReport,
    _verify_snapshot,
    simulate_existing_v2_update,
)
from specsafe.hugging_face_space_publication_v2.readiness import (
    EXPECTED_REPO_ID,
    EXPECTED_V1_REVISION,
)
from specsafe.hugging_face_space_publication_v2.update_plan import V1_FILES

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("scenario", "expected_outcome", "commit_count", "rollback"),
    [
        (FailureScenario.HAPPY_PATH, SimulationOutcome.VERIFIED_V2, 1, False),
        (FailureScenario.CONCURRENT_BEFORE_COMMIT, SimulationOutcome.CONCURRENT_CHANGE, 0, False),
        (FailureScenario.COMMIT_REJECTED, SimulationOutcome.NO_COMMIT, 0, False),
        (
            FailureScenario.LOST_COMMIT_ACKNOWLEDGEMENT,
            SimulationOutcome.MANUAL_INTERVENTION,
            1,
            False,
        ),
        (
            FailureScenario.V2_APPLICATION_FAILURE,
            SimulationOutcome.VERIFIED_V1_ROLLBACK,
            2,
            True,
        ),
        (
            FailureScenario.V2_FILE_HASH_MISMATCH,
            SimulationOutcome.VERIFIED_V1_ROLLBACK,
            2,
            True,
        ),
        (
            FailureScenario.REMOTE_MOVES_BEFORE_ROLLBACK,
            SimulationOutcome.MANUAL_INTERVENTION,
            1,
            False,
        ),
        (
            FailureScenario.ROLLBACK_CAS_CONFLICT,
            SimulationOutcome.MANUAL_INTERVENTION,
            1,
            False,
        ),
        (
            FailureScenario.ROLLBACK_VERIFICATION_FAILURE,
            SimulationOutcome.MANUAL_INTERVENTION,
            2,
            False,
        ),
    ],
)
def test_simulated_executor_failure_taxonomy(
    scenario: FailureScenario,
    expected_outcome: SimulationOutcome,
    commit_count: int,
    rollback: bool,
) -> None:
    report = simulate_existing_v2_update(PROJECT_ROOT, scenario=scenario)
    assert report.outcome is expected_outcome
    assert report.simulated_commit_count == commit_count
    assert report.rollback_verified is rollback
    assert report.simulation_only is True
    assert report.publication_authorized is False
    assert report.real_remote_mutation is False
    assert report.live_receipt_written is False
    assert report.baseline_preflight_passed is True
    assert report.trace[:3] == (
        "local_plan_verified",
        "retained_v1_verified",
        "remote_v1_preflight_verified",
    )


def test_success_means_v2_verified_only_in_simulation() -> None:
    report = simulate_existing_v2_update(PROJECT_ROOT)
    assert report.forward_commit_attempted is True
    assert report.forward_commit_acknowledged is True
    assert report.final_revision == SIMULATED_V2_REVISION
    assert report.rollback_attempted is False
    assert report.manual_intervention_required is False
    assert report.trace[-1] == "public_v2_files_and_html_verified"


def test_conflict_happens_at_atomic_commit_not_only_at_preflight() -> None:
    report = simulate_existing_v2_update(
        PROJECT_ROOT,
        scenario=FailureScenario.CONCURRENT_BEFORE_COMMIT,
    )
    assert report.final_revision == SIMULATED_CONCURRENT_REVISION
    assert report.forward_commit_attempted is True
    assert report.forward_commit_acknowledged is False
    assert report.rollback_attempted is False
    assert report.manual_intervention_required is True
    assert "forward_parent_cas_conflict_no_simulated_write" in report.trace


def test_lost_acknowledgement_is_not_a_safe_retry_or_rollback_signal() -> None:
    report = simulate_existing_v2_update(
        PROJECT_ROOT,
        scenario=FailureScenario.LOST_COMMIT_ACKNOWLEDGEMENT,
    )
    assert report.final_revision == SIMULATED_V2_REVISION
    assert report.forward_commit_acknowledged is False
    assert report.simulated_commit_count == 1
    assert report.rollback_attempted is False
    assert report.manual_intervention_required is True
    assert "forward_commit_response_uncertain_no_blind_retry" in report.trace


def test_successful_rollback_is_guarded_and_verified() -> None:
    report = simulate_existing_v2_update(
        PROJECT_ROOT,
        scenario=FailureScenario.V2_APPLICATION_FAILURE,
    )
    assert report.rollback_attempted is True
    assert report.rollback_verified is True
    assert report.final_revision == SIMULATED_ROLLBACK_REVISION
    assert report.trace[-1] == "v1_rollback_verified"


def test_remote_move_prevents_rollback_after_simulated_commit() -> None:
    report = simulate_existing_v2_update(
        PROJECT_ROOT,
        scenario=FailureScenario.REMOTE_MOVES_BEFORE_ROLLBACK,
    )
    assert report.rollback_attempted is False
    assert report.manual_intervention_required is True
    assert "remote_revision_moved_rollback_withheld" in report.trace


def test_rollback_conflict_preserves_unknown_owner_changes() -> None:
    report = simulate_existing_v2_update(
        PROJECT_ROOT,
        scenario=FailureScenario.ROLLBACK_CAS_CONFLICT,
    )
    assert report.rollback_attempted is True
    assert report.rollback_verified is False
    assert report.manual_intervention_required is True
    assert "rollback_parent_cas_conflict_manual_recovery_required" in report.trace


def test_bad_simulator_repo_or_cas_blocks_mutation() -> None:
    original = {name: name.encode("utf-8") for name in V1_FILES}
    gateway = InMemoryExistingSpaceGateway(
        baseline_files=original,
        scenario=FailureScenario.HAPPY_PATH,
    )
    with pytest.raises(SimulationIntegrityError, match="pinned repository ID"):
        gateway.guarded_commit(
            repo_id="other/space",
            parent_commit=EXPECTED_V1_REVISION,
            uploads={},
            delete_files=(),
            rollback=False,
        )
    with pytest.raises(SimulatedCasConflict, match="parent_commit"):
        gateway.guarded_commit(
            repo_id=EXPECTED_REPO_ID,
            parent_commit="f" * 40,
            uploads={},
            delete_files=(),
            rollback=False,
        )
    assert gateway.commits == 0
    assert gateway.revision == EXPECTED_V1_REVISION
    assert gateway.files == original


def test_simulator_verification_rejects_wrong_file_bytes() -> None:
    original = {name: name.encode("utf-8") for name in V1_FILES}
    original["index.html"] = (
        b'<html><title>SpecSafe</title><div id="root"></div>'
        b'<link href="/assets/index-ComhRJPm.css">'
        b'<script src="/assets/index-DBdnOm5m.js"></script></html>'
    )
    gateway = InMemoryExistingSpaceGateway(
        baseline_files=original,
        scenario=FailureScenario.HAPPY_PATH,
    )
    assert _verify_snapshot(
        gateway,
        revision=EXPECTED_V1_REVISION,
        expected=original,
        expect_v2=False,
    )
    assert not _verify_snapshot(
        gateway,
        revision=EXPECTED_V1_REVISION,
        expected={**original, "README.md": b"different"},
        expect_v2=False,
    )


def test_simulation_report_cannot_escalate_authorization() -> None:
    report = simulate_existing_v2_update(PROJECT_ROOT)
    record = report.model_dump()
    record["publication_authorized"] = True
    with pytest.raises(ValidationError, match="publication_authorized"):
        V2ExecutorSimulationReport.model_validate(record)
    assert report.model_dump(mode="json")["real_remote_mutation"] is False


def test_simulation_source_contains_no_hub_adapter_or_network_upload() -> None:
    import inspect

    import specsafe.hugging_face_space_publication_v2.executor_simulation as module

    source = inspect.getsource(module)
    for forbidden in (
        "import huggingface_hub",
        "from huggingface_hub",
        "HfApi(",
        "urlopen(",
        "create_commit(",
    ):
        assert forbidden not in source
    assert "parent_commit" in source
    assert "SIMULATED_V2_REVISION" in source
