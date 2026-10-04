"""Dummy data for 03_Real-Estate. Deterministic (seeded); re-run to regenerate."""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(303)
OUT = Path(__file__).resolve().parents[1] / "03_Real-Estate" / "data"
OUT.mkdir(parents=True, exist_ok=True)
START, TODAY = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")
months = pd.date_range(START, TODAY, freq="MS")

# --- Properties -------------------------------------------------------------
cities = {"Austin": ("TX", 1.00), "Denver": ("CO", 1.08), "Nashville": ("TN", 0.95), "Phoenix": ("AZ", 0.90),
          "Raleigh": ("NC", 0.93), "Seattle": ("WA", 1.35)}
ptypes = {"Multifamily": (24, 120, 1.9), "Office": (6, 30, 2.6), "Retail": (4, 18, 2.3), "Industrial": (2, 10, 1.1)}
words = ["Cedar", "Harbor", "Maple", "Summit", "Park", "River", "Stone", "Union", "Lakeview", "Grand", "Mill",
         "Foundry", "Orchard", "Canal", "Highline", "Arbor", "Beacon", "Crescent"]
tails = {"Multifamily": ["Residences", "Lofts", "Flats", "Commons"], "Office": ["Tower", "Plaza", "Exchange"],
         "Retail": ["Marketplace", "Shops", "Square"], "Industrial": ["Logistics Center", "Distribution Park"]}
managers = ["Elise Morgan", "Victor Chen", "Renee Abbott", "Samir Dalal", "Joanna Pike"]
props, used = [], set()
for pk in range(1, 37):
    t = rng.choice(list(ptypes), p=[0.45, 0.22, 0.20, 0.13])
    city = rng.choice(list(cities))
    while True:
        nm = f"{rng.choice(words)} {rng.choice(tails[t])}"
        if nm not in used:
            used.add(nm)
            break
    lo, hi, psf = ptypes[t]
    props.append({"PropertyKey": pk, "Property": nm, "PropertyType": t, "City": city, "State": cities[city][0],
                  "Units": int(rng.integers(lo, hi)), "YearBuilt": int(rng.integers(1985, 2023)),
                  "AcquiredDate": (pd.Timestamp("2016-01-01") + pd.Timedelta(days=int(rng.integers(0, 3200)))).date(),
                  "PropertyManager": rng.choice(managers), "Psf": psf * cities[city][1],
                  "Quality": float(np.clip(rng.normal(1, 0.12), 0.7, 1.3))})
props = pd.DataFrame(props)

# --- Units ------------------------------------------------------------------
units = []
uk = 1
for _, p in props.iterrows():
    for n in range(1, p.Units + 1):
        if p.PropertyType == "Multifamily":
            beds = int(rng.choice([0, 1, 2, 3], p=[0.12, 0.42, 0.36, 0.10]))
            sqft, utype = int(rng.normal(480 + 290 * beds, 60)), ["Studio", "1 Bed", "2 Bed", "3 Bed"][beds]
        else:
            sqft = int(rng.lognormal({"Office": 8.1, "Retail": 7.8, "Industrial": 9.9}[p.PropertyType], 0.45))
            utype = "Suite" if p.PropertyType != "Industrial" else "Bay"
        mult = 1.0 if p.PropertyType == "Multifamily" else 1 / 12  # commercial psf quoted annually
        rent = round(sqft * p.Psf * p.Quality * mult * rng.normal(1, 0.05), -1)
        units.append({"UnitKey": uk, "PropertyKey": int(p.PropertyKey), "UnitNumber": f"{p.PropertyKey:02d}-{n:03d}",
                      "UnitType": utype, "SquareFeet": sqft, "MarketRent": rent})
        uk += 1
units = pd.DataFrame(units)

# valuation: annual market rent / cap rate, with purchase price below that
cap = {"Multifamily": 0.052, "Office": 0.074, "Retail": 0.066, "Industrial": 0.058}
annual = units.groupby("PropertyKey").MarketRent.sum() * 12
props["CurrentValue"] = (props.PropertyKey.map(annual) * 0.62 / props.PropertyType.map(cap)).round(-4)
props["PurchasePrice"] = (props.CurrentValue / rng.uniform(1.05, 1.7, len(props))).round(-4)

