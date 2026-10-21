"""Persistent Databricks-notebook worker used by runner.py at build time.

Databricks is a cloud service, so the examples run locally on:
  * Apache Spark 4.2 (PySpark, local mode) for every query, DataFrame and Structured Streaming example;
  * delta-rs (the `deltalake` package, the Rust implementation of the Delta Lake protocol) for Delta tables:
    every Delta table is a real directory of Parquet files plus a real _delta_log, and every write, UPDATE,
    DELETE, MERGE, OPTIMIZE, VACUUM, RESTORE, time-travel read and Change Data Feed read goes through delta-rs;
  * MLflow 3 with a local tracking store.
Spark reads a Delta table by scanning exactly the Parquet files of the requested table version, so EXPLAIN
plans show real file scans, partition filters and pushed filters.

Reads one JSON request per line on stdin, writes one JSON reply per line on stdout."""
import contextlib, datetime, decimal, io, json, os, re, shutil, sys, time, traceback, textwrap
os.environ['TZ'] = 'Asia/Kolkata'; time.tzset()
os.environ.setdefault('PYSPARK_PYTHON', sys.executable)
import warnings; warnings.filterwarnings('ignore')

BASE = '/tmp/upv_dbx'
LAKE, VOL, MLR = BASE + '/lake', BASE + '/volumes', BASE + '/mlstore'
SHOWN_LAKE = 's3://cdac-lakehouse'
for d in (LAKE, VOL):
    os.makedirs(d, exist_ok=True)
os.chdir(BASE)

import pyarrow as pa
from deltalake import DeltaTable as _DT, write_deltalake
from deltalake.schema import Field as _Field, PrimitiveType as _Prim
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType

spark = (SparkSession.builder.master('local[2]').appName('upvanta-databricks')
         .config('spark.ui.enabled', 'false')
         .config('spark.sql.session.timeZone', 'Asia/Kolkata')
         .config('spark.sql.warehouse.dir', BASE + '/spark-warehouse')
         .config('spark.driver.memory', '2g')
         .config('spark.sql.execution.pythonUDF.arrow.enabled', 'false')
         .getOrCreate())
spark.sparkContext.setLogLevel('OFF')
DEFAULT_CONF = {k: v for k, v in spark.sparkContext.getConf().getAll()}
_real_sql = spark.sql
_real_table = spark.table


class DbxError(Exception):
    """An error printed the way a Databricks notebook shows it."""


from pyspark.errors import AnalysisException as _PyAE


class AnalysisException(DbxError, _PyAE):
    def __init__(self, msg):
        Exception.__init__(self, msg)
        self._msg = msg

    def __str__(self):
        return self._msg

    def getMessage(self):
        return self._msg


# ------------------------------------------------------------------ text helpers
UUID = re.compile(r'([0-9a-f]{4})[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')


def shown(s):
    s = str(s).replace('file://' + LAKE, SHOWN_LAKE).replace('file:' + LAKE, SHOWN_LAKE).replace(LAKE, SHOWN_LAKE)
    s = s.replace('file://' + VOL, '/Volumes').replace('file:' + VOL, '/Volumes').replace(VOL, '/Volumes')
    s = s.replace('file:' + MLR, 'mlruns').replace(MLR, 'mlruns')
    s = re.sub(r'__([a-z0-9_]+?)__([a-z0-9_]+?)__([a-z0-9_]+)\b', r'\1.\2.\3', s)
    return UUID.sub(r'\1…', s)


def real_path(p):
    p = p.replace(SHOWN_LAKE, LAKE)
    if p.startswith('dbfs:/Volumes'):
        p = p[5:]
    if p.startswith('/Volumes'):
        p = VOL + p[len('/Volumes'):]
    return p


def mask_strings(s):
    lits = []

    def rep(m):
        lits.append(m.group(0)); return f'\x00{len(lits) - 1}\x00'
    return re.sub(r"'(?:[^'\\]|\\.)*'", rep, s), lits


def unmask(s, lits):
    return re.sub(r'\x00(\d+)\x00', lambda m: lits[int(m.group(1))], s)


def norm_arrow(t):
    cols, fields = [], []
    for i, f in enumerate(t.schema):
        c = t.column(i)
        typ = f.type
        if pa.types.is_string_view(typ) or pa.types.is_large_string(typ):
            typ = pa.string()
        elif pa.types.is_binary_view(typ) or pa.types.is_large_binary(typ):
            typ = pa.binary()
        elif pa.types.is_unsigned_integer(typ):
            typ = pa.int64()
        if typ != f.type:
            c = c.cast(typ)
        cols.append(c); fields.append(pa.field(f.name, typ, f.nullable))
    return pa.table(cols, schema=pa.schema(fields))


def split_sql(src):
    out, buf, i, q = [], [], 0, False
    while i < len(src):
        ch = src[i]
        if not q and src.startswith('--', i):
            j = src.find('\n', i); j = len(src) if j < 0 else j
            i = j; continue
        if ch == "'":
            q = not q
        if ch == ';' and not q:
            s = ''.join(buf).strip()
            if s: out.append(s)
            buf = []
        else:
            buf.append(ch)
        i += 1
    s = ''.join(buf).strip()
    if s: out.append(s)
    return out


def top_split(s, sep=','):
    parts, depth, buf = [], 0, ''
    for ch in s:
        if ch == '(': depth += 1
        elif ch == ')': depth -= 1
        if ch == sep and depth == 0:
            parts.append(buf.strip()); buf = ''
        else:
            buf += ch
    if buf.strip(): parts.append(buf.strip())
    return parts


def match_paren(s, i):
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '(': depth += 1
        elif s[j] == ')':
            depth -= 1
            if depth == 0: return j
    raise DbxError('unbalanced parentheses')


# ------------------------------------------------------------------ value formatting (Spark show style)
def fmt(v, top=True):
    if v is None:
        return 'NULL' if top else 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float):
        if v != v: return 'NaN'
        return repr(v)
    if isinstance(v, decimal.Decimal):
        return str(v)
    if isinstance(v, datetime.datetime):
        s = v.strftime('%Y-%m-%d %H:%M:%S.%f').rstrip('0').rstrip('.')
        return s
    if isinstance(v, datetime.date):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return '[' + ' '.join(f'{b:02X}' for b in v) + ']'
    if hasattr(v, 'asDict'):
        return '{' + ', '.join(fmt(x, False) for x in v) + '}'
    if isinstance(v, dict):
        return '{' + ', '.join(f'{fmt(k, False)} -> {fmt(x, False)}' for k, x in v.items()) + '}'
    if isinstance(v, (list, tuple)):
        return '[' + ', '.join(fmt(x, False) for x in v) + ']'
    return str(v)


def render(cols, rows, multiline=False):
    data = [[shown(fmt(c)) for c in r] for r in rows]
    if multiline:
        cells = [[c.split('\n') for c in r] for r in data]
    else:
        cells = [[[c.replace('\n', '\\n')] for c in r] for r in data]
    w = [max([len(c)] + [len(l) for r in cells for l in r[i]]) for i, c in enumerate(cols)]
    line = '+' + '+'.join('-' * (x + 2) for x in w) + '+'
    out = [line, '| ' + ' | '.join(c.ljust(w[i]) for i, c in enumerate(cols)) + ' |', line]
    for r in cells:
        for k in range(max([len(c) for c in r] or [1])):
            out.append('| ' + ' | '.join((r[i][k] if k < len(r[i]) else '').ljust(w[i]) for i in range(len(cols))) + ' |')
    out.append(line)
    return '\n'.join(out)


def render_vertical(cols, row):
    w = max(len(c) for c in cols)
    lines = ['-RECORD 0' + '-' * max(10, w)]
    for c, v in zip(cols, row):
        lines.append(f' {c.ljust(w)} | {shown(fmt(v))}')
    return '\n'.join(lines)


def render_df(df, limit=1000):
    rows = df.limit(limit).collect()
    return render(df.columns, [list(r) for r in rows])


# ------------------------------------------------------------------ the lakehouse
DML_KINDS = ('INSERT', 'UPDATE', 'DELETE', 'MERGE')


