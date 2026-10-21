from build import *
from build import _attrs, _t


# ------------------------------------------------------------------ helpers
def _node(x, y, label, color='blue', step=None, focus=None, r=22, size=11, sub=None):
    c = PALETTE.get(color, color)
    s = (f'<g{_attrs(step, focus)} class="sbox"><circle cx="{x}" cy="{y}" r="{r}" fill="#1e293b"/>'
         f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="2"/>'
         f'<text x="{x}" y="{y + 4}" font-size="{size}" fill="#f1f5f9" text-anchor="middle" font-weight="bold">{_t(label)}</text>')
    if sub:
        s += f'<text x="{x}" y="{y + r + 14}" font-size="10" fill="#cbd5e1" text-anchor="middle">{_t(sub)}</text>'
    return s + '</g>'


def _rows(x, y, w, rows, color='#162033', step=None, rh=24, size=11, focus_rows=None, kw=None, key_color=None):
    """Sorted key/value rows: rows = [(key, value), ...]."""
    out = []
    kw = kw or 90
    for i, (k, v) in enumerate(rows):
        f = (focus_rows or {}).get(i)
        g = (scell(x, y + i * rh, kw, rh, k, key_color or '#334155', '#fff', bold=True, size=size)
             + scell(x + kw, y + i * rh, w - kw, rh, v, color if i % 2 == 0 else '#0f172a', size=size))
        out.append(f'<g{_attrs(step, f)}>{g}</g>')
    return ''.join(out)


def _region(x, y, w, h, title, rng, color='green', step=None, focus=None):
    return (sbox(x, y, w, h, '', '', color, step=step, focus=focus, fill_opacity=0.08)
            + stext(x + w / 2, y + 18, title, color, 12, step=step, bold=True)
            + stext(x + w / 2, y + 34, rng, '#cbd5e1', 10, step=step))


# ================================================================== 1 Foundations
def what_is_hbase_anim():
    elems = [
        stext(380, 24, 'HBase = random, real-time access on top of HDFS', 'blue', 15, bold=True),
        sbox(20, 50, 330, 95, 'HDFS alone', 'huge files, write-once, sequential scans\nno "update row 2401"', 'gray', step=1, size=13),
        sbox(410, 50, 330, 95, 'HBase', 'get / put a single row in milliseconds\nbillions of rows × millions of columns', 'green', step=2, focus=2, size=13),
        sarrow(350, 97, 408, 97, 'green', step=2),
        sbox(20, 170, 220, 50, 'Sorted by row key', '', 'blue', step=3, size=12),
        sbox(270, 170, 220, 50, 'Strongly consistent', 'per row', 'purple', step=3, size=12),
        sbox(520, 170, 220, 50, 'Scales by regions', 'auto-sharded', 'amber', step=3, size=12),
        sbox(20, 240, 720, 40, 'Data stored as HFiles on HDFS  ·  coordinated by ZooKeeper  ·  modelled on Google Bigtable', '', 'cyan', step=4, size=12),
    ]
    return anim(canvas(760, 295, *elems), [
        'HDFS is excellent for storing huge files and scanning them in batch, but it cannot update or fetch one small record quickly.',
        '<strong>HBase</strong> adds a database layer on top: you can read or write any single row by its key in milliseconds, even in tables with billions of rows.',
        'Rows are kept <strong>sorted by row key</strong>, every row operation is <strong>strongly consistent</strong>, and tables split automatically into <strong>regions</strong> spread over many servers.',
        'Underneath, data is stored in HFiles on HDFS and the cluster is coordinated by ZooKeeper. The design follows Google\'s Bigtable paper (2006).',
    ])


def rdbms_vs_hbase_anim():
    elems = [
        stext(380, 24, 'Fixed columns vs sparse column families', 'blue', 15, bold=True),
        sbox(20, 50, 340, 200, '', '', 'gray', step=1, fill_opacity=0.06), stext(190, 70, 'RDBMS: every row has every column', 'gray', 12, step=1, bold=True),
        stable(40, 85, ['roll', 'name', 'phone', 'github'], [['2401', 'Anuj', 'NULL', 'NULL'], ['2402', 'Aarshvi', '98…', 'NULL']], [55, 80, 75, 85], step=1, title_color='gray'),
        stext(190, 190, 'schema change = ALTER TABLE', 'gray', 11, step=2), stext(190, 208, 'NULLs still take space', 'gray', 11, step=2),
        sbox(400, 50, 340, 200, '', '', 'green', step=3, fill_opacity=0.08), stext(570, 70, 'HBase: only the cells you write', 'green', 12, step=3, bold=True),
        _rows(415, 85, 310, [('2401', 'info:name=Anuj'), ('2402', 'info:name=Aarshvi  info:phone=98…'), ('2403', 'info:name=Riya  links:github=…')], step=3, kw=60, key_color='#059669'),
        stext(570, 185, 'new qualifier = just put it', 'green', 11, step=4, focus=4, bold=True),
        stext(570, 203, 'no NULLs stored', 'green', 11, step=4),
        stext(380, 280, 'trade-off: no joins, no SQL, no secondary indexes (out of the box)', 'amber', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'In a relational table every row has the same columns, and missing values are stored as NULL.',
        'Adding a column means an ALTER TABLE for the whole table.',
        'In HBase only the <strong>column family</strong> is declared. Each row stores only the cells that were actually written.',
        'A new column qualifier can be added at any time just by writing it. Sparse data costs nothing.',
        'The trade-off: no SQL, no joins, no secondary indexes and no multi-row transactions out of the box (Apache Phoenix adds SQL on top).',
    ])


def when_hbase_anim():
    elems = [
        stext(380, 24, 'HDFS vs Hive vs HBase: which one?', 'blue', 15, bold=True),
        sbox(20, 55, 230, 175, '', '', 'gray', step=1, fill_opacity=0.08), stext(135, 75, 'HDFS', 'gray', 13, step=1, bold=True),
        stext(135, 100, 'file system', '#e2e8f0', 11, step=1), stext(135, 120, 'write once, read many', '#e2e8f0', 11, step=1),
        stext(135, 140, 'full-file scans', '#e2e8f0', 11, step=1), stext(135, 175, 'raw / landing data', 'gray', 11, step=1, bold=True),
        sbox(265, 55, 230, 175, '', '', 'amber', step=2, fill_opacity=0.08), stext(380, 75, 'Hive', 'amber', 13, step=2, bold=True),
        stext(380, 100, 'SQL over files', '#e2e8f0', 11, step=2), stext(380, 120, 'batch analytics', '#e2e8f0', 11, step=2),
        stext(380, 140, 'seconds to minutes', '#e2e8f0', 11, step=2), stext(380, 175, 'reports, aggregations', 'amber', 11, step=2, bold=True),
        sbox(510, 55, 230, 175, '', '', 'green', step=3, fill_opacity=0.08), stext(625, 75, 'HBase', 'green', 13, step=3, bold=True),
        stext(625, 100, 'key-value / wide-column', '#e2e8f0', 11, step=3), stext(625, 120, 'random get / put', '#e2e8f0', 11, step=3),
        stext(625, 140, 'milliseconds', '#e2e8f0', 11, step=3), stext(625, 175, 'serving, lookups, updates', 'green', 11, step=3, bold=True),
        stext(380, 265, 'often together: HBase serves live data, Hive/Spark analyse it in batch', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        '<strong>HDFS</strong> is a distributed file system: ideal for huge files written once and scanned in full.',
        '<strong>Hive</strong> puts SQL tables on those files for batch analytics; queries take seconds to minutes.',
        '<strong>HBase</strong> is a database for random, real-time reads and writes of individual rows by key.',
        'They complement each other: HBase serves the live application, while Hive or Spark analyse the same data in bulk.',
    ])


