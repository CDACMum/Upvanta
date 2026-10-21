from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

SECTION = dict(level='intermediate', title='Data Modeling', questions=[

# ------------------------------------------------------------------ 23
Q('Embedding vs referencing: how do you decide?', 'Embedding vs Referencing', minutes=10, cards=[
    definition(
        defbox('<strong>Embedding</strong> stores related data inside the parent document (sub-documents, arrays). <strong>Referencing</strong> stores '
               'the related document\'s <code>_id</code> and keeps it in its own collection (like a foreign key).',
               'MongoDB modelling is driven by <strong>access patterns</strong>: "data that is accessed together should be stored together", while '
               'keeping documents bounded in size.'),
        table(['Prefer embedding when…', 'Prefer referencing when…'], [
            ['The child belongs to one parent ("contains")', 'The child is shared by many parents (many-to-many)'],
            ['It is read together with the parent', 'It is often read on its own'],
            ['It is small and bounded (a few addresses)', 'It is large or grows without limit (logs, attempts)'],
            ['You need atomic updates of parent + child', 'It changes frequently and independently'],
        ]),
        tags('Embedding', 'Referencing', 'Data Modeling', 'Access Patterns', 'Denormalization'),
    ),
    analogy('Embedding is keeping a student\'s <strong>photo and address inside their file</strong>. Referencing is writing "<strong>see course '
            'booklet PG-DBDA</strong>" in the file instead of copying the 40-page course booklet into every student\'s file.'),
    embed_ref_anim(),
    real_world(
        scenario('Student, course, attempts',
                 ul('Address and phone numbers → <strong>embedded</strong> in student (owned, small, read with the profile).',
                    'Course details → <strong>referenced</strong> by course id (shared by 300 students, edited centrally); a few fields such as course name may be copied (extended reference).',
                    'Exam attempts → <strong>separate collection</strong> with the roll number (unbounded, queried by exam).')),
    ),
    example(
        mql('''
// Embedded: one read gives the whole profile, one update changes it atomically
db.students.insertOne({ _id: 2401, name: 'Anuj', address: { city: 'Pune', pin: '411001' }, phones: ['98xxxxxx01'] })
db.students.updateOne({ _id: 2401 }, { $set: { 'address.city': 'Mumbai' }, $push: { phones: '98xxxxxx02' } })
db.students.findOne({ _id: 2401 })

// Referenced: course is shared, the student stores only its id
db.courses.insertOne({ _id: 'PG-DBDA', title: 'Big Data Analytics', months: 6, fee: 95000 })
db.students.updateOne({ _id: 2401 }, { $set: { courseId: 'PG-DBDA' } })
db.students.aggregate([
  { $match: { _id: 2401 } },
  { $lookup: { from: 'courses', localField: 'courseId', foreignField: '_id', as: 'course' } },
  { $project: { name: 1, 'course.title': 1, 'course.months': 1 } }
])
'''),
        title='Example'),
    steps(
        ('List the screens/APIs and their queries', 'What is read together? What is written together?'),
        ('Check cardinality', 'One-to-few, one-to-many, one-to-squillions, many-to-many.'),
        ('Check growth', 'Anything that grows without limit gets its own collection.'),
        ('Decide per relationship', 'Embed, reference, or reference + copy a few fields.'),
        ('Validate with real data', 'Document sizes, query counts per page, index needs.'),
        title='Steps to Model a Relationship'),
    crossq(
        ('Is duplicating data in MongoDB bad?', 'Not necessarily. Copying a few rarely changing fields (course title into enrolment) avoids joins; the cost is updating copies when the source changes, which is acceptable for slowly changing data.'),
        ('How do you model many-to-many (students ↔ courses)?', 'Arrays of references on one or both sides (<code>courseIds</code> in students), or a separate enrolment collection when the relationship has its own attributes (date, fee status).'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you model one-to-many relationships of different sizes?', 'One-to-Many Patterns', minutes=8, cards=[
    definition(
        table(['Cardinality', 'Example', 'Model'], [
            ['One-to-few (≤ tens)', 'Addresses of a student', 'Embed an array of sub-documents'],
            ['One-to-many (hundreds–thousands)', 'Marks entries of a student', 'Array of child ids in the parent, or parent id in each child'],
            ['One-to-squillions (unbounded)', 'Attendance/log events of a student', 'Parent id in each child only; never an array in the parent'],
        ]),
        tags('One-to-Few', 'One-to-Many', 'One-to-Squillions', 'Unbounded Arrays', 'Parent Reference'),
    ),
    analogy('Few: keep your <strong>three ID cards in your wallet</strong>. Many: keep a <strong>list of receipt numbers</strong> in your wallet '
            'and the receipts in a box. Squillions: each <strong>CCTV frame</strong> is labelled with the camera number; the camera does not carry a list of its frames.'),
    one_to_many_anim(),
    real_world(
        scenario('A production incident',
                 p('A first version stored every login event in an array inside the student document. Active students\' documents grew to several MB; '
                   'every login rewrote the whole document, and a few hit the 16 MB limit and failed. Moving logins to their own collection '
                   '(with <code>roll</code> and a TTL index) fixed it.')),
    ),
    example(
        mql('''
// one-to-squillions: child references parent
db.logins.insertMany([
  { roll: 2401, at: new Date('2026-10-13T09:00:00Z'), device: 'web' },
  { roll: 2401, at: new Date('2026-10-13T14:10:00Z'), device: 'app' },
  { roll: 2402, at: new Date('2026-10-13T09:05:00Z'), device: 'web' }
])
db.logins.createIndex({ roll: 1, at: -1 })
db.logins.find({ roll: 2401 }, { _id: 0, at: 1, device: 1 }).sort({ at: -1 }).limit(1)

// one-to-many with a bounded "recent" array (subset pattern)
db.students.updateOne(
  { _id: 2401 },
  { $push: { recentLogins: { $each: [ { at: new Date('2026-10-13T14:10:00Z') } ], $slice: -3 } } },
  { upsert: true }
)
db.students.findOne({ _id: 2401 })
'''),
        title='Example'),
    steps(
        ('Estimate the maximum number of children', 'Per parent, over the application\'s lifetime.'),
        ('Few → embed', 'Array of sub-documents.'),
        ('Many → reference', 'Array of ids (bounded) or parent id in each child.'),
        ('Unbounded → child collection', 'Index on the parent id (+ time).'),
        ('Need recent items in the parent?', '<code>$push</code> with <code>$slice</code> to keep only the last N.'),
        title='Steps'),
    crossq(
        ('Why are unbounded arrays dangerous?', 'Documents grow without limit (16 MB cap), every update rewrites a larger document, indexes on the array become huge, and reads fetch data you rarely need.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What schema design patterns do you know in MongoDB?', 'Schema Design Patterns', minutes=10, cards=[
    definition(
        table(['Pattern', 'Problem it solves', 'Idea'], [
            ['Bucket', 'Millions of tiny documents (sensor readings, logs)', 'Group a time window per document with an array of readings'],
            ['Computed', 'Expensive aggregation on every read', 'Store pre-computed totals; update them on write ($inc)'],
            ['Subset', 'Large documents with rarely used parts', 'Keep the hot subset embedded, the rest in another collection'],
            ['Extended reference', 'Frequent $lookup for a few fields', 'Copy those fields into the referencing document'],
            ['Outlier', 'A few documents much larger than the rest', 'Flag and overflow outliers instead of designing for them'],
            ['Polymorphic', 'Different kinds of entities in one collection', 'Common fields + type-specific fields, with a type field'],
            ['Schema versioning', 'Evolving document shapes', 'A version field; migrate lazily'],
            ['Attribute', 'Many similar optional fields', 'Array of {k, v} pairs with one index'],
        ]),
        tags('Bucket Pattern', 'Computed Pattern', 'Subset Pattern', 'Extended Reference', 'Outlier Pattern', 'Attribute Pattern'),
    ),
    analogy('Design patterns are <strong>standard kitchen layouts</strong>: you do not reinvent where the sink goes for every house. Each pattern is a '
            'proven answer to a recurring problem: storing many small readings, avoiding repeated calculations, keeping documents small.'),
    patterns_anim(),
    real_world(
        scenario('Face-attendance camera data',
                 p('Each camera produces a recognition event every few seconds. The <strong>bucket pattern</strong> stores one document per camera '
                   'per hour with an array of events and a count: 24 documents per camera per day instead of ~20,000, with much smaller indexes. '
                   'MongoDB 5.0+ <strong>time-series collections</strong> apply this bucketing automatically.')),
    ),
    example(
        mql('''
// Computed pattern: keep course statistics up to date on every result
db.course_stats.insertOne({ _id: 'PG-DBDA', students: 0, totalMarks: 0 })
db.course_stats.updateOne({ _id: 'PG-DBDA' }, { $inc: { students: 1, totalMarks: 78 } })
db.course_stats.updateOne({ _id: 'PG-DBDA' }, { $inc: { students: 1, totalMarks: 91 } })
db.course_stats.aggregate([ { $project: { students: 1, avg: { $divide: ['$totalMarks', '$students'] } } } ])

// Bucket pattern: one document per camera per hour
db.camera_events.updateOne(
  { camera: 'KHR-GATE-1', hour: new Date('2026-10-13T09:00:00Z'), count: { $lt: 1000 } },
  { $push: { events: { roll: 2401, t: new Date('2026-10-13T09:02:11Z') } }, $inc: { count: 1 } },
  { upsert: true }
)
db.camera_events.updateOne(
  { camera: 'KHR-GATE-1', hour: new Date('2026-10-13T09:00:00Z'), count: { $lt: 1000 } },
  { $push: { events: { roll: 2402, t: new Date('2026-10-13T09:03:40Z') } }, $inc: { count: 1 } },
  { upsert: true }
)
db.camera_events.find({}, { _id: 0 })
'''),
        mq('''
// MongoDB 5.0+: let the server do the bucketing
db.createCollection('readings', {
  timeseries: { timeField: 't', metaField: 'camera', granularity: 'seconds' },
  expireAfterSeconds: 60 * 60 * 24 * 90      // keep 90 days
})
''', 'Time-series collection'),
        title='Example'),
    steps(
        ('Find the pain point', 'Too many documents? Slow repeated aggregation? Huge documents? Frequent lookups?'),
        ('Match it to a pattern', 'Bucket, computed, subset, extended reference, outlier…'),
        ('Apply to one collection', 'Migrate gradually (schema versioning helps).'),
        ('Measure', 'Document count, size, index size, query latency before/after.'),
        title='Steps to Apply a Pattern'),
    crossq(
        ('What is the trade-off of the computed pattern?', 'Writes do extra work and the computed value can drift if an update path forgets to maintain it; periodic reconciliation jobs are common.'),
        ('When would you use the attribute pattern?', 'Products with many optional specs (RAM, screen, colour…): store <code>specs: [{k: \'ram\', v: 16}, …]</code> and index <code>{\'specs.k\': 1, \'specs.v\': 1}</code> instead of one index per attribute.'),
    ),
]),

# ------------------------------------------------------------------ 26
Q('MongoDB is schemaless. How do you enforce a schema?', 'Schema Validation', minutes=8, cards=[
    definition(
        defbox('MongoDB is <strong>schema-flexible</strong>, not schema-less: you can attach a <strong>validator</strong> to a collection, usually '
               '<code>$jsonSchema</code> (required fields, BSON types, ranges, enums, patterns) or any query expression. Inserts and updates that '
               'violate it fail with "Document failed validation".',
               '<code>validationLevel</code>: <code>strict</code> (all writes) or <code>moderate</code> (only documents that are already valid). '
               '<code>validationAction</code>: <code>error</code> (reject) or <code>warn</code> (log only).'),
        tags('Schema Validation', '$jsonSchema', 'validator', 'validationLevel', 'validationAction', 'collMod'),
    ),
    analogy('A flexible schema is like a notebook with blank pages; a validator is a <strong>stamp at the office door</strong> that checks every '
            'form for required fields before it is filed. You decide how strict the stamp is.'),
    validation_anim(),
    real_world(
        scenario('Protecting exam results',
                 p('After a bug inserted marks as strings and some above 100, the <code>results</code> collection got a validator: '
                   '<code>marks</code> must be an int between 0 and 100, <code>roll</code> and <code>exam</code> are required. Bad writes now fail '
                   'immediately in testing instead of corrupting reports.')),
    ),
    example(
        mql('''
db.createCollection('results', {
  validator: { $jsonSchema: {
    bsonType: 'object',
    required: ['roll', 'exam', 'marks'],
    properties: {
      roll:  { bsonType: 'int', minimum: 2400 },
      exam:  { bsonType: 'string', enum: ['SQL', 'Spark', 'Python'] },
      marks: { bsonType: 'int', minimum: 0, maximum: 100 }
    }
  } }
})
db.results.insertOne({ roll: 2401, exam: 'SQL', marks: 82 })
db.results.insertOne({ roll: 2402, exam: 'SQL', marks: 120 })
db.results.insertOne({ roll: 2403, exam: 'Hadoop', marks: 70 })
db.results.insertOne({ roll: 2404, marks: 66 })
db.results.updateOne({ roll: 2401 }, { $set: { marks: -5 } })
db.results.countDocuments()

// find existing documents that would violate a schema (useful before enabling it)
db.results.find({ $nor: [ { $jsonSchema: { required: ['roll', 'exam', 'marks'] } } ] }).count()
'''),
        mq('''
// add or change validation on an existing collection
db.runCommand({
  collMod: 'students',
  validator: { $jsonSchema: { required: ['name', 'course'] } },
  validationLevel: 'moderate',      // do not block updates to old invalid docs
  validationAction: 'warn'          // log only while cleaning data
})
''', 'collMod on an existing collection'),
        title='Example'),
    steps(
        ('Write the schema', 'Required fields, types, ranges, enums.'),
        ('Check existing data', 'Find violators with <code>$nor: [{$jsonSchema: ...}]</code>.'),
        ('Start with warn + moderate', 'Observe logs without breaking the application.'),
        ('Fix data, then switch to error + strict', 'Via <code>collMod</code>.'),
        ('Keep application-side validation too', 'For friendly error messages.'),
        title='Steps to Introduce Validation'),
    crossq(
        ('Does validation slow down writes?', 'Slightly: every insert/update is checked. The cost is small compared with cleaning corrupt data later.'),
        ('Can validation enforce uniqueness or references?', 'No. Uniqueness needs a unique index; referential integrity must be handled by the application or transactions.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What is the 16 MB document limit? How do you store large files (GridFS)?', '16 MB Limit & GridFS', minutes=6, cards=[
    definition(
        defbox('A BSON document can be at most <strong>16 MB</strong> (it also limits nesting to 100 levels). The limit stops a single document from '
               'using excessive RAM or bandwidth and pushes designs away from unbounded growth.',
               '<strong>GridFS</strong> stores larger files by splitting them into 255 KB chunks in <code>fs.chunks</code>, with metadata in '
               '<code>fs.files</code>. Drivers provide upload/download streams.'),
        tags('16 MB', 'GridFS', 'fs.files', 'fs.chunks', 'Large Files', 'Object Storage'),
    ),
    analogy('An envelope can carry only so many pages. For a <strong>thick thesis</strong> you post it in numbered envelopes plus a cover letter '
            'listing them (GridFS), or you upload it to a cloud drive and post only the link (object storage).'),
    gridfs_anim(),
    real_world(
        scenario('Scanned answer sheets',
                 p('Each scanned answer sheet PDF is 5–40 MB. They are uploaded to object storage (S3/MinIO) and the attempt document stores '
                   'the URL, checksum and page count. GridFS was considered but object storage was cheaper and served files via CDN directly.')),
    ),
    example(
        sh('''
# Upload / list / download with the mongofiles tool
mongofiles --db cdac put answer_sheet_2401.pdf
mongofiles --db cdac list
mongofiles --db cdac get answer_sheet_2401.pdf
''', 'mongofiles'),
        js('''
import gridfs
from pymongo import MongoClient

db = MongoClient()["cdac"]
fs = gridfs.GridFS(db)
with open("answer_sheet_2401.pdf", "rb") as f:
    file_id = fs.put(f, filename="answer_sheet_2401.pdf", roll=2401)
data = fs.get(file_id).read()
''', 'Python (PyMongo GridFS)'),
        title='Example'),
    steps(
        ('Estimate file sizes', 'Below a few MB and few in number? A BinData field may be fine.'),
        ('Larger files → GridFS or object storage', 'Object storage is usually cheaper and CDN-friendly.'),
        ('Store metadata in MongoDB', 'Owner, size, checksum, URL or GridFS id.'),
        ('Index metadata', 'e.g. <code>fs.files</code> on <code>metadata.roll</code>.'),
        title='Steps to Store Large Files'),
    crossq(
        ('Your document is approaching 16 MB. What do you do?', 'Re-model: move unbounded arrays to a child collection, use the subset/bucket pattern, or move binary data out. Raising the limit is not possible.'),
    ),
]),
])
