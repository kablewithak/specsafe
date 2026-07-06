"""Regression tests for V4 module dependency direction."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_clean_import(import_statement: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    source_root = _PROJECT_ROOT / "src"
    existing_python_path = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = (
        str(source_root)
        if not existing_python_path
        else f"{source_root}{os.pathsep}{existing_python_path}"
    )
    return subprocess.run(
        [sys.executable, "-c", import_statement],
        cwd=_PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def test_regularized_v4_fitter_import_is_independent_of_heldout_package_exports() -> None:
    completed = _run_clean_import(
        "from specsafe.traces.regularized_isotonic_calibration_v4 "
        "import RegularizedIsotonicCalibrationV4Artifact"
    )

    assert completed.returncode == 0, completed.stderr


def test_public_heldout_package_export_import_is_cycle_free() -> None:
    completed = _run_clean_import(
        "from specsafe.heldout_calibration "
        "import run_v4_final_heldout_calibration_assessment_once"
    )

    assert completed.returncode == 0, completed.stderr
