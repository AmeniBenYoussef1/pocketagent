"""Unit tests for src/baselines/retrieval.py."""

import pytest

from src.baselines.retrieval import TfidfRetriever, predict

WORD = {"analyzer": "word", "ngram_range": [1, 2]}
CHAR = {"analyzer": "char_wb", "ngram_range": [2, 5]}


def row(i, loc, utt, call):
    return {"id": str(i), "locale": loc, "utt": utt, "call": call}


TRAIN = [
    row(0, "en-US", "wake me up at five am", 'alarm_set(time="five am")'),
    row(1, "en-US", "what is the weather in paris", 'weather_query(place_name="paris")'),
    row(2, "fr-FR", "quel temps fait il à paris", 'weather_query(place_name="paris")'),
    row(3, "fr-FR", "réveille moi à cinq heures", 'alarm_set(time="cinq heures")'),
    row(4, "ar-SA", "صحيني الساعة خمسة", 'alarm_set(time="الساعة خمسة")'),
]


@pytest.mark.parametrize("variant", [WORD, CHAR])
def test_identical_utterance_returns_its_own_call(variant):
    preds = predict(TRAIN, TRAIN, variant, sublinear_tf=True)
    assert [p["pred"] for p in preds] == [r["call"] for r in TRAIN]
    assert all(p["similarity"] == pytest.approx(1.0) for p in preds)


def test_locales_are_kept_separate():
    # english words, but the query is fr-FR: only fr-FR train rows can be returned
    query = [row(9, "fr-FR", "what is the weather in paris", 'weather_query(place_name="paris")')]
    preds = predict(TRAIN, query, WORD, sublinear_tf=True)
    assert preds[0]["nearest_id"] in {"2", "3"}


def test_ties_go_to_lowest_index():
    retriever = TfidfRetriever("word", (1, 2)).fit(["set an alarm", "set an alarm", "play music"])
    idx, _ = retriever.nearest(["set an alarm"])
    assert idx[0] == 0


def test_no_overlap_is_deterministic():
    retriever = TfidfRetriever("word", (1, 1)).fit(["set an alarm", "play music"])
    idx, sim = retriever.nearest(["zzz"])
    assert (idx[0], sim[0]) == (0, 0.0)


def test_char_ngrams_match_arabic_clitic():
    # "وصحيني" (and wake me) shares char n-grams with "صحيني" but not the word
    train = [row(0, "ar-SA", "شغل موسيقى", "play_music()"), TRAIN[4]]
    query = [row(1, "ar-SA", "وصحيني", 'alarm_set(time="x")')]
    assert predict(train, query, CHAR, sublinear_tf=True)[0]["nearest_id"] == "4"
