# Credentialing Turnaround Analysis

**Where do credentialing applications get stuck — and what would a credentialing team fix first?**

This project analyzes a synthetic dataset of 120 medical staff credentialing applications (hospital privileging) to find the bottleneck in the application-to-decision workflow. All data is fictional and was generated for portfolio purposes; no real provider or patient information is included.

## Tools

- **SQL (SQLite)** — all analysis queries
- **CSV** — source data (3 tables)
- **Dashboard** — interactive summary of the findings

## The data

| Table | Rows | What it holds |
|---|---|---|
| `applications.csv` | 120 | One row per application: provider, specialty, application type, received date, status, decision date, total days to decision |
| `application_steps.csv` | 620 | Every workflow step each application passed through, with days spent in each step |
| `verification_items.csv` | 880 | Every primary-source verification item requested (license, DEA, NPDB, education, malpractice history, references) with return times |

Specialties covered: Anesthesiology, Cardiology, Emergency Medicine, Family Medicine, General Surgery, Neurology, OB/GYN, Orthopedic Surgery, Pediatrics, Radiology.

## Key findings

1. **Primary-source verification is the bottleneck.** Applications spend an average of **35.8 days** in the verification step — about **6× longer** than the next slowest step (Peer References, 6.0 days). Every other step averages 5 days or less.
2. **The State Medical License check is the slowest single verification item**, averaging **24.1 days** to return, followed by Malpractice Claims History (17.9 days) and Education & Training (15.5 days). The NPDB query is fastest at 4.5 days.
3. **Turnaround varies by specialty.** OB/GYN applications take the longest start to finish (**91.0 days** average); Family Medicine is fastest (**69.6 days**). Overall average across decided applications: **80.8 days**.
4. **15 of the 37 still-open applications have been sitting in a single step for 30+ days** — most of them waiting at Completeness Review — and 23 of the 37 open applications are already 61–90 days old.

## Questions the SQL answers (`starter-queries.sql`)

1. Average turnaround by specialty — which specialties wait longest?
2. Average days per workflow step — where is the bottleneck?
3. Applications stuck 30+ days in their current step — what needs attention today?
4. Aging buckets for the open queue — how old is the unfinished work?
5. Monthly received vs. decided volume — is the team keeping up?
6. Slowest verification items — which checks drag the longest?
7. Decision outcomes by specialty

## What I would recommend (the "so what")

- Attack the verification step first: it holds ~44% of the average application's total lifetime. Earlier license-verification requests and parallel (rather than sequential) item requests would cut the most days.
- Add an aging alert at 30 days in any single step — 15 applications in this dataset would have been flagged before they stalled.
- Watch Completeness Review on the open queue specifically: completed applications move through it in 5 days, yet it is where most currently-stuck applications are waiting — a sign of queue neglect rather than step difficulty.

## Files

- `applications.csv`, `application_steps.csv`, `verification_items.csv` — the dataset
- `starter-queries.sql` — the 7 analysis queries (SQLite syntax)
- `dashboard.html` — the interactive dashboard (open in any browser)

## Author

Lania Scales — credentialing specialist transitioning into healthcare data analytics.
[GitHub portfolio](https://github.com/Lania08/data-analytics-portfolio-)