def data_model_anim():
    elems = [
        stext(380, 24, '(row key, family:qualifier, timestamp) → value', 'blue', 15, bold=True),
        scell(30, 55, 100, 30, 'row key', '#10b981', '#fff', step=1, focus=1, bold=True),
        scell(135, 55, 290, 30, 'family: info', '#0ea5e9', '#fff', step=2, focus=2, bold=True),
        scell(430, 55, 300, 30, 'family: marks', '#8b5cf6', '#fff', step=2, focus=2, bold=True),
        scell(135, 90, 145, 26, 'name', '#1e40af', '#fff', step=3, size=11), scell(280, 90, 145, 26, 'city', '#1e40af', '#fff', step=3, size=11),
        scell(430, 90, 150, 26, 'sql', '#6d28d9', '#fff', step=3, size=11), scell(580, 90, 150, 26, 'spark', '#6d28d9', '#fff', step=3, size=11),
        scell(30, 121, 100, 40, '2401', '#334155', step=1, bold=True), scell(135, 121, 145, 40, 'Anuj', '#162033', step=3),
        scell(280, 121, 145, 40, 'Mumbai @t2', '#162033', step=4, focus=4, size=11), scell(430, 121, 150, 40, '78', '#162033', step=3),
        scell(580, 121, 150, 40, '', '#0f172a', step=3),
        scell(30, 166, 100, 40, '2402', '#334155', step=1, bold=True), scell(135, 166, 145, 40, 'Aarshvi', '#162033', step=3),
        scell(280, 166, 145, 40, '', '#0f172a', step=3), scell(430, 166, 150, 40, '', '#0f172a', step=3), scell(580, 166, 150, 40, '88', '#162033', step=3),
        stext(352, 222, 'older version: Pune @t1', 'amber', 11, step=4, focus=4),
        stext(380, 255, 'a sorted, sparse, multi-dimensional, persistent map', 'cyan', 13, step=5, focus=5, bold=True),
        stext(380, 278, 'SortedMap<RowKey, SortedMap<Family, SortedMap<Qualifier, SortedMap<Timestamp, Value>>>>', '#94a3b8', 10, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'A <strong>row key</strong> identifies each row. Rows are stored sorted by this key, as raw bytes.',
        'Columns are grouped into <strong>column families</strong> (info, marks), which are declared when the table is created and stored separately on disk.',
        'Inside a family, <strong>column qualifiers</strong> (name, city, sql…) are created freely at write time. Empty cells are simply not stored.',
        'Each cell can keep several <strong>versions</strong>, identified by timestamp. A read returns the newest version by default.',
        'So HBase is a sorted, sparse, multidimensional map: row → family → qualifier → timestamp → value. Everything is bytes.',
    ])


def cp_anim():
    elems = [
        stext(380, 24, 'HBase is CP: one RegionServer owns each row', 'blue', 15, bold=True),
        _region(30, 55, 300, 100, 'Region A on RS1', "rows '' … '2410'", 'green', step=1),
        _region(430, 55, 300, 100, 'Region B on RS2', "rows '2410' … ''", 'blue', step=1),
        stext(180, 115, 'all reads & writes of 2401', 'green', 11, step=2), stext(180, 131, 'go to RS1 only', 'green', 11, step=2, bold=True),
        sbox(30, 175, 300, 45, 'row-level atomic: put of many', 'columns of one row = all or nothing', 'purple', step=3, size=12),
        sbox(430, 175, 300, 45, 'RS1 crashes → region offline', 'until reassigned (seconds to minutes)', 'red', step=4, focus=4, size=12),
        stext(380, 255, 'consistency first: never two versions of the truth, but brief unavailability on failure', 'amber', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 275, *elems), [
        'A table is split into regions; each region is served by exactly <strong>one RegionServer</strong> at a time.',
        'So every read and write of a given row goes through the same server, which always has the latest value: <strong>strong consistency</strong>.',
        'Operations on a single row are <strong>atomic</strong>, even across column families: a reader never sees half a put. There are no multi-row transactions.',
        'If that RegionServer fails, its regions are unavailable until the HMaster reassigns them and the WAL is replayed.',
        'This is the CP choice in CAP: consistency over availability, the opposite trade-off to Cassandra.',
    ])


# ================================================================== 2 Shell & data operations
def ddl_anim():
    elems = [
        stext(380, 24, 'Table lifecycle in the HBase shell', 'blue', 15, bold=True),
        sbox(20, 60, 130, 45, 'create_namespace', '', 'gray', step=1, size=11),
        sbox(170, 60, 130, 45, 'create', 'table + families', 'green', step=1, size=11),
        sbox(320, 60, 130, 45, 'alter', 'add/modify family', 'blue', step=2, size=11),
        sbox(470, 60, 130, 45, 'disable', '', 'amber', step=3, focus=3, size=11),
        sbox(620, 60, 120, 45, 'drop', '', 'red', step=3, size=11),
        sarrow(150, 82, 168, 82, 'gray', step=1), sarrow(300, 82, 318, 82, 'gray', step=2),
        sarrow(450, 82, 468, 82, 'gray', step=3), sarrow(600, 82, 618, 82, 'gray', step=3),
        stext(380, 140, "namespace:table  e.g. 'cdac:students'  (default namespace if omitted)", 'cyan', 12, step=1),
        stext(380, 175, 'families are schema; qualifiers are not', 'green', 12, step=2, bold=True),
        stext(380, 210, 'a table must be disabled before drop (and before some alters in old versions)', 'amber', 12, step=3, focus=3),
        stext(380, 245, 'list · describe · exists · is_enabled · truncate · count', '#cbd5e1', 12, step=4),
    ]
    return anim(canvas(760, 265, *elems), [
        'A <strong>namespace</strong> groups tables (like a database or schema). <code>default</code> and the system namespace <code>hbase</code> always exist. Then <code>create</code> defines a table and its column families.',
        '<code>alter</code> adds, changes or removes column families and their settings (VERSIONS, TTL, compression). Qualifiers never need DDL.',
        'Dropping is a two-step safety mechanism: <code>disable</code> takes all regions offline, then <code>drop</code> deletes the table.',
        'Other everyday commands: <code>list</code>, <code>describe</code>, <code>exists</code>, <code>is_enabled</code>, <code>truncate</code> (disable + drop + recreate) and <code>count</code>.',
    ])


def crud_anim():
    elems = [
        stext(380, 24, 'put · get · scan · delete', 'blue', 15, bold=True),
        sbox(20, 55, 170, 45, "put t, row, 'cf:q', v", '', 'green', step=1, size=11),
        sbox(20, 115, 170, 45, 'get t, row', '', 'blue', step=2, size=11),
        sbox(20, 175, 170, 45, 'scan t, {…}', '', 'purple', step=3, size=11),
        sbox(20, 235, 170, 45, 'delete / deleteall', '', 'red', step=4, size=11),
        _rows(260, 70, 470, [('2401', 'info:city=Mumbai  info:name=Anuj  marks:sql=78'), ('2402', 'info:city=Mumbai  info:name=Aarshvi'),
                             ('2403', 'info:name=Riya')], step=1, kw=70, key_color='#059669', focus_rows={0: 2}),
        sarrow(190, 137, 258, 92, 'blue', step=2),
        '<g data-step="3"><rect x="256" y="66" width="478" height="76" fill="none" stroke="#8b5cf6" stroke-width="3" rx="4"/></g>',
        stext(495, 165, 'scan: a range of rows in key order', 'purple', 11, step=3),
        stext(495, 200, 'put = insert OR update (new version)', 'green', 12, step=1, bold=True),
        stext(495, 230, 'delete writes a marker, data removed later', 'red', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 295, *elems), [
        '<code>put</code> writes one cell. There is no difference between insert and update: writing again simply creates a newer version.',
        '<code>get</code> reads one row by its key (optionally only some columns or versions). This is the fastest operation.',
        '<code>scan</code> reads a contiguous range of rows in row-key order, optionally filtered.',
        '<code>delete</code> removes a column, and <code>deleteall</code> a whole row. Both write delete markers; the data is physically removed at major compaction.',
    ])


def versions_anim():
    elems = [
        stext(380, 24, "Cell versions: info:city of row 2401 (VERSIONS => 3)", 'blue', 15, bold=True),
        scell(60, 60, 200, 34, 't3  10:00:00.009', '#10b981', '#fff', step=3, focus=3, size=11), scell(260, 60, 200, 34, 'Thane', '#162033', step=3),
        scell(60, 94, 200, 34, 't2  10:00:00.007', '#0ea5e9', '#fff', step=2, size=11), scell(260, 94, 200, 34, 'Mumbai', '#0f172a', step=2),
        scell(60, 128, 200, 34, 't1  10:00:00.002', '#475569', '#fff', step=1, size=11), scell(260, 128, 200, 34, 'Pune', '#162033', step=1),
        stext(560, 80, 'get → newest only', 'green', 12, step=3, bold=True),
        stext(560, 112, 'VERSIONS => 3 → all three', 'blue', 12, step=4),
        stext(560, 144, 'TIMERANGE → as of a time', 'purple', 12, step=4),
        stext(380, 200, 'a 4th put pushes the oldest version out (removed at compaction)', 'amber', 12, step=5, focus=5, bold=True),
        stext(380, 228, 'timestamps: server time by default, or set explicitly by the client', '#cbd5e1', 11, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Each put creates a new <strong>version</strong> of the cell, stamped with a timestamp (milliseconds).',
        'Versions are stored newest first.',
        'A normal <code>get</code> or <code>scan</code> returns only the latest version.',
        'Ask for more with <code>VERSIONS => n</code> (up to the family\'s VERSIONS setting), or read the value as of a past moment with <code>TIMERANGE</code> / <code>TIMESTAMP</code>.',
        'The family\'s <code>VERSIONS</code> setting (default 1) limits how many versions are kept; extra old versions are hidden immediately and removed at compaction.',
    ])


