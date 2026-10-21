from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

LOGINS = """
CREATE TABLE logins (user_id INT, login_date DATE, PRIMARY KEY (user_id, login_date));
INSERT INTO logins VALUES
(1, '2026-01-01'), (1, '2026-01-02'), (1, '2026-01-03'), (1, '2026-01-05'), (1, '2026-01-06'),
(1, '2026-01-09'), (1, '2026-01-10'), (1, '2026-01-11'), (1, '2026-01-12'),
(2, '2026-01-01'), (2, '2026-01-03'), (2, '2026-01-04'),
(3, '2026-01-07'), (3, '2026-01-08'), (3, '2026-01-09');
"""

SECTION = dict(level='advanced', title='SQL Coding Round', questions=[

# ------------------------------------------------------------------ 36
Q('How do you find and delete duplicate rows?', 'Find & Delete Duplicates', minutes=8, cards=[
    definition(
        defbox('Duplicates are rows that repeat the same <strong>business key</strong> (e.g. the same email) even though the '
               'surrogate id differs. Find them with <code>GROUP BY … HAVING COUNT(*) &gt; 1</code>, then delete all but one '
               'copy per key using <code>ROW_NUMBER()</code> or a self-join.'),
        tags('Duplicates', 'GROUP BY HAVING', 'ROW_NUMBER', 'DELETE JOIN', 'Deduplication'),
    ),
    example(
        sqlrun("""
CREATE TABLE subscribers (id INT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(40), city VARCHAR(20));
INSERT INTO subscribers (email, city) VALUES
 ('asha@x.com', 'Mumbai'), ('ravi@x.com', 'Pune'), ('asha@x.com', 'Mumbai'),
 ('neha@x.com', 'Delhi'),  ('ravi@x.com', 'Pune'), ('asha@x.com', 'Thane');

-- 1. Which keys are duplicated, and how often?
SELECT email, COUNT(*) AS copies
FROM subscribers GROUP BY email HAVING COUNT(*) > 1;

-- 2. Show every duplicate row except the first (lowest id) per email
WITH ranked AS (
    SELECT id, email, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
    FROM subscribers
)
SELECT id, email, rn FROM ranked WHERE rn > 1;

-- 3. Delete them (MySQL: DELETE with a JOIN to the ranked result)
DELETE s FROM subscribers s
JOIN (SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
      FROM subscribers) d ON d.id = s.id
WHERE d.rn > 1;

SELECT * FROM subscribers ORDER BY id;
"""),
        title='Example'),
    explanation(
        code("""
-- Before MySQL 8: self-join, keep the lowest id
DELETE s1 FROM subscribers s1
JOIN subscribers s2 ON s1.email = s2.email AND s1.id > s2.id;

-- Prevent new duplicates
ALTER TABLE subscribers ADD UNIQUE KEY uk_email (email);
""", 'Alternatives'),
        title='Other Ways'),
    warn('MySQL does not let you DELETE from a table and SELECT from the same table in a plain subquery '
         '(<code>DELETE FROM t WHERE id IN (SELECT … FROM t)</code> gives ERROR 1093). Use the JOIN form above, or wrap the '
         'subquery in another derived table.', 'ERROR 1093'),
    crossq(
        ('Which copy should you keep?', 'Decide by a rule: the first (lowest id), the latest (<code>ORDER BY updated_at DESC</code>) or the most complete. State the rule in the interview.'),
        ('How do you find rows that are duplicate across all columns?', '<code>GROUP BY email, city HAVING COUNT(*) &gt; 1</code> (list every column except the id).'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('Find employees who earn more than their manager', 'Earning More Than Manager', minutes=5, cards=[
    definition(
        defbox('A self-join problem: join <code>employees</code> to itself, matching each employee\'s <code>manager_id</code> to '
               'the manager\'s <code>emp_id</code>, then compare the two salaries.'),
        tags('Self Join', 'Hierarchy', 'Comparison'),
    ),
    sample('employees'),
    example(
        sqlrun("""
SELECT e.name AS employee, e.salary, m.name AS manager, m.salary AS manager_salary
FROM employees e
JOIN employees m ON e.manager_id = m.emp_id
WHERE e.salary > m.salary;

-- Variation: managers paid less than at least one of their reports, with the count
SELECT m.name AS manager, COUNT(*) AS reports_paid_more
FROM employees e
JOIN employees m ON e.manager_id = m.emp_id
WHERE e.salary > m.salary
GROUP BY m.emp_id, m.name;
""", setup=EMP),
        title='Example'),
    crossq(
        ('Why INNER JOIN rather than LEFT JOIN?', 'Employees without a manager (Arjun) have nothing to compare with. A LEFT JOIN would give NULL for the manager\'s salary, and the WHERE comparison would drop them anyway.'),
        ('Find employees who earn more than their department\'s average.', 'Correlated subquery, derived table or <code>AVG(salary) OVER (PARTITION BY dept_id)</code>. All three are shown in the Subqueries and Window Functions sections.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('Find users who logged in on 3 or more consecutive days (Gaps and Islands)', 'Consecutive Days (Gaps & Islands)', minutes=9, cards=[
    definition(
        defbox('<strong>Gaps and islands</strong> problems ask for runs of consecutive values (islands) separated by missing '
               'values (gaps). The standard trick: within an island, <code>value − ROW_NUMBER()</code> is constant, so it can be '
               'used as a group key.'),
        tags('Gaps and Islands', 'Consecutive', 'Streak', 'ROW_NUMBER', 'Date Arithmetic'),
    ),
    islands_anim(),
    example(
        sqlrun("""
WITH numbered AS (
    SELECT user_id, login_date,
           login_date - INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) DAY AS grp
    FROM logins
),
streaks AS (
    SELECT user_id, MIN(login_date) AS streak_start, MAX(login_date) AS streak_end, COUNT(*) AS days
    FROM numbered
    GROUP BY user_id, grp
)
SELECT * FROM streaks
WHERE days >= 3
ORDER BY user_id, streak_start;
""", setup=LOGINS),
        title='Example: All Streaks of 3+ Days'),
    example(
        sqlrun("""
-- Alternative with LAG / LEAD: users with a 3-day run (fine for a fixed small N)
SELECT DISTINCT user_id
FROM (SELECT user_id, login_date,
             LAG(login_date, 2) OVER (PARTITION BY user_id ORDER BY login_date) AS two_before
      FROM logins) t
WHERE DATEDIFF(login_date, two_before) = 2
ORDER BY user_id;
""", setup=LOGINS),
        title='Example: LAG Approach'),
    interview(p('If the same user can log in several times a day, first reduce to one row per user per day '
                '(<code>SELECT DISTINCT user_id, DATE(login_ts)</code>), otherwise duplicate dates break the row-number arithmetic.')),
    crossq(
        ('What is the longest streak per user?', 'Take the <code>streaks</code> CTE and <code>SELECT user_id, MAX(days) … GROUP BY user_id</code>.'),
        ('How do you find the gaps instead?', 'Use LEAD: rows where <code>DATEDIFF(LEAD(login_date) OVER (…), login_date) &gt; 1</code> mark the start of a gap.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Find customers who bought every product in a category (Relational Division)', 'Bought All Products', minutes=7, cards=[
    definition(
        defbox('"Customers who bought <strong>all</strong> X" is called <strong>relational division</strong>. The usual solution '
               'counts the distinct products each customer bought from the set and compares it with the size of the set.'),
        tags('Relational Division', 'COUNT DISTINCT', 'HAVING', 'NOT EXISTS'),
    ),
    sample('products', 'order_items', note='Plus <code>orders</code> (order_id → customer_id) from the earlier sample data.'),
    example(
        sqlrun("""
-- Customers who bought every Furniture product (Desk and Chair)
SELECT c.name
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items i  ON i.order_id = o.order_id
JOIN products p     ON p.product_id = i.product_id
WHERE p.category = 'Furniture'
GROUP BY c.customer_id, c.name
HAVING COUNT(DISTINCT p.product_id) = (SELECT COUNT(*) FROM products WHERE category = 'Furniture')
ORDER BY c.name;

-- Same with double NOT EXISTS: "no furniture product that the customer has not bought"
SELECT c.name FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM products p
    WHERE p.category = 'Furniture'
      AND NOT EXISTS (SELECT 1 FROM orders o JOIN order_items i ON i.order_id = o.order_id
                      WHERE o.customer_id = c.customer_id AND i.product_id = p.product_id))
ORDER BY c.name;
""", setup=SALES),
        title='Example'),
    warn('Use <code>COUNT(DISTINCT p.product_id)</code>. A customer who bought the Desk twice and never the Chair would '
         'otherwise count 2 and be reported wrongly.'),
    crossq(
        ('Customers who bought Laptop but never Headphones?', 'Semi-join plus anti-join: <code>WHERE EXISTS (… Laptop …) AND NOT EXISTS (… Headphones …)</code>.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('How do you pivot rows into columns and unpivot columns into rows in MySQL?', 'Pivot & Unpivot', minutes=7, cards=[
    definition(
        defbox('<strong>Pivot</strong> turns values of one column into separate columns (months across the top). MySQL has no '
               'PIVOT keyword, so it is done with <strong>conditional aggregation</strong>. <strong>Unpivot</strong> turns columns '
               'back into rows, done with <strong>UNION ALL</strong> (or a CROSS JOIN with a list of column names).'),
        tags('Pivot', 'Unpivot', 'Conditional Aggregation', 'UNION ALL', 'Dynamic SQL'),
    ),
    example(
        sqlrun("""
-- Pivot: revenue per category, one column per month
SELECT p.category,
       SUM(CASE WHEN MONTH(o.order_date) = 1 THEN p.price * i.qty ELSE 0 END) AS jan,
       SUM(CASE WHEN MONTH(o.order_date) = 2 THEN p.price * i.qty ELSE 0 END) AS feb,
       SUM(CASE WHEN MONTH(o.order_date) = 3 THEN p.price * i.qty ELSE 0 END) AS mar,
       SUM(p.price * i.qty)                                                   AS total
FROM orders o
JOIN order_items i ON i.order_id = o.order_id
JOIN products p    ON p.product_id = i.product_id
WHERE o.status <> 'CANCELLED'
GROUP BY p.category;
""", setup=SALES),
        title='Example: Pivot'),
    example(
        sqlrun("""
CREATE TABLE quarterly (region VARCHAR(10), q1 INT, q2 INT, q3 INT);
INSERT INTO quarterly VALUES ('West', 100, 120, 90), ('North', 80, 95, 110);

-- Unpivot: one row per region per quarter
SELECT region, 'Q1' AS quarter, q1 AS sales FROM quarterly
UNION ALL SELECT region, 'Q2', q2 FROM quarterly
UNION ALL SELECT region, 'Q3', q3 FROM quarterly
ORDER BY region, quarter;
"""),
        title='Example: Unpivot'),
    explanation(
        p('When the pivot columns are not known in advance (every month that exists), build the CASE list with '
          '<code>GROUP_CONCAT</code> from the data and run it as a prepared statement (<code>PREPARE stmt FROM @sql; EXECUTE stmt;</code>). '
          'In practice this is often left to the BI tool or to pandas/Spark (<code>pivot</code>).'),
        title='Dynamic Pivot'),
    crossq(
        ('Why is unpivoted (long) data usually preferred for storage?', 'Adding a new quarter or month needs no schema change, and filters and aggregates work on one column. Wide (pivoted) layouts are for presentation.'),
    ),
]),

# ------------------------------------------------------------------ 41
Q('How do you calculate the median in MySQL?', 'Median', minutes=6, cards=[
    definition(
        defbox('The <strong>median</strong> is the middle value of the sorted data, or the average of the two middle values when '
               'the count is even. MySQL has no MEDIAN() or PERCENTILE_CONT function, so it is computed with window functions.'),
        tags('Median', 'ROW_NUMBER', 'COUNT OVER', 'Percentile'),
    ),
    example(
        sqlrun("""
-- Overall median salary (10 rows → average of the 5th and 6th)
WITH s AS (
    SELECT salary,
           ROW_NUMBER() OVER (ORDER BY salary) AS rn,
           COUNT(*)     OVER ()                AS cnt
    FROM employees
)
SELECT AVG(salary) AS median_salary
FROM s
WHERE rn IN (FLOOR((cnt + 1) / 2), CEIL((cnt + 1) / 2));

-- Median per department
WITH s AS (
    SELECT dept_id, salary,
           ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary) AS rn,
           COUNT(*)     OVER (PARTITION BY dept_id)                AS cnt
    FROM employees WHERE dept_id IS NOT NULL
)
SELECT dept_id, AVG(salary) AS median_salary
FROM s
WHERE rn IN (FLOOR((cnt + 1) / 2), CEIL((cnt + 1) / 2))
GROUP BY dept_id;
""", setup=EMP),
        title='Example'),
    explanation(
        p('For odd <code>cnt</code>, FLOOR and CEIL of (cnt + 1) / 2 are the same row, so the AVG is just that value. For even '
          '<code>cnt</code> they are the two middle rows. The same pattern gives other percentiles by changing the position formula.'),
        title='Why FLOOR and CEIL'),
    crossq(
        ('Why might the median be preferred over the average?', 'It is not pulled by outliers. One very high salary raises the average a lot but barely moves the median.'),
        ('Which databases have a built-in function?', 'PostgreSQL and Oracle: <code>PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary)</code>. Spark SQL: <code>percentile_approx</code> or <code>median()</code>.'),
    ),
]),

# ------------------------------------------------------------------ 42
Q('Count new vs returning customers each month', 'New vs Returning Customers', minutes=7, cards=[
    definition(
        defbox('A customer is <strong>new</strong> in the month of their first order and <strong>returning</strong> in any later '
               'month they order again. Find each customer\'s first order month, then compare it with each order\'s month.'),
        tags('Cohort', 'First Purchase', 'MIN OVER', 'Retention', 'Product Analytics'),
    ),
    example(
        sqlrun("""
WITH o AS (
    SELECT customer_id,
           DATE_FORMAT(order_date, '%Y-%m') AS month,
           DATE_FORMAT(MIN(order_date) OVER (PARTITION BY customer_id), '%Y-%m') AS first_month
    FROM orders
    WHERE status <> 'CANCELLED'
)
SELECT month,
       COUNT(DISTINCT customer_id)                                       AS active,
       COUNT(DISTINCT CASE WHEN month = first_month THEN customer_id END) AS new_customers,
       COUNT(DISTINCT CASE WHEN month > first_month THEN customer_id END) AS returning_customers
FROM o
GROUP BY month
ORDER BY month;
""", setup=SALES),
        title='Example'),
    example(
        sqlrun("""
-- Month-over-month retention: of the customers active in a month, how many came back the next month?
WITH m AS (
    SELECT DISTINCT customer_id, DATE_FORMAT(order_date, '%Y-%m-01') AS month
    FROM orders WHERE status <> 'CANCELLED'
)
SELECT DATE_FORMAT(a.month, '%Y-%m') AS month,
       COUNT(*)              AS active,
       COUNT(b.customer_id)  AS retained_next_month
FROM m a
LEFT JOIN m b ON b.customer_id = a.customer_id
             AND b.month = a.month + INTERVAL 1 MONTH
GROUP BY a.month
ORDER BY a.month;
""", setup=SALES),
        title='Example: Next-Month Retention'),
    interview(p('Clarify definitions first: does a cancelled order count as activity? Is "new" based on signup date or first order? '
                'Here cancelled orders are excluded, which is why Neha is new in March, not January.')),
    crossq(
        ('How would you build a full cohort table?', 'Group by first_month (the cohort) and by the number of months since it (<code>TIMESTAMPDIFF(MONTH, first_month, month)</code>), count distinct customers, then pivot months-since into columns.'),
    ),
]),

# ------------------------------------------------------------------ 43
Q('Find missing IDs or gaps in a sequence', 'Missing IDs / Sequence Gaps', minutes=6, cards=[
    definition(
        defbox('Gaps appear when rows were deleted, inserts failed, or an extract missed data. Two approaches: compare each value '
               'with the <strong>next</strong> one using LEAD, or generate the full expected sequence (recursive CTE) and anti-join.'),
        tags('Gaps', 'LEAD', 'Recursive CTE', 'Anti-join', 'Data Quality'),
    ),
    example(
        sqlrun("""
CREATE TABLE invoices (invoice_no INT PRIMARY KEY);
INSERT INTO invoices VALUES (1001), (1002), (1003), (1006), (1007), (1010);

-- 1. Gap ranges with LEAD
SELECT invoice_no + 1 AS gap_from, next_no - 1 AS gap_to
FROM (SELECT invoice_no, LEAD(invoice_no) OVER (ORDER BY invoice_no) AS next_no FROM invoices) t
WHERE next_no - invoice_no > 1;

-- 2. Every missing number: generate the full range, then anti-join
SET SESSION cte_max_recursion_depth = 100000;
WITH RECURSIVE seq AS (
    SELECT MIN(invoice_no) AS n, MAX(invoice_no) AS mx FROM invoices
    UNION ALL
    SELECT n + 1, mx FROM seq WHERE n < mx
)
SELECT GROUP_CONCAT(n ORDER BY n) AS missing
FROM seq
WHERE NOT EXISTS (SELECT 1 FROM invoices i WHERE i.invoice_no = seq.n);
"""),
        title='Example'),
    real_world(p('A daily reconciliation check in a pipeline: an invoice series or an auto-increment id that jumps after a load can '
                 'indicate missing records. Note that AUTO_INCREMENT gaps are normal after rollbacks and failed inserts, so they '
                 'alone do not prove data loss.')),
    crossq(
        ('Find missing dates in a daily table?', 'The same two approaches with dates: <code>DATEDIFF(LEAD(day) OVER (ORDER BY day), day) &gt; 1</code>, or a recursive date series LEFT JOINed to the table.'),
    ),
]),

])
