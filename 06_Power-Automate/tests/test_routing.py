"""Routing check for flow 01. Run: python tests/test_routing.py

route() is a Python mirror of the Route_destination_folder expression, so this
catches rule-order and case-policy mistakes before deployment. It also asserts
the flow JSON still contains every destination the mirror returns.
"""
import json
from pathlib import Path

FLOWS = Path(__file__).resolve().parent.parent / "flows"
ROOT = "/Shared Documents/Landing/"


def route(name: str) -> str:
    low = name.lower()
    if "quote log customer contracts" in low or "customer contract log" in low:
        return ROOT + "Contracts"
    if "quote log" in low:
        return ROOT + "Quotes"
    if low.startswith("design registration"):
        return ROOT + "Design Registrations"
    if "price list" in low:
        return ROOT + "Price List"
    if "Distributor Backlog" in name or "Distributor Month-End Inventory" in name:  # case-exact
        return ROOT + "Inventory"
    if "ytd sales detail" in low:
        return "SKIP"
    return ROOT + "_Inbox Unrouted"


CASES = {
    "Quote Log 2026.xlsx": "Quotes",
    "Quote Log 2022 Rev1.xlsx": "Quotes",
    "quote log 2026.xlsx": "Quotes",
    "Quote Log Customer Contracts 2024.xlsx": "Contracts",  # ordering trap
    "Customer Contract Log 2026.xlsx": "Contracts",
    "Design Registrations Log(Sheet1).csv": "Design Registrations",
    "design registration log v2.xlsx": "Design Registrations",
    "2026 Price List.xlsx": "Price List",
    "CONFIDENTIAL PRICE LIST 2024.xlsx": "Price List",
    "Distributor Backlog_260824.xlsx": "Inventory",
    "Distributor Month-End Inventory_thru 2607.xlsm": "Inventory",
    "distributor backlog_260824.xlsx": "_Inbox Unrouted",  # wrong case is quarantined
    "2026 YTD Sales Detail_thru 2607 (2).xlsx": "SKIP",
    "2026 ytd sales detail.xlsx": "SKIP",
    "Random Report.xlsx": "_Inbox Unrouted",
    "Quotes Mapping.xlsx": "_Inbox Unrouted",  # curated file must not be overwritten by an upload
}

if __name__ == "__main__":
    for name, want in CASES.items():
        got = route(name)
        assert got == (want if want == "SKIP" else ROOT + want), f"{name}: {got}"

    expr = json.loads((FLOWS / "01_file_intake_router.flow.json").read_text(encoding="utf-8"))[
        "actions"]["Route_destination_folder"]["inputs"]
    for want in set(CASES.values()):
        assert f"'{want if want == 'SKIP' else ROOT + want}'" in expr, f"flow JSON lacks {want}"
    assert expr.count("(") == expr.count(")")

    for f in FLOWS.glob("*.json"):
        json.loads(f.read_text(encoding="utf-8"))
    print(f"{len(CASES)}/{len(CASES)} routing cases pass; flow JSON parses")
