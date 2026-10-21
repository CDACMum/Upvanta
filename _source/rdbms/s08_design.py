from build import *
from rdbms.anims import *

SECTION = dict(level='expert', title='Design & Architecture', questions=[

# ------------------------------------------------------------------ 49
Q('What is the difference between OLTP and OLAP?', 'OLTP vs OLAP', minutes=7, cards=[
    definition(
        defbox('<strong>OLTP (Online Transaction Processing)</strong> systems run the day-to-day operations of a business '
               '— many small, fast reads and writes by many users (place an order, pay a fee, book a seat).',
               '<strong>OLAP (Online Analytical Processing)</strong> systems support analysis and reporting — fewer but '
               'complex queries that scan and aggregate large volumes of historical data (revenue by region by quarter).'),
        tags('OLTP', 'OLAP', 'Data Warehouse', 'Row Store', 'Column Store', 'ETL'),
    ),
    comparison(
        table(['Aspect', 'OLTP', 'OLAP'], [
            ['Purpose', 'Run the business', 'Analyse the business'],
            ['Typical query', 'Fetch/update one order by id', 'SUM of sales by month, region, product'],
            ['Operations', 'INSERT, UPDATE, DELETE, point SELECT', 'Large SELECTs with aggregations'],
            ['Rows touched per query', 'Few', 'Millions'],
            ['Data', 'Current, detailed', 'Historical, integrated, often summarised'],
            ['Schema', 'Normalized (3NF)', 'Denormalized (star / snowflake)'],
            ['Storage', 'Row-oriented', 'Usually column-oriented'],
            ['Users', 'Thousands of clerks, customers, apps', 'Analysts, managers, BI tools'],
            ['Response time', 'Milliseconds', 'Seconds to minutes'],
            ['Examples', 'MySQL, PostgreSQL, Oracle, SQL Server', 'Snowflake, Redshift, BigQuery, Hive, ClickHouse'],
        ]),
    ),
    visual(svg("""
<svg width="760" height="200" viewBox="0 0 760 200" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="200" fill="#1e293b"/>
  <defs><marker id="a3" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/></marker></defs>
  <g text-anchor="middle" font-size="13">
    <rect x="20" y="30" width="150" height="40" rx="8" fill="#0ea5e9" opacity="0.25" stroke="#0ea5e9"/><text x="95" y="55" fill="#f1f5f9">Orders DB (MySQL)</text>
    <rect x="20" y="80" width="150" height="40" rx="8" fill="#0ea5e9" opacity="0.25" stroke="#0ea5e9"/><text x="95" y="105" fill="#f1f5f9">CRM (PostgreSQL)</text>
    <rect x="20" y="130" width="150" height="40" rx="8" fill="#0ea5e9" opacity="0.25" stroke="#0ea5e9"/><text x="95" y="155" fill="#f1f5f9">Payments (Oracle)</text>
    <rect x="260" y="70" width="140" height="60" rx="10" fill="#f59e0b" opacity="0.25" stroke="#f59e0b"/><text x="330" y="97" fill="#f1f5f9" font-weight="bold">ETL / ELT</text><text x="330" y="115" fill="#cbd5e1" font-size="11">Spark, Airflow, dbt</text>
    <rect x="480" y="70" width="140" height="60" rx="10" fill="#10b981" opacity="0.25" stroke="#10b981"/><text x="550" y="97" fill="#f1f5f9" font-weight="bold">Data Warehouse</text><text x="550" y="115" fill="#cbd5e1" font-size="11">OLAP</text>
    <rect x="660" y="80" width="85" height="40" rx="8" fill="#8b5cf6" opacity="0.25" stroke="#8b5cf6"/><text x="702" y="105" fill="#f1f5f9">BI / ML</text>
    <g stroke="#94a3b8" stroke-width="2" marker-end="url(#a3)"><line x1="170" y1="50" x2="255" y2="90"/><line x1="170" y1="100" x2="255" y2="100"/><line x1="170" y1="150" x2="255" y2="112"/><line x1="400" y1="100" x2="475" y2="100"/><line x1="620" y1="100" x2="655" y2="100"/></g>
    <text x="95" y="192" fill="#38bdf8" font-size="12" font-weight="bold">OLTP sources</text>
    <text x="550" y="160" fill="#34d399" font-size="12" font-weight="bold">OLAP</text>
  </g>
</svg>""", 'Data engineers move data from OLTP sources into OLAP systems — this pipeline is the core of the job')),
    crossq(
        ('Why not run reports directly on the OLTP database?',
         'Heavy analytical scans compete with live transactions for CPU, memory and locks, slowing the business; the '
         'normalized schema needs many joins; and history may be overwritten. A read replica or a warehouse isolates the load.'),
        ('Why are column stores faster for OLAP?',
         'An aggregate like <code>SUM(amount)</code> reads only the <code>amount</code> column instead of whole rows; '
         'columns of the same type compress extremely well; and vectorised execution processes many values at once.'),
        ('What is HTAP?',
         'Hybrid Transactional/Analytical Processing — one system serving both workloads (e.g. TiDB, SingleStore, MySQL HeatWave, SQL Server columnstore on OLTP tables).'),
    ),
]),

# ------------------------------------------------------------------ 50
Q('What is the difference between Star Schema and Snowflake Schema?', 'Star vs Snowflake Schema', minutes=8, cards=[
    definition(
        defbox('Both are <strong>dimensional models</strong> used in data warehouses, with a central <strong>fact table</strong> '
               'surrounded by <strong>dimension tables</strong>.',
               '<strong>Star schema</strong> — dimensions are denormalized (one table per dimension), so the diagram looks like a star.',
               '<strong>Snowflake schema</strong> — dimensions are normalized into sub-dimensions (product → category → '
               'department), so the diagram branches like a snowflake.'),
        tags('Star Schema', 'Snowflake Schema', 'Dimensional Modelling', 'Kimball', 'Fact Table', 'Dimension Table'),
    ),
    comparison(
        table(['Aspect', 'Star', 'Snowflake'], [
            ['Dimension tables', 'Denormalized, wide', 'Normalized into several tables'],
            ['Joins per query', 'Fewer (fact → dimension)', 'More (fact → dim → sub-dim)'],
            ['Query performance', 'Faster, simpler SQL', 'Slower, more complex SQL'],
            ['Storage', 'More (redundant attribute values)', 'Less'],
            ['Maintenance of dimensions', 'Updates touch more rows', 'Easier, less redundancy'],
            ['Understandability for BI users', 'High', 'Lower'],
            ['Typical choice', 'Default for most warehouses', 'Very large or shared hierarchies'],
        ]),
    ),
    visual(svg("""
<svg width="760" height="330" viewBox="0 0 760 330" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
  <rect width="760" height="330" fill="#1e293b"/>
  <g text-anchor="middle" font-size="12">
    <text x="190" y="25" fill="#0ea5e9" font-size="15" font-weight="bold">Star</text>
    <rect x="130" y="135" width="120" height="50" rx="8" fill="#f59e0b" opacity="0.3" stroke="#f59e0b" stroke-width="2"/><text x="190" y="165" fill="#f1f5f9" font-weight="bold">fact_sales</text>
    <rect x="130" y="45" width="120" height="36" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="190" y="68" fill="#f1f5f9">dim_date</text>
    <rect x="15" y="140" width="95" height="40" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="62" y="164" fill="#f1f5f9">dim_store</text>
    <rect x="270" y="140" width="100" height="40" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="320" y="158" fill="#f1f5f9">dim_product</text><text x="320" y="173" fill="#94a3b8" font-size="10">+category</text>
    <rect x="130" y="240" width="120" height="36" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="190" y="263" fill="#f1f5f9">dim_customer</text>
    <g stroke="#64748b" stroke-width="2"><line x1="190" y1="81" x2="190" y2="135"/><line x1="110" y1="160" x2="130" y2="160"/><line x1="250" y1="160" x2="270" y2="160"/><line x1="190" y1="185" x2="190" y2="240"/></g>
    <line x1="395" y1="20" x2="395" y2="310" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>
    <text x="575" y="25" fill="#0ea5e9" font-size="15" font-weight="bold">Snowflake</text>
    <rect x="515" y="135" width="120" height="50" rx="8" fill="#f59e0b" opacity="0.3" stroke="#f59e0b" stroke-width="2"/><text x="575" y="165" fill="#f1f5f9" font-weight="bold">fact_sales</text>
    <rect x="515" y="45" width="120" height="36" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="575" y="68" fill="#f1f5f9">dim_date</text>
    <rect x="415" y="140" width="85" height="40" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="457" y="164" fill="#f1f5f9">dim_store</text>
    <rect x="655" y="140" width="95" height="40" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="702" y="164" fill="#f1f5f9">dim_product</text>
    <rect x="655" y="225" width="95" height="36" rx="6" fill="#334155" stroke="#8b5cf6"/><text x="702" y="248" fill="#f1f5f9">dim_category</text>
    <rect x="415" y="225" width="85" height="36" rx="6" fill="#334155" stroke="#8b5cf6"/><text x="457" y="248" fill="#f1f5f9">dim_city</text>
    <rect x="515" y="240" width="120" height="36" rx="6" fill="#334155" stroke="#0ea5e9"/><text x="575" y="263" fill="#f1f5f9">dim_customer</text>
    <g stroke="#64748b" stroke-width="2"><line x1="575" y1="81" x2="575" y2="135"/><line x1="500" y1="160" x2="515" y2="160"/><line x1="635" y1="160" x2="655" y2="160"/><line x1="575" y1="185" x2="575" y2="240"/><line x1="702" y1="180" x2="702" y2="225"/><line x1="457" y1="180" x2="457" y2="225"/></g>
    <text x="380" y="315" fill="#94a3b8">Snowflake splits dimensions into sub-dimensions (purple)</text>
  </g>
</svg>""", 'Same fact table — the difference is only in how the dimensions are modelled')),
    example(
        code("""
-- Star schema
CREATE TABLE dim_product (
    product_key   INT PRIMARY KEY,      -- surrogate key
    product_id    VARCHAR(20),          -- business key from source
    product_name  VARCHAR(100),
    category_name VARCHAR(50),          -- denormalized into the dimension
    brand_name    VARCHAR(50)
);

CREATE TABLE fact_sales (
    date_key     INT,
    product_key  INT,
    store_key    INT,
    customer_key INT,
    quantity     INT,
    amount       DECIMAL(12,2),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key)
    -- ... other dimension FKs
);

-- Typical analytical query
SELECT d.year, d.month, p.category_name, SUM(f.amount) AS revenue
FROM fact_sales f
JOIN dim_date d    ON d.date_key = f.date_key
JOIN dim_product p ON p.product_key = f.product_key
GROUP BY d.year, d.month, p.category_name;
"""),
        title='Example'),
    crossq(
        ('What is a galaxy (fact constellation) schema?',
         'Multiple fact tables sharing common (<strong>conformed</strong>) dimensions — e.g. fact_sales and fact_returns both using dim_date and dim_product.'),
        ('Kimball vs Inmon?',
         '<strong>Kimball</strong> (bottom-up): build dimensional data marts (star schemas) with conformed dimensions. '
         '<strong>Inmon</strong> (top-down): build a normalized enterprise warehouse (3NF) first, then derive data marts from it.'),
    ),
]),

# ------------------------------------------------------------------ 51
Q('What are Fact tables and Dimension tables?', 'Fact vs Dimension Tables', minutes=7, cards=[
    definition(
        defbox('A <strong>fact table</strong> stores the <strong>measurements</strong> of a business process — numeric, '
               'additive values such as quantity, amount, duration — plus foreign keys to dimensions. It is long and narrow '
               '(millions to billions of rows).',
               'A <strong>dimension table</strong> stores the <strong>descriptive context</strong> of those measurements — '
               'who, what, where, when: customer, product, store, date. It is short and wide (many text attributes).'),
        hl('Facts answer "how much / how many"; dimensions answer "by what" — revenue (fact) by month, city and product (dimensions).', 'In one line'),
        tags('Fact Table', 'Dimension Table', 'Measures', 'Grain', 'Additive', 'Conformed Dimension'),
    ),
    comparison(
        table(['Aspect', 'Fact table', 'Dimension table'], [
            ['Contains', 'Measures + foreign keys', 'Descriptive attributes'],
            ['Shape', 'Many rows, few columns', 'Fewer rows, many columns'],
            ['Growth', 'Grows continuously (every transaction)', 'Grows slowly'],
            ['Key', 'Composite of dimension keys (or a surrogate)', 'Surrogate key'],
            ['Example', 'fact_sales(date_key, product_key, qty, amount)', 'dim_product(product_key, name, category, brand)'],
        ]),
    ),
    explanation(
        p('<strong>Grain</strong> — the most important design decision: what one fact row represents (one line item on '
          'one bill, or one product per store per day). Declare the grain <em>before</em> choosing dimensions and facts.'),
        table(['Measure type', 'Meaning', 'Example'], [
            ['Additive', 'Can be summed across all dimensions', 'sales amount, quantity'],
            ['Semi-additive', 'Can be summed across some dimensions, not time', 'account balance, stock on hand'],
            ['Non-additive', 'Cannot be summed', 'ratios, percentages, unit price'],
        ]),
        table(['Fact table type', 'Description'], [
            ['Transaction', 'One row per event (each sale)'],
            ['Periodic snapshot', 'One row per entity per period (stock level each day)'],
            ['Accumulating snapshot', 'One row per process instance, updated as milestones occur (order → shipped → delivered)'],
            ['Factless', 'No measures, only keys — records that an event happened (student attended lecture)'],
        ]),
    ),
    crossq(
        ('What is a conformed dimension?',
         'A dimension shared by multiple fact tables / data marts with the same keys and meaning (e.g. one dim_date and '
         'one dim_customer used everywhere), so results from different marts can be compared.'),
        ('What is a degenerate dimension?',
         'A dimension attribute stored directly in the fact table with no dimension table of its own — typically the invoice or order number.'),
        ('What is a junk dimension?',
         'A single dimension that combines several low-cardinality flags and indicators (is_promo, payment_mode, channel) to avoid many tiny dimensions.'),
    ),
]),

# ------------------------------------------------------------------ 52
Q('What are Slowly Changing Dimensions (SCD)? Explain Type 1, 2 and 3', 'Slowly Changing Dimensions', minutes=9, cards=[
    definition(
        defbox('A <strong>Slowly Changing Dimension (SCD)</strong> is a dimension whose attributes change occasionally — '
               'a customer moves city, a product changes category. The SCD <strong>type</strong> decides whether and how '
               'the history of those changes is kept.'),
        table(['Type', 'Approach', 'History kept?'], [
            ['Type 0', 'Never change the value (retain original)', 'Original only'],
            ['Type 1', 'Overwrite the old value', 'No'],
            ['Type 2', 'Insert a new row for each change, with validity dates / current flag', 'Full history'],
            ['Type 3', 'Add a column for the previous value', 'Only the last change'],
            ['Type 4', 'Current values in the dimension, history in a separate history table', 'Full (separately)'],
            ['Type 6', 'Hybrid of 1 + 2 + 3', 'Full + current value on every row'],
        ]),
        tags('SCD', 'Type 1', 'Type 2', 'Type 3', 'Surrogate Key', 'Effective Date', 'Data Warehouse'),
    ),
    scd2_anim(),
    example(
        p('Customer C101 moves from <strong>Pune</strong> to <strong>Mumbai</strong> on 2026-06-01.'),
        code("""
-- TYPE 1: overwrite (history lost)
+--------------+-------------+--------+
| customer_key | customer_id | city   |
+--------------+-------------+--------+
| 1            | C101        | Mumbai |
+--------------+-------------+--------+

-- TYPE 2: new row (full history)
+--------------+-------------+--------+------------+------------+------------+
| customer_key | customer_id | city   | valid_from | valid_to   | is_current |
+--------------+-------------+--------+------------+------------+------------+
| 1            | C101        | Pune   | 2024-01-10 | 2026-05-31 | 0          |
| 2            | C101        | Mumbai | 2026-06-01 | 9999-12-31 | 1          |
+--------------+-------------+--------+------------+------------+------------+

-- TYPE 3: previous-value column (one level of history)
+--------------+-------------+--------------+---------------+
| customer_key | customer_id | current_city | previous_city |
+--------------+-------------+--------------+---------------+
| 1            | C101        | Mumbai       | Pune          |
+--------------+-------------+--------------+---------------+
""", 'The same change under each type', 'fa-table'),
        code("""
-- SCD Type 2 load in SQL (two steps, inside one transaction)
-- 1) Expire the current row if the tracked attribute changed
UPDATE dim_customer d
JOIN stg_customer s ON s.customer_id = d.customer_id
SET d.valid_to = CURRENT_DATE - INTERVAL 1 DAY,
    d.is_current = 0
WHERE d.is_current = 1
  AND d.city <> s.city;

-- 2) Insert a new current row for changed and brand-new customers
INSERT INTO dim_customer (customer_id, city, valid_from, valid_to, is_current)
SELECT s.customer_id, s.city, CURRENT_DATE, '9999-12-31', 1
FROM stg_customer s
LEFT JOIN dim_customer d
       ON d.customer_id = s.customer_id AND d.is_current = 1
WHERE d.customer_id IS NULL;
""", 'SCD Type 2 implementation'),
        title='Example'),
    interview(
        hl('Sales made while the customer lived in Pune stay linked to surrogate key 1 (Pune); new sales link to key 2 '
           '(Mumbai). That is why SCD Type 2 <strong>needs surrogate keys</strong> — customer_id C101 alone cannot tell the versions apart.', 'Why Type 2 matters'),
        p('In modern stacks SCD2 is built with <code>MERGE</code> (Delta Lake, Snowflake, BigQuery), dbt snapshots, or Spark jobs.'),
    ),
    crossq(
        ('Which SCD type is most used?',
         'Type 1 for corrections and attributes where history does not matter (spelling of a name), and Type 2 for attributes that affect analysis over time (city, segment, price category).'),
        ('How do you find the record valid on a given date in Type 2?',
         '<code>WHERE customer_id = \'C101\' AND \'2025-03-15\' BETWEEN valid_from AND valid_to</code>.'),
        ('What is a rapidly changing dimension?',
         'An attribute that changes too often for Type 2 (e.g. a customer\'s credit score monthly). It is usually split out into a separate "mini-dimension" of banded values.'),
    ),
]),

# ------------------------------------------------------------------ 53
Q('What is the CAP theorem? When would you choose RDBMS over NoSQL?', 'CAP Theorem & RDBMS vs NoSQL', minutes=8, cards=[
    definition(
        defbox('The <strong>CAP theorem</strong> (Eric Brewer, 2000) states that a distributed data store can guarantee '
               'at most two of these three properties at the same time:'),
        ul('<strong>C — Consistency</strong>: every read gets the most recent write (all nodes see the same data).',
           '<strong>A — Availability</strong>: every request gets a (non-error) response, even if some nodes are down.',
           '<strong>P — Partition tolerance</strong>: the system keeps working even if the network between nodes is cut.'),
        hl('Network partitions <em>will</em> happen in a distributed system, so P is mandatory. The real choice is: during a partition, stay <strong>consistent (CP)</strong> or stay <strong>available (AP)</strong>?', 'Practical reading'),
        tags('CAP Theorem', 'Consistency', 'Availability', 'Partition Tolerance', 'NoSQL', 'PACELC'),
    ),
    comparison(
        table(['Category', 'Behaviour during partition', 'Examples'], [
            ['CP', 'Refuse some requests to avoid inconsistent data', 'HBase, MongoDB (default), Zookeeper, Redis Cluster'],
            ['AP', 'Answer every request, may return stale data; reconcile later', 'Cassandra, DynamoDB, CouchDB'],
            ['CA', 'Only possible without partitions — a single-node system', 'Single-server MySQL/PostgreSQL'],
        ]),
        table(['Aspect', 'RDBMS', 'NoSQL'], [
            ['Data model', 'Tables with fixed schema', 'Document, key-value, column-family, graph'],
            ['Schema', 'Schema-on-write, strict', 'Flexible / schema-less'],
            ['Transactions', 'Full ACID, multi-row, multi-table', 'Often limited; BASE / eventual consistency'],
            ['Joins', 'Powerful', 'Limited — data is denormalized/embedded'],
            ['Scaling', 'Mainly vertical; horizontal via sharding (complex)', 'Horizontal by design'],
            ['Query language', 'SQL (standard)', 'Product-specific APIs'],
        ]),
        title='CAP Categories & RDBMS vs NoSQL'),
    real_world(
        table(['Choose RDBMS when…', 'Choose NoSQL when…'], [
            ['Data is structured and relationships matter', 'Data is semi-structured or the schema changes often'],
            ['You need ACID transactions (payments, inventory, bookings)', 'You need massive write throughput / horizontal scale (IoT, logs, clickstream)'],
            ['Complex ad-hoc queries and joins are needed', 'Access is by key with simple patterns'],
            ['Strong consistency is non-negotiable', 'High availability matters more than immediate consistency'],
        ]),
        note('Most real systems are <strong>polyglot</strong>: MySQL for orders, Redis for cache/sessions, Elasticsearch for search, Cassandra or a data lake for events.'),
        title='How to Choose'),
    crossq(
        ('What is PACELC?',
         'An extension of CAP: if there is a <strong>P</strong>artition, choose <strong>A</strong> or <strong>C</strong>; '
         '<strong>E</strong>lse (normal operation), choose <strong>L</strong>atency or <strong>C</strong>onsistency. '
         'E.g. Cassandra is PA/EL, a typical RDBMS cluster is PC/EC.'),
        ('Is "C" in CAP the same as "C" in ACID?',
         'No. CAP consistency means linearizability — all replicas return the latest write. ACID consistency means the database moves between states that satisfy all integrity constraints.'),
        ('What is NewSQL?',
         'Systems that offer SQL and ACID with horizontal scaling — Google Spanner, CockroachDB, TiDB, YugabyteDB.'),
    ),
]),

# ------------------------------------------------------------------ 54
Q('What is the difference between Partitioning and Sharding?', 'Partitioning vs Sharding', minutes=7, cards=[
    definition(
        defbox('<strong>Partitioning</strong> splits one large table into smaller pieces (partitions) <strong>within the '
               'same database server</strong>. The table still looks like one table to queries.',
               '<strong>Sharding</strong> splits data across <strong>multiple database servers</strong> (shards), each holding '
               'a subset of rows. It is horizontal partitioning across machines, used to scale beyond one server.'),
        tags('Partitioning', 'Sharding', 'Horizontal Scaling', 'Partition Pruning', 'Shard Key'),
    ),
    comparison(
        table(['Aspect', 'Partitioning', 'Sharding'], [
            ['Where the pieces live', 'Same server / instance', 'Different servers'],
            ['Goal', 'Manageability, faster queries via pruning, easy archiving', 'Scale writes, storage and load horizontally'],
            ['Transparency', 'Handled fully by the DBMS', 'Often needs app logic or a middleware (Vitess, Citus)'],
            ['Cross-piece queries / joins', 'Normal SQL', 'Expensive or limited'],
            ['Transactions across pieces', 'Normal', 'Need distributed transactions'],
        ]),
        table(['Partitioning type', 'How rows are assigned', 'Example'], [
            ['Horizontal (range)', 'By value ranges', 'orders by year'],
            ['Horizontal (list)', 'By explicit value lists', 'customers by region IN (\'West\', \'North\')'],
            ['Horizontal (hash)', 'By hash of a key — even spread', 'users by HASH(user_id)'],
            ['Vertical', 'Split <em>columns</em> into separate tables', 'Move a large BLOB/profile column out'],
        ]),
    ),
    example(
        code("""
-- MySQL range partitioning
CREATE TABLE orders (
    order_id   BIGINT,
    order_date DATE,
    amount     DECIMAL(10,2),
    PRIMARY KEY (order_id, order_date)          -- partition column must be in every unique key
)
PARTITION BY RANGE (YEAR(order_date)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pmax  VALUES LESS THAN MAXVALUE
);

-- Partition pruning: only p2026 is scanned
EXPLAIN SELECT SUM(amount) FROM orders
WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01';

-- Archiving old data is instant
ALTER TABLE orders DROP PARTITION p2024;
"""),
        title='Example: Partitioning in MySQL'),
    crossq(
        ('How do you choose a shard key?',
         'High cardinality, even distribution, and present in most queries so each query hits one shard (e.g. '
         '<code>customer_id</code> for an e-commerce app). Avoid monotonically increasing keys with range sharding — all new writes hit one shard (hotspot).'),
        ('What is partition pruning?',
         'The optimizer skips partitions that cannot contain matching rows, based on the WHERE condition on the partition key. Data engineers use the same idea with Hive / Spark partitioned folders (<code>/year=2026/month=10/</code>).'),
    ),
]),

# ------------------------------------------------------------------ 55
Q('What is Database Replication?', 'Replication', minutes=7, cards=[
    definition(
        defbox('<strong>Replication</strong> is keeping copies of the same data on multiple database servers. Changes made '
               'on one server (the <strong>primary / source</strong>) are copied to others (<strong>replicas</strong>).'),
        ul('<strong>High availability</strong> — if the primary fails, promote a replica (failover).',
           '<strong>Read scaling</strong> — send reporting and read-only traffic to replicas.',
           '<strong>Disaster recovery</strong> — a replica in another data centre / region.',
           '<strong>Analytics / CDC</strong> — run heavy queries or stream changes without loading the primary.'),
        tags('Replication', 'Primary-Replica', 'Master-Slave', 'Binlog', 'Failover', 'Replication Lag'),
    ),
    comparison(
        table(['Type', 'Description', 'Trade-off'], [
            ['Asynchronous', 'Primary commits, then ships changes; replicas apply later', 'Fast; replica may lag; recent commits can be lost on failover'],
            ['Semi-synchronous', 'Primary waits until at least one replica has <em>received</em> the change', 'Little/no data loss; slightly slower commits'],
            ['Synchronous', 'Primary waits until replicas have <em>applied</em> the change', 'No loss; highest latency'],
            ['Primary-replica (single-leader)', 'One writable node, many read-only', 'Simple; writes don\'t scale'],
            ['Multi-primary (multi-leader)', 'Several writable nodes', 'Write scaling; conflict resolution needed'],
        ]),
    ),
    explanation(
        p('<strong>How MySQL replication works:</strong> the primary writes every change to its <strong>binary log '
          '(binlog)</strong>. Each replica\'s I/O thread copies binlog events into its local <strong>relay log</strong>, and '
          'the SQL (applier) thread replays them. Replicas can use GTIDs (global transaction ids) to track their position.'),
        p('The same binlog is what <strong>CDC tools</strong> such as Debezium read to stream every insert/update/delete '
          'into Kafka — a very common data-engineering pattern.', True),
        title='How It Works (MySQL)'),
    crossq(
        ('What is replication lag and why does it matter?',
         'The delay between a commit on the primary and its appearance on a replica. A user who updates their profile and '
         'immediately reads from a lagging replica sees old data ("read-your-writes" problem). Fix: read critical data from the primary.'),
        ('Is replication a backup?',
         'No. A mistaken <code>DROP TABLE</code> or bad UPDATE is replicated instantly to every replica. You still need backups and point-in-time recovery (or a deliberately delayed replica).'),
    ),
]),

# ------------------------------------------------------------------ 56
Q('What are the types of Data Integrity?', 'Data Integrity Types', minutes=5, cards=[
    definition(
        defbox('<strong>Data integrity</strong> means data is accurate, consistent and valid throughout its life. An RDBMS '
               'enforces several kinds of integrity through constraints.'),
        table(['Integrity type', 'Rule', 'Enforced by'], [
            ['Entity integrity', 'Every row is uniquely identifiable; primary key is unique and NOT NULL', 'PRIMARY KEY'],
            ['Referential integrity', 'Foreign key values must exist in the referenced table (or be NULL)', 'FOREIGN KEY + ON DELETE/UPDATE actions'],
            ['Domain integrity', 'Values are of the right type, format and range', 'Data types, NOT NULL, CHECK, DEFAULT, ENUM'],
            ['User-defined (business) integrity', 'Organisation-specific rules', 'CHECK, triggers, stored procedures, application logic'],
        ]),
        tags('Entity Integrity', 'Referential Integrity', 'Domain Integrity', 'Business Rules', 'Constraints'),
    ),
    example(
        code("""
CREATE TABLE fee_payments (
    payment_id  INT PRIMARY KEY,                               -- entity integrity
    student_id  INT NOT NULL,
    amount      DECIMAL(10,2) NOT NULL CHECK (amount > 0),     -- domain integrity
    mode        ENUM('UPI', 'CARD', 'NEFT', 'CASH') NOT NULL,  -- domain integrity
    paid_on     DATE NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id)   -- referential integrity
);

-- Business rule: cash payments above ₹2,00,000 not allowed
ALTER TABLE fee_payments
ADD CONSTRAINT chk_cash_limit CHECK (mode <> 'CASH' OR amount <= 200000);
"""),
        title='Example: All Four in One Table'),
    crossq(
        ('What is physical integrity vs logical integrity?',
         '<strong>Physical</strong>: protection of stored data from hardware failure, corruption or disasters (RAID, backups, checksums). '
         '<strong>Logical</strong>: correctness of data values and relationships — the four types above.'),
        ('How do data engineers check integrity in pipelines?',
         'With data-quality tests — not-null, unique, accepted-values and relationship tests in dbt, or expectations in Great Expectations — run after every load.'),
    ),
]),

# ------------------------------------------------------------------ 57
Q('Case Study: Design the database schema for an e-commerce application', 'Case Study: E-commerce Schema', minutes=12, tag='Design', cards=[
    definition(
        defbox('Schema-design questions test whether you can turn requirements into entities, relationships, keys and '
               'constraints — and explain your trade-offs. Think aloud: <strong>requirements → entities → relationships → '
               'keys & constraints → normalization check → indexes → scale considerations</strong>.'),
        tags('Schema Design', 'Data Modelling', 'E-commerce', 'Normalization', 'Indexing'),
        title='How to Approach It'),
    explanation(
        p('<strong>Requirements (clarify first with the interviewer):</strong>'),
        ul('Customers register and can have multiple addresses.',
           'Products belong to a category; categories can have sub-categories.',
           'A customer places orders; an order has many products with quantity and the price at the time of order.',
           'Each order has one or more payments and a shipment status.',
           'Customers can review products they bought.'),
        table(['Relationship', 'Type', 'Implemented as'], [
            ['Customer – Address', '1 : N', 'customer_id FK in addresses'],
            ['Category – Category', '1 : N (self)', 'parent_id FK in categories'],
            ['Category – Product', '1 : N', 'category_id FK in products'],
            ['Customer – Order', '1 : N', 'customer_id FK in orders'],
            ['Order – Product', 'M : N', 'order_items junction table'],
            ['Order – Payment', '1 : N', 'order_id FK in payments'],
            ['Customer – Product (review)', 'M : N', 'reviews table'],
        ]),
        title='Requirements & Relationships'),
    example(
        code("""
CREATE TABLE customers (
    customer_id  BIGINT AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(100) NOT NULL,
    email        VARCHAR(150) NOT NULL UNIQUE,
    phone        VARCHAR(15),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE addresses (
    address_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id  BIGINT NOT NULL,
    line1        VARCHAR(200) NOT NULL,
    city         VARCHAR(60)  NOT NULL,
    state        VARCHAR(60)  NOT NULL,
    pincode      CHAR(6)      NOT NULL,
    is_default   BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

CREATE TABLE categories (
    category_id  INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(80) NOT NULL,
    parent_id    INT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);

CREATE TABLE products (
    product_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    sku          VARCHAR(40) NOT NULL UNIQUE,
    name         VARCHAR(200) NOT NULL,
    category_id  INT NOT NULL,
    price        DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock_qty    INT NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    is_active    BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE orders (
    order_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id  BIGINT NOT NULL,
    address_id   BIGINT NOT NULL,
    order_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status       ENUM('PLACED','PAID','SHIPPED','DELIVERED','CANCELLED') NOT NULL DEFAULT 'PLACED',
    total_amount DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (address_id)  REFERENCES addresses(address_id),
    INDEX idx_orders_customer_date (customer_id, order_date)
);

CREATE TABLE order_items (
    order_id     BIGINT,
    product_id   BIGINT,
    quantity     INT NOT NULL CHECK (quantity > 0),
    unit_price   DECIMAL(10,2) NOT NULL,      -- price at the time of order
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_items_product (product_id)
);

CREATE TABLE payments (
    payment_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id     BIGINT NOT NULL,
    amount       DECIMAL(12,2) NOT NULL,
    method       ENUM('UPI','CARD','NETBANKING','COD') NOT NULL,
    status       ENUM('PENDING','SUCCESS','FAILED','REFUNDED') NOT NULL,
    paid_at      DATETIME,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE reviews (
    customer_id  BIGINT,
    product_id   BIGINT,
    rating       TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment      TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
);
"""),
        title='Schema (MySQL)'),
    interview(
        p('<strong>Design decisions to explain — this is what earns the marks:</strong>'),
        ul('<strong>unit_price in order_items</strong> — a deliberate copy of the product price, because prices change '
           'but an old invoice must not. This is not a normalization violation; it is a different fact (price at sale time).',
           '<strong>total_amount in orders</strong> — derived and denormalized for fast listing; recomputed in the same transaction as items.',
           '<strong>Address as a separate table</strong> referenced by the order — but many systems also copy the shipping '
           'address into the order so later edits do not change past orders.',
           '<strong>Self-referencing categories</strong> for unlimited depth; query them with a recursive CTE.',
           '<strong>Indexes</strong> chosen for real queries: "my orders, latest first" → (customer_id, order_date); "who bought product X" → order_items(product_id).',
           '<strong>Stock update</strong> with <code>UPDATE products SET stock_qty = stock_qty - ? WHERE product_id = ? AND stock_qty >= ?</code> to avoid overselling.',
           '<strong>Scale</strong>: read replicas for catalogue browsing, Redis for cart/sessions, partition orders by date, '
           'shard by customer_id at very large scale, CDC to a warehouse for analytics.'),
        title='Talking Points'),
    crossq(
        ('Where would you store the shopping cart?',
         'Often in Redis (fast, temporary, per-session) or a <code>cart_items(customer_id, product_id, qty)</code> table if carts must persist across devices.'),
        ('How would you support product attributes that differ per category (size for shirts, RAM for phones)?',
         'Options: an EAV table <code>product_attributes(product_id, attr_name, attr_value)</code>, a JSON column (MySQL JSON with generated-column indexes), or a document store for the catalogue. Discuss query and validation trade-offs.'),
        ('How would you design this for analytics?',
         'Build a star schema in the warehouse: fact_order_items (grain: one product per order) with dim_date, dim_customer (SCD2 on city/segment), dim_product (SCD2 on category/price band) and dim_payment_method.'),
    ),
]),

])
