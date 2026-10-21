from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py

SECTION = dict(level='intermediate', title='Row Key & Schema Design', questions=[

# ------------------------------------------------------------------ 16
Q('Why is row key design the most important decision in HBase? What are the principles?', 'Row Key Design Principles', minutes=10, cards=[
    definition(
        defbox('The row key is HBase\'s <strong>only index</strong> and decides <strong>data placement</strong> (which region), <strong>sort order</strong> '
               '(what a range scan returns) and <strong>load distribution</strong>. A query that cannot use the key becomes a full table scan.'),
        ul('Lead the key with the attribute you look up or scan by (e.g. <code>roll|date</code> for "a student\'s history").',
           'Avoid monotonically increasing leading parts (timestamps, sequences): they create write hotspots.',
           'Keep keys <strong>short</strong>: the row key is stored with every cell (also family and qualifier names).',
           'Use <strong>fixed-width</strong> parts and a separator so prefixes and ranges are unambiguous.',
           'Row keys are immutable: "changing" one means writing a new row and deleting the old one.'),
        tags('Row key', 'Only index', 'Hotspot', 'Prefix scan', 'Fixed width', 'Composite key'),
    ),
    analogy('Arranging books in a library: if they are ordered by <strong>student roll number then date</strong>, finding a student\'s books is one shelf. '
            'If they are ordered by <strong>arrival time</strong>, every new book goes to the same last shelf and one librarian is overwhelmed.'),
    rowkey_principles_anim(),
    real_world(
        scenario('Same data, three keys',
                 table(['Row key', 'Good for', 'Bad for'], [
                     ['<code>roll|yyyyMMdd</code>', 'a student\'s history (prefix scan)', 'a whole centre on one day'],
                     ['<code>centre|yyyyMMdd|roll</code>', 'a centre\'s day', 'one student across centres'],
                     ['<code>yyyyMMddHHmmss|roll</code>', 'nothing much', 'hotspot on the newest region'],
                 ])),
    ),
    example(
        hsh('''
create 'att', 'a'
put 'att', '2401|20261013', 'a:s', 'P'
put 'att', '2401|20261014', 'a:s', 'A'
put 'att', '2402|20261013', 'a:s', 'P'
put 'att', '2402|20261014', 'a:s', 'P'
# student history: one prefix scan, already in date order
scan 'att', {ROWPREFIXFILTER => '2401|'}
# one day for all students: the key cannot help, every row is read and filtered
scan 'att', {FILTER => "RowFilter(=, 'substring:|20261014')"}
'''),
        title='Example'),
    steps(
        ('List the queries', 'Which values are always known? Which ranges are scanned?'),
        ('Order key parts: equality first, range last', 'e.g. <code>roll|date</code>.'),
        ('Check write distribution', 'Does the leading part spread writes? If not, salt or hash.'),
        ('Encode with fixed width', 'Zero-pad, use codes, binary longs.'),
        ('Add tables for other access paths', 'Index tables or Phoenix indexes.'),
        title='Steps'),
    crossq(
        ('How long can a row key be?', 'Up to 32,767 bytes, but keep it as short as possible (tens of bytes), since it is repeated for every cell.'),
        ('Can you change the row key of existing data?', 'Only by writing new rows and deleting old ones, typically with a MapReduce/Spark job into a new table.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is hotspotting? How do salting, hashing and key reversal prevent it?', 'Hotspotting & Salting', minutes=10, cards=[
    definition(
        defbox('<strong>Hotspotting</strong> happens when a large share of traffic goes to one region, and therefore one RegionServer. The classic cause is a key '
               'that increases monotonically (timestamp, sequence ID): every new row sorts after the previous one, so all inserts hit the last region.'),
        table(['Technique', 'How', 'Trade-off'], [
            ['Salting', 'prefix = hash(id) % N, e.g. <code>3|20261014…</code>', 'reads of a range need N scans (one per salt)'],
            ['Hashing', 'key = hash(natural key) (e.g. MD5 prefix)', 'perfect spread, but no meaningful range scans'],
            ['Reversing', 'reverse a fixed-width field: phone numbers, domain names (com.cdac.www)', 'only helps when the end of the value varies most'],
            ['Pre-splitting', '<code>SPLITS =&gt; […]</code> at create time', 'needs knowledge of the key distribution'],
        ]),
        tags('Hotspot', 'Salting', 'Hashing', 'Key reversal', 'Pre-split', 'Monotonic keys'),
    ),
    analogy('If every arriving parcel is labelled with the time it came in, they all go to the <strong>last counter</strong>. Adding a "counter number" '
            '(0–3) in front spreads parcels over four counters, but finding all parcels from 10–11 am means asking all four counters.'),
    hotspot_anim(),
    real_world(
        scenario('Exam-day event log',
                 p('Proctoring events keyed by timestamp overloaded one RegionServer at 10:00 when 5,000 candidates started together. Re-keying as '
                   '<code>salt(0-7)|timestamp|roll</code> and pre-splitting into 8 regions spread the load across all servers.')),
    ),
    example(
        hsh('''
create 'events', 'e', {SPLITS => ['1', '2', '3']}
# application computes salt = hash(roll) % 4
put 'events', '0|20261014100003|2404', 'e:type', 'login'
put 'events', '1|20261014100001|2401', 'e:type', 'login'
put 'events', '2|20261014100002|2402', 'e:type', 'login'
put 'events', '3|20261014100002|2403', 'e:type', 'login'
put 'events', '1|20261014101451|2401', 'e:type', 'tab_switch'
scan 'events'
# all events of 10:00-10:10 = one scan per salt bucket (here bucket 1)
scan 'events', {STARTROW => '1|20261014100000', STOPROW => '1|20261014101000'}
'''),
        p('The table was pre-split at "1", "2" and "3", so each salt bucket lives in its own region from the start. A time-range report runs the bucket scan four '
          'times (0–3) in parallel and merges the results.', top=True),
        title='Example'),
    steps(
        ('Detect', 'Region request counts in the Master UI; one RegionServer much busier than others.'),
        ('Choose salt or hash', 'Salt if you still need time ranges; hash if you only do point gets.'),
        ('Pick N', 'Roughly the number of RegionServers (or a multiple).'),
        ('Pre-split on the salt prefixes', 'So buckets start on different servers.'),
        title='Steps'),
    crossq(
        ('Why not random salts?', 'With a random salt you cannot recompute it for a get; you would have to query all buckets. A deterministic hash of the entity ID keeps point gets to one lookup.'),
        ('Does Phoenix support salting?', 'Yes: <code>CREATE TABLE … SALT_BUCKETS = 8</code> adds and handles the salt byte automatically.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('How do you design row keys for time-series data and "latest first" reads?', 'Time-Series Keys', minutes=9, cards=[
    definition(
        defbox('Typical key: <code>entity | time</code> (plus a salt if writes are very concentrated). Putting the entity first keeps one source\'s readings together '
               'and spreads writes across entities. Time inside the key gives range scans per entity.',
               'For <strong>latest-first</strong> reads, store a <strong>reversed timestamp</strong>: <code>Long.MAX_VALUE − ts</code>, zero-padded to 19 digits (or as an '
               '8-byte big-endian long). Then a forward prefix scan with <code>LIMIT 1</code> returns the newest row. OpenTSDB, a time-series database on HBase, '
               'uses a similar design (metric + base hour, with offsets in qualifiers).'),
        tags('Time series', 'Reversed timestamp', 'Long.MAX_VALUE', 'OpenTSDB', 'Latest N'),
    ),
    analogy('A <strong>news feed</strong>: you always want the newest item on top. Numbering items with "how long until the end of time" makes the newest '
            'have the smallest number, so it naturally comes first.'),
    reverse_ts_anim(),
    real_world(
        scenario('Lab sensor dashboard',
                 p('Key <code>sensor|reversed_ts</code>: "current temperature of S01" is one short scan; "last hour" is a range between two reversed timestamps. '
                   'A family TTL of 30 days expires old readings automatically.')),
    ),
    example(
        hsh('''
create 'readings', {NAME => 'r', TTL => 2592000}
# reversed = 9223372036854775807 - epoch_ms  (10:00, 10:05, 10:10 IST)
put 'readings', 'S01|9223370244902575807', 'r:temp', '24.5'
put 'readings', 'S01|9223370244902275807', 'r:temp', '25.3'
put 'readings', 'S01|9223370244901975807', 'r:temp', '25.9'
put 'readings', 'S02|9223370244902575807', 'r:temp', '22.0'
# latest reading of S01
scan 'readings', {ROWPREFIXFILTER => 'S01|', LIMIT => 1}
# all S01 readings, newest first
scan 'readings', {ROWPREFIXFILTER => 'S01|'}
'''),
        py('''
MAX = 2**63 - 1
def reading_key(sensor, epoch_ms):
    return f"{sensor}|{MAX - epoch_ms:019d}"          # fixed 19 digits → text order = numeric order

print(reading_key("S01", 1791952200000))               # 10:00 IST
print(reading_key("S01", 1791952800000))               # 10:10 IST → smaller key, sorts first
''', 'Computing reversed keys'),
        title='Example'),
    steps(
        ('Entity first, time second', 'Spreads writes and groups readings per entity.'),
        ('Reverse time for latest-first', 'Pad to fixed width.'),
        ('Expire with TTL', 'Per family.'),
        ('Salt only if one entity is extremely hot', 'Most workloads are spread by the entity part already.'),
        title='Steps'),
    crossq(
        ('Why not use the cell timestamp/versions for time series?', 'Versions are limited per cell and meant for a few historical values; millions of readings belong in separate rows (or qualifiers).'),
        ('How do you query a time range with reversed keys?', 'Swap the bounds: STARTROW = entity|reverse(end_time), STOPROW = entity|reverse(start_time).'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('Tall-narrow vs flat-wide tables: which should you choose?', 'Tall vs Wide Tables', minutes=8, cards=[
    definition(
        table(['', 'Tall-narrow', 'Flat-wide'], [
            ['Shape', 'many rows, few columns: <code>roll|date → status</code>', 'few rows, many columns: <code>roll → {date: status, …}</code>'],
            ['Read pattern', 'prefix/range scan', 'single get (optionally column filters)'],
            ['Atomicity', 'per event row', 'all columns of an entity updated atomically'],
            ['Distribution', 'splits naturally across regions', 'a row never splits: huge rows hurt'],
            ['Advice', 'default choice', 'only for bounded data that must be read or changed together'],
        ]),
        tags('Tall-narrow', 'Flat-wide', 'Row size', 'Atomicity'),
    ),
    analogy('Tall = <strong>one index card per class attended</strong> filed by student and date. Wide = <strong>one big sheet per student</strong> with a '
            'box per date. The sheet is handy, but after years it no longer fits in one folder.'),
    tall_wide_anim(),
    real_world(
        scenario('Choosing for attendance',
                 p('Daily attendance for a 6-month course (~150 dates) is bounded, so a wide row per student is fine and gives the whole history in one get. '
                   'Proctoring events (thousands per attempt, unbounded across years) use a tall design.')),
    ),
    example(
        hsh('''
create 'att_tall', 'a'
put 'att_tall', '2401|20261001', 'a:s', 'P'
put 'att_tall', '2401|20261002', 'a:s', 'A'
put 'att_tall', '2402|20261001', 'a:s', 'P'
scan 'att_tall', {ROWPREFIXFILTER => '2401|'}
create 'att_flat', 'a'
put 'att_flat', '2401', 'a:20261001', 'P'
put 'att_flat', '2401', 'a:20261002', 'A'
put 'att_flat', '2402', 'a:20261001', 'P'
get 'att_flat', '2401'
'''),
        title='Example'),
    steps(
        ('Estimate maximum row size', 'Columns per row × cell size over the data\'s lifetime.'),
        ('Bounded and read together?', 'Wide is OK.'),
        ('Unbounded or appended forever?', 'Tall.'),
        ('Need atomic multi-column updates?', 'Keep those columns in one row.'),
        title='Steps'),
    crossq(
        ('What happens if a row grows to many GB?', 'It cannot be split, so its region cannot be split below that size; reads load huge results and can cause RegionServer memory pressure.'),
        ('Is there a limit on columns per row?', 'No hard limit, but the practical limit is the row size the region and clients can handle (keep rows to a few MB).'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('HBase has no secondary indexes. How do you query by a non-key column?', 'Secondary Access Paths', minutes=8, cards=[
    definition(
        defbox('Options when you need to find rows by something other than the row key:'),
        ul('<strong>Index table</strong> maintained by the application: key = indexed value (+ main key for uniqueness), value = main key or copied columns.',
           '<strong>Apache Phoenix</strong> secondary indexes: <code>CREATE INDEX</code> (global or local), maintained automatically.',
           '<strong>Coprocessors</strong> (server-side triggers) that update an index table on every put.',
           '<strong>External search</strong>: replicate data into Solr/Elasticsearch (e.g. via the HBase indexer) for full-text or multi-field search.',
           '<strong>Filters</strong> on a scan: fine for occasional or small-range queries only.'),
        tags('Index table', 'Phoenix index', 'Coprocessor', 'Elasticsearch', 'Dual write'),
    ),
    analogy('A dictionary is ordered by word. To find words by meaning you need a separate <strong>thesaurus</strong> that points back to the dictionary pages.'),
    index_table_anim(),
    real_world(
        scenario('Login by email',
                 p('The portal keys students by roll number. A small <code>students_by_email</code> table maps email → roll. Registration writes both; a nightly job '
                   'compares them and repairs any index rows a failed write left behind.')),
    ),
    example(
        hsh('''
create 'students', 'info'
create 'students_by_email', 'r'
put 'students', '2401', 'info:email', 'anuj@cdac.in'
put 'students_by_email', 'anuj@cdac.in', 'r:roll', '2401'
put 'students', '2402', 'info:email', 'aarshvi@cdac.in'
put 'students_by_email', 'aarshvi@cdac.in', 'r:roll', '2402'
# login: index lookup, then main-table lookup
get 'students_by_email', 'aarshvi@cdac.in'
get 'students', '2402'
'''),
        title='Example'),
    steps(
        ('Prefer Phoenix if you use SQL', 'Indexes kept consistent automatically.'),
        ('Otherwise write an index table', 'Write index first or main first consistently, and make the reader tolerate a stale index.'),
        ('Run a reconciliation job', 'Spark/MapReduce comparing both tables.'),
        ('For search, use Solr/Elasticsearch', 'Not HBase filters.'),
        title='Steps'),
    crossq(
        ('Which should be written first, the index or the main row?', 'Usually the main row first, then the index; a reader that finds an index entry should verify the main row still matches (and treat mismatches as stale).'),
        ('Global vs local Phoenix indexes?', 'Global indexes are separate tables (fast reads, extra write cost, cross-region writes); local indexes live in the same regions as the data (cheaper writes, reads must check every region).'),
    ),
]),
])
