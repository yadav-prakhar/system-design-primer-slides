## Section 2: CAP Theorem, Consistency & Availability Patterns

---

## Part A: CAP Theorem

### Slide 1: CAP Theorem — Concept Introduction
- CAP stands for Consistency, Availability, Partition Tolerance
  - A theorem by Eric Brewer (2000) about distributed data stores
- A distributed system can guarantee at most TWO of the three at the same time
  - You cannot escape the trade-off when a network partition occurs
- Partition Tolerance is non-negotiable in real distributed systems
  - Networks fail; you must handle dropped or delayed messages between nodes
- Therefore the realistic choice is between CP and AP, not CA
  - CA only exists in single-node or assumed-perfect-network systems
- CAP guides architectural decisions for databases, caches, and messaging systems
  - Different workloads (banking vs social feed) tolerate different sacrifices
[Visual suggestion: a triangle with C, A, P at the corners; three overlapping circles; highlight that during a partition you must drop either C or A]

---

### Slide 2: CAP — Defining the Three Properties Precisely
- Consistency (C): every read receives the most recent write or an error
  - Equivalent to linearizability — all clients see the same data at the same time
- Availability (A): every request receives a non-error response (no guarantee it is the latest)
  - The system stays responsive even if data is stale
- Partition Tolerance (P): the system continues to operate despite network message loss between nodes
  - The cluster does not collapse when a link breaks
- "Pick 2" is misleading — it really means "during a partition, pick C or A"
  - When the network is healthy, you can have both C and A
- CAP is about the worst-case behavior, not steady-state behavior
  - The trade-off shows up only when partitions happen
[Visual suggestion: a 2-column comparison: "Healthy network → C + A possible" vs "Partition → choose C or A"]

---

### Slide 3: CAP Theorem — Deep Explanation (How the Trade-off Plays Out)
- Imagine two replicas separated by a broken link receiving conflicting writes
  - Replica A gets value X=10, replica B gets value X=20, neither can sync
- A CP system refuses one of the writes (or blocks reads) to preserve correctness
  - Sacrifices availability — the client gets an error or timeout
- An AP system accepts both writes and reconciles later (last-write-wins, vector clocks, CRDTs)
  - Sacrifices consistency — clients may read stale or divergent data temporarily
- The choice is fundamentally about user experience and business risk
  - "Wrong answer" vs "no answer" — pick which one your domain can survive
- CAP is not binary in practice; tunable consistency (Cassandra, DynamoDB) lets you slide along the spectrum
  - You set quorum levels per operation: stricter for money, looser for likes
[Visual suggestion: timeline showing partition at T=5s; CP path shows "request blocked"; AP path shows "request served, reconcile at T=12s"]

---

### Slide 4: CP Systems — Concept and Examples
- CP = Consistent + Partition Tolerant; sacrifices availability during partitions
  - The system would rather return an error than risk stale data
- Use when correctness matters more than uptime
  - Banking ledgers, inventory counts, distributed locks, leader election
- HBase: built on HDFS, uses a single RegionServer per region — strong consistency, no split-brain
  - If the RegionServer is unreachable, that region becomes unavailable until failover
- ZooKeeper: coordination service using ZAB protocol; majority quorum required for writes
  - Loses availability when fewer than (N/2)+1 nodes are reachable, but never lies
- etcd, Google Spanner (with Paxos), MongoDB (in majority write concern) follow the same pattern
  - All choose to halt rather than serve potentially incorrect data
[Visual suggestion: 5-node ZooKeeper cluster, 2 nodes partitioned off; minority side rejects writes, majority continues]

---

### Slide 5: AP Systems — Concept and Examples
- AP = Available + Partition Tolerant; sacrifices strict consistency during partitions
  - Always returns a response, even if the data might be stale
- Use when uptime and responsiveness matter more than perfect freshness
  - Social feeds, shopping carts, DNS, content delivery, analytics
- Cassandra: peer-to-peer ring, tunable consistency, gossip-based replication
  - Writes accepted at any node; conflicts resolved by last-write-wins timestamp
