"""cqlsim - a small, deterministic CQL engine that follows Apache Cassandra 5.0 semantics.

Used at build time to produce the Output boxes of the Cassandra module. It implements:
  * Murmur3Partitioner tokens (bit-for-bit, including Cassandra's signed-byte tail quirk)
  * partition order by token, clustering order (ASC/DESC) inside a partition
  * Cassandra's WHERE-clause rules and its error messages (ALLOW FILTERING, clustering prefix,
    partition-key restrictions, ORDER BY, GROUP BY), secondary indexes and SAI
  * upserts, last-write-wins by write timestamp, row/range/partition tombstones,
    TTL with a simulated clock, WRITETIME/TTL functions, static columns
  * collections, frozen UDTs, counters, lightweight transactions (IF ...), batches,
    materialized views, INSERT/SELECT JSON, aggregates and GROUP BY
  * cqlsh-style output (right-aligned table, "(N rows)", warnings, error lines)
It is a single-node simulation: replication, consistency levels and repair are not simulated.
"""
import datetime as _dt
import decimal
import json
import random
import re
import struct
import uuid as _uuid

MASK = (1 << 64) - 1


# ============================================================ Murmur3 (Cassandra flavour)
def _rotl(x, r):
    return ((x << r) | (x >> (64 - r))) & MASK


def _fmix(k):
    k ^= k >> 33
    k = (k * 0xff51afd7ed558ccd) & MASK
    k ^= k >> 33
    k = (k * 0xc4ceb9fe1a85ec53) & MASK
    k ^= k >> 33
    return k


def murmur3_token(data: bytes) -> int:
    length = len(data)
    nblocks = length >> 4
    h1 = h2 = 0
    c1, c2 = 0x87c37b91114253d5, 0x4cf5ad432745937f
    for i in range(nblocks):
        k1 = int.from_bytes(data[i * 16:i * 16 + 8], 'little')
        k2 = int.from_bytes(data[i * 16 + 8:i * 16 + 16], 'little')
        k1 = (k1 * c1) & MASK; k1 = _rotl(k1, 31); k1 = (k1 * c2) & MASK; h1 ^= k1
        h1 = _rotl(h1, 27); h1 = (h1 + h2) & MASK; h1 = (h1 * 5 + 0x52dce729) & MASK
        k2 = (k2 * c2) & MASK; k2 = _rotl(k2, 33); k2 = (k2 * c1) & MASK; h2 ^= k2
        h2 = _rotl(h2, 31); h2 = (h2 + h1) & MASK; h2 = (h2 * 5 + 0x38495ab5) & MASK
    off = nblocks * 16
    rem = length & 15

    def sb(j):  # Java signed byte, sign-extended to long (Cassandra's historical quirk)
        b = data[off + j]
        return b - 256 if b > 127 else b
    k1 = k2 = 0
    if rem > 8:
        for j in range(rem - 1, 7, -1):
            k2 ^= (sb(j) << (8 * (j - 8))) & MASK
        k2 = (k2 * c2) & MASK; k2 = _rotl(k2, 33); k2 = (k2 * c1) & MASK; h2 ^= k2
    if rem > 0:
        for j in range(min(rem, 8) - 1, -1, -1):
            k1 ^= (sb(j) << (8 * j)) & MASK
        k1 = (k1 * c1) & MASK; k1 = _rotl(k1, 31); k1 = (k1 * c2) & MASK; h1 ^= k1
    h1 ^= length; h2 ^= length
    h1 = (h1 + h2) & MASK; h2 = (h2 + h1) & MASK
    h1 = _fmix(h1); h2 = _fmix(h2)
    h1 = (h1 + h2) & MASK
    t = h1 - (1 << 64) if h1 >= 1 << 63 else h1
    return (1 << 63) - 1 if t == -(1 << 63) else t


# ============================================================ errors
class CQLError(Exception):
    def __init__(self, msg, kind='InvalidRequest', code='2200 [Invalid query]'):
        super().__init__(msg)
        self.msg, self.kind, self.code = msg, kind, code

    def render(self):
        if self.kind in ('SyntaxException', 'AlreadyExists'):
            return f'{self.kind}: {self.msg}'
        return f'{self.kind}: Error from server: code={self.code} message="{self.msg}"'


def inv(msg):
    return CQLError(msg)


# ============================================================ tokenizer
TOKEN_RE = re.compile(r"""
    (?P<ws>\s+|--[^\n]*|//[^\n]*|/\*.*?\*/)
  | (?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})
  | (?P<blob>0[xX][0-9a-fA-F]*)
  | (?P<num>\d+\.\d*(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+|\d+)
  | (?P<str>'(?:[^']|'')*')
  | (?P<qid>"(?:[^"]|"")+")
  | (?P<id>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<op><=|>=|!=|\[|\]|[(),;.=<>{}:+\-*?])
""", re.S | re.X)


class Tok:
    __slots__ = ('kind', 'val', 'raw')

    def __init__(self, kind, val, raw):
        self.kind, self.val, self.raw = kind, val, raw

    def __repr__(self):
        return f'{self.kind}:{self.val}'


def tokenize(src):
    out, pos = [], 0
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise CQLError(f"line 1:{pos} character '{src[pos]}' not recognized", 'SyntaxException')
        pos = m.end()
        k = m.lastgroup
        t = m.group(k)
        if k == 'ws':
            continue
        if k == 'str':
            out.append(Tok('str', t[1:-1].replace("''", "'"), t))
        elif k == 'qid':
            out.append(Tok('id', t[1:-1].replace('""', '"'), t))
        elif k == 'id':
            out.append(Tok('id', t.lower(), t))
        else:
            out.append(Tok(k, t, t))
    out.append(Tok('eof', None, ''))
    return out


# ============================================================ types
NUMERIC = {'int', 'bigint', 'smallint', 'tinyint', 'varint', 'double', 'float', 'decimal', 'counter'}
SIMPLE = NUMERIC | {'text', 'varchar', 'ascii', 'uuid', 'timeuuid', 'timestamp', 'date', 'time', 'boolean', 'blob', 'inet', 'duration'}


def tname(t):
    if isinstance(t, str):
        return 'text' if t == 'varchar' else t
    if t[0] == 'frozen':
        return f'frozen<{tname(t[1])}>'
    if t[0] == 'udt':
        return t[1]
    if t[0] == 'map':
        return f'map<{tname(t[1])}, {tname(t[2])}>'
    return f'{t[0]}<{tname(t[1])}>'


def base_t(t):
    while isinstance(t, tuple) and t[0] == 'frozen':
        t = t[1]
    return t


EPOCH = _dt.datetime(1970, 1, 1, tzinfo=_dt.timezone.utc)


def parse_ts(s):
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,6}))?)?)?\s*(Z|[+-]\d{2}:?\d{2})?', s.strip())
    if not m:
        raise ValueError(s)
    y, mo, d, h, mi, se, frac, tz = m.groups()
    dt = _dt.datetime(int(y), int(mo), int(d), int(h or 0), int(mi or 0), int(se or 0),
                      int((frac or '0').ljust(6, '0')[:6]))
    off = 0
    if tz and tz != 'Z':
        sign = -1 if tz[0] == '-' else 1
        tz = tz[1:].replace(':', '')
        off = sign * (int(tz[:2]) * 60 + int(tz[2:]))
    dt = dt.replace(tzinfo=_dt.timezone(_dt.timedelta(minutes=off)))
    return int((dt - EPOCH).total_seconds() * 1000)


def fmt_ts(ms):
    dt = EPOCH + _dt.timedelta(milliseconds=ms)
    return dt.strftime('%Y-%m-%d %H:%M:%S.') + f'{(ms % 1000) * 1000:06d}+0000'


class TimeUUID:
    """v1 UUID that sorts by its timestamp (as Cassandra's TimeUUIDType does)."""
    __slots__ = ('u',)

    def __init__(self, u):
        self.u = u

    @property
    def ms(self):
        return (self.u.time - 0x01b21dd213814000) // 10000

    def key(self):
        return (self.u.time, self.u.bytes)

    def __eq__(self, o):
        return isinstance(o, TimeUUID) and o.u == self.u

    def __hash__(self):
        return hash(self.u)

    def __str__(self):
        return str(self.u)


class UDTVal(dict):
    pass


class Func:
    def __init__(self, name, args):
        self.name, self.args = name, args


# ============================================================ schema objects
class Column:
    def __init__(self, name, ctype, kind='regular'):
        self.name, self.type, self.kind = name, ctype, kind


class Table:
    def __init__(self, ks, name, cols, pk, ck, order, options):
        self.ks, self.name = ks, name
        self.cols = cols                       # name -> Column (declaration order)
        self.pk, self.ck = pk, ck
        self.order = order                     # ck -> 'ASC'/'DESC'
        self.options = options
        self.parts = {}                        # pk tuple -> Partition
        self.indexes = {}                      # index name -> (column, kind, target)
        self.views = []
        self.is_view = False
        self.counter = any(base_t(c.type) == 'counter' for c in cols.values())

    @property
    def full(self):
        return f'{self.ks}.{self.name}'

    def star_cols(self):
        statics = sorted(c for c, v in self.cols.items() if v.kind == 'static')
        regs = sorted(c for c, v in self.cols.items() if v.kind == 'regular')
        return self.pk + self.ck + statics + regs

    def partitions(self, eng):
        return self.parts


class View(Table):
    def __init__(self, ks, name, base, select_cols, pk, ck, order, notnull):
        cols = {}
        for c in pk:
            cols[c] = Column(c, base.cols[c].type, 'partition')
        for c in ck:
            cols[c] = Column(c, base.cols[c].type, 'clustering')
        for c in select_cols:
            if c not in cols:
                cols[c] = Column(c, base.cols[c].type, 'regular')
        super().__init__(ks, name, cols, pk, ck, order, {})
        self.base, self.notnull = base, notnull
        self.is_view = True

    def partitions(self, eng):
        parts = {}
        for bp in eng.ordered_parts(self.base):
            for row in eng.iter_rows(self.base, bp):
                vals = {c: row.get(c) for c in self.cols}
                if any(vals.get(c) is None for c in self.pk + self.ck):
                    continue
                pkey = tuple(vals[c] for c in self.pk)
                part = parts.setdefault(pkey, Partition())
                ckey = tuple(vals[c] for c in self.ck)
                r = part.rows.setdefault(ckey, Row())
                r.marker = (row['__ts'], None)
                for c in self.cols:
                    if c not in self.pk and c not in self.ck and vals.get(c) is not None:
                        r.cells[c] = Cell(vals[c], row['__ts'], None)
        return parts


