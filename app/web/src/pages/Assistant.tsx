import { useEffect, useRef, useState } from "react";
import { api, type AgentResponse, type Decoding, type Locale, type ModelInfo, type ParseResult } from "../api";
import { CallText, CallView } from "../components/CallView";
import { AttentionHeatmap, ConfidenceMeter, TokenChips } from "../components/Hood";
import { EmailDraft, ToolResult } from "../components/ToolCards";
import { Button, Card, EmptyState, ErrorState, Label, Segmented, Skeleton, Spinner, cx } from "../components/ui";

const EXAMPLES: Record<Locale, string[]> = {
  "en-US": [
    "wake me up at seven am tomorrow",
    "what's the weather in paris tomorrow",
    "add dentist to my calendar on friday",
    "play some jazz",
    "send an email to john about the party",
    "set an alarm",
  ],
  "fr-FR": [
    "réveille-moi à sept heures demain",
    "quel temps fera-t-il à lyon demain",
    "ajoute dentiste à mon agenda vendredi",
    "mets du jazz",
    "envoie un mail à marie pour la fête",
  ],
  "ar-SA": ["صحيني الساعة ستة الصبح", "كيف الطقس في دبي بكرة", "شغل موسيقى جاز", "ابعث ايميل لأحمد عن الحفلة"],
};
const LANGS: { value: Locale; label: string }[] = [
  { value: "en-US", label: "EN" },
  { value: "fr-FR", label: "FR" },
  { value: "ar-SA", label: "AR" },
];

interface Turn {
  id: number;
  utterance: string;
  locale: Locale;
  parse?: ParseResult;
  response?: AgentResponse;
  error?: string;
  busy: boolean;
  fill?: Record<string, string>; // answers given so far to follow-up questions
}

let nextId = 1;

