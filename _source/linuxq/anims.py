from build import *


def _lines(x, y, lines, color='#e2e8f0', size=11, step=None, gap=16):
    return ''.join(stext(x, y + i * gap, ln, color, size, 'start', step=step).replace('<text ', '<text xml:space="preserve" ', 1)
                   for i, ln in enumerate(lines))


def _codebox(x, y, w, h, lines, color='gray', step=None, tcolor='#e2e8f0', size=11, focus=None):
    return sbox(x, y, w, h, '', '', color, step=step, fill_opacity=0.08, focus=focus) + _lines(x + 14, y + 22, lines, tcolor, size, step=step)


def _row(items, y, x0=20, w=130, gap=14, h=56, size=12, arrows=True):
    out = []
    for i, (t, s, c, st) in enumerate(items):
        x = x0 + i * (w + gap)
        out.append(sbox(x, y, w, h, t, s, c, step=st, size=size))
        if arrows and i:
            out.append(sarrow(x - gap, y + h / 2, x - 2, y + h / 2, 'gray', step=st))
    return ''.join(out)


# ============================================================ section 1
def layers_anim():
    elems = [
        stext(380, 24, 'Layers of a Linux system', 'blue', 15, bold=True),
        sbox(20, 230, 720, 34, 'Hardware: CPU · RAM · disks · network', '', 'gray', step=1, size=12),
        sbox(60, 180, 640, 40, 'Kernel: processes · memory · files · devices · network', 'Linux = the kernel (Linus Torvalds, 1991)', 'blue', step=2, size=12),
        sbox(100, 130, 560, 40, 'Shell (bash, zsh) + system tools (GNU coreutils)', 'you type commands → system calls', 'green', step=3, size=12),
        sbox(140, 80, 480, 40, 'Applications: Hadoop · Spark · Kafka · MySQL · Python', '', 'purple', step=4, size=12),
        stext(380, 60, 'distribution = kernel + tools + package manager: Ubuntu, RHEL, Rocky, Debian, Amazon Linux', 'amber', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'At the bottom is the hardware.',
        'The <strong>kernel</strong> manages it: scheduling processes, memory, file systems, devices and networking. Strictly, "Linux" is this kernel.',
        'The <strong>shell</strong> and command-line tools let users talk to the kernel; each command becomes system calls.',
        'Applications, including the whole big-data stack, run on top. Almost all servers and clusters run Linux.',
        'A <strong>distribution</strong> packages the kernel with tools, a package manager and defaults.',
    ])


