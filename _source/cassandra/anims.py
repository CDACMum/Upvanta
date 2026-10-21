import math

from build import *
from build import _attrs, _t


# ------------------------------------------------------------------ drawing helpers
def _node(x, y, label, color='blue', step=None, focus=None, r=22, size=11, sub=None):
    c = PALETTE.get(color, color)
    s = (f'<g{_attrs(step, focus)} class="sbox"><circle cx="{x}" cy="{y}" r="{r}" fill="#1e293b"/>'
         f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="2"/>'
         f'<text x="{x}" y="{y + 4}" font-size="{size}" fill="#f1f5f9" text-anchor="middle" font-weight="bold">{_t(label)}</text>')
    if sub:
        s += f'<text x="{x}" y="{y + r + 14}" font-size="10" fill="#cbd5e1" text-anchor="middle">{_t(sub)}</text>'
    return s + '</g>'


def _ring_pos(cx, cy, r, n, i, start=-90):
    a = math.radians(start + 360 * i / n)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def _ring(cx, cy, r, labels, color='blue', step=None, focus_map=None, colors=None, subs=None, nr=22):
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#475569" stroke-width="2" stroke-dasharray="4,4"{_attrs(step)}/>']
    for i, lab in enumerate(labels):
        x, y = _ring_pos(cx, cy, r, len(labels), i)
        f = (focus_map or {}).get(i)
        col = (colors or {}).get(i, color)
        out.append(_node(x, y, lab, col, step=step, focus=f, r=nr, sub=(subs or {}).get(i)))
    return ''.join(out)


def _mono(x, y, text, color='#e2e8f0', size=11, step=None, focus=None, anchor='start'):
    c = PALETTE.get(color, color)
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" text-anchor="{anchor}" '
            f'font-family="Fira Code, monospace"{_attrs(step, focus)}>{_t(text)}</text>')


def _part(x, y, w, key, rows, color='green', step=None, focus=None, title=None, rh=22, kw=None):
    """A partition: a key box on the left and its sorted rows on the right."""
    kw = kw or 110
    h = rh * max(1, len(rows)) + 8
    out = [sbox(x, y, w, h, '', '', color, step=step, focus=focus, fill_opacity=0.08)]
    out.append(scell(x + 4, y + 4, kw, h - 8, key, PALETTE.get(color, color), '#fff', step=step, bold=True, size=11))
    for i, r in enumerate(rows):
        out.append(scell(x + kw + 8, y + 4 + i * rh, w - kw - 12, rh, r, '#162033' if i % 2 == 0 else '#0f172a', step=step, size=11))
    if title:
        out.append(stext(x + w / 2, y - 6, title, color, 11, step=step, bold=True))
    return ''.join(out)


# ================================================================== 1 Foundations
def masterless_anim():
    labels = ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']
    elems = [
        stext(380, 24, 'A Cassandra cluster: a ring of equal nodes', 'blue', 15, bold=True),
        _ring(250, 150, 95, labels, 'blue', step=1),
        sbox(470, 55, 270, 50, 'No master, no single point of failure', '', 'green', step=2, focus=2, size=12),
        sbox(20, 40, 120, 40, 'Client', '', 'gray', step=3, size=12),
        sarrow(140, 58, 226, 58, 'amber', step=3),
        stext(22, 100, 'any node can be', 'amber', 11, 'start', step=3), stext(22, 114, 'the coordinator', 'amber', 11, 'start', step=3, bold=True),
        sflow(250, 55, 332, 102, 'amber', step=4, count=2), sflow(250, 55, 168, 198, 'amber', step=4, count=2),
        sbox(470, 120, 270, 60, 'Data copied to RF replicas', 'e.g. RF = 3 → 3 nodes hold each row', 'amber', step=4, size=12),
        sbox(470, 195, 270, 60, 'Add nodes → more capacity', 'linear scale-out, no downtime', 'purple', step=5, focus=5, size=12),
        stext(380, 295, 'peer-to-peer · always on · write-optimised · tunable consistency', 'cyan', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 310, *elems), [
        'A Cassandra cluster is a set of <strong>nodes arranged in a logical ring</strong>. Every node runs the same software and has the same role.',
        'There is <strong>no master</strong>. Nodes learn about each other through gossip, so no single machine failing can stop the cluster.',
        'A client can connect to <strong>any node</strong>. That node acts as the <strong>coordinator</strong> for the request.',
        'The coordinator forwards the write to the nodes that own the row. With replication factor 3, three nodes keep a copy.',
        'Adding nodes adds capacity almost linearly. This is why Cassandra is used for huge, always-on, write-heavy workloads.',
    ])


def topology_anim():
    elems = [
        stext(380, 24, 'Cluster → Data centres → Racks → Nodes', 'blue', 15, bold=True),
        sbox(15, 45, 730, 250, '', '', 'gray', step=1, fill_opacity=0.04),
        stext(380, 64, 'cluster: cdac_prod', 'gray', 12, step=1, bold=True),
        sbox(30, 75, 340, 205, '', '', 'blue', step=2, fill_opacity=0.08), stext(200, 95, 'DC: dc_mumbai', 'blue', 12, step=2, bold=True),
        sbox(390, 75, 340, 205, '', '', 'purple', step=2, fill_opacity=0.08), stext(560, 95, 'DC: dc_pune (analytics)', 'purple', 12, step=2, bold=True),
        sbox(45, 105, 150, 160, '', '', 'cyan', step=3, fill_opacity=0.06), stext(120, 122, 'rack r1', 'cyan', 11, step=3),
        sbox(205, 105, 150, 160, '', '', 'cyan', step=3, fill_opacity=0.06), stext(280, 122, 'rack r2', 'cyan', 11, step=3),
        _node(120, 160, 'N1', 'blue', step=3), _node(120, 220, 'N2', 'blue', step=3),
        _node(280, 160, 'N3', 'blue', step=3), _node(280, 220, 'N4', 'blue', step=3),
        _node(480, 170, 'N5', 'purple', step=3), _node(560, 170, 'N6', 'purple', step=3), _node(640, 170, 'N7', 'purple', step=3),
        sflow(142, 160, 258, 160, 'green', step=4, count=2), sflow(142, 220, 258, 220, 'green', step=4, count=2),
        stext(560, 230, 'gossip every second', 'green', 11, step=4),
        stext(560, 250, 'snitch knows DC + rack', 'amber', 11, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        'A <strong>cluster</strong> is the whole Cassandra installation. It has a name, and all its nodes share one token ring per data centre.',
        'A <strong>data centre</strong> is a group of nodes, often in one location or used for one workload (e.g. live traffic vs analytics). Replication is configured per DC.',
        'Inside a DC, nodes sit in <strong>racks</strong> (failure domains). Cassandra spreads replicas across racks so one failed rack does not lose all copies.',
        'Nodes exchange state with a few peers every second through the <strong>gossip</strong> protocol, so every node knows who is up or down.',
        'The <strong>snitch</strong> (e.g. GossipingPropertyFileSnitch) tells Cassandra which DC and rack each node is in, which drives replica placement and request routing.',
    ])


def rdbms_vs_cass():
    elems = [
        stext(380, 24, 'Same requirement, two mindsets', 'blue', 15, bold=True),
        sbox(20, 50, 340, 235, '', '', 'gray', step=1, fill_opacity=0.06), stext(190, 70, 'RDBMS: model the data', 'gray', 13, step=1, bold=True),
        stable(45, 90, ['roll', 'name'], [['2401', 'Anuj'], ['2402', 'Aarshvi']], [60, 90], step=1, title_color='gray'),
        stable(215, 90, ['roll', 'exam', 'marks'], [['2401', 'SQL', '78'], ['2402', 'SQL', '91']], [40, 50, 45], step=1, title_color='gray'),
        stext(190, 200, 'normalise, then JOIN at read time', 'gray', 11, step=2),
        stext(190, 222, 'one server, ACID, any query', 'gray', 11, step=2),
        sbox(400, 50, 340, 235, '', '', 'green', step=3, fill_opacity=0.08), stext(570, 70, 'Cassandra: model the queries', 'green', 13, step=3, bold=True),
        _part(420, 90, 300, '2401', ['SQL · 78 · Anuj', 'Spark · 84 · Anuj'], 'green', step=3, title='marks_by_student'),
        stext(570, 180, 'one table per query, data duplicated', 'green', 11, step=4, focus=4),
        stext(570, 202, 'no joins: one partition read', 'green', 11, step=4),
        stext(570, 248, 'INSERT = upsert, no "duplicate key"', 'amber', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'In an RDBMS you design normalised tables first (students, marks) and connect them with keys.',
        'Any question can be answered later with joins, ACID transactions and a flexible query optimiser, but usually on one primary server.',
        'In Cassandra you start from the <strong>queries</strong>. For "show a student\'s marks" you create a table partitioned by roll number that already contains everything the screen needs.',
        'There are no joins. Data is duplicated into one table per access pattern, and each read touches a single partition.',
        'Writes are <strong>upserts</strong>: inserting an existing key silently overwrites it. There is no "duplicate key" error and no read-before-write.',
    ])


def cap_anim():
    elems = [
        stext(380, 24, 'CAP: Cassandra chooses Availability, with tunable Consistency', 'blue', 14, bold=True),
        _node(150, 90, 'N1', 'green', step=1, sub='marks = 78'), _node(380, 90, 'N2', 'green', step=1, sub='marks = 78'),
        _node(610, 90, 'N3', 'green', step=1, sub='marks = 78'),
        '<g data-step="2"><line x1="495" y1="55" x2="495" y2="135" stroke="#ef4444" stroke-width="5" stroke-dasharray="8,5"/></g>',
        stext(495, 152, 'partition', 'red', 11, step=2, bold=True),
        sbox(40, 195, 300, 40, 'write marks = 85 at CL ONE', '', 'amber', step=3, size=12),
        sarrow(190, 195, 170, 160, 'amber', step=3),
        stext(150, 150, 'now 85', 'amber', 11, step=3, bold=True), stext(380, 150, 'now 85', 'amber', 11, step=3, bold=True),
        stext(610, 150, 'still 78 (stale)', 'red', 11, step=3, focus=3, bold=True),
        stext(380, 255, 'AP: stays available; replicas converge later (hints, repair)', 'green', 12, step=4, focus=4, bold=True),
        stext(380, 280, 'QUORUM reads + QUORUM writes → always see the latest value', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'Three replicas hold the same row. While the network is healthy, every write reaches all of them.',
        'A <strong>network partition</strong> cuts N3 off. CAP says a distributed system must now choose between consistency and availability.',
        'Cassandra keeps accepting writes. With consistency level ONE, a write succeeds as soon as one reachable replica stores it; N3 misses the update.',
        'This is <strong>AP</strong> behaviour: always writable and readable, eventually consistent. Hinted handoff and repair bring N3 up to date when the network heals.',
        'Consistency is <strong>tunable per query</strong>: with QUORUM reads and writes (R + W > RF), reads always overlap the latest write, giving strong consistency for that data.',
    ])


