"""Adds balance-sheet style monthly data to 04_Finance-Operations (cash, payables, capex) and the P&L line list.

Derived from the files written by generate_finance_ops.py, so run that first. Deterministic (seeded).
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(4042)
DATA = Path(__file__).resolve().parents[1] / "04_Finance-Operations" / "data"

gl = pd.read_csv(DATA / "gl_actuals.csv", parse_dates=["Month"])
coa = pd.read_csv(DATA / "chart_of_accounts.csv")
ar = pd.read_csv(DATA / "ar_invoices.csv", parse_dates=["InvoiceDate", "PaidDate"])
inv = pd.read_csv(DATA / "inventory_snapshots.csv", parse_dates=["Month"])

g = gl.merge(coa, on="AccountCode")
by = g.pivot_table(index="Month", columns="PnLSection", values="Amount", aggfunc="sum")
acc = g.pivot_table(index="Month", columns="AccountCode", values="Amount", aggfunc="sum")
months = by.index

ebitda = by["Revenue"] - by["COGS"] - by["OpEx"]
net_income = ebitda - by["Below EBITDA"]
depreciation = acc[7000]

# Month-end balances that drive working capital
eom = months + pd.offsets.MonthEnd(0)
ar_bal = pd.Series([ar[(ar.InvoiceDate <= d) & (ar.PaidDate.isna() | (ar.PaidDate > d))].Amount.sum() for d in eom], index=months)
inv_bal = inv.groupby("Month").InventoryValue.sum().reindex(months)
payable_base = acc[5000] + acc[5200] + acc[[6100, 6200, 6300, 6400, 6500]].sum(axis=1)
ap_bal = payable_base * rng.normal(1.22, 0.05, len(months)) * np.linspace(1.0, 0.9, len(months))  # paying suppliers faster over time

capex = pd.Series(rng.normal(70_000, 18_000, len(months)).clip(25_000), index=months)
capex.loc[["2024-09-01", "2025-06-01", "2026-03-01"]] += [210_000, 260_000, 340_000]  # warehouse automation tranches

# The receivables ledger starts empty in January 2024, so the first months of working-capital build are smoothed out
d_nwc = (ar_bal + inv_bal - ap_bal).diff().fillna(0)
d_nwc.iloc[:6] = d_nwc.iloc[6:18].mean()
ocf = net_income + depreciation - d_nwc
fcf = ocf - capex
debt_service = 45_000
cash = 5_400_000 + (fcf - debt_service).cumsum()

out = pd.DataFrame({
    "Month": months.date, "CashBalance": cash.round(2).values, "AccountsPayable": ap_bal.round(2).values,
    "OperatingCashFlow": ocf.round(2).values, "Capex": capex.round(2).values, "DebtService": debt_service,
})
out.to_csv(DATA / "cash_monthly.csv", index=False)

lines = pd.DataFrame(
    [
        (1, "Revenue", "total", 0), (2, "Product revenue", "detail", 4000), (3, "Service revenue", "detail", 4100),
        (4, "Subscription revenue", "detail", 4200),
        (5, "Cost of goods sold", "total", 0), (6, "Gross profit", "subtotal", 0), (7, "Gross margin %", "ratio", 0),
        (8, "Operating expenses", "total", 0), (9, "Salaries & benefits", "detail", 6000), (10, "Marketing", "detail", 6100),
        (11, "Software & IT", "detail", 6200), (12, "Rent & facilities", "detail", 6300), (13, "Travel", "detail", 6400),
        (14, "Professional fees", "detail", 6500),
        (15, "EBITDA", "subtotal", 0), (16, "EBITDA margin %", "ratio", 0),
        (17, "Depreciation", "detail", 7000), (18, "Interest expense", "detail", 7100), (19, "Income tax", "detail", 7200),
        (20, "Net income", "subtotal", 0), (21, "Net margin %", "ratio", 0),
    ],
    columns=["LineOrder", "Line", "LineType", "AccountCode"],
)
# Columns for the clickable charts: the bridge steps in order, short axis labels, and the OpEx account group
lines["LineName"] = lines.Line
bridge = {1: "Revenue", 5: "COGS", 6: "Gross profit", 8: "OpEx", 15: "EBITDA", 17: "D&A", 18: "Interest", 19: "Tax", 20: "Net income"}
lines["BridgeOrder"] = lines.LineOrder.map({o: i + 1 for i, o in enumerate(bridge)}).fillna(0).astype(int)
lines["BridgeLabel"] = lines.LineOrder.map(bridge).fillna("")
lines["LineGroup"] = lines.AccountCode.between(6000, 6999).map({True: "OpEx", False: ""})
lines.loc[lines.LineType == "detail", "Line"] = "    " + lines.Line  # indent account rows under their section
lines.to_csv(DATA / "pnl_lines.csv", index=False, encoding="utf-8")

y = months.year == 2026
print(f"2026 YTD revenue {by['Revenue'][y].sum():,.0f}; EBITDA {ebitda[y].sum():,.0f}; net income {net_income[y].sum():,.0f}")
print(f"invoiced 2026 {ar[ar.InvoiceDate.dt.year == 2026].Amount.sum():,.0f}")
print(f"AR {ar_bal.iloc[-1]:,.0f}; inventory {inv_bal.iloc[-1]:,.0f}; AP {ap_bal.iloc[-1]:,.0f}")
print("cash:", [round(v / 1e6, 2) for v in cash.values])
print("fcf :", [round(v / 1e3) for v in fcf.values])
t3 = slice(-3, None)
print(f"DSO {ar_bal.iloc[-1] / by['Revenue'].iloc[t3].sum() * 92:.0f}; DIO {inv_bal.iloc[-1] / by['COGS'].iloc[t3].sum() * 92:.0f}; "
      f"DPO {ap_bal.iloc[-1] / by['COGS'].iloc[t3].sum() * 92:.0f}")
