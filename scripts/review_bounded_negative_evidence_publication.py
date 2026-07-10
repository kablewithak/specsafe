from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.publication_readiness import (
    check_committed_publication_readiness_decision,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not args.check:
        parser.error(
            "only --check is supported; the reviewed decision is governed in source control"
        )

    check_committed_publication_readiness_decision(Path(args.project_root))
    print("Bounded negative-evidence publication-readiness decision is canonical.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
