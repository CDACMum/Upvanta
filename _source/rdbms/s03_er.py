from build import *

SECTION = dict(level='intermediate', title='ER Modelling & Relationships', questions=[

# ------------------------------------------------------------------ 14
Q('What are the types of relationships between tables? (1:1, 1:N, M:N)', 'Relationship Types', minutes=7, cards=[
    definition(
        defbox('A <strong>relationship</strong> describes how rows of one table are associated with rows of another. '
               'Its <strong>cardinality</strong> states how many rows on each side can be linked.'),
        table(['Type', 'Meaning', 'Example', 'How it is implemented'], [
            ['One-to-One (1:1)', 'One row ↔ at most one row', 'Student ↔ Hostel locker', 'FK with UNIQUE constraint on either side'],
            ['One-to-Many (1:N)', 'One parent ↔ many children', 'Department → Students', 'FK in the "many" (child) table'],
            ['Many-to-One (N:1)', 'Same as 1:N viewed from the child side', 'Students → Department', 'FK in the child table'],
            ['Many-to-Many (M:N)', 'Many ↔ many', 'Students ↔ Courses', 'A separate junction (bridge) table'],
        ]),
        tags('Cardinality', 'One-to-One', 'One-to-Many', 'Many-to-Many', 'Junction Table'),
    ),
    example(
        code("""
-- 1:N  One department has many students
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    dept_id    INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- 1:1  One student has at most one locker
CREATE TABLE lockers (
    locker_no  INT PRIMARY KEY,
    student_id INT UNIQUE,                -- UNIQUE makes it 1:1
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- M:N  Students take many courses; courses have many students
CREATE TABLE enrollments (
    student_id INT,
    course_id  INT,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)
);
"""),
        title='Example: All Three in SQL'),
    visual(svg("""
<svg width="760" height="300" viewBox="0 0 760 300" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="300" fill="#1e293b"/>
  <g font-size="14" text-anchor="middle">
    <rect x="30" y="40" width="150" height="44" rx="8" fill="#334155" stroke="#0ea5e9" stroke-width="2"/><text x="105" y="67" fill="#f1f5f9">Student</text>
    <rect x="310" y="40" width="150" height="44" rx="8" fill="#334155" stroke="#0ea5e9" stroke-width="2"/><text x="385" y="67" fill="#f1f5f9">Locker</text>
    <line x1="180" y1="62" x2="310" y2="62" stroke="#fbbf24" stroke-width="2"/>
    <text x="245" y="55" fill="#fbbf24" font-size="13">1 : 1</text>

    <rect x="30" y="125" width="150" height="44" rx="8" fill="#334155" stroke="#10b981" stroke-width="2"/><text x="105" y="152" fill="#f1f5f9">Department</text>
    <rect x="310" y="125" width="150" height="44" rx="8" fill="#334155" stroke="#10b981" stroke-width="2"/><text x="385" y="152" fill="#f1f5f9">Student</text>
    <line x1="180" y1="147" x2="310" y2="147" stroke="#fbbf24" stroke-width="2"/>
    <line x1="295" y1="147" x2="310" y2="135" stroke="#fbbf24" stroke-width="2"/><line x1="295" y1="147" x2="310" y2="159" stroke="#fbbf24" stroke-width="2"/>
    <text x="245" y="140" fill="#fbbf24" font-size="13">1 : N</text>

    <rect x="30" y="215" width="150" height="44" rx="8" fill="#334155" stroke="#8b5cf6" stroke-width="2"/><text x="105" y="242" fill="#f1f5f9">Student</text>
    <rect x="300" y="215" width="170" height="44" rx="8" fill="#8b5cf6" opacity="0.3" stroke="#8b5cf6" stroke-width="2"/><text x="385" y="242" fill="#f1f5f9">Enrollment</text>
    <rect x="590" y="215" width="150" height="44" rx="8" fill="#334155" stroke="#8b5cf6" stroke-width="2"/><text x="665" y="242" fill="#f1f5f9">Course</text>
    <line x1="180" y1="237" x2="300" y2="237" stroke="#fbbf24" stroke-width="2"/>
    <line x1="470" y1="237" x2="590" y2="237" stroke="#fbbf24" stroke-width="2"/>
    <text x="240" y="230" fill="#fbbf24" font-size="13">1 : N</text><text x="530" y="230" fill="#fbbf24" font-size="13">N : 1</text>
    <text x="385" y="285" fill="#94a3b8" font-size="12">M : N is always broken into two 1 : N relationships through a junction table</text>
  </g>
</svg>""", 'How each relationship type is physically implemented')),
    crossq(
        ('Why can\'t M:N be implemented with a foreign key directly?',
         'A column can hold only one value per row (1NF). To link one student to five courses you would need a list '
         'inside a cell or five columns — both violate good design. The junction table holds one row per pair.'),
        ('When would you use a 1:1 relationship instead of one table?',
         'To separate rarely-used or large columns (e.g. a profile photo), sensitive columns with different access '
         'rights (e.g. salary details), or optional data that most rows do not have.'),
        ('Can a junction table have its own columns?',
         'Yes — attributes of the relationship itself, like <code>enrolled_on</code>, <code>grade</code> or '
         '<code>fee_paid</code>, belong in the junction table.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do you implement a Many-to-Many relationship?', 'Many-to-Many & Junction Table', minutes=6, cards=[
    definition(
        defbox('A many-to-many relationship is implemented with a third table called a <strong>junction</strong>, '
               '<strong>bridge</strong>, <strong>associative</strong> or <strong>link</strong> table. It contains a '
               'foreign key to each side, and the combination of the two is usually its primary key.'),
        tags('Junction Table', 'Bridge Table', 'Associative Entity', 'Composite Key', 'M:N'),
    ),
    example(
        code("""
CREATE TABLE students (student_id INT PRIMARY KEY, name VARCHAR(100));
CREATE TABLE courses  (course_id  INT PRIMARY KEY, title VARCHAR(100));

CREATE TABLE enrollments (
    student_id  INT,
    course_id   INT,
    enrolled_on DATE,
    grade       CHAR(2),
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)
);

INSERT INTO students VALUES (101,'Asha'), (102,'Rohit');
INSERT INTO courses  VALUES (1,'SQL'), (2,'Spark'), (3,'Python');
INSERT INTO enrollments VALUES (101,1,'2026-08-01','A'), (101,2,'2026-08-01','B'),
                               (102,1,'2026-08-02','A'), (102,3,'2026-08-02','A');

-- Which courses has each student taken?
SELECT s.name, c.title, e.grade
FROM students s
JOIN enrollments e ON e.student_id = s.student_id
JOIN courses c     ON c.course_id  = e.course_id
ORDER BY s.name;
"""),
        output("""
+-------+--------+-------+
| name  | title  | grade |
+-------+--------+-------+
| Asha  | SQL    | A     |
| Asha  | Spark  | B     |
| Rohit | SQL    | A     |
| Rohit | Python | A     |
+-------+--------+-------+
"""),
        title='Example: Students and Courses'),
    interview(
        hl('If the same pair can occur more than once (a student re-taking a course), the composite key is not enough. '
           'Add a surrogate key (<code>enrollment_id</code>) or include the term/attempt in the key: '
           '<code>PRIMARY KEY (student_id, course_id, term)</code>.', 'Follow-up interviewers like'),
        p('Also index the <strong>second</strong> column of the composite key separately (<code>INDEX(course_id)</code>) '
          'so that "all students in course X" queries are fast — the composite index only helps lookups that start with <code>student_id</code>.'),
    ),
    crossq(
        ('Name some real-world many-to-many relationships.',
         'Students–Courses, Authors–Books, Products–Orders (order_items), Actors–Movies, Users–Roles, Doctors–Patients.'),
        ('How is M:N represented in a NoSQL document database?',
         'Usually by embedding an array of ids in one or both documents (e.g. a <code>course_ids</code> array in the '
         'student document), accepting some duplication in exchange for fewer joins.'),
    ),
]),

# ------------------------------------------------------------------ 16
Q('What is an ER Diagram? Explain entity, attribute and relationship', 'ER Diagram Basics', minutes=7, cards=[
    definition(
        defbox('An <strong>Entity-Relationship (ER) diagram</strong> is a visual model of the data in a system, '
               'introduced by Peter Chen in 1976. It is drawn during <strong>conceptual design</strong>, before any '
               'tables are created, and is later converted into a relational schema.'),
        table(['Concept', 'Meaning', 'Chen notation symbol'], [
            ['Entity', 'A real-world object with independent existence (Student, Course)', 'Rectangle'],
            ['Weak entity', 'Entity that depends on another for identification', 'Double rectangle'],
            ['Attribute', 'Property of an entity (name, email)', 'Ellipse'],
            ['Key attribute', 'Uniquely identifies the entity', 'Ellipse with underlined name'],
            ['Multivalued attribute', 'Can hold several values (phone numbers)', 'Double ellipse'],
            ['Derived attribute', 'Calculated from others (age from DOB)', 'Dashed ellipse'],
            ['Relationship', 'Association between entities (Enrolls)', 'Diamond'],
        ]),
        tags('ER Diagram', 'Entity', 'Attribute', 'Relationship', 'Chen Notation', 'Crow\'s Foot'),
    ),
    visual(svg("""
<svg width="760" height="300" viewBox="0 0 760 300" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="300" fill="#1e293b"/>
  <g font-size="13" text-anchor="middle" fill="#f1f5f9">
    <rect x="70" y="130" width="140" height="50" fill="#0ea5e9" opacity="0.3" stroke="#0ea5e9" stroke-width="2"/><text x="140" y="160" font-weight="bold">STUDENT</text>
    <polygon points="380,115 450,155 380,195 310,155" fill="#fbbf24" opacity="0.25" stroke="#fbbf24" stroke-width="2"/><text x="380" y="160" font-weight="bold">ENROLLS</text>
    <rect x="550" y="130" width="140" height="50" fill="#0ea5e9" opacity="0.3" stroke="#0ea5e9" stroke-width="2"/><text x="620" y="160" font-weight="bold">COURSE</text>
    <line x1="210" y1="155" x2="310" y2="155" stroke="#cbd5e1" stroke-width="2"/><text x="255" y="148" fill="#fbbf24">M</text>
    <line x1="450" y1="155" x2="550" y2="155" stroke="#cbd5e1" stroke-width="2"/><text x="505" y="148" fill="#fbbf24">N</text>
    <ellipse cx="60" cy="60" rx="55" ry="22" fill="none" stroke="#10b981" stroke-width="2"/><text x="60" y="65" text-decoration="underline">student_id</text>
    <ellipse cx="190" cy="50" rx="45" ry="22" fill="none" stroke="#10b981" stroke-width="2"/><text x="190" y="55">name</text>
    <ellipse cx="70" cy="250" rx="60" ry="22" fill="none" stroke="#10b981" stroke-width="2"/><ellipse cx="70" cy="250" rx="54" ry="17" fill="none" stroke="#10b981" stroke-width="1.5"/><text x="70" y="255">phone</text>
    <ellipse cx="210" cy="255" rx="40" ry="22" fill="none" stroke="#10b981" stroke-width="2" stroke-dasharray="5,4"/><text x="210" y="260">age</text>
    <line x1="80" y1="80" x2="115" y2="130" stroke="#64748b"/><line x1="180" y1="72" x2="160" y2="130" stroke="#64748b"/>
    <line x1="90" y1="228" x2="115" y2="180" stroke="#64748b"/><line x1="200" y1="233" x2="170" y2="180" stroke="#64748b"/>
    <ellipse cx="380" cy="60" rx="45" ry="22" fill="none" stroke="#10b981" stroke-width="2"/><text x="380" y="65">grade</text>
    <line x1="380" y1="82" x2="380" y2="115" stroke="#64748b"/>
    <ellipse cx="620" cy="60" rx="55" ry="22" fill="none" stroke="#10b981" stroke-width="2"/><text x="620" y="65" text-decoration="underline">course_id</text>
    <ellipse cx="660" cy="250" rx="45" ry="22" fill="none" stroke="#10b981" stroke-width="2"/><text x="660" y="255">title</text>
    <line x1="620" y1="82" x2="620" y2="130" stroke="#64748b"/><line x1="650" y1="228" x2="640" y2="180" stroke="#64748b"/>
    <text x="470" y="292" fill="#94a3b8" font-size="12">underlined = key · double = multivalued · dashed = derived</text>
  </g>
</svg>""", 'Chen-notation ER diagram: STUDENT —M:N— COURSE through the ENROLLS relationship')),
    explanation(
        p('<strong>Converting an ER diagram to tables</strong> (the most-asked follow-up):'),
        ul('Each <strong>strong entity</strong> → a table; key attribute → primary key.',
           '<strong>Composite attribute</strong> (address) → one column per part (street, city, pin).',
           '<strong>Multivalued attribute</strong> (phones) → a separate table <code>student_phones(student_id, phone)</code>.',
           '<strong>Derived attribute</strong> (age) → usually not stored; calculate it in a query or view.',
           '<strong>1:N relationship</strong> → FK in the N-side table.',
           '<strong>M:N relationship</strong> → junction table; relationship attributes (grade) go there.',
           '<strong>Weak entity</strong> → table whose PK = owner\'s PK + partial key.'),
    ),
    crossq(
        ('What is the difference between Chen notation and Crow\'s Foot notation?',
         'Chen uses rectangles, ellipses and diamonds — good for teaching concepts. <strong>Crow\'s Foot</strong> draws '
         'tables as boxes with their columns and shows cardinality with symbols at line ends (a "crow\'s foot" for many). '
         'Tools like MySQL Workbench, dbdiagram.io and ERwin use Crow\'s Foot.'),
        ('What is an entity set vs an entity?',
         'An <strong>entity</strong> is one object (student Asha). The <strong>entity set</strong> is the collection '
         'of all entities of that type (all students) — it becomes the table.'),
        ('What is an EER diagram?',
         'Enhanced ER adds specialisation/generalisation (Employee → Faculty, Staff), inheritance and categories. '
         'MySQL Workbench calls its diagrams "EER diagrams".'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('What are the types of attributes in an ER model?', 'Attribute Types', minutes=5, cards=[
    definition(
        table(['Attribute type', 'Description', 'Example', 'In tables'], [
            ['Simple (atomic)', 'Cannot be divided further', 'roll_no, gender', 'One column'],
            ['Composite', 'Made of sub-parts', 'address → street, city, pin', 'One column per part'],
            ['Single-valued', 'One value per entity', 'date_of_birth', 'One column'],
            ['Multivalued', 'Several values per entity', 'phone numbers, skills', 'Separate table'],
            ['Derived', 'Computed from other attributes', 'age (from DOB), total_marks', 'Not stored — computed'],
            ['Stored', 'Physically saved; others are derived from it', 'date_of_birth', 'Column'],
            ['Key', 'Uniquely identifies the entity', 'student_id', 'Primary key'],
            ['Complex', 'Composite + multivalued', 'multiple addresses, each with parts', 'Separate table with part columns'],
        ]),
        tags('Simple Attribute', 'Composite Attribute', 'Multivalued', 'Derived', 'Key Attribute'),
    ),
    example(
        code("""
-- Composite attribute 'address' split into parts
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name       VARCHAR(100),
    dob        DATE,               -- stored
    street     VARCHAR(100),
    city       VARCHAR(50),
    pincode    CHAR(6)
);

-- Multivalued attribute 'phone' → its own table
CREATE TABLE student_phones (
    student_id INT,
    phone      VARCHAR(15),
    PRIMARY KEY (student_id, phone),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Derived attribute 'age' computed when needed
SELECT name, TIMESTAMPDIFF(YEAR, dob, CURDATE()) AS age FROM students;
"""),
        title='Example: Mapping Attributes to Tables'),
    crossq(
        ('Why should derived attributes usually not be stored?',
         'They become stale — age changes every year, total marks change when one mark is corrected. Store the base '
         'value and compute. Exception: when computation is expensive and the value is read very often (then keep it '
         'updated with a trigger or a generated column).'),
        ('What is a generated (computed) column?',
         'A column whose value is computed from an expression: <code>total INT AS (theory + practical) STORED</code>. '
         'MySQL supports VIRTUAL (computed on read) and STORED (saved on write) generated columns.'),
    ),
]),

# ------------------------------------------------------------------ 18
Q('What is the difference between a Strong Entity and a Weak Entity?', 'Strong vs Weak Entity', minutes=5, cards=[
    definition(
        defbox('A <strong>strong entity</strong> has its own key attribute and can be identified independently '
               '(e.g. Employee with emp_id).',
               'A <strong>weak entity</strong> cannot be uniquely identified by its own attributes alone. It depends on '
               'a strong (owner/identifying) entity, and is identified by the owner\'s key plus its own '
               '<strong>partial key (discriminator)</strong>.'),
        tags('Strong Entity', 'Weak Entity', 'Partial Key', 'Discriminator', 'Identifying Relationship'),
    ),
    comparison(
        table(['Aspect', 'Strong entity', 'Weak entity'], [
            ['Own primary key', 'Yes', 'No — only a partial key'],
            ['Existence', 'Independent', 'Depends on the owner entity'],
            ['ER symbol', 'Single rectangle', 'Double rectangle'],
            ['Relationship to owner', 'Normal (single diamond)', 'Identifying (double diamond)'],
            ['Participation', 'Partial or total', 'Always total in the identifying relationship'],
            ['Example', 'Employee, Order, Building', 'Dependent, Order line, Room'],
        ]),
    ),
    example(
        code("""
-- Owner (strong) entity
CREATE TABLE employees (
    emp_id INT PRIMARY KEY,
    name   VARCHAR(100)
);

-- Weak entity: a dependent is identified by (emp_id, dependent_name)
CREATE TABLE dependents (
    emp_id         INT,
    dependent_name VARCHAR(100),      -- partial key
    relation       VARCHAR(20),
    PRIMARY KEY (emp_id, dependent_name),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id) ON DELETE CASCADE
);
"""),
        note('<code>ON DELETE CASCADE</code> fits naturally: if the employee leaves, the dependent records have no meaning on their own.'),
        title='Example: Employee and Dependents'),
    crossq(
        ('Give more examples of weak entities.',
         'Room (identified by building + room no.), Installment (loan + installment no.), Order line (order + line no.), '
         'Chapter (book + chapter no.).'),
        ('If we add a surrogate id to a weak entity, is it still weak?',
         'Physically it now has its own key, so in the table design it behaves like a strong entity. Conceptually it is '
         'still existence-dependent on its owner. Many real systems add surrogate ids for convenience.'),
    ),
]),

# ------------------------------------------------------------------ 19
Q('What is the difference between Cardinality and Participation?', 'Cardinality vs Participation', minutes=6, cards=[
    definition(
        defbox('<strong>Cardinality (cardinality ratio)</strong> — the <em>maximum</em> number of entities that can be '
               'associated through a relationship: 1:1, 1:N or M:N.',
               '<strong>Participation (modality / optionality)</strong> — the <em>minimum</em>: whether every entity '
               '<strong>must</strong> take part in the relationship (<strong>total</strong>) or <strong>may</strong> '
               'take part (<strong>partial</strong>).'),
        hl('Cardinality answers "how many at most?"; participation answers "is it mandatory?"', 'In one line'),
        tags('Cardinality', 'Participation', 'Total', 'Partial', 'Min-Max Notation', 'Optionality'),
    ),
    example(
        table(['Statement', 'Cardinality', 'Participation'], [
            ['Every student must belong to exactly one department', 'N:1', 'Student: total · Department: partial (a new department may have no students yet)'],
            ['An employee may manage at most one department; every department has one manager', '1:1', 'Employee: partial · Department: total'],
            ['A student can enroll in many courses; a course can have many students', 'M:N', 'Both partial'],
        ]),
        code("""
-- Total participation of student in 'belongs to' → FK is NOT NULL
CREATE TABLE students (
    student_id INT PRIMARY KEY,
    dept_id    INT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

-- Partial participation → FK can be NULL
CREATE TABLE employees (
    emp_id    INT PRIMARY KEY,
    mentor_id INT NULL,
    FOREIGN KEY (mentor_id) REFERENCES employees(emp_id)
);
""", 'How participation shows up in SQL'),
        title='Example'),
    explanation(
        p('<strong>Notations:</strong>'),
        ul('<strong>Chen</strong>: total participation = double line, partial = single line.',
           '<strong>Min-max</strong>: (min, max) on each side, e.g. Student (1,1) — Department (0,N).',
           '<strong>Crow\'s Foot</strong>: a bar (|) means "one / mandatory", a circle (○) means "zero / optional", '
           'and the crow\'s foot means "many". "|<" reads "one or many", "○<" reads "zero or many".'),
    ),
    crossq(
        ('What is existence dependency?',
         'When an entity cannot exist without another — it implies total participation. Weak entities are always existence-dependent on their owner.'),
        ('How do you enforce "a department must have at least one student" in SQL?',
         'Standard constraints cannot enforce a minimum of one child. You need application logic, a trigger, or a '
         'deferred check. This is why total participation on the "1" side is usually enforced outside the schema.'),
    ),
]),

])
