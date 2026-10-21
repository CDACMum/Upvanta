from build import *
from build import _attrs
from mysql.anims import _rows, _clause


def _node(x, y, w, h, title, sub='', color='blue', step=None, focus=None, size=12):
    return sbox(x, y, w, h, title, sub, color, step=step, focus=focus, size=size)


# ------------------------------------------------------------------ s01
def arch_anim():
    elems = [
        _node(15, 40, 120, 56, 'DAG files', 'dags/*.py (bundle)', 'gray', step=1, focus='1'),
        sflow(135, 68, 175, 68, 'cyan', step=2, count=2),
        _node(175, 40, 140, 56, 'DAG Processor', 'parses files', 'purple', step=2, focus='2'),
        sflow(315, 68, 355, 140, 'purple', step=2, count=2),
        _node(330, 140, 150, 70, 'Metadata DB', 'serialized DAGs,\nruns, task states', 'amber', step=2),
        _node(175, 250, 140, 56, 'Scheduler', 'decides what runs', 'blue', step=3, focus='3'),
        sflow(315, 270, 355, 205, 'blue', step=3, count=2),
        sflow(245, 306, 245, 330, 'blue', step=4, count=2),
        _node(175, 330, 140, 50, 'Executor', 'Local / Celery / K8s', 'blue', step=4, focus='4', size=12),
        sflow(315, 355, 540, 355, 'green', step=4, count=3),
        _node(540, 320, 220, 64, 'Workers', 'run task code (Task SDK)', 'green', step=5, focus='5'),
        sflow(650, 320, 650, 220, 'green', step=5, count=2),
        _node(560, 140, 200, 80, 'API Server', 'UI + REST API +\nTask Execution API', 'pink', step=5, focus='5,6'),
        sflow(560, 180, 482, 180, 'pink', step=5, count=2),
        _node(600, 30, 160, 56, 'You (browser)', 'Airflow UI', 'gray', step=6),
        sflow(680, 86, 680, 140, 'gray', step=6, count=2),
        _node(15, 140, 130, 70, 'Triggerer', 'waits for deferred\ntasks (async)', 'cyan', step=7, focus='7'),
        sflow(145, 175, 330, 175, 'cyan', step=7, count=2),
    ]
    elems.append(stext(390, 410, 'Airflow 3: workers call the Task Execution API instead of opening the metadata DB', 'amber', 12, step=5, bold=True))
    return anim(canvas(780, 425, *elems), [
        'You write DAGs as Python files in the <strong>dags folder</strong> (in Airflow 3 a <em>DAG bundle</em>, which can also be a Git repo).',
        'The <strong>DAG processor</strong> parses the files continuously and stores a <strong>serialized</strong> version of each DAG in the <strong>metadata database</strong> (PostgreSQL or MySQL in production).',
        'The <strong>scheduler</strong> reads the serialized DAGs, creates DAG runs when their schedule is due, and decides which task instances are ready (dependencies met, slots free).',
        'Ready tasks are handed to the <strong>executor</strong>, which decides <em>where</em> they run: local processes, a Celery worker pool, or one Kubernetes pod per task.',
        '<strong>Workers</strong> execute your task code. In Airflow 3 they report state and read XComs, variables and connections through the <strong>API server</strong>\'s Task Execution API, not by connecting to the database directly.',
        'The <strong>API server</strong> also serves the web UI and the REST API, so you monitor runs, read logs and trigger DAGs through it.',
        'The <strong>triggerer</strong> runs <em>deferred</em> tasks (async sensors and waits) in an event loop, so thousands of waits cost almost nothing and occupy no worker slot.',
    ])


def dag_anim():
    elems = [
        _node(20, 60, 120, 50, 'extract', '', 'blue', step=1),
        _node(200, 20, 120, 50, 'clean', '', 'purple', step=1),
        _node(200, 100, 120, 50, 'validate', '', 'purple', step=1),
        _node(380, 60, 120, 50, 'load', '', 'green', step=1),
        sarrow(140, 80, 198, 45, 'gray', step=1), sarrow(140, 90, 198, 125, 'gray', step=1),
        sarrow(320, 45, 378, 78, 'gray', step=1), sarrow(320, 125, 378, 92, 'gray', step=1),
        stext(260, 185, 'Directed: every edge has a direction (upstream → downstream)', 'cyan', 12, step=2, bold=True),
        stext(260, 205, 'Acyclic: following arrows never brings you back to a task', 'cyan', 12, step=2, bold=True),
        _node(560, 40, 100, 44, 'A', '', 'red', step=3),
        _node(660, 120, 100, 44, 'B', '', 'red', step=3),
        _node(540, 140, 100, 44, 'C', '', 'red', step=3),
        sarrow(640, 84, 690, 118, 'red', step=3), sarrow(660, 150, 642, 158, 'red', step=3), sarrow(580, 140, 595, 86, 'red', step=3),
        stext(650, 215, 'A → B → C → A: a cycle', 'red', 12, step=3, bold=True),
        stext(650, 235, 'no task could ever start', 'red', 11, step=3),
        stext(390, 270, 'Airflow rejects it at parse time: AirflowDagCycleException', 'amber', 13, step=4, bold=True, focus='4'),
    ]
    return anim(canvas(780, 285, *elems), [
        'A DAG is a set of tasks with dependencies. Here <code>extract</code> must finish before <code>clean</code> and <code>validate</code>, which both run before <code>load</code>.',
        'It is <strong>directed</strong> (dependencies have a direction) and <strong>acyclic</strong> (no path leads back to where it started), so there is always a valid order to run the tasks.',
        'If A waited for C, C for B and B for A, none of them could ever start: a <strong>cycle</strong>.',
        'Airflow checks this when parsing the file and refuses to load a DAG with a cycle. Loops must be modelled differently, for example with dynamic task mapping or by re-triggering the DAG.',
    ])


