## Section 6: Databases — RDBMS and NoSQL

### Slide 1: Section Overview — Why Databases Matter
- The database is the system's memory
  - It is the single most important component for correctness, durability, and scale.
- Choice of database shapes architecture
  - Schema model, scaling strategy, and consistency guarantees ripple through every service.
- Two dominant families: RDBMS and NoSQL
  - RDBMS = structured, relational, ACID; NoSQL = flexible, distributed, BASE.
- Real systems use both
  - Polyglot persistence: pick the right tool for each workload (orders in Postgres, feed in Cassandra).
- This section covers RDBMS, NoSQL types, SQL vs NoSQL, and scaling techniques
  - With trade-offs, examples, and interview-ready framing.
[Visual suggestion: Split-screen graphic — left half shows a structured spreadsheet labeled "RDBMS", right half shows a JSON document, key-value pair, and graph node labeled "NoSQL".]

---

## Part 1: Relational Databases (RDBMS)

### Slide 2: What Is an RDBMS — Concept Introduction
- Data stored in tables (rows and columns)
  - A table is a 2D structure where each row is a record and each column is a typed attribute.
- Strict schema enforced before writes
  - Every row in a table conforms to the same column definitions and data types.
- Relationships expressed via foreign keys
  - One table references another's primary key, modeling 1:1, 1:N, and N:M relationships.
- Manipulated using SQL (Structured Query Language)
  - Declarative: you describe what you want, not how to fetch it.
- Examples: PostgreSQL, MySQL, Oracle, SQL Server
  - Decades of maturity, tooling, and ecosystem support.
[Visual suggestion: Two tables side by side. Users(id, name, email) connected by a foreign key arrow to Orders(order_id, user_id, total). Highlight the user_id column as the link.]

### Slide 3: RDBMS Deep Dive — Tables, Keys, and Relations
- Primary key uniquely identifies a row
  - Typically an auto-incrementing integer or UUID; enforces uniqueness and indexes by default.
- Foreign key enforces referential integrity
  - Database refuses to insert an Order with a user_id that does not exist in Users.
- Normalization eliminates redundancy
  - Splitting data across tables (3NF) so each fact lives in exactly one place.
- Joins reassemble normalized data at query time
  - INNER, LEFT, RIGHT, FULL — the cost of normalization is paid on reads.
- Constraints encode business rules
  - NOT NULL, UNIQUE, CHECK, DEFAULT — the database becomes a guardian of data quality.
[Visual suggestion: ER diagram with three boxes — Users, Orders, Products — and a junction table OrderItems linking Orders to Products (N:M). Label each line with cardinality (1, N).]

### Slide 4: ACID Properties — Concept Introduction
- ACID is the contract that makes RDBMS trustworthy for money, inventory, and identity
  - Four guarantees that hold even when crashes, conflicts, or concurrency happen.
- A — Atomicity
  - All operations in a transaction succeed together, or none of them do. No half-states.
- C — Consistency
  - The database moves from one valid state to another; constraints are never violated.
- I — Isolation
  - Concurrent transactions appear to run one at a time; intermediate states are hidden.
- D — Durability
  - Once committed, data survives crashes, power loss, and reboots (written to disk/WAL).
[Visual suggestion: Four-quadrant graphic. Each quadrant shows a letter (A, C, I, D) with a small icon — a chain link, a checkmark, two parallel arrows, a hard drive.]

### Slide 5: ACID Deep Dive — The Bank Transfer Example
- Classic example: transfer $100 from Alice to Bob
  - Two operations: debit Alice (-$100), credit Bob (+$100). Both must succeed.
- Atomicity in action
  - If credit to Bob fails after debiting Alice, the debit is rolled back. No money lost.
- Consistency in action
  - Total money in the system before and after the transfer is identical. Sum invariant preserved.
- Isolation in action
  - A second transaction reading Alice's balance mid-transfer sees either the old or new value, never an in-between.
- Durability in action
  - After the transfer commits and the bank's server crashes, the transfer is still recorded on restart.
[Visual suggestion: Four-panel comic. Panel 1: Alice $500, Bob $200. Panel 2: Atomicity (-100/+100 atomic). Panel 3: Crash icon. Panel 4: Reboot, Alice $400, Bob $300 — durable.]

### Slide 6: When to Use RDBMS
- Structured data with stable schema
  - User profiles, orders, financial records — entities that don't change shape weekly.
- Complex queries with joins and aggregations
  - "Total revenue per region per month for top-10 products" — SQL excels here.
- Strong transactional guarantees needed
  - Banking, e-commerce checkout, inventory, ticketing — anywhere correctness > scale.
- Reporting, analytics, and ad hoc queries
  - SQL is the lingua franca of analysts and BI tools.
- Moderate scale (thousands to low millions of QPS with tuning)
  - A well-tuned Postgres handles enormous workloads before you need to shard.
[Visual suggestion: Decision flowchart — "Need ACID transactions? -> Yes -> RDBMS. Schema stable? -> Yes -> RDBMS. Complex joins? -> Yes -> RDBMS."]

