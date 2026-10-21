"""Web UI for the tax demo: every bank line reviewed live, or a stack of R&D projects screened.

.venv/bin/python server.py   ->  http://localhost:8081
"""

import json
import time
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

import engine

HERE = Path(__file__).parent
OUT = HERE / "out"
app = FastAPI()


def event(kind: str, data: dict) -> str:
    return f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def for_screen(rec: dict) -> dict:
    out = {"id": rec["id"], "ms": rec["ms"], "error": rec.get("error")}
    if not rec.get("error"):
        out["answers"] = rec["response"]["answers"]
        out["tokens"] = (rec["response"].get("usage") or {}).get("input_tokens") or 0
    return out


@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/config")
def config():
    return {
        "backends": [{"name": n, "runs_in": b["runs_in"], "model": engine.MODELS[n], "price": engine.PRICE.get(n)}
                     for n, b in engine.BACKENDS.items()],
        "recordings": sorted((p.name for p in OUT.glob("*.json")), reverse=True) if OUT.exists() else [],
    }


@app.get("/api/items")
def items(dataset: str):
    if dataset not in engine.DATASETS:
        raise HTTPException(404)
    return engine.load(dataset)


@app.get("/api/prompt")
def prompt(dataset: str):
    """Everything one request carries, built by the same code as a real run: one example item and every question."""
    if dataset not in engine.DATASETS:
        raise HTTPException(404)
    data = engine.load(dataset)
    item = next((i for i in data["items"] if i.get("planted_mistake")), data["items"][0])
    state, questions = engine.build(dataset, data, item)
    return {"state": state, "questions": {k: q.model_dump(mode="json") for k, q in questions.items()}}


@app.get("/api/run")
def run(dataset: str, backend: str):
    if dataset not in engine.DATASETS or backend not in engine.BACKENDS:
        raise HTTPException(404)
    data = engine.load(dataset)

    def events():
        yield event("start", {"total": len(data["items"]), "backend": backend})
        try:
            c = engine.connect(backend)
        except Exception as e:
            yield event("failed", {"error": f"{type(e).__name__}: {str(e)[:160]}"})
            return
        records = []
        for rec in engine.stream(c, backend, dataset, data, data["items"]):
            records.append(rec)
            yield event("result", for_screen(rec))
        OUT.mkdir(exist_ok=True)
        name = f"{dataset}__{backend}__{datetime.now():%Y%m%d-%H%M%S}.json"
        (OUT / name).write_text(json.dumps({
            "dataset": dataset, "backend": backend, "runs_in": engine.BACKENDS[backend]["runs_in"],
            "model": engine.MODELS[backend], "recorded": datetime.now().isoformat(timespec="seconds"), "records": records,
        }, ensure_ascii=False))
        yield event("done", {"recording": name})

    return StreamingResponse(events(), media_type="text/event-stream")


@app.get("/api/replay")
def replay(file: str):
    path = OUT / Path(file).name
    if not path.exists():
        raise HTTPException(404)
    run = json.loads(path.read_text())

    def events():
        yield event("start", {"total": len(run["records"]), "backend": run["backend"], "replay": True})
        start = time.perf_counter()
        for rec in sorted(run["records"], key=lambda r: r["t"]):
            time.sleep(max(0.0, rec["t"] - (time.perf_counter() - start)))
            yield event("result", for_screen(rec))
        yield event("done", {"recording": path.name})

    return StreamingResponse(events(), media_type="text/event-stream")


if __name__ == "__main__":
    # Watch mode: restarts on any .py change. index.html and data/*.json are read per request, so a browser refresh is enough.
    uvicorn.run("server:app", host="127.0.0.1", port=8081, log_level="warning", reload=True, reload_dirs=[str(HERE)])