def cql_types_anim():
    elems = [
        stext(380, 24, 'CQL: SQL-like syntax, Cassandra rules', 'blue', 15, bold=True),
        sbox(20, 50, 230, 210, '', '', 'blue', step=1, fill_opacity=0.08), stext(135, 70, 'Familiar', 'blue', 13, step=1, bold=True),
        stext(35, 95, 'CREATE TABLE · INSERT', '#e2e8f0', 11, 'start', step=1), stext(35, 113, 'SELECT · UPDATE · DELETE', '#e2e8f0', 11, 'start', step=1),
        stext(35, 131, 'WHERE · ORDER BY · LIMIT', '#e2e8f0', 11, 'start', step=1), stext(35, 149, 'GROUP BY · COUNT · AVG', '#e2e8f0', 11, 'start', step=1),
        sbox(265, 50, 230, 210, '', '', 'red', step=2, fill_opacity=0.08), stext(380, 70, 'Missing on purpose', 'red', 13, step=2, bold=True),
        stext(280, 95, 'no JOINs', '#e2e8f0', 11, 'start', step=2), stext(280, 113, 'no sub-queries', '#e2e8f0', 11, 'start', step=2),
        stext(280, 131, 'no foreign keys', '#e2e8f0', 11, 'start', step=2), stext(280, 149, 'WHERE only on key columns', '#e2e8f0', 11, 'start', step=2),
        stext(280, 167, '(or indexed ones)', '#94a3b8', 11, 'start', step=2),
        sbox(510, 50, 230, 210, '', '', 'green', step=3, fill_opacity=0.08), stext(625, 70, 'Extra types', 'green', 13, step=3, bold=True),
        stext(525, 95, 'uuid · timeuuid', '#e2e8f0', 11, 'start', step=3), stext(525, 113, 'set · list · map', '#e2e8f0', 11, 'start', step=3),
        stext(525, 131, 'user-defined types (UDT)', '#e2e8f0', 11, 'start', step=3), stext(525, 149, 'counter · duration', '#e2e8f0', 11, 'start', step=3),
        stext(525, 167, 'vector<float, n> (5.0)', '#e2e8f0', 11, 'start', step=3),
        stext(380, 285, 'cqlsh = command-line shell that sends CQL to a node (port 9042)', 'amber', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        '<strong>CQL</strong> (Cassandra Query Language) looks like SQL: tables, rows, columns and the usual statements.',
        'Features that need data from many partitions or nodes are deliberately missing: joins, sub-queries, foreign keys and filtering on arbitrary columns.',
        'It adds types suited to distributed data: UUIDs and time-based timeuuids, collections, user-defined types, counters and (in 5.0) vectors for similarity search.',
        '<strong>cqlsh</strong> is the interactive shell. Applications use drivers (Java, Python, Go) that speak the same native protocol on port 9042.',
    ])


# ================================================================== 2 Data model & keys
def keyspace_anim():
    elems = [
        stext(380, 24, 'Keyspace replication strategies', 'blue', 15, bold=True),
        sbox(20, 50, 350, 225, '', '', 'gray', step=1, fill_opacity=0.06),
        stext(195, 70, "SimpleStrategy, RF = 3", 'gray', 13, step=1, bold=True),
        _ring(195, 170, 72, ['A', 'B', 'C', 'D', 'E', 'F'], 'gray', step=1, focus_map={0: 2, 1: 2, 2: 2}, colors={0: 'green', 1: 'green', 2: 'green'}, nr=18),
        stext(195, 268, 'next 3 nodes clockwise, ignores racks/DCs', 'gray', 11, step=2),
        sbox(390, 50, 350, 225, '', '', 'green', step=3, fill_opacity=0.06),
        stext(565, 70, "NetworkTopologyStrategy", 'green', 13, step=3, bold=True),
        stext(565, 90, "{'dc_mumbai': 3, 'dc_pune': 2}", 'green', 11, step=3),
        sbox(405, 105, 155, 140, '', '', 'blue', step=3, fill_opacity=0.08), stext(482, 122, 'dc_mumbai', 'blue', 11, step=3, bold=True),
        sbox(575, 105, 150, 140, '', '', 'purple', step=3, fill_opacity=0.08), stext(650, 122, 'dc_pune', 'purple', 11, step=3, bold=True),
        _node(440, 155, 'r1', 'blue', step=4, focus=4, r=17), _node(482, 205, 'r2', 'blue', step=4, focus=4, r=17), _node(525, 155, 'r3', 'blue', step=4, focus=4, r=17),
        _node(615, 175, 'r1', 'purple', step=4, focus=4, r=17), _node(685, 175, 'r2', 'purple', step=4, focus=4, r=17),
        stext(565, 268, 'copies per DC, spread across racks', 'green', 11, step=4, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'A <strong>keyspace</strong> is the top-level container (like a database). Its main setting is <strong>replication</strong>: how many copies of every row, and where.',
        '<strong>SimpleStrategy</strong> puts the first replica on the token owner and the next copies on the following nodes clockwise. It knows nothing about racks or DCs: only for single-DC labs.',
        '<strong>NetworkTopologyStrategy</strong> takes a replica count for each data centre, so live and analytics DCs can have different RFs.',
        'Within each DC it places replicas on <strong>different racks</strong> where possible. This is the strategy to use in production, even with one DC.',
    ])


def primary_key_anim():
    elems = [
        stext(380, 24, 'PRIMARY KEY ((roll_no), exam_date, module)', 'blue', 15, bold=True),
        scell(160, 45, 140, 30, 'roll_no', '#10b981', '#fff', step=1, focus=1, bold=True),
        scell(300, 45, 140, 30, 'exam_date', '#f59e0b', '#fff', step=2, focus=2, bold=True),
        scell(440, 45, 140, 30, 'module', '#f59e0b', '#fff', step=2, focus=2, bold=True),
        stext(230, 92, 'partition key', 'green', 11, step=1), stext(370, 92, 'clustering columns', 'amber', 11, step=2),
        stext(230, 108, '→ which node(s)', 'green', 11, step=1), stext(370, 108, '→ order inside partition', 'amber', 11, step=2),
        _part(40, 145, 330, '2401', ['2026-10-05 · Spark · 84', '2026-09-10 · SQL · 78'], 'green', step=3, title='partition 2401 (node N2)', kw=70),
        _part(400, 145, 330, '2402', ['2026-09-10 · SQL · 91'], 'blue', step=3, title='partition 2402 (node N5)', kw=70),
        stext(205, 225, 'rows sorted by exam_date DESC', 'amber', 11, step=4, focus=4),
        stext(380, 260, 'partition key + clustering columns = unique row', 'cyan', 12, step=5, focus=5, bold=True),
        stext(380, 284, 'same key again = overwrite (upsert)', 'red', 11, step=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'The first part of the primary key is the <strong>partition key</strong>. Its hash (token) decides which nodes store the data. All rows with the same partition key live together.',
        'The remaining columns are <strong>clustering columns</strong>. They do not affect placement; they sort rows inside the partition.',
        'So all of student 2401\'s marks form one partition on one set of replicas, and 2402 is a different partition, probably on other nodes.',
        'Inside the partition, rows are stored on disk in clustering order (here newest exam first), which makes range scans and "latest N" queries cheap.',
        'Partition key plus clustering columns uniquely identify a row. Writing the same full key again overwrites that row.',
    ])


def composite_pk_anim():
    elems = [
        stext(380, 24, 'Composite partition key: ((sensor, day), ts)', 'blue', 15, bold=True),
        sbox(20, 50, 340, 120, '', '', 'red', step=1, fill_opacity=0.08),
        stext(190, 70, 'PRIMARY KEY (sensor, ts)', 'red', 12, step=1, bold=True),
        scell(40, 85, 80, 70, 'lab-1', '#ef4444', '#fff', step=1, bold=True),
        scell(125, 85, 215, 70, '≈ 86,400 rows/day … forever', '#334155', step=1),
        stext(190, 190, 'one partition grows without limit', 'red', 11, step=2, focus=2, bold=True),
        sbox(400, 50, 340, 175, '', '', 'green', step=3, fill_opacity=0.08),
        stext(570, 70, 'PRIMARY KEY ((sensor, day), ts)', 'green', 12, step=3, bold=True),
        scell(420, 85, 120, 32, 'lab-1 | 10-13', '#10b981', '#fff', step=3, size=11), scell(545, 85, 175, 32, '86,400 rows', '#334155', step=3, size=11),
        scell(420, 122, 120, 32, 'lab-1 | 10-14', '#10b981', '#fff', step=3, size=11), scell(545, 122, 175, 32, '86,400 rows', '#334155', step=3, size=11),
        scell(420, 159, 120, 32, 'lab-2 | 10-14', '#10b981', '#fff', step=3, size=11), scell(545, 159, 175, 32, '…', '#334155', step=3, size=11),
        stext(570, 215, 'bounded partitions, spread over nodes', 'green', 11, step=4, focus=4),
        stext(380, 260, "token = hash(sensor + day): a query must give BOTH parts", 'amber', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'If the partition key is only <code>sensor</code>, every reading a sensor ever sends lands in one partition.',
        'That partition grows forever: it becomes slow to read, hard to compact and repair, and one node ends up doing all the work for a busy sensor (a hot spot).',
        'A <strong>composite partition key</strong> <code>(sensor, day)</code> starts a new partition every day. This technique is called <strong>bucketing</strong>.',
        'Partitions now have a predictable size and are spread across the cluster.',
        'The token is computed from all partition key columns together, so a query must provide <strong>both</strong> sensor and day to find the partition.',
    ])