# --- Leases -----------------------------------------------------------------
tenant_first = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie", "Avery", "Quinn", "Drew", "Reese"]
tenant_last = ["Adams", "Brooks", "Cruz", "Diaz", "Evans", "Foster", "Gray", "Hayes", "Irwin", "Jensen", "Klein", "Lopez"]
biz = ["Dental", "Fitness", "Coffee", "Law Group", "Design Studio", "Logistics", "Pharmacy", "Consulting", "Bakery", "Tech"]
leases, lk = [], 1
weak = set(props.sort_values("Quality").PropertyKey.head(6))  # properties with an occupancy problem
for _, u in units.iterrows():
    p = props.loc[u.PropertyKey - 1]
    resid = p.PropertyType == "Multifamily"
    cur = START - pd.Timedelta(days=int(rng.integers(0, 330)))
    rent = u.MarketRent * rng.uniform(0.86, 0.96)
    while cur < TODAY:
        term = int(rng.choice([6, 12, 12, 12, 18])) if resid else int(rng.choice([36, 60, 84]))
        end = cur + pd.DateOffset(months=term) - pd.Timedelta(days=1)
        tenant = (f"{rng.choice(tenant_first)} {rng.choice(tenant_last)}" if resid
                  else f"{rng.choice(words)} {rng.choice(biz)}")
        leases.append({"LeaseKey": lk, "UnitKey": int(u.UnitKey), "PropertyKey": int(u.PropertyKey), "Tenant": tenant,
                       "StartDate": cur.date(), "EndDate": end.date(), "MonthlyRent": round(rent, -1),
                       "SecurityDeposit": round(rent, -1), "Reliability": float(rng.beta(9, 1.2))})
        lk += 1
        renew = rng.random() < (0.50 if resid else 0.7)
        gap = 0 if renew else int(rng.gamma(2.0, 75 if u.PropertyKey in weak else 22))
        cur = end + pd.Timedelta(days=1 + gap)
        rent = rent * rng.uniform(1.02, 1.07)
leases = pd.DataFrame(leases)
leases["Status"] = np.where(pd.to_datetime(leases.EndDate) < TODAY, "Expired", "Active")

# --- Rent payments (one row per lease per month due) ------------------------
pay = []
for _, l in leases.iterrows():
    s, e = pd.Timestamp(l.StartDate), min(pd.Timestamp(l.EndDate), TODAY)
    for m in months[(months >= s.replace(day=1)) & (months <= e)]:
        r = rng.random()
        if r < l.Reliability:
            paid, delay = l.MonthlyRent, int(rng.integers(-3, 4))
        elif r < l.Reliability + 0.07:
            paid, delay = l.MonthlyRent, int(rng.integers(6, 40))
        elif r < l.Reliability + 0.10:
            paid, delay = round(l.MonthlyRent * rng.uniform(0.3, 0.8), -1), int(rng.integers(5, 30))
        else:
            paid, delay = 0.0, None
        pd_date = m + pd.Timedelta(days=delay) if delay is not None else pd.NaT
        if pd_date is not pd.NaT and pd_date > TODAY:
            paid, pd_date = 0.0, pd.NaT
        status = "Unpaid" if paid == 0 else "Partial" if paid < l.MonthlyRent else "Late" if delay > 5 else "On Time"
        pay.append((l.LeaseKey, l.UnitKey, l.PropertyKey, m.date(), l.MonthlyRent, paid,
                    pd_date.date() if pd_date is not pd.NaT else None, status))
pay = pd.DataFrame(pay, columns=["LeaseKey", "UnitKey", "PropertyKey", "DueDate", "AmountDue", "AmountPaid",
                                 "PaidDate", "PaymentStatus"])
pay.insert(0, "PaymentKey", np.arange(1, len(pay) + 1))

# --- Operating expenses (monthly per property) ------------------------------
exp_cats = {"Property Tax": 0.11, "Insurance": 0.04, "Utilities": 0.06, "Repairs & Maintenance": 0.07,
            "Management Fee": 0.04, "Marketing": 0.01, "Payroll": 0.05}