### Slide 7: Indexes — Concept Introduction
- An index is an auxiliary data structure that accelerates lookups
  - Like the index in the back of a book — find a topic without reading every page.
- Most common: B-tree index
  - Balanced tree that keeps lookup, insert, and delete at O(log n).
- Without index: full table scan O(n)
  - Database reads every row to find a match — fine for small tables, fatal at scale.
- With index: O(log n) lookup
  - 1 billion rows? ~30 comparisons instead of 1 billion.
- Indexes are not free
  - They consume disk, slow down writes, and need maintenance.
[Visual suggestion: Two diagrams side by side. Left: linear scan through 1B rows (red, slow). Right: B-tree with 4 levels reaching the same row (green, fast).]

### Slide 8: B-Tree Index — How It Works
- Self-balancing tree with sorted keys
  - Each node holds many keys (high fan-out), keeping the tree shallow even for billions of rows.
- Reads traverse from root to leaf in O(log n)
  - 4–5 disk reads typically reach any row in a multi-billion-row table.
- Range queries are fast
  - Leaves are linked in sorted order — "WHERE age BETWEEN 25 AND 35" walks adjacent leaves.
- Writes must update the index
  - Every INSERT/UPDATE/DELETE rebalances the tree — extra cost on writes.
- Multiple indexes per table possible
  - Each index is its own structure; more indexes = faster reads, slower writes, more disk.
[Visual suggestion: B-tree diagram. Root node with 3 keys, internal nodes branching out, leaf nodes at the bottom linked left-to-right with horizontal arrows showing the sorted chain.]

### Slide 9: Indexes — Read vs Write Trade-off
- Reads: indexes turn O(n) into O(log n)
  - Massive speedup for SELECT, especially with WHERE, JOIN, and ORDER BY.
- Writes: every modification updates every relevant index
  - INSERT into a table with 5 indexes = 6 disk operations (1 table + 5 indexes).
- Storage cost
  - Indexes can occupy 10–50% of table size; sometimes more than the data itself.
- Index only what you query
  - Don't index every column "just in case" — measure first, then add.
- Composite indexes for multi-column queries
  - INDEX(country, city) speeds up WHERE country='US' AND city='NYC' but not WHERE city alone.
[Visual suggestion: Seesaw diagram. One side labeled "Read speed" with a green up arrow, other side "Write speed" with a red down arrow. Indexes sit in the middle as the fulcrum.]

### Slide 10: Query Optimization Basics
- The query planner translates SQL into an execution plan
  - For each query, the database picks join order, index usage, and scan strategy.
- EXPLAIN reveals the plan
  - `EXPLAIN ANALYZE SELECT ...` shows estimated and actual cost, rows, and operations.
- Watch for full table scans on large tables
  - "Seq Scan" on millions of rows = missing index or non-sargable predicate.
- Avoid SELECT *
  - Fetching unused columns wastes I/O, memory, and network.
- Statistics drive the planner
  - Run ANALYZE periodically so the planner knows row counts and value distributions.
[Visual suggestion: Screenshot mockup of EXPLAIN output showing nodes — Hash Join, Index Scan, Seq Scan — with cost annotations. Highlight a "Seq Scan on 10M rows" in red.]

### Slide 11: RDBMS Examples in the Wild
- PostgreSQL — the Swiss Army knife
  - Open source, ACID, JSON support, extensions (PostGIS, pg_trgm), strong concurrency (MVCC).
- MySQL — the web's workhorse
  - Powers WordPress, half the internet's CMS layer; fast, simple, well-known.
- Oracle — the enterprise heavyweight
  - Decades in banks, telecoms, governments; rich feature set, expensive licensing.
- SQL Server — the Microsoft stack pick
  - Tight integration with .NET, Windows, and Azure; strong tooling.
- SQLite — the embedded champion
  - Single-file database in your phone, browser, OS. Most-deployed database on Earth.
[Visual suggestion: Logo grid of the five databases with one-line descriptors under each.]

### Slide 12: RDBMS Trade-offs
- Strong consistency, mature tooling, declarative SQL
  - Decades of optimization, books, and battle-tested patterns.
- Rigid schema slows iteration
  - Adding a column to a 1B-row table can lock the table for hours without care.
- Vertical scaling is the easy path
  - Bigger CPU, more RAM, faster SSD — but there's a ceiling and it's expensive.
- Horizontal scaling (sharding) is hard
  - Distributing joins and transactions across nodes is genuinely difficult.
- Best fit: structured, transactional, query-heavy systems
  - Banking, ERP, CRM, e-commerce checkout, identity.
[Visual suggestion: Pros/Cons table — left column green check icons (ACID, SQL, joins, mature), right column red X icons (rigid schema, vertical scaling limit, sharding pain).]

---

## Part 2: NoSQL Databases — Types Deep Dive

### Slide 13: NoSQL — Concept Introduction
- "Not Only SQL" — a family, not a single technology
  - Born from Web 2.0 needs: massive scale, flexible schemas, distributed by default.
- Four main types
  - Key-Value, Document, Wide Column, Graph — each with different data models and use cases.
