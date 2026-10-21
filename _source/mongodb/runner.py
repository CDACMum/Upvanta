"""MongoDB examples are executed at build time by mongo_shell.js: a mongosh-like shell whose
queries, updates and aggregation pipelines are evaluated by mingo (a JavaScript implementation
of the MongoDB Query Language). Results are cached in _mongocache/, so rebuilding an unchanged
module needs no Node.js. To re-run edited examples you need Node.js and `npm install mingo@6 acorn@8`
in a folder whose node_modules path is given by MINGO_DIR (default: mongodb/node_modules)."""
import hashlib, json, os, pathlib, subprocess, textwrap
from build import code, output

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE.parent / '_mongocache'


def _run(setup, src):
    req = {'setup': setup, 'code': src}
    key = hashlib.sha1(json.dumps(req, sort_keys=True).encode()).hexdigest()[:16]
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f'{key}.json'
    if f.exists():
        return json.loads(f.read_text())['output']
    env = dict(os.environ)
    env.setdefault('MINGO_DIR', str(HERE / 'node_modules'))
    r = subprocess.run(['node', str(HERE / 'mongo_shell.js')], input=json.dumps(req), capture_output=True, text=True, timeout=60, env=env)
    res = json.loads(r.stdout or '{"error": %s}' % json.dumps(r.stderr))
    if 'error' in res:
        raise RuntimeError(f"MongoDB example failed: {res['error']}\n---\n{src}")
    f.write_text(json.dumps(res))
    return res['output']


def mql(src, setup='', title='mongosh', show_output=True):
    """mongosh block + real output. setup: statements run first but not shown."""
    src = textwrap.dedent(src).strip('\n')
    out = _run(textwrap.dedent(setup), src)
    return code(src, title, 'fa-leaf') + (output(out) if out and show_output else '')


def mq(src, title='mongosh'):
    """Shown without running (needs a real server: explain, replication, sharding, transactions)."""
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-leaf')


def sh(src, title='Shell'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')


def js(src, title):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-brands fa-js')
