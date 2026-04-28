## Section 8: Asynchronism and Message Queues

### Slide 1: Section Overview — Why Asynchronism Matters
- Modern systems must stay responsive even when work is slow
  - Users expect sub-second responses; backend work (email, ML, billing) often takes seconds to minutes
- Async lets us decouple "accepting work" from "doing work"
  - The web tier acknowledges quickly, while heavy lifting happens elsewhere
- Message queues are the connective tissue of distributed systems
  - They smooth out traffic spikes, isolate failures, and enable horizontal scaling
- This section covers queues, task systems, streaming, backpressure, and orchestration
  - From SQS-style queues to Kafka-scale streaming to Temporal-style workflows
[Visual suggestion: Split-screen — left: synchronous "user waits 30s for email confirmation"; right: asynchronous "user sees instant 'Order placed' while worker handles email in background"]

---

### Slide 2: Synchronous vs Asynchronous — Concept Introduction
- Synchronous = caller blocks until the callee returns a response
  - Like phoning someone and staying on the line until they answer your question
- Asynchronous = caller hands off work and continues immediately
  - Like dropping a letter in a mailbox; you don't wait for the recipient to read it
- Sync is simpler to reason about; async is more scalable under load
  - Sync ties up threads/connections; async frees them to serve more requests
- The choice is per-operation, not per-system
  - A single API can do sync DB reads but async email sending
[Visual suggestion: Two timelines — "Sync: Request → [wait] → Response" vs "Async: Request → Ack ↓ ... Worker processes later"]

---

### Slide 3: Synchronous Processing — Deep Explanation
- Caller thread is blocked end-to-end
  - HTTP connection, DB connection, memory, and CPU are all held hostage
- Failures cascade immediately to the user
  - If the payment gateway is down, the user sees a 500 right now
- Latency = sum of all downstream latencies
  - p99 of your API ≥ p99 of every dependency you call serially
- Easier to debug: stack traces show the full call path
  - Great for CRUD APIs, simple reads, and operations under ~200ms
- Bad fit for slow, flaky, or expensive operations
  - Email, video transcoding, third-party APIs, ML inference
[Visual suggestion: Stack of bars showing "API latency = auth (50ms) + DB (100ms) + payment (2s) + email (3s) = 5.15s response time"]

---

### Slide 4: Asynchronous Processing — Deep Explanation
- Producer enqueues a task and returns to the caller
  - Caller sees a 202 Accepted with a tracking ID, not a 200 OK with the final result
- A separate worker pool consumes and processes tasks
  - Workers scale independently from web servers based on queue depth
- Status is tracked out-of-band
  - Polling, webhooks, WebSockets, or push notifications inform the user when done
- Improves availability: producer survives consumer outages
  - If the email service dies, orders still complete; emails go out when it recovers
- Adds complexity: eventual consistency, retries, idempotency, dead letters
  - You trade a simple call stack for a distributed state machine
[Visual suggestion: Diagram — User → API (returns 202 + jobId) → Queue → Worker → DB/Notification, with dotted "status check" line from User to API]

---

### Slide 5: Async Example — Uber Ride Request
- Rider taps "Request Ride" — must feel instant
  - Sync work: validate user, check payment method, create ride record (~100ms)
- Async work fanned out to queues
  - Driver matching, ETA calculation, surge pricing logging, fraud scoring, push notifications
- Each downstream system scales independently
  - Matching service runs on GPU-backed workers; logging runs on cheap commodity boxes
- If notification service is down, the ride still happens
  - The push is retried from the queue when notifications recover
[Visual suggestion: Uber app screen "Finding driver..." with branching arrows to 5 background services, each with its own queue]

---

### Slide 6: Sync vs Async — Trade-offs
- Sync wins on: simplicity, immediate feedback, strong consistency
  - One request, one response, one transaction — easy mental model
- Async wins on: throughput, resilience, decoupling, smoothing spikes
  - Producers don't care if consumers are slow, scaling, or briefly down
- Async costs: operational complexity, harder debugging, eventual consistency
  - You now own a queue, retry logic, DLQs, idempotency keys, and observability
- Rule of thumb: async anything that is slow (>1s), flaky, or non-critical-path
  - Email, analytics, search indexing, thumbnails, webhooks
[Visual suggestion: Comparison table with rows Latency / Throughput / Complexity / Failure Isolation / Consistency, columns Sync / Async]

