from build import *
from etl.anims import *

SECTION = dict(level='expert', title='Scenario & Design', questions=[

# ------------------------------------------------------------------ 46
Q('Design: an incremental pipeline from a production MySQL database to a data warehouse', 'Design: MySQL → Warehouse', minutes=10, tag='Design', cards=[
    definition(
        defbox('<strong>Scenario:</strong> An e-commerce company runs on MySQL (orders, order_items, customers, products; '
               '~5 million orders, ~200k changes/day). Analysts need sales data in the warehouse with at most 15 minutes delay, '
               'including cancellations and deleted test orders. The production database must not be slowed down.'),
        title='Problem Statement'),
    explanation(
        table(['Question', 'Why it matters'], [
            ['Latency needed — 15 min, hourly, daily?', 'Decides CDC/streaming vs scheduled batch'],
            ['Do rows get updated? Hard-deleted?', 'Timestamp extraction misses deletes → CDC'],
            ['Is there a reliable updated_at with an index?', 'Possible watermark alternative'],
            ['Is a read replica available? binlog access?', 'Source impact and CDC feasibility'],
            ['History required (SCD2)?', 'Dimension design'],
            ['Volume, growth, retention, PII?', 'Partitioning, cost, masking'],
        ]),
        title='Clarifying Questions to Ask First'),
    mysql_to_wh(),
    explanation(
        ul('<strong>Ingestion</strong>: Debezium MySQL connector (initial snapshot, then binlog streaming) → Kafka topics per table. Alternative for simpler needs: watermark-based extraction every 15 min from a read replica.',
           '<strong>Bronze</strong>: raw change events appended to Delta/Iceberg tables, partitioned by ingestion date, with binlog position.',
           '<strong>Silver</strong>: Spark Structured Streaming (trigger every 5 min) or scheduled job that deduplicates by primary key, orders by binlog position and MERGEs into mirror tables, applying deletes.',
           '<strong>Gold</strong>: dbt or Spark builds dim_customer (SCD2), dim_product, fact_order_items, and daily aggregates; facts partitioned by order date.',
           '<strong>Orchestration</strong>: Airflow for batch steps, backfills and dependencies; streaming jobs monitored separately.',
           '<strong>Quality</strong>: row-count reconciliation vs source per day, unique/not-null tests, freshness alerts (&gt; 30 min lag pages on-call).',
           '<strong>Reliability</strong>: idempotent MERGEs, streaming checkpoints, schema registry for evolution, dead-letter topic for malformed events.',
           '<strong>Security</strong>: CDC user with replication privileges only; PII hashed in silver; secrets in a vault.'),
        title='Proposed Design'),
    crossq(
        ('Why not just run SELECT * FROM orders every 15 minutes?',
         'Full scans of a growing table every 15 minutes hurt production, miss hard deletes, and get slower every month. CDC reads only the changes from the log.'),
        ('How would you do the initial historical load of 5 million orders?',
         'Use the connector\'s consistent snapshot (or a one-time bulk export from a replica) and record the binlog position at that point; start streaming from exactly that position so nothing is missed or duplicated.'),
    ),
]),

# ------------------------------------------------------------------ 47
Q('Design: vendors drop daily CSV files on S3 — build a robust ingestion pipeline', 'Design: Daily Vendor Files', minutes=9, tag='Design', cards=[
    definition(
        defbox('<strong>Scenario:</strong> 40 vendors upload a stock file each night to <code>s3://incoming/&lt;vendor&gt;/</code>. '
               'Files sometimes arrive late, twice, partially uploaded, with an extra column, or with bad rows. The business '
               'needs a consolidated stock table by 8 AM.'),
        title='Problem Statement'),
    explanation(
        table(['Concern', 'Design decision'], [
            ['Detecting arrival', 'S3 event notification → queue, or an Airflow S3 sensor per vendor with a deadline'],
            ['Partial uploads', 'Vendors upload to a temp name and rename, or send a _SUCCESS/manifest file; process only after the marker'],
            ['Duplicates / re-sends', 'Control table keyed by file name + checksum (ETag/MD5); skip if already processed; a corrected file overwrites the vendor/date partition'],
            ['Schema drift', 'Validate header against the vendor\'s expected schema; new columns → warn; missing required → reject file'],
            ['Bad rows', 'PERMISSIVE parsing; quarantine bad rows with reason; fail the file if &gt; threshold'],
            ['Raw retention', 'Copy original file to bronze (immutable) before processing'],
            ['Late files', 'Process what arrived by 7:30, mark missing vendors in a status table, reprocess automatically when a late file lands'],
            ['Output', 'Silver stock table partitioned by stock_date, MERGE by (vendor, sku, stock_date)'],
            ['Visibility', 'Status dashboard: vendor × date → arrived / processed / rejected; alerts to vendor managers'],
        ]),
        title='Design'),
    example(
        sqlrun("""
CREATE TABLE file_control (
  file_name VARCHAR(100), vendor VARCHAR(20), file_date DATE, checksum CHAR(32),
  status VARCHAR(12), rows_ok INT, rows_bad INT, processed_at DATETIME,
  PRIMARY KEY (file_name, checksum)
);
INSERT INTO file_control VALUES
 ('stock_V01_20261008.csv', 'V01', '2026-10-08', 'a1b2c3', 'SUCCESS',  1200, 0,  '2026-10-09 01:10'),
 ('stock_V02_20261008.csv', 'V02', '2026-10-08', 'd4e5f6', 'REJECTED', 0,  640, '2026-10-09 01:12'),
 ('stock_V02_20261008.csv', 'V02', '2026-10-08', '9f8e7d', 'SUCCESS',  640, 0,  '2026-10-09 05:40');

-- Has this exact file (same content) been processed already?
SELECT COUNT(*) AS already_done FROM file_control
WHERE file_name = 'stock_V01_20261008.csv' AND checksum = 'a1b2c3' AND status = 'SUCCESS';

-- Morning status per vendor (latest attempt wins)
SELECT vendor, file_date, status, rows_ok, rows_bad
FROM (SELECT f.*, ROW_NUMBER() OVER (PARTITION BY vendor, file_date ORDER BY processed_at DESC) rn
      FROM file_control f) t
WHERE rn = 1;
"""),
        title='Example: File Control Table'),
    crossq(
        ('Why use the checksum and not just the file name?',
         'Vendors re-send corrected files with the same name. Same name + different checksum = new content to process; same name + same checksum = duplicate to skip.'),
    ),
]),

# ------------------------------------------------------------------ 48
Q('Scenario: a critical pipeline failed at 3 AM. What do you do?', 'Incident: 3 AM Failure', minutes=7, tag='Scenario', cards=[
    definition(
        defbox('This question tests operational maturity: calm triage, communication, a correct fix, and preventing '
               'recurrence. Structure the answer as a runbook.'),
        title='What the Interviewer Is Testing'),
    explanation(
        table(['Phase', 'Actions'], [
            ['1. Assess impact', 'Which pipeline, which tables, which dashboards/consumers, which SLA? Is data wrong, or only late?'],
            ['2. Communicate', 'Acknowledge the alert; post a short status in the incident channel; inform stakeholders if the SLA will be missed — before they discover it'],
            ['3. Diagnose', 'Read the task log and error; check what changed (deploy, source schema, credentials expired, disk/quota, upstream late, volume spike)'],
            ['4. Mitigate', 'Fix forward or roll back the deploy; re-run the failed task (safe because idempotent); if data is bad, hold publishing so dashboards keep yesterday\'s correct data'],
            ['5. Verify', 'Reconcile counts/totals, run quality checks, confirm dashboards'],
            ['6. Close &amp; learn', 'Blameless post-mortem: root cause, timeline, action items (new test, alert, retry policy, runbook update)'],
        ]),
        title='Runbook'),
    interview(
        hl('Mention <strong>idempotent re-runs</strong>, <strong>not publishing bad data</strong>, <strong>proactive stakeholder '
           'communication</strong> and a <strong>post-mortem with a preventive action</strong>. These four points separate strong '
           'answers from "I would check the logs and re-run it".', 'What earns the marks'),
    ),
    crossq(
        ('What are common root causes of pipeline failures?',
         'Upstream schema changes, late or missing source data, expired credentials/certificates, out-of-memory from volume growth, skew, dependency/library upgrades, quota limits, and bad deploys.'),
    ),
]),

# ------------------------------------------------------------------ 49
Q('How do you handle duplicate events? Explain at-most-once, at-least-once and exactly-once', 'Delivery Guarantees', minutes=8, cards=[
    definition(
        table(['Guarantee', 'Meaning', 'Risk'], [
            ['At-most-once', 'Each message processed 0 or 1 times', 'Data loss'],
            ['At-least-once', 'Each message processed 1 or more times', 'Duplicates'],
            ['Exactly-once', 'Each message affects the result exactly once', 'Needs coordination: idempotent or transactional sinks'],
        ]),
        tags('At-least-once', 'Exactly-once', 'Idempotent Consumer', 'Kafka Offsets', 'Event ID', 'Deduplication'),
    ),
    delivery_anim(),
    example(
        sqlrun("""
CREATE TABLE payments (event_id VARCHAR(40) PRIMARY KEY, order_id INT, amount INT, received_at DATETIME);

-- The same event delivered three times (retries / consumer restart)
INSERT IGNORE INTO payments VALUES ('evt-7f1c', 5001, 1499, NOW());
INSERT IGNORE INTO payments VALUES ('evt-7f1c', 5001, 1499, NOW());
INSERT IGNORE INTO payments VALUES ('evt-7f1c', 5001, 1499, NOW());
INSERT IGNORE INTO payments VALUES ('evt-90aa', 5002,  299, NOW());

SELECT order_id, COUNT(*) AS rows_stored, SUM(amount) AS total FROM payments GROUP BY order_id;
""", 'Idempotent consumer: the unique event_id absorbs duplicates'),
        title='Example'),
    crossq(
        ('Does Kafka support exactly-once?',
         'Within Kafka (consume → process → produce to Kafka) yes: idempotent producers plus transactions (<code>enable.idempotence</code>, <code>transactional.id</code>, consumers with <code>isolation.level=read_committed</code>). Writing to an external database needs an idempotent or transactional sink.'),
        ('What if events have no unique id?',
         'Create a deterministic one — e.g. a hash of source system + key + event timestamp — or use the source position (Kafka topic-partition-offset, binlog file+position) as the id.'),
    ),
]),

# ------------------------------------------------------------------ 50
Q('Which ETL / data integration tools should you know?', 'ETL Tools Landscape', minutes=6, cards=[
    definition(
        table(['Category', 'Tools', 'Notes'], [
            ['Enterprise GUI ETL', 'Informatica PowerCenter / IDMC, IBM DataStage, Talend, SSIS, Pentaho', 'Common in banks, insurance, large Indian IT services projects'],
            ['Cloud-native ETL', 'AWS Glue, Azure Data Factory, Google Dataflow / Data Fusion, Databricks Workflows', 'Managed, serverless options in each cloud'],
            ['Managed ingestion (EL)', 'Fivetran, Airbyte (open source), Stitch, Hevo', 'Pre-built connectors for SaaS and databases'],
            ['CDC', 'Debezium, AWS DMS, Oracle GoldenGate, Qlik Replicate', 'Log-based change capture'],
            ['Processing engines', 'Apache Spark (PySpark), Flink, Beam, pandas/Polars, DuckDB', 'Code-based transformations'],
            ['In-warehouse transformation', 'dbt, SQLMesh, Dataform, stored procedures', 'ELT with SQL, testing and lineage'],
            ['Orchestration', 'Apache Airflow, Dagster, Prefect, ADF pipelines, Step Functions', 'Scheduling and dependencies'],
            ['Streaming', 'Kafka + Kafka Connect, Kinesis, Pub/Sub, Spark Structured Streaming', 'Real-time pipelines'],
            ['Quality &amp; observability', 'Great Expectations, Soda, dbt tests, Monte Carlo, Elementary', 'Data tests and monitoring'],
        ]),
        tags('Informatica', 'Talend', 'AWS Glue', 'Azure Data Factory', 'dbt', 'Airflow', 'Spark', 'Fivetran', 'Airbyte'),
    ),
    interview(
        p('Interviewers care less about which tool you used than whether you understand the <strong>concepts underneath</strong> — '
          'incremental loads, CDC, idempotency, data quality, partitioning, orchestration. Explain your project in those terms, '
          'then name the tools. A good modern combination to learn: <strong>Python + SQL + PySpark + Airflow + dbt + one cloud '
          '(AWS Glue/S3 or Azure ADF/ADLS)</strong>.'),
        title='How to Talk About Tools'),
    crossq(
        ('Code-based or GUI ETL tools — which is better?',
         'Code (SQL/Python/Spark + Git) gives version control, testing, code review and reuse; GUI tools give faster onboarding and visual flows for standard patterns. Many enterprises use both; the industry trend is toward code-first with managed services.'),
    ),
]),

])