def scan_order_anim():
    elems = [
        stext(380, 24, 'Row keys sort as BYTES, not as numbers', 'blue', 15, bold=True),
        _rows(40, 60, 250, [('1', ''), ('10', ''), ('100', ''), ('2', ''), ('25', ''), ('9', '')], step=1, kw=250, key_color='#334155'),
        stext(165, 220, 'lexicographic: "10" < "2" < "9"', 'red', 12, step=2, focus=2, bold=True),
        _rows(430, 60, 250, [('001', ''), ('002', ''), ('009', ''), ('010', ''), ('025', ''), ('100', '')], step=3, kw=250, key_color='#059669'),
        stext(555, 220, 'zero-padded: order = numeric order', 'green', 12, step=3, bold=True),
        stext(380, 255, "STARTROW inclusive · STOPROW exclusive · ROWPREFIXFILTER · REVERSED", 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 275, *elems), [
        'HBase compares row keys byte by byte. Numbers stored as text therefore sort like dictionary words.',
        '"10" comes before "2", and "100" before "25". Range scans on such keys return surprising results.',
        'Fixed-width keys (zero-padded text, or binary big-endian numbers) make byte order equal numeric order.',
        'Scans select a contiguous key range: <code>STARTROW</code> is inclusive, <code>STOPROW</code> exclusive; <code>ROWPREFIXFILTER</code> sets both from a prefix; <code>REVERSED</code> scans backwards.',
    ])


def counter_anim():
    elems = [
        stext(380, 24, 'incr: atomic counters inside a row', 'blue', 15, bold=True),
        sbox(30, 55, 200, 40, "incr …, 'stats:views', 1", '', 'green', step=1, size=11),
        sbox(30, 105, 200, 40, "incr …, 'stats:views', 1", '', 'green', step=1, size=11),
        sbox(30, 155, 200, 40, "incr …, 'stats:views', 5", '', 'green', step=1, size=11),
        sarrow(230, 75, 330, 120, 'green', step=2), sarrow(230, 125, 330, 125, 'green', step=2), sarrow(230, 175, 330, 130, 'green', step=2),
        sbox(330, 95, 180, 60, 'RegionServer', 'row lock → read → +n → write', 'purple', step=2, focus=2, size=11),
        sarrow(510, 125, 560, 125, 'green', step=3),
        sbox(560, 100, 180, 50, 'views = 7', '', 'green', step=3, size=13),
        stext(380, 230, "stored as an 8-byte long: \\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x07", 'amber', 12, step=4, focus=4, bold=True),
        stext(380, 255, 'read it with get_counter; a normal put of "7" is text, not a counter', '#cbd5e1', 11, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'Many clients increment the same counter cell concurrently.',
        'The RegionServer serialises increments on the row (row lock), so each one reads the current value, adds, and writes atomically. None are lost.',
        'The result is exact, because one server owns the row (unlike Cassandra\'s distributed counters).',
        'Counters are stored as 8-byte big-endian longs, so the shell shows them as \\x bytes; use <code>get_counter</code> to read them as a number.',
    ])


# ================================================================== 3 Filters
def filter_anim():
    elems = [
        stext(380, 24, 'Filters run on the RegionServer, inside the scan', 'blue', 15, bold=True),
        sbox(20, 55, 140, 45, 'Client', "scan + FILTER", 'gray', step=1, size=12),
        sarrow(160, 77, 218, 77, 'gray', step=1),
        sbox(220, 45, 330, 160, '', '', 'purple', step=2, fill_opacity=0.08),
        stext(385, 65, 'RegionServer', 'purple', 12, step=2, bold=True),
        _rows(235, 75, 300, [('2401', 'city=Mumbai'), ('2402', 'city=Mumbai'), ('2403', 'city=Pune'), ('2404', 'city=Delhi')], step=2, kw=70,
              focus_rows={0: 3, 1: 3}),
        stext(385, 190, "ValueFilter(=,'binary:Mumbai')", 'amber', 11, step=3, bold=True),
        sarrow(550, 120, 598, 120, 'green', step=4),
        sbox(600, 95, 140, 50, '2 rows', 'over the network', 'green', step=4, size=12),
        stext(380, 240, 'saves network transfer, NOT disk reads: every row in the range is still read', 'red', 12, step=5, focus=5, bold=True),
        stext(380, 265, 'narrow the range first (STARTROW/STOPROW, prefix), then filter', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'The client sends a scan with a <strong>filter</strong>, written in the Filter Language as a string in the shell.',
        'The RegionServer reads the rows of the requested range from MemStore and HFiles.',
        'It evaluates the filter for each row and cell (here: value equals Mumbai).',
        'Only matching cells travel back to the client.',
        'Filters reduce network traffic but not the amount of data read; a filter on a full-table scan is still a full-table scan. Restrict the key range first.',
    ])


def scvf_anim():
    elems = [
        stext(380, 24, "SingleColumnValueFilter('info','city',=,'binary:Mumbai')", 'blue', 14, bold=True),
        _rows(30, 55, 330, [('10', 'info:name=Old  (no city!)'), ('2401', 'info:city=Mumbai'), ('2402', 'info:city=Mumbai'), ('2403', 'info:city=Pune')],
              step=1, kw=60, focus_rows={0: 2}),
        stext(195, 170, 'default filterIfMissing = false', 'red', 12, step=2, bold=True),
        stext(195, 190, '→ row 10 is RETURNED', 'red', 12, step=2, focus=2),
        sbox(400, 55, 340, 60, "…,'binary:Mumbai', true, true)", 'filterIfMissing, latestVersionOnly', 'green', step=3, size=12),
        stext(570, 140, '→ only 2401 and 2402', 'green', 12, step=3, focus=3, bold=True),
        stext(380, 235, 'latestVersionOnly = true: older versions of city are ignored', 'amber', 12, step=4),
        stext(380, 260, 'whole row returned (unless SingleColumnValueExcludeFilter)', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 275, *elems), [
        'A SingleColumnValueFilter keeps rows where one particular column has a matching value. Row 10 has no city column at all.',
        'Surprise: with the default <code>filterIfMissing = false</code>, rows that do not have the column are <strong>included</strong>.',
        'Pass <code>true</code> as the 5th argument (filterIfMissing) to drop rows without the column. The 6th argument, latestVersionOnly, should normally stay true.',
        'With latestVersionOnly only the newest version of the column is tested. The filter returns the whole row; SingleColumnValueExcludeFilter drops the tested column.',
    ])


def column_filter_anim():
    elems = [
        stext(380, 24, 'Wide rows: filter the COLUMNS of a row', 'blue', 15, bold=True),
        scell(20, 60, 90, 40, '2401', '#10b981', '#fff', step=1, bold=True),
    ]
    quals = ['att:2026-10-01', 'att:2026-10-02', 'att:2026-10-03', 'att:2026-11-01', 'att:2026-11-02', 'info:name']
    for i, q in enumerate(quals):
        foc = 2 if i < 3 else None
        elems.append(scell(115 + i * 105, 60, 105, 40, q, '#0369a1' if q.startswith('att') else '#6d28d9', '#fff', step=1, focus=foc, size=10))
    elems += [
        stext(380, 135, "ColumnPrefixFilter('2026-10')  → October columns only", 'blue', 12, step=2, bold=True),
        stext(380, 165, "QualifierFilter(>=,'binary:2026-11')  → from November", 'purple', 12, step=3),
        stext(380, 195, "FamilyFilter(=,'binary:info')  → one family", 'green', 12, step=3),
        stext(380, 225, 'ColumnPaginationFilter(2, 0)  → first 2 columns, then (2, 2)…', 'amber', 12, step=4, focus=4),
        stext(380, 260, 'COLUMNS => [...] picks exact columns without a filter', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 275, *elems), [
        'In a "wide" design one row can hold thousands of columns, e.g. one attendance column per day.',
        '<code>ColumnPrefixFilter</code> keeps qualifiers that start with a prefix, e.g. one month of attendance.',
        '<code>QualifierFilter</code> and <code>FamilyFilter</code> compare qualifier or family names with a comparator.',
        '<code>ColumnPaginationFilter(limit, offset)</code> pages through the columns of very wide rows. To fetch known columns, simply list them in <code>COLUMNS</code>.',
    ])


def keyonly_anim():
    elems = [
        stext(380, 24, 'Cheap scans: keys only, first cell only, pages', 'blue', 15, bold=True),
        _rows(20, 60, 330, [('u1', 'cf:a=1  cf:b=2  cf:c=…'), ('u2', 'cf:a=3'), ('u3', 'cf:c=x  cf:d=…')], step=1, kw=60),
        sbox(400, 50, 340, 50, 'FirstKeyOnlyFilter()', 'only the first cell of each row', 'blue', step=2, size=12),
        sbox(400, 110, 340, 50, 'KeyOnlyFilter()', 'cells without values (empty value)', 'purple', step=2, size=12),
        stext(570, 185, 'together: the fastest way to list / count row keys', 'green', 11, step=2, bold=True),
        sbox(20, 160, 330, 50, 'PageFilter(2)', 'at most 2 rows … per REGION', 'amber', step=3, focus=3, size=12),
        stext(185, 235, 'client must still stop at 2 and remember the last key', 'amber', 11, step=3),
        stext(380, 265, 'next page: STARTROW => last_key + "\\x00"', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'Some tasks need row keys only, e.g. counting rows or listing IDs. Transferring every cell would waste bandwidth.',
        '<code>FirstKeyOnlyFilter</code> returns just the first cell of each row, and <code>KeyOnlyFilter</code> strips the values. The shell\'s <code>count</code> command uses this technique.',
        '<code>PageFilter(n)</code> limits rows, but it is evaluated independently in each region, so a scan over several regions can return more than n rows.',
        'For pagination, remember the last row key of a page and start the next scan just after it (append a zero byte).',
    ])


