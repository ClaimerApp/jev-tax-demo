"""Shared by the terminal runner and the web UI: load a dataset, ask a backend, decide what a human should look at.

Jev makes the judgement; this code owns the rules (compare with the books, apply the confidence threshold).
"""

import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from backends import BACKENDS as _BACKENDS, MODELS as _MODELS, PRICE_PER_M_INPUT as _PRICE, client  # noqa: E402

import tax_questions as Q  # noqa: E402

BACKENDS = dict(_BACKENDS) | {"mock": {"base_url": "(offline)", "key": None, "runs_in": "Mock: rehearsal only"}}
MODELS = dict(_MODELS) | {"mock": "random-not-a-model"}
PRICE = dict(_PRICE) | {"mock": 0.0}
WORKERS = {"jev": 4, "eigenjev": 4, "mock": 6}

DATASETS = {
    "ledger": HERE / "data" / "ledger.json",
    "rd": HERE / "data" / "rd_projects.json",
}


def load(dataset: str) -> dict:
    return json.loads(DATASETS[dataset].read_text())


def build(dataset: str, data: dict, item: dict) -> tuple[dict, dict]:
    if dataset == "ledger":
        return Q.ledger_state(data["company"], item), Q.LEDGER_QUESTIONS
    return Q.rd_state(item), Q.RD_QUESTIONS


# ---------------------------------------------------------------- mock backend (rehearsal without keys or network)

class _Resp(dict):
    def model_dump(self, mode: str = "json") -> dict:
        return dict(self)


def _mock_choice(options: list[str], key: str | None, rng: random.Random) -> dict:
    if key is None:
        pick, conf = rng.choice(options), rng.uniform(0.35, 0.68)
    elif rng.random() < 0.9:
        pick, conf = key, rng.uniform(0.82, 0.99)
    else:
        pick, conf = rng.choice([o for o in options if o != key]), rng.uniform(0.45, 0.8)
    rest = (1 - conf) / (len(options) - 1)
    return {"type": "choice", "choice": pick, "confidence": round(conf, 3),
            "probabilities": {o: round(conf if o == pick else rest, 3) for o in options}}


def _mock_noul(key: bool | None, rng: random.Random) -> dict:
    if key is None:
        return {"type": "noul", "noul": round(rng.uniform(0.3, 0.7), 3)}
    p = rng.uniform(0.75, 0.98) if rng.random() < 0.88 else rng.uniform(0.2, 0.5)
    return {"type": "noul", "noul": round(p if key else 1 - p, 3)}


def mock_answer(dataset: str, item: dict) -> _Resp:
    rng = random.Random()
    time.sleep(rng.uniform(0.12, 0.38))
    if dataset == "ledger":
        k = item["key"]
        answers = {
            "ct": _mock_choice(list(Q.CT_LABELS), k["ct"], rng),
            "vat": _mock_choice(list(Q.VAT_LABELS), k["vat"], rng),
            "rd": _mock_noul(k["rd"], rng),
        }
    else:
        exp = item["expected"]
        good = exp == "qualifies"
        answers = {
            "advance": _mock_noul(good if exp != "borderline" else None, rng),
            "uncertainty": _mock_noul(good if exp != "borderline" else None, rng),
            "routine": _mock_noul((not good) if exp != "borderline" else None, rng),
            "verdict": _mock_choice(list(Q.VERDICT_LABELS), exp, rng),
            "evidence": {"type": "score", "score": round(rng.uniform(0.2, 1.9) if not good else rng.uniform(1.4, 2.0), 2),
                         "confidence": 0.7, "legend": {}, "probabilities": {}},
        }
    return _Resp(model="mock", usage={"input_tokens": 0, "output_tokens": 0}, answers=answers)


class MockClient:
    def system_one(self, state, questions):  # only used by connect()'s ping
        return _Resp(model="mock", usage={"input_tokens": 0}, answers={})


# ---------------------------------------------------------------- asking

def connect(name: str):
    """Client for a backend, or raise if it's misconfigured or unreachable."""
    if name == "mock":
        return MockClient()
    c = client(name)
    c.system_one({"text": "ping"}, {"ok": Q.RD})
    return c


