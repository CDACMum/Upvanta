from build import *


def _obj(x, y, w, h, label, color='blue', step=None, focus=None):
    return sbox(x, y, w, h, label, '', color, step=step, focus=focus, size=13)


def _name(x, y, label, step=None, focus=None):
    return sbox(x, y, 60, 34, label, '', 'gray', step=step, focus=focus, size=14)


def names_refs():
    elems = [
        stext(110, 30, 'Names', 'gray', 13, bold=True), stext(470, 30, 'Objects (heap)', 'blue', 13, bold=True),
        _name(80, 60, 'a', step=1),
        _obj(330, 55, 280, 44, 'list  [1, 2, 3]', 'blue', step=1, focus=1),
        sarrow(140, 77, 328, 77, 'cyan', step=1),
        _name(80, 120, 'b', step=2, focus=2),
        sarrow(140, 137, 328, 90, 'cyan', step=2),
        stext(470, 140, 'b = a  → no copy, same object', 'cyan', 12, step=2),
        _obj(330, 55, 280, 44, 'list  [1, 2, 3, 4]', 'amber', step=3, focus=3),
        stext(470, 160, 'b.append(4) → a sees it too', 'amber', 12, step=3),
        _name(80, 200, 'c', step=4, focus=4),
        _obj(330, 195, 280, 44, 'NEW list  [1, 2, 3, 4]', 'green', step=4, focus=4),
        sarrow(140, 217, 328, 217, 'green', step=4),
        stext(470, 262, 'c = list(a) → a separate object (copy)', 'green', 12, step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        '<code>a = [1, 2, 3]</code> creates a list <strong>object</strong> and binds the <strong>name</strong> <code>a</code> to it. The name is a label, not a box holding the list.',
        '<code>b = a</code> copies nothing. It attaches a second label to the <strong>same</strong> object, so <code>a is b</code> is True.',
        '<code>b.append(4)</code> mutates that one shared object, so printing <code>a</code> also shows 4.',
        '<code>c = list(a)</code> builds a <strong>new</strong> list object. Changing <code>c</code> no longer affects <code>a</code>.',
    ])


def dict_hash():
    elems = [
        stext(100, 40, "d['city'] = 'Pune'", 'cyan', 14, bold=True),
        sbox(40, 70, 130, 44, "key 'city'", '', 'gray', step=1, focus=1),
        sbox(220, 70, 150, 44, "hash('city')", '= 7310829...', 'amber', step=2, focus=2, size=12),
        sarrow(170, 92, 218, 92, 'amber', step=2),
        sbox(220, 140, 150, 44, '% 8 slots', '→ slot 5', 'purple', step=3, focus=3, size=12),
        sarrow(295, 114, 295, 138, 'purple', step=3),
    ]
    for i in range(8):
        y = 30 + i * 34
        elems.append(scell(470, y, 40, 32, str(i), '#334155', '#94a3b8'))
        elems.append(scell(510, y, 220, 32, '', '#0f172a'))
    elems += [
        '<g data-step="4" data-focus="4">' + scell(510, 30 + 5 * 34, 220, 32, "'city' → 'Pune'", '#064e3b', '#bbf7d0', bold=True) + '</g>',
        sarrow(370, 162, 508, 216, 'green', step=4),
        '<g data-step="5">' + scell(510, 30 + 1 * 34, 220, 32, "'name' → 'Asha'", '#162033', '#e2e8f0') + '</g>',
        stext(200, 240, "lookup d['city']: same hash → slot 5", 'green', 12, step=5, focus=5),
        stext(200, 258, '→ compare key → return value: O(1)', 'green', 12, step=5),
        stext(200, 290, 'collision? probe another slot; keys must be hashable', 'gray', 11, step=6, focus=6),
    ]
    return anim(canvas(760, 310, *elems), [
        'We store the key <code>\'city\'</code> with the value <code>\'Pune\'</code>.',
        'Python computes <code>hash(\'city\')</code>, a large integer derived from the key\'s content. Equal keys always produce equal hashes.',
        'The hash is reduced to an index into the internal table (conceptually <code>hash % table_size</code>), here slot 5.',
        'The key, value and hash are stored in that slot. No searching through other entries was needed.',
        'A lookup repeats the same calculation, jumps straight to slot 5, confirms the stored key equals <code>\'city\'</code> and returns the value. That is average <strong>O(1)</strong> however big the dict is.',
        'If two keys land in the same slot (a collision), Python probes other slots. This is why keys must be <strong>hashable</strong> (immutable): a key whose hash changed after insertion could never be found again.',
    ])


