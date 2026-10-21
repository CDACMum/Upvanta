from build import *

def etl_pipeline():
    svg = canvas(760, 300,
        stext(380, 26, 'Nightly ETL run', 'blue', 15, bold=True),
        sbox(20, 55, 140, 42, 'MySQL', 'exam marks', 'gray', step=1, focus=1),
        sbox(20, 125, 140, 42, 'REST API', 'attendance', 'gray', step=1, focus=1),
        sbox(20, 195, 140, 42, 'CSV file', 'company offers', 'gray', step=1, focus=1),
        sbox(215, 110, 120, 72, 'Extract', 'copy changed\nrows & files', 'blue', step=2, focus=2),
        sflow(160, 76, 215, 130, 'cyan', step=2), sflow(160, 146, 215, 146, 'cyan', step=2), sflow(160, 216, 215, 162, 'cyan', step=2),
        sbox(385, 110, 130, 72, 'Transform', 'clean · dedupe\njoin · derive', 'amber', step=3, focus=3),
        sflow(335, 146, 385, 146, 'amber', step=3, count=2),
        stext(450, 210, 'trim names → map codes → % attendance', 'amber', 11, step=3),
        stext(450, 226, '→ join per student → CTC band', 'amber', 11, step=3),
        sbox(565, 110, 120, 72, 'Load', 'warehouse\ntables', 'green', step=4, focus=4),
        sflow(515, 146, 565, 146, 'green', step=4, count=2),
        sbox(585, 225, 160, 50, 'Placement dashboard', '', 'purple', step=5, focus=5, size=12),
        sflow(625, 182, 665, 225, 'purple', step=5, count=2),
    )
    return anim(svg, [
        'Three <strong>source systems</strong> hold the raw data, each in a different format and owned by a different team.',
        '<strong>Extract</strong> copies only what is needed (ideally only what changed since the last run) into the pipeline, '
        'so the live systems are disturbed as little as possible.',
        '<strong>Transform</strong> applies the business rules on a processing engine: clean names, map codes, compute '
        'attendance %, join everything on student id, derive CTC bands.',
        '<strong>Load</strong> writes the clean, integrated result into warehouse tables in one controlled step.',
        'Analysts and dashboards read from the warehouse. They never query the source systems directly.',
    ])


def etl_vs_elt():
    svg = canvas(760, 320,
        stext(30, 40, 'ETL', 'blue', 16, 'start', bold=True),
        sbox(80, 20, 110, 44, 'Sources', '', 'gray', step=1),
        sbox(250, 20, 190, 44, 'ETL engine', 'transform here', 'amber', step=1, focus=1),
        sbox(500, 20, 230, 44, 'Warehouse', 'clean data only', 'green', step=1),
        sflow(190, 42, 250, 42, 'cyan', step=1, count=2), sflow(440, 42, 500, 42, 'green', step=1, count=2),
        stext(345, 90, 'raw data is NOT kept in the target', 'red', 12, step=2, focus=2),
        stext(30, 175, 'ELT', 'green', 16, 'start', bold=True),
        sbox(80, 155, 110, 44, 'Sources', '', 'gray', step=3),
        sbox(250, 130, 480, 160, '', '', 'green', step=3, fill_opacity=0.07),
        stext(490, 150, 'Cloud warehouse / lakehouse', 'green', 12, step=3),
        sbox(270, 165, 170, 50, 'raw tables', 'loaded as-is', 'blue', step=3, focus=3),
        sflow(190, 177, 270, 188, 'cyan', step=3, count=2),
        sbox(540, 165, 170, 50, 'clean models', 'SQL / dbt', 'amber', step=4, focus=4),
        sflow(440, 190, 540, 190, 'amber', step=4, count=2),
        stext(490, 250, 'bug found? → just re-run SQL on stored raw data', 'cyan', 12, step=5, focus=5),
        stext(490, 270, 'no need to extract from the source again', 'cyan', 12, step=5),
    )
    return anim(svg, [
        '<strong>ETL</strong>: data is transformed on a separate engine (Informatica, Spark, a Python server) and only the cleaned result reaches the warehouse.',
        'The warehouse never sees the raw data. To fix a transformation bug you must <strong>extract from the source again</strong>, and the source may no longer have the old data.',
        '<strong>ELT</strong>: data is loaded into the warehouse <strong>as-is</strong> first, into raw tables. Loading is fast because nothing is transformed yet.',
        'Transformations then run <strong>inside</strong> the warehouse with SQL (often dbt models), using the warehouse\'s scalable compute.',
        'Because the raw data stays in the warehouse, reprocessing is just re-running SQL. That flexibility is why ELT dominates in the cloud.',
    ])


