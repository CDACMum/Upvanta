from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh, conf, py

SECTION = dict(level='expert', title='Scenarios & Ecosystem', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: Design a Cassandra schema for an online exam platform.', 'Exam Platform Schema Design', minutes=12, cards=[
    definition(
        defbox('Requirements for a C-DAC online exam platform (tens of thousands of candidates per exam):'),
        ul('<strong>Q1</strong>: a student\'s result history, newest first.',
           '<strong>Q2</strong>: the merit list of an exam, highest marks first.',
           '<strong>Q3</strong>: the proctoring event timeline of one attempt (login, tab switch, answer saves), kept for 90 days.',
           '<strong>W1</strong>: a submitted result must appear in Q1 and Q2; a result can be submitted only once.'),
        p('Design: one table per query, logged batch for W1, LWT for "submit once", TTL for events.', top=True),
        tags('Schema design', 'Query-first', 'Logged batch', 'LWT', 'TTL', 'Bounded partitions'),
    ),
    analogy('An exam office keeps <strong>three registers</strong> instead of one: each student\'s mark card, each exam\'s merit list, and each '
            'candidate\'s invigilation log, each register laid out exactly as it will be read.'),
    exam_schema_anim(),
    real_world(
        scenario('Partition size check',
                 ul('<code>results_by_student</code>: ~30 rows per student over the course → tiny.',
                    '<code>results_by_exam</code>: one row per candidate, up to ~20,000 per exam → a few MB, fine. (For 10 lakh candidates, add a bucket.)',
                    '<code>events_by_attempt</code>: ~500 events per attempt → small, and expires after 90 days.')),
    ),
    example(
        cql('''
CREATE TABLE results_by_student (roll_no int, exam_date date, exam text, marks int,
  PRIMARY KEY ((roll_no), exam_date, exam)) WITH CLUSTERING ORDER BY (exam_date DESC, exam ASC);

CREATE TABLE results_by_exam (exam text, marks int, roll_no int, name text,
  PRIMARY KEY ((exam), marks, roll_no)) WITH CLUSTERING ORDER BY (marks DESC, roll_no ASC);

CREATE TABLE attempt_status (exam text, roll_no int, status text, PRIMARY KEY ((exam, roll_no)));

CREATE TABLE events_by_attempt (exam text, roll_no int, event_time timestamp, event text, detail text,
  PRIMARY KEY ((exam, roll_no), event_time)) WITH default_time_to_live = 7776000;

-- results already submitted by other candidates
INSERT INTO results_by_exam (exam, marks, roll_no, name) VALUES ('SQL-2026-10', 91, 2402, 'Aarshvi');
INSERT INTO results_by_exam (exam, marks, roll_no, name) VALUES ('SQL-2026-10', 76, 2403, 'Vineeta');
INSERT INTO results_by_exam (exam, marks, roll_no, name) VALUES ('SQL-2026-10', 97, 2417, 'Meera');

-- during the exam
INSERT INTO attempt_status (exam, roll_no, status) VALUES ('SQL-2026-10', 2401, 'started');
INSERT INTO events_by_attempt (exam, roll_no, event_time, event, detail) VALUES ('SQL-2026-10', 2401, '2026-10-14 10:00:03+0530', 'login', '10.0.4.17');
INSERT INTO events_by_attempt (exam, roll_no, event_time, event, detail) VALUES ('SQL-2026-10', 2401, '2026-10-14 10:14:51+0530', 'tab_switch', '2 s');
INSERT INTO events_by_attempt (exam, roll_no, event_time, event, detail) VALUES ('SQL-2026-10', 2401, '2026-10-14 10:15:02+0530', 'answer', 'q12');

-- W1: submit once (LWT), then write both result tables together
UPDATE attempt_status SET status = 'submitted' WHERE exam = 'SQL-2026-10' AND roll_no = 2401 IF status = 'started';
BEGIN BATCH
  INSERT INTO results_by_student (roll_no, exam_date, exam, marks) VALUES (2401, '2026-10-14', 'SQL-2026-10', 82);
  INSERT INTO results_by_exam (exam, marks, roll_no, name) VALUES ('SQL-2026-10', 82, 2401, 'Anuj');
APPLY BATCH;

-- Q1, Q2, Q3
SELECT exam_date, exam, marks FROM results_by_student WHERE roll_no = 2401;
SELECT marks, roll_no, name FROM results_by_exam WHERE exam = 'SQL-2026-10' LIMIT 3;
SELECT event_time, event, detail, TTL(event) FROM events_by_attempt WHERE exam = 'SQL-2026-10' AND roll_no = 2401;
'''),
        p('The merit list comes out sorted by marks with no sorting work, because marks is a DESC clustering column. The proctoring events '
          'show their remaining TTL (90 days).', top=True),
        title='Example'),
    steps(
        ('List queries and write paths', 'Q1–Q3, W1.'),
        ('One table per query', 'Keys from the WHERE clause and required order.'),
        ('Add correctness mechanisms', 'LWT for "only once", logged batch for multi-table writes.'),
        ('Add lifecycle settings', 'TTL for events; TWCS for the events table.'),
        ('Check partition sizes and hot spots', 'Bucket the merit list if an exam has very many candidates.'),
        title='Steps to Present a Design in an Interview'),
    crossq(
        ('Why is roll_no part of results_by_exam\'s key?', 'Without it, two students with the same marks would have the same primary key and one row '
         'would overwrite the other.'),
        ('How do you correct a mark after evaluation?', 'Update results_by_student, and in results_by_exam delete the row with the old marks and insert '
         'one with the new marks (marks is a clustering column), in one logged batch.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: Model a chat/messaging feature (like a class discussion group) in Cassandra.', 'Messaging Schema Design', minutes=10, cards=[
    definition(
        defbox('Messaging is a classic Cassandra workload: very high write rates, reads of the latest messages, scrolling back in time. Design:'),
        ul('<code>messages_by_conversation</code>: partition <code>((conversation_id, month))</code>, clustering <code>message_id timeuuid DESC</code>.',
           'Open a chat = first 50 rows of the current month. Scroll back = <code>message_id &lt; last_seen_id</code>, then the previous month.',
           '<code>conversations_by_user</code>: the inbox, ordered by last activity (rewritten when a new message arrives).',
           '<code>timeuuid</code> makes every message unique and time-ordered even when sent in the same millisecond.'),
        tags('timeuuid', 'Time bucket', 'Cursor pagination', 'Inbox table', 'High write rate'),
    ),
    analogy('Each class group has a <strong>notebook per month</strong>; new messages are written at the top. Reading the latest messages means '
            'opening this month\'s notebook; scrolling back means turning pages, then picking up last month\'s notebook.'),
    chat_anim(),
    real_world(
        scenario('At scale',
                 p('Discord famously stored billions of messages in Cassandra (and later in ScyllaDB) using exactly this pattern: channel + time bucket as the '
                   'partition key and a time-ordered ID as the clustering column.')),
    ),
    example(
        cql('''
CREATE TABLE messages_by_conversation (
  conversation_id text, month text, message_id timeuuid, sender text, body text,
  PRIMARY KEY ((conversation_id, month), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);

INSERT INTO messages_by_conversation (conversation_id, month, message_id, sender, body)
VALUES ('dbda-group', '2026-10', now(), 'Vineeta', 'Lab at 2 pm today');
!sleep 540
INSERT INTO messages_by_conversation (conversation_id, month, message_id, sender, body)
VALUES ('dbda-group', '2026-10', now(), 'Anuj', 'Thanks!');
!sleep 120
INSERT INTO messages_by_conversation (conversation_id, month, message_id, sender, body)
VALUES ('dbda-group', '2026-10', now(), 'Aarshvi', 'Notes uploaded to the portal');

-- open the chat: newest first
SELECT toTimestamp(message_id) AS sent_at, sender, body
FROM messages_by_conversation WHERE conversation_id = 'dbda-group' AND month = '2026-10' LIMIT 2;

-- scroll back: older than the oldest message on screen (cursor = its timeuuid)
SELECT toTimestamp(message_id) AS sent_at, sender, body
FROM messages_by_conversation WHERE conversation_id = 'dbda-group' AND month = '2026-10'
  AND message_id < maxTimeuuid('2026-10-14 04:38:00+0000') LIMIT 2;
'''),
        p('In a real application the cursor is the exact <code>message_id</code> of the last row shown. Here <code>maxTimeuuid()</code> builds the '
          'largest possible timeuuid for a moment in time, which is handy for time-based paging.', top=True),
        title='Example'),
    steps(
        ('Partition by conversation + time bucket', 'Bucket size from the busiest conversation\'s volume.'),
        ('Cluster by timeuuid DESC', 'Unique, ordered, newest first.'),
        ('Paginate with a cursor', 'Never with OFFSET (not supported); pass the last seen ID.'),
        ('Maintain an inbox table', 'Write it in the same request as the message.'),
        title='Steps'),
    crossq(
        ('Why not use timestamp as the clustering column?', 'Two messages in the same millisecond would get the same key and one would overwrite the other.'),
        ('How do you delete a message?', 'Delete the row (one tombstone per message is fine); for "delete for everyone" in big groups, prefer a '
         '<code>deleted</code> flag to avoid many tombstones in hot partitions.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('How is Cassandra used in data engineering pipelines with Spark and Kafka?', 'Cassandra with Spark & Kafka', minutes=10, cards=[
    definition(
        defbox('Cassandra is usually the <strong>operational serving store</strong> in a pipeline, not the analytics engine:'),
        ul('<strong>Kafka → Cassandra</strong>: the DataStax Apache Kafka Connector (sink) or a Spark Structured Streaming job writes events into query '
           'tables, mapping topic fields to columns.',
           '<strong>Spark Cassandra Connector</strong>: reads tables in parallel (one Spark partition per group of token ranges, data-locality aware), '
           'pushes down partition-key and clustering predicates, and writes DataFrames back (<code>df.write.format("org.apache.spark.sql.cassandra")</code>).',
           '<strong>Exports to the lake</strong>: Spark jobs unload tables to Parquet/Iceberg for warehouse analytics and joins.',
           '<strong>CDC</strong>: with <code>cdc_enabled</code>, commit-log segments are exposed for change capture (e.g. Debezium connector).',
           '<strong>DSBulk</strong>: command-line bulk loading and unloading (CSV/JSON).'),
        tags('Spark Cassandra Connector', 'Kafka Connect sink', 'Structured Streaming', 'CDC', 'DSBulk', 'Serving layer'),
    ),
    analogy('Cassandra is the <strong>shop counter</strong>: always open, instantly finds an item by its code. Spark is the <strong>back-office '
            'accountant</strong> who periodically takes the stock lists and builds the monthly reports.'),
    pipeline_anim(),
    real_world(
        scenario('Exam analytics pipeline',
                 p('Answer-save events flow through Kafka into <code>events_by_attempt</code> (serving the live proctor dashboard). Every night a Spark '
                   'job reads the day\'s results with the connector, joins them with course data from PostgreSQL, writes centre-wise statistics back into '
                   'a small Cassandra summary table for the portal, and exports Parquet files for the warehouse.')),
    ),
    example(
        py('''
from pyspark.sql import SparkSession, functions as F

spark = (SparkSession.builder.appName("exam-stats")
         .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1")
         .config("spark.cassandra.connection.host", "10.0.1.11")
         .config("spark.cassandra.connection.localDC", "dc_pune")       # analytics DC
         .getOrCreate())

results = (spark.read.format("org.apache.spark.sql.cassandra")
           .options(keyspace="exam_live", table="results_by_exam").load()
           .filter(F.col("exam") == "SQL-2026-10"))                       # pushed down to Cassandra

stats = results.agg(F.count("*").alias("candidates"), F.avg("marks").alias("avg_marks"))

(stats.withColumn("exam", F.lit("SQL-2026-10"))
      .write.format("org.apache.spark.sql.cassandra")
      .options(keyspace="exam_live", table="exam_stats").mode("append").save())
''', 'PySpark with the Spark Cassandra Connector'),
        conf('''
{
  "name": "exam-events-sink",
  "config": {
    "connector.class": "com.datastax.oss.kafka.sink.CassandraSinkConnector",
    "topics": "exam-events",
    "contactPoints": "10.0.1.11",
    "loadBalancing.localDc": "dc_mumbai",
    "topic.exam-events.exam_live.events_by_attempt.mapping":
      "exam=value.exam, roll_no=value.roll, event_time=value.ts, event=value.type, detail=value.detail"
  }
}
''', 'Kafka Connect sink configuration'),
        sh('''
$ dsbulk unload -k exam_live -t results_by_exam -url /data/export/results     # table → CSV files
$ dsbulk load   -k exam_live -t results_by_student -url results.csv -header true
''', 'DSBulk'),
        title='Example'),
    steps(
        ('Model serving tables first', 'Pipelines write into query-shaped tables.'),
        ('Isolate analytics', 'Point Spark at a separate analytics DC (<code>localDC</code>) so batch scans do not hurt live traffic.'),
        ('Push predicates down', 'Filter on partition/clustering keys so the connector reads less.'),
        ('Use idempotent writes', 'Streaming retries then cannot create duplicates.'),
        title='Steps'),
    crossq(
        ('How does the connector parallelise a full-table read?', 'It splits the token ring into ranges, groups them into Spark partitions (by '
         '<code>spark.cassandra.input.split.sizeInMB</code>) and reads each range with <code>token(pk) &gt; ? AND token(pk) &lt;= ?</code> queries, '
         'preferring executors on the replica nodes.'),
        ('Why not run heavy aggregations directly in Cassandra?', 'CQL aggregates run on one coordinator and are meant for single partitions; table-wide '
         'aggregation needs a distributed engine like Spark.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Troubleshooting: How do you diagnose slow queries and timeouts in Cassandra?', 'Performance Troubleshooting', minutes=11, cards=[
    definition(
        table(['Symptom', 'Likely cause', 'How to confirm', 'Fix'], [
            ['Read timeouts on one table', 'Large partitions', '<code>nodetool tablehistograms</code>, "Writing large partition" warnings', 'Bucket the partition key'],
            ['Slow reads, tombstone warnings', 'Delete/TTL-heavy pattern, queue anti-pattern', 'Tombstone warnings in system.log, tracing', 'Redesign; TWCS + TTL; avoid nulls'],
            ['Latency rising over days', 'Compaction falling behind', '<code>nodetool compactionstats</code>, SSTables per read', 'Throughput, strategy (LCS/UCS), disk I/O'],
            ['One node overloaded', 'Hot partition or uneven tokens', 'Per-node metrics, <code>nodetool toppartitions</code>, <code>status</code>', 'Bucketing, rebalance'],
            ['Long GC pauses', 'Heap pressure: big partitions, large batches', 'GC logs, <code>nodetool gcstats</code>', 'Fix the model; JVM/heap tuning (G1/ZGC)'],
            ['Timeouts cluster-wide', 'ALLOW FILTERING / full scans', 'Slow query log, tracing', 'Query tables or SAI'],
        ]),
        tags('nodetool', 'tablehistograms', 'tombstones', 'compactionstats', 'tracing', 'toppartitions', 'GC'),
    ),
    analogy('A doctor first checks <strong>temperature and pulse</strong> (metrics), then orders <strong>specific tests</strong> (nodetool, tracing), '
            'and only then prescribes. In Cassandra the diagnosis is very often "the table design does not fit the query".'),
    troubleshoot_anim(),
    real_world(
        scenario('The slow attendance report',
                 p('Read latency for <code>attendance_by_centre</code> grew from 5 ms to 800 ms over a semester. <code>tablehistograms</code> showed a max '
                   'partition size of 1.2 GB: the key was just <code>centre</code>, so each centre\'s partition grew forever. Re-keying to '
                   '<code>(centre, day)</code> and backfilling with Spark brought reads back under 5 ms.')),
    ),
    example(
        sh('''
$ nodetool tpstats                        # thread pools: pending / blocked / dropped messages
$ nodetool tablestats cdac.attendance_by_centre
$ nodetool tablehistograms cdac attendance_by_centre
$ nodetool toppartitions cdac attendance_by_centre 10000   # sample hot partitions for 10 s
$ nodetool compactionstats
$ grep -E "large partition|tombstone" /var/log/cassandra/system.log | tail
''', 'Diagnostic commands (real cluster)'),
        cq('''
TRACING ON;
SELECT * FROM cdac.attendance_by_centre WHERE centre = 'Kharghar' LIMIT 100;
-- look for: number of sstables merged, "Read N live rows and M tombstone cells", nodes contacted
''', 'Tracing one query'),
        conf('''
# cassandra.yaml guardrails (4.1+/5.0) that stop bad patterns early
partition_size_warn_threshold: 100MiB
tombstone_warn_threshold: 1000
allow_filtering_enabled: false
''', 'Guardrails'),
        title='Example'),
    steps(
        ('Find which table and query', 'Application metrics, slow query log (<code>slow_query_log_timeout</code>).'),
        ('Trace it', 'TRACING ON: SSTables merged, tombstones, replicas.'),
        ('Check table statistics', 'Partition size, SSTables per read, tombstones per slice.'),
        ('Check node health', 'tpstats (dropped messages), GC, disk, compaction backlog.'),
        ('Fix the root cause', 'Usually the data model: bucket, re-key or add a query table.'),
        title='Steps'),
    crossq(
        ('What does "dropped MUTATION messages" in tpstats mean?', 'The node was too overloaded to apply some writes before their timeout; they were '
         'dropped (hints/repair recover them). It signals overload: too much traffic, slow disks, GC or compaction.'),
        ('Is adding nodes a fix for a large partition?', 'No. A partition lives on RF replicas no matter how many nodes exist; only changing the partition '
         'key spreads it.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Compare Cassandra with HBase, MongoDB and DynamoDB. How do you choose?', 'Cassandra vs HBase vs MongoDB vs DynamoDB', minutes=10, cards=[
    definition(
        table(['', 'Cassandra', 'HBase', 'MongoDB', 'DynamoDB'], [
            ['Data model', 'Wide-column (partitions + clustering rows)', 'Wide-column (row key + column families)', 'Documents (BSON)', 'Key-value / wide-column (partition + sort key)'],
            ['Architecture', 'Masterless ring', 'HMaster + RegionServers on HDFS, ZooKeeper', 'Replica sets (one primary), sharding via mongos', 'Fully managed AWS service'],
            ['Consistency', 'Tunable (AP by default)', 'Strong per row (CP)', 'Strong on primary; tunable read/write concern', 'Eventual or strong reads per request'],
            ['Multi-region', 'Built-in, active-active', 'Replication add-on', 'Atlas global clusters / zone sharding', 'Global tables'],
            ['Query flexibility', 'Key-based CQL, SAI', 'Get/Scan by row key, filters', 'Rich queries, aggregation, many indexes', 'Key-based, GSI/LSI'],
            ['Best at', 'Massive writes, always-on, multi-DC', 'Hadoop-integrated random read/write', 'General application data, flexible queries', 'Serverless apps on AWS'],
        ]),
        tags('Cassandra', 'HBase', 'MongoDB', 'DynamoDB', 'ScyllaDB', 'Choosing a database'),
    ),
    analogy('Choosing a vehicle: <strong>Cassandra</strong> is a fleet of identical buses that never all break down at once; <strong>HBase</strong> '
            'is a train on the Hadoop railway; <strong>MongoDB</strong> is a flexible car that goes anywhere; <strong>DynamoDB</strong> is a taxi service: '
            'no maintenance, pay per ride, but only in AWS city.'),
    compare_anim(),
    real_world(
        scenario('Decisions in one organisation',
                 ul('Exam event logs and IoT telemetry, multi-region, write-heavy → <strong>Cassandra</strong>.',
                    'Student portal content with changing fields and ad-hoc admin queries → <strong>MongoDB</strong>.',
                    'Random-access lookups on data already in the on-prem Hadoop cluster → <strong>HBase</strong>.',
                    'A small AWS-hosted serverless app → <strong>DynamoDB</strong>.')),
    ),
    example(
        cq('''
-- The same lookup in each system
-- Cassandra (CQL)
SELECT marks FROM marks_by_student WHERE roll_no = 2401 AND exam_date = '2026-10-05';
-- HBase shell
--   get 'marks', '2401#2026-10-05'
-- MongoDB (mongosh)
--   db.marks.find({ roll_no: 2401, exam_date: ISODate('2026-10-05') })
-- DynamoDB (AWS CLI)
--   aws dynamodb get-item --table-name marks --key '{"roll_no":{"N":"2401"},"exam_date":{"S":"2026-10-05"}}'
''', 'Same query, four databases'),
        title='Example'),
    steps(
        ('List access patterns and volumes', 'Read/write ratio, data size, latency targets.'),
        ('Decide consistency and availability needs', 'Strong vs tunable, multi-region active-active?'),
        ('Check query flexibility needs', 'Known key lookups vs ad-hoc queries.'),
        ('Consider operations and ecosystem', 'Team skills, cloud vs on-prem, managed services (Astra DB, Keyspaces, Atlas).'),
        ('Prototype with real data', 'Measure p99 latency at expected load.'),
        title='Steps to Choose'),
    crossq(
        ('What is ScyllaDB?', 'A C++ re-implementation of Cassandra (CQL- and driver-compatible) with a shard-per-core design, aiming for lower latency '
         'and fewer nodes. Concepts and data modelling are the same.'),
        ('What is Amazon Keyspaces?', 'A serverless, Cassandra-compatible (CQL) managed service on AWS. Many features match Cassandra, but some '
         '(e.g. certain consistency levels, materialized views) differ, so check compatibility.'),
        ('Why does Cassandra appear in so many interviews for data engineers?', 'It is the standard example of a distributed, AP, write-optimised store '
         'and tests understanding of partitioning, replication, consistency and query-first modelling, concepts that transfer to every big data system.'),
    ),
]),
])
