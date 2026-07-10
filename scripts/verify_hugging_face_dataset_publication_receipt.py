from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.hugging_face_dataset_publication import (
    check_committed_publication_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not args.check:
        parser.error("only --check is supported for the retained publication receipt")

    receipt = check_committed_publication_receipt(Path(args.project_root))
    print(f"Verified public Hugging Face Dataset: {receipt.repository_id}")
    print(f"Verified published revision: {receipt.published_revision}")
    print("Publication receipt is canonical and no credential is retained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
