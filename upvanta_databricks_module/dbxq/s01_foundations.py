from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py, sh, conf

RUN_NOTE = note('Databricks is a cloud service, so every example with an Output box was executed while this page was built on a '
                'local stand-in: <strong>Apache Spark 4.2</strong> (the engine inside Databricks Runtime) for queries, DataFrames and streaming, '
                'and <strong>delta-rs</strong>, the Rust implementation of the open Delta Lake protocol, for every Delta table operation '
                '(writes, UPDATE, DELETE, MERGE, OPTIMIZE, VACUUM, RESTORE, time travel, Change Data Feed). Each Delta table is a real '
                'folder of Parquet files with a real <code>_delta_log</code>. Results are printed one table per statement; Databricks '
                'notebooks show the same rows as an interactive grid. Features that need a workspace (clusters, jobs, Unity Catalog '
                'grants, Auto Loader, Lakeflow pipelines, Photon, model serving) are marked "shown, not executed". Most examples use the '
                'same small table, <code>cdac.bda.students</code> (8 rows).',
                'How the examples were run')

SECTION = dict(level='beginner', title='Databricks Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is Databricks? What problems does it solve and when should you use it?', 'What is Databricks', minutes=8, cards=[
    definition(
        defbox('<strong>Databricks</strong> is a cloud <strong>data and AI platform</strong> built by the original creators of Apache Spark. '
               'It runs on <strong>AWS, Microsoft Azure (as Azure Databricks) and Google Cloud</strong> and gives one workspace for data '
               'engineering, SQL analytics, data science, machine learning and generative-AI applications.',
               'Its core pieces are: managed <strong>Apache Spark</strong> plus the native <strong>Photon</strong> engine for compute; '
               '<strong>Delta Lake</strong>, an open table format that adds ACID transactions to files in your cloud storage; '
               '<strong>Unity Catalog</strong> for governance (permissions, lineage, auditing); and tools such as notebooks, Lakeflow '
               '(ingestion, declarative pipelines and jobs), Databricks SQL, MLflow and Mosaic AI. Databricks calls this architecture the '
               '<strong>lakehouse</strong>.'),
        tags('Lakehouse', 'Apache Spark', 'Photon', 'Delta Lake', 'Unity Catalog', 'MLflow', 'AWS / Azure / GCP'),
    ),
    analogy('Think of a large <strong>college campus</strong> built around one central library (your cloud storage). Every department, '
            'from the exam cell to the placement cell to the research lab, works from the same books, with one librarian (Unity Catalog) '
            'deciding who may read what. Nobody keeps private photocopies of the whole library.'),
    what_is_dbx_anim(),
    comparison(
        table(['Use Databricks when…', 'Think twice when…'], [
            ['Large volumes of raw files, logs or events must be cleaned and joined', 'The data fits comfortably in one PostgreSQL or MySQL server'],
            ['The same data feeds both BI dashboards and machine learning', 'You need an OLTP database for an application with millisecond row updates'],
            ['You need batch and streaming pipelines on the same tables', 'The team only writes SQL reports and a managed warehouse already covers it'],
            ['You want open formats (Delta, Parquet, Iceberg) in your own storage', 'You must run entirely on-premises with no cloud account'],
        ]),
        title='When to Use It'),
    real_world(
        scenario('Who uses it',
                 ul('Banks, retailers, telecoms, healthcare and media companies use Databricks for ETL, streaming, reporting and ML.',
                    'Typical users: data engineers writing PySpark and SQL pipelines, analysts in Databricks SQL or Power BI, and data scientists '
                    'training models tracked with MLflow.',
                    'At C-DAC scale: attendance logs, CCEE exam results and placement data from every centre land as files; pipelines turn them into '
                    'clean Delta tables; the exam cell queries them with SQL while a data science team trains a "likely to be placed" model on '
                    'the same tables.')),
    ),
    example(
        RUN_NOTE,
        sql('''
SELECT * FROM students ORDER BY roll_no;

SELECT course,
       COUNT(*)                         AS total,
       CAST(AVG(marks) AS DECIMAL(5,2)) AS avg_marks
FROM   students
GROUP  BY course
ORDER  BY avg_marks DESC;
'''),
        p('This is ordinary Spark SQL (ANSI SQL with extensions). The table is a Delta table; the same rows could be read from Python with '
          '<code>spark.table("students")</code>.', top=True),
        title='Example: Your First Queries'),
    steps(
        ('Get a workspace', 'Students can use <strong>Databricks Free Edition</strong> (no credit card); companies create a workspace in their '
         'AWS, Azure or GCP account.'),
        ('Pick compute', 'Use serverless compute, or create a small cluster with auto-termination.'),
        ('Create a notebook', 'Workspace → Create → Notebook; choose Python or SQL as the default language.'),
        ('Create a table', 'Upload a CSV with "Create or modify table", or run CREATE TABLE … and INSERT.'),
        ('Query and visualise', 'Run SQL, then add a chart to the result with display().'),
        title='Steps to Try It'),
    crossq(
        ('Is Databricks the same as Apache Spark?', 'No. Spark is the open-source engine. Databricks is a managed platform that includes an '
         'optimised Spark runtime plus Photon, Delta Lake, Unity Catalog, notebooks, job orchestration, SQL warehouses and ML tooling.'),
        ('Where does the data live?', 'In <em>your</em> cloud object storage (S3, ADLS Gen2 or GCS), mostly as Delta tables (Parquet data files + a '
         'transaction log). Databricks does not lock the data inside a proprietary store.'),
        ('Is Databricks a data warehouse?', 'It includes warehouse capabilities (Databricks SQL, SQL warehouses), but the platform is broader: it '
         'is a lakehouse that also covers streaming, data engineering and ML on the same tables.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('Explain the Databricks architecture: control plane, compute plane and workspace.', 'Architecture', minutes=8, cards=[
    definition(
        defbox('Databricks is split into two planes. The <strong>control plane</strong> is managed by Databricks in its own cloud account: the '
               'web application, notebooks and their code, the job scheduler, the cluster manager, and Unity Catalog metadata.',
               'The <strong>compute plane</strong> is where data is processed. With <strong>classic compute</strong>, clusters are virtual machines '
               'launched in <em>your</em> cloud account and virtual network. With <strong>serverless compute</strong>, Databricks runs the '
               'machines in a serverless compute plane in its account, in the same region, isolated per workspace.',
               'A <strong>workspace</strong> is one deployment of the UI and its objects (notebooks, jobs, clusters, SQL warehouses) for a team. '
               'An <strong>account</strong> can have many workspaces, and they can share one Unity Catalog <strong>metastore</strong> per region.'),
        tags('Control plane', 'Classic compute plane', 'Serverless compute plane', 'Workspace', 'Account', 'Metastore'),
    ),
    analogy('An airline: the <strong>control tower</strong> (control plane) plans flights and gives instructions but carries no passengers. The '
            '<strong>aircraft</strong> (compute) carry the load; some are your own planes (classic), some are chartered and ready on the runway '
            '(serverless). The cargo (data) is stored in your own warehouse at the airport, not in the tower.'),
    control_plane_anim(),
    comparison(
        table(['', 'Classic compute', 'Serverless compute'], [
            ['Where the VMs run', 'Your cloud account and VPC/VNet', 'Databricks-managed account, same region'],
            ['Start-up time', 'Minutes (VMs must boot)', 'Seconds'],
            ['Who manages instance types, versions', 'You (cluster configuration)', 'Databricks'],
            ['Billing', 'DBUs to Databricks + VM cost to your cloud provider', 'DBUs only (infrastructure included)'],
            ['Typical use', 'Custom networking, GPUs, special libraries', 'Notebooks, jobs, pipelines and SQL with no setup'],
        ]),
        title='Classic vs Serverless'),
    real_world(
        scenario('Workspaces at C-DAC',
                 p('One Databricks <strong>account</strong> for C-DAC Mumbai could have three workspaces: <code>cdac-dev</code>, '
                   '<code>cdac-test</code> and <code>cdac-prod</code>. All three attach to the same Unity Catalog metastore for the Mumbai '
                   'region, so a table such as <code>cdac.bda.students</code> is defined once and permissions decide which workspace and '
                   'which group can read or change it.')),
    ),
    example(
        sh('''
# Databricks CLI: talks to the control plane's REST API
databricks auth login --host https://adb-1234567890123456.7.azuredatabricks.net
databricks clusters list
databricks jobs list
databricks catalogs list
'''),
        sq('''
-- in any notebook or SQL editor: where am I?
SELECT current_metastore(), current_catalog(), current_schema(), current_user();
'''),
        title='Example'),
    steps(
        ('Account console', 'Create workspaces, users, groups, service principals and the regional metastore.'),
        ('Workspace', 'Each team works here: notebooks, jobs, clusters, SQL warehouses.'),
        ('Storage', 'Configure the cloud storage location that Unity Catalog uses for managed tables.'),
        ('Compute', 'Choose serverless, or classic clusters in your network.'),
        title='Steps'),
    crossq(
        ('Does table data pass through the control plane?', 'No. Compute reads and writes your data directly in cloud storage. The control plane '
         'stores notebook code, job definitions, query history and metadata, and sends commands to the compute.'),
        ('Why would a bank prefer classic compute?', 'To keep processing inside its own network with private connectivity, custom routes or '
         'firewalls, specific instance types or GPUs. Serverless now supports many network controls, so the choice is narrowing.'),
        ('What is the difference between an account and a workspace?', 'The account is the top-level billing and identity boundary (users, '
         'groups, metastores, workspaces). A workspace is one environment inside it where people do their work.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What is the difference between a data lake, a data warehouse and a lakehouse?', 'Lake vs Warehouse vs Lakehouse', minutes=8, cards=[
    definition(
        table(['', 'Data lake', 'Data warehouse', 'Lakehouse'], [
            ['Storage', 'Object storage, any file format', 'Proprietary, managed by the vendor', 'Object storage, open table format (Delta, Iceberg)'],
            ['Data types', 'Structured, semi-structured, unstructured', 'Mainly structured', 'All of them'],
            ['Transactions (ACID)', 'No', 'Yes', 'Yes, via the transaction log'],
            ['Schema', 'Schema-on-read, easily inconsistent', 'Schema-on-write, enforced', 'Enforced, with controlled evolution'],
            ['Best at', 'Cheap raw storage, ML on files', 'Fast BI SQL', 'BI, streaming and ML on one copy'],
        ]),
        defbox('A <strong>lakehouse</strong> keeps data as open files in a lake but adds a <strong>metadata and transaction layer</strong> (Delta Lake) '
               'and a <strong>governance layer</strong> (Unity Catalog), so the files behave like reliable warehouse tables.'),
        tags('Data lake', 'Data warehouse', 'Lakehouse', 'Open table format', 'ACID', 'Schema-on-read'),
    ),
    analogy('A data lake is a <strong>storeroom</strong> where anyone drops boxes; cheap, but nobody knows what is inside. A warehouse is a '
            '<strong>shop</strong> with labelled shelves, but everything must be repacked into the shop\'s own boxes. A lakehouse puts '
            '<strong>labels, a register and a lock</strong> on the storeroom, so it works like the shop without repacking.'),
    lakehouse_anim(),
    real_world(
        scenario('The old two-system setup',
                 p('Before a lakehouse, a typical setup copied data twice: raw files into a lake (for data science), then a nightly ETL into a '
                   'warehouse (for BI). The two copies drifted apart, numbers in dashboards and models disagreed, and both were paid for. On '
                   'Databricks the raw files and the curated tables live in the same storage, and dashboards and ML read the same Delta tables.')),
    ),
    example(
        pyrun('''
spark.sql("CREATE TABLE results AS SELECT roll_no, marks FROM students WHERE course = 'PGCP-BDA'")
spark.sql("UPDATE results SET marks = marks + 2 WHERE marks < 60")

loc = spark.sql("DESCRIBE DETAIL results").first()["location"]
for f in dbutils.fs.ls(loc):
    print(f.name)
print("--- _delta_log ---")
for f in dbutils.fs.ls(loc + "/_delta_log"):
    print(f.name)
'''),
        p('A Delta table is just a folder: Parquet data files plus a <code>_delta_log</code> folder with one JSON file per commit. Commit 0 '
          'is the CREATE TABLE AS SELECT; commit 1 is the UPDATE. The UPDATE did not change the first Parquet file in place: it wrote a '
          'second file and recorded in <code>…001.json</code> that the new file replaces the old one. The old file stays for time travel.',
          top=True),
        title='Example: A Table Is Files + a Log'),
    steps(
        ('Land raw data in the lake', 'Files go to cloud storage or a Unity Catalog volume, unchanged.'),
        ('Convert to Delta tables', 'Pipelines write cleaned data as Delta tables (bronze → silver → gold).'),
        ('Govern', 'Register tables in Unity Catalog and grant access to groups.'),
        ('Serve', 'BI uses SQL warehouses; data science reads the same tables from notebooks.'),
        title='Steps'),
    crossq(
        ('Is a lakehouse just Parquet files?', 'No. Plain Parquet folders have no transactions: a failed job can leave half-written files and '
         'readers may see them. Delta adds an ordered transaction log that defines exactly which files make up each version of the table.'),
        ('Can other engines read a Delta table?', 'Yes. Delta Lake is open source; Spark, Trino, Flink, DuckDB, Polars and others have Delta '
         'readers. With UniForm, a Delta table can also be read as an Apache Iceberg table.'),
        ('Does a lakehouse make a warehouse unnecessary?', 'For many teams, yes: Databricks SQL warehouses serve BI directly on Delta tables. '
         'Some organisations still keep a separate warehouse for existing tools, but the lakehouse removes the need to copy data into it.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('How do notebooks work in Databricks? Explain magic commands, dbutils and display().', 'Notebooks & dbutils', minutes=7, cards=[
    definition(
        defbox('A Databricks <strong>notebook</strong> is a document of cells attached to compute. It has a default language (Python, SQL, Scala '
               'or R); all cells share one Spark session available as <code>spark</code>. Notebooks support real-time co-editing, comments, '
               'version history, Git folders and scheduling as a job.'),
        table(['Command / tool', 'What it does'], [
            ['<code>%sql</code>, <code>%python</code>, <code>%scala</code>, <code>%r</code>', 'Run this cell in another language'],
            ['<code>%md</code>', 'Formatted text (Markdown) for documentation'],
            ['<code>%run ./notebook</code>', 'Run another notebook inline; its functions and variables become available'],
            ['<code>%pip install pkg</code>', 'Install a Python library for this notebook\'s session'],
            ['<code>%sh</code>', 'Run a shell command on the driver'],
            ['<code>display(df)</code>', 'Show a DataFrame as an interactive table with built-in charts'],
            ['<code>dbutils.fs</code>', 'List, copy, move and read files (volumes, cloud paths)'],
            ['<code>dbutils.widgets</code>', 'Notebook parameters (text, dropdown) used by jobs'],
            ['<code>dbutils.secrets</code>', 'Read secrets (passwords, keys) without printing them'],
        ]),
        tags('Notebook', 'Magic commands', '%run', '%pip', 'dbutils', 'display()', 'Volumes'),
    ),
    analogy('A notebook is a <strong>lab record book</strong>: each page (cell) can be an experiment in Python, a query in SQL or a written '
            'observation in Markdown, and the whole book is run on the lab\'s equipment (the attached compute).'),
    notebook_anim(),
    real_world(
        scenario('A weekly results notebook',
                 ul('Cell 1 (<code>%md</code>): what the notebook does and who owns it.',
                    'Cell 2 (Python): <code>dbutils.widgets.text("exam", "CCEE")</code> so the job can pass the exam name.',
                    'Cell 3 (<code>%sql</code>): the result query, displayed as a table and a bar chart.',
                    'The notebook is scheduled as a Lakeflow job every Monday at 07:00.')),
    ),
    example(
        pyrun('''
dbutils.fs.put("/Volumes/cdac/bda/raw/attendance.csv",
               "roll_no,date,present\\n2401,2026-03-02,1\\n2402,2026-03-02,0\\n2403,2026-03-02,1\\n", True)

display(dbutils.fs.ls("/Volumes/cdac/bda/raw/"))

att = (spark.read.option("header", True).option("inferSchema", True)
            .csv("/Volumes/cdac/bda/raw/attendance.csv"))
att.printSchema()
display(att)
'''),
        sq('''
%sql
-- a SQL cell in a Python notebook; the CSV file can be queried directly
SELECT * FROM read_files('/Volumes/cdac/bda/raw/attendance.csv', format => 'csv', header => true);
''', title='Notebook cells (shown, not executed)'),
        p('Volumes (<code>/Volumes/&lt;catalog&gt;/&lt;schema&gt;/&lt;volume&gt;/</code>) are the Unity Catalog way to store and govern files. '
          'The older DBFS root (<code>dbfs:/</code>) and mounts still work in some workspaces but are no longer recommended.', top=True),
        title='Example'),
    steps(
        ('Create', 'Workspace → Create → Notebook; pick a default language.'),
        ('Attach compute', 'Choose serverless or a running cluster from the compute selector.'),
        ('Write cells', 'Mix languages with magic commands; document with %md.'),
        ('Parameterise', 'Add widgets so a job can pass values.'),
        ('Share and version', 'Use Git folders for version control and share the notebook with a group.'),
        title='Steps'),
    crossq(
        ('Can a SQL cell use a DataFrame created in Python?', 'Yes, register it first: <code>df.createOrReplaceTempView("att")</code>, then '
         '<code>%sql SELECT * FROM att</code>. Both languages share the same Spark session.'),
        ('What is the difference between %run and dbutils.notebook.run()?', '<code>%run</code> runs the other notebook inline in the same '
         'session (shared variables). <code>dbutils.notebook.run(path, timeout, args)</code> starts it as a separate run and only returns a '
         'string exit value; it is used for simple orchestration.'),
        ('Why should secrets come from dbutils.secrets and not be written in the code?', 'Code is saved, versioned and shared. '
         '<code>dbutils.secrets.get(scope, key)</code> reads the value at run time, and Databricks redacts it if it is printed.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What types of compute does Databricks offer? Explain clusters, autoscaling, auto-termination and DBUs.', 'Compute & DBUs', minutes=8, cards=[
    definition(
        table(['Compute', 'Purpose', 'Notes'], [
            ['<strong>All-purpose compute</strong>', 'Interactive notebooks, shared by a team', 'Started manually; auto-terminates when idle'],
            ['<strong>Job compute</strong>', 'Runs a scheduled job, then terminates', 'Cheaper DBU rate than all-purpose; isolated per run'],
            ['<strong>Serverless compute</strong>', 'Notebooks, jobs and pipelines without managing VMs', 'Starts in seconds; billed only while working'],
            ['<strong>SQL warehouse</strong>', 'SQL editor, dashboards, BI tools (Power BI, Tableau)', 'Serverless, Pro or Classic; Photon on'],
            ['<strong>Instance pool</strong>', 'Ready idle VMs that clusters can grab', 'Cuts cluster start time on classic compute'],
        ]),
        defbox('A classic cluster is one <strong>driver</strong> node plus zero or more <strong>worker</strong> nodes, running a chosen '
               '<strong>Databricks Runtime</strong> (DBR) version, such as an LTS release, or DBR ML with ML libraries pre-installed. '
               '<strong>Autoscaling</strong> sets a min and max number of workers. <strong>Auto-termination</strong> stops an idle cluster after '
               'N minutes. An <strong>access mode</strong> (standard/shared or dedicated/single-user) decides how Unity Catalog isolates users.',
               'Usage is measured in <strong>DBUs</strong> (Databricks Units): a normalised unit of processing per hour, billed per second. The '
               'price per DBU depends on the cloud, the pricing tier and the compute type; classic compute also incurs the cloud provider\'s VM '
               'charges.'),
        tags('All-purpose', 'Job compute', 'Serverless', 'SQL warehouse', 'Autoscaling', 'Auto-termination', 'DBU', 'Databricks Runtime'),
    ),
    analogy('Compute options are like <strong>transport</strong>: an all-purpose cluster is a car you keep running for the team; job compute is '
            'a cab booked for one trip; serverless is a metro that is always there and charges per ride; a SQL warehouse is a dedicated bus '
            'route for report users.'),
    compute_anim(),
    real_world(
        scenario('Cutting a lab bill',
                 p('A batch of 60 students each creates an all-purpose cluster with no auto-termination for a Spark lab and leaves it running '
                   'overnight. The fix: a <strong>cluster policy</strong> that limits node types and size and forces auto-termination at 30 minutes, '
                   'a shared cluster per lab group (or serverless notebooks), and job compute for the scheduled grading job.')),
    ),
    example(
        conf('''
{
  "cluster_name": "bda-lab-shared",
  "spark_version": "16.4.x-scala2.12",
  "node_type_id": "Standard_D4ds_v5",
  "autoscale": { "min_workers": 1, "max_workers": 4 },
  "autotermination_minutes": 30,
  "data_security_mode": "USER_ISOLATION",
  "spark_conf": { "spark.sql.shuffle.partitions": "auto" },
  "custom_tags": { "course": "PGCP-BDA", "owner": "lab-team" }
}
''', title='Cluster definition (Clusters API / UI JSON)'),
        sq('''
-- what did compute cost last month? (Unity Catalog system tables)
SELECT usage_date, sku_name, SUM(usage_quantity) AS dbus
FROM   system.billing.usage
WHERE  usage_date >= date_trunc('MONTH', current_date() - INTERVAL 1 MONTH)
GROUP  BY usage_date, sku_name
ORDER  BY usage_date;
'''),
        title='Example'),
    steps(
        ('Prefer serverless or job compute', 'For scheduled work, never reuse an always-on all-purpose cluster.'),
        ('Set autoscaling ranges', 'Small min, sensible max; check the Spark UI before raising it.'),
        ('Always set auto-termination', '15–60 minutes for interactive clusters.'),
        ('Use cluster policies', 'Limit sizes, runtime versions and require tags for cost tracking.'),
        ('Watch system.billing.usage', 'Review DBUs by tag, job and warehouse every month.'),
        title='Steps'),
    crossq(
        ('Why is job compute cheaper than all-purpose compute?', 'Databricks charges a lower DBU rate for automated job workloads than for '
         'interactive all-purpose clusters, and job clusters exist only for the duration of the run.'),
        ('What is the difference between a standard (shared) and a dedicated (single-user) access mode?', 'Standard mode lets many users share '
         'a cluster with Unity Catalog isolation between them (some low-level APIs are restricted). Dedicated mode assigns the cluster to one '
         'user or group and allows all features, such as RDD APIs and some ML libraries.'),
        ('What is Photon?', 'A vectorised query engine written in C++ that runs Spark SQL and DataFrame operations faster. It is enabled on SQL '
         'warehouses and serverless and can be enabled on clusters; it uses a higher DBU rate but often finishes jobs in much less time.'),
    ),
]),

])
