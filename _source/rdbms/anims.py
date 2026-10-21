from build import *


def fk_integrity():
    elems = [
        stable(30, 50, ['dept_id', 'dept_name'], [['1', 'Big Data'], ['2', 'AI']], [80, 120], title='departments (parent)', title_color='blue'),
        stable(380, 50, ['student_id', 'name', 'dept_id'], [['101', 'Asha', '1'], ['102', 'Rohit', '2']], [100, 100, 80],
               title='students (child)', title_color='green', focus_rows={0: '1', 1: '1'}),
        sarrow(612, 89, 112, 89, 'pink', step=1, mid=(360, 20)),
        stext(360, 32, 'every dept_id must exist in the parent', 'pink', 12, step=1),
        '<g data-step="2" data-focus="2">' + scell(380, 128, 100, 26, '103', '#7f1d1d', '#fecaca') + scell(480, 128, 100, 26, 'Meera', '#7f1d1d', '#fecaca')
        + scell(580, 128, 80, 26, '9', '#7f1d1d', '#fecaca', bold=True) + '</g>',
        '<g data-step="3"><line x1="382" y1="141" x2="658" y2="141" stroke="#ef4444" stroke-width="2"/></g>',
        stext(520, 200, '✘ INSERT rejected: dept 9 does not exist', 'red', 12, step=2, bold=True),
        '<g data-step="3"><rect x="28" y="74" width="204" height="28" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="5,4"/></g>',
        stext(130, 140, '✘ DELETE dept 1 blocked:', 'red', 12, step=3, focus=3, bold=True),
        stext(130, 158, 'student 101 still points to it', 'red', 12, step=3),
        '<g data-step="4" data-focus="4">' + scell(380, 154, 100, 26, '104', '#064e3b', '#bbf7d0') + scell(480, 154, 100, 26, 'Kiran', '#064e3b', '#bbf7d0')
        + scell(580, 154, 80, 26, 'NULL', '#064e3b', '#bbf7d0') + '</g>',
        stext(520, 220, '✔ NULL FK allowed: "no department yet"', 'green', 12, step=4, bold=True),
    ]
    return anim(canvas(760, 235, *elems), [
        'The <code>dept_id</code> column in <strong>students</strong> is a foreign key referring to <code>departments.dept_id</code>. Students is the <em>child</em> table and departments the <em>parent</em>.',
        'Inserting a student with <code>dept_id = 9</code> fails because department 9 does not exist. The database blocks <strong>orphan</strong> rows on INSERT and UPDATE.',
        'Deleting department 1 also fails (with the default RESTRICT action) because a student still refers to it. The database protects the relationship from the parent side too.',
        'A <strong>NULL</strong> foreign key is allowed unless the column is declared NOT NULL. It means "no relationship yet", and referential integrity only checks non-NULL values.',
    ])


def cascade_anim():
    elems = [
        stable(30, 50, ['order_id', 'customer'], [['5001', 'Asha'], ['5002', 'Rohit']], [90, 110], title='orders', title_color='blue',
               focus_rows={0: '1'}),
        stable(330, 50, ['order_id', 'product', 'qty'], [['5001', 'P1', '2'], ['5001', 'P7', '1'], ['5002', 'P3', '5']], [90, 90, 60],
               title='order_items  (ON DELETE CASCADE)', title_color='green', focus_rows={0: '2', 1: '2'}),
        stext(130, 160, 'DELETE FROM orders', 'amber', 12, step=1, bold=True),
        stext(130, 178, 'WHERE order_id = 5001', 'amber', 12, step=1, bold=True),
        '<g data-step="1"><line x1="32" y1="89" x2="228" y2="89" stroke="#ef4444" stroke-width="2"/></g>',
        sarrow(232, 89, 328, 89, 'red', step=2), sarrow(232, 89, 328, 115, 'red', step=2),
        '<g data-step="2"><line x1="332" y1="89" x2="568" y2="89" stroke="#ef4444" stroke-width="2"/><line x1="332" y1="115" x2="568" y2="115" stroke="#ef4444" stroke-width="2"/></g>',
        stext(450, 175, 'children deleted automatically', 'red', 12, step=2),
        stable(330, 205, ['customer_id', 'name'], [['C9', 'Zoya']], [110, 110], title='customers', title_color='purple', step=3),
        stable(600, 205, ['order', 'cust'], [['7001', 'NULL']], [70, 70], title='orders (SET NULL)', title_color='purple', step=3, focus_rows={0: '3'}),
        stext(160, 248, 'ON DELETE SET NULL: order kept,', 'purple', 12, step=3, focus=3),
        stext(160, 266, 'link to deleted customer cleared', 'purple', 12, step=3),
    ]
    return anim(canvas(760, 290, *elems), [
        'Order 5001 is deleted from the parent table <strong>orders</strong>.',
        'Because the foreign key on <strong>order_items</strong> was declared <code>ON DELETE CASCADE</code>, the database automatically deletes the two child rows of order 5001. Order 5002 is untouched.',
        'With <code>ON DELETE SET NULL</code>, the child row is kept but its foreign key becomes NULL. This is useful when the child still has value on its own, such as keeping order history after a customer account is removed.',
    ])


