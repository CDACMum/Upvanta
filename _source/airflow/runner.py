"""Run example DAGs on a real Airflow install and turn the noisy log into a short transcript.

Needs:  AF_PY   = python of a virtualenv with apache-airflow installed
        AF_HOME = an AIRFLOW_HOME where `airflow db migrate` has been run
Results are cached in _afcache/ keyed by the DAG source, so rebuilding is fast.
"""
import hashlib, json, os, pathlib, re, shutil, subprocess, textwrap
from build import code, output, esc

AF_BIN = os.environ.get('AF_BIN', '/home/claude/af/bin')
AF_HOME = os.environ.get('AF_HOME', '/home/claude/afhome')
CACHE = pathlib.Path(__file__).parent.parent / '_afcache'
ENV = dict(os.environ, AIRFLOW_HOME=AF_HOME, AIRFLOW__CORE__LOAD_EXAMPLES='False',
           PYTHONWARNINGS='ignore', AIRFLOW__LOGGING__LOGGING_LEVEL='INFO')

def _cached(key, fn):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (hashlib.sha1(key.encode()).hexdigest() + '.json')
    if f.exists():
        return json.loads(f.read_text())
    res = fn()
    f.write_text(json.dumps(res))
    return res

def _fresh_dags_folder(src, name):
    """src: one DAG file's source, or a dict {file_name: source} for several files."""
    d = pathlib.Path(AF_HOME) / 'dags'
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    files = src if isinstance(src, dict) else {name: src}
    for n, code_ in files.items():
        (d / f'{n}.py').write_text(textwrap.dedent(code_).strip('\n') + '\n')

TS = re.compile(r'^\d{4}-\d\d-\d\dT[\d:.]+Z \[(\w+)\s*\] (.*)$')

def condense(raw):
    """Keep what a student needs: task start/end, printed output, returns, states, errors."""
    out = []
    for line in raw.splitlines():
        m = TS.match(line)
        if not m:
            s = line.rstrip()
            if s and not s.startswith(('Traceback', '  File', '    ', 'DeprecationWarning')):
                out.append('   ' + s)          # print() output from task code
            continue
        lvl, msg = m.groups()
        full = msg
        msg = re.sub(r'\s+\[[\w.]+\]\s+loc=\S+.*$', '', msg).strip()
        if 'SubprocessHook' in full:                       # BashOperator: rendered command and its output
            if msg.startswith('Running command:'):
                cmd = re.search(r"'-c', (['\"])(.*)\1\]$", msg)
                out.append('   $ ' + (cmd.group(2) if cmd else msg))
            elif 'loc=subprocess.py:99' in full:
                out.append('   ' + msg)
            continue
        if '.unusual_prefix_' in full and lvl == 'info':     # self.log calls from classes defined in the DAG file
            out.append('   log: ' + msg[:200])
            continue
        if msg.startswith('Running statement:'):
            stmt = re.sub(r', parameters: .*$', '', msg[len('Running statement:'):]).strip()
            out.append('   running SQL: ' + (stmt if len(stmt) <= 110 else stmt[:107] + '…'))
            continue
        if msg.startswith('[DAG TEST] starting task_id='):
            t = re.search(r'task_id=(\S+) map_index=(-?\d+)', msg)
            mi = '' if t.group(2) == '-1' else f'[{t.group(2)}]'
            out.append(f'▶ {t.group(1)}{mi}')
        elif msg.startswith('Done. Returned value was:'):
            out.append('   returned: ' + msg.split(':', 1)[1].strip())
        elif 'Task instance state updated' in line and 'new_state=' in line:
            st = re.search(r'new_state=(\w+)', line).group(1)
            out.append(f'   state: {st}')
        elif msg.startswith('DagRun Finished'):
            st = re.search(r'state=(\w+)', msg).group(1)
            di = re.search(r'data_interval_start=([^,]+), data_interval_end=([^,]+),', msg)
            out.append(f'DAG run finished: {st}')
            if di:
                out.append(f'   data interval: {di.group(1)}  →  {di.group(2)}')
        elif lvl in ('error', 'critical'):
            if 'XCom not found' in msg and 'offset=' in full:
                continue        # internal probe past the end of a mapped-results list (harmless)
            out.append('   ERROR: ' + msg[:220])
        elif msg.startswith(('Following branch', 'Skipping tasks [', 'Poking for', 'Success criteria met',
                             'Rescheduling task')):
            out.append('   ' + msg[:160])
        elif msg.startswith('[DAG TEST] running trigger in line'):
            out.append('   ⏳ trigger running (in the triggerer, no worker slot used)')
        elif msg == 'trigger starting':
            cls = re.search(r'\[[\w.]*\.(\w+Trigger)\]', full)
            out.append(f'   trigger started: {cls.group(1) if cls else "trigger"}')
    # collapse duplicate consecutive lines
    res = []
    for l in out:
        if not res or res[-1] != l:
            res.append(l)
    return '\n'.join(res)

