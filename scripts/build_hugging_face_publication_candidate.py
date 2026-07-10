from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.hugging_face_publication_candidate import (
    check_committed_publication_candidate,
    write_publication_candidate,
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
        check_committed_publication_candidate(root)
        print("Hugging Face publication candidate is canonical and upload remains unauthorized.")
        return 0

    output = write_publication_candidate(root)
    print(f"Wrote local Hugging Face publication candidate: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
