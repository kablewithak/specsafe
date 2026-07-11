import {
  ArrowRight,
  Ban,
  CheckCircle2,
  Database,
  ExternalLink,
  FileCheck2,
  Gauge,
  GitCommitHorizontal,
  Info,
  LockKeyhole,
  Scale,
  ShieldAlert,
  Sparkles,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";

import { MetricCard } from "@/components/metric-card";
import { PolicyCaseMatrix } from "@/components/policy-case-matrix";
import { SectionHeading } from "@/components/section-heading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { loadEvidence, type EvidenceIndex } from "@/lib/evidence";
import { formatDecimal, shortHash } from "@/lib/format";

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

function ResultCount({ label, value, tone }: { label: string; value: number; tone: "win" | "neutral" | "loss" }) {
  const styles = {
    win: "border-emerald-300/18 bg-emerald-400/[0.07] text-emerald-100",
    neutral: "border-sky-200/18 bg-sky-200/[0.07] text-sky-100",
    loss: "border-rose-300/18 bg-rose-400/[0.07] text-rose-100",
  } as const;

  return (
    <div className={`rounded-2xl border p-4 text-center ${styles[tone]}`}>
      <p className="text-3xl font-semibold">{value}</p>
      <p className="mt-1 text-xs uppercase tracking-[0.16em] text-white/48">{label}</p>
    </div>
  );
}

function AppContent({ evidence }: { evidence: EvidenceIndex }) {
  const fixedWins = evidence.cases.filter(
    (item) => item.adaptive_vs_fixed === "adaptive_higher_utility",
  );
  const fixedNeutral = evidence.cases.filter(
    (item) => item.adaptive_vs_fixed === "utility_neutral",
  );
  const fixedLosses = evidence.cases.filter(
    (item) => item.adaptive_vs_fixed === "adaptive_lower_utility",
  );
  const thresholdWins = evidence.cases.filter(
    (item) => item.adaptive_vs_threshold === "adaptive_higher_utility",
  );
  const thresholdNeutral = evidence.cases.filter(
    (item) => item.adaptive_vs_threshold === "utility_neutral",
  );
  const thresholdLosses = evidence.cases.filter(
    (item) => item.adaptive_vs_threshold === "adaptive_lower_utility",
  );

  return (
    <TooltipProvider delayDuration={180}>
      <a
        href="#main-content"
        className="fixed left-4 top-4 z-50 -translate-y-24 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-black transition focus:translate-y-0"
      >
        Skip to main content
      </a>
      <div className="min-h-screen overflow-x-hidden bg-background text-foreground">
        <header className="sticky top-0 z-40 border-b border-white/8 bg-background/78 backdrop-blur-xl">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 md:px-8">
            <a
              href="#overview"
              className="group flex items-center gap-3 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300"
            >
              <span className="grid h-9 w-9 place-items-center rounded-xl border border-amber-300/25 bg-amber-300/10 font-mono text-sm font-semibold text-amber-100">
                SS
              </span>
              <span>
                <span className="block text-sm font-semibold text-white">SpecSafe</span>
                <span className="hidden text-xs text-white/42 sm:block">Reliability evidence lab</span>
              </span>
            </a>
            <nav
              aria-label="Primary navigation"
              className="hidden items-center gap-6 text-sm text-white/55 md:flex"
            >
              <a className="hover:text-white" href="#north-star">North star</a>
              <a className="hover:text-white" href="#policy-results">Results</a>
              <a className="hover:text-white" href="#confidence-gate">Safety gate</a>
              <a className="hover:text-white" href="#evidence">Evidence</a>
            </nav>
            <Badge variant="danger" className="gap-2">
              <Ban className="h-3.5 w-3.5" aria-hidden="true" />
              Activation blocked
            </Badge>
          </div>
        </header>

        <main id="main-content">
          <section id="overview" className="relative isolate overflow-hidden border-b border-white/8">
            <div className="absolute inset-0 -z-10 bg-grid opacity-40" />
            <div className="absolute left-1/2 top-0 -z-10 h-[620px] w-[900px] -translate-x-1/2 rounded-full bg-amber-300/[0.07] blur-3xl" />
            <div className="mx-auto grid max-w-7xl gap-10 px-5 pb-20 pt-16 md:px-8 md:pb-28 md:pt-24 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
              <div className="space-y-8">
                <div className="flex flex-wrap gap-2">
                  {evidence.maturity_labels.map((label) => (
                    <Badge key={label}>{label}</Badge>
                  ))}
                </div>
                <div className="space-y-5">
                  <p className="font-mono text-xs uppercase tracking-[0.24em] text-amber-200/80">
                    Causal confidence-scheduled verification
                  </p>
                  <h1 className="max-w-5xl text-balance text-5xl font-semibold leading-[0.98] tracking-[-0.045em] text-white md:text-7xl">
                    When should AI spend more compute?
                  </h1>
                  <p className="max-w-3xl text-pretty text-lg leading-8 text-white/62 md:text-xl">
                    {evidence.tested_question}
                  </p>
                </div>
                <div className="max-w-3xl rounded-3xl border border-amber-200/14 bg-amber-200/[0.04] p-6 md:p-7">
                  <p className="font-mono text-xs uppercase tracking-[0.18em] text-amber-200/70">
                    Short answer
                  </p>
                  <p className="mt-3 text-lg leading-8 text-white/82">{evidence.quick_summary}</p>
                </div>
                <div className="flex flex-wrap gap-3 text-sm">
                  <a
                    href="#north-star"
                    className="inline-flex items-center gap-2 rounded-xl bg-amber-200 px-4 py-3 font-semibold text-zinc-950 transition hover:bg-amber-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  >
                    Start with the question <ArrowRight className="h-4 w-4" />
                  </a>
                  <a
                    href="#confidence-gate"
                    className="inline-flex items-center gap-2 rounded-xl border border-white/12 bg-white/[0.04] px-4 py-3 font-semibold text-white transition hover:bg-white/[0.08] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300"
                  >
                    Why activation failed <ShieldAlert className="h-4 w-4" />
                  </a>
                </div>
              </div>

              <Card className="overflow-hidden border-rose-400/30 bg-rose-950/20">
                <CardHeader className="border-b border-rose-300/10 bg-rose-400/[0.05]">
                  <div className="flex items-center justify-between gap-4">
                    <Badge variant="danger">Hard gate</Badge>
                    <LockKeyhole className="h-5 w-5 text-rose-200" aria-hidden="true" />
                  </div>
                  <h2 className="pt-4 text-3xl font-semibold tracking-tight text-white">Do not activate.</h2>
                  <p className="text-sm leading-6 text-white/55">
                    Better probability estimates were not enough. Ranking safety regressed beyond the declared limit.
                  </p>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  <div className="flex items-end justify-between gap-4">
                    <div>
                      <p className="text-sm text-white/48">Observed safety breach</p>
                      <p className="mt-2 text-5xl font-semibold tracking-tight text-rose-200">
                        {formatDecimal(evidence.calibration_gate.degradation_multiple_of_limit, 2)}×
                      </p>
                      <p className="mt-2 text-xs uppercase tracking-[0.18em] text-white/42">
                        the permitted degradation
                      </p>
                    </div>
                    <XCircle className="h-12 w-12 text-rose-300/80" aria-hidden="true" />
                  </div>
                  <div className="grid gap-3 border-t border-white/8 pt-5 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
                    <div>
                      <p className="text-xs text-white/42">Decision</p>
                      <p className="mt-1 font-mono text-sm text-white">
                        {evidence.calibration_gate.decision_outcome}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-white/42">Failure label</p>
                      <p className="mt-1 font-mono text-sm text-rose-200">
                        {evidence.calibration_gate.failure_label}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </section>

          <section id="north-star" className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
            <SectionHeading
              eyebrow="01 / North star"
              title="Spend compute where it helps—without cheating."
              description="SpecSafe was built to test one reliability question before any adaptive policy earns the right to control verification work."
            />
            <div className="mt-10 grid gap-5 lg:grid-cols-3">
              <Card className="border-amber-300/18 bg-amber-300/[0.04]">
                <CardHeader>
                  <Gauge className="h-6 w-6 text-amber-200" aria-hidden="true" />
                  <p className="pt-5 font-mono text-xs uppercase tracking-[0.18em] text-amber-200/70">
                    Question
                  </p>
                  <h2 className="text-2xl font-semibold text-white">
                    Can adaptive verification spend compute more intelligently?
                  </h2>
                </CardHeader>
                <CardContent>
                  <p className="leading-7 text-white/58">
                    It may use current calibrated confidence and current capacity, but never future outcomes or retrospective answers.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <Scale className="h-6 w-6 text-sky-200" aria-hidden="true" />
                  <p className="pt-5 font-mono text-xs uppercase tracking-[0.18em] text-sky-200/70">
                    Method
                  </p>
                  <h2 className="text-2xl font-semibold text-white">
                    Compare three policies on the same six governed cases.
                  </h2>
                </CardHeader>
                <CardContent>
                  <p className="leading-7 text-white/58">
                    Fixed length, static threshold, and adaptive scheduling face identical conditions. Unsafe retrospective controls stay excluded.
                  </p>
                </CardContent>
              </Card>
              <Card className="border-rose-300/18 bg-rose-400/[0.04]">
                <CardHeader>
                  <ShieldAlert className="h-6 w-6 text-rose-200" aria-hidden="true" />
                  <p className="pt-5 font-mono text-xs uppercase tracking-[0.18em] text-rose-200/70">
                    Answer
                  </p>
                  <h2 className="text-2xl font-semibold text-white">
                    Sometimes useful. Not safe to activate.
                  </h2>
                </CardHeader>
                <CardContent>
                  <p className="leading-7 text-white/58">
                    Adaptive scheduling helped in constrained conditions, stayed neutral in several cases, and lost once. The real confidence candidate then failed ranking safety.
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="mt-16">
              <div className="max-w-3xl">
                <p className="font-mono text-xs uppercase tracking-[0.2em] text-white/38">
                  The three policies
                </p>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white">
                  One decision-time boundary. Three ways to spend verification work.
                </h2>
              </div>
              <div className="mt-8 grid gap-5 md:grid-cols-3">
                {evidence.policies.map((policy, index) => (
                  <Card
                    key={policy.policy_key}
                    className={policy.capacity_aware ? "border-emerald-300/20 bg-emerald-950/10" : undefined}
                  >
                    <CardHeader>
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-mono text-xs text-white/35">0{index + 1}</span>
                        <Badge variant={policy.capacity_aware ? "success" : "neutral"}>
                          {policy.capacity_aware ? "Capacity-aware" : "Fixed rule"}
                        </Badge>
                      </div>
                      <h3 className="pt-8 text-2xl font-semibold text-white">{policy.display_name}</h3>
                    </CardHeader>
                    <CardContent>
                      <p className="leading-7 text-white/55">{policy.plain_language_description}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </section>

          <section id="policy-results" className="border-y border-white/8 bg-white/[0.018]">
            <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
              <SectionHeading
                eyebrow="02 / Policy results"
                title="The adaptive policy was useful, not universal."
                description="The result is mixed by design: wins, neutral cases, and the loss must all remain legible at the same time."
              />

              <Card className="mt-10 overflow-hidden">
                <CardHeader className="border-b border-white/8">
                  <p className="font-mono text-xs uppercase tracking-[0.18em] text-white/40">
                    Outcome scoreboard
                  </p>
                  <h3 className="text-2xl font-semibold text-white">How adaptive scheduling compared</h3>
                  <p className="max-w-3xl text-sm leading-6 text-white/52">
                    Neutral is not missing data. It means the adaptive policy produced the same governed utility as the comparator.
                  </p>
                </CardHeader>
                <CardContent className="space-y-6 pt-6">
                  <div className="grid gap-4 lg:grid-cols-[1fr_1.35fr] lg:items-center">
                    <div>
                      <p className="text-sm text-white/48">Adaptive versus fixed length</p>
                      <p className="mt-2 text-2xl font-semibold text-white">2 wins · 3 neutral · 1 loss</p>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <ResultCount label="Wins" value={evidence.adaptive_vs_fixed.adaptive_higher} tone="win" />
                      <ResultCount label="Neutral" value={evidence.adaptive_vs_fixed.neutral} tone="neutral" />
                      <ResultCount label="Loss" value={evidence.adaptive_vs_fixed.adaptive_lower} tone="loss" />
                    </div>
                  </div>
                  <div className="h-px bg-white/8" />
                  <div className="grid gap-4 lg:grid-cols-[1fr_1.35fr] lg:items-center">
                    <div>
                      <p className="text-sm text-white/48">Adaptive versus static threshold</p>
                      <p className="mt-2 text-2xl font-semibold text-white">3 wins · 2 neutral · 1 loss</p>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <ResultCount label="Wins" value={evidence.adaptive_vs_threshold.adaptive_higher} tone="win" />
                      <ResultCount label="Neutral" value={evidence.adaptive_vs_threshold.neutral} tone="neutral" />
                      <ResultCount label="Loss" value={evidence.adaptive_vs_threshold.adaptive_lower} tone="loss" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="mt-6 grid gap-5 lg:grid-cols-2">
                <Card>
                  <CardHeader>
                    <Badge>Against fixed length</Badge>
                    <h3 className="pt-3 text-xl font-semibold text-white">Every case bucket, named explicitly</h3>
                  </CardHeader>
                  <CardContent className="space-y-4 text-sm">
                    <p className="leading-6 text-white/58">
                      <span className="font-semibold text-emerald-200">Wins:</span>{" "}
                      {fixedWins.map((item) => item.case_id).join(" · ")}
                    </p>
                    <p data-testid="fixed-neutral-cases" className="leading-6 text-white/58">
                      <span className="font-semibold text-sky-200">Neutral:</span>{" "}
                      {fixedNeutral.map((item) => item.case_id).join(" · ")}
                    </p>
                    <p className="leading-6 text-white/58">
                      <span className="font-semibold text-rose-200">Loss:</span>{" "}
                      {fixedLosses.map((item) => item.case_id).join(" · ")}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <Badge>Against static threshold</Badge>
                    <h3 className="pt-3 text-xl font-semibold text-white">The adversarial case becomes an extra win</h3>
                  </CardHeader>
                  <CardContent className="space-y-4 text-sm">
                    <p className="leading-6 text-white/58">
                      <span className="font-semibold text-emerald-200">Wins:</span>{" "}
                      {thresholdWins.map((item) => item.case_id).join(" · ")}
                    </p>
                    <p className="leading-6 text-white/58">
                      <span className="font-semibold text-sky-200">Neutral:</span>{" "}
                      {thresholdNeutral.map((item) => item.case_id).join(" · ")}
                    </p>
                    <p className="leading-6 text-white/58">
                      <span className="font-semibold text-rose-200">Loss:</span>{" "}
                      {thresholdLosses.map((item) => item.case_id).join(" · ")}
                    </p>
                  </CardContent>
                </Card>
              </div>

              <div className="mt-8">
                <PolicyCaseMatrix cases={evidence.cases} />
              </div>

              <div className="mt-8 grid gap-5 md:grid-cols-3">
                <Card className="border-sky-200/16 bg-sky-200/[0.035]">
                  <CardHeader>
                    <Badge variant="neutral">Why neutral matters</Badge>
                    <h3 className="pt-3 text-xl font-semibold text-white">No forced winner</h3>
                  </CardHeader>
                  <CardContent>
                    <p className="leading-7 text-white/58">
                      Three cases matched fixed length exactly. Keeping them visible prevents a few dramatic wins from becoming a universal claim.
                    </p>
                  </CardContent>
                </Card>
                <Card className="border-rose-400/25 bg-rose-950/15">
                  <CardHeader>
                    <Badge variant="danger">The loss</Badge>
                    <h3 className="pt-3 text-xl font-semibold text-white">MPC5-103 · Moderate load</h3>
                  </CardHeader>
                  <CardContent>
                    <p className="leading-7 text-white/58">
                      {fixedLosses[0]?.plain_language_result}
                    </p>
                  </CardContent>
                </Card>
                <Card className="border-emerald-400/18 bg-emerald-950/10">
                  <CardHeader>
                    <Badge variant="success">The clearest wins</Badge>
                    <h3 className="pt-3 text-xl font-semibold text-white">MPC5-104 and MPC5-105</h3>
                  </CardHeader>
                  <CardContent>
                    <p className="leading-7 text-white/58">
                      Adaptive scheduling avoided the large losses produced by fixed rules under saturated and jagged capacity.
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </section>

          <section id="confidence-gate" className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
            <SectionHeading
              eyebrow="03 / Confidence gate"
              title="Calibration improved. Ranking safety failed."
              description={evidence.calibration_gate.plain_language_result}
            />
            <div className="mt-10 grid gap-5 lg:grid-cols-3">
              {evidence.calibration_gate.metrics.map((metric) => (
                <MetricCard key={metric.metric_key} metric={metric} />
              ))}
            </div>
            <Card className="mt-8 overflow-hidden border-rose-400/30 bg-gradient-to-br from-rose-950/30 to-card/70">
              <div className="grid gap-8 p-7 md:p-9 lg:grid-cols-[0.65fr_1.35fr] lg:items-center">
                <div>
                  <p className="font-mono text-xs uppercase tracking-[0.22em] text-rose-200/75">Activation rule</p>
                  <p className="mt-4 text-6xl font-semibold tracking-[-0.05em] text-white">
                    {formatDecimal(evidence.calibration_gate.degradation_multiple_of_limit, 2)}×
                  </p>
                  <p className="mt-2 text-sm text-white/48">worse than the maximum permitted AUROC degradation</p>
                </div>
                <div className="space-y-5">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
                      <p className="text-xs text-white/42">Allowed degradation</p>
                      <p className="mt-2 font-mono text-xl text-white">
                        {evidence.calibration_gate.maximum_allowed_auroc_degradation}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-rose-300/15 bg-rose-400/[0.05] p-4">
                      <p className="text-xs text-white/42">Observed delta</p>
                      <p className="mt-2 font-mono text-xl text-rose-200">
                        {evidence.calibration_gate.observed_auroc_delta}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-3 rounded-2xl border border-rose-300/15 bg-rose-400/[0.06] p-4">
                    <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-rose-200" />
                    <p className="text-sm leading-6 text-white/65">
                      The system kept the candidate as diagnostic evidence and forced the conservative fallback. It did not promote a threshold or scheduler.
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </section>

          <section id="what-it-means" className="border-y border-white/8 bg-white/[0.018]">
            <div className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
              <SectionHeading
                eyebrow="04 / What it means"
                title="Reliability is the gate, not the average score."
                description={evidence.final_interpretation}
              />
              <div className="mt-10 grid gap-5 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <Scale className="h-6 w-6 text-amber-200" aria-hidden="true" />
                    <h3 className="pt-5 text-xl font-semibold text-white">Mixed evidence is still useful</h3>
                  </CardHeader>
                  <CardContent>
                    <p className="leading-7 text-white/55">
                      The adaptive policy earned real wins, but one loss prevents a global-winner claim.
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <LockKeyhole className="h-6 w-6 text-amber-200" aria-hidden="true" />
                    <h3 className="pt-5 text-xl font-semibold text-white">Safety gates must be independent</h3>
                  </CardHeader>
                  <CardContent>
                    <p className="leading-7 text-white/55">
                      A model can improve calibration metrics and still become less safe for ranking-driven automation.
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <FileCheck2 className="h-6 w-6 text-amber-200" aria-hidden="true" />
                    <h3 className="pt-5 text-xl font-semibold text-white">Negative evidence is a deliverable</h3>
                  </CardHeader>
                  <CardContent>
                    <p className="leading-7 text-white/55">
                      Blocking activation is a successful reliability outcome when the promotion contract is breached.
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </section>

          <section id="evidence" className="mx-auto max-w-7xl px-5 py-20 md:px-8 md:py-28">
            <SectionHeading
              eyebrow="05 / Evidence explorer"
              title="Inspect the boundary, not just the headline."
              description="The interface is read-only. It displays one frozen, hash-bound evidence contract and does not run inference or collect input."
            />
            <Tabs defaultValue="boundary" className="mt-10">
              <TabsList aria-label="Evidence views">
                <TabsTrigger value="boundary">Boundary</TabsTrigger>
                <TabsTrigger value="claims">Claims</TabsTrigger>
                <TabsTrigger value="sources">Sources</TabsTrigger>
                <TabsTrigger value="dataset">Dataset</TabsTrigger>
              </TabsList>
              <TabsContent value="boundary">
                <div className="grid gap-5 md:grid-cols-3">
                  <Card>
                    <CardHeader>
                      <Gauge className="h-5 w-5 text-amber-200" />
                      <p className="pt-4 text-sm text-white/45">Valid causal comparisons</p>
                      <p className="text-4xl font-semibold text-white">{evidence.valid_causal_comparisons}</p>
                    </CardHeader>
                  </Card>
                  <Card>
                    <CardHeader>
                      <Ban className="h-5 w-5 text-amber-200" />
                      <p className="pt-4 text-sm text-white/45">Unsafe controls excluded</p>
                      <p className="text-4xl font-semibold text-white">
                        {evidence.unsafe_retrospective_controls_excluded}
                      </p>
                    </CardHeader>
                  </Card>
                  <Card>
                    <CardHeader>
                      <Database className="h-5 w-5 text-amber-200" />
                      <p className="pt-4 text-sm text-white/45">User input collected</p>
                      <p className="text-4xl font-semibold text-white">
                        {evidence.user_input_collection ? "Yes" : "No"}
                      </p>
                    </CardHeader>
                  </Card>
                </div>
              </TabsContent>
              <TabsContent value="claims">
                <div className="grid gap-5 lg:grid-cols-2">
                  <Card className="border-emerald-400/18">
                    <CardHeader>
                      <Badge variant="success">Supported</Badge>
                      <h3 className="text-xl font-semibold text-white">What the evidence can say</h3>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-4">
                        {evidence.supported_claims.map((claim) => (
                          <li key={claim} className="flex gap-3 text-sm leading-6 text-white/58">
                            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />
                            {claim}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                  <Card className="border-rose-400/18">
                    <CardHeader>
                      <Badge variant="danger">Not established</Badge>
                      <h3 className="text-xl font-semibold text-white">What the evidence cannot say</h3>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-4">
                        {evidence.non_claims.map((claim) => (
                          <li key={claim} className="flex gap-3 text-sm leading-6 text-white/58">
                            <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-300" />
                            {claim}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              <TabsContent value="sources">
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm text-white/45">Frozen schema</p>
                        <h3 className="mt-2 font-mono text-sm text-white/80">{evidence.schema_version}</h3>
                      </div>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <button
                            type="button"
                            className="rounded-lg p-2 text-white/45 hover:bg-white/5 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300"
                            aria-label="Evidence source explanation"
                          >
                            <Info className="h-5 w-5" />
                          </button>
                        </TooltipTrigger>
                        <TooltipContent>
                          SHA-256 identities are displayed in shortened form here. The frozen JSON retains the complete values.
                        </TooltipContent>
                      </Tooltip>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {evidence.source_artifacts.map((source) => (
                      <div
                        key={source.relative_path}
                        className="grid gap-2 rounded-2xl border border-white/8 bg-black/20 p-4 md:grid-cols-[1fr_auto] md:items-center"
                      >
                        <code className="break-all text-xs text-white/62">{source.relative_path}</code>
                        <code className="text-xs text-amber-100/72">{shortHash(source.sha256)}</code>
                      </div>
                    ))}
                    <div className="flex items-center gap-2 pt-3 text-xs text-white/40">
                      <GitCommitHorizontal className="h-4 w-4" />
                      Source commit {evidence.source_commit}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="dataset">
                <Card>
                  <CardHeader>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="success">Public</Badge>
                      <Badge>Ungated</Badge>
                      <Badge>{evidence.dataset_publication.exact_file_count} exact files</Badge>
                    </div>
                    <h3 className="pt-4 text-2xl font-semibold text-white">
                      {evidence.dataset_publication.repository_id}
                    </h3>
                    <p className="text-white/52">
                      Anonymous public verification passed against revision {evidence.dataset_publication.published_revision}.
                    </p>
                  </CardHeader>
                  <CardContent>
                    <a
                      href={evidence.dataset_publication.repository_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 rounded-xl border border-white/12 bg-white/[0.04] px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/[0.08] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-300"
                    >
                      Open the Dataset <ExternalLink className="h-4 w-4" />
                    </a>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </section>
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
    </TooltipProvider>
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
