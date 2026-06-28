"""Runtime gate that prevents schedulers from receiving retrospective information."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from specsafe.contracts.models import (
    CausalSafetyAssessment,
    CausalSafetyStatus,
    CausalSafetyViolation,
    CausalSchedulerContext,
    CausalViolationCode,
)

_FORBIDDEN_FIELD_PREFIXES = ("future_", "retrospective_", "observed_")
_FORBIDDEN_FIELD_NAMES = {
    "target_acceptance_outcomes",
    "verification_outcomes",
    "retrospective_optimal_prefix",
}


class ForbiddenInformationAccessError(ValueError):
    """Raised when a runtime policy receives a non-causal context."""

    def __init__(self, violation: CausalSafetyViolation) -> None:
        super().__init__(violation.message)
        self.violation = violation


def assess_runtime_context(context: object) -> CausalSafetyAssessment:
    """Assess whether ``context`` is the exact approved runtime contract.

    The exact-type check is intentional. Future evaluation-only shapes must not become
    silently valid through inheritance or accidental structural compatibility.
    """

    if type(context) is CausalSchedulerContext:
        return CausalSafetyAssessment(status=CausalSafetyStatus.PASS)

    field_names = _extract_field_names(context)
    offending_fields = tuple(
        field_name
        for field_name in field_names
        if field_name.startswith(_FORBIDDEN_FIELD_PREFIXES)
        or field_name in _FORBIDDEN_FIELD_NAMES
    )

    if offending_fields:
        violation = CausalSafetyViolation(
            code=CausalViolationCode.FORBIDDEN_FUTURE_INFORMATION_ACCESS,
            message=(
                "runtime scheduling context contains fields that expose future, observed, "
                "or retrospective information"
            ),
            offending_fields=offending_fields,
        )
    else:
        violation = CausalSafetyViolation(
            code=CausalViolationCode.UNAPPROVED_RUNTIME_CONTEXT_TYPE,
            message="runtime scheduling requires the exact CausalSchedulerContext contract",
            offending_fields=field_names,
        )

    return CausalSafetyAssessment(status=CausalSafetyStatus.FAIL, violation=violation)


def require_causal_runtime_context(context: object) -> CausalSchedulerContext:
    """Return an approved context or raise a machine-readable boundary error."""

    assessment = assess_runtime_context(context)
    if assessment.status is CausalSafetyStatus.FAIL:
        assert assessment.violation is not None
        raise ForbiddenInformationAccessError(assessment.violation)
    assert type(context) is CausalSchedulerContext
    return context


def _extract_field_names(context: object) -> tuple[str, ...]:
    """Return visible field names without serialising or inspecting field values."""

    if isinstance(context, BaseModel):
        return tuple(type(context).model_fields)

    attributes: dict[str, Any] | None = getattr(context, "__dict__", None)
    if attributes is None:
        return ()
    return tuple(attributes)
