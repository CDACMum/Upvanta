"""Runs Matplotlib / Seaborn examples for real and caches the printed output AND the figures in _vizcache/.

vizrun(src, setup=...) -> code block + text output (if any) + the real chart images.
  setup : shared sample-data code run before src (hidden; shown once in the data note).
Figures are captured after the script ends (every open figure, in order), so the shown code keeps its plt.show().
While src/setup are unchanged, the cache is used and Matplotlib is not needed.
To re-run edited examples set VIZ_PY to a Python that has Matplotlib, Seaborn, pandas and NumPy installed.
"""
import base64, hashlib, io, json, os, pathlib, subprocess, textwrap, tempfile
from build import code, output, esc

CACHE = pathlib.Path(__file__).resolve().parent.parent / '_vizcache'
PY = os.environ.get('VIZ_PY', 'python3')

PRELUDE = """
import warnings
def _show(message, category, filename, lineno, file=None, line=None):
    print(f'{category.__name__}: {str(message).splitlines()[0]}')
warnings.showwarning = _show
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
np.set_printoptions(linewidth=100, suppress=True, precision=4)
pd.set_option('display.width', 110)
pd.set_option('display.max_columns', 20)
"""

EPILOGUE = """
import matplotlib.pyplot as _plt
for _i, _n in enumerate(_plt.get_fignums()):
    _plt.figure(_n).savefig(f'__fig{_i:02d}.png', dpi=100, bbox_inches='tight', pad_inches=0.15)
"""


def _clean(src):
    return textwrap.dedent(src).strip('\n')


def _shrink(png):
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert('RGB')
        q = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        from PIL import ImageChops, ImageStat
        err = sum(ImageStat.Stat(ImageChops.difference(im, q.convert('RGB'))).mean) / 3
        if err > 0.6:                      # smooth gradients would band: keep the full-colour PNG
            return png
        buf = io.BytesIO()
        q.save(buf, 'PNG', optimize=True)
        return buf.getvalue() if len(buf.getvalue()) < len(png) else png
    except Exception:
        return png


def run(src, setup='', expect_error=False, files=None):
    src, setup = _clean(src), _clean(setup)
    key = hashlib.sha256(json.dumps([PRELUDE, EPILOGUE, setup, src, files or {}], sort_keys=True).encode()).hexdigest()[:16]
    cf = CACHE / f'{key}.json'
    if cf.exists():
        d = json.loads(cf.read_text())
        return d['out'], d.get('imgs', [])
    work = pathlib.Path(tempfile.mkdtemp(prefix='upv_viz_'))
    for name, content in (files or {}).items():
        (work / name).write_text(_clean(content) + '\n')
    script = PRELUDE + '\n' + setup + '\n' + src + '\n' + EPILOGUE
    r = subprocess.run([PY, '-I', '-c', script], capture_output=True, text=True, timeout=300, cwd=work)
    out = r.stdout.rstrip('\n')
    if r.returncode != 0:
        last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'error'
        if not expect_error:
            raise RuntimeError(f'visualization example failed: {last}\n---\n{r.stderr[-2500:]}\n---\n{src}')
        out = (out + '\n' if out else '') + last
    imgs = [base64.b64encode(_shrink(p.read_bytes())).decode() for p in sorted(work.glob('__fig*.png'))]
    imgs += ['gif:' + base64.b64encode(p.read_bytes()).decode() for p in sorted(work.glob('*.gif'))]   # animations the example saved
    CACHE.mkdir(exist_ok=True)
    cf.write_text(json.dumps({'src': src, 'out': out, 'imgs': imgs}))
    return out, imgs


def figures(imgs, title='Figure'):
    if not imgs:
        return ''
    tags = ''.join(f'<img src="data:image/{"gif" if b.startswith("gif:") else "png"};base64,{b[4:] if b.startswith("gif:") else b}" '
                   f'alt="{esc(title)} {i + 1}" loading="lazy" '
                   f'style="display:block;max-width:100%;height:auto;margin:0.6rem auto;border-radius:8px;background:#fff">'
                   for i, b in enumerate(imgs))
    label = 'Rendered chart' if len(imgs) == 1 else f'Rendered charts ({len(imgs)})'
    return (f'<div class="output-box"><div class="output-title"><i class="fas fa-image"></i> {label}</div>'
            f'<div style="padding:0.5rem 0.75rem">{tags}</div></div>')


def vizrun(src, setup='', title='Python (Matplotlib)', expect_error=False, files=None, out_title='Output'):
    out, imgs = run(src, setup, expect_error, files)
    return code(_clean(src), title, 'fa-brands fa-python') + (output(out, out_title) if out else '') + figures(imgs)


def pyshow(src, title='Python (Matplotlib)'):
    """Code shown, not executed."""
    return code(_clean(src), title, 'fa-brands fa-python')
