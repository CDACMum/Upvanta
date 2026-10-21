from build import *
from airflow.anims import *
from airflow.runner import dagtest, afcli, afpy

DAILY_SALES = '''
import pendulum
from airflow.sdk import dag, task
from airflow.timetables.interval import CronDataIntervalTimetable

@dag(schedule=CronDataIntervalTimetable("@daily", timezone="UTC"),
     start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False)
def daily_sales():
    @task
    def load(**context):
        print("loading", context["data_interval_start"], "->", context["data_interval_end"])
    load()

daily_sales()
'''

LOAD_ORDERS = '''
import pendulum
from airflow.sdk import dag, task, Asset

orders = Asset("s3://lake/orders")

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     default_args={"owner": "anuj"})
def load_orders():
    @task(outlets=[orders])                 # success of this task = an update of the asset
    def write_orders():
        print("wrote 1,240 orders to s3://lake/orders/dt=2026-10-10/")
    write_orders()

load_orders()
'''

SALES_REPORT = '''
import pendulum
from airflow.sdk import dag, task, Asset

orders = Asset("s3://lake/orders")
customers = Asset("s3://lake/customers")

@dag(schedule=[orders, customers],          # run when BOTH assets have new events
     start_date=pendulum.datetime(2026, 10, 1, tz="UTC"), catchup=False,
     default_args={"owner": "aarshvi"})
def sales_report():
    @task
    def build_report():
        print("joining fresh orders and customers")
    build_report()

sales_report()
'''

