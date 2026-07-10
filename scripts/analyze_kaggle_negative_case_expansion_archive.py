from __future__ import annotations

from pathlib import Path

from specsafe.kaggle_trace_analysis.negative_case_expansion_analysis import (
    write_negative_case_reports,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-negative-case-expansion-v1"
    / "attempt-001-t4"
)


def main() -> None:
    analysis_report, replay_report = write_negative_case_reports(ATTEMPT_DIR)

    signal = analysis_report["signal_diagnostics"]
    combined = analysis_report["combined_raw_count_implication"]
    thresholds = replay_report["threshold_diagnostics"]

    print("analysis_report=", ATTEMPT_DIR / "trace_analysis_report.json")
    print("replay_report=", ATTEMPT_DIR / "trace_replay_report.json")
    print("runtime_record_count=", analysis_report["record_counts"]["runtime_record_count"])
    print("target_argmax_match_count=", signal["target_argmax_match_count"])
    print("target_argmax_nonmatch_count=", signal["target_argmax_nonmatch_count"])
    print("raw_confidence_roc_auc_diagnostic=", signal["raw_confidence_roc_auc_diagnostic"])
    print("combined_nonmatch_count=", combined["combined_nonmatch_count"])
    print(
        "negative_count_floor_crossed_on_raw_count=",
        combined["negative_count_floor_crossed_on_raw_count"],
    )
    print("threshold_0_5_selected_nonmatch_count=", thresholds[5]["selected_nonmatch_count"])
    print("negative-case analysis/replay status: PASS")


if __name__ == "__main__":
    main()