class Cell:
    __slots__ = ('v', 'ts', 'exp', 'ttl')

    def __init__(self, v, ts, exp, ttl=None):
        self.v, self.ts, self.exp, self.ttl = v, ts, exp, ttl


class Row:
    def __init__(self):
        self.cells = {}
        self.marker = None      # (ts, exp) - written by INSERT
        self.tomb = None        # deletion timestamp


class Partition:
    def __init__(self):
        self.rows = {}
        self.static = {}
        self.tomb = None
        self.ranges = []        # (lo, lo_incl, hi, hi_incl, ts) on clustering prefix tuples


# ============================================================ engine
class Engine:
    START_MS = parse_ts('2026-10-14 10:00:00+0530')

    def __init__(self):
        self.keyspaces = {}
        self.types = {}
        self.ks = None
        self.now_us = self.START_MS * 1000
        self.rnd = random.Random(2026)
        self.consistency = 'ONE'
        self.node = 0x0242ac120002

    # ---------------------------------------------------------- clock
    def tick(self):
        self.now_us += 1000
        return self.now_us

    @property
    def now_s(self):
        return self.now_us // 1_000_000

    def new_timeuuid(self, ms=None):
        if ms is None:
            self.tick()
            t100 = self.now_us * 10 + 0x01b21dd213814000
        else:
            t100 = ms * 10000 + 0x01b21dd213814000
        tl = t100 & 0xffffffff
        tm = (t100 >> 32) & 0xffff
        th = ((t100 >> 48) & 0x0fff) | 0x1000
        cs = 0x8000 | (self.rnd.getrandbits(14))
        return TimeUUID(_uuid.UUID(fields=(tl, tm, th, cs >> 8, cs & 0xff, self.node)))

    # ---------------------------------------------------------- entry point
    def run(self, src):
        """Execute a script; returns list of (statement_text, output_or_None)."""
        results = []
        for kind, body in split_script(src):
            if kind == 'directive':
                m = re.match(r'sleep\s+(\d+)', body)
                if m:
                    self.now_us += int(m.group(1)) * 1_000_000
                continue
            prompt_ks = self.ks
            try:
                toks = tokenize(body)
                p = Parser(toks, self)
                stmt = p.statement()
                out = stmt()
            except CQLError as e:
                out = ('error', e.render())
            results.append((body, out, prompt_ks))
        return results

    # ---------------------------------------------------------- lookup
    def table(self, ks, name, allow_view=True):
        ks = ks or self.ks
        if ks is None:
            raise inv('No keyspace has been specified. USE a keyspace, or explicitly specify keyspace.tablename')
        if ks not in self.keyspaces:
            raise inv(f"Keyspace '{ks}' does not exist")
        t = self.keyspaces[ks]['tables'].get(name)
        if t is None:
            raise inv(f'table {name} does not exist')
        if t.is_view and not allow_view:
            raise inv(f'Cannot directly modify a materialized view')
        return t

    def token_of(self, t, pkvals):
        cols = [t.cols[c] for c in t.pk]
        if len(cols) == 1:
            data = serialize(cols[0].type, pkvals[0])
        else:
            data = b''
            for c, v in zip(cols, pkvals):
                b = serialize(c.type, v)
                data += struct.pack('>H', len(b)) + b + b'\x00'
        return murmur3_token(data)

    def ordered_parts(self, t):
        parts = t.partitions(self)
        keys = sorted(parts, key=lambda k: (self.token_of(t, k), sort_key_tuple([t.cols[c].type for c in t.pk], k)))
        return [(k, parts[k]) for k in keys]

    # ---------------------------------------------------------- liveness
    def live(self, cell, *tombs):
        if cell is None:
            return False
        if cell.exp is not None and cell.exp <= self.now_s:
            return False
        for tb in tombs:
            if tb is not None and cell.ts <= tb:
                return False
        return True

    def row_tombs(self, t, part, ckey):
        tombs = [part.tomb]
        for lo, li, hi, hi_i, ts in part.ranges:
            if in_range(t, ckey, lo, li, hi, hi_i):
                tombs.append(ts)
        r = part.rows.get(ckey)
        if r is not None:
            tombs.append(r.tomb)
        return tombs

    def iter_rows(self, t, item, reverse=False):
        """Yield visible rows of a partition as dicts (with __ts / __cells meta)."""
        pkey, part = item
        types = [t.cols[c].type for c in t.ck]
        statics = {}
        for c, cell in part.static.items():
            if cell.v is not None and self.live(cell, part.tomb):
                statics[c] = cell
        keys = sorted(part.rows, key=lambda k: sort_key_tuple(types, k, [t.order.get(c, 'ASC') for c in t.ck]))
        if reverse:
            keys.reverse()
        any_row = False
        for ck in keys:
            r = part.rows[ck]
            tombs = self.row_tombs(t, part, ck)
            cells = {c: cell for c, cell in r.cells.items() if cell.v is not None and self.live(cell, *tombs)}
            marker_live = r.marker is not None and self.live(Cell(None, r.marker[0], r.marker[1]), *tombs)
            if not cells and not marker_live:
                continue
            any_row = True
            row = dict(zip(t.pk, pkey))
            row.update(zip(t.ck, ck))
            row['__cells'] = dict(cells)
            row['__cells'].update(statics)
            for c, cell in statics.items():
                row[c] = cell.v
            for c, cell in cells.items():
                row[c] = cell.v
            row['__ts'] = max([cl.ts for cl in cells.values()] + ([r.marker[0]] if marker_live else []))
            yield row
        if not any_row and statics:
            row = dict(zip(t.pk, pkey))
            for c in t.ck:
                row[c] = None
            for c, cell in statics.items():
                row[c] = cell.v
            row['__cells'] = dict(statics)
            row['__ts'] = max(cl.ts for cl in statics.values())
            yield row


def in_range(t, ckey, lo, li, hi, hi_i):
    types = [t.cols[c].type for c in t.ck]
    orders = ['ASC'] * len(t.ck)
    k = sort_key_tuple(types, ckey, orders)
    if lo is not None:
        n = len(lo)
        a = sort_key_tuple(types[:n], ckey[:n], orders[:n]); b = sort_key_tuple(types[:n], lo, orders[:n])
        if a < b or (a == b and not li):
            return False
    if hi is not None:
        n = len(hi)
        a = sort_key_tuple(types[:n], ckey[:n], orders[:n]); b = sort_key_tuple(types[:n], hi, orders[:n])
        if a > b or (a == b and not hi_i):
            return False
    return True


# ============================================================ values
def sort_key(ctype, v):
    ct = base_t(ctype)
    if v is None:
        return (0,)
    if isinstance(v, TimeUUID):
        return (1, v.key())
    if isinstance(v, _uuid.UUID):
        return (1, (v.version or 0, v.bytes))
    if isinstance(v, str):
        return (1, v.encode())
    if isinstance(v, (list, tuple)):
        return (1, tuple(sort_key(None, x) for x in v))
    if isinstance(v, dict):
        return (1, tuple(sorted((str(k), str(x)) for k, x in v.items())))
    if isinstance(v, (set, frozenset)):
        return (1, tuple(sorted(sort_key(None, x) for x in v)))
    return (1, v)


class _Rev:
    __slots__ = ('k',)

    def __init__(self, k):
        self.k = k

    def __lt__(self, o):
        return self.k > o.k

    def __gt__(self, o):
        return self.k < o.k

    def __eq__(self, o):
        return self.k == o.k

    def __le__(self, o):
        return self.k >= o.k

    def __ge__(self, o):
        return self.k <= o.k


def sort_key_tuple(types, vals, orders=None):
    out = []
    for i, (t, v) in enumerate(zip(types, vals)):
        k = sort_key(t, v)
        if orders and orders[i] == 'DESC':
            k = _Rev(k)
        out.append(k)
    return tuple(out)


def serialize(ctype, v):
    ct = base_t(ctype)
    if ct == 'int':
        return struct.pack('>i', v)
    if ct in ('bigint', 'counter', 'timestamp'):
        return struct.pack('>q', v)
    if ct == 'smallint':
        return struct.pack('>h', v)
    if ct == 'tinyint':
        return struct.pack('>b', v)
    if ct in ('text', 'varchar', 'ascii'):
        return v.encode('utf-8')
    if ct == 'uuid':
        return v.bytes
    if ct == 'timeuuid':
        return v.u.bytes
    if ct == 'date':
        return struct.pack('>I', (v + (1 << 31)) & 0xffffffff)
    if ct == 'boolean':
        return b'\x01' if v else b'\x00'
    if ct == 'double':
        return struct.pack('>d', v)
    if ct == 'float':
        return struct.pack('>f', v)
    if ct == 'blob':
        return v
    raise inv(f'Unsupported partition key type {tname(ctype)}')


def fmt(ctype, v, nested=False):
    ct = base_t(ctype)
    if v is None:
        return 'null'
    if isinstance(ct, tuple):
        if ct[0] == 'list':
            return '[' + ', '.join(fmt(ct[1], x, True) for x in v) + ']'
        if ct[0] == 'set':
            return '{' + ', '.join(fmt(ct[1], x, True) for x in sorted(v, key=lambda x: sort_key(ct[1], x))) + '}'
        if ct[0] == 'map':
            return '{' + ', '.join(f'{fmt(ct[1], k, True)}: {fmt(ct[2], x, True)}'
                                   for k, x in sorted(v.items(), key=lambda kv: sort_key(ct[1], kv[0]))) + '}'
        if ct[0] == 'udt':
            ftypes = ct[2]
            return '{' + ', '.join(f'{f}: {fmt(ft, v.get(f), True)}' for f, ft in ftypes) + '}'
    if ct in ('text', 'varchar', 'ascii'):
        return "'" + v.replace("'", "''") + "'" if nested else v
    if ct == 'timestamp':
        s = fmt_ts(v)
        return f"'{s}'" if nested else s
    if ct == 'date':
        s = (EPOCH + _dt.timedelta(days=v)).strftime('%Y-%m-%d')
        return f"'{s}'" if nested else s
    if ct == 'boolean':
        return 'True' if v else 'False'
    if ct == 'double':
        return _fmt_float(v, 12)
    if ct == 'float':
        return _fmt_float(v, 5)
    if ct == 'decimal':
        return str(v)
    if ct == 'blob':
        return '0x' + v.hex()
    return str(v)