def watermark():
    rows = [(110, '10-06 09:00'), (190, '10-07 18:30'), (360, '10-08 08:15'), (470, '10-08 10:45')]
    elems = [
        stext(380, 28, 'orders.updated_at timeline', 'blue', 14, bold=True),
        '<line x1="50" y1="150" x2="720" y2="150" stroke="#64748b" stroke-width="3"/>',
        stext(725, 155, 'time →', 'gray', 11, 'end'),
    ]
    for x, label in rows:
        elems += [f'<circle cx="{x}" cy="150" r="9" fill="#38bdf8"/>', stext(x, 178, label, '#cbd5e1', 11)]
    elems += [
        # control table
        sbox(510, 40, 220, 76, 'etl_watermark', '', 'purple', fill_opacity=0.15, top=True),
        stext(620, 82, 'last_value = 10-07 23:59', '#e2e8f0', 12, step=1, focus=1),
        '<line x1="545" y1="78" x2="695" y2="78" stroke="#ef4444" stroke-width="2" data-step="3"/>',
        stext(620, 104, 'last_value = 10-08 10:45 ✔', 'green', 12, step=3, focus=3, bold=True),
        # old watermark
        '<g data-step="1" data-focus="1"><line x1="260" y1="115" x2="260" y2="195" stroke="#fbbf24" stroke-width="3"/></g>',
        stext(260, 212, 'watermark', 'amber', 11, step=1),
        # window run N
        '<rect x="262" y="132" width="230" height="36" fill="#0ea5e9" fill-opacity="0.18" stroke="#0ea5e9" stroke-dasharray="5,4" data-step="2" data-focus="2"/>',
        stext(377, 125, 'Run N reads (watermark, max]', 'cyan', 12, step=2),
        sflow(377, 168, 377, 245, 'cyan', step=2, count=2),
        sbox(300, 245, 155, 40, 'staging → target', '', 'green', step=2),
        # new watermark
        '<g data-step="3"><line x1="492" y1="115" x2="492" y2="195" stroke="#f472b6" stroke-width="3" stroke-dasharray="6,4"/></g>',
        # new rows
        '<g data-step="4" data-focus="4"><circle cx="580" cy="150" r="9" fill="#a3e635"/><circle cx="650" cy="150" r="9" fill="#a3e635"/></g>',
        stext(615, 178, 'new changes', 'green', 11, step=4),
        '<rect x="494" y="132" width="180" height="36" fill="#10b981" fill-opacity="0.18" stroke="#10b981" stroke-dasharray="5,4" data-step="5" data-focus="5"/>',
        stext(584, 210, 'Run N+1 reads only these', 'green', 12, step=5),
        stext(150, 250, 'If a run fails, the watermark is NOT', 'red', 12, step=6, focus=6),
        stext(150, 268, 'moved → next run re-reads the window', 'red', 12, step=6),
        stext(150, 286, '→ the load must be an upsert', 'red', 12, step=6),
    ]
    return anim(canvas(760, 300, *elems), [
        'Rows in the source carry an <code>updated_at</code> timestamp. The control table <code>etl_watermark</code> remembers the highest value already loaded: <strong>10-07 23:59</strong>.',
        'Run N reads only rows with <code>updated_at</code> greater than the watermark (up to a fixed upper bound taken at the start), and loads them into staging and then the target.',
        'Only <strong>after the load succeeds</strong> is the watermark moved forward to the highest value processed: <strong>10-08 10:45</strong>.',
        'During the day the application inserts and updates more rows, each with a newer <code>updated_at</code>.',
        'Run N+1 reads only the rows after the new watermark. Old rows are never re-read, so each run stays small however big the table grows.',
        'Safety: if a run fails part-way, the watermark stays where it was, so the next run re-reads the same window. Load with MERGE/upsert so that re-reading never creates duplicates.',
    ])


