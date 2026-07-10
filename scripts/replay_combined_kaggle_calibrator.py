from pathlib import Path

from specsafe.kaggle_trace_calibration.replay_combined_calibrator import (
    CALIBRATOR_REPLAY_REPORT_PATH,
    build_combined_calibrator_replay,
)


def main() -> None:
    build_combined_calibrator_replay(root=Path("."), write_outputs=True)
    print(f"wrote {CALIBRATOR_REPLAY_REPORT_PATH}")


if __name__ == "__main__":
    main()
