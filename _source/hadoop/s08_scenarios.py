from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml

SECTION = dict(level='expert', title='Ecosystem, Admin & Scenarios', questions=[

# ------------------------------------------------------------------ 42
Q('Hadoop MapReduce vs Apache Spark: what are the differences?', 'MapReduce vs Spark', minutes=8, cards=[
    comparison(
        table(['Aspect', 'Hadoop MapReduce', 'Apache Spark'], [
            ['Processing model', 'Two fixed stages (map, reduce); multi-step logic = chain of jobs', 'DAG of many stages, optimised as a whole'],
            ['Intermediate data', 'Written to disk (and HDFS between jobs)', 'Kept in memory where possible, spills to disk'],
            ['Speed', 'Slower, especially for iterative and multi-step jobs', 'Often 10–100× faster for iterative/ML; typically several times faster for ETL'],
            ['APIs', 'Low-level Java map/reduce (Streaming for other languages)', 'DataFrames, SQL, Python/Scala/Java/R, Structured Streaming, MLlib'],
            ['Streaming', 'No (batch only)', 'Yes (micro-batch Structured Streaming)'],
            ['Fault tolerance', 'Re-run failed tasks; data on disk', 'Re-compute lost partitions from lineage; checkpoints'],
            ['Resource manager', 'YARN', 'YARN, Kubernetes, standalone'],
            ['Storage', 'HDFS (or any Hadoop FileSystem)', 'Not a storage system; reads HDFS, S3, JDBC, Kafka …'],
        ]),
        tags('Spark', 'MapReduce', 'In-memory', 'DAG', 'Lineage'),
    ),
    explanation(
        p('Spark <strong>does not replace Hadoop as a whole</strong>: it replaces MapReduce as the processing engine. A very common '
          'architecture is <strong>Spark on YARN reading and writing HDFS</strong>, with Hive Metastore for table definitions.'),
        title='Key Point'),
    crossq(
        ('Is MapReduce still used?', 'Rarely for new code. It still runs under the hood of some tools (DistCp, older Hive-on-MR jobs, '
         'Sqoop) and in legacy pipelines. Interviewers ask about it because its concepts (splits, shuffle, partitioning, combiners) map directly onto Spark.'),
        ('Why is MapReduce slow for iterative algorithms?', 'Each iteration is a separate job that reads input from HDFS and writes its '
         'result back to HDFS (with replication). Spark keeps the working set cached in memory across iterations.'),
    ),
]),

# ------------------------------------------------------------------ 43
Q('How do you join two datasets in MapReduce?', 'Joins in MapReduce', minutes=8, cards=[
    definition(
        defbox('<strong>Reduce-side join</strong>: both datasets are mapped to <code>(join_key, tagged_record)</code>; the shuffle brings '
               'matching keys together and the reducer combines them. Works for any sizes.',
               '<strong>Map-side join</strong>: the small dataset is loaded into memory in every mapper (Distributed Cache) and the big '
               'dataset is joined while it is read; no shuffle or reduce phase is needed.'),
        tags('Reduce-side Join', 'Map-side Join', 'Replicated Join', 'Distributed Cache', 'Broadcast Join'),
    ),
    joins_anim(),
    example(
        pyrun('''
from itertools import groupby

students = [("2401", "Anuj"), ("2402", "Vineeta"), ("2403", "Aarshvi")]
marks    = [("2401", "SQL", 82), ("2402", "SQL", 91), ("2401", "Spark", 77), ("2403", "Spark", 88)]

# ---- reduce-side join: tag, shuffle (sort by key), combine per key
mapped = [(r, "S", n) for r, n in students] + [(r, "M", f"{s}={m}") for r, s, m in marks]
print("reduce-side join:")
for roll, group in groupby(sorted(mapped), key=lambda x: x[0]):
    group = list(group)
    name = [v for _, t, v in group if t == "S"][0]
    for _, t, v in group:
        if t == "M":
            print("  ", roll, name, v)

# ---- map-side join: small table becomes an in-memory dict in every mapper
lookup = dict(students)
print("map-side join:")
for roll, subject, m in marks:
    print("  ", roll, lookup[roll], f"{subject}={m}")
'''),
        title='Example: Both Joins in Python'),
    crossq(
        ('What is the equivalent in Hive and Spark?', 'Hive: MAPJOIN (auto-converted when the small table is under '
         '<code>hive.auto.convert.join.noconditionaltask.size</code>). Spark: broadcast hash join (<code>broadcast(df)</code> or '
         '<code>spark.sql.autoBroadcastJoinThreshold</code>, default 10 MB).'),
        ('What is a bucketed / sort-merge map-side join?', 'If both datasets are bucketed and sorted on the join key into the same number '
         'of buckets, each mapper can merge matching buckets directly without a shuffle (Hive SMB join).'),
    ),
]),

# ------------------------------------------------------------------ 44
Q('What are the main Hadoop configuration files?', 'Configuration Files', minutes=7, cards=[
    definition(
        table(['File', 'Configures', 'Key properties'], [
            ['<code>hadoop-env.sh</code>', 'Environment for all daemons', '<code>JAVA_HOME</code>, heap sizes (<code>HADOOP_HEAPSIZE_MAX</code>), log dirs'],
            ['<code>core-site.xml</code>', 'Common settings for HDFS and clients', '<code>fs.defaultFS</code>, <code>hadoop.tmp.dir</code>, <code>fs.trash.interval</code>, <code>io.file.buffer.size</code>'],
            ['<code>hdfs-site.xml</code>', 'NameNode, DataNodes, HA', '<code>dfs.replication</code>, <code>dfs.blocksize</code>, <code>dfs.namenode.name.dir</code>, <code>dfs.datanode.data.dir</code>'],
            ['<code>yarn-site.xml</code>', 'ResourceManager and NodeManagers', '<code>yarn.resourcemanager.hostname</code>, <code>yarn.nodemanager.resource.memory-mb</code>, <code>yarn.nodemanager.aux-services=mapreduce_shuffle</code>'],
            ['<code>mapred-site.xml</code>', 'MapReduce jobs', '<code>mapreduce.framework.name=yarn</code>, task memory, compression, JobHistory address'],
            ['<code>workers</code> (Hadoop 2: <code>slaves</code>)', 'Hosts on which start scripts launch DataNodes/NodeManagers', 'One hostname per line'],
            ['<code>capacity-scheduler.xml</code>', 'YARN queues', 'Queue capacities, ACLs'],
        ]),
        tags('core-site.xml', 'hdfs-site.xml', 'yarn-site.xml', 'mapred-site.xml', 'fs.defaultFS'),
    ),
    example(
        xml('''
<!-- core-site.xml -->
<configuration>
  <property><name>fs.defaultFS</name><value>hdfs://master1:8020</value></property>
  <property><name>fs.trash.interval</name><value>1440</value></property>
</configuration>

<!-- hdfs-site.xml -->
<configuration>
  <property><name>dfs.replication</name><value>3</value></property>
  <property><name>dfs.namenode.name.dir</name><value>/data/1/nn,/nfs/nn</value></property>
  <property><name>dfs.datanode.data.dir</name><value>/data/1/dn,/data/2/dn,/data/3/dn</value></property>
</configuration>
''', 'Minimal cluster configuration'),
        sh('''
hdfs getconf -confKey dfs.blocksize      # value the client actually sees
hdfs getconf -namenodes
hadoop version
''', 'Check effective settings'),
        title='Example'),
    crossq(
        ('Precedence: which value wins?', 'Defaults (<code>*-default.xml</code> inside the jars) < site files < values set by the job '
         '(<code>-D</code>, <code>conf.set()</code>). A property marked <code>&lt;final&gt;true&lt;/final&gt;</code> in a site file cannot be overridden by jobs.'),
        ('Why list several directories in <code>dfs.namenode.name.dir</code>?', 'The NameNode writes its metadata to every listed directory; '
         'losing one disk then does not lose the namespace. An NFS mount adds an off-machine copy.'),
    ),
]),

# ------------------------------------------------------------------ 45
Q('Scenario: How many nodes do you need to store 500 TB of data?', 'Capacity Planning', minutes=8, cards=[
    definition(
        defbox('Capacity questions test whether you account for <strong>replication</strong>, <strong>growth</strong>, '
               '<strong>temporary/intermediate space</strong> and <strong>usable disk</strong> per node, and whether you state your assumptions.'),
        tags('Capacity Planning', 'Sizing', 'Replication', 'Growth', 'Compression'),
    ),
    example(
        pyrun('''
import math

raw_data_tb      = 500     # data today
growth_per_year  = 0.30    # 30% yearly growth
years            = 2
compression      = 0.5     # Parquet/ORC stores data at ~50% of the raw size
replication      = 3
temp_overhead    = 0.25    # shuffle spill, staging, tmp, logs (25%)
disks, disk_tb   = 12, 8   # per worker node
usable_fraction  = 0.75    # keep disks below ~75-80% full

data_future = raw_data_tb * (1 + growth_per_year) ** years
stored      = data_future * compression
on_disk     = stored * replication * (1 + temp_overhead)
per_node    = disks * disk_tb * usable_fraction
nodes       = math.ceil(on_disk / per_node)

print(f"data in {years} years        : {data_future:,.0f} TB")
print(f"after compression      : {stored:,.0f} TB")
print(f"x{replication} replication + temp  : {on_disk:,.0f} TB of raw disk")
print(f"usable per node        : {per_node:,.0f} TB  ({disks} x {disk_tb} TB x {usable_fraction:.0%})")
print(f"worker nodes needed    : {nodes}  (+ masters: 2 NN, 3 JN/ZK, 2 RM)")
# With RS-6-3 erasure coding on, say, 60% cold data:
cold = stored * 0.6
ec_disk = (cold * 1.5 + (stored - cold) * replication) * (1 + temp_overhead)
print(f"with EC on cold data   : {ec_disk:,.0f} TB -> {math.ceil(ec_disk / per_node)} nodes")
'''),
        title='Example: Worked Sizing'),
    interview(
        hl('Say your assumptions out loud (growth, compression, replication, headroom) before giving a number. The exact number matters less '
           'than a clear, defensible method. Also mention compute: the nodes must have enough cores and memory for the processing workload.', 'How to answer')),
    crossq(
        ('Why keep disks below ~75–80% full?', 'HDFS needs room for re-replication after failures, for the balancer to move blocks, and for '
         'temporary data. Nearly full DataNodes stop accepting writes and slow down the cluster.'),
    ),
]),

# ------------------------------------------------------------------ 46
Q('HDFS vs cloud object storage (S3, ADLS, GCS): is Hadoop still needed?', 'HDFS vs Cloud Storage', minutes=7, cards=[
    comparison(
        table(['Aspect', 'HDFS', 'Object storage (S3 / ADLS / GCS)'], [
            ['Storage and compute', 'Coupled: same servers', 'Separate: scale and pay independently'],
            ['Durability', 'Replication you manage (3×)', 'Provider-managed (e.g. S3: 11 nines)'],
            ['Data locality', 'Yes', 'No: all reads over the network'],
            ['Rename / directory ops', 'Atomic metadata operation', 'S3: copy + delete per object (slow, not atomic); ADLS Gen2 has hierarchical namespace'],
            ['Small files limit', 'NameNode heap', 'No NameNode, but many small objects still slow listing and reading'],
            ['Cost model', 'Hardware + operations team', 'Pay per GB-month + requests'],
            ['Access from Hadoop', '<code>hdfs://</code>', '<code>s3a://</code>, <code>abfs://</code>, <code>gs://</code> connectors'],
        ]),
        tags('S3', 'ADLS', 'GCS', 's3a', 'Separation of Storage and Compute', 'EMR', 'Dataproc'),
    ),
    explanation(
        p('Many organisations have moved new workloads to cloud object storage with Spark on managed services (AWS EMR, Azure HDInsight / '
          'Databricks, Google Dataproc) and table formats like <strong>Iceberg</strong>, <strong>Delta Lake</strong> and <strong>Hudi</strong>. '
          'But HDFS and YARN remain in large on-premise estates (banking, telecom, government) where data must stay in-house, and the '
          'Hadoop FileSystem API (<code>s3a</code>, <code>abfs</code>) is still how Spark talks to cloud storage.'),
        title='Where Hadoop Stands Today'),
    crossq(
        ('Why are Spark jobs writing to S3 sometimes slow at the end?', 'The classic output committer renames task output into the final '
         'directory; on S3 a rename is a copy of every object. Use the S3A committers (magic/staging) or a table format that commits via metadata.'),
    ),
]),

# ------------------------------------------------------------------ 47
Q('How is a Hadoop cluster secured?', 'Hadoop Security', minutes=6, cards=[
    definition(
        table(['Layer', 'Mechanism'], [
            ['Authentication', '<strong>Kerberos</strong> (<code>hadoop.security.authentication=kerberos</code>); users <code>kinit</code>, services use keytabs. Without it, Hadoop trusts whatever username the client claims ("simple" mode)'],
            ['Authorisation', 'HDFS POSIX-style permissions and ACLs (<code>hdfs dfs -setfacl</code>); YARN queue ACLs; Apache Ranger for central, fine-grained (table/column/row) policies'],
            ['Encryption at rest', 'HDFS <strong>encryption zones</strong> with keys in the Hadoop KMS'],
            ['Encryption in transit', 'RPC privacy (<code>hadoop.rpc.protection=privacy</code>), encrypted data transfer, HTTPS for web UIs'],
            ['Perimeter', 'Apache Knox gateway; edge nodes; firewalls'],
            ['Audit', 'NameNode audit log, Ranger audit, Atlas lineage'],
        ]),
        tags('Kerberos', 'Ranger', 'ACL', 'Encryption Zone', 'KMS', 'Knox'),
    ),
    example(
        sh('''
kinit vineeta@CDAC.LOCAL          # get a Kerberos ticket
klist                             # show tickets
hdfs dfs -setfacl -m user:anuj:r-x /data/exams
hdfs dfs -getfacl /data/exams
hdfs crypto -createZone -keyName examkey -path /data/secure
''', 'Commands'),
        title='Example'),
    crossq(
        ('A job fails with "GSS initiate failed / No valid credentials provided". Why?', 'No valid Kerberos ticket: the user did not '
         '<code>kinit</code>, the ticket expired, or a long-running service is missing its keytab/principal configuration.'),
    ),
]),

# ------------------------------------------------------------------ 48
Q('Troubleshooting scenarios commonly asked in interviews', 'Troubleshooting Scenarios', minutes=10, cards=[
    real_world(
        scenario('1. NameNode heap keeps growing and GC pauses are long',
                 ul('Check the object count (NameNode UI: files + blocks). Usually caused by small files.',
                    'Find directories with many small files, compact them, enforce name quotas (<code>-setQuota</code>), clean up old data.',
                    'Short term: raise NameNode heap; long term: federation or moving cold data out.')),
        scenario('2. "Could only be written to 0 of the 1 minReplication nodes"',
                 ul('No DataNode could accept the write: all DataNodes dead, disks full, or excluded.',
                    'Check <code>hdfs dfsadmin -report</code> (live nodes, remaining space), DataNode logs, and network/firewall to DataNode ports.')),
        scenario('3. <code>hdfs fsck /</code> reports missing or corrupt blocks',
                 ul('Missing: all replicas are on dead nodes. Bring those nodes/disks back first.',
                    'If truly lost, list affected files with <code>-list-corruptfileblocks</code>, restore them from source/backup, then '
                    '<code>hdfs fsck / -delete</code> (or <code>-move</code> to <code>/lost+found</code>).')),
        scenario('4. A job worked yesterday, today one reducer runs for hours',
                 ul('Compare per-task input records: a new hot key (skew), e.g. a default value like <code>NULL</code> or <code>unknown</code>.',
                    'Filter or salt it; use a combiner or map-side join.')),
        scenario('5. Spark on YARN application stuck in ACCEPTED',
                 ul('Queue full or AM limit reached, or requested container bigger than <code>yarn.scheduler.maximum-allocation-mb</code>.',
                    'Check the RM scheduler page, lower executor size/count, or submit to another queue.')),
        scenario('6. DataNodes are unevenly full after adding new nodes',
                 ul('New nodes receive only new data. Run <code>hdfs balancer -threshold 10</code> during off-peak hours with a bandwidth limit.')),
    ),
    interview(
        hl('For every scenario follow the same pattern: <strong>symptom → where you look (UI, logs, CLI) → root cause → immediate fix → '
           'prevention</strong>.', 'Answer structure')),
]),
])
