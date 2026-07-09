from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

DEFAULT_CORPUS_PATH = Path("data/fixtures/kaggle_trace_corpus_expansion_v1/prompt_corpus.json")
DEFAULT_OUTPUT_PATH = Path(
    "evidence/kaggle-trace-collection/"
    "v5-qwen-governed-trace-collection-v2/"
    "pre-collection/pre_collection_manifest.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the governed pre-collection manifest for Kaggle trace v2."
    )
    parser.add_argument(
        "--corpus-path",
        default=DEFAULT_CORPUS_PATH,
        type=Path,
        help="Path to the planned prompt corpus JSON.",
    )
    parser.add_argument(
        "--output-path",
        default=DEFAULT_OUTPUT_PATH,
        type=Path,
        help="Path where the deterministic pre-collection manifest will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_and_write_precollection_manifest = _load_manifest_writer()
    manifest = build_and_write_precollection_manifest(
        corpus_path=args.corpus_path,
        output_path=args.output_path,
    )
    print(f"wrote {args.output_path}")
    print(f"manifest_id={manifest.manifest_id}")
    print(f"planned_runtime_records={manifest.record_plan.planned_runtime_records}")
    print("calibration_fit_status=not_authorized")
    print("threshold_promotion_status=not_authorized")


def _load_manifest_writer() -> Callable[..., object]:
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if src_path.exists() and str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from specsafe.kaggle_trace_collection.precollection_manifest import (
        build_and_write_precollection_manifest,
    )

    return build_and_write_precollection_manifest


if __name__ == "__main__":
    main()
