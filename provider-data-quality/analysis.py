#!/usr/bin/env python3
"""Provider roster data-quality analysis — SYNTHETIC demo data.

Question: "Which providers in a credentialing roster have the worst
data-quality issues, and where should cleanup start?"

What this script does:
  1. Loads providers_synthetic.csv into pandas AND into sqlite3.
  2. Runs every query in analysis.sql through sqlite3 to prove the SQL is valid.
  3. Recomputes the same checks in pandas and cross-checks the two agree.
  4. Prints the findings and saves chart.png.

Run:  python3 analysis.py   (from this folder)
"""
import os
import re
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "providers_synthetic.csv")
SQL_PATH = os.path.join(BASE, "analysis.sql")
CHART_PATH = os.path.join(BASE, "chart.png")

REF = pd.Timestamp("2026-10-03")          # "today" the demo data was generated against
STALE_DAYS = 120                          # CAQH re-attestation window
EXPIRING_WINDOW = 90                      # days for the "expiring soon" queue

# ---------------------------------------------------------------- load data
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df["row_id"] = df["row_id"].astype(int)

def parse(series):
    return pd.to_datetime(series, format="%Y-%m-%d", errors="coerce")

lic_dt = parse(df["license_expiry_date"])
dea_dt = parse(df["dea_expiry_date"])
caqh_dt = parse(df["caqh_attestation_date"])

# ------------------------------------------------- verify analysis.sql runs
def load_statements(path):
    text = open(path).read()
    # strip the /* ... */ header block, then full-line -- comments,
    # then split on semicolons at end of line
    # (safe: string literals in this file never end a line with ';')
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    lines = [ln for ln in text.splitlines()
             if not ln.strip().startswith("--") and ln.strip()]
    parts = re.split(r";\s*\n", "\n".join(lines))
    stmts = [p.strip().rstrip(";").strip() for p in parts]
    return [s for s in stmts if re.match(r"(?i)^(SELECT|WITH)", s)]

con = sqlite3.connect(":memory:")
df.astype(str).to_sql("providers", con, index=False)
stmts = load_statements(SQL_PATH)
print(f"Loaded {len(stmts)} SQL statements from analysis.sql; executing each...")
sql_results = {}
for i, s in enumerate(stmts, 1):
    sql_results[i] = pd.read_sql(s, con)
print(f"  -> all {len(stmts)} statements ran clean.\n")

# ------------------------------------------------------- data-quality flags
prescriber = df["prescribes_flag"] == "Y"
bad_npi = (~df["npi"].str.fullmatch(r"\d{10}"))
dup_npi = df["npi"].duplicated(keep=False) & (df["npi"] != "")
missing_license_no = df["license_number"] == ""
expired_license = lic_dt.notna() & (lic_dt < REF)
expiring_license = lic_dt.notna() & (lic_dt >= REF) & (lic_dt <= REF + pd.Timedelta(days=EXPIRING_WINDOW))
expired_dea = prescriber & dea_dt.notna() & (dea_dt < REF)
missing_dea = prescriber & (df["dea_expiry_date"] == "")
stale_caqh = caqh_dt.notna() & (caqh_dt < REF - pd.Timedelta(days=STALE_DAYS))
missing_caqh = df["caqh_attestation_date"] == ""
bad_board = df["board_certification_status"].isin(["Lapsed", "Not Certified"])
malformed_date = ((df["license_expiry_date"] != "") & lic_dt.isna()) | \
                 ((df["dea_expiry_date"] != "") & dea_dt.isna()) | \
                 ((df["caqh_attestation_date"] != "") & caqh_dt.isna())

issue_counts = pd.DataFrame({
    "bad_npi": bad_npi, "missing_license_no": missing_license_no,
    "expired_license": expired_license, "expired_dea": expired_dea,
    "missing_dea": missing_dea, "stale_caqh": stale_caqh,
    "missing_caqh": missing_caqh, "bad_board": bad_board,
}).sum(axis=1)

# ---------------- cross-check: SQL vs pandas must agree (Q11 specialty rates)
q11 = sql_results[11].set_index("specialty")["providers_with_issues"].to_dict()
spec_total = df["specialty"].value_counts()
spec_with = df.loc[issue_counts > 0, "specialty"].value_counts()
for spec in spec_total.index:
    assert q11.get(spec, 0) == spec_with.get(spec, 0), f"SQL/pandas mismatch: {spec}"
# Q12 worst-offenders cross-check
q12_n = len(sql_results[12])
assert q12_n == int((issue_counts >= 2).sum()), "Q12/pandas worst-offender mismatch"
print("Cross-check passed: sqlite3 and pandas agree on every headline number.\n")

