from build import *
from build import _attrs, _t


# ------------------------------------------------------------------ drawing helpers
def _cyl(x, y, w, h, label, color='blue', step=None, focus=None, sub=None):
    """Storage cylinder."""
    c = PALETTE.get(color, color)
    e = 9
    s = (f'<g class="sbox"{_attrs(step, focus)}>'
         f'<path d="M{x} {y + e} L{x} {y + h - e} A{w/2} {e} 0 0 0 {x + w} {y + h - e} L{x + w} {y + e}" '
         f'fill="{c}" fill-opacity="0.22" stroke="{c}" stroke-width="2"/>'
         f'<ellipse cx="{x + w/2}" cy="{y + e}" rx="{w/2}" ry="{e}" fill="#1e293b" stroke="{c}" stroke-width="2"/>'
         f'<text x="{x + w/2}" y="{y + h/2 + 8}" font-size="12" fill="#f1f5f9" text-anchor="middle" font-weight="bold">{_t(label)}</text>')
    if sub:
        s += f'<text x="{x + w/2}" y="{y + h/2 + 23}" font-size="10" fill="#cbd5e1" text-anchor="middle">{_t(sub)}</text>'
    return s + '</g>'


def _grid(x, y, headers, rows, widths, rh=22, step=None, hl=None, hcolor='#0e7490', size=11):
    """Small table: hl = set of row indexes to highlight (or dict row->colour)."""
    out, cx = [], x
    for j, hd in enumerate(headers):
        out.append(scell(cx, y, widths[j], rh, hd, hcolor, '#fff', step=step, bold=True, size=size))
        cx += widths[j]
    for i, r in enumerate(rows):
        cx = x
        fill = '#162033' if i % 2 == 0 else '#0f172a'
        if hl and i in hl:
            fill = hl[i] if isinstance(hl, dict) else '#14532d'
        for j, v in enumerate(r):
            out.append(scell(cx, y + rh * (i + 1), widths[j], rh, v, fill, step=step, size=size))
            cx += widths[j]
    return ''.join(out)


def _file(x, y, label, color='blue', step=None, focus=None, w=86, h=34, sub=None, op=0.22):
    """A Parquet data file tile."""
    return sbox(x, y, w, h, label, sub or '', color, step=step, focus=focus, fill_opacity=op, size=11)


def _title(text, color='blue'):
    return stext(380, 24, text, color, 15, bold=True)


# ================================================================== 1 Foundations
def what_is_dbx_anim():
    elems = [
        _title('Databricks: one platform on top of your cloud storage'),
        sbox(20, 50, 150, 52, 'Sources', 'databases · files · Kafka\nSaaS apps · IoT', 'gray', step=1),
        sflow(170, 76, 290, 130, 'cyan', step=1, count=2),
        sbox(290, 60, 180, 120, 'Databricks', 'Spark + Photon compute\nDelta Lake tables\nUnity Catalog governance', 'blue', step=2, focus=2),
        _cyl(290, 200, 180, 55, 'Your cloud storage', 'cyan', step=2, sub='S3 · ADLS · GCS'),
        sflow(470, 85, 590, 60, 'green', step=3, count=2), sflow(470, 120, 590, 125, 'green', step=3, count=2),
        sflow(470, 155, 590, 190, 'green', step=3, count=2), sflow(470, 170, 590, 250, 'green', step=3, count=2),
        sbox(590, 40, 150, 40, 'Data engineering', 'ETL · streaming', 'green', step=3),
        sbox(590, 105, 150, 40, 'SQL & BI', 'SQL warehouses · dashboards', 'amber', step=3),
        sbox(590, 170, 150, 40, 'Data science & ML', 'notebooks · MLflow', 'purple', step=3),
        sbox(590, 235, 150, 40, 'GenAI apps', 'model serving · agents', 'pink', step=3),
        stext(380, 290, 'one copy of the data, open formats, many workloads', 'amber', 13, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        'Data arrives from operational databases, files, event streams and SaaS tools.',
        '<strong>Databricks</strong> provides managed Apache Spark (and the Photon engine), stores tables in the open <strong>Delta Lake</strong> format in <em>your</em> cloud storage, and governs them with <strong>Unity Catalog</strong>.',
        'The same tables serve data engineering pipelines, SQL analytics and dashboards, data science and machine learning, and generative-AI applications.',
        'This is the <strong>lakehouse</strong> idea: one copy of the data in open formats, with warehouse-style reliability and governance on top of a data lake.',
    ])


def control_plane_anim():
    elems = [
        _title('Control plane vs compute plane'),
        sbox(30, 50, 330, 130, 'Control plane', 'Databricks account\nweb UI · notebooks · job scheduler\ncluster manager · Unity Catalog metadata', 'purple', step=1, focus=1),
        sbox(400, 50, 330, 60, 'Classic compute plane', 'VMs in YOUR cloud account (VPC / VNet)', 'blue', step=2),
        sbox(400, 120, 330, 60, 'Serverless compute plane', 'compute in Databricks\' account, starts in seconds', 'green', step=3),
        sarrow(360, 85, 398, 80, 'gray', step=2), sarrow(360, 140, 398, 150, 'gray', step=3),
        _cyl(250, 205, 260, 60, 'Data in your cloud storage', 'cyan', step=4, sub='Delta / Parquet files never leave it'),
        sflow(565, 182, 470, 210, 'cyan', step=4, count=2), sflow(565, 112, 450, 210, 'cyan', step=4, count=2),
        stext(380, 290, 'the control plane sends instructions; compute reads and writes your data', 'amber', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        'The <strong>control plane</strong> is run by Databricks: the workspace UI, notebooks, the job scheduler, the cluster manager and the Unity Catalog metastore.',
        'In <strong>classic compute</strong>, clusters are virtual machines created inside <em>your</em> cloud account and network.',
        'With <strong>serverless compute</strong>, Databricks runs the machines in its own account in your region; they start in seconds and you do not manage instances.',
        'Either way, table data stays in your cloud storage. Compute reads and writes it; the control plane only coordinates.',
    ])


def lakehouse_anim():
    elems = [
        _title('Data lake + data warehouse = lakehouse'),
        sbox(20, 50, 220, 110, 'Data lake', 'cheap object storage, any format\nno transactions, no schema checks\n"data swamp" risk', 'gray', step=1),
        sbox(270, 50, 220, 110, 'Data warehouse', 'ACID, fast SQL, governance\nproprietary storage\nstructured data, costly copies', 'amber', step=2),
        sbox(520, 50, 220, 110, 'Lakehouse', 'open files in the lake\n+ transaction log (Delta)\n+ governance (Unity Catalog)', 'green', step=3, focus=3),
        stext(380, 190, 'what the transaction log adds to plain Parquet files', 'cyan', 13, step=4, bold=True),
        _grid(110, 205, ['Feature', 'Plain Parquet folder', 'Delta table'], [
            ['Atomic commits', 'no — readers can see half a write', 'yes'],
            ['UPDATE / DELETE / MERGE', 'rewrite folders by hand', 'one SQL statement'],
            ['Schema enforcement', 'none', 'yes, evolution on request'],
            ['Time travel', 'no', 'yes (DESCRIBE HISTORY)'],
        ], [150, 230, 160], rh=24, step=4),
    ]
    return anim(canvas(760, 335, *elems), [
        'A <strong>data lake</strong> stores any file cheaply, but it has no transactions or schema checks, so it easily becomes a "data swamp".',
        'A <strong>data warehouse</strong> gives reliable, fast SQL, but data must be loaded into its own storage and copied again for ML.',
        'A <strong>lakehouse</strong> keeps open files in the lake and adds a transaction log and governance layer on top, so one copy serves BI and ML.',
        'The Delta transaction log is what turns a folder of Parquet files into a table with atomic commits, DML, schema enforcement and time travel.',
    ])


