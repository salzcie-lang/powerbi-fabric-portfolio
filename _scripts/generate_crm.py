"""Dummy data for 02_CRM-Pipeline. Deterministic (seeded); re-run to regenerate."""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(202)
OUT = Path(__file__).resolve().parents[1] / "02_CRM-Pipeline" / "data"
OUT.mkdir(parents=True, exist_ok=True)
START, TODAY = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")

# --- Reps -------------------------------------------------------------------
teams = {"Enterprise": 4, "Mid-Market": 5, "SMB": 5}
names = ["Harper Quinn", "Jonas Weber", "Amara Okoye", "Theo Laurent", "Sana Iqbal", "Marcus Bell", "Ingrid Solberg",
         "Rafael Souza", "Naomi Clarke", "Kenji Mori", "Layla Farouk", "Piotr Zielinski", "Grace Liu", "Dylan Ross"]
reps, i = [], 0
for team, n in teams.items():
    for _ in range(n):
        reps.append({"RepKey": i + 1, "Rep": names[i], "Team": team, "Skill": float(np.clip(rng.normal(1, 0.25), 0.5, 1.6)),
                     "QuarterlyQuota": {"Enterprise": 230000, "Mid-Market": 150000, "SMB": 60000}[team]})
        i += 1
reps = pd.DataFrame(reps)

# --- Accounts ---------------------------------------------------------------
industries = ["SaaS", "Healthcare", "Retail", "Manufacturing", "Fintech", "Education", "Logistics", "Media"]
stems = ["Acorn", "Beacon", "Cinder", "Delta", "Ember", "Flint", "Glacier", "Helix", "Indigo", "Jasper", "Kite",
         "Lumen", "Mosaic", "Nova", "Onyx", "Prism", "Quill", "Rune", "Sable", "Terra", "Unity", "Vela", "Wren"]
tails = ["Analytics", "Health", "Commerce", "Dynamics", "Capital", "Learning", "Freight", "Media", "Cloud", "Labs"]
accounts, seen = [], set()
for ak in range(1, 601):
    while True:
        nm = f"{rng.choice(stems)} {rng.choice(tails)}"
        if nm in seen:
            nm = f"{nm} {int(rng.integers(2, 99))}"
        if nm not in seen:
            seen.add(nm)
            break
    seg = rng.choice(["Enterprise", "Mid-Market", "SMB"], p=[0.15, 0.35, 0.50])
    accounts.append({"AccountKey": ak, "Account": nm, "Segment": seg, "Industry": rng.choice(industries),
                     "Country": rng.choice(["United States", "United Kingdom", "Germany", "Canada", "Australia",
                                            "Netherlands", "UAE", "Singapore"], p=[.42, .14, .1, .1, .08, .06, .05, .05]),
                     "Employees": int({"Enterprise": 4000, "Mid-Market": 600, "SMB": 60}[seg] * rng.lognormal(0, 0.6))})
accounts = pd.DataFrame(accounts)

# --- Leads ------------------------------------------------------------------
sources = {"Organic Search": (0.24, 0.30), "Paid Search": (0.20, 0.17), "Referral": (0.12, 0.44),
           "Events": (0.10, 0.26), "Outbound": (0.20, 0.12), "Partner": (0.08, 0.35), "Social": (0.06, 0.09)}
n_leads = 8200
src = rng.choice(list(sources), size=n_leads, p=[v[0] for v in sources.values()])
span = (TODAY - START).days
created = START + pd.to_timedelta((rng.beta(1.3, 1.0, n_leads) * span).astype(int), unit="D")
acct = rng.integers(1, 601, n_leads)
qual_p = np.array([sources[s][1] for s in src])
qualified = rng.random(n_leads) < qual_p
leads = pd.DataFrame({"LeadKey": np.arange(1, n_leads + 1), "CreatedDate": created.date, "LeadSource": src,
                      "AccountKey": acct})
resp = np.round(rng.lognormal(1.2, 1.0, n_leads), 1)
leads["FirstResponseHours"] = np.where(src == "Outbound", np.nan, resp)
age = (TODAY - created).days
leads["Status"] = np.where(qualified & (age > 5), "Qualified",
                           np.where(age < 14, "New", rng.choice(["Disqualified", "Nurturing"], n_leads, p=[0.6, 0.4])))

