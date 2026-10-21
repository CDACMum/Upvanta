from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py, xml

STUDENTS = '''
create 'students', {NAME => 'info', VERSIONS => 3}, {NAME => 'marks'}
put 'students', '2401', 'info:name', 'Anuj'
put 'students', '2401', 'info:city', 'Pune'
put 'students', '2401', 'marks:sql', '78'
put 'students', '2402', 'info:name', 'Aarshvi'
put 'students', '2402', 'info:city', 'Mumbai'
put 'students', '2403', 'info:name', 'Riya'
put 'students', '2403', 'info:city', 'Thane'
'''

SECTION = dict(level='basic', title='HBase Shell & Data Operations', questions=[

# ------------------------------------------------------------------ 6
Q('How do you create, describe, alter and drop tables and namespaces in HBase?', 'Namespaces & Table DDL', minutes=8, cards=[
    definition(
        table(['Command', 'Purpose'], [
            ['<code>create_namespace \'cdac\'</code>', 'Create a namespace (like a database). <code>default</code> and <code>hbase</code> (system) always exist.'],
            ["<code>create 'cdac:students', 'info', 'marks'</code>", 'Create a table with column families (options per family in a hash).'],
            ['<code>list</code>, <code>describe</code>, <code>exists</code>', 'List tables, show family settings, check existence.'],
            ['<code>alter</code>', 'Add, modify or delete column families and table attributes.'],
            ['<code>disable</code> → <code>drop</code>', 'A table must be disabled before it can be dropped.'],
            ['<code>truncate</code>', 'Disable, drop and recreate with the same schema (all data gone).'],
        ]),
        tags('create_namespace', 'create', 'describe', 'alter', 'disable', 'drop', 'truncate'),
    ),
    analogy('Creating a table is like setting up a <strong>cupboard with labelled drawers</strong> (families). You can add or relabel drawers later, but to '
            'throw the cupboard away you must first lock it (disable).'),
    ddl_anim(),
    real_world(
        scenario('Namespaces per project',
                 p('The exam team uses namespace <code>exam</code>, the attendance team <code>att</code>. Quotas and permissions can be granted per namespace '
                   '(<code>grant \'att_team\', \'RW\', \'@att\'</code>), so teams cannot touch each other\'s tables.')),
    ),
    example(
        hsh('''
create_namespace 'cdac'
create 'cdac:students', {NAME => 'info', VERSIONS => 3}, {NAME => 'marks', TTL => 31536000}
list
describe 'cdac:students'
alter 'cdac:students', {NAME => 'contact'}
alter 'cdac:students', {NAME => 'marks', METHOD => 'delete'}
drop 'cdac:students'
disable 'cdac:students'
drop 'cdac:students'
exists 'cdac:students'
''', expect_error=True),
        title='Example'),
    steps(
        ('Create a namespace per application', '<code>create_namespace \'cdac\'</code>'),
        ('Create the table with families and settings', 'VERSIONS, TTL, COMPRESSION per family; SPLITS for pre-splitting.'),
        ('Inspect', '<code>describe</code> shows every family setting.'),
        ('Change later with alter', 'New families or settings; existing data adopts settings at compaction.'),
        ('Drop safely', '<code>disable</code> then <code>drop</code>; snapshot first if in doubt.'),
        title='Steps'),
    crossq(
        ('Why must a table be disabled before drop?', 'Disabling closes all its regions on the RegionServers (flushing MemStores), so no region is serving or writing data when files are deleted.'),
        ('Does alter need the table disabled?', 'Not in modern HBase (online schema change is on by default); regions are reopened one by one with the new schema.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How do put, get, scan, delete and deleteall work?', 'put / get / scan / delete', minutes=9, cards=[
    definition(
        table(['Command', 'Syntax', 'Notes'], [
            ['put', "<code>put 't', 'row', 'cf:q', 'value' [, ts]</code>", 'Insert or update one cell (new version).'],
            ['get', "<code>get 't', 'row' [, {COLUMN =&gt; …, VERSIONS =&gt; n}]</code>", 'Read one row; fastest operation.'],
            ['scan', "<code>scan 't', {STARTROW =&gt; …, STOPROW =&gt; …, COLUMNS =&gt; […], LIMIT =&gt; n, FILTER =&gt; …}</code>", 'Read a key range in order.'],
            ['delete', "<code>delete 't', 'row', 'cf:q' [, ts]</code>", 'Delete all versions of a column (up to ts).'],
            ['deleteall', "<code>deleteall 't', 'row' [, 'cf:q']</code>", 'Delete a whole row (or column).'],
            ['count', "<code>count 't'</code>", 'Counts rows by scanning (slow on big tables; use the RowCounter MapReduce job).'],
        ]),
        tags('put', 'get', 'scan', 'delete', 'deleteall', 'count'),
    ),
    analogy('put is <strong>writing a dated note</strong> into a folder, get is <strong>pulling one folder</strong>, scan is <strong>walking along the shelf</strong> '
            'between two labels, and delete is <strong>sticking a "cancelled" slip</strong> over a note.'),
    crud_anim(),
    real_world(
        scenario('A student portal backend',
                 ul('Profile page: <code>get</code> by roll number.',
                    'Update city: <code>put</code> the new value; the old one stays as a version if VERSIONS &gt; 1.',
                    'Admin list of a batch: <code>scan</code> with a row-key prefix.',
                    'Remove a test account: <code>deleteall</code>.')),
    ),
    example(
        hsh('''
get 'students', '2401'
get 'students', '2401', 'info:name'
put 'students', '2401', 'info:city', 'Mumbai'
get 'students', '2401', {COLUMN => ['info:city', 'marks:sql']}
scan 'students', {COLUMNS => ['info:name'], LIMIT => 2}
delete 'students', '2402', 'info:city'
deleteall 'students', '2403'
scan 'students'
count 'students'
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Read by key whenever possible', 'get is a single region lookup.'),
        ('Limit columns', 'COLUMNS / COLUMN so fewer bytes travel.'),
        ('Bound scans', 'STARTROW/STOPROW or ROWPREFIXFILTER, plus LIMIT.'),
        ('Prefer batching from code', 'Java <code>Table.put(List)</code> / BufferedMutator for bulk writes.'),
        title='Steps'),
    crossq(
        ('Is there an UPDATE command?', 'No: put is used for both insert and update.'),
        ('Why is count slow on big tables?', 'It scans every row through the RegionServers. For large tables use <code>hbase org.apache.hadoop.hbase.mapreduce.RowCounter &lt;table&gt;</code>, which runs in parallel.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How do versions and timestamps work in HBase?', 'Versions & Timestamps', minutes=8, cards=[
    definition(
        defbox('Every cell value carries a <strong>timestamp</strong> (milliseconds since epoch). By default the RegionServer assigns the current time; the client '
               'can also set it explicitly. A put to an existing cell creates a <strong>new version</strong> rather than overwriting in place.',
               'The family setting <code>VERSIONS</code> (default 1) is the maximum number of versions kept; <code>MIN_VERSIONS</code> works with TTL. Reads return '
               'the newest version unless you ask for <code>VERSIONS =&gt; n</code>, a specific <code>TIMESTAMP</code>, or a <code>TIMERANGE =&gt; [from, to)</code>.'),
        tags('Version', 'Timestamp', 'VERSIONS', 'TIMERANGE', 'TIMESTAMP', 'Time travel'),
    ),
    analogy('A <strong>register where corrections are written on new lines with the date</strong>. Normally you read the latest line; when needed, you can read '
            'what the register said on any earlier date, as long as old lines have not been cleared out.'),
    versions_anim(),
    real_world(
        scenario('Address history',
                 p('<code>info:city</code> is kept with <code>VERSIONS =&gt; 3</code>, so the office can see a student\'s last three addresses without a separate history table.')),
    ),
    example(
        hsh('''
put 'students', '2401', 'info:city', 'Mumbai'
put 'students', '2401', 'info:city', 'Thane'
get 'students', '2401', 'info:city'
get 'students', '2401', {COLUMN => 'info:city', VERSIONS => 3}
# a fourth version: only 3 are kept (VERSIONS => 3)
put 'students', '2401', 'info:city', 'Nashik'
get 'students', '2401', {COLUMN => 'info:city', VERSIONS => 5}
# the value as it was just before 10:00:00.009 (TIMERANGE end is exclusive)
get 'students', '2401', {COLUMN => 'info:city', TIMERANGE => [0, 1791952200009]}
# 'marks' keeps only 1 version
put 'students', '2401', 'marks:sql', '85'
get 'students', '2401', {COLUMN => 'marks:sql', VERSIONS => 3}
''', setup=STUDENTS),
        title='Example'),
    steps(
        ('Decide how much history you need', 'VERSIONS per family; keep 1 when history is not needed.'),
        ('Read history explicitly', '<code>VERSIONS =&gt; n</code> or <code>TIMERANGE</code>.'),
        ('Avoid client timestamps unless needed', 'Explicit timestamps are useful for idempotent re-loads, but wrong clocks cause surprising results.'),
        title='Steps'),
    crossq(
        ('What happens with a put using an older explicit timestamp?', 'It is stored as an older version; reads still return the newest timestamp, so the "late" write appears to be ignored.'),
        ('Are versions a good way to store unlimited history?', 'No: use a row per event (tall table) or qualifiers with dates. Versions are for limited history of the same value.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How do scans work? Explain STARTROW, STOPROW, prefixes and row key ordering.', 'Scans & Key Ordering', minutes=9, cards=[
    definition(
        defbox('A <strong>scan</strong> reads rows in <strong>row-key byte order</strong> from <code>STARTROW</code> (inclusive) to <code>STOPROW</code> (exclusive). '
               '<code>ROWPREFIXFILTER</code> sets both to cover all keys starting with a prefix. Other options: <code>COLUMNS</code>, <code>LIMIT</code>, '
               '<code>REVERSED</code>, <code>VERSIONS</code>, <code>TIMERANGE</code>, <code>FILTER</code>, <code>CACHE</code>/<code>BATCH</code> (rows/cells per RPC).',
               'Keys compare <strong>lexicographically as bytes</strong>: "10" &lt; "2" &lt; "9". Numbers in keys must be fixed width (zero-padded) or binary '
               'for ranges to behave numerically.'),
        tags('scan', 'STARTROW', 'STOPROW', 'ROWPREFIXFILTER', 'REVERSED', 'Lexicographic order'),
    ),
    analogy('A <strong>dictionary</strong>: words are ordered letter by letter, so "10" comes before "2" just as "ba" comes before "c". To list numbers in '
            'order, write them with the same number of digits (002, 010).'),
    scan_order_anim(),
    real_world(
        scenario('A bug that zero-padding fixed',
                 p('Roll numbers 9, 10, 11… were stored as plain text; "scan from 9 to 12" returned nothing because "9" sorts after "12". Re-keying with '
                   'zero-padded six-digit roll numbers made range scans correct.')),
    ),
    example(
        hsh('''
create 'rolls', 'i'
put 'rolls', '9', 'i:n', 'nine'
put 'rolls', '10', 'i:n', 'ten'
put 'rolls', '100', 'i:n', 'hundred'
put 'rolls', '2', 'i:n', 'two'
scan 'rolls'
# "rows 2 to 9"? '10' and '100' sort BEFORE '2', so only '2' comes back
scan 'rolls', {STARTROW => '2', STOPROW => '9'}
create 'rolls_padded', 'i'
put 'rolls_padded', '009', 'i:n', 'nine'
put 'rolls_padded', '010', 'i:n', 'ten'
put 'rolls_padded', '100', 'i:n', 'hundred'
put 'rolls_padded', '002', 'i:n', 'two'
scan 'rolls_padded', {STARTROW => '002', STOPROW => '011'}
scan 'rolls_padded', {REVERSED => true, LIMIT => 2}
'''),
        title='Example'),
    steps(
        ('Encode key parts with fixed width', 'Zero-pad numbers, fixed-length codes, a separator such as <code>|</code>.'),
        ('Use STARTROW/STOPROW or ROWPREFIXFILTER', 'Never scan the whole table when a range will do.'),
        ('Tune caching', '<code>CACHE =&gt; 500</code> (rows per RPC) for large scans.'),
        ('Prefer forward scans', 'Reverse scans work but are slower.'),
        title='Steps'),
    crossq(
        ('Is STOPROW inclusive?', 'No, it is exclusive. For an inclusive end use the InclusiveStopFilter or append a zero byte to the stop key.'),
        ('How is ROWPREFIXFILTER different from PrefixFilter?', 'ROWPREFIXFILTER sets the scan\'s start and stop rows, so only that key range is read. PrefixFilter is a filter evaluated on every row of the range, so without a start row it scans from the beginning.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How do counters (incr) and append work in HBase?', 'Counters & Append', minutes=7, cards=[
    definition(
        defbox('<code>incr \'t\', \'row\', \'cf:q\', n</code> atomically adds n to a <strong>64-bit long</strong> stored in the cell and returns the new value; the '
               'cell is created at 0 if absent. <code>get_counter</code> reads it as a number (a plain get shows 8 raw bytes). '
               '<code>append</code> atomically appends bytes to a cell\'s value.',
               'Both are executed by the RegionServer under the row lock, so concurrent clients never lose updates. A counter cell must contain exactly 8 bytes; '
               'incrementing a cell written with put (text) fails.'),
        tags('incr', 'get_counter', 'append', 'Atomic', '8-byte long'),
    ),
    analogy('A <strong>turnstile counter</strong> at the exam hall gate: every person clicks it, the machine adds one atomically, and the display always shows the exact total.'),
    counter_anim(),
    real_world(
        scenario('Live dashboards',
                 p('Per-centre check-in counters (<code>incr</code> on <code>att:checkins</code>) feed a live dashboard during exam day; the coordinator sees exact '
                   'numbers per centre, refreshed every few seconds with a get.')),
    ),
    example(
        hsh('''
create 'stats', 's'
incr 'stats', 'KHR|20261014', 's:checkins', 1
incr 'stats', 'KHR|20261014', 's:checkins', 1
incr 'stats', 'KHR|20261014', 's:checkins', 5
get 'stats', 'KHR|20261014'
get_counter 'stats', 'KHR|20261014', 's:checkins'
# a value written with put is text, not an 8-byte long
put 'stats', 'KHR|20261014', 's:late', '3'
incr 'stats', 'KHR|20261014', 's:late', 1
append 'stats', 'KHR|20261014', 's:log', 'in;'
append 'stats', 'KHR|20261014', 's:log', 'out;'
''', expect_error=True),
        title='Example'),
    steps(
        ('Use a dedicated family/qualifier for counters', 'Never mix with put-written text values.'),
        ('Increment by n in one call', 'Batch increments from the client where possible.'),
        ('Read with get_counter', 'Or decode 8 bytes with <code>Bytes.toLong</code> in Java.'),
        ('Watch hot counter rows', 'A single global counter row becomes a hotspot; shard it into N rows and sum on read.'),
        title='Steps'),
    crossq(
        ('Are HBase increments idempotent?', 'No: if a client retries an increment after a timeout, it may be applied twice. Nonces in the client protocol reduce this, but use event rows for exact accounting.'),
        ('Why is the shell output \\x00…\\x07?', 'The shell prints bytes with Bytes.toStringBinary; non-printable bytes appear as \\xNN. The counter is the big-endian long 7.'),
    ),
]),
])
