from build import *


def _dn(x, y, name, blocks, step=None, focus=None, color='green', w=150):
    """DataNode box with a row of block chips."""
    out = [sbox(x, y, w, 78, name, '', color, step=step, focus=focus, top=True)]
    for i, (b, c) in enumerate(blocks):
        out.append(scell(x + 10 + i * 34, y + 38, 30, 26, b, PALETTE.get(c, c), '#fff', step=step, bold=True, size=11))
    return ''.join(out)


def hdfs_arch():
    elems = [
        stext(380, 26, 'HDFS: one master, many workers', 'blue', 15, bold=True),
        sbox(30, 60, 130, 60, 'Client', 'hdfs dfs / Spark', 'gray', step=1, focus=1),
        sbox(285, 45, 200, 90, 'NameNode', 'namespace · file → blocks\nblock → DataNodes\n(metadata in RAM)', 'blue', step=2, focus=2),
        sarrow(160, 85, 283, 85, 'blue', step=2),
        stext(222, 76, 'metadata', 'blue', 11, step=2),
        _dn(40, 205, 'DataNode 1', [('B1', 'blue'), ('B2', 'amber'), ('B3', 'purple')], step=3, focus=3),
        _dn(305, 205, 'DataNode 2', [('B1', 'blue'), ('B3', 'purple')], step=3, focus=3),
        _dn(570, 205, 'DataNode 3', [('B1', 'blue'), ('B2', 'amber'), ('B3', 'purple')], step=3, focus=3),
        sarrow(115, 205, 330, 137, 'pink', step=4, dashed=True),
        sarrow(380, 205, 382, 137, 'pink', step=4, dashed=True),
        sarrow(645, 205, 440, 137, 'pink', step=4, dashed=True),
        stext(620, 165, 'heartbeat every 3 s', 'pink', 11, step=4, focus=4),
        stext(620, 180, '+ block reports', 'pink', 11, step=4),
        sflow(95, 120, 105, 205, 'green', step=5, count=3),
        stext(160, 175, 'data flows directly', 'green', 11, step=5, focus=5),
        stext(160, 190, 'client ⇄ DataNode', 'green', 11, step=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'A <strong>client</strong> (the <code>hdfs dfs</code> shell, a Spark job, a Hive query) wants to read or write a file.',
        'It first asks the <strong>NameNode</strong>. The NameNode holds only <strong>metadata</strong> in memory: the directory tree, which blocks make up each file and which DataNodes hold each block. It stores no file data.',
        'The actual data lives on the <strong>DataNodes</strong> as blocks (128 MB by default). Each block is stored on 3 different DataNodes, so losing one machine loses no data.',
        'Every DataNode sends a <strong>heartbeat</strong> to the NameNode every 3 seconds ("I am alive") and periodically a <strong>block report</strong> listing every block it holds. This is how the NameNode knows where blocks are.',
        'Data itself <strong>never passes through the NameNode</strong>. After getting block locations, the client reads and writes directly with the DataNodes. This keeps the master from becoming a bandwidth bottleneck.',
    ])


def block_split():
    elems = [
        stext(380, 26, 'Uploading results.csv (500 MB) with block size 128 MB, replication 3', 'blue', 14, bold=True),
        sbox(30, 50, 700, 40, 'results.csv — 500 MB', '', 'gray', step=1, focus=1),
        sbox(30, 110, 178, 44, 'B1 · 128 MB', '', 'blue', step=2, focus=2),
        sbox(208, 110, 178, 44, 'B2 · 128 MB', '', 'amber', step=2, focus=2),
        sbox(386, 110, 178, 44, 'B3 · 128 MB', '', 'purple', step=2, focus=2),
        sbox(564, 110, 166, 44, 'B4 · 116 MB', '', 'pink', step=3, focus=3),
        stext(647, 172, 'last block uses only 116 MB on disk', 'pink', 11, step=3),
        _dn(30, 200, 'DN1', [('B1', 'blue'), ('B3', 'purple'), ('B4', 'pink')], step=4, w=130),
        _dn(175, 200, 'DN2', [('B1', 'blue'), ('B2', 'amber')], step=4, w=130),
        _dn(320, 200, 'DN3', [('B2', 'amber'), ('B3', 'purple'), ('B4', 'pink')], step=4, w=130),
        _dn(465, 200, 'DN4', [('B1', 'blue'), ('B2', 'amber'), ('B4', 'pink')], step=4, w=130),
        _dn(610, 200, 'DN5', [('B3', 'purple')], step=4, w=130),
        stext(380, 305, '4 blocks × 3 replicas = 12 block copies · 1,500 MB of raw disk', 'green', 13, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 320, *elems), [
        'A 500 MB file is copied into HDFS. HDFS never stores it as one piece.',
        'It is cut into fixed-size <strong>blocks</strong> of 128 MB (the default <code>dfs.blocksize</code> since Hadoop 2).',
        'The last block holds only the remaining 116 MB. A block is <strong>not padded</strong>: a small or partial block uses only as much disk as its data.',
        'Each block is <strong>replicated 3 times</strong> on different DataNodes. The NameNode chooses where, spreading copies across nodes and racks.',
        'Total raw storage is file size × replication = 1,500 MB. That 3× overhead is the price of fault tolerance (Hadoop 3 erasure coding reduces it).',
    ])


