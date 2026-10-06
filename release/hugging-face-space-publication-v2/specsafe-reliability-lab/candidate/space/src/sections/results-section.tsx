import { useMemo, useState } from "react";

import { PolicyCaseMatrix } from "@/components/policy-case-matrix";
import {
  UtilityDifferencePlot,
  type ComparisonBaseline,
} from "@/components/results/utility-difference-plot";
import type { EvidenceCase, EvidenceIndex } from "@/lib/evidence";

type ResultsSectionProps = {
  evidence: EvidenceIndex;
};

function comparisonResult(item: EvidenceCase, baseline: ComparisonBaseline) {
  return baseline === "fixed"
    ? item.adaptive_vs_fixed
    : item.adaptive_vs_threshold;
}

function summaryFor(evidence: EvidenceIndex, baseline: ComparisonBaseline) {
  return baseline === "fixed"
    ? evidence.adaptive_vs_fixed
    : evidence.adaptive_vs_threshold;
}

export function ResultsSection({ evidence }: ResultsSectionProps) {
  const [baseline, setBaseline] = useState<ComparisonBaseline>("fixed");

  const counts = summaryFor(evidence, baseline);

  const buckets = useMemo(() => {
    const wins = evidence.cases.filter(
      (item) => comparisonResult(item, baseline) === "adaptive_higher_utility",
    );
    const neutral = evidence.cases.filter(
      (item) => comparisonResult(item, baseline) === "utility_neutral",
    );
    const losses = evidence.cases.filter(
      (item) => comparisonResult(item, baseline) === "adaptive_lower_utility",
    );

    return { wins, neutral, losses };
  }, [baseline, evidence.cases]);

  const baselineLabel =
    baseline === "fixed" ? "Fixed length" : "Static threshold";

  return (
    <section
      id="policy-results"
      className="border-b border-black/10 bg-[#f7f3ea] text-[#171714]"
    >
      <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
        <div className="grid gap-10 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-black/42">
              03 / What happened
            </p>
            <h2 className="mt-4 max-w-xl text-balance text-3xl font-semibold tracking-[-0.035em] text-[#171714] md:text-5xl">
              The adaptive policy was useful, not universal.
            </h2>
            <p className="mt-6 max-w-xl text-pretty text-lg leading-8 text-black/62">
              Compare adaptive scheduling against one baseline at a time. The zero line is
              deliberate: neutral outcomes remain evidence rather than disappearing between
              larger wins and losses.
            </p>
          </div>

          <div className="border-y border-black/10 py-6">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/30">
              Compare adaptive against
            </p>
            <div
              className="mt-4 flex flex-wrap gap-2"
              aria-label="Comparison baseline"
            >
              <button
                type="button"
                aria-pressed={baseline === "fixed"}
                onClick={() => setBaseline("fixed")}
                className={
                  baseline === "fixed"
                    ? "border-b border-rose-800 px-1 pb-2 text-sm font-semibold text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45"
                    : "border-b border-transparent px-1 pb-2 text-sm text-black/42 transition-colors hover:text-black/75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45"
                }
              >
                Fixed length
              </button>
              <button
                type="button"
                aria-pressed={baseline === "threshold"}
                onClick={() => setBaseline("threshold")}
                className={
                  baseline === "threshold"
                    ? "border-b border-rose-800 px-1 pb-2 text-sm font-semibold text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45"
                    : "border-b border-transparent px-1 pb-2 text-sm text-black/42 transition-colors hover:text-black/75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45"
                }
              >
                Static threshold
              </button>
            </div>

            <p className="mt-6 text-3xl font-semibold tracking-[-0.03em] text-[#171714]">
              {counts.adaptive_higher} wins · {counts.neutral} neutral ·{" "}
              {counts.adaptive_lower} loss
            </p>
            <p className="mt-2 text-sm text-black/42">
              Adaptive versus {baselineLabel.toLowerCase()}
            </p>
          </div>
        </div>

        <div className="mt-14">
          <UtilityDifferencePlot cases={evidence.cases} baseline={baseline} />
        </div>

        <div className="mt-10 grid gap-8 border-t border-black/10 pt-7 md:grid-cols-3">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-sky-900/70">
              Neutral is evidence
            </p>
            <p
              data-testid={baseline === "fixed" ? "fixed-neutral-cases" : "threshold-neutral-cases"}
              className="mt-3 text-sm leading-6 text-black/58"
            >
              {buckets.neutral.map((item) => item.case_id).join(" · ")}
            </p>
            <p className="mt-3 text-sm leading-6 text-black/40">
              Equal governed utility means the adaptive policy did not earn a win in those
              conditions.
            </p>
          </div>

          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-rose-900/75">
              The loss
            </p>
            <h3 className="mt-3 text-lg font-semibold text-[#171714]">
              MPC5-103 · Moderate load
            </h3>
            <p className="mt-3 text-sm leading-6 text-black/52">
              {evidence.cases.find((item) => item.case_id === "MPC5-103")?.plain_language_result}
            </p>
          </div>

          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-emerald-900/75">
              Clearest constrained-capacity wins
            </p>
            <h3 className="mt-3 text-lg font-semibold text-[#171714]">
              MPC5-104 + MPC5-105
            </h3>
            <p className="mt-3 text-sm leading-6 text-black/52">
              The adaptive policy avoided the large losses produced by the simpler baselines
              under saturated and jagged capacity.
            </p>
          </div>
        </div>

        <div className="sr-only" aria-live="polite">
          Wins: {buckets.wins.map((item) => item.case_id).join(", ")}. Neutral:{" "}
          {buckets.neutral.map((item) => item.case_id).join(", ")}. Losses:{" "}
          {buckets.losses.map((item) => item.case_id).join(", ")}.
        </div>

        <details className="group mt-14 border-t border-black/10 pt-6">
          <summary className="cursor-pointer list-none text-sm font-semibold text-black/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45">
            <span className="border-b border-black/20 pb-1 transition-colors group-open:border-rose-800/60">
              View exact values
            </span>
          </summary>
          <div className="mt-7">
            <PolicyCaseMatrix cases={evidence.cases} />
          </div>
        </details>
      </div>
    </section>
  );
}
