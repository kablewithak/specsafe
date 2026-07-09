from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from specsafe.kaggle_trace_collection.collection_readiness_bundle import (  # noqa: E402
    READINESS_BUNDLE_PATH,
    write_readiness_bundle,
)


def main() -> int:
    bundle = write_readiness_bundle(REPO_ROOT)
    output_path = REPO_ROOT / READINESS_BUNDLE_PATH
    print(f"wrote={output_path.as_posix()}")
    print(f"readiness_bundle_id={bundle.readiness_bundle_id}")
    print(f"planned_runtime_records={bundle.planned_runtime_records}")
    print(f"model_execution_status={bundle.model_execution_status}")
    print(f"calibration_fit_status={bundle.calibration_fit_status}")
    print(f"threshold_promotion_status={bundle.threshold_promotion_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
