from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py

RESULTS = {
    '/Volumes/cdac/bda/landing/results/kharghar_0301.json':
        '{"roll_no": "2401", "subject": "SQL", "marks": "72", "centre": "Kharghar", "ts": "2026-03-01 10:00:00"}\n'
        '{"roll_no": "2403", "subject": "SQL", "marks": "91", "centre": "Kharghar", "ts": "2026-03-01 10:00:00"}\n'
        '{"roll_no": "2405", "subject": "SQL", "marks": "105", "centre": "Kharghar", "ts": "2026-03-01 10:00:00"}\n',
    '/Volumes/cdac/bda/landing/results/juhu_0301.json':
        '{"roll_no": "2402", "subject": "SQL", "marks": "85", "centre": "Juhu", "ts": "2026-03-01 10:05:00"}\n'
        '{"roll_no": "2402", "subject": "SQL", "marks": "88", "centre": "Juhu", "ts": "2026-03-01 18:30:00"}\n'
        '{"roll_no": null, "subject": "SQL", "marks": "40", "centre": "Juhu", "ts": "2026-03-01 10:05:00"}\n',
}

SWIPES = {'/Volumes/cdac/bda/landing/swipes/batch1.json':
          '{"roll_no": 2401, "gate": "G1", "ts": "2026-03-02 09:01:10"}\n'
          '{"roll_no": 2402, "gate": "G1", "ts": "2026-03-02 09:02:45"}\n'
          '{"roll_no": 2403, "gate": "G2", "ts": "2026-03-02 09:04:05"}\n'
          '{"roll_no": 2404, "gate": "G2", "ts": "2026-03-02 09:06:30"}\n'}

CORRECTIONS = {'/Volumes/cdac/bda/landing/corrections/c1.json':
               '{"roll_no": 2404, "marks": 69.00, "changed_at": "2026-03-03 11:00:00"}\n'
               '{"roll_no": 2404, "marks": 71.50, "changed_at": "2026-03-03 15:30:00"}\n'
               '{"roll_no": 2408, "marks": 61.00, "changed_at": "2026-03-03 12:10:00"}\n'
               '{"roll_no": 2412, "marks": 77.00, "changed_at": "2026-03-03 12:15:00"}\n'}

FEEDBACK = """
CREATE TABLE raw_feedback AS SELECT * FROM VALUES
  (1, '{"roll_no": 2401, "student": {"name": "Anuj", "centre": "Kharghar"}, "scores": [{"sub": "SQL", "m": 72}, {"sub": "Python", "m": 64}]}'),
  (2, '{"roll_no": 2402, "student": {"name": "Aarshvi", "centre": "Juhu"}, "scores": [{"sub": "SQL", "m": 85}], "remarks": "late fee paid"}')
  AS t(id, payload);
"""

