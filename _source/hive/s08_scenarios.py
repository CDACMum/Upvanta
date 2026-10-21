from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

RAW = {
    'landing/attendance/dt=2026-10-12/att.csv': '2401,Anuj,Kharghar,P,09:02\n2402,Vineeta,Kharghar,P,08:55\n2403,Aarshvi,Juhu,A,\n',
    'landing/attendance/dt=2026-10-13/att.csv': '2401,Anuj,Kharghar,A,\n2402,Vineeta,Kharghar,P,08:58\n2403,Aarshvi,Juhu,P,09:31\n2404,Rohit,Juhu,X,09:00\n',
}

SECTION = dict(level='expert', title='Real-World Scenarios', questions=[

# ------------------------------------------------------------------ 35
Q('Scenario: Design a Hive pipeline for daily attendance data, from raw CSV to report.', 'End-to-End Pipeline', minutes=12, cards=[
    definition(
        defbox('A standard Hive design uses <strong>layers</strong>: a <strong>raw</strong> external table over files exactly as received, a '
               '<strong>curated</strong> ORC table partitioned by date with clean types and validated values, and <strong>report</strong> '
               'tables/views on top. Each daily run touches only one partition and is <strong>idempotent</strong> (INSERT OVERWRITE).'),
        tags('Pipeline Design', 'Raw Layer', 'Curated Layer', 'External Table', 'INSERT OVERWRITE', 'Idempotent'),
    ),
    analogy('Like a <strong>post office</strong>: letters are first dropped in the inbox as they arrive (raw), then sorted, checked for '
            'proper addresses and put in pigeonholes by date (curated), and finally the summary of deliveries is reported to the head office (report).'),
    pipeline_anim(),
    real_world(
        scenario('Requirements',
                 ul('Face-recognition devices at every centre drop a CSV per day into <code>/landing/attendance/dt=YYYY-MM-DD/</code>.',
                    'Status must be P or A; some rows have errors.',
                    'Coordinators need a daily centre-wise attendance %; data must be re-runnable for any day.')),
    ),
    example(
        datafile('/data/landing/attendance/dt=2026-10-13/att.csv', RAW['landing/attendance/dt=2026-10-13/att.csv']),
        hql('''
-- 1. RAW: external, all STRING, partitioned like the folders
--    (if files had a header: TBLPROPERTIES ('skip.header.line.count'='1'))
CREATE EXTERNAL TABLE raw_attendance (roll_no STRING, name STRING, centre STRING, status STRING, in_time STRING)
PARTITIONED BY (dt STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION '/data/landing/attendance';
MSCK REPAIR TABLE raw_attendance;

-- 2. CURATED: typed ORC, partitioned by date
CREATE TABLE attendance (roll_no INT, name STRING, centre STRING, present BOOLEAN, in_time STRING)
PARTITIONED BY (dt STRING) STORED AS ORC;

-- 3. QUARANTINE: rows that fail validation, with the reason
CREATE TABLE attendance_rejects (roll_no STRING, status STRING, reason STRING)
PARTITIONED BY (dt STRING) STORED AS ORC;

-- 4. Daily load for one date (re-runnable: OVERWRITE)
INSERT OVERWRITE TABLE attendance PARTITION (dt = '2026-10-13')
SELECT CAST(roll_no AS INT), trim(name), centre, status = 'P', in_time
FROM raw_attendance WHERE dt = '2026-10-13' AND status IN ('P', 'A') AND CAST(roll_no AS INT) IS NOT NULL;

INSERT OVERWRITE TABLE attendance_rejects PARTITION (dt = '2026-10-13')
SELECT roll_no, status, 'invalid status' FROM raw_attendance
WHERE dt = '2026-10-13' AND status NOT IN ('P', 'A');

-- 5. REPORT
SELECT dt, centre, COUNT(*) AS students,
       ROUND(100 * AVG(CASE WHEN present THEN 1 ELSE 0 END), 1) AS attendance_pct
FROM attendance GROUP BY dt, centre ORDER BY centre;

SELECT * FROM attendance_rejects;
''', files=RAW),
        title='Example: The Whole Pipeline'),
    steps(
        ('Agree the landing layout', 'One folder per day, <code>dt=YYYY-MM-DD</code>, fixed file format with a header.'),
        ('Create the raw external table', 'All STRING columns, partitioned by dt (add <code>skip.header.line.count</code> if files have a header).'),
        ('Register each new day', '<code>ALTER TABLE raw_attendance ADD IF NOT EXISTS PARTITION (dt=\'{{ ds }}\')</code>.'),
        ('Validate and load the curated table', '<code>INSERT OVERWRITE ... PARTITION (dt=...)</code> with casts and checks; bad rows to a reject table.'),
        ('Gather statistics', '<code>ANALYZE TABLE attendance PARTITION (dt=...) COMPUTE STATISTICS;</code>'),
        ('Build reports', 'Views or summary tables for dashboards.'),
        ('Schedule and monitor', 'Airflow DAG (one task per step), alert if rejects exceed a threshold or no file arrives.'),
        title='Steps to Build It'),
    crossq(
        ('Why keep the raw table as STRING?', 'So no value is lost or silently turned into NULL before validation; the curated load decides what is valid.'),
        ('How do you re-process a past day after a bug fix?', 'Re-run the daily load for that date: because it uses INSERT OVERWRITE on one partition, the old data for that day is replaced and other days are untouched.'),
        ('How would you handle late-arriving files?', 'The DAG for that date is re-triggered (or a sensor waits for the file); idempotent partition overwrites make re-runs safe.'),
    ),
]),

# ------------------------------------------------------------------ 36
Q('Scenario: How do you implement SCD Type 2 in Hive?', 'SCD Type 2 in Hive', minutes=12, cards=[
    definition(
        defbox('A <strong>Slowly Changing Dimension Type 2</strong> keeps full history: when an attribute changes, the current row is '
               '<strong>closed</strong> (end date, <code>is_current = N</code>) and a <strong>new version</strong> is inserted. In Hive this is done '
               'either with <strong>MERGE</strong> on an ACID table, or, on non-ACID tables, by <strong>rebuilding</strong> the dimension with '
               'INSERT OVERWRITE from (old rows ∪ changes).'),
        tags('SCD Type 2', 'Slowly Changing Dimension', 'History', 'MERGE', 'INSERT OVERWRITE', 'Effective Dates'),
    ),
    analogy('A <strong>passport\'s address history</strong>: when you move, the old address is not erased; it is marked "valid until" a date, '
            'and the new address is added "valid from" the next day. You can always tell where someone lived on any date.'),
    scd2_anim(),
    real_world(
        scenario('Why history matters',
                 p('A placement report by city must show where a student lived <em>when they were placed</em>. If the city were simply overwritten '
                   '(SCD Type 1), last year\'s report would change every time a student moved.')),
    ),
    example(
        hql('''
-- Rebuild approach (works on any table format)
INSERT OVERWRITE TABLE dim_student_new
SELECT * FROM (
  -- 1. history rows and unchanged current rows stay as they are
  SELECT d.id, d.city, d.start_dt, d.end_dt, d.is_current
  FROM dim_student d LEFT JOIN src s ON d.id = s.id
  WHERE d.is_current = 'N' OR s.id IS NULL OR d.city = s.city
  UNION ALL
  -- 2. changed current rows are closed (end = yesterday)
  SELECT d.id, d.city, d.start_dt, date_sub('2026-10-13', 1), 'N'
  FROM dim_student d JOIN src s ON d.id = s.id
  WHERE d.is_current = 'Y' AND d.city <> s.city
  UNION ALL
  -- 3. new versions for changed rows, and brand-new ids
  SELECT s.id, s.city, DATE '2026-10-13', DATE '9999-12-31', 'Y'
  FROM src s LEFT JOIN dim_student d ON d.id = s.id AND d.is_current = 'Y'
  WHERE d.id IS NULL OR d.city <> s.city
) x;

SELECT * FROM dim_student_new ORDER BY id, start_dt;
''', setup='''
CREATE TABLE dim_student (id INT, city STRING, start_dt DATE, end_dt DATE, is_current STRING) STORED AS ORC;
INSERT INTO dim_student VALUES
  (2401, 'Pune',   DATE '2025-07-01', DATE '9999-12-31', 'Y'),
  (2402, 'Pune',   DATE '2025-07-01', DATE '9999-12-31', 'Y'),
  (2403, 'Nashik', DATE '2025-07-01', DATE '9999-12-31', 'Y');
CREATE TABLE src (id INT, city STRING) STORED AS ORC;
INSERT INTO src VALUES (2401, 'Pune'), (2402, 'Mumbai'), (2404, 'Thane');
CREATE TABLE dim_student_new (id INT, city STRING, start_dt DATE, end_dt DATE, is_current STRING) STORED AS ORC;
'''),
        note('Inputs: the dimension had 2401 Pune, 2402 Pune, 2403 Nashik (all current); today\'s source has 2401 Pune (no change), '
             '2402 Mumbai (moved) and 2404 Thane (new). 2403 is not in today\'s source and stays unchanged. Then swap the tables: '
             '<code>ALTER TABLE ... RENAME</code>, or <code>INSERT OVERWRITE dim_student SELECT * FROM dim_student_new</code>.', 'Read the output'),
        hq('''
-- ACID approach (Hive 3, dim_student is a transactional ORC table)
MERGE INTO dim_student AS t
USING (
  SELECT s.id AS join_id, s.* FROM src s            -- rows to update/insert by id
  UNION ALL
  SELECT NULL AS join_id, s.* FROM src s            -- extra copy: forces INSERT of the new version
  JOIN dim_student d ON s.id = d.id AND d.is_current = 'Y' AND s.city <> d.city
) AS u
ON t.id = u.join_id AND t.is_current = 'Y'
WHEN MATCHED AND t.city <> u.city THEN
  UPDATE SET end_dt = date_sub(current_date, 1), is_current = 'N'
WHEN NOT MATCHED THEN
  INSERT VALUES (u.id, u.city, current_date, DATE '9999-12-31', 'Y');
''', 'SCD2 with MERGE (Hive 3 ACID)'),
        title='Example'),
    steps(
        ('Design the dimension', 'Business key, tracked attributes, <code>start_dt</code>, <code>end_dt</code>, <code>is_current</code> (optionally a surrogate key).'),
        ('Stage today\'s source', 'One row per business key (deduplicate first).'),
        ('Detect changes', 'Join current rows to the source on the key and compare tracked attributes (or a hash of them).'),
        ('Close and insert', 'MERGE on ACID tables, or rebuild with the three-part UNION ALL into a new table and swap.'),
        ('Validate', 'Exactly one current row per key: <code>SELECT id FROM dim WHERE is_current=\'Y\' GROUP BY id HAVING COUNT(*) &gt; 1</code> must return nothing.'),
        title='Steps to Implement SCD2'),
    crossq(
        ('Why the "UNION ALL with NULL join key" trick in MERGE?', 'One MERGE can apply only one action per source row. A changed row needs two actions (close the old, insert the new), so the source row is duplicated: one copy matches and updates, the other (NULL key) never matches and inserts.'),
        ('SCD Type 1 vs Type 2 vs Type 3?', 'Type 1 overwrites (no history); Type 2 adds a new row per change (full history); Type 3 keeps a "previous value" column (limited history).'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: Remove duplicate records and find the latest record per key.', 'Deduplication', minutes=8, cards=[
    definition(
        defbox('Duplicates arrive from retries, overlapping extracts and CDC replays. Exact duplicates can be removed with <code>DISTINCT</code> '
               'or GROUP BY; "keep the latest version per key" needs <code>ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC)</code> '
               'and a filter on row number 1.'),
        tags('Deduplication', 'ROW_NUMBER', 'Latest Record', 'DISTINCT', 'CDC'),
    ),
    analogy('Several copies of the same <strong>leave application</strong>, some edited later. You keep only the one with the most recent date '
            'stamp for each employee and shred the rest.'),
    dedup_anim(),
    real_world(
        scenario('Student profile updates',
                 p('The admission portal sends every profile change as a new row. The Hive job keeps the latest row per roll number for the '
                   'current-profile table, using <code>updated_at</code> plus a tie-breaker so reruns always pick the same row.')),
    ),
    example(
        hql('''
CREATE TABLE profile_changes (roll_no INT, phone STRING, city STRING, updated_at TIMESTAMP) STORED AS ORC;
INSERT INTO profile_changes VALUES
  (2401, '98xxxxxx01', 'Pune',   TIMESTAMP '2026-07-01 10:00:00'),
  (2401, '98xxxxxx01', 'Mumbai', TIMESTAMP '2026-09-15 18:30:00'),
  (2401, '98xxxxxx01', 'Mumbai', TIMESTAMP '2026-09-15 18:30:00'),   -- exact duplicate (retry)
  (2402, '98xxxxxx02', 'Vashi',  TIMESTAMP '2026-08-20 09:00:00');

SELECT roll_no, phone, city, updated_at
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY roll_no ORDER BY updated_at DESC) AS rn
  FROM profile_changes
) t
WHERE rn = 1
ORDER BY roll_no;

-- How many duplicates were there?
SELECT COUNT(*) AS total_rows, COUNT(DISTINCT roll_no) AS distinct_students FROM profile_changes;
'''),
        title='Example'),
    steps(
        ('Define the key and the "latest" rule', 'e.g. roll_no; newest updated_at; tie-breaker: highest batch_id.'),
        ('Number rows per key', '<code>ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC, batch_id DESC)</code>'),
        ('Keep rn = 1', 'In an outer query.'),
        ('Write with INSERT OVERWRITE', 'So the deduplicated table is rebuilt cleanly.'),
        title='Steps'),
    crossq(
        ('Why ROW_NUMBER and not RANK here?', 'RANK gives equal ranks to ties, so two rows with the same timestamp would both survive. ROW_NUMBER always picks exactly one.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('How do you optimise a slow Hive query? Give a checklist.', 'Performance Tuning Checklist', minutes=9, cards=[
    definition(
        table(['Area', 'What to do'], [
            ['Read less data', 'Partition filters (check pruning in EXPLAIN), select only needed columns, ORC/Parquet, predicate pushdown'],
            ['Joins', 'Map joins for small tables, bucket/SMB joins for big-big joins, filter before joining, fix skew'],
            ['Engine', 'Tez (or LLAP), vectorization on, CBO on with fresh statistics'],
            ['Parallelism', '<code>hive.exec.parallel=true</code> for independent stages; sensible reducer counts (<code>hive.exec.reducers.bytes.per.reducer</code>)'],
            ['Files', 'No small files (merge/compact); split-friendly formats'],
            ['Avoid', '<code>ORDER BY</code> without LIMIT, <code>COUNT(DISTINCT)</code> on huge data (use GROUP BY then count), functions on partition columns in WHERE, <code>SELECT *</code>'],
            ['Memory', 'Container size and <code>-Xmx</code> matching; map-side aggregation (<code>hive.map.aggr</code>)'],
        ]),
        tags('Performance', 'Tuning', 'Partition Pruning', 'Vectorization', 'CBO', 'Tez', 'Map Join'),
    ),
    analogy('Speeding up a delivery route: <strong>carry fewer parcels</strong> (read less data), <strong>take better roads</strong> (join '
            'strategy), <strong>use a faster vehicle</strong> (Tez, vectorization), <strong>send more vans in parallel</strong> (parallelism), '
            'and <strong>do not stop at every house for one letter</strong> (small files).'),
    tuning_anim(),
    real_world(
        scenario('Before and after',
                 table(['Change', 'Effect'], [
                     ['CSV → ORC + ZLIB', '7× less data read'],
                     ['Added <code>dt</code> filter the dashboard forgot', 'Read 1 day instead of 3 years'],
                     ['ANALYZE TABLE (stale stats)', 'Hive picked a map join for the 20 MB dimension'],
                     ['<code>COUNT(DISTINCT roll_no)</code> → subquery GROUP BY', 'No longer one single reducer'],
                     ['Compacted 30,000 small files', 'Planning time from 3 min to 10 s'],
                 ])),
    ),
    example(
        hql('''
CREATE TABLE logins (roll_no INT, dt STRING) STORED AS ORC;
INSERT INTO logins SELECT 2400 + CAST(rand(5) * 500 AS INT), '2026-10-13' FROM range(0, 20000);

-- Slow pattern on big data: one reducer must see all values
SELECT COUNT(DISTINCT roll_no) AS active_students FROM logins;

-- Scalable pattern: distinct in parallel first, then count
SELECT COUNT(*) AS active_students FROM (SELECT roll_no FROM logins GROUP BY roll_no) t;
'''),
        hq('''
SET hive.execution.engine = tez;
SET hive.vectorized.execution.enabled = true;
SET hive.cbo.enable = true;
SET hive.compute.query.using.stats = true;
SET hive.exec.parallel = true;
SET hive.auto.convert.join = true;
SET hive.optimize.ppd = true;
SET hive.merge.tezfiles = true;
''', 'Typical session settings'),
        title='Example'),
    steps(
        ('Get the plan', '<code>EXPLAIN</code> / <code>EXPLAIN DEPENDENCY</code>: is pruning happening? what join type?'),
        ('Find the slow vertex', 'Tez UI: time per vertex, input records per task (skew?), GC time.'),
        ('Fix data layout', 'Format, partitions, small files, statistics.'),
        ('Fix the query', 'Filters early, avoid anti-patterns, rewrite skewed joins.'),
        ('Tune settings last', 'Container sizes, reducers, parallelism.'),
        title='Steps to Diagnose'),
    crossq(
        ('Why is <code>COUNT(DISTINCT x)</code> slow in Hive?', 'Hive often computes it in a single reducer that must see all distinct values. The GROUP BY + COUNT rewrite spreads the work (newer Hive versions do this rewrite automatically in some cases).'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Troubleshooting scenarios frequently asked in Hive interviews', 'Troubleshooting Scenarios', minutes=10, cards=[
    analogy('Troubleshooting Hive is like a doctor\'s visit: <strong>symptom</strong> (error message or slowness) → <strong>tests</strong> '
            '(EXPLAIN, logs, Tez UI, metastore) → <strong>diagnosis</strong> (root cause) → <strong>treatment</strong> (fix) → '
            '<strong>prevention</strong> (so it does not happen again).', title='How to Approach It'),
    troubleshoot_anim(),
    real_world(
        scenario('1. "SELECT returns all NULLs" after creating a table over CSV files',
                 ul('Wrong delimiter (e.g. table says <code>,</code> but file uses <code>|</code>), quoted fields, or a header row.',
                    'Check with <code>hdfs dfs -cat ... | head</code>; fix ROW FORMAT / SerDe; add <code>skip.header.line.count</code>.')),
        scenario('2. New data written by Spark is not visible in Hive',
                 ul('New partition folders are not registered → <code>ALTER TABLE ADD PARTITION</code> / <code>MSCK REPAIR</code>.',
                    'Or stale stats answering COUNT(*) from metadata → <code>ANALYZE TABLE</code> or set <code>hive.compute.query.using.stats=false</code>.')),
        scenario('3. Query stuck at 99% for hours',
                 ul('One reducer with a hot key (skew): check task input records in Tez UI.',
                    'Fix: map join, skew join settings, salting, or filter NULL keys.')),
        scenario('4. "Container killed by YARN for exceeding memory limits" / OutOfMemory in map join',
                 ul('Raise <code>hive.tez.container.size</code> with <code>-Xmx</code> ≈ 80% of it.',
                    'For map joins: stats wrong → small table not small; refresh stats or lower <code>noconditionaltask.size</code>.')),
        scenario('5. "Number of dynamic partitions created is 1500, which is more than 1000"',
                 ul('Check the partition column is not accidentally high-cardinality (a timestamp?).',
                    'If intended, raise <code>hive.exec.max.dynamic.partitions</code> / <code>.pernode</code>.')),
        scenario('6. Query takes minutes before any task starts',
                 ul('Too many partitions or files to list (metastore + NameNode calls).',
                    'Add partition filters, coarsen partitioning, compact small files.')),
        scenario('7. Table dropped by mistake',
                 ul('External table: recreate it with the same DDL and LOCATION; run MSCK REPAIR. Data is safe.',
                    'Managed table: recover from HDFS trash (<code>/user/hive/.Trash</code>) if enabled, else from backup/snapshot. '
                    'Prevention: external tables for raw data, HDFS snapshots, Ranger permissions.')),
    ),
    example(
        hql('''
-- Scenario 1 reproduced: the file uses "|" but the table says ","
CREATE EXTERNAL TABLE wrong_delim (roll_no INT, name STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
LOCATION '/data/raw/pipe';
SELECT * FROM wrong_delim;

-- Fix: drop (external = data safe) and recreate with the right delimiter
DROP TABLE wrong_delim;
CREATE EXTERNAL TABLE wrong_delim (roll_no INT, name STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY '|'
LOCATION '/data/raw/pipe';
SELECT * FROM wrong_delim;
''', files={'raw/pipe/p.txt': '2401|Anuj|78\n2402|Vineeta|91\n'}),
        title='Example: Diagnosing the All-NULL Table'),
    steps(
        ('Read the exact error', 'Beeline message, then HiveServer2 log, then the failed Tez task log (<code>yarn logs -applicationId ...</code>).'),
        ('Reproduce small', 'Same query with LIMIT or on one partition.'),
        ('Inspect metadata', '<code>DESCRIBE FORMATTED</code>, <code>SHOW PARTITIONS</code>, <code>SHOW CREATE TABLE</code>.'),
        ('Inspect data', '<code>hdfs dfs -ls / -cat</code> the actual files.'),
        ('Fix and prevent', 'Change DDL/settings; add a check to the pipeline.'),
        title='Steps for Any Hive Problem'),
    crossq(
        ('Where are Hive logs?', 'HiveServer2 log on the server (e.g. <code>/var/log/hive/hiveserver2.log</code>), query logs in Beeline (<code>--verbose</code>), and Tez task logs via <code>yarn logs -applicationId &lt;id&gt;</code> or the Tez UI.'),
        ('A query that worked yesterday fails today. What do you check first?', 'What changed: new data (bad values, skew, a new partition), schema changes, statistics, cluster capacity/queue, or configuration. Compare the plan and input sizes of yesterday\'s and today\'s runs.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Where does Hive fit in a modern data platform (Spark, Trino, Iceberg, cloud)?', 'Hive in the Modern Stack', minutes=8, cards=[
    definition(
        defbox('Hive has two roles today. As a <strong>query engine</strong> (HiveServer2 + Tez/LLAP) it is mainly used in on-prem Cloudera/HDP '
               'estates for batch ETL. As a <strong>catalogue</strong>, the <strong>Hive Metastore</strong> is everywhere: Spark, Trino, Impala, '
               'Flink and many cloud services (AWS Glue Data Catalog is Hive-Metastore-compatible) use it to find tables.',
               'Newer <strong>open table formats</strong>, <strong>Apache Iceberg</strong>, Delta Lake and Hudi, solve Hive table limitations '
               '(directory-based partitions, slow listing, no safe concurrent writes on plain tables, no time travel) and are often registered '
               '<em>in</em> the Hive Metastore. <strong>Hive 4</strong> (2024) supports Iceberg tables natively.'),
        tags('Hive Metastore', 'Iceberg', 'Delta Lake', 'Hudi', 'AWS Glue', 'Trino', 'Hive 4'),
    ),
    analogy('The Hive Metastore is like a city\'s <strong>address directory</strong>: many delivery companies (Spark, Trino, Impala) use the '
            'same directory to find houses. Iceberg is a <strong>modern building with its own security desk and visitor log</strong>: it is still '
            'listed in the city directory, but it tracks exactly who lives where and keeps the history of every change.'),
    comparison(
        table(['Problem with classic Hive tables', 'How Iceberg solves it'], [
            ['Partitions are folders; users must filter on the exact partition column', '<strong>Hidden partitioning</strong>: <code>PARTITIONED BY days(event_ts)</code>, queries filter on event_ts'],
            ['Listing thousands of folders is slow (especially on S3)', 'Metadata files list data files directly'],
            ['Changing partitioning means rewriting the table', '<strong>Partition evolution</strong>'],
            ['No safe concurrent writers; partial writes visible', 'Atomic snapshot commits'],
            ['No time travel', '<code>FOR SYSTEM_TIME AS OF</code> / snapshot ids'],
        ]),
    ),
    iceberg_anim(),
    real_world(
        scenario('Migration path',
                 p('A company moving from on-prem Hadoop to AWS keeps its HiveQL knowledge and table names: tables move to S3 as Iceberg, the '
                   'catalogue becomes AWS Glue (Hive-Metastore-compatible), ETL runs on Spark (EMR), and analysts query with Athena/Trino.')),
    ),
    example(
        hq('''
-- Hive 4: create an Iceberg table
CREATE TABLE exam_events (roll_no INT, event STRING, event_ts TIMESTAMP)
PARTITIONED BY SPEC (day(event_ts))
STORED BY ICEBERG STORED AS PARQUET;

SELECT * FROM exam_events FOR SYSTEM_TIME AS OF '2026-10-12 23:59:59';   -- time travel
ALTER TABLE exam_events SET PARTITION SPEC (hour(event_ts));          -- partition evolution
''', 'Hive 4 + Iceberg'),
        sh('''
# Spark using the same Hive Metastore
spark-sql --conf spark.sql.catalogImplementation=hive \\
          --conf spark.hadoop.hive.metastore.uris=thrift://hms:9083 \\
          -e "SELECT COUNT(*) FROM cdac.attendance WHERE dt='2026-10-13'"
''', 'Spark on the Hive Metastore'),
        title='Example'),
    steps(
        ('Keep one catalogue', 'Hive Metastore (or Glue / a REST catalog) shared by every engine.'),
        ('Store data in open formats', 'ORC/Parquet, ideally as Iceberg tables for new datasets.'),
        ('Pick engines per workload', 'Spark/Hive for batch ETL, Trino/Impala for interactive SQL.'),
        ('Migrate gradually', 'Iceberg can adopt existing Parquet/ORC Hive tables in place (migrate/snapshot procedures).'),
        title='Steps to Modernise a Hive Platform'),
    crossq(
        ('Is learning Hive still worth it?', 'Yes: HiveQL is close to Spark SQL, the metastore concepts (databases, external tables, partitions, SerDes) are used by every engine, and many enterprises in India (banks, telecom, government) still run Hive in production.'),
        ('What is AWS Glue Data Catalog\'s relation to Hive?', 'It is a managed, Hive-Metastore-compatible catalogue. EMR Spark/Hive, Athena and Redshift Spectrum use it the way on-prem engines use HMS.'),
    ),
]),
])
