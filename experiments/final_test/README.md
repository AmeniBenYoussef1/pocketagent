# Final test evaluation

Run once, after the model and every setting were fixed on dev (commit 9046da3): joint E2 with beam 3,
and B0 (char 2-5 grams, the variant chosen on dev) for comparison. Nothing was changed after these numbers.

## B0 retrieval

| locale | EM | EM strict | intent | slot F1 | valid | macro intent F1 | macro EM | macro slot F1 |
|---|---|---|---|---|---|---|---|---|
| overall | 34.7% | 34.4% | 68.4% | 42.4% | 100.0% | 64.6% | 37.8% | 39.7% |
| en-US | 38.2% | 37.8% | 70.8% | 47.3% | 100.0% | 67.4% | 42.1% | 45.1% |
| fr-FR | 34.8% | 34.5% | 70.5% | 41.0% | 100.0% | 67.0% | 37.7% | 40.2% |
| ar-SA | 31.1% | 31.0% | 63.8% | 38.9% | 100.0% | 59.7% | 33.7% | 36.0% |

| locale | n seen | EM seen | n unseen | EM unseen | intent unseen | slot F1 unseen |
|---|---|---|---|---|---|---|
| overall | 408 | 80.6% | 8514 | 32.5% | 67.6% | 40.7% |
| en-US | 21 | 85.7% | 2953 | 37.9% | 70.7% | 47.0% |
| fr-FR | 150 | 85.3% | 2824 | 32.2% | 69.5% | 39.4% |
| ar-SA | 237 | 77.2% | 2737 | 27.1% | 62.3% | 35.4% |

Error types (% of test): correct 34.7, wrong intent 31.6, missing slot 13.2, extra slot 6.8, wrong slot names 4.3, repeated copy 0.0, value partly wrong 4.3, value wrong 5.0

## E2 + beam 3 (final)

| locale | EM | EM strict | intent | slot F1 | valid | macro intent F1 | macro EM | macro slot F1 |
|---|---|---|---|---|---|---|---|---|
| overall | 57.6% | 57.6% | 79.4% | 69.3% | 100.0% | 75.0% | 58.2% | 65.8% |
| en-US | 62.7% | 62.7% | 82.6% | 73.5% | 100.0% | 78.6% | 63.6% | 70.5% |
| fr-FR | 57.7% | 57.7% | 80.8% | 68.9% | 100.0% | 76.0% | 57.7% | 65.2% |
| ar-SA | 52.4% | 52.4% | 74.6% | 65.3% | 100.0% | 70.1% | 53.3% | 62.0% |

| locale | n seen | EM seen | n unseen | EM unseen | intent unseen | slot F1 unseen |
|---|---|---|---|---|---|---|
| overall | 408 | 85.0% | 8514 | 56.3% | 78.9% | 68.5% |
| en-US | 21 | 85.7% | 2953 | 62.5% | 82.6% | 73.4% |
| fr-FR | 150 | 90.7% | 2824 | 55.9% | 80.0% | 68.3% |
| ar-SA | 237 | 81.4% | 2737 | 49.8% | 73.7% | 63.6% |

Error types (% of test): correct 57.6, wrong intent 20.6, missing slot 5.8, extra slot 6.7, wrong slot names 4.5, repeated copy 0.3, value partly wrong 4.2, value wrong 0.3
