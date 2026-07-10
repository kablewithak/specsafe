from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.bounded_negative_evidence import (
    check_committed_release_pack,
    write_release_pack,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    if args.check:
        check_committed_release_pack(project_root)
        print("Bounded negative-evidence release pack is canonical.")
        return 0

    output = write_release_pack(project_root)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
