## Section 4: Load Balancers and Reverse Proxies

### Slide 1: Section Overview
- What this section covers
  - Load balancers: distributing traffic across many backend servers
  - Reverse proxies: front-door servers that mediate client-server communication
  - Algorithms, configurations, and trade-offs that real systems use
- Why it matters
  - Almost every scaled system sits behind an LB and/or reverse proxy
  - Interview staple: "How does traffic reach your service?" expects this knowledge
- Mental model
  - LB = traffic cop directing cars to open lanes
  - Reverse proxy = receptionist that screens, redirects, and logs every visitor
[Visual suggestion: Title slide with a network diagram showing clients -> LB/Proxy -> pool of app servers]

---

### Slide 2: What is a Load Balancer?
- Definition
  - A device or software that distributes incoming network traffic across multiple backend servers
  - Sits between clients and the server pool, presenting a single endpoint (one IP/DNS name)
- Why it exists
  - A single server has finite CPU, memory, and bandwidth; eventually it tips over
  - Horizontal scaling (more servers) only works if traffic is shared evenly
- The two jobs of an LB
  - Distribute load so no single server is overwhelmed
  - Detect and route around unhealthy servers automatically
[Visual suggestion: Many client icons -> single LB box -> fan-out to N server icons]

---

### Slide 3: Why You Need a Load Balancer
- Scalability
  - Add or remove servers without changing the public endpoint
  - Linear capacity increase as you add backends (in theory)
- High availability
  - If one backend dies, the LB stops sending traffic to it; users feel nothing
  - Enables zero-downtime deploys via rolling restarts
- Performance and flexibility
  - Route requests intelligently (by region, content type, user)
  - Offload expensive work like SSL termination from app servers
- Real-world analogy
  - Grocery store checkout: a single line that feeds whichever cashier opens up next, instead of choosing a lane and getting stuck behind the price-check
[Visual suggestion: Side-by-side - left: 1 server crushed by traffic; right: LB spreading load to 4 healthy servers]

---

### Slide 4: Layer 4 vs Layer 7 Load Balancing - Concept
- The OSI model in one breath
  - Layer 4 = Transport (TCP/UDP, IP addresses, ports)
  - Layer 7 = Application (HTTP, gRPC, headers, cookies, URLs)
- Layer 4 LB
  - Forwards packets based on IP and port without inspecting payload
  - Fast, cheap, protocol-agnostic
- Layer 7 LB
  - Reads the HTTP request and routes based on URL path, headers, cookies, method
  - Smarter but more CPU-intensive
[Visual suggestion: OSI stack with L4 and L7 highlighted, plus an HTTP request being inspected at L7]

---

### Slide 5: Layer 4 Load Balancing - Deep Dive
- How it works
  - Operates at the TCP/UDP level; sees source/dest IP and port
  - Performs NAT (Network Address Translation) to forward connections to backends
  - One TCP connection from client maps to one TCP connection to backend
- Strengths
  - Very fast, low latency (minimal processing per packet)
  - Works for any TCP/UDP protocol: databases, game servers, MQTT, raw sockets
  - Lower CPU and memory footprint
- Limitations
  - Cannot route based on URL or HTTP headers
  - Cannot terminate SSL or inspect content
  - Sticky sessions limited to source IP (coarse)
- Examples
  - AWS Network Load Balancer (NLB), HAProxy in TCP mode, IPVS, Linux LVS
[Visual suggestion: Packet flow diagram showing IP/port headers being read and forwarded as opaque bytes]

---

### Slide 6: Layer 7 Load Balancing - Deep Dive
- How it works
  - Terminates the client TCP connection, parses HTTP, then opens a new connection to backend
  - Can read URL path, query string, headers, cookies, body
- Smart routing examples
  - `/api/*` -> API server pool, `/static/*` -> CDN/static pool, `/admin/*` -> admin pool
  - Route mobile clients to mobile-optimized backend via User-Agent header
  - A/B testing by routing 10% of users to a canary pool based on cookie
- Bonus features unlocked
  - SSL/TLS termination, response caching, compression, request rewriting
  - Authentication, rate limiting, web application firewall (WAF)
- Examples
  - AWS Application Load Balancer (ALB), Nginx, HAProxy in HTTP mode, Envoy, Traefik
[Visual suggestion: HTTP request being parsed; arrows splitting based on `/api`, `/static`, `/admin` paths]

