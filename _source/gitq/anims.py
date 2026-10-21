from build import *
from build import _t


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


def _dot(x, y, color, step=None, r=5, focus=None):
    c = PALETTE.get(color, color)
    a = f' data-step="{step}"' if step else ''
    f = f' data-focus="{focus}"' if focus else ''
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"{a}{f}/>'


def _axes(x, y, w, h, xl='', yl='', step=None):
    return (sarrow(x, y + h, x + w, y + h, 'gray', step=step) + sarrow(x, y + h, x, y, 'gray', step=step)
            + stext(x + w / 2, y + h + 18, xl, 'gray', 11, step=step) + stext(x - 12, y - 6, yl, 'gray', 11, anchor='start', step=step))


def _path(fn, x0, x1, X, Y, W, H, ymax, n=80):
    """Polyline of fn over [x0, x1] mapped into the box (X, Y, W, H); ymax maps to the top."""
    pts = []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        pts.append(f'{X + W * k / n:.1f} {Y + H - H * min(fn(x), ymax) / ymax:.1f}')
    return 'M ' + ' L '.join(pts)


def _curve(fn, x0, x1, X, Y, W, H, ymax, color='blue', step=None, width=2.5, fill=False):
    d = _path(fn, x0, x1, X, Y, W, H, ymax)
    c = PALETTE.get(color, color)
    a = f' data-step="{step}"' if step else ''
    if fill:
        return f'<path d="{d} L {X + W} {Y + H} L {X} {Y + H} Z" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="{width}"{a}/>'
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{width}"{a}/>'


def _area(fn, x0, x1, a0, a1, X, Y, W, H, ymax, color='amber', step=None, n=60):
    """Shaded area under fn between a0 and a1 (data units)."""
    sx = lambda x: X + W * (x - x0) / (x1 - x0)
    pts = [f'{sx(a0):.1f} {Y + H}']
    for k in range(n + 1):
        x = a0 + (a1 - a0) * k / n
        pts.append(f'{sx(x):.1f} {Y + H - H * min(fn(x), ymax) / ymax:.1f}')
    pts.append(f'{sx(a1):.1f} {Y + H}')
    c = PALETTE.get(color, color)
    st = f' data-step="{step}"' if step else ''
    return f'<path d="M {" L ".join(pts)} Z" fill="{c}" fill-opacity="0.45" stroke="none"{st}/>'


def _bars(vals, X, Y, W, H, vmax, color='blue', step=None, gap=3, labels=None, lsize=10):
    out = []
    bw = W / len(vals)
    c = PALETTE.get(color, color)
    a = f' data-step="{step}"' if step else ''
    for i, v in enumerate(vals):
        h = H * v / vmax
        out.append(f'<rect x="{X + i * bw + gap / 2:.1f}" y="{Y + H - h:.1f}" width="{bw - gap:.1f}" height="{h:.1f}" fill="{c}"{a}/>')
        if labels:
            out.append(stext(X + i * bw + bw / 2, Y + H + 14, labels[i], 'gray', lsize, step=step))
    return ''.join(out)


def _npdf(m=0, s=1):
    import math
    return lambda x: math.exp(-((x - m) / s) ** 2 / 2) / (s * math.sqrt(2 * math.pi))




# ============================================================ git drawing helpers
def _c(x, y, label, col='blue', step=None, r=13, sub=None, focus=None):
    """A commit circle with a short label (hash or name) and optional caption below."""
    c = PALETTE.get(col, col)
    a = f' data-step="{step}"' if step else ''
    f = f' data-focus="{focus}"' if focus else ''
    out = f'<g{a}{f}><circle cx="{x}" cy="{y}" r="{r}" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="2.5"/>' \
          f'<text x="{x}" y="{y + 4}" font-size="10" fill="#e2e8f0" text-anchor="middle">{_t(label)}</text></g>'
    if sub:
        out += stext(x, y + r + 14, sub, 'gray', 9, step=step)
    return out


def _e(x1, y1, x2, y2, step=None, col='#64748b', r=13, dashed=False):
    """Edge from a child commit (x2) back to its parent (x1), drawn between circle edges."""
    import math
    d = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    a = f' data-step="{step}"' if step else ''
    dash = ' stroke-dasharray="5,4"' if dashed else ''
    return (f'<line x1="{x1 + ux * r:.1f}" y1="{y1 + uy * r:.1f}" x2="{x2 - ux * r:.1f}" y2="{y2 - uy * r:.1f}" '
            f'stroke="{PALETTE.get(col, col)}" stroke-width="2.5"{dash}{a}/>')


def _ref(x, y, name, col='green', step=None, w=None, focus=None):
    """A branch/tag/HEAD label box."""
    w = w or max(44, 7.2 * len(name) + 14)
    return sbox(x - w / 2, y - 11, w, 22, name, '', col, step=step, size=10, focus=focus)


def _ptr(x1, y1, x2, y2, step=None, col='gray'):
    return sarrow(x1, y1, x2, y2, col, step=step)


def _stub(t='todo'):
    return anim(canvas(760, 60, stext(380, 30, t, 'blue', 14, step=1)), [t])


def _hide(x, y, w, h, step):
    """Covers an earlier element from `step` on (elements cannot disappear, so they are dimmed)."""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1e293b" fill-opacity="0.82" data-step="{step}"/>'


def _chain(pts, step=None, col='#64748b', r=13):
    return ''.join(_e(x1, y1, x2, y2, step, col, r) for (x1, y1), (x2, y2) in zip(pts, pts[1:]))


def _title(t):
    return stext(380, 24, t, 'blue', 15, bold=True)


# ============================================================ s01 foundations
def vc_anim():
    dev = lambda x, y, name, st, full: (sbox(x, y, 104, 58, name, 'full history' if full else 'working copy', 'green' if full else 'gray', step=st, size=12))
    e = [_title('Centralized vs distributed version control'),
         stext(190, 54, 'Centralized (SVN)', 'amber', 13, step=1, bold=True),
         sbox(125, 66, 130, 50, 'Central server', 'the only history', 'amber', step=1, size=12)]
    for i, x in enumerate([18, 138, 258]):
        e.append(dev(x, 168, ['Asha', 'Ravi', 'Neha'][i], 1, False))
        e.append(sarrow(x + 52, 166, 190 + (i - 1) * 30, 118, 'amber', step=1))
    e += [stext(190, 250, 'commit, log, diff → need the server', 'amber', 11, step=1),
          stext(190, 268, 'server down = nobody can commit', 'red', 11, step=1),
          stext(570, 54, 'Distributed (Git)', 'green', 13, step=2, bold=True),
          sbox(505, 66, 130, 50, 'GitHub', 'just another clone', 'purple', step=2, size=12)]
    for i, x in enumerate([398, 518, 638]):
        e.append(dev(x, 168, ['Asha', 'Ravi', 'Neha'][i], 2, True))
        e.append(sarrow(x + 52, 166, 570 + (i - 1) * 30, 118, 'green', step=2))
    e += [stext(570, 250, 'every clone has every commit', 'green', 11, step=2),
          stext(570, 268, 'push / pull only to share', 'green', 11, step=2),
          _codebox(40, 292, 330, 92, ['$ git init lab-manual', '  → lab-manual/.git  (the repository)', '$ git commit -m "Start the lab manual"',
                                      '[main (root-commit) 1408405]', '$ du -sh .git  →  176K'], 'blue', step=3),
          _c(440, 338, '1408405', 'green', step=3, r=26),
          _ref(440, 384, 'main', 'green', step=3),
          _codebox(520, 292, 220, 92, ['offline:  commit  log  diff', '          branch  merge', 'online:   push  pull  fetch', '          clone'], 'green', step=4)]
    return anim(canvas(760, 400, *e), [
        'In centralized systems the history lives only on the server; developers hold working copies and need the server for almost everything.',
        'In Git every clone is a complete repository. GitHub is a shared copy the team agrees on, not a different kind of system.',
        'git init creates the .git folder — that folder is the repository. The first commit gets a hash (1408405 in our run) and the main branch points to it.',
        'Because history is local, everyday commands are fast and work offline; only sharing needs the network.',
    ])


def areas_anim():
    X = [20, 270, 520]
    e = [_title('Working directory → staging area → repository')]
    for x, (t, s, c) in zip(X, [('Working directory', 'files you edit', 'gray'), ('Staging area (index)', 'next commit, being prepared', 'amber'),
                                 ('Repository (.git)', 'committed snapshots', 'green')]):
        e.append(sbox(x, 44, 220, 260, t, s, c, top=True, size=13, fill_opacity=0.1))
    e += [sarrow(242, 76, 268, 76, 'amber'), stext(255, 38, 'add', 'amber', 11),
          sarrow(492, 76, 518, 76, 'green'), stext(505, 38, 'commit', 'green', 11)]
    f = lambda x, y, name, tag, col, st, focus=None: (sbox(x + 10, y, 200, 30, name + '   ' + tag, '', col, step=st, size=11, focus=focus))
    e += [f(20, 96, 'hive_lab.sql', '??', 'gray', 1), f(20, 134, 'spark_lab.py', '??', 'gray', 1),
          f(270, 96, 'hive_lab.sql', 'new file', 'amber', 2, '2'), _hide(30, 96, 200, 30, 2),
          _c(570, 112, 'c1', 'green', step=3), stext(660, 116, 'Add Hive lab query', 'green', 10, step=3),
          _hide(280, 96, 200, 30, 3),
          f(20, 172, 'hive_lab.sql', ' M', 'red', 4, '4'),
          f(270, 134, 'hive_lab.sql', 'M', 'amber', 5), f(270, 172, 'spark_lab.py', 'A', 'amber', 5),
          _hide(30, 134, 200, 30, 5), _hide(30, 172, 200, 30, 5),
          _c(570, 170, '3647d34', 'green', step=6, r=24), _e(570, 112, 570, 170, step=6, r=24),
          stext(660, 204, 'Fix Hive comment', 'green', 10, step=6), stext(660, 218, 'and add Spark lab', 'green', 10, step=6),
          _hide(280, 134, 200, 30, 6), _hide(280, 172, 200, 30, 6),
          stext(380, 330, 'git status → nothing to commit, working tree clean', 'green', 12, step=6, bold=True),
          stext(380, 352, 'status columns: left = staged, right = not staged;  ?? = untracked', 'cyan', 11, step=4)]
    return anim(canvas(760, 368, *e), [
        'Two new files exist only in the working directory: git status shows them as ?? (untracked).',
        'git add hive_lab.sql copies that file\'s current content into the staging area — the draft of the next commit.',
        'git commit stores the staged snapshot permanently in the repository. spark_lab.py was not staged, so it is not in the commit.',
        'Editing hive_lab.sql again makes the working copy differ from the last commit: " M" (modified, not staged).',
        'git add with both files stages the modification (M) and the new file (A).',
        'The second commit (3647d34) contains both. Working directory, index and HEAD now match: the tree is clean.',
    ])


def config_anim():
    e = [_title('Three configuration levels — the most specific wins'),
         sbox(30, 50, 300, 62, 'system  (--system)', '/etc/gitconfig  ·  every user', 'gray', step=1, size=12),
         sbox(30, 128, 300, 78, 'global  (--global)', '~/.gitconfig  ·  you, all repos\nuser.email = asha@cdac.example', 'blue', step=1, size=12),
         sbox(30, 222, 300, 62, 'local  (default)', '.git/config  ·  this repo only', 'green', step=1, size=12),
         stext(350, 90, 'lowest priority', 'gray', 11, 'start', step=1), stext(350, 260, 'highest priority', 'green', 11, 'start', step=1),
         sarrow(458, 100, 458, 246, 'gray', step=1),
         _codebox(480, 46, 260, 84, ['[user]', '  name  = Asha Patil', '  email = asha@cdac.example', '[alias] lg = log --oneline …'], 'blue', step=2),
         _codebox(480, 150, 260, 50, ['# in course/.git/config', 'user.email = asha.patil@cdac.in'], 'green', step=3),
         sbox(140, 310, 480, 54, 'commit author:  Asha Patil <asha.patil@cdac.in>', 'name from global, email overridden locally', 'amber', step=4, size=12, focus='4'),
         stext(380, 392, 'git config --list --show-origin  shows which file each value came from', 'cyan', 12, step=5),
         stext(380, 412, 'git lg  → alias for log --oneline --graph --all', 'purple', 12, step=5)]
    return anim(canvas(760, 426, *e), [
        'Git reads three files in order: system, global, local. A value set at a more specific level overrides the same key above it.',
        'The global file holds your identity and aliases (here user.name Asha Patil, email asha@cdac.example and the lg alias).',
        'Inside the course repository a local user.email is set — only this repository uses it.',
        'The commit therefore records the global name with the local email: Asha Patil <asha.patil@cdac.in>.',
        'Use --show-origin to debug which file a value comes from; aliases work in every repository.',
    ])


