# 06 · Power Automate: File Intake Automation

Four cloud flows that move business files into a SharePoint landing zone, tell the data team what arrived, and send email on behalf of a data pipeline. They are generalised from flows built for client engagements; names, sites and addresses are placeholders.

![Architecture](exports/02%20Architecture.png)

Case study: [8-page PDF](exports/Power%20Automate%20-%20File%20Intake%20Automation.pdf). All four flows were deployed to a Power Automate environment and run live on 5 and 6 October 2026; the screenshots in `screenshots/` are from those runs.

## The flows

| # | Flow | Trigger | What it does |
|---|---|---|---|
| 01 | [File intake router](flows/01_file_intake_router.flow.json) | OneDrive for Business: file created or modified, subfolders included | Routes each file by name to one of five landing folders. Unknown names go to a quarantine folder. Large sales extracts are skipped |
| 02 | [Landing zone alert](flows/02_landing_zone_alert.flow.json) | SharePoint: file created or modified in the landing zone | Emails the data team with file, folder, editor, version and the refresh step that file needs. Quarantined files are sent with high importance |
| 04 | [Email attachment capture](flows/04_email_attachment_capture.flow.json) | Outlook: new email matching a subject filter, with attachments | Saves each data attachment to the landing zone with chunked transfer. For source systems that can only email their exports |
| 03 | [Pipeline notification outbox](flows/03_pipeline_notification_outbox.flow.json) | SharePoint: file created in a `Pending` folder | Reads one JSON digest per pipeline run, sends it, and moves the file to `Sent` or `Rejected` so the pipeline can see the outcome. Standard connectors only |

```
analyst's OneDrive ──▶ 01 router ──▶ SharePoint landing zone ──▶ dataflows / pipeline ──▶ Power BI
                          │                    │                          │
                          └─▶ _Inbox Unrouted  └─▶ 02 alert email         └─▶ 03 outbox ──▶ digest email
emailed exports ───▶ 04 capture ──▶ SharePoint landing zone
```

## Design decisions

**01 · File intake router**

- Filtering happens in trigger conditions, so Office lock files (`~$`), folders and unsupported extensions never consume a run.
- `splitOn` is `@triggerBody()`. The OneDrive trigger returns a bare array; the SharePoint trigger in flow 02 wraps items in `value`. Using the wrong one fails every run.
- Rule order matters. Contract logs are named "Quote Log Customer Contracts …", so the contract rule is tested before the quote rule.
- Case policy is set per file family to match the downstream reader. Most rules are case-insensitive. Inventory names are case-exact because the dataflow that reads them is case-sensitive: a wrongly cased file is quarantined and alerted instead of landing where nothing reads it.
- Same-name uploads overwrite the destination, and SharePoint keeps the previous copy as a version. Daily files are re-dropped under the same name.

**02 · Landing zone alert**

- The email names the next refresh step for that file type. Refreshes are not triggered automatically, because source file layouts change and a person should look first.
- One flow covers normal uploads and quarantined files; the subject and importance change.

**04 · Email attachment capture**

- The subject filter and the attachment requirement sit on the trigger, so unrelated mail never starts a run.
- Inline images such as signatures are filtered out before the copy; only `.csv` and `.xlsx` attachments are saved.

**03 · Pipeline notification outbox**

- The pipeline renders the digest and writes it as a JSON file; the flow owns the mail connection. No mail credentials live in the data platform.
- A file drop replaces an HTTP trigger, so the flow needs no Premium licence.
- The folder is the status. `Sent` means delivered, `Rejected` means the payload was missing recipients, subject or body, and a file still in `Pending` means the send failed and the run can be resubmitted.
- In the original engagement this was designed so that one receiving flow takes over from a set of per-region polling flows.

## Checks

| Check | Result |
|---|---|
| `python tests/test_routing.py` | 16/16 file names route as expected, including the ordering trap, wrong-case inventory and skip cases. The test is a Python mirror of the routing expression, not the Power Automate engine |
| Flow 01 live run, 5 October 2026 | Seven test files were dropped into the OneDrive folder. The `.txt` file started no run. Six runs fired on the next 5-minute poll and all succeeded: quote log to Quotes, contract log to Contracts, registration log to Design Registrations, an unknown name and a wrongly cased inventory file to `_Inbox Unrouted`, and the sales extract skipped with no copy |
| Flow 01 overwrite, same day | The same seven names were dropped again with new content. Six more runs succeeded, so a same-name file replaces the earlier copy without error |
| Flow 03 rejection path, same day | A digest with an empty recipient list was written to `Pending`. The flow read it, skipped the send and moved the file to `Rejected` |
| Flow 03 send path, same day | A valid digest was read, emailed and moved to `Sent` in one run; an invalid one dropped alongside it went to `Rejected` |
| Flow 02 live run, same day | Six runs, six alert emails: one per file that reached the landing zone, including the two quarantined files and the export saved by flow 04 |
| Flow 04 live run, same day | A test email with a `.csv` and a `.png` attachment arrived. One run; only the `.csv` was saved to `Trend Exports` |
| Power Automate definition validator on flow 02 | No structural errors after fixes |

The test files were small text payloads with spreadsheet names, so file size and content integrity were not exercised. A failed send in flow 03 (file left in `Pending`) was not provoked.

One behaviour to know: flow 03's trigger only sees files created after its first successful poll, so the `Pending`, `Sent` and `Rejected` folders must exist before the flow is switched on.

## Folders

| Folder | Contents |
|---|---|
| `flows/` | The four flow definitions (`triggers` and `actions`) |
| `tests/` | Routing check for flow 01 |
| `exports/` | Architecture diagram, the 8-page case study (PNG + PDF) and the thumbnail |
| `screenshots/` | Portal captures from the live runs: canvases, run views, run history, landing zone, emails |
| `diagram/` | HTML sources for the diagram, cover and slides (`build_slides.py` generates the slide pages) |
| `_build/` | Deploy, run-check, crop, render and PDF scripts |

## Deploy

Each file is a flow definition (`triggers` and `actions`). Create OneDrive, SharePoint and Office 365 Outlook connections, copy `_build/env.example.json` to `_build/env.local.json`, fill in the values below, then run `python _build/deploy.py flows/<file> "<flow name>"` after `az login`. `python _build/runs.py <since-iso-utc>` lists runs and action results for the deployed flows.

To rebuild the slides and PDF: `python _build/make_pdf.py` (needs Chrome).

| Placeholder | Where |
|---|---|
| `<onedrive-drop-folder-id>` | flow 01 trigger |
| `https://contoso.sharepoint.com/sites/DataLanding` and `/Shared Documents/Landing/...` | flows 01, 02 and 04 |
| `<document-library-id>` | flow 02 trigger |
| `data-team@contoso.com` | flow 02 |
