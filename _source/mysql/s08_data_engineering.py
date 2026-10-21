import os, glob
from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

# SELECT … INTO OUTFILE refuses to overwrite, so clear old export files before each build
for f in glob.glob('/tmp/orders_export.csv'):
    os.remove(f)

def binlog_update_event():
    """Decode the newest binlog (rotated just before the example) and return the shell command plus
    the real row event for the accounts UPDATE run by the example above."""
    import subprocess
    datadir = subprocess.run(['mysql', '-uroot', '-NBe', 'SELECT @@datadir'], capture_output=True, text=True).stdout.strip()
    last = subprocess.run(['mysql', '-uroot', '-NBe', 'SHOW BINARY LOGS'], capture_output=True, text=True).stdout.split()[-3]
    dump = subprocess.run(['mysqlbinlog', '--base64-output=DECODE-ROWS', '-vv', f'{datadir}{last}'],
                          capture_output=True, text=True).stdout.splitlines()
    start = max(i for i, l in enumerate(dump) if l.startswith('### UPDATE `upvanta`.`accounts`'))
    block = [dump[start]]
    for l in dump[start + 1:]:
        if not l.startswith('###'):
            break
        block.append(l)
    cmd = f"""
# Decode the row events of the current binlog file (run in the MySQL data directory)
mysqlbinlog --base64-output=DECODE-ROWS -vv {last}
"""
    return code(cmd, 'Shell', 'fa-terminal') + output('\n'.join(block), "Output (the UPDATE event, decoded from this server's binlog)")


