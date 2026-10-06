import {
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";

import { SiteHeader } from "@/components/site-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { loadEvidence, type EvidenceIndex } from "@/lib/evidence";
import { HeroSection } from "@/sections/hero-section";
import { UnderstandSystemSection } from "@/sections/understand-system-section";
import { ResultsSection } from "@/sections/results-section";
import { ConfidenceGateSection } from "@/sections/confidence-gate-section";
import { FindingsSection } from "@/sections/findings-section";
import { EvidenceExplorerSection } from "@/sections/evidence-explorer-section";
import { WhyItMattersSection } from "@/sections/why-it-matters-section";

function LoadingState() {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-6 text-foreground">
      <div className="space-y-4 text-center">
        <div className="mx-auto h-10 w-10 animate-pulse rounded-full border border-amber-300/40 bg-amber-300/10" />
        <p className="text-sm text-white/55">Loading frozen evidence…</p>
      </div>
    </main>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <main className="grid min-h-screen place-items-center bg-background px-6 text-foreground">
      <Card className="max-w-xl border-rose-400/30 bg-rose-950/15">
        <CardHeader>
          <Badge variant="danger">Evidence load failed</Badge>
          <h1 className="text-2xl font-semibold">The interface failed closed.</h1>
        </CardHeader>
        <CardContent>
          <p className="text-white/60">{message}</p>
        </CardContent>
      </Card>
    </main>
  );
}

function AppContent({ evidence }: { evidence: EvidenceIndex }) {
  return (
    <>
      <a
        href="#main-content"
        className="fixed left-4 top-4 z-50 -translate-y-24 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-black transition focus:translate-y-0"
      >
        Skip to main content
      </a>
      <div className="min-h-screen overflow-x-clip bg-background text-foreground">
        <SiteHeader />

        <main id="main-content">
          <HeroSection evidence={evidence} />
          <WhyItMattersSection />
          <UnderstandSystemSection evidence={evidence} />

          <ResultsSection evidence={evidence} />

          <ConfidenceGateSection evidence={evidence} />

          <FindingsSection evidence={evidence} />

          <EvidenceExplorerSection evidence={evidence} />

        </main>

        <footer className="border-t border-white/8 px-5 py-10 md:px-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-5 text-sm text-white/42 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-200/70" />
              Read-only evidence surface. No live inference. No user input.
            </div>
            <p>SpecSafe · {evidence.space_id}</p>
          </div>
        </footer>
      </div>
    </>
  );
}

export default function App() {
  const [evidence, setEvidence] = useState<EvidenceIndex | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void loadEvidence(controller.signal)
      .then(setEvidence)
      .catch((caught: unknown) => {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        setError(caught instanceof Error ? caught.message : "Unknown evidence error.");
      });
    return () => controller.abort();
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!evidence) return <LoadingState />;
  return <AppContent evidence={evidence} />;
}
