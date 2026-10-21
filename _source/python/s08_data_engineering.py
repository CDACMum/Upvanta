from build import *

SECTION = dict(level='advanced', title='Python for Data Engineering', questions=[

# ------------------------------------------------------------------ 44
Q('How do you process a file that is larger than memory?', 'Processing Large Files', minutes=7, cards=[
    definition(
        defbox('Never load the whole file with <code>read()</code> or a plain <code>pd.read_csv()</code>. Instead '
               '<strong>stream</strong> it: read a line or a chunk at a time, process it, keep only aggregated results, '
               'and let each chunk be garbage-collected.'),
        table(['Technique', 'How'], [
            ['Iterate the file object', '<code>for line in f:</code> — one line in memory at a time'],
            ['csv module', '<code>csv.DictReader(f)</code> streams rows'],
            ['pandas chunks', '<code>pd.read_csv(path, chunksize=100_000)</code> yields DataFrames'],
            ['Read only needed columns / types', '<code>usecols=[...]</code>, <code>dtype={...}</code> cut memory sharply'],
            ['Columnar formats', 'Parquet with pyarrow reads only selected columns and row groups'],
            ['Out-of-core engines', 'Polars (lazy/streaming), DuckDB, Dask, Spark for very large data'],
        ]),
        tags('Chunking', 'Streaming', 'chunksize', 'usecols', 'Parquet', 'Memory'),
    ),
    example(
        pyrun("""
import csv, random
from collections import defaultdict

random.seed(7)
with open("sales.csv", "w", newline="") as f:          # create a sample file
    w = csv.writer(f)
    w.writerow(["order_id", "city", "amount"])
    for i in range(200_000):
        w.writerow([i, random.choice(["Pune", "Mumbai", "Delhi"]), random.randint(100, 5000)])

# 1) Pure Python streaming aggregation
totals = defaultdict(int)
with open("sales.csv", newline="") as f:
    for row in csv.DictReader(f):
        totals[row["city"]] += int(row["amount"])
print(dict(sorted(totals.items())))

# 2) pandas in chunks
import pandas as pd
parts = []
for chunk in pd.read_csv("sales.csv", usecols=["city", "amount"],
                         dtype={"city": "category", "amount": "int32"},
                         chunksize=50_000):
    parts.append(chunk.groupby("city", observed=True)["amount"].sum())
print(pd.concat(parts).groupby(level=0).sum().to_dict())
"""),
        title='Example: Aggregating a Large CSV'),
    crossq(
        ('How do you count lines in a 20 GB file quickly?',
         '<code>sum(1 for _ in open(path, "rb"))</code> streams in binary; reading fixed-size blocks and counting <code>b"\\n"</code> is faster still. On Linux, <code>wc -l</code>.'),
        ('Why does pandas use so much memory?',
         'Object (string) columns store Python objects, and int64/float64 are defaults. Use <code>category</code> for repeated strings, smaller numeric types, and only the columns you need.'),
    ),
]),

# ------------------------------------------------------------------ 45
Q('How do you flatten nested JSON in Python?', 'Flattening Nested JSON', minutes=7, cards=[
    definition(
        defbox('API responses and event logs are usually <strong>nested JSON</strong>: objects inside objects and arrays of '
               'objects. Before loading into a table you <strong>flatten</strong> it — nested keys become columns like '
               '<code>customer.city</code>, and arrays become separate rows.'),
        tags('JSON', 'Flatten', 'Recursion', 'json_normalize', 'Explode', 'Semi-structured'),
    ),
    example(
        pyrun("""
import json

order = json.loads('''
{"order_id": 5001,
 "customer": {"id": "C101", "name": "Asha", "address": {"city": "Pune", "pin": "411001"}},
 "items": [{"sku": "P1", "qty": 2}, {"sku": "P7", "qty": 1}],
 "paid": true}
''')

def flatten(obj, parent="", sep="."):
    flat = {}
    for key, value in obj.items():
        name = f"{parent}{sep}{key}" if parent else key
        if isinstance(value, dict):
            flat.update(flatten(value, name, sep))      # recurse into objects
        else:
            flat[name] = value                          # lists kept as-is here
    return flat

for k, v in flatten(order).items():
    print(f"{k:<24} {v}")
"""),
        pyrun("""
import pandas as pd

orders = [
    {"order_id": 5001, "customer": {"id": "C101", "city": "Pune"},
     "items": [{"sku": "P1", "qty": 2}, {"sku": "P7", "qty": 1}]},
    {"order_id": 5002, "customer": {"id": "C102", "city": "Delhi"},
     "items": [{"sku": "P3", "qty": 5}]},
]

# One row per item, with parent fields repeated
df = pd.json_normalize(orders, record_path="items",
                       meta=["order_id", ["customer", "id"], ["customer", "city"]])
print(df.to_string(index=False))
""", 'pandas.json_normalize: arrays become rows'),
        title='Example'),
    crossq(
        ('How would you do this in PySpark?',
         'Read with <code>spark.read.json()</code>, select nested fields with dot notation (<code>col("customer.address.city")</code>) and turn arrays into rows with <code>explode("items")</code>.'),
        ('How do you handle keys that are missing in some records?',
         'Use <code>dict.get(key)</code> with defaults, or let <code>json_normalize</code> fill NaN, then define a fixed target schema so downstream tables do not change shape unexpectedly.'),
    ),
]),

# ------------------------------------------------------------------ 46
Q('How do you connect to a database from Python safely? (DB-API, parameterized queries)', 'Database Access & SQL Injection', minutes=8, cards=[
    definition(
        defbox('Python database drivers follow the <strong>DB-API 2.0</strong> standard (PEP 249): '
               '<code>connect()</code> → <code>cursor()</code> → <code>execute()</code> → <code>fetch*()</code> → '
               '<code>commit()</code>/<code>rollback()</code> → <code>close()</code>. The same pattern works with sqlite3, '
               'mysql-connector, PyMySQL and psycopg.',
               'Always use <strong>parameterized queries</strong> — pass values separately from the SQL text. Never build SQL '
               'with f-strings or <code>+</code>, which allows <strong>SQL injection</strong>.'),
        tags('DB-API', 'Cursor', 'Parameterized Query', 'SQL Injection', 'executemany', 'SQLAlchemy'),
    ),
    example(
        pyrun("""
import sqlite3

conn = sqlite3.connect(":memory:")
cur = conn.cursor()
cur.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, city TEXT)")

rows = [(1, "Asha", "Pune"), (2, "Rohit", "Mumbai"), (3, "Meera", "Pune")]
cur.executemany("INSERT INTO students VALUES (?, ?, ?)", rows)   # bulk insert
conn.commit()

city = "Pune"
cur.execute("SELECT id, name FROM students WHERE city = ?", (city,))   # SAFE
print(cur.fetchall())

# What injection looks like
evil = "x' OR '1'='1"
unsafe_sql = f"SELECT name FROM students WHERE city = '{evil}'"         # DANGEROUS
print("unsafe returns:", conn.execute(unsafe_sql).fetchall())
print("safe returns  :", conn.execute("SELECT name FROM students WHERE city = ?", (evil,)).fetchall())

# Transaction with context manager: commit on success, rollback on error
try:
    with conn:
        conn.execute("UPDATE students SET city = 'Delhi' WHERE id = 1")
        conn.execute("INSERT INTO students VALUES (1, 'Dup', 'X')")        # PK violation
except sqlite3.IntegrityError as e:
    print("rolled back:", e)
print(conn.execute("SELECT city FROM students WHERE id = 1").fetchone())
conn.close()
"""),
        py("""
# MySQL with mysql-connector-python (placeholder is %s, not ?)
import os
import mysql.connector
import pandas as pd

conn = mysql.connector.connect(host="localhost", user="etl", password=os.environ["DB_PASS"],
                               database="college_db")
with conn.cursor(dictionary=True) as cur:
    cur.execute("SELECT name, cgpa FROM students WHERE dept_id = %s AND cgpa > %s", (1, 8.0))
    for row in cur:
        print(row["name"], row["cgpa"])
conn.close()

# SQLAlchemy + pandas
from sqlalchemy import create_engine, text
engine = create_engine("mysql+pymysql://etl:***@localhost/college_db")
df = pd.read_sql(text("SELECT * FROM students WHERE dept_id = :d"), engine, params={"d": 1})
df.to_sql("students_copy", engine, if_exists="replace", index=False, chunksize=10_000)
""", 'MySQL and SQLAlchemy (not executed here)'),
        title='Example'),
    crossq(
        ('Why is executemany() faster than calling execute() in a loop?',
         'Fewer round-trips and statement preparations; many drivers send it as a single batched or multi-row INSERT. For very large loads use the database\'s bulk loader (LOAD DATA, COPY).'),
        ('Where should database passwords come from?',
         'Environment variables, a secrets manager (AWS Secrets Manager, Vault) or Airflow connections — never hard-coded in the script or committed to Git.'),
        ('What is connection pooling?',
         'Reusing a set of open connections instead of opening a new one per query. SQLAlchemy\'s engine pools connections by default.'),
    ),
]),

# ------------------------------------------------------------------ 47
Q('How do you pull data from a REST API with pagination and retries?', 'REST APIs: Pagination & Retries', minutes=8, cards=[
    definition(
        defbox('Ingesting from REST APIs is a daily data-engineering task. A robust extractor handles: '
               '<strong>authentication</strong>, <strong>pagination</strong> (page numbers, offsets or cursors), '
               '<strong>timeouts</strong>, <strong>retries with backoff</strong> for 429/5xx errors, and '
               '<strong>rate limits</strong>.'),
        tags('requests', 'REST API', 'Pagination', 'Retry', 'Exponential Backoff', 'Rate Limit', 'Timeout'),
    ),
    example(
        py("""
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session(token):
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1,                  # waits 1, 2, 4, 8 … seconds
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session

def fetch_all(session, url, page_size=100):
    \"\"\"Yield records from a page-number paginated API.\"\"\"
    page = 1
    while True:
        resp = session.get(url, params={"page": page, "per_page": page_size}, timeout=30)
        resp.raise_for_status()                               # raise for 4xx/5xx
        records = resp.json()["data"]
        if not records:
            break
        yield from records
        page += 1

def fetch_all_cursor(session, url):
    \"\"\"Cursor-based pagination: the API returns the next cursor.\"\"\"
    params = {}
    while True:
        body = session.get(url, params=params, timeout=30).json()
        yield from body["items"]
        if not body.get("next_cursor"):
            break
        params["cursor"] = body["next_cursor"]

session = make_session(token=os.environ["API_TOKEN"])
# batches() is the helper from question 37; load_to_staging() writes to your DB
for batch in batches(fetch_all(session, "https://api.example.com/v1/orders"), 1000):
    load_to_staging(batch)                                    # write in batches
""", 'Production-style extractor (requests)'),
        title='Example'),
    explanation(
        table(['Pagination style', 'How it works', 'Notes'], [
            ['Page number', '<code>?page=3&amp;per_page=100</code>', 'Simple; rows can shift if data changes mid-extract'],
            ['Offset / limit', '<code>?offset=200&amp;limit=100</code>', 'Slow for large offsets on the server'],
            ['Cursor / token', '<code>?cursor=eyJpZCI6...</code> from previous response', 'Stable and efficient — preferred'],
            ['Time-window', '<code>?updated_since=2026-10-01T00:00Z</code>', 'Used for incremental loads'],
        ]),
        p('<strong>Idempotency</strong>: write each run so it can be safely re-run (e.g. upsert by primary key, or overwrite '
          'the date partition). APIs fail mid-way; a re-run must not create duplicates.', True),
        title='Pagination Styles'),
    crossq(
        ('What is exponential backoff with jitter?',
         'After each failure wait longer (1s, 2s, 4s, 8s …) plus a small random amount, so many clients do not retry at the same instant and overload the server again.'),
        ('Which HTTP errors should be retried?',
         '429 (rate limited — honour the Retry-After header), 500, 502, 503, 504 and network timeouts. Do not retry 400, 401, 403, 404 — they will fail again.'),
    ),
]),

# ------------------------------------------------------------------ 48
Q('How do you use the logging module instead of print?', 'Logging', minutes=6, cards=[
    definition(
        defbox('The <code>logging</code> module records events with <strong>levels</strong>, timestamps and source '
               'information, and sends them to configurable <strong>handlers</strong> (console, file, rotating files, '
               'cloud logging). Unlike <code>print</code>, levels can be switched without editing code.'),
        table(['Level', 'Use for'], [
            ['DEBUG', 'Detailed diagnostic information'],
            ['INFO', 'Normal milestones: "loaded 12,000 rows"'],
            ['WARNING', 'Something unexpected but the job continues'],
            ['ERROR', 'An operation failed'],
            ['CRITICAL', 'The application cannot continue'],
        ]),
        tags('logging', 'Logger', 'Handler', 'Formatter', 'Log Level', 'logger.exception'),
    ),
    example(
        pyrun("""
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s %(name)s: %(message)s",   # add %(asctime)s in real jobs
    stream=sys.stdout,
)
log = logging.getLogger("etl.orders")                 # one logger per module

log.debug("not shown at INFO level")
log.info("extract started for %s", "2026-10-08")      # lazy %-formatting
rows = 12_450
log.info("loaded %d rows", rows)
log.warning("%d rows had missing city", 37)

try:
    1 / 0
except ZeroDivisionError:
    log.exception("transform failed")                 # ERROR + traceback
"""),
        title='Example'),
    crossq(
        ('Why use logging.getLogger(__name__)?',
         'Each module gets its own named logger in a hierarchy (<code>etl.extract</code>, <code>etl.load</code>), so you can control levels and handlers per component.'),
        ('Why log with "%s" arguments instead of f-strings?',
         'The message is formatted only if the record is actually emitted — cheaper for DEBUG logs that are disabled — and log aggregators can group messages by their template.'),
    ),
]),

# ------------------------------------------------------------------ 49
Q('How do you work with dates, times and time zones?', 'Datetime & Time Zones', minutes=7, cards=[
    definition(
        defbox('The <code>datetime</code> module provides <code>date</code>, <code>time</code>, <code>datetime</code> and '
               '<code>timedelta</code>. A datetime is either <strong>naive</strong> (no time zone) or <strong>aware</strong> '
               '(has <code>tzinfo</code>). <code>zoneinfo</code> (Python 3.9+) supplies real time zones like '
               '<code>Asia/Kolkata</code>.'),
        hl('Store and process timestamps in <strong>UTC</strong>; convert to local time only for display.', 'Golden rule'),
        tags('datetime', 'timedelta', 'zoneinfo', 'UTC', 'strftime', 'strptime', 'ISO 8601'),
    ),
    example(
        pyrun("""
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo

# Parse and format
d = datetime.strptime("08-10-2026 22:45", "%d-%m-%Y %H:%M")
print(d.strftime("%Y-%m-%d %H:%M"), d.strftime("%A, %d %b %Y"))

# Arithmetic
print(d + timedelta(days=7, hours=3))
print((date(2026, 12, 31) - date(2026, 10, 8)).days, "days left in the year")

# Aware datetimes and conversion
ist = datetime(2026, 10, 8, 22, 45, tzinfo=ZoneInfo("Asia/Kolkata"))
print(ist.isoformat())
print(ist.astimezone(timezone.utc).isoformat())
print(ist.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %H:%M %Z"))

# ISO 8601 strings from APIs
ts = datetime.fromisoformat("2026-10-08T17:15:00+00:00")
print(ts.tzinfo, ts.timestamp())

# Daily partitions for a backfill
start = date(2026, 10, 1)
print([str(start + timedelta(days=i)) for i in range(3)])
"""),
        title='Example'),
    crossq(
        ('What is wrong with datetime.now() in pipelines?',
         'It returns a naive local time that depends on the server\'s time zone. Use <code>datetime.now(timezone.utc)</code>. In Airflow, use the run\'s logical date instead of "now" so re-runs process the same window.'),
        ('Can you compare naive and aware datetimes?',
         'No — Python raises TypeError. Make both aware (attach a zone with <code>replace(tzinfo=...)</code> or convert) before comparing.'),
    ),
]),

# ------------------------------------------------------------------ 50
Q('How are regular expressions used in Python?', 'Regular Expressions', minutes=7, cards=[
    definition(
        defbox('The <code>re</code> module matches text against <strong>patterns</strong>. Data engineers use it to '
               'validate formats, parse logs, extract fields and clean messy strings.'),
        table(['Function', 'Purpose'], [
            ['re.search', 'First match anywhere in the string'],
            ['re.match / re.fullmatch', 'Match at the start / the entire string'],
            ['re.findall / re.finditer', 'All matches (list / iterator of match objects)'],
            ['re.sub', 'Replace matches'],
            ['re.split', 'Split on a pattern'],
            ['re.compile', 'Pre-compile a pattern used many times'],
        ]),
        table(['Token', 'Meaning'], [
            ['\\d \\w \\s', 'digit, word character, whitespace (capital = NOT)'],
            ['. ^ $', 'any char, start, end'],
            ['* + ? {m,n}', 'repetition; add ? for non-greedy (<code>.*?</code>)'],
            ['[A-Z] [^0-9]', 'character class / negated class'],
            ['( ) (?P&lt;name&gt; )', 'capturing group / named group'],
        ]),
        tags('re', 'Regex', 'search', 'findall', 'sub', 'Named Groups', 'Log Parsing'),
    ),
    example(
        pyrun("""
import re

log = '192.168.1.10 - - [08/Oct/2026:22:45:01 +0530] "GET /api/orders?id=7 HTTP/1.1" 503 1234'

pattern = re.compile(
    r'(?P<ip>\\d+\\.\\d+\\.\\d+\\.\\d+) .*?\\[(?P<ts>[^\\]]+)\\] "(?P<method>\\w+) (?P<path>\\S+)[^"]*" (?P<status>\\d{3})'
)
m = pattern.search(log)
print(m.groupdict())

text = "Contact asha.p@cdac.in or rohit@example.com, phone 98200-11111"
print(re.findall(r"[\\w.+-]+@[\\w-]+\\.[\\w.]+", text))
print(re.sub(r"\\D", "", "98200-11111"))                    # keep digits only

print(bool(re.fullmatch(r"[A-Z]{5}\\d{4}[A-Z]", "ABCDE1234F")))   # PAN-like format
print(re.split(r"\\s*[;,|]\\s*", "pune; mumbai,delhi | agra"))
print(re.sub(r"\\s+", " ", "  too    many   spaces ").strip())
"""),
        title='Example: Parsing an Access Log'),
    crossq(
        ('Why use raw strings r"..." for patterns?',
         'Backslashes are special both in Python strings and in regex. In a raw string Python leaves them alone, so <code>r"\\d"</code> reaches the regex engine as <code>\\d</code>.'),
        ('Greedy vs non-greedy?',
         '<code>.*</code> matches as much as possible; <code>.*?</code> as little as possible. On <code>&lt;b&gt;x&lt;/b&gt;&lt;b&gt;y&lt;/b&gt;</code>, <code>&lt;b&gt;.*&lt;/b&gt;</code> matches everything, <code>&lt;b&gt;.*?&lt;/b&gt;</code> matches the first tag pair.'),
    ),
]),

# ------------------------------------------------------------------ 51
Q('What are type hints? Are they enforced?', 'Type Hints', minutes=5, cards=[
    definition(
        defbox('<strong>Type hints</strong> (PEP 484) annotate the expected types of variables, parameters and return '
               'values. Python <strong>does not enforce them at runtime</strong>; they are used by IDEs for autocompletion '
               'and by static checkers like <strong>mypy</strong> or <strong>pyright</strong> to catch bugs before running.'),
        tags('Type Hints', 'typing', 'mypy', 'Optional', 'Union', 'TypedDict', 'Static Analysis'),
    ),
    example(
        pyrun("""
from typing import Iterator, TypedDict

class OrderRow(TypedDict):
    order_id: int
    city: str
    amount: float

def parse_rows(lines: list[str]) -> Iterator[OrderRow]:
    for line in lines:
        oid, city, amt = line.split(",")
        yield {"order_id": int(oid), "city": city, "amount": float(amt)}

def total(rows: list[OrderRow], city: str | None = None) -> float:
    return sum(r["amount"] for r in rows if city is None or r["city"] == city)

rows = list(parse_rows(["1,Pune,250.0", "2,Delhi,100.5", "3,Pune,49.5"]))
print(total(rows), total(rows, city="Pune"))

def double(x: int) -> int:
    return x * 2
print(double("ab"))          # runs fine: hints are NOT enforced at runtime
print(double.__annotations__)
"""),
        title='Example'),
    crossq(
        ('Optional[str] vs str | None?',
         'Identical. <code>str | None</code> is the modern syntax (3.10+). Note that Optional means "may be None", not "optional argument".'),
        ('How do you validate types at runtime?',
         'Use <strong>pydantic</strong> models or dataclass validation libraries — common for API payloads and pipeline configs.'),
    ),
]),

# ------------------------------------------------------------------ 52
Q('How do you unit-test data transformations with pytest?', 'Testing with pytest', minutes=7, cards=[
    definition(
        defbox('<strong>pytest</strong> is the most popular Python testing framework. Tests are plain functions named '
               '<code>test_*</code> that use bare <code>assert</code> statements. Fixtures provide reusable test data, and '
               'parametrize runs one test with many inputs.',
               'For pipelines, keep transformations as <strong>pure functions</strong> (input → output, no I/O) so they are easy to test.'),
        tags('pytest', 'Unit Test', 'Fixture', 'parametrize', 'assert', 'Mocking', 'CI'),
    ),
    example(
        pyrun('''
import pathlib, subprocess, sys, textwrap

pathlib.Path("transform.py").write_text(textwrap.dedent("""
    def clean_city(city):
        if city is None or not city.strip():
            return "UNKNOWN"
        return " ".join(city.split()).title()

    def dedupe_latest(rows):
        latest = {}
        for r in rows:
            if r["id"] not in latest or r["updated"] > latest[r["id"]]["updated"]:
                latest[r["id"]] = r
        return sorted(latest.values(), key=lambda r: r["id"])
"""))

pathlib.Path("test_transform.py").write_text(textwrap.dedent("""
    import pytest
    from transform import clean_city, dedupe_latest

    @pytest.mark.parametrize("raw, expected", [
        ("  navi   mumbai ", "Navi Mumbai"),
        ("PUNE", "Pune"),
        ("", "UNKNOWN"),
        (None, "UNKNOWN"),
    ])
    def test_clean_city(raw, expected):
        assert clean_city(raw) == expected

    @pytest.fixture
    def rows():
        return [{"id": 1, "updated": 1}, {"id": 1, "updated": 3}, {"id": 2, "updated": 2}]

    def test_dedupe_keeps_latest(rows):
        out = dedupe_latest(rows)
        assert [r["updated"] for r in out] == [3, 2]

    def test_bad_input_raises():
        with pytest.raises(KeyError):
            dedupe_latest([{"updated": 1}])
"""))

r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_transform.py"],
                   capture_output=True, text=True)
print(r.stdout.strip().splitlines()[-1])
''', 'Writing transform.py and its tests, then running pytest'),
        title='Example'),
    crossq(
        ('How do you test code that calls a database or an API?',
         'Separate I/O from logic and test the logic directly. For the I/O layer, use mocks (<code>unittest.mock.patch</code>, the <code>responses</code> library for HTTP), an in-memory SQLite/DuckDB, or a disposable database container (testcontainers).'),
        ('Unit tests vs data-quality tests?',
         'Unit tests check your <strong>code</strong> with known inputs before deployment. Data-quality tests (dbt tests, Great Expectations) check the <strong>actual data</strong> after every run — nulls, duplicates, ranges, freshness. Pipelines need both.'),
    ),
]),

])
