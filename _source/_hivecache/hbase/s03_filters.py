from build import *
from hbase.anims import *
from hbase.runner import hsh, hq, sh, java, py

DATA = '''
create 'students', 'info', 'marks'
put 'students', '10', 'info:name', 'Old'
put 'students', '2401', 'info:name', 'Anuj'
put 'students', '2401', 'info:city', 'Mumbai'
put 'students', '2401', 'marks:sql', '78'
put 'students', '2402', 'info:name', 'Aarshvi'
put 'students', '2402', 'info:city', 'Mumbai'
put 'students', '2402', 'marks:sql', '91'
put 'students', '2403', 'info:name', 'Riya'
put 'students', '2403', 'info:city', 'Pune'
put 'students', '2403', 'marks:sql', '9'
put 'students', '2404', 'info:name', 'Rohit'
put 'students', '2404', 'info:city', 'Navi Mumbai'
put 'students', '2404', 'marks:sql', '100'
'''

SECTION = dict(level='intermediate', title='Filters', questions=[

# ------------------------------------------------------------------ 11
Q('What are filters in HBase? How do RowFilter, PrefixFilter and ValueFilter work?', 'Filters Basics', minutes=9, cards=[
    definition(
        defbox('A <strong>filter</strong> restricts which rows and cells a scan or get returns. Filters run <strong>on the RegionServer</strong>, so non-matching '
               'data is not sent over the network, but it is still <strong>read</strong>. In the shell they are written in the <strong>Filter Language</strong> '
               '(a string), and can be combined with <code>AND</code>, <code>OR</code> and brackets.'),
        table(['Filter', 'Keeps'], [
            ["<code>PrefixFilter('24')</code>", 'rows whose key starts with a prefix'],
            ["<code>RowFilter(&gt;=, 'binary:2402')</code>", 'rows whose key compares true'],
            ["<code>ValueFilter(=, 'binary:Mumbai')</code>", 'cells whose value compares true (other cells of the row are dropped)'],
            ["<code>QualifierFilter</code>, <code>FamilyFilter</code>", 'cells by qualifier / family name'],
        ]),
        tags('Filter Language', 'Server-side filtering', 'RowFilter', 'PrefixFilter', 'ValueFilter', 'AND / OR'),
    ),
    analogy('A filter is a <strong>sieve at the warehouse door</strong>: everything on the shelves you asked for is still carried to the door, but only the '
            'matching items are loaded onto your truck.'),
    filter_anim(),
    real_world(
        scenario('Narrow first, then filter',
                 p('"Mumbai students of batch 24" = <code>ROWPREFIXFILTER =&gt; \'24\'</code> (reads only that key range) plus a value filter on city. Using only the '
                   'value filter would read the whole table.')),
    ),
    example(
        hsh('''
scan 'students', {FILTER => "PrefixFilter('24')", COLUMNS => ['info:name']}
scan 'students', {FILTER => "RowFilter(>=, 'binary:2403')", COLUMNS => ['info:name']}
scan 'students', {FILTER => "ValueFilter(=, 'binary:Mumbai')"}
scan 'students', {ROWPREFIXFILTER => '240', FILTER => "ValueFilter(=, 'substring:mumbai') AND QualifierFilter(=, 'binary:city')"}
''', setup=DATA),
        p('<code>ValueFilter</code> works per <strong>cell</strong>: it returns only the matching city cells, not the rest of the row. Use '
          'SingleColumnValueFilter (next question) to select whole rows by a column value.', top=True),
        title='Example'),
    steps(
        ('Restrict the key range', 'STARTROW/STOPROW or ROWPREFIXFILTER.'),
        ('Add filters for what the key cannot express', 'Values, qualifiers.'),
        ('Limit columns', 'COLUMNS so less data is assembled.'),
        ('Check cost', 'If a filter is used constantly on full scans, redesign the key or add an index table.'),
        title='Steps'),
    crossq(
        ('Does a filter make a full scan fast?', 'No. Every row in the scanned range is still read from MemStore/HFiles; filters only save network transfer and client work.'),
        ('How do you write a filter in Java?', '<code>scan.setFilter(new ValueFilter(CompareOperator.EQUAL, new BinaryComparator(Bytes.toBytes("Mumbai"))))</code>; combine with <code>FilterList</code>.'),
    ),
]),

# ------------------------------------------------------------------ 12
Q('How does SingleColumnValueFilter work? What is the filterIfMissing gotcha?', 'SingleColumnValueFilter', minutes=8, cards=[
    definition(
        defbox("<code>SingleColumnValueFilter('family', 'qualifier', op, 'comparator:value', filterIfMissing, latestVersionOnly)</code> keeps <strong>whole rows</strong> "
               "where one column's value matches. It is the closest thing to <code>WHERE city = 'Mumbai'</code>.",
               '<strong>Gotcha</strong>: <code>filterIfMissing</code> defaults to <strong>false</strong>, so rows that <strong>do not have</strong> the column at all '
               'are <strong>returned</strong>. Pass <code>true</code> to exclude them. <code>latestVersionOnly</code> (default true) tests only the newest version. '
               '<code>SingleColumnValueExcludeFilter</code> does the same but omits the tested column from the result.'),
        tags('SingleColumnValueFilter', 'filterIfMissing', 'latestVersionOnly', 'SingleColumnValueExcludeFilter'),
    ),
    analogy('Asking "everyone whose form says city = Mumbai" and also receiving every form where the <strong>city box was left empty</strong>, unless you '
            'explicitly say "skip blank forms".'),
    scvf_anim(),
    real_world(
        scenario('A report with ghost rows',
                 p('A "Mumbai students" export included old placeholder rows that had no city column. The fix was adding <code>true, true</code> as the last two '
                   'arguments (filterIfMissing, latestVersionOnly).')),
    ),
    example(
        hsh('''
scan 'students', {FILTER => "SingleColumnValueFilter('info', 'city', =, 'binary:Mumbai')", COLUMNS => ['info:name', 'info:city']}
scan 'students', {FILTER => "SingleColumnValueFilter('info', 'city', =, 'binary:Mumbai', true, true)", COLUMNS => ['info:name', 'info:city']}
scan 'students', {FILTER => "SingleColumnValueFilter('info', 'city', =, 'substring:mumbai', true, true)", COLUMNS => ['info:name', 'info:city']}
''', setup=DATA),
        p('Row <code>10</code> has no <code>info:city</code>, so the first scan returns it. With filterIfMissing = true it disappears. The substring comparator also '
          'matches "Navi Mumbai".', top=True),
        title='Example'),
    steps(
        ('Always set filterIfMissing explicitly', 'Usually <code>true</code>.'),
        ('Keep latestVersionOnly = true', 'Unless you really want any version to match.'),
        ('Request the tested column', 'If you use COLUMNS, include the tested column, or the filter cannot see it.'),
        title='Steps'),
    crossq(
        ('Why must the tested column be in the scan\'s columns?', 'The filter only sees the cells the scan reads. If COLUMNS excludes info:city, every row looks "missing" the column.'),
        ('Is it efficient?', 'It still reads every row in the range; for frequent queries by that column, maintain an index table or use Phoenix.'),
    ),
]),

# ------------------------------------------------------------------ 13
Q('Which filters work on columns? How do you handle very wide rows?', 'Column Filters & Wide Rows', minutes=8, cards=[
    definition(
        table(['Filter', 'Keeps'], [
            ["<code>ColumnPrefixFilter('2026-10')</code>", 'qualifiers starting with a prefix'],
            ["<code>MultipleColumnPrefixFilter('a', 'b')</code>", 'qualifiers starting with any of several prefixes'],
            ["<code>QualifierFilter(&gt;=, 'binary:2026-11')</code>", 'qualifiers comparing true'],
            ["<code>FamilyFilter(=, 'binary:info')</code>", 'cells of matching families'],
            ['<code>ColumnPaginationFilter(limit, offset)</code>', 'a page of columns from each row'],
            ['<code>ColumnCountGetFilter(n)</code>', 'the first n columns'],
        ]),
        tags('ColumnPrefixFilter', 'QualifierFilter', 'FamilyFilter', 'ColumnPaginationFilter', 'Wide rows'),
    ),
    analogy('A student\'s <strong>attendance register page</strong> with one box per day; column filters let you photocopy only October, or only the first 10 boxes.'),
    column_filter_anim(),
    real_world(
        scenario('Monthly attendance from a wide row',
                 p('Attendance is stored as one row per student and one qualifier per day (<code>att:2026-10-14</code>). A month view is a get with '
                   '<code>ColumnPrefixFilter(\'2026-10\')</code>, returning ~22 cells instead of the whole year.')),
    ),
    example(
        hsh('''
create 'att_wide', 'att', 'info'
put 'att_wide', '2401', 'info:name', 'Anuj'
put 'att_wide', '2401', 'att:2026-10-01', 'P'
put 'att_wide', '2401', 'att:2026-10-02', 'A'
put 'att_wide', '2401', 'att:2026-10-03', 'P'
put 'att_wide', '2401', 'att:2026-11-01', 'P'
put 'att_wide', '2401', 'att:2026-11-02', 'P'
get 'att_wide', '2401', {FILTER => "ColumnPrefixFilter('2026-10')"}
get 'att_wide', '2401', {FILTER => "QualifierFilter(>=, 'binary:2026-11')"}
get 'att_wide', '2401', {FILTER => "FamilyFilter(=, 'binary:info')"}
get 'att_wide', '2401', {FILTER => "ColumnPaginationFilter(2, 0)"}
get 'att_wide', '2401', {FILTER => "ColumnPaginationFilter(2, 2)"}
'''),
        p('The QualifierFilter also returned <code>info:name</code>: it compares qualifiers of <em>every</em> family, and "name" is greater than "2026-11" in byte '
          'order. Combine it with a FamilyFilter, or list the family in COLUMNS, to stay inside <code>att</code>.', top=True),
        title='Example'),
    steps(
        ('Put sortable data in qualifiers', 'Dates as yyyy-MM-dd so prefixes and ranges work.'),
        ('Fetch slices with column filters', 'Prefix or range.'),
        ('Page very wide rows', 'ColumnPaginationFilter, or Scan.setBatch in Java.'),
        ('Keep rows bounded', 'A row never splits across regions.'),
        title='Steps'),
    crossq(
        ('Why are qualifiers sorted?', 'Cells in a row are stored sorted by family, then qualifier, so prefix and range filters on qualifiers can seek efficiently.'),
        ('What is Scan.setBatch?', 'It limits cells per Result, so a huge row is returned in chunks instead of one enormous response.'),
    ),
]),

# ------------------------------------------------------------------ 14
Q('How do KeyOnlyFilter, FirstKeyOnlyFilter and PageFilter help with counting and pagination?', 'Key-Only & Page Filters', minutes=7, cards=[
    definition(
        defbox('<code>FirstKeyOnlyFilter()</code> returns only the first cell of each row and <code>KeyOnlyFilter()</code> strips values. Together they make '
               'listing or counting row keys cheap; the shell\'s <code>count</code> and the RowCounter job use this idea.',
               '<code>PageFilter(n)</code> stops after n rows <strong>per region</strong>, so on a multi-region table the client can receive more than n rows and must '
               'stop itself. Pagination is done by remembering the last row key and starting the next scan just after it.'),
        tags('KeyOnlyFilter', 'FirstKeyOnlyFilter', 'PageFilter', 'Pagination', 'count'),
    ),
    analogy('To count students in a hostel you read the <strong>name plate on each door</strong> (key only), you do not empty every room.'),
    keyonly_anim(),
    real_world(
        scenario('Admin paging',
                 p('The admin portal shows 50 students per page: a scan with <code>STARTROW</code> = last key of the previous page + <code>\\x00</code>, '
                   '<code>LIMIT =&gt; 50</code>, and <code>FirstKeyOnlyFilter</code> when only IDs are needed.')),
    ),
    example(
        hsh('''
scan 'students', {FILTER => "FirstKeyOnlyFilter() AND KeyOnlyFilter()"}
scan 'students', {FILTER => "PageFilter(2)"}
scan 'students', {STARTROW => "2401\\x00", LIMIT => 2, COLUMNS => ['info:name']}
''', setup=DATA),
        p('The third scan is "page 2": it starts just after the last key of page 1 (2401) by appending a zero byte, which needs a double-quoted string in the shell.', top=True),
        title='Example'),
    steps(
        ('Count large tables with RowCounter', '<code>hbase org.apache.hadoop.hbase.mapreduce.RowCounter students</code>'),
        ('List keys with FirstKeyOnly + KeyOnly', 'Minimal data transferred.'),
        ('Paginate by last key', 'Not by offset (HBase has no OFFSET).'),
        title='Steps'),
    crossq(
        ('Why is there no OFFSET in HBase?', 'Skipping n rows would still require reading them; key-based continuation is constant cost per page.'),
        ('Is PageFilter reliable alone?', 'No: it is applied per region (and per RegionServer scanner), so always combine it with a client-side limit (the shell\'s LIMIT does this).'),
    ),
]),

# ------------------------------------------------------------------ 15
Q('How do comparators work in filters? Why do numbers stored as strings compare wrongly?', 'Comparators & Byte Order', minutes=8, cards=[
    definition(
        table(['Comparator', 'Syntax', 'Meaning'], [
            ['binary', "<code>'binary:Pune'</code>", 'byte-by-byte comparison (supports =, !=, &lt;, &lt;=, &gt;, &gt;=)'],
            ['binaryprefix', "<code>'binaryprefix:Nav'</code>", 'compare only the first bytes'],
            ['substring', "<code>'substring:mumbai'</code>", 'contains, case-insensitive (only = and !=)'],
            ['regexstring', "<code>'regexstring:^24[0-9]{2}$'</code>", 'Java regular expression (only = and !=)'],
        ]),
        p('Because <code>binary</code> compares bytes, text numbers compare like words: <code>\'9\' &gt; \'80\'</code> but <code>\'100\' &lt; \'80\'</code>. Store '
          'numbers as fixed-width text or as binary (<code>Bytes.toBytes(long)</code>, big-endian; flip the sign bit for negatives) to compare numerically.', top=True),
        tags('BinaryComparator', 'BinaryPrefixComparator', 'SubstringComparator', 'RegexStringComparator', 'Byte order'),
    ),
    analogy('Sorting exam marks written on cards <strong>alphabetically</strong>: "100" comes before "80" because "1" comes before "8". You need to write all '
            'marks with three digits ("080", "100") for the order to make sense.'),
    comparator_anim(),
    real_world(
        scenario('Toppers query gone wrong',
                 p('"Marks greater than 80" returned 9 and 91 but not 100. Marks were stored as plain text. The team switched to three-digit text ("009", "091", '
                   '"100") for display-friendly values and kept a binary copy for numeric filters.')),
    ),
    example(
        hsh('''
scan 'students', {FILTER => "SingleColumnValueFilter('marks', 'sql', >, 'binary:80', true, true)", COLUMNS => ['marks:sql']}
scan 'students', {FILTER => "SingleColumnValueFilter('info', 'city', =, 'binaryprefix:Nav', true, true)", COLUMNS => ['info:city']}
scan 'students', {FILTER => "RowFilter(=, 'regexstring:^240[2-3]$')", COLUMNS => ['info:name']}
''', setup=DATA),
        p('Marks "9" passes "&gt; 80" (because the character 9 is greater than 8) and "100" fails (1 is less than 8). Only 91 is a correct match.', top=True),
        title='Example'),
    steps(
        ('Choose an encoding per field', 'Fixed-width text, or binary for numbers and timestamps.'),
        ('Use binary comparators on correctly encoded data', 'Then &lt; and &gt; behave numerically.'),
        ('Use substring/regex only for text', 'They only support = and !=.'),
        title='Steps'),
    crossq(
        ('How do you encode negative numbers so byte order is numeric?', 'Flip the sign bit of the two\'s-complement value (as Phoenix and OrderedBytes do), so negatives sort before positives.'),
        ('Are regex filters expensive?', 'Yes, they evaluate a regular expression on every row or cell scanned; prefer key prefixes where possible.'),
    ),
]),
])
