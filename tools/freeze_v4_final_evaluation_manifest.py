"""Freeze V4 final-evaluation provenance without scoring held-out evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path

from specsafe.traces.calibration_redesign_v4_final_manifest import (
    freeze_calibration_redesign_v4_final_evaluation_manifest,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "data" / "fixtures" / "synthetic_calibration_redesign_v4"
)


def main() -> None:
    """Create the write-once final manifest and evidence index for the local fixture root."""

    manifest, index = freeze_calibration_redesign_v4_final_evaluation_manifest(_FIXTURE_ROOT)
    manifest_path = _FIXTURE_ROOT / "final_evaluation_manifest.json"
    index_path = _FIXTURE_ROOT / "final_evidence_index.json"

    print("V4 final-evaluation manifest freeze: PASS")
    print(f"Case pairs: {manifest.case_pair_count}")
    print(f"Assets: {manifest.asset_count}")
    print(f"Final observations: {manifest.observation_count}")
    print(f"Final aggregate bytes: {manifest.aggregate_byte_count}")
    print(f"Final aggregate SHA-256: {manifest.aggregate_sha256}")
    print(f"Final manifest SHA-256: {hashlib.sha256(manifest_path.read_bytes()).hexdigest()}")
    print(f"Final evidence index SHA-256: {hashlib.sha256(index_path.read_bytes()).hexdigest()}")
    print(f"Index aggregate SHA-256: {index.aggregate_sha256}")


if __name__ == "__main__":
    main()
