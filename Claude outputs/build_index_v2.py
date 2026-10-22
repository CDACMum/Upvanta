# Usage (from _source):  python build_index.py index_template.html ../index.html
# Generates the Upvanta index.html from the module catalogue below.
# A module with a "page" is live; one without is shown as "In preparation".
import html, json, sys

STAGES = [
    ("foundations", "Foundations", "#9AA9FF", "The language, shell, versioning and maths every data role is tested on."),
    ("collect", "Collect", "#B48CFF", "Getting data in: scraping, APIs and the formats it arrives in."),
    ("store", "Store", "#4FC3F7", "Relational and NoSQL databases, and how to model data inside them."),
    ("process", "Process", "#2EC4B6", "Batch processing at every scale, from a DataFrame to a cluster."),
    ("stream", "Stream", "#78D27E", "Events, real-time pipelines and the guarantees behind them."),
    ("orchestrate", "Orchestrate", "#E8D25A", "Scheduling, transforming and testing the pipelines themselves."),
    ("warehouse", "Warehouse", "#F29A4A", "Dimensional modelling and the cloud warehouses that serve analytics."),
    ("cloud", "Cloud", "#AEBBD0", "The managed data services on AWS, Azure and Google Cloud."),
    ("visualise", "Visualise", "#FF8FB1", "Turning results into charts, dashboards and reports."),
    ("learn", "Learn", "#FF6F61", "Machine learning, from fundamentals to models in production."),
    ("operate", "Operate", "#B8E05A", "Containers, architecture, governance and keeping it all reliable."),
]