def normalize_2nf_3nf():
    elems = [
        stable(20, 45, ['student_id', 'course_id', 'student_name', 'course_name', 'grade'],
               [['101', 'C1', 'Asha', 'SQL', 'A'], ['101', 'C2', 'Asha', 'Spark', 'B'], ['102', 'C1', 'Rohit', 'SQL', 'A']],
               [90, 85, 110, 105, 60], title='enrollments: key = (student_id, course_id)', title_color='red', step=1),
        '<g data-focus="2" data-step="2"><rect x="198" y="68" width="116" height="80" fill="none" stroke="#fbbf24" stroke-width="2" stroke-dasharray="5,4"/>'
        '<rect x="316" y="68" width="101" height="80" fill="none" stroke="#fbbf24" stroke-width="2" stroke-dasharray="5,4"/></g>',
        stext(320, 170, 'student_name depends only on student_id; course_name only on course_id → partial dependency', 'amber', 12, step=2),
        stable(20, 215, ['student_id', 'student_name'], [['101', 'Asha'], ['102', 'Rohit']], [90, 110], title='students', title_color='green', step=3, focus_rows={0: '3', 1: '3'}),
        stable(255, 215, ['course_id', 'course_name'], [['C1', 'SQL'], ['C2', 'Spark']], [85, 105], title='courses', title_color='green', step=3, focus_rows={0: '3', 1: '3'}),
        stable(480, 215, ['student_id', 'course_id', 'grade'], [['101', 'C1', 'A'], ['101', 'C2', 'B'], ['102', 'C1', 'A']], [90, 85, 60],
               title='enrollments', title_color='green', step=4, focus_rows={0: '4', 1: '4', 2: '4'}),
        stext(380, 345, '"Asha" is now stored once: rename her in one row, no anomalies', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 360, *elems), [
        'This table is in 1NF, with composite key (student_id, course_id). Notice "Asha" and "SQL" repeated on several rows.',
        '<code>student_name</code> depends only on <code>student_id</code>, and <code>course_name</code> only on <code>course_id</code>. Each depends on <em>part</em> of the key. This is a <strong>partial dependency</strong>, which 2NF forbids.',
        'Move each partially dependent column into a table keyed by the part it depends on: <strong>students</strong>(student_id, name) and <strong>courses</strong>(course_id, name).',
        'What remains in <strong>enrollments</strong> depends on the whole key: the grade a student got in a course.',
        'Each fact is now stored once. Updates touch one row, a new course can exist without students, and deleting an enrollment never loses course details.',
    ])


