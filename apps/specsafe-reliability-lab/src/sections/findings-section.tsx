import { Check, Minus, X } from "lucide-react";

import type { EvidenceIndex } from "@/lib/evidence";

type FindingsSectionProps = {
  evidence: EvidenceIndex;
};

const findings = [
  {
    number: "01",
    title: "Adaptive verification can help without being a global winner.",
    detail:
      "The governed cases contain wins, neutral outcomes, and a loss. The useful conclusion is conditional behavior, not universal superiority.",
  },
  {
    number: "02",
    title: "A better average metric does not authorize automation.",
    detail:
      "Calibration improved while ranking safety regressed. Different required properties need independent acceptance gates.",
  },
  {
    number: "03",
    title: "Blocking promotion is a successful reliability outcome.",
    detail:
      "The candidate remained useful as diagnostic evidence even though it was not safe enough to control runtime scheduling.",
  },
] as const;

export function FindingsSection({ evidence }: FindingsSectionProps) {
  return (
    <section
      id="what-it-means"
      className="border-b border-black/10 bg-[#f2efe6] text-[#171714]"
    >
      <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
        <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-black/42">
              05 / What we learned
            </p>
            <h2 className="mt-4 max-w-xl text-balance text-3xl font-semibold tracking-[-0.035em] text-[#171714] md:text-5xl">
              Reliability is the gate, not the average score.
            </h2>
          </div>

          <div>
            <p className="max-w-3xl text-pretty text-lg leading-8 text-black/62">
              {evidence.final_interpretation}
            </p>
            <p className="mt-5 max-w-3xl text-sm leading-7 text-black/44">
              The result is valuable because the evaluation preserved the mixed outcome and
              stopped a promising candidate from becoming an unsupported deployment claim.
            </p>
          </div>
        </div>

        <div className="mt-16 divide-y divide-black/10 border-y border-black/10">
          {findings.map((finding) => (
            <article
              key={finding.number}
              className="grid gap-4 py-7 md:grid-cols-[70px_0.9fr_1.1fr] md:gap-8"
            >
              <p className="font-mono text-xs text-black/28">{finding.number}</p>
              <h3 className="text-xl font-semibold leading-7 tracking-[-0.02em] text-[#171714]">
                {finding.title}
              </h3>
              <p className="text-sm leading-7 text-black/48">{finding.detail}</p>
            </article>
          ))}
        </div>

        <div className="mt-20">
          <div className="max-w-3xl">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-black/30">
              Interpretation boundary
            </p>
            <h3 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-[#171714]">
              What the evidence supports — and what it does not.
            </h3>
            <p className="mt-4 text-sm leading-7 text-black/44">
              A reliability result is only as trustworthy as its claim boundary. Supported
              statements stay separate from conclusions this experiment did not establish.
            </p>
          </div>

          <div className="mt-10 grid gap-10 lg:grid-cols-2 lg:gap-16">
            <div>
              <div className="flex items-center gap-2 border-t border-emerald-800/35 pt-5 text-emerald-900">
                <Check className="h-4 w-4" aria-hidden="true" />
                <h4 className="text-sm font-semibold">Supported by the evidence</h4>
              </div>

              <ul className="mt-5 divide-y divide-black/8">
                {evidence.supported_claims.map((claim) => (
                  <li key={claim} className="grid grid-cols-[18px_1fr] gap-3 py-4">
                    <span
                      className="mt-2 h-1.5 w-1.5 rounded-full bg-emerald-800"
                      aria-hidden="true"
                    />
                    <span className="text-sm leading-7 text-black/58">{claim}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <div className="flex items-center gap-2 border-t border-rose-800/35 pt-5 text-rose-900">
                <X className="h-4 w-4" aria-hidden="true" />
                <h4 className="text-sm font-semibold">Not established</h4>
              </div>

              <ul className="mt-5 divide-y divide-black/8">
                {evidence.non_claims.map((claim) => (
                  <li key={claim} className="grid grid-cols-[18px_1fr] gap-3 py-4">
                    <Minus className="mt-1.5 h-3.5 w-3.5 text-rose-900/70" aria-hidden="true" />
                    <span className="text-sm leading-7 text-black/58">{claim}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-16 border-l-2 border-rose-800/45 pl-5 md:pl-7">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-rose-900/70">
            The reliability result
          </p>
          <p className="mt-3 max-w-4xl text-xl font-semibold leading-8 text-[#171714] md:text-2xl">
            The system did not prove that adaptive scheduling should be deployed. It proved
            that the evaluation process could preserve useful positive evidence, expose a
            hidden regression, and refuse promotion when the contract was breached.
          </p>
        </div>
      </div>
    </section>
  );
}
