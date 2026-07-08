"""Generate a local diagnostics report for a retained Kaggle trace archive."""

from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.kaggle_trace_analysis import write_trace_analysis_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a retained SpecSafe Kaggle trace archive.",
    )
    parser.add_argument(
        "--archive",
        required=True,
        type=Path,
        help="Path to the retained Kaggle trace archive ZIP.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path where the analysis report JSON should be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = write_trace_analysis_report(args.archive, args.output)
    print(
        "wrote trace analysis report "
        f"collection_id={report.collection_id} "
        f"attempt={report.collection_attempt_id} "
        f"records={report.runtime_record_count} "
        f"match_rate={report.target_argmax_match_rate:.6f}",
    )


if __name__ == "__main__":
    main()