---

### Slide 7: Message Queues — Concept Introduction
- A message queue is a buffer between producers and consumers
  - Producers write messages; consumers read messages; the queue durably holds them in between
- Analogy: a post office mailbox
  - Senders drop letters anytime; recipients pick up when ready; the box holds mail safely in between
- Messages are typically small payloads (JSON, Protobuf, Avro)
  - Often a reference + metadata, not the full data — e.g., "process file s3://bucket/key"
- Decouples in time, space, and rate
  - Producer and consumer don't need to be online together, on the same host, or running at the same speed
[Visual suggestion: Three boxes — Producer(s) → [Queue: ▢▢▢▢▢] → Consumer(s), with arrows showing one-way message flow]

---

### Slide 8: Message Queues — Core Benefits
- Decoupling: services evolve independently
  - Add new consumers without touching producers; swap implementations behind the queue
- Buffering: absorbs traffic spikes
  - Black Friday surge fills the queue; consumers drain it at their own pace instead of crashing
- Reliability: messages persist through restarts and failures
  - Durable queues replicate to disk; in-flight work isn't lost when a worker dies
- Retry & redelivery: built-in fault tolerance
  - Failed messages reappear after a visibility timeout, no custom retry code needed
- Fan-out: one event, many consumers
  - "OrderPlaced" can simultaneously trigger billing, shipping, analytics, and email services
[Visual suggestion: Funnel diagram — many spiky producer arrows on top → flat queue line → smooth consumer arrows on bottom (rate smoothing)]

---

### Slide 9: Dead Letter Queues (DLQ) — Deep Explanation
- A DLQ is a secondary queue for messages that repeatedly fail
  - After N retries (typically 3–10), the broker moves the message to the DLQ instead of redelivering forever
- Prevents poison messages from blocking the queue
  - One malformed JSON shouldn't stall thousands of healthy orders behind it
- DLQ contents are inspected by humans or replay tools
  - Common causes: bad data, schema drift, downstream bugs, missing dependencies
- Always set DLQs in production
  - Without one, retries pile up forever, queue grows unbounded, and observability becomes a nightmare
- Monitor DLQ depth as a critical alert
  - DLQ growth = silent business failures; treat it like a P1 page
[Visual suggestion: Main queue → consumer (red X failure 3x) → arrow to DLQ box; separate "Ops Engineer" inspecting DLQ]

---

### Slide 10: Delivery Semantics — At-most/At-least/Exactly-once
- At-most-once: message delivered 0 or 1 times
  - Fast and simple, but messages can be lost; OK for metrics, not for payments
- At-least-once: message delivered 1 or more times (duplicates possible)
  - The default for most queues (SQS, RabbitMQ); requires idempotent consumers
- Exactly-once: message processed exactly 1 time end-to-end
  - The "holy grail"; truly hard in distributed systems; usually approximated via idempotency + dedup IDs
- Kafka offers "exactly-once semantics" within Kafka transactions
  - Real exactly-once across external systems (e.g., DB + email) needs idempotency keys
- Practical advice: design consumers to be idempotent
  - Use unique message IDs, upserts, and dedup tables; assume at-least-once
[Visual suggestion: Three timelines showing same message — at-most-once (lost), at-least-once (delivered twice), exactly-once (delivered once)]

---

### Slide 11: Message Ordering Guarantees
- FIFO queues preserve order within a partition/group
  - SQS FIFO, Kafka per-partition, RabbitMQ per-queue: messages exit in the same order they entered
- Standard (non-FIFO) queues maximize throughput, no ordering guarantee
  - SQS Standard can deliver out-of-order; trade strict order for massive scale
- Global ordering across partitions is usually impossible at scale
  - You can have order OR parallelism; pick one per use case
- Use a partition key to keep related messages ordered together
  - e.g., partition by userId so all events for one user are processed in order
- Many systems don't actually need strict order
  - Use timestamps + idempotency to handle out-of-order events gracefully
[Visual suggestion: Two queues side-by-side — FIFO (1,2,3,4 in/out) vs Standard (1,2,3,4 in / 2,1,4,3 out)]

---

### Slide 12: Message Queue Examples — Real Systems
- RabbitMQ: mature, AMQP-based, flexible routing
  - Strong for complex routing topologies (direct, topic, fanout exchanges); used by Reddit, Instagram early days