def clustering_order_anim():
    elems = [
        stext(380, 24, 'WITH CLUSTERING ORDER BY (ts DESC)', 'blue', 15, bold=True),
        _part(30, 50, 380, "('lab-1', 2026-10-14)", ['10:10 · 25.9', '10:05 · 25.3', '10:00 · 24.5'], 'green', step=1, kw=150,
              title='partition on disk (newest first)'),
        sbox(450, 50, 290, 40, 'SELECT … LIMIT 1 → 10:10', '', 'green', step=2, focus=2, size=12),
        stext(595, 108, 'latest reading = first row, no sorting', 'green', 11, step=2),
        sbox(450, 125, 290, 40, 'ORDER BY ts ASC → read backwards', '', 'blue', step=3, size=12),
        stext(595, 183, 'allowed: exact reverse of stored order', 'blue', 11, step=3),
        sbox(30, 160, 380, 40, 'ORDER BY temp  ✗', '', 'red', step=4, focus=4, size=12),
        stext(220, 218, 'only clustering columns can be ordered', 'red', 11, step=4),
        stext(380, 260, 'ORDER BY needs the partition key in WHERE (= or IN)', 'amber', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'Rows inside a partition are physically stored sorted by the clustering columns, in the order declared with <code>CLUSTERING ORDER BY</code>.',
        'With <code>ts DESC</code>, the newest reading is stored first, so "latest N readings" is a sequential read with no sorting work.',
        '<code>ORDER BY</code> can only choose the stored order or its <strong>exact reverse</strong>; Cassandra simply reads the partition backwards.',
        'You cannot sort by a regular column like <code>temp</code>: Cassandra never sorts result sets in memory.',
        'Ordering is only defined within one partition, so <code>ORDER BY</code> requires the partition key to be restricted with = or IN.',
    ])


def static_anim():
    elems = [
        stext(380, 24, 'Static column: one value per partition', 'blue', 15, bold=True),
        sbox(40, 50, 680, 150, '', '', 'green', step=1, fill_opacity=0.08),
        scell(55, 60, 130, 130, 'DBDA-2026', '#10b981', '#fff', step=1, bold=True),
        scell(195, 60, 160, 32, 'coordinator (static)', '#8b5cf6', '#fff', step=2, focus=2, size=11),
        scell(360, 60, 345, 32, 'Vineeta  → stored ONCE for the partition', '#334155', step=2, size=11),
        scell(195, 100, 160, 28, 'roll 2401', '#162033', step=1, size=11), scell(360, 100, 345, 28, 'Anuj', '#162033', step=1, size=11),
        scell(195, 130, 160, 28, 'roll 2402', '#0f172a', step=1, size=11), scell(360, 130, 345, 28, 'Aarshvi', '#0f172a', step=1, size=11),
        scell(195, 160, 160, 28, 'roll 2403', '#162033', step=1, size=11), scell(360, 160, 345, 28, 'Rohit', '#162033', step=1, size=11),
        sbox(40, 215, 330, 45, "UPDATE … SET coordinator = 'Manoj'", 'WHERE batch = …', 'amber', step=3, size=11),
        stext(555, 235, 'every row now shows Manoj', 'amber', 12, step=3, focus=3, bold=True),
        stext(380, 285, 'needs clustering columns · not part of the key · like a 1-to-many "header"', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'A partition holds many rows: here one row per student in the batch.',
        'A <strong>static</strong> column belongs to the <strong>partition</strong>, not to a row. Its value is stored once, however many rows the partition has.',
        'Updating it needs only the partition key, and every row of the partition immediately shows the new value.',
        'Static columns are only allowed in tables with clustering columns. They model the "one" side of a one-to-many relationship inside the same partition.',
    ])


# ================================================================== 3 Querying
def where_rules_anim():
    elems = [
        stext(380, 24, 'Which WHERE clauses can Cassandra serve?', 'blue', 15, bold=True),
        stext(380, 50, 'PRIMARY KEY ((roll_no), exam_date, module)', 'gray', 12, step=1),
        sbox(20, 65, 720, 36, "WHERE roll_no = 2401", '', 'green', step=1, size=12),
        stext(735, 88, '✓ one partition', 'green', 11, 'end', step=1),
        sbox(20, 110, 720, 36, "WHERE roll_no = 2401 AND exam_date >= '2026-10-01'", '', 'green', step=2, size=12),
        stext(735, 133, '✓ slice', 'green', 11, 'end', step=2),
        sbox(20, 155, 720, 36, "WHERE roll_no = 2401 AND module = 'SQL'", '', 'red', step=3, focus=3, size=12),
        stext(735, 178, '✗ skips exam_date', 'red', 11, 'end', step=3),
        sbox(20, 200, 720, 36, "WHERE marks > 80", '', 'red', step=4, focus=4, size=12),
        stext(735, 223, '✗ every partition', 'red', 11, 'end', step=4),
        stext(380, 270, 'rule: partition key first, then clustering columns left-to-right', 'amber', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'Giving the full partition key lets the coordinator compute the token and go straight to the replicas: the ideal query.',
        'Within the partition you can add clustering-column restrictions in declared order, including one range on the last restricted column. Cassandra reads a contiguous slice.',
        'Restricting <code>module</code> without <code>exam_date</code> would need scanning the whole partition, so Cassandra rejects it.',
        'Filtering on a regular column like <code>marks</code> without the partition key means reading every partition on every node, which is also rejected.',
        'The rule follows the storage layout: partition key to find the data, then clustering columns from left to right to find a contiguous slice.',
    ])


def allow_filtering_anim():
    elems = [
        stext(380, 24, 'SELECT * FROM marks WHERE marks > 80 ALLOW FILTERING', 'blue', 14, bold=True),
        _ring(220, 150, 85, ['N1', 'N2', 'N3', 'N4', 'N5', 'N6'], 'red', step=2, nr=20),
        sbox(20, 45, 110, 36, 'Client', '', 'gray', step=1, size=12),
        stext(220, 283, 'scan ALL partitions on ALL nodes', 'red', 11, step=2, focus=2, bold=True),
        sbox(400, 60, 340, 50, 'read 10,000,000 rows', '', 'red', step=3, size=13),
        sarrow(570, 110, 570, 140, 'gray', step=3),
        sbox(400, 140, 340, 50, 'return 12 rows', '', 'green', step=3, size=13),
        stext(570, 215, 'cost ∝ table size, not result size', 'amber', 12, step=4, focus=4, bold=True),
        stext(570, 245, 'OK: small tables, or WHERE has the partition key', 'green', 11, step=5),
        stext(570, 265, 'fix: a table designed for this query, or SAI', 'cyan', 11, step=5, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'Without the partition key, Cassandra cannot know which nodes hold matching rows.',
        'So the coordinator must contact <strong>every node</strong> and each node must scan <strong>every partition</strong> of the table.',
        'Most of the data read is thrown away after the filter is applied.',
        'The work grows with table size, not with result size. On a large table this causes timeouts and load on the whole cluster, so Cassandra refuses unless you add <code>ALLOW FILTERING</code>.',
        'It is acceptable when the partition key is also restricted (filtering one partition) or on small tables. Otherwise model a new table for the query, or add an SAI index.',
    ])


def index_anim():
    elems = [
        stext(380, 24, 'Secondary index (2i) vs Storage-Attached Index (SAI)', 'blue', 15, bold=True),
        sbox(20, 50, 350, 225, '', '', 'gray', step=1, fill_opacity=0.06),
        stext(195, 70, 'Each node indexes only its own data', 'gray', 12, step=1, bold=True),
        _node(80, 120, 'N1', 'blue', step=1, sub='idx: local'), _node(195, 120, 'N2', 'blue', step=1, sub='idx: local'), _node(310, 120, 'N3', 'blue', step=1, sub='idx: local'),
        sflow(195, 210, 95, 168, 'amber', step=2, count=2), sflow(195, 210, 295, 168, 'amber', step=2, count=2),
        stext(195, 232, "WHERE centre = 'Juhu'", 'amber', 11, step=2), stext(195, 250, '→ asks (almost) every node', 'amber', 11, step=2, focus=2),
        sbox(390, 50, 350, 225, '', '', 'green', step=3, fill_opacity=0.08),
        stext(565, 70, 'SAI (Cassandra 5.0)', 'green', 13, step=3, bold=True),
        stext(405, 98, '• index attached to each SSTable/memtable', '#e2e8f0', 11, 'start', step=3),
        stext(405, 118, '• =, range (<, >), CONTAINS, vector ANN', '#e2e8f0', 11, 'start', step=3),
        stext(405, 138, '• combine several indexed columns with AND', '#e2e8f0', 11, 'start', step=3),
        stext(405, 158, '• much smaller and faster than 2i', '#e2e8f0', 11, 'start', step=3),
        stext(565, 200, 'best: partition key + indexed column', 'green', 11, step=4, focus=4, bold=True),
        stext(565, 220, 'avoid: high-cardinality or very common values', 'red', 11, step=4),
        stext(565, 250, "CREATE INDEX … USING 'sai'", 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'Cassandra indexes are <strong>local</strong>: every node indexes only the rows it stores. There is no global index to look up.',
        'A query on an indexed column without the partition key must therefore ask enough nodes to cover the whole ring and merge their answers, so it is a fan-out query.',
        '<strong>SAI</strong> (Storage-Attached Indexing, default choice from Cassandra 5.0) attaches index data to each SSTable, supports ranges, CONTAINS and vector search, and lets you AND several indexed columns.',
        'Indexes work best together with the partition key, or for medium-cardinality columns. For hot, latency-critical queries, a dedicated table is still the fastest design.',
    ])


def collections_anim():
    elems = [
        stext(380, 24, 'Collections and UDTs inside one row', 'blue', 15, bold=True),
        sbox(20, 50, 720, 190, '', '', 'green', step=1, fill_opacity=0.06),
        scell(35, 60, 100, 170, '2401', '#10b981', '#fff', step=1, bold=True),
        scell(145, 60, 130, 32, 'skills set<text>', '#0ea5e9', '#fff', step=1, size=11), scell(280, 60, 445, 32, "{'kafka', 'spark', 'sql'}  unique, sorted", '#334155', step=1, size=11),
        scell(145, 100, 130, 32, 'phones list<text>', '#f59e0b', '#fff', step=2, size=11), scell(280, 100, 445, 32, "['98200…', '99300…']  ordered, duplicates OK", '#334155', step=2, size=11),
        scell(145, 140, 130, 32, 'scores map', '#8b5cf6', '#fff', step=3, size=11), scell(280, 140, 445, 32, "{'SQL': 78, 'Spark': 84}  key → value", '#334155', step=3, size=11),
        scell(145, 180, 130, 40, 'addr frozen<UDT>', '#ec4899', '#fff', step=4, size=11), scell(280, 180, 445, 40, "{city: 'Pune', pin: 411001}  one blob", '#334155', step=4, size=11),
        stext(380, 268, 'keep collections small (tens of items); a growing list → use clustering rows', 'amber', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'A <strong>set</strong> stores unique values and returns them sorted. Adding an existing value changes nothing. Good for tags and skills.',
        'A <strong>list</strong> keeps insertion order and allows duplicates. Appends are cheap; setting an element by index needs a read-before-write internally.',
        'A <strong>map</strong> stores key-value pairs; single entries can be added or removed (<code>scores[\'Spark\'] = 84</code>).',
        'A <strong>user-defined type</strong> groups named fields (an address). Declared <code>frozen</code>, it is stored and rewritten as one value.',
        'A collection is read in full with its row, so keep it small. Data that grows without limit belongs in clustering rows, not in a collection.',
    ])


