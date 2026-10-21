"""The questions each System One backend is asked, word for word. Same text for every backend."""

from typesafe_sdk import Choice, Noul, Score

# ---------------------------------------------------------------- Ledger review: one bank line at a time

CT_LABELS = {
    "allowable": "Allowable",
    "capital": "Capital",
    "disallowable": "Disallowable",
    "not_expense": "Not an expense",
}
VAT_LABELS = {
    "standard": "20%",
    "zero": "Zero",
    "exempt": "Exempt",
    "no_vat": "No VAT",
    "reverse_charge": "Reverse charge",
}

CT = Choice(
    instructions=(
        "How should `bank_line` be treated for UK corporation tax in `company`'s accounts? "
        "Judge from the bank text, the receipt note if there is one, the amount and what the company does."
    ),
    criteria={
        "allowable": (
            "Allowable revenue expense: an ordinary running cost of the trade, such as software, rent, travel, "
            "staff-only events, insurance, rates, professional fees or materials."
        ),
        "capital": (
            "Capital expenditure: buying an asset that lasts for years, such as computers, servers, vehicles, "
            "machinery or building works. Relief comes through capital allowances, not as an expense."
        ),
        "disallowable": (
            "A business payment that is not deductible: entertaining clients, prospects or other non-staff guests "
            "(including staff who attend as hosts), and fines or penalties."
        ),
        "not_expense": (
            "Not an expense of the company at all: paying tax already owed (PAYE, VAT, corporation tax), transfers "
            "between the company's own accounts, loans and repayments, and the director's personal spending, "
            "which is charged to the director's loan account."
        ),
    },
)

VAT = Choice(
    instructions=(
        "Which VAT code should `company` use when posting `bank_line`? The company is VAT registered "
        "and can reclaim input VAT on its business costs, except where recovery is blocked."
    ),
    criteria={
        "standard": "20%: a UK VAT-registered supplier charging standard-rated VAT that the company can reclaim.",
        "zero": "Zero rated: VAT at 0%, for example rail and air fares and books.",
        "exempt": "Exempt: insurance, postage stamps, bank and other financial charges.",
        "no_vat": (
            "No VAT to reclaim: outside the scope of VAT (tax payments, business rates, statutory fees, transfers, "
            "loans, penalties), a supplier that is not VAT registered, or input VAT that is blocked (client "
            "entertaining, cars with private use, personal spending)."
        ),
        "reverse_charge": "Reverse charge: business services bought from a supplier based outside the UK.",
    },
)

RD = Noul(
    instructions=(
        "Suppose `company`'s project work counts as R&D. Is `bank_line` a cost in a category that can qualify "
        "for UK R&D tax relief: staff costs, software, cloud computing or data licences used in the R&D, "
        "consumable materials used up in the R&D, or R&D subcontracted to another organisation? "
        "Capital equipment, travel, marketing and general overheads do not qualify."
    ),
)


def ledger_state(company: dict, item: dict) -> dict:
    line = {
        "date": item["date"],
        "bank_text": item["bank_text"],
        "amount_out": f"£{item['amount']:,.2f}",
    }
    if item.get("receipt_note"):
        line["receipt_note"] = item["receipt_note"]
    return {"company": company, "bank_line": line}


LEDGER_QUESTIONS = {"ct": CT, "vat": VAT, "rd": RD}

# ---------------------------------------------------------------- R&D screen: one project summary at a time

VERDICT_LABELS = {"qualifies": "Potentially qualifies", "borderline": "Borderline", "does_not_qualify": "Does not qualify"}

ADVANCE = Noul(
    instructions=(
        "Does `project` seek an advance in overall knowledge or capability in a field of science or technology, "
        "beyond what is already publicly available and beyond just the company's own knowledge?"
    ),
)
UNCERTAINTY = Noul(
    instructions=(
        "At the start of `project`, was there scientific or technological uncertainty: something a competent "
        "professional in the field could not readily know or work out?"
    ),
)
ROUTINE = Noul(
    instructions=(
        "Is `project` mainly routine or non-technological work: applying existing products, tools or documented "
        "methods, visual or design changes, or commercial and social-science research?"
    ),
)
VERDICT = Choice(
    instructions="Under the UK DSIT guidelines on the meaning of R&D, how does `project` look for an R&D tax relief claim?",
    criteria={
        "qualifies": "Likely qualifies: a clear technological advance sought, with uncertainty resolved by systematic work.",
        "borderline": "Borderline: might qualify, but needs more evidence of an advance or of real technological uncertainty before claiming.",
        "does_not_qualify": "Does not qualify: routine, commercial, aesthetic, or outside science and technology.",
    },
)
EVIDENCE = Score(
    instructions="How well does the summary in `project` evidence the claim for an HMRC caseworker?",
    criteria=[
        "Assertions only: no technical detail",
        "Some technical detail, but the uncertainties are vague",
        "Specific uncertainties, what was tried, what failed and the outcome",
    ],
)


def rd_state(item: dict) -> dict:
    return {"project": {"company": item["company"], "title": item["title"], "summary": item["summary"]}}


RD_QUESTIONS = {"advance": ADVANCE, "uncertainty": UNCERTAINTY, "routine": ROUTINE, "verdict": VERDICT, "evidence": EVIDENCE}