- Amazon SQS: fully managed, infinite scale, pay-per-message
  - Used internally across Amazon for decoupling services; FIFO and Standard variants
- ActiveMQ / Artemis: JMS-compliant, Java ecosystem staple
  - Common in enterprise Java systems; supports topics and queues
- Redis Streams / Lists: lightweight queueing inside Redis
  - Good for moderate scale; simple ops if you already run Redis
- NATS / NATS JetStream: high-perf, cloud-native
  - Sub-millisecond latency; popular in service mesh and IoT scenarios
[Visual suggestion: Logos grid (RabbitMQ, SQS, ActiveMQ, Redis, NATS) with one-line descriptors and "best for" tags]

---

### Slide 13: Message Queue Diagram — Order Processing Flow
- Producer: checkout service writes "OrderPlaced" message
  - Includes orderId, userId, items, amount, timestamp
- Queue: durable, replicated, partitioned by orderId
  - Persists message even if all consumers are down
- Consumers: billing, inventory, notification workers
  - Each consumer group processes independently and at its own rate
- ACK / NACK feedback loop
  - Successful processing → ACK removes message; failure → NACK triggers retry, eventually DLQ
[Visual suggestion: Flow — Checkout Service → "OrderPlaced" → [Queue with 3 messages] → 3 parallel consumer groups (Billing/Inventory/Email), each with ACK arrows back]

---

### Slide 14: Message Queues — Trade-offs
- Pro: massive decoupling, resilience, elastic scaling
  - Producers and consumers evolve, fail, and scale independently
- Con: eventual consistency
  - Data is "in flight" — readers may see stale state until consumers catch up
- Con: operational overhead
  - Monitoring, DLQs, replay tooling, schema management, on-call rotations
- Con: harder debugging
  - Distributed traces across queue boundaries require correlation IDs and tracing tools (OpenTelemetry, Jaeger)
- Watch for: queue depth growth, consumer lag, redelivery rate, DLQ size
  - These are your golden signals for queue-based systems
[Visual suggestion: Pros/Cons split with green checkmarks (decoupling, scaling) and red warnings (consistency, ops cost)]

---

### Slide 15: Task / Job Queues — Concept Introduction
- Task queues are message queues specialized for "units of work"
  - The message represents a function to call, not just an event that happened
- Difference from generic message queues
  - Task queue knows about retries, scheduling, priorities, results, and worker pools out of the box
- Workers pull tasks and execute code
  - "Send email to bob@x.com" → worker invokes send_email() with those args
- Often paired with a result backend
  - Stores task status (PENDING, STARTED, SUCCESS, FAILURE) and return value for later lookup
[Visual suggestion: Code snippet showing `send_email.delay(user_id=123)` on left, worker process on right pulling and executing the function]

---

### Slide 16: Task Queues — Common Use Cases
- Image / video processing
  - Resize, transcode, watermark; CPU/GPU-heavy work offloaded from web servers
- Email & SMS delivery
  - Third-party APIs are slow and flaky; never block a request on Mailgun/Twilio
- Report & PDF generation
  - 30-second SQL queries and PDF rendering happen async; user gets an email when ready
- ML inference & training jobs
  - Long-running model runs queued and dispatched to GPU workers
- Periodic / scheduled tasks
  - Nightly cleanup, weekly digests, hourly reindexing handled by the same workers
[Visual suggestion: Icon grid — camera (image), envelope (email), document (report), brain (ML), clock (scheduled)]

---

### Slide 17: Task Queue Workers — Pull-Based Processing
- Workers poll the queue for tasks
  - "Anything for me?" — pull model gives natural backpressure
- Concurrency tuned per worker
  - N processes × M threads/coroutines per process = total parallelism
- Acknowledge after success, requeue or DLQ on failure
  - Tasks that crash mid-flight are re-delivered to another worker
- Workers are stateless and horizontally scalable
  - Add more workers when the queue backs up; remove them when idle
- Long-running tasks need heartbeats
  - Otherwise the broker thinks the worker died and re-delivers, causing duplicates
[Visual suggestion: Queue at top, 4 worker boxes pulling down arrows; one worker shows "heartbeat ❤" while processing a long task]

---

### Slide 18: Priority Queues
- Not all tasks are equal — some need to jump the line
  - Paid-tier customer reports vs free-tier batch jobs
