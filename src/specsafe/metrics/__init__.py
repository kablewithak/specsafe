"""Provider-neutral metric primitives used across SpecSafe evidence boundaries."""

from specsafe.metrics.ranking import (
    TieAwareAurocInputError,
    calculate_tie_aware_auroc,
)

__all__ = [
    "TieAwareAurocInputError",
    "calculate_tie_aware_auroc",
]
