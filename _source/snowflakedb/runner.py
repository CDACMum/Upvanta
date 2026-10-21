"""Runs the Snowflake SQL examples at build time.

Snowflake is a cloud-only service, so the examples run on fakesnow (a Snowflake emulator that translates
Snowflake SQL to DuckDB) through the real snowflake-connector-python API, inside a fresh database
CDAC.BDA for every example. Output is rendered in SnowSQL's table format.

Every result is cached in _snowflakecache/<hash>.json, so a computer without fakesnow rebuilds the
page byte-for-byte from the cache. Set SNOWFLAKE_REFRESH=1 to re-execute everything.

Rules followed by the examples (to keep emulator output identical to real Snowflake):
  * every computed column has an alias; averages/divisions are cast to NUMBER(p,s)
  * OBJECT keys print sorted (as Snowflake stores them); Python iterates cursors via fetchall()
  * FLATTEN results are ordered by INDEX
  * features the emulator cannot run (warehouses, Time Travel, streams, tasks, Snowpipe, shares,
    RBAC, masking policies) use sq() and are shown without output
"""
import datetime
import decimal
import hashlib
import io
import json
import os
import pathlib
import re
import textwrap
import contextlib

from build import code, output

CACHE = pathlib.Path(__file__).resolve().parent.parent / '_snowflakecache'
PROMPT = 'CDAC.BDA>'
VARIANT_CODES = {5, 9, 10}   # VARIANT, OBJECT, ARRAY in snowflake-connector type codes

# ------------------------------------------------------------------ shared sample data
STUDENTS = """
CREATE OR REPLACE TABLE students (
  roll_no  INT,
  name     VARCHAR,
  course   VARCHAR,
  centre   VARCHAR,
  marks    NUMBER(5,2),
  joined   DATE
);
INSERT INTO students VALUES
  (2401, 'Anuj',    'PGCP-BDA', 'Kharghar', 78.50, '2026-02-02'),
  (2402, 'Aarshvi', 'PGCP-BDA', 'Juhu',     88.00, '2026-02-02'),
  (2403, 'Riya',    'PGCP-AI',  'Kharghar', 91.25, '2026-02-03'),
  (2404, 'Kabir',   'PGCP-AC',  'Kharghar', 67.00, '2026-02-03'),
  (2405, 'Sana',    'PGCP-BDA', 'Kharghar', 93.75, '2026-02-04'),
  (2406, 'Omkar',   'PGCP-AI',  'Juhu',     72.50, '2026-02-04'),
  (2407, 'Meera',   'PGCP-AC',  'Juhu',     84.00, '2026-02-05'),
  (2408, 'Tejas',   'PGCP-BDA', 'Juhu',     59.25, '2026-02-05');
"""


# ------------------------------------------------------------------ statement splitting
def split_sql(src):
    """Split on ';' outside quotes and $$ blocks."""
    out, buf, i, q, dollar = [], [], 0, False, False
    while i < len(src):
        ch = src[i]
        if not q and not dollar and src.startswith('--', i):      # comment: copy to end of line
            j = src.find('\n', i)
            j = len(src) if j < 0 else j
            buf.append(src[i:j]); i = j; continue
        if not q and src.startswith('$$', i):
            dollar = not dollar
            buf.append('$$'); i += 2; continue
        if ch == "'" and not dollar:
            q = not q
        if ch == ';' and not q and not dollar:
            s = ''.join(buf).strip()
            if s:
                out.append(s)
            buf = []
        else:
            buf.append(ch)
        i += 1
    s = ''.join(buf).strip()
    if s:
        out.append(s)
    return out


def _strip_comments(stmt):
    return '\n'.join(l for l in stmt.splitlines() if not l.strip().startswith('--')).strip()


