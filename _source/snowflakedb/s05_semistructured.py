from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq

SUBMISSIONS = '''
CREATE OR REPLACE TABLE submissions (v VARIANT, src_file VARCHAR);
INSERT INTO submissions
SELECT PARSE_JSON(column1), column2 FROM VALUES
 ('{"roll":2401,"name":"Anuj","centre":"Kharghar","contact":{"city":"Panvel","phone":null},
    "exams":[{"sub":"SQL","m":78},{"sub":"Spark","m":82}],"submitted":"2026-02-15T10:42:00"}', 'sub_0215_kh.json'),
 ('{"roll":2402,"name":"Aarshvi","centre":"Juhu","contact":{"city":"Andheri","phone":"98200 12345"},
    "exams":[{"sub":"SQL","m":91},{"sub":"Spark","m":88},{"sub":"Python","m":95}],"submitted":"2026-02-15T11:05:00"}', 'sub_0215_ju.json'),
 ('{"roll":2403,"name":"Riya","centre":"Kharghar","contact":{"city":"Vashi"},
    "exams":[{"sub":"SQL","m":84}],"submitted":"2026-02-15T11:30:00"}', 'sub_0215_kh.json');
'''

SECTION = dict(level='intermediate', title='Semi-structured Data (JSON, VARIANT)', questions=[

# ------------------------------------------------------------------ 21
Q('What is the VARIANT data type? How do you query JSON stored in Snowflake?', 'VARIANT & Path Queries', minutes=9, cards=[
    definition(
        defbox('Snowflake has three semi-structured types: <strong>VARIANT</strong> (any value: object, array, string, number, boolean, null), '
               '<strong>OBJECT</strong> (key–value pairs) and <strong>ARRAY</strong>. JSON, Avro, ORC, Parquet and XML can all be loaded into '
               'VARIANT columns without defining a schema first.',
               'Navigate with <code>col:key</code> (or <code>col[\'key\']</code>), <code>.key</code> for deeper levels and <code>[n]</code> for array '
               'elements (zero-based). The result is still VARIANT, so strings print with double quotes; cast with <code>::STRING</code>, '
               '<code>::INT</code>, <code>::TIMESTAMP_NTZ</code> and so on. A missing key returns SQL NULL. A JSON <code>null</code> is a '
               'VARIANT null, which is <strong>not</strong> SQL NULL (test it with <code>IS_NULL_VALUE</code>).'),
        tags('VARIANT', 'OBJECT', 'ARRAY', 'PARSE_JSON', 'col:key', '::cast', 'IS_NULL_VALUE', 'Schema-on-read'),
    ),
    analogy('A VARIANT column is a <strong>filing cabinet drawer</strong> that accepts any shape of document. The path <code>v:contact.city</code> '
            'is like saying "open the contact folder and read the city line", and the cast is copying that line onto a typed form.'),
    variant_anim(),
    real_world(
        scenario('Online exam submissions',
                 p('The exam portal sends one JSON document per candidate: identity, contact details, an array of subject marks and a submission '
                   'time. Different exams add new fields over time. Landing them in a VARIANT column means loads never fail when a field is added; '
                   'queries pick out the fields they need.')),
    ),
    example(
        sql(SUBMISSIONS + '''
SELECT v:roll::INT               AS roll_no,
       v:name                    AS name_variant,
       v:name::STRING            AS name,
       v:contact.city::STRING    AS city,
       v:exams[0].sub::STRING    AS first_subject,
       v:submitted::TIMESTAMP_NTZ AS submitted_at,
       ARRAY_SIZE(v:exams)       AS exams_taken
FROM   submissions
ORDER  BY roll_no;

-- three kinds of "nothing": a JSON null, a missing key, and a real value
SELECT v:roll::INT                        AS roll_no,
       v:contact.phone                    AS phone,
       v:contact.phone IS NULL            AS is_sql_null,
       IS_NULL_VALUE(v:contact.phone)     AS is_json_null
FROM   submissions
ORDER  BY roll_no;
''', data=False, show='queries'),
        p('Anuj\'s phone is a JSON <code>null</code>: not SQL NULL, but <code>IS_NULL_VALUE</code> is TRUE. Riya has no phone key at all, so the '
          'path returns SQL NULL. <code>NAME_VARIANT</code> keeps its quotes because it is still a VARIANT.', top=True),
        title='Example'),
    steps(
        ('Create a VARIANT column', '<code>CREATE TABLE raw (v VARIANT, src_file VARCHAR, loaded_at TIMESTAMP_LTZ);</code>'),
        ('Load JSON', '<code>COPY INTO raw (v) FROM @stage FILE_FORMAT = (TYPE = JSON)</code>, or <code>PARSE_JSON</code> on strings.'),
        ('Explore', 'Select a few rows, look at keys with <code>OBJECT_KEYS(v)</code> or by flattening.'),
        ('Query with paths and casts', 'Always cast to the type you need before comparing or aggregating.'),
        title='Steps'),
    crossq(
        ('Why cast? The value is already 2401.', 'Without a cast it is a VARIANT holding a number. Comparisons and joins with typed columns, '
         'arithmetic and sorting are clearer and safer on the cast value, and string values lose their quotes.'),
        ('What if a key name has spaces or special characters?', 'Use double quotes in the path, <code>v:"exam date"</code>, or bracket notation '
         '<code>v[\'exam date\']</code>. Key names in paths are case-sensitive.'),
        ('What does PARSE_JSON do with invalid JSON?', 'It raises an error. <code>TRY_PARSE_JSON</code> returns NULL instead, useful for cleaning '
         'raw text.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What does LATERAL FLATTEN do? How do you turn a JSON array into rows?', 'FLATTEN', minutes=9, cards=[
    definition(
        defbox('<code>FLATTEN</code> is a table function that explodes an array or object into one row per element (or per key). Used with '
               '<code>LATERAL</code> (or a comma join), it is evaluated once for each row of the table on its left, and its output rows are joined '
               'back to that parent row.',
               'Output columns: <code>SEQ</code> (input row sequence), <code>KEY</code> (for objects), <code>PATH</code>, <code>INDEX</code> (for arrays), '
               '<code>VALUE</code> (the element) and <code>THIS</code> (the array/object being flattened). Options: <code>OUTER => TRUE</code> keeps '
               'parent rows whose array is empty or missing (like a LEFT JOIN); <code>RECURSIVE => TRUE</code> expands every nested level; '
               '<code>PATH => \'…\'</code> starts at a sub-path.'),
        tags('FLATTEN', 'LATERAL', 'VALUE', 'INDEX', 'OUTER', 'RECURSIVE', 'Explode'),
    ),
    analogy('A parent row is a <strong>tiffin box with compartments</strong>. FLATTEN puts each compartment\'s food on its own plate, and writes the '
            'owner\'s name on every plate so you still know whose lunch it is.'),
    flatten_anim(),
    real_world(
        scenario('Subject-wise results',
                 p('Each submission holds an array of subject marks. Reporting needs one row per student per subject to compute subject averages, '
                   'pass counts and toppers. FLATTEN turns three JSON documents into six subject rows that can be grouped like any table.')),
    ),
    example(
        sql(SUBMISSIONS + '''
-- one row per student per subject
SELECT s.v:roll::INT           AS roll_no,
       s.v:name::STRING        AS name,
       e.index                 AS idx,
       e.value:sub::STRING     AS subject,
       e.value:m::INT          AS marks
FROM   submissions s,
       LATERAL FLATTEN(input => s.v:exams) e
ORDER  BY roll_no, idx;

-- now it is ordinary SQL: subject-wise statistics
SELECT e.value:sub::STRING              AS subject,
       COUNT(*)                         AS candidates,
       AVG(e.value:m::INT)::NUMBER(5,2) AS avg_marks,
       MAX(e.value:m::INT)              AS best
FROM   submissions s, LATERAL FLATTEN(input => s.v:exams) e
GROUP  BY subject
ORDER  BY subject;

-- flatten an OBJECT: one row per key
SELECT s.v:roll::INT AS roll_no, c.key, c.value
FROM   submissions s, LATERAL FLATTEN(input => s.v:contact) c
ORDER  BY roll_no, c.key;
''', data=False, show='queries'),
        p('Riya\'s contact object has only <code>city</code>, so she contributes one row to the last query. In a real account, add '
          '<code>OUTER => TRUE</code> to keep a student whose array is empty:', top=True),
        sq('''
SELECT s.v:roll::INT AS roll_no, e.value:sub::STRING AS subject
FROM   submissions s, LATERAL FLATTEN(input => s.v:exams, OUTER => TRUE) e;
-- a student with "exams": [] appears once with SUBJECT = NULL instead of disappearing

SELECT f.path, f.key, f.value
FROM   submissions s, LATERAL FLATTEN(input => s.v, RECURSIVE => TRUE) f;   -- every nested element
'''),
        title='Example'),
    steps(
        ('Identify the array path', 'For example <code>v:exams</code>.'),
        ('Add LATERAL FLATTEN', 'In the FROM clause, after the table, with an alias.'),
        ('Select parent and child fields', 'Parent through the table alias, child through <code>alias.value:…</code>.'),
        ('Decide on OUTER', 'Keep parents with empty arrays if the report must list everyone.'),
        ('Nest FLATTENs for arrays inside arrays', 'A second LATERAL FLATTEN on <code>e.value:items</code>, and so on.'),
        title='Steps'),
    crossq(
        ('Why did a student vanish from my flattened result?', 'Their array was empty, NULL or missing. Without <code>OUTER => TRUE</code> FLATTEN '
         'produces no rows for them, and the lateral join drops the parent.'),
        ('Is FLATTEN expensive?', 'It multiplies rows (one per element), so the cost grows with array sizes. For frequent queries, flatten once into a '
         'typed table or dynamic table.'),
        ('How is FLATTEN different from Spark\'s explode?', 'Same idea. FLATTEN also returns INDEX, KEY and PATH, works on objects as well as arrays, and '
         'can recurse.'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How do you build JSON from relational data? Explain OBJECT_CONSTRUCT, ARRAY_AGG and OBJECT_AGG.', 'Building JSON', minutes=7, cards=[
    definition(
        table(['Function', 'Returns'], [
            ['<code>OBJECT_CONSTRUCT(k1, v1, k2, v2 …)</code>', 'An OBJECT from key/value pairs; <code>OBJECT_CONSTRUCT(*)</code> uses all columns. '
             'Pairs with a NULL value are left out (use <code>OBJECT_CONSTRUCT_KEEP_NULL</code> to keep them).'],
            ['<code>ARRAY_CONSTRUCT(v1, v2 …)</code>', 'An ARRAY of the given values'],
            ['<code>ARRAY_AGG(expr) [WITHIN GROUP (ORDER BY …)]</code>', 'Aggregate: an ARRAY of values from the rows in each group'],
            ['<code>OBJECT_AGG(key, value)</code>', 'Aggregate: one OBJECT built from key/value pairs across rows'],
            ['<code>TO_JSON(variant)</code>', 'The JSON text (VARCHAR) of a VARIANT, e.g. for an API body'],
        ]),
        tags('OBJECT_CONSTRUCT', 'ARRAY_CONSTRUCT', 'ARRAY_AGG', 'OBJECT_AGG', 'TO_JSON', 'Nested JSON'),
    ),
    analogy('FLATTEN unpacks a parcel into items on a table; these functions <strong>pack</strong> items from the table back into labelled boxes '
            '(objects) and bags (arrays).'),
    construct_anim(),
    real_world(
        scenario('Feeding the placement portal',
                 p('The placement portal\'s API expects one JSON document per course with an array of eligible students. One query with '
                   '<code>ARRAY_AGG(OBJECT_CONSTRUCT(…))</code> grouped by course produces exactly that payload.')),
    ),
    example(
        sql('''
-- one JSON object per student
SELECT OBJECT_CONSTRUCT('roll', roll_no, 'name', name, 'marks', marks) AS student_json
FROM   students
WHERE  centre = 'Juhu'
ORDER  BY roll_no
LIMIT  2;

-- one document per course, students ordered by marks
SELECT course,
       ARRAY_AGG(OBJECT_CONSTRUCT('name', name, 'marks', marks))
         WITHIN GROUP (ORDER BY marks DESC) AS toppers
FROM   students
WHERE  course = 'PGCP-AI'
GROUP  BY course;

-- name → marks lookup object for one centre
SELECT OBJECT_AGG(name, marks::VARIANT) AS marks_by_name
FROM   students
WHERE  centre = 'Kharghar';
''', show='queries'),
        p('Keys inside each object print in sorted order, as Snowflake stores them, not in the order you wrote them.', top=True),
        title='Example'),
    steps(
        ('Shape each element', 'OBJECT_CONSTRUCT with the fields the consumer expects.'),
        ('Group into arrays', 'ARRAY_AGG … WITHIN GROUP (ORDER BY …) for a stable order.'),
        ('Wrap the document', 'Another OBJECT_CONSTRUCT around the arrays if needed.'),
        ('Deliver', 'Unload with <code>FILE_FORMAT = (TYPE = JSON)</code> or return TO_JSON(…) to an application.'),
        title='Steps'),
    crossq(
        ('Why is a key missing from my OBJECT_CONSTRUCT output?', 'Its value was NULL; OBJECT_CONSTRUCT omits NULL values. Use '
         'OBJECT_CONSTRUCT_KEEP_NULL or wrap the value in COALESCE.'),
        ('Can the order of keys be controlled?', 'No: OBJECT keys are stored and printed in sorted order. Use an ARRAY if order matters.'),
        ('Is there a size limit?', 'Yes, a single VARIANT/OBJECT/ARRAY value has a maximum size (tens of MB). Very large aggregations should be split, '
         'for example one document per course instead of one for the whole institute.'),
    ),
]),

# ------------------------------------------------------------------ 24
Q('How do you load Parquet or Avro files without writing the table schema by hand?', 'INFER_SCHEMA & Schema Evolution', minutes=7, cards=[
    definition(
        defbox('Self-describing formats (Parquet, Avro, ORC, and CSV with a header) contain column names and types. '
               '<code>INFER_SCHEMA</code> reads them from staged files and returns column definitions. '
               '<code>CREATE TABLE … USING TEMPLATE</code> creates a table from that output in one statement.',
               '<code>COPY INTO … MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE</code> loads file columns into table columns by name rather than position. '
               'With <code>ENABLE_SCHEMA_EVOLUTION = TRUE</code> on the table, COPY and Snowpipe can add new columns automatically when files gain '
               'fields (and drop NOT NULL constraints for missing ones).'),
        tags('INFER_SCHEMA', 'USING TEMPLATE', 'MATCH_BY_COLUMN_NAME', 'Schema evolution', 'Parquet', 'Avro'),
    ),
    analogy('Instead of writing the attendance register\'s column headings by hand, you <strong>photocopy the header row</strong> from the first page '
            'of the files you received.'),
    infer_anim(),
    real_world(
        scenario('Data lake export from the LMS',
                 p('The learning-management system exports daily Parquet files with 60 columns. INFER_SCHEMA plus USING TEMPLATE creates the table in '
                   'seconds; schema evolution adds the new <code>video_watch_minutes</code> column when it appears next term without failing the load.')),
    ),
    example(
        sq('''
CREATE FILE FORMAT parquet_ff TYPE = PARQUET;

-- what columns do the files have?
SELECT column_name, type, nullable
FROM   TABLE(INFER_SCHEMA(LOCATION => '@lake_stage/lms/', FILE_FORMAT => 'parquet_ff'));

-- create the table from the files' schema
CREATE TABLE lms_activity USING TEMPLATE (
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
  FROM TABLE(INFER_SCHEMA(LOCATION => '@lake_stage/lms/', FILE_FORMAT => 'parquet_ff')));

ALTER TABLE lms_activity SET ENABLE_SCHEMA_EVOLUTION = TRUE;

COPY INTO lms_activity FROM @lake_stage/lms/
FILE_FORMAT = (FORMAT_NAME = 'parquet_ff')
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

-- CSV with a header can be inferred too
CREATE FILE FORMAT csv_hdr TYPE = CSV PARSE_HEADER = TRUE;
'''),
        p('Alternatively, load each Parquet row as one VARIANT (<code>SELECT $1 FROM @stage</code>) and extract columns later, which never fails on '
          'schema changes.', top=True),
        title='Example (shown, not executed)'),
    steps(
        ('Stage sample files', 'A representative set, including the newest structure.'),
        ('Inspect with INFER_SCHEMA', 'Check names, types and nullability.'),
        ('Create with USING TEMPLATE', 'Adjust types afterwards if needed (e.g. NUMBER scale).'),
        ('Load by name', 'MATCH_BY_COLUMN_NAME, and enable schema evolution if fields will be added.'),
        title='Steps'),
    crossq(
        ('Does MATCH_BY_COLUMN_NAME work with JSON?', 'Yes, for JSON objects whose top-level keys match column names, as well as Parquet, Avro, ORC '
         'and CSV with PARSE_HEADER.'),
        ('What happens to a file column that has no matching table column?', 'It is ignored (unless schema evolution adds it). Table columns with no '
         'matching file column get NULL.'),
        ('When is VARIANT landing better than schema inference?', 'When the structure changes often or is deeply nested; you keep the full record and '
         'decide later which fields to promote to columns.'),
    ),
]),

# ------------------------------------------------------------------ 25
Q('Should semi-structured data stay in VARIANT or be flattened into columns? How does it affect performance?', 'VARIANT vs Columns', minutes=8, cards=[
    definition(
        defbox('When JSON is loaded into VARIANT, Snowflake automatically extracts frequently occurring keys into hidden, columnar '
               '<strong>sub-columns</strong> with their own min/max metadata. Queries on those paths read only that sub-column and can prune '
               'micro-partitions, so VARIANT queries are often close to the speed of normal columns.',
               'This does not happen for every key: keys with mixed types across rows (a number in some rows, a string in others), objects with '
               'very many distinct keys, deep nesting, and arrays are stored less efficiently. Values such as dates stored as strings also cannot '
               'be pruned as dates. Such fields are better extracted into typed columns.'),
        tags('Sub-columns', 'Columnarization', 'Pruning on VARIANT', 'Typed columns', 'Bronze / Silver'),
    ),
    analogy('Keeping everything in VARIANT is like keeping <strong>scanned forms</strong>: complete and flexible, but every lookup needs reading. '
            'Extracting key fields is <strong>typing them into a register</strong>: fast to search, at the cost of a little effort up front.'),
    semi_perf_anim(),
    real_world(
        scenario('Raw + curated layers',
                 p('Submissions stay as VARIANT in <code>RAW.SUBMISSIONS</code> for audit and replay. A typed table <code>CLEAN.EXAM_MARKS</code> '
                   '(roll_no INT, subject VARCHAR, marks INT, submitted_at TIMESTAMP_NTZ) is built from it for reporting. Dashboards query the typed '
                   'table; investigations go to the raw JSON.')),
    ),
    example(
        sql(SUBMISSIONS + '''
-- promote frequently used fields to a typed, flattened table
CREATE OR REPLACE TABLE exam_marks AS
SELECT s.v:roll::INT                AS roll_no,
       s.v:centre::STRING           AS centre,
       e.value:sub::STRING          AS subject,
       e.value:m::INT               AS marks,
       s.v:submitted::TIMESTAMP_NTZ AS submitted_at,
       s.src_file
FROM   submissions s, LATERAL FLATTEN(input => s.v:exams) e;

SELECT centre, subject, COUNT(*) AS n, MAX(marks) AS best
FROM   exam_marks
GROUP  BY ALL
ORDER  BY centre, subject;
''', data=False, show='queries'),
        p('In production this <code>CREATE TABLE AS</code> would be a dynamic table or a stream + task, so the typed table stays in step with the raw '
          'data.', top=True),
        title='Example'),
    steps(
        ('Land raw as VARIANT', 'With file name and load time.'),
        ('Find the hot fields', 'Fields used in filters, joins and GROUP BY; dates and IDs first.'),
        ('Extract them with casts', 'Into a curated table or view, flattening arrays you aggregate.'),
        ('Keep the raw column', 'For fields nobody has asked for yet and for re-processing.'),
        title='Steps'),
    crossq(
        ('Will a view over VARIANT perform like a table?', 'A view does not store anything, so every query does the path extraction and casting again. '
         'If the sub-columns are well extracted it may be fine; for heavy use a materialized/dynamic table is faster.'),
        ('Why are my date filters on JSON slow?', 'The date is a string inside the VARIANT, so min/max pruning works on text. Cast and store it as '
         'DATE or TIMESTAMP in a column.'),
        ('Does Snowflake support XML?', 'Yes, XML can be loaded into VARIANT and queried with <code>XMLGET</code> and <code>GET</code>, though JSON and '
         'Parquet are far more common.'),
    ),
]),
])