- Designed for horizontal scale
  - Distribute data across many cheap machines instead of one expensive one.
- Trade strict ACID for flexibility and scale
  - Most NoSQL systems offer BASE (eventual consistency) by default.
- Schema-less or schema-flexible
  - No need to ALTER TABLE before adding a new field.
[Visual suggestion: Four-quadrant grid — top-left Key-Value (Redis), top-right Document (MongoDB), bottom-left Wide Column (Cassandra), bottom-right Graph (Neo4j). Each quadrant shows a tiny data model sketch.]

### Slide 14: Key-Value Stores — Concept
- Simplest data model: a giant distributed hash map
  - You give it a key, it gives you a value. That's it.
- Operations are O(1) average
  - GET, SET, DELETE — predictable, blazing-fast latency (sub-millisecond).
- Values are opaque to the database
  - Could be a string, JSON blob, image bytes — the store doesn't care.
- No queries, joins, or filtering on values
  - You either know the key, or you don't find the data.
- Examples: Redis, Memcached, DynamoDB, Riak
  - Used as caches, session stores, leaderboards, rate limiters.
[Visual suggestion: Hash table diagram — keys ("user:123", "session:abc", "cart:7") on the left, opaque values on the right, arrows connecting them.]

### Slide 15: Key-Value Stores — Use Cases and Examples
- Caching layer in front of slower databases
  - Redis caches hot user profiles; cache hit avoids hitting Postgres.
- Session storage for web apps
  - Store login session by session ID; fast lookup on every request.
- Real-time leaderboards and counters
  - Redis sorted sets rank millions of players in microseconds.
- Shopping cart and shopping-session state
  - Per-user data, no relational joins needed.
- DynamoDB at Amazon scale
  - Powers Amazon.com's catalog and orders pipeline; predictable single-digit-ms latency at any scale.
[Visual suggestion: Architecture diagram — App server -> Redis (cache) -> Postgres (source of truth). Show 95% of reads hitting Redis, 5% missing through to Postgres.]

### Slide 16: Document Stores — Concept
- Data stored as self-contained documents (typically JSON/BSON)
  - Each document is a flexible, nested record — no fixed schema across documents.
- Documents grouped into collections
  - Like tables, but documents in the same collection can have different fields.
- Rich queries on document fields
  - Unlike key-value, you can query nested fields, arrays, and ranges.
- Indexes on any field
  - Including nested paths like `address.city` or `tags.0`.
- Examples: MongoDB, CouchDB, Amazon DocumentDB, Firestore
  - Ideal when entities are naturally hierarchical (a blog post with comments embedded).
[Visual suggestion: A JSON document for a "blog_post" with nested comments array and tags array. Show how this would map to 3 tables in RDBMS (Posts, Comments, Tags) — highlight the simplification.]

### Slide 17: Document Stores — Use Cases and Examples
- Content management systems
  - Articles with varying fields (image, video, gallery) fit naturally as documents.
- User profiles with evolving fields
  - Adding "preferences.dark_mode" doesn't require a migration.
- Product catalogs with diverse attributes
  - A shoe has size and color; a laptop has CPU and RAM — same collection, different fields.
- Event logging and IoT data
  - Documents with timestamps and sensor readings, schema evolves as new sensors come online.
- MongoDB at scale
  - Used by The New York Times, eBay, Cisco — millions of documents, sharded clusters.
[Visual suggestion: MongoDB collection illustration with three documents — a shoe, a laptop, a book — each with different fields, all in one "products" collection.]

### Slide 18: Wide Column Stores — Concept
- Data stored as rows where each row can have a flexible set of columns
  - Think "table" but each row picks its own columns; columns are sparse.
- Organized into column families
  - A column family groups related columns physically together on disk.
- Optimized for massive write throughput and time-series data
  - Append-friendly storage (LSM trees) — millions of writes per second per node.
- Queries by row key are fast; cross-row scans are slower
  - Designed for predictable access patterns, not ad hoc joins.
- Examples: Apache Cassandra, HBase, ScyllaDB, Google Bigtable
  - The backbone of many internet-scale services.
[Visual suggestion: Wide-column table illustration. Row keys on the left ("user:123"), then two column families (PersonalInfo: name, email) and (Activity: last_login, last_action) — show that rows can have different columns under each family.]

### Slide 19: Column Families — Going Deeper
- A column family is a container for related columns
  - Stored together on disk, accessed together — analogous to a "vertical partition".
- Each row may have any subset of columns within a family
  - Sparse rows are normal — no NULL bloat for missing columns.
- Read/write paths are tuned per family
  - Different compression, caching, and TTLs per family.
- Wide rows can have millions of columns
  - Time-series: row = sensor_id, columns = timestamps -> readings.
- Cassandra's keyspace -> table -> partition -> row -> columns hierarchy
  - Partition key determines which node owns the data.
[Visual suggestion: Diagram of a sensor wide row. Row key "sensor_42" with thousands of columns named by timestamp ("2026-04-28T10:00", "2026-04-28T10:01", ...) each storing a temperature reading.]

### Slide 20: Wide Column Stores — Use Cases and Examples
- Time-series data and IoT
  - Sensor readings, metrics, logs — billions of writes, queried by time range.