---

### Slide 7: L4 vs L7 - When to Use Which
- Use Layer 4 when
  - Maximum throughput and lowest latency are critical
  - Protocol is non-HTTP (databases, custom TCP, UDP gaming)
  - You don't need content-based routing
- Use Layer 7 when
  - You need URL/header-based routing or microservice routing
  - SSL termination, caching, or WAF features are required
  - Cost of extra CPU is acceptable for the flexibility gained
- Common pattern
  - L4 LB in front of L7 LB: NLB -> ALB -> services (gets DDoS resilience + smart routing)
- Quick rule of thumb
  - HTTP/HTTPS service? Default to L7. Anything else? Default to L4.
[Visual suggestion: Decision tree - "Is it HTTP?" yes->L7, no->L4; "Need content routing?" yes->L7, no->L4]

---

### Slide 8: Load Balancing Algorithms - Why They Matter
- The core question
  - Given an incoming request and N healthy backends, which backend gets it?
- Why it's not trivial
  - Servers may have different capacities (old vs new hardware)
  - Requests have wildly different costs (a search vs a static asset)
  - Some requests need to land on the same server (session state)
- Categories of algorithms
  - Stateless rotation: Round Robin, Random
  - Capacity-aware: Weighted Round Robin
  - Load-aware: Least Connections, Least Response Time
  - Affinity-aware: IP Hash, Sticky Sessions
[Visual suggestion: 6 algorithm icons in a 2x3 grid with one-line descriptions]

---

### Slide 9: Round Robin
- How it works
  - Send request 1 to server A, request 2 to B, request 3 to C, then back to A
  - Pure rotation; no awareness of load or capacity
- Why it exists
  - Simplest possible distribution; trivial to implement (just a counter)
  - Works well when servers are identical and requests are similar in cost
- When to use
  - Homogeneous server pool, short-lived stateless requests (e.g., simple REST APIs)
  - Default starting point if you have no other information
- Pitfalls
  - Ignores actual server load - one slow request on server A doesn't stop A from getting more
  - Bad fit for variable request costs (some servers can pile up while others are idle)
[Visual suggestion: Circular arrow cycling A -> B -> C -> A with sequential request numbers]

---

### Slide 10: Weighted Round Robin
- How it works
  - Assign each server a weight; higher weight = more requests
  - Example: A=3, B=2, C=1 means 6-request cycle goes A,A,A,B,B,C
- Why it exists
  - Real fleets are heterogeneous: a 32-core box can handle more than an 8-core box
  - Lets you mix instance sizes during migrations or capacity ramps
- When to use
  - Mixed hardware generations, gradual rollouts (give canary 1%, prod 99%)
  - Different cloud regions/zones with different capacities
- Pitfalls
  - Weights are static; if server B suddenly slows down, weights don't auto-adjust
  - Operators forget to update weights after hardware changes
[Visual suggestion: Three buckets sized 3x, 2x, 1x with balls falling into them proportionally]

---

### Slide 11: Least Connections
- How it works
  - Track the number of active connections per backend; send new request to the server with fewest
- Why it exists
  - Long-lived or variable-duration requests cause uneven load with Round Robin
  - "Connections in flight" is a cheap proxy for "current load"
- When to use
  - Long-lived connections: WebSockets, database pools, streaming endpoints
  - Variable request durations (some endpoints take 50ms, others 5s)
- Pitfalls
  - Connection count != actual CPU work (one heavy request can starve a "lightly loaded" server)
  - LB must track connection state, slightly more overhead than Round Robin
[Visual suggestion: Three servers with connection counts 7, 3, 5; new request arrow points to the "3" server]

---

### Slide 12: Least Response Time
- How it works
  - Track each server's recent average response latency; pick the fastest responder
  - Often combined with Least Connections (pick lowest of: connections * avg_latency)
- Why it exists
  - Latency directly reflects user experience and true server health
  - Catches partially degraded servers that still accept connections but respond slowly
- When to use
  - Latency-sensitive APIs, user-facing endpoints
  - Heterogeneous workloads where some servers might be GC-pausing or thrashing
- Pitfalls
  - Requires continuous latency measurement, more LB CPU
  - Can oscillate ("herd" toward a fast server until it gets overloaded)
[Visual suggestion: Three servers showing 50ms, 200ms, 80ms; arrow goes to 50ms one]

---

