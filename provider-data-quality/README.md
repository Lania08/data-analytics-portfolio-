# Provider Roster Data-Quality Project

**The question:** *Which providers in a credentialing roster have the worst
data-quality issues, and where should cleanup start?*

This is a portfolio project built on **100% fictional data** — every name,
NPI, license number, and date was generated for this demo. Nothing here
describes a real provider or a real organization. The numbers below describe
the made-up dataset, not anyone's actual records.

---

## What I did (the method)

1. **Generated a synthetic 200-provider roster** (`providers_synthetic.csv`)
   with realistic credentialing fields: NPI, name, specialty, state, license
   number, license expiry, DEA expiry, a flag for whether the provider
   prescribes (not every specialty needs a DEA), board certification status,
   malpractice history flag, and CAQH attestation date. A share of rows were
   deliberately given missing, stale, expired, duplicated, or malformed
   values — the same problems that show up in real credentialing files.

2. **Wrote 12 SQL data-quality queries** (`analysis.sql`) covering: missing or
   malformed NPIs, duplicate NPIs, expired licenses, licenses expiring in the
   next 90 days, expired or missing DEA registrations for prescribers, stale
   (>120 days) or missing CAQH attestations, lapsed board certification,
   unparseable dates, per-specialty issue rates, and a "worst offenders"
   ranking of providers with 2+ issues.

3. **Built the Python analysis** (`analysis.py`) with pandas. It loads the CSV,
   runs all 12 SQL queries through Python's built-in sqlite3 to prove the SQL
   is valid, re-computes every check in pandas, and **cross-checks the two
   against each other** — they agree on every headline number. It prints the
   findings and saves the chart (`chart.png`).

## The dataset

| Detail | Value |
|---|---|
| File | `providers_synthetic.csv` |
| Rows | 200 providers |
| Specialties | 12 (e.g., Pediatrics, Cardiology, Radiology) |
| States | 7 (GA, FL, TX, NC, SC, TN, AL) |
| Reference "today" | 2026-10-03 (all relative dates are built from this) |
| Synthetic label | Every row carries `data_source_note`: *"SYNTHETIC — fictional demo data; names, NPIs, licenses, dates invented"* |

The generator (`gen_providers.py`, kept with my scratch notes — not part of the
deliverable) uses a fixed random seed, so re-generating produces the exact
same file, and anyone can re-run the analysis and get these exact results.

## The results (as of the 2026-10-03 reference date)

| Check | Providers | Share |
|---|---|---|
| Missing or malformed NPI (not 10 digits) | 12 | 6.0% |
| Duplicate NPI shared by 2+ records | 4 (2 duplicate groups) | 2.0% |
| Missing license number | 6 | 3.0% |
| **Expired** license | 15 | 7.5% |
| License expiring within 90 days | 11 | 5.5% |
| **Expired** DEA (prescribers) | 10 | 5.0% |
| Missing DEA for prescribers | 8 | 4.0% |
| Stale CAQH attestation (>120 days) | 18 | 9.0% |
| Missing CAQH attestation date | 12 | 6.0% |
| Board cert lapsed / not certified | 38 | 19.0% |
| Unparseable dates (e.g. `13/45/2026`, `02/30/2026`, `pending`) | 3 | 1.5% |
| Malpractice history flagged | 11 | 5.5% |

- **89 of 200 providers (44.5%)** have at least one data-quality issue.
- **28 providers (14.0%)** have two or more issues — that's the suggested
  cleanup queue.
- The two worst records (3 issues each — expired license + missing CAQH +
  bad board status): Leo Kane (General Surgery, NC) and Ibrahim Ashford
  (Neurology, NC).
- Highest issue rate by specialty: **Pediatrics, 69.2%** (9 of 13 providers);
  lowest: **Emergency Medicine, 21.4%** (3 of 14). Full breakdown is in
  `chart.png`.

## How to run it

Requirements: Python 3 with `pandas` and `matplotlib`
(`pip install pandas matplotlib` — sqlite3 is built into Python).

```bash
cd portfolio-project-provider-data-quality
python3 analysis.py
```

That prints every finding, proves all 12 SQL queries run, cross-checks the
SQL results against the pandas results, and regenerates `chart.png`.

To run the SQL on its own against the CSV with the sqlite3 command-line tool:

```bash
sqlite3 :memory: -cmd ".mode table" \
  ".import --csv --skip 1 providers_synthetic.csv providers" \
  < analysis.sql
```

(Paste any single query from `analysis.sql` to run just that check.)

Note: if you re-run on a later real-world date, the expired/expiring counts
will shift — that's expected, since they're measured against "today".

## How to talk about this in interviews

Say it in your own words, but these are the honest talking points:

- **Why this project:** "I work in medical staff credentialing, so I picked a
  problem I understand: dirty roster data slows down privileging and
  payer enrollment. I wanted to show I can find the problems *and* say
  where to start fixing them."
- **The data:** "It's synthetic — 200 fictional providers I generated with a
  seeded script, so it's fully reproducible. I labeled every row as synthetic
  so there's no confusion with real PHI."
- **The method:** "I wrote 12 SQL checks — expired licenses, stale CAQH
  attestations, missing DEAs for prescribers, bad NPIs, duplicates — then
  built the same checks in Python with pandas and had the script cross-check
  the two against each other. They agreed on every number, which is how I
  know the logic is right."
- **The recommendation:** "44.5% of the roster had at least one issue, so I
  ranked providers by issue count — 28 had two or more, and 2 had three.
  That's the cleanup queue: start with the multi-issue records instead of
  working the list alphabetically."
- **What you'd do next with real data:** "Severity-weight the issues — an
  expired license blocks privileging, a stale CAQH attestation is an admin
  follow-up — validate NPIs against the public NPPES registry, and turn the
  checks into a recurring report so the roster never drifts this far again."
- If asked about a number, point at the CSV row: every finding traces back to
  specific rows you can show. Nothing is hand-waved.
