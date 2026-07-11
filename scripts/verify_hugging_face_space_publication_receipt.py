from __future__ import annotations

import argparse
import json
from pathlib import Path

from specsafe.hugging_face_space_publication_receipt import (
    HuggingFaceAnonymousPublicationGateway,
    check_committed_reconciliation,
    verify_local_publication_receipt,
    write_remote_reconciliation,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the retained SpecSafe Hugging Face Space publication receipt "
            "and reconcile it anonymously against the published Space."
        )
    )
    parser.add_argument("--project-root", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-local", action="store_true")
    mode.add_argument("--write-remote-reconciliation", action="store_true")
    mode.add_argument("--check-committed", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = Path(args.project_root)

    if args.check_local:
        verified = verify_local_publication_receipt(root)
        print(
            json.dumps(
                {
                    "candidate_tree_sha256": verified.receipt.candidate_tree_sha256,
                    "evidence_index_sha256": verified.receipt.evidence_index_sha256,
                    "publication_id": verified.receipt.publication_id,
                    "published_from_git_sha": verified.receipt.published_from_git_sha,
                    "published_revision": verified.receipt.published_revision,
                    "receipt_byte_count": verified.receipt_byte_count,
                    "receipt_sha256": verified.receipt_sha256,
                    "remote_file_count": verified.receipt.remote_file_count,
                    "schema_version": verified.receipt.schema_version,
                },
                indent=2,
                sort_keys=True,
            )
        )
        print("Local publication receipt verification passed; no network action was performed.")
        return 0

    if args.write_remote_reconciliation:
        gateway = HuggingFaceAnonymousPublicationGateway()
        record = write_remote_reconciliation(root, gateway)
        print(json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True))
        print(
            "Anonymous publication reconciliation passed and was written locally; "
            "no credential was used."
        )
        return 0

    record = check_committed_reconciliation(root)
    print(json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True))
    print("Committed publication receipt and reconciliation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
