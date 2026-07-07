"""Regression coverage for controlled synthetic reporting and Phase 5 gating."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsafe.reporting.controlled_synthetic_comparison import (
    CONTROLLED_SYNTHETIC_COMPARISON_REPORT_RELATIVE_PATH,
    CONTROLLED_SYNTHETIC_PHASE5_GATE_RELATIVE_PATH,
    ControlledSyntheticComparisonReportError,
    ControlledSyntheticComparisonReportErrorCode,
    build_controlled_synthetic_phase5_gate,
    canonical_controlled_synthetic_phase5_gate_json,
    check_committed_controlled_synthetic_comparison_report,
    default_controlled_synthetic_comparison_report_path,
    default_controlled_synthetic_phase5_gate_path,
    render_controlled_synthetic_comparison_report,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_RESULT_PATH = (
    _PROJECT_ROOT
    / "evidence"
    / "matched-policy-comparison"
    / "v5-controlled-synthetic-comparison-v1"
    / "result.json"
)


def test_phase5_gate_is_bounded_and_authorizes_kaggle_only() -> None:
    gate = build_controlled_synthetic_phase5_gate(_PROJECT_ROOT)

    assert gate.validity_marker == "VALID_COMPARISON"
    assert gate.evidence_class == "synthetic_controlled"
    assert gate.evidence_maturity_label == "synthetic_fixture_validated"
    assert gate.phase5_gate_status == "passes_controlled_synthetic_phase5_gate"
    assert gate.case_count == 6
    assert gate.valid_matched_comparison_count == 6
    assert gate.unsafe_control_exclusion_count == 6
    assert gate.kaggle_experiment_authorized is True
    assert gate.public_replay_release_authorized is False
    assert gate.runtime_control_eligible is False
    assert gate.promotion_eligible is False
    assert gate.result_reexecution_performed is False


def test_committed_phase5_gate_and_markdown_report_are_canonical() -> None:
    gate = build_controlled_synthetic_phase5_gate(_PROJECT_ROOT)

    assert default_controlled_synthetic_phase5_gate_path(_PROJECT_ROOT) == (
        _PROJECT_ROOT / CONTROLLED_SYNTHETIC_PHASE5_GATE_RELATIVE_PATH
    )
    assert default_controlled_synthetic_comparison_report_path(_PROJECT_ROOT) == (
        _PROJECT_ROOT / CONTROLLED_SYNTHETIC_COMPARISON_REPORT_RELATIVE_PATH
    )
    assert default_controlled_synthetic_phase5_gate_path(_PROJECT_ROOT).read_text(
        encoding="utf-8"
    ) == canonical_controlled_synthetic_phase5_gate_json(gate)
    assert default_controlled_synthetic_comparison_report_path(_PROJECT_ROOT).read_text(
        encoding="utf-8"
    ) == render_controlled_synthetic_comparison_report(_PROJECT_ROOT)
    check_committed_controlled_synthetic_comparison_report(_PROJECT_ROOT)


def test_report_preserves_mixed_outcomes_and_unsafe_exclusion() -> None:
    report = render_controlled_synthetic_comparison_report(_PROJECT_ROOT)

    assert "VALID_COMPARISON" in report
    assert "Adaptive lower utility" in report
    assert "MPC5-103" in report
    assert "MPC5-104" in report
    assert "MPC5-105" in report
    assert "causal_safety_status=fail" in report
    assert "kaggle_experiment_authorized=true" in report
    assert "public_replay_release_authorized=false" in report
    assert "No global policy winner is established." in report


def test_phase5_gate_rejects_retained_result_hash_drift(tmp_path: Path) -> None:
    copied_root = tmp_path / "specsafe"
    copied_root.mkdir()
    (copied_root / "pyproject.toml").write_text("[project]\nname='specsafe'\n", encoding="utf-8")
    result_path = copied_root / _RESULT_PATH.relative_to(_PROJECT_ROOT)
    result_path.parent.mkdir(parents=True)
    payload = json.loads(_RESULT_PATH.read_text(encoding="utf-8"))
    payload["run_id"] = "tampered-run"
    result_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ControlledSyntheticComparisonReportError) as error_info:
        build_controlled_synthetic_phase5_gate(copied_root)

    assert (
        error_info.value.code
        is ControlledSyntheticComparisonReportErrorCode.RESULT_PROVENANCE_MISMATCH
    )
