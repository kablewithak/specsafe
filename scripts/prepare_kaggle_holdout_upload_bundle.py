"""Prepare the governed Kaggle upload bundle for candidate-calibrator holdout collection.

This script validates the label-free independent holdout prompt corpus and packages
only the public-safe inputs needed for a private Kaggle collection run. It does not
collect traces, fit or replay a calibrator, tune thresholds, or make promotion claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

FORBIDDEN_HOLDOUT_PROMPT_FIELDS = frozenset(
    {
        "observed_acceptance",
        "conditional_acceptance_label",
        "prefix_survival_label",
        "target_probability",
        "draft_probability",
        "raw_confidence",
        "calibrated_acceptance_probability",
        "threshold_decision",
        "scheduler_decision",
        "verification_decision",
    }
)

ALLOWED_WORKLOAD_TYPES = frozenset({"structured_text", "code", "open_ended_chat"})
REQUIRED_DATA_ROLE = "independent_holdout_precollection"
REQUIRED_SPLIT = "independent_holdout_candidate_calibrator_v1"
REQUIRED_EXPECTED_TRACE_ROLE = "holdout_evaluation_only"
REQUIRED_DATA_CLASSIFICATION = "public_safe_self_authored_no_pii"


class HoldoutPromptRecord(BaseModel):
    """Strict label-free prompt record for independent holdout collection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: Annotated[str, Field(min_length=1)]
    corpus_id: Annotated[str, Field(min_length=1)]
    split: Annotated[str, Field(min_length=1)]
    workload_type: Annotated[str, Field(min_length=1)]
    prompt_text: Annotated[str, Field(min_length=1)]
    source_type: Annotated[str, Field(min_length=1)]
    data_classification: Annotated[str, Field(min_length=1)]
    expected_trace_role: Annotated[str, Field(min_length=1)]
    authoring_boundary: Annotated[str, Field(min_length=1)]
    allowed_use: tuple[str, ...]
    forbidden_use: tuple[str, ...]

    @model_validator(mode="before")
    @classmethod
    def reject_label_or_outcome_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        forbidden = sorted(set(data) & FORBIDDEN_HOLDOUT_PROMPT_FIELDS)
        if forbidden:
            fields = ", ".join(forbidden)
            msg = f"holdout prompt corpus must be label-free; forbidden fields: {fields}"
            raise ValueError(msg)
        return data

    @model_validator(mode="after")
    def enforce_holdout_boundary(self) -> Self:
        if self.workload_type not in ALLOWED_WORKLOAD_TYPES:
            msg = f"unsupported workload_type for holdout corpus: {self.workload_type}"
            raise ValueError(msg)
        if self.split != REQUIRED_SPLIT:
            msg = f"holdout prompt split must be {REQUIRED_SPLIT!r}"
            raise ValueError(msg)
        if self.expected_trace_role != REQUIRED_EXPECTED_TRACE_ROLE:
            msg = f"expected_trace_role must be {REQUIRED_EXPECTED_TRACE_ROLE!r}"
            raise ValueError(msg)
        if self.data_classification != REQUIRED_DATA_CLASSIFICATION:
            msg = f"data_classification must be {REQUIRED_DATA_CLASSIFICATION!r}"
            raise ValueError(msg)
        return self


