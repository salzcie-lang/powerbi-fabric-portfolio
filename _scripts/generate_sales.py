"""Dummy data for 01_Sales-Analytics. Deterministic (seeded); re-run to regenerate."""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(101)
OUT = Path(__file__).resolve().parents[1] / "01_Sales-Analytics" / "data"
OUT.mkdir(parents=True, exist_ok=True)
START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")

# --- Regions and reps -------------------------------------------------------
regions = pd.DataFrame(
    {
        "RegionKey": [1, 2, 3, 4, 5],
        "Region": ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"],
        "RegionManager": ["Dana Whitfield", "Lukas Brandt", "Mei Tanaka", "Camila Ortiz", "Omar Haddad"],
        "Weight": [0.36, 0.27, 0.20, 0.10, 0.07],
    }
)
countries = {
    1: ["United States", "Canada"],
    2: ["United Kingdom", "Germany", "France", "Netherlands", "Spain"],
    3: ["Australia", "Japan", "Singapore", "India"],
    4: ["Brazil", "Mexico", "Chile"],
    5: ["United Arab Emirates", "Saudi Arabia", "South Africa"],
}
first = ["Ava", "Noah", "Liam", "Emma", "Mia", "Ethan", "Sofia", "Lucas", "Aria", "Mason", "Zoe", "Leo",
         "Nora", "Owen", "Isla", "Ravi", "Yuki", "Elena", "Tariq", "Chloe", "Diego", "Hana", "Felix", "Priya"]
last = ["Carter", "Nguyen", "Schmidt", "Rossi", "Patel", "Kim", "Silva", "Dubois", "Novak", "Hughes", "Khan",
        "Moreno", "Larsen", "Okafor", "Sato", "Fischer", "Reyes", "Walsh", "Ivanov", "Costa", "Mehta", "Berg"]

reps = []
rep_key = 1
for rk, n in zip(regions.RegionKey, [7, 6, 5, 3, 3]):
    for _ in range(n):
        reps.append(
            {
                "RepKey": rep_key,
                "SalesRep": f"{rng.choice(first)} {rng.choice(last)}",
                "RegionKey": rk,
                "HireDate": (pd.Timestamp("2019-01-01") + pd.Timedelta(days=int(rng.integers(0, 2200)))).date(),
                "Skill": rng.normal(1.0, 0.22),
            }
        )
        rep_key += 1
reps = pd.DataFrame(reps)
reps["Skill"] = reps.Skill.clip(0.55, 1.6)

# --- Products ---------------------------------------------------------------
catalog = {
    "Laptops": (["Ultrabook", "Workstation", "Business"], 780, 2400, 0.22),
    "Monitors": (["4K", "Ultrawide", "Standard"], 160, 900, 0.28),
    "Accessories": (["Keyboards", "Mice", "Docking", "Headsets"], 25, 260, 0.46),
    "Networking": (["Routers", "Switches", "Access Points"], 90, 1400, 0.34),
    "Software": (["Security", "Productivity", "Analytics"], 60, 1200, 0.72),
    "Services": (["Installation", "Support Plan", "Training"], 150, 3000, 0.58),
}
brands = ["Northwind", "Vertex", "Lumina", "Corelink", "Apex"]
products = []
pk = 1
for cat, (subs, lo, hi, margin) in catalog.items():
    for sub in subs:
        for i in range(int(rng.integers(3, 6))):
            price = round(float(rng.uniform(lo, hi)), -1) - 1
            m = float(np.clip(rng.normal(margin, 0.05), 0.08, 0.85))
            products.append(
                {
                    "ProductKey": pk,
                    "SKU": f"{cat[:3].upper()}-{pk:04d}",
                    "Product": f"{rng.choice(brands)} {sub} {100 + i * 10 + int(rng.integers(0, 9))}",
                    "Category": cat,
                    "Subcategory": sub,
                    "ListPrice": price,
                    "UnitCost": round(price * (1 - m), 2),
                    "Popularity": float(rng.pareto(2.2) + 0.3),
                }
            )
            pk += 1
products = pd.DataFrame(products)

# --- Customers --------------------------------------------------------------
segments = ["Enterprise", "Mid-Market", "Small Business"]
industries = ["Technology", "Healthcare", "Retail", "Manufacturing", "Financial Services", "Education", "Logistics"]
stems = ["Alder", "Brightline", "Cobalt", "Dune", "Everest", "Fathom", "Granite", "Harbor", "Ion", "Juniper",
         "Keystone", "Lattice", "Meridian", "Nimbus", "Orchard", "Pinnacle", "Quartz", "Ridge", "Summit", "Tidal",
         "Umbra", "Vantage", "Willow", "Xenon", "Yonder", "Zephyr"]
suffix = ["Group", "Labs", "Systems", "Partners", "Holdings", "Industries", "Solutions", "Works", "Global", "Co"]
customers = []
names = set()
for ck in range(1, 421):
    rk = int(rng.choice(regions.RegionKey, p=regions.Weight))
    while True:
        name = f"{rng.choice(stems)} {rng.choice(suffix)}"
        if name not in names:
            names.add(name)
            break
        name = f"{name} {rng.choice(['International', 'Digital', 'Retail', 'Health', 'Energy'])}"
        if name not in names:
            names.add(name)
            break
    seg = rng.choice(segments, p=[0.18, 0.37, 0.45])
    customers.append(
        {
            "CustomerKey": ck,
            "Customer": name,
            "Segment": seg,
            "Industry": rng.choice(industries),
            "Country": rng.choice(countries[rk]),
            "RegionKey": rk,
            "FirstOrderDate": (START + pd.Timedelta(days=int(rng.beta(1.1, 2.6) * 900))).date(),
            "Size": {"Enterprise": 5.0, "Mid-Market": 2.0, "Small Business": 0.8}[seg] * float(rng.lognormal(0, 0.5)),
        }
    )