def cdc_flow():
    elems = [
        sbox(15, 40, 120, 50, 'Application', '', 'gray'),
        sbox(170, 25, 160, 85, 'orders table', '', 'blue', fill_opacity=0.15, top=True),
        stext(250, 70, '5001 · PENDING', '#e2e8f0', 12, step=1),
        '<line x1="195" y1="66" x2="305" y2="66" stroke="#ef4444" stroke-width="2" data-step="2"/>',
        stext(250, 92, '5001 · PAID', 'green', 12, step=2),
        '<line x1="195" y1="88" x2="305" y2="88" stroke="#ef4444" stroke-width="2" data-step="3"/>',
        sflow(135, 65, 170, 65, 'gray', step=1, count=1),
        sbox(170, 135, 160, 150, 'binlog', '', 'amber', fill_opacity=0.12, top=True),
        sbox(182, 175, 136, 28, 'c  5001 PENDING', '', 'green', step=1, focus=1, size=11),
        sbox(182, 210, 136, 28, 'u  PENDING→PAID', '', 'amber', step=2, focus=2, size=11),
        sbox(182, 245, 136, 28, 'd  5001', '', 'red', step=3, focus=3, size=11),
        sbox(375, 160, 120, 60, 'Debezium', 'reads binlog', 'amber', step=4, focus=4),
        sflow(330, 190, 375, 190, 'amber', step=4, count=2),
        sbox(530, 160, 100, 60, 'Kafka', 'orders topic', 'purple', step=4),
        sflow(495, 190, 530, 190, 'purple', step=4, count=2),
        sbox(530, 40, 210, 70, 'Lakehouse table', 'apply in order:\nc → u → d', 'green', step=5, focus=5),
        sflow(580, 160, 620, 110, 'green', step=5, count=2),
        stext(635, 135, '5001 removed ✔', 'green', 12, step=5),
        stext(380, 300, 'Every change is captured in order, including DELETE, without querying the table', 'gray', 12, step=6, focus=6),
    ]
    return anim(canvas(760, 315, *elems), [
        'The application <strong>inserts</strong> order 5001 with status PENDING. MySQL writes the row and also records a <em>create</em> event in its <strong>binary log</strong>.',
        'The order is paid: an <strong>UPDATE</strong> changes the status. The binlog records an <em>update</em> event with both the <em>before</em> and the <em>after</em> values.',
        'The order is cancelled and <strong>deleted</strong>. The row is gone from the table, but the binlog still has a <em>delete</em> event. A timestamp-based query could never see this.',
        '<strong>Debezium</strong> (a Kafka Connect connector) reads the binlog like a replica would and publishes each event to a Kafka topic. No extra queries hit the orders table.',
        'The consumer applies the events <strong>in order</strong> (create, then update, then delete) using MERGE, so the lakehouse table ends up with exactly the same state as the source.',
        'That is why log-based CDC is preferred: low impact on the source, near real-time, captures deletes and every intermediate change.',
    ])


def dedup_rownumber():
    hdr = ['customer_id', 'city', 'updated_at']
    w = [100, 90, 150]
    rows = [['101', 'Pune', '10-01 10:00'], ['101', 'Mumbai', '10-05 09:30'], ['101', 'Mumbai', '10-05 09:30'], ['102', 'Delhi', '10-02 11:00']]
    elems = [
        stable(20, 50, hdr, rows, w, title='stg_customers', focus_rows={0: '2', 1: '2', 2: '2', 3: '2'}),
        '<g data-step="2"><rect x="16" y="73" width="348" height="82" fill="none" stroke="#fbbf24" stroke-width="2" stroke-dasharray="6,4" rx="4"/>'
        '<rect x="16" y="153" width="348" height="28" fill="none" stroke="#a78bfa" stroke-width="2" stroke-dasharray="6,4" rx="4"/></g>',
        stext(190, 215, 'PARTITION BY customer_id', 'amber', 12, step=2),
        scell(360, 50, 50, 26, 'rn', '#8b5cf6', '#fff', step=3, bold=True),
        scell(360, 76, 50, 26, '3', '#162033', '#fca5a5', step=3, focus=3),
        scell(360, 102, 50, 26, '1', '#162033', '#86efac', step=3, focus=3),
        scell(360, 128, 50, 26, '2', '#162033', '#fca5a5', step=3, focus=3),
        scell(360, 154, 50, 26, '1', '#162033', '#86efac', step=3, focus=3),
        stext(190, 235, 'ORDER BY updated_at DESC → number rows', 'purple', 12, step=3),
        '<g data-step="4"><line x1="22" y1="89" x2="405" y2="89" stroke="#ef4444" stroke-width="2"/><line x1="22" y1="141" x2="405" y2="141" stroke="#ef4444" stroke-width="2"/></g>',
        stext(190, 255, 'WHERE rn = 1 → drop the rest', 'red', 12, step=4),
        sflow(415, 128, 470, 128, 'green', step=5, count=2),
        stable(480, 90, ['customer_id', 'city'], [['101', 'Mumbai'], ['102', 'Delhi']], [110, 100], step=5, title='result', title_color='green'),
    ]
    return anim(canvas(760, 275, *elems), [
        'Staging holds 4 rows: customer 101 appears three times (an old version, a newer version and an exact duplicate from a retry); customer 102 appears once.',
        '<code>PARTITION BY customer_id</code> splits the rows into one group per business key. Each group is handled independently.',
        '<code>ORDER BY updated_at DESC</code> sorts each group newest-first and <code>ROW_NUMBER()</code> numbers the rows 1, 2, 3… Add a tie-breaker (such as batch_id) so equal timestamps are numbered the same way every run.',
        'The filter <code>WHERE rn = 1</code> keeps only the newest row of each group. The older version and the duplicate are discarded.',
        'Result: exactly one current row per customer, ready to be merged into the target.',
    ])


