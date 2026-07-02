"""Assess the frozen temperature artifact against quarantined final-evaluation evidence."""

from __future__ import annotations

from pathlib import Path

from specsafe.traces import write_logit_temperature_scaling_heldout_assessment

FIXTURE_ROOT = Path("data/fixtures/synthetic_calibration_redesign")
ARTIFACT_PATH = Path("evidence/calibration/logit-temperature-scaling-v1/artifact.json")
OUTPUT_PATH = Path(
    "evidence/calibration/logit-temperature-scaling-v1/heldout_assessment.json"
)


if __name__ == "__main__":
    result = write_logit_temperature_scaling_heldout_assessment(
        fixture_root=FIXTURE_ROOT,
        artifact_path=ARTIFACT_PATH,
        output_path=OUTPUT_PATH,
    )
    print(f"Wrote held-out assessment: {OUTPUT_PATH}")
    print(f"Status: {result.status.value}")
    print(f"Promotion decision: {result.promotion_decision.value}")
