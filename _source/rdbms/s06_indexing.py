from build import *
from rdbms.anims import *

SECTION = dict(level='advanced', title='Indexing', questions=[

# ------------------------------------------------------------------ 39
Q('What is an Index and how does it work?', 'Index Basics', minutes=7, cards=[
    definition(
        defbox('An <strong>index</strong> is a separate data structure that stores the values of one or more columns in '
               '<strong>sorted order</strong> together with pointers to the matching rows. It lets the DBMS find rows '
               'without scanning the whole table.'),
        hl('Like the index at the back of a textbook: to find "deadlock" you look it up alphabetically and jump to page 214, instead of reading every page.', 'Analogy'),
        tags('Index', 'B+ Tree', 'Full Table Scan', 'Index Seek', 'Selectivity'),
    ),
    explanation(
        p('Most RDBMS indexes are <strong>B+ trees</strong>: a balanced tree where internal nodes hold keys for '
          'navigation and leaf nodes hold the sorted keys plus row pointers. Leaves are linked, so range scans are fast.'),
        table(['Without index', 'With index'], [
            ['Full table scan — read every row: O(n)', 'Tree lookup: O(log n) — 3–4 page reads even for millions of rows'],
            ['1 crore rows → 1 crore comparisons', '1 crore rows → about 4 levels of the tree'],
        ]),
        p('<strong>Indexes speed up:</strong> WHERE filters, JOIN conditions, ORDER BY / GROUP BY (data already sorted), '
          'MIN/MAX, and uniqueness checks. <strong>They cost:</strong> disk space and slower INSERT/UPDATE/DELETE, '
          'because every index must be updated too.', True),
    ),
    btree_search(),
    example(
        code("""
CREATE INDEX idx_students_email ON students(email);

-- Uses the index (index lookup)
SELECT * FROM students WHERE email = 'asha@mail.com';

-- See whether an index is used
EXPLAIN SELECT * FROM students WHERE email = 'asha@mail.com';

-- List and drop indexes (MySQL)
SHOW INDEX FROM students;
DROP INDEX idx_students_email ON students;
"""),
        title='Example'),
    crossq(
        ('What is selectivity (cardinality) of an index?',
         'The ratio of distinct values to total rows. An index on <code>email</code> (all distinct) is highly selective '
         'and very useful; an index on <code>gender</code> (2–3 values) is low-selectivity and the optimizer usually ignores it.'),
        ('Why B+ tree and not a binary search tree?',
         'A B+ tree node holds hundreds of keys (one disk page), so the tree is very shallow — few disk reads. A binary '
         'tree would be ~25 levels deep for 1 crore rows, i.e. 25 disk reads.'),
        ('Are primary keys indexed automatically?',
         'Yes, and so are UNIQUE constraints. In MySQL InnoDB foreign key columns are also indexed automatically if no suitable index exists.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('What is the difference between a Clustered and a Non-clustered index?', 'Clustered vs Non-clustered', minutes=7, cards=[
    definition(
        defbox('A <strong>clustered index</strong> determines the <strong>physical order</strong> in which table rows are '
               'stored. The leaf level of the index <em>is</em> the table data. Hence a table can have only '
               '<strong>one</strong> clustered index.',
               'A <strong>non-clustered (secondary) index</strong> is a separate structure: its leaves hold the indexed '
               'value plus a <strong>pointer</strong> to the row. A table can have many non-clustered indexes.'),
        hl('Clustered = a telephone directory (the data itself is sorted by name). Non-clustered = the index at the back of a book (sorted list that points to pages).', 'Analogy'),
        tags('Clustered Index', 'Non-clustered Index', 'Secondary Index', 'Bookmark Lookup', 'InnoDB'),
    ),
    secondary_lookup(),
    comparison(
        table(['Aspect', 'Clustered', 'Non-clustered'], [
            ['Number per table', 'One', 'Many'],
            ['Leaf level contains', 'Full data rows', 'Key + pointer (row locator)'],
            ['Physical row order', 'Sorted by the index key', 'Not affected'],
            ['Extra storage', 'None (it is the table)', 'Yes, separate structure'],
            ['Lookup cost', 'One tree traversal', 'Index traversal + lookup into table'],
            ['Range queries on key', 'Very fast (rows are contiguous)', 'Slower if many lookups needed'],
            ['Default in MySQL InnoDB', 'The PRIMARY KEY', 'Every other index'],
        ]),
    ),
    explanation(
        p('<strong>In MySQL InnoDB</strong> the table is always clustered on the primary key. A secondary index stores '
          'the indexed column(s) <strong>plus the primary key value</strong> as the row pointer. So a lookup through a '
          'secondary index is: find PK in secondary index → search the clustered index by PK → get the row.'),
        p('Consequences for design:', True),
        ul('Keep the primary key <strong>short</strong> — it is copied into every secondary index.',
           'Use an <strong>increasing</strong> primary key (AUTO_INCREMENT) so new rows append at the end instead of '
           'causing page splits in the middle.',
           'If a query needs only columns in the secondary index + PK, the second lookup is skipped (covering index).'),
        title='How MySQL InnoDB Does It'),
    crossq(
        ('Can a clustered index be on a non-primary-key column?',
         'In SQL Server, yes — you can choose any column. In MySQL InnoDB, no — the clustered index is always the primary key (or the first UNIQUE NOT NULL index, or a hidden row id).'),
        ('Is a heap table the same as a table with no clustered index?',
         'Yes. In SQL Server/PostgreSQL a table without a clustered index is a heap — rows are stored in no particular order. PostgreSQL tables are always heaps; its CLUSTER command sorts once but does not maintain the order.'),
    ),
]),

# ------------------------------------------------------------------ 41
Q('What is the difference between B-Tree and Hash indexes?', 'B-Tree vs Hash Index', minutes=5, cards=[
    definition(
        defbox('A <strong>B-Tree (B+ tree) index</strong> keeps keys sorted in a balanced tree. It supports equality, '
               'range, prefix and sorting operations.',
               'A <strong>hash index</strong> applies a hash function to the key and stores it in a hash table. It is '
               'extremely fast for exact matches (<code>=</code>) but cannot do ranges or sorting.'),
        tags('B-Tree', 'Hash Index', 'Range Query', 'Equality Lookup', 'Adaptive Hash Index'),
    ),
    comparison(
        table(['Operation', 'B-Tree', 'Hash'], [
            ['= (equality)', '✅ O(log n)', '✅ O(1) on average'],
            ['&lt;, &gt;, BETWEEN', '✅', '❌'],
            ['LIKE \'abc%\' (prefix)', '✅', '❌'],
            ['ORDER BY on key', '✅ (already sorted)', '❌'],
            ['MIN / MAX', '✅', '❌'],
            ['Leftmost prefix of composite key', '✅', '❌ (needs full key)'],
            ['Typical availability', 'Default in almost every RDBMS', 'MySQL MEMORY engine, PostgreSQL HASH, InnoDB adaptive hash (internal)'],
        ]),
    ),
    example(
        code("""
-- MEMORY engine supports explicit hash indexes
CREATE TABLE session_cache (
    session_id CHAR(32),
    user_id    INT,
    INDEX idx_session USING HASH (session_id)
) ENGINE = MEMORY;

-- PostgreSQL
CREATE INDEX idx_sessions_hash ON sessions USING HASH (session_id);
"""),
        note('InnoDB only creates B-Tree indexes on disk. It can automatically build an in-memory '
             '<strong>Adaptive Hash Index</strong> on hot B-Tree pages (<code>innodb_adaptive_hash_index</code>).'),
        title='Example'),
    crossq(
        ('Which other index types exist?',
         '<strong>Full-text</strong> (word search), <strong>spatial / R-tree</strong> (geo data), <strong>GIN/GiST</strong> '
         '(PostgreSQL arrays, JSONB, full text), <strong>bitmap</strong> (Oracle, data warehouses, low-cardinality columns), '
         'and <strong>BRIN</strong> (PostgreSQL, very large naturally-ordered tables).'),
        ('When is a bitmap index a good choice?',
         'For low-cardinality columns (gender, status, region) in read-mostly warehouses — bitmaps combine quickly with AND/OR. They are bad for OLTP because updates lock large ranges.'),
    ),
]),

# ------------------------------------------------------------------ 42
Q('When should you NOT create an index? When do indexes hurt?', 'When Indexes Hurt', minutes=6, cards=[
    definition(
        defbox('Indexes speed up reads but are not free. Each index uses disk and memory, and must be maintained on '
               'every INSERT, UPDATE and DELETE. Too many or poorly chosen indexes make a database slower.'),
        tags('Over-indexing', 'Write Overhead', 'Low Selectivity', 'Unused Index', 'Index Maintenance'),
    ),
    explanation(
        table(['Situation', 'Why an index does not help or hurts'], [
            ['Small tables (a few hundred rows)', 'A full scan is as fast as an index lookup'],
            ['Low-selectivity columns (gender, yes/no flags)', 'The optimizer would read a large share of the table anyway'],
            ['Write-heavy tables (logs, event streams)', 'Every insert updates every index → slower ingestion'],
            ['Columns frequently updated', 'Each update rewrites the index entry'],
            ['Columns never used in WHERE / JOIN / ORDER BY', 'Pure overhead'],
            ['Duplicate / redundant indexes', '(a) and (a, b) — the first is usually redundant'],
            ['Bulk loads', 'Faster to drop/disable secondary indexes, load, then rebuild'],
        ]),
        p('<strong>Queries that cannot use an index on the column</strong> (very common interview follow-up):', True),
        code("""
-- Function on the column
WHERE YEAR(order_date) = 2026            -- ❌
WHERE order_date >= '2026-01-01'
  AND order_date <  '2027-01-01'         -- ✅

-- Leading wildcard
WHERE name LIKE '%kumar'                 -- ❌
WHERE name LIKE 'kumar%'                 -- ✅

-- Implicit type conversion (phone is VARCHAR)
WHERE phone = 9820011111                 -- ❌ number compared to string
WHERE phone = '9820011111'               -- ✅

-- Arithmetic on the column
WHERE salary * 12 > 1200000              -- ❌
WHERE salary > 100000                    -- ✅

-- OR across different columns (often)
WHERE email = 'x' OR phone = 'y'         -- may scan; consider UNION
""", 'Index-killing patterns'),
    ),
    crossq(
        ('How do you find unused indexes in MySQL?',
         'Query <code>sys.schema_unused_indexes</code> (MySQL 5.7+ with performance_schema), or check '
         '<code>performance_schema.table_io_waits_summary_by_index_usage</code>. In PostgreSQL use <code>pg_stat_user_indexes</code>.'),
        ('How many indexes per table is too many?',
         'There is no fixed number. OLTP tables typically have 3–6 well-chosen indexes. Each new index should be justified by a frequent, important query.'),
    ),
]),

# ------------------------------------------------------------------ 43
Q('What is a Composite Index? Explain the leftmost-prefix rule', 'Composite Index & Leftmost Prefix', minutes=7, cards=[
    definition(
        defbox('A <strong>composite (multi-column) index</strong> is one index built on two or more columns, e.g. '
               '<code>(dept_id, city, name)</code>. Entries are sorted by the first column, then by the second within it, and so on.',
               'The <strong>leftmost-prefix rule</strong>: the index can be used only for queries that filter on a '
               '<strong>left-to-right prefix</strong> of its columns — (dept_id), (dept_id, city) or (dept_id, city, name).'),
        hl('A phone directory sorted by (surname, first name) helps you find "Sharma" or "Sharma, Rohit", but not "everyone called Rohit".', 'Analogy'),
        tags('Composite Index', 'Leftmost Prefix', 'Column Order', 'Range Condition'),
    ),
    example(
        code("""
CREATE INDEX idx_dept_city_name ON students(dept_id, city, name);
"""),
        table(['Query condition', 'Index used?', 'Why'], [
            ['WHERE dept_id = 1', '✅ Yes', 'Leftmost column'],
            ['WHERE dept_id = 1 AND city = \'Pune\'', '✅ Yes', 'Prefix (dept_id, city)'],
            ['WHERE dept_id = 1 AND city = \'Pune\' AND name = \'Asha\'', '✅ Yes', 'Full index'],
            ['WHERE city = \'Pune\' AND dept_id = 1', '✅ Yes', 'Order in WHERE does not matter — the optimizer reorders'],
            ['WHERE city = \'Pune\'', '❌ No (normally)', 'Skips the leftmost column'],
            ['WHERE name = \'Asha\'', '❌ No', 'Not a prefix'],
            ['WHERE dept_id = 1 AND name = \'Asha\'', '⚠️ Partly', 'Only dept_id part used for seeking; name filtered afterwards'],
            ['WHERE dept_id &gt; 1 AND city = \'Pune\'', '⚠️ Partly', 'A range on a column stops seeking on the columns after it'],
        ]),
        title='Example: Which Queries Use the Index?'),
    interview(
        hl('Put columns used with <strong>equality (=)</strong> first, then the column used for a <strong>range</strong> '
           'or <strong>ORDER BY</strong>. Among equality columns, the one used in the most queries goes first.', 'Column-order rule'),
        p('MySQL 8.0.13+ has <strong>skip scan</strong>, which can sometimes use an index even when the first column is '
          'missing (if it has few distinct values) — but do not design around it.'),
    ),
    crossq(
        ('Is an index on (a, b) the same as separate indexes on a and b?',
         'No. The composite index serves <code>a = ? AND b = ?</code> in one seek. Two single indexes need index merge or '
         'pick just one. However, (a, b) also covers queries on a alone, making a separate index on a redundant.'),
        ('Can a composite index help ORDER BY?',
         'Yes: with <code>INDEX(dept_id, created_at)</code>, <code>WHERE dept_id = 1 ORDER BY created_at</code> reads rows already sorted — no filesort.'),
    ),
]),

# ------------------------------------------------------------------ 44
Q('What is a Covering Index?', 'Covering Index', minutes=5, cards=[
    definition(
        defbox('A <strong>covering index</strong> is an index that contains <strong>all the columns a query needs</strong> '
               '— in SELECT, WHERE, JOIN and ORDER BY. The DBMS answers the query from the index alone, without visiting '
               'the table rows ("index-only scan").'),
        tags('Covering Index', 'Index-only Scan', 'Using index', 'INCLUDE columns'),
    ),
    example(
        code("""
CREATE INDEX idx_dept_name ON students(dept_id, name);

-- Covered: everything needed is in the index (+ PK in InnoDB)
EXPLAIN SELECT student_id, name FROM students WHERE dept_id = 1;
--   Extra: Using index        ← index-only, no table lookup

-- Not covered: email is not in the index → table lookup per row
EXPLAIN SELECT name, email FROM students WHERE dept_id = 1;
--   Extra: (blank) / Using index condition

-- SQL Server / PostgreSQL 11+: add non-key columns to the leaf level
CREATE INDEX idx_dept_incl ON students(dept_id) INCLUDE (name, email);
"""),
        note('In InnoDB every secondary index already contains the primary key, so <code>student_id</code> above is "free".'),
        title='Example'),
    crossq(
        ('Why is a covering index faster?',
         'It avoids the second lookup into the clustered index / heap for every matching row — often the most expensive part. The index is also smaller than the table, so more of it fits in memory.'),
        ('What is the downside?',
         'Wider indexes take more space and make writes slower. Build covering indexes only for frequent, performance-critical queries.'),
        ('Why is SELECT * bad for performance?',
         'It prevents covering indexes, transfers unnecessary data and breaks when columns are added. Select only the columns you need.'),
    ),
]),

])
