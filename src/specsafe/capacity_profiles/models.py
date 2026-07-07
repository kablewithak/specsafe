"""Typed, synthetic capacity-profile contracts for controlled SpecSafe replay.

Capacity profiles are declared synthetic governance inputs. They convert the lawful
runtime capacity snapshot into deterministic normalized capacity and marginal-cost
proxies. They are not hardware measurements, a throughput benchmark, or scheduler
logic.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from specsafe.contracts import CapacityProfileSource, CapacitySnapshot
from specsafe.contracts.models import StrictContract


class CapacityProfileKind(StrEnum):
    """Named synthetic profile families required before load-aware policy work."""

    LIGHT_LOAD = "light_load"
    MODERATE_LOAD = "moderate_load"
    SATURATED_LOAD = "saturated_load"
    JAGGED_CAPACITY = "jagged_capacity"
    FLAT_CAPACITY_CONTROL = "flat_capacity_control"


class CapacityProfileUnit(StrEnum):
    """Declared units for synthetic capacity and marginal verification cost."""

    NORMALIZED_CAPACITY_POINTS = "normalized_capacity_points"


class CapacityLoadUnit(StrEnum):
    """Declared unit used to select a profile window from a runtime snapshot."""

    REQUEST_TOKEN_LOAD_UNITS = "request_token_load_units"


class CapacityProfileViolationCode(StrEnum):
    """Machine-readable capacity-profile validation and lookup failures."""

    MANIFEST_SCHEMA_ERROR = "capacity_profile_manifest_schema_error"
    MANIFEST_INTEGRITY_MISMATCH = "capacity_profile_manifest_integrity_mismatch"
    PROFILE_SCHEMA_ERROR = "capacity_profile_schema_error"
    PROFILE_INTEGRITY_MISMATCH = "capacity_profile_integrity_mismatch"
    PROFILE_PROVENANCE_MISMATCH = "capacity_profile_provenance_mismatch"
    PROFILE_NOT_FOUND = "capacity_profile_not_found"
    SNAPSHOT_PROFILE_MISMATCH = "capacity_snapshot_profile_mismatch"
    SNAPSHOT_SOURCE_MISMATCH = "capacity_snapshot_source_mismatch"


class CapacityProfileError(ValueError):
    """Raised when a synthetic capacity profile cannot be loaded or evaluated."""

    def __init__(self, code: CapacityProfileViolationCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class CapacityProfileWindow(StrictContract):
    """One deterministic request-token-load window in a synthetic profile.

    ``maximum_request_token_load`` is inclusive. ``None`` is permitted only for the
    final unbounded window. The values are normalized simulation inputs rather than
    observations from a serving system.
    """

    maximum_request_token_load: int | None = Field(default=None, ge=0)
    available_capacity_units: float = Field(gt=0.0)
    marginal_verification_cost_units: float = Field(ge=0.0)


class CapacityProfileEvaluation(StrictContract):
    """The deterministic profile result available to a future policy boundary."""

    profile_id: str = Field(min_length=1, max_length=128)
    profile_version: str = Field(min_length=1, max_length=64)
    profile_kind: CapacityProfileKind
    source: Literal[CapacityProfileSource.SYNTHETIC] = CapacityProfileSource.SYNTHETIC
    capacity_unit: CapacityProfileUnit
    load_unit: CapacityLoadUnit
    request_token_load: int = Field(ge=0)
    selected_maximum_request_token_load: int | None = Field(default=None, ge=0)
    available_capacity_units: float = Field(gt=0.0)
    marginal_verification_cost_units: float = Field(ge=0.0)


class SyntheticCapacityProfile(StrictContract):
    """A versioned synthetic relationship between lawful load and capacity proxies."""

    schema_version: str = Field(min_length=1, max_length=64)
    profile_id: str = Field(min_length=1, max_length=128)
    profile_version: str = Field(min_length=1, max_length=64)
    profile_kind: CapacityProfileKind
    source: Literal[CapacityProfileSource.SYNTHETIC] = CapacityProfileSource.SYNTHETIC
    capacity_unit: CapacityProfileUnit = CapacityProfileUnit.NORMALIZED_CAPACITY_POINTS
    load_unit: CapacityLoadUnit = CapacityLoadUnit.REQUEST_TOKEN_LOAD_UNITS
    provenance_note: str = Field(min_length=1, max_length=500)
    windows: tuple[CapacityProfileWindow, ...] = Field(min_length=2)

    @field_validator("profile_id", "profile_version", "schema_version")
    @classmethod
    def validate_identifier_characters(cls, value: str) -> str:
        """Keep fixture identifiers safe for manifests and deterministic reports."""

        if any(character.isspace() for character in value):
            raise ValueError("capacity profile identifiers must not contain whitespace")
        return value

    @model_validator(mode="after")
    def validate_window_shape(self) -> SyntheticCapacityProfile:
        """Require a complete deterministic window partition and declared behaviour."""

        previous_maximum: int | None = None
        for index, window in enumerate(self.windows):
            maximum = window.maximum_request_token_load
            if maximum is None:
                if index != len(self.windows) - 1:
                    raise ValueError(
                        "an unbounded capacity window must be the final profile window"
                    )
                continue
            if previous_maximum is not None and maximum <= previous_maximum:
                raise ValueError(
                    "capacity profile window maxima must be strictly increasing"
                )
            previous_maximum = maximum

        if self.windows[-1].maximum_request_token_load is not None:
            raise ValueError("capacity profiles require a final unbounded window")

        availability = tuple(window.available_capacity_units for window in self.windows)
        cost = tuple(window.marginal_verification_cost_units for window in self.windows)

        if self.profile_kind is CapacityProfileKind.FLAT_CAPACITY_CONTROL:
            if len(set(availability)) != 1 or len(set(cost)) != 1:
                raise ValueError(
                    "flat_capacity_control must keep capacity and marginal cost constant"
                )
        elif self.profile_kind is CapacityProfileKind.JAGGED_CAPACITY:
            has_capacity_recovery = any(
                later > earlier for earlier, later in zip(availability, availability[1:])
            )
            has_cost_recovery = any(later < earlier for earlier, later in zip(cost, cost[1:]))
            if not has_capacity_recovery or not has_cost_recovery:
                raise ValueError(
                    "jagged_capacity requires an intentional capacity and cost reversal"
                )
        else:
            if any(later > earlier for earlier, later in zip(availability, availability[1:])):
                raise ValueError(
                    "non-jagged synthetic capacity availability must not increase with load"
                )
            if any(later < earlier for earlier, later in zip(cost, cost[1:])):
                raise ValueError(
                    "non-jagged marginal verification cost must not decrease with load"
                )

        return self

    def evaluate(self, snapshot: CapacitySnapshot) -> CapacityProfileEvaluation:
        """Evaluate this profile against one lawful decision-time capacity snapshot."""

        if type(snapshot) is not CapacitySnapshot:
            raise CapacityProfileError(
                CapacityProfileViolationCode.SNAPSHOT_PROFILE_MISMATCH,
                "capacity profile evaluation requires the exact CapacitySnapshot contract",
            )
        if snapshot.source is not self.source:
            raise CapacityProfileError(
                CapacityProfileViolationCode.SNAPSHOT_SOURCE_MISMATCH,
                "capacity snapshot source does not match the synthetic profile source",
            )
        if snapshot.profile_id != self.profile_id:
            raise CapacityProfileError(
                CapacityProfileViolationCode.SNAPSHOT_PROFILE_MISMATCH,
                "capacity snapshot profile_id does not match the selected capacity profile",
            )

        request_token_load = (
            snapshot.active_request_count * snapshot.verification_batch_tokens
        )
        for window in self.windows:
            maximum = window.maximum_request_token_load
            if maximum is None or request_token_load <= maximum:
                return CapacityProfileEvaluation(
                    profile_id=self.profile_id,
                    profile_version=self.profile_version,
                    profile_kind=self.profile_kind,
                    capacity_unit=self.capacity_unit,
                    load_unit=self.load_unit,
                    request_token_load=request_token_load,
                    selected_maximum_request_token_load=maximum,
                    available_capacity_units=window.available_capacity_units,
                    marginal_verification_cost_units=window.marginal_verification_cost_units,
                )

        raise AssertionError("validated capacity profile must contain an unbounded final window")

    def configuration_sha256(self) -> str:
        """Return a stable hash for policy/configuration provenance without file I/O."""

        return hashlib.sha256(_canonical_json(self.model_dump(mode="json"))).hexdigest()


class SyntheticCapacityProfileFixtureManifestEntry(StrictContract):
    """Hash-addressed reference to one synthetic capacity-profile fixture."""

    profile_kind: CapacityProfileKind
    profile_id: str = Field(min_length=1, max_length=128)
    profile_version: str = Field(min_length=1, max_length=64)
    relative_path: str = Field(min_length=1, max_length=300)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0)

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        """Keep fixture manifests inside their declared root."""

        normalized = value.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            raise ValueError("relative_path must remain inside the capacity fixture root")
        return normalized


class SyntheticCapacityProfileFixtureManifest(StrictContract):
    """Immutable inventory for the complete V1 synthetic capacity-profile set."""

    schema_version: str = Field(min_length=1, max_length=64)
    fixture_set_id: str = Field(min_length=1, max_length=128)
    fixture_set_version: str = Field(min_length=1, max_length=64)
    source: Literal[CapacityProfileSource.SYNTHETIC] = CapacityProfileSource.SYNTHETIC
    provenance_note: str = Field(min_length=1, max_length=500)
    entries: tuple[SyntheticCapacityProfileFixtureManifestEntry, ...] = Field(
        min_length=5, max_length=5
    )

    @model_validator(mode="after")
    def validate_complete_profile_inventory(self) -> SyntheticCapacityProfileFixtureManifest:
        """Require exactly the named synthetic profiles authorised by the handover."""

        kinds = tuple(entry.profile_kind for entry in self.entries)
        if set(kinds) != set(CapacityProfileKind) or len(set(kinds)) != len(kinds):
            raise ValueError(
                "capacity profile manifest must contain each required profile kind exactly once"
            )
        profile_ids = tuple(entry.profile_id for entry in self.entries)
        if len(set(profile_ids)) != len(profile_ids):
            raise ValueError("capacity profile manifest profile IDs must be unique")
        paths = tuple(entry.relative_path for entry in self.entries)
        if len(set(paths)) != len(paths):
            raise ValueError("capacity profile manifest paths must be unique")
        return self


class SyntheticCapacityProfileFixtureSet(StrictContract):
    """Validated synthetic profile fixture set for later deterministic policy replay."""

    manifest: SyntheticCapacityProfileFixtureManifest
    profiles: tuple[SyntheticCapacityProfile, ...] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def validate_manifest_alignment(self) -> SyntheticCapacityProfileFixtureSet:
        """Ensure loaded profile identity agrees exactly with the frozen manifest."""

        manifest_by_kind = {entry.profile_kind: entry for entry in self.manifest.entries}
        profile_by_kind = {profile.profile_kind: profile for profile in self.profiles}
        if set(profile_by_kind) != set(manifest_by_kind):
            raise ValueError("loaded capacity profiles must match the manifest profile kinds")

        for kind, entry in manifest_by_kind.items():
            profile = profile_by_kind[kind]
            if profile.profile_id != entry.profile_id:
                raise ValueError("loaded capacity profile ID does not match manifest")
            if profile.profile_version != entry.profile_version:
                raise ValueError("loaded capacity profile version does not match manifest")
        return self

    def profile_for_id(self, profile_id: str) -> SyntheticCapacityProfile:
        """Resolve one declared profile by stable ID or raise a typed error."""

        for profile in self.profiles:
            if profile.profile_id == profile_id:
                return profile
        raise CapacityProfileError(
            CapacityProfileViolationCode.PROFILE_NOT_FOUND,
            f"synthetic capacity profile {profile_id!r} is not in the loaded fixture set",
        )

    def profile_for_kind(self, profile_kind: CapacityProfileKind) -> SyntheticCapacityProfile:
        """Resolve one declared profile family without relying on fixture-file paths."""

        for profile in self.profiles:
            if profile.profile_kind is profile_kind:
                return profile
        raise CapacityProfileError(
            CapacityProfileViolationCode.PROFILE_NOT_FOUND,
            f"synthetic capacity profile kind {profile_kind.value!r} is not loaded",
        )


def _canonical_json(payload: object) -> bytes:
    """Serialize profile configuration deterministically for evidence retention."""

    return (
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