- Messaging and activity feeds
  - WhatsApp, Discord, Instagram store messages and events at massive scale.
- Recommendation systems' feature stores
  - Pre-computed features per user, retrieved by user ID in microseconds.
- Cassandra at Netflix and Discord
  - Discord migrated trillions of messages from MongoDB to Cassandra to ScyllaDB.
- HBase at Facebook (Messenger)
  - Stores conversations and search indexes; pairs with Hadoop.
[Visual suggestion: Architecture diagram — IoT devices -> Kafka -> Cassandra cluster (5 nodes) -> dashboard reading recent metrics by time range.]

### Slide 21: Graph Databases — Concept
- Data modeled as nodes (entities) and edges (relationships)
  - Each node and edge can have properties (key-value pairs).
- Relationships are first-class citizens
  - Traversing an edge is O(1) — no join cost regardless of graph size.
- Query language: Cypher (Neo4j), Gremlin, GQL
  - "MATCH (a:Person)-[:FRIEND]->(b:Person) WHERE a.name='Alice' RETURN b"
- Excels at multi-hop relationship queries
  - "Friends of friends who like jazz and live in Berlin" — a nightmare in SQL, trivial in graph.
- Examples: Neo4j, Amazon Neptune, JanusGraph, ArangoDB
  - Used wherever connection patterns matter more than entities themselves.
[Visual suggestion: Graph illustration — circles for People, lines labeled "FRIEND", "LIKES", "LIVES_IN", connecting to Bands, Cities. Highlight a 3-hop path "Alice -> Bob -> JazzBand -> Berlin".]

### Slide 22: Graph Databases — Use Cases and Examples
- Social networks
  - Friends-of-friends, mutual connections, network analysis (LinkedIn, Facebook).
- Recommendation engines
  - "Customers who bought X also bought Y" — collaborative filtering as graph traversal.
- Fraud detection
  - Detect rings of accounts sharing devices, addresses, or payment methods.
- Knowledge graphs
  - Google Knowledge Graph, Wikidata — entities and relationships powering search.
- Network and IT operations
  - Map dependencies between services, hosts, and incidents for root-cause analysis.
[Visual suggestion: Fraud-detection graph — multiple "Account" nodes connecting to a single "Device" node and "Address" node, highlighting suspicious shared edges in red.]

### Slide 23: NoSQL Trade-offs Across Types
- Key-Value: ultimate speed, minimal querying
  - You sacrifice query power for raw latency and throughput.
- Document: schema flexibility with rich queries
  - Trade-off: harder to enforce cross-document consistency.
- Wide Column: massive write throughput
  - Trade-off: must design tables around access patterns up front.
- Graph: relationship traversal is cheap
  - Trade-off: not ideal for bulk analytics or simple key lookups.
- No NoSQL type does everything well
  - Pick based on dominant access pattern, not hype.
[Visual suggestion: Radar chart with axes — Read Speed, Write Speed, Schema Flexibility, Query Power, Relationship Depth. Each NoSQL type drawn as a colored polygon showing strengths.]

---

## Part 3: SQL vs NoSQL — When to Use Which

### Slide 24: SQL vs NoSQL — Concept Introduction
- Not a war, a toolkit
  - Modern systems use both; the question is which fits a given workload.
- Five lenses to compare
  - Schema, scale, consistency, query complexity, and ecosystem maturity.
- SQL's home turf: structured, transactional, complex queries
  - Joins, aggregations, ACID — when correctness matters.
- NoSQL's home turf: massive scale, flexible schemas, simple access patterns
  - Horizontal scaling, eventual consistency, document/graph shapes.
- The right answer is usually "it depends" — and often "both"
  - Polyglot persistence is the modern default at scale.
[Visual suggestion: Two columns — "SQL strengths" (consistency, joins, mature tooling) vs "NoSQL strengths" (scale, schema flexibility, distributed). Bridge labeled "Polyglot persistence" at the bottom.]

### Slide 25: Schema Flexibility — SQL vs NoSQL
- SQL: schema-on-write
  - Define columns and types up front; every row must match.
- Adding a column requires migration
  - ALTER TABLE on a billion-row table can lock or take hours; tools like pt-online-schema-change help.
- NoSQL: schema-on-read (mostly)
  - Documents/columns can vary; the application interprets the shape.
- NoSQL wins for evolving data
  - Startups iterating on product ideas; user-generated content with unknown future fields.
- But schema-less is not free
  - You still need discipline — otherwise you get inconsistent, undocumented data.
[Visual suggestion: Two database icons. SQL: locked box with rigid columns. NoSQL: open box with flexible documents of varying shapes.]

### Slide 26: Scale — Vertical vs Horizontal
- SQL: vertical scaling first
  - Bigger box (more CPU, RAM, SSD). Simple, but ceiling and cost grow non-linearly.
- SQL horizontal scaling: read replicas, then sharding
  - Read replicas easy; sharding hard because of joins and cross-shard transactions.
- NoSQL: horizontal scaling by design
  - Distribute data across many cheap nodes; scale by adding more.
