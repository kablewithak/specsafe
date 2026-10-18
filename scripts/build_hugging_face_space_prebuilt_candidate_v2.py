from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.hugging_face_space_prebuilt_candidate_v2 import (
    check_committed_prebuilt_candidate_v2,
    write_prebuilt_candidate_v2,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build or verify the locally compiled Hugging Face static-Space "
            "V2 publication candidate."
        )
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--write",
        action="store_true",
        help="Build, validate, and replace the committed V2 prebuilt candidate.",
    )
    action.add_argument(
        "--check",
        action="store_true",
        help="Rebuild and verify the committed V2 prebuilt candidate byte-for-byte.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    project_root = Path(__file__).resolve().parents[1]

    if args.write:
        manifest = write_prebuilt_candidate_v2(project_root)
        print(
            "Hugging Face V2 prebuilt Space candidate written: "
            f"{manifest.exact_candidate_file_count} files, "
            f"tree_sha256={manifest.candidate_tree_sha256}, "
            "provider_side_build_required=false"
        )
        return

    manifest = check_committed_prebuilt_candidate_v2(project_root)
    print(
        "Hugging Face V2 prebuilt Space candidate check passed: "
        f"{manifest.exact_candidate_file_count} files, "
        f"tree_sha256={manifest.candidate_tree_sha256}"
    )


if __name__ == "__main__":
    main()
