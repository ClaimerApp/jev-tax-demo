"""Terminal version of the tax demo. Also the quickest way to record a backup before the webinar.

python run.py --dataset ledger --backend jev [--threshold 0.8]
python run.py --dataset rd --backend jev
python run.py --dataset ledger --backend mock     # rehearsal: random answers, no network
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from rich.console import Console

import engine
import tax_questions as Q

console = Console(highlight=False)
OUT = Path(__file__).parent / "out"
COL = {"ok": "green", "check": "yellow", "flag": "bold red"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=list(engine.DATASETS), default="ledger")
    ap.add_argument("--backend", choices=list(engine.BACKENDS), default="jev")
    ap.add_argument("--threshold", type=float, default=0.8, help="below this confidence, a human checks the line")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    data = engine.load(args.dataset)
    items = data["items"][: args.limit]
    by_id = {it["id"]: it for it in items}
    c = engine.connect(args.backend)
    console.rule(f"[bold]{args.backend}[/] · {engine.BACKENDS[args.backend]['runs_in']} · {engine.MODELS[args.backend]} · {args.dataset}")

    records = []
    for rec in engine.stream(c, args.backend, args.dataset, data, items):
        records.append(rec)
        it = by_id[rec["id"]]
        if rec.get("error"):
            console.print(f"  {rec['id']}  [red]error: {rec['error'][:70]}[/]")
            continue
        a = rec["response"]["answers"]
        if args.dataset == "ledger":
            s = engine.ledger_status(it, a, args.threshold)
            console.print(
                f"  {it['bank_text'][:26]:<26} £{it['amount']:>9,.2f}  "
                f"CT {Q.CT_LABELS[a['ct']['choice']]:<14} {a['ct']['confidence']:.2f}  "
                f"VAT {Q.VAT_LABELS[a['vat']['choice']]:<14} {a['vat']['confidence']:.2f}  "
                f"[{COL[s['line']]}]{s['line']:<5}[/]  [dim]{rec['ms']:>4.0f} ms[/]"
            )
        else:
            v = a["verdict"]
            mark = "✓" if v["choice"] == it["expected"] else "✗"
            console.print(f"  {it['title'][:40]:<40} {Q.VERDICT_LABELS[v['choice']]:<17} {v['confidence']:.2f} {mark}  [dim]{rec['ms']:>4.0f} ms[/]")

    run = {"dataset": args.dataset, "backend": args.backend, "runs_in": engine.BACKENDS[args.backend]["runs_in"],
           "model": engine.MODELS[args.backend], "recorded": datetime.now().isoformat(timespec="seconds"), "records": records}
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{args.dataset}__{args.backend}__{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(run, ensure_ascii=False))

    if args.dataset == "ledger":
        s = engine.summarise_ledger(items, records, args.threshold, engine.PRICE.get(args.backend))
        console.print(json.dumps(s, indent=1, default=lambda x: round(x, 4)))
    else:
        console.print(engine.summarise_rd(items, records))
    console.print(f"[dim]recorded to {path}[/]")


if __name__ == "__main__":
    main()
