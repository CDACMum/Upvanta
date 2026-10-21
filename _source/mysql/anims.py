from build import *
from build import _attrs


def _clause(x, y, w, h, text, color='#334155', step=None, focus=None, size=12, tcolor='#e2e8f0', mono=True):
    """Left-aligned code-style row."""
    ff = ' font-family="Fira Code, monospace"' if mono else ''
    return (f'<g class="sbox"{_attrs(step, focus)}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{color}" '
            f'fill-opacity="0.55" stroke="#475569"/><text x="{x + 10}" y="{y + h/2 + 4}" font-size="{size}" fill="{tcolor}"{ff}>{text}</text></g>')


# ------------------------------------------------------------------ s01
def mysql_arch():
    elems = [
        sbox(20, 120, 120, 70, 'Client', 'mysql CLI / app\nJDBC / Python', 'gray', step=1),
        sflow(140, 155, 185, 155, 'cyan', step=1, count=2),
        sbox(185, 40, 160, 230, 'Connection Layer', '', 'blue', step=2, focus=2, top=True),
        stext(265, 95, 'thread per connection', '#cbd5e1', 11, step=2),
        stext(265, 125, 'authentication', '#cbd5e1', 11, step=2),
        stext(265, 155, '(user@host + password)', '#cbd5e1', 11, step=2),
        stext(265, 185, 'privilege check', '#cbd5e1', 11, step=2),
        sflow(345, 155, 380, 155, 'cyan', step=3, count=2),
        sbox(380, 40, 190, 230, 'SQL Layer (Server)', '', 'purple', step=3, top=True),
        sbox(395, 75, 160, 38, 'Parser', 'syntax → parse tree', 'purple', step=3, focus=3, size=12),
        sbox(395, 128, 160, 38, 'Optimizer', 'picks index & join order', 'purple', step=4, focus=4, size=12),
        sbox(395, 181, 160, 38, 'Executor', 'runs the plan', 'purple', step=5, focus=5, size=12),
        stext(475, 250, 'same for every engine', '#cbd5e1', 11, step=3),
        sflow(570, 200, 600, 200, 'amber', step=5, count=2),
        sbox(600, 40, 145, 230, 'Storage Engine', '', 'green', step=6, top=True),
        sbox(612, 75, 121, 38, 'InnoDB', 'default engine', 'green', step=6, focus=6, size=12),
        sbox(612, 128, 121, 38, 'Buffer Pool', 'cached pages', 'green', step=6, size=12),
        sbox(612, 181, 121, 38, 'Redo / Undo logs', 'crash safety, MVCC', 'green', step=6, size=11),
        sflow(672, 270, 672, 300, 'green', step=7, count=2),
        sbox(560, 300, 225, 40, 'Disk: .ibd files, binlog', '', 'amber', step=7, focus=7, size=12),
        sflow(560, 320, 80, 190, 'pink', step=8, count=3, mid=(80, 330)),
        stext(330, 336, 'result rows back to client', 'pink', 12, step=8, bold=True),
    ]
    return anim(canvas(800, 350, *elems), [
        'A client (the <code>mysql</code> command line, a Java/Python program, Spark over JDBC) sends a SQL statement over TCP port <strong>3306</strong> or a local socket.',
        'The <strong>connection layer</strong> gives the session a thread, checks <code>user@host</code> and password, and later checks privileges for each table touched.',
        'The <strong>parser</strong> checks syntax and builds a parse tree. Misspelled keywords fail here with <code>ERROR 1064</code>.',
        'The <strong>optimizer</strong> estimates costs and chooses the plan: which index to use, the join order, whether to sort in memory. <code>EXPLAIN</code> shows this decision.',
        'The <strong>executor</strong> runs the plan, asking the storage engine for rows through a common handler API.',
        'The <strong>storage engine</strong> (InnoDB by default) actually stores and fetches rows. It keeps hot pages in the <strong>buffer pool</strong> (memory) and uses redo/undo logs for transactions.',
        'Data finally lives on disk as InnoDB tablespace files (<code>.ibd</code>). Changes are also written to the <strong>binary log</strong>, used for replication and CDC.',
        'The result set travels back up the same path to the client.',
    ])


def query_order():
    written = [
        ('SELECT dept_id, AVG(salary) AS avg_sal', 5),
        ('FROM employees', 1),
        ('WHERE salary &gt; 60000', 2),
        ('GROUP BY dept_id', 3),
        ('HAVING COUNT(*) &gt;= 2', 4),
        ('ORDER BY avg_sal DESC', 6),
        ('LIMIT 1', 7),
    ]
    run = [
        ('1  FROM / JOIN', 'blue', '10 rows'),
        ('2  WHERE', 'cyan', '8 rows'),
        ('3  GROUP BY', 'purple', '3 groups'),
        ('4  HAVING', 'pink', '2 groups'),
        ('5  SELECT (aliases made)', 'green', '2 rows, 2 cols'),
        ('6  ORDER BY', 'amber', 'sorted'),
        ('7  LIMIT', 'red', '1 row'),
    ]
    elems = [stext(160, 30, 'As you WRITE it', '#94a3b8', 13, bold=True),
             stext(500, 30, 'As MySQL RUNS it (logically)', '#94a3b8', 13, bold=True)]
    for i, (t, k) in enumerate(written):
        y = 45 + i * 40
        elems.append(_clause(15, y, 300, 30, t, focus=str(k)))
        elems.append(stext(328, y + 20, str(k), '#fbbf24', 13, bold=True, step=k))
    for i, (t, c, rows) in enumerate(run):
        y = 45 + i * 40
        elems.append(sbox(370, y, 230, 30, t, '', c, step=i + 1, focus=str(i + 1), size=12))
        elems.append(stext(615, y + 20, rows, '#e2e8f0', 12, anchor='start', step=i + 1))
    return anim(canvas(760, 330, *elems), [
        '<strong>FROM</strong> (and any JOINs) runs first and builds the working set: all 10 employees.',
        '<strong>WHERE</strong> filters individual rows: 8 employees earn more than 60,000. Aggregates and SELECT aliases do not exist yet, so they cannot be used here.',
        '<strong>GROUP BY</strong> collapses the rows into one group per <code>dept_id</code>: departments 10, 20 and 30.',
        '<strong>HAVING</strong> filters groups: department 30 has only one qualifying employee and is removed.',
        '<strong>SELECT</strong> now computes the output columns, including <code>AVG(salary)</code>, and creates the alias <code>avg_sal</code>.',
        '<strong>ORDER BY</strong> runs after SELECT, which is why it <em>can</em> use the alias <code>avg_sal</code>.',
        '<strong>LIMIT</strong> is last: only the top row is returned. (DISTINCT, when present, runs between SELECT and ORDER BY.)',
    ])


# ------------------------------------------------------------------ s02
GROUP_COLORS = {10: '#1e3a5f', 20: '#3b2a5c', 30: '#4a3416', None: '#4b1d1d'}

