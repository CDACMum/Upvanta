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
         f'<text x="{x + w/2}" y="{y + h/2 + 8}" font-size="12" fill="#f1f5f9" text-anchor="middle" font-weight="bold">{label}</text>')
    if sub:
        s += f'<text x="{x + w/2}" y="{y + h/2 + 23}" font-size="10" fill="#cbd5e1" text-anchor="middle">{sub}</text>'
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


def _mp(x, y, label, color='blue', step=None, focus=None, w=86, h=40, sub=None, op=0.22):
    """Micro-partition tile."""
    return sbox(x, y, w, h, label, sub or '', color, step=step, focus=focus, fill_opacity=op, size=11)


def _title(text, color='blue'):
    return stext(380, 24, text, color, 15, bold=True)


# ================================================================== 1 Foundations
def what_is_snowflake_anim():
    elems = [
        _title('Snowflake: a fully managed cloud data platform'),
        sbox(20, 50, 160, 50, 'Sources', 'apps · files · Kafka · SaaS', 'gray', step=1),
        sflow(180, 75, 300, 140, 'cyan', step=1, count=2),
        sbox(300, 95, 160, 95, 'Snowflake', 'SQL · storage · compute\nruns on AWS / Azure / GCP', 'blue', step=2, focus=2),
        stext(380, 210, 'nothing to install or tune', 'blue', 11, step=2),
        sflow(460, 120, 580, 70, 'green', step=3, count=2), sflow(460, 150, 580, 145, 'green', step=3, count=2),
        sflow(460, 175, 580, 220, 'green', step=3, count=2),
        sbox(580, 45, 160, 45, 'BI dashboards', 'Power BI · Tableau', 'green', step=3),
        sbox(580, 120, 160, 45, 'Data science', 'Python · Snowpark · ML', 'purple', step=3),
        sbox(580, 195, 160, 45, 'Data sharing', 'other accounts, live', 'amber', step=3),
        stext(380, 270, 'pay per second of compute + per TB of storage', 'amber', 13, step=4, focus=4, bold=True),
        stext(380, 292, 'separate storage and compute, each scaled on its own', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 305, *elems), [
        'Data arrives from applications, files in cloud storage, streaming systems and SaaS tools.',
        '<strong>Snowflake</strong> is a cloud data platform delivered as a service. You get SQL, storage and compute with no hardware or software to install, and it runs on AWS, Azure or Google Cloud.',
        'One copy of data serves many workloads at once: BI reporting, data science and live sharing with other organisations.',
        'Billing follows usage: compute is charged per second while a warehouse runs, storage per terabyte per month. Storage and compute scale independently.',
    ])


def architecture_anim():
    elems = [
        _title('Three independent layers'),
        sbox(40, 45, 680, 60, 'Cloud Services layer', 'authentication · metadata · query optimiser · transactions · security', 'purple', step=1, focus=1),
        sbox(40, 125, 205, 70, 'Warehouse ETL_WH', 'Medium · 4 credits/hr', 'blue', step=2),
        sbox(277, 125, 205, 70, 'Warehouse BI_WH', 'Small · 2 credits/hr', 'green', step=2),
        sbox(515, 125, 205, 70, 'Warehouse DS_WH', 'Large · 8 credits/hr', 'amber', step=2),
        stext(380, 118, 'Query Processing (compute) layer', 'blue', 11, step=2, bold=True),
        sflow(142, 195, 300, 235, 'cyan', step=3, count=2), sflow(380, 195, 380, 235, 'cyan', step=3, count=2),
        sflow(617, 195, 460, 235, 'cyan', step=3, count=2),
        _cyl(200, 230, 360, 60, 'Database Storage layer', 'cyan', step=3, sub='compressed columnar micro-partitions in S3 / Blob / GCS'),
        stext(380, 305, 'ETL loads never slow down BI queries: each warehouse is separate compute', 'green', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 315, *elems), [
        'The <strong>Cloud Services</strong> layer is the brain: it handles logins, keeps all metadata, parses and optimises queries, manages transactions and enforces security.',
        'The <strong>compute layer</strong> is made of <strong>virtual warehouses</strong>: independent clusters of machines that run queries. Each team or job can have its own.',
        'All warehouses read the same data from the <strong>storage layer</strong>, which keeps tables as compressed columnar micro-partitions in the cloud provider\'s object storage.',
        'Because compute is separate from storage, a heavy ETL job and a BI dashboard on different warehouses do not compete for CPU. This is the <strong>multi-cluster, shared-data</strong> architecture.',
    ])


def pricing_anim():
    elems = [
        _title('What you pay for'),
        sbox(30, 50, 220, 120, 'Compute', 'virtual warehouses\ncredits × time running\nper second, 60 s minimum', 'blue', step=1, focus=1),
        sbox(270, 50, 220, 120, 'Storage', 'average TB per month\n(compressed)\nincl. Time Travel + Fail-safe', 'cyan', step=2, focus=2),
        sbox(510, 50, 220, 120, 'Serverless & transfer', 'Snowpipe, auto-clustering,\nsearch optimisation …\n+ cross-region egress', 'purple', step=3),
        _grid(140, 195, ['Size', 'XS', 'S', 'M', 'L', 'XL'], [['credits / hour', '1', '2', '4', '8', '16']],
              [120, 70, 70, 70, 70, 70], step=4),
        stext(380, 270, 'each size up doubles credits/hour; a query that runs in half the time costs the same', 'amber', 12, step=4, bold=True),
        stext(380, 292, 'cloud services are free up to 10% of daily warehouse usage', 'gray', 11, step=5),
    ]
    return anim(canvas(760, 305, *elems), [
        '<strong>Compute</strong> is billed in <strong>credits</strong> for the time a warehouse is running, per second with a 60-second minimum each time it starts.',
        '<strong>Storage</strong> is billed on the average compressed terabytes stored per month, including data kept for Time Travel and Fail-safe.',
        '<strong>Serverless features</strong> (Snowpipe, automatic clustering, search optimisation, serverless tasks and others) use Snowflake-managed compute and are billed separately. Moving data out to another region or cloud costs data-transfer charges.',
        'Warehouse sizes double at each step: X-Small 1 credit per hour, Small 2, Medium 4, Large 8, X-Large 16, and so on. If a bigger size halves the run time, the cost stays the same.',
        'Cloud services usage is charged only above 10% of that day\'s warehouse credits. The price of a credit depends on edition, cloud and region.',
    ])


def hierarchy_anim():
    elems = [
        _title('Object hierarchy'),
        sbox(20, 45, 720, 255, 'Organization', '', 'gray', step=1, fill_opacity=0.05, top=True),
        sbox(40, 75, 680, 215, 'Account  (e.g. cdac-mumbai)', '', 'purple', step=1, fill_opacity=0.07, top=True),
        sbox(60, 105, 190, 170, 'Warehouses', '', 'blue', step=2, fill_opacity=0.08, top=True),
        sbox(270, 105, 170, 170, 'Users & Roles', '', 'amber', step=2, fill_opacity=0.08, top=True),
        sbox(460, 105, 240, 170, 'Database  CDAC', '', 'cyan', step=3, fill_opacity=0.08, top=True, focus=3),
        sbox(475, 135, 210, 125, 'Schema  BDA', '', 'green', step=4, fill_opacity=0.1, top=True),
        stext(490, 175, '• tables, views', '#e2e8f0', 11, 'start', step=4),
        stext(490, 193, '• stages, file formats', '#e2e8f0', 11, 'start', step=4),
        stext(490, 211, '• streams, tasks, pipes', '#e2e8f0', 11, 'start', step=4),
        stext(490, 229, '• functions, procedures', '#e2e8f0', 11, 'start', step=4),
        stext(155, 160, 'ETL_WH', '#e2e8f0', 11, step=2), stext(155, 180, 'BI_WH', '#e2e8f0', 11, step=2),
        stext(355, 160, 'SYSADMIN', '#e2e8f0', 11, step=2), stext(355, 180, 'ANALYST', '#e2e8f0', 11, step=2),
        stext(380, 315, 'fully qualified name: CDAC.BDA.STUDENTS', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 325, *elems), [
        'An <strong>organization</strong> groups one or more <strong>accounts</strong>. An account lives in one cloud region and is what you log in to.',
        '<strong>Account-level objects</strong> include warehouses, users, roles, resource monitors and databases themselves.',
        'A <strong>database</strong> is a logical container. It holds no compute; any warehouse can query any database the role is allowed to use.',
        'A <strong>schema</strong> inside the database holds the actual objects: tables, views, stages, file formats, sequences, streams, tasks, pipes, UDFs and stored procedures.',
        'Objects are addressed as <code>database.schema.object</code>. Unquoted names are stored in UPPER case.',
    ])


