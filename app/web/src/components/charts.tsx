// Small SVG charts in the app palette: grouped bars, lines, stacked bars. Each has hover and a legend.
import { useState, type ReactNode } from "react";

export interface Series {
  key: string;
  label: string;
  color: string;
}

function Legend({ series }: { series: Series[] }) {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-ink-2">
      {series.map((s) => (
        <li key={s.key} className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm ring-1 ring-espresso/15" style={{ background: s.color }} />
          {s.label}
        </li>
      ))}
    </ul>
  );
}

function Tooltip({ x, y, children }: { x: number; y: number; children: ReactNode }) {
  return (
    <div
      className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-xl border border-line bg-page px-3 py-2 text-xs shadow-[var(--shadow-soft)]"
      style={{ left: `${x}%`, top: `${y}%` }}
    >
      {children}
    </div>
  );
}

const W = 720;

export function GroupedBars({
  categories,
  series,
  values,
  max = 1,
  format,
}: {
  categories: string[];
  series: Series[];
  values: (number | null)[][]; // [series][category]
  max?: number;
  format: (v: number) => string;
}) {
  const [hover, setHover] = useState<[number, number] | null>(null);
  const H = 280, top = 12, bottom = 34, left = 40;
  const plotH = H - top - bottom, groupW = (W - left) / categories.length;
  const barW = Math.min(28, (groupW * 0.72) / series.length);
  const gap = 3;
  const y = (v: number) => top + plotH * (1 - v / max);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => t * max);
  const tip = hover && values[hover[0]][hover[1]] !== null ? hover : null;
  return (
    <div>
      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Grouped bar chart" onMouseLeave={() => setHover(null)}>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={left} x2={W} y1={y(t)} y2={y(t)} stroke="var(--line)" strokeWidth={1} />
              <text x={left - 8} y={y(t) + 4} textAnchor="end" className="fill-[var(--ink-2)] text-[11px]">
                {format(t)}
              </text>
            </g>
          ))}
          {categories.map((c, ci) => {
            const gx = left + ci * groupW + (groupW - series.length * (barW + gap)) / 2;
            return (
              <g key={c}>
                {series.map((s, si) => {
                  const v = values[si][ci];
                  if (v === null) return null;
                  const active = !hover || (hover[0] === si && hover[1] === ci);
                  return (
                    <rect
                      key={s.key}
                      x={gx + si * (barW + gap)}
                      y={y(v)}
                      width={barW}
                      height={Math.max(1, y(0) - y(v))}
                      rx={4}
                      fill={s.color}
                      stroke="rgb(58 42 36 / 0.18)"
                      strokeWidth={1}
                      opacity={active ? 1 : 0.4}
                      className="ease"
                      onMouseEnter={() => setHover([si, ci])}
                    />
                  );
                })}
                <text x={left + ci * groupW + groupW / 2} y={H - 10} textAnchor="middle" className="fill-[var(--ink)] text-[12px]">
                  {c}
                </text>
              </g>
            );
          })}
        </svg>
        {tip && (
          <Tooltip
            x={((left + tip[1] * groupW + groupW / 2) / W) * 100}
            y={(y(values[tip[0]][tip[1]]!) / H) * 100}
          >
            <span className="font-medium">{series[tip[0]].label}</span>
            <span className="text-ink-2"> · {categories[tip[1]]}: </span>
            {format(values[tip[0]][tip[1]]!)}
          </Tooltip>
        )}
      </div>
      <div className="mt-3">
        <Legend series={series} />
      </div>
    </div>
  );
}