def group_by_anim():
    emps = [('Arjun', 10, '150000'), ('Priya', 10, '120000'), ('Rahul', 10, '95000'), ('Sneha', 10, '95000'),
            ('Vikram', 20, '110000'), ('Anjali', 20, '82000'), ('Karan', 20, '115000'),
            ('Meera', 30, '70000'), ('Rohit', 30, '52000'), ('Divya', None, '60000')]
    elems = [stext(117, 30, 'employees (10 rows)', '#38bdf8', 13, bold=True)]
    x0, y0, h = 15, 40, 26
    for j, (hd, w) in enumerate(zip(['name', 'dept_id', 'salary'], [72, 62, 72])):
        elems.append(scell(x0 + [0, 72, 134][j], y0, w, h, hd, '#0ea5e9', '#fff', bold=True))
    plain = ''
    colored = ''
    for i, (n, d, s) in enumerate(emps):
        y = y0 + h * (i + 1)
        for j, (v, w) in enumerate(zip([n, 'NULL' if d is None else str(d), s], [72, 62, 72])):
            plain += scell(x0 + [0, 72, 134][j], y, w, h, v, '#162033')
            colored += scell(x0 + [0, 72, 134][j], y, w, h, v, GROUP_COLORS[d])
    elems.append(f'<g>{plain}</g>')
    elems.append(f'<g data-step="2">{colored}</g>')
    buckets = [(10, 'dept 10', 'Arjun, Priya, Rahul, Sneha', '4', '460000', 'blue'),
               (20, 'dept 20', 'Vikram, Anjali, Karan', '3', '307000', 'purple'),
               (30, 'dept 30', 'Meera, Rohit', '2', '122000', 'amber'),
               (None, 'dept NULL', 'Divya', '1', '60000', 'red')]
    for i, (d, title, names, cnt, sm, col) in enumerate(buckets):
        y = 45 + i * 72
        elems.append(sbox(270, y, 220, 60, title, names, col, step=2, size=12))
        elems.append(stext(500, y + 26, f'COUNT = {cnt}', '#e2e8f0', 12, anchor='start', step=3))
        elems.append(stext(500, y + 44, f'SUM = {sm}', '#e2e8f0', 12, anchor='start', step=3))
    elems.append(sflow(222, 180, 268, 180, 'cyan', step=2, count=2))
    elems.append('<g data-step="4" data-focus="4"><rect x="268" y="259" width="340" height="64" rx="9" fill="none" stroke="#ef4444" stroke-width="2"/>'
                 '<line x1="270" y1="291" x2="606" y2="291" stroke="#ef4444" stroke-width="3"/></g>')
    elems.append(stext(440, 340, 'HAVING COUNT(*) >= 2 removes this group', 'red', 12, step=4, bold=True))
    elems.append(stable(625, 70, ['dept', 'cnt', 'total'], [['10', '4', '460000'], ['20', '3', '307000'], ['30', '2', '122000']],
                        [42, 36, 62], step=5, title='result', title_color='green'))
    elems.append(sflow(600, 140, 622, 140, 'green', step=5, count=2))
    return anim(canvas(780, 355, *elems), [
        'The query is <code>SELECT dept_id, COUNT(*), SUM(salary) FROM employees GROUP BY dept_id HAVING COUNT(*) &gt;= 2</code>. It starts from the 10 rows of <strong>employees</strong>.',
        '<strong>GROUP BY dept_id</strong> puts rows with the same department into one bucket. Note that all NULL departments go into <strong>one NULL group</strong>.',
        'Aggregate functions run once <strong>per bucket</strong>: each group gets its own COUNT and SUM.',
        '<strong>HAVING</strong> then filters whole groups. The NULL group has only 1 row, so it is dropped.',
        'The result has <strong>one row per surviving group</strong>. Columns can only be the grouped column or aggregates, since a group has no single "name".',
    ])


# ------------------------------------------------------------------ s03 joins
def _rows(x, y, rows, widths, h=26, step=None, colors=None, size=12):
    out = ''
    for ri, r in enumerate(rows):
        cx = x
        for v, w in zip(r, widths):
            col = (colors or {}).get(ri, '#0f172a' if ri % 2 else '#162033')
            tc = '#fca5a5' if v == 'NULL' else '#e2e8f0'
            out += scell(cx, y + ri * h, w, h, v, col, tc, size=size)
            cx += w
    return f'<g{_attrs(step)}>{out}</g>'


def join_types():
    E = [('Arjun', '10'), ('Vikram', '20'), ('Meera', '30'), ('Divya', 'NULL')]
    D = [('10', 'Data Eng'), ('20', 'Analytics'), ('30', 'HR'), ('40', 'Marketing')]
    elems = [
        stable(60, 40, ['name', 'dept_id'], [list(r) for r in E], [90, 70], title='employees e', title_color='blue'),
        stable(500, 40, ['dept_id', 'dept_name'], [list(r) for r in D], [70, 110], title='departments d', title_color='purple'),
    ]
    for i in range(3):
        y = 79 + 26 * i
        elems.append(sarrow(222, y, 498, y, 'green', step=1))
    elems.append(stext(360, 70, 'ON e.dept_id = d.dept_id', 'green', 12, step=1, bold=True))
    elems.append(stext(250, 160, '✘ no match', 'red', 11, anchor='start', step=1))
    elems.append(stext(490, 160, 'no match ✘', 'red', 11, anchor='end', step=1))
    W = [78, 105]
    panels = [
        ('INNER JOIN', 'green', [('Arjun', 'Data Eng'), ('Vikram', 'Analytics'), ('Meera', 'HR')], {}),
        ('LEFT JOIN', 'blue', [('Arjun', 'Data Eng'), ('Vikram', 'Analytics'), ('Meera', 'HR'), ('Divya', 'NULL')], {3: '#3b1d1d'}),
        ('RIGHT JOIN', 'purple', [('Arjun', 'Data Eng'), ('Vikram', 'Analytics'), ('Meera', 'HR'), ('NULL', 'Marketing')], {3: '#3b1d1d'}),
        ('FULL OUTER', 'amber', [('Arjun', 'Data Eng'), ('Vikram', 'Analytics'), ('Meera', 'HR'), ('Divya', 'NULL'), ('NULL', 'Marketing')],
         {3: '#3b1d1d', 4: '#3b1d1d'}),
    ]
    for k, (t, c, rows, cols) in enumerate(panels):
        x = 12 + k * 197
        st = k + 2
        elems.append(f'<g data-step="{st}" data-focus="{st}" class="sbox"><rect x="{x - 4}" y="203" width="{sum(W) + 8}" height="{26 * (len(rows) + 1) + 34}" rx="8" fill="none" stroke="{PALETTE[c]}" stroke-width="1.5"/></g>')
        elems.append(stext(x + sum(W) / 2, 222, f'{t}: {len(rows)} rows', PALETTE[c], 12, step=st, bold=True))
        elems.append(_rows(x, 232, [('name', 'dept_name')], W, step=st, colors={0: PALETTE[c]}))
        elems.append(_rows(x, 258, rows, W, step=st, colors=cols))
    elems.append(stext(400, 410, 'CROSS JOIN: no ON clause, every row with every row → 4 × 4 = 16 rows', 'pink', 13, step=6, bold=True))
    return anim(canvas(800, 425, *elems), [
        'Rows are matched on <code>e.dept_id = d.dept_id</code>. Three pairs match. Divya has no department (NULL never matches anything) and Marketing has no employees.',
        '<strong>INNER JOIN</strong> returns only the matching pairs: 3 rows. Unmatched rows from both sides disappear.',
        '<strong>LEFT JOIN</strong> keeps <em>every</em> row from the left table. Divya has no match, so the department columns are filled with NULL.',
        '<strong>RIGHT JOIN</strong> keeps every row from the right table. Marketing appears with NULL employee columns. (Any RIGHT JOIN can be rewritten as a LEFT JOIN by swapping the tables.)',
        '<strong>FULL OUTER JOIN</strong> keeps unmatched rows from both sides. MySQL has no FULL JOIN keyword, so it is built as LEFT JOIN UNION RIGHT JOIN.',
        '<strong>CROSS JOIN</strong> has no condition and returns the Cartesian product: every employee paired with every department.',
    ])


