"""Upvanta module page builder.

Usage: python build.py rdbms   -> writes out/rdbms.html
Each module lives in <module>/ with a meta.py (TITLE, ICON, PAGE_TITLE) and
sNN_*.py files, each defining SECTION = dict(level=..., title=..., questions=[...]).
"""
import html, importlib, pathlib, sys, re

ROOT = pathlib.Path(__file__).parent

# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(s, quote=False)

def p(s, top=False):
    st = ' style="margin-top: 1rem;"' if top else ''
    return f'<p{st}>{s}</p>'

def defbox(*paras):
    inner = ''.join(p(x, i > 0) for i, x in enumerate(paras))
    return f'<div class="definition-box">{inner}</div>'

def hl(s, label=None):
    lab = f'<strong>{label}:</strong> ' if label else ''
    return f'<div class="highlight-box">{lab}{s}</div>'

def note(s, label='Note'):
    return f'<div class="note-box"><strong>{label}:</strong> {s}</div>'

def warn(s, label='Common Mistake'):
    return f'<div class="warning-box"><strong>{label}:</strong> {s}</div>'

def tags(*items):
    t = ''.join(f'<span class="keyword-tag"><i class="fas fa-tag"></i> {x}</span>' for x in items)
    return f'<div class="keyword-tags">{t}</div>'

def ul(*items):
    return '<ul class="point-list">' + ''.join(f'<li>{x}</li>' for x in items) + '</ul>'

def table(headers, rows, caption=None):
    th = ''.join(f'<th>{h}</th>' for h in headers)
    trs = ''
    for r in rows:
        tds = ''.join(f'<td>{"<strong>"+c+"</strong>" if i == 0 else c}</td>' for i, c in enumerate(r))
        trs += f'<tr>{tds}</tr>'
    cap = f'<p class="table-caption">{caption}</p>' if caption else ''
    return f'<div class="table-container"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>{cap}'

def code(src, title='SQL', icon='fa-database'):
    src = src.strip('\n')
    return (f'<div class="example-box"><div class="example-header">'
            f'<span class="example-title"><i class="fas {icon}"></i> {title}</span>'
            f'<button class="copy-btn" onclick="copyCode(this)"><i class="fas fa-copy"></i> Copy</button>'
            f'</div><pre><code>{esc(src)}</code></pre></div>')

def output(src, title='Output'):
    src = src.strip('\n')
    return (f'<div class="output-box"><div class="output-title"><i class="fas fa-terminal"></i> {title}</div>'
            f'<pre>{esc(src)}</pre></div>')

import subprocess, textwrap
def pyrun(src, title='Python', expect_error=False):
    """Code block + real output captured by executing the code at build time."""
    src = textwrap.dedent(src).strip('\n')
    r = subprocess.run(['python3', '-c', src], capture_output=True, text=True, timeout=60, cwd='/tmp')
    out = r.stdout.rstrip('\n')
    if r.returncode != 0:
        last = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'error'
        if not expect_error:
            raise RuntimeError(f'Example failed: {last}\n---\n{src}')
        out = (out + '\n' if out else '') + last
    return code(src, title, 'fa-brands fa-python') + (output(out) if out else '')

_sql_counter = [0]
def sqlrun(src, title='SQL (MySQL)', expect_error=False, show_output=True, setup=''):
    """SQL block + real output from executing it on a fresh MySQL-compatible database.
    setup: SQL run first but not shown (e.g. shared sample tables)."""
    src = textwrap.dedent(src).strip('\n')
    _sql_counter[0] += 1
    db = 'upvanta'   # one fresh database per example, dropped afterwards
    script = f'DROP DATABASE IF EXISTS {db}; CREATE DATABASE {db}; USE {db};\n'
    if setup:
        r0 = subprocess.run(['mysql', '-uroot'], input=script + setup,
                            capture_output=True, text=True, timeout=60)
        if r0.stderr.strip():
            raise RuntimeError(f'SQL setup failed: {r0.stderr}')
        script = f'USE {db};\n'
    script += src
    r = subprocess.run(['mysql', '-uroot', '-t', '--force'], input=script, capture_output=True, text=True, timeout=60)
    errs = [l for l in r.stderr.splitlines() if l.startswith('ERROR')]
    if errs and not expect_error:
        raise RuntimeError(f'SQL example failed: {errs}\n---\n{src}')
    out = r.stdout.rstrip('\n')
    if errs:
        out = (out + '\n' if out else '') + '\n'.join(e.split(' at line ')[0] + ':' + e.split(':', 1)[1] if ' at line ' in e else e for e in errs)
    subprocess.run(['mysql', '-uroot', '-e', f'DROP DATABASE IF EXISTS {db}'])
    return code(src, title) + (output(out) if out and show_output else '')

