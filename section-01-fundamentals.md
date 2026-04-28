# System Design PowerPoint Slides
## Section 1: Fundamentals

---

## Topic 1: What is System Design?

### Slide 1: What is System Design? (Concept Introduction)
- The discipline of defining components, interfaces, and data flow for a system
  - It is the bridge between abstract requirements and concrete code that must run reliably at scale.
- A decision-making process under constraints (cost, latency, traffic, team)
  - Every choice trades one property for another; design is choosing which trade-offs to accept consciously.
- Operates at the "macro" level above class/function design
  - It answers questions like "how do services talk?" rather than "how do I sort this list?"
- Output is typically a blueprint: diagrams, contracts, capacity plans
  - Engineers then implement that blueprint; without it, teams build incompatible pieces.
[Visual suggestion: Pyramid with three layers - bottom "Code (functions/classes)", middle "Architecture (services/modules)", top "System Design (cross-service contracts, data flow, deployment)"]

---

### Slide 2: Why System Design Matters (Deep Explanation)
- Mistakes at the design layer are the most expensive to fix
  - A wrong database choice may require months of dual-writes and migrations; a wrong function is a 10-line patch.
- Non-functional requirements (NFRs) usually decide success, not features
  - Users abandon a correct app that takes 8 seconds to load; latency, availability, and cost are first-class citizens.
- It forces explicit reasoning about failure
  - In a single process, failure means a crash; in a distributed system, failure means partial, partial, partial - and design must say what each partial means.
- It aligns the team on shared mental models
  - Without a design doc, two engineers will independently invent two incompatible queue contracts and discover the conflict in production.
[Visual suggestion: Cost-of-change curve - x-axis "Time (Idea -> Design -> Build -> Deploy -> Production)", y-axis "Cost to fix" rising exponentially]

---

### Slide 3: Scope of System Design (Deep Explanation)
- Functional scope: what the system does (APIs, workflows, features)
  - Defines the contract with users; e.g., "upload a video, get a transcoded URL within 60 seconds."
- Non-functional scope: how well it does it (latency, availability, durability, cost, security)
  - These are measurable targets like "p99 < 200 ms" or "99.95% monthly uptime."
- Operational scope: how it is run (deployment, observability, on-call, capacity)
  - A design that cannot be debugged at 3 AM is not a finished design.
- Evolution scope: how it changes (versioning, migrations, deprecations)
  - Real systems live for years; design must allow swapping a database without a rewrite.
[Visual suggestion: 4-quadrant diagram labeled Functional / Non-Functional / Operational / Evolution, each with example bullet points]

---

### Slide 4: System Design as a Restaurant (Analogy)
- The menu is the API contract
  - It tells customers what they can order and what they will receive; you cannot change it on a whim mid-service.
- The kitchen layout is the service topology
  - Where the prep station, grill, and pass are placed determines throughput; a bad layout creates bottlenecks no recipe can fix.
- Reservations and waitlists are rate limiting and queueing
  - Without them, a popular Saturday night collapses the entire restaurant; with them, the experience degrades gracefully.
- Health inspectors are observability and SLOs
  - You cannot only check the kitchen when the customers complain; you instrument continuously so you catch issues before they reach the diner.
[Visual suggestion: Restaurant floor plan with labels mapping kitchen-to-services, host-to-load-balancer, menu-to-API]

---

## Topic 2: Performance vs Scalability

### Slide 5: Performance vs Scalability (Concept Introduction)
- Performance: how fast the system responds for a single unit of work
  - Measured per request - latency, response time, time-to-first-byte for one user.
- Scalability: how the system behaves as load grows
  - Measured by how performance and cost change as users, data, or traffic multiply.
- They are related but independent properties
  - A system can be fast for one user yet collapse at 1,000 users; another can be slow per request but handle a million in parallel.
- Optimizing one does not automatically improve the other
  - Caching can boost performance without helping scalability; sharding scales but may worsen single-request latency.
[Visual suggestion: Two side-by-side gauges: "Performance = speed of one car" vs "Scalability = how the highway handles 100,000 cars"]

---

### Slide 6: Defining Performance Precisely (Deep Explanation)
- Performance is a distribution, not a number
  - "Average latency 100 ms" hides that 1% of users wait 10 seconds; always think p50, p95, p99, p999.
- Response time = service time + waiting time
  - Even a 5 ms operation feels slow if it queues 200 ms behind other work; queueing is often the real culprit.
- Tail latency dominates user experience in distributed calls
  - If one request fans out to 100 services, the slowest one defines the user-perceived latency.
- Performance is bounded by the critical path
  - Optimizing code that is not on the critical path adds complexity without speeding anything up.
[Visual suggestion: Latency histogram with marked p50, p95, p99 lines and a long tail to the right]

---

