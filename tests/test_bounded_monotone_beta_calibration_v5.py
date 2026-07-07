"""Regression tests for the one V5 calibration-only bounded-monotone-beta fit."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import specsafe.traces.bounded_monotone_beta_calibration_v5 as fit_module
from specsafe.heldout_calibration.v5_final_assessment import (
    V5AdaptivePolicyResearchEligibility,
)
from specsafe.traces.bounded_monotone_beta_calibration_v5 import (
    V5BoundedMonotoneBetaFitError,
    V5BoundedMonotoneBetaFitViolationCode,
    canonical_v5_bounded_monotone_beta_artifact_json,
    canonical_v5_bounded_monotone_beta_fit_diagnostics_json,
    fit_v5_bounded_monotone_beta_calibration,
    load_v5_bounded_monotone_beta_calibration_fit,
    write_v5_bounded_monotone_beta_calibration_fit,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE_ROOT = _PROJECT_ROOT / "data" / "fixtures" / "synthetic_calibration_successor_v5"
_ARTIFACT_FILENAME = "bounded_monotone_beta_calibration_artifact.json"
_DIAGNOSTICS_FILENAME = "bounded_monotone_beta_calibration_fit_diagnostics.json"

_PRE_FIT_EXCLUSIONS = {
    "No V5 calibration artifact, fit diagnostic, or final assessment result is present.",
    "No V5 fitter, threshold selection, or parameter mutation is authorized.",
}
_FIT_EXCLUSIONS = {
    "V5 bounded-monotone-beta calibration artifact and fit diagnostics are retained "
    "as calibration-only evidence.",
    "No V5 final-evaluation asset, final manifest, held-out assessment, scheduler, "
    "baseline comparison, capacity profile, utility scorer, or runtime control is authorized.",
}


def _copy_fixture_root(tmp_path: Path) -> Path:
    copied_root = tmp_path / "synthetic_calibration_successor_v5"
    shutil.copytree(_FIXTURE_ROOT, copied_root)
    return copied_root


def _restore_manifest_only_root(root: Path) -> None:
    shutil.rmtree(root / "final_evaluation")
    (root / _ARTIFACT_FILENAME).unlink()
    (root / _DIAGNOSTICS_FILENAME).unlink()
    registry_path = root / "scenario_family_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload.update(
        {
            "registry_status": "calibration_manifest_frozen",
            "v5_final_evaluation_runtime_or_outcome_assets_authored": False,
            "v5_calibration_artifact_authored": False,
            "v5_calibration_fit_diagnostics_authored": False,
            "frozen_calibration_artifact_sha256": None,
            "frozen_calibration_fit_diagnostics_sha256": None,
            "next_authorized_artifact": "v5-bounded-monotone-beta-fit-diagnostics",
        }
    )
    for family in payload["families"]:
        if family["scenario_family_id"] == "CSV5-FINAL-CURVE-COVERAGE":
            family["authoring_status"] = "reserved_for_v5_case_authoring"
    payload["explicit_exclusions"] = [
        exclusion
        for exclusion in payload["explicit_exclusions"]
        if exclusion not in _FIT_EXCLUSIONS
        and not exclusion.startswith("Only CSV5-201..CSV5-209")
        and not exclusion.startswith("No V5 final-evaluation manifest")
    ]
    payload["explicit_exclusions"].extend(sorted(_PRE_FIT_EXCLUSIONS))
    registry_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_loads_retained_fit_artifact_and_calibration_only_diagnostics() -> None:
    result = load_v5_bounded_monotone_beta_calibration_fit(_FIXTURE_ROOT)

    assert result.artifact.fitting_completed is True
    assert result.artifact.calibration_observation_count == 192
    assert result.artifact.monotonicity_verification.verification_passed is True
    assert result.diagnostics.sample_count == 192
    assert result.diagnostics.diagnostic_numeric_precision_decimal_places == 12
    assert result.diagnostics.positive_label_count > 0
    assert result.diagnostics.negative_label_count > 0
    assert result.diagnostics.final_evaluation_accessed is False
    assert result.diagnostics.threshold_selection_performed is False
    assert result.diagnostics.scheduler_or_policy_execution_performed is False
    assert result.diagnostics.promotion_status == "not_assessed"
    assert result.diagnostics.runtime_control_eligible is False
    assert result.diagnostics.calibrated_metrics.mean_binary_negative_log_likelihood < (
        result.diagnostics.raw_metrics.mean_binary_negative_log_likelihood
    )
    assert result.diagnostics.auroc_delta == 0.0
    assert (
        V5AdaptivePolicyResearchEligibility.ELIGIBLE_FOR_CONTROLLED_POLICY_RESEARCH.value
        not in result.diagnostics.model_dump_json()
    )


def test_fit_is_deterministic_on_a_restored_manifest_only_root(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    _restore_manifest_only_root(root)

    written = write_v5_bounded_monotone_beta_calibration_fit(root)
    loaded = load_v5_bounded_monotone_beta_calibration_fit(root)
    retained = load_v5_bounded_monotone_beta_calibration_fit(_FIXTURE_ROOT)

    assert written == loaded
    assert canonical_v5_bounded_monotone_beta_artifact_json(written.artifact) == (
        canonical_v5_bounded_monotone_beta_artifact_json(retained.artifact)
    )
    assert canonical_v5_bounded_monotone_beta_fit_diagnostics_json(written.diagnostics) == (
        canonical_v5_bounded_monotone_beta_fit_diagnostics_json(retained.diagnostics)
    )


def test_fit_rejects_existing_destinations_before_rebuilding() -> None:
    with pytest.raises(V5BoundedMonotoneBetaFitError) as error:
        fit_v5_bounded_monotone_beta_calibration(_FIXTURE_ROOT)

    assert error.value.code is V5BoundedMonotoneBetaFitViolationCode.DESTINATION_ALREADY_EXISTS


def test_fit_rejects_tampered_calibration_asset_before_writing(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    _restore_manifest_only_root(root)
    asset_path = root / "inputs" / "cases" / "CSV5-101.json"
    asset_path.write_text(asset_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(V5BoundedMonotoneBetaFitError) as error:
        fit_v5_bounded_monotone_beta_calibration(root)

    assert error.value.code is V5BoundedMonotoneBetaFitViolationCode.MANIFEST_INTEGRITY_FAILURE


def test_retained_fit_rejects_tampered_artifact_bytes(tmp_path: Path) -> None:
    root = _copy_fixture_root(tmp_path)
    artifact_path = root / _ARTIFACT_FILENAME
    artifact_path.write_text(artifact_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(V5BoundedMonotoneBetaFitError) as error:
        load_v5_bounded_monotone_beta_calibration_fit(root)

    assert error.value.code is V5BoundedMonotoneBetaFitViolationCode.PROVENANCE_MISMATCH


def test_retained_fit_coexists_with_quarantined_final_assets_without_final_result() -> None:
    present_names = {child.name for child in _FIXTURE_ROOT.iterdir()}

    assert "final_evaluation" in present_names
    assert "adversarial_regression" not in present_names
    assert "final_evaluation_manifest.json" not in present_names
    assert "final_assessment_result.json" not in present_names
    assert "scheduling" not in present_names
    assert "capacity_profiles" not in present_names


def test_fit_normalizes_sub_precision_optimizer_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _copy_fixture_root(tmp_path)
    _restore_manifest_only_root(root)

    baseline = fit_v5_bounded_monotone_beta_calibration(root)
    original = fit_module._fit_projected_gradient_descent

    def with_sub_precision_variation(*args, **kwargs):
        parameters, metadata = original(*args, **kwargs)
        metadata["final_gradient_norm"] = float(metadata["final_gradient_norm"]) + 1e-15
        return parameters, metadata

    monkeypatch.setattr(fit_module, "_fit_projected_gradient_descent", with_sub_precision_variation)
    varied = fit_v5_bounded_monotone_beta_calibration(root)

    assert canonical_v5_bounded_monotone_beta_artifact_json(baseline.artifact) == (
        canonical_v5_bounded_monotone_beta_artifact_json(varied.artifact)
    )
    assert canonical_v5_bounded_monotone_beta_fit_diagnostics_json(baseline.diagnostics) == (
        canonical_v5_bounded_monotone_beta_fit_diagnostics_json(varied.diagnostics)
    )