def aggregate_anim():
    elems = [
        stext(380, 24, 'Aggregates: cheap inside a partition, costly across the table', 'blue', 14, bold=True),
        _part(30, 55, 330, '2401', ['Spark · 84', 'SQL · 78', 'Python · 79'], 'green', step=1, kw=70, title='WHERE roll_no = 2401'),
        stext(195, 150, 'count / avg over one partition ✓', 'green', 11, step=1, bold=True),
        _ring(560, 120, 65, ['N1', 'N2', 'N3', 'N4', 'N5'], 'red', step=2, nr=18),
        stext(560, 215, 'no partition key → scans every node', 'red', 11, step=2, focus=2, bold=True),
        stext(560, 233, 'warning: Aggregation query used', 'red', 10, step=2), stext(560, 247, 'without partition key', 'red', 10, step=2),
        sbox(30, 175, 330, 45, 'GROUP BY roll_no', 'only key columns, in key order', 'amber', step=3, size=12),
        stext(380, 270, 'avg(int) is an int: 241 / 3 = 80 (not 80.33) → cast or use double', 'pink', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'Aggregates (<code>count</code>, <code>min</code>, <code>max</code>, <code>sum</code>, <code>avg</code>) are computed by the coordinator. Within one partition they are cheap.',
        'Without the partition key they scan the whole table across all nodes. Cassandra allows it but returns a warning, and big tables will time out.',
        '<code>GROUP BY</code> works only on primary key columns, in key order (partition key first). Groups come out in storage order.',
        'Aggregates keep the input type: <code>avg</code> of an <code>int</code> column returns an integer. Store marks as double or cast if you need decimals.',
    ])


# ================================================================== 4 Writes, TTL, deletes, counters, batches
def lww_anim():
    elems = [
        stext(380, 24, 'Last write wins: the newest timestamp decides', 'blue', 15, bold=True),
        sbox(20, 50, 220, 55, "marks = 78", 'writetime 10:00:00.001', 'gray', step=1, size=13),
        sbox(270, 50, 220, 55, "marks = 85", 'writetime 10:00:05.000', 'green', step=2, focus=2, size=13),
        sbox(520, 50, 220, 55, "marks = 60", 'USING TIMESTAMP (older)', 'red', step=3, size=13),
        sarrow(130, 105, 360, 160, 'gray', step=4), sarrow(380, 105, 380, 160, 'green', step=4), sarrow(630, 105, 400, 160, 'red', step=4),
        sbox(260, 160, 240, 50, 'read → marks = 85', '', 'green', step=4, focus=4, size=13),
        stext(380, 240, 'per CELL, not per row · no locks · no read-before-write', 'amber', 12, step=5, bold=True),
        stext(380, 262, 'clocks must be in sync (NTP) for this to be meaningful', 'red', 11, step=5, focus=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Every value written to Cassandra carries a <strong>write timestamp</strong> (microseconds), normally set by the coordinator or driver.',
        'A later write to the same cell has a higher timestamp.',
        'A write with an <em>older</em> timestamp (e.g. a delayed retry, or an explicit <code>USING TIMESTAMP</code>) can arrive later but still loses.',
        'When replicas or SSTables disagree, Cassandra keeps the value with the <strong>highest timestamp</strong>. This is the conflict-resolution rule, called last write wins (LWW).',
        'It works cell by cell, needs no locks, and is why INSERT and UPDATE are both upserts. It also means server clocks must be synchronised with NTP.',
    ])


def ttl_anim():
    elems = [
        stext(380, 24, "INSERT … USING TTL 300 (OTP valid 5 minutes)", 'blue', 15, bold=True),
        '<g data-step="1"><rect x="60" y="80" width="640" height="18" rx="9" fill="#334155"/></g>',
        '<g data-step="2"><rect x="60" y="80" width="256" height="18" rx="9" fill="#f59e0b"/></g>',
        '<g data-step="3"><rect x="60" y="80" width="640" height="18" rx="9" fill="#ef4444" fill-opacity="0.6"/></g>',
        stext(60, 70, 'write: TTL 300 s', 'green', 11, 'start', step=1, bold=True),
        stext(316, 120, 'after 120 s: TTL(code) = 180', 'amber', 11, step=2, focus=2),
        stext(700, 120, 'after 300 s: expired', 'red', 11, 'end', step=3, focus=3, bold=True),
        sbox(60, 150, 300, 50, 'expired cell → tombstone', 'removed for good by compaction', 'red', step=4, size=12),
        sbox(400, 150, 300, 50, 'default_time_to_live', 'table-level TTL for every write', 'purple', step=5, size=12),
        stext(380, 240, 'TTL is per cell: updating one column resets only that column', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 260, *elems), [
        'A write can carry a <strong>TTL</strong> (time to live) in seconds. Cassandra stores the expiry time with each cell.',
        '<code>TTL(column)</code> shows the remaining seconds, which keep counting down.',
        'When the TTL ends, the data simply stops appearing in reads. No delete job is needed.',
        'An expired cell becomes a tombstone and is purged during compaction (after gc_grace_seconds), so heavy TTL use still creates tombstones.',
        'A table can set <code>default_time_to_live</code> for all writes. TTL applies per cell: rewriting one column gives only that column a new TTL.',
    ])


def tombstone_anim():
    elems = [
        stext(380, 24, 'A DELETE is a write: the tombstone', 'blue', 15, bold=True),
        sbox(20, 50, 220, 60, 'SSTable 1 (old)', 'marks = 78 @ t1', 'gray', step=1, size=12),
        sbox(270, 50, 220, 60, 'DELETE at t2', 'writes a tombstone', 'red', step=2, focus=2, size=12),
        sbox(520, 50, 220, 60, 'read merges both', 't2 > t1 → row hidden', 'amber', step=3, size=12),
        '<g data-step="4"><rect x="20" y="140" width="720" height="16" rx="8" fill="#334155"/>'
        '<rect x="20" y="140" width="430" height="16" rx="8" fill="#f59e0b" fill-opacity="0.8"/></g>',
        stext(235, 175, 'gc_grace_seconds (default 10 days)', 'amber', 11, step=4, bold=True),
        stext(595, 175, 'compaction may purge', 'green', 11, step=4),
        stext(380, 205, 'repair must run within gc_grace, or deleted data can come back (zombies)', 'red', 12, step=5, focus=5, bold=True),
        stext(380, 240, 'many tombstones in a partition → slow reads, TombstoneOverwhelmingException', 'pink', 12, step=6, focus=6),
    ]
    return anim(canvas(760, 260, *elems), [
        'SSTables are immutable, so a DELETE cannot remove the old value from files that already exist.',
        'Instead it writes a <strong>tombstone</strong>: a marker saying "deleted at timestamp t2".',
        'Reads merge data from all sources; the tombstone is newer than the value, so the row is not returned.',
        'Tombstones are kept for <code>gc_grace_seconds</code> (10 days by default) so that every replica learns about the delete, and are then purged by compaction.',
        'If a replica was down and is not repaired within that window, it may still hold the old value and resurrect it after the tombstone is purged ("zombie" data).',
        'Reading through many tombstones is slow; past 100,000 in one query Cassandra aborts. Queue-like or delete-heavy patterns are therefore anti-patterns.',
    ])


def counter_anim():
    elems = [
        stext(380, 24, 'Counter columns: distributed increments', 'blue', 15, bold=True),
        sbox(30, 55, 200, 40, 'views + 1  (N1)', '', 'green', step=1, size=12),
        sbox(30, 105, 200, 40, 'views + 1  (N2)', '', 'green', step=1, size=12),
        sbox(30, 155, 200, 40, 'views + 5  (N3)', '', 'green', step=1, size=12),
        sarrow(230, 75, 330, 120, 'green', step=2), sarrow(230, 125, 330, 125, 'green', step=2), sarrow(230, 175, 330, 130, 'green', step=2),
        sbox(330, 95, 180, 60, 'views = 7', 'sum of per-node shards', 'green', step=2, focus=2, size=13),
        stext(625, 70, 'Rules', 'amber', 13, step=3, bold=True),
        stext(540, 95, '• only UPDATE … SET c = c + n', '#e2e8f0', 11, 'start', step=3),
        stext(540, 115, '• no INSERT, cannot set a value', '#e2e8f0', 11, 'start', step=3),
        stext(540, 135, '• table: key columns + counters only', '#e2e8f0', 11, 'start', step=3),
        stext(540, 155, '• cannot use TTL', '#e2e8f0', 11, 'start', step=3),
        stext(380, 230, 'not idempotent: a retried increment may be counted twice', 'red', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 250, *elems), [
        'Many clients can increment the same counter at the same time on different coordinators.',
        'Each replica tracks its own share; the value read is the merged sum, so increments are never lost to last-write-wins.',
        'Counters have strict rules: only increments and decrements via UPDATE, a counter table holds only counters besides its key, and no TTL.',
        'An increment is <strong>not idempotent</strong>: if a write times out and the client retries, the count may be applied twice. Use counters for approximate metrics such as page views, not money.',
    ])


def batch_anim():
    elems = [
        stext(380, 24, 'BEGIN BATCH … APPLY BATCH', 'blue', 15, bold=True),
        sbox(20, 50, 340, 200, '', '', 'green', step=1, fill_opacity=0.08),
        stext(190, 70, 'Good: keep denormalised tables in sync', 'green', 12, step=1, bold=True),
        sbox(40, 85, 300, 34, 'INSERT INTO users_by_id …', '', 'green', step=1, size=11),
        sbox(40, 125, 300, 34, 'INSERT INTO users_by_email …', '', 'green', step=1, size=11),
        stext(190, 185, 'logged batch → batchlog on 2 nodes', 'green', 11, step=2, focus=2),
        stext(190, 203, 'all statements eventually applied', 'green', 11, step=2),
        stext(190, 230, '(atomic, but NOT isolated)', 'amber', 11, step=2),
        sbox(400, 50, 340, 200, '', '', 'red', step=3, fill_opacity=0.08),
        stext(570, 70, 'Bad: bulk loading many partitions', 'red', 12, step=3, bold=True),
        sbox(420, 85, 300, 90, 'BATCH of 5,000 rows', 'different partitions → one coordinator\nholds everything, then fans out', 'red', step=3, size=12),
        stext(570, 200, 'slower than async single writes', 'red', 11, step=4, focus=4, bold=True),
        stext(570, 220, 'UNLOGGED is fine for ONE partition', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 265, *elems), [
        'A <strong>logged batch</strong> groups writes that must all happen, typically the same data written to several denormalised tables.',
        'Cassandra first stores the batch in a <strong>batchlog</strong> on other nodes. If the coordinator dies, the batch is replayed, so all statements are eventually applied. Readers may still see a partial state (no isolation).',
        'Batches are <strong>not</strong> a bulk-load optimisation. A batch touching many partitions puts the entire load on one coordinator.',
        'For bulk loads use many concurrent single-partition writes. An unlogged batch is efficient only when all statements hit the <strong>same partition</strong>.',
    ])


