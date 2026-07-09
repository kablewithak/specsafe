from __future__ import annotations

from pathlib import Path

from specsafe.kaggle_trace_calibration.expanded_archive_diagnostics import (
    build_calibration_diagnostic_report,
    write_json_lf,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
REPORT_PATH = ATTEMPT_DIR / "trace_calibration_diagnostic_report.json"


def main() -> None:
    report = build_calibration_diagnostic_report(ATTEMPT_DIR)
    write_json_lf(REPORT_PATH, report)
    print(f"wrote {REPORT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
