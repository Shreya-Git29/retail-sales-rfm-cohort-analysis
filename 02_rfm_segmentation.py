"""
02_rfm_segmentation.py
------------------------
Builds RFM (Recency, Frequency, Monetary) scores per customer and
assigns each customer to a named segment. This is the analytical core
of the project - the part interviewers will ask you to explain in
detail, so every step below is deliberately explicit rather than
hidden inside one clever one-liner.

Output: outputs/rfm_segments.csv (feed this into Power BI / Tableau)
"""

import pandas as pd
import numpy as np

CLEAN_PATH = "/home/claude/retail_project/data/retail_transactions_clean.csv"
OUT_PATH = "/home/claude/retail_project/outputs/rfm_segments.csv"

df = pd.read_csv(CLEAN_PATH, parse_dates=["InvoiceDate"])

# Exclude guest checkouts - can't compute customer-level RFM without an ID
df = df[df["IsGuestCheckout"] == 0].copy()

# ------------------------------------------------------------
# 1. Snapshot date = one day after the last transaction in the dataset
#    (standard convention so "Recency" is always >= 1)
# ------------------------------------------------------------
snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
print(f"Snapshot date: {snapshot_date.date()}")

# ------------------------------------------------------------
# 2. Aggregate to customer level
#    Recency  = days since last purchase
#    Frequency = number of DISTINCT invoices (not line items)
#    Monetary  = total net revenue (returns already netted via LineRevenue)
# ------------------------------------------------------------
rfm = df.groupby("CustomerID").agg(
    Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
    Frequency=("InvoiceNo", "nunique"),
    Monetary=("LineRevenue", "sum")
).reset_index()

# Drop customers with net-negative monetary value (pure returners, no
# real purchases) - document this as a deliberate business decision
before_n = len(rfm)
rfm = rfm[rfm["Monetary"] > 0]
print(f"Excluded {before_n - len(rfm)} customers with net-negative spend (returns-only)")

# ------------------------------------------------------------
# 3. Score each dimension 1-5 using quintiles.
#    Recency: LOWER is better -> reverse the labels (5 = most recent)
#    Frequency & Monetary: HIGHER is better -> normal labels
#    qcut can fail on heavily-tied data, so we use rank() first to
#    guarantee even bins - this is a common real-world gotcha, worth
#    mentioning if asked "did you hit any issues?"
# ------------------------------------------------------------
def score_quintile(series, ascending):
    ranks = series.rank(method="first", ascending=ascending)
    return pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)

rfm["R_Score"] = score_quintile(rfm["Recency"], ascending=False)   # most recent -> 5
rfm["F_Score"] = score_quintile(rfm["Frequency"], ascending=True)  # most frequent -> 5
rfm["M_Score"] = score_quintile(rfm["Monetary"], ascending=True)   # highest spend -> 5

rfm["RFM_Score"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)
rfm["RFM_Total"] = rfm[["R_Score", "F_Score", "M_Score"]].sum(axis=1)

# ------------------------------------------------------------
# 4. Map scores to business-readable segment names.
#    These rules are a simplified, defensible version of the standard
#    RFM segment map - adjust thresholds if your data's distribution differs.
# ------------------------------------------------------------
def segment_customer(row):
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif r >= 4 and f >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "Recent Customers"
    elif r == 3 and f >= 3:
        return "Potential Loyalists"
    elif r <= 2 and f >= 4 and m >= 4:
        return "At Risk (High Value)"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f <= 2 and m <= 2:
        return "Hibernating / Lost"
    else:
        return "Needs Attention"

rfm["Segment"] = rfm.apply(segment_customer, axis=1)

# ------------------------------------------------------------
# 5. Segment-level summary (this table is your headline business output)
# ------------------------------------------------------------
segment_summary = rfm.groupby("Segment").agg(
    Customers=("CustomerID", "count"),
    AvgRecency=("Recency", "mean"),
    AvgFrequency=("Frequency", "mean"),
    AvgMonetary=("Monetary", "mean"),
    TotalRevenue=("Monetary", "sum")
).round(1).sort_values("TotalRevenue", ascending=False)

segment_summary["PctOfCustomers"] = (segment_summary["Customers"] / segment_summary["Customers"].sum() * 100).round(1)
segment_summary["PctOfRevenue"] = (segment_summary["TotalRevenue"] / segment_summary["TotalRevenue"].sum() * 100).round(1)

print("\n" + "=" * 70)
print("RFM SEGMENT SUMMARY")
print("=" * 70)
print(segment_summary.to_string())

top_segment = segment_summary.index[0]
print(f"\nHeadline insight: '{top_segment}' customers are "
      f"{segment_summary.loc[top_segment, 'PctOfCustomers']}% of the customer base "
      f"but drive {segment_summary.loc[top_segment, 'PctOfRevenue']}% of revenue.")

rfm.to_csv(OUT_PATH, index=False)
segment_summary.to_csv("/home/claude/retail_project/outputs/rfm_segment_summary.csv")
print(f"\nSaved -> {OUT_PATH}")
print("Saved -> outputs/rfm_segment_summary.csv")