# ------------------------------------------------------------------ s02
def deps_anim():
    elems = [
        _clause(20, 15, 740, 28, 'start &gt;&gt; [extract_orders, extract_customers] &gt;&gt; transform &gt;&gt; load', size=12, step=1),
        _node(20, 80, 110, 44, 'start', '', 'gray', step=1),
        _node(190, 55, 160, 40, 'extract_orders', '', 'blue', step=2, focus='2'),
        _node(190, 110, 160, 40, 'extract_customers', '', 'blue', step=2, focus='2'),
        sarrow(130, 95, 188, 75, 'gray', step=2), sarrow(130, 108, 188, 128, 'gray', step=2),
        _node(410, 80, 120, 44, 'transform', '', 'purple', step=3, focus='3'),
        sarrow(350, 75, 408, 95, 'gray', step=3), sarrow(350, 130, 408, 110, 'gray', step=3),
        _node(590, 80, 110, 44, 'load', '', 'green', step=3),
        sarrow(530, 102, 588, 102, 'gray', step=3),
        stext(270, 175, 'fan-out', 'cyan', 12, step=2, bold=True), stext(470, 175, 'fan-in', 'cyan', 12, step=3, bold=True),
        _clause(20, 205, 740, 28, 'cross_downstream([a1, a2], [b1, b2])   # every a → every b', size=12, step=4),
        _node(140, 250, 80, 36, 'a1', '', 'blue', step=4), _node(140, 300, 80, 36, 'a2', '', 'blue', step=4),
        _node(360, 250, 80, 36, 'b1', '', 'green', step=4), _node(360, 300, 80, 36, 'b2', '', 'green', step=4),
        sarrow(220, 268, 358, 268, 'gray', step=4), sarrow(220, 272, 358, 312, 'gray', step=4),
        sarrow(220, 314, 358, 274, 'gray', step=4), sarrow(220, 318, 358, 318, 'gray', step=4),
        stext(620, 285, '[a1, a2] &gt;&gt; [b1, b2]', 'red', 12, step=4, bold=True),
        stext(620, 303, 'is NOT allowed (list &gt;&gt; list)', 'red', 12, step=4),
    ]
    return anim(canvas(780, 350, *elems), [
        'The bit-shift operator <code>&gt;&gt;</code> means "runs before". One line can describe the whole flow.',
        'A <strong>list</strong> on the right of <code>&gt;&gt;</code> fans out: both extracts depend on <code>start</code> and run in parallel.',
        'A list on the left fans in: <code>transform</code> waits for <em>both</em> extracts (by default, trigger rule all_success).',
        'Python cannot apply <code>&gt;&gt;</code> between two lists, so for "every task in A before every task in B" use <code>cross_downstream</code>. For a long linear sequence use <code>chain(t1, t2, t3, …)</code>.',
    ])


# ------------------------------------------------------------------ s03 scheduling
def schedule_anim():
    X0, DAY = 50, 210
    elems = [stext(390, 22, 'schedule="@daily", start_date = 1 Oct 2026', '#38bdf8', 13, bold=True)]
    elems.append(f'<line x1="{X0 - 20}" y1="70" x2="{X0 + 3 * DAY + 20}" y2="70" stroke="#64748b" stroke-width="2"/>')
    for i, d in enumerate(['1 Oct 00:00', '2 Oct 00:00', '3 Oct 00:00', '4 Oct 00:00']):
        x = X0 + i * DAY
        elems.append(f'<line x1="{x}" y1="62" x2="{x}" y2="78" stroke="#94a3b8" stroke-width="2"/>')
        elems.append(stext(x, 54, d, '#cbd5e1', 11))
    # trigger timetable (Airflow 3 default)
    elems.append(stext(20, 112, 'Airflow 3 default: CronTriggerTimetable (no data interval)', 'green', 12, anchor='start', step=1, bold=True))
    for i in range(3):
        x = X0 + i * DAY
        elems.append(f'<g data-step="2" data-focus="2"><circle cx="{x}" cy="140" r="9" fill="#10b981"/></g>')
        elems.append(stext(x, 166, f'logical {i + 1} Oct', 'green', 11, step=2))
    elems.append(stext(390, 190, 'runs AT the scheduled time; logical date = run time', 'green', 12, step=2))
    # interval timetable (Airflow 2 behaviour)
    elems.append(stext(20, 232, 'Airflow 2 behaviour: CronDataIntervalTimetable', 'purple', 12, anchor='start', step=3, bold=True))
    for i in range(3):
        x = X0 + i * DAY
        elems.append(f'<g data-step="3"><rect x="{x}" y="248" width="{DAY}" height="26" rx="5" fill="#8b5cf6" fill-opacity="0.25" stroke="#8b5cf6"/></g>')
        elems.append(stext(x + DAY / 2, 266, f'data interval {i + 1} → {i + 2} Oct', '#e9d5ff', 11, step=3))
        elems.append(f'<g data-step="4" data-focus="4"><circle cx="{x + DAY}" cy="296" r="9" fill="#f59e0b"/></g>')
        elems.append(stext(x + DAY, 322, f'run for {i + 1} Oct starts here', 'amber', 11, step=4))
    elems.append(stext(390, 350, 'logical date = START of the interval, but the run happens at its END', 'amber', 12, step=4, bold=True))
    return anim(canvas(780, 365, *elems), [
        'Two timetables can interpret the same <code>@daily</code>. Airflow 3 uses <code>CronTriggerTimetable</code> by default (setting <code>create_cron_data_intervals = False</code>).',
        'A trigger timetable simply fires at each cron time. The run at 1 Oct 00:00 has logical date 1 Oct, and its data interval has zero length (start = end).',
        'Airflow 2 (and Airflow 3 with <code>CronDataIntervalTimetable</code>) gives each run a <strong>data interval</strong>: the day of data it is responsible for.',
        'The run for interval 1 → 2 Oct can only start once that day is over, at 2 Oct 00:00, yet its <strong>logical date</strong> is 1 Oct. This "runs one interval late" behaviour is the most-asked scheduling question.',
    ])


