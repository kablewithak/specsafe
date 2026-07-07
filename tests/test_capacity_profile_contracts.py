"""Unit tests for strict synthetic capacity-profile contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from specsafe.capacity_profiles import (
    CapacityProfileError,
    CapacityProfileKind,
    CapacityProfileViolationCode,
    CapacityProfileWindow,
    SyntheticCapacityProfile,
)
from specsafe.contracts import CapacityProfileSource, CapacitySnapshot


def make_profile(
    *,
    profile_kind: CapacityProfileKind = CapacityProfileKind.MODERATE_LOAD,
    windows: tuple[CapacityProfileWindow, ...] | None = None,
) -> SyntheticCapacityProfile:
    return SyntheticCapacityProfile(
        schema_version="synthetic-capacity-profile-v1",
        profile_id=f"synthetic-{profile_kind.value}-v1",
        profile_version="v1",
        profile_kind=profile_kind,
        provenance_note="Synthetic test profile; not a serving measurement.",
        windows=windows
        or (
            CapacityProfileWindow(
                maximum_request_token_load=256,
                available_capacity_units=100.0,
                marginal_verification_cost_units=0.25,
            ),
            CapacityProfileWindow(
                maximum_request_token_load=1024,
                available_capacity_units=75.0,
                marginal_verification_cost_units=0.75,
            ),
            CapacityProfileWindow(
                maximum_request_token_load=None,
                available_capacity_units=30.0,
                marginal_verification_cost_units=2.5,
            ),
        ),
    )


def make_snapshot(profile_id: str) -> CapacitySnapshot:
    return CapacitySnapshot(
        profile_id=profile_id,
        source=CapacityProfileSource.SYNTHETIC,
        active_request_count=16,
        verification_batch_tokens=64,
    )


def test_profile_contract_is_immutable_and_rejects_unknown_fields() -> None:
    profile = make_profile()

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SyntheticCapacityProfile(
            **profile.model_dump(),
            observed_serving_throughput=123.0,
        )

    with pytest.raises(ValidationError):
        profile.profile_id = "mutated"


def test_non_jagged_profiles_reject_capacity_recovery() -> None:
    with pytest.raises(ValidationError, match="must not increase"):
        make_profile(
            windows=(
                CapacityProfileWindow(
                    maximum_request_token_load=256,
                    available_capacity_units=40.0,
                    marginal_verification_cost_units=1.0,
                ),
                CapacityProfileWindow(
                    maximum_request_token_load=None,
                    available_capacity_units=60.0,
                    marginal_verification_cost_units=2.0,
                ),
            )
        )


def test_jagged_profile_requires_capacity_and_cost_reversal() -> None:
    with pytest.raises(ValidationError, match="requires an intentional"):
        make_profile(
            profile_kind=CapacityProfileKind.JAGGED_CAPACITY,
            windows=(
                CapacityProfileWindow(
                    maximum_request_token_load=256,
                    available_capacity_units=90.0,
                    marginal_verification_cost_units=0.5,
                ),
                CapacityProfileWindow(
                    maximum_request_token_load=None,
                    available_capacity_units=20.0,
                    marginal_verification_cost_units=3.0,
                ),
            ),
        )


def test_flat_capacity_control_requires_constant_values() -> None:
    with pytest.raises(ValidationError, match="flat_capacity_control"):
        make_profile(
            profile_kind=CapacityProfileKind.FLAT_CAPACITY_CONTROL,
            windows=(
                CapacityProfileWindow(
                    maximum_request_token_load=256,
                    available_capacity_units=100.0,
                    marginal_verification_cost_units=0.1,
                ),
                CapacityProfileWindow(
                    maximum_request_token_load=None,
                    available_capacity_units=99.0,
                    marginal_verification_cost_units=0.1,
                ),
            ),
        )


def test_profile_evaluation_uses_lawful_snapshot_fields_deterministically() -> None:
    profile = make_profile()
    evaluation = profile.evaluate(make_snapshot(profile.profile_id))

    assert evaluation.request_token_load == 1024
    assert evaluation.selected_maximum_request_token_load == 1024
    assert evaluation.available_capacity_units == 75.0
    assert evaluation.marginal_verification_cost_units == 0.75
    assert profile.evaluate(make_snapshot(profile.profile_id)) == evaluation


def test_profile_evaluation_rejects_snapshot_source_or_identity_mismatch() -> None:
    profile = make_profile()

    with pytest.raises(CapacityProfileError) as identity_error:
        profile.evaluate(make_snapshot("synthetic-other-v1"))
    assert identity_error.value.code is CapacityProfileViolationCode.SNAPSHOT_PROFILE_MISMATCH

    with pytest.raises(CapacityProfileError) as source_error:
        profile.evaluate(
            CapacitySnapshot(
                profile_id=profile.profile_id,
                source=CapacityProfileSource.KAGGLE_MEASURED,
                active_request_count=16,
                verification_batch_tokens=64,
            )
        )
    assert source_error.value.code is CapacityProfileViolationCode.SNAPSHOT_SOURCE_MISMATCH


def test_profile_configuration_hash_is_stable_and_content_sensitive() -> None:
    profile = make_profile()
    same_profile = SyntheticCapacityProfile.model_validate(profile.model_dump(mode="json"))
    changed_profile = make_profile(
        windows=(
            CapacityProfileWindow(
                maximum_request_token_load=256,
                available_capacity_units=100.0,
                marginal_verification_cost_units=0.25,
            ),
            CapacityProfileWindow(
                maximum_request_token_load=1024,
                available_capacity_units=70.0,
                marginal_verification_cost_units=0.75,
            ),
            CapacityProfileWindow(
                maximum_request_token_load=None,
                available_capacity_units=30.0,
                marginal_verification_cost_units=2.5,
            ),
        )
    )

    assert profile.configuration_sha256() == same_profile.configuration_sha256()
    assert profile.configuration_sha256() != changed_profile.configuration_sha256()
