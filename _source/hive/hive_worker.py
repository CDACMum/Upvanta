"""Persistent Spark SQL (Hive support) worker used by runner.py at build time.
Reads one JSON request per line on stdin, writes one JSON reply per line on stdout."""
import json, os, re, shutil, sys, io, contextlib, time
os.environ['TZ'] = 'Asia/Kolkata'; time.tzset()

WH, DATA, MS = '/tmp/upv_hive/wh', '/tmp/upv_hive/data', '/tmp/upv_hive/ms'
os.makedirs('/tmp/upv_hive', exist_ok=True)
os.chdir('/tmp/upv_hive')
from pyspark.sql import SparkSession
spark = (SparkSession.builder.master('local[2]').appName('upvanta-hive')
         .config('spark.sql.warehouse.dir', WH)
         .config('spark.ui.enabled', 'false')
         .config('spark.sql.shuffle.partitions', '4')
         .config('spark.sql.adaptive.enabled', 'false')
         .config('spark.sql.session.timeZone', 'Asia/Kolkata')
         .config('spark.hadoop.javax.jdo.option.ConnectionURL', f'jdbc:derby:;databaseName={MS};create=true')
         .enableHiveSupport().getOrCreate())
spark.sparkContext.setLogLevel('OFF')

def to_real(s):
    return re.sub(r"(?<=['\s])/data/", DATA + "/", s)

UUID = re.compile(r'-([0-9a-f]{8})-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
def to_shown(s):
    s = s.replace(f'file:{WH}', '/user/hive/warehouse').replace(WH, '/user/hive/warehouse')
    s = s.replace(f'file:{DATA}', '/data').replace(DATA, '/data')
    return UUID.sub(r'-\1…', s)

def fmt(v):
    if v is None: return 'NULL'
    if isinstance(v, bool): return str(v).lower()
    if isinstance(v, float): return repr(v)
    if isinstance(v, (list, dict)) or hasattr(v, 'asDict'):
        return json.dumps(conv(v), ensure_ascii=False, separators=(',', ':'))
    return str(v)

def conv(v):
    if hasattr(v, 'asDict'): return {k: conv(x) for k, x in v.asDict().items()}
    if isinstance(v, dict): return {str(k): conv(x) for k, x in v.items()}
    if isinstance(v, list): return [conv(x) for x in v]
    return v

def table(cols, rows):
    data = [[to_shown(fmt(c)) for c in r] for r in rows]
    w = [max([len(c)] + [len(r[i]) for r in data]) for i, c in enumerate(cols)]
    line = '+' + '+'.join('-' * (x + 2) for x in w) + '+'
    out = [line, '| ' + ' | '.join(c.ljust(w[i]) for i, c in enumerate(cols)) + ' |', line]
    out += ['| ' + ' | '.join(r[i].ljust(w[i]) for i in range(len(cols))) + ' |' for r in data]
    out.append(line)
    return '\n'.join(out)

def tree(path):
    real = to_real(" " + path)[1:]
    if path.startswith('/user/hive/warehouse'):
        real = path.replace('/user/hive/warehouse', WH)
    lines = []
    for root, dirs, files in os.walk(real):
        dirs.sort()
        for f in sorted(files):
            if f.endswith('.crc') or f == '_SUCCESS' or f.startswith('.'):
                continue
            p = os.path.join(root, f)
            lines.append(f'{os.path.getsize(p):>7}  {to_shown(p)}')
    return '\n'.join(lines) or '(empty)'

def _strip_comment(line):
    i = line.find('--')
    while i != -1:
        if line[:i].count("'") % 2 == 0:
            return line[:i].rstrip()
        i = line.find('--', i + 2)
    return line

def split(sql):
    sql = '\n'.join(_strip_comment(l) for l in sql.split('\n'))
    return [s.strip() for s in re.split(r';\s*(?:\n|$)', sql) if s.strip()]

def run(req):
    spark.sql('USE default')
    for (name,) in spark.sql('SHOW DATABASES').collect():
        if name != 'default':
            spark.sql(f'DROP DATABASE IF EXISTS {name} CASCADE')
    for r in spark.sql('SHOW TABLES IN default').collect():
        spark.sql(f'DROP TABLE IF EXISTS default.{r.tableName}')
    shutil.rmtree(DATA, ignore_errors=True)
    spark.sql('SET hive.exec.dynamic.partition.mode=nonstrict')
    spark.sql('CREATE DATABASE cdac'); spark.sql('USE cdac')
    for rel, content in (req.get('files') or {}).items():
        p = os.path.join(DATA, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w').write(content)
    for st in split(req.get('setup', '')):
        spark.sql(to_real(st)).collect()
    outs = []
    for st in split(req['sql']):
        m = re.match(r'(?is)^dfs\s+-ls\s+-R\s+(\S+)$', st)
        if m:
            outs.append(tree(m.group(1))); continue
        try:
            df = spark.sql(to_real(st))
            if re.match(r'(?is)^(set\s+\S+\s*=|create|drop|insert|load|alter|msck|use|truncate|analyze|cache|refresh)', st) \
                    or re.match(r'(?is)^from\s.*\binsert\b', st):
                df.collect(); continue
            rows = df.collect()
            if not df.columns:
                continue
            if df.columns == ['plan']:
                outs.append('\n'.join(r[0].rstrip() for r in rows)); continue
            outs.append(table(df.columns, rows))
        except Exception as e:
            msg = str(e).strip().split('\n')[0]
            msg = re.sub(r'\s*SQLSTATE: \w+', '', msg)
            if not req.get('expect_error'):
                return {'error': msg, 'stmt': st}
            outs.append('Error: ' + to_shown(msg))
    return {'output': to_shown('\n\n'.join(outs))}

print(json.dumps({'ready': True}), flush=True)
for line in sys.stdin:
    req = json.loads(line)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            res = run(req)
    except Exception as e:
        res = {'error': repr(e)[:2000]}
    print(json.dumps(res), flush=True)
