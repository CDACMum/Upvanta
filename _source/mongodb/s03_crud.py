from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

SECTION = dict(level='intermediate', title='CRUD & Querying', questions=[

# ------------------------------------------------------------------ 11
Q('How do you query documents with find()? Explain comparison and logical operators.', 'find() & Query Operators', minutes=9, cards=[
    definition(
        defbox('<code>db.collection.find(filter, projection)</code> returns a <strong>cursor</strong> over the documents matching the '
               '<strong>filter document</strong>. <code>findOne()</code> returns the first match or <code>null</code>. Conditions on several fields '
               'are combined with an implicit AND.'),
        table(['Category', 'Operators', 'Example'], [
            ['Comparison', '<code>$eq $ne $gt $gte $lt $lte $in $nin</code>', '<code>{ marks: { $gte: 60, $lt: 80 } }</code>'],
            ['Logical', '<code>$and $or $not $nor</code>', '<code>{ $or: [ { course: \'PG-DAC\' }, { marks: { $gt: 85 } } ] }</code>'],
            ['Element', '<code>$exists $type</code>', '<code>{ email: { $exists: false } }</code>'],
            ['Evaluation', '<code>$regex $expr $mod $text</code>', '<code>{ name: { $regex: \'^A\' } }</code>'],
            ['Array', '<code>$all $elemMatch $size</code>', '<code>{ skills: { $all: [\'sql\', \'python\'] } }</code>'],
        ]),
        tags('find', 'findOne', 'Filter', '$gt', '$in', '$or', '$exists', '$regex', '$expr'),
    ),
    analogy('A filter document is a <strong>wanted poster</strong>: "course: PG-DBDA, marks above 80". The guard (MongoDB) checks each '
            'document against every line on the poster and lets through only those that match all of them.'),
    find_anim(),
    real_world(
        scenario('Placement eligibility list',
                 p('A company visiting campus needs PG-DBDA or PG-DAI students with at least 75 marks and SQL skills: '
                   '<code>{course: {$in: [...]}, marks: {$gte: 75}, skills: \'sql\'}</code>. The placement cell runs it from Compass '
                   'and exports the result to CSV.')),
    ),
    example(
        mql('''
db.students.find({ course: 'PG-DBDA', marks: { $gt: 80 } }, { name: 1, marks: 1 })

db.students.find({ marks: { $gte: 60, $lt: 75 } }, { name: 1, marks: 1 })

db.students.find({ course: { $in: ['PG-DBDA', 'PG-DAI'] }, skills: 'sql', marks: { $gte: 75 } }, { name: 1, course: 1 })

db.students.find({ $or: [ { centre: 'Juhu', marks: { $lt: 60 } }, { skills: { $size: 0 } } ] }, { name: 1, centre: 1, marks: 1 })

db.students.find({ name: { $regex: '^A' } }, { _id: 0, name: 1 })

// $expr compares two fields of the same document
db.students.find({ $expr: { $gt: ['$marks', 85] } }, { _id: 0, name: 1, marks: 1 })
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Write the filter as a document', 'One key per field; operators as nested documents.'),
        ('Add a projection', 'Return only the fields you need.'),
        ('Run and check the count', '<code>db.students.countDocuments(filter)</code>.'),
        ('Index the filtered fields', 'Equality fields first (see the ESR rule) and verify with <code>explain()</code>.'),
        title='Steps to Write a Query'),
    crossq(
        ('<code>{marks: {$gt: 60}, marks: {$lt: 80}}</code>: what is wrong?', 'A JavaScript object cannot have the same key twice; the second replaces the first, so only <code>$lt: 80</code> applies. Combine them: <code>{marks: {$gt: 60, $lt: 80}}</code>.'),
        ('$in vs $or?', 'For several values of the same field, <code>$in</code> is simpler and usually faster. <code>$or</code> is for conditions on different fields.'),
        ('Does a regex query use an index?', 'Only a case-sensitive prefix regex (<code>/^An/</code>) can use an index efficiently; others scan all index keys or documents.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How do projection, sort, skip and limit work? How do you paginate?', 'Projection, Sort & Pagination', minutes=8, cards=[
    definition(
        defbox('<strong>Projection</strong> (second argument of <code>find</code>) chooses returned fields: <code>1</code> to include, '
               '<code>0</code> to exclude (do not mix, except <code>_id: 0</code>). Cursor methods: <code>sort({f: 1 | -1})</code>, '
               '<code>skip(n)</code>, <code>limit(n)</code>. The server always applies them in the order sort → skip → limit.'),
        tags('Projection', 'sort', 'skip', 'limit', 'Pagination', 'Cursor', 'Keyset Pagination'),
    ),
    analogy('A <strong>merit list on a notice board</strong>: sort students by marks (sort), the first page shows ranks 1–10 (limit 10), the '
            'second page skips the first 10 (skip 10). Projection is printing only name and marks instead of the whole admission form.'),
    pagination_anim(),
    real_world(
        scenario('Paging through 50,000 attempts',
                 p('The admin portal lists exam attempts 20 per page. Pages near the start use <code>skip/limit</code>; for "load more" in the '
                   'mobile app, the API sends the last seen <code>(score, _id)</code> and queries <code>{score: {$lt: last}}</code>, which stays fast at any depth.')),
    ),
    example(
        mql('''
// projection: include fields, hide _id
db.students.find({}, { _id: 0, name: 1, marks: 1 }).sort({ marks: -1 }).limit(3)

// page 2 of size 3
db.students.find({}, { _id: 0, name: 1, marks: 1 }).sort({ marks: -1, _id: 1 }).skip(3).limit(3)

// exclusion projection: everything except address and scores
db.students.findOne({ _id: 2402 }, { address: 0, scores: 0 })

// keyset pagination: continue after the last item of page 1 (Aarshvi, 84)
db.students.find({ marks: { $lt: 84 } }, { _id: 0, name: 1, marks: 1 }).sort({ marks: -1 }).limit(3)
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Fix a deterministic sort', 'Sort on the business field plus a unique tie-breaker such as <code>_id</code>.'),
        ('First page', '<code>.sort(...).limit(size)</code>.'),
        ('Next pages', 'Small apps: <code>skip((page-1)*size)</code>. Large data: filter on the last seen sort values (keyset).'),
        ('Index the sort fields', 'So the server reads rows already in order instead of sorting in memory.'),
        title='Steps to Implement Pagination'),
    crossq(
        ('Why can results "jump" between pages?', 'Without a unique tie-breaker, documents with equal sort values have no fixed order, so they can appear on two pages or none.'),
        ('Can you mix inclusion and exclusion in a projection?', 'No, except for <code>_id</code>, which may be excluded from an inclusion projection.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('How do you query arrays and embedded documents? When do you need $elemMatch?', 'Arrays, Dot Notation & $elemMatch', minutes=9, cards=[
    definition(
        defbox('<strong>Arrays</strong>: <code>{skills: \'sql\'}</code> matches if <em>any</em> element equals \'sql\'; <code>$all</code> requires all '
               'listed values; <code>$size</code> matches an exact length; <code>{\'skills.0\': \'sql\'}</code> checks a position.',
               '<strong>Embedded documents</strong>: use <strong>dot notation</strong>, <code>{\'address.city\': \'Pune\'}</code>.',
               '<strong>Arrays of documents</strong>: separate conditions on <code>\'scores.sub\'</code> and <code>\'scores.m\'</code> may be satisfied '
               'by different elements; <code>$elemMatch</code> forces one element to satisfy all of them.'),
        tags('Dot Notation', '$elemMatch', '$all', '$size', 'Arrays', 'Embedded Documents'),
    ),
    analogy('Asking a class "has anyone scored above 80 in <strong>Spark</strong>?" Without $elemMatch it is like asking "is there a Spark '
            'marksheet <em>and</em> some marksheet above 80?", so a student with Spark 61 and SQL 82 says yes. $elemMatch asks about the '
            '<strong>same marksheet</strong>.'),
    array_query_anim(),
    real_world(
        scenario('Scholarship eligibility',
                 p('"Students with at least 80 in Spark" must use <code>$elemMatch</code> on the scores array. A version using two separate '
                   'dot-notation conditions wrongly included Anuj (Spark 61, SQL 82) until it was fixed.')),
    ),
    example(
        mql('''
db.students.find({ skills: 'python' }, { _id: 0, name: 1, skills: 1 })
db.students.find({ skills: { $all: ['python', 'sql'] } }, { _id: 0, name: 1 })
db.students.find({ skills: { $size: 0 } }, { _id: 0, name: 1 })
db.students.find({ 'address.city': 'Pune' }, { _id: 0, name: 1, 'address.city': 1 })

// WRONG: conditions satisfied by different array elements
db.students.find({ 'scores.sub': 'Spark', 'scores.m': { $gte: 80 } }, { _id: 0, name: 1, scores: 1 })

// RIGHT: both conditions on the same element
db.students.find({ scores: { $elemMatch: { sub: 'Spark', m: { $gte: 80 } } } }, { _id: 0, name: 1, scores: 1 })
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Single condition on array values', 'Plain equality or operator: <code>{skills: \'sql\'}</code>.'),
        ('Several conditions on one array element', 'Wrap them in <code>$elemMatch</code>.'),
        ('Nested fields', 'Dot notation in quotes: <code>\'address.city\'</code>.'),
        ('Index', 'Indexes on array fields become multikey indexes automatically.'),
        title='Steps'),
    crossq(
        ('Does <code>{address: {city: \'Pune\'}}</code> equal <code>{\'address.city\': \'Pune\'}</code>?', 'No. The first is an exact match on the whole embedded document (same fields, same order); it fails if address also has a pin. Use dot notation to match one field.'),
        ('How do you return only the matching array element?', 'Projection with <code>$elemMatch</code> or the positional <code>$</code> (<code>{\'scores.$\': 1}</code>), or <code>$filter</code> in an aggregation.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do you update documents? Explain the update operators and upsert.', 'Update Operators & Upsert', minutes=9, cards=[
    definition(
        defbox('<code>updateOne(filter, update, options)</code> and <code>updateMany(...)</code> modify matching documents with '
               '<strong>update operators</strong>; <code>replaceOne</code> replaces the whole document (except <code>_id</code>). '
               'With <code>{upsert: true}</code>, if nothing matches, a new document is created from the filter\'s equality fields plus the update.'),
        table(['Operator', 'Effect'], [
            ['<code>$set</code> / <code>$unset</code>', 'Set a field (creating it) / remove a field'],
            ['<code>$inc</code> / <code>$mul</code>', 'Add to / multiply a number atomically'],
            ['<code>$min</code> / <code>$max</code>', 'Update only if the new value is lower / higher'],
            ['<code>$rename</code>', 'Rename a field'],
            ['<code>$push</code> / <code>$addToSet</code>', 'Append to array / append if not present (with <code>$each</code>, <code>$slice</code>, <code>$sort</code>)'],
            ['<code>$pull</code> / <code>$pop</code>', 'Remove matching elements / first or last element'],
            ['<code>$setOnInsert</code>', 'Set only when an upsert inserts'],
            ['<code>$currentDate</code>', 'Set a field to the current date'],
        ]),
        tags('updateOne', 'updateMany', '$set', '$inc', '$push', '$addToSet', 'upsert', '$setOnInsert'),
    ),
    analogy('Update operators are <strong>correction instructions</strong> on a form ("change marks to 82", "add 1 to attempts", "add Spark to '
            'skills") rather than filling a brand-new form. Upsert is "<strong>update this student\'s record, or open a new file if none exists</strong>".'),
    update_ops_anim(),
    real_world(
        scenario('Daily login counter per student',
                 p('Every login runs <code>updateOne({roll, day}, {$inc: {count: 1}, $setOnInsert: {first: now}}, {upsert: true})</code>. '
                   'The first login of the day creates the document, later ones increment it, all in one atomic statement without a prior read.')),
    ),
    example(
        mql('''
db.students.updateOne({ _id: 2401 }, { $set: { marks: 82 }, $inc: { attempts: 1 }, $push: { skills: 'kafka' } })
db.students.updateOne({ _id: 2401 }, { $addToSet: { skills: 'sql' } })          // already present: no change
db.students.findOne({ _id: 2401 }, { marks: 1, attempts: 1, skills: 1 })

// 5 grace marks for everyone below 70
db.students.updateMany({ marks: { $lt: 70 } }, { $inc: { marks: 5 } })
db.students.find({}, { _id: 0, name: 1, marks: 1 })

// upsert: no document for 2410 → one is created
db.students.updateOne(
  { _id: 2410 },
  { $set: { name: 'Isha', course: 'PG-DBDA' }, $setOnInsert: { createdBy: 'import' } },
  { upsert: true }
)
db.students.findOne({ _id: 2410 })
''', setup=SMALL),
        title='Example'),
    steps(
        ('Write the filter', 'As specific as possible (by <code>_id</code> when you can).'),
        ('Choose operators', '<code>$set</code> for values, <code>$inc</code> for counters, array operators for lists.'),
        ('Decide One vs Many', '<code>updateOne</code> changes the first match only.'),
        ('Add upsert if needed', 'With <code>$setOnInsert</code> for creation-only fields.'),
        ('Check the result', '<code>matchedCount</code> vs <code>modifiedCount</code> tells you whether anything changed.'),
        title='Steps for a Safe Update'),
    crossq(
        ('What happens with <code>updateOne({_id: 1}, {name: \'X\'})</code>?', 'It is rejected: update documents must contain only operators. To replace the whole document use <code>replaceOne</code>.'),
        ('matchedCount 1 but modifiedCount 0: why?', 'The document matched but the update set the same values it already had (e.g. <code>$addToSet</code> of an existing value).'),
        ('Why is $inc better than reading, adding and writing back?', 'Two concurrent read-modify-write cycles lose one update; $inc is applied atomically on the server.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you update a specific element inside an array? Explain $, $[] and $[identifier].', 'Positional Array Updates', minutes=8, cards=[
    definition(
        table(['Operator', 'Updates', 'Example'], [
            ['<code>$</code>', 'The <strong>first</strong> element that matched the query filter', '<code>{\'scores.sub\': \'Spark\'}, {$set: {\'scores.$.m\': 75}}</code>'],
            ['<code>$[]</code>', '<strong>All</strong> elements', '<code>{$inc: {\'scores.$[].m\': 5}}</code>'],
            ['<code>$[id]</code> + <code>arrayFilters</code>', 'All elements matching a condition', '<code>{$set: {\'scores.$[s].pass\': false}}, {arrayFilters: [{\'s.m\': {$lt: 60}}]}</code>'],
        ]),
        tags('Positional Operator', '$', '$[]', 'arrayFilters', 'Array Update'),
    ),
    analogy('A marksheet with several rows. <code>$</code> = "correct the row I pointed at", <code>$[]</code> = "add grace marks to every row", '
            '<code>$[low]</code> = "mark every row below 60 as failed".'),
    positional_anim(),
    real_world(
        scenario('Re-evaluation of one subject',
                 p('After re-evaluation, only the Spark score of student 2401 changes. <code>updateOne({_id: 2401, \'scores.sub\': \'Spark\'}, '
                   '{$set: {\'scores.$.m\': 75}})</code> updates that element without rewriting the array from the application.')),
    ),
    example(
        mql('''
db.students.updateOne({ _id: 2401, 'scores.sub': 'Spark' }, { $set: { 'scores.$.m': 75 } })
db.students.findOne({ _id: 2401 }, { scores: 1 })

db.students.updateOne({ _id: 2401 }, { $inc: { 'scores.$[].m': 5 } })
db.students.findOne({ _id: 2401 }, { scores: 1 })

db.students.updateMany(
  {},
  { $set: { 'scores.$[low].remedial': true } },
  { arrayFilters: [ { 'low.m': { $lt: 60 } } ] }
)
db.students.find({ 'scores.remedial': true }, { _id: 0, name: 1, scores: 1 })
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Identify the element', 'By a field inside it (subject), not by index position.'),
        ('One known element', 'Put the condition in the filter and use <code>$</code>.'),
        ('All elements', '<code>$[]</code>.'),
        ('Some elements', '<code>$[name]</code> plus <code>arrayFilters</code>.'),
        title='Steps'),
    crossq(
        ('Why not update by index, e.g. <code>scores.1.m</code>?', 'Indexes shift when elements are added or removed concurrently; matching by content is safer.'),
        ('Can $ be used with upsert?', 'Not to insert into an array of a new document; the positional operator needs an existing matched element.'),
    ),
]),

# ------------------------------------------------------------------ 16
Q('How do delete, replace and findOneAndUpdate work? How do you build an atomic counter?', 'Delete, Replace & findOneAndUpdate', minutes=8, cards=[
    definition(
        table(['Method', 'Does', 'Returns'], [
            ['<code>deleteOne / deleteMany</code>', 'Removes the first / all matches', '<code>{acknowledged, deletedCount}</code>'],
            ['<code>replaceOne</code>', 'Replaces the whole document (keeps _id)', 'Update result'],
            ['<code>findOneAndUpdate</code>', 'Finds, updates and <strong>returns</strong> the document atomically', 'The document before (default) or after (<code>returnDocument: \'after\'</code>)'],
            ['<code>findOneAndDelete</code>', 'Removes and returns the document', 'The removed document'],
        ]),
        tags('deleteOne', 'deleteMany', 'replaceOne', 'findOneAndUpdate', 'Atomic Counter', 'Soft Delete'),
    ),
    analogy('<code>findOneAndUpdate</code> is a <strong>token machine</strong> at a bank: pressing the button both gives you a number and advances '
            'the counter in one movement, so two customers never get the same token.'),
    find_modify_anim(),
    real_world(
        scenario('Soft delete instead of delete',
                 p('Students who withdraw are not deleted (fee records reference them). The app sets <code>{status: \'withdrawn\', '
                   'withdrawnAt: now}</code>, and queries use a partial index on active students. Only GDPR-style requests trigger a real delete.')),
    ),
    example(
        mql('''
db.counters.insertOne({ _id: 'roll', seq: 2410 })

// atomic counter: two calls, two different numbers
db.counters.findOneAndUpdate({ _id: 'roll' }, { $inc: { seq: 1 } }, { returnDocument: 'after' })
db.counters.findOneAndUpdate({ _id: 'roll' }, { $inc: { seq: 1 } }, { returnDocument: 'after' })

db.students.deleteMany({ marks: { $lt: 70 } })
db.students.replaceOne({ _id: 2401 }, { name: 'Anuj Kumar', course: 'PG-DBDA', marks: 80 })
db.students.find()
''', setup=SMALL),
        title='Example'),
    steps(
        ('Counters', 'Create one document per sequence; use <code>findOneAndUpdate</code> with <code>$inc</code> and <code>returnDocument: \'after\'</code>.'),
        ('Deletes', 'Run the same filter with <code>find()</code>/<code>countDocuments()</code> first; then delete.'),
        ('Prefer soft delete', 'A status field keeps history and references intact.'),
        ('Bulk cleanup of old data', 'Use a TTL index instead of periodic deleteMany jobs.'),
        title='Steps'),
    crossq(
        ('<code>deleteMany({})</code> vs <code>drop()</code>?', 'deleteMany removes documents one by one but keeps the collection, indexes and validation; drop removes everything at once and is much faster for wiping a collection.'),
        ('Is an auto-increment id needed in MongoDB?', 'Usually not; ObjectId is unique without coordination. Use a counter only when humans need sequential numbers (receipt numbers, roll numbers).'),
    ),
]),
])