def merge_anim():
    w = [70, 90, 80]
    elems = [
        stable(30, 60, ['id', 'name', 'price'], [['1', 'Pen', '10'], ['2', 'Book', '120']], w, title='target: dim_product', title_color='green', step=1),
        stable(470, 60, ['id', 'name', 'price'], [['2', 'Book', '135'], ['3', 'Bag', '899']], w, title='staging: changes', title_color='blue', step=2,
               focus_rows={0: '3', 1: '4'}),
        sarrow(468, 99, 272, 112, 'amber', step=3, mid=(370, 70)),
        stext(370, 62, 'MATCHED on id → UPDATE', 'amber', 12, step=3, bold=True),
        scell(190, 112, 80, 26, '135 ✔', '#78350f', '#fde68a', step=3, focus=3, bold=True),
        sarrow(468, 125, 272, 150, 'green', step=4, mid=(370, 170)),
        stext(370, 190, 'NOT MATCHED → INSERT', 'green', 12, step=4, bold=True),
        '<g data-step="4" data-focus="4">' + scell(30, 138, 70, 26, '3', '#064e3b', '#bbf7d0') + scell(100, 138, 90, 26, 'Bag', '#064e3b', '#bbf7d0')
        + scell(190, 138, 80, 26, '899', '#064e3b', '#bbf7d0') + '</g>',
        stext(150, 200, 'id 1 not in staging → left unchanged', 'gray', 12, step=5, focus=5),
        stext(150, 218, '(with CDC: WHEN MATCHED AND op = \'D\' → DELETE)', 'gray', 11, step=5),
        stext(380, 255, 'One atomic statement: either all changes apply or none', 'cyan', 13, step=6, focus=6, bold=True),
    ]
    return anim(canvas(760, 275, *elems), [
        'The <strong>target</strong> table already holds products 1 and 2.',
        'The <strong>staging</strong> table holds today\'s changes: product 2 has a new price and product 3 is new. Staging must contain at most one row per key, so deduplicate first.',
        'MERGE joins staging to the target <code>ON t.id = s.id</code>. Product 2 <strong>matches</strong>, so the <code>WHEN MATCHED</code> branch updates its price from 120 to 135.',
        'Product 3 has <strong>no match</strong> in the target, so the <code>WHEN NOT MATCHED</code> branch inserts it.',
        'Product 1 is not in staging, so it is untouched. With CDC data, an extra branch can delete rows whose change operation is "D".',
        'All of this happens in <strong>one atomic statement</strong>. Re-running it with the same staging data gives the same result, which makes MERGE the foundation of idempotent loads.',
    ])