# (stage, symbol, title, description, keywords, page or None, question count)
M = [
 ("foundations","Py","Python Fundamentals","Data types, functions, OOP, decorators, generators, error handling","python oop decorators generators functions","python.html",65),
 ("foundations","Lx","Linux & Shell Scripting","Commands, permissions, processes, bash scripting, cron jobs","linux shell bash commands scripting unix","linux.html",40),
 ("foundations","Gt","Git & Version Control","Branching, merging, pull requests, collaboration workflows","git version control branching merging github","git.html",40),
 ("foundations","St","Statistics & Probability","Hypothesis testing, distributions, A/B testing, statistical inference","statistics probability hypothesis testing distributions","statistics.html",40),
 ("foundations","Sc","Scala","Functional programming, case classes, pattern matching, collections","scala functional programming pattern matching collections jvm",None,0),
 ("foundations","Jv","OOP & Java","Object-oriented principles, inheritance, polymorphism, collections","java oop inheritance polymorphism collections",None,0),
 ("foundations","Cs","Computer Science Fundamentals","Data structures, algorithms, complexity analysis, design patterns","computer science algorithms data structures complexity",None,0),

 ("collect","Ws","Web Scraping","BeautifulSoup, Scrapy, Selenium, requests, data extraction","web scraping beautifulsoup scrapy selenium api",None,0),
 ("collect","Ap","APIs & REST","HTTP methods, authentication, rate limiting, JSON and XML parsing","api rest http authentication json xml",None,0),
 ("collect","Df","Data Formats","JSON, XML, Parquet, Avro, CSV, protocol buffers","data formats json xml parquet avro csv protobuf",None,0),

 ("store","Rd","RDBMS Fundamentals","Normalization, keys, relationships, ACID properties, database design","database sql relational normalization acid keys","rdbms.html",126),
 ("store","My","MySQL & Advanced SQL","Queries, JOINs, indexes, window functions, CTEs, EXPLAIN","mysql sql queries joins indexes optimization window functions cte explain","mysql.html",55),
 ("store","Mo","MongoDB","Documents, CRUD, aggregation pipeline, indexing, sharding","mongodb nosql document database aggregation sharding","mongodb.html",40),
 ("store","Ca","Apache Cassandra","Wide-column model, distribution, consistency levels, query-first modelling","cassandra distributed nosql wide-column consistency cql","cassandra.html",40),
 ("store","Hb","Apache HBase","Row keys, column families, regions, reads and writes on HDFS","hbase nosql hadoop column family region","hbase.html",40),
 ("store","Re","Redis","In-memory data structures, caching strategies, pub/sub, persistence","redis cache in-memory data structures pubsub","redis.html",100),
 ("store","Sq","SQL Advanced","Complex queries, performance tuning, execution plans, stored procedures","sql advanced queries optimization performance tuning",None,0),
 ("store","Dm","Data Modeling","Dimensional modelling, data vault, normalization vs denormalization","data modeling dimensional vault normalization denormalization",None,0),

 ("process","Hd","Hadoop & HDFS","HDFS architecture, MapReduce, YARN, replication, fault tolerance","hadoop hdfs mapreduce yarn distributed","hadoop.html",48),
 ("process","Hv","Apache Hive","HiveQL, partitioning, bucketing, file formats, external tables","hive hiveql partitioning bucketing sql hadoop","hive.html",40),
 ("process","Sp","Apache Spark & PySpark","RDDs, DataFrames, transformations, lazy evaluation, optimization","spark pyspark rdd dataframe transformation action","pyspark.html",44),
 ("process","Sx","PySpark Question Bank","An extended bank of Spark questions for deeper practice","spark pyspark rdd dataframe extended bank","apache-pyspark.html",226),
 ("process","Db","Databricks","Delta Lake, notebooks, jobs, Unity Catalog, MLflow","databricks delta lake spark mlflow notebooks","databricks.html",40),
 ("process","Pd","Pandas","DataFrames, cleaning, merging, groupby, time series, reshaping","pandas dataframe python data cleaning groupby","pandas.html",40),
 ("process","Np","NumPy","Arrays, vectorization, broadcasting, linear algebra","numpy arrays vectorization linear algebra statistics","numpy.html",40),
 ("process","Pl","Polars","Fast DataFrames, lazy evaluation, parallel execution","polars dataframe lazy evaluation parallel processing",None,0),
 ("process","Dk","Dask","Parallel computing, distributed DataFrames, scalable analytics","dask parallel distributed dataframe scalable",None,0),

 ("stream","Kf","Apache Kafka","Producers, consumers, topics, partitions, delivery guarantees","kafka streaming events producers consumers topics","kafka.html",35),
 ("stream","Fl","Apache Flink","Stateful stream processing, event time, windows","flink stream processing stateful event time",None,0),
 ("stream","Ss","Spark Structured Streaming","Micro-batches, watermarks, checkpointing","spark streaming structured micro-batch watermarks",None,0),
 ("stream","Rt","Real-time Analytics","Lambda and Kappa architectures, real-time pipelines","real-time analytics lambda kappa architecture",None,0),

 ("orchestrate","Af","Apache Airflow","DAGs, scheduling, operators, sensors, executors","airflow workflow orchestration dag scheduling","airflow.html",49),
 ("orchestrate","Dt","dbt","Models, materializations, tests, Jinja, documentation","dbt data build tool transformation testing documentation","dbt.html",40),
 ("orchestrate","El","ETL & ELT Concepts","Extraction, transformation patterns, loading, CDC, data quality","etl elt pipeline transformation cdc","etl.html",50),
 ("orchestrate","Bm","Apache Beam","Unified batch and stream pipelines, portability","apache beam pipeline batch stream processing",None,0),
 ("orchestrate","Ge","Great Expectations","Data validation, quality checks, automated testing","great expectations data quality validation testing",None,0),

 ("warehouse","Dw","Data Warehouse Fundamentals","Star and snowflake schemas, facts, dimensions, SCDs","data warehouse star schema dimension fact scd","dw-fundamentals.html",37),
 ("warehouse","Sf","Snowflake","Virtual warehouses, micro-partitions, time travel, data sharing","snowflake cloud warehouse virtual time travel","snowflake.html",40),
 ("warehouse","Rs","Amazon Redshift","Columnar storage, distribution styles, compression, tuning","redshift aws columnar distribution compression",None,0),
 ("warehouse","Bq","Google BigQuery","Serverless warehouse, partitioning, clustering, nested data","bigquery google serverless partitioning clustering",None,0),

 ("cloud","Cb","Cloud Computing Basics","IaaS, PaaS, SaaS, deployment models, scalability, cost","cloud computing iaas paas saas deployment",None,0),
 ("cloud","Aw","AWS Data Services","S3, Glue, Athena, EMR, Lambda, Kinesis, DynamoDB","aws ec2 s3 lambda glue athena emr kinesis",None,0),
 ("cloud","Az","Azure Data Services","Data Factory, Synapse, Data Lake, Blob Storage","azure data factory synapse databricks blob storage",None,0),
 ("cloud","Gc","Google Cloud Platform","Dataflow, Dataproc, Cloud Storage, Pub/Sub, Composer","gcp google dataflow dataproc pubsub composer",None,0),

 ("visualise","Mp","Matplotlib & Seaborn","Plot types, customisation, statistical charts in Python","matplotlib seaborn python visualization plots charts","matplotlib.html",40),
 ("visualise","Tb","Tableau","Dashboards, calculated fields, parameters, data blending","tableau dashboards visualization bi analytics",None,0),
 ("visualise","Pb","Power BI","DAX, Power Query, data modelling, report design","power bi dax query modeling visualization",None,0),

 ("learn","Sk","scikit-learn","Preprocessing, pipelines, model training, hyperparameter tuning","scikit-learn sklearn model training preprocessing pipeline machine learning","sklearn.html",40),
 ("learn","Ml","ML Fundamentals","Supervised and unsupervised learning, regression, classification, clustering","machine learning supervised unsupervised regression classification",None,0),
 ("learn","Fe","Feature Engineering","Selection, encoding, scaling, transformation techniques","feature engineering selection encoding scaling transformation",None,0),
 ("learn","Me","Model Evaluation","Metrics, cross-validation, bias-variance trade-off","model evaluation metrics cross-validation bias variance",None,0),
 ("learn","Tf","TensorFlow & Keras","Neural networks, deep learning, model deployment","tensorflow keras neural networks deep learning",None,0),
 ("learn","Pt","PyTorch","Computation graphs, model building, training loops","pytorch deep learning neural networks training",None,0),
 ("learn","Mo","MLOps","Deployment, monitoring, versioning, CI/CD for ML","mlops deployment monitoring versioning cicd",None,0),

 ("operate","Dc","Docker","Images, Dockerfiles, containers, networking","docker containers containerization dockerfile images devops",None,0),
 ("operate","K8","Kubernetes","Pods, services, deployments, orchestration","kubernetes k8s pods services deployments orchestration",None,0),
 ("operate","Sd","Data System Design","Scalability, availability, CAP theorem, trade-offs","system design scalability availability cap theorem",None,0),
 ("operate","Ds","Distributed Systems","Partitioning, replication, consistency models, fault tolerance","distributed systems partitioning replication consistency",None,0),
 ("operate","Po","Performance Optimization","Query tuning, indexing strategies, caching, partitioning","optimization performance query indexing caching",None,0),
 ("operate","Tc","Testing & CI/CD","Unit and integration tests, automated pipelines","testing cicd unit integration automated pipelines",None,0),
 ("operate","Dg","Data Governance","Data quality, metadata, lineage, privacy","data governance quality metadata lineage privacy",None,0),
 ("operate","Se","Security & Compliance","Encryption, access control, GDPR, data masking","security compliance encryption gdpr data masking",None,0),
]
# MLOps symbol clash with MongoDB
M = [(s, "Mx" if t == "MLOps" else sym, t, d, k, p, q) for (s, sym, t, d, k, p, q) in M]