def notebook_anim():
    elems = [
        _title('A notebook is attached to compute'),
        sbox(30, 50, 330, 230, '', '', 'gray', step=1, fill_opacity=0.08),
        stext(195, 72, 'Notebook (default language: Python)', '#f1f5f9', 12, step=1, bold=True),
        sbox(45, 85, 300, 34, 'df = spark.table("students")', '', 'blue', step=1, size=11),
        sbox(45, 128, 300, 34, '%sql SELECT course, avg(marks) …', '', 'amber', step=2, size=11, focus=2),
        sbox(45, 171, 300, 34, '%md ## Results for the review', '', 'purple', step=2, size=11),
        sbox(45, 214, 300, 34, '%run ./common_setup', '', 'green', step=3, size=11),
        sbox(45, 245, 300, 28, 'display(df)  ·  dbutils.fs.ls(...)', '', 'cyan', step=4, size=11),
        sarrow(362, 150, 430, 150, 'gray', step=1),
        sbox(435, 95, 290, 110, 'Compute', 'cluster, serverless or\nSQL warehouse\none Spark session per notebook', 'blue', step=1),
        stext(580, 240, 'magic commands change the language of one cell', 'amber', 12, step=2),
        stext(580, 258, '%run shares variables; %pip installs libraries', 'green', 12, step=3),
    ]
    return anim(canvas(760, 295, *elems), [
        'A notebook has a default language (Python, SQL, Scala or R) and runs on the compute it is attached to. All cells share one Spark session, available as <code>spark</code>.',
        'A <strong>magic command</strong> at the top of a cell switches that cell\'s language: <code>%sql</code>, <code>%python</code>, <code>%scala</code>, <code>%r</code>, or <code>%md</code> for formatted text.',
        '<code>%run ./other_notebook</code> runs another notebook inline, so its functions and variables become available. <code>%pip install</code> adds a library for this notebook only.',
        '<code>display()</code> renders a DataFrame as an interactive table or chart, and <code>dbutils</code> gives file, secret, widget and job utilities.',
    ])


def compute_anim():
    elems = [
        _title('Which compute for which job?'),
        _grid(30, 45, ['Compute', 'Used for', 'Life cycle'], [
            ['All-purpose cluster', 'interactive notebooks, many users', 'you start / auto-terminate'],
            ['Job compute', 'scheduled production jobs', 'created per run, then gone'],
            ['Serverless (notebooks/jobs)', 'same, without managing VMs', 'starts in seconds'],
            ['SQL warehouse', 'SQL editor, dashboards, BI tools', 'auto-stop when idle'],
        ], [190, 270, 240], rh=30, step=1),
        stext(380, 205, 'a cluster = 1 driver + N workers', 'cyan', 13, step=2, bold=True),
        sbox(60, 220, 120, 50, 'Driver', 'plans the job', 'purple', step=2),
        sbox(220, 220, 100, 50, 'Worker 1', 'executor', 'blue', step=2), sbox(335, 220, 100, 50, 'Worker 2', 'executor', 'blue', step=2),
        sbox(450, 220, 100, 50, 'Worker 3', 'autoscaled', 'blue', step=3, fill_opacity=0.1, focus=3),
        sbox(580, 215, 160, 60, 'Billed in DBUs', 'per second, by compute\ntype and size', 'amber', step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'Databricks has several kinds of compute: <strong>all-purpose</strong> clusters for interactive work, <strong>job compute</strong> created for each job run, <strong>serverless</strong> compute, and <strong>SQL warehouses</strong> for SQL and BI.',
        'A classic cluster has one <strong>driver</strong> that plans the work and several <strong>workers</strong> whose executors run the tasks.',
        'With <strong>autoscaling</strong> the cluster adds workers when there is a backlog of tasks and removes them when they are idle. <strong>Auto-termination</strong> shuts an idle cluster down.',
        'Usage is measured in <strong>DBUs</strong> (Databricks Units) per hour, charged per second; the rate depends on the compute type and size. With classic compute you also pay your cloud provider for the VMs.',
    ])


# ================================================================== 2 Spark on Databricks
def spark_exec_anim():
    elems = [
        _title('From one action to many tasks'),
        sbox(20, 50, 210, 70, 'Your code', 'read → filter → groupBy\n→ count()  (action)', 'gray', step=1),
        sarrow(230, 85, 285, 85, 'gray', step=2),
        sbox(290, 50, 180, 70, 'Driver', 'builds and optimises\nthe plan (Catalyst)', 'purple', step=2, focus=2),
        sarrow(470, 85, 525, 85, 'gray', step=3),
        sbox(530, 45, 210, 80, 'Job', 'Stage 1: read + filter\n(shuffle boundary)\nStage 2: aggregate', 'amber', step=3),
        stext(380, 150, 'each stage = one task per partition', 'cyan', 13, step=4, bold=True),
        sbox(40, 170, 160, 90, 'Executor 1', '', 'blue', step=4),
        sbox(300, 170, 160, 90, 'Executor 2', '', 'blue', step=4),
        sbox(560, 170, 160, 90, 'Executor 3', '', 'blue', step=4),
        _file(55, 205, 'task p0', 'green', step=4, w=60), _file(125, 205, 'task p1', 'green', step=4, w=60),
        _file(315, 205, 'task p2', 'green', step=4, w=60), _file(385, 205, 'task p3', 'green', step=4, w=60),
        _file(575, 205, 'task p4', 'green', step=4, w=60), _file(645, 205, 'task p5', 'green', step=4, w=60),
        stext(380, 285, 'transformations are lazy: nothing runs until an action', 'amber', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'You write transformations (read, filter, groupBy) and finally an <strong>action</strong> such as <code>count()</code>, <code>collect()</code>, <code>display()</code> or a write.',
        'The <strong>driver</strong> turns the code into a logical plan, optimises it with the Catalyst optimiser and creates a physical plan.',
        'Each action becomes a <strong>job</strong>. The job is split into <strong>stages</strong> at every shuffle (data exchange between machines).',
        'Each stage runs as many <strong>tasks</strong> as there are partitions. Tasks run in parallel on the executors\' cores.',
        'Transformations are <strong>lazy</strong>: Spark only records them. Work starts when an action needs a result, which lets Spark optimise the whole chain at once.',
    ])


def read_files_anim():
    elems = [
        _title('Reading files into a DataFrame'),
        _file(30, 60, 'marks.csv', 'gray', step=1, w=110), _file(30, 105, 'events.json', 'gray', step=1, w=110),
        _file(30, 150, 'part-0.parquet', 'gray', step=1, w=110),
        sarrow(145, 120, 215, 120, 'gray', step=2),
        sbox(220, 70, 240, 100, 'spark.read', '.format("csv")\n.option("header", True)\n.schema(...)  or inferSchema\n.load(path)', 'blue', step=2, focus=2),
        sarrow(460, 120, 520, 120, 'gray', step=3),
        stable(525, 75, ['roll_no', 'marks'], [['2401', '78.5'], ['2402', '88.0'], ['…', '…']], [90, 90], h=24, step=3, title='DataFrame', title_color='green'),
        stext(380, 205, 'the same plan, two languages', 'amber', 13, step=4, bold=True),
        sbox(60, 220, 300, 50, 'df.groupBy("course").avg("marks")', '', 'purple', step=4, size=11),
        sbox(400, 220, 300, 50, 'SELECT course, avg(marks) … GROUP BY', '', 'purple', step=4, size=11),
    ]
    return anim(canvas(760, 290, *elems), [
        'Raw files arrive as CSV, JSON, Parquet or other formats, usually in a Unity Catalog <strong>volume</strong> or cloud storage path.',
        '<code>spark.read</code> takes a format, options and an optional schema. With a schema given, Spark does not need to scan the files first; <code>inferSchema</code> costs an extra pass.',
        'The result is a <strong>DataFrame</strong>: a distributed table with named, typed columns.',
        'The DataFrame API and Spark SQL compile to the same optimised plan, so choose whichever is clearer for the task.',
    ])


def shuffle_anim():
    elems = [
        _title('Narrow vs wide transformations'),
        stext(190, 55, 'Narrow: filter, select, withColumn', 'green', 13, step=1, bold=True),
        _file(60, 70, 'p0', 'blue', step=1, w=60), _file(60, 115, 'p1', 'blue', step=1, w=60),
        sarrow(122, 87, 210, 87, 'green', step=1), sarrow(122, 132, 210, 132, 'green', step=1),
        _file(215, 70, 'p0′', 'green', step=1, w=60), _file(215, 115, 'p1′', 'green', step=1, w=60),
        stext(190, 175, 'each output partition needs one input partition', 'gray', 11, step=1),
        stext(570, 55, 'Wide: groupBy, join, orderBy, distinct', 'red', 13, step=2, bold=True),
        _file(430, 70, 'p0', 'blue', step=2, w=60), _file(430, 115, 'p1', 'blue', step=2, w=60),
        sflow(492, 87, 640, 87, 'red', step=3, count=2), sflow(492, 87, 640, 132, 'red', step=3, count=2),
        sflow(492, 132, 640, 87, 'red', step=3, count=2), sflow(492, 132, 640, 132, 'red', step=3, count=2),
        _file(645, 70, 'BDA', 'amber', step=2, w=60), _file(645, 115, 'AI', 'amber', step=2, w=60),
        stext(570, 175, 'rows with the same key move to the same partition', 'gray', 11, step=3),
        sbox(60, 200, 300, 70, 'repartition(n)', 'full shuffle, can increase or\ndecrease, evens out sizes', 'purple', step=4),
        sbox(400, 200, 300, 70, 'coalesce(n)', 'merges partitions without a\nshuffle, can only decrease', 'cyan', step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'A <strong>narrow</strong> transformation produces each output partition from one input partition, so it runs inside a stage with no data movement.',
        'A <strong>wide</strong> transformation needs rows from many partitions: grouping, joining, sorting and distinct.',
        'Spark performs a <strong>shuffle</strong>: rows are written out, sent over the network and regrouped by key. Shuffles are the most expensive part of most jobs.',
        '<code>repartition(n)</code> shuffles to exactly n balanced partitions; <code>coalesce(n)</code> only merges existing partitions and avoids a shuffle, so it can only reduce the count.',
    ])


