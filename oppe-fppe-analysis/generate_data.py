"""Generate the synthetic dataset for Project #3: OPPE/FPPE outlier analysis.

40 fictional practitioners x 8 quarters (2024Q1-2025Q4) of OPPE-style metrics:
  case_volume            - cases/encounters in the quarter (the denominator)
  chart_deficiency_rate  - % of charts with documentation deficiencies (lower is better)
  complaint_rate         - patient complaints per 100 cases (lower is better)
  complication_rate      - % of cases with a complication (lower is better)

Planted patterns (so the analysis can be graded):
  * 2 practitioners with a STEADY WORSENING trend across all 8 quarters
  * 1 practitioner with a SUDDEN SPIKE in the last 2 quarters
  * 1 practitioner CHRONICALLY above the peer group on every metric
  * 1 practitioner who was poor early, then IMPROVED after Q4 (an FPPE that worked)
  * 1 practitioner with scary-looking rates but TINY case volume
    (small numbers - should be monitored, not flagged)
  * everyone else: stable, around the peer average, normal noise

All names are fictional; seeded for reproducibility.
"""
import csv
import random

random.seed(20261115)

FIRST = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
         "David","Elizabeth","William","Barbara","Richard","Susan","Joseph","Jessica",
         "Thomas","Sarah","Charles","Karen","Daniel","Nancy","Matthew","Lisa"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
        "Rodriguez","Martinez","Wilson","Anderson","Thomas","Taylor","Moore",
        "Jackson","Martin","Lee","Thompson","White","Harris","Clark","Lewis",
        "Robinson","Walker","Young","Allen","King","Wright","Scott","Nguyen"]
SPECIALTIES = ["Anesthesiology","Cardiology","Emergency Medicine","Family Medicine",
               "General Surgery","Neurology","OB/GYN","Orthopedic Surgery",
               "Pediatrics","Radiology"]
QUARTERS = ["2024Q1","2024Q2","2024Q3","2024Q4","2025Q1","2025Q2","2025Q3","2025Q4"]

def clamp(x, lo, hi): return max(lo, min(hi, x))

practitioners = []
used = set()
while len(practitioners) < 40:
    fn, ln = random.choice(FIRST), random.choice(LAST)
    if (fn, ln) in used: continue
    used.add((fn, ln))
    practitioners.append({"id": f"DR-{101+len(practitioners)}", "name": f"{fn} {ln}",
                          "specialty": random.choice(SPECIALTIES)})

# roles by index: 0,1 worsening trend | 2 spike | 3 chronic | 4 improved | 5 low volume
rows = []
for idx, p in enumerate(practitioners):
    base_vol = random.randint(60, 140)
    for qi, q in enumerate(QUARTERS):
        vol = base_vol + random.randint(-12, 12)
        chart = clamp(random.gauss(6, 1.5), 1, 15)      # peer norm ~6%
        compl = clamp(random.gauss(1.2, 0.5), 0, 4)     # peer norm ~1.2 per 100
        comp  = clamp(random.gauss(2.5, 0.8), 0, 6)     # peer norm ~2.5%
        if idx in (0, 1):                                # steady worsening
            chart += qi * 1.6; compl += qi * 0.45; comp += qi * 0.55
        elif idx == 2:                                   # sudden spike, last 2 quarters
            if qi >= 6: chart += 9; compl += 2.6; comp += 3.4
        elif idx == 3:                                   # chronically high
            chart += 6.5; compl += 1.9; comp += 2.6
        elif idx == 4:                                   # poor early, improves after Q4
            if qi < 4: chart += 6; compl += 1.7; comp += 2.2
            else: chart += 1.0; compl += 0.3; comp += 0.4
        elif idx == 5:                                   # tiny volume, noisy rates
            vol = random.randint(4, 9)
            chart = clamp(random.gauss(14, 5), 2, 30); compl = clamp(random.gauss(4, 2.5), 0, 10)
            comp = clamp(random.gauss(6, 3), 0, 15)
        rows.append({"practitioner_id": p["id"], "practitioner_name": p["name"],
                     "specialty": p["specialty"], "quarter": q, "case_volume": vol,
                     "chart_deficiency_rate": round(chart, 1),
                     "complaint_rate": round(compl, 1),
                     "complication_rate": round(comp, 1)})

with open("oppe_metrics.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

print(f"{len(practitioners)} practitioners x {len(QUARTERS)} quarters = {len(rows)} rows")
print("planted: 2 worsening trends, 1 spike, 1 chronic, 1 improved-after-FPPE, 1 low-volume trap")
for i, p in enumerate(practitioners[:6]):
    print(" ", p["id"], p["name"], "-", ["worsening","worsening","spike","chronic","improved","low-volume"][i])
