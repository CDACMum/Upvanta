"""Runs NumPy examples for real and caches the printed output in _npcache/.

pdrun(src, setup=...)  -> code block + output box.
  setup : shared sample-data code run before src (hidden, shown once per section in DATA_NOTE).
While src/setup are unchanged, the cache is used and NumPy is not needed.
To re-run edited examples set NP_PY to a Python that has NumPy 2 installed.
"""
import hashlib, json, os, pathlib, subprocess, textwrap, tempfile
from build import code, output

CACHE = pathlib.Path(__file__).resolve().parent.parent / '_npcache'
PY = os.environ.get('NP_PY', 'python3')

PRELUDE = """
import warnings
def _show(message, category, filename, lineno, file=None, line=None):
    print(f'{category.__name__}: {str(message).splitlines()[0]}')
warnings.showwarning = _show
import numpy as np
np.set_printoptions(linewidth=100)
"""


def _clean(src):
    return textwrap.dedent(src).strip('\n')


def run(src, setup='', expect_error=False, files=None):
    src, setup = _clean(src), _clean(setup)
    key = hashlib.sha256(json.dumps([PRELUDE, setup, src, files or {}], sort_keys=True).encode()).hexdigest()[:16]
    cf = CACHE / f'{key}.json'
    if cf.exists():
        return json.loads(cf.read_text())['out']
    work = pathlib.Path(tempfile.mkdtemp(prefix='upv_np_'))
    for name, content in (files or {}).items():
        (work / name).write_text(_clean(content) + '\n')
    script = PRELUDE + '\n' + setup + '\n' + src + '\n'
    r = subprocess.run([PY, '-I', '-c', script], capture_output=True, text=True, timeout=180, cwd=work)
    out = r.stdout.rstrip('\n')
    if r.returncode != 0:
        last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'error'
        if not expect_error:
            raise RuntimeError(f'NumPy example failed: {last}\n---\n{r.stderr[-2500:]}\n---\n{src}')
        out = (out + '\n' if out else '') + last
    CACHE.mkdir(exist_ok=True)
    cf.write_text(json.dumps({'src': src, 'out': out}, indent=1))
    return out


def nprun(src, setup='', title='Python (NumPy)', expect_error=False, files=None, out_title='Output'):
    out = run(src, setup, expect_error, files)
    return code(_clean(src), title, 'fa-brands fa-python') + (output(out, out_title) if out else '')


def pyshow(src, title='Python (NumPy)'):
    """Code shown, not executed."""
    return code(_clean(src), title, 'fa-brands fa-python')
