from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml

SECTION = dict(level='intermediate', title='HDFS Read, Write & Operations', questions=[

# ------------------------------------------------------------------ 12
Q('Explain how a file is written to HDFS.', 'HDFS Write Path', minutes=9, cards=[
    definition(
        defbox('A write is coordinated by the NameNode but the data goes straight from the client to a <strong>pipeline of '
               'DataNodes</strong>. The client sends each packet once; the DataNodes forward it to each other.'),
        tags('Write Pipeline', 'Packet', 'ACK', 'DFSOutputStream', 'Lease'),
    ),
    write_pipeline(),
    explanation(
        ul('Data is buffered and split into <strong>packets</strong> (64 KB by default) placed on a <strong>data queue</strong>; '
           'sent packets move to an <strong>ack queue</strong> until every DataNode in the pipeline confirms them.',
           'If a DataNode in the pipeline fails, the pipeline is closed, unacknowledged packets are put back on the data queue, the '
           'failed node is removed and writing continues with the remaining nodes. The NameNode later re-replicates the block to restore the replication factor.',
           'The write succeeds once <code>dfs.namenode.replication.min</code> (default 1) replicas are written.',
           'Data written is not guaranteed visible to readers until the block completes or the writer calls <code>hflush()</code>/<code>hsync()</code>.'),
        title='Details Interviewers Ask'),
    crossq(
        ('Why a pipeline instead of the client writing 3 copies?', 'The client\'s network link would carry 3× the data. With a '
         'pipeline the client uploads once and the copies travel between DataNodes, usually only one hop crossing racks.'),
        ('What is the difference between hflush and hsync?', '<code>hflush()</code> guarantees the data has reached all DataNodes\' memory '
         'and is visible to new readers. <code>hsync()</code> also forces it to disk on the DataNodes.'),
        ('What happens if the client dies while writing?', 'It stops renewing its lease. Once the lease\'s hard limit expires, the NameNode '
         'performs lease recovery, finalising the last block at a length all replicas agree on, and closes the file.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('Explain how a file is read from HDFS.', 'HDFS Read Path', minutes=7, cards=[
    definition(
        defbox('The client gets block locations from the NameNode, then reads each block <strong>directly</strong> from the '
               '<strong>closest</strong> DataNode holding it, verifying checksums as it goes.'),
        tags('Read Path', 'DFSInputStream', 'Network Distance', 'Checksum', 'Short-circuit Read'),
    ),
    read_path(),
    explanation(
        table(['Distance', 'Example', 'Value'], [
            ['Same node', 'Task runs on the DataNode holding the block', '0'],
            ['Same rack, other node', 'Different server, same switch', '2'],
            ['Other rack, same data centre', 'Cross the core switch', '4'],
            ['Other data centre', 'Rare in HDFS', '6'],
        ], caption='HDFS network topology distances used to sort replicas'),
        title='How "Closest" Is Decided'),
    crossq(
        ('What is a short-circuit local read?', 'When the client is on the same machine as the block, it reads the block file directly '
         'from local disk via a shared file descriptor, bypassing the DataNode\'s TCP path. Enabled with <code>dfs.client.read.shortcircuit</code>.'),
        ('What does the DataNode do about corrupt blocks?', 'Clients report checksum failures, and a background <strong>block scanner</strong> '
         'verifies blocks periodically. Corrupt replicas are reported to the NameNode, which copies a healthy replica and deletes the bad one.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('What HDFS shell commands do you use most often?', 'HDFS Shell Commands', minutes=8, cards=[
    definition(
        defbox('<code>hdfs dfs</code> (or <code>hadoop fs</code>, which also works with other file systems such as S3) '
               'provides Unix-like commands. <code>hdfs dfsadmin</code> and <code>hdfs fsck</code> are for administrators.'),
        tags('hdfs dfs', 'hadoop fs', 'fsck', 'dfsadmin', 'put', 'get'),
    ),
    example(
        sh('''
hdfs dfs -mkdir -p /data/exams/2026                 # create directory tree
hdfs dfs -put marks.csv /data/exams/2026/          # local -> HDFS  (copyFromLocal)
hdfs dfs -get /data/exams/2026/marks.csv .         # HDFS -> local  (copyToLocal)
hdfs dfs -ls -R /data/exams                         # list recursively
hdfs dfs -cat /data/exams/2026/marks.csv | head     # print contents
hdfs dfs -tail /logs/app.log                        # last 1 KB of a file
hdfs dfs -du -s -h /data/exams                      # size (and space incl. replicas)
hdfs dfs -count -q -h /user/vineeta                 # dirs, files, bytes, quotas
hdfs dfs -mv /tmp/a.csv /data/                      # move / rename (metadata only)
hdfs dfs -cp /data/a.csv /backup/                   # copy (data is copied)
hdfs dfs -rm -r /tmp/old                            # delete (goes to trash if enabled)
hdfs dfs -getmerge /out/wordcount merged.txt        # merge part-files into one local file
hdfs dfs -chmod 750 /data/exams; hdfs dfs -chown vineeta:dbda /data/exams
hdfs dfs -setrep -w 2 /data/archive                 # change replication
hdfs dfs -appendToFile new.log /logs/app.log        # append
hdfs dfs -test -e /data/_SUCCESS && echo exists     # check existence in scripts
'''),
        title='Everyday Commands'),
    example(
        sh('''
hdfs dfsadmin -report                  # capacity, live/dead DataNodes
hdfs dfsadmin -safemode get            # is the NameNode in safe mode?
hdfs fsck / -list-corruptfileblocks    # find corrupt files
hdfs fsck /data -files -blocks -locations
hdfs dfsadmin -setSpaceQuota 10t /user/vineeta
hdfs dfsadmin -setQuota 100000 /user/vineeta   # max number of names
hdfs balancer -threshold 10            # even out disk usage across DataNodes
hdfs haadmin -getServiceState nn1      # active / standby
hadoop distcp hdfs://nn1/data hdfs://nn2/data   # parallel copy between clusters
'''),
        title='Administration'),
    crossq(
        ('<code>hadoop fs</code> vs <code>hdfs dfs</code>?', '<code>hadoop fs</code> is the generic FileSystem shell and works with any '
         'supported file system (<code>file://</code>, <code>s3a://</code>, <code>abfs://</code>). <code>hdfs dfs</code> is the same shell for HDFS. '
         '<code>hadoop dfs</code> is deprecated.'),
        ('Why is <code>-mv</code> fast but <code>-cp</code> slow?', 'A move within HDFS only changes metadata in the NameNode. A copy '
         'reads and rewrites every block.'),
        ('How do you copy a large dataset between clusters?', 'With <code>hadoop distcp</code>, which runs a map-only MapReduce job so many '
         'files are copied in parallel. <code>-update</code> copies only changed files.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('What is safe mode in HDFS?', 'Safe Mode', minutes=6, cards=[
    definition(
        defbox('<strong>Safe mode</strong> is a read-only state of the NameNode. Clients can list and read files, but no '
               'creates, deletes, renames or replication changes are allowed.',
               'The NameNode enters it automatically at <strong>start-up</strong> while it loads metadata and collects block '
               'reports. It leaves once a threshold of blocks (<code>dfs.namenode.safemode.threshold-pct</code>, default '
               '<strong>0.999</strong>) have their minimum replicas reported, plus a 30-second extension.'),
        tags('Safe Mode', 'Read-only', 'Block Reports', 'dfsadmin'),
    ),
    example(
        sh('''
hdfs dfsadmin -safemode get      # Safe mode is ON / OFF
hdfs dfsadmin -safemode enter    # e.g. before maintenance or saving the namespace
hdfs dfsadmin -saveNamespace     # (requires safe mode) write a fresh fsimage
hdfs dfsadmin -safemode leave
hdfs dfsadmin -safemode wait     # scripts: block until safe mode ends
'''),
        title='Commands'),
    real_world(
        scenario('Cluster stuck in safe mode after a restart',
                 ul('Check <code>hdfs dfsadmin -report</code>: are all DataNodes alive? If some did not start, blocks are missing.',
                    'Run <code>hdfs fsck / -list-corruptfileblocks</code> to see which files have no live replica.',
                    'Bring back the missing DataNodes. Leave safe mode manually only after deciding the missing data is acceptable '
                    '(and then delete or restore the corrupt files), otherwise you hide a real data-loss problem.')),
    ),
    crossq(
        ('A Spark job fails with <code>SafeModeException: Cannot create file</code>. Why?', 'The NameNode is in safe mode (recently '
         'restarted, or put there by an admin). Writes are rejected until it leaves safe mode.'),
    ),
]),

# ------------------------------------------------------------------ 16
Q('What is the small files problem in Hadoop? How do you solve it?', 'Small Files Problem', minutes=8, cards=[
    definition(
        defbox('A <strong>small file</strong> is one much smaller than the HDFS block size. Large numbers of them hurt HDFS and '
               'processing engines because <strong>each file and block is an object in NameNode memory</strong>, and engines typically '
               'create <strong>one task per file</strong>.'),
        tags('Small Files', 'NameNode Heap', 'Compaction', 'HAR', 'SequenceFile', 'CombineFileInputFormat'),
    ),
    small_files(),
    example(
        pyrun('''
BYTES = 150           # approx. NameNode heap per object
def cost(n_files, file_kb, block_mb=128):
    blocks = n_files * max(1, -(-file_kb // (block_mb * 1024)))
    objects = n_files + blocks
    return objects, objects * BYTES

for label, n, kb in [("one 1 GB file", 1, 1024 * 1024),
                     ("10,000 x 100 KB files", 10_000, 100),
                     ("10 million x 100 KB", 10_000_000, 100)]:
    objs, heap = cost(n, kb)
    print(f"{label:<24} objects={objs:>12,}  heap={heap / 1024**2:>9,.3f} MB  map tasks={objs - n:>11,}")
'''),
        title='Example: The Cost in Numbers'),
    explanation(
        table(['Fix', 'How'], [
            ['Prevent at ingestion', 'Buffer and write bigger files (Flume/Kafka Connect roll size, Spark <code>coalesce</code>/<code>repartition</code> before writing)'],
            ['Periodic compaction', 'A job that reads a partition\'s small files and rewrites them as a few large Parquet/ORC files'],
            ['Container formats', 'Pack many small files into a SequenceFile or Avro file (filename as key, content as value)'],
            ['Hadoop Archives (HAR)', '<code>hadoop archive -archiveName exams.har -p /data/small /data/archive</code>: fewer NameNode objects, read via <code>har://</code>'],
            ['Combine at read time', '<code>CombineFileInputFormat</code> / Hive <code>CombineHiveInputFormat</code> / Spark <code>maxPartitionBytes</code> pack many files into one split'],
            ['Table formats', 'Iceberg / Delta / Hudi have built-in compaction (<code>OPTIMIZE</code>, <code>rewrite_data_files</code>)'],
        ]),
        title='Solutions'),
    crossq(
        ('Where do small files come from in practice?', 'Streaming jobs writing every few seconds, Spark jobs with too many output '
         'partitions (e.g. 200 shuffle partitions × many date partitions), over-partitioned Hive tables, and IoT/log sources writing one file per event batch.'),
        ('How would you find small files?', '<code>hdfs dfs -count</code> per directory (files vs bytes), or analyse an fsimage dump '
         '(<code>hdfs oiv -p Delimited</code>) to compute file-size distributions per directory.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is data locality? Why is it important?', 'Data Locality', minutes=6, cards=[
    definition(
        defbox('<strong>Data locality</strong> means running a task on (or close to) the node that stores the data it processes, '
               'so the data is read from local disk instead of over the network. "Move computation to data."'),
        table(['Level', 'Meaning', 'Cost'], [
            ['Node-local (data-local)', 'Task runs on a DataNode holding the block', 'Cheapest: local disk read'],
            ['Rack-local', 'Task runs in the same rack as a replica', 'One switch hop'],
            ['Off-rack (any)', 'Task runs elsewhere', 'Crosses the core network'],
        ]),
        tags('Data Locality', 'Node-local', 'Rack-local', 'Delay Scheduling'),
    ),
    explanation(
        p('The YARN scheduler receives the preferred hosts and racks for each task from the ApplicationMaster. If no container '
          'is free on a preferred node, it may wait briefly (<strong>delay scheduling</strong>) before relaxing to rack-local and then any node. '
          'Spark exposes the same idea through <code>spark.locality.wait</code> (default 3 s).'),
        title='How It Is Achieved'),
    crossq(
        ('Does data locality apply when data is on S3?', 'No. Compute nodes do not store S3 data, so every read goes over the network. '
         'Cloud architectures rely on high network bandwidth and columnar formats instead.'),
        ('Why does locality matter less than it used to?', 'Data-centre networks became much faster (25–100 Gbps), while columnar formats '
         'and compression reduce bytes read. It still helps, but separation of storage and compute is now common.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('How do you recover accidentally deleted files in HDFS?', 'Trash & Snapshots', minutes=6, cards=[
    definition(
        defbox('<strong>Trash</strong>: if <code>fs.trash.interval</code> (minutes) is greater than 0, <code>hdfs dfs -rm</code> moves files '
               'to <code>/user/&lt;user&gt;/.Trash/Current</code> instead of deleting them. They are purged after the interval. '
               'The default is 0 (disabled); many clusters set 1440 (1 day).',
               '<strong>Snapshots</strong>: read-only, point-in-time copies of a directory. Creating one is instant and costs no '
               'extra space until files change, because only metadata is recorded.'),
        tags('Trash', 'fs.trash.interval', 'Snapshot', 'skipTrash', 'Backup'),
    ),
    example(
        sh('''
# Restore from trash
hdfs dfs -ls /user/vineeta/.Trash/Current/data/exams
hdfs dfs -mv /user/vineeta/.Trash/Current/data/exams/marks.csv /data/exams/

hdfs dfs -rm -skipTrash /tmp/huge.log      # bypasses trash: cannot be undone
hdfs dfs -expunge                          # empty trash now

# Snapshots
hdfs dfsadmin -allowSnapshot /data/exams
hdfs dfs -createSnapshot /data/exams before_cleanup
hdfs dfs -ls /data/exams/.snapshot/before_cleanup
hdfs dfs -cp /data/exams/.snapshot/before_cleanup/marks.csv /data/exams/
hdfs snapshotDiff /data/exams before_cleanup .
'''),
        title='Commands'),
    crossq(
        ('Is replication a backup?', 'No. Replication protects against hardware failure, but a delete or a buggy job that overwrites data '
         'is applied to every replica. Use trash, snapshots and copies to another cluster (DistCp) for backup.'),
    ),
]),
])
