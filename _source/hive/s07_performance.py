from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

GEN = '''
CREATE TABLE gen AS
SELECT 240000 + id AS roll_no,
       element_at(array('Mumbai','Pune','Navi Mumbai','Bengaluru','Hyderabad'), CAST(rand(1) * 5 AS INT) + 1) AS city,
       element_at(array('PG-DBDA','PG-DAC','PG-DAI'), CAST(rand(2) * 3 AS INT) + 1) AS course,
       CAST(35 + rand(3) * 66 AS INT) AS marks
FROM range(0, 200000) AS t(id);
'''

SECTION = dict(level='advanced', title='Storage, Engines & Performance', questions=[

# ------------------------------------------------------------------ 29
Q('Which file formats does Hive support? Why is ORC preferred?', 'File Formats & ORC', minutes=10, cards=[
    definition(
        defbox('Hive tables can be stored as <strong>TEXTFILE</strong> (default), <strong>SEQUENCEFILE</strong>, <strong>AVRO</strong>, '
               '<strong>PARQUET</strong> or <strong>ORC</strong> (<code>STORED AS ...</code>). <strong>ORC (Optimized Row Columnar)</strong> was '
               'built for Hive: columnar storage in <strong>stripes</strong> (~64–256 MB) with <strong>min/max indexes</strong> per stripe and per '
               '10,000 rows, optional <strong>bloom filters</strong>, lightweight encodings plus ZLIB/Snappy/ZSTD compression, and it is required '
               'for ACID tables.'),
        tags('ORC', 'Parquet', 'Avro', 'TEXTFILE', 'Stripe', 'Predicate Pushdown', 'Bloom Filter', 'Compression'),
    ),
    analogy('A text file is a <strong>diary</strong>: to find all marks you read every page line by line. ORC is a <strong>well-organised '
            'register</strong> with one column per subject and a summary on top of every page ("marks on this page: 35–98"), so you can jump '
            'straight to the marks column and skip pages that cannot contain what you need.'),
    orc_anim(),
    real_world(
        scenario('Converting the raw layer',
                 p('Raw CSV exam data (1.2 TB) was rewritten as ORC with ZLIB: 180 GB on disk, and the "average marks by course for one centre" '
                   'query went from 14 minutes to under 1 minute, because Hive read only 2 of 25 columns and skipped stripes using min/max statistics.')),
    ),
    example(
        hql('''
CREATE TABLE s_text    ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE AS SELECT * FROM gen;
CREATE TABLE s_orc     STORED AS ORC     AS SELECT * FROM gen;
CREATE TABLE s_parquet STORED AS PARQUET AS SELECT * FROM gen;

SELECT 'TEXTFILE' AS format, COUNT(*) AS rows FROM s_text
UNION ALL SELECT 'ORC', COUNT(*) FROM s_orc
UNION ALL SELECT 'PARQUET', COUNT(*) FROM s_parquet;

dfs -ls -R /user/hive/warehouse/cdac.db/s_text;
dfs -ls -R /user/hive/warehouse/cdac.db/s_orc;
dfs -ls -R /user/hive/warehouse/cdac.db/s_parquet;
''', setup=GEN),
        note('The same 200,000 rows: compare the byte sizes in the first column of each listing. Columnar formats store each column together, so '
             'repeated values (city, course) compress extremely well.', 'Read the output'),
        hql('''
EXPLAIN SELECT AVG(marks) FROM s_orc WHERE city = 'Pune';
''', setup=GEN + "CREATE TABLE s_orc STORED AS ORC AS SELECT * FROM gen;"),
        note('<code>ReadSchema: struct&lt;city,marks&gt;</code> = only 2 of the 4 columns are read (column pruning), and '
             '<code>PushedFilters: [EqualTo(city,Pune)]</code> = the filter is handed to the ORC reader, which skips stripes/row groups whose '
             'min/max statistics exclude "Pune" (predicate pushdown).', 'Read the plan'),
        title='Example: Same Data in Three Formats'),
    hq('''
CREATE TABLE results_orc (roll_no INT, name STRING, course STRING, marks INT)
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES (
  'orc.compress'             = 'ZLIB',      -- or SNAPPY / ZSTD
  'orc.bloom.filter.columns' = 'roll_no',   -- fast point lookups on roll_no
  'orc.stripe.size'          = '67108864'
);
SET hive.optimize.ppd = true;               -- predicate pushdown (default)
SET hive.optimize.index.filter = true;      -- use ORC indexes to skip data
''', 'Tuning an ORC table'),
    steps(
        ('Create the ORC table', '<code>CREATE TABLE t (...) STORED AS ORC TBLPROPERTIES (\'orc.compress\'=\'ZLIB\');</code>'),
        ('Load from the raw table', '<code>INSERT OVERWRITE TABLE t SELECT ... FROM raw_text;</code> (never LOAD DATA a CSV into it).'),
        ('Add bloom filters for lookup columns', '<code>orc.bloom.filter.columns</code> for ids you filter with <code>=</code>.'),
        ('Sort on frequently filtered columns', '<code>INSERT ... SORT BY city</code> tightens min/max ranges so more stripes are skipped.'),
        ('Verify', '<code>DESCRIBE FORMATTED t</code> → <code>OrcSerde</code>; <code>hive --orcfiledump &lt;file&gt;</code> shows stripes and statistics.'),
        title='Steps to Convert a Table to ORC'),
    crossq(
        ('ORC vs Parquet?', 'Both columnar and splittable. ORC has richer built-in indexes and is required for Hive ACID; Parquet has broader ecosystem support (Spark default, Impala, cloud warehouses). Use ORC for Hive-centric warehouses, Parquet when many engines share data.'),
        ('When is TEXTFILE still used?', 'For landing/raw data exactly as received, and for exchange with systems that only understand CSV.'),
        ('Is Snappy-compressed ORC splittable?', 'Yes. Compression is applied per stripe/stream inside the file, so the file can still be split at stripe boundaries.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What execution engines can Hive use? Compare MapReduce, Tez and Spark.', 'Execution Engines (MR / Tez / Spark)', minutes=8, cards=[
    definition(
        defbox('<code>hive.execution.engine</code> selects how plans run: <strong>mr</strong> (MapReduce, deprecated since Hive 2), '
               '<strong>tez</strong> (default in Hive 2/3 distributions) or <strong>spark</strong> (Hive on Spark; removed in Hive 4). '
               '<strong>LLAP</strong> adds long-running daemons with in-memory caching on top of Tez for interactive queries.'),
        table(['Aspect', 'MapReduce', 'Tez', 'Spark'], [
            ['Plan', 'Chain of map→reduce jobs', 'One DAG of vertices', 'One DAG of stages'],
            ['Intermediate data', 'HDFS between jobs', 'Local disk / in memory between vertices', 'Memory/disk between stages'],
            ['Container reuse', 'No', 'Yes, plus warm sessions', 'Long-lived executors'],
            ['Speed', 'Slowest', 'Fast', 'Fast'],
            ['Status', 'Deprecated', 'Standard', 'Removed in Hive 4'],
        ]),
        tags('Tez', 'MapReduce', 'Hive on Spark', 'LLAP', 'DAG', 'hive.execution.engine'),
    ),
    analogy('MapReduce is sending a parcel through <strong>several courier companies</strong>, each one unpacking, storing it in its warehouse '
            'and repacking it for the next. Tez is <strong>one company with one route plan</strong>: the parcel moves directly from van to van.'),
    engines_anim(),
    real_world(
        scenario('Migration result',
                 p('A legacy cluster still running <code>hive.execution.engine=mr</code> switched to Tez: a nightly report with 3 joins and 2 '
                   'aggregations went from 9 MapReduce jobs (47 minutes) to one Tez DAG (11 minutes) without changing the SQL.')),
    ),
    example(
        hq('''
SET hive.execution.engine = tez;
SET tez.queue.name = analytics;            -- YARN queue
SET hive.tez.container.size = 4096;        -- MB per Tez task container
SET hive.tez.java.opts = -Xmx3276m;        -- ~80% of the container
SET hive.prewarm.enabled = true;           -- keep warm containers for the session

-- Beeline progress output looks like:
-- VERTICES      MODE    STATUS     TOTAL  COMPLETED  RUNNING  PENDING  FAILED
-- Map 1 ......  container SUCCEEDED     12         12        0        0       0
-- Reducer 2 ..  container RUNNING        4          1        3        0       0
''', 'Tez settings'),
        title='Example'),
    steps(
        ('Check the current engine', '<code>SET hive.execution.engine;</code>'),
        ('Switch to Tez', '<code>SET hive.execution.engine=tez;</code> per session, or in <code>hive-site.xml</code> for everyone.'),
        ('Size containers', '<code>hive.tez.container.size</code> and <code>hive.tez.java.opts</code>.'),
        ('Monitor', 'Tez UI / YARN UI: per-vertex time, task counts and failed attempts.'),
        title='Steps to Run on Tez'),
    crossq(
        ('What is a vertex in Tez?', 'A processing step in the DAG (e.g. "Map 1" scanning a table, "Reducer 2" aggregating). Edges describe how data moves between vertices (one-to-one, broadcast, scatter-gather/shuffle).'),
        ('What does LLAP add?', 'Persistent daemons on worker nodes that cache ORC data in memory and run query fragments without starting containers, giving interactive latency with the same SQL.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('What is the cost-based optimizer? Why are table statistics important? What is vectorization?', 'CBO, Statistics & Vectorization', minutes=9, cards=[
    definition(
        defbox('The <strong>cost-based optimizer (CBO)</strong>, built on Apache Calcite, chooses join order, join type (map join or shuffle) and '
               'other plan details by estimating the cost of alternatives. Its estimates come from <strong>statistics</strong> stored in the '
               'metastore: row counts, sizes, and per-column number of distinct values, NULLs, min/max.',
               '<strong>Vectorization</strong> processes data in <strong>batches of 1,024 rows</strong> per column instead of one row at a time, '
               'using tight loops that suit modern CPUs (works with ORC; Parquet in newer versions).'),
        tags('CBO', 'Calcite', 'ANALYZE TABLE', 'Statistics', 'Vectorization', 'hive.compute.query.using.stats'),
    ),
    analogy('Planning a journey: the CBO is <strong>Google Maps</strong> choosing a route from traffic data. Without statistics it is a driver with '
            'an outdated map, who may pick a jammed road (a shuffle join of a "small" table that is actually huge). Vectorization is a '
            '<strong>bus</strong> instead of individual auto-rickshaws: 1,024 passengers handled per trip.'),
    cbo_anim(),
    real_world(
        scenario('Stale statistics',
                 p('After a back-fill tripled a table, its stats still said 10 MB, so Hive chose a map join and tasks failed with OutOfMemory. '
                   'Running <code>ANALYZE TABLE ... COMPUTE STATISTICS FOR COLUMNS</code> after loads fixed it, and the ETL now does it automatically.')),
    ),
    example(
        hql('''
CREATE TABLE s_orc STORED AS ORC AS SELECT * FROM gen;

ANALYZE TABLE s_orc COMPUTE STATISTICS;
ANALYZE TABLE s_orc COMPUTE STATISTICS FOR COLUMNS city, marks;

DESCRIBE EXTENDED s_orc city;
DESCRIBE EXTENDED s_orc marks;
''', setup=GEN),
        hq('''
SET hive.cbo.enable = true;
SET hive.compute.query.using.stats = true;   -- answer COUNT(*)/MIN/MAX from stats, no job
SET hive.stats.fetch.column.stats = true;
SET hive.stats.autogather = true;            -- basic stats on every INSERT
SET hive.vectorized.execution.enabled = true;
SET hive.vectorized.execution.reduce.enabled = true;

ANALYZE TABLE attendance PARTITION (dt='2026-10-13') COMPUTE STATISTICS FOR COLUMNS;
EXPLAIN VECTORIZATION ONLY SELECT city, AVG(marks) FROM s_orc GROUP BY city;
''', 'Hive settings'),
        title='Example: Gathering and Reading Statistics'),
    steps(
        ('Enable auto-gathering', '<code>hive.stats.autogather=true</code> for basic stats on insert.'),
        ('Compute column stats after loads', '<code>ANALYZE TABLE t [PARTITION (...)] COMPUTE STATISTICS FOR COLUMNS;</code>'),
        ('Enable CBO and vectorization', 'The settings above (defaults in Hive 3).'),
        ('Check the plan', '<code>EXPLAIN</code> shows estimated rows; wildly wrong estimates mean stale stats.'),
        title='Steps to Help the Optimizer'),
    crossq(
        ('Why can <code>SELECT COUNT(*) FROM t</code> return instantly in Hive?', 'With <code>hive.compute.query.using.stats=true</code> and accurate stats, Hive answers from metastore statistics without reading data. If files were changed outside Hive, the answer can be wrong.'),
        ('Which statistics matter most for joins?', 'Row counts and data size (to decide map join vs shuffle join) and number of distinct values of join keys (to estimate join output size and order).'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What is data skew in Hive? How do you handle skewed joins and GROUP BYs?', 'Data Skew', minutes=9, cards=[
    definition(
        defbox('<strong>Skew</strong> happens when a few key values have far more rows than the rest. Since all rows of a key go to the same '
               'reducer, that reducer becomes the bottleneck: the query sits at "99%" for a long time.'),
        table(['Technique', 'How'], [
            ['Map join', 'If the other side is small, avoid the shuffle entirely'],
            ['Skew join', '<code>hive.optimize.skewjoin=true</code>, <code>hive.skewjoin.key=100000</code>: keys above the threshold are processed in a follow-up map join'],
            ['Skewed table', '<code>SKEWED BY (city) ON (\'Mumbai\') STORED AS DIRECTORIES</code> stores hot values separately'],
            ['GROUP BY skew', '<code>hive.groupby.skewindata=true</code>: random distribution + partial aggregation, then final aggregation'],
            ['Map-side aggregation', '<code>hive.map.aggr=true</code> (default): partial aggregates in mappers'],
            ['Salting', 'Manually add a random suffix to the hot key, aggregate twice'],
            ['Filter junk keys', 'NULL, 0, "unknown" keys often cause skew; filter or handle separately'],
        ]),
        tags('Data Skew', 'Skew Join', 'Salting', 'hive.groupby.skewindata', 'SKEWED BY', 'Hot Key'),
    ),
    analogy('Exam paper evaluation with 4 evaluators, distributed by centre. Mumbai centre has 9,000 papers and the others 300 each. Three '
            'evaluators finish by lunch; the Mumbai evaluator works for a week. Salting is splitting Mumbai\'s papers into 4 bundles '
            '(Mumbai#0…#3) so all evaluators help, then adding up their totals.'),
    skew_anim(),
    real_world(
        scenario('NULL customer ids',
                 p('In a retail join, 40% of transactions had <code>customer_id = NULL</code> (walk-in customers). All NULLs hashed to one '
                   'reducer. Filtering NULL keys out of the join (they cannot match anyway) and UNION ALL-ing them back cut the job from 3 hours to 20 minutes.')),
    ),
    example(
        hql('''
CREATE TABLE visits AS
SELECT CASE WHEN id % 10 < 8 THEN 'Mumbai' ELSE element_at(array('Pune','Nashik','Nagpur'), CAST(id % 3 AS INT) + 1) END AS city,
       id AS visit_id
FROM range(0, 100000) AS t(id);

-- How skewed is the key?
SELECT city, COUNT(*) AS n FROM visits GROUP BY city ORDER BY n DESC;

-- Salting: stage 1 aggregates (city, salt), stage 2 removes the salt
SELECT city, SUM(partial) AS visits
FROM (
  SELECT city, salt, COUNT(*) AS partial
  FROM (SELECT city, CAST(rand(42) * 8 AS INT) AS salt FROM visits) s
  GROUP BY city, salt
) p
GROUP BY city ORDER BY visits DESC;
'''),
        hq('''
SET hive.optimize.skewjoin = true;
SET hive.skewjoin.key = 100000;            -- rows per key above which a key is "skewed"
SET hive.groupby.skewindata = true;        -- two-stage GROUP BY

CREATE TABLE visits_sk (city STRING, visit_id BIGINT)
SKEWED BY (city) ON ('Mumbai') STORED AS DIRECTORIES;   -- list bucketing
''', 'Hive\'s built-in skew handling'),
        title='Example: Detecting Skew and Salting'),
    steps(
        ('Confirm skew', 'Tez UI: one task much slower with far more input records; then <code>GROUP BY key ORDER BY COUNT(*) DESC LIMIT 20</code>.'),
        ('Remove junk keys', 'NULL/default values: filter, or handle separately.'),
        ('Try a map join', 'If the other table is small enough.'),
        ('Enable skew settings', 'skewjoin / groupby.skewindata.'),
        ('Salt manually for full control', 'Random suffix → partial aggregate → final aggregate (for joins, replicate the small side for each salt value).'),
        title='Steps to Fix a Skewed Query'),
    crossq(
        ('Why does <code>hive.groupby.skewindata</code> help?', 'The first job spreads rows randomly across reducers and computes partial aggregates, so the hot key is shared; a second job combines the partials by key.'),
        ('Does increasing the number of reducers fix skew?', 'No. All rows of the hot key still go to one reducer. You must split the key (salt) or avoid the shuffle (map join).'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('How do you handle the small files problem in Hive?', 'Small Files in Hive', minutes=8, cards=[
    definition(
        defbox('Small files appear from frequent <code>INSERT ... VALUES</code>, streaming ingestion, too many reducers, and dynamic '
               'partition inserts where every task writes to every partition. They slow down planning (listing), add NameNode/metastore load '
               'and create too many tasks.'),
        table(['Fix', 'Setting / command'], [
            ['Merge output files at the end of a query', '<code>hive.merge.tezfiles=true</code> (Tez), <code>hive.merge.mapfiles</code>, <code>hive.merge.mapredfiles</code>, <code>hive.merge.smallfiles.avgsize</code>, <code>hive.merge.size.per.task</code>'],
            ['Combine small files on read', '<code>hive.input.format=org.apache.hadoop.hive.ql.io.CombineHiveInputFormat</code> (default), <code>tez.grouping.*</code>'],
            ['Concatenate ORC/RC files', '<code>ALTER TABLE t PARTITION (dt=...) CONCATENATE;</code>'],
            ['Rewrite the partition', '<code>INSERT OVERWRITE TABLE t PARTITION (...) SELECT * FROM t WHERE ...</code>'],
            ['One writer per partition', '<code>DISTRIBUTE BY</code> the partition column in dynamic partition inserts'],
            ['ACID tables', 'Compaction (automatic) merges delta files'],
        ]),
        tags('Small Files', 'hive.merge', 'CONCATENATE', 'INSERT OVERWRITE', 'Compaction', 'CombineHiveInputFormat'),
    ),
    analogy('A cupboard where each receipt is kept in its <strong>own separate envelope</strong>: finding anything means opening thousands of '
            'envelopes. Compaction is emptying them into a few thick files.'),
    small_files_anim(),
    real_world(
        scenario('Hourly inserts',
                 p('An hourly job inserted into a daily partition 24 times; each insert with 50 reducers wrote 50 files, so 1,200 files per day '
                   'of only 2–5 MB each. A nightly <code>INSERT OVERWRITE</code> of yesterday\'s partition with <code>hive.merge.tezfiles=true</code> '
                   'turned that into 4 files of ~250 MB, and queries over a month became 6× faster.')),
    ),
    example(
        hql('''
CREATE TABLE events (roll_no INT, action STRING) PARTITIONED BY (dt STRING) STORED AS ORC;

-- 6 small inserts into the same partition = 6+ small files
INSERT INTO events PARTITION (dt='2026-10-13') VALUES (2401,'login');
INSERT INTO events PARTITION (dt='2026-10-13') VALUES (2402,'login');
INSERT INTO events PARTITION (dt='2026-10-13') VALUES (2401,'quiz');
INSERT INTO events PARTITION (dt='2026-10-13') VALUES (2403,'login');
INSERT INTO events PARTITION (dt='2026-10-13') VALUES (2402,'quiz');
INSERT INTO events PARTITION (dt='2026-10-13') VALUES (2401,'logout');
dfs -ls -R /user/hive/warehouse/cdac.db/events;

-- Compact: copy the partition aside, then rewrite it as one file
CREATE TABLE events_tmp STORED AS ORC AS SELECT roll_no, action FROM events WHERE dt = '2026-10-13';
INSERT OVERWRITE TABLE events PARTITION (dt='2026-10-13')
SELECT /*+ COALESCE(1) */ roll_no, action FROM events_tmp;
DROP TABLE events_tmp;
dfs -ls -R /user/hive/warehouse/cdac.db/events;
SELECT COUNT(*) AS rows_after FROM events;
'''),
        note('In Hive you can overwrite a partition directly from itself (<code>INSERT OVERWRITE ... SELECT ... FROM events WHERE dt=...</code>), '
             'and no hint is needed: with <code>hive.merge.tezfiles=true</code> Hive adds a merge step when the average output file is below '
             '<code>hive.merge.smallfiles.avgsize</code> (16 MB by default). Spark SQL, used to run this example, refuses to overwrite a table it is '
             'reading, hence the temporary copy.', 'In Hive'),
        title='Example: Many Small Files, Then One'),
    steps(
        ('Measure', '<code>hdfs dfs -count /warehouse/.../t/*</code> → files per partition and average size.'),
        ('Enable merge settings', '<code>SET hive.merge.tezfiles=true; SET hive.merge.smallfiles.avgsize=134217728;</code>'),
        ('Compact existing partitions', '<code>ALTER TABLE ... CONCATENATE</code> (ORC) or INSERT OVERWRITE.'),
        ('Fix the source', 'Batch inserts, fewer reducers, <code>DISTRIBUTE BY</code> partition column.'),
        title='Steps to Fix Small Files'),
    crossq(
        ('Why does INSERT OVERWRITE of a partition from itself work?', 'Hive reads the partition into the job first and writes the result to a staging directory; only when the job succeeds is the old data replaced.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('Does Hive support ACID transactions, UPDATE, DELETE and MERGE? How does it work?', 'ACID Transactions', minutes=10, cards=[
    definition(
        defbox('Since Hive 0.14 (and fully in Hive 3), <strong>transactional tables</strong> support <code>INSERT</code>, <code>UPDATE</code>, '
               '<code>DELETE</code> and <code>MERGE</code> with ACID guarantees (snapshot isolation). Requirements: <strong>managed table, ORC '
               'format</strong>, <code>\'transactional\'=\'true\'</code>, and the transaction manager <code>DbTxnManager</code>. In Hive 3, '
               'managed ORC tables are transactional by default; <code>\'transactional_properties\'=\'insert_only\'</code> allows other formats for inserts only.',
               'Data is never modified in place. Changes are written as <strong>delta</strong> and <strong>delete_delta</strong> directories; '
               'readers merge them with the base; <strong>compaction</strong> periodically rewrites them.'),
        tags('ACID', 'Transactional Table', 'UPDATE', 'DELETE', 'MERGE', 'Delta Files', 'Compaction', 'DbTxnManager'),
    ),
    analogy('A printed <strong>register that cannot be erased</strong>. To correct marks you attach a <strong>correction slip</strong> '
            '("roll 2402: cancel 85, now 91"). Readers look at the page and all slips together. When the slips pile up, a clerk '
            '<strong>rewrites a clean page</strong> including all corrections (compaction).'),
    acid_anim(),
    real_world(
        scenario('Re-evaluation results and GDPR-style deletes',
                 ul('After re-evaluation, 300 marks change: one <code>MERGE</code> from the re-evaluation table updates them in place, '
                    'instead of rewriting the whole year\'s partition.',
                    'A student withdraws consent: <code>DELETE FROM students WHERE roll_no = 2405</code> removes them from all history.',
                    'SCD Type 2 dimensions are maintained with MERGE.')),
    ),
    example(
        hq('''
SET hive.support.concurrency = true;
SET hive.txn.manager = org.apache.hadoop.hive.ql.lockmgr.DbTxnManager;

CREATE TABLE marks_acid (roll_no INT, subject STRING, marks INT)
STORED AS ORC
TBLPROPERTIES ('transactional' = 'true');

INSERT INTO marks_acid VALUES (2401,'SQL',78), (2402,'SQL',85), (2405,'SQL',70);

UPDATE marks_acid SET marks = 91 WHERE roll_no = 2402 AND subject = 'SQL';
DELETE FROM marks_acid WHERE roll_no = 2405;

-- Upsert from a staging table
MERGE INTO marks_acid AS t
USING reeval AS s
ON t.roll_no = s.roll_no AND t.subject = s.subject
WHEN MATCHED AND s.new_marks IS NULL THEN DELETE
WHEN MATCHED THEN UPDATE SET marks = s.new_marks
WHEN NOT MATCHED THEN INSERT VALUES (s.roll_no, s.subject, s.new_marks);

SHOW TRANSACTIONS;
SHOW COMPACTIONS;
ALTER TABLE marks_acid COMPACT 'major';     -- request compaction manually
''', 'HiveQL on Hive 3'),
        sh('''
$ hdfs dfs -ls /warehouse/tablespace/managed/hive/cdac.db/marks_acid
drwxr-xr-x  .../marks_acid/delta_0000001_0000001_0000
drwxr-xr-x  .../marks_acid/delta_0000002_0000002_0000         <- UPDATE: new version
drwxr-xr-x  .../marks_acid/delete_delta_0000002_0000002_0000  <- UPDATE: old version removed
drwxr-xr-x  .../marks_acid/delete_delta_0000003_0000003_0000  <- DELETE
# after major compaction:
drwxr-xr-x  .../marks_acid/base_0000003
''', 'Directory layout (illustrative)'),
        note('These statements need a real Hive 3 server; Spark SQL, which ran the other examples, cannot write Hive ACID tables, so no output is shown here.', 'Note'),
        title='Example'),
    steps(
        ('Enable the transaction manager', '<code>hive.support.concurrency=true</code>, <code>hive.txn.manager=...DbTxnManager</code> (set by default in HDP/CDP).'),
        ('Enable compaction on the metastore', '<code>hive.compactor.initiator.on=true</code>, <code>hive.compactor.worker.threads&gt;0</code>.'),
        ('Create the table', 'Managed, <code>STORED AS ORC</code>, <code>TBLPROPERTIES (\'transactional\'=\'true\')</code>.'),
        ('Use UPDATE / DELETE / MERGE', 'Batch changes: one MERGE of 10,000 rows is far better than 10,000 UPDATEs.'),
        ('Monitor', '<code>SHOW COMPACTIONS</code>, <code>SHOW LOCKS</code>, <code>SHOW TRANSACTIONS</code>.'),
        title='Steps to Create an ACID Table'),
    crossq(
        ('Can external tables be transactional?', 'No. Hive must own the files to manage deltas and compaction.'),
        ('Minor vs major compaction?', 'Minor merges delta files into one delta (and delete deltas into one); major rewrites base + all deltas into a new base, physically removing deleted rows.'),
        ('Is Hive ACID meant for OLTP?', 'No. Each statement is a heavyweight job. It is for occasional batch corrections, GDPR deletes and MERGE-based upserts.'),
        ('Can Spark read Hive ACID tables?', 'Not with plain Spark SQL; it needs the Hive Warehouse Connector (Cloudera) or reading via Hive. This is one reason many teams use Iceberg/Delta/Hudi instead.'),
    ),
]),
])