def py(src, title='Python'):
    """Code block without execution (fragments, files, network)."""
    return code(textwrap.dedent(src), title, 'fa-brands fa-python')

def cross(*pairs):
    items = ''
    for q, a in pairs:
        items += (f'<div class="cross-question-item"><div class="cross-question-text">'
                  f'<i class="fas fa-arrow-right"></i><span><strong>{q}</strong></span></div>'
                  f'<div class="cross-answer">{a}</div></div>')
    return f'<div class="cross-questions">{items}</div>'

def scenario(title, body):
    return f'<div class="scenario-box"><div class="scenario-title"><i class="fas fa-briefcase"></i> {title}</div>{body}</div>'

def compare(*cards):
    c = ''.join(f'<div class="comparison-card"><h4>{t}</h4>{b}</div>' for t, b in cards)
    return f'<div class="comparison-grid">{c}</div>'

def svg(markup, caption):
    return f'<div class="image-container">{markup.strip()}<p class="image-caption">{caption}</p></div>'

# ---------------------------------------------------------------- animated diagrams
_svg_id = [0]
PALETTE = {'blue': '#0ea5e9', 'green': '#10b981', 'amber': '#f59e0b', 'purple': '#8b5cf6',
           'red': '#ef4444', 'pink': '#f472b6', 'gray': '#94a3b8', 'cyan': '#06b6d4'}

def _t(v):
    return str(v).replace('<', '&lt;').replace('>', '&gt;')

def _attrs(step=None, focus=None):
    a = ''
    if step is not None:
        a += f' data-step="{step}"'
    if focus is not None:
        a += f' data-focus="{focus}"'
    return a

def sbox(x, y, w, h, title, sub='', color='blue', step=None, focus=None, fill_opacity=0.22, size=13, top=False):
    c = PALETTE.get(color, color)
    lines = sub.split('\n') if sub else []
    ty = y + h / 2 + (4 if not lines else -6 * len(lines) + 2)
    if top:
        ty = y + 20
    t = (f'<text x="{x + w/2}" y="{ty}" font-size="{size}" fill="#f1f5f9" text-anchor="middle" font-weight="bold">{_t(title)}</text>')
    for i, ln in enumerate(lines):
        t += f'<text x="{x + w/2}" y="{ty + 16 + i*14}" font-size="11" fill="#cbd5e1" text-anchor="middle">{_t(ln)}</text>'
    return (f'<g class="sbox"{_attrs(step, focus)}><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#1e293b"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" '
            f'fill="{c}" fill-opacity="{fill_opacity}" stroke="{c}" stroke-width="2"/>{t}</g>')

def stext(x, y, text, color='#cbd5e1', size=12, anchor='middle', step=None, focus=None, bold=False):
    c = PALETTE.get(color, color)
    fw = ' font-weight="bold"' if bold else ''
    text = _t(text)
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" text-anchor="{anchor}"{fw}{_attrs(step, focus)}>{text}</text>'

def sarrow(x1, y1, x2, y2, color='gray', step=None, dashed=False, mid=None):
    c = PALETTE.get(color, color)
    d = f'M {x1} {y1} Q {mid[0]} {mid[1]} {x2} {y2}' if mid else f'M {x1} {y1} L {x2} {y2}'
    dash = ' stroke-dasharray="6,5"' if dashed else ''
    return (f'<path d="{d}" stroke="{c}" stroke-width="2" fill="none"{dash} marker-end="url(#MARK)"{_attrs(step)}/>')

