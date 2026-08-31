"""
03_cohort_analysis.py
------------------------
Builds a monthly acquisition-cohort retention table:
"Of customers who made their FIRST purchase in month X, what % were
still buying in month X+1, X+2, ... X+6?"

This answers a different question than RFM (which is a snapshot).
Cohort analysis shows retention TRENDS over time, which is what
"support targeted retention decisions" in a resume bullet should
actually be backed by.

Output: outputs/cohort_retention_matrix.csv + a heatmap PNG
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLEAN_PATH = "/home/claude/retail_project/data/retail_transactions_clean.csv"
OUT_CSV = "/home/claude/retail_project/outputs/cohort_retention_matrix.csv"
OUT_PNG = "/home/claude/retail_project/outputs/cohort_retention_heatmap.png"

df = pd.read_csv(CLEAN_PATH, parse_dates=["InvoiceDate"])
df = df[df["IsGuestCheckout"] == 0].copy()

# ------------------------------------------------------------
# 1. Assign each customer a Cohort = month of their FIRST purchase
# ------------------------------------------------------------
df["OrderMonth"] = df["InvoiceDate"].dt.to_period("M")
first_purchase = df.groupby("CustomerID")["OrderMonth"].min().rename("CohortMonth")
df = df.merge(first_purchase, on="CustomerID")

# ------------------------------------------------------------
# 2. CohortIndex = number of months between the order and the
#    customer's first purchase (0 = acquisition month, 1 = month after, ...)
# ------------------------------------------------------------
df["CohortIndex"] = (
    (df["OrderMonth"].dt.year - df["CohortMonth"].dt.year) * 12
    + (df["OrderMonth"].dt.month - df["CohortMonth"].dt.month)
)

# ------------------------------------------------------------
# 3. Count distinct active customers per (CohortMonth, CohortIndex)
# ------------------------------------------------------------
cohort_data = (
    df.groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
    .nunique()
    .reset_index()
)
cohort_counts = cohort_data.pivot(index="CohortMonth", columns="CohortIndex", values="CustomerID")

cohort_sizes = cohort_counts.iloc[:, 0]
retention = cohort_counts.divide(cohort_sizes, axis=0).round(3)

# Keep only cohorts with at least 4 months of possible history and
# only the first 6 months of index, so the matrix is clean to read
retention_display = retention.iloc[:, :7]

print("=" * 70)
print("COHORT RETENTION MATRIX (% of cohort still active, month 0-6)")
print("=" * 70)
print((retention_display * 100).round(1).to_string())

avg_m1_retention = retention_display[1].mean() * 100 if 1 in retention_display.columns else np.nan
avg_m3_retention = retention_display[3].mean() * 100 if 3 in retention_display.columns else np.nan
print(f"\nAverage Month-1 retention across cohorts: {avg_m1_retention:.1f}%")
print(f"Average Month-3 retention across cohorts: {avg_m3_retention:.1f}%")

retention_display.to_csv(OUT_CSV)
print(f"\nSaved -> {OUT_CSV}")

# ------------------------------------------------------------
# 4. Heatmap visualization
# ------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
im = ax.imshow(retention_display.values, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")

ax.set_xticks(range(retention_display.shape[1]))
ax.set_xticklabels(retention_display.columns)
ax.set_yticks(range(retention_display.shape[0]))
ax.set_yticklabels([str(p) for p in retention_display.index])
ax.set_xlabel("Months Since First Purchase")
ax.set_ylabel("Acquisition Cohort")
ax.set_title("Customer Retention by Acquisition Cohort")

for i in range(retention_display.shape[0]):
    for j in range(retention_display.shape[1]):
        val = retention_display.values[i, j]
        if not np.isnan(val):
            ax.text(j, i, f"{val*100:.0f}%", ha="center", va="center",
                     color="white" if val > 0.5 else "black", fontsize=8)

plt.colorbar(im, ax=ax, label="Retention Rate")
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=150)
print(f"Saved -> {OUT_PNG}")
