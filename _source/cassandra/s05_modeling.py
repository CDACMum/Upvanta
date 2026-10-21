from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh, conf, py

SECTION = dict(level='intermediate', title='Data Modeling', questions=[

# ------------------------------------------------------------------ 21
Q('How do you design a data model in Cassandra? Explain query-first modelling.', 'Query-First Modelling', minutes=11, cards=[
    definition(
        defbox('Cassandra data modelling is <strong>query-driven</strong>: you start from the application\'s access patterns and design '
               '<strong>one table per query</strong> (or per small group of queries), so that every read is served by <strong>one partition</strong>. '
               'The widely taught method (Chebotko) has four steps: conceptual model (entities, relationships) → <strong>application workflow</strong> '
               '(list of queries) → <strong>logical model</strong> (tables with keys chosen from the queries) → <strong>physical model</strong> (types, '
               'bucketing, size checks, compaction, TTL).',
               'Mapping rules: <strong>equality predicates → partition key</strong>; <strong>range predicates and required ordering → clustering '
               'columns</strong>; add columns to make each row unique; denormalise data instead of joining.'),
        tags('Query-first', 'Chebotko diagram', 'One table per query', 'Denormalisation', 'Access patterns'),
    ),
    analogy('A <strong>restaurant kitchen</strong> preps ingredients for the menu it actually serves. You do not stock a raw cow and expect to '
            'serve any dish quickly; you prepare exactly what each dish needs, even if the same onions are chopped for three dishes.'),
    query_first_anim(),
    real_world(
        scenario('Exam portal queries → tables',
                 table(['Query', 'Table', 'Primary key'], [
                     ['Q1 A student\'s marks, newest first', '<code>marks_by_student</code>', '<code>((roll_no), exam_date DESC, module)</code>'],
                     ['Q2 Merit list of an exam', '<code>marks_by_exam</code>', '<code>((exam), marks DESC, roll_no)</code>'],
                     ['Q3 Attendance of a centre on a day', '<code>attendance_by_centre_day</code>', '<code>((centre, day), roll_no)</code>'],
                 ])),
    ),
    example(
        cql('''
CREATE TABLE marks_by_student (roll_no int, exam_date date, module text, marks int, PRIMARY KEY ((roll_no), exam_date, module))
  WITH CLUSTERING ORDER BY (exam_date DESC, module ASC);
CREATE TABLE marks_by_exam (exam text, marks int, roll_no int, name text, PRIMARY KEY ((exam), marks, roll_no))
  WITH CLUSTERING ORDER BY (marks DESC, roll_no ASC);

-- one result is written to both tables
BEGIN BATCH
  INSERT INTO marks_by_student (roll_no, exam_date, module, marks) VALUES (2401, '2026-10-05', 'Spark', 84);
  INSERT INTO marks_by_exam (exam, marks, roll_no, name) VALUES ('Spark-2026-10', 84, 2401, 'Anuj');
APPLY BATCH;
BEGIN BATCH
  INSERT INTO marks_by_student (roll_no, exam_date, module, marks) VALUES (2402, '2026-10-05', 'Spark', 88);
  INSERT INTO marks_by_exam (exam, marks, roll_no, name) VALUES ('Spark-2026-10', 88, 2402, 'Aarshvi');
APPLY BATCH;
BEGIN BATCH
  INSERT INTO marks_by_student (roll_no, exam_date, module, marks) VALUES (2403, '2026-10-05', 'Spark', 84);
  INSERT INTO marks_by_exam (exam, marks, roll_no, name) VALUES ('Spark-2026-10', 84, 2403, 'Vineeta');
APPLY BATCH;

-- Q2: top 3 of the exam, already sorted on disk
SELECT marks, roll_no, name FROM marks_by_exam WHERE exam = 'Spark-2026-10' LIMIT 3;
'''),
        p('<code>roll_no</code> is a clustering column after <code>marks</code> so that two students with the same marks (84) are two different rows '
          'instead of one overwriting the other.', top=True),
        title='Example: Two Tables for Two Queries'),
    steps(
        ('List entities and relationships', 'Student, exam, centre, attempt.'),
        ('Write the application workflow', 'Every screen → its query with inputs and ordering.'),
        ('Design one table per query', 'Equality → partition key; range/order → clustering; add uniqueness columns.'),
        ('Check partition size and write cost', 'Bucket if partitions can grow without limit; count tables written per action.'),
        ('Decide how tables stay in sync', 'Logged batches, or idempotent writes from a stream processor.'),
        title='Steps'),
    crossq(
        ('Is duplicating data not wasteful?', 'Disk is cheap and Cassandra compresses data. Network round trips to many nodes, scans and joins are what '
         'is expensive at scale, so trading storage for single-partition reads is the right trade.'),
        ('What if a new query appears later?', 'Create a new table for it and backfill it (Spark job or DSBulk unload/load), then write to it as well '
         'from the application.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How do you handle relationships without joins? Explain denormalisation.', 'Denormalisation', minutes=9, cards=[
    definition(
        defbox('Cassandra has no joins, so data that a query needs from several entities is <strong>copied into the query\'s table</strong> at write time '
               '(<strong>denormalisation</strong>). The application (or a pipeline) writes every change to all tables that contain the data.',
               'Patterns: <strong>lookup tables</strong> (students_by_email → roll_no), <strong>copying attributes</strong> (exam name stored in every '
               'result row), <strong>static columns</strong> for one-to-many in one partition, <strong>collections/UDTs</strong> for small nested data. '
               'Changing a value that is part of a key means deleting and re-inserting the row.'),
        tags('Denormalisation', 'Lookup table', 'Data duplication', 'Write amplification', 'Application-side join'),
    ),
    analogy('A school keeps the student\'s name on the <strong>ID card, the hall ticket and the mark sheet</strong>. Nobody looks up a central '
            'register to print a hall ticket. When a name changes, every document has to be reprinted.'),
    denorm_anim(),
    real_world(
        scenario('Login by email, profile by roll number',
                 p('Students log in with their email but the rest of the system uses roll numbers. A small <code>students_by_email</code> table maps email → '
                   'roll number and name; both tables are written in a logged batch at registration, and an email change deletes the old lookup row and '
                   'inserts the new one in the same batch.')),
    ),
    example(
        cql('''
-- change of email: remove the old lookup row, insert the new one, update the profile
BEGIN BATCH
  DELETE FROM students_by_email WHERE email = 'riya@cdac.in';
  INSERT INTO students_by_email (email, roll_no, name) VALUES ('riya.k@cdac.in', 2405, 'Riya');
  UPDATE students_by_roll SET email = 'riya.k@cdac.in' WHERE roll_no = 2405;
APPLY BATCH;

SELECT * FROM students_by_email;
SELECT * FROM students_by_roll WHERE roll_no = 2405;
''', setup='''
CREATE TABLE students_by_roll  (roll_no int PRIMARY KEY, email text, name text);
CREATE TABLE students_by_email (email text PRIMARY KEY, roll_no int, name text);
INSERT INTO students_by_roll (roll_no, email, name) VALUES (2405, 'riya@cdac.in', 'Riya');
INSERT INTO students_by_email (email, roll_no, name) VALUES ('riya@cdac.in', 2405, 'Riya');
'''),
        title='Example: Keeping Two Tables in Sync'),
    steps(
        ('Identify which tables hold a copy of each attribute', 'Document it next to the schema.'),
        ('Write all copies together', 'Logged batch, or one stream-processing job that owns the writes.'),
        ('Handle key changes as delete + insert', 'Old lookup row must be removed.'),
        ('Reconcile periodically', 'A Spark job can compare tables and repair drift.'),
        title='Steps'),
    crossq(
        ('Could you join in the application instead?', 'Yes, for small fan-outs: read the parent, then fetch a few children asynchronously. For lists of '
         'hundreds of items this becomes slow; denormalise those.'),
        ('What about data that changes very often (e.g. a student\'s display name everywhere)?', 'Copy only what the query really needs, store rarely '
         'changing data in copies, and keep frequently changing data in one place fetched by key.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('What are hot partitions and large partitions? How do you avoid them?', 'Partition Size & Hot Spots', minutes=9, cards=[
    definition(
        defbox('A <strong>large partition</strong> holds too much data (common guideline: keep partitions under about <strong>100 MB</strong> and '
               '<strong>100,000 rows</strong>). It slows reads, compaction, repair and streaming, and stresses the JVM heap. Cassandra logs a warning for '
               'partitions larger than <code>compaction_large_partition_warning_threshold</code>.',
               'A <strong>hot partition</strong> receives a disproportionate share of traffic. Because a partition lives on exactly RF replicas, those nodes '
               'become the bottleneck while the rest of the cluster is idle. Causes: low-cardinality partition keys (status, country, date only) or '
               'celebrity keys. Fixes: <strong>time bucketing</strong> and <strong>synthetic sharding</strong> (bucket = hash(id) % N).'),
        tags('Large partition', 'Hot partition', 'Bucketing', 'Synthetic shard', 'Cardinality'),
    ),
    analogy('All admission forms of the state dropped into <strong>one counter</strong> at one office: the queue there is endless while other '
            'counters sit idle. Opening counters by district and day spreads the queue.'),
    hot_partition_anim(),
    real_world(
        scenario('Result-day traffic',
                 p('On result day, every student opens the merit list of the same exam: one partition, very hot. The team caches the merit list in the '
                   'application and also splits <code>marks_by_exam</code> into 4 buckets by <code>roll_no % 4</code> so reads and writes spread across '
                   '4× more replicas.')),
    ),
    example(
        cql('''
CREATE TABLE logins_by_day (
  day     date,
  bucket  int,          -- roll_no % 4, computed by the application
  ts      timestamp,
  roll_no int,
  PRIMARY KEY ((day, bucket), ts, roll_no)
);

INSERT INTO logins_by_day (day, bucket, ts, roll_no) VALUES ('2026-10-14', 1, '2026-10-14 09:00:01+0530', 2401);
INSERT INTO logins_by_day (day, bucket, ts, roll_no) VALUES ('2026-10-14', 2, '2026-10-14 09:00:02+0530', 2402);
INSERT INTO logins_by_day (day, bucket, ts, roll_no) VALUES ('2026-10-14', 3, '2026-10-14 09:00:02+0530', 2403);
INSERT INTO logins_by_day (day, bucket, ts, roll_no) VALUES ('2026-10-14', 0, '2026-10-14 09:00:03+0530', 2404);

-- each bucket is a different partition with its own token, so different replicas
SELECT day, bucket, token(day, bucket), roll_no FROM logins_by_day;

-- a reader asks all buckets (better: 4 parallel queries) and merges the results
SELECT count(*) AS logins FROM logins_by_day WHERE day = '2026-10-14' AND bucket IN (0, 1, 2, 3);
'''),
        sh('''
$ nodetool tablehistograms cdac logins_by_day
Percentile  Read Latency  Write Latency  SSTables  Partition Size  Cell Count
                (micros)       (micros)                 (bytes)
50%                 ...            ...         1          ...           ...
99%                 ...            ...         2          ...           ...
Max                 ...            ...         3          ...           ...
''', 'Checking partition sizes (real cluster)'),
        title='Example'),
    steps(
        ('Estimate partition size', 'Rows per partition × average row size, over the data\'s lifetime.'),
        ('Add a time bucket', 'Hour/day/month depending on volume.'),
        ('Add a synthetic bucket if one key is hot', 'bucket = hash(id) % N, with N chosen from expected traffic.'),
        ('Monitor', '<code>nodetool tablehistograms</code>, large-partition warnings, per-node request metrics.'),
        title='Steps'),
    crossq(
        ('Why can\'t Cassandra split a big partition across nodes automatically?', 'A partition is the unit of placement: it maps to one token and '
         'therefore to one set of replicas. Splitting must be done in the data model by changing the partition key.'),
        ('How does a reader find all buckets?', 'The number of buckets is fixed and known to the application (0…N-1), so it queries each one, ideally in '
         'parallel, and merges the results.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you model time-series data in Cassandra?', 'Time-Series Modelling', minutes=9, cards=[
    definition(
        defbox('Time-series data (sensor readings, logs, metrics, events) fits Cassandra well: append-only writes, reads of recent ranges, and expiry of '
               'old data. The standard design:'),
        ul('Partition key = <strong>source + time bucket</strong>: <code>((sensor_id, day))</code>, sized to keep partitions bounded.',
           'Clustering column = <strong>timestamp DESC</strong> (or timeuuid when several events can share a timestamp).',
           '<strong>TTL</strong> (or <code>default_time_to_live</code>) for retention.',
           '<strong>TimeWindowCompactionStrategy (TWCS)</strong> with a window matching the bucket, so expired data is dropped file by file.',
           'Avoid updates and deletes; write each event once.'),
        tags('Time series', 'Time bucket', 'Clustering DESC', 'TTL', 'TWCS', 'PER PARTITION LIMIT'),
    ),
    analogy('A <strong>weather station log book</strong>: a new book every day per station, newest entries on top, and books older than 30 days '
            'are thrown away as whole books, not page by page.'),
    timeseries_anim(),
    real_world(
        scenario('Lab power and temperature monitoring',
                 p('120 sensors × 1 reading/second → about 10 million rows a day. With day buckets each partition holds about 86,400 rows; the dashboard '
                   'shows the latest values with <code>PER PARTITION LIMIT 1</code> and the last hour with a clustering range. Data older than 30 days '
                   'expires automatically.')),
    ),
    example(
        cql('''
CREATE TABLE sensor_readings (
  sensor text, day date, ts timestamp, temp double, power_w int,
  PRIMARY KEY ((sensor, day), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND default_time_to_live = 2592000
  AND compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_unit': 'DAYS', 'compaction_window_size': 1};

INSERT INTO sensor_readings (sensor, day, ts, temp, power_w) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:00:00+0530', 24.5, 410);
INSERT INTO sensor_readings (sensor, day, ts, temp, power_w) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:05:00+0530', 25.3, 455);
INSERT INTO sensor_readings (sensor, day, ts, temp, power_w) VALUES ('lab-1', '2026-10-14', '2026-10-14 10:10:00+0530', 25.9, 470);
INSERT INTO sensor_readings (sensor, day, ts, temp, power_w) VALUES ('lab-2', '2026-10-14', '2026-10-14 10:00:00+0530', 22.0, 300);
INSERT INTO sensor_readings (sensor, day, ts, temp, power_w) VALUES ('lab-2', '2026-10-14', '2026-10-14 10:10:00+0530', 22.4, 315);

-- latest reading of every sensor-day
SELECT sensor, ts, temp FROM sensor_readings PER PARTITION LIMIT 1;

-- a time window for one sensor (timestamps are shown in UTC)
SELECT ts, temp, power_w FROM sensor_readings
WHERE sensor = 'lab-1' AND day = '2026-10-14'
  AND ts >= '2026-10-14 10:03:00+0530' AND ts < '2026-10-14 10:15:00+0530';

SELECT max(temp), avg(power_w) FROM sensor_readings WHERE sensor = 'lab-1' AND day = '2026-10-14';
'''),
        title='Example'),
    steps(
        ('Pick the bucket from volume', 'Rows per source per bucket should stay in the tens of thousands.'),
        ('Cluster by time DESC', 'Latest-first reads are the most common.'),
        ('Set retention', '<code>default_time_to_live</code>.'),
        ('Use TWCS', 'Window ≈ bucket size; avoid out-of-order writes into old windows.'),
        ('Query ranges across buckets in the app', 'Compute the buckets that cover the range, query each.'),
        title='Steps'),
    crossq(
        ('Why use timeuuid instead of timestamp as the clustering column?', 'If two events from the same source can have the same millisecond, a timestamp '
         'key would overwrite one of them. A timeuuid is unique and still sorts by time.'),
        ('Why does TWCS suit TTL data?', 'Each SSTable contains one time window. When all its data has expired, the whole file is deleted without '
         'compaction work or tombstone scanning.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What are materialized views? Why are they discouraged in production?', 'Materialized Views', minutes=8, cards=[
    definition(
        defbox('A <strong>materialized view</strong> (MV) is a table that Cassandra maintains automatically from a base table with a <strong>different '
               'primary key</strong>: <code>CREATE MATERIALIZED VIEW v AS SELECT … FROM base WHERE … IS NOT NULL PRIMARY KEY (…)</code>. The view\'s key '
               'must contain all base-table key columns plus at most one other column.',
               'Since Cassandra 4.0 MVs are <strong>experimental and disabled by default</strong> (<code>materialized_views_enabled: false</code>). The '
               'view is updated asynchronously after a read-before-write on the base replica, and views can <strong>diverge</strong> from their base '
               'table without an effective way to detect or fix it. Most teams maintain query tables themselves or use SAI.'),
        tags('Materialized view', 'Experimental', 'materialized_views_enabled', 'View drift', 'Alternative: SAI'),
    ),
    analogy('An <strong>automatic photocopier</strong> that is supposed to update the copy in the other office whenever you change the original. '
            'Convenient, but sometimes a page is not copied, and there is no list of which pages were missed.'),
    mv_anim(),
    real_world(
        scenario('What teams do instead',
                 ul('Application writes both tables in a logged batch (full control, testable).',
                    'An SAI index for occasional lookups by a non-key column.',
                    'A Kafka/Spark pipeline that builds read-optimised tables from the event stream.')),
    ),
    example(
        cql('''
CREATE TABLE students (roll_no int PRIMARY KEY, name text, city text);
INSERT INTO students (roll_no, name, city) VALUES (2401, 'Anuj', 'Pune');
INSERT INTO students (roll_no, name, city) VALUES (2402, 'Aarshvi', 'Mumbai');
INSERT INTO students (roll_no, name, city) VALUES (2408, 'Kiran', 'Pune');

CREATE MATERIALIZED VIEW students_by_city AS
  SELECT city, roll_no, name FROM students
  WHERE city IS NOT NULL AND roll_no IS NOT NULL
  PRIMARY KEY ((city), roll_no);

SELECT * FROM students_by_city WHERE city = 'Pune';

UPDATE students SET city = 'Mumbai' WHERE roll_no = 2408;
SELECT * FROM students_by_city WHERE city = 'Pune';

INSERT INTO students_by_city (city, roll_no, name) VALUES ('Nagpur', 2499, 'X');
''', expect_error=True),
        p('This run assumes <code>materialized_views_enabled: true</code>. On a default Cassandra 4.0+ node, the CREATE statement fails with '
          '"Materialized views are disabled. Enable in cassandra.yaml to use."', top=True),
        title='Example'),
    steps(
        ('Prefer an application-maintained table', 'Write it in the same logged batch as the base table.'),
        ('Or index the column with SAI', 'For lower-traffic lookups.'),
        ('If you must use an MV', 'Enable it explicitly, keep the view key simple, and monitor for divergence.'),
        title='Steps'),
    crossq(
        ('Why must every view key column be IS NOT NULL?', 'A row with a null key column has no place in the view\'s partitioning, so it is excluded explicitly.'),
        ('Can you write to a view directly?', 'No: "Cannot directly modify a materialized view". Writes go to the base table only.'),
    ),
]),
])