- Implementation 1: separate queues per priority
  - Workers always check `high` before `medium` before `low`; simple and effective
- Implementation 2: priority field on messages
  - Broker (e.g., RabbitMQ priority queues) reorders internally; can starve low-priority tasks
- Watch out for starvation
  - High-priority floods can permanently block low-priority work; use weighted fair scheduling
- Use case: real-time vs batch
  - Interactive ML inference high-priority, nightly retraining low-priority on the same workers
[Visual suggestion: Three lanes labeled HIGH / MED / LOW feeding into shared worker pool, with worker checking lanes top-down]

---

### Slide 19: Task Queue Examples — Celery, Sidekiq, Bull
- Celery (Python): the de-facto Python task queue
  - Used by Instagram, Mozilla; supports RabbitMQ/Redis brokers, scheduled tasks, chains, groups, chords
- Sidekiq (Ruby): Redis-backed, high-performance
  - Default in Rails apps; Shopify processes billions of jobs/day on Sidekiq
- Bull / BullMQ (Node.js): Redis-backed, modern API
  - Used by NestJS apps; supports priorities, rate limiting, repeatable jobs
- Resque (Ruby), RQ (Python), Hangfire (.NET)
  - Each ecosystem has its own; pick the one with the best community in your language
- Cloud-native: AWS Step Functions + Lambda, GCP Cloud Tasks
  - Managed task execution without running your own workers
[Visual suggestion: Logo grid by language ecosystem — Python (Celery), Ruby (Sidekiq), Node (BullMQ), .NET (Hangfire)]

---

### Slide 20: Task Queue Example — Email Delivery at Scale
- User signs up → sync code creates account, returns 200
  - Total sync latency: ~80ms
- Async: `send_welcome_email.delay(user_id)` enqueued in Redis
  - Returns instantly; web server moves on
- Email worker picks up task, calls SendGrid API
  - Takes 800ms–3s; if SendGrid is slow, only the worker waits, not the user
- On failure: exponential backoff retries (1m, 5m, 30m, 2h)
  - Transient SendGrid 5xx errors recover automatically
- After max retries: task → DLQ, ops alerted
  - User experience never degraded, even during a 4-hour SendGrid outage
[Visual suggestion: Sequence diagram — User → API (200 OK in 80ms), API → Redis Queue, Worker → SendGrid (with retry loop)]

---

### Slide 21: Task Queues — Trade-offs
- Pro: massively improves perceived latency
  - User-facing requests stay fast even when downstream is slow
- Pro: built-in retry, scheduling, monitoring
  - Saves writing custom orchestration code per use case
- Con: idempotency burden on the developer
  - Tasks may run twice; "send email" running twice = bad user experience
- Con: state visibility — "did it run?"
  - Need result backends, dashboards (Flower for Celery, Sidekiq Web UI), alerting
- Con: version skew between producers and workers
  - Deploying new task signatures while old workers run = pickle/serialization errors
[Visual suggestion: Two-column trade-off table with concrete examples in each cell]

---

### Slide 22: Pub/Sub & Event Streaming — Concept Introduction
- Point-to-point queue: one message, one consumer (load balancing)
  - Each task processed by exactly one worker
- Pub/Sub: one message, many subscribers (broadcast)
  - Producer publishes once; every subscribed consumer gets its own copy
- Event streaming: durable, replayable log of events
  - Consumers can rewind to any point in history; events are facts, not commands
- Mental shift: events vs commands
  - Command "ChargeCustomer" → one handler. Event "OrderPlaced" → many independent reactions
[Visual suggestion: Two diagrams — left "Queue: 1 msg → 1 of N consumers", right "Pub/Sub: 1 msg → all N subscribers"]

---

### Slide 23: Event Sourcing — The Concept
- Store every state change as an immutable event
  - Instead of `account.balance = 100`, store `Deposited(amount=100)` and `Withdrew(amount=20)`
- Current state = replay of all past events
  - Audit trail, time travel, and debugging come for free
- Pairs naturally with Kafka-style event logs
  - The log IS the source of truth; databases become materialized views
- Enables CQRS (Command Query Responsibility Segregation)
  - Write side appends events; read side projects events into query-optimized views
- Real example: banking ledgers, Git, blockchain
  - All are append-only event logs by design