def join_anim():
    elems = [
        _title('Broadcast hash join vs sort-merge join'),
        stext(190, 55, 'Broadcast hash join', 'green', 13, step=1, bold=True),
        sbox(110, 70, 160, 40, 'small: courses (3 rows)', '', 'amber', step=1, size=11),
        sflow(190, 112, 75, 160, 'amber', step=2, count=2), sflow(190, 112, 190, 160, 'amber', step=2, count=2),
        sflow(190, 112, 305, 160, 'amber', step=2, count=2),
        _file(40, 165, 'big p0', 'blue', step=1, w=70), _file(155, 165, 'big p1', 'blue', step=1, w=70),
        _file(270, 165, 'big p2', 'blue', step=1, w=70),
        stext(190, 225, 'copy the small table to every executor', 'green', 11, step=2),
        stext(190, 241, 'big table is NOT shuffled', 'green', 11, step=2, bold=True),
        stext(570, 55, 'Sort-merge join', 'red', 13, step=3, bold=True),
        _file(440, 75, 'A p0', 'blue', step=3, w=60), _file(440, 120, 'A p1', 'blue', step=3, w=60),
        _file(660, 75, 'B p0', 'purple', step=3, w=60), _file(660, 120, 'B p1', 'purple', step=3, w=60),
        sflow(500, 92, 560, 165, 'red', step=3, count=2), sflow(660, 137, 600, 165, 'red', step=3, count=2),
        sbox(520, 165, 120, 40, 'sort + merge', 'by join key', 'red', step=3, size=11),
        stext(570, 225, 'both sides shuffled by the join key', 'red', 11, step=3),
        stext(380, 278, 'AQE switches to broadcast at runtime when one side turns out small', 'amber', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'When one side of a join is small (below <code>spark.sql.autoBroadcastJoinThreshold</code>, 10 MB by default), Spark can use a <strong>broadcast hash join</strong>.',
        'The small table is sent to every executor and kept in memory as a hash table. The large table is joined where it already is, with no shuffle.',
        'When both sides are large, Spark uses a <strong>sort-merge join</strong>: both are shuffled by the join key, sorted, and merged partition by partition.',
        '<strong>Adaptive Query Execution</strong> re-plans at runtime using real sizes: it can switch a planned sort-merge join to a broadcast join and split skewed partitions.',
    ])


def cache_anim():
    elems = [
        _title('Spark cache vs Databricks disk cache'),
        sbox(30, 50, 330, 120, 'Spark cache  df.cache()', 'you choose what to cache\nstored in executor memory/disk\nlazy: filled by the first action\nfree it with unpersist()', 'blue', step=1, focus=1),
        sbox(400, 50, 330, 120, 'Disk cache (automatic)', 'copies of remote Parquet files\non workers\' local SSDs\nno code; stays consistent\nwhen files change', 'green', step=2),
        stext(380, 195, 'when caching helps', 'amber', 13, step=3, bold=True),
        _grid(80, 205, ['Good', 'Not worth it'], [
            ['a DataFrame reused in several actions', 'used once'],
            ['iterative ML training on the same data', 'larger than cluster memory'],
            ['interactive exploration of one subset', 'data that changes every run'],
        ], [300, 300], rh=24, step=3),
    ]
    return anim(canvas(760, 310, *elems), [
        'The <strong>Spark cache</strong> (<code>cache()</code> / <code>persist()</code>) keeps a DataFrame you choose in executor memory or disk. It is lazy: the first action fills it.',
        'The Databricks <strong>disk cache</strong> works automatically on supported instance types: remote Parquet/Delta files read once are copied to the workers\' local SSDs and reused.',
        'Cache only what is reused several times. Caching a DataFrame used once just adds work, and caching more than memory holds causes spilling or eviction.',
    ])


# ================================================================== 3 Delta Lake fundamentals
def delta_log_anim():
    elems = [
        _title('A Delta table = Parquet files + an ordered transaction log'),
        stext(150, 55, '_delta_log/', 'amber', 13, step=1, bold=True),
        sbox(40, 65, 220, 40, '000…000.json', 'CREATE: add file A', 'amber', step=1, size=11),
        sbox(40, 115, 220, 40, '000…001.json', 'INSERT: add file B', 'amber', step=2, size=11),
        sbox(40, 165, 220, 40, '000…002.json', 'UPDATE: remove A, add C', 'amber', step=3, size=11, focus=3),
        sbox(40, 215, 220, 40, '000…010.checkpoint.parquet', 'state summary every N commits', 'gray', step=5, size=11),
        stext(560, 55, 'data files (Parquet, never edited in place)', 'cyan', 13, step=1, bold=True),
        _file(400, 70, 'file A', 'blue', step=1), _file(500, 70, 'file B', 'blue', step=2),
        _file(600, 70, 'file C', 'green', step=3),
        stext(443, 125, 'A is removed from the log, but stays on disk', 'gray', 11, step=3),
        stext(443, 140, '(time travel, until VACUUM)', 'gray', 11, step=3),
        sbox(370, 165, 360, 75, 'Reader of version 2', 'replays 0 → 1 → 2  ⇒  current files = {B, C}\nsees all of a commit or none of it', 'purple', step=4),
        stext(380, 285, 'writers commit by creating the next JSON file atomically (optimistic concurrency)', 'amber', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Creating the table writes data file A and the first commit, <code>00000000000000000000.json</code>, which records "add A" plus the schema and properties.',
        'Each later write adds a new numbered JSON commit. An INSERT records "add B".',
        'An UPDATE never modifies a Parquet file. It writes file C with the changed rows and commits "remove A, add C". A stays on disk for time travel.',
        'A reader replays the commits up to a version to find the current set of files. A commit is a single new file, so readers see all of it or nothing: that is atomicity. Concurrent writers use optimistic concurrency and retry or fail on conflicts.',
        'Every few commits a <strong>checkpoint</strong> Parquet file summarises the state, so readers do not have to replay thousands of JSON files.',
    ])


def managed_external_anim():
    elems = [
        _title('Managed vs external tables in Unity Catalog'),
        sbox(30, 50, 330, 120, 'Managed table', 'CREATE TABLE cdac.bda.marks (…)\nUnity Catalog chooses the location\nDROP TABLE deletes the data\n(recoverable with UNDROP for 7 days)', 'green', step=1, focus=1),
        sbox(400, 50, 330, 120, 'External table', 'CREATE TABLE … LOCATION \'s3://…\'\nyou choose the path (external location)\nDROP TABLE removes only the metadata\nfiles stay', 'amber', step=2),
        stext(380, 200, 'three-level names', 'cyan', 13, step=3, bold=True),
        sbox(90, 215, 160, 50, 'catalog', 'cdac', 'purple', step=3), sarrow(250, 240, 290, 240, 'gray', step=3),
        sbox(295, 215, 160, 50, 'schema', 'bda', 'blue', step=3), sarrow(455, 240, 495, 240, 'gray', step=3),
        sbox(500, 215, 160, 50, 'table / view / volume', 'students', 'green', step=3),
    ]
    return anim(canvas(760, 285, *elems), [
        'A <strong>managed table</strong> stores its files in the storage Unity Catalog manages for the catalog or schema. Dropping it deletes the data (Unity Catalog keeps it recoverable with <code>UNDROP</code> for a limited time). Databricks recommends managed tables.',
        'An <strong>external table</strong> points to a path you choose under a registered external location. Dropping it removes only the table definition; the files remain for other tools.',
        'Every object has a three-level name: <code>catalog.schema.object</code>, for example <code>cdac.bda.students</code>.',
    ])


