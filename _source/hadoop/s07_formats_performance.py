from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml

SECTION = dict(level='advanced', title='File Formats, Compression & Tuning', questions=[

# ------------------------------------------------------------------ 38
Q('Which file formats are used in Hadoop? Compare Text, SequenceFile, Avro, Parquet and ORC.', 'File Formats', minutes=10, cards=[
    definition(
        defbox('The storage format decides how much disk a dataset uses, how much data a query must read, and whether files can be '
               'split across tasks. <strong>Row formats</strong> store whole records together (good for writing and reading entire rows); '
               '<strong>columnar formats</strong> store each column together (good for analytics that read a few columns).'),
        tags('Parquet', 'ORC', 'Avro', 'SequenceFile', 'Row vs Columnar', 'Schema Evolution'),
    ),
    comparison(
        table(['Format', 'Layout', 'Schema', 'Splittable', 'Strengths', 'Typical use'], [
            ['Text / CSV / JSON', 'Row, human-readable', 'None (schema-on-read)', 'Yes if uncompressed or bzip2', 'Simple, universal', 'Landing / raw zone, exchange'],
            ['SequenceFile', 'Row, binary key-value', 'Writable classes', 'Yes (sync markers)', 'Fast, compressible by record/block', 'Intermediate MapReduce data, packing small files'],
            ['Avro', 'Row, binary', 'JSON schema stored in file', 'Yes', 'Best <strong>schema evolution</strong>, compact, language-neutral', 'Ingestion, Kafka messages, write-heavy pipelines'],
            ['Parquet', 'Columnar (row groups → column chunks → pages)', 'Embedded', 'Yes (row groups)', 'Column pruning, predicate pushdown, great compression; Spark\'s default', 'Analytics in Spark, Hive, Trino, data lakes'],
            ['ORC', 'Columnar (stripes)', 'Embedded', 'Yes (stripes)', 'Lightweight indexes, bloom filters, Hive ACID tables', 'Hive-centric warehouses'],
        ]),
    ),
    example(
        p('The same 100,000 student records written in four formats with PyArrow (Parquet with Snappy, ORC with zlib):'),
        pyrun('''
import csv, json, os, random
import pyarrow as pa, pyarrow.parquet as pq, pyarrow.orc as orc

random.seed(7)
n = 100_000
rows = {"roll_no": list(range(240001, 240001 + n)),
        "city":    [random.choice(["Mumbai", "Pune", "Navi Mumbai", "Bengaluru", "Hyderabad"]) for _ in range(n)],
        "course":  [random.choice(["PG-DBDA", "PG-DAC", "PG-DAI"]) for _ in range(n)],
        "marks":   [random.randint(35, 100) for _ in range(n)]}
table = pa.table(rows)

with open("students.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(rows); w.writerows(zip(*rows.values()))
with open("students.json", "w") as f:
    for r in zip(*rows.values()):
        f.write(json.dumps(dict(zip(rows, r))) + "\\n")
pq.write_table(table, "students.parquet", compression="snappy")
orc.write_table(table, "students.orc", compression="zlib")

for fn in ["students.csv", "students.json", "students.parquet", "students.orc"]:
    print(f"{fn:<18} {os.path.getsize(fn) / 1024:>7,.0f} KB")

# Column pruning: read ONE column without touching the others
marks = pq.read_table("students.parquet", columns=["marks"])
print("\\nread only 'marks':", marks.num_rows, "rows,", marks.num_columns, "column")
stats = pq.ParquetFile("students.parquet").metadata.row_group(0).column(3).statistics
print("row-group stats for marks: min =", stats.min, " max =", stats.max)
'''),
        title='Example: Same Data, Four Formats'),
    explanation(
        ul('<strong>Column pruning</strong>: <code>SELECT AVG(marks)</code> reads only the marks column chunks.',
           '<strong>Predicate pushdown</strong>: min/max statistics per row group (Parquet) or stripe/row index (ORC) let readers skip '
           'blocks entirely, e.g. a row group with max(marks) = 100 can be skipped for <code>WHERE marks &gt; 100</code>.',
           '<strong>Better compression</strong>: similar values sit together (all cities, all marks), so dictionary and run-length encoding work well.'),
        title='Why Columnar Formats Are Faster for Analytics'),
    crossq(
        ('Parquet or ORC?', 'Both are excellent columnar formats. Parquet has the widest ecosystem support (Spark default, Delta, Iceberg, '
         'cloud warehouses); ORC is tightly integrated with Hive (ACID tables, rich indexes). Choose what your main engine favours.'),
        ('When is Avro better than Parquet?', 'For write-heavy, record-at-a-time workloads (streaming ingestion, Kafka) and when schemas '
         'evolve often, since Avro handles added/removed/renamed fields with defaults and aliases. For analytical reads, Parquet/ORC win.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Which compression codecs are used in Hadoop? What does "splittable" mean?', 'Compression & Splittability', minutes=9, cards=[
    definition(
        defbox('A compressed file is <strong>splittable</strong> if a reader can start decompressing from the middle of the file. Only then can '
               'several map tasks process different parts of one large file in parallel. A non-splittable 10 GB gzip file is processed by '
               '<strong>one</strong> task, losing all parallelism and data locality.'),
        tags('Compression', 'Splittable', 'gzip', 'bzip2', 'Snappy', 'LZ4', 'Zstandard', 'LZO'),
    ),
    comparison(
        table(['Codec', 'Ratio', 'Speed', 'Splittable as a plain file?', 'Typical use'], [
            ['gzip (deflate)', 'Good', 'Medium', 'No', 'Archives, final outputs that are read whole'],
            ['bzip2', 'Best of these', 'Slow', '<strong>Yes</strong>', 'Large text archives that must stay splittable'],
            ['Snappy', 'Lower', 'Very fast', 'No', 'Inside Parquet/ORC/Avro/SequenceFile; map output'],
            ['LZ4', 'Lower', 'Very fast', 'No', 'Map output / shuffle compression'],
            ['Zstandard (zstd)', 'Close to gzip or better', 'Fast', 'No', 'Modern default inside Parquet/ORC'],
            ['LZO', 'Lower', 'Fast', 'Yes, after building an index', 'Legacy (GPL licence, installed separately)'],
        ]),
        note('Inside <strong>container formats</strong> (Parquet, ORC, Avro, SequenceFile) splittability comes from the format: each row group, '
             'stripe or block is compressed independently. So <strong>Snappy-compressed Parquet is splittable</strong> even though a raw '
             '<code>.snappy</code> file is not.', 'Key Point'),
    ),
    example(
        pyrun('''
import bz2, gzip, lzma, random, time

random.seed(1)
lines = [f"2026-10-13 10:{i % 60:02d}:{i % 59:02d} INFO user={random.randint(1, 5000)} "
         f"page=/course/{random.choice(['dbda', 'dac', 'dai'])} status={random.choice([200, 200, 200, 404, 500])}"
         for i in range(60_000)]
data = "\\n".join(lines).encode()
print(f"original: {len(data) / 1024:,.0f} KB")

for name, fn in [("gzip -6", lambda d: gzip.compress(d, 6)),
                 ("bzip2 -9", lambda d: bz2.compress(d, 9)),
                 ("xz/lzma", lambda d: lzma.compress(d))]:
    t = time.perf_counter()
    out = fn(data)
    ms = (time.perf_counter() - t) * 1000
    print(f"{name:<9} {len(out) / 1024:>6,.0f} KB  ratio {len(data) / len(out):4.1f}x  ({ms:5.0f} ms)")
'''),
        title='Example: Ratio vs Speed on a Log File'),
    example(
        xml('''
<!-- Compress map output (shuffle) and final output -->
<property><name>mapreduce.map.output.compress</name><value>true</value></property>
<property><name>mapreduce.map.output.compress.codec</name>
          <value>org.apache.hadoop.io.compress.SnappyCodec</value></property>
<property><name>mapreduce.output.fileoutputformat.compress</name><value>true</value></property>
<property><name>mapreduce.output.fileoutputformat.compress.codec</name>
          <value>org.apache.hadoop.io.compress.GzipCodec</value></property>
''', 'mapred-site.xml'),
        title='Configuration'),
    crossq(
        ('You receive a 50 GB <code>.gz</code> log file every day. How do you process it efficiently?', 'Because gzip is not splittable, one '
         'task would read it all. Ask the source for many smaller gz files or bzip2, or run one job that decompresses and rewrites it as '
         'Parquet (or splittable chunks), then do all further processing on the converted data.'),
        ('Which codec for intermediate (shuffle) data?', 'A fast one: Snappy, LZ4 or zstd at a low level. Speed matters more than ratio there.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('What is data skew in MapReduce, and how do you handle it?', 'Data Skew', minutes=8, cards=[
    definition(
        defbox('<strong>Data skew</strong> happens when some keys have far more records than others. All values of a key go to one reducer, '
               'so that reducer runs for hours while the others finish in minutes. The job is only as fast as its slowest task.'),
        tags('Data Skew', 'Hot Key', 'Salting', 'Straggler', 'Combiner'),
    ),
    example(
        pyrun('''
import random
from collections import Counter

random.seed(3)
# 1 million page views: one "home" page gets 60% of the traffic
pages = ["home"] * 600_000 + [f"page{random.randint(1, 2000)}" for _ in range(400_000)]
R = 8
def part(key):
    return sum(map(ord, key)) % R

load = Counter(part(p) for p in pages)
print("records per reducer, plain key :", [load[r] for r in range(R)])

# Salting: spread the hot key over SALT sub-keys, aggregate twice
SALT = 8
salted = Counter(part(f"{p}#{random.randrange(SALT)}" if p == "home" else p) for p in pages)
print("records per reducer, salted key:", [salted[r] for r in range(R)])
'''),
        title='Example: Skew and Salting'),
    explanation(
        table(['Technique', 'How it helps'], [
            ['Combiner', 'Pre-aggregates on the map side so the hot key sends far fewer records'],
            ['Salting', 'Add a random suffix to the hot key (<code>home#3</code>), aggregate per salted key, then a second step strips the salt and combines'],
            ['Isolate hot keys', 'Process the few heavy keys separately (custom partitioner or separate job) and union the results'],
            ['Map-side join', 'Broadcast the small table so the skewed key never goes through a reducer'],
            ['Filter early', 'Drop NULL or dummy keys (e.g. <code>customer_id = 0</code>) that often cause skew'],
        ]),
        title='Solutions'),
    crossq(
        ('How do you detect skew?', 'In the JobHistory/Spark UI, one or a few reduce tasks take much longer and process far more input '
         'records/bytes than the median. Counting records per key (<code>GROUP BY key ORDER BY count DESC LIMIT 20</code>) confirms the hot keys.'),
    ),
]),

# ------------------------------------------------------------------ 41
Q('How would you tune a slow MapReduce job?', 'MapReduce Tuning', minutes=8, cards=[
    definition(
        table(['Area', 'What to check / change'], [
            ['Input', 'Small files → combine (<code>CombineTextInputFormat</code>); non-splittable gzip → convert; use columnar formats'],
            ['Mappers', 'Split size (<code>split.minsize/maxsize</code>) so tasks run ~1–2 min or longer, not seconds'],
            ['Map side', 'Increase <code>mapreduce.task.io.sort.mb</code> to reduce spills (check the "Spilled Records" counter); add a combiner'],
            ['Shuffle', 'Compress map output with Snappy/LZ4; filter and project in the mapper'],
            ['Reducers', 'Set a sensible <code>mapreduce.job.reduces</code>; fix skew; raise reducer memory if spilling'],
            ['Containers', 'Right-size <code>memory.mb</code> and <code>java.opts</code>; avoid GC pressure'],
            ['Joins', 'Map-side join when one side is small'],
            ['Speculation / uber', 'Speculation for stragglers on bad nodes; uber mode for tiny jobs'],
            ['Engine', 'Often the biggest win: rewrite as Spark or Hive-on-Tez to avoid disk writes between stages'],
        ]),
        tags('Tuning', 'Spills', 'io.sort.mb', 'Combiner', 'Compression', 'Counters'),
    ),
    interview(
        hl('Start with evidence: look at the job counters and task timeline (which phase is slow: map, shuffle or reduce? Are a few tasks '
           'much slower?). Then change one thing at a time. Interviewers value the method more than a list of properties.', 'Answer structure')),
    crossq(
        ('Which counters indicate problems?', '<code>Spilled Records</code> much higher than map output records (sort buffer too small), '
         'large <code>Reduce shuffle bytes</code> (no combiner/compression), high <code>GC time elapsed</code> (memory too small), and big '
         'differences in per-task input records (skew).'),
    ),
]),
])
