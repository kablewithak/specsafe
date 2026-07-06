"""Regression tests for the one-time V4 final held-out calibration assessment."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from specsafe.heldout_calibration.v4_final_assessment import (
    V4AdaptivePolicyResearchEligibility,
    V4FinalHeldOutAssessmentResult,
    V4FinalHeldOutAssessmentStatus,
)
from specsafe.heldout_calibration.v4_final_assessment_runner import (
    V4FinalHeldOutAssessmentExecutionError,
    V4FinalHeldOutAssessmentExecutionErrorCode,
    run_v4_final_heldout_calibration_assessment_once,
)
from specsafe.traces.calibration_redesign_v4 import (
    CalibrationRedesignV4ScenarioFamilyRegistry,
)
from specsafe.traces.calibration_redesign_v4_final_manifest import (
    load_calibration_redesign_v4_final_manifested_fixture_set,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = (
    _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v4"
)
_CALIBRATION_EVIDENCE_ROOT = (
    _PROJECT_ROOT / "evidence" / "calibration" / "regularized-isotonic-calibration-v4"
)
_RESULT_RELATIVE_PATH = (
    Path("evidence")
    / "heldout-calibration"
    / "v4-final-heldout-calibration-assessment-v1"
    / "result.json"
)
_PRE_ASSESSMENT_EXCLUSIONS = (
    "No V4 final-evaluation held-out assessment or result is present.",
    "No V4 held-out calibration, policy, or runtime claim is made.",
    (
        "V4 final-evaluation manifest freeze does not author an assessment, "
        "baseline, or policy result."
    ),
)
_POST_ASSESSMENT_EXCLUSIONS = (
    "V4 held-out calibration assessment is write-once evidence.",
    "V4 held-out calibration evidence does not establish production performance.",
    "V4 policy, baseline, replay, and runtime-control work remain blocked pending remediation.",
    "V4 runtime control remains prohibited pending policy and baseline evidence.",
)


def _restore_pre_assessment_registry(fixture_root: Path) -> None:
    """Restore a temporary copy to the immutable pre-assessment input state.

    The committed fixture root records the completed write-once result. Assessment execution
    tests need a separate temporary copy at the immediately preceding authorised stage.
    """

    registry_path = fixture_root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if payload.get("registry_status") != "final_heldout_calibration_assessed":
        raise AssertionError("test setup requires the committed post-assessment V4 registry")

    payload.update(
        {
            "registry_status": "final_evaluation_manifest_frozen",
            "v4_final_heldout_calibration_assessment_authored": False,
            "final_heldout_calibration_assessment_sha256": None,
            "final_heldout_calibration_assessment_relative_path": None,
            "final_heldout_calibration_status": None,
            "next_authorized_artifact": "v4-final-heldout-calibration-assessment",
        }
    )
    retained_exclusions = [
        item
        for item in payload["explicit_exclusions"]
        if item not in _POST_ASSESSMENT_EXCLUSIONS
        and item not in _PRE_ASSESSMENT_EXCLUSIONS
    ]
    payload["explicit_exclusions"] = [
        *retained_exclusions,
        *_PRE_ASSESSMENT_EXCLUSIONS,
    ]
    CalibrationRedesignV4ScenarioFamilyRegistry.model_validate(payload)
    registry_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _copied_project_root(tmp_path: Path) -> tuple[Path, Path]:
    """Copy immutable V4 inputs so tests never mutate committed final evidence."""

    project_root = tmp_path / "project"
    fixture_root = (
        project_root / "data" / "fixtures" / "synthetic_calibration_redesign_v4"
    )
    calibration_evidence_root = (
        project_root
        / "evidence"
        / "calibration"
        / "regularized-isotonic-calibration-v4"
    )
    shutil.copytree(_FIXTURE_ROOT, fixture_root)
    _restore_pre_assessment_registry(fixture_root)
    calibration_evidence_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_CALIBRATION_EVIDENCE_ROOT, calibration_evidence_root)
    return project_root, fixture_root


def _result_path(project_root: Path) -> Path:
    return project_root / _RESULT_RELATIVE_PATH


def test_assessment_retains_complete_gate_evidence_and_blocks_ranking_regression(
    tmp_path: Path,
) -> None:
    project_root, fixture_root = _copied_project_root(tmp_path)

    result, destination = run_v4_final_heldout_calibration_assessment_once(
        fixture_root,
        _result_path(project_root),
    )

    assert destination.is_file()
    assert result.status is V4FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
    assert (
        result.adaptive_policy_research_eligibility
        is V4AdaptivePolicyResearchEligibility.BLOCKED
    )
    assert result.fallback is not None
    assert result.fallback.fallback_policy_id == "fixed_short_1"
    assert result.case_count == 36
    assert result.observation_count == 144
    assert tuple(item.observation_count for item in result.position_metrics) == (36, 36, 36, 36)
    assert result.brier_score_improvement == pytest.approx(0.035430737397119355)
    assert result.ece_10_bin_improvement == pytest.approx(0.0384251543209877)
    assert result.auroc_delta == pytest.approx(-0.012890625000000044)
    assert result.gate_checks.brier_improvement_passed is True
    assert result.gate_checks.ece_improvement_passed is True
    assert result.gate_checks.ranking_safety_passed is False
    assert result.calibration_refit_performed is False
    assert result.scheduler_or_policy_execution_performed is False
    assert result.runtime_control_eligible is False


def test_assessment_result_is_canonical_and_registry_anchors_failed_gate_output(
    tmp_path: Path,
) -> None:
    project_root, fixture_root = _copied_project_root(tmp_path)

    _, destination = run_v4_final_heldout_calibration_assessment_once(
        fixture_root,
        _result_path(project_root),
    )

    result_bytes = destination.read_bytes()
    result = V4FinalHeldOutAssessmentResult.model_validate_json(result_bytes)
    registry = json.loads((fixture_root / "scenario_family_registry.json").read_text())

    assert result.status is V4FinalHeldOutAssessmentStatus.RANKING_SAFETY_REGRESSION
    assert registry["registry_status"] == "final_heldout_calibration_assessed"
    assert registry["v4_final_heldout_calibration_assessment_authored"] is True
    assert registry["final_heldout_calibration_status"] == "RANKING_SAFETY_REGRESSION"
    assert registry["final_heldout_calibration_assessment_sha256"] == hashlib.sha256(
        result_bytes
    ).hexdigest()
    assert registry["final_heldout_calibration_assessment_relative_path"] == (
        _RESULT_RELATIVE_PATH.as_posix()
    )
    assert registry["next_authorized_artifact"] == "v4-calibration-remediation-decision"


def test_assessment_result_is_write_once(tmp_path: Path) -> None:
    project_root, fixture_root = _copied_project_root(tmp_path)
    destination = _result_path(project_root)

    run_v4_final_heldout_calibration_assessment_once(fixture_root, destination)

    with pytest.raises(V4FinalHeldOutAssessmentExecutionError) as error:
        run_v4_final_heldout_calibration_assessment_once(fixture_root, destination)

    assert error.value.code is V4FinalHeldOutAssessmentExecutionErrorCode.DESTINATION_ALREADY_EXISTS


def test_tampered_final_asset_blocks_assessment_before_result_creation(tmp_path: Path) -> None:
    project_root, fixture_root = _copied_project_root(tmp_path)
    tampered_asset = (
        fixture_root / "final_evaluation" / "inputs" / "cases" / "CRV4-201.json"
    )
    tampered_asset.write_bytes(tampered_asset.read_bytes() + b"\n")

    with pytest.raises(V4FinalHeldOutAssessmentExecutionError) as error:
        run_v4_final_heldout_calibration_assessment_once(
            fixture_root,
            _result_path(project_root),
        )

    assert error.value.code is V4FinalHeldOutAssessmentExecutionErrorCode.FROZEN_PROVENANCE_MISMATCH
    assert not _result_path(project_root).exists()


def test_tampered_calibration_artifact_blocks_assessment_before_result_creation(
    tmp_path: Path,
) -> None:
    project_root, fixture_root = _copied_project_root(tmp_path)
    artifact_path = (
        project_root
        / "evidence"
        / "calibration"
        / "regularized-isotonic-calibration-v4"
        / "artifact.json"
    )
    artifact_path.write_bytes(artifact_path.read_bytes() + b"\n")

    with pytest.raises(V4FinalHeldOutAssessmentExecutionError) as error:
        run_v4_final_heldout_calibration_assessment_once(
            fixture_root,
            _result_path(project_root),
        )

    assert error.value.code is V4FinalHeldOutAssessmentExecutionErrorCode.ARTIFACT_HASH_MISMATCH
    assert not _result_path(project_root).exists()


def test_identical_frozen_inputs_produce_identical_assessment_bytes(tmp_path: Path) -> None:
    first_project_root, first_fixture_root = _copied_project_root(tmp_path / "first")
    second_project_root, second_fixture_root = _copied_project_root(tmp_path / "second")

    _, first_destination = run_v4_final_heldout_calibration_assessment_once(
        first_fixture_root,
        _result_path(first_project_root),
    )
    _, second_destination = run_v4_final_heldout_calibration_assessment_once(
        second_fixture_root,
        _result_path(second_project_root),
    )

    assert first_destination.read_bytes() == second_destination.read_bytes()


def test_post_assessment_final_manifest_loader_remains_readable(tmp_path: Path) -> None:
    project_root, fixture_root = _copied_project_root(tmp_path)

    run_v4_final_heldout_calibration_assessment_once(
        fixture_root,
        _result_path(project_root),
    )

    loaded = load_calibration_redesign_v4_final_manifested_fixture_set(fixture_root)
    assert len(loaded.cases) == 36
    assert loaded.manifest.observation_count == 144