- DynamoDB: AWS's managed AP store with eventual consistency by default
  - Optional "strongly consistent reads" trade availability for freshness
- Riak, CouchDB, Voldemort follow Amazon's Dynamo paper design
  - All embrace temporary divergence and reconcile via vector clocks or merge functions
[Visual suggestion: Cassandra ring with 6 nodes; partition splits 3 vs 3; both sides keep accepting writes; arrows show later reconciliation]

---

### Slide 6: CA Systems — Why They Are Not Realistic in Distributed Systems
- CA = Consistent + Available, but only when there are no partitions
  - In practice, distributed networks always partition eventually
- A single-node relational database (PostgreSQL, MySQL standalone) is "CA"
  - But it is not actually distributed — there is no partition to tolerate
- Two-phase commit clusters are sometimes called CA, but they freeze under partitions
  - That freezing IS sacrificing availability, so they are really CP
- Believing you have CA usually means you have unaccounted-for risk
  - Your "always-on" assumption breaks the moment a switch flaps
- The honest framing: distributed systems must pick between CP and AP
  - CA is a marketing label, not an engineering reality
[Visual suggestion: a triangle with "CA" corner crossed out and labeled "single-node only"; arrow pointing to "real distributed = CP or AP"]

---

### Slide 7: CAP — Banking vs Social Media Analogy
- ATM withdrawal (CP): bank refuses to dispense cash if it cannot verify your balance
  - Better to say "service unavailable" than to let you overdraw
- Twitter timeline (AP): you see tweets even if the count is slightly stale
  - "37 likes" vs "39 likes" — nobody dies, the app stays usable
- DNS (AP): cached records may be stale but resolution always succeeds
  - Eventual propagation across the globe is acceptable for name lookups
- Stock trading exchange (CP): a trade must reflect the true order book
  - Showing wrong prices could cause millions in losses, so halt instead
- Picking CP vs AP is fundamentally a product decision, not a tech decision
  - Engineering serves the cost of being wrong vs the cost of being down
[Visual suggestion: split panel — left "ATM screen showing Service Unavailable", right "Twitter feed loading with stale like counts"]

---

### Slide 8: CAP Theorem — Diagram Slide
- Draw the canonical CAP triangle with three vertices
  - C (Consistency), A (Availability), P (Partition Tolerance)
- Show three overlapping regions on the edges
  - CP edge: HBase, ZooKeeper, etcd, Spanner
  - AP edge: Cassandra, DynamoDB, Riak, CouchDB
  - CA edge: traditional RDBMS (single node) — mark as "not truly distributed"
- Add a horizontal "partition occurred" line through the middle
  - Above it: healthy state, all three achievable
  - Below it: must drop either C or A
- Annotate each system with its trade-off rationale
  - e.g., "ZooKeeper: blocks minority side to avoid split-brain"
[Visual suggestion: equilateral triangle with vertex labels, system logos placed on edges, dashed "partition line" cutting across the middle]

---

### Slide 9: CAP Theorem — Trade-offs Slide
- CP trade-off: stronger correctness, but you must tolerate downtime windows
  - Failover is slow because the system pauses until quorum re-forms
- AP trade-off: always-on UX, but clients must handle stale or conflicting data
  - Application code becomes more complex (conflict resolution, retries)
- Latency cost in CP: every write waits for quorum acknowledgment
  - Cross-region writes can take 100s of ms or fail outright
- Operational cost in AP: you need monitoring for replication lag and divergence
  - Hidden bugs show up only under partition or load
- The trade-off is not permanent; it is per-operation when using tunable consistency
  - Read at quorum for the cart total, read at ONE for product images
[Visual suggestion: a 2x2 matrix — rows: CP/AP; columns: Pros/Cons — filled with bullet points above]

---

## Part B: Consistency Patterns

### Slide 10: Consistency Patterns — Concept Introduction
- Consistency defines what guarantees a system makes about read-after-write visibility
  - "If I write X=5, when will I (or others) see X=5?"
- Three main models on a spectrum: weak, eventual, strong
  - From "no promises" to "immediately and forever"
- The right model depends on the data's tolerance for staleness
  - Likes count → eventual; bank balance → strong
