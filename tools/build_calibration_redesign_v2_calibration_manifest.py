"""Build the immutable V2 calibration-only manifest from committed local assets."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces.calibration_redesign_v2_manifest import (
    build_calibration_redesign_v2_calibration_manifest,
)

FIXTURE_ROOT = Path("data/fixtures/synthetic_calibration_redesign_v2")


def main() -> None:
    """Build and print the deterministic V2 calibration manifest path."""

    manifest_path = build_calibration_redesign_v2_calibration_manifest(FIXTURE_ROOT)
    print(f"Built V2 calibration manifest: {manifest_path.as_posix()}")


if __name__ == "__main__":
    main()
