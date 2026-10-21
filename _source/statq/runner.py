"""Runs statistics examples (NumPy, pandas, SciPy, statsmodels) for real and caches the printed output in _statcache/.

strun(src, setup=...)  -> code block + output box.
  setup : shared sample-data code run before src (hidden, shown once per section in DATA_NOTE).
While src/setup are unchanged, the cache is used and SciPy/statsmodels are not needed.
To re-run edited examples set STAT_PY to a Python that has NumPy, pandas, SciPy and statsmodels installed.
"""
import hashlib, json, os, pathlib, subprocess, textwrap, tempfile
from build import code, output

CACHE = pathlib.Path(__file__).resolve().parent.parent / '_statcache'
PY = os.environ.get('STAT_PY', 'python3')

PRELUDE = """
import warnings
def _show(message, category, filename, lineno, file=None, line=None):
    print(f'{category.__name__}: {str(message).splitlines()[0]}')
warnings.showwarning = _show
import numpy as np, pandas as pd
np.set_printoptions(linewidth=100, suppress=True, precision=4)
pd.set_option('display.width', 110)
pd.set_option('display.max_columns', 20)
"""


def _clean(src):
    return textwrap.dedent(src).strip('\n')


def run(src, setup='', expect_error=False, files=None):
    src, setup = _clean(src), _clean(setup)
    key = hashlib.sha256(json.dumps([PRELUDE, setup, src, files or {}], sort_keys=True).encode()).hexdigest()[:16]
    cf = CACHE / f'{key}.json'
    if cf.exists():
        return json.loads(cf.read_text())['out']
    work = pathlib.Path(tempfile.mkdtemp(prefix='upv_st_'))
    for name, content in (files or {}).items():
        (work / name).write_text(_clean(content) + '\n')
    script = PRELUDE + '\n' + setup + '\n' + src + '\n'
    r = subprocess.run([PY, '-I', '-c', script], capture_output=True, text=True, timeout=180, cwd=work)
    out = r.stdout.rstrip('\n')
    if r.returncode != 0:
        last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'error'
        if not expect_error:
            raise RuntimeError(f'statistics example failed: {last}\n---\n{r.stderr[-2500:]}\n---\n{src}')
        out = (out + '\n' if out else '') + last
    CACHE.mkdir(exist_ok=True)
    cf.write_text(json.dumps({'src': src, 'out': out}, indent=1))
    return out


def strun(src, setup='', title='Python (SciPy)', expect_error=False, files=None, out_title='Output'):
    out = run(src, setup, expect_error, files)
    return code(_clean(src), title, 'fa-brands fa-python') + (output(out, out_title) if out else '')


def pyshow(src, title='Python (SciPy)'):
    """Code shown, not executed."""
    return code(_clean(src), title, 'fa-brands fa-python')
