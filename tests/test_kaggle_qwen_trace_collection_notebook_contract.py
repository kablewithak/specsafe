from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "kaggle"
    / "specsafe_v5_qwen_trace_collection.ipynb"
)
CORPUS_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fixtures"
    / "kaggle_trace_collection_v1"
    / "prompt_corpus.json"
)


def _notebook_source() -> str:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )


def _assignment_value(source: str, name: str) -> object:
    module = ast.parse(source)
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(statement.value)
    raise AssertionError(f"Missing assignment: {name}")


def test_notebook_is_valid_json() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))

    assert notebook["nbformat"] == 4
    assert len(notebook["cells"]) == 4


def test_notebook_prompt_corpus_matches_versioned_fixture() -> None:
    source = _notebook_source()
    prompt_cases = _assignment_value(source, "PROMPT_CASES")
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    canonical = json.dumps(corpus, sort_keys=True, separators=(",", ":")).encode("utf-8")

    assert tuple(corpus["cases"]) == prompt_cases
    assert hashlib.sha256(canonical).hexdigest() == _assignment_value(
        source, "PROMPT_CORPUS_SHA256"
    )
    assert corpus["case_count"] == 6
    assert {case["workload_type"] for case in corpus["cases"]} == {
        "structured_text",
        "code",
        "open_ended_chat",
    }


def test_notebook_requires_trace_collection_lineage_and_write_once_outputs() -> None:
    source = _notebook_source()

    assert 'PREFLIGHT_ATTEMPT_ID = "attempt-003-t4-pass"' in source
    assert "PREFLIGHT_RESULT_SHA256" in source
    assert "require_clean_destination" in source
    assert "output_already_exists" in source
    assert "trace_collection_performed" in source
    assert "trace_collection_archive_created" in source
    assert "specsafe_v5_qwen_trace_collection_v1_attempt_001.zip" in source


def test_notebook_uses_pinned_models_and_bounded_greedy_collection() -> None:
    source = _notebook_source()

    assert 'DRAFT_MODEL_REVISION = "060db6499f32faf8b98477b0a26969ef7d8b9987"' in source
    assert 'TARGET_MODEL_REVISION = "8faed761d45a263340a0528343f099c05c9a4323"' in source
    assert "MAX_BLOCK_POSITIONS = 4" in source
    assert "model.generate(" not in source
    assert "trust_remote_code=False" in source
    assert "dtype=dtype" in source


def test_notebook_separates_runtime_and_post_hoc_outcomes_and_avoids_raw_export() -> None:
    source = _notebook_source()

    assert '"runtime_records.jsonl"' in source
    assert '"expected_outcomes.jsonl"' in source
    assert '"target_argmax_matches_candidate"' in source
    assert '"prefix_target_argmax_match"' in source
    assert '"prompt_sha256"' in source
    assert '"prompt_text"' not in source
    assert '"decoded_candidate"' not in source
    assert '"full_logits"' not in source
