from __future__ import annotations

import os

from specsafe.hugging_face_dataset_publication import validate_workflow_environment


def main() -> int:
    gate = validate_workflow_environment(os.environ)
    print(
        "GitHub Actions publication gate passed for "
        f"{gate.namespace}; the credential value was not logged."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
