# ADR-0046 — Controlled Hugging Face Dataset Publication

## Status

Accepted.

## Decision

SpecSafe will publish the authorized nine-file Dataset candidate through one controlled Python client.

The publisher will:

1. reject any existing target repository;
2. require the namespace to belong to the authenticated user or one of their organizations;
3. create the Dataset privately;
4. remove the platform-generated `.gitattributes` file when present;
5. commit only the nine authorized candidate files;
6. verify every remote byte while the repository is private;
7. make the Dataset public and ungated only after private verification passes;
8. repeat exact-byte verification anonymously;
9. write a sanitized local receipt containing the repository identity and published revision.

If private-stage validation fails, the newly created repository is deleted. If anonymous public validation fails, the repository is returned to private visibility.

## Credential boundary

The publisher uses the locally managed Hugging Face login. It accepts no token argument and writes no credential, environment value, or authentication response into the receipt.

## Existing repository rule

Publication over an existing repository is rejected. SpecSafe will not merge with, replace, or clean an unknown remote state.

## Result boundary

The publication distributes the retained negative-evidence result. It does not promote the candidate calibrator, scheduler, threshold, or system and does not establish production performance.
