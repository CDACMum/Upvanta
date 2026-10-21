from build import *

SECTION = dict(level='beginner', title='Foundations', questions=[

# ------------------------------------------------------------------ 1
Q('What is a Database and a DBMS?', 'Database & DBMS', minutes=5, cards=[
    definition(
        defbox('A <strong>database</strong> is an organised collection of related data stored so that it can be '
               'easily accessed, managed and updated.',
               'A <strong>Database Management System (DBMS)</strong> is the software that sits between users/applications '
               'and the stored data. It lets you define, create, query, update and administer the database while '
               'handling security, concurrency, backup and recovery for you.'),
        hl('The database is the <em>data</em>; the DBMS is the <em>software that manages</em> the data. '
           'MySQL, PostgreSQL, Oracle and SQL Server are DBMS products — the databases are what you create inside them.',
           'One-line answer'),
        tags('Database', 'DBMS', 'Data Management', 'Data Independence', 'Concurrency', 'Recovery'),
    ),
    explanation(
        p('A DBMS takes care of everything an application would otherwise have to build by itself:'),
        table(['Function', 'What it means'], [
            ['Data definition', 'Create and change structures — tables, columns, data types, constraints'],
            ['Data manipulation', 'Insert, update, delete and retrieve data through a query language'],
            ['Integrity', 'Enforce rules such as "age cannot be negative" or "every order must have a customer"'],
            ['Security', 'Users, roles and permissions — who can read or change what'],
            ['Concurrency control', 'Many users can work at once without corrupting each other\'s changes'],
            ['Backup &amp; recovery', 'Restore a consistent state after a crash or failure'],
            ['Data independence', 'Applications are shielded from how and where data is physically stored'],
        ]),
        p('<strong>Types of DBMS:</strong>'),
        ul('<strong>Hierarchical</strong> — tree structure, parent → child (IBM IMS). Historic.',
           '<strong>Network</strong> — graph structure, records with many parents (IDMS). Historic.',
           '<strong>Relational (RDBMS)</strong> — data in tables linked by keys (MySQL, PostgreSQL, Oracle). Most widely used.',
           '<strong>Object-oriented</strong> — stores objects as used in OOP languages (db4o).',
           '<strong>NoSQL</strong> — document, key-value, column-family and graph stores (MongoDB, Redis, Cassandra, Neo4j).'),
    ),
    real_world(
        scenario('College admission system',
                 p('Without a DBMS, each department keeps its own Excel sheet of students. The accounts office has '
                   'a student\'s old phone number, the exam cell has the new one, and two clerks editing the same '
                   'file overwrite each other\'s work.') +
                 p('With a DBMS, there is one <strong>students</strong> table that every department reads from. '
                   'Access is controlled by role, simultaneous updates are handled safely, and a nightly backup '
                   'protects the data.', True)),
    ),
    crossq(
        ('Is Excel a DBMS?',
         'No. Excel is a spreadsheet. It stores data in rows and columns but does not enforce data types or '
         'relationships, does not support safe multi-user concurrent updates, has no transaction or recovery '
         'mechanism, and does not scale to millions of rows. It is fine for analysis, not for managing shared data.'),
        ('Is MySQL a database or a DBMS?',
         'MySQL is a <strong>DBMS</strong> (more precisely an RDBMS). Inside one MySQL server you can create many '
         'databases, e.g. <code>college_db</code> and <code>library_db</code>.'),
        ('What is metadata?',
         '"Data about data" — table names, column names, data types, constraints, indexes and users. The DBMS stores '
         'it in the <strong>data dictionary / system catalog</strong> (in MySQL: <code>information_schema</code>).'),
    ),
]),

# ------------------------------------------------------------------ 2
Q('What is an RDBMS? How is it different from a DBMS?', 'RDBMS vs DBMS', minutes=7, cards=[
    definition(
        defbox('An <strong>RDBMS (Relational Database Management System)</strong> is a DBMS based on the '
               '<strong>relational model</strong> proposed by E. F. Codd in 1970. Data is stored in '
               '<strong>tables (relations)</strong>, and tables are linked to each other through '
               '<strong>keys</strong> — primary keys and foreign keys.',
               'Every RDBMS is a DBMS, but not every DBMS is relational.'),
        tags('RDBMS', 'Relational Model', 'E. F. Codd', 'Tables', 'Primary Key', 'Foreign Key', 'SQL'),
    ),
    comparison(
        table(['Aspect', 'DBMS (general)', 'RDBMS'], [
            ['Data storage', 'Files, hierarchies, graphs or tables', 'Always tables of rows and columns'],
            ['Relationships', 'Not necessarily enforced', 'Enforced through primary and foreign keys'],
            ['Normalization', 'Not applicable / not required', 'Supported to remove redundancy'],
            ['Integrity constraints', 'Limited', 'PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK, NOT NULL'],
            ['Transactions (ACID)', 'May not be supported', 'Fully supported'],
            ['Query language', 'Varies by product', 'SQL (standard)'],
            ['Multi-user access', 'Often limited', 'Designed for many concurrent users'],
            ['Examples', 'File systems, IMS, XML stores', 'MySQL, PostgreSQL, Oracle, SQL Server, DB2'],
        ], 'DBMS vs RDBMS — the classic interview comparison'),
    ),
    example(
        p('Two related tables in a college database. <code>dept_id</code> in <strong>students</strong> refers to '
          '<code>dept_id</code> in <strong>departments</strong>:'),
        code("""
CREATE TABLE departments (
    dept_id    INT PRIMARY KEY,
    dept_name  VARCHAR(50) NOT NULL
);

CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) UNIQUE,
    dept_id    INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO departments VALUES (1, 'Big Data Analytics'), (2, 'Artificial Intelligence');
INSERT INTO students VALUES (101, 'Asha',  'asha@mail.com',  1),
                            (102, 'Rohit', 'rohit@mail.com', 2);

-- The relationship lets us combine the tables
SELECT s.name, d.dept_name
FROM students s
JOIN departments d ON s.dept_id = d.dept_id;
""", 'Defining related tables'),
        output("""
+-------+-------------------------+
| name  | dept_name               |
+-------+-------------------------+
| Asha  | Big Data Analytics      |
| Rohit | Artificial Intelligence |
+-------+-------------------------+
"""),
        note('Trying to insert a student with <code>dept_id = 9</code> fails, because department 9 does not exist. '
             'The RDBMS enforces the relationship for you — this is <strong>referential integrity</strong>.'),
        title='Example: Relationship in Action'),
    visual(svg("""
<svg width="760" height="300" viewBox="0 0 760 300" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="300" fill="#1e293b"/>
  <text x="380" y="30" font-size="18" fill="#0ea5e9" text-anchor="middle" font-weight="bold">Tables linked by keys</text>
  <!-- departments -->
  <rect x="30" y="60" width="300" height="36" fill="#0ea5e9" rx="6"/>
  <text x="180" y="84" font-size="15" fill="#fff" text-anchor="middle" font-weight="bold">departments</text>
  <rect x="30" y="96" width="300" height="34" fill="#334155"/>
  <text x="45" y="118" font-size="13" fill="#fbbf24" font-weight="bold">🔑 dept_id (PK)</text>
  <text x="170" y="118" font-size="13" fill="#cbd5e1">dept_name</text>
  <rect x="30" y="130" width="300" height="30" fill="#0f172a"/>
  <text x="50" y="150" font-size="13" fill="#e2e8f0">1</text><text x="170" y="150" font-size="13" fill="#e2e8f0">Big Data Analytics</text>
  <rect x="30" y="160" width="300" height="30" fill="#0f172a" stroke="#334155"/>
  <text x="50" y="180" font-size="13" fill="#e2e8f0">2</text><text x="170" y="180" font-size="13" fill="#e2e8f0">Artificial Intelligence</text>
  <!-- students -->
  <rect x="420" y="60" width="320" height="36" fill="#10b981" rx="6"/>
  <text x="580" y="84" font-size="15" fill="#fff" text-anchor="middle" font-weight="bold">students</text>
  <rect x="420" y="96" width="320" height="34" fill="#334155"/>
  <text x="435" y="118" font-size="13" fill="#fbbf24" font-weight="bold">🔑 student_id</text>
  <text x="560" y="118" font-size="13" fill="#cbd5e1">name</text>
  <text x="630" y="118" font-size="13" fill="#f472b6" font-weight="bold">🔗 dept_id (FK)</text>
  <rect x="420" y="130" width="320" height="30" fill="#0f172a"/>
  <text x="435" y="150" font-size="13" fill="#e2e8f0">101</text><text x="560" y="150" font-size="13" fill="#e2e8f0">Asha</text><text x="665" y="150" font-size="13" fill="#e2e8f0">1</text>
  <rect x="420" y="160" width="320" height="30" fill="#0f172a" stroke="#334155"/>
  <text x="435" y="180" font-size="13" fill="#e2e8f0">102</text><text x="560" y="180" font-size="13" fill="#e2e8f0">Rohit</text><text x="665" y="180" font-size="13" fill="#e2e8f0">2</text>
  <!-- arrows -->
  <path d="M 660 155 C 560 230, 200 240, 55 155" stroke="#f472b6" stroke-width="2" fill="none" stroke-dasharray="6,4"/>
  <path d="M 660 185 C 580 270, 180 280, 55 185" stroke="#f472b6" stroke-width="2" fill="none" stroke-dasharray="6,4"/>
  <text x="380" y="285" font-size="13" fill="#94a3b8" text-anchor="middle">Each foreign key value must match an existing primary key value</text>
</svg>""", 'A foreign key in one table points to the primary key of another — the heart of the relational model')),
    crossq(
        ('Who proposed the relational model?',
         '<strong>Dr. E. F. (Edgar Frank) Codd</strong> of IBM, in his 1970 paper "A Relational Model of Data for '
         'Large Shared Data Banks". He later published <strong>Codd\'s 12 rules</strong> that define what a fully '
         'relational DBMS must satisfy.'),
        ('Can you name a few of Codd\'s rules?',
         '<strong>Information rule</strong> — all data is stored as values in tables. <strong>Guaranteed access</strong> '
         '— every value is reachable by table name + primary key + column name. <strong>Systematic treatment of NULL</strong>. '
         '<strong>Active online catalog</strong> — metadata is itself stored in tables. <strong>Data independence</strong> '
         '(physical and logical). No commercial RDBMS satisfies all 12 completely.'),
        ('Is MongoDB an RDBMS?',
         'No. MongoDB is a NoSQL <strong>document database</strong>. It stores JSON-like documents in collections, '
         'has a flexible schema and does not enforce foreign keys.'),
    ),
]),

# ------------------------------------------------------------------ 3
Q('What are the disadvantages of a file system compared to a DBMS?', 'File System vs DBMS', minutes=5, cards=[
    definition(
        defbox('Before DBMSs, applications stored data in plain <strong>files</strong> (text, CSV, binary). Each '
               'program managed its own files and its own logic for reading them. A DBMS replaces this with one '
               'shared, centrally controlled store.'),
        tags('File System', 'Data Redundancy', 'Inconsistency', 'Data Isolation', 'Atomicity'),
    ),
    comparison(
        table(['Problem in file systems', 'Example', 'How a DBMS solves it'], [
            ['Data redundancy', 'Student address stored in admission, hostel and library files',
             'Store once, reference by key (normalization)'],
            ['Data inconsistency', 'Address updated in one file, not the others', 'Single copy → always consistent'],
            ['Difficult data access', 'New report needs a new program to be written', 'Ad-hoc queries with SQL'],
            ['Data isolation', 'Data scattered in different files and formats', 'Uniform tables in one database'],
            ['Integrity problems', '"Marks ≤ 100" checked in code — easily missed', 'CHECK / NOT NULL / FK constraints'],
            ['Atomicity problems', 'Crash after debiting A but before crediting B', 'Transactions — all or nothing'],
            ['Concurrent access anomalies', 'Two clerks book the last hostel room', 'Locking and isolation levels'],
            ['Security problems', 'Anyone with file access sees everything', 'Users, roles, GRANT / REVOKE'],
        ]),
    ),
    interview(
        hl('Remember the 8 problems with the phrase <strong>"RIDI-AICS"</strong>: '
           '<strong>R</strong>edundancy, <strong>I</strong>nconsistency, <strong>D</strong>ifficult access, '
           '<strong>I</strong>solation, <strong>A</strong>tomicity, <strong>I</strong>ntegrity, '
           '<strong>C</strong>oncurrency, <strong>S</strong>ecurity.', 'Memory trick'),
        p('Interviewers usually expect 4–5 points with one example each — redundancy, inconsistency, atomicity, '
          'concurrency and security are the strongest.'),
    ),
    crossq(
        ('When would you still prefer plain files?',
         'For large, write-once, read-many data that is processed in bulk — log files, images, video, or data lake '
         'files like <strong>Parquet/CSV on HDFS or S3</strong>. Data engineers use files plus engines like Spark for '
         'analytics, and an RDBMS for transactional data.'),
        ('What is data redundancy and is it always bad?',
         'Redundancy is the same data stored in multiple places. In OLTP systems it causes anomalies, so we normalize. '
         'In data warehouses, <strong>controlled redundancy (denormalization)</strong> is added deliberately to make '
         'analytical queries faster.'),
    ),
]),

# ------------------------------------------------------------------ 4
Q('Explain table, row, column, tuple, attribute, domain, degree and cardinality', 'Relational Terminology', minutes=6, cards=[
    definition(
        defbox('The relational model has formal mathematical terms, and SQL products use everyday names for the '
               'same ideas. Interviewers often mix both, so you should know the mapping.'),
        table(['Relational term', 'SQL / everyday term', 'Meaning'], [
            ['Relation', 'Table', 'A set of tuples with the same attributes'],
            ['Tuple', 'Row / record', 'One entry in the table — e.g. one student'],
            ['Attribute', 'Column / field', 'A named property — e.g. <code>name</code>, <code>email</code>'],
            ['Domain', 'Data type + allowed values', 'Set of valid values for an attribute — e.g. marks 0 to 100'],
            ['Degree', 'Number of columns', 'How many attributes the relation has'],
            ['Cardinality', 'Number of rows', 'How many tuples the relation currently holds'],
            ['Relation schema', 'Table structure', 'Name + attributes, e.g. STUDENT(id, name, email, dept_id)'],
            ['Relation instance', 'Table data at a moment', 'The actual rows present right now'],
        ]),
        tags('Relation', 'Tuple', 'Attribute', 'Domain', 'Degree', 'Cardinality'),
    ),
    example(
        code("""
-- students table
+------------+-------+-----------------+---------+
| student_id | name  | email           | dept_id |
+------------+-------+-----------------+---------+
| 101        | Asha  | asha@mail.com   | 1       |
| 102        | Rohit | rohit@mail.com  | 2       |
| 103        | Meera | meera@mail.com  | 1       |
+------------+-------+-----------------+---------+
""", 'students', 'fa-table'),
        ul('<strong>Degree</strong> = 4 (student_id, name, email, dept_id)',
           '<strong>Cardinality</strong> = 3 (three rows)',
           '<strong>Tuple</strong> = (102, \'Rohit\', \'rohit@mail.com\', 2)',
           '<strong>Domain</strong> of <code>dept_id</code> = the set of existing department ids {1, 2}'),
        warn('"Cardinality" has a second meaning in ER modelling — the type of relationship (1:1, 1:N, M:N). '
             'Clarify which one the interviewer means.', 'Watch out'),
        title='Example: Identifying the Terms'),
    explanation(
        p('<strong>Properties of a relation</strong> — interviewers sometimes ask for these:'),
        ul('Each cell holds a single <strong>atomic</strong> value (no lists inside a cell).',
           'Each column has a unique name, and all values in a column come from the same domain.',
           'No two rows are identical (in the pure model — SQL tables allow duplicates unless a key prevents it).',
           'The order of rows does not matter, and the order of columns does not matter.'),
    ),
    crossq(
        ('If a table has 5 columns and 1,000 rows, what are its degree and cardinality?',
         'Degree = <strong>5</strong>, cardinality = <strong>1,000</strong>.'),
        ('Does the order of rows in a table matter?',
         'No. A relation is a <em>set</em>, so rows have no guaranteed order. If you need an order, you must use '
         '<code>ORDER BY</code> — never rely on insertion order.'),
        ('What is a NULL value?',
         'NULL means "unknown" or "not applicable". It is <strong>not</strong> zero and <strong>not</strong> an '
         'empty string. Any comparison with NULL using <code>=</code> gives UNKNOWN, so you must use '
         '<code>IS NULL</code> / <code>IS NOT NULL</code>.'),
    ),
]),

# ------------------------------------------------------------------ 5
Q('What is SQL? Explain DDL, DML, DQL, DCL and TCL', 'SQL Command Types', minutes=7, cards=[
    definition(
        defbox('<strong>SQL (Structured Query Language)</strong> is the standard language for creating, querying and '
               'managing relational databases. It is <strong>declarative</strong>: you describe <em>what</em> '
               'result you want, and the database\'s query optimizer decides <em>how</em> to get it.',
               'SQL is standardised by ANSI/ISO (SQL-86, SQL-92, SQL:1999 … SQL:2023). Each vendor adds its own '
               'extensions — MySQL, PostgreSQL and Oracle each have small syntax differences.'),
        tags('SQL', 'Declarative', 'DDL', 'DML', 'DQL', 'DCL', 'TCL'),
    ),
    comparison(
        table(['Category', 'Full form', 'Purpose', 'Commands'], [
            ['DDL', 'Data Definition Language', 'Define or change structure', 'CREATE, ALTER, DROP, TRUNCATE, RENAME'],
            ['DML', 'Data Manipulation Language', 'Change the data', 'INSERT, UPDATE, DELETE, MERGE'],
            ['DQL', 'Data Query Language', 'Read the data', 'SELECT'],
            ['DCL', 'Data Control Language', 'Permissions', 'GRANT, REVOKE'],
            ['TCL', 'Transaction Control Language', 'Manage transactions', 'COMMIT, ROLLBACK, SAVEPOINT, SET TRANSACTION'],
        ]),
        title='The Five Sub-Languages'),
    example(
        code("""
-- DDL: define structure
CREATE TABLE courses (
    course_id   INT PRIMARY KEY,
    course_name VARCHAR(60) NOT NULL,
    fee         DECIMAL(10,2)
);
ALTER TABLE courses ADD COLUMN duration_months INT;

-- DML: change data
INSERT INTO courses VALUES (1, 'PGCP-BDA', 95000, 6);
UPDATE courses SET fee = 98000 WHERE course_id = 1;

-- DQL: read data
SELECT course_name, fee FROM courses WHERE fee > 50000;

-- DCL: permissions
GRANT SELECT ON college_db.courses TO 'report_user'@'localhost';

-- TCL: transactions
START TRANSACTION;
DELETE FROM courses WHERE course_id = 1;
ROLLBACK;   -- the delete is undone
"""),
        title='Example: One Command from Each Category'),
    interview(
        hl('<code>TRUNCATE</code> is <strong>DDL</strong>, not DML — even though it removes data. It deallocates the '
           'table\'s data pages instead of deleting row by row, and in MySQL it causes an implicit commit, so it '
           'cannot be rolled back.', 'Favourite trick question'),
        p('Also note: in MySQL and Oracle, every DDL statement causes an <strong>implicit COMMIT</strong>. '
          'PostgreSQL is different — DDL can run inside a transaction and be rolled back.'),
    ),
    crossq(
        ('Is SELECT part of DML or DQL?',
         'Both answers appear in textbooks. Many classify SELECT as DML (it manipulates data for retrieval); others '
         'separate it as DQL. Mention both — the five-category split (DDL/DML/DQL/DCL/TCL) is the most common in interviews.'),
        ('What does "SQL is declarative" mean?',
         'You state the result you want (<code>SELECT name FROM students WHERE dept_id = 1</code>) without writing '
         'loops or saying which index to use. Compare with procedural code (Python, Java), where you write the '
         'step-by-step algorithm.'),
        ('Is SQL case-sensitive?',
         'Keywords are not (<code>select</code> = <code>SELECT</code>). Whether table names and string comparisons '
         'are case-sensitive depends on the DBMS, operating system and collation. In MySQL on Linux, table names are '
         'case-sensitive by default; on Windows they are not.'),
    ),
]),

# ------------------------------------------------------------------ 6
Q('What is the difference between schema and instance? Explain the three-schema architecture', 'Schema, Instance & 3-Level Architecture', minutes=8, cards=[
    definition(
        defbox('<strong>Schema</strong> — the <em>design</em> or structure of the database: tables, columns, data types, '
               'constraints and relationships. It changes rarely.',
               '<strong>Instance (state)</strong> — the actual <em>data</em> in the database at a particular moment. '
               'It changes every time data is inserted, updated or deleted.'),
        hl('Schema is like the <strong>blueprint of a building</strong>; instance is the <strong>people inside it right now</strong>.', 'Analogy'),
        tags('Schema', 'Instance', 'ANSI-SPARC', 'Data Independence', 'Physical Level', 'Logical Level', 'View Level'),
    ),
    explanation(
        p('The <strong>ANSI/SPARC three-schema architecture</strong> separates how users see data from how it is stored:'),
        table(['Level', 'Also called', 'Describes', 'Who uses it'], [
            ['External level', 'View level', 'Part of the database relevant to one user group (views)', 'End users, applications'],
            ['Conceptual level', 'Logical level', 'All tables, columns, relationships and constraints', 'Database designers, DBAs'],
            ['Internal level', 'Physical level', 'Files, pages, indexes, storage blocks, compression', 'DBMS engine, DBAs'],
        ]),
        p('The goal is <strong>data independence</strong>:', True),
        ul('<strong>Physical data independence</strong> — change the internal level (add an index, move to SSD, '
           'change file organisation) without changing the logical schema or applications. Easy to achieve.',
           '<strong>Logical data independence</strong> — change the conceptual schema (add a column, split a table) '
           'without changing external views or applications. Harder to achieve.'),
    ),
    visual(svg("""
<svg width="760" height="380" viewBox="0 0 760 380" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="380" fill="#1e293b"/>
  <text x="380" y="30" font-size="18" fill="#0ea5e9" text-anchor="middle" font-weight="bold">Three-Schema Architecture</text>
  <rect x="60" y="55" width="190" height="55" rx="8" fill="#8b5cf6" opacity="0.25" stroke="#8b5cf6" stroke-width="2"/>
  <text x="155" y="80" font-size="14" fill="#f1f5f9" text-anchor="middle" font-weight="bold">View 1</text>
  <text x="155" y="98" font-size="12" fill="#cbd5e1" text-anchor="middle">Exam cell</text>
  <rect x="285" y="55" width="190" height="55" rx="8" fill="#8b5cf6" opacity="0.25" stroke="#8b5cf6" stroke-width="2"/>
  <text x="380" y="80" font-size="14" fill="#f1f5f9" text-anchor="middle" font-weight="bold">View 2</text>
  <text x="380" y="98" font-size="12" fill="#cbd5e1" text-anchor="middle">Accounts</text>
  <rect x="510" y="55" width="190" height="55" rx="8" fill="#8b5cf6" opacity="0.25" stroke="#8b5cf6" stroke-width="2"/>
  <text x="605" y="80" font-size="14" fill="#f1f5f9" text-anchor="middle" font-weight="bold">View 3</text>
  <text x="605" y="98" font-size="12" fill="#cbd5e1" text-anchor="middle">Placement</text>
  <line x1="155" y1="110" x2="330" y2="170" stroke="#64748b" stroke-width="2"/>
  <line x1="380" y1="110" x2="380" y2="170" stroke="#64748b" stroke-width="2"/>
  <line x1="605" y1="110" x2="430" y2="170" stroke="#64748b" stroke-width="2"/>
  <text x="560" y="150" font-size="12" fill="#fbbf24">↕ Logical data independence</text>
  <rect x="200" y="170" width="360" height="60" rx="8" fill="#0ea5e9" opacity="0.25" stroke="#0ea5e9" stroke-width="2"/>
  <text x="380" y="196" font-size="15" fill="#f1f5f9" text-anchor="middle" font-weight="bold">Conceptual / Logical Schema</text>
  <text x="380" y="216" font-size="12" fill="#cbd5e1" text-anchor="middle">students, departments, courses, enrollments + constraints</text>
  <line x1="380" y1="230" x2="380" y2="280" stroke="#64748b" stroke-width="2"/>
  <text x="560" y="262" font-size="12" fill="#fbbf24">↕ Physical data independence</text>
  <rect x="200" y="280" width="360" height="60" rx="8" fill="#10b981" opacity="0.25" stroke="#10b981" stroke-width="2"/>
  <text x="380" y="306" font-size="15" fill="#f1f5f9" text-anchor="middle" font-weight="bold">Internal / Physical Schema</text>
  <text x="380" y="326" font-size="12" fill="#cbd5e1" text-anchor="middle">data files, pages, B-tree indexes, storage</text>
  <text x="380" y="368" font-size="12" fill="#94a3b8" text-anchor="middle">Mappings between levels let each level change without breaking the one above it</text>
</svg>""", 'External views → one conceptual schema → one physical storage layout')),
    example(
        code("""
-- Conceptual level: the full table
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name       VARCHAR(100),
    phone      VARCHAR(15),
    fee_paid   DECIMAL(10,2),
    cgpa       DECIMAL(3,2)
);

-- External level: placement cell sees only what it needs
CREATE VIEW placement_view AS
SELECT student_id, name, cgpa FROM students;

-- Internal level change: add an index.
-- No application or view has to change -> physical data independence
CREATE INDEX idx_students_cgpa ON students(cgpa);
"""),
        title='Example: The Levels in SQL'),
    crossq(
        ('Which data independence is harder to achieve, and why?',
         '<strong>Logical</strong> data independence. Applications and views are written against the logical schema, '
         'so removing or renaming a column or splitting a table can break them. Physical changes (indexes, storage) '
         'are hidden by the DBMS completely.'),
        ('What is a subschema?',
         'Another name for an external schema / view — the subset of the database that a particular user or '
         'application is allowed to see.'),
        ('Where is the schema itself stored?',
         'In the <strong>data dictionary (system catalog)</strong>. In MySQL you can query it through '
         '<code>information_schema.tables</code> and <code>information_schema.columns</code>.'),
    ),
]),

])
