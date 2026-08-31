# Retail Sales & Customer Segmentation — RFM + Cohort Analysis

An end-to-end retail analytics project built using **Python, SQL, and data visualization** to analyze customer behavior, sales performance, returns, and customer retention.

The project starts with a deliberately messy retail transaction dataset and takes it through **data quality auditing, cleaning, business analysis, RFM customer segmentation, cohort retention analysis, and visualization**.

---

## 📌 Business Problem

> **Which customers should we prioritize for retention, and is customer loyalty improving or declining over time?**

Every analysis in this project is designed to answer this business question.

The project focuses on turning raw transactional data into actionable insights that can support customer retention and revenue decisions.

---

## 🎯 Project Objectives

- Audit and identify data quality issues
- Clean and standardize raw retail transaction data
- Analyze revenue and order trends
- Analyze product/category returns
- Identify high-value customers
- Segment customers using **RFM analysis**
- Analyze customer retention using **cohort analysis**
- Generate business-focused visualizations
- Prepare analytical datasets for Power BI/Tableau dashboards

---

## 🗂️ Project Structure

```text
retail_project/
│
├── data/
│   ├── generate_data.py
│   ├── retail_transactions_raw.csv
│   ├── retail_transactions_clean.csv
│   ├── customers_reference.csv
│   └── products_reference.csv
│
├── sql/
│   ├── 01_schema_and_cleaning.sql
│   └── 02_business_queries.sql
│
├── python/
│   ├── 01_data_cleaning.py
│   ├── 02_rfm_segmentation.py
│   ├── 03_cohort_analysis.py
│   └── 04_visualizations.py
│
├── outputs/
│   ├── rfm_segments.csv
│   ├── rfm_segment_summary.csv
│   ├── cohort_retention_matrix.csv
│   ├── cohort_retention_heatmap.png
│   └── chart_*.png
│
└── README.md
