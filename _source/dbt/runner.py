"""dbt examples are executed for real at build time with dbt-core + dbt-duckdb in a fresh
project per example; console output is cached in _dbtcache/ so rebuilding an unchanged module
needs no dbt install. To re-run edited examples set DBT_BIN to the folder containing the dbt
executable (default /home/claude/dbtenv/bin)."""
import hashlib, json, os, pathlib, re, shutil, subprocess, tempfile, textwrap
from build import code, output, esc
from dbt.seeds import SEEDS

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE.parent / '_dbtcache'
_PENDING = {}

BASE = {
    'dbt_project.yml': """name: cdac_dw
version: '1.0'
profile: cdac
seeds:
  cdac_dw:
    +schema: raw
""",
}
LANG = {'.sql': ('SQL / Jinja', 'fa-database'), '.yml': ('YAML', 'fa-file-code'), '.csv': ('CSV', 'fa-file-csv'), '.md': ('Markdown', 'fa-file-lines')}


def dfile(path, content, show=True):
    """Register a project file for the next dbtrun() and show it as a code block."""
    content = textwrap.dedent(content).strip('\n') + '\n'
    _PENDING[path] = content
    if not show:
        return ''
    ext = pathlib.Path(path).suffix
    return code(content, path, LANG.get(ext, ('', 'fa-file'))[1])


def _clean(text):
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    out = []
    for ln in text.splitlines():
        ln = re.sub(r'^\d{2}:\d{2}:\d{2}\s{1,2}', '', ln).rstrip()
        if 'anonymous usage' in ln.lower() or ln.startswith('Registered adapter') or 'Unable to do partial parsing' in ln:
            continue
        out.append(ln)
    s = '\n'.join(out)
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = re.sub(r'(?m)^\s*$\n(?=Concurrency)', '', s)
    return s.strip('\n')


def _run(files, cmds, allow_fail):
    req = {'files': files, 'cmds': cmds}
    key = hashlib.sha1(json.dumps(req, sort_keys=True).encode()).hexdigest()[:16]
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f'{key}.json'
    if f.exists():
        return json.loads(f.read_text())['output']
    work = pathlib.Path(tempfile.mkdtemp(prefix='upv_dbt_')) / 'cdac_dw'
    work.mkdir(parents=True)
    allfiles = dict(BASE); allfiles.update(SEEDS); allfiles.update(files)
    for p, c in allfiles.items():
        fp = work / p; fp.parent.mkdir(parents=True, exist_ok=True); fp.write_text(c)
    (work / 'profiles.yml').write_text(
        "cdac:\n  target: dev\n  outputs:\n    dev:\n      type: duckdb\n      path: cdac.duckdb\n      schema: dev\n      threads: 1\n"
        "    prod:\n      type: duckdb\n      path: cdac.duckdb\n      schema: prod\n      threads: 4\n")
    env = dict(os.environ, DBT_PROFILES_DIR=str(work), DBT_SEND_ANONYMOUS_USAGE_STATS='false', DBT_USE_COLORS='false',
               DBT_PRINTER_WIDTH='100', TZ='Asia/Kolkata', DO_NOT_TRACK='1')
    binp = os.environ.get('DBT_BIN', '/home/claude/dbtenv/bin')
    env['PATH'] = binp + ':' + env.get('PATH', '')
    blocks = []
    for c in cmds:
        hidden = c.startswith('!')
        cmd = c.lstrip('!')
        r = subprocess.run(['bash', '-c', cmd], cwd=work, env=env, capture_output=True, text=True, timeout=300)
        txt = _clean(r.stdout + r.stderr).replace(str(work), '~/cdac_dw')
        if r.returncode != 0 and not allow_fail and not hidden:
            raise RuntimeError(f'dbt example failed: {cmd}\n{txt}')
        if r.returncode != 0 and hidden:
            raise RuntimeError(f'dbt setup command failed: {cmd}\n{txt}')
        if not hidden:
            blocks.append(f'$ {cmd}\n{txt}')
    if not os.environ.get("DBT_KEEP_TMP"): shutil.rmtree(work.parent, ignore_errors=True)
    out = '\n\n'.join(blocks)
    f.write_text(json.dumps({'output': out}))
    return out


def dbtrun(*cmds, extra=None, allow_fail=False, title='Terminal'):
    """Run dbt commands on a fresh project made of the seeds + files registered with dfile() (+ extra hidden files).
    Commands starting with '!' run silently (setup)."""
    files = dict(_PENDING); files.update({k: textwrap.dedent(v).strip('\n') + '\n' for k, v in (extra or {}).items()})
    _PENDING.clear()
    out = _run(files, list(cmds), allow_fail)
    shown = [c for c in cmds if not c.startswith('!')]
    return code('\n'.join(shown), title, 'fa-terminal') + output(out)


def yml(src, title):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-file-code')


def sqlc(src, title='SQL / Jinja'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-database')


def sh(src, title='Terminal'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')