### Slide 13: IP Hash and Sticky Sessions
- How IP Hash works
  - Hash the client IP address; map hash to a backend server
  - Same client IP -> same server (deterministic)
- How Sticky Sessions work (L7)
  - LB sets or reads a cookie (e.g., `AWSALB`); same cookie -> same backend
- Why they exist
  - When servers store session state in memory, the user must come back to the same one
  - Avoids needing a shared session store (Redis) for simple apps
- When to use
  - Legacy stateful apps, in-memory session caches
  - WebSocket connections (you want subsequent messages to land on the same server)
- Pitfalls
  - Uneven distribution if a few clients are very heavy (NAT, mobile carriers behind one IP)
  - Server failure loses that user's session entirely
  - Anti-pattern in modern microservices - prefer stateless services with external session store
[Visual suggestion: Hash function mapping IP 1.2.3.4 -> Server B consistently across multiple requests]

---

### Slide 14: Random
- How it works
  - Pick a backend uniformly at random for each request
- Why it exists
  - Stateless, requires no counters or coordination
  - Statistically converges to even distribution at high request volume
- When to use
  - Very high QPS, stateless services where simplicity matters
  - Distributed LBs that can't share state (each instance can pick independently)
- Variant: "Power of Two Choices"
  - Pick 2 random servers, send to whichever has fewer connections
  - Surprisingly close to optimal Least Connections, with minimal state
- Pitfalls
  - Can produce short-term hotspots due to randomness
  - Less predictable than Round Robin for debugging
[Visual suggestion: Dice rolling and selecting a server from a fan; second panel shows "pick 2, choose the lighter"]

---

### Slide 15: Algorithm Selection Cheat Sheet
- Identical servers, short requests -> Round Robin
- Mixed hardware or canary deploys -> Weighted Round Robin
- Long-lived connections (WebSocket, DB pool) -> Least Connections
- Latency-critical user-facing API -> Least Response Time
- Stateful session-in-memory app -> IP Hash / Sticky Sessions
- Massively parallel stateless service -> Random or Power of Two Choices
- Don't know yet?
  - Start with Round Robin, measure, then refine
[Visual suggestion: Decision matrix table with workload characteristics on rows and algorithms on columns]

---

### Slide 16: Load Balancing Algorithm - Real Example
- Scenario: e-commerce site on Black Friday
  - 5 app servers (3 new powerful boxes, 2 older boxes), HTTP traffic
  - Some requests are 50ms (browse), some are 3s (checkout/payment)
- Naive Round Robin
  - Older boxes get same share as new ones -> they slow down -> users wait
- Weighted + Least Connections combo
  - Weights: new=3, old=1; tiebreak by least active connections
  - New servers absorb more load; if new server is mid-checkout, the next request goes elsewhere
- Result
  - Even latency across the fleet, no single hotspot
[Visual suggestion: Timeline showing requests flowing; old vs new servers; healthy traffic curves]

---

### Slide 17: Hardware vs Software Load Balancers
- Hardware LBs
  - Dedicated physical appliances: F5 BIG-IP, Citrix ADC, A10
  - Pros: extremely high throughput, custom ASICs, vendor support
  - Cons: expensive ($$$), inflexible, slow to upgrade, vendor lock-in
- Software LBs
  - Run on commodity servers/VMs/containers: Nginx, HAProxy, Envoy, Traefik
  - Pros: cheap, elastic, scriptable, integrates with CI/CD
  - Cons: you operate it; throughput limited by host hardware
- Cloud-managed LBs
  - AWS ELB (ALB/NLB/GWLB), GCP Cloud Load Balancing, Azure Load Balancer
  - Best of both: software-defined, elastic, managed by cloud provider
- Today's reality
  - Software/cloud-managed dominates; hardware LBs survive in regulated/on-prem niches
[Visual suggestion: Three columns - hardware appliance icon, server with Nginx logo, cloud provider logos]

---

### Slide 18: Load Balancer Examples in the Wild
- Nginx
  - Originally a web server; excellent L7 LB and reverse proxy; huge open-source community
- HAProxy
  - Specialist LB; battle-tested at extreme scale (Stack Overflow, GitHub used it heavily)
- AWS ELB family
  - ALB (L7, HTTP/HTTPS, host/path routing), NLB (L4, ultra-low latency), GWLB (network appliances)
- Envoy
  - Modern L7 proxy; powers service meshes (Istio, Consul Connect); rich observability
