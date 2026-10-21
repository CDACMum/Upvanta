from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml

SECTION = dict(level='basic', title='HDFS Architecture', questions=[

# ------------------------------------------------------------------ 6
Q('What is HDFS? What are its key design goals?', 'What is HDFS', minutes=6, cards=[
    definition(
        defbox('<strong>HDFS (Hadoop Distributed File System)</strong> is a distributed file system that stores very large files '
               'as blocks spread across many machines, replicating each block for fault tolerance. It presents one file system '
               'namespace (<code>/user/vineeta/marks.csv</code>) even though the data lives on hundreds of disks.'),
        tags('HDFS', 'Distributed File System', 'Write Once Read Many', 'High Throughput', 'Fault Tolerance'),
    ),
    explanation(
        table(['Design goal', 'What it means'], [
            ['Very large files', 'Optimised for files of hundreds of MB to TBs, and millions (not billions) of files'],
            ['Streaming data access', '<strong>Write once, read many</strong>: data is written, then scanned many times from start to end'],
            ['High throughput over low latency', 'Reading a whole dataset fast matters more than fetching one record fast'],
            ['Hardware failure is normal', 'Detect failures and recover automatically through replication'],
            ['Move computation to data', 'Expose block locations so schedulers can run tasks where the data is'],
            ['Portability', 'Runs on commodity hardware and many OSs (Java)'],
        ]),
        title='Design Goals'),
    explanation(
        ul('Files can be <strong>appended to</strong> but not modified in place: there are no random writes.',
           'Only <strong>one writer</strong> per file at a time (enforced with a lease from the NameNode).',
           'Not POSIX-compliant: no <code>seek</code>-and-write, relaxed semantics for speed.'),
        title='Write Semantics'),
    crossq(
        ('Why is HDFS write-once?', 'It keeps replication and consistency simple: blocks never change after they are written, so '
         'replicas cannot diverge, and readers never see partially updated blocks. Updates are done by rewriting files or partitions '
         '(table formats like Hudi, Iceberg and Delta handle this for you).'),
        ('What is a lease in HDFS?', 'A time-limited lock the NameNode gives to the client writing a file, so no other client can '
         'write it at the same time. The client renews it while writing; if the client dies, the lease expires and the NameNode recovers the file.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('What are the roles of the NameNode and DataNode?', 'NameNode vs DataNode', minutes=8, cards=[
    comparison(
        table(['Aspect', 'NameNode (master)', 'DataNode (worker)'], [
            ['Stores', '<strong>Metadata</strong>: directory tree, file → block list, permissions, replication factor; block → DataNode map (in RAM only)', 'The actual <strong>data blocks</strong> as files on local disks, each with a checksum file'],
            ['Persistence', 'fsimage + edit log on disk', 'Block files under <code>dfs.datanode.data.dir</code>'],
            ['Talks to', 'Clients (metadata ops), DataNodes (instructions)', 'Clients (read/write data), other DataNodes (replication pipeline)'],
            ['Sends / receives', 'Receives heartbeats and block reports; replies with commands (replicate, delete, …)', 'Sends heartbeat every 3 s, full block report every 6 h, incremental reports on changes'],
            ['Hardware', 'Lots of RAM, reliable hardware (RAID for metadata disks)', 'Many large disks (JBOD, no RAID)'],
            ['How many', '1 active (+ standby/standbys in HA)', 'Tens to thousands'],
            ['If it fails', 'Without HA: whole file system unavailable', 'Its blocks are re-replicated from other copies'],
        ]),
        tags('NameNode', 'DataNode', 'Metadata', 'Heartbeat', 'Block Report', 'JBOD'),
    ),
    explanation(
        p('The NameNode does <strong>not</strong> store the block-to-DataNode mapping on disk. It rebuilds it at start-up from the block '
          'reports that DataNodes send. That is why a freshly started NameNode stays in <strong>safe mode</strong> until enough block '
          'reports arrive.'),
        p('Because the whole namespace lives in the NameNode\'s heap, the <strong>number of files and blocks</strong> (not the data size) '
          'limits how big a cluster can grow. A common rule of thumb is about <strong>150 bytes of heap per file, directory or block</strong>.', top=True),
        title='Key Point: Metadata Lives in RAM'),
    example(
        pyrun('''
# Rule of thumb: ~150 bytes of NameNode heap per object (file, directory or block)
BYTES_PER_OBJECT = 150
BLOCK_MB = 128

def namenode_heap(files, avg_file_mb, dirs):
    blocks_per_file = max(1, -(-avg_file_mb // BLOCK_MB))      # ceiling division
    objects = files + dirs + files * blocks_per_file
    return objects, objects * BYTES_PER_OBJECT / 1024**3

for files, size_mb in [(10_000_000, 512), (100_000_000, 1)]:
    objs, gb = namenode_heap(files, size_mb, dirs=files // 100)
    data_tb = files * size_mb / 1024**2
    print(f"{files:>11,} files x {size_mb:>3} MB = {data_tb:>7,.0f} TB data -> "
          f"{objs:>11,} objects, ~{gb:5.1f} GB heap")
'''),
        title='Example: Estimating NameNode Memory'),
    note('The second case stores 50× less data but needs more NameNode memory: this is the <strong>small files problem</strong>.', 'Notice'),
    crossq(
        ('Does a client\'s data pass through the NameNode?', 'No. The NameNode only returns block locations; data is streamed '
         'directly between the client and DataNodes.'),
        ('Why do DataNodes use JBOD instead of RAID?', 'HDFS already replicates blocks across machines, so RAID redundancy is wasted '
         'space. JBOD lets each disk work independently (no slowest-disk penalty), and one failed disk loses only its blocks.'),
        ('What commands does the NameNode send in heartbeat replies?', 'Replicate a block to another DataNode, delete (invalidate) a '
         'block, re-register or send a full block report, recover a block, or shut down.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What is a block in HDFS? Why is the block size so large?', 'HDFS Blocks', minutes=8, cards=[
    definition(
        defbox('A <strong>block</strong> is the unit in which HDFS stores and replicates data. Every file is split into blocks of '
               '<code>dfs.blocksize</code> (default <strong>128 MB</strong> in Hadoop 2/3, 64 MB in Hadoop 1). Each block is stored '
               'as an ordinary file on a DataNode\'s local disk.',
               'A file smaller than the block size occupies only its real size on disk: a 1 MB file uses 1 MB, not 128 MB. '
               'But it still costs one block entry in NameNode memory.'),
        tags('Block', 'dfs.blocksize', '128 MB', 'Seek Time', 'Input Split'),
    ),
    block_split(),
    explanation(
        ul('<strong>Less seek overhead</strong>: a disk seek takes ~10 ms; transferring 128 MB takes about a second. With big blocks, '
           'time is spent reading data, not seeking.',
           '<strong>Less NameNode memory</strong>: fewer blocks to track per TB of data.',
           '<strong>Fewer tasks</strong>: one map task per block, so fewer, longer tasks with less scheduling overhead.',
           '<strong>But not too large</strong>: too few blocks means too few parallel tasks and slower recovery of a lost block.'),
        title='Why Large Blocks?'),
    example(
        pyrun('''
import math

def plan(file_mb, block_mb=128, replication=3):
    blocks = math.ceil(file_mb / block_mb)
    last = file_mb - (blocks - 1) * block_mb
    print(f"{file_mb} MB file, {block_mb} MB blocks, replication {replication}")
    print(f"  blocks          : {blocks} ({blocks - 1} x {block_mb} MB + 1 x {last} MB)")
    print(f"  block replicas  : {blocks * replication}")
    print(f"  raw disk used   : {file_mb * replication} MB")
    print(f"  map tasks (default, 1 per block): {blocks}")

plan(500)
plan(500, block_mb=256)
'''),
        sh('''
# Set the block size for one upload (bytes), then inspect the blocks
hdfs dfs -D dfs.blocksize=268435456 -put results.csv /data/exams/
hdfs fsck /data/exams/results.csv -files -blocks -locations
'''),
        title='Example: Blocks for a 500 MB File'),
    crossq(
        ('If a 1 MB file is stored in HDFS, how much disk does it use?', '1 MB per replica (3 MB with replication 3). The block is not '
         'padded to 128 MB. The cost of small files is NameNode memory and task overhead, not disk space.'),
        ('Can different files have different block sizes?', 'Yes. Block size is set per file when it is written (<code>-D dfs.blocksize=…</code> '
         'or in the client API). Changing <code>dfs.blocksize</code> later does not affect existing files.'),
        ('Block vs input split?', 'A block is a <strong>physical</strong> division of stored data. An input split is a <strong>logical</strong> '
         'chunk of input given to one map task; a split may cross block boundaries so that a record is never cut in half. See the MapReduce section.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What is the replication factor? What is rack awareness?', 'Replication & Rack Awareness', minutes=8, cards=[
    definition(
        defbox('The <strong>replication factor</strong> is the number of copies kept of each block (<code>dfs.replication</code>, '
               'default <strong>3</strong>). It can be set per file.',
               '<strong>Rack awareness</strong> means the NameNode knows which rack each DataNode is in and places replicas so that '
               'the data survives the loss of a whole rack while keeping cross-rack traffic low.'),
        tags('Replication Factor', 'dfs.replication', 'Rack Awareness', 'Replica Placement', 'setrep'),
    ),
    rack_awareness(),
    example(
        sh('''
# Change replication of existing data (-w waits until done)
hdfs dfs -setrep -w 2 /data/archive/2023

# Replication is the 2nd column of -ls output for files
hdfs dfs -ls /data/exams

# Show the rack of each DataNode
hdfs dfsadmin -printTopology
'''),
        xml('''
<!-- hdfs-site.xml -->
<property>
  <name>dfs.replication</name>
  <value>3</value>
</property>
<!-- core-site.xml: script that maps a host/IP to a rack, e.g. /dc1/rack1 -->
<property>
  <name>net.topology.script.file.name</name>
  <value>/etc/hadoop/conf/rack-topology.sh</value>
</property>
''', 'Configuration'),
        title='Commands and Configuration'),
    crossq(
        ('Why is the default 3 and not 2?', 'With 2 copies, a second failure during the hours it takes to re-replicate loses data. 3 '
         'copies tolerate two simultaneous failures and allow the cross-rack placement (1 + 2) at reasonable cost.'),
        ('What happens if no rack script is configured?', 'Every node is placed in <code>/default-rack</code>. Replicas are still on '
         'different nodes, but all three could be in the same physical rack.'),
        ('Can the replication factor be higher than the number of DataNodes?', 'It can be set, but a DataNode never holds two replicas '
         'of the same block, so the blocks stay under-replicated (shown by <code>hdfs fsck</code>).'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What are fsimage and edit logs? What does the Secondary NameNode do?', 'fsimage, Edits & Secondary NN', minutes=8, cards=[
    definition(
        defbox('<strong>fsimage</strong>: a checkpoint file holding the complete namespace (directories, files, block IDs, '
               'permissions) at a point in time.',
               '<strong>Edit log (edits)</strong>: an append-only journal of every change since the last fsimage.',
               '<strong>Secondary NameNode</strong>: a helper that periodically merges fsimage + edits into a new fsimage '
               '(a <strong>checkpoint</strong>) so the edit log stays small and restarts stay fast.'),
        tags('fsimage', 'Edit Log', 'Checkpoint', 'Secondary NameNode', 'Standby NameNode'),
    ),
    checkpoint_anim(),
    warn('The Secondary NameNode is <strong>not a hot standby or backup NameNode</strong>. If the NameNode dies, the Secondary does '
         'not take over. At best its latest checkpoint can help recover metadata, losing changes made since.', 'Classic Trap'),
    explanation(
        ul('In an <strong>HA</strong> cluster there is no Secondary NameNode. The <strong>Standby NameNode</strong> performs checkpoints.',
           'Hadoop also has a <strong>Checkpoint Node</strong> and a <strong>Backup Node</strong> (keeps an in-memory, up-to-date copy), '
           'but they are rarely used; HA replaced them.',
           'Metadata directories (<code>dfs.namenode.name.dir</code>) are usually written to several disks, including an NFS mount, for safety.'),
        title='Points to Remember'),
    crossq(
        ('What happens at NameNode start-up?', 'It loads the latest fsimage into memory, replays the edit log on top, writes a new '
         'checkpoint, then waits in safe mode for DataNode block reports to rebuild the block-location map.'),
        ('Why not update the fsimage directly on every change?', 'The fsimage is large (GBs). Rewriting it per operation would be far too '
         'slow. Appending a small record to the edit log is fast and durable.'),
        ('How can you inspect an fsimage?', 'With the Offline Image Viewer: <code>hdfs oiv -p XML -i fsimage_000… -o fsimage.xml</code>. '
         'Edits use the Offline Edits Viewer (<code>hdfs oev</code>).'),
    ),
]),

# ------------------------------------------------------------------ 11
Q('What are the limitations of HDFS? When should you not use it?', 'HDFS Limitations', minutes=6, cards=[
    definition(
        table(['Limitation', 'Why', 'Alternative'], [
            ['Low-latency access', 'Optimised for throughput; every read goes NameNode → DataNode', 'HBase, Cassandra, an RDBMS, Redis'],
            ['Lots of small files', 'Each file/block costs NameNode heap; one task per file', 'Merge files; Parquet/ORC compaction; HAR'],
            ['Random / in-place updates', 'Write once; only appends', 'HBase, or table formats: Hudi, Iceberg, Delta Lake'],
            ['Multiple concurrent writers', 'One writer per file (lease)', 'Write separate files per writer'],
            ['NameNode scalability', 'Whole namespace in one JVM heap', 'Federation, or object stores (S3, ADLS, GCS)'],
            ['Storage cost of 3× replication', '200% overhead', 'Erasure coding for cold data'],
            ['Coupled storage and compute', 'Scaling storage means adding servers with CPUs too', 'Cloud object storage + elastic compute'],
        ]),
        tags('Small Files', 'Latency', 'Append-only', 'Object Storage'),
    ),
    crossq(
        ('Why are companies moving from HDFS to S3/ADLS?', 'Storage and compute scale and are billed separately, there are no NameNodes '
         'to run, durability is managed by the provider, and clusters can be shut down when idle. The trade-offs are no data locality and '
         'different consistency/rename semantics, which formats like Iceberg and Delta handle.'),
    ),
]),
])
