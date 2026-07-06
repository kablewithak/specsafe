"""Build the immutable V3 final-evaluation manifest without assessing it."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces.calibration_redesign_v3_final_manifest import (
    build_calibration_redesign_v3_final_evaluation_manifest,
)

FIXTURE_ROOT = Path("data/fixtures/synthetic_calibration_redesign_v3")


def main() -> None:
    """Build and print the deterministic V3 final-evaluation manifest path."""

    manifest_path = build_calibration_redesign_v3_final_evaluation_manifest(FIXTURE_ROOT)
    print(f"Built V3 final-evaluation manifest: {manifest_path.as_posix()}")


if __name__ == "__main__":
    main()
