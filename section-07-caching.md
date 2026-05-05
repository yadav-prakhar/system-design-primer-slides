## Section 7: Caching

---

### Slide 1: Section Overview — Caching
- Caching is the single highest-leverage performance technique in system design
  - One well-placed cache can reduce latency by 10–100x and database load by 90%+
- We will cover what caching is, where to put caches, read/write strategies, invalidation, eviction, and distributed caching
  - Each topic includes intuition, real-world examples, diagrams, and trade-offs
- Caching is everywhere: CPU registers, browsers, CDNs, app servers, databases, distributed systems
  - Almost every "fast" system you use is fast because of layered caches
- Master caching and you master ~40% of system design interview problems
  - Twitter timelines, YouTube videos, Amazon product pages, Facebook feeds — all cache-driven
- Core lesson: caching trades freshness for speed; the art is choosing the right trade-off
  - Strong consistency + cache = hard problem; eventual consistency + cache = standard pattern
[Visual suggestion: Pyramid diagram showing latency hierarchy — CPU register (1ns) → L1 (1ns) → L2 (4ns) → RAM (100ns) → SSD (100µs) → Network (1ms) → Disk (10ms), with cache layers labeled at each tier]

---

### Slide 2: What is Caching?
- A cache is temporary, fast storage that holds the results of expensive computations or fetches
  - "Expensive" can mean slow database query, network round-trip, CPU computation, or disk I/O
- Goal: serve future requests for the same data without redoing the work
  - First request pays full cost; subsequent requests pay near-zero cost
- Caches exploit two fundamental properties of real workloads
  - Temporal locality (recently used data is likely used again soon)
  - Spatial locality (data near recently used data is likely used soon)
- The core trade-off: speed vs. freshness vs. memory cost
  - Faster reads, but data may be stale; uses RAM (expensive) instead of disk (cheap)
- Caching is NOT a database — it is a derived, disposable view of authoritative data
  - The source of truth always lives elsewhere; cache can be wiped without data loss
[Visual suggestion: Two-panel comparison: Left panel "Without Cache" — User → App → Database (slow, 50ms); Right panel "With Cache" — User → App → Cache (fast, 1ms), with database shown in background as fallback]

---

### Slide 3: Why Caching? — The Business Case
- Reduces latency: serving from RAM is ~100x faster than disk and ~1000x faster than network
  - Page load drops from 500ms to 5ms — measurably better user experience
- Reduces backend load: a 90% cache hit ratio means your database handles only 10% of traffic
  - Lets you scale to 10x users on the same database hardware
- Reduces cost: cache hits are cheaper than database queries, API calls, or recomputation
  - Cache a $0.01 LLM call once; serve 1M users from cache for the same penny
- Improves availability: cached data can serve users even when the origin is down
  - Stale-while-revalidate keeps the site up during database outages
- Smooths traffic spikes: cache absorbs flash crowds before they hit the origin
  - Black Friday, viral tweets, breaking news — cache is your shock absorber
[Visual suggestion: Bar chart comparing latencies on log scale — L1 cache (1ns), Memory (100ns), SSD (100µs), Network (1ms), Database query (10–100ms), Cross-region call (100ms)]

---

### Slide 4: Cache Hierarchy — From CPU to Network
- Modern computing is a stack of caches, each larger but slower than the one above
  - Optimizing the hot path means keeping data as high in the hierarchy as possible
- CPU caches: L1 (~32KB, 1ns), L2 (~256KB, 4ns), L3 (~8MB, 12ns)
  - Hardware-managed; invisible to your application but matters for performance-critical code
- Main memory (RAM): ~16–256GB, ~100ns access — where most application caches live
  - Redis, Memcached, in-process LRU caches, JVM heap all live here
- Local disk / SSD: ~1TB, ~100µs — used for browser cache, OS page cache, large object cache
  - CDN edge nodes use SSD-backed caches for warm assets
- Network and remote storage: ~1ms+ — origin servers, S3, primary databases
  - This is what we are trying to avoid hitting on the hot path
[Visual suggestion: Inverted pyramid showing hierarchy with size growing downward and speed shrinking — CPU registers at top (bytes, picoseconds) to global storage at bottom (petabytes, hundreds of ms)]

---

### Slide 5: Intuition — Cache as a Workshop Bench
- Imagine a carpenter with a workshop full of tools stored in a basement
  - Walking to the basement for every tool would make any job impossibly slow
- The carpenter keeps frequently used tools (hammer, tape measure, pencil) on the workbench
  - The workbench is small but right next to the work — instant access
- Less-used tools (specialty saws) sit on a nearby shelf — quick to grab but a step away
  - Rarely used tools (annual jigs) stay in the basement
- Cache hierarchy works exactly the same way
  - L1 = pocket, L2 = workbench, L3 = shelf, RAM = closet, disk = basement, network = warehouse across town
- The skill is predicting which tools you'll need next and pre-staging them
  - This is exactly what cache eviction policies and prefetching algorithms do
[Visual suggestion: Cartoon of a carpenter at a workbench with tools labeled by access frequency, basement stairs leading down to "cold storage" labeled with database/network icons]

---

### Slide 6: Cache Hit vs. Cache Miss
- Cache hit: requested data is found in the cache — return immediately
  - Cost = cache access time (~1ms for Redis, ~1ns for L1)
- Cache miss: requested data is not in the cache — must fetch from origin
  - Cost = cache access + origin access + (usually) write-back to cache
- Three flavors of miss matter in practice
  - Compulsory miss: first time data is requested (unavoidable cold start)
  - Capacity miss: cache too small to hold working set (evicted before reuse)
  - Conflict miss: hashing collisions in set-associative caches (rare in software caches)
- Miss penalty is the dominant performance variable in any cached system
  - A 50ms miss vs 1ms hit means even small miss-rate changes drastically shift average latency
- Average latency formula: AvgLatency = HitRate × HitLatency + MissRate × MissLatency
  - At 95% hit rate with 1ms hit / 50ms miss → avg = 3.45ms; at 80% → avg = 10.8ms (3x worse)
[Visual suggestion: Flowchart — Request arrives → Check cache → "Hit?" diamond → Yes (green path, return cached value) / No (red path, fetch from DB, store in cache, return). Latency labels on each path.]

---