def shallow_deep():
    elems = [
        _name(30, 50, 'orig', step=1), _obj(160, 45, 170, 44, 'dict', 'blue', step=1),
        _obj(470, 45, 250, 44, "inner list ['SQL','Python']", 'amber', step=1, focus=1),
        sarrow(90, 67, 158, 67, 'cyan', step=1), sarrow(330, 67, 468, 67, 'amber', step=1),
        _name(30, 130, 'shallow', step=2, focus=2), _obj(160, 125, 170, 44, 'NEW dict', 'blue', step=2, focus=2),
        sarrow(90, 147, 158, 147, 'cyan', step=2), sarrow(330, 147, 468, 80, 'amber', step=2),
        stext(400, 125, 'shares the SAME inner list', 'amber', 11, step=2),
        _name(30, 210, 'deep', step=3, focus=3), _obj(160, 205, 170, 44, 'NEW dict', 'green', step=3, focus=3),
        _obj(470, 205, 250, 44, "NEW list ['SQL','Python']", 'green', step=3, focus=3),
        sarrow(90, 227, 158, 227, 'green', step=3), sarrow(330, 227, 468, 227, 'green', step=3),
        _obj(470, 45, 250, 44, "inner ['SQL','Python','Spark']", 'red', step=4, focus=4),
        stext(380, 285, "orig['skills'].append('Spark') → visible via orig AND shallow; deep unaffected", 'red', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        '<code>orig</code> is a dict whose <code>"skills"</code> value is a list, a separate inner object.',
        '<code>copy.copy(orig)</code> (a shallow copy) creates a <strong>new outer dict</strong>, but its <code>"skills"</code> entry points to the <strong>same</strong> inner list.',
        '<code>copy.deepcopy(orig)</code> recursively copies everything: a new dict <strong>and</strong> a new inner list.',
        'Appending to the inner list through <code>orig</code> changes the one shared list, so the shallow copy sees "Spark" too. The deep copy is completely independent.',
    ])


def mutable_default():
    elems = [
        sbox(30, 40, 330, 60, 'def add_record(record, batch=[ ])', 'default list created ONCE, at def time', 'purple', step=1, focus=1, size=12),
        _obj(470, 45, 250, 50, 'batch default: [ ]', 'amber', step=1),
        sarrow(360, 70, 468, 70, 'amber', step=1),
        sbox(30, 140, 230, 44, "add_record('r1')", '', 'blue', step=2, focus=2),
        _obj(470, 45, 250, 50, "batch default: ['r1']", 'amber', step=2, focus=2),
        sarrow(260, 160, 470, 95, 'blue', step=2, dashed=True),
        sbox(30, 210, 230, 44, "add_record('r2')", '', 'blue', step=3, focus=3),
        _obj(470, 45, 250, 50, "batch default: ['r1', 'r2']", 'red', step=3, focus=3),
        sarrow(260, 230, 520, 95, 'red', step=3, dashed=True),
        stext(560, 150, "expected ['r2'], got ['r1', 'r2']", 'red', 12, step=3, bold=True),
        stext(560, 230, 'fix: batch=None, then', 'green', 12, step=4, focus=4),
        stext(560, 248, 'if batch is None: batch = [ ]', 'green', 12, step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'When Python executes the <code>def</code> statement it evaluates the default <code>[]</code> <strong>once</strong> and stores that list object on the function (<code>add_record.__defaults__</code>).',
        'The first call uses the default and appends "r1" to that stored list.',
        'The second call uses <strong>the same list object</strong>, which already holds "r1", so the result is <code>[\'r1\', \'r2\']</code>. State leaks between calls.',
        'Fix: use <code>None</code> as the default and create a fresh list inside the function on each call.',
    ])