export function LineChart({
  xs,
  series,
  values,
  format,
  xLabel,
}: {
  xs: number[];
  series: Series[];
  values: number[][]; // [series][x]
  format: (v: number) => string;
  xLabel: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const H = 240, top = 12, bottom = 34, left = 48, right = 12;
  const all = values.flat();
  const lo = Math.min(0, ...all), hi = Math.max(...all) * 1.05 || 1;
  const x = (i: number) => left + ((W - left - right) * i) / Math.max(1, xs.length - 1);
  const y = (v: number) => top + (H - top - bottom) * (1 - (v - lo) / (hi - lo));
  const ticks = [0, 0.5, 1].map((t) => lo + t * (hi - lo));
  return (
    <div>
      <div className="relative">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full"
          role="img"
          aria-label="Line chart"
          onMouseMove={(e) => {
            const r = e.currentTarget.getBoundingClientRect();
            const px = ((e.clientX - r.left) / r.width) * W;
            const i = Math.round(((px - left) / (W - left - right)) * (xs.length - 1));
            setHover(Math.max(0, Math.min(xs.length - 1, i)));
          }}
          onMouseLeave={() => setHover(null)}
        >
          {ticks.map((t) => (
            <g key={t}>
              <line x1={left} x2={W - right} y1={y(t)} y2={y(t)} stroke="var(--line)" />
              <text x={left - 8} y={y(t) + 4} textAnchor="end" className="fill-[var(--ink-2)] text-[16px]">
                {format(t)}
              </text>
            </g>
          ))}
          {xs.map((v, i) =>
            i % Math.ceil(xs.length / 10) === 0 || i === xs.length - 1 ? (
              <text key={i} x={x(i)} y={H - 10} textAnchor="middle" className="fill-[var(--ink-2)] text-[16px]">
                {v}
              </text>
            ) : null,
          )}
          {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={top} y2={H - bottom} stroke="var(--ink-2)" strokeDasharray="3 3" />}
          {series.map((s, si) => (
            <g key={s.key}>
              <polyline
                fill="none"
                stroke={s.color}
                strokeWidth={2}
                strokeLinejoin="round"
                points={values[si].map((v, i) => `${x(i)},${y(v)}`).join(" ")}
              />
              {hover !== null && <circle cx={x(hover)} cy={y(values[si][hover])} r={4.5} fill={s.color} stroke="var(--page)" strokeWidth={2} />}
            </g>
          ))}
        </svg>
        {hover !== null && (
          <Tooltip x={(x(hover) / W) * 100} y={(top / H) * 100 + 4}>
            <span className="text-ink-2">
              {xLabel} {xs[hover]}
            </span>
            {series.map((s, si) => (
              <span key={s.key} className="block">
                {s.label}: <span className="font-medium">{format(values[si][hover])}</span>
              </span>
            ))}
          </Tooltip>
        )}
      </div>
      {series.length > 1 && (
        <div className="mt-2">
          <Legend series={series} />
        </div>
      )}
    </div>
  );
}

export function StackedBars({
  rows,
  parts,
  values,
}: {
  rows: string[];
  parts: Series[];
  values: number[][]; // [row][part], shares of all examples
}) {
  const [hover, setHover] = useState<[number, number] | null>(null);
  return (
    <div>
      <div className="space-y-3" onMouseLeave={() => setHover(null)}>
        {rows.map((r, ri) => {
          const total = values[ri].reduce((a, b) => a + b, 0);
          return (
            <div key={r} className="grid grid-cols-[7rem_1fr_3.5rem] items-center gap-3">
              <span className="text-sm">{r}</span>
              <div className="flex h-5 gap-[2px] overflow-hidden rounded-md">
                {parts.map((p, pi) => (
                  <div
                    key={p.key}
                    title={`${p.label}: ${(100 * values[ri][pi]).toFixed(1)}%`}
                    onMouseEnter={() => setHover([ri, pi])}
                    className="ease h-full"
                    style={{
                      width: `${(100 * values[ri][pi]) / Math.max(total, 1e-9)}%`,
                      background: p.color,
                      opacity: hover && !(hover[0] === ri && hover[1] === pi) ? 0.45 : 1,
                    }}
                  />
                ))}
              </div>
              <span className="text-end text-xs tabular-nums text-ink-2">{(100 * total).toFixed(1)}%</span>
            </div>
          );
        })}
      </div>
      <p className="mt-3 h-4 text-xs text-ink-2" aria-live="polite">
        {hover ? `${rows[hover[0]]}, ${parts[hover[1]].label}: ${(100 * values[hover[0]][hover[1]]).toFixed(1)}% of dev` : "Bars show the share of dev examples with each error; the total is the error rate."}
      </p>
      <div className="mt-2">
        <Legend series={parts} />
      </div>
    </div>
  );
}
