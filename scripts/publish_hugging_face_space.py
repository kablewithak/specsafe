from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from specsafe.hugging_face_space_publication import (
    HuggingFaceSpaceHubGateway,
    build_publication_plan,
    preflight_remote_publication,
    publish_authorized_space,
    read_publication_git_state,
    validate_publication_git_state,
)

EXPECTED_CONFIRMATION = "PUBLISH_EXACT_SPACE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-local", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("--namespace")
    parser.add_argument("--confirmation")
    parser.add_argument("--receipt-path")
    parser.add_argument("--application-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    root = Path(args.project_root)
    if args.check_local:
        plan = build_publication_plan(root)
        print(json.dumps(plan.model_dump(mode="json"), indent=2, sort_keys=True))
        print("Local Space publication plan is canonical; no network action was performed.")
        return 0

    if not args.namespace:
        parser.error("--namespace is required for --preflight and --publish")

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        parser.error("HF_TOKEN must be set in the current process environment")
    gateway = HuggingFaceSpaceHubGateway(token=token)

    if args.preflight:
        repo_id = preflight_remote_publication(root, args.namespace, gateway)
        print(f"Remote preflight passed for new Space repository: {repo_id}")
        print("No remote repository was created or modified.")
        return 0

    if args.confirmation != EXPECTED_CONFIRMATION:
        parser.error(f"--confirmation must be exactly {EXPECTED_CONFIRMATION}")
    git_state = validate_publication_git_state(read_publication_git_state(root))
    receipt = publish_authorized_space(
        root,
        args.namespace,
        gateway,
        published_from_git_sha=git_state.head_sha,
        receipt_path=args.receipt_path,
        application_timeout_seconds=args.application_timeout_seconds,
    )
    print(f"Published and verified Space: {receipt.repository_id}")
    print(f"Published revision: {receipt.published_revision}")
    print(f"Public application: {receipt.application_url}")
    print("A sanitized publication receipt was written locally. No credential was logged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
