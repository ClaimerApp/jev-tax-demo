# Jev tax demo: results for the 23 Oct 2026 webinar

Averages of 5 runs per model per demo, recorded 21 Oct 2026, 21:27 to 21:28 (UK). Every run completed with no errors.
Repo: github.com/ClaimerApp/jev-tax-demo. Raw runs: `out/*.json` (20 files, not in git).

## What was tested

Two demos, each sent to two hosted "System One" models through the same SDK with identical questions:

| Model | Where it runs | Model ID | Price |
|---|---|---|---|
| **Jev** | TypeSafe, US | `jev-1.13.0` | $0.042 per million input tokens |
| **EigenJev** | Eigenwelt, Berlin (EU) | `jev-latest` (serves openjev-0.1) | Free for now |

A third model, Kev (open weights, runs on a laptop), was dropped. It took about 0.9 s per bank line, so about 95 s per run instead of about 6 s.

1. **Bank lines: tax and VAT.** 106 invented bank lines (Apr to Sep 2026) for an invented UK company, Brightwell Robotics Ltd (12 staff, warehouse robots, VAT registered, does R&D). For each line the model answers three questions:
   - **Tax treatment**: Allowable / Capital / Disallowable / Not an expense
   - **VAT code**: 20% / Zero / Exempt / No VAT / Reverse charge
   - **R&D cost?**: yes/no, as a probability
2. **R&D project screen.** 12 invented project summaries. For each, the model answers: tech advance? uncertainty? mostly routine? (yes/no each), a verdict (Potentially qualifies / Borderline / Does not qualify), and evidence quality (0 to 2).

**How little the models are told.** Each request contains one bank line or one project, a one-sentence company description, and the questions with a one-line description of each answer option. That's 360 words per bank line and 262 words per project. There are no examples, no training on this data and no chart of accounts. The model never sees how the line was coded. It returns only probabilities, with no explanation.

**Answer key.** Adam (Claimer) reviewed every line and project; the answer key is his own review, not HMRC's.
- **14 bank lines were miscoded on purpose** ("planted mistakes") for the model to catch. Examples: a staff party coded as client entertaining, the director's Netflix charged to the company, insurance coded at 20% VAT instead of exempt.
- **13 bank lines can't be decided from the bank line alone** (Amazon Marketplace, PayPal, Tesco, Uber, Landsec rent). For these the correct answer is "needs a receipt", so **being unsure counts as correct**.
- 79 lines are clean: they were coded correctly and both their tax and VAT answers are known.

**Threshold.** If the model is less than **80%** confident in an answer, the line goes to a human. Comparing answers with the coding and the answer key, and applying the threshold, is ordinary code, not the model.

## Headline: bank lines (106 lines, mean of 5 runs, min to max in brackets)

| | **Jev** | **EigenJev** |
|---|---|---|
| Coding mistakes caught (of 14 planted) | **14/14, 100%** (every run) | **14/14, 100%** (every run) |
| Correct coding wrongly challenged (of 79 clean lines) | **1.6/79, 2%** (1 to 3) | **15.4/79, 19.5%** (14 to 16) |
| Sent to a human | 72/106, 68% (71 to 74) | 42.8/106, 40% (41 to 44) |
| …of which needs-receipt lines (of 13) | 13/13 | 8.8/13 (8 to 9) |
| **Correct, tax treatment** | **92%** (91 to 93) | **88%** (same every run) |
| **Correct, VAT** | **93%** (92 to 94) | **68%** (67 to 69) |
| **Correct, R&D cost** | **94%** (same every run) | **90%** (90 to 91) |
| Time for all 106 lines | 5.7 s (5.4 to 6.1) | 4.9 s (4.8 to 5.0) |
| Median time per line | 201 ms | 186 ms |
| Cost per run of 106 lines | **$0.0044** | $0 (free for now) |

"Correct" is measured the way the UI measures it. For a line with a known answer, the model's top pick matches the key, whether or not it was sure. For a needs-receipt line, the model has to be unsure.

The split below separates the model being confidently wrong from it being confident when it should have asked for a receipt:

| Per run (mean) | Jev | EigenJev |
|---|---|---|
| Confidently wrong, lines with a known answer: tax | 2.2 of 98 | 5.0 of 98 |
| Confidently wrong, lines with a known answer: VAT | **0 of 93** | **13.2 of 93** |
| Confidently wrong, lines with a known answer: R&D cost | 0 of 95 | 0 of 95 |
| Bank lines with any confidently wrong answer | **2.2 of 106** | **18.2 of 106** |
| Top pick right on known-answer lines (tax / VAT / R&D) | 94% / 92% / 100% | 93% / 70% / 100% |
| Confident without a receipt (tax / VAT / R&D cost) | 2.4 of 8 / 0.2 of 13 / 6.0 of 11 | 6.0 of 8 / 6.2 of 13 / 10.2 of 11 |
| Unsure answers (tax / VAT / R&D cost, each of 106) | 26.4 / 49.4 / 26.8 | 9.4 / 34.6 / 0.8 |

## Headline: R&D project screen (12 projects, mean of 5 runs)

| | **Jev** | **EigenJev** |
|---|---|---|
| Same verdict as Adam's review | **10/12, 83%** (every run) | **11/12, 92%** (every run) |
| Confidently wrong | **0/12** | **0/12** |
| Sent to a human | 3/12, 25% | 2/12, 17% |
| Time for all 12 projects | 0.89 s (0.67 to 1.43) | 0.59 s |
| Median time per project | 262 ms | 177 ms |
| Cost per run | $0.0004 | $0 |