def sflow(x1, y1, x2, y2, color='cyan', step=None, dur=1.6, count=3, mid=None, r=5):
    """Dots travelling along a path to show data moving."""
    c = PALETTE.get(color, color)
    d = f'M {x1} {y1} Q {mid[0]} {mid[1]} {x2} {y2}' if mid else f'M {x1} {y1} L {x2} {y2}'
    dots = ''.join(
        f'<circle r="{r}" fill="{c}" opacity="0.95"><animateMotion dur="{dur}s" begin="{i * dur / count:.2f}s" '
        f'repeatCount="indefinite" path="{d}"/></circle>' for i in range(count))
    return f'<g class="sflow"{_attrs(step)}>{dots}</g>'

def scell(x, y, w, h, text, color='#334155', tcolor='#e2e8f0', step=None, focus=None, bold=False, size=12):
    fw = ' font-weight="bold"' if bold else ''
    return (f'<g{_attrs(step, focus)} class="scell"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" stroke="#1e293b"/>'
            f'<text x="{x + w/2}" y="{y + h/2 + 4}" font-size="{size}" fill="{tcolor}" text-anchor="middle"{fw}>{_t(text)}</text></g>')

def stable(x, y, headers, rows, widths, h=26, step=None, focus_rows=None, title=None, title_color='blue', row_steps=None):
    """Small table. focus_rows: {row_index: 'steps'}; row_steps: {row_index: step}"""
    out = []
    if title:
        out.append(stext(x + sum(widths) / 2, y - 8, title, PALETTE.get(title_color, title_color), 13, bold=True))
    cx = x
    for hd, w in zip(headers, widths):
        out.append(scell(cx, y, w, h, hd, PALETTE.get(title_color, title_color), '#fff', bold=True))
        cx += w
    for ri, row in enumerate(rows):
        cx = x
        rs = (row_steps or {}).get(ri)
        fr = (focus_rows or {}).get(ri)
        cells = ''
        for val, w in zip(row, widths):
            cells += scell(cx, y + h * (ri + 1), w, h, val, '#0f172a' if ri % 2 else '#162033')
            cx += w
        out.append(f'<g class="srow"{_attrs(rs, fr)}>{cells}</g>')
    return f'<g{_attrs(step)}>' + ''.join(out) + '</g>'

def canvas(w, h, *elems):
    _svg_id[0] += 1
    mid = f'mk{_svg_id[0]}'
    body = ''.join(elems).replace('url(#MARK)', f'url(#{mid})')
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Inter, sans-serif"><rect width="{w}" height="{h}" fill="#1e293b"/>'
            f'<defs><marker id="{mid}" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">'
            f'<path d="M0,0 L0,6 L9,3 z" fill="#94a3b8"/></marker></defs>{body}</svg>')

def anim(svg_markup, steps, title='How It Works — Step by Step'):
    """Interactive step-by-step animated diagram with synced explanation."""
    items = ''.join(f'<li><span class="anim-num">{i + 1}</span><span>{s}</span></li>' for i, s in enumerate(steps))
    return card(title, 'fa-film',
        f'<div class="anim-box" data-steps="{len(steps)}">'
        f'<div class="anim-stage">{svg_markup}</div>'
        f'<div class="anim-controls">'
        f'<button class="anim-btn" data-act="prev" title="Previous step"><i class="fas fa-backward-step"></i> Prev</button>'
        f'<button class="anim-btn anim-play" data-act="play" title="Play"><i class="fas fa-play"></i> Play</button>'
        f'<button class="anim-btn" data-act="next" title="Next step">Next <i class="fas fa-forward-step"></i></button>'
        f'<button class="anim-btn" data-act="reset" title="Restart"><i class="fas fa-rotate-left"></i> Restart</button>'
        f'<span class="anim-counter">Step 1 / {len(steps)}</span></div>'
        f'<ol class="anim-steps">{items}</ol></div>')

def card(title, icon, *parts):
    return (f'<div class="content-card"><div class="section-title"><i class="fas {icon}"></i> {title}</div>'
            + ''.join(parts) + '</div>')