- Cloudflare Load Balancing
  - Global anycast LB at the edge; geographic + health-based routing
[Visual suggestion: Logo grid with 1-line capability summary under each]

---

### Slide 19: Active-Active Configuration
- How it works
  - Two or more LBs handle live traffic simultaneously, each serving a fraction
  - Clients reach them via DNS round robin, anycast, or virtual IPs
- Pros
  - Full hardware utilization (no idle standby)
  - Higher aggregate throughput
  - Faster failover - peers already warm
- Cons
  - More complex (state sync, session affinity coordination)
  - Capacity planning must assume one node can fail and remaining must absorb load
- Common in
  - Cloud-native deployments, anycast CDNs, large-scale ALB/NLB
[Visual suggestion: Two LB boxes both receiving traffic, both forwarding to shared backend pool]

---

### Slide 20: Active-Passive Configuration
- How it works
  - One LB (active) handles all traffic; second LB (passive) sits idle, ready to take over
  - Failover via VRRP/keepalived virtual IP, or DNS update
- Pros
  - Simpler mental model and configuration
  - No state-sync complexity during normal operation
- Cons
  - 50% of capacity is idle (wasted hardware)
  - Failover takes seconds (VIP migration, ARP refresh, DNS TTL)
- Common in
  - Traditional on-prem deployments, smaller setups, regulated environments
[Visual suggestion: Active LB with green check serving traffic; passive LB with grey "standby" badge waiting]

---

### Slide 21: Disadvantages of Load Balancers
- Added complexity
  - One more system to configure, monitor, secure, and patch
  - Misconfiguration can break the entire fleet at once
- Single point of failure (if not redundant)
  - The LB itself can crash; a single LB = entire site down
  - Always deploy redundant LBs (active-active or active-passive)
- Latency overhead
  - Every request makes an extra hop through the LB
  - L7 inspection adds CPU time (header parsing, SSL termination)
- Cost
  - Cloud LBs are billed per hour + per GB processed; high-traffic sites pay real money
- Debugging difficulty
  - Adds a layer to trace through; client IP can get masked (need `X-Forwarded-For`)
[Visual suggestion: Red warning triangle with bullet list of risks; arrow showing extra hop adding latency]

---

### Slide 22: Health Checks
- What they are
  - Periodic probes the LB sends to each backend to verify it's alive and serving
  - Unhealthy backends are removed from the rotation automatically
- Types of health checks
  - TCP: can the LB open a TCP connection? (L4)
  - HTTP: does GET `/health` return 200? (L7, smarter)
  - Application-aware: check that DB connection works, dependencies are reachable
- Best practices
  - Dedicated `/healthz` endpoint that exercises real dependencies
  - Threshold-based: mark unhealthy after N consecutive failures (avoid flapping)
  - Different intervals for different criticality (fast for prod, slower for staging)
- Pitfalls
  - Health check that's too cheap returns 200 even when app is broken (false healthy)
  - Health check that's too heavy adds load and can itself cause failures
[Visual suggestion: LB pinging 3 backends; one returns red X and is crossed off the rotation]

---

### Slide 23: Connection Draining (Graceful Shutdown)
- The problem
  - You need to remove a server from the pool (deploy, patch, scale-in)
  - Killing it instantly drops in-flight requests -> users see errors
- How draining works
  - Mark backend as "draining"; LB stops sending NEW connections to it
  - Existing connections finish naturally up to a timeout (e.g., 30-300 seconds)
  - After all connections close (or timeout), backend is fully removed
- Why it matters
  - Zero-downtime deploys, rolling updates, auto-scale-in events
  - Critical for long-lived connections (WebSockets, file uploads)
- Configuration knobs
  - AWS: "deregistration delay" on target groups (default 300s)
  - Nginx: `server ... down` directive after reload
  - Kubernetes: `terminationGracePeriodSeconds` + `preStop` hook
[Visual suggestion: Server marked "draining" with hourglass; new arrows blocked, existing connections finishing]

---

### Slide 24: Load Balancer - Architecture Diagram
- Components in the diagram
  - Clients (browsers, mobile apps) on the left
  - DNS pointing `api.example.com` to LB's public IP
  - Two redundant LBs in active-active behind a virtual IP / anycast
  - Backend pool of N app servers in private subnet
  - Health check arrows from LB to each backend
  - Monitoring/metrics pipe to Datadog/CloudWatch