def comparator_anim():
    elems = [
        stext(380, 24, 'Comparators decide HOW values are compared', 'blue', 15, bold=True),
        stable(30, 50, ['comparator', 'example', 'matches'], [
            ['binary', "'binary:Pune'", 'exact bytes / byte order'],
            ['binaryprefix', "'binaryprefix:Nav'", 'starts with'],
            ['substring', "'substring:mum'", 'contains (case-insensitive)'],
            ['regexstring', "'regexstring:^24[0-9]{2}$'", 'regular expression'],
        ], [150, 260, 290], step=1, title_color='blue'),
        sbox(30, 195, 700, 40, "ValueFilter(>,'binary:80') on '9' and '100':  '9' > '80' ✓   '100' > '80' ✗", '', 'red', step=2, focus=2, size=12),
        stext(380, 260, 'store numbers as fixed-width or binary (Bytes.toBytes(int)) to compare them correctly', 'green', 12, step=3, focus=3, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'Filter comparisons use a <strong>comparator</strong>: binary (byte order), binaryprefix, substring or regexstring, combined with =, !=, &lt;, &lt;=, &gt;, &gt;=.',
        'binary comparison is byte-by-byte. Numbers stored as text compare like words: "9" is greater than "80", but "100" is not.',
        'Store numbers with a fixed width or as binary (Java <code>Bytes.toBytes</code>) so that byte order equals numeric order.',
    ])


# ================================================================== 4 Row key design
def rowkey_principles_anim():
    elems = [
        stext(380, 24, 'The row key is the only index HBase has', 'blue', 15, bold=True),
        sbox(20, 55, 230, 70, 'Access by key', 'get = one region, ms', 'green', step=1, size=12),
        sbox(265, 55, 230, 70, 'Range scans', 'contiguous keys = cheap', 'blue', step=2, size=12),
        sbox(510, 55, 230, 70, 'Anything else', 'full scan or extra table', 'red', step=3, size=12),
        stext(380, 155, 'Design rules', 'amber', 13, step=4, bold=True),
        stext(60, 180, '1. put what you query by at the START of the key', '#e2e8f0', 12, 'start', step=4),
        stext(60, 200, '2. spread writes across regions (avoid monotonic keys)', '#e2e8f0', 12, 'start', step=4),
        stext(60, 220, '3. keep keys short (stored in EVERY cell)', '#e2e8f0', 12, 'start', step=4),
        stext(60, 240, '4. fixed-width fields + separators so prefixes work', '#e2e8f0', 12, 'start', step=4),
        stext(60, 260, '5. row keys are immutable: changing one = delete + put', '#e2e8f0', 12, 'start', step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'A get by row key goes straight to one region and is answered in milliseconds.',
        'Because rows are sorted by key, rows with a common key prefix are stored next to each other, so a range scan reads them together.',
        'HBase has no other index. A query by any other field must scan the table or use a second table / Phoenix index.',
        'Hence the rules: lead with the query field, avoid hotspots, keep keys short (the key is repeated in every cell on disk), use fixed-width parts, and remember a key cannot be updated.',
    ])


def hotspot_anim():
    elems = [
        stext(380, 24, 'Monotonic keys → one hot region; salting spreads them', 'blue', 15, bold=True),
        _region(20, 50, 160, 70, 'Region 1', "'' … '20261'", 'gray', step=1),
        _region(195, 50, 160, 70, 'Region 2', "'20261' … ''", 'red', step=1, focus=1),
        stext(190, 140, 'key = timestamp → ALL new writes hit the last region', 'red', 11, step=1, bold=True),
        sbox(400, 50, 340, 70, "key = salt + '|' + timestamp", "salt = hash(id) % 4  →  '0|…', '1|…', '2|…', '3|…'", 'green', step=2, size=12),
    ]
    for i in range(4):
        elems.append(_region(400 + i * 87, 140, 80, 60, f'R{i}', f"'{i}|' …", 'green', step=3))
    elems += [
        stext(570, 222, 'writes spread over 4 regions / servers', 'green', 11, step=3, bold=True),
        stext(380, 255, 'cost: a time-range read must run 4 scans (one per salt) and merge', 'amber', 12, step=4, focus=4, bold=True),
        stext(380, 278, 'alternatives: hash the key (no range scans) or reverse it (e.g. reversed phone/domain)', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'With a timestamp (or sequence number) as the key, every new row sorts after the previous one, so all writes go to the <strong>last region</strong>: one RegionServer does all the work (a hotspot).',
        '<strong>Salting</strong> prefixes the key with a small bucket number computed from the data, e.g. hash(id) % 4.',
        'Consecutive writes now land in 4 different key ranges, i.e. different regions on different servers.',
        'The price is on reads: a time-range query must scan each salt bucket and merge the results.',
        'Other options: <strong>hashing</strong> the whole key (spreads perfectly but kills range scans) or <strong>reversing</strong> a field whose end varies most (phone numbers, domain names).',
    ])


def reverse_ts_anim():
    elems = [
        stext(380, 24, 'Latest first: Long.MAX_VALUE - timestamp in the key', 'blue', 15, bold=True),
        _rows(30, 55, 330, [('S01|1791952200000', '10:00'), ('S01|1791952500000', '10:05'), ('S01|1791952800000', '10:10')], step=1, kw=200),
        stext(195, 140, 'normal timestamp: oldest first', 'gray', 11, step=1),
        _rows(400, 55, 340, [('S01|9223370244901975807', '10:10'), ('S01|9223370244902275807', '10:05'), ('S01|9223370244902575807', '10:00')],
              step=2, kw=230, key_color='#059669', focus_rows={0: 2}),
        stext(570, 140, 'reversed: newest row comes first', 'green', 11, step=2, bold=True),
        stext(380, 190, "scan ROWPREFIXFILTER => 'S01|', LIMIT => 1  → latest reading", 'green', 12, step=3, focus=3, bold=True),
        stext(380, 225, 'all reversed values have 19 digits, so text order = numeric order', 'amber', 11, step=4),
        stext(380, 250, '(REVERSED => true scans also work, but are slower than forward scans)', '#94a3b8', 11, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'With <code>sensor|timestamp</code> keys, a sensor\'s readings are sorted oldest first.',
        'Storing <code>Long.MAX_VALUE − timestamp</code> instead inverts the order: the newest reading has the smallest key.',
        'A forward prefix scan with LIMIT 1 now returns the latest value immediately.',
        'Pad the reversed number to a fixed width (here 19 digits) so byte order matches numeric order. Reverse scans are an alternative but cost more.',
    ])


def tall_wide_anim():
    elems = [
        stext(380, 24, 'Tall-narrow vs flat-wide tables', 'blue', 15, bold=True),
        sbox(20, 50, 340, 205, '', '', 'blue', step=1, fill_opacity=0.08), stext(190, 70, 'Tall: one row per event', 'blue', 12, step=1, bold=True),
        _rows(35, 82, 310, [('2401|2026-10-01', 'att:status=P'), ('2401|2026-10-02', 'att:status=A'), ('2401|2026-10-03', 'att:status=P'),
                            ('2402|2026-10-01', 'att:status=P')], step=1, kw=150),
        stext(190, 205, 'many small rows · scan by prefix', 'blue', 11, step=1), stext(190, 223, 'splits evenly across regions', 'blue', 11, step=1),
        sbox(400, 50, 340, 205, '', '', 'purple', step=2, fill_opacity=0.08), stext(570, 70, 'Wide: one row per student', 'purple', 12, step=2, bold=True),
        _rows(415, 82, 310, [('2401', '10-01=P  10-02=A  10-03=P …'), ('2402', '10-01=P  …')], step=2, kw=60, key_color='#6d28d9'),
        stext(570, 160, 'one get = whole history', 'purple', 11, step=2), stext(570, 178, 'row-level atomic updates', 'purple', 11, step=2),
        stext(570, 205, 'a row never splits: keep it bounded', 'red', 11, step=3, focus=3, bold=True),
        stext(380, 285, 'HBase reference guide: prefer tall-narrow unless you need per-row atomicity', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        '<strong>Tall-narrow</strong>: one row per event, with the entity and date in the key. Read a range with a prefix scan.',
        '<strong>Flat-wide</strong>: one row per entity, with one column per event. One get returns everything, and updates to a row are atomic.',
        'A row is never split across regions, so very wide rows can become huge and unbalanced.',
        'The general advice is tall-narrow; use wide rows only for bounded data that must be read or updated together.',
    ])


