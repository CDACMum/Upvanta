from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

SECTION = dict(level='advanced', title='Replication, Sharding & Transactions', questions=[

# ------------------------------------------------------------------ 33
Q('What is a replica set? How does failover work?', 'Replica Sets', minutes=10, cards=[
    definition(
        defbox('A <strong>replica set</strong> is a group of <code>mongod</code> processes that hold the same data: one <strong>primary</strong> '
               '(receives all writes) and one or more <strong>secondaries</strong> (replicate the primary\'s <strong>oplog</strong> and apply it). '
               'If the primary becomes unavailable, the members hold an <strong>election</strong> and a secondary that can reach a majority becomes primary.',
               'Typical size: 3 members (tolerates 1 failure) or 5 (tolerates 2). An <strong>arbiter</strong> votes but holds no data (avoid in '
               'production where possible). Special members: hidden, delayed (protection against bad deletes), priority 0.'),
        tags('Replica Set', 'Primary', 'Secondary', 'Oplog', 'Election', 'Failover', 'Arbiter'),
    ),
    analogy('A <strong>head teacher and two deputies</strong>. Only the head signs orders (writes); the deputies copy every order into their own '
            'register (oplog). If the head falls ill, the staff vote, and the deputy with the most up-to-date register who gets a majority of votes '
            'becomes the new head.'),
    replica_anim(),
    real_world(
        scenario('Exam day without downtime',
                 p('The exam platform runs a 3-member replica set across three availability zones. When one zone had a network failure mid-exam, '
                   'the primary in that zone stepped down, a secondary was elected in ~8 seconds, and drivers with retryable writes resubmitted '
                   'pending answer saves. Candidates saw a brief "saving…" spinner, not an error.')),
    ),
    example(
        mq('''
// initiate a 3-member replica set (each mongod started with --replSet rs0)
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: 'mongo1:27017', priority: 2 },
    { _id: 1, host: 'mongo2:27017' },
    { _id: 2, host: 'mongo3:27017' }
  ]
})
rs.status()          // member states: PRIMARY / SECONDARY, optime, health
rs.conf()            // configuration
rs.stepDown(60)      // planned failover (e.g. before maintenance)
db.getReplicationInfo() // oplog size and time window
''', 'Replica set administration (real server)'),
        sh('''
mongod --replSet rs0 --port 27017 --dbpath /data/rs0 --bind_ip_all
# Application connection string lists the members and the set name
mongodb://mongo1:27017,mongo2:27017,mongo3:27017/cdac?replicaSet=rs0&retryWrites=true&w=majority
''', 'Starting members and connecting'),
        title='Example'),
    steps(
        ('Start each mongod with the same replSet name', '<code>--replSet rs0</code> (or in the config file).'),
        ('Initiate', '<code>rs.initiate({...})</code> on one member with all hosts.'),
        ('Check', '<code>rs.status()</code> shows one PRIMARY and SECONDARYs.'),
        ('Connect applications with the set name', 'The driver discovers the primary and follows failovers.'),
        ('Test failover', 'Stop the primary in staging and watch the election.'),
        title='Steps to Create a Replica Set'),
    crossq(
        ('Why an odd number of voting members?', 'Elections need a strict majority. With 4 members a 2–2 network split leaves no majority, so no primary can be elected; 3 or 5 avoid ties.'),
        ('What is the oplog?', 'A capped collection (<code>local.oplog.rs</code>) recording every write as an idempotent operation. Secondaries tail it; its size determines how long a secondary can be down and still catch up.'),
        ('What is a rollback?', 'If a primary accepted writes that were not replicated to a majority before it failed, those writes are rolled back when it rejoins. <code>w: "majority"</code> prevents acknowledged writes from being rolled back.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('What are write concern, read concern and read preference?', 'Write/Read Concern & Read Preference', minutes=9, cards=[
    definition(
        table(['Setting', 'Controls', 'Common values'], [
            ['Write concern (<code>w</code>, <code>j</code>, <code>wtimeout</code>)', 'How many members must acknowledge a write', '<code>w: 1</code>, <code>w: \'majority\'</code> (default since 5.0), <code>j: true</code>'],
            ['Read concern', 'Which data a read may see', '<code>local</code> (default), <code>majority</code> (only majority-committed), <code>linearizable</code>, <code>snapshot</code> (transactions)'],
            ['Read preference', 'Which members serve reads', '<code>primary</code> (default), <code>primaryPreferred</code>, <code>secondary</code>, <code>secondaryPreferred</code>, <code>nearest</code>'],
        ]),
        tags('Write Concern', 'Read Concern', 'Read Preference', 'w: majority', 'Consistency', 'Durability'),
    ),
    analogy('Write concern is <strong>how many people must sign a register</strong> before a decision counts. Read concern is <strong>whether you '
            'trust a rumour or only officially minuted decisions</strong>. Read preference is <strong>whom you ask</strong>: the principal\'s office or the nearest staff member.'),
    write_concern_anim(),
    real_world(
        scenario('Mixing settings per operation',
                 ul('Exam answer saves: <code>w: \'majority\'</code> (must survive failover).',
                    'Analytics dashboards: <code>readPreference: secondaryPreferred</code> (offload the primary, a few seconds stale is fine).',
                    'Login audit events: <code>w: 1</code> (high volume, losing one on failover is acceptable).',
                    'Result publication check: <code>readConcern: \'majority\'</code> so a rolled-back result is never shown.')),
    ),
    example(
        mq('''
db.attempts.insertOne({ roll: 2401, exam: 'SQL', score: 82 },
                      { writeConcern: { w: 'majority', j: true, wtimeout: 5000 } })

db.attempts.find({ exam: 'SQL' }).readPref('secondaryPreferred')
db.results.find({ roll: 2401 }).readConcern('majority')
''', 'Per-operation settings (real replica set)'),
        sh('''
# Defaults for a whole client in the connection string
mongodb://m1,m2,m3/cdac?replicaSet=rs0&w=majority&readConcernLevel=majority&readPreference=primaryPreferred
''', 'Connection-string defaults'),
        title='Example'),
    steps(
        ('Classify operations', 'Critical writes, bulk/low-value writes, real-time reads, analytical reads.'),
        ('Set client defaults', 'Usually <code>w=majority</code>, primary reads.'),
        ('Override per operation', 'Lower write concern for bulk logs; secondary reads for reports.'),
        ('Set wtimeout', 'So writes do not wait forever when members are down.'),
        title='Steps'),
    crossq(
        ('Can reading from a secondary return stale data?', 'Yes: secondaries lag the primary (usually milliseconds, more under load). Use them only where slightly stale data is acceptable.'),
        ('What does w: 0 mean?', 'Fire-and-forget: no acknowledgement at all. Errors are not reported; rarely appropriate.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('What is sharding? Explain the architecture of a sharded cluster.', 'Sharding', minutes=10, cards=[
    definition(
        defbox('<strong>Sharding</strong> partitions a collection\'s data across several <strong>shards</strong> (each a replica set) based on a '
               '<strong>shard key</strong>, so storage and throughput scale horizontally. Components: <strong>mongos</strong> routers (clients connect '
               'to them), <strong>config servers</strong> (a replica set storing metadata: which ranges/chunks live on which shard) and the shards.',
               'Data is divided into <strong>chunks</strong> (ranges of shard-key values); the <strong>balancer</strong> migrates chunks to keep shards even.'),
        tags('Sharding', 'Shard', 'mongos', 'Config Servers', 'Chunk', 'Balancer', 'Horizontal Scaling'),
    ),
    analogy('A national exam board with <strong>regional offices</strong>. Each office (shard) holds records for a range of roll numbers. The '
            'reception desk (mongos) checks the master list (config servers) and sends your request to the right office. If one office gets too '
            'full, some files are moved to another (balancer).'),
    sharding_anim(),
    real_world(
        scenario('When sharding became necessary',
                 p('Attempt data grew past 4 TB and peak exam writes exceeded what one primary could handle. The <code>attempts</code> collection was '
                   'sharded on <code>{exam: 1, roll: 1}</code> across 4 shards; queries for one exam or one student stay targeted, and write load is spread.')),
    ),
    example(
        mq('''
sh.enableSharding('cdac')                          // (optional since 6.0)
db.attempts.createIndex({ exam: 1, roll: 1 })
sh.shardCollection('cdac.attempts', { exam: 1, roll: 1 })

sh.status()                                        // shards, chunks per shard, balancer state
db.attempts.getShardDistribution()                 // data and documents per shard

db.attempts.find({ exam: 'SQL-2026-10', roll: 2401 }).explain()   // SINGLE_SHARD (targeted)
db.attempts.find({ score: { $gt: 90 } }).explain()                 // SHARD_MERGE (scatter-gather)
''', 'Sharding commands (real sharded cluster)'),
        title='Example'),
    steps(
        ('Confirm the need', 'Data size or write throughput beyond one replica set after optimisation.'),
        ('Deploy the topology', 'Config server replica set, shard replica sets, mongos routers.'),
        ('Choose the shard key carefully', 'Hard to change later (resharding exists since 5.0 but is costly).'),
        ('Create the supporting index and shard the collection', '<code>sh.shardCollection(ns, key)</code>.'),
        ('Monitor distribution', '<code>sh.status()</code>, balancer, jumbo chunks.'),
        title='Steps to Shard a Collection'),
    crossq(
        ('Replication vs sharding?', 'Replication copies the same data to several servers for availability and read scaling. Sharding splits different data across servers for capacity and write scaling. Production clusters use both.'),
        ('What is a jumbo chunk?', 'A chunk that grew beyond the maximum size and cannot be split because all its documents share the same shard-key value, so the balancer cannot move it: a symptom of a low-cardinality shard key.'),
    ),
]),

# ------------------------------------------------------------------ 36
Q('How do you choose a good shard key? Ranged vs hashed sharding?', 'Shard Key Selection', minutes=9, cards=[
    definition(
        defbox('A good shard key has <strong>high cardinality</strong> (many distinct values), <strong>low frequency</strong> (no value dominates), '
               'is <strong>not monotonically increasing</strong> (or is hashed), and appears in most queries so they can be <strong>targeted</strong>.',
               '<strong>Ranged sharding</strong> keeps nearby values together (efficient range queries) but monotonic keys create a hot shard. '
               '<strong>Hashed sharding</strong> spreads writes evenly but range queries become scatter-gather.'),
        tags('Shard Key', 'Cardinality', 'Hot Shard', 'Hashed Sharding', 'Ranged Sharding', 'Targeted Query'),
    ),
    analogy('Dividing exam papers among evaluators: by <strong>date received</strong> (monotonic) means today\'s evaluator gets everything; by '
            '<strong>"pass/fail"</strong> (2 values) means only two evaluators can ever work; by <strong>exam + roll number</strong> spreads the '
            'work and still lets you find one student\'s paper quickly.'),
    shard_key_anim(),
    real_world(
        scenario('Choosing for attempts',
                 table(['Candidate key', 'Verdict'], [
                     ['<code>{_id: 1}</code> (ObjectId)', 'Bad: monotonic, all inserts on one shard'],
                     ['<code>{course: 1}</code>', 'Bad: 3 values, jumbo chunks, cannot scale beyond 3 shards'],
                     ['<code>{_id: \'hashed\'}</code>', 'Even writes, but "all attempts of exam X" hits every shard'],
                     ['<code>{exam: 1, roll: 1}</code>', 'Good: high cardinality, queries by exam or exam+roll are targeted'],
                 ])),
    ),
    example(
        mq('''
sh.shardCollection('cdac.logins', { _id: 'hashed' })          // even write distribution
sh.shardCollection('cdac.attempts', { exam: 1, roll: 1 })      // ranged compound key

// MongoDB 5.0+: change a bad key without downtime (expensive, copies data)
db.adminCommand({ reshardCollection: 'cdac.attempts', key: { exam: 1, roll: 1 } })
''', 'Shard key commands (real cluster)'),
        title='Example'),
    steps(
        ('List the dominant queries', 'Which fields appear in nearly all of them?'),
        ('Check cardinality and frequency', '<code>db.coll.aggregate([{$group: {_id: \'$field\', n: {$sum: 1}}}, {$sort: {n: -1}}])</code>.'),
        ('Avoid monotonic ranged keys', 'Hash them or combine with a high-cardinality prefix.'),
        ('Prefer compound keys', 'Coarse field for targeting + fine field for cardinality.'),
        ('Test with production-like load', 'Watch chunk distribution and per-shard write rates.'),
        title='Steps to Choose a Shard Key'),
    crossq(
        ('Can you change the shard key?', 'Since 4.4 you can add suffix fields (refineCollectionShardKey) and since 5.0 fully reshard, but resharding rewrites the collection; choosing well upfront is still essential.'),
        ('What happens to a query without the shard key?', 'mongos sends it to all shards and merges results (scatter-gather), which gets slower as shards are added.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Does MongoDB support transactions? When should you use them?', 'Multi-Document Transactions', minutes=9, cards=[
    definition(
        defbox('Operations on a <strong>single document are always atomic</strong>. Since <strong>4.0</strong> (replica sets) and <strong>4.2</strong> '
               '(sharded clusters), MongoDB supports <strong>multi-document ACID transactions</strong> with snapshot isolation, using a session: '
               '<code>startTransaction</code> → operations → <code>commitTransaction</code> / <code>abortTransaction</code>.',
               'Limits: 60-second default lifetime, more memory/locking overhead, not available on standalone servers. Use them when several '
               'documents must change together and the model cannot put them in one document.'),
        tags('Transactions', 'ACID', 'Session', 'commitTransaction', 'Snapshot Isolation', 'withTransaction'),
    ),
    analogy('A transaction is a <strong>sealed envelope of instructions</strong> given to the office: either every instruction inside is carried '
            'out, or the envelope is returned unopened. Single-document updates are like a single form, which is always processed completely.'),
    txn_anim(),
    real_world(
        scenario('Seat allocation and fee payment',
                 p('Accepting an admission offer inserts a payment, updates the student\'s status and decrements available seats in the course. '
                   'Running these in one transaction guarantees a seat is never taken without payment, or paid for without a seat, even under concurrent offers.')),
    ),
    example(
        mq('''
const session = db.getMongo().startSession()
const cdac = session.getDatabase('cdac')
session.startTransaction({ readConcern: { level: 'snapshot' }, writeConcern: { w: 'majority' } })
try {
  cdac.payments.insertOne({ roll: 2410, amount: 95000, at: new Date() })
  cdac.students.updateOne({ _id: 2410 }, { $set: { status: 'admitted' } })
  const r = cdac.courses.updateOne({ _id: 'PG-DBDA', seats: { $gt: 0 } }, { $inc: { seats: -1 } })
  if (r.modifiedCount === 0) throw new Error('No seats left')
  session.commitTransaction()
} catch (e) {
  session.abortTransaction()
  print('rolled back: ' + e.message)
} finally {
  session.endSession()
}
''', 'Transaction in mongosh (needs a replica set)'),
        js('''
# PyMongo: with_transaction retries transient errors automatically
with client.start_session() as s:
    def admit(s):
        db = s.client.cdac
        db.payments.insert_one({"roll": 2410, "amount": 95000}, session=s)
        db.students.update_one({"_id": 2410}, {"$set": {"status": "admitted"}}, session=s)
        r = db.courses.update_one({"_id": "PG-DBDA", "seats": {"$gt": 0}}, {"$inc": {"seats": -1}}, session=s)
        if r.modified_count == 0:
            raise RuntimeError("No seats left")
    s.with_transaction(admit)
''', 'Python (PyMongo)'),
        title='Example'),
    steps(
        ('First try a single-document design', 'Atomic without a transaction (e.g. embed seat counts and holders).'),
        ('Use a replica set', 'Transactions do not work on a standalone mongod.'),
        ('Wrap the operations', 'Start a session and use <code>withTransaction</code> (handles retries).'),
        ('Keep them short', 'Few documents, well under 60 seconds, no user interaction inside.'),
        ('Handle errors', 'Abort on business-rule failure; retry on TransientTransactionError.'),
        title='Steps to Use a Transaction'),
    crossq(
        ('If MongoDB has transactions, should you model it like an RDBMS?', 'No. Transactions are for the cases that need them; an RDBMS-style normalised model with transactions everywhere loses MongoDB\'s performance benefits.'),
        ('What is a write conflict?', 'Two transactions modifying the same document: one aborts with a WriteConflict (TransientTransactionError) and should be retried.'),
    ),
]),
])
