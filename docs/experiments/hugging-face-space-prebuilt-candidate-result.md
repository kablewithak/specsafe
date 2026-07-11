# Hugging Face Space prebuilt candidate result

## Trigger

```text
source_candidate_file_count=35
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
remote_source_upload_revision=78102df9fc41f0fd42363bbd0a7eb4371469c5d6
remote_source_upload_stage=CONFIG_ERROR
remote_source_upload_rollback=private
publication_receipt_written=false
```

## Intervention

Replace the provider-side Node build dependency with a locally built, validated,
hash-bound static runtime candidate.

## Required local gates

```text
source_candidate_check=required
npm_ci=required
evidence_check=required
eslint=required
unit_tests=required
vite_production_build=required
prebuilt_candidate_byte_check=required
```

## Acceptance criteria

```text
sdk=static
app_file=index.html
app_build_command=absent
provider_side_build_required=false
frozen_evidence_sha256=de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e
live_inference=false
user_input_collection=false
remote_mutation=false
next_step=rebind_controlled_publication_executor_to_prebuilt_candidate
```

The generated file count and aggregate candidate-tree SHA-256 are recorded by
`prebuilt_candidate_manifest.json` after the local build.
