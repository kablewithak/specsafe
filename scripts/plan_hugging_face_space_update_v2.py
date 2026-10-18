"""Offline, non-publishing, manifest-bound Space V2 update operation preview."""

from __future__ import annotations

import argparse
from pathlib import Path

from specsafe.hugging_face_space_publication_v2.update_plan import (
    build_existing_space_v2_update_plan,
    canonical_update_plan_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check the exact V1-to-V2 Space asset delta without remote mutation."
    )
    parser.add_argument("--check-local", action="store_true", required=True)
    args = parser.parse_args()
    if not args.check_local:
        parser.error("Only the read-only --check-local action is permitted")
    root = Path(__file__).resolve().parents[1]
    plan = build_existing_space_v2_update_plan(root)
    print(canonical_update_plan_json(plan).decode("utf-8"), end="")
    print("V2 EXACT UPDATE OPERATIONS QUALIFIED; PUBLICATION NOT AUTHORIZED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