# standard card shortcuts
def definition(*parts, title='Definition'):            return card(title, 'fa-book', *parts)
def explanation(*parts, title='Detailed Explanation'): return card(title, 'fa-lightbulb', *parts)
def example(*parts, title='Example'):                  return card(title, 'fa-code', *parts)
def comparison(*parts, title='Comparison'):            return card(title, 'fa-scale-balanced', *parts)
def visual(*parts, title='Visual Understanding'):      return card(title, 'fa-image', *parts)
def real_world(*parts, title='Real-World Scenario'):   return card(title, 'fa-briefcase', *parts)
def interview(*parts, title='Interview Tip'):          return card(title, 'fa-user-tie', *parts)
def crossq(*pairs):       return card('Cross Questions', 'fa-question-circle', cross(*pairs))


def analogy(text, title='Analogy'):
    """Everyday comparison that makes the concept click."""
    return card(title, 'fa-people-arrows',
                f'<div class="analogy-box"><i class="fas fa-quote-left"></i><div>{text}</div></div>')

def steps(*items, title='Steps to Create'):
    """Numbered how-to steps; each item is (heading, detail_html) or a plain string."""
    lis = ''
    for it in items:
        if isinstance(it, tuple):
            lis += f'<li><div class="how-step-h">{it[0]}</div><div class="how-step-d">{it[1]}</div></li>'
        else:
            lis += f'<li><div class="how-step-d">{it}</div></li>'
    return card(title, 'fa-list-ol', f'<ol class="how-steps">{lis}</ol>')

def Q(title, short, cards, minutes=6, tag='Concept'):
    return dict(title=title, short=short, cards=cards, minutes=minutes, tag=tag)

# ---------------------------------------------------------------- page
LEVELS = {'beginner': 'Beginner', 'basic': 'Basic', 'intermediate': 'Intermediate',
          'advanced': 'Advanced', 'expert': 'Expert'}