def _fmt_float(v, prec):
    """cqlsh's format_floating_point_type (float_precision=5, double_precision=12)."""
    import math, sys
    if v != v:
        return 'NaN'
    if v in (float('inf'), float('-inf')):
        return 'Infinity' if v > 0 else '-Infinity'
    exponent = int(math.log10(abs(v))) if abs(v) > sys.float_info.epsilon else -sys.maxsize - 1
    if -4 <= exponent < prec:
        prec = prec + exponent + 1
    return '%.*g' % (prec, v)


def coerce(ctype, v, col, eng):
    """Literal -> stored value, with Cassandra's error messages for type mismatches."""
    ct = base_t(ctype)
    if v is None:
        return None
    if isinstance(v, Func):
        v = eval_func(v, eng, ctype)
        if isinstance(v, tuple) and v and v[0] == '__typed':
            return v[1]
    kind, val = v if isinstance(v, tuple) and v and v[0] in ('int', 'float', 'str', 'bool', 'uuid', 'blob', 'coll', 'list', 'map', 'set', 'udt', 'raw') else ('raw', v)
    label = {'int': 'INTEGER', 'float': 'FLOAT', 'str': 'STRING', 'bool': 'BOOLEAN', 'uuid': 'UUID', 'blob': 'HEX'}.get(kind)

    def bad():
        shown = val if kind != 'str' else val
        return inv(f'Invalid {label} constant ({shown}) for "{col}" of type {tname(ctype)}')
    if kind == 'raw':
        return val
    if isinstance(ct, tuple):
        if ct[0] == 'list':
            if kind not in ('list', 'coll'):
                raise inv(f'Invalid list literal for {col} of type {tname(ctype)}')
            return [coerce(ct[1], x, col, eng) for x in val]
        if ct[0] == 'set':
            if kind not in ('set', 'coll', 'map') or (kind == 'map' and val):
                raise inv(f'Invalid set literal for {col} of type {tname(ctype)}')
            return frozenset(coerce(ct[1], x, col, eng) for x in val) if val else frozenset()
        if ct[0] == 'map':
            if kind not in ('map', 'udt', 'set'):
                raise inv(f'Invalid map literal for {col} of type {tname(ctype)}')
            if kind == 'udt':
                val = [(('str', k), x) for k, x in val]
            return {coerce(ct[1], k, col, eng): coerce(ct[2], x, col, eng) for k, x in val}
        if ct[0] == 'udt':
            if kind != 'udt':
                raise inv(f'Invalid user type literal for {col} of type {ct[1]}')
            fields = dict(ct[2])
            out = UDTVal()
            for k, x in val:
                if k not in fields:
                    raise inv(f'Unknown field \'{k}\' in value of user defined type {ct[1]}')
                out[k] = coerce(fields[k], x, col, eng)
            return out
    if ct in ('int', 'bigint', 'smallint', 'tinyint', 'varint', 'counter'):
        if kind != 'int':
            raise bad()
        n = int(val)
        if ct == 'int' and not -2**31 <= n < 2**31:
            raise inv(f'Invalid INTEGER constant ({val}) for "{col}" of type int')
        return n
    if ct in ('double', 'float'):
        if kind not in ('int', 'float'):
            raise bad()
        return float(val)
    if ct == 'decimal':
        if kind not in ('int', 'float'):
            raise bad()
        return decimal.Decimal(val)
    if ct in ('text', 'varchar', 'ascii'):
        if kind != 'str':
            raise bad()
        return val
    if ct == 'boolean':
        if kind != 'bool':
            raise bad()
        return val
    if ct == 'uuid':
        if kind != 'uuid':
            raise bad()
        return _uuid.UUID(val)
    if ct == 'timeuuid':
        if kind != 'uuid':
            raise bad()
        u = _uuid.UUID(val)
        if u.version != 1:
            raise inv(f'Unsupported UUID version for timeuuid: {u.version}')
        return TimeUUID(u)
    if ct == 'timestamp':
        if kind == 'int':
            return int(val)
        if kind == 'str':
            try:
                return parse_ts(val)
            except ValueError:
                raise inv(f"Unable to parse a date/time from '{val}'")
        raise bad()
    if ct == 'date':
        if kind == 'str':
            try:
                return parse_ts(val) // 86400000
            except ValueError:
                raise inv(f"Unable to coerce '{val}' to a formatted date (long)")
        raise bad()
    if ct == 'blob':
        if kind != 'blob':
            raise bad()
        return bytes.fromhex(val[2:])
    return val