def legb_anim():
    elems = [
        sbox(20, 20, 720, 270, 'B — Built-in', 'len, print, range …', 'purple', fill_opacity=0.08, top=True),
        sbox(50, 70, 660, 205, 'G — Global (module)', "x = 'global'", 'blue', fill_opacity=0.08, top=True),
        sbox(80, 120, 600, 145, 'E — Enclosing: def outer()', "x = 'enclosing'", 'amber', fill_opacity=0.1, top=True),
        sbox(110, 170, 300, 80, 'L — Local: def inner()', 'print(x)', 'green', fill_opacity=0.15, top=True, focus='1'),
        stext(560, 200, '① look in Local: not found', 'green', 12, step=1),
        stext(560, 220, '② Enclosing: found → "enclosing"', 'amber', 12, step=2, focus=2, bold=True),
        stext(560, 240, '(Global and Built-in never checked)', 'gray', 11, step=3),
        stext(380, 305, 'Assigning to x inside inner() makes x LOCAL (unless declared nonlocal / global)', 'red', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 320, *elems), [
        'Inside <code>inner()</code>, Python looks up the name <code>x</code> in the <strong>Local</strong> scope first. There is no local <code>x</code>.',
        'Next it checks the <strong>Enclosing</strong> function <code>outer()</code>, finds <code>x = \'enclosing\'</code> and prints it.',
        'The search stops at the first match. <strong>Global</strong> and <strong>Built-in</strong> are only checked if the earlier scopes do not have the name.',
        'Scope is decided at compile time: if <code>inner()</code> assigns to <code>x</code> anywhere, <code>x</code> is local throughout the function. Reading it before the assignment raises <code>UnboundLocalError</code>, which is why <code>nonlocal</code> and <code>global</code> exist.',
    ])


def decorator_anim():
    elems = [
        sbox(30, 40, 200, 50, 'def load_rows(n)', 'original function', 'blue', step=1, focus=1, size=12),
        sbox(300, 30, 200, 70, 'timer(load_rows)', 'returns wrapper', 'amber', step=2, focus=2),
        sarrow(230, 65, 298, 65, 'amber', step=2),
        sbox(570, 30, 170, 70, 'wrapper', 'remembers func\n(closure)', 'purple', step=2),
        sarrow(500, 65, 568, 65, 'purple', step=2),
        stext(380, 130, 'name load_rows now points to wrapper  (@timer = rebinding)', 'purple', 12, step=3, focus=3, bold=True),
        sbox(30, 170, 160, 44, 'load_rows(500)', 'caller', 'gray', step=4, focus=4, size=12),
        sbox(240, 160, 230, 64, 'wrapper', 'start timer → call func\n→ stop timer → log', 'purple', step=4, focus=4, size=12),
        sflow(190, 192, 240, 192, 'cyan', step=4, count=1),
        sbox(530, 170, 200, 44, 'original load_rows', 'does the real work', 'blue', step=5, focus=5, size=12),
        sflow(470, 192, 530, 192, 'blue', step=5, count=1),
        stext(380, 260, 'load_rows took 0.050s  → result returned to caller', 'green', 12, step=6, focus=6),
    ]
    return anim(canvas(760, 280, *elems), [
        'We start with an ordinary function <code>load_rows</code>.',
        '<code>@timer</code> calls <code>timer(load_rows)</code>. Inside, a new function <code>wrapper</code> is defined that keeps a reference to the original function through a closure.',
        'The decorator syntax rebinds the name: <code>load_rows = timer(load_rows)</code>. The name <code>load_rows</code> now refers to <strong>wrapper</strong>. <code>functools.wraps</code> copies the original name and docstring onto it.',
        'When code calls <code>load_rows(500)</code>, it is really calling <strong>wrapper</strong>, which starts the timer…',
        '…then calls the <strong>original</strong> function with the same <code>*args, **kwargs</code>…',
        '…then stops the timer, logs the duration and returns the original result. Behaviour was added without editing <code>load_rows</code> itself.',
    ])


