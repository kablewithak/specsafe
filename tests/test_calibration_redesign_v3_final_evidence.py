from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from specsafe.traces.calibration_redesign_v3_final_evidence import (
    CalibrationRedesignV3FinalEvidenceLoadError,
    CalibrationRedesignV3FinalEvidenceViolationCode,
    load_calibration_redesign_v3_final_evidence_index,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
FROZEN_CALIBRATION_EVIDENCE_ROOT = (
    PROJECT_ROOT / "evidence" / "calibration" / "quantile-isotonic-calibration-v1"
)


def _copy_project_root(tmp_path: Path) -> tuple[Path, Path]:
    """Copy only the governed V3 assets required by these mutation tests."""

    project_root = tmp_path / "project"
    fixture_root = project_root / "data" / "fixtures" / "synthetic_calibration_redesign_v3"
    calibration_evidence_root = (
        project_root / "evidence" / "calibration" / "quantile-isotonic-calibration-v1"
    )
    shutil.copytree(FIXTURE_ROOT, fixture_root)
    shutil.copytree(FROZEN_CALIBRATION_EVIDENCE_ROOT, calibration_evidence_root)
    return project_root, fixture_root


def test_final_evidence_index_preserves_frozen_calibration_provenance() -> None:
    index = load_calibration_redesign_v3_final_evidence_index(FIXTURE_ROOT)

    assert index.final_evaluation_case_count == 24
    assert index.final_evaluation_observation_count == 96
    assert index.candidate_positions_per_case == 4
    assert index.schema_version == "calibration-redesign-v3-final-evidence-index-v2"
    assert index.index_status == "final_evaluation_manifest_frozen"
    assert sum(len(family.authored_case_ids) for family in index.families) == 24
    assert index.final_evaluation_manifest_path == "final_evaluation_manifest.json"
    assert index.next_authorized_artifact == "v3-one-time-final-assessment"


def test_final_evidence_index_rejects_changed_frozen_artifact(tmp_path: Path) -> None:
    project_root, fixture_root = _copy_project_root(tmp_path)
    artifact_path = (
        project_root
        / "evidence"
        / "calibration"
        / "quantile-isotonic-calibration-v1"
        / "artifact.json"
    )
    artifact_path.write_bytes(artifact_path.read_bytes() + b"\n")

    with pytest.raises(CalibrationRedesignV3FinalEvidenceLoadError) as error_info:
        load_calibration_redesign_v3_final_evidence_index(fixture_root)

    assert (
        error_info.value.code
        is CalibrationRedesignV3FinalEvidenceViolationCode.INDEX_PROVENANCE_MISMATCH
    )