- Flow labels
  - 1: Client DNS lookup -> LB IP
  - 2: Client TCP/TLS handshake terminates at LB
  - 3: LB picks healthy backend per algorithm (e.g., least-conn)
  - 4: LB opens connection to backend, proxies request
  - 5: Response returns through LB to client
  - 6: Periodic health checks (dotted lines) to all backends
[Visual suggestion: Full architecture diagram with the components and numbered flow labels above]

---

### Slide 25: Load Balancer - Trade-offs
- Performance vs flexibility
  - L4 = fast/dumb; L7 = smart/slower; pick based on need
- Cost vs availability
  - Active-active = full capacity but complex; active-passive = simple but half-capacity idle
- Stickiness vs even distribution
  - Sticky sessions help legacy apps but cause hot spots and lose state on failover
- Health-check sensitivity
  - Aggressive checks catch failures fast but cause flapping; lax checks miss issues
- DIY vs managed
  - Self-hosted (HAProxy/Nginx) = control + ops burden; cloud LB = convenience + cost + lock-in
[Visual suggestion: Five balance-scale icons, each showing one trade-off]

---

### Slide 26: What is a Reverse Proxy?
- Definition
  - A server that sits in front of one or more backend servers and forwards client requests to them
  - Clients believe they're talking to the proxy; backends are hidden
- The "reverse" part
  - Forward proxy: hides the CLIENT from the server (e.g., corporate proxy filtering employee web traffic)
  - Reverse proxy: hides the SERVER from the client (the public-facing front door)
- Why "reverse"
  - The direction of "who is being represented" is flipped vs a forward proxy
- Real-world analogy
  - Reverse proxy = hotel concierge: you ask "I want room service," concierge calls the right department; you never deal with kitchen directly
[Visual suggestion: Two diagrams side by side - forward proxy (clients hidden) vs reverse proxy (server hidden)]

---

### Slide 27: Forward Proxy vs Reverse Proxy
- Forward proxy
  - Lives near the client; client explicitly configures it
  - Use cases: corporate firewall, content filtering, anonymity (VPN-ish), caching outbound traffic
  - Examples: Squid, corporate web proxies
- Reverse proxy
  - Lives near the server; clients are unaware of backends
  - Use cases: hide backend topology, SSL termination, caching, load balancing, security
  - Examples: Nginx, HAProxy, Cloudflare, Apache mod_proxy
- One-line distinction
  - Forward proxy = "I'll fetch the internet for you" (client-side)
  - Reverse proxy = "I'll hand your request to the right server" (server-side)
[Visual suggestion: Two-panel diagram - forward proxy between many clients and the internet; reverse proxy between internet and many backend servers]

---

### Slide 28: Reverse Proxy Benefits - SSL Termination
- What it is
  - Reverse proxy holds the SSL/TLS certificates and decrypts HTTPS traffic at the edge
  - Forwards plaintext (or re-encrypted) HTTP to backends inside the trusted network
- Why it matters
  - SSL handshakes are CPU-intensive; centralizing them spares backend CPU
  - One place to manage certificates, renewals, cipher suites (instead of N servers)
  - Backends speak simple HTTP, easier to develop and debug
- Trade-off
  - Internal traffic is plaintext unless you re-encrypt (zero-trust networks usually re-encrypt)
[Visual suggestion: HTTPS arrow from client to proxy (locked), HTTP arrow from proxy to backends (unlocked, inside private network bubble)]

---

### Slide 29: Reverse Proxy Benefits - Caching
- What it is
  - Proxy stores recent responses; future identical requests served from cache without hitting backend
- Why it matters
  - Massive reduction in backend load (especially for static assets, API responses)
  - Lower latency for users (cached response is microseconds)
- What to cache
  - Static files (images, CSS, JS): cache for hours/days
  - API responses with short TTL (10-60 seconds) for dashboards and feeds
  - Respect HTTP cache headers (`Cache-Control`, `ETag`, `Vary`)
- Real-world
  - Nginx with `proxy_cache`, Varnish, Cloudflare edge cache
[Visual suggestion: First request goes through proxy to backend (slow); second request returns from proxy cache (fast)]

---

### Slide 30: Reverse Proxy Benefits - Compression and Performance
- Compression
  - Proxy gzip/brotli-compresses responses before sending to client
  - Reduces bandwidth by 60-80% for HTML/JSON/CSS
  - Backends don't waste CPU on compression