customers = pd.DataFrame(customers)

# --- Orders (line level) ----------------------------------------------------
days = pd.date_range(START, END, freq="D")
t = np.arange(len(days))
season = 1 + 0.16 * np.sin(2 * np.pi * (days.dayofyear - 255) / 365) + np.where(days.month.isin([11, 12]), 0.22, 0)
growth = 1 + 0.42 * t / len(days)
weekday = np.where(days.dayofweek < 5, 1.0, 0.28)
dip = np.where((days >= "2025-06-01") & (days <= "2025-08-15"), 0.84, 1.0)  # a soft patch to explain
lam = 21 * season * growth * weekday * dip
orders_per_day = rng.poisson(lam)

channels, ch_p = ["Direct", "Partner", "Online"], [0.45, 0.25, 0.30]
rows = []
order_id = 100000
cust_first = pd.to_datetime(customers.FirstOrderDate).values
sub_slope = {"Standard": -0.72, "Mice": -0.68, "Routers": -0.62, "Productivity": -0.55, "Docking": -0.7, "Training": -0.5,
             "Security": 0.9, "Analytics": 0.8, "Ultrawide": 0.6}
prod_slope = products.Subcategory.map(sub_slope).fillna(0).values
cust_slope = np.clip(rng.normal(0.05, 0.75, len(customers)), -0.95, 1.6)
for d, n, tf in zip(days, orders_per_day, t / len(days)):
    prod_w = products.Popularity.values * (1 + prod_slope * tf)
    eligible = customers[cust_first <= np.datetime64(d)]
    if eligible.empty or n == 0:
        continue
    w = eligible.Size.values * np.clip(1 + cust_slope[eligible.CustomerKey.values - 1] * tf, 0.05, None)
    w = w / w.sum()
    for ck in rng.choice(eligible.CustomerKey.values, size=n, p=w):
        c = customers.loc[ck - 1]
        rep_pool = reps[reps.RegionKey == c.RegionKey]
        rep = rep_pool.sample(1, weights=rep_pool.Skill, random_state=int(rng.integers(0, 1e9))).iloc[0]
        order_id += 1
        channel = rng.choice(channels, p=ch_p)
        for _, p in products.sample(int(rng.integers(1, 4)), weights=prod_w,
                                    random_state=int(rng.integers(0, 1e9))).iterrows():
            qty = max(1, int(rng.poisson(1.2 + c.Size * 0.9)))
            disc_cap = {"Enterprise": 0.22, "Mid-Market": 0.14, "Small Business": 0.08}[c.Segment]
            disc = round(float(rng.choice([0, 0, 0.05, 0.10, disc_cap])), 2)
            if c.RegionKey == 4 and p.Category == "Laptops":
                disc = min(0.30, disc + 0.10)  # margin leak to find on the Products page
            rows.append(
                (order_id, d.date(), int(ck), int(p.ProductKey), int(rep.RepKey), channel, qty,
                 p.ListPrice, disc, round(qty * p.ListPrice * (1 - disc), 2), round(qty * p.UnitCost, 2))
            )
orders = pd.DataFrame(
    rows,
    columns=["OrderID", "OrderDate", "CustomerKey", "ProductKey", "RepKey", "Channel", "Quantity",
             "UnitPrice", "DiscountPct", "Revenue", "Cost"],
)

# --- Monthly targets by region ----------------------------------------------
o = orders.assign(Month=pd.to_datetime(orders.OrderDate).dt.to_period("M").dt.to_timestamp()).merge(
    customers[["CustomerKey", "RegionKey"]], on="CustomerKey"
)
actual = o.groupby(["Month", "RegionKey"], as_index=False).Revenue.sum()
smooth = actual.groupby("RegionKey").Revenue.transform(lambda s: s.rolling(3, min_periods=1, center=True).mean())
bias = actual.RegionKey.map({1: 0.97, 2: 1.03, 3: 0.95, 4: 1.12, 5: 1.01})
targets = actual.assign(TargetRevenue=(smooth * bias * rng.normal(1.0, 0.03, len(actual))).round(-2))[
    ["Month", "RegionKey", "TargetRevenue"]
]
targets["Month"] = targets.Month.dt.date

regions.drop(columns="Weight").to_csv(OUT / "regions.csv", index=False)
reps.drop(columns="Skill").to_csv(OUT / "sales_reps.csv", index=False)
products.drop(columns="Popularity").to_csv(OUT / "products.csv", index=False)
customers.drop(columns="Size").to_csv(OUT / "customers.csv", index=False)
orders.to_csv(OUT / "orders.csv", index=False)
targets.to_csv(OUT / "targets.csv", index=False)

print(f"orders: {len(orders):,} lines, {orders.OrderID.nunique():,} orders, revenue {orders.Revenue.sum():,.0f}")
print(f"margin: {1 - orders.Cost.sum() / orders.Revenue.sum():.1%}; customers {len(customers)}, products {len(products)}")
