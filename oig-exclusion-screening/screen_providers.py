"""OIG exclusion screening pipeline (portfolio project #2).

Screens a provider roster against an exclusion list in three passes:

  Pass 1 - EXACT match:  normalized first name + last name + date of birth
                         identical in both files.
  Pass 2 - RULE match:   last name + date of birth identical and the first
                         initial matches (catches records where the first
                         name was reduced to an initial).
  Pass 3 - FUZZY match:  names are not identical but very similar
                         (rapidfuzz token_set_ratio >= 80). If the date of
                         birth also matches, it is most likely the same
                         person with a misspelled name. If the DOB differs,
                         it is flagged as a name-only similarity - probably a
                         different person who shares a common name.

Every flagged provider lands in screening_results.csv for human review.
Nothing is auto-cleared or auto-confirmed: screening flags, people decide.

In production this same script runs against the real OIG LEIE download
(https://oig.hhs.gov/exclusions/downloadables.asp), refreshed monthly.
The sample exclusion_list.csv here is fictional, with planted test cases
so accuracy can be measured. See generate_data.py.
"""
import re
import pandas as pd
from rapidfuzz import fuzz

FUZZY_THRESHOLD = 85

def normalize(name: str) -> str:
    """Uppercase, drop punctuation, collapse extra spaces."""
    name = re.sub(r"[^A-Z0-9 ]", " ", str(name).upper())
    return re.sub(r"\s+", " ", name).strip()

roster = pd.read_csv("provider_roster.csv", dtype=str)
excl = pd.read_csv("exclusion_list.csv", dtype=str)

for df in (roster, excl):
    df["first_n"] = df["first_name"].map(normalize)
    df["last_n"] = df["last_name"].map(normalize)
    df["full_n"] = df["first_n"] + " " + df["last_n"]

excl_by_key = {}
for _, e in excl.iterrows():
    excl_by_key.setdefault((e["first_n"], e["last_n"], e["date_of_birth"]), e)

results = []
for _, p in roster.iterrows():
    base = {"provider_id": p["provider_id"],
            "provider_name": f'{p["first_name"]} {p["last_name"]}',
            "date_of_birth": p["date_of_birth"],
            "specialty": p["specialty"]}

    # Pass 1 - exact
    hit = excl_by_key.get((p["first_n"], p["last_n"], p["date_of_birth"]))
    if hit is not None:
        results.append({**base, "result": "EXACT MATCH - excluded, escalate",
                        "match_score": 100,
                        "matched_record": f'{hit["first_name"]} {hit["last_name"]}, DOB {hit["date_of_birth"]}',
                        "exclusion_type": hit["exclusion_type"],
                        "exclusion_date": hit["exclusion_date"]})
        continue

    # Pass 2 - last name + DOB + first initial
    rule_hit = None
    for _, e in excl.iterrows():
        if (e["last_n"] == p["last_n"] and e["date_of_birth"] == p["date_of_birth"]
                and e["first_n"][:1] == p["first_n"][:1]):
            rule_hit = e
            break
    if rule_hit is not None:
        results.append({**base, "result": "FUZZY MATCH - same person likely, review",
                        "match_score": "",
                        "matched_record": f'{rule_hit["first_name"]} {rule_hit["last_name"]}, DOB {rule_hit["date_of_birth"]}',
                        "exclusion_type": rule_hit["exclusion_type"],
                        "exclusion_date": rule_hit["exclusion_date"]})
        continue

    # Pass 3 - fuzzy name similarity. First and last names are scored
    # separately and averaged, and the last name must be at least 80%
    # similar on its own. (An earlier version scored the full name with
    # token_set_ratio and flagged 19 name-only look-alikes - anyone who
    # shared one common name token. Scoring the parts separately cut the
    # review queue to the real look-alikes and lost zero true matches.)
    best_score, best = 0, None
    for _, e in excl.iterrows():
        first_score = fuzz.ratio(p["first_n"], e["first_n"])
        # token_set_ratio for the last name so a hyphenated surname on one
        # side (CARTER vs CARTER-REYES) still scores as the same name.
        last_score = fuzz.token_set_ratio(p["last_n"], e["last_n"])
        if last_score < 80:
            continue
        score = (first_score + last_score) / 2
        if score > best_score:
            best_score, best = score, e
    if best is not None and best_score >= FUZZY_THRESHOLD:
        same_dob = best["date_of_birth"] == p["date_of_birth"]
        results.append({**base,
                        "result": ("FUZZY MATCH - same person likely, review" if same_dob
                                   else "NAME SIMILARITY ONLY - DOB differs, review"),
                        "match_score": round(best_score, 1),
                        "matched_record": f'{best["first_name"]} {best["last_name"]}, DOB {best["date_of_birth"]}',
                        "exclusion_type": best["exclusion_type"],
                        "exclusion_date": best["exclusion_date"]})

out = pd.DataFrame(results)
out.to_csv("screening_results.csv", index=False)

exact = (out["result"] == "EXACT MATCH - excluded, escalate").sum()
fuzzy = (out["result"] == "FUZZY MATCH - same person likely, review").sum()
name_only = (out["result"] == "NAME SIMILARITY ONLY - DOB differs, review").sum()
print(f"Screened {len(roster)} providers against {len(excl)} exclusion records")
print(f"  EXACT matches:            {exact}")
print(f"  FUZZY matches (same DOB): {fuzzy}  <- exact matching alone would have MISSED these")
print(f"  Name-only similarities:   {name_only}  <- flagged, but DOB differs (likely a different person)")
print(f"  Clear:                    {len(roster) - len(out)}")
print(f"Flagged for human review:   {len(out)}  -> screening_results.csv")