def on_vs_where():
    W = [100, 75, 78]
    on_rows = [('Data Eng.', 'Arjun', '150000'), ('Data Eng.', 'Priya', '120000'), ('Analytics', 'Vikram', '110000'),
               ('Analytics', 'Karan', '115000'), ('HR', 'NULL', 'NULL'), ('Marketing', 'NULL', 'NULL')]
    all_rows = [('Data Eng.', 'Arjun', '150000', 1), ('Data Eng.', 'Priya', '120000', 1), ('Data Eng.', 'Rahul', '95000', 0),
                ('Data Eng.', 'Sneha', '95000', 0), ('Analytics', 'Vikram', '110000', 1), ('Analytics', 'Anjali', '82000', 0),
                ('Analytics', 'Karan', '115000', 1), ('HR', 'Meera', '70000', 0), ('HR', 'Rohit', '52000', 0),
                ('Marketing', 'NULL', 'NULL', 0)]
    h = 22
    elems = [
        stext(146, 22, 'Filter in ON', 'green', 13, bold=True, step=1),
        _clause(10, 30, 275, 44, '', step=1),
        stext(18, 47, 'LEFT JOIN employees e ON d.dept_id = e.dept_id', '#e2e8f0', 10, anchor='start', step=1),
        stext(18, 64, '  AND e.salary &gt; 100000', '#86efac', 10, anchor='start', step=1, bold=True),
        _rows(14, 84, [('dept_name', 'name', 'salary')], W, h=h, step=2, colors={0: '#10b981'}, size=11),
        _rows(14, 84 + h, [r for r in on_rows], W, h=h, step=2, colors={4: '#123b2c', 5: '#123b2c'}, size=11),
        stext(146, 84 + h * 7 + 20, '6 rows: every department kept', 'green', 12, step=2, bold=True),
        stext(560, 22, 'Filter in WHERE', 'red', 13, bold=True, step=3),
        _clause(410, 30, 300, 44, '', step=3),
        stext(418, 47, 'LEFT JOIN employees e ON d.dept_id = e.dept_id', '#e2e8f0', 10, anchor='start', step=3),
        stext(418, 64, 'WHERE e.salary &gt; 100000', '#fca5a5', 10, anchor='start', step=3, bold=True),
        _rows(430, 84, [('dept_name', 'name', 'salary')], W, h=h, step=3, colors={0: '#ef4444'}, size=11),
        _rows(430, 84 + h, [r[:3] for r in all_rows], W, h=h, step=3, size=11),
    ]
    strikes = ''.join(f'<line x1="430" y1="{84 + h * (i + 1) + h / 2}" x2="{430 + sum(W)}" y2="{84 + h * (i + 1) + h / 2}" stroke="#ef4444" stroke-width="2"/>'
                      for i, r in enumerate(all_rows) if not r[3])
    elems.append(f'<g data-step="4" data-focus="4">{strikes}</g>')
    elems.append(stext(560, 84 + h * 11 + 20, 'only 4 rows: HR and Marketing vanished', 'red', 12, step=4, bold=True))
    elems.append(stext(560, 84 + h * 11 + 38, 'NULL &gt; 100000 is UNKNOWN → row dropped', 'red', 11, step=4))
    return anim(canvas(770, 370, *elems), [
        'Goal: list <strong>every department</strong> with its employees earning above 1,00,000, keeping departments that have none. The first query puts the salary condition in the <strong>ON</strong> clause.',
        'With the condition in ON, it only decides <em>which employees match</em>. HR and Marketing find no matching employee, so LEFT JOIN keeps them with NULLs. Result: 6 rows, all 4 departments.',
        'The second query puts the condition in <strong>WHERE</strong>. First the LEFT JOIN produces all 10 department–employee rows (Marketing with NULLs).',
        'Then WHERE filters the joined rows. Low earners are removed, and so is the Marketing row, because <code>NULL &gt; 100000</code> is unknown. The LEFT JOIN has silently become an <strong>INNER JOIN</strong>. Rule: conditions on the right-hand table of a LEFT JOIN go in ON.',
    ])


def not_in_null():
    elems = [
        _clause(15, 20, 600, 30, 'SELECT name FROM employees WHERE emp_id NOT IN (SELECT manager_id FROM employees);', step=1, size=11),
        stext(20, 80, 'subquery returns:', '#94a3b8', 12, anchor='start', step=1),
    ]
    vals = ['1', '2', '5', '8', 'NULL']
    elems.append('<g data-step="1">' + ''.join(
        scell(150 + i * 60, 64, 56, 26, v, '#4b1d1d' if v == 'NULL' else '#1e3a5f',
              '#fca5a5' if v == 'NULL' else '#e2e8f0', bold=True) for i, v in enumerate(vals)) + '</g>')
    elems.append(stext(20, 130, 'Check emp 3 (Rahul):  3 NOT IN (1, 2, 5, 8, NULL)  means', '#e2e8f0', 12, anchor='start', step=2, bold=True))
    parts = [('3≠1', 'TRUE', 'green'), ('3≠2', 'TRUE', 'green'), ('3≠5', 'TRUE', 'green'), ('3≠8', 'TRUE', 'green'), ('3≠NULL', 'UNKNOWN', 'red')]
    for i, (e, r, c) in enumerate(parts):
        x = 20 + i * 140
        elems.append(sbox(x, 145, 112, 44, e, r, c, step=2 if c == 'green' else 3, focus='3' if c == 'red' else None, size=12))
        if i < 4:
            elems.append(stext(x + 126, 172, 'AND', '#94a3b8', 11, step=2, bold=True))
    elems.append(stext(20, 220, 'TRUE AND TRUE AND TRUE AND TRUE AND UNKNOWN = UNKNOWN → WHERE drops the row', 'red', 12, anchor='start', step=3, bold=True))
    elems.append(stext(20, 244, 'Same for every employee → result: 0 rows (expected 6 non-managers)', 'red', 12, anchor='start', step=4, bold=True, focus='4'))
    elems.append(sbox(20, 268, 340, 54, 'Fix 1: NOT EXISTS', 'NULLs in the subquery cannot break it', 'green', step=5, size=12))
    elems.append(sbox(380, 268, 340, 54, 'Fix 2: … WHERE manager_id IS NOT NULL', 'remove NULLs from the NOT IN list', 'green', step=5, size=12))
    return anim(canvas(740, 335, *elems), [
        'We want employees who are <strong>not managers</strong>. The subquery returns every manager_id, and Arjun\'s manager_id is <strong>NULL</strong>, so the list contains a NULL.',
        '<code>x NOT IN (a, b, c)</code> is shorthand for <code>x &lt;&gt; a AND x &lt;&gt; b AND x &lt;&gt; c</code>. For Rahul (3) the first four comparisons are TRUE.',
        'But <code>3 &lt;&gt; NULL</code> is <strong>UNKNOWN</strong>, and TRUE AND UNKNOWN is UNKNOWN. WHERE keeps only TRUE rows, so Rahul is dropped.',
        'Every employee hits the same NULL comparison, so the query silently returns <strong>no rows at all</strong>, with no error.',
        'Use <code>NOT EXISTS</code> (or a LEFT JOIN … IS NULL anti-join), or exclude NULLs inside the subquery. Both return the 6 correct employees.',
    ])