[Visual suggestion: Bank account view — left "Events: +100, -20, +50" / right "Materialized State: balance=130"]

---

### Slide 24: Apache Kafka — Architecture Deep Dive
- Topic: a named stream of events (e.g., `orders`, `clicks`, `page_views`)
  - Logical category; producers write to topics, consumers read from topics
- Partition: a topic split into ordered, append-only logs
  - Each partition is a separate file on disk; partitions = unit of parallelism
- Offset: monotonically increasing ID per partition
  - Consumers track their own offset; "I've read up to message 4,521"
- Consumer group: a set of consumers sharing the work
  - Kafka assigns partitions to consumers in the group; one partition → one consumer in a group
- Brokers + replication: distributed, fault-tolerant
  - Each partition replicated across N brokers (typically 3); leader handles writes, followers stay in sync
[Visual suggestion: Topic "orders" with 3 partitions, each showing ordered messages with offset numbers, and 3 consumers in a group each reading a different partition]

---

### Slide 25: Why Kafka is Durable and Replayable
- Append-only commit log on disk
  - Sequential writes are fast; old messages aren't deleted on consume
- Configurable retention (time or size)
  - "Keep 7 days" or "keep 1TB"; consumers can re-read anytime within retention
- Replication for fault tolerance
  - Replication factor 3 means any 2 broker failures are survivable
- Consumers track their own offsets (in `__consumer_offsets` topic)
  - Reset to earliest, latest, or arbitrary timestamp — replay last hour of events for free
- This is why Kafka unlocks new architectures
  - Event sourcing, change data capture, stream processing, log aggregation all ride on these properties
[Visual suggestion: Disk-shaped commit log with messages 0–9, replicated across 3 brokers; consumer arrow pointing to offset 6 with note "can reset to 0 anytime"]

---

### Slide 26: Kafka Use Cases — Real Examples
- LinkedIn: Kafka was born here for activity feeds & metrics
  - Now handles 7+ trillion messages/day; powers feed, search indexing, monitoring
- Netflix: real-time analytics, recommendation pipelines
  - 10+ trillion events/day flow through Kafka into Flink and Spark jobs
- Uber: trip events, dynamic pricing, fraud detection
  - Surge pricing runs on Kafka streams of recent ride requests
- Change Data Capture (CDC) with Debezium
  - Stream every DB change into Kafka; downstream services build their own views
- Log aggregation (replacing Scribe/Flume)
  - All app logs flow through Kafka into Elasticsearch / S3 / Snowflake
[Visual suggestion: World map / company logos showing Kafka deployments at scale, with throughput numbers]

---

### Slide 27: Pub/Sub Alternatives — Pulsar, Kinesis, Google Pub/Sub
- Apache Pulsar: tiered storage, multi-tenancy, geo-replication
  - Separates compute (brokers) from storage (BookKeeper); good for very long retention
- AWS Kinesis Data Streams: managed, Kafka-like
  - Tightly integrated with AWS (Lambda triggers, Firehose to S3); per-shard pricing
- Google Cloud Pub/Sub: globally-distributed, push or pull
  - Scales to millions of msg/s; supports push to HTTP endpoints
- AWS SNS: pure pub/sub (no durable log)
  - Fan-out to SQS, Lambda, HTTP, email; not for replay
- Azure Event Hubs: Microsoft's Kafka equivalent
  - Kafka-protocol-compatible; integrates with Azure Stream Analytics
[Visual suggestion: Comparison matrix — features (durability, retention, throughput, managed) across Kafka / Pulsar / Kinesis / Pub/Sub]

---

### Slide 28: Pub/Sub Diagram — News Feed Fan-Out
- Producer: a user posts a tweet
  - Single write to `tweets` topic with userId, content, timestamp
- Topic: durable, partitioned by userId
  - One partition per user "shard"; ordered per user
- Consumers (independent groups)
  - Search indexer, ML moderation, follower fan-out, analytics — each at its own pace
- No coupling between subscribers
  - Adding "fraud detection" later = new consumer group, no producer change
[Visual suggestion: Central Kafka topic, 1 producer arrow in, 4 consumer group arrows out, each labeled with its purpose]

---

### Slide 29: Pub/Sub & Streaming — Trade-offs
- Pro: ultimate decoupling and replayability
  - Add new consumers years later; rebuild views from scratch using historical events
