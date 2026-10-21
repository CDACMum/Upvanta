"""hbasesim - a small, deterministic HBase shell that follows Apache HBase 2.x semantics.

Used at build time to produce the Output boxes of the HBase module. It implements:
  * tables in namespaces, column families with VERSIONS / TTL / MIN_VERSIONS / KEEP_DELETED_CELLS
  * row keys sorted as raw bytes (lexicographic), families and qualifiers sorted
  * multi-version cells with timestamps, delete markers (Delete, DeleteColumn, DeleteFamily) and RAW scans
  * put / get / scan / count / delete / deleteall / incr / get_counter / append / truncate
  * scan options: STARTROW, STOPROW, ROWPREFIXFILTER, COLUMNS, LIMIT, REVERSED, VERSIONS, TIMERANGE, RAW, FILTER
  * the HBase Filter Language: PrefixFilter, RowFilter, ColumnPrefixFilter, QualifierFilter, FamilyFilter,
    ValueFilter, SingleColumnValueFilter (incl. filterIfMissing), PageFilter, KeyOnlyFilter, FirstKeyOnlyFilter,
    InclusiveStopFilter, ColumnCountGetFilter, TimestampsFilter with AND / OR and binary / binaryprefix /
    substring / regexstring comparators
  * DDL: create (with SPLITS), alter, describe, list, exists, disable, enable, drop, namespaces
  * hbase shell-style output (ROW / COLUMN+CELL, "N row(s)", "=>" return values, ERROR lines)
It is a single-process simulation: RegionServers, HDFS, WAL and ZooKeeper are not simulated.
"""
import datetime as _dt
import re
import struct

IST = _dt.timezone(_dt.timedelta(hours=5, minutes=30))
LATEST = 2 ** 63 - 1


class ShellError(Exception):
    pass


# ============================================================ byte helpers
def to_bytes(v):
    if isinstance(v, bytes):
        return v
    if isinstance(v, int):
        return str(v).encode()
    return v.encode('latin-1') if isinstance(v, str) else bytes(v)


def show_bytes(b):
    """Bytes.toStringBinary: printable ASCII as-is, everything else as \\xNN."""
    out = []
    for c in b:
        if 32 <= c < 127 and c != 92:
            out.append(chr(c))
        else:
            out.append('\\x%02X' % c)
    return ''.join(out)


def fmt_ts(ms):
    dt = _dt.datetime.fromtimestamp(ms / 1000, IST)
    return dt.strftime('%Y-%m-%dT%H:%M:%S.') + f'{ms % 1000:03d}'


# ============================================================ tokenizer (a little Ruby)
TOK = re.compile(r"""
    (?P<ws>\s+|\#[^\n]*)
  | (?P<arrow>=>)
  | (?P<sq>'(?:[^'\\]|\\.)*')
  | (?P<dq>"(?:[^"\\]|\\.)*")
  | (?P<num>-?\d+)
  | (?P<id>[A-Za-z_][A-Za-z0-9_:.]*[?!]?)
  | (?P<op>[{}\[\],()])
""", re.X)


def _unescape_dq(s):
    out, i = bytearray(), 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            if n == 'x':
                out.append(int(s[i + 2:i + 4], 16)); i += 4; continue
            out += {'n': b'\n', 't': b'\t', '\\': b'\\', '"': b'"', "'": b"'"}.get(n, n.encode()); i += 2; continue
        out += c.encode('latin-1'); i += 1
    return bytes(out)


def tokenize(src):
    toks, pos = [], 0
    while pos < len(src):
        m = TOK.match(src, pos)
        if not m:
            raise ShellError(f"SyntaxError: unexpected character '{src[pos]}'")
        pos = m.end()
        k = m.lastgroup
        t = m.group(k)
        if k == 'ws':
            continue
        if k == 'sq':
            toks.append(('str', t[1:-1].replace("\\'", "'").replace('\\\\', '\\').encode('latin-1')))
        elif k == 'dq':
            toks.append(('str', _unescape_dq(t[1:-1])))
        elif k == 'num':
            toks.append(('num', int(t)))
        else:
            toks.append((k, t))
    return toks


