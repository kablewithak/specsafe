"""Filesystem loader for the governed synthetic capacity-profile fixture set."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from specsafe.capacity_profiles.models import (
    CapacityProfileError,
    CapacityProfileViolationCode,
    SyntheticCapacityProfile,
    SyntheticCapacityProfileFixtureManifest,
    SyntheticCapacityProfileFixtureSet,
)

_MANIFEST_FILENAME = "manifest.json"


def load_synthetic_capacity_profile_fixture_set(
    root: Path,
) -> SyntheticCapacityProfileFixtureSet:
    """Load every manifest-declared synthetic capacity profile with byte verification.

    This loader is deliberately read-only. It does not author fixtures, update hashes,
    or infer missing profiles. A later scheduler can depend on the returned object
    without needing access to the fixture filesystem.
    """

    resolved_root = root.resolve()
    manifest_path = resolved_root / _MANIFEST_FILENAME
    try:
        manifest = SyntheticCapacityProfileFixtureManifest.model_validate(
            json.loads(manifest_path.read_text(encoding="utf-8"))
        )
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise CapacityProfileError(
            CapacityProfileViolationCode.MANIFEST_SCHEMA_ERROR,
            f"unable to load synthetic capacity-profile manifest: {error}",
        ) from error

    profiles: list[SyntheticCapacityProfile] = []
    for entry in manifest.entries:
        profile_path = resolved_root / entry.relative_path
        try:
            raw = profile_path.read_bytes()
        except OSError as error:
            raise CapacityProfileError(
                CapacityProfileViolationCode.PROFILE_SCHEMA_ERROR,
                f"unable to read synthetic capacity profile {entry.relative_path!r}: {error}",
            ) from error

        if len(raw) != entry.byte_count or hashlib.sha256(raw).hexdigest() != entry.sha256:
            raise CapacityProfileError(
                CapacityProfileViolationCode.PROFILE_INTEGRITY_MISMATCH,
                f"synthetic capacity profile {entry.relative_path!r} does not match its manifest",
            )

        try:
            profile = SyntheticCapacityProfile.model_validate(json.loads(raw))
        except (json.JSONDecodeError, ValidationError) as error:
            raise CapacityProfileError(
                CapacityProfileViolationCode.PROFILE_SCHEMA_ERROR,
                f"synthetic capacity profile {entry.relative_path!r} is invalid: {error}",
            ) from error

        if (
            profile.profile_kind is not entry.profile_kind
            or profile.profile_id != entry.profile_id
            or profile.profile_version != entry.profile_version
        ):
            raise CapacityProfileError(
                CapacityProfileViolationCode.PROFILE_PROVENANCE_MISMATCH,
                "synthetic capacity profile "
                f"{entry.relative_path!r} disagrees with manifest identity",
            )
        profiles.append(profile)

    try:
        return SyntheticCapacityProfileFixtureSet(
            manifest=manifest,
            profiles=tuple(profiles),
        )
    except ValidationError as error:
        raise CapacityProfileError(
            CapacityProfileViolationCode.MANIFEST_SCHEMA_ERROR,
            f"synthetic capacity-profile fixture set is invalid: {error}",
        ) from error
