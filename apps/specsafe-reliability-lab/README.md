# SpecSafe Reliability Lab — Local Visual Shell

This directory contains the local, read-only React presentation for the SpecSafe Hugging Face Space.

## Boundary

```text
live_inference=false
user_input_collection=false
remote_publication=false
canonical_evidence=release/hugging-face-space/specsafe-reliability-lab/evidence_index.json
```

The interface never imports research metrics from TypeScript constants. `npm run evidence:sync` verifies the canonical index byte count and SHA-256 against the frozen manifest, then copies the exact index and manifest into `public/evidence/` for the static build.

## Local commands

```powershell
npm ci
npm audit --audit-level=low
npm run evidence:check
npm run lint
npm run test
npm run build
npm run test:e2e:install
npm run test:e2e
npm run dev
```

Open the local URL printed by Vite. The browser smoke suite covers desktop and mobile Chromium, horizontal overflow, the blocked decision, key case identities, and keyboard access to the evidence explorer.

## Publication status

This directory is a local visual shell only. It does not create, update, or publish a Hugging Face Space. A later slice must freeze the exact publication candidate and its Space metadata before any controlled remote upload.