def log_anim():
    xs = [110, 270, 430, 590]
    hs = ['940d2cb', '8346568', '536a22a', '0fb78d4']
    msg = ['pass mark 40', 'Document rules', 'Raise pass mark to 50', 'Add grade function']
    e = [_title('Navigating history: hashes, HEAD~n and searches')]
    for i, (x, h, m) in enumerate(zip(xs, hs, msg)):
        e.append(_c(x, 110, h, 'blue', step=1, r=30, focus='3' if i == 2 else None))
        e.append(stext(x, 160, m, 'gray', 10, step=1))
    e.append(_chain([(x, 110) for x in xs], step=1, r=30))
    e += [_ref(690, 110, 'HEAD → main', 'green', step=1),
          sarrow(642, 110, 622, 110, 'green', step=1)]
    for i, lab in enumerate(['HEAD~3', 'HEAD~2', 'HEAD~1', 'HEAD']):
        e.append(stext(xs[i], 66, lab, 'amber', 11, step=2, bold=True))
    e += [_codebox(40, 190, 330, 54, ['$ git log -S "PASS_MARK = 50" --oneline', '536a22a Raise pass mark to 50'], 'purple', step=3),
          stext(205, 262, 'pickaxe: commits that added/removed the text', 'purple', 11, step=3),
          _codebox(390, 190, 330, 54, ['$ git show HEAD~2:grade.py', 'PASS_MARK = 40'], 'amber', step=4),
          stext(555, 262, 'a file as it was in an older commit', 'amber', 11, step=4),
          _codebox(40, 284, 680, 54, ["$ git log --format='%h | %an | %ad | %s' --date=format:'%d %b %H:%M'",
                                      '0fb78d4 | Asha Patil | 14 Oct 09:07 | Add grade function'], 'cyan', step=5)]
    return anim(canvas(760, 352, *e), [
        'Four commits, newest on the right. Each points back to its parent; main (and HEAD) point to the newest, 0fb78d4.',
        'Relative names count back from HEAD: HEAD~1 is the parent, HEAD~2 the grandparent, and so on.',
        'git log -S finds the commit whose diff added or removed a string — here the change to a pass mark of 50.',
        'git show <commit>:<path> prints a file as it was then, without checking anything out.',
        '--format and --date build one-line reports with exactly the fields you need.',
    ])


def objects_anim():
    e = [_title('Inside .git/objects: commit → tree → blobs'),
         sbox(300, 44, 160, 48, 'commit', 'tree b7d9fc6 · author · msg', 'purple', step=1, size=12),
         sbox(300, 128, 160, 48, 'tree b7d9fc6', 'root folder', 'blue', step=2, size=12),
         sarrow(380, 92, 380, 126, 'gray', step=2),
         sbox(110, 214, 170, 48, 'tree 5029819', 'lab1/  and  lab2/', 'blue', step=3, size=12, focus='3'),
         sbox(480, 214, 170, 48, 'blob a5aa839', '"student_id,score"', 'green', step=2, size=12, focus='3'),
         sarrow(330, 176, 170, 212, 'gray', step=3), stext(230, 186, 'lab1', 'gray', 10, step=3),
         sarrow(370, 176, 250, 212, 'gray', step=3), stext(326, 206, 'lab2', 'gray', 10, step=3),
         sarrow(420, 176, 540, 212, 'gray', step=2), stext(500, 188, 'marks.csv', 'gray', 10, step=2),
         sarrow(280, 238, 478, 238, 'gray', step=3), stext(380, 230, 'marks.csv', 'gray', 10, step=3),
         stext(380, 290, '3 copies of marks.csv, 2 identical folders → only 4 objects', 'amber', 12, step=3, bold=True),
         sbox(110, 314, 170, 48, 'tree b00a3eb', 'new lab2/', 'red', step=4, size=12),
         sbox(480, 314, 170, 48, 'new blob', '"student_id,score,grade"', 'red', step=4, size=12),
         sarrow(280, 338, 478, 338, 'red', step=4),
         stext(380, 384, 'after editing lab2/marks.csv: lab1 tree and root blob are reused, only lab2 changes', 'red', 12, step=4),
         stext(380, 406, 'object id = SHA-1 of content  →  same content, same id (git hash-object marks.csv → a5aa839…)', 'cyan', 11, step=5)]
    return anim(canvas(760, 420, *e), [
        'A commit object stores a pointer to one tree, the author, committer, time and message.',
        'The root tree lists names and modes and points to blobs (file contents) and other trees.',
        'Identical content is stored once: marks.csv is one blob, and lab1 and lab2 are the same tree 5029819. git count-objects reports 4 objects.',
        'Changing one file creates a new blob and new trees only along its path; everything else is shared with the previous commit.',
        'Every object is named by the hash of its content — that is why Git can detect corruption and deduplicate automatically.',
    ])


# ============================================================ s02 everyday
def diff_anim():
    X = [30, 280, 530]
    e = [_title('Which two versions does each git diff compare?')]
    for x, (t, c) in zip(X, [('Working directory', 'gray'), ('Staging area', 'amber'), ('HEAD (last commit)', 'green')]):
        e.append(sbox(x, 44, 200, 34, t, '', c, size=12))
    cell = lambda x, y, txt, col, st, focus=None: sbox(x, y, 200, 30, txt, '', col, step=st, size=11, focus=focus, fill_opacity=0.12)
    e += [cell(30, 90, 'm >= 40', 'gray', 1), cell(280, 90, 'm >= 40', 'gray', 1), cell(530, 90, 'm >= 40', 'gray', 1),
          stext(255, 146, 'all three equal → git status clean', 'gray', 11, step=1),
          cell(30, 90, 'm >= 50', 'red', 2, '2'),
          sarrow(130, 170, 130, 124, 'red', step=2), sarrow(380, 170, 380, 124, 'red', step=2),
          '<path d="M130 170 L380 170" stroke="#ef4444" stroke-width="2" fill="none" data-step="2"/>',
          stext(255, 186, 'git diff  (working dir vs index)', 'red', 12, step=2, bold=True),
          cell(280, 90, 'm >= 50', 'amber', 3, '3'),
          sarrow(380, 214, 380, 124, 'amber', step=3), sarrow(630, 214, 630, 124, 'amber', step=3),
          '<path d="M380 214 L630 214" stroke="#f59e0b" stroke-width="2" fill="none" data-step="3"/>',
          stext(505, 232, 'git diff --staged  (index vs HEAD)', 'amber', 12, step=3, bold=True),
          stext(255, 206, 'now empty — WD = index', 'gray', 10, step=3),
          cell(30, 90, 'm >= 50 + print("debug")', 'purple', 4, '4'),
          sarrow(110, 262, 110, 124, 'purple', step=4), sarrow(650, 262, 650, 124, 'purple', step=4),
          '<path d="M110 262 L650 262" stroke="#8b5cf6" stroke-width="2" fill="none" data-step="4"/>',
          stext(380, 280, 'git diff HEAD  (working dir vs last commit)', 'purple', 12, step=4, bold=True),
          _codebox(60, 298, 300, 54, ['return "P" if m >= [-40-]{+50+} else "F"', '{+print("debug")+}'], 'purple', step=4, size=10),
          stext(210, 370, '--word-diff marks changed words only', 'purple', 10, step=4),
          _codebox(400, 298, 320, 54, ['$ git diff HEAD~1 HEAD --name-only', 'grade.py'], 'cyan', step=5),
          stext(560, 370, 'any two commits; --stat / --name-only summarize', 'cyan', 10, step=5)]
    return anim(canvas(760, 384, *e), [
        'grade.py has the same content in the working directory, the index and the last commit.',
        'After editing, plain git diff shows working directory vs index: the change that is not yet staged.',
        'After git add, git diff is empty; git diff --staged shows what the next commit will contain.',
        'Adding a debug line makes the working copy differ from both; git diff HEAD shows everything since the last commit, here as a word diff.',
        'git diff A B compares any two commits; summary options keep the output short.',
    ])


def ignore_anim():
    files = [('data/raw.csv', 'data/', 2), ('venv/pyvenv.cfg', 'venv/', 2), ('__pycache__/x.pyc', '__pycache__/', 2), ('logs/app.log', '*.log', 2),
             ('logs/keep.log', '!logs/keep.log', 3), ('.env', '.env', 2), ('analysis.ipynb', '', 0)]
    e = [_title('.gitignore patterns decide what git status shows'),
         _codebox(30, 44, 190, 124, ['data/', 'venv/', '__pycache__/', '*.log', '!logs/keep.log', '.env'], 'amber', step=1),
         stext(125, 186, '.gitignore', 'amber', 12, step=1, bold=True)]
    for i, (f, rule, st) in enumerate(files):
        y = 58 + i * 34
        e.append(sbox(250, y - 14, 170, 28, f, '', 'gray', size=11, step=1))
        if st == 2:
            e += [_hide(250, y - 14, 170, 28, 2), stext(440, y + 4, 'ignored  ←  ' + rule, 'red', 11, 'start', step=2)]
        elif st == 3:
            e += [stext(440, y + 4, 'tracked again  ←  ' + rule, 'green', 11, 'start', step=3, bold=True)]
        else:
            e += [stext(440, y + 4, 'untracked → will be added', 'green', 11, 'start', step=2)]
    e += [_codebox(30, 296, 330, 54, ['$ git check-ignore -v logs/app.log', '.gitignore:4:*.log    logs/app.log'], 'cyan', step=4),
          stext(195, 368, 'which file, line and pattern ignored it', 'cyan', 10, step=4),
          _codebox(390, 296, 340, 70, ['config.ini already committed → ignoring has no effect', '$ git rm --cached config.ini', '→ untracked, still on disk (ls shows it)'], 'red', step=5)]
    return anim(canvas(760, 384, *e), [
        'The project contains data, a virtualenv, caches, logs, secrets and a notebook. .gitignore lists patterns, one per line.',
        'A trailing / matches folders, * matches any name. Matching untracked files disappear from git status.',
        'A ! pattern re-includes a file excluded earlier (the parent folder itself must not be ignored).',
        'git check-ignore -v explains which rule matched — the quickest way to debug a pattern.',
        '.gitignore only affects untracked files. For a file already committed, remove it from the index with git rm --cached and commit; it stays on disk.',
    ])


def undo_anim():
    xs, y = [70, 190, 310, 430], 92
    e = [_title('Undo tools: what each one changes'),
         _c(xs[0], y, '2a83fd1', 'blue', r=24, sub='line 1'), _c(xs[1], y, 'bd5d4ee', 'blue', r=24, sub='line 2'),
         _c(xs[2], y, '6aebf25', 'blue', r=24, sub='line 3'), _chain([(x, y) for x in xs[:3]], r=24),
         _ref(xs[2], 46, 'main', 'green'),
         _c(xs[3], y, 'add63d0', 'amber', step=1, r=24, sub='Revert line 3'), _e(xs[2], y, xs[3], y, step=1, r=24),
         _ref(xs[3], 46, 'main', 'green', step=1), _hide(xs[2] - 26, 34, 52, 24, 1),
         stext(600, 80, 'git revert HEAD', 'amber', 12, step=1, bold=True), stext(600, 98, 'new commit that undoes', 'amber', 11, step=1),
         stext(600, 114, 'safe on pushed history', 'amber', 11, step=1),
         _hide(xs[3] - 26, 34, 52, 24, 2), _ref(xs[2], 46, 'main', 'green', step=2), _hide(xs[3] - 30, 62, 60, 66, 2),
         stext(600, 140, 'reset --soft HEAD~1 → change staged', 'purple', 11, step=2),
         _hide(xs[2] - 26, 34, 52, 24, 3), _ref(xs[1], 46, 'main', 'green', step=3), _hide(xs[2] - 30, 62, 60, 66, 3),
         stext(600, 158, 'reset HEAD~1 → main at bd5d4ee', 'red', 11, step=3)]
    rows = [['restore <file>', '—', '—', '✔ from index'], ['restore --staged <file>', '—', '✔ from HEAD', '—'], ['reset --soft <c>', '✔', '—', '—'],
            ['reset [--mixed] <c>', '✔', '✔', '—'], ['reset --hard <c>', '✔', '✔', '✔ (lost!)'], ['revert <c>', 'new commit', '✔', '✔']]
    e += [stable(60, 196, ['command', 'branch', 'index', 'working dir'], rows, [220, 130, 130, 160], h=26, step=4, title='what is overwritten',
                 title_color='purple', focus_rows={4: '5'}),
          stext(380, 396, 'restore and reset --hard discard uncommitted work for good; revert never rewrites history', 'red', 12, step=5, bold=True)]
    return anim(canvas(760, 410, *e), [
        'git revert HEAD adds commit add63d0 that removes line 3. History only grows, so it is the right tool after pushing.',
        'git reset --soft HEAD~1 moves main back one commit; the revert\'s change stays staged (status "M ").',
        'git reset HEAD~1 (mixed, the default) moves main again and unstages; main now points at bd5d4ee.',
        'Summary: restore works on files; reset moves the branch and optionally the index and working directory; revert adds a new commit.',
        'Only --hard and restore throw away uncommitted work — check git status and git diff first.',
    ])


