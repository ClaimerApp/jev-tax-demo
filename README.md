# Jev tax demo

Live demos from the Claimer webinar *Have you met Jev?* (Friday 23 October 2026): TypeSafe's Jev, a "System One" decision model, run on UK tax tasks.

Jev doesn't write text. You give it some facts and a set of options, and it returns a pick from those options with a probability. These demos show what that looks like on bookkeeping review and R&D screening, and where it needs a person.

| Tab | What happens | The point it makes |
|---|---|---|
| **Bank lines: tax and VAT** | 106 bank lines for an invented company (Brightwell Robotics Ltd). Jev decides the corporation tax treatment, VAT code and "R&D cost?" for each line, without seeing how it was posted. Code compares its answers with the books. | Review every line, not a sample. People only see the disagreements and the lines Jev is unsure about. |
| **R&D project screen** | 12 invented project summaries. Five questions each (advance? uncertainty? routine? verdict, evidence quality), one call per project. | Eligibility is a judgement call. Jev gives a consistent first pass with a probability, not a decision to hand to HMRC. |

**All data is invented.** Payee names are real UK suppliers so the lines look familiar, but no transaction, project or client is real.

## Run it

You need Python 3.10+ and an API key for at least one backend.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                 # add your TypeSafe key (and EigenJev if you have one)
.venv/bin/python server.py           # http://localhost:8081
```

Pick a backend, press **Run** (or `r`). `k` toggles the answer key. Click a ledger row to see the full probability spread. The slider sets the confidence below which a line goes to a person.

| Backend | Runs in | Notes |
|---|---|---|
| `jev` | TypeSafe, US | Needs `TYPESAFE_API_KEY` |
| `eigenjev` | Eigenwelt, Berlin | Same API, different base URL |
| `kev` | Your machine | Open weights; start the Kev server first ([jaredpalmer/kev](https://github.com/jaredpalmer/kev)) |
| `mock` | Nowhere | Random answers under an orange banner. For rehearsing the clicks only; never present its numbers |

All backends speak the same API, so `backends.py` swaps only the base URL.

Terminal version (also records a run):

```bash
.venv/bin/python run.py --dataset ledger --backend jev [--threshold 0.8]
.venv/bin/python run.py --dataset rd --backend jev
```

Every run, from the web page or the terminal, is saved to `out/`. Pick one from **Replay** and it plays back at the original pace with no network: the backup if the API is slow on the day.

## What's in the ledger

- **14 planted posting mistakes:** a client dinner posted to travel, a client hospitality box posted as a staff event, the staff summer party posted as client entertaining, a parking penalty in travel, an HMRC penalty and the corporation tax payment in professional fees, VAT claimed on a company car, German hosting coded at 20% instead of reverse charge, rail fares and insurance coded at 20%, a MacBook expensed as software, a workshop fit-out in general expenses, and a director's Netflix and a child car seat charged to the company.
- **13 lines that can't be decided from the bank line alone** (Amazon Marketplace, Tesco, PayPal, Uber, rent where the option to tax is unknown). The right answer is "a person looks at the receipt".
- The answer key is a reading of standard UK treatment written for a demo, not advice. The R&D "my call" column is likewise one reviewer's judgement, not HMRC's.

## Files

| File | What |
|---|---|
| `make_ledger.py` | Generates `data/ledger.json` (seeded, so it's the same every time) |
| `data/rd_projects.json` | The 12 project summaries |
| `tax_questions.py` | Every question, word for word |
| `engine.py` | Asking, the mock backend, and the rules (threshold, compare with the books) |
| `backends.py` | Jev, EigenJev and Kev: same SDK, different base URL |
| `server.py`, `static/index.html` | The web UI |
| `run.py` | The terminal version |

Built on [assembledadam/typesafe-jev-benchmarking](https://github.com/assembledadam/typesafe-jev-benchmarking), which runs the same three backends on email triage.

## Privacy

Running the hosted backends sends each bank line or project summary to TypeSafe (US) or Eigenwelt (EU). That's fine for this invented data. Check the data terms before using real client data with any of them.

## Licence

MIT
