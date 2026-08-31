"""
generate_data.py
-----------------
Generates a realistic, intentionally messy retail transactions dataset
so the cleaning step in this project has real work to do.

Simulates 18 months of transactions for an online + in-store retail
business selling across 6 product categories, with:
  - Duplicate rows (system double-logged some orders)
  - Missing CustomerID on some rows (guest checkouts)
  - Missing/blank product descriptions
  - Negative quantities (returns/cancellations)
  - Zero or negative unit prices (data entry errors)
  - Inconsistent country casing ("India" vs "india" vs "INDIA")
  - A few far-future / far-past invoice dates (typos)
  - Some customers with only 1 purchase, others with 30+ (realistic skew)

Output: data/retail_transactions_raw.csv
"""

import numpy as np
import pandas as pd
from faker import Faker
import random

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# ---------------------------------------------------------------
# 1. Reference data: customers, products, countries
# ---------------------------------------------------------------
N_CUSTOMERS = 850
countries = ["India", "United Kingdom", "United States", "Germany", "UAE", "Singapore"]
country_weights = [0.55, 0.15, 0.12, 0.08, 0.06, 0.04]

customers = pd.DataFrame({
    "CustomerID": [f"CUST{i:05d}" for i in range(1, N_CUSTOMERS + 1)],
    "Country": np.random.choice(countries, N_CUSTOMERS, p=country_weights),
    "SignupDate": [fake.date_between(start_date="-30m", end_date="-2m") for _ in range(N_CUSTOMERS)]
})

categories = {
    "Electronics": ["Wireless Earbuds", "Bluetooth Speaker", "Phone Case", "USB-C Cable", "Power Bank 10000mAh", "Smartwatch Band"],
    "Home & Kitchen": ["Non-Stick Pan", "LED Desk Lamp", "Cotton Bedsheet Set", "Insulated Water Bottle", "Ceramic Mug Set", "Storage Organizer"],
    "Apparel": ["Cotton T-Shirt", "Denim Jacket", "Running Shoes", "Wool Sweater", "Formal Shirt", "Yoga Pants"],
    "Beauty & Personal Care": ["Face Serum", "Herbal Shampoo", "Lip Balm Set", "Sunscreen SPF50", "Hair Dryer", "Beard Trimmer"],
    "Sports & Outdoors": ["Yoga Mat", "Resistance Bands Set", "Water Bottle Sipper", "Camping Torch", "Badminton Racket", "Cycling Gloves"],
    "Stationery & Office": ["Notebook Set", "Gel Pen Pack", "Desk Organizer", "Sticky Notes Pack", "Whiteboard Marker Set", "Backpack"]
}

products = []
pid = 10000
base_prices = {
    "Electronics": (399, 3499), "Home & Kitchen": (249, 2499), "Apparel": (299, 1999),
    "Beauty & Personal Care": (149, 1499), "Sports & Outdoors": (199, 2999), "Stationery & Office": (49, 999)
}
for cat, items in categories.items():
    lo, hi = base_prices[cat]
    for item in items:
        pid += 1
        products.append({
            "StockCode": f"P{pid}",
            "Description": item,
            "Category": cat,
            "UnitPrice": round(np.random.uniform(lo, hi), 2)
        })
products = pd.DataFrame(products)

# ---------------------------------------------------------------
# 2. Simulate transactions with realistic customer purchase skew
#    (a small % of customers drive a large share of orders - Pareto-ish)
# ---------------------------------------------------------------
purchase_counts = np.random.pareto(a=1.6, size=N_CUSTOMERS) * 2 + 1
purchase_counts = np.clip(purchase_counts.astype(int), 1, 45)

rows = []
invoice_no = 500000
start_date = pd.Timestamp("2025-01-01")
end_date = pd.Timestamp("2026-06-30")
date_range_days = (end_date - start_date).days

for idx, cust in customers.iterrows():
    n_orders = purchase_counts[idx]
    for _ in range(n_orders):
        invoice_no += 1
        order_date = start_date + pd.Timedelta(days=np.random.randint(0, date_range_days))
        n_items = np.random.randint(1, 6)
        for _ in range(n_items):
            prod = products.sample(1).iloc[0]
            qty = np.random.randint(1, 6)
            # ~3% of line items are returns (negative qty)
            if np.random.rand() < 0.03:
                qty = -qty
            rows.append({
                "InvoiceNo": invoice_no,
                "StockCode": prod["StockCode"],
                "Description": prod["Description"],
                "Category": prod["Category"],
                "Quantity": qty,
                "InvoiceDate": order_date,
                "UnitPrice": prod["UnitPrice"],
                "CustomerID": cust["CustomerID"],
                "Country": cust["Country"]
            })

df = pd.DataFrame(rows)

# ---------------------------------------------------------------
# 3. Inject realistic messiness
# ---------------------------------------------------------------
n = len(df)

# a) ~1.5% duplicate rows (system double-logged)
dupes = df.sample(frac=0.015, random_state=1)
df = pd.concat([df, dupes], ignore_index=True)

# b) ~4% missing CustomerID (guest checkout)
guest_idx = df.sample(frac=0.04, random_state=2).index
df.loc[guest_idx, "CustomerID"] = np.nan

# c) ~1% missing Description
desc_idx = df.sample(frac=0.01, random_state=3).index
df.loc[desc_idx, "Description"] = np.nan

# d) ~0.5% zero/negative UnitPrice (data entry errors)
price_idx = df.sample(frac=0.005, random_state=4).index
df.loc[price_idx, "UnitPrice"] = 0

# e) inconsistent country casing/spacing
def messy_country(c):
    r = np.random.rand()
    if r < 0.1:
        return c.upper()
    elif r < 0.2:
        return c.lower()
    elif r < 0.25:
        return f" {c} "
    return c
df["Country"] = df["Country"].apply(messy_country)

# f) a handful of typo dates (future/past outliers) - ~0.2%
typo_idx = df.sample(frac=0.002, random_state=5).index
df.loc[typo_idx, "InvoiceDate"] = pd.Timestamp("2029-01-01")

# g) shuffle and finalize column order
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"]).dt.strftime("%Y-%m-%d")
df = df[["InvoiceNo", "StockCode", "Description", "Category", "Quantity",
         "InvoiceDate", "UnitPrice", "CustomerID", "Country"]]
df = df.sample(frac=1, random_state=6).reset_index(drop=True)

out_path = "/home/claude/retail_project/data/retail_transactions_raw.csv"
df.to_csv(out_path, index=False)
customers.to_csv("/home/claude/retail_project/data/customers_reference.csv", index=False)
products.to_csv("/home/claude/retail_project/data/products_reference.csv", index=False)

print(f"Generated {len(df):,} transaction line items")
print(f"Unique invoices: {df['InvoiceNo'].nunique():,}")
print(f"Unique customers referenced: {df['CustomerID'].nunique():,}")
print(f"Missing CustomerID rows: {df['CustomerID'].isna().sum()}")
print(f"Missing Description rows: {df['Description'].isna().sum()}")
print(f"Duplicate rows (exact): {df.duplicated().sum()}")
print(f"Saved to {out_path}")
