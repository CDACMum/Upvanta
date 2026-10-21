from build import *
from rdbms.anims import *

SECTION = dict(level='advanced', title='Transactions & Concurrency', questions=[

# ------------------------------------------------------------------ 29
Q('What is a Transaction?', 'Transaction', minutes=5, cards=[
    definition(
        defbox('A <strong>transaction</strong> is a sequence of one or more database operations that is treated as a '
               '<strong>single logical unit of work</strong>. Either <strong>all</strong> of its operations take effect '
               '(COMMIT), or <strong>none</strong> of them do (ROLLBACK).'),
        hl('Transferring ₹5,000 from A to B is two updates — debit A, credit B. If the system crashes between them, '
           'money must not vanish. A transaction guarantees both happen or neither does.', 'Classic example'),
        tags('Transaction', 'Unit of Work', 'COMMIT', 'ROLLBACK', 'Atomicity'),
    ),
    example(
        code("""
START TRANSACTION;

UPDATE accounts SET balance = balance - 5000 WHERE acc_no = 'A101';
UPDATE accounts SET balance = balance + 5000 WHERE acc_no = 'B202';

-- Both succeeded → make them permanent
COMMIT;

-- If anything had failed, we would run:
-- ROLLBACK;   → both updates are undone
"""),
        code("""
# Python (mysql-connector) — how applications use transactions
conn.autocommit = False
try:
    cur.execute("UPDATE accounts SET balance = balance - %s WHERE acc_no = %s", (5000, 'A101'))
    cur.execute("UPDATE accounts SET balance = balance + %s WHERE acc_no = %s", (5000, 'B202'))
    conn.commit()
except Exception:
    conn.rollback()
    raise
""", 'Python', 'fa-code'),
        title='Example: Fund Transfer'),
    crossq(
        ('What is autocommit?',
         'In autocommit mode (MySQL\'s default), every single statement is its own transaction and is committed '
         'immediately. <code>START TRANSACTION</code> (or <code>SET autocommit = 0</code>) groups statements until COMMIT/ROLLBACK.'),
        ('Do SELECT statements run inside transactions?',
         'Yes. A SELECT reads a consistent snapshot according to the isolation level. In InnoDB with REPEATABLE READ, '
         'all SELECTs in one transaction see the same snapshot.'),
        ('Which statements cannot be rolled back in MySQL?',
         'DDL statements — CREATE, ALTER, DROP, TRUNCATE, RENAME — cause an implicit commit. Changes to non-transactional '
         'tables (MyISAM) also cannot be rolled back.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('Explain ACID properties', 'ACID Properties', minutes=8, cards=[
    definition(
        defbox('<strong>ACID</strong> is the set of four properties that guarantee database transactions are processed reliably.'),
        table(['Property', 'Guarantee', 'Bank-transfer example', 'Implemented by'], [
            ['Atomicity', 'All or nothing', 'Debit without credit never happens', 'Undo log / rollback segments'],
            ['Consistency', 'DB moves from one valid state to another; all constraints hold', 'Total money is the same before and after; balance never negative (CHECK)', 'Constraints, triggers + correct application logic'],
            ['Isolation', 'Concurrent transactions do not interfere; result as if run one after another', 'Another user never sees A debited but B not yet credited', 'Locks, MVCC, isolation levels'],
            ['Durability', 'Once committed, changes survive crashes and power failures', 'After "Transfer successful", a crash does not undo it', 'Redo log / write-ahead log (WAL), flush to disk'],
        ]),
        tags('ACID', 'Atomicity', 'Consistency', 'Isolation', 'Durability', 'WAL', 'Redo Log', 'Undo Log'),
    ),
    acid_transfer(),
    visual(svg("""
<svg width="760" height="240" viewBox="0 0 760 240" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="240" fill="#1e293b"/>
  <g text-anchor="middle">
    <rect x="25" y="40" width="165" height="160" rx="12" fill="#0ea5e9" opacity="0.18" stroke="#0ea5e9" stroke-width="2"/>
    <text x="107" y="95" font-size="44" fill="#38bdf8" font-weight="bold">A</text><text x="107" y="125" font-size="15" fill="#f1f5f9" font-weight="bold">Atomicity</text><text x="107" y="150" font-size="12" fill="#cbd5e1">all or nothing</text><text x="107" y="175" font-size="11" fill="#94a3b8">undo log</text>
    <rect x="207" y="40" width="165" height="160" rx="12" fill="#10b981" opacity="0.18" stroke="#10b981" stroke-width="2"/>
    <text x="289" y="95" font-size="44" fill="#34d399" font-weight="bold">C</text><text x="289" y="125" font-size="15" fill="#f1f5f9" font-weight="bold">Consistency</text><text x="289" y="150" font-size="12" fill="#cbd5e1">valid → valid state</text><text x="289" y="175" font-size="11" fill="#94a3b8">constraints</text>
    <rect x="389" y="40" width="165" height="160" rx="12" fill="#f59e0b" opacity="0.18" stroke="#f59e0b" stroke-width="2"/>
    <text x="471" y="95" font-size="44" fill="#fbbf24" font-weight="bold">I</text><text x="471" y="125" font-size="15" fill="#f1f5f9" font-weight="bold">Isolation</text><text x="471" y="150" font-size="12" fill="#cbd5e1">no interference</text><text x="471" y="175" font-size="11" fill="#94a3b8">locks / MVCC</text>
    <rect x="571" y="40" width="165" height="160" rx="12" fill="#8b5cf6" opacity="0.18" stroke="#8b5cf6" stroke-width="2"/>
    <text x="653" y="95" font-size="44" fill="#a78bfa" font-weight="bold">D</text><text x="653" y="125" font-size="15" fill="#f1f5f9" font-weight="bold">Durability</text><text x="653" y="150" font-size="12" fill="#cbd5e1">survives crashes</text><text x="653" y="175" font-size="11" fill="#94a3b8">redo log / WAL</text>
  </g>
</svg>""", 'Each ACID property and the mechanism the DBMS uses to provide it')),
    explanation(
        p('<strong>How durability works — write-ahead logging (WAL):</strong> before a changed data page is written to '
          'the data file, the change is first appended to a sequential log (InnoDB: the <em>redo log</em>) and flushed '
          'to disk at COMMIT. After a crash, the DBMS replays the redo log to restore committed changes and uses the '
          '<em>undo log</em> to roll back uncommitted ones.'),
        p('In MySQL, <code>innodb_flush_log_at_trx_commit = 1</code> (default) flushes the log on every commit — full '
          'durability. Values 0 or 2 are faster but can lose about one second of commits on a crash.'),
    ),
    crossq(
        ('Which ACID property is the responsibility of the application rather than the DBMS?',
         '<strong>Consistency</strong>, partly. The DBMS enforces declared constraints, but business rules such as '
         '"total money is preserved" depend on the transaction being written correctly.'),
        ('What is BASE?',
         'The NoSQL alternative: <strong>B</strong>asically <strong>A</strong>vailable, <strong>S</strong>oft state, '
         '<strong>E</strong>ventual consistency. It trades strict consistency for availability and scale (Cassandra, DynamoDB).'),
        ('Does MongoDB support ACID?',
         'Single-document operations have always been atomic; multi-document ACID transactions are supported since MongoDB 4.0 (replica sets) and 4.2 (sharded clusters).'),
        ('Is ACID guaranteed in MyISAM?',
         'No. MyISAM has no transactions, no rollback and only table-level locks. InnoDB is the ACID-compliant engine in MySQL.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('What are the states of a transaction?', 'Transaction States', minutes=5, cards=[
    definition(
        table(['State', 'Meaning'], [
            ['Active', 'The transaction is executing its read/write operations'],
            ['Partially committed', 'The last statement has executed; changes are still in memory/logs, not yet guaranteed'],
            ['Committed', 'All changes are permanently recorded; durability guaranteed'],
            ['Failed', 'An error occurred, or the transaction can no longer proceed normally'],
            ['Aborted', 'All changes have been rolled back; database restored to the state before the transaction'],
            ['Terminated', 'The transaction has left the system (after commit or abort)'],
        ]),
        tags('Active', 'Partially Committed', 'Committed', 'Failed', 'Aborted', 'Terminated'),
    ),
    visual(svg("""
<svg width="760" height="260" viewBox="0 0 760 260" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="260" fill="#1e293b"/>
  <defs><marker id="ar" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/></marker></defs>
  <g text-anchor="middle" font-size="14" font-weight="bold">
    <ellipse cx="90" cy="130" rx="65" ry="30" fill="#0ea5e9" opacity="0.25" stroke="#0ea5e9" stroke-width="2"/><text x="90" y="135" fill="#f1f5f9">Active</text>
    <ellipse cx="300" cy="60" rx="95" ry="32" fill="#f59e0b" opacity="0.2" stroke="#f59e0b" stroke-width="2"/><text x="300" y="56" fill="#f1f5f9">Partially</text><text x="300" y="74" fill="#f1f5f9">committed</text>
    <ellipse cx="510" cy="60" rx="75" ry="30" fill="#10b981" opacity="0.25" stroke="#10b981" stroke-width="2"/><text x="510" y="65" fill="#f1f5f9">Committed</text>
    <ellipse cx="300" cy="200" rx="65" ry="30" fill="#ef4444" opacity="0.25" stroke="#ef4444" stroke-width="2"/><text x="300" y="205" fill="#f1f5f9">Failed</text>
    <ellipse cx="510" cy="200" rx="70" ry="30" fill="#ef4444" opacity="0.15" stroke="#f87171" stroke-width="2"/><text x="510" y="205" fill="#f1f5f9">Aborted</text>
    <ellipse cx="680" cy="130" rx="70" ry="30" fill="#8b5cf6" opacity="0.25" stroke="#8b5cf6" stroke-width="2"/><text x="680" y="135" fill="#f1f5f9">Terminated</text>
  </g>
  <g stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#ar)">
    <line x1="140" y1="110" x2="210" y2="72"/><line x1="395" y1="60" x2="432" y2="60"/>
    <line x1="140" y1="150" x2="233" y2="192"/><line x1="300" y1="92" x2="300" y2="168"/>
    <line x1="365" y1="200" x2="437" y2="200"/><line x1="580" y1="75" x2="625" y2="105"/><line x1="575" y1="188" x2="625" y2="155"/>
  </g>
  <g font-size="11" fill="#cbd5e1"><text x="128" y="78">last stmt</text><text x="160" y="185">error</text><text x="400" y="50">flush</text><text x="310" y="135">fail</text><text x="380" y="190">rollback</text></g>
</svg>""", 'Transaction state diagram')),
    crossq(
        ('After a transaction is aborted, what can the system do?',
         'It can <strong>restart</strong> the transaction (if the failure was temporary, e.g. a deadlock victim) or '
         '<strong>kill</strong> it (if it was a logical error such as bad input).'),
        ('Why is "partially committed" not the same as committed?',
         'The changes may still be only in memory buffers. Until the commit record is flushed to the log on disk, a '
         'crash would lose them — so the transaction could still fail.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('Explain COMMIT, ROLLBACK and SAVEPOINT', 'COMMIT, ROLLBACK & SAVEPOINT', minutes=6, cards=[
    definition(
        table(['Command', 'Purpose'], [
            ['START TRANSACTION / BEGIN', 'Starts a new transaction (turns off autocommit until it ends)'],
            ['COMMIT', 'Makes all changes of the transaction permanent and visible to others'],
            ['ROLLBACK', 'Undoes all changes made since the transaction started'],
            ['SAVEPOINT name', 'Marks a point inside a transaction to which you can roll back partially'],
            ['ROLLBACK TO SAVEPOINT name', 'Undoes changes made after that savepoint; the transaction stays active'],
            ['RELEASE SAVEPOINT name', 'Removes the savepoint (does not commit anything)'],
        ]),
        tags('TCL', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'Partial Rollback'),
    ),
    example(
        code("""
START TRANSACTION;

INSERT INTO orders VALUES (5001, 101, '2026-10-01');
SAVEPOINT after_order;

INSERT INTO order_items VALUES (5001, 'P1', 2);
INSERT INTO order_items VALUES (5001, 'P9', 1);   -- wrong product added
ROLLBACK TO SAVEPOINT after_order;                -- undo only the items

INSERT INTO order_items VALUES (5001, 'P2', 1);   -- correct item
COMMIT;

-- Result: order 5001 with only item P2
"""),
        title='Example: Partial Rollback'),
    crossq(
        ('Does ROLLBACK TO SAVEPOINT end the transaction?',
         'No. The transaction is still open; you must still COMMIT or ROLLBACK. Savepoints created after the one you rolled back to are discarded.'),
        ('Can you roll back after COMMIT?',
         'No. Committed changes are durable. To reverse them you must run new compensating statements, or restore from a backup / point-in-time recovery.'),
        ('Where are savepoints useful in practice?',
         'In long batch jobs and stored procedures — if one step of a multi-step load fails you can undo just that step and continue or retry.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What are Dirty Read, Non-repeatable Read, Phantom Read and Lost Update?', 'Concurrency Problems', minutes=8, cards=[
    definition(
        defbox('When transactions run concurrently without enough isolation, they can see or overwrite each other\'s '
               'intermediate work. These are the standard <strong>read phenomena</strong>.'),
        table(['Problem', 'What happens'], [
            ['Dirty read', 'T1 reads data written by T2 that is <strong>not yet committed</strong>; T2 then rolls back, so T1 used data that never existed'],
            ['Non-repeatable read', 'T1 reads a row twice and gets <strong>different values</strong> because T2 updated and committed it in between'],
            ['Phantom read', 'T1 runs the same query twice and gets <strong>new or missing rows</strong> because T2 inserted/deleted matching rows'],
            ['Lost update', 'T1 and T2 both read a value, both modify it, and the later write <strong>overwrites</strong> the earlier one'],
        ]),
        tags('Dirty Read', 'Non-repeatable Read', 'Phantom Read', 'Lost Update', 'Read Phenomena'),
    ),
    dirty_read(),
    example(
        code("""
-- DIRTY READ
T1: UPDATE accounts SET balance = 0 WHERE id = 1;      -- not committed
T2: SELECT balance FROM accounts WHERE id = 1;         -- sees 0
T1: ROLLBACK;                                          -- balance back to 10000
-- T2 acted on a value that never officially existed

-- NON-REPEATABLE READ
T1: SELECT balance FROM accounts WHERE id = 1;         -- 10000
T2: UPDATE accounts SET balance = 8000 WHERE id = 1; COMMIT;
T1: SELECT balance FROM accounts WHERE id = 1;         -- 8000  (same row, new value)

-- PHANTOM READ
T1: SELECT COUNT(*) FROM students WHERE dept_id = 1;   -- 30
T2: INSERT INTO students VALUES (999, 'New', 1); COMMIT;
T1: SELECT COUNT(*) FROM students WHERE dept_id = 1;   -- 31  (a "phantom" row)

-- LOST UPDATE
T1: SELECT stock FROM products WHERE id = 7;           -- 10
T2: SELECT stock FROM products WHERE id = 7;           -- 10
T1: UPDATE products SET stock = 9 WHERE id = 7; COMMIT;   -- sold 1
T2: UPDATE products SET stock = 9 WHERE id = 7; COMMIT;   -- sold 1, but writes 9 again
-- Two items sold, stock reduced by only one
""", 'Timelines', 'fa-timeline'),
        title='Example: Each Problem Step by Step'),
    explanation(
        p('<strong>Avoiding the lost update:</strong>'),
        code("""
-- 1) Do the arithmetic in the database (atomic)
UPDATE products SET stock = stock - 1 WHERE id = 7 AND stock > 0;

-- 2) Pessimistic: lock the row while reading
START TRANSACTION;
SELECT stock FROM products WHERE id = 7 FOR UPDATE;
UPDATE products SET stock = stock - 1 WHERE id = 7;
COMMIT;

-- 3) Optimistic: version column
UPDATE products SET stock = 9, version = version + 1
WHERE id = 7 AND version = 3;    -- 0 rows affected → someone else changed it → retry
"""),
        title='Fixes'),
    crossq(
        ('Non-repeatable read vs phantom read — the key difference?',
         'Non-repeatable read: the <strong>same row</strong> changes value (UPDATE). Phantom read: the <strong>set of rows</strong> changes (INSERT/DELETE) for the same condition.'),
        ('Which isolation level prevents dirty reads?',
         'READ COMMITTED and above. Only READ UNCOMMITTED allows them.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('Explain transaction Isolation Levels', 'Isolation Levels', minutes=8, cards=[
    definition(
        defbox('The SQL standard defines four <strong>isolation levels</strong>. Each one decides which read phenomena are '
               'allowed. Higher isolation = more correctness but less concurrency (more locking/waiting).'),
        table(['Isolation level', 'Dirty read', 'Non-repeatable read', 'Phantom read'], [
            ['READ UNCOMMITTED', '❌ Possible', '❌ Possible', '❌ Possible'],
            ['READ COMMITTED', '✅ Prevented', '❌ Possible', '❌ Possible'],
            ['REPEATABLE READ', '✅ Prevented', '✅ Prevented', '❌ Possible (standard) / mostly prevented in InnoDB'],
            ['SERIALIZABLE', '✅ Prevented', '✅ Prevented', '✅ Prevented'],
        ], 'Isolation levels vs read phenomena (SQL-92 standard)'),
        tags('Isolation Levels', 'READ COMMITTED', 'REPEATABLE READ', 'SERIALIZABLE', 'Snapshot'),
    ),
    comparison(
        table(['Database', 'Default isolation level'], [
            ['MySQL (InnoDB)', 'REPEATABLE READ'],
            ['PostgreSQL', 'READ COMMITTED'],
            ['Oracle', 'READ COMMITTED'],
            ['SQL Server', 'READ COMMITTED'],
        ]),
        note('InnoDB\'s REPEATABLE READ uses a consistent snapshot for plain SELECTs and <strong>next-key (gap) locks</strong> '
             'for locking reads and updates, so most phantom cases are prevented — stronger than the SQL standard requires.'),
        title='Defaults Across Databases'),
    example(
        code("""
-- Check the current level
SELECT @@transaction_isolation;

-- Change for the current session
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- Change only for the next transaction
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
SELECT SUM(balance) FROM accounts;
COMMIT;
"""),
        title='Example: Setting Isolation in MySQL'),
    crossq(
        ('Which isolation level would you choose for a banking system?',
         'For balance transfers, at least REPEATABLE READ with explicit row locks (<code>SELECT … FOR UPDATE</code>), '
         'or SERIALIZABLE for the critical section. Reporting queries on the same DB can use READ COMMITTED.'),
        ('Why not always use SERIALIZABLE?',
         'It drastically reduces concurrency: more locking, more waiting, more deadlocks and transaction retries. Most applications are correct and much faster at READ COMMITTED or REPEATABLE READ.'),
        ('What is snapshot isolation?',
         'Each transaction reads from a snapshot taken at its start (via MVCC). It prevents dirty, non-repeatable and '
         'phantom reads but allows a subtle anomaly called <strong>write skew</strong>.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('What are Locks? Explain shared vs exclusive and row vs table locks', 'Locks', minutes=7, cards=[
    definition(
        defbox('A <strong>lock</strong> is a mechanism that controls concurrent access to data. A transaction acquires a '
               'lock before reading or writing, and other transactions must wait if they need an incompatible lock.'),
        table(['Lock', 'Also called', 'Allows others to', 'Acquired by'], [
            ['Shared (S)', 'Read lock', 'Read, but not write', '<code>SELECT … FOR SHARE</code> (LOCK IN SHARE MODE)'],
            ['Exclusive (X)', 'Write lock', 'Neither read-with-lock nor write', 'UPDATE, DELETE, INSERT, <code>SELECT … FOR UPDATE</code>'],
        ]),
        table(['Requested →<br>Held ↓', 'Shared (S)', 'Exclusive (X)'], [
            ['Shared (S)', '✅ Compatible', '❌ Wait'],
            ['Exclusive (X)', '❌ Wait', '❌ Wait'],
        ], 'Lock compatibility matrix'),
        tags('Shared Lock', 'Exclusive Lock', 'Row Lock', 'Table Lock', 'Gap Lock', 'Two-Phase Locking'),
    ),
    explanation(
        table(['Granularity', 'Locks', 'Concurrency', 'Overhead', 'Example'], [
            ['Row-level', 'Individual rows', 'High', 'Higher (many locks)', 'InnoDB'],
            ['Page-level', 'A data page', 'Medium', 'Medium', 'SQL Server (escalation)'],
            ['Table-level', 'The whole table', 'Low', 'Low', 'MyISAM, <code>LOCK TABLES</code>, DDL'],
        ]),
        p('<strong>Two-Phase Locking (2PL)</strong>: a transaction has a <em>growing</em> phase (acquires locks, releases '
          'none) and a <em>shrinking</em> phase (releases locks, acquires none). This guarantees serializable schedules. '
          '<strong>Strict 2PL</strong> holds all exclusive locks until commit — used by most DBMSs.', True),
        p('<strong>InnoDB extras</strong>: <em>record locks</em> (one index record), <em>gap locks</em> (the gap between '
          'records — blocks inserts), <em>next-key locks</em> (record + gap), and <em>intention locks</em> (IS/IX at table '
          'level, signalling row locks below).'),
    ),
    example(
        code("""
-- Session 1
START TRANSACTION;
SELECT * FROM seats WHERE seat_no = 'A1' FOR UPDATE;   -- X lock on the row

-- Session 2 (waits until session 1 commits)
UPDATE seats SET booked_by = 'Rohit' WHERE seat_no = 'A1';

-- Session 1
UPDATE seats SET booked_by = 'Asha' WHERE seat_no = 'A1';
COMMIT;                                                 -- lock released, session 2 proceeds
"""),
        warn('InnoDB locks <strong>index records</strong>. If the WHERE column has no index, InnoDB scans and locks every '
             'row it examines — effectively locking the whole table.', 'Important'),
        title='Example: Booking a Seat'),
    crossq(
        ('What is lock escalation?',
         'Converting many fine-grained locks (rows) into one coarse lock (table) to save memory. SQL Server does this; InnoDB does not escalate.'),
        ('Does a plain SELECT take locks in InnoDB?',
         'No. A normal SELECT is a non-locking consistent read from an MVCC snapshot. Only <code>FOR SHARE</code> / <code>FOR UPDATE</code> take locks (except under SERIALIZABLE).'),
    ),
]),

# ------------------------------------------------------------------ 36
Q('What is a Deadlock? How can it be prevented?', 'Deadlock', minutes=7, cards=[
    definition(
        defbox('A <strong>deadlock</strong> occurs when two or more transactions each hold a lock the other needs, so '
               'all of them wait forever. Neither can proceed without the other releasing its lock first.'),
        hl('T1 locks row A and waits for row B. T2 locks row B and waits for row A. Circular wait → deadlock.', 'Simplest case'),
        tags('Deadlock', 'Circular Wait', 'Wait-for Graph', 'Deadlock Victim', 'Lock Ordering'),
    ),
    deadlock_anim(),
    example(
        code("""
-- Session 1                                  -- Session 2
START TRANSACTION;                            START TRANSACTION;
UPDATE accounts SET balance = balance - 100
  WHERE id = 1;          -- locks row 1
                                              UPDATE accounts SET balance = balance - 50
                                                WHERE id = 2;        -- locks row 2
UPDATE accounts SET balance = balance + 100
  WHERE id = 2;          -- waits for row 2
                                              UPDATE accounts SET balance = balance + 50
                                                WHERE id = 1;        -- waits for row 1 → DEADLOCK
"""),
        output("""
ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction
"""),
        note('InnoDB detects the cycle immediately, rolls back the transaction that is cheapest to undo (the '
             '<strong>victim</strong>) and lets the other continue. <code>SHOW ENGINE INNODB STATUS</code> shows the latest deadlock.'),
        title='Example: Transfer in Opposite Directions'),
    explanation(
        p('<strong>Four necessary conditions (Coffman)</strong> — all must hold for a deadlock: mutual exclusion, '
          'hold and wait, no preemption, circular wait. Breaking any one prevents deadlock.'),
        table(['Strategy', 'How'], [
            ['Prevention', 'Always lock resources in the same order (e.g. lower account id first); lock everything needed at once'],
            ['Avoidance', 'Wait-die / wound-wait schemes using transaction timestamps'],
            ['Detection & recovery', 'Build a wait-for graph, find cycles, roll back a victim (what InnoDB does)'],
            ['Timeout', '<code>innodb_lock_wait_timeout</code> — give up after N seconds'],
        ]),
        p('<strong>Practical tips:</strong> keep transactions short, access tables/rows in a consistent order, index the '
          'columns in WHERE clauses (fewer rows locked), and make the application <strong>retry</strong> on error 1213.', True),
        title='Prevention & Handling'),
    crossq(
        ('Deadlock vs lock wait — what is the difference?',
         'A lock wait is temporary: T2 waits until T1 commits. A deadlock is a cycle that can never resolve on its own — the DBMS must break it.'),
        ('What is starvation?',
         'A transaction waits indefinitely because others keep getting the resource first (e.g. always chosen as deadlock victim). Fixed by aging / priorities.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('What is the difference between Optimistic and Pessimistic concurrency control?', 'Optimistic vs Pessimistic', minutes=6, cards=[
    definition(
        defbox('<strong>Pessimistic concurrency control</strong> assumes conflicts are likely, so it <strong>locks data '
               'before using it</strong> and others wait.',
               '<strong>Optimistic concurrency control</strong> assumes conflicts are rare, so it <strong>does not lock</strong> '
               'while working. At write time it checks whether someone else changed the data; if so, the update is rejected and retried.'),
        tags('Optimistic Locking', 'Pessimistic Locking', 'Version Column', 'SELECT FOR UPDATE', 'Retry'),
    ),
    comparison(
        table(['Aspect', 'Pessimistic', 'Optimistic'], [
            ['Assumption', 'Conflicts are frequent', 'Conflicts are rare'],
            ['Mechanism', 'Locks (<code>SELECT … FOR UPDATE</code>)', 'Version number / timestamp check on update'],
            ['Waiting', 'Others block', 'No blocking'],
            ['On conflict', 'Prevented up front', 'Detected at commit → retry'],
            ['Deadlocks', 'Possible', 'Not from this mechanism'],
            ['Best for', 'High contention: seat booking, inventory, balances', 'Low contention, web apps, long user "think time"'],
        ]),
    ),
    example(
        code("""
-- PESSIMISTIC
START TRANSACTION;
SELECT qty FROM inventory WHERE item_id = 7 FOR UPDATE;   -- others wait
UPDATE inventory SET qty = qty - 1 WHERE item_id = 7;
COMMIT;

-- OPTIMISTIC  (table has a 'version' column)
SELECT qty, version FROM inventory WHERE item_id = 7;     -- qty=10, version=4
-- ... user edits for a while, no locks held ...
UPDATE inventory
SET qty = 9, version = version + 1
WHERE item_id = 7 AND version = 4;
-- 1 row affected  → success
-- 0 rows affected → someone else updated it first → reload and retry
"""),
        title='Example'),
    crossq(
        ('Which approach do ORMs like Hibernate/JPA use for @Version?',
         'Optimistic locking. The ORM adds <code>AND version = ?</code> to the UPDATE and throws an OptimisticLockException if no row is updated.'),
        ('Why is pessimistic locking bad for web forms?',
         'A user may open an edit page and leave for lunch — holding a database lock that long would block everyone else. Optimistic locking holds nothing while the user thinks.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('What is MVCC (Multi-Version Concurrency Control)?', 'MVCC', minutes=7, cards=[
    definition(
        defbox('<strong>MVCC</strong> lets readers and writers work at the same time without blocking each other by '
               'keeping <strong>multiple versions</strong> of a row. A writer creates a new version; readers continue to '
               'see the version that was committed when their snapshot was taken.'),
        hl('Readers don\'t block writers, and writers don\'t block readers.', 'Key benefit'),
        tags('MVCC', 'Snapshot', 'Undo Log', 'Read View', 'Consistent Read', 'Vacuum'),
    ),
    mvcc_anim(),
    explanation(
        table(['Database', 'How old versions are kept'], [
            ['MySQL InnoDB', 'Row stores the latest version + a pointer into the <strong>undo log</strong>; older versions are rebuilt from undo records. A purge thread cleans them.'],
            ['PostgreSQL', 'Old and new versions (tuples) stay in the table itself with xmin/xmax transaction ids; <strong>VACUUM</strong> removes dead tuples.'],
            ['Oracle', 'Undo tablespace with rollback segments.'],
        ]),
        p('Each InnoDB row has hidden columns: <code>DB_TRX_ID</code> (the transaction that last changed it) and '
          '<code>DB_ROLL_PTR</code> (pointer to the previous version in the undo log). When a transaction reads, it uses '
          'a <strong>read view</strong> — the list of transactions active at snapshot time — to decide which version is visible.', True),
        p('<strong>READ COMMITTED</strong> creates a new read view for every statement; <strong>REPEATABLE READ</strong> '
          'creates one at the first read and reuses it for the whole transaction. That is exactly why one sees changes committed by others and the other does not.'),
    ),
    example(
        code("""
-- REPEATABLE READ (MySQL default)
-- Session 1                                   -- Session 2
START TRANSACTION;
SELECT fee FROM courses WHERE id = 1;  -- 95000
                                               UPDATE courses SET fee = 98000 WHERE id = 1;
                                               COMMIT;
SELECT fee FROM courses WHERE id = 1;  -- still 95000 (same snapshot, read from undo)
COMMIT;
SELECT fee FROM courses WHERE id = 1;  -- 98000 (new snapshot)
"""),
        title='Example: Snapshot in Action'),
    crossq(
        ('What is the cost of MVCC?',
         'Extra storage for old versions, and background cleanup (InnoDB purge, PostgreSQL VACUUM). A very long-running '
         'transaction prevents cleanup, so undo logs / table bloat grow.'),
        ('Does MVCC eliminate the need for locks?',
         'No. Two writers updating the same row still need a lock — MVCC removes reader/writer blocking, not writer/writer conflicts.'),
    ),
]),

])
