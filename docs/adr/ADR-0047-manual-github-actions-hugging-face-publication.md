# ADR-0047 — Manual GitHub Actions Hugging Face Publication

## Status

Accepted.

## Decision

The authorized SpecSafe Dataset will be published through a manually dispatched GitHub Actions workflow from the default `main` branch.

The exact target is:

```text
KaboKableMolefe/specsafe-bounded-negative-evidence-v1
```

The workflow will not run on pushes or pull requests. A user must open the Actions interface, select the workflow, retain the exact namespace, and type the explicit confirmation phrase:

```text
PUBLISH_EXACT_DATASET
```

## Credential boundary

The workflow uses the `HF_TOKEN` secret from the protected GitHub environment:

```text
hugging-face-publication
```

The token is exposed only to the dispatch-validation, remote-preflight, and publication steps. It is not passed as a command-line argument, printed, committed, or stored in the publication receipt.

## Publication behavior

The existing controlled publisher remains authoritative. The workflow only orchestrates it:

1. validate the manual dispatch and protected credential presence;
2. validate the exact local candidate and authorization;
3. run focused regression tests;
4. run a no-write remote preflight;
5. publish the exact nine-file Dataset;
6. verify the private and anonymous public remote states;
7. validate the generated receipt; and
8. upload the receipt as a GitHub Actions artifact for review.

## Receipt policy

The workflow does not commit or push the receipt back to the repository. Automatic source-control writes would combine remote publication with evidence acceptance.

The receipt is downloaded from the successful workflow run, reviewed, and committed through a separate pull request.

## Failure posture

- Existing target repository: stop.
- Wrong namespace: stop.
- Wrong confirmation phrase: stop.
- Non-`main` ref: stop.
- Missing environment secret: stop.
- Candidate or authorization drift: stop.
- Private-stage failure: the controlled publisher deletes the newly created remote Dataset.
- Public verification failure: the controlled publisher returns the Dataset to private visibility.

## Consequence

After this workflow is merged to `main` and the protected environment is configured, the next action is a single manual publication run. A successful run produces the remote Dataset and a reviewable publication receipt without granting the workflow permission to modify the GitHub repository.