def amend_anim():
    e = [_title('--amend replaces the last commit with a new one'),
         _c(170, 110, '9ae9af5', 'red', step=1, r=30), stext(170, 160, '"Add grde fucntion"', 'red', 11, step=1),
         stext(170, 176, 'grade.py', 'gray', 10, step=1),
         _ref(170, 56, 'main', 'green', step=1),
         sbox(330, 92, 150, 36, 'staged: test_grade.py', '', 'amber', step=2, size=11),
         _c(590, 110, '601d989', 'green', step=3, r=30), stext(590, 160, '"Add grade function with tests"', 'green', 11, step=3),
         stext(590, 176, 'grade.py + test_grade.py', 'gray', 10, step=3),
         _hide(140, 44, 60, 24, 3), _ref(590, 56, 'main', 'green', step=3),
         sarrow(482, 110, 556, 110, 'amber', step=3), stext(519, 100, 'amend', 'amber', 10, step=3),
         _hide(80, 76, 180, 110, 4),
         stext(170, 210, 'old commit still exists (reflog)', 'gray', 11, step=4),
         _codebox(40, 230, 680, 54, ['601d989 HEAD@{0}: commit (amend): Add grade function with tests', '9ae9af5 HEAD@{1}: commit (initial): Add grde fucntion'], 'cyan', step=4),
         sbox(140, 304, 480, 54, 'Amend only commits that are not pushed', 'others may already have 9ae9af5; pushing 601d989 would need a force push', 'red', step=5, size=12)]
    return anim(canvas(760, 372, *e), [
        'The first commit has a typo in the message and is missing the test file.',
        'Stage the forgotten file.',
        'git commit --amend builds a brand-new commit (601d989) from the index with the new message; main moves to it. Commits are immutable, so it cannot be edited in place.',
        'The replaced commit 9ae9af5 is no longer on any branch but is still in the reflog for a while.',
        'Because the hash changes, amending a commit that others already have rewrites shared history.',
    ])


def stash_anim():
    e = [_title('git stash: a shelf for unfinished work'),
         sbox(30, 46, 240, 120, 'feature/report — working dir', '', 'blue', top=True, size=12, fill_opacity=0.1, step=1),
         sbox(50, 84, 200, 28, 'report.html   M', '', 'red', step=1, size=11), sbox(50, 120, 200, 28, 'notes.txt   ??', '', 'gray', step=1, size=11),
         sbox(470, 46, 260, 120, 'stash stack', '', 'purple', top=True, size=12, fill_opacity=0.1),
         sbox(490, 84, 220, 46, 'stash@{0}', 'report: chart section  (-u: incl. notes.txt)', 'purple', step=2, size=12, focus='4'),
         sarrow(272, 106, 466, 106, 'purple', step=2), stext(370, 96, 'stash push -u -m', 'purple', 11, step=2),
         _hide(40, 76, 220, 80, 2), stext(150, 160, 'clean', 'green', 11, step=2, bold=True),
         sbox(30, 200, 700, 60, '', '', 'gray', fill_opacity=0.06, step=3),
         stext(380, 222, 'git switch main → fix heading → commit → git switch feature/report', 'amber', 12, step=3, bold=True),
         stext(380, 244, 'the urgent fix happens with a clean tree; nothing half-done gets committed', 'gray', 11, step=3),
         _codebox(30, 278, 330, 54, ['$ git stash list', 'stash@{0}: On feature/report: report: chart section'], 'cyan', step=4, size=10),
         stext(195, 350, 'stash show -p --include-untracked to inspect', 'cyan', 10, step=4),
         sarrow(466, 150, 272, 170, 'green', step=5), stext(370, 182, 'stash pop', 'green', 11, step=5, bold=True),
         _hide(480, 76, 240, 60, 5), _hide(40, 150, 220, 16, 5),
         sbox(50, 84, 200, 28, 'report.html   M', '', 'red', step=5, size=11), sbox(50, 120, 200, 28, 'notes.txt   ??', '', 'gray', step=5, size=11),
         _codebox(390, 278, 340, 54, [' M report.html', '?? notes.txt   (Dropped refs/stash@{0})'], 'green', step=5, size=10)]
    return anim(canvas(760, 364, *e), [
        'You are midway through a change: one modified file and one new untracked file.',
        'git stash push -u -m saves both (-u includes untracked files) on a stack and resets the working directory to HEAD.',
        'With a clean tree you can switch branches, make the urgent fix and come back.',
        'git stash list and git stash show identify each entry; a message makes them easy to tell apart.',
        'git stash pop re-applies the newest entry and drops it from the stack; apply would keep it.',
    ])


# ============================================================ s03 branching
def branch_anim():
    R = 26
    e = [_title('A branch is a movable pointer; HEAD says which one you are on'),
         _c(160, 150, 'fe51df2', 'blue', r=R, sub='Initial portal'),
         _ref(160, 96, 'main', 'green'), _ref(160, 56, 'HEAD', 'amber', step=None),
         sarrow(160, 67, 160, 84, 'amber'),
         _ref(300, 96, 'feature/export', 'purple', step=1),
         _hide(130, 44, 60, 24, 1), _ref(300, 56, 'HEAD', 'amber', step=1), sarrow(300, 67, 300, 84, 'amber', step=1),
         _c(440, 150, '5137d40', 'purple', step=2, r=R, sub='Add attendance export'), _e(160, 150, 440, 150, step=2, r=R),
         _hide(240, 44, 120, 64, 2), _ref(440, 96, 'feature/export', 'purple', step=2), _ref(440, 56, 'HEAD', 'amber', step=2),
         sarrow(440, 67, 440, 84, 'amber', step=2),
         _codebox(520, 50, 220, 104, ['.git/HEAD', ' ref: refs/heads/feature/export', '', '.git/refs/heads/feature/export', ' 5137d4079fb836d7…'], 'cyan', step=3, size=10),
         _hide(410, 44, 60, 24, 4), _ref(160, 56, 'HEAD', 'amber', step=4), sarrow(160, 67, 160, 84, 'amber', step=4),
         stext(160, 210, 'switch main → files back to app.txt only', 'amber', 11, step=4),
         _codebox(40, 240, 680, 70, ['$ git branch -d feature/export', "error: the branch 'feature/export' is not fully merged.",
                                     '$ git branch -D feature/export   →  Deleted branch feature/export (was 5137d40).'], 'red', step=5, size=11),
         stext(380, 334, '-d protects unmerged work; -D forces. The commit stays in the reflog for a while.', 'red', 12, step=5)]
    return anim(canvas(760, 350, *e), [
        'git switch -c feature/export creates a new pointer at the current commit and moves HEAD to it. Nothing is copied.',
        'A new commit moves only the branch HEAD is on; main stays at fe51df2.',
        'Under the hood: HEAD is a file naming the current branch, and the branch is a file holding one commit hash.',
        'git switch main moves HEAD back and updates the working directory to that commit.',
        'Deleting an unmerged branch needs -D; the branch is only a label, the commit object remains reachable through the reflog.',
    ])


def merge_anim():
    R, y0, y1 = 22, 100, 180
    P = {'603572b': (60, y0), '0c6da16': (160, y0), 'aa94f07': (290, y0), 'a6cc0b6': (290, y1), '8777b17': (420, y0), 'a4fc5da': (530, y1), '7b2a818': (640, y0)}
    e = [_title('Fast-forward, three-way and --no-ff merges'),
         _c(*P['603572b'], '603572b', 'blue', r=R, sub='Initial')]
    e += [_c(*P['0c6da16'], '0c6da16', 'purple', step=1, r=R, sub='Feature A'), _e(*P['603572b'], *P['0c6da16'], step=1, r=R),
          _ref(160, 52, 'main, feature/a', 'green', step=1),
          stext(110, 236, '① fast-forward: main just slides', 'green', 11, step=1, bold=True), stext(110, 252, 'to 0c6da16 — no new commit', 'green', 11, step=1),
          _c(*P['aa94f07'], 'aa94f07', 'blue', step=2, r=R, sub='Update main'), _e(*P['0c6da16'], *P['aa94f07'], step=2, r=R),
          _c(*P['a6cc0b6'], 'a6cc0b6', 'purple', step=2, r=R), stext(262, y1 + 4, 'Feature B', 'gray', 9, 'end', step=2), _e(*P['0c6da16'], *P['a6cc0b6'], step=2, r=R),
          _ref(290, 222, 'feature/b', 'purple', step=2),
          '<circle cx="160" cy="100" r="30" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-dasharray="4,3" data-step="3"/>',
          stext(160, 150, 'merge-base', 'amber', 11, step=3, bold=True),
          _c(*P['8777b17'], '8777b17', 'green', step=4, r=R), _e(*P['aa94f07'], *P['8777b17'], step=4, r=R), _e(*P['a6cc0b6'], *P['8777b17'], step=4, r=R),
          stext(420, 64, 'merge commit', 'green', 10, step=4), stext(420, 78, '2 parents', 'green', 10, step=4),
          stext(380, 252, '② three-way: base + both tips → new commit', 'green', 11, step=4, bold=True),
          _c(*P['a4fc5da'], 'a4fc5da', 'purple', step=5, r=R, sub='Feature C'), _e(*P['8777b17'], *P['a4fc5da'], step=5, r=R),
          _c(*P['7b2a818'], '7b2a818', 'green', step=5, r=R), _e(*P['8777b17'], *P['7b2a818'], step=5, r=R, dashed=True), _e(*P['a4fc5da'], *P['7b2a818'], step=5, r=R),
          _ref(700, 52, 'main', 'green', step=5),
          stext(620, 236, '③ --no-ff: fast-forward was possible,', 'green', 11, step=5, bold=True), stext(620, 252, 'but a merge commit records the feature', 'green', 11, step=5),
          _codebox(40, 274, 680, 54, ["$ git log --merges --format='%h parents: %p  %s'",
                                      "7b2a818 parents: 8777b17 a4fc5da   ·   8777b17 parents: aa94f07 a6cc0b6"], 'cyan', step=6, size=11)]
    return anim(canvas(760, 342, *e), [
        'feature/a is directly ahead of main, so git merge only moves the main pointer forward ("Fast-forward").',
        'Now both branches have new commits: main has aa94f07, feature/b has a6cc0b6. Histories have diverged.',
        'Git finds the merge base — the last common commit, 0c6da16 (git merge-base).',
        'A three-way merge combines base, ours and theirs into a new merge commit 8777b17 with two parents.',
        '--no-ff forces a merge commit even when a fast-forward was possible, keeping the feature visible as a group.',
        'git log --merges shows each merge commit with its two parents.',
    ])


def conflict_anim():
    R = 24
    e = [_title('A conflict: both sides changed the same line'),
         _c(80, 110, 'c01054d', 'blue', r=R, sub='PASS_MARK = 40'),
         _c(240, 70, '69d5363', 'green', step=1, r=R), stext(330, 74, 'main: 45', 'green', 11, 'start', step=1), _e(80, 110, 240, 70, step=1, r=R),
         _c(240, 150, '9ca2fa4', 'purple', step=1, r=R), stext(330, 154, 'raise-pass: 50', 'purple', 11, 'start', step=1), _e(80, 110, 240, 150, step=1, r=R),
         stext(80, 160, 'base', 'amber', 11, step=1),
         _codebox(440, 44, 290, 126, ['COURSE = "PG-DBDA"', '<<<<<<< HEAD', 'PASS_MARK = 45', '=======', 'PASS_MARK = 50', '>>>>>>> raise-pass'], 'red', step=2, size=11),
         stext(585, 186, 'git status: UU settings.py', 'red', 11, step=2, bold=True),
         _codebox(40, 204, 330, 140, ['<<<<<<< ours', 'PASS_MARK = 45', '||||||| base', 'PASS_MARK = 40', '=======', 'PASS_MARK = 50', '>>>>>>> theirs'], 'amber', step=3, size=11),
         stext(205, 362, 'checkout --conflict=diff3 adds the base', 'amber', 11, step=3),
         _codebox(400, 204, 330, 70, ['PASS_MARK = {"PG-DBDA": 50,', '             "Bridge": 45}', '$ git add settings.py && git commit'], 'green', step=4, size=11),
         _c(560, 316, 'd67ea80', 'green', step=5, r=R), stext(640, 320, 'merge commit', 'green', 11, 'start', step=5),
         stext(560, 362, 'conflict resolved and recorded', 'green', 11, step=5)]
    return anim(canvas(760, 378, *e), [
        'From the same base (40), main set the pass mark to 45 and raise-pass set it to 50 — the same line on both sides.',
        'git merge stops and writes both versions into the file between markers; git status shows UU (unmerged).',
        'The diff3 style also shows the base, which tells you what each side actually changed.',
        'Edit the file to the correct combined result (here: keep both pass marks), remove the markers and git add it.',
        'git commit completes the merge commit d67ea80. git merge --abort would have returned to the state before the merge.',
    ])


def rebase_anim():
    R = 24
    e = [_title('Rebase replays your commits on top of the new base'),
         _c(80, 90, '4154582', 'blue', r=R, sub='Base'), _c(220, 90, '5ab0a7b', 'blue', r=R, sub='Main moved on'), _e(80, 90, 220, 90, r=R),
         _ref(220, 46, 'main', 'green'),
         _c(220, 190, '67eac74', 'purple', r=R), _c(360, 190, '153a38d', 'purple', r=R), _e(80, 90, 220, 190, r=R), _e(220, 190, 360, 190, r=R),
         _ref(450, 190, 'feature', 'purple'),
         stext(290, 238, 'feature was started from Base', 'gray', 11),
         _c(360, 90, '625572b', 'purple', step=1, r=R, sub='Feature step 1'), _e(220, 90, 360, 90, step=1, r=R),
         sarrow(228, 166, 340, 112, 'amber', step=1, dashed=True),
         _c(500, 90, '5a545a7', 'purple', step=2, r=R, sub='Feature step 2'), _e(360, 90, 500, 90, step=2, r=R),
         sarrow(368, 166, 480, 112, 'amber', step=2, dashed=True),
         _hide(190, 160, 300, 60, 2), _ref(590, 90, 'feature', 'purple', step=2),
         stext(330, 264, 'old 67eac74 / 153a38d: no branch, still in the reflog', 'gray', 11, step=2),
         _hide(190, 34, 60, 24, 3), _ref(500, 46, 'main', 'green', step=3),
         stext(380, 290, 'git switch main && git merge feature  →  Fast-forward (linear history)', 'green', 12, step=3, bold=True),
         sbox(110, 310, 540, 50, 'Golden rule: do not rebase commits others already have', 'new hashes = new commits; pushed copies would conflict with the rewritten ones', 'red', step=4, size=12)]
    return anim(canvas(760, 374, *e), [
        'git rebase main takes Feature step 1 and applies its change on top of main\'s tip, creating a new commit 625572b.',
        'Feature step 2 is replayed on top of that (5a545a7) and the feature branch moves to the copy. HEAD went from 153a38d to 5a545a7.',
        'Because feature is now directly ahead of main, merging it is a fast-forward and history is a straight line.',
        'Rebasing creates new commits, so only rebase work that has not been shared (or coordinate a force push).',
    ])