def table_types_anim():
    elems = [
        _title('Permanent vs Transient vs Temporary tables'),
        _grid(30, 50, ['', 'Permanent', 'Transient', 'Temporary'], [
            ['Time Travel', '0–90 days*', '0–1 day', '0–1 day'],
            ['Fail-safe', '7 days', 'none', 'none'],
            ['Visible to', 'all sessions', 'all sessions', 'this session only'],
            ['Dropped when', 'you drop it', 'you drop it', 'session ends'],
            ['Typical use', 'core tables', 'staging, ETL work', 'scratch in a script'],
        ], [150, 180, 180, 190], rh=30, step=1, size=12),
        stext(380, 240, '* 90 days needs Enterprise edition; Standard allows up to 1 day', 'gray', 11, step=1),
        sbox(185, 255, 390, 40, 'no Fail-safe → lower storage bill for re-creatable data', '', 'green', step=2, focus=2, size=12),
    ]
    return anim(canvas(760, 305, *elems), [
        'All three types store data the same way. They differ in how long deleted or changed data is kept for recovery, and who can see them.',
        'Use <strong>transient</strong> tables for data you can rebuild (staging, intermediate ETL output). They skip the 7-day Fail-safe, so they cost less to store.',
    ])


# ================================================================== 2 Virtual warehouses
def warehouse_anim():
    elems = [
        _title('A virtual warehouse = a compute cluster you can resize'),
        sbox(30, 60, 120, 60, 'X-Small', '1 credit/hr', 'blue', step=1),
        sbox(170, 55, 130, 70, 'Small', '2 credits/hr', 'blue', step=1),
        sbox(320, 50, 140, 80, 'Medium', '4 credits/hr', 'blue', step=1),
        sbox(480, 45, 150, 90, 'Large', '8 credits/hr', 'blue', step=1),
        stext(690, 95, '… 6X-Large', 'gray', 12, step=1),
        stext(380, 160, 'each size has about twice the compute of the one before', 'cyan', 12, step=2, bold=True),
        sbox(60, 185, 290, 90, 'ALTER WAREHOUSE … SET', 'WAREHOUSE_SIZE = \'LARGE\'\nnew queries use the new size;\nrunning queries finish on the old', 'amber', step=3, focus=3),
        sbox(410, 185, 290, 90, 'No data inside', 'reads tables from shared storage;\nlocal SSD only caches data\nwhile it is running', 'green', step=4),
    ]
    return anim(canvas(760, 295, *elems), [
        'A <strong>virtual warehouse</strong> is a named cluster of compute that runs your SQL. Sizes go from X-Small to 6X-Large.',
        'Every step up roughly doubles the compute resources, and doubles the credits charged per hour.',
        'You can resize a warehouse at any time, even while it is running. Queries already running finish on the old size; new and queued queries use the new size.',
        'A warehouse stores no tables. It reads micro-partitions from the storage layer and keeps a temporary cache on its local SSD while it is running.',
    ])


def scale_up_out_anim():
    elems = [
        _title('Scale UP for slow queries, scale OUT for many users'),
        stext(190, 55, 'Scale up (bigger size)', 'blue', 13, step=1, bold=True),
        sbox(60, 70, 90, 50, 'S', '1 big query', 'blue', step=1),
        sarrow(155, 95, 200, 95, 'blue', step=1),
        sbox(205, 65, 120, 70, 'L', 'same query faster', 'blue', step=1, focus=1),
        stext(190, 160, 'complex joins, large scans, spilling', 'gray', 11, step=1),
        stext(570, 55, 'Scale out (multi-cluster)', 'green', 13, step=2, bold=True),
        sbox(420, 70, 90, 50, 'M #1', '', 'green', step=2), sbox(520, 70, 90, 50, 'M #2', '', 'green', step=3),
        sbox(620, 70, 90, 50, 'M #3', '', 'green', step=3),
        stext(570, 145, '50 analysts at 10 a.m. → extra clusters start', 'green', 11, step=3),
        stext(570, 162, 'queue drains → clusters shut down', 'green', 11, step=3),
        _grid(170, 190, ['Policy', 'Starts a cluster when…'], [
            ['STANDARD', 'a query queues (favours speed)'],
            ['ECONOMY', 'enough load to keep it busy ~6 min (favours cost)'],
        ], [130, 330], rh=28, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        '<strong>Scaling up</strong> means a bigger size. It helps a single heavy query: more memory and CPU, less spilling to disk.',
        '<strong>Scaling out</strong> means a <strong>multi-cluster warehouse</strong> (Enterprise edition) with a minimum and maximum number of clusters of the same size.',
        'When many users run queries at once, Snowflake starts extra clusters so queries do not queue. When load drops, the extra clusters shut down.',
        'The <strong>scaling policy</strong> decides how eagerly clusters start: STANDARD starts one as soon as queries queue; ECONOMY waits until there is enough work to keep it busy for about six minutes.',
    ])


def suspend_anim():
    elems = [
        _title('Auto-suspend and auto-resume'),
        stext(40, 70, 'time →', 'gray', 11, 'start', step=1),
        sbox(40, 85, 150, 40, 'query', '', 'blue', step=1), sbox(200, 85, 90, 40, 'query', '', 'blue', step=1),
        sbox(300, 85, 120, 40, 'idle 60 s', '', 'gray', step=2, fill_opacity=0.1),
        sbox(430, 85, 120, 40, 'SUSPENDED', '', 'red', step=2, focus=2),
        sbox(560, 85, 160, 40, 'query → RESUME', '', 'green', step=3, focus=3),
        stext(380, 160, 'billed per second while running, minimum 60 s each time it resumes', 'amber', 12, step=4, bold=True),
        _grid(150, 180, ['Setting', 'Typical value'], [
            ['AUTO_SUSPEND', '60 s (BI / ad hoc), 300+ s if cache reuse matters'],
            ['AUTO_RESUME', 'TRUE'],
            ['INITIALLY_SUSPENDED', 'TRUE at creation'],
        ], [170, 290], rh=26, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'While queries run, the warehouse is in the STARTED state and consuming credits.',
        'After it has been idle for <code>AUTO_SUSPEND</code> seconds it suspends itself and stops billing. Its local cache is lost.',
        'With <code>AUTO_RESUME = TRUE</code>, the next query that needs it starts it again automatically, usually within seconds.',
        'Billing is per second while running, with a <strong>60-second minimum</strong> every time it resumes. Very low suspend values can cost more if a warehouse resumes many times.',
        'A common starting point is 60 seconds for BI and ad hoc warehouses, longer when the local cache matters for repeated queries.',
    ])


def cache_anim():
    elems = [
        _title('Three caches, checked in this order'),
        sbox(30, 50, 140, 40, 'SELECT …', '', 'gray', step=1),
        sarrow(170, 70, 225, 70, 'gray', step=1),
        sbox(230, 45, 500, 55, '① Result cache (Cloud Services)', 'identical query + unchanged data → answer in ms, no warehouse, 24 h', 'green', step=1, focus=1),
        sbox(230, 115, 500, 55, '② Metadata', 'COUNT(*), MIN/MAX on a table answered from micro-partition stats', 'purple', step=2),
        sbox(230, 185, 500, 55, '③ Warehouse local disk cache', 'micro-partitions read earlier stay on the warehouse SSD until it suspends', 'blue', step=3),
        _cyl(330, 255, 300, 50, 'Remote storage (slowest)', 'cyan', step=4),
        stext(110, 290, 'only on a miss', 'gray', 11, step=4),
    ]
    return anim(canvas(760, 315, *elems), [
        'The <strong>result cache</strong> keeps the results of every query for 24 hours. If the same query text runs again, the role has access and the data has not changed, the stored result is returned without using a warehouse.',
        'Some queries need no data at all: row counts and MIN/MAX are answered from the <strong>metadata</strong> Snowflake keeps for every micro-partition.',
        'The <strong>warehouse cache</strong> is the local SSD of a running warehouse. Data read by earlier queries is reused until the warehouse suspends.',
        'Only data not found in any cache is read from <strong>remote storage</strong>, which is the slowest path.',
    ])


