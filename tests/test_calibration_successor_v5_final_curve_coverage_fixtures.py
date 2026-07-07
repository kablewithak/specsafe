"""Coverage and quarantine tests for the first V5 held-out curve-coverage family."""

from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from specsafe.traces.bounded_monotone_beta_calibration_v5 import (
    load_v5_bounded_monotone_beta_calibration_fit,
)
from specsafe.traces.calibration_successor_v5_final_cases import (
    CalibrationSuccessorV5FinalCaseContractError,
    CalibrationSuccessorV5FinalCaseViolationCode,
    load_calibration_successor_v5_final_curve_coverage_replay_case,
    summarize_final_curve_coverage_workloads,
)
from specsafe.traces.calibration_successor_v5_manifest import (
    load_calibration_successor_v5_calibration_manifest,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(201, 210))


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_final_curve_coverage_loads_exactly_nine_quarantined_heldout_case_pairs() -> None:
    replay_cases = tuple(
        load_calibration_successor_v5_final_curve_coverage_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _CASE_IDS
    )

    assert tuple(case.runtime_input.case_id for case in replay_cases) == _CASE_IDS
    assert all(case.runtime_input.split.value == "final_evaluation" for case in replay_cases)
    assert all(case.runtime_input.data_role.value == "held_out_evaluation" for case in replay_cases)
    assert all(
        case.runtime_input.scenario_family_id == "CSV5-FINAL-CURVE-COVERAGE"
        for case in replay_cases
    )
    assert all(len(case.runtime_input.contexts) == 4 for case in replay_cases)
    assert all(len(case.expected_outcomes.outcomes) == 4 for case in replay_cases)


def test_final_curve_coverage_spans_confidence_deciles_workloads_positions_and_outcome_mix() -> (
    None
):
    replay_cases = tuple(
        load_calibration_successor_v5_final_curve_coverage_replay_case(_FIXTURE_ROOT, case_id)
        for case_id in _CASE_IDS
    )
    confidences = [
        context.conditional_survival_confidence
        for case in replay_cases
        for context in case.runtime_input.contexts
    ]
    workloads = Counter(
        context.workload_type.value
        for case in replay_cases
        for context in case.runtime_input.contexts
    )
    positions = Counter(
        context.block_position_index
        for case in replay_cases
        for context in case.runtime_input.contexts
    )
    outcomes_by_workload: dict[str, list[bool]] = defaultdict(list)
    for case in replay_cases:
        workload = case.runtime_input.contexts[0].workload_type.value
        outcomes_by_workload[workload].extend(
            outcome.observed_acceptance for outcome in case.expected_outcomes.outcomes
        )

    assert len(confidences) == 36
    assert {min(int(confidence * 10), 9) for confidence in confidences} == set(range(10))
    assert workloads == {"structured_text": 12, "code": 12, "open_ended_chat": 12}
    assert positions == Counter({1: 9, 2: 9, 3: 9, 4: 9})
    assert summarize_final_curve_coverage_workloads(replay_cases) == {
        "code": 3,
        "open_ended_chat": 3,
        "structured_text": 3,
    }
    assert all(any(values) and not all(values) for values in outcomes_by_workload.values())


def test_final_runtime_assets_exclude_posthoc_labels_and_tokens() -> None:
    runtime_payload = json.loads(
        (_FIXTURE_ROOT / "final_evaluation" / "inputs" / "cases" / "CSV5-203.json").read_text(
            encoding="utf-8"
        )
    )
    rendered = json.dumps(runtime_payload, sort_keys=True)

    assert "candidate_token_id" not in rendered
    assert "observed_acceptance" not in rendered
    assert "prefix_survival_label" not in rendered
    assert runtime_payload["contexts"][0]["visible_prefix_token_ids"] == []
    assert runtime_payload["contexts"][3]["visible_prefix_token_ids"]


def test_final_curve_loader_rejects_future_case_reservation() -> None:
    with pytest.raises(CalibrationSuccessorV5FinalCaseContractError) as error:
        load_calibration_successor_v5_final_curve_coverage_replay_case(_FIXTURE_ROOT, "CSV5-210")

    assert error.value.code is CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR


def test_final_curve_outcome_runtime_misalignment_is_rejected(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    outcome_path = root / "final_evaluation" / "expected_outcomes" / "cases" / "CSV5-205.json"
    payload = json.loads(outcome_path.read_text(encoding="utf-8"))
    payload["fixture_id"] = "misaligned-final-fixture"
    outcome_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationSuccessorV5FinalCaseContractError) as error:
        load_calibration_successor_v5_final_curve_coverage_replay_case(root, "CSV5-205")

    assert error.value.code is CalibrationSuccessorV5FinalCaseViolationCode.CASE_ALIGNMENT_ERROR


def test_final_assets_do_not_change_frozen_calibration_manifest_or_fit_provenance() -> None:
    manifest = load_calibration_successor_v5_calibration_manifest(_FIXTURE_ROOT)
    retained_fit = load_v5_bounded_monotone_beta_calibration_fit(_FIXTURE_ROOT)

    assert manifest.case_ids == tuple(f"CSV5-{number:03d}" for number in range(101, 149))
    assert (
        manifest.aggregate_sha256
        == "c84085828e04176fef31ed02466697650dbb7723afa065b2561227125ba5a795"
    )
    assert all(not asset.relative_path.startswith("final_evaluation/") for asset in manifest.assets)
    assert retained_fit.artifact.calibration_manifest.aggregate_sha256 == manifest.aggregate_sha256
    assert retained_fit.diagnostics.final_evaluation_accessed is False
    assert (_FIXTURE_ROOT / "final_evaluation_manifest.json").is_file()
    assert (_FIXTURE_ROOT / "final_evidence_index.json").is_file()
    assert not (_FIXTURE_ROOT / "final_assessment_result.json").exists()
