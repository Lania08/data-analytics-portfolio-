"""OPPE outlier analysis (portfolio project #3).

OPPE = Ongoing Professional Practice Evaluation: the recurring review of a
practitioner's quality metrics that Joint Commission standards require.
When OPPE shows a practitioner drifting outside peer norms, the follow-up
is FPPE = a Focused evaluation of that practitioner.

This script reads 8 quarters of metrics for 40 practitioners and flags
four patterns, using peer benchmarks plus fixed review thresholds:

  CHRONIC   above the review threshold in 6+ of 8 quarters
  TREND     steadily worsening (slope >= +0.8 points/quarter on the chart
            deficiency rate) and currently above the peer median
  SPIKE     the last 2 quarters jump far above that practitioner's own
            first-6-quarter average and over the threshold
  MONITOR   average quarterly volume under 20 cases: rates swing wildly
            on tiny denominators, so these practitioners are watched,
            never flagged - the volume guard runs FIRST

Thresholds (set above peer norms of ~6% / ~1.2 / ~2.5%):
  chart_deficiency_rate > 10% | complaint_rate > 3.0 per 100 | complication_rate > 5%

Output: oppe_flags.csv - one row per flagged practitioner, with the
evidence and a recommendation (FPPE review vs. continue OPPE/monitor).
Flags are a starting point for peer review, never a conclusion by
themselves.
"""
import numpy as np
import pandas as pd

THRESHOLDS = {"chart_deficiency_rate": 10.0, "complaint_rate": 3.0, "complication_rate": 5.0}
MIN_VOLUME = 20

df = pd.read_csv("oppe_metrics.csv")
quarters = sorted(df["quarter"].unique())
peer_median = df.groupby("quarter")["chart_deficiency_rate"].median()

flags = []
for (pid, name, spec), g in df.groupby(["practitioner_id", "practitioner_name", "specialty"]):
    g = g.sort_values("quarter")
    avg_vol = g["case_volume"].mean()
    reasons, evidence = [], []

    # Volume guard first: small denominators get monitored, not flagged
    if avg_vol < MIN_VOLUME:
        flags.append({"practitioner_id": pid, "practitioner_name": name, "specialty": spec,
                      "avg_quarterly_volume": round(avg_vol, 1),
                      "flag_type": "MONITOR - low volume",
                      "evidence": f"avg {avg_vol:.0f} cases/quarter; rates not reliable at this volume",
                      "recommendation": "Continue OPPE; review rates only when volume grows"})
        continue

    # CHRONIC: over threshold in 6+ of 8 quarters, any metric
    for metric, thr in THRESHOLDS.items():
        over = (g[metric] > thr).sum()
        if over >= 6:
            reasons.append("CHRONIC")
            evidence.append(f"{metric} over {thr} in {over} of 8 quarters (latest {g[metric].iloc[-1]})")
            break

    # TREND: slope on chart deficiency rate + currently above peer median
    x = np.arange(len(g))
    slope = np.polyfit(x, g["chart_deficiency_rate"], 1)[0]
    latest_q = g["quarter"].iloc[-1]
    if slope >= 0.8 and g["chart_deficiency_rate"].iloc[-1] > peer_median[latest_q]:
        reasons.append("TREND")
        evidence.append(f"chart deficiency rising {slope:+.1f} pts/quarter, now {g['chart_deficiency_rate'].iloc[-1]}% vs peer median {peer_median[latest_q]}%")

    # SPIKE: last 2 quarters vs own first-6 average, chart deficiency rate
    first6 = g["chart_deficiency_rate"].iloc[:6].mean()
    last2 = g["chart_deficiency_rate"].iloc[6:].mean()
    if last2 - first6 >= 5 and last2 > THRESHOLDS["chart_deficiency_rate"]:
        reasons.append("SPIKE")
        evidence.append(f"chart deficiency jumped from {first6:.1f}% avg (first 6 qtrs) to {last2:.1f}% (last 2 qtrs)")

    if reasons:
        flags.append({"practitioner_id": pid, "practitioner_name": name, "specialty": spec,
                      "avg_quarterly_volume": round(avg_vol, 1),
                      "flag_type": " + ".join(reasons),
                      "evidence": "; ".join(evidence),
                      "recommendation": "FPPE review recommended"})

out = pd.DataFrame(flags).sort_values("flag_type")
out.to_csv("oppe_flags.csv", index=False)

fppe = out[out["recommendation"] == "FPPE review recommended"]
monitor = out[out["flag_type"].str.startswith("MONITOR")]
print(f"Analyzed {df['practitioner_id'].nunique()} practitioners x {len(quarters)} quarters")
print(f"  FPPE review recommended: {len(fppe)}")
for _, r in fppe.iterrows():
    print(f"    {r['practitioner_id']} {r['practitioner_name']} ({r['specialty']}) - {r['flag_type']}")
print(f"  Monitor (low volume):    {len(monitor)}")
for _, r in monitor.iterrows():
    print(f"    {r['practitioner_id']} {r['practitioner_name']} ({r['specialty']})")
print(f"  Continue routine OPPE:   {df['practitioner_id'].nunique() - len(out)}")
print("Details -> oppe_flags.csv")
