from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

RUN_NOTE = note('Every example with an Output box was executed while this page was built, in a mongosh-style shell whose queries, '
                'updates and aggregation pipelines are evaluated by <strong>mingo</strong>, a JavaScript implementation of the MongoDB Query '
                'Language. Output follows mongosh\'s format. Features that need a real server (explain plans, replica sets, sharding, '
                'transactions) are shown without output.', 'How the examples were run')

SECTION = dict(level='beginner', title='NoSQL Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is NoSQL? Why was it needed?', 'What is NoSQL', minutes=7, cards=[
    definition(
        defbox('<strong>NoSQL</strong> ("Not only SQL") is a family of databases that store data in models other than relational tables: '
               '<strong>documents, key-value pairs, wide columns or graphs</strong>. They are designed to <strong>scale horizontally</strong> '
               'across many servers, handle <strong>flexible or changing schemas</strong>, and stay available at very large scale.',
               'They became popular in the late 2000s (Google Bigtable, Amazon Dynamo, then MongoDB, Cassandra, Redis) when web companies '
               'outgrew single relational servers.'),
        tags('NoSQL', 'Horizontal Scaling', 'Flexible Schema', 'Distributed', 'Big Data'),
    ),
    analogy('A relational database is a <strong>government office register</strong> with fixed printed columns: every entry must fit the '
            'columns, and when one register is full you buy a bigger, costlier register. A NoSQL database is a <strong>set of folders in many '
            'cupboards</strong>: each folder can hold whatever papers that person has, and when space runs out you simply add another cupboard.'),
    why_nosql(),
    real_world(
        scenario('C-DAC online exam platform',
                 p('During an all-India entrance exam, 30,000 candidates save answers every few seconds. Each candidate\'s attempt has a '
                   'different number of questions answered, flags and timings. Storing each attempt as one MongoDB document, spread over a '
                   'replica set, handles the write burst and the varying structure without schema migrations on exam day.')),
        scenario('Industry',
                 ul('Product catalogues with thousands of different attributes per category (e-commerce) → document databases.',
                    'Sessions, carts and caches → key-value stores (Redis).',
                    'IoT readings and time series at millions of writes/second → wide-column stores (Cassandra).',
                    'Fraud rings and recommendations → graph databases (Neo4j).')),
    ),
    example(
        RUN_NOTE,
        mql('''
use cdac
// No CREATE TABLE: the collection is created by the first insert,
// and documents in it may have different fields
db.students.insertOne({ _id: 2401, name: 'Anuj', course: 'PG-DBDA', skills: ['sql', 'spark'] })
db.students.insertOne({ _id: 2402, name: 'Vineeta', course: 'PG-DBDA', address: { city: 'Navi Mumbai' } })
db.students.find()
'''),
        title='Example: A Schema-Flexible Collection'),
    steps(
        ('Identify the access patterns', 'Which screens/APIs read and write which data, how often, how much.'),
        ('Check the data shape', 'Nested, varying, hierarchical data suits documents; simple lookups suit key-value; relationships suit graphs.'),
        ('Check scale and availability needs', 'Writes per second, data growth, multi-region, tolerance for stale reads.'),
        ('Pick the model and product', 'e.g. MongoDB for documents, Redis for cache, Cassandra for time series.'),
        ('Prototype with real queries', 'Measure before committing; keep the RDBMS where transactions and joins dominate.'),
        title='Steps to Decide Whether to Use NoSQL'),
    crossq(
        ('Does NoSQL mean "no SQL at all"?', 'No, "Not only SQL". Many NoSQL systems have SQL-like languages (Cassandra CQL, MongoDB SQL interface in Atlas), and the idea is to use the right model for each job alongside relational databases.'),
        ('Is NoSQL always faster than SQL?', 'No. It is faster for the access patterns it is designed for (lookups by key, reading whole documents). Ad-hoc joins and complex multi-table transactions are often better in an RDBMS.'),
        ('Name NoSQL databases you know and their type.', 'MongoDB, Couchbase (document); Redis, DynamoDB (key-value); Cassandra, HBase (wide-column); Neo4j, Amazon Neptune (graph).'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What are the types of NoSQL databases? Give examples and use cases.', 'Types of NoSQL', minutes=8, cards=[
    definition(
        table(['Type', 'Data model', 'Examples', 'Best for'], [
            ['Key-value', 'key → opaque value', 'Redis, DynamoDB, Memcached', 'Caching, sessions, carts, rate limits, OTPs'],
            ['Document', 'JSON/BSON documents with nested fields, queryable by any field', 'MongoDB, Couchbase, Firestore', 'User profiles, catalogues, content, most application data'],
            ['Wide-column', 'Rows with flexible, sparse column families, partitioned by key', 'Cassandra, HBase, ScyllaDB', 'Time series, logs, IoT, huge write volumes'],
            ['Graph', 'Nodes and relationships with properties', 'Neo4j, Neptune, JanusGraph', 'Social networks, fraud detection, recommendations'],
        ]),
        tags('Key-Value', 'Document', 'Wide-Column', 'Graph', 'Redis', 'Cassandra', 'Neo4j'),
    ),
    analogy('Four ways of storing student information: a <strong>locker room</strong> (key-value: locker number → whatever is inside), a '
            '<strong>file per student</strong> (document: everything about one student in one folder), a <strong>giant attendance sheet</strong> '
            'with one row per student and a column per day (wide-column), and a <strong>friendship chart</strong> drawing who studies with whom (graph).'),
    nosql_types(),
    real_world(
        scenario('One application, several stores (polyglot persistence)',
                 ul('MongoDB: student profiles, exam attempts.',
                    'Redis: login sessions and OTPs with automatic expiry.',
                    'Cassandra: face-attendance events from every camera, every second.',
                    'Neo4j: mentor–student–project relationships for recommendations.',
                    'PostgreSQL: fee payments that need strict transactions.')),
    ),
    example(
        mql('''
// Document model: any field, including nested ones, is queryable
db.students.find({ 'address.city': 'Pune' }, { name: 1, 'address.city': 1 })
db.students.find({ skills: 'python' }, { _id: 0, name: 1 })
''', setup=STUDENTS),
        sh('''
# Key-value (Redis): only by key, value is opaque
SET otp:2401 482913 EX 300        # expires after 5 minutes
GET otp:2401

# Wide-column (Cassandra CQL): queries must use the partition key
SELECT * FROM attendance WHERE roll_no = 2401 AND day >= '2026-10-01';

# Graph (Neo4j Cypher)
MATCH (s:Student {name:'Anuj'})-[:STUDIES_WITH*2]-(friend) RETURN friend.name;
''', 'The same idea in other NoSQL stores (shown, not run)'),
        title='Example'),
    steps(
        ('List the main queries', 'By key only? By many fields? By relationships? Huge time-ordered writes?'),
        ('Map queries to a model', 'Key-only → KV; rich queries on records → document; partition + time range → wide-column; traversals → graph.'),
        ('Check consistency needs', 'Strong vs eventual; transactions needed?'),
        ('Choose and test', 'Load realistic data volume and measure latency.'),
        title='Steps to Pick a NoSQL Type'),
    crossq(
        ('Which type is MongoDB?', 'A document database: it stores BSON documents in collections and can query, index and aggregate on any field, including nested ones.'),
        ('Why can\'t you query a key-value store by value?', 'The value is opaque to the store; it only indexes keys. You must design keys for your lookups or use a secondary index feature if the product offers one.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('Explain the CAP theorem. Where does MongoDB fit?', 'CAP Theorem', minutes=9, cards=[
    definition(
        defbox('The <strong>CAP theorem</strong> (Eric Brewer, 2000) says a distributed data system can guarantee at most two of: '
               '<strong>Consistency</strong> (every read sees the latest write), <strong>Availability</strong> (every request to a working node '
               'gets a response) and <strong>Partition tolerance</strong> (the system keeps working despite lost messages between nodes).',
               'Because network partitions cannot be avoided, the real choice is: <strong>during a partition, prefer C or A?</strong> '
               '<strong>PACELC</strong> adds: <em>Else</em> (no partition), trade <strong>Latency</strong> against <strong>Consistency</strong>.'),
        tags('CAP Theorem', 'Consistency', 'Availability', 'Partition Tolerance', 'PACELC', 'CP', 'AP'),
    ),
    analogy('Two branches of a bank share account balances by phone. The phone line goes dead (partition). A customer at the second branch asks '
            'to withdraw money. The branch can <strong>refuse until the line is back</strong> (consistent, not available) or <strong>pay out '
            'based on its last known balance</strong> (available, possibly wrong). It cannot do both safely.'),
    cap_anim(),
    real_world(
        scenario('MongoDB\'s position',
                 p('MongoDB is usually described as <strong>CP</strong>: writes go only to the primary, and if the primary is cut off from the '
                   'majority it steps down; the minority side cannot accept writes. With <code>w: "majority"</code> and '
                   '<code>readConcern: "majority"</code>, acknowledged data is never lost or seen stale on the primary. Reading from secondaries '
                   '(<code>readPreference: "secondary"</code>) trades some consistency for availability and latency, so MongoDB is tunable.')),
        scenario('Other systems',
                 ul('Cassandra, DynamoDB: AP by default, tunable consistency per query (e.g. QUORUM).',
                    'HBase, ZooKeeper, etcd: CP.',
                    'Single-node RDBMS: no partitions to tolerate, so CAP does not really apply.')),
    ),
    example(
        mq('''
// Tune the C/A trade-off per operation in MongoDB
db.attempts.insertOne(
  { roll: 2401, exam: 'SQL', score: 82 },
  { writeConcern: { w: 'majority', wtimeout: 5000 } }   // durable across failover
)
db.attempts.find({ roll: 2401 }).readConcern('majority')      // only majority-committed data
db.attempts.find({ exam: 'SQL' }).readPref('secondaryPreferred') // may be slightly stale, offloads primary
''', 'Consistency settings (need a replica set)'),
        title='Example'),
    steps(
        ('Ask "what happens during a partition?"', 'Is a stale or missing answer worse than no answer?'),
        ('Classify each operation', 'Payments, seat allocation → consistency. Feeds, counters, recommendations → availability.'),
        ('Configure the database', 'MongoDB: write concern, read concern, read preference per operation.'),
        ('Test failure', 'Kill the primary or block network in staging and observe behaviour.'),
        title='Steps to Apply CAP in a Design'),
    crossq(
        ('Why can\'t you pick CA?', 'In a distributed system, partitions will happen. A system that is "CA" simply has no defined behaviour when they do, so it is not really an option for distributed databases.'),
        ('What is eventual consistency?', 'If no new writes occur, all replicas will eventually return the same value. In between, different replicas may answer differently.'),
        ('Is MongoDB strictly CP?', 'With default settings (majority writes, primary reads) it behaves CP. Read preferences and lower write concerns let you move towards availability and lower latency for chosen operations.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What is the difference between ACID and BASE?', 'ACID vs BASE', minutes=7, cards=[
    definition(
        defbox('<strong>ACID</strong>: <strong>A</strong>tomicity (all or nothing), <strong>C</strong>onsistency (constraints always hold), '
               '<strong>I</strong>solation (concurrent transactions do not see each other\'s partial work), <strong>D</strong>urability '
               '(committed data survives crashes).',
               '<strong>BASE</strong>: <strong>B</strong>asically <strong>A</strong>vailable, <strong>S</strong>oft state, <strong>E</strong>ventually '
               'consistent: the design philosophy of many distributed NoSQL stores that favour availability and scale over immediate consistency.'),
        tags('ACID', 'BASE', 'Transactions', 'Eventual Consistency', 'Atomicity'),
    ),
    analogy('ACID is a <strong>bank transfer</strong>: money leaves one account and arrives in the other together, or not at all. BASE is a '
            '<strong>WhatsApp group</strong>: a message reaches everyone eventually, and for a few seconds some members see it while others do not, which is acceptable.'),
    acid_base(),
    real_world(
        scenario('MongoDB gives you both levels',
                 ul('Every single-document write is ACID (atomic, isolated) by design.',
                    'Multi-document ACID transactions exist since 4.0 for when you need them (fee payment + seat update).',
                    'Reading from secondaries or using w:1 relaxes guarantees for speed: closer to BASE.')),
    ),
    example(
        mql('''
// A single-document update is atomic: both changes happen together or not at all
db.students.updateOne(
  { _id: 2401 },
  { $inc: { feesPaid: 45000 }, $push: { receipts: { no: 'R-1001', amount: 45000 } } }
)
db.students.findOne({ _id: 2401 }, { name: 1, feesPaid: 1, receipts: 1 })
''', setup=SMALL),
        title='Example: Single-Document Atomicity'),
    steps(
        ('List operations that must never be partial', 'Payments, seat booking, inventory decrement.'),
        ('Try to keep them in one document', 'Single-document writes are atomic in MongoDB without transactions.'),
        ('Use transactions only when necessary', 'When several documents/collections must change together.'),
        ('Relax where acceptable', 'Counters, analytics, feeds can use eventual consistency.'),
        title='Steps to Choose Guarantees'),
    crossq(
        ('Is the "C" in ACID the same as the "C" in CAP?', 'No. ACID consistency means the database moves from one valid state to another (constraints hold). CAP consistency means every read sees the latest write across replicas (linearizability).'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('SQL vs NoSQL (MongoDB): how do you decide which to use?', 'SQL vs MongoDB', minutes=8, cards=[
    comparison(
        table(['Aspect', 'Relational (MySQL, PostgreSQL)', 'MongoDB'], [
            ['Data model', 'Tables, rows, fixed columns', 'Collections of JSON-like documents'],
            ['Schema', 'Defined upfront; ALTER TABLE to change', 'Flexible; optional validation rules'],
            ['Relationships', 'Normalised tables + JOINs', 'Embedding (preferred) or references + $lookup'],
            ['Scaling', 'Mainly vertical; sharding is hard', 'Horizontal sharding built in'],
            ['Transactions', 'Multi-row ACID everywhere', 'Single-document atomic; multi-document transactions available'],
            ['Query language', 'SQL', 'MQL (JSON filters) + aggregation pipeline'],
            ['Best fit', 'Highly relational data, complex ad-hoc joins, strict integrity', 'Hierarchical/varying data, high write rates, fast iteration'],
        ]),
        table(['SQL term', 'MongoDB term'], [
            ['Database', 'Database'], ['Table', 'Collection'], ['Row', 'Document'], ['Column', 'Field'],
            ['Primary key', '<code>_id</code>'], ['JOIN', 'Embedding / <code>$lookup</code>'], ['GROUP BY', '<code>$group</code> stage'], ['Index', 'Index'],
        ], caption='Terminology mapping'),
        tags('SQL vs NoSQL', 'Collection', 'Document', 'JOIN', 'Embedding'),
    ),
    analogy('A relational database is like a <strong>well-organised spreadsheet workbook</strong> with separate linked sheets; MongoDB is like a '
            '<strong>set of complete student files</strong>, each file containing everything about one student. The spreadsheet is great for '
            'cross-sheet analysis; the files are great when you usually need one whole student at a time.'),
    sql_vs_nosql(),
    real_world(
        scenario('Choosing for an institute',
                 ul('Fees, accounting, payroll: <strong>PostgreSQL/MySQL</strong> (strict integrity, many relationships, reports with joins).',
                    'Learning platform: course content with varying structure, quizzes, user activity: <strong>MongoDB</strong>.',
                    'Both together, connected by ETL into a warehouse for reporting.')),
    ),
    example(
        code('''
-- SQL: three tables and a join to build one profile
SELECT s.roll_no, s.name, k.skill, m.subject, m.marks
FROM students s
LEFT JOIN skills k ON k.roll_no = s.roll_no
LEFT JOIN marks  m ON m.roll_no = s.roll_no
WHERE s.roll_no = 2401;
''', 'SQL (MySQL)', 'fa-database'),
        mql('''
// MongoDB: one document, one read
db.students.findOne({ _id: 2401 }, { name: 1, skills: 1, scores: 1 })
''', setup=STUDENTS),
        title='Example: One Profile, Two Models'),
    steps(
        ('Write down the top 10 queries', 'And the expected data volume and write rate.'),
        ('Check relationships', 'Many-to-many with ad-hoc joins everywhere → relational. Mostly hierarchical "parent with children" → document.'),
        ('Check schema stability', 'Frequently changing or per-record attributes favour documents.'),
        ('Check transaction needs', 'Mostly single-entity updates → MongoDB is fine; heavy cross-entity transactions → RDBMS.'),
        ('Prototype both if unsure', 'Benchmark the critical queries.'),
        title='Steps to Decide'),
    crossq(
        ('Can MongoDB do joins?', 'Yes, with <code>$lookup</code> in the aggregation pipeline, but frequent joins usually signal that the data should be embedded or the model revisited.'),
        ('What is the biggest mistake when moving from SQL to MongoDB?', 'Copying the normalised table design 1:1 into collections and then using $lookup everywhere. Model documents around how the application reads the data.'),
    ),
]),
])
