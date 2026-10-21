from build import *
from mongodb.anims import *
from mongodb.runner import mql, mq, sh, js
from mongodb.data import STUDENTS, SMALL

MARKS = """
db.marks.insertMany([
  { roll: 2401, sub: 'SQL', m: 82 }, { roll: 2401, sub: 'Spark', m: 77 },
  { roll: 2402, sub: 'SQL', m: 91 }, { roll: 2403, sub: 'Java', m: 84 }, { roll: 2405, sub: 'SQL', m: 75 }
])
"""

ATT = """
db.attendance.insertMany([
  { roll: 2401, day: new Date('2026-10-12'), present: true },  { roll: 2402, day: new Date('2026-10-12'), present: true },
  { roll: 2403, day: new Date('2026-10-12'), present: false }, { roll: 2401, day: new Date('2026-10-13'), present: false },
  { roll: 2402, day: new Date('2026-10-13'), present: true },  { roll: 2403, day: new Date('2026-10-13'), present: true }
])
"""

SECTION = dict(level='intermediate', title='Aggregation Framework', questions=[

# ------------------------------------------------------------------ 17
Q('What is the aggregation pipeline? Explain the common stages.', 'Aggregation Pipeline', minutes=10, cards=[
    definition(
        defbox('The <strong>aggregation pipeline</strong> processes documents through a sequence of <strong>stages</strong>; each stage transforms '
               'the stream of documents and passes the result to the next. It is MongoDB\'s equivalent of SQL\'s WHERE, GROUP BY, JOIN, ORDER BY '
               'and computed columns, and runs on the server.'),
        table(['Stage', 'SQL equivalent', 'Purpose'], [
            ['<code>$match</code>', 'WHERE / HAVING', 'Filter documents (put early, can use indexes)'],
            ['<code>$project</code> / <code>$addFields</code> / <code>$set</code>', 'SELECT expressions', 'Reshape, compute new fields'],
            ['<code>$group</code>', 'GROUP BY', 'Aggregate with <code>$sum $avg $min $max $push $addToSet $count</code>'],
            ['<code>$sort</code> / <code>$limit</code> / <code>$skip</code>', 'ORDER BY / LIMIT', 'Order and page results'],
            ['<code>$unwind</code>', '—', 'One document per array element'],
            ['<code>$lookup</code>', 'LEFT OUTER JOIN', 'Join another collection'],
            ['<code>$count</code>, <code>$facet</code>, <code>$bucket</code>, <code>$setWindowFields</code>', 'COUNT, multiple queries, CASE bins, window functions', 'Analytics'],
            ['<code>$out</code> / <code>$merge</code>', 'CREATE TABLE AS / MERGE', 'Write results to a collection'],
        ]),
        tags('Aggregation Pipeline', '$match', '$group', '$project', '$sort', 'Stages', 'Accumulators'),
    ),
    analogy('An <strong>assembly line</strong> in a factory: raw parts (documents) enter, the first station rejects defective parts ($match), the '
            'next groups them by type ($group), another sorts boxes ($sort), and the last puts on labels ($project). Each station only sees what the previous one hands over.'),
    pipeline_anim(),
    real_world(
        scenario('Course-wise performance report',
                 p('Every Monday the academic coordinator needs the number of students, average marks and topper per course, only for students '
                   'who appeared (marks ≥ 60). One aggregation pipeline produces the table directly from the <code>students</code> collection.')),
    ),
    example(
        mql('''
db.students.aggregate([
  { $match: { marks: { $gte: 60 } } },
  { $group: { _id: '$course', students: { $sum: 1 }, avg: { $avg: '$marks' }, best: { $max: '$marks' } } },
  { $sort: { avg: -1 } },
  { $project: { _id: 0, course: '$_id', students: 1, avg: { $round: ['$avg', 1] }, best: 1 } }
])

// count per centre (shortcut stage)
db.students.aggregate([ { $match: { centre: 'Juhu' } }, { $count: 'juhuStudents' } ])

// computed fields with conditional logic
db.students.aggregate([
  { $project: { _id: 0, name: 1, marks: 1,
      grade: { $switch: { branches: [ { case: { $gte: ['$marks', 85] }, then: 'A' }, { case: { $gte: ['$marks', 70] }, then: 'B' } ], default: 'C' } } } },
  { $sort: { marks: -1 } }, { $limit: 4 }
])
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Write the question in plain words', '"Average marks per course for students who appeared, best first."'),
        ('Start with $match', 'Filter as early as possible; it can use an index.'),
        ('Add $group', '<code>_id</code> = the grouping key; accumulators for each metric.'),
        ('Sort, limit and shape', '<code>$sort</code>, <code>$limit</code>, then <code>$project</code> to rename/round.'),
        ('Build incrementally', 'Run the pipeline after each added stage to check intermediate output.'),
        title='Steps to Build a Pipeline'),
    crossq(
        ('Why put $match first?', 'It reduces the number of documents every later stage processes, and only a $match (or $sort) at the start of the pipeline can use an index.'),
        ('$project vs $addFields?', '$project returns only the listed fields (plus _id); $addFields/$set keeps all existing fields and adds or overwrites the given ones.'),
        ('What is the 100 MB limit?', 'Each blocking stage ($group, $sort) may use up to 100 MB of RAM; beyond that it fails unless <code>allowDiskUse</code> lets it spill to disk (default true since 6.0).'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What does $unwind do? How do you aggregate values inside arrays?', '$unwind & Array Aggregation', minutes=8, cards=[
    definition(
        defbox('<code>$unwind: \'$skills\'</code> deconstructs an array field: it outputs one copy of the document <strong>per element</strong>, with '
               'the array replaced by that element. Documents with empty or missing arrays are dropped unless <code>preserveNullAndEmptyArrays: true</code>.',
               'After unwinding, <code>$group</code> can count or sum per element. Without unwinding, array operators such as <code>$size</code>, '
               '<code>$filter</code>, <code>$map</code> and <code>$reduce</code> work on the array inside each document.'),
        tags('$unwind', '$group', '$size', '$filter', '$map', 'preserveNullAndEmptyArrays'),
    ),
    analogy('A box containing three different books is <strong>unpacked</strong> so that each book sits on the conveyor separately, each with a '
            'copy of the box label. Now you can count books by title across all boxes.'),
    unwind_anim(),
    real_world(
        scenario('Skill gap analysis',
                 p('To decide which add-on workshops to run, the placement cell counts how many students list each skill: '
                   '<code>$unwind</code> skills, <code>$group</code> by skill, <code>$sort</code> by count.')),
    ),
    example(
        mql('''
db.students.aggregate([
  { $unwind: '$skills' },
  { $group: { _id: '$skills', students: { $sum: 1 }, names: { $push: '$name' } } },
  { $sort: { students: -1, _id: 1 } },
  { $limit: 4 }
])

// keep students with no skills
db.students.aggregate([
  { $match: { course: 'PG-DAC' } },
  { $unwind: { path: '$skills', preserveNullAndEmptyArrays: true } },
  { $project: { _id: 0, name: 1, skills: 1 } }
])

// work on arrays WITHOUT unwinding
db.students.aggregate([
  { $match: { course: 'PG-DBDA' } },
  { $project: { _id: 0, name: 1, nSkills: { $size: '$skills' },
      goodScores: { $filter: { input: '$scores', as: 's', cond: { $gte: ['$$s.m', 80] } } } } }
])
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Need per-element statistics across documents?', '$unwind then $group.'),
        ('Need per-document calculations on the array?', 'Use $size/$filter/$map/$reduce, no unwind.'),
        ('Keep documents with empty arrays', '<code>preserveNullAndEmptyArrays: true</code>.'),
        ('Filter before unwinding', 'A $match before $unwind keeps the multiplied stream small.'),
        title='Steps'),
    crossq(
        ('Why can $unwind be expensive?', 'It multiplies documents: 1 million students × 20 skills = 20 million intermediate documents. Filter first and project only needed fields.'),
        ('How do you rebuild the array after unwinding?', '$group by the original _id with <code>$push</code> (keeps duplicates/order) or <code>$addToSet</code>.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('How do you join collections in MongoDB with $lookup?', '$lookup (Joins)', minutes=9, cards=[
    definition(
        defbox('<code>$lookup</code> performs a <strong>left outer join</strong> to another collection in the same database. The basic form matches '
               '<code>localField</code> to <code>foreignField</code> and stores the matching documents as an array in <code>as</code>. The pipeline '
               'form (<code>let</code> + <code>pipeline</code>) allows any conditions, filtering and projection of the joined documents.'),
        tags('$lookup', 'Join', 'localField', 'foreignField', 'Left Outer Join', 'Pipeline Lookup'),
    ),
    analogy('Each student file gets a <strong>stapled bundle of their marksheets</strong> fetched from the exam office drawer. If the exam office has '
            'none, the student file gets an empty bundle, not removed (left outer join).'),
    lookup_anim(),
    real_world(
        scenario('Report card generation',
                 p('Marks are stored in their own collection (they are many, written by the exam module). The report card query joins them '
                   'to students with <code>$lookup</code>, computes totals and formats one document per student. The <code>marks.roll</code> '
                   'field is indexed so each lookup is an index seek.')),
    ),
    example(
        mql('''
db.students.aggregate([
  { $match: { _id: { $in: [2401, 2402, 2404] } } },
  { $lookup: { from: 'marks', localField: '_id', foreignField: 'roll', as: 'results' } },
  { $project: { name: 1, subjects: { $size: '$results' }, total: { $sum: '$results.m' } } }
])

// pipeline form: only SQL marks, only the needed fields
db.students.aggregate([
  { $match: { course: 'PG-DBDA' } },
  { $lookup: {
      from: 'marks', let: { r: '$_id' },
      pipeline: [ { $match: { $expr: { $eq: ['$roll', '$$r'] }, sub: 'SQL' } }, { $project: { _id: 0, m: 1 } } ],
      as: 'sql' } },
  { $project: { _id: 0, name: 1, sqlMarks: { $first: '$sql.m' } } }
])
''', setup=STUDENTS + MARKS),
        title='Example'),
    steps(
        ('Confirm a join is really needed', 'If the data is always read together and small, embed it instead.'),
        ('Index the foreign field', '<code>db.marks.createIndex({roll: 1})</code>.'),
        ('$match before $lookup', 'Join only the documents you need.'),
        ('Shape the joined array', 'Use the pipeline form to filter/project, or $unwind it to one document per match.'),
        title='Steps for an Efficient $lookup'),
    crossq(
        ('How do you make $lookup behave like an INNER JOIN?', 'Follow it with <code>{$match: {results: {$ne: []}}}</code> or <code>$unwind</code> without preserveNullAndEmptyArrays.'),
        ('Can $lookup join a sharded collection?', 'Since MongoDB 5.1 the <code>from</code> collection can be sharded. Joins across databases are not supported.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What are $facet and $bucket? How do you build a dashboard query?', '$facet & $bucket', minutes=8, cards=[
    definition(
        defbox('<code>$bucket</code> groups documents into ranges of a field (<code>boundaries</code>), like a histogram; <code>$bucketAuto</code> '
               'chooses the ranges automatically. <code>$facet</code> runs several sub-pipelines on the same input in one stage and returns one '
               'document with an array per facet, ideal for dashboards and search pages with multiple filters/counts.'),
        tags('$facet', '$bucket', '$bucketAuto', 'Histogram', 'Dashboard', 'Faceted Search'),
    ),
    analogy('<code>$bucket</code> is sorting answer sheets into <strong>grade trays</strong> (below 60, 60–79, 80+). <code>$facet</code> is several '
            'clerks each preparing a different summary from <strong>photocopies of the same pile</strong> at the same time.'),
    facet_anim(),
    real_world(
        scenario('Coordinator dashboard',
                 p('One API call returns: students per course, the marks distribution, and the top 3 students, which three dashboard widgets '
                   'render. Using $facet halves page load time compared with three separate queries.')),
    ),
    example(
        mql('''
db.students.aggregate([
  { $bucket: { groupBy: '$marks', boundaries: [0, 60, 80, 101], default: 'other',
               output: { count: { $sum: 1 }, names: { $push: '$name' } } } }
])

db.students.aggregate([
  { $facet: {
      byCourse: [ { $group: { _id: '$course', n: { $sum: 1 } } }, { $sort: { _id: 1 } } ],
      toppers:  [ { $sort: { marks: -1 } }, { $limit: 3 }, { $project: { _id: 0, name: 1, marks: 1 } } ],
      overall:  [ { $group: { _id: null, avg: { $avg: '$marks' }, n: { $sum: 1 } } }, { $project: { _id: 0 } } ]
  } }
])
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('List the widgets', 'Each widget = one facet.'),
        ('Put shared filters before $facet', 'So they run once and can use indexes.'),
        ('Write each sub-pipeline', 'Groups, buckets, top-N.'),
        ('Return one document to the UI', 'Each key feeds one chart.'),
        title='Steps for a Dashboard Query'),
    crossq(
        ('Can stages inside $facet use indexes?', 'No. Sub-pipelines work on the documents passed in, so filter with an indexed $match before $facet.'),
        ('What does the default bucket do?', 'Collects documents whose value falls outside all boundaries; without it such documents cause an error.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('How do you do window functions, date grouping and running totals in MongoDB?', '$setWindowFields & Dates', minutes=9, cards=[
    definition(
        defbox('<code>$setWindowFields</code> (MongoDB 5.0+) adds computed fields based on a <strong>window</strong> of related documents: '
               '<code>partitionBy</code> (group), <code>sortBy</code> (order), and outputs such as <code>$rank</code>, <code>$denseRank</code>, '
               '<code>$documentNumber</code>, <code>$shift</code> (previous/next value), and accumulators over a frame (<code>window: {documents: '
               '[\'unbounded\', \'current\']}</code> for running totals).',
               'Date operators (<code>$dateToString</code>, <code>$dateTrunc</code>, <code>$year</code>, <code>$dayOfWeek</code>…) group time data by day, week or month.'),
        tags('$setWindowFields', '$rank', 'Running Total', '$dateToString', '$dateTrunc', 'Time Series'),
    ),
    analogy('Window functions give every student a <strong>badge computed by looking at classmates</strong> (rank in course, running total) while '
            'everybody stays in the room, unlike $group, which sends everyone home and keeps one summary card per course.'),
    window_anim(),
    real_world(
        scenario('Attendance trend',
                 p('Daily attendance % per day is computed with <code>$group</code> on <code>$dateToString</code>, then a 7-day moving average '
                   'with <code>$setWindowFields</code> smooths weekends and holidays for the trend chart.')),
    ),
    example(
        mql('''
db.students.aggregate([
  { $match: { course: { $in: ['PG-DBDA', 'PG-DAC'] } } },
  { $setWindowFields: { partitionBy: '$course', sortBy: { marks: -1 },
      output: { rank: { $rank: {} }, denseRank: { $denseRank: {} } } } },
  { $project: { _id: 0, course: 1, name: 1, marks: 1, rank: 1, denseRank: 1 } }
])
''', setup=STUDENTS),
        mql('''
db.attendance.aggregate([
  { $group: { _id: { $dateToString: { format: '%Y-%m-%d', date: '$day' } },
              present: { $sum: { $cond: ['$present', 1, 0] } }, total: { $sum: 1 } } },
  { $sort: { _id: 1 } },
  { $setWindowFields: { sortBy: { _id: 1 },
      output: { cumulativePresent: { $sum: '$present', window: { documents: ['unbounded', 'current'] } } } } },
  { $project: { day: '$_id', _id: 0, pct: { $round: [{ $multiply: [{ $divide: ['$present', '$total'] }, 100] }, 1] }, cumulativePresent: 1 } }
])
''', setup=ATT),
        title='Example'),
    steps(
        ('Choose partition and order', 'partitionBy = group; sortBy = sequence.'),
        ('Pick the output', 'Ranking, $shift for previous values, or an accumulator with a window frame.'),
        ('Dates: group on a truncated date', '<code>$dateTrunc</code> (unit day/week/month) or <code>$dateToString</code>; mind the timezone option.'),
        ('Filter afterwards if needed', 'e.g. <code>{$match: {rank: {$lte: 3}}}</code> for top-3 per group.'),
        title='Steps'),
    crossq(
        ('How did people do top-N per group before 5.0?', '$sort then $group with $push and $slice (or $first for top-1). Since 5.2 there are also $topN/$bottomN accumulators.'),
        ('Why specify a timezone in date grouping?', 'Dates are stored in UTC; grouping by day in UTC shifts IST activity after 18:30 into the next day. Use <code>timezone: \'Asia/Kolkata\'</code>.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How do you store aggregation results? Explain $out and $merge.', '$out & $merge', minutes=7, cards=[
    definition(
        defbox('<code>$out: \'coll\'</code> writes the pipeline result to a collection, <strong>replacing</strong> it entirely (atomically). '
               '<code>$merge: {into, on, whenMatched, whenNotMatched}</code> <strong>merges</strong> results into an existing collection: '
               'replace/merge/keep matched documents, insert or discard new ones. Both must be the last stage.'),
        tags('$out', '$merge', 'Materialized View', 'Incremental Refresh', 'On-demand View'),
    ),
    analogy('<code>$out</code> is <strong>reprinting the whole notice board</strong> every time. <code>$merge</code> is <strong>pinning updated '
            'notices</strong> over the old ones and adding new ones, leaving the rest as they were.'),
    out_merge_anim(),
    real_world(
        scenario('Daily attendance summary',
                 p('A scheduled job runs a pipeline for yesterday only and <code>$merge</code>s one document per day into '
                   '<code>attendance_daily</code>. Dashboards read this small collection instead of aggregating millions of raw events.')),
    ),
    example(
        mql('''
db.attendance.aggregate([
  { $group: { _id: '$day', present: { $sum: { $cond: ['$present', 1, 0] } }, total: { $sum: 1 } } },
  { $out: 'attendance_daily' }
])
db.attendance_daily.find().sort({ _id: 1 })
''', setup=ATT),
        mq('''
// incremental: only yesterday, merged into the summary
db.attendance.aggregate([
  { $match: { day: ISODate('2026-10-13') } },
  { $group: { _id: '$day', present: { $sum: { $cond: ['$present', 1, 0] } }, total: { $sum: 1 } } },
  { $merge: { into: 'attendance_daily', on: '_id', whenMatched: 'replace', whenNotMatched: 'insert' } }
])
''', '$merge for incremental refresh'),
        title='Example'),
    steps(
        ('Write and test the pipeline', 'Without the output stage first.'),
        ('Full rebuild?', 'Append <code>$out</code>.'),
        ('Incremental?', '<code>$match</code> the new period and append <code>$merge</code> with an <code>on</code> key that has a unique index.'),
        ('Schedule', 'Atlas Triggers, cron, or Airflow.'),
        title='Steps to Build a Materialized View'),
    crossq(
        ('View vs on-demand materialized view?', 'A view (<code>db.createView</code>) re-runs its pipeline at every read and stores nothing; a materialized collection built with $out/$merge is pre-computed and fast but must be refreshed.'),
    ),
]),
])