def profile_anim():
    elems = [
        _title('Reading the Query Profile'),
        sbox(280, 45, 200, 40, 'Result', '', 'gray', step=1),
        sarrow(380, 125, 380, 90, 'gray', step=1),
        sbox(280, 125, 200, 40, 'Aggregate  8%', '', 'blue', step=1),
        sarrow(380, 205, 380, 170, 'gray', step=1),
        sbox(280, 205, 200, 40, 'Join  61%', '', 'red', step=2, focus=2),
        sarrow(250, 260, 300, 247, 'gray', step=1), sarrow(510, 260, 460, 247, 'gray', step=1),
        sbox(120, 260, 180, 40, 'TableScan EXAMS 28%', '', 'blue', step=1, size=11),
        sbox(460, 260, 180, 40, 'TableScan STUDENTS 3%', '', 'blue', step=1, size=11),
        stext(620, 60, 'Look for:', 'amber', 12, step=3, bold=True),
        stext(560, 82, '• bytes spilled to local/remote', '#e2e8f0', 11, 'start', step=3),
        stext(560, 100, '• partitions scanned vs total', '#e2e8f0', 11, 'start', step=3),
        stext(560, 118, '• exploding join (rows out ≫ in)', '#e2e8f0', 11, 'start', step=3),
        stext(560, 136, '• queued time (overloaded WH)', '#e2e8f0', 11, 'start', step=3),
        stext(20, 140, 'most expensive node', 'red', 11, 'start', step=2),
        stext(20, 156, 'is shown first', 'red', 11, 'start', step=2),
    ]
    return anim(canvas(760, 310, *elems), [
        'The <strong>Query Profile</strong> in Snowsight shows the execution plan as a tree of operators with the share of time spent in each.',
        'Start from the most expensive node. Here the Join takes 61% of the time.',
        'Then check the statistics: spilling means the warehouse is too small for the data; scanning most partitions means pruning is not working; far more rows coming out of a join than going in means a bad join condition; queuing means too many concurrent queries.',
    ])


# ================================================================== 3 Micro-partitions & performance
def micropartition_anim():
    elems = [
        _title('A table is stored as micro-partitions'),
        _grid(30, 50, ['ROLL_NO', 'COURSE', 'CENTRE', 'MARKS'], [
            ['2401', 'PGCP-BDA', 'Kharghar', '78.50'], ['2402', 'PGCP-BDA', 'Juhu', '88.00'],
            ['2403', 'PGCP-AI', 'Kharghar', '91.25'], ['2404', 'PGCP-AC', 'Kharghar', '67.00'],
            ['…', '…', '…', '…']], [70, 80, 80, 60], rh=24, step=1),
        sarrow(330, 120, 380, 120, 'gray', step=2),
        _mp(390, 50, 'MP 1', 'blue', step=2, sub='rows 1–40k'), _mp(490, 50, 'MP 2', 'blue', step=2, sub='rows 40k–80k'),
        _mp(590, 50, 'MP 3', 'blue', step=2, sub='…'),
        stext(560, 115, 'each 50–500 MB uncompressed, immutable', 'blue', 11, step=2),
        sbox(390, 130, 290, 70, 'Inside: columnar', 'ROLL_NO | COURSE | CENTRE | MARKS\neach column compressed on its own', 'cyan', step=3, focus=3),
        sbox(390, 215, 290, 70, 'Metadata per column', 'min / max · distinct count · null count', 'purple', step=4, focus=4),
        stext(170, 220, 'no PARTITION BY needed:', 'green', 12, step=5, bold=True),
        stext(170, 238, 'created automatically', 'green', 12, step=5),
        stext(170, 256, 'in load order', 'green', 12, step=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'You see a normal table of rows and columns.',
        'Snowflake splits it automatically into <strong>micro-partitions</strong>: contiguous groups of rows, each 50–500 MB before compression (much smaller on disk). They are immutable: a change writes new micro-partitions.',
        'Inside each micro-partition data is <strong>stored by column</strong> and every column is compressed separately, so a query reads only the columns it needs.',
        'For every column in every micro-partition the Cloud Services layer keeps <strong>metadata</strong>: the min and max value, the number of distinct values and null count.',
        'You never declare partitions. They are created as data is loaded, so their contents follow the order of loading.',
    ])


def pruning_anim():
    vals = [('MP1', '2026-01-01', '01-10'), ('MP2', '2026-01-11', '01-20'), ('MP3', '2026-01-21', '01-31'),
            ('MP4', '2026-02-01', '02-10'), ('MP5', '2026-02-11', '02-20'), ('MP6', '2026-02-21', '02-28')]
    elems = [_title("WHERE exam_date = '2026-02-15'")]
    for i, (n, a, b) in enumerate(vals):
        x = 30 + i * 120
        elems.append(_mp(x, 60, n, 'blue', step=1, w=105, h=55, sub=f'date {a[5:]}…{b}'))
        if n != 'MP5':
            elems.append(sbox(x, 60, 105, 55, '', '', 'gray', step=2, fill_opacity=0.65))
            elems.append(stext(x + 52, 140, 'skipped', 'red', 11, step=2))
        else:
            elems.append(stext(x + 52, 140, 'scanned', 'green', 12, step=2, focus=2, bold=True))
    elems += [
        stext(380, 180, 'Partitions scanned: 1   Partitions total: 6', 'amber', 14, step=3, bold=True),
        stext(380, 210, 'pruning uses only the min/max metadata, no data is read to decide', 'gray', 12, step=3),
        stext(380, 250, "WHERE TO_CHAR(exam_date) LIKE '%-02-15'  → wrapping the column in a function", 'red', 12, step=4, focus=4),
        stext(380, 270, 'can stop pruning: compare the column directly', 'red', 12, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'The table has six micro-partitions. The metadata says which date range each one holds.',
        'For <code>exam_date = \'2026-02-15\'</code> only MP5 can contain matching rows. The other five are <strong>pruned</strong>: never read.',
        'The Query Profile reports this as <em>Partitions scanned</em> vs <em>Partitions total</em>. Good pruning is the biggest performance win in Snowflake.',
        'Pruning works best when the filter compares the column directly. Wrapping it in an expression may prevent Snowflake from using the min/max ranges.',
    ])


