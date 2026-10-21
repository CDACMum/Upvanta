from build import *


def _file(x, y, name, color='gray', step=None, focus=None, w=150, h=34, sub=''):
    return sbox(x, y, w, h, name, sub, color, step=step, focus=focus, size=11)


# ------------------------------------------------------------------ foundations
def hive_intro():
    elems = [
        stext(380, 24, 'From a SQL query to a distributed job', 'blue', 15, bold=True),
        sbox(20, 55, 200, 70, 'Analyst writes SQL', 'SELECT city, AVG(marks)\nFROM students GROUP BY city', 'gray', step=1, focus=1, size=12),
        sbox(280, 55, 200, 70, 'Hive', 'parses, plans, optimises\nlooks up table schema', 'amber', step=2, focus=2),
        sarrow(220, 90, 278, 90, 'amber', step=2),
        sbox(540, 40, 200, 100, '', '', 'blue', step=3, fill_opacity=0.08),
        stext(640, 60, 'Tez / MapReduce / Spark job', 'blue', 12, step=3, bold=True, focus=3),
        sbox(555, 72, 55, 30, 'task', '', 'blue', step=3, size=11), sbox(612, 72, 55, 30, 'task', '', 'blue', step=3, size=11),
        sbox(669, 72, 55, 30, 'task', '', 'blue', step=3, size=11), sbox(583, 106, 55, 28, 'task', '', 'blue', step=3, size=11),
        sbox(641, 106, 55, 28, 'task', '', 'blue', step=3, size=11),
        sarrow(480, 90, 538, 90, 'blue', step=3),
        sbox(120, 190, 520, 60, '', '', 'green', step=4, fill_opacity=0.08),
        stext(380, 210, 'HDFS / S3: plain files (CSV, ORC, Parquet)', 'green', 12, step=4, bold=True),
        _file(140, 220, 'part-0001.orc', 'green', step=4, w=150, h=24), _file(305, 220, 'part-0002.orc', 'green', step=4, w=150, h=24),
        _file(470, 220, 'part-0003.orc', 'green', step=4, w=150, h=24),
        sflow(380, 190, 640, 140, 'green', step=4, count=3),
        sbox(280, 280, 200, 36, 'Result table', '', 'purple', step=5, focus=5, size=12),
        sflow(560, 140, 420, 280, 'purple', step=5, count=2),
    ]
    return anim(canvas(760, 330, *elems), [
        'An analyst writes ordinary SQL (HiveQL). They do not need to know Java, MapReduce or how the cluster works.',
        '<strong>Hive</strong> parses the query, checks the table definition in its <strong>metastore</strong>, and builds an optimised execution plan.',
        'The plan is turned into a <strong>distributed job</strong> (Tez, MapReduce or Spark) whose tasks run in parallel across the cluster under YARN.',
        'The tasks read the table\'s data straight from <strong>files in HDFS or cloud storage</strong>. A Hive table is just a directory of files plus a schema.',
        'The aggregated result is returned to the analyst like any database query. Hive feels like a database, but it is a SQL layer over files.',
    ])


def hive_arch():
    elems = [
        stext(380, 22, 'Hive architecture', 'blue', 15, bold=True),
        sbox(20, 45, 150, 40, 'Beeline (CLI)', '', 'gray', step=1, size=12),
        sbox(20, 95, 150, 40, 'JDBC / ODBC apps', '', 'gray', step=1, size=12),
        sbox(20, 145, 150, 40, 'Hue / BI tools', '', 'gray', step=1, size=12),
        sbox(220, 80, 150, 70, 'HiveServer2', 'sessions · auth\nconcurrency', 'cyan', step=2, focus=2),
        sarrow(170, 65, 218, 100, 'cyan', step=2), sarrow(170, 115, 218, 115, 'cyan', step=2), sarrow(170, 165, 218, 130, 'cyan', step=2),
        sbox(420, 40, 320, 150, '', '', 'amber', step=3, fill_opacity=0.07),
        stext(580, 60, 'Driver', 'amber', 13, step=3, bold=True),
        sbox(435, 72, 95, 50, 'Compiler', 'parse · analyse', 'amber', step=3, focus=3, size=11),
        sbox(535, 72, 95, 50, 'Optimizer', 'CBO · rules', 'amber', step=3, focus=3, size=11),
        sbox(635, 72, 95, 50, 'Executor', 'runs stages', 'amber', step=3, focus=3, size=11),
        sarrow(370, 115, 433, 100, 'amber', step=3),
        sbox(435, 230, 160, 64, 'Metastore', 'schemas · locations\npartitions', 'purple', step=4, focus=4),
        sbox(615, 236, 125, 52, 'MySQL / Postgres', 'backing DB', 'gray', step=4, size=11),
        sarrow(482, 122, 500, 228, 'purple', step=4), sarrow(595, 262, 613, 262, 'purple', step=4),
        sbox(20, 230, 190, 64, 'Tez / MR / Spark', 'on YARN', 'blue', step=5, focus=5),
        sbox(225, 230, 190, 64, 'HDFS / S3', 'data files', 'green', step=5, focus=5),
        sarrow(682, 122, 140, 228, 'blue', step=5, mid=(700, 215)),
        sflow(320, 230, 210, 262, 'green', step=5, count=2),
    ]
    return anim(canvas(760, 305, *elems), [
        '<strong>Clients</strong>: Beeline (the command-line client), applications over JDBC/ODBC, and tools such as Hue, Tableau or Power BI.',
        '<strong>HiveServer2</strong> is the server clients connect to (default port 10000). It handles many concurrent sessions and authentication (Kerberos, LDAP).',
        'The <strong>Driver</strong> receives the query. The <strong>compiler</strong> parses it and checks it; the <strong>optimizer</strong> rewrites the plan (predicate pushdown, partition pruning, join order); the <strong>executor</strong> runs the resulting stages in order.',
        'During compilation the driver asks the <strong>Metastore</strong> for the table\'s columns, file format, location and partitions. The metastore keeps this metadata in a normal relational database such as MySQL.',
        'The plan runs as <strong>Tez, MapReduce or Spark</strong> jobs on YARN, which read and write the data files in <strong>HDFS or S3</strong>. Hive itself stores no data.',
    ])


def query_flow():
    labels = [('1', 'executeQuery', 'Beeline → HiveServer2'), ('2', 'getPlan', 'Driver → Compiler'),
              ('3', 'getMetadata', 'Compiler → Metastore'), ('4', 'sendMetadata', 'columns, location, partitions'),
              ('5', 'sendPlan', 'optimised DAG of stages'), ('6', 'executePlan', 'Executor → Tez on YARN'),
              ('7', 'fetchResults', 'results → Beeline')]
    elems = [stext(380, 22, 'Life of a Hive query', 'blue', 15, bold=True)]
    cols = [('Beeline', 70, 'gray'), ('HiveServer2 / Driver', 230, 'cyan'), ('Compiler', 390, 'amber'),
            ('Metastore', 540, 'purple'), ('Tez / YARN / HDFS', 690, 'blue')]
    for name, x, c in cols:
        elems.append(sbox(x - 65, 40, 130, 34, name, '', c, size=11))
        elems.append(f'<line x1="{x}" y1="74" x2="{x}" y2="320" stroke="#475569" stroke-dasharray="4,4"/>')
    hops = [(70, 230), (230, 390), (390, 540), (540, 390), (390, 230), (230, 690), (690, 70)]
    for i, ((x1, x2), (n, t, sub)) in enumerate(zip(hops, labels)):
        y = 100 + i * 32
        color = ['cyan', 'amber', 'purple', 'purple', 'amber', 'blue', 'green'][i]
        elems.append(sarrow(x1, y, x2 + (-4 if x2 > x1 else 4), y, color, step=i + 1))
        elems.append(stext((x1 + x2) / 2, y - 5, f'{n}. {t}', color, 11, step=i + 1, focus=i + 1, bold=True))
    return anim(canvas(760, 330, *elems), [
        'The user runs a query in Beeline. It is sent to <strong>HiveServer2</strong>, which creates a session and hands the query to the <strong>Driver</strong>.',
        'The Driver asks the <strong>Compiler</strong> for an execution plan. The compiler parses the SQL into an abstract syntax tree and checks the syntax.',
        'For semantic analysis the compiler needs metadata: does the table exist, what are its columns and types, where are its files? It asks the <strong>Metastore</strong>.',
        'The Metastore returns the schema, storage format, HDFS location and the list of partitions (which is how partition pruning becomes possible).',
        'The compiler and optimizer produce a <strong>DAG of stages</strong> (map/reduce or Tez vertices, plus metadata operations) and send the plan back to the Driver.',
        'The Executor submits the stages to the execution engine. Tez runs them as YARN containers that read the table\'s files from HDFS.',
        'Results are written to a temporary location and <strong>fetched</strong> back through HiveServer2 to Beeline, row by row.',
    ])


# ------------------------------------------------------------------ metastore & loading
def metastore_modes():
    elems = [
        stext(130, 26, 'Embedded', 'gray', 14, bold=True),
        stext(380, 26, 'Local', 'amber', 14, bold=True),
        stext(630, 26, 'Remote (production)', 'green', 14, bold=True),
        '<line x1="255" y1="15" x2="255" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        '<line x1="505" y1="15" x2="505" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(30, 50, 200, 150, '', '', 'gray', step=1, fill_opacity=0.07),
        stext(130, 70, 'one JVM', 'gray', 11, step=1),
        sbox(50, 80, 160, 40, 'Hive / Driver', '', 'gray', step=1, size=12),
        sbox(50, 135, 160, 50, 'Derby DB', 'embedded', 'gray', step=1, focus=1, size=12),
        stext(130, 230, 'one user at a time', 'red', 12, step=1),
        stext(130, 248, 'testing only', 'red', 12, step=1),
        sbox(280, 50, 200, 100, '', '', 'amber', step=2, fill_opacity=0.07),
        stext(380, 70, 'one JVM', 'amber', 11, step=2),
        sbox(300, 85, 160, 50, 'Hive + Metastore', 'service code', 'amber', step=2, size=12),
        sbox(300, 190, 160, 50, 'MySQL', 'separate server', 'blue', step=2, focus=2, size=12),
        sarrow(380, 135, 380, 188, 'amber', step=2),
        stext(380, 268, 'many users, but every client', 'amber', 11, step=2),
        stext(380, 284, 'needs DB credentials', 'amber', 11, step=2),
        sbox(525, 45, 95, 40, 'HS2', '', 'cyan', step=3, size=12), sbox(640, 45, 95, 40, 'Spark', '', 'cyan', step=3, size=12),
        sbox(570, 125, 120, 50, 'Metastore', 'Thrift :9083', 'green', step=3, focus=3, size=12),
        sarrow(572, 85, 615, 123, 'green', step=3), sarrow(688, 85, 650, 123, 'green', step=3),
        sbox(570, 210, 120, 46, 'MySQL', '', 'blue', step=3, size=12),
        sarrow(630, 175, 630, 208, 'green', step=3),
        stext(630, 282, 'shared by Hive, Spark, Trino', 'green', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        '<strong>Embedded</strong>: the metastore service and an embedded Derby database run inside the same JVM as Hive. Only one session can use it. Fine for a laptop, never for a cluster.',
        '<strong>Local</strong>: the metastore code still runs inside each Hive process, but the metadata is in a separate MySQL/PostgreSQL server, so several users can share it. Every client needs the database credentials.',
        '<strong>Remote</strong>: the metastore runs as its own service (Thrift, default port 9083). HiveServer2, Spark and other clients talk to it over the network; only it talks to the database.',
        'Remote mode is the production standard because one metastore becomes the shared <strong>catalog</strong> for Hive, Spark, Trino/Presto and Impala: a table created in one is visible in all.',
    ])


