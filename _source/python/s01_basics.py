from build import *
from python.anims import *

SECTION = dict(level='beginner', title='Python Basics', questions=[

# ------------------------------------------------------------------ 1
Q('What is Python? What are its key features?', 'What is Python', minutes=5, cards=[
    definition(
        defbox('<strong>Python</strong> is a high-level, general-purpose, <strong>interpreted</strong> programming '
               'language created by <strong>Guido van Rossum</strong> and first released in 1991. It emphasises readable '
               'code — indentation is part of the syntax — and supports procedural, object-oriented and functional styles.',
               'In data engineering, Python is the glue language: PySpark jobs, Airflow DAGs, ETL scripts, API '
               'ingestion, data-quality checks and ML pipelines are all commonly written in it.'),
        tags('Python', 'Interpreted', 'Dynamically Typed', 'High-level', 'Open Source', 'Guido van Rossum'),
    ),
    explanation(
        table(['Feature', 'What it means'], [
            ['Interpreted', 'No separate compile step for the programmer; code is run by the interpreter'],
            ['Dynamically typed', 'Variable types are decided at runtime — no type declarations'],
            ['Strongly typed', 'No silent conversions: <code>"5" + 5</code> raises TypeError'],
            ['High-level', 'Memory management, garbage collection handled automatically'],
            ['Multi-paradigm', 'Procedural, object-oriented and functional programming'],
            ['Batteries included', 'Large standard library: json, csv, datetime, re, os, logging, sqlite3…'],
            ['Huge ecosystem', 'pandas, NumPy, PySpark, requests, SQLAlchemy, Airflow, scikit-learn'],
            ['Portable', 'Same code runs on Windows, Linux and macOS'],
        ]),
    ),
    example(
        pyrun("""
import sys
print("Python version:", sys.version.split()[0])

# Strongly typed: no silent string/number mixing
try:
    print("5" + 5)
except TypeError as e:
    print("TypeError:", e)

print("5" + str(5), int("5") + 5)
"""),
        title='Example'),
    crossq(
        ('Is Python compiled or interpreted?',
         'Both, in a sense. CPython first <strong>compiles</strong> source code to <strong>bytecode</strong> (.pyc), then the '
         'Python Virtual Machine <strong>interprets</strong> that bytecode. It is called interpreted because there is no '
         'separate ahead-of-time compile step producing machine code.'),
        ('What are the disadvantages of Python?',
         'Slower than C/Java for CPU-bound code, the GIL limits multi-threaded CPU work, higher memory use, and runtime '
         'type errors. In data engineering this is mitigated because heavy work runs inside optimised engines (NumPy, Spark, databases).'),
        ('Python 2 vs Python 3?',
         'Python 2 reached end of life in January 2020. Key Python 3 differences: <code>print()</code> is a function, '
         'strings are Unicode by default, <code>/</code> is true division (<code>3/2 = 1.5</code>), and <code>range</code> is lazy.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('How does Python code get executed? (Bytecode, PVM, CPython)', 'How Python Code Runs', minutes=6, cards=[
    definition(
        defbox('When you run <code>python script.py</code>, the source code is first <strong>compiled into bytecode</strong> '
               '— a low-level, platform-independent instruction set. The bytecode is then executed by the '
               '<strong>Python Virtual Machine (PVM)</strong>, which is the interpreter loop inside CPython.'),
        tags('CPython', 'Bytecode', 'PVM', '.pyc', '__pycache__', 'dis module'),
    ),
    visual(svg("""
<svg width="740" height="160" viewBox="0 0 740 160" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="740" height="160" fill="#1e293b"/>
  <defs><marker id="pa" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/></marker></defs>
  <g text-anchor="middle" font-size="13">
    <rect x="20" y="45" width="130" height="64" rx="10" fill="#334155" stroke="#94a3b8"/><text x="85" y="73" fill="#f1f5f9" font-weight="bold">script.py</text><text x="85" y="93" fill="#94a3b8" font-size="11">source code</text>
    <rect x="200" y="45" width="130" height="64" rx="10" fill="#0ea5e9" opacity="0.25" stroke="#0ea5e9"/><text x="265" y="73" fill="#f1f5f9" font-weight="bold">Compiler</text><text x="265" y="93" fill="#cbd5e1" font-size="11">parse → AST</text>
    <rect x="380" y="45" width="130" height="64" rx="10" fill="#f59e0b" opacity="0.25" stroke="#f59e0b"/><text x="445" y="73" fill="#f1f5f9" font-weight="bold">Bytecode</text><text x="445" y="93" fill="#cbd5e1" font-size="11">.pyc in __pycache__</text>
    <rect x="560" y="45" width="160" height="64" rx="10" fill="#10b981" opacity="0.25" stroke="#10b981"/><text x="640" y="73" fill="#f1f5f9" font-weight="bold">Python VM (PVM)</text><text x="640" y="93" fill="#cbd5e1" font-size="11">executes instructions</text>
    <g stroke="#94a3b8" stroke-width="2" marker-end="url(#pa)"><line x1="150" y1="77" x2="195" y2="77"/><line x1="330" y1="77" x2="375" y2="77"/><line x1="510" y1="77" x2="555" y2="77"/></g>
    <text x="370" y="140" fill="#94a3b8" font-size="12">Compilation happens automatically each time; cached .pyc files skip it for unchanged imported modules</text>
  </g>
</svg>""", 'Source → bytecode → Python Virtual Machine')),
    example(
        pyrun("""
import dis

def add_tax(price):
    return price * 1.18

dis.dis(add_tax)   # show the bytecode instructions
"""),
        note('The exact instruction names vary between Python versions — bytecode is an internal detail of CPython.'),
        title='Example: Viewing Bytecode'),
    comparison(
        table(['Implementation', 'Written in', 'Notes'], [
            ['CPython', 'C', 'The reference and most-used implementation; has the GIL'],
            ['PyPy', 'RPython', 'JIT compiler — often several times faster for pure-Python loops'],
            ['Jython', 'Java', 'Runs on the JVM (Python 2 only)'],
            ['IronPython', 'C#', 'Runs on .NET'],
            ['MicroPython', 'C', 'For microcontrollers'],
        ]),
        title='Python Implementations'),
    crossq(
        ('Why are .pyc files created only for imported modules, not the main script?',
         'Caching helps when the same module is imported again later. The main script is compiled in memory each run; '
         'writing a .pyc for it would rarely be reused.'),
        ('Is PySpark code executed by the PVM?',
         'Partly. Your driver code runs in the Python interpreter, but DataFrame operations are sent to the JVM (Spark '
         'engine) through Py4J. Python UDFs run in Python worker processes on executors — one reason they are slower than built-in functions.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What is dynamic typing? How do variables work in Python?', 'Dynamic Typing & References', minutes=6, cards=[
    definition(
        defbox('In Python a <strong>variable is a name that refers to an object</strong>. The object has a type; the name '
               'does not. The same name can later refer to an object of a different type — this is '
               '<strong>dynamic typing</strong>.',
               'Assignment never copies data: <code>b = a</code> makes <code>b</code> refer to the <strong>same '
               'object</strong> as <code>a</code>.'),
        hl('Think of variables as <strong>labels (sticky notes)</strong> attached to objects, not as boxes that contain values.', 'Mental model'),
        tags('Dynamic Typing', 'Names', 'References', 'id()', 'type()', 'Strong Typing'),
    ),
    names_refs(),
    example(
        pyrun("""
x = 10
print(type(x))
x = "ten"            # same name, now refers to a str
print(type(x))

a = [1, 2, 3]
b = a                # b refers to the SAME list
b.append(4)
print("a =", a)      # a sees the change
print("same object?", a is b)

c = list(a)          # a new list (a copy)
c.append(5)
print("a =", a, " c =", c)
"""),
        title='Example'),
    crossq(
        ('What is the difference between dynamic and static typing?',
         'Static typing (Java, C) checks types at compile time and variables have fixed declared types. Dynamic typing '
         '(Python) checks types at runtime, so type errors appear only when that line runs. Type hints + tools like mypy add optional static checking.'),
        ('What does id() return?',
         'A unique integer identifying the object during its lifetime. In CPython it is the object\'s memory address. '
         'Two names with the same <code>id</code> refer to the same object.'),
        ('Python is dynamically typed — is it also weakly typed?',
         'No. Python is <strong>dynamically</strong> but <strong>strongly</strong> typed: it does not silently convert '
         'between unrelated types (<code>"5" + 5</code> fails). JavaScript, in contrast, is weakly typed (<code>"5" + 5 = "55"</code>).'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What is the difference between mutable and immutable objects?', 'Mutable vs Immutable', minutes=7, cards=[
    definition(
        defbox('A <strong>mutable</strong> object can be changed in place after it is created. An '
               '<strong>immutable</strong> object cannot — any "change" creates a new object.'),
        table(['Immutable', 'Mutable'], [
            ['int, float, complex, bool', 'list'],
            ['str', 'dict'],
            ['tuple', 'set'],
            ['frozenset', 'bytearray'],
            ['bytes, None', 'most user-defined class instances'],
        ]),
        tags('Mutable', 'Immutable', 'Hashable', 'In-place', 'tuple', 'frozenset'),
    ),
    example(
        pyrun("""
s = "data"
print(id(s) == id(s.upper()))   # upper() returns a NEW string
s2 = s
s += "eng"                       # creates a new object; s2 still the old one
print(s, s2)

nums = [1, 2]
alias = nums
nums += [3]                      # list += extends IN PLACE
print(nums, alias, nums is alias)

t = (1, [10, 20])                # tuple is immutable...
t[1].append(30)                  # ...but the list inside it is mutable
print(t)

try:
    t[0] = 99
except TypeError as e:
    print("TypeError:", e)
"""),
        title='Example'),
    explanation(
        p('<strong>Why it matters:</strong>'),
        ul('<strong>Dictionary keys and set elements must be hashable</strong> — in practice, immutable. '
           'A tuple can be a dict key; a list cannot.',
           '<strong>Shared references</strong>: passing a list to a function lets the function modify the caller\'s list.',
           '<strong>Mutable default arguments</strong> are shared between calls (see question 17).',
           '<strong>Performance</strong>: building a string with <code>+=</code> in a loop creates many new objects — use <code>"".join(parts)</code>.',
           '<strong>Thread safety</strong>: immutable objects can be shared between threads safely.'),
        title='Why It Matters'),
    crossq(
        ('Is a tuple containing a list hashable?',
         'No. A tuple is hashable only if all its elements are hashable. <code>hash((1, [2]))</code> raises TypeError.'),
        ('Why are strings immutable in Python?',
         'So they can be hashed and used as dict keys, safely shared and cached (interning), and used across threads without locks.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What are Python\'s built-in data types?', 'Built-in Data Types', minutes=6, cards=[
    definition(
        table(['Category', 'Types', 'Example'], [
            ['Numeric', 'int, float, complex', '<code>42</code>, <code>3.14</code>, <code>2+3j</code>'],
            ['Boolean', 'bool (subclass of int)', '<code>True</code>, <code>False</code>'],
            ['Text', 'str', '<code>"PGCP-BDA"</code>'],
            ['Sequence', 'list, tuple, range', '<code>[1, 2]</code>, <code>(1, 2)</code>, <code>range(5)</code>'],
            ['Mapping', 'dict', '<code>{"id": 101}</code>'],
            ['Set', 'set, frozenset', '<code>{1, 2, 3}</code>'],
            ['Binary', 'bytes, bytearray, memoryview', '<code>b"abc"</code>'],
            ['None', 'NoneType', '<code>None</code>'],
        ]),
        tags('int', 'float', 'str', 'list', 'tuple', 'dict', 'set', 'None', 'bool'),
    ),
    example(
        pyrun("""
print(type(True), True + True)          # bool is a subclass of int
print(10 / 4, 10 // 4, 10 % 4, 2 ** 10)  # true div, floor div, modulo, power
print(0.1 + 0.2)                         # floating-point representation error
print(round(0.1 + 0.2, 2))

from decimal import Decimal
print(Decimal("0.1") + Decimal("0.2"))   # exact decimal arithmetic for money

big = 2 ** 100                           # ints have arbitrary precision
print(big)
print(int("101", 2), hex(255), float("nan") == float("nan"))
"""),
        title='Example'),
    interview(
        warn('Never use <code>float</code> for money. <code>0.1 + 0.2 != 0.3</code>. Use <code>decimal.Decimal</code> in '
             'Python and <code>DECIMAL(p, s)</code> in SQL.', 'Data engineering gotcha'),
    ),
    crossq(
        ('What is the difference between None, 0, "" and False?',
         'All are <strong>falsy</strong> in an <code>if</code>, but they are different values of different types. Check '
         'for missing values with <code>x is None</code>, not <code>if not x</code> — otherwise 0 and "" are treated as missing too.'),
        ('What are truthy and falsy values?',
         'Falsy: <code>None, False, 0, 0.0, "", [], (), {}, set(), range(0)</code>. Everything else is truthy, including <code>"0"</code> and <code>[0]</code>.'),
    ),
]),

# ------------------------------------------------------------------ 6
Q('What is the difference between "is" and "=="?', 'is vs ==', minutes=5, cards=[
    definition(
        defbox('<code>==</code> checks <strong>equality of values</strong> — it calls the object\'s <code>__eq__</code> method.',
               '<code>is</code> checks <strong>identity</strong> — whether both names refer to the <strong>same object</strong> '
               'in memory (same <code>id()</code>).'),
        hl('Use <code>is</code> only for singletons: <code>x is None</code>, <code>x is True</code>. Use <code>==</code> for everything else.', 'Rule'),
        tags('is', '==', 'Identity', 'Equality', 'Interning', 'None'),
    ),
    example(
        pyrun("""
a = [1, 2, 3]
b = [1, 2, 3]
c = a
print(a == b, a is b)   # equal values, different objects
print(a == c, a is c)   # same object

x = 256
y = 256
print(x is y)           # small ints (-5..256) are cached by CPython

value = None
print(value is None)    # the correct way to test for None
"""),
        warn('Results of <code>is</code> on numbers and strings depend on CPython caching/interning and can differ in '
             'other situations or implementations. Never use <code>is</code> to compare numbers or strings.', 'Pitfall'),
        title='Example'),
    crossq(
        ('Why is "x is None" preferred over "x == None"?',
         'None is a singleton, so identity is exact and fast. <code>==</code> can be overridden by a class\'s '
         '<code>__eq__</code> (e.g. a pandas Series returns an element-wise result, not True/False).'),
        ('What is string interning?',
         'CPython reuses one object for some strings (identifiers, short literals) to save memory and speed up dictionary lookups. <code>sys.intern()</code> forces it.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('What is PEP 8? Explain indentation, comments and docstrings', 'PEP 8 & Docstrings', minutes=5, cards=[
    definition(
        defbox('<strong>PEP 8</strong> is Python\'s official <strong>style guide</strong>. PEP = Python Enhancement Proposal. '
               'It standardises naming, layout and formatting so that Python code looks consistent across teams.',
               'Python uses <strong>indentation</strong> (4 spaces by convention) to define code blocks instead of braces. '
               'Wrong indentation is a syntax error, not just a style issue.'),
        tags('PEP 8', 'Indentation', 'Docstring', 'snake_case', 'black', 'flake8'),
    ),
    explanation(
        table(['Item', 'PEP 8 convention', 'Example'], [
            ['Variables, functions', 'snake_case', '<code>total_amount</code>, <code>load_data()</code>'],
            ['Classes', 'PascalCase (CapWords)', '<code>DataLoader</code>'],
            ['Constants', 'UPPER_SNAKE_CASE', '<code>MAX_RETRIES = 3</code>'],
            ['Private (by convention)', 'leading underscore', '<code>_helper()</code>'],
            ['Indentation', '4 spaces, no tabs', ''],
            ['Line length', '79 characters (many teams use 88–120)', ''],
            ['Imports', 'At top; standard library, third-party, local — separated by blank lines', ''],
            ['Blank lines', '2 around top-level functions/classes, 1 between methods', ''],
        ]),
    ),
    example(
        pyrun('''
MAX_RETRIES = 3


def clean_name(raw_name: str) -> str:
    """Return the name stripped of spaces and in title case.

    Args:
        raw_name: Name as received from the source system.

    Returns:
        Cleaned name, e.g. "  asha PATIL " -> "Asha Patil".
    """
    # Comments explain WHY; the docstring explains WHAT the function does
    return " ".join(raw_name.split()).title()


print(clean_name("  asha   PATIL "))
print(clean_name.__doc__.splitlines()[0])
'''),
        title='Example: Well-styled Function'),
    crossq(
        ('What is the difference between a comment and a docstring?',
         'A comment (<code>#</code>) is ignored by the interpreter. A docstring is a string literal as the first '
         'statement of a module, class or function; it is stored in <code>__doc__</code> and shown by <code>help()</code> and documentation tools.'),
        ('Which tools enforce style automatically?',
         '<strong>black</strong> or <strong>ruff format</strong> (formatters), <strong>flake8</strong> / <strong>ruff</strong> / '
         '<strong>pylint</strong> (linters), <strong>isort</strong> (imports), usually run in pre-commit hooks and CI.'),
    ),
]),

])
