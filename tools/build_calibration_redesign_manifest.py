"""Build the immutable fresh calibration fixture manifest from committed local assets."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces import build_calibration_redesign_manifest


FIXTURE_ROOT = Path("data/fixtures/synthetic_calibration_redesign")


def main() -> None:
    """Build and print the deterministic manifest path for the governed fixture set."""

    manifest_path = build_calibration_redesign_manifest(FIXTURE_ROOT)
    print(f"Built fresh calibration manifest: {manifest_path.as_posix()}")


if __name__ == "__main__":
    main()