def load_data_anim():
    elems = [
        stext(380, 24, 'LOAD DATA: moving vs copying files', 'blue', 15, bold=True),
        sbox(20, 60, 200, 60, 'Your laptop / edge node', 'marks.csv (local disk)', 'gray', step=1, size=12),
        sbox(20, 190, 200, 60, 'HDFS landing area', '/landing/marks.csv', 'gray', step=3, size=12),
        sbox(480, 110, 260, 90, '', '', 'green', step=1, fill_opacity=0.08),
        stext(610, 132, 'table directory', 'green', 12, step=1, bold=True),
        stext(610, 150, '/user/hive/warehouse/cdac.db/marks/', 'green', 11, step=1),
        _file(500, 160, 'marks.csv', 'green', step=2, focus=2, w=105, h=28),
        sflow(220, 90, 500, 170, 'cyan', step=2, count=3),
        stext(345, 105, 'LOAD DATA LOCAL INPATH', 'cyan', 12, step=2, bold=True),
        stext(345, 121, 'COPIES the file', 'cyan', 11, step=2),
        _file(615, 160, 'marks_1.csv', 'green', step=4, focus=4, w=110, h=28),
        sflow(220, 220, 615, 175, 'amber', step=4, count=3),
        stext(345, 240, 'LOAD DATA INPATH (no LOCAL)', 'amber', 12, step=4, bold=True),
        stext(345, 256, 'MOVES the file (it disappears)', 'amber', 11, step=4),
        '<g data-step="5"><line x1="25" y1="195" x2="215" y2="245" stroke="#ef4444" stroke-width="3"/><line x1="215" y1="195" x2="25" y2="245" stroke="#ef4444" stroke-width="3"/></g>',
        stext(610, 230, 'no parsing, no validation:', 'pink', 12, step=6, focus=6),
        stext(610, 246, 'files are placed as they are', 'pink', 12, step=6),
    ]
    return anim(canvas(760, 280, *elems), [
        'A Hive table is a directory. Loading data means getting files into that directory.',
        '<code>LOAD DATA <strong>LOCAL</strong> INPATH</code> reads a file from the machine running the client/HiveServer2 and <strong>copies</strong> it into the table directory in HDFS.',
        'Now the file is already in HDFS, in a landing folder.',
        '<code>LOAD DATA INPATH</code> (without LOCAL) treats the path as an HDFS path. A move inside HDFS is only a rename in the NameNode, so it is instant even for huge files…',
        '…but the source file <strong>no longer exists</strong> in the landing folder. That surprises many people.',
        'Either way Hive does <strong>not</strong> parse or check the data. It only places files. Bad rows show up later as NULLs at query time (schema-on-read).',
    ])


# ------------------------------------------------------------------ tables
def managed_external():
    elems = [
        stext(190, 26, 'Managed (internal) table', 'blue', 15, bold=True),
        stext(570, 26, 'External table', 'green', 15, bold=True),
        '<line x1="380" y1="15" x2="380" y2="290" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(60, 50, 260, 50, 'Metastore entry', 'students_m', 'purple', step=1, focus='1,3'),
        sbox(60, 140, 260, 70, 'Data files', '/user/hive/warehouse/\ncdac.db/students_m/', 'blue', step=1, focus='1,3'),
        sbox(440, 50, 260, 50, 'Metastore entry', 'students_x', 'purple', step=2, focus='2,4'),
        sbox(440, 140, 260, 70, 'Data files', '/data/raw/students/\n(you chose the location)', 'green', step=2, focus=2),
        stext(380, 245, 'DROP TABLE …', 'red', 14, step=3, bold=True),
        '<g data-step="3"><line x1="65" y1="55" x2="315" y2="95" stroke="#ef4444" stroke-width="4"/><line x1="315" y1="55" x2="65" y2="95" stroke="#ef4444" stroke-width="4"/>'
        '<line x1="65" y1="145" x2="315" y2="205" stroke="#ef4444" stroke-width="4"/><line x1="315" y1="145" x2="65" y2="205" stroke="#ef4444" stroke-width="4"/></g>',
        stext(190, 272, 'metadata AND data deleted', 'red', 12, step=3, focus=3, bold=True),
        '<g data-step="4"><line x1="445" y1="55" x2="695" y2="95" stroke="#ef4444" stroke-width="4"/><line x1="695" y1="55" x2="445" y2="95" stroke="#ef4444" stroke-width="4"/></g>',
        stext(570, 272, 'only metadata deleted, files remain ✔', 'green', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 290, *elems), [
        'A <strong>managed table</strong> is owned by Hive: its metadata is in the metastore and, by default, its files live under the warehouse directory.',
        'An <strong>external table</strong> also has a metastore entry, but it only <strong>points to</strong> files at a <code>LOCATION</code> you choose. Hive does not own them.',
        'Dropping a managed table deletes <strong>both</strong> the metadata and the data files (to trash, if enabled).',
        'Dropping an external table deletes only the metadata. The files stay, so other tools (Spark jobs, other tables) can keep using them and you can recreate the table any time.',
    ])


def schema_on_read():
    lines = ['2401,Anuj,78', '2402,Vineeta,91', '2403,Aarshvi,abc', '2404,Rohit']
    elems = [stext(380, 24, 'Schema-on-read: the schema is applied when you SELECT', 'blue', 15, bold=True),
             sbox(20, 45, 230, 170, '', '', 'gray', fill_opacity=0.06, step=1),
             stext(135, 65, 'students.csv in HDFS', 'gray', 12, step=1, bold=True)]
    for i, ln in enumerate(lines):
        elems.append(stext(40, 95 + i * 28, ln, '#e2e8f0', 13, 'start', step=1))
    elems += [
        sbox(285, 60, 170, 70, 'Table definition', 'roll INT, name STRING\nmarks INT · delimiter ,', 'purple', step=2, focus=2, size=12),
        sflow(250, 130, 480, 130, 'amber', step=3, count=3),
        stext(370, 160, 'split on "," → cast to types', 'amber', 11, step=3),
        stable(480, 60, ['roll', 'name', 'marks'], [['2401', 'Anuj', '78'], ['2402', 'Vineeta', '91'], ['2403', 'Aarshvi', 'NULL'], ['2404', 'Rohit', 'NULL']],
               [70, 90, 70], step=3, title='SELECT * FROM students', title_color='green', focus_rows={2: '4', 3: '4'}),
        stext(380, 250, '"abc" is not an INT → NULL · missing field → NULL · no error is raised', 'red', 12, step=4, focus=4),
        stext(380, 272, 'Change the table definition → the same files are read differently', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 290, *elems), [
        'The file in HDFS is just text. Nothing checked it when it was loaded: row 3 has text in the marks column and row 4 has a missing field.',
        'The table definition in the metastore says how to interpret the bytes: column names, types, and the field delimiter (via the SerDe).',
        'Only when a query <strong>reads</strong> the data does Hive split each line and convert the fields to the declared types.',
        'Values that cannot be converted, and missing fields, become <strong>NULL</strong>. Hive does not reject the row or fail the query, so bad data can go unnoticed.',
        'Because the schema is not baked into the data, you can drop and recreate the table with a different schema and read the same files again. That is the flexibility of schema-on-read.',
    ])


def serde_anim():
    elems = [
        stext(380, 24, 'SerDe = Serializer / Deserializer', 'blue', 15, bold=True),
        sbox(20, 70, 170, 60, 'HDFS file', 'bytes on disk', 'gray', step=1),
        sbox(240, 60, 150, 80, 'InputFormat', 'splits file into\nrecords (lines)', 'amber', step=1, focus=1, size=12),
        sbox(440, 60, 150, 80, 'Deserializer', 'record → columns', 'purple', step=2, focus=2, size=12),
        sbox(630, 70, 110, 60, 'Row', 'for the query', 'green', step=2),
        sflow(190, 100, 240, 100, 'amber', step=1, count=2), sflow(390, 100, 440, 100, 'purple', step=2, count=2), sflow(590, 100, 630, 100, 'green', step=2, count=2),
        stext(380, 172, 'READ path', 'cyan', 12, step=2, bold=True),
        sbox(630, 200, 110, 60, 'Row', 'from INSERT', 'green', step=3),
        sbox(440, 190, 150, 80, 'Serializer', 'columns → bytes', 'purple', step=3, focus=3, size=12),
        sbox(240, 190, 150, 80, 'OutputFormat', 'writes records\nto files', 'amber', step=3, focus=3, size=12),
        sbox(20, 200, 170, 60, 'HDFS file', '', 'gray', step=3),
        sflow(630, 230, 590, 230, 'green', step=3, count=2), sflow(440, 230, 390, 230, 'purple', step=3, count=2), sflow(240, 230, 190, 230, 'amber', step=3, count=2),
        stext(380, 300, 'LazySimpleSerDe (text) · OpenCSVSerde · JsonSerDe · RegexSerDe · OrcSerde · ParquetHiveSerDe', 'pink', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 315, *elems), [
        'When Hive reads a table, the <strong>InputFormat</strong> reads the file and cuts it into records, e.g. one line per record for text files.',
        'The <strong>Deserializer</strong> turns each record into columns: it splits on the delimiter (or parses JSON, CSV with quotes, a regex…) and converts values to the column types.',
        'When Hive writes (INSERT), the <strong>Serializer</strong> turns each row back into bytes in the table\'s format, and the <strong>OutputFormat</strong> writes them to files.',
        'You choose the SerDe in <code>ROW FORMAT SERDE …</code> or implicitly with <code>STORED AS ORC/PARQUET</code>. This is how one SQL engine can read many file formats.',
    ])