def rack_awareness():
    elems = [
        stext(380, 26, 'Default replica placement (replication = 3)', 'blue', 15, bold=True),
        sbox(40, 50, 300, 230, '', '', 'gray', fill_opacity=0.06),
        stext(190, 72, 'Rack A  (switch A)', 'gray', 13, bold=True),
        sbox(420, 50, 300, 230, '', '', 'gray', fill_opacity=0.06),
        stext(570, 72, 'Rack B  (switch B)', 'gray', 13, bold=True),
        sbox(70, 90, 240, 40, 'Node A1 · writer', '', 'cyan', step=1, focus=1, size=12),
        sbox(70, 145, 240, 40, 'Node A2', '', 'gray'),
        sbox(70, 200, 240, 40, 'Node A3', '', 'gray'),
        sbox(450, 90, 240, 40, 'Node B1', '', 'gray'),
        sbox(450, 145, 240, 40, 'Node B2', '', 'gray'),
        sbox(450, 200, 240, 40, 'Node B3', '', 'gray'),
        scell(255, 97, 46, 26, 'R1', '#0ea5e9', '#fff', step=1, focus=1, bold=True),
        scell(635, 152, 46, 26, 'R2', '#f59e0b', '#fff', step=2, focus=2, bold=True),
        scell(635, 207, 46, 26, 'R3', '#10b981', '#fff', step=3, focus=3, bold=True),
        sarrow(310, 110, 450, 160, 'amber', step=2),
        sarrow(658, 178, 658, 205, 'green', step=3),
        stext(380, 300, 'lose a node → 2 copies left · lose all of Rack B → R1 survives on Rack A', 'pink', 12, step=4, focus=4, bold=True),
    ]
    return anim(canvas(760, 315, *elems), [
        '<strong>Replica 1</strong> goes on the node where the writer runs (if that node is a DataNode), otherwise on a random node. Writing locally is fastest.',
        '<strong>Replica 2</strong> goes on a node in a <strong>different rack</strong>. If the whole of Rack A loses power or its switch fails, the data is still available.',
        '<strong>Replica 3</strong> goes on a <em>different node in the same rack as replica 2</em>. Only one copy crosses between racks during the write, which saves inter-rack bandwidth.',
        'Result: survives any single node failure and any single rack failure, with only one cross-rack transfer per block. The NameNode learns the topology from a <strong>rack-awareness script</strong> (<code>net.topology.script.file.name</code>).',
    ])


def checkpoint_anim():
    elems = [
        stext(380, 26, 'How NameNode metadata is persisted and checkpointed', 'blue', 15, bold=True),
        sbox(30, 55, 230, 70, 'NameNode RAM', 'full namespace +\nblock map', 'blue', step=1, focus=1),
        sbox(155, 160, 105, 60, 'fsimage', 'snapshot', 'purple', step=1),
        sbox(30, 160, 105, 60, 'edits', 'change log', 'amber', step=2, focus=2),
        sflow(82, 125, 82, 160, 'amber', step=2, count=2),
        stext(145, 245, 'mkdir, create, rename, delete …', 'amber', 11, step=2),
        stext(145, 262, 'appended to edits — fsimage untouched', 'amber', 11, step=2),
        sbox(450, 55, 280, 70, 'Secondary / Standby NameNode', 'does the checkpoint', 'green', step=3, focus=3, size=12),
        sarrow(260, 190, 448, 100, 'purple', step=3, mid=(360, 120)),
        stext(370, 168, 'copy fsimage + edits', 'purple', 11, step=3),
        sbox(510, 160, 160, 60, 'new fsimage', 'old image + edits', 'green', step=4, focus=4),
        sarrow(590, 125, 590, 158, 'green', step=4),
        sarrow(510, 210, 262, 210, 'green', step=5, dashed=True),
        stext(390, 235, 'new fsimage replaces old · old edits purged', 'green', 11, step=5, focus=5),
        stext(380, 290, 'checkpoint every 1 h  or  every 1,000,000 transactions', 'cyan', 12, step=6, focus=6, bold=True),
    ]
    return anim(canvas(760, 305, *elems), [
        'The NameNode keeps the whole namespace in <strong>RAM</strong> for speed, and persists it on disk as an <strong>fsimage</strong>: a snapshot of the namespace at some point in time.',
        'Changes are not written into the fsimage directly. Every change (create, rename, delete) is appended to the <strong>edits</strong> log, which is cheap and safe.',
        'If edits grow unbounded, a restart takes very long (all edits must be replayed). So a <strong>Secondary NameNode</strong> (or, in HA, the Standby NameNode) periodically copies fsimage and edits.',
        'It loads the fsimage, replays the edits on top, and writes a <strong>new fsimage</strong>. This merge is a <strong>checkpoint</strong>.',
        'The new fsimage replaces the old one and the old edits can be discarded, so the next restart only replays a short log.',
        'Defaults: <code>dfs.namenode.checkpoint.period</code> = 3600 s and <code>dfs.namenode.checkpoint.txns</code> = 1,000,000, whichever comes first. Note: the Secondary NameNode is a <strong>checkpoint helper, not a backup</strong>.',
    ])