# ================================================================== 5 Data modeling
def query_first_anim():
    elems = [
        stext(380, 24, 'Query-first modelling (Chebotko method)', 'blue', 15, bold=True),
        sbox(20, 50, 220, 205, '', '', 'gray', step=1, fill_opacity=0.06), stext(130, 70, '1. Application workflow', 'gray', 12, step=1, bold=True),
        stext(35, 98, 'Q1 student\'s marks, newest', '#e2e8f0', 11, 'start', step=1),
        stext(35, 118, 'Q2 toppers of an exam', '#e2e8f0', 11, 'start', step=1),
        stext(35, 138, 'Q3 attendance of a centre', '#e2e8f0', 11, 'start', step=1),
        stext(35, 158, '    on a day', '#e2e8f0', 11, 'start', step=1),
        sarrow(240, 150, 268, 150, 'gray', step=2),
        sbox(270, 50, 220, 205, '', '', 'amber', step=2, fill_opacity=0.08), stext(380, 70, '2. One table per query', 'amber', 12, step=2, bold=True),
        stext(285, 98, 'marks_by_student', '#fde68a', 11, 'start', step=2), stext(285, 114, '  ((roll), exam_date DESC)', '#e2e8f0', 10, 'start', step=2),
        stext(285, 140, 'marks_by_exam', '#fde68a', 11, 'start', step=2), stext(285, 156, '  ((exam), marks DESC, roll)', '#e2e8f0', 10, 'start', step=2),
        stext(285, 182, 'attendance_by_centre_day', '#fde68a', 11, 'start', step=2), stext(285, 198, '  ((centre, day), roll)', '#e2e8f0', 10, 'start', step=2),
        sarrow(490, 150, 518, 150, 'gray', step=3),
        sbox(520, 50, 220, 205, '', '', 'green', step=3, fill_opacity=0.08), stext(630, 70, '3. Check & optimise', 'green', 12, step=3, bold=True),
        stext(535, 98, '• each query = 1 partition', '#e2e8f0', 11, 'start', step=3),
        stext(535, 118, '• partitions < ~100 MB', '#e2e8f0', 11, 'start', step=3),
        stext(535, 138, '• no unbounded growth', '#e2e8f0', 11, 'start', step=3),
        stext(535, 158, '• writes fan out to all copies', '#e2e8f0', 11, 'start', step=3),
        stext(380, 285, 'data is duplicated on purpose: disk is cheap, cross-node reads are not', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Start from the <strong>application workflow</strong>: list every screen or report and the exact query it needs (what is given, what is returned, in which order).',
        'Design <strong>one table per query</strong>: the given values become the partition key, the required order becomes clustering columns.',
        'Check every table: one partition per query, bounded partition size, and the cost of writing the same fact to several tables.',
        'Denormalisation is intentional. Storage is cheap; reading across many nodes is what makes queries slow.',
    ])


def denorm_anim():
    elems = [
        stext(380, 24, 'One fact, written to two tables', 'blue', 15, bold=True),
        sbox(270, 45, 220, 45, 'App: new student registers', '', 'gray', step=1, size=12),
        sarrow(330, 90, 230, 115, 'green', step=2), sarrow(430, 90, 530, 115, 'green', step=2),
        stext(380, 118, 'logged BATCH', 'amber', 11, step=2, bold=True),
        _part(40, 140, 320, '2405', ['email · name · course'], 'green', step=2, kw=90, title='students_by_roll'),
        _part(400, 140, 340, 'riya@cdac.in', ['roll 2405 · name'], 'blue', step=2, kw=120, title='students_by_email'),
        stext(200, 205, 'profile page: WHERE roll_no = ?', 'green', 11, step=3),
        stext(570, 205, 'login: WHERE email = ?', 'blue', 11, step=3),
        stext(380, 245, 'both reads hit exactly one partition', 'cyan', 12, step=3, focus=3, bold=True),
        stext(380, 270, 'changing the email = delete old row + insert new row (in a batch)', 'amber', 11, step=4, focus=4),
    ]
    return anim(canvas(760, 285, *elems), [
        'A student registers once, but the application looks students up in two ways: by roll number and by email.',
        'The application writes the same data to two tables, each keyed for one lookup, together in a logged batch so both eventually succeed.',
        'Each read is now a single-partition lookup, however large the tables get.',
        'The price is on updates: changing a key value (the email) means deleting the old row and inserting a new one, and the application owns that consistency.',
    ])


def hot_partition_anim():
    elems = [
        stext(380, 24, 'Hot and large partitions, and how bucketing fixes them', 'blue', 14, bold=True),
        _node(100, 110, 'N1', 'gray', step=1), _node(200, 110, 'N2', 'red', step=1, focus=1, r=30, sub='90% of traffic'), _node(300, 110, 'N3', 'gray', step=1),
        stext(200, 175, "partition 'all_logins'", 'red', 11, step=1, bold=True),
        stext(200, 195, 'too big (GBs), too busy', 'red', 11, step=2, focus=2),
        sbox(420, 50, 320, 45, "((event_type, day, bucket))", '', 'green', step=3, size=12),
        stext(580, 112, 'bucket = hash(user_id) % 8', 'green', 11, step=3),
        _node(470, 160, 'N1', 'green', step=4), _node(540, 160, 'N2', 'green', step=4), _node(610, 160, 'N3', 'green', step=4), _node(680, 160, 'N4', 'green', step=4),
        stext(580, 210, 'load spread evenly', 'green', 11, step=4, bold=True),
        stext(380, 245, 'guideline: < 100 MB and < 100,000 rows per partition', 'amber', 12, step=5, focus=5, bold=True),
        stext(380, 268, 'reads then query the buckets (in parallel) and merge', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'If many writes share one partition key (e.g. one global "all_logins" partition), all of them go to the same few replicas: a <strong>hot partition</strong>.',
        'The partition also grows very large, making reads, compaction and repair slow, and it can never be split across nodes.',
        'The fix is to add more to the partition key: a <strong>time bucket</strong> (day, hour) and/or a <strong>synthetic bucket</strong> number computed from another field.',
        'Writes are now spread over many partitions and therefore over all nodes.',
        'Keep partitions bounded (a common rule of thumb: under 100 MB and 100,000 rows). Reads ask each bucket in parallel and combine the results.',
    ])


def timeseries_anim():
    elems = [
        stext(380, 24, 'Time-series: ((sensor, day), ts DESC) + TTL + TWCS', 'blue', 14, bold=True),
        _part(30, 50, 330, 'lab-1 · 10-14', ['10:10 · 25.9', '10:05 · 25.3', '10:00 · 24.5'], 'green', step=1, kw=110),
        _part(400, 50, 330, 'lab-1 · 10-13', ['23:55 · 23.1', '…'], 'gray', step=1, kw=110),
        stext(195, 145, 'latest N: LIMIT N (stored first)', 'green', 11, step=2, focus=2, bold=True),
        stext(195, 163, 'range: ts >= … AND ts < …', 'green', 11, step=2),
        sbox(30, 185, 330, 45, 'default_time_to_live = 30 days', 'old data expires automatically', 'purple', step=3, size=12),
        sbox(400, 185, 330, 45, 'TimeWindowCompactionStrategy', 'whole SSTables dropped when expired', 'amber', step=4, size=12),
        stext(380, 265, 'write-once, read-recent, expire-old: Cassandra\'s favourite workload', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'Time-series data is partitioned by source <strong>and</strong> time bucket, with the timestamp as a descending clustering column.',
        'The latest readings are the first rows of today\'s partition (<code>LIMIT N</code>). Time ranges are contiguous slices.',
        'A table-level TTL removes old readings automatically after the retention period.',
        '<strong>TWCS</strong> groups SSTables by time window; once a whole window has expired, its files are dropped without rewriting, avoiding tombstone overhead.',
        'Append-only writes, recent reads and age-based expiry are exactly the pattern Cassandra handles best (IoT, logs, metrics, events).',
    ])


def mv_anim():
    elems = [
        stext(380, 24, 'Materialized view: the server maintains a second table', 'blue', 14, bold=True),
        _part(30, 55, 320, '2401', ['Anuj · Pune'], 'green', step=1, kw=80, title='base: students (roll_no)'),
        sarrow(350, 75, 410, 75, 'amber', step=2),
        _part(410, 55, 320, 'Pune', ['2401 · Anuj', '2408 · Kiran'], 'blue', step=2, kw=80, title='view: students_by_city ((city), roll_no)'),
        stext(380, 150, 'every base write → read old row → update view (async)', 'amber', 11, step=2, focus=2),
        sbox(30, 175, 700, 50, 'Disabled by default since 4.0 (materialized_views_enabled: false) · experimental', '', 'red', step=3, focus=3, size=12),
        stext(380, 250, 'views can drift out of sync with no easy repair → prefer app-managed tables or SAI', 'pink', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 270, *elems), [
        'A materialized view is defined as a SELECT on a base table with a <strong>different primary key</strong>.',
        'On every base-table write, Cassandra reads the old row and updates the view in the background, maintaining the denormalised copy for you.',
        'Because of known consistency problems, views are <strong>experimental</strong> and disabled by default since Cassandra 4.0.',
        'A view can silently diverge from its base table and there is no reliable tool to detect it. Most teams write the second table from the application (with batches) or use SAI.',
    ])


