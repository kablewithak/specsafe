from __future__ import annotations

from pathlib import Path

from specsafe.kaggle_trace_collection.negative_case_precollection_bundle import (
    write_negative_case_precollection_bundle,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path, readiness_path = write_negative_case_precollection_bundle(repo_root)
    print(f"Wrote {manifest_path}")
    print(f"Wrote {readiness_path}")


if __name__ == "__main__":
    main()