def acid_transfer():
    elems = [
        sbox(40, 50, 170, 60, 'Account A', '₹10,000', 'blue', step=1),
        sbox(550, 50, 170, 60, 'Account B', '₹5,000', 'blue', step=1),
        stext(380, 40, 'START TRANSACTION', 'amber', 13, step=1, focus=1, bold=True),
        sbox(40, 140, 170, 60, 'Account A', '₹5,000  (−5,000)', 'amber', step=2, focus=2),
        stext(380, 175, 'UPDATE A … −5000  (in undo log)', 'amber', 12, step=2),
        stext(380, 230, '💥 server crashes before crediting B', 'red', 13, step=3, focus=3, bold=True),
        sbox(40, 250, 170, 60, 'Account A', '₹10,000  restored', 'green', step=4, focus=4),
        stext(380, 285, 'on restart: undo log rolls back the uncommitted change', 'green', 12, step=4),
        stext(380, 330, 'Normal run: debit + credit → COMMIT → redo log flushed → survives any crash', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 350, *elems), [
        'A transfer of ₹5,000 from A to B starts as one <strong>transaction</strong>: two updates that must succeed or fail together.',
        'The debit from A is applied. The old value is recorded in the <strong>undo log</strong> so it can be reversed.',
        'The server crashes <em>before</em> the credit to B and before COMMIT. Without atomicity, ₹5,000 would simply vanish.',
        '<strong>Atomicity</strong>: on restart the database uses the undo log to roll back every uncommitted change, so A is back to ₹10,000. <strong>Consistency</strong> holds: the total money is unchanged.',
        'In a normal run both updates succeed and COMMIT writes to the <strong>redo log</strong> on disk. <strong>Durability</strong> means a crash after COMMIT can never lose the transfer, and <strong>isolation</strong> means nobody saw the half-done state in between.',
    ])


def dirty_read():
    elems = [
        stext(70, 40, 'T1', 'blue', 15, bold=True), stext(70, 200, 'T2', 'purple', 15, bold=True),
        '<line x1="100" y1="35" x2="740" y2="35" stroke="#334155" stroke-width="2"/>',
        '<line x1="100" y1="195" x2="740" y2="195" stroke="#334155" stroke-width="2"/>',
        sbox(110, 55, 200, 50, 'UPDATE balance = 0', 'not committed', 'blue', step=1, focus=1, size=12),
        sbox(300, 120, 160, 50, 'balance', '10,000 → 0 (uncommitted)', 'amber', step=1, fill_opacity=0.15, size=12),
        sbox(330, 215, 200, 50, 'SELECT balance → 0', 'READ UNCOMMITTED', 'purple', step=2, focus=2, size=12),
        sflow(380, 170, 420, 215, 'red', step=2, count=2),
        sbox(480, 55, 160, 50, 'ROLLBACK', 'balance back to 10,000', 'red', step=3, focus=3, size=12),
        stext(560, 290, 'T2 acted on a value that never officially existed', 'red', 12, step=4, focus=4, bold=True),
        stext(560, 310, 'READ COMMITTED or higher prevents this', 'green', 12, step=4),
    ]
    return anim(canvas(760, 325, *elems), [
        'Transaction T1 sets the balance to 0 but has <strong>not committed</strong> yet.',
        'T2 runs at <code>READ UNCOMMITTED</code> and reads the balance: it sees 0, an uncommitted value. This is a <strong>dirty read</strong>.',
        'T1 hits an error and <strong>rolls back</strong>, so the real balance is 10,000 again.',
        'T2 has already made a decision (for example rejecting a payment) based on data that never existed. Any isolation level from READ COMMITTED upward prevents dirty reads.',
    ])