def clustering_anim():
    elems = [
        _title('Clustering: put similar values in the same micro-partitions'),
        stext(190, 55, 'Before (loaded in random order)', 'red', 12, step=1, bold=True),
        stext(570, 55, 'After CLUSTER BY (exam_date)', 'green', 12, step=2, bold=True),
    ]
    before = ['Jan–Dec', 'Jan–Nov', 'Feb–Dec', 'Jan–Dec']
    after = ['Jan–Mar', 'Apr–Jun', 'Jul–Sep', 'Oct–Dec']
    for i in range(4):
        elems.append(_mp(40 + (i % 2) * 150, 70 + (i // 2) * 55, f'MP{i+1}', 'red', step=1, w=140, h=45, sub=before[i]))
        elems.append(_mp(420 + (i % 2) * 150, 70 + (i // 2) * 55, f'MP{i+1}', 'green', step=2, w=140, h=45, sub=after[i]))
    elems += [
        stext(190, 200, "a query for 'May' must scan all 4", 'red', 11, step=1),
        stext(570, 200, "a query for 'May' scans only MP2", 'green', 11, step=2),
        stext(380, 235, 'clustering depth: average number of overlapping partitions (lower = better)', 'amber', 12, step=3, focus=3, bold=True),
        stext(380, 262, 'Automatic Clustering re-sorts in the background (serverless credits)', 'purple', 12, step=4),
        stext(380, 282, 'use for multi-TB tables queried by a column, e.g. a date', 'gray', 11, step=4),
    ]
    return anim(canvas(760, 295, *elems), [
        'When data arrives in random order, every micro-partition holds values from the whole range, so filters can prune nothing.',
        'A <strong>clustering key</strong> asks Snowflake to keep rows with similar key values together, so each micro-partition covers a narrow range.',
        'The <strong>clustering depth</strong> measures how many micro-partitions overlap for a value. Check it with <code>SYSTEM$CLUSTERING_INFORMATION</code>.',
        'Once a key is defined, <strong>Automatic Clustering</strong> maintains it in the background using serverless compute, billed in credits. It is worth it only for large tables with selective, frequent filters.',
    ])


def accel_anim():
    elems = [
        _title('Extra performance features (Enterprise edition)'),
        sbox(20, 50, 230, 150, 'Search Optimization', 'point lookups on\nhigh-cardinality columns\nWHERE email = …\nsubstring, VARIANT, geo', 'blue', step=1, focus=1),
        sbox(265, 50, 230, 150, 'Materialized View', 'pre-computed result\nof one table\nkept up to date\nautomatically', 'green', step=2, focus=2),
        sbox(510, 50, 230, 150, 'Query Acceleration', 'offloads parts of big\nscans to shared serverless\ncompute for outlier\nqueries', 'purple', step=3, focus=3),
        stext(380, 230, 'all three run on serverless compute and add storage or credit cost', 'amber', 12, step=4, bold=True),
        stext(380, 255, 'measure first: Query Profile, then enable the one that matches the problem', 'gray', 12, step=4),
    ]
    return anim(canvas(760, 275, *elems), [
        '<strong>Search Optimization Service</strong> builds a persistent search access path so selective lookups (an email, an ID, a substring) skip almost all micro-partitions.',
        'A <strong>materialized view</strong> stores the pre-computed result of a query on a single table and Snowflake keeps it current in the background.',
        'The <strong>Query Acceleration Service</strong> lends extra serverless compute to large scans in outlier queries, so one huge query does not need a permanently bigger warehouse.',
        'Each feature has a maintenance cost. Use the Query Profile to find the real bottleneck before turning one on.',
    ])


def qualify_anim():
    elems = [
        _title('QUALIFY filters on a window function'),
        _grid(30, 55, ['NAME', 'COURSE', 'MARKS', 'RNK'], [
            ['Sana', 'PGCP-BDA', '93.75', '1'], ['Aarshvi', 'PGCP-BDA', '88.00', '2'], ['Anuj', 'PGCP-BDA', '78.50', '3'],
            ['Riya', 'PGCP-AI', '91.25', '1'], ['Omkar', 'PGCP-AI', '72.50', '2']],
            [90, 100, 70, 50], rh=26, step=1, hl={0: '#14532d', 3: '#14532d'}),
        sbox(400, 55, 330, 90, 'Without QUALIFY', 'SELECT * FROM (\n  SELECT …, RANK() OVER (…) rnk FROM t\n) WHERE rnk = 1', 'gray', step=2),
        sbox(400, 165, 330, 75, 'With QUALIFY', 'SELECT … FROM t\nQUALIFY RANK() OVER (…) = 1', 'green', step=3, focus=3),
        stext(380, 270, 'order of evaluation: FROM → WHERE → GROUP BY → HAVING → WINDOW → QUALIFY', 'amber', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'A window function ranks students inside each course. We want only rank 1 per course (the green rows).',
        'In standard SQL you cannot filter on a window function in WHERE, so you wrap the query in a sub-query.',
        'Snowflake\'s <strong>QUALIFY</strong> clause filters on window-function results directly, in one query.',
        'QUALIFY is evaluated after window functions, just as HAVING is evaluated after GROUP BY.',
    ])


# ================================================================== 4 Loading data
def stages_anim():
    elems = [
        _title('Stages: where files wait before loading'),
        sbox(20, 55, 150, 45, 'Laptop file', 'results.csv', 'gray', step=1),
        sflow(170, 77, 260, 77, 'cyan', step=1, count=2), stext(215, 68, 'PUT', 'cyan', 11, step=1, bold=True),
        sbox(260, 45, 230, 75, 'Internal stage', '@~ (user) · @%students (table)\n@cdac_stage (named)', 'blue', step=1, focus=1),
        sbox(20, 160, 150, 45, 'S3 / ADLS / GCS', 'bucket path', 'gray', step=2),
        sflow(170, 182, 260, 182, 'amber', step=2, count=2),
        sbox(260, 150, 230, 75, 'External stage', 'URL + STORAGE INTEGRATION\n(no keys in SQL)', 'amber', step=2, focus=2),
        sflow(490, 85, 590, 135, 'green', step=3, count=2), sflow(490, 185, 590, 145, 'green', step=3, count=2),
        sbox(590, 110, 150, 55, 'Table', 'COPY INTO', 'green', step=3),
        stext(380, 260, 'LIST @cdac_stage;  ·  SELECT $1, $2 FROM @cdac_stage (query files in place)', 'purple', 12, step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'An <strong>internal stage</strong> is storage managed by Snowflake. Every user has <code>@~</code>, every table has <code>@%table</code>, and you can create named stages. Local files are uploaded with <code>PUT</code> (from SnowSQL or a driver).',
        'An <strong>external stage</strong> points to your own bucket or container. Access is granted through a <strong>storage integration</strong>, so no secret keys appear in SQL.',
        '<code>COPY INTO table</code> loads staged files into a table using a warehouse.',
        'You can list staged files and even query them directly with <code>$1, $2 …</code> column positions before loading.',
    ])


def copy_anim():
    files = ['part_01.csv', 'part_02.csv', 'part_03.csv']
    elems = [_title('COPY INTO remembers which files it loaded')]
    for i, f in enumerate(files):
        elems.append(sbox(30, 55 + i * 55, 160, 42, f, '', 'blue', step=1, size=12))
    elems += [
        sflow(190, 120, 320, 120, 'green', step=1, count=3),
        sbox(320, 90, 160, 60, 'STUDENTS', '+3 files loaded', 'green', step=1),
        sbox(520, 55, 220, 120, 'Load metadata (64 days)', 'part_01.csv  LOADED\npart_02.csv  LOADED\npart_03.csv  LOADED', 'purple', step=2, focus=2),
        stext(380, 210, 'Run COPY again → "Copy executed with 0 files processed."', 'amber', 12, step=3, bold=True),
        stext(380, 232, 'FORCE = TRUE reloads (duplicates!) · ON_ERROR = CONTINUE | SKIP_FILE | ABORT_STATEMENT', 'gray', 11, step=4),
        stext(380, 252, 'VALIDATION_MODE = RETURN_ERRORS checks files without loading', 'gray', 11, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        '<code>COPY INTO</code> reads all matching files in the stage, in parallel, and loads them into the table.',
        'For every table, Snowflake records which files were loaded (name and checksum) and keeps this <strong>load metadata for 64 days</strong>.',
        'Running the same COPY again skips files already loaded, so a re-run after a failure does not create duplicates.',
        '<code>FORCE = TRUE</code> ignores the metadata and reloads. <code>ON_ERROR</code> decides what happens to bad rows, and <code>VALIDATION_MODE</code> tests files without loading them.',
    ])


def snowpipe_anim():
    elems = [
        _title('Snowpipe: continuous loading as files arrive'),
        sbox(20, 60, 150, 50, 'New file in S3', 'att_2026-02-15.json', 'gray', step=1),
        sflow(170, 85, 260, 85, 'amber', step=2, count=2),
        sbox(260, 60, 150, 50, 'Event (SQS)', 'ObjectCreated', 'amber', step=2),
        sflow(410, 85, 500, 85, 'cyan', step=3, count=2),
        sbox(500, 50, 240, 70, 'PIPE  att_pipe', 'AUTO_INGEST = TRUE\nruns its COPY INTO', 'blue', step=3, focus=3),
        sarrow(620, 120, 620, 165, 'green', step=3),
        sbox(530, 165, 180, 45, 'ATTENDANCE table', '', 'green', step=3),
        stext(200, 160, 'serverless: no warehouse needed', 'purple', 12, step=4, bold=True),
        stext(200, 180, 'latency: usually a minute or so', 'purple', 11, step=4),
        stext(380, 245, 'Snowpipe Streaming: rows (not files) from Kafka / SDK, lower latency', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 265, *elems), [
        'A new attendance file lands in the bucket.',
        'The cloud storage sends an event notification (for example an S3 event to an SQS queue that Snowflake provides).',
        'The <strong>pipe</strong> receives the event and runs its <code>COPY INTO</code> statement for just that file.',
        'Snowpipe runs on serverless compute, so no warehouse has to be running. Files usually appear in the table within a minute or two.',
        '<strong>Snowpipe Streaming</strong> writes rows directly through an SDK or the Kafka connector, without intermediate files, for lower latency.',
    ])


def unload_anim():
    elems = [
        _title('Unloading: COPY INTO @stage'),
        sbox(30, 70, 170, 60, 'Table / query', 'RESULTS', 'green', step=1),
        sflow(200, 100, 330, 100, 'cyan', step=1, count=3),
        sbox(330, 50, 200, 100, '@export_stage/results/', 'data_0_0_0.csv.gz\ndata_0_1_0.csv.gz\ndata_0_2_0.csv.gz', 'blue', step=2, focus=2),
        sbox(570, 50, 170, 100, 'PARTITION BY', 'centre=Juhu/…\ncentre=Kharghar/…', 'purple', step=3),
        stext(380, 190, 'parallel: one file per thread; SINGLE = TRUE for one file', 'amber', 12, step=2),
        stext(380, 215, 'MAX_FILE_SIZE · HEADER = TRUE · FILE_FORMAT (CSV, JSON, PARQUET)', 'gray', 12, step=4),
        stext(380, 240, 'then GET @stage (internal) or read straight from the bucket (external)', 'gray', 12, step=4),
    ]
    return anim(canvas(760, 260, *elems), [
        '<code>COPY INTO @stage FROM table_or_query</code> writes data out to files.',
        'The warehouse writes files in parallel, so you get several files by default. <code>SINGLE = TRUE</code> forces one file.',
        '<code>PARTITION BY</code> an expression writes files into folder-like prefixes, useful for data lakes.',
        'Choose the file format and size, then download with <code>GET</code> from an internal stage or let other tools read from the external bucket.',
    ])


def filesize_anim():
    elems = [
        _title('Loading is parallel per file'),
        sbox(30, 55, 200, 70, '1 file × 20 GB', 'one thread busy,\nothers idle', 'red', step=1),
        sbox(280, 55, 200, 70, '200 000 files × 10 KB', 'per-file overhead\ndominates', 'red', step=2),
        sbox(530, 55, 200, 70, '~100 files × 100–250 MB', 'compressed: every\nthread busy', 'green', step=3, focus=3),
        stext(380, 160, 'split big files, combine tiny ones', 'amber', 13, step=4, bold=True),
        stext(380, 185, 'load into a staging table, transform with SQL (ELT)', 'gray', 12, step=4),
        stext(380, 205, 'use a dedicated loading warehouse sized to the number of files', 'gray', 12, step=4),
    ]
    return anim(canvas(760, 225, *elems), [
        'One huge file is loaded by one thread, so most of the warehouse sits idle.',
        'Millions of tiny files spend more time on per-file overhead than on loading data.',
        'Snowflake recommends files of roughly <strong>100–250 MB compressed</strong> so the load spreads across all threads.',
        'Split or combine files before loading, land them in a staging table and transform with SQL afterwards.',
    ])



# ================================================================== 5 Semi-structured
def variant_anim():
    elems = [
        _title('VARIANT: store JSON as-is, query it with paths'),
        sbox(20, 50, 300, 150, 'raw.v  (VARIANT)', '{ "roll": 2401,\n  "name": "Anuj",\n  "exams": [\n    {"sub":"SQL","m":78},\n    {"sub":"Spark","m":82} ] }', 'gray', step=1),
        sarrow(325, 125, 380, 125, 'gray', step=2),
        _grid(390, 50, ['Path', 'Result'], [
            ['v:name', '"Anuj"  (VARIANT)'], ['v:name::STRING', 'Anuj'], ['v:exams[0].sub', '"SQL"'],
            ["v['roll']::INT", '2401'], ['v:missing', 'NULL']], [170, 170], rh=27, step=2),
        stext(380, 230, ': navigates the object · [n] indexes arrays (from 0) · :: casts', 'amber', 12, step=3, bold=True),
        stext(380, 255, 'Snowflake stores common keys as hidden columns, so path queries still prune', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'A <strong>VARIANT</strong> column can hold any JSON (or Avro, Parquet, ORC, XML) value: objects, arrays, strings, numbers, nested to any depth.',
        'Use <code>column:key</code> and <code>[index]</code> to navigate. The result is still a VARIANT (strings appear in double quotes) until you cast it.',
        'Cast with <code>::STRING</code>, <code>::INT</code>, <code>::DATE</code> and so on. A missing key returns NULL, not an error.',
        'Snowflake extracts frequently used keys into hidden columns with their own statistics, so queries on JSON paths are columnar and can prune micro-partitions.',
    ])


def flatten_anim():
    elems = [
        _title('LATERAL FLATTEN: one row per array element'),
        _grid(30, 55, ['ROLL', 'EXAMS (array)'], [['2401', '[SQL 78, Spark 82]'], ['2402', '[SQL 91]']], [70, 170], rh=30, step=1),
        sarrow(285, 100, 340, 100, 'gray', step=2),
        stext(312, 88, 'FLATTEN', 'amber', 11, step=2, bold=True),
        _grid(350, 55, ['ROLL', 'INDEX', 'SUBJECT', 'M'], [['2401', '0', 'SQL', '78'], ['2401', '1', 'Spark', '82'], ['2402', '0', 'SQL', '91']],
              [70, 70, 110, 60], rh=30, step=2, hl={0: '#1e3a5f', 1: '#1e3a5f'}),
        stext(380, 210, 'FLATTEN columns: SEQ · KEY · PATH · INDEX · VALUE · THIS', 'cyan', 12, step=3, bold=True),
        stext(380, 235, 'OUTER => TRUE keeps rows whose array is empty or NULL', 'purple', 12, step=4),
        stext(380, 255, 'RECURSIVE => TRUE walks every nested level', 'purple', 12, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'Each student row holds an array of exam objects.',
        '<code>LATERAL FLATTEN(input => v:exams)</code> produces one output row per array element, joined back to its parent row.',
        'FLATTEN returns the columns SEQ, KEY, PATH, INDEX, VALUE and THIS. You normally use <code>VALUE</code> (the element) and <code>INDEX</code> (its position).',
        'Without <code>OUTER => TRUE</code>, a parent with an empty array disappears from the result, just like an inner join. <code>RECURSIVE => TRUE</code> expands all nested levels.',
    ])


def construct_anim():
    elems = [
        _title('Relational → JSON'),
        _grid(30, 60, ['NAME', 'COURSE', 'MARKS'], [['Sana', 'PGCP-BDA', '93.75'], ['Aarshvi', 'PGCP-BDA', '88.00']], [90, 100, 70], rh=28, step=1),
        sarrow(300, 100, 350, 100, 'gray', step=2),
        sbox(360, 50, 380, 60, 'OBJECT_CONSTRUCT(\'name\', name, \'marks\', marks)', '{"marks": 93.75, "name": "Sana"}', 'blue', step=2, size=11),
        sbox(360, 125, 380, 60, 'ARRAY_AGG(obj) … GROUP BY course', '[ {…Sana…}, {…Aarshvi…} ]', 'green', step=3, size=11),
        sbox(360, 200, 380, 60, 'OBJECT_AGG(name, marks)', '{"Aarshvi": 88, "Sana": 93.75}', 'purple', step=4, size=11),
        stext(170, 200, 'build API payloads', 'amber', 12, step=5, bold=True),
        stext(170, 220, 'or nested exports', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'Start from ordinary rows.',
        '<code>OBJECT_CONSTRUCT</code> turns columns into a JSON object (keys are stored sorted).',
        '<code>ARRAY_AGG</code> collects values from many rows into one array per group.',
        '<code>OBJECT_AGG</code> builds one object from key/value pairs across rows.',
        'Together they produce nested JSON for APIs, or for unloading with <code>COPY INTO @stage FILE_FORMAT = (TYPE = JSON)</code>.',
    ])


def infer_anim():
    elems = [
        _title('Loading Parquet without writing the schema'),
        sbox(20, 55, 170, 60, '@lake/results/', '*.parquet', 'gray', step=1),
        sarrow(190, 85, 245, 85, 'gray', step=2),
        sbox(250, 45, 230, 80, 'INFER_SCHEMA(...)', 'ROLL_NO NUMBER\nNAME TEXT\nMARKS REAL', 'blue', step=2, focus=2),
        sarrow(480, 85, 535, 85, 'gray', step=3),
        sbox(540, 45, 200, 80, 'CREATE TABLE …', 'USING TEMPLATE', 'green', step=3),
        sbox(160, 165, 440, 60, "COPY INTO results FROM @lake/results/", "MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE", 'amber', step=4, focus=4, size=12),
        stext(380, 255, 'Parquet / Avro / ORC carry their own schema; CSV can be inferred too', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'Parquet files in a stage already contain column names and types.',
        '<code>INFER_SCHEMA</code> reads that metadata and returns the column definitions.',
        '<code>CREATE TABLE … USING TEMPLATE</code> creates a table from those definitions in one statement.',
        '<code>MATCH_BY_COLUMN_NAME</code> loads each file column into the table column with the same name, regardless of order.',
        'Schema evolution (<code>ENABLE_SCHEMA_EVOLUTION = TRUE</code>) can add new columns automatically when files gain fields.',
    ])


def semi_perf_anim():
    elems = [
        _title('Keep it in VARIANT or flatten into columns?'),
        sbox(20, 50, 350, 165, 'Keep VARIANT when…', '', 'blue', step=1, fill_opacity=0.08, top=True),
        stext(40, 100, '• structure changes often', '#e2e8f0', 12, 'start', step=1),
        stext(40, 122, '• landing / raw (bronze) layer', '#e2e8f0', 12, 'start', step=1),
        stext(40, 144, '• rarely queried fields', '#e2e8f0', 12, 'start', step=1),
        stext(40, 166, '• audit: keep the original payload', '#e2e8f0', 12, 'start', step=1),
        sbox(390, 50, 350, 165, 'Extract to columns when…', '', 'green', step=2, fill_opacity=0.08, top=True),
        stext(410, 100, '• fields used in filters and joins', '#e2e8f0', 12, 'start', step=2),
        stext(410, 122, '• dates/timestamps stored as strings', '#e2e8f0', 12, 'start', step=2),
        stext(410, 144, '• mixed types in one key', '#e2e8f0', 12, 'start', step=2),
        stext(410, 166, '• arrays that must be aggregated', '#e2e8f0', 12, 'start', step=2),
        stext(380, 245, 'common pattern: raw VARIANT table → typed, flattened table via a view or dynamic table', 'amber', 12, step=3, bold=True),
    ]
    return anim(canvas(760, 265, *elems), [
        'VARIANT is ideal for landing data whose shape changes, and for keeping the original payload.',
        'Hidden sub-columns are not created for every key (for example keys with mixed types, or very many keys), and strings that hold dates do not prune well. Extract heavily used fields into typed columns.',
        'Most pipelines keep both: a raw VARIANT table and a curated, typed table built from it.',
    ])


# ================================================================== 6 Time Travel, Fail-safe, cloning
def timetravel_anim():
    elems = [
        _title('Time Travel: query or restore the past'),
        stext(60, 75, '09:00', 'gray', 11, step=1), stext(260, 75, '10:00', 'gray', 11, step=1), stext(460, 75, '10:05', 'gray', 11, step=1),
        stext(660, 75, 'now', 'gray', 11, step=1),
        sarrow(40, 85, 720, 85, 'gray', step=1),
        sbox(20, 100, 160, 45, 'data v1', '', 'blue', step=1), sbox(220, 100, 160, 45, 'UPDATE → v2', '', 'blue', step=1),
        sbox(420, 100, 160, 45, 'bad DELETE → v3', '', 'red', step=1, focus=1),
        sbox(110, 170, 540, 40, "SELECT * FROM results AT(TIMESTAMP => '…10:00'::TIMESTAMP_LTZ)", '', 'green', step=2, size=12),
        sbox(110, 220, 540, 40, "SELECT * FROM results BEFORE(STATEMENT => '&lt;query id of DELETE&gt;')", '', 'green', step=3, size=12),
        stext(380, 290, 'UNDROP TABLE · CREATE TABLE … CLONE … AT(…) to restore', 'amber', 13, step=4, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        'Every change creates new micro-partitions; the old ones are kept for the <strong>retention period</strong> (<code>DATA_RETENTION_TIME_IN_DAYS</code>).',
        'Query the table as it was at a timestamp with <code>AT(TIMESTAMP => …)</code>, or <code>AT(OFFSET => -seconds)</code>.',
        '<code>BEFORE(STATEMENT => query_id)</code> returns the data just before a given statement ran, which is perfect for undoing one bad DELETE.',
        'Restore with <code>UNDROP</code> for dropped objects, or clone the old version into a new table.',
    ])


def failsafe_anim():
    elems = [
        _title('Continuous Data Protection lifecycle'),
        sbox(20, 60, 200, 70, 'Current data', 'you query it', 'blue', step=1),
        sarrow(220, 95, 270, 95, 'gray', step=2),
        sbox(275, 60, 220, 70, 'Time Travel', '0–90 days · self-service\nAT / BEFORE / UNDROP', 'green', step=2, focus=2),
        sarrow(495, 95, 545, 95, 'gray', step=3),
        sbox(550, 60, 190, 70, 'Fail-safe', '7 days · only Snowflake\nSupport can recover', 'amber', step=3, focus=3),
        stext(380, 175, 'Permanent table: Time Travel (default 1 day) + 7 days Fail-safe', 'cyan', 12, step=4),
        stext(380, 197, 'Transient / temporary: max 1 day Time Travel, no Fail-safe', 'cyan', 12, step=4),
        stext(380, 230, 'storage for both periods is billed: churny staging tables → transient', 'red', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 250, *elems), [
        'Live data is what normal queries see.',
        'Changed or deleted data enters <strong>Time Travel</strong>, where you can query and restore it yourself for the retention period.',
        'After Time Travel expires, permanent-table data moves into <strong>Fail-safe</strong> for 7 more days. You cannot query it; only Snowflake Support can recover it after a disaster.',
        'Transient and temporary tables have at most one day of Time Travel and no Fail-safe.',
        'Both periods count toward storage cost, so frequently rewritten, re-creatable tables are cheaper as transient tables.',
    ])


def clone_anim():
    elems = [
        _title('Zero-copy clone'),
        sbox(40, 50, 200, 45, 'RESULTS', '', 'blue', step=1), sbox(520, 50, 200, 45, 'RESULTS_DEV (clone)', '', 'purple', step=1),
    ]
    for i in range(3):
        elems.append(_mp(220 + i * 110, 140, f'MP{i+1}', 'cyan', step=1, w=95))
        elems.append(sarrow(140, 95, 260 + i * 110, 138, 'blue', step=1))
        elems.append(sarrow(620, 95, 270 + i * 110, 138, 'purple', step=2))
    elems += [
        stext(380, 205, 'clone = new metadata pointing at the same micro-partitions: seconds, no extra storage', 'green', 12, step=2, bold=True),
        _mp(540, 225, 'MP2′', 'amber', step=3, w=95),
        stext(330, 250, 'UPDATE on the clone writes new MP2′ only for the clone', 'amber', 12, step=3),
        stext(380, 290, 'clone databases, schemas, tables · combine with AT(…) to clone the past', 'gray', 11, step=4),
    ]
    return anim(canvas(760, 305, *elems), [
        'A table is a list of micro-partitions recorded in metadata.',
        '<code>CREATE TABLE results_dev CLONE results</code> copies only the metadata. Both tables point at the same micro-partitions, so the clone is instant and uses no extra storage.',
        'When either table changes, new micro-partitions are written for that table only. You pay storage only for the changed data.',
        'You can clone whole databases or schemas (for a dev or test copy) and clone a past state with <code>AT</code> or <code>BEFORE</code>.',
    ])


def recovery_anim():
    elems = [
        _title('Undo an accidental DELETE'),
        sbox(20, 50, 220, 55, '10:42  DELETE FROM results;', 'forgot the WHERE!', 'red', step=1, size=12),
        sbox(270, 50, 220, 55, 'Find the query ID', 'QUERY_HISTORY / Snowsight', 'amber', step=2),
        sbox(520, 50, 220, 55, 'Clone the state before it', 'BEFORE(STATEMENT => id)', 'green', step=3, size=12),
        sarrow(240, 77, 268, 77, 'gray', step=2), sarrow(490, 77, 518, 77, 'gray', step=3),
        sbox(130, 140, 500, 55, 'ALTER TABLE results SWAP WITH results_restored;', 'atomic metadata swap: names exchange instantly', 'blue', step=4, focus=4, size=12),
        stext(380, 230, 'or INSERT the missing rows back from the old version', 'gray', 12, step=5),
        stext(380, 252, 'only works inside the retention period: check it is long enough', 'red', 12, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'A DELETE without a WHERE clause empties the table.',
        'Find the query ID of the bad statement in the query history.',
        'Create a clone of the table as it was just <strong>before</strong> that statement.',
        '<code>ALTER TABLE … SWAP WITH …</code> exchanges the two tables in one atomic metadata operation, so users see the restored table immediately.',
        'For partial damage you can instead re-insert only the affected rows. Everything depends on the retention period still covering the incident.',
    ])


def replication_anim():
    elems = [
        _title('Replication and failover across regions'),
        sbox(20, 60, 260, 150, 'Primary account', 'AWS ap-south-1 (Mumbai)\ndatabases, users, roles,\nwarehouses, integrations', 'blue', step=1),
        sflow(280, 135, 480, 135, 'cyan', step=2, count=3),
        stext(380, 120, 'scheduled refresh', 'cyan', 11, step=2),
        sbox(480, 60, 260, 150, 'Secondary account', 'Azure Central India (Pune)\nread-only replica', 'gray', step=2),
        sbox(480, 230, 260, 50, 'Promote to primary', 'Business Critical edition', 'red', step=3, focus=3, size=12),
        stext(160, 250, 'replication group / failover group', 'amber', 12, step=4, bold=True),
        stext(160, 270, 'client redirect: one connection URL', 'amber', 11, step=4),
    ]
    return anim(canvas(760, 295, *elems), [
        'Objects live in a primary account in one region.',
        'A <strong>replication group</strong> copies selected databases (and optionally users, roles, warehouses) to a secondary account in another region or even another cloud (here AWS Mumbai to Azure Pune) on a schedule. Only changed data is transferred.',
        'With a <strong>failover group</strong> (Business Critical edition) the secondary can be promoted to primary during an outage.',
        '<strong>Client Redirect</strong> gives applications a connection URL that can be pointed at whichever account is primary.',
    ])


# ================================================================== 7 Streams, tasks, dynamic tables, sharing
def stream_anim():
    elems = [
        _title('A stream records changes since it was last consumed'),
        sbox(20, 55, 190, 45, 'RAW_RESULTS', 'source table', 'blue', step=1),
        sbox(20, 125, 190, 70, 'DML', 'INSERT 2409\nUPDATE 2402 marks', 'gray', step=1),
        sarrow(210, 150, 255, 150, 'gray', step=2),
        _grid(260, 55, ['ROLL', 'MARKS', 'ACTION', 'ISUPDATE'], [
            ['2409', '81.00', 'INSERT', 'FALSE'], ['2402', '88.00', 'DELETE', 'TRUE'], ['2402', '90.00', 'INSERT', 'TRUE']],
            [70, 70, 90, 90], rh=28, step=2),
        stext(425, 50, 'STREAM raw_results_s', 'amber', 12, step=2, bold=True),
        sbox(600, 70, 140, 80, 'MERGE …', 'consumes it:\noffset moves on', 'green', step=3, focus=3),
        stext(380, 220, 'a stream stores an offset, not the data: changes come from table versions (Time Travel)', 'cyan', 12, step=4),
        stext(380, 245, 'standard · append-only · insert-only (external tables)', 'gray', 12, step=4),
    ]
    return anim(canvas(760, 265, *elems), [
        'Rows are inserted and updated in the source table.',
        'Selecting from the <strong>stream</strong> returns the net changes with metadata columns: <code>METADATA$ACTION</code> (INSERT/DELETE), <code>METADATA$ISUPDATE</code> and <code>METADATA$ROW_ID</code>. An update appears as a DELETE plus an INSERT pair.',
        'When a DML statement (such as MERGE) reads the stream inside a transaction that commits, the stream\'s offset advances and those changes are no longer returned.',
        'A stream holds no copy of the data: it is an offset into the table\'s version history. Types: standard, append-only and insert-only.',
    ])


def task_anim():
    elems = [
        _title('Tasks and task graphs'),
        sbox(20, 50, 210, 60, 'ROOT: load_raw', "SCHEDULE = 'USING CRON\n0 2 * * * Asia/Kolkata'", 'blue', step=1, size=12),
        sarrow(230, 80, 290, 60, 'gray', step=2), sarrow(230, 80, 290, 140, 'gray', step=2),
        sbox(295, 35, 200, 50, 'clean_results', 'AFTER load_raw', 'green', step=2),
        sbox(295, 115, 200, 50, 'clean_attendance', 'AFTER load_raw', 'green', step=2),
        sarrow(495, 60, 545, 95, 'gray', step=3), sarrow(495, 140, 545, 105, 'gray', step=3),
        sbox(550, 75, 190, 55, 'build_report', 'AFTER both', 'purple', step=3),
        stext(380, 200, "WHEN SYSTEM$STREAM_HAS_DATA('raw_s') → skip run when nothing changed", 'amber', 12, step=4, bold=True),
        stext(380, 225, 'WAREHOUSE = etl_wh  or omit it → serverless task', 'gray', 12, step=5),
        stext(380, 247, 'tasks are created SUSPENDED: ALTER TASK … RESUME', 'red', 12, step=5),
    ]
    return anim(canvas(760, 265, *elems), [
        'A <strong>task</strong> runs one SQL statement or stored procedure on a schedule (minutes or a CRON expression with a time zone).',
        'Child tasks declare <code>AFTER parent</code>, forming a <strong>task graph</strong> (DAG). Only the root task has a schedule.',
        'A task can wait for several predecessors, so the report is built only after both cleaning tasks succeed.',
        'A <code>WHEN</code> condition such as <code>SYSTEM$STREAM_HAS_DATA</code> skips the run when there are no new changes, avoiding needless compute.',
        'Tasks use a named warehouse or, if none is given, serverless compute. New tasks are suspended until you resume them.',
    ])


def dynamic_anim():
    elems = [
        _title('Three ways to keep a derived table fresh'),
        _grid(20, 55, ['', 'Streams + Tasks', 'Dynamic table', 'Materialized view'], [
            ['You write', 'MERGE logic + schedule', 'one SELECT', 'one SELECT'],
            ['Joins allowed', 'yes', 'yes', 'no (single table)'],
            ['Freshness', 'task schedule', 'TARGET_LAG', 'always current'],
            ['Refresh', 'your code', 'incremental or full', 'background'],
            ['Best for', 'custom logic, SCD', 'declarative pipelines', 'speeding up queries'],
        ], [140, 190, 190, 200], rh=30, step=1, size=11),
        sbox(170, 245, 420, 45, "CREATE DYNAMIC TABLE … TARGET_LAG = '10 minutes'", 'Snowflake works out the incremental refresh', 'green', step=2, focus=2, size=12),
    ]
    return anim(canvas(760, 305, *elems), [
        'Streams and tasks are imperative: you write the MERGE and the schedule. Dynamic tables are declarative: you write the query and how stale it may be. Materialized views are for accelerating queries on one table.',
        'A <strong>dynamic table</strong> refreshes automatically to stay within its <code>TARGET_LAG</code>, incrementally when the query allows it, and can be chained into a pipeline.',
    ])


def sharing_anim():
    elems = [
        _title('Secure Data Sharing: no copies, no files'),
        sbox(20, 50, 260, 160, 'Provider: C-DAC Mumbai', '', 'blue', step=1, fill_opacity=0.08, top=True),
        _cyl(60, 95, 180, 60, 'RESULTS', 'blue', step=1),
        stext(150, 185, 'SHARE results_share', 'amber', 12, step=2, bold=True),
        sflow(280, 130, 480, 130, 'green', step=3, count=3),
        stext(380, 115, 'metadata grant only', 'green', 11, step=3),
        sbox(480, 50, 260, 160, 'Consumer: university account', '', 'purple', step=3, fill_opacity=0.08, top=True),
        sbox(520, 100, 180, 50, 'read-only DB', 'uses OWN warehouse', 'purple', step=3),
        stext(380, 245, 'live: consumer sees updates instantly · provider pays storage, consumer pays compute', 'cyan', 12, step=4),
        stext(380, 268, 'no Snowflake account? → reader account (provider pays) · public: Marketplace', 'gray', 11, step=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'The provider owns the data in its own account.',
        'It creates a <strong>share</strong> and grants access to chosen databases, schemas, tables and secure views.',
        'The consumer creates a read-only database from the share. Nothing is copied: queries read the provider\'s micro-partitions directly.',
        'Changes are visible immediately. The provider pays for storage; the consumer pays for the warehouse it queries with. Cross-region sharing needs replication or listings with auto-fulfilment.',
        'A consumer without Snowflake can get a <strong>reader account</strong> managed (and paid for) by the provider. Public datasets are offered through the Snowflake Marketplace.',
    ])


def snowpark_anim():
    elems = [
        _title('Bring code to the data: Snowpark & UDFs'),
        sbox(20, 55, 230, 120, 'Your Python', "session.table('results')\n  .filter(col('marks') > 80)\n  .group_by('course')\n  .count()", 'gray', step=1, size=12),
        sarrow(250, 115, 300, 115, 'gray', step=2), stext(275, 105, 'lazy', 'gray', 10, step=2),
        sbox(305, 70, 170, 90, 'SQL generated', 'runs in a warehouse\nwhen .collect() /\n.show() is called', 'blue', step=2, focus=2),
        sbox(510, 40, 230, 60, 'UDF / UDTF', 'Python, Java, Scala, JS, SQL', 'green', step=3),
        sbox(510, 115, 230, 60, 'Stored procedure', 'control flow, DDL, loops', 'purple', step=3),
        stext(380, 215, 'data never leaves Snowflake; Snowpark-optimised warehouses for ML memory', 'amber', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 235, *elems), [
        'The <strong>Snowpark</strong> DataFrame API lets you write transformations in Python, Java or Scala.',
        'DataFrame operations are lazy: they are translated to SQL and run inside a Snowflake warehouse only when you call an action such as <code>collect()</code>.',
        'Custom logic can be registered as <strong>UDFs</strong> (per-row), <strong>UDTFs</strong> (return tables) or <strong>stored procedures</strong> (multi-statement logic).',
        'The code runs next to the data, so large datasets are not pulled to your laptop.',
    ])


# ================================================================== 8 Security, cost, scenarios
def rbac_anim():
    elems = [
        _title('Role hierarchy (privileges flow upward)'),
        sbox(300, 40, 160, 40, 'ACCOUNTADMIN', '', 'red', step=1),
        sbox(140, 105, 160, 40, 'SECURITYADMIN', '', 'amber', step=1), sbox(460, 105, 160, 40, 'SYSADMIN', '', 'blue', step=1),
        sbox(140, 170, 160, 40, 'USERADMIN', '', 'amber', step=1),
        sarrow(220, 105, 330, 82, 'gray', step=1), sarrow(540, 105, 430, 82, 'gray', step=1), sarrow(220, 170, 220, 147, 'gray', step=1),
        sbox(380, 170, 140, 40, 'BDA_ENGINEER', '', 'green', step=2), sbox(540, 170, 140, 40, 'BDA_ANALYST', '', 'green', step=2),
        sarrow(450, 170, 520, 147, 'gray', step=2), sarrow(610, 170, 560, 147, 'gray', step=2),
        stext(530, 235, 'custom roles granted to SYSADMIN', 'green', 11, step=2),
        stext(200, 250, 'GRANT SELECT ON ALL TABLES IN SCHEMA cdac.bda', 'cyan', 11, step=3),
        stext(200, 266, '  TO ROLE bda_analyst;', 'cyan', 11, step=3),
        stext(200, 282, 'GRANT ROLE bda_analyst TO USER riya;', 'cyan', 11, step=3),
        stext(560, 280, 'privileges → roles → users', 'amber', 13, step=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Snowflake ships with system roles. ACCOUNTADMIN sits on top; SECURITYADMIN and USERADMIN manage users and grants; SYSADMIN owns databases and warehouses.',
        'You create <strong>custom roles</strong> for job functions and grant them to SYSADMIN so administrators inherit their privileges.',
        'Privileges are granted to <strong>roles</strong>, and roles are granted to <strong>users</strong> (or to other roles).',
        'This is role-based access control (RBAC). A user acts through one primary role at a time, plus any secondary roles enabled for the session.',
    ])


def masking_anim():
    elems = [
        _title('Masking and row access policies'),
        _grid(30, 60, ['NAME', 'PHONE', 'CENTRE'], [['Anuj', '98200 12345', 'Kharghar'], ['Riya', '98330 54321', 'Kharghar'], ['Meera', '99870 11111', 'Juhu']],
              [90, 120, 100], rh=28, step=1),
        stext(185, 50, 'role HR_ADMIN sees', 'blue', 11, step=1),
        _grid(430, 60, ['NAME', 'PHONE', 'CENTRE'], [['Anuj', '*****12345', 'Kharghar'], ['Riya', '*****54321', 'Kharghar']],
              [90, 120, 100], rh=28, step=2),
        stext(585, 50, 'role KHARGHAR_COORD sees', 'purple', 11, step=2),
        sbox(40, 190, 320, 55, 'MASKING POLICY on PHONE', 'CASE WHEN role = HR_ADMIN THEN val ELSE mask', 'amber', step=3, size=12),
        sbox(400, 190, 320, 55, 'ROW ACCESS POLICY on table', 'centre must match the user\'s mapping', 'green', step=4, size=12),
        stext(380, 280, 'defined once, enforced on every query, view and share (Enterprise edition)', 'cyan', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'An HR administrator sees full phone numbers and every centre.',
        'A Kharghar coordinator sees masked phone numbers and only Kharghar rows, from the same table.',
        'A <strong>masking policy</strong> is a SQL function attached to a column. It decides at query time, based on the role, what value to return.',
        'A <strong>row access policy</strong> attached to the table decides which rows are visible, often using a mapping table.',
        'Policies are enforced everywhere the column is used. Tag-based masking can apply one policy to every column with a given tag.',
    ])


def cost_anim():
    elems = [
        _title('Controlling cost'),
        sbox(20, 50, 230, 70, 'Resource monitor', 'credit quota per month\nnotify 75% · suspend 100%', 'red', step=1, focus=1),
        sbox(265, 50, 230, 70, 'Right-size warehouses', 'separate per workload\nauto-suspend 60 s', 'blue', step=2),
        sbox(510, 50, 230, 70, 'Query timeouts', 'STATEMENT_TIMEOUT_IN_SECONDS\nstop runaway queries', 'amber', step=3),
        sbox(20, 140, 230, 70, 'Storage hygiene', 'transient staging tables\nshort retention on scratch', 'cyan', step=4),
        sbox(265, 140, 230, 70, 'Watch serverless', 'clustering, search opt.,\nMVs, pipes', 'purple', step=4),
        sbox(510, 140, 230, 70, 'Measure', 'ACCOUNT_USAGE views\nWAREHOUSE_METERING_HISTORY', 'green', step=5, focus=5),
        stext(380, 245, 'biggest lever: idle warehouses and oversized warehouses', 'amber', 13, step=5, bold=True),
    ]
    return anim(canvas(760, 265, *elems), [
        'A <strong>resource monitor</strong> sets a credit quota for warehouses or the whole account and can notify or suspend warehouses at thresholds.',
        'Give each workload its own correctly sized warehouse with short auto-suspend.',
        'Statement timeouts and queue timeouts stop runaway or forgotten queries.',
        'Use transient tables and short retention for data that can be rebuilt, and review serverless features you have turned on.',
        'Measure spending with <code>SNOWFLAKE.ACCOUNT_USAGE</code> views and Snowsight cost management before and after each change.',
    ])


def pipeline_anim():
    elems = [
        _title('C-DAC exam results pipeline on Snowflake'),
        sbox(10, 60, 125, 55, 'Exam portal', 'JSON files', 'gray', step=1),
        sflow(135, 87, 170, 87, 'cyan', step=1, count=2),
        sbox(170, 60, 125, 55, 'S3 stage', 'Snowpipe', 'amber', step=2),
        sflow(295, 87, 330, 87, 'cyan', step=2, count=2),
        sbox(330, 50, 130, 75, 'RAW', 'v VARIANT\n+ file, load_ts', 'blue', step=2),
        sflow(460, 87, 495, 87, 'cyan', step=3, count=2),
        sbox(495, 50, 125, 75, 'CLEAN', 'typed, deduped\nMERGE / DT', 'green', step=3, focus=3),
        sflow(620, 87, 650, 87, 'cyan', step=4, count=2),
        sbox(650, 50, 100, 75, 'MART', 'rank lists\ncentre stats', 'purple', step=4),
        sbox(170, 170, 420, 50, 'stream + task  OR  dynamic table (TARGET_LAG 5 min)', '', 'cyan', step=3, size=12),
        stext(380, 250, 'BI_WH (Small, multi-cluster) for dashboards · ETL_WH (Medium) for transforms', 'gray', 12, step=5),
        stext(380, 272, 'roles: BDA_ENGINEER writes RAW/CLEAN, BDA_ANALYST reads MART only', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'The exam portal writes one JSON file per submitted paper.',
        'Files land in an S3 stage and Snowpipe loads them into a <strong>RAW</strong> table that keeps the whole payload in a VARIANT column plus load metadata.',
        'A stream plus task (or a dynamic table) turns raw JSON into a typed, deduplicated <strong>CLEAN</strong> table with MERGE.',
        'The <strong>MART</strong> layer holds reporting tables: rank lists, centre-wise statistics, pass percentages.',
        'Separate warehouses and roles keep loading, transforming and reporting isolated and secure.',
    ])


def compare_anim():
    elems = [
        _title('Snowflake vs other cloud warehouses'),
        _grid(20, 50, ['', 'Snowflake', 'Redshift', 'BigQuery', 'Databricks SQL'], [
            ['Clouds', 'AWS, Azure, GCP', 'AWS', 'GCP (+Omni)', 'AWS, Azure, GCP'],
            ['Compute', 'warehouses', 'clusters / serverless', 'serverless slots', 'SQL warehouses'],
            ['Storage', 'own format (+Iceberg)', 'own (+Spectrum)', 'own (+BigLake)', 'Delta Lake files'],
            ['Pricing', 'credits / second', 'node-hours / RPU', 'per TB or slots', 'DBU'],
            ['Tuning', 'cluster keys', 'dist + sort keys', 'partition + cluster', 'Z-order / liquid'],
        ], [110, 150, 160, 150, 150], rh=32, step=1, size=11),
        stext(380, 260, 'the right choice depends on cloud, team skills, workloads and cost model', 'amber', 12, step=2, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'All four separate storage from compute to some degree. They differ in which clouds they run on, how compute is provisioned and billed, and which physical-design knobs you tune.',
        'In interviews, compare on facts (cloud, pricing, concurrency, ecosystem) rather than declaring one the winner.',
    ])


# ------------------------------------------------------------------ export list
__all__ = [n for n in dir() if n.endswith('_anim')] + ['_cyl', '_grid', '_mp', '_title']
