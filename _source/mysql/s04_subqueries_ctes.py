from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

SECTION = dict(level='intermediate', title='Subqueries, CTEs & Set Operations', questions=[

# ------------------------------------------------------------------ 23
Q('What are the types of subqueries? What is a correlated subquery?', 'Subqueries & Correlated Subqueries', minutes=8, cards=[
    definition(
        defbox('A <strong>subquery</strong> is a SELECT nested inside another statement. By what it returns it can be '
               '<strong>scalar</strong> (one value), <strong>row</strong> (one row), <strong>column</strong> (one column, used with IN/ANY/ALL) '
               'or <strong>table</strong> (a derived table in FROM).',
               'A <strong>correlated subquery</strong> refers to a column of the outer query, so logically it is evaluated '
               '<strong>once per outer row</strong>. A non-correlated subquery runs once on its own.'),
        tags('Scalar Subquery', 'Derived Table', 'Correlated Subquery', 'IN', 'ANY', 'ALL'),
    ),
    table(['Type', 'Example'], [
        ['Scalar (in SELECT or WHERE)', '<code>WHERE salary &gt; (SELECT AVG(salary) FROM employees)</code>'],
        ['Column / list', '<code>WHERE dept_id IN (SELECT dept_id FROM departments WHERE dept_name LIKE \'D%\')</code>'],
        ['Row', '<code>WHERE (dept_id, salary) = (SELECT dept_id, MAX(salary) FROM … )</code>'],
        ['Derived table (in FROM)', '<code>FROM (SELECT dept_id, AVG(salary) a FROM employees GROUP BY dept_id) t</code>'],
        ['Correlated', '<code>WHERE salary &gt; (SELECT AVG(salary) FROM employees x WHERE x.dept_id = e.dept_id)</code>'],
    ]),
    correlated_anim(),
    example(
        sqlrun("""
-- Scalar, non-correlated: above the company average (runs once)
SELECT name, salary FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees)
ORDER BY salary DESC;

-- Correlated: above their own department's average
SELECT e.name, e.dept_id, e.salary
FROM employees e
WHERE e.salary > (SELECT AVG(x.salary) FROM employees x WHERE x.dept_id = e.dept_id)
ORDER BY e.dept_id;

-- Same result with a derived table: each average computed once
SELECT e.name, e.dept_id, e.salary
FROM employees e
JOIN (SELECT dept_id, AVG(salary) AS avg_sal FROM employees GROUP BY dept_id) d
  ON d.dept_id = e.dept_id
WHERE e.salary > d.avg_sal
ORDER BY e.dept_id;

-- Scalar subquery in SELECT
SELECT name, salary,
       salary - (SELECT AVG(salary) FROM employees) AS diff_from_avg
FROM employees WHERE emp_id <= 3;
""", setup=EMP),
        title='Example'),
    crossq(
        ('What happens if a scalar subquery returns more than one row?', 'An error: <code>ERROR 1242: Subquery returns more than 1 row</code>. Use IN, add LIMIT 1, or aggregate.'),
        ('What do ANY and ALL mean?', '<code>salary &gt; ALL (subquery)</code>: greater than every value (i.e. the max). <code>salary &gt; ANY (…)</code>: greater than at least one (i.e. the min). <code>= ANY</code> is the same as IN.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('What is the difference between EXISTS and IN?', 'EXISTS vs IN', minutes=6, cards=[
    definition(
        defbox('<strong>IN</strong> checks whether a value is in the list a subquery returns. <strong>EXISTS</strong> checks '
               'whether a (usually correlated) subquery returns <strong>at least one row</strong>; it stops at the first match '
               'and does not care what the row contains.'),
        tags('EXISTS', 'IN', 'Semi-join', 'NOT EXISTS', 'Short-circuit'),
    ),
    comparison(
        table(['Aspect', 'IN', 'EXISTS'], [
            ['Tests', 'Value membership', 'Existence of any row'],
            ['Subquery type', 'Usually non-correlated', 'Usually correlated'],
            ['SELECT list in subquery', 'Must return the compared column', 'Irrelevant (SELECT 1 by convention)'],
            ['NULL in subquery (negated form)', 'NOT IN breaks: returns nothing', 'NOT EXISTS is safe'],
            ['Performance in MySQL 8', 'Both are converted to semi-joins; usually the same plan', 'Same'],
            ['Readability', 'Natural for small fixed lists', 'Natural for "has related rows"'],
        ]),
    ),
    example(
        sqlrun("""
-- Customers who have at least one delivered order
SELECT name FROM customers
WHERE customer_id IN (SELECT customer_id FROM orders WHERE status = 'DELIVERED')
ORDER BY name;

SELECT c.name FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o
              WHERE o.customer_id = c.customer_id AND o.status = 'DELIVERED')
ORDER BY c.name;

-- A JOIN would repeat customers with many orders; EXISTS/IN do not
SELECT c.name FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.status = 'DELIVERED' ORDER BY c.name;
""", setup=SALES),
        title='Example'),
    interview(p('The old rule "EXISTS is faster for big subqueries, IN for small" came from older MySQL versions. In MySQL 8 '
                'the optimizer turns both into <strong>semi-joins</strong>, so pick the one that reads better and prefer '
                '<strong>NOT EXISTS over NOT IN</strong> for the NULL reason. Then check with EXPLAIN.')),
    crossq(
        ('Why use EXISTS or IN instead of a JOIN here?', 'A JOIN returns one row per matching order, so Asha (two delivered orders) appears twice. A semi-join returns each customer once, without needing DISTINCT.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What is the difference between UNION and UNION ALL? Does MySQL support INTERSECT and EXCEPT?', 'UNION, INTERSECT, EXCEPT', minutes=6, cards=[
    definition(
        defbox('Set operators combine the results of two SELECTs vertically. <strong>UNION</strong> removes duplicate rows, '
               '<strong>UNION ALL</strong> keeps them. <strong>INTERSECT</strong> returns rows present in both and '
               '<strong>EXCEPT</strong> rows in the first but not the second; MySQL supports these from <strong>8.0.31</strong>.'),
        tags('UNION', 'UNION ALL', 'INTERSECT', 'EXCEPT', 'Set Operations'),
    ),
    comparison(
        table(['Operator', 'Result', 'Duplicates'], [
            ['UNION ALL', 'All rows from both', 'Kept (fastest: no dedup)'],
            ['UNION', 'All rows from both', 'Removed (needs a sort/hash)'],
            ['INTERSECT', 'Rows in both', 'Removed'],
            ['EXCEPT', 'Rows in first, not in second', 'Removed'],
        ]),
        p('Rules: same number of columns, compatible types, column names come from the <strong>first</strong> SELECT, and '
          'ORDER BY / LIMIT at the end apply to the combined result.', True),
    ),
    example(
        sqlrun("""
CREATE TABLE crm_emails   (email VARCHAR(40));
CREATE TABLE store_emails (email VARCHAR(40));
INSERT INTO crm_emails   VALUES ('asha@x.com'), ('ravi@x.com'), ('neha@x.com');
INSERT INTO store_emails VALUES ('ravi@x.com'), ('neha@x.com'), ('imran@x.com');

SELECT COUNT(*) AS union_all FROM (SELECT email FROM crm_emails UNION ALL SELECT email FROM store_emails) t;
SELECT COUNT(*) AS union_    FROM (SELECT email FROM crm_emails UNION     SELECT email FROM store_emails) t;

SELECT email AS in_both     FROM crm_emails INTERSECT SELECT email FROM store_emails ORDER BY in_both;
SELECT email AS only_in_crm FROM crm_emails EXCEPT    SELECT email FROM store_emails;
"""),
        title='Example'),
    interview(p('Use <strong>UNION ALL by default</strong> when you know the inputs cannot overlap (for example, appending '
                'January and February partitions). UNION adds an expensive de-duplication step.')),
    crossq(
        ('How did people write INTERSECT and EXCEPT before 8.0.31?', 'INTERSECT as <code>WHERE EXISTS</code> / inner join, and EXCEPT as <code>WHERE NOT EXISTS</code> / LEFT JOIN … IS NULL. These still work on every version.'),
        ('UNION vs JOIN?', 'UNION stacks rows (more rows, same columns). JOIN combines columns side by side (wider rows) based on a matching condition.'),
    ),
]),

# ------------------------------------------------------------------ 26
Q('What is a CTE (Common Table Expression)? Why use it?', 'CTEs (WITH Clause)', minutes=6, cards=[
    definition(
        defbox('A <strong>CTE</strong> is a named, temporary result set defined with <code>WITH name AS (SELECT …)</code> '
               'at the start of a statement and usable like a table in the rest of that statement. MySQL supports CTEs from <strong>8.0</strong>.'),
        tags('WITH', 'CTE', 'Readability', 'Recursive', 'MySQL 8'),
    ),
    explanation(
        ul('<strong>Readability</strong>: a long query becomes named steps that read top to bottom, like a pipeline.',
           '<strong>Reuse</strong>: one CTE can be referenced several times in the same query (a derived table must be repeated).',
           '<strong>Chaining</strong>: a later CTE can use an earlier one.',
           '<strong>Recursion</strong>: <code>WITH RECURSIVE</code> handles hierarchies and series (next question).',
           'Scope: a CTE exists only for the single statement; it is not stored anywhere.'),
    ),
    example(
        sqlrun("""
-- Customers whose spend is above the average customer's spend
WITH customer_spend AS (
    SELECT customer_id, SUM(amount) AS spend, COUNT(*) AS orders
    FROM orders
    WHERE status <> 'CANCELLED'
    GROUP BY customer_id
),
avg_spend AS (
    SELECT AVG(spend) AS avg_val FROM customer_spend      -- uses the first CTE
)
SELECT c.name, s.orders, s.spend, ROUND(a.avg_val) AS avg_spend
FROM customer_spend s
JOIN customers c ON c.customer_id = s.customer_id
CROSS JOIN avg_spend a
WHERE s.spend > a.avg_val
ORDER BY s.spend DESC;
""", setup=SALES),
        title='Example: Chained CTEs'),
    crossq(
        ('Is a CTE faster than a subquery?', 'Not by itself. MySQL can merge a CTE into the outer query or materialise it once (useful when it is referenced several times). Its main benefit is readability.'),
        ('Can you use a CTE in UPDATE or DELETE?', 'Yes, MySQL allows <code>WITH … UPDATE</code> and <code>WITH … DELETE</code> statements, e.g. to delete duplicates found by a CTE.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What is a recursive CTE? Write one for an employee hierarchy and a date series', 'Recursive CTEs', minutes=8, cards=[
    definition(
        defbox('A <strong>recursive CTE</strong> refers to itself. It has an <strong>anchor member</strong> (the starting rows) '
               'and a <strong>recursive member</strong> joined to the previous iteration\'s rows, combined with UNION ALL. '
               'It repeats until an iteration returns no rows.'),
        tags('WITH RECURSIVE', 'Anchor Member', 'Recursive Member', 'Hierarchy', 'Date Series', 'cte_max_recursion_depth'),
    ),
    recursive_cte(),
    example(
        sqlrun("""
WITH RECURSIVE org AS (
    SELECT emp_id, name, manager_id, 1 AS level, CAST(name AS CHAR(200)) AS path
    FROM employees WHERE manager_id IS NULL                 -- anchor
    UNION ALL
    SELECT e.emp_id, e.name, e.manager_id, o.level + 1, CONCAT(o.path, ' > ', e.name)
    FROM employees e JOIN org o ON e.manager_id = o.emp_id  -- recursive member
)
SELECT level, name, path FROM org ORDER BY path;
""", setup=EMP),
        title='Example 1: Reporting Hierarchy'),
    example(
        sqlrun("""
-- Daily revenue for 1-10 Jan 2026, including days with no orders
WITH RECURSIVE days AS (
    SELECT DATE('2026-01-01') AS d
    UNION ALL
    SELECT d + INTERVAL 1 DAY FROM days WHERE d < '2026-01-10'
)
SELECT days.d, COALESCE(SUM(o.amount), 0) AS revenue
FROM days
LEFT JOIN orders o ON o.order_date = days.d
GROUP BY days.d
ORDER BY days.d;
""", setup=SALES),
        title='Example 2: Filling Missing Dates'),
    warn('Columns get their type and width from the <strong>anchor</strong> member. Without <code>CAST(name AS CHAR(200))</code> the path column '
         'would be only as wide as the first name, and longer paths would fail with "Data too long".', 'Gotcha'),
    crossq(
        ('How do you prevent infinite loops (e.g. a cycle in manager_id)?', 'Add a stop condition such as <code>WHERE o.level &lt; 20</code>, or track the path and skip ids already in it. MySQL also aborts after <code>cte_max_recursion_depth</code> (1000) iterations.'),
        ('Where else are recursive CTEs used?', 'Bill of materials (parts within parts), category trees, folder structures, graph traversal, and generating number or date series.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What is the difference between a derived table, a CTE, a temporary table and a view?', 'Derived Table vs CTE vs Temp Table vs View', minutes=6, cards=[
    definition(
        defbox('All four let you name an intermediate result, but they differ in <strong>how long they live</strong> and '
               '<strong>who can see them</strong>.'),
        tags('Derived Table', 'CTE', 'Temporary Table', 'View', 'Scope'),
    ),
    comparison(
        table(['Aspect', 'Derived table', 'CTE', 'Temporary table', 'View'], [
            ['Defined with', 'Subquery in FROM', 'WITH … AS', 'CREATE TEMPORARY TABLE', 'CREATE VIEW'],
            ['Lifetime', 'One statement', 'One statement', 'Until the session ends (or DROP)', 'Permanent (until DROP)'],
            ['Visible to', 'That statement', 'That statement', 'Only the creating session', 'All users with privileges'],
            ['Stores data', 'No (may be materialised internally)', 'No (may be materialised)', 'Yes, physically', 'No, only the query text'],
            ['Can be indexed', 'No', 'No', 'Yes', 'No (uses base table indexes)'],
            ['Reuse in same query', 'Must repeat', 'Yes, by name', 'Yes', 'Yes'],
            ['Recursive', 'No', 'Yes', 'No', 'No (but can wrap a recursive CTE)'],
        ]),
    ),
    example(
        sqlrun("""
-- Temporary table: compute once, index it, use in several later queries
CREATE TEMPORARY TABLE tmp_customer_spend AS
SELECT customer_id, SUM(amount) AS spend FROM orders
WHERE status <> 'CANCELLED' GROUP BY customer_id;
ALTER TABLE tmp_customer_spend ADD PRIMARY KEY (customer_id);

SELECT COUNT(*) AS big_spenders FROM tmp_customer_spend WHERE spend > 10000;

-- View: a saved query that always reflects current data
CREATE VIEW v_delivered AS
SELECT order_id, customer_id, amount FROM orders WHERE status = 'DELIVERED';

UPDATE orders SET status = 'DELIVERED' WHERE order_id = 110;
SELECT COUNT(*) AS delivered_now FROM v_delivered;
""", setup=SALES),
        title='Example'),
    interview(p('Choose by scope: <strong>CTE</strong> for readable steps inside one query, <strong>temporary table</strong> when '
                'a heavy intermediate result is reused across several statements in a session (e.g. a stored procedure or ETL step), '
                'and a <strong>view</strong> to give many users a stable, secure interface to the data.')),
    crossq(
        ('Are temporary tables visible to other connections?', 'No. Two sessions can each have a temporary table named <code>tmp_x</code> without conflict, and it is dropped automatically when the session closes.'),
    ),
]),

])
