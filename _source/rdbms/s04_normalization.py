from build import *
from rdbms.anims import *

SECTION = dict(level='intermediate', title='Normalization', questions=[

# ------------------------------------------------------------------ 20
Q('What is Normalization and why is it needed?', 'Normalization: What & Why', minutes=6, cards=[
    definition(
        defbox('<strong>Normalization</strong> is the process of organising columns and tables to '
               '<strong>reduce data redundancy</strong> and <strong>eliminate insert, update and delete anomalies</strong>. '
               'It works by splitting a large table into smaller, well-structured tables and linking them with keys.',
               'It is done step by step through <strong>normal forms</strong>: 1NF → 2NF → 3NF → BCNF → 4NF → 5NF. '
               'Each form removes a specific kind of dependency problem.'),
        hl('"The key, the whole key, and nothing but the key — so help me Codd." '
           '1NF: atomic values with a key · 2NF: depend on the <em>whole</em> key · 3NF: depend on <em>nothing but</em> the key.', 'Classic memory line'),
        tags('Normalization', 'Redundancy', 'Anomalies', 'Normal Forms', 'Decomposition', 'Lossless Join'),
    ),
    explanation(
        table(['Normal form', 'Rule', 'Removes'], [
            ['1NF', 'Atomic values, no repeating groups, each row unique', 'Multi-valued cells, repeating columns'],
            ['2NF', '1NF + no partial dependency on part of a composite key', 'Partial dependencies'],
            ['3NF', '2NF + no transitive dependency (non-key → non-key)', 'Transitive dependencies'],
            ['BCNF', 'Every determinant is a candidate key', 'Remaining anomalies from overlapping candidate keys'],
            ['4NF', 'BCNF + no multi-valued dependencies', 'Independent multi-valued facts in one table'],
            ['5NF', '4NF + no join dependencies', 'Redundancy that only lossless joins of 3+ tables can remove'],
        ]),
        p('<strong>Benefits:</strong> less storage wasted, one place to update each fact, consistent data, cleaner '
          'design. <strong>Cost:</strong> more tables and more joins at query time. In practice OLTP systems are '
          'normalized to <strong>3NF/BCNF</strong>; analytics systems are often deliberately denormalized.', True),
    ),
    crossq(
        ('Who introduced normalization?',
         'E. F. Codd introduced 1NF (1970), 2NF and 3NF (1971). BCNF was defined by Boyce and Codd in 1974; 4NF by Fagin (1977) and 5NF by Fagin (1979).'),
        ('What is a lossless (non-additive) decomposition?',
         'Splitting a table so that joining the parts back gives <strong>exactly</strong> the original rows — no rows '
         'lost and no spurious extra rows. It is guaranteed when the common column(s) form a key of at least one of the parts.'),
        ('What is dependency preservation?',
         'After decomposition, every functional dependency can still be checked within a single table, without joins. '
         '3NF decomposition can always preserve dependencies; BCNF sometimes cannot.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('What are Insertion, Update and Deletion anomalies?', 'Anomalies', minutes=6, cards=[
    definition(
        defbox('<strong>Anomalies</strong> are problems that arise when one table stores facts about several different '
               'things. They are the reason we normalize.'),
        tags('Insertion Anomaly', 'Update Anomaly', 'Deletion Anomaly', 'Redundancy'),
    ),
    example(
        p('Consider this un-normalized table that mixes student, course and faculty facts:'),
        code("""
+------------+--------+-----------+-------------+--------------+---------------+
| student_id | name   | course_id | course_name | faculty_name | faculty_phone |
+------------+--------+-----------+-------------+--------------+---------------+
| 101        | Asha   | C1        | SQL         | Prof. Rao    | 98200 11111   |
| 102        | Rohit  | C1        | SQL         | Prof. Rao    | 98200 11111   |
| 103        | Meera  | C2        | Spark       | Prof. Iyer   | 98200 22222   |
+------------+--------+-----------+-------------+--------------+---------------+
""", 'student_course (badly designed)', 'fa-table'),
        table(['Anomaly', 'What goes wrong here'], [
            ['Insertion', 'A new course C3 "Kafka" cannot be added until at least one student enrols — student_id (part of the key) would be NULL.'],
            ['Update', 'If Prof. Rao changes phone number, every row of C1 must be updated. Miss one row and the data becomes inconsistent.'],
            ['Deletion', 'If Meera (the only Spark student) leaves, deleting her row also deletes the fact that course C2 exists and who teaches it.'],
        ]),
        title='Example: One Table, Three Anomalies'),
    explanation(
        p('<strong>Fix:</strong> split by subject — each table holds facts about one thing.'),
        code("""
students(student_id PK, name)
courses(course_id PK, course_name, faculty_id FK)
faculty(faculty_id PK, faculty_name, faculty_phone)
enrollments(student_id FK, course_id FK, PK(student_id, course_id))
""", 'Normalized design', 'fa-sitemap'),
        p('Now a course can be added without students, the phone number lives in exactly one row, and deleting a '
          'student only removes the enrollment.'),
        title='Solution'),
    crossq(
        ('Which anomaly is caused directly by redundancy?',
         'The <strong>update anomaly</strong> — the same fact stored many times must be updated many times. Insertion '
         'and deletion anomalies come from mixing independent facts in one table.'),
        ('Can anomalies exist in a 3NF table?',
         'Rarely, yes — when a table has overlapping composite candidate keys. BCNF removes those remaining cases.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What is a Functional Dependency?', 'Functional Dependency', minutes=7, cards=[
    definition(
        defbox('A <strong>functional dependency (FD)</strong> <code>X → Y</code> means that the value of attribute set '
               '<strong>X</strong> uniquely determines the value of <strong>Y</strong>. Whenever two rows have the same X, '
               'they must have the same Y.',
               'X is called the <strong>determinant</strong> and Y the <strong>dependent</strong>. '
               'Example: <code>student_id → name</code> — knowing the student id tells you the name.'),
        tags('Functional Dependency', 'Determinant', 'Armstrong\'s Axioms', 'Closure', 'Partial', 'Transitive'),
    ),
    explanation(
        table(['Type', 'Meaning', 'Example'], [
            ['Trivial', 'Y is a subset of X', '{student_id, name} → name'],
            ['Non-trivial', 'Y is not a subset of X', 'student_id → name'],
            ['Full', 'Y depends on the whole of X, not on any part', '{student_id, course_id} → grade'],
            ['Partial', 'Y depends on only part of a composite key', '{student_id, course_id} → student_name (needs only student_id)'],
            ['Transitive', 'X → Y and Y → Z, so X → Z through Y', 'student_id → dept_id → dept_name'],
            ['Multivalued (MVD)', 'X →→ Y: X determines a set of Y values independent of other attributes', 'emp_id →→ skill'],
        ]),
        p('<strong>Armstrong\'s axioms</strong> — the rules used to derive all FDs:', True),
        ul('<strong>Reflexivity</strong>: if Y ⊆ X, then X → Y',
           '<strong>Augmentation</strong>: if X → Y, then XZ → YZ',
           '<strong>Transitivity</strong>: if X → Y and Y → Z, then X → Z',
           'Derived rules: <strong>Union</strong> (X→Y, X→Z ⇒ X→YZ), <strong>Decomposition</strong> (X→YZ ⇒ X→Y), '
           '<strong>Pseudo-transitivity</strong> (X→Y, WY→Z ⇒ WX→Z)'),
    ),
    example(
        code("""
Relation R(A, B, C, D)   FDs: A → B,  B → C,  C → D

Closure of A (A+):
  start      {A}
  A → B      {A, B}
  B → C      {A, B, C}
  C → D      {A, B, C, D}   = all attributes

A+ contains every attribute, so A is a (candidate) key of R.

Closure of B (B+) = {B, C, D}  → missing A, so B is not a key.
""", 'Finding a candidate key using attribute closure', 'fa-calculator'),
        title='Example: Attribute Closure'),
    crossq(
        ('How do you find candidate keys from a set of FDs?',
         '1) Attributes that never appear on the right side of any FD must be in every key. 2) Compute the closure of '
         'that set. 3) If it covers all attributes it is the key; otherwise add other attributes one by one and keep only minimal sets.'),
        ('What is a minimal (canonical) cover?',
         'The smallest equivalent set of FDs: single attribute on the right side, no extraneous attributes on the left, '
         'and no redundant FD. It is the starting point for 3NF synthesis.'),
        ('Can an FD be discovered by looking at data?',
         'Data can disprove an FD (two rows with the same X and different Y) but cannot prove it — FDs are business '
         'rules that must hold for <em>all</em> possible data, so they come from understanding the domain.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('What is First Normal Form (1NF)?', '1NF', minutes=5, cards=[
    definition(
        defbox('A table is in <strong>First Normal Form</strong> if:'),
        ul('Every column holds <strong>atomic</strong> (indivisible) values — no lists, sets or nested tables in a cell.',
           'There are <strong>no repeating groups</strong> of columns (phone1, phone2, phone3…).',
           'Each column holds values of a single type (one domain).',
           'Each row is unique — the table has a primary key.'),
        tags('1NF', 'Atomic Values', 'Repeating Groups', 'Multivalued'),
    ),
    example(
        code("""
-- ❌ Not in 1NF: multiple values in one cell
+------------+-------+---------------------+
| student_id | name  | courses             |
+------------+-------+---------------------+
| 101        | Asha  | SQL, Spark, Python  |
| 102        | Rohit | SQL                 |
+------------+-------+---------------------+

-- ❌ Also not in 1NF: repeating groups
| student_id | name | course1 | course2 | course3 |
""", 'Violations', 'fa-xmark'),
        code("""
-- ✅ In 1NF: one value per cell, one row per student-course pair
+------------+-------+--------+
| student_id | name  | course |
+------------+-------+--------+
| 101        | Asha  | SQL    |
| 101        | Asha  | Spark  |
| 101        | Asha  | Python |
| 102        | Rohit | SQL    |
+------------+-------+--------+
PRIMARY KEY (student_id, course)
""", 'Fixed', 'fa-check'),
        note('This 1NF table still repeats the name "Asha" — that is a <strong>partial dependency</strong>, removed in 2NF.'),
        title='Example'),
    crossq(
        ('Why are repeating columns (course1, course2, course3) a problem?',
         'A fixed limit (what about a 4th course?), many NULLs, and queries become awkward — "who takes SQL?" must check all three columns.'),
        ('Is a JSON column a violation of 1NF?',
         'Strictly yes, if you query inside it. Modern databases (MySQL JSON type, PostgreSQL JSONB) allow it '
         'pragmatically for semi-structured data, but values you filter, join or aggregate on should be proper columns.'),
        ('Is "address" atomic?',
         'It depends on use. If you only ever display it, one column is fine. If you search by city or pincode, split it — atomicity is relative to how the data is used.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('What is Second Normal Form (2NF)?', '2NF', minutes=6, cards=[
    definition(
        defbox('A table is in <strong>Second Normal Form</strong> if it is in 1NF and has <strong>no partial '
               'dependency</strong> — every non-prime attribute depends on the <strong>whole</strong> of every candidate '
               'key, not on just part of it.',
               '2NF only matters for tables with a <strong>composite key</strong>. A 1NF table with a single-column key is automatically in 2NF.'),
        tags('2NF', 'Partial Dependency', 'Composite Key', 'Full Functional Dependency'),
    ),
    normalize_2nf_3nf(),
    example(
        code("""
enrollments(student_id, course_id, student_name, course_name, grade)
Primary key: (student_id, course_id)

FDs:
  (student_id, course_id) → grade          full dependency    ✅
  student_id              → student_name   partial dependency ❌
  course_id               → course_name    partial dependency ❌
""", 'Not in 2NF', 'fa-xmark'),
        code("""
students(student_id PK, student_name)
courses(course_id PK, course_name)
enrollments(student_id, course_id, grade,  PK(student_id, course_id))
""", 'Decomposed into 2NF', 'fa-check'),
        code("""
CREATE TABLE students (student_id INT PRIMARY KEY, student_name VARCHAR(100));
CREATE TABLE courses  (course_id  INT PRIMARY KEY, course_name  VARCHAR(100));
CREATE TABLE enrollments (
    student_id INT,
    course_id  INT,
    grade      CHAR(2),
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)
);
"""),
        title='Example'),
    interview(
        hl('Rule of thumb: <strong>move each partially dependent attribute into a table keyed by the part of the key it depends on</strong>.', 'How to convert'),
    ),
    crossq(
        ('Can a table with a single-column primary key violate 2NF?',
         'No — partial dependency needs a composite key. (It can still violate 3NF.)'),
        ('Does 2NF consider only the primary key?',
         'The formal definition uses <strong>all candidate keys</strong>: no non-prime attribute may depend on a proper subset of any candidate key.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('What is Third Normal Form (3NF)?', '3NF', minutes=6, cards=[
    definition(
        defbox('A table is in <strong>Third Normal Form</strong> if it is in 2NF and has <strong>no transitive '
               'dependency</strong> — no non-prime attribute depends on another non-prime attribute.',
               'Formal definition: for every non-trivial FD <code>X → A</code>, either X is a super key, or A is a prime attribute.'),
        tags('3NF', 'Transitive Dependency', 'Non-prime Attribute', 'Super Key'),
    ),
    example(
        code("""
students(student_id, name, dept_id, dept_name, hod_name)
Primary key: student_id

FDs:
  student_id → name, dept_id
  dept_id    → dept_name, hod_name       (non-key → non-key)

So student_id → dept_id → dept_name   is a TRANSITIVE dependency ❌
Problem: dept_name and hod_name repeat for every student of the department.
""", 'Not in 3NF', 'fa-xmark'),
        code("""
students(student_id PK, name, dept_id FK)
departments(dept_id PK, dept_name, hod_name)
""", 'Decomposed into 3NF', 'fa-check'),
        title='Example'),
    visual(svg("""
<svg width="720" height="210" viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="720" height="210" fill="#1e293b"/>
  <g font-size="14" text-anchor="middle">
    <rect x="40" y="70" width="150" height="50" rx="8" fill="#fbbf24" opacity="0.25" stroke="#fbbf24" stroke-width="2"/><text x="115" y="100" fill="#fde68a" font-weight="bold">student_id</text>
    <rect x="285" y="70" width="150" height="50" rx="8" fill="#334155" stroke="#0ea5e9" stroke-width="2"/><text x="360" y="100" fill="#f1f5f9">dept_id</text>
    <rect x="530" y="70" width="150" height="50" rx="8" fill="#334155" stroke="#ef4444" stroke-width="2"/><text x="605" y="100" fill="#f1f5f9">dept_name</text>
    <line x1="190" y1="95" x2="280" y2="95" stroke="#10b981" stroke-width="3"/><polygon points="280,89 290,95 280,101" fill="#10b981"/>
    <line x1="435" y1="95" x2="525" y2="95" stroke="#ef4444" stroke-width="3"/><polygon points="525,89 535,95 525,101" fill="#ef4444"/>
    <path d="M 115 120 Q 360 200 605 120" stroke="#ef4444" stroke-width="2" fill="none" stroke-dasharray="6,4"/>
    <text x="360" y="185" fill="#fca5a5" font-size="13">transitive: student_id → dept_name (through dept_id)</text>
    <text x="360" y="40" fill="#0ea5e9" font-size="16" font-weight="bold">Transitive dependency</text>
  </g>
</svg>""", 'A non-key attribute (dept_name) depends on another non-key attribute (dept_id) — move it out')),
    crossq(
        ('Is a table in 3NF always free of redundancy?',
         'Almost always for practical designs. The remaining edge case is when a non-key attribute determines part of '
         'a candidate key — that is what BCNF fixes.'),
        ('Why is 3NF usually the target in practice?',
         'It removes nearly all anomalies while always allowing a lossless, dependency-preserving decomposition. '
         'Going further (BCNF, 4NF) gives little extra benefit for most business schemas.'),
        ('Is storing "city" and "pincode" together a 3NF violation?',
         'If pincode → city holds, then student_id → pincode → city is transitive, so strictly yes. Many designs '
         'accept it because a pincode-city lookup table adds a join for little gain — a conscious denormalization.'),
    ),
]),

# ------------------------------------------------------------------ 26
Q('What is BCNF? How is it different from 3NF?', 'BCNF', minutes=7, cards=[
    definition(
        defbox('<strong>Boyce-Codd Normal Form (BCNF)</strong> is a stricter version of 3NF: for every non-trivial '
               'functional dependency <code>X → Y</code>, <strong>X must be a super key</strong>.',
               '3NF allows <code>X → A</code> when A is a prime attribute even if X is not a key. BCNF removes that '
               'exception. It matters only when a table has <strong>multiple overlapping composite candidate keys</strong>.'),
        hl('3NF: "every determinant is a key <em>or</em> the dependent is prime". BCNF: "every determinant is a key". Full stop.', 'Difference in one line'),
        tags('BCNF', '3.5NF', 'Determinant', 'Super Key', 'Overlapping Candidate Keys'),
    ),
    example(
        code("""
course_teaching(student, subject, teacher)

Rules:
  • Each teacher teaches only one subject:        teacher → subject
  • For a subject, a student has one teacher:      (student, subject) → teacher

Candidate keys: (student, subject) and (student, teacher)
Prime attributes: student, subject, teacher  (all of them)

3NF?  teacher → subject : subject is prime  → allowed ✅ in 3NF
BCNF? teacher is NOT a super key            → violates BCNF ❌

+---------+---------+------------+
| student | subject | teacher    |
+---------+---------+------------+
| Asha    | SQL     | Prof. Rao  |
| Rohit   | SQL     | Prof. Rao  |   ← "Prof. Rao teaches SQL" repeated
| Asha    | Spark   | Prof. Iyer |
+---------+---------+------------+
""", 'In 3NF but not in BCNF', 'fa-xmark'),
        code("""
teacher_subject(teacher PK, subject)
student_teacher(student, teacher,  PK(student, teacher))
""", 'BCNF decomposition', 'fa-check'),
        warn('This BCNF decomposition <strong>loses the dependency</strong> (student, subject) → teacher — it can no '
             'longer be checked inside one table. This is the classic trade-off: BCNF is not always dependency-preserving.', 'Trade-off'),
        title='Example'),
    crossq(
        ('Is every BCNF relation in 3NF?',
         'Yes. BCNF ⊂ 3NF. But not every 3NF relation is in BCNF.'),
        ('Why is BCNF sometimes called 3.5NF?',
         'Because it sits between 3NF and 4NF — stronger than 3NF, but deals only with functional dependencies, not multi-valued ones.'),
        ('Is a relation with only two attributes always in BCNF?',
         'Yes. Any two-attribute relation is in BCNF, whichever FDs hold.'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('What are 4NF and 5NF?', '4NF & 5NF', minutes=6, cards=[
    definition(
        defbox('<strong>Fourth Normal Form (4NF)</strong>: the table is in BCNF and has no non-trivial '
               '<strong>multi-valued dependency (MVD)</strong> other than on a super key. An MVD <code>X →→ Y</code> '
               'means X determines a <em>set</em> of Y values independently of the other attributes.',
               '<strong>Fifth Normal Form (5NF / PJNF)</strong>: the table is in 4NF and cannot be decomposed further '
               'without loss — every <strong>join dependency</strong> is implied by its candidate keys.'),
        tags('4NF', '5NF', 'Multi-valued Dependency', 'Join Dependency', 'PJNF'),
    ),
    example(
        code("""
faculty_info(faculty, subject, language)
-- A faculty teaches several subjects AND speaks several languages.
-- Subjects and languages are independent of each other.

+-----------+---------+----------+
| faculty   | subject | language |
+-----------+---------+----------+
| Prof. Rao | SQL     | English  |
| Prof. Rao | SQL     | Hindi    |
| Prof. Rao | Spark   | English  |
| Prof. Rao | Spark   | Hindi    |   ← every combination must be stored
+-----------+---------+----------+
faculty →→ subject   and   faculty →→ language
Adding a language means adding one row per subject.  ❌ Not in 4NF
""", 'Not in 4NF', 'fa-xmark'),
        code("""
faculty_subject(faculty, subject)      PK(faculty, subject)
faculty_language(faculty, language)   PK(faculty, language)
""", '4NF decomposition', 'fa-check'),
        title='Example: 4NF'),
    explanation(
        p('<strong>5NF example</strong> — agent, company, product: "an agent sells a product for a company" only when '
          'the agent represents the company, the agent sells that product type, and the company makes the product. '
          'If this rule holds, the 3-column table can be split into three 2-column tables '
          '(agent-company, agent-product, company-product) and rejoined without loss. If the rule does not hold, the 3-column table is already in 5NF.'),
        note('4NF and 5NF are rarely needed in day-to-day design. For interviews, be able to define them and give the faculty-subject-language example for 4NF.'),
    ),
    crossq(
        ('What is the difference between an FD and an MVD?',
         'An FD <code>X → Y</code> says X determines exactly one Y value. An MVD <code>X →→ Y</code> says X determines a '
         'set of Y values, independent of the remaining attributes. Every FD is also an MVD.'),
        ('What is 6NF?',
         'Each table holds the key plus at most one other attribute. Used in temporal databases and in Data Vault / '
         'anchor modelling, not in typical OLTP design.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('What is Denormalization? When should you use it?', 'Denormalization', minutes=6, cards=[
    definition(
        defbox('<strong>Denormalization</strong> is the deliberate introduction of controlled redundancy into a '
               'normalized design — combining tables or copying columns — to <strong>reduce joins and speed up reads</strong>.',
               'It is a performance decision made <em>after</em> normalizing, not a reason to skip normalization.'),
        tags('Denormalization', 'Read Performance', 'Redundancy', 'Data Warehouse', 'Star Schema'),
    ),
    comparison(
        table(['Aspect', 'Normalization', 'Denormalization'], [
            ['Goal', 'Remove redundancy & anomalies', 'Faster reads, simpler queries'],
            ['Tables', 'More, smaller tables', 'Fewer, wider tables'],
            ['Joins', 'Many', 'Few'],
            ['Writes', 'Fast and simple', 'Slower — duplicates must be kept in sync'],
            ['Storage', 'Less', 'More'],
            ['Integrity', 'Easy to maintain', 'Risk of inconsistency'],
            ['Best for', 'OLTP — banking, orders, ERP', 'OLAP — reporting, dashboards, data warehouses'],
        ]),
    ),
    example(
        code("""
-- Techniques
-- 1) Store a copied column to avoid a join
ALTER TABLE orders ADD COLUMN customer_name VARCHAR(100);

-- 2) Store a pre-computed aggregate
ALTER TABLE customers ADD COLUMN total_orders INT DEFAULT 0;

-- 3) Summary / reporting table refreshed by a scheduled job
CREATE TABLE daily_sales_summary AS
SELECT DATE(order_date) AS sale_date, product_id,
       SUM(qty) AS units, SUM(qty * price) AS revenue
FROM order_items oi JOIN orders o USING (order_id)
GROUP BY DATE(order_date), product_id;

-- 4) Flatten dimensions in a warehouse (star schema)
-- dim_product(product_key, product_name, category_name, brand_name)
"""),
        title='Example: Common Denormalization Techniques'),
    crossq(
        ('How do you keep denormalized data consistent?',
         'Triggers, application logic in the same transaction, scheduled ETL refreshes, materialized views, or '
         'change-data-capture pipelines that update the copies.'),
        ('Why is data in a data lake / warehouse often denormalized?',
         'Analytical queries scan millions of rows; joins across huge tables are expensive, especially in distributed '
         'engines like Spark or BigQuery. Wide, denormalized tables in columnar formats (Parquet) are much faster to scan.'),
    ),
]),

])
