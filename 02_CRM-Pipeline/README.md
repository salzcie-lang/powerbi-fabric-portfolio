# 02 · CRM Pipeline

**Question:** will we hit quota, and where does the funnel leak? Built for sales operations and team leads.

![Pipeline Overview](screenshots/Pipeline%20Overview.png)

## Pages

| Page | What it shows |
|---|---|
| Pipeline Overview | Open pipeline, closed-won and quota attainment with trends |
| [Funnel & Conversion](screenshots/Funnel%20%26%20Conversion.png) | Stage-to-stage conversion and lead-source performance |
| [Rep Performance](screenshots/Rep%20Performance.png) | Closed revenue, quota and activity by rep |
| [Deal Detail](screenshots/Deal%20Detail.png) | Opportunity-level table |

## Model

- `Opportunities`, `Leads`, `Stage History` and `Activities` as facts with `Accounts`, `Reps`, `Stages` and a `Date` table; 8 relationships
- 62 DAX measures grouped as Closed, Pipeline, Leads, Quota and Activity, plus label and conditional-formatting measures
- Model source is TMDL in `CRMPipeline.SemanticModel/definition`; the report is PBIR in `CRMPipeline.Report/definition`

## Data

Synthetic and seeded, January 2025 to September 2026, in `data/`. Planted patterns: referral and partner leads win far more often, and deals stall in Discovery.

## Open it

1. Open `CRMPipeline.pbip` in Power BI Desktop (PBIP support enabled).
2. In **Transform data > Edit parameters**, set `DataFolder` to the absolute path of this folder's `data/` directory.
3. Refresh.

Rebuild from scratch with the scripts in [`_scripts`](../_scripts): `generate_crm.py`, `model_crm.py`, `make_background_crm.py`, `build_crm.sh`.

Tested: built and rendered in Power BI Desktop against the CSV files here; the images above are captures of those pages. Not tested: opening from a fresh clone on another machine, or publishing to the Power BI service.
