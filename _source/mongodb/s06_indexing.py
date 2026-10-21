from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

SECTION = dict(level='advanced', title='Indexing & Performance', questions=[

# ------------------------------------------------------------------ 28
Q('What is an index in MongoDB? How does it speed up queries?', 'Indexes', minutes=9, cards=[
    definition(
        defbox('An <strong>index</strong> is a separate, sorted data structure (a <strong>B-tree</strong>) that stores the values of one or more fields '
               'with pointers to the documents. With a suitable index the query planner performs an <strong>IXSCAN</strong> (index scan) and fetches '
               'only matching documents, instead of a <strong>COLLSCAN</strong> that reads every document.',
               'Every collection has a unique index on <code>_id</code>. Indexes speed up reads (filters, sorts, range queries) but cost disk/RAM and '
               'slow down writes, because each insert/update must also update every index.'),
        tags('Index', 'B-tree', 'IXSCAN', 'COLLSCAN', 'createIndex', 'Query Planner'),
    ),
    analogy('The <strong>index at the back of a textbook</strong>: to find "partitioning" you look it up alphabetically and jump to pages 112 and 140, '
            'instead of reading the whole book. Each new edition must also update the index, which is the write cost.'),
    index_anim(),
    real_world(
        scenario('Result lookup during result day',
                 p('On result day, 30,000 students look up <code>{roll, exam}</code>. Without an index each lookup scanned 2 million attempts '
                   '(~1.2 s, CPU at 100%). A compound index <code>{roll: 1, exam: 1}</code> made each lookup a few milliseconds.')),
    ),
    example(
        mql('''
db.students.createIndex({ marks: 1 })
db.students.createIndex({ course: 1, marks: -1 }, { name: 'course_marks' })
db.students.getIndexes()

db.students.find({ course: 'PG-DBDA' }, { _id: 0, name: 1, marks: 1 }).sort({ marks: -1 })
db.students.dropIndex('marks_1')
''', setup=STUDENTS),
        mq('''
db.students.find({ marks: { $gte: 90 } }).explain('executionStats')
// Without the index:  winningPlan.stage: 'COLLSCAN',  totalDocsExamined: 8
// With { marks: 1 }:  winningPlan: FETCH ← IXSCAN { marks: 1 }, totalKeysExamined: 1, totalDocsExamined: 1
''', 'Checking with explain (needs a real server; values from this 8-document example)'),
        title='Example'),
    steps(
        ('Find the slow query', 'Profiler, slow query log or Atlas Performance Advisor.'),
        ('Read its explain plan', 'COLLSCAN or high docsExamined/nReturned ratio?'),
        ('Create the index', '<code>db.coll.createIndex({field: 1})</code> (builds without blocking reads/writes in 4.2+).'),
        ('Verify', 'explain shows IXSCAN and fewer documents examined.'),
        ('Remove unused indexes', '<code>$indexStats</code> shows how often each index is used.'),
        title='Steps to Add an Index'),
    crossq(
        ('Does the direction 1 / -1 matter?', 'For a single-field index, no: it can be read in both directions. For compound indexes used for sorting on several fields, the relative directions must match the sort (or its exact reverse).'),
        ('Why not index every field?', 'Each index slows every write, uses RAM (the working set should fit in memory) and disk. Index only what real queries need.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('What types of indexes does MongoDB support?', 'Index Types', minutes=10, cards=[
    definition(
        table(['Type', 'Create', 'Use'], [
            ['Single field', '<code>{marks: 1}</code>', 'Filter/sort on one field'],
            ['Compound', '<code>{course: 1, marks: -1}</code>', 'Several fields; order matters (ESR rule)'],
            ['Multikey', 'automatic on array fields', 'Query array elements: <code>{skills: \'sql\'}</code>'],
            ['Text', '<code>{bio: \'text\'}</code>', 'Keyword search with <code>$text</code> (Atlas Search for advanced search)'],
            ['2dsphere', '<code>{location: \'2dsphere\'}</code>', 'Geo queries: <code>$near</code>, <code>$geoWithin</code>'],
            ['Hashed', '<code>{_id: \'hashed\'}</code>', 'Hashed sharding, equality lookups'],
            ['Wildcard', '<code>{\'specs.$**\': 1}</code>', 'Unknown/dynamic field names'],
        ]),
        table(['Option', 'Effect'], [
            ['<code>unique: true</code>', 'Rejects duplicate values (error 11000)'],
            ['<code>expireAfterSeconds</code> (TTL)', 'Background thread deletes documents after the time on a date field'],
            ['<code>partialFilterExpression</code>', 'Index only documents matching a filter (smaller index)'],
            ['<code>sparse: true</code>', 'Skip documents that lack the field (older alternative to partial)'],
            ['<code>collation</code>', 'Case-insensitive / language-aware comparisons'],
        ]),
        tags('Compound Index', 'Multikey', 'Text Index', '2dsphere', 'Hashed', 'TTL', 'Unique', 'Partial', 'Wildcard'),
    ),
    analogy('Different <strong>indexes in a library</strong>: by title (single), by author then year (compound), by keyword (text), a map of '
            'branches (geo), and a "return by" list that removes overdue slips automatically (TTL).'),
    index_types_anim(),
    real_world(
        scenario('Indexes in the exam platform',
                 ul('<code>attempts</code>: unique compound <code>{roll: 1, exam: 1}</code>, so a student cannot have two attempts of the same exam.',
                    '<code>otps</code>: TTL index on <code>createdAt</code> with <code>expireAfterSeconds: 300</code>; OTPs vanish after 5 minutes.',
                    '<code>students</code>: partial index on <code>{course: 1}</code> only where <code>status: \'active\'</code>.',
                    '<code>centres</code>: 2dsphere on location for "nearest exam centre".')),
    ),
    example(
        mql('''
// unique compound index prevents duplicate attempts
db.attempts.createIndex({ roll: 1, exam: 1 }, { unique: true })
db.attempts.insertOne({ roll: 2401, exam: 'SQL', score: 82 })
db.attempts.insertOne({ roll: 2401, exam: 'SQL', score: 90 })

// TTL: delete OTP documents 300 seconds after createdAt
db.otps.createIndex({ createdAt: 1 }, { expireAfterSeconds: 300 })

// partial index: only active students are indexed
db.students.createIndex({ course: 1 }, { partialFilterExpression: { status: 'active' } })

db.attempts.getIndexes()
db.otps.getIndexes()
'''),
        mq('''
db.students.createIndex({ bio: 'text' })
db.students.find({ $text: { $search: 'spark kafka' } }, { score: { $meta: 'textScore' } })

db.centres.createIndex({ location: '2dsphere' })
db.centres.find({ location: { $near: { $geometry: { type: 'Point', coordinates: [73.0657, 19.0473] }, $maxDistance: 5000 } } })
''', 'Text and geospatial queries (server features)'),
        title='Example'),
    steps(
        ('Identify the query shape', 'Equality, range, sort, array, text, geo?'),
        ('Pick the index type and options', 'Compound in ESR order; unique/TTL/partial as needed.'),
        ('Create it', '<code>createIndex(keys, options)</code>; on large collections during low traffic.'),
        ('Check usage', '<code>db.coll.aggregate([{$indexStats: {}}])</code>; drop unused ones.'),
        title='Steps'),
    crossq(
        ('Can a compound index have two array fields?', 'No. A compound multikey index may include at most one array-valued field per document.'),
        ('How precise is TTL deletion?', 'The TTL monitor runs about every 60 seconds, so documents are removed shortly after expiry, not at the exact second.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How should fields be ordered in a compound index? Explain the ESR rule.', 'Compound Indexes & ESR', minutes=9, cards=[
    definition(
        defbox('In a compound index, entries are sorted by the first field, then the second, and so on. Order fields as '
               '<strong>Equality → Sort → Range</strong> (ESR): fields compared with equality first, then fields used in <code>sort()</code>, '
               'then fields with range conditions (<code>$gt</code>, <code>$lt</code>, <code>$in</code> with many values, <code>$regex</code>).',
               'A compound index also serves queries on its <strong>prefixes</strong>: <code>{a, b, c}</code> supports <code>{a}</code> and '
               '<code>{a, b}</code>, but not <code>{b}</code> or <code>{c}</code> alone.'),
        tags('Compound Index', 'ESR Rule', 'Index Prefix', 'In-memory Sort', 'Equality Sort Range'),
    ),
    analogy('A <strong>telephone directory</strong> is sorted by city, then surname, then first name. Finding "Mumbai, Sharma" is fast; finding '
            'everyone named "Rohit" (third field) means reading the whole book. Put the field you always know exactly (city) first.'),
    esr_anim(),
    real_world(
        scenario('Fixing an in-memory sort',
                 p('The leaderboard query <code>find({exam: \'SQL\', score: {$gte: 40}}).sort({submittedAt: 1})</code> used index '
                   '<code>{exam: 1, score: 1, submittedAt: 1}</code> and showed a SORT stage. Reordering to <code>{exam: 1, submittedAt: 1, score: 1}</code> '
                   '(E-S-R) removed the in-memory sort and cut latency by 80%.')),
    ),
    example(
        mql('''
db.students.createIndex({ course: 1, name: 1, marks: 1 })     // E, S, R

db.students.find({ course: 'PG-DBDA', marks: { $gte: 75 } }, { _id: 0, name: 1, marks: 1 }).sort({ name: 1 })
db.students.getIndexes()
''', setup=STUDENTS),
        mq('''
// explain('executionStats') of the query above
//   with { course: 1, name: 1, marks: 1 }:  IXSCAN → FETCH, no SORT stage
//   with { course: 1, marks: 1, name: 1 }:  IXSCAN → FETCH → SORT (in memory)

// prefix rule: { course: 1, name: 1, marks: 1 } also serves
db.students.find({ course: 'PG-DAC' })                       // prefix { course }
db.students.find({ course: 'PG-DAC', name: 'Rohit' })        // prefix { course, name }
// but NOT
db.students.find({ marks: { $gt: 80 } })                     // not a prefix → needs its own index
''', 'What explain shows (real server)'),
        title='Example'),
    steps(
        ('Write the query shape', 'Which fields use equality, which are sorted, which use ranges?'),
        ('Order the index fields E → S → R', 'Most selective equality field first if there are several.'),
        ('Match sort directions', 'Sort {a: 1, b: -1} needs an index {a: 1, b: -1} or {a: -1, b: 1}.'),
        ('Reuse prefixes', 'One {a, b, c} index can replace separate {a} and {a, b} indexes.'),
        ('Confirm with explain', 'No SORT stage, keys examined ≈ documents returned.'),
        title='Steps to Design a Compound Index'),
    crossq(
        ('Is <code>$in</code> equality or range?', 'With a few values the planner can treat it like several equalities (and still sort via a merge); with many values treat it as a range for ESR purposes.'),
        ('Does the order of fields in the query filter matter?', 'No. The planner reorders conditions; only the index field order matters.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('What is a covered query? How do you read an explain plan?', 'Covered Queries & explain()', minutes=9, cards=[
    definition(
        defbox('A <strong>covered query</strong> is answered entirely from an index: all filter fields and all returned fields are in the index, so no '
               'document is fetched (<code>totalDocsExamined: 0</code>, plan has PROJECTION_COVERED/IXSCAN but no FETCH). You must exclude '
               '<code>_id</code> unless it is in the index.',
               '<code>explain(\'executionStats\')</code> shows the <strong>winning plan</strong> (stages), <strong>rejected plans</strong>, and execution '
               'statistics: <code>nReturned</code>, <code>totalKeysExamined</code>, <code>totalDocsExamined</code>, <code>executionTimeMillis</code>.'),
        tags('Covered Query', 'explain', 'executionStats', 'winningPlan', 'totalDocsExamined', 'PROJECTION_COVERED'),
    ),
    analogy('Answering "which pages mention Hive?" from the <strong>book\'s index alone</strong>, without opening any page, is a covered query. '
            'explain() is the <strong>receipt</strong> that tells you how many index entries and pages were actually touched.'),
    covered_anim(),
    explain_anim(),
    real_world(
        scenario('High-traffic lookup',
                 p('The mobile app\'s "my courses" screen needs only course codes and names for a roll number. A covered index '
                   '<code>{roll: 1, courseCode: 1, courseName: 1}</code> with projection <code>{_id: 0, courseCode: 1, courseName: 1}</code> '
                   'serves it from memory without touching documents.')),
    ),
    example(
        mq('''
db.enrolments.createIndex({ roll: 1, courseCode: 1, courseName: 1 })
db.enrolments.find({ roll: 2401 }, { _id: 0, courseCode: 1, courseName: 1 }).explain('executionStats')

// abridged output of a covered query (MongoDB 7)
{
  queryPlanner: {
    winningPlan: {
      stage: 'PROJECTION_COVERED',
      inputStage: { stage: 'IXSCAN', keyPattern: { roll: 1, courseCode: 1, courseName: 1 }, indexName: 'roll_1_courseCode_1_courseName_1' }
    },
    rejectedPlans: []
  },
  executionStats: { nReturned: 3, executionTimeMillis: 0, totalKeysExamined: 3, totalDocsExamined: 0 }
}
''', 'explain() on a real server (abridged, values illustrative)'),
        title='Example'),
    steps(
        ('Run explain(\'executionStats\')', 'On the exact query, with realistic data.'),
        ('Check the stage tree', 'COLLSCAN = no index; SORT = in-memory sort; FETCH after IXSCAN = documents read.'),
        ('Compare the counts', 'keysExamined and docsExamined should be close to nReturned.'),
        ('For hot queries try covering', 'Add returned fields to the index and exclude _id.'),
        title='Steps to Analyse a Query'),
    crossq(
        ('Why can\'t a query on an array field be covered?', 'A multikey index stores one entry per array element, so it cannot reconstruct the whole array value; MongoDB must fetch the document.'),
        ('What are the three explain verbosity modes?', '<code>queryPlanner</code> (plan only, default), <code>executionStats</code> (runs the winning plan), <code>allPlansExecution</code> (also stats for rejected plans).'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('How do you improve MongoDB performance? Give a checklist.', 'Performance Checklist', minutes=9, cards=[
    definition(
        table(['Area', 'What to check / do'], [
            ['Indexes', 'Every frequent query uses an index (ESR order); remove unused indexes; avoid regex/$where scans'],
            ['Data model', 'Embed what is read together; no unbounded arrays; documents of reasonable size; bucket pattern for time data'],
            ['Queries', 'Project only needed fields; limit results; keyset pagination; $match early in pipelines'],
            ['Memory', 'Working set (hot data + indexes) fits in RAM (WiredTiger cache ≈ 50% of RAM − 1 GB)'],
            ['Writes', 'Batch inserts (<code>insertMany</code>, <code>bulkWrite</code>), appropriate write concern, avoid hot shard keys'],
            ['Reads at scale', 'Read from secondaries where staleness is acceptable; cache hot data (Redis)'],
            ['Monitoring', 'Profiler, <code>mongostat</code>, <code>mongotop</code>, <code>db.currentOp()</code>, Atlas metrics, slow query log'],
        ]),
        tags('Performance', 'Working Set', 'Profiler', 'mongostat', 'Index', 'Data Model'),
    ),
    analogy('Speeding up a <strong>canteen queue</strong>: an index is a menu board so nobody asks the cook about every dish; good modelling is '
            'pre-packing combo meals that are ordered together; projection is handing over only what was ordered; RAM is counter space, which '
            'is fast only while everything fits on it.'),
    troubleshoot_anim(),
    real_world(
        scenario('Before and after',
                 table(['Change', 'Effect'], [
                     ['Index {exam: 1, submittedAt: 1, score: 1}', 'Leaderboard 1.4 s → 12 ms'],
                     ['Projection of 5 fields instead of whole attempt (300 KB)', 'Network traffic −95%'],
                     ['Logins moved out of the student document', 'Student updates 10× faster'],
                     ['Read preference secondaryPreferred for reports', 'Primary CPU −40% during exams'],
                 ])),
    ),
    example(
        mq('''
db.setProfilingLevel(1, { slowms: 100 })                 // record operations slower than 100 ms
db.system.profile.find().sort({ millis: -1 }).limit(5)   // slowest recent operations
db.students.aggregate([ { $indexStats: {} } ])           // how often each index is used
db.currentOp({ secs_running: { $gte: 5 } })             // long-running operations right now
db.serverStatus().wiredTiger.cache                       // cache usage
''', 'Diagnostics (real server)'),
        sh('''
mongostat --host localhost:27017      # inserts/queries/updates per second, cache, queues
mongotop  --host localhost:27017      # time spent reading/writing per collection
''', 'Command-line monitoring'),
        title='Example'),
    steps(
        ('Measure', 'Profiler / slow log / Atlas: find the top slow and most frequent operations.'),
        ('Explain them', 'Look for COLLSCAN, SORT, high examined/returned ratios.'),
        ('Fix indexes first', 'Usually the biggest and cheapest win.'),
        ('Fix the model', 'Unbounded arrays, huge documents, frequent $lookup.'),
        ('Scale hardware/topology last', 'More RAM, read replicas, sharding.'),
        title='Steps'),
    crossq(
        ('What is the working set?', 'The data and indexes the application touches frequently. If it does not fit in the WiredTiger cache/RAM, reads go to disk and latency jumps.'),
        ('When do you shard?', 'When a single replica set cannot hold the data or sustain the write throughput even after indexing and modelling are optimised, not as a first step.'),
    ),
]),
])
