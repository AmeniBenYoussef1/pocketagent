import { useState } from "react";
import { CallText } from "../components/CallView";
import { Card, Label, cx } from "../components/ui";

const BLOCKS = [
  {
    key: "utterance",
    title: "Utterance",
    example: "<en> wake me up at five am",
    text: "The command is split on spaces and a language tag is added in front. The vocabularies were built from the training split only, so a rare word becomes <UNK>.",
  },
  {
    key: "encoder",
    title: "Encoder",
    example: "BiLSTM, 2 layers",
    text: "A bidirectional LSTM reads the words left to right and right to left, and keeps one vector per word. E0 only keeps the last state, which is why it struggles with long commands.",
  },
  {
    key: "attention",
    title: "Attention + copy",
    example: "p_gen = 0.03 on \"five\"",
    text: "At each output step, attention weighs the input words. The copy switch p_gen then decides between writing a word from the vocabulary and copying the attended word, so names and numbers come out exactly as typed.",
  },
  {
    key: "decoder",
    title: "Decoder",
    example: "greedy or beam 3",
    text: "An LSTM writes the call one token at a time until <EOS>. Greedy takes the best token at each step; beam search keeps the three best partial calls.",
  },
  {
    key: "call",
    title: "Function call",
    example: "alarm_set(time=\"five am\")",
    call: true,
    text: "The tokens are joined back into a call: the intent is the function name, the slots are the arguments, and the values are copied from the command.",
  },
  {
    key: "validator",
    title: "Validator",
    example: "time: 05:00",
    text: "The call is parsed and checked. Unknown functions are refused, a missing argument becomes a question, low confidence becomes \"Did you mean...?\", and times and dates are normalized.",
  },
  {
    key: "tool",
    title: "Tool",
    example: "alarm, weather, calendar...",
    text: "Only then does a tool run. E-mails are always drafts first and are sent only after an explicit confirmation.",
  },
];

export default function HowItWorks() {
  const [active, setActive] = useState<string | null>(null);
  return (
    <div className="space-y-10">
      <header className="max-w-2xl">
        <Label>Architecture</Label>
        <h1 className="mt-2 text-5xl leading-[1.05]">
          From a sentence to an <em>action</em>
        </h1>
        <p className="mt-3 text-ink-2">
          The model is an encoder-decoder trained from scratch on MASSIVE (English, French, Arabic). Everything after the call is plain code.
        </p>
      </header>

      <Card className="p-8">
        <ol className="flex flex-col items-stretch gap-3 lg:flex-row lg:items-center">
          {BLOCKS.map((b, i) => (
            <li key={b.key} className="flex flex-col items-center gap-3 lg:flex-1 lg:flex-row">
              <button
                onMouseEnter={() => setActive(b.key)}
                onMouseLeave={() => setActive(null)}
                onFocus={() => setActive(b.key)}
                onBlur={() => setActive(null)}
                onClick={() => document.getElementById(b.key)?.scrollIntoView({ behavior: "smooth", block: "center" })}
                className={cx(
                  "ease w-full rounded-2xl border px-3 py-4 text-center",
                  active === b.key ? "border-terracotta bg-page shadow-[var(--shadow-soft)]" : "border-line bg-card-soft",
                  (i === 0 || i >= 4) && "border-dashed",
                  i === 0 && "bg-transparent",
                )}
              >
                <span className="label block">{i === 0 ? "input" : i < 4 ? "model" : "agent"}</span>
                <span className="mt-1 block font-display text-xl leading-tight">{b.title}</span>
              </button>
              {i < BLOCKS.length - 1 && (
                <span aria-hidden className="text-terracotta lg:rotate-0 rotate-90">
                  →
                </span>
              )}
            </li>
          ))}
        </ol>
        <p className="mt-5 text-xs text-ink-2">Solid blocks are the neural model; the input and the agent code around it are dashed.</p>
      </Card>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {BLOCKS.map((b, i) => (
          <article
            key={b.key}
            id={b.key}
            onMouseEnter={() => setActive(b.key)}
            onMouseLeave={() => setActive(null)}
            className={cx("card ease p-6", active === b.key && "border-terracotta")}
          >
            <Label>Step {i + 1}</Label>
            <h2 className="mt-1 text-3xl">{b.title}</h2>
            <div className="mt-3 rounded-xl border border-line bg-card-soft px-3 py-2">
              {b.call ? <CallText call={b.example} className="text-xs" /> : <code dir="ltr" className="font-mono text-xs text-ink">{b.example}</code>}
            </div>
            <p className="mt-3 text-sm leading-relaxed text-ink-2">{b.text}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