def row_multiplication():
    W1 = [70, 80]
    elems = [
        stable(20, 40, ['order_id', 'amount'], [['101', '57500'], ['102', '8000'], ['105', '12500']], W1, title='orders', title_color='blue'),
        stext(95, 165, 'SUM(amount) = 78000 ✔', 'green', 12, step=1, bold=True),
        stable(220, 40, ['order_id', 'product'], [['101', 'Laptop'], ['101', 'Headphones'], ['102', 'Desk'], ['105', 'Desk'], ['105', 'Chair']],
               [70, 95], title='order_items', title_color='purple', step=2, focus_rows={0: '2', 1: '2', 3: '2', 4: '2'}),
        stext(302, 220, 'orders 101 and 105 have 2 items each', 'purple', 11, step=2),
    ]
    elems.append(sflow(390, 120, 476, 120, 'cyan', step=3, count=2))
    rows = [['101', 'Laptop', '57500'], ['101', 'Headphones', '57500'], ['102', 'Desk', '8000'], ['105', 'Desk', '12500'], ['105', 'Chair', '12500']]
    elems.append(stable(480, 40, ['order_id', 'product', 'o.amount'], rows, [65, 95, 75], title='orders JOIN order_items', title_color='amber',
                        step=3, focus_rows={1: '3,4', 4: '3,4'}))
    elems.append(stext(597, 220, 'SUM(o.amount) = 148000 ✘', 'red', 13, step=4, bold=True, focus='4'))
    elems.append(stext(597, 238, '57500 and 12500 counted twice', 'red', 11, step=4))
    elems.append(sbox(140, 258, 520, 46, 'Fix: aggregate the child table first, then join',
                      '', 'green', step=5, size=12))
    return anim(canvas(780, 315, *elems), [
        'Three orders whose amounts add up to <strong>78,000</strong>. One row per order.',
        'The <strong>order_items</strong> table has one row per product, so orders 101 and 105 appear twice. The join key is not unique on this side.',
        'A join returns one row per <em>matching pair</em>. Each order row is repeated once for each of its items: 3 orders become 5 rows, and <code>amount</code> is copied onto every copy.',
        'Summing the order amount after the join counts orders 101 and 105 twice: 1,48,000 instead of 78,000. This "fan-out" bug is very common in reporting queries.',
        'Sum order amounts from <strong>orders</strong> alone, or pre-aggregate <strong>order_items</strong> in a subquery/CTE (one row per order) before joining. <code>SUM(DISTINCT amount)</code> is <em>not</em> a fix: two different orders can have the same amount.',
    ])


# ------------------------------------------------------------------ s04 subqueries & CTEs
def correlated_anim():
    emps = [('Arjun', '10', '150000'), ('Priya', '10', '120000'), ('Rahul', '10', '95000'), ('Sneha', '10', '95000'),
            ('Vikram', '20', '110000'), ('Anjali', '20', '82000'), ('Karan', '20', '115000'),
            ('Meera', '30', '70000'), ('Rohit', '30', '52000')]
    marks = ['✔', '✔', '✘', '✘', '✔', '✘', '✔', '✔', '✘']
    mark_step = {0: 3, 2: 4, 4: 5}
    h, y0 = 26, 40
    elems = [_clause(15, 4, 740, 26, 'SELECT name FROM employees e WHERE salary &gt; (SELECT AVG(salary) FROM employees x WHERE x.dept_id = e.dept_id)', size=10)]
    elems.append(stable(15, y0 + 4, ['name', 'dept', 'salary'], [list(r) for r in emps], [72, 50, 72], h=h, title_color='blue',
                        focus_rows={0: '1,2,3', 2: '4', 4: '5'}))
    for i, m in enumerate(marks):
        y = y0 + 4 + h * (i + 1) + 17
        elems.append(stext(225, y, m, 'green' if m == '✔' else 'red', 15, step=mark_step.get(i, 6), bold=True))
    inner = [(0, 'dept 10', '(150000+120000+95000+95000)/4 = 115000', '150000 &gt; 115000 → keep', 2, 'green'),
             (2, 'dept 10 (again!)', 'AVG recomputed = 115000', '95000 &gt; 115000 → drop', 4, 'red'),
             (4, 'dept 20', '(110000+82000+115000)/3 = 102333', '110000 &gt; 102333 → keep', 5, 'green')]
    for ri, title, calc, cmp_, st, col in inner:
        y = y0 + 4 + h * (ri + 1) - 4
        elems.append(sarrow(240, y + 17, 300, y + 17, 'gray', step=st))
        elems.append(sbox(305, y - 2, 300, 44, f'inner query for {title}', calc, 'purple', step=st, focus=str(st), size=11))
        elems.append(stext(615, y + 24, cmp_, col, 11, anchor='start', step=st + (1 if st == 2 else 0), bold=True))
    elems.append(stext(450, 312, 'Logically the inner query runs once per outer row: 9 rows → 9 AVG computations', 'amber', 12, step=6, bold=True))
    elems.append(stext(450, 332, 'Better: compute each department average once (derived table / CTE / window function)', 'green', 12, step=6))
    return anim(canvas(780, 345, *elems), [
        'The outer query reads employees one row at a time. The first row is Arjun of department 10.',
        'The inner query refers to the outer row (<code>e.dept_id</code>), so it is <strong>correlated</strong>: it cannot run on its own. For Arjun it computes the average salary of department 10 = 1,15,000.',
        'Arjun\'s 1,50,000 is greater than 1,15,000, so the row is kept.',
        'For Rahul the inner query runs again for department 10 and gets the same 1,15,000. 95,000 is not greater, so Rahul is dropped.',
        'For Vikram the inner query computes department 20\'s average, 1,02,333. 1,10,000 is greater, so he is kept.',
        'This continues for every row. The result is correct, but the repeated work makes correlated subqueries slow on big tables unless the optimizer rewrites them, so pre-aggregating is the usual fix.',
    ])


