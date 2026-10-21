"""Runs the CQL examples at build time with cqlsim.py (a deterministic CQL engine that follows
Cassandra 5.0's rules: Murmur3 tokens, clustering order, WHERE-clause restrictions and their error
messages, last-write-wins timestamps, TTL, tombstones, collections, counters, LWT, SAI).
Pure Python, no Cassandra install needed, so every rebuild gives the same output.

In an example:
  !sleep N     advance the simulated clock by N seconds (shown as a comment)
Statements in `setup` run first and are not shown.
"""
import re
import textwrap

from build import code, output
from cassandra.cqlsim import Engine, render

DEFAULT_SETUP = """
CREATE KEYSPACE cdac WITH replication = {'class': 'NetworkTopologyStrategy', 'dc_mumbai': 3};
USE cdac;
"""


def _display(src):
    def rep(m):
        n = int(m.group(1))
        when = f'{n // 60} minutes' if n >= 120 and n % 60 == 0 else f'{n} seconds'
        return f'-- ... {when} later ...'
    return re.sub(r'^!sleep\s+(\d+)\s*$', rep, src, flags=re.M)


def cql(src, setup='', title='cqlsh', expect_error=False, show_output=True, keyspace=True):
    """CQL block + output produced by executing it on cqlsim."""
    src = textwrap.dedent(src).strip('\n')
    eng = Engine()
    pre = (DEFAULT_SETUP if keyspace else '') + textwrap.dedent(setup)
    if pre.strip():
        for stmt, res, _ in eng.run(pre):
            if res is not None and res[0] == 'error':
                raise RuntimeError(f'CQL setup failed: {res[1]}\n--- {stmt}')
    results = eng.run(src)
    errs = [r for _, r, _ in results if r is not None and r[0] == 'error']
    if errs and not expect_error:
        raise RuntimeError(f'CQL example failed: {errs[0][1]}\n---\n{src}')
    if expect_error and not errs:
        raise RuntimeError(f'CQL example was expected to fail but did not:\n{src}')
    out = render(results)
    return code(_display(src), title, 'fa-database') + (output(out) if out and show_output else '')


def cq(src, title='cqlsh'):
    """CQL shown without running (multi-node behaviour, server configuration)."""
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-database')


def sh(src, title='Shell'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')


def py(src, title='Python'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-brands fa-python')


def conf(src, title='cassandra.yaml'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-gear')
