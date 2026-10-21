from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py, xml, sql

SECTION = dict(level='expert', title='Scenarios & Ecosystem', questions=[

# ------------------------------------------------------------------ 36
Q('Scenario: Design an HBase table for exam-day attendance across all C-DAC centres.', 'Attendance Table Design', minutes=11, cards=[
    definition(
        defbox('Requirements: ~20,000 candidates check in within 30 minutes at many centres; queries are (1) "attendance of centre X on day D" for coordinators and '
               '(2) "check-in record of a student" for the portal.'),
        ul('Main table key: <code>salt | centre | yyyyMMdd | roll</code> with salt = hash(roll) % 8 → the morning burst spreads over 8 regions (pre-split on "0"…"7").',
           'Centre-day report = 8 prefix scans <code>n|KHR|20261014|</code>, run in parallel and merged.',
           'Student lookup = a second table keyed <code>roll | yyyyMMdd</code> (written together with the main row).',
           'One family <code>a</code> (status, time, gate), TTL of 2 years; live per-centre totals with <code>incr</code> on a small counters table.'),
        tags('Schema design', 'Salting', 'Pre-split', 'Second table', 'Counters', 'TTL'),
    ),
    analogy('Eight check-in counters (salt buckets) at every centre gate: candidates are sent to a counter by the last digit of a hash of their roll number, and '
            'the coordinator collects the eight lists at the end.'),
    attendance_design_anim(),
    real_world(
        scenario('Why not centre|date|roll alone?',
                 p('A large centre would put thousands of check-ins into one key range at 9 am: one region, one RegionServer. Salting trades a slightly more complex '
                   'report (8 scans) for an even write load.')),
    ),
    example(
        hsh('''
create 'att_day', {NAME => 'a', TTL => 63072000}, {SPLITS => ['1', '2', '3', '4', '5', '6', '7']}
create 'att_by_roll', 'a'
create 'att_counts', 'c'
# application: salt = hash(roll) % 8  (here 2401 -> 3, 2402 -> 6, 2403 -> 3)
put 'att_day', '3|KHR|20261014|2401', 'a:time', '09:02'
put 'att_by_roll', '2401|20261014', 'a:centre', 'KHR'
incr 'att_counts', 'KHR|20261014', 'c:present', 1
put 'att_day', '6|KHR|20261014|2402', 'a:time', '09:05'
put 'att_by_roll', '2402|20261014', 'a:centre', 'KHR'
incr 'att_counts', 'KHR|20261014', 'c:present', 1
put 'att_day', '3|KHR|20261014|2403', 'a:time', '09:11'
put 'att_by_roll', '2403|20261014', 'a:centre', 'KHR'
incr 'att_counts', 'KHR|20261014', 'c:present', 1
# coordinator report: one prefix scan per salt (buckets 3 and 6 shown)
scan 'att_day', {ROWPREFIXFILTER => '3|KHR|20261014|'}
scan 'att_day', {ROWPREFIXFILTER => '6|KHR|20261014|'}
get_counter 'att_counts', 'KHR|20261014', 'c:present'
# student portal
get 'att_by_roll', '2402|20261014'
'''),
        title='Example'),
    steps(
        ('Write down the queries and the peak write rate', 'Burst of check-ins, coordinator report, student lookup.'),
        ('Design the main key for the dominant read', 'centre|day|roll, salted for writes.'),
        ('Add a table per other access path', 'roll|day for students.'),
        ('Pre-split on the salt', 'Regions ready before exam day.'),
        ('Add TTL and counters', 'Retention and live totals.'),
        title='Steps to Present the Design'),
    crossq(
        ('How many salt buckets would you use?', 'Roughly the number of RegionServers (or a small multiple), so each server takes part in the burst; more buckets mean more scans per report.'),
        ('Could Phoenix do this?', 'Yes: a table with PRIMARY KEY (centre, day, roll), SALT_BUCKETS = 8 and an index on (roll, day); Phoenix handles salting and parallel scans automatically.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Scenario: Design an HBase table for user messages / activity feeds.', 'Messages & Activity Feeds', minutes=9, cards=[
    definition(
        defbox('Row key <code>userId | reversedTimestamp | messageId</code>: all of a user\'s messages are contiguous and <strong>newest first</strong>; the message ID '
               'makes keys unique when two arrive in the same millisecond. Opening the inbox is a short prefix scan with a LIMIT; older pages continue from the last '
               'key. Family <code>m</code> holds sender, subject and body; a separate small table (or counter) stores unread counts.'),
        tags('Inbox', 'Reversed timestamp', 'Prefix scan', 'Pagination', 'Facebook Messages'),
    ),
    analogy('Each user has a <strong>pigeonhole</strong> where new letters are always put on top; you take the top 20, and next time continue from the last letter you saw.'),
    messages_anim(),
    real_world(
        scenario('At scale',
                 p('Facebook\'s 2010 Messages system chose HBase for its strong consistency per user and high write throughput, with per-user data kept together by row-key design.')),
    ),
    example(
        hsh('''
create 'inbox', 'm'
put 'inbox', 'u2401|9223370244902575807|m80', 'm:from', 'Vineeta'
put 'inbox', 'u2401|9223370244902575807|m80', 'm:body', 'Lab at 2 pm'
put 'inbox', 'u2401|9223370244902035807|m87', 'm:from', 'Aarshvi'
put 'inbox', 'u2401|9223370244902035807|m87', 'm:body', 'Notes uploaded'
put 'inbox', 'u2401|9223370244901915807|m93', 'm:from', 'Anuj'
put 'inbox', 'u2401|9223370244901915807|m93', 'm:body', 'Thanks!'
put 'inbox', 'u2402|9223370244902575807|m80', 'm:from', 'Vineeta'
# newest two messages of user 2401
scan 'inbox', {ROWPREFIXFILTER => 'u2401|', LIMIT => 2, COLUMNS => ['m:from']}
# next page: start just after the last key shown
scan 'inbox', {STARTROW => "u2401|9223370244902035807|m87\\x00", STOPROW => 'u2401}', LIMIT => 2, COLUMNS => ['m:from']}
'''),
        p('The stop row <code>u2401}</code> works because "}" sorts just after "|", so it ends the prefix range.', top=True),
        title='Example'),
    steps(
        ('Group by user in the key', 'User first.'),
        ('Reverse time for newest-first', 'Fixed-width reversed millis.'),
        ('Add a unique suffix', 'Message ID.'),
        ('Paginate by last key', 'No offsets.'),
        title='Steps'),
    crossq(
        ('What if one user (a bot) receives millions of messages?', 'Their key range becomes a hot region; add a bucket to that user\'s key (userId|bucket|…) or archive old messages to another table.'),
        ('How do you mark a message as read?', 'A put to <code>m:read</code> on that row; row-level atomicity makes it safe, and an <code>incr</code> on an unread counter keeps the badge count.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('How is HBase used with Spark, Hive and MapReduce?', 'HBase with Spark & Hive', minutes=9, cards=[
    definition(
        table(['Tool', 'How', 'Use'], [
            ['Hive', 'External table with <code>HBaseStorageHandler</code> and <code>hbase.columns.mapping</code>', 'SQL reports over HBase data, joins with Hive tables'],
            ['Spark', 'hbase-spark connector (<code>org.apache.hadoop.hbase.spark</code>), or TableInputFormat via newAPIHadoopRDD', 'ETL, ML features, writes via bulk put / bulk load'],
            ['MapReduce', 'TableMapReduceUtil, TableMapper / TableReducer', 'RowCounter, CopyTable, Export/Import, ImportTsv'],
            ['Snapshots', '<code>snapshot</code>, ExportSnapshot, TableSnapshotInputFormat', 'Analytics directly on HFiles without loading RegionServers'],
        ]),
        tags('Hive HBaseStorageHandler', 'hbase-spark', 'TableInputFormat', 'MapReduce', 'Snapshots'),
    ),
    analogy('HBase is the <strong>live counter</strong>; Hive and Spark are <strong>auditors</strong> who either queue at the counter (scans through RegionServers) '
            'or, better, take a <strong>photocopy of the records</strong> (snapshot) to the back office.'),
    spark_hive_anim(),
    real_world(
        scenario('Nightly analytics without hurting the portal',
                 p('A nightly job takes an HBase snapshot of the attendance table and runs a Spark job on it through TableSnapshotInputFormat, reading HFiles '
                   'straight from HDFS. The RegionServers serving the student portal are not touched.')),
    ),
    example(
        sql('''
CREATE EXTERNAL TABLE hbase_students (roll STRING, name STRING, city STRING, sql_marks INT)
STORED BY 'org.apache.hadoop.hive.hbase.HBaseStorageHandler'
WITH SERDEPROPERTIES ("hbase.columns.mapping" = ":key,info:name,info:city,marks:sql")
TBLPROPERTIES ("hbase.table.name" = "cdac:students");

SELECT city, AVG(sql_marks) FROM hbase_students GROUP BY city;
''', 'Hive over an HBase table'),
        py('''
df = (spark.read.format("org.apache.hadoop.hbase.spark")
      .option("hbase.columns.mapping",
              "roll STRING :key, name STRING info:name, city STRING info:city")
      .option("hbase.table", "cdac:students")
      .option("hbase.spark.use.hbasecontext", False)
      .load())
df.filter(df.city == "Mumbai").show()     # row-key and column filters are pushed down where possible
''', 'PySpark with the hbase-spark connector'),
        hq('''
snapshot 'cdac:students', 'students_20261014'
clone_snapshot 'students_20261014', 'students_copy'
''', 'Snapshots (real cluster)'),
        title='Example'),
    steps(
        ('Light queries: Hive/Spark through RegionServers', 'Small ranges, with filters pushed down.'),
        ('Heavy analytics: snapshots', 'TableSnapshotInputFormat or ExportSnapshot to another cluster.'),
        ('Writes from Spark', 'Bulk load for large volumes, BufferedMutator-based bulkPut otherwise.'),
        title='Steps'),
    crossq(
        ('Why are Hive queries on HBase slower than on ORC tables?', 'They read rows through RegionServers (row-oriented, all versions/filters applied) instead of scanning compressed columnar files directly.'),
        ('What does a snapshot copy?', 'Only metadata (the list of HFiles); the files are shared until compaction would delete them, so snapshots are fast and cheap.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Troubleshooting: What are common HBase performance problems and how do you fix them?', 'Performance Troubleshooting', minutes=10, cards=[
    definition(
        defbox('Most problems come from row key or family design, or from resource limits on RegionServers:'),
        ul('<strong>Hotspots</strong>: one server busy → salt/hash keys, pre-split, check request counts per region.',
           '<strong>Write stalls</strong> ("Blocking updates", "Too many store files") → tune flush size and compaction, fewer families, faster disks.',
           '<strong>Long GC pauses</strong> → RegionServer considered dead (ZooKeeper timeout) → off-heap BucketCache, G1/ZGC, moderate heap (≈ 16–32 GB).',
           '<strong>Slow random reads</strong> → Bloom filters, block cache size, major compaction, data locality.',
           '<strong>Too many small regions</strong> → merge / normaliser, larger max.filesize.',
           '<strong>Slow scans</strong> → scanner caching (<code>CACHE</code>), limit columns, use snapshots for analytics.'),
        tags('Hotspot', 'Write stall', 'GC pause', 'BucketCache', 'HBCK2', 'Metrics'),
    ),
    analogy('Like a hospital triage: check the <strong>vital signs</strong> (UI, metrics), find which <strong>organ</strong> (server, region, family) is struggling, '
            'and treat the cause, which is usually the design, not just the symptom.'),
    tuning_anim(),
    real_world(
        scenario('The 9 am stall',
                 p('Every morning at check-in time, one RegionServer logged "Blocking updates" and the portal timed out. Region metrics showed all writes on one region '
                   '(timestamp-led keys). Salting into 8 buckets and pre-splitting removed the stall.')),
    ),
    example(
        sh('''
# web UIs
http://master:16010            # Master: servers, regions per server, regions in transition
http://regionserver:16030      # RegionServer: requests per region, memstore, block cache, compaction queue

# command line
$ hbase canary                         # probes every region for read latency
$ hbase hbck -j hbase-hbck2.jar        # inspect / fix inconsistencies (HBase 2)
$ grep -E "Blocking updates|Too many store files|responseTooSlow|GC pause" /var/log/hbase/*regionserver*.log
''', 'Diagnostic tools'),
        xml('''
<property><name>hbase.hregion.memstore.flush.size</name><value>134217728</value></property>
<property><name>hbase.hstore.blockingStoreFiles</name><value>16</value></property>
<property><name>hbase.regionserver.handler.count</name><value>60</value></property>
<property><name>zookeeper.session.timeout</name><value>60000</value></property>
''', 'Commonly tuned settings (hbase-site.xml)'),
        title='Example'),
    steps(
        ('Find the hot or slow component', 'Master UI → server → region.'),
        ('Read the RegionServer log', 'Blocking updates, slow responses, GC pauses.'),
        ('Fix design causes first', 'Keys, families, region sizes.'),
        ('Then tune resources', 'Cache, heap/GC, handlers, compaction throughput.'),
        title='Steps'),
    crossq(
        ('Why can a GC pause kill a RegionServer?', 'If the JVM pauses longer than the ZooKeeper session timeout, the server is declared dead and its regions are reassigned; when it wakes up it aborts itself.'),
        ('What is "responseTooSlow" in the log?', 'A warning for RPCs exceeding a threshold, with details of the call: a quick way to find expensive scans or hot regions.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Compare HBase and Cassandra. When would you choose each?', 'HBase vs Cassandra', minutes=10, cards=[
    definition(
        table(['', 'HBase', 'Cassandra'], [
            ['Architecture', 'Master + RegionServers, ZooKeeper, HDFS', 'Masterless peer-to-peer ring'],
            ['CAP', 'CP: strong consistency per row', 'AP by default, tunable per query'],
            ['Key ordering', 'Global order by row key → range scans over any key range', 'Hashed partitions; order only inside a partition'],
            ['Failure behaviour', 'Regions briefly unavailable during recovery', 'Other replicas keep serving'],
            ['Multi-datacenter', 'Asynchronous replication between clusters', 'Built-in, active-active'],
            ['Atomic ops', 'Row-level atomicity, exact counters, checkAndMutate', 'Partition-level batches, LWT (Paxos), approximate counters'],
            ['Ecosystem', 'Hadoop (HDFS, MapReduce, Hive, Spark, Phoenix)', 'Standalone; Spark connector, Kafka'],
            ['Query language', 'API + shell; SQL via Phoenix', 'CQL (SQL-like)'],
        ]),
        tags('HBase', 'Cassandra', 'CP vs AP', 'Range scans', 'Multi-DC', 'Bigtable', 'Dynamo'),
    ),
    analogy('HBase is a <strong>well-organised central archive</strong> with one authoritative clerk per drawer; Cassandra is a <strong>network of branch offices</strong> '
            'that each keep copies and keep working even when cut off from each other.'),
    hbase_vs_cassandra_anim(),
    real_world(
        scenario('Choosing for C-DAC workloads',
                 ul('Attendance and results already in a Hadoop platform, needing consistent reads and range scans → <strong>HBase</strong>.',
                    'A national, always-on exam event platform across two data centres, write-heavy → <strong>Cassandra</strong>.',
                    'Either way, the data model starts from the queries and the key design.')),
    ),
    example(
        hq('''
# Same lookup in both systems
# HBase shell
get 'marks', '2401|20261005'
# Cassandra (CQL)
#   SELECT marks FROM marks_by_student WHERE roll_no = 2401 AND exam_date = '2026-10-05';
''', 'The same lookup'),
        title='Example'),
    steps(
        ('Do you already run Hadoop/HDFS?', 'HBase fits naturally.'),
        ('Must it stay writable during any failure, across regions?', 'Cassandra.'),
        ('Need range scans over arbitrary key ranges or exact counters?', 'HBase.'),
        ('Team skills and operations', 'HBase needs HDFS + ZooKeeper operations; Cassandra is self-contained.'),
        title='Steps to Choose'),
    crossq(
        ('What do they have in common?', 'Both are wide-column stores derived from Bigtable\'s storage design: in-memory buffer, append-only log, immutable sorted files, compaction, Bloom filters, versions/timestamps.'),
        ('What about Google Cloud Bigtable?', 'Google\'s managed Bigtable service exposes an HBase-compatible API, so HBase knowledge transfers directly.'),
    ),
]),
])
