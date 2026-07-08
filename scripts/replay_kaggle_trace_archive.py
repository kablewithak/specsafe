"""Regenerate the retained Kaggle trace replay report."""

from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.kaggle_trace_replay import build_trace_replay_report, write_trace_replay_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay threshold diagnostics over a retained Kaggle trace archive."
    )
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--trace-analysis-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_trace_replay_report(
        archive_path=args.archive,
        trace_analysis_report_path=args.trace_analysis_report,
    )
    write_trace_replay_report(report, args.output)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