def irebase_anim():
    R = 22
    old = [('60ea44e', 'Add CSV export', 'pick', 'green'), ('9a0ed31', 'fix typo', 'fixup', 'amber'), ('0fa4080', 'WIP tests', 'reword', 'blue'), ('1309c05', 'add debug log', 'drop', 'red')]
    e = [_title('Interactive rebase: edit the todo list, Git rewrites the commits'),
         _c(60, 80, '4154582', 'gray', r=R, sub='Base')]
    for i, (h, m, act, col) in enumerate(old):
        x = 180 + i * 140
        e += [_c(x, 80, h, 'blue', r=R, sub=m), _e(x - 140, 80, x, 80, r=R)]
    e += [_codebox(60, 140, 380, 112, ['# git rebase -i HEAD~4  (oldest first)'] + [f'{a:<7} {h} {m}' for h, m, a, c in old], 'gray', step=1, size=11)]
    for i, (h, m, act, col) in enumerate(old):
        e.append(stext(460, 178 + i * 16, {'pick': 'keep as is', 'fixup': 'meld into previous, drop message', 'reword': 'keep, edit message → "Add export tests"',
                                            'drop': 'remove the commit'}[act], col, 11, 'start', step=2))
    e += [_c(60, 300, '4154582', 'gray', step=3, r=R),
          _c(220, 300, 'a1aa372', 'green', step=3, r=R, sub='Add CSV export (+typo fix)'), _e(60, 300, 220, 300, step=3, r=R),
          _c(400, 300, '1c4682c', 'blue', step=3, r=R, sub='Add export tests'), _e(220, 300, 400, 300, step=3, r=R),
          _ref(490, 300, 'main', 'green', step=3),
          stext(620, 296, 'debug.log is gone;', 'red', 11, step=3), stext(620, 312, 'all hashes are new', 'red', 11, step=3),
          stext(380, 360, 'squash = meld and combine messages · edit = stop to amend · reorder lines to reorder commits', 'cyan', 11, step=4)]
    return anim(canvas(760, 374, *e), [
        'git rebase -i HEAD~4 opens a todo list of the last four commits, oldest first, each starting with pick.',
        'Changing the verb on each line tells Git what to do with that commit.',
        'Git replays the list: the typo fix is folded into "Add CSV export" (now a1aa372), the WIP commit gets a real message and the debug commit is dropped.',
        'Other verbs: squash keeps both messages, edit pauses for changes, and moving lines reorders commits. Only do this on unshared commits.',
    ])


# ============================================================ s04 remotes
def fetch_anim():
    R = 24
    e = [_title('fetch updates origin/main; pull also moves your branch'),
         sbox(20, 44, 300, 170, 'server: portal.git', '', 'purple', top=True, size=12, fill_opacity=0.08),
         sbox(400, 44, 340, 230, "Asha's clone", '', 'blue', top=True, size=12, fill_opacity=0.08),
         _c(90, 120, 'cc0faf8', 'blue', r=R), _ref(90, 166, 'main', 'purple'),
         _c(470, 140, 'cc0faf8', 'blue', r=R), _ref(470, 90, 'main', 'green'), _ref(470, 190, 'origin/main', 'gray'),
         _c(230, 120, '8fd2056', 'amber', step=1, r=R), _e(90, 120, 230, 120, step=1, r=R), _hide(60, 154, 60, 24, 1), _ref(230, 166, 'main', 'purple', step=1),
         stext(170, 200, 'Ravi pushed "Add login page"', 'amber', 11, step=1),
         sflow(322, 120, 398, 140, 'amber', step=2),
         _c(640, 140, '8fd2056', 'amber', step=2, r=R), _e(470, 140, 640, 140, step=2, r=R), _hide(430, 178, 80, 24, 2), _ref(640, 190, 'origin/main', 'gray', step=2),
         stext(570, 236, 'git status -sb → [behind 1]; files unchanged', 'amber', 11, step=2, bold=True),
         stext(570, 254, 'git log main..origin/main → 8fd2056', 'amber', 11, step=2),
         _hide(440, 78, 60, 24, 3), _ref(640, 90, 'main', 'green', step=3), sarrow(490, 116, 616, 116, 'green', step=3),
         stext(380, 300, 'git pull = git fetch + git merge origin/main  →  Fast-forward; login.html appears', 'green', 12, step=3, bold=True),
         stext(380, 326, 'remote-tracking branches (origin/*) only move when you fetch, pull or push', 'cyan', 11, step=4)]
    return anim(canvas(760, 342, *e), [
        'Ravi pushes a commit; the server\'s main moves. Asha\'s clone knows nothing yet — origin/main is her last snapshot of the server.',
        'git fetch downloads the new commit and moves origin/main only. Her main branch and her files are untouched, so she can inspect first.',
        'git pull fetches and then merges origin/main into main. Here that is a fast-forward and login.html appears in the working directory.',
        'origin/main is a local, read-only bookmark of the remote; it is refreshed only by talking to the remote.',
    ])


def push_anim():
    R = 22
    e = [_title('Why a push is rejected, and how to fix it'),
         _c(60, 110, 'cc0faf8', 'blue', r=R), _c(180, 70, '6e4737b', 'amber', r=R, step=1), _e(60, 110, 180, 70, step=1, r=R),
         stext(180, 40, 'Ravi: login (on server)', 'amber', 11, step=1),
         _c(180, 150, 'contact', 'blue', r=R, step=1), _e(60, 110, 180, 150, step=1, r=R),
         stext(180, 192, 'Asha: README contact (local)', 'blue', 11, step=1),
         _codebox(430, 46, 310, 70, [' ! [rejected]  main -> main (fetch first)', 'hint: the remote contains work that', 'you do not have locally'], 'red', step=2, size=10),
         stext(585, 134, 'pushing would drop 6e4737b', 'red', 11, step=2, bold=True),
         _c(320, 110, 'b261440', 'green', r=R, step=3), _e(180, 70, 320, 110, step=3, r=R), _e(180, 150, 320, 110, step=3, r=R),
         stext(360, 176, 'git pull → merge commit b261440', 'green', 11, 'start', step=3),
         stext(360, 194, 'git push → 6e4737b..b261440', 'green', 11, 'start', step=3, bold=True),
         _codebox(40, 252, 680, 70, ['$ git push -u origin feature/timetable', " * [new branch]  feature/timetable -> feature/timetable",
                                     "branch 'feature/timetable' set up to track 'origin/feature/timetable'."], 'purple', step=4, size=11),
         stext(380, 344, '-u records the upstream once; later plain git push / git pull know where to go (git branch -vv)', 'purple', 11, step=5)]
    return anim(canvas(760, 360, *e), [
        'Both sides moved on from cc0faf8: the server has Ravi\'s commit, Asha has her own.',
        'A push may only fast-forward the remote branch. Asha\'s main does not contain 6e4737b, so Git rejects the push instead of losing Ravi\'s work.',
        'git pull brings his commit in and creates a merge commit; now her main contains the server\'s main, and the push succeeds.',
        'For a new branch, git push -u origin <branch> creates it on the server and sets it as the upstream.',
        'With an upstream, git status shows ahead/behind and git push needs no arguments.',
    ])


def pullrb_anim():
    R = 22
    e = [_title('pull --no-rebase (merge) vs pull --rebase'),
         _c(80, 110, 'cc0faf8', 'blue', r=R), _c(200, 70, '6e4737b', 'amber', r=R, sub='login (Ravi)'), _c(200, 160, 'about', 'blue', r=R, sub='Add about page'),
         _e(80, 110, 200, 70, r=R), _e(80, 110, 200, 160, r=R),
         stext(140, 214, 'both sides have one new commit', 'gray', 11),
         stext(560, 48, '--no-rebase (merge)', 'purple', 13, step=2, bold=True),
         _c(400, 110, 'cc0faf8', 'blue', r=R, step=2), _c(500, 74, '6e4737b', 'amber', r=R, step=2), _c(500, 150, '296b853', 'blue', r=R, step=2),
         _c(620, 110, '3f532bb', 'purple', r=R, step=2), _e(400, 110, 500, 74, step=2, r=R), _e(400, 110, 500, 150, step=2, r=R),
         _e(500, 74, 620, 110, step=2, r=R), _e(500, 150, 620, 110, step=2, r=R),
         stext(690, 106, 'merge', 'purple', 10, step=2), stext(690, 120, 'commit', 'purple', 10, step=2),
         stext(560, 198, 'true history, extra merge commit', 'purple', 11, step=2),
         stext(380, 252, '--rebase', 'green', 13, step=3, bold=True),
         _c(200, 300, 'cc0faf8', 'blue', r=R, step=3), _c(340, 300, '6e4737b', 'amber', r=R, step=3), _c(480, 300, '28e9291', 'green', r=R, step=3, sub='Add about page (replayed)'),
         _e(200, 300, 340, 300, step=3, r=R), _e(340, 300, 480, 300, step=3, r=R),
         stext(620, 304, 'straight line', 'green', 11, 'start', step=3),
         stext(380, 362, 'rebase rewrites only your unpushed local commits; set pull.rebase=true to make it the default', 'cyan', 11, step=4),
         stext(380, 380, 'if a conflict occurs: fix, git add, git rebase --continue (or --abort)', 'cyan', 11, step=4)]
    return anim(canvas(760, 394, *e), [
        'Asha and Ravi both committed after cc0faf8. Asha now pulls.',
        'pull --no-rebase merges origin/main into main, creating merge commit 3f532bb that joins the two lines.',
        'pull --rebase fetches, then replays Asha\'s commit on top of Ravi\'s: new hash 28e9291, no merge commit, linear history.',
        'Rebasing during pull is safe because the replayed commits were never pushed; conflicts are handled one commit at a time.',
    ])


def pr_anim():
    e = [_title('Fork and pull-request workflow'),
         sbox(280, 44, 200, 50, 'upstream: portal.git', 'maintainers merge here', 'purple', size=12),
         sbox(560, 44, 180, 50, 'ravi-fork.git', "Ravi's copy on GitHub", 'amber', step=1, size=12),
         sbox(560, 200, 180, 50, "Ravi's laptop", 'origin=fork, upstream=portal', 'blue', step=1, size=12),
         sbox(20, 200, 180, 50, "Asha (maintainer)", 'reviews and merges', 'green', size=12),
         sarrow(650, 198, 650, 96, 'amber', step=2), stext(660, 150, 'push -u origin', 'amber', 11, 'start', step=2),
         stext(660, 166, 'feature/results', 'amber', 11, 'start', step=2),
         sarrow(558, 70, 482, 70, 'pink', step=3, dashed=True), stext(520, 40, 'pull request #1', 'pink', 12, step=3, bold=True),
         sarrow(560, 84, 200, 214, 'gray', step=4, dashed=True), stext(390, 238, 'fetch ravi · review main..ravi/feature/results', 'gray', 11, step=4),
         sarrow(110, 198, 300, 96, 'green', step=5), stext(192, 140, 'merge --no-ff · push', 'green', 11, 'end', step=5),
         _codebox(140, 270, 480, 54, ['*   e3e15f3 Merge pull request #1 from ravi/feature/results', '| * 292b2fa Add results page'], 'green', step=5, size=11),
         sarrow(420, 96, 600, 198, 'cyan', step=6), stext(560, 140, 'fetch upstream', 'cyan', 11, step=6),
         stext(380, 348, 'Ravi syncs: git merge --ff-only upstream/main — never commit directly on main', 'cyan', 12, step=6, bold=True)]
    return anim(canvas(760, 362, *e), [
        'Contributors without write access fork the project. Ravi\'s laptop has two remotes: origin (his fork) and upstream (the original).',
        'He works on a feature branch and pushes it to his fork.',
        'A pull request asks the maintainers to merge feature/results into upstream main; CI and reviewers comment on it.',
        'The maintainer can fetch the contributor\'s branch and review exactly the commits in main..ravi/feature/results.',
        'Merging the PR creates a merge commit on upstream main (e3e15f3).',
        'Ravi updates his own main from upstream with a fast-forward and starts the next branch from it.',
    ])