def index_table_anim():
    elems = [
        stext(380, 24, 'No secondary indexes: maintain an index table', 'blue', 15, bold=True),
        stext(190, 55, "students (key = roll)", 'green', 12, step=1, bold=True),
        _rows(30, 65, 320, [('2401', 'info:email=anuj@cdac.in'), ('2402', 'info:email=aarshvi@cdac.in')], step=1, kw=60, key_color='#059669'),
        stext(570, 55, 'students_by_email (key = email)', 'blue', 12, step=2, bold=True),
        _rows(410, 65, 330, [('aarshvi@cdac.in', 'r:roll=2402'), ('anuj@cdac.in', 'r:roll=2401')], step=2, kw=150, key_color='#0369a1'),
        sarrow(350, 90, 408, 90, 'amber', step=2),
        stext(380, 150, 'login: get index by email → get students by roll (2 gets)', 'green', 12, step=3, bold=True),
        stext(380, 185, 'two puts are NOT atomic together → index can briefly be stale', 'red', 12, step=4, focus=4),
        stext(380, 220, 'Apache Phoenix: CREATE INDEX maintains this for you (global / local indexes)', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 240, *elems), [
        'The main table is keyed by roll number, so a lookup by email would need a full scan.',
        'An <strong>index table</strong> uses the email as its row key and stores the roll number (or a copy of the needed columns).',
        'A login does two fast gets: index → main table (or one, if the index row holds all needed data).',
        'HBase has no multi-row transactions, so the application must handle failures between the two puts (retry, repair job).',
        'Apache Phoenix provides real secondary indexes on HBase and keeps them consistent.',
    ])


# ================================================================== 5 Deletes, TTL, families
def delete_marker_anim():
    elems = [
        stext(380, 24, 'Delete markers (tombstones)', 'blue', 15, bold=True),
        stable(30, 50, ['marker', 'shell', 'hides'], [
            ['Delete', '(Java API: addColumn)', 'one version'],
            ['DeleteColumn', "delete t, r, 'cf:q'", 'all versions ≤ ts of a column'],
            ['DeleteFamily', "deleteall t, r", 'all columns of a family ≤ ts'],
        ], [130, 230, 300], step=1, title_color='red'),
        sbox(30, 160, 220, 50, 'MemStore / HFile', 'marker stored like a cell', 'gray', step=2, size=12),
        sarrow(250, 185, 290, 185, 'gray', step=2),
        sbox(290, 160, 200, 50, 'reads skip masked cells', '', 'amber', step=2, size=12),
        sarrow(490, 185, 530, 185, 'gray', step=3),
        sbox(530, 160, 210, 50, 'major compaction', 'drops marker + data', 'green', step=3, focus=3, size=12),
        stext(380, 245, "scan … {RAW => true, VERSIONS => 10} shows markers and deleted cells", 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 265, *elems), [
        'HBase files are immutable, so a delete writes a <strong>marker</strong>. There are three kinds, by scope.',
        'Markers live in the MemStore and HFiles like normal cells, and every read skips the cells they mask.',
        'Only a <strong>major compaction</strong> rewrites the files without the marker and the deleted data, freeing the space.',
        'A RAW scan shows what is physically stored, including markers and masked versions, which is useful for debugging.',
    ])


def ttl_anim():
    elems = [
        stext(380, 24, 'Column-family TTL (and MIN_VERSIONS)', 'blue', 15, bold=True),
        '<g data-step="1"><rect x="60" y="70" width="640" height="18" rx="9" fill="#334155"/></g>',
        '<g data-step="2"><rect x="60" y="70" width="640" height="18" rx="9" fill="#ef4444" fill-opacity="0.6"/></g>',
        stext(60, 60, "{NAME => 'c', TTL => 300}", 'green', 11, 'start', step=1, bold=True),
        stext(700, 110, 'after 300 s: cell invisible', 'red', 11, 'end', step=2, focus=2, bold=True),
        sbox(60, 135, 300, 50, 'removed at compaction', 'no delete markers needed', 'green', step=3, size=12),
        sbox(400, 135, 300, 50, 'MIN_VERSIONS => 1', 'keep the newest version even if expired', 'purple', step=4, focus=4, size=12),
        stext(380, 225, 'TTL is per family (seconds); cell-level TTL exists in the Java API', 'cyan', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 245, *elems), [
        'A column family can declare a <strong>TTL</strong> in seconds. Every cell in it expires that long after its timestamp.',
        'Expired cells disappear from reads immediately.',
        'They are physically dropped when files are compacted. Unlike deletes, expiry needs no markers.',
        'With <code>MIN_VERSIONS</code>, HBase keeps at least that many recent versions even after they expire, e.g. "keep 30 days of readings, but always the last known value".',
        'TTL is set per family; the Java API can also set a per-cell TTL on a Put.',
    ])


def keep_deleted_anim():
    elems = [
        stext(380, 24, 'KEEP_DELETED_CELLS: time travel past a delete', 'blue', 15, bold=True),
        '<g data-step="1"><line x1="60" y1="100" x2="700" y2="100" stroke="#475569" stroke-width="3"/></g>',
        _node(150, 100, 't1', 'blue', step=1, sub="'started'"), _node(330, 100, 't2', 'blue', step=1, sub="'submitted'"),
        _node(510, 100, 't3', 'red', step=2, sub='delete'),
        stext(610, 80, 'now', '#94a3b8', 11, step=2),
        sbox(40, 165, 330, 45, 'get (now) → nothing', '', 'red', step=2, size=12),
        sbox(390, 165, 330, 45, 'get TIMERANGE [0, t3) → both versions', '', 'green', step=3, focus=3, size=12),
        stext(380, 245, 'audit / recovery: deleted data stays readable "as of" an earlier time', 'cyan', 12, step=4, bold=True),
        stext(380, 268, 'still bound by VERSIONS and TTL; costs storage', 'amber', 11, step=4),
    ]
    return anim(canvas(760, 285, *elems), [
        'An exam attempt was "started", then "submitted".',
        'Then the column is deleted. A normal read now returns nothing.',
        'With <code>KEEP_DELETED_CELLS => true</code>, a read with a time range that ends <strong>before</strong> the delete still sees the old versions, and compaction keeps them.',
        'Useful for audit trails and recovering from accidental deletes. The cells are still limited by VERSIONS and TTL and use disk space.',
    ])


def cf_design_anim():
    elems = [
        stext(380, 24, 'Column families are physical: design few of them', 'blue', 15, bold=True),
        sbox(20, 50, 720, 120, '', '', 'gray', step=1, fill_opacity=0.05), stext(380, 70, 'Region (one key range)', 'gray', 12, step=1, bold=True),
        sbox(40, 85, 330, 75, 'Store: info', 'MemStore + HFiles of its own', 'blue', step=1, size=12),
        sbox(390, 85, 330, 75, 'Store: marks', 'MemStore + HFiles of its own', 'purple', step=1, size=12),
        stext(380, 195, 'one MemStore fills → ALL families of the region flush', 'red', 12, step=2, focus=2, bold=True),
        stext(380, 220, '→ many tiny files for small families, more compaction', 'red', 11, step=2),
        stext(380, 250, 'rules: 1–3 families · short names (stored in every cell) · group by access pattern', 'green', 12, step=3, focus=3, bold=True),
        stext(380, 275, 'per-family settings: VERSIONS, TTL, COMPRESSION, BLOOMFILTER, BLOCKCACHE, IN_MEMORY', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'Each column family is a separate <strong>Store</strong> inside every region, with its own MemStore and its own HFiles on disk.',
        'Flushing is per region: when one family\'s MemStore fills up, the other families are typically flushed too, creating many small files if their data volumes differ a lot.',
        'Therefore keep 1–3 families, give them short names (the family name is stored in every cell) and group columns that are read together.',
        'Families are also where storage settings live: versions, TTL, compression, Bloom filters, caching.',
    ])


def storage_tuning_anim():
    elems = [
        stext(380, 24, 'Family-level storage settings', 'blue', 15, bold=True),
        stable(20, 50, ['setting', 'what it does', 'typical choice'], [
            ['COMPRESSION', 'compress HFile blocks', 'SNAPPY / LZ4 / ZSTD'],
            ['DATA_BLOCK_ENCODING', 'encode repeated key prefixes', 'FAST_DIFF / ROW_INDEX_V1'],
            ['BLOOMFILTER', 'skip HFiles without the row', 'ROW (default), ROWCOL'],
            ['BLOCKSIZE', 'HFile block size', '64 KB; smaller for random gets'],
            ['BLOCKCACHE / IN_MEMORY', 'cache blocks / higher priority', 'true / for small hot families'],
        ], [190, 260, 270], step=1, title_color='blue'),
        stext(380, 230, 'set with create or alter: alter t, {NAME => \'info\', COMPRESSION => \'SNAPPY\'}', 'green', 12, step=2, bold=True),
        stext(380, 258, 'existing HFiles change at the next major compaction', 'amber', 11, step=3, focus=3),
    ]
    return anim(canvas(760, 275, *elems), [
        'These family-level settings trade CPU, memory and disk for speed. Compression and data block encoding shrink files; Bloom filters and caching speed up reads.',
        'They are set when the table is created or later with <code>alter</code>.',
        'New settings apply to newly written files; existing HFiles are rewritten with them at the next major compaction.',
    ])