def write_pipeline():
    elems = [
        stext(380, 24, 'Writing one block: the replication pipeline', 'blue', 15, bold=True),
        sbox(20, 120, 120, 60, 'Client', 'DFSOutputStream', 'gray', step=1),
        sbox(300, 40, 160, 50, 'NameNode', '', 'blue', step=1, focus=1),
        sarrow(140, 130, 298, 72, 'blue', step=1),
        stext(190, 82, '① create /results.csv', 'blue', 11, step=1),
        sarrow(298, 82, 145, 145, 'cyan', step=2, dashed=True),
        stext(300, 125, '② write B1 to DN1, DN3, DN4', 'cyan', 11, step=2, focus=2),
        sbox(190, 200, 120, 56, 'DN1', 'rack A', 'green', step=3),
        sbox(370, 200, 120, 56, 'DN3', 'rack B', 'green', step=3),
        sbox(550, 200, 120, 56, 'DN4', 'rack B', 'green', step=3),
        sflow(140, 165, 190, 220, 'cyan', step=3, count=3),
        sflow(310, 220, 370, 220, 'cyan', step=3, count=3),
        sflow(490, 220, 550, 220, 'cyan', step=3, count=3),
        stext(380, 190, '64 KB packets flow down the pipeline', 'cyan', 11, step=3, focus=3),
        sflow(550, 245, 490, 245, 'green', step=4, count=2, r=4),
        sflow(370, 245, 310, 245, 'green', step=4, count=2, r=4),
        sflow(190, 245, 140, 175, 'green', step=4, count=2, r=4),
        stext(380, 280, 'ACKs travel back up the pipeline', 'green', 11, step=4, focus=4),
        stext(620, 60, 'block complete →', 'purple', 11, step=5, focus=5),
        stext(620, 76, 'next block, new pipeline', 'purple', 11, step=5),
    ]
    return anim(canvas(760, 300, *elems), [
        'The client calls <code>create()</code>. The NameNode checks permissions and that the file does not already exist, and records the new file in the namespace.',
        'For each block, the client asks the NameNode for target DataNodes. The NameNode returns a list chosen by the placement policy (here DN1, DN3, DN4).',
        'The client streams the data in small <strong>packets</strong> to <strong>DN1 only</strong>. DN1 stores each packet and forwards it to DN3, which forwards it to DN4: a <strong>pipeline</strong>. The client uploads each byte once, not three times.',
        '<strong>Acknowledgements</strong> flow back from DN4 → DN3 → DN1 → client. A packet is removed from the client\'s ack queue only when all replicas have it.',
        'When the block is full, the client asks for a new set of DataNodes for the next block. On <code>close()</code>, the NameNode marks the file complete once the minimum replicas are confirmed.',
    ])


def read_path():
    elems = [
        stext(380, 24, 'Reading a file from HDFS', 'blue', 15, bold=True),
        sbox(20, 110, 130, 60, 'Client', 'on node A2', 'gray', step=1),
        sbox(300, 40, 170, 50, 'NameNode', '', 'blue', step=1, focus=1),
        sarrow(150, 120, 298, 70, 'blue', step=1),
        stext(200, 76, '① open()', 'blue', 11, step=1),
        stable(500, 40, ['block', 'locations (closest first)'], [['B1', 'A2, B1, B3'], ['B2', 'A1, B2, B3']], [60, 180], step=2, title='② block locations', title_color='cyan'),
        sbox(200, 215, 120, 50, 'DN A2', 'same node', 'green', step=3, focus=3),
        sbox(360, 215, 120, 50, 'DN A1', 'same rack', 'green', step=4, focus=4),
        sbox(520, 215, 120, 50, 'DN B3', 'other rack', 'gray', step=4),
        sflow(260, 215, 110, 170, 'green', step=3, count=3),
        sflow(400, 215, 130, 170, 'green', step=4, count=3),
        stext(360, 290, 'if a DataNode fails or a checksum mismatches → next replica in the list', 'red', 12, step=5, focus=5),
    ]
    return anim(canvas(760, 305, *elems), [
        'The client calls <code>open()</code> and asks the NameNode for the file\'s block locations.',
        'The NameNode returns, for each block, the DataNodes that hold a replica, <strong>sorted by network distance</strong> from the client.',
        'The client reads block B1 directly from the closest replica. Here it is on the same node, so it is a fast <strong>local read</strong> (short-circuit reads can even bypass the DataNode process).',
        'Then it reads B2 from the closest replica of B2, here in the same rack. Data is streamed block by block; the NameNode is not involved in transferring data.',
        'Every block has <strong>checksums</strong>. If a read fails or the checksum does not match, the client reports the bad replica to the NameNode and reads from the next DataNode in the list.',
    ])


