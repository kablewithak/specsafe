"""Freeze the complete V4 calibration corpus exactly once.

This command is intentionally narrow. It performs the governed metadata transition from
completed calibration authoring to calibration-manifest freeze, then writes and verifies the
immutable manifest. It does not fit calibration or execute scheduler, policy, or replay code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from specsafe.traces.calibration_redesign_v4_manifest import (
    CalibrationRedesignV4ManifestError,
    load_calibration_redesign_v4_calibration_manifest,
    write_calibration_redesign_v4_calibration_manifest,
)

_EXPECTED_PRE_FREEZE_STATUS = "calibration_capacity_contrast_authored"
_EXPECTED_PRE_FREEZE_ARTIFACT = "v4-calibration-manifest-freeze"
_FROZEN_STATUS = "calibration_manifest_frozen"
_NEXT_ARTIFACT = "v4-calibration-fit-and-diagnostics"
_MANIFEST_FILENAME = "calibration_manifest.json"

_FROZEN_EXCLUSIONS = [
    "No V4 final-evaluation runtime-input case assets are present.",
    "No V4 final-evaluation expected-outcome assets or labels are present.",
    "No V4 adversarial-regression runtime-input or expected-outcome assets are present.",
    "No V4 final-evaluation manifest is present.",
    "No V4 calibration artifact or fit report is present.",
    "No V4 final-evidence index or held-out result is present.",
    "No V4 calibrator fitting has been performed.",
    "No V4 scheduler, baseline, capacity, or replay implementation is authorized.",
    "No closed-programme data-bearing evidence influenced V4 case design.",
    "No V4 performance, calibration, policy, or runtime claim is made.",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze the immutable V4 calibration manifest exactly once."
    )
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=Path("data/fixtures/synthetic_calibration_redesign_v4"),
        help="Path to the V4 synthetic calibration fixture root.",
    )
    arguments = parser.parse_args()
    fixture_root = arguments.fixture_root.resolve()
    registry_path = fixture_root / "scenario_family_registry.json"
    manifest_path = fixture_root / _MANIFEST_FILENAME

    if manifest_path.exists():
        raise SystemExit(
            "Stop: calibration_manifest.json already exists. "
            "This freeze command will not overwrite it."
        )
    try:
        original_registry_bytes = registry_path.read_bytes()
        registry_payload = json.loads(original_registry_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SystemExit(
            f"Stop: unable to read current V4 registry: {error}"
        ) from error

    _assert_pre_freeze_registry(registry_payload)
    frozen_registry_bytes = _frozen_registry_bytes(registry_payload)
    try:
        registry_path.write_bytes(frozen_registry_bytes)
        manifest = write_calibration_redesign_v4_calibration_manifest(fixture_root)
        verified_manifest = load_calibration_redesign_v4_calibration_manifest(
            fixture_root
        )
    except (CalibrationRedesignV4ManifestError, OSError) as error:
        if manifest_path.exists():
            manifest_path.unlink()
        registry_path.write_bytes(original_registry_bytes)
        raise SystemExit(
            f"Stop: V4 calibration manifest freeze failed: {error}"
        ) from error

    if verified_manifest != manifest:
        manifest_path.unlink()
        registry_path.write_bytes(original_registry_bytes)
        raise SystemExit(
            "Stop: generated V4 calibration manifest did not verify exactly."
        )

    print("V4 calibration manifest freeze: PASS")
    print(f"Manifest: {manifest_path.as_posix()}")
    print(f"Case pairs: {manifest.case_pair_count}")
    print(f"Assets: {manifest.asset_count}")
    print(f"Aggregate bytes: {manifest.aggregate_byte_count}")
    print(f"Aggregate SHA-256: {manifest.aggregate_sha256}")
    return 0


def _assert_pre_freeze_registry(payload: object) -> None:
    if not isinstance(payload, dict):
        raise SystemExit("Stop: V4 registry must be a JSON object.")
    if payload.get("registry_status") != _EXPECTED_PRE_FREEZE_STATUS:
        raise SystemExit("Stop: V4 registry is not at completed calibration authoring.")
    if payload.get("v4_manifests_authored") is not False:
        raise SystemExit(
            "Stop: V4 registry does not have the expected pre-freeze manifest state."
        )
    if payload.get("next_authorized_artifact") != _EXPECTED_PRE_FREEZE_ARTIFACT:
        raise SystemExit(
            "Stop: V4 registry does not authorize calibration-manifest freeze."
        )


def _frozen_registry_bytes(payload: dict[str, object]) -> bytes:
    payload["registry_status"] = _FROZEN_STATUS
    payload["v4_manifests_authored"] = True
    payload["next_authorized_artifact"] = _NEXT_ARTIFACT
    payload["explicit_exclusions"] = _FROZEN_EXCLUSIONS
    return (
        json.dumps(
            payload,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