def deadlock_anim():
    elems = [
        sbox(60, 60, 140, 60, 'T1', 'transfer A → B', 'blue'),
        sbox(560, 60, 140, 60, 'T2', 'transfer B → A', 'purple'),
        sbox(250, 210, 110, 50, 'row A', '', 'gray'),
        sbox(400, 210, 110, 50, 'row B', '', 'gray'),
        sarrow(150, 120, 290, 208, 'blue', step=1),
        stext(150, 175, 'locks A', 'blue', 12, step=1, focus=1, bold=True),
        sarrow(610, 120, 470, 208, 'purple', step=2),
        stext(610, 175, 'locks B', 'purple', 12, step=2, focus=2, bold=True),
        sarrow(200, 100, 420, 208, 'blue', step=3, dashed=True, mid=(330, 110)),
        stext(330, 95, 'T1 waits for B', 'blue', 12, step=3, focus=3),
        sarrow(560, 100, 330, 208, 'purple', step=4, dashed=True, mid=(440, 140)),
        stext(600, 150, 'T2 waits for A', 'purple', 12, step=4, focus=4),
        stext(380, 300, '🔁 cycle detected → InnoDB rolls back T2 (victim), T1 continues', 'red', 13, step=5, focus=5, bold=True),
        stext(380, 322, 'Prevention: always lock rows in the same order (e.g. lower account id first)', 'green', 12, step=6, focus=6),
    ]
    return anim(canvas(760, 340, *elems), [
        'T1 starts a transfer from A to B and updates row A, taking an <strong>exclusive lock</strong> on it.',
        'At the same moment T2 transfers from B to A and locks row B.',
        'T1 now needs row B to credit it, but B is locked by T2, so T1 <strong>waits</strong>.',
        'T2 needs row A, which T1 holds, so T2 waits too. Each waits for the other: a <strong>circular wait</strong> that can never resolve on its own.',
        'InnoDB\'s deadlock detector finds the cycle in its wait-for graph, rolls back the cheaper transaction (the <strong>victim</strong>, error 1213) and lets the other finish. The application should retry the victim.',
        'Prevention: make every transaction lock resources in the <strong>same order</strong>, keep transactions short, and index the WHERE columns so fewer rows get locked.',
    ])


def mvcc_anim():
    elems = [
        stext(70, 45, 'Session 1', 'blue', 13, bold=True), stext(70, 245, 'Session 2', 'purple', 13, bold=True),
        sbox(120, 20, 210, 46, 'START + SELECT fee', 'snapshot taken → 95,000', 'blue', step=1, focus=1, size=12),
        sbox(330, 110, 150, 70, 'courses row', 'v1: 95,000', 'gray', step=1, fill_opacity=0.15),
        sbox(330, 220, 220, 46, 'UPDATE fee = 98,000; COMMIT', '', 'purple', step=2, focus=2, size=12),
        sbox(500, 110, 150, 70, 'courses row', 'v2: 98,000 (latest)', 'green', step=2, focus=2),
        sarrow(480, 145, 498, 145, 'gray', step=2),
        stext(415, 198, 'v1 kept in undo log', 'gray', 11, step=2),
        sbox(120, 110, 180, 46, 'SELECT fee again', '→ 95,000 (same snapshot)', 'blue', step=3, focus=3, size=12),
        sflow(330, 145, 300, 135, 'blue', step=3, count=1),
        sbox(560, 20, 180, 46, 'COMMIT; new SELECT', '→ 98,000', 'blue', step=4, focus=4, size=12),
        stext(380, 300, 'Readers never block writers, writers never block readers', 'cyan', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 320, *elems), [
        'Session 1 starts a transaction at REPEATABLE READ and reads the fee: 95,000. InnoDB creates a <strong>read view</strong>, a snapshot of what is committed at that moment.',
        'Session 2 updates the fee to 98,000 and commits. It is <strong>not blocked</strong> by session 1\'s read. The old version stays in the undo log, linked from the new row.',
        'Session 1 reads again inside the same transaction. The newest version was committed after its snapshot, so InnoDB follows the undo chain and returns the old version: still 95,000.',
        'After session 1 commits, a new transaction gets a new snapshot and sees 98,000.',
        'That is <strong>MVCC</strong>: several versions of a row coexist, each transaction sees a consistent snapshot, and plain reads take no locks.',
    ])


