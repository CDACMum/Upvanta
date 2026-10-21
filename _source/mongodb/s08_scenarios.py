from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

EXAM_SETUP = """
db.exams.insertOne({ _id: 'SQL-2026-10', title: 'SQL Module End', duration: 60, maxMarks: 100,
  questions: [ { qno: 1, text: 'Which clause filters groups?', options: ['WHERE', 'HAVING', 'ORDER BY'], answer: 1 },
               { qno: 2, text: 'Default isolation in MySQL InnoDB?', options: ['READ COMMITTED', 'REPEATABLE READ'], answer: 1 } ] })
db.attempts.createIndex({ roll: 1, exam: 1 }, { unique: true })
db.attempts.insertMany([
  { roll: 2401, exam: 'SQL-2026-10', score: 82, submittedAt: new Date('2026-10-13T10:58:00Z') },
  { roll: 2402, exam: 'SQL-2026-10', score: 91, submittedAt: new Date('2026-10-13T10:41:00Z') },
  { roll: 2403, exam: 'SQL-2026-10', score: 91, submittedAt: new Date('2026-10-13T10:55:00Z') },
  { roll: 2404, exam: 'SQL-2026-10', score: 38, submittedAt: new Date('2026-10-13T11:00:00Z') }
])
"""

SECTION = dict(level='expert', title='Real-World Scenarios', questions=[

# ------------------------------------------------------------------ 38
Q('Scenario: Design the MongoDB schema for an online exam portal.', 'Exam Portal Schema Design', minutes=12, cards=[
    definition(
        defbox('Schema design in MongoDB starts from <strong>access patterns</strong>: list the operations, their frequency and the data each needs, then '
               'decide embedding vs referencing per relationship, add computed fields for expensive reads, and design indexes for every frequent query.'),
        table(['Operation', 'Frequency', 'Design decision'], [
            ['Load an exam with all questions', 'Every candidate at start', 'Embed questions in the exam document'],
            ['Save an answer', 'Every few seconds per candidate', 'One attempt document per (roll, exam); <code>$set</code> one answer'],
            ['Prevent a second attempt', 'Every start', 'Unique index <code>{roll, exam}</code>'],
            ['Leaderboard per exam', 'After the exam', 'Index <code>{exam: 1, score: -1, submittedAt: 1}</code>'],
            ['Exam statistics on dashboard', 'Many reads', 'Computed <code>exam_stats</code> updated on submission'],
        ]),
        tags('Schema Design', 'Access Patterns', 'Embedding', 'Unique Index', 'Computed Pattern', 'Leaderboard'),
    ),
    analogy('Designing the schema is like <strong>arranging an exam hall</strong>: question papers come sealed as one packet per exam (embedded), each '
            'candidate gets one answer booklet (attempt document), the invigilator\'s register prevents anyone from sitting twice (unique index), '
            'and a tally sheet is updated as booklets are collected (computed stats).'),
    exam_schema_anim(),
    real_world(
        scenario('Why not one document per student with all attempts inside?',
                 p('A student takes dozens of exams over a course and each attempt holds all answers: the array would grow without limit and every '
                   'answer save would rewrite a large document. Attempts are independent, queried by exam, and therefore their own collection.')),
    ),
    example(
        mql('''
// Start an exam: load it once, with questions embedded (answers hidden)
db.exams.findOne({ _id: 'SQL-2026-10' }, { 'questions.answer': 0 })

// A second attempt by the same student is rejected by the unique index
db.attempts.insertOne({ roll: 2401, exam: 'SQL-2026-10', score: 0 })

// Leaderboard: highest score first, earlier submission wins ties
db.attempts.find({ exam: 'SQL-2026-10' }, { _id: 0, roll: 1, score: 1 }).sort({ score: -1, submittedAt: 1 }).limit(3)

// Exam statistics
db.attempts.aggregate([
  { $match: { exam: 'SQL-2026-10' } },
  { $group: { _id: '$exam', attempts: { $sum: 1 }, avg: { $avg: '$score' },
              passed: { $sum: { $cond: [{ $gte: ['$score', 40] }, 1, 0] } } } }
])
''', setup=EXAM_SETUP),
        title='Example'),
    steps(
        ('List operations with frequency and latency needs', 'As in the table above.'),
        ('Identify entities and relationships', 'Students, exams, questions, attempts, stats.'),
        ('Decide embed vs reference', 'Questions embedded in exams; attempts separate; small student info copied into attempts if needed for reports.'),
        ('Design indexes per query', 'Unique {roll, exam}; {exam, score, submittedAt}.'),
        ('Add validation and computed fields', '$jsonSchema on attempts; exam_stats updated with $inc.'),
        ('Load-test exam-day traffic', 'Thousands of concurrent answer saves; check latency and replica-set lag.'),
        title='Steps to Design the Schema'),
    crossq(
        ('How do you save answers efficiently?', '<code>updateOne({roll, exam}, {$set: {\'answers.q17\': 2, lastSavedAt: now}})</code>: a small targeted update instead of resending the whole attempt.'),
        ('How do you stop candidates from seeing correct answers?', 'Project them out (<code>{\'questions.answer\': 0}</code>) in the API, or store answers in a separate collection only the grader reads.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('How is MongoDB used in data engineering pipelines (CDC, Spark, Kafka)?', 'MongoDB in Data Pipelines', minutes=10, cards=[
    definition(
        defbox('MongoDB is usually the <strong>operational</strong> store; analytics run elsewhere. Data moves out by: <strong>batch export</strong> '
               '(<code>mongoexport</code>, <code>mongodump</code>, Spark connector reads), or <strong>change data capture</strong> with '
               '<strong>change streams</strong>, real-time insert/update/delete events built on the oplog, consumed by Kafka connectors (MongoDB '
               'Kafka Connector, Debezium) or applications.',
               'Data also flows <em>in</em>: Spark or Kafka sink connectors write processed results back for applications to serve.'),
        tags('Change Streams', 'CDC', 'Kafka Connector', 'Spark Connector', 'mongoexport', 'Debezium', 'Data Lake'),
    ),
    analogy('MongoDB is the <strong>shop counter</strong> where sales happen live. Change streams are a <strong>CCTV feed</strong> of every sale sent to '
            'head office as it happens; the nightly export is the <strong>end-of-day ledger copy</strong>.'),
    cdc_anim(),
    real_world(
        scenario('Near-real-time attendance analytics',
                 p('A change stream on <code>attendance</code> feeds a Kafka topic through the MongoDB source connector; Spark Structured Streaming '
                   'aggregates attendance per centre every minute into Parquet on the data lake and a summary collection for the dashboard. '
                   'The nightly batch job is kept only for reconciliation.')),
    ),
    example(
        mq('''
// Change stream: react to new submissions (needs a replica set)
const cursor = db.attempts.watch([ { $match: { operationType: { $in: ['insert', 'update'] } } } ],
                                 { fullDocument: 'updateLookup' })
while (cursor.hasNext()) {
  const ev = cursor.next()
  print(ev.operationType, ev.documentKey._id, ev.fullDocument.score)
  // store ev._id (resume token) to resume after a restart: watch([], { resumeAfter: token })
}
''', 'Change stream in mongosh'),
        js('''
# PySpark with the MongoDB Spark Connector (v10)
df = (spark.read.format("mongodb")
      .option("connection.uri", "mongodb://m1,m2,m3/?replicaSet=rs0")
      .option("database", "cdac").option("collection", "attempts")
      .load())
(df.filter("exam = 'SQL-2026-10'")
   .groupBy("exam").avg("score")
   .write.mode("overwrite").parquet("s3a://cdac-lake/gold/exam_stats/"))
''', 'Batch read with Spark'),
        sh('''
# Export for a nightly batch / backup
mongoexport --uri "mongodb://m1/cdac" --collection attempts --query '{"exam":"SQL-2026-10"}' \\
            --type json --out attempts_sql_2026_10.json
mongodump --uri "mongodb://m1/cdac" --gzip --archive=cdac_2026-10-13.gz
''', 'Command-line export and backup'),
        title='Example'),
    steps(
        ('Decide latency needs', 'Daily batch is enough? Use the Spark connector or mongoexport. Minutes or seconds? Change streams + Kafka.'),
        ('For CDC, use a replica set', 'Change streams require the oplog.'),
        ('Persist resume tokens', 'So consumers continue exactly where they stopped after a restart.'),
        ('Flatten documents for analytics', 'Explode arrays and nested fields into columns in Spark.'),
        ('Land in the lake/warehouse', 'Parquet/Iceberg or a warehouse table; schedule with Airflow.'),
        title='Steps to Build the Pipeline'),
    crossq(
        ('What happens if a change-stream consumer is down for a long time?', 'It can resume only while its resume token is still in the oplog window; after that it must re-snapshot the collection. Size the oplog for the longest expected outage.'),
        ('Why not run analytics directly on the production MongoDB?', 'Heavy aggregations compete with application traffic. Use a dedicated analytics secondary (hidden member/analytics nodes) or move data to a lake/warehouse.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('MongoDB troubleshooting scenarios commonly asked in interviews', 'Troubleshooting Scenarios', minutes=10, cards=[
    definition(
        defbox('Interviewers present symptoms and expect a structured diagnosis: <strong>symptom → evidence (logs, explain, metrics) → root cause → '
               'fix → prevention</strong>. Most MongoDB problems come from missing indexes, poor data models, shard keys, or misunderstood consistency settings.'),
        tags('Troubleshooting', 'Duplicate Key', 'Slow Query', '16 MB', 'Hot Shard', 'Replication Lag'),
    ),
    analogy('Like a <strong>mechanic</strong>: a strange noise (symptom), a diagnostic scan (explain, profiler), the worn part (root cause), a '
            'replacement (fix) and a service schedule (monitoring) so it does not happen again.'),
    scenarios_anim(),
    real_world(
        scenario('1. Duplicate students after a network retry',
                 ul('The app retried an insert with a new ObjectId after a timeout; both inserts succeeded.',
                    'Fix: use the roll number as <code>_id</code> (or a unique index on it) and <code>updateOne(..., {upsert: true})</code> so retries are idempotent.')),
        scenario('2. Dashboard query takes 8 seconds',
                 ul('Profiler shows COLLSCAN on 5 million attempts and an in-memory SORT.',
                    'Fix: compound index in ESR order matching the filter and sort; project only needed fields.')),
        scenario('3. "BSONObj size … is invalid. Size must be between 0 and 16793600"',
                 ul('An activity array inside the student document grew for years.',
                    'Fix: move activities to their own collection (child references parent); keep a bounded "recent" subset.')),
        scenario('4. One shard at 95% CPU, others idle',
                 ul('Shard key <code>{createdAt: 1}</code>: all new inserts land in the last chunk.',
                    'Fix: reshard to a hashed or compound key such as <code>{exam: 1, roll: 1}</code>.')),
        scenario('5. Student updates marks but still sees the old value',
                 ul('Reads use <code>secondaryPreferred</code> and the secondary lags.',
                    'Fix: read-your-own-writes flows read from the primary or use causally consistent sessions.')),
    ),
    example(
        mql('''
// Idempotent "create or update" survives retries: running it twice gives one document
db.students.updateOne({ _id: 2410 }, { $set: { name: 'Isha', course: 'PG-DBDA' } }, { upsert: true })
db.students.updateOne({ _id: 2410 }, { $set: { name: 'Isha', course: 'PG-DBDA' } }, { upsert: true })
db.students.countDocuments({ _id: 2410 })

// Find documents with unexpectedly large arrays before they become a problem
db.students.aggregate([
  { $project: { name: 1, nScores: { $size: '$scores' }, nSkills: { $size: '$skills' } } },
  { $sort: { nSkills: -1 } }, { $limit: 3 }
])
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Collect the exact error and timing', 'Driver error code, server logs, when it started.'),
        ('Gather evidence', 'Profiler/slow log, <code>explain()</code>, <code>rs.status()</code>, <code>sh.status()</code>, Atlas/mongostat metrics.'),
        ('Name the root cause', 'Index, model, shard key, consistency setting, capacity.'),
        ('Fix and verify', 'Re-run explain/load test; compare metrics.'),
        ('Prevent', 'Validation rules, unique indexes, alerts on slow queries and replication lag.'),
        title='Steps for Any MongoDB Problem'),
    crossq(
        ('How do you find which queries are slow in production?', 'Enable the profiler for slow operations (<code>db.setProfilingLevel(1, {slowms: 100})</code>), read the slow-query entries in the mongod log, or use Atlas Query Profiler / Performance Advisor.'),
        ('What is replication lag and how do you monitor it?', 'How far a secondary\'s applied oplog is behind the primary. Check <code>rs.printSecondaryReplicationInfo()</code> or monitoring metrics; causes are slow disks, heavy writes or network issues.'),
    ),
]),
])
