from build import *


def _doc(x, y, w, lines, color='green', step=None, focus=None, title=None):
    """A JSON-ish document card."""
    h = 22 + 16 * len(lines) + (18 if title else 0)
    out = [sbox(x, y, w, h, '', '', color, step=step, focus=focus, fill_opacity=0.12)]
    ty = y + 18
    if title:
        out.append(stext(x + w / 2, ty, title, color, 12, step=step, bold=True)); ty += 18
    for i, ln in enumerate(lines):
        out.append(stext(x + 12, ty + i * 16, ln, '#e2e8f0', 11, 'start', step=step))
    return ''.join(out)


# ================================================================== NoSQL foundations
def why_nosql():
    elems = [
        stext(380, 24, 'Why NoSQL appeared', 'blue', 15, bold=True),
        sbox(20, 55, 220, 70, 'One big SQL server', 'fixed schema · joins\nscale up only', 'gray', step=1),
        sbox(270, 45, 220, 40, 'Millions of users', '', 'red', step=2, focus=2, size=12),
        sbox(270, 95, 220, 40, 'Changing data shapes', '', 'red', step=2, focus=2, size=12),
        sbox(270, 145, 220, 40, 'Always-on, many regions', '', 'red', step=2, focus=2, size=12),
        sbox(530, 50, 210, 140, '', '', 'green', step=3, fill_opacity=0.08),
        stext(635, 70, 'NoSQL cluster', 'green', 13, step=3, bold=True),
        sbox(545, 85, 55, 40, 'node', '', 'green', step=3, size=11), sbox(607, 85, 55, 40, 'node', '', 'green', step=3, size=11),
        sbox(669, 85, 55, 40, 'node', '', 'green', step=3, size=11), sbox(576, 135, 55, 40, 'node', '', 'green', step=3, size=11),
        sbox(638, 135, 55, 40, 'node', '', 'green', step=3, size=11),
        stext(380, 240, 'flexible schema · scale out by adding nodes · built-in replication', 'green', 12, step=4, focus=4, bold=True),
        stext(380, 265, 'trade-off: fewer joins, often relaxed consistency', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 285, *elems), [
        'For decades most applications used one relational database on one large server, with a fixed schema and joins between normalised tables.',
        'Web-scale applications brought new pressures: huge numbers of users and writes, data whose shape changes every release, and the need to stay online across regions.',
        '<strong>NoSQL</strong> databases spread data over a cluster of ordinary machines, so capacity grows by adding nodes (horizontal scaling).',
        'They store data in flexible models (documents, key-value, wide columns, graphs) that need no upfront schema, and replicate it automatically.',
        'The price is usually fewer joins and transactions across records, and sometimes eventual instead of immediate consistency.',
    ])


def nosql_types():
    elems = [stext(380, 24, 'The four main NoSQL data models', 'blue', 15, bold=True)]
    elems += [
        sbox(20, 50, 350, 105, '', '', 'blue', step=1, fill_opacity=0.08),
        stext(195, 70, 'Key-Value  (Redis, DynamoDB)', 'blue', 13, step=1, bold=True),
        scell(40, 85, 130, 26, 'session:2401', '#0ea5e9', '#fff', step=1, size=11), scell(170, 85, 180, 26, '{cart: 3 items}', '#334155', step=1, size=11),
        scell(40, 113, 130, 26, 'otp:9876', '#0ea5e9', '#fff', step=1, size=11), scell(170, 113, 180, 26, '482913 (TTL 5 min)', '#334155', step=1, size=11),
        sbox(390, 50, 350, 105, '', '', 'green', step=2, fill_opacity=0.08),
        stext(565, 70, 'Document  (MongoDB, Couchbase)', 'green', 13, step=2, bold=True),
        stext(410, 92, "{ _id: 2401, name: 'Anuj',", '#e2e8f0', 11, 'start', step=2),
        stext(410, 108, "  skills: ['sql','spark'],", '#e2e8f0', 11, 'start', step=2),
        stext(410, 124, "  address: { city: 'Pune' } }", '#e2e8f0', 11, 'start', step=2),
        sbox(20, 170, 350, 105, '', '', 'amber', step=3, fill_opacity=0.08),
        stext(195, 190, 'Wide-column  (Cassandra, HBase)', 'amber', 13, step=3, bold=True),
        scell(40, 205, 80, 26, 'row key', '#f59e0b', '#fff', step=3, size=11), scell(120, 205, 75, 26, 'login:10-12', '#334155', step=3, size=10),
        scell(195, 205, 75, 26, 'login:10-13', '#334155', step=3, size=10), scell(270, 205, 80, 26, '… millions', '#334155', step=3, size=10),
        stext(195, 255, 'rows can have different columns', 'amber', 11, step=3),
        sbox(390, 170, 350, 105, '', '', 'purple', step=4, fill_opacity=0.08),
        stext(565, 190, 'Graph  (Neo4j, Neptune)', 'purple', 13, step=4, bold=True),
        '<g data-step="4"><circle cx="450" cy="235" r="18" fill="#8b5cf6"/><circle cx="565" cy="215" r="18" fill="#8b5cf6"/><circle cx="680" cy="240" r="18" fill="#8b5cf6"/>'
        '<line x1="468" y1="230" x2="547" y2="218" stroke="#a78bfa" stroke-width="2"/><line x1="583" y1="220" x2="662" y2="236" stroke="#a78bfa" stroke-width="2"/></g>',
        stext(508, 260, 'KNOWS', '#a78bfa', 10, step=4), stext(622, 260, 'WORKS_AT', '#a78bfa', 10, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        '<strong>Key-value</strong>: the simplest model, a giant dictionary. Lookups by key are extremely fast; the value is opaque. Ideal for caches, sessions, OTPs, carts.',
        '<strong>Document</strong>: each record is a self-describing JSON-like document with nested objects and arrays, queryable by any field. Ideal for general application data.',
        '<strong>Wide-column</strong>: rows identified by a key, with a huge, sparse, flexible set of columns, partitioned across many nodes. Ideal for time series and very high write rates.',
        '<strong>Graph</strong>: nodes and relationships are first-class, so multi-hop queries (friends of friends, fraud rings, recommendations) are fast.',
    ])


def cap_anim():
    elems = [
        stext(380, 24, 'CAP: during a network partition, choose C or A', 'blue', 15, bold=True),
        sbox(60, 60, 200, 70, 'Node Mumbai', 'marks = 78', 'green', step=1),
        sbox(500, 60, 200, 70, 'Node Pune', 'marks = 78', 'green', step=1),
        sflow(260, 95, 500, 95, 'green', step=1, count=3),
        stext(300, 85, 'replication', 'green', 11, step=1),
        '<g data-step="2"><line x1="370" y1="60" x2="390" y2="130" stroke="#ef4444" stroke-width="5"/></g>',
        stext(380, 150, 'network partition', 'red', 12, step=2, focus=2, bold=True),
        sbox(60, 60, 200, 70, 'Node Mumbai', 'write: marks = 91', 'amber', step=3, focus=3),
        sbox(40, 190, 320, 60, 'CP: Pune refuses reads/writes', 'until it can confirm the latest value', 'blue', step=4, focus=4, size=12),
        sbox(400, 190, 320, 60, 'AP: Pune keeps answering', 'may return the old 78 (stale)', 'purple', step=5, focus=5, size=12),
        stext(380, 280, 'no partition → you can have both consistency and availability', 'cyan', 12, step=6, focus=6),
    ]
    return anim(canvas(760, 295, *elems), [
        'Two replicas of the same data normally stay in sync over the network.',
        'A <strong>network partition</strong> cuts the link. In a distributed system partitions will happen, so Partition tolerance is not optional.',
        'A client writes a new value (91) on the Mumbai side. Pune cannot learn about it.',
        '<strong>CP</strong> choice: Pune refuses requests (or only the majority side accepts writes) so nobody reads stale data. Consistent, but partly unavailable. MongoDB with majority writes behaves like this.',
        '<strong>AP</strong> choice: Pune keeps serving, possibly the old value, and the sides reconcile later. Always available, eventually consistent. Cassandra and DynamoDB default to this.',
        'CAP only forces the choice <em>during</em> a partition. The PACELC extension adds: Else (normal operation) you trade Latency against Consistency.',
    ])


def acid_base():
    elems = [
        stext(190, 26, 'ACID (relational, MongoDB txns)', 'blue', 13, bold=True),
        stext(570, 26, 'BASE (many NoSQL systems)', 'green', 13, bold=True),
        '<line x1="380" y1="15" x2="380" y2="290" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
    ]
    for i, (t, d) in enumerate([('Atomic', 'all or nothing'), ('Consistent', 'rules always hold'), ('Isolated', 'no half-done reads'), ('Durable', 'survives a crash')]):
        elems.append(sbox(60, 45 + i * 55, 260, 44, t, d, 'blue', step=1, focus=1, size=12))
    for i, (t, d) in enumerate([('Basically Available', 'always answers'), ('Soft state', 'may change without input'), ('Eventually consistent', 'replicas converge')]):
        elems.append(sbox(440, 45 + i * 70, 260, 50, t, d, 'green', step=2, focus=2, size=12))
    elems.append(stext(380, 280, 'money transfer → ACID · like counter / feed → BASE is fine', 'amber', 12, step=3, focus=3, bold=True))
    return anim(canvas(760, 295, *elems), [
        '<strong>ACID</strong> guarantees that a transaction is all-or-nothing, keeps data valid, is isolated from concurrent transactions, and is never lost once committed.',
        '<strong>BASE</strong> favours availability and scale: the system always responds, replicas may briefly disagree, and they converge over time.',
        'Choose per use case: fee payments and seat allocation need ACID; view counts, likes and activity feeds tolerate eventual consistency.',
    ])


