# SpecSafe V5 Qwen Negative-Case Expansion V1 — Private Kaggle Run README

This README is the notebook-side run guide for the third governed Kaggle trace collection:

- Collection ID: `v5-qwen-negative-case-expansion-v1`
- Attempt ID: `attempt-001-t4`
- Purpose: increase nonmatch/negative observations after the v2 calibration diagnostic blocked fitting on negative-count grounds.
- Planned prompts: `16`
- Candidate positions per prompt: `4`
- Planned runtime records: `64`
- Minimum additional negatives needed: `7`

## Hard boundary

This run is private evidence acquisition only.

Do not use this bundle to:

- fit a Kaggle-derived calibrator
- tune or promote thresholds
- promote scheduler utility
- publish public artifacts
- claim production speedup, latency, throughput, cost savings, or production readiness

## Required Kaggle settings

Use a private Kaggle notebook with:

- Accelerator: GPU T4 x2 is acceptable
- Internet: enabled, only for public Hugging Face model download if models are not already cached
- Dataset: upload the generated private input ZIP as a private dataset
- Dataset title recommendation: `specsafe-qwen-negcase-v1-t4-input`

## Minimal input discovery cell

```python
from pathlib import Path

commit_files = list(Path("/kaggle/input").rglob("RUN_SOURCE_COMMIT.txt"))
assert commit_files, "RUN_SOURCE_COMMIT.txt not found under /kaggle/input"
INPUT_ROOT = commit_files[0].parent
print("INPUT_ROOT=", INPUT_ROOT)
print("source_commit=", (INPUT_ROOT / "RUN_SOURCE_COMMIT.txt").read_text().strip())
for path in sorted(INPUT_ROOT.rglob("*")):
    if path.is_file():
        print(path.relative_to(INPUT_ROOT))
```

## Minimal readiness validation cell

```python
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

input_manifest = json.loads((INPUT_ROOT / "UPLOAD_BUNDLE_INPUT_MANIFEST.json").read_text())
for item in input_manifest["included_files"]:
    path = INPUT_ROOT / item["path"]
    assert path.exists(), item["path"]
    assert sha256_file(path) == item["sha256"], item["path"]

readiness_path = INPUT_ROOT / (
    "evidence/kaggle-trace-collection/v5-qwen-negative-case-expansion-v1/"
    "readiness/collection_readiness_bundle.json"
)
readiness = json.loads(readiness_path.read_text())
assert readiness["readiness_status"] == "ready_for_private_kaggle_t4_collection"
assert readiness["calibration_fit_status"] == "not_authorized"
print("readiness validation: PASS")
```

## Collection expectation

The collection notebook should emit a private archive under `/kaggle/working` containing:

- `runtime_records.jsonl`
- `expected_outcome_records.jsonl`
- `timing_records.jsonl`
- `trace_summary.json`
- `environment_report.json`
- `retention_manifest.json`

Keep the archive private until a repo retention PR validates it.
