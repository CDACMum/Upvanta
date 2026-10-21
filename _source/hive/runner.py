"""HiveQL examples are executed at build time on Spark SQL with Hive support
(PySpark 4.2, Hive metastore/SerDe 2.3) and the results cached in _hivecache/.
While an example is unchanged, the build uses the cache and needs no Spark install.
To re-run edited examples set HIVE_PY to a Python that has pyspark installed
(default /home/claude/sparkenv/bin/python)."""
import hashlib, json, os, pathlib, subprocess, textwrap
from build import code, output

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / '_hivecache'
_proc = [None]


def _worker():
    if _proc[0] is None:
        py = os.environ.get('HIVE_PY', '/home/claude/sparkenv/bin/python')
        _proc[0] = subprocess.Popen([py, str(pathlib.Path(__file__).parent / 'hive_worker.py')],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        while True:
            line = _proc[0].stdout.readline()
            if not line:
                raise RuntimeError('Hive worker failed to start')
            if line.startswith('{') and json.loads(line).get('ready'):
                break
    return _proc[0]


def _run(req):
    key = hashlib.sha1(json.dumps(req, sort_keys=True).encode()).hexdigest()[:16]
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f'{key}.json'
    if f.exists():
        return json.loads(f.read_text())
    p = _worker()
    p.stdin.write(json.dumps(req) + '\n'); p.stdin.flush()
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError('Hive worker died')
        if line.startswith('{'):
            res = json.loads(line); break
    if 'error' in res:
        raise RuntimeError(f"HiveQL example failed: {res['error']}\n--- {res.get('stmt', '')}\n{req['sql']}")
    f.write_text(json.dumps(res))
    return res


def hql(src, setup='', files=None, title='HiveQL', expect_error=False, show_output=True):
    """HiveQL block + real output. setup: statements run first but not shown.
    files: {relative path under /data/: content} written before the run."""
    src = textwrap.dedent(src).strip('\n')
    res = _run({'sql': src, 'setup': textwrap.dedent(setup), 'files': files or {}, 'expect_error': expect_error})
    out = res['output']
    return code(src, title, 'fa-database') + (output(out) if out and show_output else '')


def hq(src, title='HiveQL'):
    """HiveQL shown without running (Hive-only features such as ACID, Tez settings)."""
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-database')


def datafile(path, content):
    """Show a raw data file that an example loads."""
    return code(textwrap.dedent(content).strip('\n'), path, 'fa-file-lines')


def sh(src, title='Shell'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')
