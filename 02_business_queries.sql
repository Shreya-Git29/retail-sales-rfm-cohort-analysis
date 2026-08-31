-- ============================================================
-- 02_business_queries.sql
-- Answers the actual business questions a stakeholder would ask.
-- Run these against vw_retail_transactions_clean, not the raw table.
-- ============================================================

-- Q1. Monthly net revenue trend (returns netted out)
SELECT
    DATE_TRUNC('month', InvoiceDate) AS month,
    SUM(LineRevenue) AS net_revenue,
    COUNT(DISTINCT InvoiceNo) AS orders,
    SUM(LineRevenue) / COUNT(DISTINCT InvoiceNo) AS avg_order_value
FROM vw_retail_transactions_clean
GROUP BY 1
ORDER BY 1;

-- Q2. Revenue and return-rate by category (which categories are profitable
--     vs. which are quietly eating margin through returns?)
SELECT
    Category,
    SUM(CASE WHEN IsReturn = 0 THEN LineRevenue ELSE 0 END) AS gross_revenue,
    SUM(LineRevenue) AS net_revenue,
    SUM(CASE WHEN IsReturn = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS return_rate
FROM vw_retail_transactions_clean
GROUP BY Category
ORDER BY net_revenue DESC;

-- Q3. Top 10 customers by lifetime net revenue (excludes guest checkouts -
--     can't attribute lifetime value without a CustomerID)
SELECT
    CustomerID,
    Country,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    SUM(LineRevenue) AS lifetime_revenue,
    MIN(InvoiceDate) AS first_purchase,
    MAX(InvoiceDate) AS last_purchase
FROM vw_retail_transactions_clean
WHERE IsGuestCheckout = 0
GROUP BY CustomerID, Country
ORDER BY lifetime_revenue DESC
LIMIT 10;

-- Q4. Revenue by country (proper-cased, deduplicated - this is why the
--     cleaning step mattered: raw data had 'india'/'INDIA'/' India ' as
--     3 separate groups before cleaning)
SELECT Country, SUM(LineRevenue) AS net_revenue, COUNT(DISTINCT CustomerID) AS customers
FROM vw_retail_transactions_clean
WHERE IsGuestCheckout = 0
GROUP BY Country
ORDER BY net_revenue DESC;

-- Q5. RFM base query - feeds directly into the Python RFM script.
--     Recency = days since last purchase (relative to snapshot date)
--     Frequency = distinct orders
--     Monetary = total net spend
WITH snapshot AS (
    SELECT MAX(InvoiceDate) AS snapshot_date FROM vw_retail_transactions_clean
)
SELECT
    t.CustomerID,
    (SELECT snapshot_date FROM snapshot) - MAX(t.InvoiceDate) AS recency_days,
    COUNT(DISTINCT t.InvoiceNo) AS frequency,
    SUM(t.LineRevenue) AS monetary
FROM vw_retail_transactions_clean t
WHERE t.IsGuestCheckout = 0
GROUP BY t.CustomerID;