def fhs_anim():
    dirs = [('/home', 'users\' files', 'green'), ('/etc', 'configuration', 'amber'), ('/var/log', 'log files', 'red'), ('/tmp', 'temporary, world-writable', 'gray'),
            ('/usr/bin', 'programs', 'blue'), ('/opt', 'add-on software (hadoop, spark)', 'purple'), ('/root', 'root\'s home', 'pink'), ('/dev /proc', 'devices · kernel info', 'cyan')]
    elems = [stext(380, 24, 'The filesystem hierarchy: one tree from /', 'blue', 15, bold=True),
             sbox(330, 45, 100, 34, '/', 'root', 'blue', step=1, size=13),
             stext(380, 98, 'everything below lives inside /', 'gray', 11, step=2)]
    for i, (d, s, c) in enumerate(dirs):
        x = 20 + (i % 4) * 182; y = 110 + (i // 4) * 70
        elems.append(sbox(x, y, 170, 52, d, s, c, step=2 if i < 4 else 3, size=12))
    elems += [
        stext(380, 268, 'absolute path: /home/student/cdac/marks.csv · relative: cdac/marks.csv (from ~) · ~ = home · . current · .. parent', 'amber', 12, step=4),
        stext(380, 292, 'no drive letters: other disks and HDFS-fuse mounts appear as directories (mount points)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 305, *elems), [
        'Everything hangs off a single root directory, <code>/</code>.',
        'Users work in <code>/home</code>; configuration lives in <code>/etc</code>; logs in <code>/var/log</code>; <code>/tmp</code> is shared scratch space.',
        'Programs are in <code>/usr/bin</code>; big-data software is often unpacked into <code>/opt</code>; <code>/proc</code> and <code>/dev</code> expose the kernel and devices as files.',
        'Absolute paths start with /; relative paths start from the current directory. <code>~</code>, <code>.</code> and <code>..</code> are shortcuts.',
        'Extra disks are mounted into the tree, so there are no drive letters.',
    ])


def fileops_anim():
    elems = [
        stext(380, 24, 'Everyday file and directory commands', 'blue', 15, bold=True),
        _codebox(20, 50, 350, 200, ['$ mkdir -p cdac/{data,scripts,logs}', '$ cd cdac', '$ touch data/marks.csv', '$ cp data/marks.csv data/marks.bak',
                                    '$ mv data/marks.bak backup.csv', '$ cp -r data data_copy', '$ rm backup.csv', '$ rm -r data_copy', '$ ls -la'], 'gray', step=1),
        sbox(400, 50, 340, 40, 'mkdir -p', 'creates parents, no error if exists', 'green', step=2, size=12),
        sbox(400, 98, 340, 40, 'cp -r / mv', 'copy recursively · move = rename', 'blue', step=3, size=12),
        sbox(400, 146, 340, 40, 'rm -r', 'NO recycle bin: deleted is gone', 'red', step=4, size=12, focus=4),
        sbox(400, 194, 340, 40, 'ls -la', 'long listing incl. hidden (.files)', 'purple', step=5, size=12),
        stext(380, 272, 'rm -i asks before deleting · never run rm -rf with an unchecked variable: rm -rf "$DIR"/ with DIR empty = rm -rf /', 'amber', 11, step=4),
    ]
    return anim(canvas(760, 290, *elems), [
        'A typical session: create a project folder structure, copy, move, delete and list.',
        '<code>mkdir -p</code> creates nested directories in one go; brace expansion makes several at once.',
        '<code>cp -r</code> copies directories; <code>mv</code> both moves and renames.',
        '<code>rm</code> deletes permanently; there is no recycle bin on the command line.',
        '<code>ls -la</code> shows permissions, owner, size, date and hidden files (names starting with a dot).',
    ])


def viewing_anim():
    elems = [
        stext(380, 24, 'Looking inside files', 'blue', 15, bold=True),
        sbox(20, 55, 170, 50, 'cat file', 'whole file at once', 'gray', step=1, size=13),
        sbox(205, 55, 170, 50, 'less file', 'scroll, / to search, q', 'blue', step=2, size=13),
        sbox(390, 55, 170, 50, 'head -n 5', 'first lines', 'green', step=3, size=13),
        sbox(575, 55, 165, 50, 'tail -n 5', 'last lines', 'green', step=3, size=13),
        sbox(20, 125, 350, 60, 'tail -f app.log', 'follow: new lines appear as they are written (Ctrl+C to stop)', 'amber', step=4, size=12, focus=4),
        sbox(390, 125, 350, 60, 'wc -l file', 'count lines (and -w words, -c bytes)', 'purple', step=5, size=12),
        stext(380, 220, 'never cat a 20 GB log: use less, head/tail, grep, or tail -n 1000', 'red', 12, step=2),
        stext(380, 245, 'file x → what kind of file it is · stat x → size, owner, timestamps', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 262, *elems), [
        '<code>cat</code> prints the entire file: fine for small files.',
        '<code>less</code> pages through large files without loading everything; search with /.',
        '<code>head</code> and <code>tail</code> show the beginning or end, e.g. a CSV header or the latest log lines.',
        '<code>tail -f</code> keeps following a growing log, the standard way to watch a running Spark or Hadoop job.',
        '<code>wc</code> counts lines, words and bytes; <code>file</code> and <code>stat</code> describe the file.',
    ])


def help_anim():
    elems = [
        stext(380, 24, 'Getting help and working faster in the shell', 'blue', 15, bold=True),
        sbox(20, 55, 230, 50, 'man ls', 'full manual (q to quit)', 'blue', step=1, size=13),
        sbox(265, 55, 230, 50, 'ls --help', 'quick option list', 'green', step=1, size=13),
        sbox(510, 55, 230, 50, 'type / which', 'what will run: alias, builtin, file', 'purple', step=2, size=12),
        sbox(20, 125, 230, 50, 'Tab', 'completes names', 'amber', step=3, size=13),
        sbox(265, 125, 230, 50, 'history · !! · Ctrl+R', 'reuse earlier commands', 'amber', step=3, size=13),
        sbox(510, 125, 230, 50, "alias ll='ls -la'", 'shortcuts (in ~/.bashrc)', 'cyan', step=4, size=12),
        stext(380, 210, 'apropos "disk usage" → find the right command when you do not know its name', 'gray', 12, step=5),
        stext(380, 235, 'Ctrl+C stop · Ctrl+D end input/logout · Ctrl+L clear · Ctrl+A / Ctrl+E start/end of line', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        '<code>man</code> pages are the reference; <code>--help</code> gives a short summary.',
        '<code>type</code> and <code>which</code> show what a command really is (alias, shell builtin or program on PATH).',
        'Tab completion and history search save typing and avoid typos.',
        'Aliases create shortcuts; put them in <code>~/.bashrc</code> so they persist.',
        'A few key combinations make the terminal much faster to use.',
    ])


# ============================================================ section 2
def perm_anim():
    elems = [
        stext(380, 24, 'Reading permissions: -rwxr-x---', 'blue', 15, bold=True),
        scell(60, 60, 40, 34, '-', '#334155', step=1),
    ]
    for i, (ch, col) in enumerate(zip('rwxr-x---', ['#0ea5e9'] * 3 + ['#10b981'] * 3 + ['#8b5cf6'] * 3)):
        elems.append(scell(100 + i * 40, 60, 40, 34, ch, col, '#fff', step=2, bold=True))
    elems += [
        stext(80, 115, 'type', 'gray', 11, step=1), stext(160, 115, 'owner (u)', 'blue', 12, step=2), stext(280, 115, 'group (g)', 'green', 12, step=2),
        stext(400, 115, 'others (o)', 'purple', 12, step=2),
        stext(160, 140, '4+2+1 = 7', 'blue', 13, step=3, bold=True), stext(280, 140, '4+0+1 = 5', 'green', 13, step=3, bold=True), stext(400, 140, '0', 'purple', 13, step=3, bold=True),
        stext(280, 168, 'chmod 750 run.sh  =  chmod u=rwx,g=rx,o= run.sh', 'amber', 13, step=3, bold=True),
        _codebox(490, 50, 250, 110, ['file      dir', 'r read     list names', 'w modify   create/delete inside', 'x execute  enter (cd)'], 'cyan', step=4, tcolor='#a5f3fc'),
        stext(380, 205, 'chmod +x script.sh · chmod g+w shared/ · chmod -R o-rwx private/', 'gray', 12, step=5),
        stext(380, 230, 'root bypasses permission checks (except execute needs at least one x bit)', 'red', 12, step=5),
    ]
    return anim(canvas(760, 250, *elems), [
        'The first character is the type: - file, d directory, l symbolic link.',
        'Then three triplets: owner, group, others, each with read, write, execute.',
        'Each triplet is an octal digit: r=4, w=2, x=1. rwxr-x--- is 750.',
        'For directories the bits mean: r = list names, w = create/delete entries, x = enter and access files.',
        '<code>chmod</code> sets them numerically or symbolically; root is not restricted by these checks.',
    ])


def owner_anim():
    elems = [
        stext(380, 24, 'Users, groups and ownership', 'blue', 15, bold=True),
        sbox(20, 55, 220, 70, 'user: student', 'numeric uid · home /home/student\nprimary group: student', 'blue', step=1, size=12),
        sbox(270, 55, 220, 70, 'groups', 'student, dbda (supplementary)', 'green', step=2, size=12),
        sbox(520, 55, 220, 70, 'file owner + group', 'every file has one of each', 'purple', step=3, size=12),
        _codebox(20, 145, 720, 70, ['# useradd -m -s /bin/bash anuj ; groupadd dbda ; usermod -aG dbda anuj     (root)',
                                     '# chown anuj:dbda report.csv ; chgrp dbda shared/ ; chmod g+w shared/          (root / owner)'], 'amber', step=4, tcolor='#fde68a'),
        stext(380, 240, '/etc/passwd: users · /etc/group: groups · /etc/shadow: password hashes (root only)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 258, *elems), [
        'Every account has a username, a numeric uid, a home directory and a primary group.',
        'Users can belong to extra groups, which is how a team shares files.',
        'Each file is owned by one user and one group; permissions apply to owner, that group, and everyone else.',
        'Administrators create users and groups and change ownership; <code>usermod -aG</code> appends a group (without -a it replaces them).',
        'Account data lives in plain text files under /etc; password hashes are in /etc/shadow, readable only by root.',
    ])


def umask_anim():
    elems = [
        stext(380, 24, 'umask: permissions taken away from new files', 'blue', 15, bold=True),
        stable(30, 60, ['', 'file', 'directory'], [['base', '666 rw-rw-rw-', '777 rwxrwxrwx'], ['umask 022', '− ----w--w-', '− ----w--w-'],
                                                   ['result', '644 rw-r--r--', '755 rwxr-xr-x']], [90, 150, 150], step=1, row_steps={1: 2, 2: 3}),
        stable(450, 60, ['umask', 'file', 'dir'], [['022', '644', '755'], ['027', '640', '750'], ['077', '600', '700']], [80, 80, 80], step=4, title='common values', title_color='green'),
        stext(380, 200, 'new files never get x automatically: chmod +x scripts explicitly', 'amber', 12, step=3),
        stext(380, 225, 'set in ~/.bashrc or /etc/profile · umask 027 for shared servers keeps "others" out', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'New files start from 666 and directories from 777.',
        'The umask lists bits to remove; 022 removes write for group and others.',
        'Result: files 644, directories 755. Execute is never granted to new files automatically.',
        'Stricter masks: 027 hides files from other users, 077 makes everything private.',
        'Set the umask in shell start-up files so it applies to every session.',
    ])


def special_anim():
    elems = [
        stext(380, 24, 'Special permission bits and ACLs', 'blue', 15, bold=True),
        sbox(20, 55, 230, 80, 'SUID (4xxx) rws', 'program runs as its OWNER\n/usr/bin/passwd → root', 'red', step=1, size=12),
        sbox(265, 55, 230, 80, 'SGID (2xxx) on dir', 'new files inherit the\ndirectory\'s group', 'green', step=2, size=12),
        sbox(510, 55, 230, 80, 'sticky (1xxx) rwt', 'in /tmp: only the owner\ncan delete their files', 'amber', step=3, size=12),
        sbox(20, 155, 720, 50, 'ACLs: setfacl -m u:anuj:r report.csv · getfacl report.csv', 'extra per-user/per-group rules beyond owner/group/others', 'purple', step=4, size=12),
        stext(380, 235, 'chmod 2775 /data/dbda (shared team folder) · chmod 1777 /tmp · find / -perm -4000 (audit SUID files)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'SUID makes an executable run with its owner\'s privileges, e.g. passwd can update /etc/shadow.',
        'SGID on a directory makes new files belong to the directory\'s group: ideal for shared team folders.',
        'The sticky bit on a world-writable directory lets only a file\'s owner delete it, as in /tmp.',
        'Access Control Lists add fine-grained permissions for specific users or groups.',
        'Typical uses: a shared project directory with 2775, /tmp with 1777, and periodic SUID audits for security.',
    ])


def sudo_anim():
    elems = [
        stext(380, 24, 'root, su and sudo', 'blue', 15, bold=True),
        sbox(20, 55, 230, 70, 'root (uid 0)', 'can do anything\nno permission checks', 'red', step=1, size=12),
        sbox(265, 55, 230, 70, 'su - root', 'become root with\nROOT\'s password', 'amber', step=2, size=12),
        sbox(510, 55, 230, 70, 'sudo command', 'one command as root with\nYOUR password, logged', 'green', step=3, size=12, focus=3),
        _codebox(20, 145, 720, 60, ['%dbda-admins ALL=(ALL) ALL          # /etc/sudoers (edit with visudo)',
                                     'anuj ALL=(root) NOPASSWD: /usr/bin/systemctl restart kafka'], 'purple', step=4, tcolor='#c4b5fd'),
        stext(380, 235, 'least privilege: daily work as a normal user · sudo only when needed · audit in /var/log/auth.log', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 255, *elems), [
        'root has uid 0 and is not restricted by permissions.',
        '<code>su</code> switches to another account (default root) and needs that account\'s password.',
        '<code>sudo</code> runs a single command with elevated rights after checking the sudoers rules, using your own password, and logs it.',
        'sudoers rules can grant everything to a group or only specific commands to a user.',
        'Best practice: work as a normal user and elevate only for administrative commands.',
    ])


# ============================================================ section 3
def grep_anim():
    lines = ['09:00:01 INFO  Starting job', '09:00:07 WARN  Missing marks 2406', '09:00:09 ERROR Cannot connect MySQL', '09:00:21 INFO  Connected',
             '09:00:40 ERROR Duplicate key 2402-SQL']
    elems = [stext(380, 24, 'grep: keep the lines that match a pattern', 'blue', 15, bold=True)]
    for i, ln in enumerate(lines):
        hit = 'ERROR' in ln
        elems.append(scell(20, 50 + i * 30, 330, 28, ln, '#162033', step=1))
        if hit:
            elems.append(scell(20, 50 + i * 30, 330, 28, ln, '#ef4444', '#fff', step=2, bold=True))
    elems += [
        stext(560, 60, "grep ERROR app.log", 'red', 13, step=2, bold=True),
        stext(560, 90, '-i ignore case · -v invert · -c count', 'purple', 12, step=3),
        stext(560, 112, '-n line numbers · -w whole word', 'purple', 12, step=3),
        stext(560, 134, '-r recursive · -l file names only', 'purple', 12, step=3),
        stext(560, 165, "grep -E 'ERROR|WARN'  (extended regex)", 'amber', 12, step=4, bold=True),
        stext(560, 187, "grep -oE '[0-9]{4}'  (only the match)", 'amber', 12, step=4),
        stext(380, 228, 'regex: ^ start · $ end · . any char · * repeat · [0-9] class · \\b word boundary', 'cyan', 12, step=5),
        stext(380, 252, 'grep -c ERROR → 2 · grep -v INFO → warnings and errors only', 'green', 12, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'A log file with mixed levels.',
        '<code>grep PATTERN file</code> prints only lines containing the pattern.',
        'Options change what is matched or printed: case, inversion, counts, line numbers, whole words, recursion.',
        '<code>-E</code> enables extended regular expressions (alternation, {n} repeats); <code>-o</code> prints just the matched part.',
        'Regular expression basics give precise patterns: anchors, character classes and repetition.',
    ])


def sed_anim():
    elems = [
        stext(380, 24, 'sed: stream editor (edit text without opening it)', 'blue', 15, bold=True),
        _codebox(20, 50, 300, 110, ['2406,ML,AB', '2406,Python,72', '2404,Java,58'], 'gray', step=1),
        sbox(345, 50, 395, 40, "sed 's/AB/0/' marks.csv", 'substitute first match per line (g = all)', 'green', step=2, size=12),
        sbox(345, 98, 395, 40, "sed '1d' · sed '/^#/d' · sed -n '2,5p'", 'delete header · delete comments · print lines 2–5', 'purple', step=3, size=12),
        sbox(345, 146, 395, 40, "sed -i.bak 's/PG-DBDA/DBDA/g' students.csv", 'edit the file in place, keep a .bak backup', 'amber', step=4, size=12, focus=4),
        stext(380, 215, "groups: sed -E 's/([0-9]+),(.*)/\\2:\\1/' swaps fields · any delimiter: s#/old/path#/new/path#", 'cyan', 12, step=5),
        stext(380, 240, 'sed reads line by line → works on files larger than memory', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 258, *elems), [
        'sed reads input line by line and applies editing commands.',
        '<code>s/old/new/</code> substitutes; add <code>g</code> to replace every match on the line.',
        'Addresses select lines: by number, range or pattern; <code>d</code> deletes, <code>p</code> prints (with <code>-n</code>).',
        '<code>-i</code> edits the file in place; <code>-i.bak</code> keeps a backup first.',
        'Capture groups and alternative delimiters make complex rewrites possible, and streaming means file size does not matter.',
    ])


def awk_anim():
    elems = [
        stext(380, 24, 'awk: fields, conditions and totals', 'blue', 15, bold=True),
        stable(20, 55, ['$1', '$2', '$3'], [['2401', 'SQL', '82'], ['2401', 'Spark', '61'], ['2402', 'SQL', '91'], ['2404', 'Java', '58']], [70, 70, 60], step=1,
               title="-F, splits on commas", title_color='blue', focus_rows={3: '2'}),
        _codebox(250, 50, 490, 54, ["awk -F, '$3 < 60 {print $1, $2}' marks.csv", '→ 2404 Java'], 'red', step=2, tcolor='#fca5a5'),
        _codebox(250, 112, 490, 54, ["awk -F, '{sum[$2]+=$3; n[$2]++} END {for (s in sum) print s, sum[s]/n[s]}'",
                                      '→ average per subject (associative arrays)'], 'green', step=3, tcolor='#86efac'),
        _codebox(250, 174, 490, 54, ["awk -F, 'NR > 1 && $3 ~ /^[0-9]+$/ {print}'", 'NR = line number · ~ regex match · skip header'], 'purple', step=4, tcolor='#c4b5fd'),
        stext(380, 255, 'pattern { action } · BEGIN{} before input · END{} after · NF fields · OFS output separator · printf formatting', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 272, *elems), [
        'awk splits each line into fields $1, $2, $3… (here on commas with <code>-F,</code>).',
        'A condition selects lines and an action prints chosen fields: marks below 60.',
        'Associative arrays accumulate per key; the END block prints results after all lines: a GROUP BY in one line.',
        'Built-in variables (NR, NF) and regex matches handle headers and bad values such as "AB".',
        'Structure: <code>pattern { action }</code>, with optional BEGIN and END blocks.',
    ])


def pipe_text_anim():
    elems = [stext(380, 24, 'Classic pipeline: top cities by student count', 'blue', 15, bold=True)]
    stages = [('tail -n +2', 'drop header', 'gray'), ('cut -d, -f5', 'city column', 'blue'), ('sort', 'group equal lines', 'purple'),
              ('uniq -c', 'count each', 'green'), ('sort -rn', 'biggest first', 'amber'), ('head -3', 'top 3', 'red')]
    for i, (t, s, c) in enumerate(stages):
        x = 20 + i * 123
        elems.append(sbox(x, 55, 112, 56, t, s, c, step=i + 1 if i < 5 else 5, size=12))
        if i:
            elems.append(sarrow(x - 11, 83, x - 1, 83, 'gray', step=i + 1 if i < 5 else 5))
    elems += [
        _codebox(20, 130, 220, 118, ['Pune', 'Navi Mumbai', 'Mumbai', 'Thane', 'Pune', 'Mumbai'], 'blue', step=2, tcolor='#7dd3fc'),
        _codebox(270, 130, 220, 118, ['Mumbai', 'Mumbai', 'Navi Mumbai', 'Pune', 'Pune', 'Thane'], 'purple', step=3, tcolor='#c4b5fd'),
        _codebox(520, 130, 220, 118, ['  2 Pune', '  2 Mumbai', '  1 Thane', '', '(uniq only merges ADJACENT', ' duplicates → sort first)'], 'green', step=4, tcolor='#86efac'),
        stext(380, 275, 'each tool does one job; | connects stdout of one to stdin of the next (the Unix philosophy)', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 292, *elems), [
        'Skip the CSV header line.',
        'Cut out the fifth comma-separated field: the city.',
        'Sort so identical cities are next to each other.',
        '<code>uniq -c</code> collapses adjacent duplicates and counts them, which is why sorting first is essential.',
        'Sort numerically in reverse and keep the top lines. Six small tools, one pipeline, no program needed.',
    ])


def find_anim():
    elems = [
        stext(380, 24, 'find: search by name, type, size, age, then act', 'blue', 15, bold=True),
        _codebox(20, 50, 340, 150, ['logs/', '  app-2026-10-01.log   12M  12 days old', '  app-2026-10-12.log    3M   1 day old', '  app-2026-10-13.log    1M   today',
                                    'data/', '  marks.csv', '  backup.tar.gz         80M'], 'gray', step=1),
        sbox(380, 50, 360, 40, "find . -name '*.log'", 'by name (quote the pattern!)', 'blue', step=2, size=12),
        sbox(380, 98, 360, 40, 'find logs -type f -mtime +7', 'modified more than 7 days ago', 'purple', step=3, size=12),
        sbox(380, 146, 360, 40, 'find . -size +50M', 'bigger than 50 MB', 'amber', step=3, size=12),
        _codebox(20, 215, 720, 50, ["find logs -name '*.log' -mtime +7 -delete      ·      find . -name '*.csv' -exec wc -l {} +      ·      | xargs gzip"],
                 'green', step=4, tcolor='#86efac'),
        stext(380, 285, 'test first without -delete · -exec … {} + batches many files per command (fast)', 'red', 12, step=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'A directory tree with logs of different ages and sizes.',
        'find walks the tree; <code>-name</code> matches file names with wildcards (quoted so the shell does not expand them).',
        'Tests combine: type, modification time in days, size.',
        'Actions: <code>-delete</code>, <code>-exec cmd {} +</code>, or pipe the names into <code>xargs</code>.',
        'Always run the search without the destructive action first and check the list.',
    ])


# ============================================================ section 4
def redirect_anim():
    elems = [
        stext(380, 24, 'Every process has three standard streams', 'blue', 15, bold=True),
        sbox(280, 95, 200, 70, 'command', 'e.g. python job.py', 'blue', step=1, size=13),
        sbox(20, 105, 180, 50, '0 stdin', 'keyboard / < file', 'gray', step=1, size=12), sarrow(200, 130, 278, 130, 'gray', step=1),
        sbox(560, 60, 180, 50, '1 stdout', 'normal output', 'green', step=1, size=12), sarrow(480, 115, 558, 88, 'green', step=1),
        sbox(560, 150, 180, 50, '2 stderr', 'error messages', 'red', step=1, size=12), sarrow(480, 145, 558, 172, 'red', step=1),
        _codebox(20, 215, 720, 70, ['cmd > out.txt   (overwrite)   cmd >> out.txt   (append)   cmd 2> err.txt   cmd > all.log 2>&1   cmd &> all.log',
                                     'cmd < input.txt      cmd 2>/dev/null   (discard errors)      cmd | tee run.log   (screen AND file)'], 'amber', step=2, tcolor='#fde68a'),
        stext(380, 305, 'order matters: > file 2>&1 sends both to file · 2>&1 > file sends errors to the screen', 'red', 12, step=3, focus=3),
    ]
    return anim(canvas(760, 320, *elems), [
        'A command reads stdin (0) and writes normal output to stdout (1) and errors to stderr (2). By default all are the terminal.',
        'Redirection connects them to files: overwrite, append, separate error file, both together, discard to /dev/null, or tee to both screen and file.',
        '<code>2&gt;&amp;1</code> means "send stderr where stdout currently goes", so it must come after <code>&gt; file</code>.',
    ])


def chain_anim():
    elems = [
        stext(380, 24, 'Combining commands', 'blue', 15, bold=True),
        sbox(20, 55, 230, 60, 'a ; b', 'run b after a, always', 'gray', step=1, size=13),
        sbox(265, 55, 230, 60, 'a && b', 'run b only if a succeeded (exit 0)', 'green', step=2, size=12),
        sbox(510, 55, 230, 60, 'a || b', 'run b only if a failed', 'red', step=3, size=12),
        sbox(20, 135, 230, 60, 'a | b', 'stdout of a → stdin of b', 'blue', step=4, size=13),
        sbox(265, 135, 230, 60, '( cd x; cmd )', 'subshell: changes do not leak', 'purple', step=5, size=12),
        sbox(510, 135, 230, 60, '{ a; b; } > out', 'group, one redirection', 'amber', step=5, size=12),
        stext(380, 230, 'mkdir -p out && python etl.py > out/run.log 2>&1 || echo "ETL failed" | mail -s alert admin', 'cyan', 12, step=4),
        stext(380, 255, '$? holds the exit status of the last command: 0 = success, anything else = failure', 'amber', 12, step=2),
    ]
    return anim(canvas(760, 272, *elems), [
        'A semicolon runs commands one after another regardless of outcome.',
        '<code>&amp;&amp;</code> continues only after success; the exit status is in <code>$?</code> (0 means success).',
        '<code>||</code> runs a fallback when the previous command failed.',
        'A pipe streams one command\'s output into the next.',
        'Parentheses run commands in a subshell (cd and variables do not affect the parent); braces group commands in the current shell.',
    ])


def env_anim():
    elems = [
        stext(380, 24, 'Shell variables, environment variables and PATH', 'blue', 15, bold=True),
        sbox(20, 55, 230, 60, 'BATCH=aug26', 'shell variable: this shell only', 'gray', step=1, size=12),
        sbox(265, 55, 230, 60, 'export BATCH', 'environment: inherited by child processes', 'green', step=2, size=12),
        sbox(510, 55, 230, 60, 'child: python job.py', "os.environ['BATCH'] → aug26", 'blue', step=2, size=12),
        sarrow(495, 85, 508, 85, 'gray', step=2),
        _codebox(20, 135, 720, 60, ['PATH=/home/student/bin:/usr/local/bin:/usr/bin:/bin     → searched left to right for commands',
                                     'export PATH="$HOME/bin:$PATH"      export JAVA_HOME=/usr/lib/jvm/java-17'], 'amber', step=3, tcolor='#fde68a'),
        stext(380, 220, '~/.bashrc (every interactive shell) · ~/.profile / ~/.bash_profile (login) · source ~/.bashrc to reload', 'purple', 12, step=4),
        stext(380, 245, 'env / printenv list the environment · unset VAR removes · VAR=x cmd sets it for one command', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 262, *elems), [
        'Assigning creates a shell variable visible only in the current shell (no spaces around =).',
        '<code>export</code> puts it in the environment, so programs started from this shell inherit it.',
        'PATH is the list of directories searched for commands; prepend your own bin directory to override.',
        'Put exports in start-up files to make them permanent; source the file to apply changes now.',
        'Inspect with env/printenv; set a variable for a single command with <code>VAR=value cmd</code>.',
    ])


def quote_anim():
    elems = [
        stext(380, 24, 'Quoting and expansions', 'blue', 15, bold=True),
        _codebox(20, 50, 720, 120, ["name=Vineeta; file='my marks.csv'",
                                    "echo 'Hello $name'      → Hello $name          (single quotes: literal)",
                                    'echo "Hello $name"      → Hello Vineeta        (double quotes: $ expanded)',
                                    'echo "Today: $(date +%F)"  → command substitution',
                                    'echo $((7 * 6))          → 42 (arithmetic)        echo {1..3} → 1 2 3 (brace)',
                                    'ls *.csv                 → globbing: the SHELL expands * before ls runs'], 'gray', step=1),
        sbox(20, 190, 350, 56, 'rm $file  →  rm my marks.csv', 'word splitting: two files "my" and "marks.csv"!', 'red', step=2, size=12, focus=2),
        sbox(390, 190, 350, 56, 'rm "$file"', 'always quote variables', 'green', step=3, size=12, focus=3),
        stext(380, 275, 'expansion order: brace → tilde → variables/command/arithmetic → word splitting → globbing', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 292, *elems), [
        'Single quotes keep text literal; double quotes allow variable, command and arithmetic expansion; braces and globs generate words.',
        'Unquoted variables are split on spaces, so a file name with a space becomes two arguments: a classic, dangerous bug.',
        'Quoting "$var" keeps it one argument. Rule: always double-quote variables unless you need splitting.',
        'The shell performs expansions in a fixed order before the command ever runs.',
    ])


def links_anim():
    elems = [
        stext(380, 24, 'Hard links vs symbolic links', 'blue', 15, bold=True),
        sbox(300, 160, 160, 60, 'inode 4711', 'data blocks of marks.csv', 'gray', step=1, size=12),
        sbox(40, 60, 180, 44, 'marks.csv', 'name → inode', 'blue', step=1, size=12), sarrow(160, 104, 330, 158, 'blue', step=1),
        sbox(40, 140, 180, 44, 'marks_hard.csv', 'ln: 2nd name, same inode', 'green', step=2, size=12), sarrow(220, 165, 298, 185, 'green', step=2),
        sbox(540, 60, 200, 44, 'latest.csv → marks.csv', 'ln -s: points to a NAME', 'purple', step=3, size=12), sarrow(540, 82, 222, 82, 'purple', step=3, dashed=True),
        stext(600, 140, 'rm marks.csv:', 'red', 12, step=4, bold=True),
        stext(600, 160, 'hard link still works', 'green', 12, step=4),
        stext(600, 180, 'symlink becomes dangling', 'red', 12, step=4),
        stext(380, 250, 'hard: same filesystem, files only · soft: any path, directories too, shown as l in ls -l', 'cyan', 12, step=5),
        stext(380, 275, 'typical: /opt/spark → /opt/spark-3.5.1 (switch versions by repointing the symlink)', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 292, *elems), [
        'A file name is a directory entry pointing to an inode, which holds the metadata and data blocks.',
        'A hard link is a second name for the same inode; both names are equal.',
        'A symbolic link is a small file containing a path to another name.',
        'Delete the original name: the hard link keeps the data alive, the symlink now points to nothing.',
        'Symlinks can cross filesystems and point to directories, which is why they are used for versioned software installs.',
    ])


# ============================================================ section 5
def script_anim():
    elems = [
        stext(380, 24, 'Anatomy of a shell script', 'blue', 15, bold=True),
        _codebox(20, 50, 400, 190, ['#!/usr/bin/env bash', '# report.sh <course> [min_marks]', 'course="$1"', 'min="${2:-60}"     # default value',
                                    'echo "script: $0, args: $#"', 'echo "all args: $@"', 'grep "$course" students.csv', 'exit 0'], 'gray', step=1),
        sbox(440, 50, 300, 40, '#!  shebang', 'which interpreter runs the file', 'blue', step=2, size=12),
        sbox(440, 98, 300, 40, '$0 $1 $2 … $# $@', 'name, arguments, count, all', 'green', step=3, size=12),
        sbox(440, 146, 300, 40, '${2:-60}', 'parameter default when missing', 'purple', step=3, size=12),
        sbox(440, 194, 300, 46, 'chmod +x report.sh', './report.sh PG-DBDA 50', 'amber', step=4, size=12),
        stext(380, 265, 'exit status of the script = exit N (or the last command); $? shows it to the caller', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 282, *elems), [
        'A script is a text file of commands, run top to bottom.',
        'The first line (shebang) tells the system which interpreter to use; <code>/usr/bin/env bash</code> finds bash on PATH.',
        'Positional parameters carry arguments: $1, $2…, $# is the count, "$@" all of them; ${var:-default} supplies defaults.',
        'Make it executable and run it with a path, or run <code>bash report.sh</code> without the x bit.',
        'The script\'s exit status tells callers (cron, CI, other scripts) whether it succeeded.',
    ])


def if_anim():
    elems = [
        stext(380, 24, 'Decisions: if, test operators and case', 'blue', 15, bold=True),
        _codebox(20, 50, 360, 140, ['if [[ -f "$file" && -s "$file" ]]; then', '    echo "processing $file"', 'elif [[ -e "$file" ]]; then',
                                    '    echo "empty file"', 'else', '    echo "missing"; exit 1', 'fi'], 'blue', step=1, tcolor='#7dd3fc'),
        stable(400, 50, ['test', 'meaning'], [['-f / -d / -e', 'file / dir / exists'], ['-s', 'non-empty'], ['-r -w -x', 'permissions'], ['== != =~', 'strings, regex'],
                                              ['-eq -lt -ge', 'integers'], ['-z / -n', 'empty / non-empty']], [120, 220], step=2),
        _codebox(20, 205, 360, 80, ['case "$course" in', '  PG-DBDA) fee=95000 ;;', '  PG-DAC|PG-DAI) fee=90000 ;;', '  *) echo unknown ;;  esac'], 'purple', step=3, tcolor='#c4b5fd'),
        stext(570, 252, '[[ ]] is bash: safer with spaces, supports && || =~', 'amber', 12, step=4),
        stext(570, 274, '(( marks >= 60 )) for arithmetic tests', 'amber', 12, step=4),
    ]
    return anim(canvas(760, 295, *elems), [
        '<code>if</code> runs a command and branches on its exit status; <code>[[ … ]]</code> is a test command.',
        'File tests check existence, type, size and permissions; string and integer comparisons use different operators.',
        '<code>case</code> matches a value against patterns, cleaner than many elifs.',
        'Prefer <code>[[ ]]</code> in bash scripts and <code>(( ))</code> for arithmetic comparisons.',
    ])


def loop_anim():
    elems = [
        stext(380, 24, 'Loops: for, while, reading a file line by line', 'blue', 15, bold=True),
        _codebox(20, 50, 350, 70, ['for f in data/*.csv; do', '    wc -l "$f"', 'done'], 'blue', step=1, tcolor='#7dd3fc'),
        _codebox(390, 50, 350, 70, ['for i in {1..5}; do …; done', 'for ((i = 0; i < 5; i++)); do …; done'], 'green', step=2, tcolor='#86efac'),
        _codebox(20, 135, 350, 100, ['while IFS=, read -r roll name course _; do', '    echo "$name → $course"', 'done < <(tail -n +2 students.csv)'], 'purple', step=3, tcolor='#c4b5fd'),
        _codebox(390, 135, 350, 100, ['tries=0', 'until ping_db || (( ++tries > 3 )); do', '    sleep 5', 'done'], 'amber', step=4, tcolor='#fde68a'),
        stext(380, 262, 'never: for line in $(cat file) (splits on spaces) · break / continue control the loop', 'red', 12, step=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'for loops over a list of words or a glob of files; quote "$f" for names with spaces.',
        'Ranges with braces, or C-style loops with arithmetic.',
        'The safe way to read a file line by line: <code>while IFS=, read -r …</code> fed from the file; IFS splits fields.',
        'until/while with a counter implement retries.',
        'Do not loop over $(cat file): it splits on every space, not on lines.',
    ])


def func_anim():
    elems = [
        stext(380, 24, 'Functions and robust scripts', 'blue', 15, bold=True),
        _codebox(20, 50, 360, 120, ['log() { echo "$(date +%T) [$1] $2" >&2; }', 'is_number() { [[ $1 =~ ^[0-9]+$ ]]; }', '',
                                    'is_number "$m" || { log WARN "bad: $m"; continue; }'], 'blue', step=1, tcolor='#7dd3fc'),
        _codebox(400, 50, 340, 120, ['set -euo pipefail', '  -e  exit on any failing command', '  -u  error on unset variables', '  -o pipefail  failing pipe stage counts'],
                 'red', step=2, tcolor='#fca5a5'),
        _codebox(20, 185, 360, 80, ['tmp=$(mktemp -d)', "trap 'rm -rf \"$tmp\"' EXIT", "trap 'log ERROR \"line $LINENO\"' ERR"], 'green', step=3, tcolor='#86efac'),
        sbox(400, 185, 340, 80, 'return N / exit N', 'functions return a status (0–255);\noutput values via echo + $(…)', 'purple', step=4, size=12),
        stext(380, 290, 'local var inside functions · shellcheck catches most scripting bugs', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 305, *elems), [
        'Functions group reusable steps; their exit status can be used directly in if/||.',
        '"Strict mode" makes scripts stop on errors and unset variables instead of carrying on with bad data.',
        '<code>trap</code> runs clean-up on exit (even after an error) and can report the failing line.',
        'Functions return a status; to return data, print it and capture with $(…).',
        'Use <code>local</code> for function variables and run ShellCheck before trusting a script.',
    ])


def arrays_anim():
    elems = [
        stext(380, 24, 'Arrays, strings, arithmetic and options', 'blue', 15, bold=True),
        _codebox(20, 50, 360, 100, ['subjects=(SQL Spark ML)', 'echo "${subjects[1]}"     # Spark', 'echo "${#subjects[@]}"   # 3', 'for s in "${subjects[@]}"; do …'],
                 'blue', step=1, tcolor='#7dd3fc'),
        _codebox(400, 50, 340, 100, ['declare -A fee=([PG-DBDA]=95000)', 'echo "${fee[PG-DBDA]}"', '', '# associative array (bash 4+)'], 'green', step=2, tcolor='#86efac'),
        _codebox(20, 165, 360, 100, ['f=marks_2026.csv', '${f%.csv} → marks_2026  ${f#marks_} → 2026.csv', '${#f} → 14  ${f^^} → MARKS_2026.CSV',
                                     '${f/2026/2027} → marks_2027.csv'], 'purple', step=3, tcolor='#c4b5fd'),
        _codebox(400, 165, 340, 100, ['total=$(( 82 + 61 ))', 'avg=$(echo "scale=2; 143/2" | bc)', 'while getopts "c:m:v" opt; do', '  case $opt in c) course=$OPTARG;; …'],
                 'amber', step=4, tcolor='#fde68a'),
        stext(380, 290, 'bash arithmetic is integer-only → bc or awk for decimals', 'red', 12, step=5),
    ]
    return anim(canvas(760, 305, *elems), [
        'Indexed arrays hold lists; "${arr[@]}" expands to all elements safely.',
        'Associative arrays map keys to values.',
        'Parameter expansion trims prefixes/suffixes, measures length, changes case and substitutes, with no external commands.',
        '$(( )) does integer arithmetic; getopts parses -c value style options.',
        'For decimals use bc or awk, because bash itself only does integers.',
    ])


# ============================================================ section 6
def process_anim():
    elems = [
        stext(380, 24, 'Processes, PIDs and signals', 'blue', 15, bold=True),
        sbox(20, 55, 180, 50, 'systemd / init', 'PID 1', 'gray', step=1, size=12),
        sbox(240, 55, 180, 50, 'bash', 'PID 4120 (PPID 1)', 'blue', step=1, size=12), sarrow(200, 80, 238, 80, 'gray', step=1),
        sbox(460, 55, 280, 50, 'python etl.py', 'PID 4188 (PPID 4120)', 'green', step=1, size=12), sarrow(420, 80, 458, 80, 'gray', step=1),
        stable(20, 130, ['state', 'meaning'], [['R', 'running'], ['S', 'sleeping (waiting)'], ['D', 'uninterruptible I/O'], ['Z', 'zombie (exited, not reaped)'], ['T', 'stopped']],
               [60, 220], step=2),
        stable(340, 130, ['signal', 'effect'], [['15 TERM', 'please stop (default kill)'], ['9 KILL', 'stop now, cannot be caught'], ['2 INT', 'Ctrl+C'], ['1 HUP', 'reload / terminal closed'],
                                                ['19 STOP / 18 CONT', 'pause / resume']], [140, 260], step=3),
        stext(380, 300, 'ps aux · ps -ef --forest · top/htop · pgrep -f etl · kill PID · pkill -f etl · kill -9 only as a last resort', 'cyan', 12, step=4),
    ]
    return anim(canvas(760, 318, *elems), [
        'Every running program is a process with a PID and a parent (PPID); everything descends from PID 1.',
        'The state column shows what a process is doing: running, sleeping, waiting on disk, zombie or stopped.',
        'Signals ask processes to do things: TERM asks politely (programs can clean up), KILL forces termination.',
        'ps/top inspect processes; pgrep/pkill find and signal them by name. Try TERM before KILL.',
    ])


def jobs_anim():
    elems = [
        stext(380, 24, 'Foreground, background and surviving logout', 'blue', 15, bold=True),
        sbox(20, 55, 230, 60, 'spark-submit job.py', 'foreground: terminal busy', 'gray', step=1, size=12),
        sbox(265, 55, 230, 60, 'spark-submit job.py &', 'background: prompt returns', 'green', step=2, size=12),
        sbox(510, 55, 230, 60, 'jobs · fg %1 · bg %1', 'Ctrl+Z suspends a foreground job', 'purple', step=3, size=12),
        sbox(20, 135, 350, 66, 'nohup ./etl.sh > etl.log 2>&1 &', 'ignores HUP: keeps running after you log out', 'amber', step=4, size=12, focus=4),
        sbox(390, 135, 350, 66, 'tmux / screen', 'reattachable sessions on servers', 'cyan', step=5, size=12),
        stext(380, 235, 'closing the terminal sends SIGHUP to its jobs → plain & jobs die · disown removes a job from the shell', 'red', 12, step=4),
        stext(380, 260, 'for real services use systemd units, not nohup', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 278, *elems), [
        'A foreground command occupies the terminal until it finishes.',
        'An ampersand starts it in the background and returns the prompt.',
        'Job control: list jobs, bring one to the foreground, Ctrl+Z to suspend, bg to resume in the background.',
        'Logging out sends SIGHUP; nohup (with output redirected) keeps a long job alive.',
        'tmux/screen keep whole sessions alive and reattachable; production services belong in systemd.',
    ])


def disk_anim():
    elems = [
        stext(380, 24, 'Disk and memory checks', 'blue', 15, bold=True),
        sbox(20, 55, 230, 60, 'df -h', 'free space per filesystem', 'blue', step=1, size=13),
        sbox(265, 55, 230, 60, 'du -sh dir/*', 'what is using the space', 'green', step=2, size=13),
        sbox(510, 55, 230, 60, 'free -h', 'RAM, swap, buff/cache', 'purple', step=3, size=13),
        sbox(20, 135, 350, 60, 'du -ah /data | sort -rh | head', 'the biggest files and folders', 'amber', step=2, size=12),
        sbox(390, 135, 350, 60, 'lsof +L1', 'deleted files still held open (space not freed)', 'red', step=4, size=12, focus=4),
        stext(380, 230, '"available" in free is what matters: cache is given back to programs when needed', 'cyan', 12, step=3),
        stext(380, 255, 'df -i → inodes · iostat / vmstat for I/O and memory pressure over time', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 272, *elems), [
        '<code>df</code> reports free space per mounted filesystem.',
        '<code>du</code> measures directories; sorted output finds what filled the disk.',
        '<code>free</code> shows memory; Linux uses spare RAM as cache, so "available" is the useful number.',
        'If df says full but du cannot find the space, a deleted file is still held open by a process: lsof shows it.',
        'Inodes and I/O statistics complete the picture.',
    ])


def cron_anim():
    fields = [('*/15', 'minute', 'blue'), ('2', 'hour', 'green'), ('*', 'day of month', 'purple'), ('*', 'month', 'amber'), ('1-5', 'day of week', 'red')]
    elems = [stext(380, 24, 'cron: run commands on a schedule', 'blue', 15, bold=True)]
    for i, (v, n, c) in enumerate(fields):
        elems.append(sbox(20 + i * 100, 55, 90, 56, v, n, c, step=1, size=13))
    elems += [
        sbox(530, 55, 210, 56, '/opt/etl/run.sh', 'command (absolute path)', 'gray', step=1, size=12),
        stext(380, 140, '"every 15 minutes during 02:00–02:59, Monday to Friday"', 'amber', 13, step=2, bold=True),
        _codebox(20, 160, 720, 70, ['0 2 * * *  /opt/etl/nightly.sh >> /var/log/etl/nightly.log 2>&1      # daily 02:00',
                                     '30 8 1 * *  /opt/reports/monthly.sh                                   # 08:30 on the 1st'], 'green', step=3, tcolor='#86efac'),
        stext(380, 255, 'crontab -e edit · crontab -l list · cron has a minimal PATH and no .bashrc → absolute paths, set variables', 'red', 12, step=4),
        stext(380, 280, 'alternatives: systemd timers · Airflow for dependencies, retries and monitoring', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 295, *elems), [
        'A crontab line has five time fields (minute, hour, day of month, month, day of week) then the command.',
        'Steps (*/15), ranges (1-5) and lists (1,15) combine into precise schedules.',
        'Typical entries redirect output to a log so failures are visible.',
        'Cron runs with a minimal environment: use absolute paths and define needed variables in the script.',
        'For pipelines with dependencies and retries, an orchestrator such as Airflow is the next step.',
    ])


def systemd_anim():
    elems = [
        stext(380, 24, 'Services with systemd and logs with journalctl', 'blue', 15, bold=True),
        _codebox(20, 50, 340, 190, ['[Unit]', 'Description=Kafka broker', 'After=network.target', '', '[Service]', 'User=kafka',
                                    'ExecStart=/opt/kafka/bin/kafka-server-start.sh …', 'Restart=on-failure', '', '[Install]', 'WantedBy=multi-user.target'], 'gray', step=1),
        sbox(380, 50, 360, 40, 'systemctl start | stop | restart kafka', 'control now', 'green', step=2, size=12),
        sbox(380, 98, 360, 40, 'systemctl enable kafka', 'start at boot', 'blue', step=2, size=12),
        sbox(380, 146, 360, 40, 'systemctl status kafka', 'running? PID, last log lines', 'purple', step=3, size=12),
        sbox(380, 194, 360, 46, 'journalctl -u kafka -f --since "1 hour ago"', 'logs of one service, follow', 'amber', step=4, size=12),
        stext(380, 265, 'files: /var/log/syslog · auth.log · application logs in /var/log/<app> or $APP_HOME/logs', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 282, *elems), [
        'A unit file describes how to run a service: user, command, restart policy, dependencies.',
        'systemctl starts/stops it now and enables it at boot.',
        'status shows whether it runs, its PID and recent log lines.',
        'journalctl reads the systemd journal, filtered by unit and time, and can follow live.',
        'Classic text logs remain under /var/log; big-data tools also keep logs in their own directories.',
    ])


# ============================================================ section 7
def tar_anim():
    elems = [
        stext(380, 24, 'Archiving (tar) vs compressing (gzip, zip)', 'blue', 15, bold=True),
        sbox(20, 55, 150, 40, 'marks.csv', '', 'gray', step=1, size=11), sbox(20, 100, 150, 40, 'students.csv', '', 'gray', step=1, size=11),
        sbox(20, 145, 150, 40, 'scripts/', '', 'gray', step=1, size=11),
        sarrow(170, 120, 218, 120, 'blue', step=2),
        sbox(220, 90, 160, 60, 'batch.tar', 'one file, not smaller', 'blue', step=2, size=12),
        sarrow(380, 120, 428, 120, 'green', step=3),
        sbox(430, 90, 160, 60, 'batch.tar.gz', 'compressed', 'green', step=3, size=12),
        sbox(610, 90, 130, 60, '.zip', 'archive + compress\nper file', 'purple', step=4, size=12),
        _codebox(20, 200, 720, 70, ['tar -czvf batch.tar.gz data/ scripts/      c create · z gzip · v verbose · f file name',
                                     'tar -tzf batch.tar.gz (list) · tar -xzf batch.tar.gz -C /restore (extract) · -j bzip2 · -J xz'], 'amber', step=5, tcolor='#fde68a'),
    ]
    return anim(canvas(760, 285, *elems), [
        'Several files and folders to back up or ship.',
        '<code>tar</code> bundles them into one archive file, keeping paths and permissions, without compressing.',
        'gzip (or bzip2/xz) compresses the archive: tar does both with <code>-z</code>.',
        'zip archives and compresses each file, common for exchange with Windows users.',
        'Flags to remember: c create, x extract, t list, z gzip, v verbose, f file; -C chooses the extraction directory.',
    ])


def ssh_anim():
    elems = [
        stext(380, 24, 'SSH: secure remote login with keys', 'blue', 15, bold=True),
        sbox(20, 60, 220, 130, 'your laptop', '~/.ssh/id_ed25519 (PRIVATE, 600)\n~/.ssh/id_ed25519.pub\n~/.ssh/config', 'blue', step=1, size=12),
        sbox(520, 60, 220, 130, 'lab server', '~/.ssh/authorized_keys\n(your PUBLIC key)\nsshd on port 22', 'green', step=2, size=12),
        sarrow(240, 100, 518, 100, 'amber', step=2), stext(380, 92, 'ssh-copy-id student@lab', 'amber', 11, step=2),
        sarrow(240, 150, 518, 150, 'purple', step=3), stext(380, 142, 'ssh lab  → challenge signed with the private key', 'purple', 11, step=3),
        stext(380, 222, 'scp file lab:/data/ · rsync -avz dir/ lab:/data/dir/ · ssh -L 8888:localhost:8888 lab (tunnel Jupyter)', 'cyan', 12, step=4),
        stext(380, 248, 'private key never leaves your machine · chmod 700 ~/.ssh, 600 private key, or ssh refuses it', 'red', 12, step=5),
    ]
    return anim(canvas(760, 265, *elems), [
        'ssh-keygen creates a key pair: a private key that stays with you and a public key you can share.',
        'The public key is appended to authorized_keys on the server (ssh-copy-id does it).',
        'On login the server challenges, your client proves it holds the private key: no password travels.',
        'The same channel copies files (scp, rsync) and forwards ports for web UIs and notebooks.',
        'Strict permissions on ~/.ssh are required; leaked private keys must be replaced.',
    ])


def net_anim():
    elems = [
        stext(380, 24, 'Networking checks from the command line', 'blue', 15, bold=True),
        sbox(20, 55, 230, 56, 'ip addr / hostname -I', 'my IP addresses', 'blue', step=1, size=12),
        sbox(265, 55, 230, 56, 'ss -tlnp', 'which ports are listening', 'green', step=2, size=12),
        sbox(510, 55, 230, 56, 'curl -I http://host:port', 'is the service answering?', 'purple', step=3, size=12),
        sbox(20, 130, 230, 56, 'ping / traceroute', 'reachability, route', 'gray', step=4, size=12),
        sbox(265, 130, 230, 56, 'nc -zv host 9092', 'is a TCP port open?', 'amber', step=4, size=12),
        sbox(510, 130, 230, 56, '/etc/hosts · dig / nslookup', 'name resolution', 'cyan', step=4, size=12),
        stext(380, 220, 'common ports: 22 SSH · 80/443 HTTP(S) · 3306 MySQL · 9870 HDFS UI · 8088 YARN · 9092 Kafka · 4040 Spark UI', 'amber', 12, step=5),
        stext(380, 245, '"connection refused" = host reachable, nothing listening · "timed out" = firewall/route problem', 'red', 12, step=5),
    ]
    return anim(canvas(760, 262, *elems), [
        'Find the machine\'s addresses.',
        'List listening sockets to confirm a service is up and on which port/interface.',
        'Talk to it: curl for HTTP services shows status codes and headers.',
        'Reachability and DNS tools narrow down where a connection fails.',
        'Know the usual ports of the big-data stack, and the difference between "refused" and "timed out".',
    ])


def bigdata_env_anim():
    elems = [
        stext(380, 24, 'Preparing a Linux machine for Hadoop/Spark', 'blue', 15, bold=True),
        sbox(20, 55, 170, 60, 'Java', 'java -version\nJAVA_HOME', 'red', step=1, size=12),
        sbox(205, 55, 170, 60, '/opt/hadoop', 'tar -xzf, symlink', 'blue', step=2, size=12),
        sbox(390, 55, 170, 60, '~/.bashrc', 'HADOOP_HOME, PATH', 'green', step=3, size=12),
        sbox(575, 55, 165, 60, 'ssh localhost', 'passwordless (start scripts)', 'purple', step=4, size=12),
        _codebox(20, 135, 720, 105, ['export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))',
                                     'export HADOOP_HOME=/opt/hadoop',
                                     'export SPARK_HOME=/opt/spark',
                                     'export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin',
                                     'source ~/.bashrc && hadoop version && spark-submit --version'], 'amber', step=3, tcolor='#fde68a'),
        stext(380, 262, 'checklist: Java version matches the release · dedicated user · data dirs owned by it · ulimit -n raised · firewall ports', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 280, *elems), [
        'Hadoop, Spark, Hive and Kafka run on the JVM: install a supported Java and know its path.',
        'Unpack the release under /opt, often behind a version-independent symlink.',
        'Export HOME variables and extend PATH in the user\'s shell start-up file.',
        'Hadoop\'s start scripts ssh to every node (even localhost), so passwordless SSH is needed.',
        'Production checklists add a service user, ownership of data directories, higher open-file limits and firewall rules.',
    ])


def pkg_anim():
    elems = [
        stext(380, 24, 'Installing software: system packages vs Python packages', 'blue', 15, bold=True),
        sbox(20, 55, 350, 110, 'Debian/Ubuntu: apt (.deb)', 'sudo apt update\nsudo apt install openjdk-17-jdk\napt list --installed · dpkg -l', 'blue', step=1, size=12),
        sbox(390, 55, 350, 110, 'RHEL/Rocky: dnf / yum (.rpm)', 'sudo dnf install java-17-openjdk\nrpm -qa | grep java', 'red', step=2, size=12),
        sbox(20, 180, 350, 80, 'Python: venv + pip', 'python3 -m venv .venv\nsource .venv/bin/activate; pip install pandas', 'green', step=3, size=12),
        sbox(390, 180, 350, 80, 'tarballs in /opt', 'Hadoop, Spark, Kafka releases\n(not always packaged)', 'purple', step=4, size=12),
        stext(380, 290, 'never "sudo pip install" into the system Python (Ubuntu 24.04 blocks it: externally-managed-environment)', 'amber', 12, step=5),
    ]
    return anim(canvas(760, 305, *elems), [
        'Ubuntu/Debian use apt and .deb packages with dependency resolution and updates.',
        'Red Hat family systems use dnf/yum and .rpm packages.',
        'Python libraries belong in a virtual environment per project.',
        'Big-data software is often installed from release tarballs into /opt.',
        'Mixing pip with the system Python can break OS tools; recent Ubuntu refuses it by default.',
    ])


# ============================================================ section 8
def logscen_anim():
    elems = [
        stext(380, 24, 'Scenario: what happened on the LMS today?', 'blue', 15, bold=True),
        _codebox(20, 50, 720, 50, ['10.0.0.5 - - [13/Oct/2026:09:01:12 +0530] "GET /lms/login HTTP/1.1" 200 512',
                                    '$1 = IP · $4 = [time · $7 = path · $9 = status · $10 = bytes'], 'gray', step=1),
        sbox(20, 120, 170, 60, 'top IPs', "awk '{print $1}' | sort\n| uniq -c | sort -rn", 'blue', step=2, size=11),
        sbox(205, 120, 170, 60, 'errors', "awk '$9 >= 400'", 'red', step=3, size=11),
        sbox(390, 120, 170, 60, 'per hour', "substr($4, 14, 2)", 'green', step=4, size=11),
        sbox(575, 120, 165, 60, 'bytes per path', 'sum[$7] += $10', 'purple', step=4, size=11),
        stext(380, 215, 'one log, four questions, no database: fields + awk + sort | uniq -c', 'amber', 12, step=5, focus=5),
        stext(380, 240, 'same logic scales to GBs (streaming) · beyond that: load into Hive/Spark', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 258, *elems), [
        'An Apache-style access log: space-separated fields for IP, time, request, status and size.',
        'Top clients: extract field 1, count, rank.',
        'Problems: filter status codes 400 and above.',
        'Traffic per hour and bytes per path: substrings and associative arrays.',
        'Every answer is a short pipeline over the raw log.',
    ])


def backup_anim():
    elems = [
        stext(380, 24, 'Scenario: daily backup with rotation', 'blue', 15, bold=True),
        _row([('check', 'source exists,\nspace free', 'gray', 1), ('archive', 'tar -czf\nname_DATE.tar.gz', 'blue', 2), ('verify', 'tar -tzf ok?', 'green', 3),
              ('rotate', 'find -mtime +7\n-delete', 'amber', 4), ('log', 'timestamped\nexit code', 'purple', 5)], 60, w=130, gap=17, h=66, size=12),
        stext(380, 170, 'backup_2026-10-13.tar.gz · backup_2026-10-12.tar.gz · … keep 7 days', 'blue', 12, step=2),
        stext(380, 200, '0 1 * * * /opt/backup/backup.sh >> /var/log/backup.log 2>&1', 'amber', 12, step=5, bold=True),
        stext(380, 228, 'a backup is only real if you have tested restoring it', 'red', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 245, *elems), [
        'Fail early if the source is missing or the target disk is full.',
        'Create a dated, compressed archive.',
        'Verify the archive can be read before trusting it.',
        'Delete archives older than the retention period.',
        'Log every run with timestamps and exit codes, and schedule it with cron. Test restores regularly.',
    ])


def diskfull_anim():
    elems = [
        stext(380, 24, 'Scenario: "No space left on device"', 'blue', 15, bold=True),
        _row([('df -h', 'which FS is full?', 'red', 1), ('du | sort -rh', 'which folder?', 'amber', 2), ('find -size +100M', 'which files?', 'blue', 3),
              ('lsof +L1', 'deleted but open?', 'purple', 4), ('df -i', 'out of inodes?', 'gray', 4)], 60, w=130, gap=17, h=60, size=12),
        sbox(20, 150, 350, 60, 'quick relief', 'compress/delete old logs · truncate open logs (: > file)\nclean package caches · move data', 'green', step=5, size=12),
        sbox(390, 150, 350, 60, 'prevent', 'logrotate · retention cron · alerts at 80 %\nseparate /var and data disks', 'cyan', step=5, size=12),
    ]
    return anim(canvas(760, 230, *elems), [
        'Confirm which filesystem is full.',
        'Drill down by directory size.',
        'Find individual large files.',
        'Check for space held by deleted-but-open files, and for inode exhaustion.',
        'Free space safely, then prevent a repeat with rotation, retention and monitoring.',
    ])


def csvjoin_anim():
    elems = [
        stext(380, 24, 'Scenario: a "SQL query" on CSV files with shell tools', 'blue', 15, bold=True),
        stable(20, 55, ['roll', 'course'], [['2401', 'PG-DBDA'], ['2403', 'PG-DAI'], ['2404', 'PG-DAC']], [60, 80], step=1, title='students.csv', title_color='blue'),
        stable(190, 55, ['roll', 'marks'], [['2401', '82'], ['2401', '61'], ['2403', '84']], [60, 60], step=1, title='marks.csv', title_color='purple'),
        sbox(340, 55, 400, 60, "awk -F, 'NR==FNR {c[$1]=$3; next} …'", 'first file → lookup table, second → join + group', 'green', step=2, size=12),
        stable(440, 135, ['course', 'avg', 'n'], [['PG-DAC', '58.0', '1'], ['PG-DAI', '78.0', '2'], ['PG-DBDA', '79.4', '5']], [90, 60, 40], step=3, title='result', title_color='green'),
        stext(200, 185, 'or: sort both files + join -t,', 'amber', 12, step=4),
        stext(200, 210, 'skip non-numeric marks ("AB")', 'red', 12, step=4),
        stext(380, 255, 'same answer as SELECT course, AVG(marks) … JOIN … GROUP BY course', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 272, *elems), [
        'Two CSV files share the roll number.',
        'awk reads the first file into an array (NR==FNR is true only while reading the first file), then looks up each mark\'s course.',
        'Sums and counts per course give the averages.',
        'Alternatives: join on sorted files; always handle bad values.',
        'The result matches the SQL GROUP BY a database would give.',
    ])


def monitor_anim():
    elems = [
        stext(380, 24, 'Scenario: a health-check script for cron', 'blue', 15, bold=True),
        sbox(20, 55, 170, 60, 'disk', 'df usage > 80 %?', 'red', step=1, size=12),
        sbox(205, 55, 170, 60, 'process', 'pgrep -f kafka?', 'blue', step=2, size=12),
        sbox(390, 55, 170, 60, 'port', 'service answering?', 'green', step=2, size=12),
        sbox(575, 55, 165, 60, 'log', 'new ERRORs?', 'amber', step=3, size=12),
        sarrow(380, 115, 380, 145, 'gray', step=4),
        sbox(200, 148, 360, 56, 'collect problems → one alert', 'mail / Slack webhook · exit 1 if any', 'purple', step=4, size=12),
        stext(380, 235, 'idempotent, quiet when healthy, lock against overlap (flock), logs every run', 'cyan', 12, step=5),
        stext(380, 260, 'beyond scripts: Prometheus + Grafana, Nagios, CloudWatch', 'gray', 12, step=5),
    ]
    return anim(canvas(760, 275, *elems), [
        'Check disk usage against a threshold.',
        'Check that critical processes run and their ports answer.',
        'Scan logs for new errors since the last run.',
        'Gather all problems into a single alert and a non-zero exit code.',
        'Good monitoring scripts are quiet when healthy and safe to run repeatedly; larger setups use monitoring systems.',
    ])