EXTRA_CSS = """
        .badge-beginner { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
        .badge-basic { background: rgba(14, 165, 233, 0.2); color: #38bdf8; border: 1px solid #0ea5e9; }
        .back-link { display: inline-flex; align-items: center; gap: 0.5rem; color: var(--text-secondary);
            text-decoration: none; font-size: 0.9rem; padding: 0.5rem 1rem; border: 1px solid var(--border-color);
            border-radius: 25px; background: var(--card-bg); transition: all 0.2s ease; }
        .back-link:hover { color: var(--primary-color); border-color: var(--primary-color); }
        .logo-wrap { display: flex; align-items: center; gap: 1.25rem; }
        .point-list { margin: 0.75rem 0 0.75rem 1.5rem; color: var(--text-secondary); line-height: 1.8; }
        .point-list li { margin-bottom: 0.35rem; }
        .point-list strong, .content-card p strong { color: var(--text-primary); }
        .content-card > p { color: var(--text-secondary); line-height: 1.8; margin-bottom: 1rem; }
        .output-box { background: #0b1220; border: 1px solid var(--border-color); border-left: 4px solid var(--success-color);
            border-radius: 8px; margin: 1rem 0; overflow-x: auto; }
        .output-title { padding: 0.5rem 1rem; font-size: 0.85rem; color: var(--success-color); border-bottom: 1px solid var(--border-color); }
        .output-box pre { margin: 0; padding: 1rem; background: transparent; font-family: 'Fira Code', monospace; font-size: 0.85rem; color: #cbd5e1; }
        .table-caption { font-size: 0.85rem; color: var(--text-secondary); text-align: center; margin-top: 0.5rem; }
        .comparison-card h4 { color: var(--primary-color); margin-bottom: 0.75rem; }
        .comparison-card ul { margin-left: 1.25rem; color: var(--text-secondary); line-height: 1.8; }
        .image-container svg { max-width: 100%; height: auto; }
        .point-list code, .definition-box code, .highlight-box code, .note-box code, .warning-box code, .cross-answer code, td code { overflow-wrap: anywhere; }
        .anim-box { margin-top: 0.5rem; }
        .anim-stage { background: #1e293b; border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; }
        .anim-stage svg { display: block; width: 100%; height: auto; }
        .anim-box [data-step] { opacity: 0; transition: opacity 0.6s ease; }
        .anim-box [data-step].on { opacity: 1; }
        .anim-box.no-js [data-step] { opacity: 1; }
        .anim-box .focus rect { stroke: #fbbf24 !important; stroke-width: 3 !important; }
        .anim-box .focus { filter: drop-shadow(0 0 6px rgba(251, 191, 36, 0.75)); }
        .anim-box text.focus { fill: #fde68a !important; }
        .anim-controls { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin: 0.9rem 0; }
        .anim-btn { background: var(--card-bg); color: var(--text-primary); border: 1px solid var(--border-color);
            border-radius: 8px; padding: 0.45rem 0.85rem; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }
        .anim-btn:hover { border-color: var(--primary-color); color: var(--primary-color); }
        .anim-btn:disabled { opacity: 0.4; cursor: not-allowed; }
        .anim-play { background: var(--primary-color); border-color: var(--primary-color); color: #fff; font-weight: 600; }
        .anim-play:hover { color: #fff; filter: brightness(1.1); }
        .anim-counter { margin-left: auto; color: var(--text-secondary); font-size: 0.85rem; }
        .anim-steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.5rem; }
        .anim-steps li { display: flex; gap: 0.75rem; align-items: flex-start; padding: 0.65rem 0.9rem; border-radius: 8px;
            border: 1px solid transparent; color: var(--text-secondary); opacity: 0.55; transition: all 0.3s; cursor: pointer; line-height: 1.6; }
        .anim-steps li.done { opacity: 0.8; }
        .anim-steps li.current { opacity: 1; color: var(--text-primary); background: rgba(14, 165, 233, 0.1);
            border-color: rgba(14, 165, 233, 0.45); }
        .anim-num { flex: 0 0 26px; height: 26px; border-radius: 50%; background: var(--border-color); color: #fff;
            display: inline-flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; }
        .anim-steps li.current .anim-num { background: var(--primary-color); }
        .anim-steps li code { overflow-wrap: anywhere; }
        @media (prefers-reduced-motion: reduce) { .anim-box [data-step] { transition: none; } }
        @media (max-width: 768px) {
            .anim-stage { overflow-x: auto; -webkit-overflow-scrolling: touch; }
            .anim-stage svg { min-width: 620px; }
            .anim-counter { margin-left: 0; width: 100%; }
        }
        .analogy-box { display: flex; gap: 1rem; align-items: flex-start; background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.35); border-left: 4px solid #8b5cf6; border-radius: 10px;
            padding: 1rem 1.25rem; color: var(--text-secondary); line-height: 1.8; }
        .analogy-box > i { color: #a78bfa; font-size: 1.2rem; margin-top: 0.3rem; }
        .analogy-box strong { color: var(--text-primary); }
        .how-steps { list-style: none; counter-reset: hs; margin: 0; padding: 0; display: grid; gap: 0.75rem; }
        .how-steps li { counter-increment: hs; position: relative; padding: 0.75rem 1rem 0.75rem 3.25rem;
            background: rgba(14, 165, 233, 0.06); border: 1px solid var(--border-color); border-radius: 10px; }
        .how-steps li::before { content: counter(hs); position: absolute; left: 0.9rem; top: 0.75rem; width: 28px; height: 28px;
            border-radius: 50%; background: var(--primary-color); color: #fff; font-weight: 700; font-size: 0.85rem;
            display: flex; align-items: center; justify-content: center; }
        .how-step-h { color: var(--text-primary); font-weight: 600; margin-bottom: 0.25rem; }
        .how-step-d { color: var(--text-secondary); line-height: 1.7; }
        .how-step-d code, .analogy-box code { overflow-wrap: anywhere; }
        .question-item.hidden-by-search { display: none !important; }
        .search-count { font-size: 0.8rem; color: var(--text-secondary); padding: 0.75rem 1.25rem; display: none; }
        .search-count.show { display: block; }
        @media (max-width: 768px) {
            .back-link span { display: none; }
            .back-link { padding: 0.5rem 0.75rem; }
            .logo-wrap { gap: 0.75rem; min-width: 0; }
            .logo-wrap { flex: 1; overflow: hidden; }
            .header-actions { flex-shrink: 0; margin-left: 0.5rem; }
            .logo { font-size: 1rem; gap: 0.5rem; white-space: nowrap; min-width: 0; }
            .logo span { overflow: hidden; text-overflow: ellipsis; }
            .logo i { font-size: 1.25rem; }
            .progress-bar-mini { width: 50px; }
            .question-meta { gap: 0.5rem; }
        }
"""