- Pro: handles massive scale (millions of msg/s)
  - Partitioning is the secret sauce
- Con: operational complexity
  - ZooKeeper/KRaft, brokers, partitions, ISR, rebalancing — Kafka has a real learning curve
- Con: ordering only within a partition
  - Need careful partition key choice to maintain useful ordering
- Con: schema evolution is critical
  - Use Avro/Protobuf with a Schema Registry; breaking changes cascade to all consumers
[Visual suggestion: Iceberg metaphor — visible "easy producer/consumer API" above water, hidden "ops, partitioning, schemas" below]

---

### Slide 30: Backpressure — Concept Introduction
- Backpressure = a slow consumer signaling "stop sending so fast"
  - When work arrives faster than it can be processed, something must give
- Without backpressure, queues grow unbounded
  - Memory blows up, latency spikes, eventually the whole system crashes
- The danger: cascading failures
  - Producer hammers a slow consumer → consumer dies → producer's queue fills → producer dies
- Goal: graceful degradation, not collapse
  - Better to drop or delay some work than to fail completely
[Visual suggestion: Water analogy — fire hose (producer) into a small drain (consumer); without overflow valve, everything floods]

---

### Slide 31: Backpressure — Solutions
- Bounded queues with rejection
  - Queue full → reject new messages with 503; producer must back off
- Rate limiting at the producer
  - Token bucket or leaky bucket caps requests/second per client
- Load shedding: drop non-critical work
  - Under stress, skip analytics events; keep payments flowing
- Circuit breakers: fail fast when downstream is unhealthy
  - Trip after N failures, return cached/default response, retry after cooldown (Hystrix, resilience4j)
- Adaptive concurrency: dynamically adjust parallelism
  - Use latency / error signals to scale workers up or down (Netflix concurrency-limits)
- Pull-based consumption naturally provides backpressure
  - Consumers pull only what they can handle; producer queue absorbs the rest
[Visual suggestion: Five icons — bounded queue, rate limiter, load shedder, circuit breaker, autoscaler — feeding into a "stable system" core]

---

### Slide 32: Backpressure Example — Stripe Webhooks
- Stripe sends webhooks for every payment event
  - Spikes during sales: thousands of events/second hitting your endpoint
- Naive: process inline → endpoint timeouts → Stripe retries → makes it worse
  - Classic positive feedback loop into total failure
- Better: webhook handler does only "verify + enqueue"
  - Returns 200 in <100ms; heavy work happens async
- Best: bounded internal queue + alert when nearing capacity
  - If queue >80%, scale workers up; if >95%, return 429 to Stripe (which retries with backoff)
- The queue acts as a shock absorber for traffic spikes
  - 10x burst becomes a 30-minute drain instead of an outage
[Visual suggestion: Time-series graph of webhook arrivals (spiky) vs queue drain (smooth), with "auto-scale" annotation at threshold]

---

### Slide 33: Backpressure — Trade-offs
- Pro: prevents catastrophic cascading failures
  - The single biggest stability win in distributed systems
- Pro: makes capacity planning explicit
  - You know your limits because you defined them
- Con: requires choosing what to drop
  - Business decision: which work is sheddable vs critical?
- Con: clients must handle 429s and retries
  - Not all clients are well-behaved; mobile apps especially
- Without it, autoscaling alone won't save you
  - You can't scale faster than failures propagate; backpressure is the brake pedal
[Visual suggestion: Two timelines — "no backpressure: gradual slowdown → cliff" vs "with backpressure: gentle plateau"]

---

### Slide 34: Workflow Orchestration — When Queues Aren't Enough
- Simple async fits "fire and forget" or single-step jobs
  - Send email, resize image, charge card
- Multi-step workflows need orchestration
  - "Place order → reserve inventory → charge card → ship → email confirmation → handle returns"
- Each step may fail, retry, or compensate
  - If charge succeeds but inventory reservation fails, you must refund (saga pattern)
- Long-running, stateful processes
  - Hours, days, or months between steps (e.g., subscription renewals, multi-day approval flows)
- Visibility & auditability requirements
  - "Where is this order?" needs a single answer, not 5 logs across 5 services
[Visual suggestion: DAG diagram — order workflow with branching, retries, and compensation arrows, contrasted with a flat queue]

---

