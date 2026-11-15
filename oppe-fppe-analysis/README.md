# OPPE/FPPE Outlier Analysis

**Finding the practitioners whose quality metrics are drifting the wrong way — before they become a problem.**

Under Joint Commission standards, hospitals run OPPE (Ongoing Professional Practice Evaluation) on every privileged practitioner: a recurring look at quality metrics over time. When OPPE shows someone trending outside peer norms, the follow-up is an FPPE (Focused Professional Practice Evaluation) — a closer, time-limited review. Somebody has to turn the raw metrics into a short, defensible list of who needs that closer look. That is this project.

All data is fictional: 40 practitioners over 8 quarters, with problem patterns planted in the data (steady decline, sudden spike, chronic over-threshold performance, an improvement case, and a low-volume trap) so the analysis can be graded against a known answer key.

## Tools

- **Python** — pandas for the analysis, numpy for trend slopes
- **CSV** — metrics in, flags out

## The data

`oppe_metrics.csv` — 320 rows (40 practitioners × 8 quarters, 2024Q1–2025Q4), one row per practitioner per quarter:

| Column | Meaning |
|---|---|
| `case_volume` | Cases that quarter — the denominator behind every rate |
| `chart_deficiency_rate` | % of charts with documentation deficiencies (lower is better) |
| `complaint_rate` | Patient complaints per 100 cases (lower is better) |
| `complication_rate` | % of cases with a complication (lower is better) |

## How the flagging works (`analyze_oppe.py`)

Review thresholds sit above the peer norms (~6% / ~1.2 / ~2.5%): chart deficiency > 10%, complaints > 3.0 per 100, complications > 5%.

- **Volume guard (runs first).** Average quarterly volume under 20 cases → **MONITOR**, never flagged. A practitioner with 7 cases and 1 bad chart shows a 14% deficiency rate; that is arithmetic, not a quality signal.
- **CHRONIC** — over a threshold in 6 or more of 8 quarters.
- **TREND** — chart deficiency rate rising ≥ 0.8 points per quarter (least-squares slope) *and* currently above the peer median for the latest quarter.
- **SPIKE** — the last 2 quarters average ≥ 5 points above the practitioner's own first-6-quarter average, and over threshold.

Flags recommend an FPPE review; they are a starting point for peer review, never a conclusion on their own.

## Results

| Outcome | Count |
|---|---|
| Practitioners analyzed | 40 |
| **FPPE review recommended** | **4** |
| Monitor (low volume) | 1 |
| Continue routine OPPE | 35 |

The four flagged practitioners (all planted patterns, all caught):

- **DR-104** — CHRONIC: chart deficiency over threshold in 8 of 8 quarters (latest 14.1%)
- **DR-102** — CHRONIC + TREND: over threshold in 6 of 8 quarters and rising +1.6 pts/quarter to 16.7% vs a 6.2% peer median
- **DR-101** — TREND: rising +1.3 pts/quarter to 16.9%
- **DR-103** — SPIKE: jumped from a 6.1% average over the first 6 quarters to 14.5% in the last 2

Just as important, two planted cases were correctly **not** flagged for FPPE:

- **DR-105** — poor metrics in the first half of the period, then sustained improvement (an earlier focused review that worked). Flagging him again would punish exactly the recovery the process is supposed to produce.
- **DR-106** — the worst-looking rates in the dataset, on an average of 7 cases per quarter. The volume guard routes her to monitoring instead of a focused review built on unreliable numbers.

## Files

- `generate_data.py` — builds the dataset (seeded, reproducible), planted patterns documented
- `analyze_oppe.py` — the OPPE analysis
- `oppe_metrics.csv` — input metrics
- `oppe_flags.csv` — output: flagged practitioners with evidence and recommendation

## Author

Lania Scales — credentialing specialist transitioning into healthcare data analytics.
[GitHub portfolio](https://github.com/Lania08/data-analytics-portfolio-)