def schema_evolution_anim():
    elems = [
        _title('Schema enforcement and schema evolution'),
        stable(30, 70, ['roll_no', 'name', 'marks'], [['2401', 'Anuj', '78.50']], [80, 80, 80], h=26, step=1, title='table schema', title_color='blue'),
        stable(430, 70, ['roll_no', 'name', 'marks', 'grade'], [['2410', 'Ishan', '80.00', 'A']], [70, 70, 70, 70], h=26, step=2, title='new data', title_color='amber'),
        sbox(200, 145, 360, 50, 'append → AnalysisException: schema mismatch', 'enforcement: unexpected column "grade" rejected', 'red', step=2, focus=2),
        sbox(40, 215, 320, 60, '.option("mergeSchema", "true")', 'evolution: add "grade" to the table;\nold rows show NULL', 'green', step=3),
        sbox(400, 215, 320, 60, 'ALTER TABLE … ADD COLUMNS', 'explicit evolution before loading', 'purple', step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'Every Delta table has a schema stored in its transaction log.',
        '<strong>Schema enforcement</strong>: a write whose columns do not match (an extra column, or an incompatible type) is rejected, so bad data never lands silently.',
        '<strong>Schema evolution</strong> on request: with <code>mergeSchema</code> (or <code>MERGE WITH SCHEMA EVOLUTION</code>) new columns are added to the table; existing rows read them as NULL.',
        'Or change the schema explicitly with <code>ALTER TABLE … ADD COLUMNS</code>, then load.',
    ])


def merge_anim():
    elems = [
        _title('MERGE INTO: update, insert and delete in one atomic commit'),
        stable(30, 70, ['roll_no', 'marks'], [['2402', '88.00'], ['2404', '67.00'], ['2408', '59.25']], [80, 80], h=26, step=1, title='target: students', title_color='blue'),
        stable(560, 70, ['roll_no', 'marks'], [['2402', '90.00'], ['2404', '70.00'], ['2409', '81.00']], [80, 80], h=26, step=1, title='source: updates', title_color='amber'),
        sbox(240, 60, 280, 40, 'ON t.roll_no = s.roll_no', '', 'gray', step=1, size=12),
        sbox(240, 110, 280, 34, 'WHEN MATCHED → UPDATE', '2402, 2404', 'green', step=2, size=11, focus=2),
        sbox(240, 152, 280, 34, 'WHEN NOT MATCHED → INSERT', '2409', 'cyan', step=3, size=11),
        sbox(240, 194, 280, 34, 'NOT MATCHED BY SOURCE → DELETE', '2408 (with a condition)', 'red', step=4, size=11),
        stext(380, 260, 'one new version; readers see all changes or none', 'amber', 13, step=5, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        '<code>MERGE</code> joins a <strong>source</strong> (new or corrected rows) to the <strong>target</strong> table on a key.',
        'Rows that match are updated (or deleted) by <code>WHEN MATCHED</code> clauses, optionally with an extra condition.',
        'Source rows with no match are inserted by <code>WHEN NOT MATCHED</code>.',
        'Target rows with no source row can be deleted or updated by <code>WHEN NOT MATCHED BY SOURCE</code>, which keeps a table in sync with a full snapshot.',
        'All of it is one transaction: one new table version.',
    ])


def constraints_anim():
    elems = [
        _title('Constraints keep bad rows out'),
        sbox(30, 50, 330, 70, 'NOT NULL', 'roll_no INT NOT NULL\nchecked on every write', 'blue', step=1),
        sbox(400, 50, 330, 70, 'CHECK', 'CONSTRAINT valid_marks\nCHECK (marks BETWEEN 0 AND 100)', 'green', step=2, focus=2),
        stable(150, 160, ['roll_no', 'marks'], [['2404', '105']], [100, 100], h=26, step=3, title='INSERT', title_color='amber'),
        sarrow(355, 199, 420, 199, 'red', step=3),
        sbox(425, 170, 310, 60, 'whole write fails', 'DELTA_VIOLATE_CONSTRAINT_WITH_VALUES\nno partial data committed', 'red', step=3),
        stext(380, 262, 'PRIMARY KEY / FOREIGN KEY in Unity Catalog are informational, not enforced', 'gray', 12, step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'A <code>NOT NULL</code> column rejects writes that contain a null in it.',
        'A <code>CHECK</code> constraint is a boolean expression every row must satisfy. It is stored in the table properties.',
        'If any row violates a constraint, the whole transaction fails and nothing is committed.',
        'Primary and foreign key constraints can be declared in Unity Catalog for documentation and query optimisation, but they are not enforced.',
    ])


# ================================================================== 4 Time travel & optimisation
def timetravel_anim():
    elems = [
        _title('Every commit is a version you can query'),
        sbox(30, 60, 130, 50, 'v0', 'CREATE', 'blue', step=1), sbox(180, 60, 130, 50, 'v1', 'INSERT 8 rows', 'blue', step=1),
        sbox(330, 60, 130, 50, 'v2', 'UPDATE +5 marks', 'amber', step=1),
        sbox(480, 60, 130, 50, 'v3', 'DELETE (mistake!)', 'red', step=2, focus=2),
        sarrow(160, 85, 178, 85, 'gray', step=1), sarrow(310, 85, 328, 85, 'gray', step=1), sarrow(460, 85, 478, 85, 'gray', step=2),
        sbox(60, 140, 300, 50, 'SELECT … VERSION AS OF 2', 'read the table as it was', 'green', step=3),
        sbox(400, 140, 330, 50, "TIMESTAMP AS OF '2026-03-01 10:00'", 'latest version at or before that time', 'green', step=3),
        sbox(180, 215, 400, 50, 'RESTORE TABLE students TO VERSION AS OF 2', 'adds v4 = copy of v2 (history kept)', 'purple', step=4, focus=4),
        sarrow(610, 85, 640, 85, 'gray', step=4), sbox(645, 60, 90, 50, 'v4', 'RESTORE', 'purple', step=4),
    ]
    return anim(canvas(760, 285, *elems), [
        'Each committed write creates a new table version, listed by <code>DESCRIBE HISTORY</code>.',
        'Mistakes are versions too: a wrong DELETE creates v3, but v2\'s files are still there.',
        'Query an older version with <code>VERSION AS OF</code> or <code>TIMESTAMP AS OF</code> to compare or copy data.',
        '<code>RESTORE</code> makes the table look like an older version again. It is itself a new commit, so the history is never rewritten.',
    ])


