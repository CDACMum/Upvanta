# Applies the Upvanta light theme to module pages (theme_light.css; redis.html uses theme_redis.css).
#   python apply_theme.py ../rdbms.html ../mysql.html ...   -> updates those pages in place
#   build.py also calls inject_theme() so newly built pages get the theme automatically.
# Safe to run again: the block between the markers is replaced, never duplicated.
import re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
START, END = '<!-- upvanta-theme:start -->', '<!-- upvanta-theme:end -->'
FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;600;700'
         '&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">')


def theme_block(css_file='theme_light.css'):
    css = (HERE / css_file).read_text(encoding='utf-8')
    return (f'{START}\n    <meta name="theme-color" content="#F7F9FC">\n    {FONTS}\n'
            f'    <style id="upvanta-theme">\n{css}\n    </style>\n    {END}\n')


BACK = ('<a href="index.html" class="back-link"><i class="fas fa-arrow-left"></i>'
        '<span>All Modules</span></a>')


def add_back_link(page):
    """Older hand-made pages have no way back to index.html; give them the same link as built pages."""
    if 'class="back-link"' in page:
        return page
    return re.sub(r'(<div class="header-content">\s*)(<div class="logo">.*?</div>)',
                  lambda m: m.group(1) + '<div class="logo-wrap">' + BACK + m.group(2) + '</div>',
                  page, count=1, flags=re.S)


def is_module_page(page):
    return 'class="question-content"' in page and 'class="content-card"' in page


def is_redis_page(page):
    """redis.html is an older hand-made page with its own layout; it gets theme_redis.css."""
    return 'id="questionContent"' in page and 'content-section' in page


def inject_theme(page):
    if is_redis_page(page) and not is_module_page(page):
        if 'class="back-link"' not in page:
            page = page.replace('<div class="logo">',
                                '<a href="index.html" class="back-link"><span>All Modules</span></a>\n            <div class="logo">', 1)
        block = theme_block('theme_redis.css')
    else:
        page = add_back_link(page)
        block = theme_block()
    if START in page:
        return re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', lambda m: block, page, flags=re.S)
    return page.replace('</head>', block + '</head>', 1)


if __name__ == '__main__':
    for name in sys.argv[1:]:
        p = Path(name)
        s = p.read_text(encoding='utf-8')
        if not (is_module_page(s) or is_redis_page(s)):
            print(f'skip {p.name}: not a generated module page')
            continue
        p.write_text(inject_theme(s), encoding='utf-8')
        print(f'themed {p.name}')
