# Data Analytics Portfolio — Lania Scales

Healthcare data analytics portfolio built during a career change from medical
staff credentialing (hospital privileging, primary-source verification, Joint
Commission standards) into data analytics. Tools: SQL, Python (pandas), Power BI.

## Projects

1. **Provider Roster Data Quality** (`provider-data-quality/`) — Which
   providers in a credentialing roster have the worst data-quality issues, and
   where should cleanup start? 12 SQL data-quality queries + a pandas
   cross-check over a synthetic 200-provider roster. Answer: 89 of 200
   providers (44.5%) have at least one issue; 28 have two or more — the
   cleanup queue.
2. **Credentialing Turnaround Dashboard** (in progress) — where applications
   get stuck, by step and specialty.
3. **OIG Exclusion Screening Pipeline** (planned) — fuzzy matching a provider
   roster against the federal exclusion list.
4. **OPPE/FPPE Outlier Analysis** (planned) — flagging practitioners trending
   the wrong way on quality metrics.

## A note on the data

Every dataset here is **100% synthetic** — generated for learning and
demonstration. Names, NPIs, license numbers, and dates are fictional. Nothing
describes a real provider, applicant, or organization.