# ================================================================== 6 Internals
def write_path_anim():
    elems = [
        stext(380, 24, 'Write path on one replica', 'blue', 15, bold=True),
        sbox(20, 55, 140, 50, 'write arrives', '', 'gray', step=1, size=12),
        sarrow(160, 80, 215, 65, 'amber', step=2), sarrow(160, 80, 215, 130, 'green', step=2),
        sbox(215, 45, 230, 45, 'Commit log (disk)', 'append-only, sequential', 'amber', step=2, size=12),
        sbox(215, 110, 230, 45, 'Memtable (memory)', 'sorted by key', 'green', step=2, focus=2, size=12),
        stext(330, 178, '→ acknowledge to coordinator', 'green', 11, step=3, bold=True),
        sarrow(445, 132, 510, 132, 'blue', step=4),
        sbox(510, 110, 230, 45, 'flush → SSTable', 'immutable, sorted file', 'blue', step=4, focus=4, size=12),
        sbox(510, 175, 110, 34, 'SSTable 1', '', 'blue', step=5, size=11), sbox(630, 175, 110, 34, 'SSTable 2', '', 'blue', step=5, size=11),
        sbox(510, 220, 230, 34, 'compaction merges them', '', 'purple', step=5, size=11),
        stext(240, 240, 'no read before write, no in-place update', 'cyan', 12, step=6, focus=6, bold=True),
        stext(240, 260, '→ writes are very fast', 'cyan', 12, step=6),
    ]
    return anim(canvas(760, 275, *elems), [
        'A replica receives a write from the coordinator.',
        'It appends the mutation to the <strong>commit log</strong> on disk (for durability) and applies it to the in-memory <strong>memtable</strong>.',
        'At that point the write is acknowledged; nothing else needs to happen synchronously.',
        'When a memtable is full, it is <strong>flushed</strong> to disk as an immutable, sorted <strong>SSTable</strong>, and the matching commit-log segments are freed.',
        'Over time many SSTables accumulate; background <strong>compaction</strong> merges them, keeping the newest version of each cell and dropping purgeable tombstones.',
        'Every write is a sequential append with no read-before-write and no random in-place update, which is why Cassandra writes are so fast.',
    ])


def read_path_anim():
    elems = [
        stext(380, 24, 'Read path on one replica', 'blue', 15, bold=True),
        sbox(20, 50, 150, 40, 'read key 2401', '', 'gray', step=1, size=12),
        sbox(200, 50, 160, 40, 'Memtable', '', 'green', step=1, size=12),
        sbox(20, 110, 150, 40, 'Row cache?', '(off by default)', 'gray', step=2, size=11),
        sbox(200, 110, 160, 40, 'Bloom filter', 'SSTable 1: maybe', 'amber', step=3, focus=3, size=11),
        sbox(380, 110, 160, 40, 'Bloom filter', 'SSTable 2: no → skip', 'red', step=3, size=11),
        sbox(200, 170, 160, 40, 'Key cache / index', 'partition offset', 'purple', step=4, size=11),
        sarrow(280, 210, 280, 232, 'gray', step=4),
        sbox(200, 232, 160, 34, 'read SSTable 1', '', 'blue', step=4, size=11),
        sbox(560, 110, 180, 100, 'Merge by timestamp', 'memtable + SSTables\nnewest cell wins,\ntombstones hide data', 'green', step=5, focus=5, size=12),
        stext(560, 245, 'fewer SSTables per read = faster', 'cyan', 12, step=6, focus=6, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'A replica checks the <strong>memtable</strong> for the newest, not-yet-flushed data.',
        'If a row cache is enabled it may answer immediately; it is off by default.',
        'For each SSTable, an in-memory <strong>Bloom filter</strong> says "definitely not here" or "maybe here", so most files that lack the key are skipped without disk I/O.',
        'For candidate SSTables, the key cache or partition index gives the exact offset of the partition in the data file.',
        'The pieces from the memtable and SSTables are <strong>merged</strong>: for each cell the newest timestamp wins, and tombstones hide deleted data.',
        'The more SSTables a partition is spread over, the slower the read. Compaction strategy choice directly affects read latency.',
    ])


def compaction_anim():
    elems = [
        stext(380, 24, 'Compaction strategies', 'blue', 15, bold=True),
        sbox(20, 50, 175, 215, '', '', 'blue', step=1, fill_opacity=0.08), stext(107, 70, 'STCS', 'blue', 13, step=1, bold=True),
        stext(107, 90, 'size-tiered', 'blue', 11, step=1),
        scell(35, 105, 40, 20, '', '#0ea5e9', step=1), scell(80, 105, 40, 20, '', '#0ea5e9', step=1), scell(125, 105, 40, 20, '', '#0ea5e9', step=1),
        scell(45, 140, 110, 26, 'merged', '#0369a1', '#fff', step=1, size=10),
        stext(107, 195, 'write-heavy', '#e2e8f0', 11, step=1), stext(107, 213, 'needs 50% spare disk', '#e2e8f0', 10, step=1),
        sbox(205, 50, 175, 215, '', '', 'green', step=2, fill_opacity=0.08), stext(292, 70, 'LCS', 'green', 13, step=2, bold=True),
        stext(292, 90, 'leveled', 'green', 11, step=2),
        scell(220, 105, 145, 18, 'L0', '#10b981', '#fff', step=2, size=10), scell(220, 127, 145, 18, 'L1 ×10', '#059669', '#fff', step=2, size=10),
        scell(220, 149, 145, 18, 'L2 ×100', '#047857', '#fff', step=2, size=10),
        stext(292, 195, 'read-heavy, updates', '#e2e8f0', 11, step=2), stext(292, 213, '~1 SSTable per read', '#e2e8f0', 10, step=2),
        sbox(390, 50, 175, 215, '', '', 'amber', step=3, fill_opacity=0.08), stext(477, 70, 'TWCS', 'amber', 13, step=3, bold=True),
        stext(477, 90, 'time-window', 'amber', 11, step=3),
        scell(405, 105, 45, 26, 'Mon', '#f59e0b', '#fff', step=3, size=10), scell(455, 105, 45, 26, 'Tue', '#f59e0b', '#fff', step=3, size=10),
        scell(505, 105, 45, 26, 'Wed', '#f59e0b', '#fff', step=3, size=10),
        stext(477, 195, 'time-series + TTL', '#e2e8f0', 11, step=3), stext(477, 213, 'drop whole windows', '#e2e8f0', 10, step=3),
        sbox(575, 50, 165, 215, '', '', 'purple', step=4, fill_opacity=0.08), stext(657, 70, 'UCS (5.0)', 'purple', 13, step=4, bold=True),
        stext(657, 90, 'unified', 'purple', 11, step=4),
        stext(657, 120, 'tunable between', '#e2e8f0', 10, step=4), stext(657, 136, 'tiered and leveled', '#e2e8f0', 10, step=4),
        stext(657, 195, 'new default choice', '#e2e8f0', 11, step=4), stext(657, 213, 'sharded, parallel', '#e2e8f0', 10, step=4),
        stext(380, 290, 'choose by workload: write-heavy · read/update-heavy · time-series', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        '<strong>Size-Tiered (STCS)</strong>, the classic default, merges SSTables of similar size. Cheap for writes, but a row can be spread over many files and a big compaction needs lots of free disk.',
        '<strong>Leveled (LCS)</strong> keeps SSTables in levels with non-overlapping ranges, so a read usually touches one file. It costs more I/O on writes, so it suits read-heavy or update-heavy tables.',
        '<strong>Time-Window (TWCS)</strong> compacts data per time window and drops whole windows when their TTL expires, which suits time-series data.',
        '<strong>Unified (UCS)</strong>, added in Cassandra 5.0, can be tuned to behave like either tiered or leveled compaction and runs compactions in parallel shards.',
        'Compaction is chosen per table: <code>ALTER TABLE … WITH compaction = {…}</code>.',
    ])


def token_ring_anim():
    labels = ['A', 'B', 'C', 'D']
    subs = {0: '-4.6e18', 1: '0', 2: '4.6e18', 3: '9.2e18'}
    elems = [
        stext(380, 24, 'Murmur3: partition key → token → node', 'blue', 15, bold=True),
        _ring(200, 150, 95, labels, 'blue', step=1, subs=subs),
        sbox(400, 50, 340, 40, "partition key: roll_no = 2401", '', 'gray', step=2, size=12),
        sarrow(570, 90, 570, 112, 'gray', step=2),
        sbox(400, 112, 340, 40, 'Murmur3 hash → 6330071308978448828', '', 'amber', step=2, focus=2, size=12),
        stext(570, 180, 'token range (4.6e18, 9.2e18] → node D', 'green', 12, step=3, focus=3, bold=True),
        _node(200 + 95 * math.cos(math.radians(145)), 150 + 95 * math.sin(math.radians(145)), '', 'amber', step=3, focus=3, r=9),
        stext(95, 240, 'token 6.33e18', 'amber', 11, step=3, bold=True),
        stext(570, 210, 'replicas: D, then next nodes clockwise', 'green', 11, step=4),
        stext(570, 245, 'vnodes: each node owns many small ranges', 'purple', 12, step=5, focus=5, bold=True),
        stext(570, 265, '(num_tokens = 16 by default in 4.0+)', 'purple', 11, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'The token space of the Murmur3Partitioner runs from -2<sup>63</sup> to 2<sup>63</sup>-1 and is arranged as a ring. Each node owns the range from the previous node\'s token (exclusive) up to its own token (inclusive).',
        'The partition key is hashed with Murmur3 into a 64-bit <strong>token</strong>. Roll number 2401 hashes to 6330071308978448828.',
        'The token 6.33×10<sup>18</sup> is greater than C\'s token (4.6×10<sup>18</sup>) and not greater than D\'s (9.2×10<sup>18</sup>), so it falls in D\'s range and D holds the first replica.',
        'Further replicas (RF > 1) go to the next nodes on the ring, subject to the DC and rack rules of the replication strategy.',
        'With <strong>virtual nodes</strong>, every node owns many small ranges spread around the ring, so adding or removing a node moves data evenly from or to all others.',
    ])


def sstable_anim():
    elems = [
        stext(380, 24, 'An SSTable is a set of immutable files', 'blue', 15, bold=True),
        sbox(20, 50, 300, 220, '', '', 'blue', step=1, fill_opacity=0.08),
        stext(170, 70, 'oa-12-big-*  (one SSTable)', 'blue', 12, step=1, bold=True),
        scell(35, 85, 270, 26, 'Data.db  — rows, sorted by token', '#0ea5e9', '#fff', step=1, size=11),
        scell(35, 115, 270, 26, 'Index.db / Partitions.db — key → offset', '#1e40af', '#fff', step=2, size=11),
        scell(35, 145, 270, 26, 'Summary.db — sample of the index', '#1e40af', '#fff', step=2, size=11),
        scell(35, 175, 270, 26, 'Filter.db — Bloom filter', '#b45309', '#fff', step=2, focus=2, size=11),
        scell(35, 205, 270, 26, 'Statistics.db — min/max ts, tombstones', '#6d28d9', '#fff', step=3, size=11),
        scell(35, 235, 270, 26, 'CompressionInfo.db · Digest · TOC', '#334155', step=3, size=11),
        sbox(360, 60, 380, 60, 'Immutable: never modified after flush', 'updates & deletes = new data in newer SSTables', 'green', step=4, focus=4, size=12),
        sbox(360, 135, 380, 60, 'Easy snapshots & backups', 'nodetool snapshot = hard links to the files', 'purple', step=5, size=12),
        sbox(360, 210, 380, 60, 'Cost: data spread across files', 'compaction rewrites them into fewer', 'amber', step=5, size=12),
    ]
    return anim(canvas(760, 285, *elems), [
        'A <strong>Sorted String Table</strong> is the on-disk format: the Data file holds partitions sorted by token, and rows sorted by clustering key inside them.',
        'Helper components make lookups fast: the partition index (BTI <code>Partitions.db</code> in 5.0), its summary, and the <strong>Bloom filter</strong> that skips files without the key.',
        'Statistics record min/max timestamps, tombstone counts and more; data is compressed in chunks (LZ4 by default).',
        'SSTables are <strong>immutable</strong>. An update or delete never edits a file; it writes newer data, and reads reconcile by timestamp.',
        'Immutability makes snapshots instant (hard links) but spreads a row over several files, which compaction later merges.',
    ])


