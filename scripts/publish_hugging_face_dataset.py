from __future__ import annotations

import argparse
import json
from pathlib import Path

from specsafe.hugging_face_dataset_publication import (
    HuggingFaceHubGateway,
    build_publication_plan,
    preflight_remote_publication,
    publish_authorized_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-local", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("--namespace")
    parser.add_argument("--receipt-path")
    args = parser.parse_args()

    root = Path(args.project_root)
    if args.check_local:
        plan = build_publication_plan(root)
        print(json.dumps(plan.model_dump(mode="json"), indent=2, sort_keys=True))
        print("Local Dataset publication plan is canonical; no network action was performed.")
        return 0

    if not args.namespace:
        parser.error("--namespace is required for --preflight and --publish")

    gateway = HuggingFaceHubGateway()
    if args.preflight:
        repo_id = preflight_remote_publication(root, args.namespace, gateway)
        print(f"Remote preflight passed for new Dataset repository: {repo_id}")
        print("No remote repository was created or modified.")
        return 0

    receipt = publish_authorized_dataset(
        root,
        args.namespace,
        gateway,
        receipt_path=args.receipt_path,
    )
    print(f"Published and verified Dataset: {receipt.repository_id}")
    print(f"Published revision: {receipt.published_revision}")
    print("A sanitized publication receipt was written locally. No credential was logged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