def assets_anim():
    elems = [
        _node(20, 60, 170, 70, 'DAG: load_orders', "owner: anuj", 'blue', step=1),
        sflow(190, 95, 300, 95, 'blue', step=2, count=2),
        _node(300, 60, 190, 70, 'Asset', 's3://lake/orders', 'amber', step=2, focus='2'),
        stext(395, 150, 'task declares outlets=[orders_asset]', '#fbbf24', 11, step=2),
        _node(20, 200, 170, 60, 'DAG: load_customers', 'owner: vineeta', 'blue', step=3),
        sflow(190, 230, 300, 230, 'blue', step=3, count=2),
        _node(300, 200, 190, 60, 'Asset', 's3://lake/customers', 'amber', step=3, focus='3'),
        sflow(490, 95, 560, 145, 'amber', step=4, count=2), sflow(490, 230, 560, 175, 'amber', step=4, count=2),
        _node(560, 125, 200, 70, 'DAG: sales_report', 'schedule=[orders, customers]\nowner: aarshvi', 'green', step=4, focus='4'),
        stext(660, 225, 'runs when BOTH assets are updated', 'green', 11, step=4, bold=True),
        stext(390, 290, 'no fixed time, no sensor polling: the schedule follows the data', 'amber', 12, step=5, bold=True),
    ]
    return anim(canvas(780, 305, *elems), [
        'Anuj\'s DAG writes order data to the lake.',
        'Its final task declares the <strong>Asset</strong> <code>s3://lake/orders</code> as an <strong>outlet</strong>. When the task succeeds, Airflow records an <em>asset event</em> ("orders was updated").',
        'Vineeta\'s DAG does the same for customers.',
        'Aarshvi\'s report DAG is scheduled on <em>both</em> assets. The scheduler starts it once each has received an event since its last run, regardless of the time of day.',
        'This is <strong>data-aware scheduling</strong> (called <em>Datasets</em> in Airflow 2.4–2.10). It replaces fragile "start at 6 AM and hope the upstream finished" schedules and cross-DAG sensors.',
    ])


# ------------------------------------------------------------------ s04 control flow
def xcom_anim():
    elems = [
        _node(20, 60, 170, 60, 'extract', 'return {"rows": 120}', 'blue', step=1, focus='1'),
        sflow(190, 90, 300, 90, 'blue', step=1, count=2),
        _node(300, 40, 190, 100, 'XCom store', 'key: return_value\ntask: extract\nrun: today\nvalue: {"rows": 120}', 'amber', step=2, focus='2'),
        sflow(490, 90, 590, 90, 'amber', step=3, count=2),
        _node(590, 60, 170, 60, 'report', 'xcom_pull / argument', 'green', step=3, focus='3'),
        stext(390, 175, 'small metadata only: counts, file paths, ids, flags', 'green', 12, step=4, bold=True),
        stext(390, 197, 'NOT DataFrames or files: XComs live in the metadata DB (or a custom backend)', 'red', 12, step=4, bold=True),
    ]
    return anim(canvas(780, 215, *elems), [
        'A task\'s return value is automatically <strong>pushed</strong> as an XCom with the key <code>return_value</code>.',
        'XComs are stored per DAG run and task instance. In Airflow 3 workers write them through the API server, which saves them in the metadata DB.',
        'A downstream task <strong>pulls</strong> the value. With TaskFlow you just pass the return value as an argument and Airflow pulls it for you (and also sets the dependency).',
        'Keep XComs small. Pass a <em>reference</em> (an S3 path, a table name) and keep the data itself in storage.',
    ])


