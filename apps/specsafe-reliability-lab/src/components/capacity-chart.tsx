import type { EvidenceCase } from "@/lib/evidence";

const SERIES = [
  { key: "fixed_utility", label: "Fixed length", fill: "#77808f" },
  { key: "threshold_utility", label: "Static threshold", fill: "#d7a954" },
  { key: "adaptive_utility", label: "Adaptive", fill: "#53c7b8" },
] as const;

const WIDTH = 960;
const HEIGHT = 390;
const MARGIN = { top: 28, right: 24, bottom: 68, left: 54 };
const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right;
const PLOT_HEIGHT = HEIGHT - MARGIN.top - MARGIN.bottom;
const DOMAIN_MIN = -14;
const DOMAIN_MAX = 4;
const GRID_VALUES = [4, 0, -4, -8, -12];

function yPosition(value: number) {
  return MARGIN.top + ((DOMAIN_MAX - value) / (DOMAIN_MAX - DOMAIN_MIN)) * PLOT_HEIGHT;
}

export function CapacityChart({ cases }: { cases: EvidenceCase[] }) {
  const groupWidth = PLOT_WIDTH / cases.length;
  const barWidth = Math.min(32, groupWidth / 4.5);
  const zeroY = yPosition(0);

  return (
    <figure className="rounded-2xl border border-white/8 bg-black/20 p-3 md:p-5">
      <svg
        className="h-auto w-full"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-labelledby="utility-chart-title utility-chart-description"
      >
        <title id="utility-chart-title">Utility comparison across six governed capacity cases</title>
        <desc id="utility-chart-description">
          Grouped bars compare fixed length, static threshold, and adaptive policy utility for cases
          MPC5-101 through MPC5-106. The adaptive policy loses on MPC5-103 and avoids large losses on
          MPC5-104 and MPC5-105.
        </desc>

        {GRID_VALUES.map((value) => {
          const y = yPosition(value);
          return (
            <g key={value}>
              <line
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={y}
                y2={y}
                stroke={value === 0 ? "rgba(255,255,255,0.28)" : "rgba(255,255,255,0.08)"}
              />
              <text
                x={MARGIN.left - 12}
                y={y + 4}
                fill="rgba(255,255,255,0.46)"
                fontSize="12"
                textAnchor="end"
              >
                {value}
              </text>
            </g>
          );
        })}

        {cases.map((item, caseIndex) => {
          const center = MARGIN.left + groupWidth * caseIndex + groupWidth / 2;
          const seriesWidth = SERIES.length * barWidth + (SERIES.length - 1) * 6;
          const startX = center - seriesWidth / 2;

          return (
            <g key={item.case_id}>
              {SERIES.map((series, seriesIndex) => {
                const value = item[series.key];
                const valueY = yPosition(value);
                const y = value >= 0 ? valueY : zeroY;
                const height = Math.max(1, Math.abs(zeroY - valueY));
                const x = startX + seriesIndex * (barWidth + 6);

                return (
                  <rect
                    key={series.key}
                    x={x}
                    y={y}
                    width={barWidth}
                    height={height}
                    rx="5"
                    fill={series.fill}
                  >
                    <title>{`${item.case_id}, ${series.label}: ${value}`}</title>
                  </rect>
                );
              })}
              <text
                x={center}
                y={HEIGHT - 42}
                fill="rgba(255,255,255,0.58)"
                fontSize="12"
                textAnchor="middle"
              >
                {item.case_id}
              </text>
            </g>
          );
        })}
      </svg>

      <figcaption className="flex flex-wrap justify-center gap-x-6 gap-y-2 border-t border-white/8 pt-4 text-xs text-white/58">
        {SERIES.map((series) => (
          <span key={series.key} className="inline-flex items-center gap-2">
            <span
              className="h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: series.fill }}
              aria-hidden="true"
            />
            {series.label}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
