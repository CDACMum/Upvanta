from build import *
from cassandra.anims import *
from cassandra.runner import cql, cq, sh, conf, py

SECTION = dict(level='advanced', title='Replication, Consistency & Operations', questions=[

# ------------------------------------------------------------------ 31
Q('How does replication work in Cassandra? How are replicas chosen?', 'Replication', minutes=9, cards=[
    definition(
        defbox('Every partition is stored on <strong>RF</strong> nodes (the replication factor of its keyspace, per data centre). All replicas are equal: '
               'there is no primary copy, and any replica can serve reads and accept writes.',
               'Placement: the node owning the partition\'s token range gets the first replica. <strong>NetworkTopologyStrategy</strong> then walks the '
               'ring clockwise, choosing nodes in <strong>racks not yet used</strong> until each DC has its RF copies (if there are fewer racks than RF, '
               'racks are reused). A write is sent to all replicas in all DCs; the consistency level only decides how many acknowledgements to wait for.'),
        tags('Replication factor', 'Replica placement', 'Rack awareness', 'Multi-DC replication', 'No primary replica'),
    ),
    analogy('Important certificates are kept in <strong>three different cupboards in three different rooms</strong> of the office, and a copy is '
            'couriered to the branch office too. Any cupboard can answer a request; no one cupboard is "the original".'),
    replication_anim(),
    real_world(
        scenario('Surviving an availability-zone outage',
                 p('A 6-node cluster in AWS uses 3 racks = 3 availability zones and RF 3. When one zone went down, every partition still had 2 replicas, so '
                   'LOCAL_QUORUM reads and writes continued without errors; hints and repair caught the zone up afterwards.')),
    ),
    example(
        cq('''
CREATE KEYSPACE exam_live
  WITH replication = {'class': 'NetworkTopologyStrategy', 'dc_mumbai': 3, 'dc_pune': 2};
''', 'Replication per data centre'),
        sh('''
$ nodetool getendpoints exam_live attempts "SQL-2026-10"
10.0.1.11     # dc_mumbai rack r1
10.0.2.12     # dc_mumbai rack r2
10.0.3.11     # dc_mumbai rack r3
10.1.1.11     # dc_pune   rack r1
10.1.2.11     # dc_pune   rack r2
''', 'Which nodes hold a partition (illustrative)'),
        title='Example'),
    steps(
        ('Configure racks', 'One rack per availability zone in <code>cassandra-rackdc.properties</code>.'),
        ('Use the same number of nodes per rack', 'Otherwise racks with fewer nodes store more data per node.'),
        ('Set RF per DC', 'Usually 3.'),
        ('Verify placement', '<code>nodetool getendpoints</code> for a sample key.'),
        title='Steps'),
    crossq(
        ('Is there a "master copy" of the data?', 'No. All replicas are peers; conflicts are resolved by timestamps (last write wins).'),
        ('What happens to a write when a replica is down?', 'The write still succeeds if enough other replicas acknowledge for the consistency level; the '
         'coordinator stores a hint for the down replica.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('Explain consistency levels. How do you achieve strong consistency in Cassandra?', 'Consistency Levels', minutes=10, cards=[
    definition(
        table(['Level', 'Replicas that must respond', 'Typical use'], [
            ['<code>ANY</code> (writes only)', 'Any node, even a hint', 'Rarely used; weakest'],
            ['<code>ONE</code> / <code>LOCAL_ONE</code>', '1 (in the local DC for LOCAL_ONE)', 'Logs, telemetry, fastest'],
            ['<code>TWO</code>, <code>THREE</code>', '2 / 3', 'Uncommon'],
            ['<code>QUORUM</code>', 'floor(total RF / 2) + 1 across all DCs', 'Strong consistency, single DC'],
            ['<code>LOCAL_QUORUM</code>', 'Quorum of the local DC only', 'Most common production setting'],
            ['<code>EACH_QUORUM</code>', 'Quorum in every DC (writes)', 'Strong multi-DC writes, higher latency'],
            ['<code>ALL</code>', 'Every replica', 'Rare: one down replica fails the request'],
            ['<code>SERIAL</code> / <code>LOCAL_SERIAL</code>', 'Paxos quorum', 'Lightweight transactions'],
        ]),
        p('<strong>Strong consistency rule</strong>: if <code>W + R &gt; RF</code> (replicas written + replicas read), every read overlaps at least one '
          'replica that has the latest write. With RF 3, <code>LOCAL_QUORUM</code> writes and reads (2 + 2 = 4 &gt; 3) are the standard choice.', top=True),
        tags('Consistency level', 'QUORUM', 'LOCAL_QUORUM', 'EACH_QUORUM', 'ONE', 'ALL', 'W + R > RF'),
    ),
    analogy('Before announcing a result, you can ask <strong>one examiner</strong> (fast, might be outdated), <strong>a majority of the panel</strong> '
            '(reliable, slightly slower) or <strong>the entire panel</strong> (most certain, but the announcement waits if anyone is absent).'),
    consistency_anim(),
    real_world(
        scenario('Mixing levels in one application',
                 ul('Answer saves during the exam: <code>LOCAL_QUORUM</code> write.',
                    'Result display: <code>LOCAL_QUORUM</code> read, never shows an older mark.',
                    'Click-stream analytics: <code>LOCAL_ONE</code> write, highest throughput.',
                    'Never <code>QUORUM</code> across two DCs on the request path: it waits for the remote DC and adds its latency.')),
    ),
    example(
        cql('''
CONSISTENCY LOCAL_QUORUM;
CONSISTENCY;
'''),
        py('''
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.policies import DCAwareRoundRobinPolicy, TokenAwarePolicy
from cassandra.query import SimpleStatement
from cassandra import ConsistencyLevel

profile = ExecutionProfile(
    load_balancing_policy=TokenAwarePolicy(DCAwareRoundRobinPolicy(local_dc='dc_mumbai')),
    consistency_level=ConsistencyLevel.LOCAL_QUORUM)
session = Cluster(['10.0.1.11'], execution_profiles={EXEC_PROFILE_DEFAULT: profile}).connect('exam_live')

# per-statement override for high-volume, low-value data
log = SimpleStatement("INSERT INTO click_log (roll_no, ts, page) VALUES (%s, toTimestamp(now()), %s)",
                      consistency_level=ConsistencyLevel.LOCAL_ONE)
session.execute(log, (2401, 'results'))
''', 'Python driver (DataStax cassandra-driver)'),
        title='Example'),
    steps(
        ('Know your RF per DC', 'e.g. 3.'),
        ('Default to LOCAL_QUORUM', 'Strong consistency within the DC, tolerant of one replica down.'),
        ('Lower it for loss-tolerant data', 'LOCAL_ONE for telemetry.'),
        ('Use a DC-aware, token-aware load-balancing policy', 'Requests go to the local DC and directly to a replica.'),
        title='Steps'),
    crossq(
        ('With RF 3, what happens to a QUORUM read when two replicas are down?', 'It fails with an Unavailable exception: only 1 of the required 2 '
         'replicas can respond. ONE would still succeed.'),
        ('Does a write at ONE reach only one node?', 'No: it is sent to all replicas; the coordinator just replies after the first acknowledgement. The '
         'other replicas usually receive it milliseconds later.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('How do replicas become consistent again? Explain hinted handoff, read repair and anti-entropy repair.', 'Hints & Repair', minutes=10, cards=[
    definition(
        table(['Mechanism', 'When', 'How'], [
            ['Hinted handoff', 'A replica is down during a write', 'Coordinator stores a hint (up to <code>max_hint_window</code>, 3 h default) and replays it when the node returns'],
            ['Read repair', 'During reads at CL > ONE that find different data', 'Coordinator merges, returns the newest data and writes it to stale replicas (blocking)'],
            ['Anti-entropy repair', 'Scheduled maintenance (<code>nodetool repair</code>)', 'Merkle trees compare token ranges between replicas; mismatched ranges are streamed'],
        ]),
        p('Hints and read repair are opportunistic. Only regular <strong>repair</strong> guarantees convergence, and every token range must be repaired at '
          'least once within <code>gc_grace_seconds</code> so that tombstones reach all replicas before they are purged. Most sites schedule it '
          'with Cassandra Reaper; newer releases are adding a built-in repair scheduler.', top=True),
        tags('Hinted handoff', 'Read repair', 'Anti-entropy', 'Merkle tree', 'nodetool repair', 'Incremental repair', 'Reaper'),
    ),
    analogy('A teacher misses a staff meeting: a colleague keeps a <strong>note for them</strong> (hint). If a parent notices two teachers giving '
            'different dates, the right date is told to both (read repair). And once a week all <strong>registers are compared line by line</strong> '
            '(repair) to catch anything missed.'),
    repair_anim(),
    real_world(
        scenario('A node down for a day',
                 p('A node was down for 26 hours for a disk replacement, longer than the 3-hour hint window. After it rejoined, the team ran '
                   '<code>nodetool repair -full</code> on it before letting it serve reads at ONE, so it did not return stale data or resurrect deleted rows.')),
    ),
    example(
        sh('''
$ nodetool repair -pr cdac             # primary-range repair: run on every node in turn
$ nodetool repair -full cdac attempts  # full repair of one table
$ nodetool repair cdac                 # incremental (default since 4.0)
$ nodetool listpendinghints
$ nodetool statushandoff
''', 'Repair and hints (real cluster)'),
        conf('''
hinted_handoff_enabled: true
max_hint_window: 3h
# table-level read repair behaviour (4.0+): BLOCKING (default) or NONE
-- ALTER TABLE cdac.attempts WITH read_repair = 'BLOCKING';
''', 'Settings'),
        title='Example'),
    steps(
        ('Schedule repairs', 'Every range within gc_grace_seconds (e.g. weekly with 10-day gc_grace), typically with Cassandra Reaper.'),
        ('Repair after long outages', 'Any node down longer than max_hint_window.'),
        ('Use -pr when running on every node', 'Avoids repairing each range RF times.'),
        ('Monitor repair duration', 'Long repairs often point to large partitions or overloaded nodes.'),
        title='Steps'),
    crossq(
        ('Full vs incremental repair?', 'Full repair compares all data. Incremental repair (default since 4.0) marks repaired SSTables and only compares '
         'unrepaired data afterwards, which is much faster for regular runs.'),
        ('What happens if you never run repair?', 'Replicas slowly diverge, reads at low consistency return stale data, and deletes can be resurrected '
         'after gc_grace_seconds.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do nodes discover each other and detect failures? How do you add or remove a node?', 'Gossip & Cluster Membership', minutes=9, cards=[
    definition(
        defbox('<strong>Gossip</strong>: every second each node exchanges versioned state (status, load, schema version, tokens) with up to three other '
               'nodes, so cluster state spreads quickly with no central coordinator. <strong>Seed nodes</strong> are the first contacts for joining nodes.',
               '<strong>Failure detection</strong>: the phi accrual failure detector uses heartbeat inter-arrival times to estimate how likely a node is to '
               'be down (<code>phi_convict_threshold</code>, default 8) and marks it DOWN locally.',
               '<strong>Membership operations</strong>: <em>bootstrap</em> (new node takes tokens and streams data), <em>decommission</em> (live node '
               'streams its data away and leaves), <em>removenode</em> (remove a dead node; others re-replicate), <em>replace</em> '
               '(<code>-Dcassandra.replace_address_first_boot=&lt;ip&gt;</code> for a failed node), <em>cleanup</em> (drop data a node no longer owns).'),
        tags('Gossip', 'Seed node', 'Phi accrual', 'Bootstrap', 'Decommission', 'removenode', 'nodetool cleanup'),
    ),
    analogy('Staff in a large office <strong>pass news along in corridor chats</strong>; within minutes everyone knows who is on leave. A new joiner '
            'first meets the <strong>receptionist</strong> (seed), who introduces them to everyone, and then takes over some files from colleagues.'),
    gossip_anim(),
    real_world(
        scenario('Scaling out before admissions',
                 p('Before admission season the team added two nodes per rack: each new node bootstrapped (streaming its share from all others thanks to '
                   'vnodes), then <code>nodetool cleanup</code> was run on the old nodes to delete data they no longer owned and recover disk space.')),
    ),
    example(
        sh('''
# add a node: same cluster_name, seeds and snitch; auto_bootstrap defaults to true
$ sudo systemctl start cassandra
$ nodetool status            # new node shows UJ (joining), then UN
$ nodetool cleanup           # afterwards, on each OLD node

# remove a healthy node
$ nodetool decommission      # run on the node that is leaving (shows UL)

# remove a dead node
$ nodetool removenode <host-id>

# replace a dead node with a new machine using the same tokens
$ cassandra -Dcassandra.replace_address_first_boot=10.0.2.12

$ nodetool gossipinfo        # raw gossip state
$ nodetool describecluster   # schema versions (should be one)
''', 'Membership operations (real cluster)'),
        title='Example'),
    steps(
        ('Add one node at a time', 'Wait until it is UN before adding the next.'),
        ('Run cleanup on old nodes', 'After all additions are finished.'),
        ('Decommission live nodes, removenode dead ones', 'Never just switch a node off for good.'),
        ('Keep 2–3 seeds per DC', 'Seeds should be stable, not every node.'),
        title='Steps'),
    crossq(
        ('Why should a seed node not bootstrap?', 'Seeds do not auto-bootstrap (they assume they are founding members), so adding a new node as a seed '
         'skips streaming and leaves it without data. Add it as a normal node first, then list it as a seed.'),
        ('What does "schema disagreement" mean?', 'Nodes report different schema versions in <code>nodetool describecluster</code>, usually after '
         'concurrent DDL or a node being down; avoid running DDL from several clients at once.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('What are lightweight transactions (LWT)? When should you use them?', 'Lightweight Transactions', minutes=9, cards=[
    definition(
        defbox('A <strong>lightweight transaction</strong> is a conditional write that is applied only if a condition holds on the current data: '
               '<code>INSERT … IF NOT EXISTS</code>, <code>UPDATE … IF col = value</code>, <code>UPDATE/DELETE … IF EXISTS</code>. It gives '
               '<strong>linearizable compare-and-set</strong> on a single partition, implemented with the <strong>Paxos</strong> consensus protocol among '
               'the partition\'s replicas.',
               'The response has an <code>[applied]</code> column; when false, it also returns the current values so the client can decide what to do. '
               'Costs: several round trips (Paxos v2 in 5.0 reduces them), contention on hot rows, and reads should use <code>SERIAL</code>/'
               '<code>LOCAL_SERIAL</code> to see in-progress LWT results. Do not mix LWT and non-LWT writes on the same data.'),
        tags('LWT', 'IF NOT EXISTS', 'IF condition', 'Paxos', 'Compare-and-set', 'SERIAL', '[applied]'),
    ),
    analogy('Booking a <strong>seat in an exam hall</strong> by phone: the clerk checks the seat chart, confirms with two colleagues that nobody else '
            'is booking it right now, and only then writes your name. Slower than writing directly, but two people never get the same seat.'),
    lwt_anim(),
    real_world(
        scenario('Where LWT is the right tool',
                 ul('Unique username or email at registration (<code>IF NOT EXISTS</code>).',
                    'Allocating a limited lab seat (<code>IF seats_left = 3</code>, then set it to 2).',
                    'State machines: move an exam attempt from "started" to "submitted" only once (<code>IF status = \'started\'</code>).')),
    ),
    example(
        cql('''
CREATE TABLE usernames (username text PRIMARY KEY, roll_no int);

INSERT INTO usernames (username, roll_no) VALUES ('anuj24', 2401) IF NOT EXISTS;
INSERT INTO usernames (username, roll_no) VALUES ('anuj24', 2417) IF NOT EXISTS;

CREATE TABLE exam_attempts (exam text, roll_no int, status text, PRIMARY KEY (exam, roll_no));
INSERT INTO exam_attempts (exam, roll_no, status) VALUES ('SQL-2026-10', 2401, 'started');

UPDATE exam_attempts SET status = 'submitted' WHERE exam = 'SQL-2026-10' AND roll_no = 2401 IF status = 'started';
-- a duplicate submit (double click, retry) is rejected and shows the current state
UPDATE exam_attempts SET status = 'submitted' WHERE exam = 'SQL-2026-10' AND roll_no = 2401 IF status = 'started';

UPDATE exam_attempts SET status = 'cancelled' WHERE exam = 'SQL-2026-10' AND roll_no = 2499 IF EXISTS;
'''),
        title='Example'),
    steps(
        ('Use LWT only where a race matters', 'Uniqueness, single-use tokens, state transitions.'),
        ('Check [applied]', 'Handle the false case using the returned current values.'),
        ('Read with SERIAL if you need in-flight LWT results', 'Otherwise a read at QUORUM may miss an uncommitted Paxos proposal.'),
        ('Avoid hot LWT rows', 'Many clients contending on one partition causes retries and timeouts.'),
        title='Steps'),
    crossq(
        ('Are LWTs ACID transactions?', 'They are atomic and isolated for <strong>one partition</strong> only. Cassandra 5.0 does not have general '
         'multi-partition transactions; the Accord protocol (CEP-15) for ACID transactions is planned for a later release.'),
        ('Why not use LWT for every write?', 'Each LWT needs several round trips between replicas, so latency is roughly 4× and throughput much lower; '
         'contention makes it worse.'),
    ),
]),
])