# ------------------------------------------------------------------ partitioning
def partition_pruning():
    days = ['dt=2026-10-11', 'dt=2026-10-12', 'dt=2026-10-13', 'dt=2026-10-14']
    elems = [stext(380, 24, "SELECT … FROM attendance WHERE dt = '2026-10-13'", 'blue', 14, bold=True),
             sbox(20, 50, 170, 60, 'attendance/', 'table directory', 'gray', step=1)]
    for i, d in enumerate(days):
        y = 50 + i * 62
        hit = d.endswith('13')
        elems.append(sbox(260, y, 200, 48, d, '3 files · 2 GB', 'green' if hit else 'gray', step=1, focus='3' if hit else None, size=12))
        elems.append(sarrow(190, 80, 258, y + 24, 'gray', step=1))
        if not hit:
            elems.append(f'<g data-step="3"><line x1="265" y1="{y + 5}" x2="455" y2="{y + 43}" stroke="#ef4444" stroke-width="3"/></g>')
    elems += [
        sbox(560, 100, 180, 60, 'Metastore', 'partition list', 'purple', step=2, focus=2),
        stext(650, 185, 'filter on partition column', 'purple', 11, step=2),
        stext(650, 200, 'is applied to the LIST of folders', 'purple', 11, step=2),
        sflow(460, 204, 560, 250, 'green', step=4, count=3),
        sbox(560, 230, 180, 50, 'Tez reads 2 GB', 'instead of 8 GB', 'green', step=4, focus=4, size=12),
    ]
    return anim(canvas(760, 305, *elems), [
        'A table <strong>partitioned by dt</strong> stores each day in its own sub-directory: <code>dt=2026-10-11/</code>, <code>dt=2026-10-12/</code> … The partition column is not stored inside the files; it is the folder name.',
        'When the query has a filter on the partition column, Hive asks the <strong>metastore</strong> which partitions match, before any data is read.',
        'All non-matching folders are <strong>pruned</strong>: they are never opened. This is <strong>partition pruning</strong>.',
        'Only the <code>dt=2026-10-13</code> folder is read: 2 GB instead of 8 GB. With years of daily data the saving is often 99% or more.',
    ])