Verdicts per project. The verdict was the same in all 5 runs for every project; the confidence shown is the mean. ⚠ means under 80%, so the project goes to a human.

| Project | Adam's call | Jev | EigenJev |
|---|---|---|---|
| Grip control for deformable parcels | Potentially qualifies | ✓ 98% | ✓ 100% |
| Low-temperature curing adhesive | Potentially qualifies | ✓ 97% | ✓ 100% |
| Telemetry compression for small satellites | Potentially qualifies | ✓ 98% | ✓ 100% |
| Oral film version of an existing drug | Potentially qualifies | ✓ 85% | ✓ 100% |
| Ledger throughput beyond database limits | Potentially qualifies | ✓ 97% | ✓ 100% |
| New online shop | Does not qualify | ✓ 84% | ✓ 100% |
| Move to the cloud | Does not qualify | ✓ 89% | ✓ 100% |
| Understanding customer churn | Does not qualify | ✓ 97% | ✓ 100% |
| Redesign of our meditation app | Does not qualify | ✓ 89% | ✓ 100% |
| Xero and Salesforce integration | Does not qualify | ✓ ⚠ 62% | ✓ 100% |
| Gluten-free sourdough | Does not qualify | ✗ ⚠ said Borderline, 24% | ✓ ⚠ 64% |
| AI document summaries | Does not qualify | ✗ ⚠ said Borderline, 56% | ✗ ⚠ said Potentially qualifies, 64% |

Neither model was confidently wrong on any project. Every miss came in under the threshold and would go to a human.

## Where each model went wrong (bank lines)

The same bank text often appears on several lines (e.g. a monthly GitHub charge), so the counts below are wrong answers out of all attempts across 5 runs.

**Jev.** Its mistakes on lines with a known answer were almost all flagged as unsure:
- Hetzner GPU servers for robot simulation (6 lines). The key says Allowable (rented servers); Jev said Capital 29 of 30 times, average confidence 72%, mostly unsure.
- VAT on LinkedIn job posts: said 20% instead of reverse charge (10/10, 68%, unsure).
- VAT on the Castle Pub staff party (a planted line): said No VAT instead of 20% (5/5, 67%, unsure).
- VAT on Waterstones textbooks: said 20% instead of zero (5/5, 46%, unsure).
- VAT on BT phone bills: wrong 13 of 30 times, very unsure (22%).
- VAT on a British Airways flight: wrong 3 of 5, unsure.
- Needs-receipt lines where it was confident anyway: R&D cost "No" on Amazon Marketplace (20/20, 88%) and PayPal (10/10, 86%); tax "Allowable" on Amazon (12 of 20).

**EigenJev.** It has a systematic VAT weakness and often defaults to "No VAT", frequently while confident:
- Reverse charge read as No VAT: GitHub (24 of 30, plus 6 times 20%), LinkedIn (97%), Figma (77%).
- Exempt read as No VAT: Hiscox insurance (6 lines, 87%), Royal Mail stamps (95%).
- Standard rate read as No VAT: Castle Pub staff party (99%), ABC Interiors fit-out (87%), Ford Transit van (96%), Smith & Co accountants (68%), Viking Direct (62%).
- Zero rate read as No VAT: Waterstones books (84%).
- Tax: Barclays bank charges called "Not an expense" (6 lines, 84%); Companies House fee called "Not an expense" (96%).
- Confident on needs-receipt lines: Amazon (tax), PayPal (tax, VAT and R&D), Tesco (VAT), Landsec rent (VAT), and HMRC PAYE (R&D cost; the key says this depends on whose salaries).

## Talking points the data supports

- **Both models caught all 14 planted mistakes in every run.**
- **Jev was almost never confidently wrong:** about 2 bank lines in 106 per run, and never on VAT. When it was wrong, it nearly always said it was unsure, so the line went to a human.
- **The trade-off is how many lines go to a human.** With an 80% threshold, Jev sends about 68% of lines to a human, while EigenJev sends about 40%. EigenJev pays for that by challenging about 1 in 5 correct codings (15 of 79), against about 2 of 79 for Jev, and by being confidently wrong on VAT about 13 times per run. The slider in the demo moves this trade-off live.
- **Speed and cost:** all 106 bank lines take about 5 to 6 seconds. That costs under half a cent per run on Jev ($0.0044, about $0.00004 per line) and nothing on EigenJev for now.
- **R&D screen:** both models agree with the reviewer on 10 to 11 of 12 projects and are never confidently wrong. The disagreements are the two projects a reviewer would expect to argue about: the bakery recipe trials and the AI document summaries.
- **Very stable:** answers barely changed across 5 runs. EigenJev's tax answers were identical every time, and run-to-run variation is mostly in speed.

## Caveats

- All data is invented, and the answer key is one reviewer's judgement, not HMRC's.
- The samples are small: 106 bank lines and 12 projects.
- Every figure depends on the 80% threshold. Lowering it sends fewer lines to a human, at the cost of more confident mistakes.
- Model versions were pinned (`jev-1.13.0`; EigenJev only offers `jev-latest`).
- The input token counts differ between the models for identical requests (Jev 103,929 per ledger run, EigenJev 74,694), presumably because they count tokens differently.
