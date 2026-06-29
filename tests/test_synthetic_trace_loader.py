from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from specsafe.contracts import TraceFixtureViolationCode, TraceSplit
from specsafe.traces import SyntheticTraceFixtureLoadError, load_synthetic_trace_fixture_set

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_trace_baselines"
)


def test_loader_returns_hash_verified_structurally_separated_fixture_set() -> None:
    fixture_set = load_synthetic_trace_fixture_set(FIXTURE_ROOT)

    assert fixture_set.manifest.fixture_set_id == "synthetic-trace-baselines-v1"
    assert fixture_set.manifest.case_count == 6
    assert {case.runtime_input.split for case in fixture_set.cases} == {
        TraceSplit.DEVELOPMENT,
        TraceSplit.CALIBRATION,
        TraceSplit.ADVERSARIAL_REGRESSION,
        TraceSplit.FINAL_EVALUATION,
    }
    assert all(
        not hasattr(case.runtime_input.contexts[0], "observed_acceptance")
        for case in fixture_set.cases
    )


def test_loader_rejects_artifact_bytes_that_do_not_match_manifest(tmp_path: Path) -> None:
    copied_root = tmp_path / "synthetic_trace_baselines"
    shutil.copytree(FIXTURE_ROOT, copied_root)

    runtime_path = copied_root / "inputs" / "STF-001-high-confidence-light.json"
    payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    payload["generation_note"] = "Tampered after manifest generation."
    runtime_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(SyntheticTraceFixtureLoadError) as error:
        load_synthetic_trace_fixture_set(copied_root)

    assert error.value.code is TraceFixtureViolationCode.TRACE_MANIFEST_MISMATCH


def test_loader_rejects_provenance_mismatch_even_when_manifest_hash_is_updated(
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "synthetic_trace_baselines"
    shutil.copytree(FIXTURE_ROOT, copied_root)

    runtime_path = copied_root / "inputs" / "STF-002-low-confidence-saturated.json"
    payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    payload["case_id"] = "STF-999"
    runtime_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    manifest_path = copied_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_bytes = runtime_path.read_bytes()
    for entry in manifest["entries"]:
        if entry["relative_path"] == "inputs/STF-002-low-confidence-saturated.json":
            entry["sha256"] = hashlib.sha256(raw_bytes).hexdigest()
            entry["byte_count"] = len(raw_bytes)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(SyntheticTraceFixtureLoadError) as error:
        load_synthetic_trace_fixture_set(copied_root)

    assert error.value.code is TraceFixtureViolationCode.TRACE_PROVENANCE_MISMATCH
