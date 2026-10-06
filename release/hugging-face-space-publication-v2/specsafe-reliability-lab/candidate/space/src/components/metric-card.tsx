import { ArrowDownRight, ArrowUpRight, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { EvidenceMetric } from "@/lib/evidence";
import { formatDecimal, formatSigned } from "@/lib/format";

export function MetricCard({ metric }: { metric: EvidenceMetric }) {
  const passed = metric.gate_result === "improved";
  const DirectionIcon = metric.movement >= 0 ? ArrowDownRight : ArrowUpRight;

  return (
    <Card className={passed ? "border-emerald-400/15" : "border-rose-400/35 bg-rose-950/15"}>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-white/58">{metric.display_name}</p>
          <h3 className="mt-2 text-2xl font-semibold text-white">{formatDecimal(metric.calibrated_value)}</h3>
        </div>
        <Badge variant={passed ? "success" : "danger"}>
          {passed ? "Improved" : "Gate failed"}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-2xl bg-white/[0.04] p-3">
            <p className="text-white/45">Before</p>
            <p className="mt-1 font-mono text-white/82">{formatDecimal(metric.raw_value)}</p>
          </div>
          <div className="rounded-2xl bg-white/[0.04] p-3">
            <p className="text-white/45">Movement</p>
            <p className="mt-1 flex items-center gap-1 font-mono text-white/82">
              {passed ? <DirectionIcon className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4 text-rose-300" />}
              {formatSigned(metric.movement)}
            </p>
          </div>
        </div>
        <p className="text-sm leading-6 text-white/48">
          {metric.lower_is_better ? "Lower is better for this metric." : "Higher is better for this metric."}
        </p>
      </CardContent>
    </Card>
  );
}