- NoSQL handles billions of rows and millions of QPS
  - Cassandra, DynamoDB, Bigtable run at petabyte scale routinely.
- Trade-off: distributed = more complexity (consistency, network failures)
  - You inherit CAP theorem realities (covered earlier in the deck).
[Visual suggestion: Left side — one giant beefy server (vertical). Right side — many small servers in a row (horizontal). Cost/scale curves below, with vertical hitting a ceiling and horizontal extending linearly.]

### Slide 27: Consistency — ACID vs BASE
- SQL: ACID (Atomicity, Consistency, Isolation, Durability)
  - Strong, immediate consistency — every read sees the latest committed write.
- NoSQL: BASE
  - Basically Available, Soft state, Eventual consistency.
- BA — Basically Available
  - The system always responds (maybe with stale data), preferring availability over correctness.
- S — Soft state
  - Replica state may be in flux; the system doesn't guarantee instantaneous synchronization.
- E — Eventual consistency
  - Given no new writes, all replicas converge to the same value eventually (milliseconds to seconds).
[Visual suggestion: Two boxes side by side. ACID box with a strict checkmark icon and "instant correctness". BASE box with three replica circles slowly converging via dotted lines, "eventual correctness".]

### Slide 28: Query Complexity — SQL Joins vs NoSQL Access Patterns
- SQL: declarative, optimizer-driven
  - You say what you want; the planner figures out the best execution.
- Joins, aggregations, subqueries, window functions are first-class
  - "Top 10 products by revenue per region this quarter" is a one-liner in SQL.
- NoSQL: model around access patterns
  - You design the schema for the queries you'll run; ad hoc queries are painful.
- Most NoSQL stores have no joins
  - You denormalize and embed, or join in application code.
- For analytics and BI: SQL still dominates
  - Even NoSQL ecosystems rely on SQL layers (Presto, Athena, Spark SQL) for analysis.
[Visual suggestion: Two side-by-side queries. Left: SQL with INNER JOINs across 4 tables. Right: NoSQL — same result requires 4 separate fetches in app code. Highlight the elegance vs verbosity contrast.]

### Slide 29: Real-World Hybrid — Twitter Uses Both
- Twitter (now X) is a textbook polyglot persistence example
  - Different workloads have radically different requirements.
- MySQL for the social graph and metadata
  - User accounts, follower relationships, settings — needs ACID and joins.
- Cassandra for the tweet timeline at massive scale
  - Hundreds of thousands of writes per second; eventual consistency acceptable for feeds.
- Redis for caching hot timelines
  - Sub-millisecond reads for active users' feeds, computed via fan-out-on-write.
- Manhattan (custom) for some real-time data
  - Internal NoSQL store optimized for low-latency reads at scale.
[Visual suggestion: Twitter architecture diagram — User-service (MySQL) -> Timeline-service (Cassandra) -> Cache-layer (Redis) -> User. Annotate each arrow with QPS / use case.]

### Slide 30: SQL vs NoSQL — Decision Framework
- Default to SQL if you're uncertain
  - Mature, well-understood, and Postgres scales further than most teams realize.
- Pick NoSQL when one of these is true
  - You need horizontal scale beyond a single node, schema is genuinely fluid, or access pattern is simple key lookup at extreme QPS.
- Match the NoSQL type to the data shape
  - Hierarchical -> document, time-series -> wide column, relationships -> graph, simple lookup -> key-value.
- Consider the team's expertise
  - A perfectly fitted database your team can't operate is worse than a slightly imperfect one they know.
- Re-evaluate as scale grows
  - Many systems start on Postgres and add specialized stores when bottlenecks appear.
[Visual suggestion: Decision tree starting at "Need ACID transactions?" branching to RDBMS or further questions about scale, schema, and access patterns, ending at specific database recommendations.]

### Slide 31: SQL vs NoSQL — Trade-offs Summary
- SQL pros: ACID, joins, mature tooling, declarative queries
  - Strong correctness guarantees and a battle-tested ecosystem.
- SQL cons: rigid schema, harder horizontal scaling
  - Migrations and sharding are real pain points at scale.
- NoSQL pros: horizontal scale, schema flexibility, specialized models
  - Designed for distributed environments from day one.
- NoSQL cons: weaker consistency, fewer joins, immature analytics tooling
  - You trade developer convenience for raw scale.
- Conclusion: pick based on workload, not ideology
  - The interview-perfect answer always weighs both sides explicitly.
[Visual suggestion: 2x2 trade-off matrix. Rows: Pros / Cons. Columns: SQL / NoSQL. Each cell with 2-3 short bullets and a small icon.]

---

## Part 4: Database Scaling Techniques

### Slide 32: Database Scaling — Concept Introduction
- A single database eventually hits a wall
  - CPU saturated, disk full, locks contended, network bottlenecked.
- Six core techniques to scale databases
  - Master-slave replication, master-master replication, federation, sharding, denormalization, SQL tuning.
- Each has different sweet spots
  - Some help reads, some help writes, some help both — at different complexity costs.