def eval_func(f, eng, want=None):
    """Evaluate a function used as a value. Always returns ('__typed', value)."""
    n = f.name
    if n == 'now':
        return ('__typed', eng.new_timeuuid())
    if n == 'uuid':
        return ('__typed', _uuid.UUID(int=eng.rnd.getrandbits(128), version=4))
    if n == 'currenttimestamp':
        eng.tick()
        return ('__typed', eng.now_us // 1000)
    if n == 'currentdate':
        return ('__typed', eng.now_us // 1000 // 86400000)
    if n in ('totimestamp', 'todate', 'tounixtimestamp'):
        a = f.args[0]
        inner = eval_func(a, eng)[1] if isinstance(a, Func) else a
        ms = inner.ms if isinstance(inner, TimeUUID) else inner
        return ('__typed', ms // 86400000 if n == 'todate' else ms)
    if n in ('mintimeuuid', 'maxtimeuuid'):
        ms = parse_ts(f.args[0][1])
        t100 = ms * 10000 + 0x01b21dd213814000 + (0 if n == 'mintimeuuid' else 9999)
        tl, tm, th = t100 & 0xffffffff, (t100 >> 32) & 0xffff, ((t100 >> 48) & 0x0fff) | 0x1000
        node, cs = (0x808080808080, 0x8080) if n == 'mintimeuuid' else (0x7f7f7f7f7f7f, 0x7f7f)
        return ('__typed', TimeUUID(_uuid.UUID(fields=(tl, tm, th, cs >> 8, cs & 0xff, node))))
    raise inv(f'Unknown function {n}')


# ============================================================ script splitting
def split_script(src):
    """Split on top-level ';' (BATCH bodies stay together). Lines starting with '!' are directives."""
    out, buf = [], []
    lines = src.split('\n')
    text = ''
    for ln in lines:
        if ln.strip().startswith('!'):
            if text.strip():
                out.extend(_split_stmts(text))
                text = ''
            out.append(('directive', ln.strip()[1:].strip()))
        else:
            text += ln + '\n'
    if text.strip():
        out.extend(_split_stmts(text))
    return out


def _split_stmts(text):
    res, cur, i, in_batch = [], '', 0, False
    toks = list(TOKEN_RE.finditer(text))
    start = 0
    words = []
    for m in toks:
        g = m.lastgroup
        t = m.group(g)
        if g == 'id':
            words.append(t.lower())
            if t.lower() == 'batch' and len(words) >= 2 and words[-2] in ('begin', 'unlogged', 'logged', 'counter'):
                in_batch = True
            if t.lower() == 'batch' and len(words) >= 2 and words[-2] == 'apply':
                in_batch = False
        if g == 'op' and t == ';' and not in_batch:
            stmt = text[start:m.end()].strip()
            if stmt.strip(';').strip():
                res.append(('cql', stmt))
            start = m.end()
            words = []
    tail = text[start:].strip()
    if tail and not re.fullmatch(r'(\s|--[^\n]*|//[^\n]*)*', tail):
        res.append(('cql', tail))
    return res


# ============================================================ parser
class Parser:
    def __init__(self, toks, eng):
        self.t, self.i, self.eng = toks, 0, eng

    # ---- token helpers
    @property
    def cur(self):
        return self.t[self.i]

    def peek(self, n=1):
        return self.t[min(self.i + n, len(self.t) - 1)]

    def at(self, *words):
        c = self.cur
        return c.kind == 'id' and c.val in words or (c.kind == 'op' and c.val in words)

    def at_seq(self, *words):
        for k, w in enumerate(words):
            c = self.peek(k)
            if not ((c.kind == 'id' and c.val == w) or (c.kind == 'op' and c.val == w)):
                return False
        return True

    def take(self, *words):
        if self.at(*words):
            v = self.cur.val
            self.i += 1
            return v
        return None

    def expect(self, *words):
        v = self.take(*words)
        if v is None:
            raise CQLError(f"line 1:0 mismatched input '{self.cur.raw}' expecting {words[0]!r}", 'SyntaxException')
        return v

    def ident(self):
        c = self.cur
        if c.kind != 'id':
            raise CQLError(f"line 1:0 no viable alternative at input '{c.raw}'", 'SyntaxException')
        self.i += 1
        return c.val

    def qname(self):
        a = self.ident()
        if self.take('.'):
            return a, self.ident()
        return None, a

    # ---- statements
    def statement(self):
        if self.take('use'):
            ks = self.ident()
            return lambda: self.eng_use(ks)
        if self.take('create'):
            if self.take('keyspace'):
                return self.create_keyspace()
            if self.take('table'):
                return self.create_table()
            if self.take('type'):
                return self.create_type()
            if self.take('materialized'):
                self.expect('view')
                return self.create_mv()
            custom = bool(self.take('custom'))
            if self.take('index'):
                return self.create_index(custom)
        if self.take('alter'):
            return self.alter()
        if self.take('drop'):
            return self.drop()
        if self.take('truncate'):
            self.take('table')
            ks, n = self.qname()
            return lambda: self.do_truncate(ks, n)
        if self.take('insert'):
            return self.insert()
        if self.take('update'):
            return self.update()
        if self.take('delete'):
            return self.delete()
        if self.take('select'):
            return self.select()
        if self.take('begin', 'apply'):
            self.i -= 1
            return self.batch()
        if self.take('consistency'):
            if self.cur.kind == 'id':
                lvl = self.ident().upper()
                def f():
                    self.eng.consistency = lvl
                    return ('text', f'Consistency level set to {lvl}.')
                return f
            return lambda: ('text', f'Current consistency level is {self.eng.consistency}.')
        raise CQLError(f"line 1:0 no viable alternative at input '{self.cur.raw}'", 'SyntaxException')

    def eng_use(self, ks):
        if ks not in self.eng.keyspaces:
            raise inv(f"Keyspace '{ks}' does not exist")
        self.eng.ks = ks
        return None

    def if_not_exists(self):
        if self.at_seq('if', 'not', 'exists'):
            self.i += 3
            return True
        return False

    def if_exists(self):
        if self.at_seq('if', 'exists'):
            self.i += 2
            return True
        return False

    def create_keyspace(self):
        ine = self.if_not_exists()
        name = self.ident()
        self.expect('with')
        opts = self.options()
        def f():
            if name in self.eng.keyspaces:
                if ine:
                    return None
                raise CQLError(f"Keyspace '{name}' already exists", 'AlreadyExists', '2400 [Query invalid because of configuration issue]')
            rep = opts.get('replication')
            if not rep or 'class' not in rep:
                raise CQLError('Missing mandatory option \'class\'', 'ConfigurationException', '2300 [Query invalid because of configuration issue]')
            self.eng.keyspaces[name] = {'tables': {}, 'replication': rep}
            return None
        return f

    def options(self):
        opts = {}
        while True:
            if self.take('clustering'):
                self.expect('order'); self.expect('by'); self.expect('(')
                order = {}
                while True:
                    c = self.ident()
                    order[c] = (self.take('asc', 'desc') or 'asc').upper()
                    if not self.take(','):
                        break
                self.expect(')')
                opts['__order'] = order
            elif self.take('compact'):
                self.expect('storage')
            else:
                k = self.ident()
                self.expect('=')
                opts[k] = self.literal_plain()
            if not self.take('and'):
                break
        return opts

    def literal_plain(self):
        v = self.term()
        return plain(v)

    def ctype(self):
        n = self.ident()
        if n == 'frozen':
            self.expect('<'); inner = self.ctype(); self.expect('>')
            return ('frozen', inner)
        if n in ('list', 'set'):
            self.expect('<'); inner = self.ctype(); self.expect('>')
            return (n, inner)
        if n == 'map':
            self.expect('<'); k = self.ctype(); self.expect(','); v = self.ctype(); self.expect('>')
            return ('map', k, v)
        if n in SIMPLE:
            return n
        ks = self.eng.ks
        key = (ks, n)
        if key not in self.eng.types:
            raise inv(f'Unknown type {ks}.{n}')
        return ('udt', n, self.eng.types[key])

    def create_type(self):
        ine = self.if_not_exists()
        ks, n = self.qname()
        self.expect('(')
        fields = []
        while True:
            f = self.ident(); t = self.ctype(); fields.append((f, t))
            if not self.take(','):
                break
        self.expect(')')
        def run():
            key = (ks or self.eng.ks, n)
            if key in self.eng.types and not ine:
                raise CQLError(f'A user type with name \'{n}\' already exists', 'InvalidRequest')
            self.eng.types[key] = fields
        return run

    def create_table(self):
        ine = self.if_not_exists()
        ks, name = self.qname()
        self.expect('(')
        cols, pk, ck, statics = {}, [], [], set()
        while True:
            if self.take('primary'):
                self.expect('key'); self.expect('(')
                if self.take('('):
                    while True:
                        pk.append(self.ident())
                        if not self.take(','):
                            break
                    self.expect(')')
                else:
                    pk.append(self.ident())
                while self.take(','):
                    ck.append(self.ident())
                self.expect(')')
            else:
                c = self.ident()
                t = self.ctype()
                cols[c] = t
                if self.take('static'):
                    statics.add(c)
                if self.take('primary'):
                    self.expect('key')
                    pk = [c]
            if not self.take(','):
                break
        self.expect(')')
        opts = {}
        if self.take('with'):
            opts = self.options()

        def run():
            ksn = ks or self.eng.ks
            if ksn is None:
                raise inv('No keyspace has been specified. USE a keyspace, or explicitly specify keyspace.tablename')
            if ksn not in self.eng.keyspaces:
                raise inv(f"Keyspace '{ksn}' does not exist")
            tabs = self.eng.keyspaces[ksn]['tables']
            if name in tabs:
                if ine:
                    return None
                raise CQLError(f"Table '{ksn}.{name}' already exists", 'AlreadyExists', '2400 [Query invalid because of configuration issue]')
            if not pk:
                raise inv(f'No PRIMARY KEY specifed for table \'{name}\' (exactly one required)')
            for c in pk + ck:
                if c not in cols:
                    raise inv(f'Unknown definition {c} referenced in PRIMARY KEY')
                bt = base_t(cols[c])
                if isinstance(bt, tuple) and bt[0] in ('list', 'set', 'map') and not (isinstance(cols[c], tuple) and cols[c][0] == 'frozen'):
                    raise inv(f'Invalid non-frozen collection type for PRIMARY KEY component {c}')
            col_objs = {}
            for c, t in cols.items():
                kind = 'partition' if c in pk else 'clustering' if c in ck else 'static' if c in statics else 'regular'
                col_objs[c] = Column(c, t, kind)
            if statics and not ck:
                raise inv('Static columns are only useful (and thus allowed) if the table has at least one clustering column')
            counters = [c for c in cols if base_t(cols[c]) == 'counter']
            if counters and len(counters) != len([c for c in cols if c not in pk and c not in ck]):
                raise CQLError('Cannot mix counter and non counter columns in the same table', 'ConfigurationException', '2300 [Query invalid because of configuration issue]')
            order = {c: 'ASC' for c in ck}
            for c, d in opts.pop('__order', {}).items():
                if c not in ck:
                    raise inv(f'Only clustering key columns can be defined in CLUSTERING ORDER directive: {c} is not a clustering column')
                order[c] = d
            tabs[name] = Table(ksn, name, col_objs, pk, ck, order, opts)
            return None
        return run

    def create_index(self, custom):
        ine = self.if_not_exists()
        iname = None
        if not self.at('on'):
            iname = self.ident()
        self.expect('on')
        ks, tn = self.qname()
        self.expect('(')
        kind = 'values'
        if self.at('keys', 'values', 'entries', 'full') and self.peek().val == '(':
            kind = self.ident(); self.expect('('); col = self.ident(); self.expect(')')
        else:
            col = self.ident()
        self.expect(')')
        using = None
        if self.take('using'):
            using = self.cur.val; self.i += 1
        if self.take('with'):
            self.options()
        sai = bool(using) and using.lower() in ('storageattachedindex', 'sai', 'org.apache.cassandra.index.sai.storageattachedindex')

        def run():
            t = self.eng.table(ks, tn, False)
            if col not in t.cols:
                raise inv(f'Undefined column name {col} in table {t.full}')
            c = t.cols[col]
            if c.kind == 'partition' and len(t.pk) == 1:
                raise inv(f'Cannot create secondary index on the only partition key column {col}')
            name = iname or f'{tn}_{col}_idx'
            if name in t.indexes:
                if ine:
                    return None
                raise inv(f'Index \'{name}\' already exists')
            t.indexes[name] = (col, 'sai' if sai else '2i', kind)
            return None
        return run

    def create_mv(self):
        ine = self.if_not_exists()
        ks, name = self.qname()
        self.expect('as'); self.expect('select')
        sel = []
        if self.take('*'):
            sel = ['*']
        else:
            while True:
                sel.append(self.ident())
                if not self.take(','):
                    break
        self.expect('from')
        bks, bname = self.qname()
        self.expect('where')
        notnull = []
        while True:
            c = self.ident(); self.expect('is'); self.expect('not'); self.expect('null')
            notnull.append(c)
            if not self.take('and'):
                break
        self.expect('primary'); self.expect('key'); self.expect('(')
        pk, ck = [], []
        if self.take('('):
            while True:
                pk.append(self.ident())
                if not self.take(','):
                    break
            self.expect(')')
        else:
            pk.append(self.ident())
        while self.take(','):
            ck.append(self.ident())
        self.expect(')')
        opts = self.options() if self.take('with') else {}

        def run():
            base = self.eng.table(bks, bname, False)
            cols = list(base.cols) if sel == ['*'] else sel
            for c in base.pk + base.ck:
                if c not in pk + ck:
                    raise inv(f'Cannot create materialized view {name} without primary key columns {c} from base {bname}')
            for c in pk + ck:
                if c not in notnull:
                    raise inv(f'Primary key columns {c} must be restricted with \'IS NOT NULL\' or otherwise')
            v = View(base.ks, name, base, cols, pk, ck, {c: 'ASC' for c in ck}, notnull)
            for c, d in opts.get('__order', {}).items():
                v.order[c] = d
            self.eng.keyspaces[base.ks]['tables'][name] = v
            base.views.append(name)
            return ('warn', 'Materialized views are experimental and are not recommended for production use.')
        return run

    def alter(self):
        self.expect('table')
        ks, n = self.qname()
        if self.take('add'):
            c = self.ident(); t = self.ctype()
            def run():
                tb = self.eng.table(ks, n, False)
                if c in tb.cols:
                    raise inv(f'Column with name \'{c}\' already exists')
                tb.cols[c] = Column(c, t, 'regular')
            return run
        if self.take('drop'):
            c = self.ident()
            def run():
                tb = self.eng.table(ks, n, False)
                if c not in tb.cols:
                    raise inv(f'Column {c} was not found in table {n}')
                if tb.cols[c].kind in ('partition', 'clustering'):
                    raise inv(f'Cannot drop PRIMARY KEY column {c}')
                del tb.cols[c]
                for p in tb.parts.values():
                    for r in p.rows.values():
                        r.cells.pop(c, None)
            return run
        if self.take('with'):
            opts = self.options()
            def run():
                tb = self.eng.table(ks, n, False)
                tb.options.update(opts)
            return run
        raise CQLError('line 1:0 unsupported ALTER', 'SyntaxException')

    def drop(self):
        what = self.ident()
        if what == 'materialized':
            self.expect('view'); what = 'view'
        ie = self.if_exists()
        ks, n = self.qname()

        def run():
            if what == 'keyspace':
                if n not in self.eng.keyspaces:
                    if ie:
                        return None
                    raise inv(f"Keyspace '{n}' doesn't exist")
                del self.eng.keyspaces[n]
                if self.eng.ks == n:
                    self.eng.ks = None
                return None
            if what in ('table', 'view'):
                try:
                    t = self.eng.table(ks, n)
                except CQLError:
                    if ie:
                        return None
                    raise
                if what == 'table' and t.views:
                    raise inv(f'Cannot drop table when materialized views still depend on it ({t.ks}.{{{", ".join(t.views)}}})')
                del self.eng.keyspaces[t.ks]['tables'][n]
                if t.is_view:
                    t.base.views.remove(n)
                return None
            if what == 'index':
                for k in self.eng.keyspaces.values():
                    for t in k['tables'].values():
                        if n in t.indexes:
                            del t.indexes[n]
                            return None
                if ie:
                    return None
                raise inv(f'Index \'{n}\' could not be found in any of the tables of keyspace \'{self.eng.ks}\'')
            if what == 'type':
                self.eng.types.pop((ks or self.eng.ks, n), None)
                return None
        return run

    def do_truncate(self, ks, n):
        t = self.eng.table(ks, n, False)
        t.parts = {}
        return None

    # ---- terms
    def term(self):
        c = self.cur
        if c.kind == 'op' and c.val == '-' and self.peek().kind == 'num':
            self.i += 2
            n = self.t[self.i - 1].val
            return ('float', '-' + n) if re.search(r'[.eE]', n) else ('int', '-' + n)
        if c.kind == 'num':
            self.i += 1
            return ('float', c.val) if re.search(r'[.eE]', c.val) else ('int', c.val)
        if c.kind == 'str':
            self.i += 1
            return ('str', c.val)
        if c.kind == 'uuid':
            self.i += 1
            return ('uuid', c.val)
        if c.kind == 'blob':
            self.i += 1
            return ('blob', c.val)
        if c.kind == 'id' and c.val in ('true', 'false'):
            self.i += 1
            return ('bool', c.val == 'true')
        if c.kind == 'id' and c.val == 'null':
            self.i += 1
            return None
        if c.kind == 'id' and c.val in ('nan', 'infinity'):
            self.i += 1
            return ('float', c.val)
        if c.kind == 'op' and c.val == '[':
            self.i += 1
            items = []
            if not self.take(']'):
                while True:
                    items.append(self.term())
                    if not self.take(','):
                        break
                self.expect(']')
            return ('list', items)
        if c.kind == 'op' and c.val == '{':
            self.i += 1
            if self.take('}'):
                return ('map', [])
            # UDT literal: {field: value}
            if self.cur.kind == 'id' and self.peek().kind == 'op' and self.peek().val == ':':
                items = []
                while True:
                    f = self.ident(); self.expect(':'); items.append((f, self.term()))
                    if not self.take(','):
                        break
                self.expect('}')
                return ('udt', items)
            first = self.term()
            if self.take(':'):
                items = [(first, self.term())]
                while self.take(','):
                    k = self.term(); self.expect(':'); items.append((k, self.term()))
                self.expect('}')
                return ('map', items)
            items = [first]
            while self.take(','):
                items.append(self.term())
            self.expect('}')
            return ('set', items)
        if c.kind == 'op' and c.val == '(':
            self.i += 1
            items = []
            while True:
                items.append(self.term())
                if not self.take(','):
                    break
            self.expect(')')
            return ('tuple', items)
        if c.kind == 'id' and self.peek().kind == 'op' and self.peek().val == '(':
            name = self.ident(); self.expect('(')
            args = []
            if not self.take(')'):
                while True:
                    args.append(self.term())
                    if not self.take(','):
                        break
                self.expect(')')
            return Func(name, args)
        raise CQLError(f"line 1:0 no viable alternative at input '{c.raw}'", 'SyntaxException')

    # ---- DML
    def using(self):
        ttl = ts = None
        if self.take('using'):
            while True:
                if self.take('ttl'):
                    ttl = int(self.term()[1])
                elif self.take('timestamp'):
                    ts = int(self.term()[1])
                if not self.take('and'):
                    break
        return ttl, ts

    def insert(self):
        self.expect('into')
        ks, n = self.qname()
        if self.take('json'):
            js = self.term()[1]
            data = json.loads(js)
            cols = list(data)
            vals = [('raw_json', data[c]) for c in cols]
        else:
            self.expect('(')
            cols = []
            while True:
                cols.append(self.ident())
                if not self.take(','):
                    break
            self.expect(')'); self.expect('values'); self.expect('(')
            vals = []
            while True:
                vals.append(self.term())
                if not self.take(','):
                    break
            self.expect(')')
        ine = self.if_not_exists()
        ttl, ts = self.using()

        def run(batch_ts=None):
            t = self.eng.table(ks, n, False)
            if t.counter:
                raise inv('INSERT statements are not allowed on counter tables, use UPDATE instead')
            if len(cols) != len(vals):
                raise inv('Unmatched column names/values')
            vmap = {}
            for c, v in zip(cols, vals):
                if c not in t.cols:
                    raise inv(f'Undefined column name {c} in table {t.full}')
                if isinstance(v, tuple) and v[0] == 'raw_json':
                    vmap[c] = from_json(t.cols[c].type, v[1], c, self.eng)
                else:
                    vmap[c] = coerce(t.cols[c].type, v, c, self.eng)
            static_only = bool(t.ck) and all(c in t.pk or t.cols[c].kind == 'static' for c in vmap) \
                and any(t.cols[c].kind == 'static' for c in vmap)
            if static_only:
                miss = [c for c in t.pk if vmap.get(c) is None]
                if miss:
                    raise inv(f'Some partition key parts are missing: {", ".join(miss)}')
            else:
                check_keys(t, vmap, 'insert')
            pkey = tuple(vmap[c] for c in t.pk)
            ckey = tuple(vmap.get(c) for c in t.ck)
            stamp = ts if ts is not None else (batch_ts or self.eng.tick())
            if ine:
                existing = self.eng_row(t, pkey, ckey)
                if existing is not None:
                    return lwt_result(t, False, existing, t.star_cols())
            ttl_ = ttl if ttl is not None else int(t.options.get('default_time_to_live', 0) or 0)
            exp = self.eng.now_s + ttl_ if ttl_ else None
            part = t.parts.setdefault(pkey, Partition())
            row = Row() if static_only else part.rows.setdefault(ckey if t.ck else (), Row())
            if not static_only and (row.marker is None or row.marker[0] <= stamp):
                row.marker = (stamp, exp)
            for c, v in vmap.items():
                if c in t.pk or c in t.ck:
                    continue
                target = part.static if t.cols[c].kind == 'static' else row.cells
                write_cell(target, c, v, stamp, exp, ttl_)
            if ine:
                return lwt_result(t, True)
            return None
        return run

    def eng_row(self, t, pkey, ckey):
        part = t.parts.get(pkey)
        if part is None:
            return None
        for r in self.eng.iter_rows(t, (pkey, part)):
            if tuple(r[c] for c in t.ck) == ckey:
                return r
        return None

    def where(self):
        rels = []
        while True:
            if self.at('token') and self.peek().val == '(':
                self.ident(); self.expect('(')
                cols = []
                while True:
                    cols.append(self.ident())
                    if not self.take(','):
                        break
                self.expect(')')
                lhs = ('token', tuple(cols))
            else:
                lhs = self.ident()
            if self.at_seq('contains', 'key'):
                self.i += 2; op = 'CONTAINS KEY'
            elif self.take('contains'):
                op = 'CONTAINS'
            elif self.take('in'):
                op = 'IN'
            elif self.at_seq('is', 'not'):
                self.i += 2; self.expect('null'); op = 'IS NOT NULL'
                rels.append((lhs, op, None))
                if not self.take('and'):
                    break
                continue
            elif self.take('like'):
                op = 'LIKE'
            else:
                op = self.cur.val
                if op not in ('=', '<', '>', '<=', '>=', '!='):
                    raise CQLError(f"line 1:0 no viable alternative at input '{self.cur.raw}'", 'SyntaxException')
                self.i += 1
            if op == 'IN':
                self.expect('(')
                vals = []
                while True:
                    vals.append(self.term())
                    if not self.take(','):
                        break
                self.expect(')')
                rels.append((lhs, op, vals))
            else:
                rels.append((lhs, op, self.term()))
            if not self.take('and'):
                break
        return rels

    def conditions(self):
        if self.at_seq('if', 'exists'):
            self.i += 2
            return 'exists'
        if self.take('if'):
            conds = []
            while True:
                c = self.ident()
                op = self.cur.val; self.i += 1
                if op == 'in':
                    op = 'IN'
                    self.expect('(')
                    vs = []
                    while True:
                        vs.append(self.term())
                        if not self.take(','):
                            break
                    self.expect(')')
                    conds.append((c, op, vs))
                else:
                    conds.append((c, op, self.term()))
                if not self.take('and'):
                    break
            return conds
        return None

    def update(self):
        ks, n = self.qname()
        ttl, ts = self.using()
        self.expect('set')
        sets = []
        while True:
            c = self.ident()
            if self.take('['):
                key = self.term(); self.expect(']'); self.expect('=')
                sets.append((c, 'put', (key, self.term())))
            else:
                self.expect('=')
                if self.cur.kind == 'id' and self.cur.val == c and self.peek().val in ('+', '-'):
                    self.i += 1
                    op = self.cur.val; self.i += 1
                    sets.append((c, 'add' if op == '+' else 'sub', self.term()))
                else:
                    v = self.term()
                    if self.at('+') and self.peek().kind == 'id' and self.peek().val == c:
                        self.i += 2
                        sets.append((c, 'prepend', v))
                    else:
                        sets.append((c, 'set', v))
            if not self.take(','):
                break
        self.expect('where')
        rels = self.where()
        conds = self.conditions()

        def run(batch_ts=None):
            t = self.eng.table(ks, n, False)
            for c, _, _ in sets:
                if c not in t.cols:
                    raise inv(f'Undefined column name {c} in table {t.full}')
                if t.cols[c].kind in ('partition', 'clustering'):
                    raise inv(f'PRIMARY KEY part {c} found in SET part')
            only_static = all(t.cols[c].kind == 'static' for c, _, _ in sets)
            keys = key_sets(t, rels, 'update', only_static, self.eng)
            stamp = ts if ts is not None else (batch_ts or self.eng.tick())
            ttl_ = ttl if ttl is not None else int(t.options.get('default_time_to_live', 0) or 0)
            exp = self.eng.now_s + ttl_ if ttl_ else None
            results = None
            for pkey, ckey in keys:
                if conds is not None:
                    cur = self.eng_row(t, pkey, ckey) if t.ck and not only_static else self.static_or_row(t, pkey, ckey)
                    if conds == 'exists':
                        if cur is None:
                            return lwt_result(t, False)
                    else:
                        ok, shown = check_conds(t, cur, conds, self.eng)
                        if not ok:
                            return lwt_result(t, False, cur, [c for c, _, _ in conds], allow_null_row=True)
                    results = lwt_result(t, True)
                part = t.parts.setdefault(pkey, Partition())
                row = part.rows.setdefault(ckey, Row()) if not only_static else None
                for c, op, v in sets:
                    col = t.cols[c]
                    target = part.static if col.kind == 'static' else row.cells
                    ct = base_t(col.type)
                    if ct == 'counter':
                        if op not in ('add', 'sub'):
                            raise inv(f'Cannot set the value of counter column {c} (counters can only be incremented/decremented, not set)')
                        cur = target.get(c)
                        base_v = cur.v if cur is not None else 0
                        delta = int(v[1]) * (1 if op == 'add' else -1)
                        target[c] = Cell(base_v + delta, stamp, None)
                        continue
                    if t.counter:
                        raise inv('Cannot mix counter and non counter columns in the same table')
                    if op == 'set':
                        write_cell(target, c, coerce(col.type, v, c, self.eng), stamp, exp, ttl_)
                    elif op in ('add', 'sub', 'prepend', 'put'):
                        if not isinstance(ct, tuple):
                            raise inv(f'Invalid operation ({c} = {c} + ?) for non counter column {c}')
                        cur = target.get(c)
                        curv = cur.v if (cur is not None and self.eng.live(cur, part.tomb)) else None
                        if op == 'put':
                            k = coerce(ct[1], v[0], c, self.eng)
                            new = dict(curv or {}); val = coerce(ct[2], v[1], c, self.eng)
                            if val is None:
                                new.pop(k, None)
                            else:
                                new[k] = val
                        else:
                            arg = coerce(col.type, v, c, self.eng)
                            if ct[0] == 'list':
                                if op == 'add':
                                    new = list(curv or []) + list(arg)
                                elif op == 'prepend':
                                    new = list(arg) + list(curv or [])
                                else:
                                    new = [x for x in (curv or []) if x not in arg]
                            elif ct[0] == 'set':
                                new = frozenset(curv or ()) | arg if op == 'add' else frozenset(curv or ()) - arg
                            else:
                                if op == 'add':
                                    new = dict(curv or {}); new.update(arg)
                                else:
                                    new = {k: x for k, x in (curv or {}).items() if k not in arg}
                        write_cell(target, c, new if new else None, stamp, exp, ttl_)
            return results
        return run

    def static_or_row(self, t, pkey, ckey):
        part = t.parts.get(pkey)
        if part is None:
            return None
        for r in self.eng.iter_rows(t, (pkey, part)):
            return r
        return None

    def delete(self):
        cols = []
        if not self.at('from'):
            while True:
                c = self.ident()
                if self.take('['):
                    k = self.term(); self.expect(']'); cols.append((c, k))
                else:
                    cols.append((c, None))
                if not self.take(','):
                    break
        self.expect('from')
        ks, n = self.qname()
        _, ts = self.using()
        self.expect('where')
        rels = self.where()
        conds = self.conditions()

        def run(batch_ts=None):
            t = self.eng.table(ks, n, False)
            stamp = ts if ts is not None else (batch_ts or self.eng.tick())
            for c, _ in cols:
                if c not in t.cols:
                    raise inv(f'Undefined column name {c} in table {t.full}')
                if t.cols[c].kind in ('partition', 'clustering'):
                    raise inv(f'Invalid identifier {c} for deletion (should not be a PRIMARY KEY part)')
            res = None
            if cols:
                keys = key_sets(t, rels, 'delete_cols', False, self.eng)
            else:
                keys = None
            pk_rels, ck_rels = split_key_rels(t, rels)
            if conds is not None:
                pkeys = key_sets(t, rels, 'update', False, self.eng)
                for pkey, ckey in pkeys:
                    cur = self.eng_row(t, pkey, ckey)
                    if conds == 'exists':
                        if cur is None:
                            return lwt_result(t, False)
                    else:
                        ok, _ = check_conds(t, cur, conds, self.eng)
                        if not ok:
                            return lwt_result(t, False, cur, [c for c, _, _ in conds], allow_null_row=True)
                res = lwt_result(t, True)
            if cols:
                for pkey, ckey in keys:
                    part = t.parts.setdefault(pkey, Partition())
                    for c, k in cols:
                        target = part.static if t.cols[c].kind == 'static' else part.rows.setdefault(ckey, Row()).cells
                        if k is not None:
                            cur = target.get(c)
                            if cur is not None:
                                ct = base_t(t.cols[c].type)
                                kk = coerce(ct[1] if ct[0] == 'map' else 'int', k, c, self.eng)
                                if ct[0] == 'map':
                                    nv = {a: b for a, b in cur.v.items() if a != kk}
                                else:
                                    nv = [x for i, x in enumerate(cur.v) if i != kk]
                                target[c] = Cell(nv or None, stamp, cur.exp)
                        else:
                            target[c] = Cell(None, stamp, None)
                return res
            # row / range / partition deletion
            pkeys = pk_values(t, pk_rels, self.eng, 'delete')
            for pkey in pkeys:
                part = t.parts.setdefault(pkey, Partition())
                if not ck_rels:
                    part.tomb = max(part.tomb or 0, stamp)
                    continue
                eq, lo, li, hi, hi_i = clustering_bounds(t, ck_rels, self.eng)
                if len(eq) == len(t.ck) and lo is None and hi is None:
                    for ck in eq_product(eq):
                        part.rows.setdefault(ck, Row()).tomb = stamp
                else:
                    for prefix in eq_product(eq) if eq else [()]:
                        rlo = prefix + lo if lo is not None else (prefix if prefix else None)
                        rhi = prefix + hi if hi is not None else (prefix if prefix else None)
                        part.ranges.append((rlo, li if lo is not None else True, rhi, hi_i if hi is not None else True, stamp))
            return res
        return run

    def batch(self):
        self.expect('begin')
        kind = self.take('unlogged', 'logged', 'counter') or 'logged'
        self.expect('batch')
        _, ts = self.using()
        stmts = []
        while not self.at('apply'):
            if self.take('insert'):
                stmts.append(self.insert())
            elif self.take('update'):
                stmts.append(self.update())
            elif self.take('delete'):
                stmts.append(self.delete())
            else:
                raise CQLError(f"line 1:0 no viable alternative at input '{self.cur.raw}'", 'SyntaxException')
            self.take(';')
        self.expect('apply'); self.expect('batch')

        def run():
            stamp = ts if ts is not None else self.eng.tick()
            out = None
            for s in stmts:
                r = s(batch_ts=stamp)
                if r is not None:
                    out = r
            return out
        return run

    # ---- SELECT
    def select(self):
        js = bool(self.take('json'))
        distinct = bool(self.take('distinct'))
        sels = []
        if self.take('*'):
            sels = ['*']
        else:
            while True:
                e = self.sel_expr()
                alias = None
                if self.take('as'):
                    alias = self.ident()
                sels.append((e, alias))
                if not self.take(','):
                    break
        self.expect('from')
        ks, n = self.qname()
        rels = []
        if self.take('where'):
            rels = self.where()
        group = []
        if self.take('group'):
            self.expect('by')
            while True:
                group.append(self.ident())
                if not self.take(','):
                    break
        order = []
        if self.take('order'):
            self.expect('by')
            while True:
                c = self.ident()
                order.append((c, (self.take('asc', 'desc') or 'asc').upper()))
                if not self.take(','):
                    break
        ppl = limit = None
        if self.at_seq('per', 'partition', 'limit'):
            self.i += 3
            ppl = int(self.term()[1])
        if self.take('limit'):
            limit = int(self.term()[1])
        allow = False
        if self.at_seq('allow', 'filtering'):
            self.i += 2
            allow = True
        return lambda: run_select(self.eng, ks, n, sels, rels, group, order, ppl, limit, allow, distinct, js)

    def sel_expr(self):
        c = self.cur
        if c.kind == 'id' and self.peek().val == '(':
            name = self.ident(); self.expect('(')
            if name == 'count' and self.take('*'):
                self.expect(')')
                return ('agg', 'count', '*')
            args = []
            if not self.take(')'):
                while True:
                    args.append(self.sel_expr())
                    if not self.take(','):
                        break
                self.expect(')')
            if name == 'cast':
                pass
            return ('fn', name, args)
        if c.kind in ('num', 'str'):
            return ('lit', self.term())
        return ('col', self.ident())


# ============================================================ DML helpers
def plain(v):
    if v is None:
        return None
    if isinstance(v, Func):
        return v
    k, val = v
    if k == 'int':
        return int(val)
    if k == 'float':
        return float(val)
    if k in ('str', 'uuid', 'bool', 'blob'):
        return val
    if k in ('list', 'set', 'tuple'):
        return [plain(x) for x in val]
    if k == 'map':
        return {plain(a): plain(b) for a, b in val}
    if k == 'udt':
        return {a: plain(b) for a, b in val}
    return val


def write_cell(target, c, v, stamp, exp, ttl=None):
    cur = target.get(c)
    if cur is not None and cur.ts > stamp:
        return                       # last write wins
    target[c] = Cell(v, stamp, exp, ttl)


def from_json(ctype, v, col, eng):
    ct = base_t(ctype)
    if v is None:
        return None
    if isinstance(ct, tuple):
        if ct[0] == 'list':
            return [from_json(ct[1], x, col, eng) for x in v]
        if ct[0] == 'set':
            return frozenset(from_json(ct[1], x, col, eng) for x in v)
        if ct[0] == 'map':
            return {from_json(ct[1], k, col, eng): from_json(ct[2], x, col, eng) for k, x in v.items()}
        if ct[0] == 'udt':
            f = dict(ct[2])
            return UDTVal({k: from_json(f[k], x, col, eng) for k, x in v.items()})
    if isinstance(v, bool):
        return coerce(ctype, ('bool', v), col, eng)
    if isinstance(v, int):
        return coerce(ctype, ('int', str(v)), col, eng)
    if isinstance(v, float):
        return coerce(ctype, ('float', repr(v)), col, eng)
    if ct in ('uuid', 'timeuuid'):
        return coerce(ctype, ('uuid', v), col, eng)
    return coerce(ctype, ('str', v), col, eng)


def check_keys(t, vmap, mode):
    miss_pk = [c for c in t.pk if c not in vmap or vmap[c] is None]
    if miss_pk:
        raise inv(f'Some partition key parts are missing: {", ".join(miss_pk)}')
    miss_ck = [c for c in t.ck if c not in vmap or vmap[c] is None]
    if miss_ck:
        raise inv(f'Some clustering keys are missing: {", ".join(miss_ck)}')


def split_key_rels(t, rels):
    pk_rels = [r for r in rels if r[0] in t.pk]
    ck_rels = [r for r in rels if r[0] in t.ck]
    return pk_rels, ck_rels


def pk_values(t, pk_rels, eng, mode):
    vals = []
    for c in t.pk:
        rs = [r for r in pk_rels if r[0] == c]
        if not rs:
            missing = [x for x in t.pk if not any(r[0] == x for r in pk_rels)]
            raise inv(f'Some partition key parts are missing: {", ".join(missing)}')
        _, op, v = rs[0]
        if op == '=':
            vals.append([coerce(t.cols[c].type, v, c, eng)])
        elif op == 'IN':
            vals.append([coerce(t.cols[c].type, x, c, eng) for x in v])
        else:
            raise inv('Only EQ and IN relation are supported on the partition key (unless you use the token() function or allow filtering)')
    return eq_product(vals)


def eq_product(lists):
    out = [()]
    for l in lists:
        out = [o + (x,) for o in out for x in l]
    return out


def clustering_bounds(t, ck_rels, eng):
    """Returns (eq_lists, lo, lo_incl, hi, hi_incl) for a clustering prefix restriction."""
    eq = []
    lo = hi = None
    li = hi_i = True
    for idx, c in enumerate(t.ck):
        rs = [r for r in ck_rels if r[0] == c]
        if not rs:
            later = [r[0] for r in ck_rels if t.ck.index(r[0]) > idx]
            if later:
                raise inv(f'PRIMARY KEY column "{later[0]}" cannot be restricted as preceding column "{c}" is not restricted')
            break
        ops = [r[1] for r in rs]
        if all(o in ('=', 'IN') for o in ops):
            r = rs[0]
            eq.append([coerce(t.cols[c].type, r[2], c, eng)] if r[1] == '=' else [coerce(t.cols[c].type, x, c, eng) for x in r[2]])
            continue
        for _, op, v in rs:
            val = coerce(t.cols[c].type, v, c, eng)
            if op in ('>', '>='):
                lo, li = (val,), op == '>='
            elif op in ('<', '<='):
                hi, hi_i = (val,), op == '<='
        later = [r[0] for r in ck_rels if t.ck.index(r[0]) > idx]
        if later:
            raise inv(f'Clustering column "{later[0]}" cannot be restricted (preceding column "{c}" is restricted by a non-EQ relation)')
        break
    return eq, lo, li, hi, hi_i


def key_sets(t, rels, mode, only_static, eng):
    for r in rels:
        if isinstance(r[0], tuple):
            raise inv('The token function cannot be used in WHERE clauses for UPDATE statements')
        if r[0] not in t.cols:
            raise inv(f'Undefined column name {r[0]} in table {t.full}')
    non_pk = [r[0] for r in rels if r[0] not in t.pk and r[0] not in t.ck]
    if non_pk:
        raise inv(f'Non PRIMARY KEY columns found in where clause: {", ".join(non_pk)} ')
    pk_rels, ck_rels = split_key_rels(t, rels)
    pkeys = pk_values(t, pk_rels, eng, mode)
    if only_static and not ck_rels:
        return [(p, None) for p in pkeys]
    if t.ck:
        missing = [c for c in t.ck if not any(r[0] == c for r in ck_rels)]
        if missing:
            raise inv(f'Some clustering keys are missing: {", ".join(missing)}')
        for r in ck_rels:
            if r[1] not in ('=', 'IN'):
                raise inv(f'Invalid operator {r[1]} for PRIMARY KEY part {r[0]}')
        eq, *_ = clustering_bounds(t, ck_rels, eng)
        cks = eq_product(eq)
    else:
        cks = [()]
    return [(p, c) for p in pkeys for c in cks]


def check_conds(t, row, conds, eng):
    for c, op, v in conds:
        if c not in t.cols:
            raise inv(f'Undefined column name {c} in table {t.full}')
        cur = row.get(c) if row else None
        want = [coerce(t.cols[c].type, x, c, eng) for x in v] if op == 'IN' else coerce(t.cols[c].type, v, c, eng)
        if not compare(cur, op, want):
            return False, None
    return True, None


def compare(a, op, b):
    if op == 'IN':
        return a in b
    if op == '=':
        return a == b
    if op == '!=':
        return a != b
    if a is None or b is None:
        return False
    ka, kb = sort_key(None, a), sort_key(None, b)
    return {'<': ka < kb, '>': ka > kb, '<=': ka <= kb, '>=': ka >= kb}[op]


def lwt_result(t, applied, row=None, cols=None, allow_null_row=False):
    headers = ['[applied]']
    vals = ['True' if applied else 'False']
    if not applied and row is not None and cols:
        for c in cols:
            headers.append(c)
            vals.append(fmt(t.cols[c].type, row.get(c)))
    return ('rows', headers, [vals], [], True)


# ============================================================ SELECT
AGG = {'count', 'min', 'max', 'sum', 'avg'}


def run_select(eng, ks, n, sels, rels, group, order, ppl, limit, allow, distinct, js):
    t = eng.table(ks, n)
    warnings = []
    # ---------------- validate columns
    for r in rels:
        if isinstance(r[0], tuple):
            if list(r[0][1]) != t.pk:
                raise inv(f'The token() function must be applied to all partition key components or none of them')
            continue
        if r[0] not in t.cols:
            raise inv(f'Undefined column name {r[0]} in table {t.full}')
    tok_rels = [r for r in rels if isinstance(r[0], tuple)]
    rels_c = [r for r in rels if not isinstance(r[0], tuple)]
    pk_rels = [r for r in rels_c if r[0] in t.pk]
    ck_rels = [r for r in rels_c if r[0] in t.ck]
    other = [r for r in rels_c if r[0] not in t.pk and r[0] not in t.ck]

    pk_full_eq = bool(pk_rels) and all(any(r[0] == c and r[1] in ('=', 'IN') for r in pk_rels) for c in t.pk) \
        and all(r[1] in ('=', 'IN') for r in pk_rels)
    pk_partial = bool(pk_rels) and not pk_full_eq
    if pk_rels and any(r[1] not in ('=', 'IN') for r in pk_rels) and not allow:
        raise inv('Only EQ and IN relation are supported on the partition key (unless you use the token() function or allow filtering)')

    FILTER_MSG = ('Cannot execute this query as it might involve data filtering and thus may have unpredictable performance. '
                  'If you want to execute this query despite the performance unpredictability, use ALLOW FILTERING')

    # which restrictions are served by an index?
    idx_by_col = {}
    for name, (col, kind, target) in t.indexes.items():
        idx_by_col.setdefault(col, []).append((kind, target))

    def indexed(r):
        for kind, target in idx_by_col.get(r[0], []):
            op = r[1]
            if op == 'CONTAINS KEY':
                if target == 'keys':
                    return True
                continue
            if op == 'CONTAINS':
                if target == 'values' and isinstance(base_t(t.cols[r[0]].type), tuple):
                    return True
                continue
            if kind == 'sai' and op in ('=', '<', '>', '<=', '>='):
                return True
            if kind == '2i' and op == '=':
                return True
        return False
    idx_used = [r for r in other + ck_rels + pk_rels if indexed(r)]
    needs_filter = False
    if not allow:
        unindexed_other = [r for r in other if not indexed(r)]
        if unindexed_other:
            if not (idx_used and False):
                needs_filter = True
        if pk_partial and not idx_used:
            needs_filter = True
        if ck_rels and not pk_full_eq and not tok_rels and not idx_used:
            needs_filter = True
        if idx_used and (unindexed_other or (len([r for r in idx_used if r in other]) and False)):
            needs_filter = True
        if needs_filter:
            raise inv(FILTER_MSG)
        if pk_full_eq or not ck_rels:
            pass
        # clustering prefix rules (only when the clustering restrictions are not served by an index)
        if ck_rels and not any(r in idx_used for r in ck_rels):
            clustering_bounds(t, ck_rels, eng)
    for r in other:
        if r[1] in ('CONTAINS', 'CONTAINS KEY') and not isinstance(base_t(t.cols[r[0]].type), tuple):
            raise inv(f'Cannot use CONTAINS on non-collection column {r[0]}')
        if r[1] == '!=':
            pass
    # ORDER BY
    reverse = False
    if order:
        if not pk_full_eq:
            raise inv('ORDER BY is only supported when the partition key is restricted by an EQ or an IN.')
        for c, _ in order:
            if c not in t.ck:
                raise inv(f'Order by is currently only supported on the clustered columns of the PRIMARY KEY, got {c}')
        idxs = [t.ck.index(c) for c, _ in order]
        if idxs != list(range(len(idxs))):
            raise inv('Order by currently only supports the ordering of columns following their declared order in the PRIMARY KEY')
        flips = {(d != t.order[c]) for c, d in order}
        if len(flips) > 1:
            raise inv('Unsupported order by relation')
        reverse = flips.pop()
    # GROUP BY
    if group:
        keys = t.pk + t.ck
        for i, c in enumerate(group):
            if c not in keys:
                raise inv(f'Group by is currently only supported on the columns of the PRIMARY KEY, got {c}')
            if i >= len(keys) or keys[i] != c:
                raise inv('Group by currently only support groups of columns following their declared order in the PRIMARY KEY')

    # ---------------- selectors
    if sels == ['*']:
        sel = [(('col', c), None) for c in t.star_cols()]
    else:
        sel = sels
    for e, _ in sel:
        for c in cols_in(e):
            if c not in t.cols:
                raise inv(f'Undefined column name {c} in selection clause')
    is_agg = any(e[0] == 'agg' or (e[0] == 'fn' and e[1] in AGG) for e, _ in sel)
    if distinct:
        for e, _ in sel:
            if e[0] == 'col' and e[1] not in t.pk and t.cols[e[1]].kind != 'static':
                raise inv(f'SELECT DISTINCT queries must only request partition key columns and/or static columns (not {e[1]})')
    if is_agg and not pk_full_eq:
        warnings.append('Aggregation query used without partition key')
    if is_agg and pk_full_eq and any(r[1] == 'IN' and len(r[2]) > 1 for r in pk_rels):
        warnings.append('Aggregation query used on multiple partition keys (IN restriction)')
    for e, _ in sel:
        if e[0] == 'fn' and e[1] in ('ttl', 'writetime'):
            c = e[2][0][1]
            if t.cols[c].kind in ('partition', 'clustering'):
                raise inv(f'Cannot use selection function {e[1]} on PRIMARY KEY part {c}')

    # ---------------- scan
    if pk_full_eq:
        pkeys = pk_values(t, pk_rels, eng, 'select')
        parts = t.partitions(eng)
        items = [(k, parts[k]) for k in sorted(set(pkeys), key=lambda k: (eng.token_of(t, k),)) if k in parts]
    else:
        items = eng.ordered_parts(t)
    rows_out = []
    for item in items:
        tok = eng.token_of(t, item[0])
        ok = True
        for (_, op, v) in tok_rels:
            if isinstance(v, Func) and v.name == 'token':
                bound = eng.token_of(t, tuple(coerce(t.cols[c].type, a, c, eng) for c, a in zip(t.pk, v.args)))
            else:
                bound = int(v[1])
            if not compare(tok, op, bound):
                ok = False
        if not ok:
            continue
        n_in_part = 0
        for row in eng.iter_rows(t, item, reverse):
            if not row_matches(t, row, rels_c, eng):
                continue
            row['__tok'] = tok
            rows_out.append(row)
            n_in_part += 1
            if distinct:
                break
            if ppl is not None and n_in_part >= ppl:
                break

    # ---------------- project
    headers = [alias or header_of(e) for e, alias in sel]
    if is_agg:
        groups = []
        if group:
            cur_key, cur = object(), None
            for r in rows_out:
                k = tuple(r.get(c) for c in group)
                if k != cur_key:
                    cur = []; groups.append(cur); cur_key = k
                cur.append(r)
        else:
            groups = [rows_out]
        out = []
        for g in groups:
            out.append([fmt_value(t, e, g, eng, agg=True) for e, _ in sel])
        if limit is not None:
            out = out[:limit]
    else:
        out = [[fmt_value(t, e, [r], eng) for e, _ in sel] for r in rows_out]
        if limit is not None:
            out = out[:limit]
    if js:
        objs = []
        for vals_row, src_row in zip(out, rows_out):
            objs.append([json.dumps(to_json_obj(t, sel, headers, src_row, eng), ensure_ascii=False).replace('": ', '": ')])
        return ('rows', ['[json]'], objs[:limit] if limit else objs, warnings, False)
    return ('rows', headers, out, warnings, False)


def to_json_obj(t, sel, headers, row, eng):
    o = {}
    for (e, _), h in zip(sel, headers):
        v = eval_expr(t, e, [row], eng)
        ctype = expr_type(t, e)
        o[h] = jsonable(ctype, v)
    return o


def jsonable(ctype, v):
    ct = base_t(ctype)
    if v is None:
        return None
    if isinstance(ct, tuple):
        if ct[0] == 'list':
            return [jsonable(ct[1], x) for x in v]
        if ct[0] == 'set':
            return [jsonable(ct[1], x) for x in sorted(v, key=lambda x: sort_key(ct[1], x))]
        if ct[0] == 'map':
            return {str(jsonable(ct[1], k)): jsonable(ct[2], x) for k, x in sorted(v.items(), key=lambda kv: sort_key(ct[1], kv[0]))}
        if ct[0] == 'udt':
            return {f: jsonable(ft, v.get(f)) for f, ft in ct[2]}
    if ct == 'timestamp':
        return fmt_ts(v).replace('.000000+0000', '.000Z')
    if ct == 'date':
        return fmt(ct, v)
    if ct in ('uuid', 'timeuuid'):
        return str(v)
    if ct == 'decimal':
        return float(v)
    return v


def cols_in(e):
    if e[0] == 'col':
        return [e[1]]
    if e[0] == 'fn':
        return [c for a in e[2] for c in cols_in(a)]
    if e[0] == 'agg' and e[2] != '*':
        return cols_in(e[2])
    return []


def header_of(e):
    if e[0] == 'col':
        return e[1]
    if e[0] == 'agg':
        return 'count'
    if e[0] == 'lit':
        return str(e[1][1])
    name = e[1]
    inner = ', '.join(header_of(a) for a in e[2])
    if name in ('ttl', 'writetime'):
        return f'{name}({inner})'
    if name == 'count' and inner:
        return f'system.count({inner})'
    return f'system.{name}({inner})'


def expr_type(t, e):
    if e[0] == 'col':
        return t.cols[e[1]].type
    if e[0] == 'agg':
        return 'bigint'
    if e[0] == 'fn':
        n = e[1]
        if n == 'token':
            return 'bigint'
        if n in ('ttl',):
            return 'int'
        if n == 'writetime':
            return 'bigint'
        if n == 'count':
            return 'bigint'
        if n in ('min', 'max', 'sum', 'avg'):
            return expr_type(t, e[2][0])
        if n == 'totimestamp':
            return 'timestamp'
        if n == 'todate':
            return 'date'
        if n == 'tounixtimestamp':
            return 'bigint'
        if n in ('totimestamp', 'dateof'):
            return 'timestamp'
    return 'text'


def eval_expr(t, e, rows, eng, agg=False):
    if e[0] == 'col':
        return rows[0].get(e[1]) if rows else None
    if e[0] == 'lit':
        return plain(e[1])
    if e[0] == 'agg':
        return len(rows)
    n, args = e[1], e[2]
    if n in AGG:
        vals = [eval_expr(t, args[0], [r], eng) for r in rows]
        vals = [v for v in vals if v is not None]
        ct = base_t(expr_type(t, args[0]))
        if n == 'count':
            return len(vals)
        if n == 'min':
            return min(vals, key=lambda v: sort_key(ct, v)) if vals else None
        if n == 'max':
            return max(vals, key=lambda v: sort_key(ct, v)) if vals else None
        if n == 'sum':
            s = sum(vals) if vals else 0
            if ct == 'int':
                s = ((s + 2**31) % 2**32) - 2**31     # int overflow, as in Cassandra
            return s
        if n == 'avg':
            if not vals:
                return 0
            if ct in ('int', 'bigint', 'smallint', 'tinyint', 'varint', 'counter'):
                s = sum(vals)
                q = abs(s) // len(vals)
                return q if s >= 0 else -q          # integer division, truncating like Java
            if ct == 'decimal':
                return sum(vals) / len(vals)
            return sum(vals) / len(vals)
    r = rows[0] if rows else {}
    if n == 'token':
        return eng.token_of(t, tuple(r.get(a[1]) for a in args))
    if n in ('ttl', 'writetime'):
        c = args[0][1]
        cell = r.get('__cells', {}).get(c)
        if cell is None or cell.v is None:
            return None
        if n == 'writetime':
            return cell.ts
        if cell.exp is None:
            return None
        return cell.exp - eng.now_s
    if n == 'totimestamp':
        v = eval_expr(t, args[0], rows, eng)
        return v.ms if isinstance(v, TimeUUID) else v
    if n == 'todate':
        v = eval_expr(t, args[0], rows, eng)
        v = v.ms if isinstance(v, TimeUUID) else v
        return v // 86400000 if v is not None else None
    if n == 'tounixtimestamp':
        v = eval_expr(t, args[0], rows, eng)
        return v.ms if isinstance(v, TimeUUID) else v
    raise inv(f'Unknown function {n}')


def fmt_value(t, e, rows, eng, agg=False):
    v = eval_expr(t, e, rows, eng, agg)
    return fmt(expr_type(t, e), v)


def row_matches(t, row, rels, eng):
    for c, op, v in rels:
        if op == 'IS NOT NULL':
            if row.get(c) is None:
                return False
            continue
        ctype = t.cols[c].type
        cur = row.get(c)
        if op == 'CONTAINS':
            bt = base_t(ctype)
            want = coerce(bt[2] if bt[0] == 'map' else bt[1], v, c, eng)
            vals = cur.values() if isinstance(cur, dict) else (cur or [])
            if want not in vals:
                return False
            continue
        if op == 'CONTAINS KEY':
            want = coerce(base_t(ctype)[1], v, c, eng)
            if not cur or want not in cur:
                return False
            continue
        if op == 'IN':
            want = [coerce(ctype, x, c, eng) for x in v]
        else:
            want = coerce(ctype, v, c, eng)
        if not compare(cur, op, want):
            return False
    return True


# ============================================================ cqlsh-style rendering
def render(results, echo=True):
    out = []
    for stmt, res, ks in results:
        if res is None:
            continue
        if echo:
            prompt = f'cqlsh:{ks}> ' if ks else 'cqlsh> '
            lines = [l.rstrip() for l in stmt.strip().split('\n') if l.strip() and not l.strip().startswith('--')]
            out.append(prompt + lines[0].strip())
            for l in lines[1:]:
                out.append(' ' * (len(prompt) - 4) + '... ' + l.strip())
            out.append('')
        if res[0] == 'error':
            out.append(res[1])
            out.append('')
            continue
        if res[0] == 'text':
            out.append(res[1])
            out.append('')
            continue
        if res[0] == 'warn':
            out.append('Warnings :')
            out.append(res[1])
            out.append('')
            continue
        _, headers, rows, warnings, lwt = res
        widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(headers)]
        out.append(' ' + ' | '.join(h.rjust(w) for h, w in zip(headers, widths)))
        out.append('+'.join('-' * (w + 2) for w in widths))
        for r in rows:
            out.append(' ' + ' | '.join(v.rjust(w) for v, w in zip(r, widths)))
        out.append('')
        if not lwt:
            out.append(f'({len(rows)} rows)')
            out.append('')
        if warnings:
            out.append('Warnings :')
            out.extend(warnings)
            out.append('')
    while out and out[-1] == '':
        out.pop()
    return '\n'.join(out)