def dagtest(src, dag_id, date=None, title='DAG (Airflow 3)', name=None, keep=None, show_states=True, conf=None, env=None):
    """Code block + condensed log of `airflow dags test` on a real Airflow install."""
    src = textwrap.dedent(src).strip('\n') + '\n'
    args = [f'{AF_BIN}/airflow', 'dags', 'test', dag_id] + ([date] if date else []) + (['-c', json.dumps(conf)] if conf else [])
    def run():
        _fresh_dags_folder(src, name or dag_id)
        r = subprocess.run(args, capture_output=True, text=True, env=dict(ENV, **(env or {})), cwd='/tmp', timeout=600)
        raw = r.stdout + r.stderr
        states = ''
        m = re.search(r'run_id=(manual__\S+?)[ ,]', raw)
        if m:
            s2 = subprocess.run([f'{AF_BIN}/airflow', 'tasks', 'states-for-dag-run', dag_id, m.group(1), '-o', 'plain'],
                                capture_output=True, text=True, env=ENV, cwd='/tmp', timeout=300)
            rows = sorted((l.split() for l in s2.stdout.splitlines() if l.startswith(dag_id + ' ')), key=lambda r: r[4])
            states = [(r[2] + (f'[{r[-1]}]' if r[-1].isdigit() and len(r) == 7 else ''), r[3]) for r in rows]
        return dict(raw=raw, rc=r.returncode, states=states)
    res = _cached('dagtest|' + ' '.join(args[3:]) + '|' + json.dumps(env or {}) + '|' + src, run)
    log = condense(res['raw'])
    if 'DAG run finished' not in log:
        raise RuntimeError(f'DAG {dag_id} did not finish:\n{res["raw"][-3000:]}')
    if keep:
        log = '\n'.join(l for l in log.splitlines() if keep(l))
    if show_states and res.get('states'):
        w = max(len(t) for t, _ in res['states'])
        log += '\n\nFinal task states:\n' + '\n'.join(f'   {t.ljust(w)}  {st}' for t, st in res['states'])
    return code(src.rstrip('\n'), title, 'fa-brands fa-python') + output(log, 'Run log: airflow dags test (condensed)')

def _exe(c):
    if c.startswith('airflow '):
        return f'{AF_BIN}/airflow ' + c[len('airflow '):]
    if c.startswith('pytest '):
        return f'cd /tmp/aftests && {AF_BIN}/python -m pytest ' + c[len('pytest '):]
    return c

def afcli(cmd_lines, src=None, name='example_dag', title='Shell', setup_cmds=(), files=None):
    """files: {path: content} written before running (e.g. a pytest file under /tmp/aftests)."""
    """Run airflow CLI commands for real (optionally with a DAG file in place) and show their output."""
    def run():
        if src is not None:
            _fresh_dags_folder(src, name)
        for p_, content in (files or {}).items():
            pathlib.Path(p_).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(p_).write_text(textwrap.dedent(content).strip('\n') + '\n')
        for c in setup_cmds:
            r0 = subprocess.run(_exe(c), shell=True, capture_output=True, text=True,
                                env=ENV, cwd='/tmp', timeout=600)
            if r0.returncode != 0:
                raise RuntimeError(f'setup command failed: {c}\n{r0.stderr[-2000:]}')
        outs = []
        for c in cmd_lines:
            r = subprocess.run(_exe(c), shell=True, capture_output=True, text=True,
                               env=ENV, cwd='/tmp', timeout=600)
            body = '\n'.join(l for l in (r.stdout + r.stderr).splitlines()
                             if not TS.match(l) and 'Warning' not in l and l.strip())
            outs.append(f'$ {c}\n{body}')
        return dict(out='\n\n'.join(outs))
    res = _cached('afcli|' + '|'.join(cmd_lines) + '|' + json.dumps(src) + '|' + '|'.join(setup_cmds) + json.dumps(files), run)
    return code('\n'.join(cmd_lines), title, 'fa-terminal') + output(res['out'])

def afpy(src, title='Python (Airflow 3)', expect_error=False):
    """Run a Python snippet in the Airflow virtualenv (e.g. parse a DAG and inspect it) and show its output."""
    src = textwrap.dedent(src).strip('\n')
    def run():
        r = subprocess.run([f'{AF_BIN}/python', '-c', src], capture_output=True, text=True, env=ENV, cwd='/tmp', timeout=300)
        out = '\n'.join(l for l in r.stdout.splitlines() if not TS.match(l))
        err = r.stderr.strip().splitlines()
        return dict(out=out, rc=r.returncode, last=err[-1] if err else '')
    res = _cached('afpy|' + src, run)
    out = res['out']
    if res['rc'] != 0:
        if not expect_error:
            raise RuntimeError(f'afpy failed: {res["last"]}\n{src}')
        out = (out + '\n' if out else '') + res['last']
    return code(src, title, 'fa-brands fa-python') + (output(out) if out else '')