- Stronger consistency costs more latency, throughput, and availability
  - You pay in coordination overhead for every write
- Many real systems mix models per data type within the same application
  - User profile (eventual) + payment record (strong) in one product
[Visual suggestion: horizontal bar from "Weak" → "Eventual" → "Strong" with example workloads under each]

---

### Slide 11: Weak Consistency — Deep Explanation
- After a write, reads may or may not see the new value, with no guarantee at all
  - The system makes a best-effort attempt and moves on
- Common in real-time systems where freshness beats correctness
  - Live video, VoIP, online multiplayer game state
- Implementation: no replication coordination, no read-after-write guarantee
  - Each node serves whatever it has locally; missed updates are simply lost or ignored
- Memcached without invalidation is effectively weak consistency
  - Stale entries linger until TTL expires; nobody guarantees freshness
- Trade you accept: lowest latency, highest throughput, but unpredictable correctness
  - Acceptable when the user can re-issue the request or the data self-corrects
[Visual suggestion: client writes X=5; three subsequent reads return 5, undefined, 3 — with arrows showing no coordination between replicas]

---

### Slide 12: Weak Consistency — Example and Analogy
- Live sports score broadcast: if you miss a goal, you don't replay it — next update overrides
  - The system never blocks waiting for stragglers
- Voice over IP: dropped audio packets are skipped, not retransmitted
  - Latency budget is too tight to wait
- Multiplayer game position updates: only the latest position matters
  - Old "I was at (10, 20)" packets are useless once "I am at (15, 25)" arrives
- Stock ticker on a public site: shows approximate prices, not authoritative
  - The actual trade settlement uses a different (strong) system
- Analogy: shouting across a noisy room — receivers hear what they hear, no acknowledgments
  - You rely on the next shout to overwrite any miss
[Visual suggestion: a stadium with thousands listening to a live commentator; if your audio glitches, you just hear the next sentence]

---

### Slide 13: Eventual Consistency — Deep Explanation
- After a write, replicas will converge to the same value if no new writes occur
  - Given enough time, all nodes will agree, but "eventually" can mean ms to minutes
- Reads can return stale data temporarily — your own write may not be visible immediately
  - Read-your-writes is a stronger sub-guarantee that some systems add on top
- Implementation: asynchronous replication, gossip protocols, anti-entropy repair
  - Background processes propagate updates and reconcile divergence
- Conflict resolution strategies needed when two replicas accept conflicting writes
  - Last-Write-Wins (timestamp), vector clocks, CRDTs, application-level merge
- DynamoDB, Cassandra, DNS, S3 (historically), email all operate eventually consistent
  - Each chose availability and partition tolerance over instant consistency
[Visual suggestion: 3 replicas; write at T=0 to replica 1; gossip arrows propagate at T=2s, T=5s; all converged by T=10s]

---

### Slide 14: Eventual Consistency — DNS Analogy
- DNS records have TTLs (Time To Live); changes propagate over hours
  - You change an A record, but resolvers worldwide still serve the old IP until cache expires
- Eventually all DNS resolvers converge to the new value
  - There is no global lock, no coordination — just timeout-based refresh
- This is acceptable because DNS prioritizes availability and scale over instant updates
  - Internet-wide propagation in milliseconds would require a coordination layer DNS doesn't have
- Email is similar: a sent message may take seconds to minutes to appear in the inbox
  - Spam filters, routing, and delivery agents add latency without breaking the system
- Shopping cart in Amazon's original Dynamo: if two devices add items, both items end up in the cart
  - "Add to cart" is mergeable — eventual consistency works because conflicts are union-able
[Visual suggestion: world map; DNS update originates in US-East; clock ticks show propagation reaching EU at T=2min, Asia at T=5min]

---

### Slide 15: Strong Consistency — Deep Explanation
- After a write completes, every subsequent read returns that value or a newer one
  - Equivalent to having a single, atomic copy of the data globally
- Linearizability: operations appear to execute instantaneously in a total order
  - This is the "ideal" but expensive guarantee
- Implementation requires coordination: consensus protocols (Paxos, Raft, ZAB)
  - A majority quorum must agree before a write is acknowledged
