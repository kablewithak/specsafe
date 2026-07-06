"""Neutral probability-ranking primitives.

These functions are intentionally outside calibration fitters and held-out assessment packages.
They provide deterministic ranking metrics without importing either execution boundary.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import isfinite


class TieAwareAurocInputError(ValueError):
    """Raised when AUROC inputs cannot support a deterministic ranking calculation."""


def calculate_tie_aware_auroc(
    probabilities: Sequence[float],
    labels: Sequence[bool],
) -> float:
    """Calculate AUROC with deterministic average ranks for tied probabilities."""

    if len(probabilities) != len(labels) or len(probabilities) < 2:
        raise TieAwareAurocInputError(
            "probabilities and labels must have equal length of at least two"
        )
    if any(
        not isfinite(probability) or not 0.0 <= probability <= 1.0
        for probability in probabilities
    ):
        raise TieAwareAurocInputError(
            "probabilities must be finite values inside the unit interval"
        )

    positive_count = sum(labels)
    negative_count = len(labels) - positive_count
    if positive_count == 0 or negative_count == 0:
        raise TieAwareAurocInputError(
            "AUROC requires at least one positive and one negative outcome"
        )

    ranked = sorted(zip(probabilities, labels, strict=True), key=lambda item: item[0])
    positive_rank_sum = 0.0
    index = 0
    while index < len(ranked):
        group_end = index + 1
        while group_end < len(ranked) and ranked[group_end][0] == ranked[index][0]:
            group_end += 1
        average_rank = ((index + 1) + group_end) / 2.0
        positive_rank_sum += average_rank * sum(
            label for _, label in ranked[index:group_end]
        )
        index = group_end

    return (positive_rank_sum - (positive_count * (positive_count + 1) / 2.0)) / (
        positive_count * negative_count
    )