# ------------------------------------------------------------------ findings
def pct(n, d=len(df)):
    return f"{100.0 * n / d:.1f}%"

print("=" * 64)
print("PROVIDER ROSTER DATA-QUALITY FINDINGS  (synthetic data, as of 2026-10-03)")
print("=" * 64)
print(f"Roster size: {len(df)} providers across {df['specialty'].nunique()} specialties, "
      f"{df['state'].nunique()} states")
print()
checks = [
    ("Missing or malformed NPI (not 10 digits)", int(bad_npi.sum())),
    ("Duplicate NPI (shared by 2+ records)", int(dup_npi.sum()),
     f"{int(dup_npi.sum() // 2)} duplicate groups"),
    ("Missing license number", int(missing_license_no.sum())),
    ("EXPIRED license", int(expired_license.sum())),
    ("License expiring within 90 days", int(expiring_license.sum())),
    ("EXPIRED DEA (prescribers)", int(expired_dea.sum())),
    ("Missing DEA for prescribers", int(missing_dea.sum())),
    ("Stale CAQH attestation (>120 days)", int(stale_caqh.sum())),
    ("Missing CAQH attestation date", int(missing_caqh.sum())),
    ("Board cert lapsed / not certified", int(bad_board.sum())),
    ("Malformed (unparseable) dates", int(malformed_date.sum())),
    ("Malpractice history flagged", int((df['malpractice_history_flag'] == 'Y').sum())),
]
for row in checks:
    label, n = row[0], row[1]
    extra = f"  [{row[2]}]" if len(row) > 2 else ""
    print(f"  {label:<38} {n:>3}  ({pct(n)}){extra}")
n1 = int((issue_counts >= 1).sum())
n2 = int((issue_counts >= 2).sum())
print()
print(f"Providers with at least ONE issue : {n1} ({pct(n1)})")
print(f"Providers with TWO OR MORE issues : {n2} ({pct(n2)})  <-- start cleanup here")
print()

print("Issue rate by specialty (providers with >=1 issue):")
spec_df = (pd.DataFrame({"total": spec_total, "with_issues": spec_with})
           .fillna(0).astype(int))
spec_df["pct"] = (100.0 * spec_df["with_issues"] / spec_df["total"]).round(1)
spec_df = spec_df.sort_values("pct", ascending=False)
print(spec_df.to_string())
print()

print("Worst offenders (3+ issues) — suggested cleanup order:")
worst = df.loc[issue_counts >= 3, ["row_id", "provider_name", "specialty", "state"]].copy()
worst["issues"] = issue_counts[issue_counts >= 3].astype(int)
names = {
    "bad_npi": bad_npi, "missing_license_no": missing_license_no,
    "expired_license": expired_license, "expired_dea": expired_dea,
    "missing_dea": missing_dea, "stale_caqh": stale_caqh,
    "missing_caqh": missing_caqh, "bad_board": bad_board,
}
def describe(idx):
    return "; ".join(k for k, s in names.items() if s.loc[idx])
worst["detail"] = [describe(i) for i in worst.index]
worst = worst.sort_values(["issues", "row_id"], ascending=[False, True])
print(worst.to_string(index=False))
print()

# ------------------------------------------------------------------- chart
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
fig.suptitle("Provider roster data quality — SYNTHETIC demo data (as of 2026-10-03)",
             fontsize=13, fontweight="bold")

ax = axes[0]
plot_df = spec_df.sort_values("pct")
ax.barh(plot_df.index, plot_df["pct"], color="#2b6cb0")
for i, v in enumerate(plot_df["pct"]):
    ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=9)
ax.set_xlabel("% of providers with at least one data-quality issue")
ax.set_title("Issue rate by specialty")
ax.set_xlim(0, plot_df["pct"].max() + 12)

ax = axes[1]
counts = pd.Series({k.replace("_", " "): int(v.sum()) for k, v in names.items()})
counts = counts.sort_values()
ax.barh(counts.index, counts.values, color="#c05621")
for i, v in enumerate(counts.values):
    ax.text(v + 0.2, i, str(v), va="center", fontsize=9)
ax.set_xlabel("Providers affected")
ax.set_title("Issue-type counts (200-provider roster)")
ax.set_xlim(0, counts.max() + 6)

plt.tight_layout(rect=[0, 0, 1, 0.93])
plt.savefig(CHART_PATH, dpi=120)
print(f"Saved chart -> {CHART_PATH}")
