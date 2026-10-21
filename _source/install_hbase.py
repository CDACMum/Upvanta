"""Run once from the Upvanta folder:  python install_hbase.py
Adds the Apache HBase card to index.html (Big Data Ecosystem) and the module to _source/README.txt."""
import pathlib, re
root = pathlib.Path(__file__).resolve().parent
idx = root / 'index.html'
h = idx.read_text(encoding='utf-8')
if 'href="hbase.html"' not in h:
    card = '''
                    <a href="hbase.html" class="module-card" data-keywords="hbase nosql wide-column hadoop hdfs row key region bigtable">
                        <div class="module-header">
                            <div class="module-icon">🗄️</div>
                            <h3 class="module-title">Apache HBase</h3>
                        </div>
                        <p class="module-description">Row key design, column families, versions, filters, regions, read/write path</p>
                        <div class="module-tags">
                            <span class="module-tag">NoSQL</span>
                            <span class="module-tag">Hadoop</span>
                        </div>
                    </a>
'''
    anchor = h.find('href="hive.html"')
    end = h.find('</a>', anchor) + len('</a>')
    h = h[:end] + '\n' + card + h[end:]
    head = h.rfind('category-title">Big Data Ecosystem', 0, anchor)
    m = re.compile(r'(<span class="category-count">)(\d+)( modules</span>)').search(h, head)
    h = h[:m.start()] + f'{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}' + h[m.end():]
    idx.write_text(h, encoding='utf-8')
    print('index.html: HBase card added')
rd = root / '_source' / 'README.txt'
r = rd.read_text(encoding='utf-8')
if 'HBase examples' not in r:
    r = re.sub(r'(Modules: [^\n]*)', lambda m: m.group(1) + ', hbase', r, count=1)
    r = r.rstrip('\n') + '\n' + (root / '_source' / 'README_hbase.txt').read_text(encoding='utf-8')
    rd.write_text(r, encoding='utf-8')
    print('_source/README.txt updated')
print('done')
