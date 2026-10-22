# Upvanta home page generator.
# Usage (from _source):  python build_index.py index_template.html ../index.html
# To publish a new module: give it a page and a question count in M below, then re-run.
import html, json, sys

STAGES = [
    ("foundations", "Foundations", "#9AA9FF"),
    ("collect", "Collect", "#B48CFF"),
    ("store", "Store", "#4FC3F7"),
    ("process", "Process", "#2EC4B6"),
    ("stream", "Stream", "#78D27E"),
    ("orchestrate", "Orchestrate", "#E8D25A"),
    ("warehouse", "Warehouse", "#F29A4A"),
    ("cloud", "Cloud", "#AEBBD0"),
    ("visualise", "Visualise", "#FF8FB1"),
    ("learn", "Learn", "#FF6F61"),
    ("operate", "Operate", "#B8E05A"),
]

# (stage, symbol, title, short description, search keywords, page or None, question count)
M = [
 ("foundations","Py","Python Fundamentals","Data types, OOP, decorators, generators","python oop decorators generators functions","python.html",65),
 ("foundations","Lx","Linux & Shell","Permissions, processes, sed, awk, scripting","linux shell bash commands scripting unix sed awk","linux.html",40),
 ("foundations","Gt","Git & GitHub","Branching, merging, rebasing, pull requests","git version control branching merging github rebase","git.html",40),
 ("foundations","St","Statistics","Distributions, hypothesis tests, CLT","statistics probability hypothesis testing distributions","statistics.html",40),
 ("foundations","Sc","Scala","","scala functional programming jvm",None,0),
 ("foundations","Jv","OOP & Java","","java oop inheritance polymorphism",None,0),
 ("foundations","Cs","CS Fundamentals","","computer science algorithms data structures complexity",None,0),

 ("collect","Ws","Web Scraping","","web scraping beautifulsoup scrapy selenium",None,0),
 ("collect","Ap","APIs & REST","","api rest http authentication json",None,0),
 ("collect","Df","Data Formats","","data formats json xml parquet avro csv",None,0),

 ("store","Rd","RDBMS Fundamentals","Keys, normalization, ACID, design","database sql relational normalization acid keys","rdbms.html",126),
 ("store","My","MySQL & Advanced SQL","Joins, indexes, window functions, CTEs","mysql sql queries joins indexes window functions cte explain","mysql.html",55),
 ("store","Mo","MongoDB","Documents, aggregation, sharding","mongodb nosql document database aggregation sharding","mongodb.html",40),
 ("store","Ca","Apache Cassandra","Partition keys, consistency, modelling","cassandra distributed nosql wide-column consistency cql","cassandra.html",40),
 ("store","Hb","Apache HBase","Row keys, column families, regions","hbase nosql hadoop column family region","hbase.html",40),
 ("store","Re","Redis","Data structures, caching, persistence","redis cache in-memory data structures pubsub","redis.html",100),
 ("store","Sq","SQL Advanced","","sql advanced tuning execution plans",None,0),
 ("store","Dm","Data Modeling","","data modeling dimensional vault",None,0),

 ("process","Hd","Hadoop & HDFS","HDFS, MapReduce, YARN","hadoop hdfs mapreduce yarn distributed","hadoop.html",48),
 ("process","Hv","Apache Hive","HiveQL, partitioning, bucketing","hive hiveql partitioning bucketing sql hadoop","hive.html",40),
 ("process","Sp","Spark & PySpark","RDDs, DataFrames, optimization","spark pyspark rdd dataframe transformation action","pyspark.html",44),
 ("process","Sx","PySpark Question Bank","Extended Spark practice","spark pyspark rdd dataframe extended bank","apache-pyspark.html",226),
 ("process","Db","Databricks","Delta Lake, jobs, Unity Catalog","databricks delta lake spark mlflow notebooks","databricks.html",40),
 ("process","Pd","Pandas","Indexing, groupby, reshaping","pandas dataframe python data cleaning groupby","pandas.html",40),
 ("process","Np","NumPy","Arrays, broadcasting, vectorization","numpy arrays vectorization linear algebra","numpy.html",40),
 ("process","Pl","Polars","","polars dataframe lazy",None,0),
 ("process","Dk","Dask","","dask parallel distributed",None,0),

 ("stream","Kf","Apache Kafka","Topics, partitions, replication","kafka streaming events producers consumers topics","kafka.html",35),
 ("stream","Fl","Apache Flink","","flink stream processing stateful",None,0),
 ("stream","Ss","Spark Streaming","","spark streaming structured micro-batch",None,0),
 ("stream","Rt","Real-time Analytics","","real-time analytics lambda kappa",None,0),

 ("orchestrate","Af","Apache Airflow","DAGs, operators, scheduling","airflow workflow orchestration dag scheduling","airflow.html",49),
 ("orchestrate","Dt","dbt","Models, tests, Jinja, lineage","dbt data build tool transformation testing","dbt.html",40),
 ("orchestrate","El","ETL & ELT","Pipelines, CDC, data quality","etl elt pipeline transformation cdc","etl.html",50),
 ("orchestrate","Bm","Apache Beam","","apache beam pipeline",None,0),
 ("orchestrate","Ge","Great Expectations","","great expectations data quality",None,0),

 ("warehouse","Dw","Data Warehousing","Star schema, facts, dimensions, SCD","data warehouse star schema dimension fact scd olap","dw-fundamentals.html",37),
 ("warehouse","Sf","Snowflake","Warehouses, micro-partitions, time travel","snowflake cloud warehouse virtual time travel","snowflake.html",40),
 ("warehouse","Rs","Amazon Redshift","","redshift aws columnar",None,0),
 ("warehouse","Bq","Google BigQuery","","bigquery google serverless",None,0),

 ("cloud","Cb","Cloud Basics","","cloud computing iaas paas saas",None,0),
 ("cloud","Aw","AWS Data Services","","aws s3 glue athena emr",None,0),
 ("cloud","Az","Azure Data Services","","azure data factory synapse",None,0),
 ("cloud","Gc","Google Cloud","","gcp dataflow dataproc pubsub",None,0),

 ("visualise","Mp","Matplotlib & Seaborn","Charts, customisation, EDA plots","matplotlib seaborn python visualization plots charts","matplotlib.html",40),
 ("visualise","Tb","Tableau","","tableau dashboards",None,0),
 ("visualise","Pb","Power BI","","power bi dax",None,0),

 ("learn","Sk","scikit-learn","Pipelines, models, tuning","scikit-learn sklearn machine learning model training","sklearn.html",40),
 ("learn","Ml","ML Fundamentals","","machine learning supervised unsupervised",None,0),
 ("learn","Fe","Feature Engineering","","feature engineering encoding scaling",None,0),
 ("learn","Me","Model Evaluation","","model evaluation metrics cross-validation",None,0),
 ("learn","Tf","TensorFlow & Keras","","tensorflow keras deep learning",None,0),
 ("learn","Pt","PyTorch","","pytorch deep learning",None,0),
 ("learn","Mx","MLOps","","mlops deployment monitoring",None,0),

 ("operate","Dc","Docker","","docker containers",None,0),
 ("operate","K8","Kubernetes","","kubernetes k8s pods",None,0),
 ("operate","Sd","System Design","","system design scalability cap",None,0),
 ("operate","Ds","Distributed Systems","","distributed systems replication consistency",None,0),
 ("operate","Po","Performance Tuning","","optimization performance indexing caching",None,0),
 ("operate","Tc","Testing & CI/CD","","testing cicd",None,0),
 ("operate","Dg","Data Governance","","data governance lineage privacy",None,0),
 ("operate","Se","Security","","security compliance encryption gdpr",None,0),
]

