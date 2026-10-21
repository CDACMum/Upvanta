from build import *
from python.anims import *


def problem(statement, *examples):
    rows = ''.join(f'<li><code>{esc(i)}</code> → <code>{esc(o)}</code></li>' for i, o in examples)
    return card('Problem', 'fa-puzzle-piece',
                defbox(statement),
                (f'<ul class="point-list">{rows}</ul>' if examples else ''))


def approach(*points, complexity=None):
    parts = [ul(*points)]
    if complexity:
        parts.append(hl(complexity, 'Complexity'))
    return card('Approach', 'fa-lightbulb', *parts)


def solution(*parts):
    return card('Solution', 'fa-code', *parts)


SECTION = dict(level='expert', title='Coding Round Problems', questions=[

# ------------------------------------------------------------------ 53
Q('Check whether a string is a palindrome (ignoring case and non-alphanumerics)', 'Palindrome', minutes=5, cards=[
    problem('Given a string, return True if it reads the same forwards and backwards, considering only letters and '
            'digits and ignoring case.',
            ('"Madam"', 'True'), ('"A man, a plan, a canal: Panama"', 'True'), ('"data"', 'False')),
    approach('<strong>Pythonic</strong>: keep only alphanumeric characters in lower case, compare with its reverse <code>s[::-1]</code>.',
             '<strong>Interview follow-up (O(1) extra space)</strong>: two pointers from both ends, skipping non-alphanumerics.',
             complexity='Both O(n) time. Slicing uses O(n) extra space; two pointers use O(1).'),
    solution(
        pyrun("""
def is_palindrome(s: str) -> bool:
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]

def is_palindrome_two_pointers(s: str) -> bool:
    i, j = 0, len(s) - 1
    while i < j:
        if not s[i].isalnum():
            i += 1
        elif not s[j].isalnum():
            j -= 1
        elif s[i].lower() != s[j].lower():
            return False
        else:
            i += 1; j -= 1
    return True

for text in ["Madam", "A man, a plan, a canal: Panama", "data", ""]:
    print(repr(text), is_palindrome(text), is_palindrome_two_pointers(text))
"""),
    ),
    crossq(
        ('How would you find the longest palindromic substring?',
         'Expand around each centre (2n−1 centres: each character and each gap) — O(n²) time, O(1) space. Manacher\'s algorithm does it in O(n) but is rarely expected.'),
    ),
]),

# ------------------------------------------------------------------ 54
Q('Count the frequency of each word in a text', 'Word Frequency', minutes=5, cards=[
    problem('Given a paragraph, return each word with its count, case-insensitive and ignoring punctuation. Then return the top 3 words.',
            ('"Data is data. Big data!"', "{'data': 3, 'is': 1, 'big': 1}")),
    approach('Normalise: lower-case, extract words with a regex (<code>[a-z0-9\']+</code>).',
             'Count with a dict (show you know the manual way) and with <code>collections.Counter</code> (the Pythonic way).',
             '<code>Counter.most_common(k)</code> returns the top k.',
             complexity='O(n) to count; most_common(k) uses a heap — O(m log k) for m distinct words.'),
    solution(
        pyrun("""
import re
from collections import Counter

text = "Data is data. Big data needs big pipelines; pipelines need data engineers!"

words = re.findall(r"[a-z0-9']+", text.lower())

# Manual
freq = {}
for w in words:
    freq[w] = freq.get(w, 0) + 1
print(freq)

# Pythonic
counts = Counter(words)
print(counts.most_common(3))
"""),
    ),
    crossq(
        ('How would you do this for a 100 GB file?',
         'Stream it line by line and update the Counter (memory grows only with the number of distinct words). Beyond one machine, this is the classic MapReduce / Spark word count: <code>flatMap → map(word, 1) → reduceByKey(+)</code>.'),
    ),
]),

# ------------------------------------------------------------------ 55
Q('Find the duplicate elements in a list', 'Find Duplicates', minutes=4, cards=[
    problem('Return the elements that appear more than once in a list (each duplicate reported once).',
            ('[4, 1, 3, 4, 2, 3, 4]', '[4, 3]')),
    approach('Track elements already seen in a <code>set</code>; when you meet one again, add it to a <code>duplicates</code> set.',
             'Or use <code>Counter</code> and keep keys with count &gt; 1.',
             'Avoid the O(n²) pattern <code>[x for x in lst if lst.count(x) &gt; 1]</code>.',
             complexity='O(n) time, O(n) space.'),
    solution(
        pyrun("""
from collections import Counter

def find_duplicates(items):
    seen, dups = set(), []
    for x in items:
        if x in seen and x not in dups:
            dups.append(x)              # keep first-repeat order
        seen.add(x)
    return dups

data = [4, 1, 3, 4, 2, 3, 4]
print(find_duplicates(data))
print([x for x, c in Counter(data).items() if c > 1])
"""),
    ),
    crossq(
        ('SQL equivalent?',
         '<code>SELECT val, COUNT(*) FROM t GROUP BY val HAVING COUNT(*) &gt; 1;</code>'),
        ('How to find the one duplicate in a list of 1..n with one number repeated, in O(1) space?',
         'Use the sum formula (sum(list) − n(n−1)/2) when exactly one number repeats once, or Floyd\'s cycle detection for the general LeetCode version.'),
    ),
]),

# ------------------------------------------------------------------ 56
Q('Two Sum: find two numbers that add up to a target', 'Two Sum', minutes=5, cards=[
    problem('Given a list of integers and a target, return the indexes of the two numbers that add up to the target. Assume exactly one solution.',
            ('nums = [2, 7, 11, 15], target = 9', '(0, 1)'), ('nums = [3, 2, 4], target = 6', '(1, 2)')),
    two_sum_anim(),
    approach('Brute force checks every pair — O(n²).',
             'Optimal: one pass with a dict mapping <code>value → index</code>. For each number, check whether '
             '<code>target − number</code> has already been seen.',
             complexity='O(n) time, O(n) space.'),
    solution(
        pyrun("""
def two_sum(nums, target):
    seen = {}                               # value -> index
    for i, n in enumerate(nums):
        need = target - n
        if need in seen:
            return seen[need], i
        seen[n] = i
    return None

print(two_sum([2, 7, 11, 15], 9))
print(two_sum([3, 2, 4], 6))
print(two_sum([1, 2], 10))
"""),
    ),
    crossq(
        ('What if the list is sorted?',
         'Use two pointers (left at start, right at end): move left up if the sum is too small, right down if too large — O(n) time, O(1) space.'),
    ),
]),

# ------------------------------------------------------------------ 57
Q('Group anagrams together', 'Group Anagrams', minutes=5, cards=[
    problem('Given a list of words, group the words that are anagrams of each other.',
            ('["eat","tea","tan","ate","nat","bat"]', '[["eat","tea","ate"], ["tan","nat"], ["bat"]]')),
    approach('Anagrams have the same letters, so <code>"".join(sorted(word))</code> is the same for all of them — use it as a dictionary key.',
             'Collect words in a <code>defaultdict(list)</code> keyed by that signature.',
             complexity='O(n · k log k) for n words of length k. A 26-letter count tuple as key gives O(n · k).'),
    solution(
        pyrun("""
from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)
    for w in words:
        groups["".join(sorted(w))].append(w)
    return list(groups.values())

print(group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))

def is_anagram(a, b):
    from collections import Counter
    return Counter(a.replace(" ", "").lower()) == Counter(b.replace(" ", "").lower())
print(is_anagram("Listen", "Silent"), is_anagram("data", "date"))
"""),
    ),
    crossq(
        ('Why can a sorted string be a dict key but a sorted list cannot?',
         'Keys must be hashable. <code>sorted()</code> returns a list (unhashable), so join it into a string or convert to a tuple.'),
    ),
]),

# ------------------------------------------------------------------ 58
Q('Flatten an arbitrarily nested list', 'Flatten Nested List', minutes=5, cards=[
    problem('Convert a list that may contain lists at any depth into a flat list.',
            ('[1, [2, [3, [4]], 5], 6]', '[1, 2, 3, 4, 5, 6]')),
    approach('<strong>Recursion</strong>: for each item, if it is a list, flatten it and extend; otherwise append.',
             '<strong>Generator</strong> with <code>yield from</code> — lazy and elegant.',
             '<strong>Iterative with a stack</strong> — avoids recursion-depth limits for extremely deep nesting.',
             complexity='O(n) over all elements.'),
    solution(
        pyrun("""
def flatten(items):
    for x in items:
        if isinstance(x, (list, tuple)):
            yield from flatten(x)
        else:
            yield x

def flatten_iterative(items):
    stack, out = [iter(items)], []
    while stack:
        for x in stack[-1]:
            if isinstance(x, (list, tuple)):
                stack.append(iter(x))
                break
            out.append(x)
        else:
            stack.pop()
    return out

data = [1, [2, [3, [4]], 5], (6, [7])]
print(list(flatten(data)))
print(flatten_iterative(data))
"""),
    ),
    crossq(
        ('Why check isinstance(x, (list, tuple)) instead of "is iterable"?',
         'Strings are iterable too — a generic check would split "abc" into characters and recurse forever on single characters.'),
        ('One-level flatten?',
         '<code>[x for sub in lst for x in sub]</code> or <code>list(itertools.chain.from_iterable(lst))</code>.'),
    ),
]),

# ------------------------------------------------------------------ 59
Q('Merge overlapping intervals', 'Merge Intervals', minutes=6, cards=[
    problem('Given a list of [start, end] intervals, merge all overlapping intervals.',
            ('[[1,3],[2,6],[8,10],[15,18]]', '[[1,6],[8,10],[15,18]]'), ('[[1,4],[4,5]]', '[[1,5]]')),
    approach('Sort intervals by start time.',
             'Walk through them: if the current interval starts before (or at) the end of the last merged one, extend that end; otherwise start a new merged interval.',
             'Data-engineering flavour: merging user sessions, maintenance windows or overlapping validity periods (SCD2).',
             complexity='O(n log n) for the sort, O(n) for the merge.'),
    solution(
        pyrun("""
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

print(merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]))
print(merge_intervals([[1, 4], [4, 5]]))
print(merge_intervals([[5, 7], [1, 2], [2, 4]]))
"""),
    ),
    crossq(
        ('How would you merge two already-sorted lists?',
         'Two pointers comparing heads — O(n + m) — or <code>heapq.merge(a, b)</code>, which also works lazily for many sorted streams.'),
    ),
]),

# ------------------------------------------------------------------ 60
Q('Remove duplicates from a list while preserving order', 'Remove Duplicates, Keep Order', minutes=4, cards=[
    problem('Return the list with duplicates removed, keeping the first occurrence of each element in its original position.',
            ('[3, 1, 3, 2, 1, 5]', '[3, 1, 2, 5]')),
    approach('<code>list(set(x))</code> loses the order — the classic wrong answer.',
             'Use a seen-set while building the output, or <code>dict.fromkeys()</code> (dicts keep insertion order).',
             complexity='O(n) time, O(n) space.'),
    solution(
        pyrun("""
def dedupe(items):
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

data = [3, 1, 3, 2, 1, 5]
print(dedupe(data))
print(list(dict.fromkeys(data)))
print(list(set(data)))          # order NOT guaranteed

# Case-insensitive dedupe keeping the first spelling
names = ["Asha", "asha", "Rohit", "ROHIT", "Meera"]
seen, out = set(), []
for n in names:
    if n.lower() not in seen:
        seen.add(n.lower()); out.append(n)
print(out)
"""),
    ),
]),

# ------------------------------------------------------------------ 61
Q('Find the second largest number in a list (without sorting)', 'Second Largest', minutes=4, cards=[
    problem('Return the second largest <strong>distinct</strong> value in a list in a single pass. Return None if it does not exist.',
            ('[10, 40, 30, 40, 20]', '30'), ('[5, 5]', 'None')),
    approach('Track <code>first</code> and <code>second</code> while scanning once.',
             'Handle duplicates of the maximum and lists with fewer than two distinct values.',
             'Shortcut answers: <code>sorted(set(x))[-2]</code> (O(n log n)) or <code>heapq.nlargest(2, set(x))</code>.',
             complexity='O(n) time, O(1) space.'),
    solution(
        pyrun("""
def second_largest(nums):
    first = second = None
    for n in nums:
        if first is None or n > first:
            first, second = n, first
        elif n != first and (second is None or n > second):
            second = n
    return second

for case in [[10, 40, 30, 40, 20], [5, 5], [7], [-3, -1, -2]]:
    print(case, "->", second_largest(case))
"""),
    ),
    crossq(
        ('SQL version?',
         '<code>SELECT MAX(salary) FROM emp WHERE salary &lt; (SELECT MAX(salary) FROM emp);</code> or <code>DENSE_RANK() = 2</code> with a window function.'),
    ),
]),

# ------------------------------------------------------------------ 62
Q('Find the top K most frequent elements', 'Top-K Frequent', minutes=5, cards=[
    problem('Return the k most frequent elements of a list.',
            ('nums = [1,1,1,2,2,3], k = 2', '[1, 2]')),
    approach('Count with <code>Counter</code>.',
             'Take the top k with a <strong>min-heap of size k</strong> (<code>heapq.nlargest</code>) — better than sorting all items when k is small.',
             'Bucket sort by frequency gives O(n).',
             complexity='Counter O(n) + heap O(m log k), where m = distinct elements.'),
    solution(
        pyrun("""
import heapq
from collections import Counter

def top_k(nums, k):
    counts = Counter(nums)
    return [x for x, _ in heapq.nlargest(k, counts.items(), key=lambda kv: kv[1])]

print(top_k([1, 1, 1, 2, 2, 3], 2))

pages = ["/home", "/cart", "/home", "/pay", "/home", "/cart", "/search"]
print(top_k(pages, 2))

# heapq basics
h = []
for x in [5, 1, 8, 3]:
    heapq.heappush(h, x)
print(heapq.heappop(h), heapq.nsmallest(2, [5, 1, 8, 3]))
"""),
    ),
    crossq(
        ('Why is a heap of size k better than sorting?',
         'Sorting all m items is O(m log m). Keeping a heap of only k items is O(m log k) — much faster when k is small (top 10 of millions).'),
    ),
]),

# ------------------------------------------------------------------ 63
Q('Check whether brackets are balanced (Valid Parentheses)', 'Valid Parentheses', minutes=5, cards=[
    problem('Given a string containing <code>()[]{}</code>, determine whether every opening bracket is closed by the same type in the correct order.',
            ('"{[()]}"', 'True'), ('"([)]"', 'False'), ('"(("', 'False')),
    stack_anim(),
    approach('Use a <strong>stack</strong> (a Python list).',
             'Push opening brackets; on a closing bracket, the top of the stack must be the matching opener.',
             'At the end the stack must be empty.',
             complexity='O(n) time, O(n) space.'),
    solution(
        pyrun("""
def is_balanced(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack

for s in ["{[()]}", "([)]", "((", "SELECT (a + (b * c))", ""]:
    print(repr(s), is_balanced(s))
"""),
    ),
    crossq(
        ('Where is this used in real life?',
         'Validating JSON/SQL expressions, config templates, and parsers in general — any nested structure is checked with a stack.'),
    ),
]),

# ------------------------------------------------------------------ 64
Q('Parse a log file and report error counts per hour and per endpoint', 'Log-File Aggregation', minutes=8, tag='Data Engineering', cards=[
    problem('Given web-server log lines in the form <code>2026-10-08 14:05:12 GET /api/orders 503 120ms</code>, report: '
            '(1) total requests per status code, (2) number of 5xx errors per hour, and (3) the endpoint with the highest average latency.'),
    approach('Stream the file line by line (it may be huge).',
             'Parse each line with <code>split()</code> (or a regex if the format is irregular); skip malformed lines but count them.',
             'Aggregate with <code>Counter</code> and <code>defaultdict</code>; compute averages from (sum, count) pairs.',
             complexity='O(n) time; memory proportional to the number of distinct hours/endpoints, not to file size.'),
    solution(
        pyrun("""
from collections import Counter, defaultdict
from pathlib import Path

Path("access.log").write_text(\"\"\"\\
2026-10-08 14:05:12 GET /api/orders 200 120ms
2026-10-08 14:17:40 GET /api/orders 503 900ms
2026-10-08 14:59:59 POST /api/pay 500 1500ms
2026-10-08 15:01:02 GET /api/users 200 80ms
corrupted line here
2026-10-08 15:20:33 POST /api/pay 200 700ms
2026-10-08 15:45:10 GET /api/orders 502 1100ms
\"\"\")

status_counts = Counter()
errors_per_hour = Counter()
latency = defaultdict(lambda: [0, 0])          # endpoint -> [total_ms, count]
bad_lines = 0

with open("access.log") as f:
    for line in f:
        parts = line.split()
        if len(parts) != 6:
            bad_lines += 1
            continue
        day, time_, method, path, status, ms = parts
        status_counts[status] += 1
        if status.startswith("5"):
            errors_per_hour[f"{day} {time_[:2]}:00"] += 1
        latency[path][0] += int(ms.rstrip("ms"))
        latency[path][1] += 1

print("Requests by status:", dict(status_counts))
print("5xx per hour      :", dict(errors_per_hour))
avg = {p: total / n for p, (total, n) in latency.items()}
slowest = max(avg, key=avg.get)
print(f"Slowest endpoint  : {slowest} ({avg[slowest]:.0f} ms avg)")
print("Malformed lines   :", bad_lines)
"""),
    ),
    crossq(
        ('How would you scale this?',
         'Same logic in PySpark: <code>spark.read.text()</code>, <code>split</code> into columns, then <code>groupBy(hour).count()</code> — or load logs into a warehouse and use SQL. For real-time, stream logs through Kafka and aggregate in windows.'),
        ('Why count malformed lines instead of ignoring them silently?',
         'Silent drops hide data-quality problems. Count them, log samples, and alert if the bad-line ratio crosses a threshold.'),
    ),
]),

# ------------------------------------------------------------------ 65
Q('Deduplicate records keeping only the latest version of each key', 'Deduplicate: Keep Latest', minutes=7, tag='Data Engineering', cards=[
    problem('A CDC feed or incremental extract delivers multiple versions of the same record. Keep only the most recent '
            'version of each <code>customer_id</code> based on <code>updated_at</code>, and drop records marked as deleted.'),
    approach('Iterate once, storing the latest record per key in a dict; replace only when the new record is newer.',
             'Then filter out tombstones (<code>op == "D"</code>).',
             'This is the Python version of SQL <code>ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) = 1</code>, a pattern used in almost every pipeline.',
             complexity='O(n) time, O(k) memory for k distinct keys.'),
    solution(
        pyrun("""
from datetime import datetime

events = [
    {"customer_id": "C1", "city": "Pune",   "op": "I", "updated_at": "2026-10-01T10:00:00"},
    {"customer_id": "C2", "city": "Delhi",  "op": "I", "updated_at": "2026-10-01T11:00:00"},
    {"customer_id": "C1", "city": "Mumbai", "op": "U", "updated_at": "2026-10-05T09:30:00"},
    {"customer_id": "C1", "city": "Nagpur", "op": "U", "updated_at": "2026-10-03T08:00:00"},  # late, older
    {"customer_id": "C3", "city": "Agra",   "op": "I", "updated_at": "2026-10-02T12:00:00"},
    {"customer_id": "C3", "city": "Agra",   "op": "D", "updated_at": "2026-10-06T12:00:00"},
]

def latest_per_key(records, key="customer_id", ts="updated_at"):
    latest = {}
    for r in records:
        r_ts = datetime.fromisoformat(r[ts])
        current = latest.get(r[key])
        if current is None or r_ts > datetime.fromisoformat(current[ts]):
            latest[r[key]] = r
    return [r for r in latest.values() if r["op"] != "D"]

for r in sorted(latest_per_key(events), key=lambda r: r["customer_id"]):
    print(r["customer_id"], r["city"], r["updated_at"])
"""),
        pyrun("""
import pandas as pd

df = pd.DataFrame([
    ("C1", "Pune",   "I", "2026-10-01 10:00"), ("C1", "Mumbai", "U", "2026-10-05 09:30"),
    ("C1", "Nagpur", "U", "2026-10-03 08:00"), ("C2", "Delhi",  "I", "2026-10-01 11:00"),
    ("C3", "Agra",   "D", "2026-10-06 12:00"),
], columns=["customer_id", "city", "op", "updated_at"])
df["updated_at"] = pd.to_datetime(df["updated_at"])

latest = (df.sort_values("updated_at")
            .drop_duplicates("customer_id", keep="last")
            .query("op != 'D'")
            .sort_values("customer_id"))
print(latest.to_string(index=False))
""", 'pandas version'),
    ),
    crossq(
        ('What if two versions have exactly the same timestamp?',
         'Define a deterministic tie-breaker — a sequence number or log position (binlog offset, Kafka offset) from the source — otherwise results can differ between runs.'),
        ('How is this done in PySpark?',
         '<code>Window.partitionBy("customer_id").orderBy(col("updated_at").desc())</code> with <code>row_number()</code>, filter <code>rn == 1</code>; or a <code>MERGE INTO</code> on Delta Lake to upsert the latest version.'),
    ),
]),

])
