from build import *
from etl.anims import *

SECTION = dict(level='advanced', title='Architecture', questions=[

# ------------------------------------------------------------------ 26
Q('What is the Medallion Architecture (Bronze, Silver, Gold)?', 'Medallion Architecture', minutes=7, cards=[
    definition(
        defbox('The <strong>medallion architecture</strong> organises a lakehouse into layers of increasing quality. '
               'Data flows <strong>Bronze → Silver → Gold</strong>, and each layer has a clear contract about what it '
               'contains. The term was popularised by Databricks; the same idea is called raw / staging / curated, or '
               'landing / conformed / presentation, elsewhere.'),
        tags('Medallion', 'Bronze', 'Silver', 'Gold', 'Lakehouse', 'Layered Architecture'),
    ),
    medallion(),
    comparison(
        table(['Layer', 'Contains', 'Typical operations', 'Who reads it'], [
            ['Bronze', 'Raw data as ingested + metadata', 'Append; no business logic', 'Data engineers only (debugging, replay)'],
            ['Silver', 'Cleaned, validated, deduplicated, conformed entities', 'Type casting, dedup, MERGE/CDC apply, joins of keys', 'Engineers, data scientists'],
            ['Gold', 'Business-level, aggregated, modelled (star schemas, KPIs)', 'Aggregations, dimensional modelling, metrics', 'Analysts, BI dashboards, apps'],
        ]),
        title='Layers at a Glance'),
    example(
        py("""
from pyspark.sql import functions as F

# BRONZE: land raw JSON as-is, add metadata
raw = (spark.read.json("s3://landing/orders/2026-10-08/")
         .withColumn("_ingested_at", F.current_timestamp())
         .withColumn("_source_file", F.input_file_name()))
raw.write.format("delta").mode("append").save("s3://lake/bronze/orders")

# SILVER: clean, type, dedupe (latest per order_id)
from pyspark.sql import Window
w = Window.partitionBy("order_id").orderBy(F.col("updated_at").desc())
silver = (spark.read.format("delta").load("s3://lake/bronze/orders")
            .filter(F.col("order_id").isNotNull())
            .withColumn("amount", F.col("amount").cast("decimal(12,2)"))
            .withColumn("rn", F.row_number().over(w)).filter("rn = 1").drop("rn"))
silver.write.format("delta").mode("overwrite").save("s3://lake/silver/orders")

# GOLD: business aggregate
gold = (silver.groupBy(F.to_date("order_ts").alias("order_date"), "city")
              .agg(F.sum("amount").alias("revenue"), F.countDistinct("customer_id").alias("buyers")))
gold.write.format("delta").mode("overwrite").save("s3://lake/gold/daily_city_revenue")
""", 'Bronze → Silver → Gold in PySpark'),
        title='Example'),
    crossq(
        ('Is the medallion architecture the same as ETL?',
         'It is an organisation of storage layers. ELT/ETL jobs move data between the layers: ingestion fills bronze, transformation jobs build silver and gold.'),
        ('Do you always need all three layers?',
         'No. Small projects may combine silver and gold; some add a "platinum" or "semantic" layer. What matters is the principle: keep raw data, and separate cleaning from business logic.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What is the difference between Lambda and Kappa architectures?', 'Lambda vs Kappa', minutes=7, cards=[
    definition(
        defbox('Both are architectures for combining large-scale historical processing with low-latency results.',
               '<strong>Lambda</strong> (Nathan Marz) runs a <strong>batch layer</strong> and a <strong>speed (streaming) '
               'layer</strong> in parallel and merges their outputs in a serving layer.',
               '<strong>Kappa</strong> (Jay Kreps) uses <strong>only a streaming layer</strong> over a replayable log; '
               'historical reprocessing is done by replaying the log.'),
        tags('Lambda Architecture', 'Kappa Architecture', 'Batch Layer', 'Speed Layer', 'Kafka', 'Replay'),
    ),
    lambda_kappa(),
    comparison(
        table(['Aspect', 'Lambda', 'Kappa'], [
            ['Layers', 'Batch + speed + serving', 'Stream + serving'],
            ['Codebases', 'Two (batch and streaming)', 'One'],
            ['Reprocessing', 'Re-run batch over all history', 'Replay the log through new code'],
            ['Complexity', 'High — keep two pipelines consistent', 'Lower operationally, but streaming is harder to write'],
            ['Requirement', 'Raw data in a lake', 'Durable log with long retention (Kafka tiered storage)'],
            ['Fits', 'Heavy historical analytics + some real-time views', 'Event-driven systems where everything is a stream'],
        ]),
    ),
    crossq(
        ('Which is more common today?',
         'Pure Lambda is declining. Lakehouses with streaming tables (Delta Live Tables, Spark Structured Streaming into Delta/Iceberg) let one codebase serve both batch and streaming — closer to Kappa in spirit.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('Compare CSV, JSON, Parquet, Avro and ORC file formats', 'File Formats', minutes=8, cards=[
    definition(
        table(['Format', 'Layout', 'Schema', 'Compression', 'Best for'], [
            ['CSV', 'Row, text', 'None (header only)', 'Poor', 'Exchanging small files with humans / legacy systems'],
            ['JSON / JSON Lines', 'Row, text, nested', 'Self-describing, no enforcement', 'Poor', 'APIs, logs, semi-structured data'],
            ['Avro', 'Row, binary', 'Embedded, evolvable', 'Good', 'Kafka messages, write-heavy ingestion, schema evolution'],
            ['Parquet', 'Columnar, binary', 'Embedded', 'Excellent', 'Analytics in lakes/warehouses (Spark, Athena, BigQuery)'],
            ['ORC', 'Columnar, binary', 'Embedded', 'Excellent', 'Hive ecosystem; similar to Parquet'],
        ]),
        tags('CSV', 'JSON', 'Parquet', 'Avro', 'ORC', 'Columnar', 'Row-based', 'Compression'),
    ),
    explanation(
        p('<strong>Why columnar formats win for analytics</strong>: a query like <code>SELECT city, SUM(amount)</code> on a '
          '50-column table reads only 2 columns. Values of one column are similar, so they compress far better '
          '(dictionary and run-length encoding). Parquet also stores <strong>min/max statistics</strong> per row group, so '
          'engines skip blocks that cannot match a filter.'),
        p('<strong>Why row formats win for ingestion</strong>: writing one complete record at a time is natural for '
          'streams; Avro\'s compact binary encoding and schema evolution rules make it the standard for Kafka.', True),
    ),
    example(
        pyrun("""
import os, pandas as pd, numpy as np

n = 200_000
rng = np.random.default_rng(1)
df = pd.DataFrame({
    "order_id": np.arange(n),
    "city": rng.choice(["Pune", "Mumbai", "Delhi", "Chennai"], n),
    "status": rng.choice(["PAID", "PENDING", "CANCELLED"], n),
    "amount": rng.integers(100, 5000, n),
})
df.to_csv("orders.csv", index=False)
df.to_json("orders.jsonl", orient="records", lines=True)
df.to_parquet("orders.parquet", index=False)          # snappy compression by default

for f in ["orders.csv", "orders.jsonl", "orders.parquet"]:
    print(f"{f:<16} {os.path.getsize(f) / 1e6:6.2f} MB")

cols = pd.read_parquet("orders.parquet", columns=["city", "amount"])   # column pruning
print(cols.groupby("city")["amount"].sum().sort_index().to_dict())
"""),
        title='Example: Same Data, Different Sizes'),
    crossq(
        ('What are row groups and why do they matter?',
         'A Parquet file is split into row groups (e.g. 128 MB); each stores column chunks with min/max stats. Engines skip whole row groups whose stats do not match the filter — "predicate pushdown". Sorting data on a common filter column makes this much more effective.'),
        ('Why is CSV dangerous for data pipelines?',
         'No types (everything is text), ambiguous dates, delimiters and quotes inside values, encoding issues, no schema, and no compression. Convert to Parquet as early as possible.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('How does partitioning work in a data lake, and what is the small-files problem?', 'Partitioning & Small Files', minutes=8, cards=[
    definition(
        defbox('<strong>Partitioning</strong> stores a table as sub-folders based on the values of one or more columns '
               '(<code>order_date=2026-10-08/</code>). Queries filtering on that column read only the matching folders — '
               '<strong>partition pruning</strong>.',
               'The <strong>small-files problem</strong> occurs when a table consists of thousands or millions of tiny files '
               '(KBs instead of ~128 MB–1 GB). Every file costs a metadata lookup, an open/close and task scheduling, so '
               'queries become slow and storage listing becomes expensive.'),
        tags('Partitioning', 'Partition Pruning', 'Small Files', 'Compaction', 'Over-partitioning', 'Z-order'),
    ),
    partition_pruning(),
    explanation(
        table(['Do', 'Avoid'], [
            ['Partition by a low/medium-cardinality column used in most filters (date)', 'Partitioning by high-cardinality columns (customer_id, order_id) → millions of folders'],
            ['Aim for partitions of at least ~1 GB of data', 'Partitioning small tables at all'],
            ['Compact small files periodically (Delta <code>OPTIMIZE</code>, Iceberg <code>rewrite_data_files</code>)', 'Streaming jobs writing a file every few seconds without compaction'],
            ['Control output files: <code>repartition("order_date")</code> before writing, or <code>maxRecordsPerFile</code>', 'Writing with 2,000 shuffle partitions × 30 dates = 60,000 files'],
            ['Use clustering / Z-ordering / sorting for other filter columns', 'Nesting many partition levels (year/month/day/hour/city)'],
        ]),
        title='Good Practice'),
    example(
        py("""
# Write one well-sized file set per date instead of hundreds of tiny files
(df.repartition("order_date")                      # all rows of a date go to the same task
   .write.mode("overwrite")
   .partitionBy("order_date")
   .parquet("s3://lake/silver/orders"))

# Delta Lake maintenance
spark.sql("OPTIMIZE delta.`s3://lake/silver/orders` ZORDER BY (customer_id)")
spark.sql("VACUUM delta.`s3://lake/silver/orders` RETAIN 168 HOURS")
""", 'PySpark / Delta Lake'),
        title='Example'),
    crossq(
        ('repartition vs coalesce before writing?',
         '<code>coalesce(n)</code> reduces partitions without a full shuffle (cheap, but can create uneven files); <code>repartition(n or col)</code> does a full shuffle and gives evenly sized output. Use repartition by the partition column for balanced files per folder.'),
        ('Partitioning vs bucketing?',
         'Partitioning creates folders by column value; bucketing hashes a column into a fixed number of files within each partition, which helps joins and aggregations on that key (Hive/Spark bucketed tables).'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What are open table formats like Delta Lake, Apache Iceberg and Apache Hudi?', 'Table Formats: Delta, Iceberg, Hudi', minutes=7, cards=[
    definition(
        defbox('Plain Parquet folders have no transactions: two jobs writing at once can corrupt a table, a failed job '
               'leaves partial files, and you cannot UPDATE or DELETE rows. An <strong>open table format</strong> adds a '
               '<strong>metadata/transaction log</strong> on top of Parquet files that records exactly which files make up '
               'each version of the table.'),
        table(['Capability', 'What it enables'], [
            ['ACID transactions', 'Readers never see half-written data; concurrent writers are coordinated'],
            ['UPDATE / DELETE / MERGE', 'CDC upserts, GDPR deletions, SCD2 in the lake'],
            ['Schema enforcement &amp; evolution', 'Reject bad writes; add columns safely'],
            ['Time travel', 'Query the table as of a version or timestamp; roll back bad loads'],
            ['File-level statistics &amp; compaction', 'Data skipping, OPTIMIZE / clustering'],
            ['Streaming + batch on one table', 'Same table is a streaming sink and a batch source'],
        ]),
        tags('Delta Lake', 'Apache Iceberg', 'Apache Hudi', 'ACID', 'Time Travel', 'Transaction Log'),
    ),
    comparison(
        table(['', 'Delta Lake', 'Apache Iceberg', 'Apache Hudi'], [
            ['Origin', 'Databricks', 'Netflix', 'Uber'],
            ['Metadata', '_delta_log JSON + checkpoints', 'Metadata files, manifest lists, manifests', 'Timeline in .hoodie folder'],
            ['Strengths', 'Tight Spark/Databricks integration, simplicity', 'Engine-neutral (Spark, Trino, Flink, Snowflake, Athena), hidden partitioning, partition evolution', 'Record-level upserts, incremental pulls, merge-on-read'],
        ]),
    ),
    example(
        code("""
-- Delta Lake / Spark SQL
MERGE INTO silver.orders t USING updates s ON t.order_id = s.order_id
WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *;

DESCRIBE HISTORY silver.orders;                       -- every version with operation & metrics
SELECT * FROM silver.orders VERSION AS OF 41;         -- time travel
SELECT * FROM silver.orders TIMESTAMP AS OF '2026-10-07 23:00:00';
RESTORE TABLE silver.orders TO VERSION AS OF 41;      -- undo a bad load

DELETE FROM silver.customers WHERE customer_id = 'C101';   -- right-to-be-forgotten request
""", 'Spark SQL on Delta Lake'),
        title='Example'),
    crossq(
        ('Copy-on-write vs merge-on-read?',
         '<strong>Copy-on-write</strong> rewrites affected files on update — slower writes, fastest reads. <strong>Merge-on-read</strong> writes small delta files and merges them at read time — fast writes, slower reads until compaction. Hudi and Iceberg (and Delta deletion vectors) support both styles.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('What is orchestration? Explain DAGs, scheduling and dependencies (Airflow)', 'Orchestration & DAGs', minutes=8, cards=[
    definition(
        defbox('<strong>Orchestration</strong> is the automated coordination of pipeline tasks: <strong>when</strong> they '
               'run (schedules, sensors, events), in <strong>what order</strong> (dependencies), with what '
               '<strong>parameters</strong>, and what happens on <strong>failure</strong> (retries, alerts).',
               'Workflows are modelled as a <strong>DAG — Directed Acyclic Graph</strong> of tasks. Apache Airflow is the '
               'most widely used orchestrator; others include Dagster, Prefect, Azure Data Factory, AWS Step Functions and Databricks Workflows.'),
        tags('Orchestration', 'DAG', 'Airflow', 'Scheduler', 'Sensor', 'Retries', 'Backfill'),
    ),
    dag_anim(),
    example(
        py("""
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

default_args = {"owner": "data-eng", "retries": 2, "retry_delay": timedelta(minutes=5)}

@dag(schedule="30 1 * * *", start_date=datetime(2026, 10, 1), catchup=False,
     default_args=default_args, tags=["sales"])
def daily_sales():

    @task
    def extract_orders(data_interval_start=None, data_interval_end=None):
        # incremental window comes from the run itself -> reproducible re-runs
        return extract(f"updated_at >= '{data_interval_start}' AND updated_at < '{data_interval_end}'")

    @task
    def load_dim_customer(): ...

    @task
    def stage_orders(path): ...

    load_fact = SQLExecuteQueryOperator(task_id="load_fact_sales", conn_id="warehouse",
                                        sql="sql/merge_fact_sales.sql")
    dq = SQLExecuteQueryOperator(task_id="dq_checks", conn_id="warehouse", sql="sql/dq_checks.sql")

    staged = stage_orders(extract_orders())
    [load_dim_customer(), staged] >> load_fact >> dq

daily_sales()
""", 'Airflow DAG (TaskFlow API)'),
        title='Example'),
    crossq(
        ('Why must the graph be acyclic?',
         'A cycle (A waits for B, B waits for A) has no valid execution order and would never finish.'),
        ('What is catchup in Airflow?',
         'With <code>catchup=True</code>, when a DAG is enabled with a past start_date, Airflow creates a run for every missed interval. Useful for backfills, dangerous if unintended.'),
        ('Cron expression "30 1 * * *" means?',
         'Every day at 01:30 (minute 30, hour 1). Fields: minute, hour, day-of-month, month, day-of-week.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What is a backfill and how do you reprocess historical data safely?', 'Backfills & Reprocessing', minutes=6, cards=[
    definition(
        defbox('A <strong>backfill</strong> runs a pipeline for past periods — to load history for a new table, to fix data '
               'after a bug, or after a source re-sends corrected data. Doing this safely depends on the pipeline being '
               '<strong>parameterised by time window</strong> and <strong>idempotent</strong>.'),
        tags('Backfill', 'Reprocessing', 'Idempotency', 'Parameterised Window', 'Airflow'),
    ),
    explanation(
        ul('<strong>Parameterise everything by the logical date / window</strong> — never use NOW() or "latest" inside the job.',
           '<strong>Write idempotently</strong>: overwrite the date partition or MERGE, so a backfill replaces old results instead of duplicating them.',
           '<strong>Respect dependencies</strong>: backfill upstream tables first, then downstream ones (or the DAG in order).',
           '<strong>Limit concurrency</strong> so the backfill does not overload the source or the cluster (<code>max_active_runs</code>).',
           '<strong>Use the right reference data</strong>: SCD2 lookups must use versions valid on the historical date.',
           '<strong>Validate and communicate</strong>: compare totals before/after, and warn consumers that numbers will change.'),
        code("""
# Airflow CLI: re-run the DAG for the first week of October
airflow dags backfill daily_sales \\
    --start-date 2026-10-01 --end-date 2026-10-07 \\
    --reset-dagruns
""", 'Terminal', 'fa-terminal'),
        title='How to Backfill Safely'),
    crossq(
        ('What makes a pipeline impossible to backfill?',
         'Reading "current" state that has since changed (e.g. a dimension without history), using now() for windows, appending instead of overwriting, or sources that no longer keep old data. Keeping a raw/bronze layer solves the last one.'),
    ),
]),

])
