"""Builds data/ledger.json: six months of bank lines for a made-up UK company, already posted to the books.

Every line has an answer key (what a careful reviewer would post) and the coding the bookkeeper actually used.
A handful of lines carry common mistakes, and a few are genuinely ambiguous from the bank line alone.
No real client data: payees are real UK suppliers so the lines look familiar, but every transaction is invented.

python make_ledger.py      # deterministic (seeded), rewrites data/ledger.json
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 23_10_2026
OUT = Path(__file__).parent / "data" / "ledger.json"

COMPANY = {
    "name": "Brightwell Robotics Ltd",
    "about": (
        "UK limited company (12 staff) that designs and builds warehouse robots. VAT registered on the standard "
        "scheme, quarterly returns. Carries out R&D. Year end 31 March 2027. Director: Sam Patel."
    ),
}

# Chart of accounts: code -> (name, corporation tax treatment that posting implies)
NOMINALS = {
    "0030": ("Office & computer equipment (fixed asset)", "capital"),
    "0040": ("Motor vehicles (fixed asset)", "capital"),
    "0050": ("Leasehold improvements (fixed asset)", "capital"),
    "5000": ("Cost of sales: components", "allowable"),
    "7100": ("Rent", "allowable"),
    "7300": ("Insurance", "allowable"),
    "7400": ("Travel", "allowable"),
    "7500": ("Postage & stationery", "allowable"),
    "7550": ("Telephone & internet", "allowable"),
    "7600": ("Legal & professional fees", "allowable"),
    "7700": ("Software & subscriptions", "allowable"),
    "7750": ("Bank charges", "allowable"),
    "7800": ("Advertising & recruitment", "allowable"),
    "7900": ("Entertaining: clients", "disallowable"),
    "7910": ("Staff welfare & events", "allowable"),
    "8000": ("Fines & penalties", "disallowable"),
    "8100": ("Business rates", "allowable"),
    "8200": ("R&D consumables", "allowable"),
    "8300": ("Subcontracted research", "allowable"),
    "9000": ("General expenses", "allowable"),
    "2200": ("VAT control", "not_expense"),
    "2210": ("PAYE & NI control", "not_expense"),
    "2300": ("Corporation tax", "not_expense"),
    "2400": ("Director's loan account", "not_expense"),
    "1210": ("Savings account", "not_expense"),
}

# VAT codes as they appear in the books (Xero-style names)
VAT_CODES = {
    "standard": "20% (VAT on Expenses)",
    "zero": "Zero Rated Expenses",
    "exempt": "Exempt Expenses",
    "no_vat": "No VAT",
    "reverse_charge": "Reverse Charge Expenses (20%)",
}

# Each template: bank text, optional receipt note, amount range, how many times it appears,
# the answer key (ct, vat, rd) and the correct posting. `mistake` is a plausible wrong posting.
# `None` in the answer key = genuinely can't tell from the bank line; a human should look.
T = [
    # Software and cloud: overseas B2B services, so reverse charge
    dict(bank="HETZNER ONLINE GMBH", note="GPU servers for robot motion simulation", amt=(380, 2400), n=6,
         ct="allowable", vat="reverse_charge", rd=True, post=("7700", "reverse_charge"), mistake=("7700", "standard")),
    dict(bank="GITHUB, INC. GITHUB.COM", note=None, amt=(84, 84), n=6,
         ct="allowable", vat="reverse_charge", rd=True, post=("7700", "reverse_charge")),
    dict(bank="FIGMA, INC.", note="Design seats for marketing website", amt=(45, 45), n=3,
         ct="allowable", vat="reverse_charge", rd=False, post=("7700", "reverse_charge")),
    dict(bank="LINKEDIN IRL JOBS", note="Job post: embedded engineer", amt=(299, 495), n=2,
         ct="allowable", vat="reverse_charge", rd=False, post=("7800", "reverse_charge")),
    dict(bank="SOLIDWORKS DASSAULT SYS UK", note="CAD licence renewal, engineering team", amt=(4200, 4200), n=1,
         ct="allowable", vat="standard", rd=True, post=("7700", "standard")),
    # Ordinary UK purchases, 20%
    dict(bank="BT GROUP PLC DD", note=None, amt=(118, 126), n=6,
         ct="allowable", vat="standard", rd=False, post=("7550", "standard")),
    dict(bank="VIKING DIRECT", note="Printer paper, toner", amt=(42, 190), n=3,
         ct="allowable", vat="standard", rd=False, post=("7500", "standard")),
    dict(bank="RS COMPONENTS LTD", note="Motor drivers + sensors for prototype gripper", amt=(160, 1850), n=5,
         ct="allowable", vat="standard", rd=True, post=("8200", "standard")),
    dict(bank="FARNELL UK", note="PCB test components", amt=(95, 640), n=3,
         ct="allowable", vat="standard", rd=True, post=("8200", "standard")),
    dict(bank="UNIVERSITY OF SURREY RES", note="Grip-force research contract, stage 2", amt=(12500, 12500), n=1,
         ct="allowable", vat="standard", rd=True, post=("8300", "standard")),
    dict(bank="SMITH & CO ACCOUNTANTS", note="Q1 bookkeeping + VAT return", amt=(780, 780), n=2,
         ct="allowable", vat="standard", rd=False, post=("7600", "standard")),
    dict(bank="PREMIER INN 4421", note="Hotel, customer site install Leeds", amt=(89, 142), n=3,
         ct="allowable", vat="standard", rd=False, post=("7400", "standard")),
    dict(bank="THE CASTLE PUB - STAFF", note="Team summer party (all staff invited)", amt=(1140, 1140), n=1,
         ct="allowable", vat="standard", rd=False, post=("7910", "standard"), mistake=("7900", "no_vat")),
    dict(bank="REGUS MGMT UK", note="Meeting room hire, London", amt=(210, 210), n=1,
         ct="allowable", vat="standard", rd=False, post=("7100", "standard")),
    # Zero rated
    dict(bank="TRAINLINE.COM", note="Return to Birmingham, customer visit", amt=(46, 182), n=5,
         ct="allowable", vat="zero", rd=False, post=("7400", "zero"), mistake=("7400", "standard")),
    dict(bank="WATERSTONES", note="Control systems textbooks", amt=(38, 96), n=1,
         ct="allowable", vat="zero", rd=False, post=("7500", "zero")),
    dict(bank="BRITISH AIRWAYS 125", note="LHR-FRA, trade show", amt=(214, 214), n=1,
         ct="allowable", vat="zero", rd=False, post=("7400", "zero")),
    # Exempt
    dict(bank="HISCOX INSURANCE DD", note="Business insurance premium", amt=(186, 186), n=6,
         ct="allowable", vat="exempt", rd=False, post=("7300", "exempt"), mistake=("7300", "standard")),
    dict(bank="ROYAL MAIL GROUP", note="Stamps", amt=(28, 64), n=2,
         ct="allowable", vat="exempt", rd=False, post=("7500", "exempt")),
    dict(bank="BARCLAYS BANK CHARGES", note=None, amt=(18.5, 42), n=6,
         ct="allowable", vat="exempt", rd=False, post=("7750", "exempt")),
    # No VAT: outside the scope, or blocked
    dict(bank="CROYDON COUNCIL NNDR", note="Business rates", amt=(612, 612), n=6,
         ct="allowable", vat="no_vat", rd=False, post=("8100", "no_vat")),
    dict(bank="COMPANIES HOUSE", note="Confirmation statement", amt=(34, 34), n=1,
         ct="allowable", vat="no_vat", rd=False, post=("7600", "no_vat")),
    dict(bank="HMRC CUMBERNAULD PAYE", note="Monthly PAYE/NIC", amt=(9400, 11200), n=5,
         ct="not_expense", vat="no_vat", rd=None, post=("2210", "no_vat")),
    dict(bank="HMRC VAT", note="VAT return Q1", amt=(14800, 14800), n=1,
         ct="not_expense", vat="no_vat", rd=False, post=("2200", "no_vat")),
    dict(bank="HMRC CORPORATION TAX", note="CT for year to 31/3/26", amt=(31200, 31200), n=1,
         ct="not_expense", vat="no_vat", rd=False, post=("2300", "no_vat"), mistake=("7600", "no_vat")),
    dict(bank="TRANSFER TO SAVER 4471", note=None, amt=(20000, 20000), n=2,
         ct="not_expense", vat="no_vat", rd=False, post=("1210", "no_vat")),
    dict(bank="S PATEL DLA REPAYMENT", note="Repay director's loan", amt=(5000, 5000), n=1,
         ct="not_expense", vat="no_vat", rd=False, post=("2400", "no_vat")),
    # Disallowable
    dict(bank="THE IVY CHELSEA GARDEN", note="Dinner with Acme Logistics (prospect)", amt=(386, 386), n=1,
         ct="disallowable", vat="no_vat", rd=False, post=("7900", "no_vat"), mistake=("7400", "standard")),
    dict(bank="TWICKENHAM HOSPITALITY", note="Box for 6, 4 customers + 2 staff", amt=(2880, 2880), n=1,
         ct="disallowable", vat="no_vat", rd=False, post=("7900", "no_vat"), mistake=("7910", "standard")),
    dict(bank="TFL PCN WESTMINSTER", note="Parking penalty, van", amt=(80, 80), n=1,
         ct="disallowable", vat="no_vat", rd=False, post=("8000", "no_vat"), mistake=("7400", "no_vat")),
    dict(bank="HMRC LATE FILING PENALTY", note=None, amt=(100, 100), n=1,
         ct="disallowable", vat="no_vat", rd=False, post=("8000", "no_vat"), mistake=("7600", "no_vat")),
    dict(bank="NETFLIX.COM", note="Director's personal subscription on company card", amt=(18.99, 18.99), n=2,
         ct="not_expense", vat="no_vat", rd=False, post=("2400", "no_vat"), mistake=("7700", "standard")),
    dict(bank="HALFORDS 0412", note="Child car seat", amt=(149, 149), n=1,
         ct="not_expense", vat="no_vat", rd=False, post=("2400", "no_vat"), mistake=("0030", "standard")),
    # Capital
    dict(bank="APPLE STORE R245", note="MacBook Pro for new firmware engineer", amt=(2399, 2399), n=1,
         ct="capital", vat="standard", rd=False, post=("0030", "standard"), mistake=("7700", "standard")),
    dict(bank="DELL CORP LTD", note="PowerEdge server for office file storage", amt=(4820, 4820), n=1,
         ct="capital", vat="standard", rd=False, post=("0030", "standard")),
    dict(bank="FORD TRANSIT CENTRE", note="Transit Custom van, deposit", amt=(8500, 8500), n=1,
         ct="capital", vat="standard", rd=False, post=("0040", "standard")),
    dict(bank="BMW FINANCIAL SVCS", note="BMW i4 company car, deposit", amt=(6000, 6000), n=1,
         ct="capital", vat="no_vat", rd=False, post=("0040", "no_vat"), mistake=("0040", "standard")),
    dict(bank="ABC INTERIORS LTD", note="Workshop partitioning and fit-out", amt=(18400, 18400), n=1,
         ct="capital", vat="standard", rd=False, post=("0050", "standard"), mistake=("9000", "standard")),
    # Ambiguous from the bank line: a reviewer would want the receipt
    dict(bank="AMZN MKTP UK*2K4", note=None, amt=(23, 189), n=4,
         ct=None, vat=None, rd=None, post=("9000", "standard")),
    dict(bank="UBER *TRIP", note=None, amt=(14, 38), n=3,
         ct="allowable", vat=None, rd=False, post=("7400", "no_vat")),
    dict(bank="TESCO STORES 3021", note=None, amt=(22, 71), n=2,
         ct=None, vat=None, rd=False, post=("7910", "standard")),
    dict(bank="PAYPAL *JHARRIS", note=None, amt=(150, 450), n=2,
         ct=None, vat=None, rd=None, post=("9000", "no_vat")),
    dict(bank="LANDSEC PROPERTIES DD", note="Quarterly rent, Croydon workshop", amt=(7250, 7250), n=2,
         ct="allowable", vat=None, rd=False, post=("7100", "standard")),
]

PLANTED_TARGET = 14  # roughly one line in ten carries a mistake


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    for t in T:
        for _ in range(t["n"]):
            lo, hi = t["amt"]
            amount = lo if lo == hi else round(rng.uniform(lo, hi), 2)
            rows.append((t, amount))

    # Choose which lines carry a mistake: one per mistake-capable template first, then more at random.
    candidates = [i for i, (t, _) in enumerate(rows) if t.get("mistake")]
    first = {}
    for i in candidates:
        first.setdefault(rows[i][0]["bank"], i)
    planted = set(first.values())
    rest = [i for i in candidates if i not in planted]
    rng.shuffle(rest)
    planted |= set(rest[: max(0, PLANTED_TARGET - len(planted))])

    start = date(2026, 4, 1)
    items = []
    for i, (t, amount) in enumerate(rows):
        nominal, vat = t["mistake"] if i in planted else t["post"]
        items.append({
            "date": (start + timedelta(days=rng.randrange(0, 183))).isoformat(),
            "bank_text": t["bank"],
            "receipt_note": t["note"],
            "amount": amount,
            "posted": {
                "nominal": f"{nominal} {NOMINALS[nominal][0]}",
                "ct": NOMINALS[nominal][1],
                "vat": vat,
                "vat_label": VAT_CODES[vat],
            },
            "key": {"ct": t["ct"], "vat": t["vat"], "rd": t["rd"]},
            "planted_mistake": i in planted,
        })
    items.sort(key=lambda r: r["date"])
    for n, it in enumerate(items, 1):
        it["id"] = f"L{n:03d}"

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"company": COMPANY, "items": items}, indent=1, ensure_ascii=False))
    amb = sum(1 for it in items if None in (it["key"]["ct"], it["key"]["vat"]))
    print(f"{len(items)} lines, {len(planted)} planted mistakes, {amb} ambiguous -> {OUT}")


if __name__ == "__main__":
    main()
