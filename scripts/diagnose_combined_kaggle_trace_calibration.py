from __future__ import annotations

from pathlib import Path

from specsafe.kaggle_trace_calibration.combined_archive_diagnostics import (
    build_combined_calibration_diagnostic_report,
    write_json_lf,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
V2_ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
NEGATIVE_CASE_ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-negative-case-expansion-v1"
    / "attempt-001-t4"
)
REPORT_PATH = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-calibration"
    / "v5-qwen-combined-v2-negative-case"
    / "combined_calibration_diagnostic_report.json"
)


def main() -> None:
    report = build_combined_calibration_diagnostic_report(
        V2_ATTEMPT_DIR,
        NEGATIVE_CASE_ATTEMPT_DIR,
    )
    write_json_lf(REPORT_PATH, report)
    readiness = report["calibration_fit_readiness"]
    diagnostics = report["calibration_diagnostics"]
    print(f"wrote={REPORT_PATH}")
    print(f"observed_record_count={readiness['observed_record_count']}")
    print(f"observed_positive_count={readiness['observed_positive_count']}")
    print(f"observed_negative_count={readiness['observed_negative_count']}")
    print(f"raw_confidence_roc_auc={diagnostics['raw_confidence_roc_auc_diagnostic']}")
    print(f"calibration_fit_authorized={readiness['calibration_fit_authorized']}")
    print(f"next_authorized_step={readiness['next_authorized_step']}")


if __name__ == "__main__":
    main()
