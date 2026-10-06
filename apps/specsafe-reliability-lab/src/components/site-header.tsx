import { Ban } from "lucide-react";

import { primaryNavigation } from "@/content/navigation";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-black/10 bg-[#f2efe6]/95 text-[#171714] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 md:px-8">
        <a
          href="#overview"
          className="group inline-flex items-center gap-3 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45 focus-visible:ring-offset-2 focus-visible:ring-offset-[#f2efe6]"
        >
          <span
            className="h-2.5 w-2.5 rounded-full bg-[#171714] shadow-[0_0_0_4px_rgba(23,23,20,0.06)]"
            aria-hidden="true"
          />
          <span className="flex items-baseline gap-2">
            <span className="text-sm font-semibold tracking-[-0.01em] text-[#171714]">
              SpecSafe
            </span>
            <span className="hidden text-xs text-black/38 sm:inline">
              Reliability evidence lab
            </span>
          </span>
        </a>

        <span className="inline-flex shrink-0 items-center gap-2 rounded-full border border-rose-800/20 bg-rose-800/[0.055] px-3 py-1 text-xs font-semibold tracking-wide text-rose-900">
          <Ban className="h-3.5 w-3.5" aria-hidden="true" />
          Activation blocked
        </span>
      </div>

      <div className="border-t border-black/[0.06]">
        <nav
          aria-label="Primary navigation"
          className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-3 py-2 [scrollbar-width:none] md:px-6 [&::-webkit-scrollbar]:hidden"
        >
          {primaryNavigation.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="group flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm text-black/55 transition-colors hover:bg-black/[0.04] hover:text-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-700/45"
            >
              <span className="font-mono text-[10px] tracking-[0.14em] text-black/28 transition-colors group-hover:text-rose-800/75">
                {item.number}
              </span>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