- Combine techniques as scale grows
  - Real systems use replication + sharding + caching + tuning together.
- Order matters: tune first, scale architecture last
  - Index a missing column before you shard.
[Visual suggestion: Stair-step diagram. Step 1: SQL tuning (cheap). Step 2: Caching. Step 3: Read replicas. Step 4: Federation. Step 5: Sharding. Step 6: NoSQL/specialized stores. Cost and complexity rise with each step.]

### Slide 33: Master-Slave Replication — Concept
- One master handles writes, one or more slaves replicate the data and serve reads
  - Asynchronous replication is the common default.
- Reads scale horizontally
  - Add more read replicas to handle more SELECT traffic.
- Writes still bottleneck on the master
  - Replication helps reads, not writes.
- Replica lag is real
  - A slave may be milliseconds-to-seconds behind master; reads can return stale data.
- Failover: a slave can be promoted to master if master fails
  - HA tools (Patroni, MHA, RDS automatic failover) automate the dance.
[Visual suggestion: One master DB at the top, two arrows down to two slave DBs. App writes go to master; reads are load-balanced across slaves. Show a "lag indicator" on the slave arrows.]

### Slide 34: Master-Slave Replication — Deep Dive and Use Cases
- Read-heavy workloads benefit massively
  - Blogs, analytics dashboards, product catalogs — 95% reads, 5% writes.
- Geographic read replicas reduce latency
  - Place replicas near users; writes still cross continents to reach master.
- Backup and analytics offload
  - Run heavy reporting queries on a replica without harming production performance.
- Trade-off: replica lag breaks "read your writes"
  - User updates profile, immediate read from replica may show old data — handle with sticky reads or read-from-master after write.
- Examples: MySQL replication, Postgres streaming replication, Aurora replicas
  - All major RDBMS support this natively.
[Visual suggestion: World map with 1 master in US-East and 4 replicas in EU, APAC, US-West, and SA. Arrows show replication; users in each region read from local replica.]

### Slide 35: Master-Master Replication — Concept
- Two (or more) masters each accept writes and replicate to each other
  - Both nodes are read/write; useful for HA across regions.
- Helps write availability and geographic write distribution
  - A failure of one master doesn't stop writes — the other keeps going.
- Conflict resolution is the hard part
  - If both masters write to the same row simultaneously, who wins?
- Common strategies: last-writer-wins, application-level CRDTs, primary-region routing
  - Each has correctness implications you must reason about explicitly.
- Examples: MySQL group replication, Postgres BDR, Galera Cluster
  - Often replaced by NoSQL multi-master systems (Cassandra, DynamoDB) at scale.
[Visual suggestion: Two database icons connected by a bidirectional arrow labeled "replication". App writes flow to either master. Highlight a "conflict" lightning bolt where both write the same row.]

### Slide 36: Replication — Trade-offs
- Master-slave: simple, scales reads, doesn't scale writes
  - The first scaling step; often sufficient for years.
- Master-master: scales writes regionally but adds conflict complexity
  - Use when geographic write availability matters more than perfect consistency.
- Both add operational burden
  - Monitoring lag, handling failover, ensuring replicas don't drift.
- Replication is not a backup
  - A bad DELETE replicates instantly to all slaves — keep real backups separately.
- Synchronous vs asynchronous replication
  - Sync = no data loss but slower writes; async = fast writes but possible loss on master crash.
[Visual suggestion: Comparison table — Master-Slave vs Master-Master. Rows: Read scaling, Write scaling, Complexity, Conflict handling. Mark with icons (check, half-check, X).]

### Slide 37: Federation — Concept Introduction
- Federation = functional partitioning by feature or domain
  - Split one big database into several smaller databases, each owning a feature area.
- Example: separate databases for users, products, and forums
  - Users-DB, Products-DB, Forums-DB — each independently scaled and operated.
- Each domain database is smaller and more focused
  - Smaller working set fits in memory; less lock contention; team ownership clear.
- Aligns with microservices decomposition
  - Each service owns its own database (database-per-service pattern).
- Trade-off: cross-domain joins now require application-level orchestration
  - You can't `JOIN users.posts ON forums.threads` anymore.
[Visual suggestion: Single monolith DB on the left labeled "Before". Three smaller DBs on the right labeled Users, Products, Forums — each connected to its own service. Arrow labeled "Federation" between them.]

### Slide 38: Federation — Deep Dive and Trade-offs
- Reduces read/write traffic per database
  - Each box only handles one domain's load; capacity grows with each split.
- Smaller databases = simpler indexes, faster vacuum/maintenance
  - Operational sanity improves dramatically.
- Independent scaling and tech choices
  - Users on Postgres, Products on Postgres+ElasticSearch, Forums on MongoDB — all valid.
- Cross-domain queries become application logic
  - Aggregating data from multiple DBs is your job, not the database's.
- Distributed transactions become hard
  - Cross-DB writes need sagas, outbox patterns, or event-driven consistency.
[Visual suggestion: Microservice architecture — each service has its own DB icon, an event bus connects them for cross-domain workflows.]

