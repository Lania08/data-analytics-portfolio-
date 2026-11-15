"""Generate the synthetic datasets for Project #2: OIG exclusion screening.

Creates two files:
  provider_roster.csv   - 200 fictional providers to screen
  exclusion_list.csv    - 45 fictional exclusion records, modeled on the fields
                          of the real OIG LEIE (List of Excluded Individuals/Entities)

Planted test cases (so the pipeline's accuracy can be measured):
  * 6 exact matches      - same name + same date of birth in both files
  * 6 fuzzy matches      - same person, but the exclusion record spells the name
                           slightly differently (typo, transposed letters,
                           hyphenated last name, one letter off)
  * 2 review traps       - same/similar name but a DIFFERENT date of birth:
                           probably a different person who happens to share a name
  * everyone else        - no match at all

All names and dates are fictional. Dates of birth use a fixed seed so the
datasets are reproducible.
"""
import csv
import random

random.seed(20261115)

FIRST = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
         "David","Elizabeth","William","Barbara","Richard","Susan","Joseph","Jessica",
         "Thomas","Sarah","Charles","Karen","Daniel","Nancy","Matthew","Lisa",
         "Anthony","Betty","Mark","Margaret","Donald","Sandra","Steven","Ashley",
         "Paul","Kimberly","Andrew","Emily","Kenneth","Donna","Kevin","Michelle",
         "Brian","Dorothy","George","Timothy","Amanda","Ronald","Deborah","Jason"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
        "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
        "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
        "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker",
        "Young","Allen","King","Wright","Scott","Nguyen","Hill","Flores","Green",
        "Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter",
        "Roberts","Gomez","Phillips","Evans","Turner","Diaz"]
SPECIALTIES = ["Anesthesiology","Cardiology","Emergency Medicine","Family Medicine",
               "General Surgery","Neurology","OB/GYN","Orthopedic Surgery",
               "Pediatrics","Radiology","Internal Medicine","Psychiatry"]
STATES = ["GA","FL","SC","NC","TN","AL","TX","OH","PA","NY"]

def dob():
    return f"{random.randint(1955,1995)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

# ---------- provider roster (200 fictional providers) ----------
roster = []
used = set()
i = 0
while len(roster) < 200:
    fn, ln = random.choice(FIRST), random.choice(LAST)
    if (fn, ln) in used:
        continue
    used.add((fn, ln))
    i += 1
    roster.append({
        "provider_id": f"PRV-{1000+i}",
        "first_name": fn, "last_name": ln,
        "date_of_birth": dob(),
        "npi": f"1{random.randint(100000000,999999999)}",
        "specialty": random.choice(SPECIALTIES),
        "practice_state": random.choice(STATES),
    })

# ---------- exclusion list (45 fictional records) ----------
excl = []
def add_exclusion(first, last, birth, etype, edate, state):
    excl.append({"last_name": last, "first_name": first, "date_of_birth": birth,
                 "exclusion_type": etype, "exclusion_date": edate, "state": state})

ETYPES = ["1128a1 - Fraud conviction","1128a3 - Program-related conviction",
          "1128b1 - License revocation or suspension","1128b4 - False claims",
          "1128b7 - Fraud, kickbacks, or other prohibited activities"]

# 6 EXACT matches: copy name + DOB straight from roster rows 0-5
for r in roster[0:6]:
    add_exclusion(r["first_name"], r["last_name"], r["date_of_birth"],
                  random.choice(ETYPES), f"20{random.randint(15,25)}-0{random.randint(1,9)}-15",
                  r["practice_state"])

# 6 FUZZY matches: same person (same DOB), name spelled a little differently
fuzzy_variants = [
    (6,  lambda f, l: (f, l.replace("son", "sen"))),          # Johnson -> Johnsen style typo
    (7,  lambda f, l: (f.replace("ae", "ea") if "ae" in f else f + "e", l)),  # first-name letter swap / extra letter
    (8,  lambda f, l: (f, l + "-Reyes")),                     # hyphenated last name on the exclusion record
    (9,  lambda f, l: (f, l[:-1] if len(l) > 4 else l + "s")),# last name one letter off
    (10, lambda f, l: (f[0] + ".", l)),                       # first name reduced to an initial
    (11, lambda f, l: (f, l.replace("ll", "l") if "ll" in l else l.replace("s", "z"))),  # doubled letter dropped / s->z
]
for idx, fn in fuzzy_variants:
    r = roster[idx]
    nf, nl = fn(r["first_name"], r["last_name"])
    add_exclusion(nf, nl, r["date_of_birth"], random.choice(ETYPES),
                  f"20{random.randint(15,25)}-0{random.randint(1,9)}-15", r["practice_state"])

# 2 REVIEW TRAPS: same name as a roster provider, different DOB (different person)
for idx in (12, 13):
    r = roster[idx]
    add_exclusion(r["first_name"], r["last_name"], "1970-01-01" if r["date_of_birth"] != "1970-01-01" else "1980-05-05",
                  random.choice(ETYPES), "2020-03-15", r["practice_state"])

# remaining exclusions: people who are NOT on the roster at all
while len(excl) < 45:
    fn, ln = random.choice(FIRST), random.choice(LAST)
    if (fn, ln) in used:
        continue
    used.add((fn, ln))
    add_exclusion(fn, ln, dob(), random.choice(ETYPES),
                  f"20{random.randint(10,25)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                  random.choice(STATES))

random.shuffle(excl)

with open("provider_roster.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(roster[0].keys())); w.writeheader(); w.writerows(roster)
with open("exclusion_list.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(excl[0].keys())); w.writeheader(); w.writerows(excl)

print(f"roster: {len(roster)} providers | exclusions: {len(excl)} records")
print("planted: 6 exact, 6 fuzzy (same DOB, name spelled differently), 2 traps (same name, different DOB)")
