# Data Analytics Portfolio — Lania Scales

Healthcare data analytics portfolio built during a career change from medical staff credentialing (hospital privileging, primary-source verification, Joint Commission standards) into data analytics. Tools: SQL, Python (pandas), Power BI.

## Projects

1. **Provider Roster Data Quality** (`provider-data-quality/`) — Which providers in a credentialing roster have the worst data-quality issues, and where should cleanup start? 12 SQL data-quality queries + a pandas cross-check over a synthetic 200-provider roster. Answer: 89 of 200 providers (44.5%) have at least one issue; 28 have two or more — the cleanup queue.

2. **Credentialing Turnaround Dashboard** (`credentialing-turnaround-analysis/`) — Where do credentialing applications get stuck, by step and specialty? SQL analysis of 120 applications (620 workflow steps, 880 verification items) with an interactive dashboard. Answer: primary-source verification is the bottleneck at 35.8 days on average — about 6× longer than any other step — and 15 applications were stalled 30+ days in a single step.

3. **OIG Exclusion Screening Pipeline** (`oig-exclusion-screening/`) — Screening a provider roster against the federal exclusion list (OIG LEIE style) with exact, rule-based, and fuzzy name matching in Python (pandas, rapidfuzz). Caught all 12 planted test matches — including 4 misspelled-name cases exact matching missed — and tuning cut false-positive review flags from 31 to 15 with no true matches lost.

4. **OPPE/FPPE Outlier Analysis** (`oppe-fppe-analysis/`) — Flagging practitioners trending the wrong way on quality metrics across 320 practitioner-quarter records (pandas, numpy), using peer benchmarks, review thresholds, and trend slopes. A case-volume guard kept low-volume practitioners out of the flag list, and all 6 planted test patterns — chronic, trending, spiking, improving, and low-volume — were classified correctly.

## A note on the data

Every dataset here is **100% synthetic** — generated for learning and demonstration. Names, NPIs, license numbers, and dates are fictional. Nothing describes a real provider, applicant, or organization.