def generator_anim():
    elems = [
        stext(150, 30, 'Caller', 'blue', 14, bold=True), stext(560, 30, 'Generator countdown(3)', 'amber', 14, bold=True),
        sbox(40, 50, 220, 40, 'g = countdown(3)', 'body NOT run yet', 'blue', step=1, focus=1, size=12),
        sbox(450, 50, 230, 40, 'created, paused at start', '', 'gray', step=1, size=12),
        sbox(40, 110, 220, 40, 'next(g)', '', 'blue', step=2, focus=2),
        sbox(450, 110, 230, 40, 'runs → yield 3 → PAUSE', 'n = 3 saved', 'amber', step=2, focus=2, size=12),
        sflow(260, 125, 450, 125, 'blue', step=2, count=1), sflow(450, 140, 260, 140, 'amber', step=2, count=1),
        stext(355, 162, 'gets 3', 'amber', 11, step=2),
        sbox(40, 180, 220, 40, 'next(g)', '', 'blue', step=3, focus=3),
        sbox(450, 180, 230, 40, 'resumes → n=2 → yield 2', 'state kept', 'amber', step=3, focus=3, size=12),
        sflow(260, 195, 450, 195, 'blue', step=3, count=1), sflow(450, 210, 260, 210, 'amber', step=3, count=1),
        sbox(40, 250, 220, 40, 'next(g) … after 1', '', 'blue', step=4, focus=4, size=12),
        sbox(450, 250, 230, 40, 'loop ends → StopIteration', 'for-loop stops cleanly', 'red', step=4, focus=4, size=12),
        stext(380, 315, 'Only ONE value exists in memory at a time → stream files of any size', 'green', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 330, *elems), [
        'Calling <code>countdown(3)</code> does <strong>not</strong> execute its body. It returns a generator object, paused before the first line.',
        'The first <code>next(g)</code> runs the body until it reaches <code>yield n</code>. The value 3 is handed to the caller and the generator <strong>pauses</strong>, keeping its local variables.',
        'The next <code>next(g)</code> <strong>resumes</strong> right after the yield, decrements <code>n</code>, loops and yields 2. No state is lost between calls.',
        'When the function body finishes, the generator raises <code>StopIteration</code>. A <code>for</code> loop handles this for you and simply ends.',
        'Because values are produced one at a time on demand, a generator can process a 50 GB file line by line with almost no memory.',
    ])


def gil_anim():
    elems = [
        stext(30, 40, 'CPU-bound: 2 threads', 'red', 13, 'start', bold=True),
        stext(30, 72, 'Thread 1', 'blue', 12, 'start'), stext(30, 104, 'Thread 2', 'purple', 12, 'start'),
    ]
    x = 110
    for i in range(8):
        t1 = i % 2 == 0
        elems.append(f'<g data-step="1"><rect x="{x}" y="{58 if t1 else 90}" width="70" height="22" fill="{"#0ea5e9" if t1 else "#8b5cf6"}" fill-opacity="0.6" rx="3"/></g>')
        x += 76
    elems += [
        stext(420, 135, 'only one thread holds the GIL → they take turns, no speed-up', 'red', 12, step=2, focus=2),
        stext(30, 185, 'I/O-bound: 2 threads', 'green', 13, 'start', bold=True),
        stext(30, 217, 'Thread 1', 'blue', 12, 'start'), stext(30, 249, 'Thread 2', 'purple', 12, 'start'),
        '<g data-step="3"><rect x="110" y="203" width="40" height="22" fill="#0ea5e9" fill-opacity="0.7" rx="3"/>'
        '<rect x="150" y="203" width="250" height="22" fill="none" stroke="#0ea5e9" stroke-dasharray="4,3" rx="3"/>'
        '<rect x="150" y="235" width="40" height="22" fill="#8b5cf6" fill-opacity="0.7" rx="3"/>'
        '<rect x="190" y="235" width="250" height="22" fill="none" stroke="#8b5cf6" stroke-dasharray="4,3" rx="3"/></g>',
        stext(275, 218, 'waiting for API (GIL released)', '#7dd3fc', 11, step=3),
        stext(315, 250, 'waiting for DB (GIL released)', '#c4b5fd', 11, step=3),
        stext(420, 290, 'waits overlap → threads give a real speed-up for I/O', 'green', 12, step=4, focus=4, bold=True),
        stext(420, 310, 'CPU-bound work → use multiprocessing (one GIL per process)', 'amber', 12, step=4),
    ]
    return anim(canvas(760, 325, *elems), [
        'Two threads run pure-Python, CPU-heavy work. In CPython only the thread holding the <strong>GIL</strong> can execute bytecode.',
        'So the threads take turns (the interpreter switches every few milliseconds). Total time is about the same as running them one after the other, and sometimes worse.',
        'Now each thread mostly <strong>waits</strong> for an API or database. While waiting on I/O, a thread <strong>releases the GIL</strong>, so the other thread can run.',
        'The waiting periods overlap, so threads (or asyncio) give a real speed-up for I/O-bound work. For CPU-bound work use <strong>multiprocessing</strong>: separate processes each have their own interpreter and GIL.',
    ])