### Slide 7: Defining Scalability Precisely (Deep Explanation)
- Vertical scaling: bigger machine (more CPU, RAM, disk)
  - Simple but bounded by hardware limits and a single point of failure; doubling cost rarely doubles capacity past a point.
- Horizontal scaling: more machines working together
  - Effectively unbounded but introduces coordination, partitioning, and network failure as new problems.
- Linear scalability: 2x resources -> 2x throughput (the gold standard)
  - Most real systems achieve sub-linear scaling because of contention, coordination, and shared state.
- Scalability is about the slope, not the intercept
  - A system starting at 100 RPS that grows to 1M RPS scales well; one at 10K RPS that caps at 12K does not.
[Visual suggestion: Two graphs: vertical scaling curve plateauing, horizontal scaling line continuing upward; x-axis "load", y-axis "throughput"]

---

### Slide 8: Highway Analogy for Performance vs Scalability
- Performance is the speed limit on the road
  - A faster sports car (better algorithm) lets one driver get there quicker - that is single-request performance.
- Scalability is the number of lanes
  - Adding lanes lets more cars travel simultaneously without slowing each other down - that is horizontal scaling.
- A 10-lane highway with a 30 mph limit moves more total people than a 1-lane road at 200 mph
  - High throughput does not require low latency; mass transit beats sports cars for moving cities.
- Bottlenecks (toll booth, on-ramp) ruin both
  - One unscaled component caps the whole system; the slowest stage defines real-world performance.
[Visual suggestion: Top-down highway diagram showing 1 lane vs 10 lanes, with a toll booth bottleneck collapsing both]

---

### Slide 9: Performance vs Scalability Trade-offs
- Caching boosts performance but can mask scaling problems
  - A hot cache hides that the underlying database cannot handle the real workload when the cache is cold.
- Sharding improves scalability but adds cross-shard latency
  - Single-key reads stay fast; queries that span shards now require fan-out and merging - slower per query.
- Replication improves read scalability and availability but hurts write performance
  - Each write must propagate; stronger consistency means more coordination and higher write latency.
- Asynchronous processing trades per-request latency for system throughput
  - The user sees an instant "queued" response, but the actual work happens later - good for throughput, bad for synchronous needs.
[Visual suggestion: 2x2 matrix - axes "Per-Request Latency" and "Total Throughput" - placing caching, sharding, replication, async in their respective quadrants]

---

## Topic 3: Latency vs Throughput

### Slide 10: Latency vs Throughput (Concept Introduction)
- Latency: the time a single operation takes from start to finish
  - Measured in time units (ms, s); answers "how long do I wait?"
- Throughput: the number of operations completed per unit time
  - Measured in rate units (req/s, MB/s); answers "how much can the system do per second?"
- They are not opposites - they are orthogonal axes
  - You can have low latency and low throughput (slow single user), or high latency and high throughput (batch pipelines).
- Both are needed; the right balance depends on the workload
  - A trading system prioritizes latency; a backup system prioritizes throughput.
[Visual suggestion: 2D plot - x-axis "Latency (lower is better)", y-axis "Throughput (higher is better)" - with examples plotted: HFT (low lat, low tput), CDN (low lat, high tput), Hadoop (high lat, high tput)]

---