### Slide 39: Sharding — Concept Introduction
- Sharding = horizontal partitioning of a single dataset across many databases
  - Split rows of one logical table across multiple physical databases (shards).
- Analogy: splitting a phone book by name
  - Shard 1 holds names A–M, Shard 2 holds names N–Z. Lookup by name routes to the right shard.
- Each shard is an independent database with the same schema
  - All shards together represent the full dataset.
- Scales reads AND writes
  - Unlike replication, every shard handles its own write load.
- The hardest mainstream scaling technique
  - Cross-shard joins, transactions, and rebalancing are non-trivial.
[Visual suggestion: A phone book split into two halves labeled "A–M" and "N–Z", each on its own database server. A "router" component on top decides which shard to query.]

### Slide 40: Sharding — Strategies
- Range-based sharding
  - Partition by key range (user_id 1–1M on shard 1, 1M–2M on shard 2). Simple but prone to hotspots.
- Hash-based sharding
  - Apply a hash function to the key; modulo over shard count distributes data evenly.
- Directory-based sharding
  - A lookup service maps keys to shards; flexible but adds a hop.
- Geo-based sharding
  - Shard by user region (EU users in EU shard); reduces latency, supports compliance (GDPR).
- Pick the shard key carefully
  - The shard key drives routing, balance, and query patterns — bad keys cause endless pain.
[Visual suggestion: Four small diagrams in a 2x2 grid showing each strategy with arrows from a "key" to a "shard" using different routing logic.]

### Slide 41: Consistent Hashing for Sharding
- Naive hash sharding: `shard = hash(key) % N`
  - Works, but adding or removing a shard remaps almost every key (massive data movement).
- Consistent hashing: keys and nodes map onto a virtual ring
  - Each key is owned by the next node clockwise on the ring.
- Adding a node only moves keys from the neighbor
  - Roughly 1/N of data moves, instead of nearly everything.
- Virtual nodes (vnodes) smooth load distribution
  - Each physical node represents many points on the ring, evening out hot spots.
- Used in DynamoDB, Cassandra, Riak, and many CDNs
  - The same algorithm powers cache layers and load balancers too.
[Visual suggestion: Circular ring diagram with 4 nodes (N1, N2, N3, N4) placed around it and several keys mapped to the next clockwise node. Show what happens when N5 is added — only nearby keys move.]

### Slide 42: Sharding — Trade-offs
- Pros: near-linear horizontal scaling for both reads and writes
  - The path to internet scale.
- Cons: cross-shard joins are painful or impossible
  - You denormalize, fan-out queries, or maintain materialized views.
- Cons: distributed transactions are hard
  - Two-phase commit is slow and fragile; sagas are the modern alternative.
- Cons: re-sharding is operationally complex
  - Splitting a hot shard while the system is live takes careful tooling.
- Hot shard problem: bad keys create skew
  - One celebrity user's tweets all hit one shard — 10x the load.
[Visual suggestion: Pros/cons split panel. Bottom shows a "hot shard" warning — one shard glowing red while others are blue, illustrating skew.]

### Slide 43: Denormalization — Concept
- Denormalization = intentionally duplicating data to speed up reads
  - The opposite of normalization; trade write/storage cost for read simplicity.
- Joins are expensive at scale
  - Pre-compute the join result and store it where it'll be read.
- Common in NoSQL and read-heavy SQL systems
  - Cassandra schemas are designed denormalized from day one.
- Example: store user_name on every order row
  - Avoid joining Orders to Users on every order list query.
- Trade-off: writes must update multiple places
  - When the user renames themselves, you update many rows — eventual consistency in app logic.
[Visual suggestion: Two diagrams. Left: normalized — Orders joins Users. Right: denormalized — Orders has user_name embedded; arrow shows a write to Users now triggers updates to many Orders rows.]

### Slide 44: Denormalization — Use Cases and Trade-offs
- Activity feeds (fan-out-on-write)
  - When someone tweets, copy the tweet into each follower's timeline at write time.
- Materialized views and read models in CQRS
  - Pre-built read shapes that match what the UI needs.
- Aggregations cached as columns
  - "post_count" on user row, updated on insert/delete, avoids COUNT(*) at read time.
- Trade-off: write amplification
  - One logical write becomes many physical writes; storage and write throughput cost rise.
- Trade-off: data drift if updates miss a copy
  - You need disciplined update paths or background reconciliation.
[Visual suggestion: Fan-out-on-write diagram. One tweet from a celebrity user fans out into N follower-timeline rows in parallel. Highlight the amplification factor.]

### Slide 45: SQL Tuning — Concept Introduction
- Tuning is the cheapest scaling technique
  - Often a missing index gives 100x speedup; do this before any sharding talk.
- Three main levers
  - Indexes, query rewriting, and schema design.
- Use EXPLAIN ANALYZE to find slow queries
  - The plan shows what the database actually does, not what you think it does.
- Cache plans and parameters
  - Prepared statements avoid replanning on each request.
- Monitor with slow query logs and APM
  - You can't tune what you don't measure.
[Visual suggestion: Toolbox illustration containing labeled tools — "EXPLAIN", "ANALYZE", "Indexes", "Slow Query Log", "Prepared Statements".]