def branch_anim():
    elems = [
        _node(20, 110, 130, 50, 'check_day', '@task.branch', 'amber', step=1, focus='1'),
        _node(240, 40, 150, 46, 'weekday_load', '', 'green', step=2, focus='2'),
        _node(240, 180, 150, 46, 'weekend_load', 'skipped', 'gray', step=2),
        sarrow(150, 125, 238, 66, 'green', step=2), sarrow(150, 145, 238, 200, 'gray', step=2, dashed=True),
        stext(85, 100, 'returns "weekday_load"', 'green', 11, step=2),
        _node(500, 60, 230, 50, 'join (all_success)', 'SKIPPED: an upstream was skipped', 'red', step=3, focus='3', size=12),
        _node(500, 160, 230, 50, 'join (none_failed_min_one_success)', 'runs ✔', 'green', step=4, focus='4', size=11),
        sarrow(390, 63, 498, 85, 'gray', step=3), sarrow(390, 200, 498, 92, 'gray', step=3, dashed=True),
        sarrow(390, 70, 498, 180, 'gray', step=4), sarrow(390, 203, 498, 190, 'gray', step=4, dashed=True),
    ]
    return anim(canvas(780, 245, *elems), [
        'A <strong>branch</strong> task returns the task_id (or list of ids) that should run next.',
        'Airflow follows that branch and marks every other directly downstream task as <strong>skipped</strong>.',
        'Trap: a join task with the default trigger rule <code>all_success</code> is <strong>skipped too</strong>, because skip propagates downstream.',
        'Give the join task <code>trigger_rule="none_failed_min_one_success"</code>: it runs if at least one branch succeeded and none failed.',
    ])


def mapping_anim():
    elems = [
        _node(20, 120, 150, 56, 'list_files', 'returns 3 paths', 'blue', step=1, focus='1'),
        stext(95, 205, "['anuj.csv', 'vineeta.csv',", '#cbd5e1', 11, step=1),
        stext(95, 221, "'aarshvi.csv']", '#cbd5e1', 11, step=1),
    ]
    for i, n in enumerate(['anuj.csv', 'vineeta.csv', 'aarshvi.csv']):
        y = 40 + i * 85
        elems.append(_node(270, y, 190, 56, f'process[{i}]', n, 'purple', step=2, focus='2'))
        elems.append(sflow(170, 148, 268, y + 28, 'blue', step=2, count=2))
        elems.append(sflow(460, y + 28, 560, 148, 'purple', step=3, count=2))
    elems.append(_node(560, 120, 190, 56, 'summarize', 'gets a list of 3 results', 'green', step=3, focus='3'))
    elems.append(stext(390, 300, 'process.expand(path=list_files()): the number of copies is decided at RUN time', 'amber', 12, step=4, bold=True))
    return anim(canvas(780, 315, *elems), [
        'An upstream task returns a list. Its length is not known when the DAG file is written: today 3 files, tomorrow maybe 50.',
        '<code>.expand()</code> creates one <strong>mapped task instance per element</strong> at run time: <code>process[0]</code>, <code>process[1]</code>, <code>process[2]</code>. They run in parallel and retry independently.',
        'A downstream task that takes the mapped output receives <strong>all results as a list</strong> (a "reduce" step).',
        'This replaces generating tasks in a Python loop at parse time, which can only use information available when the file is parsed.',
    ])


def trigger_rules_anim():
    ups = [('extract_a', 'success', 'green'), ('extract_b', 'failed', 'red'), ('extract_c', 'skipped', 'gray')]
    elems = [stext(110, 25, 'upstream task states', '#94a3b8', 12, bold=True)]
    for i, (n, st, c) in enumerate(ups):
        elems.append(_node(20, 40 + i * 62, 180, 50, n, st, c, step=1))
    rules = [
        ('all_success (default)', '✘ upstream_failed', 'red', 2),
        ('all_failed', '✘ skipped', 'red', 2),
        ('all_done', '✔ runs', 'green', 3),
        ('one_success', '✔ runs', 'green', 3),
        ('one_failed', '✔ runs', 'green', 3),
        ('none_failed', '✘ upstream_failed', 'red', 4),
        ('none_skipped', '✘ skipped', 'red', 4),
        ('none_failed_min_one_success', '✘ upstream_failed', 'red', 4),
        ('always', '✔ runs', 'green', 3),
    ]
    for i, (r, res, c, st) in enumerate(rules):
        col, row = i % 3, i // 3
        x, y = 240 + col * 180, 40 + row * 70
        elems.append(_node(x, y, 170, 56, r, res, c, step=st, focus=str(st), size=11))
    for i in range(3):
        elems.append(sflow(200, 65 + i * 62, 238, 68 + i * 70, 'gray', step=1, count=1))
    elems.append(stext(400, 268, 'Run state is decided by the LEAF tasks: if a cleanup leaf with all_done succeeds,', 'amber', 12, step=5, bold=True))
    elems.append(stext(400, 288, 'the DAG run can show success even though extract_b failed', 'amber', 12, step=5, bold=True))
    return anim(canvas(790, 300, *elems), [
        'A downstream task has three upstream tasks that ended as <strong>success</strong>, <strong>failed</strong> and <strong>skipped</strong>. Its <code>trigger_rule</code> decides whether it runs.',
        'With the default <code>all_success</code> it does not run and is marked <strong>upstream_failed</strong>. <code>all_failed</code> needs every upstream to fail.',
        '<code>all_done</code> (all finished, whatever the result), <code>one_success</code>, <code>one_failed</code> and <code>always</code> let it run. These suit cleanup, alerting and "best effort" tasks.',
        'The <code>none_*</code> rules are about tolerating skips. They still stop on a failure, which is what you want for a join after branching.',
        'Careful: the DAG run\'s final state comes from its leaf tasks. An <code>all_done</code> cleanup task at the end can hide upstream failures unless you add alerts or a final check task.',
    ])


