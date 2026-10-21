from build import *
from python.anims import *

SECTION = dict(level='basic', title='Data Structures', questions=[

# ------------------------------------------------------------------ 8
Q('What is the difference between a List and a Tuple?', 'List vs Tuple', minutes=6, cards=[
    definition(
        defbox('A <strong>list</strong> is an ordered, <strong>mutable</strong> sequence written with square brackets '
               '<code>[ ]</code>. A <strong>tuple</strong> is an ordered, <strong>immutable</strong> sequence written with '
               'parentheses <code>( )</code>.'),
        tags('list', 'tuple', 'Mutable', 'Immutable', 'Hashable', 'Unpacking'),
    ),
    comparison(
        table(['Aspect', 'List', 'Tuple'], [
            ['Syntax', '<code>[1, 2, 3]</code>', '<code>(1, 2, 3)</code> — single item needs a comma: <code>(1,)</code>'],
            ['Mutability', 'Mutable — append, remove, sort in place', 'Immutable'],
            ['Hashable / dict key', 'No', 'Yes (if all elements are hashable)'],
            ['Memory', 'More (over-allocates for growth)', 'Less'],
            ['Speed', 'Slightly slower to create', 'Slightly faster to create and iterate'],
            ['Methods', 'Many (append, extend, insert, pop, sort…)', 'Only count() and index()'],
            ['Typical use', 'Collection of similar items that changes', 'Fixed record of related values; return multiple values'],
        ]),
    ),
    example(
        pyrun("""
import sys

marks = [78, 85, 92]
marks.append(66)
print(marks)

record = ("C101", "Asha", 8.7)          # a fixed record
student_id, name, cgpa = record         # tuple unpacking
print(student_id, name, cgpa)

print(sys.getsizeof([1, 2, 3]), sys.getsizeof((1, 2, 3)))  # bytes

# Tuples can be dictionary keys, lists cannot
distance = {("Mumbai", "Pune"): 150}
print(distance[("Mumbai", "Pune")])

def min_max(values):
    return min(values), max(values)     # returns a tuple
low, high = min_max(marks)
print(low, high)
"""),
        title='Example'),
    crossq(
        ('Can you modify a tuple?',
         'Not its structure. You can create a new tuple (<code>t + (4,)</code>), convert to a list and back, or mutate a mutable object inside it.'),
        ('What is a namedtuple?',
         'A tuple subclass with named fields: <code>Point = namedtuple("Point", "x y")</code>; <code>p.x</code> is more readable than <code>p[0]</code>. It stays immutable and lightweight.'),
        ('What is extended unpacking?',
         '<code>first, *middle, last = [1, 2, 3, 4, 5]</code> gives first=1, middle=[2, 3, 4], last=5.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('Explain list operations and slicing', 'List Operations & Slicing', minutes=7, cards=[
    definition(
        defbox('<strong>Slicing</strong> extracts part of a sequence with <code>seq[start:stop:step]</code>. '
               '<code>start</code> is included, <code>stop</code> is excluded, and negative indexes count from the end. '
               'Slicing always returns a <strong>new</strong> object.'),
        tags('Slicing', 'append', 'extend', 'insert', 'pop', 'sort', 'Negative Index'),
    ),
    example(
        pyrun("""
data = [10, 20, 30, 40, 50, 60]

print(data[1:4])     # [20, 30, 40]
print(data[:3])      # first 3
print(data[-2:])     # last 2
print(data[::2])     # every 2nd element
print(data[::-1])    # reversed copy
print(data[10:20])   # out-of-range slice -> [] (no error)
"""),
        pyrun("""
items = [3, 1, 2]
items.append(4)          # add one item at the end
items.extend([5, 6])     # add many items
items.insert(0, 0)       # insert at index
print(items)

last = items.pop()       # remove & return last
items.remove(3)          # remove first occurrence of a VALUE
print(items, last)

items.sort(reverse=True) # in place, returns None
print(items)
print(sorted(["pune", "Mumbai", "delhi"], key=str.lower))

print([1, 2] * 3, 2 in items, items.index(2), items.count(2))
""", 'List methods'),
        title='Example'),
    comparison(
        table(['Pair', 'Difference'], [
            ['append vs extend', '<code>append([5, 6])</code> adds one element (a list); <code>extend([5, 6])</code> adds two elements'],
            ['remove vs pop vs del', 'remove(value) by value; pop(index) by index and returns it; <code>del lst[i]</code> by index or slice, returns nothing'],
            ['sort() vs sorted()', 'sort() changes the list in place and returns None; sorted() returns a new list and works on any iterable'],
        ]),
        title='Frequently Confused Methods'),
    crossq(
        ('Why does "x = x.sort()" give None?',
         '<code>list.sort()</code> sorts in place and returns None. Use <code>x.sort()</code> alone, or <code>x = sorted(x)</code>.'),
        ('How do you copy a list?',
         '<code>b = a[:]</code>, <code>b = list(a)</code> or <code>b = a.copy()</code> — all shallow copies. For nested lists use <code>copy.deepcopy(a)</code>.'),
        ('What is the time complexity of insert(0, x)?',
         'O(n) — every element shifts right. For frequent inserts/removals at both ends use <code>collections.deque</code> (O(1)).'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How does a Python dictionary work internally?', 'Dictionary Internals', minutes=8, cards=[
    definition(
        defbox('A <strong>dictionary</strong> stores <strong>key → value</strong> pairs and gives average '
               '<strong>O(1)</strong> lookup, insert and delete. Internally it is a <strong>hash table</strong>: Python '
               'computes <code>hash(key)</code>, uses it to pick a slot, and stores the key, value and hash there.',
               'Since Python 3.7, dictionaries are guaranteed to <strong>preserve insertion order</strong>.'),
        tags('dict', 'Hash Table', 'hash()', 'Collision', 'O(1)', 'Insertion Order'),
    ),
    dict_hash(),
    explanation(
        ul('<strong>Keys must be hashable</strong> (immutable): str, int, tuple of immutables. Lists/dicts cannot be keys.',
           '<strong>Collisions</strong> (two keys mapping to the same slot) are resolved by <em>open addressing</em> — '
           'probing other slots. Equal keys must have equal hashes, which is why <code>__eq__</code> and <code>__hash__</code> must agree.',
           'The table is <strong>resized</strong> (roughly doubled) when about two-thirds full, so occasional inserts cost O(n), but average stays O(1).',
           'Modern CPython uses a compact layout: a small index array plus a dense entries array — that is what keeps insertion order.'),
    ),
    example(
        pyrun("""
student = {"id": 101, "name": "Asha", "dept": "BDA"}

print(student["name"])
print(student.get("email"))              # None instead of KeyError
print(student.get("email", "n/a"))

student["email"] = "asha@mail.com"        # add / update
student.update({"cgpa": 8.7, "dept": "AI"})
print(list(student.keys()))

for key, value in student.items():
    print(f"{key:>6}: {value}")

removed = student.pop("email")
print(removed, "email" in student)

# setdefault / counting pattern
counts = {}
for city in ["Pune", "Mumbai", "Pune", "Delhi", "Pune"]:
    counts[city] = counts.get(city, 0) + 1
print(counts)

# merge (3.9+)
print({"a": 1} | {"b": 2})
"""),
        title='Example'),
    crossq(
        ('What happens if two keys have the same hash?',
         'That is a collision. Python probes for another slot; on lookup it compares both the hash and the key with '
         '<code>==</code>, so the right value is still found. Many collisions degrade performance toward O(n).'),
        ('Why can\'t a list be a dictionary key?',
         'Lists are mutable — if the list changed after insertion, its hash would change and the entry could never be found again. So lists are unhashable.'),
        ('dict[key] vs dict.get(key)?',
         '<code>d[key]</code> raises KeyError if missing; <code>d.get(key, default)</code> returns the default (None if not given). Use <code>[]</code> when absence is a bug, <code>get</code> when absence is normal.'),
    ),
]),

# ------------------------------------------------------------------ 11
Q('What is a Set? What operations does it support?', 'Sets', minutes=5, cards=[
    definition(
        defbox('A <strong>set</strong> is an <strong>unordered</strong> collection of <strong>unique</strong>, hashable '
               'elements, implemented as a hash table (keys only). Membership tests are O(1) on average.',
               '<code>frozenset</code> is the immutable (hashable) version.'),
        tags('set', 'frozenset', 'Union', 'Intersection', 'Difference', 'Deduplication'),
    ),
    example(
        pyrun("""
batch_a = {"Asha", "Rohit", "Meera", "Kiran"}
batch_b = {"Meera", "Kiran", "Zoya"}

print(sorted(batch_a | batch_b))   # union
print(sorted(batch_a & batch_b))   # intersection
print(sorted(batch_a - batch_b))   # difference: in A not in B
print(sorted(batch_a ^ batch_b))   # symmetric difference: in exactly one

ids = [101, 102, 101, 103, 102]
print(len(set(ids)), "unique ids")

print({1, 2} <= {1, 2, 3})          # subset
empty = set()                       # {} would be an empty DICT
print(type(empty), type({}))
"""),
        title='Example'),
    real_world(
        scenario('Find records missing in the target after a load',
                 pyrun("""
source_ids = {1, 2, 3, 4, 5, 6}
target_ids = {1, 2, 4, 6}
missing = source_ids - target_ids
print("Missing in target:", sorted(missing))
""", 'Reconciliation check')),
    ),
    crossq(
        ('Why is "x in set" faster than "x in list"?',
         'A set uses hashing — O(1) average. A list must compare elements one by one — O(n). For 1 lakh lookups against 1 lakh items, that is the difference between milliseconds and minutes.'),
        ('Does converting a list to a set keep the order?',
         'No — sets are unordered. To remove duplicates while keeping order use <code>list(dict.fromkeys(items))</code>.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What are list, dict and set comprehensions?', 'Comprehensions', minutes=6, cards=[
    definition(
        defbox('A <strong>comprehension</strong> is a concise expression that builds a list, dict or set from an iterable, '
               'optionally filtering and transforming each element.',
               '<code>[expression for item in iterable if condition]</code>'),
        tags('List Comprehension', 'Dict Comprehension', 'Set Comprehension', 'Nested', 'Pythonic'),
    ),
    example(
        pyrun("""
marks = [45, 78, 92, 33, 67]

# loop version
passed = []
for m in marks:
    if m >= 40:
        passed.append(m)

# comprehension version
passed = [m for m in marks if m >= 40]
print(passed)

grades = ["PASS" if m >= 40 else "FAIL" for m in marks]   # if-else goes BEFORE for
print(grades)

names = ["asha", "rohit", "meera"]
print({n: len(n) for n in names})                # dict comprehension
print({len(n) for n in names})                   # set comprehension

matrix = [[1, 2, 3], [4, 5, 6]]
print([x for row in matrix for x in row])        # flatten (outer loop first)
print([[row[i] for row in matrix] for i in range(3)])   # transpose
"""),
        title='Example'),
    interview(
        hl('<code>[x if c else y for x in data]</code> transforms every item. <code>[x for x in data if c]</code> filters items. '
           'The position of the <code>if</code> changes the meaning.', 'Common confusion'),
        p('Comprehensions are usually faster than equivalent <code>for</code> loops with <code>append</code>, but keep them '
          'readable — if it needs more than two clauses, write a normal loop.'),
    ),
    crossq(
        ('Is there a tuple comprehension?',
         'No. <code>(x for x in data)</code> creates a <strong>generator expression</strong>, not a tuple. Use <code>tuple(x for x in data)</code>.'),
        ('Do comprehension variables leak into the outer scope?',
         'Not in Python 3 — the loop variable is local to the comprehension.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What is the difference between a shallow copy and a deep copy?', 'Shallow vs Deep Copy', minutes=6, cards=[
    definition(
        defbox('<strong>Assignment</strong> (<code>b = a</code>) copies nothing — both names point to the same object.',
               'A <strong>shallow copy</strong> creates a new outer object but <strong>shares the inner objects</strong>.',
               'A <strong>deep copy</strong> recursively copies the outer object <strong>and everything inside it</strong>.'),
        tags('copy', 'deepcopy', 'Shallow Copy', 'Nested Objects', 'Aliasing'),
    ),
    shallow_deep(),
    example(
        pyrun("""
import copy

original = {"name": "Asha", "skills": ["SQL", "Python"]}

alias = original
shallow = copy.copy(original)          # or original.copy() / dict(original)
deep = copy.deepcopy(original)

original["skills"].append("Spark")     # mutate the INNER list
original["name"] = "Asha P"            # rebind a top-level key

print("alias  :", alias)
print("shallow:", shallow)
print("deep   :", deep)
"""),
        note('The shallow copy kept the old name (top level was copied) but sees "Spark" (the inner list is shared). The deep copy is fully independent.'),
        title='Example'),
    crossq(
        ('Which operations make shallow copies?',
         '<code>list(a)</code>, <code>a[:]</code>, <code>a.copy()</code>, <code>dict(d)</code>, <code>d.copy()</code>, <code>set(s)</code>, <code>copy.copy(x)</code>.'),
        ('Why not always deepcopy?',
         'It is slower and uses more memory, and some objects (files, sockets, locks) cannot be deep-copied. Use it only when nested mutable data must be independent.'),
        ('What is the classic bug with [[0] * 3] * 3?',
         'It creates three references to the <strong>same</strong> inner list, so changing one row changes all. Use <code>[[0] * 3 for _ in range(3)]</code>.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('Explain string operations and f-strings', 'Strings & f-strings', minutes=7, cards=[
    definition(
        defbox('A <strong>string</strong> (<code>str</code>) is an immutable sequence of Unicode characters. Every string '
               'method returns a <strong>new</strong> string.',
               '<strong>f-strings</strong> (Python 3.6+) embed expressions directly: <code>f"{name} scored {marks}"</code>. '
               'They are the most readable and fastest way to format strings.'),
        tags('str', 'f-string', 'split', 'join', 'strip', 'Unicode', 'encode/decode'),
    ),
    example(
        pyrun("""
raw = "  Asha,PGCP-BDA,Navi Mumbai  "

clean = raw.strip()
parts = clean.split(",")
print(parts)
print(" | ".join(parts))

name = "asha patil"
print(name.title(), name.upper(), name.replace("asha", "Asha"))
print(name.startswith("asha"), "patil" in name, name.find("x"))
print("EMP-007".split("-")[1].zfill(5))

amount, pct = 1234567.891, 0.8765
print(f"{amount:,.2f}")       # thousands separator, 2 decimals
print(f"{pct:.1%}")           # percentage
print(f"{'ID':<6}|{'Name':^10}|{42:>5}")   # alignment
print(f"{amount=}")           # self-documenting (3.8+)

text = "डेटा"                  # Unicode
print(len(text), text.encode("utf-8"))
"""),
        title='Example'),
    interview(
        warn('Building strings with <code>+=</code> inside a loop is O(n²) because each step creates a new string. Collect '
             'pieces in a list and use <code>"".join(pieces)</code>.', 'Performance tip'),
    ),
    crossq(
        ('How do you reverse a string?',
         '<code>s[::-1]</code>. For words: <code>" ".join(s.split()[::-1])</code>.'),
        ('What is the difference between str and bytes?',
         '<code>str</code> is text (Unicode code points); <code>bytes</code> is raw binary data. Convert with '
         '<code>s.encode("utf-8")</code> and <code>b.decode("utf-8")</code>. Files, sockets and Kafka messages carry bytes.'),
        ('split() vs split(" ")?',
         '<code>split()</code> splits on any run of whitespace and drops empty strings. <code>split(" ")</code> splits on every single space and keeps empty strings: <code>"a  b".split(" ")</code> → <code>["a", "", "b"]</code>.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('Explain useful built-ins: enumerate, zip, sorted, any, all, min/max with key', 'Useful Built-ins', minutes=6, cards=[
    definition(
        table(['Built-in', 'Purpose'], [
            ['enumerate(it, start=0)', 'Index + value pairs while looping'],
            ['zip(a, b, …)', 'Iterate several iterables in parallel (stops at the shortest)'],
            ['sorted(it, key=…, reverse=…)', 'New sorted list using a key function'],
            ['min / max (key=…)', 'Smallest / largest by a key'],
            ['sum, len, abs, round', 'Arithmetic helpers'],
            ['any / all', 'True if any / all elements are truthy (short-circuit)'],
            ['map / filter', 'Lazy transform / filter'],
            ['range(start, stop, step)', 'Lazy sequence of integers'],
            ['isinstance(obj, type)', 'Type check that respects inheritance'],
        ]),
        tags('enumerate', 'zip', 'sorted', 'key', 'any', 'all', 'isinstance'),
    ),
    example(
        pyrun("""
students = ["Asha", "Rohit", "Meera"]
marks = [88, 72, 95]

for rank, name in enumerate(students, start=1):
    print(rank, name)

pairs = list(zip(students, marks))
print(pairs)
print(dict(zip(students, marks)))

print(sorted(pairs, key=lambda p: p[1], reverse=True))
print(max(pairs, key=lambda p: p[1]))

names, scores = zip(*pairs)            # "unzip"
print(names, scores)

print(any(m < 75 for m in marks), all(m > 50 for m in marks))

records = [{"id": 2, "city": "Pune"}, {"id": 1, "city": "Delhi"}, {"id": 3, "city": "Agra"}]
print([r["id"] for r in sorted(records, key=lambda r: (r["city"], r["id"]))])
"""),
        title='Example'),
    crossq(
        ('What if the iterables passed to zip have different lengths?',
         'zip stops at the shortest. Use <code>itertools.zip_longest(a, b, fillvalue=None)</code> to go to the longest, or <code>zip(a, b, strict=True)</code> (3.10+) to raise an error on mismatch.'),
        ('Is Python\'s sort stable?',
         'Yes. sorted() and list.sort() use Timsort, which is stable — equal keys keep their original order. This allows multi-level sorting by sorting on the secondary key first.'),
    ),
]),

])
