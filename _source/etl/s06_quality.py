from build import *
from etl.anims import *

SECTION = dict(level='advanced', title='Data Quality & Reliability', questions=[

# ------------------------------------------------------------------ 33
Q('What are the dimensions of data quality?', 'Data Quality Dimensions', minutes=6, cards=[
    definition(
        defbox('Data quality is measured along several <strong>dimensions</strong>. Each one translates into concrete, '
               'automatable checks in a pipeline.'),
        table(['Dimension', 'Question it answers', 'Example check'], [
            ['Completeness', 'Is all expected data present?', 'No NULL order_id; today\'s file has all 30 stores'],
            ['Validity', 'Does data follow the rules and formats?', 'Email matches pattern; status in (PAID, PENDING, CANCELLED)'],
            ['Accuracy', 'Does it reflect reality?', 'Totals match the finance system'],
            ['Consistency', 'Does it agree across systems/tables?', 'Order count in silver = count in source'],
            ['Uniqueness', 'Are there duplicates?', 'order_id unique in fact table'],
            ['Timeliness / freshness', 'Is it up to date?', 'MAX(updated_at) within the last 2 hours'],
            ['Integrity', 'Do relationships hold?', 'Every fact.customer_key exists in dim_customer'],
        ]),
        tags('Data Quality', 'Completeness', 'Validity', 'Accuracy', 'Consistency', 'Uniqueness', 'Freshness'),
    ),
    example(
        sqlrun("""
CREATE TABLE fact_orders (order_id INT, customer_key INT, status VARCHAR(10), amount DECIMAL(10,2), loaded_at DATETIME);
INSERT INTO fact_orders VALUES
 (1, 10, 'PAID', 500, NOW()), (2, 11, 'PAID', -20, NOW()), (2, 11, 'PAID', -20, NOW()),
 (3, NULL, 'SHIPPED', 75, NOW()), (4, 12, 'PENDING', 300, NOW() - INTERVAL 5 HOUR);

SELECT 'completeness: null customer_key' AS check_name, COUNT(*) AS result FROM fact_orders WHERE customer_key IS NULL
UNION ALL
SELECT 'validity: bad status', COUNT(*) FROM fact_orders WHERE status NOT IN ('PAID','PENDING','CANCELLED')
UNION ALL
SELECT 'validity: negative amount', COUNT(*) FROM fact_orders WHERE amount < 0
UNION ALL
SELECT 'uniqueness: duplicate order_id', COUNT(*) FROM (SELECT order_id FROM fact_orders GROUP BY order_id HAVING COUNT(*) > 1) d
UNION ALL
SELECT 'freshness: hours since last load', TIMESTAMPDIFF(HOUR, MAX(loaded_at), NOW()) FROM fact_orders;
"""),
        title='Example: Quality Checks in SQL'),
    crossq(
        ('Who defines what "good quality" means?',
         'The business owners of the data, together with engineers. Engineers implement and automate the checks; thresholds (e.g. "up to 0.5% unknown city is acceptable") are business decisions.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do you implement data validation checks in a pipeline?', 'Validation Checks (dbt, Great Expectations)', minutes=7, cards=[
    definition(
        defbox('Validation checks are automated tests that run <strong>on the data</strong> at each stage, usually right '
               'after loading a layer and before publishing it. A failed critical check stops the pipeline; a warning-level '
               'check alerts but continues.'),
        table(['Where', 'What to check'], [
            ['On ingest (bronze)', 'File arrived, not empty, expected columns, row count within normal range'],
            ['After transform (silver)', 'Primary key unique & not null, types valid, accepted values, referential integrity'],
            ['Before publish (gold)', 'Totals reconcile with source, no sudden drops/spikes vs history, freshness'],
        ]),
        tags('Data Validation', 'dbt tests', 'Great Expectations', 'Soda', 'Severity', 'Quality Gate'),
    ),
    example(
        code("""
# models/silver/schema.yml  (dbt)
version: 2
models:
  - name: silver_orders
    columns:
      - name: order_id
        tests: [not_null, unique]
      - name: status
        tests:
          - accepted_values:
              values: ['PAID', 'PENDING', 'CANCELLED']
      - name: customer_id
        tests:
          - relationships:
              to: ref('silver_customers')
              field: customer_id
              config: {severity: warn}
""", 'dbt tests (YAML)', 'fa-file-code'),
        pyrun("""
import pandas as pd

df = pd.DataFrame({"order_id": [1, 2, 2, 4], "status": ["PAID", "PAID", "PAID", "LOST"],
                   "amount": [500, 120, 120, -5]})

checks = {
    "order_id not null":  df["order_id"].notna().all(),
    "order_id unique":    df["order_id"].is_unique,
    "status accepted":    df["status"].isin(["PAID", "PENDING", "CANCELLED"]).all(),
    "amount >= 0":        (df["amount"] >= 0).all(),
    "row count > 0":      len(df) > 0,
}
for name, ok in checks.items():
    print(f"{'PASS' if ok else 'FAIL'}  {name}")

failed = [n for n, ok in checks.items() if not ok]
if failed:
    print(f"Quality gate FAILED ({len(failed)} checks) -> do not publish")
""", 'A minimal quality gate in Python'),
        title='Example'),
    crossq(
        ('What is anomaly detection in data quality?',
         'Instead of fixed rules, compare each run with history: row count, NULL rate or revenue outside, say, 3 standard deviations of the last 30 days triggers an alert. Tools like Monte Carlo, Soda and Elementary automate this.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you handle bad records without failing the whole pipeline?', 'Bad Records & Quarantine', minutes=6, cards=[
    definition(
        defbox('Failing a 10-million-row load because of 3 malformed rows is usually wrong; silently dropping them is '
               'worse. The standard pattern is to <strong>route bad records to a quarantine (dead-letter) area with the '
               'reason</strong>, load the good ones, and alert when the error rate crosses a threshold.'),
        tags('Bad Records', 'Quarantine', 'Dead Letter Queue', 'Error Threshold', 'badRecordsPath', 'PERMISSIVE'),
    ),
    quarantine(),
    example(
        py("""
# Spark: keep malformed CSV/JSON rows instead of failing or dropping them
df = (spark.read
        .option("mode", "PERMISSIVE")                        # FAILFAST | DROPMALFORMED | PERMISSIVE
        .option("columnNameOfCorruptRecord", "_corrupt")
        .schema(expected_schema_with_corrupt_col)
        .csv("s3://landing/vendor/2026-10-08/"))

bad  = df.filter("_corrupt IS NOT NULL")
good = df.filter("_corrupt IS NULL").drop("_corrupt")

bad.withColumn("reason", F.lit("unparseable row")).write.mode("append").parquet("s3://lake/quarantine/vendor")
ratio = bad.count() / max(df.count(), 1)
if ratio > 0.01:
    raise ValueError(f"{ratio:.2%} bad rows - stopping load")   # fails the task -> alert
""", 'PySpark'),
        title='Example'),
    crossq(
        ('When should the pipeline fail instead of quarantining?',
         'When the problem is structural (missing columns, wrong file, schema change), when the error rate is above the agreed threshold, or for critical financial data where partial loads are unacceptable.'),
    ),
]),

# ------------------------------------------------------------------ 36
Q('What is data reconciliation? How do you verify a load is complete and correct?', 'Reconciliation', minutes=6, cards=[
    definition(
        defbox('<strong>Reconciliation</strong> compares source and target to prove that nothing was lost, duplicated or '
               'altered in transit. It is the pipeline\'s equivalent of balancing accounts.'),
        table(['Level', 'Check'], [
            ['Row counts', 'COUNT(*) per table / per day in source = target (after known filters)'],
            ['Control totals', 'SUM(amount), SUM(qty) match'],
            ['Key sets', 'Keys missing in target / extra in target (anti-joins)'],
            ['Hash / checksum', 'Hash of each row or of sorted columns per partition matches'],
            ['Distribution', 'MIN/MAX dates, distinct counts, NULL rates within tolerance'],
        ]),
        tags('Reconciliation', 'Row Count', 'Control Totals', 'Checksum', 'Audit'),
    ),
    example(
        sqlrun("""
CREATE TABLE src_orders (order_id INT, order_date DATE, amount DECIMAL(10,2));
CREATE TABLE tgt_orders LIKE src_orders;
INSERT INTO src_orders VALUES (1,'2026-10-07',100), (2,'2026-10-07',250), (3,'2026-10-08',75), (4,'2026-10-08',30);
INSERT INTO tgt_orders VALUES (1,'2026-10-07',100), (2,'2026-10-07',250), (3,'2026-10-08',75);

SELECT s.order_date,
       s.cnt  AS src_rows, COALESCE(t.cnt, 0)  AS tgt_rows,
       s.total AS src_amount, COALESCE(t.total, 0) AS tgt_amount,
       CASE WHEN s.cnt = t.cnt AND s.total = t.total THEN 'OK' ELSE 'MISMATCH' END AS status
FROM (SELECT order_date, COUNT(*) cnt, SUM(amount) total FROM src_orders GROUP BY order_date) s
LEFT JOIN (SELECT order_date, COUNT(*) cnt, SUM(amount) total FROM tgt_orders GROUP BY order_date) t
       ON t.order_date = s.order_date
ORDER BY s.order_date;

-- Which keys are missing?
SELECT s.order_id FROM src_orders s LEFT JOIN tgt_orders t USING (order_id) WHERE t.order_id IS NULL;
"""),
        title='Example: Count & Sum Reconciliation by Day'),
    crossq(
        ('Source and target are in different systems — how do you compare them?',
         'Compute the same aggregates (counts, sums, hashes per partition) on both sides and compare the small results, rather than moving full data. Store them in an audit table per run for trend analysis.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('How do you monitor pipelines? What are SLAs and data freshness?', 'Monitoring, SLAs & Freshness', minutes=6, cards=[
    definition(
        defbox('Pipeline <strong>monitoring</strong> watches both the <strong>jobs</strong> (did they run, how long, did '
               'they fail) and the <strong>data</strong> (is it fresh, complete, plausible). An <strong>SLA</strong> '
               '(service-level agreement) is a promise to consumers — e.g. "yesterday\'s sales are in the dashboard by 7:00 AM IST".'),
        table(['Signal', 'Example alert'], [
            ['Job failure', 'Task failed after all retries → page on-call'],
            ['Duration', 'Run took 3× its 30-day average'],
            ['SLA miss', 'gold.daily_sales not updated by 07:00'],
            ['Freshness', 'MAX(event_time) older than 2 hours'],
            ['Volume', 'Row count 60% below normal for a weekday'],
            ['Schema change', 'New/missing column detected'],
            ['Cost', 'Warehouse credits for the job doubled'],
        ]),
        tags('Monitoring', 'SLA', 'SLO', 'Freshness', 'Alerting', 'Observability'),
    ),
    example(
        sqlrun("""
CREATE TABLE etl_run_log (run_id INT, pipeline VARCHAR(30), status VARCHAR(10),
                          started_at DATETIME, finished_at DATETIME, rows_loaded INT);
INSERT INTO etl_run_log VALUES
 (101, 'daily_sales', 'SUCCESS', '2026-10-06 01:30', '2026-10-06 01:52', 120450),
 (102, 'daily_sales', 'SUCCESS', '2026-10-07 01:30', '2026-10-07 01:55', 118900),
 (103, 'daily_sales', 'SUCCESS', '2026-10-08 01:30', '2026-10-08 03:41',  41200);

SELECT run_id,
       TIMESTAMPDIFF(MINUTE, started_at, finished_at) AS minutes,
       rows_loaded,
       CASE WHEN finished_at > DATE(started_at) + INTERVAL 3 HOUR THEN 'SLA_MISS' ELSE 'ON_TIME' END AS sla,
       CASE WHEN rows_loaded < 0.6 * (SELECT AVG(rows_loaded) FROM etl_run_log r2 WHERE r2.run_id < r.run_id)
            THEN 'VOLUME_DROP' ELSE 'OK' END AS volume
FROM etl_run_log r ORDER BY run_id;
"""),
        title='Example: Run Log as a Monitoring Source'),
    crossq(
        ('SLA vs SLO vs SLI?',
         'SLI = the measured indicator (data freshness in minutes). SLO = internal target (freshness &lt; 60 min 99% of days). SLA = the external commitment, often with consequences if missed.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('What is data lineage and why does it matter? What is a data catalog?', 'Lineage & Data Catalog', minutes=6, cards=[
    definition(
        defbox('<strong>Data lineage</strong> traces where data comes from, which transformations it went through, and '
               'where it goes — at table level and ideally at column level.',
               'A <strong>data catalog</strong> is a searchable inventory of datasets with their schema, descriptions, '
               'owners, quality status, classifications (PII) and lineage.'),
        tags('Data Lineage', 'Data Catalog', 'Metadata', 'Impact Analysis', 'OpenLineage', 'DataHub'),
    ),
    explanation(
        table(['Use', 'How lineage helps'], [
            ['Impact analysis', 'Before changing a column in silver.orders, see every dashboard and model that depends on it'],
            ['Root-cause analysis', 'A KPI looks wrong → trace back to the source table and run that introduced the issue'],
            ['Compliance', 'Show auditors where PII flows and who can access it (GDPR, India\'s DPDP Act)'],
            ['Trust &amp; discovery', 'Analysts find the right, certified table instead of building their own copy'],
        ]),
        p('Tools: <strong>dbt docs</strong> (lineage graph from <code>ref()</code>), <strong>OpenLineage</strong> + Marquez '
          '(collected from Airflow/Spark), <strong>DataHub</strong>, <strong>Amundsen</strong>, <strong>Unity Catalog</strong>, '
          '<strong>AWS Glue Data Catalog</strong>, <strong>Microsoft Purview</strong>.', True),
    ),
    crossq(
        ('How does dbt build lineage automatically?',
         'Models reference each other with <code>{{ ref(\'model_name\') }}</code> and sources with <code>{{ source(...) }}</code> instead of hard-coded table names, so dbt knows the full dependency graph and runs models in order.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('How do you make pipelines restartable? Explain checkpoints', 'Restartability & Checkpoints', minutes=6, cards=[
    definition(
        defbox('A <strong>restartable</strong> pipeline can resume after a failure without manual cleanup and without '
               'reprocessing everything from scratch. It records <strong>progress (checkpoints)</strong> and makes each step '
               'idempotent so a step can safely run again.'),
        tags('Restartability', 'Checkpoint', 'Idempotency', 'Control Table', 'Streaming Checkpoint'),
    ),
    explanation(
        ul('Split the pipeline into <strong>small, independent steps</strong> with clear inputs/outputs (stage → transform → publish), so a failure re-runs one step, not the whole chain.',
           'Keep a <strong>control table</strong> of processed units (files, partitions, watermarks) with status; skip units already marked SUCCESS.',
           'Write outputs <strong>atomically</strong> (temp location + rename/commit, table formats, transactions) so a crash never leaves half-written results.',
           'Streaming engines persist offsets and state in a <strong>checkpoint location</strong> (Spark <code>checkpointLocation</code>, Flink savepoints); on restart they continue exactly where they stopped.'),
    ),
    example(
        pyrun("""
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE file_log (file_name TEXT PRIMARY KEY, status TEXT)")
files = ["sales_01.csv", "sales_02.csv", "sales_03.csv", "sales_04.csv"]

def process(name, fail_on=None):
    if name == fail_on:
        raise RuntimeError(f"crash while processing {name}")
    return f"loaded {name}"

def run(fail_on=None):
    done = {r[0] for r in conn.execute("SELECT file_name FROM file_log WHERE status='SUCCESS'")}
    for f in files:
        if f in done:
            print("  skip  ", f)
            continue
        print(" ", process(f, fail_on))
        with conn:
            conn.execute("INSERT OR REPLACE INTO file_log VALUES (?, 'SUCCESS')", (f,))

print("Run 1:")
try:
    run(fail_on="sales_03.csv")
except RuntimeError as e:
    print("  FAILED:", e)
print("Run 2 (restart):")
run()
"""),
        title='Example: Resume From Where It Failed'),
    crossq(
        ('Why must a streaming checkpoint location never be shared or deleted casually?',
         'It holds the offsets and state of that exact query. Sharing it between queries corrupts both; deleting it makes the query start again from the configured starting offsets — causing duplicates or data loss.'),
    ),
]),

])