def two_sum_anim():
    nums = [2, 11, 7, 15]
    elems = [stext(380, 28, 'nums = [2, 11, 7, 15], target = 9', 'cyan', 14, bold=True)]
    for i, n in enumerate(nums):
        elems.append(sbox(80 + i * 90, 50, 70, 44, str(n), f'i={i}', 'blue', focus=(str(i + 1) if i < 3 else None), size=15))
    elems += [
        stext(560, 70, 'seen = { value: index }', 'amber', 12, 'start', bold=True),
        stext(560, 100, '2 → 0', '#e2e8f0', 13, 'start', step=1),
        stext(560, 122, '11 → 1', '#e2e8f0', 13, 'start', step=2),
        stext(240, 130, 'i=0: need 9−2 = 7 → not in seen → store 2', 'gray', 12, step=1),
        stext(240, 152, 'i=1: need 9−11 = −2 → not in seen → store 11', 'gray', 12, step=2),
        stext(240, 174, 'i=2: need 9−7 = 2 → 2 IS in seen (index 0)!', 'green', 12, step=3, focus=3, bold=True),
        stext(380, 220, 'answer: (0, 2)  — one pass, O(n) time', 'green', 15, step=4, focus=4, bold=True),
        stext(380, 245, 'brute force would check every pair: O(n²)', 'red', 12, step=4),
    ]
    return anim(canvas(760, 265, *elems), [
        'Look at <code>2</code>. To reach 9 we need 7. The dict <code>seen</code> is empty, so store 2 with its index 0.',
        'Look at <code>11</code>. We need −2, which has not been seen, so store 11 → 1.',
        'Look at <code>7</code>. We need 2, and 2 <strong>is</strong> in <code>seen</code> at index 0. Dict lookup is O(1), so no inner loop is needed.',
        'Return <code>(0, 2)</code>. A single pass makes it O(n) time with O(n) extra memory, instead of the O(n²) nested-loop brute force.',
    ])


def stack_anim():
    s = '{[()]}'
    elems = [stext(380, 30, 'is_balanced("{[()]}")', 'cyan', 14, bold=True)]
    for i, ch in enumerate(s):
        elems.append(sbox(60 + i * 60, 50, 50, 44, ch, '', 'gray', focus=str(i + 1), size=18))
    # stack visual at right
    elems += ['<rect x="520" y="60" width="120" height="190" fill="none" stroke="#64748b" stroke-width="2"/>',
              stext(580, 270, 'stack', 'gray', 12)]
    pushes = [(1, '{', 210), (2, '[', 170), (3, '(', 130)]
    for st, ch, y in pushes:
        elems.append(sbox(530, y, 100, 36, ch, '', 'amber', step=st, size=16))
    elems += [
        stext(250, 140, 'opening bracket → push', 'amber', 12, step=1),
        sbox(530, 130, 100, 36, '(  ✔ pop', '', 'green', step=4, focus=4, size=13),
        stext(250, 160, ') matches top ( → pop', 'green', 12, step=4),
        sbox(530, 170, 100, 36, '[  ✔ pop', '', 'green', step=5, focus=5, size=13),
        sbox(530, 210, 100, 36, '{  ✔ pop', '', 'green', step=6, focus=6, size=13),
        stext(250, 200, 'stack empty at the end → balanced ✔', 'green', 13, step=7, focus=7, bold=True),
        stext(250, 225, 'mismatch or leftover → not balanced', 'red', 12, step=7),
    ]
    return anim(canvas(760, 290, *elems), [
        '<code>{</code> is an opening bracket, so push it onto the stack.',
        '<code>[</code> is opening, so push.',
        '<code>(</code> is opening, so push. The top of the stack is always the most recent unclosed bracket.',
        '<code>)</code> closes. The top of the stack is <code>(</code>, a matching pair, so pop it.',
        '<code>]</code> matches the new top <code>[</code>, so pop.',
        '<code>}</code> matches <code>{</code>, so pop.',
        'The string is finished and the stack is empty, so the brackets are balanced. A mismatch at any point (for example <code>([)]</code>) or brackets left on the stack means unbalanced. O(n) time.',
    ])
