"""
01_data_cleaning.py
--------------------
Loads the raw messy dataset, audits data quality, applies documented
cleaning rules, and saves a clean dataset for downstream analysis.

This mirrors sql/01_schema_and_cleaning.sql - in a real project you'd
pick ONE of SQL or Python for the actual cleaning (not both), but doing
it here in pandas keeps this reference project runnable end-to-end
without a database. Use the SQL file to show you can do this layer in
SQL too.
"""

import pandas as pd
import numpy as np

RAW_PATH = "/home/claude/retail_project/data/retail_transactions_raw.csv"
CLEAN_PATH = "/home/claude/retail_project/data/retail_transactions_clean.csv"

df = pd.read_csv(RAW_PATH, parse_dates=["InvoiceDate"])

print("=" * 60)
print("DATA QUALITY AUDIT (before cleaning)")
print("=" * 60)
print(f"Total rows:                 {len(df):,}")
print(f"Exact duplicate rows:       {df.duplicated().sum():,}")
print(f"Missing CustomerID:         {df['CustomerID'].isna().sum():,}")
print(f"Missing Description:        {df['Description'].isna().sum():,}")
print(f"UnitPrice <= 0:             {(df['UnitPrice'] <= 0).sum():,}")
print(f"Negative Quantity (returns):{(df['Quantity'] < 0).sum():,}")
print(f"Future-dated rows:          {(df['InvoiceDate'] > pd.Timestamp.today()).sum():,}")
print(f"Distinct raw Country values:{df['Country'].nunique()} -> {sorted(df['Country'].unique())[:6]}...")

# ------------------------------------------------------------
# Cleaning rules (same logic/reasoning as the SQL view - keep these
# two files in sync, and explain these decisions in your README)
# ------------------------------------------------------------
before = len(df)

# 1. Drop exact duplicate rows
df = df.drop_duplicates()

# 2. Standardize Country: trim whitespace, title case
df["Country"] = df["Country"].str.strip().str.title()

# 3. Flag guest checkouts instead of dropping (still valid revenue,
#    just can't be attributed to a customer for RFM/cohort)
df["IsGuestCheckout"] = df["CustomerID"].isna().astype(int)

# 4. Drop rows with missing Description (can't categorize/report on these)
df = df[df["Description"].notna()]

# 5. Drop invalid prices (data entry errors, not real transactions)
df = df[df["UnitPrice"] > 0]

# 6. Drop future-dated rows (typos - keep threshold at "today")
df = df[df["InvoiceDate"] <= pd.Timestamp.today()]

# 7. Flag returns instead of dropping (needed for accurate net revenue)
df["IsReturn"] = (df["Quantity"] < 0).astype(int)

# 8. Derived column used everywhere downstream
df["LineRevenue"] = (df["Quantity"] * df["UnitPrice"]).round(2)

after = len(df)

print("\n" + "=" * 60)
print("CLEANING SUMMARY")
print("=" * 60)
print(f"Rows before cleaning: {before:,}")
print(f"Rows after cleaning:  {after:,}")
print(f"Rows removed:         {before - after:,} ({(before-after)/before:.1%})")
print(f"Guest checkout rows retained (flagged, excluded from RFM): "
      f"{df['IsGuestCheckout'].sum():,}")
print(f"Return line items retained (flagged): {df['IsReturn'].sum():,}")
print(f"Net revenue in clean data: {df['LineRevenue'].sum():,.2f}")

df.to_csv(CLEAN_PATH, index=False)
print(f"\nSaved clean dataset -> {CLEAN_PATH}")