export default function Assistant() {
  const [models, setModels] = useState<ModelInfo[] | null>(null);
  const [threshold, setThreshold] = useState(0.5);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [locale, setLocale] = useState<Locale>("en-US");
  const [model, setModel] = useState("e2");
  const [decoding, setDecoding] = useState<Decoding>("greedy");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const loadModels = () => {
    setModelsError(null);
    api.models().then(
      (m) => {
        setModels(m.models);
        setThreshold(m.threshold);
        const preferred = m.models.find((x) => x.id === m.default.model && x.ready);
        setModel(preferred?.id ?? m.models.find((x) => x.ready)?.id ?? "e2");
        if (preferred && m.default.decoding !== "nearest") setDecoding(m.default.decoding);
      },
      (e: Error) => setModelsError(e.message),
    );
  };
  useEffect(loadModels, []);
  // share links: /?q=wake+me+up+at+seven&lang=fr sends the command once the models are known
  const shared = useRef(false);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (!models || shared.current || !q) return;
    shared.current = true;
    const lang = ({ en: "en-US", fr: "fr-FR", ar: "ar-SA" } as Record<string, Locale>)[params.get("lang") ?? "en"] ?? "en-US";
    setLocale(lang);
    send(q, lang);
  }, [models]);
  // block body: an effect must not return anything but a cleanup, and recent browsers
  // return a Promise from scrollIntoView, which React would then try to call
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  const rtl = locale === "ar-SA";
  const current = models?.find((m) => m.id === model);
  // a follow-up is pending when the last turn ended with a question
  const last = turns[turns.length - 1];
  const pending = last && !last.busy && last.response?.status === "needs_input" ? last : null;
  const shown = turns.find((t) => t.id === selected) ?? [...turns].reverse().find((t) => t.parse);

  const update = (id: number, patch: Partial<Turn>) =>
    setTurns((ts) => ts.map((t) => (t.id === id ? { ...t, ...patch } : t)));

  async function send(text: string, lang: Locale = locale) {
    const utterance = text.trim();
    if (!utterance) return;
    setInput("");
    const id = nextId++;

    // the previous turn asked for a missing argument: this message is the answer
    if (pending?.parse && pending.response) {
      const name = pending.response.missing[0];
      const fill = { ...(pending.fill ?? {}), [name]: utterance };
      setTurns((ts) => [...ts, { id, utterance, locale: pending.locale, parse: pending.parse, busy: true, fill }]);
      setSelected(id);
      try {
        const response = await api.execute({
          call: pending.parse.call, locale: pending.locale, confidence: pending.parse.confidence, confirmed: true, fill,
        });
        update(id, { response, busy: false });
      } catch (e) {
        update(id, { error: (e as Error).message, busy: false });
      }
      return;
    }

    setTurns((ts) => [...ts, { id, utterance, locale: lang, busy: true }]);
    setSelected(id);
    try {
      const parse = await api.parse(utterance, lang, model, model === "b0" ? "nearest" : decoding);
      update(id, { parse });
      const response = await api.execute({ call: parse.call, locale: lang, confidence: parse.confidence });
      update(id, { response, busy: false });
    } catch (e) {
      update(id, { error: (e as Error).message, busy: false });
    }
  }

  async function confirmCall(turn: Turn) {
    if (!turn.parse) return;
    update(turn.id, { busy: true });
    try {
      const response = await api.execute({
        call: turn.parse.call, locale: turn.locale, confidence: turn.parse.confidence, confirmed: true, fill: turn.fill,
      });
      update(turn.id, { response, busy: false });
    } catch (e) {
      update(turn.id, { error: (e as Error).message, busy: false });
    }
  }

  async function draftAction(turn: Turn, action: "confirm" | "cancel") {
    const draftId = Number(turn.response?.result?.id);
    update(turn.id, { busy: true });
    try {
      const r = await api.draft(draftId, action);
      update(turn.id, { response: { ...turn.response!, status: "executed", message: r.message, result: r.result }, busy: false });
    } catch (e) {
      update(turn.id, { error: (e as Error).message, busy: false });
    }
  }

  function edit(turn: Turn) {
    setLocale(turn.locale);
    setInput(turn.utterance);
    inputRef.current?.focus();
  }

  return (
    <div className="grid gap-6 lg:grid-cols-12">
      {/* conversation */}
      <Card className="flex min-h-[38rem] min-w-0 flex-col p-0 lg:col-span-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-6 py-4">
          <Segmented label="Language" options={LANGS} value={locale} onChange={setLocale} />
          {models && (
            <div className="flex flex-wrap items-center gap-2">
              <Segmented
                label="Model"
                options={models.map((m) => ({ value: m.id, label: m.short, disabled: !m.ready }))}
                value={model}
                onChange={setModel}
              />
              <Segmented
                label="Decoding"
                options={[
                  { value: "greedy" as Decoding, label: "Greedy", disabled: model === "b0" },
                  { value: "beam3" as Decoding, label: "Beam 3", disabled: model === "b0" },
                ]}
                value={decoding}
                onChange={setDecoding}
              />
            </div>
          )}
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-6" aria-live="polite">
          {modelsError && <ErrorState message={`The API is not reachable: ${modelsError}`} onRetry={loadModels} />}
          {!modelsError && turns.length === 0 && (
            <div>
              <h2 className="text-3xl">
                What can I <em>do</em> for you?
              </h2>
              <p className="mt-2 max-w-sm text-sm text-ink-2">
                Type a command in English, French or Arabic. I turn it into a function call, check it, then run a tool.
              </p>
            </div>
          )}
          {turns.map((t) => (
            <TurnView
              key={t.id}
              turn={t}
              selected={shown?.id === t.id}
              onSelect={() => setSelected(t.id)}
              onConfirm={() => confirmCall(t)}
              onEdit={() => edit(t)}
              onDraft={(a) => draftAction(t, a)}
            />
          ))}
          <div ref={endRef} />
        </div>

        <div className="border-t border-line px-6 py-4">
          <div className="mb-3 flex flex-wrap gap-2" dir={rtl ? "rtl" : "ltr"}>
            {EXAMPLES[locale].map((ex) => (
              <button
                key={ex}
                onClick={() => send(ex)}
                disabled={!!modelsError}
                className="ease rounded-full border border-line px-3 py-1 text-xs text-ink-2 hover:border-terracotta hover:text-ink"
              >
                {ex}
              </button>
            ))}
          </div>
          <form
            className="flex items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <label htmlFor="command" className="sr-only">
              Command
            </label>
            <textarea
              id="command"
              ref={inputRef}
              dir={rtl ? "rtl" : "ltr"}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              placeholder={pending ? "Your answer" : rtl ? "اكتب أمرا" : locale === "fr-FR" ? "Écrivez une commande" : "Type a command"}
              className="ease max-h-32 min-h-11 flex-1 resize-none rounded-2xl border border-line bg-page px-4 py-2.5 text-sm placeholder:text-ink-2 focus:border-terracotta focus:outline-none"
            />
            <Button variant="primary" type="submit" disabled={!input.trim() || !!modelsError}>
              Send
            </Button>
          </form>
          <p className="mt-2 text-xs text-ink-2">Enter to send, Shift+Enter for a new line.</p>
        </div>
      </Card>

      {/* under the hood */}
      <div className="min-w-0 space-y-6 lg:col-span-7">
        <Card>
          <div className="flex items-baseline justify-between gap-4">
            <h2 className="text-3xl">
              Under the <em>hood</em>
            </h2>
            {current && <span className="label">{current.short} {current.name}</span>}
          </div>
          {!shown && (
            <div className="mt-6">
              <EmptyState title="Nothing to show yet">Send a command and the call, its confidence and the attention appear here.</EmptyState>
            </div>
          )}
          {shown && !shown.parse && shown.busy && (
            <div className="mt-6 space-y-3">
              <Skeleton className="h-12" />
              <Skeleton className="h-16" />
              <Skeleton className="h-40" />
            </div>
          )}
          {shown && !shown.parse && shown.error && <div className="mt-6"><ErrorState message={shown.error} /></div>}
          {shown?.parse && <HoodDetails turn={shown} parse={shown.parse} threshold={threshold} models={models ?? []} />}
        </Card>
      </div>
    </div>
  );
}

