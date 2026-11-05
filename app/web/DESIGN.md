# PocketAgent web app: design plan

React + Vite + TypeScript + Tailwind, served by the FastAPI app (`/api/...`) on one port.

## Identity

Palette, as Tailwind tokens. Light colours are surfaces only. Text shades were darkened (or lightened in dark mode) until every pair reaches 4.5:1; the original values stay for fills, borders and chips.

| token | value | used for |
|---|---|---|
| linen | #F4ECE3 | page background |
| petal | #F8D9C9 | cards, panels |
| apricot | #F2B59C | generated-token chips, medium confidence, highlights |
| rosewood | #E08A7C | low-confidence fill, warnings (fill) |
| terracotta | #A9675A | accents, borders, active states |
| olive | #6E6447 | success fill, copied-token chips, high confidence |
| espresso | #3A2A24 | main text |
| cocoa | #7A645A | decorative only |
| ink-cocoa | #715D54 | secondary text (4.64:1 on petal) |
| ink-terracotta | #8A5348 | function names, links (4.62:1) |
| ink-olive | #6B6145 | argument names (4.61:1) |
| ink-rosewood | #AC3B29 | values in calls, warning text (4.62:1) |
| button | #965A4E | primary button, linen text on it (4.64:1) |

Dark mode (toggle, saved in localStorage): background #2B211D, cards #3A2D28, text linen, secondary #AA958B, function names #BF8E84, argument names #A59873, values rosewood #E08A7C, petal and apricot for highlights. Terracotta and olive stay for fills and borders.

Type: Cormorant Garamond for headings, with one word in italics per heading; Inter for body; uppercase Inter with wide tracking for small labels; JetBrains Mono for calls. Fonts are bundled (@fontsource), so the app works offline.

Shape: 20px radius cards, 1px borders in terracotta at low opacity, soft shadow, 150 to 200 ms transitions on hover, focus and theme. No emoji, no component library.

## Layout

Top bar: wordmark "PocketAgent" in Cormorant, three links (Assistant, Results, How it works), the theme toggle. Content is max 1280px wide, centred, with generous padding. Below 1024px the two columns stack.

## Page 1: Assistant

Two columns, 5/7.

Left, the conversation:
- header with the language switch (EN / FR / AR, a segmented control) and the model selector (B0, E0, E1, E2, each greedy or beam 3)
- example commands for the current language, as small pill buttons; clicking sends one
- the message list: user bubbles on petal, agent replies on linen with a thin border; each agent reply can be selected, the selected one has a terracotta left edge
- tool cards inside the replies: alarm, weather (real forecast from Open-Meteo, offline estimate if the network fails), calendar event, now playing, e-mail draft with Confirm and Cancel
- follow-ups: a missing argument gives a question, and the next message fills it; low confidence gives "Did you mean ...?" with Confirm and Edit; an invalid or unknown call gives a short plain message
- input at the bottom, Enter to send, Shift+Enter for a new line; with Arabic selected the input and the bubbles switch to RTL

Right, "Under the hood" for the selected turn:
- the call, syntax highlighted (function name, argument names, values, punctuation), with a copy button
- confidence meter (olive above the threshold, apricot near it, rosewood below) and latency in ms
- call tokens as chips: olive outline for tokens copied from the input, apricot for generated ones (E2's p_gen), with a legend and the p_gen value on hover
- attention heatmap, output tokens by input words, sequential scale from petal to terracotta; hovering a cell highlights its row and column and shows the weight; input words run right to left for Arabic
- "Compare models": runs the same command through the other models and lists their calls side by side

Empty state: a short line and the examples. Loading: a skeleton in the panel. Error: a card with the message and a retry button.

## Page 2: Results

All numbers come from `GET /api/results`, read from `experiments/`.
- headline row: three stat tiles (best dev EM, slot F1, intent accuracy) for the best run
- model ladder: grouped bars per language for B0, E0, E1, E2, E2 + beam 3, with a metric switch (EM, intent, slot F1); runs keep the same colour everywhere
- learning curves: train and dev loss, dev EM, for the selected run
- error types: horizontal stacked bars, one per model
- greedy vs beam and seen vs unseen: small tables
- E7 (per-locale) appears when its runs exist

## Page 3: How it works

A horizontal diagram (vertical on mobile): utterance, encoder, attention + copy, decoder, function call, validator, tool. Each block is a card with a one-paragraph explanation; hovering a block highlights it in the diagram.

## API additions

- `GET /api/models`: available models and decoding options
- `POST /api/parse`: call, confidence, latency, tokens with p_gen and copied/generated, attention, missing arguments
- `POST /api/execute`: run a call (with fill-ins for follow-ups), or confirm / cancel a draft
- `GET /api/results`: everything the Results page shows