- Examples: Google Spanner (TrueTime + Paxos), CockroachDB, etcd, ZooKeeper, traditional RDBMS
  - All pay latency cost for guaranteed correctness
- Cost: every write incurs at least one round-trip to a quorum
  - Cross-region clusters add tens to hundreds of ms per write
[Visual suggestion: client → leader → 2 of 3 followers must ACK → leader responds OK; show the latency arrow grow with each hop]

---

### Slide 16: Strong Consistency — Banking Analogy
- Bank balance must reflect every deposit and withdrawal immediately
  - You cannot "eventually" have $500; either you have it now or you don't
- Two ATMs withdrawing from the same account must coordinate
  - Otherwise both succeed, the balance goes negative, and the bank loses money
- Inventory in an e-commerce checkout (last unit) — must be strongly consistent
  - Selling the same physical item twice creates customer-service disasters
- Distributed locks (ZooKeeper, etcd) — only one client can hold the lock
  - Eventual consistency would let two clients both think they have it (split-brain)
- Strong consistency = "the truth is one, and everyone sees it the same way"
  - Worth the latency for correctness-critical workloads
[Visual suggestion: two ATMs both trying to withdraw $100 from a $150 account; coordinator allows one and rejects the other]

---

### Slide 17: Consistency Patterns — Comparison Diagram
- Draw three horizontal lanes representing the three models
  - Lane 1: Weak — write at T=0; reads return random values, no guarantees
  - Lane 2: Eventual — reads return old values briefly; converge to new value at T=convergence
  - Lane 3: Strong — read at any T after write returns the new value, always
- Add latency bars showing relative write cost
  - Weak: lowest; Eventual: medium; Strong: highest
- Add availability bars showing tolerance to partitions
  - Weak/Eventual: high availability; Strong: drops during partition
- Mark example systems on each lane
  - Weak: VoIP, live video; Eventual: DNS, Cassandra, S3; Strong: Spanner, etcd, RDBMS
- Add a "tunable consistency" callout for systems like Cassandra and DynamoDB
  - Same system can shift between lanes per operation via quorum settings
[Visual suggestion: 3 horizontal timelines stacked vertically with color-coded write/read events and latency bars]

---

### Slide 18: Consistency Patterns — Trade-offs Slide
- Weak: maximum performance, but data may be silently wrong
  - Only safe when staleness is invisible or self-correcting
- Eventual: high availability and scalability, but app must handle stale reads
  - Need conflict resolution and possibly read-your-writes guarantees
- Strong: developer-friendly correctness, but latency and availability costs
  - Cross-region strong consistency can make writes 10x slower
- Mixed strategies are typical in production
  - Strong for money flows, eventual for feeds, weak for telemetry
- Choosing too strong is a common over-engineering trap
  - Costs throughput and availability for guarantees you didn't actually need
[Visual suggestion: 3-column table — Weak | Eventual | Strong — rows: Latency, Availability, Complexity, Use cases]

---

## Part C: Availability Patterns

### Slide 19: Availability Patterns — Concept Introduction
- Availability = the percentage of time the system is operational and serving requests
  - Measured as uptime divided by total time, expressed as "nines"
- Two main techniques to achieve high availability: fail-over and replication
  - Fail-over swaps in a backup; replication keeps multiple live copies
- Availability is multiplicative across dependencies in a chain
  - 99.9% × 99.9% × 99.9% = 99.7% — each hop reduces overall availability
- High availability requires eliminating single points of failure (SPOFs)
  - Redundancy in compute, storage, network, and even regions
- Availability is expensive — each additional "nine" costs roughly 10x more
  - 99% to 99.9% is doable; 99.999% requires multi-region active-active and obsessive ops
[Visual suggestion: pyramid showing cost vs nines — base "99%" wide; tip "99.999%" narrow with $$$$ label]

---

### Slide 20: Fail-over — Concept and Mechanisms
- Fail-over = automatically switching to a standby system when the primary fails
  - Detection (heartbeats, health checks) → promotion (standby takes over) → traffic redirect