# ------------------------------------------------------------------ s05 sensors / pools
def sensor_modes_anim():
    X0, X1 = 170, 760
    W = X1 - X0
    elems = [stext(465, 22, 'Waiting 60 minutes for a file that arrives at minute 60', '#38bdf8', 13, bold=True)]
    for k in range(0, 7):
        x = X0 + W * k / 6
        elems.append(stext(x, 42, f'{k * 10}m', '#64748b', 10))
    lanes = [('poke', 'amber', 2), ('reschedule', 'purple', 3), ('deferrable', 'green', 4)]
    for i, (name, col, st) in enumerate(lanes):
        y = 60 + i * 80
        elems.append(stext(20, y + 28, f'mode="{name}"' if name != 'deferrable' else 'deferrable=True', PALETTE[col], 12, anchor='start', bold=True, step=1))
        elems.append(f'<g data-step="1"><rect x="{X0}" y="{y + 10}" width="{W}" height="30" rx="5" fill="#162033" stroke="#334155"/></g>')
    # poke: occupies slot the whole time
    y = 70
    elems.append(f'<g data-step="2" data-focus="2"><rect x="{X0}" y="{y}" width="{W}" height="30" rx="5" fill="#f59e0b" fill-opacity="0.55"/></g>')
    elems.append(stext(X0 + W / 2, y + 20, 'worker slot busy for 60 min (sleeping between pokes)', '#fff', 11, step=2, bold=True))
    # reschedule: short bursts
    y = 150
    bursts = ''.join(f'<rect x="{X0 + W * k / 12}" y="{y}" width="8" height="30" fill="#8b5cf6"/>' for k in range(0, 13))
    elems.append(f'<g data-step="3" data-focus="3">{bursts}</g>')
    elems.append(stext(X0 + W / 2, y + 48, 'slot used only for a few seconds every 5 min; state up_for_reschedule in between', 'purple', 11, step=3))
    # deferrable
    y = 230
    elems.append(f'<g data-step="4" data-focus="4"><rect x="{X0}" y="{y}" width="8" height="30" fill="#10b981"/><rect x="{X1 - 8}" y="{y}" width="8" height="30" fill="#10b981"/>'
                 f'<rect x="{X0 + 10}" y="{y + 10}" width="{W - 20}" height="10" fill="#06b6d4" fill-opacity="0.35"/></g>')
    elems.append(stext(X0 + W / 2, y + 48, 'worker starts, defers, frees its slot; the triggerer waits asynchronously; a worker resumes it', 'green', 11, step=4))
    elems.append(stext(400, 325, 'One triggerer can wait for thousands of deferred tasks at once', 'amber', 12, step=5, bold=True))
    return anim(canvas(780, 340, *elems), [
        'A sensor waits for a condition. Three ways to wait for the same file that only appears after an hour.',
        '<strong>poke</strong> (default): the task keeps its worker slot for the whole wait, sleeping between checks. Simple, but 100 waiting sensors = 100 blocked slots.',
        '<strong>reschedule</strong>: after each check the task gives back its slot and is rescheduled for the next check. Good for long waits with a large <code>poke_interval</code>.',
        '<strong>deferrable</strong>: the task hands the wait to a <strong>trigger</strong> running in the triggerer (async event loop) and exits. When the trigger fires, the task resumes on a worker.',
        'Prefer deferrable versions of sensors and long-running operators where they exist (many provider operators have <code>deferrable=True</code>).',
    ])


def pools_anim():
    elems = [stext(130, 25, 'queued tasks (priority_weight)', '#94a3b8', 12, bold=True)]
    tasks = [('load_anuj', '1'), ('load_vineeta', '5'), ('load_aarshvi', '3'), ('load_ravi', '1'), ('load_neha', '1')]
    for i, (n, w) in enumerate(tasks):
        elems.append(_node(20, 40 + i * 52, 220, 42, f'{n}', f'priority_weight={w}', 'blue', step=1, size=12))
    elems.append(_node(330, 90, 170, 130, 'Pool: mysql_pool', 'slots = 2', 'amber', step=2, focus='2'))
    elems.append(_node(590, 60, 170, 46, 'running: load_vineeta', '', 'green', step=3, focus='3', size=11))
    elems.append(_node(590, 120, 170, 46, 'running: load_aarshvi', '', 'green', step=3, focus='3', size=11))
    elems.append(sflow(240, 113, 328, 140, 'blue', step=3, count=2)); elems.append(sflow(240, 165, 328, 170, 'blue', step=3, count=2))
    elems.append(sflow(500, 140, 588, 83, 'green', step=3, count=2)); elems.append(sflow(500, 160, 588, 143, 'green', step=3, count=2))
    elems.append(stext(675, 200, '3 others wait in "scheduled"', 'amber', 11, step=3))
    elems.append(stext(675, 218, 'until a slot frees up', 'amber', 11, step=3))
    elems.append(stext(400, 320, 'Pools protect a shared resource: at most 2 tasks hit the MySQL source at once, across ALL DAGs', 'amber', 12, step=4, bold=True))
    return anim(canvas(780, 335, *elems), [
        'Five extract tasks (possibly from different DAGs) are ready to run against the same MySQL replica.',
        'They are all assigned to the pool <code>mysql_pool</code>, which has only <strong>2 slots</strong>.',
        'The scheduler fills the slots in order of <strong>priority_weight</strong> (Vineeta 5, Aarshvi 3). The others stay scheduled until a slot is released.',
        'Pools limit concurrency against a <em>resource</em>; DAG-level settings such as <code>max_active_tasks</code> limit concurrency <em>within a DAG</em>.',
    ])


