"""Helpers that really execute Hadoop-Streaming style examples at build time."""
import pathlib, subprocess, tempfile, textwrap
from build import code, output, esc

WORK = pathlib.Path(tempfile.gettempdir()) / 'upvanta_hadoop'


def put(name, src):
    """Write a helper file (mapper.py, input.txt …) into the example folder; returns its code block."""
    WORK.mkdir(exist_ok=True)
    src = textwrap.dedent(src).strip('\n') + '\n'
    (WORK / name).write_text(src)
    return src


def pyfile(name, src):
    """Show a Python file and save it for later shell runs."""
    s = put(name, src)
    return code(s, name, 'fa-brands fa-python')


def txtfile(name, src):
    s = put(name, src)
    return code(s, name, 'fa-file-lines')


def shrun(src, title='Shell (local test)'):
    """Run a bash pipeline in the example folder and show the real output."""
    src = textwrap.dedent(src).strip('\n')
    WORK.mkdir(exist_ok=True)
    r = subprocess.run(['bash', '-c', 'set -o pipefail; ' + src], capture_output=True, text=True, timeout=60, cwd=WORK,
                       env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
    if r.returncode != 0:
        raise RuntimeError(f'Shell example failed: {r.stderr}\n---\n{src}')
    out = r.stdout.rstrip('\n')
    return code(src, title, 'fa-terminal') + (output(out) if out else '')


def sh(src, title='HDFS shell'):
    """Command reference block (not executed: needs a live cluster)."""
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')


def xml(src, title):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-file-code')