function TurnView({
  turn,
  selected,
  onSelect,
  onConfirm,
  onEdit,
  onDraft,
}: {
  turn: Turn;
  selected: boolean;
  onSelect: () => void;
  onConfirm: () => void;
  onEdit: () => void;
  onDraft: (a: "confirm" | "cancel") => void;
}) {
  const r = turn.response;
  const rtl = turn.locale === "ar-SA";
  const isDraft = r?.intent === "email_sendemail" && r.result && "sent" in r.result;
  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <p dir={rtl ? "rtl" : "auto"} className="max-w-[85%] rounded-2xl rounded-ee-md bg-apricot/45 px-4 py-2.5 text-sm text-espresso dark:bg-card-soft dark:text-ink">
          {turn.utterance}
        </p>
      </div>
      <div
        role="button"
        tabIndex={0}
        aria-pressed={selected}
        aria-label="Show this turn under the hood"
        onClick={onSelect}
        onKeyDown={(e) => {
          if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            onSelect();
          }
        }}
        className={cx(
          "ease block w-full cursor-pointer rounded-2xl border bg-page px-4 py-3 text-start text-sm",
          selected ? "border-terracotta border-s-4" : "border-line hover:border-terracotta/60",
        )}
      >
        {turn.busy && !r && <Spinner label="Thinking" />}
        {turn.error && <span className="text-val">That didn't work: {turn.error}</span>}
        {r && (
          <>
            <p>{r.message}</p>
            {r.status === "needs_confirmation" && !isDraft && turn.parse && (
              <div className="mt-2" onClick={(e) => e.stopPropagation()}>
                <CallText call={turn.parse.call} className="text-xs" />
                <div className="mt-3 flex gap-2">
                  <Button variant="primary" onClick={onConfirm} disabled={turn.busy}>
                    Confirm
                  </Button>
                  <Button onClick={onEdit}>Edit</Button>
                </div>
              </div>
            )}
            {r.status === "needs_input" && <p className="mt-1 text-xs text-ink-2">Type the answer below.</p>}
            {isDraft && (
              <div onClick={(e) => e.stopPropagation()}>
                <EmailDraft r={r.result!} onConfirm={() => onDraft("confirm")} onCancel={() => onDraft("cancel")} busy={turn.busy} />
              </div>
            )}
            {r.status === "executed" && r.result && !isDraft && <ToolResult intent={r.intent} result={r.result} />}
          </>
        )}
      </div>
    </div>
  );
}

