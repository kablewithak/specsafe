from __future__ import annotations

from specsafe.candidate_calibrator_closeout import (
    build_candidate_calibrator_promotion_closeout,
)

if __name__ == "__main__":
    decision = build_candidate_calibrator_promotion_closeout()
    print(
        "candidate_calibrator_promotion_closeout "
        f"decision={decision.decision_outcome.value} "
        f"status={decision.promotion_attempt_status.value} "
        f"failure_labels={','.join(decision.failure_labels)}"
    )
