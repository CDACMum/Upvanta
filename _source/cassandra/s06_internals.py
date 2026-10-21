from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh, conf

SECTION = dict(level='advanced', title='Storage Engine Internals', questions=[

# ------------------------------------------------------------------ 26
Q('Explain the write path in Cassandra: commit log, memtable and SSTable.', 'Write Path', minutes=9, cards=[
    definition(
        defbox('On each replica a write goes through these steps:'),
        ul('<strong>Commit log</strong>: the mutation is appended to a sequential, durable log on disk (for crash recovery). '
           '<code>commitlog_sync: periodic</code> (default, fsync every 10 s) or <code>batch</code>/<code>group</code> for stricter durability.',
           '<strong>Memtable</strong>: the mutation is applied to an in-memory, sorted structure for that table (trie-based in 5.0).',
           'The replica <strong>acknowledges</strong> the write to the coordinator. No disk read and no in-place update happened.',
           '<strong>Flush</strong>: when the memtable reaches its size limit (or on <code>nodetool flush</code>, commit-log pressure), it is written to '
           'disk as an immutable <strong>SSTable</strong>, and the corresponding commit-log segments are recycled.',
           '<strong>Compaction</strong> later merges SSTables, keeping the newest version of each cell.'),
        tags('Commit log', 'Memtable', 'Flush', 'SSTable', 'Sequential I/O', 'Durability'),
    ),
    analogy('A busy exam controller notes every mark change in a <strong>bound diary</strong> (commit log) and on a <strong>whiteboard</strong> '
            '(memtable). When the whiteboard is full, it is photographed and archived as a <strong>printed sheet</strong> (SSTable) and wiped. If the '
            'power fails, the diary is used to rebuild the whiteboard.'),
    write_path_anim(),
    real_world(
        scenario('Why writes stay fast under load',
                 p('During an online exam, 5,000 candidates save answers every 30 seconds. Each save is a commit-log append plus a memtable insert on 3 '
                   'replicas, with no read of existing data, so write latency stays around a millisecond even as the table grows.')),
    ),
    example(
        sh('''
$ nodetool flush cdac attempts          # force memtable → SSTable
$ ls /var/lib/cassandra/data/cdac/attempts-*/
nb-1-big-Data.db  nb-1-big-Index.db  nb-1-big-Filter.db  nb-1-big-Statistics.db  ...
$ ls /var/lib/cassandra/commitlog/
CommitLog-8-1791952200123.log  CommitLog-8-1791952200456.log
''', 'Seeing the files (real node, illustrative)'),
        conf('''
commitlog_sync: periodic
commitlog_sync_period: 10000ms
memtable:
  configurations:
    default:
      class_name: TrieMemtable        # Cassandra 5.0
memtable_heap_space: 2048MiB
''', 'cassandra.yaml'),
        title='Example'),
    steps(
        ('Put the commit log on fast storage', 'Ideally separate from data directories on spinning disks; SSDs are standard today.'),
        ('Size memtables', 'Larger memtables → fewer, bigger SSTables, more memory.'),
        ('Flush before snapshots/backups', '<code>nodetool flush</code> then <code>nodetool snapshot</code>.'),
        ('Watch pending flushes/compactions', '<code>nodetool tpstats</code>, <code>nodetool compactionstats</code>.'),
        title='Steps'),
    crossq(
        ('What happens if a node crashes before a flush?', 'On restart it replays the commit log to rebuild the memtables. With periodic sync, up to the '
         'last sync period of writes may be lost on that node, but other replicas still have them.'),
        ('Is a write "durable" when the client gets success?', 'It is in the commit log (and memory) of as many replicas as the consistency level '
         'requires. Durability across machines comes from replication rather than from fsync on each write.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('Explain the read path. What roles do Bloom filters, the partition index and caches play?', 'Read Path', minutes=10, cards=[
    definition(
        defbox('A read on a replica combines all places where a partition\'s data may be:'),
        ul('<strong>Memtable</strong>: newest, not yet flushed data.',
           '<strong>Row cache</strong> (optional, off by default): whole partitions kept in memory.',
           '<strong>Bloom filter</strong> per SSTable: a probabilistic structure answering "definitely not here" or "maybe here", so most SSTables '
           'without the key are skipped without disk I/O (false-positive chance tuned by <code>bloom_filter_fp_chance</code>).',
           '<strong>Key cache / partition index</strong>: locate the partition\'s offset in the Data file (in 5.0, BTI trie indexes).',
           '<strong>Merge</strong>: data from the memtable and each SSTable is merged cell by cell; the newest timestamp wins and tombstones hide older data.',
           'Across replicas, the coordinator compares responses (digests) and triggers <strong>read repair</strong> if they differ.'),
        tags('Read path', 'Bloom filter', 'Key cache', 'Partition index', 'Row cache', 'Merge by timestamp', 'Digest'),
    ),
    analogy('Looking for a file in several cupboards. Each cupboard has a <strong>sticker list</strong> (Bloom filter) that says "not here" or '
            '"maybe here". You open only the "maybe" cupboards, use the cupboard\'s <strong>index card</strong> to find the exact shelf, and if you find '
            'several versions, you keep the one with the latest date.'),
    read_path_anim(),
    real_world(
        scenario('Why compaction strategy affects read latency',
                 p('A frequently updated profile table on STCS had rows spread over 12 SSTables, so p99 reads touched many files. Switching to '
                   'LeveledCompactionStrategy brought most reads down to 1–2 SSTables and halved p99 latency.')),
    ),
    example(
        cq('''
TRACING ON;
SELECT * FROM cdac.marks_by_student WHERE roll_no = 2401;
-- trace output (abridged, real node):
--  Executing single-partition query on marks_by_student
--  Acquiring sstable references
--  Bloom filter allows skipping sstable 7
--  Partition index with 0 entries found for sstable 5
--  Merged data from memtables and 2 sstables
--  Read 3 live rows and 0 tombstone cells
''', 'Tracing a read'),
        sh('''
$ nodetool tablestats cdac.marks_by_student | grep -E "SSTable count|Bloom filter|Local read latency|tombstones"
$ nodetool info | grep -i "key cache"
''', 'Checking read-path statistics'),
        title='Example'),
    steps(
        ('Trace slow queries', '<code>TRACING ON</code> in cqlsh: number of SSTables, tombstones, nodes involved.'),
        ('Check SSTables per read', '<code>nodetool tablehistograms</code>.'),
        ('Tune Bloom filters for read-heavy tables', 'Lower <code>bloom_filter_fp_chance</code> (more memory, fewer false positives).'),
        ('Pick compaction to reduce SSTables per read', 'LCS/UCS for read-heavy workloads.'),
        title='Steps'),
    crossq(
        ('Can a Bloom filter give a wrong "not present"?', 'No. Bloom filters can have false positives ("maybe" when absent) but never false negatives.'),
        ('Why is the row cache off by default?', 'It caches whole partitions on heap/off-heap and is invalidated by writes; it helps only small, hot, '
         'read-mostly partitions. The OS page cache and key cache are usually enough.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What is compaction? Compare the compaction strategies.', 'Compaction Strategies', minutes=10, cards=[
    definition(
        defbox('<strong>Compaction</strong> merges several SSTables into new ones, keeping only the newest version of each cell, dropping expired data '
               'and tombstones older than gc_grace_seconds, and reducing the number of files a read must check. It runs in the background and is '
               'configured per table.'),
        table(['Strategy', 'How it works', 'Best for', 'Trade-off'], [
            ['SizeTiered (STCS)', 'Merges SSTables of similar size', 'Write-heavy, insert-mostly', 'Rows spread over many files; needs up to 50% free disk'],
            ['Leveled (LCS)', 'Levels of non-overlapping SSTables, each 10× the previous', 'Read-heavy, frequent updates', 'More write I/O (write amplification)'],
            ['TimeWindow (TWCS)', 'STCS within each time window; old windows never mixed', 'Time-series with TTL', 'Poor with out-of-order writes or deletes'],
            ['Unified (UCS, 5.0)', 'One configurable strategy covering tiered↔leveled, sharded compactions', 'General purpose (recommended for new tables in 5.0)', 'Needs tuning knowledge for edge cases'],
        ]),
        tags('Compaction', 'STCS', 'LCS', 'TWCS', 'UCS', 'Write amplification', 'Space amplification'),
    ),
    analogy('Filing loose notes into folders. <strong>STCS</strong> merges piles when you have several of similar size; <strong>LCS</strong> keeps '
            'a strictly organised cabinet (more filing work, faster finding); <strong>TWCS</strong> keeps one box per week and throws away whole boxes '
            'when they are too old.'),
    compaction_anim(),
    real_world(
        scenario('One cluster, three strategies',
                 ul('<code>proctor_events</code> (append-only, 30-day TTL): TWCS with 1-day windows.',
                    '<code>profiles</code> (frequent updates, read-heavy): LCS.',
                    'New tables on Cassandra 5.0: UCS with defaults, tuned only if metrics show a problem.')),
    ),
    example(
        cql('''
CREATE TABLE profiles (roll_no int PRIMARY KEY, name text, city text)
  WITH compaction = {'class': 'LeveledCompactionStrategy', 'sstable_size_in_mb': 160};

ALTER TABLE profiles WITH compaction = {'class': 'UnifiedCompactionStrategy', 'scaling_parameters': 'T4'};

ALTER TABLE profiles WITH gc_grace_seconds = 432000;
'''),
        sh('''
$ nodetool compactionstats          # running and pending compactions
$ nodetool setcompactionthroughput 128   # MiB/s
$ nodetool compact cdac profiles    # major compaction (use rarely, especially with STCS)
''', 'Operating compaction (real node)'),
        title='Example'),
    steps(
        ('Classify the table', 'Insert-only, update-heavy or time-series with TTL.'),
        ('Pick the strategy', 'STCS / LCS / TWCS, or UCS on 5.0.'),
        ('Leave disk headroom', 'Especially for STCS (temporary space for the merged output).'),
        ('Monitor pending compactions', 'A growing backlog means more SSTables per read and slower queries.'),
        title='Steps'),
    crossq(
        ('Why is a major compaction with STCS discouraged?', 'It produces one huge SSTable that will not be compacted again for a long time, so '
         'tombstones and overwritten data in it linger.'),
        ('What is write amplification?', 'How many times a piece of data is rewritten to disk over its lifetime. LCS rewrites data at each level, so it has '
         'higher write amplification but fewer SSTables per read.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('What is a partitioner and a token? How are partitions distributed across nodes, and what are vnodes?', 'Partitioner, Tokens & Vnodes', minutes=10, cards=[
    definition(
        defbox('The <strong>partitioner</strong> hashes the partition key into a <strong>token</strong>. The default <code>Murmur3Partitioner</code> '
               'produces 64-bit tokens from -2<sup>63</sup> to 2<sup>63</sup>-1, spreading keys evenly regardless of their values. '
               '(<code>ByteOrderedPartitioner</code> keeps key order but causes hot spots; avoid it.)',
               'The token space is a <strong>ring</strong>; each node owns the ranges ending at its tokens. With <strong>virtual nodes (vnodes)</strong>, '
               'each node has many tokens (<code>num_tokens</code>, default 16 since 4.0, previously 256), so it owns many small ranges spread around the '
               'ring. This balances data, and when a node joins or leaves, all other nodes share the streaming work.'),
        tags('Partitioner', 'Murmur3', 'Token', 'Token range', 'Ring', 'Vnodes', 'num_tokens'),
    ),
    analogy('A circular running track divided into numbered segments. Each <strong>roll number is converted by a fixed formula</strong> into a '
            'position on the track, and whoever is responsible for that segment keeps the file. With vnodes, each person looks after many short '
            'segments spread around the track instead of one long one.'),
    token_ring_anim(),
    real_world(
        scenario('Even data without planning',
                 p('Roll numbers 2401, 2402, 2403… are consecutive, but their Murmur3 tokens are scattered across the whole ring, so consecutive students '
                   'land on different nodes and the load is spread evenly. This is also why <code>SELECT *</code> without WHERE returns rows in an '
                   'order that looks random: it is token order.')),
    ),
    example(
        cql('''
CREATE TABLE students (roll_no int PRIMARY KEY, name text);
INSERT INTO students (roll_no, name) VALUES (2401, 'Anuj');
INSERT INTO students (roll_no, name) VALUES (2402, 'Aarshvi');
INSERT INTO students (roll_no, name) VALUES (2403, 'Vineeta');
INSERT INTO students (roll_no, name) VALUES (2404, 'Rohit');
INSERT INTO students (roll_no, name) VALUES (2405, 'Riya');

SELECT roll_no, name, token(roll_no) FROM students;

-- reading a token range: how Spark and DSBulk split a full-table scan
SELECT roll_no, token(roll_no) FROM students WHERE token(roll_no) > 0;
'''),
        sh('''
$ nodetool getendpoints cdac students 2401    # which replicas hold roll_no 2401
10.0.1.12
10.0.2.11
10.0.1.11
$ nodetool ring | head                         # tokens owned by each node
$ nodetool describering cdac                   # token ranges → endpoints
''', 'Finding the replicas of a key (real cluster)'),
        title='Example'),
    steps(
        ('Keep Murmur3Partitioner', 'It is the default and changing it requires reloading all data.'),
        ('Use num_tokens = 16 for new clusters', 'With the token allocation algorithm (<code>allocate_tokens_for_local_replication_factor</code>).'),
        ('Check balance', '<code>nodetool status</code> "Owns (effective)" column.'),
        ('Locate a key', '<code>nodetool getendpoints ks table key</code>.'),
        title='Steps'),
    crossq(
        ('Why did num_tokens drop from 256 to 16?', '256 tokens per node made repairs and streaming slower and reduced availability in larger clusters '
         '(more nodes share ranges). With the newer token allocation algorithm, 16 tokens give good balance with less overhead.'),
        ('Does the token decide all replicas?', 'It decides the first replica (the node owning the range). The replication strategy then picks the remaining '
         'RF-1 replicas walking the ring, respecting racks and DCs.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What is an SSTable? Why are SSTables immutable and what does that imply?', 'SSTables & Immutability', minutes=8, cards=[
    definition(
        defbox('An <strong>SSTable</strong> (Sorted String Table) is Cassandra\'s on-disk data file set, written once by a memtable flush or a '
               'compaction and <strong>never modified</strong> afterwards. Partitions are stored in token order and rows in clustering order.',
               'Components: <code>Data.db</code> (compressed rows), the partition index (<code>Index.db</code>/<code>Summary.db</code>, or '
               '<code>Partitions.db</code>/<code>Rows.db</code> for the 5.0 BTI format), <code>Filter.db</code> (Bloom filter), '
               '<code>Statistics.db</code> (min/max timestamps, tombstone counts), <code>CompressionInfo.db</code>, <code>Digest</code>, <code>TOC.txt</code>.',
               'Immutability means writes never seek or lock, snapshots are instant (hard links) and files can be streamed safely. The costs are that '
               'updates and deletes create new versions and tombstones, and reads may have to merge several SSTables until compaction rewrites them.'),
        tags('SSTable', 'Immutable', 'Data.db', 'Bloom filter', 'BTI format', 'Snapshot', 'Hard link'),
    ),
    analogy('Printed <strong>monthly bulletins</strong>: once printed they are never edited. Corrections appear in the next bulletin, and readers '
            'check the latest bulletins first. Once a year the office prints a consolidated edition (compaction) and recycles the old ones.'),
    sstable_anim(),
    real_world(
        scenario('Backups in seconds',
                 p('Nightly backups run <code>nodetool snapshot</code>, which creates hard links to the current SSTables, taking seconds regardless of '
                   'data size. The snapshot directories are then copied to object storage at leisure, because the files will never change.')),
    ),
    example(
        sh('''
$ ls /var/lib/cassandra/data/cdac/marks_by_student-*/
oa-3-big-CompressionInfo.db  oa-3-big-Data.db  oa-3-big-Digest.crc32  oa-3-big-Filter.db
oa-3-big-Index.db  oa-3-big-Statistics.db  oa-3-big-Summary.db  oa-3-big-TOC.txt

$ tools/bin/sstablemetadata oa-3-big-Data.db | grep -E "Minimum timestamp|Maximum timestamp|Estimated droppable tombstones"
$ tools/bin/sstabledump oa-3-big-Data.db      # JSON view of partitions, rows, tombstones

$ nodetool snapshot -t before_upgrade cdac    # instant, hard links
''', 'Inspecting SSTables (real node, illustrative)'),
        title='Example'),
    steps(
        ('Find the table directory', '<code>data/&lt;keyspace&gt;/&lt;table&gt;-&lt;id&gt;/</code>.'),
        ('Inspect metadata', '<code>sstablemetadata</code>: timestamps, droppable tombstones, compression ratio.'),
        ('Dump contents for debugging', '<code>sstabledump</code> shows rows and tombstones as JSON.'),
        ('Back up via snapshots', '<code>nodetool snapshot</code>, then copy; <code>nodetool clearsnapshot</code> to free space.'),
        title='Steps'),
    crossq(
        ('If SSTables are immutable, how is disk space reclaimed?', 'Compaction writes new SSTables without overwritten data, expired data and purgeable '
         'tombstones, then deletes the old files.'),
        ('What does "oa" in the file name mean?', 'The SSTable format version: e.g. "nb" for Cassandra 4.x, "oa" for 5.0\'s big format and "da" for the 5.0 BTI format. '
         '<code>nodetool upgradesstables</code> rewrites files to the current version after an upgrade.'),
    ),
]),
])