function HoodDetails({ turn, parse, threshold, models }: { turn: Turn; parse: ParseResult; threshold: number; models: ModelInfo[] }) {
  const [compare, setCompare] = useState<(ParseResult & { label: string })[] | null>(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);
  useEffect(() => {
    setCompare(null);
  }, [turn.id]);

  async function runCompare() {
    setComparing(true);
    setCompareError(null);
    const jobs = models
      .filter((m) => m.ready)
      .flatMap((m) => (m.id === "b0" ? [[m, "nearest"]] : [[m, "greedy"], [m, "beam3"]]) as [ModelInfo, Decoding][]);
    try {
      const out = await Promise.all(
        jobs.map(async ([m, d]) => ({ ...(await api.parse(turn.utterance, turn.locale, m.id, d)), label: `${m.short}${d === "beam3" ? " + beam 3" : ""}` })),
      );
      setCompare(out);
    } catch (e) {
      setCompareError((e as Error).message);
    } finally {
      setComparing(false);
    }
  }

  return (
    <div className="mt-6 space-y-7">
      <div>
        <Label className="mb-2">Predicted call</Label>
        <CallView call={parse.call} />
        {parse.nearest && <p className="mt-2 text-xs text-ink-2">Copied from the closest training command: "{parse.nearest}"</p>}
      </div>

      <div className="grid gap-6 sm:grid-cols-[1fr_auto]">
        <div>
          <Label className="mb-2">{parse.model === "b0" ? "Similarity" : "Confidence"}</Label>
          <ConfidenceMeter value={parse.confidence} threshold={threshold} />
        </div>
        <div className="sm:text-end">
          <Label className="mb-2">Latency</Label>
          <p className="font-display text-3xl">
            {parse.latency_ms.toFixed(0)}
            <span className="ms-1 text-base text-ink-2">ms</span>
          </p>
          <p className="text-xs text-ink-2">{parse.decoding === "beam3" ? "beam 3" : parse.decoding}</p>
        </div>
      </div>

      {parse.tokens && (
        <div>
          <Label className="mb-2">Call tokens</Label>
          <TokenChips tokens={parse.tokens} />
        </div>
      )}

      <div>
        <Label className="mb-2">Attention</Label>
        {parse.attention ? (
          <AttentionHeatmap attention={parse.attention} locale={turn.locale} />
        ) : (
          <p className="text-sm text-ink-2">
            {parse.model === "b0" ? "Retrieval has no attention." : parse.model === "e0" ? "E0 has no attention: the decoder only sees the encoder's last state." : "No attention for a malformed call."}
          </p>
        )}
      </div>

      <div>
        <div className="flex items-center justify-between">
          <Label>Compare models</Label>
          <Button onClick={runCompare} disabled={comparing}>
            {comparing ? <Spinner label="Running" /> : compare ? "Run again" : "Run all models"}
          </Button>
        </div>
        {compareError && <div className="mt-3"><ErrorState message={compareError} onRetry={runCompare} /></div>}
        {compare && (
          <ul className="mt-3 divide-y divide-line rounded-2xl border border-line">
            {compare.map((c) => (
              <li key={c.label} className="grid grid-cols-[6.5rem_1fr_auto] items-baseline gap-3 px-4 py-2.5">
                <span className="label">{c.label}</span>
                <CallText call={c.call} className="text-xs" />
                <span className="text-xs text-ink-2 tabular-nums">
                  {c.confidence === null ? "n/a" : c.confidence.toFixed(2)} · {c.latency_ms.toFixed(0)} ms
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
