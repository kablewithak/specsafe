# Hugging Face Space Prebuilt Publication Executor Result

## Result

```text
result=executor_rebound_locally
actual_space_publication=false
remote_mutation=false
existing_private_space_mutation=false
publication_receipt_written=false
```

## Bound candidate

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
sdk=static
app_file=index.html
app_build_command=absent
source_candidate_file_count=35
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
prebuilt_candidate_file_count=5
prebuilt_candidate_tree_sha256=4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362
evidence_index_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
provider_side_build_required=false
```

## Executor changes

- loads the strict prebuilt candidate manifest;
- validates source-candidate lineage and exact runtime asset paths;
- versions the publication plan and receipt boundary to v2;
- records both source and prebuilt candidate hashes in the receipt;
- rejects provider-side build metadata;
- requires exactly five remote files and exact byte hashes;
- uses a new exact confirmation value: `PUBLISH_EXACT_PREBUILT_SPACE`;
- fails immediately on terminal Hugging Face Space stages.

## Next authorized step

Merge this executor to `main`. Then inspect and delete only the known failed private Space, rerun
non-mutating preflight, publish the exact prebuilt candidate, remove the token, inspect the receipt,
and complete anonymous browser review.