def static_dynamic():
    elems = [
        stext(190, 26, 'Static partitioning', 'blue', 14, bold=True),
        stext(570, 26, 'Dynamic partitioning', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(30, 50, 320, 44, "PARTITION (course='DBDA')", 'value written in the statement', 'blue', step=1, focus=1, size=12),
        sbox(30, 130, 320, 70, 'all selected rows', '→ course=DBDA/', 'blue', step=1, size=12),
        sarrow(190, 94, 190, 128, 'blue', step=1),
        stext(190, 230, 'one partition per INSERT', 'blue', 12, step=2),
        stext(190, 248, 'you must know the value', 'blue', 12, step=2),
        stext(190, 266, 'fast: no shuffle', 'blue', 12, step=2),
        sbox(410, 50, 320, 44, 'PARTITION (course)', 'value taken from the LAST select column', 'green', step=3, focus=3, size=12),
        stable(430, 110, ['name', 'course'], [['Anuj', 'DBDA'], ['Vineeta', 'DAC'], ['Aarshvi', 'DBDA'], ['Rohit', 'DAI']], [120, 110], step=3, title_color='green'),
        sbox(410, 245, 100, 40, 'DBDA/', '', 'green', step=4, focus=4, size=12),
        sbox(520, 245, 100, 40, 'DAC/', '', 'green', step=4, focus=4, size=12),
        sbox(630, 245, 100, 40, 'DAI/', '', 'green', step=4, focus=4, size=12),
        sflow(540, 240, 460, 245, 'green', step=4, count=2), sflow(540, 240, 570, 245, 'green', step=4, count=2), sflow(540, 240, 680, 245, 'green', step=4, count=2),
    ]
    return anim(canvas(760, 300, *elems), [
        '<strong>Static</strong>: you write the partition value in the statement, e.g. <code>PARTITION (course=\'DBDA\')</code>. Every row the SELECT returns goes into that one folder.',
        'It is simple and fast, but you need one INSERT per partition and must know the values in advance. Typical for daily loads: <code>PARTITION (dt=\'${run_date}\')</code>.',
        '<strong>Dynamic</strong>: you name only the partition column. Hive takes its value from the <strong>last column(s)</strong> of the SELECT, row by row.',
        'Hive creates as many partitions as there are distinct values: DBDA, DAC and DAI here, in one statement. Limits such as <code>hive.exec.max.dynamic.partitions</code> protect against creating thousands by mistake.',
    ])


def msck_anim():
    elems = [
        stext(380, 24, 'Files added outside Hive are invisible until registered', 'blue', 15, bold=True),
        sbox(20, 60, 210, 140, '', '', 'purple', step=1, fill_opacity=0.08),
        stext(125, 80, 'Metastore partitions', 'purple', 12, step=1, bold=True),
        sbox(40, 95, 170, 30, 'dt=2026-10-11', '', 'purple', step=1, size=11),
        sbox(40, 132, 170, 30, 'dt=2026-10-12', '', 'purple', step=1, size=11),
        sbox(40, 165, 170, 30, 'dt=2026-10-13', '', 'green', step=4, focus=4, size=11),
        sbox(520, 60, 220, 140, '', '', 'gray', step=1, fill_opacity=0.08),
        stext(630, 80, 'HDFS: /data/logs/', 'gray', 12, step=1, bold=True),
        sbox(545, 95, 170, 30, 'dt=2026-10-11/', '', 'gray', step=1, size=11),
        sbox(545, 132, 170, 30, 'dt=2026-10-12/', '', 'gray', step=1, size=11),
        sbox(545, 165, 170, 30, 'dt=2026-10-13/', 'new', 'amber', step=2, focus=2, size=11),
        stext(630, 225, 'Spark / Flume / hdfs dfs -put', 'amber', 11, step=2),
        stext(380, 125, 'SELECT … WHERE dt=\'2026-10-13\'', 'red', 12, step=3),
        stext(380, 143, '→ 0 rows (Hive doesn\'t know it)', 'red', 12, step=3, focus=3, bold=True),
        sarrow(520, 180, 212, 180, 'green', step=4),
        stext(380, 260, 'MSCK REPAIR TABLE logs;  or  ALTER TABLE logs ADD PARTITION (dt=\'2026-10-13\');', 'green', 12, step=4, focus=4, bold=True),
        stext(380, 285, 'now the new day is queryable', 'green', 12, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'Hive knows about a partition only if it is registered in the <strong>metastore</strong>. Here the metastore and HDFS agree on two days.',
        'Another tool (a Spark job, Flume, or someone with <code>hdfs dfs -put</code>) writes a new folder <code>dt=2026-10-13/</code> directly into the table\'s location.',
        'A query for that day returns <strong>no rows</strong>. The files exist, but the partition is not in the metastore, so Hive never looks there.',
        '<code>MSCK REPAIR TABLE</code> scans the table location and adds missing partitions (in Hive 3 it can also <code>SYNC</code>/<code>DROP</code> removed ones). For a known folder, <code>ALTER TABLE … ADD PARTITION</code> is faster.',
    ])


# ------------------------------------------------------------------ bucketing
def bucketing_anim():
    rows = [('2401', 1), ('2402', 2), ('2403', 3), ('2404', 0), ('2405', 1), ('2406', 2)]
    elems = [stext(380, 24, 'CLUSTERED BY (roll_no) INTO 4 BUCKETS', 'blue', 15, bold=True),
             stext(380, 46, 'bucket = hash(roll_no) mod 4   (for an INT, hash = the value itself)', 'cyan', 12, step=1, focus=1)]
    for i, (r, b) in enumerate(rows):
        y = 70 + i * 36
        elems.append(sbox(30, y, 110, 28, f'roll {r}', '', 'gray', step=2, size=11))
        elems.append(stext(205, y + 19, f'{r} mod 4 = {b}', 'amber', 11, step=2))
    cols = ['blue', 'green', 'purple', 'pink']
    for b in range(4):
        members = ', '.join(r for r, bb in rows if bb == b)
        elems.append(sbox(470, 65 + b * 56, 270, 46, f'bucket file {b:06d}_0', members, cols[b], step=3, focus=3, size=12))
    for i, (r, b) in enumerate(rows):
        elems.append(sflow(270, 84 + i * 36, 470, 88 + b * 56, cols[b], step=3, count=1))
    elems.append(stext(380, 300, 'fixed number of files · same key → same bucket → bucket joins & sampling', 'green', 12, step=4, focus=4, bold=True))
    return anim(canvas(760, 315, *elems), [
        'Bucketing splits a table (or each partition) into a <strong>fixed number of files</strong> chosen at CREATE time, based on a hash of a column.',
        'For each row Hive computes <code>hash(roll_no) mod 4</code>. For integer columns the hash is the number itself, so roll 2403 goes to bucket 3.',
        'Each bucket is one file. All rows with the same key always land in the same bucket file, and the number of files never grows with the data.',
        'Because both tables bucketed the same way have matching keys in matching files, Hive can join bucket-to-bucket without a full shuffle, and sample data by reading just one bucket.',
    ])


def bucket_join():
    elems = [
        stext(380, 24, 'Bucket map join / Sort-Merge-Bucket (SMB) join', 'blue', 15, bold=True),
        stext(150, 52, 'students (4 buckets on roll)', 'blue', 12, bold=True),
        stext(610, 52, 'marks (4 buckets on roll)', 'green', 12, bold=True),
    ]
    for b in range(4):
        y = 65 + b * 52
        elems.append(sbox(50, y, 200, 40, f'students bucket {b}', '', 'blue', step=1, focus='2' if b == 0 else None, size=12))
        elems.append(sbox(510, y, 200, 40, f'marks bucket {b}', '', 'green', step=1, focus='2' if b == 0 else None, size=12))
        elems.append(sbox(305, y + 4, 150, 32, f'task {b}: join', '', 'amber', step=3, focus=3, size=11))
        elems.append(sflow(250, y + 20, 305, y + 20, 'blue', step=3, count=2))
        elems.append(sflow(510, y + 20, 455, y + 20, 'green', step=3, count=2))
    elems += [
        stext(380, 290, 'same column, same bucket count (or multiples) → no full shuffle', 'cyan', 12, step=4, focus=4, bold=True),
        stext(380, 308, 'sorted buckets (SORTED BY) → merge join, little memory (SMB)', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 320, *elems), [
        'Both tables are bucketed on the join key <code>roll</code> into the same number of buckets.',
        'A row with a given roll number is in bucket <em>k</em> of <strong>both</strong> tables. Matching rows can only ever be in matching buckets.',
        'So Hive starts one task per bucket pair: task 0 joins students bucket 0 with marks bucket 0, and so on. No task needs data from other buckets, so the big shuffle of a normal join disappears.',
        'If the buckets are also <strong>sorted</strong> on the key (<code>SORTED BY</code>), each task does a streaming merge of two sorted files: the <strong>SMB join</strong>, which works even when neither table fits in memory.',
    ])


# ------------------------------------------------------------------ querying
def sort_by_anim():
    elems = [stext(380, 22, 'ORDER BY vs SORT BY vs DISTRIBUTE BY vs CLUSTER BY', 'blue', 15, bold=True)]
    panels = [
        ('ORDER BY marks', 1, 'blue', [['35 47 58 62 71 78 84 91']], 'one reducer · total order · slow on big data'),
        ('SORT BY marks', 2, 'amber', [['47 62 78 91'], ['35 58 71 84']], 'sorted within each reducer only'),
        ('DISTRIBUTE BY course', 3, 'purple', [['DBDA DBDA DBDA'], ['DAC DAC DAI DAI DAI']], 'same key → same reducer, unsorted'),
        ('CLUSTER BY course', 4, 'green', [['DBDA DBDA DBDA'], ['DAC DAC DAI DAI DAI']], '= DISTRIBUTE BY + SORT BY same column'),
    ]
    for i, (name, step, col, reducers, note_) in enumerate(panels):
        y = 45 + i * 68
        elems.append(sbox(20, y, 190, 52, name, '', col, step=step, focus=step, size=12))
        for j, r in enumerate(reducers):
            elems.append(sbox(230 + j * 245, y + 2, 235, 28, f'reducer {j}: {r[0]}', '', col, step=step, size=11))
        elems.append(stext(475, y + 48, note_, col, 11, step=step))
    return anim(canvas(760, 325, *elems), [
        '<code>ORDER BY</code> guarantees a <strong>total order</strong> of the whole result, so all rows must pass through a <strong>single reducer</strong>. On large data that one task becomes the bottleneck (strict mode requires a LIMIT).',
        '<code>SORT BY</code> sorts the data <strong>within each reducer</strong>. With 2 reducers you get 2 individually sorted outputs, but not a global order. Faster, because sorting is parallel.',
        '<code>DISTRIBUTE BY</code> controls <strong>which reducer</strong> each row goes to: all rows with the same course go to the same reducer. It does not sort.',
        '<code>CLUSTER BY col</code> is shorthand for <code>DISTRIBUTE BY col SORT BY col</code>: rows are grouped by key per reducer and sorted within it.',
    ])


def map_join_anim():
    elems = [
        stext(380, 24, 'Map join: broadcast the small table, skip the shuffle', 'blue', 15, bold=True),
        sbox(20, 55, 180, 50, 'courses (small)', '3 rows, a few KB', 'green', step=1, focus=1),
        sbox(20, 200, 180, 50, 'enrolments (big)', '200 million rows', 'blue', step=1),
        sbox(250, 55, 160, 50, 'local task', 'builds hash table', 'amber', step=2, focus=2, size=12),
        sflow(200, 80, 250, 80, 'green', step=2, count=2),
        sbox(460, 50, 100, 60, 'distributed', 'cache', 'amber', step=2, size=12),
        sarrow(410, 80, 458, 80, 'amber', step=2),
    ]
    for i in range(3):
        x = 260 + i * 165
        elems.append(sbox(x, 175, 150, 70, f'map task {i + 1}', 'hash table in RAM\n+ slice of big table', 'purple', step=3, focus=3, size=11))
        elems.append(sflow(510, 110, x + 75, 175, 'amber', step=3, count=2))
    elems += [
        sflow(200, 225, 260, 210, 'blue', step=3, count=3),
        stext(475, 280, 'no shuffle · no reduce phase · joined output written directly', 'green', 12, step=4, focus=4, bold=True),
        stext(475, 298, 'auto-chosen when small side < hive.auto.convert.join.noconditionaltask.size', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 310, *elems), [
        'A big fact table (enrolments) is joined with a tiny lookup table (courses).',
        'A <strong>local task</strong> reads the small table and builds an in-memory <strong>hash table</strong> from it, which is shipped to every node (distributed cache / broadcast).',
        'Each map task loads the hash table and streams its slice of the big table through it, looking up the matching course for every row.',
        'No data is shuffled and there is no reduce phase, which is usually many times faster. Hive converts joins to map joins automatically when the small table is below the size threshold.',
    ])


def explode_anim():
    elems = [
        stext(380, 24, 'LATERAL VIEW explode(): one row per array element', 'blue', 15, bold=True),
        stable(20, 60, ['name', 'skills'], [['Anuj', '[sql, spark]'], ['Vineeta', '[python, hive, kafka]']], [90, 170], step=1, title='students', title_color='blue'),
        sbox(320, 60, 150, 56, 'explode(skills)', 'UDTF: 1 row → n rows', 'amber', step=2, focus=2, size=12),
        stable(320, 150, ['skill'], [['sql'], ['spark'], ['python'], ['hive'], ['kafka']], [150], step=2, title='virtual table', title_color='amber'),
        sflow(280, 95, 320, 90, 'amber', step=2, count=2),
        stable(530, 60, ['name', 'skill'], [['Anuj', 'sql'], ['Anuj', 'spark'], ['Vineeta', 'python'], ['Vineeta', 'hive'], ['Vineeta', 'kafka']], [100, 100],
               step=3, title='result', title_color='green', focus_rows={0: '3', 1: '3'}),
        sflow(470, 200, 530, 150, 'green', step=3, count=2),
        stext(380, 330, 'OUTER keeps rows whose array is empty or NULL', 'pink', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 345, *elems), [
        'Each student row has an <code>ARRAY&lt;STRING&gt;</code> of skills. Reports usually need one row per skill.',
        '<code>explode()</code> is a <strong>table-generating function (UDTF)</strong>: it turns one array into several rows. Used alone it can only return the exploded column.',
        '<code>LATERAL VIEW</code> joins each input row with the rows its own array produced, so other columns (name) are repeated next to each skill.',
        'Students with an empty or NULL array disappear from the result. <code>LATERAL VIEW OUTER explode(...)</code> keeps them with a NULL skill.',
    ])


def window_anim():
    rows = [['DBDA', 'Vineeta', '91', '1'], ['DBDA', 'Anuj', '78', '2'], ['DBDA', 'Meera', '78', '2'],
            ['DAC', 'Rohit', '88', '1'], ['DAC', 'Aarshvi', '84', '2']]
    elems = [
        stext(380, 24, 'RANK() OVER (PARTITION BY course ORDER BY marks DESC)', 'blue', 14, bold=True),
        stable(80, 60, ['course', 'name', 'marks', 'rank'], [r[:3] + [''] for r in rows], [110, 120, 90, 80], step=1, title_color='blue'),
        '<g data-step="2"><rect x="76" y="83" width="408" height="82" fill="none" stroke="#fbbf24" stroke-width="2" stroke-dasharray="6,4" rx="4"/>'
        '<rect x="76" y="163" width="408" height="56" fill="none" stroke="#a78bfa" stroke-width="2" stroke-dasharray="6,4" rx="4"/></g>',
        stext(600, 120, 'window 1: DBDA', 'amber', 12, step=2),
        stext(600, 195, 'window 2: DAC', 'purple', 12, step=2),
    ]
    for i, r in enumerate(rows):
        elems.append(scell(400, 86 + i * 26, 80, 26, r[3], '#162033', '#fde68a', step=3, focus=3, bold=True))
    elems += [
        stext(600, 140, 'ties share rank 2', 'green', 12, step=4, focus=4),
        stext(380, 260, 'unlike GROUP BY, every input row is kept, with a value computed over its window', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'Start with one row per student: course, name, marks.',
        '<code>PARTITION BY course</code> splits the rows into independent <strong>windows</strong>, one per course (this has nothing to do with table partitions).',
        'Inside each window, <code>ORDER BY marks DESC</code> sorts the rows and <code>RANK()</code> numbers them: 1 for the topper of each course.',
        'Anuj and Meera both have 78, so both get rank 2 (the next would be 4). <code>DENSE_RANK()</code> would give 3 next; <code>ROW_NUMBER()</code> gives unique numbers.',
        'Window functions keep <strong>every row</strong> and add a computed column, whereas GROUP BY collapses rows. That is why they are used for top-N per group, running totals and deduplication.',
    ])


# ------------------------------------------------------------------ performance
def engines_anim():
    elems = [
        stext(190, 24, 'MapReduce: chain of jobs', 'red', 14, bold=True),
        stext(570, 24, 'Tez: one DAG', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(40, 45, 120, 38, 'Job 1: M → R', '', 'red', step=1, size=12),
        sbox(200, 45, 140, 38, 'HDFS (3× write)', '', 'gray', step=1, size=11),
        sbox(40, 125, 120, 38, 'Job 2: M → R', '', 'red', step=1, size=12),
        sbox(200, 125, 140, 38, 'HDFS (3× write)', '', 'gray', step=1, size=11),
        sbox(40, 205, 120, 38, 'Job 3: M → R', '', 'red', step=1, size=12),
        sarrow(160, 64, 198, 64, 'red', step=1), sarrow(270, 83, 110, 123, 'red', step=1),
        sarrow(160, 144, 198, 144, 'red', step=1), sarrow(270, 163, 110, 203, 'red', step=1),
        stext(190, 275, 'each job: new containers + full HDFS write/read', 'red', 12, step=2, focus=2),
        sbox(430, 50, 110, 38, 'Map 1', '', 'green', step=3, size=12), sbox(600, 50, 110, 38, 'Map 2', '', 'green', step=3, size=12),
        sbox(515, 130, 110, 38, 'Reducer 1', '', 'green', step=3, focus=3, size=12),
        sbox(515, 210, 110, 38, 'Reducer 2', '', 'green', step=3, size=12),
        sflow(485, 88, 560, 130, 'green', step=3, count=2), sflow(655, 88, 580, 130, 'green', step=3, count=2), sflow(570, 168, 570, 210, 'green', step=3, count=2),
        stext(570, 275, 'data flows between vertices directly · containers reused', 'green', 12, step=4, focus=4),
        stext(570, 293, 'hive.execution.engine=tez (default in Hive 2+/3)', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 305, *elems), [
        'With <strong>MapReduce</strong>, a query with a join, a GROUP BY and an ORDER BY becomes a <strong>chain of separate jobs</strong>. Each one writes its full output to HDFS for the next to read.',
        'Every job also starts fresh containers and JVMs, and HDFS writes are replicated 3×. Most of the time is overhead, not computation.',
        '<strong>Tez</strong> compiles the same query into <strong>one DAG</strong> of vertices (map and reduce steps) with edges between them, submitted as a single application.',
        'Intermediate data flows directly between vertices (no HDFS round trips), containers are reused, and the session stays warm, so the same query is typically several times faster. MapReduce as Hive\'s engine is deprecated.',
    ])


def acid_anim():
    elems = [
        stext(380, 24, 'Hive ACID: base + delta files, merged by compaction', 'blue', 15, bold=True),
        sbox(20, 55, 180, 50, 'base_0000001/', '1,000,000 rows', 'blue', step=1, focus=1, size=12),
        sbox(230, 55, 160, 50, 'delta_0000002', 'INSERT 500 rows', 'green', step=2, focus=2, size=12),
        sbox(410, 55, 160, 50, 'delete_delta_3', 'DELETE 20 rows', 'red', step=3, focus=3, size=12),
        sbox(590, 55, 150, 50, 'delete_delta_4 +', 'delta_4 (UPDATE)', 'amber', step=3, focus=3, size=11),
        sbox(230, 150, 340, 46, 'Reader merges base + deltas on the fly', 'snapshot by transaction id', 'purple', step=4, focus=4, size=12),
        sflow(110, 105, 300, 150, 'purple', step=4, count=2), sflow(400, 105, 400, 150, 'purple', step=4, count=2), sflow(665, 105, 500, 150, 'purple', step=4, count=2),
        sbox(60, 230, 270, 50, 'Minor compaction', 'many deltas → one delta', 'amber', step=5, size=12),
        sbox(430, 230, 270, 50, 'Major compaction', 'base + deltas → new base', 'green', step=5, focus=5, size=12),
        stext(380, 300, 'UPDATE = delete old version + insert new version', 'cyan', 12, step=3),
    ]
    return anim(canvas(760, 310, *elems), [
        'A transactional (ACID) table stores its data as ORC files. The initial data is in a <strong>base</strong> directory.',
        'Files in HDFS cannot be edited, so each INSERT writes a new <strong>delta</strong> directory tagged with the transaction id.',
        'A DELETE writes a <strong>delete_delta</strong> that lists the ids of removed rows. An UPDATE is a delete of the old version plus a delta with the new version.',
        'Readers merge base and deltas on the fly, seeing only committed transactions (snapshot isolation). Many small deltas make reads slower.',
        'Background <strong>compaction</strong> fixes that: minor compaction merges deltas together; major compaction rewrites base + all deltas into a new base, after which old files are cleaned up.',
    ])


def skew_anim():
    elems = [
        stext(380, 24, 'Skewed join key: one reducer gets most of the data', 'blue', 15, bold=True),
        stext(190, 50, 'without skew handling', 'red', 13, bold=True),
        stext(570, 50, 'skew join / salting', 'green', 13, bold=True),
        '<line x1="380" y1="40" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
    ]
    loads = [0.9, 0.1, 0.12, 0.08]
    for i, l in enumerate(loads):
        y = 70 + i * 48
        elems.append(stext(30, y + 22, f'R{i}', 'gray', 12, 'start', step=1))
        elems.append(f'<rect x="60" y="{y + 6}" width="{l * 290:.0f}" height="26" rx="4" fill="{"#ef4444" if l > 0.5 else "#64748b"}" data-step="1"{" data-focus=\"1\"" if l > 0.5 else ""}/>')
    elems.append(stext(205, 280, 'city = "Mumbai" → 90% of rows on R0', 'red', 12, step=2, focus=2))
    for i in range(4):
        y = 70 + i * 48
        elems.append(stext(410, y + 22, f'R{i}', 'gray', 12, 'start', step=3))
        elems.append(f'<rect x="440" y="{y + 6}" width="{0.3 * 290:.0f}" height="26" rx="4" fill="#10b981" data-step="3"/>')
    elems.append(stext(570, 280, 'hot key split into Mumbai#0..#3', 'green', 12, step=3, focus=3))
    elems.append(stext(570, 298, 'or handled by a separate map join', 'green', 12, step=4, focus=4))
    return anim(canvas(760, 310, *elems), [
        'In a join or GROUP BY, all rows with the same key go to one reducer. Most keys are small, but one key (Mumbai) has 90% of the rows.',
        'Reducer R0 runs for hours while the others finish in minutes: the query is stuck at "99% complete". That is <strong>data skew</strong>.',
        '<strong>Salting</strong> adds a random suffix to the hot key so its rows are spread over several reducers; a second aggregation step combines the partial results.',
        'Hive can also do it for you: <code>hive.optimize.skewjoin=true</code> processes keys above <code>hive.skewjoin.key</code> rows in a separate map-join stage, and <code>hive.groupby.skewindata=true</code> does a two-stage GROUP BY.',
    ])


def small_files_anim():
    elems = [
        stext(380, 24, 'Too many small files in a Hive table', 'blue', 15, bold=True),
        sbox(20, 50, 200, 46, 'Streaming / hourly INSERTs', '', 'gray', step=1, size=12),
    ]
    for r in range(4):
        for c in range(10):
            elems.append(scell(260 + c * 24, 50 + r * 20, 21, 17, '', '#ef4444', step=1))
    elems += [
        stext(380, 145, '2,000 files of 200 KB per partition', 'red', 12, step=1),
        stext(380, 170, '→ 2,000 tasks, NameNode pressure, slow listing', 'red', 12, step=2, focus=2, bold=True),
        sbox(560, 50, 180, 80, 'Fix', 'merge on write ·\nCONCATENATE ·\ncompaction job', 'green', step=3, focus=3, size=12),
        sbox(260, 205, 110, 44, '256 MB', '', 'green', step=4), sbox(380, 205, 110, 44, '256 MB', '', 'green', step=4),
        sflow(380, 130, 380, 205, 'green', step=4, count=3),
        stext(380, 280, 'hive.merge.tezfiles=true · ALTER TABLE t PARTITION(...) CONCATENATE (ORC) · INSERT OVERWRITE', 'cyan', 11, step=4, focus=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'Frequent small inserts (every few minutes, or a query with many reducers) leave thousands of tiny files in each partition.',
        'Every file costs NameNode memory and usually becomes its own task, so queries spend more time opening files and starting tasks than reading data.',
        'Hive offers fixes at write time (merge small output files) and after the fact (concatenate or compact).',
        'Settings such as <code>hive.merge.tezfiles</code> add a merge step after the query; <code>ALTER TABLE … CONCATENATE</code> merges ORC files; an <code>INSERT OVERWRITE</code> of the partition rewrites it into a few large files.',
    ])


def scd2_anim():
    elems = [
        stext(380, 24, 'SCD Type 2: keep history by versioning rows', 'blue', 15, bold=True),
        stable(20, 60, ['id', 'city', 'start', 'end', 'current'], [['2402', 'Pune', '2025-07-01', '9999-12-31', 'Y']], [55, 90, 100, 100, 70],
               step=1, title='dim_student (before)', title_color='blue'),
        stable(20, 160, ['id', 'city'], [['2402', 'Mumbai']], [55, 90], step=2, title='today\'s source', title_color='amber'),
        stable(330, 160, ['id', 'city', 'start', 'end', 'current'], [['2402', 'Pune', '2025-07-01', '2026-10-12', 'N'], ['2402', 'Mumbai', '2026-10-13', '9999-12-31', 'Y']],
               [55, 90, 100, 100, 70], step=3, title='dim_student (after)', title_color='green', focus_rows={0: '3', 1: '4'}),
        stext(560, 80, 'changed city detected', 'amber', 12, step=2, focus=2),
        stext(560, 100, 'by comparing source vs current row', 'amber', 11, step=2),
        stext(380, 290, 'facts join on (id, date BETWEEN start AND end) to get the city at that time', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 305, *elems), [
        'The dimension has one <strong>current</strong> row for student 2402: city Pune, valid from July 2025 with an open end date.',
        'Today\'s source says the student now lives in Mumbai. Comparing source with the current row detects the change.',
        'The old row is <strong>closed</strong>: its end date becomes yesterday and current = N. The history is not overwritten.',
        'A <strong>new row</strong> is added with Mumbai, starting today, current = Y. In Hive this is done with MERGE on ACID tables, or by rebuilding the table/partition with INSERT OVERWRITE.',
        'Reports can now show the city a student had at the time of any event, by joining on the id and the validity dates.',
    ])


# ------------------------------------------------------------------ additional animations
def write_vs_read():
    elems = [
        stext(190, 26, 'RDBMS: schema-on-write', 'blue', 14, bold=True),
        stext(570, 26, 'Hive: schema-on-read', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(40, 50, 300, 40, "INSERT (2403, 'Aarshvi', 'abc')", '', 'gray', step=1, size=12),
        sbox(110, 120, 160, 50, 'Validate types', 'and constraints', 'amber', step=1, focus=1, size=12),
        sarrow(190, 90, 190, 118, 'amber', step=1),
        sbox(90, 205, 200, 44, 'ERROR: rejected ✘', '', 'red', step=2, focus=2, size=12),
        sarrow(190, 170, 190, 203, 'red', step=2),
        stext(190, 280, 'slow write, guaranteed clean data', 'blue', 12, step=2),
        sbox(420, 50, 300, 40, 'hdfs dfs -put marks.csv', '', 'gray', step=3, size=12),
        sbox(490, 120, 160, 50, 'File stored as-is', 'no checks', 'green', step=3, focus=3, size=12),
        sarrow(570, 90, 570, 118, 'green', step=3),
        sbox(470, 205, 200, 44, 'SELECT → marks = NULL', '', 'amber', step=4, focus=4, size=12),
        sarrow(570, 170, 570, 203, 'amber', step=4),
        stext(570, 280, 'fast write, quality checked by you', 'green', 12, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'In an RDBMS every INSERT goes through validation: types, NOT NULL, primary and foreign keys.',
        'A bad value (text in an INT column) is <strong>rejected at write time</strong>. Data in the table is always valid, but every write pays for the checks.',
        'In Hive, data arrives as files and is stored <strong>exactly as received</strong>. Nothing is validated, so loading terabytes is fast.',
        'Problems appear only when you <strong>read</strong>: the bad value becomes NULL. Data quality checks become the pipeline\'s responsibility.',
    ])


def db_tree():
    elems = [
        stext(380, 24, 'Databases and tables are just directories', 'blue', 15, bold=True),
        sbox(20, 60, 230, 40, '/user/hive/warehouse/', '', 'gray', step=1, size=12),
        sbox(60, 125, 190, 36, 'raw.db/', 'CREATE DATABASE raw', 'amber', step=2, focus=2, size=11),
        sbox(60, 205, 190, 36, 'dw.db/', 'CREATE DATABASE dw', 'amber', step=2, focus=2, size=11),
        sarrow(40, 100, 58, 143, 'gray', step=2), sarrow(40, 100, 58, 223, 'gray', step=2, mid=(40, 223)),
        sbox(320, 125, 200, 36, 'students/', 'CREATE TABLE raw.students', 'blue', step=3, focus=3, size=11),
        sbox(320, 205, 200, 36, 'attendance/', 'CREATE TABLE dw.attendance', 'blue', step=3, focus=3, size=11),
        sarrow(250, 143, 318, 143, 'gray', step=3), sarrow(250, 223, 318, 223, 'gray', step=3),
        sbox(570, 125, 170, 36, 'part-00000.orc', '', 'green', step=4, size=11),
        sbox(570, 195, 170, 30, 'dt=2026-10-12/', '', 'green', step=4, size=11),
        sbox(570, 232, 170, 30, 'dt=2026-10-13/', '', 'green', step=4, size=11),
        sarrow(520, 143, 568, 143, 'gray', step=4), sarrow(520, 223, 568, 212, 'gray', step=4), sarrow(520, 223, 568, 245, 'gray', step=4),
        stext(380, 295, 'DROP DATABASE raw → refused while it has tables · DROP DATABASE raw CASCADE → tables dropped too', 'red', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 310, *elems), [
        'Everything Hive manages lives under the <strong>warehouse directory</strong> (<code>hive.metastore.warehouse.dir</code>).',
        '<code>CREATE DATABASE raw</code> creates a folder <code>raw.db/</code> and a metastore entry. The <code>default</code> database uses the warehouse root.',
        '<code>CREATE TABLE raw.students</code> creates a sub-folder for the table inside its database folder (for managed tables).',
        'Data files go inside the table folder; partitioned tables get one sub-folder per partition value.',
        'Dropping a database that still contains tables fails; <code>CASCADE</code> drops the tables as well (and the data of managed tables).',
    ])


def complex_types_anim():
    elems = [
        stext(380, 24, 'Reading ARRAY, MAP and STRUCT values', 'blue', 15, bold=True),
        sbox(20, 55, 720, 46, "Vineeta | ['python','hive','kafka'] | {'SQL':91, 'Spark':88} | {city:'Navi Mumbai', pin:'410210'}", '', 'gray', step=1, size=12),
        stext(120, 125, 'ARRAY<STRING>', 'blue', 12, step=2, bold=True),
        scell(30, 135, 60, 28, 'python', '#0ea5e9', '#fff', step=2, focus=2, size=11), scell(92, 135, 60, 28, 'hive', '#334155', step=2, size=11), scell(154, 135, 60, 28, 'kafka', '#334155', step=2, size=11),
        stext(60, 185, '[0]', 'blue', 11, step=2), stext(122, 185, '[1]', 'gray', 11, step=2), stext(184, 185, '[2]', 'gray', 11, step=2),
        stext(120, 215, "skills[0] → 'python'", 'blue', 12, step=2, focus=2, bold=True),
        stext(380, 125, 'MAP<STRING,INT>', 'amber', 12, step=3, bold=True),
        stable(300, 135, ['key', 'value'], [['SQL', '91'], ['Spark', '88']], [80, 80], step=3, title_color='amber', focus_rows={1: '3'}),
        stext(380, 235, "marks['Spark'] → 88", 'amber', 12, step=3, focus=3, bold=True),
        stext(640, 125, 'STRUCT<city,pin>', 'green', 12, step=4, bold=True),
        sbox(560, 135, 160, 34, 'city: Navi Mumbai', '', 'green', step=4, focus=4, size=11),
        sbox(560, 175, 160, 34, 'pin: 410210', '', 'gray', step=4, size=11),
        stext(640, 235, 'address.city → Navi Mumbai', 'green', 12, step=4, focus=4, bold=True),
        stext(380, 285, 'size(skills) = 3 · map_keys(marks) = [SQL, Spark] · explode() turns an array into rows', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'One row can hold nested values: a list of skills, a map of subject to marks, and an address with fixed fields.',
        'An <strong>ARRAY</strong> is an ordered list; elements are read by position starting at 0: <code>skills[0]</code>.',
        'A <strong>MAP</strong> stores key → value pairs; read a value by its key: <code>marks[\'Spark\']</code>. A missing key returns NULL.',
        'A <strong>STRUCT</strong> groups named fields of different types; read one with a dot: <code>address.city</code>.',
        'Helper functions work on them: <code>size()</code>, <code>map_keys()</code>, <code>map_values()</code>, <code>array_contains()</code>, and <code>explode()</code> to turn elements into rows.',
    ])


def view_anim():
    elems = [
        stext(190, 26, 'View', 'blue', 14, bold=True),
        stext(570, 26, 'Materialized view', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(70, 50, 240, 40, 'SELECT * FROM v_summary', '', 'gray', step=1, size=12),
        sbox(70, 120, 240, 50, 'Hive substitutes the', 'view\'s stored SQL', 'blue', step=1, focus=1, size=12),
        sbox(70, 200, 240, 44, 'scans base table every time', '', 'amber', step=2, focus=2, size=12),
        sarrow(190, 90, 190, 118, 'blue', step=1), sarrow(190, 170, 190, 198, 'amber', step=2),
        stext(190, 275, 'no storage · always current', 'blue', 12, step=2),
        sbox(450, 50, 240, 40, 'CREATE MATERIALIZED VIEW mv', '', 'gray', step=3, size=12),
        sbox(450, 120, 240, 50, 'result stored as', 'an ORC table', 'green', step=3, focus=3, size=12),
        sarrow(570, 90, 570, 118, 'green', step=3),
        sbox(450, 200, 240, 44, 'matching query → read mv', '(automatic rewrite)', 'green', step=4, focus=4, size=12),
        sarrow(570, 170, 570, 198, 'green', step=4),
        stext(570, 275, 'fast · needs REBUILD after new data', 'green', 12, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'A <strong>view</strong> stores only its SELECT statement. Querying the view makes Hive substitute that SQL into your query.',
        'So every query on the view scans the base tables again: no extra storage, always up to date, but no faster than the original query.',
        'A <strong>materialized view</strong> runs its query once and stores the result as a real table.',
        'When a later query can be answered from it, the optimizer rewrites the query to read the small stored result. After base tables change, it must be rebuilt.',
    ])


def add_column_anim():
    elems = [
        stext(380, 24, 'ALTER TABLE students ADD COLUMNS (email STRING)', 'blue', 14, bold=True),
        sbox(20, 55, 200, 50, 'Metastore schema', 'roll_no, name', 'purple', step=1, size=12),
        sbox(20, 55, 200, 50, 'Metastore schema', 'roll_no, name, email', 'purple', step=2, focus=2, size=12),
        sbox(300, 55, 200, 50, 'old file (Sept)', '2401, Anuj', 'gray', step=1, size=12),
        sbox(540, 55, 200, 50, 'new file (Oct)', '2402, Vineeta, v@cdac.in', 'green', step=3, size=12),
        stext(400, 130, 'files are NOT rewritten', 'gray', 12, step=2),
        stable(170, 165, ['roll_no', 'name', 'email'], [['2401', 'Anuj', 'NULL'], ['2402', 'Vineeta', 'v@cdac.in']], [110, 120, 160],
               step=4, title='SELECT * FROM students', title_color='green', focus_rows={0: '4'}),
        stext(380, 290, 'old rows have no value for the new column → NULL', 'amber', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 305, *elems), [
        'The table has two columns, and its existing data file contains values for those two only.',
        '<code>ADD COLUMNS</code> changes only the <strong>schema in the metastore</strong>. The command finishes instantly; no file is touched.',
        'New data written after the change includes the email column.',
        'When reading, the SerDe maps columns by name (ORC/Parquet) or position (text). Old files simply have no email, so it is returned as NULL.',
    ])


def over_partition_anim():
    elems = [
        stext(190, 26, 'PARTITIONED BY (dt)', 'green', 14, bold=True),
        stext(570, 26, 'PARTITIONED BY (roll_no)', 'red', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
    ]
    for i in range(3):
        elems.append(sbox(40 + i * 110, 55, 100, 70, f'dt=10-1{i + 1}', '2 GB', 'green', step=1, size=12))
    for r in range(6):
        for c in range(12):
            elems.append(scell(400 + c * 28, 55 + r * 22, 25, 19, '', '#ef4444', step=2))
    elems += [
        stext(190, 160, '365 folders/year · large files', 'green', 12, step=1, focus=1),
        stext(570, 200, '100,000 folders · files of a few KB', 'red', 12, step=2, focus=2),
        stext(190, 230, 'WHERE dt=… reads 1 folder ✔', 'green', 12, step=3, focus=3),
        stext(570, 230, 'WHERE course=… lists 100,000 folders ✘', 'red', 12, step=3, focus=3),
        stext(380, 280, 'high-cardinality key → bucket it (CLUSTERED BY), do not partition it', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Partitioning by date gives a manageable number of folders, each holding a healthy amount of data.',
        'Partitioning by roll number creates one folder per student: tens of thousands of tiny folders and files, each a metastore and NameNode entry.',
        'Queries on the date table prune to one folder. On the over-partitioned table, any query not filtering on roll_no must list and open every folder.',
        'Rule: partition by a low-cardinality filter column; for high-cardinality join/lookup keys use bucketing.',
    ])


def part_vs_bucket_anim():
    elems = [
        stext(380, 24, 'PARTITIONED BY (exam_date) CLUSTERED BY (roll_no) INTO 4 BUCKETS', 'blue', 13, bold=True),
        sbox(20, 50, 160, 40, 'exam_attempts/', '', 'gray', step=1, size=12),
    ]
    for i, d in enumerate(['exam_date=10-12/', 'exam_date=10-13/']):
        y = 110 + i * 100
        elems.append(sbox(60, y, 190, 40, d, 'one folder per value', 'green', step=1, focus=1, size=11))
        elems.append(sarrow(100, 90, 98, y, 'gray', step=1))
        for b in range(4):
            elems.append(sbox(300 + b * 112, y - 5, 100, 50, f'bucket {b}', f'roll mod 4 = {b}', ['blue', 'purple', 'amber', 'pink'][b], step=2, focus=2, size=11))
        elems.append(sarrow(250, y + 20, 298, y + 20, 'gray', step=2))
    elems.append(stext(380, 290, 'filter on exam_date → prune folders · join on roll_no → match bucket k with bucket k', 'cyan', 12, step=3, focus=3, bold=True))
    return anim(canvas(760, 305, *elems), [
        '<strong>Partitioning</strong> makes one sub-folder per value of exam_date. The number of folders grows with the data (one per day).',
        '<strong>Bucketing</strong> splits each partition into a fixed number of files by hash of roll_no. There are always 4 files per partition.',
        'Each technique serves a different query pattern: date filters skip folders; joins on roll_no pair up matching buckets.',
    ])


def sampling_anim():
    elems = [stext(380, 24, 'TABLESAMPLE(BUCKET 1 OUT OF 4 ON roll_no)', 'blue', 15, bold=True)]
    for b in range(4):
        elems.append(sbox(40 + b * 175, 60, 150, 60, f'bucket {b}', '25% of students', 'blue' if b == 0 else 'gray', step=1, focus='2' if b == 0 else None, size=12))
    elems += [
        stext(380, 150, 'Hive reads only the first bucket file', 'blue', 12, step=2, focus=2),
        sflow(115, 120, 380, 190, 'blue', step=2, count=3),
        sbox(280, 190, 200, 44, 'sample: 25% of rows', 'same students every time', 'green', step=3, focus=3, size=12),
        stext(380, 270, 'ON rand() instead → random rows, but the whole table is scanned', 'amber', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'The table is bucketed by roll_no into 4 bucket files, each holding about a quarter of the students.',
        'Sampling "bucket 1 out of 4" on the bucketing column means Hive opens only one file. The other three are never read.',
        'The result is a repeatable 25% sample: the same students every run, which makes testing and comparisons easy.',
        'Sampling on <code>rand()</code> or a non-bucket column still gives a sample, but Hive must read every file to pick the rows.',
    ])


def udf_types_anim():
    elems = [
        stext(380, 24, 'UDF vs UDAF vs UDTF', 'blue', 15, bold=True),
        stext(130, 55, 'UDF: 1 → 1', 'blue', 13, step=1, bold=True),
        stext(380, 55, 'UDAF: many → 1', 'amber', 13, step=2, bold=True),
        stext(630, 55, 'UDTF: 1 → many', 'green', 13, step=3, bold=True),
    ]
    for i, v in enumerate(['anuj', 'vineeta', 'rohit']):
        elems.append(scell(30, 75 + i * 34, 80, 28, v, '#334155', step=1, size=11))
        elems.append(scell(160, 75 + i * 34, 80, 28, v.upper(), '#0ea5e9', '#fff', step=1, focus=1, size=11))
        elems.append(sarrow(112, 89 + i * 34, 158, 89 + i * 34, 'blue', step=1))
    for i, v in enumerate(['78', '91', '66']):
        elems.append(scell(290, 75 + i * 34, 60, 28, v, '#334155', step=2, size=11))
        elems.append(sarrow(352, 89 + i * 34, 408, 123, 'amber', step=2))
    elems.append(scell(410, 109, 80, 28, 'avg 78.3', '#f59e0b', '#fff', step=2, focus=2, size=11))
    elems.append(scell(530, 109, 110, 28, '[sql, spark, hive]', '#334155', step=3, size=10))
    for i, v in enumerate(['sql', 'spark', 'hive']):
        elems.append(scell(670, 75 + i * 34, 70, 28, v, '#10b981', '#fff', step=3, focus=3, size=11))
        elems.append(sarrow(642, 123, 668, 89 + i * 34, 'green', step=3))
    elems += [
        stext(130, 205, 'upper(), concat(), mask()', 'blue', 11, step=1),
        stext(380, 205, 'sum(), avg(), collect_set()', 'amber', 11, step=2),
        stext(630, 205, 'explode(), json_tuple()', 'green', 11, step=3),
        stext(380, 260, 'custom: Java GenericUDF / GenericUDAFResolver / GenericUDTF, or TRANSFORM with a script', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'A <strong>UDF</strong> works on one row at a time and returns one value per row, like <code>upper(name)</code>.',
        'A <strong>UDAF</strong> consumes many rows (a whole group) and returns one value, like <code>avg(marks)</code>. It must support partial aggregation across tasks.',
        'A <strong>UDTF</strong> takes one row and produces several rows, like <code>explode(skills)</code>.',
        'You can write your own in Java and register them, or plug in a script with <code>TRANSFORM</code>.',
    ])


def rollup_anim():
    rows = [['Juhu', 'PG-DAC', '90'], ['Juhu', 'PG-DAI', '40'], ['Juhu', 'NULL', '130'],
            ['Kharghar', 'PG-DAC', '120'], ['Kharghar', 'PG-DBDA', '60'], ['Kharghar', 'NULL', '180'], ['NULL', 'NULL', '310']]
    elems = [
        stext(380, 24, 'GROUP BY centre, course WITH ROLLUP', 'blue', 15, bold=True),
        stable(180, 50, ['centre', 'course', 'total'], rows, [130, 130, 100],
               row_steps={0: 1, 1: 1, 3: 1, 4: 1, 2: 2, 5: 2, 6: 3}, focus_rows={2: '2', 5: '2', 6: '3'}, title_color='blue'),
        stext(620, 100, '(centre, course)', 'blue', 12, step=1),
        stext(620, 150, '(centre) subtotals', 'amber', 12, step=2),
        stext(620, 230, '() grand total', 'green', 12, step=3),
    ]
    return anim(canvas(760, 270, *elems), [
        'ROLLUP first produces the normal groups, one row per (centre, course).',
        'Then it adds a subtotal per centre: course is NULL in those rows (Juhu 130, Kharghar 180).',
        'Finally a grand total row where both columns are NULL. All levels come from one scan of the data.',
    ])


def cbo_anim():
    elems = [
        stext(190, 26, 'Stale stats: "attempts = 10 MB"', 'red', 13, bold=True),
        stext(570, 26, 'Fresh stats: "attempts = 80 GB"', 'green', 13, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(60, 55, 260, 44, 'Optimizer: small table → map join', '', 'red', step=1, focus=1, size=12),
        sbox(60, 130, 260, 50, 'Load 80 GB into each', 'task\'s memory', 'red', step=2, size=12),
        sbox(60, 210, 260, 44, 'OutOfMemoryError ✘', '', 'red', step=2, focus=2, size=12),
        sarrow(190, 99, 190, 128, 'red', step=2), sarrow(190, 180, 190, 208, 'red', step=2),
        sbox(440, 55, 260, 44, 'ANALYZE TABLE … COMPUTE STATISTICS', '', 'amber', step=3, focus=3, size=11),
        sbox(440, 130, 260, 50, 'Optimizer: big + big →', 'shuffle / SMB join', 'green', step=4, size=12),
        sbox(440, 210, 260, 44, 'completes ✔', '', 'green', step=4, focus=4, size=12),
        sarrow(570, 99, 570, 128, 'green', step=4), sarrow(570, 180, 570, 208, 'green', step=4),
        stext(380, 285, 'the CBO is only as good as the statistics in the metastore', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'The cost-based optimizer reads table sizes from the metastore. Here the stats are stale: they still say the table is 10 MB.',
        'Believing it is small, Hive builds a map join and tries to load the table into memory in every task. The real table is 80 GB, so tasks fail.',
        'After a load, <code>ANALYZE TABLE ... COMPUTE STATISTICS [FOR COLUMNS]</code> updates row counts, sizes and column statistics.',
        'With correct numbers, the optimizer chooses a shuffle or SMB join and the right join order. The query succeeds.',
        'Gather statistics as part of every load job.',
    ])


def pipeline_anim():
    elems = [
        stext(380, 24, 'Raw → Curated → Report, one partition per day', 'blue', 15, bold=True),
        sbox(20, 60, 150, 70, 'Device CSV', '/landing/attendance/\ndt=2026-10-13/', 'gray', step=1, size=11),
        sbox(210, 60, 160, 70, 'raw_attendance', 'EXTERNAL · STRING\nADD PARTITION', 'amber', step=2, focus=2, size=11),
        sflow(170, 95, 210, 95, 'amber', step=2, count=2),
        sbox(410, 40, 160, 60, 'attendance', 'ORC · typed\nINSERT OVERWRITE', 'green', step=3, focus=3, size=11),
        sbox(410, 120, 160, 50, 'attendance_rejects', 'reason column', 'red', step=3, size=11),
        sflow(370, 85, 410, 70, 'green', step=3, count=2), sflow(370, 105, 410, 140, 'red', step=3, count=1),
        sbox(610, 40, 130, 60, 'report view', 'attendance %', 'purple', step=4, focus=4, size=11),
        sflow(570, 70, 610, 70, 'purple', step=4, count=2),
        sbox(210, 210, 360, 50, 'Airflow DAG (daily)', 'sensor → add partition → load → analyze → checks', 'cyan', step=5, focus=5, size=12),
        stext(380, 290, 're-run any day safely: INSERT OVERWRITE replaces only that partition', 'green', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        'Each day the devices drop a CSV into a date folder in the landing area.',
        'The <strong>raw</strong> external table reads the files as they are (all STRING), and the new date is registered as a partition.',
        'The load validates and casts the data into the <strong>curated</strong> ORC table, overwriting that day\'s partition; invalid rows go to a <strong>reject</strong> table with a reason.',
        'A <strong>report</strong> view computes centre-wise attendance % for dashboards.',
        'An orchestrator runs the steps daily. Because every step overwrites a single partition, re-running any day is safe.',
    ])


def dedup_anim():
    rows = [['2401', 'Pune', '07-01', '3'], ['2401', 'Mumbai', '09-15', '1'], ['2401', 'Mumbai', '09-15', '2'], ['2402', 'Vashi', '08-20', '1']]
    elems = [
        stext(380, 24, 'Keep the latest row per roll_no', 'blue', 15, bold=True),
        stable(60, 55, ['roll_no', 'city', 'updated', 'rn'], [r[:3] + [''] for r in rows], [100, 110, 100, 60], step=1, title_color='blue'),
        '<g data-step="2"><rect x="56" y="78" width="378" height="82" fill="none" stroke="#fbbf24" stroke-width="2" stroke-dasharray="6,4" rx="4"/></g>',
        stext(560, 120, 'PARTITION BY roll_no', 'amber', 12, step=2),
        stext(560, 140, 'ORDER BY updated DESC', 'amber', 12, step=2),
    ]
    for i, r in enumerate(rows):
        elems.append(scell(370, 81 + i * 26, 60, 26, r[3], '#162033', '#86efac' if r[3] == '1' else '#fca5a5', step=3, focus=3, bold=True))
    elems += [
        '<g data-step="4"><line x1="62" y1="94" x2="428" y2="94" stroke="#ef4444" stroke-width="2"/><line x1="62" y1="146" x2="428" y2="146" stroke="#ef4444" stroke-width="2"/></g>',
        stext(560, 190, 'WHERE rn = 1', 'red', 13, step=4, focus=4, bold=True),
        stext(380, 230, 'result: 2401 Mumbai (latest), 2402 Vashi', 'green', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 250, *elems), [
        'The change log has several rows for 2401, including an exact duplicate from a retried load.',
        'The window groups rows per roll_no and sorts each group newest first.',
        '<code>ROW_NUMBER()</code> numbers the rows 1, 2, 3 within each group. Ties still get different numbers, so exactly one row is number 1.',
        'Filtering <code>rn = 1</code> drops older versions and duplicates.',
        'One row per student remains: their latest profile.',
    ])


def iceberg_anim():
    elems = [
        stext(190, 26, 'Classic Hive table', 'amber', 14, bold=True),
        stext(570, 26, 'Iceberg table', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        sbox(90, 50, 200, 40, 'Metastore', 'list of partitions', 'purple', step=1, size=12),
    ]
    for i in range(4):
        elems.append(sbox(40 + i * 78, 120, 70, 36, f'dt=…{i}', '', 'gray', step=1, size=10))
    elems += [
        stext(190, 190, 'planning = LIST every folder', 'amber', 12, step=2, focus=2),
        stext(190, 208, '(slow on S3, no atomic commits)', 'amber', 11, step=2),
        sbox(450, 50, 240, 36, 'Catalog (HMS / Glue) → pointer', '', 'purple', step=3, size=11),
        sbox(450, 106, 240, 36, 'metadata.json: schema, snapshots', '', 'green', step=3, focus=3, size=11),
        sbox(450, 162, 240, 36, 'manifest list → manifests', '', 'green', step=3, size=11),
        sbox(450, 218, 240, 36, 'data files (exact list)', '', 'green', step=3, size=11),
        sarrow(570, 86, 570, 104, 'green', step=3), sarrow(570, 142, 570, 160, 'green', step=3), sarrow(570, 198, 570, 216, 'green', step=3),
        stext(570, 280, 'atomic commits · time travel · hidden partitioning', 'green', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'A classic Hive table is "a directory": the metastore keeps the partition list, and the files are whatever sits in each folder.',
        'To plan a query, engines list folders and files. On object storage that is slow, and a half-finished write can be seen by readers.',
        'An <strong>Iceberg</strong> table is still registered in the catalog, but the catalog points to a metadata file that lists snapshots, manifests and the exact data files.',
        'Each write creates a new snapshot atomically. This enables time travel, safe concurrent writers, and partitioning that users do not have to know about.',
    ])


def shared_catalog_anim():
    elems = [
        stext(380, 24, 'Three engines, one catalogue, one copy of the data', 'blue', 15, bold=True),
        sbox(40, 50, 190, 54, 'Hive on Tez', 'nightly ETL', 'amber', step=1, focus=1),
        sbox(285, 50, 190, 54, 'Spark SQL', 'pipelines · ML', 'blue', step=1, focus=1),
        sbox(530, 50, 190, 54, 'Trino / Impala', 'dashboards · ad hoc', 'pink', step=1, focus=1),
        sbox(255, 145, 250, 50, 'Hive Metastore', 'cdac.placements → location, schema', 'purple', step=2, focus=2),
        sarrow(135, 104, 300, 143, 'purple', step=2), sarrow(380, 104, 380, 143, 'purple', step=2), sarrow(625, 104, 460, 143, 'purple', step=2),
        sbox(180, 230, 400, 50, 'HDFS / S3: placements/*.parquet', '', 'green', step=3, focus=3),
        sflow(135, 104, 260, 230, 'amber', step=3, count=2), sflow(380, 104, 380, 230, 'blue', step=3, count=2), sflow(625, 104, 500, 230, 'pink', step=3, count=2),
        stext(380, 300, 'each engine reads the files itself with its own execution model', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 315, *elems), [
        'Different engines suit different workloads: Hive for heavy batch, Spark for pipelines and ML, Trino/Impala for fast interactive SQL.',
        'They all ask the same <strong>Hive Metastore</strong> where a table lives and what its schema is, so a table created once is visible to all.',
        'The data exists only once, as ORC/Parquet files in HDFS or S3.',
        'Each engine then reads those files with its own execution model, so you choose the engine per query without copying data.',
    ])


def orc_anim():
    elems = [
        stext(380, 24, "SELECT AVG(marks) FROM s_orc WHERE city = 'Pune'", 'blue', 14, bold=True),
        sbox(20, 50, 720, 30, 'ORC file:  footer (schema, stripe statistics)  +  stripes', '', 'gray', step=1, size=12),
    ]
    stats = [('Stripe 1', 'city: Bengaluru–Hyderabad', False), ('Stripe 2', 'city: Mumbai–Pune', True), ('Stripe 3', 'city: Bengaluru–Mumbai', False)]
    for i, (n, st, hit) in enumerate(stats):
        x = 20 + i * 245
        elems.append(sbox(x, 100, 230, 150, '', '', 'green' if hit else 'gray', step=1, fill_opacity=0.08))
        elems.append(stext(x + 115, 120, n, 'green' if hit else 'gray', 12, bold=True, step=1))
        elems.append(stext(x + 115, 138, st, 'amber', 11, step=2, focus=2))
        for c, col in enumerate(['roll', 'city', 'course', 'marks']):
            read = hit and col in ('city', 'marks')
            elems.append(scell(x + 10 + c * 53, 155, 50, 80, col, '#10b981' if read else '#334155', '#fff', step=3 if read else 1, focus=3 if read else None, size=10))
        if not hit:
            elems.append(f'<g data-step="2"><line x1="{x + 5}" y1="105" x2="{x + 225}" y2="245" stroke="#ef4444" stroke-width="3"/></g>')
    elems.append(stext(380, 285, 'skip stripes by min/max (predicate pushdown) · read 2 of 4 columns (column pruning)', 'cyan', 12, step=4, focus=4, bold=True))
    return anim(canvas(760, 300, *elems), [
        'An ORC file is divided into <strong>stripes</strong>; inside each stripe every column is stored separately. The footer holds the schema and statistics.',
        'Each stripe has <strong>min/max statistics</strong> per column. "Pune" cannot be in a stripe whose city range is Bengaluru–Hyderabad (alphabetical), so those stripes are skipped without reading them.',
        'In the remaining stripe only the <strong>city</strong> and <strong>marks</strong> columns are read; roll and course are never touched.',
        'Predicate pushdown plus column pruning is why ORC/Parquet queries read a small fraction of the bytes a CSV table needs.',
    ])


def tuning_anim():
    stages = [('Read less', 'partition pruning · columns · ORC', 'green'), ('Join smart', 'map / SMB join · fix skew', 'blue'),
              ('Faster engine', 'Tez · vectorization · CBO + stats', 'purple'), ('Healthy files', 'no small files', 'amber')]
    elems = [stext(380, 24, 'Where the time goes, and what to fix first', 'blue', 15, bold=True)]
    for i, (t, sub, c) in enumerate(stages):
        w = 680 - i * 120
        elems.append(sbox(380 - w / 2, 50 + i * 58, w, 48, t, sub, c, step=i + 1, focus=i + 1, size=12))
    elems.append(stext(380, 295, 'biggest wins usually come from the top: bytes not read cost nothing', 'cyan', 12, step=5, focus=5, bold=True))
    return anim(canvas(760, 310, *elems), [
        '<strong>Read less data</strong>: partition filters, selecting only needed columns, and columnar formats usually give the largest speed-ups.',
        '<strong>Choose the right join</strong>: broadcast small tables, bucket big ones, and handle skewed keys.',
        '<strong>Use the fast execution path</strong>: Tez (or LLAP), vectorized execution, and the cost-based optimizer fed with fresh statistics.',
        '<strong>Keep files healthy</strong>: merge small files so planning and task start-up do not dominate.',
        'Work top-down and measure each change with EXPLAIN and the Tez UI.',
    ])


def troubleshoot_anim():
    elems = [stext(380, 24, 'A repeatable troubleshooting loop', 'blue', 15, bold=True)]
    steps_ = [('Symptom', 'error · slow\nwrong result', 'red'), ('Evidence', 'EXPLAIN · logs\nTez UI · files', 'amber'),
              ('Root cause', 'data · metadata\nresources', 'purple'), ('Fix', 'DDL · settings\nquery', 'green'), ('Prevent', 'checks · alerts\nstats', 'cyan')]
    for i, (t, sub, c) in enumerate(steps_):
        x = 15 + i * 150
        elems.append(sbox(x, 90, 135, 80, t, sub, c, step=i + 1, focus=i + 1, size=12))
        if i:
            elems.append(sarrow(x - 15, 130, x - 2, 130, 'gray', step=i + 1))
    elems += [
        sarrow(690, 170, 85, 172, 'cyan', step=5, dashed=True, mid=(380, 260)),
        stext(380, 280, 'every incident should end with a check that catches it next time', 'cyan', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Start from the exact <strong>symptom</strong>: the full error message, which stage is slow, or which numbers are wrong.',
        'Collect <strong>evidence</strong>: EXPLAIN, HiveServer2 and Tez task logs, the Tez/YARN UI, and the actual files in HDFS.',
        'Name the <strong>root cause</strong>: is it the data (delimiter, skew, small files), the metadata (partitions, stats) or resources (memory, queue)?',
        'Apply the <strong>fix</strong> at the right level: table DDL, session settings or the query itself.',
        '<strong>Prevent</strong> recurrence: add a data-quality check, an alert, or automatic statistics to the pipeline.',
    ])
