from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

SECTION = dict(level='intermediate', title='Joins', questions=[

# ------------------------------------------------------------------ 16
Q('What are the different types of joins in MySQL?', 'Types of Joins', minutes=8, cards=[
    definition(
        defbox('A <strong>join</strong> combines rows from two tables based on a related column. MySQL supports '
               '<strong>INNER JOIN</strong>, <strong>LEFT [OUTER] JOIN</strong>, <strong>RIGHT [OUTER] JOIN</strong>, '
               '<strong>CROSS JOIN</strong> and self joins. <strong>FULL OUTER JOIN</strong> is not supported directly and is emulated with UNION.'),
        tags('INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL OUTER JOIN', 'CROSS JOIN', 'Self Join'),
    ),
    join_types(),
    comparison(
        table(['Join', 'Returns', 'Typical use'], [
            ['INNER JOIN', 'Only matching rows from both tables', 'Orders with their customer details'],
            ['LEFT JOIN', 'All left rows + matches (NULL if none)', 'All customers, with orders if any'],
            ['RIGHT JOIN', 'All right rows + matches', 'Rarely used; rewrite as LEFT JOIN'],
            ['FULL OUTER JOIN', 'All rows from both sides', 'Reconciling two systems'],
            ['CROSS JOIN', 'Every combination (m × n rows)', 'Generating calendars, size × colour variants'],
            ['SELF JOIN', 'A table joined to itself', 'Employee → manager hierarchy'],
        ]),
    ),
    sample('departments', 'employees'),
    example(
        sqlrun("""
-- INNER: employees that have a department
SELECT e.name, d.dept_name
FROM employees e
INNER JOIN departments d ON e.dept_id = d.dept_id
ORDER BY e.emp_id;

-- LEFT: every department with its head count, including empty ones
SELECT d.dept_name, COUNT(e.emp_id) AS head_count
FROM departments d
LEFT JOIN employees e ON e.dept_id = d.dept_id
GROUP BY d.dept_id, d.dept_name
ORDER BY d.dept_id;

-- CROSS: all department x city combinations
SELECT COUNT(*) AS combinations
FROM departments CROSS JOIN (SELECT DISTINCT city FROM employees) c;
""", setup=EMP),
        title='Example'),
    warn('In the LEFT JOIN head count, use <code>COUNT(e.emp_id)</code>, not <code>COUNT(*)</code>. Marketing has one row with NULLs, so COUNT(*) would wrongly report 1 employee.'),
    crossq(
        ('What is the difference between JOIN and INNER JOIN?', 'None. <code>JOIN</code> on its own means INNER JOIN. Likewise LEFT JOIN = LEFT OUTER JOIN.'),
        ('What is a NATURAL JOIN?', 'A join on all columns with the same name in both tables. Avoid it: adding an unrelated column with a matching name (e.g. <code>updated_at</code>) silently changes the join.'),
        ('What does USING do?', '<code>JOIN departments USING (dept_id)</code> is shorthand for <code>ON e.dept_id = d.dept_id</code> when the column names are the same, and returns that column once.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What is a Self Join? Give examples', 'Self Join', minutes=6, cards=[
    definition(
        defbox('A <strong>self join</strong> joins a table to itself, using two different aliases so each copy can play a '
               'different role. It is used for hierarchical data (employee → manager) and for comparing rows within the same table.'),
        tags('Self Join', 'Alias', 'Hierarchy', 'manager_id'),
    ),
    example(
        sqlrun("""
-- Each employee with the manager's name (LEFT JOIN keeps the top boss)
SELECT e.name AS employee, COALESCE(m.name, '— top —') AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.emp_id
ORDER BY e.emp_id;

-- Managers and how many direct reports they have
SELECT m.name AS manager, COUNT(*) AS direct_reports
FROM employees e
JOIN employees m ON e.manager_id = m.emp_id
GROUP BY m.emp_id, m.name
ORDER BY direct_reports DESC, manager;

-- Pairs of colleagues in the same city (each pair once)
SELECT a.name AS emp1, b.name AS emp2, a.city
FROM employees a
JOIN employees b ON a.city = b.city AND a.emp_id < b.emp_id
WHERE a.city = 'Pune';
""", setup=EMP),
        title='Example'),
    interview(p('In the pairs query, <code>a.emp_id &lt; b.emp_id</code> avoids pairing a row with itself and avoids listing '
                'both (A, B) and (B, A). Interviewers often check that you remember this.')),
    crossq(
        ('How do you get the full chain of managers (all levels), not just the direct one?', 'A self join only goes one level per join. For any depth use a <strong>recursive CTE</strong> (see the CTE section).'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('MySQL has no FULL OUTER JOIN. How do you emulate it?', 'FULL OUTER JOIN Emulation', minutes=5, cards=[
    definition(
        defbox('Combine a <strong>LEFT JOIN</strong> (all left rows plus matches) with the rows that exist <strong>only on the '
               'right</strong>. The safe way is <code>LEFT JOIN … UNION ALL … RIGHT JOIN … WHERE left.key IS NULL</code>.'),
        tags('FULL OUTER JOIN', 'UNION', 'UNION ALL', 'Reconciliation'),
    ),
    example(
        sqlrun("""
SELECT e.name, d.dept_name
FROM employees e LEFT JOIN departments d ON e.dept_id = d.dept_id
UNION ALL
SELECT e.name, d.dept_name
FROM employees e RIGHT JOIN departments d ON e.dept_id = d.dept_id
WHERE e.emp_id IS NULL;        -- only the right-side rows with no match
""", setup=EMP),
        title='Example'),
    explanation(
        p('A shorter version uses plain <code>UNION</code> of the LEFT and RIGHT joins, which removes duplicates. It works '
          'here, but it also removes <em>genuine</em> duplicate rows (two employees with the same name in the same department), '
          'and the DISTINCT step costs a sort. The UNION ALL + IS NULL version is exact and faster.'),
        title='Why UNION ALL and IS NULL?'),
    real_world(p('Reconciliation between a source system and the warehouse: full outer join on the business key and flag rows '
                 'as <em>missing in target</em> (right side NULL), <em>missing in source</em> (left side NULL) or <em>mismatch</em> (both present, values differ).')),
    crossq(
        ('Which databases support FULL OUTER JOIN natively?', 'PostgreSQL, SQL Server, Oracle, Spark SQL and Hive all do. MySQL (all versions) does not.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What is the difference between putting a condition in ON vs WHERE in a LEFT JOIN?', 'ON vs WHERE in LEFT JOIN', minutes=6, cards=[
    definition(
        defbox('For an INNER JOIN, a filter in ON or WHERE gives the same result. For a <strong>LEFT JOIN</strong> it does not:',
               'A condition in <strong>ON</strong> only controls which right-side rows <em>match</em>; every left row is still kept. '
               'A condition on the right table in <strong>WHERE</strong> runs after the join and removes the NULL-extended rows, '
               'turning the LEFT JOIN into an INNER JOIN.'),
        tags('LEFT JOIN', 'ON Clause', 'WHERE Clause', 'Outer Join Filter'),
    ),
    on_vs_where(),
    example(
        sqlrun("""
-- Condition in ON: all 4 departments kept
SELECT d.dept_name, e.name, e.salary
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id AND e.salary > 100000
ORDER BY d.dept_id, e.salary DESC;

-- Condition in WHERE: HR and Marketing disappear
SELECT d.dept_name, e.name, e.salary
FROM departments d
LEFT JOIN employees e ON d.dept_id = e.dept_id
WHERE e.salary > 100000
ORDER BY d.dept_id, e.salary DESC;
""", setup=EMP),
        title='Example'),
    hl('Filter on the <strong>left</strong> (preserved) table → WHERE. Filter on the <strong>right</strong> (optional) table → ON. '
       'The only right-table condition that belongs in WHERE is <code>IS NULL</code> for anti-joins.', 'Rule of thumb'),
    crossq(
        ('What happens with a left-table condition in ON, e.g. ON … AND d.dept_name = \'HR\'?', 'It does <em>not</em> filter departments. All 4 departments are still returned; only HR gets matched employees, the others get NULLs. That surprises many people.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('How do you find rows in one table that have no match in another? (Anti-join and the NOT IN NULL trap)', 'Anti-joins & NOT IN Trap', minutes=8, cards=[
    definition(
        defbox('An <strong>anti-join</strong> returns rows of table A with <strong>no matching row</strong> in table B, e.g. '
               'customers who never ordered. Three common ways: <code>LEFT JOIN … WHERE b.key IS NULL</code>, '
               '<code>NOT EXISTS</code> and <code>NOT IN</code>.'),
        tags('Anti-join', 'NOT EXISTS', 'NOT IN', 'LEFT JOIN IS NULL', 'Three-valued Logic'),
    ),
    example(
        sqlrun("""
-- Customers who never placed an order: three equivalent ways
SELECT c.name FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL;

SELECT c.name FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);

SELECT name FROM customers
WHERE customer_id NOT IN (SELECT customer_id FROM orders);
""", setup=SALES),
        title='Example: Customers Without Orders'),
    not_in_null(),
    example(
        sqlrun("""
-- Employees who are not anyone's manager
SELECT COUNT(*) AS not_in_result
FROM employees WHERE emp_id NOT IN (SELECT manager_id FROM employees);

SELECT name AS not_exists_result
FROM employees e
WHERE NOT EXISTS (SELECT 1 FROM employees x WHERE x.manager_id = e.emp_id)
ORDER BY emp_id;
""", setup=EMP),
        title='Example: The Trap with Real Data'),
    comparison(
        table(['Method', 'NULL-safe', 'Notes'], [
            ['NOT EXISTS', 'Yes', 'Clearest intent; MySQL 8 runs it as an anti-join'],
            ['LEFT JOIN … IS NULL', 'Yes', 'Test a NOT NULL column of B (e.g. its primary key)'],
            ['NOT IN (subquery)', '<strong>No</strong>', 'Returns nothing if the subquery yields any NULL'],
        ]),
        title='Which to Use'),
    crossq(
        ('Does IN have the same problem?', 'No. <code>x IN (1, NULL)</code> is TRUE when x = 1 and UNKNOWN otherwise, so matching rows are still found. Only the negation is broken.'),
        ('Why test o.order_id IS NULL rather than o.status IS NULL?', 'Because a real order can have a NULL status. The primary key of the right table is NULL only when there was no match.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('Why does a join return more rows than expected? (Row multiplication / fan-out)', 'Join Row Multiplication', minutes=7, cards=[
    definition(
        defbox('A join returns one row for <strong>every matching pair</strong>. If the join key is not unique on one side, '
               'rows from the other side are <strong>repeated</strong>. Aggregating a column after such a join inflates the totals.'),
        hl('Before writing any join, ask: "What is the grain (one row per what) of each table, and of the result?"', 'Habit'),
        tags('Fan-out', 'Grain', 'Duplicates', 'Many-to-Many', 'Pre-aggregation'),
    ),
    row_multiplication(),
    example(
        sqlrun("""
-- Wrong: order amount repeated once per item
SELECT SUM(o.amount) AS wrong_revenue
FROM orders o JOIN order_items i ON i.order_id = o.order_id
WHERE o.status <> 'CANCELLED';

-- Right: revenue from orders alone
SELECT SUM(amount) AS revenue FROM orders WHERE status <> 'CANCELLED';

-- Right, when item data is also needed: aggregate items first
SELECT o.order_id, o.amount, i.items
FROM orders o
JOIN (SELECT order_id, COUNT(*) AS items FROM order_items GROUP BY order_id) i
  ON i.order_id = o.order_id
WHERE o.order_id IN (101, 102, 105);
""", setup=SALES),
        title='Example'),
    crossq(
        ('Table A has 5 rows and B has 4 rows. What are the min and max rows of A INNER JOIN B?', 'Min 0 (no matches). Max 20, if every row matches every row (e.g. all join keys are the same value). LEFT JOIN: min 5, max 20.'),
        ('A has keys (1,1,2) and B has keys (1,1,1,3). How many rows does the inner join return?', 'Key 1: 2 × 3 = 6 rows. Key 2 and 3 have no partner. Total <strong>6</strong>. LEFT JOIN: 7 (the 2 is kept with NULLs).'),
        ('How do you detect fan-out in a pipeline?', 'Compare <code>COUNT(*)</code> before and after the join, or check the key is unique: <code>SELECT key, COUNT(*) FROM b GROUP BY key HAVING COUNT(*) &gt; 1</code>.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('How does MySQL execute joins internally? (Nested Loop, Block Nested Loop, Hash Join)', 'Join Algorithms', minutes=6, cards=[
    definition(
        defbox('MySQL has traditionally executed joins as <strong>nested loops</strong>: for each row of the outer (driving) '
               'table, look up matching rows in the inner table. Since <strong>MySQL 8.0.18</strong> it also uses '
               '<strong>hash joins</strong> for equi-joins where the inner table has no usable index.'),
        tags('Nested Loop Join', 'Index Nested Loop', 'Block Nested Loop', 'Hash Join', 'Driving Table'),
    ),
    comparison(
        table(['Algorithm', 'How it works', 'When MySQL uses it'], [
            ['Index nested loop', 'For each outer row, an index lookup on the inner table', 'Join column of inner table is indexed (the best case)'],
            ['Block nested loop (old)', 'Buffer many outer rows, then scan the inner table once per buffer', 'No index; replaced by hash join in 8.0.20+'],
            ['Hash join', 'Build a hash table on the smaller input, then probe it with the other', 'Equi-join without a usable index (8.0.18+)'],
        ]),
        p('MySQL has no sort-merge join. The optimizer also picks the <strong>join order</strong>: usually the table that '
          'produces fewer rows after filtering drives the loop.', True),
    ),
    example(
        sqlrun(r"""
CREATE TABLE a (id INT, val INT);
CREATE TABLE b (id INT, val INT);
INSERT INTO a VALUES (1, 10), (2, 20), (3, 30);
-- 1000 rows in b (generated with a recursive CTE)
INSERT INTO b
WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 1000)
SELECT n, n * 10 FROM s;

-- No index on b.id: hash join
EXPLAIN FORMAT=TREE SELECT * FROM a JOIN b ON a.id = b.id\G

-- With an index on b.id: index nested loop
CREATE INDEX idx_b_id ON b(id);
ANALYZE TABLE a, b;            -- refresh optimizer statistics
EXPLAIN FORMAT=TREE SELECT * FROM a JOIN b ON a.id = b.id\G
"""),
        title='Example: Seeing the Algorithm in EXPLAIN'),
    interview(p('The practical takeaway: <strong>index the join columns</strong>, especially foreign keys on the child table. '
                'That lets MySQL do index nested loop joins, which touch only the matching rows.')),
    crossq(
        ('Which join algorithms does Spark use, for comparison?', 'Broadcast hash join (small table copied to every executor), shuffle hash join and sort-merge join (the default for two large tables).'),
    ),
]),

])
