from __future__ import annotations

from pathlib import Path

from specsafe.kaggle_trace_analysis.expanded_archive_analysis import (
    build_trace_analysis_report,
    write_json_lf,
)

ATTEMPT_DIR = (
    Path("evidence")
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
REPORT_PATH = ATTEMPT_DIR / "trace_analysis_report.json"


def main() -> None:
    report = build_trace_analysis_report(ATTEMPT_DIR)
    write_json_lf(REPORT_PATH, report)
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