# ------------------------------------------------------------------ s06 executors / states
def executors_anim():
    elems = [
        _node(20, 140, 130, 60, 'Scheduler', '+ executor', 'blue', step=1),
        _node(250, 20, 220, 70, 'LocalExecutor', 'subprocesses on the\nscheduler machine', 'gray', step=2, focus='2'),
        sflow(150, 160, 248, 60, 'gray', step=2, count=2),
        _node(250, 135, 160, 70, 'Celery queue', 'Redis / RabbitMQ', 'amber', step=3, focus='3'),
        sflow(150, 170, 248, 170, 'amber', step=3, count=2),
        _node(500, 110, 120, 40, 'worker 1', '', 'green', step=3, size=12), _node(500, 160, 120, 40, 'worker 2', '', 'green', step=3, size=12),
        _node(500, 210, 120, 40, 'worker 3', '', 'green', step=3, size=12),
        sflow(410, 160, 498, 130, 'amber', step=3, count=1), sflow(410, 170, 498, 180, 'amber', step=3, count=1), sflow(410, 180, 498, 230, 'amber', step=3, count=1),
        _node(250, 270, 160, 60, 'Kubernetes API', '', 'purple', step=4, focus='4'),
        sflow(150, 185, 248, 295, 'purple', step=4, count=2),
        _node(500, 270, 80, 50, 'pod', 'task A', 'purple', step=4, size=12), _node(590, 270, 80, 50, 'pod', 'task B', 'purple', step=4, size=12),
        _node(680, 270, 80, 50, 'pod', 'task C', 'purple', step=4, size=12),
        sflow(410, 300, 498, 295, 'purple', step=4, count=2),
        stext(640, 40, 'single machine, no extra infra', '#cbd5e1', 11, step=2),
        stext(690, 180, 'always-on worker pool,', '#cbd5e1', 11, step=3), stext(690, 196, 'fast task start', '#cbd5e1', 11, step=3),
        stext(620, 345, 'one pod per task: isolation, scale to zero, slower start', '#cbd5e1', 11, step=4),
    ]
    return anim(canvas(780, 360, *elems), [
        'The executor runs inside the scheduler and decides <em>how and where</em> each queued task instance is executed.',
        '<strong>LocalExecutor</strong>: tasks run as parallel processes on the scheduler\'s machine. Fine for small teams and development.',
        '<strong>CeleryExecutor</strong>: tasks go into a message queue and a pool of always-running workers on several machines picks them up. Scales horizontally; workers must have all dependencies installed.',
        '<strong>KubernetesExecutor</strong>: every task runs in its own pod, which is created for the task and deleted afterwards. Great isolation and per-task resources; a few seconds of start-up per task. Airflow 3 can also use several executors in one deployment.',
    ])


def states_anim():
    elems = [
        _node(15, 140, 95, 44, 'none', '', 'gray', step=1, size=12),
        _node(150, 140, 110, 44, 'scheduled', '', 'blue', step=1, focus='1', size=12),
        _node(300, 140, 95, 44, 'queued', '', 'blue', step=2, focus='2', size=12),
        _node(435, 140, 105, 44, 'running', '', 'cyan', step=2, focus='2', size=12),
        _node(610, 60, 150, 40, 'success', '', 'green', step=3, size=12),
        _node(610, 120, 150, 40, 'failed', '', 'red', step=3, size=12),
        _node(610, 180, 150, 40, 'up_for_retry', '', 'amber', step=4, focus='4', size=12),
        _node(610, 240, 150, 40, 'up_for_reschedule', '', 'purple', step=4, focus='4', size=12),
        _node(610, 300, 150, 40, 'deferred', '', 'cyan', step=4, focus='4', size=12),
        _node(150, 260, 170, 40, 'skipped', '', 'gray', step=5, focus='5', size=12),
        _node(150, 310, 170, 40, 'upstream_failed', '', 'red', step=5, focus='5', size=12),
        sarrow(110, 162, 148, 162, 'gray', step=1), sarrow(260, 162, 298, 162, 'gray', step=2), sarrow(395, 162, 433, 162, 'gray', step=2),
        sarrow(540, 155, 608, 80, 'green', step=3), sarrow(540, 162, 608, 140, 'red', step=3),
        sarrow(540, 170, 608, 200, 'amber', step=4), sarrow(540, 175, 608, 258, 'purple', step=4), sarrow(540, 180, 608, 318, 'cyan', step=4),
        sarrow(685, 222, 205, 186, 'amber', step=4, dashed=True, mid=(420, 250)),
        sarrow(80, 184, 148, 280, 'gray', step=5, dashed=True), sarrow(70, 184, 148, 328, 'red', step=5, dashed=True),
        stext(420, 40, 'scheduler checks dependencies, pools, concurrency', '#94a3b8', 11, step=1),
    ]
    return anim(canvas(780, 365, *elems), [
        'Each DAG run starts with task instances in state <strong>none</strong>. When dependencies are met (trigger rule satisfied) the scheduler sets them to <strong>scheduled</strong>.',
        'When a slot is available (parallelism, pool, max_active_tasks), the task is <strong>queued</strong> to the executor, and becomes <strong>running</strong> when a worker starts it.',
        'It ends in <strong>success</strong> or <strong>failed</strong>.',
        'Intermediate states: <strong>up_for_retry</strong> (failed, will retry after retry_delay, back to scheduled), <strong>up_for_reschedule</strong> (sensor in reschedule mode) and <strong>deferred</strong> (waiting on a trigger).',
        'Some tasks never run: <strong>skipped</strong> (branching, short-circuit, AirflowSkipException) and <strong>upstream_failed</strong> (trigger rule cannot be met because of failures). Others you may meet: removed, restarting, and <strong>awaiting_input</strong> for human-in-the-loop tasks (Airflow 3.1+).',
    ])