def recursive_cte():
    def node(x, y, name, st, col):
        return sbox(x, y, 130, 34, name, '', col, step=st, focus=str(st), size=12)
    elems = [stext(105, 30, 'Anchor (level 1)', 'blue', 12, bold=True, step=1),
             stext(345, 30, 'Iteration 1 (level 2)', 'purple', 12, bold=True, step=2),
             stext(585, 30, 'Iteration 2 (level 3)', 'green', 12, bold=True, step=3)]
    elems.append(node(40, 160, 'Arjun', 1, 'blue'))
    l2 = [('Priya', 55), ('Vikram', 135), ('Meera', 215), ('Divya', 285)]
    for n, y in l2:
        elems.append(node(280, y, n, 2, 'purple'))
        elems.append(sarrow(170, 177, 278, y + 17, 'gray', step=2))
    l3 = [('Rahul', 45, 55), ('Sneha', 90, 55), ('Anjali', 140, 135), ('Karan', 185, 135), ('Rohit', 235, 215)]
    for n, y, py in l3:
        elems.append(node(520, y, n, 3, 'green'))
        elems.append(sarrow(410, py + 17, 518, y + 17, 'gray', step=3))
    elems.append(sbox(520, 285, 230, 40, 'Iteration 3: 0 rows → STOP', '', 'red', step=4, focus='4', size=12))
    elems.append(stext(400, 350, 'Final result = anchor UNION ALL iteration 1 UNION ALL iteration 2 → 1 + 4 + 5 = 10 rows', 'amber', 12, step=5, bold=True))
    return anim(canvas(780, 365, *elems), [
        'The <strong>anchor member</strong> runs once: <code>SELECT … FROM employees WHERE manager_id IS NULL</code> returns the top of the tree, Arjun, at level 1.',
        'The <strong>recursive member</strong> joins employees to the rows produced in the previous step (<code>e.manager_id = cte.emp_id</code>): Arjun\'s 4 direct reports, level 2.',
        'It runs again using <em>only the new rows</em> from iteration 1, finding their reports: 5 employees at level 3. Divya has no reports.',
        'Iteration 3 joins against the level-3 rows and finds nothing. An empty result ends the recursion.',
        'All iterations are combined with UNION ALL. MySQL stops with an error if recursion goes deeper than <code>cte_max_recursion_depth</code> (default 1000), which protects against cycles.',
    ])


# ------------------------------------------------------------------ s05 window functions
def window_vs_groupby():
    emps = [('Arjun', '10', '150000'), ('Priya', '10', '120000'), ('Rahul', '10', '95000'), ('Sneha', '10', '95000'),
            ('Vikram', '20', '110000'), ('Anjali', '20', '82000'), ('Karan', '20', '115000'),
            ('Meera', '30', '70000'), ('Rohit', '30', '52000')]
    gcol = {'10': '#1e3a5f', '20': '#3b2a5c', '30': '#4a3416'}
    W = [70, 45, 70]
    h, y0 = 24, 44
    elems = [stext(107, 30, 'employees', '#38bdf8', 13, bold=True)]
    elems.append(_rows(15, y0, [('name', 'dept', 'salary')], W, h=h, colors={0: '#0ea5e9'}, size=11))
    elems.append(_rows(15, y0 + h, emps, W, h=h, size=11))
    elems.append(_rows(15, y0 + h, emps, W, h=h, size=11, step=1, colors={i: gcol[r[1]] for i, r in enumerate(emps)}))
    # GROUP BY result
    elems.append(stext(320, 30, 'GROUP BY dept_id', 'amber', 13, bold=True, step=2))
    elems.append(_rows(250, y0, [('dept', 'AVG(salary)')], [50, 90], h=h, colors={0: '#f59e0b'}, size=11, step=2))
    elems.append(_rows(250, y0 + h, [('10', '115000'), ('20', '102333'), ('30', '61000')], [50, 90], h=h, size=11, step=2,
                       colors={0: gcol['10'], 1: gcol['20'], 2: gcol['30']}))
    elems.append(stext(320, y0 + h * 4 + 20, '9 rows → 3 rows', 'amber', 12, step=2, bold=True))
    elems.append(stext(320, y0 + h * 4 + 38, 'names are lost', 'amber', 11, step=2))
    # window result
    avg = {'10': '115000', '20': '102333', '30': '61000'}
    rows = [(n, d, s, avg[d]) for n, d, s in emps]
    elems.append(stext(600, 30, 'AVG(salary) OVER (PARTITION BY dept_id)', 'green', 12, bold=True, step=3))
    elems.append(_rows(440, y0, [('name', 'dept', 'salary', 'dept_avg')], [70, 45, 70, 80], h=h, colors={0: '#10b981'}, size=11, step=3))
    elems.append(_rows(440, y0 + h, rows, [70, 45, 70, 80], h=h, size=11, step=3, colors={i: gcol[r[1]] for i, r in enumerate(rows)}))
    elems.append(stext(600, y0 + h * 10 + 22, '9 rows → still 9 rows, plus the aggregate', 'green', 12, step=3, bold=True))
    elems.append(stext(400, y0 + h * 10 + 50, 'Now each row can be compared with its group: salary − dept_avg, % of dept total, rank in dept …',
                       '#e2e8f0', 12, step=4))
    return anim(canvas(780, 350, *elems), [
        'Both queries split the rows into the same groups by department (shown in colour). In window functions a group is called a <strong>partition</strong>.',
        '<strong>GROUP BY</strong> collapses each group to a single row. You get the average, but the individual employees are gone.',
        'A <strong>window function</strong> computes the same average over the partition but <strong>writes it onto every row</strong>. No rows are removed.',
        'Because detail and aggregate sit side by side, comparisons like "salary vs department average" need no self-join or subquery.',
    ])


def rank_anim():
    rows = [('Arjun', '150000'), ('Priya', '120000'), ('Karan', '115000'), ('Vikram', '110000'),
            ('Rahul', '95000'), ('Sneha', '95000'), ('Anjali', '82000'), ('Meera', '70000')]
    rn = [str(i + 1) for i in range(8)]
    rk = ['1', '2', '3', '4', '5', '5', '7', '8']
    dr = ['1', '2', '3', '4', '5', '5', '6', '7']
    h, y0 = 28, 50
    elems = [stext(110, 34, 'ORDER BY salary DESC', '#38bdf8', 13, bold=True)]
    elems.append(_rows(20, y0, [('name', 'salary')], [80, 90], h=h, colors={0: '#0ea5e9'}))
    elems.append(_rows(20, y0 + h, rows, [80, 90], h=h, colors={4: '#4a3416', 5: '#4a3416'}))
    for k, (title, vals, col, st) in enumerate([('ROW_NUMBER()', rn, '#10b981', 2), ('RANK()', rk, '#8b5cf6', 3), ('DENSE_RANK()', dr, '#f472b6', 4)]):
        x = 220 + k * 125
        elems.append(_rows(x, y0, [(title,)], [115], h=h, colors={0: col}, step=st))
        cells = [(v,) for v in vals]
        elems.append(_rows(x, y0 + h, cells, [115], h=h, step=st, colors={4: '#4a3416', 5: '#4a3416'}))
    elems.append(stext(600, y0 + h * 5 + 18, '← tie', 'amber', 13, anchor='start', step=1, bold=True))
    elems.append(f'<g data-step="5" data-focus="5"><rect x="345" y="{y0 + h * 7}" width="115" height="{h}" fill="none" stroke="#fbbf24" stroke-width="3"/>'
                 f'<rect x="470" y="{y0 + h * 7}" width="115" height="{h}" fill="none" stroke="#fbbf24" stroke-width="3"/></g>')
    elems.append(stext(465, y0 + h * 9 + 24, 'RANK jumps 5 → 7 (gap)   ·   DENSE_RANK goes 5 → 6 (no gap)', 'amber', 12, step=5, bold=True))
    return anim(canvas(780, 340, *elems), [
        'All three functions number rows in the order given by <code>OVER (ORDER BY salary DESC)</code>. Rahul and Sneha both earn 95,000: a <strong>tie</strong>.',
        '<strong>ROW_NUMBER()</strong> gives every row a unique number 1, 2, 3 … Ties are broken arbitrarily (add a second ORDER BY column to make it deterministic).',
        '<strong>RANK()</strong> gives tied rows the same rank (5, 5) and then <strong>skips</strong>: the next rank is 7, like positions in a race.',
        '<strong>DENSE_RANK()</strong> also gives ties the same rank but does <strong>not skip</strong>: the next rank is 6.',
        'So for "the 6th highest <em>distinct</em> salary" use DENSE_RANK = 6 (82,000). RANK has no row with 6 at all.',
    ])