- Two flavors: active-passive and active-active
  - Differ in whether the standby is idle or already serving traffic
- Detection time + promotion time = recovery time objective (RTO)
  - Faster detection means faster recovery but more false positives
- Common mechanism: virtual IPs, DNS failover, load balancer health checks, leader election
  - Each adds latency and complexity to the failover path
- Fail-over is reactive — it kicks in after something breaks
  - Replication is proactive — multiple copies always serve in parallel
[Visual suggestion: primary server with heartbeat to standby; primary fails (red X); standby promoted; clients redirected via VIP]

---

### Slide 21: Active-Passive Fail-over — Deep Explanation
- One active node serves all traffic; the passive node stands by, often replicating data
  - Passive does no useful work until the active dies
- Cheaper to operate (less load on standby) but slower to recover
  - Promotion can take seconds to minutes depending on the technology
- Common in traditional RDBMS clusters (PostgreSQL streaming replication, MySQL with MHA)
  - Read replicas may serve read-only traffic while waiting to promote
- Risk: split-brain if both nodes think they are active simultaneously
  - Mitigated with fencing (STONITH), witness nodes, or quorum-based election
- RTO is typically 30 seconds to 5 minutes; RPO depends on replication mode
  - Synchronous replication = zero data loss; async = potential lag
[Visual suggestion: client → load balancer → active DB; passive DB receives async replication; on failure, LB switches arrow to passive]

---

### Slide 22: Active-Active Fail-over — Deep Explanation
- Multiple nodes serve traffic concurrently; if one fails, the others absorb the load
  - No promotion delay — surviving nodes continue without interruption
- Higher cost (all nodes provisioned for full capacity) but near-zero RTO
  - Used when downtime tolerance is in the milliseconds (financial trading, large web apps)
- Requires data to be replicated in all directions (multi-master) or sharded with redundancy
  - Conflict resolution becomes mandatory if writes go to multiple primaries
- Examples: Cassandra rings, DynamoDB global tables, Galera Cluster for MySQL
  - All nodes accept reads and writes, gossip changes, reconcile conflicts
- Capacity planning: must size each node to handle the failure load
  - If you have 3 active nodes and one fails, the remaining 2 must absorb 50% more traffic
[Visual suggestion: 3 active nodes behind LB, all serving traffic; one fails; arrows redistribute to remaining 2 with thicker stroke]

---

### Slide 23: Fail-over — Banking and Web Analogy
- Active-passive: a backup generator at a hospital — silent until the power cuts out
  - Costs money to maintain but only kicks on when needed
- Active-active: multiple cashiers at a bank counter — if one leaves, others keep serving
  - All are working all the time; no waiting period when one disappears
- Active-passive in web infra: PostgreSQL primary + hot standby with pgpool or Patroni
  - Standby promotes on failure, DNS or VIP redirects clients
- Active-active in web infra: AWS Route 53 latency routing across us-east-1 and us-west-2
  - Both regions live; user routed to nearest healthy region
- Choose based on RTO budget and operational maturity
  - Active-active is more powerful but harder to get right
[Visual suggestion: split panel — left "hospital with backup generator (active-passive)"; right "supermarket checkout lanes (active-active)"]

---

### Slide 24: Replication — Master-Slave (Primary-Replica) Pattern
- One master accepts writes; one or more slaves replicate the master's data
  - Reads can be load-balanced across slaves to scale read throughput
- Replication can be synchronous (master waits for slave ACK) or asynchronous (fire and forget)
  - Sync = stronger durability, higher latency; async = faster writes, possible data loss on failover
- Slave promotion is required if the master dies — this is the failover path
  - Slaves are often consistent with the master with some replication lag
- MySQL replication, PostgreSQL streaming replication, MongoDB replica sets
  - All variants of master-slave with different lag and consistency semantics
- Read-write split is a common pattern: app routes writes to master, reads to slaves
  - Beware of read-your-writes anomalies caused by replication lag
[Visual suggestion: master in center; 3 slaves with replication arrows; client writes go to master, reads fan out to slaves]

---