# ------------------------------------------------------------------ s07 best practices
def idempotency_anim():
    elems = [stext(200, 24, 'Non-idempotent: INSERT INTO sales …', 'red', 13, bold=True),
             stext(590, 24, 'Idempotent: DELETE partition, then INSERT', 'green', 13, bold=True)]
    elems.append(_rows(60, 40, [('date', 'rows in table')], [120, 160], colors={0: '#ef4444'}))
    elems.append(_rows(60, 66, [('2026-10-10', '1,240')], [120, 160], step=1))
    elems.append(_rows(60, 66, [('2026-10-10', '2,480  ✘ doubled')], [120, 160], step=2, colors={0: '#4b1d1d'}))
    elems.append(_rows(60, 66, [('2026-10-10', '3,720  ✘ tripled')], [120, 160], step=3, colors={0: '#4b1d1d'}))
    elems.append(_rows(450, 40, [('date', 'rows in table')], [120, 160], colors={0: '#10b981'}))
    elems.append(_rows(450, 66, [('2026-10-10', '1,240')], [120, 160], step=1))
    elems.append(_rows(450, 66, [('2026-10-10', '1,240  ✔ same')], [120, 160], step=2, colors={0: '#123b2c'}))
    elems.append(_rows(450, 66, [('2026-10-10', '1,240  ✔ same')], [120, 160], step=3, colors={0: '#123b2c'}))
    for st, txt in [(1, 'run 1 (scheduled)'), (2, 'run 2 (retry after a later task failed)'), (3, 'run 3 (backfill / manual clear)')]:
        elems.append(stext(390, 110 + st * 26, txt, '#e2e8f0', 12, step=st, bold=(st == 1)))
    elems.append(stext(390, 240, 'Same input + same run → same result, no matter how many times it runs', 'amber', 13, step=4, bold=True, focus='4'))
    return anim(canvas(780, 260, *elems), [
        'The first run loads 1,240 rows for 10 Oct into the target. Both approaches look correct so far.',
        'A downstream task fails and the load task is retried (or someone clears it). The plain INSERT appends the same 1,240 rows again; the idempotent version first deletes the 10 Oct partition, so the count stays 1,240.',
        'Backfills and manual reruns make it worse for the plain INSERT. Airflow re-runs tasks routinely, so every task must be safe to repeat.',
        'Ways to be idempotent: overwrite a partition (DELETE + INSERT in one transaction, INSERT OVERWRITE), MERGE/upsert on a key, or write files to a path determined by the run (dt={{ ds }}) and replace them.',
    ])


def parsing_anim():
    elems = [
        _node(20, 60, 170, 80, 'DAG file', 'module-level code\n+ DAG definition', 'gray', step=1),
        _node(300, 60, 180, 80, 'DAG processor', 'imports the file\nevery ~30 s', 'purple', step=1, focus='1'),
        sflow(190, 100, 298, 100, 'purple', step=1, count=3, dur=1.0),
        _node(590, 30, 170, 50, 'serialized DAG', 'stored in DB', 'amber', step=1, size=12),
        sflow(480, 90, 588, 58, 'amber', step=1, count=2),
        _node(20, 180, 260, 60, 'requests.get(api) at top level', 'runs ~2,880 times a day', 'red', step=2, focus='2', size=12),
        _node(300, 180, 210, 60, 'Variable.get() at top level', 'API call on every parse', 'red', step=2, size=12),
        _node(530, 180, 230, 60, 'heavy imports (pandas, torch)', 'slow parse, timeouts', 'red', step=2, size=12),
        _node(80, 270, 620, 50, 'Move the work into tasks (or templates); import heavy libs inside the task function', '', 'green', step=3, focus='3', size=12),
    ]
    return anim(canvas(780, 335, *elems), [
        'The DAG processor <strong>re-imports every DAG file</strong> periodically (<code>min_file_process_interval</code>, 30 s by default) to pick up changes. Only the resulting DAG structure is stored.',
        'Anything at module level runs on every parse, not once per DAG run: API calls, DB queries, Variable.get(), reading big files. It slows parsing for <em>all</em> DAGs and can hit <code>dagbag_import_timeout</code>.',
        'Keep files declarative and fast to import. Do real work inside tasks, read variables via templates or inside tasks, and import heavy libraries inside the task function.',
    ])


