from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

SECTION = dict(level='basic', title='MongoDB Basics', questions=[

# ------------------------------------------------------------------ 6
Q('What is MongoDB? Explain its architecture and main components.', 'MongoDB Architecture', minutes=8, cards=[
    definition(
        defbox('<strong>MongoDB</strong> is an open-source (SSPL licence), document-oriented NoSQL database that stores data as '
               '<strong>BSON documents</strong> in <strong>collections</strong>. It provides rich queries, secondary indexes, an aggregation '
               'framework, replication (replica sets) and horizontal scaling (sharding). MongoDB Atlas is its managed cloud service.'),
        table(['Component', 'Role'], [
            ['<code>mongod</code>', 'The database server process: stores data (WiredTiger engine), executes queries, maintains indexes'],
            ['<code>mongosh</code>', 'Interactive JavaScript shell for administration and queries (replaced the old <code>mongo</code> shell)'],
            ['Drivers', 'Official libraries: PyMongo, Node.js, Java, C#, Go… used by applications'],
            ['Replica set', 'A primary + secondaries with the same data, for high availability'],
            ['<code>mongos</code> + config servers', 'Router and metadata servers of a sharded cluster'],
            ['Tools', 'Compass (GUI), mongodump/mongorestore (backup), mongoimport/mongoexport (CSV/JSON)'],
        ]),
        tags('MongoDB', 'mongod', 'mongosh', 'WiredTiger', 'Replica Set', 'mongos', 'Atlas'),
    ),
    analogy('MongoDB is like a <strong>library system</strong>: <code>mongod</code> is the library building that holds the books, <code>mongosh</code> '
            'and Compass are the librarian\'s desk, drivers are the online catalogue apps that patrons use, a replica set is a set of identical '
            'branch libraries that can take over if one closes, and sharding splits a huge collection across several buildings by book number.'),
    mongo_arch(),
    real_world(
        scenario('Typical deployments',
                 ul('Development: one local <code>mongod</code> or a free Atlas cluster.',
                    'Production: a 3-member replica set (primary + 2 secondaries) across availability zones.',
                    'Very large scale: a sharded cluster, each shard a replica set, with mongos routers next to the application servers.')),
    ),
    example(
        sh('''
# Start a server (data directory + port) and connect
mongod --dbpath /data/db --port 27017
mongosh "mongodb://localhost:27017"

# Atlas / replica set connection string
mongosh "mongodb+srv://cluster0.abcde.mongodb.net/cdac" --username vineeta
''', 'Starting and connecting'),
        js('''
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["cdac"]
db.students.insert_one({"_id": 2401, "name": "Anuj", "course": "PG-DBDA"})
for s in db.students.find({"course": "PG-DBDA"}, {"name": 1}):
    print(s)
''', 'Python (PyMongo)'),
        title='Example'),
    steps(
        ('Install', 'MongoDB Community Server + mongosh (or create a free Atlas cluster).'),
        ('Start mongod', 'With a data directory; as a service in production.'),
        ('Connect', '<code>mongosh</code> locally or with the Atlas connection string.'),
        ('Create users', '<code>db.createUser({...})</code> and enable authentication (<code>security.authorization: enabled</code>).'),
        ('Connect your application', 'Use the official driver with a connection string from configuration, not hard-coded.'),
        title='Steps to Get MongoDB Running'),
    crossq(
        ('What is WiredTiger?', 'MongoDB\'s default storage engine since 3.2: document-level concurrency control, compression (snappy/zstd/zlib), checkpoints plus a write-ahead journal for durability.'),
        ('What is the default port?', '27017 for mongod/mongos; config servers commonly use 27019 and shards 27018 in docs examples.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('What are databases, collections and documents in MongoDB?', 'Database, Collection, Document', minutes=6, cards=[
    definition(
        defbox('A <strong>document</strong> is a single record: an ordered set of field–value pairs (values can be strings, numbers, dates, '
               'arrays or nested documents), with a unique <code>_id</code>. A <strong>collection</strong> is a group of documents, usually of the '
               'same kind; it has no enforced schema by default. A <strong>database</strong> is a namespace that holds collections, each with its own files and permissions.',
               'Databases and collections are created <strong>implicitly</strong> the first time you insert into them.'),
        tags('Database', 'Collection', 'Document', 'Field', 'Namespace', 'Capped Collection'),
    ),
    analogy('A database is a <strong>filing cabinet</strong>, a collection is a <strong>drawer</strong> labelled "students", and each document '
            'is a <strong>file folder</strong> for one student. Folders in the same drawer can contain different papers.'),
    db_coll_doc(),
    real_world(
        scenario('Naming in the C-DAC platform',
                 p('Database <code>cdac_lms</code>; collections <code>students</code>, <code>courses</code>, <code>exams</code>, '
                   '<code>attempts</code>, <code>attendance</code>. Each collection gets its own indexes and validation rules.')),
    ),
    example(
        mql('''
use cdac
db.courses.insertOne({ _id: 'PG-DBDA', months: 6, modules: ['Python', 'SQL', 'Big Data'] })
db.students.insertOne({ _id: 2401, name: 'Anuj', course: 'PG-DBDA' })
show collections
db.getName()
db.students.countDocuments()
db.courses.drop()
show collections
'''),
        title='Example'),
    steps(
        ('Switch to (or create) a database', '<code>use cdac</code> (created on first write).'),
        ('Create a collection', 'Implicitly by inserting, or explicitly with <code>db.createCollection(\'students\', {validator: ...})</code> for options.'),
        ('Insert documents', '<code>insertOne</code> / <code>insertMany</code>.'),
        ('Inspect', '<code>show collections</code>, <code>db.students.countDocuments()</code>, <code>db.stats()</code>.'),
        title='Steps to Create a Collection'),
    crossq(
        ('What is a capped collection?', 'A fixed-size collection that keeps documents in insertion order and overwrites the oldest when full, like a ring buffer (logs). Created with <code>createCollection(name, {capped: true, size: bytes})</code>.'),
        ('Are field names case-sensitive?', 'Yes, and so are collection names and string values in queries.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What is BSON? How is it different from JSON? What data types does MongoDB support?', 'BSON & Data Types', minutes=8, cards=[
    definition(
        defbox('<strong>BSON (Binary JSON)</strong> is the binary format MongoDB uses to store documents and send them over the network. It '
               'keeps JSON\'s structure but is <strong>typed</strong>, <strong>length-prefixed</strong> (fast to traverse) and supports more types.'),
        table(['BSON type', 'mongosh example', 'Notes'], [
            ['String', "'Anuj'", 'UTF-8'],
            ['Int32 / Int64 / Double', '78, NumberLong(…), 78.5', 'mongosh numbers are doubles unless written as integers'],
            ['Decimal128', "NumberDecimal('45000.50')", 'Exact decimal: use for money'],
            ['Date', "new Date('2026-10-13')", 'Milliseconds since epoch, UTC'],
            ['ObjectId', 'ObjectId()', '12-byte unique id'],
            ['Boolean, Null', 'true, null', ''],
            ['Array, Object', "['sql'], { city: 'Pune' }", 'Nested documents and lists'],
            ['Binary, Regex, Timestamp', '…', 'Files, patterns, internal oplog timestamps'],
        ]),
        tags('BSON', 'JSON', 'Data Types', 'Decimal128', 'Date', 'ObjectId', '16 MB'),
    ),
    analogy('JSON is a <strong>handwritten letter</strong>: readable, but the reader must interpret every word. BSON is a <strong>printed form '
            'with labelled boxes</strong> and the length of each box written on top, so the clerk can jump straight to the box they need.'),
    bson_anim(),
    real_world(
        scenario('A real bug from storing dates as strings',
                 p('Exam start times were stored as strings like "13/10/2026 09:00". Sorting and range queries ("exams this week") gave wrong '
                   'results because strings compare alphabetically. Converting them to BSON <code>Date</code> made range queries correct and indexable.')),
    ),
    example(
        mql('''
db.payments.insertOne({
  _id: 'R-1001', roll: 2401,
  amount: NumberDecimal('45000.50'),
  paidOn: new Date('2026-10-13T09:30:00Z'),
  verified: true, remarks: null
})
db.payments.findOne()

// Query by type: find documents where amount is stored as a string by mistake
db.payments.insertOne({ _id: 'R-1002', roll: 2402, amount: '45000' })
db.payments.find({ amount: { $type: 'string' } })
'''),
        title='Example'),
    steps(
        ('Pick precise types', 'Dates as Date, money as Decimal128, ids as ObjectId or a natural key.'),
        ('Validate types', 'Use <code>$jsonSchema</code> with <code>bsonType</code> to reject wrong types.'),
        ('Find inconsistencies', '<code>{field: {$type: \'string\'}}</code> to locate mistyped values.'),
        ('Fix with an update pipeline', '<code>updateMany({...}, [{$set: {amount: {$toDecimal: \'$amount\'}}}])</code>.'),
        title='Steps to Keep Types Clean'),
    crossq(
        ('What is the maximum document size?', '16 MB. Larger binary data goes to GridFS or object storage.'),
        ('Why is JSON not enough for a database?', 'JSON has no date, binary, integer vs double distinction or decimal type, and is slow to scan because it is text without length prefixes.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What is _id and ObjectId? Can you use your own _id?', '_id & ObjectId', minutes=7, cards=[
    definition(
        defbox('Every document must have a unique <code>_id</code> field, which acts as its <strong>primary key</strong> and is automatically '
               'indexed (unique index <code>_id_</code>). If you do not supply one, the driver generates an <strong>ObjectId</strong>: a 12-byte '
               'value made of a 4-byte timestamp, a 5-byte random value and a 3-byte counter.',
               'You may use any unique, immutable value as <code>_id</code>: a roll number, an email, a composite object.'),
        tags('_id', 'ObjectId', 'Primary Key', 'Unique Index', 'Natural Key'),
    ),
    analogy('An ObjectId is like a <strong>railway ticket PNR</strong>: generated at the counter without asking a central office, it encodes '
            'when it was issued, and no two tickets share it.'),
    objectid_anim(),
    real_world(
        scenario('Natural vs generated keys',
                 ul('<code>students</code>: <code>_id: 2401</code> (roll number) is natural, short and always known, so lookups need no extra index.',
                    '<code>attendance</code> events: ObjectId, since there is no natural unique key and inserts come from many devices.',
                    'Never use a value that can change (e.g. phone number) as <code>_id</code>: it is immutable.')),
    ),
    example(
        mql('''
db.logins.insertOne({ roll: 2401, at: new Date('2026-10-13T09:00:00Z') })
db.logins.findOne()
db.logins.findOne()._id.getTimestamp()     // the creation time is inside the ObjectId

// Natural key as _id
db.students.insertOne({ _id: 2401, name: 'Anuj' })
db.students.insertOne({ _id: 2401, name: 'Someone else' })

// _id cannot be changed once set
db.students.updateOne({ _id: 2401 }, { $set: { _id: 2499 } })
db.students.getIndexes()
'''),
        title='Example'),
    steps(
        ('Decide the key', 'Is there a natural, unique, immutable identifier? Use it. Otherwise let the driver generate an ObjectId.'),
        ('Insert', 'Provide <code>_id</code> explicitly or omit it.'),
        ('Handle duplicates', 'Catch error code 11000 (duplicate key) in the application.'),
        title='Steps to Choose an _id'),
    crossq(
        ('Can two documents in different collections have the same _id?', 'Yes. Uniqueness is per collection.'),
        ('Is ObjectId a good shard key?', 'Not as a ranged key: it increases over time, so all inserts go to one shard. Use hashed _id or a different key.'),
        ('Can _id be an array?', 'No. It can be any type except an array (and regex).'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How do you insert documents? What is the difference between ordered and unordered inserts?', 'Insert Operations', minutes=7, cards=[
    definition(
        defbox('<code>insertOne(doc)</code> inserts one document; <code>insertMany([docs], {ordered})</code> inserts a batch. With '
               '<code>ordered: true</code> (default) the server stops at the first error; with <code>ordered: false</code> it continues with the '
               'remaining documents and reports all errors. Each document insert is atomic; the batch is not a transaction.'),
        tags('insertOne', 'insertMany', 'ordered', 'bulkWrite', 'Duplicate Key'),
    ),
    analogy('Posting a stack of letters: <strong>ordered</strong> is a clerk who stops at the first letter with a wrong address and returns the '
            'rest unposted; <strong>unordered</strong> is a clerk who posts all good letters and gives you back only the faulty ones.'),
    insert_anim(),
    real_world(
        scenario('Bulk loading exam registrations',
                 p('A CSV of 25,000 registrations is loaded with <code>insertMany(..., {ordered: false})</code> in batches of 1,000. Duplicate '
                   'registrations (same roll number) fail individually and are logged, while all valid rows are inserted in one pass.')),
    ),
    example(
        mql('''
db.students.insertOne({ _id: 2401, name: 'Anuj' })

// ordered (default): stops at the duplicate, 2405 is never inserted
db.students.insertMany([ { _id: 2402, name: 'Vineeta' }, { _id: 2401, name: 'dup' }, { _id: 2405, name: 'Meera' } ])
db.students.find({}, { name: 1 })
'''),
        mq('''
// ordered: false → 2402 and 2405 inserted, the duplicate reported
db.students.insertMany(
  [ { _id: 2402, name: 'Vineeta' }, { _id: 2401, name: 'dup' }, { _id: 2405, name: 'Meera' } ],
  { ordered: false }
)
// MongoBulkWriteError: E11000 duplicate key error ... writeErrors: [ { index: 1, code: 11000 } ], insertedCount: 2

// mixed operations in one round trip
db.students.bulkWrite([
  { insertOne: { document: { _id: 2406, name: 'Kabir' } } },
  { updateOne: { filter: { _id: 2402 }, update: { $set: { course: 'PG-DBDA' } } } },
  { deleteOne: { filter: { _id: 2405 } } }
])
''', 'Unordered inserts and bulkWrite (real server error format)'),
        title='Example'),
    steps(
        ('Prepare documents', 'Clean types; set <code>_id</code> if you have a natural key.'),
        ('Batch them', '500–1,000 documents per <code>insertMany</code> for bulk loads.'),
        ('Choose ordered or unordered', 'Unordered for independent records (faster, continues on errors).'),
        ('Handle errors', 'Inspect <code>writeErrors</code> and log/retry failed documents.'),
        ('For files', '<code>mongoimport --type csv --headerline --db cdac --collection students --file students.csv</code>.'),
        title='Steps for a Bulk Load'),
    crossq(
        ('Does a failed insertMany roll back the documents already inserted?', 'No. Documents inserted before the error stay. Use a transaction if the batch must be all-or-nothing.'),
        ('insert() vs insertOne()?', 'The old <code>insert()</code> is deprecated; use <code>insertOne</code>/<code>insertMany</code>, which return clear result objects.'),
    ),
]),
])