### Slide 25: Replication — Master-Master (Multi-Master) Pattern
- Multiple masters all accept writes; changes replicate to each other
  - No single write bottleneck; geographic distribution feels local to each region
- Conflict resolution is mandatory because two masters can write the same key concurrently
  - Strategies: last-write-wins, custom merge, CRDTs, application-level resolution
- Active-active deployments often use master-master to avoid promotion delays
  - Examples: MySQL Galera, CockroachDB, Cassandra (no master at all — peer-to-peer)
- Stronger availability and write scalability, but harder to reason about
  - You must design schemas and writes to be idempotent and conflict-aware
- Replication lag still exists; cross-region writes may not be visible everywhere immediately
  - Treat the system as eventually consistent unless explicitly using strong consistency mode
[Visual suggestion: 3 masters in a triangle, all replicating to each other; clients in each region write to nearest master]

---

### Slide 26: Replication — Failure Modes and Diagrams
- Replication lag: slaves fall behind under heavy write load
  - User writes a comment, reads back, sees nothing — confusing UX
- Split-brain: in master-master, network partition causes both sides to accept conflicting writes
  - Reconciliation can lose data unless conflict-free types are used
- Cascading failure: master dies, all reads go to a single overloaded slave, slave dies too
  - Mitigate with capacity headroom and read-traffic shedding
- Stale replicas serving reads: caused by lag or partition
  - Use "read from primary" for critical reads, "read from replica" for non-critical
- Replication topology choices: chain, tree, star, mesh
  - Affect propagation latency and resilience
[Visual suggestion: master with a queue showing 30s of unreplicated writes piling up; one slave shown as "lagging"]

---

### Slide 27: Replication — Diagram Slide
- Top half: master-slave topology
  - 1 master with arrows to N slaves; client write arrow to master; client read arrows split
- Bottom half: master-master topology
  - 3 nodes in a ring with bidirectional arrows; clients connect to any node for read/write
- Annotate with lag indicators on the replication arrows
  - "async ~50ms" or "sync ~5ms" labels
- Show a failover scenario in a side panel
  - Master fails (red X); one slave promoted (gold star); clients re-route
- Add a legend distinguishing sync vs async arrows
  - Solid line = sync, dashed line = async
[Visual suggestion: layered diagram with master-slave above and master-master below, sharing a legend on the right]

---

### Slide 28: Availability in Numbers — Concept Introduction
- Availability is expressed in "nines": 99%, 99.9%, 99.99%, 99.999%
  - Each extra nine represents 10x less downtime
- 99% = 3.65 days of downtime per year (acceptable for non-critical internal tools)
  - 8.76 hours per month; ~1.68 hours per week
- 99.9% (three nines) = 8.76 hours per year (typical web service SLA)
  - 43.2 minutes per month; ~10 minutes per week
- 99.99% (four nines) = 52.6 minutes per year (high-availability systems)
  - 4.38 minutes per month; ~1 minute per week
- 99.999% (five nines) = 5.26 minutes per year (telecom, financial systems)
  - 26 seconds per month — requires multi-region active-active and very mature ops
[Visual suggestion: table with columns "Nines | Downtime/year | Downtime/month | Downtime/week | Examples"]

---

### Slide 29: Availability in Numbers — Deep Explanation and Math
- SLA (Service Level Agreement): contractual availability promise to customers
  - Often comes with credits if breached (e.g., 10% refund if monthly uptime <99.9%)
- SLO (Service Level Objective): internal target, usually stricter than SLA
  - Engineering aims for 99.95% to safely meet a 99.9% SLA
- SLI (Service Level Indicator): the actual measured metric (success rate, latency)
  - SLO is "this metric must be ≥ X%" over a window
- Availability composes multiplicatively in series, additively in parallel
  - 3 services chained at 99.9% each = 99.7% overall
  - 2 redundant 99% services in parallel ≈ 99.99% combined (1 - 0.01²)
- Always count dependency availability: DNS, CDN, load balancer, database
  - Your max possible uptime is the product of your weakest links
[Visual suggestion: chain of 3 boxes labeled "99.9%" with the result "99.7%" at the end; below: 2 parallel boxes "99%" with result "99.99%"]

