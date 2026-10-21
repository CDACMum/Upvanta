from build import *
from snowflakedb.anims import *
from snowflakedb.runner import sql, sq

CONTACTS = '''
CREATE OR REPLACE TABLE contacts (roll_no INT, name VARCHAR, phone VARCHAR, centre VARCHAR);
INSERT INTO contacts VALUES
  (2401, 'Anuj',  '98200 12345', 'Kharghar'),
  (2403, 'Riya',  '98330 54321', 'Kharghar'),
  (2407, 'Meera', '99870 11111', 'Juhu');
CREATE OR REPLACE TABLE centre_access (role_name VARCHAR, centre VARCHAR);
INSERT INTO centre_access VALUES ('KHARGHAR_COORD', 'Kharghar'), ('JUHU_COORD', 'Juhu');
'''

PIPELINE = '''
CREATE OR REPLACE TABLE raw_submissions (v VARIANT, src_file VARCHAR, loaded_at TIMESTAMP_NTZ);
INSERT INTO raw_submissions
SELECT PARSE_JSON(column1), column2, column3::TIMESTAMP_NTZ FROM VALUES
 ('{"roll":2401,"centre":"Kharghar","course":"PGCP-BDA","exams":[{"sub":"SQL","m":78},{"sub":"Spark","m":82}]}', 'f1.json', '2026-02-15 10:00:00'),
 ('{"roll":2402,"centre":"Juhu","course":"PGCP-BDA","exams":[{"sub":"SQL","m":91},{"sub":"Spark","m":35}]}',     'f1.json', '2026-02-15 10:00:00'),
 ('{"roll":2405,"centre":"Kharghar","course":"PGCP-BDA","exams":[{"sub":"SQL","m":95},{"sub":"Spark","m":89}]}', 'f2.json', '2026-02-15 10:05:00'),
 ('{"roll":2408,"centre":"Juhu","course":"PGCP-BDA","exams":[{"sub":"SQL","m":38},{"sub":"Spark","m":44}]}',     'f2.json', '2026-02-15 10:05:00'),
 ('{"roll":2402,"centre":"Juhu","course":"PGCP-BDA","exams":[{"sub":"SQL","m":91},{"sub":"Spark","m":41}]}',     'f3.json', '2026-02-16 09:00:00');
'''

