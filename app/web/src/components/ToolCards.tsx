import type { ReactNode } from "react";
import { Button, Label } from "./ui";

type R = Record<string, unknown>;
const s = (v: unknown) => (v === null || v === undefined || v === "" ? null : String(v));

function Shell({ kind, children }: { kind: string; children: ReactNode }) {
  return (
    <div dir="ltr" className="ease mt-3 rounded-2xl border border-line bg-page p-4 text-start">
      <Label>{kind}</Label>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

function formatDate(iso: string | null) {
  if (!iso) return null;
  const d = new Date(`${iso}T12:00:00`);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });
}

function Alarm({ r }: { r: R }) {
  return (
    <Shell kind="Alarm set">
      <p className="font-display text-4xl leading-none">{s(r.time)}</p>
      <p className="mt-1 text-sm text-ink-2">{formatDate(s(r.date)) ?? "Next time it comes round"}</p>
    </Shell>
  );
}

function Weather({ r }: { r: R }) {
  const live = r.source === "Open-Meteo";
  return (
    <Shell kind={live ? "Forecast" : "Forecast, offline estimate"}>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="font-display text-2xl leading-tight">{s(r.place)}</p>
          <p className="text-sm text-ink-2">{formatDate(s(r.date)) ?? "Today"}</p>
        </div>
        <p className="font-display text-4xl leading-none">
          {r.temp_max_c !== undefined ? `${Math.round(Number(r.temp_max_c))}°` : `${s(r.temp_c)}°`}
          {r.temp_min_c !== undefined && <span className="text-2xl text-ink-2"> / {Math.round(Number(r.temp_min_c))}°</span>}
        </p>
      </div>
      <p className="mt-2 text-sm first-letter:uppercase">
        {s(r.condition)}
        {r.precipitation_chance !== undefined && r.precipitation_chance !== null && (
          <span className="text-ink-2">, {String(r.precipitation_chance)}% chance of rain</span>
        )}
      </p>
      {s(r.note) && <p className="mt-1 text-xs text-ink-2">{s(r.note)}</p>}
      {live && <p className="mt-2 text-xs text-ink-2">Data from Open-Meteo</p>}
    </Shell>
  );
}

function Calendar({ r }: { r: R }) {
  return (
    <Shell kind="Added to calendar">
      <p className="font-display text-2xl leading-tight first-letter:uppercase">{s(r.event_name)}</p>
      <p className="text-sm text-ink-2">
        {formatDate(s(r.date))}
        {s(r.time) && `, ${s(r.time)}`}
      </p>
    </Shell>
  );
}

function NowPlaying({ r }: { r: R }) {
  const title = s(r.song) ?? s(r.playlist) ?? (s(r.genre) ? `${s(r.genre)} mix` : "Shuffle");
  return (
    <Shell kind="Now playing">
      <div className="flex items-center gap-4">
        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-terracotta">
          <span className="flex h-5 items-end gap-[3px]" aria-hidden>
            {[0.5, 1, 0.7, 0.85].map((h, i) => (
              <span key={i} className="w-[3px] animate-pulse rounded-full bg-linen" style={{ height: `${h * 100}%`, animationDelay: `${i * 120}ms` }} />
            ))}
          </span>
        </div>
        <div>
          <p className="font-display text-2xl leading-tight first-letter:uppercase">{title}</p>
          <p className="text-sm text-ink-2">{s(r.artist) ?? "Mock player"}</p>
        </div>
      </div>
    </Shell>
  );
}

export function EmailDraft({ r, onConfirm, onCancel, busy }: { r: R; onConfirm?: () => void; onCancel?: () => void; busy?: boolean }) {
  const state = r.cancelled ? "Draft deleted" : r.sent ? "E-mail sent" : "Draft, not sent";
  return (
    <Shell kind={state}>
      <dl className="grid grid-cols-[4rem_1fr] gap-y-1 text-sm">
        <dt className="text-ink-2">To</dt>
        <dd className="font-medium">{s(r.to)}</dd>
        <dt className="text-ink-2">Subject</dt>
        <dd>{s(r.subject) ?? <span className="text-ink-2">none</span>}</dd>
      </dl>
      {!r.sent && !r.cancelled && onConfirm && (
        <div className="mt-4 flex gap-2">
          <Button variant="primary" onClick={onConfirm} disabled={busy}>
            Send
          </Button>
          <Button onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
        </div>
      )}
    </Shell>
  );
}

export function ToolResult({ intent, result }: { intent: string | null; result: R }) {
  if (intent === "alarm_set") return <Alarm r={result} />;
  if (intent === "weather_query") return <Weather r={result} />;
  if (intent === "calendar_set") return <Calendar r={result} />;
  if (intent === "play_music") return <NowPlaying r={result} />;
  return (
    <Shell kind="Result">
      <pre className="overflow-x-auto font-mono text-xs">{JSON.stringify(result, null, 2)}</pre>
    </Shell>
  );
}
