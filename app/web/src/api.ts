// Types and calls for the FastAPI app (/api, proxied in dev, same origin in production).

export type Locale = "en-US" | "fr-FR" | "ar-SA";
export type Decoding = "greedy" | "beam3" | "nearest";

export interface ModelInfo {
  id: string;
  short: string;
  name: string;
  ready: boolean;
  decodings: Decoding[];
}

export interface Token {
  token: string;
  prob: number;
  p_gen: number | null;
  source: "copied" | "generated" | null;
}

export interface Attention {
  src_tokens: string[];
  tgt_tokens: string[];
  weights: number[][];
}

export interface ParseResult {
  model: string;
  decoding: Decoding;
  call: string;
  confidence: number | null;
  latency_ms: number;
  tokens: Token[] | null;
  attention: Attention | null;
  nearest?: string;
}

export interface AgentResponse {
  status: "executed" | "needs_input" | "needs_confirmation" | "rejected";
  message: string;
  intent: string | null;
  args: Record<string, string | null>;
  result: Record<string, unknown> | null;
  call: string | null;
  confidence: number | null;
  missing: string[];
}

export type LocaleMetrics = Record<"em" | "em_strict" | "intent" | "slot_f1" | "valid" | "macro_em", number>;

export interface SubsetScores {
  n: number;
  exact_match: number | null;
  intent_accuracy: number | null;
  slot_f1: number | null;
}

export interface RunResult {
  id: string;
  label: string;
  group: "ladder" | "decoding" | "per_locale";
  metrics: Record<string, LocaleMetrics>;
  seen_unseen: Record<string, { seen: SubsetScores; unseen: SubsetScores }>;
  errors: Record<string, number>;
  history: { epoch: number; train_loss: number; dev_loss: number; dev_em: number; train_seconds: number }[] | null;
  decode: { beam_size: number; decode_seconds: number } | null;
}

export interface CalibrationRow {
  threshold: number;
  coverage: number;
  accuracy_kept: number | null;
  accuracy_asked: number | null;
}

export interface Results {
  locales: string[];
  error_categories: string[];
  runs: RunResult[];
  calibration: Record<"mean" | "min", { auroc: number; table: CalibrationRow[] }> | null;
}

async function request<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
    } catch {
      // keep the status text
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  models: () =>
    request<{ models: ModelInfo[]; threshold: number; default: { model: string; decoding: Decoding } }>("/models"),
  parse: (utterance: string, locale: Locale, model: string, decoding: Decoding) =>
    request<ParseResult>("/parse", { utterance, locale, model, decoding }),
  execute: (body: {
    call: string;
    locale: Locale;
    confidence: number | null;
    confirmed?: boolean;
    fill?: Record<string, string>;
  }) => request<AgentResponse>("/execute", body),
  draft: (draft_id: number, action: "confirm" | "cancel") =>
    request<AgentResponse>("/execute", { draft_id, action }),
  results: () => request<Results>("/results"),
};
