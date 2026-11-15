# OIG Exclusion Screening Pipeline

**Screening a provider roster against an exclusion list — including the matches that exact matching misses.**

Federal healthcare programs cannot pay for services ordered or provided by excluded individuals. Hospitals and health plans are expected to screen providers against the OIG's List of Excluded Individuals/Entities (LEIE) — and a name spelled one letter differently on the exclusion record is exactly how an excluded person slips through a name-only check.

This project builds a small, auditable screening pipeline in Python. All data is fictional: the roster and the exclusion records were generated with planted test cases (misspellings, hyphenated surnames, an initial-only first name, and same-name/different-person traps) so the pipeline's accuracy can be measured instead of assumed. In production, the same script runs against the real monthly LEIE download with no code changes.

## Tools

- **Python** — pandas for data handling, rapidfuzz for fuzzy name matching
- **CSV** — roster, exclusion list, and review output

## The data

| File | Rows | What it holds |
|---|---|---|
| `provider_roster.csv` | 200 | Fictional providers to screen: name, date of birth, NPI, specialty, practice state |
| `exclusion_list.csv` | 45 | Fictional exclusion records modeled on LEIE fields: name, date of birth, exclusion type (1128a/b authorities), exclusion date, state |
| `screening_results.csv` | 15 | Output: every flagged provider, with the matched record and the reason it was flagged |

## How the screening works (`screen_providers.py`)

1. **Normalize** — names are uppercased, punctuation is stripped, and spacing is standardized in both files before any comparison.
2. **Pass 1 — Exact match.** First name + last name + date of birth identical → *EXACT MATCH — excluded, escalate.*
3. **Pass 2 — Rule match.** Last name + date of birth identical and the first initial matches → catches records where the first name was reduced to an initial (e.g., "D. Martin").
4. **Pass 3 — Fuzzy match.** First and last names are scored separately (rapidfuzz) and averaged; the last name must score at least 80 on its own (token-set scoring, so CARTER matches CARTER-REYES). Scores ≥ 85 flag the provider:
   - Same date of birth → *FUZZY MATCH — same person likely, review*
   - Different date of birth → *NAME SIMILARITY ONLY — DOB differs, review* (probably a different person who shares a common name)

Nothing is auto-confirmed or auto-cleared beyond the exact pass: the pipeline flags, and a human decides.

## Results on the test data

| Outcome | Count |
|---|---|
| Providers screened | 200 |
| Exact matches | 8 |
| Fuzzy matches (same DOB — would have been missed by exact matching) | 4 |
| Name-only similarities (DOB differs — flagged for review, not treated as matches) | 3 |
| Clear | 185 |
| **Total flagged for human review** | **15** |

All 12 planted same-person cases were caught (8 exact, 4 fuzzy/rule), and both planted same-name traps landed in the review bucket instead of being reported as exclusions.

## What tuning taught me

The first version scored the whole name at once with token-set matching and flagged **31** providers — anyone who shared one common name token with an excluded person (e.g., "Thomas Thomas" matching "Elizabeth Thomas" at 100%). A review queue that noisy trains people to ignore it. Scoring first and last names separately and requiring the surname to match on its own cut the queue to **15** with zero true matches lost. A screening tool is only useful if its flags are worth reading.

## Files

- `generate_data.py` — builds both datasets (seeded, reproducible) with the planted test cases documented
- `screen_providers.py` — the screening pipeline
- `provider_roster.csv`, `exclusion_list.csv` — inputs
- `screening_results.csv` — the flagged-for-review output

## Author

Lania Scales — credentialing specialist transitioning into healthcare data analytics.
[GitHub portfolio](https://github.com/Lania08/data-analytics-portfolio-)