### Slide 7: Cache Hit Ratio — The Most Important Metric
- Hit ratio = cache hits / total requests — measures how effective your cache is
  - 90% means 9 out of 10 requests skip the database; 50% means cache is barely helping
- Why it matters more than raw cache size
  - A 100GB cache with 30% hit rate is worse than a 10GB cache with 95% hit rate
- Target hit ratios depend on workload
  - Web page caches: 95–99% (Cloudflare reports ~95% globally)
  - Database query caches: 80–95% typical
  - User session caches: ~99%
- Below 80% hit ratio, ask yourself
  - Is the cache too small? Is TTL too short? Is the access pattern truly random?
- Hot keys often dominate the hit ratio (Pareto / Zipf distribution)
  - Top 20% of keys often serve 80% of traffic — caching them gets you most of the win
[Visual suggestion: Line graph showing average latency on Y-axis vs. hit ratio on X-axis — exponential drop in latency as hit ratio crosses 90%, 95%, 99% thresholds]

---

### Slide 8: When Caching Helps — and When It Hurts
- Caching helps when read traffic dominates write traffic
  - Read-heavy workloads (1000:1 reads:writes) get massive benefit from caching
- Caching helps when the same data is requested repeatedly (high reuse)
  - Trending tweets, popular product pages, common search results
- Caching helps when origin computation is expensive relative to cache lookup
  - Complex SQL joins, ML inference, third-party API calls
- Caching HURTS when data changes faster than it is read
  - Real-time stock prices, live game state — cache is stale before it is reused
- Caching HURTS when working set is larger than cache (low locality)
  - Random scans over a 1TB table with 10GB cache → ~1% hit rate, just adds overhead
- Caching adds complexity: invalidation bugs, stale data, consistency edge cases
  - Don't add a cache "just because" — measure first, cache the actual hot path
[Visual suggestion: Two columns — "Cache YES" with examples (user profiles, product catalog, news articles, autocomplete) vs "Cache NO" (real-time bidding, audit logs, one-time tokens, write-heavy tables)]

---

### Slide 9: Caching Layers — The Big Picture
- A modern web request passes through 5–7 cache layers before hitting the origin
  - Each layer captures a slice of traffic and forwards only the misses downstream
- Browser cache → CDN edge → reverse proxy → app cache → distributed cache → DB cache → disk
  - Goal: maximize hits at the highest, cheapest layer
- Multi-layer caching is multiplicative — 50% hit at each of 4 layers = 6.25% reaches origin
  - This is why CDN + Redis + DB query cache together can absorb millions of QPS
- Each layer has different TTLs, sizes, eviction policies, and invalidation semantics
  - Static assets cached for a year at the edge; user data cached for seconds in app
- Design rule: cache as close to the user as possible, but as far back as correctness requires
  - Personalized data → app/distributed cache; public assets → CDN; computed views → DB cache
[Visual suggestion: Horizontal layered diagram: Browser → CDN → Reverse Proxy → App Server (in-process cache) → Redis → Database (query cache + buffer pool) → Disk; with traffic-funnel showing requests filtering at each layer]

---

### Slide 10: Layer 1 — Client-Side Caching
- Browser HTTP cache stores responses based on Cache-Control, ETag, Last-Modified headers
  - Cache-Control: max-age=31536000, immutable → cache for a year, never revalidate
- Service workers enable programmatic offline caches (PWAs)
  - Gmail, Google Docs, Twitter use service workers for offline-first behavior
- localStorage / sessionStorage / IndexedDB store structured data locally
  - User preferences, draft messages, recently viewed items — survive page refresh
- Pros: zero network cost, offline support, instant load on repeat visits
  - 304 Not Modified responses save bandwidth even when revalidating
- Cons: no central control once cached — bad deploys can persist for hours/days
  - Must use cache-busting URLs (style.abc123.css) for safe updates
[Visual suggestion: Browser window diagram showing layers — HTTP cache → Service Worker → IndexedDB → localStorage, with arrows showing fallback order]

---

### Slide 11: Layer 2 — CDN Caching
- CDN = Content Delivery Network: geographically distributed edge servers caching origin content
  - Cloudflare, Akamai, Fastly, AWS CloudFront, Google Cloud CDN
- Caches static assets (images, CSS, JS, video segments) at edge nodes near users
  - Tokyo user fetches asset from Tokyo POP, not Virginia origin — 200ms → 5ms
- Modern CDNs cache dynamic content via edge functions and smart cache keys
  - Cloudflare Workers, Fastly Compute@Edge let you cache personalized HTML
- Cache invalidation via purge APIs, surrogate keys (Fastly), or versioned URLs
  - Netflix versions every asset; never invalidate, just deploy new URLs
- Real example: YouTube video streaming
  - Hot videos cached at thousands of edge POPs; long-tail fetched from regional caches
- Pros: massive scale (Tbps of bandwidth), DDoS absorption, global low latency
  - Cons: cost, cache key complexity for dynamic content, debugging hit/miss across POPs
[Visual suggestion: World map showing user requests routed to nearest CDN edge (colored dots on each continent) with origin server in one location; arrows showing cache hits vs misses going to origin]

---

### Slide 12: Layer 3 — Reverse Proxy / Web Server Cache
- A reverse proxy sits between clients and app servers, caching HTTP responses
  - Nginx, Varnish, HAProxy, Apache Traffic Server, Envoy
- Caches full HTML pages, API responses, even fragments (Edge Side Includes)
  - One cached response can serve millions of identical requests
- Varnish is the gold standard for HTTP caching
  - VCL (Varnish Configuration Language) lets you express complex cache rules
  - Used by Wikipedia, NYT, Reddit to absorb traffic spikes
- Sits in your data center — different role than CDN (which sits globally)
  - CDN handles geographic distribution; reverse proxy handles per-DC absorption
- Real example: Wikipedia serves ~20 billion pageviews/month with Varnish doing most of the work
  - Database is rarely touched for anonymous reads of popular articles
[Visual suggestion: Diagram: Internet → Load Balancer → Varnish/Nginx (cache) → App Server cluster → Database; with cache hit returning at proxy level, miss going through to app]

---

