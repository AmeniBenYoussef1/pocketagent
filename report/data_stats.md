# Data stats

Vocabularies are fitted on train only, with min_freq = 2. Regenerate with `python -m src.data.vocab --report`.

## Vocabulary sizes and dev `<UNK>` rate

Source `<UNK>` is measured on utterance tokens. Target `<UNK>` is measured on slot value tokens only, since intents, slot names and `( ) = " ,` are always in the target vocabulary.

| vocab | locale | src size | tgt size | src `<UNK>` | tgt `<UNK>` |
|---|---|---|---|---|---|
| per locale | en-US | 2,772 | 1,657 | 5.2% | 15.2% |
| per locale | fr-FR | 3,351 | 1,574 | 6.4% | 15.7% |
| per locale | ar-SA | 4,064 | 1,850 | 13.8% | 23.2% |
| joint | en-US | 9,947 | 4,801 | 4.7% | 13.2% |
| joint | fr-FR | 9,947 | 4,801 | 5.5% | 12.9% |
| joint | ar-SA | 9,947 | 4,801 | 13.0% | 21.5% |

- Sizes include `<PAD> <UNK> <SOS> <EOS>`, the language tags (source) and the 60 intents, 55 slot names and 5 syntax tokens (target).
- Arabic has about 2.5x the English `<UNK>` rate because clitics like و and ال are attached to words, so each word form is rarer. Subwords (step 8) should help here.
- The joint vocabulary lowers `<UNK>` a bit for every language, since names, numbers and "olly" are shared.
- Without a copy mechanism, about 1 value token in 7 (EN) to 1 in 4 (AR) can't be generated. This is the main reason for E2.

## Target length

Target tokens include `<SOS>` and `<EOS>`.

| locale | train max | train > 40 (dropped) | dev max | test max |
|---|---|---|---|---|
| en-US | 56 | 7 | 39 | 42 |
| fr-FR | 56 | 9 | 39 | 40 |
| ar-SA | 51 | 4 | 37 | 38 |

- max_tgt_len = 40 (p99.9 of train is 37-38). The 20 longer train examples (0.06%) are dropped, not truncated, so the model never learns a call without `)` and `<EOS>`.
- Dev and test are never filtered. At inference the decoder runs up to 48 tokens, so the longest test call (42) is not cut. Test lengths were only read to confirm this, nothing was tuned on them.
- max_src_len = 32 tokens including the language tag, which truncates 5 of 34,542 train utterances.
