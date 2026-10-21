from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py, xml, sql

SECTION = dict(level='advanced', title='Clients, Recovery & Tools', questions=[

# ------------------------------------------------------------------ 31
Q('How does a client find which RegionServer holds a row? What is hbase:meta?', 'hbase:meta & Client Lookup', minutes=8, cards=[
    definition(
        defbox('<code>hbase:meta</code> is a system table with one row per region: <code>table,startkey,regionid</code> → server, state, region info. Its own location is '
               'stored in <strong>ZooKeeper</strong>. A client reads ZooKeeper once, then meta, then contacts the RegionServer directly, <strong>caching</strong> region '
               'locations. When a region moves, the old server replies <code>NotServingRegionException</code> and the client refreshes its cache.'),
        tags('hbase:meta', 'ZooKeeper', 'Region location cache', 'NotServingRegionException'),
    ),
    analogy('Finding a book in a big library: the <strong>notice board</strong> (ZooKeeper) says where the <strong>catalogue</strong> is (hbase:meta); the catalogue '
            'says which room has the shelf; next time you remember the room yourself.'),
    meta_lookup_anim(),
    real_world(
        scenario('Why the first request is slower',
                 p('After an application restart, the first requests to each region pay for meta lookups. Warm-up calls or a long-lived shared Connection avoid repeating this.')),
    ),
    example(
        hq('''
scan 'hbase:meta', {FILTER => "PrefixFilter('students,')", COLUMNS => ['info:server', 'info:regioninfo']}
''', 'Looking at hbase:meta (real cluster)'),
        java('''
try (Connection conn = ConnectionFactory.createConnection(conf);
     RegionLocator locator = conn.getRegionLocator(TableName.valueOf("students"))) {
    HRegionLocation loc = locator.getRegionLocation(Bytes.toBytes("2401"));
    System.out.println(loc.getHostname() + " " + loc.getRegion().getRegionNameAsString());
}
''', 'RegionLocator (Java client)'),
        title='Example'),
    steps(
        ('Create one Connection per application', 'It holds the meta cache.'),
        ('Let the client retry', 'Defaults handle region moves and splits transparently.'),
        ('Monitor meta', 'It is critical: keep it healthy and its server lightly loaded.'),
        title='Steps'),
    crossq(
        ('Was there a -ROOT- table?', 'In HBase before 0.96 a -ROOT- table pointed to .META.; it was removed, and ZooKeeper now points directly to hbase:meta.'),
        ('What happens if the meta RegionServer dies?', 'hbase:meta is reassigned first; until then new lookups wait, though cached locations keep working.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What happens when a RegionServer fails? How does HBase recover?', 'Failure Recovery', minutes=9, cards=[
    definition(
        ul('The RegionServer\'s <strong>ZooKeeper session expires</strong> (ephemeral node disappears).',
           'The <strong>HMaster</strong> marks the server dead and runs a recovery procedure.',
           'The dead server\'s <strong>WAL</strong> files are <strong>split</strong> by region (distributed log splitting).',
           'Its regions are <strong>reassigned</strong> to live RegionServers, which <strong>replay</strong> the recovered edits, then open the regions.',
           'During this (seconds to a few minutes) those regions are unavailable: the CP trade-off. <strong>Region replicas</strong> (<code>REGION_REPLICATION</code>) '
           'can serve <em>timeline-consistent</em> reads meanwhile.'),
        tags('Failover', 'WAL splitting', 'Region reassignment', 'MTTR', 'Region replicas', 'Timeline consistency'),
    ),
    analogy('A clerk falls ill: the head office collects the clerk\'s <strong>carbon-copy logbook</strong>, hands each file and the relevant logbook pages to other '
            'clerks, who bring the files up to date before serving the public again.'),
    failover_anim(),
    real_world(
        scenario('Reducing recovery time',
                 p('Lowering the ZooKeeper session timeout from 90 s to 30 s and keeping WALs small (more frequent rolls) cut mean time to recovery for exam-day tables. '
                   'A read-replica setting on the hot results table kept results pages readable during recovery.')),
    ),
    example(
        hq('''
create 'results', 'r', {REGION_REPLICATION => 2}    # one primary + one read replica per region
''', 'Region replicas (real cluster)'),
        java('''
Get get = new Get(Bytes.toBytes("SQL|2401"));
get.setConsistency(Consistency.TIMELINE);          // allow a secondary replica to answer
Result r = table.get(get);
boolean stale = r.isStale();                       // true if served by a replica
''', 'Timeline-consistent read (Java client)'),
        sh('''
$ hbase hbck -details          # HBase 1.x consistency check
$ hbase hbck -j hbase-hbck2.jar assigns <encoded-region>   # HBase 2: fix stuck regions with HBCK2
''', 'Repair tools'),
        title='Example'),
    steps(
        ('Monitor dead servers and regions in transition', 'Master UI.'),
        ('Tune session timeout and WAL size', 'Faster detection, faster replay.'),
        ('Use region replicas for read-critical tables', 'Accept possible staleness.'),
        ('Use HBCK2 for stuck regions', 'Never edit hbase:meta by hand.'),
        title='Steps'),
    crossq(
        ('Is acknowledged data lost when a RegionServer crashes?', 'No (with the WAL on): every acknowledged edit is in the WAL on HDFS and is replayed.'),
        ('What is a region in transition (RIT)?', 'A region being opened, closed, split or moved; long-lasting RIT usually indicates a problem (HDFS issues, corrupt files) that HBCK2 can help fix.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('How do applications connect to HBase? Explain the Java API, Thrift (HappyBase) and REST.', 'HBase Clients', minutes=9, cards=[
    definition(
        table(['Client', 'Use', 'Notes'], [
            ['Java API', 'Production applications, Spark/MapReduce', '<code>Connection</code> (heavy, shared) → <code>Table</code> (light): Put, Get, Scan, Delete, BufferedMutator'],
            ['Thrift gateway', 'Python, C++, PHP…', 'Python library <strong>HappyBase</strong> talks to the Thrift server (port 9090)'],
            ['REST gateway (Stargate)', 'Any language over HTTP', 'JSON/XML/protobuf; good for simple integrations'],
            ['HBase shell', 'Administration, testing', 'JRuby on the Java API'],
            ['Phoenix JDBC', 'SQL access', 'Standard JDBC driver'],
        ]),
        tags('Java API', 'Connection', 'Table', 'HappyBase', 'Thrift', 'REST'),
    ),
    analogy('The Java API is <strong>walking into the office</strong>; Thrift and REST are <strong>calling the help desk</strong>, which goes to the office for you.'),
    clients_anim(),
    real_world(
        scenario('A Python analytics team',
                 p('Data scientists use HappyBase through a Thrift server to fetch a student\'s event history into pandas; the production portal uses the Java API '
                   'with a shared Connection inside a Spring Boot service.')),
    ),
    example(
        java('''
Configuration conf = HBaseConfiguration.create();          // reads hbase-site.xml
try (Connection conn = ConnectionFactory.createConnection(conf);
     Table table = conn.getTable(TableName.valueOf("cdac:students"))) {

    Put put = new Put(Bytes.toBytes("2401"));
    put.addColumn(Bytes.toBytes("info"), Bytes.toBytes("name"), Bytes.toBytes("Anuj"));
    table.put(put);

    Result r = table.get(new Get(Bytes.toBytes("2401")));
    System.out.println(Bytes.toString(r.getValue(Bytes.toBytes("info"), Bytes.toBytes("name"))));

    Scan scan = new Scan().withStartRow(Bytes.toBytes("24")).withStopRow(Bytes.toBytes("25"));
    try (ResultScanner rs = table.getScanner(scan)) {
        for (Result row : rs) System.out.println(Bytes.toString(row.getRow()));
    }
}
''', 'Java client API'),
        py('''
import happybase                                    # pip install happybase; needs `hbase thrift start`

conn = happybase.Connection('hbase-thrift.cdac.local', port=9090)
table = conn.table('cdac:students')
table.put(b'2401', {b'info:name': b'Anuj', b'info:city': b'Pune'})
print(table.row(b'2401'))                           # {b'info:city': b'Pune', b'info:name': b'Anuj'}
for key, data in table.scan(row_prefix=b'24', columns=[b'info:name'], limit=10):
    print(key, data)
with table.batch(batch_size=1000) as b:             # buffered writes
    b.put(b'2402', {b'info:name': b'Aarshvi'})
''', 'Python with HappyBase'),
        sh('''
$ curl -H "Accept: application/json" http://hbase-rest:8080/cdac:students/2401
''', 'REST gateway'),
        title='Example'),
    steps(
        ('Share one Connection', 'Thread-safe and expensive; Tables are cheap.'),
        ('Close Tables and scanners', 'try-with-resources / context managers.'),
        ('Batch writes', 'BufferedMutator, happybase batch.'),
        ('Run Thrift/REST servers close to the cluster', 'Scale them horizontally for many clients.'),
        title='Steps'),
    crossq(
        ('Why are all values bytes in the API?', 'HBase stores bytes only; <code>Bytes.toBytes</code>/<code>Bytes.toString</code> (or Phoenix types) handle encoding.'),
        ('What is an HBase coprocessor?', 'Server-side code loaded into RegionServers: observers (triggers on get/put) or endpoints (custom RPCs, e.g. aggregations). Phoenix is largely built on coprocessors.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do you bulk load large data into HBase? Why is it faster than puts?', 'Bulk Loading', minutes=8, cards=[
    definition(
        defbox('<strong>Bulk loading</strong> generates HFiles directly with MapReduce or Spark, partitioned and sorted according to the table\'s region boundaries, and then '
               'hands them to the RegionServers (<code>completebulkload</code>). The data never passes through the <strong>WAL</strong> or <strong>MemStore</strong>, so it '
               'causes no flushes or compaction storms and is far faster than millions of individual puts.',
               'Tools: <code>ImportTsv</code> (CSV/TSV, with <code>-Dimporttsv.bulk.output</code>), <code>HFileOutputFormat2</code> in custom jobs, the hbase-spark connector\'s '
               '<code>hbaseBulkLoad</code>, and <code>BulkLoadHFiles</code>. Pre-split the table first so the job writes into many regions.'),
        tags('Bulk load', 'ImportTsv', 'HFileOutputFormat2', 'completebulkload', 'No WAL'),
    ),
    analogy('Instead of handing a clerk 1 crore forms one by one, you deliver <strong>ready-sorted, bound volumes</strong> that go straight onto the shelves.'),
    bulkload_anim(),
    real_world(
        scenario('Five years of attendance',
                 p('Historical attendance (~3 billion rows) was loaded with ImportTsv into 64 pre-split regions in about 40 minutes, compared with an estimated 2 days '
                   'with puts; the live cluster stayed responsive throughout.')),
    ),
    example(
        sh('''
# 1. generate HFiles from a CSV on HDFS (columns mapped to row key and family:qualifier)
$ hbase org.apache.hadoop.hbase.mapreduce.ImportTsv \\
    -Dimporttsv.separator=',' \\
    -Dimporttsv.columns=HBASE_ROW_KEY,a:status,a:centre \\
    -Dimporttsv.bulk.output=/tmp/att_hfiles \\
    attendance /data/attendance/2021-2025.csv

# 2. move the HFiles into the table's regions
$ hbase completebulkload /tmp/att_hfiles attendance
''', 'ImportTsv + completebulkload'),
        title='Example'),
    steps(
        ('Create and pre-split the table', 'Matching the key distribution of the data.'),
        ('Generate HFiles', 'ImportTsv, Spark or MapReduce with HFileOutputFormat2.'),
        ('Load them', 'completebulkload / BulkLoadHFiles.'),
        ('Handle replication', 'Enable bulk-load replication if the table is replicated to another cluster.'),
        title='Steps'),
    crossq(
        ('Why must HFiles be sorted and partitioned by region?', 'Each HFile is adopted by one region and must contain only keys in its range, in sorted order.'),
        ('What happens if a region split during the load?', 'The loader detects it and splits the affected HFile into two before loading.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('What is Apache Phoenix? How does it add SQL to HBase?', 'Apache Phoenix', minutes=9, cards=[
    definition(
        defbox('<strong>Apache Phoenix</strong> is a SQL layer and JDBC driver for HBase. It compiles SQL into HBase scans, pushes filters and aggregations into '
               'RegionServers with coprocessors, and stores its schema in system tables. A table\'s <code>PRIMARY KEY</code> columns are encoded into the HBase '
               '<strong>row key</strong>; other columns become cells.',
               'Features: typed columns (correct numeric ordering), <code>UPSERT</code>, secondary indexes (global, local, covered, functional), salting '
               '(<code>SALT_BUCKETS</code>), views, joins and sub-queries, ACID transactions (with Omid/Tephra), and integration with Spark and Hive.'),
        tags('Phoenix', 'SQL on HBase', 'JDBC', 'UPSERT', 'Secondary index', 'SALT_BUCKETS'),
    ),
    analogy('Phoenix is an <strong>interpreter</strong> who lets you ask HBase questions in SQL and translates them into HBase\'s own language of row keys and scans.'),
    phoenix_anim(),
    real_world(
        scenario('SQL for the coordinators',
                 p('Coordinators use a BI tool via the Phoenix JDBC driver to query attendance by centre and date; a covered global index on '
                   '<code>(centre, day)</code> makes those queries index lookups instead of full scans.')),
    ),
    example(
        sql('''
CREATE TABLE attendance (
    roll_no   INTEGER NOT NULL,
    day       DATE    NOT NULL,
    centre    VARCHAR,
    status    CHAR(1)
    CONSTRAINT pk PRIMARY KEY (roll_no, day)     -- becomes the HBase row key
) SALT_BUCKETS = 8;

UPSERT INTO attendance VALUES (2401, TO_DATE('2026-10-14'), 'KHR', 'P');

CREATE INDEX att_by_centre ON attendance (centre, day) INCLUDE (status);   -- covered global index

SELECT centre, COUNT(*) AS present
FROM attendance
WHERE day = TO_DATE('2026-10-14') AND status = 'P'
GROUP BY centre;
''', 'Apache Phoenix SQL (sqlline.py)'),
        title='Example'),
    steps(
        ('Install the Phoenix server jar on RegionServers', 'Matching the HBase version.'),
        ('Connect with sqlline.py or JDBC', '<code>jdbc:phoenix:zk1,zk2,zk3:2181</code>'),
        ('Design the PRIMARY KEY like a row key', 'Leading columns = most common filters.'),
        ('Add indexes for other access paths', 'Covered indexes avoid lookups back to the data table.'),
        title='Steps'),
    crossq(
        ('Can Phoenix read tables created in the HBase shell?', 'Yes, by creating a Phoenix VIEW (or TABLE) mapped to the existing HBase table and its column families.'),
        ('Is Phoenix a data warehouse?', 'No: it is optimised for low-latency OLTP-style queries on HBase; large analytical scans are better in Spark/Hive on columnar files.'),
    ),
]),
])
