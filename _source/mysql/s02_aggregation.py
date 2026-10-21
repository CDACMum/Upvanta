from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

SECTION = dict(level='basic', title='Filtering, Aggregation & Functions', questions=[

# ------------------------------------------------------------------ 9
Q('How do LIKE, IN, BETWEEN and REGEXP work for filtering?', 'LIKE, IN, BETWEEN, REGEXP', minutes=6, cards=[
    definition(
        defbox('<strong>LIKE</strong> matches patterns with two wildcards: <code>%</code> (any number of characters) and '
               '<code>_</code> (exactly one). <strong>IN</strong> tests membership in a list. <strong>BETWEEN a AND b</strong> '
               'is an <em>inclusive</em> range. <strong>REGEXP</strong> (or <code>RLIKE</code>) matches regular expressions.'),
        tags('LIKE', 'Wildcards', 'IN', 'BETWEEN', 'REGEXP', 'Collation'),
    ),
    sample('employees'),
    example(
        sqlrun("""
-- Names starting with R, and names whose 2nd letter is 'r'
SELECT name FROM employees WHERE name LIKE 'R%';
SELECT name FROM employees WHERE name LIKE '_r%';

-- IN list and inclusive BETWEEN
SELECT name, city FROM employees WHERE city IN ('Pune', 'Delhi') ORDER BY name;
SELECT name, salary FROM employees WHERE salary BETWEEN 82000 AND 95000 ORDER BY salary;

-- Names starting with a vowel, or ending in 'ya'
SELECT name FROM employees WHERE name REGEXP '^[AEIOU]|ya$';

-- Comparisons are case-insensitive with the default collation
SELECT COUNT(*) AS matches FROM employees WHERE name = 'arjun';
""", setup=EMP),
        title='Example'),
    warn('<code>BETWEEN \'2026-01-01\' AND \'2026-01-31\'</code> on a <strong>DATETIME</strong> column misses everything after '
         'midnight on 31 Jan, because \'2026-01-31\' means 2026-01-31 00:00:00. Use a half-open range instead: '
         '<code>dt &gt;= \'2026-01-01\' AND dt &lt; \'2026-02-01\'</code>.', 'Classic Date Bug'),
    crossq(
        ('Does LIKE \'%abc\' use an index?', 'No. A leading wildcard means the B-tree cannot be used, so MySQL scans. <code>LIKE \'abc%\'</code> (prefix) can use an index. For "contains" searches on text, use a FULLTEXT index.'),
        ('How do you search for a literal % or _?', 'Escape it: <code>LIKE \'50\\%%\'</code> or choose an escape character: <code>LIKE \'50!%%\' ESCAPE \'!\'</code>.'),
        ('How do you make a comparison case-sensitive?', 'Use a binary or case-sensitive collation: <code>WHERE name = BINARY \'arjun\'</code> or <code>WHERE name COLLATE utf8mb4_bin = \'arjun\'</code>.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('How does GROUP BY work? Explain COUNT(*), COUNT(col) and COUNT(DISTINCT col)', 'GROUP BY & Aggregates', minutes=7, cards=[
    definition(
        defbox('<strong>GROUP BY</strong> collapses rows that share the same value(s) into one group, and <strong>aggregate '
               'functions</strong> (COUNT, SUM, AVG, MIN, MAX) compute one value per group.'),
        tags('GROUP BY', 'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT'),
    ),
    group_by_anim(),
    comparison(
        table(['Form', 'Counts', 'NULLs'], [
            ['COUNT(*)', 'Every row in the group', 'Included'],
            ['COUNT(1)', 'Same as COUNT(*) (no performance difference in MySQL)', 'Included'],
            ['COUNT(col)', 'Rows where col is not NULL', 'Skipped'],
            ['COUNT(DISTINCT col)', 'Distinct non-NULL values', 'Skipped'],
        ]),
        title='The COUNT Variants'),
    example(
        sqlrun("""
SELECT dept_id, COUNT(*) AS cnt, SUM(salary) AS total,
       ROUND(AVG(salary)) AS avg_sal, MIN(salary) AS min_sal, MAX(salary) AS max_sal
FROM employees
GROUP BY dept_id
ORDER BY dept_id;

SELECT COUNT(*) AS rows_, COUNT(dept_id) AS non_null_dept,
       COUNT(DISTINCT dept_id) AS distinct_dept, COUNT(DISTINCT city) AS cities
FROM employees;

-- Group by more than one column
SELECT dept_id, city, COUNT(*) AS cnt
FROM employees WHERE dept_id IS NOT NULL
GROUP BY dept_id, city ORDER BY dept_id, city;
""", setup=EMP),
        title='Example'),
    crossq(
        ('Which rows go into the NULL group?', 'All rows whose grouping column is NULL form <strong>one</strong> group, even though NULL ≠ NULL in comparisons.'),
        ('Is ORDER BY implied by GROUP BY in MySQL 8?', 'No. Since 8.0 GROUP BY does not sort the result. Add ORDER BY explicitly if you need an order.'),
        ('What is the difference between SELECT DISTINCT and GROUP BY?', 'For listing unique values they give the same result and usually the same plan. GROUP BY is needed when you also want aggregates per value.'),
    ),
]),

# ------------------------------------------------------------------ 11
Q('What is the ONLY_FULL_GROUP_BY error and how do you fix it?', 'ONLY_FULL_GROUP_BY Error', minutes=6, cards=[
    definition(
        defbox('With the <code>ONLY_FULL_GROUP_BY</code> SQL mode (on by default since MySQL 5.7), every column in SELECT, '
               'HAVING or ORDER BY must be either in the GROUP BY, inside an aggregate, or <em>functionally dependent</em> on '
               'the GROUP BY columns. Otherwise MySQL raises <strong>ERROR 1055</strong>.'),
        hl('A group of 4 employees has 4 names. If you ask for <code>name</code> per department, which one should MySQL return? '
           'Old MySQL silently picked any one; strict mode refuses.', 'Why'),
        tags('ONLY_FULL_GROUP_BY', 'ERROR 1055', 'ANY_VALUE', 'Functional Dependency', 'sql_mode'),
    ),
    example(
        sqlrun("""
-- Intent: highest-paid employee in each department
SELECT dept_id, name, MAX(salary) AS max_sal
FROM employees
GROUP BY dept_id;
""", setup=EMP, expect_error=True),
        title='The Error'),
    example(
        sqlrun("""
-- Fix 1: join back to the aggregated result (works in every database)
SELECT e.dept_id, e.name, e.salary
FROM employees e
JOIN (SELECT dept_id, MAX(salary) AS max_sal
      FROM employees GROUP BY dept_id) m
  ON e.dept_id = m.dept_id AND e.salary = m.max_sal
ORDER BY e.dept_id;

-- Fix 2: window function (MySQL 8+)
SELECT dept_id, name, salary
FROM (SELECT dept_id, name, salary,
             RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rnk
      FROM employees WHERE dept_id IS NOT NULL) t
WHERE rnk = 1;

-- ANY_VALUE: only when you truly do not care which value is returned
SELECT dept_id, ANY_VALUE(city) AS some_city, COUNT(*) AS cnt
FROM employees WHERE dept_id IS NOT NULL GROUP BY dept_id;
""", setup=EMP),
        title='The Fixes'),
    warn('Turning the mode off (<code>SET sql_mode = \'\'</code>) hides the error but returns an <strong>arbitrary</strong> name, '
         'usually not the one with the max salary. That is a silent wrong answer.', 'Do Not'),
    crossq(
        ('When is a non-grouped column allowed?', 'When it is functionally dependent on the group: <code>GROUP BY emp_id</code> (a primary key) lets you select any column of that row, because the key determines them.'),
        ('Why does MAX(salary) not return the matching name?', 'Aggregates work independently per column. MAX(salary) finds the largest value; it does not "point" at the row that holds it.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How do you use CASE expressions and conditional aggregation?', 'CASE & Conditional Aggregation', minutes=7, cards=[
    definition(
        defbox('<strong>CASE</strong> is SQL\'s if-else. It returns a value and can be used in SELECT, WHERE, ORDER BY, GROUP BY '
               'and inside aggregates.',
               '<strong>Conditional aggregation</strong> puts CASE inside SUM/COUNT to compute several filtered totals in one '
               'pass, e.g. one column per status. It is the standard way to <strong>pivot</strong> rows into columns.'),
        tags('CASE WHEN', 'IF()', 'Conditional Aggregation', 'Pivot', 'SUM(CASE…)'),
    ),
    explanation(
        code("""
-- Searched CASE (most common)
CASE WHEN salary >= 110000 THEN 'High'
     WHEN salary >= 80000  THEN 'Medium'
     ELSE 'Low' END

-- Simple CASE
CASE status WHEN 'DELIVERED' THEN 1 ELSE 0 END

-- MySQL shortcut for two branches
IF(status = 'CANCELLED', 0, amount)
""", 'Syntax'),
        p('Conditions are checked top to bottom and the <strong>first</strong> true branch wins. With no ELSE, unmatched rows get NULL.', True),
    ),
    sample('orders'),
    example(
        sqlrun("""
-- Salary bands
SELECT name, salary,
       CASE WHEN salary >= 110000 THEN 'High'
            WHEN salary >= 80000  THEN 'Medium'
            ELSE 'Low' END AS band
FROM employees ORDER BY salary DESC LIMIT 5;

-- Pivot: one row per month, one column per status
SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,
       COUNT(*) AS orders,
       SUM(CASE WHEN status = 'DELIVERED' THEN 1 ELSE 0 END) AS delivered,
       SUM(status = 'SHIPPED')                                AS shipped,   -- MySQL: TRUE = 1
       SUM(CASE WHEN status = 'CANCELLED' THEN amount ELSE 0 END) AS cancelled_value,
       SUM(IF(status <> 'CANCELLED', amount, 0))              AS net_revenue
FROM orders
GROUP BY month ORDER BY month;
""", setup=ALL),
        title='Example'),
    interview(p('Custom sort order is another favourite: <code>ORDER BY CASE status WHEN \'SHIPPED\' THEN 1 WHEN \'DELIVERED\' THEN 2 ELSE 3 END</code> '
                '(or MySQL\'s <code>ORDER BY FIELD(status, \'SHIPPED\', \'DELIVERED\')</code>).')),
    crossq(
        ('COUNT(CASE WHEN … THEN 1 END) vs SUM(CASE WHEN … THEN 1 ELSE 0 END)?', 'Same result. COUNT counts non-NULL values, and CASE without ELSE gives NULL for non-matching rows.'),
        ('How do you update different rows to different values in one statement?', '<code>UPDATE employees SET salary = CASE WHEN dept_id = 10 THEN salary * 1.10 ELSE salary * 1.05 END;</code>'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('What are the commonly used string functions in MySQL?', 'String Functions', minutes=6, cards=[
    definition(
        defbox('String functions clean and reshape text: joining, cutting, searching, padding and changing case. They are used '
               'heavily in data cleaning and in coding rounds (for example extracting the domain from an email).'),
        tags('CONCAT', 'SUBSTRING', 'SUBSTRING_INDEX', 'TRIM', 'REPLACE', 'CHAR_LENGTH', 'LPAD'),
    ),
    explanation(
        table(['Function', 'Purpose', 'Example → result'], [
            ['CONCAT(a, b, …)', 'Join strings (NULL if any argument is NULL)', "CONCAT('Big', 'Data') → BigData"],
            ['CONCAT_WS(sep, …)', 'Join with separator, skips NULLs', "CONCAT_WS('-', 'a', NULL, 'b') → a-b"],
            ['SUBSTRING(s, pos, len)', 'Part of a string (1-based)', "SUBSTRING('MySQL', 3, 3) → SQL"],
            ['LEFT / RIGHT(s, n)', 'First / last n characters', "RIGHT('2026-10', 2) → 10"],
            ['SUBSTRING_INDEX(s, d, n)', 'Text before the n-th delimiter (after it if n &lt; 0)', "SUBSTRING_INDEX('a@x.com', '@', -1) → x.com"],
            ['LOCATE / INSTR', 'Position of a substring (0 if absent)', "LOCATE('@', 'a@x.com') → 2"],
            ['TRIM / LTRIM / RTRIM', 'Remove spaces (or given chars)', "TRIM('  hi ') → hi"],
            ['REPLACE(s, from, to)', 'Replace all occurrences', "REPLACE('9-8-7', '-', '') → 987"],
            ['UPPER / LOWER', 'Change case', "UPPER('pune') → PUNE"],
            ['LENGTH vs CHAR_LENGTH', 'Bytes vs characters', "LENGTH('₹') → 3, CHAR_LENGTH('₹') → 1"],
            ['LPAD / RPAD', 'Pad to a length', "LPAD('7', 3, '0') → 007"],
        ]),
    ),
    example(
        sqlrun("""
CREATE TABLE contacts (id INT, full_name VARCHAR(50), email VARCHAR(60), phone VARCHAR(20));
INSERT INTO contacts VALUES
 (1, '  asha  RAO ', 'Asha.Rao@Gmail.com', '+91 98200-12345'),
 (2, 'ravi kumar',   'ravi@cdac.in',       '98201 54321');

SELECT id,
       CONCAT(UPPER(LEFT(TRIM(full_name), 1)),
              LOWER(REGEXP_REPLACE(SUBSTRING(TRIM(full_name), 2), ' +', ' '))) AS clean_name,
       LOWER(SUBSTRING_INDEX(email, '@', -1))                   AS domain,
       RIGHT(REPLACE(REPLACE(REPLACE(phone, ' ', ''), '-', ''), '+91', ''), 10) AS phone10,
       CONCAT('EMP', LPAD(id, 4, '0'))                          AS emp_code
FROM contacts;
"""),
        title='Example: Cleaning Contact Data'),
    crossq(
        ('Why does CONCAT return NULL sometimes?', 'If any argument is NULL, CONCAT returns NULL. Use CONCAT_WS or wrap columns in COALESCE.'),
        ('How do you collapse multiple spaces inside a string?', "MySQL 8: <code>REGEXP_REPLACE(s, ' +', ' ')</code>. REGEXP_SUBSTR and REGEXP_INSTR are also available."),
    ),
]),

# ------------------------------------------------------------------ 14
Q('What are the commonly used date and time functions in MySQL?', 'Date & Time Functions', minutes=7, cards=[
    definition(
        defbox('Date functions get the current time, do date arithmetic, extract parts and format or parse dates. Almost every '
               'reporting and incremental-load query uses them.'),
        tags('NOW', 'CURDATE', 'DATE_ADD', 'DATEDIFF', 'TIMESTAMPDIFF', 'DATE_FORMAT', 'STR_TO_DATE', 'LAST_DAY'),
    ),
    explanation(
        table(['Function', 'Purpose'], [
            ['NOW() / CURDATE() / CURTIME()', 'Current datetime / date / time'],
            ['DATE_ADD(d, INTERVAL n unit) / DATE_SUB', 'Add or subtract days, months, hours …'],
            ['DATEDIFF(a, b)', 'Days between two dates (a − b)'],
            ['TIMESTAMPDIFF(unit, a, b)', 'Difference in any unit (b − a): MONTH, YEAR, HOUR …'],
            ['YEAR(), MONTH(), DAY(), DAYNAME(), QUARTER(), WEEK()', 'Extract parts'],
            ['DATE_FORMAT(d, fmt)', "Date → string, e.g. '%Y-%m' or '%d %b %Y'"],
            ['STR_TO_DATE(s, fmt)', "String → date, e.g. STR_TO_DATE('11/10/2026', '%d/%m/%Y')"],
            ['LAST_DAY(d)', 'Last day of that month'],
            ['DATE(dt)', 'Strip the time part'],
        ]),
    ),
    example(
        sqlrun("""
SET @d = '2026-10-11';

SELECT DATE_ADD(@d, INTERVAL 30 DAY)            AS plus_30_days,
       DATE_SUB(@d, INTERVAL 1 MONTH)           AS minus_1_month,
       LAST_DAY(@d)                             AS month_end,
       DATE_FORMAT(@d, '%Y-%m-01')              AS month_start,
       DATE_FORMAT(@d, '%d %b %Y, %W')          AS pretty,
       STR_TO_DATE('15/08/2026', '%d/%m/%Y')    AS parsed;

-- Tenure of each employee as on @d
SELECT name, hire_date,
       DATEDIFF(@d, hire_date)                   AS days,
       TIMESTAMPDIFF(YEAR, hire_date, @d)        AS full_years
FROM employees ORDER BY hire_date LIMIT 4;

-- Monthly revenue
SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, SUM(amount) AS revenue
FROM orders WHERE status <> 'CANCELLED'
GROUP BY month ORDER BY month;
""", setup=ALL),
        title='Example'),
    warn('<code>WHERE YEAR(order_date) = 2026</code> wraps the column in a function, so an index on order_date cannot be used. '
         'Write <code>WHERE order_date &gt;= \'2026-01-01\' AND order_date &lt; \'2027-01-01\'</code>. See "Why is my index not used?" in the Performance section.',
         'Performance Trap'),
    crossq(
        ('NOW() vs SYSDATE()?', 'NOW() is fixed at the start of the statement (same value for every row). SYSDATE() is evaluated each time it is called, so it can differ within one statement.'),
        ('How do you get the first day of the current month?', "<code>DATE_FORMAT(CURDATE(), '%Y-%m-01')</code> or <code>LAST_DAY(CURDATE() - INTERVAL 1 MONTH) + INTERVAL 1 DAY</code>."),
    ),
]),

# ------------------------------------------------------------------ 15
Q('What are GROUP_CONCAT and WITH ROLLUP?', 'GROUP_CONCAT & ROLLUP', minutes=6, cards=[
    definition(
        defbox('<strong>GROUP_CONCAT</strong> is an aggregate that joins the values of a group into one string, e.g. all '
               'employee names of a department as "Arjun, Priya, Rahul".',
               '<strong>WITH ROLLUP</strong> adds subtotal rows for each level of the GROUP BY and a grand-total row. The '
               '<code>GROUPING()</code> function tells you whether a NULL in the result is a real NULL or a subtotal row.'),
        tags('GROUP_CONCAT', 'SEPARATOR', 'WITH ROLLUP', 'GROUPING()', 'Subtotals'),
    ),
    example(
        sqlrun("""
SELECT dept_id,
       GROUP_CONCAT(name ORDER BY salary DESC SEPARATOR ', ') AS team,
       GROUP_CONCAT(DISTINCT city ORDER BY city) AS cities
FROM employees WHERE dept_id IS NOT NULL
GROUP BY dept_id;

-- Subtotal per department and a grand total
SELECT IF(GROUPING(dept_id), 'ALL DEPTS', dept_id) AS dept,
       IF(GROUPING(city), 'subtotal', city)        AS city,
       SUM(salary) AS total_salary
FROM employees WHERE dept_id IS NOT NULL
GROUP BY dept_id, city WITH ROLLUP;
""", setup=EMP),
        title='Example'),
    warn('GROUP_CONCAT output is cut at <code>group_concat_max_len</code> (default 1024 bytes) with only a warning. For long lists raise it: <code>SET SESSION group_concat_max_len = 100000;</code>', 'Silent Truncation'),
    crossq(
        ('What is the equivalent in other databases?', 'PostgreSQL and SQL Server use <code>STRING_AGG(name, \', \')</code>, Oracle uses <code>LISTAGG</code>, Spark SQL uses <code>concat_ws(\',\', collect_list(name))</code>.'),
        ('Does MySQL support CUBE and GROUPING SETS?', 'No, only WITH ROLLUP. Other combinations can be built with UNION ALL of separate GROUP BYs.'),
    ),
]),

])
