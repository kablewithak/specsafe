import {
  Check,
  Database,
  ExternalLink,
  FileCheck2,
  GitCommitHorizontal,
  LockKeyhole,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { EvidenceIndex } from "@/lib/evidence";

type EvidenceExplorerSectionProps = {
  evidence: EvidenceIndex;
};

function yesNo(value: boolean) {
  return value ? "Yes" : "No";
}

export function EvidenceExplorerSection({
  evidence,
}: EvidenceExplorerSectionProps) {
  return (
    <section id="evidence" className="bg-background">
      <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
        <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-amber-200/65">
              06 / Inspect the evidence
            </p>
            <h2 className="mt-4 max-w-xl text-balance text-3xl font-semibold tracking-[-0.035em] text-white md:text-5xl">
              Verify the boundary, not just the headline.
            </h2>
          </div>

          <div>
            <p className="max-w-3xl text-pretty text-lg leading-8 text-white/58">
              This interface is a read-only view over one frozen evidence contract. It does
              not run inference, accept user input, or rewrite the underlying artifacts.
            </p>

            <div className="mt-7 grid gap-5 border-y border-white/10 py-5 sm:grid-cols-3">
              <div>
                <p className="text-xs text-white/32">Read only</p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {yesNo(evidence.read_only)}
                </p>
              </div>
              <div>
                <p className="text-xs text-white/32">Live inference</p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {yesNo(evidence.live_inference)}
                </p>
              </div>
              <div>
                <p className="text-xs text-white/32">User input collected</p>
                <p className="mt-2 text-sm font-semibold text-white">
                  {yesNo(evidence.user_input_collection)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <Tabs defaultValue="boundary" className="mt-16">
          <TabsList aria-label="Evidence views">
            <TabsTrigger value="boundary">Boundary</TabsTrigger>
            <TabsTrigger value="claims">Claims</TabsTrigger>
            <TabsTrigger value="sources">Sources</TabsTrigger>
            <TabsTrigger value="dataset">Dataset</TabsTrigger>
          </TabsList>

          <TabsContent value="boundary">
            <div className="mt-8 grid gap-10 lg:grid-cols-[0.82fr_1.18fr]">
              <div>
                <div className="flex items-center gap-2 text-amber-200/75">
                  <LockKeyhole className="h-4 w-4" aria-hidden="true" />
                  <p className="font-mono text-[10px] uppercase tracking-[0.18em]">
                    Governed boundary
                  </p>
                </div>
                <h3 className="mt-4 text-2xl font-semibold tracking-[-0.025em] text-white">
                  What counted as valid evidence.
                </h3>
                <p className="mt-4 max-w-lg text-sm leading-7 text-white/42">
                  Valid comparisons had to respect decision-time causality. Retrospective
                  controls that depended on future information were explicitly excluded.
                </p>
              </div>

              <dl className="divide-y divide-white/10 border-y border-white/10">
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-center">
                  <dt className="text-sm text-white/46">Valid causal comparisons</dt>
                  <dd className="font-mono text-xl font-semibold text-white">
                    {evidence.valid_causal_comparisons}
                  </dd>
                </div>
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-center">
                  <dt className="text-sm text-white/46">Unsafe retrospective controls excluded</dt>
                  <dd className="font-mono text-xl font-semibold text-white">
                    {evidence.unsafe_retrospective_controls_excluded}
                  </dd>
                </div>
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-center">
                  <dt className="text-sm text-white/46">Unsafe controls failed causal safety</dt>
                  <dd className="text-sm font-semibold text-white">
                    {yesNo(evidence.unsafe_controls_failed_causal_safety)}
                  </dd>
                </div>
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-center">
                  <dt className="text-sm text-white/46">Evidence schema</dt>
                  <dd className="break-all font-mono text-xs text-white/70 sm:text-right">
                    {evidence.schema_version}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="mt-12 border-t border-white/10 pt-6">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/28">
                Maturity labels
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {evidence.maturity_labels.map((label) => (
                  <Badge key={label}>{label}</Badge>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="claims">
            <div className="mt-8 grid gap-12 lg:grid-cols-2 lg:gap-16">
              <div>
                <div className="flex items-center gap-2 border-t border-emerald-300/35 pt-5 text-emerald-200">
                  <Check className="h-4 w-4" aria-hidden="true" />
                  <h3 className="text-sm font-semibold">Supported</h3>
                </div>
                <ul className="mt-5 divide-y divide-white/8">
                  {evidence.supported_claims.map((claim) => (
                    <li key={claim} className="py-4 text-sm leading-7 text-white/56">
                      {claim}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <div className="flex items-center gap-2 border-t border-rose-300/35 pt-5 text-rose-200">
                  <X className="h-4 w-4" aria-hidden="true" />
                  <h3 className="text-sm font-semibold">Not established</h3>
                </div>
                <ul className="mt-5 divide-y divide-white/8">
                  {evidence.non_claims.map((claim) => (
                    <li key={claim} className="py-4 text-sm leading-7 text-white/56">
                      {claim}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="sources">
            <div className="mt-8">
              <div className="flex items-center gap-2 text-amber-200/75">
                <FileCheck2 className="h-4 w-4" aria-hidden="true" />
                <p className="font-mono text-[10px] uppercase tracking-[0.18em]">
                  Source artifacts
                </p>
              </div>

              <div className="mt-5 divide-y divide-white/10 border-y border-white/10">
                {evidence.source_artifacts.map((source) => (
                  <div
                    key={source.relative_path}
                    className="grid gap-4 py-5 lg:grid-cols-[1fr_0.95fr]"
                  >
                    <code className="break-all text-xs leading-6 text-white/62">
                      {source.relative_path}
                    </code>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.15em] text-white/26">
                        SHA-256
                      </p>
                      <code className="mt-2 block break-all text-xs leading-6 text-amber-100/70">
                        {source.sha256}
                      </code>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex items-center gap-2 text-xs text-white/38">
                <GitCommitHorizontal className="h-4 w-4" aria-hidden="true" />
                <span>Source commit</span>
                <code className="text-white/65">{evidence.source_commit}</code>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="dataset">
            <div className="mt-8 grid gap-12 lg:grid-cols-[0.75fr_1.25fr]">
              <div>
                <div className="flex items-center gap-2 text-emerald-200">
                  <Database className="h-4 w-4" aria-hidden="true" />
                  <p className="font-mono text-[10px] uppercase tracking-[0.18em]">
                    Public governed release
                  </p>
                </div>

                <h3 className="mt-4 break-words text-2xl font-semibold tracking-[-0.025em] text-white">
                  {evidence.dataset_publication.repository_id}
                </h3>

                <p className="mt-4 text-sm leading-7 text-white/44">
                  Anonymous public verification passed against the published revision.
                </p>

                <a
                  href={evidence.dataset_publication.repository_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-6 inline-flex items-center gap-2 border-b border-white/30 pb-1 text-sm font-semibold text-white transition-colors hover:border-amber-200 hover:text-amber-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300"
                >
                  Open the Dataset
                  <ExternalLink className="h-4 w-4" aria-hidden="true" />
                </a>
              </div>

              <dl className="divide-y divide-white/10 border-y border-white/10">
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-center">
                  <dt className="text-sm text-white/46">Public</dt>
                  <dd className="text-sm font-semibold text-white">
                    {yesNo(evidence.dataset_publication.public)}
                  </dd>
                </div>
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-center">
                  <dt className="text-sm text-white/46">Gated</dt>
                  <dd className="text-sm font-semibold text-white">
                    {yesNo(evidence.dataset_publication.gated)}
                  </dd>
                </div>
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-center">
                  <dt className="text-sm text-white/46">Exact files</dt>
                  <dd className="font-mono text-sm font-semibold text-white">
                    {evidence.dataset_publication.exact_file_count}
                  </dd>
                </div>
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-start">
                  <dt className="text-sm text-white/46">Published revision</dt>
                  <dd className="break-all font-mono text-xs text-white/70 sm:max-w-md sm:text-right">
                    {evidence.dataset_publication.published_revision}
                  </dd>
                </div>
                <div className="grid gap-3 py-5 sm:grid-cols-[1fr_auto] sm:items-start">
                  <dt className="text-sm text-white/46">Manifest SHA-256</dt>
                  <dd className="break-all font-mono text-xs leading-6 text-white/70 sm:max-w-md sm:text-right">
                    {evidence.dataset_publication.publication_manifest_sha256}
                  </dd>
                </div>
              </dl>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}