def tag_anim():
    R = 24
    e = [_title('Lightweight vs annotated tags, and git describe'),
         _c(100, 170, 'cc0faf8', 'blue', r=R, sub='Initial commit'),
         _ref(100, 116, 'v1.0-light', 'gray', step=1), sarrow(100, 128, 100, 144, 'gray', step=1),
         stext(100, 92, 'lightweight: ref → commit', 'gray', 10, step=1),
         sbox(190, 44, 210, 58, 'tag object bf178e3', 'v1.0.0 · Asha Patil · message', 'amber', step=2, size=11),
         _ref(295, 126, 'v1.0.0', 'amber', step=2), sarrow(295, 114, 295, 104, 'amber', step=2), sarrow(230, 102, 118, 150, 'amber', step=2),
         stext(560, 64, 'annotated: ref → tag object → commit', 'amber', 11, step=2),
         stext(560, 80, '(tagger, date, message; can be signed)', 'amber', 10, step=2),
         _c(260, 210, 'results', 'blue', r=R, step=3), _c(400, 210, '4fccfa2', 'blue', r=R, step=3, sub='Fix results layout'),
         _e(100, 170, 260, 210, step=3, r=R), _e(260, 210, 400, 210, step=3, r=R),
         _codebox(470, 150, 270, 54, ['$ git describe', 'v1.0.0-2-g4fccfa2'], 'green', step=3, size=11),
         stext(605, 222, 'tag · commits since · g + hash', 'green', 10, step=3),
         _codebox(40, 262, 470, 70, ['$ git push origin v1.0.0     (tags are not pushed by default)', 'bf178e3…  refs/tags/v1.0.0', 'cc0faf8…  refs/tags/v1.0.0^{}   (peeled to the commit)'], 'purple', step=4, size=11),
         _ref(400, 166, 'v1.1.0', 'amber', step=5), stext(620, 300, 'git tag -a v1.1.0', 'amber', 11, step=5),
         stext(620, 316, '→ describe = v1.1.0', 'amber', 11, step=5, bold=True)]
    return anim(canvas(760, 346, *e), [
        'A lightweight tag is just a named pointer to a commit, like a branch that never moves.',
        'An annotated tag creates a tag object (bf178e3) storing tagger, date and message; the ref points to that object. Use annotated tags for releases.',
        'Two commits later, git describe names HEAD relative to the nearest annotated tag: v1.0.0-2-g4fccfa2.',
        'Tags must be pushed explicitly; ls-remote shows the tag object and the commit it peels to (^{}).',
        'Tagging the new commit as v1.1.0 makes git describe print just the tag name.',
    ])


# ============================================================ s05 history
def cherry_anim():
    R = 24
    e = [_title('cherry-pick copies one commit onto another branch'),
         _c(70, 80, '9831c34', 'blue', r=R, sub='Release 2.3'),
         _c(220, 80, 'a1b6f1c', 'gray', r=R, sub='WIP dashboard'), _c(370, 80, 'de98af4', 'amber', r=R, sub='Fix timer timezone', focus='2'),
         _c(520, 80, 'a0621df', 'gray', r=R, sub='WIP charts'), _chain([(70, 80), (220, 80), (370, 80), (520, 80)], r=R),
         _ref(610, 80, 'main', 'green'), _ref(70, 170, 'release/2.3', 'purple'), sarrow(70, 158, 70, 126, 'purple'),
         stext(560, 206, 'release needs the fix, not the unfinished dashboard', 'gray', 11, step=1),
         _c(220, 220, '8c4b067', 'amber', r=R, step=3, sub='Fix timer timezone'), _e(70, 80, 220, 220, step=3, r=R),
         sarrow(350, 126, 240, 196, 'amber', step=2, dashed=True),
         stext(340, 172, 'git cherry-pick -x de98af4', 'amber', 12, 'start', step=2, bold=True),
         _hide(20, 124, 100, 58, 3), _ref(330, 236, 'release/2.3', 'purple', step=3),
         _codebox(400, 270, 340, 70, ['Fix exam timer timezone', '', '(cherry picked from commit de98af40f73d…)'], 'cyan', step=4, size=11),
         stext(200, 290, 'same change, new commit and hash', 'amber', 11, step=3),
         stext(200, 306, '(different parent)', 'amber', 11, step=3),
         stext(380, 366, 'use for hotfixes/backports; avoid as a substitute for merging whole branches (duplicates)', 'red', 11, step=5)]
    return anim(canvas(760, 380, *e), [
        'main has a bug fix sandwiched between two unfinished commits; release/2.3 needs only the fix.',
        'On release/2.3, git cherry-pick takes the diff introduced by de98af4 …',
        '… and applies it as a new commit 8c4b067 on the release branch. Same change and message, different parent, so a different hash.',
        '-x appends "(cherry picked from commit …)" so the copy can be traced back to its original.',
        'Cherry-picking many commits between long-lived branches creates duplicates; prefer merging when you want everything.',
    ])


def reflog_anim():
    R = 24
    xs = [80, 210, 340, 470]
    hs = [('0ac7eee', 'chapter 1'), ('16fde17', 'chapter 2'), ('a7816aa', 'chapter 3'), ('77c6b54', 'chapter 4')]
    e = [_title('The reflog remembers where HEAD has been')]
    for x, (h, m) in zip(xs, hs):
        e.append(_c(x, 90, h, 'blue', r=R, sub=m))
    e += [_chain([(x, 90) for x in xs], r=R), _ref(470, 46, 'main', 'green'),
          _hide(186, 60, 310, 66, 1), _hide(440, 34, 60, 24, 1), _ref(80, 46, 'main', 'green', step=1),
          stext(330, 148, 'git reset --hard HEAD~3: three chapters "gone"', 'red', 12, step=1, bold=True),
          _codebox(40, 168, 470, 86, ['$ git reflog -4', '0ac7eee HEAD@{0}: reset: moving to HEAD~3', '77c6b54 HEAD@{1}: commit: Write chapter 4',
                                      'a7816aa HEAD@{2}: commit: Write chapter 3'], 'amber', step=2, size=11),
          stext(630, 196, 'every move of HEAD', 'amber', 11, step=2), stext(630, 212, 'is logged locally', 'amber', 11, step=2),
          _hide(50, 34, 60, 24, 3)]
    for x, (h, m) in zip(xs, hs):
        e.append(_c(x, 90, h, 'green', r=R, step=3, sub=m))
    e += [_chain([(x, 90) for x in xs], step=3, col='green', r=R), _ref(470, 46, 'main', 'green', step=3),
          stext(630, 86, 'git reset --hard HEAD@{1}', 'green', 11, step=3, bold=True), stext(630, 102, '→ all four back', 'green', 11, step=3),
          _codebox(40, 274, 680, 70, ['$ git branch -D experiment   →  Deleted branch experiment (was c0ac884).', '$ git reflog | grep -m1 "Experiment"   →  c0ac884 HEAD@{1}: commit: Experiment',
                                      '$ git branch experiment c0ac884'], 'purple', step=4, size=11),
          stext(380, 366, 'reflog is local and expires (90 days by default; 30 for unreachable commits) — not a backup', 'red', 11, step=5)]
    return anim(canvas(760, 380, *e), [
        'A hard reset moves main back three commits. git log no longer shows chapters 2–4.',
        'The commits still exist. git reflog lists every position HEAD has had: before the reset it was at 77c6b54 (HEAD@{1}).',
        'Resetting to HEAD@{1} restores the branch — and the files — exactly.',
        'A deleted branch is recovered the same way: find its last commit in the reflog and create a branch there.',
        'The reflog lives only in your clone and expires, so it is an undo safety net, not a backup.',
    ])


def bisect_anim():
    X0, DX = 40, 22.6
    xp = lambda i: X0 + i * DX
    rows = [(1, 0, 30, None, None, 'start: HEAD~30 good, HEAD bad — 30 suspects'),
            (2, 1, 30, 15, 'good', 'test notes 15 → good: bug is after it'),
            (3, 16, 30, 22, 'bad', 'test notes 22 → bad: bug is at or before it'),
            (4, 16, 22, 18, 'good', 'test notes 18 → good'),
            (5, 19, 22, 20, 'bad', 'test notes 20 → bad, then #19 → bad')]
    e = [_title('git bisect: binary search for the first bad commit')]
    for st, lo, hi, t, res, txt in rows:
        y = 40 + st * 46
        e.append(f'<rect x="{xp(lo) - 9:.1f}" y="{y - 12}" width="{xp(hi) - xp(lo) + 18:.1f}" height="24" rx="12" fill="#f59e0b" fill-opacity="0.15" data-step="{st}"/>')
        for i in range(31):
            col = 'green' if i == 0 else ('red' if i == 30 else '#475569')
            if t is not None and i == t:
                col = 'green' if res == 'good' else 'red'
            e.append(_dot(xp(i), y, col, step=st, r=6 if i == t else 4))
        if st == 5:
            e.append(_dot(xp(19), y, 'red', step=st, r=6))
        e.append(stext(xp(30) + 12 - 0, y - 16, txt, 'amber' if st < 5 else 'red', 11, 'end', step=st))
    e += [stext(xp(0), 300, 'good', 'green', 10, step=1), stext(xp(30), 300, 'bad', 'red', 10, step=1),
          sbox(xp(19) - 70, 308, 140, 40, '8aaf448 (#19)', 'first bad commit', 'red', step=6, size=12, focus='6'),
          sarrow(xp(19), 306, xp(19), 280, 'red', step=6),
          stext(30, 322, '30 suspects → 5 tests (log₂30 ≈ 5)', 'cyan', 12, 'start', step=6, bold=True),
          stext(30, 340, 'git bisect run check.py automates every test', 'cyan', 11, 'start', step=6),
          stext(30, 358, 'git bisect reset when done', 'gray', 11, 'start', step=6)]
    return anim(canvas(760, 370, *e), [
        'Mark a known good commit (HEAD~30) and a known bad one (HEAD). Bisect checks out the middle.',
        'check.py exits 0 on "Update notes 15", so it is good; the culprit is in the newer half.',
        '"Update notes 22" fails, so the bug arrived at or before it.',
        '"Update notes 18" passes; three candidates remain.',
        '"Update notes 20" and then "Refactor grade boundaries (#19)" fail, while 18 passed.',
        'Bisect reports 8aaf448 as the first bad commit after only 5 tests. git bisect run makes the whole search automatic: exit 0 = good, 1–127 = bad, 125 = skip.',
    ])


def blame_anim():
    rows = [['^d94d86c', 'Asha Patil', '09:03', '1', 'def report(att):'], ['d5277f48', 'Asha Patil', '09:06', '2', '    # attendance percentage …'],
            ['afb2abc7', 'Ravi Kumar', '09:05', '3', '    return min(att, 95)']]
    e = [_title('Who changed this line, and why?'),
         stable(30, 54, ['commit', 'author', 'time', 'line', 'content'], rows, [100, 110, 70, 50, 360], h=28, step=1, title='git blame report.py',
                title_color='blue', focus_rows={2: '2'}),
         stext(380, 186, '^ = line unchanged since the first (boundary) commit', 'gray', 11, step=1),
         _codebox(30, 202, 330, 54, ['$ git blame -L 3,3 --porcelain report.py', 'author Ravi Kumar · summary Cap attendance at 95%'], 'amber', step=2, size=10),
         _codebox(400, 202, 330, 54, ['$ git log -S "min(att, 95)"', 'afb2abc Ravi Kumar Cap attendance at 95%'], 'purple', step=3, size=10),
         stext(380, 286, 'git log -L :report:report.py — the function\'s whole story', 'green', 12, step=4, bold=True)]
    hist = [('d94d86c', 'Add attendance report', '+ return att'), ('afb2abc', 'Cap attendance at 95%', '- return att  + return min(att, 95)'),
            ('d5277f4', 'Document report()', '+ # attendance percentage …')]
    for i, (h, m, d) in enumerate(hist):
        x = 130 + i * 250
        e += [_c(x, 326, h, 'green', step=4, r=26), stext(x, 368, m, 'green', 10, step=4), stext(x, 384, d, 'gray', 10, step=4)]
    e += [_chain([(130, 326), (380, 326), (630, 326)], step=4, r=26),
          stext(380, 410, 'blame shows the last change only: use -w (ignore whitespace), -C (moved code), --ignore-revs-file for reformat commits', 'cyan', 11, step=5)]
    return anim(canvas(760, 424, *e), [
        'git blame annotates each line with the commit, author and time that last changed it.',
        '-L limits blame to a line range; --porcelain gives machine-readable fields such as author and summary.',
        'git log -S (pickaxe) finds the commit that introduced a string, even if the line was later moved.',
        'git log -L follows a line range or a function through history, showing each change as a diff.',
        'A whitespace or reformatting commit can hide the real author; blame options and an ignore-revs file skip them.',
    ])


