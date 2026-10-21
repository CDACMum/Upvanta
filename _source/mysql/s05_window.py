from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

MONTHLY = """
CREATE TABLE monthly_revenue (month DATE PRIMARY KEY, revenue INT);
INSERT INTO monthly_revenue VALUES
('2026-01-01', 120), ('2026-02-01', 150), ('2026-03-01', 135),
('2026-04-01', 180), ('2026-05-01', 210), ('2026-06-01', 190);
"""

DAILY = """
CREATE TABLE daily_sales (day INT PRIMARY KEY, sales INT);
INSERT INTO daily_sales VALUES (1, 100), (2, 300), (3, 200), (4, 400), (5, 100), (6, 300);
"""

SECTION = dict(level='advanced', title='Window Functions', questions=[

# ------------------------------------------------------------------ 29
Q('What are window functions? How are they different from GROUP BY?', 'Window Functions Basics', minutes=8, cards=[
    definition(
        defbox('A <strong>window function</strong> performs a calculation across a set of rows related to the current row '
               '(its <em>window</em>) and returns a value <strong>for every row</strong>, without collapsing them. MySQL supports '
               'them from <strong>8.0</strong>.'),
        code("""
function_name(expr) OVER (
    PARTITION BY col      -- split rows into groups (optional)
    ORDER BY col          -- order within each partition (optional)
    ROWS/RANGE BETWEEN …  -- frame: which rows around the current one (optional)
)""", 'Syntax'),
        tags('OVER', 'PARTITION BY', 'ORDER BY', 'Frame', 'Analytic Functions', 'MySQL 8'),
    ),
    window_vs_groupby(),
    explanation(
        table(['Category', 'Functions'], [
            ['Ranking', 'ROW_NUMBER, RANK, DENSE_RANK, NTILE, PERCENT_RANK, CUME_DIST'],
            ['Value / offset', 'LAG, LEAD, FIRST_VALUE, LAST_VALUE, NTH_VALUE'],
            ['Aggregate as window', 'SUM, AVG, COUNT, MIN, MAX … with OVER()'],
        ]),
        p('Window functions are evaluated <strong>after WHERE, GROUP BY and HAVING</strong>, just before ORDER BY. So you '
          '<strong>cannot</strong> use them in WHERE; wrap the query in a CTE or derived table and filter outside.', True),
    ),
    example(
        sqlrun("""
SELECT name, dept_id, salary,
       ROUND(AVG(salary) OVER (PARTITION BY dept_id))           AS dept_avg,
       salary - ROUND(AVG(salary) OVER (PARTITION BY dept_id))  AS diff,
       ROUND(100 * salary / SUM(salary) OVER (PARTITION BY dept_id), 1) AS pct_of_dept,
       COUNT(*) OVER ()                                          AS company_headcount
FROM employees
WHERE dept_id IS NOT NULL
ORDER BY dept_id, salary DESC;
""", setup=EMP),
        title='Example'),
    example(
        sqlrun("""
-- Correct: compute in a CTE, filter outside
WITH ranked AS (
    SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC) AS rn FROM employees
)
SELECT name, salary FROM ranked WHERE rn <= 3;

-- Not allowed: window function in WHERE
SELECT name FROM employees WHERE ROW_NUMBER() OVER (ORDER BY salary DESC) <= 3;
""", setup=EMP, expect_error=True),
        title='Filtering on a Window Function'),
    crossq(
        ('What does OVER () with nothing inside mean?', 'The whole result set is one window. <code>SUM(salary) OVER ()</code> puts the grand total on every row.'),
        ('Can you name and reuse a window?', 'Yes: <code>… OVER w … WINDOW w AS (PARTITION BY dept_id ORDER BY salary DESC)</code>.'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('What is the difference between ROW_NUMBER, RANK and DENSE_RANK?', 'ROW_NUMBER vs RANK vs DENSE_RANK', minutes=6, cards=[
    definition(
        defbox('All three number the rows of each partition in the given order. They differ only in how they treat '
               '<strong>ties</strong>: ROW_NUMBER always gives unique numbers, RANK gives ties the same number and leaves gaps, '
               'DENSE_RANK gives ties the same number without gaps.'),
        tags('ROW_NUMBER', 'RANK', 'DENSE_RANK', 'Ties', 'Top-N'),
    ),
    rank_anim(),
    example(
        sqlrun("""
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num,
       RANK()       OVER (ORDER BY salary DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rnk
FROM employees
ORDER BY salary DESC;
""", setup=EMP),
        title='Example'),
    comparison(
        table(['Need', 'Use'], [
            ['Exactly one row per group (dedup, latest record)', 'ROW_NUMBER'],
            ['Nth highest distinct value', 'DENSE_RANK'],
            ['Competition ranking (1, 2, 2, 4)', 'RANK'],
            ['Top N including everyone tied at the boundary', 'RANK or DENSE_RANK'],
        ]),
        title='Which One to Use'),
    crossq(
        ('Is ROW_NUMBER deterministic for ties?', 'No. Rahul and Sneha could swap numbers between runs. Add a tie-breaker: <code>ORDER BY salary DESC, emp_id</code>.'),
    ),
]),

# ------------------------------------------------------------------ 31
Q('How do you find the Nth highest salary? Give multiple approaches', 'Nth Highest Salary', minutes=8, cards=[
    definition(
        defbox('The most asked SQL interview question. The intended meaning is usually the Nth highest <strong>distinct</strong> '
               'salary, and the query should return <strong>NULL</strong> when there are fewer than N distinct salaries.'),
        tags('Nth Highest', 'DENSE_RANK', 'LIMIT OFFSET', 'Correlated Subquery', 'Ties'),
    ),
    example(
        sqlrun("""
-- Approach 1: DISTINCT + LIMIT/OFFSET  (N = 3 → OFFSET 2)
SELECT DISTINCT salary AS third_highest
FROM employees ORDER BY salary DESC LIMIT 1 OFFSET 2;

-- Approach 2: DENSE_RANK (also returns all employees with that salary)
SELECT name, salary
FROM (SELECT name, salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS dr
      FROM employees) t
WHERE dr = 5;

-- Approach 3: correlated subquery (works on old versions too)
SELECT DISTINCT salary AS third_highest
FROM employees e1
WHERE 2 = (SELECT COUNT(DISTINCT e2.salary) FROM employees e2 WHERE e2.salary > e1.salary);

-- Second highest using MAX (classic)
SELECT MAX(salary) AS second_highest
FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);

-- Return NULL when N is too big: wrap in a scalar subquery
SELECT (SELECT DISTINCT salary FROM employees
        ORDER BY salary DESC LIMIT 1 OFFSET 99) AS hundredth_highest;
""", setup=EMP),
        title='Example'),
    comparison(
        table(['Approach', 'Pros', 'Cons'], [
            ['DISTINCT + LIMIT OFFSET', 'Short, fast with an index on salary', 'MySQL-specific; OFFSET cannot be a variable in plain SQL (use a prepared statement or a function)'],
            ['DENSE_RANK', 'Returns the names too; easy per department with PARTITION BY', 'Needs MySQL 8'],
            ['Correlated COUNT', 'Works everywhere', 'O(n²) on large tables'],
            ['MAX with subquery', 'Very simple', 'Only practical for the 2nd highest'],
        ]),
    ),
    interview(p('Always ask: "Distinct salaries or positions?" With salaries 150, 120, 120, the 3rd highest distinct is none, but '
                'the 3rd row is 120. State your assumption and mention how ties and N &gt; count are handled.')),
    crossq(
        ('How do you find the Nth highest salary in each department?', '<code>DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC)</code> and filter on the rank (next question).'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('How do you get the top N rows per group? (e.g. top 2 earners in each department)', 'Top N per Group', minutes=7, cards=[
    definition(
        defbox('Rank the rows <strong>within each group</strong> using a window function with <code>PARTITION BY</code>, then '
               'filter on the rank in an outer query. The choice of ROW_NUMBER, RANK or DENSE_RANK decides how ties are handled.'),
        tags('Top-N per Group', 'PARTITION BY', 'ROW_NUMBER', 'Greatest-N-per-group'),
    ),
    example(
        sqlrun("""
WITH ranked AS (
    SELECT dept_id, name, salary,
           ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rn,
           DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS dr
    FROM employees
    WHERE dept_id IS NOT NULL
)
SELECT dept_id, name, salary, rn, dr
FROM ranked
WHERE dr <= 3          -- try rn <= 3: Sneha or Rahul would be cut
ORDER BY dept_id, salary DESC;
""", setup=EMP),
        title='Example: Top 3 Salaries per Department (with ties)'),
    example(
        sqlrun("""
-- Latest order of each customer: the classic "one row per group" with ROW_NUMBER
SELECT customer_id, order_id, order_date, amount
FROM (SELECT o.*, ROW_NUMBER() OVER (PARTITION BY customer_id
                                     ORDER BY order_date DESC, order_id DESC) AS rn
      FROM orders o) t
WHERE rn = 1
ORDER BY customer_id;
""", setup=SALES),
        title='Example: Latest Record per Key'),
    explanation(
        code("""
SELECT e.dept_id, e.name, e.salary
FROM employees e
WHERE (SELECT COUNT(DISTINCT x.salary) FROM employees x
       WHERE x.dept_id = e.dept_id AND x.salary > e.salary) < 2;
""", 'Before MySQL 8: Correlated Count'),
        title='Without Window Functions'),
    real_world(p('"Latest record per key" is how you deduplicate CDC or incremental data before merging into a target: '
                 'keep <code>rn = 1</code> per primary key ordered by <code>updated_at DESC</code>.')),
    crossq(
        ('ROW_NUMBER or DENSE_RANK for "top 3 earners"?', 'Ask. If two people tie for 3rd, ROW_NUMBER returns exactly 3 rows (dropping one arbitrarily). DENSE_RANK/RANK return everyone tied, which is usually fairer for reports.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What are LAG and LEAD? Calculate month-over-month growth', 'LAG & LEAD', minutes=7, cards=[
    definition(
        defbox('<strong>LAG(expr, n, default)</strong> returns the value of <code>expr</code> from the row <em>n</em> rows '
               '<strong>before</strong> the current row in the window order; <strong>LEAD</strong> returns it from <em>n</em> rows '
               '<strong>after</strong>. n defaults to 1 and the default value to NULL.'),
        tags('LAG', 'LEAD', 'Offset', 'Month-over-Month', 'Previous Row'),
    ),
    lag_lead_anim(),
    example(
        sqlrun("""
SELECT DATE_FORMAT(month, '%b') AS mon, revenue,
       LAG(revenue)  OVER w                                         AS prev_month,
       revenue - LAG(revenue) OVER w                                AS change_abs,
       ROUND(100 * (revenue - LAG(revenue) OVER w) / LAG(revenue) OVER w, 1) AS change_pct,
       LEAD(revenue) OVER w                                         AS next_month
FROM monthly_revenue
WINDOW w AS (ORDER BY month)
ORDER BY month;
""", setup=MONTHLY),
        title='Example: Month-over-Month Growth'),
    example(
        sqlrun("""
-- Days between consecutive orders of the same customer
SELECT customer_id, order_id, order_date,
       DATEDIFF(order_date, LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date)) AS days_since_prev
FROM orders
WHERE customer_id IN (1, 2)
ORDER BY customer_id, order_date;
""", setup=SALES),
        title='Example: Gap Between Orders per Customer'),
    crossq(
        ('How did people do this before window functions?', 'A self-join on the previous period: <code>JOIN monthly_revenue p ON p.month = m.month - INTERVAL 1 MONTH</code>. LAG is simpler and also works when periods are missing (it takes the previous <em>row</em>).'),
        ('Find months where revenue dropped compared to the previous month.', 'Compute LAG in a CTE, then <code>WHERE revenue &lt; prev_month</code> outside (Mar and Jun here).'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do you calculate running totals and moving averages? Explain ROWS vs RANGE frames', 'Running Totals & Frames', minutes=8, cards=[
    definition(
        defbox('An aggregate with <code>OVER (ORDER BY …)</code> works on a <strong>frame</strong>: a range of rows relative to '
               'the current row. With ORDER BY and no explicit frame, the default is '
               '<code>RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW</code>, which gives a running total.'),
        tags('Running Total', 'Moving Average', 'Frame', 'ROWS', 'RANGE', 'UNBOUNDED PRECEDING'),
    ),
    frame_anim(),
    example(
        sqlrun("""
SELECT day, sales,
       SUM(sales) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
       ROUND(AVG(sales) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moving_avg_3,
       SUM(sales) OVER (ORDER BY day ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING)          AS centred_sum_3
FROM daily_sales
ORDER BY day;
""", setup=DAILY),
        title='Example: Running Total and Moving Average'),
    comparison(
        table(['Frame unit', 'Meaning', 'With ties in ORDER BY'], [
            ['ROWS', 'Physical rows: "2 rows before me"', 'Each row gets its own running value'],
            ['RANGE', 'Logical values: "all rows whose ORDER BY value is ≤ mine"', 'Tied rows (peers) get the <strong>same</strong> value'],
        ]),
        title='ROWS vs RANGE'),
    example(
        sqlrun("""
SELECT name, salary,
       SUM(salary) OVER (ORDER BY salary)                                            AS default_range,
       SUM(salary) OVER (ORDER BY salary ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS with_rows
FROM employees
WHERE salary BETWEEN 80000 AND 115000
ORDER BY salary;
""", setup=EMP),
        title='Example: Where RANGE and ROWS Differ'),
    warn('Rahul and Sneha both earn 95,000, so with the default RANGE frame they are peers and both get 2,72,000. '
         'If you want a strict row-by-row running total, write ROWS explicitly (and add a unique tie-breaker to ORDER BY).', 'Gotcha'),
    crossq(
        ('Running total per customer?', 'Add a partition: <code>SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date ROWS UNBOUNDED PRECEDING)</code>.'),
        ('What frame bounds are allowed?', '<code>UNBOUNDED PRECEDING</code>, <code>n PRECEDING</code>, <code>CURRENT ROW</code>, <code>n FOLLOWING</code>, <code>UNBOUNDED FOLLOWING</code>. RANGE also accepts intervals in MySQL: <code>RANGE BETWEEN INTERVAL 7 DAY PRECEDING AND CURRENT ROW</code>.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('Explain FIRST_VALUE, LAST_VALUE, NTH_VALUE, NTILE, PERCENT_RANK and CUME_DIST', 'Other Window Functions', minutes=7, cards=[
    definition(
        defbox('<strong>FIRST_VALUE / LAST_VALUE / NTH_VALUE</strong> return the value from the first, last or nth row of the frame. '
               '<strong>NTILE(n)</strong> splits the ordered rows into n roughly equal buckets (quartiles, deciles). '
               '<strong>PERCENT_RANK</strong> and <strong>CUME_DIST</strong> give a row\'s relative position between 0 and 1.'),
        tags('FIRST_VALUE', 'LAST_VALUE', 'NTH_VALUE', 'NTILE', 'PERCENT_RANK', 'CUME_DIST'),
    ),
    explanation(
        table(['Function', 'Formula / meaning'], [
            ['NTILE(4)', 'Bucket number 1–4; earlier buckets get the extra rows when the count does not divide evenly'],
            ['PERCENT_RANK()', '(rank − 1) / (rows − 1): 0 for the first row, 1 for the last'],
            ['CUME_DIST()', 'rows with value ≤ current / total rows: always &gt; 0'],
        ]),
    ),
    example(
        sqlrun("""
SELECT name, dept_id, salary,
       FIRST_VALUE(name) OVER w                                              AS top_earner,
       LAST_VALUE(name)  OVER w                                              AS last_value_default,
       LAST_VALUE(name)  OVER (w ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS lowest_earner
FROM employees
WHERE dept_id = 10
WINDOW w AS (PARTITION BY dept_id ORDER BY salary DESC, emp_id);

SELECT name, salary,
       NTILE(4) OVER (ORDER BY salary DESC)                   AS quartile,
       ROUND(PERCENT_RANK() OVER (ORDER BY salary DESC), 2)   AS pct_rank,
       ROUND(CUME_DIST()    OVER (ORDER BY salary DESC), 2)   AS cum_dist
FROM employees
ORDER BY salary DESC;
""", setup=EMP),
        title='Example'),
    warn('<code>LAST_VALUE</code> with the default frame (up to the <em>current row</em>) just returns the current row\'s value, '
         'as the <code>last_value_default</code> column shows. Extend the frame to <code>UNBOUNDED FOLLOWING</code>, or use '
         'FIRST_VALUE with the opposite ORDER BY.', 'Classic Trap'),
    crossq(
        ('Where is NTILE used in practice?', 'Customer segmentation (top 10% spenders with NTILE(10)), splitting a table into equal chunks for parallel extraction, and grading on a curve.'),
    ),
]),

])
