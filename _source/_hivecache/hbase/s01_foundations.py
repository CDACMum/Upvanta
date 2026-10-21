from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py, xml

RUN_NOTE = note('Every HBase shell example with an Output box was executed while this page was built. It ran on an HBase shell engine '
                'that follows Apache HBase 2.x behaviour: byte-ordered row keys, column families, versions and timestamps, delete markers, '
                'TTL, filters and counters. The output is in hbase shell format; the shell\'s "Took N seconds" timing lines are left out '
                'and timestamps are shown in IST. Cluster-level commands (regions, compaction, replication) are shown without output.',
                'How the examples were run')

SECTION = dict(level='beginner', title='HBase Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Apache HBase? What are its features and when should you use it?', 'What is HBase', minutes=8, cards=[
    definition(
        defbox('<strong>Apache HBase</strong> is an open-source, distributed, column-family-oriented <strong>NoSQL database</strong> that runs on top of '
               '<strong>HDFS</strong>. It is modelled on Google\'s <strong>Bigtable</strong> and provides <strong>random, real-time read/write access</strong> '
               'to very large tables: billions of rows and millions of columns.',
               'Key features: strongly consistent reads and writes per row, automatic sharding of tables into <strong>regions</strong>, automatic failover '
               'of RegionServers, rows sorted by key (fast range scans), multiple versions per cell, block cache and Bloom filters, and integration with '
               'MapReduce, Spark, Hive and Phoenix. The current stable line is HBase 2.x (2.5/2.6).'),
        tags('NoSQL', 'Wide-column', 'Bigtable', 'HDFS', 'Random read/write', 'Strong consistency', 'Regions'),
    ),
    analogy('HDFS is a <strong>warehouse of sealed cartons</strong>: great for storing and shipping whole cartons. HBase is the <strong>indexed '
            'shelving system</strong> built inside that warehouse, so you can pick or replace one item by its label in seconds.'),
    what_is_hbase_anim(),
    real_world(
        scenario('Who uses it',
                 ul('Facebook Messages (2010) and many large Chinese internet companies (Alibaba, Xiaomi) ran some of the biggest deployments.',
                    'Banks and telecoms keep customer event history (call records, transactions) for real-time lookups next to their Hadoop data lake.',
                    'At C-DAC scale: per-student activity and attendance history that must be updated live and read by key, on the same Hadoop cluster used for analytics.')),
    ),
    example(
        RUN_NOTE,
        hsh('''
create 'students', 'info', 'marks'
put 'students', '2401', 'info:name', 'Anuj'
put 'students', '2401', 'info:city', 'Pune'
put 'students', '2401', 'marks:sql', '78'
put 'students', '2402', 'info:name', 'Aarshvi'
get 'students', '2401'
scan 'students'
'''),
        title='Example: Your First HBase Table'),
    steps(
        ('Start HBase', 'Standalone mode for learning: download HBase, set <code>JAVA_HOME</code>, run <code>bin/start-hbase.sh</code> (or <code>docker run -it -p 16010:16010 harisekhon/hbase</code>).'),
        ('Open the shell', '<code>bin/hbase shell</code>'),
        ('Create a table with column families', "<code>create 'students', 'info', 'marks'</code>"),
        ('Write and read', '<code>put</code>, <code>get</code>, <code>scan</code>'),
        ('Check the web UI', 'HMaster UI at http://localhost:16010'),
        title='Steps to Try It'),
    crossq(
        ('Is HBase a column-oriented database like a columnar warehouse?', 'Not really. It is column-<strong>family</strong> oriented: each family is stored '
         'separately, but within a family data is stored row by row. Columnar warehouses (Parquet, Redshift) store each column separately for analytic scans.'),
        ('Does HBase support SQL?', 'Not natively; it has a get/put/scan API and the shell. Apache Phoenix adds SQL, and Hive can query HBase tables through a storage handler.'),
        ('When is HBase the wrong choice?', 'Small data (use an RDBMS), complex ad-hoc queries and joins (use a warehouse), or when you have no Hadoop/HDFS platform and '
         'want minimal operations (consider Cassandra or a managed service).'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('How is HBase different from an RDBMS?', 'HBase vs RDBMS', minutes=8, cards=[
    definition(
        table(['Aspect', 'RDBMS', 'HBase'], [
            ['Schema', 'Fixed columns and types', 'Only column families fixed; qualifiers created on write; all values are bytes'],
            ['Data layout', 'Rows with every column (NULLs)', 'Sparse: only written cells are stored'],
            ['Query language', 'SQL, joins, sub-queries', 'get / put / scan / filters (SQL via Phoenix)'],
            ['Indexes', 'Any number of secondary indexes', 'Only the row key (index tables / Phoenix for more)'],
            ['Transactions', 'Multi-row ACID', 'Atomic per row only'],
            ['Scaling', 'Mostly vertical', 'Horizontal: regions spread over RegionServers'],
            ['Versions', 'One value per cell', 'Several timestamped versions per cell'],
            ['Data size', 'GBs to a few TBs', 'TBs to PBs'],
        ]),
        tags('Sparse', 'Schema-less qualifiers', 'Row-level atomicity', 'No joins', 'Horizontal scaling'),
    ),
    analogy('An RDBMS table is a <strong>printed form</strong> with the same boxes for everyone, many left blank. An HBase row is a <strong>file folder</strong> '
            'with labelled sections (families) where you add only the pages you actually have.'),
    rdbms_vs_hbase_anim(),
    real_world(
        scenario('Student profiles with optional fields',
                 p('Some students have GitHub links, some have three phone numbers, some have internship details. In HBase each student row simply holds the '
                   'qualifiers it needs (<code>links:github</code>, <code>contact:phone2</code>…), with no schema change and no NULL columns.')),
    ),
    example(
        hsh('''
create 'profiles', 'info', 'links'
put 'profiles', '2401', 'info:name', 'Anuj'
put 'profiles', '2402', 'info:name', 'Aarshvi'
put 'profiles', '2402', 'info:phone', '9820011111'
# a brand-new qualifier, no ALTER TABLE needed
put 'profiles', '2403', 'info:name', 'Riya'
put 'profiles', '2403', 'links:github', 'github.com/riya-k'
scan 'profiles'
# families ARE schema: an undeclared family is rejected
put 'profiles', '2404', 'social:twitter', '@x'
''', expect_error=True),
        title='Example: Sparse Rows'),
    steps(
        ('List access patterns', 'HBase only serves key-based access efficiently.'),
        ('Design the row key', 'From the most common lookup or scan.'),
        ('Group columns into 1–3 families', 'By how they are read and how long they live.'),
        ('Denormalise', 'Store what a read needs in the row instead of joining.'),
        title='Steps to Move a Table from RDBMS to HBase'),
    crossq(
        ('What data types does HBase have?', 'None: row keys, qualifiers and values are byte arrays. The application (or Phoenix) decides how to encode numbers, dates and strings.'),
        ('Can you update a row in HBase?', 'Yes: a put to an existing row/column writes a newer version, which reads then return. Old versions are kept up to the family\'s VERSIONS setting.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('HDFS vs Hive vs HBase: when would you use each?', 'HDFS vs Hive vs HBase', minutes=7, cards=[
    definition(
        table(['', 'HDFS', 'Hive', 'HBase'], [
            ['What it is', 'Distributed file system', 'SQL engine + metastore over files', 'NoSQL database on HDFS'],
            ['Access pattern', 'Write once, sequential read', 'Batch SQL scans and aggregations', 'Random get/put by row key, range scans'],
            ['Latency', 'Seconds+ (file level)', 'Seconds to minutes', 'Milliseconds'],
            ['Updates', 'Append only', 'Limited (ACID tables)', 'Yes, per cell, with versions'],
            ['Typical use', 'Landing raw data, data lake', 'Reports, ETL, analytics', 'Serving live lookups, user profiles, event history'],
        ]),
        tags('HDFS', 'Hive', 'HBase', 'Batch vs real-time', 'Data lake'),
    ),
    analogy('HDFS is the <strong>archive room</strong>, Hive is the <strong>analyst</strong> who reads whole archive boxes to write reports, and HBase is the '
            '<strong>enquiry counter</strong> that answers "show me student 2401" instantly.'),
    when_hbase_anim(),
    real_world(
        scenario('One platform, three layers',
                 p('Daily attendance CSVs land in HDFS. Hive builds monthly attendance reports per centre. The student portal shows "my attendance today" '
                   'from HBase, which is updated live as students check in. A nightly Spark job reconciles HBase with the Hive tables.')),
    ),
    example(
        hsh('''
create 'attendance', 'a'
put 'attendance', '2401|20261014', 'a:status', 'P'
put 'attendance', '2401|20261015', 'a:status', 'A'
put 'attendance', '2402|20261014', 'a:status', 'P'
# real-time point lookup: one row by key
get 'attendance', '2401|20261015'
# a student's month: a prefix range scan
scan 'attendance', {ROWPREFIXFILTER => '2401|202610'}
'''),
        sh('''
-- Hive (batch): the same data analysed with SQL over files, minutes not milliseconds
SELECT centre, month, AVG(present) FROM attendance_history GROUP BY centre, month;
''', 'Hive for the analytics side'),
        title='Example'),
    steps(
        ('Need SQL analytics over big files?', 'Hive / Spark SQL.'),
        ('Need millisecond lookups or updates by key?', 'HBase.'),
        ('Just need to store files cheaply?', 'HDFS (or object storage).'),
        ('Need both?', 'HBase for serving; export or snapshot it for Hive/Spark analytics.'),
        title='Steps to Choose'),
    crossq(
        ('Can Hive query HBase tables?', 'Yes, with an external table using <code>org.apache.hadoop.hive.hbase.HBaseStorageHandler</code>, but such queries scan HBase and are slower than Hive on ORC/Parquet.'),
        ('Why not just use HBase for analytics?', 'HBase reads rows through RegionServers and is optimised for point and range access; columnar formats on HDFS are far faster for scanning a few columns of billions of rows.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('Explain the HBase data model: row key, column family, qualifier, cell, timestamp.', 'HBase Data Model', minutes=10, cards=[
    definition(
        table(['Term', 'Meaning'], [
            ['Table', 'Collection of rows, belongs to a namespace (<code>default</code> if none).'],
            ['Row key', 'Unique byte-array identifier of a row. Rows are stored <strong>sorted</strong> by row key (byte order). The only index.'],
            ['Column family', 'Group of columns declared at table creation. Stored separately on disk; has settings (VERSIONS, TTL, compression).'],
            ['Column qualifier', 'Name of a column within a family, created on write: <code>info:name</code>. Unlimited and different per row.'],
            ['Cell', 'The intersection {row, family:qualifier, timestamp} holding a value (bytes).'],
            ['Timestamp / version', 'Every cell value has a timestamp (ms); several versions can be kept, newest returned by default.'],
        ]),
        p('Logically HBase is a <strong>sorted, sparse, multidimensional map</strong>: '
          '<code>(row key, family, qualifier, timestamp) → value</code>.', top=True),
        tags('Row key', 'Column family', 'Qualifier', 'Cell', 'Version', 'Timestamp', 'Sparse map'),
    ),
    analogy('A <strong>library catalogue drawer</strong>: the drawer label is the row key, the colour of the card is the family, the field name on the card is '
            'the qualifier, and corrections are added as new dated cards on top instead of erasing the old ones.'),
    data_model_anim(),
    real_world(
        scenario('One row, many dimensions',
                 p('Row <code>2401</code> holds <code>info:name</code>, <code>info:city</code> (with the old city as an older version) and '
                   '<code>marks:sql</code>. Another row might have a completely different set of qualifiers in the same families.')),
    ),
    example(
        hsh('''
create 'students', {NAME => 'info', VERSIONS => 3}, {NAME => 'marks'}
put 'students', '2401', 'info:name', 'Anuj'
put 'students', '2401', 'info:city', 'Pune'
put 'students', '2401', 'marks:sql', '78'
put 'students', '2401', 'info:city', 'Mumbai'
put 'students', '2402', 'marks:spark', '88'
scan 'students'
get 'students', '2401', {COLUMN => 'info:city', VERSIONS => 3}
'''),
        p('Cells inside a row are returned sorted by family, then qualifier. The scan shows only the latest city; asking for versions shows both.', top=True),
        title='Example'),
    steps(
        ('Pick the row key', 'What is the main lookup/scan key?'),
        ('Pick families', 'Group columns by access pattern and settings; keep 1–3.'),
        ('Name qualifiers', 'Short names, possibly with data in them (e.g. a date) for wide rows.'),
        ('Decide versions', 'VERSIONS per family: 1 unless history is needed.'),
        title='Steps to Design a Table'),
    crossq(
        ('Are rows sorted by family or qualifier too?', 'Rows are sorted by row key; inside a row, cells are sorted by family, qualifier, then timestamp (newest first).'),
        ('Where is the table schema stored?', 'In the table descriptor (families and their settings), kept by the master in <code>hbase:meta</code>-related system tables / filesystem. Qualifiers are not part of the schema.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('Is HBase CP or AP? What consistency and atomicity guarantees does it give?', 'Consistency & Atomicity', minutes=8, cards=[
    definition(
        defbox('HBase is a <strong>CP</strong> system: each region is served by exactly <strong>one RegionServer</strong>, so all reads and writes of a row '
               'go through one place and always see the latest committed data (<strong>strong consistency</strong>). If that server fails, its regions are '
               'briefly <strong>unavailable</strong> until reassigned.',
               'Guarantees: operations on a <strong>single row are atomic</strong> (a put of many columns, even across families, is all-or-nothing), '
               'with atomic <code>increment</code>, <code>append</code> and <code>checkAndMutate</code>. There are <strong>no multi-row transactions</strong> '
               '(Phoenix/Omid/Tephra add them on top). Scans are not snapshot-isolated across rows.'),
        tags('CP', 'Strong consistency', 'Row-level atomicity', 'checkAndMutate', 'No multi-row transactions'),
    ),
    analogy('Each <strong>file has exactly one clerk</strong> responsible for it. You always get the latest version, and nobody sees a half-updated page; '
            'but if that clerk falls ill, the file is unavailable until another clerk takes over.'),
    cp_anim(),
    real_world(
        scenario('Exact counters',
                 p('An online exam counts submitted answers per candidate with <code>incr</code>. Because one RegionServer owns the row and serialises increments, '
                   'the count is exact even with retries from many browser tabs (unlike approximate distributed counters).')),
    ),
    example(
        hsh('''
create 'exam_stats', 's'
incr 'exam_stats', 'SQL-2026-10|2401', 's:answers', 1
incr 'exam_stats', 'SQL-2026-10|2401', 's:answers', 1
incr 'exam_stats', 'SQL-2026-10|2401', 's:answers', 1
get_counter 'exam_stats', 'SQL-2026-10|2401', 's:answers'
'''),
        java('''
// Atomic compare-and-set on one row (Java API): submit only if status is still 'started'
boolean ok = table.checkAndMutate(Bytes.toBytes("SQL-2026-10|2401"), Bytes.toBytes("s"))
        .qualifier(Bytes.toBytes("status"))
        .ifEquals(Bytes.toBytes("started"))
        .thenPut(new Put(Bytes.toBytes("SQL-2026-10|2401"))
                 .addColumn(Bytes.toBytes("s"), Bytes.toBytes("status"), Bytes.toBytes("submitted")));
''', 'checkAndMutate (Java client)'),
        title='Example'),
    steps(
        ('Keep data that must change together in one row', 'Row-level atomicity is the only built-in transaction.'),
        ('Use incr / checkAndMutate for races', 'Counters, state transitions, "only once" actions.'),
        ('Plan for brief unavailability', 'Client retries; region replicas for read availability.'),
        title='Steps'),
    crossq(
        ('How is this different from Cassandra?', 'Cassandra lets any replica accept writes and resolves conflicts by timestamp (AP, tunable). HBase routes each row to one server (CP), giving strict consistency but less availability during failures.'),
        ('Are reads from region replicas consistent?', 'No: with <code>REGION_REPLICATION &gt; 1</code>, secondary replicas serve <em>timeline-consistent</em> reads that may be slightly stale; the client must request <code>Consistency.TIMELINE</code>.'),
    ),
]),
])