def idempotency_anim():
    elems = [
        stext(190, 30, 'Append-only load', 'red', 14, bold=True),
        stext(570, 30, 'Delete-then-insert by window', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="270" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
        sbox(90, 60, 200, 46, 'Run 1 inserts 08-Oct', 'revenue = ₹1,000', 'blue', step=1, focus=1),
        sbox(470, 60, 200, 46, 'Run 1: delete 08-Oct, insert', 'revenue = ₹1,000', 'blue', step=1, focus=1),
        stext(380, 135, '⚠ job fails AFTER loading, Airflow retries it', 'amber', 13, step=2, focus=2, bold=True),
        sbox(90, 160, 200, 46, 'Retry inserts again', 'revenue = ₹2,000 ✘', 'red', step=3, focus=3),
        sbox(470, 160, 200, 46, 'Retry: delete 08-Oct, insert', 'revenue = ₹1,000 ✔', 'green', step=4, focus=4),
        stext(190, 240, 'dashboard shows double revenue', 'red', 12, step=3),
        stext(570, 240, 'same result however many runs', 'green', 12, step=4),
    ]
    return anim(canvas(760, 280, *elems), [
        'Both pipelines load the sales for 8 October. After the first run both show the correct revenue of ₹1,000.',
        'The job crashes <em>after</em> the data was written but before it reported success, so the orchestrator retries it. This happens all the time in production.',
        'The append-only pipeline inserts the same rows again, and revenue doubles to ₹2,000. The pipeline is <strong>not idempotent</strong>.',
        'The second pipeline first deletes the 8-October window and then inserts it, inside one transaction (or uses MERGE / partition overwrite). Revenue stays ₹1,000 however many times it runs.',
    ])


def medallion():
    elems = [
        sbox(15, 95, 120, 70, 'Sources', 'DBs · APIs\nfiles · events', 'gray'),
        sbox(185, 70, 150, 120, 'BRONZE', 'raw, as received\nappend-only\n+ load metadata', '#b45309', step=1, focus=1),
        sflow(135, 130, 185, 130, '#d97706', step=1),
        sbox(385, 70, 150, 120, 'SILVER', 'cleaned · typed\ndeduplicated\nconformed keys', '#94a3b8', step=2, focus=2),
        sflow(335, 130, 385, 130, '#cbd5e1', step=2),
        sbox(585, 70, 160, 120, 'GOLD', 'business-level\nstar schemas\nKPIs & aggregates', '#eab308', step=3, focus=3),
        sflow(535, 130, 585, 130, '#facc15', step=3),
        stext(665, 225, 'BI · ML · reverse ETL', 'purple', 12, step=4, focus=4),
        sarrow(665, 190, 665, 210, 'purple', step=4),
        sarrow(460, 250, 260, 250, 'pink', step=5, dashed=True),
        stext(360, 272, 'bug in silver logic? rebuild silver & gold from bronze', 'pink', 12, step=5, focus=5),
        stext(380, 30, 'quality and trust increase →', 'green', 13, step=3, bold=True),
    ]
    return anim(canvas(760, 290, *elems), [
        '<strong>Bronze</strong> stores data exactly as it arrived from each source, append-only, plus metadata (load time, source file, batch id). Nothing is lost.',
        '<strong>Silver</strong> applies technical clean-up: correct types, standard formats, deduplication, NULL handling and joining keys across sources. It is the trusted single version of each entity.',
        '<strong>Gold</strong> holds business-ready data: star schemas, aggregates and KPI tables shaped for specific uses such as the sales dashboard or the placement report.',
        'Consumers (BI tools, data scientists, applications) read mostly from Gold, sometimes from Silver, and never from Bronze.',
        'Because Bronze keeps the raw history, any downstream layer can be rebuilt after a logic change. That is the main reason for the layered design.',
    ])


def lambda_kappa():
    elems = [
        stext(30, 30, 'Lambda architecture', 'blue', 14, 'start', bold=True),
        sbox(20, 75, 110, 50, 'Events', '', 'gray', step=1),
        sbox(190, 45, 170, 44, 'Batch layer', 'Spark daily · accurate', 'blue', step=1, focus=1),
        sbox(190, 110, 170, 44, 'Speed layer', 'streaming · recent', 'amber', step=2, focus=2),
        sflow(130, 92, 190, 67, 'cyan', step=1, count=2), sflow(130, 108, 190, 132, 'amber', step=2, count=2),
        sbox(420, 75, 150, 50, 'Serving layer', 'merge both views', 'green', step=3, focus=3),
        sflow(360, 67, 420, 92, 'cyan', step=3, count=2), sflow(360, 132, 420, 108, 'amber', step=3, count=2),
        stext(665, 92, '⚠ same logic', 'red', 12, step=3), stext(665, 108, 'written twice', 'red', 12, step=3),
        '<line x1="20" y1="180" x2="740" y2="180" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
        stext(30, 210, 'Kappa architecture', 'green', 14, 'start', bold=True),
        sbox(20, 230, 110, 50, 'Events', '', 'gray', step=4),
        sbox(190, 230, 170, 50, 'Kafka log', 'retained, replayable', 'purple', step=4, focus=4),
        sflow(130, 255, 190, 255, 'purple', step=4, count=2),
        sbox(420, 230, 150, 50, 'Stream processor', 'one codebase', 'amber', step=5, focus=5),
        sflow(360, 255, 420, 255, 'amber', step=5, count=2),
        sbox(620, 230, 120, 50, 'Serving', '', 'green', step=5),
        sflow(570, 255, 620, 255, 'green', step=5, count=2),
        stext(380, 300, 'reprocess = replay the log from the beginning with the new code', 'cyan', 12, step=6, focus=6),
    ]
    return anim(canvas(760, 315, *elems), [
        '<strong>Lambda</strong>: every event goes to a <strong>batch layer</strong> that periodically recomputes complete, accurate results over all history.',
        'The same events also go to a <strong>speed layer</strong> (streaming) that covers the hours since the last batch run with fast, approximate results.',
        'A serving layer merges both views for queries. The drawback is that the business logic must be written and maintained <strong>twice</strong>, in batch and in streaming code, and the two often drift apart.',
        '<strong>Kappa</strong> removes the batch layer: all data flows through a durable, replayable log such as Kafka with long retention.',
        'A single stream-processing codebase (Flink or Spark Structured Streaming) produces the serving tables.',
        'To fix a bug or change logic, you replay the log from the start through the new code. One codebase, one truth. Modern lakehouses with streaming tables follow this idea.',
    ])


def partition_pruning():
    parts = ['2026-10-04', '2026-10-05', '2026-10-06', '2026-10-07', '2026-10-08']
    elems = [stext(380, 28, "s3://lake/silver/orders/  (partitioned by order_date)", 'blue', 13, bold=True)]
    for i, d in enumerate(parts):
        x = 30 + i * 145
        hit = d >= '2026-10-07'
        elems.append(sbox(x, 50, 130, 120, f'order_date=', f'{d}\n\n3 files · 1.2 GB', 'blue', step=1,
                          focus=('3' if hit else '2'), fill_opacity=0.15))
        if not hit:
            elems.append(f'<g data-step="3"><line x1="{x}" y1="50" x2="{x+130}" y2="170" stroke="#ef4444" stroke-width="2"/>'
                         f'<line x1="{x+130}" y1="50" x2="{x}" y2="170" stroke="#ef4444" stroke-width="2"/></g>')
    elems += [
        sbox(130, 200, 500, 40, "WHERE order_date >= '2026-10-07'", '', 'amber', step=2, focus=2, size=13),
        stext(380, 268, 'Engine reads 2 of 5 folders: 2.4 GB instead of 6 GB', 'green', 13, step=3, bold=True),
        stext(380, 290, "WHERE YEAR(order_date) = 2026 or a filter on a non-partition column → no pruning", 'red', 12, step=4, focus=4),
    ]
    return anim(canvas(760, 305, *elems), [
        'The table is stored as one folder per <code>order_date</code>. Each folder holds that day\'s Parquet files.',
        'A query filters on the <strong>partition column</strong>: only orders from 7 October onward are needed.',
        'The engine compares the filter with the folder names <strong>before reading any data</strong> and skips the partitions that cannot match. This is <strong>partition pruning</strong>: 60% less data scanned, faster and cheaper.',
        'Pruning only works when the filter is on the partition column in a form the engine understands. Wrapping it in a function or filtering only on other columns forces a full scan.',
    ])


def dag_anim():
    elems = [
        sbox(20, 110, 120, 44, 'extract_orders', '', 'gray', step=1, focus=1, size=11),
        sbox(20, 40, 120, 44, 'extract_customers', '', 'gray', step=1, focus=1, size=11),
        sbox(20, 180, 120, 44, 'wait_for_file', 'sensor', 'gray', step=1, focus=1, size=11),
        sbox(200, 40, 130, 44, 'load_dim_customer', '', 'gray', step=1, size=11),
        sbox(200, 145, 130, 44, 'stage_orders', '', 'gray', step=1, size=11),
        sbox(390, 95, 130, 44, 'load_fact_sales', '', 'gray', step=1, size=11),
        sbox(570, 95, 80, 44, 'dq_checks', '', 'gray', step=1, size=11),
        sbox(680, 95, 70, 44, 'publish', '', 'gray', step=1, size=11),
        sarrow(140, 62, 198, 62, step=1), sarrow(140, 132, 198, 160, step=1), sarrow(140, 202, 198, 175, step=1),
        sarrow(330, 62, 388, 108, step=1), sarrow(330, 167, 388, 125, step=1), sarrow(520, 117, 568, 117, step=1), sarrow(650, 117, 678, 117, step=1),
        # states
        sbox(20, 40, 120, 44, 'extract_customers', '✔ success', 'green', step=2, size=11),
        sbox(20, 110, 120, 44, 'extract_orders', '✔ success', 'green', step=2, size=11),
        sbox(20, 180, 120, 44, 'wait_for_file', '✔ file arrived', 'green', step=2, size=11),
        sbox(200, 40, 130, 44, 'load_dim_customer', '✔ success', 'green', step=3, size=11),
        sbox(200, 145, 130, 44, 'stage_orders', '✘ timeout', 'red', step=3, focus=3, size=11),
        sbox(200, 145, 130, 44, 'stage_orders', '↻ retry 1 ✔', 'green', step=4, focus=4, size=11),
        sbox(390, 95, 130, 44, 'load_fact_sales', '✔ success', 'green', step=5, focus=5, size=11),
        sbox(570, 95, 80, 44, 'dq_checks', '✔ pass', 'green', step=6, focus=6, size=11),
        sbox(680, 95, 70, 44, 'publish', '✔', 'green', step=6, size=11),
        stext(380, 260, 'If dq_checks fails → publish never runs, an alert is sent, dashboards keep yesterday\'s good data', 'amber', 12, step=7, focus=7),
    ]
    return anim(canvas(760, 280, *elems), [
        'A <strong>DAG</strong> (Directed Acyclic Graph) declares tasks and their dependencies. Arrows mean "must finish before". There are no cycles, so there is always a valid order.',
        'Tasks with no upstream dependency start <strong>in parallel</strong>: two extracts and a <em>sensor</em> that waits until the vendor file lands.',
        '<code>load_dim_customer</code> succeeds, but <code>stage_orders</code> fails with a timeout. Its downstream tasks wait. They do not run on incomplete data.',
        'The orchestrator <strong>retries</strong> the failed task automatically (with a delay, as configured with retries and retry_delay). The retry succeeds. This is safe only because the task is idempotent.',
        'Once <strong>all</strong> upstream tasks have succeeded, <code>load_fact_sales</code> runs. Dimensions are always loaded before facts.',
        'Data-quality checks pass, so the <code>publish</code> step makes the new data visible to dashboards.',
        'If the checks had failed, publishing would be skipped and the team alerted. A quality gate stops bad data from reaching users.',
    ])


def quarantine():
    elems = [
        sbox(20, 110, 120, 60, 'Incoming batch', '10,000 rows', 'gray', step=1, focus=1),
        sbox(200, 95, 150, 90, 'Validation', 'schema · not-null\nranges · formats\nreferences', 'amber', step=2, focus=2),
        sflow(140, 140, 200, 140, 'gray', step=2, count=2),
        sbox(430, 40, 150, 60, 'Silver table', '9,962 valid rows', 'green', step=3, focus=3),
        sflow(350, 120, 430, 75, 'green', step=3, count=3),
        sbox(430, 180, 150, 60, 'Quarantine', '38 rows + reason', 'red', step=4, focus=4),
        sflow(350, 160, 430, 205, 'red', step=4, count=2),
        sbox(620, 180, 125, 60, 'Alert / ticket', 'if > 1% bad', 'purple', step=5, focus=5, size=12),
        sflow(580, 210, 620, 210, 'purple', step=5, count=1),
        sbox(620, 40, 125, 60, 'Re-process', 'after fix', 'blue', step=6, focus=6, size=12),
        sarrow(682, 180, 682, 104, 'blue', step=6, dashed=True),
        stext(380, 280, 'Good data keeps flowing; bad rows are kept, explained and fixable, never silently dropped', 'cyan', 12, step=6),
    ]
    return anim(canvas(760, 295, *elems), [
        'A batch of 10,000 rows arrives from a vendor file.',
        'Every row passes through <strong>validation rules</strong>: the expected columns and types, mandatory fields, value ranges, formats (email, PAN, pincode) and references (does the customer exist?).',
        'Rows that pass all rules are loaded into the Silver table, so the pipeline keeps flowing.',
        'Rows that fail are written to a <strong>quarantine (dead-letter) table</strong> together with the reason and the batch id. They are not silently dropped.',
        'If the share of bad rows crosses a threshold (say 1%), the run raises an alert or opens a ticket for the data owner. A sudden jump usually means a source problem.',
        'After the source is fixed or the rule is corrected, quarantined rows are re-processed. Nothing is lost and everything is traceable.',
    ])


def skew_anim():
    sizes = [('Pune', 18), ('Delhi', 20), ('Chennai', 16), ('Mumbai', 210), ('Agra', 14)]
    elems = [stext(380, 26, 'Rows per task after shuffling by city', 'blue', 14, bold=True)]
    for i, (city, h) in enumerate(sizes):
        x = 60 + i * 130
        color = '#ef4444' if city == 'Mumbai' else '#0ea5e9'
        elems.append(f'<g data-step="1" data-focus="{"2" if city == "Mumbai" else "1"}"><rect x="{x}" y="{250 - h}" width="80" height="{h}" fill="{color}" fill-opacity="0.5" stroke="{color}"/></g>')
        elems.append(stext(x + 40, 268, city, '#cbd5e1', 12, step=1))
    elems += [
        stext(220, 80, '1 task runs for 40 min,', 'red', 12, step=2, focus=2),
        stext(220, 98, 'the other 4 finish in 2 min', 'red', 12, step=2),
        stext(220, 116, '→ the whole stage waits', 'red', 12, step=2),
        stext(380, 290, 'Fix: salting (Mumbai → Mumbai_0..Mumbai_9), broadcast join, or Spark AQE skew-join handling', 'green', 12, step=3, focus=3),
    ]
    for j in range(10):
        x = 575 + j * 16
        elems.append(f'<g data-step="3"><rect x="{x}" y="100" width="12" height="22" fill="#10b981" fill-opacity="0.6" stroke="#10b981"/></g>')
    elems.append(stext(650, 90, 'after salting: Mumbai → 10 small tasks', 'green', 11, step=3))
    return anim(canvas(760, 305, *elems), [
        'After a shuffle (a <code>groupBy</code> or <code>join</code> on <code>city</code>), all rows with the same key go to the same task. Most cities have similar volumes.',
        'One key, <strong>Mumbai</strong>, has 10× more rows than the others. Its task runs far longer while every other executor sits idle. This is <strong>data skew</strong>: the stage is as slow as its slowest task.',
        'Fixes: <strong>salt</strong> the hot key (add a random suffix so its rows spread across many tasks, then combine the partial results), <strong>broadcast</strong> the small side of a join, or let Spark 3\'s <strong>Adaptive Query Execution</strong> split skewed partitions automatically.',
    ])


def pushdown_anim():
    elems = [
        stext(190, 28, 'Without pushdown', 'red', 14, bold=True),
        stext(570, 28, 'With predicate & projection pushdown', 'green', 14, bold=True),
        '<line x1="380" y1="15" x2="380" y2="290" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
        sbox(90, 50, 200, 50, 'MySQL / Parquet', '50 columns · 10 M rows', 'gray'),
        sbox(470, 50, 200, 50, 'MySQL / Parquet', '50 columns · 10 M rows', 'gray'),
        sflow(190, 100, 190, 170, 'red', step=1, count=6, r=6),
        stext(260, 140, '10 M rows × 50 cols', 'red', 11, step=1),
        sbox(90, 170, 200, 50, 'Spark filters', 'keeps 0.1 M rows', 'amber', step=1, focus=1),
        sbox(470, 120, 200, 40, "WHERE city = 'Pune'", 'runs at the source', 'green', step=2, focus=2, size=12),
        sflow(570, 160, 570, 225, 'green', step=2, count=2, r=4),
        stext(640, 195, '0.1 M rows × 3 cols', 'green', 11, step=3, focus=3),
        sbox(470, 225, 200, 40, 'Spark', 'tiny transfer', 'green', step=3),
        stext(190, 260, 'slow network transfer, high memory', 'red', 12, step=1),
    ]
    return anim(canvas(760, 300, *elems), [
        'Without pushdown, the engine reads <strong>every row and every column</strong> from the source, moves it all across the network, and only then filters. That is slow, memory-hungry and expensive.',
        '<strong>Predicate pushdown</strong> sends the filter (<code>WHERE city = \'Pune\'</code>) to the source: the database uses its index, and Parquet skips row groups whose min/max statistics cannot match.',
        '<strong>Projection pushdown</strong> reads only the columns the query actually uses. Together they move a tiny fraction of the data.',
    ])


def delivery_anim():
    elems = [
        sbox(20, 120, 120, 50, 'Producer', '', 'gray'),
        sbox(320, 120, 120, 50, 'Kafka', '', 'purple'),
        sbox(620, 120, 120, 50, 'Consumer → DB', '', 'gray'),
        sflow(140, 145, 320, 145, 'cyan', count=2),
        stext(380, 40, 'At-most-once', 'amber', 14, step=1, focus=1, bold=True),
        stext(380, 62, 'commit offset BEFORE processing → crash = event lost', 'amber', 12, step=1),
        sflow(440, 145, 620, 145, 'red', step=2, count=2),
        stext(530, 205, 'crash after writing, before committing offset', 'red', 12, step=2, focus=2),
        stext(530, 225, '→ event re-delivered → written TWICE (at-least-once)', 'red', 12, step=2),
        stext(380, 262, 'Exactly-once effect = at-least-once delivery + idempotent write (unique event_id + MERGE)', 'green', 13, step=3, focus=3, bold=True),
        stext(380, 284, 'or transactional sinks (Kafka transactions, Spark checkpoints + Delta)', 'green', 12, step=3),
    ]
    return anim(canvas(760, 300, *elems), [
        '<strong>At-most-once</strong>: the consumer acknowledges (commits its offset) before processing. If it crashes mid-way, the message is never processed again, so data can be <strong>lost</strong>.',
        '<strong>At-least-once</strong> (the usual default): the consumer commits after processing. If it crashes after writing but before committing, the message is delivered again, so data can be <strong>duplicated</strong>.',
        'True end-to-end <strong>exactly-once</strong> is achieved in practice by combining at-least-once delivery with an <strong>idempotent sink</strong> (deduplicate on a unique event id, MERGE on key), or with transactional writes that commit data and offsets together.',
    ])


def mysql_to_wh():
    elems = [
        sbox(15, 110, 120, 60, 'MySQL', 'orders, customers', 'blue', step=1, focus=1),
        sbox(170, 110, 120, 60, 'Debezium', 'binlog CDC', 'amber', step=2, focus=2),
        sflow(135, 140, 170, 140, 'amber', step=2, count=2),
        sbox(325, 110, 100, 60, 'Kafka', 'topic/table', 'purple', step=2),
        sflow(290, 140, 325, 140, 'purple', step=2, count=2),
        sbox(460, 40, 130, 54, 'Bronze', 'raw change events', '#b45309', step=3, focus=3),
        sflow(425, 130, 460, 75, '#d97706', step=3, count=2),
        sbox(460, 115, 130, 54, 'Silver', 'MERGE latest state', '#94a3b8', step=4, focus=4),
        sflow(525, 94, 525, 115, '#cbd5e1', step=4, count=1),
        sbox(460, 190, 130, 54, 'Gold', 'fact_sales, dims', '#eab308', step=5, focus=5),
        sflow(525, 169, 525, 190, '#facc15', step=5, count=1),
        sbox(625, 115, 125, 54, 'DQ + publish', 'tests, alerts', 'green', step=6, focus=6, size=12),
        sflow(590, 217, 640, 169, 'green', step=6, count=1),
        stext(380, 280, 'Airflow orchestrates batch steps · checkpoints & watermarks make every step restartable', 'cyan', 12, step=7, focus=7),
    ]
    return anim(canvas(760, 295, *elems), [
        'The source is the production MySQL database. The goal is to get its changes into the warehouse every few minutes without slowing the application down.',
        '<strong>Debezium</strong> reads the binlog (log-based CDC) after an initial snapshot and publishes one Kafka topic per table. The production tables are never queried in a loop.',
        'A streaming job (or Kafka Connect sink) appends raw change events, unchanged, into <strong>Bronze</strong> with metadata. This is the replayable history.',
        'A job <strong>MERGE</strong>s the latest change per primary key into <strong>Silver</strong>: ordered by binlog position, deletes applied, types fixed. Silver mirrors the source tables.',
        '<strong>Gold</strong> builds the business model: SCD2 dimensions first, then facts with surrogate-key lookups, then aggregates.',
        'Data-quality tests (row counts vs source, not-null, uniqueness, freshness) gate publishing, and failures alert the on-call engineer.',
        'Everything is idempotent and restartable: streaming checkpoints, MERGE-based loads, and an orchestrator for the batch parts and backfills.',
    ])