### Slide 46: SQL Tuning — Practical Techniques
- Add indexes that match WHERE, JOIN, and ORDER BY clauses
  - Composite indexes for multi-column predicates; covering indexes to avoid table lookups.
- Avoid N+1 queries from ORMs
  - Eager-load relations; one well-formed JOIN beats 1000 tiny SELECTs.
- Rewrite non-sargable predicates
  - `WHERE YEAR(created_at) = 2026` blocks index use; `WHERE created_at >= '2026-01-01' AND < '2027-01-01'` doesn't.
- Use LIMIT and pagination correctly
  - Keyset pagination (WHERE id > last_id) beats OFFSET for deep pages.
- Vacuum, analyze, and update statistics regularly
  - Stale stats lead the planner astray.
[Visual suggestion: Before/after EXPLAIN comparison. Before: Seq Scan, 1.2s. After: Index Scan, 8ms. Highlight the change in green.]

### Slide 47: Database Scaling — Trade-offs Summary
- Replication: scales reads, simple to operate
  - First step for most systems.
- Federation: cleaner ownership, smaller working sets
  - Aligns with microservices; cross-domain queries get harder.
- Sharding: scales reads and writes
  - Highest complexity, hardest to get right.
- Denormalization: fast reads at the cost of write complexity
  - Default in NoSQL; selective in SQL.
- SQL tuning: highest ROI per hour of effort
  - Always do this first; it often delays the need for harder steps.
[Visual suggestion: ROI vs Complexity scatter plot. SQL tuning: low complexity, high ROI. Replication: medium both. Sharding: high complexity, high ROI but slow to realize.]

---

## Section Wrap-Up

### Slide 48: Key Takeaways
- RDBMS = ACID, structured, joins, mature
  - Default choice for most transactional workloads. Postgres scales further than people think.
- NoSQL is a family with four main types
  - Key-Value (Redis), Document (MongoDB), Wide Column (Cassandra), Graph (Neo4j) — pick by data shape.
- ACID vs BASE is the consistency trade-off
  - Strong consistency vs eventual consistency; pick what your business actually requires.
- Sharding = splitting data horizontally; federation = splitting by domain
  - Different tools for different problems; both increase complexity.
- Real systems are polyglot
  - Twitter, Netflix, Amazon use 5–10 different databases together by design.
[Visual suggestion: One-page cheat sheet — three columns: "Choose RDBMS when", "Choose NoSQL when", "Scale by". Each with 4 bullets.]

### Slide 49: Interview Tips
- Always ask about scale, schema stability, and consistency before recommending a database
  - "How many writes per second? How does the schema evolve? Is stale read OK?" wins points.
- Define ACID and BASE precisely if you mention them
  - Especially Isolation and Eventual consistency — interviewers probe these.
- Mention specific examples: Postgres, MongoDB, Cassandra, Redis, Neo4j
  - Concrete examples beat vague references.
- For sharding, explain the shard key and consistent hashing
  - These are the most common follow-up questions.
- Discuss trade-offs explicitly — never claim one option is "best"
  - "I'd start with Postgres; if writes exceed 50k/s I'd shard or move hot tables to Cassandra."
[Visual suggestion: Speech-bubble graphic — interviewer asks "Which database?", candidate replies with a structured framework: "Depends on (1) scale, (2) schema, (3) consistency, (4) team".]

### Slide 50: Common Pitfalls
- Choosing NoSQL "for scale" before you have scale
  - Most products fail from lack of users, not too many. Postgres is fine for most startups.
- Forgetting to define ACID precisely
  - Mixing up Consistency (constraint integrity) with CAP-Consistency (linearizability) is a classic stumble.
- Ignoring replica lag in read-after-write scenarios
  - "User updates profile, sees old data" is a top user-facing bug.
- Sharding too early or with a bad shard key
  - Reshardings are expensive; pick a key with high cardinality and even access.
- Over-indexing tables
  - Every index slows writes; benchmark before adding.
- Treating replication as a backup
  - It isn't. Bad writes (DELETE without WHERE) replicate instantly. Keep point-in-time backups separately.
[Visual suggestion: "Pitfall warning" board with 6 stop-sign icons, each labeled with a pitfall in red text and a one-line corrective tip below in green.]

### Slide 51: Section Closing — Mental Models
- "Pick the database that matches your access patterns"
  - Not the trendiest, not the simplest, the one that fits your reads and writes.
- "Tune before you scale, scale before you shard"
  - Cheapest fix first, most expensive last.
- "Polyglot persistence is normal at scale"
  - Don't hunt for one database to rule them all — there isn't one.
- "Consistency is a spectrum, not a switch"
  - From linearizable to eventual; pick the weakest level your business tolerates.
- Up next: Caching — the secret weapon that makes most databases survivable
  - We'll cover Redis, Memcached, CDN caches, and cache invalidation strategies.
[Visual suggestion: Mountain summit graphic — climber at the top labeled "scale" with checkpoints below (tune, replicate, federate, shard, denormalize). A signpost ahead points to "Section 7: Caching".]
