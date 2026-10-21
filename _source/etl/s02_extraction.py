from build import *
from etl.anims import *

SECTION = dict(level='basic', title='Extraction', questions=[

# ------------------------------------------------------------------ 7
Q('What is the difference between full extraction and incremental extraction?', 'Full vs Incremental Extraction', minutes=6, cards=[
    definition(
        defbox('<strong>Full extraction</strong> reads the entire source dataset every run.',
               '<strong>Incremental (delta) extraction</strong> reads only the records that were <strong>inserted, updated '
               '(or deleted)</strong> since the previous successful run.'),
        tags('Full Load', 'Incremental Load', 'Delta', 'Watermark', 'CDC'),
    ),
    comparison(
        table(['Aspect', 'Full extraction', 'Incremental extraction'], [
            ['Data read per run', 'Everything', 'Only changes'],
            ['Source load / run time', 'High, grows with table size', 'Low, grows with change volume'],
            ['Complexity', 'Simple', 'Needs a change indicator and state tracking'],
            ['Detects deletes', 'Yes (by comparison)', 'Not with timestamps alone — needs CDC or soft deletes'],
            ['Good for', 'Small tables, reference data, first (initial) load, sources with no change tracking', 'Large, frequently changing tables'],
        ]),
    ),
    example(
        sqlrun("""
CREATE TABLE orders (
  order_id INT PRIMARY KEY, amount DECIMAL(10,2), status VARCHAR(10),
  updated_at DATETIME NOT NULL,
  INDEX idx_updated_at (updated_at)               -- essential for incremental queries
);
INSERT INTO orders VALUES
 (1, 500, 'PAID',    '2026-10-06 09:00:00'),
 (2, 750, 'PAID',    '2026-10-07 18:30:00'),
 (3, 120, 'PENDING', '2026-10-08 08:15:00'),
 (4, 999, 'PAID',    '2026-10-08 10:45:00');

-- Full extraction
SELECT COUNT(*) AS full_rows FROM orders;

-- Incremental: everything changed after the last successful run
SET @last_run = '2026-10-07 23:59:59';
SELECT order_id, amount, status, updated_at
FROM orders
WHERE updated_at > @last_run
ORDER BY updated_at;
"""),
        title='Example'),
    crossq(
        ('Why is an index on updated_at important?',
         'Without it, the incremental query scans the whole table — defeating the purpose. With the index, only the changed rows are read.'),
        ('Can you rely on updated_at being correct?',
         'Only if every write path updates it. Bulk fixes run directly in SQL, triggers that are disabled, or app bugs can '
         'change rows without changing updated_at. Verify with periodic full reconciliations, or use log-based CDC.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How does a watermark (high-water mark) based incremental load work?', 'Watermark Incremental Load', minutes=8, cards=[
    definition(
        defbox('A <strong>watermark</strong> is the highest value of a change-tracking column (e.g. <code>updated_at</code> '
               'or an auto-increment <code>id</code>) that was successfully processed in the previous run. It is stored in a '
               'small <strong>control (audit) table</strong>. Each run extracts rows above the stored watermark, then '
               'advances the watermark <strong>only after the load succeeds</strong>.'),
        tags('Watermark', 'High-water Mark', 'Control Table', 'Incremental Load', 'Overlap Window'),
    ),
    watermark(),
    example(
        sqlrun("""
CREATE TABLE etl_watermark (table_name VARCHAR(50) PRIMARY KEY, last_value DATETIME, updated_on DATETIME);
INSERT INTO etl_watermark VALUES ('orders', '2026-10-07 23:59:59', NOW());

CREATE TABLE src_orders (order_id INT PRIMARY KEY, amount DECIMAL(10,2), updated_at DATETIME, INDEX(updated_at));
INSERT INTO src_orders VALUES (1, 500, '2026-10-06 09:00:00'), (2, 750, '2026-10-08 08:15:00'),
                              (3, 120, '2026-10-08 10:45:00');
CREATE TABLE stg_orders LIKE src_orders;

-- 1) Read the watermark
SELECT last_value INTO @wm FROM etl_watermark WHERE table_name = 'orders';

-- 2) Fix the upper bound BEFORE extracting (rows written during the run go to the next run)
SET @upper = (SELECT MAX(updated_at) FROM src_orders);

-- 3) Extract the window (wm, upper]
INSERT INTO stg_orders
SELECT * FROM src_orders WHERE updated_at > @wm AND updated_at <= @upper;

-- 4) Advance the watermark only after the load succeeded
UPDATE etl_watermark SET last_value = @upper, updated_on = NOW() WHERE table_name = 'orders';

SELECT order_id, updated_at FROM stg_orders;
SELECT table_name, last_value FROM etl_watermark;
"""),
        title='Example: Watermark Load in SQL'),
    explanation(
        ul('<strong>Advance the watermark last</strong>. If the job fails midway, the next run re-reads the same window — so the load must be idempotent (MERGE/upsert).',
           '<strong>Use a fixed upper bound</strong> captured at the start, so rows committed during extraction are not half-included.',
           '<strong>Overlap / lookback window</strong>: subtract a few minutes from the watermark to catch long transactions that committed late with an earlier timestamp; the upsert removes the duplicates.',
           '<strong>Store per table</strong> (and per source) in a control table with run id, row counts and status — this doubles as an audit log.',
           '<strong>Auto-increment id as watermark</strong> works for append-only tables (logs, events) but misses updates.'),
        title='Design Rules'),
    crossq(
        ('Why use > and not >= on the watermark?',
         '<code>&gt;</code> avoids re-reading the last row every run. But if many rows share the exact same timestamp and the '
         'previous run stopped part-way through them, some could be missed — which is why an overlap window plus idempotent upsert is the robust choice.'),
        ('In Airflow, where would the watermark come from?',
         'Often from the run\'s data interval: <code>data_interval_start</code> and <code>data_interval_end</code>. Each run '
         'processes a fixed, reproducible window — backfills and re-runs then become trivial.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What is Change Data Capture (CDC)? Explain its types', 'Change Data Capture (CDC)', minutes=9, cards=[
    definition(
        defbox('<strong>Change Data Capture</strong> is the set of techniques for identifying and capturing the '
               '<strong>inserts, updates and deletes</strong> made in a source database, so that only the changes are '
               'propagated downstream — ideally in near real time.'),
        table(['CDC type', 'How it works', 'Pros', 'Cons'], [
            ['Timestamp / query-based', 'Query rows where <code>updated_at &gt; watermark</code>', 'Simple, no special access', 'Misses hard deletes; misses intermediate changes; load on source; depends on correct timestamps'],
            ['Trigger-based', 'DB triggers write every change into a shadow/audit table', 'Captures deletes and every change', 'Adds overhead to every write; triggers must be maintained'],
            ['Snapshot diff', 'Compare today\'s full extract with yesterday\'s', 'Works with any source', 'Expensive for large tables; only daily granularity'],
            ['Log-based', 'Read the database transaction log (MySQL binlog, PostgreSQL WAL, Oracle redo)', 'Captures everything incl. deletes, in order, with very low source impact, near real time', 'Needs log access/permissions and retention; more infrastructure'],
        ]),
        tags('CDC', 'Binlog', 'WAL', 'Debezium', 'Kafka Connect', 'Log-based CDC', 'Triggers'),
    ),
    cdc_flow(),
    example(
        code("""
{
  "op": "u",                                  // c = create, u = update, d = delete, r = snapshot read
  "ts_ms": 1791479700123,
  "source": {"db": "shop", "table": "orders", "file": "binlog.000042", "pos": 18734},
  "before": {"order_id": 5001, "status": "PENDING", "amount": 1499.00},
  "after":  {"order_id": 5001, "status": "PAID",    "amount": 1499.00}
}
""", 'A Debezium change event (simplified)', 'fa-code'),
        pyrun("""
# Applying a stream of CDC events to a target (key -> current row)
events = [
    {"op": "c", "key": 1, "after": {"status": "PENDING"}},
    {"op": "c", "key": 2, "after": {"status": "PENDING"}},
    {"op": "u", "key": 1, "after": {"status": "PAID"}},
    {"op": "d", "key": 2, "after": None},
    {"op": "c", "key": 3, "after": {"status": "PAID"}},
]
target = {}
for e in events:                       # events must be applied IN ORDER per key
    if e["op"] == "d":
        target.pop(e["key"], None)
    else:
        target[e["key"]] = e["after"]
print(target)
""", 'Applying CDC events'),
        title='Example'),
    crossq(
        ('What MySQL settings does log-based CDC need?',
         '<code>binlog_format = ROW</code>, <code>binlog_row_image = FULL</code>, binary logging enabled with enough retention, '
         'a unique <code>server_id</code>, and a user with REPLICATION SLAVE / REPLICATION CLIENT privileges.'),
        ('What is the initial snapshot in CDC?',
         'Before streaming changes, the connector reads the current full table (op = "r") and records the log position, so '
         'the target starts complete and then stays in sync from that exact point.'),
        ('Name some CDC tools.',
         'Debezium (open source, Kafka Connect), AWS DMS, Oracle GoldenGate, Qlik Replicate, Fivetran/Airbyte log-based connectors, Striim; Databricks and Snowflake also have native CDC ingestion features.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How do you handle deleted records in the source during incremental loads?', 'Handling Source Deletes', minutes=7, cards=[
    definition(
        defbox('A timestamp-based incremental query only sees rows that <strong>still exist</strong>. If a row is '
               '<strong>hard-deleted</strong> in the source, it simply disappears and the target keeps a stale copy forever. '
               'Deletes need a deliberate strategy.'),
        table(['Strategy', 'How', 'When'], [
            ['Soft delete in source', 'Source sets <code>is_deleted = 1</code> and updates updated_at instead of DELETE', 'If you can influence the application'],
            ['Log-based CDC', 'Capture DELETE events (op = "d") from the binlog/WAL', 'Best general solution'],
            ['Trigger / audit table', 'A DELETE trigger writes the key into a deletes table', 'When CDC is not available'],
            ['Key comparison (anti-join)', 'Periodically extract all primary keys from source; keys in target but not in source are deleted', 'Small/medium tables, or weekly reconciliation'],
            ['Full reload', 'Truncate and reload the whole table', 'Small tables'],
        ]),
        tags('Hard Delete', 'Soft Delete', 'Tombstone', 'Anti-join', 'CDC', 'Reconciliation'),
    ),
    example(
        sqlrun("""
CREATE TABLE src_keys (customer_id INT PRIMARY KEY);            -- keys extracted from source today
INSERT INTO src_keys VALUES (1), (2), (4);

CREATE TABLE dim_customer (customer_id INT PRIMARY KEY, name VARCHAR(20), is_deleted TINYINT DEFAULT 0);
INSERT INTO dim_customer (customer_id, name) VALUES (1,'Asha'), (2,'Rohit'), (3,'Meera'), (4,'Zoya');

-- Find rows that no longer exist in the source (anti-join)
SELECT d.customer_id, d.name
FROM dim_customer d
LEFT JOIN src_keys s ON s.customer_id = d.customer_id
WHERE s.customer_id IS NULL;

-- Mark them as deleted in the warehouse (keep history)
UPDATE dim_customer d
LEFT JOIN src_keys s ON s.customer_id = d.customer_id
SET d.is_deleted = 1
WHERE s.customer_id IS NULL;

SELECT * FROM dim_customer;
"""),
        title='Example: Detecting Deletes by Key Comparison'),
    crossq(
        ('Should the warehouse also hard-delete?',
         'Usually not — mark as deleted (soft delete, or close the SCD2 record) so historical facts still join to their '
         'dimension. Exception: legal deletion requests (right to be forgotten), where data must be physically removed or anonymised.'),
        ('What is a tombstone?',
         'A marker record meaning "this key was deleted". In Kafka/Debezium it is a message with the key and a null value, which also lets log compaction remove the key.'),
    ),
]),

# ------------------------------------------------------------------ 11
Q('What is a landing zone / raw layer, and why keep raw data?', 'Landing Zone & Raw Layer', minutes=5, cards=[
    definition(
        defbox('The <strong>landing zone</strong> (raw, bronze layer) is where extracted data is first stored '
               '<strong>exactly as received</strong> — same format, no transformations — usually in object storage, '
               'partitioned by source and load date.'),
        code("""
s3://cdac-datalake/raw/
  mysql/shop/orders/load_date=2026-10-08/part-0000.parquet
  api/crm/contacts/load_date=2026-10-08/page-001.json
  sftp/vendor_x/stock/load_date=2026-10-08/stock_20261008.csv
""", 'Typical raw layout', 'fa-folder-tree'),
        tags('Landing Zone', 'Raw Layer', 'Bronze', 'Immutable', 'Replay', 'Audit'),
    ),
    explanation(
        ul('<strong>Reprocessing</strong>: when a transformation bug is found, rebuild downstream tables from raw without hitting the source again (the source may no longer have the old data).',
           '<strong>Auditability</strong>: prove exactly what the source sent on a given day.',
           '<strong>Decoupling</strong>: extraction and transformation can fail and retry independently.',
           '<strong>New use cases</strong>: a column nobody needed last year is still available.',
           'Keep raw data <strong>immutable and append-only</strong>; add metadata columns such as <code>_load_ts</code>, <code>_source_file</code>, <code>_batch_id</code>.',
           'Apply <strong>lifecycle rules</strong> (move to cheaper storage after N days, delete after the retention period) and protect PII with access controls.'),
        title='Why Keep Raw Data'),
    crossq(
        ('Should raw data be stored as CSV/JSON or converted to Parquet?',
         'Store files exactly as received when auditability matters (original CSV/JSON); many teams additionally write a '
         'Parquet copy in bronze for efficient processing. Database extracts are usually written straight to Parquet/Avro.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What is a staging area and why is it used?', 'Staging Area', minutes=5, cards=[
    definition(
        defbox('A <strong>staging area</strong> is an intermediate storage location (tables or files) where extracted data '
               'is held <strong>temporarily</strong> for cleansing, validation and transformation before being loaded into '
               'the final target tables.'),
        tags('Staging', 'Intermediate Tables', 'Validation', 'Isolation', 'Swap'),
    ),
    explanation(
        ul('<strong>Isolation from sources</strong>: extract quickly, release the source, then transform at leisure.',
           '<strong>Validation before publishing</strong>: run quality checks on staging; only load the target if they pass, so consumers never see half-loaded or bad data.',
           '<strong>Set-based operations</strong>: join and merge large batches efficiently inside the database.',
           '<strong>Restartability</strong>: if the load fails, the staged data is still there.',
           '<strong>Atomic publish</strong>: build a new table in staging and swap it in with a rename.'),
        sqlrun("""
CREATE TABLE sales_summary     (city VARCHAR(20), revenue DECIMAL(12,2));
INSERT INTO sales_summary VALUES ('Pune', 1000);

-- Build the new version on the side
CREATE TABLE sales_summary_new (city VARCHAR(20), revenue DECIMAL(12,2));
INSERT INTO sales_summary_new VALUES ('Pune', 1250), ('Delhi', 800);

-- Validate, then swap atomically: readers never see an empty or partial table
RENAME TABLE sales_summary TO sales_summary_old, sales_summary_new TO sales_summary;
DROP TABLE sales_summary_old;

SELECT * FROM sales_summary;
""", 'Atomic swap pattern'),
        title='Why Use Staging'),
    crossq(
        ('Staging vs landing zone?',
         'Landing/raw is the permanent, as-received copy. Staging is a working area, usually truncated or overwritten each run, holding data being prepared for the next layer.'),
    ),
]),

])