def ask(c, name: str, dataset: str, data: dict, item: dict, t0: float) -> dict:
    state, questions = build(dataset, data, item)
    rec = {"id": item["id"]}
    start = time.perf_counter()
    try:
        resp = mock_answer(dataset, item) if name == "mock" else c.system_one(state, questions)
        rec["response"] = resp.model_dump(mode="json")
    except Exception as e:  # one failed line is logged, never a crash
        rec["error"] = f"{type(e).__name__}: {e}"
    end = time.perf_counter()
    rec["ms"] = (end - start) * 1000
    rec["t"] = end - t0
    return rec


def stream(c, name: str, dataset: str, data: dict, items: list[dict]) -> Iterator[dict]:
    """Records in completion order."""
    t0 = time.perf_counter()
    with ThreadPoolExecutor(WORKERS.get(name, 4)) as pool:
        futures = [pool.submit(ask, c, name, dataset, data, it, t0) for it in items]
        for f in as_completed(futures):
            yield f.result()


# ---------------------------------------------------------------- rules (code, not the model)

def ledger_status(item: dict, answers: dict, threshold: float) -> dict:
    """ok / check (model unsure) / flag (model confident the books are wrong), per question and overall."""
    out = {}
    for q, posted in (("ct", item["posted"]["ct"]), ("vat", item["posted"]["vat"])):
        a = answers[q]
        if a["confidence"] < threshold:
            out[q] = "check"
        elif a["choice"] != posted:
            out[q] = "flag"
        else:
            out[q] = "ok"
    out["line"] = "flag" if "flag" in out.values() else "check" if "check" in out.values() else "ok"
    return out


def summarise_ledger(items: list[dict], records: list[dict], threshold: float, price: float | None) -> dict:
    by_id = {it["id"]: it for it in items}
    ok = [r for r in records if not r.get("error")]
    st = {r["id"]: ledger_status(by_id[r["id"]], r["response"]["answers"], threshold) for r in ok}
    planted = [i for i in st if by_id[i]["planted_mistake"]]
    clean = [i for i in st if not by_id[i]["planted_mistake"] and None not in (by_id[i]["key"]["ct"], by_id[i]["key"]["vat"])]
    ambiguous = [i for i in st if None in (by_id[i]["key"]["ct"], by_id[i]["key"]["vat"])]

    def acc(q):
        rows = [r for r in ok if by_id[r["id"]]["key"][q] is not None]
        return sum(r["response"]["answers"][q]["choice"] == by_id[r["id"]]["key"][q] for r in rows) / len(rows) if rows else None

    rd_rows = [r for r in ok if by_id[r["id"]]["key"]["rd"] is not None]
    ms = sorted(r["ms"] for r in ok)
    tokens = sum((r["response"].get("usage") or {}).get("input_tokens") or 0 for r in ok)
    return {
        "lines": len(records), "errors": len(records) - len(ok),
        "flag": sum(s["line"] == "flag" for s in st.values()),
        "check": sum(s["line"] == "check" for s in st.values()),
        "ok": sum(s["line"] == "ok" for s in st.values()),
        "planted": len(planted),
        "planted_flagged": sum(st[i]["line"] == "flag" for i in planted),
        "planted_surfaced": sum(st[i]["line"] != "ok" for i in planted),
        "false_alarms": sum(st[i]["line"] == "flag" for i in clean),
        "ambiguous": len(ambiguous),
        "ambiguous_to_human": sum(st[i]["line"] != "ok" for i in ambiguous),
        "acc_ct": acc("ct"), "acc_vat": acc("vat"),
        "acc_rd": (sum((r["response"]["answers"]["rd"]["noul"] >= 0.5) == by_id[r["id"]]["key"]["rd"] for r in rd_rows) / len(rd_rows)) if rd_rows else None,
        "p50_ms": ms[len(ms) // 2] if ms else None,
        "wall_s": max((r["t"] for r in records), default=0),
        "cost": None if price is None else tokens * price / 1e6,
        "tokens": tokens,
    }


def summarise_rd(items: list[dict], records: list[dict]) -> dict:
    by_id = {it["id"]: it for it in items}
    ok = [r for r in records if not r.get("error")]
    right = sum(r["response"]["answers"]["verdict"]["choice"] == by_id[r["id"]]["expected"] for r in ok)
    return {"projects": len(records), "errors": len(records) - len(ok), "agree": right,
            "wall_s": max((r["t"] for r in records), default=0)}