def ha_anim():
    elems = [
        stext(380, 24, 'NameNode High Availability (Quorum Journal Manager)', 'blue', 15, bold=True),
        sbox(40, 50, 170, 60, 'Active NN', 'serves clients', 'green', step=1, focus='1,5'),
        sbox(550, 50, 170, 60, 'Standby NN', 'hot spare', 'gray', step=1, focus=1),
        sbox(250, 140, 80, 44, 'JN1', '', 'purple', step=2),
        sbox(340, 140, 80, 44, 'JN2', '', 'purple', step=2),
        sbox(430, 140, 80, 44, 'JN3', '', 'purple', step=2),
        sflow(150, 110, 290, 140, 'purple', step=2, count=2),
        stext(380, 125, 'Active writes edits to a majority of JournalNodes', 'purple', 11, step=2, focus=2),
        sflow(470, 140, 600, 110, 'purple', step=3, count=2),
        stext(640, 135, 'Standby tails edits', 'purple', 11, step=3, focus=3),
        stext(640, 150, '+ gets block reports', 'purple', 11, step=3),
        sbox(40, 230, 170, 44, 'ZKFC', 'health checks', 'amber', step=4),
        sbox(295, 230, 170, 44, 'ZooKeeper', 'active lock', 'amber', step=4, focus=4),
        sbox(550, 230, 170, 44, 'ZKFC', 'health checks', 'amber', step=4),
        sarrow(210, 252, 293, 252, 'amber', step=4), sarrow(548, 252, 467, 252, 'amber', step=4),
        '<g data-step="5"><line x1="45" y1="55" x2="205" y2="105" stroke="#ef4444" stroke-width="4"/><line x1="205" y1="55" x2="45" y2="105" stroke="#ef4444" stroke-width="4"/></g>',
        stext(380, 300, 'Active dies → lock released → Standby ZKFC fences old Active, promotes Standby', 'red', 12, step=5, focus=5, bold=True),
        sbox(550, 50, 170, 60, 'NEW Active NN', 'took over in seconds', 'green', step=6, focus=6, size=12),
    ]
    return anim(canvas(760, 315, *elems), [
        'Two (Hadoop 3: two or more) NameNodes run. Only one is <strong>Active</strong> and serves clients; the other is a <strong>Standby</strong> with the same namespace in memory.',
        'The Active NameNode writes every edit to a group of <strong>JournalNodes</strong> (usually 3 or 5). A write succeeds once a <strong>majority</strong> confirms it.',
        'The Standby continuously reads (tails) the edits from the JournalNodes and applies them. DataNodes send block reports and heartbeats to <strong>both</strong> NameNodes, so the Standby is ready instantly. The Standby also does the checkpointing.',
        'A <strong>ZKFailoverController (ZKFC)</strong> runs next to each NameNode, checks its health and holds a lock in <strong>ZooKeeper</strong> for the Active one.',
        'If the Active NameNode crashes, its ZooKeeper session expires and the lock is released. The other ZKFC <strong>fences</strong> the old Active (the JournalNodes also reject writes from it) to prevent split-brain.',
        'The Standby is promoted to Active. Clients configured with the logical nameservice (e.g. <code>hdfs://mycluster</code>) fail over automatically.',
    ])


def dn_failure():
    elems = [
        stext(380, 24, 'A DataNode dies: automatic re-replication', 'blue', 15, bold=True),
        sbox(290, 45, 180, 50, 'NameNode', '', 'blue'),
        _dn(40, 150, 'DN1', [('B1', 'blue'), ('B2', 'amber')], step=1),
        _dn(230, 150, 'DN2', [('B1', 'blue'), ('B2', 'amber')], step=1, focus='2,3'),
        _dn(420, 150, 'DN3', [('B1', 'blue')], step=1),
        _dn(610, 150, 'DN4', [('B2', 'amber')], step=1, w=130),
        '<g data-step="2"><line x1="235" y1="155" x2="375" y2="223" stroke="#ef4444" stroke-width="4"/><line x1="375" y1="155" x2="235" y2="223" stroke="#ef4444" stroke-width="4"/></g>',
        stext(305, 142, 'no heartbeat…', 'red', 12, step=2, focus=2),
        stext(380, 295, 'after ~10.5 min DN2 is declared dead: B1 and B2 now have only 2 replicas', 'amber', 12, step=3, focus=3, bold=True),
        sflow(110, 215, 470, 215, 'amber', step=4, count=3, mid=(290, 300)),
        scell(464, 188, 30, 26, 'B2', '#f59e0b', '#fff', step=4, focus=4, bold=True),
        sflow(450, 215, 660, 215, 'blue', step=4, count=3, mid=(560, 290)),
        scell(654, 188, 30, 26, 'B1', '#0ea5e9', '#fff', step=4, focus=4, bold=True),
        stext(380, 116, 'NameNode schedules copies from surviving replicas', 'green', 12, step=4),
        stext(380, 318, 'replication back to 3 — no admin action needed', 'green', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 332, *elems), [
        'Each block has 3 replicas spread over the DataNodes, and every DataNode sends a heartbeat every 3 seconds.',
        'DN2 crashes (disk, power, network). Its heartbeats stop.',
        'The NameNode waits before acting, to avoid a re-replication storm on short glitches. With defaults it declares a node dead after <strong>2 × 5 min recheck + 10 × 3 s heartbeat = 10.5 minutes</strong>. Blocks that were on DN2 are now <strong>under-replicated</strong>.',
        'The NameNode tells DataNodes that still hold good replicas to copy them to other nodes (respecting rack placement). Here DN1 copies B2 to DN3 and DN3 copies B1 to DN4. Clients can keep reading the whole time.',
        'Once every block is back to its target replication, the cluster has healed itself. If DN2 returns later with old copies, the extra (over-replicated) replicas are deleted.',
    ])


