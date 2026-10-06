import { Check, LockKeyhole, X } from "lucide-react";

import { DefinitionExplorer } from "@/components/concepts/definition-explorer";
import {
  causalBoundaryExplanation,
  comparisonExplanation,
  projectExplanation,
} from "@/content/explanations";
import type { EvidenceIndex } from "@/lib/evidence";

type UnderstandSystemSectionProps = {
  evidence: EvidenceIndex;
};

const permittedInputs = [
  "Current confidence",
  "Current capacity",
  "Decision-time trace information",
] as const;

const forbiddenInputs = [
  "Future correctness",
  "Later outcomes",
  "Retrospective labels",
] as const;

export function UnderstandSystemSection({
  evidence,
}: UnderstandSystemSectionProps) {
  return (
    <section
      id="north-star"
      className="border-b border-black/10 bg-[#ebe7dc] text-[#171714]"
    >
      <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
        <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-black/42">
              02 / Understand the system
            </p>
            <h2 className="mt-4 max-w-xl text-balance text-3xl font-semibold tracking-[-0.035em] text-[#171714] md:text-5xl">
              One question. Three policies. One causal boundary.
            </h2>
            <p className="mt-6 max-w-xl text-pretty text-lg leading-8 text-black/62">
              {projectExplanation.summary}
            </p>
            <p className="mt-5 max-w-xl text-sm leading-7 text-black/48">
              {projectExplanation.detail}
            </p>
          </div>

          <div className="divide-y divide-black/10 border-y border-black/10">
            <div className="grid gap-3 py-6 md:grid-cols-[96px_1fr]">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/30">
                Question
              </p>
              <h3 className="text-xl font-semibold tracking-[-0.02em] text-[#171714]">
                Can adaptive verification spend compute more intelligently?
              </h3>
            </div>
            <div className="grid gap-3 py-6 md:grid-cols-[96px_1fr]">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/30">
                Method
              </p>
              <h3 className="text-xl font-semibold tracking-[-0.02em] text-[#171714]">
                Compare three policies on the same six governed cases.
              </h3>
            </div>
            <div className="grid gap-3 py-6 md:grid-cols-[96px_1fr]">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/30">
                Answer
              </p>
              <h3 className="text-xl font-semibold tracking-[-0.02em] text-[#171714]">
                Sometimes useful. Not safe to activate.
              </h3>
            </div>
          </div>
        </div>

        <div className="mt-20 border-t border-black/10 pt-8">
          <div className="grid gap-8 lg:grid-cols-[0.8fr_1.2fr]">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-black/32">
                Core concepts
              </p>
              <h3 className="mt-3 text-2xl font-semibold tracking-[-0.025em] text-[#171714]">
                Learn only what you need, when you need it.
              </h3>
              <p className="mt-3 max-w-lg text-sm leading-7 text-black/45">
                These definitions explain the decision boundary. Exact measurements and
                outcomes remain in the frozen evidence contract.
              </p>
            </div>
            <DefinitionExplorer />
          </div>
        </div>

        <div className="mt-20">
          <div className="max-w-3xl">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-black/32">
              What was tested
            </p>
            <h3 className="mt-3 text-3xl font-semibold tracking-[-0.03em] text-[#171714]">
              {comparisonExplanation.title}
            </h3>
            <p className="mt-4 text-base leading-7 text-black/52">
              {comparisonExplanation.summary}
            </p>
          </div>

          <div className="mt-10 border-y border-black/10">
            <div className="grid lg:grid-cols-[0.8fr_1.25fr_0.8fr_0.9fr]">
              <div className="border-b border-black/10 py-6 lg:border-b-0 lg:border-r lg:pr-6">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/28">
                  Input
                </p>
                <p className="mt-3 text-base font-medium text-[#171714]">
                  Frozen trace
                </p>
                <p className="mt-2 text-sm leading-6 text-black/44">
                  The underlying case stays fixed across policy comparisons.
                </p>
              </div>

              <div className="border-b border-black/10 py-6 lg:border-b-0 lg:border-r lg:px-6">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/28">
                  Decision
                </p>
                <div className="mt-4 divide-y divide-black/8">
                  {evidence.policies.map((policy) => (
                    <div
                      key={policy.policy_key}
                      className="grid gap-2 py-4 first:pt-0 md:grid-cols-[140px_1fr]"
                    >
                      <p className="text-sm font-semibold text-[#171714]">
                        {policy.display_name}
                      </p>
                      <p className="text-sm leading-6 text-black/46">
                        {policy.plain_language_description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-b border-black/10 py-6 lg:border-b-0 lg:border-r lg:px-6">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/28">
                  Action
                </p>
                <p className="mt-3 text-base font-medium text-[#171714]">
                  Verification effort
                </p>
                <p className="mt-2 text-sm leading-6 text-black/44">
                  Each policy decides how much checking work to spend.
                </p>
              </div>

              <div className="py-6 lg:pl-6">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/28">
                  Evaluation
                </p>
                <p className="mt-3 text-base font-medium text-[#171714]">
                  Governed utility
                </p>
                <p className="mt-2 text-sm leading-6 text-black/44">
                  Outcomes are compared only after the decision has been made.
                </p>
              </div>
            </div>
          </div>

          <p className="mt-5 max-w-3xl text-sm leading-7 text-black/40">
            {comparisonExplanation.detail}
          </p>
        </div>

        <div className="mt-20 grid gap-10 border-t border-black/10 pt-8 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <div className="flex items-center gap-2 text-black/58">
              <LockKeyhole className="h-4 w-4" aria-hidden="true" />
              <p className="font-mono text-[11px] uppercase tracking-[0.18em]">
                Causal boundary
              </p>
            </div>
            <h3 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-[#171714]">
              {causalBoundaryExplanation.title}
            </h3>
            <p className="mt-4 max-w-lg text-base leading-7 text-black/52">
              {causalBoundaryExplanation.summary}
            </p>
            <p className="mt-4 max-w-lg text-sm leading-7 text-black/40">
              {causalBoundaryExplanation.detail}
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2">
            <div className="border-t border-emerald-800/35 pt-5">
              <div className="flex items-center gap-2 text-emerald-900">
                <Check className="h-4 w-4" aria-hidden="true" />
                <p className="text-sm font-semibold">Allowed at decision time</p>
              </div>
              <ul className="mt-5 space-y-3">
                {permittedInputs.map((item) => (
                  <li
                    key={item}
                    className="border-b border-black/8 pb-3 text-sm text-black/58 last:border-0"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="border-t border-rose-800/35 pt-5">
              <div className="flex items-center gap-2 text-rose-900">
                <X className="h-4 w-4" aria-hidden="true" />
                <p className="text-sm font-semibold">Forbidden because it knows the future</p>
              </div>
              <ul className="mt-5 space-y-3">
                {forbiddenInputs.map((item) => (
                  <li
                    key={item}
                    className="border-b border-black/8 pb-3 text-sm text-black/58 last:border-0"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
