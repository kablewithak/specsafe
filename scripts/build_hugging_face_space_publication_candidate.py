from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.hugging_face_space_publication_candidate import (
    check_committed_candidate,
    write_candidate,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build or verify the exact standalone Hugging Face Space "
            "publication candidate."
        )
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--write",
        action="store_true",
        help="Replace the committed candidate and manifest.",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="Verify the committed candidate and manifest byte-for-byte.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    project_root = Path(__file__).resolve().parents[1]

    if args.write:
        manifest = write_candidate(project_root)
        print(
            "Hugging Face Space publication candidate written: "
            f"{manifest.exact_candidate_file_count} files, "
            f"tree_sha256={manifest.candidate_tree_sha256}"
        )
        return

    check_committed_candidate(project_root)
    print("Hugging Face Space publication candidate check passed.")


if __name__ == "__main__":
    main()
