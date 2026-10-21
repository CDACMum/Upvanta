from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh, conf

RUN_NOTE = note('Every CQL example with an Output box was executed while this page was built. It ran on a CQL engine that follows '
                'Apache Cassandra 5.0\'s rules: Murmur3 tokens, clustering order, the WHERE-clause restrictions and their exact error '
                'messages, timestamps, TTL, tombstones and lightweight transactions. Output is shown in cqlsh format. '
                'Multi-node behaviour (replication, consistency, repair) and nodetool commands are shown without output.',
                'How the examples were run')

SECTION = dict(level='beginner', title='Cassandra Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Apache Cassandra? What are its key features and when should you use it?', 'What is Cassandra', minutes=8, cards=[
    definition(
        defbox('<strong>Apache Cassandra</strong> is an open-source, distributed <strong>wide-column NoSQL database</strong> designed to store very large '
               'amounts of data across many commodity servers with <strong>no single point of failure</strong>. It was built at Facebook (2008) for inbox '
               'search, combining Amazon <strong>Dynamo</strong>\'s distribution model (consistent hashing, replication, gossip) with Google '
               '<strong>Bigtable</strong>\'s storage model (memtables, SSTables, column families).',
               'Key features: <strong>masterless</strong> peer-to-peer architecture, <strong>linear horizontal scaling</strong>, built-in '
               '<strong>multi-data-centre replication</strong>, <strong>tunable consistency</strong> per query, very fast writes, and a SQL-like '
               'query language (CQL). The current major version is <strong>5.0</strong> (Storage-Attached Indexes, vector search, Unified Compaction, '
               'trie-based memtables and SSTables, Java 17).'),
        tags('Distributed', 'Wide-column', 'Masterless', 'Linear scalability', 'Multi-DC', 'Tunable consistency', 'CQL'),
    ),
    analogy('A chain of <strong>identical bank branches with no head office</strong>. Every branch can serve any customer; each account is kept at '
            'three branches, so one branch closing never stops service. To handle more customers you simply open more branches.'),
    masterless_anim(),
    comparison(
        table(['Use Cassandra when…', 'Avoid Cassandra when…'], [
            ['Writes are heavy and continuous (events, IoT, logs, messages)', 'You need joins, ad-hoc queries or complex reporting'],
            ['You need 24×7 availability, even across data centres', 'Data is small enough for one PostgreSQL/MySQL server'],
            ['Data grows to terabytes or petabytes', 'You need multi-row ACID transactions (e.g. ledgers)'],
            ['Queries are known in advance and look up by key', 'Query patterns change often or are not known yet'],
        ]),
        title='When to Use It'),
    real_world(
        scenario('Who uses it',
                 ul('<strong>Apple</strong> runs one of the largest deployments (hundreds of thousands of nodes) for iCloud and other services.',
                    '<strong>Netflix</strong> stores viewing history and personalisation data across regions.',
                    '<strong>Uber, Instagram, Discord (earlier), Spotify</strong>: messaging, feeds, trip and user data.',
                    'At C-DAC scale: an online exam platform can log every proctoring event of thousands of simultaneous candidates in Cassandra without a write bottleneck.')),
    ),
    example(
        RUN_NOTE,
        cql('''
CREATE TABLE students (
  roll_no int PRIMARY KEY,
  name    text,
  course  text,
  city    text
);

INSERT INTO students (roll_no, name, course, city) VALUES (2401, 'Anuj', 'PG-DBDA', 'Pune');
INSERT INTO students (roll_no, name, course, city) VALUES (2402, 'Aarshvi', 'PG-DBDA', 'Mumbai');
INSERT INTO students (roll_no, name, course, city) VALUES (2403, 'Vineeta', 'PG-DAC', 'Navi Mumbai');

SELECT * FROM students;
SELECT name, course FROM students WHERE roll_no = 2402;
'''),
        p('Notice that rows are not returned in roll-number order. A full-table read returns partitions in <strong>token order</strong> (the hash of the '
          'partition key), because that is how data is spread around the cluster.', top=True),
        title='Example: Your First Cassandra Table'),
    steps(
        ('Start Cassandra', 'Docker: <code>docker run -d --name cass -p 9042:9042 cassandra:5.0</code>, or install the tarball and run <code>bin/cassandra</code>.'),
        ('Open cqlsh', '<code>docker exec -it cass cqlsh</code> (or <code>bin/cqlsh localhost 9042</code>).'),
        ('Create a keyspace', "<code>CREATE KEYSPACE cdac WITH replication = {'class': 'NetworkTopologyStrategy', 'datacenter1': 1};</code> then <code>USE cdac;</code>"),
        ('Create a table and insert', 'Design the primary key around the query, then INSERT rows.'),
        ('Query by key', '<code>SELECT … WHERE roll_no = …;</code>'),
        title='Steps to Try It'),
    crossq(
        ('Is Cassandra a column-oriented database like Redshift?', 'No. "Wide-column" means rows identified by a key, each with many (possibly sparse) '
         'columns grouped into partitions. Storage is row-oriented within a partition. Columnar warehouses (Redshift, BigQuery) store each column '
         'separately for analytics scans.'),
        ('Why is Cassandra so good at writes?', 'A write is an append to the commit log plus an insert into an in-memory memtable: no disk seek, '
         'no read-before-write and no locking. Files on disk (SSTables) are immutable and written sequentially.'),
        ('Who maintains Cassandra?', 'The Apache Software Foundation, with major contributions from Apple, DataStax, Netflix and others. DataStax '
         'Enterprise and Astra DB are commercial distributions; ScyllaDB is a compatible C++ re-implementation.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain the architecture of Cassandra: nodes, ring, data centres, racks, gossip and snitch.', 'Cassandra Architecture', minutes=9, cards=[
    definition(
        table(['Component', 'What it is'], [
            ['Node', 'One Cassandra process (one server). Stores part of the data and can serve any request.'],
            ['Ring', 'The logical circle of token ranges. Every node owns some ranges of the hash space.'],
            ['Data centre (DC)', 'A group of related nodes, often one physical location or one workload (live, analytics). Replication is set per DC.'],
            ['Rack', 'A failure domain inside a DC (a physical rack or cloud availability zone). Replicas are spread across racks.'],
            ['Cluster', 'All nodes and DCs that share one schema and cluster name.'],
            ['Coordinator', 'The node a client request arrives at. It forwards the request to the replicas and collects the answers.'],
            ['Gossip', 'Peer-to-peer protocol by which nodes exchange state (up/down, load, schema version) every second.'],
            ['Snitch', 'Tells Cassandra each node\'s DC and rack (e.g. GossipingPropertyFileSnitch, Ec2Snitch).'],
            ['Partitioner', 'Hashes the partition key to a token (Murmur3Partitioner by default).'],
        ]),
        tags('Node', 'Ring', 'Data Center', 'Rack', 'Coordinator', 'Gossip', 'Snitch', 'Partitioner'),
    ),
    analogy('A national exam board: <strong>regional offices</strong> (data centres), each with several <strong>buildings</strong> (racks) and '
            '<strong>clerks</strong> (nodes). Any clerk can take your form (coordinator) and knows which clerks keep your file. Clerks chat every '
            'minute about who is on leave (gossip), and the staff directory (snitch) says who sits in which building.'),
    topology_anim(),
    real_world(
        scenario('Two data centres for two workloads',
                 p('The live exam system runs in <code>dc_mumbai</code> with RF 3 and LOCAL_QUORUM. A separate <code>dc_pune</code> with RF 2 receives the '
                   'same data through replication and is used only by Spark analytics jobs, so heavy reports never slow down candidates taking exams.')),
    ),
    example(
        sh('''
$ nodetool status
Datacenter: dc_mumbai
=====================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address      Load       Tokens  Owns (effective)  Host ID   Rack
UN  10.0.1.11    212.4 GiB  16      50.0%             3f2a…     r1
UN  10.0.1.12    208.9 GiB  16      50.0%             9c41…     r1
UN  10.0.2.11    215.0 GiB  16      50.0%             17be…     r2
UN  10.0.2.12    210.7 GiB  16      50.0%             a0d3…     r2
''', 'nodetool status (illustrative output from a 4-node DC, RF 2)'),
        conf('''
# cassandra.yaml (per node)
cluster_name: 'cdac_prod'
num_tokens: 16
endpoint_snitch: GossipingPropertyFileSnitch
seed_provider:
  - class_name: org.apache.cassandra.locator.SimpleSeedProvider
    parameters:
      - seeds: "10.0.1.11,10.0.2.11"

# cassandra-rackdc.properties (per node)
dc=dc_mumbai
rack=r1
''', 'Node configuration'),
        title='Example'),
    steps(
        ('Plan DCs and racks', 'One DC per region or workload; one rack per availability zone.'),
        ('Configure each node', 'Same <code>cluster_name</code>, seeds, snitch; set dc/rack in <code>cassandra-rackdc.properties</code>.'),
        ('Start seed nodes first', 'Then the others; they join via gossip and take token ranges.'),
        ('Verify', '<code>nodetool status</code> shows every node <code>UN</code> (Up, Normal).'),
        ('Create keyspaces with NetworkTopologyStrategy', 'Give a replica count for each DC.'),
        title='Steps to Build a Cluster'),
    crossq(
        ('What does "UN" mean in nodetool status?', 'Up and Normal. Other states: DN (down), UJ (joining/bootstrapping), UL (leaving), UM (moving).'),
        ('What is the role of a seed node?', 'A contact point for new nodes to learn the cluster topology via gossip. Seeds are not masters; '
         'use 2–3 per DC, and do not make every node a seed.'),
        ('Can a client talk to any node?', 'Yes. Drivers are token-aware: they compute the token themselves and send the request directly to a '
         'replica, saving one network hop.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('How is Cassandra different from a relational database?', 'Cassandra vs RDBMS', minutes=8, cards=[
    definition(
        table(['Aspect', 'RDBMS (MySQL, PostgreSQL)', 'Cassandra'], [
            ['Architecture', 'Single primary (plus replicas)', 'Masterless ring, every node equal'],
            ['Scaling', 'Mostly vertical; sharding is manual', 'Horizontal, add nodes'],
            ['Design approach', 'Model the data (normalise), query anything', 'Model the queries, one table per query'],
            ['Joins / sub-queries', 'Yes', 'No'],
            ['Transactions', 'Multi-row ACID', 'Atomic per partition; lightweight transactions (Paxos) for compare-and-set'],
            ['INSERT on existing key', 'Duplicate-key error', 'Silent overwrite (upsert)'],
            ['Consistency', 'Strong', 'Tunable per query (eventual … strong)'],
            ['Schema', 'Fixed, enforced', 'Table schema enforced, but sparse: absent columns use no space'],
            ['Writes', 'B-tree update in place', 'Append-only (commit log + memtable + SSTables)'],
        ]),
        tags('Normalisation vs denormalisation', 'Upsert', 'No joins', 'Horizontal scaling', 'Query-first modelling'),
    ),
    analogy('An RDBMS is a <strong>library with a card catalogue</strong>: books are stored once and you can find them by author, title or subject. '
            'Cassandra is a set of <strong>ready-made photocopy folders</strong>, one per question people ask. Finding an answer is instant, but '
            'every new question needs a new folder, and each new page is copied into every folder that needs it.'),
    rdbms_vs_cass(),
    real_world(
        scenario('Keeping both',
                 p('C-DAC\'s admission and fee data (needs transactions, joins and reports) stays in PostgreSQL. The exam-attempt event stream (millions '
                   'of writes per exam day, read by attempt ID) goes to Cassandra. Using the right store for each workload is a common architecture.')),
    ),
    example(
        cql('''
CREATE TABLE marks_by_student (
  roll_no int, module text, marks int,
  PRIMARY KEY (roll_no, module)
);

INSERT INTO marks_by_student (roll_no, module, marks) VALUES (2401, 'SQL', 78);
-- same primary key again: no error, the row is overwritten
INSERT INTO marks_by_student (roll_no, module, marks) VALUES (2401, 'SQL', 85);
SELECT * FROM marks_by_student;

-- filtering on a non-key column is refused
SELECT * FROM marks_by_student WHERE marks > 80;
''', expect_error=True),
        title='Example: Upsert, and No Ad-hoc Filtering'),
    steps(
        ('List the queries first', 'Which screen needs which data, given which input?'),
        ('Pick partition keys from the WHERE clause', 'The value the application always has (roll number, user ID, sensor + day).'),
        ('Duplicate data instead of joining', 'Write the same fact to every table that needs it.'),
        ('Keep relational data relational', 'Billing, accounting and ad-hoc reporting are better in an RDBMS or warehouse.'),
        title='Steps to Move a Workload from RDBMS to Cassandra'),
    crossq(
        ('If INSERT overwrites, how do you insert only if absent?', '<code>INSERT … IF NOT EXISTS</code>: a lightweight transaction (Paxos). It is '
         'slower, so use it only when duplicates must be prevented, e.g. unique usernames.'),
        ('Does Cassandra enforce a schema?', 'Yes: tables, column names and types are defined and enforced. What is flexible is sparsity: a row stores '
         'only the columns that were written, and columns can be added with ALTER TABLE without rewriting data.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('Explain the CAP theorem. Where does Cassandra fit, and what does "tunable consistency" mean?', 'CAP & Tunable Consistency', minutes=9, cards=[
    definition(
        defbox('<strong>CAP theorem</strong>: when a <strong>network partition</strong> (P) happens, a distributed system must choose between '
               '<strong>Consistency</strong> (every read sees the latest write or gets an error) and <strong>Availability</strong> (every request gets '
               'a non-error response). Partitions cannot be ruled out in real networks, so the real choice is C or A while the network is split.',
               'Cassandra is usually described as <strong>AP</strong>: it prefers to stay available and accept writes, and replicas converge later '
               '(<strong>eventual consistency</strong>). But consistency is <strong>tunable per request</strong> through the consistency level (ONE, '
               'QUORUM, ALL…). Choosing QUORUM for both reads and writes gives strong consistency for that data, at the cost of failing requests when a '
               'majority of replicas is unreachable.'),
        tags('CAP theorem', 'AP system', 'Eventual consistency', 'Tunable consistency', 'Consistency level', 'R + W > RF'),
    ),
    analogy('Three notice boards in three buildings hold the exam schedule. If the corridor between them is blocked, you can either '
            '<strong>keep updating the boards you can reach</strong> (available, but one board is briefly out of date) or <strong>refuse changes until '
            'all boards can be updated</strong> (consistent, but unavailable). Cassandra lets each notice decide how many boards must agree.'),
    cap_anim(),
    real_world(
        scenario('Different levels for different data',
                 ul('Proctoring events: write at <code>ONE</code>, maximum availability, a lost event is tolerable.',
                    'Exam results: write and read at <code>LOCAL_QUORUM</code>, so a published result is never read stale.',
                    'Unique registration IDs: lightweight transaction with <code>SERIAL</code> consistency.')),
    ),
    example(
        cql('''
CONSISTENCY;
CONSISTENCY LOCAL_QUORUM;
'''),
        cq('''
-- In application code the level is set per statement, e.g. Python driver:
--   SimpleStatement("SELECT ...", consistency_level=ConsistencyLevel.LOCAL_QUORUM)
-- With RF = 3 in the local DC:
--   LOCAL_QUORUM write (2 replicas) + LOCAL_QUORUM read (2 replicas) = 4 > 3  -> strong consistency
--   ONE write + ONE read = 2, not > 3                                        -> may read stale data
''', 'Consistency per request'),
        title='Example'),
    steps(
        ('Find the RF of the keyspace', 'e.g. 3 replicas per DC.'),
        ('Decide what stale data costs', 'Metrics and logs: low. Balances and results: high.'),
        ('Pick levels so that W + R > RF where it matters', 'Typically LOCAL_QUORUM for both.'),
        ('Use ONE/LOCAL_ONE for availability-first data', 'High-volume telemetry.'),
        title='Steps to Choose Consistency'),
    crossq(
        ('Is Cassandra CP or AP?', 'By default (CL ONE) it behaves as AP. With QUORUM/ALL it behaves more like CP for those requests: they fail rather '
         'than return stale data when too many replicas are unreachable. The trade-off is chosen per query, not for the whole system.'),
        ('What is PACELC?', 'An extension of CAP: if Partitioned, choose Availability or Consistency; Else (normal operation), choose Latency or '
         'Consistency. Cassandra is PA/EL by default: favours availability and low latency.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What is CQL and cqlsh? Which data types does Cassandra support?', 'CQL, cqlsh & Data Types', minutes=8, cards=[
    definition(
        defbox('<strong>CQL</strong> (Cassandra Query Language) is Cassandra\'s SQL-like language for defining keyspaces and tables and for reading and '
               'writing data. <strong>cqlsh</strong> is the command-line shell (Python) that sends CQL to a node over the native protocol (port 9042); '
               'applications use drivers (Java, Python, Go, Node.js, C#).'),
        table(['Category', 'Types'], [
            ['Numeric', '<code>int</code>, <code>bigint</code>, <code>smallint</code>, <code>tinyint</code>, <code>varint</code>, <code>float</code>, <code>double</code>, <code>decimal</code>'],
            ['Text', '<code>text</code> (= <code>varchar</code>, UTF-8), <code>ascii</code>'],
            ['Date/time', '<code>timestamp</code> (ms since epoch), <code>date</code>, <code>time</code>, <code>duration</code>'],
            ['Identifiers', '<code>uuid</code> (random, v4), <code>timeuuid</code> (time-based, v1, sortable)'],
            ['Other', '<code>boolean</code>, <code>blob</code>, <code>inet</code>, <code>counter</code>'],
            ['Collections', '<code>set&lt;T&gt;</code>, <code>list&lt;T&gt;</code>, <code>map&lt;K,V&gt;</code>, <code>tuple</code>'],
            ['User-defined', '<code>CREATE TYPE</code> (UDT), usually <code>frozen&lt;…&gt;</code>'],
            ['Vector (5.0)', '<code>vector&lt;float, n&gt;</code> for embeddings and similarity search'],
        ]),
        tags('CQL', 'cqlsh', 'Native protocol 9042', 'timeuuid', 'Collections', 'UDT', 'vector'),
    ),
    analogy('CQL is like <strong>speaking a familiar language with a strict accent rule</strong>: the words are SQL, but you may only ask questions the '
            'way the data is filed. Asking "find everyone with marks above 80" is like asking a filing clerk to open every drawer in every building.'),
    cql_types_anim(),
    real_world(
        scenario('Choosing types for an attendance table',
                 ul('<code>timeuuid</code> for event IDs: unique and naturally time-ordered.',
                    '<code>timestamp</code> for clock times, stored in UTC; cqlsh displays them with <code>+0000</code>.',
                    '<code>date</code> for the day bucket in a partition key.',
                    '<code>decimal</code> for fees (exact), not <code>double</code>.')),
    ),
    example(
        cql('''
CREATE TABLE attendance (
  centre     text,
  day        date,
  event_id   timeuuid,
  roll_no    int,
  checked_in timestamp,
  on_time    boolean,
  fee_due    decimal,
  PRIMARY KEY ((centre, day), event_id)
);

INSERT INTO attendance (centre, day, event_id, roll_no, checked_in, on_time, fee_due)
VALUES ('Kharghar', '2026-10-14', now(), 2401, '2026-10-14 09:02:00+0530', true, 0.00);

SELECT roll_no, checked_in, on_time, fee_due, toTimestamp(event_id) AS event_time
FROM attendance WHERE centre = 'Kharghar' AND day = '2026-10-14';

-- type checking is strict
INSERT INTO attendance (centre, day, event_id, roll_no) VALUES ('Kharghar', '2026-10-14', now(), '2401');
''', expect_error=True),
        p('Timestamps are stored in UTC: 09:02 IST is shown as 03:32 UTC. <code>now()</code> generates a new timeuuid and '
          '<code>toTimestamp()</code> extracts the time inside it.', top=True),
        title='Example: Common Types'),
    steps(
        ('Connect', '<code>cqlsh &lt;host&gt; 9042 -u &lt;user&gt; -p &lt;password&gt;</code>'),
        ('Explore', '<code>DESCRIBE KEYSPACES;</code> <code>DESCRIBE TABLE cdac.attendance;</code>'),
        ('Run scripts', '<code>cqlsh -f schema.cql</code> or <code>SOURCE \'schema.cql\';</code>'),
        ('Load / unload CSV', '<code>COPY attendance TO \'att.csv\' WITH HEADER = true;</code> (for small data; use DSBulk for large loads).'),
        ('Inspect a query', '<code>TRACING ON;</code> then run the query to see which nodes and SSTables it touched.'),
        title='Useful cqlsh Commands'),
    crossq(
        ('uuid vs timeuuid?', '<code>uuid()</code> generates a random version-4 UUID with no ordering. <code>now()</code> generates a version-1 timeuuid '
         'containing a timestamp; as a clustering column it sorts by time, and <code>toTimestamp()</code> extracts that time.'),
        ('text vs varchar?', 'Identical: <code>varchar</code> is an alias of <code>text</code> (UTF-8).'),
        ('Can you change a column\'s type later?', 'Practically no; only a few compatible changes were ever allowed and Cassandra 4+ forbids most. Add '
         'a new column and migrate data instead.'),
    ),
]),
])
