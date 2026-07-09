from __future__ import annotations

from pathlib import Path

from specsafe.kaggle_trace_replay.expanded_archive_replay import write_replay_report

REPO_ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_DIR = (
    REPO_ROOT
    / "evidence"
    / "kaggle-trace-collection"
    / "v5-qwen-governed-trace-collection-v2"
    / "attempt-001-t4"
)
REPORT_PATH = ATTEMPT_DIR / "trace_replay_report.json"


if __name__ == "__main__":
    write_replay_report(ATTEMPT_DIR, REPORT_PATH)
    print(REPORT_PATH)