potential = units.groupby("PropertyKey").MarketRent.sum()
exp = []
for pkey, pot in potential.items():
    age_factor = 1 + max(0, 2005 - props.loc[pkey - 1].YearBuilt) * 0.012
    for m in months:
        for cat, share in exp_cats.items():
            bump = age_factor if cat == "Repairs & Maintenance" else 1.0
            winter = 1.25 if cat == "Utilities" and m.month in (12, 1, 2, 7, 8) else 1.0
            exp.append((pkey, m.date(), cat, round(pot * share * bump * winter * rng.normal(1, 0.12), 2)))
exp = pd.DataFrame(exp, columns=["PropertyKey", "Month", "ExpenseCategory", "Amount"])

# --- Maintenance requests ---------------------------------------------------
cats = {"Plumbing": 340, "HVAC": 620, "Electrical": 280, "Appliance": 210, "General": 120, "Roofing": 1900, "Pest": 150}
mnt = []
for _, u in units.iterrows():
    p = props.loc[u.PropertyKey - 1]
    rate = 1.1 * (1 + max(0, 2008 - p.YearBuilt) * 0.03)
    for _ in range(rng.poisson(rate * len(months) / 12)):
        opened = START + pd.Timedelta(days=int(rng.integers(0, (TODAY - START).days)))
        cat = rng.choice(list(cats), p=[.24, .18, .12, .16, .22, .03, .05])
        pri = rng.choice(["Emergency", "High", "Normal", "Low"], p=[.06, .2, .54, .2])
        days = max(0, int(rng.gamma(2, {"Emergency": 0.6, "High": 1.8, "Normal": 4.0, "Low": 8.0}[pri])))
        closed = opened + pd.Timedelta(days=days)
        done = closed <= TODAY
        mnt.append((int(u.UnitKey), int(u.PropertyKey), opened.date(), closed.date() if done else None, cat, pri,
                    "Completed" if done else "Open", round(cats[cat] * rng.lognormal(0, 0.6), 2) if done else None))
mnt = pd.DataFrame(mnt, columns=["UnitKey", "PropertyKey", "OpenedDate", "CompletedDate", "Category", "Priority",
                                 "Status", "Cost"])
mnt.insert(0, "RequestKey", np.arange(1, len(mnt) + 1))

# --- Map position (equirectangular, 0-100 on both axes; matches the dotted map drawn in the page background)
LON0, LON1, LAT0, LAT1 = -125.0, -66.0, 24.0, 50.0
city_xy = {"Austin": (-97.74, 30.27), "Denver": (-104.99, 39.74), "Nashville": (-86.78, 36.16),
           "Phoenix": (-112.07, 33.45), "Raleigh": (-78.64, 35.78), "Seattle": (-122.33, 47.61)}
spread = np.random.default_rng(7)  # scatter properties around each metro so every building gets its own pin
props["Longitude"] = (props.City.map(lambda c: city_xy[c][0]) + spread.normal(0, 0.11, len(props))).round(4)
props["Latitude"] = (props.City.map(lambda c: city_xy[c][1]) + spread.normal(0, 0.08, len(props))).round(4)
props["MapX"] = ((props.Longitude - LON0) / (LON1 - LON0) * 100).round(2)
props["MapY"] = ((props.Latitude - LAT0) / (LAT1 - LAT0) * 100).round(2)

# --- Property photos: free Unsplash photos (unsplash.com licence), referenced by URL, cycled within each property type
PHOTOS = {
    "Multifamily": ["1515263487990-61b07816b324", "1545324418-cc1a3fa10c00", "1624204386084-dd8c05e32226", "1579632652768-6cb9dcf85912",
                    "1516501312919-d0cb0b7b60b8", "1619994121345-b61cd610c5a6", "1638973140785-3b918e290682", "1592276040264-e10344a6a10e"],
    "Office": ["1574958269340-fa927503f3dd", "1576731753569-3e93a228048c", "1470075801209-17f9ec0cada6", "1549757521-4160565ff3de",
               "1621831337128-35676ca30868", "1597220141661-df3e77364fee", "1593054538306-3e61b738a10c"],
    "Retail": ["1684014450587-3c7f09c53e74", "1734004723482-b601578026b9", "1774876203004-461433250ada", "1677592737831-cafae8417bdd"],
    "Industrial": ["1758789667762-56175fe4601c", "1717662292789-e97dfb7d3c88", "1656120199083-eff40d26bd0c", "1780367261654-45395777b560",
                   "1677257872254-e3a4fb6e62c8", "1768095522064-fc8a162e5da6"],
}
seq = props.groupby("PropertyType").cumcount()
ids = [PHOTOS[t][i % len(PHOTOS[t])] for t, i in zip(props.PropertyType, seq)]
props["Photo"] = [f"https://images.unsplash.com/photo-{i}?w=160&h=110&fit=crop&q=70" for i in ids]
props["PhotoLarge"] = [f"https://images.unsplash.com/photo-{i}?w=1040&h=760&fit=crop&q=75" for i in ids]

