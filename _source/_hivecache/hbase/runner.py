"""Runs the HBase shell examples at build time with hbasesim.py (a deterministic HBase shell that follows
HBase 2.x semantics: byte-ordered row keys, column families, versions, timestamps, delete markers, TTL,
filters, counters). Pure Python, no HBase install needed, so every rebuild gives the same output.
The shell's "Took N seconds" timing lines are left out.

In an example:
  !sleep N     advance the simulated clock by N seconds (shown as a comment)
Commands in `setup` run first and are not shown."""
import re
import textwrap

from build import code, output
from hbase.hbasesim import Shell, render


def _display(src):
    def rep(m):
        n = int(m.group(1))
        when = f'{n // 60} minutes' if n >= 120 and n % 60 == 0 else f'{n} seconds'
        return f'# ... {when} later ...'
    return re.sub(r'^!sleep\s+(\d+)\s*$', rep, src, flags=re.M)


def hsh(src, setup='', title='HBase shell', expect_error=False, show_output=True):
    """HBase shell block + output produced by executing it on hbasesim."""
    src = textwrap.dedent(src).strip('\n')
    sh_ = Shell()
    if setup.strip():
        for cmd, res in sh_.run(textwrap.dedent(setup)):
            if res and res.startswith('ERROR'):
                raise RuntimeError(f'HBase setup failed: {res}\n--- {cmd}')
    sh_.n = 0
    results = sh_.run(src)
    errs = [r for _, r in results if r and r.startswith('ERROR')]
    if errs and not expect_error:
        raise RuntimeError(f'HBase example failed: {errs[0]}\n---\n{src}')
    if expect_error and not errs:
        raise RuntimeError(f'HBase example was expected to fail but did not:\n{src}')
    out = render(results)
    return code(_display(src), title, 'fa-terminal') + (output(out) if out and show_output else '')


def hq(src, title='HBase shell'):
    """Shown without running (cluster-level commands)."""
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')


def sh(src, title='Shell'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')


def java(src, title='Java'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-brands fa-java')


def py(src, title='Python'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-brands fa-python')


def xml(src, title='hbase-site.xml'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-gear')


def sql(src, title='Apache Phoenix (SQL)'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-database')
