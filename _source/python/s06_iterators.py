from build import *
from python.anims import *

SECTION = dict(level='advanced', title='Iterators & Generators', questions=[

# ------------------------------------------------------------------ 34
Q('What is the difference between an iterable and an iterator?', 'Iterable vs Iterator', minutes=6, cards=[
    definition(
        defbox('An <strong>iterable</strong> is any object you can loop over — it has <code>__iter__()</code> that returns '
               'an iterator (list, tuple, str, dict, set, file, range).',
               'An <strong>iterator</strong> is the object that actually produces values one at a time with '
               '<code>__next__()</code>, and raises <code>StopIteration</code> when exhausted. It remembers its position '
               'and can be consumed <strong>only once</strong>.'),
        hl('A book is iterable; a bookmark is the iterator. Many bookmarks can walk the same book independently.', 'Analogy'),
        tags('Iterable', 'Iterator', '__iter__', '__next__', 'StopIteration', 'Iterator Protocol'),
    ),
    example(
        pyrun("""
cities = ["Pune", "Mumbai", "Delhi"]      # iterable
it = iter(cities)                         # iterator
print(next(it), next(it), next(it))
try:
    next(it)
except StopIteration:
    print("exhausted")

# What a for loop really does
it = iter(cities)
while True:
    try:
        city = next(it)
    except StopIteration:
        break
    print("visiting", city)

# A custom iterator: page numbers for an API
class Pages:
    def __init__(self, total):
        self.total, self.current = total, 0
    def __iter__(self):
        return self
    def __next__(self):
        if self.current >= self.total:
            raise StopIteration
        self.current += 1
        return self.current

p = Pages(3)
print(list(p), list(p))                   # second pass is empty: consumed
"""),
        title='Example'),
    crossq(
        ('Is a list an iterator?',
         'No — it is an iterable. <code>next([1, 2])</code> raises TypeError. Calling <code>iter()</code> on it gives a fresh iterator each time, which is why you can loop over a list many times.'),
        ('Is a file object an iterator?',
         'Yes. It is its own iterator, yielding one line at a time — which is why reading a big file line by line uses very little memory, and why a second loop over the same open file yields nothing.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('What are generators and the yield keyword? Why are they memory-efficient?', 'Generators & yield', minutes=8, cards=[
    definition(
        defbox('A <strong>generator function</strong> contains <code>yield</code>. Calling it does not run the body — it '
               'returns a <strong>generator</strong> (a kind of iterator). Each <code>next()</code> runs the code until the '
               'next <code>yield</code>, hands out that value, and <strong>pauses</strong> with all local state saved.',
               'Because values are produced <strong>lazily, one at a time</strong>, a generator can process data far larger '
               'than memory — millions of lines, an endless stream, or paginated API results.'),
        tags('Generator', 'yield', 'Lazy Evaluation', 'yield from', 'Memory Efficient', 'Pipeline'),
    ),
    generator_anim(),
    example(
        pyrun("""
import sys

def squares_list(n):
    return [i * i for i in range(n)]

def squares_gen(n):
    for i in range(n):
        yield i * i

print(sys.getsizeof(squares_list(1_000_000)), "bytes for the list")
print(sys.getsizeof(squares_gen(1_000_000)), "bytes for the generator")

g = squares_gen(4)
print(next(g), next(g), list(g))

def countdown(n):
    print("  starting")
    while n > 0:
        yield n
        n -= 1
    print("  done")

for x in countdown(3):
    print(x)
"""),
        pyrun("""
# Generator PIPELINE: each stage pulls one record at a time
from pathlib import Path

Path("app.log").write_text(
    "INFO start\\nERROR db timeout\\nINFO rows=10\\nERROR api 503\\nWARN slow\\n")

def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line.rstrip("\\n")

def only_errors(lines):
    for line in lines:
        if line.startswith("ERROR"):
            yield line

def parse(lines):
    for line in lines:
        level, *msg = line.split(" ", 1)
        yield {"level": level, "msg": msg[0]}

for record in parse(only_errors(read_lines("app.log"))):
    print(record)
""", 'Streaming a log file through a generator pipeline'),
        title='Example'),
    explanation(
        ul('<strong>yield vs return</strong>: return ends the function; yield pauses it and resumes later.',
           '<strong>yield from iterable</strong> delegates to another generator: <code>yield from read_lines(p)</code>.',
           'A generator can be iterated <strong>only once</strong>; call the function again for a fresh one.',
           'The same lazy idea powers Spark (transformations are lazy until an action), pandas <code>chunksize</code> and database cursors.'),
        title='Key Points'),
    crossq(
        ('When should you NOT use a generator?',
         'When you need random access (<code>data[500]</code>), the length, or to iterate several times — then materialise a list.'),
        ('What do send() and close() do?',
         '<code>gen.send(value)</code> resumes the generator and makes the paused <code>yield</code> expression evaluate to that value (used for coroutines). <code>gen.close()</code> raises GeneratorExit inside it so it can clean up.'),
    ),
]),

# ------------------------------------------------------------------ 36
Q('What is the difference between a generator expression and a list comprehension?', 'Generator Expressions', minutes=4, cards=[
    definition(
        defbox('A <strong>generator expression</strong> looks like a list comprehension but uses parentheses: '
               '<code>(x * 2 for x in data)</code>. It produces values lazily instead of building the full list in memory.'),
        tags('Generator Expression', 'List Comprehension', 'Lazy', 'Memory'),
    ),
    comparison(
        table(['Aspect', 'List comprehension [ … ]', 'Generator expression ( … )'], [
            ['Result', 'A list in memory', 'A lazy generator'],
            ['Memory', 'O(n)', 'O(1)'],
            ['Reusable', 'Yes', 'No — single pass'],
            ['Indexing / len()', 'Yes', 'No'],
            ['Best for', 'Small/medium data you reuse', 'Feeding sum, max, any, join, or huge data'],
        ]),
    ),
    example(
        pyrun("""
import sys
nums = range(1_000_000)

print(sum([n * n for n in nums]))   # builds a 1M-element list first
print(sum(n * n for n in nums))     # no list: parentheses of sum() are enough

lst = [n for n in range(1000)]
gen = (n for n in range(1000))
print(sys.getsizeof(lst), sys.getsizeof(gen))

has_negative = any(x < 0 for x in [5, 3, -1, 8])   # stops at -1
print(has_negative)
"""),
        title='Example'),
    crossq(
        ('Why is any(x &lt; 0 for x in data) better than any([x &lt; 0 for x in data])?',
         'The generator version short-circuits — it stops at the first True — and never builds a list. The list version evaluates every element first.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Which collections and itertools utilities should every data engineer know?', 'collections & itertools', minutes=8, cards=[
    definition(
        table(['Tool', 'What it gives you'], [
            ['collections.Counter', 'Count hashable items; most_common()'],
            ['collections.defaultdict', 'Dict that creates a default value for missing keys — easy grouping'],
            ['collections.deque', 'Fast O(1) append/pop at both ends; bounded queues with maxlen'],
            ['collections.namedtuple', 'Lightweight immutable records with named fields'],
            ['collections.OrderedDict', 'Order-aware dict with move_to_end() — handy for LRU caches'],
            ['itertools.chain', 'Join several iterables lazily'],
            ['itertools.islice', 'Slice any iterator lazily (first N lines of a file)'],
            ['itertools.groupby', 'Group <strong>consecutive</strong> items by a key (sort first!)'],
            ['itertools.batched / islice loop', 'Split a stream into fixed-size batches'],
            ['itertools.product / combinations / permutations', 'Cartesian products and combinatorics'],
            ['itertools.accumulate', 'Running totals'],
        ]),
        tags('Counter', 'defaultdict', 'deque', 'namedtuple', 'chain', 'groupby', 'islice', 'accumulate'),
    ),
    example(
        pyrun("""
from collections import Counter, defaultdict, deque, namedtuple

orders = [("Pune", "UPI", 500), ("Mumbai", "CARD", 1200), ("Pune", "CARD", 300),
          ("Delhi", "UPI", 800), ("Pune", "UPI", 150)]

print(Counter(city for city, _, _ in orders).most_common(2))

by_city = defaultdict(list)
for city, mode, amt in orders:
    by_city[city].append(amt)
print(dict(by_city))

revenue = defaultdict(int)
for city, _, amt in orders:
    revenue[city] += amt
print(dict(revenue))

last3 = deque(maxlen=3)               # keeps only the latest 3
for o in orders:
    last3.append(o[2])
print(list(last3))

Order = namedtuple("Order", "city mode amount")
o = Order(*orders[0])
print(o.city, o.amount)
""", 'collections'),
        pyrun("""
from itertools import chain, islice, groupby, accumulate, product

print(list(chain([1, 2], (3, 4), range(5, 7))))
print(list(islice(range(1_000_000), 3)))
print(list(accumulate([100, 250, 50])))          # running total
print(list(product(["dev", "prod"], ["mysql", "s3"])))

rows = [("BDA", "Asha"), ("AI", "Rohit"), ("BDA", "Meera"), ("AI", "Zoya")]
rows.sort(key=lambda r: r[0])                     # groupby needs sorted input
for dept, group in groupby(rows, key=lambda r: r[0]):
    print(dept, [name for _, name in group])

def batches(iterable, size):                      # batch a stream for bulk inserts
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk
print(list(batches(range(7), 3)))
""", 'itertools'),
        title='Example'),
    crossq(
        ('Why must data be sorted before itertools.groupby?',
         'groupby only groups <strong>consecutive</strong> equal keys — unlike SQL GROUP BY. Unsorted input gives repeated, split groups.'),
        ('defaultdict vs dict.setdefault?',
         'Both handle missing keys. defaultdict is cleaner for repeated use; setdefault creates the default object on every call even when the key exists.'),
    ),
]),

])
