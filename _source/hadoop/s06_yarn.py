from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml

SECTION = dict(level='advanced', title='YARN', questions=[

# ------------------------------------------------------------------ 33
Q('What is YARN? Explain its architecture.', 'YARN Architecture', minutes=8, cards=[
    definition(
        defbox('<strong>YARN (Yet Another Resource Negotiator)</strong> is Hadoop\'s cluster resource manager, introduced in Hadoop 2. '
               'It separates <strong>resource management</strong> (one global ResourceManager) from <strong>application management</strong> '
               '(one ApplicationMaster per application), so MapReduce, Spark, Tez, Flink and others can share one cluster.'),
        table(['Component', 'Runs', 'Responsibility'], [
            ['ResourceManager (RM)', 'Master (1 active + standby for HA)', 'Owns all cluster resources. <strong>Scheduler</strong>: allocates containers by queue policy. <strong>ApplicationsManager</strong>: accepts jobs, launches and restarts AMs'],
            ['NodeManager (NM)', 'Every worker', 'Launches and monitors containers, enforces memory/CPU limits, reports node health and resources, serves shuffle data (auxiliary service)'],
            ['ApplicationMaster (AM)', 'One container per application', 'Negotiates containers with the RM, launches tasks via NMs, tracks progress, handles task failures'],
            ['Container', 'On a NodeManager', 'A bundle of resources (memory MB + vcores, optionally GPUs) in which one task/executor runs'],
            ['Timeline / JobHistory Server', 'Master', 'History of finished applications'],
        ]),
        tags('YARN', 'ResourceManager', 'NodeManager', 'ApplicationMaster', 'Container', 'Scheduler'),
    ),
    example(
        sh('''
yarn node -list -all                         # NodeManagers and their state
yarn application -list                       # running applications
yarn application -status application_1760000000000_0042
yarn application -kill  application_1760000000000_0042
yarn logs -applicationId application_1760000000000_0042 | less   # aggregated logs
yarn queue -status default
# Web UI: http://<resourcemanager>:8088
''', 'YARN CLI'),
        title='Everyday Commands'),
    crossq(
        ('Why does each application get its own ApplicationMaster?', 'It removes the bottleneck of Hadoop 1\'s JobTracker, which tracked '
         'every task of every job. With per-application AMs the RM only allocates resources, so it scales to many thousands of nodes and '
         'each framework can implement its own task logic.'),
        ('Does the RM restart failed tasks?', 'No. The RM only restarts a failed <em>ApplicationMaster</em>. Task-level retries are the AM\'s job.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('Explain the flow of a job submitted to YARN.', 'YARN Job Flow', minutes=8, cards=[
    definition(
        defbox('From submission to completion: client → RM → AM container → AM negotiates task containers → NMs run tasks → AM reports and unregisters.'),
        tags('Job Submission', 'ApplicationMaster', 'Container Allocation', 'Heartbeat'),
    ),
    yarn_flow(),
    explanation(
        ul('Before submitting, the client copies the job resources (jar, config, split information) to a staging directory in HDFS so any node can fetch them.',
           'The AM sends heartbeats to the RM; resource requests and container grants travel on these heartbeats.',
           'Requests carry <strong>locality preferences</strong> (node, rack, any). The scheduler tries to honour them.',
           'If the AM itself fails, the RM launches a new attempt; MapReduce\'s AM can recover the tasks already completed.'),
        title='Details'),
    crossq(
        ('Where do the logs of a finished job go?', 'With log aggregation enabled (<code>yarn.log-aggregation-enable</code>), NodeManagers '
         'upload container logs to HDFS when the application ends; view them with <code>yarn logs -applicationId …</code>.'),
        ('What does "ACCEPTED: waiting for AM container to be allocated" mean?', 'The application is queued but there is no capacity in its '
         'queue (or AM resource limit reached) to start the AM. Check the queue\'s usage and <code>maximum-am-resource-percent</code>.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('What are the YARN schedulers? Compare FIFO, Capacity and Fair schedulers.', 'YARN Schedulers', minutes=8, cards=[
    definition(
        defbox('The <strong>Scheduler</strong> inside the ResourceManager decides which application gets which containers. It is '
               'pluggable via <code>yarn.resourcemanager.scheduler.class</code>. Apache Hadoop\'s default is the <strong>Capacity Scheduler</strong>.'),
        tags('FIFO Scheduler', 'Capacity Scheduler', 'Fair Scheduler', 'Queue', 'Preemption'),
    ),
    comparison(
        table(['Aspect', 'FIFO', 'Capacity', 'Fair'], [
            ['Idea', 'First come, first served', 'Hierarchical queues each guaranteed a % of the cluster', 'All running apps get an equal (weighted) share over time'],
            ['Small job behind a big job', 'Waits until the big job finishes', 'Runs in its own queue\'s capacity', 'Gets its fair share almost immediately'],
            ['Idle capacity', '—', 'Queues can borrow up to <code>maximum-capacity</code> (elasticity)', 'Shared among active apps'],
            ['Multi-tenancy', 'No', 'Yes: per-team queues, user limits, ACLs', 'Yes: pools/queues with weights and min shares'],
            ['Preemption', 'No', 'Yes (reclaim borrowed capacity)', 'Yes'],
            ['Typical use', 'Test / single user', 'Default in Apache Hadoop; shared enterprise clusters', 'Was CDH\'s default; interactive + batch mix'],
        ]),
    ),
    example(
        xml('''
<!-- capacity-scheduler.xml: two teams share the cluster 70/30 -->
<property><name>yarn.scheduler.capacity.root.queues</name><value>etl,analytics</value></property>
<property><name>yarn.scheduler.capacity.root.etl.capacity</name><value>70</value></property>
<property><name>yarn.scheduler.capacity.root.analytics.capacity</name><value>30</value></property>
<!-- analytics may grow to 50% when etl is idle -->
<property><name>yarn.scheduler.capacity.root.analytics.maximum-capacity</name><value>50</value></property>
''', 'capacity-scheduler.xml'),
        sh('''
spark-submit --master yarn --queue analytics report.py
mapred streaming -D mapreduce.job.queuename=etl ...
yarn rmadmin -refreshQueues          # apply queue changes without restart
''', 'Submitting to a queue'),
        title='Example: Queues'),
    crossq(
        ('What is preemption?', 'When a queue is below its guaranteed capacity because another queue borrowed resources, the RM can kill '
         'containers of the borrowing queue to give capacity back. The killed tasks are retried later.'),
    ),
]),

# ------------------------------------------------------------------ 36
Q('What is the difference between Spark client mode and cluster mode on YARN?', 'Spark on YARN: Client vs Cluster', minutes=7, cards=[
    definition(
        defbox('With <code>--master yarn</code>, Spark executors always run in YARN containers. <code>--deploy-mode</code> decides '
               'where the <strong>driver</strong> runs: on the submitting machine (<strong>client</strong>, the default) or inside the '
               'YARN ApplicationMaster (<strong>cluster</strong>).'),
        tags('Spark on YARN', 'deploy-mode', 'Driver', 'Executor', 'ApplicationMaster'),
    ),
    spark_yarn_modes(),
    example(
        sh('''
spark-submit --master yarn --deploy-mode cluster \\
  --num-executors 10 --executor-cores 4 --executor-memory 8g \\
  --driver-memory 4g --queue etl \\
  --conf spark.dynamicAllocation.enabled=true \\
  daily_marks_etl.py --date 2026-10-13
''', 'spark-submit'),
        title='Example'),
    comparison(
        table(['Aspect', 'Client mode', 'Cluster mode'], [
            ['Driver location', 'Submitting machine', 'AM container in the cluster'],
            ['Output / logs', 'In your terminal', 'YARN logs'],
            ['Client must stay connected', 'Yes', 'No'],
            ['Network', 'Driver ↔ executors traffic crosses to the client machine', 'All inside the cluster'],
            ['Use for', 'spark-shell, pyspark, notebooks, debugging', 'Production, scheduled (Airflow) jobs'],
        ]),
    ),
    crossq(
        ('Can spark-shell run in cluster mode?', 'No. Interactive shells need the driver locally, so they only support client mode.'),
        ('Why does an executor ask YARN for more memory than <code>--executor-memory</code>?', 'YARN containers must also fit off-heap '
         'overhead: <code>spark.executor.memoryOverhead</code> = max(384 MB, 10% of executor memory). An 8g executor requests about 8.8 GB, rounded up to the scheduler\'s allocation increment.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('How do you size YARN containers? Why are containers killed for exceeding memory?', 'Container Sizing', minutes=9, cards=[
    definition(
        table(['Property', 'Meaning', 'Default'], [
            ['<code>yarn.nodemanager.resource.memory-mb</code>', 'Memory on each node available to containers', '8192'],
            ['<code>yarn.nodemanager.resource.cpu-vcores</code>', 'Vcores on each node available to containers', '8'],
            ['<code>yarn.scheduler.minimum-allocation-mb</code>', 'Smallest container; requests are rounded up to a multiple', '1024'],
            ['<code>yarn.scheduler.maximum-allocation-mb</code>', 'Largest single container', '8192'],
            ['<code>mapreduce.map.memory.mb</code> / <code>reduce.memory.mb</code>', 'Container size for map / reduce tasks', '1024'],
            ['<code>mapreduce.map.java.opts</code>', 'JVM heap inside the container, about 80% of the container', '-Xmx derived from memory.mb'],
            ['<code>yarn.nodemanager.vmem-check-enabled</code>', 'Kill containers exceeding virtual memory limit', 'true (often disabled)'],
        ]),
        tags('Container Sizing', 'memory-mb', 'vcores', 'java.opts', 'Physical Memory Limit'),
    ),
    example(
        pyrun('''
import math
# One worker node: 128 GB RAM, 32 cores
node_ram_gb, node_cores = 128, 32
reserved_gb = 16            # OS, DataNode, NodeManager daemons
yarn_mb = (node_ram_gb - reserved_gb) * 1024
yarn_vcores = node_cores - 2
min_alloc = 1024

def containers(request_mb, vcores=1):
    size = math.ceil(request_mb / min_alloc) * min_alloc      # round up
    by_mem = yarn_mb // size
    by_cpu = yarn_vcores // vcores
    return size, min(by_mem, by_cpu), "memory" if by_mem < by_cpu else "cores"

print(f"yarn.nodemanager.resource.memory-mb = {yarn_mb}, cpu-vcores = {yarn_vcores}")
for name, mb, vc in [("map task 2 GB", 2048, 1),
                     ("Spark executor 8g, 2 cores", 8192 + max(384, int(0.10 * 8192)), 2)]:
    size, n, limit = containers(mb, vc)
    print(f"{name:<30} request {mb:>5} MB -> container {size:>5} MB, {n:>2} per node (limited by {limit})")
'''),
        title='Example: How Many Containers Fit on a Node?'),
    real_world(
        scenario('"Container killed by YARN for exceeding memory limits. 4.1 GB of 4 GB physical memory used"',
                 ul('The NodeManager measures the whole process (heap + off-heap: thread stacks, native buffers, Python workers in '
                    'PySpark) and kills it above the container size.',
                    'MapReduce: keep <code>-Xmx</code> ≈ 80% of <code>memory.mb</code>, or raise <code>mapreduce.map.memory.mb</code>.',
                    'Spark: raise <code>spark.executor.memoryOverhead</code> (PySpark/UDF-heavy jobs need more), or reduce data per task '
                    '(more partitions, fix skew).')),
    ),
    crossq(
        ('A Spark job requests 10 executors but gets 6. Why?', 'The queue\'s capacity or user limit is reached, or no node has a free gap big enough for one more '
         'executor container (memory + overhead, rounded up). Check the RM UI scheduler page; smaller executors often pack better.'),
    ),
]),
])
