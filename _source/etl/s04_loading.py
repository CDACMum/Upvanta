from build import *
from etl.anims import *

SECTION = dict(level='intermediate', title='Loading', questions=[

# ------------------------------------------------------------------ 20
Q('What is the difference between full load, incremental load and upsert?', 'Full vs Incremental vs Upsert', minutes=6, cards=[
    definition(
        table(['Load type', 'What it does', 'Use when'], [
            ['Full load (truncate + reload)', 'Empty the target and load everything again', 'Small tables, reference data, initial load, when changes cannot be tracked'],
            ['Incremental append (insert-only)', 'Add only new rows', 'Immutable data: events, logs, transactions that never change'],
            ['Incremental upsert (merge)', 'Insert new rows and update changed ones by key', 'Mutable entities: customers, orders whose status changes'],
            ['Upsert + delete', 'Also remove/flag rows deleted in source', 'Full sync with CDC'],
            ['Partition overwrite', 'Replace only the affected date partitions', 'Large fact tables, reprocessing a window'],
        ]),
        tags('Full Load', 'Incremental Load', 'Upsert', 'Append', 'Partition Overwrite', 'Initial Load'),
    ),
    interview(
        hl('A typical table goes through an <strong>initial (historical) full load</strong> once, then switches to '
           '<strong>incremental</strong> runs. Design both paths — the initial load often needs batching and different tuning.', 'Remember'),
    ),
    crossq(
        ('What is the risk of truncate-and-load for a table people query all day?',
         'Between TRUNCATE and the end of the load, readers see an empty or partial table. Load into a new table and swap (RENAME), or use a transactional table format.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('What is MERGE / UPSERT? How is it written in different systems?', 'MERGE / UPSERT', minutes=8, cards=[
    definition(
        defbox('<strong>Upsert</strong> = UPDATE if the key exists, otherwise INSERT. The SQL-standard statement is '
               '<code>MERGE</code>, which compares a source (staging) set with a target table on a key and applies '
               'matched / not-matched actions — insert, update and optionally delete — in one atomic statement.'),
        tags('MERGE', 'UPSERT', 'ON DUPLICATE KEY UPDATE', 'ON CONFLICT', 'Delta Lake', 'Idempotent Load'),
    ),
    merge_anim(),
    example(
        sqlrun("""
CREATE TABLE dim_product (product_id INT PRIMARY KEY, name VARCHAR(30), price DECIMAL(8,2), updated_at DATETIME);
INSERT INTO dim_product VALUES (1, 'Pen', 10.00, '2026-10-01'), (2, 'Book', 120.00, '2026-10-01');

CREATE TABLE stg_product (product_id INT, name VARCHAR(30), price DECIMAL(8,2), updated_at DATETIME);
INSERT INTO stg_product VALUES (2, 'Book', 135.00, '2026-10-08'),      -- changed
                               (3, 'Bag',  899.00, '2026-10-08');      -- new

-- MySQL upsert
INSERT INTO dim_product (product_id, name, price, updated_at)
SELECT product_id, name, price, updated_at FROM stg_product
ON DUPLICATE KEY UPDATE
    name       = VALUES(name),
    price      = VALUES(price),
    updated_at = VALUES(updated_at);

SELECT * FROM dim_product;
""", 'MySQL: INSERT … ON DUPLICATE KEY UPDATE'),
        code("""
-- Snowflake / SQL Server / Oracle / BigQuery / Databricks (standard MERGE)
MERGE INTO dim_product AS t
USING stg_product AS s
  ON t.product_id = s.product_id
WHEN MATCHED AND s.updated_at > t.updated_at THEN
  UPDATE SET name = s.name, price = s.price, updated_at = s.updated_at
WHEN NOT MATCHED THEN
  INSERT (product_id, name, price, updated_at)
  VALUES (s.product_id, s.name, s.price, s.updated_at);
-- Optional with CDC: WHEN MATCHED AND s.op = 'D' THEN DELETE
""", 'Standard MERGE'),
        code("""
-- PostgreSQL
INSERT INTO dim_product (product_id, name, price, updated_at)
SELECT product_id, name, price, updated_at FROM stg_product
ON CONFLICT (product_id) DO UPDATE
SET name = EXCLUDED.name, price = EXCLUDED.price, updated_at = EXCLUDED.updated_at
WHERE dim_product.updated_at < EXCLUDED.updated_at;
""", 'PostgreSQL: ON CONFLICT'),
        py("""
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "s3://lake/silver/dim_product")
(target.alias("t")
   .merge(updates_df.alias("s"), "t.product_id = s.product_id")
   .whenMatchedUpdateAll(condition="s.updated_at > t.updated_at")
   .whenNotMatchedInsertAll()
   .execute())
""", 'PySpark + Delta Lake'),
        title='Example'),
    crossq(
        ('Why add "s.updated_at > t.updated_at" to the MATCHED clause?',
         'So an older version arriving late (or a re-run of an old batch) never overwrites newer data.'),
        ('What happens if the source has two rows for the same key in one MERGE?',
         'Most engines raise an error ("multiple source rows matched") or the result is non-deterministic. Deduplicate the staging data first.'),
        ('In MySQL 8.0.20+, what replaces VALUES() in ON DUPLICATE KEY UPDATE?',
         'A row alias: <code>INSERT … SELECT … AS new ON DUPLICATE KEY UPDATE price = new.price</code>. VALUES() still works but is deprecated.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What is idempotency and why is it critical for pipelines?', 'Idempotency', minutes=7, cards=[
    definition(
        defbox('A pipeline run is <strong>idempotent</strong> if running it <strong>once or many times</strong> for the same '
               'input/window produces <strong>the same result</strong> in the target — no duplicates, no double counting.'),
        hl('Pipelines fail and get retried — by Airflow, by an on-call engineer, by a backfill. If a retry doubles the revenue in a dashboard, the pipeline is not production-ready.', 'Why it matters'),
        tags('Idempotency', 'Retry', 'Re-run', 'Backfill', 'Deterministic', 'Exactly-once'),
    ),
    idempotency_anim(),
    comparison(
        table(['Non-idempotent pattern', 'Idempotent alternative'], [
            ['<code>INSERT INTO fact SELECT … FROM stg</code> on every run', 'MERGE on a key, or delete-then-insert the window inside one transaction'],
            ['Append today\'s file to a table', 'Overwrite the <code>load_date=…</code> partition'],
            ['Window defined as "since the last run" using NOW()', 'Window defined by the scheduled interval (data_interval_start → end)'],
            ['Counter columns incremented in place (<code>total = total + x</code>)', 'Recompute aggregates from detail for the window'],
            ['Generating random ids at load', 'Deterministic keys (hash of business key)'],
        ]),
        title='Patterns'),
    example(
        sqlrun("""
CREATE TABLE fact_daily_sales (sale_date DATE, city VARCHAR(20), revenue INT, PRIMARY KEY (sale_date, city));
CREATE TABLE stg_sales (sale_date DATE, city VARCHAR(20), amount INT);
INSERT INTO stg_sales VALUES ('2026-10-08','Pune',500), ('2026-10-08','Pune',300), ('2026-10-08','Delhi',200);

-- The load for one day: delete the window, then insert it, in ONE transaction
START TRANSACTION;
DELETE FROM fact_daily_sales WHERE sale_date = '2026-10-08';
INSERT INTO fact_daily_sales
SELECT sale_date, city, SUM(amount) FROM stg_sales WHERE sale_date = '2026-10-08' GROUP BY sale_date, city;
COMMIT;

-- Run it again (a retry): result is identical, nothing doubled
START TRANSACTION;
DELETE FROM fact_daily_sales WHERE sale_date = '2026-10-08';
INSERT INTO fact_daily_sales
SELECT sale_date, city, SUM(amount) FROM stg_sales WHERE sale_date = '2026-10-08' GROUP BY sale_date, city;
COMMIT;

SELECT * FROM fact_daily_sales;
"""),
        title='Example: Delete-Insert by Window'),
    crossq(
        ('Is MERGE automatically idempotent?',
         'For the same staged data, yes — re-running updates rows to the same values. But it is not idempotent if the staging step itself appends duplicates on each retry, or if the MERGE computes values relative to existing ones (e.g. adding amounts).'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('Truncate-and-load vs append vs partition overwrite — when to use each?', 'Truncate-Load vs Append vs Overwrite', minutes=6, cards=[
    definition(
        table(['Write mode', 'Behaviour', 'Good for', 'Danger'], [
            ['Truncate + load (overwrite table)', 'Replace all data', 'Small dimensions, snapshots, reference tables', 'Empty table during load; expensive for big tables'],
            ['Append', 'Add rows', 'Immutable events', 'Duplicates on retry unless deduplicated'],
            ['Dynamic partition overwrite', 'Replace only the partitions present in the new data', 'Large fact tables partitioned by date; reprocessing a window', 'Wrong partition values can wipe data; static overwrite may replace the WHOLE table'],
            ['Merge / upsert', 'Row-level insert/update/delete', 'Mutable entities, CDC', 'Slower; needs dedup and keys'],
        ]),
        tags('Overwrite', 'Append', 'Dynamic Partition Overwrite', 'insertInto', 'saveAsTable'),
    ),
    example(
        py("""
# Spark: replace ONLY the partitions contained in df (e.g. sale_date=2026-10-06..08)
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

(df.write
   .mode("overwrite")
   .insertInto("sales.fact_daily_sales"))            # table partitioned by sale_date

# Delta Lake: explicit, safer form
(df.write.format("delta")
   .mode("overwrite")
   .option("replaceWhere", "sale_date >= '2026-10-06' AND sale_date <= '2026-10-08'")
   .save("s3://lake/gold/fact_daily_sales"))
""", 'PySpark'),
        warn('With Spark\'s default <code>partitionOverwriteMode = static</code>, <code>mode("overwrite")</code> on a '
             'partitioned table deletes <strong>all</strong> partitions, not just the ones you wrote. Many production '
             'incidents start here.', 'Classic incident'),
        title='Example'),
    crossq(
        ('Which mode would you choose for a daily file that may be re-sent with corrections?',
         'Partition overwrite by file date (or by the business date inside it): the corrected file simply replaces the earlier version — idempotent and simple.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you load large volumes of data efficiently?', 'Bulk Loading', minutes=7, cards=[
    definition(
        defbox('Row-by-row inserts are the slowest way to load data: one network round-trip, one statement parse and often '
               'one commit per row. <strong>Bulk loading</strong> sends data in large batches or uses the database\'s native '
               'loader that writes data pages directly.'),
        table(['Technique', 'Example'], [
            ['Native bulk loader', 'MySQL <code>LOAD DATA INFILE</code>, PostgreSQL <code>COPY</code>, Snowflake/Redshift <code>COPY INTO</code> from S3, BigQuery load jobs'],
            ['Batched inserts', '<code>executemany</code> / multi-row INSERT with 1,000–10,000 rows per statement'],
            ['Fewer commits', 'Commit per batch, not per row'],
            ['Defer indexes &amp; constraints', 'Drop/disable secondary indexes during a huge initial load, rebuild afterwards'],
            ['Parallelism', 'Split by key range or partition and load in parallel (watch for lock contention)'],
            ['Right file format &amp; size', 'Compressed Parquet/CSV files of ~100 MB–1 GB for cloud warehouses'],
            ['Staging then set-based MERGE', 'Bulk-load into staging, then one MERGE into the target'],
        ]),
        tags('Bulk Load', 'LOAD DATA', 'COPY', 'executemany', 'Batch Size', 'Parallel Load'),
    ),
    example(
        pyrun("""
import sqlite3, time

rows = [(i, f"name_{i}", i % 100) for i in range(100_000)]

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT, score INT)")

t = time.perf_counter()
for r in rows[:20_000]:                         # row-by-row with commit each time
    conn.execute("INSERT INTO t VALUES (?, ?, ?)", r)
    conn.commit()
slow = (time.perf_counter() - t) * 5           # scaled to 100k rows

conn.execute("DELETE FROM t"); conn.commit()
t = time.perf_counter()
with conn:                                      # one transaction
    conn.executemany("INSERT INTO t VALUES (?, ?, ?)", rows)
fast = time.perf_counter() - t

print(f"row-by-row (est.): {slow:.2f}s   executemany: {fast:.2f}s   -> ~{slow / fast:.0f}x faster")
print(conn.execute("SELECT COUNT(*) FROM t").fetchone()[0], "rows loaded")
"""),
        note('This demo uses an in-memory SQLite database, so each commit is cheap. Against a real MySQL/PostgreSQL server over '
             'the network, every row-by-row insert also pays a network round-trip and a disk flush, and the gap is typically 50–500×.'),
        code("""
-- MySQL native bulk load (server must allow local_infile)
LOAD DATA LOCAL INFILE '/data/orders_2026-10-08.csv'
INTO TABLE stg_orders
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\\n'
IGNORE 1 LINES
(order_id, customer_id, @amount, order_date)
SET amount = NULLIF(@amount, '');

-- Snowflake from S3
COPY INTO raw.orders
FROM @s3_stage/orders/2026-10-08/
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;
""", 'Native loaders'),
        title='Example'),
    crossq(
        ('Why can too large a batch also be bad?',
         'Huge transactions hold locks longer, bloat undo/redo logs, cause replication lag, and a failure rolls back everything. Tune batch size — often 1k–50k rows for inserts.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('In what order should dimensions and facts be loaded, and why?', 'Load Order: Dimensions then Facts', minutes=5, cards=[
    definition(
        defbox('In a star schema, <strong>dimensions are loaded before facts</strong>. Fact rows store dimension surrogate '
               'keys, so every dimension member a fact refers to must already exist (or be created as an inferred member) '
               'when the fact is loaded.'),
        tags('Load Order', 'Dependencies', 'Dimensions', 'Facts', 'DAG', 'Referential Integrity'),
    ),
    example(
        code("""
extract_all_sources
      │
      ▼
load_staging
      │
      ├──► load_dim_date (static, pre-populated)
      ├──► load_dim_customer (SCD2)      ┐
      ├──► load_dim_product  (SCD2)      ├─ can run in parallel
      └──► load_dim_store    (SCD1)      ┘
                      │
                      ▼
              load_fact_sales  (lookups → surrogate keys)
                      │
                      ▼
          build_aggregates / marts → data quality checks → refresh BI
""", 'Typical DAG order', 'fa-sitemap'),
        title='Example'),
    explanation(
        ul('Load dimensions <strong>in parallel</strong> where they are independent; facts wait for all their dimensions.',
           'Snowflaked dimensions load parent first (category before product).',
           'Aggregates and marts are built after facts, and data-quality checks gate the final publish.',
           'For SCD Type 2 dimensions, the fact lookup must use the version valid on the <strong>fact\'s event date</strong> '
           '(<code>event_date BETWEEN valid_from AND valid_to</code>), not just the current row.'),
        p('See the RDBMS module for star schemas, fact/dimension tables and SCD types in detail.', True),
        title='Rules'),
    crossq(
        ('What if a dimension load fails but the fact load is critical?',
         'Options: block the fact load (strict), or load facts with inferred members / unknown keys and repair later (available). Decide per business requirement and document it.'),
    ),
]),

])
