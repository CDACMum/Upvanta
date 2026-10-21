from build import *
from etl.anims import *

SECTION = dict(level='beginner', title='Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is ETL?', 'What is ETL', minutes=6, cards=[
    definition(
        defbox('<strong>ETL — Extract, Transform, Load</strong> — is the process of moving data from source systems into a '
               'target system (usually a data warehouse) in a form that is ready for analysis.'),
        table(['Step', 'What happens', 'Examples'], [
            ['Extract', 'Read data from one or more sources', 'MySQL orders table, CRM API, CSV files on SFTP, Kafka topic'],
            ['Transform', 'Clean, standardise, join, deduplicate, aggregate, apply business rules', 'Trim names, convert currencies, map status codes, derive revenue'],
            ['Load', 'Write the result into the target', 'Insert into fact_sales, upsert dim_customer, write Parquet to S3'],
        ]),
        tags('ETL', 'Extract', 'Transform', 'Load', 'Data Warehouse', 'Data Pipeline'),
    ),
    etl_pipeline(),
    real_world(
        scenario('C-DAC placement analytics',
                 p('Every night: <strong>extract</strong> student marks from the exam MySQL database, attendance from the face-attendance '
                   'system\'s API, and company offers from a Google Sheet export; <strong>transform</strong> — standardise '
                   'student ids, calculate attendance %, derive CTC bands, join everything per student; <strong>load</strong> '
                   'into a reporting table that powers the placement dashboard.')),
    ),
    crossq(
        ('Why not run reports directly on the source databases?',
         'Sources are built for transactions, not analysis: heavy queries slow down the live application, data is spread '
         'across systems with different formats and keys, and sources often overwrite history. ETL integrates, cleans and preserves it.'),
        ('Name some ETL tools.',
         'GUI/enterprise: Informatica PowerCenter, Talend, SSIS, Azure Data Factory, AWS Glue, Matillion. Code-based: '
         'Python, PySpark, dbt (transform), Airflow (orchestration). Ingestion SaaS: Fivetran, Airbyte, Stitch.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What is the difference between ETL and ELT?', 'ETL vs ELT', minutes=7, cards=[
    definition(
        defbox('In <strong>ETL</strong>, data is transformed on a separate processing engine <strong>before</strong> it is '
               'loaded into the target.',
               'In <strong>ELT</strong>, raw data is loaded into the target <strong>first</strong>, and transformed '
               '<strong>inside</strong> the target using its own compute — typically SQL in a cloud warehouse or lakehouse '
               '(Snowflake, BigQuery, Redshift, Databricks).'),
        tags('ETL', 'ELT', 'Cloud Data Warehouse', 'dbt', 'Raw Layer', 'Pushdown'),
    ),
    comparison(
        table(['Aspect', 'ETL', 'ELT'], [
            ['Order', 'Extract → Transform → Load', 'Extract → Load → Transform'],
            ['Where transformation runs', 'ETL server / Spark cluster / tool engine', 'Inside the warehouse/lakehouse (SQL)'],
            ['Raw data kept in target?', 'Usually not', 'Yes — raw layer is preserved'],
            ['Reprocessing', 'Re-extract from source', 'Re-run SQL on stored raw data'],
            ['Time to availability', 'Slower — transform first', 'Faster — load immediately'],
            ['Scalability', 'Limited by ETL server', 'Elastic warehouse compute'],
            ['Sensitive data', 'Can be masked before landing', 'Lands raw — needs strong governance'],
            ['Typical era / tools', 'On-prem warehouses; Informatica, SSIS, Talend', 'Cloud; Fivetran/Airbyte + dbt + Snowflake/BigQuery'],
        ]),
    ),
    etl_vs_elt(),
    example(
        sqlrun("""
-- ELT in miniature: load raw, then transform with SQL inside the database
CREATE TABLE raw_orders (order_id INT, cust VARCHAR(50), amount VARCHAR(20), status VARCHAR(10));
INSERT INTO raw_orders VALUES
 (1, '  asha ', '1,200.50', 'paid'),
 (2, 'ROHIT',   '300',      'PAID'),
 (3, 'meera',   'n/a',      'cancelled');

CREATE TABLE stg_orders AS
SELECT order_id,
       CONCAT(UPPER(LEFT(TRIM(cust), 1)), LOWER(SUBSTRING(TRIM(cust), 2))) AS customer,
       CASE WHEN amount REGEXP '^[0-9,.]+$'
            THEN CAST(REPLACE(amount, ',', '') AS DECIMAL(10,2)) END     AS amount,
       UPPER(status)                                                    AS status
FROM raw_orders;

SELECT * FROM stg_orders;
"""),
        title='Example: ELT with SQL'),
    crossq(
        ('Which is better?',
         'Neither universally. ELT dominates modern cloud stacks because warehouse compute is elastic and keeping raw data '
         'enables reprocessing. ETL still fits when data must be masked or reduced before landing, when the target is '
         'not a powerful engine, or for heavy non-SQL transformations (ML features, complex parsing in Spark).'),
        ('What is "reverse ETL"?',
         'Moving modelled data <em>out</em> of the warehouse back into operational tools — e.g. pushing a customer churn score into the CRM (tools: Hightouch, Census).'),
        ('What is EtLT?',
         'A hybrid: light transformations during extraction (masking PII, type fixes, deduplication), load, then heavy business transformations in the warehouse.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What is a data pipeline? What are its components?', 'Data Pipeline Components', minutes=6, cards=[
    definition(
        defbox('A <strong>data pipeline</strong> is an automated series of steps that moves data from sources to '
               'destinations, transforming it along the way. ETL/ELT is one kind of pipeline; others include streaming '
               'pipelines, ML feature pipelines and reverse-ETL syncs.'),
        table(['Component', 'Role', 'Examples'], [
            ['Sources', 'Where data originates', 'OLTP databases, APIs, files, event streams, SaaS apps'],
            ['Ingestion', 'Bring data in (batch or streaming)', 'Sqoop (legacy), Debezium, Kafka Connect, Airbyte, Glue, custom Python'],
            ['Storage', 'Raw and processed data at rest', 'S3 / ADLS / HDFS data lake, warehouse tables'],
            ['Processing', 'Transformations', 'Spark, SQL/dbt, Flink, pandas'],
            ['Orchestration', 'Scheduling, dependencies, retries', 'Airflow, Dagster, Prefect, ADF, cron'],
            ['Serving', 'Make data usable', 'Warehouse marts, BI dashboards, APIs, feature stores'],
            ['Quality &amp; observability', 'Tests, monitoring, alerts, lineage', 'dbt tests, Great Expectations, Monte Carlo, OpenLineage'],
            ['Governance &amp; security', 'Access control, catalog, PII handling', 'IAM, Unity Catalog, Glue Data Catalog, DataHub'],
        ]),
        tags('Data Pipeline', 'Ingestion', 'Orchestration', 'Data Lake', 'Observability', 'Governance'),
    ),
    interview(
        hl('When asked "explain a pipeline you built", walk through these components in order: <strong>source → ingestion → '
           'storage layers → transformations → orchestration → quality checks → consumers</strong>, giving volumes, '
           'frequency and one problem you solved.', 'How to answer project questions'),
    ),
    crossq(
        ('What makes a pipeline "production-grade"?',
         'Idempotent and re-runnable, incremental, monitored with alerts, tested (code and data), documented, versioned in '
         'Git, deployed through CI/CD, secure with secrets management, and with clear ownership and SLAs.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What is the difference between batch processing and stream processing?', 'Batch vs Streaming', minutes=7, cards=[
    definition(
        defbox('<strong>Batch processing</strong> collects data over a period and processes it together on a schedule — '
               'hourly, daily. <strong>Stream processing</strong> processes each event (or small micro-batch) continuously, '
               'within seconds or milliseconds of it occurring.'),
        tags('Batch', 'Streaming', 'Micro-batch', 'Latency', 'Kafka', 'Spark Structured Streaming', 'Flink'),
    ),
    comparison(
        table(['Aspect', 'Batch', 'Streaming'], [
            ['Data', 'Bounded (a day\'s files, a table snapshot)', 'Unbounded (never-ending event flow)'],
            ['Latency', 'Minutes to hours', 'Milliseconds to seconds'],
            ['Trigger', 'Schedule (cron, Airflow)', 'Arrival of events'],
            ['Complexity', 'Simpler to build, test and re-run', 'Harder: state, ordering, late events, exactly-once'],
            ['Cost', 'Cluster runs only during the job', 'Always-on infrastructure'],
            ['Tools', 'Spark batch, SQL/dbt, Hive, Glue', 'Kafka, Spark Structured Streaming, Flink, Kinesis'],
            ['Use cases', 'Daily sales reports, payroll, monthly billing, ML training', 'Fraud detection, live dashboards, alerts, recommendations'],
        ]),
        note('<strong>Micro-batch</strong> (Spark Structured Streaming default) processes small batches every few seconds — '
             'near real-time with batch-like simplicity.'),
    ),
    crossq(
        ('How do you decide between batch and streaming?',
         'Ask what latency the business actually needs and what it is worth. "Real-time" is often requested but a 15-minute '
         'batch is enough. Choose streaming when a decision must be made while the event still matters — fraud, alerts, live pricing.'),
        ('What is event time vs processing time?',
         'Event time is when the event happened (the timestamp in the record); processing time is when the system handles it. '
         'Networks and outages delay events, so correct streaming aggregations use event time with <strong>watermarks</strong> to handle late data.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What is the difference between a data lake, a data warehouse and a lakehouse?', 'Lake vs Warehouse vs Lakehouse', minutes=8, cards=[
    definition(
        defbox('A <strong>data warehouse</strong> stores structured, cleaned, modelled data in tables, optimised for SQL '
               'analytics (schema-on-write).',
               'A <strong>data lake</strong> stores any data — structured, semi-structured, unstructured — as files in cheap '
               'object storage, in raw form (schema-on-read).',
               'A <strong>lakehouse</strong> adds warehouse features (ACID transactions, schema enforcement, updates/deletes, '
               'time travel, fast SQL) on top of lake storage using open <strong>table formats</strong> (Delta Lake, Apache Iceberg, Apache Hudi).'),
        tags('Data Lake', 'Data Warehouse', 'Lakehouse', 'Schema-on-read', 'Schema-on-write', 'Delta Lake', 'Iceberg'),
    ),
    comparison(
        table(['Aspect', 'Data warehouse', 'Data lake', 'Lakehouse'], [
            ['Data types', 'Structured', 'All (CSV, JSON, Parquet, images, logs)', 'All, with tables over files'],
            ['Schema', 'On write', 'On read', 'On write (enforced), evolvable'],
            ['Storage', 'Proprietary, managed', 'Object storage (S3, ADLS, GCS, HDFS)', 'Object storage + open table format'],
            ['ACID / updates', 'Yes', 'No (files are immutable)', 'Yes'],
            ['Cost', 'Higher', 'Lowest', 'Low storage + elastic compute'],
            ['Users', 'Analysts, BI', 'Data scientists, engineers', 'Both'],
            ['Risk', 'Rigid, costly for raw data', 'Becomes a "data swamp" without governance', 'Newer, more moving parts'],
            ['Examples', 'Snowflake, Redshift, BigQuery, Teradata', 'S3/ADLS + Hive/Spark', 'Databricks, Iceberg on Trino/Snowflake, Hudi'],
        ]),
    ),
    crossq(
        ('What is a data swamp?',
         'A data lake where files are dumped without metadata, ownership, quality checks or cataloguing, so nobody can find or trust the data.'),
        ('What is a data mart?',
         'A subject-specific subset of the warehouse for one department — sales mart, finance mart — usually a star schema.'),
        ('Why do lakes use Parquet?',
         'Columnar, compressed, stores schema and statistics, and supports predicate/column pruning — far faster and cheaper for analytics than CSV/JSON.'),
    ),
]),

# ------------------------------------------------------------------ 6
Q('What types of source systems does a data engineer extract from?', 'Source System Types', minutes=6, cards=[
    definition(
        table(['Source type', 'Examples', 'Typical extraction method', 'Watch out for'], [
            ['Relational databases', 'MySQL, PostgreSQL, Oracle, SQL Server', 'JDBC queries (full/incremental), CDC from logs', 'Load on production DB, long-running queries, deletes'],
            ['NoSQL databases', 'MongoDB, Cassandra, DynamoDB', 'Native connectors, change streams', 'Nested/flexible schema'],
            ['REST / GraphQL APIs', 'Salesforce, payment gateways, government portals', 'HTTP with pagination', 'Rate limits, auth tokens, API changes'],
            ['Files', 'CSV/Excel/JSON on SFTP, S3, email', 'File watchers / sensors, batch reads', 'Late, partial, duplicate or malformed files'],
            ['Event streams', 'Kafka, Kinesis, Pub/Sub, clickstream', 'Consumers / streaming jobs', 'Ordering, duplicates, late events'],
            ['SaaS applications', 'Google Analytics, HubSpot, Zoho', 'Managed connectors (Fivetran, Airbyte)', 'Schema changes by vendor'],
            ['Logs &amp; IoT', 'Web server logs, sensors', 'Agents (Fluentd), MQTT, streams', 'Very high volume'],
        ]),
        tags('Source Systems', 'JDBC', 'API', 'Files', 'Event Streams', 'SaaS', 'CDC'),
    ),
    interview(
        p('Before extracting from any source, ask: <strong>volume, frequency of change, how changes are identified '
          '(timestamps? CDC?), are deletes possible, access method and limits, schema stability, and who owns it</strong>. '
          'These answers decide full vs incremental extraction and the whole pipeline design.'),
        title='Questions to Ask About Every Source'),
    crossq(
        ('How do you avoid overloading a production database while extracting?',
         'Read from a replica, extract incrementally, run in off-peak windows, use indexed predicates, paginate large reads, '
         'limit parallel connections — or best, use log-based CDC which reads the binlog instead of querying tables.'),
    ),
]),

])
