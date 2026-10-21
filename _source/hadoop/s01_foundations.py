from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml

SECTION = dict(level='beginner', title='Hadoop Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Hadoop and why was it created?', 'What is Hadoop', minutes=6, cards=[
    definition(
        defbox('<strong>Apache Hadoop</strong> is an open-source framework for <strong>storing</strong> and <strong>processing</strong> '
               'very large datasets across a <strong>cluster of ordinary (commodity) machines</strong>. It splits data into blocks, '
               'spreads them over many nodes, and sends the computation to the nodes where the data already sits.',
               'It grew out of two Google papers — the <em>Google File System</em> (2003) and <em>MapReduce</em> (2004) — and was '
               'built by Doug Cutting and Mike Cafarella for the Nutch search engine, then developed at Yahoo! and released as an '
               'Apache project.'),
        tags('Hadoop', 'Distributed Storage', 'Distributed Processing', 'Commodity Hardware', 'Scale-out'),
    ),
    explanation(
        p('By the mid-2000s, web companies had more data than any single server could store or scan in reasonable time. Buying '
          'bigger machines (<strong>scale-up</strong>) became very expensive and still hit a ceiling. Hadoop\'s answer was '
          '<strong>scale-out</strong>: add more cheap machines and let software handle the rest.'),
        table(['Problem', 'Hadoop\'s answer'], [
            ['Data too big for one disk', 'HDFS splits files into blocks spread across many disks'],
            ['Machines fail often at scale', 'Every block is replicated (default 3 copies); failed tasks are re-run elsewhere'],
            ['Moving terabytes over the network is slow', '<strong>Data locality</strong>: ship the small program to the data, not the data to the program'],
            ['Parallel programming is hard', 'MapReduce: write map and reduce functions; the framework handles distribution, retries and sorting'],
            ['Expensive specialised hardware', 'Runs on commodity servers; reliability comes from software'],
        ]),
        title='Why Hadoop?'),
    visual(
        svg('''<svg width="700" height="170" viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
<rect width="700" height="170" fill="#1e293b"/>
<text x="175" y="28" fill="#f59e0b" font-size="14" font-weight="bold" text-anchor="middle">Scale-up (vertical)</text>
<rect x="120" y="45" width="110" height="105" rx="8" fill="#f59e0b" fill-opacity="0.2" stroke="#f59e0b" stroke-width="2"/>
<text x="175" y="95" fill="#f1f5f9" font-size="12" text-anchor="middle">one huge server</text>
<text x="175" y="112" fill="#cbd5e1" font-size="11" text-anchor="middle">costly · has a limit</text>
<line x1="350" y1="15" x2="350" y2="160" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>
<text x="525" y="28" fill="#10b981" font-size="14" font-weight="bold" text-anchor="middle">Scale-out (horizontal) — Hadoop</text>
<g fill="#10b981" fill-opacity="0.2" stroke="#10b981" stroke-width="2">
<rect x="390" y="50" width="50" height="40" rx="6"/><rect x="450" y="50" width="50" height="40" rx="6"/><rect x="510" y="50" width="50" height="40" rx="6"/><rect x="570" y="50" width="50" height="40" rx="6"/>
<rect x="390" y="100" width="50" height="40" rx="6"/><rect x="450" y="100" width="50" height="40" rx="6"/><rect x="510" y="100" width="50" height="40" rx="6"/><rect x="570" y="100" width="50" height="40" rx="6"/></g>
<text x="660" y="100" fill="#10b981" font-size="20" text-anchor="middle">+</text>
<text x="525" y="160" fill="#cbd5e1" font-size="11" text-anchor="middle">many cheap nodes · add more as data grows</text>
</svg>''', 'Hadoop scales by adding commodity nodes rather than buying a bigger machine')),
    crossq(
        ('Is Hadoop a database?', 'No. Hadoop is a storage + processing framework. HDFS is a file system, not a database: there are no '
         'tables, indexes or transactions. Tools such as Hive and HBase add SQL tables or key-value access on top of it.'),
        ('What does "commodity hardware" mean? Is it cheap desktop PCs?', 'Standard rack servers from any vendor, not specialised '
         'high-end hardware. They still need decent RAM, disks and networking. "Commodity" means reliability is provided by '
         'Hadoop\'s software (replication, re-execution), not by expensive hardware.'),
        ('Is Hadoop still relevant today?', 'Its ideas are everywhere: Spark, Hive, Iceberg and cloud object stores all reuse HDFS/YARN '
         'concepts. Many banks, telecoms and government organisations still run on-premise Hadoop clusters, and Spark on YARN with HDFS '
         'is common. New projects increasingly use cloud storage (S3/ADLS/GCS) instead of HDFS, but interviewers still test these fundamentals.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What are the core components of Hadoop?', 'Core Components', minutes=6, cards=[
    definition(
        defbox('Apache Hadoop itself consists of four modules:'),
        table(['Component', 'Role', 'Master / Worker daemons'], [
            ['HDFS', 'Distributed, fault-tolerant storage', 'NameNode / DataNode (+ Secondary or Standby NameNode)'],
            ['YARN', 'Cluster resource management and job scheduling', 'ResourceManager / NodeManager'],
            ['MapReduce', 'Batch processing programming model that runs on YARN', 'Per-job ApplicationMaster + map/reduce tasks'],
            ['Hadoop Common', 'Shared libraries and utilities: configuration, RPC, file system abstraction, security', '—'],
        ]),
        tags('HDFS', 'YARN', 'MapReduce', 'Hadoop Common', 'NameNode', 'ResourceManager'),
    ),
    hdfs_arch(),
    explanation(
        p('Think of it as an operating system for a cluster: <strong>HDFS is the disk</strong>, <strong>YARN is the CPU and memory '
          'scheduler</strong>, and <strong>MapReduce (or Spark, Tez) is an application</strong> that runs on top.'),
        ul('<strong>Master-worker</strong> design everywhere: one master keeps the global picture, many workers do the heavy lifting.',
           'Workers are usually co-located: every worker machine runs a <strong>DataNode</strong> (storage) and a <strong>NodeManager</strong> '
           '(compute), which is what makes data locality possible.'),
        title='How They Fit Together'),
    interview(
        hl('Name the four modules, then the daemons of each, then say how a job uses them: data sits on DataNodes, the job asks the '
           'ResourceManager for containers on NodeManagers, and tasks run next to the data blocks.', 'Answer structure')),
    crossq(
        ('What does a typical worker node run?', 'A DataNode and a NodeManager. Master nodes run the NameNode(s), ResourceManager(s), '
         'JournalNodes, ZooKeeper and the MapReduce JobHistory Server.'),
        ('Can you use YARN without HDFS, or HDFS without MapReduce?', 'Yes. Spark on YARN can read from S3. HDFS is used by Spark, '
         'Hive, Presto/Trino and HBase without any MapReduce at all.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What is the Hadoop ecosystem? Name the main tools and their purpose.', 'Hadoop Ecosystem', minutes=7, cards=[
    definition(
        defbox('The <strong>Hadoop ecosystem</strong> is the set of projects built around HDFS and YARN to ingest, process, query, '
               'coordinate and govern big data.'),
        table(['Category', 'Tool', 'Purpose'], [
            ['SQL / warehouse', 'Hive', 'SQL (HiveQL) on files in HDFS; metastore holds table schemas'],
            ['SQL engines', 'Impala, Presto/Trino, Spark SQL', 'Faster interactive SQL on the same data'],
            ['Processing', 'Spark, Tez, MapReduce, Pig (legacy)', 'Batch and streaming computation'],
            ['NoSQL', 'HBase', 'Random, real-time read/write by row key on top of HDFS'],
            ['Ingestion', 'Sqoop (retired 2021), Flume, Kafka, NiFi', 'Move data from RDBMS, logs and streams into HDFS'],
            ['Coordination', 'ZooKeeper', 'Leader election, locks, configuration (used by HDFS HA, HBase, Kafka)'],
            ['Workflow', 'Oozie (legacy), Airflow', 'Schedule and chain jobs'],
            ['Security / governance', 'Kerberos, Ranger, Atlas, Knox', 'Authentication, authorisation, lineage, gateway'],
            ['Management', 'Ambari, Cloudera Manager', 'Install, configure and monitor the cluster'],
        ]),
        tags('Hive', 'HBase', 'Spark', 'Sqoop', 'Flume', 'ZooKeeper', 'Oozie', 'Ranger'),
    ),
    real_world(
        scenario('A typical on-prem pipeline (bank / telecom)',
                 p('Nightly <strong>Sqoop</strong> (or Spark JDBC) imports from Oracle into HDFS → <strong>Spark on YARN</strong> cleans '
                   'and joins the data → results stored as partitioned ORC/Parquet <strong>Hive</strong> tables → analysts query with '
                   '<strong>Impala/Trino</strong> → <strong>Airflow/Oozie</strong> schedules it all → <strong>Ranger</strong> controls '
                   'who can see which columns.')),
    ),
    crossq(
        ('HDFS vs HBase?', 'HDFS stores large files for sequential scans (write once, read many). HBase is a column-family NoSQL '
         'store <em>on top of</em> HDFS for fast random reads/writes of individual rows by key.'),
        ('Why was Sqoop retired and what replaced it?', 'Sqoop moved to the Apache Attic in 2021 due to inactivity. Teams now use '
         'Spark JDBC reads, Kafka Connect/Debezium for CDC, or managed tools such as AWS DMS, Airbyte and Fivetran.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What are the differences between Hadoop 1, Hadoop 2 and Hadoop 3?', 'Hadoop 1 vs 2 vs 3', minutes=7, cards=[
    comparison(
        table(['Feature', 'Hadoop 1.x', 'Hadoop 2.x', 'Hadoop 3.x'], [
            ['Resource management', 'JobTracker + TaskTracker (MapReduce only)', 'YARN (ResourceManager + NodeManager)', 'YARN + opportunistic containers, Timeline Service v2'],
            ['Processing engines', 'MapReduce only', 'MapReduce, Spark, Tez, … on YARN', 'Same, plus GPU/FPGA resource types'],
            ['Default block size', '64 MB', '128 MB', '128 MB'],
            ['NameNode availability', 'Single point of failure', 'HA with one Active + one Standby', 'HA with multiple Standby NameNodes'],
            ['Scaling the namespace', 'One NameNode', 'Federation (several namespaces)', 'Federation + Router-based federation'],
            ['Fault tolerance of data', '3× replication', '3× replication', 'Replication <strong>or erasure coding</strong> (~50% overhead)'],
            ['Resource slots', 'Fixed map slots and reduce slots', 'Flexible containers (memory + vcores)', 'Containers with custom resource types'],
            ['Java', 'Java 6', 'Java 7', 'Java 8+ (3.3+ also runs on Java 11)'],
            ['Default web UI ports', 'NameNode 50070', 'NameNode 50070', 'NameNode <strong>9870</strong>, DataNode 9864'],
        ]),
    ),
    explanation(
        p('The biggest change was <strong>Hadoop 2\'s YARN</strong>. In Hadoop 1, the JobTracker did both resource management '
          'and job monitoring for every job, which limited clusters to roughly 4,000 nodes and allowed only MapReduce. YARN split '
          'those duties: one ResourceManager for resources, and a separate ApplicationMaster per job. Any engine could now share the cluster.'),
        p('<strong>Hadoop 3\'s headline feature is erasure coding</strong>, which roughly halves the storage cost of fault tolerance for cold data.', top=True),
        title='Key Takeaways'),
    crossq(
        ('Why did the default block size grow from 64 MB to 128 MB?', 'Disks and networks got faster and datasets grew. Bigger blocks '
         'mean fewer blocks to track in NameNode memory and fewer, longer-running map tasks, while keeping seek time a small fraction of transfer time.'),
        ('What were the limitations of the JobTracker?', 'Single point of failure, a scalability ceiling (~4,000 nodes / 40,000 tasks), '
         'poor utilisation because map and reduce slots were fixed, and no support for non-MapReduce workloads.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('How is Hadoop different from a traditional RDBMS?', 'Hadoop vs RDBMS', minutes=6, cards=[
    comparison(
        table(['Aspect', 'RDBMS (MySQL, Oracle)', 'Hadoop (HDFS + engines)'], [
            ['Data size', 'GBs to a few TBs', 'TBs to PBs'],
            ['Data types', 'Structured', 'Structured, semi-structured (JSON, logs), unstructured (images, text)'],
            ['Schema', '<strong>Schema-on-write</strong>: must match before insert', '<strong>Schema-on-read</strong>: store raw, apply schema when reading'],
            ['Scaling', 'Mostly vertical (bigger server)', 'Horizontal (add nodes)'],
            ['Workload', 'OLTP: many small reads/writes, low latency', 'Batch analytics: full scans of huge data, high throughput'],
            ['Updates', 'Row-level UPDATE/DELETE, ACID transactions', 'Write once, read many; files are appended or rewritten'],
            ['Latency', 'Milliseconds', 'Seconds to hours'],
            ['Cost', 'Licensed software, premium hardware', 'Open source on commodity hardware'],
        ]),
        tags('Schema-on-read', 'Schema-on-write', 'OLTP', 'Batch', 'Throughput vs Latency'),
    ),
    real_world(
        scenario('They complement each other',
                 p('An online exam portal stores registrations and answers in <strong>MySQL</strong> (many small transactions). Every '
                   'night the data is copied into <strong>HDFS</strong>, where years of history and click-stream logs are analysed with '
                   'Spark/Hive. Hadoop does not replace the transactional database.')),
    ),
    crossq(
        ('What is schema-on-read? Give an advantage and a risk.', 'Data is stored as-is and a schema is applied only when a query reads '
         'it (e.g. a Hive external table over JSON files). Advantage: fast ingestion and flexibility to reinterpret data later. Risk: bad '
         'records are discovered only at query time.'),
    ),
]),
])