- Connection pooling / multiplexing
  - Proxy keeps long-lived connections to backends, reuses them across many client requests
  - Reduces backend connection-setup overhead
- HTTP/2 and HTTP/3 termination
  - Proxy speaks modern protocols to clients while backends stay on simple HTTP/1.1
- Buffering
  - Proxy absorbs slow clients; backends only see fast, complete requests
[Visual suggestion: Compressed payload icons; pool of reusable connections between proxy and backends]

---

### Slide 31: Reverse Proxy Benefits - Security
- Hides backend topology
  - Attackers see only the proxy IP; internal IPs, ports, and architecture are masked
- Centralized security policy
  - WAF (web application firewall) rules: block SQL injection, XSS, bot patterns
  - Rate limiting per IP / per token to defend against abuse and DDoS
- TLS hygiene
  - Modern cipher suites, HSTS, OCSP stapling enforced once at the proxy
- Authentication offload
  - JWT validation, OAuth2 introspection, mTLS done at the proxy; backends trust forwarded identity
[Visual suggestion: Shield icon over the proxy; arrows of attacks bouncing off; clean traffic continuing inward]

---

### Slide 32: Reverse Proxy Benefits - Centralized Logging and Observability
- Single place to log everything
  - Every request and response passes through the proxy -> uniform access logs
  - Backend servers can stay focused on business logic
- Metrics for free
  - Request rate, latency percentiles (p50/p95/p99), error rates, status code distribution
  - Per-route, per-host, per-upstream breakdowns
- Distributed tracing
  - Inject `X-Request-Id` and trace headers at the proxy; propagate downstream
- Examples
  - Nginx access logs -> Loki/ELK; Envoy metrics -> Prometheus + Grafana
[Visual suggestion: Proxy with three streams emerging: logs, metrics, traces, each going to its respective tool]

---

### Slide 33: Reverse Proxy vs Load Balancer - The Difference
- Reverse proxy
  - Primary job: mediate and enhance client-server communication (SSL, caching, security)
  - Can sit in front of just ONE backend (no load balancing needed)
- Load balancer
  - Primary job: distribute requests across MANY backends
  - Specifically picks which server gets each request via an algorithm
- The overlap
  - Most modern reverse proxies (Nginx, HAProxy, Envoy) ALSO load balance
  - Most modern L7 load balancers (ALB, Envoy) ALSO act as reverse proxies
- The honest answer
  - In practice the terms blur; the same software fills both roles
  - The distinction is conceptual: "what's its primary purpose in this deployment?"
[Visual suggestion: Venn diagram - "Reverse Proxy" circle, "Load Balancer" circle, large overlap labeled "Nginx, HAProxy, Envoy, ALB"]

---

### Slide 34: Reverse Proxy Examples in the Wild
- Nginx
  - Most popular open-source reverse proxy; powers half the internet's top sites
  - Strong at HTTP, static serving, caching; config-file driven
- HAProxy
  - Reverse proxy + LB heavyweight; preferred for raw performance and TCP workloads
- Apache HTTPD (mod_proxy)
  - Older but still common; heavily used in legacy enterprise stacks
- Cloudflare
  - Global reverse proxy as a service; DDoS protection, CDN, WAF baked in
- Envoy / Traefik
  - Modern cloud-native reverse proxies; great for Kubernetes and service meshes
[Visual suggestion: Logo strip with 1-2 word descriptors of strengths]

---

### Slide 35: Reverse Proxy - Architecture Diagram
- Components
  - Client (browser/mobile)
  - DNS -> Reverse Proxy public IP (often Cloudflare or Nginx fronted)
  - Reverse Proxy box with: TLS termination module, cache, WAF, log/metrics export
  - Backend services in private subnet (web app, API, microservices)
  - Optional: separate static asset origin (S3) and DB cluster behind app servers
- Flow labels
  - 1: Client makes HTTPS request to `app.example.com`
  - 2: TLS terminates at proxy; request decrypted and inspected
  - 3: WAF rules evaluated; bad requests rejected with 403
  - 4: Cache lookup; if hit, return immediately
  - 5: If miss, forward to appropriate backend (per path-based routing)
  - 6: Backend responds; proxy may cache, then compresses and re-encrypts to client
  - 7: Access log + metrics emitted to observability stack