# ================================================================== 6 Architecture
def architecture_anim():
    elems = [
        stext(380, 24, 'HBase architecture', 'blue', 15, bold=True),
        sbox(20, 50, 140, 45, 'Client', '', 'gray', step=1, size=12),
        sbox(200, 45, 170, 55, 'ZooKeeper', 'meta location, liveness', 'amber', step=2, size=11),
        sbox(410, 45, 170, 55, 'HMaster (active)', 'DDL, assignment, balance', 'purple', step=3, focus=3, size=11),
        sbox(600, 45, 140, 55, 'HMaster', '(backup)', 'gray', step=3, size=11),
        sarrow(160, 70, 198, 70, 'amber', step=2),
    ]
    for i, x in enumerate((40, 285, 530)):
        elems.append(sbox(x, 125, 200, 95, '', '', 'green', step=4, fill_opacity=0.08))
        elems.append(stext(x + 100, 143, f'RegionServer {i + 1}', 'green', 12, step=4, bold=True))
        elems.append(scell(x + 10, 152, 85, 26, f'region {chr(65 + 2 * i)}', '#059669', '#fff', step=4, size=10))
        elems.append(scell(x + 105, 152, 85, 26, f'region {chr(66 + 2 * i)}', '#059669', '#fff', step=4, size=10))
        elems.append(stext(x + 100, 200, 'WAL · MemStores · BlockCache', '#cbd5e1', 10, step=4))
    elems += [
        sarrow(90, 95, 140, 123, 'green', step=5),
        stext(150, 113, 'reads/writes go DIRECTLY to RegionServers', 'green', 10, 'start', step=5, bold=True),
        sbox(20, 240, 720, 40, 'HDFS: HFiles + WAL files (replicated ×3 by HDFS)', '', 'blue', step=6, size=12),
    ]
    return anim(canvas(760, 295, *elems), [
        'Applications use the HBase client library (Java, or REST/Thrift gateways).',
        '<strong>ZooKeeper</strong> stores the location of the <code>hbase:meta</code> table and tracks which servers are alive.',
        'The <strong>HMaster</strong> handles DDL, assigns regions to RegionServers and balances them. A backup master takes over via ZooKeeper if it fails.',
        '<strong>RegionServers</strong> serve regions (key ranges of tables). Each has a WAL, a MemStore per family and a BlockCache.',
        'Data requests go directly from the client to the RegionServer; the master is not on the read/write path.',
        'All files (HFiles and WALs) are stored on <strong>HDFS</strong>, which provides replication and durability.',
    ])


def region_anim():
    elems = [
        stext(380, 24, 'Regions: contiguous key ranges that split as they grow', 'blue', 15, bold=True),
        _region(20, 50, 720, 60, "Region of 'students'", "start '' → end ''  (one region at creation)", 'gray', step=1),
        _region(20, 130, 355, 60, 'daughter A', "'' → '2450'", 'green', step=2),
        _region(385, 130, 355, 60, 'daughter B', "'2450' → ''", 'green', step=2),
        stext(380, 120, 'size > hbase.hregion.max.filesize (default 10 GB) → split at the midpoint key', 'amber', 11, step=2, bold=True),
        sbox(20, 210, 720, 40, "create 'students', 'info', {SPLITS => ['2410', '2420', '2430']}  →  4 regions from day one", '', 'purple', step=3, focus=3, size=12),
        stext(380, 275, 'pre-splitting avoids the "one hot region" phase after creating a table', 'cyan', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 290, *elems), [
        'A table starts as a single <strong>region</strong> covering the whole key space. A region is the unit of distribution and load balancing.',
        'When a region grows beyond the configured maximum size, it splits at a middle key into two daughter regions, which the master can move to other servers.',
        '<strong>Pre-splitting</strong> creates several regions immediately, based on known key boundaries (e.g. salt prefixes or roll-number ranges).',
        'Without pre-splitting, a new table receives all its initial load on one region and one server until splits happen.',
    ])


def write_path_anim():
    elems = [
        stext(380, 24, 'Write path on a RegionServer', 'blue', 15, bold=True),
        sbox(20, 60, 120, 45, 'put', '', 'gray', step=1, size=12),
        sarrow(140, 82, 198, 70, 'amber', step=2), sarrow(140, 82, 198, 140, 'green', step=3),
        sbox(200, 45, 250, 50, 'WAL (on HDFS)', 'append for durability', 'amber', step=2, size=12),
        sbox(200, 115, 250, 50, 'MemStore (memory)', 'sorted by key, per family', 'green', step=3, focus=3, size=12),
        stext(325, 190, '→ client acknowledged', 'green', 11, step=3, bold=True),
        sarrow(450, 140, 508, 140, 'blue', step=4),
        sbox(510, 115, 230, 50, 'flush → HFile', 'immutable, on HDFS', 'blue', step=4, size=12),
        stext(625, 190, 'memstore.flush.size (128 MB)', '#cbd5e1', 10, step=4),
        stext(380, 230, 'crash before flush? replay the WAL to rebuild the MemStore', 'purple', 12, step=5, focus=5, bold=True),
        stext(380, 255, 'Durability.SKIP_WAL = faster but data loss on crash (bulk load style)', 'red', 11, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'A client sends a <strong>put</strong> to the RegionServer hosting the row\'s region.',
        'The edit is first appended to the <strong>Write-Ahead Log</strong> (WAL) on HDFS, so it survives a server crash.',
        'Then it is added to the <strong>MemStore</strong> of the column family, an in-memory sorted buffer, and the client gets success.',
        'When a MemStore reaches its flush size, it is written to a new immutable <strong>HFile</strong> on HDFS.',
        'If the server dies before flushing, the WAL is split and replayed on the servers that take over its regions. Skipping the WAL is faster but loses unflushed data.',
    ])


def read_path_anim():
    elems = [
        stext(380, 24, 'Read path on a RegionServer', 'blue', 15, bold=True),
        sbox(20, 55, 130, 40, 'get 2401', '', 'gray', step=1, size=12),
        sbox(190, 50, 170, 50, 'BlockCache', 'recently read blocks', 'purple', step=2, size=12),
        sbox(400, 50, 170, 50, 'MemStore', 'unflushed edits', 'green', step=2, size=12),
        sbox(190, 125, 170, 50, 'Bloom filter', 'HFile 1: maybe', 'amber', step=3, focus=3, size=12),
        sbox(400, 125, 170, 50, 'Bloom filter', 'HFile 2: no → skip', 'red', step=3, size=12),
        sbox(190, 200, 170, 45, 'block index → block', 'read 64 KB block', 'blue', step=4, size=11),
        sbox(600, 95, 140, 90, 'merge', 'newest version\nwins; delete\nmarkers mask', 'green', step=5, focus=5, size=12),
        stext(500, 270, 'more HFiles per region = slower reads → compaction', 'cyan', 12, step=6, focus=6, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'A get for row 2401 reaches the region\'s RegionServer.',
        'It checks the <strong>BlockCache</strong> (LRU/bucket cache of HFile blocks) and the <strong>MemStore</strong> for recent edits.',
        'For each HFile, the <strong>Bloom filter</strong> says whether the row might be there; files that certainly do not contain it are skipped.',
        'For the remaining files, the block index locates the 64 KB block containing the row, which is read from HDFS (ideally a local replica) and cached.',
        'Cells from all sources are merged: the newest versions win and delete markers hide deleted data.',
        'Every extra HFile can add work, which is why compaction matters for read latency.',
    ])


def compaction_anim():
    elems = [
        stext(380, 24, 'Minor vs major compaction', 'blue', 15, bold=True),
        scell(40, 60, 70, 30, 'HFile', '#0ea5e9', '#fff', step=1, size=10), scell(115, 60, 70, 30, 'HFile', '#0ea5e9', '#fff', step=1, size=10),
        scell(190, 60, 70, 30, 'HFile', '#0ea5e9', '#fff', step=1, size=10), scell(265, 60, 70, 30, 'HFile', '#0ea5e9', '#fff', step=1, size=10),
        sarrow(185, 95, 185, 120, 'gray', step=2),
        scell(110, 122, 150, 30, 'larger HFile', '#0369a1', '#fff', step=2, size=11),
        stext(185, 175, 'MINOR: merge a few small files', 'blue', 12, step=2, bold=True),
        stext(185, 193, 'keeps delete markers', 'blue', 11, step=2),
        scell(430, 60, 300, 30, 'all HFiles of the store', '#6d28d9', '#fff', step=3, size=11),
        sarrow(580, 95, 580, 120, 'gray', step=3),
        scell(480, 122, 200, 30, 'one HFile', '#4c1d95', '#fff', step=3, size=11),
        stext(580, 175, 'MAJOR: rewrite everything', 'purple', 12, step=3, bold=True),
        stext(580, 193, 'drops deleted, expired, extra versions', 'purple', 11, step=3),
        stext(380, 235, 'major compactions are I/O heavy: often scheduled off-peak (or triggered manually)', 'amber', 12, step=4, focus=4, bold=True),
        stext(380, 260, 'they also restore data locality after region moves', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 275, *elems), [
        'Each flush adds a new HFile, so a store accumulates files over time.',
        '<strong>Minor compaction</strong> merges a few smaller files into one, reducing the number of files per read. Delete markers are kept.',
        '<strong>Major compaction</strong> rewrites all files of a store into one, permanently removing deleted cells, markers, expired cells and versions beyond VERSIONS.',
        'Major compactions are expensive, so many clusters disable the automatic weekly run and schedule them off-peak. They also make data local to the RegionServer again.',
    ])