### Slide 35: Workflow Orchestration Tools
- AWS Step Functions: managed state machines (JSON / ASL)
  - Tight AWS integration; visual workflow editor; great for serverless workflows
- Apache Airflow: Python DAGs, batch / data pipelines
  - Originally Airbnb; the standard for ETL & data engineering
- Temporal: code-as-workflow, durable execution
  - Write workflows like normal code; Temporal handles retries, state, history; used by Uber, Snap, Datadog
- Cadence (Uber's predecessor to Temporal): similar model
  - Same authors; Temporal is the actively-developed fork
- Argo Workflows: Kubernetes-native, container per step
  - Strong fit for ML pipelines and Kubernetes-heavy shops
[Visual suggestion: 5-tile gallery with tool logo, language, sweet spot — Step Functions / Airflow / Temporal / Argo / Prefect]

---

### Slide 36: Orchestration Example — Uber Trip Lifecycle
- Workflow steps: request → match → pickup → ride → drop-off → fare → receipt → rating
  - Spans 30+ minutes; each step is its own service
- Built on Temporal/Cadence at Uber
  - Workflow code resembles a normal program; durability and retries handled by the platform
- Failure handling: retry transient errors, compensate on permanent failures
  - Driver cancels mid-ride? Refund partial fare, rematch rider, notify both parties
- Single source of truth for trip state
  - Customer support and analytics query one workflow, not 8 services
[Visual suggestion: Linear timeline of trip steps with retry loops, branching for cancellation, and a "Temporal" badge orchestrating it all]

---

### Slide 37: Section Key Takeaways
- Async = decouple "accepting work" from "doing work"
  - The single biggest tool for building responsive, resilient systems
- Message queues add buffering, retries, and fault isolation
  - DLQs, idempotency, and ordering choices are non-negotiable in production
- Task queues specialize for application work units
  - Celery, Sidekiq, Bull bring batteries-included retries, scheduling, priorities
- Streaming (Kafka) unlocks pub/sub, event sourcing, and replay
  - Topics + partitions + offsets are the foundational vocabulary
- Backpressure prevents cascading failures
  - Bounded queues, rate limits, circuit breakers, load shedding
- Orchestration handles multi-step durable workflows
  - Reach for Temporal/Step Functions/Airflow when queues alone aren't enough
[Visual suggestion: 6-icon summary grid mapping each takeaway to a pictogram]

---

### Slide 38: Interview Tips — Async & Queues
- Default to async for any operation >1s or with external dependencies
  - "I'd send the email via a Celery/SQS task so we return 202 immediately"
- Always mention idempotency when discussing at-least-once delivery
  - "Consumer will be idempotent using a dedup table on messageId"
- Pick the right tool for the job
  - SQS for simple work queues, Kafka for streaming/replay, Temporal for multi-step workflows
- Show you understand failure modes
  - DLQs, poison messages, consumer lag, replication factor, partition rebalancing
- Talk through partitioning strategy in streaming questions
  - "Partition by userId so all events for one user stay ordered on one partition"
- Mention observability: queue depth, consumer lag, redelivery rate, DLQ size
  - These are the SRE-level signals that show maturity
[Visual suggestion: Interview "cheat sheet" panel with 6 bullet headers, each with a 1-line answer template]

---

### Slide 39: Common Pitfalls
- Treating queues as databases
  - Queues are for in-flight work; long-term state belongs in a DB
- Forgetting idempotency
  - At-least-once delivery means duplicates; "send email twice" or "charge card twice" = real bugs
- No DLQ → infinite retries
  - Poison messages block the queue forever; producers stop, alerts fire, weekend ruined
- Ignoring consumer lag
  - Lag silently grows for hours, then SLOs are violated; monitor it as a top-tier signal
- Picking Kafka when SQS would do (or vice versa)
  - Kafka is heavy operationally; don't run it for 100 messages/day. Don't use SQS where you need replay.
- Synchronous-feeling APIs over async backends
  - Polling forever for a job result instead of using webhooks/WebSockets degrades UX
- Schema changes that break consumers
  - Always use a Schema Registry + backward-compatible evolution (Avro, Protobuf)
- Not testing failure paths
  - Worker crashes mid-task, broker restarts, network partitions — chaos test these in staging
[Visual suggestion: "Warning signs" themed slide — 8 red caution-tape strips, each with a one-line pitfall]