e = html.escape
color = {s[0]: s[2] for s in STAGES}
ready = [m for m in M if m[5]]
total_q = sum(m[6] for m in ready)
n_ready, n_prep = len(ready), len(M) - len(ready)

def row(m):
    s, sym, t, d, k, p, q = m
    search = e(f"{t} {d} {k}".lower())
    if p:
        return f'''<li class="mod" data-s="{search}" data-ready="1"><a href="{p}" class="mod-link">
<span class="tile" aria-hidden="true">{e(sym)}</span>
<span class="mod-body"><span class="mod-title">{e(t)}</span><span class="mod-desc">{e(d)}</span></span>
<span class="mod-meta"><span class="qcount">{q}</span><span class="qlabel">questions</span></span></a></li>'''
    return f'''<li class="mod is-prep" data-s="{search}" data-ready="0"><div class="mod-link">
<span class="tile" aria-hidden="true">{e(sym)}</span>
<span class="mod-body"><span class="mod-title">{e(t)}</span><span class="mod-desc">{e(d)}</span></span>
<span class="mod-meta"><span class="prep">In preparation</span></span></div></li>'''

stations, sections = [], []
for i, (sid, name, col, desc) in enumerate(STAGES, 1):
    mods = [m for m in M if m[0] == sid]
    mods.sort(key=lambda m: (m[5] is None,))
    r = sum(1 for m in mods if m[5])
    stations.append(f'''<li class="station" style="--c:{col};--i:{i-1}"><a href="#{sid}">
<span class="track"></span><span class="dot{' is-empty' if r == 0 else ''}"></span>
<span class="st-name">{e(name)}</span><span class="st-count">{r} of {len(mods)} ready</span></a></li>''')
    sections.append(f'''<section class="stage" id="{sid}" style="--c:{col}" data-stage>
<header class="stage-head"><span class="stage-no">{i}</span><div><h2>{e(name)}</h2><p>{e(desc)}</p>
<p class="stage-ready"><span class="js-ready">{r}</span> of <span class="js-total">{len(mods)}</span> ready to practise</p></div></header>
<ul class="mods">{''.join(row(m) for m in mods)}</ul></section>''')

tpl = open(sys.argv[1], encoding="utf-8").read()
out = (tpl.replace("{{STATIONS}}", "\n".join(stations))
          .replace("{{SECTIONS}}", "\n".join(sections))
          .replace("{{TOTAL_Q}}", f"{total_q:,}")
          .replace("{{N_READY}}", str(n_ready))
          .replace("{{N_PREP}}", str(n_prep))
          .replace("{{N_ALL}}", str(len(M))))
open(sys.argv[2], "w", encoding="utf-8").write(out)
print("modules", len(M), "ready", n_ready, "questions", total_q)