# ------------------------------------------------------------------ s08 scenarios
def pipeline_anim():
    elems = [
        stext(390, 22, 'Run for logical date 10 Oct: data interval 10 Oct 00:00 → 11 Oct 00:00', '#38bdf8', 13, bold=True),
        _node(15, 50, 150, 70, 'MySQL replica', 'orders', 'blue', step=1),
        _node(215, 50, 160, 70, 'extract_delta', 'WHERE updated_at in\nthe data interval', 'purple', step=1, focus='1', size=12),
        sflow(165, 85, 213, 85, 'blue', step=1, count=2),
        _node(425, 50, 160, 70, 'lake (S3)', 'orders/dt=2026-10-10/', 'amber', step=2, focus='2', size=12),
        sflow(375, 85, 423, 85, 'purple', step=2, count=2),
        _node(625, 50, 140, 70, 'quality_check', 'row count > 0,\nno null keys', 'cyan', step=3, focus='3', size=12),
        sflow(585, 85, 623, 85, 'amber', step=3, count=2),
        _node(425, 170, 160, 70, 'load_warehouse', 'MERGE / upsert\non order_id', 'green', step=4, focus='4', size=12),
        sflow(695, 120, 585, 200, 'cyan', step=4, count=2),
        _node(215, 170, 160, 70, 'fact_orders', 'warehouse table', 'green', step=4, size=12),
        sflow(425, 205, 375, 205, 'green', step=4, count=2),
        _node(15, 170, 150, 70, 'notify', 'on success / failure', 'gray', step=5, size=12),
        stext(390, 275, 'Rerun 10 Oct any day → same files, same rows: the run only ever touches its own interval', 'amber', 12, step=5, bold=True),
    ]
    return anim(canvas(780, 290, *elems), [
        'Extract only the rows that changed in this run\'s <strong>data interval</strong>, from a read replica, using the indexed <code>updated_at</code> column.',
        'Write them to the lake under a path built from the run (<code>dt={{ ds }}</code>), replacing any earlier file for that date.',
        'Check the data before publishing: row counts, null keys, duplicates. Fail loudly instead of loading bad data.',
        'Load the warehouse idempotently: MERGE (upsert) on the order key, or delete the 10 Oct partition and insert the new rows in one transaction.',
        'Notify on failure. Because every step is scoped to the interval and idempotent, retries, backfills and manual reruns are all safe.',
    ])


def cross_dag_anim():
    elems = [
        _node(20, 40, 170, 56, 'DAG A: load_orders', 'daily 02:00', 'blue', step=1),
        _node(20, 160, 170, 56, 'DAG B: sales_report', 'needs A\'s data', 'green', step=1),
        _node(270, 20, 230, 56, 'ExternalTaskSensor in B', 'waits for A.load to succeed', 'purple', step=2, focus='2', size=12),
        stext(385, 95, 'B polls A; logical dates must line up', 'purple', 11, step=2),
        _node(270, 115, 230, 56, 'TriggerDagRunOperator in A', 'A starts B at its end', 'amber', step=3, focus='3', size=12),
        stext(385, 190, 'push model: A must know about B', 'amber', 11, step=3),
        _node(270, 215, 230, 56, 'Asset', 'A updates it, B is scheduled on it', 'cyan', step=4, focus='4', size=12),
        stext(385, 290, 'decoupled: B depends on the DATA, not on A', 'cyan', 11, step=4, bold=True),
        sarrow(190, 70, 268, 48, 'gray', step=2), sarrow(500, 48, 560, 48, 'gray', step=2),
        sarrow(190, 75, 268, 143, 'gray', step=3), sarrow(500, 143, 560, 143, 'gray', step=3),
        sarrow(190, 80, 268, 243, 'gray', step=4), sarrow(500, 243, 560, 243, 'gray', step=4),
        _node(560, 20, 200, 56, 'B runs', 'when sensor succeeds', 'green', step=2, size=12),
        _node(560, 115, 200, 56, 'B runs', 'when A triggers it', 'green', step=3, size=12),
        _node(560, 215, 200, 56, 'B runs', 'when the asset is updated', 'green', step=4, size=12),
    ]
    return anim(canvas(780, 305, *elems), [
        'DAG B must run only after DAG A has loaded the orders. Three common ways to express a cross-DAG dependency.',
        '<strong>ExternalTaskSensor</strong> (pull): B waits for a task in A for the matching logical date. Works, but B occupies (or defers) a slot while waiting and the two schedules must be aligned.',
        '<strong>TriggerDagRunOperator</strong> (push): the last task of A starts B. Simple, but A has to know every downstream DAG.',
        '<strong>Assets</strong> (data-aware): A declares the asset it produces, B is scheduled on that asset. Neither DAG names the other, which scales best to many producers and consumers.',
    ])
