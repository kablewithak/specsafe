"""Integration tests for the governed V1 synthetic capacity-profile fixture set."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from specsafe.capacity_profiles import (
    CapacityProfileError,
    CapacityProfileKind,
    CapacityProfileViolationCode,
    load_synthetic_capacity_profile_fixture_set,
)
from specsafe.contracts import CapacityProfileSource, CapacitySnapshot

_ROOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "synthetic_capacity_profiles"
    / "v1"
)


def make_snapshot(profile_id: str, *, active_requests: int, batch_tokens: int) -> CapacitySnapshot:
    return CapacitySnapshot(
        profile_id=profile_id,
        source=CapacityProfileSource.SYNTHETIC,
        active_request_count=active_requests,
        verification_batch_tokens=batch_tokens,
    )


def copy_fixture_root(tmp_path: Path) -> Path:
    target = tmp_path / "synthetic_capacity_profiles_v1"
    shutil.copytree(_ROOT, target)
    return target


def test_loads_exactly_the_five_authorized_synthetic_profiles() -> None:
    fixture_set = load_synthetic_capacity_profile_fixture_set(_ROOT)

    assert fixture_set.manifest.fixture_set_id == "synthetic-capacity-profiles-v1"
    assert tuple(profile.profile_kind for profile in fixture_set.profiles) == (
        CapacityProfileKind.LIGHT_LOAD,
        CapacityProfileKind.MODERATE_LOAD,
        CapacityProfileKind.SATURATED_LOAD,
        CapacityProfileKind.JAGGED_CAPACITY,
        CapacityProfileKind.FLAT_CAPACITY_CONTROL,
    )


def test_light_moderate_and_saturated_profiles_diverge_under_identical_load() -> None:
    fixture_set = load_synthetic_capacity_profile_fixture_set(_ROOT)
    light = fixture_set.profile_for_kind(CapacityProfileKind.LIGHT_LOAD)
    moderate = fixture_set.profile_for_kind(CapacityProfileKind.MODERATE_LOAD)
    saturated = fixture_set.profile_for_kind(CapacityProfileKind.SATURATED_LOAD)

    light_result = light.evaluate(
        make_snapshot(light.profile_id, active_requests=16, batch_tokens=64)
    )
    moderate_result = moderate.evaluate(
        make_snapshot(moderate.profile_id, active_requests=16, batch_tokens=64)
    )
    saturated_result = saturated.evaluate(
        make_snapshot(saturated.profile_id, active_requests=16, batch_tokens=64)
    )

    assert light_result.request_token_load == 1024
    assert (
        light_result.available_capacity_units
        > moderate_result.available_capacity_units
        > saturated_result.available_capacity_units
    )
    assert (
        light_result.marginal_verification_cost_units
        < moderate_result.marginal_verification_cost_units
        < saturated_result.marginal_verification_cost_units
    )


def test_flat_capacity_control_is_invariant_across_load_windows() -> None:
    fixture_set = load_synthetic_capacity_profile_fixture_set(_ROOT)
    profile = fixture_set.profile_for_kind(CapacityProfileKind.FLAT_CAPACITY_CONTROL)

    low = profile.evaluate(make_snapshot(profile.profile_id, active_requests=2, batch_tokens=64))
    medium = profile.evaluate(
        make_snapshot(profile.profile_id, active_requests=16, batch_tokens=64)
    )
    high = profile.evaluate(make_snapshot(profile.profile_id, active_requests=64, batch_tokens=128))

    assert (
        low.available_capacity_units
        == medium.available_capacity_units
        == high.available_capacity_units
    )
    assert (
        low.marginal_verification_cost_units
        == medium.marginal_verification_cost_units
        == high.marginal_verification_cost_units
    )


def test_jagged_capacity_contains_an_intentional_recovery_not_present_in_monotonic_profiles(
) -> None:
    fixture_set = load_synthetic_capacity_profile_fixture_set(_ROOT)
    profile = fixture_set.profile_for_kind(CapacityProfileKind.JAGGED_CAPACITY)

    before_recovery = profile.evaluate(
        make_snapshot(profile.profile_id, active_requests=8, batch_tokens=64)
    )
    after_recovery = profile.evaluate(
        make_snapshot(profile.profile_id, active_requests=16, batch_tokens=64)
    )

    assert before_recovery.request_token_load < after_recovery.request_token_load
    assert after_recovery.available_capacity_units > before_recovery.available_capacity_units
    assert (
        after_recovery.marginal_verification_cost_units
        < before_recovery.marginal_verification_cost_units
    )


def test_manifest_detects_a_one_byte_fixture_change(tmp_path: Path) -> None:
    copied_root = copy_fixture_root(tmp_path)
    path = copied_root / "profiles" / "saturated_load.json"
    path.write_bytes(path.read_bytes() + b"\n")

    with pytest.raises(CapacityProfileError) as error:
        load_synthetic_capacity_profile_fixture_set(copied_root)

    assert error.value.code is CapacityProfileViolationCode.PROFILE_INTEGRITY_MISMATCH


def test_manifest_and_fixture_identity_mismatch_fails_explicitly(tmp_path: Path) -> None:
    copied_root = copy_fixture_root(tmp_path)
    profile_path = copied_root / "profiles" / "moderate_load.json"
    profile_payload = json.loads(profile_path.read_text(encoding="utf-8"))
    profile_payload["profile_id"] = "synthetic-moderate-load-mismatch-v1"
    profile_bytes = (
        json.dumps(profile_payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    profile_path.write_bytes(profile_bytes)

    manifest_path = copied_root / "manifest.json"
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_entry = next(
        entry
        for entry in manifest_payload["entries"]
        if entry["profile_kind"] == "moderate_load"
    )
    manifest_entry["sha256"] = hashlib.sha256(profile_bytes).hexdigest()
    manifest_entry["byte_count"] = len(profile_bytes)
    manifest_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(CapacityProfileError) as error:
        load_synthetic_capacity_profile_fixture_set(copied_root)

    assert error.value.code is CapacityProfileViolationCode.PROFILE_PROVENANCE_MISMATCH


def test_unknown_profile_resolution_fails_with_a_machine_readable_code() -> None:
    fixture_set = load_synthetic_capacity_profile_fixture_set(_ROOT)

    with pytest.raises(CapacityProfileError) as error:
        fixture_set.profile_for_id("synthetic-missing-v1")

    assert error.value.code is CapacityProfileViolationCode.PROFILE_NOT_FOUND
