"""Dummy data for 04_Finance-Operations. Deterministic (seeded); re-run to regenerate."""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(404)
OUT = Path(__file__).resolve().parents[1] / "04_Finance-Operations" / "data"
OUT.mkdir(parents=True, exist_ok=True)
START, TODAY = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")
months = pd.date_range(START, TODAY, freq="MS")

# --- Chart of accounts ------------------------------------------------------
coa = pd.DataFrame(
    [
        (4000, "Product Revenue", "Revenue", "Revenue", 1, 1), (4100, "Service Revenue", "Revenue", "Revenue", 1, 1),
        (4200, "Subscription Revenue", "Revenue", "Revenue", 1, 1),
        (5000, "Materials", "Cost of Goods Sold", "COGS", 2, -1), (5100, "Direct Labor", "Cost of Goods Sold", "COGS", 2, -1),
        (5200, "Freight & Logistics", "Cost of Goods Sold", "COGS", 2, -1),
        (6000, "Salaries & Benefits", "Operating Expenses", "OpEx", 3, -1), (6100, "Marketing", "Operating Expenses", "OpEx", 3, -1),
        (6200, "Software & IT", "Operating Expenses", "OpEx", 3, -1), (6300, "Rent & Facilities", "Operating Expenses", "OpEx", 3, -1),
        (6400, "Travel", "Operating Expenses", "OpEx", 3, -1), (6500, "Professional Fees", "Operating Expenses", "OpEx", 3, -1),
        (7000, "Depreciation", "Other", "Below EBITDA", 4, -1), (7100, "Interest Expense", "Other", "Below EBITDA", 4, -1),
        (7200, "Income Tax", "Other", "Below EBITDA", 4, -1),
    ],
    columns=["AccountCode", "Account", "AccountGroup", "PnLSection", "SectionOrder", "Sign"],
)
depts = pd.DataFrame({"DepartmentKey": range(1, 8),
                      "Department": ["Sales", "Marketing", "Operations", "Engineering", "Customer Success", "Finance", "HR & Admin"],
                      "CostCenterOwner": ["P. Navarro", "L. Ashford", "D. Kowalski", "S. Raman", "T. Okonkwo", "M. Lindqvist", "A. Bishop"]})

# --- GL actuals + budget (monthly, account x department) --------------------
t = np.arange(len(months))
rev_curve = 2_050_000 * (1 + 0.012 * t) * (1 + 0.07 * np.sin(2 * np.pi * (months.month - 10) / 12))
rev_mix = {4000: 0.52, 4100: 0.20, 4200: 0.28}
cogs_ratio = {5000: 0.24, 5100: 0.12, 5200: 0.05}
opex_base = {6000: 520_000, 6100: 150_000, 6200: 95_000, 6300: 78_000, 6400: 34_000, 6500: 42_000}
dept_share = {  # how each opex account splits over departments
    6000: [.22, .10, .20, .26, .10, .06, .06], 6100: [.10, .82, 0, 0, .08, 0, 0], 6200: [.10, .10, .12, .50, .08, .06, .04],
    6300: [.14, .10, .34, .20, .08, .07, .07], 6400: [.52, .14, .10, .06, .12, .03, .03], 6500: [.05, .08, .07, .10, 0, .50, .20],
}
gl, bud = [], []
for i, m in enumerate(months):
    rev = rev_curve[i]
    for acc, share in rev_mix.items():
        b = rev * share
        a = b * rng.normal(1.0, 0.035) * (0.93 if (acc == 4000 and m.year == 2026 and m.month in (4, 5, 6)) else 1.0)
        gl.append((m.date(), acc, 1, round(a, 2)))
        bud.append((m.date(), acc, 1, round(b, -2)))
    for acc, ratio in cogs_ratio.items():
        drift = 1 + (0.18 * max(0, i - 24) / 9 if acc == 5200 else 0)  # freight creeping up in 2026
        gl.append((m.date(), acc, 3, round(rev * ratio * drift * rng.normal(1, 0.04), 2)))
        bud.append((m.date(), acc, 3, round(rev * ratio, -2)))
    for acc, base in opex_base.items():
        grow = base * (1 + 0.008 * i)
        for dk, sh in zip(depts.DepartmentKey, dept_share[acc]):
            if sh == 0:
                continue
            over = 1.14 if (acc == 6100 and m.year == 2026) else 1.09 if (acc == 6400 and dk == 1) else 1.0
            gl.append((m.date(), acc, dk, round(grow * sh * over * rng.normal(1, 0.05), 2)))
            bud.append((m.date(), acc, dk, round(grow * sh, -2)))
    for acc, amt in {7000: 61_000, 7100: 18_500, 7200: rev * 0.028}.items():
        gl.append((m.date(), acc, 6, round(amt * rng.normal(1, 0.02), 2)))
        bud.append((m.date(), acc, 6, round(amt, -2)))
gl = pd.DataFrame(gl, columns=["Month", "AccountCode", "DepartmentKey", "Amount"])
bud = pd.DataFrame(bud, columns=["Month", "AccountCode", "DepartmentKey", "BudgetAmount"])