# Real questions from the module pages, shown in the moving ticker.
TICKER = [
 ("rdbms.html","What is a Foreign Key and Referential Integrity?"),
 ("kafka.html","How do partitions work in Kafka?"),
 ("mysql.html","What is the logical order of execution of a SELECT query?"),
 ("pyspark.html","What is an RDD? How is it different from a DataFrame?"),
 ("snowflake.html","What are micro-partitions?"),
 ("airflow.html","What is a DAG? Why must it be acyclic?"),
 ("python.html","What is the difference between \"is\" and \"==\"?"),
 ("dw-fundamentals.html","What is the Inmon vs Kimball approach?"),
 ("mongodb.html","Explain the CAP theorem. Where does MongoDB fit?"),
 ("git.html","What does git cherry-pick do and when should you use it?"),
 ("statistics.html","What is the central limit theorem and why is it so important?"),
 ("hive.html","Hive vs Spark SQL vs Impala/Trino: when do you use which?"),
 ("pandas.html","What is the difference between loc, iloc, at, iat and []?"),
 ("dbt.html","What is ref()? How does dbt build the DAG and lineage?"),
 ("cassandra.html","What does ALLOW FILTERING do? Why is it dangerous?"),
 ("etl.html","What is the difference between full and incremental extraction?"),
 ("hadoop.html","What are the roles of the NameNode and DataNode?"),
 ("linux.html","What are SUID, SGID and the sticky bit?"),
 ("numpy.html","What is the difference between a view and a copy in NumPy?"),
 ("sklearn.html","How do you handle imbalanced classes?"),
 ("databricks.html","What is schema enforcement and schema evolution in Delta Lake?"),
 ("hbase.html","Is HBase CP or AP?"),
 ("mysql.html","What is the difference between WHERE and HAVING?"),
 ("kafka.html","What is the role of ZooKeeper in Kafka? What is KRaft?"),
 ("dw-fundamentals.html","What is the difference between OLTP and OLAP?"),
 ("pyspark.html","What is a SparkSession? How do you create one?"),
 ("python.html","What is the difference between mutable and immutable objects?"),
 ("snowflake.html","How do auto-suspend and auto-resume work?"),
]

