from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.hugging_face_space_publication_candidate_v2 import (
    check_committed_candidate_v2,
    write_candidate_v2,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Build or verify the isolated V2 Hugging Face Space source candidate.")
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--write",
        action="store_true",
        help="Write the V2 candidate and manifest in the V2 namespace.",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="Verify the committed V2 candidate and manifest byte-for-byte.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    project_root = Path(__file__).resolve().parents[1]

    if args.write:
        manifest = write_candidate_v2(project_root)
        print(
            "Hugging Face Space V2 source candidate written: "
            f"{manifest.exact_candidate_file_count} files, "
            f"tree_sha256={manifest.candidate_tree_sha256}, "
            f"source_commit={manifest.source_commit}"
        )
        return

    check_committed_candidate_v2(project_root)
    print("Hugging Face Space V2 source candidate check passed.")


if __name__ == "__main__":
    main()