# --- Opportunities ----------------------------------------------------------
stages = ["Discovery", "Qualification", "Proposal", "Negotiation"]
stage_prob = {"Discovery": 0.10, "Qualification": 0.25, "Proposal": 0.50, "Negotiation": 0.75}
lost_reasons = ["Price", "Competitor", "No Budget", "Timing", "No Decision", "Product Fit"]
seg_team = {"Enterprise": "Enterprise", "Mid-Market": "Mid-Market", "SMB": "SMB"}
opps, hist = [], []
ok = 1
for _, l in leads[leads.Status == "Qualified"].iterrows():
    a = accounts.loc[l.AccountKey - 1]
    pool = reps[reps.Team == seg_team[a.Segment]]
    rep = pool.sample(1, random_state=int(rng.integers(0, 1e9))).iloc[0]
    c0 = pd.Timestamp(l.CreatedDate) + pd.Timedelta(days=int(rng.integers(1, 12)))
    base = {"Enterprise": 95000, "Mid-Market": 32000, "SMB": 9000}[a.Segment]
    amount = round(float(base * rng.lognormal(0, 0.55)), -2)
    cycle = int({"Enterprise": 95, "Mid-Market": 55, "SMB": 28}[a.Segment] * rng.lognormal(0, 0.4))
    win_p = float(np.clip(0.27 * rep.Skill * (1.25 if l.LeadSource in ("Referral", "Partner") else 1.0)
                          * (0.8 if amount > base * 1.8 else 1.0), 0.05, 0.7))
    close = c0 + pd.Timedelta(days=cycle)
    if close <= TODAY:
        won = rng.random() < win_p
        stage = "Closed Won" if won else "Closed Lost"
        reached = 4 if won else int(rng.choice([1, 2, 3, 4], p=[0.30, 0.30, 0.25, 0.15]))
        reason = None if won else rng.choice(lost_reasons, p=[0.26, 0.22, 0.16, 0.12, 0.16, 0.08])
        close_date, prob = close.date(), 1.0 if won else 0.0
    else:
        frac = (TODAY - c0).days / max(cycle, 1)
        reached = int(np.clip(np.ceil(frac * 4 + rng.normal(0, 0.5)), 1, 4))
        stage, reason = stages[reached - 1], None
        close_date, prob = close.date(), stage_prob[stage]
    # stage history: when each stage was entered
    cut = np.sort(rng.random(reached - 1)) if reached > 1 else np.array([])
    end = min(close, TODAY)
    entered = [c0] + [c0 + (end - c0) * float(x) for x in cut]
    for s, e in zip(stages[:reached], entered):
        hist.append((ok, s, e.date()))
    if stage.startswith("Closed"):
        hist.append((ok, stage, close.date()))
    last_touch = min(TODAY, end) - pd.Timedelta(days=int(rng.exponential(9 if stage != "Discovery" else 16)))
    opps.append({"OpportunityKey": ok, "Opportunity": f"{a.Account} - {rng.choice(['New Business', 'Expansion', 'Renewal'], p=[.6, .25, .15])}",
                 "AccountKey": int(a.AccountKey), "RepKey": int(rep.RepKey), "LeadKey": int(l.LeadKey),
                 "LeadSource": l.LeadSource, "CreatedDate": c0.date(), "CloseDate": close_date, "Stage": stage,
                 "Amount": amount, "Probability": prob, "LostReason": reason,
                 "LastActivityDate": max(last_touch, c0).date()})
    ok += 1
opps = pd.DataFrame(opps)
opps = opps[pd.to_datetime(opps.CreatedDate) <= TODAY].reset_index(drop=True)
hist = pd.DataFrame(hist, columns=["OpportunityKey", "Stage", "EnteredDate"])
hist = hist[hist.OpportunityKey.isin(opps.OpportunityKey)].copy()
hist["StageOrder"] = hist.Stage.map({"Discovery": 1, "Qualification": 2, "Proposal": 3, "Negotiation": 4, "Closed Won": 5, "Closed Lost": 6})

# --- Activities -------------------------------------------------------------
acts = []
for _, o in opps.iterrows():
    c0 = pd.Timestamp(o.CreatedDate)
    end = min(pd.Timestamp(o.CloseDate), TODAY)
    n = int(rng.poisson(4 + 6 * (o.Stage == "Closed Won") + 0.00002 * o.Amount))
    for _ in range(n):
        d = c0 + (end - c0) * float(rng.random())
        acts.append((o.OpportunityKey, o.RepKey, d.date(), rng.choice(["Call", "Email", "Meeting", "Demo"], p=[.34, .40, .18, .08])))
acts = pd.DataFrame(acts, columns=["OpportunityKey", "RepKey", "ActivityDate", "ActivityType"])
acts.insert(0, "ActivityKey", np.arange(1, len(acts) + 1))

stage_dim = pd.DataFrame({"Stage": stages + ["Closed Won", "Closed Lost"], "StageOrder": [1, 2, 3, 4, 5, 6],
                          "StageGroup": ["Open"] * 4 + ["Won", "Lost"], "DefaultProbability": [0.10, 0.25, 0.50, 0.75, 1, 0]})

reps.drop(columns="Skill").to_csv(OUT / "reps.csv", index=False)
accounts.to_csv(OUT / "accounts.csv", index=False)
leads.to_csv(OUT / "leads.csv", index=False)
opps.to_csv(OUT / "opportunities.csv", index=False)
hist.to_csv(OUT / "stage_history.csv", index=False)
acts.to_csv(OUT / "activities.csv", index=False)
stage_dim.to_csv(OUT / "stages.csv", index=False)

closed = opps[opps.Stage.str.startswith("Closed")]
print(f"leads {len(leads):,}; opps {len(opps):,}; open {len(opps) - len(closed):,}; "
      f"win rate {(closed.Stage == 'Closed Won').mean():.1%}; won {opps[opps.Stage == 'Closed Won'].Amount.sum():,.0f}; "
      f"activities {len(acts):,}")
