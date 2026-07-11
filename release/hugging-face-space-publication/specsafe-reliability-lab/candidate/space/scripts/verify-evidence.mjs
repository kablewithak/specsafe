import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";

const evidencePath = new URL(
  "../public/evidence/evidence_index.json",
  import.meta.url,
);
const expectedByteCount = 9206;
const expectedSha256 = "de6af9e8263269b4c689f636739ca840b905d685852280e9b79f574ac4ffb57e";

const payload = await readFile(evidencePath);
if (payload.byteLength !== expectedByteCount) {
  throw new Error(
    `Evidence byte-count mismatch: ${payload.byteLength} !== ${expectedByteCount}`,
  );
}

const actualSha256 = createHash("sha256").update(payload).digest("hex");
if (actualSha256 !== expectedSha256) {
  throw new Error(
    `Evidence SHA-256 mismatch: ${actualSha256} !== ${expectedSha256}`,
  );
}

const evidence = JSON.parse(payload.toString("utf8"));
if (
  evidence.read_only !== true ||
  evidence.live_inference !== false ||
  evidence.user_input_collection !== false
) {
  throw new Error("Evidence authorization boundary changed.");
}

console.log(`Evidence check passed: ${actualSha256}`);
