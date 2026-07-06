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


def _copy_project_root(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT, project_root)
    return (
        project_root,
        project_root / "data" / "fixtures" / "synthetic_calibration_redesign_v3",
    )


def test_final_evidence_index_preserves_frozen_calibration_provenance() -> None:
    index = load_calibration_redesign_v3_final_evidence_index(FIXTURE_ROOT)

    assert index.final_evaluation_case_count == 24
    assert index.final_evaluation_observation_count == 96
    assert index.candidate_positions_per_case == 4
    assert index.index_status == "jagged_capacity_authored"
    assert sum(len(family.authored_case_ids) for family in index.families) == 24
    assert index.next_authorized_artifact == "v3-final-evaluation-manifest-freeze"


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
