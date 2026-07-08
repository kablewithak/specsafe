"""Static contract checks for the V5 Kaggle Qwen qualification notebook."""

from __future__ import annotations

import json
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_NOTEBOOK_PATH = _PROJECT_ROOT / "notebooks" / "kaggle" / "specsafe_v5_qwen_preflight.ipynb"
_P100_FAILURE_PATH = (
    _PROJECT_ROOT
    / "evidence"
    / "kaggle-preflight"
    / "v5-qwen-same-tokenizer-preflight-v1"
    / "attempt-001-p100-result.json"
)
_T4_FAILURE_PATH = (
    _PROJECT_ROOT
    / "evidence"
    / "kaggle-preflight"
    / "v5-qwen-same-tokenizer-preflight-v1"
    / "attempt-002-t4-result.json"
)


def _notebook_source() -> str:
    notebook = json.loads(_NOTEBOOK_PATH.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    assert notebook["nbformat_minor"] >= 5
    assert all(cell["outputs"] == [] for cell in notebook["cells"] if cell["cell_type"] == "code")
    return "\n".join("".join(cell["source"]) for cell in notebook["cells"])


def test_notebook_qualifies_exact_declared_pair_without_trace_collection() -> None:
    source = _notebook_source()

    assert 'DRAFT_MODEL_ID = "Qwen/Qwen2.5-0.5B"' in source
    assert 'TARGET_MODEL_ID = "Qwen/Qwen2.5-1.5B"' in source
    assert 'PREFLIGHT_ID = "v5-qwen-same-tokenizer-preflight-v1"' in source
    assert '"trace_collection_allowed": False' in source
    assert '"trace_collection_performed": False' in source
    assert "Stop here; trace collection is a later governed slice." in source


def test_notebook_pins_revisions_and_proves_tokenizer_compatibility() -> None:
    source = _notebook_source()

    assert "HfApi()" in source
    assert "api.model_info(model_id)" in source
    assert "revision=draft_revision.revision" in source
    assert "revision=target_revision.revision" in source
    assert "token_to_id_mapping_match" in source
    assert "draft_tokenizer.get_vocab()" in source
    assert "target_tokenizer.get_vocab()" in source
    assert "special_token_map_match" in source
    assert "draft_tokenizer.special_tokens_map" in source
    assert "target_tokenizer.special_tokens_map" in source
    assert "additional_special_token_ids" in source
    assert "convert_tokens_to_ids" in source
    assert "additional_special_tokens_ids" not in source
    assert "probe_token_ids_match" in source
    assert "trust_remote_code=False" in source


def test_notebook_runs_gpu_architecture_gate_before_hub_access() -> None:
    source = _notebook_source()

    assert '"gpu_architecture_unsupported"' in source
    assert "torch.cuda.get_device_capability(0)" in source
    assert "torch.cuda.get_arch_list()" in source
    assert source.index("require_supported_gpu_architecture()") < source.index("api = HfApi()")


def test_notebook_uses_padded_vocabulary_safe_logits_qualification() -> None:
    source = _notebook_source()

    assert "dtype=dtype" in source
    assert "torch_dtype=dtype" not in source
    assert "model.config.vocab_size" in source
    assert "model_config_vocabulary_size" in source
    assert "observed_logits_vocabulary_size" in source
    assert "tokenizer_vocabulary_size" in source
    assert "maximum_probe_token_id" in source
    assert "finite_logits" in source
    assert '"logits_non_finite"' in source
    assert '"model_output_vocabulary_mismatch"' in source
    assert '"tokenizer_vocabulary_exceeds_model_output"' in source
    assert '"probe_token_outside_model_output"' in source
    assert "observed_logits_vocabulary_size != model_config_vocabulary_size" in source
    assert "tokenizer_vocabulary_size > model_config_vocabulary_size" in source


def test_notebook_requires_bounded_failure_record_and_finite_logits() -> None:
    source = _notebook_source()

    assert "require_kaggle_gpu()" in source
    assert "require_source_commit_sha()" in source
    assert "test_logits_access(" in source
    assert "torch.isfinite(logits).all()" in source
    assert "write_result(result)" in source
    assert "specsafe_v5_qwen_preflight_result.json" in source
    assert "Kaggle preflight failed. The result file was retained" in source


def test_first_p100_attempt_is_retained_without_trace_collection() -> None:
    result = json.loads(_P100_FAILURE_PATH.read_text(encoding="utf-8"))

    assert result["preflight_status"] == "fails_kaggle_preflight"
    assert result["trace_collection_allowed"] is False
    assert result["trace_collection_performed"] is False
    assert result["failure"]["code"] == "unexpected_preflight_failure"
    assert "additional_special_tokens_ids" in result["failure"]["message"]
    assert result["environment"]["gpu_name"] == "Tesla P100-PCIE-16GB"
    assert result["draft_logits_access"] is None
    assert result["target_logits_access"] is None


def test_second_t4_attempt_retains_tokenizer_success_and_logits_failure() -> None:
    result = json.loads(_T4_FAILURE_PATH.read_text(encoding="utf-8"))

    assert result["preflight_status"] == "fails_kaggle_preflight"
    assert result["trace_collection_allowed"] is False
    assert result["trace_collection_performed"] is False
    assert result["failure"]["code"] == "logits_access_failed"
    assert result["environment"]["gpu_name"] == "Tesla T4"
    assert result["environment"]["gpu_architecture"] == "sm_75"
    assert result["tokenizer_compatibility"]["passed"] is True
    assert result["draft_logits_access"] is None
    assert result["target_logits_access"] is None


def test_notebook_does_not_reference_tokens_or_private_prompt_inputs() -> None:
    source = _notebook_source()

    assert "HF_TOKEN" not in source
    assert "KAGGLE_KEY" not in source
    assert "client_prompt" not in source
    assert "private_prompt" not in source
    assert "os.environ" not in source
