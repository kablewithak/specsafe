# Hugging Face Space Publication Runbook

## Boundary

This runbook publishes the exact locally built static candidate only after the rebound executor is
merged to clean `main`.

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
repository_type=space
sdk=static
app_file=index.html
app_build_command=absent
candidate_file_count=5
candidate_tree_sha256=4e1eb0f186ed629e2a2fa352cd8943da5a5771aa43198f51814bb5013cf71362
source_candidate_file_count=35
source_candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
existing_repository_policy=reject
provider_side_build_required=false
private_stage=true
anonymous_repository_verification=true
anonymous_application_verification=true
```

## Local tooling validation

```powershell
python .\scripts\build_hugging_face_space_prebuilt_candidate.py --check
python .\scripts\publish_hugging_face_space.py --check-local
python -m pytest .\tests\test_hugging_face_space_publication.py
python -m pytest .\tests\test_hugging_face_space_publication_git_gate.py
python -m pytest .\tests\test_hugging_face_space_hub_adapter.py
```

These commands perform no network mutation.

## Failed private Space cleanup

The failed source-candidate publication remains private at revision
`78102df9fc41f0fd42363bbd0a7eb4371469c5d6`. Before final publication, authenticate with a temporary
write token, inspect the repository, and delete it only when all of these values match:

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
private=true
sdk=static
sha=78102df9fc41f0fd42363bbd0a7eb4371469c5d6
stage=CONFIG_ERROR
remote_file_count=35
```

Do not delete a repository whose identity, visibility, revision, stage, or file count differs.

## Provider scaffold normalization

A newly created static Space may begin with this provider-generated scaffold:

```text
.gitattributes
README.md
index.html
style.css
```

Only this exact set, or a subset, is normalized. `README.md` and `index.html` are overwritten by the
prebuilt candidate. `.gitattributes` and `style.css` are deleted in the exact commit. Any unknown
initial path revokes publication. Post-commit gates require exactly five files and exact hashes.

## Remote preflight

Use a temporary Hugging Face write token and keep it only in the current PowerShell process.

```powershell
$SecureToken = Read-Host "Hugging Face write token" -AsSecureString
$TokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureToken)

try {
    $env:HF_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($TokenPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($TokenPointer)
    Remove-Variable SecureToken, TokenPointer -ErrorAction SilentlyContinue
}

python .\scripts\publish_hugging_face_space.py `
    --preflight `
    --namespace KaboKableMolefe
```

Preflight verifies namespace ownership and confirms that the target Space does not exist. It does
not mutate the remote service.

## Controlled publication

Publication is allowed only from clean `main` and requires the new prebuilt-candidate confirmation.

```powershell
python .\scripts\publish_hugging_face_space.py `
    --publish `
    --namespace KaboKableMolefe `
    --confirmation PUBLISH_EXACT_PREBUILT_SPACE `
    --application-timeout-seconds 900
```

Successful publication writes:

```text
evidence/publication-receipts/specsafe-reliability-lab/
hugging_face_space_publication_receipt.json
```

The v2 receipt contains the remote revision, public application URL, local Git SHA, source-candidate
lineage, prebuilt manifest and tree hashes, all five runtime file hashes, and verification outcomes.
It contains no credential material.

## Manual anonymous review

Before staging the receipt:

1. open the printed application URL in a private browser window;
2. confirm the North Star appears before detailed results;
3. confirm neutral outcomes are visible;
4. confirm `MPC5-103` remains the loss;
5. confirm `MPC5-104` and `MPC5-105` remain the clearest wins;
6. confirm `KEEP_DIAGNOSTIC_ONLY`, `ranking_safety_regression`, and approximately `24.36x` remain
   visible;
7. confirm no login is required and no input or upload control exists;
8. confirm desktop and narrow-mobile layouts have no horizontal overflow.

## Credential cleanup

```powershell
Remove-Item Env:HF_TOKEN -ErrorAction SilentlyContinue
Test-Path Env:HF_TOKEN
```

The final command must return `False`. Revoke the temporary token after successful publication.

## Failure behavior

- Failure before public release deletes the newly created Space.
- Failure after public release returns the Space to private.
- Terminal provider stages fail immediately and trigger rollback.
- An existing Space is never overwritten.
- An existing receipt is never overwritten.
- A failed publication does not authorize manual editing of the remote repository.
- An unknown provider-created initial file revokes publication and triggers deletion rollback.
