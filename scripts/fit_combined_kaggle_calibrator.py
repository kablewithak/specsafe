from pathlib import Path

from specsafe.kaggle_trace_calibration.fit_combined_calibrator import (
    CALIBRATOR_FIT_REPORT_PATH,
    CALIBRATOR_MODEL_PATH,
    build_combined_calibrator_fit,
)


def main() -> None:
    build_combined_calibrator_fit(root=Path("."), write_outputs=True)
    print(f"wrote {CALIBRATOR_MODEL_PATH}")
    print(f"wrote {CALIBRATOR_FIT_REPORT_PATH}")


if __name__ == "__main__":
    main()