class Lake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.tables = {}      # full name -> dict(path, ops={version: (label, params)})
        self.views = {}       # full name -> set(full table names it depends on)
        self.built = {}       # view name -> (table, version) currently registered
        self.schema = 'cdac.bda'
        self.confs = {}
        for v in spark.catalog.listTables():
            if v.isTemporary:
                spark.catalog.dropTempView(v.name)
        spark.catalog.clearCache()
        for k in list(self.confs):
            pass
        if os.path.exists(LAKE): shutil.rmtree(LAKE)
        if os.path.exists(VOL): shutil.rmtree(VOL)
        os.makedirs(LAKE); os.makedirs(VOL)
        for sub in ('raw', 'landing', 'checkpoints', 'exports'):
            os.makedirs(f'{VOL}/cdac/bda/{sub}', exist_ok=True)

    # ---------- names
    def full(self, name):
        parts = [p.strip('`').lower() for p in name.strip().split('.')]
        cat, sch = self.schema.split('.')
        if len(parts) == 1: return f'{cat}.{sch}.{parts[0]}'
        if len(parts) == 2: return f'{cat}.{parts[0]}.{parts[1]}'
        return '.'.join(parts[:3])

    @staticmethod
    def vname(full):
        return '__' + full.replace('.', '__')

    def path(self, full):
        c, s, t = full.split('.')
        return f'{LAKE}/{c}/{s}/{t}'

    def dt(self, full, version=None):
        if full not in self.tables:
            short = full.split('.')
            raise DbxError(f"[TABLE_OR_VIEW_NOT_FOUND] The table or view `{'`.`'.join(short)}` cannot be found. Verify the spelling "
                           f"and correctness of the schema and catalog. SQLSTATE: 42P01")
        return _DT(self.tables[full]['path'], version=version)

    def quoted(self, full):
        return '`' + '`.`'.join(full.split('.')) + '`'

    # ---------- reading a Delta version as a Spark DataFrame (scans the real parquet files)
    def spark_schema(self, dt):
        return StructType.fromJson(json.loads(dt.schema().to_json()))

    def read(self, full, version=None):
        dt = self.dt(full, version)
        schema = self.spark_schema(dt)
        files = dt.file_uris()
        names = [f.name for f in schema.fields]
        if not files:
            return spark.createDataFrame([], schema)
        parts = dt.metadata().partition_columns
        r = spark.read.schema(schema)
        if parts:
            r = r.option('basePath', self.tables[full]['path'])
        return r.parquet(*files).select(*[f'`{n}`' for n in names])

    def register(self, full, version=None, alias=None):
        dt = self.dt(full, version)
        v = dt.version()
        name = alias or self.vname(full)
        if self.built.get(name) != (full, v):
            self.read(full, version).createOrReplaceTempView(name)
            self.built[name] = (full, v)
        return name

    def version_for_ts(self, full, ts):
        t = datetime.datetime.fromisoformat(ts.strip("'"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=datetime.datetime.now().astimezone().tzinfo)
        best = None
        for h in sorted(self.dt(full).history(), key=lambda h: h['version']):
            if datetime.datetime.fromtimestamp(h['timestamp'] / 1000).astimezone() <= t:
                best = h['version']
        if best is None:
            raise DbxError(f'[DELTA_TIMESTAMP_EARLIER_THAN_COMMIT_RETENTION] The provided timestamp ({ts}) is before the earliest version '
                           f'available to this table.')
        return best

    # ---------- rewrite table names in a Spark query
    def rewrite(self, sql):
        s, lits = mask_strings(sql)
        s = self._timetravel(s, lits)
        s = self._table_changes(s, lits)

        def rep(m):
            tok = m.group(0)
            if m.start() > 0 and s[m.start() - 1] in '.`':
                return tok
            if re.search(r'\bAS\s+$', s[max(0, m.start() - 8):m.start()], re.I):
                return tok
            parts = tok.split('.')
            for k in (3, 2, 1):
                if len(parts) >= k:
                    head = '.'.join(parts[:k])
                    f = self.full(head)
                    if f in self.tables or f in self.views:
                        if f in self.tables:
                            self.register(f)
                        else:
                            for dep in self.views[f]: self.register(dep)
                        rest = parts[k:]
                        return '.'.join([self.vname(f)] + rest)
            return tok
        s = re.sub(r'(?<![\w$])[A-Za-z_]\w*(?:\.[A-Za-z_]\w*){0,3}(?![\w(])', rep, s)
        return unmask(s, lits)

    def _timetravel(self, s, lits):
        def rep(m):
            f = self.full(m.group('n'))
            how, val = m.group('how').upper(), m.group('v')
            if how == 'VERSION':
                ver = int(val)
            else:
                ver = self.version_for_ts(f, unmask(val, lits))
            try:
                return self.register(f, ver, alias=f'{self.vname(f)}__v{ver}')
            except Exception as e:
                if 'not found' in str(e).lower() or 'version' in str(e).lower():
                    latest = self.dt(f).version()
                    raise DbxError(f'[DELTA_VERSION_NOT_FOUND] Cannot time travel Delta table to version {ver}. Available versions: [0, {latest}].')
                raise
        s = re.sub(r'(?P<n>[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*){0,2})\s+(?P<how>VERSION|TIMESTAMP)\s+AS\s+OF\s+(?P<v>\d+|\x00\d+\x00)',
                   rep, s, flags=re.I)
        s = re.sub(r'(?P<n>[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*){0,2})@v(?P<v>\d+)\b',
                   lambda m: self.register(self.full(m.group('n')), int(m.group('v')),
                                           alias=f"{self.vname(self.full(m.group('n')))}__v{m.group('v')}"), s)
        return s

    def _table_changes(self, s, lits):
        def rep(m):
            args = [unmask(a, lits).strip() for a in top_split(m.group(1))]
            f = self.full(args[0].strip("'"))
            start = int(args[1]); end = int(args[2]) if len(args) > 2 else None
            dt = self.dt(f)
            if dt.metadata().configuration.get('delta.enableChangeDataFeed', 'false').lower() != 'true':
                raise DbxError(f'[DELTA_MISSING_CHANGE_DATA] Error getting change data for range [{start} , {end or dt.version()}] as change data was not\n'
                               f'recorded for version [{start}]. If you\'ve enabled change data feed on this table,\nuse `DESCRIBE HISTORY` to see '
                               f'when it was first enabled.\nOtherwise, to start recording change data, use `ALTER TABLE table_name SET TBLPROPERTIES\n'
                               f'(delta.enableChangeDataFeed=true)`.')
            kw = dict(starting_version=start)
            if end is not None: kw['ending_version'] = end
            t = norm_arrow(pa.table(dt.load_cdf(**kw).read_all()))
            t = t.set_column(t.schema.get_field_index('_commit_timestamp'), '_commit_timestamp',
                             t.column('_commit_timestamp').cast(pa.timestamp('us', tz='UTC')))
            order = [c for c in t.column_names if not c.startswith('_')] + ['_change_type', '_commit_version', '_commit_timestamp']
            name = f'{self.vname(f)}__cdf{start}_{end or "x"}'
            spark.createDataFrame(t.select(order)).createOrReplaceTempView(name)
            self.built.pop(name, None)
            return name
        return re.sub(r'table_changes\s*\(([^()]*)\)', rep, s, flags=re.I)

    # ---------- converting Spark rows for a Delta write
    def to_arrow(self, df):
        t = df.toArrow()
        cols = []
        for i, f in enumerate(t.schema):
            c = t.column(i)
            if pa.types.is_timestamp(f.type):
                c = c.cast(pa.timestamp('us', tz='UTC'))
            cols.append(c)
        return pa.table(cols, names=t.column_names)

    def target_cols(self, full):
        return self.spark_schema(self.dt(full)).fields

    def conform(self, full, df, cols=None, by_name=False):
        fields = self.target_cols(full)
        names = [f.name for f in fields]
        data_cols = df.columns
        if by_name:
            sel = [f'CAST(`{f.name}` AS {f.dataType.simpleString()}) AS `{f.name}`' if f.name in data_cols else
                   f'CAST(NULL AS {f.dataType.simpleString()}) AS `{f.name}`' for f in fields]
            return df.selectExpr(*sel)
        cols = [c.strip('` ').lower() for c in cols] if cols else names
        if len(data_cols) > len(cols):
            raise DbxError(f'[INSERT_COLUMN_ARITY_MISMATCH.TOO_MANY_DATA_COLUMNS] Cannot write to {self.quoted(full)}, the reason is too many data '
                           f'columns:\nTable columns: {", ".join("`" + c + "`" for c in cols)}.\nData columns: '
                           f'{", ".join("`" + c + "`" for c in data_cols)}. SQLSTATE: 21S01')
        if len(data_cols) < len(cols):
            raise DbxError(f'[INSERT_COLUMN_ARITY_MISMATCH.NOT_ENOUGH_DATA_COLUMNS] Cannot write to {self.quoted(full)}, the reason is not enough '
                           f'data columns:\nTable columns: {", ".join("`" + c + "`" for c in cols)}.\nData columns: '
                           f'{", ".join("`" + c + "`" for c in data_cols)}. SQLSTATE: 21S01')
        pos = dict(zip(cols, data_cols))
        sel = []
        for f in fields:
            t = f.dataType.simpleString()
            sel.append(f'CAST(`{pos[f.name]}` AS {t}) AS `{f.name}`' if f.name in pos else f'CAST(NULL AS {t}) AS `{f.name}`')
        return df.selectExpr(*sel)

    def constraints(self, full):
        conf = self.dt(full).metadata().configuration
        orig = self.tables[full].get('checks', {})
        return {k.split('.', 2)[2]: orig.get(k.split('.', 2)[2], v) for k, v in conf.items() if k.startswith('delta.constraints.')}

    def check(self, full, df):
        for f in self.target_cols(full):
            if not f.nullable and df.filter(f'`{f.name}` IS NULL').limit(1).count():
                raise DbxError(f'[DELTA_NOT_NULL_CONSTRAINT_VIOLATED] NOT NULL constraint violated for column: {f.name}. SQLSTATE: 23502')
        for name, expr in self.constraints(full).items():
            bad = df.filter(f'NOT coalesce(({expr}), false)').limit(1).collect()
            if bad:
                row = bad[0].asDict()
                used = [c for c in row if re.search(rf'\b{re.escape(c)}\b', expr)]
                vals = '\n'.join(f' - {c} : {fmt(row[c])}' for c in used)
                raise DbxError(f'[DELTA_VIOLATE_CONSTRAINT_WITH_VALUES] CHECK constraint {name} ({expr}) violated by row with values:\n{vals}'
                               f'\nSQLSTATE: 23001')

    def label(self, full, label, params=None):
        v = self.dt(full).version()
        self.tables[full]['ops'][v] = (label, params)

    # ---------- table creation / writes
    def create(self, full, df, replace=False, partition_by=None, props=None, label=None, if_not_exists=False, not_null=()):
        path = self.path(full)
        exists = full in self.tables
        if exists and if_not_exists:
            return None
        if exists and not replace:
            raise DbxError(f'[TABLE_OR_VIEW_ALREADY_EXISTS] Cannot create table or view {self.quoted(full)} because it already exists.\n'
                           f'Choose a different name, drop or replace the existing object, add the IF NOT EXISTS clause to tolerate '
                           f'pre-existing objects, add the OR REPLACE clause to replace the existing materialized view, or add the OR '
                           f'REFRESH clause to refresh the existing streaming table. SQLSTATE: 42P07')
        t = self.to_arrow(df)
        if not_null:
            t = pa.table(t.columns, schema=pa.schema([f.with_nullable(f.name not in not_null) for f in t.schema]))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if exists:
            write_deltalake(path, t, mode='overwrite', schema_mode='overwrite', partition_by=partition_by or None,
                            configuration=props or None)
        else:
            write_deltalake(path, t, mode='error', partition_by=partition_by or None, configuration=props or None)
            self.tables[full] = dict(path=path, ops={})
        self.label(full, label or ('CREATE OR REPLACE TABLE' if exists else 'CREATE TABLE'))
        return t.num_rows

    def append(self, full, df, mode='append', predicate=None, merge_schema=False):
        if merge_schema:
            extra = [c for c in df.columns if c not in [f.name for f in self.target_cols(full)]]
            if extra:
                self.check(full, self.conform(full, df, by_name=True))
            tf = {f.name: f.dataType.simpleString() for f in self.target_cols(full)}
            df = df.selectExpr(*[f'CAST(`{c}` AS {tf[c]}) AS `{c}`' if c in tf else f'`{c}`' for c in df.columns])
            t = self.to_arrow(df)
            write_deltalake(self.tables[full]['path'], t, mode=mode, schema_mode='merge')
            return t.num_rows
        self.check(full, df)
        t = self.to_arrow(df)
        kw = dict(mode=mode)
        if predicate:
            kw['predicate'] = predicate
        write_deltalake(self.tables[full]['path'], t, **kw)
        return t.num_rows

    def schema_mismatch(self, full, df):
        def tree(st):
            return '\n'.join(f'-- {f.name}: {f.dataType.typeName() if not hasattr(f.dataType, "simpleString") else _tn(f.dataType)} '
                             f'(nullable = {str(f.nullable).lower()})' for f in st.fields)
        tid = self.dt(full).metadata().id
        return AnalysisException(f'[_LEGACY_ERROR_TEMP_DELTA_0007] A schema mismatch detected when writing to the Delta table (Table ID: {tid}).\n'
                        f'To enable schema migration using DataFrameWriter or DataStreamWriter, please set:\n'
                        f'\'.option("mergeSchema", "true")\'.\nFor other operations, set the session configuration\n'
                        f'spark.databricks.delta.schema.autoMerge.enabled to "true". See the documentation\n'
                        f'specific to the operation for details.\n\nTable schema:\nroot\n{tree(self.spark_schema(self.dt(full)))}\n\n'
                        f'Data schema:\nroot\n{tree(df.schema)}')

    # ---------- the SQL dispatcher
    def sql(self, stmt):
        s = stmt.strip().rstrip(';').strip()
        m, lits = mask_strings(s)
        u = ' '.join(m.split()).upper()
        word = u.split(None, 1)[0] if u else ''
        handlers = [
            (r'^CREATE\s+(OR\s+REPLACE\s+)?(TEMP(ORARY)?\s+)?VIEW\b', self._create_view),
            (r'^CREATE\s+(CATALOG|SCHEMA|DATABASE|VOLUME)\b', self._noop),
            (r'^CREATE\s+(OR\s+REPLACE\s+)?TABLE\b', self._create_table),
            (r'^(USE)\b', self._use),
            (r'^INSERT\b', self._insert),
            (r'^UPDATE\b', self._update),
            (r'^DELETE\s+FROM\b', self._delete),
            (r'^MERGE\s+INTO\b', self._merge),
            (r'^(DESCRIBE|DESC)\s+HISTORY\b', self._history),
            (r'^(DESCRIBE|DESC)\s+DETAIL\b', self._detail),
            (r'^OPTIMIZE\b', self._optimize),
            (r'^VACUUM\b', self._vacuum),
            (r'^RESTORE\b', self._restore),
            (r'^ALTER\s+TABLE\b', self._alter),
            (r'^SHOW\s+TBLPROPERTIES\b', self._tblprops),
            (r'^SHOW\s+TABLES\b', self._show_tables),
            (r'^DROP\s+TABLE\b', self._drop),
            (r'^DROP\s+VIEW\b', self._drop_view),
            (r'^SET\b', self._set),
            (r'^(DESCRIBE|DESC)\b', self._describe),
        ]
        for pat, fn in handlers:
            if re.match(pat, u):
                return fn(s, m, lits)
        return self._query(s)

    def _query(self, s):
        return _real_sql(self.rewrite(s))

    def _noop(self, s, m, lits):
        return None

    def _use(self, s, m, lits):
        parts = s.split()
        name = parts[-1].strip('`').lower()
        kind = parts[1].upper() if len(parts) > 2 else ''
        cat, sch = self.schema.split('.')
        if kind == 'CATALOG': self.schema = f'{name}.{sch}'
        elif '.' in name: self.schema = name
        else: self.schema = f'{cat}.{name}'
        return None

    def _set(self, s, m, lits):
        body = s[3:].strip()
        if '=' not in body:
            return None
        k, v = [x.strip() for x in body.split('=', 1)]
        self.confs[k] = v
        try:
            spark.conf.set(k, v)
        except Exception:
            pass
        return spark.createDataFrame([(k, v)], 'key string, value string')

    def conf_true(self, k):
        return str(self.confs.get(k, 'false')).lower() == 'true'

    def _create_view(self, s, m, lits):
        mm = re.match(r'CREATE\s+(OR\s+REPLACE\s+)?(TEMP(?:ORARY)?\s+)?VIEW\s+(IF\s+NOT\s+EXISTS\s+)?(\S+)\s+AS\s+(.*)$', s, re.S | re.I)
        full = self.full(mm.group(4))
        q = mm.group(5)
        before = set(self.built)
        sq = self.rewrite(q)
        deps = set()
        for f in self.tables:
            if re.search(rf'\b{self.vname(f)}\b', sq): deps.add(f)
        for v, d in self.views.items():
            if re.search(rf'\b{self.vname(v)}\b', sq): deps |= d
        _real_sql(f'CREATE OR REPLACE TEMP VIEW {self.vname(full)} AS {sq}')
        self.views[full] = deps
        return None

    def _drop_view(self, s, m, lits):
        name = s.split()[-1]
        full = self.full(name)
        if full in self.views:
            spark.catalog.dropTempView(self.vname(full)); del self.views[full]
        return None

    def _parse_props(self, txt):
        props = {}
        for kv in top_split(txt):
            k, v = kv.split('=', 1)
            props[k.strip().strip("'`")] = v.strip().strip("'")
        return props

    def _create_table(self, s, m, lits):
        mm = re.match(r'CREATE\s+(?P<rep>OR\s+REPLACE\s+)?TABLE\s+(?P<ine>IF\s+NOT\s+EXISTS\s+)?(?P<name>[\w.`]+)\s*(?P<rest>.*)$', m, re.S | re.I)
        full = self.full(mm.group('name'))
        rest = mm.group('rest')
        cols_ddl = None
        if rest.startswith('('):
            j = match_paren(rest, 0)
            cols_ddl = unmask(rest[1:j], lits); rest = rest[j + 1:].strip()
        part = props = None
        q = None
        mq = re.search(r'\bAS\s+(SELECT|WITH|VALUES|\()', rest, re.I)
        opts = rest[:mq.start()] if mq else rest
        if mq:
            q = unmask(rest[mq.start() + 2:].strip(), lits)
        mp = re.search(r'PARTITIONED\s+BY\s*\(([^)]*)\)', opts, re.I)
        if mp: part = [c.strip().strip('`').lower() for c in mp.group(1).split(',')]
        mt = re.search(r'TBLPROPERTIES\s*\(', opts, re.I)
        if mt:
            j = match_paren(opts, mt.end() - 1)
            props = self._parse_props(unmask(opts[mt.end():j], lits))
        if re.search(r'\bCLUSTER\s+BY\b', opts, re.I):
            raise DbxError('CLUSTER BY (liquid clustering) is shown without output on this page')
        rep = bool(mm.group('rep'))
        not_null = set()
        if q is not None:
            df = _real_sql(self.rewrite(q))
            n = self.create(full, df, replace=rep, partition_by=part, props=props,
                            label=('CREATE OR REPLACE TABLE AS SELECT' if rep else 'CREATE TABLE AS SELECT'),
                            if_not_exists=bool(mm.group('ine')))
            if n is None: return None
            return spark.createDataFrame([(n, n)], 'num_affected_rows bigint, num_inserted_rows bigint')
        defs, checks = [], {}
        for c in top_split(cols_ddl):
            ck = re.match(r'CONSTRAINT\s+(\w+)\s+CHECK\s*\((.*)\)\s*$', c, re.I | re.S)
            if ck:
                checks[ck.group(1)] = ck.group(2).strip(); continue
            cname = c.split()[0].strip('`').lower()
            if re.search(r'\bNOT\s+NULL\b', c, re.I):
                not_null.add(cname)
            c = re.sub(r'\bNOT\s+NULL\b', '', c, flags=re.I)
            c = re.sub(r"\bCOMMENT\s+'(?:[^'\\]|\\.)*'", '', c, flags=re.I)
            defs.append(c.strip())
        schema = StructType.fromDDL(', '.join(defs))
        df = spark.createDataFrame([], schema)
        n = self.create(full, df, replace=rep, partition_by=part, props=props, if_not_exists=bool(mm.group('ine')), not_null=not_null)
        for k, v in checks.items():
            self.dt(full).alter.add_constraint({k: v})
            self.tables[full].setdefault('checks', {})[k] = v
        return None

    def _source_df(self, body):
        """VALUES (...) | SELECT ... | WITH ... | TABLE x"""
        b = body.strip()
        if re.match(r'VALUES\b', b, re.I):
            return _real_sql(self.rewrite('SELECT * FROM ' + b))
        if re.match(r'TABLE\s', b, re.I):
            return _real_sql(self.rewrite('SELECT * FROM ' + b[5:].strip()))
        return _real_sql(self.rewrite(b))

    def _insert(self, s, m, lits):
        mm = re.match(r'INSERT\s+(?P<mode>INTO|OVERWRITE)\s+(?:TABLE\s+)?(?P<name>[\w.`]+)\s*(?P<rest>.*)$', m, re.S | re.I)
        full = self.full(mm.group('name'))
        self.dt(full)
        rest = mm.group('rest')
        cols = None
        by_name = False
        if re.match(r'BY\s+NAME\b', rest, re.I):
            by_name = True; rest = rest[7:].strip()
        if rest.startswith('('):
            j = match_paren(rest, 0)
            inner = rest[1:j]
            if not re.match(r'\s*(SELECT|WITH)\b', inner, re.I):
                cols = [c.strip() for c in inner.split(',')]; rest = rest[j + 1:].strip()
        predicate = None
        mr = re.match(r'REPLACE\s+WHERE\s+(.*?)\s+(SELECT|WITH|VALUES|TABLE)\b', rest, re.S | re.I)
        if mr:
            predicate = unmask(mr.group(1), lits)
            rest = rest[mr.start(2):]
        df = self._source_df(unmask(rest, lits))
        df = self.conform(full, df, cols, by_name=by_name)
        mode = 'overwrite' if mm.group('mode').upper() == 'OVERWRITE' or predicate else 'append'
        n = self.append(full, df, mode=mode, predicate=predicate)
        self.label(full, 'WRITE', {'mode': 'Overwrite' if mode == 'overwrite' else 'Append',
                                   **({'predicate': f'["{predicate}"]'} if predicate else {})})
        return spark.createDataFrame([(n, n)], 'num_affected_rows bigint, num_inserted_rows bigint')

    def _split_where(self, txt):
        mw = re.search(r'\bWHERE\b', txt, re.I)
        if not mw: return txt, None
        return txt[:mw.start()], txt[mw.end():].strip()

    def _update(self, s, m, lits):
        mm = re.match(r'UPDATE\s+(?P<name>[\w.`]+)(?:\s+(?:AS\s+)?(?P<alias>(?!SET\b)\w+))?\s+SET\s+(?P<rest>.*)$', m, re.S | re.I)
        full = self.full(mm.group('name'))
        sets, where = self._split_where(mm.group('rest'))
        updates = {}
        for a in top_split(sets):
            k, v = a.split('=', 1)
            updates[k.strip().split('.')[-1].strip('`').lower()] = unmask(v.strip(), lits)
        pred = unmask(where, lits) if where else None
        # validate CHECK / NOT NULL constraints on the rows the UPDATE would produce
        view = self.register(full)
        fields = [f.name for f in self.target_cols(full)]
        sel = ', '.join(f'{updates[c]} AS `{c}`' if c in updates else f'`{c}`' for c in fields)
        preview = _real_sql(f'SELECT {sel} FROM {view}' + (f' WHERE {self.rewrite(pred)}' if pred else ''))
        self.check(full, self.conform(full, preview, by_name=True))
        dt = self.dt(full)
        r = dt.update(updates=updates, predicate=pred) if pred else dt.update(updates=updates)
        self.label(full, 'UPDATE', {'predicate': f'["{pred}"]' if pred else '["true"]'})
        n = r['num_updated_rows']
        return spark.createDataFrame([(n,)], 'num_affected_rows bigint')

    def _delete(self, s, m, lits):
        mm = re.match(r'DELETE\s+FROM\s+(?P<name>[\w.`]+)(?:\s+(?:AS\s+)?(?P<alias>(?!WHERE\b)\w+))?\s*(?P<rest>.*)$', m, re.S | re.I)
        full = self.full(mm.group('name'))
        _, where = self._split_where(mm.group('rest'))
        pred = unmask(where, lits) if where else None
        dt = self.dt(full)
        r = dt.delete(pred) if pred else dt.delete()
        self.label(full, 'DELETE', {'predicate': f'["{pred}"]' if pred else '[]'})
        n = r.get('num_deleted_rows') or 0
        return spark.createDataFrame([(n,)], 'num_affected_rows bigint')

    # ---------- MERGE
    def _merge(self, s, m, lits):
        mm = re.match(r'MERGE\s+(?:WITH\s+SCHEMA\s+EVOLUTION\s+)?INTO\s+(?P<name>[\w.`]+)(?:\s+(?:AS\s+)?(?P<ta>(?!USING\b)\w+))?\s+USING\s+(?P<rest>.*)$',
                      m, re.S | re.I)
        evolve = bool(re.match(r'MERGE\s+WITH\s+SCHEMA\s+EVOLUTION', m, re.I))
        full = self.full(mm.group('name'))
        ta = mm.group('ta') or full.split('.')[-1]
        rest = mm.group('rest').strip()
        if rest.startswith('('):
            j = match_paren(rest, 0)
            src_sql = unmask(rest[1:j], lits); rest = rest[j + 1:].strip()
            src_df = _real_sql(self.rewrite(src_sql))
            default_sa = 'source'
        else:
            name, rest = rest.split(None, 1)
            src_df = _real_sql(self.rewrite('SELECT * FROM ' + name))
            default_sa = name.split('.')[-1]
        ms = re.match(r'(?:AS\s+)?(?P<sa>(?!ON\b)\w+)?\s*ON\s+(?P<rest>.*)$', rest, re.S | re.I)
        sa = ms.group('sa') or default_sa
        rest = ms.group('rest')
        parts = re.split(r'\bWHEN\b', rest, flags=re.I)
        on = unmask(parts[0].strip(), lits)
        clauses = []
        for c in parts[1:]:
            c = c.strip()
            mc = re.match(r'(?P<kind>NOT\s+MATCHED(?:\s+BY\s+(?:TARGET|SOURCE))?|MATCHED)(?:\s+AND\s+(?P<cond>.*?))?\s+THEN\s+(?P<act>.*)$',
                          c, re.S | re.I)
            kind = ' '.join(mc.group('kind').upper().split())
            if kind == 'NOT MATCHED BY TARGET': kind = 'NOT MATCHED'
            cond = unmask(mc.group('cond'), lits) if mc.group('cond') else None
            act = mc.group('act').strip()
            clauses.append((kind, cond, act))
        return self.do_merge(full, src_df, on, ta, sa, clauses, lits, evolve)

    def do_merge(self, full, src_df, on, ta, sa, clauses, lits=(), evolve=False):
        evolve = evolve or self.conf_true('spark.databricks.delta.schema.autoMerge.enabled')
        src = self.to_arrow(src_df)
        dt = self.dt(full)
        b = dt.merge(source=src, predicate=on, source_alias=sa, target_alias=ta, merge_schema=evolve)
        params = {'predicate': f'["{on}"]'}
        for kind, cond, act in clauses:
            au = act.upper()
            kw = {'predicate': cond} if cond else {}
            if kind == 'MATCHED':
                if au.startswith('DELETE'):
                    b = b.when_matched_delete(**kw)
                elif re.match(r'UPDATE\s+SET\s+\*', au):
                    b = b.when_matched_update_all(**kw)
                else:
                    sets = re.sub(r'^UPDATE\s+SET\s+', '', act, flags=re.I)
                    upd = {}
                    for a in top_split(sets):
                        k, v = a.split('=', 1)
                        upd[k.strip().split('.')[-1].strip('`').lower()] = unmask(v.strip(), lits)
                    b = b.when_matched_update(updates=upd, **kw)
            elif kind == 'NOT MATCHED':
                if re.match(r'INSERT\s*\*', au):
                    b = b.when_not_matched_insert_all(**kw)
                else:
                    mi = re.match(r'INSERT\s*\((.*?)\)\s*VALUES\s*\((.*)\)\s*$', act, re.S | re.I)
                    cols = [c.strip().strip('`').lower() for c in mi.group(1).split(',')]
                    vals = [unmask(v, lits) for v in top_split(mi.group(2))]
                    b = b.when_not_matched_insert(updates=dict(zip(cols, vals)), **kw)
            else:  # NOT MATCHED BY SOURCE
                if au.startswith('DELETE'):
                    b = b.when_not_matched_by_source_delete(**kw)
                else:
                    sets = re.sub(r'^UPDATE\s+SET\s+', '', act, flags=re.I)
                    upd = {}
                    for a in top_split(sets):
                        k, v = a.split('=', 1)
                        upd[k.strip().split('.')[-1].strip('`').lower()] = unmask(v.strip(), lits)
                    b = b.when_not_matched_by_source_update(updates=upd, **kw)
        try:
            r = b.execute()
        except Exception as e:
            msg = str(e)
            if 'multiple source rows' in msg.lower() or 'duplicate' in msg.lower() and 'source' in msg.lower():
                raise DbxError('[DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE] Cannot perform Merge as multiple source rows matched '
                               'and attempted to modify the same\ntarget row in the Delta table in possibly conflicting ways. By SQL semantics '
                               'of Merge,\nwhen multiple source rows match on the same target row, the result may be ambiguous\nas it is unclear '
                               'which source row should be used to update or delete the matching\ntarget row. You can preprocess the source table '
                               'to eliminate the possibility of\nmultiple matches. SQLSTATE: 21506')
            if 'invalid data' in msg.lower() or 'failed validation' in msg.lower():
                raise DbxError('[DELTA_VIOLATE_CONSTRAINT_WITH_VALUES] CHECK constraint violated by a row written by MERGE')
            raise
        self.label(full, 'MERGE', params)
        ins, upd, de = r['num_target_rows_inserted'], r['num_target_rows_updated'], r['num_target_rows_deleted']
        return spark.createDataFrame([(ins + upd + de, upd, de, ins)],
                                     'num_affected_rows bigint, num_updated_rows bigint, num_deleted_rows bigint, num_inserted_rows bigint')

    # ---------- Delta utility commands
    def _name_after(self, s, kw_re):
        mm = re.match(kw_re + r'\s+(?P<name>[\w.`]+)', s, re.I)
        return self.full(mm.group('name')), s[mm.end():].strip()

    def history_rows(self, full, limit=None):
        ops = self.tables[full]['ops']
        rows = []
        for h in sorted(self.dt(full).history(), key=lambda h: -h['version']):
            v = h['version']
            op, params = ops.get(v, (h['operation'], None))
            p = params if params is not None else {k: v2 for k, v2 in (h.get('operationParameters') or {}).items()
                                                   if k not in ('metadata', 'protocol', 'location', 'mode') or op == 'WRITE'}
            if op.startswith('CREATE') and params is None:
                md = self.dt(full, v).metadata()
                p = {'isManaged': 'true', 'description': None, 'partitionBy': json.dumps(md.partition_columns),
                     'properties': json.dumps(dict(md.configuration))}
            if op == 'WRITE' and 'mode' in p and 'partitionBy' not in p:
                p = {'mode': p['mode'], **{k: x for k, x in p.items() if k != 'mode'}}
            metrics = {}
            for k, x in (h.get('operationMetrics') or {}).items():
                if k in ('num_retries', 'num_partitions'):
                    continue
                if h['operation'] in ('WRITE', 'CREATE TABLE') and k in ('num_added_files', 'num_added_rows'):
                    k = {'num_added_files': 'numFiles', 'num_added_rows': 'numOutputRows'}[k]
                metrics[re.sub(r'_(\w)', lambda mm: mm.group(1).upper(), k)] = str(x)
            ts = datetime.datetime.fromtimestamp(h['timestamp'] / 1000)
            rows.append((v, ts.replace(microsecond=0), op, {k: (None if x is None else str(x)) for k, x in p.items()}, h.get('readVersion'), metrics))
        return rows[:limit] if limit else rows

    def _history(self, s, m, lits):
        full, rest = self._name_after(s, r'(?:DESCRIBE|DESC)\s+HISTORY')
        ml = re.search(r'LIMIT\s+(\d+)', rest, re.I)
        rows = self.history_rows(full, int(ml.group(1)) if ml else None)
        return ('history', rows)
        return spark.createDataFrame(rows, 'version bigint, timestamp timestamp, operation string, operationParameters map<string,string>, '
                                           'readVersion bigint, operationMetrics map<string,string>')

    def detail_row(self, full):
        dt = self.dt(full)
        md = dt.metadata()
        acts = pa.table(dt.get_add_actions(flatten=True))
        size = sum(acts.column('size_bytes').to_pylist()) if acts.num_rows else 0
        pr = dt.protocol()
        hist = sorted(dt.history(), key=lambda h: h['version'])
        created = datetime.datetime.fromtimestamp(md.created_time / 1000).replace(microsecond=0)
        modified = datetime.datetime.fromtimestamp(hist[-1]['timestamp'] / 1000).replace(microsecond=0)
        feats = sorted(set((pr.reader_features or []) + (pr.writer_features or [])))
        return ('delta', md.id, full, self.tables[full]['path'], created, modified, list(md.partition_columns), [],
                acts.num_rows, size, dict(md.configuration), pr.min_reader_version, pr.min_writer_version, feats)

    DETAIL_COLS = ['format', 'id', 'name', 'location', 'createdAt', 'lastModified', 'partitionColumns', 'clusteringColumns', 'numFiles',
                   'sizeInBytes', 'properties', 'minReaderVersion', 'minWriterVersion', 'tableFeatures']

    def _detail(self, s, m, lits):
        full, _ = self._name_after(s, r'(?:DESCRIBE|DESC)\s+DETAIL')
        r = self.detail_row(full)
        return spark.createDataFrame([r], 'format string, id string, name string, location string, createdAt timestamp, lastModified timestamp, '
                                          'partitionColumns array<string>, clusteringColumns array<string>, numFiles bigint, sizeInBytes bigint, '
                                          'properties map<string,string>, minReaderVersion int, minWriterVersion int, tableFeatures array<string>')

    def _optimize(self, s, m, lits):
        full, rest = self._name_after(s, r'OPTIMIZE')
        rm, _ = mask_strings(rest)
        z = re.search(r'ZORDER\s+BY\s*\(([^)]*)\)', rest, re.I)
        w = re.search(r'WHERE\s+(.*?)(?=\s+ZORDER\b|$)', rest, re.I | re.S)
        filt = None
        if w:
            filt = []
            for cond in re.split(r'\s+AND\s+', w.group(1), flags=re.I):
                c, v = [x.strip() for x in cond.split('=')]
                filt.append((c.strip('`').lower(), '=', v.strip("'")))
        dt = self.dt(full)
        if z:
            cols = [c.strip().strip('`').lower() for c in z.group(1).split(',')]
            r = dt.optimize.z_order(cols, partition_filters=filt) if filt else dt.optimize.z_order(cols)
        else:
            r = dt.optimize.compact(partition_filters=filt) if filt else dt.optimize.compact()
        self.label(full, 'OPTIMIZE', {'predicate': json.dumps([w.group(1).strip()] if w else []),
                                      'zOrderBy': json.dumps([c.strip() for c in z.group(1).split(',')] if z else [])})
        fa, fr = json.loads(r['filesAdded']), json.loads(r['filesRemoved'])
        metrics = {'numFilesAdded': r['numFilesAdded'], 'numFilesRemoved': r['numFilesRemoved'],
                   'filesAdded': {k: fa[k] for k in ('min', 'max', 'avg', 'totalFiles', 'totalSize')},
                   'filesRemoved': {k: fr[k] for k in ('min', 'max', 'avg', 'totalFiles', 'totalSize')},
                   'partitionsOptimized': r['partitionsOptimized'], 'numBatches': r['numBatches'],
                   'totalConsideredFiles': r['totalConsideredFiles'], 'totalFilesSkipped': r['totalFilesSkipped']}
        return ('optimize', self.tables[full]['path'], metrics)

    def _vacuum(self, s, m, lits):
        full, rest = self._name_after(s, r'VACUUM')
        mr = re.search(r'RETAIN\s+(\d+(?:\.\d+)?)\s+HOURS', rest, re.I)
        dry = bool(re.search(r'DRY\s+RUN', rest, re.I))
        hours = float(mr.group(1)) if mr else 168
        check = str(self.confs.get('spark.databricks.delta.retentionDurationCheck.enabled', 'true')).lower() != 'false'
        if hours < 168 and check:
            raise DbxError('requirement failed: Are you sure you would like to vacuum files with such a low retention period? If you have\n'
                           'writers that are currently writing to this table, there is a risk that you may corrupt the\nstate of your Delta '
                           'table.\n\nIf you are certain that there are no operations being performed on this table, such as\n'
                           'insert/upsert/delete/optimize, then you may turn off this check by setting:\n'
                           'spark.databricks.delta.retentionDurationCheck.enabled = false\n\nIf you are not sure, please use a value not less '
                           'than "168 hours".')
        dt = self.dt(full)
        files = dt.vacuum(retention_hours=int(hours), dry_run=dry, enforce_retention_duration=False)
        p = self.tables[full]['path']
        if dry:
            return ('vacuum_dry', [f'{p}/{f}' for f in sorted(files)])
        if files:
            v = self.dt(full).version()
            for ver in range(v - 1, v + 1):
                pass
        return ('vacuum', p, len(files))

    def _restore(self, s, m, lits):
        mm = re.match(r'RESTORE\s+(?:TABLE\s+)?(?P<name>[\w.`]+)\s+(?:TO\s+)?(?P<how>VERSION|TIMESTAMP)\s+AS\s+OF\s+(?P<v>.+)$', s, re.I | re.S)
        full = self.full(mm.group('name'))
        ver = int(mm.group('v')) if mm.group('how').upper() == 'VERSION' else self.version_for_ts(full, mm.group('v').strip())
        cur = {r['path']: r['size_bytes'] for r in pa.table(self.dt(full).get_add_actions(flatten=True)).to_pylist()}
        tgt = {r['path']: r['size_bytes'] for r in pa.table(self.dt(full, ver).get_add_actions(flatten=True)).to_pylist()}
        self.dt(full).restore(ver)
        self.label(full, 'RESTORE', {'version': str(ver), 'timestamp': 'null'})
        removed = set(cur) - set(tgt); restored = set(tgt) - set(cur)
        row = (sum(tgt.values()), len(tgt), len(removed), len(restored), sum(cur[f] for f in removed), sum(tgt[f] for f in restored))
        return spark.createDataFrame([row], 'table_size_after_restore bigint, num_of_files_after_restore bigint, num_removed_files bigint, '
                                            'num_restored_files bigint, removed_files_size bigint, restored_files_size bigint')

    def _alter(self, s, m, lits):
        full, rest = self._name_after(s, r'ALTER\s+TABLE')
        dt = self.dt(full)
        mc = re.match(r'ADD\s+CONSTRAINT\s+(\w+)\s+CHECK\s*\((.*)\)\s*$', rest, re.I | re.S)
        if mc:
            name, expr = mc.group(1), mc.group(2).strip()
            view = self.register(full)
            n = _real_sql(f'SELECT count(*) FROM {view} WHERE NOT coalesce(({expr}), false)').collect()[0][0]
            if n:
                raise DbxError(f'[DELTA_NEW_CHECK_CONSTRAINT_VIOLATION] {n} rows in {full} violate the new CHECK constraint ({expr}). SQLSTATE: 23512')
            dt.alter.add_constraint({name: expr})
            self.tables[full].setdefault('checks', {})[name] = expr
            self.label(full, 'ADD CONSTRAINT', {'name': name, 'expr': expr})
            return None
        md = re.match(r'DROP\s+CONSTRAINT\s+(?:IF\s+EXISTS\s+)?(\w+)', rest, re.I)
        if md:
            dt.alter.drop_constraint(md.group(1))
            self.tables[full].get('checks', {}).pop(md.group(1), None)
            self.label(full, 'DROP CONSTRAINT', {'name': md.group(1)})
            return None
        mt = re.match(r'SET\s+TBLPROPERTIES\s*\((.*)\)\s*$', rest, re.I | re.S)
        if mt:
            props = self._parse_props(mt.group(1))
            dt.alter.set_table_properties(props)
            self.label(full, 'SET TBLPROPERTIES', {'properties': json.dumps(props)})
            return None
        ma = re.match(r'ADD\s+COLUMNS?\s*\((.*)\)\s*$', rest, re.I | re.S)
        if ma:
            fields = []
            for c in top_split(ma.group(1)):
                c = re.sub(r"\bCOMMENT\s+'(?:[^'\\]|\\.)*'", '', c, flags=re.I).strip()
                name, typ = c.split(None, 1)
                st = StructType.fromDDL(f'`{name}` {typ}')
                fields.append(_Field(name.strip('`').lower(), _Prim(_delta_type(st.fields[0].dataType)), nullable=True))
            dt.alter.add_columns(fields)
            self.label(full, 'ADD COLUMNS', {'columns': json.dumps([f.name for f in fields])})
            return None
        raise DbxError(f'ALTER TABLE form not supported by the build emulator: {rest}')

    def _tblprops(self, s, m, lits):
        full, _ = self._name_after(s, r'SHOW\s+TBLPROPERTIES')
        dt = self.dt(full)
        pr = dt.protocol()
        orig = self.tables[full].get('checks', {})
        rows = [(k, orig.get(k[len('delta.constraints.'):], v) if k.startswith('delta.constraints.') else v)
                for k, v in sorted(dt.metadata().configuration.items())]
        rows += [('delta.minReaderVersion', str(pr.min_reader_version)), ('delta.minWriterVersion', str(pr.min_writer_version))]
        return spark.createDataFrame(sorted(rows), 'key string, value string')

    def _show_tables(self, s, m, lits):
        mm = re.match(r'SHOW\s+TABLES(?:\s+(?:IN|FROM)\s+([\w.`]+))?', s, re.I)
        sch = mm.group(1)
        sch = (sch.strip('`').lower() if sch and '.' in sch else f"{self.schema.split('.')[0]}.{sch.lower()}") if sch else self.schema
        rows = sorted({tuple(f.rsplit('.', 1)) for f in list(self.tables) + list(self.views) if f.rsplit('.', 1)[0] == sch})
        return spark.createDataFrame([(r[0].split('.')[1], r[1], False) for r in rows] or [],
                                     'database string, tableName string, isTemporary boolean')

    def _drop(self, s, m, lits):
        mm = re.match(r'DROP\s+TABLE\s+(IF\s+EXISTS\s+)?([\w.`]+)', s, re.I)
        full = self.full(mm.group(2))
        if full not in self.tables:
            if mm.group(1): return None
            self.dt(full)
        shutil.rmtree(self.tables[full]['path'], ignore_errors=True)
        del self.tables[full]
        for k in [k for k, v in self.built.items() if v[0] == full]:
            spark.catalog.dropTempView(k); del self.built[k]
        return None

    def _describe(self, s, m, lits):
        mm = re.match(r'(?:DESCRIBE|DESC)\s+(?:TABLE\s+)?(EXTENDED\s+)?([\w.`]+)', s, re.I)
        full = self.full(mm.group(2))
        if full in self.tables:
            df = _real_sql(f'DESCRIBE {self.register(full)}')
            parts = self.dt(full).metadata().partition_columns
            rows = [tuple(r) for r in df.collect()]
            if parts:
                rows += [('# Partition Information', '', ''), ('# col_name', 'data_type', 'comment')]
                rows += [r for r in rows if r[0] in parts]
            if mm.group(1):
                d = dict(zip(self.DETAIL_COLS, self.detail_row(full)))
                rows += [('', '', ''), ('# Detailed Table Information', '', ''), ('Catalog', full.split('.')[0], ''),
                         ('Database', full.split('.')[1], ''), ('Table', full.split('.')[2], ''), ('Type', 'MANAGED', ''),
                         ('Location', d['location'], ''), ('Provider', 'delta', ''),
                         ('Table Properties', '[' + ','.join(f'{k}={v}' for k, v in sorted(d['properties'].items())) + ']', '')]
            return spark.createDataFrame(rows, 'col_name string, data_type string, comment string')
        return _real_sql('DESCRIBE ' + self.rewrite(mm.group(2)))

    # ---------- Python-side writes
    def write_df(self, full, df, mode='append', options=None, partition_by=None):
        options = {k.lower(): str(v).lower() for k, v in (options or {}).items()}
        merge = options.get('mergeschema') == 'true' or self.conf_true('spark.databricks.delta.schema.autoMerge.enabled')
        exists = full in self.tables
        mode = mode or 'errorifexists'
        if not exists:
            self.create(full, df, partition_by=partition_by, label='CREATE TABLE AS SELECT')
            return
        if mode in ('error', 'errorifexists'):
            raise DbxError(f'[TABLE_OR_VIEW_ALREADY_EXISTS] Cannot create table or view {self.quoted(full)} because it already exists.')
        if mode == 'ignore':
            return
        tnames = [f.name for f in self.target_cols(full)]
        if mode == 'overwrite' and options.get('overwriteschema') == 'true':
            self.create(full, df, replace=True, partition_by=partition_by, label='CREATE OR REPLACE TABLE AS SELECT')
            return
        if set(df.columns) - set(tnames) and not merge:
            raise self.schema_mismatch(full, df)
        if not merge:
            df = self.conform(full, df, by_name=True)
        pred = options.get('replacewhere')
        self.append(full, df, mode='overwrite' if mode == 'overwrite' else 'append', merge_schema=merge,
                    predicate=None)
        self.label(full, 'WRITE', {'mode': 'Overwrite' if mode == 'overwrite' else 'Append',
                                   **({'mergeSchema': 'true'} if merge else {})})


def _tn(dt):
    s = dt.simpleString()
    return {'int': 'integer', 'bigint': 'long', 'smallint': 'short', 'tinyint': 'byte'}.get(s, s)


def _delta_type(dt):
    s = dt.simpleString()
    return {'int': 'integer', 'bigint': 'long', 'smallint': 'short', 'tinyint': 'byte'}.get(s, s)


lake = Lake()


# ------------------------------------------------------------------ rendering a SQL statement result
def render_result(res):
    if res is None:
        return ''
    if isinstance(res, tuple):
        if res[0] == 'optimize':
            m = res[2]
            js = json.dumps(m, indent=2)
            return render(['path', 'metrics'], [[res[1], js]], multiline=True)
        if res[0] == 'history':
            return render(['version', 'timestamp', 'operation', 'operationParameters'], [list(r[:4]) for r in res[1]])
        if res[0] == 'vacuum_dry':
            n = len(res[1])
            head = f'Found {n} files (and 0 directories) in a total of 1 directories that are safe to delete.'
            return head + ('\n' + render(['path'], [[p] for p in res[1]]) if n else '')
        if res[0] == 'vacuum':
            return f'Deleted {res[2]} files and directories in a total of 1 directories.\n' + render(['path'], [[res[1]]])
    df = res
    if 'tableFeatures' in df.columns and 'sizeInBytes' in df.columns:
        r = df.collect()[0]
        return render_vertical(df.columns, list(r))
    if df.columns[:3] == ['version', 'timestamp', 'operation']:
        rows = df.select('version', 'timestamp', 'operation', 'operationParameters').collect()
        return render(['version', 'timestamp', 'operation', 'operationParameters'], [list(r) for r in rows])
    return render_df(df)


def first_line(stmt):
    s = ' '.join(l for l in stmt.splitlines() if not l.strip().startswith('--'))
    s = ' '.join(s.split())
    return s if len(s) <= 90 else s[:87] + '...'


PROMPT = 'cdac.bda>'


def run_sql(setup, src, show, expect_error):
    for st in split_sql(setup):
        lake.sql(st)
    blocks = []
    stmts = split_sql(src)
    for i, st in enumerate(stmts):
        kind = ' '.join(st.split()).upper()
        try:
            res = lake.sql(st)
        except Exception as e:
            if not expect_error:
                raise
            blocks.append(f'{PROMPT} {first_line(st)}\n' + err_text(e))
            continue
        k1 = kind.split()[0]
        want = (show == 'all' or (isinstance(show, list) and i in show) or
                (show in ('dml', 'queries') and (k1 in ('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC', 'OPTIMIZE', 'VACUUM', 'RESTORE', 'TABLE', 'EXPLAIN', 'FROM')
                                               or (show == 'dml' and k1 in DML_KINDS) or (kind.startswith('CREATE') and ' AS ' in kind and show == 'dml' and False))))
        if want and res is not None:
            if k1 == 'EXPLAIN':
                txt = res.collect()[0][0]
                blocks.append(f'{PROMPT} {first_line(st)}\n' + shown(clean_plan(txt)))
            else:
                blocks.append(f'{PROMPT} {first_line(st)}\n' + render_result(res))
    return '\n\n'.join(blocks)


def _loc(m):
    first = m.group(1)
    for f, t in lake.tables.items():
        if t['path'] in first:
            return f'Location: PreparedDeltaFileIndex(1 paths)[{t["path"]}]'
    return m.group(0)


def clean_plan(txt):
    txt = re.sub(r'#\d+L?', '', txt)
    txt = re.sub(r'Location: InMemoryFileIndex\(\d+ paths\)\[((?:file:)?/[^,\]]*?)(?:\.\.\.|(?:, (?:file:)?/[^,\]]*)*\])', _loc, txt)
    txt = re.sub(r'file:' + re.escape(LAKE), SHOWN_LAKE, txt)
    txt = re.sub(r'\[plan_id=\d+\]', '', txt)
    return '\n'.join(l.rstrip().rstrip(',') for l in txt.rstrip().splitlines())


NOT_FOUND = ('[TABLE_OR_VIEW_NOT_FOUND] The table or view {name} cannot be found. Verify the spelling and correctness of the schema '
             'and catalog.\nIf you did not qualify the name with a schema, verify the current_schema() output, or qualify the name with '
             'the correct schema and catalog.\nTo tolerate the error on drop use DROP VIEW IF EXISTS or DROP TABLE IF EXISTS. SQLSTATE: 42P01')


def err_text(e):
    if isinstance(e, DbxError):
        return shown(str(e))
    msg = str(e)
    m = re.search(r'\[REQUIRES_SINGLE_PART_NAMESPACE\][^`]*(`[^ ]+`)', msg)
    if m:
        return NOT_FOUND.format(name=m.group(1).rstrip('.'))
    m = re.search(r'\[TABLE_OR_VIEW_NOT_FOUND\] The table or view (`[^ ]+`)', msg)
    if m:
        name = m.group(1)
        parts = name.strip('`').split('`.`')
        if len(parts) == 1:
            name = '`' + '`.`'.join(lake.schema.split('.') + parts) + '`'
        return NOT_FOUND.format(name=shown(name))
    # pyspark errors: keep the first block (error class + message), drop JVM stack traces
    msg = msg.split('\n\nJVM stacktrace')[0].split('\nJVM stacktrace')[0]
    msg = re.split(r'\n\s*at [\w.$]+\(', msg)[0]
    msg = re.sub(r'\s*;\s*\n.*', '', msg, flags=re.S) if 'SQLSTATE' in msg else msg
    return shown(msg.strip())


# ------------------------------------------------------------------ Python notebook shims
class _Writer:
    def __init__(self, df):
        self._df, self._fmt, self._mode, self._opts, self._parts = df, 'delta', None, {}, None
        self._real = DataFrame.__dict__['write'].fget(df) if isinstance(DataFrame.__dict__.get('write'), property) else None

    def format(self, f): self._fmt = f.lower(); return self
    def mode(self, m): self._mode = m.lower(); return self
    def option(self, k, v): self._opts[k] = v; return self
    def options(self, **kw): self._opts.update(kw); return self
    def partitionBy(self, *cols):
        self._parts = [c.lower() for c in (cols[0] if len(cols) == 1 and isinstance(cols[0], (list, tuple)) else cols)]; return self

    def saveAsTable(self, name):
        if self._fmt != 'delta':
            raise DbxError('only Delta tables are supported by the build emulator')
        lake.write_df(lake.full(name), self._df, self._mode, self._opts, self._parts)

    def _realw(self):
        w = _orig_write.fget(self._df).format(self._fmt)
        if self._mode: w = w.mode(self._mode)
        for k, v in self._opts.items(): w = w.option(k, v)
        if self._parts: w = w.partitionBy(*self._parts)
        return w

    def save(self, path=None):
        self._realw().save(real_path(path))

    def json(self, path): self._fmt = 'json'; self.save(path)
    def parquet(self, path): self._fmt = 'parquet'; self.save(path)
    def csv(self, path): self._fmt = 'csv'; self.save(path)


class _StreamWriter:
    def __init__(self, df):
        self._df = df
        self._w = _orig_writeStream.fget(df)
        self._fmt, self._mode, self._fb = 'delta', 'append', None

    def format(self, f):
        self._fmt = f.lower()
        if self._fmt != 'delta': self._w = self._w.format(f)
        return self

    def outputMode(self, m): self._mode = m.lower(); self._w = self._w.outputMode(m); return self
    def option(self, k, v):
        if isinstance(v, str): v = real_path(v)
        self._w = self._w.option(k, v); return self
    def queryName(self, n): self._w = self._w.queryName(n); return self
    def trigger(self, **kw): self._w = self._w.trigger(**kw); return self
    def foreachBatch(self, fn): self._fb = fn; self._w = self._w.foreachBatch(fn); return self

    def toTable(self, name):
        full = lake.full(name)
        mode = self._mode

        def sink(bdf, bid):
            t = norm_arrow(bdf.toArrow())          # scan the micro-batch exactly once
            if t.num_rows == 0:
                return
            bdf = spark.createDataFrame(t, schema=bdf.schema)
            if full not in lake.tables:
                lake.create(full, bdf, label='CREATE TABLE AS SELECT')
                lake.tables[full]['ops'][0] = ('STREAMING UPDATE', {'outputMode': mode.capitalize(), 'epochId': str(bid)})
            else:
                df = lake.conform(full, bdf, by_name=True)
                lake.append(full, df, mode='overwrite' if mode == 'complete' else 'append')
                lake.label(full, 'STREAMING UPDATE', {'outputMode': mode.capitalize(), 'epochId': str(bid)})
        return self._w.foreachBatch(sink).start()

    def start(self, path=None):
        if self._fmt == 'delta' and self._fb is None:
            raise DbxError('path-based Delta streaming sinks are not used on this page')
        return self._w.start(real_path(path)) if path else self._w.start()


from pyspark.sql.classic.dataframe import DataFrame as _CDF
_orig_session = _CDF.__dict__['sparkSession']
_orig_write = _CDF.__dict__['write']
_orig_writeStream = _CDF.__dict__['writeStream']
_CDF.write = property(lambda self: _Writer(self))
_CDF.writeStream = property(lambda self: _StreamWriter(self))


class _ReaderProxy:
    def __init__(self, r, opts=None):
        self._r, self._opts = r, dict(opts or {})

    def option(self, k, v):
        o = dict(self._opts); o[k.lower()] = v
        return _ReaderProxy(self._r.option(k, real_path(v) if isinstance(v, str) else v), o)

    def options(self, **kw):
        out = self
        for k, v in kw.items(): out = out.option(k, v)
        return out

    def table(self, name):
        full = lake.full(name)
        if full not in lake.tables:
            return _real_table(lake.rewrite(name))
        o = self._opts
        if str(o.get('readchangefeed', 'false')).lower() == 'true':
            args = f"'{full}', {int(o.get('startingversion', 0))}" + (f", {int(o['endingversion'])}" if 'endingversion' in o else '')
            return _real_sql(lake.rewrite(f'SELECT * FROM table_changes({args})'))
        if 'versionasof' in o:
            return lake.read(full, int(o['versionasof']))
        if 'timestampasof' in o:
            return lake.read(full, lake.version_for_ts(full, str(o['timestampasof'])))
        return lake.read(full)

    def load(self, path=None, *a, **kw): return self._r.load(real_path(path), *a, **kw) if path else self._r.load(*a, **kw)
    def json(self, path, *a, **kw): return self._r.json(real_path(path), *a, **kw)
    def csv(self, path, *a, **kw): return self._r.csv(real_path(path), *a, **kw)
    def parquet(self, *paths): return self._r.parquet(*[real_path(p) for p in paths])
    def text(self, path, *a, **kw): return self._r.text(real_path(path), *a, **kw)

    def __getattr__(self, k):
        v = getattr(self._r, k)
        if callable(v):
            def wrap(*a, **kw):
                out = v(*a, **kw)
                return _ReaderProxy(out, self._opts) if out.__class__.__name__ in ('DataFrameReader', 'DataStreamReader') else out
            return wrap
        return v


class _SparkProxy:
    def __init__(self, session=None): self._s = session
    def __getattr__(self, k): return getattr(spark, k)
    def sql(self, q, *a, **kw):
        if self._s is not None and self._s is not spark:
            # foreachBatch runs in a cloned session: copy its temp views into the main session
            for t in self._s.catalog.listTables():
                if t.isTemporary and not t.name.startswith('__'):
                    spark.createDataFrame(norm_arrow(self._s.table(t.name).toArrow())).createOrReplaceTempView(t.name)
        r = lake.sql(q)
        if isinstance(r, tuple) and r[0] == 'history':
            return spark.createDataFrame(r[1], 'version bigint, timestamp timestamp, operation string, operationParameters map<string,string>, '
                                               'readVersion bigint, operationMetrics map<string,string>')
        if isinstance(r, tuple):
            raise DbxError('use SQL cells for OPTIMIZE / VACUUM output')
        return r if r is not None else spark.createDataFrame([], 'result string')
    def table(self, name): return _ReaderProxy(spark.read).table(name)
    @property
    def read(self): return _ReaderProxy(spark.read)
    @property
    def readStream(self): return _ReaderProxy(spark.readStream)


class _DeltaMergeBuilder:
    def __init__(self, dtab, source, cond):
        self.d, self.src, self.cond, self.clauses = dtab, source, cond, []
        self.sa = getattr(source, '_upv_alias', 'source')

    def _sets(self, d):
        return ', '.join(f'{k} = {v}' for k, v in d.items())

    def whenMatchedUpdateAll(self, condition=None): self.clauses.append(('MATCHED', condition, 'UPDATE SET *')); return self
    def whenMatchedUpdate(self, condition=None, set=None): self.clauses.append(('MATCHED', condition, 'UPDATE SET ' + self._sets(set))); return self
    def whenMatchedDelete(self, condition=None): self.clauses.append(('MATCHED', condition, 'DELETE')); return self
    def whenNotMatchedInsertAll(self, condition=None): self.clauses.append(('NOT MATCHED', condition, 'INSERT *')); return self
    def whenNotMatchedInsert(self, condition=None, values=None):
        self.clauses.append(('NOT MATCHED', condition, f'INSERT ({", ".join(values)}) VALUES ({", ".join(values.values())})')); return self
    def whenNotMatchedBySourceDelete(self, condition=None): self.clauses.append(('NOT MATCHED BY SOURCE', condition, 'DELETE')); return self
    def whenNotMatchedBySourceUpdate(self, condition=None, set=None):
        self.clauses.append(('NOT MATCHED BY SOURCE', condition, 'UPDATE SET ' + self._sets(set))); return self
    def withSchemaEvolution(self): self.evolve = True; return self

    def execute(self):
        r = lake.do_merge(self.d.full, self.src, self.cond, self.d.alias_, self.sa, self.clauses, (), getattr(self, 'evolve', False))
        return r


class DeltaTable:
    def __init__(self, full): self.full, self.alias_ = full, full.split('.')[-1]
    @classmethod
    def forName(cls, sp, name): lake.dt(lake.full(name)); return cls(lake.full(name))
    def alias(self, a): self.alias_ = a; return self
    def toDF(self): return lake.read(self.full)
    def history(self, limit=None):
        rows = lake.history_rows(self.full, limit)
        return spark.createDataFrame(rows, 'version bigint, timestamp timestamp, operation string, operationParameters map<string,string>, '
                                           'readVersion bigint, operationMetrics map<string,string>')
    def detail(self):
        return spark.createDataFrame([lake.detail_row(self.full)], lake._detail.__code__ and
                                     'format string, id string, name string, location string, createdAt timestamp, lastModified timestamp, '
                                     'partitionColumns array<string>, clusteringColumns array<string>, numFiles bigint, sizeInBytes bigint, '
                                     'properties map<string,string>, minReaderVersion int, minWriterVersion int, tableFeatures array<string>')
    def merge(self, source, condition): return _DeltaMergeBuilder(self, source, condition)
    def restoreToVersion(self, v): return lake.sql(f'RESTORE TABLE {self.full} TO VERSION AS OF {int(v)}')


_CDF.sparkSession = property(lambda self: _SparkProxy(_orig_session.fget(self)))

_orig_explain = _CDF.explain
def _explain(self, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _orig_explain(self, *a, **kw)
    print(clean_plan(buf.getvalue()))
_CDF.explain = _explain

_orig_alias = _CDF.alias
def _alias(self, a):
    out = _orig_alias(self, a); out._upv_alias = a; return out
_CDF.alias = _alias


class _FileInfo(tuple):
    _fields = ('path', 'name', 'size', 'modificationTime')
    def __new__(cls, *a): return tuple.__new__(cls, a)
    path = property(lambda s: s[0]); name = property(lambda s: s[1]); size = property(lambda s: s[2])
    modificationTime = property(lambda s: s[3])
    def __repr__(self): return f"FileInfo(path='{self[0]}', name='{self[1]}', size={self[2]}, modificationTime={self[3]})"


class _Fs:
    def ls(self, path):
        rp = real_path(path).rstrip('/')
        out = []
        for n in sorted(os.listdir(rp)):
            if n.endswith('.crc') or n.startswith('.') or n.startswith('_') and n not in ('_delta_log',) and not n.startswith('_delta'):
                continue
            full = os.path.join(rp, n)
            isdir = os.path.isdir(full)
            shown_p = shown('dbfs:' + full if full.startswith(VOL) else full) + ('/' if isdir else '')
            out.append(_FileInfo(shown_p, n + ('/' if isdir else ''), 0 if isdir else os.path.getsize(full),
                                 int(os.path.getmtime(full) * 1000)))
        return out

    def head(self, path, maxBytes=65536):
        with open(real_path(path), encoding='utf-8') as f:
            return f.read(maxBytes)

    def put(self, path, contents, overwrite=False):
        rp = real_path(path)
        os.makedirs(os.path.dirname(rp), exist_ok=True)
        with open(rp, 'w', encoding='utf-8') as f:
            f.write(contents)
        print(f'Wrote {len(contents.encode())} bytes.')
        return True

    def mkdirs(self, path): os.makedirs(real_path(path), exist_ok=True); return True
    def rm(self, path, recurse=False):
        rp = real_path(path)
        shutil.rmtree(rp) if os.path.isdir(rp) else os.remove(rp); return True


class _Widgets:
    def __init__(self): self.v = {}
    def text(self, name, default='', label=None): self.v.setdefault(name, default)
    def dropdown(self, name, default, choices, label=None): self.v.setdefault(name, default)
    def get(self, name): return self.v[name]


class _TaskValues:
    def __init__(self): self.v = {}
    def set(self, key, value): self.v[key] = value
    def get(self, taskKey, key, default=None, debugValue=None): return self.v.get(key, debugValue if debugValue is not None else default)


class _Jobs:
    def __init__(self): self.taskValues = _TaskValues()


class _DbUtils:
    def __init__(self): self.fs, self.widgets, self.jobs = _Fs(), _Widgets(), _Jobs()


def display(obj):
    if isinstance(obj, list) and obj and isinstance(obj[0], _FileInfo):
        print(render(list(_FileInfo._fields), [list(x) for x in obj]))
        return
    if hasattr(obj, 'isStreaming') and obj.isStreaming:
        raise DbxError('display() of a streaming DataFrame is not used on this page')
    print(render_df(obj))


def run_py(setup, src):
    g = {'__name__': '__main__', 'spark': _SparkProxy(), 'display': display, 'dbutils': _DbUtils(), 'DeltaTable': DeltaTable}
    if setup:
        for st in split_sql(setup):
            lake.sql(st)
    if 'mlflow' in src:
        os.makedirs(MLR, exist_ok=True)
        import mlflow
        mlflow.set_tracking_uri(f'sqlite:///{MLR}/mlflow.db')
        mlflow.set_registry_uri(f'sqlite:///{MLR}/mlflow.db')
    code_ = src.replace("'/Volumes/", f"'{VOL}/").replace('"/Volumes/', f'"{VOL}/').replace("f'/Volumes/", f"f'{VOL}/")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code_, '<cell>', 'exec'), g)
    finally:
        for q in spark.streams.active:
            try: q.stop()
            except Exception: pass
    return shown(buf.getvalue().rstrip('\n'))


