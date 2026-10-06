import { ArrowRight, ShieldAlert } from "lucide-react";

import type { EvidenceIndex } from "@/lib/evidence";
import { formatDecimal } from "@/lib/format";

type HeroSectionProps = {
  evidence: EvidenceIndex;
};

export function HeroSection({ evidence }: HeroSectionProps) {
  const breachMagnitude = formatDecimal(
    evidence.calibration_gate.degradation_multiple_of_limit,
    2,
  );

  return (
    <section
      id="overview"
      className="border-b border-black/10 bg-[#f2efe6] text-[#171714]"
    >
      <div className="mx-auto max-w-7xl px-5 py-16 md:px-8 md:py-24 lg:py-28">
        <div className="grid gap-14 lg:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)] lg:items-end">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-black/48">
              SpecSafe · Causal confidence-scheduled verification
            </p>

            <h1 className="mt-7 max-w-5xl text-balance text-5xl font-semibold leading-[0.96] tracking-[-0.055em] text-[#11110f] md:text-7xl lg:text-[5.5rem]">
              When should AI spend more compute?
            </h1>

            <p className="mt-7 max-w-3xl text-pretty text-lg leading-8 text-black/62 md:text-xl">
              {evidence.tested_question}
            </p>

            <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-sm font-medium">
              <a
                href="#why-it-matters"
                className="inline-flex items-center gap-2 border-b border-black/35 pb-1 text-black transition-colors hover:border-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black/50"
              >
                Understand the failure
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </a>
              <a
                href="#evidence"
                className="inline-flex items-center gap-2 border-b border-black/15 pb-1 text-black/55 transition-colors hover:border-black/50 hover:text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black/50"
              >
                Inspect the evidence
              </a>
            </div>
          </div>

          <aside
            aria-label="Current promotion decision"
            className="border-l-2 border-rose-700 pl-6 md:pl-8"
          >
            <div className="flex items-center gap-2 text-rose-800">
              <ShieldAlert className="h-4 w-4" aria-hidden="true" />
              <p className="font-mono text-[11px] uppercase tracking-[0.18em]">
                Promotion blocked
              </p>
            </div>

            <h2 className="mt-5 text-2xl font-semibold leading-tight tracking-[-0.025em] text-black md:text-[1.75rem]">
              Calibration improved, but confidence ranking got worse.
            </h2>

            <p className="mt-5 text-[15px] leading-7 text-black/68">
              The confidence signal became worse at ranking stronger predictions above
              weaker ones. Because that property is required for automated scheduling,
              SpecSafe blocked activation and kept the candidate for diagnostic use only.
            </p>

            <dl className="mt-8 divide-y divide-black/12 border-y border-black/12">
              <div className="grid grid-cols-[110px_1fr] gap-5 py-4">
                <dt className="text-xs font-medium text-black/48">Status</dt>
                <dd className="text-right text-sm font-semibold text-black">
                  Diagnostic only
                </dd>
              </div>

              <div className="grid grid-cols-[110px_1fr] gap-5 py-4">
                <dt className="text-xs font-medium text-black/48">Why blocked</dt>
                <dd className="text-right text-sm font-semibold text-rose-800">
                  Ranking safety regressed
                </dd>
              </div>

              <div className="grid grid-cols-[110px_1fr] gap-5 py-4">
                <dt className="text-xs font-medium text-black/48">Observed breach</dt>
                <dd className="text-right text-sm font-semibold text-rose-800">
                  {breachMagnitude}× beyond allowed degradation
                </dd>
              </div>
            </dl>

            <p className="mt-4 text-xs leading-5 text-black/42">
              Machine decision:{" "}
              <span className="font-mono text-black/58">
                {evidence.calibration_gate.decision_outcome}
              </span>
            </p>
          </aside>
        </div>
      </div>
    </section>
  );
}
