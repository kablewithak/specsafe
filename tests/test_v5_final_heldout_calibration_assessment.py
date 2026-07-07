"""Execution and retained-evidence tests for the write-once V5 held-out gate."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from specsafe.heldout_calibration.v5_final_assessment import (
    V5AdaptivePolicyResearchEligibility,
    V5FinalHeldOutAssessmentResult,
    V5FinalHeldOutAssessmentStatus,
)
from specsafe.heldout_calibration.v5_final_assessment_runner import (
    V5FinalHeldOutAssessmentExecutionError,
    V5FinalHeldOutAssessmentExecutionErrorCode,
    build_v5_final_heldout_calibration_result,
    run_v5_final_heldout_calibration_assessment_once,
)
from specsafe.traces.calibration_successor_v5 import (
    load_calibration_successor_v5_scenario_family_registry,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SOURCE_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
_RESULT_RELATIVE_PATH = (
    "evidence/heldout-calibration/v5-final-heldout-calibration-assessment-v1/result.json"
)


def _copied_pre_assessment_fixture_root(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    fixture_root = project_root / "data" / "fixtures" / "synthetic_calibration_successor_v5"
    fixture_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_SOURCE_FIXTURE_ROOT, fixture_root)

    registry_path = fixture_root / "scenario_family_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry.update(
        {
            "registry_status": "final_evaluation_manifest_frozen",
            "v5_final_heldout_calibration_assessment_authored": False,
            "final_heldout_calibration_assessment_sha256": None,
            "final_heldout_calibration_assessment_relative_path": None,
            "final_heldout_calibration_status": None,
            "next_authorized_artifact": "v5-final-heldout-calibration-assessment",
        }
    )
    post_assessment_exclusions = {
        "V5 held-out calibration assessment is write-once evidence.",
        (
            "V5 held-out calibration evidence is synthetic and does not establish "
            "production performance."
        ),
        "No V5 runtime control is authorized.",
        (
            "V5 adaptive policy research is eligible only under controlled "
            "frozen-evidence evaluation; no scheduler, baseline comparison, "
            "capacity profile, or utility result is present."
        ),
    }
    registry["explicit_exclusions"] = [
        item for item in registry["explicit_exclusions"] if item not in post_assessment_exclusions
    ]
    for item in (
        (
            "No V5 scheduler, baseline comparison, capacity profile, utility scorer, "
            "or runtime control is authorized."
        ),
        (
            "V5 final-evaluation manifest freeze does not author an assessment, "
            "baseline, or policy result."
        ),
        (
            "No V5 held-out assessment, scheduler, baseline comparison, capacity "
            "profile, utility scorer, or runtime control is authorized."
        ),
    ):
        if item not in registry["explicit_exclusions"]:
            registry["explicit_exclusions"].append(item)
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return project_root, fixture_root


def test_retained_v5_assessment_result_passes_the_frozen_gate() -> None:
    result_path = _PROJECT_ROOT / _RESULT_RELATIVE_PATH
    result = V5FinalHeldOutAssessmentResult.model_validate_json(result_path.read_bytes())

    assert result.status is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
    assert (
        result.adaptive_policy_research_eligibility
        is V5AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH
    )
    assert result.fallback is None
    assert result.case_count == 36
    assert result.observation_count == 144
    assert result.brier_score_improvement == pytest.approx(0.043888783385395425)
    assert result.ece_10_bin_improvement == pytest.approx(0.10653018631428904)
    assert result.auroc_delta == pytest.approx(0.0)
    assert result.calibration_refit_performed is False
    assert result.policy_or_replay_execution_performed is False
    assert result.runtime_control_eligible is False


def test_v5_assessment_is_deterministic_from_a_pre_assessment_copy(tmp_path: Path) -> None:
    _, fixture_root = _copied_pre_assessment_fixture_root(tmp_path)

    result = build_v5_final_heldout_calibration_result(fixture_root)

    assert result.status is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE
    assert result.brier_score_improvement == pytest.approx(0.043888783385395425)
    assert result.ece_10_bin_improvement == pytest.approx(0.10653018631428904)
    assert result.auroc_delta == pytest.approx(0.0)


def test_v5_assessment_writes_once_and_advances_registry_after_persistence(
    tmp_path: Path,
) -> None:
    project_root, fixture_root = _copied_pre_assessment_fixture_root(tmp_path)
    destination = project_root / _RESULT_RELATIVE_PATH

    result, persisted = run_v5_final_heldout_calibration_assessment_once(
        fixture_root,
        destination,
    )

    assert persisted == destination
    assert destination.is_file()
    assert result.status is V5FinalHeldOutAssessmentStatus.PASSES_V5_CALIBRATION_ELIGIBILITY_GATE

    registry = load_calibration_successor_v5_scenario_family_registry(
        fixture_root / "scenario_family_registry.json",
        allow_final_evaluation_manifest_assets=True,
    )
    assert registry.registry_status == "final_heldout_calibration_assessed"
    assert registry.v5_final_heldout_calibration_assessment_authored is True
    assert (
        registry.final_heldout_calibration_assessment_sha256
        == hashlib.sha256(destination.read_bytes()).hexdigest()
    )
    assert registry.final_heldout_calibration_status == result.status.value
    assert registry.next_authorized_artifact == "v5-calibrated-causal-load-aware-policy-foundation"


def test_v5_existing_destination_blocks_any_reassessment_before_input_loading(
    tmp_path: Path,
) -> None:
    project_root, fixture_root = _copied_pre_assessment_fixture_root(tmp_path)
    destination = project_root / _RESULT_RELATIVE_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("already retained\n", encoding="utf-8")
    registry_before = (fixture_root / "scenario_family_registry.json").read_bytes()

    with pytest.raises(V5FinalHeldOutAssessmentExecutionError) as error:
        run_v5_final_heldout_calibration_assessment_once(fixture_root, destination)

    assert error.value.code is V5FinalHeldOutAssessmentExecutionErrorCode.DESTINATION_ALREADY_EXISTS
    assert (fixture_root / "scenario_family_registry.json").read_bytes() == registry_before