class P:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self, n=0):
        return self.t[self.i + n] if self.i + n < len(self.t) else ('eof', None)

    def take(self, kind=None, val=None):
        k, v = self.peek()
        if (kind is None or k == kind) and (val is None or v == val):
            self.i += 1
            return v
        return None

    def value(self):
        k, v = self.peek()
        if k in ('str', 'num'):
            self.i += 1
            return v
        if k == 'op' and v == '[':
            self.i += 1
            items = []
            while not self.take('op', ']'):
                items.append(self.value())
                self.take('op', ',')
            return items
        if k == 'op' and v == '{':
            self.i += 1
            d = {}
            while not self.take('op', '}'):
                key = self.value()
                self.take('arrow')
                d[key if not isinstance(key, bytes) else key.decode('latin-1')] = self.value()
                self.take('op', ',')
            return d
        if k == 'id':
            self.i += 1
            if v in ('true', 'false'):
                return v == 'true'
            if v == 'nil':
                return None
            return ('const', v)
        raise ShellError(f'SyntaxError: unexpected {v!r}')

    def args(self):
        """positional args, then an optional bare hash (CONST => value, ...)."""
        pos, kw = [], None
        while self.peek()[0] != 'eof':
            if self.peek(1)[0] == 'arrow':
                kw = kw if kw is not None else {}
                key = self.value(); self.take('arrow')
                kw[key[1] if isinstance(key, tuple) else (key.decode('latin-1') if isinstance(key, bytes) else key)] = self.value()
            else:
                pos.append(self.value())
            self.take('op', ',')
        if kw is not None:
            pos.append(kw)
        return pos


def keyname(k):
    if isinstance(k, tuple):
        return k[1]
    if isinstance(k, bytes):
        return k.decode('latin-1')
    return k


def norm(d):
    return {keyname(k): v for k, v in d.items()} if isinstance(d, dict) else d


def s(v):
    return v.decode('latin-1') if isinstance(v, bytes) else (str(v) if v is not None else None)


# ============================================================ schema / storage
FAMILY_DEFAULTS = dict(VERSIONS=1, TTL=None, MIN_VERSIONS=0, KEEP_DELETED_CELLS=False, BLOOMFILTER='ROW',
                       IN_MEMORY=False, COMPRESSION='NONE', BLOCKCACHE=True, BLOCKSIZE=65536,
                       DATA_BLOCK_ENCODING='NONE', REPLICATION_SCOPE=0)