def sql_vs_nosql():
    elems = [
        stext(190, 26, 'Relational: 3 tables + joins', 'blue', 13, bold=True),
        stext(570, 26, 'MongoDB: 1 document', 'green', 13, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        stable(30, 55, ['roll', 'name'], [['2401', 'Anuj']], [70, 90], step=1, title='students', title_color='blue'),
        stable(200, 55, ['roll', 'skill'], [['2401', 'sql'], ['2401', 'spark']], [70, 80], step=1, title='skills', title_color='blue'),
        stable(60, 170, ['roll', 'subject', 'marks'], [['2401', 'SQL', '82'], ['2401', 'Spark', '77']], [60, 90, 70], step=1, title='marks', title_color='blue'),
        stext(190, 285, 'read a profile = JOIN 3 tables', 'amber', 12, step=2, focus=2),
        _doc(400, 50, 340, ["{ _id: 2401, name: 'Anuj',", "  skills: ['sql', 'spark'],", "  marks: [ { subject: 'SQL', marks: 82 },",
                            "           { subject: 'Spark', marks: 77 } ] }"], 'green', step=3, focus=3),
        stext(570, 185, 'read a profile = 1 lookup by _id', 'green', 12, step=3, bold=True),
        stext(570, 225, 'data that is read together', 'green', 12, step=4),
        stext(570, 243, 'is stored together', 'green', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'In a relational design, a student\'s profile is <strong>normalised</strong> into several tables linked by roll number.',
        'Reading the full profile requires joining all of them, which is fine on one server but expensive when tables are spread over many machines.',
        'In MongoDB the whole profile, including the lists, is stored as <strong>one document</strong> and fetched in a single read.',
        'The guiding rule of document modelling: data that is accessed together should be stored together.',
    ])


# ================================================================== MongoDB basics
def mongo_arch():
    elems = [
        stext(380, 24, 'From your code to MongoDB', 'blue', 15, bold=True),
        sbox(20, 55, 170, 60, 'Application', 'PyMongo / Node / Java', 'gray', step=1, size=12),
        sbox(20, 135, 170, 50, 'mongosh / Compass', '', 'gray', step=1, size=12),
        sbox(270, 75, 200, 80, 'mongod', 'database server\nWiredTiger storage', 'green', step=2, focus=2),
        sarrow(190, 85, 268, 105, 'green', step=2), sarrow(190, 160, 268, 130, 'green', step=2),
        stext(230, 205, 'BSON over TCP :27017', 'green', 11, step=2),
        sbox(540, 45, 200, 160, '', '', 'blue', step=3, fill_opacity=0.08),
        stext(640, 65, 'replica set', 'blue', 12, step=3, bold=True),
        sbox(555, 78, 170, 34, 'primary', '', 'blue', step=3, size=11), sbox(555, 118, 170, 34, 'secondary', '', 'gray', step=3, size=11),
        sbox(555, 158, 170, 34, 'secondary', '', 'gray', step=3, size=11),
        sarrow(470, 115, 538, 115, 'blue', step=3),
        sbox(270, 235, 200, 50, 'mongos router', '+ config servers', 'purple', step=4, focus=4, size=12),
        stext(610, 255, 'sharded cluster = many replica sets', 'purple', 12, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        'Applications use an official <strong>driver</strong> (PyMongo, Node.js, Java); humans use <strong>mongosh</strong> or the Compass GUI.',
        'They talk to <strong>mongod</strong>, the database server process, on port 27017 using the BSON wire protocol. mongod stores data with the WiredTiger storage engine (compression, document-level locking).',
        'In production, mongod runs as a <strong>replica set</strong>: one primary takes writes, secondaries keep copies for high availability.',
        'For very large data, a <strong>sharded cluster</strong> splits collections across several replica sets; applications connect to <strong>mongos</strong> routers, which use config servers to find the right shard.',
    ])


def db_coll_doc():
    elems = [
        stext(380, 24, 'Database → Collection → Document', 'blue', 15, bold=True),
        sbox(20, 50, 720, 230, '', '', 'gray', step=1, fill_opacity=0.05),
        stext(380, 70, 'database: cdac', 'gray', 13, step=1, bold=True),
        sbox(40, 85, 330, 180, '', '', 'blue', step=2, fill_opacity=0.08),
        stext(205, 105, 'collection: students', 'blue', 12, step=2, bold=True),
        sbox(390, 85, 330, 180, '', '', 'amber', step=2, fill_opacity=0.08),
        stext(555, 105, 'collection: courses', 'amber', 12, step=2, bold=True),
        _doc(55, 115, 300, ["{ _id: 2401, name: 'Anuj', marks: 78 }"], 'green', step=3, focus=3),
        _doc(55, 160, 300, ["{ _id: 2402, name: 'Vineeta',", "  skills: ['python', 'hive'] }"], 'green', step=3, focus=3),
        _doc(405, 115, 300, ["{ _id: 'PG-DBDA', months: 6 }"], 'green', step=3),
        stext(205, 255, 'documents in one collection can differ', 'pink', 11, step=4, focus=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'A <strong>database</strong> is a container of collections (like a schema in SQL). One server holds many databases.',
        'A <strong>collection</strong> is a group of related documents (like a table), but without a fixed set of columns.',
        'A <strong>document</strong> is one record: field–value pairs, stored as BSON, with a unique <code>_id</code>.',
        'Documents in the same collection may have different fields: Vineeta has skills, Anuj has marks. Structure is enforced only if you add schema validation.',
    ])


def bson_anim():
    elems = [
        stext(380, 24, 'JSON (what you write) vs BSON (what MongoDB stores)', 'blue', 14, bold=True),
        _doc(20, 50, 300, ["{ \"name\": \"Anuj\",", "  \"marks\": 78,", "  \"joined\": \"2026-07-01\" }"], 'gray', step=1, title='JSON: text'),
        sarrow(320, 95, 418, 95, 'amber', step=2),
        stext(370, 85, 'driver encodes', 'amber', 11, step=2),
        sbox(420, 50, 320, 110, '', '', 'green', step=2, fill_opacity=0.1),
        stext(580, 70, 'BSON: binary, typed', 'green', 12, step=2, bold=True),
        scell(435, 82, 60, 24, 'len', '#334155', step=2, size=10), scell(495, 82, 70, 24, 'string', '#0ea5e9', '#fff', step=2, size=10),
        scell(565, 82, 60, 24, 'int32', '#f59e0b', '#fff', step=3, focus=3, size=10), scell(625, 82, 90, 24, 'date (int64)', '#8b5cf6', '#fff', step=3, focus=3, size=10),
        stext(580, 130, 'each field: type byte + name + value', 'green', 11, step=2),
        stext(380, 200, 'BSON adds types JSON lacks: int32 · int64 · double · Decimal128 · Date · ObjectId · binary', 'purple', 12, step=3),
        stext(380, 230, 'length prefixes let MongoDB skip fields quickly while scanning', 'cyan', 12, step=4, focus=4),
        stext(380, 262, 'max document size: 16 MB', 'red', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 280, *elems), [
        'You write documents in JSON-like syntax in mongosh or your program.',
        'The driver encodes them as <strong>BSON</strong> (Binary JSON) before sending them to the server, which stores BSON on disk.',
        'BSON is <strong>typed</strong>: a number can be a 32-bit int, 64-bit long, double or Decimal128; dates are real dates; ObjectId is its own type. JSON has only "number" and "string".',
        'Every element carries its length, so the server can traverse and skip fields efficiently without parsing text.',
        'A single BSON document can be at most 16 MB; larger files go to GridFS.',
    ])


def objectid_anim():
    elems = [
        stext(380, 24, "ObjectId('6acdf311 a3f19c2e7b 4e21a1')  →  12 bytes", 'blue', 15, bold=True),
        scell(60, 70, 260, 50, '4 bytes: timestamp (seconds)', '#0ea5e9', '#fff', step=1, focus=1, size=12),
        scell(320, 70, 250, 50, '5 bytes: random per process', '#8b5cf6', '#fff', step=2, focus=2, size=12),
        scell(570, 70, 150, 50, '3 bytes: counter', '#10b981', '#fff', step=3, focus=3, size=12),
        stext(190, 150, 'creation time is inside the id', 'blue', 12, step=1),
        stext(445, 150, 'unique per machine/process', 'purple', 12, step=2),
        stext(645, 150, 'unique within a second', 'green', 12, step=3),
        stext(380, 200, 'generated by the driver: no round trip to a central counter', 'amber', 12, step=4, focus=4, bold=True),
        stext(380, 230, 'roughly increasing over time → newest ids sort last', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 250, *elems), [
        'The first 4 bytes are a <strong>timestamp</strong> in seconds, so <code>ObjectId.getTimestamp()</code> tells you when the document was created.',
        'The next 5 bytes are a <strong>random value</strong> unique to the machine and process that generated it.',
        'The last 3 bytes are an incrementing <strong>counter</strong>, so one process can create millions of unique ids per second.',
        'Because ids are created by the client driver, inserts need no central sequence, which is essential in a sharded, distributed database.',
        'Ids increase roughly with time, so sorting by <code>_id</code> approximates insertion order.',
    ])


def insert_anim():
    elems = [
        stext(380, 24, 'insertMany: ordered vs unordered', 'blue', 15, bold=True),
    ]
    for i, (t, c) in enumerate([('2401', 'green'), ('2402', 'green'), ('2401 (dup)', 'red'), ('2404', 'gray')]):
        elems.append(sbox(40 + i * 120, 55, 110, 36, t, '', c, step=1, size=12))
    elems += [
        stext(260, 120, 'ordered: true (default)', 'blue', 13, step=2, bold=True),
        stext(260, 140, 'inserts 2401, 2402 → error on dup → STOPS', 'red', 12, step=2, focus=2),
        stext(260, 158, '2404 is NOT inserted', 'red', 12, step=2),
        stext(260, 200, 'ordered: false', 'green', 13, step=3, bold=True),
        stext(260, 220, 'skips the dup, continues → 2404 inserted', 'green', 12, step=3, focus=3),
        stext(260, 238, 'error lists the failed documents', 'green', 12, step=3),
        sbox(530, 110, 210, 80, 'Single document writes', 'are always atomic', 'purple', step=4, focus=4, size=12),
    ]
    return anim(canvas(760, 270, *elems), [
        'A batch of four documents, one of which repeats an existing <code>_id</code>.',
        'With the default <code>ordered: true</code>, MongoDB inserts in order and stops at the first error. Documents after the failure are not inserted.',
        'With <code>ordered: false</code>, it attempts every document, reports which ones failed, and inserts the rest. Faster for bulk loads.',
        'Each individual document insert is atomic, but the batch as a whole is not a transaction (unless you run it inside one).',
    ])


# ================================================================== CRUD
def find_anim():
    rows = [['2401', 'Anuj', 'PG-DBDA', '78'], ['2402', 'Vineeta', 'PG-DBDA', '91'], ['2403', 'Aarshvi', 'PG-DAC', '84'], ['2404', 'Rohit', 'PG-DAC', '66']]
    elems = [
        stext(380, 24, "db.students.find({ course: 'PG-DBDA', marks: { $gt: 80 } })", 'blue', 13, bold=True),
        stable(40, 55, ['_id', 'name', 'course', 'marks'], rows, [70, 100, 100, 70], step=1, title_color='blue', focus_rows={0: '2', 1: '2,3'}),
        stext(560, 85, "course = 'PG-DBDA'", 'amber', 12, step=2, focus=2),
        stext(560, 105, '→ 2 documents', 'amber', 12, step=2),
        stext(560, 140, 'AND marks > 80', 'purple', 12, step=3, focus=3),
        stext(560, 160, '→ Vineeta only', 'purple', 12, step=3),
        '<g data-step="3"><line x1="44" y1="94" x2="380" y2="94" stroke="#ef4444" stroke-width="2"/><line x1="44" y1="146" x2="380" y2="146" stroke="#ef4444" stroke-width="2"/><line x1="44" y1="172" x2="380" y2="172" stroke="#ef4444" stroke-width="2"/></g>',
        stext(380, 230, 'a filter document: each field is a condition, all must match (implicit AND)', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 250, *elems), [
        'The collection holds four students. <code>find()</code> takes a <strong>filter document</strong> describing what to match.',
        '<code>{course: \'PG-DBDA\'}</code> is an equality condition: two documents match.',
        '<code>{marks: {$gt: 80}}</code> uses a <strong>comparison operator</strong>. Conditions on several fields are combined with AND, so only Vineeta matches both.',
        'Use <code>$or</code>, <code>$in</code>, <code>$and</code>, <code>$not</code> for other combinations, and an index on the filtered fields to avoid scanning every document.',
    ])


def pagination_anim():
    elems = [stext(380, 24, 'find().sort({ marks: -1 }).skip(2).limit(2)', 'blue', 15, bold=True)]
    names = [('Vineeta', 91), ('Sana', 88), ('Aarshvi', 84), ('Anuj', 78), ('Kabir', 72), ('Rohit', 66)]
    for i, (n, m) in enumerate(names):
        y = 50 + i * 36
        elems.append(sbox(60, y, 220, 30, f'{n} · {m}', '', 'gray', step=1, size=12))
        if i in (2, 3):
            elems.append(sbox(60, y, 220, 30, f'{n} · {m}', '', 'green', step=3, focus=3, size=12))
        if i < 2:
            elems.append(f'<g data-step="2"><line x1="65" y1="{y + 15}" x2="275" y2="{y + 15}" stroke="#ef4444" stroke-width="2"/></g>')
    elems += [
        stext(300, 64, '← sorted by marks, highest first', 'blue', 12, 'start', step=1),
        stext(300, 100, '← skip(2): page 1 already shown', 'red', 12, 'start', step=2, focus=2),
        stext(300, 136, '← limit(2): page 2', 'green', 12, 'start', step=3),
        stext(300, 172, '', 'green', 12, 'start', step=3),
        stext(380, 300, 'large skip() still walks the skipped docs → use range-based paging', 'amber', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 315, *elems), [
        '<code>sort({marks: -1})</code> orders the matching documents by marks, descending.',
        '<code>skip(2)</code> discards the first two: that was page 1.',
        '<code>limit(2)</code> returns the next two: page 2. Page n = <code>skip((n-1) × size).limit(size)</code>.',
        'Skip still has to walk past the skipped documents, so page 5,000 is slow. For deep paging, remember the last value seen and query <code>{marks: {$lt: lastMarks}}</code> (keyset pagination).',
    ])


def array_query_anim():
    elems = [
        stext(380, 24, 'Querying arrays and embedded documents', 'blue', 15, bold=True),
        _doc(20, 50, 340, ["{ name: 'Anuj', skills: ['sql', 'spark'],", "  scores: [ { sub: 'SQL', m: 82 },", "            { sub: 'Spark', m: 61 } ],",
                           "  address: { city: 'Pune' } }"], 'gray', step=1),
        stext(400, 70, "{ skills: 'spark' }", 'green', 12, 'start', step=2, focus=2, bold=True),
        stext(400, 88, 'matches if ANY element equals spark', 'green', 11, 'start', step=2),
        stext(400, 120, "{ 'address.city': 'Pune' }", 'blue', 12, 'start', step=3, focus=3, bold=True),
        stext(400, 138, 'dot notation reaches inside sub-documents', 'blue', 11, 'start', step=3),
        stext(400, 170, "{ 'scores.sub': 'Spark', 'scores.m': { $gt: 80 } }", 'red', 12, 'start', step=4, focus=4, bold=True),
        stext(400, 188, 'MATCHES (Spark from one element, 82 from another!)', 'red', 11, 'start', step=4),
        stext(400, 220, "{ scores: { $elemMatch: { sub: 'Spark', m: { $gt: 80 } } } }", 'green', 12, 'start', step=5, focus=5, bold=True),
        stext(400, 238, 'no match: both conditions on the SAME element', 'green', 11, 'start', step=5),
    ]
    return anim(canvas(760, 260, *elems), [
        'A document with an array of strings, an array of sub-documents and an embedded object.',
        'An equality condition on an array field matches when <strong>any</strong> element matches. No special syntax needed.',
        '<strong>Dot notation</strong> reaches into embedded documents and arrays of documents: <code>\'address.city\'</code>, <code>\'scores.sub\'</code>.',
        'Trap: separate conditions on array sub-fields can be satisfied by <strong>different</strong> elements. Here "Spark" comes from one score and "> 80" from another, so the document wrongly matches.',
        '<code>$elemMatch</code> requires one single element to satisfy all conditions. Anuj\'s Spark score is 61, so he is correctly excluded.',
    ])


def update_ops_anim():
    elems = [
        stext(380, 24, 'Update operators change fields in place', 'blue', 15, bold=True),
        _doc(20, 50, 290, ["{ _id: 2401, marks: 78,", "  skills: ['sql'], attempts: 1 }"], 'gray', step=1, title='before'),
        stext(330, 80, "$set: { marks: 82 }", 'blue', 12, 'start', step=2, focus=2),
        stext(330, 105, "$inc: { attempts: 1 }", 'amber', 12, 'start', step=3, focus=3),
        stext(330, 130, "$push: { skills: 'spark' }", 'green', 12, 'start', step=4, focus=4),
        stext(330, 155, "$addToSet: { skills: 'sql' } → no duplicate", 'purple', 12, 'start', step=4),
        stext(330, 180, "$unset: { temp: '' } · $pull: { skills: 'x' }", 'pink', 12, 'start', step=4),
        _doc(20, 160, 290, ["{ _id: 2401, marks: 82,", "  skills: ['sql', 'spark'], attempts: 2 }"], 'green', step=5, focus=5, title='after'),
        stext(380, 270, 'one updateOne = atomic for that document · only changed fields are sent', 'cyan', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 285, *elems), [
        'Instead of rewriting the whole document, an update describes <strong>changes</strong> with operators.',
        '<code>$set</code> sets a field (creating it if missing).',
        '<code>$inc</code> adds to a number atomically, perfect for counters: no read-modify-write race.',
        '<code>$push</code> appends to an array; <code>$addToSet</code> appends only if the value is not already present; <code>$pull</code> removes matching elements; <code>$unset</code> removes a field.',
        'All operators in one update are applied atomically to the document.',
    ])


def positional_anim():
    elems = [
        stext(380, 24, 'Updating elements inside an array', 'blue', 15, bold=True),
        stable(30, 60, ['idx', 'sub', 'm'], [['0', 'SQL', '70'], ['1', 'Spark', '60'], ['2', 'Hive', '55']], [50, 90, 60], step=1, title='scores', title_color='blue'),
        stext(420, 70, "{ 'scores.sub': 'Spark' }, { $set: { 'scores.$.m': 75 } }", 'amber', 12, step=2, focus=2, bold=True),
        stext(420, 90, '$ = FIRST element matched by the query (index 1)', 'amber', 11, step=2),
        scell(170, 112, 60, 26, '75', '#78350f', '#fde68a', step=2, focus=2, bold=True),
        stext(420, 135, "{ $inc: { 'scores.$[].m': 5 } }", 'green', 12, step=3, focus=3, bold=True),
        stext(420, 155, '$[] = EVERY element', 'green', 11, step=3),
        stext(420, 195, "{ $set: { 'scores.$[low].pass': false } },", 'purple', 12, step=4, focus=4, bold=True),
        stext(420, 213, "{ arrayFilters: [ { 'low.m': { $lt: 60 } } ] }", 'purple', 12, step=4, focus=4, bold=True),
        stext(420, 233, '$[low] = elements matching the filter', 'purple', 11, step=4),
        scell(230, 138, 70, 26, 'pass:false', '#4c1d95', '#ddd6fe', step=4, focus=4, size=10),
    ]
    return anim(canvas(760, 260, *elems), [
        'A document holds an array of score sub-documents. How do you change just one of them?',
        'The positional operator <code>$</code> refers to the first array element that matched the query. Here the Spark element (index 1) is set to 75.',
        'The all-positional operator <code>$[]</code> applies the update to every element, e.g. 5 grace marks for all subjects.',
        'The filtered positional operator <code>$[identifier]</code> with <code>arrayFilters</code> updates only elements meeting a condition, here every score below 60.',
    ])


def find_modify_anim():
    elems = [
        stext(380, 24, 'Generating the next roll number safely', 'blue', 15, bold=True),
        sbox(20, 60, 160, 44, 'Request A', '', 'blue', step=1, size=12), sbox(20, 170, 160, 44, 'Request B', '', 'purple', step=1, size=12),
        sbox(300, 105, 180, 70, "counters", "{ _id: 'roll', seq: 2410 }", 'amber', step=1, size=12),
        stext(240, 40, 'read 2410 → write 2411', 'red', 11, step=2), stext(240, 240, 'read 2410 → write 2411', 'red', 11, step=2),
        stext(380, 210, '✘ find + update separately: both get 2411', 'red', 12, step=2, focus=2, bold=True),
        sarrow(180, 82, 298, 125, 'green', step=3), sarrow(180, 192, 298, 155, 'green', step=3),
        stext(620, 90, 'findOneAndUpdate(', 'green', 12, step=3, focus=3),
        stext(620, 108, "{ _id: 'roll' },", 'green', 12, step=3),
        stext(620, 126, '{ $inc: { seq: 1 } },', 'green', 12, step=3),
        stext(620, 144, "{ returnDocument: 'after' })", 'green', 12, step=3),
        stext(380, 280, '✔ one atomic operation: A gets 2411, B gets 2412', 'green', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'Two registrations arrive at the same time and both need the next roll number from a counters document.',
        'If each request first reads the counter and then writes counter + 1, both can read 2410 and both assign 2411: a race condition.',
        '<code>findOneAndUpdate</code> with <code>$inc</code> finds and modifies the document in <strong>one atomic step</strong> and returns it.',
        'The server serialises the two operations on that document, so each request gets a different number.',
    ])


# ================================================================== aggregation
def pipeline_anim():
    elems = [
        stext(380, 24, 'Aggregation pipeline: documents flow through stages', 'blue', 15, bold=True),
        sbox(20, 60, 110, 60, '8 students', '', 'gray', step=1, size=12),
        sbox(160, 55, 130, 70, '$match', "marks ≥ 60", 'blue', step=2, focus=2, size=12),
        sbox(320, 55, 130, 70, '$group', '_id: course\navg, count', 'amber', step=3, focus=3, size=12),
        sbox(480, 55, 130, 70, '$sort', 'avg: -1', 'purple', step=4, focus=4, size=12),
        sbox(640, 55, 100, 70, '$project', 'round avg', 'green', step=5, focus=5, size=12),
        sflow(130, 90, 160, 90, 'blue', step=2, count=2), sflow(290, 90, 320, 90, 'amber', step=3, count=2),
        sflow(450, 90, 480, 90, 'purple', step=4, count=2), sflow(610, 90, 640, 90, 'green', step=5, count=2),
        stext(225, 150, '8 → 7 docs', 'blue', 11, step=2), stext(385, 150, '7 → 3 docs', 'amber', 11, step=3),
        stext(545, 150, 'ordered', 'purple', 11, step=4), stext(690, 150, 'final shape', 'green', 11, step=5),
        stable(220, 180, ['_id', 'students', 'avg'], [['PG-DAI', '2', '80'], ['PG-DBDA', '3', '82.3'], ['PG-DAC', '2', '75']], [110, 90, 80], step=5, title_color='green'),
    ]
    return anim(canvas(760, 290, *elems), [
        'The input is every document in the collection. A pipeline is an array of <strong>stages</strong>; each stage\'s output is the next stage\'s input.',
        '<code>$match</code> filters early (like WHERE), reducing work for later stages and allowing an index to be used.',
        '<code>$group</code> combines documents with the same <code>_id</code> expression and computes accumulators such as <code>$avg</code>, <code>$sum</code>, <code>$push</code>.',
        '<code>$sort</code> orders the grouped results.',
        '<code>$project</code> reshapes each document: rename, compute, round, or hide fields. The result is the final report.',
    ])


def unwind_anim():
    elems = [
        stext(380, 24, '$unwind then $group: count students per skill', 'blue', 15, bold=True),
        _doc(20, 55, 230, ["{ name: 'Anuj',", "  skills: ['sql','spark'] }"], 'gray', step=1),
        _doc(20, 125, 230, ["{ name: 'Vineeta',", "  skills: ['python','spark'] }"], 'gray', step=1),
        sbox(270, 95, 110, 50, "$unwind", "'$skills'", 'amber', step=2, focus=2, size=12),
        sflow(250, 115, 270, 120, 'amber', step=2, count=2),
    ]
    rows = [('Anuj', 'sql'), ('Anuj', 'spark'), ('Vineeta', 'python'), ('Vineeta', 'spark')]
    for i, (n, s) in enumerate(rows):
        elems.append(sbox(400, 45 + i * 40, 160, 32, f'{n} · {s}', '', 'amber', step=2, size=11))
    elems += [
        sflow(560, 120, 600, 120, 'green', step=3, count=2),
        stable(600, 70, ['_id', 'n'], [['spark', '2'], ['python', '1'], ['sql', '1']], [80, 50], step=3, title='$group', title_color='green'),
        stext(380, 230, 'arrays: $unwind turns 1 doc with n elements into n docs', 'cyan', 12, step=4, focus=4),
        stext(380, 250, 'preserveNullAndEmptyArrays: true keeps docs with empty arrays', 'pink', 12, step=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'Each student document holds an array of skills.',
        '<code>$unwind</code> outputs one document per array element, copying the other fields. Two documents with two skills each become four.',
        'Now <code>$group</code> by skill can count students per skill: spark appears twice.',
        'Without the option, documents whose array is empty or missing disappear at $unwind; <code>preserveNullAndEmptyArrays</code> keeps them.',
    ])


def lookup_anim():
    elems = [
        stext(380, 24, "$lookup: { from: 'marks', localField: '_id', foreignField: 'roll', as: 'scores' }", 'blue', 12, bold=True),
        _doc(20, 55, 220, ["{ _id: 2401, name: 'Anuj' }"], 'blue', step=1, title='students'),
        stable(280, 55, ['roll', 'sub', 'm'], [['2401', 'SQL', '82'], ['2402', 'SQL', '91'], ['2401', 'Spark', '77']], [60, 70, 50], step=1, title='marks', title_color='amber', focus_rows={0: '2', 2: '2'}),
        stext(380, 190, 'find marks where roll = 2401', 'amber', 12, step=2, focus=2),
        _doc(500, 55, 240, ["{ _id: 2401, name: 'Anuj',", "  scores: [", "    { roll: 2401, sub: 'SQL', m: 82 },", "    { roll: 2401, sub: 'Spark', m: 77 } ] }"], 'green', step=3, focus=3, title='result'),
        sflow(460, 110, 500, 110, 'green', step=3, count=2),
        stext(380, 240, 'like a LEFT OUTER JOIN: no match → empty array', 'cyan', 12, step=4, focus=4),
        stext(380, 262, 'index marks.roll, and avoid $lookup in hot paths (embed instead)', 'pink', 12, step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'Two collections: students and marks. Marks reference students by roll number.',
        'For each input document, <code>$lookup</code> finds documents in the <code>from</code> collection whose <code>foreignField</code> equals this document\'s <code>localField</code>.',
        'The matches are added as an <strong>array</strong> field (<code>as</code>), so one student carries all their marks.',
        'It behaves like a left outer join. It runs a query per document, so index the foreign field; if you always need the data together, embedding is usually better.',
    ])


def facet_anim():
    elems = [
        stext(380, 24, '$facet: several pipelines over the same input', 'blue', 15, bold=True),
        sbox(20, 110, 140, 60, 'students', 'after $match', 'gray', step=1, size=12),
        sbox(220, 45, 220, 50, 'byCourse', '$group by course', 'blue', step=2, focus=2, size=12),
        sbox(220, 115, 220, 50, 'marksBands', '$bucket 0–60–80–101', 'amber', step=2, focus=2, size=12),
        sbox(220, 185, 220, 50, 'toppers', '$sort + $limit 3', 'green', step=2, focus=2, size=12),
        sflow(160, 140, 220, 70, 'blue', step=2, count=2), sflow(160, 140, 220, 140, 'amber', step=2, count=2), sflow(160, 140, 220, 210, 'green', step=2, count=2),
        _doc(500, 70, 240, ["{ byCourse: [ … ],", "  marksBands: [ … ],", "  toppers: [ … ] }"], 'purple', step=3, focus=3, title='ONE result document'),
        sflow(440, 140, 500, 120, 'purple', step=3, count=3),
        stext(380, 265, 'one round trip feeds a whole dashboard (counts, histogram, top list)', 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'The same set of documents (after a common $match) is needed for several summaries.',
        '<code>$facet</code> runs multiple sub-pipelines in parallel on that same input: a group by course, a histogram with <code>$bucket</code>, and a top-3 list.',
        'Each sub-pipeline\'s result becomes an array field in a single output document.',
        'A dashboard page gets all its widgets\' data in one query instead of three.',
    ])


def window_anim():
    elems = [
        stext(380, 24, '$setWindowFields: rank inside each course', 'blue', 15, bold=True),
        stable(60, 55, ['course', 'name', 'marks', 'rank'], [['DBDA', 'Vineeta', '91', ''], ['DBDA', 'Anuj', '78', ''], ['DBDA', 'Meera', '78', ''], ['DAC', 'Aarshvi', '84', ''], ['DAC', 'Rohit', '66', '']],
               [100, 110, 80, 70], step=1, title_color='blue'),
        '<g data-step="2"><rect x="56" y="78" width="368" height="82" fill="none" stroke="#fbbf24" stroke-width="2" stroke-dasharray="6,4" rx="4"/>'
        '<rect x="56" y="158" width="368" height="56" fill="none" stroke="#a78bfa" stroke-width="2" stroke-dasharray="6,4" rx="4"/></g>',
        stext(560, 110, "partitionBy: '$course'", 'amber', 12, step=2),
        stext(560, 135, 'sortBy: { marks: -1 }', 'amber', 12, step=2),
    ]
    for i, r in enumerate(['1', '2', '2', '1', '2']):
        elems.append(scell(350, 81 + i * 26, 70, 26, r, '#162033', '#fde68a', step=3, focus=3, bold=True))
    elems += [
        stext(560, 180, 'output: { rank: { $rank: {} } }', 'green', 12, step=3),
        stext(380, 245, 'every document kept + a computed field (unlike $group)', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 265, *elems), [
        'Each document is one student with course and marks.',
        '<code>partitionBy</code> splits documents into windows per course; <code>sortBy</code> orders each window by marks, highest first.',
        '<code>$rank</code> numbers documents within their window. Ties (78, 78) share rank 2. <code>$denseRank</code>, <code>$documentNumber</code>, running <code>$sum</code> and moving averages work the same way.',
        'Like SQL window functions, every document is kept and gets a new field; nothing is collapsed. Available since MongoDB 5.0.',
    ])


def out_merge_anim():
    elems = [
        stext(380, 24, 'Saving pipeline results: $out vs $merge', 'blue', 15, bold=True),
        sbox(20, 90, 170, 60, 'aggregation', 'daily attendance %', 'gray', step=1, size=12),
        sbox(260, 50, 220, 60, '$out: report', 'REPLACES the whole collection', 'amber', step=2, focus=2, size=12),
        sbox(260, 150, 220, 60, '$merge: into report', 'upsert by key, keep others', 'green', step=3, focus=3, size=12),
        sflow(190, 120, 260, 80, 'amber', step=2, count=2), sflow(190, 120, 260, 180, 'green', step=3, count=2),
        stable(540, 50, ['_id', 'pct'], [['10-12', '92'], ['10-13', '88 ✔']], [90, 70], step=3, title='report', title_color='green', focus_rows={1: '3'}),
        stext(380, 255, 'incremental refresh = materialized view: $merge only the new day', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 275, *elems), [
        'An aggregation computes a report. Normally the result is returned to the client.',
        '<code>$out</code> writes the result to a collection, <strong>replacing</strong> its entire contents atomically. Good for full rebuilds.',
        '<code>$merge</code> merges results into an existing collection: matched documents are replaced or merged, new ones inserted, the rest untouched.',
        'Running a pipeline for just yesterday with <code>$merge</code> gives an incrementally maintained summary collection, MongoDB\'s version of a materialized view.',
    ])


# ================================================================== modelling
def embed_ref_anim():
    elems = [
        stext(190, 26, 'Embedding', 'green', 15, bold=True),
        stext(570, 26, 'Referencing', 'blue', 15, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        _doc(30, 50, 320, ["{ _id: 2401, name: 'Anuj',", "  address: { city: 'Pune', pin: '411001' },", "  phones: ['98…01', '98…02'] }"], 'green', step=1, focus=1),
        stext(190, 150, '1 read · atomic update', 'green', 12, step=2),
        stext(190, 170, 'best for: owned, bounded, read together', 'green', 12, step=2, focus=2),
        _doc(410, 50, 160, ["{ _id: 2401,", "  name: 'Anuj',", "  course_id: 'DBDA' }"], 'blue', step=3, title='students'),
        _doc(590, 50, 150, ["{ _id: 'DBDA',", "  months: 6,", "  fee: 95000 }"], 'blue', step=3, title='courses'),
        sarrow(570, 115, 588, 115, 'blue', step=3),
        stext(570, 180, '2 reads or $lookup', 'blue', 12, step=4),
        stext(570, 200, 'best for: shared, large or unbounded,', 'blue', 12, step=4, focus=4),
        stext(570, 218, 'changes independently', 'blue', 12, step=4, focus=4),
        stext(380, 275, 'design from your queries: how is the data read and written?', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 290, *elems), [
        '<strong>Embedding</strong> puts related data inside the parent document: the address and phone numbers live inside the student.',
        'One read returns everything and one update changes it atomically. Ideal when the child belongs to one parent, stays small and is read with it.',
        '<strong>Referencing</strong> stores an id pointing to a document in another collection, like a foreign key.',
        'Needed when the related data is shared by many parents (a course), large or growing without limit, or updated on its own. Reads need a second query or $lookup.',
        'Unlike SQL normalisation rules, MongoDB modelling starts from the application\'s access patterns.',
    ])


def one_to_many_anim():
    elems = [stext(380, 24, 'One-to-many: choose by "how many?"', 'blue', 15, bold=True)]
    cols = [('One-to-few', 'addresses of a student', 'embed array', 'green'), ('One-to-many', 'marks of a student (100s)', 'array of ids or child → parent ref', 'amber'),
            ('One-to-squillions', 'attendance logs (millions)', 'child stores parent id only', 'red')]
    for i, (t, ex, how, c) in enumerate(cols):
        x = 20 + i * 245
        elems.append(sbox(x, 55, 230, 60, t, ex, c, step=i + 1, focus=i + 1, size=12))
        elems.append(stext(x + 115, 140, how, c, 12, step=i + 1, bold=True))
    elems += [
        _doc(20, 165, 230, ["{ _id: 2401,", "  addresses: [ {…}, {…} ] }"], 'green', step=1),
        _doc(265, 165, 230, ["{ _id: 2401,", "  mark_ids: [ 101, 102, … ] }"], 'amber', step=2),
        _doc(510, 165, 230, ["{ _id: ObjectId(…),", "  roll: 2401, ts: …, in: 'P' }"], 'red', step=3),
        stext(380, 280, 'never let an array grow without limit (16 MB cap, slow updates)', 'pink', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        '<strong>One-to-few</strong>: a handful of child items, always read with the parent. Embed them as an array.',
        '<strong>One-to-many</strong>: hundreds of items, sometimes needed alone. Keep an array of child ids in the parent, or store the parent\'s id in each child.',
        '<strong>One-to-squillions</strong>: unbounded, e.g. log entries. Each child stores the parent\'s id; the parent stores nothing about them.',
        'An ever-growing array eventually hits the 16 MB document limit and makes every update rewrite a huge document.',
    ])


def patterns_anim():
    elems = [stext(380, 24, 'Common MongoDB schema design patterns', 'blue', 15, bold=True)]
    pats = [('Bucket', 'group 1 hour of sensor readings\ninto one document', 'blue'), ('Computed', 'store totals/averages, update\non write instead of every read', 'green'),
            ('Subset', 'keep last 10 reviews embedded,\nrest in another collection', 'amber'), ('Extended reference', 'copy frequently read fields\n(course name) into the child', 'purple'),
            ('Outlier', 'flag the rare huge document,\noverflow to extra docs', 'pink'), ('Schema versioning', 'schema_version field lets old\nand new shapes coexist', 'cyan')]
    for i, (t, d, c) in enumerate(pats):
        x = 20 + (i % 3) * 245; y = 55 + (i // 3) * 110
        elems.append(sbox(x, y, 230, 90, t, d, c, step=i + 1, focus=i + 1, size=13))
    return anim(canvas(760, 290, *elems), [
        '<strong>Bucket</strong>: instead of one document per reading (millions), store a time window per document with an array of readings. Fewer documents, smaller indexes. (Time-series collections do this automatically.)',
        '<strong>Computed</strong>: pre-compute values that are read often, such as a course\'s student count or average marks, and update them with $inc on write.',
        '<strong>Subset</strong>: embed only the part of a large list that is usually shown (latest items) and keep the full list elsewhere, keeping the main document small.',
        '<strong>Extended reference</strong>: copy a few frequently needed fields of the referenced document to avoid a $lookup on every read, accepting some duplication.',
        '<strong>Outlier</strong>: design for the typical case and handle the rare oversized document (a course with 10,000 students) specially.',
        '<strong>Schema versioning</strong>: a version field lets the application handle old and new document shapes while data is migrated gradually.',
    ])


def validation_anim():
    elems = [
        stext(380, 24, 'Schema validation with $jsonSchema', 'blue', 15, bold=True),
        _doc(20, 50, 330, ["validator: { $jsonSchema: {", "  required: ['name', 'marks'],", "  properties: {", "    marks: { bsonType: 'int', minimum: 0, maximum: 100 }", "} } }"], 'purple', step=1, title='collection rule'),
        sbox(420, 50, 320, 44, "{ name: 'Anuj', marks: 78 }", '', 'gray', step=2, size=12),
        sbox(420, 110, 320, 44, "{ name: 'X', marks: 120 }", '', 'gray', step=3, size=12),
        sbox(420, 170, 320, 44, "{ name: 'Y' }", '', 'gray', step=4, size=12),
        stext(580, 106, '✔ inserted', 'green', 12, step=2, focus=2, bold=True),
        stext(580, 166, '✘ Document failed validation (max 100)', 'red', 12, step=3, focus=3, bold=True),
        stext(580, 226, '✘ Document failed validation (marks required)', 'red', 12, step=4, focus=4, bold=True),
        stext(190, 230, 'validationAction: error | warn', 'cyan', 12, step=5, focus=5),
        stext(190, 250, 'validationLevel: strict | moderate', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'A collection can have a <strong>validator</strong>, usually a <code>$jsonSchema</code> describing required fields, types and ranges.',
        'A document that satisfies the rules is inserted normally.',
        'A document breaking a rule (marks above 100) is rejected with "Document failed validation".',
        'A missing required field is also rejected. Flexible schema does not have to mean no schema.',
        '<code>validationAction: \'warn\'</code> only logs violations (useful while cleaning old data); <code>validationLevel: \'moderate\'</code> skips checks on existing invalid documents.',
    ])


def gridfs_anim():
    elems = [
        stext(380, 24, 'Documents max 16 MB → large files go to GridFS', 'blue', 15, bold=True),
        sbox(20, 60, 180, 60, 'answer_sheet.pdf', '40 MB', 'gray', step=1, size=12),
    ]
    for i in range(6):
        elems.append(scell(250 + i * 70, 60, 64, 40, f'chunk {i}', '#0ea5e9', '#fff', step=2, focus=2, size=11))
    elems += [
        stext(450, 125, 'split into 255 KB chunks → fs.chunks', 'blue', 12, step=2),
        sbox(250, 160, 410, 50, 'fs.files', "{ filename, length: 40 MB, chunkSize, uploadDate, metadata }", 'green', step=3, focus=3, size=11),
        stext(380, 250, 'read back in order · stream a range · replicated like any data', 'cyan', 12, step=4, focus=4),
        stext(380, 272, 'often better: store files in S3/object storage, keep the URL in MongoDB', 'amber', 12, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'A single BSON document cannot exceed 16 MB, so a 40 MB scanned answer sheet cannot be stored as one field.',
        '<strong>GridFS</strong> splits the file into chunks (255 KB by default) stored as documents in <code>fs.chunks</code>.',
        'A matching document in <code>fs.files</code> holds the file\'s metadata. Drivers reassemble the chunks when reading.',
        'GridFS is useful when files must live with the data and be replicated; many architectures prefer object storage plus a URL field.',
    ])


# ================================================================== indexing
def index_anim():
    elems = [
        stext(190, 26, 'No index: COLLSCAN', 'red', 14, bold=True),
        stext(570, 26, 'Index on marks: IXSCAN', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
        stext(380, 48, 'find({ marks: { $gte: 90 } })', 'blue', 12, bold=True),
    ]
    for i in range(10):
        elems.append(scell(40 + (i % 5) * 62, 70 + (i // 5) * 40, 56, 32, f'doc{i}', '#7f1d1d', '#fecaca', step=1, focus=1, size=10))
    elems.append(stext(190, 175, 'reads EVERY document (10 of 10)', 'red', 12, step=1, bold=True))
    keys = ['66', '72', '78', '84', '88', '91', '95']
    for i, k in enumerate(keys):
        hit = int(k) >= 90
        elems.append(scell(410 + i * 46, 80, 44, 30, k, '#10b981' if hit else '#334155', '#fff', step=2, focus=2 if hit else None, size=11))
    elems += [
        stext(570, 245, 'sorted B-tree of marks → jump to 90, read 2 keys', 'green', 12, step=2),
        sarrow(640, 112, 610, 160, 'green', step=3), sarrow(680, 112, 690, 160, 'green', step=3),
        scell(570, 160, 70, 30, 'doc 5', '#064e3b', '#bbf7d0', step=3, size=11), scell(660, 160, 70, 30, 'doc 8', '#064e3b', '#bbf7d0', step=3, size=11),
        stext(570, 210, 'fetch only matching documents (2 of 10)', 'green', 12, step=3, bold=True),
        stext(380, 280, 'cost: extra storage + every write must also update each index', 'amber', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'Without an index, MongoDB must examine every document in the collection (<strong>COLLSCAN</strong>) to find matches.',
        'An index keeps the values of a field <strong>sorted</strong> (a B-tree) with pointers to documents. MongoDB jumps straight to 90 and reads only the qualifying keys (<strong>IXSCAN</strong>).',
        'Only the matching documents are fetched. On millions of documents the difference is milliseconds vs seconds.',
        'Indexes are not free: they use disk and RAM, and every insert/update must maintain them. Index for your real queries only.',
    ])


def esr_anim():
    elems = [
        stext(380, 24, "find({ course: 'DBDA', marks: { $gte: 80 } }).sort({ name: 1 })", 'blue', 13, bold=True),
        sbox(40, 60, 200, 60, 'E: Equality', "course", 'green', step=1, focus=1, size=13),
        sbox(280, 60, 200, 60, 'S: Sort', "name", 'amber', step=2, focus=2, size=13),
        sbox(520, 60, 200, 60, 'R: Range', "marks", 'purple', step=3, focus=3, size=13),
        sarrow(240, 90, 278, 90, 'gray', step=2), sarrow(480, 90, 518, 90, 'gray', step=3),
        stext(380, 160, 'createIndex({ course: 1, name: 1, marks: 1 })', 'cyan', 14, step=4, focus=4, bold=True),
        stext(380, 195, 'equality narrows to one contiguous block, already sorted by name → no in-memory SORT', 'green', 12, step=4),
        stext(380, 230, '{ course: 1, marks: 1, name: 1 } → range first breaks the sort order → SORT stage', 'red', 12, step=5, focus=5),
        stext(380, 255, 'prefix rule: this index also serves queries on { course } and { course, name }', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'Fields with <strong>equality</strong> conditions go first in a compound index: they narrow the index to a contiguous range of entries.',
        'Fields used for <strong>sort</strong> go next: within that range, entries are already in sort order, so MongoDB avoids an expensive in-memory sort.',
        'Fields with <strong>range</strong> conditions ($gt, $lt, $in on many values) go last.',
        'This is the <strong>ESR rule</strong>: Equality, Sort, Range.',
        'Putting the range field before the sort field breaks the ordering and forces a blocking SORT stage. Compound indexes also serve queries on any <strong>prefix</strong> of their fields.',
    ])


def covered_anim():
    elems = [
        stext(380, 24, "find({ course: 'DBDA' }, { _id: 0, course: 1, name: 1 })", 'blue', 13, bold=True),
        sbox(40, 60, 300, 80, 'Index { course: 1, name: 1 }', 'contains course AND name', 'green', step=1, focus=1, size=12),
        sbox(440, 60, 280, 80, 'documents on disk', '', 'gray', step=1, size=12),
        sflow(340, 100, 440, 100, 'red', step=2, count=2),
        stext(390, 160, 'normal query: index → FETCH document', 'red', 12, step=2),
        '<g data-step="3"><line x1="345" y1="70" x2="435" y2="130" stroke="#ef4444" stroke-width="4"/></g>',
        stext(190, 190, 'covered: answer built from the index alone', 'green', 13, step=3, focus=3, bold=True),
        stext(190, 210, 'explain: totalDocsExamined: 0', 'green', 12, step=3),
        stext(380, 255, '_id must be excluded (it is not in the index) · no array fields in the index', 'amber', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 270, *elems), [
        'The query filters on course and returns only course and name. Both fields are in the compound index.',
        'Normally MongoDB finds keys in the index and then fetches each full document from disk.',
        'Here every returned field is already in the index, so no document is fetched: a <strong>covered query</strong>, the fastest kind of read.',
        'You must exclude <code>_id</code> (unless it is in the index), and covered queries are not possible on multikey (array) index fields.',
    ])


def index_types_anim():
    elems = [stext(380, 24, 'Index types', 'blue', 15, bold=True)]
    types = [('Single field', '{ marks: 1 }', 'blue'), ('Compound', '{ course: 1, marks: -1 }', 'green'), ('Multikey', '{ skills: 1 } on an array', 'amber'),
             ('Text', "{ bio: 'text' }", 'purple'), ('Geospatial', "{ loc: '2dsphere' }", 'pink'), ('Hashed', "{ roll: 'hashed' }", 'cyan'),
             ('TTL', 'expireAfterSeconds: 300', 'red'), ('Unique / Partial', 'unique · partialFilterExpression', 'gray')]
    for i, (t, d, c) in enumerate(types):
        x = 20 + (i % 4) * 182; y = 55 + (i // 4) * 105
        elems.append(sbox(x, y, 170, 85, t, d, c, step=i // 2 + 1, focus=i // 2 + 1, size=12))
    return anim(canvas(760, 280, *elems), [
        '<strong>Single-field</strong> indexes speed up filters and sorts on one field; <strong>compound</strong> indexes cover several fields in a chosen order.',
        '<strong>Multikey</strong> indexes are created automatically when the field holds arrays (one key per element). <strong>Text</strong> indexes support keyword search on string content.',
        '<strong>2dsphere</strong> indexes answer "near me" and within-area queries. <strong>Hashed</strong> indexes spread values evenly and are used for hashed sharding.',
        '<strong>TTL</strong> indexes delete documents automatically after a time (OTPs, sessions, logs). <strong>Unique</strong> indexes prevent duplicates; <strong>partial</strong> indexes include only documents matching a filter.',
    ])


def explain_anim():
    elems = [
        stext(380, 24, 'Reading explain("executionStats")', 'blue', 15, bold=True),
        sbox(40, 55, 300, 50, 'winningPlan.stage', 'COLLSCAN ✘  vs  IXSCAN → FETCH ✔', 'blue', step=1, focus=1, size=12),
        sbox(40, 125, 300, 50, 'nReturned', 'documents returned', 'green', step=2, size=12),
        sbox(40, 195, 300, 50, 'totalKeysExamined / totalDocsExamined', 'work done', 'amber', step=2, focus=2, size=11),
        sbox(420, 55, 300, 50, 'executionTimeMillis', 'server time', 'purple', step=3, size=12),
        sbox(420, 125, 300, 50, 'SORT stage present?', 'in-memory sort → fix index order', 'red', step=3, focus=3, size=12),
        sbox(420, 195, 300, 50, 'rejectedPlans', 'other indexes the planner tried', 'gray', step=3, size=12),
        stext(380, 275, 'goal: keysExamined ≈ docsExamined ≈ nReturned', 'cyan', 13, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 290, *elems), [
        'The first thing to check is the plan\'s stages: <strong>COLLSCAN</strong> means no index was used; <strong>IXSCAN</strong> followed by FETCH means an index found the documents.',
        'Compare <strong>nReturned</strong> with <strong>totalKeysExamined</strong> and <strong>totalDocsExamined</strong>. Examining 1,000,000 documents to return 20 is the classic sign of a missing or wrong index.',
        'A <strong>SORT</strong> stage means the results were sorted in memory (limited to 100 MB unless spilling is allowed); fix it with an index in the right order. <strong>rejectedPlans</strong> shows alternatives the planner considered.',
        'A healthy query examines about as many keys and documents as it returns.',
    ])


# ================================================================== replication / sharding / txns
def replica_anim():
    elems = [
        stext(380, 24, 'Replica set: automatic failover', 'blue', 15, bold=True),
        sbox(40, 60, 100, 40, 'App', '', 'gray', step=1, size=12),
        sbox(280, 50, 200, 60, 'PRIMARY', 'all writes · oplog', 'green', step=1, focus='1,4'),
        sbox(160, 180, 190, 60, 'SECONDARY 1', 'replays oplog', 'gray', step=2, size=12),
        sbox(410, 180, 190, 60, 'SECONDARY 2', 'replays oplog', 'gray', step=2, size=12),
        sarrow(140, 80, 278, 80, 'green', step=1),
        sflow(330, 110, 255, 180, 'cyan', step=2, count=2), sflow(430, 110, 505, 180, 'cyan', step=2, count=2),
        '<g data-step="3"><line x1="285" y1="55" x2="475" y2="105" stroke="#ef4444" stroke-width="5"/><line x1="475" y1="55" x2="285" y2="105" stroke="#ef4444" stroke-width="5"/></g>',
        stext(620, 80, 'heartbeats stop (10 s)', 'red', 12, step=3, focus=3),
        sbox(160, 180, 190, 60, 'NEW PRIMARY', 'elected by majority', 'green', step=4, focus=4, size=12),
        sarrow(120, 100, 230, 178, 'green', step=4),
        stext(380, 280, 'drivers retry writes and reconnect automatically · usually < 12 s', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'A <strong>replica set</strong> is a group of mongod processes with the same data. Only the <strong>primary</strong> accepts writes and records them in its <strong>oplog</strong> (operations log).',
        '<strong>Secondaries</strong> continuously copy and replay the oplog, staying close to the primary. They can serve reads if the application allows.',
        'If the primary crashes, the others stop receiving heartbeats (default election timeout 10 seconds).',
        'The remaining members hold an <strong>election</strong>; a secondary with up-to-date data and votes from a majority becomes the new primary. An odd number of voting members (3, 5) avoids ties.',
        'Drivers discover the new primary and retryable writes resend the failed write, so applications see only a short pause.',
    ])


def write_concern_anim():
    elems = [
        stext(380, 24, 'Write concern: when is a write "done"?', 'blue', 15, bold=True),
        sbox(30, 60, 120, 40, 'App write', '', 'gray', step=1, size=12),
        sbox(230, 50, 160, 50, 'Primary', '', 'green', step=1, size=12),
        sbox(450, 50, 140, 50, 'Secondary 1', '', 'gray', step=2, size=12),
        sbox(610, 50, 130, 50, 'Secondary 2', '', 'gray', step=2, size=12),
        sarrow(150, 80, 228, 80, 'green', step=1),
        sflow(390, 75, 450, 75, 'cyan', step=2, count=2),
        stext(310, 140, 'w: 1 → ack after primary only', 'amber', 12, step=1, focus=1),
        stext(310, 160, 'fast, but lost if primary dies before replicating', 'amber', 11, step=1),
        stext(470, 200, "w: 'majority' → ack after 2 of 3 have it (default)", 'green', 12, step=2, focus=2, bold=True),
        stext(470, 220, 'survives failover: cannot be rolled back', 'green', 11, step=2),
        stext(380, 255, "j: true → written to the on-disk journal before ack", 'purple', 12, step=3, focus=3),
        stext(380, 280, "readConcern 'majority' + readPreference 'secondary' control the read side", 'cyan', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 295, *elems), [
        'With <code>w: 1</code> the client is acknowledged as soon as the primary applies the write. If the primary fails before secondaries copy it, that write can be rolled back.',
        'With <code>w: \'majority\'</code> (the default since MongoDB 5.0) the acknowledgement waits until most members have the write, so it survives any failover.',
        '<code>j: true</code> additionally requires the write to reach the journal on disk.',
        'On the read side, <strong>read concern</strong> chooses what data is visible (e.g. only majority-committed) and <strong>read preference</strong> chooses which members serve reads (primary, secondary, nearest).',
    ])


def sharding_anim():
    elems = [
        stext(380, 24, 'Sharded cluster', 'blue', 15, bold=True),
        sbox(20, 55, 120, 44, 'App', '', 'gray', step=1, size=12),
        sbox(200, 50, 160, 56, 'mongos', 'router', 'purple', step=1, focus=1),
        sbox(440, 50, 300, 56, 'Config servers (replica set)', 'which chunk is on which shard', 'amber', step=2, focus=2, size=12),
        sarrow(140, 77, 198, 77, 'purple', step=1), sarrow(360, 78, 438, 78, 'amber', step=2),
    ]
    for i, (rng, c) in enumerate([('roll 2400–2599', 'green'), ('roll 2600–2799', 'blue'), ('roll 2800–…', 'pink')]):
        x = 30 + i * 245
        elems.append(sbox(x, 160, 220, 70, f'Shard {i + 1} (replica set)', rng, c, step=3, focus=3, size=12))
    elems += [
        sflow(280, 106, 140, 160, 'green', step=4, count=2),
        stext(380, 135, "find({ roll: 2421 }) → only shard 1 (targeted)", 'green', 12, step=4, focus=4),
        stext(380, 260, "find({ city: 'Pune' }) → all shards (scatter-gather)", 'red', 12, step=5, focus=5),
        stext(380, 282, 'balancer moves chunks to keep shards even', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 295, *elems), [
        'Applications connect to <strong>mongos</strong>, a lightweight router; they never talk to shards directly.',
        '<strong>Config servers</strong> store cluster metadata: how each sharded collection is split into <strong>chunks</strong> by shard key range and which shard holds each chunk.',
        'Each <strong>shard</strong> is itself a replica set holding a subset of the data. Adding shards adds storage and write capacity.',
        'A query that includes the <strong>shard key</strong> is routed only to the shard(s) owning those values: a targeted query.',
        'A query without the shard key must be sent to every shard and merged (scatter-gather), which scales poorly. The <strong>balancer</strong> migrates chunks to keep shards evenly loaded.',
    ])


def shard_key_anim():
    elems = [
        stext(190, 26, 'Ranged key: createdAt', 'red', 14, bold=True),
        stext(570, 26, 'Hashed key: hashed(_id)', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-dasharray="6,5" stroke-width="2"/>',
    ]
    for i in range(3):
        load = [0.15, 0.15, 0.95][i]
        elems.append(stext(40, 75 + i * 50, f'S{i + 1}', 'gray', 12, 'start', step=1))
        elems.append(f'<rect x="70" y="{60 + i * 50}" width="{load * 270:.0f}" height="26" rx="4" fill="{"#ef4444" if load > 0.5 else "#64748b"}" data-step="1"/>')
        elems.append(stext(420, 75 + i * 50, f'S{i + 1}', 'gray', 12, 'start', step=2))
        elems.append(f'<rect x="450" y="{60 + i * 50}" width="{0.4 * 270:.0f}" height="26" rx="4" fill="#10b981" data-step="2"/>')
    elems += [
        stext(190, 225, 'all new inserts hit the last chunk → hot shard', 'red', 12, step=1, focus=1),
        stext(570, 225, 'inserts spread evenly', 'green', 12, step=2, focus=2),
        stext(570, 243, 'but range queries go to all shards', 'amber', 12, step=3, focus=3),
        stext(380, 280, 'good key: high cardinality · even frequency · not monotonic · used in queries', 'cyan', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 295, *elems), [
        'With a <strong>monotonically increasing</strong> ranged shard key (a timestamp or ObjectId), every new document has the highest value, so all inserts go to the last chunk on one shard: a hot spot.',
        'A <strong>hashed</strong> shard key distributes documents by the hash of the value, spreading writes evenly over all shards.',
        'The trade-off: values that are adjacent are scattered, so range queries on that field must ask every shard.',
        'A good shard key has many distinct values, no very frequent value, does not increase monotonically (or is hashed), and appears in most queries so they can be targeted. Compound keys (e.g. { centre: 1, roll: 1 }) often achieve this.',
    ])


def txn_anim():
    elems = [
        stext(380, 24, 'Multi-document transaction: fee payment', 'blue', 15, bold=True),
        sbox(20, 60, 140, 44, 'startTransaction', '', 'purple', step=1, focus=1, size=12),
        sbox(200, 50, 250, 44, 'payments.insertOne(…)', '', 'blue', step=2, size=12),
        sbox(200, 104, 250, 44, "students.updateOne($inc paid)", '', 'blue', step=2, size=12),
        sbox(200, 158, 250, 44, "seats.updateOne($inc taken)", '', 'blue', step=2, size=12),
        sarrow(160, 82, 198, 72, 'purple', step=2),
        sbox(510, 60, 230, 50, 'commitTransaction', 'all 3 visible at once', 'green', step=3, focus=3, size=12),
        sbox(510, 140, 230, 50, 'abortTransaction', 'none applied', 'red', step=4, focus=4, size=12),
        sarrow(450, 120, 508, 88, 'green', step=3), sarrow(450, 140, 508, 162, 'red', step=4),
        stext(380, 245, 'replica set or sharded cluster required · keep under 60 s · prefer single-doc design', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 265, *elems), [
        'Since MongoDB 4.0 (replica sets) and 4.2 (sharded clusters), several operations can run in one ACID transaction inside a session.',
        'Recording a payment touches three collections: the payment record, the student\'s paid amount and the course\'s seat count.',
        'On <strong>commit</strong>, all three changes become visible together.',
        'On error or <strong>abort</strong>, none of them is applied: no half-paid student.',
        'Transactions cost performance (locks, oplog size, 60-second default limit), so first try to design so that one document holds what must change together; single-document writes are always atomic.',
    ])


# ================================================================== scenarios
def exam_schema_anim():
    elems = [
        stext(380, 24, 'Exam portal schema (access-pattern driven)', 'blue', 15, bold=True),
        _doc(20, 50, 230, ["students", "{ _id: 2401, name, course,", "  contact: {…},", "  enrolled: [ 'SQL-2026-10', … ] }"], 'blue', step=1, focus=1),
        _doc(270, 50, 220, ["exams", "{ _id: 'SQL-2026-10',", "  questions: [ {q, options, ans} ],", "  duration: 60 }"], 'amber', step=2, focus=2),
        _doc(510, 50, 230, ["attempts", "{ roll: 2401, exam: …,", "  answers: [ … ], score: 82,", "  started, submitted }"], 'green', step=3, focus=3),
        _doc(270, 175, 220, ["exam_stats (computed)", "{ _id: exam, attempts: 412,", "  avg: 71.4, pass: 380 }"], 'purple', step=4, focus=4),
        stext(380, 285, 'indexes: attempts { roll: 1, exam: 1 } unique · { exam: 1, score: -1, submittedAt: 1 }', 'cyan', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 300, *elems), [
        '<strong>students</strong>: profile with embedded contact details and a small array of enrolments (bounded).',
        '<strong>exams</strong>: each exam embeds its questions, because they are always loaded together when the exam starts.',
        '<strong>attempts</strong>: one document per student per exam (unbounded over time, so not embedded in students), holding answers and score.',
        '<strong>exam_stats</strong>: the computed pattern; updated with $inc on each submission so the dashboard never has to aggregate thousands of attempts.',
        'Indexes follow the queries: a unique index stops double attempts; another serves "leaderboard for an exam".',
    ])


def cdc_anim():
    elems = [
        stext(380, 24, 'MongoDB in a data pipeline', 'blue', 15, bold=True),
        sbox(20, 60, 160, 60, 'MongoDB', 'operational data', 'green', step=1),
        sbox(230, 50, 170, 44, 'Change stream', 'insert/update/delete events', 'amber', step=2, focus=2, size=11),
        sbox(230, 110, 170, 44, 'Kafka Connect / Debezium', '', 'amber', step=2, size=11),
        sbox(450, 60, 130, 60, 'Kafka', 'topic', 'purple', step=3, size=12),
        sbox(620, 40, 120, 44, 'Spark', 'connector', 'blue', step=3, size=12),
        sbox(620, 100, 120, 44, 'Data lake', 'Parquet', 'cyan', step=3, size=12),
        sflow(180, 85, 230, 72, 'amber', step=2, count=2), sflow(400, 85, 450, 90, 'purple', step=3, count=2),
        sflow(580, 80, 620, 62, 'blue', step=3, count=2), sflow(580, 95, 620, 122, 'cyan', step=3, count=2),
        sbox(230, 200, 300, 50, 'Batch: mongoexport / Spark read', 'nightly snapshot to the lake', 'gray', step=4, focus=4, size=12),
        sflow(100, 120, 230, 225, 'gray', step=4, count=2),
    ]
    return anim(canvas(760, 270, *elems), [
        'MongoDB usually holds live application data; analytics happen elsewhere.',
        '<strong>Change streams</strong> (built on the oplog, replica set required) let consumers subscribe to every insert, update and delete as it happens; Kafka connectors use them for CDC.',
        'Events flow through Kafka to Spark Structured Streaming or straight into a data lake as Parquet, keeping analytical copies minutes behind production.',
        'For simpler needs, a nightly batch reads collections with the Spark connector or <code>mongoexport</code>.',
    ])


def troubleshoot_anim():
    elems = [stext(380, 24, 'Diagnosing a slow MongoDB query', 'blue', 15, bold=True)]
    steps_ = [('Profiler / slow log', 'queries > 100 ms', 'red'), ('explain()', 'COLLSCAN? SORT?', 'amber'),
              ('Index fix', 'ESR order', 'green'), ('Model fix', 'huge docs? $lookup?', 'purple'), ('Verify', 'docs ≈ returned', 'cyan')]
    for i, (t, sub, c) in enumerate(steps_):
        x = 15 + i * 150
        elems.append(sbox(x, 90, 135, 80, t, sub, c, step=i + 1, focus=i + 1, size=12))
        if i:
            elems.append(sarrow(x - 15, 130, x - 2, 130, 'gray', step=i + 1))
    elems.append(stext(380, 230, 'also check: working set fits in RAM · replication lag · connection pool', 'cyan', 12, step=5))
    return anim(canvas(760, 250, *elems), [
        'Find the slow operations: the database profiler (<code>db.setProfilingLevel(1, {slowms: 100})</code>), the slow-query log, or Atlas Performance Advisor.',
        'Run <code>explain(\'executionStats\')</code> on the query: look for COLLSCAN, in-memory SORT, and docs examined much larger than returned.',
        'Create or reorder an index following the ESR rule; consider a covered index for hot queries.',
        'If the index is fine, look at the data model: very large documents, unbounded arrays, or $lookup on every read.',
        'Re-run explain and confirm the work done is close to the results returned.',
    ])


def scenarios_anim():
    elems = [stext(380, 24, 'Symptom → likely cause → fix', 'blue', 15, bold=True)]
    rows = [('E11000 duplicate key', 'retry inserted twice / race', 'unique index + upsert / idempotent key', 'red'),
            ('Query slow, CPU 100%', 'COLLSCAN, missing index', 'explain() → ESR index', 'amber'),
            ('Document too large (16 MB)', 'unbounded array', 'child collection / bucket', 'purple'),
            ('One shard overloaded', 'monotonic shard key', 'hashed or compound key', 'pink'),
            ('Stale data on reads', 'secondary reads / lag', 'primary or majority read concern', 'cyan')]
    for i, (s, c, f, col) in enumerate(rows):
        y = 45 + i * 48
        elems.append(sbox(15, y, 230, 40, s, '', col, step=i + 1, focus=i + 1, size=11))
        elems.append(sarrow(245, y + 20, 268, y + 20, 'gray', step=i + 1))
        elems.append(sbox(270, y, 220, 40, c, '', 'gray', step=i + 1, size=11))
        elems.append(sarrow(490, y + 20, 513, y + 20, 'gray', step=i + 1))
        elems.append(sbox(515, y, 230, 40, f, '', 'green', step=i + 1, size=11))
    return anim(canvas(760, 295, *elems), [
        '<strong>Duplicate key errors</strong> usually mean a retried or concurrent insert. Make writes idempotent: natural unique keys, upserts.',
        '<strong>Slow queries with high CPU</strong> are most often collection scans: find them in the profiler and add the right compound index.',
        '<strong>Documents hitting 16 MB</strong> come from arrays that grow forever. Move the children to their own collection or bucket them.',
        '<strong>One busy shard</strong> while others idle points to a monotonically increasing or low-cardinality shard key.',
        '<strong>Users not seeing their own updates</strong> often read from lagging secondaries; use primary reads or causal consistency for that flow.',
    ])
