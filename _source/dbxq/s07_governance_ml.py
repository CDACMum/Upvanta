from build import *
from dbxq.anims import *
from dbxq.runner import sql, sq, pyrun, py, sh, conf

SECTION = dict(level='advanced', title='Governance, Security & Machine Learning', questions=[

# ------------------------------------------------------------------ 31
Q('What is Unity Catalog? Explain the metastore, the three-level namespace and what it governs.', 'Unity Catalog', minutes=9, cards=[
    definition(
        defbox('<strong>Unity Catalog</strong> (UC) is Databricks\' unified governance layer for data and AI. One <strong>metastore</strong> per '
               'cloud region holds the metadata and is attached to all workspaces in that region, so permissions and definitions are shared '
               'across workspaces. (It replaces the older per-workspace Hive metastore and table ACLs.)',
               'Objects are addressed as <code>catalog.schema.object</code>. Securable objects include catalogs, schemas, tables, views, '
               'materialized views, <strong>volumes</strong> (governed files), <strong>functions</strong>, <strong>registered models</strong>, '
               'plus <strong>storage credentials</strong>, <strong>external locations</strong>, <strong>connections</strong> (federation) and '
               '<strong>shares</strong>.'),
        table(['Capability', 'What you get'], [
            ['Access control', 'ANSI SQL GRANT/REVOKE on every securable, inherited down the hierarchy'],
            ['Fine-grained control', 'Row filters, column masks, attribute-based policies with tags'],
            ['Lineage', 'Automatic table- and column-level lineage across notebooks, jobs, pipelines and dashboards'],
            ['Auditing', 'Audit logs and system tables (<code>system.access.audit</code>, billing, lineage)'],
            ['Discovery', 'Catalog Explorer, comments, tags, search'],
            ['Open access', 'Delta Sharing, Iceberg REST catalog API for external engines'],
        ]),
        tags('Unity Catalog', 'Metastore', 'catalog.schema.table', 'Securable', 'Volume', 'External location', 'Lineage', 'System tables'),
    ),
    analogy('Unity Catalog is the <strong>central library catalogue and security desk</strong> for all branches of a university: every book '
            '(table, file, model) has one entry, one set of borrowing rules, and a record of who read it, whichever branch (workspace) you '
            'visit.'),
    uc_anim(),
    real_world(
        scenario('Organising C-DAC data',
                 ul('Catalogs by environment: <code>cdac_dev</code>, <code>cdac_prod</code>; or by domain: <code>exams</code>, '
                    '<code>placements</code>, <code>hr</code>.',
                    'Schemas by layer or subject: <code>exams.bronze</code>, <code>exams.silver</code>, <code>exams.gold</code>.',
                    'Groups from the identity provider (<code>exam-cell</code>, <code>placement-cell</code>, <code>faculty</code>) get privileges; '
                    'individuals never do.',
                    'Lineage shows that the placement dashboard depends on <code>exams.gold.rank_list</code>, so a schema change there is reviewed '
                    'first.')),
    ),
    example(
        sq('''
CREATE CATALOG IF NOT EXISTS cdac MANAGED LOCATION 's3://cdac-uc-root/cdac';
CREATE SCHEMA  IF NOT EXISTS cdac.bda COMMENT 'PGCP-BDA course data';
CREATE VOLUME  IF NOT EXISTS cdac.bda.raw;                    -- governed folder for files

SHOW CATALOGS;
SHOW SCHEMAS IN cdac;
DESCRIBE CATALOG EXTENDED cdac;

-- who read the students table last week? (system tables)
SELECT event_time, user_identity.email, action_name
FROM   system.access.audit
WHERE  request_params.full_name_arg = 'cdac.bda.students'
  AND  event_date >= current_date() - INTERVAL 7 DAYS;

-- what feeds the gold table?
SELECT source_table_full_name, target_table_full_name, entity_type
FROM   system.access.table_lineage
WHERE  target_table_full_name = 'cdac.bda.gold_rank_list';
'''),
        title='Example'),
    steps(
        ('Create the metastore', 'One per region in the account console; assign workspaces (new workspaces get one automatically).'),
        ('Set up storage', 'Storage credentials and external locations; a managed location for catalogs.'),
        ('Design catalogs and schemas', 'By environment and domain; document ownership.'),
        ('Grant to groups', 'USE CATALOG, USE SCHEMA, SELECT, MODIFY …; owners per object.'),
        ('Monitor', 'Lineage, audit and billing system tables.'),
        title='Steps'),
    crossq(
        ('What is the difference between the Hive metastore and Unity Catalog?', 'The legacy Hive metastore is per workspace, has a two-level '
         'namespace (<code>schema.table</code>) and limited security. UC is account-level, shared by workspaces, three-level, and adds '
         'fine-grained access, lineage, auditing, volumes and models. Old Hive tables appear under the <code>hive_metastore</code> catalog until '
         'migrated.'),
        ('Can Unity Catalog govern files, not just tables?', 'Yes, through volumes (managed or external) for non-tabular files and external '
         'locations for paths used by external tables.'),
        ('Is Unity Catalog only for Databricks?', 'There is an open-source Unity Catalog project, and Databricks\' UC exposes open APIs (including '
         'an Iceberg REST catalog) so engines such as Spark, Trino or DuckDB can read governed tables.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('How do you control access to data? Explain GRANT, row filters, column masks and dynamic views.', 'Access Control', minutes=9, cards=[
    definition(
        defbox('Privileges are granted to <strong>principals</strong> (users, groups, service principals) on <strong>securables</strong>. To read '
               'a table, a principal needs <code>USE CATALOG</code> on the catalog, <code>USE SCHEMA</code> on the schema and <code>SELECT</code> '
               'on the table. Privileges granted on a catalog or schema are inherited by the objects inside it. Every object has an '
               '<strong>owner</strong> who can grant privileges on it.'),
        table(['Privilege', 'Allows'], [
            ['<code>USE CATALOG</code> / <code>USE SCHEMA</code>', 'Traverse into the container'],
            ['<code>SELECT</code>', 'Read tables and views'],
            ['<code>MODIFY</code>', 'INSERT, UPDATE, DELETE, MERGE'],
            ['<code>CREATE TABLE</code>, <code>CREATE SCHEMA</code>, …', 'Create objects in a container'],
            ['<code>READ VOLUME</code> / <code>WRITE VOLUME</code>', 'Files in a volume'],
            ['<code>EXECUTE</code>', 'Call a function or use a model'],
            ['<code>MANAGE</code>, <code>ALL PRIVILEGES</code>', 'Administer the object / everything except ownership'],
        ]),
        defbox('For finer control: a <strong>row filter</strong> is a SQL function attached to a table that returns true for rows the current '
               'user may see; a <strong>column mask</strong> is a function that returns the value or a masked version. Both can test '
               '<code>is_account_group_member()</code> or <code>current_user()</code>. <strong>Dynamic views</strong> do the same inside a view. '
               '<strong>ABAC policies</strong> apply filters and masks automatically to every table carrying a governed tag.'),
        tags('GRANT', 'REVOKE', 'USE CATALOG', 'SELECT', 'MODIFY', 'Row filter', 'Column mask', 'Dynamic view', 'ABAC'),
    ),
    analogy('Grants are the <strong>keys to buildings, floors and rooms</strong> (catalog, schema, table). A row filter is a librarian who '
            'shows each centre coordinator only their own centre\'s files; a column mask blacks out phone numbers on the copy you are given.'),
    access_anim(),
    real_world(
        scenario('Coordinators and the placement cell',
                 p('All centres share one <code>students</code> table. A row filter returns only the coordinator\'s own centre (group '
                   '<code>coord-kharghar</code> sees Kharghar rows), the exam cell sees everything, and a column mask shows phone numbers in full '
                   'only to the <code>placement-cell</code> group. There is one table to maintain instead of one copy per centre.')),
    ),
    example(
        sq('''
GRANT USE CATALOG ON CATALOG cdac       TO `exam-cell`;
GRANT USE SCHEMA  ON SCHEMA  cdac.bda   TO `exam-cell`;
GRANT SELECT      ON TABLE   cdac.bda.students TO `exam-cell`;
GRANT MODIFY      ON TABLE   cdac.bda.students TO `sp-results-pipeline`;   -- a service principal
REVOKE MODIFY     ON TABLE   cdac.bda.students FROM `faculty`;
SHOW GRANTS ON TABLE cdac.bda.students;

-- row filter: coordinators see their own centre, the exam cell sees all
CREATE OR REPLACE FUNCTION cdac.bda.centre_filter(centre STRING)
RETURN is_account_group_member('exam-cell')
    OR (centre = 'Kharghar' AND is_account_group_member('coord-kharghar'))
    OR (centre = 'Juhu'     AND is_account_group_member('coord-juhu'));
ALTER TABLE cdac.bda.students SET ROW FILTER cdac.bda.centre_filter ON (centre);

-- column mask: phone visible only to the placement cell
CREATE OR REPLACE FUNCTION cdac.bda.mask_phone(phone STRING)
RETURN CASE WHEN is_account_group_member('placement-cell') THEN phone
            ELSE concat(left(phone, 2), 'xxxxxx', right(phone, 2)) END;
ALTER TABLE cdac.bda.students ALTER COLUMN phone SET MASK cdac.bda.mask_phone;

-- dynamic view: the older way, still useful for shares and complex logic
CREATE OR REPLACE VIEW cdac.bda.students_secure AS
SELECT roll_no, name, centre,
       CASE WHEN is_account_group_member('placement-cell') THEN phone ELSE NULL END AS phone
FROM   cdac.bda.students
WHERE  is_account_group_member('exam-cell') OR centre = 'Kharghar';
'''),
        title='Example'),
    steps(
        ('Use groups', 'Grant to groups synced from the identity provider, never to individuals.'),
        ('Least privilege', 'Readers get SELECT; only pipelines (service principals) get MODIFY.'),
        ('Grant at the right level', 'Schema-level grants for a team\'s area; table-level for exceptions.'),
        ('Protect sensitive data', 'Row filters and column masks, or tag-based ABAC policies at scale.'),
        ('Review', 'SHOW GRANTS and the audit system table regularly.'),
        title='Steps'),
    crossq(
        ('Why does a user with SELECT on a table still get "permission denied"?', 'They are probably missing <code>USE CATALOG</code> or '
         '<code>USE SCHEMA</code> on the parents, or the compute they use does not support Unity Catalog (e.g. a no-isolation cluster).'),
        ('Row filter or dynamic view?', 'Row filters and masks protect the table itself, whichever way it is queried. A dynamic view only '
         'protects users who query the view, so you must also stop them reading the base table.'),
        ('Who can grant privileges?', 'The object owner, users with MANAGE on it, owners of the parent catalog/schema, and metastore admins.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('How do you handle secrets, identities and cluster security in Databricks?', 'Secrets & Identity', minutes=7, cards=[
    definition(
        table(['Concern', 'Databricks feature'], [
            ['Passwords, API keys', '<strong>Secret scopes</strong> (Databricks-backed or Azure Key Vault-backed); <code>dbutils.secrets.get(scope, key)</code>; values are redacted in output'],
            ['Non-human identities', '<strong>Service principals</strong> for jobs, pipelines and CI/CD, authenticating with OAuth'],
            ['People and groups', 'SCIM provisioning from Microsoft Entra ID, Okta, etc.; SSO; account-level groups'],
            ['Cloud storage access', '<strong>Storage credentials</strong> (IAM role, managed identity) and <strong>external locations</strong> in Unity Catalog'],
            ['Compute settings', '<strong>Cluster policies</strong>: allowed node types, max size, required tags, forced auto-termination'],
            ['Network', 'Private connectivity (PrivateLink), IP access lists, customer-managed VPC/VNet, serverless network policies'],
            ['Encryption', 'At rest and in transit by default; customer-managed keys optional'],
        ]),
        tags('Secret scope', 'dbutils.secrets', 'Service principal', 'OAuth', 'SCIM', 'Storage credential', 'Cluster policy', 'PrivateLink'),
    ),
    analogy('A secret scope is a <strong>locker</strong>: your code knows the locker number, not the combination, and the content is never '
            'printed on any report. A service principal is a <strong>department ID card</strong> that keeps working when an employee leaves.'),
    secrets_anim(),
    real_world(
        scenario('Reading from the admissions MySQL database',
                 p('The nightly job reads applications from the admissions MySQL server. The password lives in the secret scope '
                   '<code>admissions</code>; the job runs as the service principal <code>sp-admissions-sync</code>, which is the only identity with '
                   'READ on that scope and MODIFY on the bronze table. Even if someone prints the variable, the notebook shows '
                   '<code>[REDACTED]</code>. A Lakehouse Federation connection is an alternative that avoids handling the password in code.')),
    ),
    example(
        sh('''
databricks secrets create-scope admissions
databricks secrets put-secret admissions mysql-password       # prompts for the value
databricks secrets put-acl admissions sp-admissions-sync READ
databricks secrets list-secrets admissions
'''),
        py('''
password = dbutils.secrets.get(scope="admissions", key="mysql-password")
print(password)                       # prints [REDACTED]

apps = (spark.read.format("jdbc")
             .option("url", "jdbc:mysql://admissions-db.cdac.in:3306/admissions")
             .option("dbtable", "applications")
             .option("user", "dbx_reader")
             .option("password", password)
             .load())
'''),
        conf('''
{
  "spark_version":           { "type": "regex", "pattern": "1[5-9]\\\\.[0-9]+\\\\.x-scala.*" },
  "node_type_id":            { "type": "allowlist", "values": ["Standard_D4ds_v5", "Standard_D8ds_v5"] },
  "autoscale.max_workers":   { "type": "range", "maxValue": 4 },
  "autotermination_minutes": { "type": "fixed", "value": 30, "hidden": true },
  "custom_tags.course":      { "type": "unlimited", "isOptional": false }
}
''', title='Cluster policy definition'),
        title='Example'),
    steps(
        ('Store secrets in scopes', 'Never in notebooks, Git or job parameters.'),
        ('Run automation as service principals', 'Give them only the privileges the job needs.'),
        ('Use UC for storage access', 'Storage credentials + external locations instead of keys or mounts.'),
        ('Constrain compute', 'Cluster policies per team; serverless where possible.'),
        title='Steps'),
    crossq(
        ('Is redaction a security boundary?', 'No. It stops accidental printing, but code that can read a secret can still misuse it. Control who '
         'can READ the scope.'),
        ('Why are personal access tokens discouraged for automation?', 'They are tied to a person, often long-lived and broadly scoped. OAuth '
         'for service principals gives short-lived tokens and survives staff changes.'),
        ('What replaced DBFS mounts?', 'Unity Catalog external locations and volumes: access is governed per user and audited, whereas a mount '
         'gave every user of the workspace the same access.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('What are Delta Sharing, Lakehouse Federation and UniForm?', 'Sharing & Federation', minutes=8, cards=[
    definition(
        table(['Feature', 'Direction', 'What it does'], [
            ['<strong>Delta Sharing</strong>', 'Out of Databricks', 'Share live tables, views, volumes, models and notebooks with other organisations without copying. '
             '<em>Databricks-to-Databricks</em> sharing uses Unity Catalog; <em>open sharing</em> gives any client (pandas, Spark, Power BI) a credential.'],
            ['<strong>Lakehouse Federation</strong>', 'Into Databricks', 'Register external databases (MySQL, PostgreSQL, SQL Server, Snowflake, BigQuery, …) as '
             '<strong>foreign catalogs</strong> through a <strong>connection</strong> and query them in place, governed by Unity Catalog.'],
            ['<strong>UniForm</strong>', 'Format interoperability', 'Writes Apache Iceberg (and Hudi) metadata next to the Delta log, so Iceberg engines read the same files.'],
            ['<strong>Marketplace / Clean Rooms</strong>', 'Exchange', 'Publish datasets to other companies; analyse joint data without exposing raw rows.'],
        ]),
        tags('Delta Sharing', 'Share', 'Recipient', 'Open sharing', 'Lakehouse Federation', 'Foreign catalog', 'UniForm', 'Iceberg'),
    ),
    analogy('Delta Sharing is giving a partner a <strong>live window into one room</strong> of your library instead of photocopying the books. '
            'Federation is your library card working in <strong>another library</strong>: you search their shelves from your own catalogue.'),
    sharing_anim(),
    real_world(
        scenario('Sharing placement statistics with industry partners',
                 p('C-DAC shares a gold table of anonymised placement statistics with three partner companies. Two of them use Databricks and '
                   'see the share as a read-only catalog; the third reads it with the open-source <code>delta-sharing</code> Python client. '
                   'Meanwhile the admissions MySQL database is a foreign catalog, so analysts join live applications with Delta tables without '
                   'an ETL job.')),
    ),
    example(
        sq('''
-- provider side
CREATE SHARE placement_share COMMENT 'Anonymised placement statistics';
ALTER SHARE placement_share ADD TABLE cdac.gold.placement_stats;
CREATE RECIPIENT acme_corp USING ID 'aws:ap-south-1:1a2b3c4d-…';        -- Databricks-to-Databricks
CREATE RECIPIENT open_partner;                                           -- open sharing: gives an activation link
GRANT SELECT ON SHARE placement_share TO RECIPIENT acme_corp;

-- Lakehouse Federation: query MySQL in place
CREATE CONNECTION admissions_mysql TYPE mysql
OPTIONS (host 'admissions-db.cdac.in', port '3306',
         user secret('admissions', 'mysql-user'), password secret('admissions', 'mysql-password'));
CREATE FOREIGN CATALOG admissions USING CONNECTION admissions_mysql;
SELECT course, COUNT(*) FROM admissions.admissions.applications GROUP BY course;

-- UniForm: make a Delta table readable as Iceberg
ALTER TABLE cdac.gold.placement_stats SET TBLPROPERTIES (
  'delta.enableIcebergCompatV2' = 'true',
  'delta.universalFormat.enabledFormats' = 'iceberg');
'''),
        py('''
# a partner without Databricks, using the open-source client
import delta_sharing
profile = "config.share"                                  # credential file from the activation link
print(delta_sharing.SharingClient(profile).list_all_tables())
df = delta_sharing.load_as_pandas(f"{profile}#placement_share.gold.placement_stats")
'''),
        title='Example'),
    steps(
        ('Prepare the data', 'Share gold tables or views with only the columns partners need.'),
        ('Create a share and recipient', 'Add objects; grant SELECT on the share.'),
        ('Monitor', 'Audit logs show recipient access; revoke at any time.'),
        ('For external sources', 'Create a connection and a foreign catalog instead of copying.'),
        title='Steps'),
    crossq(
        ('Does the recipient pay for compute?', 'Yes. The recipient queries with their own compute (or client); the provider pays for storage and '
         'any egress, which is why sharing within the same cloud region is cheapest.'),
        ('When is federation not a good idea?', 'For heavy, repeated analytical queries: each query runs against the source database. Federation '
         'is great for exploration and occasional joins; for regular heavy use, ingest the data (for example with Lakeflow Connect).'),
        ('Delta, Iceberg, Hudi: do you have to choose?', 'Less than before: UniForm lets one Delta table be read as Iceberg, and Unity Catalog '
         'can also manage Iceberg tables, so engines with different preferences can share data.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How is MLflow used on Databricks? Explain experiments, runs, the model registry and serving.', 'MLflow & ML Lifecycle', minutes=10, cards=[
    definition(
        defbox('<strong>MLflow</strong> is an open-source platform (created by Databricks) for the ML lifecycle, built into every workspace.'),
        table(['Component', 'Purpose'], [
            ['<strong>Tracking</strong>', 'Experiments contain runs; each run logs parameters, metrics, tags and artifacts (models, plots)'],
            ['<strong>Autologging</strong>', '<code>mlflow.autolog()</code> records parameters, metrics and the model for scikit-learn, XGBoost, PyTorch, Spark ML …'],
            ['<strong>Models</strong>', 'A standard format (flavours + signature + environment) that any MLflow tool can load'],
            ['<strong>Model registry in Unity Catalog</strong>', 'Versioned models as <code>catalog.schema.model</code> with aliases (<code>@champion</code>), lineage and grants'],
            ['<strong>Model Serving</strong>', 'REST endpoints for real-time inference, with autoscaling (Mosaic AI Model Serving)'],
            ['<strong>GenAI</strong>', 'Tracing, evaluation and prompt management for LLM and agent applications (MLflow 3)'],
        ]),
        tags('MLflow', 'Experiment', 'Run', 'Autologging', 'Model registry', 'Unity Catalog models', 'Alias', 'Model Serving'),
    ),
    analogy('MLflow is a <strong>lab notebook that fills itself in</strong>: every experiment\'s settings and results are recorded, the best '
            'sample goes to the <strong>approved shelf</strong> with a version number (registry), and from there it is <strong>dispatched</strong> '
            'to whoever needs it (serving).'),
    mlflow_anim(),
    real_world(
        scenario('A placement prediction model',
                 p('A data scientist trains several models to predict placement from marks and attendance. Each run is tracked; the best one is '
                   'registered as <code>cdac.ml.placement_model</code>, version 3 gets the alias <code>@champion</code>, and a nightly job scores '
                   'the new batch with <code>models:/cdac.ml.placement_model@champion</code>. When version 4 is better, only the alias moves; the job '
                   'code does not change.')),
    ),
    example(
        pyrun('''
import mlflow, mlflow.sklearn
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

pdf = spark.sql("""SELECT CAST(marks AS DOUBLE) AS marks,
                          CASE WHEN marks >= 75 THEN 1 ELSE 0 END AS placed
                   FROM students""").toPandas()
X, y = pdf[["marks"]], pdf["placed"]

mlflow.set_experiment("/Users/student@cdac.in/placement")
for C in (0.01, 1.0):
    with mlflow.start_run(run_name=f"logreg_C{C}"):
        model = LogisticRegression(C=C).fit(X, y)
        mlflow.log_param("C", C)
        mlflow.log_metric("accuracy", accuracy_score(y, model.predict(X)))
        mlflow.sklearn.log_model(model, name="model", input_example=X.head(2))

runs = mlflow.search_runs(experiment_names=["/Users/student@cdac.in/placement"],
                          order_by=["metrics.accuracy DESC"])
print(runs[["tags.mlflow.runName", "params.C", "metrics.accuracy"]].to_string(index=False))

best = runs.iloc[0]
mv = mlflow.register_model(f"runs:/{best.run_id}/model", "placement_model")
print("registered", mv.name, "version", mv.version)

loaded = mlflow.pyfunc.load_model(f"models:/placement_model/{mv.version}")
print(loaded.predict(pd.DataFrame({"marks": [60.0, 80.0, 95.0]})))
'''),
        py('''
# on Databricks: models live in Unity Catalog
mlflow.set_registry_uri("databricks-uc")
mv = mlflow.register_model(f"runs:/{run_id}/model", "cdac.ml.placement_model")
client = mlflow.MlflowClient()
client.set_registered_model_alias("cdac.ml.placement_model", "champion", mv.version)

# batch scoring with Spark
predict = mlflow.pyfunc.spark_udf(spark, "models:/cdac.ml.placement_model@champion")
scored = spark.table("cdac.bda.students").withColumn("placed_pred", predict("marks"))
''', title='Python on Databricks (shown, not executed)'),
        p('Both runs reach an accuracy of 1.0 because <code>placed</code> is derived directly from <code>marks</code> in this toy table; on '
          'real data the runs would differ, and the sorted <code>search_runs</code> table (or the experiment UI) is how you pick the winner. '
          'Locally the model is registered under a plain name; on Databricks it gets a three-level Unity Catalog name.', top=True),
        title='Example'),
    steps(
        ('Track', 'Set an experiment; use autolog or log params, metrics and the model.'),
        ('Compare', 'Sort and chart runs in the experiment UI or with search_runs.'),
        ('Register', 'Register the chosen model in Unity Catalog; add a description and tags.'),
        ('Promote with aliases', 'Move <code>@champion</code> / <code>@challenger</code> instead of hard-coding versions.'),
        ('Deploy', 'Model Serving endpoint, or spark_udf in a batch job; monitor quality over time.'),
        title='Steps'),
    crossq(
        ('Why did MLflow drop model "stages" (Staging/Production)?', 'With the Unity Catalog registry, stages were replaced by <strong>aliases</strong>, '
         'which are flexible names pointing to versions, and by separate catalogs for environments.'),
        ('What does the model signature do?', 'It records the expected input and output schema, so serving endpoints and spark_udf can validate '
         'inputs; it is inferred from <code>input_example</code>.'),
        ('Where is Feature Engineering in this picture?', 'Feature tables are Delta tables in Unity Catalog with a primary key. Models logged with '
         'feature lookups know which features they need, so serving can fetch them automatically.'),
    ),
]),

])
