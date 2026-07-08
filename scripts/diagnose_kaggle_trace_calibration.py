"""CLI for retained Kaggle trace calibration diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.kaggle_trace_calibration import (
    build_trace_calibration_diagnostic_report,
    write_trace_calibration_diagnostic_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a diagnostic calibration report for a retained Kaggle trace archive."
    )
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--trace-analysis-report", required=True, type=Path)
    parser.add_argument("--trace-replay-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_trace_calibration_diagnostic_report(
        archive_path=args.archive,
        trace_analysis_report_path=args.trace_analysis_report,
        trace_replay_report_path=args.trace_replay_report,
    )
    write_trace_calibration_diagnostic_report(report, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