# ================================================================== 7 Distribution & consistency
def replication_anim():
    labels = ['N1', 'N2', 'N3', 'N4', 'N5', 'N6']
    elems = [
        stext(380, 24, "RF = 3 with NetworkTopologyStrategy (3 racks)", 'blue', 15, bold=True),
        _ring(220, 165, 100, labels, 'blue', step=1, subs={0: 'rack1', 1: 'rack1', 2: 'rack2', 3: 'rack2', 4: 'rack3', 5: 'rack3'}),
        sbox(440, 50, 300, 40, 'token of partition → owner N1', '', 'amber', step=2, size=12),
        sbox(440, 100, 300, 40, 'N2 is rack1 again → skipped', '', 'red', step=3, size=12),
        sbox(440, 150, 300, 40, 'replicas: N1 (r1), N3 (r2), N5 (r3)', '', 'green', step=4, focus=4, size=12),
        stext(590, 220, 'a whole rack can fail, data stays available', 'green', 11, step=5, bold=True),
        stext(590, 245, 'RF = copies, not nodes: 6 nodes, 3 copies', 'cyan', 11, step=5),
    ]
    return anim(canvas(760, 290, *elems), [
        'Six nodes in one data centre, two in each of three racks. The keyspace uses <code>NetworkTopologyStrategy</code> with RF 3.',
        'The partition\'s token makes N1 the primary owner, so N1 gets the first replica.',
        'Walking clockwise, N2 is in the same rack as N1, so the strategy skips it to avoid two copies in one failure domain.',
        'It continues until it has three replicas in three different racks: N1, N3 and N5.',
        'Losing a whole rack still leaves two copies, and each node stores roughly half the data (6 nodes, 3 copies).',
    ])


def consistency_anim():
    elems = [
        stext(380, 24, 'Consistency level = replicas that must answer', 'blue', 15, bold=True),
        sbox(20, 45, 130, 40, 'Coordinator', '', 'gray', step=1, size=12),
        _node(260, 70, 'R1', 'green', step=1), _node(260, 140, 'R2', 'green', step=1), _node(260, 210, 'R3', 'gray', step=1),
        sarrow(150, 65, 236, 70, 'green', step=1), sarrow(150, 70, 236, 135, 'green', step=1), sarrow(150, 75, 236, 200, 'gray', step=1),
        stext(560, 60, 'RF = 3', 'gray', 13, step=1, bold=True),
        stext(400, 90, 'ONE', 'amber', 12, 'start', step=2, bold=True), stext(510, 90, '1 replica: fastest, may be stale', '#e2e8f0', 11, 'start', step=2),
        stext(400, 115, 'QUORUM', 'green', 12, 'start', step=3, bold=True), stext(510, 115, '2 of 3 (floor(RF/2)+1)', '#e2e8f0', 11, 'start', step=3),
        stext(400, 140, 'LOCAL_QUORUM', 'green', 12, 'start', step=3, bold=True), stext(510, 140, 'quorum in my DC only', '#e2e8f0', 11, 'start', step=3),
        stext(400, 165, 'ALL', 'red', 12, 'start', step=2, bold=True), stext(510, 165, '3 of 3: any node down = fail', '#e2e8f0', 11, 'start', step=2),
        sbox(20, 240, 720, 45, 'Write QUORUM (2) + Read QUORUM (2) = 4 > RF 3  →  read always overlaps the latest write', '', 'cyan', step=4, focus=4, size=12),
    ]
    return anim(canvas(760, 300, *elems), [
        'The coordinator always sends the request to all replicas that are up; the <strong>consistency level</strong> says how many must reply before it answers the client.',
        '<strong>ONE</strong> is fastest and most available but can read stale data. <strong>ALL</strong> is strongest but fails if any replica is down.',
        '<strong>QUORUM</strong> needs a majority (2 of 3). <strong>LOCAL_QUORUM</strong> counts only the local data centre, which avoids cross-DC latency and is the usual production choice.',
        'If writes + reads together touch more replicas than RF (W + R > RF), every read overlaps at least one replica with the latest write: strong consistency.',
    ])


def repair_anim():
    elems = [
        stext(380, 24, 'How replicas get back in sync', 'blue', 15, bold=True),
        sbox(20, 50, 230, 210, '', '', 'amber', step=1, fill_opacity=0.08), stext(135, 70, '1. Hinted handoff', 'amber', 12, step=1, bold=True),
        _node(70, 120, 'C', 'gray', step=1), _node(190, 120, 'R3', 'red', step=1, sub='down'),
        stext(135, 175, 'coordinator stores a hint', '#e2e8f0', 11, step=1), stext(135, 193, 'replays it when R3 returns', '#e2e8f0', 11, step=1),
        stext(135, 220, '(hints kept 3 hours)', '#94a3b8', 10, step=1),
        sbox(265, 50, 230, 210, '', '', 'green', step=2, fill_opacity=0.08), stext(380, 70, '2. Read repair', 'green', 12, step=2, bold=True),
        _node(320, 120, 'R1', 'green', step=2, sub='85 @t2'), _node(440, 120, 'R2', 'red', step=2, sub='78 @t1'),
        stext(380, 175, 'digests differ during a read', '#e2e8f0', 11, step=2), stext(380, 193, 'newest value written back', '#e2e8f0', 11, step=2),
        sbox(510, 50, 230, 210, '', '', 'purple', step=3, fill_opacity=0.08), stext(625, 70, '3. Anti-entropy repair', 'purple', 12, step=3, bold=True),
        stext(625, 105, 'nodetool repair -pr', '#e2e8f0', 11, step=3), stext(625, 130, 'Merkle trees compare', '#e2e8f0', 11, step=3),
        stext(625, 148, 'ranges, stream the diff', '#e2e8f0', 11, step=3), stext(625, 180, 'incremental repair', '#e2e8f0', 11, step=3),
        stext(625, 198, 'only unrepaired data', '#e2e8f0', 11, step=3),
        stext(380, 285, 'run full repair on every node within gc_grace_seconds (e.g. weekly)', 'red', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        '<strong>Hinted handoff</strong>: if a replica is down during a write, the coordinator stores a hint and delivers it when the node comes back (within max_hint_window, 3 hours by default).',
        '<strong>Read repair</strong>: when a read at QUORUM finds replicas that disagree, the coordinator returns the newest value and writes it to the stale replicas.',
        '<strong>Anti-entropy repair</strong> (<code>nodetool repair</code>) builds Merkle trees of token ranges on each replica, compares them and streams only the differences. Incremental repair skips data already repaired.',
        'Hints and read repair are best-effort. Regular repair is mandatory: every range must be repaired within gc_grace_seconds, or deletes may be resurrected.',
    ])


def gossip_anim():
    labels = ['N1', 'N2', 'N3', 'N4', 'N5']
    elems = [
        stext(380, 24, 'Gossip, failure detection and adding a node', 'blue', 15, bold=True),
        _ring(200, 160, 95, labels, 'blue', step=1, colors={0: 'green'}),
        sflow(200, 65, 290, 130, 'green', step=1, count=2), sflow(200, 65, 144, 237, 'green', step=1, count=2),
        stext(200, 280, 'each second: exchange state with up to 3 peers', 'green', 11, step=1),
        sbox(410, 50, 330, 45, 'Seed nodes', 'contact points for joining nodes, not masters', 'amber', step=2, size=12),
        sbox(410, 105, 330, 45, 'Phi accrual failure detector', 'marks a node DOWN when heartbeats stop', 'red', step=3, focus=3, size=12),
        sbox(410, 160, 330, 45, 'Bootstrap N6', 'takes token ranges, streams data from peers', 'green', step=4, focus=4, size=12),
        sbox(410, 215, 330, 45, 'Decommission / removenode', 'hands ranges to the remaining nodes', 'purple', step=5, size=12),
    ]
    return anim(canvas(760, 295, *elems), [
        'Nodes share membership and status with the <strong>gossip</strong> protocol: every second each node exchanges versioned state with up to three others, so news reaches the whole cluster quickly.',
        '<strong>Seed nodes</strong> are just well-known contact points for nodes joining the cluster; they are not masters.',
        'The <strong>phi accrual failure detector</strong> watches heartbeat arrival times and marks a node down when it is unlikely to be alive, so coordinators stop routing to it.',
        'A new node <strong>bootstraps</strong>: it picks token ranges and streams the matching data from existing replicas before serving reads.',
        'Removing a node (<code>nodetool decommission</code>, or <code>removenode</code> for a dead one) streams its ranges to the remaining nodes.',
    ])


def lwt_anim():
    elems = [
        stext(380, 24, 'Lightweight transaction: INSERT … IF NOT EXISTS (Paxos)', 'blue', 14, bold=True),
        sbox(20, 55, 150, 40, 'Coordinator', '', 'gray', step=1, size=12),
        _node(300, 75, 'R1', 'blue', step=1), _node(400, 75, 'R2', 'blue', step=1), _node(500, 75, 'R3', 'blue', step=1),
        sbox(20, 125, 720, 30, '1. Prepare / promise (ballot)', '', 'blue', step=1, size=12),
        sbox(20, 160, 720, 30, '2. Read current value, check the IF condition', '', 'amber', step=2, focus=2, size=12),
        sbox(20, 195, 720, 30, '3. Propose / accept the new value', '', 'green', step=3, size=12),
        sbox(20, 230, 720, 30, '4. Commit', '', 'purple', step=3, size=12),
        stext(380, 285, '≈ 4 round trips: use only where a race really matters (unique username, seat booking)', 'red', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'A conditional write (<code>IF NOT EXISTS</code>, <code>IF col = value</code>, <code>IF EXISTS</code>) runs the <strong>Paxos</strong> consensus protocol among the partition\'s replicas, starting with a prepare/promise round.',
        'The current value is read at SERIAL consistency and the condition is evaluated. If it fails, the client gets <code>[applied] = False</code> plus the current values.',
        'If it holds, the new value is proposed, accepted by a quorum and committed: a linearizable compare-and-set.',
        'This costs several round trips (Cassandra 5.0\'s Paxos v2 reduces them), so use LWTs for real race conditions like unique registrations, not for every write.',
    ])