def optimize_anim():
    elems = [
        _title('OPTIMIZE compacts small files; Z-ORDER co-locates values'),
        stext(170, 55, 'after 40 small appends', 'gray', 12, step=1, bold=True),
        *[_file(30 + (i % 5) * 58, 65 + (i // 5) * 34, f'{i+1}', 'red', step=1, w=50, h=28) for i in range(10)],
        sarrow(330, 120, 400, 120, 'gray', step=2),
        stext(380, 105, 'OPTIMIZE', 'amber', 12, step=2, bold=True),
        _file(420, 75, 'file 1', 'green', step=2, w=140, h=40, sub='~1 GB target'),
        _file(580, 75, 'file 2', 'green', step=2, w=140, h=40),
        stext(570, 150, 'ZORDER BY (roll_no): each file holds a narrow range', 'cyan', 12, step=3, bold=True),
        _grid(420, 160, ['file', 'min roll_no', 'max roll_no'], [['file 1', '2401', '2450'], ['file 2', '2451', '2500']], [90, 100, 100], rh=24, step=3),
        stext(380, 260, "WHERE roll_no = 2405 → file 2 skipped using min/max statistics (data skipping)", 'amber', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'Frequent small writes (streaming, hourly loads) create many small files. Each file costs an open, a request to cloud storage and metadata work.',
        '<code>OPTIMIZE</code> rewrites small files into fewer large ones (bin-packing), in a new version. Readers are not blocked.',
        '<code>ZORDER BY</code> also sorts the rows along the chosen columns so that each file covers a narrow range of their values.',
        'Delta stores min/max statistics per file. A query on <code>roll_no</code> can skip every file whose range cannot contain the value.',
    ])


def layout_anim():
    elems = [
        _title('Three ways to lay out data for faster reads'),
        sbox(20, 50, 230, 150, 'PARTITIONED BY (course)', 'one folder per value\ngood: low-cardinality column\nalways in filters, ≥ 1 GB each\nbad: too many small partitions', 'blue', step=1),
        sbox(265, 50, 230, 150, 'ZORDER BY (roll_no)', 'sorts inside files\nmust be re-run with OPTIMIZE\nrewrites all data in scope\nchange columns = full rewrite', 'amber', step=2),
        sbox(510, 50, 230, 150, 'CLUSTER BY (roll_no)', 'liquid clustering\nincremental, only new data\nchange keys any time\nCLUSTER BY AUTO picks keys', 'green', step=3, focus=3),
        stext(380, 235, 'new tables: prefer liquid clustering instead of partitioning + Z-order', 'green', 13, step=4, bold=True),
        stext(380, 258, 'keep partitioning only for very large tables with an obvious date/region filter', 'gray', 12, step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        '<strong>Partitioning</strong> writes one directory per value of a column. Filters on it skip whole folders, but high-cardinality columns create thousands of tiny partitions.',
        '<strong>Z-ordering</strong> co-locates related values inside files during OPTIMIZE. It is not incremental: re-running rewrites the data in scope.',
        '<strong>Liquid clustering</strong> (<code>CLUSTER BY</code>) clusters data incrementally, lets you change clustering keys without rewriting, and can choose keys automatically.',
        'Databricks recommends liquid clustering for new tables; it cannot be combined with partitioning or Z-order on the same table.',
    ])


def vacuum_anim():
    elems = [
        _title('VACUUM deletes files no longer needed'),
        _file(40, 70, 'A (removed v2)', 'gray', step=1, w=150, op=0.1), _file(210, 70, 'B (current)', 'green', step=1, w=150),
        _file(380, 70, 'C (current)', 'green', step=1, w=150), _file(550, 70, 'D (removed v5)', 'gray', step=1, w=150, op=0.1),
        stext(380, 135, 'retention threshold: 7 days (delta.deletedFileRetentionDuration)', 'amber', 12, step=2, bold=True),
        sbox(40, 150, 320, 60, 'removed more than 7 days ago', 'A → deleted by VACUUM', 'red', step=3, focus=3),
        sbox(400, 150, 320, 60, 'removed recently', 'D → kept', 'blue', step=3),
        stext(380, 245, 'after VACUUM you cannot time travel to versions that need deleted files', 'red', 12, step=4, bold=True),
        stext(380, 265, 'the log keeps history (30 days by default) but data files are gone', 'gray', 11, step=4),
    ]
    return anim(canvas(760, 285, *elems), [
        'UPDATE, DELETE, MERGE and OPTIMIZE leave old files on disk, marked as removed in the log. Storage keeps growing.',
        '<code>VACUUM</code> deletes files that are not part of the current version and were removed longer ago than the retention threshold (7 days by default).',
        'Recently removed files are kept so that running readers and short time travel still work.',
        'After a file is vacuumed, versions that need it can no longer be queried, even if they still appear in DESCRIBE HISTORY.',
    ])


def cdf_anim():
    elems = [
        _title('Change Data Feed: row-level changes per version'),
        sbox(30, 55, 220, 50, "delta.enableChangeDataFeed", "= true", 'purple', step=1),
        stable(300, 70, ['roll_no', 'marks', '_change_type', '_commit_version'], [
            ['2403', '91', 'insert', '3'],
            ['2401', '64', 'update_preimage', '4'],
            ['2401', '67', 'update_postimage', '4'],
            ['2402', '85', 'delete', '5'],
        ], [70, 60, 150, 120], h=26, step=2, title="table_changes('marks_log', 3)", title_color='green'),
        sbox(30, 220, 220, 50, 'Downstream', 'apply only changes to silver/gold', 'cyan', step=3),
        sflow(250, 245, 300, 245, 'cyan', step=3, count=2),
        stext(530, 230, 'cheaper than re-reading the whole table', 'amber', 12, step=3, bold=True),
        stext(530, 250, 'feeds CDC, audits and incremental ML features', 'gray', 11, step=3),
    ]
    return anim(canvas(760, 285, *elems), [
        'Enable the Change Data Feed with a table property. From then on, Delta records row-level changes for every commit.',
        'Read them with <code>table_changes()</code> (SQL) or <code>readChangeFeed</code> (Python). Updates appear as a pre-image and a post-image; each row has the version and commit timestamp.',
        'Downstream tables can process only what changed since the last run instead of recomputing from the full table.',
    ])


# ================================================================== 5 Ingestion & streaming
def medallion_anim():
    elems = [
        _title('Medallion architecture: bronze → silver → gold'),
        sbox(20, 60, 130, 70, 'Sources', 'CSV / JSON drops\nKafka · CDC', 'gray', step=1),
        sflow(150, 95, 200, 95, 'cyan', step=1, count=2),
        sbox(200, 50, 160, 90, 'Bronze', 'raw, as received\n+ ingest time, file name\nappend-only', 'amber', step=1, focus=1),
        sflow(360, 95, 400, 95, 'cyan', step=2, count=2),
        sbox(400, 50, 160, 90, 'Silver', 'cleaned, typed\nde-duplicated, joined\none row per entity', 'gray', step=2, focus=2, fill_opacity=0.35),
        sflow(560, 95, 600, 95, 'cyan', step=3, count=2),
        sbox(600, 50, 140, 90, 'Gold', 'aggregates for\ndashboards, ML\nfeatures', 'amber', step=3, focus=3, fill_opacity=0.45),
        _grid(80, 170, ['Layer', 'Who uses it', 'Quality checks'], [
            ['Bronze', 'data engineers, replay', 'none / schema only'],
            ['Silver', 'analysts, data scientists', 'types, nulls, duplicates, constraints'],
            ['Gold', 'business users, BI tools', 'business rules, reconciliations'],
        ], [120, 230, 250], rh=26, step=4),
    ]
    return anim(canvas(760, 285, *elems), [
        '<strong>Bronze</strong> tables keep the raw data exactly as received, plus metadata such as ingest time and source file, so any later step can be re-run from it.',
        '<strong>Silver</strong> tables are cleaned and conformed: correct types, valid values, duplicates removed, related data joined.',
        '<strong>Gold</strong> tables are shaped for consumption: aggregates, KPIs, features for ML, often one table per use case.',
        'Each layer adds quality guarantees and is read by a different audience. The layers are a convention, not a product feature.',
    ])


def autoloader_anim():
    elems = [
        _title('Auto Loader: incremental file ingestion'),
        _cyl(20, 60, 170, 70, 'landing volume', 'gray', step=1, sub='new files keep arriving'),
        _file(40, 150, 'day1.json', 'blue', step=1, w=70, h=28), _file(115, 150, 'day2.json', 'blue', step=1, w=70, h=28),
        _file(78, 183, 'day3.json', 'green', step=3, w=70, h=28, focus=3),
        sflow(190, 95, 270, 95, 'cyan', step=2, count=2),
        sbox(270, 50, 220, 110, 'cloudFiles stream', 'directory listing or\nfile notifications\nschema inference +\nschemaLocation', 'blue', step=2),
        sflow(490, 95, 570, 95, 'cyan', step=2, count=2),
        sbox(570, 60, 170, 70, 'bronze table', 'Delta', 'amber', step=2),
        sbox(270, 185, 220, 60, 'checkpoint', 'which files are done\n(exactly once)', 'purple', step=3),
        sbox(530, 175, 210, 75, '_rescued_data', 'values that do not fit\nthe schema are kept,\nnot lost', 'red', step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'Files keep arriving in cloud storage or a volume, often thousands per day.',
        'Auto Loader is a Structured Streaming source (<code>format("cloudFiles")</code>). It discovers new files by listing the directory or through cloud file-notification events, infers the schema and stores it in <code>schemaLocation</code>.',
        'The checkpoint records which files were processed, so each file is loaded exactly once, even after a restart. Only the new file is read on the next run.',
        'Values that do not match the schema go into a <code>_rescued_data</code> column instead of being dropped; new columns can evolve the schema.',
    ])


def streaming_anim():
    elems = [
        _title('Structured Streaming: an unbounded table processed in micro-batches'),
        _grid(30, 50, ['input rows arriving'], [['batch 0: 3 rows'], ['batch 1: 1 row'], ['batch 2: …']], [180], rh=28, step=1),
        sflow(212, 92, 280, 92, 'cyan', step=1, count=2),
        sbox(280, 50, 200, 90, 'Query', 'same DataFrame code\nas batch', 'blue', step=1),
        sflow(480, 92, 550, 92, 'cyan', step=1, count=2),
        sbox(550, 55, 190, 75, 'Sink', 'Delta table · Kafka\nforeachBatch', 'green', step=1),
        sbox(280, 160, 200, 50, 'checkpointLocation', 'offsets + state', 'purple', step=2, focus=2),
        _grid(30, 225, ['Trigger', 'Behaviour'], [
            ['default / processingTime', 'continuous micro-batches'],
            ['availableNow=True', 'process all available data, then stop'],
        ], [190, 280], rh=24, step=3),
        sbox(530, 225, 210, 60, 'watermark', 'how late data may be;\nold state is dropped', 'amber', step=4),
    ]
    return anim(canvas(760, 305, *elems), [
        'Structured Streaming treats a stream as a table that keeps growing. You write ordinary DataFrame code; Spark runs it incrementally in micro-batches and writes to a sink.',
        'The <strong>checkpoint</strong> stores source offsets and aggregation state, which gives exactly-once processing with Delta sinks and lets a stopped query resume where it left off.',
        'The <strong>trigger</strong> decides when batches run: continuously, every N seconds, or <code>availableNow</code> to process everything available and stop, which is ideal for scheduled jobs.',
        'For aggregations on event time, a <strong>watermark</strong> says how late events can arrive; state older than that is cleaned up.',
    ])


def foreachbatch_anim():
    elems = [
        _title('Upserting a stream into Delta with foreachBatch + MERGE'),
        sbox(20, 60, 160, 70, 'Change stream', 'corrections arrive\nevery minute', 'gray', step=1),
        sflow(180, 95, 250, 95, 'cyan', step=1, count=2),
        sbox(250, 50, 240, 90, 'foreachBatch(fn)', 'fn(batch_df, batch_id)\nruns once per micro-batch\nwith a normal DataFrame', 'blue', step=2, focus=2),
        sarrow(490, 95, 555, 95, 'gray', step=3),
        sbox(560, 55, 180, 80, 'MERGE INTO silver', 'update matched\ninsert new', 'green', step=3),
        sbox(250, 170, 240, 60, 'de-duplicate first', 'latest row per key in the batch', 'amber', step=3),
        stext(380, 262, 'idempotent: a retried batch must not apply changes twice', 'red', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'A streaming source delivers new and changed records, for example marks corrections or CDC events.',
        '<code>foreachBatch</code> hands every micro-batch to your function as an ordinary DataFrame, so you can use any batch operation, including MERGE.',
        'Inside the function, keep one row per key (latest change), then MERGE it into the target table.',
        'A batch can be retried after a failure, so the logic must be idempotent: MERGE on a key is; blind appends are not (use txnVersion / txnAppId options for those).',
    ])


def json_anim():
    elems = [
        _title('From nested JSON to rows and columns'),
        sbox(20, 55, 300, 110, '{ "roll_no": 2401,', '"student": {"name": "Anuj",\n "centre": "Kharghar"},\n"scores": [{"sub":"SQL","m":72},\n            {"sub":"Python","m":64}] }', 'gray', step=1),
        sarrow(325, 110, 385, 110, 'gray', step=2),
        sbox(390, 50, 350, 50, 'from_json / parse_json', 'string → STRUCT / VARIANT', 'blue', step=2),
        sbox(390, 110, 350, 50, 'student.name  ·  scores[0].m', 'dot and index access', 'purple', step=3),
        sbox(390, 170, 350, 50, 'explode(scores)', 'one row per array element', 'green', step=4, focus=4),
        stable(150, 240, ['roll_no', 'sub', 'm'], [['2401', 'SQL', '72'], ['2401', 'Python', '64']], [90, 90, 70], h=22, step=4),
        sbox(490, 240, 250, 50, 'transform / filter / aggregate', 'higher-order functions on arrays', 'amber', step=5),
    ]
    return anim(canvas(760, 315, *elems), [
        'Semi-structured data arrives as JSON strings with nested objects and arrays.',
        'Parse it with <code>from_json</code> and a schema (giving a STRUCT), or store it as a <code>VARIANT</code> with <code>parse_json</code> when the shape varies.',
        'Nested fields are read with dot notation and array elements with an index.',
        '<code>explode</code> turns each array element into its own row, ready for joins and aggregations.',
        'Higher-order functions (<code>transform</code>, <code>filter</code>, <code>aggregate</code>, <code>exists</code>) work on arrays without exploding them.',
    ])


# ================================================================== 6 Pipelines, jobs & performance
def ldp_anim():
    elems = [
        _title('Lakeflow Declarative Pipelines: declare tables, not steps'),
        sbox(20, 55, 220, 85, 'Streaming table', 'bronze_marks\nincremental from files\n(Auto Loader)', 'amber', step=1),
        sflow(240, 97, 290, 97, 'cyan', step=2, count=2),
        sbox(290, 55, 200, 85, 'Streaming table', 'silver_marks\n+ expectations', 'gray', step=2, fill_opacity=0.35),
        sflow(490, 97, 540, 97, 'cyan', step=3, count=2),
        sbox(540, 55, 200, 85, 'Materialized view', 'gold_course_avg\nkept up to date', 'amber', step=3, fill_opacity=0.45),
        _grid(60, 170, ['Expectation', 'On violation'], [
            ['EXPECT (marks IS NOT NULL)', 'keep row, record metric'],
            ['… ON VIOLATION DROP ROW', 'drop the row'],
            ['… ON VIOLATION FAIL UPDATE', 'stop the update'],
        ], [300, 230], rh=26, step=4),
        stext(380, 290, 'the engine works out order, retries, checkpoints and compute', 'green', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        'A <strong>streaming table</strong> processes each new input row once, which suits ingestion from files or Kafka.',
        'Downstream streaming tables read incrementally from upstream ones and apply cleaning logic.',
        'A <strong>materialized view</strong> holds the result of a query and is refreshed (incrementally where possible) when the pipeline updates.',
        '<strong>Expectations</strong> are data-quality rules: keep and count, drop, or fail on violation. Their metrics appear in the pipeline UI and event log.',
        'You declare the tables; the pipeline builds the dependency graph, runs steps in order, manages checkpoints and retries, and can run on serverless compute.',
    ])


def jobs_anim():
    elems = [
        _title('A Lakeflow job is a graph of tasks'),
        sbox(30, 110, 140, 50, 'ingest', 'notebook', 'blue', step=1),
        sbox(230, 50, 150, 50, 'clean_marks', 'pipeline', 'purple', step=2), sbox(230, 170, 150, 50, 'clean_attendance', 'SQL file', 'purple', step=2),
        sarrow(170, 125, 228, 80, 'gray', step=2), sarrow(170, 145, 228, 192, 'gray', step=2),
        sbox(440, 110, 150, 50, 'publish_gold', 'Python wheel', 'green', step=3),
        sarrow(380, 75, 438, 128, 'gray', step=3), sarrow(380, 195, 438, 145, 'gray', step=3),
        sbox(630, 110, 110, 50, 'notify', 'if failed', 'red', step=4),
        sarrow(590, 135, 628, 135, 'red', step=4, dashed=True),
        stext(380, 255, 'triggers: schedule · file arrival · table update · continuous · API', 'amber', 12, step=5, bold=True),
        stext(380, 275, 'per task: retries, timeout, job compute or serverless, parameters, task values', 'gray', 11, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'A job (Lakeflow Jobs, formerly Workflows) starts with a task such as a notebook that ingests data.',
        'Tasks declare dependencies. Two cleaning tasks can run in parallel once ingestion succeeds; tasks can be notebooks, pipelines, SQL, Python wheels, dbt, JARs or other jobs.',
        'A task runs only when all of its dependencies succeeded (or according to its "run if" condition).',
        'Conditional tasks and "run if" rules handle failures, for example a notification task.',
        'Jobs run on schedules, on file arrival, on table updates, continuously, or via the API, each task with its own compute, retries and timeouts.',
    ])


def cicd_anim():
    elems = [
        _title('CI/CD with Git folders and Asset Bundles'),
        sbox(20, 60, 150, 70, 'Developer', 'Git folder in the\nworkspace (branch)', 'gray', step=1),
        sarrow(170, 95, 225, 95, 'gray', step=1),
        sbox(230, 60, 140, 70, 'Git repo', 'pull request\nreview', 'purple', step=2),
        sarrow(370, 95, 425, 95, 'gray', step=2),
        sbox(430, 55, 150, 80, 'CI pipeline', 'unit tests\nbundle validate', 'blue', step=3),
        sarrow(580, 95, 630, 70, 'gray', step=4), sarrow(580, 95, 630, 125, 'gray', step=4),
        sbox(635, 45, 110, 45, 'staging', 'deploy -t staging', 'amber', step=4, size=11),
        sbox(635, 105, 110, 45, 'prod', 'deploy -t prod', 'green', step=4, size=11),
        sbox(200, 175, 360, 85, 'databricks.yml', 'jobs, pipelines, clusters, permissions\nas code, with variables per target\ndev · staging · prod', 'cyan', step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Developers work in a <strong>Git folder</strong> (formerly Repos) in the workspace, on their own branch.',
        'Changes go to the Git provider as pull requests and are reviewed.',
        'A CI pipeline (GitHub Actions, Azure DevOps, GitLab) runs unit tests and <code>databricks bundle validate</code>.',
        'On merge, the pipeline runs <code>databricks bundle deploy</code> to staging and then production targets, using a service principal.',
        'A <strong>Databricks Asset Bundle</strong> describes the code and the resources it needs (jobs, pipelines, compute, permissions) in <code>databricks.yml</code>, with settings per target.',
    ])


def udf_anim():
    elems = [
        _title('Built-in functions vs Python UDF vs pandas UDF'),
        sbox(20, 55, 230, 120, 'Built-in functions', 'run inside the JVM / Photon\noptimised, vectorised\nno serialisation\n→ always try first', 'green', step=1, focus=1),
        sbox(265, 55, 230, 120, 'Python UDF (@udf)', 'row by row\nJVM ⇄ Python serialisation\nCatalyst cannot look inside\n→ slowest', 'red', step=2),
        sbox(510, 55, 230, 120, 'pandas UDF', 'batches as Arrow\n→ pandas Series\nvectorised in Python\n→ much faster than @udf', 'amber', step=3),
        stext(380, 205, 'plan nodes you will see', 'cyan', 13, step=4, bold=True),
        _grid(140, 215, ['UDF type', 'Physical plan node'], [['@udf', 'BatchEvalPython'], ['@pandas_udf', 'ArrowEvalPython']], [200, 280], rh=26, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'Spark\'s built-in functions (<code>pyspark.sql.functions</code>, SQL functions) run inside the engine and can be optimised and vectorised.',
        'A plain Python UDF sends rows to a Python worker, runs your function once per row and sends results back: flexible but slow.',
        'A pandas UDF (vectorised UDF) exchanges data in Apache Arrow batches and calls your function on whole pandas Series, which is far cheaper per row.',
        'In the plan, Python UDFs appear as <code>BatchEvalPython</code> and pandas UDFs as <code>ArrowEvalPython</code>.',
    ])


def tuning_anim():
    elems = [
        _title('Where Spark jobs lose time'),
        _grid(30, 50, ['Symptom in the Spark UI', 'Likely cause', 'Fix'], [
            ['one task 50× longer than the rest', 'data skew on a key', 'AQE skew join, salting, filter hot key'],
            ['"Spill (disk)" in stages', 'partitions too big for memory', 'more partitions, bigger nodes'],
            ['thousands of tiny tasks', 'small files / too many partitions', 'OPTIMIZE, coalesce, AQE'],
            ['huge shuffle read/write', 'wide joins of big tables', 'broadcast, filter early, clustering'],
            ['driver out of memory', 'collect() / toPandas() on big data', 'write to a table, limit()'],
        ], [230, 230, 240], rh=30, step=1),
        stext(380, 250, 'measure first (Spark UI, query profile), change one thing, measure again', 'amber', 13, step=2, focus=2, bold=True),
    ]
    return anim(canvas(760, 270, *elems), [
        'Most slow Spark jobs show one of a few patterns in the Spark UI or the query profile: skewed tasks, spill, too many small tasks, huge shuffles, or driver memory problems.',
        'Tune by measuring: find the slow stage, identify the cause, change one setting or the code, and compare again.',
    ])


# ================================================================== 7 Governance, security & ML
def uc_anim():
    elems = [
        _title('Unity Catalog: one governance layer for the account'),
        sbox(270, 45, 220, 45, 'Metastore (per region)', '', 'purple', step=1),
        sarrow(380, 90, 160, 120, 'gray', step=2), sarrow(380, 90, 380, 120, 'gray', step=2), sarrow(380, 90, 600, 120, 'gray', step=2),
        sbox(80, 120, 160, 45, 'catalog: cdac', '', 'blue', step=2), sbox(300, 120, 160, 45, 'catalog: dev', '', 'blue', step=2),
        sbox(520, 120, 160, 45, 'catalog: system', '', 'gray', step=2),
        sarrow(160, 165, 160, 190, 'gray', step=3),
        sbox(80, 190, 160, 45, 'schema: bda', '', 'cyan', step=3),
        sbox(20, 255, 95, 40, 'tables', '', 'green', step=3, size=11), sbox(120, 255, 95, 40, 'views', '', 'green', step=3, size=11),
        sbox(220, 255, 95, 40, 'volumes', '', 'green', step=3, size=11), sbox(320, 255, 95, 40, 'models', '', 'green', step=3, size=11),
        sbox(420, 255, 95, 40, 'functions', '', 'green', step=3, size=11),
        sbox(540, 185, 200, 110, 'Across all workspaces', 'GRANT / REVOKE\nlineage · audit logs\ntags · search', 'amber', step=4, focus=4),
    ]
    return anim(canvas(760, 310, *elems), [
        'Unity Catalog has one <strong>metastore</strong> per cloud region, shared by the workspaces attached to it.',
        'Objects are organised as <strong>catalog → schema → object</strong>. Catalogs often map to environments or business units; <code>system</code> holds system tables (billing, audit, lineage).',
        'Schemas contain tables, views, volumes (files), registered ML models and functions.',
        'Permissions, lineage, auditing, tags and discovery are defined once and apply in every attached workspace.',
    ])


def access_anim():
    elems = [
        _title('Who sees what: grants, row filters and column masks'),
        sbox(20, 55, 220, 70, 'GRANT SELECT', 'ON TABLE cdac.bda.students\nTO `exam-cell`', 'blue', step=1),
        sbox(20, 140, 220, 50, 'USE CATALOG + USE SCHEMA', 'needed on the parents too', 'gray', step=1),
        stable(300, 70, ['roll_no', 'centre', 'phone'], [['2401', 'Kharghar', '98xxxxxx12'], ['2403', 'Kharghar', '99xxxxxx07']], [80, 100, 120], h=26, step=2,
               title='Kharghar coordinator sees', title_color='green'),
        sbox(300, 160, 300, 45, 'row filter', 'centre = user\'s centre', 'green', step=2, size=11),
        sbox(300, 215, 300, 45, 'column mask', 'phone masked unless in `placement-cell`', 'amber', step=3, size=11, focus=3),
        sbox(620, 70, 120, 190, 'Same table', 'different results\nfor different\nusers', 'purple', step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'Privileges are granted to groups on securables. To read a table a user needs <code>USE CATALOG</code>, <code>USE SCHEMA</code> and <code>SELECT</code>.',
        'A <strong>row filter</strong> is a SQL function attached to the table that decides which rows each user may see.',
        'A <strong>column mask</strong> is a function that returns the real value or a masked value depending on who is asking.',
        'One table, one copy of the data, but every user sees only what they are allowed to.',
    ])


def secrets_anim():
    elems = [
        _title('Credentials without passwords in code'),
        sbox(30, 55, 220, 80, 'Secret scope', 'key: mysql-password\nbacked by Databricks or\nAzure Key Vault', 'purple', step=1),
        sarrow(250, 95, 300, 95, 'gray', step=1),
        sbox(305, 55, 230, 80, 'dbutils.secrets.get(…)', 'value used at run time,\nprinted as [REDACTED]', 'blue', step=1),
        sbox(30, 165, 220, 80, 'Service principal', 'identity for jobs & CI\nOAuth, no personal token', 'green', step=2, focus=2),
        sbox(305, 165, 230, 80, 'Storage credential', 'cloud IAM role / managed\nidentity used by Unity Catalog', 'amber', step=3),
        sbox(560, 55, 180, 190, 'Policies', 'cluster policies limit\nsizes and settings;\ngroups get rights,\nnot individuals', 'cyan', step=4),
    ]
    return anim(canvas(760, 265, *elems), [
        'Passwords and API keys are stored in a <strong>secret scope</strong> and read with <code>dbutils.secrets.get</code>; notebook output redacts them.',
        'Production jobs and CI/CD run as a <strong>service principal</strong>, a non-human identity, not as a person.',
        'Access to cloud storage goes through <strong>storage credentials</strong> and external locations in Unity Catalog, not through keys in code.',
        'Cluster policies and group-based permissions keep configurations and access consistent.',
    ])


def sharing_anim():
    elems = [
        _title('Delta Sharing and Lakehouse Federation'),
        sbox(20, 60, 200, 90, 'Provider', 'C-DAC Mumbai\nCREATE SHARE results_share', 'blue', step=1),
        sflow(220, 105, 330, 105, 'green', step=2, count=3),
        stext(275, 95, 'open protocol', 'green', 10, step=2),
        sbox(330, 60, 190, 90, 'Recipient', 'another Databricks\nor pandas / Power BI /\nSpark (open client)', 'green', step=2),
        stext(270, 175, 'no copy: the recipient reads the live table', 'green', 12, step=2, bold=True),
        sbox(560, 50, 180, 50, 'Databricks query', '', 'purple', step=3),
        sarrow(650, 100, 600, 150, 'gray', step=3), sarrow(650, 100, 700, 150, 'gray', step=3),
        sbox(540, 150, 110, 45, 'MySQL', 'federated', 'amber', step=3, size=11), sbox(660, 150, 90, 45, 'Snowflake', 'federated', 'amber', step=3, size=11),
        stext(645, 220, 'query external databases in place', 'amber', 11, step=3),
        sbox(160, 220, 330, 60, 'UniForm', 'Delta table also readable as Iceberg', 'cyan', step=4),
    ]
    return anim(canvas(760, 295, *elems), [
        'With <strong>Delta Sharing</strong>, a provider adds tables (or views, volumes, models) to a <strong>share</strong> and grants it to a <strong>recipient</strong>.',
        'The recipient reads the current data directly, without a copy, either in their own Databricks workspace or with open clients (pandas, Spark, Power BI) using a credential file.',
        '<strong>Lakehouse Federation</strong> goes the other way: Databricks registers external databases (MySQL, PostgreSQL, Snowflake, …) as foreign catalogs and queries them in place.',
        '<strong>UniForm</strong> writes Iceberg metadata alongside Delta, so Iceberg engines can read the same table.',
    ])


def mlflow_anim():
    elems = [
        _title('MLflow: track, register, serve'),
        sbox(20, 60, 160, 80, 'Experiment', 'many runs', 'blue', step=1),
        sbox(200, 50, 170, 100, 'Run', 'params: C=1.0\nmetrics: accuracy\nartifacts: model', 'purple', step=1, focus=1),
        sarrow(370, 100, 420, 100, 'gray', step=2),
        sbox(425, 50, 160, 100, 'Model in Unity Catalog', 'cdac.bda.placement_model\nversion 1, 2, …\naliases: @champion', 'green', step=2),
        sarrow(585, 100, 625, 100, 'gray', step=3),
        sbox(630, 60, 115, 80, 'Serving', 'REST endpoint\nor batch', 'amber', step=3),
        sbox(200, 185, 385, 70, 'Same model, same code, reproducible', 'every run stores code version, data, environment', 'cyan', step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'An <strong>experiment</strong> groups <strong>runs</strong>; each run logs parameters, metrics and artifacts such as the trained model.',
        'A good run\'s model is registered in the <strong>model registry</strong> (in Unity Catalog: <code>catalog.schema.model</code>) as a numbered version, with aliases such as <code>@champion</code>.',
        'Registered models are deployed to a <strong>Model Serving</strong> endpoint for real-time predictions, or loaded in batch jobs.',
        'Because runs record environment and lineage, any result can be traced and reproduced.',
    ])


# ================================================================== 8 Scenarios
def sqlwh_anim():
    elems = [
        _title('Databricks SQL: warehouses for BI'),
        sbox(20, 55, 200, 90, 'Users & tools', 'SQL editor · AI/BI dashboards\nGenie · Power BI · Tableau', 'gray', step=1),
        sflow(220, 100, 290, 100, 'cyan', step=1, count=2),
        sbox(290, 50, 200, 100, 'SQL warehouse', 'Photon · result cache\nintelligent workload\nmanagement', 'blue', step=2, focus=2),
        sflow(490, 100, 560, 100, 'cyan', step=2, count=2),
        _cyl(560, 65, 180, 70, 'Delta tables', 'cyan', step=2, sub='Unity Catalog'),
        _grid(80, 180, ['Type', 'Start-up', 'Notes'], [
            ['Serverless', 'seconds', 'recommended; scales automatically'],
            ['Pro', 'minutes', 'in your cloud account'],
            ['Classic', 'minutes', 'fewer features'],
        ], [150, 120, 330], rh=26, step=3),
    ]
    return anim(canvas(760, 290, *elems), [
        'Analysts use the SQL editor, AI/BI dashboards, Genie (natural-language questions) or external BI tools through JDBC/ODBC.',
        'A <strong>SQL warehouse</strong> is compute dedicated to SQL, with Photon, caching and automatic scaling across clusters for concurrency.',
        'Serverless SQL warehouses start in seconds and are the recommended type; Pro and Classic run in your own cloud account.',
    ])


def cost_anim():
    elems = [
        _title('Where Databricks money goes'),
        sbox(20, 55, 230, 90, 'Compute (DBUs)', 'by compute type and size\nper second while running', 'amber', step=1, focus=1),
        sbox(265, 55, 230, 90, 'Cloud infrastructure', 'VMs, disks, network\n(classic compute only)', 'blue', step=1),
        sbox(510, 55, 230, 90, 'Storage', 'object storage for tables,\nold versions until VACUUM', 'cyan', step=1),
        _grid(60, 175, ['Lever', 'Effect'], [
            ['job compute / serverless instead of all-purpose', 'lower DBU rate, no idle time'],
            ['auto-termination, auto-stop on warehouses', 'no idle clusters'],
            ['spot instances for workers, right-sized nodes', 'cheaper VMs'],
            ['tags + system.billing.usage + budgets', 'see and control spend'],
        ], [360, 280], rh=26, step=2),
    ]
    return anim(canvas(760, 310, *elems), [
        'Costs come from DBUs for compute, cloud infrastructure for classic compute, and storage for tables and their old versions.',
        'Most savings come from choosing the right compute type, avoiding idle time, right-sizing, and watching usage by tag.',
    ])


def exam_pipeline_anim():
    elems = [
        _title('Scenario: CCEE results from JSON files to a rank list'),
        _file(20, 60, 'kharghar.json', 'gray', step=1, w=110), _file(20, 100, 'juhu.json', 'gray', step=1, w=110),
        sflow(130, 95, 180, 95, 'cyan', step=1, count=2),
        sbox(180, 55, 130, 80, 'bronze_results', 'raw + file name', 'amber', step=1),
        sflow(310, 95, 360, 95, 'cyan', step=2, count=2),
        sbox(360, 55, 150, 80, 'silver_results', 'typed, valid,\nlatest per roll_no', 'gray', step=2, fill_opacity=0.35),
        sflow(510, 95, 560, 95, 'cyan', step=3, count=2),
        sbox(560, 55, 180, 80, 'gold_rank_list', 'RANK() per course\npass/fail', 'amber', step=3, fill_opacity=0.45, focus=3),
        sbox(180, 170, 330, 60, 'quality checks', 'marks 0–100 · roll_no not null · duplicates', 'red', step=2),
        sbox(560, 170, 180, 60, 'consumers', 'dashboard · results PDF\nplacement cell', 'green', step=4),
    ]
    return anim(canvas(760, 250, *elems), [
        'Each centre uploads a JSON file of results to a volume; bronze keeps them as received, with the source file name.',
        'Silver parses and types the data, rejects invalid marks, and keeps only the latest record per roll number and subject.',
        'Gold computes totals and ranks per course with window functions.',
        'Dashboards, the published PDF and the placement cell all read the same gold table.',
    ])


def scd2_anim():
    elems = [
        _title('SCD Type 2: keep history of a changing attribute'),
        stable(30, 70, ['roll_no', 'centre', 'start', 'end', 'current'], [['2404', 'Kharghar', '02-03', 'NULL', 'true']],
               [70, 90, 70, 70, 70], h=26, step=1, title='before', title_color='blue'),
        sbox(450, 60, 280, 50, 'change: 2404 moves to Juhu on 03-10', '', 'amber', step=2),
        stable(30, 160, ['roll_no', 'centre', 'start', 'end', 'current'], [['2404', 'Kharghar', '02-03', '03-10', 'false'], ['2404', 'Juhu', '03-10', 'NULL', 'true']],
               [70, 90, 70, 70, 70], h=26, step=3, title='after one MERGE', title_color='green', focus_rows={0: 3, 1: 3}),
        sbox(450, 150, 280, 90, 'MERGE trick', 'source = changes (key = roll_no)\nUNION changes (key = NULL)\nmatched → close old row\nnot matched → insert new', 'purple', step=4, focus=4),
    ]
    return anim(canvas(760, 265, *elems), [
        'A Type 2 dimension keeps one row per version of an entity, with validity dates and a current flag.',
        'When an attribute changes (a student transfers centres), the history must be kept.',
        'The current row is closed (end date, current = false) and a new current row is inserted, in the same transaction.',
        'One MERGE can do both: the source contains each changed row twice, once with the real key (to close the old row) and once with a NULL key (so it is inserted).',
    ])


def compare_anim():
    elems = [
        _title('Databricks among other platforms'),
        _grid(20, 50, ['', 'Databricks', 'Snowflake', 'AWS EMR / Glue', 'Microsoft Fabric'], [
            ['Core idea', 'lakehouse on open files', 'managed cloud warehouse', 'managed open-source', 'SaaS analytics suite'],
            ['Storage', 'your object storage (Delta)', 'Snowflake-managed / Iceberg', 'your S3', 'OneLake (Delta)'],
            ['Strength', 'Spark, streaming, ML', 'SQL simplicity, sharing', 'flexibility, cost control', 'Power BI integration'],
            ['Ops effort', 'low–medium', 'very low', 'high', 'low'],
        ], [110, 165, 165, 145, 135], rh=34, step=1),
        stext(380, 245, 'the right answer depends on workloads, skills and existing cloud', 'amber', 13, step=2, bold=True),
    ]
    return anim(canvas(760, 265, *elems), [
        'Databricks, Snowflake, AWS EMR/Glue and Microsoft Fabric overlap but start from different ideas: open lakehouse, managed warehouse, managed open source, and an all-in-one SaaS suite.',
        'In interviews, compare on workloads, data formats, skills, governance and cost, not on brand.',
    ])
