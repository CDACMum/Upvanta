from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py, conf

MARKS_CSV = {'/Volumes/cdac/bda/raw/marks.csv': '''
roll_no,subject,marks
2401,SQL,72
2402,SQL,85
2401,Python,64
2402,Python,90
2403,SQL,91
''', '/Volumes/cdac/bda/raw/feedback.json': '''
{"roll_no": 2401, "rating": 4, "comment": "Good labs"}
{"roll_no": 2402, "rating": 5, "comment": "Clear explanations", "tags": ["spark", "delta"]}
'''}

SECTION = dict(level='basic', title='Apache Spark on Databricks', questions=[

# ------------------------------------------------------------------ 6
Q('How does Spark execute code on Databricks? Explain driver, executors, jobs, stages, tasks and lazy evaluation.', 'Spark Execution Model', minutes=9, cards=[
    definition(
        defbox('Every Databricks cluster runs Apache Spark. The <strong>driver</strong> runs your notebook code, builds an execution plan and '
               'schedules work. <strong>Executors</strong> on the worker nodes run <strong>tasks</strong>, one per data <strong>partition</strong>, '
               'using one CPU core each.',
               'Spark operations are either <strong>transformations</strong> (<code>select</code>, <code>filter</code>, <code>join</code>, '
               '<code>groupBy</code>), which only describe a new DataFrame, or <strong>actions</strong> (<code>count</code>, <code>collect</code>, '
               '<code>show</code>, <code>display</code>, writes), which need a result. Transformations are <strong>lazy</strong>: each action '
               'starts a <strong>job</strong>, the job is divided into <strong>stages</strong> at every shuffle, and each stage runs as many tasks '
               'as it has partitions.'),
        tags('Driver', 'Executor', 'Job', 'Stage', 'Task', 'Partition', 'Lazy evaluation', 'Catalyst'),
    ),
    analogy('The driver is an <strong>exam controller</strong> who plans how answer sheets will be evaluated; executors are the '
            '<strong>evaluators</strong>, each checking one bundle (partition) at a time. Nothing is evaluated until the result is actually '
            'requested (the action), so the controller can first plan the cheapest way to do it.'),
    spark_exec_anim(),
    real_world(
        scenario('Why lazy evaluation matters',
                 p('A notebook reads a 2 TB attendance table, filters one centre, and selects three columns. Because nothing runs until '
                   '<code>display()</code>, the Catalyst optimiser pushes the filter and the column list into the file scan: Spark reads only the '
                   'needed columns of the Parquet files and skips row groups whose statistics rule out the centre.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F

df  = spark.table("students")
bda = df.filter(F.col("course") == "PGCP-BDA").select("name", "marks")   # transformations: nothing runs yet
print(type(bda).__name__)

bda.explain()                                                            # the plan Spark will run
print("rows:", bda.count())                                              # action: a job runs now
print("partitions:", df.rdd.getNumPartitions(), "| cores:", spark.sparkContext.defaultParallelism)
'''),
        p('Read the plan bottom-up: <code>FileScan parquet</code> reads only <code>name, course, marks</code> (<code>ReadSchema</code>), and the '
          'filter was pushed into the scan (<code>PushedFilters: EqualTo(course,PGCP-BDA)</code>) so Parquet statistics can skip data. The '
          'tiny table has 1 partition; the build machine has 2 cores. On a real cluster you see each job, stage and task in the '
          '<strong>Spark UI</strong> (compute → Spark UI, or the "View" link under a cell).', top=True),
        title='Example'),
    steps(
        ('Write transformations', 'Chain reads, filters, joins and aggregations.'),
        ('Inspect the plan', 'Use <code>df.explain()</code> or <code>EXPLAIN</code> in SQL before running a heavy query.'),
        ('Trigger one action', 'Avoid calling <code>count()</code> or <code>display()</code> repeatedly on the same expensive chain.'),
        ('Check the Spark UI', 'Jobs → Stages → Tasks: look for skew (one slow task) and spill.'),
        title='Steps'),
    crossq(
        ('Is collect() safe on a big DataFrame?', 'No. <code>collect()</code> brings every row to the driver and can run it out of memory. Use '
         '<code>display()</code>, <code>limit()</code>, <code>take(n)</code> or write the result to a table.'),
        ('What decides the number of tasks in a stage?', 'The number of partitions: for a file scan, mainly the file sizes and '
         '<code>spark.sql.files.maxPartitionBytes</code> (128 MB by default); after a shuffle, <code>spark.sql.shuffle.partitions</code> '
         '(200 by default), adjusted at runtime by AQE.'),
        ('Where does a Python UDF run?', 'On the executors, in Python worker processes next to the JVM. Data is serialised between the JVM and '
         'Python, which is why built-in functions are usually faster.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How do you read files into DataFrames? Compare the DataFrame API with Spark SQL.', 'Reading Data & DataFrames', minutes=8, cards=[
    definition(
        defbox('A <strong>DataFrame</strong> is a distributed collection of rows with named, typed columns. Files are read with '
               '<code>spark.read.format(...).option(...).schema(...).load(path)</code> or shortcuts such as <code>spark.read.csv()</code>, '
               '<code>.json()</code> and <code>.parquet()</code>; tables with <code>spark.table("catalog.schema.table")</code>.',
               'The <strong>DataFrame API</strong> (Python, Scala) and <strong>Spark SQL</strong> are two front-ends for the same engine: both '
               'become the same logical plan, are optimised by Catalyst and run identically. A DataFrame can be exposed to SQL with '
               '<code>createOrReplaceTempView()</code>, and a SQL result is itself a DataFrame (<code>spark.sql(...)</code>).'),
        table(['Option', 'Meaning'], [
            ['<code>header</code>', 'CSV: first line holds column names'],
            ['<code>inferSchema</code>', 'Scan the data to guess types (extra pass over the files)'],
            ['<code>.schema("a INT, b STRING")</code>', 'Give types up front: faster and safer'],
            ['<code>mode</code>', 'PERMISSIVE (default, bad fields → null), DROPMALFORMED, FAILFAST'],
            ['<code>rescuedDataColumn</code>', 'Databricks: keep values that do not fit the schema in a JSON column'],
            ['<code>multiLine</code>', 'JSON/CSV records that span several lines'],
        ]),
        tags('DataFrame', 'spark.read', 'Schema', 'inferSchema', 'Temp view', 'spark.sql', 'Catalyst'),
    ),
    analogy('The DataFrame API and SQL are like ordering in <strong>English or Hindi</strong> at the same restaurant: the kitchen (the engine) '
            'receives the same order and cooks the same dish.'),
    read_files_anim(),
    real_world(
        scenario('Why production pipelines declare schemas',
                 p('A centre uploads a marks CSV where one row has "AB" (absent) in the marks column. With <code>inferSchema</code>, the whole '
                   'column silently becomes a string and later averages fail. With an explicit <code>marks INT</code> schema, the bad value '
                   'becomes null (or the job fails with FAILFAST), and the rest of the data keeps the right type.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F

inferred = (spark.read.option("header", True).option("inferSchema", True)
                 .csv("/Volumes/cdac/bda/raw/marks.csv"))
inferred.printSchema()

marks = (spark.read.format("csv").option("header", True)
              .schema("roll_no INT, subject STRING, marks INT")
              .load("/Volumes/cdac/bda/raw/marks.csv"))

feedback = spark.read.json("/Volumes/cdac/bda/raw/feedback.json")
feedback.printSchema()

# DataFrame API
marks.groupBy("subject").agg(F.avg("marks").alias("avg_marks")).orderBy("subject").show()

# the same question in SQL
marks.createOrReplaceTempView("marks_raw")
spark.sql("SELECT subject, avg(marks) AS avg_marks FROM marks_raw GROUP BY subject ORDER BY subject").show()
''', files=MARKS_CSV, data=False),
        p('JSON schema inference found the optional <code>tags</code> array and set it to null for the record that does not have it. Both '
          'queries return the same rows because they compile to the same plan.', top=True),
        title='Example'),
    steps(
        ('Know the format', 'CSV, JSON, Parquet, Avro, ORC, text, binary files, or a table.'),
        ('Declare the schema', 'In production, always; use inference only to explore.'),
        ('Choose a mode', 'PERMISSIVE plus a rescued-data column for messy data; FAILFAST for strict inputs.'),
        ('Save as a Delta table', '<code>df.write.saveAsTable("cdac.bda.marks")</code> so others query a governed table, not files.'),
        title='Steps'),
    crossq(
        ('Is SQL slower than PySpark DataFrames?', 'No. Both are compiled to the same plan. Speed differences come from what the query does, '
         'not from the language; Python UDFs are the exception because they run outside the JVM.'),
        ('What is the difference between a temp view and a table?', 'A temp view is only a name for a DataFrame in the current Spark session; '
         'it stores no data and disappears when the session ends. A table is registered in Unity Catalog and stored as files.'),
        ('What does read_files() do in Databricks SQL?', 'It is a table-valued function that reads files (CSV, JSON, Parquet, …) directly in SQL, '
         'with schema inference and the same options as <code>spark.read</code>, e.g. <code>SELECT * FROM read_files(\'/Volumes/…\', '
         'format =&gt; \'json\')</code>.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What are narrow and wide transformations? Explain shuffles, partitions, repartition and coalesce.', 'Shuffles & Partitions', minutes=9, cards=[
    definition(
        defbox('A <strong>narrow</strong> transformation (<code>filter</code>, <code>select</code>, <code>withColumn</code>, <code>union</code>) '
               'computes each output partition from one input partition. A <strong>wide</strong> transformation (<code>groupBy</code>, '
               '<code>join</code>, <code>orderBy</code>, <code>distinct</code>, window functions) needs rows with the same key together, so Spark '
               'performs a <strong>shuffle</strong>: data is written to local disk, sent across the network and re-read. In a plan a shuffle '
               'appears as <code>Exchange</code>.',
               'After a shuffle the number of partitions is <code>spark.sql.shuffle.partitions</code> (200 by default). '
               '<strong>Adaptive Query Execution (AQE)</strong>, on by default, measures the real shuffle sizes and <em>coalesces</em> many small '
               'partitions into fewer ones. On Databricks, <code>spark.sql.shuffle.partitions = auto</code> lets the platform pick the number.'),
        table(['', '<code>repartition(n, cols…)</code>', '<code>coalesce(n)</code>'], [
            ['Shuffle', 'Yes (full)', 'No (merges neighbouring partitions)'],
            ['Can increase partitions', 'Yes', 'No, only decrease'],
            ['Partition sizes', 'Even', 'Can be uneven'],
            ['Typical use', 'Spread data before a heavy step; partition by a key', 'Fewer output files at the end of a job'],
        ]),
        tags('Narrow', 'Wide', 'Shuffle', 'Exchange', 'spark.sql.shuffle.partitions', 'AQE', 'repartition', 'coalesce'),
    ),
    analogy('Sorting answer sheets by subject: if every evaluator just stamps their own pile, that is <strong>narrow</strong>. If all Python '
            'sheets from every pile must go to one room and all SQL sheets to another, everyone has to carry paper between rooms: that is a '
            '<strong>shuffle</strong>.'),
    shuffle_anim(),
    real_world(
        scenario('200 tiny files',
                 p('A daily job aggregates 50 MB of data and writes it as a Delta table. Without AQE it produced 200 partitions and so 200 '
                   'tiny files every day, slowing down every reader. With AQE coalescing (default on Databricks) plus optimized writes and '
                   'auto compaction on the table, the output is a handful of right-sized files.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F

agg = (spark.table("students")
            .groupBy("course").agg(F.count("*").alias("n"), F.avg("marks").alias("avg_marks")))
print(spark.conf.get("spark.sql.shuffle.partitions"), spark.conf.get("spark.sql.adaptive.enabled"))
agg.collect()          # run it, so explain() shows the final adaptive plan
agg.explain()

big = spark.range(0, 1_000_000, numPartitions=8)
print(big.rdd.getNumPartitions(),
      big.repartition(4).rdd.getNumPartitions(),
      big.coalesce(2).rdd.getNumPartitions())
big.coalesce(2).explain()
big.repartition(4, "id").explain()
'''),
        p('In the <strong>Initial Plan</strong> the aggregation has an <code>Exchange hashpartitioning(course, 200)</code>: a shuffle into 200 '
          'partitions. In the <strong>Final Plan</strong> AQE added <code>AQEShuffleRead coalesced</code> because the real shuffle data was tiny. '
          '<code>coalesce(2)</code> has no Exchange at all; <code>repartition(4, "id")</code> does.', top=True),
        title='Example'),
    steps(
        ('Find the shuffles', 'Look for <code>Exchange</code> in <code>explain()</code> or shuffle read/write sizes in the Spark UI.'),
        ('Filter and select early', 'Less data in, less data shuffled.'),
        ('Let AQE size partitions', 'Keep AQE on; consider <code>shuffle.partitions = auto</code> on Databricks.'),
        ('Broadcast small sides', 'A broadcast join avoids shuffling the big table.'),
        ('Control output files', 'Use optimized writes / auto compaction, or <code>coalesce</code> before a write.'),
        title='Steps'),
    crossq(
        ('Why can coalesce(1) be slow?', 'It forces the whole final stage into one task, so one core does all the work and one file is written. '
         'Use it only for small outputs (a small CSV export).'),
        ('Does repartition("col") guarantee one file per value?', 'No. It hashes rows into <code>spark.sql.shuffle.partitions</code> partitions; '
         'several values can share a partition. Use <code>partitionBy</code> on the writer for one folder per value.'),
        ('What is spill?', 'When a task\'s data does not fit in memory during a shuffle, sort or aggregation, Spark writes it temporarily to '
         'disk. The Spark UI shows "Spill (memory/disk)"; heavy spill means too few partitions or too little memory per core.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How does Spark choose a join strategy? Explain broadcast joins, sort-merge joins and AQE.', 'Joins & AQE', minutes=9, cards=[
    definition(
        table(['Strategy', 'When Spark uses it', 'Cost'], [
            ['<strong>Broadcast hash join</strong>', 'One side is small (≤ <code>spark.sql.autoBroadcastJoinThreshold</code>, 10 MB by default) '
             'or has a <code>broadcast</code> hint', 'Small side copied to every executor; big side not shuffled'],
            ['<strong>Sort-merge join</strong>', 'Both sides large, equi-join, sortable keys (default for big joins)', 'Both sides shuffled and sorted'],
            ['<strong>Shuffle hash join</strong>', 'One side much smaller but too big to broadcast, or hinted', 'Both shuffled, no sort; builds a hash table per partition'],
            ['<strong>Broadcast nested loop</strong>', 'Non-equi conditions (&lt;, BETWEEN, OR) with a small side', 'Can be very slow'],
        ]),
        defbox('<strong>Adaptive Query Execution (AQE)</strong> re-optimises a query between stages using actual statistics. It '
               '<strong>coalesces</strong> shuffle partitions, <strong>converts</strong> sort-merge joins to broadcast joins when a side turns out '
               'small, and <strong>splits skewed partitions</strong> in sort-merge joins (<code>spark.sql.adaptive.skewJoin.enabled</code>).'),
        tags('Broadcast hash join', 'Sort-merge join', 'Shuffle hash join', 'autoBroadcastJoinThreshold', 'Join hints', 'AQE', 'Skew join'),
    ),
    analogy('To match 20 lakh exam answers with 3 course names, you give every evaluator a <strong>printed copy of the 3 names</strong> '
            '(broadcast). To match 20 lakh answers with 20 lakh attendance records, both piles have to be <strong>sorted by roll number</strong> '
            'and walked through together (sort-merge).'),
    join_anim(),
    real_world(
        scenario('A slow dashboard query',
                 p('A query joins a 400 GB attendance fact table with a 2 MB centres dimension, but the plan shows a SortMergeJoin because '
                   'the dimension was read through a view with a complex filter and its size estimate was wrong. Collecting table statistics '
                   '(<code>ANALYZE TABLE … COMPUTE STATISTICS</code>), relying on AQE, or adding <code>/*+ BROADCAST(c) */</code> turns it into a '
                   'broadcast join and removes the shuffle of the 400 GB side.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F

spark.sql("""CREATE TABLE courses AS
             SELECT * FROM VALUES (0L, 'PGCP-BDA'), (1L, 'PGCP-AI'), (2L, 'PGCP-AC') AS t(course_id, course)""")
marks   = spark.range(0, 2_000_000).select((F.col("id") % 3).alias("course_id"), (F.rand(7) * 100).alias("marks"))
courses = spark.table("courses")

marks.join(courses, "course_id").explain()                  # small Delta table → broadcast

spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)  # turn automatic broadcasting off
marks.join(courses, "course_id").explain()                  # → sort-merge join, both sides shuffled

marks.join(F.broadcast(courses), "course_id").explain()     # a hint still forces a broadcast
''', data=False),
        sq('''
-- the same hint in SQL
SELECT /*+ BROADCAST(c) */ m.*, c.course
FROM   marks m JOIN courses c ON m.course_id = c.course_id;
'''),
        p('With automatic broadcasting on, Spark knew from the Delta table\'s file size that <code>courses</code> is tiny and chose '
          '<code>BroadcastHashJoin … BuildRight</code> with a <code>BroadcastExchange</code>. With the threshold set to -1 it planned a '
          '<code>SortMergeJoin</code> with an <code>Exchange</code> and <code>Sort</code> on both sides.', top=True),
        title='Example'),
    steps(
        ('Read the plan', 'Find the join operator and the Exchange nodes.'),
        ('Check sizes', 'Is one side small enough to broadcast? Are table statistics current?'),
        ('Keep AQE on', 'It fixes many join choices and skew at runtime.'),
        ('Hint when sure', '<code>BROADCAST</code>, <code>MERGE</code>, <code>SHUFFLE_HASH</code> hints override the planner.'),
        ('Handle skew', 'AQE skew join, or salt a hot key when one value dominates.'),
        title='Steps'),
    crossq(
        ('Can you broadcast a 2 GB table?', 'Technically up to the broadcast limit (8 GB), but it must fit in the driver and every executor\'s '
         'memory and is sent over the network to each one. In practice broadcast only tables of tens to a few hundred MB.'),
        ('What is data skew in a join?', 'One key has far more rows than others (e.g. a default centre id), so one task gets most of the data '
         'and runs for hours while others finish in seconds. AQE splits such partitions; salting (adding a random suffix to the key) is the '
         'manual fix.'),
        ('Why does a non-equi join become slow?', 'Hash and sort-merge joins need equality keys. Conditions such as <code>a.ts BETWEEN b.start '
         'AND b.end</code> fall back to nested-loop joins, which compare many pairs of rows. Add an equality key (e.g. date) if possible.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How does caching work? Compare Spark caching, the Databricks disk cache and Photon.', 'Caching & Photon', minutes=7, cards=[
    definition(
        defbox('<strong>Spark caching</strong>: <code>df.cache()</code> (or <code>persist(level)</code>) marks a DataFrame to be kept in executor '
               'memory and disk after it is first computed. It is lazy, specific to that DataFrame\'s plan, and released with '
               '<code>unpersist()</code>. In SQL: <code>CACHE TABLE t</code>.',
               'The <strong>Databricks disk cache</strong> (formerly "Delta cache") automatically keeps local copies of remote Parquet/Delta '
               'files on the workers\' SSDs, in an efficient format, and detects when files change. It needs no code and is on by default '
               'for SSD-backed instance types and SQL warehouses.',
               '<strong>Photon</strong> is not a cache: it is Databricks\' vectorised C++ execution engine that runs supported SQL and '
               'DataFrame operators faster than the JVM engine.'),
        tags('cache()', 'persist()', 'StorageLevel', 'unpersist()', 'CACHE TABLE', 'Disk cache', 'Photon'),
    ),
    analogy('Spark cache is <strong>keeping a photocopy</strong> of a specific report on your desk because you will read it ten times today. '
            'The disk cache is the <strong>library\'s reading-room shelf</strong> that automatically keeps recently borrowed books nearby. '
            'Photon is a <strong>faster reader</strong>, not a shelf.'),
    cache_anim(),
    real_world(
        scenario('Caching in an ML notebook',
                 p('A data scientist filters 30 lakh student records, engineers 40 features and then tries 12 models on the result. Caching the '
                   'feature DataFrame once avoids recomputing the filter and joins 12 times. At the end of the notebook she calls '
                   '<code>unpersist()</code> so the shared cluster gets its memory back.')),
    ),
    example(
        pyrun('''
df = spark.table("students").filter("marks >= 70")
df.cache()                                   # lazy: nothing is stored yet
print(df.is_cached, df.storageLevel)

print(df.count())                            # first action computes and fills the cache
df.groupBy("centre").count().explain()       # later queries read InMemoryTableScan

df.unpersist()
print(df.is_cached)
'''),
        sq('''
-- SQL equivalents
CACHE TABLE top_students AS SELECT * FROM students WHERE marks >= 70;
UNCACHE TABLE top_students;
'''),
        p('The default level for DataFrames is <code>MEMORY_AND_DISK</code> (printed as "Disk Memory Deserialized"). The second plan reads '
          'from <code>InMemoryTableScan</code> instead of the Parquet files.', top=True),
        title='Example'),
    steps(
        ('Identify reuse', 'A DataFrame used by several actions or loops.'),
        ('Cache after the expensive part', 'After joins and filters, before the repeated use.'),
        ('Materialise', 'Run one action (e.g. count) to fill it.'),
        ('Release', '<code>unpersist()</code> when done, especially on shared clusters.'),
        title='Steps'),
    crossq(
        ('Is df.cache() supported on serverless compute?', 'No. Serverless compute does not support <code>cache()</code>/<code>persist()</code> '
         'on DataFrames; it relies on the disk cache and other optimisations instead. On classic clusters it works as described.'),
        ('Does the disk cache return stale data after an UPDATE?', 'No. An UPDATE writes new files with new names; the cache is keyed by file, '
         'so readers fetch the new files and old cached copies are evicted.'),
        ('Should you cache a table read once in a job?', 'No. Caching adds work to write the cache; it only pays off when the data is read '
         'again.'),
    ),
]),

])
