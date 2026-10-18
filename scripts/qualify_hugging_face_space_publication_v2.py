from __future__ import annotations

import argparse
import json
from pathlib import Path

from specsafe.hugging_face_space_publication_v2 import (
    build_local_v2_release_readiness,
    preflight_existing_v2_space,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only SpecSafe V2 existing-Space release qualification."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-local", action="store_true")
    action.add_argument("--preflight-remote", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]

    if args.check_local:
        result = build_local_v2_release_readiness(root)
        print(json.dumps(result.model_dump(mode="json"), sort_keys=True, indent=2))
        print("LOCAL V2 RELEASE READY; REMOTE STATE NOT OBSERVED; NO MUTATION")
        return 0

    from specsafe.hugging_face_space_publication_receipt import (
        HuggingFaceAnonymousPublicationGateway,
    )

    gateway = HuggingFaceAnonymousPublicationGateway()
    result = preflight_existing_v2_space(root, gateway)
    print(json.dumps(result.model_dump(mode="json"), sort_keys=True, indent=2))
    print("REMOTE V1 BASELINE PREFLIGHT PASSED; NO MUTATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