SECTION = dict(level='expert', title='MySQL for Data Engineering', questions=[

# ------------------------------------------------------------------ 50
Q('How do you do an upsert in MySQL? Compare ON DUPLICATE KEY UPDATE, REPLACE and INSERT IGNORE', 'Upserts', minutes=8, cards=[
    definition(
        defbox('An <strong>upsert</strong> inserts a row if its key is new and updates it if the key already exists. MySQL has '
               'no MERGE statement; it offers <strong>INSERT … ON DUPLICATE KEY UPDATE</strong>, <strong>REPLACE</strong> and '
               '<strong>INSERT IGNORE</strong>. All of them detect "exists" through a <strong>PRIMARY KEY or UNIQUE index</strong>.'),
        tags('Upsert', 'ON DUPLICATE KEY UPDATE', 'REPLACE', 'INSERT IGNORE', 'Idempotent Load'),
    ),
    upsert_anim(),
    example(
        sqlrun("""
CREATE TABLE accounts (id INT PRIMARY KEY, name VARCHAR(20), balance INT,
                       updated_at DATETIME DEFAULT '2026-01-01 00:00:00');
INSERT INTO accounts (id, name, balance) VALUES (1, 'Asha', 500), (2, 'Ravi', 300);

-- Upsert (MySQL 8.0.19+ row alias syntax)
INSERT INTO accounts (id, name, balance) VALUES (2, 'Ravi', 450), (3, 'Neha', 200) AS new
ON DUPLICATE KEY UPDATE balance = new.balance, updated_at = '2026-10-11 09:00:00';
SELECT ROW_COUNT() AS affected;          -- 2 for the update + 1 for the insert
SELECT * FROM accounts;

-- INSERT IGNORE: skips the conflicting row (with a warning), inserts the rest
INSERT IGNORE INTO accounts (id, name, balance) VALUES (1, 'Asha', 999), (4, 'Imran', 50);
SELECT id, balance FROM accounts WHERE id IN (1, 4);

-- REPLACE: deletes row 2 and inserts a new one; updated_at falls back to the default
REPLACE INTO accounts (id, name, balance) VALUES (2, 'Ravi', 475);
SELECT * FROM accounts WHERE id = 2;
"""),
        title='Example'),
    comparison(
        table(['Statement', 'On key conflict', 'Watch out for'], [
            ['INSERT … ON DUPLICATE KEY UPDATE', 'Updates the listed columns of the existing row', 'Any UNIQUE key can trigger it, not just the PK'],
            ['REPLACE INTO', 'Deletes the old row, inserts the new one', 'Unlisted columns reset; DELETE triggers and cascades fire; new auto-increment id'],
            ['INSERT IGNORE', 'Silently skips the row', 'Also turns other errors (bad dates, too-long strings) into warnings'],
        ]),
    ),
    real_world(p('Idempotent loads: an incremental batch may be re-run after a failure. With ON DUPLICATE KEY UPDATE on the '
                 'business key the second run leaves the table unchanged instead of creating duplicates. Add '
                 '<code>WHERE new.updated_at &gt; accounts.updated_at</code>-style logic (via IF()) if older data must not overwrite newer.')),
    crossq(
        ('What was the syntax before 8.0.19?', '<code>ON DUPLICATE KEY UPDATE balance = VALUES(balance)</code>. VALUES() still works but is deprecated.'),
        ('How do you upsert from a staging table?', '<code>INSERT INTO target (…) SELECT … FROM staging ON DUPLICATE KEY UPDATE col = VALUES(col)</code> (or with a row alias). Do it in batches for very large staging tables.'),
    ),
]),

# ------------------------------------------------------------------ 51
Q('How do you bulk load and export large data in MySQL efficiently?', 'Bulk Load & Export', minutes=8, cards=[
    definition(
        defbox('<strong>LOAD DATA INFILE</strong> reads a CSV/TSV file straight into a table and is typically 10–20× faster '
               'than individual INSERTs. <strong>SELECT … INTO OUTFILE</strong> writes a query result to a file on the server. '
               'From application code, use <strong>multi-row INSERTs</strong> in batches inside transactions.'),
        tags('LOAD DATA INFILE', 'LOCAL INFILE', 'INTO OUTFILE', 'Batch Insert', 'secure_file_priv'),
    ),
    example(
        sqlrun("""
-- Export a query result as CSV (file is written on the MySQL server)
SELECT order_id, customer_id, order_date, amount, status
INTO OUTFILE '/tmp/orders_export.csv'
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\\n'
FROM orders WHERE status = 'DELIVERED';

-- Load it into a new table
CREATE TABLE orders_copy LIKE orders;
LOAD DATA INFILE '/tmp/orders_export.csv'
INTO TABLE orders_copy
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\\n'
(order_id, customer_id, order_date, amount, status);

SELECT COUNT(*) AS loaded, SUM(amount) AS total FROM orders_copy;
""", setup=SALES),
        title='Example: Export and Re-load a CSV'),
    explanation(
        ul('<code>LOAD DATA LOCAL INFILE</code> reads the file from the <strong>client</strong> machine (needs <code>local_infile=ON</code> on both sides). Without LOCAL the file must be on the server, inside <code>secure_file_priv</code>.',
           'Use <code>IGNORE 1 LINES</code> to skip a header row, and <code>SET col = NULLIF(@var, \'\')</code> to transform values while loading.',
           'From Python/Java: <code>executemany</code> / JDBC batching with <code>rewriteBatchedStatements=true</code>, commit every 5,000–50,000 rows.',
           'For a one-off huge load into an empty table: load in primary-key order, and create secondary indexes after the load.',
           'Check warnings after loading (<code>SHOW WARNINGS</code>): truncated or invalid values are often only warnings.'),
        title='Tips'),
    crossq(
        ('Why is LOAD DATA so much faster than INSERTs?', 'One statement parses the whole file: no per-row network round trip, SQL parsing or commit, and InnoDB can write rows in large batches.'),
        ('How would you export a 500 GB table for a data lake?', 'Not with one SELECT. Use parallel chunked reads by primary-key ranges (Spark JDBC, MySQL Shell <code>util.exportTable</code>, or <code>util.dumpTables</code>), ideally from a replica, written as compressed Parquet.'),
    ),
]),

# ------------------------------------------------------------------ 52
Q('How do you store and query JSON data in MySQL?', 'JSON in MySQL', minutes=8, cards=[
    definition(
        defbox('MySQL 5.7+ has a native <strong>JSON</strong> data type that validates documents and stores them in a binary '
               'format for fast access. You read fields with <code>JSON_EXTRACT</code> or the <code>-&gt;</code> / '
               '<code>-&gt;&gt;</code> operators, flatten arrays into rows with <code>JSON_TABLE</code>, and build JSON with '
               '<code>JSON_OBJECT</code> / <code>JSON_ARRAYAGG</code>.'),
        tags('JSON', '->>', 'JSON_EXTRACT', 'JSON_TABLE', 'JSON_ARRAYAGG', 'Generated Column'),
    ),
    explanation(
        table(['Syntax', 'Returns'], [
            ["<code>doc-&gt;'$.device.os'</code>", 'JSON value (strings keep their quotes)'],
            ["<code>doc-&gt;&gt;'$.device.os'</code>", 'Unquoted text: same as JSON_UNQUOTE(JSON_EXTRACT(…))'],
            ["<code>doc-&gt;'$.items[0]'</code>", 'First array element'],
            ["<code>JSON_CONTAINS(doc, '\"upi\"', '$.tags')</code>", '1 if the array contains the value'],
        ]),
    ),
    example(
        sqlrun("""
CREATE TABLE app_events (
  id INT PRIMARY KEY,
  payload JSON NOT NULL
);
INSERT INTO app_events VALUES
 (1, '{"user": 101, "event": "checkout", "device": {"os": "android"}, "items": [{"sku": "P1", "qty": 1}, {"sku": "P2", "qty": 2}]}'),
 (2, '{"user": 102, "event": "search",   "device": {"os": "ios"},     "items": []}'),
 (3, '{"user": 101, "event": "checkout", "device": {"os": "web"},     "items": [{"sku": "P3", "qty": 1}]}');

-- Extract fields
SELECT id, payload->>'$.event' AS event, payload->'$.device.os' AS os_json,
       payload->>'$.device.os' AS os, JSON_LENGTH(payload, '$.items') AS n_items
FROM app_events;

-- Flatten the items array into rows
SELECT e.id, payload->>'$.user' AS user_id, jt.sku, jt.qty
FROM app_events e,
     JSON_TABLE(e.payload, '$.items[*]' COLUMNS (sku VARCHAR(10) PATH '$.sku',
                                                 qty INT         PATH '$.qty')) AS jt;

-- Build JSON from relational rows
SELECT JSON_OBJECT('user', user_id, 'events', JSON_ARRAYAGG(event)) AS summary
FROM (SELECT payload->>'$.user' AS user_id, payload->>'$.event' AS event FROM app_events) t
GROUP BY user_id;
"""),
        title='Example'),
    example(
        sqlrun("""
CREATE TABLE app_events (id INT PRIMARY KEY, payload JSON NOT NULL,
  event_type VARCHAR(20) AS (payload->>'$.event') STORED,   -- generated column
  INDEX idx_event_type (event_type));
INSERT INTO app_events (id, payload) VALUES (1, '{"event": "checkout"}'), (2, '{"event": "search"}');

EXPLAIN FORMAT=TREE SELECT id FROM app_events WHERE event_type = 'checkout'\\G
"""),
        title='Example: Indexing a JSON Field'),
    interview(p('JSON columns suit semi-structured data such as event payloads or settings whose keys vary. Fields you filter '
                'or join on often should be promoted to real (or generated) columns with indexes, because a JSON column itself cannot be indexed directly.')),
    crossq(
        ('JSON vs storing JSON text in VARCHAR/TEXT?', 'The JSON type rejects invalid documents, stores a binary format that allows reading a field without parsing the whole text, and supports partial in-place updates.'),
        ('Multi-valued index?', 'MySQL 8.0.17+ can index arrays: <code>INDEX ((CAST(payload-&gt;\'$.tags\' AS CHAR(20) ARRAY)))</code>, used by MEMBER OF and JSON_CONTAINS.'),
    ),
]),

# ------------------------------------------------------------------ 53
Q('What is the MySQL binary log? How is it used for replication and Change Data Capture (CDC)?', 'Binary Log & CDC', minutes=9, cards=[
    definition(
        defbox('The <strong>binary log (binlog)</strong> is MySQL\'s ordered record of every committed change. Replicas replay it '
               'to stay in sync, it enables point-in-time recovery, and <strong>CDC tools</strong> such as Debezium read it to '
               'stream inserts, updates and deletes to Kafka and on into a data lake or warehouse.'),
        tags('Binary Log', 'binlog_format', 'ROW', 'GTID', 'Replication', 'Debezium', 'CDC'),
    ),
    comparison(
        table(['binlog_format', 'What is logged', 'Notes'], [
            ['STATEMENT', 'The SQL statement text', 'Small, but non-deterministic statements (NOW(), UUID(), LIMIT without ORDER BY) can differ on replicas'],
            ['ROW (default since 5.7.7)', 'Before/after image of every changed row', 'Exact and required for CDC; larger for bulk updates'],
            ['MIXED', 'Statement normally, row when unsafe', 'Compromise; not suitable for CDC'],
        ]),
    ),
    cdc_anim(),
    example(
        sqlrun("""
SHOW VARIABLES WHERE Variable_name IN
  ('log_bin', 'binlog_format', 'binlog_row_image', 'gtid_mode', 'binlog_expire_logs_seconds');

-- Make a change, then look at the events it produced
CREATE TABLE accounts (id INT PRIMARY KEY, balance INT);
INSERT INTO accounts VALUES (1, 500);
UPDATE accounts SET balance = 450 WHERE id = 1;
""", setup='FLUSH BINARY LOGS;'),
        title='Example: Checking the Binlog Configuration'),
    explanation(
        binlog_update_event(),
        p('In ROW format an UPDATE carries both the old values (WHERE) and the new values (SET). That before/after pair is '
          'exactly what a CDC change record contains.', True),
        title='What a ROW Event Looks Like'),
    comparison(
        table(['Approach', 'Captures deletes', 'Load on source', 'Latency'], [
            ['Query-based (WHERE updated_at &gt; watermark)', 'No (unless soft deletes)', 'Queries on the tables', 'Minutes–hours (batch)'],
            ['Log-based CDC (binlog)', 'Yes', 'Very low (reads the log)', 'Seconds'],
        ]),
        title='Query-based vs Log-based CDC'),
    crossq(
        ('What is a GTID?', 'A Global Transaction Identifier (<code>server_uuid:transaction_no</code>) given to every committed transaction. Replicas and CDC tools can resume by GTID instead of by file name and position, which makes failover much easier.'),
        ('What happens if binlogs are purged before the CDC connector reads them?', 'The connector cannot continue and must take a fresh snapshot. Keep <code>binlog_expire_logs_seconds</code> longer than any expected connector downtime.'),
    ),
]),

# ------------------------------------------------------------------ 54
Q('How do you extract data from MySQL into a data lake incrementally? (Spark JDBC partitioned reads)', 'Incremental Extract with Spark', minutes=9, cards=[
    definition(
        defbox('A typical batch extract reads only rows changed since the last run (a <strong>watermark</strong> on '
               '<code>updated_at</code> or an increasing id), splits the read into <strong>parallel chunks</strong> by a numeric '
               'key, and writes Parquet/Delta files to the lake. Spark\'s JDBC source does the chunking with '
               '<code>partitionColumn</code>, <code>lowerBound</code>, <code>upperBound</code> and <code>numPartitions</code>.'),
        tags('Spark JDBC', 'partitionColumn', 'numPartitions', 'fetchsize', 'Watermark', 'Read Replica'),
    ),
    example(
        sqlrun("""
-- 1. Find the bounds of this run's delta (watermark from the previous successful run)
SET @last_watermark = '2026-02-01';
SELECT MIN(order_id) AS lower_bound, MAX(order_id) AS upper_bound, COUNT(*) AS rows_to_extract,
       MAX(order_date) AS new_watermark
FROM orders
WHERE order_date > @last_watermark;

-- 2. What each of 2 Spark tasks will run (Spark generates these ranges)
SELECT 'task 1' AS task, COUNT(*) AS rows_read FROM orders WHERE order_date > @last_watermark AND order_id < 108
UNION ALL
SELECT 'task 2', COUNT(*) FROM orders WHERE order_date > @last_watermark AND order_id >= 108;
""", setup=SALES),
        title='Example: Planning the Extract in SQL'),
    explanation(
        py("""
bounds = spark.read.jdbc(url, f"(SELECT MIN(order_id) lo, MAX(order_id) hi FROM orders "
                              f" WHERE updated_at > '{last_watermark}') b", properties=props).first()

df = (spark.read.format("jdbc")
      .option("url", "jdbc:mysql://replica-host:3306/shop")       # read from a replica
      .option("dbtable", f"(SELECT * FROM orders WHERE updated_at > '{last_watermark}') src")
      .option("partitionColumn", "order_id")                      # numeric/date column
      .option("lowerBound", bounds.lo).option("upperBound", bounds.hi)
      .option("numPartitions", 8)                                  # 8 parallel queries
      .option("fetchsize", 10000)                                  # rows per round trip
      .option("user", user).option("password", password)
      .load())

(df.withColumn("load_date", F.current_date())
   .write.mode("append").partitionBy("load_date").parquet("s3://lake/raw/orders/"))
# Save the new watermark only after the write succeeds
""", 'PySpark'),
        title='The Spark Job'),
    warn('<code>lowerBound</code> and <code>upperBound</code> only decide how the range is <strong>split</strong>; they do not '
         'filter. Rows outside the bounds still go into the first and last partitions. A skewed key (most ids in one range) '
         'gives one slow task, so pick an evenly distributed column.', 'Common Misunderstanding'),
    explanation(
        ul('Read from a <strong>replica</strong>, not the primary, so extracts never slow the application.',
           'Index the watermark column (<code>updated_at</code>), otherwise every run is a full scan.',
           'Use <code>&gt;</code> the previous watermark and allow a small overlap for late commits, then deduplicate downstream (MERGE on the key).',
           'Store the watermark only after the data is safely written, so a failed run is simply repeated.',
           'Query-based extraction cannot see hard DELETEs; use soft deletes or log-based CDC when deletes matter.'),
        title='Good Practice'),
    crossq(
        ('Why not one big JDBC read?', 'A single connection reads serially through one cursor on one executor: slow, and it may run out of memory. Partitioned reads run numPartitions queries in parallel.'),
        ('What happens if numPartitions is too high?', 'Each partition is a separate connection and query on MySQL. Too many can overload the source; 4–16 is typical.'),
    ),
]),

# ------------------------------------------------------------------ 55
Q('How do you back up and restore a MySQL database? Explain logical vs physical backups and point-in-time recovery', 'Backup & Restore', minutes=7, cards=[
    definition(
        defbox('A <strong>logical backup</strong> exports SQL statements or data files (mysqldump, MySQL Shell dump utilities). '
               'A <strong>physical backup</strong> copies the InnoDB data files themselves (Percona XtraBackup, MySQL Enterprise Backup). '
               '<strong>Point-in-time recovery (PITR)</strong> restores the last full backup and then replays the binary logs up to a chosen moment.'),
        tags('mysqldump', '--single-transaction', 'XtraBackup', 'Point-in-time Recovery', 'MySQL Shell'),
    ),
    comparison(
        table(['Aspect', 'Logical (mysqldump / Shell)', 'Physical (XtraBackup)'], [
            ['Output', 'SQL / CSV files', 'Copy of data files'],
            ['Speed on large DBs', 'Slow to restore (re-executes inserts, rebuilds indexes)', 'Fast backup and restore'],
            ['Portability', 'Across versions and platforms; can restore one table', 'Same major version; whole instance'],
            ['Typical size', 'Up to tens of GB', 'Hundreds of GB to TB'],
        ]),
    ),
    explanation(
        code("""
# Consistent logical backup of InnoDB tables without locking them
mysqldump --single-transaction --routines --triggers --events \\
          --source-data=2 shop | gzip > shop_2026-10-11.sql.gz

# Restore
gunzip < shop_2026-10-11.sql.gz | mysql shop

# Faster, parallel dump and load with MySQL Shell
mysqlsh root@db -- util dump-schemas shop --outputUrl=/backups/shop_2026-10-11
mysqlsh root@db -- util load-dump /backups/shop_2026-10-11

# Point-in-time recovery: replay binlogs after the backup, stop before the bad statement
mysqlbinlog --start-position=157 --stop-datetime="2026-10-11 14:29:59" \\
            binlog.000012 binlog.000013 | mysql
""", 'Shell', 'fa-terminal'),
        p('<code>--single-transaction</code> starts a REPEATABLE READ transaction, so the dump is a consistent snapshot of all '
          'InnoDB tables while the application keeps writing. <code>--source-data=2</code> records the binlog position of that '
          'snapshot as a comment, which is the starting point for PITR or for setting up a replica.', True),
        title='Commands'),
    interview(p('A backup is only proven by a <strong>restore test</strong>. Mention scheduled restores into a test server, '
                'off-site copies, and monitoring of backup size and duration.')),
    crossq(
        ('Someone ran DELETE without WHERE at 14:30. How do you recover?', 'Restore the latest full backup to a new server, replay the binlog from the backup position up to just before 14:30 (<code>--stop-datetime</code> or the exact position found with mysqlbinlog), verify, then copy the table back.'),
        ('Is a replica a backup?', 'No. A replica copies mistakes too: the DELETE reaches it within seconds. A <em>delayed</em> replica (<code>SOURCE_DELAY</code>) can help, but proper backups are still needed.'),
    ),
]),

])