# ================================================================== 8 Scenarios & ecosystem
def exam_schema_anim():
    elems = [
        stext(380, 24, 'Online exam platform: three queries, three tables', 'blue', 14, bold=True),
        _part(20, 55, 350, '2401', ['2026-10-14 · SQL · 82', '2026-10-05 · Spark · 84'], 'green', step=1, kw=70, title='Q1 results_by_student'),
        _part(390, 55, 350, 'SQL-2026-10', ['97 · 2417 · Meera', '91 · 2402 · Aarshvi'], 'amber', step=2, kw=110, title='Q2 results_by_exam (marks DESC)'),
        _part(20, 160, 720, "('SQL-2026-10', 2401)", ['10:00:03 · login · 10.0.4.17', '10:14:51 · tab_switch', '10:15:02 · answer q12'], 'purple', step=3, kw=180, title='Q3 events_by_attempt ((exam, roll), event_time)'),
        stext(380, 285, 'one exam submit = logged BATCH into Q1 + Q2 tables; events written with TTL', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Q1, a student\'s result history (newest first): partition by roll number, cluster by exam date descending.',
        'Q2, the merit list of an exam: partition by exam, cluster by marks descending (then roll number so ties stay unique).',
        'Q3, the proctoring timeline of one attempt: partition by (exam, roll), cluster by event time. One partition holds one attempt\'s events, so size is bounded.',
        'Submitting a result writes Q1 and Q2 together in a logged batch. High-volume proctoring events get a TTL so they expire after the retention period.',
    ])


def chat_anim():
    elems = [
        stext(380, 24, 'Messaging: ((conversation_id, month), message_id timeuuid DESC)', 'blue', 14, bold=True),
        _part(20, 55, 450, "('dbda-group', '2026-10')", ['11:42 · Aarshvi: notes uploaded', '11:40 · Anuj: thanks!', '11:31 · Vineeta: lab at 2 pm'], 'green', step=1, kw=170),
        stext(245, 150, 'newest first → open chat = LIMIT 50', 'green', 11, step=2, focus=2, bold=True),
        sbox(500, 55, 240, 75, 'timeuuid = time + uniqueness', 'sorts by time, no collisions\nfrom two senders', 'amber', step=3, size=12),
        sbox(20, 175, 450, 45, "scroll up: WHERE message_id < <oldest seen> LIMIT 50", '', 'blue', step=4, size=12),
        sbox(500, 150, 240, 70, 'month bucket', 'bounded partitions for\nyears-long chats', 'purple', step=5, size=12),
        stext(380, 260, 'inbox list = another table: conversations_by_user ((user), last_msg_time DESC)', 'cyan', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'Each conversation-month is a partition, and messages inside it are ordered by a time-based <strong>timeuuid</strong>, newest first.',
        'Opening a chat reads the first 50 rows of the current partition: one sequential read.',
        'A timeuuid encodes the creation time and a unique node/clock part, so two messages in the same millisecond never overwrite each other.',
        'Scrolling back uses the last seen id as a cursor (<code>message_id &lt; …</code>), a cheap slice of the same partition.',
        'Monthly buckets keep partitions bounded; the inbox (latest conversation first) is a separate table maintained on every send.',
    ])


def pipeline_anim():
    elems = [
        stext(380, 24, 'Cassandra in a data engineering pipeline', 'blue', 15, bold=True),
        sbox(20, 60, 140, 50, 'Apps / IoT', '', 'gray', step=1, size=12),
        sbox(190, 60, 140, 50, 'Kafka', 'events', 'amber', step=1, size=12),
        sbox(360, 60, 160, 50, 'Kafka Connect /', 'Spark Streaming', 'purple', step=2, size=11),
        sbox(550, 60, 190, 50, 'Cassandra', 'serving store (ms reads)', 'green', step=2, focus=2, size=12),
        sarrow(160, 85, 188, 85, 'gray', step=1), sarrow(330, 85, 358, 85, 'amber', step=2), sarrow(520, 85, 548, 85, 'purple', step=2),
        sbox(550, 150, 190, 50, 'Spark + Cassandra', 'connector: batch analytics', 'blue', step=3, size=11),
        sarrow(645, 110, 645, 148, 'blue', step=3),
        sbox(300, 150, 200, 50, 'Data lake / warehouse', 'Parquet, Iceberg', 'cyan', step=3, size=11),
        sarrow(548, 175, 502, 175, 'blue', step=3),
        sbox(20, 150, 230, 50, 'CDC (commit log)', '→ Debezium → Kafka', 'pink', step=4, size=11),
        stext(380, 250, 'Cassandra = fast operational store; analytics happen in Spark/warehouse', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 270, *elems), [
        'Events from applications and devices are published to <strong>Kafka</strong>.',
        'A Kafka Connect Cassandra sink (or a Spark Structured Streaming job) writes them into Cassandra tables designed for the serving queries.',
        'The <strong>Spark Cassandra Connector</strong> reads whole tables in parallel, token range by token range, for batch analytics and for exporting to the lake or warehouse.',
        'Cassandra\'s <strong>CDC</strong> feature exposes commit-log segments, which tools like Debezium turn into change events for downstream systems.',
        'The typical split: Cassandra serves high-volume, low-latency reads and writes; heavy aggregations and joins run in Spark or a warehouse.',
    ])


def troubleshoot_anim():
    elems = [
        stext(380, 24, 'Troubleshooting a slow Cassandra table', 'blue', 15, bold=True),
        sbox(20, 50, 230, 50, 'Symptom', 'read timeouts, high p99', 'red', step=1, size=12),
        sarrow(250, 75, 278, 75, 'gray', step=2),
        sbox(280, 50, 460, 50, 'nodetool tablehistograms cdac.results', 'partition size, SSTables per read, latency percentiles', 'amber', step=2, size=11),
        sbox(20, 125, 230, 45, 'Large partition?', 'warning in system.log', 'purple', step=3, size=11),
        sbox(265, 125, 230, 45, 'Tombstones?', 'tombstone_warn_threshold', 'purple', step=3, size=11),
        sbox(510, 125, 230, 45, 'Many SSTables/read?', 'compaction behind', 'purple', step=3, size=11),
        sbox(20, 190, 230, 45, 'bucket the key', '', 'green', step=4, size=12),
        sbox(265, 190, 230, 45, 'avoid deletes / use TWCS', '', 'green', step=4, size=12),
        sbox(510, 190, 230, 45, 'LCS/UCS, check compaction', '', 'green', step=4, size=12),
        stext(380, 270, 'most performance problems are data-model problems', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'Start from a measurable symptom: timeouts in the application, high p99 latency in metrics.',
        '<code>nodetool tablestats</code> and <code>tablehistograms</code> show partition sizes, SSTables per read, tombstones per slice and latency percentiles for the suspect table.',
        'The usual culprits: an oversized or hot partition, reads scanning many tombstones, or compaction falling behind so each read touches many SSTables.',
        'Each has a known fix: bucket the partition key, change the delete pattern (or use TTL + TWCS), or change the compaction strategy and its throughput.',
        'In practice most Cassandra performance problems come from the data model, so check the model before tuning JVM or hardware.',
    ])


def compare_anim():
    elems = [
        stext(380, 24, 'Choosing among wide-column and NoSQL stores', 'blue', 15, bold=True),
        sbox(20, 50, 175, 125, '', '', 'green', step=1, fill_opacity=0.08), stext(107, 70, 'Cassandra', 'green', 13, step=1, bold=True),
        stext(107, 95, 'masterless ring', '#e2e8f0', 11, step=1), stext(107, 113, 'multi-DC built in', '#e2e8f0', 11, step=1),
        stext(107, 131, 'AP, tunable', '#e2e8f0', 11, step=1), stext(107, 149, 'huge write volume', '#e2e8f0', 11, step=1),
        sbox(205, 50, 175, 125, '', '', 'amber', step=2, fill_opacity=0.08), stext(292, 70, 'HBase', 'amber', 13, step=2, bold=True),
        stext(292, 95, 'master + RegionServers', '#e2e8f0', 11, step=2), stext(292, 113, 'on HDFS + ZooKeeper', '#e2e8f0', 11, step=2),
        stext(292, 131, 'CP, strong consistency', '#e2e8f0', 11, step=2), stext(292, 149, 'Hadoop ecosystem', '#e2e8f0', 11, step=2),
        sbox(390, 50, 175, 125, '', '', 'blue', step=3, fill_opacity=0.08), stext(477, 70, 'MongoDB', 'blue', 13, step=3, bold=True),
        stext(477, 95, 'documents (JSON)', '#e2e8f0', 11, step=3), stext(477, 113, 'rich queries, indexes', '#e2e8f0', 11, step=3),
        stext(477, 131, 'primary per replica set', '#e2e8f0', 11, step=3), stext(477, 149, 'general app data', '#e2e8f0', 11, step=3),
        sbox(575, 50, 165, 125, '', '', 'purple', step=4, fill_opacity=0.08), stext(657, 70, 'DynamoDB', 'purple', 13, step=4, bold=True),
        stext(657, 95, 'AWS managed', '#e2e8f0', 11, step=4), stext(657, 113, 'same Dynamo ideas', '#e2e8f0', 11, step=4),
        stext(657, 131, 'pay per request', '#e2e8f0', 11, step=4), stext(657, 149, 'AWS lock-in', '#e2e8f0', 11, step=4),
        stext(380, 205, 'pick by access pattern, consistency need, ecosystem and operations team', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 225, *elems), [
        '<strong>Cassandra</strong>: peer-to-peer, multi-data-centre replication out of the box, availability first with tunable consistency, best for massive write volumes and known queries.',
        '<strong>HBase</strong>: also a wide-column store, but with a master and RegionServers on HDFS; strongly consistent per row, natural inside a Hadoop stack.',
        '<strong>MongoDB</strong>: a document database with flexible ad-hoc queries and secondary indexes; one primary per replica set takes writes.',
        '<strong>DynamoDB</strong>: AWS\'s fully managed key-value/wide-column service from the same Dynamo paper; no servers to run, but tied to AWS and its pricing.',
        'The choice depends on access patterns, consistency needs, existing ecosystem and who will operate it.',
    ])
