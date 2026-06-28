"""Test-only unsafe context shapes used as negative controls.

This module exists so tests can demonstrate that retrospective information would be
useful to an optimiser but is invalid at the runtime scheduling boundary.
"""

from __future__ import annotations

from specsafe.contracts.models import CausalSchedulerContext, StrictContract


class RetrospectiveEvaluationContext(StrictContract):
    """An intentionally invalid context that includes unavailable future information."""

    runtime_context: CausalSchedulerContext
    future_candidate_token_ids: tuple[int, ...]
    future_acceptance_outcomes: tuple[bool, ...]