# Nodes of the animated pipeline in the hero: (column, row, page)
FLOW = [
 (0,0,"rdbms.html","RDBMS"),(0,1,"mysql.html","MySQL"),(0,2,"mongodb.html","MongoDB"),
 (1,0,"kafka.html","Kafka"),(1,1,"airflow.html","Airflow"),(1,2,"etl.html","ETL"),
 (2,0,"pyspark.html","Spark"),(2,1,"databricks.html","Databricks"),(2,2,"dbt.html","dbt"),
 (3,0,"snowflake.html","Snowflake"),(3,1,"dw-fundamentals.html","Warehouse"),(3,2,"matplotlib.html","Matplotlib"),
]
FLOW_COLS = ["Store", "Move", "Process", "Serve"]
FLOW_EDGES = [(0,3),(0,4),(1,3),(1,5),(2,4),(2,5),
              (3,6),(3,7),(4,7),(4,8),(5,6),(5,8),
              (6,9),(6,10),(7,9),(7,11),(8,10),(8,11)]

e = html.escape
col = {s[0]: s[2] for s in STAGES}
sname = {s[0]: s[1] for s in STAGES}
bypage = {m[5]: m for m in M if m[5]}
live = [m for m in M if m[5]]
soon = [m for m in M if not m[5]]
total_q = sum(m[6] for m in live)
maxq = max(m[6] for m in live)

# ---- stage tabs
tabs = ['<button class="tab is-on" role="tab" aria-selected="true" data-tab="all">All</button>']
for sid, name, c in STAGES:
    n = sum(1 for m in live if m[0] == sid)
    tabs.append(f'<button class="tab" role="tab" aria-selected="false" data-tab="{sid}" style="--c:{c}">{e(name)}<span>{n}</span></button>')