def detached_anim():
    R = 24
    e = [_title('Detached HEAD: HEAD points to a commit, not a branch'),
         _c(120, 150, 'c0d5c25', 'blue', r=R, sub='v1'), _c(300, 150, 'c58994f', 'blue', r=R, sub='v2'), _e(120, 150, 300, 150, r=R),
         _ref(120, 200, 'tag v1.0', 'amber'), _ref(300, 104, 'main', 'green'), _ref(300, 62, 'HEAD', 'amber'), sarrow(300, 73, 300, 92, 'amber'),
         _hide(270, 50, 60, 24, 1), _ref(120, 104, 'HEAD', 'red', step=1), sarrow(120, 116, 120, 124, 'red', step=1),
         _codebox(420, 50, 320, 54, ['$ cat .git/HEAD', 'c0d5c25c22cf203b0c90695faf7c90c0cfe679ad'], 'red', step=1, size=10),
         stext(580, 122, 'a hash, not "ref: refs/heads/…"', 'red', 11, step=1),
         _c(240, 270, '702d573', 'purple', r=R, step=2, sub='Hotfix on v1'), _e(120, 150, 240, 270, step=2, r=R),
         _hide(90, 92, 60, 24, 2), _ref(316, 270, 'HEAD', 'red', step=2),
         _hide(280, 258, 72, 24, 3), _ref(300, 62, 'HEAD', 'amber', step=3), sarrow(300, 73, 300, 92, 'amber', step=3),
         _codebox(420, 150, 320, 70, ['Warning: you are leaving 1 commit behind,', 'not connected to any of your branches:', '  702d573 Hotfix on v1'], 'amber', step=3, size=10),
         _ref(110, 300, 'hotfix/v1.0.1', 'green', step=4), sarrow(160, 294, 214, 278, 'green', step=4),
         _codebox(420, 240, 320, 54, ['$ git reflog -2  → 702d573 HEAD@{1}', '$ git branch hotfix/v1.0.1 HEAD@{1}'], 'green', step=4, size=10),
         stext(580, 330, 'or, before leaving: git switch -c <name>', 'green', 11, step=5, bold=True)]
    return anim(canvas(760, 352, *e), [
        'git switch --detach v1.0 checks out the tagged commit. HEAD now stores a commit hash directly; no branch is checked out.',
        'Committing still works, but the new commit 702d573 belongs to no branch — only HEAD points to it.',
        'Switching back to main leaves it behind; Git warns, because nothing references it any more.',
        'Rescue it with a branch at its hash, found in the warning or the reflog.',
        'Best practice: if you plan to commit, create a branch first with git switch -c.',
    ])


# ============================================================ s06 workflows
def flow_anim():
    R = 21
    L = {'main': 70, 'hotfix': 122, 'release': 174, 'develop': 226, 'feature': 278}
    C = {'0299dbb': (110, 'main'), '0b25572': (180, 'feature'), 'd44b3f4': (250, 'develop'), '542d1b4': (320, 'release'), '3e7fcc0': (390, 'main'),
         'd0ebf9c': (460, 'develop'), 'aa33d79': (530, 'hotfix'), '4272948': (600, 'main'), 'f292c4c': (670, 'develop')}
    P = {k: (x, L[l]) for k, (x, l) in C.items()}
    col = {'main': 'blue', 'hotfix': 'red', 'release': 'amber', 'develop': 'purple', 'feature': 'green'}
    st = {'0299dbb': 1, '0b25572': 2, 'd44b3f4': 2, '542d1b4': 3, '3e7fcc0': 3, 'd0ebf9c': 3, 'aa33d79': 4, '4272948': 4, 'f292c4c': 4}
    edges = [('0299dbb', '0b25572', 2), ('0299dbb', 'd44b3f4', 2), ('0b25572', 'd44b3f4', 2), ('d44b3f4', '542d1b4', 3), ('0299dbb', '3e7fcc0', 3),
             ('542d1b4', '3e7fcc0', 3), ('d44b3f4', 'd0ebf9c', 3), ('542d1b4', 'd0ebf9c', 3), ('3e7fcc0', 'aa33d79', 4), ('3e7fcc0', '4272948', 4),
             ('aa33d79', '4272948', 4), ('d0ebf9c', 'f292c4c', 4), ('aa33d79', 'f292c4c', 4)]
    e = [_title('Git Flow with real commits from the example')]
    for name, y in L.items():
        e += [stext(16, y + 4, name, col[name], 11, 'start', step=1, bold=True),
              f'<line x1="86" y1="{y}" x2="740" y2="{y}" stroke="{PALETTE[col[name]]}" stroke-opacity="0.18" stroke-width="10" data-step="1"/>']
    for a, b, s_ in edges:
        e.append(_e(*P[a], *P[b], step=s_, r=R))
    for k, (x, l) in C.items():
        e.append(_c(*P[k], k, col[l], step=st[k], r=R))
    e += [stext(110, 46, 'v1.0', 'amber', 10, step=1, bold=True), stext(390, 46, 'v1.1', 'amber', 10, step=3, bold=True),
          stext(600, 46, 'v1.1.1', 'amber', 10, step=4, bold=True),
          stable(40, 334, ['strategy', 'long-lived branches', 'release style', 'fits'],
                 [['Git Flow', 'main + develop (+ release/hotfix)', 'scheduled versions', 'packaged / versioned software'],
                  ['GitHub Flow', 'main only + short feature branches', 'deploy after each PR', 'web apps, small teams'],
                  ['Trunk-based', 'main; branches live < 1–2 days', 'continuous; feature flags', 'mature CI, many deploys/day']],
                 [110, 220, 170, 180], h=24, step=5, title='compare', title_color='cyan')]
    return anim(canvas(760, 440, *e), [
        'Git Flow keeps two permanent branches: main (released versions, tagged) and develop (integration).',
        'Features branch off develop and are merged back with --no-ff (d44b3f4).',
        'A release branch stabilises the version (542d1b4), is merged into main and tagged v1.1, then merged back into develop.',
        'A hotfix branches from main, is merged to main as v1.1.1 and back into develop so the fix is not lost.',
        'GitHub Flow and trunk-based development drop develop/release branches and rely on short-lived branches, CI and frequent deploys.',
    ])


def methods_anim():
    R = 22
    e = [_title('Three ways to merge a pull request (real history)'),
         _c(380, 330, '4154582', 'gray', r=R), stext(350, 334, 'Base', 'gray', 11, 'end'),
         _c(380, 260, 'c9eeef0', 'purple', r=R, step=1), _e(380, 330, 380, 260, step=1, r=R),
         _c(470, 310, 'e92132c', 'blue', r=R, step=1), _c(470, 260, 'b577141', 'blue', r=R, step=1),
         _e(380, 330, 470, 310, step=1, r=R), _e(470, 310, 470, 260, step=1, r=R), _e(470, 260, 380, 260, step=1, r=R),
         stext(240, 264, 'merge commit', 'purple', 12, 'end', step=1, bold=True),
         stext(240, 280, 'all commits + 1 merge commit', 'purple', 10, 'end', step=1),
         _c(380, 190, '2a114f1', 'amber', r=R, step=2), _e(380, 260, 380, 190, step=2, r=R),
         stext(240, 194, 'squash merge', 'amber', 12, 'end', step=2, bold=True),
         stext(240, 210, '2 commits → 1 new commit', 'amber', 10, 'end', step=2),
         _c(380, 120, '044fa4b', 'green', r=R, step=3), _c(380, 60, '0570fb2', 'green', r=R, step=3),
         _e(380, 190, 380, 120, step=3, r=R), _e(380, 120, 380, 60, step=3, r=R),
         stext(240, 94, 'rebase merge', 'green', 12, 'end', step=3, bold=True),
         stext(240, 110, 'commits copied, no merge commit', 'green', 10, 'end', step=3),
         _ref(470, 60, 'main', 'green', step=3),
         _codebox(540, 110, 200, 104, ['$ git branch --no-merged', '  pr-squash', '', 'squashed content is in main,', 'but its commits are not'], 'red', step=4, size=10),
         stext(640, 236, 'delete squash branches with -D', 'red', 10, step=4),
         stext(380, 378, 'merge: full context · squash: one tidy commit per PR · rebase: linear, keeps each commit', 'cyan', 11, step=5)]
    return anim(canvas(760, 392, *e), [
        '"Create a merge commit" keeps the PR\'s commits and adds a merge commit with two parents (c9eeef0).',
        '"Squash and merge" combines the PR into one new commit (2a114f1); the original commits are not in main.',
        '"Rebase and merge" replays each commit on top of main (new hashes 044fa4b, 0570fb2) and fast-forwards — linear history.',
        'Because squash creates new content, Git does not consider pr-squash merged; that is expected.',
        'Teams usually pick one method per repository and enforce it in the GitHub settings.',
    ])


def hooks_anim():
    e = [_title('Client-side hooks run at fixed points of git commit'),
         sbox(20, 60, 120, 50, 'git commit', '', 'gray', step=1, size=13),
         sbox(180, 60, 160, 50, 'pre-commit', 'checks staged diff', 'amber', step=1, size=12),
         sbox(380, 60, 160, 50, 'commit-msg', 'checks message ($1)', 'purple', step=1, size=12),
         sbox(580, 60, 160, 50, 'commit created', '', 'green', step=1, size=12),
         sarrow(140, 85, 178, 85, 'gray', step=1), sarrow(340, 85, 378, 85, 'gray', step=1), sarrow(540, 85, 578, 85, 'gray', step=1),
         stext(380, 244, 'any hook exiting non-zero aborts the commit', 'gray', 11, step=1),
         sarrow(260, 112, 260, 170, 'red', step=2),
         _codebox(130, 172, 270, 54, ['+db_password=secret123', 'pre-commit: remove passwords/print()…'], 'red', step=2, size=10),
         sarrow(460, 112, 520, 170, 'red', step=3),
         _codebox(420, 172, 320, 54, ['"added stuff"', "commit-msg: use 'type: summary' …"], 'red', step=3, size=10),
         stext(660, 136, 'feat: add grade function → 69fd01d', 'green', 11, step=4, bold=True),
         sbox(130, 258, 500, 50, 'git config core.hooksPath .githooks', 'hooks live in the repo and are committed, so the team shares them', 'cyan', step=5, size=12),
         stext(380, 336, 'hooks can be skipped (git commit --no-verify): enforce the same checks in CI / branch protection', 'red', 11, step=6)]
    return anim(canvas(760, 352, *e), [
        'git commit runs pre-commit (before the message), then commit-msg (with the message file), then creates the commit.',
        'Our pre-commit hook scans the staged diff and rejects a password, so the secret never enters history.',
        'Our commit-msg hook rejects a message that is not in "type: summary" form.',
        'A conventional message passes both hooks and the commit is created.',
        '.git/hooks is not versioned; pointing core.hooksPath to a committed folder shares hooks with everyone (tools like pre-commit do the same).',
        'Client hooks are a convenience, not security — repeat important checks on the server side.',
    ])


def attrs_anim():
    e = [_title('.gitattributes: line endings, binary files, large files'),
         _codebox(30, 46, 220, 70, ['* text=auto', '*.sh text eol=lf', '*.png binary'], 'amber', step=1, size=11),
         sbox(300, 46, 140, 46, 'working copy', 'run.sh: CRLF', 'gray', step=2, size=12),
         sbox(560, 46, 170, 46, 'repository (index)', 'run.sh: LF', 'green', step=2, size=12),
         sarrow(440, 69, 558, 69, 'green', step=2), stext(500, 60, 'normalised', 'green', 10, step=2),
         _codebox(300, 108, 430, 70, ['$ git ls-files --eol', 'i/lf    w/crlf  attr/text eol=lf     run.sh', 'i/-text w/-text attr/-text         logo.png'], 'cyan', step=3, size=10),
         _codebox(30, 196, 330, 54, ['$ git cat-file -p HEAD:run.sh | od -c', 'e c h o   h e l l o \\n'], 'green', step=3, size=10),
         _codebox(400, 196, 330, 54, [' logo.png | Bin 11 -> 18 bytes', 'Binary files a/logo.png and b/logo.png differ'], 'purple', step=4, size=10),
         stext(565, 268, 'binary = no text diff, no merge, no EOL conversion', 'purple', 10, step=4),
         sbox(130, 286, 500, 54, 'Large files: Git LFS (*.csv filter=lfs) or DVC', 'repo stores a small pointer; content lives on an LFS / storage server', 'blue', step=5, size=12)]
    return anim(canvas(760, 354, *e), [
        '.gitattributes assigns attributes by pattern; it is committed, so every clone behaves the same.',
        'text=auto / eol=lf normalise line endings: the repository stores LF even if a Windows editor wrote CRLF.',
        'git ls-files --eol shows the index (i/) and working copy (w/) endings and the attribute applied; the stored blob ends in \\n.',
        'binary turns off text diffs, merges and conversion, so Git only reports that the file changed.',
        'Large or frequently changing binaries belong in Git LFS or DVC, which keep only pointers in the repository.',
    ])


def convention_anim():
    rows = [['af389ff', 'feat(results): add PDF download', 'minor'], ['8b1c9fd', 'fix(timer): use IST for exam end time', 'patch'],
            ['8832c65', 'docs: update admin guide', '—'], ['1cae733', 'fix(login): handle expired sessions', 'patch'],
            ['bccc874', 'feat(admin)!: replace CSV upload …', 'MAJOR'], ['97568fb', 'test: add timer tests', '—']]
    e = [_title('Conventional Commits → semantic version → changelog'),
         stable(30, 56, ['commit', 'message since v1.4.2', 'bump'], rows, [90, 300, 80], h=26, step=1, title='type(scope)!: summary', title_color='blue',
                focus_rows={4: '2'}),
         sbox(540, 50, 200, 80, 'MAJOR . MINOR . PATCH', 'breaking · feature · fix', 'amber', step=2, size=12),
         stext(640, 160, 'v1.4.2  →  v2.0.0', 'red', 16, step=3, bold=True),
         stext(640, 180, 'highest bump wins: ! = breaking', 'red', 11, step=3),
         _codebox(540, 200, 200, 130, ['## Features', '- replace CSV upload …', '- add PDF download', '## Fixes', '- handle expired sessions', '- use IST for exam end time'],
                  'green', step=4, size=10),
         stext(250, 260, 'git log v1.4.2..HEAD --grep="^feat" → changelog sections', 'green', 11, step=4),
         _codebox(30, 280, 300, 54, ['$ git shortlog -sn v1.4.2..HEAD', '5 Asha Patil   1 Ravi Kumar'], 'cyan', step=5, size=10),
         stext(250, 356, 'tools: commitlint (hook/CI), semantic-release / release-please automate the tag and notes', 'cyan', 11, step=5)]
    return anim(canvas(760, 370, *e), [
        'Each commit message starts with a type (feat, fix, docs, test …), an optional scope and ! for breaking changes.',
        'Semantic versioning: breaking change → MAJOR, new feature → MINOR, bug fix → PATCH; docs/tests change nothing.',
        'The release since v1.4.2 contains a breaking change, so the next version is v2.0.0.',
        'Because messages are structured, git log --grep can generate the changelog automatically.',
        'shortlog credits contributors; commitlint and release tools enforce and automate the whole process.',
    ])