### Slide 11: Why Latency and Throughput Diverge (Deep Explanation)
- Throughput = concurrency / latency (Little's Law)
  - If each request takes 100 ms and you run 50 in parallel, throughput is 500 req/s; you can grow throughput by lowering latency or adding concurrency.
- Batching increases throughput at the cost of latency
  - Grouping 100 small writes into one large write amortizes overhead per item but makes the first item wait for the last.
- Pipelining hides latency without reducing it
  - While one stage waits, another processes; total wall time per request is unchanged but units-per-second goes up.
- Network and disk have very different latency/throughput profiles
  - SSDs: 100 microsecond latency, GB/s throughput; spinning disk: 10 ms latency, 100 MB/s throughput - design must respect both numbers.
[Visual suggestion: Pipeline diagram showing 4 stages processing different requests simultaneously, with a single request's latency highlighted as horizontal length]

---

### Slide 12: Latency Sources You Must Know (Deep Explanation)
- Speed of light is non-negotiable
  - Light needs about 5 ms to cross the US one way; no software optimization beats geography for cross-continent calls.
- Network round trips are the usual culprit
  - Each TCP handshake and TLS negotiation adds RTTs; reducing chattiness often beats optimizing CPU.
- Disk I/O is orders of magnitude slower than memory
  - Memory access is nanoseconds; SSD is microseconds; spinning disk is milliseconds; design data placement accordingly.
- Garbage collection, context switches, and locks add jitter
  - These are why p99 is so much worse than p50; fixing the median rarely fixes the tail.
[Visual suggestion: "Latency numbers every engineer should know" log-scale chart - L1 cache 1ns, RAM 100ns, SSD 100us, network 1ms, cross-continent 100ms]

---

### Slide 13: Coffee Shop Analogy for Latency vs Throughput
- Latency is how long one customer waits for their coffee
  - A pour-over latte takes 4 minutes regardless of how many baristas you hire for one customer.
- Throughput is how many coffees the shop serves per hour
  - Adding baristas, espresso machines, and a second register grows throughput without changing one customer's wait.
- Drive-through windows trade latency for throughput
  - Pre-batching milk, simplifying the menu, and parallel windows raise cups-per-hour but add steps that could be slower per cup.
- A queue forming is a sign throughput is below arrival rate
  - When customers arrive faster than the shop serves them, latency grows unboundedly even though the baristas are at full speed.
[Visual suggestion: Coffee shop diagram with one register (low throughput), three registers (high throughput), and a growing queue when arrival rate exceeds service rate]

---

### Slide 14: Latency vs Throughput Trade-offs
- Optimizing for low latency often caps throughput
  - Dedicating resources to fast single-request paths (no batching, low queue depth) leaves capacity unused under load.
- Optimizing for high throughput often raises latency
  - Batching, buffering, and queueing increase efficiency but make any single request wait longer.
- Synchronous APIs prioritize latency; asynchronous pipelines prioritize throughput
  - REST/RPC give immediate answers; Kafka/SQS process backlogs but the producer does not see the result.
- Workload matters: real-time vs analytics have opposite design pressures
  - A search box must answer in 50 ms per query; a nightly ETL must finish 1 TB by morning - same data, different systems.
[Visual suggestion: Two side-by-side architectures: "Low Latency Path" (sync, in-memory, no batch) vs "High Throughput Path" (async, batch, queue)]

---

## Topic 4: Availability vs Consistency Trade-off (CAP)

### Slide 15: Availability vs Consistency (Concept Introduction)
- Consistency (C in CAP): every read sees the most recent write
  - All nodes agree on the same value at the same time, as if there were a single copy.
- Availability (A in CAP): every request gets a non-error response
  - The system stays responsive even if some replicas are unreachable, even if data is stale.
- Partition tolerance (P): system continues despite network failures between nodes
  - In any real distributed system, partitions will happen, so P is not optional - it is reality.
- CAP theorem: during a partition, you must choose C or A - you cannot have both
  - This is the core trade-off; understanding it shapes every distributed data decision.
[Visual suggestion: Classic CAP triangle with C, A, P at corners; arrow showing "you pick 2 sides during a partition"]

---

### Slide 16: What Consistency Really Means (Deep Explanation)
- Strong consistency: a read after a write always returns the new value
  - Implemented via consensus (Raft, Paxos) or single-leader writes; expensive because nodes must agree before returning.
- Eventual consistency: replicas converge given no new writes
  - Reads may return stale data temporarily; cheap and highly available, but applications must tolerate disagreement.
- Causal consistency: operations that are causally related are seen in order
  - "Reply" must appear after "comment"; unrelated operations can be observed in any order.
- Consistency is not a binary - it is a spectrum
  - Read-your-writes, monotonic reads, and bounded staleness are middle-ground guarantees with real production value.
[Visual suggestion: Spectrum from "Strong Consistency" (linearizable) on the left to "Eventual" on the right, with milestones - Sequential, Causal, Read-Your-Writes - placed between]

---

### Slide 17: What Availability Really Means (Deep Explanation)
- Availability is measured in 9s of uptime
  - 99.9% = ~8.7 hours downtime/year; 99.99% = 52 minutes; 99.999% = 5 minutes - each "9" costs roughly 10x more.
- Availability includes "responds with a useful answer," not just "responds"
  - A 500 error is technically a response but counts as unavailable; SLOs measure successful responses.
- Highly available systems must tolerate partial failure gracefully
  - When a replica is down, the system serves from another; when a region is down, traffic shifts to another region.
- Availability is harder than it looks because of dependency chains
  - A service with 99.9% uptime that depends on three other 99.9% services has at best 99.7% effective availability.
[Visual suggestion: Stacked bar showing how dependencies multiply downtime; table of "9s" mapped to allowed downtime per year]

---

### Slide 18: Bank vs Social Feed Analogy
- A bank chooses consistency over availability
  - If the network partitions, an ATM should refuse the withdrawal rather than risk double-spending; "service unavailable" beats incorrect balance.
- A social feed chooses availability over consistency
  - Users seeing slightly stale likes is fine; a blank feed is unacceptable, so each region serves its local replica.
- A shopping cart blends both at different layers
  - Adding to cart is AP (it just works); checkout is CP (must agree on inventory and price exactly).
- The right choice depends on the cost of being wrong
  - Wrong money is a lawsuit; wrong like count is a shrug; design the trade-off per feature, not per system.
[Visual suggestion: Two columns - "Bank (CP): refuse if uncertain" vs "Social Feed (AP): always show something" - with example error and stale-data screens]

---

### Slide 19: PACELC - Beyond CAP (Deep Explanation)
- CAP only describes behavior during a partition
  - But partitions are rare; most of the time the network is fine, and CAP says nothing about that case.
- PACELC: if Partition then A vs C, Else (normal operation) Latency vs Consistency
  - It captures that even without partitions, stronger consistency costs more latency due to coordination.
- Example: Dynamo-style stores are PA/EL (available during partition, low latency normally)
  - They sacrifice consistency in both regimes for speed and uptime.
- Example: Spanner-style stores are PC/EC (consistent during partition, consistent normally)
  - They accept higher latency from cross-region consensus to keep correctness everywhere.
[Visual suggestion: PACELC matrix - rows "Partition / No Partition", columns "Consistency vs Availability/Latency" - with real systems mapped]

---

### Slide 20: Availability vs Consistency Trade-offs in Practice
- Strong consistency requires coordination, which limits scale and uptime
  - Quorum reads/writes and consensus protocols add latency and create unavailability when too many nodes are down.
- Eventual consistency enables scale and uptime but pushes complexity to the application
  - The app must handle conflicts (last-write-wins, CRDTs, user merge), which is real engineering work.
- The choice is feature-by-feature, not system-wide
  - The same product may store user profiles eventually but billing strongly; design each data flow on its own merits.
- Read your SLA, not the marketing
  - "Highly available" and "consistent" are vague; quantify required uptime, max staleness, and conflict resolution explicitly.
[Visual suggestion: Decision tree - "Is incorrect data acceptable for this feature?" -> Yes (AP) / No (CP) - with example features at each leaf]

---

## Section Wrap-Up

### Slide 21: Key Takeaways
- System design is about trade-offs under constraints, not about finding the "best" answer
  - Every choice gives up something; the goal is to give up the right thing for your context.
- Performance and scalability are independent - measure and optimize them separately
  - Fast for one user does not imply fast for a million; design for the actual workload, not the demo.
- Latency and throughput are orthogonal - know which one your workload demands
  - Real-time systems chase latency; batch systems chase throughput; mixing the two confuses design.
- CAP/PACELC force explicit decisions about consistency, availability, and latency
  - Distributed systems will partition; deciding in advance how the system behaves is the core of system design.
- All four concepts compose - real systems navigate every trade-off simultaneously
  - A single feature may demand low latency, high throughput, strong consistency, and high availability - acknowledge what gives.
[Visual suggestion: Mind map with "System Design" center node, branches to Performance/Scalability/Latency/Throughput/Consistency/Availability, each with key trade-off labels]

---

### Slide 22: Interview Tips
- Always clarify functional and non-functional requirements before designing
  - Asking "what is the read:write ratio?" or "what latency is acceptable?" signals senior thinking and prevents wasted whiteboard work.
- State assumptions out loud and write them down
  - Interviewers grade reasoning, not memorized answers; explicit assumptions show you understand the trade-off space.
- Use back-of-envelope numbers to justify choices
  - "10M DAU * 100 events = 1B events/day = 12K events/sec" turns vague design into a concrete capacity argument.
- Name the trade-off you are choosing and why
  - Saying "I am picking AP here because stale reads are acceptable for this feed" is stronger than "I'll use Cassandra."
- Start simple, then scale - do not over-engineer round one
  - A monolith that works beats a microservice diagram that does not; show you can evolve a design instead of premature complexity.
[Visual suggestion: Whiteboard checklist: Clarify -> Estimate -> Sketch high-level -> Identify bottlenecks -> Apply trade-offs -> Discuss evolution]

---

### Slide 23: Common Pitfalls
- Confusing performance with scalability
  - Adding a faster CPU does not help when the database is the bottleneck; profile first, optimize the right axis.
- Optimizing average latency while ignoring tail latency
  - Users feel p99, not p50; a "fast" service with bad p99 fans out into terrible end-to-end experiences.
- Treating CAP as a one-time choice for the whole system
  - It is per data flow and per failure mode; saying "we are AP" hides where you actually need C.
- Using "highly available" or "scalable" without numbers
  - These are aspirations, not requirements; without SLOs, you cannot tell if the design meets the need.
- Adding caches/queues/microservices before the simple version is exhausted
  - Each adds operational burden, failure modes, and consistency complications; only introduce them when the simpler design provably fails.
- Forgetting the cost dimension
  - A design that meets all NFRs at 100x the budget is wrong; design includes "is this cost-effective at our scale?"
[Visual suggestion: List of red-flag phrases ("we'll just cache it", "Mongo is web scale", "we need microservices") with the underlying mistake annotated next to each]