# ------------------------------------------------------------------ value formatting
def _norm(v):
    """Snowflake prints whole numbers inside VARIANT without a decimal part (88, not 88.0)."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, list):
        return [_norm(x) for x in v]
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    return v


def _fmt(v, type_code):
    if v is None:
        return ['NULL']
    if type_code in VARIANT_CODES or isinstance(v, (list, dict)):
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except ValueError:
                return [v]
        return json.dumps(_norm(v), indent=2, sort_keys=True).splitlines()
    if isinstance(v, bool):
        return ['True' if v else 'False']
    if isinstance(v, decimal.Decimal):
        return [str(v)]
    if isinstance(v, float):
        return [repr(v)]
    if isinstance(v, datetime.datetime):
        return [v.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]]
    if isinstance(v, datetime.date):
        return [v.isoformat()]
    return str(v).splitlines() or ['']


def _numeric(v):
    return isinstance(v, (int, float, decimal.Decimal)) and not isinstance(v, bool)


def render_table(cols, rows):
    """SnowSQL-style table (multi-line cells for VARIANT)."""
    names = [c[0] for c in cols]
    cells = [[_fmt(v, cols[j][1]) for j, v in enumerate(r)] for r in rows]
    width = [max([len(names[j])] + [len(l) for r in cells for l in r[j]]) for j in range(len(names))]
    right = [bool(rows) and all(_numeric(r[j]) or r[j] is None for r in rows) for j in range(len(names))]
    sep = '+' + '+'.join('-' * (w + 2) for w in width) + '+'
    mid = '|' + '+'.join('-' * (w + 2) for w in width) + '|'
    lines = [sep, '| ' + ' | '.join(n.ljust(width[j]) for j, n in enumerate(names)) + ' |', mid]
    for r in cells:
        for k in range(max(len(c) for c in r)):
            parts = []
            for j, c in enumerate(r):
                t = c[k] if k < len(c) else ''
                parts.append(t.rjust(width[j]) if right[j] else t.ljust(width[j]))
            lines.append('| ' + ' | '.join(parts) + ' |')
    lines.append(sep)
    lines.append(f'{len(rows)} Row(s) produced.')
    return '\n'.join(lines)


def _first_line(stmt):
    s = ' '.join(_strip_comments(stmt).split())
    return s if len(s) <= 90 else s[:87] + '...'


# ------------------------------------------------------------------ execution
def _execute(setup, src, show):
    import fakesnow
    import snowflake.connector
    blocks = []
    with fakesnow.patch():
        conn = snowflake.connector.connect(database='CDAC', schema='BDA')
        cur = conn.cursor()
        for stmt in split_sql(setup):
            cur.execute(stmt)
        stmts = split_sql(src)
        for idx, stmt in enumerate(stmts):
            cur.execute(stmt)
            rows = cur.fetchall()
            cols = [(d.name, d.type_code) for d in cur.description]
            kind = _strip_comments(stmt).split(None, 1)[0].upper()
            want = show == 'all' or (show == 'queries' and kind in ('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC')) \
                or (show == 'dml' and kind in ('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC', 'INSERT', 'UPDATE', 'DELETE', 'MERGE')) \
                or (isinstance(show, (list, tuple, set)) and idx in show)
            if want:
                blocks.append(f'{PROMPT} {_first_line(stmt)}\n' + render_table(cols, rows))
        conn.close()
    return '\n\n'.join(blocks)


def _cached(kind, payload, fn):
    key = hashlib.sha1(json.dumps([kind, payload], sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f'{key}.json'
    if f.exists() and not os.environ.get('SNOWFLAKE_REFRESH'):
        return json.loads(f.read_text(encoding='utf-8'))['output']
    out = fn()
    CACHE.mkdir(exist_ok=True)
    f.write_text(json.dumps({'kind': kind, 'input': payload, 'output': out}, indent=1, ensure_ascii=False), encoding='utf-8')
    return out


def sql(src, setup='', title='Snowflake SQL', show='dml', data=True):
    """SQL block + real output. show = 'queries' | 'dml' (default) | 'all' | list of statement indexes."""
    src = textwrap.dedent(src).strip('\n')
    pre = (STUDENTS if data else '') + textwrap.dedent(setup)
    out = _cached('sql', [pre, src, show if isinstance(show, str) else list(show)], lambda: _execute(pre, src, show))
    return code(src, title, 'fa-database') + (output(out) if out else '')


def pyrun(src, title='Python (snowflake-connector-python)'):
    """Python using the real Snowflake connector API, executed against the emulator; stdout is the output."""
    src = textwrap.dedent(src).strip('\n')

    def go():
        import fakesnow
        buf = io.StringIO()
        with fakesnow.patch(), contextlib.redirect_stdout(buf):
            exec(compile(src, '<example>', 'exec'), {'__name__': '__main__'})
        return buf.getvalue().rstrip('\n')
    out = _cached('py', src, go)
    return code(src, title, 'fa-brands fa-python') + (output(out) if out else '')


def sq(src, title='Snowflake SQL (shown, not executed)'):
    """Snowflake SQL shown without running: needs a real account (warehouses, Time Travel, streams, tasks…)."""
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-database')


def py(src, title='Python'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-brands fa-python')


def sh(src, title='Shell'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-terminal')


def conf(src, title='Configuration'):
    return code(textwrap.dedent(src).strip('\n'), title, 'fa-gear')