# --- Accounts receivable invoices -------------------------------------------
cust = [f"{a} {b}" for a in ["Atlas", "Borealis", "Cascade", "Dynamo", "Echo", "Forge", "Gable", "Horizon", "Iris", "Jetty",
                              "Kestrel", "Linden"] for b in ["Supply", "Retail", "Foods", "Medical", "Motors"]]
cust_terms = {c: int(rng.choice([15, 30, 30, 45, 60])) for c in cust}
cust_slow = {c: float(rng.gamma(1.4, 7)) for c in cust}
ar = []
for inv in range(1, 3601):
    c = rng.choice(cust)
    d = START + pd.Timedelta(days=int(rng.integers(0, (TODAY - START).days)))
    due = d + pd.Timedelta(days=cust_terms[c])
    amt = round(float(rng.lognormal(9.6, 0.8)), 2)
    paid = due + pd.Timedelta(days=int(rng.normal(cust_slow[c], 9)))
    if paid > TODAY or rng.random() < 0.015:
        paid = pd.NaT
    ar.append((f"INV-{20000 + inv}", c, d.date(), due.date(), cust_terms[c], amt, paid.date() if paid is not pd.NaT else None,
               "Paid" if paid is not pd.NaT else "Open"))
ar = pd.DataFrame(ar, columns=["InvoiceNumber", "Customer", "InvoiceDate", "DueDate", "TermsDays", "Amount", "PaidDate", "Status"])

# --- Operations: warehouses, shipments, inventory ---------------------------
wh = pd.DataFrame({"WarehouseKey": [1, 2, 3, 4], "Warehouse": ["Dallas DC", "Chicago DC", "Atlanta DC", "Reno DC"],
                   "Region": ["South", "Midwest", "Southeast", "West"], "CapacityPallets": [5200, 4400, 3800, 3000]})
carriers = {"SwiftLine": (0.95, 4.1), "BlueArrow": (0.91, 3.6), "Continental Freight": (0.88, 3.2), "RapidHaul": (0.82, 2.9)}
n = 26000
sd = START + pd.to_timedelta(np.sort(rng.integers(0, (TODAY - START).days + 1, n)), unit="D")
car = rng.choice(list(carriers), n, p=[.34, .28, .22, .16])
whk = rng.choice(wh.WarehouseKey, n, p=[.34, .28, .22, .16])
promised = rng.choice([2, 3, 5], n, p=[.3, .45, .25])
ot_p = np.array([carriers[c][0] for c in car]) - np.where((whk == 4) & (sd >= "2026-03-01"), 0.12, 0)  # Reno slipping
late = rng.random(n) > ot_p
actual = promised + np.where(late, rng.integers(1, 6, n), -rng.integers(0, 2, n))
weight = np.round(rng.lognormal(5.2, 0.8, n), 1)
cost = np.round(weight * np.array([carriers[c][1] for c in car]) * 0.06 * rng.normal(1, 0.1, n) + 18, 2)
ship = pd.DataFrame({"ShipmentID": [f"SHP-{500000 + i}" for i in range(n)], "ShipDate": sd.date, "WarehouseKey": whk,
                     "Carrier": car, "PromisedDays": promised, "ActualDays": np.maximum(actual, 1), "WeightKg": weight,
                     "FreightCost": cost, "Units": rng.integers(1, 60, n)})
ship["DeliveredOnTime"] = (ship.ActualDays <= ship.PromisedDays).astype(int)

cats = ["Electronics", "Home Goods", "Apparel", "Industrial Parts", "Consumables"]
inv = []
for w in wh.WarehouseKey:
    for c in cats:
        level, base = rng.uniform(300, 900), rng.uniform(400, 800)
        for m in months:
            demand = base * (1 + 0.25 * np.sin(2 * np.pi * (m.month - 9) / 12)) * rng.normal(1, 0.12)
            level = max(40, level + rng.normal(base, 90) - demand)
            unit_cost = {"Electronics": 310, "Home Goods": 85, "Apparel": 40, "Industrial Parts": 190, "Consumables": 22}[c]
            inv.append((m.date(), w, c, int(level), int(demand), round(level * unit_cost, 2), int(base * 0.6)))
inv = pd.DataFrame(inv, columns=["Month", "WarehouseKey", "ProductCategory", "PalletsOnHand", "PalletsShipped",
                                 "InventoryValue", "ReorderPoint"])

coa.to_csv(OUT / "chart_of_accounts.csv", index=False)
depts.to_csv(OUT / "departments.csv", index=False)
gl.to_csv(OUT / "gl_actuals.csv", index=False)
bud.to_csv(OUT / "budget.csv", index=False)
ar.to_csv(OUT / "ar_invoices.csv", index=False)
wh.to_csv(OUT / "warehouses.csv", index=False)
ship.to_csv(OUT / "shipments.csv", index=False)
inv.to_csv(OUT / "inventory_snapshots.csv", index=False)

g = gl.merge(coa, on="AccountCode")
rev, cogs, opex = (g[g.PnLSection == s].Amount.sum() for s in ("Revenue", "COGS", "OpEx"))
print(f"revenue {rev:,.0f}; gross margin {(rev - cogs) / rev:.1%}; EBITDA margin {(rev - cogs - opex) / rev:.1%}; "
      f"AR open {ar[ar.Status == 'Open'].Amount.sum():,.0f}; shipments {len(ship):,}; on-time {ship.DeliveredOnTime.mean():.1%}")
