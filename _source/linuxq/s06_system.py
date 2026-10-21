from build import *
from linuxq.anims import *
from linuxq.runner import shrun, sh, script_file
from linuxq.data import COMMON

GRACEFUL = r"""
#!/usr/bin/env bash
trap 'echo "[$$] got TERM: saving checkpoint and exiting"; exit 0' TERM
echo "[$$] job started"
while true; do sleep 1; done
"""

SECTION = dict(level='advanced', title='Processes & System Administration', questions=[

# ------------------------------------------------------------------ 26
Q('What is a process? How do you list, find and kill processes? Explain signals.', 'Processes & Signals', minutes=8, cards=[
    definition(
        defbox('A <strong>process</strong> is a running program with a <strong>PID</strong>, a parent (<strong>PPID</strong>), an owner, a state and resources. '
               '<code>ps aux</code> / <code>ps -ef</code> list processes; <code>ps -o pid,ppid,stat,cmd</code> chooses columns; <code>top</code>/<code>htop</code> '
               'show live usage; <code>pgrep -f pattern</code> finds PIDs by command line.',
               '<strong>Signals</strong> notify processes: <code>SIGTERM (15)</code> polite stop (default of <code>kill</code>), <code>SIGKILL (9)</code> immediate, '
               'cannot be caught, <code>SIGINT (2)</code> Ctrl+C, <code>SIGHUP (1)</code> hang-up/reload, <code>SIGSTOP/SIGCONT</code> pause/resume. '
               '<code>kill PID</code>, <code>kill -9 PID</code>, <code>pkill -f pattern</code>, <code>killall name</code>.'),
        tags('process', 'PID', 'ps', 'top', 'kill', 'signals'),
    ),
    analogy('Processes are <strong>employees on a shift</strong>, each with an ID badge and a manager (parent). SIGTERM is "<strong>please finish up and go '
            'home</strong>": they save their work first. SIGKILL is <strong>security escorting them out instantly</strong>: unsaved work is lost.'),
    process_anim(),
    real_world(
        scenario('A stuck Spark driver',
                 p('A Spark job hangs and blocks the next run. <code>pgrep -af spark-submit</code> finds it; <code>kill PID</code> lets it release resources and write '
                   'logs; only if it ignores TERM for a minute, <code>kill -9</code>. Killing with -9 first can leave lock files and half-written output behind.')),
    ),
    example(
        script_file('job.sh', GRACEFUL),
        shrun("""
            bash job.sh > job.out 2>&1 &
            sleep 1
            pgrep -f 'bash job.sh'
            ps -o pid,ppid,stat,etime,cmd -p "$(pgrep -f 'bash job.sh')"
            kill -TERM "$(pgrep -f 'bash job.sh')"; sleep 1.5
            cat job.out
            sleep 300 & pid=$!; sleep 0.2
            kill -STOP $pid; ps -o pid,stat,cmd -p $pid
            kill -CONT $pid; ps -o pid,stat,cmd -p $pid
            kill -9 $pid; wait $pid 2>/dev/null; echo "exit status after SIGKILL: $?"
            kill -l | head -n 2
        """, files={'job.sh': GRACEFUL}),
        title='Example: Find a Job, Stop It Gracefully, Pause/Resume, Force Kill'),
    steps(
        ('Find', '<code>pgrep -af name</code> or <code>ps aux | grep [n]ame</code>.'),
        ('Inspect', '<code>ps -o pid,ppid,stat,%cpu,%mem,etime,cmd -p PID</code>.'),
        ('Ask to stop', '<code>kill PID</code> (TERM); wait.'),
        ('Force if necessary', '<code>kill -9 PID</code>.'),
        ('Clean up', 'Check for leftover lock/temp files and child processes.'),
        title='Steps to Stop a Process Safely'),
    crossq(
        ('What is a zombie process?', 'A child that has exited but whose parent has not read its exit status (wait); it uses no resources except a process-table entry. Fix the parent or it disappears when the parent exits.'),
        ('What is an orphan?', 'A process whose parent died; it is adopted by PID 1 (or a subreaper), which reaps it later.'),
        ('Why 137 after kill -9?', 'Shells report death by signal as 128 + signal number: 128 + 9 = 137 (143 for TERM).'),
    ),
]),

# ------------------------------------------------------------------ 27
Q('How do you run commands in the background? Explain &, jobs, fg/bg, nohup and disown.', 'Background Jobs & nohup', minutes=7, cards=[
    definition(
        defbox('<code>cmd &amp;</code> starts a job in the background (<code>$!</code> holds its PID). In an interactive shell, <code>jobs</code> lists jobs, '
               '<code>fg %1</code> brings one to the foreground, <strong>Ctrl+Z</strong> suspends the foreground job, <code>bg %1</code> resumes it in the background, '
               '<code>wait</code> waits for background jobs.',
               'When a terminal closes, its jobs get <strong>SIGHUP</strong> and usually die. <code>nohup cmd &gt; log 2&gt;&amp;1 &amp;</code> ignores HUP; '
               '<code>disown</code> removes a job from the shell\'s job table; <code>tmux</code>/<code>screen</code> keep whole sessions alive; long-running services '
               'belong in systemd.'),
        tags('background', 'jobs', 'fg', 'bg', 'nohup', 'tmux'),
    ),
    analogy('A background job is <strong>putting the rice on the stove and continuing to chop vegetables</strong>. nohup is <strong>telling the cook not to '
            'switch off the stove when you leave the kitchen</strong>.'),
    jobs_anim(),
    real_world(
        scenario('Training a model over SSH',
                 p('A 3-hour model training run started over SSH died when the Wi-Fi dropped. Running it as <code>nohup python train.py &gt; train.log 2&gt;&amp;1 &amp;</code> '
                   '(or inside tmux) keeps it alive; <code>tail -f train.log</code> checks progress after reconnecting.')),
    ),
    example(
        shrun("""
            !set -m
            sleep 30 &
            sleep 40 &
            jobs
            echo "last background PID: $!"
            kill %1; sleep 0.2; jobs
            nohup bash -c 'echo started; sleep 1; echo finished' > long.log 2>&1 &
            wait
            cat long.log
            kill %2 2>/dev/null; wait 2>/dev/null; jobs; echo 'no jobs left'
        """),
        sh("""
            python train.py            # running in the foreground...
            ^Z                         # Ctrl+Z: [1]+  Stopped   python train.py
            bg %1                      # continue it in the background
            disown -h %1               # do not send it HUP when this shell exits
            tmux new -s train          # or work inside tmux; detach with Ctrl+B d, reattach: tmux attach -t train
        """, title='Shell (interactive job control)'),
        title='Example: Background Jobs, jobs/kill %n, nohup'),
    steps(
        ('Short background task', '<code>cmd &amp;</code>, then <code>wait</code> in scripts.'),
        ('Must survive logout', '<code>nohup cmd &gt; file.log 2&gt;&amp;1 &amp;</code>.'),
        ('Interactive work over SSH', 'tmux/screen.'),
        ('Production services', 'A systemd unit with Restart=on-failure.'),
        ('Monitor', '<code>tail -f</code> the log; <code>pgrep -af</code> the process.'),
        title='Steps to Run Long Jobs'),
    crossq(
        ('Where does nohup write output if you do not redirect?', 'To nohup.out in the current directory (or $HOME).'),
        ('Why does "jobs" show nothing in a new terminal?', 'Jobs belong to the shell that started them; another shell has its own job table (use ps/pgrep instead).'),
        ('How do you run several commands in parallel and wait for all?', 'Start each with &, then wait; or xargs -P / GNU parallel.'),
    ),
]),

# ------------------------------------------------------------------ 28
Q('How do you check disk space and memory? What do df, du, free and lsof show?', 'Disk & Memory', minutes=7, cards=[
    definition(
        defbox('<code>df -h</code> free/used space per mounted filesystem (<code>-i</code> inodes); <code>du -sh path</code> space used by files/directories '
               '(<code>--max-depth=1</code>, sort with <code>sort -rh</code>); <code>free -h</code> memory and swap, where <strong>available</strong> is what new '
               'programs can use (cache is reclaimable); <code>lsof</code> lists open files (<code>lsof +L1</code> deleted-but-open files, <code>lsof -i :8080</code> '
               'who uses a port); <code>vmstat</code>, <code>iostat</code>, <code>top</code> for activity over time.'),
        tags('df', 'du', 'free', 'lsof', 'disk space', 'memory'),
    ),
    analogy('<code>df</code> tells you <strong>how full each cupboard is</strong>; <code>du</code> <strong>weighs each shelf</strong> to find what fills it; '
            '<code>free</code> checks the <strong>desk space</strong>; <code>lsof</code> finds who is still <strong>holding a file you thought you threw away</strong>.'),
    disk_anim(),
    real_world(
        scenario('"No space left on device" on a Kafka broker',
                 p('<code>df -h</code> shows /data at 100 %; <code>du -sh /data/* | sort -rh</code> shows the log segments; an old application log was deleted but '
                   '<code>lsof +L1</code> shows the process still holding it open, so restarting that process actually freed the space.')),
    ),
    example(
        shrun("""
            !mkdir -p data/raw data/clean logs; head -c 4000000 /dev/urandom > data/raw/big.bin; head -c 900000 /dev/urandom > data/clean/c.bin; head -c 50000 /dev/urandom > logs/a.log
            df -h /home | tail -n 1
            df -i /home | tail -n 1
            du -sh data logs
            du -ah . | sort -rh | head -n 4
            free -h
            sleep 300 < data/raw/big.bin &
            rm data/raw/big.bin; du -sh data
            lsof +L1 2>/dev/null | awk 'NR == 1 || /big.bin/'
            kill $!
        """),
        title='Example: Free Space, Biggest Folders, Memory and a Deleted-but-Open File'),
    steps(
        ('Which filesystem is full?', '<code>df -h</code> (and <code>df -i</code>).'),
        ('What is using it?', '<code>du -h --max-depth=1 /path | sort -rh</code>, drilling down.'),
        ('Space not freed after deleting?', '<code>lsof +L1</code>; restart or truncate via the process.'),
        ('Memory pressure?', '<code>free -h</code>, <code>top</code> sorted by %MEM, check swap usage.'),
        ('Prevent', 'Log rotation, retention jobs, monitoring alerts at 80 %.'),
        title='Steps to Investigate Space and Memory'),
    crossq(
        ('Why can df and du disagree?', 'Deleted files still open (counted by df, invisible to du), files hidden under mount points, reserved blocks for root, and filesystem metadata.'),
        ('Is high "buff/cache" a problem?', 'No: Linux uses free RAM as disk cache and gives it back on demand; watch "available" and swap activity instead.'),
        ('How do you empty a huge open log without restarting?', 'Truncate it: : > app.log (or truncate -s 0), so the process keeps writing to the same, now empty, file.'),
    ),
]),

# ------------------------------------------------------------------ 29
Q('How do you schedule jobs with cron? Explain the crontab format.', 'cron & crontab', minutes=8, cards=[
    definition(
        defbox('<strong>cron</strong> is a daemon that runs commands on a schedule. Each user has a <strong>crontab</strong> (<code>crontab -e</code> edit, '
               '<code>crontab -l</code> list, <code>crontab -r</code> remove); system jobs live in <code>/etc/crontab</code> and <code>/etc/cron.d/</code>.',
               'Format: <code>minute hour day-of-month month day-of-week command</code> with <code>*</code> any, <code>,</code> lists, <code>-</code> ranges, '
               '<code>*/n</code> steps; shortcuts <code>@daily</code>, <code>@reboot</code>. Cron uses a minimal environment (short PATH, no .bashrc), the '
               'crontab owner\'s home as working directory, and mails or discards output, so redirect it to a log.'),
        table(['Line', 'Meaning'], [
            ['0 2 * * *', 'every day at 02:00'],
            ['*/15 * * * *', 'every 15 minutes'],
            ['30 18 * * 1-5', '18:30 Monday to Friday'],
            ['0 9 1 * *', '09:00 on the 1st of every month'],
            ['@reboot', 'once at boot'],
        ]),
        tags('cron', 'crontab', 'scheduling', '@daily'),
    ),
    analogy('cron is an <strong>office alarm clock with a timetable</strong>: at each listed time it wakes up and does the task, whether or not anyone is at '
            'their desk. It does not know your personal preferences (.bashrc), so every instruction must be complete.'),
    cron_anim(),
    real_world(
        scenario('Nightly result pipeline',
                 p('<code>15 1 * * * /opt/etl/pull_marks.sh &gt;&gt; /var/log/etl/pull.log 2&gt;&amp;1</code> pulls marks from the exam server; at 02:00 another entry '
                   'loads them into Hive; a weekly entry deletes logs older than 30 days. When dependencies and retries grow, the team moves the chain to Airflow.')),
    ),
    example(
        shrun("""
            cat > my.cron <<'EOF'
            # m  h  dom mon dow  command
            15  1  *   *   *    /home/student/cdac/pull_marks.sh >> /home/student/cdac/logs/pull.log 2>&1
            */15 8-18 * *  1-5  /home/student/cdac/check_lms.sh
            0   3  *   *   0    find /home/student/cdac/logs -name '*.log' -mtime +30 -delete
            EOF
            crontab my.cron
            crontab -l
            crontab -r; crontab -l
        """),
        title='Example: Installing, Listing and Removing a crontab'),
    steps(
        ('Write the script', 'Absolute paths, set PATH and needed variables inside it, strict mode (cron\'s default PATH is only /usr/bin:/bin).'),
        ('Test it manually', 'Run it from a different directory, ideally with <code>env -i</code> to mimic cron.'),
        ('Add the schedule', '<code>crontab -e</code>; verify the line on crontab.guru.'),
        ('Log output', '<code>&gt;&gt; file.log 2&gt;&amp;1</code>.'),
        ('Prevent overlaps', '<code>flock -n /tmp/job.lock script.sh</code> so a slow run does not overlap the next one.'),
        title='Steps to Schedule a Job Reliably'),
    crossq(
        ('Why does a script work manually but not in cron?', 'Different environment: PATH, missing variables (JAVA_HOME), relative paths, no TTY, different working directory or user.'),
        ('What if the server is off at the scheduled time?', 'Plain cron skips the run; anacron or systemd timers with Persistent=true run missed jobs later.'),
        ('How is % special in crontab?', 'Unescaped % becomes a newline in the command; write \\% (e.g. date +\\%F).'),
    ),
]),

# ------------------------------------------------------------------ 30
Q('How do you manage services and read logs? Explain systemctl, journalctl and /var/log.', 'Services & Logs', minutes=8, cards=[
    definition(
        defbox('<strong>systemd</strong> is the init system (PID 1) on most distributions. Services are described by <strong>unit files</strong> '
               '(<code>/etc/systemd/system/name.service</code>). <code>systemctl start|stop|restart|reload|status name</code> controls them; '
               '<code>enable</code>/<code>disable</code> sets start at boot; <code>systemctl daemon-reload</code> after editing units; '
               '<code>systemctl list-units --failed</code> shows failures.',
               '<strong>journalctl</strong> reads the systemd journal: <code>-u name</code> one unit, <code>-f</code> follow, <code>--since "1 hour ago"</code>, '
               '<code>-p err</code> priority, <code>-b</code> this boot. Traditional text logs live in <code>/var/log</code> (syslog, auth.log, application folders) '
               'and are rotated by <strong>logrotate</strong>.'),
        tags('systemd', 'systemctl', 'journalctl', 'unit file', '/var/log', 'logrotate'),
    ),
    analogy('systemd is a <strong>building manager</strong> with a card for every service: how to start it, as which user, and what to do if it stops '
            '(restart it). journalctl is the <strong>manager\'s logbook</strong>, searchable by service and time.'),
    systemd_anim(),
    real_world(
        scenario('Keeping Kafka and the LMS API running',
                 p('Kafka, ZooKeeper/KRaft and the LMS API run as systemd services with <code>Restart=on-failure</code>; after a reboot they start automatically. '
                   'When the API fails, <code>systemctl status lms-api</code> shows the exit code and <code>journalctl -u lms-api --since today -p err</code> the cause.')),
    ),
    example(
        sh("""
            sudo tee /etc/systemd/system/lms-api.service > /dev/null <<'EOF'
            [Unit]
            Description=LMS REST API
            After=network.target mysql.service

            [Service]
            User=lms
            WorkingDirectory=/opt/lms
            Environment=APP_ENV=prod
            ExecStart=/opt/lms/venv/bin/uvicorn app:api --port 8000
            Restart=on-failure
            RestartSec=5

            [Install]
            WantedBy=multi-user.target
            EOF

            sudo systemctl daemon-reload
            sudo systemctl enable --now lms-api
            systemctl status lms-api
            journalctl -u lms-api -f --since "10 min ago"
            systemctl list-units --type=service --state=failed
        """, title='Shell (systemd: shown, not run; this build server has no systemd as PID 1)'),
        shrun("""
            systemctl is-system-running
            ls /var/log | head -n 8
            tail -n 3 /var/log/dpkg.log | cut -c1-70
            ls /etc/logrotate.d | head -n 5
        """),
        title='Example: A Unit File and Service Commands; /var/log on the Build Server'),
    steps(
        ('Write a unit file', 'User, WorkingDirectory, ExecStart, Restart.'),
        ('Load and start', '<code>systemctl daemon-reload</code>, <code>systemctl enable --now name</code>.'),
        ('Check', '<code>systemctl status name</code>.'),
        ('Read logs', '<code>journalctl -u name -f</code>.'),
        ('Rotate application logs', 'A logrotate config in /etc/logrotate.d/.'),
        title='Steps to Run Something as a Service'),
    crossq(
        ('restart vs reload?', 'restart stops and starts the process; reload asks it to re-read configuration without stopping (only if the service supports it, often via SIGHUP).'),
        ('Why does systemctl fail inside Docker containers?', 'Containers usually run a single application as PID 1, not systemd, so there is no service manager to talk to.'),
        ('Where do you look first when a service will not start?', 'systemctl status (exit code, last lines), then journalctl -u name -b, then the application\'s own log files and permissions on its directories.'),
    ),
]),
])