# ============================================================ s07 github & tooling
def ssh_anim():
    e = [_title('SSH keys: the private key never leaves your laptop'),
         sbox(20, 46, 300, 150, "Asha's laptop  ~/.ssh", '', 'blue', top=True, size=12, fill_opacity=0.08),
         sbox(440, 46, 300, 150, 'GitHub', '', 'purple', top=True, size=12, fill_opacity=0.08),
         sbox(40, 84, 260, 40, 'id_ed25519   -rw-------', 'private key — secret', 'red', step=1, size=11),
         sbox(40, 136, 260, 40, 'id_ed25519.pub   -rw-r--r--', 'public key — safe to share', 'green', step=1, size=11),
         stext(170, 214, 'ssh-keygen -t ed25519 -C "asha@cdac.example"', 'blue', 11, step=1),
         sarrow(302, 160, 458, 160, 'green', step=2), stext(380, 154, 'public key', 'green', 10, step=2),
         sbox(460, 140, 260, 40, 'authorized key: ssh-ed25519 AAAA…', '', 'green', step=2, size=11),
         stext(590, 196 - 70, 'Settings → SSH and GPG keys', 'green', 10, step=2),
         sarrow(438, 94, 302, 94, 'amber', step=3), stext(370, 88, 'challenge', 'amber', 10, step=3),
         sarrow(302, 118, 438, 118, 'amber', step=3), stext(370, 134, 'signed response', 'amber', 10, step=3),
         stext(590, 96, 'verified with public key ✔', 'green', 11, step=3, bold=True),
         _codebox(20, 236, 350, 86, ['Host github-cdac', '    HostName github.com', '    User git', '    IdentityFile ~/.ssh/id_ed25519'], 'cyan', step=4, size=10),
         _codebox(390, 236, 350, 86, ['$ git remote set-url origin \\', '    git@github-cdac:asha-patil/portal.git', 'before: https://github.com/asha-patil/…'], 'cyan', step=4, size=10),
         stext(380, 348, 'HTTPS needs a personal access token (not your password) + credential helper; SSH needs a key once per machine', 'gray', 11, step=5)]
    return anim(canvas(760, 362, *e), [
        'ssh-keygen creates a key pair: the private key (readable only by you) and the public key.',
        'You give GitHub only the public key.',
        'On each connection GitHub sends a challenge; your SSH client signs it with the private key and GitHub checks the signature. No password crosses the network.',
        'A Host alias in ~/.ssh/config picks the key; the remote URL is switched from HTTPS to SSH with git remote set-url.',
        'HTTPS works too, but GitHub requires a token instead of a password; store it in a credential helper.',
    ])


def ci_anim():
    steps_ = ['actions/checkout@v4', 'setup-python 3.12', 'pip install -r requirements.txt', 'pytest -q']
    e = [_title('GitHub Actions: every push and pull request runs the tests'),
         sbox(20, 56, 140, 50, 'git push / PR', '', 'gray', step=1, size=12),
         _codebox(20, 124, 140, 54, ['.github/workflows/', '  ci.yml'], 'amber', step=1, size=10),
         sarrow(162, 81, 208, 81, 'gray', step=1),
         sbox(210, 46, 300, 196, 'runner: ubuntu-latest', '', 'blue', top=True, size=12, fill_opacity=0.08, step=2)]
    for i, s_ in enumerate(steps_):
        e.append(sbox(230, 78 + i * 40, 260, 30, s_, '', 'blue', step=2, size=11))
    e += [sbox(550, 56, 190, 56, '✔ main: 2 passed', 'commit gets a green check', 'green', step=3, size=12),
          sarrow(492, 200, 548, 90, 'green', step=3),
          sbox(550, 140, 190, 70, '✘ fix/boundary', 'm > 50: test_pass failed\n1 failed, 1 passed', 'red', step=4, size=12),
          sarrow(492, 200, 548, 176, 'red', step=4),
          sbox(130, 270, 500, 54, 'Branch protection: "tests" must pass before merge', 'the PR with the boundary bug cannot be merged', 'red', step=5, size=12, focus='5'),
          stext(380, 350, 'same pytest command locally and in CI — CI just makes it impossible to forget', 'cyan', 11, step=5)]
    return anim(canvas(760, 364, *e), [
        'A workflow file in .github/workflows declares when to run (push to main, pull requests) and what to do.',
        'GitHub starts a fresh runner, checks out the commit, installs Python and the requirements, then runs pytest.',
        'On main both tests pass (2 passed) and the commit is marked green.',
        'On fix/boundary the changed comparison makes grade(50) return "F": test_pass fails and the check turns red.',
        'With a required status check, a red PR cannot be merged — bugs are caught before they reach main.',
    ])


