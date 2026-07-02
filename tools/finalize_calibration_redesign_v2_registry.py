"""Finalize the reviewed V2 registry proposal into a hash-linked registry."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces.calibration_redesign_v2 import (
    build_calibration_redesign_v2_scenario_family_registry,
)

FIXTURE_ROOT = Path("data/fixtures/synthetic_calibration_redesign_v2")


def main() -> None:
    """Build only the final registry; no runtime or outcome fixture is created."""

    registry_path = build_calibration_redesign_v2_scenario_family_registry(FIXTURE_ROOT)
    print(f"Finalized V2 registry: {registry_path}")


if __name__ == "__main__":
    main()
