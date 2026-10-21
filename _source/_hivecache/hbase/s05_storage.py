from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py

SECTION = dict(level='intermediate', title='Deletes, TTL & Column Families', questions=[

# ------------------------------------------------------------------ 21
Q('How do deletes work in HBase? What are delete markers (tombstones)?', 'Deletes & Tombstones', minutes=9, cards=[
    definition(
        defbox('HFiles are immutable, so a delete writes a <strong>delete marker</strong> (tombstone) with a timestamp. Reads skip cells masked by markers; '
               '<strong>major compaction</strong> physically removes both the markers and the deleted cells.'),
        table(['Marker', 'Created by', 'Masks'], [
            ['Delete', 'Java <code>Delete.addColumn</code>', 'one version of a column'],
            ['DeleteColumn', "shell <code>delete 't','r','cf:q'</code>", 'all versions of a column with ts ≤ marker ts'],
            ['DeleteFamily', "shell <code>deleteall 't','r'</code>", 'all columns of a family with ts ≤ marker ts'],
        ]),
        p('Because markers mask everything up to their timestamp, a later put with an <strong>older explicit timestamp</strong> stays invisible until major '
          'compaction removes the marker. A <code>RAW =&gt; true</code> scan shows markers and masked cells.', top=True),
        tags('Delete marker', 'Tombstone', 'DeleteColumn', 'DeleteFamily', 'Major compaction', 'RAW scan'),
    ),
    analogy('Pasting a <strong>"withdrawn" slip</strong> over pages in a bound register. Readers skip them; the pages are only physically removed when the '
            'register is rebound (major compaction).'),
    delete_marker_anim(),
    real_world(
        scenario('Debugging "disappearing" data',
                 p('A batch job re-loaded old data with explicit (old) timestamps after a deleteall, and the rows did not appear. A RAW scan showed a DeleteFamily marker '
                   'newer than the loaded cells. Fix: re-load with current timestamps, or run a major compaction before re-loading.')),
    ),
    example(
        hsh('''
create 'attempts', {NAME => 'a', VERSIONS => 3}
put 'attempts', 'SQL|2401', 'a:status', 'started'
put 'attempts', 'SQL|2401', 'a:status', 'submitted'
put 'attempts', 'SQL|2401', 'a:score', '82'
delete 'attempts', 'SQL|2401', 'a:status'
get 'attempts', 'SQL|2401'
scan 'attempts', {RAW => true, VERSIONS => 5}
deleteall 'attempts', 'SQL|2401'
# a put with an OLD explicit timestamp is still masked by the DeleteFamily marker
put 'attempts', 'SQL|2401', 'a:score', '90', 1791952200000
get 'attempts', 'SQL|2401'
scan 'attempts', {RAW => true, VERSIONS => 5}
'''),
        title='Example'),
    steps(
        ('Delete with the narrowest scope', 'Column rather than row when possible.'),
        ('Avoid explicit timestamps around deletes', 'They interact with markers in surprising ways.'),
        ('Use TTL instead of mass deletes', 'Expiry needs no markers.'),
        ('Inspect with RAW scans', 'To see what is physically stored.'),
        title='Steps'),
    crossq(
        ('When is the space of deleted data freed?', 'At major compaction of the store; minor compactions keep markers because older files may still contain masked cells.'),
        ('What is KEEP_DELETED_CELLS?', 'A family setting that keeps deleted cells (subject to VERSIONS/TTL) so time-range reads before the delete still see them. See the question on time travel.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How does TTL work in HBase? What is MIN_VERSIONS?', 'TTL & MIN_VERSIONS', minutes=7, cards=[
    definition(
        defbox('<code>TTL</code> (seconds) is a column-family setting: a cell expires TTL seconds after its <strong>timestamp</strong>. Expired cells are invisible to '
               'reads immediately and are removed during compaction. No delete markers are written.',
               '<code>MIN_VERSIONS</code> keeps at least that many of the newest versions of each column even after they expire, so you can expire history but keep the '
               'last known value. A per-cell TTL can also be set on a Put in the Java API (<code>put.setTTL(ms)</code>).'),
        tags('TTL', 'MIN_VERSIONS', 'Expiry', 'Compaction', 'Cell TTL'),
    ),
    analogy('<strong>Milk cartons with expiry dates</strong>: the shop stops selling them on the date without anyone writing "deleted" on them, and the next '
            'clean-up throws them out. MIN_VERSIONS is a rule to always keep the newest carton on display.'),
    ttl_anim(),
    real_world(
        scenario('OTPs and sensor history',
                 ul('<code>otp</code> family with <code>TTL =&gt; 300</code>: codes vanish after 5 minutes.',
                    'Sensor readings with <code>TTL =&gt; 30 days</code> and <code>MIN_VERSIONS =&gt; 1</code> on a "last value" column, so a sensor that stops reporting still shows its last reading.')),
    ),
    example(
        hsh('''
create 'otp', {NAME => 'c', TTL => 300}
put 'otp', '9820012345', 'c:code', '482913'
get 'otp', '9820012345'
!sleep 301
get 'otp', '9820012345'
create 'sensor_last', {NAME => 'v', TTL => 60, VERSIONS => 3, MIN_VERSIONS => 1}
put 'sensor_last', 'S01', 'v:temp', '24.5'
put 'sensor_last', 'S01', 'v:temp', '25.3'
!sleep 120
# both versions are older than the TTL, but MIN_VERSIONS keeps the newest one
get 'sensor_last', 'S01', {COLUMN => 'v:temp', VERSIONS => 3}
describe 'otp'
'''),
        title='Example'),
    steps(
        ('Put data with different lifetimes in different families', 'TTL is per family.'),
        ('Set TTL at create or with alter', "<code>alter 't', {NAME =&gt; 'c', TTL =&gt; 300}</code>"),
        ('Add MIN_VERSIONS when the last value must survive', 'Usually 1.'),
        title='Steps'),
    crossq(
        ('Is TTL measured from insert time?', 'From the cell\'s timestamp, which is normally the write time. Writing with an old explicit timestamp can make data expire immediately.'),
        ('Does an expired cell free disk space immediately?', 'No, only when its HFile is compacted.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('What is KEEP_DELETED_CELLS? How do you read data "as of" an earlier time?', 'Time Travel & KEEP_DELETED_CELLS', minutes=8, cards=[
    definition(
        defbox('Every cell has a timestamp, so reads can ask for the state of data at an earlier time with <code>TIMERANGE =&gt; [min, max)</code> or '
               '<code>TIMESTAMP =&gt; t</code>, provided the old versions are still kept (VERSIONS, TTL).',
               'Normally a delete hides older versions even for time-range reads. With <code>KEEP_DELETED_CELLS =&gt; true</code> on the family, deleted cells are retained '
               'and a time-range read whose range ends <strong>before the delete</strong> still returns them. Major compaction also keeps them (until VERSIONS/TTL '
               'remove them). Useful for audit, recovery and consistent historical snapshots.'),
        tags('KEEP_DELETED_CELLS', 'TIMERANGE', 'Point-in-time read', 'Audit', 'Recovery'),
    ),
    analogy('A register with the policy "<strong>never tear out pages</strong>, even withdrawn ones". Today\'s reader sees only valid entries, but an auditor can '
            'ask "show me the register as it was on 10 October" and see everything that existed then.'),
    keep_deleted_anim(),
    real_world(
        scenario('Recovering an accidental delete',
                 p('A coordinator deleted a batch\'s marks by mistake at 15:05. The marks family had <code>KEEP_DELETED_CELLS</code> and VERSIONS 5, so a scan with '
                   '<code>TIMERANGE</code> ending at 15:04 retrieved the data, which was re-inserted.')),
    ),
    example(
        hsh('''
create 'audit', {NAME => 'd', VERSIONS => 5, KEEP_DELETED_CELLS => true}
put 'audit', 'SQL|2401', 'd:status', 'started'
put 'audit', 'SQL|2401', 'd:status', 'submitted'
delete 'audit', 'SQL|2401', 'd:status'
get 'audit', 'SQL|2401'
# as of just before the delete (10:00:00.003); the end of TIMERANGE is exclusive
get 'audit', 'SQL|2401', {COLUMN => 'd:status', TIMERANGE => [0, 1791952200003], VERSIONS => 5}
'''),
        title='Example'),
    steps(
        ('Enable on families that need audit/recovery', "<code>alter 't', {NAME =&gt; 'd', KEEP_DELETED_CELLS =&gt; true}</code>"),
        ('Keep enough versions', 'VERSIONS bounds how much history survives.'),
        ('Bound storage with TTL', 'Deleted cells still use disk.'),
        ('Read history with TIMERANGE', 'End the range before the delete.'),
        title='Steps'),
    crossq(
        ('Does KEEP_DELETED_CELLS make normal reads return deleted data?', 'No: normal reads (no time range) still hide deleted cells.'),
        ('What are HBase snapshots then?', 'A table-level, point-in-time copy of the file list (no data copy), used for backup, cloning and export (ExportSnapshot). Different from cell versions.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How should you design column families? Why should there be few of them?', 'Column Family Design', minutes=8, cards=[
    definition(
        defbox('A column family is a <strong>physical</strong> unit: in each region it is a separate <strong>Store</strong> with its own MemStore and HFiles, and its own '
               'settings. Guidelines from the HBase reference guide:'),
        ul('Use <strong>1–3 families</strong>. Flushes and compactions happen per region; a small family is flushed along with a big one, producing many tiny files.',
           'Families with very different sizes in the same table make scans of the small family slow (spread over many regions).',
           'Group columns <strong>read together</strong> and columns with the <strong>same lifetime/settings</strong> (TTL, VERSIONS, compression).',
           'Use <strong>short names</strong> (often one letter): the family name is stored in every cell.'),
        tags('Column family', 'Store', 'MemStore per family', 'Flush', 'Short names'),
    ),
    analogy('Families are like <strong>separate filing cabinets</strong> per subject in every office. Each cabinet needs its own clerk and clean-up schedule, so '
            'having twenty cabinets for a few papers each creates a lot of overhead.'),
    cf_design_anim(),
    real_world(
        scenario('Two families, two lifetimes',
                 p('Table <code>students</code>: family <code>p</code> (profile, VERSIONS 3, kept forever) and family <code>e</code> (recent events, TTL 30 days, '
                   'compressed with ZSTD). Profile reads never touch the larger event files.')),
    ),
    example(
        hsh('''
create 'students', {NAME => 'p', VERSIONS => 3}, {NAME => 'e', TTL => 2592000, COMPRESSION => 'ZSTD'}
put 'students', '2401', 'p:name', 'Anuj'
put 'students', '2401', 'e:20261014T1000', 'login'
# read only the profile family: the event store is not touched
get 'students', '2401', {COLUMN => 'p'}
describe 'students'
'''),
        title='Example'),
    steps(
        ('Start with one family', 'Add a second only for different access or lifetime.'),
        ('Name families with one or two letters', 'Saves space in every cell.'),
        ('Set per-family options', 'VERSIONS, TTL, COMPRESSION, BLOOMFILTER.'),
        ('Avoid adding many families later', 'Each new family is another store in every region.'),
        title='Steps'),
    crossq(
        ('Can a get read just one family?', 'Yes, and it avoids reading the other stores entirely: <code>get \'t\', \'r\', {COLUMN =&gt; \'p\'}</code>.'),
        ('Do short qualifier names matter too?', 'Yes, qualifiers are also stored per cell; data block encoding (FAST_DIFF) and compression reduce but do not remove the cost.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What are compression, data block encoding, Bloom filters and block cache settings?', 'Storage Tuning Settings', minutes=8, cards=[
    definition(
        table(['Setting (per family)', 'Effect', 'Common choice'], [
            ['<code>COMPRESSION</code>', 'compresses HFile blocks on disk', 'SNAPPY or LZ4 (fast), ZSTD/GZ (smaller)'],
            ['<code>DATA_BLOCK_ENCODING</code>', 'encodes repeated key prefixes inside blocks', 'FAST_DIFF, or ROW_INDEX_V1 for faster random gets'],
            ['<code>BLOOMFILTER</code>', 'lets reads skip HFiles that do not contain the row (or row+column)', 'ROW (default); ROWCOL for column-specific gets'],
            ['<code>BLOCKSIZE</code>', 'unit of reading and caching', '64 KB default; smaller for random reads, larger for scans'],
            ['<code>BLOCKCACHE</code> / <code>IN_MEMORY</code>', 'cache blocks; higher cache priority', 'true / true only for small hot families'],
        ]),
        tags('Compression', 'Data block encoding', 'Bloom filter', 'Block size', 'BlockCache', 'BucketCache'),
    ),
    analogy('Compression is <strong>vacuum-packing</strong> boxes, Bloom filters are <strong>"not in this box" stickers</strong>, and the block cache is the '
            '<strong>desk drawer</strong> for papers you used recently.'),
    storage_tuning_anim(),
    real_world(
        scenario('Halving storage',
                 p('Switching an event family from no compression to ZSTD with FAST_DIFF encoding cut its HDFS footprint by about 70%, which also meant fewer '
                   'blocks to read per scan. Random-get latency on the profile family improved after enabling ROWCOL Bloom filters.')),
    ),
    example(
        hsh('''
create 'events', 'e'
alter 'events', {NAME => 'e', COMPRESSION => 'SNAPPY', DATA_BLOCK_ENCODING => 'FAST_DIFF', BLOOMFILTER => 'ROWCOL', BLOCKSIZE => 32768}
describe 'events'
'''),
        hq('''
major_compact 'events'      # rewrite existing HFiles with the new settings
''', 'Applying settings to existing data (real cluster)'),
        title='Example'),
    steps(
        ('Enable compression on every family', 'Native codecs (Snappy/LZ4/ZSTD) must be installed on all nodes.'),
        ('Add data block encoding for long keys', 'FAST_DIFF is a good default.'),
        ('Keep Bloom filters on', 'ROW for gets by row, ROWCOL for gets by row + column.'),
        ('Size the block cache', 'Off-heap BucketCache for large caches.'),
        title='Steps'),
    crossq(
        ('Why can compression make reads faster?', 'Fewer bytes are read from HDFS and more data fits in the cache; decompression with Snappy/LZ4 is cheap compared to disk I/O.'),
        ('When does a Bloom filter not help?', 'For scans over ranges (it answers "is this row/column here?" only) and when almost every HFile contains the requested rows.'),
    ),
]),
])
