"""Normalized provenance contracts for valid capacity-blind baseline policies.

These contracts classify baseline behavior without changing how a baseline decides. They
exist so a future same-input comparison can retain exact policy identity and configuration
hashes rather than reconstructing them from ad hoc runtime objects.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from specsafe.contracts.models import StrictContract

if TYPE_CHECKING:
    from specsafe.scheduling.policies import (
        FixedLengthPolicyConfig,
        StaticThresholdPolicyConfig,
    )


class BaselinePolicyKind(StrEnum):
    """Valid baseline families currently authorized for controlled replay."""

    FIXED_LENGTH = "fixed_length"
    STATIC_THRESHOLD = "static_threshold"


class PolicyClassification(StrEnum):
    """Promotion classification for a retained policy descriptor."""

    VALID_BASELINE = "valid_baseline"


class PolicyCapacitySensitivity(StrEnum):
    """Whether a policy rule changes its decision from capacity conditions."""

    CAPACITY_BLIND = "capacity_blind"


class BaselinePolicyDescriptor(StrictContract):
    """Immutable normalized identity for one causal capacity-blind baseline.

    The descriptor deliberately does not include utility, capacity outcome, or winner
    fields. It records only a valid baseline's declared behavior and exact configuration
    identity for later governed comparison work.
    """

    policy_id: str = Field(min_length=1, max_length=128)
    policy_kind: BaselinePolicyKind
    classification: Literal[PolicyClassification.VALID_BASELINE] = (
        PolicyClassification.VALID_BASELINE
    )
    capacity_sensitivity: Literal[PolicyCapacitySensitivity.CAPACITY_BLIND] = (
        PolicyCapacitySensitivity.CAPACITY_BLIND
    )
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def configuration_sha256(
    config: FixedLengthPolicyConfig | StaticThresholdPolicyConfig,
) -> str:
    """Return the stable evidence hash for one immutable policy configuration."""

    canonical_json = json.dumps(
        config.model_dump(mode="json"),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(f"{canonical_json}\n".encode()).hexdigest()
