from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml, pyfile, txtfile, shrun

SECTION = dict(level='intermediate', title='MapReduce', questions=[

# ------------------------------------------------------------------ 24
Q('What is MapReduce? Explain its phases.', 'MapReduce Phases', minutes=9, cards=[
    definition(
        defbox('<strong>MapReduce</strong> is a programming model and execution engine for processing large datasets in parallel. '
               'You write two functions; the framework handles splitting input, scheduling tasks near the data, moving and sorting '
               'intermediate data, and retrying failures.'),
        table(['Phase', 'Input → Output', 'Where'], [
            ['Input split + RecordReader', 'File → records, e.g. (byte offset, line)', 'Map task'],
            ['Map', '(k1, v1) → list of (k2, v2)', 'Map task, in parallel per split'],
            ['Combine (optional)', '(k2, [v2]) → (k2, v2) locally', 'Map side'],
            ['Partition', 'k2 → reducer number', 'Map side'],
            ['Shuffle &amp; Sort', 'Copy each partition to its reducer; merge-sort by key', 'Between map and reduce'],
            ['Reduce', '(k2, [v2, v2, …]) → list of (k3, v3)', 'Reduce task'],
            ['OutputFormat', 'Write results to HDFS (<code>part-r-NNNNN</code>)', 'Reduce task'],
        ]),
        tags('MapReduce', 'Map', 'Reduce', 'Shuffle', 'Sort', 'Key-Value'),
    ),
    mapreduce_flow(),
    crossq(
        ('Is the reduce phase mandatory?', 'No. With <code>mapreduce.job.reduces = 0</code> the job is <strong>map-only</strong>: mapper '
         'output is written straight to HDFS (<code>part-m-NNNNN</code>), with no shuffle. Used for filtering, format conversion and DistCp.'),
        ('Can reducers start before all mappers finish?', 'Reducers can start <em>copying</em> map output early (slow start, '
         '<code>mapreduce.job.reduce.slowstart.completedmaps</code>, default 0.05), but the reduce function itself runs only after '
         'every map has finished, because any mapper could still produce a value for any key.'),
        ('Where is map output stored?', 'On the local disk of the node that ran the mapper, not in HDFS: it is temporary and replicating it would waste I/O. If that node dies before reducers fetch it, the map task is re-run.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('Write a word count program for Hadoop. How do you run Python code on Hadoop?', 'Word Count (Streaming)', minutes=10, cards=[
    definition(
        defbox('<strong>Hadoop Streaming</strong> lets any executable that reads <code>stdin</code> and writes <code>stdout</code> act as '
               'mapper or reducer. Each line of output is a record; the text before the first <strong>tab</strong> is the key.',
               'The reducer receives lines <strong>sorted by key</strong>, so all values of one key arrive together and it only '
               'has to detect where the key changes.'),
        tags('Hadoop Streaming', 'Python', 'stdin/stdout', 'Word Count', 'mapper.py', 'reducer.py'),
    ),
    example(
        pyfile('mapper.py', '''
#!/usr/bin/env python3
import sys
import re

for line in sys.stdin:
    for word in re.findall(r"[a-z]+", line.lower()):
        print(f"{word}\\t1")
'''),
        pyfile('reducer.py', '''
#!/usr/bin/env python3
import sys

current, count = None, 0
for line in sys.stdin:
    word, value = line.rstrip("\\n").split("\\t", 1)
    if word == current:
        count += int(value)
    else:
        if current is not None:
            print(f"{current}\\t{count}")
        current, count = word, int(value)
if current is not None:
    print(f"{current}\\t{count}")
'''),
        txtfile('input.txt', '''
Big data is big.
Hadoop stores big data in HDFS.
Spark and Hadoop process data.
'''),
        title='The Program'),
    example(
        p('Before submitting to a cluster, test with a Unix pipe. <code>sort</code> plays the role of the shuffle &amp; sort phase:'),
        shrun('''
cat input.txt | python3 mapper.py | sort | python3 reducer.py
'''),
        sh('''
# Same scripts on the cluster
hdfs dfs -put input.txt /user/vineeta/wc/in/
mapred streaming \\
  -files mapper.py,reducer.py \\
  -mapper "python3 mapper.py" \\
  -reducer "python3 reducer.py" \\
  -input /user/vineeta/wc/in \\
  -output /user/vineeta/wc/out
hdfs dfs -cat /user/vineeta/wc/out/part-00000
# (older syntax: hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar ...)
''', 'Run on the cluster'),
        title='Test Locally, Then Submit'),
    example(
        code('''
public class WordCount {
  public static class TokenizerMapper extends Mapper<Object, Text, Text, IntWritable> {
    private final static IntWritable one = new IntWritable(1);
    private Text word = new Text();
    public void map(Object key, Text value, Context ctx) throws IOException, InterruptedException {
      StringTokenizer itr = new StringTokenizer(value.toString().toLowerCase());
      while (itr.hasMoreTokens()) { word.set(itr.nextToken()); ctx.write(word, one); }
    }
  }
  public static class IntSumReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
    public void reduce(Text key, Iterable<IntWritable> values, Context ctx) throws IOException, InterruptedException {
      int sum = 0;
      for (IntWritable v : values) sum += v.get();
      ctx.write(key, new IntWritable(sum));
    }
  }
  public static void main(String[] args) throws Exception {
    Job job = Job.getInstance(new Configuration(), "word count");
    job.setJarByClass(WordCount.class);
    job.setMapperClass(TokenizerMapper.class);
    job.setCombinerClass(IntSumReducer.class);     // reducer reused as combiner
    job.setReducerClass(IntSumReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(IntWritable.class);
    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));
    System.exit(job.waitForCompletion(true) ? 0 : 1);
  }
}
// hadoop jar wc.jar WordCount /wc/in /wc/out
''', 'WordCount.java (classic Java API)', 'fa-brands fa-java'),
        title='The Same Job in Java'),
    crossq(
        ('Why use <code>Text</code> and <code>IntWritable</code> instead of <code>String</code> and <code>int</code>?', 'Hadoop serialises '
         'keys and values with its compact <strong>Writable</strong> interface for the shuffle. Keys must be <code>WritableComparable</code> so they can be sorted.'),
        ('What happens if the output directory already exists?', 'The job fails before starting (<code>FileAlreadyExistsException</code>). '
         'This protects you from overwriting results; delete it or use a new path.'),
    ),
]),

# ------------------------------------------------------------------ 26
Q('What happens during the shuffle and sort phase?', 'Shuffle & Sort', minutes=8, cards=[
    definition(
        defbox('<strong>Shuffle</strong> is the transfer of map output to reducers; <strong>sort</strong> ensures each reducer sees its '
               'keys in order with all values grouped. It is usually the most expensive part of a job (disk + network).'),
        tags('Shuffle', 'Sort', 'Spill', 'Merge', 'io.sort.mb', 'Circular Buffer'),
    ),
    explanation(
        table(['Side', 'Step', 'Detail'], [
            ['Map', 'Buffer', 'Map output goes into an in-memory circular buffer (<code>mapreduce.task.io.sort.mb</code>, default 100 MB)'],
            ['Map', 'Partition + sort', 'Records are tagged with their partition and sorted by (partition, key) in memory'],
            ['Map', 'Spill', 'When the buffer is 80% full (<code>mapreduce.map.sort.spill.percent</code>) a background thread spills it to a local file; the combiner runs here'],
            ['Map', 'Merge', 'All spill files are merged into one sorted, partitioned output file per map task'],
            ['Reduce', 'Copy (fetch)', 'Reducers fetch their partition from every map output over HTTP as maps finish'],
            ['Reduce', 'Merge / sort', 'Fetched segments are merged (in memory and on disk) into one sorted stream'],
            ['Reduce', 'Reduce', 'The reduce function is called once per key with an iterator over its values'],
        ]),
        title='Step by Step'),
    example(
        p('This Python simulation reproduces what the framework does between <code>map</code> and <code>reduce</code>: partition, sort, group.'),
        pyrun('''
from itertools import groupby

map_outputs = {
    "map-0": [("big", 1), ("data", 1), ("big", 1)],
    "map-1": [("data", 1), ("is", 1), ("big", 1)],
}
R = 2
def partition(key):                      # simple stand-in for hashCode() % R
    return len(key) % R

# map side: partition then sort each map's output
for m, pairs in map_outputs.items():
    parts = {r: sorted(p for p in pairs if partition(p[0]) == r) for r in range(R)}
    print(m, parts)

# reduce side: fetch the reducer's partition from every map, merge-sort, group by key
for r in range(R):
    fetched = sorted(p for pairs in map_outputs.values() for p in pairs if partition(p[0]) == r)
    groups = {k: [v for _, v in g] for k, g in groupby(fetched, key=lambda kv: kv[0])}
    print(f"reducer {r} input: {groups}  ->  output: { {k: sum(v) for k, v in groups.items()} }")
'''),
        title='Example: Simulating Shuffle & Sort'),
    crossq(
        ('How do you reduce shuffle cost?', 'Use a combiner, compress map output (<code>mapreduce.map.output.compress=true</code> with '
         'Snappy/LZ4), filter and project early in the mapper, use map-side joins, and avoid skewed keys.'),
        ('What is a secondary sort?', 'Getting the <em>values</em> for a key in sorted order (e.g. events per user by time). Use a composite '
         'key (user, time), partition and group on user only, and sort on the full key.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What is a combiner? When can you use one?', 'Combiner', minutes=7, cards=[
    definition(
        defbox('A <strong>combiner</strong> is an optional "mini-reducer" that runs on each mapper\'s output, on the map node, before the '
               'shuffle. It pre-aggregates values with the same key to reduce the data sent over the network.',
               'Hadoop may run it zero, one or many times, so the result must not depend on how often it runs: the function must be '
               '<strong>commutative and associative</strong>, and its input and output types must match the map output types.'),
        tags('Combiner', 'Mini-reducer', 'Commutative', 'Associative', 'Shuffle Reduction'),
    ),
    combiner_anim(),
    example(
        pyfile('combiner.py', '''
#!/usr/bin/env python3
# Same logic as reducer.py: sums the counts of one mapper's output
import sys
current, count = None, 0
for line in sys.stdin:
    word, value = line.rstrip("\\n").split("\\t", 1)
    if word == current:
        count += int(value)
    else:
        if current is not None:
            print(f"{current}\\t{count}")
        current, count = word, int(value)
if current is not None:
    print(f"{current}\\t{count}")
'''),
        shrun('''
echo "records shuffled WITHOUT combiner: $(python3 mapper.py < input.txt | wc -l)"
echo "records shuffled WITH combiner:    $(python3 mapper.py < input.txt | sort | python3 combiner.py | wc -l)"
echo "--- final result is the same ---"
python3 mapper.py < input.txt | sort | python3 combiner.py | sort | python3 reducer.py | head -4
'''),
        sh('''
mapred streaming -files mapper.py,combiner.py,reducer.py \\
  -mapper "python3 mapper.py" -combiner "python3 combiner.py" -reducer "python3 reducer.py" \\
  -input /wc/in -output /wc/out2
''', 'Run on the cluster'),
        title='Example: Measuring the Effect'),
    example(
        pyrun('''
# Why AVERAGE cannot be used as a combiner
mapper1 = [10, 20, 30]      # values for one key on mapper 1
mapper2 = [40]              # values on mapper 2

true_avg = sum(mapper1 + mapper2) / 4
avg_of_avgs = (sum(mapper1) / 3 + sum(mapper2) / 1) / 2
print("correct average          :", true_avg)
print("average of local averages:", avg_of_avgs, "<- WRONG")

# Fix: combine (sum, count) pairs, divide only in the reducer
partials = [(sum(mapper1), len(mapper1)), (sum(mapper2), len(mapper2))]
total, n = map(sum, zip(*partials))
print("sum/count combiner       :", total / n)
'''),
        title='Example: When a Combiner Gives Wrong Answers'),
    crossq(
        ('Combiner vs reducer?', 'A reducer is mandatory for aggregation and sees all values of a key from all mappers; a combiner is an '
         'optimisation that sees only one mapper\'s (or one spill\'s) values and is not guaranteed to run.'),
        ('Which operations are safe in a combiner?', 'Sum, count, min, max, and set union. Not average, median or distinct-count '
         '(unless you change what is emitted, e.g. (sum, count) pairs for average).'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What is a partitioner? When do you write a custom one?', 'Partitioner', minutes=7, cards=[
    definition(
        defbox('The <strong>partitioner</strong> decides which reducer receives each intermediate key. The default '
               '<code>HashPartitioner</code> computes <code>(key.hashCode() &amp; Integer.MAX_VALUE) % numReduceTasks</code>, '
               'so the same key always goes to the same reducer and keys are spread roughly evenly.'),
        tags('Partitioner', 'HashPartitioner', 'numReduceTasks', 'Custom Partitioner', 'TotalOrderPartitioner'),
    ),
    partitioner_anim(),
    example(
        pyrun('''
import ctypes

def text_hash(s):                     # org.apache.hadoop.io.Text.hashCode()
    h = 1
    for b in s.encode("utf-8"):
        b = b - 256 if b > 127 else b    # Java bytes are signed
        h = ctypes.c_int32(31 * h + b).value
    return h

def hash_partition(key, reducers):    # HashPartitioner.getPartition
    return (text_hash(key) & 0x7FFFFFFF) % reducers

for k in ["big", "data", "is", "hadoop", "spark"]:
    print(f"{k:<7} hashCode={text_hash(k):>11}  -> reducer {hash_partition(k, 3)}")
'''),
        title='Example: Exactly How Hadoop Picks the Reducer'),
    example(
        code('''
public class StatePartitioner extends Partitioner<Text, IntWritable> {
  @Override
  public int getPartition(Text key, IntWritable value, int numPartitions) {
    String state = key.toString().split(",")[0];          // key = "MH,Mumbai"
    if (state.equals("MH")) return 0;                      // big state gets its own reducer
    return 1 + (state.hashCode() & Integer.MAX_VALUE) % (numPartitions - 1);
  }
}
// job.setPartitionerClass(StatePartitioner.class); job.setNumReduceTasks(4);
''', 'Custom partitioner (Java)', 'fa-brands fa-java'),
        title='Example: Custom Partitioner'),
    crossq(
        ('When would you write a custom partitioner?', 'To send related keys to the same reducer (e.g. all cities of a state), to isolate '
         'a hot key, for secondary sort (partition on part of a composite key), or to produce globally sorted output with '
         '<code>TotalOrderPartitioner</code> (range partitioning using sampled split points).'),
        ('What if a partitioner returns a number ≥ the number of reducers?', 'The task fails with an "Illegal partition" error.'),
        ('How many output files does a job produce?', 'One per reducer (<code>part-r-00000</code> …), even if a reducer received no keys (empty file), unless <code>LazyOutputFormat</code> is used.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('What is an input split? How are the numbers of mappers and reducers decided?', 'Input Split & Task Count', minutes=8, cards=[
    definition(
        defbox('An <strong>input split</strong> is the logical chunk of input processed by one map task. It is just a description: '
               'file, start offset, length and preferred hosts. The <strong>RecordReader</strong> turns it into records, reading a '
               'little past the end of the split to finish the last record and skipping the partial record at its start.'),
        tags('Input Split', 'RecordReader', 'Number of Mappers', 'Number of Reducers', 'split.minsize', 'split.maxsize'),
    ),
    comparison(
        table(['Aspect', 'HDFS Block', 'Input Split'], [
            ['Nature', 'Physical: bytes on disk', 'Logical: a range given to a mapper'],
            ['Decided by', '<code>dfs.blocksize</code> when the file is written', 'InputFormat at job submission'],
            ['Record boundaries', 'Ignored (a line can be cut in two)', 'Respected by the RecordReader'],
            ['Default size', '128 MB', 'Equal to the block size'],
        ]),
    ),
    example(
        pyrun('''
import math
MB = 1024**2

def split_size(block, min_size=1, max_size=2**63 - 1):
    # FileInputFormat.computeSplitSize
    return max(min_size, min(max_size, block))

def n_maps(file_sizes, block=128 * MB, **kw):
    s = split_size(block, **kw)
    total = 0
    for size in file_sizes:
        # the last split may be up to 10% bigger (SPLIT_SLOP = 1.1)
        n, rest = 0, size
        while rest / s > 1.1:
            n, rest = n + 1, rest - s
        total += n + (1 if rest else 0)
    return total, s // MB

files = [1000 * MB, 300 * MB, 5 * MB]
print("default                     :", n_maps(files))
print("maxsize = 64 MB (more maps) :", n_maps(files, max_size=64 * MB))
print("minsize = 256 MB (fewer)    :", n_maps(files, min_size=256 * MB))
'''),
        title='Example: Counting Map Tasks'),
    explanation(
        ul('<strong>Mappers</strong> = number of input splits (you influence it with <code>mapreduce.input.fileinputformat.split.minsize/maxsize</code>, '
           'not by setting a number). Each file gets its own splits, which is why small files create many mappers.',
           '<strong>Reducers</strong> are set explicitly: <code>mapreduce.job.reduces</code> (default 1) or <code>job.setNumReduceTasks()</code>. '
           'A common guideline is 0.95 or 1.75 × (nodes × containers per node).',
           'Non-splittable files (e.g. gzip) always produce one split per file, however large.'),
        title='Points to Remember'),
    crossq(
        ('A line is split across two blocks. Is it processed twice or lost?', 'Neither. The RecordReader for the first split reads past '
         'its end (remote read if needed) to complete the line; the second split\'s reader skips everything up to the first newline.'),
        ('What happens with too many or too few reducers?', 'Too few: each reducer handles a huge partition, runs long and may spill heavily. '
         'Too many: many tiny output files and scheduling overhead.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What are InputFormats and OutputFormats in MapReduce?', 'InputFormat & OutputFormat', minutes=6, cards=[
    definition(
        defbox('An <strong>InputFormat</strong> defines how input is split and how each split is turned into key-value records. '
               'An <strong>OutputFormat</strong> defines how reducer (or mapper) output is written.'),
        table(['InputFormat', 'Key', 'Value', 'Use'], [
            ['TextInputFormat (default)', 'Byte offset (LongWritable)', 'Line (Text)', 'Plain text, CSV, logs'],
            ['KeyValueTextInputFormat', 'Text before the separator (tab)', 'Rest of the line', 'Output of a previous job'],
            ['NLineInputFormat', 'Offset', 'Line; each mapper gets N lines', 'Small input with CPU-heavy work per line'],
            ['SequenceFileInputFormat', 'Stored key', 'Stored value', 'Binary key-value files; chaining jobs'],
            ['CombineTextInputFormat', 'Offset', 'Line', 'Many small files packed into fewer splits'],
            ['DBInputFormat', 'Row number', 'Row', 'Read from a relational table via JDBC'],
        ]),
        table(['OutputFormat', 'Writes'], [
            ['TextOutputFormat (default)', '<code>key\\tvalue</code> lines'],
            ['SequenceFileOutputFormat', 'Binary SequenceFile, efficient input for the next job'],
            ['MultipleOutputs', 'Several named outputs from one job (e.g. good/bad records)'],
            ['LazyOutputFormat', 'Creates a file only when the first record is written (no empty part files)'],
            ['NullOutputFormat', 'Nothing (job has side effects only)'],
        ]),
        tags('InputFormat', 'TextInputFormat', 'SequenceFile', 'OutputFormat', 'RecordReader', 'RecordWriter'),
    ),
    crossq(
        ('What are the key and value given to a mapper by default?', 'With <code>TextInputFormat</code>, the key is the byte offset of the line in the file and the value is the line\'s text. The key is usually ignored.'),
        ('What does an OutputCommitter do?', 'Makes output appear atomically: tasks write to temporary attempt directories, successful attempts are committed (moved) into the output directory, and a <code>_SUCCESS</code> marker is written when the job completes.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('How does MapReduce handle task failures? What is speculative execution?', 'Task Failures & Speculation', minutes=7, cards=[
    definition(
        defbox('<strong>Task failure</strong>: if a task attempt throws an exception, its JVM dies or it stops reporting progress for '
               '10 minutes (<code>mapreduce.task.timeout</code>), the ApplicationMaster reschedules it, preferably on another node. '
               'After 4 failed attempts (<code>mapreduce.map.maxattempts</code> / <code>reduce.maxattempts</code>) the job fails.',
               '<strong>Speculative execution</strong>: if a task runs much slower than the average of its peers (a <strong>straggler</strong>, '
               'e.g. on a node with a failing disk), the AM launches a duplicate attempt elsewhere. Whichever finishes first wins; the other is killed.'),
        tags('Fault Tolerance', 'Task Attempt', 'Speculative Execution', 'Straggler', 'Blacklisting'),
    ),
    explanation(
        table(['Failure', 'What happens'], [
            ['Task attempt fails', 'Retried up to 4 times; node may be blacklisted for the job after repeated failures'],
            ['NodeManager dies', 'RM stops receiving heartbeats; its running tasks are rerun, and completed <em>map</em> tasks are rerun too because their output was on that node\'s local disk'],
            ['ApplicationMaster dies', 'RM restarts it (<code>mapreduce.am.max-attempts</code>, default 2); job recovery restores completed tasks'],
            ['ResourceManager dies', 'With RM HA, the standby RM takes over and running applications recover'],
        ]),
        title='Failure Types'),
    crossq(
        ('When should you disable speculative execution?', 'When tasks have side effects that must not run twice (writing to an external '
         'database or calling an API), or on busy clusters where duplicates waste resources. Properties: <code>mapreduce.map.speculative</code>, '
         '<code>mapreduce.reduce.speculative</code>.'),
        ('Does speculative execution fix data skew?', 'No. A task slow because it has more data will be just as slow on another node. Speculation only helps with slow <em>machines</em>.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('What are counters, the Distributed Cache and uber jobs in MapReduce?', 'Counters, Cache & Uber Mode', minutes=6, cards=[
    definition(
        table(['Feature', 'What it is', 'Example'], [
            ['Counters', 'Global counts aggregated across all tasks; built-in (records in/out, bytes, spills) and custom', 'Count malformed lines: <code>context.getCounter("QUALITY","BAD_ROWS").increment(1)</code>; in Streaming print <code>reporter:counter:QUALITY,BAD_ROWS,1</code> to stderr'],
            ['Distributed Cache', 'Ships read-only files (lookup tables, jars, scripts) to every task node once per job', '<code>-files cities.csv</code>; used for map-side joins'],
            ['Uber mode', 'Runs all tasks of a small job inside the ApplicationMaster JVM, avoiding container start-up cost', '<code>mapreduce.job.ubertask.enable=true</code> for jobs with ≤ 9 maps and ≤ 1 reduce (defaults)'],
            ['JobHistory Server', 'Keeps logs, counters and timings of finished jobs', 'Web UI on port 19888'],
        ]),
        tags('Counters', 'Distributed Cache', 'Uber Mode', 'JobHistory Server'),
    ),
    example(
        pyfile('clean_mapper.py', '''
#!/usr/bin/env python3
# Map-only job: keep valid "roll,marks" rows, count bad ones with a Hadoop counter
import sys
for line in sys.stdin:
    parts = line.strip().split(",")
    if len(parts) == 2 and parts[1].isdigit():
        print(f"{parts[0]}\\t{parts[1]}")
    else:
        sys.stderr.write("reporter:counter:QUALITY,BAD_ROWS,1\\n")
'''),
        txtfile('marks.csv', '''
2401,78
2402,abc
2403,91
broken-line
'''),
        shrun('''
python3 clean_mapper.py < marks.csv 2> counters.log
echo "--- stderr (Hadoop turns these lines into counters) ---"
cat counters.log
'''),
        title='Example: Custom Counter from a Streaming Mapper'),
    crossq(
        ('Why use counters instead of print statements?', 'Prints go to per-task logs scattered across nodes. Counters are summed by the '
         'framework and shown in one place (job output, web UI, JobHistory), and can be read programmatically to fail a job if, for example, bad rows exceed 1%.'),
    ),
]),
])