def btree_search():
    elems = [
        stext(380, 26, 'Find student_id = 52', 'blue', 14, bold=True),
        sbox(320, 45, 120, 36, '40 | 70', '', 'blue', focus='1'),
        sbox(70, 120, 140, 36, '10 | 25', '', 'gray'),
        sbox(310, 120, 140, 36, '45 | 60', '', 'gray', focus='2'),
        sbox(550, 120, 140, 36, '75 | 90', '', 'gray'),
        sarrow(350, 81, 160, 118), sarrow(380, 81, 380, 118, 'amber'), sarrow(410, 81, 600, 118),
    ]
    leaves = ['5,8', '10,18', '25,33', '41,44', '45,52', '60,66', '75,81', '90,97']
    for i, lv in enumerate(leaves):
        x = 20 + i * 90
        elems.append(sbox(x, 200, 80, 34, lv, '', 'green', focus=('3' if lv == '45,52' else None), fill_opacity=0.18, size=12))
    elems += [
        sarrow(380, 156, 420, 198, 'amber'),
        stext(570, 68, '52 ≥ 40 and < 70 → middle child', 'amber', 12, step=1),
        stext(560, 175, '52 ≥ 45 and < 60 → this leaf', 'amber', 12, step=2),
        stext(420, 260, '52 found → row pointer → row', 'green', 13, step=3, bold=True),
        sbox(330, 275, 180, 36, 'row: 52, Meera, BDA', '', 'purple', step=4, focus=4, size=12),
        stext(380, 330, '3 page reads instead of scanning every row: O(log n)', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 345, *elems), [
        'The search starts at the <strong>root</strong>. 52 is between 40 and 70, so follow the middle pointer.',
        'In the internal node, 52 is between 45 and 60, so follow the pointer to the leaf that holds 45–59.',
        'The <strong>leaf</strong> contains key 52 with a pointer to the row (in InnoDB the clustered leaf <em>is</em> the row).',
        'Only 3 pages were read. Even with 10 million rows a B+ tree is typically 3–4 levels deep, which is why indexed lookups are so fast.',
    ])


def secondary_lookup():
    elems = [
        stext(190, 30, 'Secondary index on email', 'amber', 13, bold=True),
        stext(570, 30, 'Clustered index (PRIMARY KEY)', 'green', 13, bold=True),
        stable(70, 50, ['email', 'PK'], [['asha@x.com', '101'], ['meera@x.com', '103'], ['rohit@x.com', '102']], [160, 80],
               title=None, title_color='amber', focus_rows={0: '1'}),
        stable(430, 50, ['student_id', 'name', 'city', 'cgpa'], [['101', 'Asha', 'Pune', '8.7'], ['102', 'Rohit', 'Delhi', '7.9'], ['103', 'Meera', 'Agra', '9.1']],
               [90, 80, 80, 60], title_color='green', focus_rows={0: '2'}),
        sarrow(312, 89, 428, 89, 'amber', step=2),
        stext(370, 80, 'PK 101', 'amber', 11, step=2),
        stext(380, 190, "SELECT name, city FROM students WHERE email = 'asha@x.com'", 'cyan', 12, step=1),
        stext(380, 215, '1) seek secondary index → PK   2) seek clustered index → full row', 'gray', 12, step=2),
        stext(380, 245, "SELECT student_id FROM students WHERE email = …  → answered from the", 'green', 12, step=3, focus=3),
        stext(380, 263, 'secondary index alone (covering index, no second lookup)', 'green', 12, step=3),
    ]
    return anim(canvas(760, 280, *elems), [
        'The query filters on <code>email</code>, which has a secondary (non-clustered) index. InnoDB seeks that index and finds asha@x.com. Its "row pointer" is the <strong>primary key value</strong>, 101.',
        'To get <code>name</code> and <code>city</code>, InnoDB does a second seek into the <strong>clustered index</strong> by PK 101, whose leaf holds the full row. Two lookups per matching row.',
        'If every column the query needs is in the secondary index (plus the PK, which is always included), the second lookup is skipped. That is a <strong>covering index</strong>, shown as "Using index" in EXPLAIN.',
    ])