SECTION = dict(level='intermediate', title='Scheduling', questions=[

# ------------------------------------------------------------------ 13
Q('Explain start_date, schedule, logical date and data interval. When does a daily DAG actually run?', 'Logical Date & Data Interval', minutes=10, cards=[
    definition(
        defbox('<strong>start_date</strong> is the first date the DAG may be scheduled for. <strong>schedule</strong> says how often. '
               'Each DAG run has a <strong>logical date</strong> (formerly <em>execution_date</em>) that identifies it, and a '
               '<strong>data interval</strong> (start, end) describing the period of data it should process.',
               'With an <em>interval</em> timetable, a run is created only <strong>after its interval ends</strong>, so the run with '
               'logical date 1 Oct starts at 2 Oct 00:00. Airflow 3\'s default <em>trigger</em> timetable for cron strings instead '
               'runs at the cron time and has an empty interval.'),
        tags('start_date', 'schedule', 'logical_date', 'data_interval_start', 'data_interval_end', 'CronTriggerTimetable', 'CronDataIntervalTimetable'),
    ),
    schedule_anim(),
    example(
        afpy('''
import pendulum
from airflow.timetables.base import TimeRestriction
from airflow.timetables.trigger import CronTriggerTimetable
from airflow.timetables.interval import CronDataIntervalTimetable

start = pendulum.datetime(2026, 10, 1, tz="UTC")
for tt in (CronTriggerTimetable("@daily", timezone="UTC"),        # Airflow 3 default for "@daily"
           CronDataIntervalTimetable("@daily", timezone="UTC")):  # Airflow 2 behaviour
    print(type(tt).__name__)
    last = None
    for _ in range(3):
        info = tt.next_dagrun_info(last_automated_data_interval=last,
                                   restriction=TimeRestriction(earliest=start, latest=None, catchup=True))
        di = info.data_interval
        print(f"  logical {info.logical_date:%d %b %H:%M} | interval {di.start:%d %b} -> {di.end:%d %b} | runs at {info.run_after:%d %b %H:%M}")
        last = di
'''),
        title='Example: What the Scheduler Computes (real timetable classes)'),
    example(
        afcli(['airflow backfill create --dag-id daily_sales --from-date 2026-10-01 --to-date 2026-10-03 --dry-run'],
              src=DAILY_SALES, name='daily_sales', setup_cmds=['airflow db reset -y', 'airflow dags reserialize']),
        title='Example: Runs a Backfill Would Create'),
    explanation(
        ul('For daily <em>batch</em> loads ("process yesterday\'s data"), the interval model is natural: filter source rows with '
           '<code>updated_at &gt;= data_interval_start AND updated_at &lt; data_interval_end</code>. Use '
           '<code>CronDataIntervalTimetable</code> or set <code>[scheduler] create_cron_data_intervals = True</code>.',
           'For "do something at 7 AM" jobs the trigger model is simpler: the run happens at 7 AM and its logical date is 7 AM.',
           'Never derive the processing window from <code>now()</code>. Use the run\'s data interval, so reruns and backfills process the right period.'),
        title='Which to Use'),
    crossq(
        ('A DAG has start_date = 1 Oct and schedule @daily (interval timetable). When is the first run?', 'At 2 Oct 00:00, for logical date 1 Oct (interval 1 Oct → 2 Oct). Nothing runs on 1 Oct itself.'),
        ('Why should start_date not be datetime.now()?', 'The file is parsed repeatedly, so start_date keeps moving forward and the scheduler may never see a complete interval after it. Use a fixed date.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('What schedule options does Airflow support? (cron, presets, timedelta, None, Assets, timetables)', 'Schedule Options', minutes=7, cards=[
    definition(
        defbox('The <code>schedule</code> argument accepts a cron string or preset, a <code>timedelta</code>, <code>None</code> '
               '(manual/external triggers only), an Asset expression (data-aware), or a <strong>Timetable</strong> object for custom logic.'),
        tags('cron', '@daily', 'timedelta', 'schedule=None', '@once', '@continuous', 'Timetable'),
    ),
    table(['Value', 'Meaning'], [
        ['<code>"0 7 * * 1-5"</code>', 'Cron: 07:00 Monday–Friday'],
        ['<code>"@hourly"</code>, <code>"@daily"</code>, <code>"@weekly"</code>, <code>"@monthly"</code>, <code>"@yearly"</code>', 'Cron presets'],
        ['<code>timedelta(hours=6)</code>', 'Every 6 hours from start_date (DeltaTriggerTimetable in Airflow 3)'],
        ['<code>None</code>', 'Never scheduled; run manually, via API or TriggerDagRunOperator'],
        ['<code>"@once"</code>', 'Exactly one run'],
        ['<code>"@continuous"</code>', 'Start the next run as soon as the previous finishes (max_active_runs=1)'],
        ['<code>[asset1, asset2]</code> or <code>asset1 | asset2</code>', 'When the assets are updated (AND / OR conditions)'],
        ['<code>CronDataIntervalTimetable(...)</code>, <code>MultipleCronTriggerTimetable(...)</code>, custom class', 'Explicit timetables: data intervals, several crons, business calendars'],
    ]),
    example(
        afpy('''
import pendulum
from datetime import timedelta
from airflow.timetables.base import TimeRestriction
from airflow.timetables.trigger import CronTriggerTimetable, DeltaTriggerTimetable, MultipleCronTriggerTimetable

start = pendulum.datetime(2026, 10, 9, tz="Asia/Kolkata")          # a Friday
cases = {
    "weekdays 06:30 IST": CronTriggerTimetable("30 6 * * 1-5", timezone="Asia/Kolkata"),
    "every 8 hours":      DeltaTriggerTimetable(timedelta(hours=8)),
    "09:00 and 18:00":    MultipleCronTriggerTimetable("0 9 * * *", "0 18 * * *", timezone="Asia/Kolkata"),
}
for name, tt in cases.items():
    last, runs = None, []
    for _ in range(4):
        info = tt.next_dagrun_info(last_automated_data_interval=last,
                                   restriction=TimeRestriction(earliest=start, latest=None, catchup=True))
        runs.append(info.run_after.in_timezone("Asia/Kolkata").format("ddd DD MMM HH:mm"))
        last = info.data_interval
    print(f"{name:<19}: " + " | ".join(runs))
'''),
        title='Example: Next 4 Runs for Different Schedules (IST)'),
    crossq(
        ('Cron field order?', 'minute hour day-of-month month day-of-week. <code>0 2 * * *</code> = 02:00 daily; <code>*/15 * * * *</code> = every 15 minutes; <code>0 0 1 * *</code> = midnight on the 1st of each month.'),
        ('How would you skip public holidays?', 'A custom Timetable that skips dates from a holiday calendar, or a ShortCircuit task at the start of the DAG that ends the run on holidays.'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('What are catchup and backfill? How do you re-run past dates?', 'Catchup & Backfill', minutes=8, cards=[
    definition(
        defbox('<strong>Catchup</strong>: when a DAG is unpaused, should the scheduler create runs for every missed interval since '
               'start_date (or since the last run)? <strong>Backfill</strong>: deliberately running a DAG for a past date range, for '
               'example to load history or reprocess after a bug fix.',
               'In Airflow 3, <code>catchup</code> defaults to <strong>False</strong> and backfills are executed by the '
               '<strong>scheduler</strong> (created from the UI, REST API or <code>airflow backfill create</code>).'),
        tags('catchup', 'Backfill', 'airflow backfill create', 'Clear Tasks', 'reprocess_behavior', 'max_active_runs'),
    ),
    comparison(
        table(['Situation', 'catchup=True', 'catchup=False'], [
            ['New DAG with start_date 30 days ago', '30 runs created immediately', 'Only the latest interval runs'],
            ['DAG paused for a week, then unpaused', 'Runs for the missed 7 days', 'Resumes with the latest interval'],
            ['Typical use', 'Pipelines where every interval must be loaded exactly once', 'Reports/snapshots where only "now" matters'],
        ]),
    ),
    example(
        afcli(['airflow backfill create --dag-id daily_sales --from-date 2026-09-28 --to-date 2026-09-30 '
               '--max-active-runs 2 --reprocess-behavior failed --dry-run'],
              src=DAILY_SALES, name='daily_sales', setup_cmds=['airflow db reset -y', 'airflow dags reserialize']),
        title='Example: Planning a Backfill'),
    explanation(
        ul('<code>--reprocess-behavior</code>: <em>none</em> (skip dates that already have runs), <em>failed</em> (re-run failed ones) or <em>completed</em> (re-run all).',
           '<code>--max-active-runs</code> limits how many dates run in parallel, so the source system is not flooded.',
           'To re-run only some tasks for some dates, <strong>clear</strong> them (UI or <code>airflow tasks clear dag -t "load.*" -s 2026-09-01 -e 2026-09-07</code>); the scheduler runs them again.',
           'Backfill only works correctly if tasks are <strong>idempotent</strong> and use the run\'s data interval, not "today".'),
        title='Good to Know'),
    crossq(
        ('A new DAG with start_date one year ago and catchup=True is unpaused. What happens and how do you control it?', '365 runs are created. Limit parallelism with <code>max_active_runs</code> (e.g. 3) so they run a few at a time, or set catchup=False and backfill deliberately.'),
    ),
]),

# ------------------------------------------------------------------ 16
Q('What are Assets (Datasets)? Explain data-aware scheduling', 'Assets & Data-aware Scheduling', minutes=8, cards=[
    definition(
        defbox('An <strong>Asset</strong> (called <em>Dataset</em> in Airflow 2.4–2.10) is a logical reference to data, identified by '
               'a URI such as <code>s3://lake/orders</code>. A task lists assets in <code>outlets</code>; when it succeeds, Airflow records '
               'an <strong>asset event</strong>. A DAG with <code>schedule=[asset]</code> runs when its assets have been updated.'),
        tags('Asset', 'Dataset', 'outlets', 'Asset Event', 'Data-aware Scheduling', '@asset', 'AssetWatcher'),
    ),
    assets_anim(),
    example(
        code(LOAD_ORDERS.strip('\n'), 'Producer DAG (Anuj)', 'fa-brands fa-python')
        + code(SALES_REPORT.strip('\n'), 'Consumer DAG (Aarshvi)', 'fa-brands fa-python'),
        title='Example: Producer and Consumer'),
    example(
        afcli(['airflow assets list -o plain', 'airflow assets details --name s3://lake/orders -o yaml'],
              src={'load_orders': LOAD_ORDERS, 'sales_report': SALES_REPORT},
              setup_cmds=['airflow db reset -y', 'airflow dags reserialize']),
        title='Example: Airflow Tracks Who Produces and Who Consumes Each Asset'),
    note('<code>producing_tasks</code> and <code>scheduled_dags</code> come from parsing the two files. <code>last_asset_event</code> '
         'is still empty: events are recorded when the producer task succeeds in a real scheduled or triggered run.', 'Reading the output'),
    explanation(
        ul('Conditions: <code>schedule=(orders &amp; customers) | manual_override</code> combines assets with AND/OR.',
           'Airflow only knows an asset was updated because a task <em>said so</em>; it does not watch S3 itself. External systems can '
           'post events through the REST API, and Airflow 3 <strong>AssetWatchers</strong> can listen to a message queue.',
           'The <code>@asset</code> decorator (Airflow 3) defines a one-task DAG that materialises an asset, like dbt models.'),
        title='Details'),
    crossq(
        ('Assets vs ExternalTaskSensor?', 'A sensor occupies (or defers) a slot while polling and couples you to the other DAG\'s schedule and task ids. Assets are event-driven: the consumer is triggered when data is ready, whenever that is.'),
    ),
]),

# ------------------------------------------------------------------ 17
Q('How does Airflow handle time zones?', 'Time Zones', minutes=6, cards=[
    definition(
        defbox('Airflow stores and compares all datetimes in <strong>UTC</strong> internally. A DAG becomes time-zone aware when its '
               '<code>start_date</code> (or timetable) carries a time zone, e.g. <code>pendulum.datetime(2026, 10, 1, tz="Asia/Kolkata")</code>. '
               'Cron schedules are then evaluated in that zone, and the UI can display any zone.'),
        tags('UTC', 'pendulum', 'Asia/Kolkata', 'default_timezone', 'DST'),
    ),
    example(
        afpy('''
import pendulum
from airflow.timetables.base import TimeRestriction
from airflow.timetables.trigger import CronTriggerTimetable

start = pendulum.datetime(2026, 10, 23, tz="UTC")
for zone in ("Asia/Kolkata", "Europe/London"):          # UK summer time ends on 25 Oct 2026
    tt, last = CronTriggerTimetable("0 9 * * *", timezone=zone), None
    print(f"09:00 every day in {zone}")
    for _ in range(3):
        info = tt.next_dagrun_info(last_automated_data_interval=last,
                                   restriction=TimeRestriction(earliest=start, latest=None, catchup=True))
        print(f"   {info.run_after.in_timezone(zone):%d %b %H:%M %Z}  =  {info.run_after:%H:%M} UTC")
        last = info.data_interval
'''),
        title='Example: The Same Cron in Two Zones'),
    explanation(
        ul('India has no daylight saving, so IST schedules are always UTC + 5:30.',
           'In DST zones, a cron in local time keeps the local clock time (09:00) and its UTC time shifts; a timedelta schedule keeps a fixed gap instead.',
           '<code>{{ ds }}</code> and <code>logical_date</code> are in UTC. Convert explicitly (<code>logical_date.in_timezone("Asia/Kolkata")</code>) when a local date matters, e.g. for partition names.'),
        title='Points to Remember'),
    warn('A naive <code>datetime(2026, 10, 1)</code> start_date is interpreted in <code>[core] default_timezone</code> (UTC by default). '
         'For an Indian team that means a "midnight" DAG actually runs at 05:30 IST.', 'Common Mistake'),
]),

# ------------------------------------------------------------------ 18
Q('My DAG is not running. What do you check?', 'Why Didn\'t My DAG Run?', minutes=7, cards=[
    definition(
        defbox('Most "the DAG never ran" problems are scheduling misunderstandings or parse errors, not bugs in Airflow. Check in '
               'this order: is it <strong>loaded</strong>, is it <strong>unpaused</strong>, is a run <strong>due</strong>, and are its tasks '
               '<strong>able to start</strong>?'),
        tags('Troubleshooting', 'Paused', 'Import Errors', 'start_date', 'max_active_runs', 'Pools'),
    ),
    table(['Symptom', 'Likely cause', 'Check / fix'], [
        ['DAG not in the UI', 'Import error, wrong folder, file ignored (.airflowignore), parse timeout', '<code>airflow dags list-import-errors</code>, banner in the UI'],
        ['DAG visible but no runs', 'DAG is paused (new DAGs start paused by default)', 'Unpause in UI or <code>airflow dags unpause</code>'],
        ['First run "missing"', 'Interval timetable: first run starts after start_date + one interval', 'Look at the "Next run" shown in the UI'],
        ['Old dates never run', 'catchup=False (default in Airflow 3)', 'Backfill the dates'],
        ['Runs created, tasks stay "scheduled"/"queued"', 'No free slot: pool, max_active_tasks, parallelism, workers down', 'Pools page, executor/worker logs'],
        ['Only one run at a time', 'max_active_runs=1 or depends_on_past=True', 'Check DAG/task arguments'],
        ['start_date in the future / dynamic', 'start_date = now() or later than expected', 'Use a fixed past date'],
    ]),
    example(
        afcli(['airflow dags list-import-errors'],
              src={'broken_dag': '''
import pendulum
from airflow.sdk import dag, task

@dag(schedule="@daily", start_date=pendulum.datetime(2026, 10, 1, tz="UTC"))
def broken_dag():
    @task
    def hello():
        print("hi Vineeta")
    hello(
broken_dag()
'''}, setup_cmds=['airflow db reset -y', 'airflow dags reserialize || true']),
        title='Example: A Missing Bracket Hides the DAG'),
    crossq(
        ('Where are parse errors logged?', 'In the DAG processor logs, and as import errors in the UI and <code>airflow dags list-import-errors</code>. A quick local check is <code>python my_dag.py</code>.'),
    ),
]),

])
