import { ArrowRight, Check, ShieldAlert, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { definitions } from "@/content/definitions";
import { confidenceGateExplanation } from "@/content/explanations";
import type { EvidenceIndex, EvidenceMetric } from "@/lib/evidence";
import { formatDecimal, formatSigned } from "@/lib/format";

type ConfidenceGateSectionProps = {
  evidence: EvidenceIndex;
};

function metricDirection(metric: EvidenceMetric) {
  if (metric.metric_key === "auroc") {
    return {
      before: formatDecimal(metric.raw_value),
      after: formatDecimal(metric.calibrated_value),
      movement: formatSigned(metric.movement),
      explanation: "Higher is better. The candidate became worse at ranking stronger predictions above weaker ones.",
    };
  }

  return {
    before: formatDecimal(metric.raw_value),
    after: formatDecimal(metric.calibrated_value),
    movement: formatSigned(metric.movement),
    explanation: "Lower is better. The candidate improved on this probability-quality metric.",
  };
}

export function ConfidenceGateSection({ evidence }: ConfidenceGateSectionProps) {
  const gate = evidence.calibration_gate;
  const improvedMetrics = gate.metrics.filter((metric) => metric.gate_result === "improved");
  const rankingMetric = gate.metrics.find((metric) => metric.metric_key === "auroc");

  if (!rankingMetric) {
    throw new Error("Frozen evidence is missing the ranking-safety metric.");
  }

  const ranking = metricDirection(rankingMetric);

  return (
    <section id="confidence-gate" className="border-b border-white/8 bg-background">
      <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
        <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-rose-200/70">
              04 / Hidden failure
            </p>
            <h2 className="mt-4 max-w-xl text-balance text-3xl font-semibold tracking-[-0.035em] text-white md:text-5xl">
              Calibration improved. Ranking safety failed.
            </h2>
            <p className="mt-6 max-w-xl text-pretty text-lg leading-8 text-white/58">
              {confidenceGateExplanation.summary}
            </p>
            <p className="mt-5 max-w-xl text-sm leading-7 text-white/42">
              {confidenceGateExplanation.detail}
            </p>
          </div>

          <div className="border-y border-white/10">
            <div className="grid gap-5 py-6 md:grid-cols-[112px_1fr_auto] md:items-center">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/30">
                Candidate
              </p>
              <div>
                <p className="text-lg font-semibold text-white">
                  Two probability metrics improved
                </p>
                <p className="mt-1 text-sm leading-6 text-white/42">
                  That was encouraging evidence, but not sufficient authorization.
                </p>
              </div>
              <Badge variant="success">Promising</Badge>
            </div>

            <div className="grid gap-5 border-t border-white/10 py-6 md:grid-cols-[112px_1fr_auto] md:items-center">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/30">
                Independent gate
              </p>
              <div>
                <p className="text-lg font-semibold text-white">
                  Ranking safety regressed
                </p>
                <p className="mt-1 text-sm leading-6 text-white/42">
                  The confidence signal became worse at preserving useful ordering.
                </p>
              </div>
              <Badge variant="danger">Failed</Badge>
            </div>

            <div className="grid gap-5 border-t border-white/10 py-6 md:grid-cols-[112px_1fr_auto] md:items-center">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/30">
                Decision
              </p>
              <div>
                <p className="font-mono text-base font-semibold text-white">
                  {gate.decision_outcome}
                </p>
                <p className="mt-1 text-sm leading-6 text-white/42">
                  Candidate retained as diagnostic evidence. Runtime control remains blocked.
                </p>
              </div>
              <Badge variant="danger">Activation blocked</Badge>
            </div>
          </div>
        </div>

        <div className="mt-16">
          <div className="grid gap-px bg-white/10 lg:grid-cols-3">
            {improvedMetrics.map((metric) => {
              const values = metricDirection(metric);

              return (
                <article key={metric.metric_key} className="bg-background p-6 md:p-7">
                  <div className="flex items-center justify-between gap-4">
                    <p className="text-sm font-semibold text-white">
                      {metric.display_name}
                    </p>
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-200">
                      <Check className="h-3.5 w-3.5" aria-hidden="true" />
                      Improved
                    </span>
                  </div>

                  <div className="mt-8 flex items-center gap-3">
                    <span className="font-mono text-lg text-white/42">
                      {values.before}
                    </span>
                    <ArrowRight className="h-4 w-4 text-white/24" aria-hidden="true" />
                    <span className="font-mono text-2xl font-semibold text-white">
                      {values.after}
                    </span>
                  </div>

                  <p className="mt-4 font-mono text-xs text-emerald-200/75">
                    movement {values.movement}
                  </p>
                  <p className="mt-4 text-sm leading-6 text-white/42">
                    {values.explanation}
                  </p>
                </article>
              );
            })}

            <article className="bg-rose-950/10 p-6 md:p-7">
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm font-semibold text-white">
                  {rankingMetric.display_name}
                </p>
                <span className="inline-flex items-center gap-1 text-xs font-medium text-rose-200">
                  <X className="h-3.5 w-3.5" aria-hidden="true" />
                  Gate failed
                </span>
              </div>

              <div className="mt-8 flex items-center gap-3">
                <span className="font-mono text-lg text-white/42">
                  {ranking.before}
                </span>
                <ArrowRight className="h-4 w-4 text-white/24" aria-hidden="true" />
                <span className="font-mono text-2xl font-semibold text-rose-100">
                  {ranking.after}
                </span>
              </div>

              <p className="mt-4 font-mono text-xs text-rose-200">
                movement {ranking.movement}
              </p>
              <p className="mt-4 text-sm leading-6 text-white/48">
                {ranking.explanation}
              </p>
            </article>
          </div>
        </div>

        <div className="mt-16 grid gap-10 border-t border-white/10 pt-8 lg:grid-cols-[0.78fr_1.22fr]">
          <div>
            <div className="flex items-center gap-2 text-rose-200">
              <ShieldAlert className="h-4 w-4" aria-hidden="true" />
              <p className="font-mono text-[11px] uppercase tracking-[0.18em]">
                Promotion boundary
              </p>
            </div>
            <h3 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-white">
              The regression was far outside tolerance.
            </h3>
            <p className="mt-4 max-w-lg text-sm leading-7 text-white/45">
              The stored AUROC delta is negative because ranking quality fell. The large positive
              multiple below is the magnitude of that degradation relative to the permitted limit,
              not an improvement score.
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            <div className="border-t border-white/15 pt-5">
              <p className="text-xs text-white/36">Maximum allowed degradation</p>
              <p className="mt-3 font-mono text-2xl font-semibold text-white">
                {gate.maximum_allowed_auroc_degradation}
              </p>
            </div>

            <div className="border-t border-rose-300/45 pt-5">
              <p className="text-xs text-white/36">Observed AUROC delta</p>
              <p className="mt-3 font-mono text-2xl font-semibold text-rose-100">
                {gate.observed_auroc_delta}
              </p>
            </div>

            <div className="border-t border-rose-300/45 pt-5">
              <p className="text-xs text-white/36">Degradation magnitude</p>
              <p className="mt-3 font-mono text-2xl font-semibold text-rose-100">
                {formatDecimal(gate.degradation_multiple_of_limit, 2)}×
              </p>
              <p className="mt-2 text-xs leading-5 text-white/34">
                permitted limit
              </p>
            </div>
          </div>
        </div>

        <div className="mt-16 grid gap-8 border-t border-white/10 pt-8 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-white/30">
              Why this gate exists
            </p>
            <h3 className="mt-4 text-2xl font-semibold tracking-[-0.02em] text-white">
              {definitions["ranking-safety"].term} is a separate requirement.
            </h3>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <p className="text-sm leading-7 text-white/55">
                {definitions["ranking-safety"].short}
              </p>
              <p className="mt-3 text-sm leading-7 text-white/38">
                {definitions["ranking-safety"].whyItMatters}
              </p>
            </div>
            <div>
              <p className="text-sm leading-7 text-white/55">
                {definitions["promotion-gate"].short}
              </p>
              <p className="mt-3 text-sm leading-7 text-white/38">
                {definitions["promotion-gate"].whyItMatters}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-16 border-l-2 border-rose-300/50 pl-5 md:pl-7">
          <p className="font-mono text-xs text-rose-200">
            {gate.failure_label}
          </p>
          <p className="mt-3 max-w-4xl text-xl font-semibold leading-8 text-white md:text-2xl">
            {gate.plain_language_result}
          </p>
          <p className="mt-4 text-sm text-white/38">
            Holdout: {gate.holdout_record_count} records · {gate.holdout_positive_count} positive ·{" "}
            {gate.holdout_negative_count} negative · status: {gate.confidence_status}
          </p>
        </div>
      </div>
    </section>
  );
}