def query_pipeline():
    elems = [
        sbox(15, 60, 130, 70, 'SQL text', 'SELECT … JOIN …\nWHERE cgpa > 8', 'gray', step=1, focus=1, size=12),
        sbox(170, 60, 130, 70, 'Parser', 'syntax OK?\ntables exist?', 'blue', step=2, focus=2),
        sflow(145, 95, 170, 95, 'cyan', step=2, count=1),
        sbox(325, 60, 130, 70, 'Rewriter', 'expand views\nflatten subqueries', 'purple', step=3, focus=3),
        sflow(300, 95, 325, 95, 'cyan', step=3, count=1),
        sbox(480, 60, 130, 70, 'Optimizer', 'cost each plan\npick cheapest', 'amber', step=4, focus=4),
        sflow(455, 95, 480, 95, 'cyan', step=4, count=1),
        sbox(440, 170, 210, 60, 'plan A: scan + hash join', 'cost 9,200', 'red', step=4, size=12, fill_opacity=0.12),
        sbox(440, 240, 210, 60, 'plan B: index range + NL join', 'cost 310 ✔', 'green', step=4, size=12, fill_opacity=0.2),
        sbox(640, 60, 110, 70, 'Executor', 'reads pages\nreturns rows', 'green', step=5, focus=5),
        sflow(610, 95, 640, 95, 'green', step=5, count=1),
        stext(200, 220, 'statistics: rows, index cardinality,', 'amber', 12, step=4),
        stext(200, 238, 'histograms (ANALYZE TABLE)', 'amber', 12, step=4),
    ]
    return anim(canvas(760, 315, *elems), [
        'The client sends SQL text. It is only a string until the database understands it.',
        'The <strong>parser</strong> checks the syntax, builds a parse tree, verifies that tables and columns exist and that the user has privileges.',
        'The <strong>rewriter</strong> expands views, turns some subqueries into joins and simplifies expressions.',
        'The <strong>cost-based optimizer</strong> generates candidate plans (join order, join algorithm, which index) and estimates each one\'s cost from <strong>statistics</strong>. It picks the cheapest. Stale statistics lead to bad plans.',
        'The <strong>executor</strong> runs the chosen plan through the storage engine, reading pages from the buffer pool or disk, and streams the result rows back. <code>EXPLAIN</code> shows you this plan.',
    ])


def scd2_anim():
    elems = [
        stable(20, 50, ['key', 'cust_id', 'city', 'valid_from', 'valid_to', 'current'],
               [['1', 'C101', 'Pune', '2024-01-10', '9999-12-31', '1']],
               [50, 80, 90, 120, 120, 80], title='dim_customer', title_color='blue', focus_rows={0: '1'}),
        sbox(570, 40, 170, 50, 'source change', 'C101 moves → Mumbai', 'amber', step=2, focus=2, size=12),
        '<g data-step="3" data-focus="3">' + scell(360, 76, 120, 26, '2026-05-31', '#78350f', '#fde68a', bold=True)
        + scell(480, 76, 80, 26, '0', '#78350f', '#fde68a', bold=True) + '</g>',
        stext(300, 150, '① expire the current version', 'amber', 12, step=3),
        '<g data-step="4" data-focus="4">' + ''.join(scell(x, 102, w, 26, v, '#064e3b', '#bbf7d0') for x, w, v in
            [(20, 50, '2'), (70, 80, 'C101'), (150, 90, 'Mumbai'), (240, 120, '2026-06-01'), (360, 120, '9999-12-31'), (480, 80, '1')]) + '</g>',
        stext(300, 170, '② insert a new current version with a NEW surrogate key', 'green', 12, step=4),
        stable(20, 220, ['order', 'customer_key', 'date'], [['O-1', '1', '2025-03-15'], ['O-2', '2', '2026-08-02']], [70, 110, 110],
               title='fact_sales', title_color='purple', step=5, focus_rows={0: '5', 1: '5'}),
        stext(520, 260, 'old sales stay linked to Pune (key 1),', 'purple', 12, step=5),
        stext(520, 278, 'new sales link to Mumbai (key 2)', 'purple', 12, step=5),
    ]
    return anim(canvas(760, 310, *elems), [
        'Customer C101 has one current row in the dimension: surrogate key 1, city Pune, valid from 2024 to "forever" (9999-12-31), current flag = 1.',
        'The source system reports that C101 has moved to Mumbai on 1 June 2026.',
        '<strong>Step 1</strong>: the existing row is expired. Its <code>valid_to</code> becomes 31 May 2026 and its current flag becomes 0. Nothing is deleted.',
        '<strong>Step 2</strong>: a new row is inserted with a <strong>new surrogate key</strong> (2), the new city, valid from 1 June, current = 1.',
        'Facts keep the surrogate key that was current when they happened, so revenue by city stays historically correct. That is why SCD Type 2 needs surrogate keys.',
    ])
