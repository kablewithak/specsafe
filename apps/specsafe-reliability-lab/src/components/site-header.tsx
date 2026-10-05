import { Ban } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { primaryNavigation } from "@/content/navigation";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/8 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 md:px-8">
        <a
          href="#overview"
          className="group inline-flex items-center gap-3 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          <span
            className="h-2.5 w-2.5 rounded-full bg-amber-200 shadow-[0_0_0_4px_rgba(253,230,138,0.08)]"
            aria-hidden="true"
          />
          <span className="flex items-baseline gap-2">
            <span className="text-sm font-semibold tracking-[-0.01em] text-white">SpecSafe</span>
            <span className="hidden text-xs text-white/38 sm:inline">Reliability evidence lab</span>
          </span>
        </a>

        <Badge variant="danger" className="shrink-0 gap-2">
          <Ban className="h-3.5 w-3.5" aria-hidden="true" />
          Activation blocked
        </Badge>
      </div>

      <div className="border-t border-white/[0.06]">
        <nav
          aria-label="Primary navigation"
          className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-3 py-2 [scrollbar-width:none] md:px-6 [&::-webkit-scrollbar]:hidden"
        >
          {primaryNavigation.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="group flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/52 transition-colors hover:bg-white/[0.04] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300"
            >
              <span className="font-mono text-[10px] tracking-[0.14em] text-white/28 transition-colors group-hover:text-amber-200/70">
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