class Family:
    def __init__(self, name, **opts):
        self.name = name
        self.o = dict(FAMILY_DEFAULTS)
        self.set(**opts)

    def set(self, **opts):
        for k, v in opts.items():
            k = k.upper()
            if k == 'NAME':
                continue
            if k in ('VERSIONS', 'MIN_VERSIONS', 'BLOCKSIZE', 'REPLICATION_SCOPE'):
                v = int(s(v)) if not isinstance(v, int) else v
            if k == 'TTL':
                v = int(s(v)) if not isinstance(v, int) else v
            if k in ('IN_MEMORY', 'BLOCKCACHE', 'KEEP_DELETED_CELLS') and not isinstance(v, bool):
                v = s(v).lower() == 'true'
            if isinstance(v, bytes):
                v = v.decode('latin-1')
            if isinstance(v, tuple):
                v = v[1]
            self.o[k] = v

    def describe(self):
        o = self.o
        ttl = 'FOREVER' if not o['TTL'] else f"{o['TTL']} SECONDS ({_human(o['TTL'])})"
        bs = o['BLOCKSIZE']
        return ("{NAME => '%s', INDEX_BLOCK_ENCODING => 'NONE', VERSIONS => '%d', KEEP_DELETED_CELLS => '%s', "
                "DATA_BLOCK_ENCODING => '%s', TTL => '%s', MIN_VERSIONS => '%d', REPLICATION_SCOPE => '%d', "
                "BLOOMFILTER => '%s', IN_MEMORY => '%s', COMPRESSION => '%s', BLOCKCACHE => '%s', "
                "BLOCKSIZE => '%d B (%dKB)'}" % (
                    self.name, o['VERSIONS'], str(o['KEEP_DELETED_CELLS']).upper(), o['DATA_BLOCK_ENCODING'], ttl,
                    o['MIN_VERSIONS'], o['REPLICATION_SCOPE'], o['BLOOMFILTER'], str(o['IN_MEMORY']).lower(),
                    o['COMPRESSION'], str(o['BLOCKCACHE']).lower(), bs, bs // 1024))


def _human(sec):
    parts = []
    for unit, n in (('DAY', 86400), ('HOUR', 3600), ('MINUTE', 60), ('SECOND', 1)):
        if sec >= n:
            q, sec = divmod(sec, n)
            parts.append(f'{q} {unit}{"S" if q > 1 else ""}')
    return ' '.join(parts)


class Table:
    def __init__(self, ns, name, families, splits):
        self.ns, self.name = ns, name
        self.families = {f.name: f for f in families}
        self.splits = sorted(splits)
        self.enabled = True
        self.cells = []          # list of [row, fam, qual, ts, type, value]; type: Put/Delete/DeleteColumn/DeleteFamily

    @property
    def full(self):
        return self.name if self.ns == 'default' else f'{self.ns}:{self.name}'


# ============================================================ filters
class Cmp:
    def __init__(self, op, comp):
        self.op = op
        kind, _, val = comp.partition(':')
        self.kind, self.val = kind, val.encode('latin-1')
        if kind not in ('binary', 'binaryprefix', 'substring', 'regexstring'):
            raise ShellError(f'Incorrect comparator type: {kind}')

    def test(self, b):
        if self.kind == 'binary':
            c = (b > self.val) - (b < self.val)
        elif self.kind == 'binaryprefix':
            pre = b[:len(self.val)]
            c = (pre > self.val) - (pre < self.val)
        elif self.kind == 'substring':
            c = 0 if self.val.lower() in b.lower() else 1
        else:
            c = 0 if re.search(self.val.decode('latin-1'), b.decode('latin-1')) else 1
        return {'=': c == 0, '!=': c != 0, '<': c < 0, '<=': c <= 0, '>': c > 0, '>=': c >= 0}[self.op]


def parse_filter(text):
    toks = re.findall(r"'(?:[^']|'')*'|<=|>=|!=|[=<>(),]|[A-Za-z_][A-Za-z0-9_]*|-?\d+", text)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def nxt():
        t = toks[pos[0]]; pos[0] += 1; return t

    def term():
        t = nxt()
        if t == '(':
            e = expr(); nxt(); return e
        name = t
        nxt()  # (
        args = []
        while peek() != ')':
            a = nxt()
            if a == ',':
                continue
            args.append(a[1:-1].replace("''", "'") if a.startswith("'") else a)
        nxt()
        return ('f', name, args)

    def expr():
        left = term()
        while peek() in ('AND', 'OR'):
            op = nxt()
            left = (op, left, term())
        return left
    return expr()


def _bool(a):
    return str(a).lower() == 'true'


class RowCtx:
    """Evaluates filters on one row: cells -> (keep_row, cells)."""

    def __init__(self, tree):
        self.tree = tree

    def apply(self, row, cells, state):
        return self._ev(self.tree, row, cells, state)

    def _ev(self, t, row, cells, state):
        if t[0] in ('AND', 'OR'):
            ok1, c1 = self._ev(t[1], row, cells, state)
            if t[0] == 'AND':
                if not ok1:
                    return False, []
                return self._ev(t[2], row, c1, state)
            ok2, c2 = self._ev(t[2], row, cells, state)
            if not ok1 and not ok2:
                return False, []
            keep = set(map(id, c1 if ok1 else [])) | set(map(id, c2 if ok2 else []))
            return True, [c for c in cells if id(c) in keep]
        _, name, a = t
        if name == 'PrefixFilter':
            return row.startswith(a[0].encode('latin-1')), cells
        if name == 'RowFilter':
            return Cmp(a[0], a[1]).test(row), cells
        if name == 'InclusiveStopFilter':
            return row <= a[0].encode('latin-1'), cells
        if name == 'FamilyFilter':
            cm = Cmp(a[0], a[1]); keep = [c for c in cells if cm.test(c[1])]; return bool(keep), keep
        if name == 'QualifierFilter':
            cm = Cmp(a[0], a[1]); keep = [c for c in cells if cm.test(c[2])]; return bool(keep), keep
        if name == 'ColumnPrefixFilter':
            p = a[0].encode('latin-1'); keep = [c for c in cells if c[2].startswith(p)]; return bool(keep), keep
        if name == 'MultipleColumnPrefixFilter':
            ps = [x.encode('latin-1') for x in a]; keep = [c for c in cells if any(c[2].startswith(p) for p in ps)]
            return bool(keep), keep
        if name == 'ValueFilter':
            cm = Cmp(a[0], a[1]); keep = [c for c in cells if cm.test(c[5])]; return bool(keep), keep
        if name in ('SingleColumnValueFilter', 'SingleColumnValueExcludeFilter'):
            fam, qual = a[0].encode('latin-1'), a[1].encode('latin-1')
            cm = Cmp(a[2], a[3])
            if_missing = _bool(a[4]) if len(a) > 4 else False
            latest_only = _bool(a[5]) if len(a) > 5 else True
            col = [c for c in cells if c[1] == fam and c[2] == qual]
            if latest_only:
                col = col[:1]
            if not col:
                return (not if_missing), cells
            if not any(cm.test(c[5]) for c in col):
                return False, []
            if name == 'SingleColumnValueExcludeFilter':
                cells = [c for c in cells if not (c[1] == fam and c[2] == qual)]
            return True, cells
        if name == 'KeyOnlyFilter':
            return True, [c[:5] + [b''] for c in cells]
        if name == 'FirstKeyOnlyFilter':
            return bool(cells), cells[:1]
        if name == 'ColumnCountGetFilter':
            n = int(a[0]); seen, keep = [], []
            for c in cells:
                if (c[1], c[2]) not in seen:
                    if len(seen) >= n:
                        break
                    seen.append((c[1], c[2]))
                keep.append(c)
            return bool(keep), keep
        if name == 'TimestampsFilter':
            tss = {int(x) for x in a}; keep = [c for c in cells if c[3] in tss]; return bool(keep), keep
        if name == 'PageFilter':
            n = int(a[0])
            state['page'] = state.get('page', 0) + 1
            return state['page'] <= n, cells
        if name == 'ColumnPaginationFilter':
            lim, off = int(a[0]), int(a[1])
            cols = []
            for c in cells:
                if (c[1], c[2]) not in cols:
                    cols.append((c[1], c[2]))
            pick = set(cols[off:off + lim])
            keep = [c for c in cells if (c[1], c[2]) in pick]
            return bool(keep), keep
        raise ShellError(f'Filter Name {name} not supported')


# ============================================================ the shell
class Shell:
    START_MS = int(_dt.datetime(2026, 10, 14, 10, 0, 0, tzinfo=IST).timestamp() * 1000)

    def __init__(self):
        self.namespaces = {'default': {}, 'hbase': {}}
        self.now = self.START_MS
        self.n = 0

    def tick(self):
        self.now += 1
        return self.now

    # ---------------------------------------------------------- run a script
    def run(self, src):
        """Returns list of (command_text, output_text_or_None)."""
        results = []
        buf = ''
        for line in src.split('\n'):
            if line.strip().startswith('!'):
                m = re.match(r'!sleep\s+(\d+)', line.strip())
                if m:
                    self.now += int(m.group(1)) * 1000
                continue
            if not line.strip() or line.strip().startswith('#'):
                if not buf:
                    continue
            buf += line + '\n'
            if buf.count('{') > buf.count('}') or buf.count('[') > buf.count(']') or buf.rstrip().endswith(','):
                continue
            cmd = buf.strip()
            buf = ''
            if not cmd:
                continue
            self.n += 1
            try:
                out = self.execute(cmd)
            except ShellError as e:
                out = f'ERROR: {e}'
            results.append((cmd, out))
        return results

    def execute(self, cmd):
        toks = tokenize(cmd)
        if not toks:
            return None
        name = toks[0][1]
        p = P(toks[1:])
        args = p.args()
        fn = getattr(self, 'cmd_' + name, None)
        if fn is None:
            raise ShellError(f"NameError: undefined local variable or method `{name}' for main:Object")
        return fn(*args)

    # ---------------------------------------------------------- helpers
    def resolve(self, tname, need_enabled=True):
        name = s(tname)
        ns, _, t = name.rpartition(':')
        ns = ns or 'default'
        tab = self.namespaces.get(ns, {}).get(t)
        if tab is None:
            raise ShellError(f'Unknown table {name}!')
        if need_enabled and not tab.enabled:
            raise ShellError(f'org.apache.hadoop.hbase.TableNotEnabledException: {name} is disabled.')
        return tab

    def colspec(self, tab, col):
        fam, _, qual = s(col).partition(':')
        if fam not in tab.families:
            raise ShellError(f'org.apache.hadoop.hbase.regionserver.NoSuchColumnFamilyException: '
                             f'Column family {fam} does not exist in table {tab.full}')
        return fam.encode(), qual.encode('latin-1')

    def live_cells(self, tab, raw=False, max_versions=None, timerange=None, columns=None):
        """Visible cells grouped by row (sorted), applying deletes, versions and TTL."""
        rows = {}
        for c in tab.cells:
            rows.setdefault(c[0], []).append(c)
        out = []
        for row in sorted(rows):
            cells = rows[row]
            # order: family, qualifier asc, timestamp desc; deletes before puts at same ts
            cells = sorted(cells, key=lambda c: (c[1], c[2], -c[3], 0 if c[4] != 'Put' else 1))
            vis = []
            if raw:
                per = {}
                for c in cells:
                    if columns and not _col_match(c, columns):
                        continue
                    if timerange and not (timerange[0] <= c[3] < timerange[1]):
                        continue
                    k = (c[1], c[2])
                    per[k] = per.get(k, 0) + 1
                    if c[4] == 'Put' and per[k] > (max_versions or 1) + sum(1 for x in cells if (x[1], x[2]) == k and x[4] != 'Put'):
                        continue
                    vis.append(c)
                out.append((row, vis))
                continue
            fam_del = {}
            for c in cells:
                if c[4] == 'DeleteFamily':
                    fam_del[c[1]] = max(fam_del.get(c[1], -1), c[3])
            col_del, ver_del = {}, set()
            if timerange:
                # KEEP_DELETED_CELLS: a time-range read before the delete still sees the data
                kd = {f.encode() for f, fo in tab.families.items() if fo.o['KEEP_DELETED_CELLS']}
                fam_del = {f: t for f, t in fam_del.items() if not (f in kd and t >= timerange[1])}
                cells_for_del = [c for c in cells if not (c[1] in kd and c[3] >= timerange[1])]
            else:
                cells_for_del = cells
            for c in cells_for_del:
                if c[4] == 'DeleteColumn':
                    k = (c[1], c[2]); col_del[k] = max(col_del.get(k, -1), c[3])
                elif c[4] == 'Delete':
                    ver_del.add((c[1], c[2], c[3]))
            count = {}
            for c in cells:
                if c[4] != 'Put':
                    continue
                fam = tab.families.get(c[1].decode())
                if fam is None:
                    continue
                k = (c[1], c[2])
                if c[3] <= fam_del.get(c[1], -1) or c[3] <= col_del.get(k, -1) or (c[1], c[2], c[3]) in ver_del:
                    continue
                ttl = fam.o['TTL']
                if ttl and c[3] + ttl * 1000 <= self.now and count.get(k, 0) >= fam.o['MIN_VERSIONS']:
                    continue
                count[k] = count.get(k, 0) + 1
                if count[k] > fam.o['VERSIONS']:
                    continue
                if count[k] > (max_versions or 1):
                    continue
                if timerange and not (timerange[0] <= c[3] < timerange[1]):
                    count[k] -= 1
                    continue
                if columns and not _col_match(c, columns):
                    continue
                vis.append(c)
            if vis:
                out.append((row, vis))
        return out

    # ---------------------------------------------------------- namespace / DDL
    def cmd_create_namespace(self, ns, *_):
        ns = s(ns)
        if ns in self.namespaces:
            raise ShellError(f'org.apache.hadoop.hbase.NamespaceExistException: {ns}')
        self.namespaces[ns] = {}
        return None

    def cmd_list_namespace(self, *_):
        names = sorted(self.namespaces)
        return 'NAMESPACE\n' + '\n'.join(names) + f'\n{len(names)} row(s)'

    def cmd_list_namespace_tables(self, ns):
        tabs = sorted(self.namespaces[s(ns)])
        return 'TABLE\n' + '\n'.join(tabs) + f'\n{len(tabs)} row(s)\n=> {_rb_list(tabs)}'

    def cmd_drop_namespace(self, ns):
        ns = s(ns)
        if self.namespaces.get(ns):
            raise ShellError(f'org.apache.hadoop.hbase.constraint.ConstraintException: Only empty namespaces can be removed. '
                             f'Namespace {ns} has {len(self.namespaces[ns])} tables')
        self.namespaces.pop(ns, None)

    def cmd_create(self, tname, *specs):
        name = s(tname)
        ns, _, t = name.rpartition(':')
        ns = ns or 'default'
        if ns not in self.namespaces:
            raise ShellError(f'org.apache.hadoop.hbase.NamespaceNotFoundException: {ns}')
        if t in self.namespaces[ns]:
            raise ShellError(f'Table already exists: {name}!')
        fams, splits = [], []
        for sp in specs:
            if isinstance(sp, bytes):
                fams.append(Family(sp.decode()))
            elif isinstance(sp, dict):
                sp = norm(sp)
                if 'SPLITS' in sp:
                    splits = [to_bytes(x) for x in sp['SPLITS']]
                if 'NAME' in sp:
                    fams.append(Family(s(sp['NAME']), **{k: v for k, v in sp.items() if k not in ('NAME', 'SPLITS')}))
        if not fams:
            raise ShellError('Table must have at least one column family')
        self.namespaces[ns][t] = Table(ns, t, fams, splits)
        return f'Created table {name}\n=> Hbase::Table - {name}'

    def cmd_list(self, *a):
        names = []
        for ns in sorted(self.namespaces):
            if ns == 'hbase':
                continue
            for t in sorted(self.namespaces[ns]):
                names.append(t if ns == 'default' else f'{ns}:{t}')
        if a:
            rx = re.compile(s(a[0]))
            names = [n for n in names if rx.fullmatch(n)]
        return 'TABLE\n' + ''.join(n + '\n' for n in names) + f'{len(names)} row(s)\n=> {_rb_list(names)}'

    def cmd_exists(self, tname):
        try:
            self.resolve(tname, False)
            return f'Table {s(tname)} does exist\n=> true'
        except ShellError:
            return f'Table {s(tname)} does not exist\n=> false'

    def cmd_is_enabled(self, tname):
        return f'{str(self.resolve(tname, False).enabled).lower()}\n=> {str(self.resolve(tname, False).enabled).lower()}'

    def cmd_disable(self, tname):
        t = self.resolve(tname, False)
        if not t.enabled:
            raise ShellError(f'org.apache.hadoop.hbase.TableNotEnabledException: {s(tname)}')
        t.enabled = False

    def cmd_enable(self, tname):
        t = self.resolve(tname, False)
        if t.enabled:
            raise ShellError(f'org.apache.hadoop.hbase.TableNotDisabledException: {s(tname)}')
        t.enabled = True

    def cmd_drop(self, tname):
        t = self.resolve(tname, False)
        if t.enabled:
            raise ShellError(f'Table {s(tname)} is enabled. Disable it first.')
        del self.namespaces[t.ns][t.name]

    def cmd_truncate(self, tname):
        t = self.resolve(tname, False)
        t.cells = []
        return f"Truncating '{s(tname)}' table (it may take a while):\nDisabling table...\nTruncating table..."

    def cmd_alter(self, tname, *specs):
        t = self.resolve(tname, False)
        msgs = []
        for sp in specs:
            sp = norm(sp) if isinstance(sp, dict) else sp
            if isinstance(sp, dict) and 'METHOD' in sp and s(sp['METHOD']) == 'delete':
                fam = s(sp['NAME'])
                t.families.pop(fam, None)
                t.cells = [c for c in t.cells if c[1] != fam.encode()]
                msgs.append('Updating all regions with the new schema...\n1/1 regions updated.\nDone.')
                continue
            if isinstance(sp, dict) and 'NAME' in sp:
                fam = s(sp['NAME'])
                opts = {k: v for k, v in sp.items() if k != 'NAME'}
                if fam in t.families:
                    t.families[fam].set(**opts)
                else:
                    t.families[fam] = Family(fam, **opts)
            elif isinstance(sp, bytes):
                t.families.setdefault(sp.decode(), Family(sp.decode()))
            msgs.append('Updating all regions with the new schema...\n1/1 regions updated.\nDone.')
        return '\n'.join(msgs) if msgs else None

    def cmd_describe(self, tname):
        t = self.resolve(tname, False)
        lines = [f'Table {t.full} is {"ENABLED" if t.enabled else "DISABLED"}',
                 f'{t.full}', 'COLUMN FAMILIES DESCRIPTION']
        for f in sorted(t.families):
            lines.append(t.families[f].describe())
            lines.append('')
        lines.append(f'{len(t.families)} row(s)')
        lines.append('Quota is disabled')
        return '\n'.join(lines)

    cmd_desc = cmd_describe

    # ---------------------------------------------------------- DML
    def cmd_put(self, tname, row, col, value, ts=None, *_):
        t = self.resolve(tname)
        fam, qual = self.colspec(t, col)
        stamp = ts if isinstance(ts, int) else self.tick()
        t.cells.append([to_bytes(row), fam, qual, stamp, 'Put', to_bytes(value)])
        return None

    def cmd_append(self, tname, row, col, value, *_):
        t = self.resolve(tname)
        fam, qual = self.colspec(t, col)
        cur = self._latest(t, to_bytes(row), fam, qual)
        new = (cur or b'') + to_bytes(value)
        t.cells.append([to_bytes(row), fam, qual, self.tick(), 'Put', new])
        return f'CURRENT VALUE = {show_bytes(new)}'

    def _latest(self, t, row, fam, qual):
        for r, cells in self.live_cells(t):
            if r == row:
                for c in cells:
                    if c[1] == fam and c[2] == qual:
                        return c[5]
        return None

    def cmd_incr(self, tname, row, col, by=1, *_):
        t = self.resolve(tname)
        fam, qual = self.colspec(t, col)
        cur = self._latest(t, to_bytes(row), fam, qual)
        if cur is not None and len(cur) != 8:
            raise ShellError('org.apache.hadoop.hbase.DoNotRetryIOException: Field is not a long, it\'s '
                             f'{len(cur)} bytes wide')
        val = (struct.unpack('>q', cur)[0] if cur else 0) + (by if isinstance(by, int) else 1)
        t.cells.append([to_bytes(row), fam, qual, self.tick(), 'Put', struct.pack('>q', val)])
        return f'COUNTER VALUE = {val}'

    def cmd_get_counter(self, tname, row, col):
        t = self.resolve(tname)
        fam, qual = self.colspec(t, col)
        cur = self._latest(t, to_bytes(row), fam, qual)
        if cur is None:
            return 'No counter found at specified coordinates'
        return f'COUNTER VALUE = {struct.unpack(">q", cur)[0]}'

    def cmd_delete(self, tname, row, col, ts=None, *_):
        t = self.resolve(tname)
        fam, qual = self.colspec(t, col)
        stamp = ts if isinstance(ts, int) else self.tick()
        t.cells.append([to_bytes(row), fam, qual, stamp, 'DeleteColumn', b''])

    def cmd_deleteall(self, tname, row, col=None, ts=None, *_):
        t = self.resolve(tname)
        stamp = ts if isinstance(ts, int) else self.tick()
        if col is not None and not isinstance(col, dict):
            fam, qual = self.colspec(t, col)
            if qual:
                t.cells.append([to_bytes(row), fam, qual, stamp, 'DeleteColumn', b''])
            else:
                t.cells.append([to_bytes(row), fam, b'', stamp, 'DeleteFamily', b''])
            return None
        for fam in t.families:
            t.cells.append([to_bytes(row), fam.encode(), b'', stamp, 'DeleteFamily', b''])

    def cmd_get(self, tname, row, *opts):
        t = self.resolve(tname)
        o = {}
        columns = None
        for x in opts:
            if isinstance(x, dict):
                o.update(norm(x))
            elif isinstance(x, (bytes, list)):
                columns = x
        columns = columns or o.get('COLUMN') or o.get('COLUMNS')
        cols = self._cols(t, columns)
        tr = o.get('TIMERANGE')
        if 'TIMESTAMP' in o:
            tr = [o['TIMESTAMP'], o['TIMESTAMP'] + 1]
        cells = []
        for r, cs in self.live_cells(t, raw=bool(o.get('RAW')), max_versions=o.get('VERSIONS'), timerange=tr, columns=cols):
            if r == to_bytes(row):
                cells = cs
        if 'FILTER' in o and cells:
            ok, cells = RowCtx(parse_filter(s(o['FILTER']))).apply(to_bytes(row), cells, {})
            if not ok:
                cells = []
        lines = [f'{"COLUMN":<34} CELL']
        for c in cells:
            lines.append(f' {show_bytes(c[1] + b":" + c[2]):<33} {_cell_text(c)}')
        lines.append(f'{len(cells)} row(s)')   # the shell's footer counts printed lines (cells)
        return '\n'.join(lines)

    def _cols(self, t, columns):
        if columns is None:
            return None
        if isinstance(columns, bytes):
            columns = [columns]
        out = []
        for c in columns:
            fam, _, qual = s(c).partition(':')
            self.colspec(t, fam)
            out.append((fam.encode(), qual.encode('latin-1') if ':' in s(c) else None))
        return out

    def cmd_scan(self, tname, opts=None):
        t = self.resolve(tname)
        o = norm(opts) if isinstance(opts, dict) else {}
        cols = self._cols(t, o.get('COLUMNS') or o.get('COLUMN'))
        rows = self.live_cells(t, raw=bool(o.get('RAW')), max_versions=o.get('VERSIONS'),
                               timerange=o.get('TIMERANGE'), columns=cols)
        start = to_bytes(o['STARTROW']) if 'STARTROW' in o else None
        stop = to_bytes(o['STOPROW']) if 'STOPROW' in o else None
        prefix = to_bytes(o['ROWPREFIXFILTER']) if 'ROWPREFIXFILTER' in o else None
        reverse = bool(o.get('REVERSED'))
        if reverse:
            rows = rows[::-1]
        flt = RowCtx(parse_filter(s(o['FILTER']))) if 'FILTER' in o else None
        state = {}
        lines = [f'{"ROW":<34} COLUMN+CELL']
        count = 0
        for row, cells in rows:
            if prefix is not None and not row.startswith(prefix):
                continue
            if not reverse:
                if start is not None and row < start:
                    continue
                if stop is not None and row >= stop:
                    continue
            else:
                if start is not None and row > start:
                    continue
                if stop is not None and row <= stop:
                    continue
            if flt:
                ok, cells = flt.apply(row, cells, state)
                if not ok or not cells:
                    continue
            if 'LIMIT' in o and count >= o['LIMIT']:
                break
            count += 1
            for c in cells:
                lines.append(f' {show_bytes(row):<33} column={show_bytes(c[1] + b":" + c[2])}, {_cell_text(c)}')
        lines.append(f'{count} row(s)')
        return '\n'.join(lines)

    def cmd_count(self, tname, *opts):
        t = self.resolve(tname)
        n = len(self.live_cells(t))
        return f'{n} row(s)\n=> {n}'

    def cmd_status(self, *a):
        return None

    def cmd_whoami(self, *a):
        return 'vineeta (auth:SIMPLE)\n    groups: vineeta'


def _col_match(c, columns):
    for fam, qual in columns:
        if c[1] == fam and (qual is None or c[2] == qual):
            return True
    return False


def _cell_text(c):
    if c[4] != 'Put':
        return f'timestamp={fmt_ts(c[3])}, type={c[4]}'
    return f'timestamp={fmt_ts(c[3])}, value={show_bytes(c[5])}'


def _rb_list(names):
    return '[' + ', '.join(f'"{n}"' for n in names) + ']'


# ============================================================ rendering
def render(results, start=1):
    out = []
    for i, (cmd, res) in enumerate(results):
        first, *rest = cmd.split('\n')
        n = start + i
        out.append(f'hbase:{n:03d}:0> {first.strip()}')
        for r in rest:
            if r.strip():
                out.append(f'hbase:{n:03d}:1> {r.strip()}')
        if res:
            out.append(res)
    return '\n'.join(out)
