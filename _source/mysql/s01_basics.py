from build import *
from mysql.anims import *
from mysql.data import EMP, SALES, ALL, sample

SECTION = dict(level='beginner', title='MySQL Basics', questions=[

# ------------------------------------------------------------------ 1
Q('What is MySQL? Explain the MySQL architecture', 'MySQL & Its Architecture', minutes=7, cards=[
    definition(
        defbox('<strong>MySQL</strong> is an open-source relational database management system, now owned by Oracle. '
               'It stores data in tables, is queried with SQL, and is one of the most widely used databases behind web '
               'and business applications.',
               'Its defining design feature is the <strong>pluggable storage engine</strong> architecture: one common '
               'SQL layer (parsing, optimisation, execution) sits on top of interchangeable engines that store the data. '
               '<strong>InnoDB</strong> has been the default engine since MySQL 5.5.'),
        hl('For a data engineer, MySQL is most often a <strong>source system</strong>: the OLTP database of an application '
           'that you extract from (full loads, incremental loads, or CDC from the binary log).', 'Why it matters'),
        tags('MySQL 8.0', 'InnoDB', 'Storage Engine', 'Optimizer', 'Port 3306', 'Client-Server'),
    ),
    mysql_arch(),
    explanation(
        table(['Layer', 'Responsibility', 'Examples'], [
            ['Connection layer', 'Client connections, threads, authentication, SSL', 'max_connections, thread cache'],
            ['SQL layer', 'Parse, check privileges, optimise and execute SQL', 'Parser, optimizer, executor, built-in functions, views, procedures'],
            ['Storage engine', 'Physically store, index and fetch rows; transactions and locking', 'InnoDB, MyISAM, MEMORY, CSV, ARCHIVE'],
            ['Files / logs', 'Durability, recovery and replication', '.ibd tablespaces, redo log, undo log, binary log'],
        ]),
        p('Because the engine is chosen per table, features such as transactions, row locking and foreign keys are '
          '<strong>engine features</strong>, not MySQL-wide features. That is why the InnoDB vs MyISAM question is so common.', True),
    ),
    example(
        sqlrun("""
SELECT VERSION() AS version;

-- Which engines does this server support, and which is the default?
SELECT ENGINE, SUPPORT, TRANSACTIONS
FROM information_schema.ENGINES
WHERE ENGINE IN ('InnoDB', 'MyISAM', 'MEMORY', 'CSV')
ORDER BY ENGINE;
"""),
        title='Example: Checking the Server'),
    crossq(
        ('Is MySQL the same as MariaDB?',
         'MariaDB is a fork of MySQL created in 2009 by MySQL\'s original developers after Oracle acquired it. Basic SQL is '
         'the same, but they have diverged: for example the <code>-&gt;&gt;</code> JSON operator and <code>EXPLAIN ANALYZE</code> '
         'are MySQL 8 syntax, while MariaDB has its own equivalents.'),
        ('What is the default port of MySQL?', '<strong>3306</strong>. MySQL X Protocol (document store) uses 33060.'),
        ('What is the difference between MySQL and SQL?',
         '<strong>SQL</strong> is the query language (a standard). <strong>MySQL</strong> is a database product that '
         'implements SQL, plus its own extensions such as <code>LIMIT</code>, <code>ON DUPLICATE KEY UPDATE</code> and <code>GROUP_CONCAT</code>.'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What is the difference between InnoDB and MyISAM?', 'InnoDB vs MyISAM', minutes=6, cards=[
    definition(
        defbox('<strong>InnoDB</strong> is MySQL\'s default, transactional storage engine: it supports ACID transactions, '
               'row-level locking, foreign keys and crash recovery.',
               '<strong>MyISAM</strong> is the older, non-transactional engine with table-level locking. It is rarely used for '
               'new tables today.'),
        tags('InnoDB', 'MyISAM', 'Row-level Locking', 'Table-level Locking', 'Crash Recovery'),
    ),
    comparison(
        table(['Feature', 'InnoDB', 'MyISAM'], [
            ['Transactions (COMMIT / ROLLBACK)', 'Yes, fully ACID', 'No'],
            ['Locking', 'Row-level (high concurrency)', 'Table-level (writes block the whole table)'],
            ['Foreign keys', 'Supported', 'Ignored'],
            ['Crash recovery', 'Automatic, using the redo log', 'Tables can be corrupted; needs REPAIR TABLE'],
            ['MVCC (consistent reads without locks)', 'Yes', 'No'],
            ['Data layout', 'Clustered on the primary key', 'Heap file + separate index file'],
            ['SELECT COUNT(*) without WHERE', 'Counts rows (slower on huge tables)', 'Instant (stored row count)'],
            ['Default since', 'MySQL 5.5', 'Was default before 5.5'],
        ]),
    ),
    example(
        sqlrun("""
CREATE TABLE acc_innodb (id INT PRIMARY KEY, bal INT) ENGINE = InnoDB;
CREATE TABLE acc_myisam (id INT PRIMARY KEY, bal INT) ENGINE = MyISAM;

START TRANSACTION;
INSERT INTO acc_innodb VALUES (1, 500);
INSERT INTO acc_myisam VALUES (1, 500);
ROLLBACK;

-- InnoDB undid the insert; MyISAM could not
SELECT 'innodb' AS engine, COUNT(*) AS rows_after_rollback FROM acc_innodb
UNION ALL
SELECT 'myisam', COUNT(*) FROM acc_myisam;
"""),
        title='Example: ROLLBACK on Each Engine'),
    interview(
        p('A short answer that scores well: <em>"InnoDB is the default and should be used for almost everything because it '
          'gives transactions, row locks, foreign keys and crash safety. MyISAM is legacy: no transactions and table-level '
          'locks, so it only made sense for read-mostly tables in old versions."</em>'),
    ),
    crossq(
        ('How do you change a table\'s engine?', '<code>ALTER TABLE t ENGINE = InnoDB;</code> It rebuilds the table, so run it in a maintenance window for big tables.'),
        ('Which other engines exist?', '<strong>MEMORY</strong> (data in RAM, lost on restart), <strong>CSV</strong> (stores rows as a CSV file), '
         '<strong>ARCHIVE</strong> (compressed, insert-only), <strong>BLACKHOLE</strong> (discards writes but still logs them for replication).'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('Explain MySQL data types. CHAR vs VARCHAR, DECIMAL vs FLOAT, DATETIME vs TIMESTAMP', 'Data Types', minutes=8, cards=[
    definition(
        defbox('A <strong>data type</strong> fixes what values a column can hold, how much space it takes and how it is '
               'compared and sorted. Picking the right type keeps data correct and tables small (and smaller tables mean '
               'more rows fit in memory).'),
        tags('INT', 'BIGINT', 'DECIMAL', 'VARCHAR', 'DATETIME', 'TIMESTAMP', 'JSON', 'ENUM'),
    ),
    explanation(
        table(['Group', 'Types', 'Notes'], [
            ['Integers', 'TINYINT (1 B), SMALLINT (2), MEDIUMINT (3), INT (4), BIGINT (8)', 'UNSIGNED doubles the positive range. INT max ≈ 2.1 billion.'],
            ['Exact decimals', 'DECIMAL(p, s)', 'Exact. Use for money: DECIMAL(12,2).'],
            ['Approximate', 'FLOAT (4 B), DOUBLE (8 B)', 'Binary floating point, small rounding errors. Use for measurements, not money.'],
            ['Strings', 'CHAR(n), VARCHAR(n), TEXT, LONGTEXT', 'n is in characters. VARCHAR up to 65,535 bytes per row in total.'],
            ['Date and time', 'DATE, TIME, DATETIME, TIMESTAMP, YEAR', 'DATETIME: 1000–9999. TIMESTAMP: 1970–2038, stored in UTC.'],
            ['Others', 'ENUM, SET, JSON, BLOB, BOOLEAN', 'BOOLEAN is just TINYINT(1).'],
        ]),
    ),
    comparison(
        table(['Pair', 'First', 'Second'], [
            ['CHAR(n) vs VARCHAR(n)', 'Fixed length, padded with spaces; trailing spaces removed on read. Good for fixed codes (country code, PAN).',
             'Variable length + 1–2 byte length prefix. Keeps trailing spaces. Good for names, emails.'],
            ['DECIMAL vs FLOAT/DOUBLE', 'Exact base-10 arithmetic', 'Approximate binary arithmetic: 0.1 + 0.2 ≠ 0.3'],
            ['DATETIME vs TIMESTAMP', 'Stores the value as given, no time zone. 5 bytes. Range to year 9999.',
             'Converted from session time zone to UTC on write and back on read. 4 bytes. Range ends 2038-01-19.'],
        ]),
        title='The Three Classic Comparisons'),
    example(
        sqlrun("""
CREATE TABLE t (c CHAR(5), v VARCHAR(5), f FLOAT, d DECIMAL(5,2),
                dt DATETIME, ts TIMESTAMP);
SET time_zone = '+05:30';
INSERT INTO t VALUES ('ab  ', 'ab  ', 0.1, 0.1, '2026-10-11 10:00:00', '2026-10-11 10:00:00');
INSERT INTO t VALUES ('x', 'x', 0.2, 0.2, NULL, NULL);

-- CHAR drops trailing spaces, VARCHAR keeps them
SELECT CONCAT('[', c, ']') AS char_val, CONCAT('[', v, ']') AS varchar_val
FROM t WHERE c LIKE 'ab%';

-- FLOAT is approximate, DECIMAL is exact
SELECT SUM(f) = 0.3 AS float_ok, SUM(d) = 0.3 AS decimal_ok FROM t;

-- Change the session time zone: TIMESTAMP shifts, DATETIME does not
SET time_zone = '+00:00';
SELECT dt, ts FROM t WHERE dt IS NOT NULL;
"""),
        title='Example: The Differences in Action'),
    warn('Never store money in FLOAT or DOUBLE, and avoid TIMESTAMP for dates that may go beyond 2038 (for example a loan maturity date). '
         'Store dates in DATE/DATETIME columns, not VARCHAR, or sorting and date arithmetic break.'),
    crossq(
        ('What does INT(11) mean?', 'Only a <em>display width</em> hint for ZEROFILL, not a size limit. INT is always 4 bytes. MySQL 8.0.17+ deprecates the width.'),
        ('What is the difference between VARCHAR and TEXT?', 'VARCHAR can have a default value and be fully indexed, and is stored inline. TEXT has no default (before 8.0.13), '
         'needs a prefix length to be indexed, and large values may be stored off-page.'),
        ('What is AUTO_INCREMENT?', 'A column attribute that generates the next integer for each new row, usually for surrogate primary keys. '
         '<code>LAST_INSERT_ID()</code> returns the value generated by your own session\'s last insert.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('What is the difference between DELETE, TRUNCATE and DROP?', 'DELETE vs TRUNCATE vs DROP', minutes=5, cards=[
    definition(
        defbox('<strong>DELETE</strong> removes selected rows (DML). <strong>TRUNCATE</strong> removes all rows by recreating '
               'the table (DDL). <strong>DROP</strong> removes the table itself: data, structure, indexes and privileges on it.'),
        tags('DELETE', 'TRUNCATE', 'DROP', 'DML', 'DDL', 'AUTO_INCREMENT'),
    ),
    comparison(
        table(['Aspect', 'DELETE', 'TRUNCATE', 'DROP'], [
            ['Type', 'DML', 'DDL', 'DDL'],
            ['WHERE clause', 'Yes', 'No (all rows)', 'No'],
            ['Rollback in InnoDB', 'Yes, inside a transaction', 'No (implicit commit)', 'No (implicit commit)'],
            ['Speed on big tables', 'Slow: row by row, logs each row', 'Fast: drops and recreates', 'Fast'],
            ['Triggers fire', 'Yes (DELETE triggers)', 'No', 'No'],
            ['AUTO_INCREMENT', 'Continues from the old value', 'Reset to 1', 'Gone with the table'],
            ['Table structure', 'Kept', 'Kept', 'Removed'],
            ['Child table with FK', 'Allowed (if rows not referenced)', 'Fails if referenced by a foreign key', 'Fails if referenced'],
        ]),
    ),
    example(
        sqlrun("""
CREATE TABLE logs (id INT AUTO_INCREMENT PRIMARY KEY, msg VARCHAR(20));
INSERT INTO logs (msg) VALUES ('a'), ('b'), ('c');

-- DELETE can be rolled back
START TRANSACTION;
DELETE FROM logs;
ROLLBACK;
SELECT COUNT(*) AS after_delete_rollback FROM logs;

-- DELETE keeps the counter, TRUNCATE resets it
DELETE FROM logs;
INSERT INTO logs (msg) VALUES ('d');
SELECT id AS id_after_delete FROM logs;

TRUNCATE TABLE logs;
INSERT INTO logs (msg) VALUES ('e');
SELECT id AS id_after_truncate FROM logs;

DROP TABLE logs;
SELECT COUNT(*) AS logs_tables_left FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'logs';
"""),
        title='Example'),
    crossq(
        ('Why is TRUNCATE faster than DELETE?', 'DELETE removes rows one by one, writing undo and binlog entries and updating every index for each row. '
         'TRUNCATE just drops and recreates the table, so the time does not depend on the row count.'),
        ('How do you delete millions of rows without locking the table for long?', 'Delete in batches, e.g. <code>DELETE FROM logs WHERE created_at &lt; \'2025-01-01\' LIMIT 10000;</code> '
         'in a loop, so each transaction is short. For a full purge of old data, partitioned tables let you <code>DROP PARTITION</code> instantly.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What is the logical order of execution of a SELECT query?', 'Order of Execution', minutes=6, cards=[
    definition(
        defbox('SQL is written in the order <code>SELECT → FROM → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT</code>, but it '
               'is <strong>logically evaluated</strong> as <code>FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT</code>.'),
        hl('This one fact explains many errors: why a SELECT alias cannot be used in WHERE, why aggregates are not allowed '
           'in WHERE, and why ORDER BY can use aliases.', 'Why interviewers ask'),
        tags('Logical Query Processing', 'WHERE', 'HAVING', 'Alias', 'ORDER BY'),
    ),
    query_order(),
    example(
        sqlrun("""
-- Works: ORDER BY runs after SELECT, so the alias exists
SELECT dept_id, AVG(salary) AS avg_sal
FROM employees
WHERE salary > 60000
GROUP BY dept_id
HAVING COUNT(*) >= 2
ORDER BY avg_sal DESC
LIMIT 1;

-- Fails: WHERE runs before SELECT, the alias does not exist yet
SELECT name, salary * 12 AS annual FROM employees WHERE annual > 1000000;
""", setup=EMP, expect_error=True),
        title='Example'),
    note('This is the <em>logical</em> order that defines the result. The optimizer may physically do things differently '
         '(for example, read rows already sorted from an index so no ORDER BY sort is needed), but the result must be the same.'),
    crossq(
        ('How would you filter on the alias then?', 'Repeat the expression (<code>WHERE salary * 12 &gt; 1000000</code>) or wrap the query in a derived table / CTE and filter outside.'),
        ('Can HAVING use a SELECT alias in MySQL?', 'Yes. MySQL allows aliases in GROUP BY and HAVING as an extension to standard SQL. Many other databases do not, so repeating the expression is more portable.'),
    ),
]),

# ------------------------------------------------------------------ 6
Q('What is the difference between WHERE and HAVING?', 'WHERE vs HAVING', minutes=5, cards=[
    definition(
        defbox('<strong>WHERE</strong> filters <strong>rows</strong> before grouping. <strong>HAVING</strong> filters '
               '<strong>groups</strong> after GROUP BY, so it can use aggregate functions such as <code>COUNT()</code> and <code>SUM()</code>.'),
        tags('WHERE', 'HAVING', 'GROUP BY', 'Aggregate'),
    ),
    comparison(
        table(['Aspect', 'WHERE', 'HAVING'], [
            ['Filters', 'Individual rows', 'Groups (aggregated rows)'],
            ['Runs', 'Before GROUP BY', 'After GROUP BY'],
            ['Aggregates allowed', 'No', 'Yes'],
            ['Can use indexes', 'Yes', 'Generally no (works on grouped results)'],
            ['Without GROUP BY', 'Normal use', 'Treats the whole result as one group'],
        ]),
    ),
    example(
        sqlrun("""
-- Departments with more than 2 employees hired from 2019 onwards
SELECT dept_id, COUNT(*) AS hired_after_2019
FROM employees
WHERE hire_date >= '2019-01-01'      -- row filter
GROUP BY dept_id
HAVING COUNT(*) > 2;                  -- group filter

-- Aggregate in WHERE is an error
SELECT dept_id FROM employees WHERE COUNT(*) > 2 GROUP BY dept_id;
""", setup=EMP, expect_error=True),
        title='Example'),
    interview(p('Put every condition that does not need an aggregate in <strong>WHERE</strong>. Filtering early means fewer rows '
                'to group, and WHERE can use an index. <code>HAVING dept_id = 10</code> works but is wasteful.')),
    crossq(
        ('Can you use HAVING without GROUP BY?', 'Yes: the whole table is one group. <code>SELECT COUNT(*) FROM employees HAVING COUNT(*) &gt; 5;</code> returns one row or nothing.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How are NULL values handled in MySQL?', 'NULL Handling', minutes=7, cards=[
    definition(
        defbox('<strong>NULL</strong> means "unknown" or "missing", not zero and not an empty string. Any comparison with NULL '
               'using <code>=</code>, <code>&lt;&gt;</code>, <code>&lt;</code> etc. gives <strong>NULL (unknown)</strong>, which WHERE treats as false.'),
        tags('NULL', 'IS NULL', 'COALESCE', 'IFNULL', 'NULLIF', '<=>', 'Three-valued Logic'),
    ),
    explanation(
        table(['Tool', 'Meaning', 'Example → result'], [
            ['IS NULL / IS NOT NULL', 'The only correct way to test for NULL', '<code>manager_id IS NULL</code>'],
            ['&lt;=&gt; (null-safe equal)', 'Like = but NULL &lt;=&gt; NULL is 1', '<code>NULL &lt;=&gt; NULL</code> → 1'],
            ['IFNULL(a, b)', 'b if a is NULL (MySQL)', '<code>IFNULL(NULL, 0)</code> → 0'],
            ['COALESCE(a, b, c…)', 'First non-NULL argument (standard SQL)', '<code>COALESCE(NULL, NULL, 5)</code> → 5'],
            ['NULLIF(a, b)', 'NULL if a = b, else a. Prevents divide-by-zero.', '<code>x / NULLIF(y, 0)</code>'],
        ]),
        p('<strong>Aggregates ignore NULLs</strong>: <code>COUNT(col)</code>, <code>SUM</code>, <code>AVG</code>, <code>MIN</code>, <code>MAX</code> skip them. '
          'Only <code>COUNT(*)</code> counts every row. In ORDER BY ASC, MySQL puts NULLs <strong>first</strong>.', True),
    ),
    example(
        sqlrun("""
SELECT NULL = NULL AS eq, NULL <=> NULL AS null_safe, NULL + 5 AS plus,
       COALESCE(NULL, 'x') AS coalesce_val, 10 / NULLIF(0, 0) AS safe_div;

-- Wrong: returns nothing.  Right: IS NULL
SELECT COUNT(*) AS wrong FROM employees WHERE dept_id = NULL;
SELECT name FROM employees WHERE dept_id IS NULL;

-- COUNT(*) counts rows, COUNT(col) skips NULLs
SELECT COUNT(*) AS all_rows, COUNT(dept_id) AS with_dept,
       COUNT(manager_id) AS with_manager
FROM employees;

-- Replace NULL for display
SELECT name, COALESCE(dept_id, 'Not assigned') AS dept
FROM employees WHERE emp_id IN (1, 10);
""", setup=EMP),
        title='Example'),
    warn('<code>NOT IN</code> with a subquery that returns even one NULL returns <strong>no rows</strong>. This classic trap is covered in the Joins section (anti-joins).'),
    crossq(
        ('What is the difference between IFNULL and COALESCE?', 'IFNULL takes exactly two arguments and is MySQL-specific. COALESCE takes any number and is standard SQL, so it is portable.'),
        ('Is an empty string the same as NULL in MySQL?', 'No. <code>\'\'</code> is a known, empty value; <code>\'\' IS NULL</code> is 0. (Oracle is the database that treats them the same.)'),
        ('Does a UNIQUE index allow multiple NULLs?', 'Yes, in InnoDB a UNIQUE column can hold many NULLs because NULL is not equal to NULL.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('How do you manage users and privileges in MySQL? Explain GRANT, REVOKE and roles', 'Users, GRANT & Roles', minutes=6, cards=[
    definition(
        defbox('A MySQL account is identified by <code>\'user\'@\'host\'</code>. <strong>GRANT</strong> gives privileges '
               '(SELECT, INSERT, UPDATE, CREATE …) at global, database, table or column level, and <strong>REVOKE</strong> '
               'takes them away. A <strong>role</strong> (MySQL 8) is a named set of privileges that can be granted to many users.'),
        tags('CREATE USER', 'GRANT', 'REVOKE', 'Roles', 'Least Privilege', 'DCL'),
    ),
    explanation(
        table(['Level', 'Syntax', 'Use'], [
            ['Global', '<code>ON *.*</code>', 'DBAs only'],
            ['Database', '<code>ON sales.*</code>', 'An application or team'],
            ['Table', '<code>ON sales.orders</code>', 'An ETL user that reads a few tables'],
            ['Column', '<code>GRANT SELECT (id, city) ON sales.customers</code>', 'Hide sensitive columns such as phone or PAN'],
        ]),
    ),
    example(
        sqlrun("""
DROP USER IF EXISTS 'etl_reader'@'%';
DROP ROLE IF EXISTS 'read_only';

-- Least privilege: a role that can only read this database
CREATE ROLE 'read_only';
GRANT SELECT ON sales.* TO 'read_only';

CREATE USER 'etl_reader'@'%' IDENTIFIED BY 'Str0ng#Pass';
GRANT 'read_only' TO 'etl_reader'@'%';
SET DEFAULT ROLE 'read_only' TO 'etl_reader'@'%';

-- Extraction for CDC tools also needs replication privileges
GRANT REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'etl_reader'@'%';

SHOW GRANTS FOR 'etl_reader'@'%';

REVOKE REPLICATION SLAVE, REPLICATION CLIENT ON *.* FROM 'etl_reader'@'%';
DROP USER 'etl_reader'@'%';
DROP ROLE 'read_only';
"""),
        title='Example: A Read-only ETL User'),
    real_world(p('Give each pipeline its own user with only <code>SELECT</code> on the tables it extracts, and connect '
                 'it to a <strong>read replica</strong>, not the primary, so heavy extract queries never slow the application.')),
    crossq(
        ('What does \'%\' mean in \'user\'@\'%\'?', 'Any host. <code>\'user\'@\'10.0.%\'</code> limits logins to that subnet, and <code>\'user\'@\'localhost\'</code> to the same machine.'),
        ('Do you need FLUSH PRIVILEGES after GRANT?', 'No. GRANT, REVOKE and CREATE USER reload privileges automatically. FLUSH PRIVILEGES is only needed if the grant tables were edited directly with INSERT/UPDATE.'),
    ),
]),

])