JS = r"""
    <script>
        const STORAGE_KEY = 'upvanta-progress-__MODULE__';
        const questionIds = Array.from(document.querySelectorAll('.question-content')).map(el => el.id);
        const totalQuestions = questionIds.length;
        let currentQuestion = questionIds[0];
        let completedQuestions = new Set();

        function loadProgress() {
            try {
                const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
                saved.forEach(id => { if (questionIds.includes(id)) completedQuestions.add(id); });
            } catch (e) { /* storage unavailable */ }
        }
        function saveProgress() {
            try { localStorage.setItem(STORAGE_KEY, JSON.stringify([...completedQuestions])); } catch (e) {}
        }

        document.addEventListener('DOMContentLoaded', function () {
            loadProgress();
            completedQuestions.forEach(id => {
                const item = document.querySelector(`[data-question="${id}"]`);
                if (item) item.classList.add('completed');
            });
            setupSidebar();
            setupCrossQuestions();
            setupSearch();
            setupScrollTop();
            setupAnimations();
            const fromHash = location.hash.replace(/^#\/?/, '');
            navigateToQuestion(questionIds.includes(fromHash) ? fromHash : questionIds[0], false);
            updateProgress();
        });

        function setupSidebar() {
            document.querySelectorAll('.difficulty-header').forEach(header => {
                header.addEventListener('click', function () {
                    this.classList.toggle('active');
                    this.nextElementSibling.classList.toggle('active');
                });
            });
            document.querySelectorAll('.question-item').forEach(item => {
                item.addEventListener('click', function () {
                    navigateToQuestion(this.getAttribute('data-question'));
                    if (window.innerWidth <= 1024) document.getElementById('sidebar').classList.remove('active');
                });
            });
        }

        function navigateToQuestion(questionId, markPrevious = true) {
            const selected = document.getElementById(questionId);
            if (!selected) return;
            if (markPrevious && currentQuestion && currentQuestion !== questionId) {
                completedQuestions.add(currentQuestion);
                const prevItem = document.querySelector(`[data-question="${currentQuestion}"]`);
                if (prevItem) prevItem.classList.add('completed');
                saveProgress();
            }
            document.querySelectorAll('.question-content').forEach(c => c.classList.remove('active'));
            selected.classList.add('active');
            currentQuestion = questionId;
            document.querySelectorAll('.question-item').forEach(i => i.classList.remove('active'));
            const activeItem = document.querySelector(`[data-question="${questionId}"]`);
            if (activeItem) {
                activeItem.classList.add('active');
                const list = activeItem.closest('.question-list');
                if (list && !list.classList.contains('active')) {
                    list.classList.add('active');
                    list.previousElementSibling.classList.add('active');
                }
            }
            history.replaceState(null, '', '#/' + questionId);
            window.scrollTo({ top: 0, behavior: markPrevious ? 'smooth' : 'auto' });
            updateProgress();
        }
        // hash is '#/qN' (not '#qN') so the browser does not jump past the fixed header
        if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

        function navigateQuestion(direction) {
            const idx = questionIds.indexOf(currentQuestion);
            const next = direction === 'next' ? idx + 1 : idx - 1;
            if (next >= 0 && next < questionIds.length) navigateToQuestion(questionIds[next]);
        }

        function setupCrossQuestions() {
            document.querySelectorAll('.cross-question-item').forEach(item => {
                item.addEventListener('click', function () { this.classList.toggle('active'); });
            });
        }

        // Search matches question titles AND full answer text
        function setupSearch() {
            const input = document.getElementById('searchInput');
            const counter = document.getElementById('searchCount');
            const index = {};
            questionIds.forEach(id => { index[id] = document.getElementById(id).textContent.toLowerCase(); });
            input.addEventListener('input', function (e) {
                const term = e.target.value.trim().toLowerCase();
                let shown = 0;
                document.querySelectorAll('.question-item').forEach(item => {
                    const id = item.getAttribute('data-question');
                    const match = !term || item.textContent.toLowerCase().includes(term) || index[id].includes(term);
                    item.classList.toggle('hidden-by-search', !match);
                    if (match) shown++;
                });
                document.querySelectorAll('.difficulty-section').forEach(sec => {
                    const any = sec.querySelectorAll('.question-item:not(.hidden-by-search)').length > 0;
                    sec.style.display = any ? '' : 'none';
                    if (term && any) {
                        sec.querySelector('.question-list').classList.add('active');
                        sec.querySelector('.difficulty-header').classList.add('active');
                    }
                });
                counter.textContent = term ? `${shown} question${shown === 1 ? '' : 's'} match "${term}"` : '';
                counter.classList.toggle('show', !!term);
            });
        }

        // Step-by-step animated diagrams
        function setupAnimations() {
            document.querySelectorAll('.anim-box').forEach(box => {
                const total = +box.dataset.steps;
                const items = Array.from(box.querySelectorAll('.anim-steps li'));
                const counter = box.querySelector('.anim-counter');
                const playBtn = box.querySelector('[data-act="play"]');
                const prevBtn = box.querySelector('[data-act="prev"]');
                const nextBtn = box.querySelector('[data-act="next"]');
                let step = 1, timer = null;
                function render() {
                    box.querySelectorAll('[data-step]').forEach(el => el.classList.toggle('on', +el.dataset.step <= step));
                    box.querySelectorAll('[data-focus]').forEach(el =>
                        el.classList.toggle('focus', el.dataset.focus.split(',').map(Number).includes(step)));
                    items.forEach((li, i) => { li.classList.toggle('current', i + 1 === step); li.classList.toggle('done', i + 1 < step); });
                    counter.textContent = `Step ${step} / ${total}`;
                    prevBtn.disabled = step === 1;
                    nextBtn.disabled = step === total;
                }
                function stop() { clearInterval(timer); timer = null; playBtn.innerHTML = '<i class="fas fa-play"></i> Play'; }
                function play() {
                    if (step === total) step = 1;
                    render();
                    playBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
                    timer = setInterval(() => { if (step < total) { step++; render(); } if (step === total) stop(); }, 3200);
                }
                playBtn.addEventListener('click', () => timer ? stop() : play());
                prevBtn.addEventListener('click', () => { stop(); if (step > 1) { step--; render(); } });
                nextBtn.addEventListener('click', () => { stop(); if (step < total) { step++; render(); } });
                box.querySelector('[data-act="reset"]').addEventListener('click', () => { stop(); step = 1; render(); });
                items.forEach((li, i) => li.addEventListener('click', () => { stop(); step = i + 1; render(); }));
                render();
            });
        }

        function setupScrollTop() {
            window.addEventListener('scroll', function () {
                document.getElementById('scrollTop').classList.toggle('visible', window.pageYOffset > 300);
            });
        }
        function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }); }

        function updateProgress() {
            const progress = (completedQuestions.size / totalQuestions) * 100;
            document.getElementById('progressFill').style.width = `${progress}%`;
            document.getElementById('progressText').textContent = `${Math.round(progress)}%`;
        }

        function toggleSidebar() { document.getElementById('sidebar').classList.toggle('active'); }

        function copyCode(button) {
            const code = button.closest('.example-box').querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                const original = button.innerHTML;
                button.innerHTML = '<i class="fas fa-check"></i> Copied!';
                button.style.background = 'var(--success-color)';
                button.style.color = 'white';
                setTimeout(() => { button.innerHTML = original; button.style.background = ''; button.style.color = ''; }, 2000);
            });
        }

        document.addEventListener('keydown', function (e) {
            if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
            if (e.key === 'ArrowRight') navigateQuestion('next');
            else if (e.key === 'ArrowLeft') navigateQuestion('prev');
        });
    </script>
"""


