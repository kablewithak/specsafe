from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.publication_authorization import (
    build_publication_authorization_decision,
    check_committed_publication_authorization_decision,
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
        check_committed_publication_authorization_decision(root)
        print("Exact Hugging Face Dataset publication is authorized; no upload was performed.")
        return 0

    decision = build_publication_authorization_decision(root)
    print(f"Wrote exact publication authorization: {decision.decision_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
