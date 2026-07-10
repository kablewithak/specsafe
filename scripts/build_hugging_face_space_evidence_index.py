from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.hugging_face_space_evidence import (
    check_committed_space_evidence_index,
    write_space_evidence_index,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root)
    if args.check:
        check_committed_space_evidence_index(root)
        print("Hugging Face Space evidence index is canonical and UI implementation is pending.")
        return 0

    output = write_space_evidence_index(root)
    print(f"Wrote frozen Hugging Face Space evidence index: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