def worktree_anim():
    e = [_title('Big repositories: shallow clone, sparse checkout, worktrees'),
         stext(130, 50, 'shallow: --depth 1', 'blue', 13, step=1, bold=True)]
    for i in range(20):
        x = 30 + (i % 10) * 20
        y = 74 + (i // 10) * 20
        e.append(_dot(x, y, '#475569', step=1, r=5))
    e += [_dot(210, 94, 'blue', step=1, r=7), _hide(20, 64, 182, 40, 1),
          stext(130, 126, 'only c65dd01 of 20 commits', 'blue', 11, step=1),
          stext(130, 142, 'is-shallow-repository: true', 'blue', 10, step=1),
          stext(390, 50, 'sparse: only spark/', 'amber', 13, step=2, bold=True),
          sbox(300, 64, 60, 34, 'spark/', '', 'amber', step=2, size=11), sbox(366, 64, 54, 34, 'hive/', '', 'gray', step=2, size=11),
          sbox(426, 64, 54, 34, 'web/', '', 'gray', step=2, size=11), _hide(364, 62, 120, 38, 2),
          stext(390, 126, 'all history, few files on disk', 'amber', 11, step=2),
          stext(390, 142, 'git sparse-checkout set spark', 'amber', 10, step=2),
          stext(640, 50, 'worktree: 2nd folder', 'green', 13, step=3, bold=True),
          sbox(540, 64, 200, 40, '~/cdac/big  [main]', 'c65dd01', 'blue', step=3, size=11),
          sbox(540, 116, 200, 40, '~/cdac/big-hotfix  [hotfix/title]', 'db2f83c → 7933590', 'green', step=3, size=11),
          sbox(220, 200, 320, 50, 'one .git: shared objects and branches', 'commit in big-hotfix → visible from big immediately', 'purple', step=4, size=12),
          sarrow(640, 158, 540, 214, 'purple', step=4),
          stext(380, 280, 'git worktree remove ../big-hotfix  → folder gone, commit 7933590 kept on hotfix/title', 'green', 11, step=5),
          stext(380, 306, 'shallow = CI and quick looks · sparse = monorepos · worktree = urgent fix without stashing', 'cyan', 11, step=5)]
    return anim(canvas(760, 322, *e), [
        'A shallow clone (--depth 1) downloads only the latest commit — fast for CI, but history commands are limited.',
        'Sparse checkout keeps the full repository but puts only the folders you choose on disk.',
        'git worktree add creates a second working folder on another branch — here an urgent title fix — while main stays untouched.',
        'Both folders share one object database, so commits made in one are visible in the other without push or fetch.',
        'Removing the worktree deletes only the folder; the branch and its commit remain.',
    ])


def secret_anim():
    R = 22
    hs = [('f619c85', 'Add app', 'blue'), ('58b3ec9', 'Add config', 'red'), ('fd08c3a', 'Add routes', 'blue'), ('8e015f9', 'Remove config', 'amber')]
    e = [_title('A committed password stays in history until it is rewritten')]
    for i, (h, m, c) in enumerate(hs):
        e.append(_c(90 + i * 150, 90, h, c, r=R, sub=m, focus='2' if i == 1 else None))
    e += [_chain([(90 + i * 150, 90) for i in range(4)], r=R), _ref(620, 90, 'main', 'green'),
          stext(240, 140, 'DB_PASSWORD = "Cdac@2026"', 'red', 11, step=1, bold=True),
          stext(540, 140, 'file deleted… but still in 58b3ec9', 'amber', 11, step=1),
          _codebox(40, 160, 330, 54, ['$ git log -S "DB_PASSWORD" --oneline', '8e015f9 Remove config · 58b3ec9 Add config'], 'red', step=2, size=10),
          _codebox(400, 160, 330, 54, ['$ git show HEAD~2:config.py', 'DB_PASSWORD = "Cdac@2026"'], 'red', step=2, size=10),
          _c(90, 260, 'f619c85', 'green', r=R, step=3, sub='Add app'), _c(240, 260, 'ff95167', 'green', r=R, step=3, sub='Add routes (new hash)'),
          _e(90, 260, 240, 260, step=3, r=R), _ref(330, 260, 'main', 'green', step=3), _hide(590, 78, 70, 24, 3),
          stext(560, 250, 'filter-branch --index-filter "git rm --cached config.py"', 'green', 10, step=3),
          stext(560, 266, '--prune-empty drops now-empty commits', 'green', 10, step=3),
          stext(380, 214 + 96, 'refs/original/refs/heads/main still keeps the old commits (log --all -S finds them)', 'amber', 11, step=3),
          _hide(30, 64, 640, 92, 4),
          stext(380, 336, 'update-ref -d refs/original · reflog expire --expire=now · gc --prune=now  →  0 hits', 'green', 11, step=4, bold=True),
          sbox(110, 352, 540, 46, '1. rotate the password  2. force-push + everyone re-clones  3. .gitignore / secret scanning', '', 'red', step=5, size=11)]
    return anim(canvas(760, 410, *e), [
        'The password was committed in 58b3ec9 and "removed" two commits later — but every old commit still contains it.',
        'Anyone with the repository can find and print it with git log -S and git show.',
        'Rewriting removes config.py from every commit: the two config commits become empty and are pruned; later commits get new hashes. A backup ref still points to the old history.',
        'Deleting the backup ref, expiring the reflog and garbage-collecting removes the old objects; the search now returns nothing.',
        'Treat the secret as leaked anyway: rotate it first, then force-push the rewritten history and prevent it from happening again. (git filter-repo is the modern tool.)',
    ])


def nb_anim():
    e = [_title('A clean filter stores notebooks without outputs'),
         sbox(20, 50, 210, 150, 'eda.ipynb (working copy)', '', 'gray', top=True, size=12, fill_opacity=0.08, step=1),
         sbox(36, 84, 178, 26, 'markdown: # Placement EDA', '', 'blue', step=1, size=10),
         sbox(36, 116, 178, 26, 'code: df.head()', '', 'blue', step=1, size=10),
         sbox(36, 148, 178, 36, 'outputs: PNG (base64)', 'execution_count: 1', 'red', step=1, size=10),
         stext(125, 220, '14 075 bytes', 'red', 12, step=1, bold=True),
         sbox(290, 96, 180, 60, 'clean filter', 'python3 nbclean.py', 'amber', step=2, size=12),
         sarrow(232, 126, 288, 126, 'amber', step=2), sarrow(472, 126, 528, 126, 'amber', step=2),
         _codebox(290, 166, 180, 40, ['*.ipynb filter=nbclean'], 'amber', step=2, size=10),
         sbox(530, 50, 210, 150, 'stored blob (HEAD)', '', 'green', top=True, size=12, fill_opacity=0.08, step=3),
         sbox(546, 84, 178, 26, 'markdown: # Placement EDA', '', 'blue', step=3, size=10),
         sbox(546, 116, 178, 26, 'code: df.head()', '', 'blue', step=3, size=10),
         sbox(546, 148, 178, 36, 'outputs: []', 'execution_count: null', 'green', step=3, size=10),
         stext(635, 220, '304 bytes', 'green', 12, step=3, bold=True),
         _codebox(20, 244, 340, 86, ['re-run (new outputs) →', '$ git status --short   →   M eda.ipynb', '$ git diff --stat | wc -l   →  0', '$ git add → nothing to commit'], 'amber', step=4, size=10),
         _codebox(400, 244, 340, 70, ['edit code (head → describe) →', '-    "df.head()"', '+    "df.describe()"'], 'green', step=5, size=10),
         stext(570, 334, 'diffs show only real changes', 'green', 11, step=5),
         stext(380, 356, 'large data: .gitignore it, version with DVC or Git LFS', 'cyan', 11, step=5)]
    return anim(canvas(760, 370, *e), [
        'The notebook on disk carries code plus outputs: an embedded image and an execution count make it 14 KB.',
        'A clean filter (declared in .gitattributes, configured with git config filter.nbclean.clean) runs whenever Git stores the file.',
        'The repository receives only code and markdown — 304 bytes. Your working copy keeps its outputs.',
        'Re-running the notebook changes only outputs: git status flags the file by size, but the cleaned content is identical, so diff and add see no change.',
        'A real code edit shows up as a one-line diff, which makes notebooks reviewable.',
    ])


# ============================================================ s08 scenarios
def wrongbranch_anim():
    R = 23
    xs = [80, 220, 360, 500]
    hs = [('cc0faf8', 'Initial'), ('4b1828d', 'step 1'), ('6065f48', 'step 2'), ('91211b2', 'step 3')]
    e = [_title('Three commits on the wrong branch: two pointer moves fix it')]
    for i, (h, m) in enumerate(hs):
        e.append(_c(xs[i], 120, h, 'blue' if i == 0 else 'amber', r=R, sub='Export: ' + m if i else m))
    e += [_chain([(x, 120) for x in xs], r=R), _ref(80, 172, 'origin/main', 'gray'), _ref(500, 72, 'main', 'green'),
          stext(640, 116, 'git status -sb', 'amber', 11, step=1), stext(640, 132, '[ahead 3] — not pushed', 'amber', 11, step=1, bold=True),
          _ref(500, 172, 'feature/attendance-export', 'purple', step=2),
          stext(380, 214, 'git branch feature/attendance-export  (keeps the commits)', 'purple', 11, step=2),
          _hide(470, 60, 60, 24, 3), _ref(80, 72, 'main', 'green', step=3), sarrow(470, 72, 112, 72, 'green', step=3),
          stext(380, 240, 'git reset --hard origin/main  (main back to cc0faf8)', 'green', 11, step=3),
          _codebox(40, 262, 680, 54, ['$ git push -u origin feature/attendance-export && git branch -vv',
                                      '* feature/attendance-export 91211b2 [origin/feature/attendance-export]   ·   main cc0faf8 [origin/main]'], 'cyan', step=4, size=10),
          stext(380, 340, 'already pushed to main? do not reset — revert on main and continue on a branch', 'red', 11, step=5)]
    return anim(canvas(760, 356, *e), [
        'Three export commits were made on main by mistake. git status -sb shows they are not pushed yet.',
        'Create the feature branch at the current commit; now a branch keeps the work safe.',
        'Move main back to origin/main. Nothing was copied — the commits simply belong to the feature branch now.',
        'Push the branch with an upstream and open a pull request as usual.',
        'Rewriting is only safe because nobody else had these commits.',
    ])


def revertmerge_anim():
    R = 21
    P = {'cc0faf8': (60, 80), '96c77e0': (150, 160), '894eb1e': (240, 160), 'd541558': (300, 80), '6794014': (400, 80),
         '105c71d': (480, 160), '54802d5': (560, 80), 'ef4cb35': (680, 80)}
    e = [_title('Reverting a pushed merge — and bringing the feature back'),
         _c(*P['cc0faf8'], 'cc0faf8', 'blue', r=R),
         _c(*P['96c77e0'], '96c77e0', 'purple', r=R), _c(*P['894eb1e'], '894eb1e', 'red', r=R),
         _e(*P['cc0faf8'], *P['96c77e0'], r=R), _e(*P['96c77e0'], *P['894eb1e'], r=R),
         _c(*P['d541558'], 'd541558', 'green', r=R), _e(*P['cc0faf8'], *P['d541558'], r=R), _e(*P['894eb1e'], *P['d541558'], r=R),
         stext(195, 204, 'feature/grading (BROKEN = 1/0)', 'red', 10), stext(300, 50, 'merge, pushed', 'green', 10),
         _c(*P['6794014'], '6794014', 'amber', r=R, step=1), _e(*P['d541558'], *P['6794014'], step=1, r=R),
         stext(400, 50, 'revert -m 1', 'amber', 10, step=1, bold=True),
         stext(380, 240, 'parent 1 = mainline (cc0faf8 side); grading.py removed, history kept', 'amber', 11, step=1),
         _c(*P['105c71d'], '105c71d', 'purple', r=R, step=2), _e(*P['894eb1e'], *P['105c71d'], step=2, r=R),
         stext(480, 204, 'Fix grading wiring', 'purple', 10, step=2),
         _codebox(40, 256, 330, 54, ['$ git merge feature/grading', 'CONFLICT (modify/delete): grading.py …'], 'red', step=3, size=10),
         stext(205, 330, 'old commits count as merged: only the fix comes in', 'red', 10, step=3),
         _c(*P['54802d5'], '54802d5', 'amber', r=R, step=4), _e(*P['6794014'], *P['54802d5'], step=4, r=R),
         stext(560, 50, 'Reapply (revert the revert)', 'amber', 10, step=4, bold=True),
         _c(*P['ef4cb35'], 'ef4cb35', 'green', r=R, step=5), _e(*P['54802d5'], *P['ef4cb35'], step=5, r=R), _e(*P['105c71d'], *P['ef4cb35'], step=5, r=R),
         _codebox(400, 256, 330, 54, ['$ git merge feature/grading → clean', "grading.py: def grade(m): return 'P' if …"], 'green', step=5, size=10),
         stext(565, 330, 'feature back, with the fix', 'green', 10, step=5)]
    return anim(canvas(760, 344, *e), [
        'The merge d541558 is already pushed. git revert -m 1 creates 6794014, undoing everything the merge brought relative to the mainline parent.',
        'The team fixes the bug on the feature branch (105c71d).',
        'Merging again does not restore grading.py: its original commits are already ancestors of main, so only the fix is merged — and it conflicts with the deletion. Abort.',
        'Reverting the revert (54802d5, "Reapply …") brings the original changes back.',
        'Now the merge brings in just the fix and completes cleanly (ef4cb35).',
    ])


def lease_anim():
    R = 21
    e = [_title('--force-with-lease refuses to overwrite work you have not seen'),
         sbox(20, 44, 340, 150, 'server: feature/report', '', 'purple', top=True, size=12, fill_opacity=0.08),
         sbox(400, 44, 340, 150, "Asha's clone", '', 'blue', top=True, size=12, fill_opacity=0.08),
         _c(60, 120, 'cc0faf8', 'blue', r=R), _c(160, 120, '3e3adb0', 'blue', r=R, sub='Report draft'), _e(60, 120, 160, 120, r=R),
         _c(270, 120, '50800ac', 'amber', r=R, step=1, sub='Ravi: totals'), _e(160, 120, 270, 120, step=1, r=R),
         _c(440, 120, 'cc0faf8', 'blue', r=R), _c(540, 90, '3e3adb0', 'gray', r=R), _e(440, 120, 540, 90, r=R),
         _ref(630, 90, 'origin/… (stale)', 'gray', step=2),
         _c(540, 160, '1cfe231', 'blue', r=R, step=2), _e(440, 120, 540, 160, step=2, r=R), stext(620, 164, 'amended', 'blue', 10, 'start', step=2),
         _codebox(40, 210, 680, 40, [' ! [rejected]  feature/report -> feature/report (stale info)   ← remote is 50800ac, lease expected 3e3adb0'], 'red', step=3, size=10),
         stext(380, 270, 'plain --force here would have deleted Ravi\'s 50800ac', 'red', 11, step=3, bold=True),
         _c(160, 320, '1cfe231', 'blue', r=R, step=4, sub='reworded'), _c(300, 320, '9d9c4d8', 'amber', r=R, step=4, sub='Ravi: totals (picked)'),
         _c(40, 320, 'cc0faf8', 'blue', r=R, step=4), _e(40, 320, 160, 320, step=4, r=R), _e(160, 320, 300, 320, step=4, r=R),
         stext(560, 312, 'git fetch → cherry-pick origin/feature/report', 'amber', 11, step=4),
         stext(560, 336, 'push --force-with-lease → accepted ✔', 'green', 12, step=5, bold=True),
         stext(560, 354, 'lease now matches what is on the server', 'green', 10, step=5)]
    return anim(canvas(760, 372, *e), [
        'Asha pushed "Report draft"; Ravi then pushed a commit on top of it.',
        'Without fetching, Asha amends her commit. Her origin/feature/report still says 3e3adb0 — stale.',
        '--force-with-lease only overwrites if the remote is where you last saw it. It moved, so the push is rejected instead of deleting Ravi\'s work.',
        'She fetches, sees his commit and cherry-picks it on top of her reworded commit.',
        'Now the lease matches and the rewritten branch is pushed safely, keeping both changes.',
    ])


def autosquash_anim():
    R = 21
    e = [_title('fixup! commits + rebase --autosquash onto the latest main'),
         _c(60, 110, 'cc0faf8', 'blue', r=R), _c(170, 60, 'bdcaeb2', 'blue', r=R, sub='Add FAQ (main)'), _e(60, 110, 170, 60, r=R)]
    br = [('83ae91a', 'chart', 'purple'), ('9571c0d', 'legend', 'purple'), ('018cf5e', 'fixup! chart', 'amber'), ('ee31f74', 'fixup! legend', 'amber')]
    for i, (h, m, c) in enumerate(br):
        x = 170 + i * 110
        e += [_c(x, 160, h, c, r=R, sub=m), _e(60 if i == 0 else x - 110, 110 if i == 0 else 160, x, 160, r=R)]
    e += [_ref(590, 160, 'feature/chart', 'purple'),
          stext(380, 222, 'git commit --fixup=HEAD~1 names the target in the message', 'amber', 11, step=1),
          _codebox(40, 240, 330, 86, ['pick   83ae91a Add attendance chart', 'fixup  018cf5e fixup! Add attendance chart', 'pick   9571c0d Add chart legend',
                                      'fixup  ee31f74 fixup! Add chart legend'], 'amber', step=2, size=10),
          stext(205, 344, '--autosquash reorders the todo list', 'amber', 10, step=2),
          _c(450, 280, 'bdcaeb2', 'blue', r=R, step=3), _c(560, 280, '0f47e12', 'green', r=R, step=3, sub='Add attendance chart'),
          _c(670, 280, '17cbb5d', 'green', r=R, step=3, sub='Add chart legend'), _e(450, 280, 560, 280, step=3, r=R), _e(560, 280, 670, 280, step=3, r=R),
          stext(560, 244, 'two clean commits on current main', 'green', 11, step=3, bold=True),
          stext(560, 344, 'push -u --force-with-lease → open the PR', 'cyan', 11, step=4)]
    return anim(canvas(760, 360, *e), [
        'While working, small corrections were committed as fixup! commits, and main gained a commit (Add FAQ) in the meantime.',
        'git rebase -i --autosquash origin/main generates a todo list that moves each fixup right after its target and marks it fixup.',
        'The branch is replayed on top of the latest main: four commits become two, each including its correction.',
        'Push the rewritten private branch with --force-with-lease and open the pull request.',
    ])


def restore_anim():
    R = 21
    hs = [('dddd611', 'Add timetable gen.', 'blue'), ('6617fee', 'Update notes', 'green'), ('0430d1e', 'Clean up scripts', 'red'),
          ('7a5cdf8', 'notes 1', 'gray'), ('1cd574b', 'notes 2', 'gray'), ('774b516', 'notes 3', 'gray')]
    e = [_title('Find the commit that deleted a file, restore it from its parent')]
    for i, (h, m, c) in enumerate(hs):
        e.append(_c(70 + i * 120, 100, h, c, r=R, sub=m, focus='2' if i == 2 else ('3' if i == 1 else None)))
    e += [_chain([(70 + i * 120, 100) for i in range(6)], r=R), _ref(670, 56, 'main', 'green'),
          stext(130, 62, 'timetable_generator.py exists', 'blue', 10, step=1),
          stext(310, 62, 'deleted here', 'red', 10, step=1, bold=True),
          _codebox(30, 166, 340, 54, ['$ git log --diff-filter=D --oneline -- timetable_generator.py', '0430d1e Clean up unused scripts'], 'red', step=2, size=10),
          sarrow(300, 136, 212, 136, 'green', step=3), stext(256, 152, '0430d1e^ (parent)', 'green', 11, step=3, bold=True),
          _codebox(400, 166, 330, 54, ['$ git show 0430d1e^:timetable_generator.py', 'def make_timetable(batch): …'], 'green', step=3, size=10),
          _codebox(30, 238, 700, 54, ['$ git restore --source=0430d1e^ --staged --worktree -- timetable_generator.py', 'A  timetable_generator.py'], 'amber', step=4, size=10),
          _c(670, 320, '5db9412', 'green', r=R, step=5), stext(560, 324, 'Restore timetable generator', 'green', 11, step=5),
          stext(300, 324, 'git log --all --diff-filter=D --name-only: unknown names', 'cyan', 10, step=5)]
    return anim(canvas(760, 352, *e), [
        'The file existed until commit 0430d1e removed it; three more commits followed.',
        '--diff-filter=D shows only commits in which the path was deleted.',
        'The last good version is in the parent of the deleting commit (0430d1e^); git show prints it without touching the working tree.',
        'git restore --source=0430d1e^ brings it back; --staged also stages it (otherwise it would be untracked).',
        'Commit the restored file. With an unknown name, list all deleted files with --name-only.',
    ])