SECTION = dict(level='advanced', title='Security, Cost & Real-World Scenarios', questions=[

# ------------------------------------------------------------------ 36
Q('How does access control work in Snowflake? Explain RBAC, system roles and best practices.', 'Access Control (RBAC)', minutes=9, cards=[
    definition(
        defbox('Snowflake combines <strong>role-based access control (RBAC)</strong>, where privileges are granted to roles and roles to users, with '
               '<strong>discretionary access control</strong>, where every object has an owner role that can grant privileges on it. Roles can be '
               'granted to other roles, forming a hierarchy in which privileges flow <strong>upward</strong>.'),
        table(['System role', 'Purpose'], [
            ['ORGADMIN', 'Organization level: accounts, organization usage'],
            ['ACCOUNTADMIN', 'Top role of the account (SYSADMIN + SECURITYADMIN). Few users, MFA, not for daily work'],
            ['SECURITYADMIN', 'Manages grants globally (MANAGE GRANTS); inherits USERADMIN'],
            ['USERADMIN', 'Creates users and roles'],
            ['SYSADMIN', 'Creates warehouses, databases and objects; custom roles should roll up to it'],
            ['PUBLIC', 'Granted to everyone automatically'],
        ]),
        defbox('A session has one <strong>primary role</strong> (<code>USE ROLE</code>) and can enable <strong>secondary roles</strong> '
               '(<code>USE SECONDARY ROLES ALL</code>) whose privileges also apply to queries. <strong>Future grants</strong> give privileges on '
               'objects that will be created later in a schema or database.'),
        tags('RBAC', 'GRANT', 'Role hierarchy', 'ACCOUNTADMIN', 'SYSADMIN', 'Future grants', 'Least privilege'),
    ),
    analogy('Keys in an institute: you do not hand each person individual keys to every room. You make <strong>key rings per job</strong> (faculty, '
            'lab assistant, exam cell) and give people the right ring. The principal\'s master ring contains all the others.'),
    rbac_anim(),
    real_world(
        scenario('Roles for the BDA programme',
                 ul('<code>BDA_ENGINEER</code>: read/write on RAW and CLEAN schemas, USAGE on ETL_WH.',
                    '<code>BDA_ANALYST</code>: SELECT on MART only, USAGE on BI_WH.',
                    '<code>BDA_STUDENT</code>: SELECT on a training schema, USAGE on LAB_WH with a resource monitor.',
                    'All three granted to SYSADMIN so administrators can manage their objects.')),
    ),
    example(
        sq('''
USE ROLE USERADMIN;
CREATE ROLE bda_analyst;
CREATE USER riya PASSWORD = '********' DEFAULT_ROLE = bda_analyst DEFAULT_WAREHOUSE = bi_wh MUST_CHANGE_PASSWORD = TRUE;
GRANT ROLE bda_analyst TO USER riya;
GRANT ROLE bda_analyst TO ROLE sysadmin;                 -- roll custom roles up to SYSADMIN

USE ROLE SECURITYADMIN;
GRANT USAGE  ON WAREHOUSE bi_wh                   TO ROLE bda_analyst;
GRANT USAGE  ON DATABASE  exam                    TO ROLE bda_analyst;
GRANT USAGE  ON SCHEMA    exam.mart               TO ROLE bda_analyst;
GRANT SELECT ON ALL TABLES    IN SCHEMA exam.mart TO ROLE bda_analyst;
GRANT SELECT ON FUTURE TABLES IN SCHEMA exam.mart TO ROLE bda_analyst;   -- tables created later

SHOW GRANTS TO ROLE bda_analyst;
SHOW GRANTS TO USER riya;
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Design functional roles', 'One per job (engineer, analyst, student), plus access roles per schema if the setup is large.'),
        ('Grant privileges to roles, never to users', 'Users only receive roles.'),
        ('Roll custom roles up to SYSADMIN', 'So objects created by them stay manageable.'),
        ('Protect ACCOUNTADMIN', 'Few people, MFA, not a default role.'),
        ('Use future grants and review', 'SHOW GRANTS and ACCOUNT_USAGE.GRANTS_TO_ROLES periodically.'),
        title='Steps'),
    crossq(
        ('What privileges does a user need to run SELECT on a table?', 'USAGE on the warehouse, USAGE on the database and schema, and SELECT on the table '
         '(through their active primary or secondary roles).'),
        ('Who owns an object, and why does it matter?', 'The role that created it (unless ownership is transferred). The owner can grant and drop it, so '
         'creating objects with ACCOUNTADMIN causes headaches; create them with SYSADMIN or functional roles.'),
        ('How do users authenticate securely?', 'SSO (SAML/OAuth), multi-factor authentication, key-pair authentication for services, and network policies '
         'that restrict client IP ranges. Password-only sign-in is being phased out for many users.'),
    ),
]),

# ------------------------------------------------------------------ 37
Q('How do you protect sensitive columns and rows? Explain masking policies, row access policies and secure views.', 'Data Governance', minutes=9, cards=[
    definition(
        table(['Feature', 'What it controls', 'How'], [
            ['Dynamic data masking policy', 'What value of a column a role sees', 'A SQL function attached to a column; evaluated at query time'],
            ['Row access policy', 'Which rows a role sees', 'A boolean SQL function attached to a table/view, often using a mapping table'],
            ['Secure view', 'Hides the view definition and blocks optimisations that could leak hidden data', '<code>CREATE SECURE VIEW</code>'],
            ['Object tagging', 'Classify columns (e.g. PII = phone)', 'Tags + tag-based masking applies a policy to all tagged columns'],
            ['Data classification', 'Finds likely sensitive columns automatically', 'SYSTEM$CLASSIFY / automatic classification'],
        ]),
        defbox('Masking and row access policies need <strong>Enterprise edition</strong>. They are defined once and enforced everywhere: direct queries, '
               'views, shares and clones. Inside a policy, <code>CURRENT_ROLE()</code> or <code>IS_ROLE_IN_SESSION()</code> decides what to return.'),
        tags('Masking policy', 'Row access policy', 'Secure view', 'Tags', 'IS_ROLE_IN_SESSION', 'PII'),
    ),
    analogy('A <strong>frosted window</strong> on certain fields of a form (masking) and a <strong>receptionist who only hands you the files for your '
            'own centre</strong> (row access): the same cabinet, different views for different people.'),
    masking_anim(),
    real_world(
        scenario('Student contact data under DPDP rules',
                 p('Phone numbers are personal data. HR administrators need the full number; centre coordinators should see only their own students and only '
                   'the last five digits. One masking policy on <code>phone</code> and one row access policy on <code>contacts</code> enforce this for every '
                   'tool, instead of maintaining separate views per centre.')),
    ),
    example(
        sq('''
CREATE MASKING POLICY phone_mask AS (val STRING) RETURNS STRING ->
  CASE WHEN IS_ROLE_IN_SESSION('HR_ADMIN') THEN val
       ELSE REGEXP_REPLACE(val, '^[0-9 ]{6}', '*****') END;
ALTER TABLE contacts MODIFY COLUMN phone SET MASKING POLICY phone_mask;

CREATE ROW ACCESS POLICY centre_rap AS (row_centre STRING) RETURNS BOOLEAN ->
  IS_ROLE_IN_SESSION('HR_ADMIN')
  OR EXISTS (SELECT 1 FROM centre_access m
             WHERE m.centre = row_centre AND IS_ROLE_IN_SESSION(m.role_name));
ALTER TABLE contacts ADD ROW ACCESS POLICY centre_rap ON (centre);
'''),
        p('The policies need a real account, but their logic is plain SQL. Here it is evaluated for two roles side by side, which is exactly what the '
          'policies return when each role queries the table:', top=True),
        sql('''
SELECT r.role_name,
       c.name,
       IFF(r.role_name = 'HR_ADMIN', c.phone,
           REGEXP_REPLACE(c.phone, '^[0-9 ]{6}', '*****'))           AS phone_seen
FROM   contacts c
CROSS  JOIN (SELECT column1 AS role_name FROM VALUES ('HR_ADMIN'), ('KHARGHAR_COORD')) r
WHERE  r.role_name = 'HR_ADMIN'
   OR  EXISTS (SELECT 1 FROM centre_access m
               WHERE m.centre = c.centre AND m.role_name = r.role_name)
ORDER  BY r.role_name, c.roll_no;
''', setup=CONTACTS, data=False, show='queries'),
        p('HR_ADMIN sees all three students with full numbers; KHARGHAR_COORD sees only Anuj and Riya, with masked numbers.', top=True),
        title='Example'),
    steps(
        ('Classify data', 'Tag PII columns (manually or with classification).'),
        ('Write policies', 'Masking per data type/pattern; row access with a mapping table.'),
        ('Attach', 'To columns/tables, or to tags for automatic coverage.'),
        ('Test as each role', '<code>USE ROLE …</code> and query; check POLICY_REFERENCES.'),
        ('Separate duties', 'A governance role owns policies; data engineers cannot bypass them.'),
        title='Steps'),
    crossq(
        ('Can the table owner see unmasked data?', 'Only if the policy allows it. Policies apply to every role, including the owner and ACCOUNTADMIN, '
         'unless the policy\'s conditions say otherwise.'),
        ('Masking policy vs a view that hides the column?', 'A view must be maintained per audience and users could query the base table if granted. A '
         'policy protects the column itself, everywhere.'),
        ('Do policies slow queries?', 'Slightly: the policy expression is evaluated per row. Keep them simple and use mapping tables for row access rather '
         'than complex logic.'),
    ),
]),

# ------------------------------------------------------------------ 38
Q('How do you monitor and control Snowflake costs?', 'Cost Management', minutes=8, cards=[
    definition(
        ul('<strong>Resource monitors</strong>: credit quotas per month/week/day for chosen warehouses or the whole account, with actions at thresholds '
           '(NOTIFY, SUSPEND after running queries finish, SUSPEND_IMMEDIATE).',
           '<strong>Budgets</strong>: monthly spending limits with notifications that also cover serverless features.',
           '<strong>Warehouse hygiene</strong>: right size, short AUTO_SUSPEND, separate warehouses per workload, multi-cluster only where concurrency needs it.',
           '<strong>Query guards</strong>: <code>STATEMENT_TIMEOUT_IN_SECONDS</code> and <code>STATEMENT_QUEUED_TIMEOUT_IN_SECONDS</code> on warehouses or users.',
           '<strong>Storage hygiene</strong>: transient tables for re-creatable data, sensible Time Travel retention, drop unused clones and tables.',
           '<strong>Serverless review</strong>: automatic clustering, search optimisation, materialized views, Snowpipe, tasks.',
           '<strong>Visibility</strong>: <code>SNOWFLAKE.ACCOUNT_USAGE</code> views (WAREHOUSE_METERING_HISTORY, QUERY_HISTORY, METERING_DAILY_HISTORY…), '
           'Snowsight Cost Management, and object tags to attribute cost to teams.'),
        tags('Resource monitor', 'Budgets', 'AUTO_SUSPEND', 'Statement timeout', 'ACCOUNT_USAGE', 'Cost attribution'),
    ),
    analogy('Running an institute canteen: a monthly budget with an alarm at 75% (resource monitor), lights and stoves off when nobody is cooking '
            '(auto-suspend), and a ledger showing which department ate what (cost attribution).'),
    cost_anim(),
    real_world(
        scenario('A student lab without surprises',
                 p('100 PGCP-BDA students share <code>LAB_WH</code> (X-Small, multi-cluster 1–3, AUTO_SUSPEND 60). A resource monitor gives it 300 credits a '
                   'month: notify the coordinator at 75%, suspend at 100%. A 10-minute statement timeout stops accidental cross joins.')),
    ),
    example(
        sql('''
-- planned monthly credits for each warehouse (hours/day × days × credits/hour × avg clusters)
SELECT warehouse, size, credits_per_hour, hours_per_day, days, avg_clusters,
       credits_per_hour * hours_per_day * days * avg_clusters AS monthly_credits
FROM VALUES ('ETL_WH', 'Medium',  4, 1.5, 30, 1.0),
            ('BI_WH',  'Small',   2, 6.0, 22, 1.5),
            ('LAB_WH', 'X-Small', 1, 4.0, 22, 2.0)
     AS t(warehouse, size, credits_per_hour, hours_per_day, days, avg_clusters)
ORDER BY monthly_credits DESC;
''', data=False, show='queries'),
        p('ETL runs 1.5 hours every night, BI is busy 6 hours on working days with 1.5 clusters on average, and the lab runs 4 hours with 2 clusters. '
          'An estimate like this is the starting point for resource-monitor quotas.', top=True),
        sq('''
CREATE RESOURCE MONITOR lab_monthly WITH CREDIT_QUOTA = 300
  FREQUENCY = MONTHLY START_TIMESTAMP = IMMEDIATELY
  TRIGGERS ON 75 PERCENT DO NOTIFY
           ON 100 PERCENT DO SUSPEND
           ON 110 PERCENT DO SUSPEND_IMMEDIATE;
ALTER WAREHOUSE lab_wh SET RESOURCE_MONITOR = lab_monthly
                           STATEMENT_TIMEOUT_IN_SECONDS = 600;

-- where did the credits go last month?
SELECT warehouse_name, SUM(credits_used) AS credits
FROM   SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE  start_time >= DATE_TRUNC('month', DATEADD(month, -1, CURRENT_DATE()))
  AND  start_time <  DATE_TRUNC('month', CURRENT_DATE())
GROUP  BY 1 ORDER BY 2 DESC;
'''),
        title='Example'),
    steps(
        ('Get visibility', 'Daily credits by warehouse and service; storage by database.'),
        ('Set guard rails', 'Resource monitors, budgets, statement timeouts.'),
        ('Fix the top items', 'Idle or oversized warehouses, runaway queries, expensive serverless features.'),
        ('Attribute and review', 'Tag warehouses/objects by team; monthly review with owners.'),
        title='Steps'),
    crossq(
        ('Can a resource monitor control serverless costs such as Snowpipe?', 'No, resource monitors apply to warehouses. Use budgets to monitor '
         'serverless and account-wide spending.'),
        ('What does SUSPEND vs SUSPEND_IMMEDIATE mean?', 'SUSPEND lets running queries finish before suspending the warehouses; SUSPEND_IMMEDIATE cancels '
         'running queries at once.'),
        ('How do you find the most expensive queries?', 'ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY gives credits per query; QUERY_HISTORY gives elapsed time, '
         'bytes scanned and warehouse size to estimate them.'),
    ),
]),

# ------------------------------------------------------------------ 39
Q('Scenario: design a Snowflake pipeline for C-DAC exam results, from JSON files to rank lists.', 'Scenario: Results Pipeline', minutes=12, cards=[
    definition(
        ul('<strong>Ingest</strong>: the exam portal writes JSON files to S3; Snowpipe (AUTO_INGEST) loads them into <code>RAW.SUBMISSIONS</code> '
           '(VARIANT + file name + load time). Nothing is rejected at this stage.',
           '<strong>Clean</strong>: a stream on RAW plus a task (or a dynamic table) flattens the exams array, casts types and keeps only the '
           '<strong>latest submission per roll number</strong> (re-submissions and revaluations replace earlier ones).',
           '<strong>Mart</strong>: rank lists per course, pass/fail per subject, centre-wise statistics.',
           '<strong>Operations</strong>: ETL_WH for transforms, BI_WH (multi-cluster) for result day, roles BDA_ENGINEER/BDA_ANALYST, masking on contact '
           'data, Time Travel 30 days on CLEAN and MART, resource monitors.'),
        tags('Snowpipe', 'VARIANT', 'FLATTEN', 'QUALIFY ROW_NUMBER', 'MERGE / Dynamic table', 'RANK', 'Medallion'),
    ),
    analogy('An answer-sheet assembly line: sheets arrive in sealed envelopes (raw), are opened, checked and the latest copy of each candidate kept '
            '(clean), and finally sorted into merit lists pinned on the notice board (mart).'),
    pipeline_anim(),
    real_world(
        scenario('Requirements that shape the design',
                 ul('Revaluation: a candidate\'s Spark marks may arrive again a day later; the latest submission must win.',
                    'Pass rule: at least 40 in every subject.',
                    'Results must be reproducible for audits: keep raw JSON and Time Travel on curated tables.',
                    'Result day: hundreds of coordinators open dashboards at once.')),
    ),
    example(
        sql(PIPELINE + '''
-- CLEAN: latest submission per candidate, one row per subject
CREATE OR REPLACE TABLE clean_marks AS
SELECT s.v:roll::INT          AS roll_no,
       s.v:centre::STRING     AS centre,
       s.v:course::STRING     AS course,
       e.value:sub::STRING    AS subject,
       e.value:m::INT         AS marks,
       s.loaded_at
FROM   raw_submissions s, LATERAL FLATTEN(input => s.v:exams) e
QUALIFY ROW_NUMBER() OVER (PARTITION BY s.v:roll::INT, e.value:sub::STRING
                           ORDER BY s.loaded_at DESC) = 1;

-- MART: result per candidate and merit rank
SELECT roll_no, centre,
       SUM(marks)::INT                                AS total,
       IFF(MIN(marks) >= 40, 'PASS', 'FAIL')          AS result,
       IFF(MIN(marks) >= 40, RANK() OVER (PARTITION BY (MIN(marks) >= 40) ORDER BY SUM(marks) DESC), NULL) AS merit_rank
FROM   clean_marks
GROUP  BY roll_no, centre
ORDER  BY merit_rank NULLS LAST, roll_no;

-- MART: centre-wise pass percentage
SELECT centre,
       COUNT(*)                                                   AS candidates,
       COUNT_IF(min_marks >= 40)                                  AS passed,
       (COUNT_IF(min_marks >= 40) * 100 / COUNT(*))::NUMBER(5,1)  AS pass_pct
FROM  (SELECT roll_no, centre, MIN(marks) AS min_marks FROM clean_marks GROUP BY roll_no, centre)
GROUP BY centre
ORDER BY centre;
''', data=False, show='queries'),
        p('Candidate 2402 was submitted twice. The revaluation file f3.json (Spark 41) replaced the first result (Spark 35), so 2402 passes. 2408 fails '
          'with 38 in SQL and gets no merit rank. In production the CREATE TABLE AS would be a MERGE fed by a stream, or a dynamic table.', top=True),
        title='Example: The Pipeline Logic, Executed'),
    steps(
        ('Land everything raw', 'Snowpipe into VARIANT with lineage columns.'),
        ('Deduplicate in CLEAN', 'QUALIFY ROW_NUMBER() OVER (PARTITION BY business key ORDER BY load time DESC) = 1.'),
        ('Automate', 'Dynamic tables with a target lag, or stream + task MERGE.'),
        ('Serve', 'MART tables/views for dashboards on a multi-cluster BI warehouse.'),
        ('Secure and monitor', 'Roles, masking, resource monitors, alerts on task failures.'),
        title='Steps'),
    crossq(
        ('Why keep the raw JSON after cleaning?', 'For audits and reprocessing: if a rule changes (e.g. the pass mark), CLEAN and MART can be rebuilt from '
         'RAW without asking centres for files again.'),
        ('How would you make the CLEAN step incremental?', 'A stream on RAW_SUBMISSIONS and a MERGE that applies only new submissions using the same '
         'ROW_NUMBER logic, or a dynamic table that Snowflake refreshes incrementally.'),
        ('How do you prevent analysts from seeing unpublished results?', 'A row access policy or secure view on MART that filters on a '
         '<code>published</code> flag, which only the exam cell\'s role can set.'),
    ),
]),

# ------------------------------------------------------------------ 40
Q('How does Snowflake compare with Redshift, BigQuery and Databricks? And how would you troubleshoot common problems?', 'Comparison & Troubleshooting', minutes=10, cards=[
    definition(
        table(['', 'Snowflake', 'Amazon Redshift', 'Google BigQuery', 'Databricks SQL'], [
            ['Deployment', 'SaaS on AWS, Azure, GCP', 'AWS (provisioned or Serverless)', 'GCP (BigQuery Omni for others)', 'AWS, Azure, GCP'],
            ['Compute model', 'Virtual warehouses, per second', 'Clusters (node-hours) or serverless RPUs', 'Serverless; on-demand per TB scanned or '
             'slot reservations', 'SQL warehouses, DBUs'],
            ['Storage', 'Managed micro-partitions; Iceberg tables', 'Managed storage; Spectrum for S3', 'Managed (Capacitor); BigLake for open formats',
             'Delta Lake / Iceberg files in your storage'],
            ['Physical tuning', 'Clustering keys (optional)', 'Distribution and sort keys', 'Partitioning and clustering', 'Liquid clustering / Z-order'],
            ['Distinctive', 'Zero-copy clone, sharing, near-zero admin', 'Deep AWS integration', 'Fully serverless, built-in ML (BigQuery ML)',
             'Lakehouse: one platform for Spark, ML and SQL'],
        ]),
        defbox('All four are strong; the choice depends on the cloud the organisation uses, existing skills, workloads (SQL BI vs Spark/ML), data '
               'sharing needs and the pricing model that best fits usage patterns.'),
        tags('Redshift', 'BigQuery', 'Databricks', 'Lakehouse', 'Pricing models', 'Troubleshooting'),
    ),
    analogy('Choosing a platform is like choosing a <strong>vehicle</strong>: a taxi (Snowflake/BigQuery, managed and pay per use), a leased car '
            '(provisioned Redshift), or a workshop where you can also build vehicles (Databricks). Each is right for some journeys.'),
    compare_anim(),
    comparison(
        table(['Problem', 'Check', 'Typical fix'], [
            ['Query suddenly slow', 'Query Profile: spilling, pruning, exploding join; was the result cache used before?', 'Fix join keys or filters; resize; cluster'],
            ['Many queries waiting', 'QUERY_HISTORY queued_overload_time', 'Multi-cluster warehouse or split workloads'],
            ['COPY loaded 0 files', 'Load metadata: files already loaded? PATTERN correct? LIST @stage', 'New file names; fix PATTERN; FORCE only if intended'],
            ['Snowpipe not loading', 'SYSTEM$PIPE_STATUS; S3 event notification; COPY_HISTORY errors', 'Fix the notification or file format; ALTER PIPE … REFRESH'],
            ['Task not running', 'Task suspended? TASK_HISTORY errors; owner has EXECUTE TASK and warehouse USAGE', 'Resume; grant privileges'],
            ['Stream is stale', 'SHOW STREAMS stale_after', 'Consume more often; recreate the stream and backfill'],
            ['"Object does not exist or not authorized"', 'Current role, database, schema; name case (quoted?)', 'USE ROLE / fully qualified names / grants'],
            ['Credits jumped', 'WAREHOUSE_METERING_HISTORY by day; serverless histories', 'AUTO_SUSPEND, resource monitors, remove unused features'],
        ]),
        title='Troubleshooting Checklist'),
    real_world(
        scenario('"Object does not exist" at 2 a.m.',
                 p('A new task failed with "Table \'RESULTS_CLEAN\' does not exist or not authorized", although the table existed. The task\'s owner role had '
                   'no USAGE on the CLEAN schema. Granting it, instead of running the task as ACCOUNTADMIN, fixed the error and kept least privilege.')),
    ),
    example(
        sq('''
-- what is my session context?  (the first thing to check for "does not exist" errors)
SELECT CURRENT_ROLE(), CURRENT_SECONDARY_ROLES(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();

-- recent failed queries and their errors
SELECT start_time, user_name, error_code, error_message, LEFT(query_text, 80) AS sql_start
FROM   SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE  execution_status = 'FAIL' AND start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP())
ORDER  BY start_time DESC LIMIT 20;

-- failed task runs
SELECT name, scheduled_time, state, error_message
FROM   TABLE(INFORMATION_SCHEMA.TASK_HISTORY(RESULT_LIMIT => 50))
WHERE  state = 'FAILED';
'''),
        title='Example (shown, not executed)'),
    steps(
        ('Reproduce and read the error', 'Note the role, warehouse and exact message.'),
        ('Check context and privileges first', 'Most "does not exist" errors are roles or names.'),
        ('Use the right history view', 'QUERY_HISTORY, COPY_HISTORY, TASK_HISTORY, PIPE status.'),
        ('Fix the cause, then the symptom', 'Grants, file names, job logic, warehouse settings.'),
        ('Add monitoring', 'Alerts or notifications so the next failure is noticed before users do.'),
        title='Steps'),
    crossq(
        ('If an interviewer asks "Why Snowflake over Redshift?", what is a balanced answer?', 'Snowflake offers separate per-second compute for each '
         'workload, near-zero tuning, multi-cloud and easy sharing. Redshift can be cheaper for steady, predictable workloads with reserved nodes and fits '
         'tightly into AWS. The right answer depends on workload pattern, cloud strategy and team skills.'),
        ('Is Snowflake a lakehouse?', 'With Apache Iceberg tables (data in open format in your own storage, managed by Snowflake or an external catalog) '
         'it can play that role, while keeping its managed tables for the best performance.'),
        ('What is Snowflake Cortex?', 'Snowflake\'s built-in AI features: SQL functions that call large language models (summarise, translate, classify, '
         'complete), plus search and analyst services, running inside Snowflake\'s security boundary.'),
    ),
]),
])
