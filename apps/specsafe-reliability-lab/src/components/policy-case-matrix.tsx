import { Badge } from "@/components/ui/badge";
import type { EvidenceCase } from "@/lib/evidence";
import { humanizeIdentifier } from "@/lib/format";

function outcomeVariant(result: EvidenceCase["adaptive_vs_fixed"]) {
  if (result === "adaptive_higher_utility") return "success" as const;
  if (result === "adaptive_lower_utility") return "danger" as const;
  return "neutral" as const;
}

function outcomeLabel(result: EvidenceCase["adaptive_vs_fixed"]) {
  if (result === "adaptive_higher_utility") return "Adaptive higher";
  if (result === "adaptive_lower_utility") return "Adaptive lower";
  return "Neutral";
}

function utility(value: number) {
  return value.toFixed(1);
}

export function PolicyCaseMatrix({ cases }: { cases: EvidenceCase[] }) {
  return (
    <section
      aria-labelledby="case-matrix-title"
      className="overflow-hidden rounded-3xl border border-white/10 bg-black/20"
    >
      <div className="border-b border-white/8 p-6 md:p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-white/40">
          Exact case comparison
        </p>
        <h3 id="case-matrix-title" className="mt-3 text-2xl font-semibold text-white">
          Utility by governed capacity condition
        </h3>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-white/52">
          Every value comes from the frozen evidence index. Neutral rows remain explicit because equal utility is part of the result, not an empty chart state.
        </p>
      </div>

      <div className="hidden overflow-x-auto md:block">
        <table className="w-full border-collapse text-left text-sm">
          <caption className="sr-only">
            Fixed length, static threshold, and adaptive utility across all six governed cases.
          </caption>
          <thead className="bg-white/[0.025] text-xs uppercase tracking-[0.12em] text-white/42">
            <tr>
              <th scope="col" className="px-6 py-4 font-medium">Case</th>
              <th scope="col" className="px-4 py-4 font-medium">Capacity</th>
              <th scope="col" className="px-4 py-4 text-right font-medium">Fixed</th>
              <th scope="col" className="px-4 py-4 text-right font-medium">Threshold</th>
              <th scope="col" className="px-4 py-4 text-right font-medium">Adaptive</th>
              <th scope="col" className="px-6 py-4 font-medium">Outcome vs fixed</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((item) => (
              <tr
                key={item.case_id}
                className="border-t border-white/8 align-top transition hover:bg-white/[0.025]"
              >
                <th scope="row" className="px-6 py-5 font-mono text-sm font-medium text-white">
                  {item.case_id}
                </th>
                <td className="px-4 py-5">
                  <p className="font-medium text-white/80">{humanizeIdentifier(item.capacity_profile)}</p>
                  <p className="mt-1 max-w-xs text-xs leading-5 text-white/42">
                    {item.plain_language_result}
                  </p>
                </td>
                <td className="px-4 py-5 text-right font-mono text-white/70">
                  {utility(item.fixed_utility)}
                </td>
                <td className="px-4 py-5 text-right font-mono text-amber-100/80">
                  {utility(item.threshold_utility)}
                </td>
                <td className="px-4 py-5 text-right font-mono font-semibold text-emerald-200">
                  {utility(item.adaptive_utility)}
                </td>
                <td className="px-6 py-5">
                  <Badge variant={outcomeVariant(item.adaptive_vs_fixed)}>
                    {outcomeLabel(item.adaptive_vs_fixed)}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="divide-y divide-white/8 md:hidden">
        {cases.map((item) => (
          <article key={item.case_id} className="space-y-4 p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-mono text-sm text-white">{item.case_id}</p>
                <h4 className="mt-1 font-semibold text-white/82">
                  {humanizeIdentifier(item.capacity_profile)}
                </h4>
              </div>
              <Badge variant={outcomeVariant(item.adaptive_vs_fixed)}>
                {outcomeLabel(item.adaptive_vs_fixed)}
              </Badge>
            </div>
            <dl className="grid grid-cols-3 gap-2">
              <div className="rounded-xl border border-white/8 bg-white/[0.025] p-3">
                <dt className="text-[11px] uppercase tracking-[0.12em] text-white/38">Fixed</dt>
                <dd className="mt-1 font-mono text-white/75">{utility(item.fixed_utility)}</dd>
              </div>
              <div className="rounded-xl border border-amber-200/10 bg-amber-200/[0.025] p-3">
                <dt className="text-[11px] uppercase tracking-[0.12em] text-white/38">Threshold</dt>
                <dd className="mt-1 font-mono text-amber-100/80">{utility(item.threshold_utility)}</dd>
              </div>
              <div className="rounded-xl border border-emerald-200/10 bg-emerald-200/[0.025] p-3">
                <dt className="text-[11px] uppercase tracking-[0.12em] text-white/38">Adaptive</dt>
                <dd className="mt-1 font-mono font-semibold text-emerald-200">
                  {utility(item.adaptive_utility)}
                </dd>
              </div>
            </dl>
            <p className="text-sm leading-6 text-white/52">{item.plain_language_result}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