---

### Slide 30: Availability in Numbers — Real-World SLA Examples
- AWS S3: 99.99% (four nines) availability SLA for standard storage
  - Backed by multi-AZ replication and erasure coding
- AWS EC2: 99.99% for instances within a region; multi-AZ deployment recommended
  - Single-AZ deployments fall to ~99.95% in practice
- Google Cloud Spanner: 99.999% (five nines) for multi-region instances
  - Achieved via Paxos quorums and TrueTime synchronization
- Most SaaS products: 99.9% on standard tier, 99.95-99.99% on enterprise tier
  - Enterprise tiers cost significantly more, often 3-5x
- Banking core systems: target 99.999% but rarely advertise SLAs to end users
  - Maintenance windows are scheduled during off-hours to preserve apparent uptime
[Visual suggestion: bar chart of common services and their SLA percentages, with downtime budget labeled in minutes/year]

---

### Slide 31: Availability — Trade-offs Slide
- Higher availability = exponentially higher cost
  - Each additional nine roughly 10x in infra, ops, and engineering time
- Active-passive: cheaper, simpler, slower failover, lower availability ceiling
  - Good fit for ~99.9% targets
- Active-active: expensive, complex, fast failover, higher availability ceiling
  - Required for ~99.99%+ targets
- Multi-region adds latency and consistency complexity
  - You buy availability with consistency or latency budget
- Over-engineering availability is a real risk
  - Five nines is wasted if your dependencies (payment processor, DNS) only offer four
[Visual suggestion: cost vs availability curve — exponential rise; horizontal lines for typical targets at 99%, 99.9%, 99.99%]

---

## Part D: Section Wrap-up

### Slide 32: Section Key Takeaways
- CAP forces a choice between consistency and availability under partition
  - In practice it's CP or AP; CA is single-node only
- Consistency exists on a spectrum: weak, eventual, strong
  - Pick per-data-type; mix within one application
- Availability is achieved via fail-over (active-passive, active-active) and replication (master-slave, master-master)
  - Each has cost, complexity, and recovery-time trade-offs
- Availability composes multiplicatively across dependencies
  - Your system's ceiling is the product of every component's nines
- Every guarantee costs latency, money, or developer effort
  - The skill is matching the guarantee level to the actual business need
[Visual suggestion: a one-page recap diagram with CAP triangle, consistency spectrum, and availability ladder side by side]

---

### Slide 33: Interview Tips
- Lead with "it depends" and ask about the workload before picking CP vs AP
  - Interviewers want to see you reason about trade-offs, not memorize answers
- Mention real systems (Cassandra, DynamoDB, Spanner, ZooKeeper) and explain why they chose their model
  - Concrete examples beat abstract claims
- Always discuss replication topology and failover behavior together
  - They are two halves of the same availability story
- Ask about target availability (SLA) early in the interview
  - Drives architectural choices: single-region vs multi-region, sync vs async replication
- Use the "during a partition, what do we do?" framing to expose CAP trade-offs
  - Shows you understand CAP is about partition behavior, not steady state
[Visual suggestion: a bulleted interview cheat-sheet card with these phrases highlighted]

---

### Slide 34: Common Pitfalls
- Claiming a system is "CA" — almost always wrong, exposes you as inexperienced
  - Distributed = must tolerate partitions = CP or AP
- Defaulting to strong consistency everywhere
  - Costs latency and availability you didn't need to spend
- Forgetting replication lag breaks read-your-writes assumptions
  - Users complain "I posted a comment but I can't see it" — classic stale-replica bug
- Ignoring the cost of an extra "nine"
  - Promising 99.99% when your DNS only offers 99.9% is mathematically impossible
- Treating CAP as static — it's per-operation, not per-system
  - Modern systems (DynamoDB, Cassandra) tune consistency per request
- Using master-master without a conflict resolution strategy
  - Silent data loss when both sides write the same key
- Overlooking detection time in failover RTO calculations
  - Health-check interval + promotion time + DNS TTL = real recovery time
[Visual suggestion: a "pitfall map" with red flags marked at each common mistake, like a minefield illustration]
