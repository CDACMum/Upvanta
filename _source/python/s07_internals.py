from build import *
from python.anims import *

SECTION = dict(level='advanced', title='Internals & Performance', questions=[

# ------------------------------------------------------------------ 38
Q('How does Python manage memory? Explain reference counting and garbage collection', 'Memory Management & GC', minutes=7, cards=[
    definition(
        defbox('CPython manages memory automatically using two mechanisms:'),
        ul('<strong>Reference counting</strong> — every object tracks how many references point to it. When the count '
           'drops to zero, the object is freed <strong>immediately</strong>.',
           '<strong>Cyclic garbage collector</strong> — finds groups of objects that reference each other (cycles) but are '
           'no longer reachable, which reference counting alone can never free. It is generational (generations 0, 1, 2): '
           'young objects are checked most often.'),
        p('All objects live on a private heap managed by Python; small objects use a fast allocator called '
          '<strong>pymalloc</strong>.'),
        tags('Reference Counting', 'Garbage Collector', 'gc module', 'Reference Cycle', 'Generations', 'weakref'),
    ),
    example(
        pyrun("""
import sys, gc

data = []
print(sys.getrefcount(data))      # +1 for the temporary argument reference
alias = data
print(sys.getrefcount(data))
del alias
print(sys.getrefcount(data))

class Node:
    def __init__(self):
        self.other = None

a, b = Node(), Node()
a.other, b.other = b, a           # reference cycle
del a, b                          # refcounts never reach 0 by themselves
print("collected:", gc.collect() >= 2)
print("thresholds:", gc.get_threshold())
"""),
        title='Example'),
    crossq(
        ('What does "del x" actually do?',
         'It deletes the <strong>name</strong>, decrementing the object\'s reference count. The object is freed only if no other references remain.'),
        ('What causes memory leaks in Python?',
         'Objects kept alive unintentionally: growing global lists/caches, closures holding big objects, unbounded <code>lru_cache</code>, and reference cycles involving objects with <code>__del__</code> in old code. Tools: <code>tracemalloc</code>, <code>objgraph</code>, memory_profiler.'),
        ('Why might a long-running process not give memory back to the OS?',
         'Freed memory often goes back to Python\'s own allocator pools for reuse rather than to the OS, so the process size can stay high even after objects are freed.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('What is the GIL (Global Interpreter Lock)?', 'The GIL', minutes=7, cards=[
    definition(
        defbox('The <strong>Global Interpreter Lock</strong> is a mutex in CPython that allows only <strong>one thread to '
               'execute Python bytecode at a time</strong>, even on a multi-core machine. It exists mainly because '
               'reference counting is not thread-safe without it.'),
        table(['Workload', 'Effect of the GIL', 'Use'], [
            ['I/O-bound (API calls, DB queries, file/network)', 'Little impact — the GIL is released while waiting for I/O', 'threading or asyncio'],
            ['CPU-bound pure Python (parsing, loops, maths)', 'Threads cannot run in parallel — no speed-up', 'multiprocessing / ProcessPoolExecutor'],
            ['NumPy, pandas, compression, many C extensions', 'C code can release the GIL', 'Often parallel already'],
        ]),
        tags('GIL', 'CPython', 'Threads', 'CPU-bound', 'I/O-bound', 'Free-threaded Python'),
    ),
    gil_anim(),
    example(
        pyrun("""
import time
from concurrent.futures import ThreadPoolExecutor

def cpu_task(n=2_000_000):
    return sum(i * i for i in range(n))

def io_task(_=None):
    time.sleep(0.2)                    # simulates waiting for an API

for name, fn in [("CPU", cpu_task), ("I/O", io_task)]:
    t = time.perf_counter()
    for _ in range(4):
        fn()
    seq = time.perf_counter() - t

    t = time.perf_counter()
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda _: fn(), range(4)))
    par = time.perf_counter() - t
    print(f"{name}: sequential {seq:.2f}s, 4 threads {par:.2f}s")
"""),
        note('I/O work speeds up about 4× with threads; CPU work does not, because of the GIL.'),
        title='Example: Threads Help I/O, Not CPU'),
    crossq(
        ('Is the GIL being removed?',
         'Python 3.13 introduced an <strong>experimental free-threaded build</strong> (PEP 703) without the GIL, and it is '
         'being stabilised in later releases. The default CPython build still has the GIL.'),
        ('Does the GIL make my code thread-safe?',
         'No. It protects interpreter internals, but a thread can be switched out between bytecode instructions, so '
         '<code>counter += 1</code> from many threads can still lose updates. Use <code>threading.Lock</code>.'),
        ('Does the GIL affect PySpark?',
         'Not for DataFrame operations — they run in the JVM across executors. It matters only for Python UDFs and driver-side Python code.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('Multithreading vs multiprocessing vs asyncio — when to use which?', 'Threading vs Multiprocessing vs asyncio', minutes=8, cards=[
    definition(
        table(['Approach', 'How it works', 'Best for', 'Watch out for'], [
            ['threading', 'Several OS threads in one process, sharing memory; GIL allows one at a time to run Python', 'I/O-bound: many API/DB calls, file transfers', 'Race conditions; no CPU speed-up'],
            ['multiprocessing', 'Separate processes, each with its own interpreter and GIL', 'CPU-bound: parsing, transformations, hashing', 'Higher memory; data must be pickled between processes'],
            ['asyncio', 'Single thread, event loop switching between coroutines at <code>await</code>', 'Very many concurrent I/O tasks (thousands of HTTP calls)', 'Needs async libraries (aiohttp, asyncpg); one blocking call stalls everything'],
        ]),
        tags('threading', 'multiprocessing', 'asyncio', 'concurrent.futures', 'async/await', 'Concurrency vs Parallelism'),
    ),
    example(
        pyrun("""
import asyncio, time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

def checksum(n):                       # CPU-bound
    return sum(i % 7 for i in range(n))

def fetch(i):                          # I/O-bound (simulated)
    time.sleep(0.1)
    return i

async def fetch_async(i):
    await asyncio.sleep(0.1)           # non-blocking wait
    return i

if __name__ == "__main__":
    t = time.perf_counter()
    with ProcessPoolExecutor() as ex:
        print(sum(ex.map(checksum, [1_000_000] * 4)))
    print(f"processes: {time.perf_counter() - t:.2f}s")

    t = time.perf_counter()
    with ThreadPoolExecutor(max_workers=20) as ex:
        print(len(list(ex.map(fetch, range(20)))))
    print(f"threads (20 x 0.1s waits): {time.perf_counter() - t:.2f}s")

    async def main():
        return await asyncio.gather(*(fetch_async(i) for i in range(100)))
    t = time.perf_counter()
    print(len(asyncio.run(main())))
    print(f"asyncio (100 x 0.1s waits): {time.perf_counter() - t:.2f}s")
"""),
        title='Example: concurrent.futures and asyncio'),
    explanation(
        hl('<strong>Concurrency</strong> = dealing with many tasks at once (interleaving). <strong>Parallelism</strong> = '
           'doing many tasks at the same instant on multiple cores. Threads/asyncio give concurrency; processes give parallelism.', 'Concurrency vs parallelism'),
        p('In data engineering, heavy parallel processing is usually delegated to distributed engines (Spark, Dask, the '
          'database itself). Python-level concurrency is mostly used for I/O: calling APIs, copying files to S3, running many small queries.'),
        title='Concepts'),
    crossq(
        ('Why is the if __name__ == "__main__" guard required with multiprocessing?',
         'On Windows and macOS, child processes are started with "spawn", which re-imports the main module. Without the guard, each child would start new children recursively.'),
        ('Thread pool size for I/O tasks?',
         'Larger than CPU count is fine (e.g. 10–50) because threads mostly wait. Respect the target system\'s limits (API rate limits, DB connections).'),
    ),
]),

# ------------------------------------------------------------------ 41
Q('What is the time complexity of common list, dict and set operations?', 'Time Complexity of Built-ins', minutes=6, cards=[
    definition(
        table(['Operation', 'list', 'dict', 'set'], [
            ['Access by index / key', 'O(1)', 'O(1) avg', '—'],
            ['x in collection', '<strong>O(n)</strong>', 'O(1) avg', 'O(1) avg'],
            ['Append / add', 'O(1) amortised', 'O(1) avg', 'O(1) avg'],
            ['Insert / delete at start', '<strong>O(n)</strong>', '—', '—'],
            ['Delete by key / value', 'O(n)', 'O(1) avg', 'O(1) avg'],
            ['pop() from end', 'O(1)', '—', '—'],
            ['Sort', 'O(n log n)', '—', '—'],
            ['Iterate', 'O(n)', 'O(n)', 'O(n)'],
            ['min / max / sum', 'O(n)', 'O(n)', 'O(n)'],
        ]),
        note('deque gives O(1) append/pop at both ends; heapq gives O(log n) push/pop for priority queues; bisect gives O(log n) search in a sorted list.'),
        tags('Big-O', 'Time Complexity', 'list', 'dict', 'set', 'deque', 'heapq'),
    ),
    example(
        pyrun("""
import time

ids_list = list(range(200_000))
ids_set = set(ids_list)
lookups = range(199_000, 200_000)       # 1,000 lookups near the end

t = time.perf_counter(); hits = sum(1 for x in lookups if x in ids_list); a = time.perf_counter() - t
t = time.perf_counter(); hits = sum(1 for x in lookups if x in ids_set);  b = time.perf_counter() - t
print(f"list: {a:.3f}s  set: {b:.5f}s  -> set is ~{a / b:,.0f}x faster")
"""),
        title='Example: Membership Test'),
    crossq(
        ('Why is list.append O(1) "amortised"?',
         'Lists over-allocate. Most appends just fill a spare slot; occasionally the list must grow and copy everything (O(n)), but averaged over many appends the cost per append is constant.'),
        ('Worst case of dict lookup?',
         'O(n) if many keys collide, but this practically never happens with built-in types thanks to good hash functions and hash randomisation for strings.'),
    ),
]),

# ------------------------------------------------------------------ 42
Q('What are modules and packages? What does if __name__ == "__main__" do?', 'Modules, Packages & __main__', minutes=6, cards=[
    definition(
        defbox('A <strong>module</strong> is a single <code>.py</code> file. A <strong>package</strong> is a directory of '
               'modules, usually with an <code>__init__.py</code>, that can be imported as a unit.',
               'Every module has a <code>__name__</code>. When a file is <strong>run directly</strong>, its '
               '<code>__name__</code> is <code>"__main__"</code>; when it is <strong>imported</strong>, it is the module\'s '
               'name. The guard <code>if __name__ == "__main__":</code> runs code only when the file is executed as a script.'),
        tags('Module', 'Package', '__init__.py', '__name__', 'import', 'sys.path'),
    ),
    example(
        py("""
etl_project/
├── pyproject.toml
├── etl/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   └── load.py
└── tests/
    └── test_transform.py
""", 'Typical project layout'),
        py("""
# etl/transform.py
def clean_city(city: str) -> str:
    return city.strip().title()

if __name__ == "__main__":          # quick manual test; NOT run on import
    print(clean_city("  navi mumbai "))
""", 'transform.py'),
        py("""
# elsewhere
from etl.transform import clean_city      # absolute import (preferred)
import etl.load as load
from . import extract                     # relative import (inside the package)
""", 'Importing'),
        title='Example'),
    explanation(
        ul('Python finds modules by searching <code>sys.path</code>: the script\'s directory, PYTHONPATH, then site-packages.',
           'A module is executed only on its <strong>first</strong> import; later imports reuse the cached object in <code>sys.modules</code>.',
           'Avoid <code>from module import *</code> — it hides where names come from and can overwrite existing names.',
           '<strong>Circular imports</strong> (a imports b, b imports a) cause partially-initialised modules; fix by restructuring or importing inside a function.'),
        title='How Imports Work'),
    crossq(
        ('Is __init__.py still required?',
         'Since Python 3.3, directories without it are "namespace packages" and can be imported. A regular package with __init__.py is still recommended for normal projects; the file can also expose a clean public API.'),
        ('How do you run a module inside a package?',
         '<code>python -m etl.transform</code> from the project root — this sets up imports correctly, unlike <code>python etl/transform.py</code>.'),
    ),
]),

# ------------------------------------------------------------------ 43
Q('What are virtual environments and how do you manage dependencies?', 'Virtual Environments & pip', minutes=5, cards=[
    definition(
        defbox('A <strong>virtual environment</strong> is an isolated Python installation for one project, with its own '
               '<code>site-packages</code>. It prevents version conflicts between projects (project A needs pandas 1.5, '
               'project B needs pandas 2.2) and keeps the system Python clean.'),
        tags('venv', 'pip', 'requirements.txt', 'pyproject.toml', 'conda', 'poetry', 'uv'),
    ),
    example(
        code("""
# Create and activate
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.venv\\Scripts\\activate             # Windows

# Install and freeze
pip install pandas==2.2.2 sqlalchemy requests
pip freeze > requirements.txt

# Recreate elsewhere (CI, server, teammate)
pip install -r requirements.txt

deactivate
""", 'Terminal', 'fa-terminal'),
        title='Example'),
    comparison(
        table(['Tool', 'Use'], [
            ['venv + pip', 'Built-in, simple, universal'],
            ['pip-tools / poetry / uv', 'Lock files with exact versions of all transitive dependencies; uv is very fast'],
            ['conda', 'Also manages non-Python dependencies (CUDA, compilers) — common in data science'],
            ['Docker', 'Freezes the whole OS + Python + packages — standard for deploying pipelines'],
        ]),
        title='Tools'),
    crossq(
        ('Why pin exact versions in production?',
         'An unpinned dependency can release a breaking version overnight and fail a scheduled pipeline. Pin versions (or use a lock file) and upgrade deliberately.'),
        ('Should the .venv folder be committed to Git?',
         'No. Commit <code>requirements.txt</code> / <code>pyproject.toml</code> and the lock file; add <code>.venv/</code> to .gitignore.'),
    ),
]),

])
