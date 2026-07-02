"""Build the immutable manifest for quarantined final-evaluation evidence."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces import build_calibration_redesign_final_evaluation_manifest

if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[1]
    fixture_root = (
        repository_root / "data" / "fixtures" / "synthetic_calibration_redesign"
    )
    manifest_path = build_calibration_redesign_final_evaluation_manifest(fixture_root)
    print(f"Wrote final-evaluation manifest: {manifest_path}")
