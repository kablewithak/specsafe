"""Coverage and quarantine tests for the final V5 held-out mixed-reliability family."""

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
    load_calibration_successor_v5_final_mixed_reliability_contrast_replay_case,
    summarize_final_mixed_reliability_contrast_workloads,
)
from specsafe.traces.calibration_successor_v5_manifest import (
    load_calibration_successor_v5_calibration_manifest,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
_CASE_IDS = tuple(f"CSV5-{number:03d}" for number in range(228, 237))


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def test_final_mixed_reliability_loads_exactly_nine_quarantined_heldout_case_pairs() -> None:
    replay_cases = tuple(
        load_calibration_successor_v5_final_mixed_reliability_contrast_replay_case(
            _FIXTURE_ROOT, case_id
        )
        for case_id in _CASE_IDS
    )

    assert tuple(case.runtime_input.case_id for case in replay_cases) == _CASE_IDS
    assert all(case.runtime_input.split.value == "final_evaluation" for case in replay_cases)
    assert all(case.runtime_input.data_role.value == "held_out_evaluation" for case in replay_cases)
    assert all(
        case.runtime_input.scenario_family_id == "CSV5-FINAL-MIXED-RELIABILITY-CONTRAST"
        for case in replay_cases
    )
    assert all(len(case.runtime_input.contexts) == 4 for case in replay_cases)
    assert all(len(case.expected_outcomes.outcomes) == 4 for case in replay_cases)


def test_final_mixed_reliability_exposes_over_and_under_confidence_contrast() -> None:
    replay_cases = tuple(
        load_calibration_successor_v5_final_mixed_reliability_contrast_replay_case(
            _FIXTURE_ROOT, case_id
        )
        for case_id in _CASE_IDS
    )
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
    high_confidence_acceptance: list[bool] = []
    lower_confidence_acceptance: list[bool] = []
    for case in replay_cases:
        confidences = [
            context.conditional_survival_confidence for context in case.runtime_input.contexts
        ]
        acceptances = [outcome.observed_acceptance for outcome in case.expected_outcomes.outcomes]
        workload = case.runtime_input.contexts[0].workload_type.value
        outcomes_by_workload[workload].extend(acceptances)
        if sum(confidences) / len(confidences) >= 0.70:
            high_confidence_acceptance.extend(acceptances)
        else:
            lower_confidence_acceptance.extend(acceptances)

    assert workloads == {"structured_text": 12, "code": 12, "open_ended_chat": 12}
    assert positions == Counter({1: 9, 2: 9, 3: 9, 4: 9})
    assert summarize_final_mixed_reliability_contrast_workloads(replay_cases) == {
        "code": 3,
        "open_ended_chat": 3,
        "structured_text": 3,
    }
    assert all(any(values) and not all(values) for values in outcomes_by_workload.values())
    assert sum(high_confidence_acceptance) / len(high_confidence_acceptance) < 0.35
    assert sum(lower_confidence_acceptance) / len(lower_confidence_acceptance) > 0.65


def test_final_mixed_runtime_assets_exclude_posthoc_labels_and_tokens() -> None:
    runtime_payload = json.loads(
        (_FIXTURE_ROOT / "final_evaluation" / "inputs" / "cases" / "CSV5-232.json").read_text(
            encoding="utf-8"
        )
    )
    rendered = json.dumps(runtime_payload, sort_keys=True)

    assert "candidate_token_id" not in rendered
    assert "observed_acceptance" not in rendered
    assert "prefix_survival_label" not in rendered
    assert runtime_payload["contexts"][0]["visible_prefix_token_ids"] == []
    assert runtime_payload["contexts"][3]["visible_prefix_token_ids"]


def test_final_mixed_loader_rejects_adversarial_reservation() -> None:
    with pytest.raises(CalibrationSuccessorV5FinalCaseContractError) as error:
        load_calibration_successor_v5_final_mixed_reliability_contrast_replay_case(
            _FIXTURE_ROOT, "CSV5-301"
        )

    assert error.value.code is CalibrationSuccessorV5FinalCaseViolationCode.CASE_ASSET_LAYOUT_ERROR


def test_final_mixed_outcome_runtime_misalignment_is_rejected(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    outcome_path = root / "final_evaluation" / "expected_outcomes" / "cases" / "CSV5-233.json"
    payload = json.loads(outcome_path.read_text(encoding="utf-8"))
    payload["fixture_id"] = "misaligned-final-mixed-fixture"
    outcome_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CalibrationSuccessorV5FinalCaseContractError) as error:
        load_calibration_successor_v5_final_mixed_reliability_contrast_replay_case(root, "CSV5-233")

    assert error.value.code is CalibrationSuccessorV5FinalCaseViolationCode.CASE_ALIGNMENT_ERROR


def test_final_mixed_assets_do_not_change_frozen_calibration_manifest_or_fit_provenance() -> None:
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
    assert not (_FIXTURE_ROOT / "final_evaluation_manifest.json").exists()
    assert not (_FIXTURE_ROOT / "final_assessment_result.json").exists()