# ================================================================== 7 Clients, recovery, tools
def meta_lookup_anim():
    elems = [
        stext(380, 24, 'How a client finds the RegionServer for a row', 'blue', 15, bold=True),
        sbox(20, 60, 130, 45, 'Client', 'get 2401', 'gray', step=1, size=12),
        sbox(200, 45, 180, 45, 'ZooKeeper', 'where is hbase:meta?', 'amber', step=1, size=11),
        sbox(200, 115, 180, 50, 'hbase:meta (on RS2)', "table,startkey → server", 'purple', step=2, size=11),
        sbox(430, 80, 160, 50, 'RS3: region', "'2400' … '2450'", 'green', step=3, focus=3, size=11),
        sarrow(150, 75, 198, 68, 'amber', step=1), sarrow(150, 90, 198, 135, 'purple', step=2), sarrow(380, 120, 428, 108, 'green', step=3),
        sbox(620, 70, 120, 70, 'meta cache', 'in the client', 'cyan', step=4, size=11),
        stext(380, 205, 'next gets: straight to RS3 using the cached location', 'cyan', 12, step=4, bold=True),
        stext(380, 235, 'region moved? NotServingRegionException → refresh cache, retry', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'The client first asks ZooKeeper where the <code>hbase:meta</code> catalog table is.',
        'It reads hbase:meta, which lists every region (table, start key) and the RegionServer hosting it.',
        'It sends the get directly to the RegionServer whose region covers the row key.',
        'Locations are cached in the client, so later requests skip ZooKeeper and meta entirely.',
        'If a region has moved or split, the old server answers NotServingRegionException; the client refreshes its cache and retries.',
    ])


def failover_anim():
    elems = [
        stext(380, 24, 'RegionServer failure and recovery', 'blue', 15, bold=True),
        sbox(20, 55, 170, 60, 'RS1 dies', 'ZK session expires', 'red', step=1, focus=1, size=12),
        sbox(210, 55, 170, 60, 'HMaster notices', 'via ZooKeeper', 'purple', step=2, size=12),
        sbox(400, 55, 170, 60, 'WAL split', 'edits grouped by region', 'amber', step=3, size=12),
        sbox(590, 55, 150, 60, 'regions reassigned', 'to RS2, RS3', 'green', step=4, size=11),
        sarrow(190, 85, 208, 85, 'gray', step=2), sarrow(380, 85, 398, 85, 'gray', step=3), sarrow(570, 85, 588, 85, 'gray', step=4),
        stext(380, 150, 'new servers replay the WAL edits, then serve: no acknowledged write is lost', 'green', 12, step=4, bold=True),
        stext(380, 185, 'meanwhile those regions are unavailable (MTTR: seconds to minutes)', 'red', 12, step=5, focus=5),
        stext(380, 220, 'region replicas (REGION_REPLICATION > 1): read-only copies for timeline-consistent reads', 'cyan', 11, step=6),
    ]
    return anim(canvas(760, 240, *elems), [
        'A RegionServer crashes; its ZooKeeper session times out.',
        'The HMaster is notified and starts recovery.',
        'The dead server\'s WAL files (on HDFS, so they survived) are split per region.',
        'Its regions are assigned to other RegionServers, which replay the WAL edits before serving. Acknowledged writes are not lost.',
        'Until recovery completes, those regions cannot be read or written: the price of strong consistency.',
        'For read availability, HBase supports region replicas: secondary read-only copies serving possibly stale ("timeline consistent") reads.',
    ])


def clients_anim():
    elems = [
        stext(380, 24, 'Ways to talk to HBase', 'blue', 15, bold=True),
        sbox(20, 55, 170, 60, 'Java client API', 'Table, Put, Get, Scan', 'green', step=1, size=12),
        sbox(205, 55, 170, 60, 'Thrift server', 'Python (HappyBase), C++', 'blue', step=2, size=12),
        sbox(390, 55, 170, 60, 'REST server', 'HTTP + JSON / XML', 'purple', step=2, size=12),
        sbox(575, 55, 165, 60, 'HBase shell', 'JRuby, admin & tests', 'gray', step=1, size=12),
        sbox(20, 140, 355, 50, 'BufferedMutator', 'batches puts client-side for throughput', 'amber', step=3, size=12),
        sbox(390, 140, 350, 50, 'Connection is heavy, Table is light', 'create one Connection per app', 'red', step=4, focus=4, size=12),
        stext(380, 225, 'Spark, MapReduce, Hive and Phoenix use the Java client underneath', 'cyan', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 245, *elems), [
        'The native <strong>Java client API</strong> is the primary interface; the <strong>shell</strong> (JRuby) is for administration and testing.',
        'Other languages use the <strong>Thrift</strong> gateway (e.g. Python\'s HappyBase) or the <strong>REST</strong> gateway.',
        '<strong>BufferedMutator</strong> buffers puts on the client and sends them in batches: much higher write throughput.',
        'A Connection is expensive (ZooKeeper session, meta cache, thread pools): create it once and share it; Table objects are cheap and short-lived.',
        'Higher-level tools (Spark connectors, MapReduce TableInputFormat, Hive HBase handler, Phoenix) are built on the Java client.',
    ])


def bulkload_anim():
    elems = [
        stext(380, 24, 'Bulk load: write HFiles directly, skip the write path', 'blue', 15, bold=True),
        sbox(20, 60, 150, 50, 'CSV / Parquet', 'on HDFS', 'gray', step=1, size=12),
        sbox(200, 60, 180, 50, 'MapReduce / Spark', 'sort by row key', 'amber', step=2, size=12),
        sbox(410, 60, 150, 50, 'HFiles', 'one set per region', 'blue', step=3, size=12),
        sbox(590, 60, 150, 50, 'completebulkload', 'move into regions', 'green', step=4, focus=4, size=11),
        sarrow(170, 85, 198, 85, 'gray', step=2), sarrow(380, 85, 408, 85, 'gray', step=3), sarrow(560, 85, 588, 85, 'gray', step=4),
        stext(380, 150, 'no WAL, no MemStore, no flushes/compactions caused by the load', 'green', 12, step=5, bold=True),
        stext(380, 180, 'much faster than millions of puts and gentle on the cluster', 'green', 11, step=5),
        stext(380, 215, 'not replicated by WAL-based replication: handle bulk-load replication separately', 'amber', 11, step=6, focus=6),
    ]
    return anim(canvas(760, 235, *elems), [
        'Start from source files, e.g. a historical export on HDFS.',
        'A MapReduce (ImportTsv / HFileOutputFormat2) or Spark job sorts records by row key and partitions them by the table\'s region boundaries.',
        'It writes complete HFiles, one set per region.',
        '<code>completebulkload</code> (LoadIncrementalHFiles / BulkLoadHFiles) moves the files into the regions atomically.',
        'The data never goes through the WAL or MemStore, so huge loads are fast and do not disturb live traffic.',
        'Because there is no WAL entry, cluster replication needs bulk-load replication enabled separately.',
    ])


def phoenix_anim():
    elems = [
        stext(380, 24, 'Apache Phoenix: SQL and indexes on HBase', 'blue', 15, bold=True),
        sbox(20, 55, 220, 50, 'SQL via JDBC', 'SELECT … WHERE … GROUP BY', 'gray', step=1, size=12),
        sarrow(240, 80, 288, 80, 'gray', step=1),
        sbox(290, 45, 200, 70, 'Phoenix', 'compiles SQL to scans\n+ coprocessors', 'purple', step=2, focus=2, size=12),
        sarrow(490, 80, 538, 80, 'gray', step=2),
        sbox(540, 55, 200, 50, 'HBase tables', 'PK → row key', 'green', step=2, size=12),
        stext(380, 150, 'PRIMARY KEY columns are encoded into the row key', 'green', 12, step=3, bold=True),
        stext(380, 178, 'CREATE INDEX: global or local secondary indexes, kept in sync', 'blue', 12, step=4),
        stext(380, 206, 'SALT_BUCKETS, aggregation pushed into RegionServers, joins, UPSERT', 'amber', 12, step=5),
        stext(380, 236, 'for OLTP-style queries on HBase, not for heavy analytics', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Phoenix gives HBase a SQL interface through a JDBC driver.',
        'It compiles SQL into HBase scans and uses coprocessors to filter and aggregate inside the RegionServers.',
        'A table\'s PRIMARY KEY columns are concatenated into the HBase row key, so key design still matters.',
        'Phoenix adds <strong>secondary indexes</strong> (global for read-heavy, local for write-heavy) that it keeps in sync.',
        'It also offers salting, UPSERT, joins and server-side aggregation; good for low-latency SQL, not for warehouse-scale analytics.',
    ])


