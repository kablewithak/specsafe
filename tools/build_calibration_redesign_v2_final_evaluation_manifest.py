"""Build the immutable V2 final-evaluation manifest from committed local assets."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces.calibration_redesign_v2_final_manifest import (
    build_calibration_redesign_v2_final_evaluation_manifest,
)

FIXTURE_ROOT = Path("data/fixtures/synthetic_calibration_redesign_v2")


def main() -> None:
    """Build and print the deterministic V2 final-evaluation manifest path."""

    manifest_path = build_calibration_redesign_v2_final_evaluation_manifest(FIXTURE_ROOT)
    print(f"Built V2 final-evaluation manifest: {manifest_path.as_posix()}")


if __name__ == "__main__":
    main()
