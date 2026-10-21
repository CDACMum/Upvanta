from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py, xml

SECTION = dict(level='advanced', title='Architecture & Internals', questions=[

# ------------------------------------------------------------------ 26
Q('Explain the architecture of HBase: HMaster, RegionServers, ZooKeeper and HDFS.', 'HBase Architecture', minutes=10, cards=[
    definition(
        table(['Component', 'Role'], [
            ['HMaster', 'Handles DDL (create/alter/drop), assigns regions to RegionServers, balances load, handles RegionServer failures. Active + backup masters; not on the read/write path.'],
            ['RegionServer', 'Serves regions: handles gets, puts and scans. Contains a WAL, a MemStore per family per region, a BlockCache, and runs flushes and compactions.'],
            ['Region', 'A contiguous range of rows [start key, end key) of one table; the unit of distribution.'],
            ['ZooKeeper', 'Holds the location of hbase:meta, master election, RegionServer liveness (ephemeral nodes).'],
            ['hbase:meta', 'System table listing every region and the server hosting it.'],
            ['HDFS', 'Stores HFiles and WAL files with 3× replication; RegionServers run next to DataNodes for data locality.'],
        ]),
        tags('HMaster', 'RegionServer', 'Region', 'ZooKeeper', 'hbase:meta', 'HDFS', 'Data locality'),
    ),
    analogy('A national exam board: the <strong>head office</strong> (HMaster) decides which <strong>regional office</strong> (RegionServer) handles which roll-number '
            'range (region), a <strong>directory</strong> (hbase:meta, located via ZooKeeper) tells you where to go, and all records are archived in the central '
            '<strong>vault</strong> (HDFS).'),
    architecture_anim(),
    real_world(
        scenario('Typical cluster layout',
                 ul('3 ZooKeeper nodes, 2 HMasters (active/backup) on master machines with the HDFS NameNodes.',
                    'Worker machines each run a DataNode and a RegionServer, so a region\'s files usually have a local replica.',
                    'Web UIs: Master on port 16010, RegionServers on 16030.')),
    ),
    example(
        hq('''
status                       # cluster summary: servers, dead servers, average load
status 'simple'              # per-RegionServer requests and regions
list_regions 'students'      # regions of a table, their servers and key ranges
balance_switch true          # enable the region balancer
''', 'Cluster commands (real cluster)'),
        xml('''
<property><name>hbase.cluster.distributed</name><value>true</value></property>
<property><name>hbase.rootdir</name><value>hdfs://namenode:8020/hbase</value></property>
<property><name>hbase.zookeeper.quorum</name><value>zk1,zk2,zk3</value></property>
''', 'hbase-site.xml'),
        title='Example'),
    steps(
        ('Run HDFS and ZooKeeper first', 'HBase depends on both.'),
        ('Configure hbase-site.xml', 'rootdir on HDFS, ZooKeeper quorum, distributed mode.'),
        ('Start masters and RegionServers', '<code>start-hbase.sh</code> with regionservers / backup-masters files.'),
        ('Verify', 'Master UI shows all RegionServers and regions online.'),
        title='Steps'),
    crossq(
        ('Does the client go through the HMaster for reads and writes?', 'No. Clients find regions via ZooKeeper and hbase:meta and talk directly to RegionServers; the master is only needed for DDL and region management.'),
        ('What happens if the active HMaster fails?', 'A backup master wins the ZooKeeper election and takes over; reads and writes continue meanwhile, only DDL and reassignment pause briefly.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What are regions? How do region splits and pre-splitting work?', 'Regions & Splitting', minutes=9, cards=[
    definition(
        defbox('A <strong>region</strong> holds a sorted, contiguous range of rows [start key, end key) of one table. A table starts with one region; when a region\'s '
               'largest store exceeds <code>hbase.hregion.max.filesize</code> (10 GB by default), it <strong>splits</strong> at a middle key into two daughters, '
               'and the master may move them to other RegionServers.',
               '<strong>Pre-splitting</strong> (<code>SPLITS =&gt; […]</code> or <code>NUMREGIONS</code> + <code>SPLITALGO</code>) creates many regions at table creation so '
               'early load is spread from day one. Regions can also be split or merged manually (<code>split</code>, <code>merge_region</code>), and the normaliser can do it automatically.'),
        tags('Region', 'Split', 'Pre-split', 'max.filesize', 'Merge', 'Normalizer'),
    ),
    analogy('A <strong>register that is split into two volumes</strong> when it gets too thick: A–M and N–Z. Opening several volumes in advance avoids every '
            'clerk waiting for the one thick register.'),
    region_anim(),
    real_world(
        scenario('Loading 50 crore rows',
                 p('A new table without pre-splits received all bulk writes on one region, which split repeatedly while overloaded. Recreating it with 32 pre-split regions '
                   '(on salt prefixes 00–31) spread the load evenly from the first minute.')),
    ),
    example(
        hsh('''
create 'students_split', 'info', {SPLITS => ['2410', '2420', '2430']}
describe 'students_split'
'''),
        hq('''
# four regions: ['', 2410) [2410, 2420) [2420, 2430) [2430, '')
list_regions 'students_split'
create 't2', 'f', {NUMREGIONS => 16, SPLITALGO => 'HexStringSplit'}   # for hex-hashed keys
split 'students', '2450'                 # manual split at a key
merge_region 'ENCODED_A', 'ENCODED_B'    # merge two adjacent regions
''', 'Region management (real cluster)'),
        title='Example'),
    steps(
        ('Know the key distribution', 'Salt prefixes, hash ranges or known ID ranges.'),
        ('Pre-split at creation', 'SPLITS or NUMREGIONS/SPLITALGO.'),
        ('Size regions sensibly', 'Typically 5–20 GB; avoid thousands of tiny regions.'),
        ('Let the balancer spread them', 'Check regions per server in the Master UI.'),
        title='Steps'),
    crossq(
        ('Can a single row be split across regions?', 'No: a row always belongs to exactly one region, which is why very wide rows are dangerous.'),
        ('Why are too many regions bad?', 'Each region has MemStores and metadata; thousands per server waste memory, cause many small flushes and slow down failover.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('Explain the HBase write path: WAL, MemStore and HFile.', 'Write Path', minutes=9, cards=[
    definition(
        ul('The client sends the put to the RegionServer hosting the row\'s region.',
           'The edit is appended to the <strong>Write-Ahead Log (WAL)</strong> on HDFS (one WAL per RegionServer, shared by its regions).',
           'The edit is written to the column family\'s <strong>MemStore</strong> (in-memory, sorted). The client is acknowledged.',
           'When a MemStore reaches <code>hbase.hregion.memstore.flush.size</code> (128 MB) or the server is under memory pressure, it is <strong>flushed</strong> to a new immutable <strong>HFile</strong> on HDFS.',
           'Once data is flushed, the corresponding WAL files can be archived.'),
        tags('WAL', 'MemStore', 'Flush', 'HFile', 'Durability', 'SKIP_WAL'),
    ),
    analogy('A bank teller records each transaction in a <strong>carbon-copy logbook</strong> (WAL) and on a <strong>daily sheet</strong> (MemStore). When the sheet '
            'is full, it is filed in the archive (HFile). If the teller collapses, the logbook lets a colleague rebuild the sheet.'),
    write_path_anim(),
    real_world(
        scenario('Write throughput tuning',
                 p('An ingestion job used <code>BufferedMutator</code> (batched writes) and kept the WAL on. Turning the WAL off (<code>Durability.SKIP_WAL</code>) was rejected '
                   'because a RegionServer crash would lose unflushed data; bulk loading HFiles was used for the one-time historical load instead.')),
    ),
    example(
        java('''
try (Connection conn = ConnectionFactory.createConnection(HBaseConfiguration.create());
     BufferedMutator mutator = conn.getBufferedMutator(TableName.valueOf("events"))) {
    for (Event e : events) {
        Put p = new Put(Bytes.toBytes(e.rowKey()));
        p.addColumn(Bytes.toBytes("e"), Bytes.toBytes("type"), Bytes.toBytes(e.type()));
        // p.setDurability(Durability.ASYNC_WAL);   // faster sync, small loss window
        mutator.mutate(p);                          // buffered client-side, sent in batches
    }
}   // close() flushes the remaining buffer
''', 'Batched writes (Java client)'),
        hq('''
flush 'events'          # force MemStores of the table to HFiles
''', 'Manual flush (real cluster)'),
        title='Example'),
    steps(
        ('Batch writes on the client', 'BufferedMutator or Table.put(List).'),
        ('Keep the WAL on for live data', 'Choose ASYNC_WAL only if a small loss window is acceptable.'),
        ('Size MemStores', 'Flush size and global memstore limits; watch for "blocking updates" warnings.'),
        ('Use bulk load for huge one-off loads', 'Bypasses the write path completely.'),
        title='Steps'),
    crossq(
        ('Why is the WAL on HDFS and not local disk?', 'If the RegionServer machine dies, other servers must read its WAL to recover; HDFS keeps it replicated and reachable.'),
        ('What are "blocking updates"?', 'When a region\'s MemStore grows beyond flush size × block multiplier (or too many HFiles wait for compaction), writes are blocked until flushes/compactions catch up.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('Explain the HBase read path: BlockCache, MemStore, HFiles and Bloom filters.', 'Read Path', minutes=9, cards=[
    definition(
        ul('A get or scan is served by the RegionServer of the region.',
           'Recent edits are in the <strong>MemStore</strong>; older data is in the store\'s <strong>HFiles</strong>.',
           '<strong>Bloom filters</strong> (per HFile) let the server skip files that cannot contain the row (or row+column).',
           'For the remaining files, the HFile <strong>block index</strong> locates the 64 KB data block; the <strong>BlockCache</strong> (on-heap LRU and/or off-heap BucketCache) is checked before reading from HDFS.',
           'Cells from MemStore and HFiles are <strong>merged</strong>: newest versions win, delete markers mask, VERSIONS/TTL applied.'),
        tags('BlockCache', 'BucketCache', 'Bloom filter', 'Block index', 'Merge', 'Short-circuit reads'),
    ),
    analogy('Looking up a file: first check the <strong>papers on your desk</strong> (BlockCache) and the <strong>in-tray</strong> (MemStore), then only the '
            '<strong>archive boxes whose label says "maybe here"</strong> (Bloom filter), and finally combine the pieces, keeping the latest corrections.'),
    read_path_anim(),
    real_world(
        scenario('Faster profile lookups',
                 p('Random gets on a 2 TB table were slow because most hit disk. Moving to an off-heap BucketCache of 32 GB per server and enabling HDFS short-circuit '
                   'local reads made the p99 latency drop from 40 ms to under 10 ms.')),
    ),
    example(
        xml('''
<property><name>hbase.bucketcache.ioengine</name><value>offheap</value></property>
<property><name>hbase.bucketcache.size</name><value>32768</value></property>  <!-- MB -->
<property><name>dfs.client.read.shortcircuit</name><value>true</value></property>
''', 'hbase-site.xml: caching and local reads'),
        hq('''
alter 'students', {NAME => 'p', BLOOMFILTER => 'ROWCOL', IN_MEMORY => 'true'}
''', 'Family settings that help reads (real cluster)'),
        title='Example'),
    steps(
        ('Keep Bloom filters on', 'ROW by default; ROWCOL for column-specific gets.'),
        ('Give reads enough cache', 'BucketCache off-heap for large caches without GC pauses.'),
        ('Keep HFiles per store low', 'Healthy compactions.'),
        ('Keep data local', 'Major compaction after region moves restores locality.'),
        title='Steps'),
    crossq(
        ('Do scans fill the block cache?', 'Large scans can evict useful cached blocks; set <code>CACHE_BLOCKS =&gt; false</code> (Java: scan.setCacheBlocks(false)) for one-off big scans.'),
        ('What is data locality and why does it matter?', 'Whether a region\'s HFile blocks have a replica on the same machine as the RegionServer; local reads avoid network hops (shown as "locality" in the UI).'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What are minor and major compactions? What is in an HFile?', 'Compactions & HFiles', minutes=9, cards=[
    definition(
        defbox('<strong>HFile</strong>: the immutable on-disk format of a store, written by flushes and compactions. It contains sorted <strong>data blocks</strong> '
               '(64 KB default), a multi-level <strong>block index</strong>, <strong>Bloom filter</strong> blocks, file info and a trailer.',
               '<strong>Minor compaction</strong> merges a few smaller HFiles of a store into a larger one (reducing files per read); it keeps delete markers. '
               '<strong>Major compaction</strong> rewrites <em>all</em> HFiles of a store into one, removing deleted cells, delete markers, expired (TTL) cells and versions '
               'beyond VERSIONS, and restoring data locality. Major compactions are I/O-heavy; many clusters disable the periodic one '
               '(<code>hbase.hregion.majorcompaction = 0</code>) and run them off-peak.'),
        tags('HFile', 'Minor compaction', 'Major compaction', 'Block index', 'Write amplification', 'Off-peak'),
    ),
    analogy('Minor compaction is <strong>stapling a few thin folders together</strong>; major compaction is <strong>re-filing the whole cabinet</strong> into '
            'one clean folder and shredding everything marked "withdrawn" or "expired".'),
    compaction_anim(),
    real_world(
        scenario('Compaction storms',
                 p('Automatic weekly major compactions started on all servers at the same time and slowed the student portal for hours. The team disabled time-based '
                   'major compaction and scheduled <code>major_compact</code> per table on Sunday nights.')),
    ),
    example(
        hq('''
compact 'events'            # request a minor compaction
major_compact 'events'      # request a major compaction
compaction_state 'events'   # NONE / MINOR / MAJOR / MAJOR_AND_MINOR
''', 'Compaction commands (real cluster)'),
        sh('''
$ hbase hfile -m -f hdfs:///hbase/data/default/events/<region>/e/<hfile>     # print HFile metadata
$ hbase hfile -p -f hdfs:///hbase/data/default/events/<region>/e/<hfile>     # print key/values
''', 'Inspecting an HFile'),
        title='Example'),
    steps(
        ('Monitor store file counts', 'Rising counts mean compaction is behind.'),
        ('Schedule major compactions off-peak', 'Or rely on minor + TTL where possible.'),
        ('Tune throughput', 'Compaction thread pools and throughput limits.'),
        ('Consider the compaction policy', 'Date-tiered compaction for time-series data with TTL.'),
        title='Steps'),
    crossq(
        ('Why does a major compaction improve reads?', 'Each store ends with one HFile, so reads check fewer files, and deleted/expired data no longer has to be skipped.'),
        ('What is date-tiered compaction?', 'A policy that groups HFiles by time window (like Cassandra\'s TWCS), good for time-series data with TTL.'),
    ),
]),
])