# ================================================================== 8 Scenarios
def attendance_design_anim():
    elems = [
        stext(380, 24, "Row key: salt | centre | yyyyMMdd | roll", 'blue', 15, bold=True),
        scell(60, 60, 70, 34, '3', '#f59e0b', '#fff', step=1, focus=1, bold=True),
        scell(130, 60, 170, 34, 'KHR', '#10b981', '#fff', step=2, bold=True),
        scell(300, 60, 190, 34, '20261014', '#0ea5e9', '#fff', step=3, bold=True),
        scell(490, 60, 190, 34, '2401', '#8b5cf6', '#fff', step=4, bold=True),
        stext(95, 112, 'hash(roll) % 8', 'amber', 10, step=1), stext(215, 112, 'centre code', 'green', 10, step=2),
        stext(395, 112, 'day', 'blue', 10, step=3), stext(585, 112, 'unique per student', 'purple', 10, step=4),
        stext(380, 155, "centre-day report: 8 prefix scans  'n|KHR|20261014|'  (n = 0…7)", 'green', 12, step=5, bold=True),
        stext(380, 185, "student history: second table  'roll|yyyyMMdd'", 'blue', 12, step=5),
        stext(380, 220, 'pre-split on salt values: 8 regions from day one', 'cyan', 12, step=6, focus=6, bold=True),
    ]
    return anim(canvas(760, 240, *elems), [
        'A <strong>salt</strong> computed from the roll number spreads the morning check-in burst over 8 key ranges.',
        'The <strong>centre code</strong> groups a centre\'s rows within each salt bucket.',
        'The <strong>day</strong> (yyyyMMdd, fixed width) makes "one centre, one day" a contiguous prefix.',
        'The <strong>roll number</strong> makes each row unique.',
        'The centre-day report runs one prefix scan per salt and merges them; per-student history uses a second table keyed by roll first.',
        'Pre-splitting the table on the salt prefixes gives 8 regions immediately.',
    ])


def messages_anim():
    elems = [
        stext(380, 24, 'Inbox: row key = userId | reversed timestamp | messageId', 'blue', 14, bold=True),
        _rows(30, 55, 700, [('u2401|9223370244901…|m93', "m:from=Anuj  m:body=Thanks!"),
                            ('u2401|9223370244902…|m87', "m:from=Aarshvi  m:body=Notes uploaded"),
                            ('u2401|9223370244902…|m80', "m:from=Vineeta  m:body=Lab at 2 pm")], step=1, kw=280),
        stext(380, 150, 'newest first, all messages of a user contiguous', 'green', 12, step=2, bold=True),
        stext(380, 180, "open inbox: scan ROWPREFIXFILTER => 'u2401|', LIMIT => 20", 'blue', 12, step=3),
        stext(380, 210, 'next page: STARTROW = last key seen + \\x00', 'purple', 12, step=4),
        stext(380, 240, 'Facebook Messages ran on HBase (2010) for exactly this access pattern', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'Each message is a row keyed by user, then reversed timestamp, then message ID (for uniqueness).',
        'A user\'s messages are stored together, newest first.',
        'Opening the inbox is one short prefix scan.',
        'Paging continues from the last key returned.',
        'Facebook moved its Messages platform to HBase in 2010 because of this write-heavy, per-user, recent-first pattern.',
    ])


def spark_hive_anim():
    elems = [
        stext(380, 24, 'HBase in the Hadoop ecosystem', 'blue', 15, bold=True),
        sbox(280, 100, 200, 60, 'HBase', 'live serving data', 'green', step=1, size=13),
        sbox(20, 40, 200, 50, 'Hive', 'HBaseStorageHandler', 'amber', step=2, size=11),
        sbox(540, 40, 200, 50, 'Spark', 'hbase-spark connector', 'purple', step=3, size=11),
        sbox(20, 175, 200, 50, 'MapReduce', 'TableMapper / TableReducer', 'gray', step=4, size=11),
        sbox(540, 175, 200, 50, 'Kafka / NiFi', 'streams into HBase', 'blue', step=4, size=11),
        sarrow(220, 70, 278, 115, 'amber', step=2), sarrow(540, 70, 482, 115, 'purple', step=3),
        sarrow(220, 195, 278, 145, 'gray', step=4), sarrow(540, 195, 482, 145, 'blue', step=4),
        stext(380, 260, 'Hive/Spark full scans are heavy: snapshot + read the HFiles, or use a replica cluster', 'red', 11, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 275, *elems), [
        'HBase usually serves an application\'s live data.',
        '<strong>Hive</strong> can define an external table on an HBase table and query it with SQL (mapping columns with <code>hbase.columns.mapping</code>).',
        '<strong>Spark</strong> reads and writes HBase through the hbase-spark connector or TableInputFormat, one task per region.',
        'MapReduce jobs and streaming tools (Kafka, NiFi) also read from and write to HBase.',
        'Analytical full scans compete with live traffic. Prefer snapshots (ExportSnapshot / TableSnapshotInputFormat reading HFiles directly) or a separate replica cluster.',
    ])


def tuning_anim():
    elems = [
        stext(380, 24, 'Common HBase problems and fixes', 'blue', 15, bold=True),
        stable(20, 50, ['symptom', 'likely cause', 'fix'], [
            ['one RS at 100%, others idle', 'hotspot: monotonic keys', 'salt / hash keys, pre-split'],
            ['write stalls (blocking updates)', 'too many HFiles', 'tune flush & compaction'],
            ['long GC pauses, RS expiry', 'big on-heap cache', 'off-heap BucketCache, G1'],
            ['slow random reads', 'cache misses, many HFiles', 'Bloom filters, cache, compact'],
            ['too many regions', 'tiny regions / small max filesize', 'merge regions, raise max filesize'],
        ], [230, 240, 250], step=1, title_color='red'),
        stext(380, 230, 'tools: Master UI (16010) · RS UI (16030) · hbck2 · hbase canary · JMX metrics', 'cyan', 12, step=2, bold=True),
        stext(380, 258, 'most problems trace back to row key and column family design', 'amber', 12, step=3, focus=3),
    ]
    return anim(canvas(760, 275, *elems), [
        'Typical production symptoms, with their usual causes and fixes.',
        'The Master and RegionServer web UIs, <code>hbck2</code> (consistency repair), <code>hbase canary</code> and JMX metrics show where the problem is.',
        'As with Cassandra, schema design (row keys, families) is behind most performance issues.',
    ])


def hbase_vs_cassandra_anim():
    elems = [
        stext(380, 24, 'HBase vs Cassandra: two wide-column stores', 'blue', 15, bold=True),
        sbox(20, 50, 350, 200, '', '', 'green', step=1, fill_opacity=0.08), stext(195, 70, 'HBase', 'green', 13, step=1, bold=True),
        stext(195, 95, 'HMaster + RegionServers + ZooKeeper', '#e2e8f0', 11, step=1),
        stext(195, 115, 'storage on HDFS', '#e2e8f0', 11, step=1),
        stext(195, 135, 'CP: strong consistency per row', '#e2e8f0', 11, step=2, bold=True),
        stext(195, 155, 'ordered keys → efficient range scans', '#e2e8f0', 11, step=3),
        stext(195, 175, 'exact counters, checkAndPut', '#e2e8f0', 11, step=3),
        stext(195, 205, 'fits an existing Hadoop platform', 'green', 11, step=4, bold=True),
        sbox(390, 50, 350, 200, '', '', 'blue', step=1, fill_opacity=0.08), stext(565, 70, 'Cassandra', 'blue', 13, step=1, bold=True),
        stext(565, 95, 'masterless ring, no ZooKeeper', '#e2e8f0', 11, step=1),
        stext(565, 115, 'own storage on local disks', '#e2e8f0', 11, step=1),
        stext(565, 135, 'AP: tunable consistency', '#e2e8f0', 11, step=2, bold=True),
        stext(565, 155, 'hashed partitions; ranges only inside one', '#e2e8f0', 11, step=3),
        stext(565, 175, 'multi-DC active-active built in', '#e2e8f0', 11, step=3),
        stext(565, 205, 'always-on, write-heavy, global', 'blue', 11, step=4, bold=True),
        stext(380, 275, 'same Bigtable storage ideas (memtable, SSTable/HFile, compaction), different distribution', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 290, *elems), [
        'HBase has master-based coordination and stores files on HDFS; Cassandra is a masterless peer-to-peer ring with its own storage.',
        'HBase gives strong consistency per row (CP); Cassandra stays available and lets each query choose its consistency (AP by default).',
        'HBase keys are ordered across the whole table, so range scans over any key range are natural; Cassandra hashes partition keys. HBase also has exact atomic counters and check-and-put.',
        'Pick HBase inside a Hadoop platform needing consistent reads and scans; pick Cassandra for always-on, multi-data-centre, write-heavy workloads.',
        'Both share Bigtable\'s storage engine design: memory buffer, immutable sorted files, compaction.',
    ])
