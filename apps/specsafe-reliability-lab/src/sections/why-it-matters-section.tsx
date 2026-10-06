import { ArrowDown, Check, X } from "lucide-react";

import { falseWinExplanation } from "@/content/explanations";

const withoutGate = [
  "A headline metric improves",
  "The change is treated as globally better",
  "The system is promoted",
] as const;

const withSpecSafe = [
  "A headline metric improves",
  "An independent reliability gate checks a different required property",
  "The hidden regression is retained and promotion is blocked",
] as const;

function Flow({
  label,
  items,
  safe,
}: {
  label: string;
  items: readonly string[];
  safe: boolean;
}) {
  const Icon = safe ? Check : X;

  return (
    <div className="border-t border-black/12 pt-5">
      <div className="flex items-center gap-2">
        <span
          className={
            safe
              ? "grid h-6 w-6 place-items-center rounded-full bg-emerald-900 text-white"
              : "grid h-6 w-6 place-items-center rounded-full bg-rose-800 text-white"
          }
        >
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        </span>
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-black/50">
          {label}
        </p>
      </div>

      <ol className="mt-7 space-y-3">
        {items.map((item, index) => (
          <li key={item}>
            <div className="grid grid-cols-[28px_1fr] gap-3">
              <span className="pt-0.5 font-mono text-xs text-black/32">
                0{index + 1}
              </span>
              <p className="text-base leading-7 text-black/72">{item}</p>
            </div>
            {index < items.length - 1 ? (
              <ArrowDown
                className="ml-[5px] mt-3 h-4 w-4 text-black/22"
                aria-hidden="true"
              />
            ) : null}
          </li>
        ))}
      </ol>
    </div>
  );
}

export function WhyItMattersSection() {
  return (
    <section
      id="why-it-matters"
      className="border-b border-black/10 bg-[#f2efe6] text-[#171714]"
    >
      <div className="mx-auto max-w-7xl px-5 py-16 md:px-8 md:py-24">
        <div className="grid gap-12 lg:grid-cols-[0.72fr_1.28fr]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-black/42">
              01 / Why this matters
            </p>
            <h2 className="mt-4 max-w-xl text-balance text-3xl font-semibold tracking-[-0.035em] text-black md:text-5xl">
              {falseWinExplanation.title}
            </h2>
            <p className="mt-6 max-w-xl text-pretty text-lg leading-8 text-black/62">
              {falseWinExplanation.summary}
            </p>
            <p className="mt-5 max-w-xl text-sm leading-7 text-black/48">
              {falseWinExplanation.detail}
            </p>
          </div>

          <div className="grid gap-10 md:grid-cols-2 md:gap-8">
            <Flow label="Without a reliability gate" items={withoutGate} safe={false} />
            <Flow label="With SpecSafe" items={withSpecSafe} safe />
          </div>
        </div>

        <div className="mt-14 border-t border-black/10 pt-6">
          <p className="max-w-4xl text-sm leading-7 text-black/48">
            The same failure pattern appears beyond verification scheduling: model updates,
            prompt changes, retrieval systems, agent policies, confidence thresholds, routing
            logic, and automated actions can all look better on one score while violating a
            different property required for safe release.
          </p>
        </div>
      </div>
    </section>
  );
}
