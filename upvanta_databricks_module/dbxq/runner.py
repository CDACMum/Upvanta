"""Runs the Databricks examples at build time and caches the results in _dbxcache/.

Databricks is a cloud service, so the examples run locally in dbx_worker.py on Apache Spark 4.2 (PySpark) plus
delta-rs (the Rust implementation of the Delta Lake protocol) for every Delta table operation, and MLflow 3.
Output is printed in notebook style (one result table per statement).
While an example is unchanged the build uses the cache and needs no Spark, Java or delta-rs.
To re-run edited examples set DBX_PY to a Python that has pyspark 4.2, deltalake, mlflow and scikit-learn
(default /home/claude/dbx/bin/python); Java 17+ must be available.

Rules the examples follow so the local run matches Databricks:
  * Delta tables use the three-level names cdac.bda.<table> (current schema cdac.bda);
  * features that need a workspace (clusters, jobs, Unity Catalog grants, Auto Loader, Lakeflow pipelines,
    Photon, serverless, model serving) use sq()/py() and are shown without output.
"""
import hashlib, json, os, pathlib, subprocess, textwrap
from build import code, output

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / '_dbxcache'
_proc = [None]

STUDENTS = """
CREATE OR REPLACE TABLE students (
  roll_no  INT,
  name     STRING,
  course   STRING,
  centre   STRING,
  marks    DECIMAL(5,2),
  joined   DATE
);
INSERT INTO students VALUES
  (2401, 'Anuj',    'PGCP-BDA', 'Kharghar', 78.50, DATE'2026-02-02'),
  (2402, 'Aarshvi', 'PGCP-BDA', 'Juhu',     88.00, DATE'2026-02-02'),
  (2403, 'Riya',    'PGCP-AI',  'Kharghar', 91.25, DATE'2026-02-03'),
  (2404, 'Kabir',   'PGCP-AC',  'Kharghar', 67.00, DATE'2026-02-03'),
  (2405, 'Sana',    'PGCP-BDA', 'Kharghar', 93.75, DATE'2026-02-04'),
  (2406, 'Omkar',   'PGCP-AI',  'Juhu',     72.50, DATE'2026-02-04'),
  (2407, 'Meera',   'PGCP-AC',  'Juhu',     84.00, DATE'2026-02-05'),
  (2408, 'Tejas',   'PGCP-BDA', 'Juhu',     59.25, DATE'2026-02-05');
"""


def _worker():
    if _proc[0] is None:
        py = os.environ.get('DBX_PY', '/home/claude/dbx/bin/python')
        _proc[0] = subprocess.Popen([py, '-I', str(pathlib.Path(__file__).parent / 'dbx_worker.py')],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        while True:
            line = _proc[0].stdout.readline()
            if not line:
                raise RuntimeError('Databricks worker failed to start (set DBX_PY)')
            if line.startswith('{') and json.loads(line).get('ready'):
                break
    return _proc[0]


def _run(req):
    key = hashlib.sha1(json.dumps(req, sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f'{key}.json'
    if f.exists() and not os.environ.get('DBX_REFRESH'):
        return json.loads(f.read_text(encoding='utf-8'))['output']
    p = _worker()
    p.stdin.write(json.dumps(req) + '\n'); p.stdin.flush()
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError('Databricks worker died')
        if line.startswith('{'):
            res = json.loads(line); break
    if 'error' in res:
        raise RuntimeError(f"Databricks example failed: {res['error']}\n{res.get('trace', '')}\n---\n{req['src']}")
    CACHE.mkdir(exist_ok=True)
    f.write_text(json.dumps({'input': req, 'output': res['output']}, indent=1, ensure_ascii=False), encoding='utf-8')
    return res['output']


def sql(src, setup='', title='Databricks SQL', show='dml', data=True, files=None, expect_error=False):
    """SQL cell + real output. show = 'queries' | 'dml' (default) | 'all' | list of statement indexes."""
    src = textwrap.dedent(src).strip('\n')
    pre = (STUDENTS if data else '') + textwrap.dedent(setup)
    out = _run({'kind': 'sql', 'setup': pre, 'src': src, 'show': show if isinstance(show, str) else list(show),
                'files': files or {}, 'expect_error': expect_error})
    return code(src, title, 'fa-database') + (output(out) if out else '')


def pyrun(src, setup='', title='Python (PySpark notebook cell)', data=True, files=None):
    """Python notebook cell (spark, display, dbutils, DeltaTable available) + its real printed output."""
    src = textwrap.dedent(src).strip('\n')
    pre = (STUDENTS if data else '') + textwrap.dedent(setup)
    out = _run({'kind': 'py', 'setup': pre, 'src': src, 'files': files or {}})
    return code(src, title, 'fa-brands fa-python') + (output(out) if out else '')


def sq(src, title='Databricks SQL (shown, not executed)'):
    """SQL that needs a real workspace (Unity Catalog grants, Lakeflow, Auto Loader, liquid clustering ...)."""
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-database')


def py(src, title='Python (shown, not executed)'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-brands fa-python')


def sh(src, title='Shell'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')


def conf(src, title='Configuration'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-gear')


def datafile(path, content):
    return code(textwrap.dedent(content).strip('\n'), path, 'fa-file-lines')
