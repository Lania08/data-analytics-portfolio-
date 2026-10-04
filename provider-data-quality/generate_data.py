"""Generate the synthetic provider roster CSV (portfolio project pack).

All data is FICTIONAL: fake NPIs, made-up names, generated dates.
Deterministic via seed so the analysis results are reproducible.
"""
import csv
import random
from datetime import date, timedelta

SEED = 42617
N_ROWS = 200
REF_DATE = date(2026, 10, 3)  # "today" used for every relative date

rng = random.Random(SEED)

FIRST = ["Amara", "Lena", "Marcus", "Priya", "James", "Sofia", "David", "Nadia",
         "Omar", "Grace", "Ethan", "Maya", "Victor", "Hannah", "Ibrahim", "Lucia",
         "Noah", "Zara", "Felix", "Tara", "Samuel", "Ivy", "Diego", "Ruth",
         "Kofi", "Elif", "Peter", "Aisha", "Leo", "Nina", "Ravi", "Clara"]
LAST = ["Okafor", "Nguyen", "Ellis", "Sharma", "Bennett", "Rossi", "Kaplan",
        "Haddad", "Farouk", "Whitfield", "Cross", "Iyer", "Delgado", "Ashford",
        "Mensah", "Vargas", "Quill", "Rahman", "Stowe", "Pillai", "Thorn",
        "Beaumont", "Kane", "Duarte", "Sellers", "Novak", "Preston", "Ali",
        "Vance", "Moreno"]
SPECIALTIES = ["Anesthesiology", "Family Medicine", "Internal Medicine",
               "Pediatrics", "Cardiology", "Orthopedic Surgery",
               "Emergency Medicine", "Radiology", "Psychiatry",
               "General Surgery", "Obstetrics & Gynecology", "Neurology"]
STATES = ["GA", "FL", "TX", "NC", "SC", "TN", "AL"]
PRESCRIBER_BY_SPECIALTY = {
    "Anesthesiology": 1.0, "Family Medicine": 1.0, "Internal Medicine": 1.0,
    "Pediatrics": 1.0, "Cardiology": 1.0, "Orthopedic Surgery": 1.0,
    "Emergency Medicine": 1.0, "Radiology": 0.15, "Psychiatry": 1.0,
    "General Surgery": 1.0, "Obstetrics & Gynecology": 1.0, "Neurology": 1.0,
}
BOARD_STATUSES = ["Board Certified", "Board Eligible", "Not Certified", "Lapsed"]

def iso(d):
    return d.strftime("%Y-%m-%d")

def fake_npi(r):
    # Fictional 10-digit NPI (real individual NPIs begin 1-4; these are invented)
    return str(r.choice([1, 2])) + "".join(str(r.randrange(10)) for _ in range(9))

names = [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in range(N_ROWS)]
# ensure a couple of distinct names share nothing; fine as-is (duplicates unlikely)

rows = []
used_npis = set()
npis = []
for i in range(N_ROWS):
    npi = fake_npi(rng)
    while npi in used_npis:
        npi = fake_npi(rng)
    used_npis.add(npi)
    npis.append(npi)

for i in range(N_ROWS):
    spec = rng.choice(SPECIALTIES)
    st = rng.choice(STATES)
    prescribes = "Y" if rng.random() < PRESCRIBER_BY_SPECIALTY[spec] else "N"

    # license expiry: mostly healthy 1-3y out; some short
    license_expiry = iso(REF_DATE + timedelta(days=rng.randint(200, 1100)))
    # DEA: ~3y cycle for prescribers
    dea_expiry = (iso(REF_DATE + timedelta(days=rng.randint(150, 1050)))
                  if prescribes == "Y" else "")
    # CAQH: re-attestation required every 120 days; mostly recent
    caqh = iso(REF_DATE - timedelta(days=rng.randint(0, 100)))
    board = rng.choices(BOARD_STATUSES, weights=[70, 12, 10, 8])[0]
    malp = "Y" if rng.random() < 0.06 else "N"
    lic_no = f"{st}-{rng.randint(100000, 999999)}"

    rows.append({
        "row_id": i + 1,
        "npi": npis[i],
        "provider_name": names[i],
        "specialty": spec,
        "state": st,
        "license_number": lic_no,
        "license_expiry_date": license_expiry,
        "dea_expiry_date": dea_expiry,
        "prescribes_flag": prescribes,
        "board_certification_status": board,
        "malpractice_history_flag": malp,
        "caqh_attestation_date": caqh,
        "data_source_note": "SYNTHETIC - fictional demo data; names, NPIs, licenses, dates invented",
    })

# ---- Inject realistic data-quality issues ---------------------------------
def pick(count, avoid=()):
    avoid = set(avoid)
    chosen = []
    while len(chosen) < count:
        j = rng.randrange(N_ROWS)
        if j not in chosen and j not in avoid:
            chosen.append(j)
    return chosen

# 1) Missing NPIs (8)
for j in pick(8):
    rows[j]["npi"] = ""
# 2) Malformed NPIs (4) — wrong length
for j in pick(4):
    rows[j]["npi"] = "".join(str(rng.randrange(10)) for _ in range(9))
# 3) Duplicate NPIs (2 pairs -> 4 rows share 2 NPIs)
dup_pairs = pick(4)
rows[dup_pairs[1]]["npi"] = rows[dup_pairs[0]]["npi"]
rows[dup_pairs[3]]["npi"] = rows[dup_pairs[2]]["npi"]
# 4) Expired licenses (15)
for j in pick(15):
    rows[j]["license_expiry_date"] = iso(REF_DATE - timedelta(days=rng.randint(30, 700)))
# 5) Licenses expiring within 90 days (12)
for j in pick(12):
    rows[j]["license_expiry_date"] = iso(REF_DATE + timedelta(days=rng.randint(1, 89)))
# 6) Expired DEA for prescribers (10)
prescribers = [j for j, r in enumerate(rows) if r["prescribes_flag"] == "Y" and r["dea_expiry_date"]]
for j in prescribers[:10]:  # deterministic slice after shuffle? keep simple, fixed slice
    rows[j]["dea_expiry_date"] = iso(REF_DATE - timedelta(days=rng.randint(15, 500)))
# 7) Missing DEA for prescribers (8) - pick prescribers with healthy DEA
dea_ok = [j for j, r in enumerate(rows)
          if r["prescribes_flag"] == "Y" and r["dea_expiry_date"] and r["dea_expiry_date"] > iso(REF_DATE)]
for j in dea_ok[:8]:
    rows[j]["dea_expiry_date"] = ""
# 8) Stale CAQH attestation (>120 days, 18)
for j in pick(18):
    rows[j]["caqh_attestation_date"] = iso(REF_DATE - timedelta(days=rng.randint(130, 600)))
# 9) Missing CAQH attestation (12)
for j in pick(12):
    rows[j]["caqh_attestation_date"] = ""
# 10) Board certification Lapsed (10)
for j in pick(10):
    rows[j]["board_certification_status"] = "Lapsed"
# 11) Missing license number (6)
for j in pick(6):
    rows[j]["license_number"] = ""
# 12) Malformed dates (3) - unparseable strings (rejected by both SQLite and pandas)
bad_dates = ["13/45/2026", "02/30/2026", "pending"]
for k, j in enumerate(pick(3)):
    rows[j]["license_expiry_date"] = bad_dates[k]

# Sort by row_id (already) and write
OUT = "/home/hatch/workspace/goals/career-change-to-data-analyst/files/portfolio-project-provider-data-quality/providers_synthetic.csv"
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(f"wrote {len(rows)} rows -> {OUT}")
