from build import *
from rdbms.anims import *

SECTION = dict(level='basic', title='Keys & Constraints', questions=[

# ------------------------------------------------------------------ 7
Q('What is a Primary Key?', 'Primary Key', minutes=6, cards=[
    definition(
        defbox('A <strong>primary key (PK)</strong> is a column, or a set of columns, whose value '
               '<strong>uniquely identifies each row</strong> in a table.',
               'A primary key must be <strong>unique</strong> and <strong>NOT NULL</strong>, and a table can have '
               '<strong>only one</strong> primary key (although that key can be made of several columns).'),
        hl('Unique + Not Null + Only one per table + Should rarely change.', 'Rules to remember'),
        tags('Primary Key', 'Uniqueness', 'NOT NULL', 'Entity Integrity', 'Clustered Index'),
    ),
    example(
        code("""
-- Column-level definition
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL
);

-- Table-level definition with a constraint name (preferred in production)
CREATE TABLE courses (
    course_id   INT,
    course_name VARCHAR(60) NOT NULL,
    CONSTRAINT pk_courses PRIMARY KEY (course_id)
);

-- Auto-generated primary key (MySQL)
CREATE TABLE enquiries (
    enquiry_id INT AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(100)
);

INSERT INTO students VALUES (101, 'Asha');
INSERT INTO students VALUES (101, 'Rohit');   -- fails: duplicate
INSERT INTO students VALUES (NULL, 'Meera');  -- fails: NULL not allowed
"""),
        output("""
ERROR 1062 (23000): Duplicate entry '101' for key 'students.PRIMARY'
ERROR 1048 (23000): Column 'student_id' cannot be null
"""),
        title='Example: Defining and Violating a Primary Key'),
    explanation(
        p('<strong>Why every table needs a primary key:</strong>'),
        ul('<strong>Entity integrity</strong> — every row can be identified and no row is "lost" as an exact duplicate.',
           '<strong>Relationships</strong> — foreign keys in other tables point to it.',
           '<strong>Performance</strong> — the DBMS automatically creates a unique index on it. In MySQL InnoDB the '
           'table data itself is physically ordered by the primary key (clustered index).',
           '<strong>Updates and deletes</strong> — <code>WHERE student_id = 101</code> touches exactly one row.'),
        p('<strong>Choosing a good primary key:</strong> small, stable (never changes), never NULL, and preferably '
          'numeric. Avoid email or phone numbers — they change, and every foreign key pointing to them would have to change too.', True),
    ),
    crossq(
        ('Can a primary key have duplicate values if it is made of two columns?',
         'Each <em>individual</em> column can repeat, but the <strong>combination</strong> must be unique. In '
         '<code>enrollments(student_id, course_id)</code> student 101 can appear many times, but (101, 5) only once.'),
        ('Can we have a table without a primary key?',
         'Yes, SQL allows it, but it is bad practice — duplicate rows cannot be told apart, and replication and '
         'many tools expect one. InnoDB silently creates a hidden 6-byte row id if no primary key or unique NOT NULL key exists.'),
        ('Can a primary key be updated?',
         'Technically yes, but it should be avoided: every referencing foreign key must change too (or be handled with '
         '<code>ON UPDATE CASCADE</code>), and in InnoDB the row is physically moved.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What are Super Key, Candidate Key and Alternate Key?', 'Super, Candidate & Alternate Keys', minutes=7, cards=[
    definition(
        table(['Key', 'Definition', 'Key property'], [
            ['Super key', 'Any set of columns that uniquely identifies a row', 'May contain extra, unnecessary columns'],
            ['Candidate key', 'A <strong>minimal</strong> super key — remove any column and it is no longer unique', 'No redundant columns'],
            ['Primary key', 'The candidate key <strong>chosen</strong> by the designer to identify rows', 'Exactly one per table'],
            ['Alternate key', 'Candidate keys that were <strong>not</strong> chosen as the primary key', 'Usually enforced with UNIQUE'],
        ]),
        hl('Super key ⊇ Candidate key ⊇ Primary key. Every candidate key is a super key, but not every super key is a candidate key.', 'Relationship'),
        tags('Super Key', 'Candidate Key', 'Alternate Key', 'Minimality', 'Prime Attribute'),
    ),
    example(
        code("""
students(student_id, roll_no, email, name, phone)

-- Assume student_id, roll_no and email are each unique.

Super keys (some of them):
  {student_id}
  {roll_no}
  {email}
  {student_id, name}
  {roll_no, email, phone}
  {student_id, roll_no, email, name, phone}   -- all columns is always a super key

Candidate keys (minimal):
  {student_id}, {roll_no}, {email}

Primary key (chosen):
  {student_id}

Alternate keys:
  {roll_no}, {email}
""", 'Identifying keys', 'fa-key'),
        code("""
CREATE TABLE students (
    student_id INT PRIMARY KEY,          -- chosen candidate key
    roll_no    VARCHAR(20) NOT NULL UNIQUE, -- alternate key
    email      VARCHAR(100) NOT NULL UNIQUE, -- alternate key
    name       VARCHAR(100),
    phone      VARCHAR(15)
);
""", 'Implementing them in SQL'),
        title='Example: Student Table'),
    visual(svg("""
<svg width="700" height="320" viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="700" height="320" fill="#1e293b"/>
  <ellipse cx="350" cy="170" rx="320" ry="135" fill="#8b5cf6" opacity="0.15" stroke="#8b5cf6" stroke-width="2"/>
  <text x="350" y="60" font-size="15" fill="#c4b5fd" text-anchor="middle" font-weight="bold">Super Keys</text>
  <ellipse cx="350" cy="185" rx="210" ry="95" fill="#0ea5e9" opacity="0.18" stroke="#0ea5e9" stroke-width="2"/>
  <text x="350" y="115" font-size="15" fill="#7dd3fc" text-anchor="middle" font-weight="bold">Candidate Keys</text>
  <ellipse cx="260" cy="200" rx="80" ry="45" fill="#fbbf24" opacity="0.25" stroke="#fbbf24" stroke-width="2"/>
  <text x="260" y="196" font-size="14" fill="#fde68a" text-anchor="middle" font-weight="bold">Primary Key</text>
  <text x="260" y="214" font-size="12" fill="#e2e8f0" text-anchor="middle">student_id</text>
  <ellipse cx="445" cy="200" rx="90" ry="45" fill="#10b981" opacity="0.25" stroke="#10b981" stroke-width="2"/>
  <text x="445" y="196" font-size="14" fill="#6ee7b7" text-anchor="middle" font-weight="bold">Alternate Keys</text>
  <text x="445" y="214" font-size="12" fill="#e2e8f0" text-anchor="middle">roll_no, email</text>
  <text x="120" y="270" font-size="12" fill="#cbd5e1">{student_id, name}</text>
  <text x="470" y="275" font-size="12" fill="#cbd5e1">{roll_no, phone}</text>
</svg>""", 'Primary and alternate keys are both candidate keys; every candidate key is a super key')),
    crossq(
        ('What is a prime attribute?',
         'An attribute that is part of <strong>any</strong> candidate key. Attributes not in any candidate key are '
         '<strong>non-prime</strong>. This distinction is central to 2NF and 3NF.'),
        ('How many super keys can a table have?',
         'Potentially many. If a relation has <em>n</em> attributes and one single-column candidate key, the number of '
         'super keys is 2<sup>n−1</sup> (the key plus any combination of the remaining n−1 attributes).'),
        ('How do you choose the primary key among candidate keys?',
         'Pick the one that is smallest, stable, never NULL and meaningful to joins — usually a numeric id. '
         'Email and phone are poor choices because they change.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What is a Foreign Key and Referential Integrity?', 'Foreign Key & Referential Integrity', minutes=7, cards=[
    definition(
        defbox('A <strong>foreign key (FK)</strong> is a column (or set of columns) in one table that refers to the '
               'primary key (or a unique key) of another table. The table holding the FK is the <strong>child</strong>; '
               'the referenced table is the <strong>parent</strong>.',
               '<strong>Referential integrity</strong> is the rule that every non-NULL foreign key value must match an '
               'existing value in the parent table — no "orphan" rows.'),
        tags('Foreign Key', 'Referential Integrity', 'Parent Table', 'Child Table', 'Orphan Rows'),
    ),
    fk_integrity(),
    example(
        code("""
CREATE TABLE departments (
    dept_id   INT PRIMARY KEY,
    dept_name VARCHAR(50)
);

CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name       VARCHAR(100),
    dept_id    INT,
    CONSTRAINT fk_student_dept
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

INSERT INTO departments VALUES (1, 'Big Data Analytics');
INSERT INTO students VALUES (101, 'Asha', 1);      -- OK
INSERT INTO students VALUES (102, 'Rohit', 9);     -- fails: dept 9 does not exist
INSERT INTO students VALUES (103, 'Meera', NULL);  -- OK: FK may be NULL
DELETE FROM departments WHERE dept_id = 1;         -- fails: child rows exist
"""),
        output("""
ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails
ERROR 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails
"""),
        title='Example: Parent and Child Tables'),
    explanation(
        p('Referential integrity can be broken in four ways, and the DBMS checks each one:'),
        table(['Operation', 'Table', 'Check performed'], [
            ['INSERT', 'Child', 'The FK value must exist in the parent'],
            ['UPDATE of FK', 'Child', 'The new value must exist in the parent'],
            ['DELETE', 'Parent', 'What happens to children? → RESTRICT / CASCADE / SET NULL'],
            ['UPDATE of PK', 'Parent', 'Same choice → RESTRICT / CASCADE / SET NULL'],
        ]),
    ),
    crossq(
        ('Can a foreign key be NULL?',
         'Yes, unless declared NOT NULL. A NULL FK means "no relationship yet" — e.g. a student not yet assigned to a '
         'department. Referential integrity applies only to non-NULL values.'),
        ('Can a foreign key reference a non-primary-key column?',
         'Yes — it can reference any column with a <strong>UNIQUE</strong> constraint (a candidate key). In MySQL the '
         'referenced column must at least be indexed.'),
        ('Can a table have a foreign key to itself?',
         'Yes — a <strong>self-referencing</strong> foreign key. Example: <code>employees.manager_id</code> references '
         '<code>employees.emp_id</code>. This models hierarchies.'),
        ('Can a table have more than one foreign key?',
         'Yes. A junction table like <code>enrollments</code> has two: one to <code>students</code> and one to <code>courses</code>.'),
        ('Do foreign keys slow things down?',
         'Slightly — every insert/update must check the parent. Many data warehouses skip enforced FKs for faster '
         'bulk loads and rely on the ETL process for integrity. In OLTP systems, keep them.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What are Composite, Surrogate and Natural keys?', 'Composite, Surrogate & Natural Keys', minutes=6, cards=[
    definition(
        table(['Key type', 'Definition', 'Example'], [
            ['Simple key', 'A key made of one column', '<code>student_id</code>'],
            ['Composite key', 'A key made of two or more columns together', '<code>(student_id, course_id)</code> in enrollments'],
            ['Natural key', 'A key that has real-world business meaning', 'Aadhaar number, PAN, ISBN, email'],
            ['Surrogate key', 'An artificial, system-generated key with no business meaning', 'AUTO_INCREMENT id, UUID'],
        ]),
        tags('Composite Key', 'Surrogate Key', 'Natural Key', 'AUTO_INCREMENT', 'UUID'),
    ),
    example(
        code("""
-- Composite primary key: one row per student per course
CREATE TABLE enrollments (
    student_id  INT,
    course_id   INT,
    enrolled_on DATE,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)
);

-- Surrogate key + natural key kept unique
CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,   -- surrogate
    isbn    CHAR(13) NOT NULL UNIQUE,         -- natural key
    title   VARCHAR(200)
);
"""),
        title='Example'),
    comparison(
        compare(
            ('Natural key', ul('✅ Meaningful, no extra column', '✅ Prevents business duplicates',
                               '❌ Can change (email, phone)', '❌ Often long strings → large indexes',
                               '❌ Sometimes not available for everyone')),
            ('Surrogate key', ul('✅ Small, fast integer joins', '✅ Never changes',
                                 '✅ Shields design from business changes', '❌ No meaning — need a UNIQUE on the natural key too',
                                 '❌ One extra column')),
        ),
        note('Common practice: use a <strong>surrogate primary key</strong> and add a <strong>UNIQUE constraint</strong> '
             'on the natural key. In data warehouses, dimension tables always use surrogate keys (needed for SCD Type 2).'),
        title='Natural vs Surrogate'),
    crossq(
        ('What is the difference between a composite key and a compound key?',
         'Many books treat them as the same. A stricter definition: a <strong>compound key</strong> is a composite key '
         'in which each column is itself a foreign key — like <code>(student_id, course_id)</code> in a junction table.'),
        ('Why do data warehouses use surrogate keys?',
         'Source systems may reuse or change their ids, several sources may collide, and SCD Type 2 needs multiple '
         'versions of the same business entity — each version needs its own key.'),
        ('Is UUID a good primary key in MySQL?',
         'It is globally unique (good for distributed systems), but random UUIDs make InnoDB insert into random pages '
         'of the clustered index, causing page splits. Use an ordered UUID (UUIDv7, or <code>UUID_TO_BIN(uuid, 1)</code>) or an integer.'),
    ),
]),

# ------------------------------------------------------------------ 11
Q('What is the difference between a Unique Key and a Primary Key?', 'Unique Key vs Primary Key', minutes=5, cards=[
    definition(
        defbox('A <strong>UNIQUE</strong> constraint ensures that all non-NULL values in a column (or set of columns) '
               'are different. Like a primary key it prevents duplicates, but it is more relaxed in a few important ways.'),
        tags('UNIQUE', 'Primary Key', 'NULL', 'Index', 'Alternate Key'),
    ),
    comparison(
        table(['Aspect', 'Primary Key', 'Unique Key'], [
            ['Duplicates allowed', 'No', 'No'],
            ['NULL allowed', 'No', 'Yes (MySQL, PostgreSQL: multiple NULLs; SQL Server: only one)'],
            ['How many per table', 'Only one', 'Many'],
            ['Index created', 'Unique index (clustered in InnoDB)', 'Unique non-clustered index'],
            ['Purpose', 'Identify each row', 'Enforce uniqueness of alternate keys'],
            ['Referenced by FK', 'Yes', 'Yes'],
        ]),
    ),
    example(
        code("""
CREATE TABLE users (
    user_id  INT PRIMARY KEY,
    email    VARCHAR(100) UNIQUE,
    username VARCHAR(30)  UNIQUE
);

INSERT INTO users VALUES (1, 'a@x.com', 'asha');
INSERT INTO users VALUES (2, NULL, 'rohit');
INSERT INTO users VALUES (3, NULL, 'meera');      -- OK in MySQL: NULLs are not equal
INSERT INTO users VALUES (4, 'a@x.com', 'kiran'); -- fails: duplicate email
"""),
        title='Example'),
    crossq(
        ('Why can a UNIQUE column hold more than one NULL?',
         'NULL means "unknown", and one unknown is not considered equal to another unknown, so they do not violate '
         'uniqueness. SQL Server is the exception — it allows only one NULL in a unique column by default.'),
        ('Can a UNIQUE constraint span multiple columns?',
         'Yes: <code>UNIQUE (dept_id, roll_no)</code> means the same roll number can exist in different departments, '
         'but not twice in the same department.'),
        ('If a unique key is NOT NULL, is it the same as a primary key?',
         'Functionally almost — it is a candidate key. The difference is that only one is designated primary, and in '
         'InnoDB only the primary key decides the physical row order.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('What are constraints? Explain NOT NULL, UNIQUE, CHECK and DEFAULT', 'Constraints', minutes=7, cards=[
    definition(
        defbox('<strong>Constraints</strong> are rules defined on table columns that the DBMS enforces automatically '
               'on every INSERT and UPDATE. They keep invalid data out of the database regardless of which application '
               'or user writes the data.'),
        table(['Constraint', 'Ensures that…'], [
            ['NOT NULL', 'The column always has a value'],
            ['UNIQUE', 'No two rows share the same value'],
            ['PRIMARY KEY', 'UNIQUE + NOT NULL; identifies each row'],
            ['FOREIGN KEY', 'The value exists in the referenced table'],
            ['CHECK', 'The value satisfies a condition (e.g. marks between 0 and 100)'],
            ['DEFAULT', 'A value is filled in automatically when none is supplied'],
        ]),
        tags('Constraints', 'NOT NULL', 'UNIQUE', 'CHECK', 'DEFAULT', 'Domain Integrity'),
    ),
    example(
        code("""
CREATE TABLE exam_results (
    result_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id  INT NOT NULL,
    subject     VARCHAR(50) NOT NULL,
    marks       INT CHECK (marks BETWEEN 0 AND 100),
    grade       CHAR(2),
    exam_date   DATE DEFAULT (CURRENT_DATE),
    status      VARCHAR(10) DEFAULT 'PENDING',
    CONSTRAINT uq_student_subject UNIQUE (student_id, subject),
    CONSTRAINT chk_status CHECK (status IN ('PENDING', 'PASS', 'FAIL')),
    CONSTRAINT fk_result_student FOREIGN KEY (student_id) REFERENCES students(student_id)
);

INSERT INTO exam_results (student_id, subject, marks) VALUES (101, 'SQL', 85);
-- exam_date = today, status = 'PENDING' filled automatically

INSERT INTO exam_results (student_id, subject, marks) VALUES (101, 'Python', 120);
-- ERROR 3819: Check constraint 'exam_results_chk_1' is violated.

-- Add / drop constraints later
ALTER TABLE exam_results ADD CONSTRAINT chk_grade CHECK (grade IN ('A','B','C','D','F'));
ALTER TABLE exam_results DROP CONSTRAINT chk_grade;   -- MySQL 8.0.19+
"""),
        title='Example: All Constraints in One Table'),
    interview(
        warn('<code>CHECK</code> constraints were <strong>parsed but silently ignored</strong> in MySQL before version '
             '<strong>8.0.16</strong>. On older versions you had to use triggers or ENUM. Mention the version if asked.', 'MySQL gotcha'),
        p('Column-level vs table-level: a constraint that involves several columns '
          '(<code>UNIQUE (student_id, subject)</code>) must be written at table level. Naming constraints '
          '(<code>CONSTRAINT chk_status …</code>) makes error messages readable and lets you drop them easily.'),
    ),
    crossq(
        ('What is the difference between a constraint and validation in the application?',
         'Application validation can be bypassed (another app, a script, a manual SQL update). Constraints are enforced '
         'by the database for every writer. Best practice is both: application checks for a friendly message, DB constraints as the guarantee.'),
        ('Can a CHECK constraint refer to another table?',
         'No. CHECK can only use values from the same row. Cross-table rules need a foreign key or a trigger.'),
        ('Does DEFAULT apply when NULL is inserted explicitly?',
         'No. DEFAULT is used only when the column is omitted (or the keyword <code>DEFAULT</code> is used). '
         'Explicitly inserting NULL stores NULL, unless the column is NOT NULL, in which case it fails.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('Explain ON DELETE CASCADE, SET NULL, RESTRICT and NO ACTION', 'Referential Actions (CASCADE)', minutes=6, cards=[
    definition(
        defbox('<strong>Referential actions</strong> tell the DBMS what to do with child rows when the parent row they '
               'reference is <strong>deleted</strong> or its key is <strong>updated</strong>.'),
        table(['Action', 'Effect on child rows when parent is deleted/updated'], [
            ['CASCADE', 'Child rows are deleted (or their FK updated) automatically'],
            ['SET NULL', 'Child FK is set to NULL (column must allow NULL)'],
            ['SET DEFAULT', 'Child FK is set to its default value (not supported by InnoDB)'],
            ['RESTRICT', 'The parent delete/update is rejected immediately if children exist'],
            ['NO ACTION', 'Rejected if children exist — checked at end of statement (same as RESTRICT in MySQL)'],
        ]),
        tags('ON DELETE CASCADE', 'ON UPDATE CASCADE', 'SET NULL', 'RESTRICT', 'NO ACTION'),
    ),
    cascade_anim(),
    example(
        code("""
CREATE TABLE orders (
    order_id    INT PRIMARY KEY,
    customer_id INT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE SET NULL          -- keep the order history, lose the link
        ON UPDATE CASCADE
);

CREATE TABLE order_items (
    order_id   INT,
    product_id INT,
    qty        INT,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE           -- items are meaningless without their order
);

DELETE FROM orders WHERE order_id = 5001;
-- all rows in order_items with order_id 5001 are deleted automatically
"""),
        title='Example: Choosing the Right Action'),
    real_world(
        table(['Relationship', 'Sensible action', 'Why'], [
            ['order → order_items', 'CASCADE', 'Items cannot exist without the order'],
            ['department → students', 'SET NULL or RESTRICT', 'Do not delete students just because a department closes'],
            ['customer → payments', 'RESTRICT', 'Financial records must never disappear silently'],
            ['post → comments', 'CASCADE', 'Comments belong to the post'],
        ]),
        warn('CASCADE can chain through many tables and delete far more than expected. Many teams prefer RESTRICT plus '
             '"soft delete" (an <code>is_deleted</code> flag) for important data.', 'Be careful'),
    ),
    crossq(
        ('What is the default action if you do not specify one?',
         'In MySQL InnoDB the default is <strong>RESTRICT / NO ACTION</strong> — the parent delete fails if children exist.'),
        ('Do CASCADE deletes fire triggers on the child table in MySQL?',
         'No. In MySQL, cascaded foreign-key actions do <strong>not</strong> activate triggers on the child table — a '
         'well-known gotcha if you rely on triggers for auditing.'),
        ('What is a soft delete?',
         'Instead of <code>DELETE</code>, you mark the row: <code>UPDATE customers SET is_deleted = 1</code>. History '
         'is preserved and nothing cascades; queries filter with <code>WHERE is_deleted = 0</code>.'),
    ),
]),

])
