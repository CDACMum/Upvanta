"""Runs Git examples for real (git 2.43, bash 5, Ubuntu 24.04) and caches the transcript in _gitcache/.

gitrun(script, files=..., user='student')  -> code block + terminal transcript.
  Each complete command is echoed as '$ cmd' followed by its output, like a real terminal.
  Lines starting with '!' are hidden setup (run, not shown).
Every example starts in a fresh /home/student (work folder ~/cdac) with a fixed ~/.gitconfig (user Asha Patil, branch main);
each git command runs one simulated minute after the previous one from 14 Oct 2026 09:00, so hashes are reproducible. While the script is unchanged the cache is used; re-running needs Linux
with git and a user called 'student' (run the build as root).
"""
import hashlib, json, os, pathlib, shutil, subprocess, textwrap
from build import code, output

CACHE = pathlib.Path(__file__).resolve().parent.parent / '_gitcache'
WORK = '/home/student/cdac'

GITCONFIG = '''[user]
	name = Asha Patil
	email = asha@cdac.example
[init]
	defaultBranch = main
[core]
	pager = cat
[color]
	ui = false
[pull]
	rebase = false
'''

# fixed start time; every git command below moves the clock one minute, so hashes are reproducible
GIT_ENV = {}


def _clean(s):
    return textwrap.dedent(s).strip('\n')


def _complete(text):
    r = subprocess.run(['bash', '-n'], input=text + '\n', capture_output=True, text=True)
    return r.returncode == 0 and 'here-document' not in r.stderr


def _chunks(src):
    """Split a script into complete commands (multi-line constructs stay together)."""
    out, cur = [], []
    for ln in src.splitlines():
        if not cur and not ln.strip():
            continue
        cur.append(ln)
        if ln.rstrip().endswith('\\'):
            continue
        text = '\n'.join(cur)
        if _complete(text[1:] if text.startswith('!') else text):
            out.append(text)
            cur = []
    if cur:
        out.append('\n'.join(cur))
    return out


def _wrap(src):
    # ls prints columns only when writing to the transcript (a regular file), like a terminal; plain in pipes
    lines = ['exec 2>&1', 'shopt -s expand_aliases',
             # simulated clock: each git command runs one minute after the previous one (from 14 Oct 2026 09:00 IST)
             '_gm=0; git() { _gm=$((_gm+1)); local d; d=$(printf "2026-10-14T%02d:%02d:00+05:30" $((9 + _gm / 60)) $((_gm % 60))); '
             'GIT_AUTHOR_DATE=$d GIT_COMMITTER_DATE=$d command git "$@"; }; export -f git 2>/dev/null; tick() { :; }',
             'ls() { if [ -f /proc/self/fd/1 ]; then command ls -C -T 0 "$@"; else command ls "$@"; fi; }']
    for ch in _chunks(src):
        hidden = ch.startswith('!')
        body = ch[1:] if hidden else ch
        if not hidden and not body.lstrip().startswith('#'):
            shown = body.replace('\n', '\n> ')
            lines.append("printf '%s\\n' " + _q('$ ' + shown))
        lines.append(body)
    return '\n'.join(lines) + '\n'


def _q(s):
    return "'" + s.replace("'", "'\\''") + "'"


def run(src, files=None, user='student', allow_fail=True, env=None):
    src = _clean(src)
    key = hashlib.sha256(json.dumps([GITCONFIG, GIT_ENV, src, files or {}, user, env or {}], sort_keys=True).encode()).hexdigest()[:16]
    cf = CACHE / f'{key}.json'
    if cf.exists():
        return json.loads(cf.read_text())['out']
    if os.geteuid() != 0 and not os.environ.get('LINUX_RUN'):
        raise RuntimeError('shell example not cached; run the build as root on Linux to execute it:\n' + src)
    shutil.rmtree('/home/student', ignore_errors=True)        # fresh home for every example
    shutil.copytree('/etc/skel', '/home/student')
    pathlib.Path('/home/student/.gitconfig').write_text(GITCONFIG)
    os.makedirs(WORK)
    for name, content in (files or {}).items():
        p = pathlib.Path(WORK) / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_clean(content) + '\n')
    subprocess.run(['chown', '-R', 'student:student', '/home/student'])
    script = pathlib.Path('/tmp/upv_git_script.sh')
    script.write_text(_wrap(src))
    script.chmod(0o755)
    base_env = {'HOME': f'/home/{user}' if user != 'root' else '/root', 'USER': user, 'LOGNAME': user,
                'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8',
                'TZ': 'Asia/Kolkata', 'TERM': 'dumb', 'SHELL': '/bin/bash', 'COLUMNS': '100'}
    base_env.update(GIT_ENV)
    base_env.update(env or {})
    cmd = ['bash', '--noprofile', '--norc', str(script)]
    if user != 'root':
        cmd = ['runuser', '-u', user, '--'] + cmd
    outfile = pathlib.Path('/tmp/upv_git_out.txt')
    with open(outfile, 'w') as fh:
        subprocess.run(cmd, cwd=WORK, env=base_env, stdout=fh, stderr=subprocess.STDOUT, timeout=120)
    import re
    out = re.sub(r'(?m)^' + re.escape(str(script)) + r': line \d+: ', 'bash: ', outfile.read_text().rstrip('\n'))
    out = out.replace(str(script), 'bash')
    out = re.sub(r'(?m)^ {20,}$', '', out)                       # progress-clearing lines from rebase
    out = re.sub(r'\n\n\n+', '\n\n', out)
    CACHE.mkdir(exist_ok=True)
    cf.write_text(json.dumps({'src': src, 'out': out}, indent=1))
    return out


def gitrun(src, files=None, title='Commands (git · bash)', user='student', env=None, show_code=True, out_title='Terminal'):
    """Transcript of a real run. show_code=True also shows the script as a code block."""
    out = run(src, files, user, env=env)
    shown = '\n'.join(l[1:] if l.startswith('!') else l for l in _clean(src).splitlines() if not l.startswith('!'))
    parts = []
    if show_code:
        parts.append(code(shown, title, 'fa-terminal'))
    parts.append(output(out, out_title + (' (as root)' if user == 'root' else '')))
    return ''.join(parts)


def sh(src, title='Shell'):
    """Shown, not executed."""
    return code(_clean(src), title, 'fa-terminal')


def script_file(name, content, title=None):
    """Show a script file's content as a code block (pass the same text in files= to run it)."""
    return code(_clean(content), title or name, 'fa-file-code')