class UploadBundleSummary(BaseModel):
    """Machine-readable summary for the generated private Kaggle upload bundle."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bundle_id: str
    created_utc: str
    data_role: str
    prompt_record_count: int
    workload_counts: dict[str, int]
    prompt_corpus_sha256: str
    precollection_manifest_sha256: str
    forbidden_reference_corpus_count: int
    duplicate_check_status: str
    zip_path: str
    zip_sha256: str
    allowed_next_step: str
    forbidden_uses: tuple[str, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_prompt_text(prompt_text: str) -> str:
    return " ".join(prompt_text.casefold().split())


def load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file_obj:
        for line_number, raw_line in enumerate(file_obj, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                msg = f"invalid JSONL at {path}:{line_number}: {exc.msg}"
                raise ValueError(msg) from exc
            if not isinstance(parsed, dict):
                msg = f"JSONL row must be an object at {path}:{line_number}"
                raise ValueError(msg)
            records.append(parsed)
    return records


def load_prompt_records(path: Path) -> list[HoldoutPromptRecord]:
    return [HoldoutPromptRecord.model_validate(row) for row in load_jsonl_records(path)]


def load_precollection_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file_obj:
        data = json.load(file_obj)
    if not isinstance(data, dict):
        raise ValueError("precollection manifest must be a JSON object")
    return data


def assert_manifest_matches_corpus(
    *,
    manifest: dict[str, Any],
    prompt_records: list[HoldoutPromptRecord],
    prompt_corpus_path: Path,
) -> None:
    if manifest.get("data_role") != REQUIRED_DATA_ROLE:
        msg = f"manifest data_role must be {REQUIRED_DATA_ROLE!r}"
        raise ValueError(msg)

    expected_count = manifest.get("prompt_record_count")
    actual_count = len(prompt_records)
    if expected_count != actual_count:
        msg = f"manifest prompt_record_count {expected_count!r} != actual count {actual_count}"
        raise ValueError(msg)

    expected_hash = manifest.get("prompt_corpus_sha256")
    actual_hash = sha256_file(prompt_corpus_path)
    if expected_hash != actual_hash:
        msg = f"manifest prompt_corpus_sha256 {expected_hash!r} != actual {actual_hash!r}"
        raise ValueError(msg)

    manifest_corpus_id = manifest.get("corpus_id")
    corpus_ids = {record.corpus_id for record in prompt_records}
    if corpus_ids != {manifest_corpus_id}:
        msg = "manifest corpus_id must match every prompt record corpus_id"
        raise ValueError(msg)


def assert_no_internal_duplicates(prompt_records: list[HoldoutPromptRecord]) -> None:
    case_counts = Counter(record.case_id for record in prompt_records)
    duplicate_case_ids = sorted(case_id for case_id, count in case_counts.items() if count > 1)
    if duplicate_case_ids:
        msg = f"duplicate holdout case_id values: {', '.join(duplicate_case_ids)}"
        raise ValueError(msg)

    text_counts = Counter(canonical_prompt_text(record.prompt_text) for record in prompt_records)
    duplicate_texts = sorted(text for text, count in text_counts.items() if count > 1)
    if duplicate_texts:
        msg = "duplicate normalized prompt_text values found inside holdout corpus"
        raise ValueError(msg)


def load_reference_prompt_texts(paths: list[Path]) -> set[str]:
    reference_texts: set[str] = set()
    for path in paths:
        if not path.exists():
            msg = f"forbidden/reference corpus path does not exist: {path}"
            raise FileNotFoundError(msg)
        for row in load_jsonl_records(path):
            prompt_text = row.get("prompt_text")
            if isinstance(prompt_text, str) and prompt_text.strip():
                reference_texts.add(canonical_prompt_text(prompt_text))
    return reference_texts


def assert_no_reference_duplicates(
    *,
    prompt_records: list[HoldoutPromptRecord],
    reference_prompt_texts: set[str],
) -> None:
    if not reference_prompt_texts:
        return
    duplicate_case_ids = [
        record.case_id
        for record in prompt_records
        if canonical_prompt_text(record.prompt_text) in reference_prompt_texts
    ]
    if duplicate_case_ids:
        joined = ", ".join(sorted(duplicate_case_ids))
        msg = f"holdout prompts duplicate forbidden/reference corpus cases: {joined}"
        raise ValueError(msg)


def write_upload_readme(
    path: Path,
    *,
    prompt_record_count: int,
    workload_counts: dict[str, int],
) -> None:
    body = f"""# V5 Candidate Calibrator Independent Holdout Kaggle Upload Bundle

## Role

This bundle is for private Kaggle holdout trace collection only.

It contains label-free, public-safe prompt inputs and manifests needed to collect
independent holdout traces for the retained candidate calibrator.

## Included files

```text
v5_candidate_calibrator_holdout_prompt_corpus.jsonl
v5_candidate_calibrator_holdout_precollection_manifest.json
UPLOAD_BUNDLE_MANIFEST.json
KAGGLE_HOLDOUT_UPLOAD_README.md
```

## Corpus summary

```text
prompt_record_count={prompt_record_count}
structured_text={workload_counts.get("structured_text", 0)}
code={workload_counts.get("code", 0)}
open_ended_chat={workload_counts.get("open_ended_chat", 0)}
```

## Allowed use

- Upload this bundle to the governed private Kaggle collection workflow.
- Collect independent holdout traces using the same governed model and tokenizer boundary.
- Retain the holdout archive for later local analysis and calibrator replay.

## Forbidden use

- Do not refit the candidate calibrator.
- Do not tune thresholds.
- Do not tune scheduler policy.
- Do not merge holdout traces into the fit pool before the promotion decision.
- Do not use this bundle for production speed, latency, throughput, cost, or serving claims.
- Do not publish raw Kaggle working directories or secrets.

## Expected later decision outputs

Exactly one later promotion decision is allowed after retained independent holdout replay:

```text
PROMOTE_CANDIDATE_CALIBRATOR
KEEP_CANDIDATE_CALIBRATOR_DIAGNOSTIC_ONLY
REQUIRE_ADDITIONAL_HOLDOUT_EVIDENCE
```
"""
    path.write_text(body, encoding="utf-8")


def prepare_upload_bundle(
    *,
    holdout_corpus_path: Path,
    precollection_manifest_path: Path,
    output_dir: Path,
    forbidden_corpus_paths: list[Path],
) -> UploadBundleSummary:
    prompt_records = load_prompt_records(holdout_corpus_path)
    manifest = load_precollection_manifest(precollection_manifest_path)
    assert_manifest_matches_corpus(
        manifest=manifest,
        prompt_records=prompt_records,
        prompt_corpus_path=holdout_corpus_path,
    )
    assert_no_internal_duplicates(prompt_records)
    reference_texts = load_reference_prompt_texts(forbidden_corpus_paths)
    assert_no_reference_duplicates(
        prompt_records=prompt_records,
        reference_prompt_texts=reference_texts,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    readme_path = output_dir / "KAGGLE_HOLDOUT_UPLOAD_README.md"
    bundle_manifest_path = output_dir / "UPLOAD_BUNDLE_MANIFEST.json"
    zip_path = output_dir / "v5_candidate_calibrator_holdout_kaggle_upload_bundle.zip"

    workload_counts = dict(Counter(record.workload_type for record in prompt_records))
    created_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    upload_manifest = {
        "bundle_id": "v5-candidate-calibrator-independent-holdout-kaggle-upload-v1",
        "created_utc": created_utc,
        "data_role": "independent_holdout_upload_bundle",
        "source_precollection_manifest": str(precollection_manifest_path.as_posix()),
        "source_prompt_corpus": str(holdout_corpus_path.as_posix()),
        "prompt_record_count": len(prompt_records),
        "workload_counts": workload_counts,
        "prompt_corpus_sha256": sha256_file(holdout_corpus_path),
        "precollection_manifest_sha256": sha256_file(precollection_manifest_path),
        "duplicate_check_status": "passed_exact_normalized_prompt_checks",
        "forbidden_reference_corpus_count": len(forbidden_corpus_paths),
        "allowed_next_step": "private_kaggle_holdout_trace_collection",
        "forbidden_uses": [
            "calibrator_refit",
            "threshold_tuning",
            "scheduler_tuning",
            "fit_pool_augmentation_before_promotion_decision",
            "production_claim",
            "hugging_face_final_release_before_holdout_decision",
        ],
    }
    bundle_manifest_path.write_text(
        json.dumps(upload_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_upload_readme(
        readme_path,
        prompt_record_count=len(prompt_records),
        workload_counts=workload_counts,
    )

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(
            holdout_corpus_path,
            arcname="v5_candidate_calibrator_holdout_prompt_corpus.jsonl",
        )
        zip_file.write(
            precollection_manifest_path,
            arcname="v5_candidate_calibrator_holdout_precollection_manifest.json",
        )
        zip_file.write(bundle_manifest_path, arcname="UPLOAD_BUNDLE_MANIFEST.json")
        zip_file.write(readme_path, arcname="KAGGLE_HOLDOUT_UPLOAD_README.md")

    return UploadBundleSummary(
        bundle_id=upload_manifest["bundle_id"],
        created_utc=created_utc,
        data_role=upload_manifest["data_role"],
        prompt_record_count=len(prompt_records),
        workload_counts=workload_counts,
        prompt_corpus_sha256=upload_manifest["prompt_corpus_sha256"],
        precollection_manifest_sha256=upload_manifest["precollection_manifest_sha256"],
        forbidden_reference_corpus_count=len(forbidden_corpus_paths),
        duplicate_check_status=upload_manifest["duplicate_check_status"],
        zip_path=str(zip_path),
        zip_sha256=sha256_file(zip_path),
        allowed_next_step=upload_manifest["allowed_next_step"],
        forbidden_uses=tuple(upload_manifest["forbidden_uses"]),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and package the SpecSafe candidate-calibrator holdout Kaggle bundle."
    )
    parser.add_argument(
        "--holdout-corpus",
        type=Path,
        default=Path("data/kaggle_holdout/v5_candidate_calibrator_holdout_prompt_corpus.jsonl"),
    )
    parser.add_argument(
        "--precollection-manifest",
        type=Path,
        default=Path(
            "data/kaggle_holdout/v5_candidate_calibrator_holdout_precollection_manifest.json"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/kaggle_holdout/v5_candidate_calibrator_holdout_upload_bundle"),
    )
    parser.add_argument(
        "--forbidden-corpus",
        action="append",
        type=Path,
        default=[],
        help="Optional JSONL prompt corpus to reject exact normalized duplicates against.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = prepare_upload_bundle(
        holdout_corpus_path=args.holdout_corpus,
        precollection_manifest_path=args.precollection_manifest,
        output_dir=args.output_dir,
        forbidden_corpus_paths=args.forbidden_corpus,
    )
    print(summary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