def lag_lead_anim():
    months = [('Jan', '120'), ('Feb', '150'), ('Mar', '135'), ('Apr', '180'), ('May', '210'), ('Jun', '190')]
    lag = ['NULL', '120', '150', '135', '180', '210']
    diff = ['NULL', '+30', '−15', '+45', '+30', '−20']
    lead = ['150', '135', '180', '210', '190', 'NULL']
    h, y0 = 32, 50
    elems = [_rows(20, y0, [('month', 'revenue (₹K)')], [70, 105], h=h, colors={0: '#0ea5e9'})]
    elems.append(_rows(20, y0 + h, months, [70, 105], h=h))
    elems.append(_rows(240, y0, [('LAG(revenue)',)], [120], h=h, colors={0: '#8b5cf6'}, step=1))
    elems.append(_rows(240, y0 + h, [(v,) for v in lag], [120], h=h, step=1))
    for i in range(5):
        y1 = y0 + h * (i + 1) + h / 2
        elems.append(sarrow(175, y1, 238, y1 + h, 'purple', step=1))
    elems.append(_rows(380, y0, [('revenue − LAG',)], [120], h=h, colors={0: '#f59e0b'}, step=2))
    elems.append(_rows(380, y0 + h, [(v,) for v in diff], [120], h=h, step=2,
                       colors={2: '#4b1d1d', 5: '#4b1d1d', 1: '#123b2c', 3: '#123b2c', 4: '#123b2c'}))
    elems.append(_rows(540, y0, [('LEAD(revenue)',)], [120], h=h, colors={0: '#f472b6'}, step=3))
    elems.append(_rows(540, y0 + h, [(v,) for v in lead], [120], h=h, step=3))
    elems.append(stext(400, y0 + h * 7 + 30, 'LAG looks back, LEAD looks ahead; the first/last row has no neighbour → NULL (or a default)', '#e2e8f0', 12, step=4))
    return anim(canvas(780, 310, *elems), [
        '<code>LAG(revenue) OVER (ORDER BY month)</code> returns the value from the <strong>previous row</strong>. Every value shifts down by one; January has no previous month, so it gets NULL.',
        'Subtracting gives month-over-month change in one pass: +30, −15, +45 … No self-join on "month − 1" is needed.',
        '<code>LEAD(revenue)</code> is the mirror image: it reads the <strong>next row</strong>, so June gets NULL.',
        'Both accept an offset and a default: <code>LAG(revenue, 12, 0)</code> gives the same month last year, or 0 when there is none.',
    ])


def frame_anim():
    days = [('1', '100'), ('2', '300'), ('3', '200'), ('4', '400'), ('5', '100'), ('6', '300')]
    run = ['100', '400', '600', '1000', '1100', '1400']
    mov = ['100.0', '200.0', '200.0', '300.0', '233.3', '266.7']
    h, y0 = 34, 50
    W = [60, 90]
    elems = [_rows(20, y0, [('day', 'sales')], W, h=h, colors={0: '#0ea5e9'})]
    elems.append(_rows(20, y0 + h, days, W, h=h))
    elems.append(_rows(230, y0, [('running_total',)], [130], h=h, colors={0: '#10b981'}, step=1))
    elems.append(_rows(230, y0 + h, [(v,) for v in run], [130], h=h, step=1))
    elems.append(_rows(390, y0, [('moving_avg_3',)], [130], h=h, colors={0: '#8b5cf6'}, step=3))
    elems.append(_rows(390, y0 + h, [(v,) for v in mov], [130], h=h, step=3))

    def frame(r1, r2, color, st, label, out_x):
        y1, y2 = y0 + h * (r1 + 1), y0 + h * (r2 + 1)
        return (f'<g data-step="{st}" data-focus="{st}"><rect x="16" y="{y1 - 2}" width="{sum(W) + 8}" height="{y2 - y1 + 4}" rx="6" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="3"/>'
                f'<rect x="{out_x}" y="{y2 - h}" width="130" height="{h}" fill="none" stroke="{color}" stroke-width="3"/></g>'
                + stext(560, (y1 + y2) / 2 + 4, label, color, 12, anchor='start', step=st, bold=True))
    elems.append(frame(0, 4, '#10b981', 2, 'day 4: rows 1..4 → 1000', 230))
    elems.append(frame(2, 5, '#8b5cf6', 4, 'day 5: rows 3..5 → 700/3', 390))
    elems.append(stext(400, y0 + h * 7 + 26, 'Running total: ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW', 'green', 12, step=2))
    elems.append(stext(400, y0 + h * 7 + 46, 'Moving average: ROWS BETWEEN 2 PRECEDING AND CURRENT ROW', 'purple', 12, step=4))
    return anim(canvas(780, 345, *elems), [
        'A <strong>running total</strong> is <code>SUM(sales) OVER (ORDER BY day)</code>: each row adds its sales to everything before it.',
        'The <strong>frame</strong> for day 4 is every row from the start up to the current row (days 1–4): 100 + 300 + 200 + 400 = 1000. The frame grows by one row each day.',
        'A <strong>3-day moving average</strong> uses a frame of fixed size: the current row and the two before it.',
        'For day 5 the frame is days 3–5: (200 + 400 + 100) / 3 = 233.3. The frame <strong>slides</strong> down one row at a time. Days 1 and 2 average over fewer rows because nothing exists before them.',
    ])


