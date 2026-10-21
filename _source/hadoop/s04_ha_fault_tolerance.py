from build import *
from hadoop.anims import *
from hadoop.runner import sh, xml

SECTION = dict(level='intermediate', title='High Availability & Fault Tolerance', questions=[

# ------------------------------------------------------------------ 19
Q('How does NameNode High Availability work?', 'NameNode HA', minutes=9, cards=[
    definition(
        defbox('In Hadoop 1 the NameNode was a <strong>single point of failure (SPOF)</strong>: if it went down, the whole file system '
               'was unavailable. <strong>HDFS High Availability</strong> (Hadoop 2+) runs an <strong>Active</strong> and one or more '
               '<strong>Standby</strong> NameNodes that share the edit log through a quorum of <strong>JournalNodes</strong>, with '
               '<strong>ZooKeeper</strong> and <strong>ZKFC</strong> handling automatic failover.'),
        tags('High Availability', 'Active/Standby', 'JournalNode', 'QJM', 'ZKFC', 'ZooKeeper', 'Fencing', 'Split-brain'),
    ),
    ha_anim(),
    explanation(
        table(['Component', 'Role'], [
            ['JournalNodes (odd number, ≥ 3)', 'Store the shared edit log; a write needs a majority, so 3 JNs tolerate 1 failure, 5 tolerate 2'],
            ['Standby NameNode', 'Tails the edits, receives block reports, takes checkpoints; ready to take over in seconds'],
            ['ZKFC', 'Monitors local NameNode health; holds/competes for the active lock in ZooKeeper; triggers failover'],
            ['ZooKeeper (3 or 5 nodes)', 'Session tracking and the lock that decides who is active'],
            ['Fencing', 'Ensures the old Active can no longer act (JournalNodes accept writes only from the newest epoch; optional sshfence/shell fence)'],
            ['Logical nameservice', '<code>fs.defaultFS = hdfs://mycluster</code>; clients try the NameNodes listed for it and follow the active one'],
        ]),
        title='Building Blocks'),
    example(
        xml('''
<!-- hdfs-site.xml (abridged) -->
<property><name>dfs.nameservices</name><value>mycluster</value></property>
<property><name>dfs.ha.namenodes.mycluster</name><value>nn1,nn2</value></property>
<property><name>dfs.namenode.rpc-address.mycluster.nn1</name><value>master1:8020</value></property>
<property><name>dfs.namenode.rpc-address.mycluster.nn2</name><value>master2:8020</value></property>
<property><name>dfs.namenode.shared.edits.dir</name>
          <value>qjournal://jn1:8485;jn2:8485;jn3:8485/mycluster</value></property>
<property><name>dfs.client.failover.proxy.provider.mycluster</name>
          <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value></property>
<property><name>dfs.ha.automatic-failover.enabled</name><value>true</value></property>
''', 'hdfs-site.xml'),
        sh('''
hdfs haadmin -getServiceState nn1        # active | standby
hdfs haadmin -failover nn1 nn2           # planned (graceful) failover
'''),
        title='Configuration'),
    crossq(
        ('What is split-brain and how does HDFS prevent it?', 'Two NameNodes both believing they are active and both modifying the '
         'namespace, corrupting it. QJM prevents it: each new active gets a higher <em>epoch</em> number and JournalNodes reject writes '
         'with an older epoch, so a stale active cannot write edits.'),
        ('Why an odd number of JournalNodes?', 'A quorum needs a majority. 4 JNs tolerate only 1 failure, the same as 3, so the extra node adds cost without extra safety.'),
        ('Is the Secondary NameNode used in HA?', 'No. The Standby NameNode does the checkpointing, so running a Secondary NameNode in an HA cluster is an error.'),
    ),
]),

# ------------------------------------------------------------------ 20
Q('What is HDFS Federation? How is it different from HA?', 'HDFS Federation', minutes=7, cards=[
    definition(
        defbox('<strong>HDFS Federation</strong> runs several <strong>independent NameNodes</strong>, each managing its own part of '
               'the namespace (a <strong>namespace volume</strong>, e.g. <code>/user</code> on NN1, <code>/data</code> on NN2). All '
               'DataNodes store blocks for all NameNodes, in separate <strong>block pools</strong>.'),
        tags('Federation', 'Namespace Volume', 'Block Pool', 'ViewFs', 'Router-based Federation'),
    ),
    visual(
        svg('''<svg width="700" height="230" viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" font-family="Inter, sans-serif">
<rect width="700" height="230" fill="#1e293b"/>
<g font-size="13" font-weight="bold" text-anchor="middle" fill="#f1f5f9">
<rect x="40" y="20" width="180" height="56" rx="9" fill="#0ea5e9" fill-opacity="0.22" stroke="#0ea5e9" stroke-width="2"/><text x="130" y="44">NameNode 1</text>
<rect x="260" y="20" width="180" height="56" rx="9" fill="#8b5cf6" fill-opacity="0.22" stroke="#8b5cf6" stroke-width="2"/><text x="350" y="44">NameNode 2</text>
<rect x="480" y="20" width="180" height="56" rx="9" fill="#f59e0b" fill-opacity="0.22" stroke="#f59e0b" stroke-width="2"/><text x="570" y="44">NameNode 3</text></g>
<g font-size="11" fill="#cbd5e1" text-anchor="middle"><text x="130" y="62">/user · block pool 1</text><text x="350" y="62">/data · block pool 2</text><text x="570" y="62">/logs · block pool 3</text></g>
<g stroke="#64748b" stroke-width="1.5"><line x1="130" y1="76" x2="120" y2="140"/><line x1="130" y1="76" x2="350" y2="140"/><line x1="130" y1="76" x2="580" y2="140"/>
<line x1="350" y1="76" x2="120" y2="140"/><line x1="350" y1="76" x2="350" y2="140"/><line x1="350" y1="76" x2="580" y2="140"/>
<line x1="570" y1="76" x2="120" y2="140"/><line x1="570" y1="76" x2="350" y2="140"/><line x1="570" y1="76" x2="580" y2="140"/></g>
<g><rect x="40" y="140" width="160" height="70" rx="9" fill="#10b981" fill-opacity="0.2" stroke="#10b981" stroke-width="2"/>
<rect x="270" y="140" width="160" height="70" rx="9" fill="#10b981" fill-opacity="0.2" stroke="#10b981" stroke-width="2"/>
<rect x="500" y="140" width="160" height="70" rx="9" fill="#10b981" fill-opacity="0.2" stroke="#10b981" stroke-width="2"/></g>
<g font-size="12" fill="#f1f5f9" text-anchor="middle" font-weight="bold"><text x="120" y="160">DataNode</text><text x="350" y="160">DataNode</text><text x="580" y="160">DataNode</text></g>
<g font-size="10" text-anchor="middle"><text x="95" y="190" fill="#38bdf8">pool1</text><text x="120" y="190" fill="#a78bfa">pool2</text><text x="145" y="190" fill="#fbbf24">pool3</text>
<text x="325" y="190" fill="#38bdf8">pool1</text><text x="350" y="190" fill="#a78bfa">pool2</text><text x="375" y="190" fill="#fbbf24">pool3</text>
<text x="555" y="190" fill="#38bdf8">pool1</text><text x="580" y="190" fill="#a78bfa">pool2</text><text x="605" y="190" fill="#fbbf24">pool3</text></g>
</svg>''', 'Federation: independent NameNodes share all DataNodes; each owns a block pool')),
    comparison(
        table(['Aspect', 'High Availability', 'Federation'], [
            ['Problem solved', 'NameNode is a single point of failure', 'One NameNode\'s heap limits namespace size and throughput'],
            ['NameNodes', 'Active + Standby with the <strong>same</strong> namespace', 'Several active NameNodes with <strong>different</strong> namespaces'],
            ['If a NameNode fails', 'Standby takes over', 'Only its namespace volume is affected (each can also have HA)'],
            ['Client view', 'One nameservice', 'Mount table (ViewFs) or Router-based Federation for a unified view'],
        ]),
    ),
    crossq(
        ('Can you combine Federation and HA?', 'Yes, and large clusters do: each nameservice in the federation is an HA pair (or group).'),
        ('What is Router-based Federation (RBF)?', 'Hadoop 2.9+/3: stateless Router processes expose one global namespace and forward '
         'each request to the right sub-cluster using a mount table stored in a State Store, so clients need no ViewFs config.'),
    ),
]),

# ------------------------------------------------------------------ 21
Q('What happens when a DataNode fails? How does HDFS detect it?', 'DataNode Failure', minutes=7, cards=[
    definition(
        defbox('DataNodes send a <strong>heartbeat</strong> every 3 seconds (<code>dfs.heartbeat.interval</code>). If none arrives for '
               '<strong>2 × dfs.namenode.heartbeat.recheck-interval + 10 × dfs.heartbeat.interval</strong> = 2 × 5 min + 10 × 3 s = '
               '<strong>10.5 minutes</strong>, the NameNode marks the DataNode <strong>dead</strong> and re-replicates its blocks from the surviving copies.'),
        tags('Heartbeat', 'Dead Node', 'Under-replicated', 'Re-replication', 'Block Report'),
    ),
    dn_failure(),
    example(
        pyrun('''
heartbeat_s = 3          # dfs.heartbeat.interval
recheck_ms = 300_000     # dfs.namenode.heartbeat.recheck-interval
timeout_s = 2 * recheck_ms / 1000 + 10 * heartbeat_s
print(f"DataNode declared dead after {timeout_s:.0f} s = {timeout_s / 60} minutes")

# Rough time to re-replicate a dead node's data
dead_node_tb = 24
live_nodes = 99
per_node_mb_s = 50       # replication bandwidth each surviving node contributes
seconds = dead_node_tb * 1024**2 / (live_nodes * per_node_mb_s)
print(f"Re-replicating {dead_node_tb} TB across {live_nodes} nodes: ~{seconds / 3600:.1f} hours")
'''),
        title='Example: Detection Timeout and Recovery Time'),
    explanation(
        ul('<strong>Disk failure</strong> (not the whole node): by default (<code>dfs.datanode.failed.volumes.tolerated = 0</code>) the '
           'DataNode shuts down on one bad disk; set it to e.g. 1 or 2 so a node with many disks keeps running.',
           'Recovery is <strong>parallel across the cluster</strong>: many nodes copy a little each, which is why recovery is fast on large clusters.',
           'Re-replication is prioritised: blocks with only one remaining replica are copied first.',
           'A node that returns is not a problem: extra replicas are simply deleted.'),
        title='Points to Remember'),
    crossq(
        ('Why does the NameNode wait 10 minutes instead of acting immediately?', 'A short network glitch or a DataNode restart would '
         'otherwise trigger copying terabytes for nothing (a "replication storm"). Reads simply switch to other replicas in the meantime.'),
        ('What is a stale DataNode?', 'One that has not sent a heartbeat for 30 s (<code>dfs.namenode.stale.datanode.interval</code>). If '
         'enabled, the NameNode avoids it for reads/writes before it is declared dead.'),
    ),
]),

# ------------------------------------------------------------------ 22
Q('What is erasure coding in HDFS? When would you use it?', 'Erasure Coding', minutes=8, cards=[
    definition(
        defbox('<strong>Erasure coding (EC)</strong>, added in Hadoop 3, stores data cells plus computed <strong>parity</strong> '
               'cells instead of full copies. With the Reed-Solomon policy <code>RS-6-3-1024k</code>, every 6 data cells get 3 parity '
               'cells: any 3 of the 9 can be lost, at only <strong>50% storage overhead</strong> versus 200% for 3× replication.'),
        tags('Erasure Coding', 'Reed-Solomon', 'RS-6-3', 'Parity', 'Striping', 'Hadoop 3'),
    ),
    ec_anim(),
    example(
        pyrun('''
data_tb = 100
schemes = {
    "3x replication": (3.0, 2),          # stored multiplier, failures tolerated
    "RS-3-2":        ((3 + 2) / 3, 2),
    "RS-6-3":        ((6 + 3) / 6, 3),
    "RS-10-4":       ((10 + 4) / 10, 4),
}
print(f"{'scheme':<16}{'raw TB':>8}{'overhead':>10}{'tolerates':>11}")
for name, (mult, fails) in schemes.items():
    print(f"{name:<16}{data_tb * mult:>8.0f}{(mult - 1) * 100:>9.0f}%{fails:>8} lost")
'''),
        sh('''
hdfs ec -listPolicies
hdfs ec -enablePolicy -policy RS-6-3-1024k
hdfs ec -setPolicy -path /data/archive -policy RS-6-3-1024k   # applies to NEW files
hdfs ec -getPolicy -path /data/archive
'''),
        title='Example: Storage for 100 TB of Data'),
    comparison(
        table(['Aspect', '3× Replication', 'Erasure Coding'], [
            ['Storage overhead', '200%', '~40–67% depending on policy'],
            ['Read performance', 'Read a whole block from one local node', 'Striped reads from many nodes; no data locality'],
            ['Recovery', 'Simple copy', 'CPU-heavy decode + network reads from several nodes'],
            ['Small files', 'Fine', 'Wasteful (a file below one stripe still needs full parity)'],
            ['Best for', 'Hot data, frequently processed', 'Cold / warm data, archives, backups'],
        ]),
    ),
    crossq(
        ('Does setting an EC policy convert existing files?', 'No. The policy applies to files written afterwards. Existing files must be '
         'rewritten (e.g. copied with DistCp into the EC directory) to be erasure-coded.'),
        ('What is the minimum number of DataNodes for RS-6-3?', '9, one per cell of a stripe (more racks than 3 recommended for rack fault tolerance).'),
    ),
]),

# ------------------------------------------------------------------ 23
Q('How do you add or remove (decommission) a DataNode, and balance the cluster?', 'Commission, Decommission & Balancer', minutes=7, cards=[
    definition(
        defbox('<strong>Commissioning</strong> adds a node; <strong>decommissioning</strong> removes one <em>gracefully</em> by copying '
               'all its blocks elsewhere before it leaves. The <strong>balancer</strong> moves blocks so that disk usage is even across DataNodes.'),
        tags('Decommission', 'Commission', 'dfs.hosts.exclude', 'refreshNodes', 'Balancer', 'Maintenance Mode'),
    ),
    example(
        sh('''
# --- Decommission dn07 ---
echo "dn07.cdac.local" >> /etc/hadoop/conf/dfs.exclude    # file named in dfs.hosts.exclude
hdfs dfsadmin -refreshNodes                                # NameNode re-reads include/exclude
hdfs dfsadmin -report -decommissioning                     # wait for "Decommissioned"
# (YARN: add to yarn.resourcemanager.nodes.exclude-path, then yarn rmadmin -refreshNodes)

# --- Commission a new node ---
# install Hadoop + same config, add host to dfs.include and the workers file, then
hdfs --daemon start datanode
yarn --daemon start nodemanager
hdfs dfsadmin -refreshNodes

# --- Balance ---
hdfs balancer -threshold 10        # each node within 10 percentage points of the cluster average
hdfs dfsadmin -setBalancerBandwidth 104857600   # 100 MB/s per DataNode
hdfs diskbalancer -plan dn03       # Hadoop 3: balance disks INSIDE one DataNode
'''),
        title='Commands'),
    warn('Never just switch off several DataNodes at once to "remove" them. If they held all replicas of some blocks, that data '
         'is lost. Decommission waits until every block is safely replicated elsewhere.', 'Common Mistake'),
    crossq(
        ('Why are new nodes empty after being added?', 'HDFS does not move existing blocks automatically; only new writes use the new '
         'node. Run the balancer to spread existing data.'),
        ('What is maintenance mode?', 'Hadoop 2.9+/3: a node can be taken down briefly (e.g. OS patching) without full re-replication, as '
         'long as a minimum number of replicas stays available elsewhere.'),
    ),
]),
])