SECTION = dict(level='intermediate', title='Ingestion, Streaming & the Medallion Architecture', questions=[

# ------------------------------------------------------------------ 21
Q('What is the medallion architecture? Build a bronze, silver and gold pipeline.', 'Medallion Architecture', minutes=10, cards=[
    definition(
        defbox('The <strong>medallion architecture</strong> organises a lakehouse into layers of increasing quality. '
               '<strong>Bronze</strong> holds raw data as received (append-only, with ingestion metadata), so it can always be replayed. '
               '<strong>Silver</strong> holds cleaned, validated, de-duplicated and conformed data, typically one row per business entity or event. '
               '<strong>Gold</strong> holds business-level tables: aggregates, KPIs, dimensional models and ML features.',
               'It is a design pattern, not a product feature: each layer is just a set of Delta tables, often in separate schemas such as '
               '<code>cdac.bronze</code>, <code>cdac.silver</code> and <code>cdac.gold</code>, with permissions to match.'),
        tags('Bronze', 'Silver', 'Gold', 'Raw data', 'Data quality', 'Replay', 'Incremental processing'),
    ),
    analogy('Gold ore (bronze) is stored as mined, so it can be re-processed if refining improves. It is then <strong>refined</strong> (silver) '
            'and finally <strong>made into jewellery</strong> (gold) for customers. You never throw away the ore.'),
    medallion_anim(),
    real_world(
        scenario('Why keep bronze?',
                 p('A bug in the silver logic rounded marks for two weeks. Because bronze kept every original file\'s rows, the team fixed the '
                   'code and rebuilt silver and gold from bronze in one run, without asking the centres to upload anything again.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F, Window

# BRONZE: raw records as received, plus where and when they came in
bronze = (spark.read.json("/Volumes/cdac/bda/landing/results/")
               .withColumn("source_file", F.element_at(F.split(F.col("_metadata.file_path"), "/"), -1))
               .withColumn("ingested_at", F.current_timestamp()))
bronze.write.mode("overwrite").saveAsTable("bronze_results")

# SILVER: typed, valid, one row per roll_no + subject (latest record wins)
latest = Window.partitionBy("roll_no", "subject").orderBy(F.col("ts").desc())
silver = (spark.table("bronze_results")
               .select(F.col("roll_no").cast("int"), "subject", F.col("marks").cast("int"),
                       "centre", F.to_timestamp("ts").alias("ts"), "source_file")
               .filter("roll_no IS NOT NULL AND marks BETWEEN 0 AND 100")
               .withColumn("rn", F.row_number().over(latest)).filter("rn = 1").drop("rn"))
silver.write.mode("overwrite").saveAsTable("silver_results")

# GOLD: what the dashboard needs
gold = (spark.table("silver_results").groupBy("centre", "subject")
             .agg(F.count("*").alias("students"), F.round(F.avg("marks"), 2).alias("avg_marks")))
gold.write.mode("overwrite").saveAsTable("gold_centre_summary")

for t in ("bronze_results", "silver_results", "gold_centre_summary"):
    print(t, spark.table(t).count())
spark.table("silver_results").orderBy("roll_no").show(truncate=False)
spark.table("gold_centre_summary").orderBy("centre").show()
''', files=RESULTS, data=False),
        p('Bronze kept all 6 raw rows, everything as strings. Silver dropped the row with no roll number and the impossible 105, and kept only '
          'the later of the two records for 2402 (88, from the 18:30 upload). <code>_metadata.file_path</code> is the hidden file-metadata '
          'column available on file sources. A production pipeline would load bronze and silver incrementally (Auto Loader, streaming, '
          'MERGE) rather than overwrite.', top=True),
        title='Example'),
    steps(
        ('Bronze', 'Land raw data with Auto Loader; add source file and ingest time; no transformations.'),
        ('Silver', 'Cast types, validate (constraints or expectations), de-duplicate, MERGE changes.'),
        ('Gold', 'Aggregate and model for each consumer; keep it small and fast.'),
        ('Govern', 'Separate schemas per layer; analysts get SELECT on gold (and maybe silver), not bronze.'),
        title='Steps'),
    crossq(
        ('Is three layers a rule?', 'No. Some pipelines need only bronze and gold; others add a "platinum" or a staging layer. The point is a '
         'clear separation between raw, trusted and consumption-ready data.'),
        ('Should bronze have a schema?', 'Usually a loose one: Auto Loader infers types or keeps strings, with a rescued-data column, so that no '
         'input is lost. Strict typing happens in silver.'),
        ('Where do data-quality failures go?', 'Often to a quarantine table next to silver (rows that failed checks, with the reason), so they '
         'can be fixed and re-processed instead of silently dropped.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What is Auto Loader? How is it different from COPY INTO and plain spark.read?', 'Auto Loader & COPY INTO', minutes=8, cards=[
    definition(
        defbox('<strong>Auto Loader</strong> is a Databricks Structured Streaming source, <code>spark.readStream.format("cloudFiles")</code>, that '
               'incrementally and efficiently loads new files from cloud storage or volumes. It tracks processed files in the stream '
               'checkpoint (exactly once), infers and stores the schema (<code>cloudFiles.schemaLocation</code>), handles schema evolution, '
               'and puts non-matching values in <code>_rescued_data</code>. It discovers files by <strong>directory listing</strong> or by '
               '<strong>file notification</strong> events, which scales to millions of files.',
               '<strong>COPY INTO</strong> is a SQL command that loads files from a location into a Delta table. It is idempotent: files already '
               'loaded are skipped. It suits thousands of files and simple SQL-only loads; Auto Loader suits millions of files, continuous '
               'arrival and schema drift.'),
        table(['', 'spark.read (batch)', 'COPY INTO', 'Auto Loader'], [
            ['Remembers loaded files', 'No: reads everything again', 'Yes (in the table)', 'Yes (checkpoint)'],
            ['Scale', 'Any, but re-reads', 'Thousands of files', 'Millions of files'],
            ['Schema drift', 'Manual', 'mergeSchema option', 'Inference, evolution, rescued data'],
            ['Language', 'Python / SQL', 'SQL', 'Python / SQL (in pipelines)'],
            ['Run as', 'Batch job', 'Batch job', 'Stream, or availableNow on a schedule'],
        ]),
        tags('Auto Loader', 'cloudFiles', 'schemaLocation', '_rescued_data', 'File notification', 'COPY INTO', 'Idempotent'),
    ),
    analogy('Auto Loader is a <strong>postal clerk with a register</strong>: every morning only the new envelopes are opened and logged. '
            'Plain <code>spark.read</code> re-opens every envelope ever received. COPY INTO is a clerk with a smaller register, fine for a small '
            'office.'),
    autoloader_anim(),
    real_world(
        scenario('Thousands of centre uploads a day',
                 p('Results, attendance and feedback files arrive from 30 centres all day. One Auto Loader stream per source, run with '
                   '<code>trigger(availableNow=True)</code> every 15 minutes by a job, loads only the new files into bronze. When a centre adds a '
                   '<code>remarks</code> field, the stream stops once with a schema-change error, records the new column, and continues on '
                   'restart (the job retries automatically).')),
    ),
    example(
        py('''
(spark.readStream
      .format("cloudFiles")
      .option("cloudFiles.format", "json")
      .option("cloudFiles.schemaLocation", "/Volumes/cdac/bda/checkpoints/results_schema")
      .option("cloudFiles.inferColumnTypes", "true")
      .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
      .load("/Volumes/cdac/bda/landing/results/")
      .withColumn("source_file", F.col("_metadata.file_path"))
      .writeStream
      .option("checkpointLocation", "/Volumes/cdac/bda/checkpoints/bronze_results")
      .trigger(availableNow=True)
      .toTable("cdac.bda.bronze_results"))
''', title='Python: Auto Loader (shown, not executed)'),
        sq('''
-- COPY INTO: SQL, idempotent, re-runnable
CREATE TABLE IF NOT EXISTS cdac.bda.bronze_results_copy;

COPY INTO cdac.bda.bronze_results_copy
FROM '/Volumes/cdac/bda/landing/results/'
FILEFORMAT = JSON
FORMAT_OPTIONS ('inferSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true');

-- Auto Loader inside a declarative pipeline (SQL)
CREATE OR REFRESH STREAMING TABLE bronze_results
AS SELECT *, _metadata.file_path AS source_file
FROM STREAM read_files('/Volumes/cdac/bda/landing/results/', format => 'json');
'''),
        p('Auto Loader and COPY INTO need a Databricks workspace, so they are shown without output. Question 23 shows the same incremental '
          'behaviour with the open-source file streaming source.', top=True),
        title='Example'),
    steps(
        ('Pick the source path', 'A volume or cloud path that only receives files for this feed.'),
        ('Set schemaLocation and checkpointLocation', 'Separate folders per stream; never share them.'),
        ('Decide on schema evolution', 'addNewColumns (default), rescue, failOnNewColumns or none.'),
        ('Schedule', 'availableNow in a job for batch-like loads, or continuous for low latency.'),
        title='Steps'),
    crossq(
        ('Directory listing or file notification mode?', 'Directory listing is simple and needs no extra permissions; Auto Loader lists only new '
         'paths efficiently. For very large or busy directories, file notification (or managed file events) uses cloud queue services so '
         'it does not have to list the folder.'),
        ('What happens if the same file is uploaded again with the same name?', 'Auto Loader ignores it by default because the path was already '
         'processed (<code>cloudFiles.allowOverwrites</code> changes that). COPY INTO also skips it unless <code>force = true</code>.'),
        ('What is in _rescued_data?', 'A JSON string with values that did not fit the schema (wrong type, unexpected column, different case), '
         'plus the source file path, so nothing is lost silently.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How does Structured Streaming work on Databricks? Explain checkpoints, triggers, output modes and watermarks.', 'Structured Streaming', minutes=10, cards=[
    definition(
        defbox('<strong>Structured Streaming</strong> treats a stream as an unbounded table. You write the same DataFrame or SQL code as for batch; '
               'Spark runs it incrementally in <strong>micro-batches</strong>. Sources include Auto Loader, Kafka/Event Hubs/Kinesis, Delta tables '
               'and files; sinks include Delta tables, Kafka and <code>foreachBatch</code>.'),
        table(['Concept', 'Meaning'], [
            ['<code>checkpointLocation</code>', 'Offsets processed and state; gives exactly-once with Delta sinks and restart where it stopped'],
            ['Trigger', 'Default (next batch as soon as possible), <code>processingTime="1 minute"</code>, <code>availableNow=True</code> (all available data, then stop), real-time mode'],
            ['Output mode', '<code>append</code> (new rows only), <code>update</code> (changed result rows), <code>complete</code> (whole result each time)'],
            ['Watermark', '<code>withWatermark("ts", "10 minutes")</code>: how late events may arrive; lets Spark finalise windows and drop old state'],
        ]),
        tags('Structured Streaming', 'Micro-batch', 'Checkpoint', 'Trigger', 'availableNow', 'Output mode', 'Watermark', 'Exactly once'),
    ),
    analogy('A streaming query is a <strong>conveyor belt</strong> at a sorting office: the checkpoint is the <strong>tally sheet</strong> of what '
            'has already passed, so after a power cut work resumes from the right parcel. The watermark is the rule "parcels more than 10 '
            'minutes late go to tomorrow\'s count".'),
    streaming_anim(),
    real_world(
        scenario('Gate swipes during exam day',
                 p('Every swipe at the exam centre gate is written to a landing folder. A stream counts entries per gate in 5-minute windows for '
                   'the control room, and a second stream appends all swipes to a bronze table for audits. Both run with checkpoints, so a cluster '
                   'restart neither loses nor double-counts swipes.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F

swipes = (spark.readStream.format("json")
               .schema("roll_no INT, gate STRING, ts TIMESTAMP")
               .load("/Volumes/cdac/bda/landing/swipes/"))
print(swipes.isStreaming)

def run_once():
    q = (swipes.withColumn("ingested_at", F.current_timestamp())
               .writeStream.format("delta")
               .option("checkpointLocation", "/Volumes/cdac/bda/checkpoints/bronze_swipes")
               .trigger(availableNow=True)
               .toTable("bronze_swipes"))
    q.awaitTermination()
    return q.lastProgress["numInputRows"]

print("run 1 read", run_once(), "rows; table has", spark.table("bronze_swipes").count())
dbutils.fs.put("/Volumes/cdac/bda/landing/swipes/batch2.json",
               '{"roll_no": 2405, "gate": "G1", "ts": "2026-03-02 09:07:50"}\\n'
               '{"roll_no": 2406, "gate": "G2", "ts": "2026-03-02 09:12:20"}\\n', True)
print("run 2 read", run_once(), "rows; table has", spark.table("bronze_swipes").count())
print("run 3 read", run_once(), "rows; table has", spark.table("bronze_swipes").count())

per_5min = (swipes.withWatermark("ts", "10 minutes")
                  .groupBy(F.window("ts", "5 minutes"), "gate").count())
q = (per_5min.writeStream.format("memory").queryName("gate_counts")
             .outputMode("update").trigger(availableNow=True).start())
q.awaitTermination()
spark.sql("SELECT window.start, window.end, gate, count FROM gate_counts ORDER BY start, gate").show()
''', files=SWIPES, data=False),
        p('Run 1 loaded the 4 rows of the first file. After a new file arrived, run 2 read only its 2 rows, and run 3 found nothing new: the '
          'checkpoint remembered what was done. The windowed aggregation uses update mode; in append mode a window is emitted only after the '
          'watermark passes its end.', top=True),
        title='Example'),
    steps(
        ('Read a stream', 'Auto Loader, Kafka or a Delta table with <code>readStream</code>.'),
        ('Transform', 'Same API as batch; add a watermark for event-time aggregations and stream-stream joins.'),
        ('Write with a checkpoint', 'One unique checkpoint folder per query, kept forever.'),
        ('Choose a trigger', 'availableNow in scheduled jobs (cheap); processingTime or continuous jobs for low latency.'),
        ('Monitor', 'Streaming query progress, input rate vs processing rate, state size.'),
        title='Steps'),
    crossq(
        ('What happens if you delete the checkpoint?', 'The query no longer knows what it processed: it starts from the beginning (or from the '
         'configured starting position) and may reprocess or skip data. Treat checkpoints as part of the table\'s state.'),
        ('Can you change a streaming query and keep the checkpoint?', 'Some changes are allowed (filters, projections, sink options); others are '
         'not (changing aggregation keys, stateful operations, the source). Incompatible changes need a new checkpoint and a backfill plan.'),
        ('Why is availableNow popular on Databricks?', 'It gives the incremental, exactly-once bookkeeping of streaming with batch-style cost: a '
         'job starts, processes everything new, and the compute shuts down.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you upsert streaming data into a Delta table with foreachBatch and MERGE?', 'Streaming Upserts (foreachBatch)', minutes=9, cards=[
    definition(
        defbox('A Delta streaming sink can only <strong>append</strong> (or overwrite in complete mode). To apply updates from a stream (CDC events, '
               'corrections) use <code>writeStream.foreachBatch(fn)</code>: Spark calls <code>fn(batch_df, batch_id)</code> once per '
               'micro-batch with an ordinary DataFrame, and inside it you can run any batch code, typically a <code>MERGE</code>.',
               'Rules: de-duplicate inside the batch (latest change per key), make the function <strong>idempotent</strong> because a failed batch '
               'is retried with the same <code>batch_id</code>, and use <code>batch_df.sparkSession</code> for SQL inside the function. In '
               'Lakeflow Declarative Pipelines, <code>AUTO CDC</code> (formerly <code>APPLY CHANGES</code>) does this declaratively, including '
               'SCD Type 2.'),
        tags('foreachBatch', 'MERGE', 'Upsert', 'CDC', 'Idempotent', 'batch_id', 'AUTO CDC'),
    ),
    analogy('foreachBatch is like a <strong>clerk who receives a tray of correction slips</strong> every few minutes: she sorts the tray, keeps '
            'only the latest slip per student, and updates the register in one go. If she is interrupted, she processes the same tray again, '
            'so updating (not appending) is what keeps the register right.'),
    foreachbatch_anim(),
    real_world(
        scenario('Re-evaluation results',
                 p('Re-evaluation results arrive throughout the week, sometimes twice for the same student. A foreachBatch stream keeps '
                   '<code>silver_marks</code> current within minutes; the de-duplication step makes sure the later of two corrections wins even '
                   'when both arrive in the same batch.')),
    ),
    example(
        pyrun('''
from pyspark.sql import functions as F, Window

spark.sql("CREATE TABLE silver_marks AS SELECT roll_no, name, marks FROM students")

corrections = (spark.readStream.format("json")
                    .schema("roll_no INT, marks DECIMAL(5,2), changed_at TIMESTAMP")
                    .load("/Volumes/cdac/bda/landing/corrections/"))

def upsert(batch_df, batch_id):
    latest = Window.partitionBy("roll_no").orderBy(F.col("changed_at").desc())
    (batch_df.withColumn("rn", F.row_number().over(latest)).filter("rn = 1")
             .createOrReplaceTempView("changes"))
    batch_df.sparkSession.sql("""
        MERGE INTO silver_marks AS t
        USING changes AS c
        ON t.roll_no = c.roll_no
        WHEN MATCHED THEN UPDATE SET t.marks = c.marks
        WHEN NOT MATCHED THEN INSERT (roll_no, marks) VALUES (c.roll_no, c.marks)
    """).show()

q = (corrections.writeStream.foreachBatch(upsert)
                .option("checkpointLocation", "/Volumes/cdac/bda/checkpoints/silver_marks")
                .trigger(availableNow=True).start())
q.awaitTermination()
spark.table("silver_marks").filter("roll_no IN (2404, 2408, 2412)").orderBy("roll_no").show()
''', files=CORRECTIONS),
        sq('''
-- the declarative version in a Lakeflow pipeline
CREATE OR REFRESH STREAMING TABLE silver_marks;

CREATE FLOW marks_cdc AS AUTO CDC INTO silver_marks
FROM STREAM(bronze_corrections)
KEYS (roll_no)
SEQUENCE BY changed_at
STORED AS SCD TYPE 1;
'''),
        p('The batch had two corrections for 2404; only the later one (71.50) was applied. 2408 was updated and 2412, a late registration, was '
          'inserted with no name yet.', top=True),
        title='Example'),
    steps(
        ('Read the change stream', 'Auto Loader, Kafka, or a Delta table\'s change feed.'),
        ('Write the batch function', 'De-duplicate by key and sequence column, then MERGE.'),
        ('Use the batch session', '<code>batch_df.sparkSession.sql(...)</code> for SQL in the function.'),
        ('Checkpoint and schedule', 'One checkpoint per query; availableNow or continuous.'),
        title='Steps'),
    crossq(
        ('Why not just append the changes and de-duplicate at query time?', 'You can (an append-only log is a valid bronze design), but every reader '
         'then pays for the de-duplication. MERGE moves the cost to write time once.'),
        ('Is foreachBatch exactly-once?', 'It is at-least-once: a batch can run again after a failure. MERGE on a key makes repeated runs give the '
         'same result. For appends inside foreachBatch, set the Delta writer options <code>txnAppId</code> and <code>txnVersion</code> (the '
         'batch_id) so Delta ignores a duplicate commit.'),
        ('How do you handle deletes from a CDC source?', 'Add a clause such as <code>WHEN MATCHED AND c.op = \'D\' THEN DELETE</code>, or use '
         'AUTO CDC with <code>APPLY AS DELETE WHEN op = \'D\'</code>.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('How do you work with semi-structured JSON data in Databricks?', 'JSON & Nested Data', minutes=9, cards=[
    definition(
        table(['Tool', 'Use'], [
            ['<code>raw:student.name</code> (Databricks SQL)', 'Extract a field from a JSON string without a schema'],
            ['<code>get_json_object(col, \'$.a.b\')</code>', 'Same, standard Spark function (returns a string)'],
            ['<code>from_json(col, schema)</code>', 'Parse into a STRUCT / ARRAY / MAP with a known schema'],
            ['<code>schema_of_json(sample)</code>', 'Derive a schema string from an example'],
            ['<code>explode</code> / <code>posexplode</code> / <code>inline</code>', 'One row per array element (or struct)'],
            ['<code>transform</code>, <code>filter</code>, <code>aggregate</code>, <code>exists</code>', 'Higher-order functions over arrays, without exploding'],
            ['<code>VARIANT</code>, <code>parse_json</code>, <code>variant_get</code>', 'Store and query JSON of changing shape efficiently'],
            ['<code>to_json</code>, <code>struct</code>, <code>collect_list</code>', 'Build JSON from relational data'],
        ]),
        defbox('The <strong>VARIANT</strong> type (Databricks Runtime 15.3+, Spark 4.0) stores semi-structured data in a binary format that is much '
               'faster to query than a JSON string while keeping the flexibility of schema-on-read.'),
        tags('JSON', 'STRUCT', 'ARRAY', 'from_json', 'explode', 'Higher-order functions', 'VARIANT', 'parse_json'),
    ),
    analogy('A JSON document is a <strong>nested folder</strong>. <code>from_json</code> gives it labelled drawers (a schema), <code>explode</code> '
            'empties a drawer of papers onto the table one by one, and VARIANT is a <strong>smart folder</strong> that remembers where everything '
            'is without needing labels first.'),
    json_anim(),
    real_world(
        scenario('Feedback forms with optional fields',
                 p('The online feedback form changes every term: new questions, optional remarks, a variable number of subjects. Storing the '
                   'payload as VARIANT in bronze keeps every version queryable; silver extracts the stable fields into typed columns and explodes '
                   'the per-subject scores into one row per subject for reporting.')),
    ),
    example(
        sql('''
SELECT get_json_object(payload, '$.student.name')  AS name,
       get_json_object(payload, '$.scores[0].sub') AS first_subject
FROM   raw_feedback;

CREATE OR REPLACE TEMP VIEW parsed AS
SELECT from_json(payload,
         'roll_no INT, student STRUCT<name: STRING, centre: STRING>, scores ARRAY<STRUCT<sub: STRING, m: INT>>') AS r
FROM raw_feedback;

SELECT r.roll_no, r.student.name, r.student.centre, size(r.scores) AS n_subjects FROM parsed;

SELECT r.roll_no, s.sub, s.m
FROM   parsed LATERAL VIEW explode(r.scores) e AS s
ORDER  BY r.roll_no, s.sub;

SELECT r.roll_no,
       transform(r.scores, x -> x.m + 5)            AS with_grace,
       filter(r.scores, x -> x.m >= 70).sub          AS passed_70,
       aggregate(r.scores, 0, (acc, x) -> acc + x.m) AS total
FROM   parsed ORDER BY r.roll_no;

SELECT variant_get(parse_json(payload), '$.student.centre', 'string') AS centre,
       variant_get(parse_json(payload), '$.remarks', 'string')        AS remarks,
       schema_of_variant(parse_json(payload))                        AS shape
FROM   raw_feedback;
''', setup=FEEDBACK, data=False),
        sq('''
-- Databricks SQL path syntax on JSON strings and VARIANT columns
SELECT payload:roll_no::INT       AS roll_no,
       payload:student.name       AS name,
       payload:scores[0].m::INT   AS first_mark
FROM   raw_feedback;
'''),
        p('<code>schema_of_variant</code> shows that the second record has an extra <code>remarks</code> field; VARIANT handles both shapes '
          'in one column, and <code>variant_get</code> returns NULL where a path does not exist.', top=True),
        title='Example'),
    steps(
        ('Land raw', 'Keep the JSON as a string or VARIANT in bronze.'),
        ('Find the schema', 'schema_of_json / schema_of_variant on samples, or let Auto Loader infer it.'),
        ('Parse', 'from_json for stable shapes; VARIANT for shapes that change.'),
        ('Flatten', 'Select nested fields; explode arrays where one row per element is needed.'),
        ('Promote', 'Store frequently used fields as typed columns in silver.'),
        title='Steps'),
    crossq(
        ('explode or a higher-order function?', 'Explode when you need one row per element (joins, group by subject). Use transform/filter/'
         'aggregate when the result stays one row per record; it avoids multiplying the rows.'),
        ('What does explode do with an empty or NULL array?', 'It produces no rows, so that record disappears. <code>explode_outer</code> keeps it '
         'with NULL values.'),
        ('Why is VARIANT faster than a JSON string?', 'A string must be parsed on every query. VARIANT is stored pre-parsed in a binary encoding, '
         'and Delta can shred frequently used paths into columns, so field access is much cheaper.'),
    ),
]),

])