# ---- live cards
cards = []
for i, m in enumerate(live):
    s, sym, t, d, k, p, q = m
    pct = round((q / maxq) ** 0.5 * 100)
    srch = e(f"{t} {d} {k} {sname[s]}".lower())
    cards.append(f'''<a class="card" href="{p}" data-stage="{s}" data-s="{srch}" style="--c:{col[s]}">
<span class="card-top"><span class="sym">{e(sym)}</span><span class="stage-tag">{e(sname[s])}</span></span>
<span class="card-title">{e(t)}</span>
<span class="card-desc">{e(d)}</span>
<span class="card-foot"><span class="bar"><i style="--w:{pct}%"></i></span><span class="q"><b>{q}</b> Qs</span></span>
</a>''')

soon_chips = "".join(
    f'<span class="chip" data-stage="{m[0]}" data-s="{e((m[2]+" "+m[4]+" "+sname[m[0]]).lower())}" style="--c:{col[m[0]]}"><i>{e(m[1])}</i>{e(m[2])}</span>'
    for m in soon)

# ---- ticker
def tchip(p, text):
    m = bypage[p]
    return f'<a class="tq" href="{p}" style="--c:{col[m[0]]}"><i>{e(m[1])}</i>{e(text)}</a>'
half = len(TICKER) // 2
row1 = "".join(tchip(*x) for x in TICKER[:half])
row2 = "".join(tchip(*x) for x in TICKER[half:])

# ---- flow svg
X = [56, 196, 336, 476]; Y = [92, 212, 332]; R = 30
nodes_svg, edges_svg = [], []
for a, b in FLOW_EDGES:
    ca, ra, _, _ = FLOW[a]; cb, rb, _, _ = FLOW[b]
    x1, y1, x2, y2 = X[ca] + R, Y[ra], X[cb] - R, Y[rb]
    mx = (x1 + x2) / 2
    edges_svg.append(f'<path class="edge" data-from="{a}" data-to="{b}" d="M{x1} {y1} C{mx} {y1} {mx} {y2} {x2} {y2}"/>')
for i, (cc, rr, p, short) in enumerate(FLOW):
    m = bypage[p]
    nodes_svg.append(f'''<a href="{p}" class="node" data-i="{i}" style="--c:{col[m[0]]}" aria-label="{e(m[2])}">
<rect x="{X[cc]-R}" y="{Y[rr]-R}" width="{2*R}" height="{2*R}" rx="16"/>
<text class="n-sym" x="{X[cc]}" y="{Y[rr]+7}">{e(m[1])}</text>
<text class="n-name" x="{X[cc]}" y="{Y[rr]+R+20}">{e(short)}</text></a>''')
heads = "".join(f'<text class="col-head" x="{X[i]}" y="28">{n}</text>' for i, n in enumerate(FLOW_COLS))
flow_svg = f'''<svg class="flow" viewBox="0 0 532 410" role="img" aria-label="Data moving from databases through Kafka and Spark into Snowflake">
<defs><filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
{heads}<g class="edges">{"".join(edges_svg)}</g><g class="packets" filter="url(#glow)"></g><g class="nodes">{"".join(nodes_svg)}</g></svg>'''

pages = json.dumps([m[5] for m in live])

tpl = open(sys.argv[1], encoding="utf-8").read()
rep = {
    "{{TABS}}": "\n".join(tabs), "{{CARDS}}": "\n".join(cards), "{{SOON}}": soon_chips,
    "{{ROW1}}": row1, "{{ROW2}}": row2, "{{FLOW}}": flow_svg, "{{PAGES}}": pages,
    "{{TOTAL_Q}}": str(total_q), "{{TOTAL_Q_FMT}}": f"{total_q:,}", "{{N_LIVE}}": str(len(live)),
    "{{N_SOON}}": str(len(soon)), "{{N_STAGES}}": str(len(STAGES)),
}
for k, v in rep.items():
    tpl = tpl.replace(k, v)
open(sys.argv[2], "w", encoding="utf-8").write(tpl)
print("live", len(live), "soon", len(soon), "questions", total_q)
