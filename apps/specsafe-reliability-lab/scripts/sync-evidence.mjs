import { createHash } from "node:crypto";
import { access, copyFile, mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(scriptDirectory, "..");
const repositoryRoot = path.resolve(appRoot, "../..");
const canonicalDirectory = path.join(
  repositoryRoot,
  "release",
  "hugging-face-space",
  "specsafe-reliability-lab",
);
const publicDirectory = path.join(appRoot, "public", "evidence");
const checkOnly = process.argv.includes("--check");

const canonicalIndexPath = path.join(canonicalDirectory, "evidence_index.json");
const canonicalManifestPath = path.join(canonicalDirectory, "evidence_manifest.json");
const publicIndexPath = path.join(publicDirectory, "evidence_index.json");
const publicManifestPath = path.join(publicDirectory, "evidence_manifest.json");

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

async function readCanonicalEvidence() {
  const [indexBytes, manifestBytes] = await Promise.all([
    readFile(canonicalIndexPath),
    readFile(canonicalManifestPath),
  ]);
  const manifest = JSON.parse(manifestBytes.toString("utf8"));
  const expected = manifest.generated_artifact;

  if (manifest.evidence_frozen !== true) {
    throw new Error("Canonical Space evidence is not marked frozen.");
  }
  if (manifest.next_authorized_step !== "build_visually_polished_read_only_space_shell") {
    throw new Error(`Unexpected authorization gate: ${manifest.next_authorized_step}`);
  }
  if (expected.relative_path !== "evidence_index.json") {
    throw new Error(`Unexpected generated artifact path: ${expected.relative_path}`);
  }
  if (indexBytes.byteLength !== expected.byte_count) {
    throw new Error(
      `Canonical evidence byte-count mismatch: ${indexBytes.byteLength} != ${expected.byte_count}`,
    );
  }
  const actualSha = sha256(indexBytes);
  if (actualSha !== expected.sha256) {
    throw new Error(`Canonical evidence SHA-256 mismatch: ${actualSha} != ${expected.sha256}`);
  }

  return { indexBytes, manifestBytes, actualSha };
}

async function assertSameBytes(sourceBytes, targetPath, label) {
  try {
    await access(targetPath);
  } catch {
    throw new Error(`${label} is missing. Run npm run evidence:sync.`);
  }
  const targetBytes = await readFile(targetPath);
  if (!sourceBytes.equals(targetBytes)) {
    throw new Error(`${label} drifted from the canonical repository artifact.`);
  }
}

async function main() {
  const { indexBytes, manifestBytes, actualSha } = await readCanonicalEvidence();

  if (checkOnly) {
    await Promise.all([
      assertSameBytes(indexBytes, publicIndexPath, "Public evidence index"),
      assertSameBytes(manifestBytes, publicManifestPath, "Public evidence manifest"),
    ]);
    console.log(`Evidence check passed: ${actualSha}`);
    return;
  }

  await mkdir(publicDirectory, { recursive: true });
  await Promise.all([
    copyFile(canonicalIndexPath, publicIndexPath),
    copyFile(canonicalManifestPath, publicManifestPath),
  ]);
  console.log(`Evidence synchronized: ${actualSha}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
