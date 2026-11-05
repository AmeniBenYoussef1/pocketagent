"""Unit tests for src/training/evaluate.py, on a tiny fake data dir in tmp_path."""

import json

from src.training.evaluate import evaluate_run, predictions_path, read_jsonl, write_jsonl


def raw(i, utt, annot, intent="alarm_set", loc="en-US"):
    return {"id": str(i), "locale": loc, "intent": intent, "utt": utt, "annot_utt": annot}


TRAIN = [raw(0, "wake me up at five am", "wake me up at [time : five am]"),
         raw(1, "what alarms do i have", "what alarms do i have", "alarm_query")]
DEV = [raw(10, "wake me up at five am", "wake me up at [time : five am]"),  # seen
       raw(11, "wake me up at six am", "wake me up at [time : six am]")]    # unseen


def make_data(tmp_path):
    data = tmp_path / "data"
    (data / "en-US").mkdir(parents=True)
    for split, rows in [("train", TRAIN), ("dev", DEV)]:
        (data / "en-US" / f"{split}.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return data


def test_gzip_round_trip_and_same_bytes(tmp_path):
    rows = [{"id": "1", "utt": "صحيني"}, {"id": "2", "utt": "l'heure"}]
    write_jsonl(tmp_path / "a.jsonl.gz", rows)
    write_jsonl(tmp_path / "b.jsonl.gz", rows)
    assert read_jsonl(tmp_path / "a.jsonl.gz") == rows
    assert (tmp_path / "a.jsonl.gz").read_bytes()[4:8] == b"\x00\x00\x00\x00"  # mtime = 0
    assert read_jsonl(tmp_path / "a.jsonl.gz") == read_jsonl(tmp_path / "b.jsonl.gz")


def test_predictions_path_prefers_gz(tmp_path):
    assert predictions_path(tmp_path, "dev").name == "predictions_dev.jsonl"
    write_jsonl(tmp_path / "predictions_dev.jsonl.gz", [])
    assert predictions_path(tmp_path, "dev").name == "predictions_dev.jsonl.gz"


def test_seen_unseen(tmp_path):
    data, run = make_data(tmp_path), tmp_path / "run"
    run.mkdir()
    # right on the seen example, wrong value on the unseen one
    write_jsonl(run / "predictions_dev.jsonl.gz", [
        {"id": "10", "locale": "en-US", "gold": 'alarm_set(time="five am")', "pred": 'alarm_set(time="five am")'},
        {"id": "11", "locale": "en-US", "gold": 'alarm_set(time="six am")', "pred": 'alarm_set(time="five am")'},
    ])
    out = evaluate_run(run, data)
    seen, unseen = out["seen_unseen"]["en-US"]["seen"], out["seen_unseen"]["en-US"]["unseen"]
    assert (seen["n"], seen["exact_match"], seen["slot_f1"]) == (1, 1.0, 1.0)
    assert (unseen["n"], unseen["exact_match"], unseen["intent_accuracy"], unseen["slot_f1"]) == (1, 0.0, 1.0, 0.0)
    assert out["seen_unseen"]["overall"]["seen"]["n"] == 1
    assert out["results"]["overall"]["exact_match"] == 0.5
    assert json.loads((run / "metrics.json").read_text())["split"] == "dev"


def test_empty_subset_is_none(tmp_path):
    data, run = make_data(tmp_path), tmp_path / "run"
    run.mkdir()
    write_jsonl(run / "predictions_dev.jsonl.gz", [
        {"id": "11", "locale": "en-US", "gold": 'alarm_set(time="six am")', "pred": 'alarm_set(time="six am")'},
    ])
    seen = evaluate_run(run, data)["seen_unseen"]["en-US"]["seen"]
    assert seen == {"n": 0, "exact_match": None, "intent_accuracy": None, "slot_f1": None}
