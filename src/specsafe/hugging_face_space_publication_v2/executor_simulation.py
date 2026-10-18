"""Offline fault-injection qualification for a future existing-Space V2 executor.

This module has no Hugging Face API, credentials, or live publication entry point.
All commit and rollback operations affect only the in-memory simulation.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from specsafe.hugging_face_space_publication_candidate.models import CandidateFileDigest
from specsafe.hugging_face_space_publication_v2.readiness import (
    EXPECTED_FILES,
    EXPECTED_REPO_ID,
    EXPECTED_V1_REVISION,
    V2_CANDIDATE_PATH,
    preflight_existing_v2_space,
)
from specsafe.hugging_face_space_publication_v2.update_plan import (
    V1_FILES,
    ExistingSpaceV2UpdatePlan,
    build_existing_space_v2_update_plan,
)

V1_CANDIDATE_PATH = Path(
    "release/hugging-face-space-prebuilt-publication/specsafe-reliability-lab/candidate/space"
)
EXPECTED_APP_URL = "https://kabokablemolefe-specsafe-reliability-lab.static.hf.space"
SIMULATED_V2_REVISION = "b" * 40
SIMULATED_ROLLBACK_REVISION = "c" * 40
SIMULATED_OTHER_REVISION = "d" * 40
SIMULATED_CONCURRENT_REVISION = "e" * 40


class FailureScenario(StrEnum):
    HAPPY_PATH = "happy_path"
    CONCURRENT_BEFORE_COMMIT = "concurrent_before_commit"
    COMMIT_REJECTED = "commit_rejected"
    LOST_COMMIT_ACKNOWLEDGEMENT = "lost_commit_acknowledgement"
    V2_APPLICATION_FAILURE = "v2_application_failure"
    V2_FILE_HASH_MISMATCH = "v2_file_hash_mismatch"
    REMOTE_MOVES_BEFORE_ROLLBACK = "remote_moves_before_rollback"
    ROLLBACK_CAS_CONFLICT = "rollback_cas_conflict"
    ROLLBACK_VERIFICATION_FAILURE = "rollback_verification_failure"


class SimulationOutcome(StrEnum):
    VERIFIED_V2 = "verified_v2"
    NO_COMMIT = "no_commit"
    CONCURRENT_CHANGE = "concurrent_change"
    VERIFIED_V1_ROLLBACK = "verified_v1_rollback"
    MANUAL_INTERVENTION = "manual_intervention"


class SimulatedCasConflict(RuntimeError):
    """Parent revision is no longer current; no write was made by the attempted commit."""


class SimulatedCommitFailure(RuntimeError):
    """Injected failure that might not reveal whether the commit was applied."""


class SimulationIntegrityError(RuntimeError):
    """Local fixture bytes differ from the committed release contract."""


class V2ExecutorSimulationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["specsafe_v2_existing_space_executor_simulation_v1"]
    scenario: FailureScenario
    outcome: SimulationOutcome
    initial_revision: Literal["453481cc16518ba8d8b425813aca4cfc74c2d0e8"]
    final_revision: str
    expected_v2_candidate_tree_sha256: Literal[
        "20a9847f98d9b0d353a37a2f035c61524c20c3a92b0298ec2076e9d9278773d0"
    ]
    baseline_preflight_passed: Literal[True]
    forward_commit_attempted: bool
    forward_commit_acknowledged: bool
    rollback_attempted: bool
    rollback_verified: bool
    manual_intervention_required: bool
    simulated_commit_count: int
    trace: tuple[str, ...]
    simulation_only: Literal[True] = True
    publication_authorized: Literal[False] = False
    real_remote_mutation: Literal[False] = False
    live_receipt_written: Literal[False] = False


class InMemoryExistingSpaceGateway:
    """Exact five-file static Space with fault injection and atomic CAS semantics."""

    def __init__(
        self,
        *,
        baseline_files: dict[str, bytes],
        scenario: FailureScenario,
    ) -> None:
        if tuple(sorted(baseline_files)) != V1_FILES:
            raise SimulationIntegrityError("in-memory baseline must contain exact V1 files")
        self.files = dict(baseline_files)
        self.revision = EXPECTED_V1_REVISION
        self.scenario = scenario
        self.commits = 0
        self._corrupt_app = False
        self._forward_done = False
        self._changed_before_rollback = False

    def repository_state(self, repo_id: str, *, revision: str) -> dict[str, object]:
        self._require_repo(repo_id)
        if revision != "main":
            raise SimulationIntegrityError("only current main can be queried for state")
        return {
            "id": repo_id,
            "sha": self.revision,
            "private": False,
            "gated": False,
            "sdk": "static",
            "stage": "RUNNING",
        }

    def list_files(self, repo_id: str, *, revision: str) -> tuple[str, ...]:
        self._require_pinned_revision(repo_id, revision)
        return tuple(sorted(self.files))

    def read_file(self, repo_id: str, filename: str, *, revision: str) -> bytes:
        self._require_pinned_revision(repo_id, revision)
        return self.files[filename]

    def fetch_application(self, application_url: str) -> dict[str, object]:
        if application_url != EXPECTED_APP_URL:
            raise SimulationIntegrityError("unexpected application URL")
        body = self.files["index.html"]
        if self._corrupt_app:
            body = b"<html>simulated broken application</html>"
        return {
            "application_url": application_url,
            "status_code": 200,
            "content_type": "text/html; charset=utf-8",
            "body": body,
        }

    def guarded_commit(
        self,
        *,
        repo_id: str,
        parent_commit: str,
        uploads: dict[str, bytes],
        delete_files: tuple[str, ...],
        rollback: bool,
    ) -> str:
        self._require_repo(repo_id)
        if not rollback and self.scenario is FailureScenario.CONCURRENT_BEFORE_COMMIT:
            self.revision = SIMULATED_CONCURRENT_REVISION
        if rollback and self.scenario is FailureScenario.ROLLBACK_CAS_CONFLICT:
            self.revision = SIMULATED_OTHER_REVISION
        if self.revision != parent_commit:
            raise SimulatedCasConflict("atomic parent_commit comparison failed")
        if not rollback and self.scenario is FailureScenario.COMMIT_REJECTED:
            raise SimulatedCommitFailure("commit rejected before remote mutation")
        if set(uploads) & set(delete_files):
            raise SimulationIntegrityError("upload and deletion paths overlap")
        expected = V1_FILES if rollback else EXPECTED_FILES
        next_files = {name: body for name, body in self.files.items() if name not in delete_files}
        next_files.update(uploads)
        if tuple(sorted(next_files)) != expected:
            raise SimulationIntegrityError("atomic operation would produce unexpected file set")
        self.files = next_files
        self.commits += 1
        self.revision = SIMULATED_ROLLBACK_REVISION if rollback else SIMULATED_V2_REVISION
        self._corrupt_app = False
        if rollback:
            if self.scenario is FailureScenario.ROLLBACK_VERIFICATION_FAILURE:
                self.files["README.md"] += b"rollback-corruption"
        else:
            self._forward_done = True
            if self.scenario in (
                FailureScenario.V2_APPLICATION_FAILURE,
                FailureScenario.REMOTE_MOVES_BEFORE_ROLLBACK,
                FailureScenario.ROLLBACK_CAS_CONFLICT,
                FailureScenario.ROLLBACK_VERIFICATION_FAILURE,
            ):
                self._corrupt_app = True
            if self.scenario is FailureScenario.V2_FILE_HASH_MISMATCH:
                self.files["README.md"] += b"remote-corruption"
            if self.scenario is FailureScenario.LOST_COMMIT_ACKNOWLEDGEMENT:
                raise SimulatedCommitFailure("simulated acknowledgement lost after commit")
        return self.revision

    def move_remote_before_rollback(self) -> None:
        if (
            self.scenario is FailureScenario.REMOTE_MOVES_BEFORE_ROLLBACK
            and self._forward_done
            and not self._changed_before_rollback
        ):
            self.revision = SIMULATED_OTHER_REVISION
            self._changed_before_rollback = True

    @staticmethod
    def _require_repo(repo_id: str) -> None:
        if repo_id != EXPECTED_REPO_ID:
            raise SimulationIntegrityError("simulator requires pinned repository ID")

    def _require_pinned_revision(self, repo_id: str, revision: str) -> None:
        self._require_repo(repo_id)
        if revision != self.revision:
            raise SimulatedCasConflict("revision moved before read")


def _load_exact_files(
    root: Path,
    candidate_path: Path,
    file_digests: tuple[CandidateFileDigest, ...],
) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for item in file_digests:
        name = item.relative_path
        path = root / candidate_path / name
        if not path.is_file() or path.is_symlink():
            raise SimulationIntegrityError(f"missing or linked fixture file: {name}")
        payload = path.read_bytes()
        if len(payload) != item.byte_count or hashlib.sha256(payload).hexdigest() != item.sha256:
            raise SimulationIntegrityError(f"fixture bytes do not match release: {name}")
        result[name] = payload
    return result


def _verify_snapshot(
    gateway: InMemoryExistingSpaceGateway,
    *,
    revision: str,
    expected: dict[str, bytes],
    expect_v2: bool,
) -> bool:
    state = gateway.repository_state(EXPECTED_REPO_ID, revision="main")
    if (
        state["sha"] != revision
        or state["id"] != EXPECTED_REPO_ID
        or state["private"] is not False
        or state["sdk"] != "static"
    ):
        return False
    if gateway.list_files(EXPECTED_REPO_ID, revision=revision) != tuple(sorted(expected)):
        return False
    for name, expected_payload in expected.items():
        actual = gateway.read_file(EXPECTED_REPO_ID, name, revision=revision)
        if hashlib.sha256(actual).digest() != hashlib.sha256(expected_payload).digest():
            return False
    application = gateway.fetch_application(EXPECTED_APP_URL)
    if application["status_code"] != 200 or "text/html" not in str(application["content_type"]):
        return False
    body = application["body"]
    if not isinstance(body, bytes) or b"SpecSafe" not in body or b'id="root"' not in body:
        return False
    required_assets = (
        (b"index-BeNBJrmc.css", b"index-CAsY5KRm.js")
        if expect_v2
        else (b"index-ComhRJPm.css", b"index-DBdnOm5m.js")
    )
    return all(asset in body for asset in required_assets)


def _report(
    *,
    scenario: FailureScenario,
    outcome: SimulationOutcome,
    gateway: InMemoryExistingSpaceGateway,
    trace: list[str],
    forward_attempted: bool,
    forward_acknowledged: bool = False,
    rollback_attempted: bool = False,
    rollback_verified: bool = False,
) -> V2ExecutorSimulationReport:
    return V2ExecutorSimulationReport(
        schema_version="specsafe_v2_existing_space_executor_simulation_v1",
        scenario=scenario,
        outcome=outcome,
        initial_revision=EXPECTED_V1_REVISION,
        final_revision=gateway.revision,
        expected_v2_candidate_tree_sha256=(
            "20a9847f98d9b0d353a37a2f035c61524c20c3a92b0298ec2076e9d9278773d0"
        ),
        baseline_preflight_passed=True,
        forward_commit_attempted=forward_attempted,
        forward_commit_acknowledged=forward_acknowledged,
        rollback_attempted=rollback_attempted,
        rollback_verified=rollback_verified,
        manual_intervention_required=outcome
        in (
            SimulationOutcome.CONCURRENT_CHANGE,
            SimulationOutcome.MANUAL_INTERVENTION,
        ),
        simulated_commit_count=gateway.commits,
        trace=tuple(trace),
    )


def simulate_existing_v2_update(
    project_root: Path | str,
    *,
    scenario: FailureScenario = FailureScenario.HAPPY_PATH,
) -> V2ExecutorSimulationReport:
    """Exercise the update/rollback state machine; never access Hugging Face remotely."""
    root = Path(project_root).expanduser().resolve()
    plan: ExistingSpaceV2UpdatePlan = build_existing_space_v2_update_plan(root)
    if plan.publication_authorized is not False or plan.remote_mutation is not False:
        raise SimulationIntegrityError("offline operation plan escalated execution authority")
    v1_files = _load_exact_files(root, V1_CANDIDATE_PATH, plan.rollback_upload_files)
    v2_files = _load_exact_files(root, V2_CANDIDATE_PATH, plan.upload_files)
    if tuple(sorted(v1_files)) != V1_FILES or tuple(sorted(v2_files)) != EXPECTED_FILES:
        raise SimulationIntegrityError("candidate file allowlists changed")
    gateway = InMemoryExistingSpaceGateway(baseline_files=v1_files, scenario=scenario)

    # Reuse the separately qualified, read-only existing-Space preflight contract.
    preflight_existing_v2_space(root, gateway)
    trace = ["local_plan_verified", "retained_v1_verified", "remote_v1_preflight_verified"]

    try:
        forward_rev = gateway.guarded_commit(
            repo_id=plan.repository_id,
            parent_commit=plan.expected_parent_commit,
            uploads=v2_files,
            delete_files=plan.delete_files,
            rollback=False,
        )
    except SimulatedCasConflict:
        trace.append("forward_parent_cas_conflict_no_simulated_write")
        return _report(
            scenario=scenario,
            outcome=SimulationOutcome.CONCURRENT_CHANGE,
            gateway=gateway,
            trace=trace,
            forward_attempted=True,
        )
    except SimulatedCommitFailure:
        # A failed response is NOT evidence that no update occurred. Do not retry.
        trace.append("forward_commit_response_uncertain_no_blind_retry")
        outcome = (
            SimulationOutcome.NO_COMMIT
            if gateway.revision == plan.expected_parent_commit
            else SimulationOutcome.MANUAL_INTERVENTION
        )
        return _report(
            scenario=scenario,
            outcome=outcome,
            gateway=gateway,
            trace=trace,
            forward_attempted=True,
        )

    trace.append("forward_commit_acknowledged")
    try:
        verified = _verify_snapshot(
            gateway, revision=forward_rev, expected=v2_files, expect_v2=True
        )
    except SimulatedCasConflict:
        verified = False
    if verified:
        trace.append("public_v2_files_and_html_verified")
        return _report(
            scenario=scenario,
            outcome=SimulationOutcome.VERIFIED_V2,
            gateway=gateway,
            trace=trace,
            forward_attempted=True,
            forward_acknowledged=True,
        )

    trace.append("v2_post_commit_verification_failed")
    gateway.move_remote_before_rollback()
    if gateway.revision != forward_rev:
        trace.append("remote_revision_moved_rollback_withheld")
        return _report(
            scenario=scenario,
            outcome=SimulationOutcome.MANUAL_INTERVENTION,
            gateway=gateway,
            trace=trace,
            forward_attempted=True,
            forward_acknowledged=True,
        )
    try:
        restored_rev = gateway.guarded_commit(
            repo_id=plan.repository_id,
            parent_commit=forward_rev,
            uploads=v1_files,
            delete_files=plan.rollback_delete_files,
            rollback=True,
        )
    except SimulatedCasConflict:
        trace.append("rollback_parent_cas_conflict_manual_recovery_required")
        return _report(
            scenario=scenario,
            outcome=SimulationOutcome.MANUAL_INTERVENTION,
            gateway=gateway,
            trace=trace,
            forward_attempted=True,
            forward_acknowledged=True,
            rollback_attempted=True,
        )

    try:
        rollback_verified = _verify_snapshot(
            gateway, revision=restored_rev, expected=v1_files, expect_v2=False
        )
    except SimulatedCasConflict:
        rollback_verified = False
    trace.append("v1_rollback_verified" if rollback_verified else "v1_rollback_verification_failed")
    return _report(
        scenario=scenario,
        outcome=(
            SimulationOutcome.VERIFIED_V1_ROLLBACK
            if rollback_verified
            else SimulationOutcome.MANUAL_INTERVENTION
        ),
        gateway=gateway,
        trace=trace,
        forward_attempted=True,
        forward_acknowledged=True,
        rollback_attempted=True,
        rollback_verified=rollback_verified,
    )
