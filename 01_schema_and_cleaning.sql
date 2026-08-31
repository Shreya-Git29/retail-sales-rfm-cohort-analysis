-- ============================================================
-- 01_schema_and_cleaning.sql
-- Retail Sales & Customer Segmentation Project
-- Purpose: define raw table, then build a CLEAN view on top of it.
-- Written for MySQL/PostgreSQL syntax (minor tweaks needed for SQL Server).
-- ============================================================

-- ---------------------------------------------------------
-- 1. Raw table (mirrors the messy CSV exactly - no fixes yet)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS retail_transactions_raw (
    InvoiceNo     VARCHAR(20),
    StockCode     VARCHAR(20),
    Description   VARCHAR(255),
    Category      VARCHAR(100),
    Quantity      INT,
    InvoiceDate   DATE,
    UnitPrice     DECIMAL(10,2),
    CustomerID    VARCHAR(20),
    Country       VARCHAR(100)
);

-- Load data (adjust path/method to your SQL client, e.g. LOAD DATA INFILE,
-- \copy in psql, or import wizard)
-- LOAD DATA INFILE 'retail_transactions_raw.csv' INTO TABLE retail_transactions_raw ...

-- ---------------------------------------------------------
-- 2. Data quality audit BEFORE cleaning (document this in your README/report -
--    recruiters and interviewers will ask "how did you know it needed cleaning?")
-- ---------------------------------------------------------
SELECT COUNT(*) AS total_rows FROM retail_transactions_raw;

SELECT COUNT(*) AS exact_duplicate_rows
FROM (
    SELECT InvoiceNo, StockCode, Quantity, InvoiceDate, CustomerID, COUNT(*) c
    FROM retail_transactions_raw
    GROUP BY InvoiceNo, StockCode, Quantity, InvoiceDate, CustomerID
    HAVING COUNT(*) > 1
) dupes;

SELECT
    SUM(CASE WHEN CustomerID IS NULL OR CustomerID = '' THEN 1 ELSE 0 END) AS missing_customer_id,
    SUM(CASE WHEN Description IS NULL OR Description = '' THEN 1 ELSE 0 END) AS missing_description,
    SUM(CASE WHEN UnitPrice <= 0 THEN 1 ELSE 0 END) AS invalid_price,
    SUM(CASE WHEN Quantity < 0 THEN 1 ELSE 0 END) AS return_line_items,
    SUM(CASE WHEN InvoiceDate > CURRENT_DATE THEN 1 ELSE 0 END) AS future_dated_rows
FROM retail_transactions_raw;

SELECT DISTINCT Country FROM retail_transactions_raw ORDER BY Country;
-- -> reveals casing/whitespace inconsistencies like 'india', 'INDIA', ' India '

-- ---------------------------------------------------------
-- 3. Cleaned view - this is what every downstream query/report should use
--    Cleaning decisions (document these explicitly - this is what
--    interviewers actually probe on):
--      a) Drop exact duplicate rows
--      b) Keep guest orders (missing CustomerID) but exclude them from
--         customer-level analysis (RFM/cohort) - they can't be attributed
--      c) Drop rows with missing Description (can't categorize the sale)
--      d) Drop rows with UnitPrice <= 0 (data entry errors, not real sales)
--      e) Keep negative-quantity rows (returns) but flag them - needed for
--         accurate net revenue, excluded from "units sold" metrics
--      f) Standardize Country text: trim + proper case
--      g) Drop invoices dated beyond current date (typos)
-- ---------------------------------------------------------
CREATE OR REPLACE VIEW vw_retail_transactions_clean AS
SELECT
    InvoiceNo,
    StockCode,
    TRIM(Description)              AS Description,
    Category,
    Quantity,
    CASE WHEN Quantity < 0 THEN 1 ELSE 0 END AS IsReturn,
    InvoiceDate,
    UnitPrice,
    ROUND(Quantity * UnitPrice, 2) AS LineRevenue,
    CustomerID,
    CASE WHEN CustomerID IS NULL OR CustomerID = '' THEN 1 ELSE 0 END AS IsGuestCheckout,
    INITCAP(TRIM(Country))         AS Country      -- Postgres: INITCAP. MySQL: use CONCAT(UPPER(LEFT(x,1)),LOWER(SUBSTRING(x,2)))
FROM retail_transactions_raw
WHERE
    Description IS NOT NULL AND Description <> ''
    AND UnitPrice > 0
    AND InvoiceDate <= CURRENT_DATE
    -- remove exact duplicates, keeping one copy of each
    AND (InvoiceNo, StockCode, Quantity, InvoiceDate, COALESCE(CustomerID,'GUEST')) IN (
        SELECT InvoiceNo, StockCode, Quantity, InvoiceDate, COALESCE(CustomerID,'GUEST')
        FROM retail_transactions_raw
        GROUP BY InvoiceNo, StockCode, Quantity, InvoiceDate, COALESCE(CustomerID,'GUEST')
    );

-- Row count check after cleaning - always report before vs. after in your README
SELECT COUNT(*) AS clean_row_count FROM vw_retail_transactions_clean;