# ------------------------------------------------------------------ s06 coding round
def islands_anim():
    dates = ['Jan 01', 'Jan 02', 'Jan 03', 'Jan 05', 'Jan 06', 'Jan 09', 'Jan 10', 'Jan 11', 'Jan 12']
    rn = [str(i + 1) for i in range(9)]
    key = ['Dec 31', 'Dec 31', 'Dec 31', 'Jan 01', 'Jan 01', 'Jan 03', 'Jan 03', 'Jan 03', 'Jan 03']
    gc = {'Dec 31': '#1e3a5f', 'Jan 01': '#3b2a5c', 'Jan 03': '#123b2c'}
    h, y0 = 28, 45
    elems = [_rows(20, y0, [('login_date',)], [110], h=h, colors={0: '#0ea5e9'})]
    elems.append(_rows(20, y0 + h, [(d,) for d in dates], [110], h=h))
    elems.append(_rows(20, y0 + h, [(d,) for d in dates], [110], h=h, step=3, colors={i: gc[k] for i, k in enumerate(key)}))
    elems.append(_rows(140, y0, [('rn',)], [60], h=h, colors={0: '#8b5cf6'}, step=2))
    elems.append(_rows(140, y0 + h, [(r,) for r in rn], [60], h=h, step=2))
    elems.append(_rows(210, y0, [('date − rn days',)], [130], h=h, colors={0: '#f59e0b'}, step=3))
    elems.append(_rows(210, y0 + h, [(k,) for k in key], [130], h=h, step=3, colors={i: gc[k] for i, k in enumerate(key)}))
    elems.append(stext(550, 300, 'Gaps after Jan 03 and Jan 06 split the dates into 3 streaks', 'red', 12, step=1))
    isl = [('Dec 31', 'Jan 01', 'Jan 03', '3'), ('Jan 01', 'Jan 05', 'Jan 06', '2'), ('Jan 03', 'Jan 09', 'Jan 12', '4')]
    elems.append(stext(560, 30, 'GROUP BY (date − rn)', 'green', 13, bold=True, step=4))
    elems.append(_rows(390, y0, [('group key', 'start', 'end', 'days')], [95, 85, 85, 55], h=h, colors={0: '#10b981'}, step=4))
    elems.append(_rows(390, y0 + h, isl, [95, 85, 85, 55], h=h, step=4, colors={0: gc['Dec 31'], 1: gc['Jan 01'], 2: gc['Jan 03']}))
    elems.append(f'<g data-step="5" data-focus="5"><rect x="390" y="{y0 + h}" width="320" height="{h}" fill="none" stroke="#fbbf24" stroke-width="3"/>'
                 f'<rect x="390" y="{y0 + 3 * h}" width="320" height="{h}" fill="none" stroke="#fbbf24" stroke-width="3"/></g>')
    elems.append(stext(550, y0 + h * 5 + 10, 'HAVING COUNT(*) &gt;= 3 → streaks of 3 and 4 days', 'amber', 12, step=5, bold=True))
    return anim(canvas(780, 345, *elems), [
        'One user\'s login dates, sorted. Some days are consecutive and some have gaps. We want each unbroken streak (an <strong>island</strong>).',
        'Number the rows in date order with <code>ROW_NUMBER()</code>. Inside a streak, the date and the row number both go up by exactly 1.',
        'So <strong>date − row_number</strong> stays constant inside a streak and changes after every gap. That constant is a group key for the island.',
        'Group by that key: MIN(date) is the start, MAX(date) the end, COUNT(*) the length. Three islands of 3, 2 and 4 days.',
        'Filter with HAVING to answer "users who logged in on 3 or more consecutive days". The same trick finds consecutive seat numbers, salary-increase streaks and so on.',
    ])


# ------------------------------------------------------------------ s07 performance
def sargable_anim():
    dates = ['Jan 03', 'Jan 09', 'Jan 21', 'Jan 28', 'Feb 02', 'Feb 14', 'Feb 25', 'Mar 04', 'Mar 10', 'Mar 18']
    w, gap, x0 = 66, 8, 20
    elems = [stext(390, 28, 'Index idx_order_date: leaf entries stored in sorted order', '#38bdf8', 13, bold=True)]
    row1 = ''.join(scell(x0 + i * (w + gap), 40, w, 30, d, '#1e3a5f') for i, d in enumerate(dates))
    elems.append(f'<g>{row1}</g>')
    elems.append(_clause(20, 95, 740, 28, "WHERE order_date &gt;= '2026-02-01' AND order_date &lt; '2026-03-01'", step=1, size=11, color='#14532d'))
    hits = ''.join(f'<rect x="{x0 + i * (w + gap)}" y="40" width="{w}" height="30" fill="#10b981" fill-opacity="0.35" stroke="#10b981" stroke-width="3"/>'
                   for i in (4, 5, 6))
    elems.append(f'<g data-step="2" data-focus="2">{hits}</g>')
    sx = x0 + 4 * (w + gap) + w / 2
    elems.append(sarrow(sx, 93, sx, 74, 'green', step=2))
    elems.append(stext(sx, 165, 'seek: jump straight to Feb 02', 'green', 12, step=2, bold=True))
    elems.append(stext(x0 + 7 * (w + gap) + w / 2, 165, 'stop at Mar 04', 'green', 12, step=2))
    elems.append(stext(390, 190, '3 entries read  (access type: range)', 'green', 12, step=2, bold=True))
    elems.append(_clause(20, 215, 740, 28, 'WHERE MONTH(order_date) = 2', step=3, size=11, color='#7f1d1d'))
    row2 = ''.join(scell(x0 + i * (w + gap), 255, w, 30, ('2' if d.startswith('Feb') else ('1' if d.startswith('Jan') else '3')),
                         '#4b1d1d', '#fecaca') for i, d in enumerate(dates))
    elems.append(f'<g data-step="3">{row2}</g>')
    elems.append(stext(22, 252, 'MONTH(order_date) computed for each entry:', '#fca5a5', 10, anchor='start', step=3))
    elems.append(sflow(x0, 300, x0 + 10 * (w + gap) - gap, 300, 'red', step=3, count=4, dur=2.4))
    elems.append(stext(390, 322, 'MONTH() must be computed for every entry: the sorted order is useless → full scan (type: ALL)',
                       'red', 12, step=3, bold=True))
    elems.append(stext(390, 348, 'Rule: leave the column bare and move the calculation to the constant side', 'amber', 13, step=4, bold=True, focus='4'))
    return anim(canvas(780, 362, *elems), [
        'An index on <code>order_date</code> keeps the dates sorted. Sorted data is what lets MySQL <em>search</em> instead of scanning.',
        'A range on the bare column lets MySQL binary-search (seek) to the first February entry, read forward and stop at the first March entry. Only the matching entries are touched.',
        'Wrap the column in a function and the index order no longer helps: MySQL cannot know where MONTH() = 2 starts, so it computes the function for every row. The predicate is not <strong>sargable</strong> (Search ARGument ABLE).',
        'The same applies to <code>DATE(created_at) = …</code>, <code>amount * 1.18 &gt; …</code>, <code>LOWER(email) = …</code> and implicit type casts. Rewrite them as ranges on the raw column, or index the expression (functional index).',
    ])


def keyset_anim():
    elems = [stext(390, 25, 'orders table: 2,00,000 rows in primary-key order', '#38bdf8', 13, bold=True)]
    X0, X1 = 20, 760
    elems.append(f'<rect x="{X0}" y="38" width="{X1 - X0}" height="34" rx="4" fill="#162033" stroke="#334155"/>')
    for k in range(0, 11):
        x = X0 + (X1 - X0) * k / 10
        elems.append(stext(x, 88, f'{k * 20}K', '#64748b', 10))
    elems.append('<g data-step="1"><rect x="20" y="38" width="6" height="34" fill="#10b981"/></g>')
    elems.append(stext(30, 112, 'Page 1: LIMIT 10 OFFSET 0 → reads 10 rows', 'green', 12, anchor='start', step=1, bold=True))
    xo = X0 + (X1 - X0) * 0.5
    elems.append(f'<g data-step="2" data-focus="2" class="sbox"><rect x="{X0}" y="38" width="{xo - X0}" height="34" fill="#ef4444" fill-opacity="0.45" stroke="#ef4444"/>'
                 f'<rect x="{xo}" y="38" width="6" height="34" fill="#f59e0b"/></g>')
    elems.append(_clause(20, 130, 740, 28, 'SELECT … FROM orders ORDER BY order_id LIMIT 10 OFFSET 100000;', step=2, size=11, color='#7f1d1d'))
    elems.append(stext(390, 180, 'reads 1,00,010 rows and throws away 1,00,000 of them; deeper pages get slower and slower', 'red', 12, step=2, bold=True))
    elems.append(f'<g data-step="3"><rect x="{X0}" y="200" width="{X1 - X0}" height="34" rx="4" fill="#162033" stroke="#334155"/>'
                 f'<rect x="{xo}" y="200" width="6" height="34" fill="#10b981"/></g>')
    elems.append(sarrow(xo + 3, 270, xo + 3, 238, 'green', step=3))
    elems.append(_clause(20, 280, 740, 28, 'SELECT … FROM orders WHERE order_id &gt; 100000 ORDER BY order_id LIMIT 10;', step=3, size=11, color='#14532d'))
    elems.append(stext(390, 330, 'seeks in the primary-key index to 1,00,001 and reads just 10 rows; every page costs the same', 'green', 12, step=3, bold=True))
    elems.append(stext(390, 352, 'The app remembers the last id it showed and passes it to the next request', 'amber', 12, step=4, bold=True, focus='4'))
    return anim(canvas(780, 365, *elems), [
        'The first page is cheap: MySQL reads 10 rows from the start of the index and stops.',
        'For page 10,001 with <code>OFFSET 100000</code>, MySQL cannot jump to row 1,00,001. It must walk through 1,00,000 rows and discard them before returning 10. Cost grows with page depth.',
        '<strong>Keyset (seek) pagination</strong> filters on the last key seen. <code>order_id &gt; 100000</code> is an index range, so MySQL jumps straight there and reads only 10 rows, at any depth.',
        'Trade-offs: you can only go next/previous, not jump to "page 537", and the sort key must be unique (add the id as a tie-breaker, e.g. <code>(created_at, id) &gt; (?, ?)</code>).',
    ])