def ec_anim():
    elems = [
        stext(190, 26, '3× replication', 'amber', 15, bold=True),
        stext(570, 26, 'Erasure coding RS-6-3', 'green', 15, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
    ]
    for r in range(3):
        for i in range(6):
            elems.append(scell(30 + i * 52, 50 + r * 36, 48, 30, f'D{i+1}', '#0ea5e9' if r == 0 else '#78350f', '#fff', step=1 if r == 0 else 2, bold=True, size=11))
    elems += [
        stext(190, 175, '6 data units → 18 stored (200% overhead)', 'amber', 12, step=2, focus=2),
        stext(190, 195, 'survives loss of any 2 copies of a unit', 'amber', 11, step=2),
    ]
    for i in range(6):
        elems.append(scell(400 + i * 40, 50, 37, 30, f'D{i+1}', '#0ea5e9', '#fff', step=3, bold=True, size=11))
    for i in range(3):
        elems.append(scell(450 + i * 50, 100, 46, 30, f'P{i+1}', '#10b981', '#fff', step=3, focus=3, bold=True, size=11))
    elems += [
        stext(570, 155, '6 data + 3 parity = 9 stored (50% overhead)', 'green', 12, step=3, focus=3),
        stext(570, 175, 'any 3 of the 9 cells can be lost', 'green', 11, step=4, focus=4),
        stext(570, 192, 'and the data is rebuilt from the other 6', 'green', 11, step=4),
        stext(380, 245, 'Cost of EC: reconstruction uses CPU + network, no data locality, poor for small files', 'pink', 12, step=5, focus=5),
        stext(380, 268, '→ use for cold / archive data; keep replication for hot data', 'pink', 12, step=5, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Take 6 blocks of data. With replication each block is stored once…',
        '…and then twice more. 6 units of data occupy 18 units of disk: <strong>200% storage overhead</strong>. It tolerates the loss of 2 replicas of any block.',
        '<strong>Erasure coding</strong> (Hadoop 3) with the Reed-Solomon policy <code>RS-6-3-1024k</code> stores the 6 data cells plus 3 computed <strong>parity</strong> cells: 9 units, only <strong>50% overhead</strong>.',
        'Any 3 of those 9 cells can be lost and the missing ones are recomputed from the remaining 6. That is better fault tolerance than 3× replication with a third of the extra storage.',
        'The trade-off: rebuilding needs CPU and network, reads are striped across many nodes (no locality), and small files waste space. Use EC for cold/archival directories, replication for hot data.',
    ])


def small_files():
    elems = [
        stext(190, 26, '1 file of 1 GB', 'green', 15, bold=True),
        stext(570, 26, '10,000 files of 100 KB', 'red', 15, bold=True),
        '<line x1="380" y1="15" x2="380" y2="300" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
        sbox(60, 50, 260, 40, '1 GB file', '', 'green', step=1),
    ]
    for i in range(8):
        elems.append(scell(60 + i * 32.5, 100, 31, 24, f'B{i+1}', '#10b981', '#fff', step=1, size=10, bold=True))
    for r in range(4):
        for i in range(14):
            elems.append(scell(400 + i * 23, 50 + r * 20, 20, 16, '', '#ef4444', '#fff', step=1))
    elems += [
        stext(570, 145, '… (10,000 files, ~1 GB in total)', 'red', 11, step=1),
        stext(190, 160, '1 file + 8 blocks = 9 objects', 'green', 12, step=2, focus=2),
        stext(570, 165, '10,000 files + 10,000 blocks = 20,000 objects', 'red', 12, step=2, focus=2),
        stext(190, 185, '≈ 1.3 KB of NameNode heap', 'green', 12, step=3, focus=3, bold=True),
        stext(570, 190, '≈ 3 MB of NameNode heap', 'red', 12, step=3, focus=3, bold=True),
        stext(190, 225, '8 map tasks', 'green', 12, step=4, focus=4),
        stext(570, 225, '10,000 map tasks (each starts a JVM)', 'red', 12, step=4, focus=4),
        stext(380, 275, 'fix: merge files · Parquet/ORC compaction · HAR · SequenceFile · CombineFileInputFormat', 'cyan', 12, step=5, focus=5, bold=True),
    ]
    return anim(canvas(760, 300, *elems), [
        'Both sides store about 1 GB of data. On the left it is one large file; on the right it is 10,000 small files.',
        'Every file, directory and block is an <strong>object in NameNode memory</strong>. The large file needs 9 objects; the small files need 20,000, because each small file still has its own block.',
        'At a rule of thumb of ~150 bytes per object, the small files use over 2,000× more NameNode heap for the same data. At billions of objects, the NameNode runs out of memory.',
        'Processing suffers too: by default each small file becomes its own input split, so a MapReduce or Spark job launches 10,000 tasks instead of 8, and task start-up dominates the run time.',
        'Fixes: merge files at ingestion, compact periodically into large Parquet/ORC files, pack them into a Hadoop Archive (HAR) or SequenceFile, or read them with <code>CombineFileInputFormat</code>.',
    ])


def mapreduce_flow():
    elems = [
        stext(380, 22, 'Word count with MapReduce', 'blue', 15, bold=True),
        sbox(10, 45, 120, 44, 'split 1', 'big data big', 'gray', step=1, size=12),
        sbox(10, 160, 120, 44, 'split 2', 'data is big', 'gray', step=1, size=12),
        sbox(160, 40, 120, 54, 'Map 1', '(big,1) (data,1)\n(big,1)', 'blue', step=2, focus=2, size=12),
        sbox(160, 155, 120, 54, 'Map 2', '(data,1) (is,1)\n(big,1)', 'blue', step=2, focus=2, size=12),
        sflow(130, 67, 160, 67, 'blue', step=2, count=2), sflow(130, 182, 160, 182, 'blue', step=2, count=2),
        sbox(310, 40, 160, 170, '', '', 'amber', step=3, fill_opacity=0.08),
        stext(390, 62, 'Shuffle &amp; Sort', 'amber', 13, step=3, bold=True, focus=3),
        stext(390, 92, 'partition by key', 'amber', 11, step=3),
        stext(390, 108, 'sort by key', 'amber', 11, step=3),
        stext(390, 124, 'group values', 'amber', 11, step=3),
        stext(390, 160, 'big → [1,1,1]', '#fde68a', 12, step=3),
        stext(390, 178, 'data → [1,1]', '#fde68a', 12, step=3),
        stext(390, 196, 'is → [1]', '#fde68a', 12, step=3),
        sflow(280, 67, 310, 100, 'amber', step=3, count=2), sflow(280, 182, 310, 150, 'amber', step=3, count=2),
        sbox(500, 45, 120, 54, 'Reduce 1', 'big → 3', 'green', step=4, focus=4),
        sbox(500, 155, 120, 54, 'Reduce 2', 'data → 2\nis → 1', 'green', step=4, focus=4),
        sflow(470, 90, 500, 72, 'green', step=4, count=2), sflow(470, 170, 500, 182, 'green', step=4, count=2),
        sbox(645, 95, 105, 64, 'HDFS', 'part-r-00000\npart-r-00001', 'purple', step=5, focus=5, size=12),
        sflow(620, 72, 645, 115, 'purple', step=5, count=2), sflow(620, 182, 645, 140, 'purple', step=5, count=2),
        stext(380, 250, 'map output → local disk of the mapper (not HDFS) · reduce output → HDFS', 'cyan', 12, step=5),
    ]
    return anim(canvas(760, 270, *elems), [
        'The input file is divided into <strong>input splits</strong> (usually one per HDFS block). Each split is fed to one map task, record by record (here, line by line).',
        'Each <strong>map</strong> task runs in parallel, ideally on the node that stores its block (data locality), and emits intermediate <code>(key, value)</code> pairs: <code>(word, 1)</code> for every word.',
        '<strong>Shuffle &amp; sort</strong>: map output is partitioned by key (which reducer gets which key), sorted, copied over the network to the reducers and merged, so each reducer sees each key once with all its values.',
        'Each <strong>reduce</strong> task receives <code>key → [values]</code> and aggregates them: <code>big → [1,1,1]</code> becomes <code>big 3</code>.',
        'Each reducer writes one output file (<code>part-r-00000</code>, <code>part-r-00001</code>…) to HDFS. Intermediate map output is written only to the mapper\'s local disk and deleted after the job.',
    ])


def combiner_anim():
    elems = [
        stext(190, 26, 'Without combiner', 'red', 15, bold=True),
        stext(570, 26, 'With combiner', 'green', 15, bold=True),
        '<line x1="380" y1="15" x2="380" y2="285" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
        sbox(60, 45, 260, 70, 'Map output on node 1', '(big,1) (big,1) (big,1) (big,1)\n(data,1) (data,1)', 'blue', step=1, size=12),
        sbox(440, 45, 260, 70, 'Map output on node 1', '(big,1) (big,1) (big,1) (big,1)\n(data,1) (data,1)', 'blue', step=1, size=12),
        sbox(480, 135, 180, 44, 'Combiner (local reduce)', '', 'amber', step=2, focus=2, size=12),
        sarrow(570, 115, 570, 133, 'amber', step=2),
        sbox(480, 195, 180, 44, '(big,4) (data,2)', '', 'green', step=2, size=12),
        sarrow(570, 179, 570, 193, 'green', step=2),
        sflow(110, 115, 110, 245, 'red', step=3, count=6, r=4),
        stext(190, 265, '6 records cross the network', 'red', 12, step=3, focus=3, bold=True),
        sflow(570, 239, 570, 260, 'green', step=3, count=2, r=4),
        stext(570, 278, '2 records cross the network', 'green', 12, step=3, focus=3, bold=True),
        stext(250, 175, 'combiner must be commutative', 'cyan', 12, step=4, focus=4),
        stext(250, 193, '&amp; associative: sum, max, min, count', 'cyan', 12, step=4),
        stext(250, 211, 'NOT average (use sum + count)', 'pink', 12, step=4),
    ]
    return anim(canvas(760, 295, *elems), [
        'A mapper on one node emits six pairs. Four of them have the same key <code>big</code>.',
        'A <strong>combiner</strong> is a "mini-reducer" that runs on the mapper\'s node, on that mapper\'s output, before the shuffle. It sums the local counts to <code>(big,4)</code> and <code>(data,2)</code>.',
        'Without a combiner, 6 records are shuffled across the network; with it, only 2. On real data (millions of repeated keys) this cuts shuffle I/O dramatically.',
        'Hadoop may run the combiner zero, one or many times, so the operation must give the same answer regardless: <strong>commutative and associative</strong> (sum, count, max, min). Averaging averages is wrong; emit (sum, count) instead and divide in the reducer.',
    ])


def partitioner_anim():
    keys = [('big', 1), ('data', 0), ('is', 2), ('hadoop', 1), ('spark', 0)]
    elems = [stext(380, 24, 'Partitioner: which reducer gets which key?', 'blue', 15, bold=True),
             stext(380, 48, 'HashPartitioner: (key.hashCode() &amp; Integer.MAX_VALUE) % numReduceTasks', 'cyan', 12, step=1, focus=1)]
    for i, (k, r) in enumerate(keys):
        y = 75 + i * 40
        elems.append(sbox(40, y, 130, 32, k, '', 'gray', step=2, size=12))
        elems.append(sarrow(172, y + 16, 200, y + 16, 'gray', step=2))
        elems.append(stext(255, y + 21, f'hash % 3 = {r}', 'amber', 12, step=2))
    cols = ['blue', 'green', 'purple']
    for r in range(3):
        elems.append(sbox(470, 70 + r * 72, 160, 56, f'Reducer {r}', ', '.join(k for k, rr in keys if rr == r), cols[r], step=3, focus=3, size=12))
    for i, (k, r) in enumerate(keys):
        elems.append(sflow(330, 91 + i * 40, 470, 98 + r * 72, cols[r], step=3, count=1))
    elems.append(stext(380, 300, 'same key → always the same reducer · custom partitioner for skew or grouping', 'pink', 12, step=4, focus=4, bold=True))
    return anim(canvas(760, 315, *elems), [
        'With R reducers, every map output key must be sent to exactly one of them. The default <strong>HashPartitioner</strong> computes the partition from the key\'s hash.',
        'Each key\'s <code>hashCode()</code> (for a <code>Text</code> key, a hash of its UTF-8 bytes) is taken modulo the number of reducers (3 here). These are the real values Hadoop computes for these words (verified in the Partitioner question).',
        'All pairs with the same key, from every mapper, land on the same reducer. That is what allows the reducer to see the complete list of values for a key.',
        'You write a <strong>custom Partitioner</strong> when keys must be grouped differently (e.g. by country so each output file holds one country) or to spread out a skewed hot key.',
    ])


def yarn_flow():
    elems = [
        stext(380, 22, 'Running a job on YARN', 'blue', 15, bold=True),
        sbox(20, 50, 120, 50, 'Client', 'spark-submit', 'gray', step=1, focus=1),
        sbox(300, 40, 180, 64, 'ResourceManager', 'Scheduler +\nApplicationsManager', 'blue', step=1, focus=1, size=12),
        sarrow(140, 75, 298, 72, 'blue', step=1),
        sbox(40, 170, 200, 120, '', '', 'gray', fill_opacity=0.06, step=2),
        stext(140, 190, 'NodeManager 1', 'gray', 12, step=2, bold=True),
        sbox(280, 170, 200, 120, '', '', 'gray', fill_opacity=0.06, step=2),
        stext(380, 190, 'NodeManager 2', 'gray', 12, step=2, bold=True),
        sbox(520, 170, 200, 120, '', '', 'gray', fill_opacity=0.06, step=2),
        stext(620, 190, 'NodeManager 3', 'gray', 12, step=2, bold=True),
        sbox(60, 205, 160, 40, 'ApplicationMaster', '', 'amber', step=2, focus=2, size=12),
        sarrow(320, 104, 160, 203, 'amber', step=2),
        sarrow(220, 215, 330, 106, 'pink', step=3, dashed=True),
        stext(30, 140, 'request containers', 'pink', 11, 'start', step=3, focus=3),
        stext(30, 155, '(memory, vcores, locality)', 'pink', 11, 'start', step=3),
        sbox(300, 210, 160, 34, 'container: task', '', 'green', step=4, focus=4, size=12),
        sbox(300, 250, 160, 34, 'container: task', '', 'green', step=4, focus=4, size=12),
        sbox(540, 210, 160, 34, 'container: task', '', 'green', step=4, focus=4, size=12),
        sflow(220, 225, 300, 227, 'green', step=4, count=2), sflow(220, 235, 540, 227, 'green', step=4, count=2, mid=(380, 300)),
        sarrow(480, 200, 470, 106, 'cyan', step=5, dashed=True),
        stext(600, 120, 'NMs report health &', 'cyan', 11, step=5),
        stext(600, 135, 'resources to the RM', 'cyan', 11, step=5),
        stext(140, 280, 'progress → client', 'purple', 11, step=6, focus=6),
    ]
    return anim(canvas(760, 305, *elems), [
        'The client submits an application (a MapReduce job, a Spark app) to the <strong>ResourceManager</strong>, the cluster-wide master that owns all resources.',
        'The RM\'s ApplicationsManager finds a NodeManager with free capacity and launches the application\'s <strong>ApplicationMaster</strong> in a first container. Each application gets its own AM.',
        'The ApplicationMaster works out how many tasks are needed and asks the RM\'s <strong>Scheduler</strong> for containers: amount of memory and vcores, preferably on nodes holding the input data.',
        'The Scheduler grants containers; the AM contacts the <strong>NodeManagers</strong> directly to launch tasks inside them. A container is a slice of memory and CPU on one node.',
        'NodeManagers monitor their containers (killing those exceeding their memory) and send heartbeats with node health and available resources to the RM.',
        'The AM tracks task progress, re-requests containers for failed tasks, reports status to the client, and unregisters from the RM when the job finishes, releasing all containers.',
    ])


def spark_yarn_modes():
    elems = [
        stext(190, 26, '--deploy-mode client', 'blue', 15, bold=True),
        stext(570, 26, '--deploy-mode cluster', 'green', 15, bold=True),
        '<line x1="380" y1="15" x2="380" y2="295" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
        sbox(40, 50, 300, 60, 'Your laptop / edge node', 'Spark DRIVER runs here', 'blue', step=1, focus=1),
        sbox(40, 150, 300, 100, '', '', 'gray', fill_opacity=0.06, step=1),
        stext(190, 170, 'YARN cluster', 'gray', 12, step=1, bold=True),
        sbox(55, 185, 85, 50, 'AM', '(launcher)', 'amber', step=1, size=12),
        sbox(150, 185, 85, 50, 'Exec', '', 'green', step=1, size=12),
        sbox(245, 185, 85, 50, 'Exec', '', 'green', step=1, size=12),
        sflow(190, 110, 190, 185, 'blue', step=1, count=3),
        stext(190, 275, 'close the terminal → job dies', 'red', 12, step=2, focus=2),
        stext(190, 292, 'good for: spark-shell, notebooks, debugging', 'cyan', 11, step=2),
        sbox(420, 50, 300, 60, 'Edge node', 'only submits, can disconnect', 'gray', step=3),
        sbox(420, 150, 300, 100, '', '', 'gray', fill_opacity=0.06, step=3),
        stext(570, 170, 'YARN cluster', 'gray', 12, step=3, bold=True),
        sbox(435, 185, 105, 50, 'AM + DRIVER', '', 'amber', step=3, focus=3, size=11),
        sbox(550, 185, 75, 50, 'Exec', '', 'green', step=3, size=12),
        sbox(635, 185, 75, 50, 'Exec', '', 'green', step=3, size=12),
        sarrow(570, 110, 520, 183, 'gray', step=3, dashed=True),
        stext(570, 275, 'survives client disconnect; logs via yarn logs', 'green', 12, step=4, focus=4),
        stext(570, 292, 'good for: production / scheduled jobs', 'cyan', 11, step=4),
    ]
    return anim(canvas(760, 305, *elems), [
        'In <strong>client mode</strong>, the Spark driver runs in the process that called <code>spark-submit</code> (your edge node). YARN runs a small ApplicationMaster that only requests executors.',
        'Results and logs appear in your terminal, which is ideal for interactive work. But the driver depends on that machine: if the session or network drops, the job dies.',
        'In <strong>cluster mode</strong>, the driver runs <em>inside</em> the ApplicationMaster container on the cluster. The submitting machine can disconnect after submission.',
        'Use cluster mode for production and Airflow-scheduled jobs. Driver output goes to YARN logs (<code>yarn logs -applicationId &lt;id&gt;</code>).',
    ])


def joins_anim():
    elems = [
        stext(190, 26, 'Reduce-side join', 'amber', 15, bold=True),
        stext(570, 26, 'Map-side (broadcast) join', 'green', 15, bold=True),
        '<line x1="380" y1="15" x2="380" y2="295" stroke="#334155" stroke-width="2" stroke-dasharray="6,5"/>',
        sbox(30, 50, 140, 44, 'orders (big)', '', 'blue', step=1),
        sbox(210, 50, 140, 44, 'customers (big)', '', 'purple', step=1),
        sbox(30, 120, 140, 40, 'Map: tag O', 'key = cust_id', 'blue', step=1, size=12),
        sbox(210, 120, 140, 40, 'Map: tag C', 'key = cust_id', 'purple', step=1, size=12),
        sflow(100, 160, 190, 205, 'amber', step=2, count=3), sflow(280, 160, 190, 205, 'amber', step=2, count=3),
        stext(190, 272, 'full shuffle of BOTH datasets', 'red', 12, step=2, focus=2),
        sbox(110, 205, 160, 44, 'Reducer joins', 'C rows × O rows per key', 'amber', step=2, focus=2, size=12),
        stext(190, 290, 'works for any sizes · slow', 'amber', 12, step=2),
        sbox(410, 50, 140, 44, 'orders (big)', '', 'blue', step=3),
        sbox(590, 50, 140, 44, 'cities (small)', '', 'green', step=3, focus=3),
        sflow(660, 94, 480, 140, 'green', step=3, count=2), sflow(660, 94, 650, 140, 'green', step=3, count=2),
        stext(660, 118, 'copied to every mapper', 'green', 11, step=3),
        sbox(410, 140, 140, 50, 'Map + hash table', 'join in memory', 'green', step=4, focus=4, size=12),
        sbox(590, 140, 140, 50, 'Map + hash table', 'join in memory', 'green', step=4, focus=4, size=12),
        stext(570, 230, 'no shuffle, no reducer', 'green', 12, step=4, focus=4, bold=True),
        stext(570, 290, 'needs one side to fit in memory', 'pink', 12, step=4),
    ]
    return anim(canvas(760, 300, *elems), [
        '<strong>Reduce-side join</strong>: mappers read both datasets, emit the join key (cust_id) as the key and tag each record with its source.',
        'Shuffle brings all records with the same key to one reducer, which combines the customer rows with the order rows. It works for any data sizes, but both datasets cross the network: slow and skew-prone.',
        '<strong>Map-side (broadcast/replicated) join</strong>: the small table is shipped to every mapper (Distributed Cache in MapReduce, broadcast in Spark, MAPJOIN in Hive).',
        'Each mapper loads it into a hash table and joins its slice of the big table locally. No shuffle and no reduce phase, so it is much faster, but the small side must fit in memory.',
    ])