def reset():
    for q in spark.streams.active:
        try: q.stop()
        except Exception: pass
    for k in list(lake.confs):
        try:
            if k in DEFAULT_CONF: spark.conf.set(k, DEFAULT_CONF[k])
            else: spark.conf.unset(k)
        except Exception:
            pass
    for k in ('spark.sql.shuffle.partitions', 'spark.sql.adaptive.enabled', 'spark.sql.autoBroadcastJoinThreshold'):
        try: spark.conf.unset(k)
        except Exception: pass
    lake.reset()
    for d in (MLR, BASE + '/mlartifacts', BASE + '/mlruns'):
        shutil.rmtree(d, ignore_errors=True)
    os.chdir(BASE)


def write_files(files):
    for rel, content in (files or {}).items():
        p = real_path(rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(textwrap.dedent(content).lstrip('\n'))


def handle(req):
    reset()
    write_files(req.get('files'))
    if req['kind'] == 'sql':
        return run_sql(req.get('setup', ''), req['src'], req.get('show', 'dml'), req.get('expect_error', False))
    return run_py(req.get('setup', ''), req['src'])


if __name__ == '__main__':
    real_stdout = sys.stdout
    sys.stdout = sys.stderr
    print(json.dumps({'ready': True}), file=real_stdout, flush=True)
    for line in sys.stdin:
        req = json.loads(line)
        try:
            out = handle(req)
            res = {'output': out}
        except Exception as e:
            res = {'error': f'{type(e).__name__}: {e}', 'trace': traceback.format_exc()[-3000:]}
        print(json.dumps(res), file=real_stdout, flush=True)
