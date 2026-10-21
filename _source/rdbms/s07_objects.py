from build import *
from rdbms.anims import *

SECTION = dict(level='advanced', title='Query Processing & DB Objects', questions=[

# ------------------------------------------------------------------ 45
Q('What is Relational Algebra? Explain its basic operations', 'Relational Algebra', minutes=8, cards=[
    definition(
        defbox('<strong>Relational algebra</strong> is a <strong>procedural</strong> query language that defines '
               'operations on relations (tables) which produce new relations. It is the theoretical foundation of SQL: '
               'the query optimizer converts SQL into a relational algebra tree before executing it.'),
        tags('Relational Algebra', 'Selection σ', 'Projection π', 'Join ⋈', 'Union', 'Cartesian Product'),
    ),
    explanation(
        table(['Operation', 'Symbol', 'Meaning', 'SQL equivalent'], [
            ['Selection', 'σ', 'Choose rows that satisfy a condition', 'WHERE'],
            ['Projection', 'π', 'Choose columns (removes duplicates)', 'SELECT DISTINCT col…'],
            ['Union', '∪', 'Rows in either relation', 'UNION'],
            ['Set difference', '−', 'Rows in R but not in S', 'EXCEPT / NOT EXISTS'],
            ['Cartesian product', '×', 'Every row of R with every row of S', 'CROSS JOIN'],
            ['Rename', 'ρ', 'Rename a relation or attribute', 'AS'],
            ['Intersection', '∩', 'Rows in both (derived)', 'INTERSECT'],
            ['Natural join', '⋈', 'Product + selection on equal common attributes', 'NATURAL JOIN / JOIN … USING'],
            ['Theta join', '⋈θ', 'Join with any condition', 'JOIN … ON condition'],
            ['Division', '÷', 'Rows related to <em>all</em> rows of another relation', 'NOT EXISTS … NOT EXISTS'],
        ]),
        p('The six <strong>fundamental</strong> operations are σ, π, ∪, −, × and ρ. All others (∩, joins, ÷) can be expressed using them.', True),
    ),
    example(
        code("""
Students(student_id, name, dept_id, cgpa)
Departments(dept_id, dept_name)

1) Names of students with CGPA above 8
   π name ( σ cgpa > 8 (Students) )
   SQL: SELECT DISTINCT name FROM Students WHERE cgpa > 8;

2) Student names with their department names
   π name, dept_name ( Students ⋈ Departments )
   SQL: SELECT s.name, d.dept_name FROM Students s JOIN Departments d USING (dept_id);

3) Students who enrolled in ALL courses (division)
   π student_id, course_id (Enrollments) ÷ π course_id (Courses)
   SQL:
   SELECT s.student_id FROM Students s
   WHERE NOT EXISTS (
       SELECT * FROM Courses c
       WHERE NOT EXISTS (
           SELECT * FROM Enrollments e
           WHERE e.student_id = s.student_id AND e.course_id = c.course_id));
""", 'Relational algebra ↔ SQL', 'fa-square-root-variable'),
        title='Example'),
    crossq(
        ('What is the difference between relational algebra and relational calculus?',
         'Algebra is <strong>procedural</strong> — it says which operations to apply in which order. Calculus (tuple and '
         'domain) is <strong>declarative</strong> — it describes the result. SQL is based mainly on tuple relational calculus, '
         'and is executed internally as algebra. Both have the same expressive power (Codd\'s theorem).'),
        ('Why does the optimizer care about relational algebra?',
         'Algebraic rules let it rewrite queries into cheaper equivalent forms — e.g. pushing selections (σ) below joins '
         'so fewer rows are joined, or reordering joins.'),
    ),
]),

# ------------------------------------------------------------------ 46
Q('How is a SQL query processed and executed internally?', 'Query Processing', minutes=8, cards=[
    definition(
        defbox('When a SQL statement is submitted, the DBMS passes it through a pipeline: <strong>parse → rewrite → '
               'optimize → execute</strong>. The optimizer chooses the cheapest of many possible execution plans using '
               'statistics about the data.'),
        tags('Parser', 'Query Optimizer', 'Execution Plan', 'Cost-based Optimizer', 'Statistics', 'EXPLAIN'),
    ),
    query_pipeline(),
    explanation(
        table(['Stage', 'What happens'], [
            ['1. Parsing', 'Checks syntax, builds a parse tree; checks that tables/columns exist and the user has privileges'],
            ['2. Rewriting', 'Expands views, flattens subqueries into joins, simplifies expressions (e.g. removes 1 = 1)'],
            ['3. Optimization', 'Generates candidate plans (join order, join algorithm, which index) and estimates the cost of each using statistics; picks the cheapest'],
            ['4. Execution', 'Runs the plan: the storage engine reads pages (from buffer pool or disk), applies filters, joins, sorts and returns rows'],
        ]),
        p('<strong>Join algorithms the optimizer chooses between:</strong> nested-loop join (good with an index on the '
          'inner table), hash join (large unsorted inputs — MySQL 8.0.18+), and sort-merge join (inputs already sorted).', True),
        p('<strong>Logical order of SQL clauses</strong> (how the result is defined, regardless of how you write it): '
          '<code>FROM/JOIN → WHERE → GROUP BY → HAVING → SELECT → DISTINCT → ORDER BY → LIMIT</code>. '
          'This is why a column alias from SELECT cannot be used in WHERE.'),
    ),
    example(
        code("""
EXPLAIN FORMAT=TREE
SELECT s.name, d.dept_name
FROM students s
JOIN departments d ON d.dept_id = s.dept_id
WHERE s.cgpa > 8;

-- EXPLAIN ANALYZE actually runs the query and shows real row counts and timing (MySQL 8.0.18+)
EXPLAIN ANALYZE
SELECT s.name, d.dept_name
FROM students s
JOIN departments d ON d.dept_id = s.dept_id
WHERE s.cgpa > 8;

-- Refresh statistics used by the optimizer
ANALYZE TABLE students;
"""),
        title='Example: Seeing the Plan'),
    crossq(
        ('Rule-based vs cost-based optimizer?',
         'A rule-based optimizer follows fixed heuristics (e.g. "always use an index if available"). A cost-based optimizer '
         'estimates I/O and CPU for each plan using statistics. All modern RDBMSs are cost-based.'),
        ('Why can the same query suddenly become slow?',
         'Stale statistics, data growth changing selectivity, a different parameter value (parameter sniffing), or a '
         'dropped/unused index. Check the plan with EXPLAIN and refresh stats with ANALYZE TABLE.'),
    ),
]),

# ------------------------------------------------------------------ 47
Q('What is a View? What is a Materialized View?', 'Views & Materialized Views', minutes=7, cards=[
    definition(
        defbox('A <strong>view</strong> is a <strong>virtual table</strong> defined by a stored SELECT query. It stores no '
               'data of its own; every time you query the view, the underlying query runs against the base tables.',
               'A <strong>materialized view</strong> stores the <strong>result</strong> of the query physically, like a '
               'table. It is fast to read but must be <strong>refreshed</strong> to reflect changes in the base tables.'),
        tags('View', 'Virtual Table', 'Materialized View', 'Refresh', 'Updatable View', 'Security'),
    ),
    comparison(
        table(['Aspect', 'View', 'Materialized view'], [
            ['Stores data', 'No — only the query', 'Yes — the result set'],
            ['Freshness', 'Always current', 'As of the last refresh'],
            ['Read speed', 'Same as running the query', 'Fast (pre-computed)'],
            ['Storage', 'None', 'Like a table'],
            ['Indexes', 'Not on the view itself (MySQL)', 'Can be indexed'],
            ['Support', 'All RDBMS', 'Oracle, PostgreSQL, Snowflake, BigQuery; <strong>not native in MySQL</strong>'],
        ]),
    ),
    example(
        code("""
-- Simple view: hide sensitive columns, simplify a join
CREATE VIEW v_student_dept AS
SELECT s.student_id, s.name, d.dept_name
FROM students s
JOIN departments d ON d.dept_id = s.dept_id;

SELECT * FROM v_student_dept WHERE dept_name = 'Big Data Analytics';

-- Give a user access only to the view, not the base table
GRANT SELECT ON college_db.v_student_dept TO 'placement'@'%';

-- Updatable view with protection against "escaping" rows
CREATE VIEW v_bda_students AS
SELECT * FROM students WHERE dept_id = 1
WITH CHECK OPTION;     -- UPDATE/INSERT through the view must keep dept_id = 1

-- PostgreSQL materialized view
CREATE MATERIALIZED VIEW mv_dept_stats AS
SELECT dept_id, COUNT(*) AS students, AVG(cgpa) AS avg_cgpa
FROM students GROUP BY dept_id;

REFRESH MATERIALIZED VIEW mv_dept_stats;
"""),
        note('In MySQL you emulate a materialized view with a summary table plus a scheduled EVENT or trigger that refreshes it.'),
        title='Example'),
    crossq(
        ('When is a view updatable?',
         'Generally when it maps to one base table without DISTINCT, GROUP BY, HAVING, aggregate functions, UNION, or '
         'subqueries in the SELECT list — so each view row corresponds to exactly one base row.'),
        ('Do views improve performance?',
         'Ordinary views do not — they are just saved queries (MySQL may merge them into the outer query). Their value is '
         'simplicity, reuse and security. Materialized views do improve read performance.'),
        ('What happens to a view if a base table column is dropped?',
         'The view becomes invalid and errors when queried. In MySQL, <code>CHECK TABLE view_name</code> reports it.'),
    ),
]),

# ------------------------------------------------------------------ 48
Q('What is the difference between Stored Procedures, Functions and Triggers?', 'Procedures vs Functions vs Triggers', minutes=8, cards=[
    definition(
        defbox('All three are named blocks of SQL/procedural code stored in the database:',
               '<strong>Stored procedure</strong> — called explicitly with <code>CALL</code>; can run any SQL, perform '
               'transactions and return zero or many result sets / OUT parameters.',
               '<strong>Function (UDF)</strong> — returns exactly <strong>one value</strong>; used inside SQL expressions '
               'like a built-in function.',
               '<strong>Trigger</strong> — not called by anyone; fires <strong>automatically</strong> BEFORE or AFTER an '
               'INSERT, UPDATE or DELETE on a table.'),
        tags('Stored Procedure', 'Function', 'Trigger', 'PL/SQL', 'CALL', 'BEFORE/AFTER'),
    ),
    comparison(
        table(['Aspect', 'Procedure', 'Function', 'Trigger'], [
            ['Invoked by', '<code>CALL proc()</code>', 'Inside SQL: <code>SELECT fn(x)</code>', 'Automatically on DML event'],
            ['Returns', '0..n result sets, OUT params', 'Exactly one value', 'Nothing'],
            ['Parameters', 'IN, OUT, INOUT', 'IN only', 'None (uses NEW / OLD rows)'],
            ['Used in SELECT/WHERE', 'No', 'Yes', 'No'],
            ['Transactions (COMMIT)', 'Allowed', 'Not allowed', 'Not allowed'],
            ['Typical use', 'Business process, batch jobs', 'Reusable calculation', 'Audit, validation, derived columns'],
        ]),
    ),
    example(
        code("""
DELIMITER //

-- Procedure: enroll a student and update the course count
CREATE PROCEDURE enroll_student(IN p_student INT, IN p_course INT)
BEGIN
    INSERT INTO enrollments(student_id, course_id, enrolled_on)
    VALUES (p_student, p_course, CURDATE());
    UPDATE courses SET enrolled_count = enrolled_count + 1 WHERE course_id = p_course;
END //

-- Function: grade from marks
CREATE FUNCTION grade_of(p_marks INT) RETURNS CHAR(1) DETERMINISTIC
BEGIN
    RETURN CASE WHEN p_marks >= 85 THEN 'A'
                WHEN p_marks >= 70 THEN 'B'
                WHEN p_marks >= 50 THEN 'C'
                ELSE 'F' END;
END //

-- Trigger: audit every fee change
CREATE TRIGGER trg_fee_audit
AFTER UPDATE ON courses
FOR EACH ROW
BEGIN
    IF OLD.fee <> NEW.fee THEN
        INSERT INTO fee_audit(course_id, old_fee, new_fee, changed_at)
        VALUES (OLD.course_id, OLD.fee, NEW.fee, NOW());
    END IF;
END //

DELIMITER ;

CALL enroll_student(101, 3);
SELECT name, marks, grade_of(marks) AS grade FROM exam_results;
"""),
        title='Example: One of Each (MySQL)'),
    crossq(
        ('Advantages and disadvantages of stored procedures?',
         '<strong>Pros:</strong> fewer network round-trips, logic close to data, reuse, permission control (grant EXECUTE '
         'without table access). <strong>Cons:</strong> harder to version-control, test and debug; vendor-specific syntax; business logic split between app and DB.'),
        ('Why can triggers be dangerous?',
         'They run invisibly — a simple UPDATE may cause cascades of hidden work, slow bulk loads, and make debugging hard. Use them sparingly, mainly for auditing.'),
        ('What are NEW and OLD in a trigger?',
         '<code>NEW</code> is the row after the change (INSERT, UPDATE); <code>OLD</code> is the row before (UPDATE, DELETE). '
         'In a BEFORE trigger you can modify <code>NEW</code> to change what gets stored.'),
    ),
]),

])
