// "Under the hood": confidence, token chips and the attention heatmap of one turn.
import { useState } from "react";
import type { Attention, Locale, Token } from "../api";
import { cx } from "./ui";

export function ConfidenceMeter({ value, threshold }: { value: number | null; threshold: number }) {
  if (value === null) return <p className="text-sm text-ink-2">No confidence for a malformed call.</p>;
  const level = value < threshold ? "low" : value < threshold + (1 - threshold) / 2 ? "medium" : "high";
  const fill = { low: "bg-rosewood", medium: "bg-apricot", high: "bg-olive" }[level];
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="font-display text-3xl">{value.toFixed(3)}</span>
        <span className="label">{level === "low" ? "below threshold" : `${level} confidence`}</span>
      </div>
      <div
        className="relative mt-2 h-2 rounded-full bg-card-soft"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={1}
        aria-valuenow={value}
        aria-label="Confidence"
      >
        <div className={cx("ease h-2 rounded-full", fill)} style={{ width: `${Math.max(2, value * 100)}%` }} />
        <div
          className="absolute -top-1 h-4 w-px bg-ink"
          style={{ left: `${threshold * 100}%` }}
          title={`threshold ${threshold}`}
        />
      </div>
      <p className="mt-1.5 text-xs text-ink-2">The line marks the threshold ({threshold}). Below it the agent asks first.</p>
    </div>
  );
}

export function TokenChips({ tokens }: { tokens: Token[] }) {
  const hasCopy = tokens.some((t) => t.source !== null);
  return (
    <div>
      <div dir="ltr" className="flex flex-wrap gap-1.5">
        {tokens.map((t, i) => (
          <span
            key={i}
            title={`p = ${t.prob.toFixed(3)}${t.p_gen === null ? "" : `, p_gen = ${t.p_gen.toFixed(2)}`}`}
            className={cx(
              "ease rounded-lg px-2 py-0.5 font-mono text-xs",
              t.source === "copied" && "bg-olive text-linen",
              t.source === "generated" && "bg-apricot text-espresso",
              t.source === null && "border border-line bg-card-soft text-ink",
            )}
          >
            {t.token}
          </span>
        ))}
      </div>
      {hasCopy ? (
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-ink-2">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded bg-olive" /> copied from the input (p_gen &lt; 0.5)
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded bg-apricot" /> generated from the vocabulary
          </span>
        </div>
      ) : (
        <p className="mt-3 text-xs text-ink-2">This model has no copy mechanism: every token is generated.</p>
      )}
    </div>
  );
}

export function AttentionHeatmap({ attention, locale }: { attention: Attention; locale: Locale }) {
  const [hover, setHover] = useState<[number, number] | null>(null);
  const { src_tokens: src, tgt_tokens: tgt, weights } = attention;
  const rtl = locale === "ar-SA";
  const cols = `minmax(5.5rem, auto) repeat(${src.length}, minmax(2.25rem, 1fr))`;
  const hovered = hover ? `${tgt[hover[0]]}  ->  ${src[hover[1]]}: ${weights[hover[0]][hover[1]].toFixed(2)}` : null;
  return (
    <div>
      <div className="overflow-x-auto pb-1">
        <div
          role="grid"
          aria-label="Attention weights, output tokens by input words"
          className="grid gap-[2px] text-xs"
          style={{ gridTemplateColumns: cols }}
          onMouseLeave={() => setHover(null)}
          dir="ltr"
        >
          <div />
          {(rtl ? [...src.keys()].reverse() : [...src.keys()]).map((j) => (
            <div
              key={`h${j}`}
              dir="auto"
              className={cx("ease truncate px-1 pb-1 text-center text-ink-2", hover?.[1] === j && "font-semibold text-ink")}
              title={src[j]}
            >
              {src[j]}
            </div>
          ))}
          {tgt.map((t, i) => (
            <Row
              key={i}
              i={i}
              token={t}
              order={rtl ? [...src.keys()].reverse() : [...src.keys()]}
              weights={weights[i]}
              hover={hover}
              setHover={setHover}
            />
          ))}
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between gap-4 text-xs text-ink-2">
        <span aria-live="polite" className="font-mono">{hovered ?? "Hover a cell to see its weight."}</span>
        <span className="inline-flex shrink-0 items-center gap-2">
          0
          <span className="h-2 w-20 rounded-full" style={{ background: "linear-gradient(90deg, var(--heat-low), var(--heat-high))" }} />
          1
        </span>
      </div>
    </div>
  );
}

function Row({
  i,
  token,
  order,
  weights,
  hover,
  setHover,
}: {
  i: number;
  token: string;
  order: number[];
  weights: number[];
  hover: [number, number] | null;
  setHover: (h: [number, number]) => void;
}) {
  return (
    <>
      <div className={cx("ease truncate pe-2 text-end font-mono", hover?.[0] === i ? "text-ink" : "text-ink-2")} title={token}>
        {token}
      </div>
      {order.map((j) => {
        const w = weights[j];
        const active = hover !== null && (hover[0] === i || hover[1] === j);
        return (
          <div
            key={j}
            role="gridcell"
            aria-label={`${token} to input ${j}: ${w.toFixed(2)}`}
            onMouseEnter={() => setHover([i, j])}
            className={cx("ease h-6 rounded-[4px]", hover && !active && "opacity-45")}
            style={{ background: `color-mix(in oklab, var(--heat-high) ${Math.round(w * 100)}%, var(--heat-low))` }}
          />
        );
      })}
    </>
  );
}