[Visual suggestion: Full architecture diagram with numbered arrows for the 7-step flow]

---

### Slide 36: Reverse Proxy - Trade-offs
- Added latency vs feature richness
  - Every request goes through extra processing; usually milliseconds, but it adds up
- Centralization vs single point of failure
  - One config to manage = nice; one outage to break everything = scary (run redundant)
- Cache freshness vs hit rate
  - Long TTLs = great hit rate, but stale data risks; short TTLs = fresh, but more backend load
- SSL termination vs end-to-end encryption
  - Offload is faster, but internal traffic is plaintext unless you re-encrypt (mTLS)
- Operational complexity
  - Powerful config languages (Nginx, Envoy YAML) = power and footguns
[Visual suggestion: Five mini scales similar to LB trade-offs slide]

---

### Slide 37: Combined Architecture - LB + Reverse Proxy in Production
- A typical large web service stack (top to bottom)
  - DNS / Anycast (Route53, Cloudflare DNS)
  - Edge CDN + WAF (Cloudflare / AWS CloudFront)
  - L4 Load Balancer (AWS NLB) for raw TCP and DDoS resilience
  - L7 Load Balancer / Reverse Proxy (ALB or Nginx) for path routing, SSL, caching
  - Service mesh sidecar proxies (Envoy) for internal service-to-service calls
  - Application servers / microservices
- What each layer does
  - Each layer adds a specific capability; you don't need every layer for every system
- Lesson
  - "Load balancer" and "reverse proxy" are roles, not products; real systems compose multiple instances
[Visual suggestion: Vertical stack diagram with each layer labeled and its role annotated on the right]

---

### Slide 38: Key Takeaways
- A load balancer distributes traffic; a reverse proxy mediates and enhances it
  - Same software often plays both roles - distinction is by purpose
- L4 vs L7 is the most important LB choice
  - L4 for raw speed and non-HTTP; L7 for content-aware routing and HTTP features
- Algorithm choice depends on workload shape
  - Round Robin for uniform; Least Connections for variable; IP Hash for stateful
- Always run redundant LBs/proxies
  - The thing that makes you highly available cannot itself be a single point of failure
- Reverse proxies unlock SSL termination, caching, compression, security, and observability
  - These are why almost every public service has one
[Visual suggestion: 5 numbered icons representing each takeaway]

---

### Slide 39: Interview Tips
- Always start with "what kind of traffic?"
  - HTTP -> L7; raw TCP/UDP -> L4; clarify before picking products
- Justify your algorithm choice
  - Don't just say "Round Robin"; explain why given the workload (uniform vs variable)
- Mention redundancy explicitly
  - Interviewers love hearing "active-active LBs" or "redundant proxies with failover"
- Bring up health checks and connection draining
  - Demonstrates you've thought about the operational lifecycle, not just the happy path
- Differentiate reverse proxy benefits clearly
  - Listing SSL termination, caching, and WAF separately shows depth
- Use real product names
  - "ALB for L7, NLB for L4, Nginx as reverse proxy" sounds way more credible than "a load balancer"
- When asked "LB or reverse proxy?"
  - Say "Often the same box; LB if I emphasize distribution, reverse proxy if I emphasize the proxying features"
[Visual suggestion: Checklist style with green ticks next to each interview tip]

---

### Slide 40: Common Pitfalls
- Forgetting LB redundancy
  - Single LB = single point of failure; always run >=2 in active-active or active-passive
- Using sticky sessions in modern microservices
  - Anti-pattern; prefer stateless services with external session store (Redis)
- Bad health checks
  - "/healthz returns 200 statically" -> LB sends traffic to a server with a broken DB
  - Always exercise real dependencies in health checks (with sane timeouts)
- Ignoring connection draining
  - Causes user-facing 5xx errors during deploys and scale-in events
- Mismatching SSL between LB and backend
  - Forgetting `X-Forwarded-Proto` -> app generates HTTP redirects in HTTPS context, infinite loop
- Caching authenticated responses by mistake
  - Leaks private data to other users; always vary on auth cookies/headers
- Treating L7 as free
  - Heavy header parsing, regex routing, WAF rules add real CPU; profile and size accordingly
- Single LB doing everything
  - Mixing public ingress, internal routing, and service mesh on one LB makes blast radius huge
[Visual suggestion: Red triangle warnings next to each pitfall in a 2-column layout]