# --- Property type pictures: small flat SVG illustrations stored as data URIs
def svg(body):
    s = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 90'><rect width='120' height='90' rx='12' fill='#EFE7D8'/>{body}</svg>"
    return "data:image/svg+xml;utf8," + s.replace("#", "%23")

G, G2, SAND, INK = "#2F6B4F", "#4E9A76", "#FFFDF8", "#1F2A24"
win = lambda x, y, w=7, h=8, f=SAND: f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='1.5' fill='{f}'/>"
ground = f"<rect x='10' y='76' width='100' height='3' rx='1.5' fill='{INK}' opacity='0.25'/>"
pictures = {
    "Multifamily": f"<rect x='24' y='26' width='40' height='50' rx='3' fill='{G}'/><rect x='64' y='38' width='32' height='38' rx='3' fill='{G2}'/>"
                   + "".join(win(30 + c * 11, 32 + r * 11) for r in range(3) for c in range(3))
                   + "".join(win(70 + c * 11, 44 + r * 11) for r in range(2) for c in range(2))
                   + f"<rect x='39' y='65' width='10' height='11' rx='1.5' fill='{INK}'/>" + ground,
    "Office": f"<rect x='40' y='12' width='40' height='64' rx='3' fill='{G}'/><rect x='56' y='6' width='8' height='8' rx='2' fill='{G2}'/>"
              + "".join(win(46 + c * 10, 19 + r * 9, 6, 5) for r in range(6) for c in range(3)) + ground,
    "Retail": f"<rect x='20' y='40' width='80' height='36' rx='3' fill='{G}'/><path d='M16 40 L24 26 H96 L104 40 Z' fill='{G2}'/>"
              + f"<rect x='28' y='48' width='28' height='18' rx='2' fill='{SAND}'/><rect x='64' y='48' width='14' height='28' rx='2' fill='{INK}'/>"
              + f"<rect x='84' y='48' width='10' height='10' rx='2' fill='{SAND}'/>" + ground,
    "Industrial": f"<path d='M14 76 V44 L38 32 V44 L62 32 V44 L86 32 V76 Z' fill='{G}'/><rect x='86' y='22' width='10' height='54' rx='2' fill='{G2}'/>"
                  + f"<rect x='24' y='56' width='18' height='20' rx='2' fill='{INK}'/>" + win(50, 54, 10, 8) + win(66, 54, 10, 8) + ground,
}
pd.DataFrame({"PropertyType": list(pictures), "Picture": [svg(b) for b in pictures.values()],
              "TypeOrder": [1, 2, 3, 4]}).to_csv(OUT / "property_types.csv", index=False)

props.drop(columns=["Psf", "Quality"]).to_csv(OUT / "properties.csv", index=False)
units.to_csv(OUT / "units.csv", index=False)
leases.drop(columns="Reliability").to_csv(OUT / "leases.csv", index=False)
pay.to_csv(OUT / "rent_payments.csv", index=False)
exp.to_csv(OUT / "operating_expenses.csv", index=False)
mnt.to_csv(OUT / "maintenance_requests.csv", index=False)

active = leases[(pd.to_datetime(leases.StartDate) <= TODAY) & (pd.to_datetime(leases.EndDate) >= TODAY)]
print(f"properties {len(props)}; units {len(units):,}; leases {len(leases):,}; occupancy {active.UnitKey.nunique() / len(units):.1%}; "
      f"payments {len(pay):,}; collected {pay.AmountPaid.sum() / pay.AmountDue.sum():.1%}; maintenance {len(mnt):,}; "
      f"portfolio value {props.CurrentValue.sum():,.0f}")
