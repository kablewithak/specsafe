"""Run offline, in-memory failure-injection cases for the existing V2 Space update."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from specsafe.hugging_face_space_publication_v2.executor_simulation import (
    FailureScenario,
    SimulationOutcome,
    simulate_existing_v2_update,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=[scenario.value for scenario in FailureScenario],
        default=FailureScenario.HAPPY_PATH.value,
    )
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    report = simulate_existing_v2_update(
        project_root,
        scenario=FailureScenario(args.scenario),
    )
    print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    if report.outcome is SimulationOutcome.VERIFIED_V2:
        print("SIMULATED V2 UPDATE VERIFIED; NO LIVE PUBLICATION")
    elif report.outcome is SimulationOutcome.VERIFIED_V1_ROLLBACK:
        print("SIMULATED V1 ROLLBACK VERIFIED; NO LIVE PUBLICATION")
    else:
        print("SIMULATED EXECUTION BLOCKED OR UNCERTAIN; NO LIVE PUBLICATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
