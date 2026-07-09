"""Prepare the private Kaggle input bundle for negative-case expansion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from specsafe.kaggle_trace_collection.negative_case_kaggle_upload_bundle import (
    build_private_kaggle_input_bundle,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the private Kaggle input ZIP for negative-case expansion."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--source-commit",
        default=None,
        help="Optional explicit source commit. Defaults to git rev-parse HEAD.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=("Optional output directory. Defaults to the repo evidence/kaggle-input path."),
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    manifest = build_private_kaggle_input_bundle(
        repo_root=Path(args.repo_root),
        output_dir=output_dir,
        source_commit=args.source_commit,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
