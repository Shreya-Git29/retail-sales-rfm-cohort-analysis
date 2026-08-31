"""
04_visualizations.py
------------------------
Generates the supporting charts a stakeholder deck / dashboard would need:
  1. Monthly net revenue trend
  2. Revenue by category
  3. Revenue and customer count by RFM segment
  4. Top 10 customers by lifetime value

These are quick matplotlib charts to sanity-check the numbers before
building the real interactive dashboard in Power BI / Tableau (see
README for that step - a static chart is not the deliverable, the
Power BI/Tableau file is).
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLEAN_PATH = "/home/claude/retail_project/data/retail_transactions_clean.csv"
RFM_PATH = "/home/claude/retail_project/outputs/rfm_segments.csv"
OUT_DIR = "/home/claude/retail_project/outputs"

df = pd.read_csv(CLEAN_PATH, parse_dates=["InvoiceDate"])
rfm = pd.read_csv(RFM_PATH)

# 1. Monthly revenue trend
monthly = df.groupby(df["InvoiceDate"].dt.to_period("M"))["LineRevenue"].sum()
fig, ax = plt.subplots(figsize=(10, 5))
monthly.plot(kind="line", marker="o", ax=ax, color="#2E86AB")
ax.set_title("Monthly Net Revenue")
ax.set_ylabel("Revenue (₹)")
ax.set_xlabel("Month")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart_monthly_revenue.png", dpi=150)
plt.close()

# 2. Revenue by category
cat_rev = df.groupby("Category")["LineRevenue"].sum().sort_values()
fig, ax = plt.subplots(figsize=(9, 5))
cat_rev.plot(kind="barh", ax=ax, color="#A23B72")
ax.set_title("Net Revenue by Category")
ax.set_xlabel("Revenue (₹)")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart_revenue_by_category.png", dpi=150)
plt.close()

# 3. Segment revenue + customer count
seg = rfm.groupby("Segment").agg(Customers=("CustomerID", "count"), Revenue=("Monetary", "sum")).sort_values("Revenue", ascending=False)
fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.bar(seg.index, seg["Revenue"], color="#F18F01")
ax1.set_ylabel("Revenue (₹)")
ax1.set_xticklabels(seg.index, rotation=35, ha="right")
ax2 = ax1.twinx()
ax2.plot(seg.index, seg["Customers"], color="#2E86AB", marker="o")
ax2.set_ylabel("Customer Count")
ax1.set_title("Revenue and Customer Count by RFM Segment")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart_segment_revenue.png", dpi=150)
plt.close()

# 4. Top 10 customers
top10 = df[df["IsGuestCheckout"] == 0].groupby("CustomerID")["LineRevenue"].sum().sort_values(ascending=False).head(10)
fig, ax = plt.subplots(figsize=(9, 5))
top10.sort_values().plot(kind="barh", ax=ax, color="#3B1F2B")
ax.set_title("Top 10 Customers by Lifetime Revenue")
ax.set_xlabel("Revenue (₹)")
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/chart_top10_customers.png", dpi=150)
plt.close()

print("Saved 4 charts to", OUT_DIR)
