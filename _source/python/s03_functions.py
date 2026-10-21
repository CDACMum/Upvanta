from build import *
from python.anims import *

SECTION = dict(level='intermediate', title='Functions', questions=[

# ------------------------------------------------------------------ 16
Q('What are *args and **kwargs?', '*args & **kwargs', minutes=6, cards=[
    definition(
        defbox('<code>*args</code> collects any number of extra <strong>positional</strong> arguments into a '
               '<strong>tuple</strong>. <code>**kwargs</code> collects any number of extra <strong>keyword</strong> '
               'arguments into a <strong>dict</strong>.',
               'The names <code>args</code> and <code>kwargs</code> are only conventions — the <code>*</code> and '
               '<code>**</code> do the work. The same operators <strong>unpack</strong> sequences and dicts when calling a function.'),
        tags('*args', '**kwargs', 'Variadic', 'Unpacking', 'Keyword-only', 'Positional-only'),
    ),
    example(
        pyrun("""
def log_event(event, *args, level="INFO", **kwargs):
    print(f"[{level}] {event} args={args} kwargs={kwargs}")

log_event("load_started")
log_event("rows_loaded", 1200, 1500, level="DEBUG", table="orders", source="mysql")

# Unpacking when calling
def full_name(first, last):
    return f"{first} {last}"

parts = ["Asha", "Patil"]
info = {"first": "Rohit", "last": "Shah"}
print(full_name(*parts), "|", full_name(**info))

# Order of parameters: positional, *args, keyword-only, **kwargs
def f(a, b=2, *args, flag=False, **kwargs):
    return a, b, args, flag, kwargs
print(f(1, 3, 4, 5, flag=True, x=9))
"""),
        title='Example'),
    explanation(
        p('<strong>Parameter order rule</strong>: <code>def f(pos_only, /, normal, *args, kw_only, **kwargs)</code>'),
        ul('Parameters after <code>*args</code> (or a bare <code>*</code>) are <strong>keyword-only</strong>.',
           'Parameters before <code>/</code> (Python 3.8+) are <strong>positional-only</strong>.',
           'Common use: wrapper functions and decorators that forward everything — <code>return func(*args, **kwargs)</code>.'),
    ),
    crossq(
        ('Why use a bare * in a function signature?',
         '<code>def connect(host, *, timeout, retries)</code> forces callers to write <code>timeout=30</code> explicitly, which makes calls self-documenting and prevents argument-order mistakes.'),
        ('What is the type of args and kwargs inside the function?',
         '<code>args</code> is a tuple, <code>kwargs</code> is a dict.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is the mutable default argument problem?', 'Mutable Default Argument Trap', minutes=5, cards=[
    definition(
        defbox('Default argument values are evaluated <strong>once</strong>, when the function is <strong>defined</strong> '
               '— not each time it is called. If the default is a mutable object (list, dict, set), every call that uses '
               'the default <strong>shares the same object</strong>, and changes accumulate between calls.'),
        tags('Default Arguments', 'Mutable', 'None Sentinel', 'Gotcha'),
    ),
    mutable_default(),
    example(
        pyrun("""
def add_record(record, batch=[]):        # BUG: one shared list
    batch.append(record)
    return batch

print(add_record("r1"))
print(add_record("r2"))                  # expected ['r2'] ...

def add_record_fixed(record, batch=None):
    if batch is None:                    # create a new list on each call
        batch = []
    batch.append(record)
    return batch

print(add_record_fixed("r1"))
print(add_record_fixed("r2"))
print(add_record.__defaults__)           # the shared default lives here
"""),
        title='Example: The Bug and the Fix'),
    crossq(
        ('Is the same true for default values like datetime.now()?',
         'Yes. <code>def log(ts=datetime.now())</code> fixes the timestamp at definition time; every call gets the same value. Use <code>ts=None</code> and compute inside.'),
        ('Is this behaviour ever useful?',
         'Occasionally as a simple cache (<code>def f(x, _cache={})</code>), but <code>functools.lru_cache</code> is clearer.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What are lambda, map, filter and reduce?', 'lambda, map, filter, reduce', minutes=6, cards=[
    definition(
        defbox('A <strong>lambda</strong> is a small anonymous function written as a single expression: '
               '<code>lambda x: x * 2</code>.',
               '<strong>map(f, it)</strong> applies f to every item; <strong>filter(f, it)</strong> keeps items where f is '
               'truthy; <strong>functools.reduce(f, it)</strong> combines items into one value. map and filter return '
               '<strong>lazy iterators</strong>.'),
        tags('lambda', 'map', 'filter', 'reduce', 'Functional Programming', 'Lazy'),
    ),
    example(
        pyrun("""
from functools import reduce

prices = [120, 450, 80, 999]

with_gst = list(map(lambda p: round(p * 1.18, 2), prices))
expensive = list(filter(lambda p: p > 100, prices))
total = reduce(lambda acc, p: acc + p, prices, 0)

print(with_gst)
print(expensive)
print(total, sum(prices))

# Usually clearer as comprehensions
print([round(p * 1.18, 2) for p in prices])
print([p for p in prices if p > 100])

# lambda is most useful as a key function
employees = [("Asha", 72000), ("Rohit", 65000), ("Meera", 91000)]
print(sorted(employees, key=lambda e: e[1], reverse=True)[0])
"""),
        title='Example'),
    crossq(
        ('Limitations of lambda?',
         'Only a single expression — no statements, no assignments (except the walrus operator), no annotations, and no name in tracebacks. For anything non-trivial, use <code>def</code>.'),
        ('Where do you see map/filter/reduce in data engineering?',
         'They are the core idea behind MapReduce and Spark RDDs: <code>rdd.map(...)</code>, <code>rdd.filter(...)</code>, <code>rdd.reduceByKey(lambda a, b: a + b)</code>.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('Explain variable scope: LEGB rule, global and nonlocal', 'Scope: LEGB, global, nonlocal', minutes=6, cards=[
    definition(
        defbox('When Python looks up a name it searches four scopes in order — the <strong>LEGB rule</strong>:'),
        table(['Scope', 'Meaning'], [
            ['L — Local', 'Names assigned inside the current function'],
            ['E — Enclosing', 'Names in enclosing (outer) functions, for nested functions'],
            ['G — Global', 'Names at the top level of the module'],
            ['B — Built-in', 'Names pre-defined by Python: len, print, range…'],
        ]),
        tags('LEGB', 'Scope', 'global', 'nonlocal', 'UnboundLocalError'),
    ),
    legb_anim(),
    example(
        pyrun("""
counter = 0                      # global

def increment():
    global counter               # without this: UnboundLocalError
    counter += 1

increment(); increment()
print("global counter:", counter)

def make_counter():
    count = 0                    # enclosing
    def step():
        nonlocal count           # modify the enclosing variable
        count += 1
        return count
    return step

c = make_counter()
print(c(), c(), c())

def broken():
    total = total + 1            # assignment makes 'total' local -> error
try:
    total = 5
    broken()
except UnboundLocalError as e:
    print("UnboundLocalError:", e)
"""),
        title='Example'),
    crossq(
        ('Why is using global variables discouraged?',
         'Any function can change them, so behaviour depends on hidden state — hard to test, debug and run in parallel. Pass values as parameters and return results instead.'),
        ('What happens if you name a variable "list" or "sum"?',
         'It shadows the built-in in that scope; later calls like <code>list(x)</code> fail with "object is not callable". Avoid built-in names.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What are first-class functions and closures?', 'Closures', minutes=6, cards=[
    definition(
        defbox('Functions in Python are <strong>first-class objects</strong>: they can be assigned to variables, passed as '
               'arguments, returned from other functions and stored in data structures.',
               'A <strong>closure</strong> is an inner function that <strong>remembers variables from its enclosing scope</strong> '
               'even after the outer function has finished executing.'),
        tags('First-class Functions', 'Closure', 'Higher-order Function', 'Factory Function', '__closure__'),
    ),
    example(
        pyrun("""
def make_validator(min_val, max_val):          # factory
    def validate(x):                           # closure over min_val, max_val
        return min_val <= x <= max_val
    return validate

valid_marks = make_validator(0, 100)
valid_cgpa = make_validator(0, 10)

print(valid_marks(85), valid_marks(120), valid_cgpa(8.6))
print([c.cell_contents for c in valid_marks.__closure__])

# Functions stored in a dict -> simple dispatch table
transforms = {"upper": str.upper, "strip": str.strip, "title": str.title}
for name in ["strip", "title"]:
    print(name, "->", repr(transforms[name]("  asha patil ")))
"""),
        title='Example'),
    crossq(
        ('What is the late-binding closure gotcha?',
         '<code>[lambda: i for i in range(3)]</code> — all three return 2, because they look up <code>i</code> when called, '
         'not when created. Fix with a default argument: <code>lambda i=i: i</code>.'),
        ('Closures vs classes?',
         'A closure is a lightweight way to keep a little state with one function. When you need several methods or a lot of state, a class is clearer.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('What are decorators? Write a timing / retry decorator', 'Decorators', minutes=8, cards=[
    definition(
        defbox('A <strong>decorator</strong> is a function that takes a function and returns a new function that adds '
               'behaviour — logging, timing, retries, caching, access checks — <strong>without changing the original code</strong>.',
               '<code>@my_decorator</code> above a function is shorthand for <code>func = my_decorator(func)</code>.'),
        tags('Decorator', '@', 'functools.wraps', 'Higher-order Function', 'Retry', 'lru_cache'),
    ),
    decorator_anim(),
    example(
        pyrun("""
import functools, time

def timer(func):
    @functools.wraps(func)                  # keep name & docstring
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.3f}s")
        return result
    return wrapper

@timer
def load_rows(n):
    time.sleep(0.05)
    return n

print(load_rows(500), load_rows.__name__)
"""),
        pyrun("""
import functools, time

def retry(times=3, delay=0.01, exceptions=(Exception,)):    # decorator WITH arguments
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"attempt {attempt} failed: {e}")
                    if attempt == times:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

calls = {"n": 0}

@retry(times=3, exceptions=(ConnectionError,))
def fetch_page():
    calls["n"] += 1
    if calls["n"] < 3:
        raise ConnectionError("API timeout")
    return {"status": 200}

print(fetch_page())
""", 'Retry decorator with arguments — very common in pipelines'),
        title='Example'),
    explanation(
        ul('<strong>functools.wraps</strong> copies <code>__name__</code>, <code>__doc__</code> etc. from the original — without it, every decorated function looks like "wrapper" in logs.',
           '<strong>Decorator with arguments</strong> = three levels: <code>retry(times)</code> → <code>decorator(func)</code> → <code>wrapper(*args)</code>.',
           '<strong>Built-in decorators</strong>: <code>@staticmethod</code>, <code>@classmethod</code>, <code>@property</code>, '
           '<code>@functools.lru_cache</code>, <code>@dataclass</code>.',
           '<strong>Stacking</strong>: <code>@a @b def f</code> means <code>f = a(b(f))</code> — the one closest to the function is applied first.',
           '<strong>Airflow</strong> uses decorators in the TaskFlow API: <code>@dag</code>, <code>@task</code>.'),
        title='Key Points'),
    crossq(
        ('Can a class be used as a decorator?',
         'Yes — any callable works. A class with <code>__init__(self, func)</code> and <code>__call__(self, *args, **kwargs)</code> can decorate functions and keep state (e.g. call counts) in attributes.'),
        ('What does @lru_cache do?',
         'Memoises results keyed by arguments: <code>@functools.lru_cache(maxsize=128)</code>. Repeated calls with the same arguments return the cached value instantly. Arguments must be hashable.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('Is Python pass-by-value or pass-by-reference?', 'Pass-by-Object-Reference', minutes=5, cards=[
    definition(
        defbox('Neither exactly. Python uses <strong>pass-by-object-reference</strong> (also called call-by-sharing): the '
               'function receives a reference to the same object the caller passed.',
               'If the object is <strong>mutable</strong> and the function <strong>mutates</strong> it, the caller sees the '
               'change. If the function <strong>rebinds</strong> the parameter name to a new object, the caller is not affected.'),
        tags('Pass by Object Reference', 'Call by Sharing', 'Mutation', 'Rebinding'),
    ),
    example(
        pyrun("""
def mutate(items):
    items.append(99)          # changes the caller's object

def rebind(items):
    items = [0, 0]            # local name now points elsewhere

def bump(n):
    n += 1                    # ints are immutable -> new object, local only

data = [1, 2]
mutate(data); print(data)
rebind(data); print(data)

x = 10
bump(x); print(x)
"""),
        title='Example'),
    crossq(
        ('How do you prevent a function from modifying your list?',
         'Pass a copy (<code>f(list(data))</code> or <code>f(tuple(data))</code>), or write the function to return a new list instead of mutating its input — the preferred, side-effect-free style.'),
    ),
]),

])
