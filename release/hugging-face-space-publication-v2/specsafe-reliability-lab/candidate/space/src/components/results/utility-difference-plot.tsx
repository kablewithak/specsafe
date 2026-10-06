import type { EvidenceCase } from "@/lib/evidence";
import { humanizeIdentifier } from "@/lib/format";

export type ComparisonBaseline = "fixed" | "threshold";

type UtilityDifferencePlotProps = {
  cases: EvidenceCase[];
  baseline: ComparisonBaseline;
};

function comparatorUtility(item: EvidenceCase, baseline: ComparisonBaseline) {
  return baseline === "fixed" ? item.fixed_utility : item.threshold_utility;
}

function difference(item: EvidenceCase, baseline: ComparisonBaseline) {
  return item.adaptive_utility - comparatorUtility(item, baseline);
}

function formatDifference(value: number) {
  if (value === 0) return "0.0";
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
}

function outcomeLabel(value: number) {
  if (value > 0) return "Adaptive higher";
  if (value < 0) return "Adaptive lower";
  return "Neutral";
}

export function UtilityDifferencePlot({
  cases,
  baseline,
}: UtilityDifferencePlotProps) {
  const differences = cases.map((item) => difference(item, baseline));
  const maximumMagnitude = Math.max(1, ...differences.map((value) => Math.abs(value)));

  return (
    <div
      role="img"
      aria-label={`Adaptive utility difference compared with ${
        baseline === "fixed" ? "fixed length" : "static threshold"
      } across six governed cases. Negative values are worse, zero is neutral, and positive values are better.`}
    >
      <div className="grid grid-cols-[minmax(112px,0.72fr)_minmax(180px,1.6fr)_52px] items-end gap-3 border-b border-black/10 pb-3 text-[10px] uppercase tracking-[0.14em] text-black/30 md:grid-cols-[minmax(180px,0.78fr)_minmax(320px,1.8fr)_72px]">
        <span>Case</span>
        <div className="grid grid-cols-3">
          <span>Lower</span>
          <span className="text-center">Neutral</span>
          <span className="text-right">Higher</span>
        </div>
        <span className="text-right">Delta</span>
      </div>

      <div className="divide-y divide-black/8">
        {cases.map((item) => {
          const delta = difference(item, baseline);
          const width = `${(Math.abs(delta) / maximumMagnitude) * 50}%`;
          const positive = delta > 0;
          const negative = delta < 0;

          return (
            <div
              key={item.case_id}
              className="grid grid-cols-[minmax(112px,0.72fr)_minmax(180px,1.6fr)_52px] items-center gap-3 py-5 md:grid-cols-[minmax(180px,0.78fr)_minmax(320px,1.8fr)_72px]"
            >
              <div className="min-w-0">
                <p className="font-mono text-xs font-semibold text-[#171714]">
                  {item.case_id}
                </p>
                <p className="mt-1 truncate text-xs text-black/40">
                  {humanizeIdentifier(item.capacity_profile)}
                </p>
              </div>

              <div className="relative h-7" aria-hidden="true">
                <div className="absolute inset-y-0 left-1/2 w-px bg-black/18" />

                {positive ? (
                  <div
                    className="absolute left-1/2 top-1/2 h-2 -translate-y-1/2 bg-emerald-700/75"
                    style={{ width }}
                  />
                ) : null}

                {negative ? (
                  <div
                    className="absolute right-1/2 top-1/2 h-2 -translate-y-1/2 bg-rose-700/75"
                    style={{ width }}
                  />
                ) : null}

                {delta === 0 ? (
                  <div className="absolute left-1/2 top-1/2 h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-sky-700 bg-[#f7f3ea]" />
                ) : null}
              </div>

              <div className="text-right">
                <p
                  className={
                    positive
                      ? "font-mono text-sm font-semibold text-emerald-800"
                      : negative
                        ? "font-mono text-sm font-semibold text-rose-800"
                        : "font-mono text-sm font-semibold text-sky-800"
                  }
                >
                  {formatDifference(delta)}
                </p>
                <span className="sr-only">{outcomeLabel(delta)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
