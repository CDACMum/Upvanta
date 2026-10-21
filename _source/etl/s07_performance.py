from build import *
from etl.anims import *

SECTION = dict(level='expert', title='Performance & Operations', questions=[

# ------------------------------------------------------------------ 40
Q('An ETL job that took 20 minutes now takes 3 hours. How do you troubleshoot it?', 'Tuning a Slow ETL Job', minutes=8, cards=[
    definition(
        defbox('Performance problems are diagnosed, not guessed. Start by finding <strong>which step</strong> got slower and '
               '<strong>what changed</strong> (data volume, data shape, code, infrastructure, source), then fix the bottleneck.'),
        tags('Performance Tuning', 'Bottleneck', 'Spark UI', 'EXPLAIN', 'Data Volume', 'Root Cause'),
    ),
    explanation(
        table(['Step', 'What to look at'], [
            ['1. Locate', 'Which task/stage is slow? Compare task durations in the orchestrator and Spark UI / query history'],
            ['2. What changed?', 'Input volume (10× more rows after a backfill?), new join, code deploy, source slower, cluster size, competing jobs'],
            ['3. Extraction', 'Full scan on source instead of incremental? Missing index on updated_at? Network throughput?'],
            ['4. Transformation', 'Shuffles, skewed keys, exploding joins (duplicate keys), Python UDFs, too many/few partitions, spills to disk'],
            ['5. Loading', 'Row-by-row inserts, MERGE without key clustering, small files, index maintenance, locks'],
            ['6. Fix &amp; verify', 'Change one thing at a time, measure, and add a duration alert so it is caught earlier next time'],
        ]),
    ),
    interview(
        ul('<strong>Filter early, select only needed columns</strong> (pushdown).',
           '<strong>Process incrementally</strong> instead of full reloads.',
           '<strong>Broadcast</strong> small dimension tables in joins; avoid joining on keys with duplicates you did not expect.',
           '<strong>Replace Python UDFs</strong> with built-in Spark SQL functions.',
           '<strong>Tune partitions</strong>: <code>spark.sql.shuffle.partitions</code>, enable AQE, avoid small files.',
           '<strong>Cache</strong> a DataFrame only if it is reused several times — and unpersist it.',
           '<strong>Bulk load</strong> and set-based MERGE instead of row-by-row operations.'),
        title='Common Fixes Interviewers Expect'),
    crossq(
        ('What is a "join explosion"?',
         'Joining on a key that is unexpectedly not unique on one side multiplies rows — 1 million orders × 5 duplicate customer rows = 5 million rows. Always check key uniqueness before joining; compare row counts before and after.'),
    ),
]),

# ------------------------------------------------------------------ 41
Q('What is data skew and how do you handle it?', 'Data Skew', minutes=7, cards=[
    definition(
        defbox('<strong>Data skew</strong> is an uneven distribution of data across partitions/tasks, usually because a few '
               'key values are far more frequent than others (a "hot key" such as a default customer id, NULL, or a very '
               'large city). The job is only as fast as its slowest task.'),
        tags('Data Skew', 'Hot Key', 'Salting', 'Broadcast Join', 'AQE', 'Shuffle'),
    ),
    skew_anim(),
    example(
        py("""
from pyspark.sql import functions as F

# 1) Let Spark 3 split skewed partitions automatically
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")

# 2) Broadcast the small side so the big side is never shuffled
result = orders.join(F.broadcast(dim_city), "city")

# 3) Salting a hot key for an aggregation
SALT = 10
partial = (orders.withColumn("salt", (F.rand() * SALT).cast("int"))
                 .groupBy("city", "salt").agg(F.sum("amount").alias("amt")))
final = partial.groupBy("city").agg(F.sum("amt").alias("revenue"))

# 4) Handle NULL keys separately (they all hash to one partition)
nulls, non_nulls = orders.filter("customer_id IS NULL"), orders.filter("customer_id IS NOT NULL")
""", 'PySpark'),
        title='Example'),
    crossq(
        ('How do you detect skew?',
         'In the Spark UI, look at a stage\'s task metrics: if the max task duration or shuffle-read size is many times the median, the stage is skewed. Then check key frequencies with <code>groupBy(key).count().orderBy(desc("count"))</code>.'),
    ),
]),

# ------------------------------------------------------------------ 42
Q('What is predicate pushdown and projection pushdown?', 'Predicate & Projection Pushdown', minutes=5, cards=[
    definition(
        defbox('<strong>Predicate pushdown</strong> moves filters (<code>WHERE</code> conditions) as close to the data source '
               'as possible, so less data is read. <strong>Projection pushdown</strong> (column pruning) reads only the columns '
               'that the query needs.'),
        tags('Predicate Pushdown', 'Projection Pushdown', 'Column Pruning', 'JDBC', 'Parquet Statistics'),
    ),
    pushdown_anim(),
    example(
        py("""
# JDBC: let MySQL do the filtering (uses its indexes) instead of pulling the whole table
orders = (spark.read.format("jdbc")
            .option("url", "jdbc:mysql://replica:3306/shop")
            .option("query", "SELECT order_id, city, amount FROM orders "
                             "WHERE updated_at >= '2026-10-08' AND city = 'Pune'")
            .option("user", user).option("password", pwd)
            .load())

# Parquet: filter + column selection are pushed into the scan automatically
pune = spark.read.parquet("s3://lake/silver/orders").select("order_id", "amount").filter("city = 'Pune'")
pune.explain()      # look for PushedFilters: [IsNotNull(city), EqualTo(city,Pune)] and ReadSchema
""", 'PySpark'),
        title='Example'),
    crossq(
        ('What can prevent pushdown?',
         'Filters applied after a Python UDF, casts or functions on the column, filters on computed columns, or data sources that do not support it. Check the physical plan with <code>explain()</code>.'),
    ),
]),

# ------------------------------------------------------------------ 43
Q('How do you handle PII and security in data pipelines?', 'PII & Security', minutes=7, cards=[
    definition(
        defbox('<strong>PII</strong> (Personally Identifiable Information) — names, phone numbers, emails, Aadhaar, PAN, '
               'addresses, bank details — must be protected throughout the pipeline. In India the <strong>Digital Personal '
               'Data Protection (DPDP) Act, 2023</strong> sets obligations on how personal data is processed; GDPR applies to EU residents.'),
        table(['Technique', 'What it does', 'Example'], [
            ['Masking', 'Hide part of the value', '98200-XXXXX'],
            ['Hashing (with salt)', 'Irreversible token; still joinable', 'sha256(salt + email)'],
            ['Tokenisation', 'Replace with a token; original kept in a secure vault', 'card → tok_8f3a…'],
            ['Encryption', 'Reversible with key; at rest and in transit', 'S3 SSE-KMS, TLS for JDBC'],
            ['Column/row-level security', 'Only authorised roles see sensitive data', 'Views, Unity Catalog / Snowflake masking policies'],
            ['Minimisation', 'Do not extract what you do not need', 'Skip Aadhaar column entirely'],
        ]),
        tags('PII', 'Masking', 'Hashing', 'Encryption', 'DPDP Act', 'GDPR', 'Least Privilege'),
    ),
    example(
        pyrun("""
import hashlib, os, re

SALT = os.environ.get("PII_SALT", "demo-salt")          # real salt comes from a secrets manager

def hash_pii(value: str) -> str:
    return hashlib.sha256((SALT + value.strip().lower()).encode()).hexdigest()[:16]

def mask_phone(p: str) -> str:
    digits = re.sub(r"\\D", "", p)
    return digits[:5] + "X" * (len(digits) - 5)

def mask_email(e: str) -> str:
    user, domain = e.split("@")
    return user[0] + "***@" + domain

row = {"name": "Asha Patil", "email": "Asha.P@cdac.in", "phone": "98200 11111"}
safe = {"customer_hash": hash_pii(row["email"]),
        "email_masked": mask_email(row["email"]),
        "phone_masked": mask_phone(row["phone"])}
print(safe)
print(hash_pii("asha.p@cdac.in ") == safe["customer_hash"])   # same person -> same hash -> joinable
"""),
        title='Example: Hashing and Masking'),
    crossq(
        ('Why add a salt when hashing?',
         'Phone numbers and emails have small, guessable value spaces; without a secret salt anyone can hash all possible phone numbers and reverse the mapping.'),
        ('Where should credentials live?',
         'In a secrets manager (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault) or the orchestrator\'s encrypted connections — never in code, notebooks, or Git. Use short-lived, least-privilege service accounts.'),
    ),
]),

# ------------------------------------------------------------------ 44
Q('How do you reduce the cost of pipelines in the cloud?', 'Cloud Cost Optimisation', minutes=6, cards=[
    definition(
        defbox('In the cloud, inefficient pipelines show up directly on the bill. Cost is driven mainly by '
               '<strong>compute time</strong>, <strong>data scanned</strong>, <strong>storage</strong> and <strong>data transfer</strong>.'),
        table(['Area', 'Techniques'], [
            ['Compute', 'Incremental instead of full loads; auto-scaling and auto-terminate clusters; spot/preemptible instances for batch; right-size warehouses; schedule only what is needed'],
            ['Data scanned', 'Parquet + partitioning + clustering; select only needed columns; avoid SELECT * in BigQuery/Athena (billed per TB scanned)'],
            ['Storage', 'Lifecycle policies (hot → infrequent → archive tiers); delete temp/staging data; VACUUM old table versions; compress'],
            ['Transfer', 'Keep compute in the same region as storage; avoid cross-cloud copies'],
            ['Governance', 'Tag resources per pipeline/team; budgets and alerts; review the most expensive queries monthly'],
        ]),
        tags('Cost Optimisation', 'FinOps', 'Spot Instances', 'Auto-scaling', 'Lifecycle Policy', 'Partitioning'),
    ),
    crossq(
        ('A BigQuery query costs ₹4,000 each run. First thing to check?',
         'How many bytes it scans: is it filtering on the partition column, selecting only needed columns, and querying a clustered table? A missing partition filter often scans the full table every run.'),
    ),
]),

# ------------------------------------------------------------------ 45
Q('How do you test ETL pipelines? What types of ETL testing exist?', 'ETL Testing', minutes=7, cards=[
    definition(
        table(['Test type', 'What it verifies', 'Example'], [
            ['Unit tests', 'Individual transformation functions/SQL logic with small fixed inputs', 'clean_city("  pune ") == "Pune"'],
            ['Schema tests', 'Columns, types, constraints of outputs', 'order_id is BIGINT NOT NULL'],
            ['Data-quality tests', 'Rules on real data each run', 'unique, not_null, accepted_values'],
            ['Reconciliation / completeness', 'Source vs target counts and totals', 'COUNT and SUM match per day'],
            ['Integration tests', 'Whole pipeline on a sample environment', 'Run the DAG on a test schema end-to-end'],
            ['Regression tests', 'Output unchanged after a refactor', 'Compare new vs old gold table (diff)'],
            ['Performance tests', 'Runtime with production-like volume', 'Load 100 M rows within the window'],
            ['Idempotency test', 'Running twice gives the same result', 'Run the same window twice, compare'],
        ]),
        tags('ETL Testing', 'Unit Test', 'Integration Test', 'Regression', 'Data Diff', 'CI/CD'),
    ),
    example(
        sqlrun("""
-- Regression test: compare the gold table built by the old and new code (data diff)
CREATE TABLE gold_old (city VARCHAR(20), revenue INT);
CREATE TABLE gold_new (city VARCHAR(20), revenue INT);
INSERT INTO gold_old VALUES ('Pune', 1000), ('Delhi', 800), ('Agra', 300);
INSERT INTO gold_new VALUES ('Pune', 1000), ('Delhi', 820), ('Agra', 300), ('Goa', 50);

SELECT COALESCE(o.city, n.city) AS city, o.revenue AS old_rev, n.revenue AS new_rev,
       CASE WHEN o.city IS NULL THEN 'ADDED'
            WHEN n.city IS NULL THEN 'REMOVED'
            ELSE 'CHANGED' END AS diff
FROM gold_old o LEFT JOIN gold_new n ON n.city = o.city
WHERE n.city IS NULL OR n.revenue <> o.revenue
UNION ALL
SELECT n.city, NULL, n.revenue, 'ADDED'
FROM gold_new n LEFT JOIN gold_old o ON o.city = n.city
WHERE o.city IS NULL;
"""),
        title='Example: Data Diff Between Two Versions'),
    crossq(
        ('How do ETL tests fit into CI/CD?',
         'On every pull request: lint SQL/Python, run unit tests, build changed dbt models on a sample/clone schema and run their tests (dbt "slim CI"), and diff key outputs. Deploy only when all pass.'),
    ),
]),

])
