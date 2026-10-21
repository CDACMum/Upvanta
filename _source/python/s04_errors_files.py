from build import *

SECTION = dict(level='intermediate', title='Errors & File Handling', questions=[

# ------------------------------------------------------------------ 23
Q('Explain exception handling: try, except, else, finally', 'try / except / else / finally', minutes=7, cards=[
    definition(
        defbox('An <strong>exception</strong> is an error raised at runtime. Python handles it with:'),
        table(['Block', 'Runs when'], [
            ['try', 'Always — contains code that may fail'],
            ['except', 'Only if a matching exception was raised in try'],
            ['else', 'Only if try completed <strong>without</strong> an exception'],
            ['finally', '<strong>Always</strong> — success, failure, even after return; used for cleanup'],
        ]),
        tags('try', 'except', 'else', 'finally', 'raise', 'Exception Hierarchy'),
    ),
    example(
        pyrun("""
def parse_amount(value):
    try:
        amount = float(value)
    except (TypeError, ValueError) as e:      # catch specific exceptions
        print(f"  bad value {value!r}: {type(e).__name__}")
        return None
    else:
        print(f"  parsed {amount}")           # only on success
        return amount
    finally:
        print("  finally runs every time")

for v in ["120.5", "abc", None]:
    print("input:", v)
    parse_amount(v)
"""),
        pyrun("""
# Re-raise with context, keeping the original cause
def load_config(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError as e:
        raise RuntimeError(f"Config missing: {path}") from e

try:
    load_config("/no/such/file.yaml")
except RuntimeError as e:
    print(e, "| caused by:", type(e.__cause__).__name__)
""", 'Exception chaining'),
        title='Example'),
    explanation(
        p('<strong>Exception hierarchy (simplified):</strong> <code>BaseException</code> → <code>Exception</code> → '
          '<code>ValueError, TypeError, KeyError, IndexError, FileNotFoundError (OSError), ZeroDivisionError, …</code>. '
          '<code>KeyboardInterrupt</code> and <code>SystemExit</code> inherit from <code>BaseException</code> directly.'),
        warn('A bare <code>except:</code> or <code>except Exception: pass</code> silently swallows bugs — including typos '
             'and, for bare except, Ctrl+C. Catch the specific exceptions you expect, and log the rest.', 'Bad practice'),
        title='Best Practices'),
    crossq(
        ('If try has a return statement, does finally still run?',
         'Yes. finally runs before the function actually returns. If finally itself has a return, it overrides the earlier one (avoid that).'),
        ('Why use else instead of putting the code inside try?',
         'It keeps the try block minimal, so you do not accidentally catch exceptions from code you did not intend to protect.'),
        ('EAFP vs LBYL?',
         '<strong>EAFP</strong> (Easier to Ask Forgiveness than Permission — try/except) is the Pythonic style. <strong>LBYL</strong> (Look Before You Leap — check first with if) can have race conditions, e.g. a file deleted between the check and the open.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you create and raise custom exceptions?', 'Custom Exceptions', minutes=5, cards=[
    definition(
        defbox('A <strong>custom exception</strong> is a class that inherits from <code>Exception</code> (or a subclass). '
               'It gives errors meaningful names that callers can catch specifically, and can carry extra data.',
               '<code>raise</code> throws an exception; <code>raise</code> alone inside an except block re-raises the current one.'),
        tags('Custom Exception', 'raise', 'Exception Hierarchy', 'Data Quality'),
    ),
    example(
        pyrun("""
class PipelineError(Exception):
    \"\"\"Base class for all pipeline errors.\"\"\"

class DataQualityError(PipelineError):
    def __init__(self, table, failed_checks):
        self.table = table
        self.failed_checks = failed_checks
        super().__init__(f"{table}: {len(failed_checks)} check(s) failed -> {failed_checks}")

def validate(table, rows):
    failed = []
    if any(r.get("id") is None for r in rows):
        failed.append("id_not_null")
    if len({r["id"] for r in rows if r.get("id")}) != len([r for r in rows if r.get("id")]):
        failed.append("id_unique")
    if failed:
        raise DataQualityError(table, failed)
    return True

rows = [{"id": 1}, {"id": 1}, {"id": None}]
try:
    validate("orders", rows)
except DataQualityError as e:
    print("Blocked load ->", e)
    print("failed checks:", e.failed_checks)
except PipelineError:
    print("other pipeline problem")
"""),
        title='Example: Data-Quality Exception'),
    crossq(
        ('Why define a base exception for your project?',
         'Callers can catch all of your library\'s errors with one <code>except PipelineError</code> while still being able to handle specific subclasses differently.'),
        ('What is the assert statement for?',
         'Internal sanity checks during development: <code>assert len(rows) > 0, "no rows"</code>. Asserts are removed when Python runs with <code>-O</code>, so never use them for input validation.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What is a context manager and the "with" statement?', 'Context Managers', minutes=6, cards=[
    definition(
        defbox('A <strong>context manager</strong> sets something up and <strong>guarantees cleanup</strong>, even if an '
               'exception occurs. The <code>with</code> statement calls its <code>__enter__</code> method at the start and '
               '<code>__exit__</code> at the end.',
               'Typical uses: files, database connections and transactions, locks, temporary directories, timers.'),
        tags('with', 'Context Manager', '__enter__', '__exit__', 'contextlib', 'Resource Cleanup'),
    ),
    example(
        pyrun("""
from contextlib import contextmanager
import time

# 1) Class-based
class Timer:
    def __init__(self, label):
        self.label = label
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    def __exit__(self, exc_type, exc, tb):
        print(f"{self.label}: {time.perf_counter() - self.start:.3f}s, error={exc_type is not None}")
        return False                     # do not suppress exceptions

with Timer("transform"):
    sum(range(1_000_000))

# 2) Generator-based with @contextmanager
@contextmanager
def transaction(conn_name):
    print(f"BEGIN on {conn_name}")
    try:
        yield
        print("COMMIT")
    except Exception as e:
        print(f"ROLLBACK because {e}")
        raise

try:
    with transaction("warehouse"):
        raise ValueError("bad row")
except ValueError:
    pass
"""),
        title='Example'),
    crossq(
        ('What happens if __exit__ returns True?',
         'The exception is suppressed and execution continues after the with block. Use this rarely — <code>contextlib.suppress(FileNotFoundError)</code> is the standard way.'),
        ('Can you open several context managers in one with?',
         'Yes: <code>with open("in.csv") as src, open("out.csv", "w") as dst:</code>. They are exited in reverse order.'),
    ),
]),

# ------------------------------------------------------------------ 26
Q('How do you read and write files, CSV and JSON in Python?', 'File Handling (CSV, JSON)', minutes=8, cards=[
    definition(
        defbox('Files are opened with <code>open(path, mode, encoding=...)</code>, preferably inside a <code>with</code> '
               'block so they are closed automatically. The standard library modules <code>csv</code> and <code>json</code> '
               'handle the two most common data-exchange formats.'),
        table(['Mode', 'Meaning'], [
            ['"r"', 'Read text (default); error if missing'],
            ['"w"', 'Write text; creates or <strong>truncates</strong>'],
            ['"a"', 'Append; creates if missing'],
            ['"x"', 'Create; error if the file exists'],
            ['"rb" / "wb"', 'Binary read / write (images, Parquet, pickles)'],
            ['"r+"', 'Read and write'],
        ]),
        tags('open', 'with', 'csv', 'json', 'encoding', 'pathlib'),
    ),
    example(
        pyrun("""
import csv, json
from pathlib import Path

folder = Path("upvanta_demo")
folder.mkdir(exist_ok=True)

# Write and read CSV
rows = [{"id": 1, "name": "Asha", "city": "Pune"},
        {"id": 2, "name": "Rohit", "city": "Mumbai"}]
csv_path = folder / "students.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name", "city"])
    writer.writeheader()
    writer.writerows(rows)

with open(csv_path, encoding="utf-8") as f:
    for row in csv.DictReader(f):          # each row is a dict of STRINGS
        print(row)

# Write and read JSON
json_path = folder / "students.json"
json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
loaded = json.loads(json_path.read_text(encoding="utf-8"))
print(loaded[1]["name"], type(loaded[0]["id"]))

# Line-by-line reading (memory-friendly)
with open(csv_path, encoding="utf-8") as f:
    print(sum(1 for _ in f) - 1, "data rows")

print(sorted(p.name for p in folder.glob("*.*")))
"""),
        title='Example'),
    interview(
        ul('Always pass <code>encoding="utf-8"</code> — the default differs between Windows and Linux.',
           'Use <code>newline=""</code> when writing CSV on Windows, otherwise blank lines appear between rows.',
           'csv.DictReader returns everything as <strong>strings</strong> — convert types explicitly.',
           '<code>f.read()</code> loads the whole file into memory; iterate the file object for large files.',
           'For JSON Lines (one JSON object per line — common for logs and Kafka dumps) read line by line with <code>json.loads(line)</code>.',
           'Use <code>pathlib.Path</code> instead of string concatenation for paths.'),
        title='Points Interviewers Look For'),
    crossq(
        ('json.load vs json.loads?',
         '<code>json.load(f)</code> reads from a file object; <code>json.loads(s)</code> parses a string. Similarly <code>json.dump(obj, f)</code> / <code>json.dumps(obj)</code>.'),
        ('When would you use pandas instead of the csv module?',
         'For analysis and transformation of tabular data that fits in memory. The csv module is lighter, streams row by row, and has no dependencies — good for simple, large or streaming files.'),
    ),
]),

])
