# Hugging Face Space Publication Runbook

## Boundary

This runbook publishes the exact frozen candidate only after the publication executor is merged to `main`.

```text
repository_id=KaboKableMolefe/specsafe-reliability-lab
repository_type=space
sdk=static
candidate_file_count=35
candidate_tree_sha256=041c8bafd573afbca5db9f55887a89007970d4a3d20b1f9486d879064897c4bb
existing_repository_policy=reject
private_stage=true
anonymous_repository_verification=true
anonymous_application_verification=true
```

## Provider scaffold normalization

A newly created static Space may begin with the provider-generated scaffold below:

```text
.gitattributes
README.md
index.html
style.css
```

The publication adapter treats only this exact known set, or a subset of it, as provider scaffold.
`README.md` and `index.html` are overwritten by the governed candidate. `.gitattributes` and
`style.css` are deleted in the same exact commit. Any other initial path remains visible to the
service and revokes publication. The private and anonymous post-commit gates still require the
exact 35-file candidate allowlist and byte hashes.

## Local tooling validation

```powershell
python .\scripts\publish_hugging_face_space.py --check-local
python -m pytest .\tests\test_hugging_face_space_publication.py
python -m pytest .\tests\test_hugging_face_space_publication_git_gate.py
python -m pytest .\tests\test_hugging_face_space_hub_adapter.py
```

`--check-local` performs no network action.

## Remote preflight

Use a Hugging Face write token scoped only as broadly as required. Set it in the current PowerShell
process; do not paste it into source, logs, screenshots, shell history files, or the publication
receipt.

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

Preflight verifies authenticated namespace ownership and confirms that the target Space does not
already exist. It performs no remote mutation.

## Controlled publication

Publication is allowed only from clean `main` and requires an explicit confirmation value.

```powershell
python .\scripts\publish_hugging_face_space.py `
    --publish `
    --namespace KaboKableMolefe `
    --confirmation PUBLISH_EXACT_SPACE
```

Successful publication writes:

```text
evidence/publication-receipts/specsafe-reliability-lab/
hugging_face_space_publication_receipt.json
```

The receipt contains the remote revision, public application URL, local Git SHA, candidate manifest
hash, aggregate candidate-tree hash, all 35 file hashes, and verification outcomes. It contains no
credential material.

## Manual anonymous review

Before staging the receipt:

1. open the printed application URL in a private/incognito browser window;
2. confirm the North Star appears before detailed results;
3. confirm neutral outcomes are visible;
4. confirm `MPC5-103` remains the loss;
5. confirm `MPC5-104` and `MPC5-105` remain the clearest wins;
6. confirm `KEEP_DIAGNOSTIC_ONLY`, `ranking_safety_regression`, and the approximately `24.36x` breach remain visible;
7. confirm no login is required and no input or upload control exists;
8. confirm desktop and narrow-mobile layouts have no horizontal overflow.

## Credential cleanup

```powershell
Remove-Item Env:HF_TOKEN -ErrorAction SilentlyContinue
```

Confirm the variable is gone without printing its former value:

```powershell
if (Test-Path Env:HF_TOKEN) {
    throw "HF_TOKEN is still present in the current process environment."
}
```

## Failure behavior

- Failure before public release deletes the newly created Space.
- Failure after public release changes the Space back to private.
- An existing Space is never overwritten.
- An existing receipt is never overwritten.
- A failed publication does not authorize manual editing of the remote repository.
- An unknown provider-created initial file revokes publication and triggers deletion rollback.
