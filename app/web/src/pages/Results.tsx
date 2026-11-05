import { useEffect, useMemo, useState } from "react";
import { api, type Results as ResultsData, type RunResult } from "../api";
import { GroupedBars, LineChart, StackedBars, type Series } from "../components/charts";
import { Card, EmptyState, ErrorState, Label, Segmented, Skeleton, pct } from "../components/ui";

// a run keeps its colour on every chart
const RUN_COLORS: Record<string, string> = {
  "b0_retrieval/char": "#7A645A",
  e0_lstm: "#F2B59C",
  e1_attn: "#E08A7C",
  e2_copy: "#A9675A",
  e2_copy_beam3: "#6E6447",
};
const LOCALE_LABEL: Record<string, string> = { overall: "All", "en-US": "English", "fr-FR": "French", "ar-SA": "Arabic" };
const METRICS = [
  { value: "em", label: "Exact match" },
  { value: "intent", label: "Intent" },
  { value: "slot_f1", label: "Slot F1" },
] as const;
type Metric = (typeof METRICS)[number]["value"];
// the error categories, grouped so the palette is enough
const ERROR_GROUPS: (Series & { cats: string[] })[] = [
  { key: "intent", label: "Wrong intent", color: "#E08A7C", cats: ["wrong intent"] },
  { key: "names", label: "Missing, extra or wrong slot", color: "#F2B59C", cats: ["missing slot", "extra slot", "wrong slot names"] },
  { key: "value", label: "Wrong value", color: "#A9675A", cats: ["value with <UNK>", "value partly wrong", "value wrong"] },
  { key: "repeat", label: "Repeated copy", color: "#6E6447", cats: ["repeated copy"] },
  { key: "invalid", label: "Invalid call", color: "#7A645A", cats: ["invalid call"] },
];

export default function Results() {
  const [data, setData] = useState<ResultsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = () => {
    setError(null);
    setData(null);
    api.results().then(setData, (e: Error) => setError(e.message));
  };
  useEffect(load, []);

  if (error) return <ErrorState message={`Couldn't load the results: ${error}`} onRetry={load} />;
  if (!data)
    return (
      <div className="space-y-6">
        <Skeleton className="h-32" />
        <Skeleton className="h-80" />
        <Skeleton className="h-64" />
      </div>
    );
  if (data.runs.length === 0) return <EmptyState title="No results yet">Train a model and its dev metrics will show up here.</EmptyState>;
  return <ResultsView data={data} />;
}

