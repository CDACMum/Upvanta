from build import *
from hive.anims import *
from hive.runner import hql, hq, sh, datafile

STUDENTS_CSV = '''2401,Anuj,PG-DBDA,78
2402,Vineeta,PG-DBDA,91
2403,Aarshvi,PG-DAC,84
2404,Rohit,PG-DAC,66
'''

SECTION = dict(level='basic', title='Metastore, Databases & Loading Data', questions=[

# ------------------------------------------------------------------ 6
Q('What is the Hive Metastore? What are its deployment modes?', 'Hive Metastore', minutes=8, cards=[
    definition(
        defbox('The <strong>Hive Metastore (HMS)</strong> is the central repository of metadata: databases, tables, columns and types, '
               'storage format and SerDe, HDFS/S3 location, partitions, statistics, and privileges. It stores this in a relational '
               'database (MySQL, PostgreSQL, Oracle) and exposes it through a <strong>Thrift</strong> API (port 9083).',
               'It holds <strong>no table data</strong>, only the description of where the data is and how to read it.'),
        table(['Mode', 'Metastore service runs', 'Database', 'Use'], [
            ['Embedded', 'Inside the Hive JVM', 'Embedded Derby', 'Single-user testing only'],
            ['Local', 'Inside each Hive/HS2 process', 'External MySQL/PostgreSQL', 'Small setups; clients need DB credentials'],
            ['Remote', 'Separate Thrift service', 'External MySQL/PostgreSQL', '<strong>Production</strong>; shared by Hive, Spark, Trino, Impala'],
        ]),
        tags('Metastore', 'HMS', 'Thrift', 'Derby', 'MySQL', 'schematool', 'Catalog'),
    ),
    analogy('The metastore is a <strong>library catalogue card index</strong>. Each card says a book\'s title, author, shelf number and '
            'language. The cards are tiny and the books stay on the shelves. If the card index is lost, the books still exist, but nobody can '
            'find or read them in the right language. That is why the metastore database must be backed up.'),
    metastore_modes(),
    real_world(
        scenario('Shared catalogue in a data platform',
                 p('A telecom company runs one remote metastore (2 instances for HA) backed by a replicated MySQL. Hive ETL creates the '
                   'tables, Spark jobs write to them, and Trino serves analysts. When the metastore database was corrupted once, all '
                   'engines lost sight of every table even though HDFS was fine. Since then the MySQL database is backed up hourly.')),
    ),
    example(
        hql('''
CREATE TABLE students (roll_no INT, name STRING, course STRING, marks INT)
STORED AS ORC;
-- Everything below comes from the metastore; no data file is read
DESCRIBE FORMATTED students;
''', setup=''),
        title='Example: What the Metastore Knows About a Table'),
    example(
        code('''
<!-- hive-site.xml on the metastore server -->
<property><name>javax.jdo.option.ConnectionURL</name>
          <value>jdbc:mysql://dbhost:3306/hive_metastore</value></property>
<property><name>javax.jdo.option.ConnectionDriverName</name><value>com.mysql.cj.jdbc.Driver</value></property>
<property><name>javax.jdo.option.ConnectionUserName</name><value>hive</value></property>
<property><name>javax.jdo.option.ConnectionPassword</name><value>********</value></property>

<!-- hive-site.xml on clients (HiveServer2, Spark, ...) -->
<property><name>hive.metastore.uris</name><value>thrift://hms1:9083,thrift://hms2:9083</value></property>
''', 'hive-site.xml (remote metastore)', 'fa-file-code'),
        title='Configuration'),
    steps(
        ('Create the backing database', '<code>CREATE DATABASE hive_metastore; CREATE USER \'hive\'@\'%\' ...; GRANT ALL ...</code> in MySQL.'),
        ('Add the JDBC driver', 'Copy the MySQL connector jar into <code>$HIVE_HOME/lib</code>.'),
        ('Configure connection properties', 'Set the <code>javax.jdo.option.*</code> properties in <code>hive-site.xml</code>.'),
        ('Initialise the schema', '<code>schematool -dbType mysql -initSchema</code> (and <code>-upgradeSchema</code> on upgrades).'),
        ('Start the service', '<code>hive --service metastore</code> and point clients to it with <code>hive.metastore.uris</code>.'),
        title='Steps to Set Up a Remote Metastore'),
    crossq(
        ('Why is Derby not used in production?', 'Embedded Derby allows only one connection: a second Hive session fails with a lock error. It is also local to one machine.'),
        ('Which important metastore tables exist in the backing DB?', '<code>DBS</code> (databases), <code>TBLS</code> (tables), <code>SDS</code> '
         '(storage descriptors: location, formats), <code>COLUMNS_V2</code>, <code>PARTITIONS</code>, <code>PARTITION_KEY_VALS</code>, <code>TABLE_PARAMS</code> (stats).'),
        ('How do Spark and Trino use the Hive Metastore?', 'They connect to the same Thrift URI, read table definitions and partition lists, then read the files themselves with their own engines.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('How do you create and manage databases in Hive?', 'Databases & Warehouse Directory', minutes=6, cards=[
    definition(
        defbox('A Hive <strong>database</strong> (synonym: <strong>schema</strong>) is a namespace for tables, mapped to a directory. By default '
               '<code>CREATE DATABASE cdac</code> creates <code>&lt;hive.metastore.warehouse.dir&gt;/cdac.db</code>, usually '
               '<code>/user/hive/warehouse/cdac.db</code> (in Hive 3 managed tables go under <code>/warehouse/tablespace/managed/hive</code>).',
               'Tables are referred to as <code>database.table</code>. The default database is <code>default</code>.'),
        tags('CREATE DATABASE', 'Schema', 'Warehouse Directory', 'LOCATION', 'DBPROPERTIES', 'CASCADE'),
    ),
    analogy('A database is a <strong>cupboard</strong> in the store-room and tables are <strong>labelled boxes</strong> in it. Creating a database '
            'just adds a new cupboard (a folder); dropping a cupboard that still has boxes in it is refused unless you say <code>CASCADE</code> '
            '("throw away the boxes too").'),
    db_tree(),
    real_world(
        scenario('Layered databases',
                 p('Projects often create one database per layer: <code>raw</code> (external tables over landing files), <code>staging</code> '
                   '(cleaned), <code>dw</code> (fact and dimension tables) and <code>reports</code>. Permissions are then granted per database.')),
    ),
    example(
        hql('''
CREATE DATABASE IF NOT EXISTS raw
  COMMENT 'landing data, external tables only'
  WITH DBPROPERTIES ('created_by' = 'vineeta', 'layer' = 'bronze');

SHOW DATABASES LIKE 'r*';
DESCRIBE DATABASE EXTENDED raw;
USE raw;
CREATE TABLE t1 (id INT);
DROP DATABASE raw;
''', expect_error=True),
        hql('''
CREATE DATABASE raw;
CREATE TABLE raw.t1 (id INT);
DROP DATABASE raw CASCADE;   -- drops the tables too
SHOW DATABASES LIKE 'r*';
'''),
        title='Example'),
    steps(
        ('Create', '<code>CREATE DATABASE IF NOT EXISTS name [COMMENT ...] [LOCATION ...] [WITH DBPROPERTIES (...)];</code>'),
        ('Switch to it', '<code>USE name;</code> or always qualify tables as <code>name.table</code>.'),
        ('Inspect', '<code>DESCRIBE DATABASE EXTENDED name;</code> shows the location and properties.'),
        ('Change properties', '<code>ALTER DATABASE name SET DBPROPERTIES (...)</code>; Hive 2.2+ can also <code>SET LOCATION</code> for new tables.'),
        ('Drop', '<code>DROP DATABASE name;</code> works only when empty; add <code>CASCADE</code> to drop its tables.'),
        title='Steps to Create a Database'),
    crossq(
        ('Does <code>DROP DATABASE ... CASCADE</code> delete data?', 'It drops all its tables: managed tables lose their data, external tables keep their files.'),
        ('What is the difference between a database and a schema in Hive?', 'None. <code>CREATE SCHEMA</code> is a synonym for <code>CREATE DATABASE</code>.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What data types does Hive support? Explain the complex types.', 'Data Types', minutes=8, cards=[
    definition(
        table(['Category', 'Types'], [
            ['Integer', '<code>TINYINT</code> (1 byte), <code>SMALLINT</code> (2), <code>INT</code> (4), <code>BIGINT</code> (8)'],
            ['Decimal', '<code>FLOAT</code>, <code>DOUBLE</code>, <code>DECIMAL(p,s)</code> (use for money)'],
            ['Text', '<code>STRING</code>, <code>VARCHAR(n)</code>, <code>CHAR(n)</code>'],
            ['Date/time', '<code>DATE</code>, <code>TIMESTAMP</code>, <code>INTERVAL</code>'],
            ['Other', '<code>BOOLEAN</code>, <code>BINARY</code>'],
            ['Complex', '<code>ARRAY&lt;T&gt;</code>, <code>MAP&lt;K,V&gt;</code>, <code>STRUCT&lt;a:T, b:T&gt;</code>, <code>UNIONTYPE</code> (rare)'],
        ]),
        tags('Primitive Types', 'ARRAY', 'MAP', 'STRUCT', 'DECIMAL', 'Nested Data'),
    ),
    analogy('Complex types are like the sections of a <strong>student file folder</strong>: an <strong>ARRAY</strong> is the list of '
            'certificates (several items of the same kind, in order); a <strong>MAP</strong> is the marksheet (subject → marks, look up by name); '
            'a <strong>STRUCT</strong> is the address block (fixed fields: city, pin, state) kept together as one unit.'),
    complex_types_anim(),
    real_world(
        scenario('Why complex types matter',
                 p('Clickstream and API data arrive as nested JSON. Instead of flattening everything into dozens of tables, Hive keeps one row '
                   'per event with arrays and structs, and queries them with <code>[]</code>, <code>.field</code> and <code>explode()</code>. '
                   'This avoids expensive joins.')),
    ),
    example(
        hql('''
CREATE TABLE student_profile (
  roll_no  INT,
  name     STRING,
  skills   ARRAY<STRING>,
  marks    MAP<STRING, INT>,
  address  STRUCT<city: STRING, pin: STRING>
) STORED AS ORC;

INSERT INTO student_profile
SELECT 2402, 'Vineeta', array('python', 'hive', 'kafka'),
       map('SQL', 91, 'Spark', 88), named_struct('city', 'Navi Mumbai', 'pin', '410210');

SELECT name,
       skills[0]          AS first_skill,
       size(skills)       AS n_skills,
       marks['Spark']     AS spark_marks,
       map_keys(marks)    AS subjects,
       address.city       AS city
FROM student_profile;
'''),
        title='Example: ARRAY, MAP and STRUCT'),
    example(
        datafile('/data/raw/profiles/p.txt', '''
2401|Anuj|sql,spark|SQL:82,Spark:77|Pune,411001
2402|Vineeta|python,hive|SQL:91,Spark:88|Navi Mumbai,410210
'''),
        hql('''
CREATE EXTERNAL TABLE profiles_txt (
  roll_no INT, name STRING,
  skills ARRAY<STRING>, marks MAP<STRING, INT>, address STRUCT<city: STRING, pin: STRING>)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY '|'
  COLLECTION ITEMS TERMINATED BY ','
  MAP KEYS TERMINATED BY ':'
STORED AS TEXTFILE
LOCATION '/data/raw/profiles';

SELECT name, skills, marks['SQL'] AS sql_marks, address.city FROM profiles_txt;
''', files={'raw/profiles/p.txt': '2401|Anuj|sql,spark|SQL:82,Spark:77|Pune,411001\n2402|Vineeta|python,hive|SQL:91,Spark:88|Navi Mumbai,410210\n'}),
        title='Example: Complex Types in a Delimited Text File'),
    steps(
        ('Identify nested fields', 'Lists → ARRAY, key/value pairs → MAP, fixed groups of fields → STRUCT.'),
        ('Declare the table', 'Use the complex types in <code>CREATE TABLE</code>.'),
        ('Choose delimiters (text files)', '<code>FIELDS</code>, <code>COLLECTION ITEMS</code> and <code>MAP KEYS TERMINATED BY</code>; for JSON use a JSON SerDe; ORC/Parquet store nesting natively.'),
        ('Query', '<code>arr[i]</code>, <code>map[\'key\']</code>, <code>struct.field</code>, <code>size()</code>, <code>explode()</code>.'),
        title='Steps to Model Nested Data'),
    crossq(
        ('STRING vs VARCHAR in Hive?', 'STRING has no length limit and is the usual choice. VARCHAR(n) truncates longer values; useful mainly for compatibility with other databases.'),
        ('Why DECIMAL for money instead of DOUBLE?', 'DOUBLE is binary floating point and cannot represent many decimal values exactly (0.1 + 0.2 ≠ 0.3), so sums drift. DECIMAL(p,s) is exact.'),
        ('What happens if you access an array index that does not exist?', 'Hive returns NULL instead of failing.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('What are the different ways to load data into a Hive table?', 'Loading Data', minutes=9, cards=[
    definition(
        table(['Method', 'What it does', 'Typical use'], [
            ['<code>LOAD DATA [LOCAL] INPATH</code>', 'Moves (HDFS) or copies (LOCAL) files into the table directory, no parsing', 'Files already in the table\'s format'],
            ['<code>INSERT INTO ... SELECT</code>', 'Runs a query and appends its result', 'Transformations, incremental loads'],
            ['<code>INSERT OVERWRITE ... SELECT</code>', 'Replaces the table or partition contents', 'Idempotent daily rebuilds'],
            ['<code>CREATE TABLE AS SELECT</code> (CTAS)', 'Creates the table and fills it from a query', 'Quick derived tables'],
            ['External table <code>LOCATION</code>', 'No load at all: the table points at existing files', 'Landing/raw data written by other tools'],
            ['<code>INSERT INTO ... VALUES</code>', 'Inserts literal rows (creates small files)', 'Tests only'],
            ['Multi-insert', '<code>FROM src INSERT ... INSERT ...</code>: one scan, several targets', 'Splitting a source into several tables'],
        ]),
        tags('LOAD DATA', 'INSERT OVERWRITE', 'CTAS', 'Multi-insert', 'External Table'),
    ),
    analogy('Getting groceries into the kitchen: <strong>LOAD DATA</strong> is carrying the bags in unopened; <strong>INSERT ... SELECT</strong> '
            'is washing and chopping the vegetables before putting them in labelled containers; an <strong>external table</strong> is leaving '
            'the vegetables at the market stall and just writing the stall\'s address in your notebook.'),
    load_data_anim(),
    real_world(
        scenario('Daily exam marks load',
                 ul('The exam system drops <code>marks_2026-10-13.csv</code> into <code>/landing/exams/</code>.',
                    'An external staging table points at the landing folder (no copy).',
                    '<code>INSERT OVERWRITE TABLE dw.marks PARTITION (dt=\'2026-10-13\') SELECT ... FROM staging</code> cleans, casts and '
                    'converts to ORC. Re-running the job for the same day replaces that day instead of duplicating it.')),
    ),
    example(
        datafile('/data/landing/students.csv', STUDENTS_CSV),
        hql('''
CREATE TABLE students_txt (roll_no INT, name STRING, course STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE;

LOAD DATA INPATH '/data/landing/students.csv' INTO TABLE students_txt;

SELECT * FROM students_txt;
dfs -ls -R /data/landing;
dfs -ls -R /user/hive/warehouse/cdac.db/students_txt;
''', files={'landing/students.csv': STUDENTS_CSV}),
        note('The landing folder is now <strong>empty</strong>: <code>LOAD DATA INPATH</code> moved the file into the table directory.', 'Notice'),
        title='Example: LOAD DATA Moves the File'),
    example(
        hql('''
-- CTAS: create + fill in one step, converting text to ORC
CREATE TABLE students_orc STORED AS ORC AS
SELECT roll_no, upper(name) AS name, course, marks FROM students_txt;

-- Multi-insert: scan the source once, write two tables
CREATE TABLE dbda (roll_no INT, name STRING) STORED AS ORC;
CREATE TABLE dac  (roll_no INT, name STRING) STORED AS ORC;
FROM students_orc
INSERT OVERWRITE TABLE dbda SELECT roll_no, name WHERE course = 'PG-DBDA'
INSERT OVERWRITE TABLE dac  SELECT roll_no, name WHERE course = 'PG-DAC';

SELECT 'dbda' AS tbl, * FROM dbda UNION ALL SELECT 'dac', * FROM dac;

-- INSERT OVERWRITE is idempotent: running it twice leaves 2 rows, not 4
INSERT OVERWRITE TABLE dbda SELECT roll_no, name FROM students_orc WHERE course = 'PG-DBDA';
INSERT OVERWRITE TABLE dbda SELECT roll_no, name FROM students_orc WHERE course = 'PG-DBDA';
SELECT COUNT(*) AS rows_in_dbda FROM dbda;
''', setup='''
CREATE TABLE students_txt (roll_no INT, name STRING, course STRING, marks INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE;
LOAD DATA INPATH '/data/landing/students.csv' INTO TABLE students_txt;
''', files={'landing/students.csv': STUDENTS_CSV}),
        title='Example: CTAS, Multi-insert and INSERT OVERWRITE'),
    steps(
        ('Land the raw file', '<code>hdfs dfs -put marks.csv /landing/exams/</code>'),
        ('Expose it', 'External table over <code>/landing/exams</code> (TEXTFILE, matching delimiter).'),
        ('Create the target', 'Managed ORC/Parquet table, partitioned by date.'),
        ('Transform and load', '<code>INSERT OVERWRITE TABLE target PARTITION (dt=...) SELECT ... FROM staging</code>'),
        ('Validate', 'Compare row counts and a few sums with the source; check for unexpected NULLs.'),
        title='Steps for a Production Load'),
    crossq(
        ('Why might <code>LOAD DATA</code> into an ORC table give garbage?', 'LOAD DATA does not convert anything. Loading a CSV file into a table declared <code>STORED AS ORC</code> '
         'puts a text file where ORC is expected, and queries fail or return nonsense. Load text into a text table, then <code>INSERT ... SELECT</code> into the ORC table.'),
        ('INSERT INTO vs INSERT OVERWRITE?', 'INTO appends new files; OVERWRITE deletes the existing files of the table/partition first. OVERWRITE makes reruns safe (idempotent).'),
        ('Why avoid many <code>INSERT ... VALUES</code>?', 'Each statement launches a job and writes at least one new small file.'),
    ),
]),
])