### Slide 13: Layer 4 — Application-Level (In-Memory) Caching
- Cache lives inside the application process — fastest possible access, no network hop
  - Java: Caffeine, Guava Cache, Ehcache; Python: functools.lru_cache, cachetools; Go: bigcache, ristretto
- Sub-microsecond access (it's just a HashMap with eviction)
  - Perfect for hot config, feature flags, computed lookup tables
- Limitation: each app instance has its own copy — N caches for N servers
  - Memory waste, inconsistent values across instances, cold cache on every deploy
- Use when: data is small, mostly static, or per-instance state is acceptable
  - Bad fit for user sessions (sticky sessions become required), good fit for currency conversion tables
- Real example: Caffeine in Twitter, Guava in many Google services
  - Often used as L1 in front of Redis (L2) — local cache catches hot keys, distributed cache catches the rest
[Visual suggestion: Three app server boxes each with embedded "in-process cache" rectangle; arrows showing each independently caching, no synchronization between them]

---

### Slide 14: Layer 5 — Database Caching
- Databases have multiple internal caches you should understand
  - Buffer pool / page cache: hot disk pages kept in RAM (Postgres shared_buffers, MySQL InnoDB buffer pool)
- Query result cache: caches result sets of identical queries
  - MySQL's old query cache was deprecated due to mutex contention; modern systems use external caches
- Materialized views: pre-computed query results stored on disk, refreshed periodically
  - Postgres MATERIALIZED VIEW; great for expensive aggregations (daily revenue, dashboards)
- Prepared statement cache: parsed/planned queries reused for performance
  - Saves 1–10ms per query in OLTP workloads
- OS page cache sits below the database, caching disk blocks transparently
  - Linux uses all free RAM for page cache; "free memory" is a meaningless metric
[Visual suggestion: Database internals diagram showing query → query cache → query planner → buffer pool → OS page cache → disk, with each layer labeled with hit/miss probability]

---

### Slide 15: Layer 6 — Distributed Caching
- Shared cache cluster accessible from all app servers — single source of cached truth
  - Redis, Memcached, Hazelcast, Aerospike
- Solves the problem of inconsistent per-instance caches in app-level caching
  - All servers see the same value; invalidation is centralized
- Adds a network hop (~0.5–1ms) but enables horizontal scaling
  - Cache cluster scales independently of app servers
- Survives app server restarts — data persists in the cache layer
  - Cold-start problem moves from "every deploy" to "rare cache failure"
- Real examples
  - Twitter: Redis stores timelines, Memcached for objects (~100s of TB across thousands of nodes)
  - Facebook: Memcached at planetary scale, originally invented McDipper, then TAO
[Visual suggestion: N app servers all connecting to a 3-node Redis cluster in the middle; database behind it as origin; arrows showing all reads hit Redis first]

---

### Slide 16: Caching Layers — Trade-offs Summary
- Browser cache: free, fastest for user, but uncontrollable once deployed
  - Trade-off: speed vs. ability to push updates
- CDN: massive scale and global, but costs money and complicates dynamic content
  - Trade-off: edge speed vs. invalidation complexity
- Reverse proxy: high throughput, full HTML caching, but per-DC only
  - Trade-off: simplicity vs. geographic reach
- App-level cache: nanosecond access, but per-instance and inconsistent
  - Trade-off: speed vs. consistency
- Distributed cache: shared and consistent, but adds network hop and operational burden
  - Trade-off: consistency vs. latency and ops cost
- Database cache: closest to truth, but limited size and contention prone
  - Trade-off: freshness vs. throughput
[Visual suggestion: Comparison matrix table — rows: Browser, CDN, Proxy, App, Distributed, DB; columns: Latency, Scale, Consistency, Ops cost, Use case]

---

### Slide 17: Caching Strategies — Read Patterns Overview
- Caching strategy = the protocol for how reads and writes interact with cache and origin
  - Different strategies optimize for different consistency/latency/complexity trade-offs
- Five canonical strategies you must know cold for interviews
  - Cache-aside, Read-through, Write-through, Write-behind, Refresh-ahead
- Two axes to think about
  - Read path: who fills the cache (application vs cache itself)
  - Write path: what gets updated and in what order (cache, DB, both, async)
- No strategy is universally best — each has a sweet spot
  - Cache-aside is the default; others solve specific problems
- We'll cover each with mechanics, pros/cons, and a real-world example
  - Memorize the diagrams, not just the names
[Visual suggestion: 2x2 grid — axes "Read" (lazy/eager) and "Write" (sync/async) — with each strategy placed in its quadrant]

---

### Slide 18: Strategy 1 — Cache-Aside (Lazy Loading)
- Application is responsible for both cache and DB; cache does not know about DB
  - Read flow: check cache → on miss, query DB → write result to cache → return
- Most popular pattern; default choice for Redis/Memcached deployments
  - Used by Facebook (Memcached + MySQL), most production stacks
- Pros
  - Only caches what's actually read (no wasted space)
  - Cache failure doesn't break the system (just slower)
  - Easy to add to an existing application
- Cons
  - First request always slow (cache miss penalty)
  - Stale data risk if DB is updated without invalidating cache
  - Two systems to coordinate — bugs in invalidation cause divergence
- Real example: Facebook's Memcached layer in front of MySQL
  - Famous "Scaling Memcache at Facebook" paper — built the canonical cache-aside pattern at scale
[Visual suggestion: Sequence diagram — App → Cache (miss) → DB (read) → App writes back to Cache → returns to user; second request hits cache directly]

---

### Slide 19: Cache-Aside — Pseudocode and Pitfalls
- Standard read implementation (Python-style)
  - `value = cache.get(key); if not value: value = db.get(key); cache.set(key, value, ttl); return value`
- Standard write implementation
  - `db.write(key, value); cache.delete(key)  # next read repopulates`
- Pitfall 1: thundering herd on miss for hot keys
  - 1000 concurrent readers all miss → 1000 DB queries; solved with mutex / single-flight
- Pitfall 2: race condition between read and write
  - Reader sees old DB value, writer updates DB and invalidates cache, reader writes stale value back
  - Solved via versioning, CAS, or "delete-after-write" with delay (Facebook's "leases")
- Pitfall 3: forgetting to invalidate on update → permanent stale cache
  - Always pair every DB write with a cache invalidation in the same code path
- Default TTL is your safety net — even buggy invalidation eventually self-heals
  - Pick TTL based on tolerance for staleness (seconds to hours)
[Visual suggestion: Code snippet on left showing read/write functions; race condition timeline on right showing how stale write can sneak in]

---

### Slide 20: Strategy 2 — Read-Through Cache
- Cache itself knows how to load from the database on miss — application talks only to cache
  - Read flow: app calls cache.get(key) → cache misses → cache calls DB loader → returns to app
- Cache acts as a smart proxy in front of the data store
  - App code is simpler — no explicit DB call in the read path
- Pros
  - Application code is clean — single API (`cache.get`)
  - Cache logic centralized; consistent behavior across services
- Cons
  - Cache must support pluggable loaders (Caffeine, Ehcache, AWS DAX do; raw Redis does not)
  - First request still slow (same cold-start as cache-aside)
  - Tighter coupling between cache and data store
- Real example: AWS DAX in front of DynamoDB; Caffeine's CacheLoader in JVM apps
  - DAX gives DynamoDB sub-millisecond reads with zero application code change
[Visual suggestion: Sequence diagram — App → Cache → (cache internally fetches from DB on miss) → returns to App; cleaner single-arrow path from app's view]

---

### Slide 21: Strategy 3 — Write-Through Cache
- Every write goes to BOTH cache and database synchronously, in the same operation
  - Write flow: app writes → cache writes → DB writes → all complete before ack
- Cache is always consistent with database — no stale data possible
  - Reads can hit cache safely, knowing it matches truth
- Pros
  - Strong consistency between cache and DB
  - No invalidation logic needed — cache always fresh
  - Simple mental model
- Cons
  - Every write pays double latency (cache write + DB write)
  - Caches data even if it's never read again — wasted memory for write-once data
  - Cache failure can fail the write (depending on implementation)
- Real example: DynamoDB DAX in write-through mode, some Hibernate L2 cache configs
  - Best when read-after-write is required and write traffic is moderate
[Visual suggestion: Sequence diagram showing parallel/sequential write to Cache and DB, both acknowledging before app returns success]

---

### Slide 22: Strategy 4 — Write-Behind (Write-Back) Cache
- Write goes to cache immediately; cache asynchronously flushes to DB later
  - Write flow: app writes → cache acks immediately → background worker batches writes to DB
- Optimizes for write-heavy workloads at the cost of durability
  - Multiple writes to the same key can coalesce, reducing DB load drastically
- Pros
  - Very fast writes (cache speed, not DB speed)
  - Batching reduces DB write amplification
  - Smooths write spikes (cache absorbs bursts)
- Cons
  - Risk of data loss if cache crashes before flush
  - Eventual consistency — DB lags cache, complicates DR and analytics
  - Complex failure recovery
- Real example: Linux page cache writing to disk; some metric/analytics pipelines (StatsD-like flushers)
  - Use when losing the last few seconds of writes is acceptable (counters, metrics, view counts)
[Visual suggestion: Sequence diagram — write to cache returns instantly; dashed async arrow from cache to DB labeled "batched flush every N seconds"]

---

### Slide 23: Strategy 5 — Refresh-Ahead Cache
- Proactively refresh cache entries BEFORE they expire, predicting next access
  - On read, if entry is "close to expiring" (e.g., 80% of TTL), trigger async refresh
- Hides cache miss latency for hot data — readers always hit warm cache
  - Particularly effective for predictable, frequently accessed keys
- Pros
  - Eliminates miss penalty for hot keys
  - Smooths out backend load (refreshes spread over time, not bursts at expiry)
- Cons
  - May refresh entries that won't be read again (wasted DB call)
  - Requires good prediction heuristic — naive implementations cause thrashing
  - More complex than TTL-only eviction
- Real example: Caffeine's `refreshAfterWrite`, Guava's `LoadingCache.refresh()`
  - Used heavily in feed/timeline systems where the same keys are read every second
[Visual suggestion: Timeline showing TTL bar — at 80% mark, async refresh fires while reads continue hitting old cached value, then new value seamlessly takes over]

---

### Slide 24: Strategies — Decision Matrix
- Cache-aside: best general-purpose default for read-heavy workloads
  - Use when: reads dominate, app can tolerate some staleness, you control DB writes
- Read-through: cleaner code than cache-aside, requires cache library support
  - Use when: building on Caffeine, DAX, Hazelcast — get the benefit for free
- Write-through: when reads must always see latest write, write volume moderate
  - Use when: user just wrote a comment and refreshes — must see their own write
- Write-behind: write-heavy, durability not critical, want batching
  - Use when: counters, view counts, telemetry, leaderboard increments
- Refresh-ahead: hot keys with predictable access, latency-sensitive reads
  - Use when: dashboards, feeds, autocomplete — same keys hit constantly
[Visual suggestion: Decision tree — "Read-heavy?" → cache-aside / read-through; "Write-heavy?" → write-behind; "Need consistency?" → write-through; "Hot predictable keys?" → refresh-ahead]

---

### Slide 25: Strategies — Real-World Example: Twitter Timeline
- Timeline read uses cache-aside on Redis fronted by per-server Caffeine (L1+L2)
  - User opens Twitter → app checks local cache → Redis → only on miss, recompute timeline
- Timeline write (new tweet) uses fanout-on-write into followers' Redis lists
  - Resembles write-through into denormalized cache structures, not the source DB
- Hot accounts (Obama, Beyoncé) bypass fanout-on-write to avoid hot-key explosion
  - Their tweets are fanned out lazily on read (fanout-on-read) — different strategy for different scale
- Counters (likes, retweets) use write-behind into Redis with periodic DB flush
  - Tolerates losing last few seconds of likes during a Redis failover
- Multiple strategies coexist in one product because workloads differ per feature
  - This is the real lesson: strategy is per-data-type, not per-system
[Visual suggestion: Twitter architecture sketch — User → App → L1 (Caffeine) → L2 (Redis fanout cache) → MySQL/Manhattan; with overlay showing different strategies per data type]

---

### Slide 26: Cache Invalidation — Why It's Hard
- Phil Karlton: "There are only two hard things in computer science: cache invalidation and naming things"
  - Quote is famous because invalidation breaks every "obvious" approach
- The fundamental problem: cache and source-of-truth can diverge silently
  - You don't know your cache is wrong until a user complains
- Sources of invalidation difficulty
  - Distributed writers updating DB without telling cache
  - Race conditions between read-from-DB and write-to-cache
  - Multi-region replication lag
  - Caches at multiple layers all need to be invalidated coherently
- Trade-off triangle: freshness, performance, complexity — pick two
  - Stronger freshness → either slower (synchronous invalidation) or more complex (event-driven)
- Invalidation bugs are the #1 cause of "weird" production issues with caches
  - User updates email → still sees old email → support ticket → days of debugging
[Visual suggestion: Three-circle Venn diagram — "Fresh", "Fast", "Simple" — with caption "you can have any two"]

---

### Slide 27: TTL-Based Expiry
- Every cache entry has a Time-To-Live; cache evicts/expires entries when TTL passes
  - Simplest invalidation strategy: don't invalidate, just let entries die naturally
- Strengths
  - Zero coordination — works without any write-side logic
  - Self-healing — even if invalidation logic is buggy, staleness is bounded
  - Predictable memory bounds
- Weaknesses
  - Stale data window equal to TTL — users see old data for up to TTL seconds
  - All-or-nothing per entry — can't be "kind of expired"
- Choosing a TTL
  - Short TTL (seconds): low staleness, low hit ratio, high DB load
  - Long TTL (hours/days): high hit ratio, high staleness risk
- Real example: DNS uses TTL exclusively (typical 300s for A records)
  - DNS chose simplicity over freshness — propagation takes minutes globally
[Visual suggestion: Timeline showing entry lifecycle — write at t=0 with TTL=60s, reads hit cache, automatic eviction at t=60s, next read causes refresh]

---

### Slide 28: Event-Driven Invalidation
- On every write to source-of-truth, emit an event that invalidates affected cache keys
  - Write to DB → publish "user:42 updated" → all caches receive event and evict user:42
- Implementations
  - Synchronous: app deletes from cache after DB write (cache-aside default)
  - Asynchronous: change-data-capture (Debezium reading MySQL binlog → Kafka → cache invalidator)
- Strengths
  - Near-real-time freshness (milliseconds, not minutes)
  - Targeted — only invalidates what changed, preserves cache for rest
- Weaknesses
  - Coupling between writer and cache invalidator
  - Lost events = permanent stale cache (need TTL as backstop)
  - Hard to invalidate derived/aggregated keys (which list views contain user 42?)
- Real example: LinkedIn's Brooklin, Netflix's ev-cache invalidation via Kafka
  - At scale, CDC pipelines are the standard for event-driven cache invalidation
[Visual suggestion: Diagram — DB write → CDC reader → Kafka topic → multiple cache invalidator workers → Redis cluster keys deleted]

---

### Slide 29: Versioning and Stale-While-Revalidate
- Versioning approach: cache key includes a version, bumping the version invalidates instantly
  - Old: `user:42` → New: `user:42:v17` — increment version, all readers fetch new key, old key expires naturally
- Avoids the race conditions of explicit deletes
  - Atomic version bump = atomic invalidation; no "delete then write" window
- Stale-while-revalidate (SWR) pattern: serve stale data while refreshing in background
  - HTTP `Cache-Control: max-age=60, stale-while-revalidate=600`
  - For 60s, fresh; for next 600s, serve stale and refresh async; after that, must revalidate
- Combines best of TTL and refresh-ahead
  - User never waits for refresh; cache is "soft expired" rather than "hard expired"
- Real example: Vercel/Next.js ISR (Incremental Static Regeneration), SWR React library
  - Modern web frameworks bake SWR into their data-fetching primitives
[Visual suggestion: Two-bar timeline — Bar 1: "fresh window (60s)" green, Bar 2: "stale-while-revalidate window (600s)" yellow with async refresh arrow, then "must revalidate" red]

---

### Slide 30: Invalidation — Trade-offs Summary
- TTL: simplest, self-healing, but bounded staleness
  - Use for: data with predictable update cadence, low write rates, tolerable staleness
- Event-driven (sync delete): fresh, but tight coupling, race-prone
  - Use for: cache-aside in monoliths, write paths fully under your control
- Event-driven (async CDC): fresh, decoupled, scales to many caches
  - Use for: distributed systems, multiple consumers of the same data
- Versioning: race-free, atomic, but key-management overhead
  - Use for: user profiles, configurations, anywhere instant global flip is needed
- Stale-while-revalidate: fast and fresh-enough, but explicit staleness window
  - Use for: dashboards, feeds, public content with eventual consistency
- Pragmatic rule: ALWAYS combine TTL with active invalidation as a safety net
  - TTL bounds the bug — even if invalidation is broken, cache eventually self-corrects
[Visual suggestion: Comparison table — strategy / freshness / complexity / coupling / safety net]

---

### Slide 31: Cache Eviction — Why We Need It
- Caches are bounded memory — when full, something must be removed to make room for new entries
  - Eviction policy = the rule for choosing the victim
- Goal: evict the entry least likely to be requested again, keep entries most likely to be requested
  - Different policies make different predictions about future access patterns
- Eviction is not invalidation
  - Invalidation: entry is wrong, must remove
  - Eviction: entry might still be valid, but we need the space
- A poor eviction policy can tank hit ratio even with plenty of memory
  - A 100GB cache with random eviction may do worse than a 10GB cache with LRU
- Real workloads have skewed access patterns (Zipf-like) — exploit this in policy choice
  - 80/20 rule: keep the 20% hottest keys, evict the long tail aggressively
[Visual suggestion: Cache visualized as a fixed-size box; new item arriving, "victim" item being pushed out via different doors labeled with policy names]

---

### Slide 32: LRU — Least Recently Used
- Evict the entry whose last access is furthest in the past
  - Assumption: data accessed recently is likely to be accessed again soon (temporal locality)
- Most popular eviction policy — sane default for almost all workloads
  - Used by Redis (allkeys-lru), Memcached, OS page caches, CPU caches
- Implementation: doubly-linked list + hash map → O(1) get/set/evict
  - Move accessed entry to front; evict from back
- Strengths
  - Adapts to changing access patterns
  - Simple, well-understood, O(1)
- Weaknesses
  - One scan over a large dataset can pollute the cache (cache thrashing)
  - Doesn't distinguish frequently used from one-time hot data
- Real example: Redis maxmemory-policy allkeys-lru — battle-tested default
  - Variants like LRU-K, ARC, 2Q address scan pollution
[Visual suggestion: Linked list diagram — head (most recent) ← A ← B ← C ← D (least recent, eviction target); on access to C, it moves to head]

---

### Slide 33: LFU — Least Frequently Used
- Evict the entry with the lowest access count
  - Assumption: frequently accessed in the past = frequently accessed in the future
- Better than LRU for stable, skewed workloads (e.g., 20% of keys serve 80% of traffic)
  - Hot keys accumulate count and stay; cold keys evicted regardless of recency
- Weakness: stale popularity — once-hot keys stay forever even after they cool down
  - Solved by aging/decay schemes (TinyLFU, W-TinyLFU)
- Modern variants
  - TinyLFU (used by Caffeine): tiny count-min sketch + window LRU; near-optimal hit ratios
  - Caffeine often beats Guava by 10–20% hit rate on production workloads
- Implementation: requires frequency counters + min-heap or buckets
  - More complex than LRU, but Caffeine has made it practical
- Use when: workload has stable hot keys (recommendation systems, popular content)
  - Don't use for: workloads with shifting popularity (trending news, real-time feeds)
[Visual suggestion: Histogram of access frequencies — eviction arrow points at the lowest-frequency bar; aging shown as bars decaying over time]

---

### Slide 34: FIFO and Random Eviction
- FIFO (First In First Out): evict the oldest entry by insertion time, ignore access pattern
  - Simple queue; O(1); used in some hardware caches and simple buffers
- FIFO weakness: a hot entry inserted long ago gets evicted even if just accessed
  - Generally underperforms LRU; rarely used in software caches today
- Random eviction: pick a random entry to evict
  - Surprisingly competitive with LRU at scale (Redis allkeys-random)
- Random's strength: zero metadata overhead, cache-friendly, no contention
  - Useful when memory tracking overhead would dwarf benefit
- Variants: random sample N, evict worst by some metric
  - Redis's LRU is actually approximate — samples 5 keys, evicts oldest among them
- Use when: workload is uniform, or per-entry tracking is too expensive
  - Reality: rarely the optimal choice but easy to implement and surprisingly OK
[Visual suggestion: Two queues side by side — FIFO showing insertion-order eviction; Random showing dart hitting a random entry]

---

### Slide 35: Eviction Policy — Choosing the Right One
- LRU: default for general-purpose caches with temporal locality
  - Web sessions, recently viewed items, query result caches
- LFU (or W-TinyLFU via Caffeine): when popularity is stable and skewed
  - Recommendation engines, popular content caches, CDN edge caches
- FIFO: simple buffers, time-windowed data, when access pattern doesn't matter
  - Recent log entries, audit trails (rarely a primary cache choice)
- Random: high-throughput caches where metadata cost matters
  - Massive Memcached-style caches, hardware-constrained systems
- TTL-only: when freshness matters more than hit ratio
  - DNS, configuration caches, anything with deterministic update windows
- Hybrid policies dominate modern systems
  - Caffeine's W-TinyLFU = window LRU + frequency-aware admission filter; SOTA in JVM
[Visual suggestion: Decision flowchart — "Stable hot keys?" → LFU; "Recency matters?" → LRU; "Time-windowed?" → FIFO; "Tracking too expensive?" → Random]

---

### Slide 36: Eviction — Real-World Examples
- Redis: configurable per-deployment via `maxmemory-policy`
  - Options: noeviction, allkeys-lru, allkeys-lfu, allkeys-random, volatile-lru (only TTL keys), etc.
- Memcached: slab-allocator + LRU per slab class
  - Each size class has its own LRU; avoids fragmentation but creates per-slab eviction pressure
- Linux page cache: 2Q (active + inactive lists) — approximate LRU with scan resistance
  - Why a simple `cat huge_file` doesn't blow away your hot working set
- CDN edge nodes: typically LRU or LFU per POP
  - Cloudflare uses Tiered Cache + LRU; Fastly uses similar approaches
- CPU caches: hardware pseudo-LRU (true LRU is too expensive in silicon)
  - Tree-based bit-encoded approximation; gets within ~5% of true LRU
[Visual suggestion: Logos of Redis, Memcached, Linux, Cloudflare with their eviction policies labeled below]

---

### Slide 37: Distributed Caching — Why Go Distributed?
- Single-node cache is limited by RAM, CPU, and network of one machine
  - Single Redis node tops out around 100GB and ~100K ops/sec; need more for scale
- Distributed cache spreads data across multiple nodes
  - 10 nodes × 100GB = 1TB working set; 10 × 100K = 1M ops/sec aggregate
- Solves three problems at once
  - Capacity (more total memory than any single machine)
  - Throughput (parallel ops across nodes)
  - Availability (replication so single-node failure doesn't lose all cache)
- Adds new problems
  - How to route a key to the correct node (sharding)
  - How to handle node failures without invalidating all keys (consistent hashing)
  - How to keep replicas consistent
- Two giants dominate the space: Redis and Memcached
  - Modern alternatives: Hazelcast, Aerospike, Apache Ignite, KeyDB, DragonflyDB
[Visual suggestion: Single big-box cache labeled "doesn't scale" vs. cluster of N smaller boxes labeled with sharding/replication arrows]

---

### Slide 38: Redis vs. Memcached — Feature Comparison
- Data types
  - Memcached: strings only (max 1MB by default)
  - Redis: strings, lists, sets, sorted sets, hashes, streams, hyperloglog, bitmaps, geo, JSON
- Persistence
  - Memcached: in-memory only, lost on restart
  - Redis: optional RDB snapshots + AOF append-only log; configurable durability
- Threading
  - Memcached: multi-threaded (good per-node throughput)
  - Redis: single-threaded core (Redis 6+ has I/O threads); simpler reasoning, less locking
- Replication and clustering
  - Memcached: client-side sharding only
  - Redis: built-in replication, Redis Cluster with hash slots, Sentinel for HA
- Use cases
  - Memcached: simple object cache, session storage, ephemeral cache
  - Redis: cache + queue + pub/sub + leaderboard + rate limiter — Swiss army knife
[Visual suggestion: Side-by-side table comparing Memcached and Redis across data types, persistence, threading, replication, ecosystem]

---

### Slide 39: Redis vs. Memcached — When to Choose Which
- Choose Memcached when
  - You need a pure cache, nothing else
  - Object size is small and uniform
  - You want simple horizontal scaling with client-side hashing
  - Predictable performance under high concurrency
- Choose Redis when
  - You need data structures (sorted sets for leaderboards, lists for queues)
  - You want persistence as a safety net
  - You need pub/sub, streams, scripting (Lua), or transactions
  - You want an integrated solution rather than 5 separate systems
- Real-world deployments
  - Facebook: massive Memcached fleet, custom enhancements (mcrouter)
  - Twitter: Redis for timelines, Memcached for objects (different fits, same company)
  - GitHub, Stack Overflow, Instagram: Redis
- Default modern choice: Redis (versatility wins for most teams)
  - Memcached still excels for very-large simple object caches at extreme scale
[Visual suggestion: Two columns of company logos under "Memcached shops" (Facebook, Pinterest historically) vs "Redis shops" (Twitter, GitHub, Snap, Discord)]

---

### Slide 40: Consistent Hashing — Sharding Across Nodes
- Problem: with N cache nodes, how do we route a key to the right one?
  - Naive: `node = hash(key) % N` — but adding/removing a node remaps almost all keys
- Consistent hashing: hash both keys and nodes onto the same ring (e.g., 0–2^32)
  - Each key is owned by the next node clockwise on the ring
- When a node is added/removed, only ~1/N of keys move
  - Dramatic improvement over modulo hashing
- Virtual nodes (vnodes) smooth load distribution
  - Each physical node owns 100–1000 vnodes around the ring → uniform key distribution
- Used in
  - Memcached client libraries (libketama)
  - Redis Cluster (hash slots — fixed 16384 slots, simpler variant of consistent hashing)
  - DynamoDB, Cassandra, Riak (full database use, same idea)
[Visual suggestion: Circular ring with node markers (N1, N2, N3, N4) and key markers (K1, K2, K3) — each key drawn with arrow to next clockwise node; show one node leaving with only adjacent keys re-mapping]

---

### Slide 41: Cache Stampede / Thundering Herd
- A hot key expires; thousands of concurrent readers all miss simultaneously
  - All of them race to query the DB and rebuild the cache → DB collapses
- Famous failure mode — has caused outages at Facebook, Instagram, Reddit
  - Worst when key is extremely popular and DB query is expensive
- Symptoms
  - Sudden DB CPU spike at exact TTL boundaries
  - Cascading latency spikes every TTL period
  - Rare but catastrophic when it happens
- Three classic solutions
  - Mutex / single-flight: only one request rebuilds, others wait
  - Probabilistic early expiration: each reader independently decides "should I refresh now?"
  - Stale-while-revalidate: serve stale, refresh in background
- Real example: Instagram's "promotional cache" pattern, Facebook's "leases" in Memcached
  - Memcached leases (described in their scaling paper) coordinate which client repopulates
[Visual suggestion: Timeline showing TTL expiry; without mitigation: spike of 1000 concurrent DB queries; with mutex: one query, 999 waiters; with SWR: zero blocked queries]

---

### Slide 42: Stampede Solution — Mutex / Single-Flight
- On cache miss, acquire a lock for that key before querying DB
  - First requester gets lock, queries DB, populates cache, releases lock
  - Concurrent requesters either wait on the lock or retry the cache after a short sleep
- Implementation
  - Redis: `SET key:lock value NX EX 10` — atomic acquire with TTL safety
  - Go: golang.org/x/sync/singleflight — in-process coalescing
- Strengths: simple, prevents stampede, works for any read path
  - Weakness: lock contention itself can become a bottleneck on extreme hot keys
- Distributed lock pitfalls
  - Lock holder crashes → use TTL on lock to avoid permanent lockout
  - Be aware of Redlock controversy (Martin Kleppmann critique) for stricter use cases
- Pattern works at any scale from in-process to global
  - Cloudflare uses single-flight extensively at edge for backend protection
[Visual suggestion: Sequence diagram — Request 1 acquires lock, queries DB, fills cache, releases lock; Requests 2–1000 wait briefly, then read fresh cache value]

---

### Slide 43: Stampede Solution — Probabilistic Early Expiration
- Each reader independently decides whether to proactively refresh, weighted by closeness to TTL
  - Probability of refresh increases as TTL approaches; far from expiry, almost zero chance
- XFetch algorithm (Vattani et al., 2015): mathematically optimal early refresh
  - `if now - delta * beta * log(rand()) >= expiry: refresh()`
  - Spreads refresh load smoothly over the last fraction of TTL
- Strengths
  - No locking required — fully decentralized
  - No synchronized expiry boundary, no thundering herd
- Weaknesses
  - Some refreshes happen "early" — small wasted work
  - Requires changing read path to know TTL/expiry timestamps
- Used in production by HashiCorp, Cloudflare, and others for hot-key caches
  - Combines beautifully with stale-while-revalidate semantics
[Visual suggestion: Probability curve over TTL — flat at 0 for first 80%, rising sharply in last 20%, several reader dots triggering refresh at staggered times]

---

### Slide 44: Hot Key Problem
- One key receives massively disproportionate traffic, overwhelming a single cache node
  - "Justin Bieber problem" — millions of fans, all hitting one timeline key
- Consistent hashing routes key X to node N; if X is super-hot, N is super-loaded
  - Other nodes idle, N's CPU/network melts; classic load skew
- Solutions
  - Local replica caching: app-level L1 in front of distributed L2 catches the hot key
  - Key splitting: shard hot key into key:0..N variants, randomized read fanout
  - Read replicas: replicate hot keys to multiple cache nodes; route reads round-robin
  - Promotional caching: pre-emptively warm and pin known hot keys
- Detection
  - Per-key counters at proxy/router (Twemproxy, Mcrouter)
  - Sample-based heavy hitter detection (count-min sketch)
- Real example: Twitter's "celebrity" handling — separate cache tier for top accounts
  - Hot keys are usually predictable (celebrities, breaking news, viral content)
[Visual suggestion: Bar chart showing one massive bar (hot key) dwarfing all others; mitigation diagram showing the hot key replicated across multiple nodes]

---

### Slide 45: Distributed Caching — Trade-offs Summary
- Centralized cache (single Redis node): simple, consistent, but limited capacity and SPOF
  - Use for: small services, low-scale workloads
- Sharded cache (consistent hashing): scales linearly, but no replication = data loss on node failure
  - Use for: pure caches where loss is acceptable, scale > durability
- Replicated cache (master + replicas): high availability, but eventual consistency between replicas
  - Use for: read-heavy hot data, where reads can hit any replica
- Sharded + replicated (Redis Cluster): scale + HA, but complex ops and edge cases
  - Use for: large production systems; the standard choice today
- Multi-region: cross-region replication for global apps, but huge consistency challenges
  - Use for: global products willing to accept eventual cross-region staleness
[Visual suggestion: Spectrum diagram — left "Simple/Limited" (single node) → right "Complex/Scalable" (sharded+replicated+multi-region) with examples placed along the spectrum]

---

### Slide 46: Caching — Key Takeaways
- Caching is the cheapest performance lever in system design
  - One Redis layer can 10x your throughput without touching the database
- Cache hit ratio is the metric — track it, alert on it, optimize for it
  - Below 80%, your cache is barely earning its keep
- Cache-aside is the default strategy; learn the others for the workloads where they fit
  - Match write-through, write-behind, refresh-ahead to specific data shapes
- Invalidation is hard — combine TTL (safety net) with active invalidation (freshness)
  - Versioned keys and stale-while-revalidate are powerful tools
- Distributed caching adds capacity/availability but requires consistent hashing, stampede protection, hot-key handling
  - Redis vs. Memcached: choose Redis unless you have a reason not to
- Cache as close to the user as correctness allows; layered caches multiply your effective hit ratio
  - Browser → CDN → proxy → app → distributed → DB — each layer matters
[Visual suggestion: Top-5 list with bold callouts for each takeaway; Twitter/Facebook/YouTube logos as supporting evidence]

---

### Slide 47: Caching — Interview Tips
- When asked about latency or throughput, propose caching FIRST — it's the lowest-cost win
  - "Before scaling the database, I'd add a cache layer to absorb read traffic"
- Always state your strategy explicitly: "I'd use cache-aside with Redis, 5-minute TTL, LRU eviction"
  - Vague answers ("I'd add caching") get probed; specific answers get nods
- Be ready to discuss invalidation — interviewers will press here
  - Have a default answer: "TTL as safety net + active invalidation on write + versioned keys for instant flips"
- Mention real systems to anchor your design
  - "Like Twitter's Caffeine + Redis layered cache" or "Like Facebook's Memcached architecture"
- Address consistency explicitly — name the trade-off, don't dodge it
  - "This gives eventual consistency; for read-after-write, I'd use write-through for that path"
- Discuss failure modes proactively (cold start, stampede, hot keys)
  - Showing you've thought about edge cases is a senior-level signal
- Know the numbers: RAM ~100ns, network ~1ms, disk ~10ms, cross-region ~100ms
  - Latency budgeting is a frequent follow-up
[Visual suggestion: Interview cheat sheet — numbered tips with example phrases in italics]

---

### Slide 48: Caching — Common Pitfalls
- Caching everything indiscriminately
  - Pitfall: low-locality data wastes memory; measure access patterns first
- Forgetting to invalidate on writes
  - Pitfall: silent staleness, hard to debug; pair every write with invalidation in same code path
- No TTL as a backstop
  - Pitfall: a single missed invalidation persists forever; always set a sane TTL
- Ignoring cache stampede
  - Pitfall: works fine until the hot key expires; add mutex / SWR / probabilistic refresh
- Over-trusting the cache for source of truth
  - Pitfall: cache is disposable; never write data only to cache (unless write-behind with durable backing)
- Massive cache key cardinality
  - Pitfall: caching unique queries with no reuse → 0% hit rate, just adds latency
- Not monitoring hit ratio
  - Pitfall: you can't fix what you don't measure; alert when hit ratio drops
- Mixing TTLs across related keys (cache aliasing)
  - Pitfall: user object expires at t=60, user's posts at t=120 → inconsistent view
- Using local cache for personalized data without sticky sessions
  - Pitfall: user's request hits a different server with stale local cache; use distributed cache instead
- Premature caching as a substitute for fixing the real bottleneck
  - Pitfall: caching a slow query is a band-aid; fix the query, then cache it
[Visual suggestion: "Cache landmines" infographic — each pitfall as a labeled mine icon with a brief mitigation note next to it]

---

### Slide 49: Caching — Mental Model Recap
- Cache = a small, fast layer that remembers expensive answers
  - Trade memory for time, trade freshness for speed
- Three questions to answer for every cache you design
  - WHERE: which layer (browser / CDN / proxy / app / distributed / DB)?
  - HOW: which strategy (cache-aside / read-through / write-through / write-behind / refresh-ahead)?
  - WHEN: invalidation (TTL / event-driven / versioned / SWR) and eviction (LRU / LFU / FIFO / random)?
- Caching is multi-layered by default in modern systems
  - Each layer absorbs a slice; misses cascade downward
- Distributed caching turns one fast box into many; consistent hashing makes it scale
  - Mind the stampede, mind the hot key, mind the network hop
- Master caching and you understand 40% of system design
  - Every "fast" system you admire is fast because someone put a cache in the right place
[Visual suggestion: One-page mental model — three concentric questions (WHERE / HOW / WHEN) with strategy options branching from each]

---

### Slide 50: Section 7 Wrap-Up
- We covered: definition, hierarchy, hit ratio, layers, strategies, invalidation, eviction, distributed caching
  - Each topic with intuition, examples, diagrams, and trade-offs
- Caching is the single most-tested topic in system design interviews
  - Expect questions about it in 80%+ of design rounds
- Always anchor caching choices in concrete trade-offs
  - "I'd choose X because it optimizes for Y, accepting cost Z"
- Up next: Section 8 — Databases, where caching meets persistence
  - Buffer pools, query caches, materialized views — caching shows up there too
- Remember: a well-placed cache is the closest thing to free performance
  - But every cache is a deal with the consistency devil — choose your terms wisely
[Visual suggestion: Section-7 summary card with all 10 sub-topics as a checklist, transitioning into Section 8 preview]
