import { useId, useState } from "react";

import {
  definitions,
  type Definition,
  type DefinitionId,
} from "@/content/definitions";

const defaultTerms = [
  "verification",
  "confidence",
  "capacity",
  "causal-information",
] as const satisfies readonly DefinitionId[];

type DefinitionExplorerProps = {
  terms?: readonly DefinitionId[];
};

function DefinitionPanel({ definition, panelId }: { definition: Definition; panelId: string }) {
  return (
    <div
      id={panelId}
      role="region"
      aria-live="polite"
      className="border-t border-black/10 pt-5"
    >
      <p className="text-lg font-semibold tracking-[-0.015em] text-[#171714]">
        {definition.term}
      </p>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-black/64">
        {definition.short}
      </p>
      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/32">
            Technical meaning
          </p>
          <p className="mt-2 text-sm leading-6 text-black/50">
            {definition.technical}
          </p>
        </div>
        {definition.whyItMatters ? (
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-black/32">
              Why it matters here
            </p>
            <p className="mt-2 text-sm leading-6 text-black/50">
              {definition.whyItMatters}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function DefinitionExplorer({
  terms = defaultTerms,
}: DefinitionExplorerProps) {
  const [activeId, setActiveId] = useState<DefinitionId>(terms[0] ?? "verification");
  const panelId = useId();

  const activeDefinition = definitions[activeId];

  return (
    <div>
      <div
        className="flex flex-wrap gap-x-5 gap-y-2"
        aria-label="Core concept definitions"
      >
        {terms.map((id) => {
          const definition = definitions[id];
          const active = id === activeId;

          return (
            <button
              key={id}
              type="button"
              aria-pressed={active}
              aria-controls={panelId}
              onClick={() => setActiveId(id)}
              className={
                active
                  ? "border-b border-rose-800 pb-1 text-sm font-medium text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45"
                  : "border-b border-transparent pb-1 text-sm text-black/42 transition-colors hover:text-black/75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45"
              }
            >
              {definition.term}
            </button>
          );
        })}
      </div>

      <div className="mt-5">
        <DefinitionPanel definition={activeDefinition} panelId={panelId} />
      </div>
    </div>
  );
}