# ------------------------------------------------------------------ s08 data engineering
def upsert_anim():
    W = [50, 80, 80]
    elems = [stable(20, 45, ['id', 'name', 'balance'], [['1', 'Asha', '500'], ['2', 'Ravi', '300']], W, title='target: accounts', title_color='blue'),
             stable(300, 45, ['id', 'name', 'balance'], [['2', 'Ravi', '450'], ['3', 'Neha', '200']], W, title='incoming batch', title_color='purple',
                    focus_rows={0: '2', 1: '3'})]
    elems.append(_clause(20, 140, 740, 28, "INSERT … VALUES (2,'Ravi',450), (3,'Neha',200) AS new ON DUPLICATE KEY UPDATE balance = new.balance;", size=10, step=1))
    elems.append(sbox(540, 40, 220, 40, 'id 2 exists → PK conflict', 'UPDATE the existing row', 'amber', step=2, focus='2', size=12))
    elems.append(sbox(540, 88, 220, 40, 'id 3 is new', 'INSERT a new row', 'green', step=3, focus='3', size=12))
    elems.append(sarrow(512, 84, 538, 62, 'amber', step=2))
    elems.append(sarrow(512, 110, 538, 108, 'green', step=3))
    elems.append(stable(20, 205, ['id', 'name', 'balance'], [['1', 'Asha', '500'], ['2', 'Ravi', '450'], ['3', 'Neha', '200']], W,
                        title='after upsert', title_color='green', step=4, focus_rows={1: '4', 2: '4'}))
    elems.append(stext(240, 245, 'row 1 untouched', '#94a3b8', 11, anchor='start', step=4))
    elems.append(stext(240, 271, 'updated  (counts as 2 affected rows)', 'amber', 11, anchor='start', step=4))
    elems.append(stext(240, 297, 'inserted (counts as 1 affected row)', 'green', 11, anchor='start', step=4))
    elems.append(sbox(500, 200, 260, 110, 'REPLACE INTO is different', 'conflicting row is DELETED,\nthen a new row INSERTED:\nunlisted columns reset to defaults,\nDELETE triggers / FK cascades fire', 'red', step=5, size=12))
    return anim(canvas(780, 325, *elems), [
        'A pipeline delivers a batch with a changed row (Ravi) and a new row (Neha). We want one statement that inserts new keys and updates existing ones: an <strong>upsert</strong>.',
        'MySQL tries to insert id 2, hits the PRIMARY KEY (or any UNIQUE key) and, instead of failing, runs the <code>ON DUPLICATE KEY UPDATE</code> part on the existing row.',
        'id 3 causes no conflict, so it is inserted normally.',
        'Result: one statement, idempotent (running the same batch again gives the same table). Row-count tip: MySQL reports 1 per insert and 2 per update (0 if the update changed nothing).',
        '<code>REPLACE</code> looks similar but is delete + insert. Columns you did not supply lose their values, ON DELETE CASCADE can wipe child rows, and the auto-increment id changes. Prefer ON DUPLICATE KEY UPDATE for upserts.',
    ])


def cdc_anim():
    elems = [
        sbox(15, 120, 110, 60, 'Application', 'INSERT / UPDATE\n/ DELETE', 'gray', step=1, size=12),
        sflow(125, 150, 160, 150, 'cyan', step=1, count=2),
        sbox(160, 105, 120, 90, 'MySQL', 'InnoDB commit', 'blue', step=1, focus='1', size=13),
        sflow(280, 150, 315, 150, 'cyan', step=2, count=2),
        sbox(315, 95, 135, 110, 'Binary log', 'ROW events:\nbefore + after\nimage of each row', 'amber', step=2, focus='2', size=13),
        sflow(450, 150, 485, 150, 'amber', step=3, count=2),
        sbox(485, 105, 120, 90, 'Debezium', 'reads binlog\nlike a replica', 'purple', step=3, focus='3', size=13),
        sflow(605, 150, 640, 150, 'purple', step=4, count=2),
        sbox(640, 105, 125, 90, 'Kafka', 'topic per table', 'pink', step=4, focus='4', size=13),
        sflow(702, 195, 702, 240, 'pink', step=5, count=2),
        sbox(560, 240, 205, 70, 'Lake / Warehouse', 'MERGE latest change per key\n(S3, Delta, Snowflake …)', 'green', step=5, focus='5', size=13),
        stext(382, 230, 'offset saved: binlog file + position / GTID', 'purple', 11, step=6, bold=True),
        stext(260, 260, 'snapshot first, then stream changes', '#cbd5e1', 11, step=6),
        stext(260, 280, 'no load on tables, deletes captured', '#cbd5e1', 11, step=6),
    ]
    elems.append(stext(390, 40, "Requires binlog_format = ROW, binlog_row_image = FULL, a unique server_id", 'amber', 12, step=2, bold=True))
    elems.append(stext(390, 60, "and a user with REPLICATION SLAVE, REPLICATION CLIENT, SELECT", 'amber', 12, step=2))
    return anim(canvas(780, 325, *elems), [
        'The application changes rows normally. Nothing in the application needs to know about CDC.',
        'On commit, MySQL writes every change to the <strong>binary log</strong>. In <strong>ROW</strong> format each event carries the before and after values of the row, including DELETEs.',
        'A CDC connector such as <strong>Debezium</strong> connects as if it were a replica and reads the binlog stream, turning each event into a change record (op = c/u/d, before, after).',
        'Changes are published to <strong>Kafka</strong>, usually one topic per table, in commit order per key.',
        'A sink job (Spark, Flink, Kafka Connect) applies them to the lake or warehouse, typically a MERGE keeping the latest change per primary key.',
        'The connector stores its position (binlog file + offset or GTID) so it resumes exactly where it stopped. It first takes a consistent snapshot of existing rows, then switches to streaming.',
    ])