function ResultsView({ data }: { data: ResultsData }) {
  const ladder = data.runs.filter((r) => r.group === "ladder");
  const best = ladder.reduce((a, b) => (b.metrics.overall.em > a.metrics.overall.em ? b : a), ladder[0]);
  const [metric, setMetric] = useState<Metric>("em");
  const trained = data.runs.filter((r) => r.history);
  const [curveRun, setCurveRun] = useState(trained.find((r) => r.id === "e2_copy")?.id ?? trained[0]?.id);
  const curve = trained.find((r) => r.id === curveRun);
  const series: Series[] = ladder.map((r) => ({ key: r.id, label: r.label, color: RUN_COLORS[r.id] ?? "#7A645A" }));
  const perLocale = data.runs.filter((r) => r.group === "per_locale");

  return (
    <div className="space-y-6">
      <header className="max-w-2xl">
        <Label>Dev split, {data.runs.length} runs</Label>
        <h1 className="mt-2 text-5xl leading-[1.05]">
          From retrieval to <em>copying</em>
        </h1>
        <p className="mt-3 text-ink-2">
          Every number comes from the run folders in experiments/. The test split is not used here.
        </p>
      </header>

      {best && (
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            ["Exact match", best.metrics.overall.em],
            ["Slot F1", best.metrics.overall.slot_f1],
            ["Intent accuracy", best.metrics.overall.intent],
          ].map(([label, v]) => (
            <Card key={label as string}>
              <Label>{label}</Label>
              <p className="mt-2 font-display text-5xl leading-none">{pct(v as number)}</p>
              <p className="mt-2 text-xs text-ink-2">{best.label}, all languages</p>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <Label>Model ladder</Label>
            <h2 className="mt-1 text-3xl">
              Each step, per <em>language</em>
            </h2>
          </div>
          <Segmented label="Metric" options={[...METRICS]} value={metric} onChange={setMetric} />
        </div>
        <div className="mt-6">
          <GroupedBars
            categories={data.locales.map((l) => LOCALE_LABEL[l] ?? l)}
            series={series}
            values={ladder.map((r) => data.locales.map((l) => r.metrics[l]?.[metric] ?? null))}
            format={(v) => `${Math.round(v * 100)}%`}
          />
        </div>
        <Table
          head={["Model", ...data.locales.map((l) => LOCALE_LABEL[l])]}
          rows={ladder.map((r) => [r.label, ...data.locales.map((l) => pct(r.metrics[l]?.[metric]))])}
        />
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <Label>Learning curves</Label>
              <h2 className="mt-1 text-3xl">
                How <em>training</em> went
              </h2>
            </div>
            {trained.length > 0 && (
              <select
                value={curveRun}
                onChange={(e) => setCurveRun(e.target.value)}
                aria-label="Run"
                className="ease rounded-full border border-line bg-page px-3 py-1.5 text-sm focus:border-terracotta focus:outline-none"
              >
                {trained.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </select>
            )}
          </div>
          {curve?.history ? (
            <div className="mt-5 space-y-6">
              <div>
                <p className="mb-1 text-sm text-ink-2">Loss per token</p>
                <LineChart
                  xs={curve.history.map((h) => h.epoch)}
                  series={[
                    { key: "train", label: "Train", color: "#A9675A" },
                    { key: "dev", label: "Dev", color: "#6E6447" },
                  ]}
                  values={[curve.history.map((h) => h.train_loss), curve.history.map((h) => h.dev_loss)]}
                  format={(v) => v.toFixed(2)}
                  xLabel="epoch"
                />
              </div>
              <div>
                <p className="mb-1 text-sm text-ink-2">Dev exact match, greedy</p>
                <LineChart
                  xs={curve.history.map((h) => h.epoch)}
                  series={[{ key: "em", label: "Dev EM", color: "#A9675A" }]}
                  values={[curve.history.map((h) => h.dev_em)]}
                  format={(v) => `${Math.round(v * 100)}%`}
                  xLabel="epoch"
                />
              </div>
              <p className="text-xs text-ink-2">
                Median {median(curve.history.map((h) => h.train_seconds)).toFixed(0)} s of training per epoch. Best dev epoch:{" "}
                {curve.history.reduce((a, b) => (b.dev_em > a.dev_em ? b : a)).epoch}.
              </p>
            </div>
          ) : (
            <p className="mt-4 text-sm text-ink-2">No training history for this run.</p>
          )}
        </Card>

        <Card>
          <Label>Error types</Label>
          <h2 className="mt-1 text-3xl">
            Where calls go <em>wrong</em>
          </h2>
          <div className="mt-6">
            <StackedBars
              rows={ladder.map((r) => r.label)}
              parts={ERROR_GROUPS}
              values={ladder.map((r) => ERROR_GROUPS.map((g) => g.cats.reduce((a, c) => a + (r.errors[c] ?? 0), 0)))}
            />
          </div>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <Label>Decoding</Label>
          <h2 className="mt-1 text-3xl">
            Greedy or <em>beam</em>
          </h2>
          <Table
            head={["E2 decoding", "EM", "Slot F1", "Time on dev"]}
            rows={data.runs
              .filter((r) => r.id === "e2_copy" || r.id.startsWith("e2_copy_beam"))
              .sort((a, b) => (a.decode?.beam_size ?? 1) - (b.decode?.beam_size ?? 1))
              .map((r) => [
                r.decode ? `Beam ${r.decode.beam_size}` : "Greedy",
                pct(r.metrics.overall.em),
                pct(r.metrics.overall.slot_f1),
                r.decode ? `${r.decode.decode_seconds.toFixed(0)} s` : "n/a",
              ])}
          />
        </Card>
        <Card>
          <Label>Seen vs unseen</Label>
          <h2 className="mt-1 text-3xl">
            Commands it has <em>never</em> seen
          </h2>
          <p className="mt-2 text-sm text-ink-2">Seen means the exact command is also in the training data.</p>
          <Table
            head={["Model", "EM seen", "EM unseen", "Slot F1 unseen"]}
            rows={ladder.map((r) => {
              const su = r.seen_unseen.overall;
              return [r.label, `${pct(su.seen.exact_match)} (${su.seen.n})`, `${pct(su.unseen.exact_match)} (${su.unseen.n})`, pct(su.unseen.slot_f1)];
            })}
          />
        </Card>
      </div>

      {perLocale.length > 0 && <PerLocale runs={data.runs} perLocale={perLocale} />}
      {data.calibration && <Calibration data={data} />}
    </div>
  );
}

function PerLocale({ runs, perLocale }: { runs: RunResult[]; perLocale: RunResult[] }) {
  const joint = runs.find((r) => r.id === "e2_copy_beam3");
  const rows = useMemo(
    () =>
      perLocale.map((r) => {
        const loc = Object.keys(r.metrics).find((k) => k !== "overall")!;
        return { loc, own: r.metrics[loc], joint: joint?.metrics[loc] };
      }),
    [perLocale, joint],
  );
  return (
    <Card>
      <Label>One model per language</Label>
      <h2 className="mt-1 text-3xl">
        Joint or <em>separate</em>
      </h2>
      <p className="mt-2 text-sm text-ink-2">E2 trained on one language only (E7) against the joint E2, both with beam 3.</p>
      <Table
        head={["Language", "EM joint", "EM separate", "Slot F1 joint", "Slot F1 separate"]}
        rows={rows.map((r) => [LOCALE_LABEL[r.loc], pct(r.joint?.em), pct(r.own.em), pct(r.joint?.slot_f1), pct(r.own.slot_f1)])}
      />
    </Card>
  );
}

function Calibration({ data }: { data: ResultsData }) {
  const c = data.calibration!;
  return (
    <Card>
      <Label>Confidence</Label>
      <h2 className="mt-1 text-3xl">
        When to <em>ask</em>
      </h2>
      <p className="mt-2 text-sm text-ink-2">
        Above the threshold the agent acts on its own. AUROC: mean {c.mean.auroc.toFixed(3)}, min {c.min.auroc.toFixed(3)}.
      </p>
      <Table
        head={["Threshold", "Acts alone (mean)", "Right when alone", "Acts alone (min)", "Right when alone"]}
        rows={c.mean.table.map((r, i) => [
          r.threshold.toFixed(2),
          pct(r.coverage),
          pct(r.accuracy_kept),
          pct(c.min.table[i].coverage),
          pct(c.min.table[i].accuracy_kept),
        ])}
      />
    </Card>
  );
}

function Table({ head, rows }: { head: string[]; rows: string[][] }) {
  return (
    <div className="mt-5 overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line">
            {head.map((h, i) => (
              <th key={h + i} className={`label pb-2 font-semibold ${i ? "text-end" : "text-start"}`}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri} className="border-b border-line/60 last:border-0">
              {r.map((c, ci) => (
                <td key={ci} className={`py-2 tabular-nums ${ci ? "text-end" : "font-medium"}`}>
                  {c}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function median(xs: number[]) {
  const s = [...xs].sort((a, b) => a - b);
  return s.length ? s[Math.floor(s.length / 2)] : 0;
}
