import { useState } from "react";
import { cx } from "./ui";

type Part = { text: string; kind: "fn" | "arg" | "val" | "punct" | "plain" };

// alarm_set(time="five am", date="friday") -> coloured parts; anything unexpected stays plain
export function highlight(call: string): Part[] {
  const m = /^([A-Za-z_]\w*)\(/.exec(call);
  if (!m) return [{ text: call, kind: "plain" }];
  const parts: Part[] = [{ text: m[1], kind: "fn" }, { text: "(", kind: "punct" }];
  let i = m[0].length;
  const arg = /\s*(,\s*)?([A-Za-z_]\w*)(=)"((?:[^"\\]|\\.)*)"/y;
  while (i < call.length) {
    arg.lastIndex = i;
    const a = arg.exec(call);
    if (!a) break;
    if (a[1]) parts.push({ text: ", ", kind: "punct" });
    parts.push({ text: a[2], kind: "arg" }, { text: "=", kind: "punct" }, { text: `"${a[4]}"`, kind: "val" });
    i = arg.lastIndex;
  }
  const rest = call.slice(i);
  if (rest) parts.push({ text: rest, kind: rest === ")" ? "punct" : "plain" });
  return parts;
}

const COLORS: Record<Part["kind"], string> = {
  fn: "text-fn font-medium",
  arg: "text-arg",
  val: "text-val",
  punct: "text-ink-2",
  plain: "text-ink",
};

export function CallText({ call, className }: { call: string; className?: string }) {
  return (
    <code dir="ltr" className={cx("font-mono text-[0.92rem] leading-relaxed break-words", className)}>
      {highlight(call).map((p, i) => (
        <span key={i} className={COLORS[p.kind]}>
          {p.text}
        </span>
      ))}
    </code>
  );
}

export function CallView({ call }: { call: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(call);
    setCopied(true);
    setTimeout(() => setCopied(false), 1400);
  };
  return (
    <div className="group relative rounded-2xl border border-line bg-card-soft px-4 py-3 pe-20">
      <CallText call={call} />
      <button
        onClick={copy}
        aria-label="Copy the call"
        className="ease label absolute end-3 top-3 rounded-full border border-line px-2.5 py-1 hover:border-terracotta hover:text-ink"
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}