def build(module):
    mdir = ROOT / module
    sys.path.insert(0, str(ROOT))
    meta = importlib.import_module(f'{module}.meta')
    files = sorted(f.stem for f in mdir.glob('s[0-9][0-9]_*.py'))
    sections = [importlib.import_module(f'{module}.{f}').SECTION for f in files]

    css = (ROOT / 'base.css').read_text()
    sidebar, main = [], []
    n = 0
    flat = [(sec, q) for sec in sections for q in sec['questions']]
    total = len(flat)
    for sec in sections:
        lvl = sec['level']
        items = ''
        for q in sec['questions']:
            n += 1
            q['id'] = f'q{n}'
            q['n'] = n
            items += (f'<div class="question-item" data-question="q{n}"><span class="question-number">{n}</span>'
                      f'<span>{q["short"]}</span></div>\n')
        sidebar.append(
            f'<div class="difficulty-section"><div class="difficulty-header" data-section="{lvl}">'
            f'<div class="difficulty-title"><span class="difficulty-badge badge-{lvl}">{LEVELS[lvl]}</span>'
            f'<span>{sec["title"]}</span></div><i class="fas fa-chevron-down"></i></div>'
            f'<div class="question-list">\n{items}</div></div>\n')
        for q in sec['questions']:
            i = q['n']
            prev_dis = ' disabled style="opacity:.4;cursor:not-allowed"' if i == 1 else ''
            next_dis = ' disabled style="opacity:.4;cursor:not-allowed"' if i == total else ''
            main.append(
                f'<!-- Question {i}: {q["title"]} -->\n'
                f'<div class="question-content" id="q{i}"><div class="question-header">'
                f'<h1 class="question-title">{q["title"]}</h1><div class="question-meta">'
                f'<span class="meta-tag"><i class="fas fa-layer-group"></i> {sec["title"]}</span>'
                f'<span class="meta-tag"><i class="fas fa-clock"></i> {q["minutes"]} min read</span>'
                f'<span class="meta-tag"><i class="fas fa-signal"></i> Difficulty: {LEVELS[lvl] if False else LEVELS[sec["level"]]}</span>'
                f'<span class="meta-tag"><i class="fas fa-hashtag"></i> {i} of {total}</span>'
                f'</div></div>\n' + '\n'.join(q['cards']) +
                f'\n<div class="navigation-buttons">'
                f'<button class="nav-btn prev" onclick="navigateQuestion(\'prev\')"{prev_dis}><i class="fas fa-arrow-left"></i> Previous</button>'
                f'<button class="nav-btn next" onclick="navigateQuestion(\'next\')"{next_dis}>Next <i class="fas fa-arrow-right"></i></button>'
                f'</div></div>\n')

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta.PAGE_TITLE}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
{css}
{EXTRA_CSS}
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo-wrap">
                <a href="index.html" class="back-link"><i class="fas fa-arrow-left"></i><span>All Modules</span></a>
                <div class="logo"><i class="fas {meta.ICON}"></i><span>{meta.TITLE}</span></div>
            </div>
            <div class="header-actions">
                <div class="search-box">
                    <i class="fas fa-search"></i>
                    <input type="text" id="searchInput" placeholder="Search questions & answers...">
                </div>
                <div class="progress-indicator">
                    <span id="progressText">0%</span>
                    <div class="progress-bar-mini"><div class="progress-fill" id="progressFill"></div></div>
                </div>
            </div>
        </div>
    </header>

    <nav class="sidebar" id="sidebar">
        <div class="search-count" id="searchCount"></div>
{''.join(sidebar)}
    </nav>

    <main class="main-content">
        <div class="content-wrapper">
{''.join(main)}
        </div>
    </main>

    <div class="mobile-toggle" onclick="toggleSidebar()"><i class="fas fa-bars"></i></div>
    <div class="scroll-top" id="scrollTop" onclick="scrollToTop()"><i class="fas fa-arrow-up"></i></div>
{JS.replace('__MODULE__', module)}
</body>
</html>
"""
    out = ROOT / 'out'
    out.mkdir(exist_ok=True)
    target = out / meta.FILENAME
    target.write_text(page)
    print(f'{target}: {total} questions in {len(sections)} sections, {len(page)//1024} KB')


if __name__ == '__main__':
    build(sys.argv[1])
