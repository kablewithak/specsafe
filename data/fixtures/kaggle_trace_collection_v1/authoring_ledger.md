# V5 Qwen Governed Trace-Collection Prompt Corpus Ledger

```text
corpus_id=v5-qwen-self-authored-trace-corpus-v1
corpus_sha256=ffe698c9d9c41ea4a374ca7d12293130c832a7523f7554079314875afcce3d52
case_count=6
source_type=self_authored_public_safe
data_role=trace_collection
collection_partition=unassigned
```

The corpus contains two self-authored prompts for each required workload family:

- `structured_text`
- `code`
- `open_ended_chat`

The raw prompt text is repository-controlled for reproducibility but is never emitted in the Kaggle export. Exports retain only `prompt_sha256`, token counts, workload type, and case identity.

No prompt may be added, removed, or rewritten after the first governed execution attempt begins without a new corpus version, hash, ADR, and execution attempt identifier.
