from build import *
from etl.anims import *

SECTION = dict(level='intermediate', title='Transformation', questions=[

# ------------------------------------------------------------------ 13
Q('What are the common types of transformations in ETL?', 'Common Transformations', minutes=7, cards=[
    definition(
        table(['Transformation', 'Purpose', 'Example'], [
            ['Cleansing', 'Fix or remove invalid data', 'Trim spaces, fix casing, nullify "N/A"'],
            ['Standardisation', 'Consistent formats and codes', 'Dates to ISO, "MH"/"Maharashtra" → "MH", phone to +91 format'],
            ['Type conversion', 'Correct data types', '"1,200.50" → DECIMAL 1200.50'],
            ['Deduplication', 'Remove repeated records', 'Keep latest version per key'],
            ['Filtering', 'Drop irrelevant rows', 'Exclude test orders'],
            ['Joining / enrichment', 'Combine sources, add attributes', 'Add region from a pincode lookup'],
            ['Derivation', 'Compute new columns', 'revenue = qty × price; age from DOB'],
            ['Aggregation', 'Summarise', 'Daily sales by city'],
            ['Pivot / unpivot', 'Reshape rows ↔ columns', 'Monthly columns → month rows'],
            ['Splitting / merging columns', 'Restructure fields', 'Full name → first, last'],
            ['Surrogate key assignment', 'Warehouse keys', 'Map customer_id → customer_key'],
            ['Masking / hashing', 'Protect sensitive data', 'Hash Aadhaar/PAN, mask phone'],
        ]),
        tags('Cleansing', 'Standardisation', 'Enrichment', 'Aggregation', 'Derivation', 'Pivot'),
    ),
    example(
        sqlrun("""
CREATE TABLE raw_students (id INT, full_name VARCHAR(60), state VARCHAR(30), dob VARCHAR(12), fee VARCHAR(12));
INSERT INTO raw_students VALUES
 (1, '  asha  patil', 'maharashtra', '05/01/2001', '95,000'),
 (2, 'ROHIT SHAH',    'MH',          '2000-12-17', '90000'),
 (3, 'meera iyer',    'Tamil Nadu',  'unknown',    'NA');

CREATE TABLE state_codes (state_name VARCHAR(30), code CHAR(2));
INSERT INTO state_codes VALUES ('maharashtra','MH'), ('mh','MH'), ('tamil nadu','TN');

WITH cleaned AS (
  SELECT id, state, dob, fee,
         LOWER(TRIM(REGEXP_REPLACE(full_name, ' +', ' '))) AS nm      -- trim + collapse spaces
  FROM raw_students
)
SELECT c.id,
       CONCAT(UPPER(LEFT(SUBSTRING_INDEX(c.nm, ' ', 1), 1)),  SUBSTRING(SUBSTRING_INDEX(c.nm, ' ', 1), 2))  AS first_name,
       CONCAT(UPPER(LEFT(SUBSTRING_INDEX(c.nm, ' ', -1), 1)), SUBSTRING(SUBSTRING_INDEX(c.nm, ' ', -1), 2)) AS last_name,
       sc.code                                                                      AS state_code,
       COALESCE(STR_TO_DATE(c.dob, '%Y-%m-%d'), STR_TO_DATE(c.dob, '%d/%m/%Y'))   AS dob,
       CASE WHEN c.fee REGEXP '^[0-9,]+$' THEN CAST(REPLACE(c.fee, ',', '') AS UNSIGNED) END AS fee
FROM cleaned c
LEFT JOIN state_codes sc ON sc.state_name = LOWER(TRIM(c.state));
"""),
        title='Example: Several Transformations in One Query'),
    crossq(
        ('Where should business logic live — in the ETL tool, in SQL, or in Python?',
         'Wherever it is most testable, versioned and visible to the team. Modern practice keeps transformations as code '
         '(SQL models in dbt or PySpark modules) in Git, with tests and reviews, rather than hidden inside GUI tool mappings.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do you handle data cleansing — nulls, blanks, invalid values and outliers?', 'Data Cleansing', minutes=7, cards=[
    definition(
        defbox('<strong>Data cleansing</strong> detects and corrects (or removes) inaccurate, incomplete, inconsistent or '
               'invalid records. The goal is not to make data "look nice" but to make it <strong>trustworthy</strong> '
               'while keeping a record of what was changed.'),
        table(['Problem', 'Typical treatment'], [
            ['Placeholder values ("NA", "null", "-", "")', 'Convert to real NULL'],
            ['Missing mandatory field', 'Reject / quarantine the row'],
            ['Missing optional field', 'Default ("UNKNOWN"), derive, or keep NULL'],
            ['Leading/trailing/multiple spaces, casing', 'TRIM, collapse spaces, standard case'],
            ['Invalid format (email, phone, PAN)', 'Validate with regex; quarantine or nullify'],
            ['Out-of-range values (age 250, negative qty)', 'Reject or flag; never silently "fix"'],
            ['Inconsistent codes', 'Map through a reference table'],
            ['Outliers', 'Flag for review; business decides whether they are errors'],
        ]),
        tags('Data Cleansing', 'NULL Handling', 'Validation', 'Quarantine', 'Standardisation'),
    ),
    example(
        pyrun("""
import pandas as pd
import numpy as np

df = pd.DataFrame({
    "id":    [1, 2, 3, 4, 5],
    "name":  ["  Asha ", "rohit", "NA", "", "Zoya"],
    "email": ["asha@x.com", "rohit@x", "meera@x.com", None, "zoya@x.com"],
    "age":   [24, 23, -1, 22, 250],
})

df["name"] = df["name"].str.strip().replace({"NA": np.nan, "": np.nan}).str.title()
df["email_valid"] = df["email"].str.match(r"^[\\w.+-]+@[\\w-]+\\.[\\w.]+$", na=False)
df["age_valid"] = df["age"].between(15, 80)

good = df[df["email_valid"] & df["age_valid"] & df["name"].notna()]
bad = df.drop(good.index)

print("clean rows:\\n", good[["id", "name", "email", "age"]].to_string(index=False))
print("quarantined ids:", bad["id"].tolist())
"""),
        title='Example: Clean, Validate, Quarantine (pandas)'),
    crossq(
        ('Should you impute missing values in ETL?',
         'Generally no — the warehouse should reflect reality. Use explicit defaults only where the business agrees (e.g. "UNKNOWN" region). Imputation for ML belongs in the feature pipeline, not the core warehouse.'),
        ('How do you treat NULLs in joins and aggregations?',
         'NULL never equals NULL, so NULL keys do not join — map them to an "Unknown" dimension member (key −1). COUNT(col) and AVG ignore NULLs; COUNT(*) does not. Be explicit with COALESCE.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you remove duplicates in a pipeline?', 'Deduplication Strategies', minutes=7, cards=[
    definition(
        defbox('Duplicates arrive from retries, overlapping extraction windows, at-least-once delivery, files sent twice, or '
               'genuine repeats in the source. The right method depends on what "duplicate" means: '
               '<strong>exact copy</strong>, <strong>same business key</strong>, or <strong>same key with a newer version</strong>.'),
        table(['Type', 'Method'], [
            ['Exact duplicate rows', '<code>SELECT DISTINCT</code> / <code>dropDuplicates()</code>'],
            ['Same key, keep latest', '<code>ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC) = 1</code>'],
            ['Same file loaded twice', 'Track processed file names / checksums in a control table'],
            ['Same event delivered twice', 'Unique event_id + MERGE / insert-if-not-exists'],
            ['Fuzzy duplicates ("Asha Patil" vs "A. Patil")', 'Matching rules / record-linkage libraries — a data-quality project, not plain ETL'],
        ]),
        tags('Deduplication', 'ROW_NUMBER', 'DISTINCT', 'Idempotency', 'Business Key'),
    ),
    dedup_rownumber(),
    example(
        sqlrun("""
CREATE TABLE stg_customers (customer_id INT, city VARCHAR(20), updated_at DATETIME, batch_id INT);
INSERT INTO stg_customers VALUES
 (101, 'Pune',   '2026-10-01 10:00:00', 1),
 (101, 'Mumbai', '2026-10-05 09:30:00', 2),
 (101, 'Mumbai', '2026-10-05 09:30:00', 2),     -- exact duplicate (retry)
 (102, 'Delhi',  '2026-10-02 11:00:00', 1);

-- Keep only the latest version of each customer
SELECT customer_id, city, updated_at
FROM (
  SELECT s.*,
         ROW_NUMBER() OVER (PARTITION BY customer_id
                            ORDER BY updated_at DESC, batch_id DESC) AS rn
  FROM stg_customers s
) t
WHERE rn = 1
ORDER BY customer_id;
"""),
        py("""
from pyspark.sql import Window, functions as F

w = Window.partitionBy("customer_id").orderBy(F.col("updated_at").desc(), F.col("batch_id").desc())
latest = (df.withColumn("rn", F.row_number().over(w))
            .filter("rn = 1")
            .drop("rn"))

exact_dedup = df.dropDuplicates()                       # all columns
key_dedup   = df.dropDuplicates(["customer_id"])        # arbitrary row per key — not deterministic!
""", 'PySpark equivalent'),
        title='Example'),
    crossq(
        ('Why is dropDuplicates(["key"]) risky?',
         'Spark keeps an arbitrary row per key — results can change between runs. Use a window with an explicit ORDER BY to decide which row wins.'),
        ('How do you dedupe in a streaming job?',
         'Keep state of seen event ids for a bounded time: <code>withWatermark("event_time", "1 hour").dropDuplicates(["event_id", "event_time"])</code> in Spark Structured Streaming.'),
    ),
]),

# ------------------------------------------------------------------ 16
Q('What are lookups and how are surrogate keys assigned during a load?', 'Lookups & Surrogate Keys', minutes=7, cards=[
    definition(
        defbox('A <strong>lookup</strong> enriches or validates incoming rows by matching them against a reference table — '
               'e.g. finding the <code>customer_key</code> for a <code>customer_id</code> while loading a fact table.',
               'A <strong>surrogate key</strong> is a warehouse-generated integer key for dimension rows, independent of the '
               'source system\'s business key. Fact tables store the surrogate key, not the business key.'),
        tags('Lookup', 'Surrogate Key', 'Business Key', 'Unknown Member', 'Key Mapping'),
    ),
    example(
        sqlrun("""
CREATE TABLE dim_customer (
  customer_key INT AUTO_INCREMENT PRIMARY KEY,     -- surrogate key
  customer_id  VARCHAR(10) UNIQUE,                 -- business key from source
  name VARCHAR(30)
);
INSERT INTO dim_customer (customer_key, customer_id, name) VALUES (-1, 'UNKNOWN', 'Unknown customer');
INSERT INTO dim_customer (customer_id, name) VALUES ('C101', 'Asha'), ('C102', 'Rohit');

CREATE TABLE stg_sales (order_id INT, customer_id VARCHAR(10), amount DECIMAL(10,2));
INSERT INTO stg_sales VALUES (1, 'C101', 500), (2, 'C102', 250), (3, 'C999', 75);

CREATE TABLE fact_sales (order_id INT, customer_key INT, amount DECIMAL(10,2));

-- Lookup: business key -> surrogate key; unmatched rows go to the Unknown member (-1)
INSERT INTO fact_sales
SELECT s.order_id, COALESCE(d.customer_key, -1), s.amount
FROM stg_sales s
LEFT JOIN dim_customer d ON d.customer_id = s.customer_id;

SELECT f.order_id, f.customer_key, d.customer_id, f.amount
FROM fact_sales f JOIN dim_customer d ON d.customer_key = f.customer_key
ORDER BY f.order_id;
"""),
        title='Example: Fact Load with Key Lookup'),
    explanation(
        p('<strong>Ways to generate surrogate keys:</strong> database identity / AUTO_INCREMENT, sequences, '
          '<code>ROW_NUMBER() + max(existing key)</code> in Spark, or a <strong>deterministic hash</strong> of the business '
          'key (e.g. <code>md5(source || customer_id)</code>, common in dbt and distributed systems because it needs no coordination).'),
        title='Generating Keys'),
    crossq(
        ('Why load unmatched facts with key −1 instead of dropping them?',
         'Dropping silently loses revenue from reports. Loading to an "Unknown" member keeps totals correct and makes the problem visible; a later job can re-point them when the dimension arrives (see late-arriving dimensions).'),
        ('Hash keys vs integer keys?',
         'Hash keys can be computed anywhere in parallel and are stable across reloads, but are larger (slower joins) and have a tiny collision risk. Integer keys are compact but need a central generator.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('How do you handle late-arriving data and late-arriving dimensions?', 'Late-Arriving Data', minutes=8, cards=[
    definition(
        defbox('<strong>Late-arriving facts</strong>: events that reach the pipeline after the period they belong to has '
               'already been processed (a mobile app syncs yesterday\'s orders today).',
               '<strong>Late-arriving dimensions (early-arriving facts)</strong>: a fact refers to a dimension member that does '
               'not exist yet in the warehouse (an order for a customer whose record arrives tomorrow).'),
        tags('Late-arriving Facts', 'Late-arriving Dimensions', 'Inferred Member', 'Event Time', 'Reprocessing Window'),
    ),
    explanation(
        table(['Problem', 'Strategies'], [
            ['Late facts', 'Partition by <strong>event date</strong>, not load date; re-process a rolling window (e.g. last 3 days) every run; use MERGE so re-processing is safe; in streaming, use watermarks and allowed lateness'],
            ['Late dimensions', '(1) Load the fact with the Unknown key (−1) and fix it later; (2) create an <strong>inferred member</strong> — a placeholder dimension row with only the business key, updated in place when the real record arrives; (3) hold the fact in a pending table and retry'],
        ]),
    ),
    example(
        sqlrun("""
CREATE TABLE dim_customer (customer_key INT AUTO_INCREMENT PRIMARY KEY, customer_id VARCHAR(10) UNIQUE,
                           name VARCHAR(30), is_inferred TINYINT DEFAULT 0);
INSERT INTO dim_customer (customer_id, name) VALUES ('C101', 'Asha');

CREATE TABLE stg_sales (order_id INT, customer_id VARCHAR(10), amount INT);
INSERT INTO stg_sales VALUES (1, 'C101', 500), (2, 'C205', 300);       -- C205 not known yet

-- 1) Create inferred members for unknown business keys
INSERT INTO dim_customer (customer_id, name, is_inferred)
SELECT DISTINCT s.customer_id, 'Pending', 1
FROM stg_sales s LEFT JOIN dim_customer d ON d.customer_id = s.customer_id
WHERE d.customer_id IS NULL;

SELECT * FROM dim_customer;

-- 2) Next day the real customer record arrives: update the inferred row in place
UPDATE dim_customer SET name = 'Kiran', is_inferred = 0
WHERE customer_id = 'C205' AND is_inferred = 1;

SELECT * FROM dim_customer;
"""),
        title='Example: Inferred Member'),
    crossq(
        ('Why does partitioning by event date matter for late data?',
         'If you partition by load date, a late event lands in today\'s partition and yesterday\'s report never includes it. '
         'With event-date partitions, you overwrite/merge the affected past partitions and reports become correct.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What is schema evolution / schema drift and how do you handle it?', 'Schema Evolution & Drift', minutes=7, cards=[
    definition(
        defbox('<strong>Schema drift</strong> is an unplanned change in the structure of incoming data — a new column, '
               'a removed column, a renamed field, a changed data type. <strong>Schema evolution</strong> is the target\'s '
               'ability to accept such changes in a controlled way.'),
        table(['Change', 'Risk', 'Typical handling'], [
            ['New column added', 'Low', 'Auto-add as nullable (Delta <code>mergeSchema</code>), or ignore until modelled'],
            ['Column removed', 'Medium', 'Keep target column, fill NULL; alert'],
            ['Column renamed', 'High', 'Looks like remove + add — needs a mapping'],
            ['Type widened (INT → BIGINT)', 'Low', 'Allow safe widening'],
            ['Type changed incompatibly (INT → STRING)', 'High', 'Fail fast; quarantine; human decision'],
            ['Nested JSON structure changed', 'Medium', 'Land raw JSON; parse with tolerant schema'],
        ]),
        tags('Schema Drift', 'Schema Evolution', 'Data Contract', 'mergeSchema', 'Avro', 'Schema Registry'),
    ),
    example(
        pyrun("""
EXPECTED = {"order_id": int, "amount": float, "city": str}

def check_schema(record: dict):
    issues = []
    missing = EXPECTED.keys() - record.keys()
    extra = record.keys() - EXPECTED.keys()
    if missing: issues.append(f"missing columns: {sorted(missing)}")
    if extra:   issues.append(f"new columns: {sorted(extra)}")
    for col, typ in EXPECTED.items():
        if col in record and record[col] is not None and not isinstance(record[col], typ):
            issues.append(f"{col}: expected {typ.__name__}, got {type(record[col]).__name__}")
    return issues

batch = [
    {"order_id": 1, "amount": 99.5, "city": "Pune"},
    {"order_id": 2, "amount": "120", "city": "Delhi"},                 # type changed
    {"order_id": 3, "amount": 10.0, "city": "Agra", "coupon": "D10"},  # new column
]
for r in batch:
    print(r["order_id"], check_schema(r) or "OK")
"""),
        py("""
# Delta Lake: allow new columns to be added automatically on write
(df.write.format("delta")
   .mode("append")
   .option("mergeSchema", "true")
   .save("s3://lake/silver/orders"))
""", 'Delta Lake schema evolution'),
        title='Example'),
    crossq(
        ('What is a data contract?',
         'An agreed, versioned specification between the producing team and data consumers — schema, types, semantics, SLAs, '
         'ownership. Breaking changes require a new version, so drift is caught at the source rather than in a broken dashboard.'),
        ('How do Avro and a Schema Registry help?',
         'Every Kafka message is written with a registered schema version; the registry enforces compatibility rules (backward/forward) so producers cannot publish breaking changes.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('How do you handle data type conversions and time zones in ETL?', 'Type & Timezone Normalisation', minutes=6, cards=[
    definition(
        defbox('Sources rarely agree on formats: dates as <code>08/10/2026</code>, <code>2026-10-08</code> or epoch '
               'milliseconds; amounts as strings with commas; booleans as Y/N, 1/0, true/false; timestamps in local time '
               'with no zone. Normalise everything into <strong>one canonical form</strong> early in the pipeline.'),
        table(['Data', 'Canonical form'], [
            ['Timestamps', 'UTC, stored as TIMESTAMP; keep original zone in a column if needed'],
            ['Dates', 'ISO 8601 DATE (YYYY-MM-DD)'],
            ['Money', 'DECIMAL with fixed scale + currency code column'],
            ['Booleans', 'TRUE/FALSE'],
            ['Codes', 'Mapped via reference tables'],
            ['Text', 'UTF-8, trimmed'],
        ]),
        tags('Type Casting', 'UTC', 'ISO 8601', 'Epoch', 'DECIMAL', 'Normalisation'),
    ),
    example(
        pyrun("""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal

IST = ZoneInfo("Asia/Kolkata")

def to_utc(value):
    if isinstance(value, (int, float)):                        # epoch milliseconds
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            local = datetime.strptime(value, fmt).replace(tzinfo=IST)   # source sends IST
            return local.astimezone(timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"unparseable timestamp: {value!r}")

for v in ["2026-10-08 22:45:00", "08/10/2026 22:45", 1791479700000]:
    print(f"{str(v):<22} -> {to_utc(v).isoformat()}")

to_bool = {"y": True, "yes": True, "1": True, "true": True, "n": False, "no": False, "0": False, "false": False}
print([to_bool[x.strip().lower()] for x in ["Y", "no", "1", "TRUE"]])
print(Decimal("1,23,456.70".replace(",", "")))
"""),
        title='Example'),
    crossq(
        ('Why store timestamps in UTC?',
         'UTC has no daylight-saving jumps or ambiguous hours, makes data from different regions comparable, and avoids errors when servers in different zones process the same data. Convert to IST only in reports.'),
        ('What goes wrong with implicit type conversion?',
         'Leading zeros are lost ("00123" → 123 for pincodes or ids), large ids lose precision as floats, "1/2/2026" is read as Jan 2 or Feb 1 depending on locale. Always define schemas explicitly instead of inferring them.'),
    ),
]),

])
