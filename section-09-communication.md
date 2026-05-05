## Section 9: Communication Protocols

### Slide 1: Why Communication Protocols Matter
- Distributed systems are conversations between machines
  - Every request, every database query, every cache hit is a network call governed by some protocol
- Protocol choice dictates latency, throughput, and reliability
  - Picking TCP vs UDP, REST vs gRPC, polling vs WebSockets can swing performance by 10x or more
- Protocols define the contract between services
  - They encode assumptions about ordering, delivery guarantees, encoding, and error handling
- System design interviews probe protocol fluency constantly
  - "How would you push live scores to 10M users?" is fundamentally a protocol question
- One layer's strength is another's weakness
  - Reliability costs latency; flexibility costs structure; choosing well requires understanding the trade space
[Visual suggestion: Layered diagram showing client -> protocol -> network -> protocol -> server, with annotations for "where latency hides" at each step]

---

### Slide 2: OSI Model - Concept Introduction
- The OSI (Open Systems Interconnection) model is a 7-layer conceptual framework for network communication
  - Created by ISO in 1984 as a vendor-neutral way to reason about networking
- Each layer has a single responsibility and talks only to layers directly above and below
  - This separation lets you swap implementations (e.g., Ethernet for Wi-Fi at L2) without rewriting upper layers
- Real-world stacks (TCP/IP) don't strictly match OSI but borrow its vocabulary
  - "L4 load balancer" or "L7 proxy" comes directly from OSI terminology
- It exists to give engineers a shared mental model
  - When someone says "the problem is at Layer 3," every network engineer knows they mean routing
- Foundational because system design constantly references L4 vs L7 distinctions
  - Understanding the model unlocks discussions about load balancers, firewalls, and proxies
[Visual suggestion: Vertical 7-layer stack with icons (cable for L1, MAC address for L2, IP for L3, TCP/UDP for L4, etc.)]

---

### Slide 3: OSI Model - The 7 Layers Deep Dive
- Layer 1 - Physical: bits over wire/fiber/radio
  - Cables, voltages, Wi-Fi signals; deals with raw 0s and 1s
- Layer 2 - Data Link: frames between adjacent nodes (Ethernet, MAC addresses)
  - Handles collisions and local addressing on the same network segment
- Layer 3 - Network: packets across networks (IP, routing)
  - Routes data between different networks using IP addresses
- Layer 4 - Transport: end-to-end delivery (TCP, UDP)
  - Manages reliability, ordering, flow control between processes on different hosts
- Layer 5-6-7 - Session, Presentation, Application: conversations, encoding (TLS, JSON), and the actual app (HTTP, SMTP)
  - In practice these three are often blurred together; HTTP, gRPC, and DNS all live "at L7"
[Visual suggestion: 7 layers with example data unit at each (bit -> frame -> packet -> segment -> data) and a representative protocol]

---

### Slide 4: OSI Model - L4 vs L7 in System Design
- L4 load balancers route on IP and port without inspecting payload
  - Fast, protocol-agnostic; AWS NLB, HAProxy in TCP mode, IPVS
- L7 load balancers understand HTTP, can route on URL, headers, cookies
  - Smarter routing (e.g., /api/v2 to new cluster); Nginx, Envoy, AWS ALB
- L4 is cheaper and faster but blind to application semantics
  - Can't do path-based routing, header rewrites, or content-based caching
- L7 enables advanced features at higher CPU cost
  - TLS termination, A/B testing, canary deployments, sticky sessions by user ID
- Choose L4 when you need raw throughput; L7 when you need application-aware routing
  - Modern systems often layer both: L4 in front of L7 for tiered scaling
[Visual suggestion: Side-by-side comparison - L4 LB looking at "envelope" only vs L7 LB reading the "letter inside"]

---

### Slide 5: OSI vs TCP/IP Model Comparison
- TCP/IP model is the practical 4-layer model the internet actually uses
  - Link -> Internet -> Transport -> Application; collapses OSI's L1+L2 and L5+L6+L7
- OSI is the textbook reference; TCP/IP is the engineering reality
  - You'll see TCP/IP terms in RFCs and documentation, OSI terms in interviews
- Mapping: OSI L1+L2 = TCP/IP Link; L3 = Internet; L4 = Transport; L5+L6+L7 = Application
  - Functionality is the same, granularity differs
- Why this matters: when you read "the application layer" in TCP/IP, it includes encoding and session management
  - HTTPS bundles HTTP (L7), TLS (L5/6), and runs on TCP (L4) over IP (L3)
- Both models exist because abstraction is the only way to manage networking complexity
  - You don't write code that thinks about voltage levels when calling fetch()
[Visual suggestion: Two stacks side-by-side with arrows mapping OSI 7 layers to TCP/IP 4 layers]

---

### Slide 6: TCP - Concept Introduction
- TCP (Transmission Control Protocol) is connection-oriented and reliable
  - Sender and receiver establish a session, exchange data with guaranteed delivery, then tear down
- Guarantees: in-order delivery, no duplicates, no losses (or you get an error)
  - The OS retransmits lost packets, reorders out-of-order ones, and deduplicates
- Trades latency and overhead for reliability
  - Every packet is acknowledged; lost packets trigger retransmission; congestion control throttles speed
- TCP is the workhorse of the internet
  - HTTP/1.1, HTTP/2, SSH, SMTP, FTP, database connections - virtually all "important" data uses TCP
- Exists because applications need reliable byte streams without writing their own retry logic
  - Before TCP, every app reinvented retry, ordering, and flow control - TCP standardized it
[Visual suggestion: Two stick figures passing numbered envelopes back and forth with checkmarks for ACKs]

---

### Slide 7: TCP - 3-Way Handshake Deep Dive
- Step 1 - SYN: client sends synchronize packet with initial sequence number
  - "Hi, I want to talk; my numbering starts at X"
- Step 2 - SYN-ACK: server replies with its own SYN and acknowledges client's SYN
  - "Got it, I'll number my data starting at Y, and I confirm I saw your X"
- Step 3 - ACK: client acknowledges server's SYN, connection established
  - "Confirmed, let's go"; takes 1.5 round-trips before any real data flows
- Connection teardown uses a 4-way handshake (FIN, ACK, FIN, ACK)
  - Each side closes its half independently; this is why "TIME_WAIT" sockets accumulate
- Handshake overhead is why TCP feels slow on high-latency networks
  - On a 100ms RTT link, you've burned 150ms before sending a single byte of data
[Visual suggestion: Sequence diagram with client and server lifelines showing SYN, SYN-ACK, ACK arrows with timestamps]

---

### Slide 8: UDP - Concept Introduction
- UDP (User Datagram Protocol) is connectionless and unreliable
  - Send a packet and hope it arrives; no handshake, no acknowledgments, no retransmission
- "Fire and forget" semantics with minimal overhead
  - 8-byte header vs TCP's 20+ bytes; no connection state on either side
- No ordering, no deduplication, no congestion control by default
  - Application is responsible for handling lost or out-of-order packets if it cares
- Faster and lighter than TCP, ideal when latency matters more than reliability
  - Real-time use cases tolerate occasional loss but cannot tolerate buffering delays
- Exists for cases where retransmission is worse than loss
  - In a video call, a 200ms-old frame is useless; better to skip it than wait for it
[Visual suggestion: Stick figure throwing paper airplanes - some fly, some crash, sender doesn't look back]

---

### Slide 9: TCP vs UDP - Trade-offs and When to Choose
- Choose TCP when correctness > speed
  - Banking transactions, file downloads, web pages, emails, database queries
- Choose UDP when speed > perfect delivery
  - Live video, online gaming, VoIP, DNS lookups, real-time telemetry, multicast
- TCP is slower because of retransmissions, ACKs, congestion control, and head-of-line blocking
  - One lost packet stalls everything behind it until it's recovered
- UDP forces you to build reliability yourself if you need it
  - QUIC (used by HTTP/3) does exactly this: UDP + custom reliability layer
- Real examples: Netflix uses TCP for control plane and UDP-based protocols for video chunks
  - Google Meet, Zoom, Discord voice all run RTP-over-UDP for audio/video streams
[Visual suggestion: Decision tree - "Is loss tolerable?" branching to UDP, "Need reliability?" branching to TCP, with example apps at leaves]

---

### Slide 10: TCP vs UDP - Real Product Examples
- HTTP, HTTPS, SSH, SFTP, SMTP -> TCP
  - Loading this slide deck, pulling git repos, sending emails all rely on TCP guarantees
- DNS queries -> primarily UDP (with TCP fallback for large responses)
  - DNS is small and idempotent; retry on timeout is fine
- Online games (Fortnite, CS:GO, Valorant) -> UDP for game state, TCP for chat/lobby
  - Position updates that arrive 50ms late are useless; chat messages need reliability
- Streaming (YouTube live, Twitch, Zoom) -> UDP-based RTP for media, TCP for control
  - Video frames can be dropped gracefully; "join meeting" command must succeed
- WhatsApp/Signal voice calls -> SRTP over UDP for audio, TCP for messaging
  - Voice tolerates loss; "read receipts" need exact-once delivery
[Visual suggestion: Product logos in two columns - TCP column (Gmail, GitHub, Stripe) and UDP column (Zoom audio, Fortnite, DNS)]

---

### Slide 11: TCP/UDP Diagram - Packet Flow Comparison
- TCP flow: connect -> data -> ACK -> data -> ACK -> close (lots of bookkeeping)
  - Each segment carries sequence numbers, ACK numbers, window size, flags
- UDP flow: send packet, send packet, send packet (no return trips)
  - Each datagram is independent with just source/dest port and length
- TCP retransmission scenario: packet 5 lost -> receiver buffers 6, 7, 8 -> sender resends 5 -> deliver 5,6,7,8 in order
  - This buffering causes head-of-line blocking
- UDP loss scenario: packet 5 lost -> receiver gets 6, 7, 8 -> application decides what to do
  - Game engine interpolates missing position; voice codec masks dropped frame
- Visualizing the difference clarifies why protocol choice matters
  - The "shape" of the conversation determines latency floor and reliability ceiling
[Visual suggestion: Two timelines side-by-side - TCP showing handshake, ordered delivery with ACKs; UDP showing simple unidirectional packet stream with one dropped]

---

### Slide 12: HTTP Protocol - Concept Introduction
- HTTP (HyperText Transfer Protocol) is the request-response protocol of the web
  - Client sends a request (method + URL + headers + optional body), server sends a response (status + headers + body)
- Stateless by design: each request is independent
  - Server doesn't remember previous requests; state lives in cookies, tokens, or databases
- Text-based and human-readable in HTTP/1.x; binary in HTTP/2 and HTTP/3
  - You can literally telnet to port 80 and type GET / HTTP/1.1 in HTTP/1.1
- Built on TCP (HTTP/1.1, HTTP/2) or QUIC/UDP (HTTP/3)
  - Transport choice fundamentally changes performance characteristics
- Exists to standardize document and resource transfer
  - Before HTTP, every system had a custom protocol; HTTP made the web possible
[Visual suggestion: Browser sending GET /index.html request with headers shown, server responding with 200 OK and HTML body]

---

### Slide 13: HTTP/1.1 Deep Dive
- Text-based protocol with one request per connection (originally)
  - Each request opens a TCP connection, sends, receives, closes - extremely wasteful
- Keep-alive (persistent connections) reuses TCP connection for multiple requests
  - Default in HTTP/1.1; saves the handshake cost on subsequent requests
- Pipelining allows multiple requests without waiting for responses
  - Rarely used in practice due to head-of-line blocking and proxy bugs
- Head-of-line blocking: response 1 must complete before response 2 starts
  - One slow image blocks all subsequent assets on the same connection
- Browsers work around this by opening 6 parallel connections per origin
  - This is why "domain sharding" was a popular HTTP/1.1 optimization
[Visual suggestion: Timeline showing 6 parallel TCP connections, each fetching assets sequentially with idle gaps]

---

### Slide 14: HTTP/2 Deep Dive
- Binary framing layer replaces text parsing
  - Frames are typed (HEADERS, DATA, SETTINGS, etc.); efficient and unambiguous
- Multiplexing: many requests/responses interleaved on one TCP connection
  - Solves application-layer head-of-line blocking; one connection serves the whole page
- HPACK header compression reduces redundant header bytes
  - Cookies, User-Agent, Accept headers are sent once and referenced by index thereafter
- Server push allows server to preemptively send resources
  - "You asked for index.html; here's style.css too because I know you'll need it"
- Still suffers from TCP-level head-of-line blocking
  - One lost TCP packet stalls all multiplexed streams until retransmission completes
[Visual suggestion: Single TCP connection with multiple colored streams (HTML, CSS, JS, images) interleaved as frames]

---

### Slide 15: HTTP/3 and QUIC Deep Dive
- HTTP/3 runs over QUIC, which runs over UDP instead of TCP
  - Google built QUIC in user space for faster iteration than kernel-level TCP changes
- Eliminates TCP head-of-line blocking by giving each stream its own loss recovery
  - A lost packet for stream 1 doesn't stall streams 2, 3, 4
- Faster connection setup with 0-RTT and 1-RTT handshakes
  - Reconnecting clients can send data with the very first packet
- TLS 1.3 baked in; encryption is mandatory at the transport level
  - No more "speak HTTP first then upgrade to TLS" round trips
- Better mobile performance with connection migration
  - Switch Wi-Fi to cellular and your QUIC connection survives via connection IDs
[Visual suggestion: HTTP/3 stack diagram - HTTP/3 -> QUIC -> UDP -> IP, with TLS 1.3 inside QUIC, contrasted with HTTP/2 -> TLS -> TCP -> IP]

---

### Slide 16: HTTP Methods Deep Dive
- GET: retrieve a resource; safe and idempotent
  - Should never modify server state; cacheable; parameters in URL
- POST: create a resource or trigger a non-idempotent action
  - Two POSTs to /orders create two orders; not safe to retry blindly
- PUT: replace a resource entirely; idempotent
  - PUT /users/42 with full user object; same call twice yields same result
- PATCH: partial update; usually idempotent but not guaranteed
  - PATCH /users/42 with {"email": "x@y.com"} only changes email
- DELETE: remove a resource; idempotent
  - HEAD: like GET but no body (check existence/headers); OPTIONS: discover allowed methods (CORS preflight)
[Visual suggestion: Method matrix with columns Safe, Idempotent, Cacheable, Has-Body and rows for each method with checkmarks]

---

### Slide 17: HTTP Status Codes Deep Dive
- 2xx Success: 200 OK, 201 Created, 204 No Content
  - 201 means resource created (use after POST); 204 means success but no body to return
- 3xx Redirection: 301 Moved Permanently, 302 Found, 304 Not Modified
  - 301 is cacheable forever; 304 enables conditional GETs with ETag/If-Modified-Since
- 4xx Client Error: 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests
  - 401 means "who are you?"; 403 means "I know you, you can't do this"; 429 signals rate limiting
- 5xx Server Error: 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout
  - 502/504 typically indicate problems behind your load balancer; 503 means deliberately unavailable
- Picking the right code matters for caching, retries, and observability
  - Returning 200 with an error body breaks every middlebox that relies on status codes
[Visual suggestion: Color-coded grid - green 2xx, yellow 3xx, orange 4xx, red 5xx with key codes and one-line descriptions]

---

### Slide 18: HTTP Headers, Cookies, and Sessions
- Headers carry metadata: Content-Type, Authorization, Cache-Control, User-Agent
  - Custom headers (X-Request-ID, X-Forwarded-For) propagate trace IDs and client IPs through proxies
- Cookies are key-value pairs the server sets and the browser sends back automatically
  - Set-Cookie response header; Cookie request header; scoped by domain and path
- Sessions are server-side state keyed by a cookie (often a session ID)
  - Alternative: stateless JWTs that encode user info in the cookie itself
- Critical security flags: HttpOnly (no JS access), Secure (HTTPS only), SameSite (CSRF protection)
  - Missing these flags is how XSS attacks steal session tokens
- Cache-Control headers govern CDN and browser caching
  - max-age, no-store, private, immutable, stale-while-revalidate each have specific meanings
[Visual suggestion: HTTP request/response with headers highlighted, showing cookie flow and a session token round trip]

---

### Slide 19: HTTP Comparison and Real Examples
- HTTP/1.1: still ubiquitous, simple to debug, fine for small APIs
  - curl, postman, server logs all show readable HTTP/1.1 traffic
- HTTP/2: most production websites in 2020+; great for multi-asset pages
  - Cloudflare, Google, Facebook serve HTTP/2 by default
- HTTP/3: rolling out at scale; Google, Cloudflare, Meta, Akamai have 30%+ traffic on HTTP/3
  - Especially beneficial for mobile users on flaky networks
- Migration is mostly transparent: same URLs, same APIs, faster transport
  - The browser and server negotiate the highest version both support via ALPN
- Choose based on infrastructure: HTTP/3 needs UDP-friendly networks (some corporate firewalls block it)
  - Most CDNs auto-upgrade and fall back gracefully
[Visual suggestion: Bar chart showing page load time for 1.1 vs 2 vs 3 on a 100-asset page, plus a globe with major adopters]

---

### Slide 20: REST API - Concept Introduction
- REST (Representational State Transfer) is an architectural style for HTTP APIs
  - Coined by Roy Fielding in 2000; not a protocol, just a set of conventions
- Core principles: client-server, stateless, cacheable, uniform interface, layered, code-on-demand (optional)
  - Statelessness means each request contains everything the server needs to process it
- Resource-oriented: every "thing" gets a URL; verbs are HTTP methods
  - /users, /users/42, /users/42/orders are nouns; GET/POST/PUT/DELETE are verbs
- Exists to standardize CRUD APIs and leverage HTTP's existing semantics
  - You get caching, content negotiation, status codes, and tooling for free
- Dominates web APIs because it's simple, debuggable, and composable
  - Stripe, GitHub, Twitter, Slack all expose REST-ish APIs as their primary interface
[Visual suggestion: URL anatomy - /api/v1/users/42/orders?status=pending broken into resource path components]

---

### Slide 21: REST URL Design and Conventions
- Use plural nouns for collections: /users, /orders, /products
  - Singular for top-level when it makes sense: /me, /health
- Use IDs for specific resources: /users/42 not /user/42 or /getUser?id=42
  - Hierarchy reflects relationships: /users/42/orders/100/items
- Filter, sort, paginate via query parameters: ?status=active&sort=-created_at&page=2
  - Don't put filters in the path; that's a different resource
- Avoid verbs in URLs; the HTTP method IS the verb
  - Bad: POST /createUser; Good: POST /users
- For non-CRUD actions, use sub-resources or be pragmatic: POST /orders/42/cancel
  - Pure REST purists hate this; everyone does it anyway
[Visual suggestion: Two columns - "Bad URL" vs "Good URL" with examples like /getUser?id=42 -> GET /users/42]

---

### Slide 22: REST Idempotency Deep Dive
- Idempotent: calling N times has the same effect as calling once
  - GET, PUT, DELETE, HEAD, OPTIONS are idempotent by spec
- POST is NOT idempotent: each call creates a new resource
  - POST /orders twice creates two orders; this is why double-clicking "Submit" is dangerous
- Idempotency enables safe retries on network failures
  - Client doesn't know if request succeeded -> retry it -> server handles duplicate gracefully
- For non-idempotent operations, use idempotency keys (Stripe-style)
  - Client generates a UUID, server stores it for 24h, returns cached response on duplicate
- Idempotency is the foundation of reliable distributed systems
  - Without it, every retry risks double-charging customers or duplicating orders
[Visual suggestion: Network failure scenario - client times out, retries, server recognizes idempotency key and returns same response]

---

### Slide 23: REST vs SOAP Comparison
- REST: lightweight, JSON, HTTP-native, easy to debug, mobile-friendly
  - Build a REST API in 10 minutes; debug it with curl
- SOAP: heavyweight, XML, protocol-agnostic, strong contracts via WSDL
  - Verbose envelopes, built-in security (WS-Security), formal schemas
- REST won for public web APIs; SOAP persists in enterprise/legacy
  - Banks, payment processors, government systems still ship SOAP endpoints
- SOAP advantages: built-in transactions, formal contracts, language-agnostic codegen
  - When you need ACID across services or strict typing, SOAP/WSDL still has merit
- REST advantages: simpler, cacheable, lower bandwidth, better tooling, ubiquitous
  - For 95% of new APIs in 2020+, REST (or gRPC, or GraphQL) wins
[Visual suggestion: Side-by-side request - REST showing tiny JSON, SOAP showing 50-line XML envelope for the same operation]

---

### Slide 24: REST Pagination, Filtering, and Versioning
- Pagination strategies: offset (?page=2&size=20), cursor (?cursor=eyJpZCI6MTAwfQ), keyset (?after_id=100)
  - Cursor and keyset are stable under inserts; offset breaks when data shifts
- Filtering: query params for simple cases (?status=active), JSON body for complex queries
  - GraphQL solves complex querying entirely; REST gets awkward past 4-5 filter dimensions
- Versioning: URL (/v1/users), header (Accept: application/vnd.api+json;version=1), query (?v=1)
  - URL versioning is most common because it's visible and easy to route
- Backward compatibility matters: never break v1 while v2 exists
  - Add fields freely; renaming or removing fields breaks clients
- Deprecation strategy: announce, dual-run, sunset with clear timelines
  - Stripe gives 1+ year notice and pins API versions per account for stability
[Visual suggestion: Pagination comparison showing offset-based "page 2 of 10" vs cursor-based "next: abc123"]

---

### Slide 25: REST API - Real Product Examples
- Stripe API: gold standard REST design with idempotency keys, versioning, deep filtering
  - GET /v1/charges?limit=10&customer=cus_123; uses cursor pagination via starting_after
- GitHub API v3: classic REST with hypermedia links and rate limit headers
  - GET /repos/{owner}/{repo}/issues; includes Link headers for pagination
- Twilio, Twitter v1.1, Slack Web API: similar RESTful patterns
  - Resource URLs, HTTP methods, JSON payloads, OAuth tokens
- Common patterns: API keys in Authorization header, JSON request/response, rate limit headers
  - X-RateLimit-Remaining and Retry-After are de facto standards
- These APIs demonstrate REST's strengths: discoverability, cacheability, ecosystem support
  - Every language has a great HTTP client; Postman/Insomnia work out of the box
[Visual suggestion: Logos of Stripe, GitHub, Twilio, Slack with example endpoints listed below each]

---

### Slide 26: REST Diagram - Request/Response Lifecycle
- Client -> DNS lookup -> TCP/TLS handshake -> HTTP request -> server
  - Modern clients reuse connections; first request pays handshake cost, subsequent ones don't
- Server -> auth middleware -> rate limiter -> router -> controller -> database -> response builder
  - Each layer can short-circuit (401 from auth, 429 from rate limiter)
- Response flows back: HTTP response -> CDN cache check -> client
  - Cacheable responses get stored at edge; subsequent requests skip the origin
- Status code, headers, body all carry information for the client
  - Client parses JSON, reads pagination links, updates UI
- Understanding this lifecycle helps debug latency: where is the time going?
  - DNS? TLS? Server-side? Database? Network? Different fixes for different bottlenecks
[Visual suggestion: Sequence diagram from browser to CDN to LB to app server to DB and back, with latency annotations]

---

### Slide 27: RPC - Concept Introduction
- RPC (Remote Procedure Call) lets you call a function on another machine like it's local
  - clientStub.getUser(42) feels like a local call but executes on a remote server
- Hides network details behind a function call abstraction
  - Marshaling, network I/O, error handling all wrapped by generated stub code
- Older than HTTP: ONC RPC (Sun, 1984), CORBA, Java RMI all predate REST
  - The idea is fundamental; modern incarnations (gRPC, Thrift) refined the execution
- Exists because thinking in functions is more natural than thinking in resources
  - For service-to-service calls, "createOrder(customer, items)" feels right; REST forces noun-shaping
- The illusion is leaky: networks fail, latency exists, partial failures happen
  - Fallacies of distributed computing - treating remote calls as local is the original sin
[Visual suggestion: Two boxes labeled "Client" and "Server" with a function call arrow that conceptually crosses both]

---

### Slide 28: gRPC Deep Dive
- gRPC = Google RPC: HTTP/2 transport, Protocol Buffers serialization, multi-language codegen
  - Open-sourced by Google in 2015; built on internal Stubby system
- Protobuf .proto files define services and messages; tooling generates clients and servers
  - One source of truth; generated code is type-safe in Go, Java, Python, C++, etc.
- Four streaming modes: unary, server-streaming, client-streaming, bidirectional
  - Replaces REST + WebSockets + polling with a single protocol
- HTTP/2 multiplexing means one connection handles many concurrent calls
  - Header compression and binary framing cut overhead vs JSON over HTTP/1.1
- Built-in deadlines, cancellation, retries, load balancing primitives
  - Production-grade out of the box; cloud providers offer managed gRPC routing
[Visual suggestion: .proto schema -> code generator -> client stub + server skeleton in 4 different languages]

---

### Slide 29: gRPC vs REST - When to Use Each
- gRPC: internal microservice-to-microservice communication
  - Strong typing, low latency, streaming, polyglot teams; Netflix, Square, Uber use it heavily
- REST: public APIs, browser clients, simple CRUD
  - Universal tooling, debuggable with curl, no special client libraries
- gRPC needs HTTP/2; some networks/proxies still struggle (improving fast)
  - gRPC-Web bridges browsers but adds a proxy hop
- REST is easier to evolve loosely; gRPC enforces stricter contracts
  - Trade-off: REST flexibility vs gRPC safety
- Many companies run both: REST at the edge for clients, gRPC internally between services
  - GraphQL is sometimes the third option for complex client queries
[Visual suggestion: Architecture diagram - mobile/browser -> REST gateway -> gRPC mesh of microservices -> databases]

---

### Slide 30: Protobuf vs JSON
- Protobuf is a binary, schema-first serialization format
  - Fields tagged by integer; no field names on the wire; schema required to decode
- JSON is text, schema-less, self-describing
  - Human-readable; works without any external definition; ubiquitous tooling
- Size: Protobuf typically 30-70% smaller than equivalent JSON
  - No quotes, no field names, integers packed efficiently, repeated fields delta-encoded
- Speed: Protobuf parses 5-10x faster than JSON in most languages
  - Generated parsers walk fixed offsets; JSON parsers tokenize and allocate strings
- Trade-off: JSON debuggable in any browser/curl; Protobuf needs schema and tools to inspect
  - Use Protobuf when bandwidth/CPU matter; JSON when human inspection matters
[Visual suggestion: Same User object shown as 200-byte JSON next to 80-byte Protobuf hex dump, with parse-time benchmark bars]

---

### Slide 31: gRPC Diagram - Streaming Modes
- Unary: one request, one response (like REST GET)
  - getUser(id) -> User
- Server streaming: one request, stream of responses
  - listEvents(filter) -> stream of Event messages; great for log tailing, news feeds
- Client streaming: stream of requests, one response
  - uploadChunks(stream of Chunk) -> UploadResult; useful for file uploads, batch ingestion
- Bidirectional streaming: both sides stream independently
  - chat(stream of Message) -> stream of Message; perfect for real-time collaboration
- All four modes share one HTTP/2 connection and contract
  - Replaces multiple protocols with a unified streaming model
[Visual suggestion: 2x2 grid showing four streaming modes with arrows representing message flow direction]

---

### Slide 32: RPC Real Examples and Trade-offs
- Google internal: Stubby (gRPC's predecessor) for thousands of microservices
  - Every internal API call is RPC; REST is rare internally
- Kubernetes: gRPC for kubelet <-> API server, etcd <-> peers
  - High-frequency control plane traffic benefits from binary efficiency
- Etsy, Square, Lyft: gRPC for service mesh; REST/GraphQL at the edge
  - Internal latency drops 30-50% vs JSON-over-HTTP/1.1
- Trade-offs: harder to debug (need grpcurl or BloomRPC), browser support requires gRPC-Web
  - Tooling has matured but still less ubiquitous than HTTP/JSON
- Choose RPC for service mesh; REST for public APIs; both for hybrid architectures
  - The right answer is rarely one protocol everywhere
[Visual suggestion: Real-world stack - mobile app -> REST -> API gateway -> gRPC -> 50 microservices]

---

### Slide 33: WebSockets - Concept Introduction
- WebSocket is a full-duplex, persistent connection over a single TCP socket
  - After an HTTP-based handshake (Upgrade: websocket), the connection becomes bidirectional
- Both sides can send messages anytime without waiting for a request
  - Server pushes events to client; client sends commands to server; symmetric
- Designed for real-time, low-latency communication
  - Avoids the cost of repeatedly opening HTTP connections or polling
- Works through most firewalls because it starts as HTTP
  - Standard ports 80/443; survives most corporate proxies (with WSS for TLS)
- Exists because HTTP's request-response model is wrong for real-time apps
  - Before WebSockets, "real-time" meant ugly hacks like long polling or Comet
[Visual suggestion: HTTP handshake transitioning into a persistent bidirectional pipe with messages flowing both ways]

---

### Slide 34: WebSockets vs Polling vs SSE
- Short polling: client requests every N seconds; simple but wasteful
  - 60 requests/min for sub-second freshness; horrendous server load and battery drain
- Long polling: client request hangs until server has data, then immediately reconnects
  - Lower waste than short polling but still HTTP overhead per message; complex on server
- SSE (Server-Sent Events): one-way server-to-client over HTTP
  - Simpler than WebSockets; built-in reconnection; client cannot push (uses separate HTTP for that)
- WebSocket: full-duplex, lowest latency, persistent connection
  - Best for chat, collaborative editing, multiplayer games
- Choose based on traffic pattern: SSE for read-heavy feeds, WebSocket for interactive
  - Stock tickers and news feeds work great with SSE; chat needs WebSockets
[Visual suggestion: Four timelines comparing short polling, long polling, SSE, and WebSocket - showing message latency and connection count]

---

### Slide 35: WebSockets - Real Product Examples
- Discord: WebSocket for voice channel signaling, presence, chat
  - Millions of concurrent connections; uses Erlang/Elixir for connection-heavy workloads
- Slack: WebSocket (RTM API) for real-time message delivery
  - Now mostly Events API + WebSocket fallback; chat updates feel instant
- Trading platforms (Robinhood, Coinbase): WebSocket for market data streams
  - Sub-millisecond price updates require persistent push connections
- Collaborative editors (Google Docs, Figma, Notion): WebSocket for OT/CRDT sync
  - Every keystroke flows over WebSocket so other users see edits in real time
- Multiplayer games (Agar.io, browser games): WebSocket for game state
  - When UDP isn't available (browsers), WebSocket is the lowest-latency option
[Visual suggestion: Product logos with their use case - Discord (voice signaling), Figma (cursor sync), Robinhood (price updates)]

---

### Slide 36: WebSocket Trade-offs and Scaling
- Stateful connections complicate horizontal scaling
  - Load balancers need sticky sessions or pub/sub backplane (Redis, Kafka) to broadcast
- Memory and file descriptors per connection
  - 1M connections = 1M sockets in kernel + app memory; tune ulimits and use efficient runtimes
- Reconnection logic is your problem: networks drop, mobile switches Wi-Fi/cellular
  - Implement exponential backoff, resume tokens, deduplication
- No built-in caching, batching, or rate limiting like HTTP
  - You build the application protocol on top - message types, ack semantics, heartbeats
- Choose only when you actually need real-time bidirectional comms
  - For "every minute" updates, polling or SSE is simpler and cheaper
[Visual suggestion: WebSocket scaling architecture - clients -> sticky LB -> WebSocket servers -> Redis pub/sub -> backend]

---

### Slide 37: WebSocket Diagram - Connection Lifecycle
- Step 1: Client sends HTTP request with Upgrade: websocket and Sec-WebSocket-Key headers
  - Looks like normal HTTP, traverses any HTTP-aware infrastructure
- Step 2: Server responds 101 Switching Protocols; TCP connection now speaks WebSocket
  - Transition is irreversible; same socket carries WS frames
- Step 3: Both sides exchange framed messages (text or binary) anytime
  - Frames have small headers; messages can be fragmented across frames
- Step 4: Heartbeats (ping/pong) keep connection alive through NAT timeouts
  - Without them, idle connections die silently after a few minutes
- Step 5: Either side sends close frame; TCP socket teardown follows
  - Graceful close codes communicate intent (1000 normal, 1001 going away, 1006 abnormal)
[Visual suggestion: Sequence diagram - HTTP upgrade handshake, then bidirectional message flow, then close handshake]

---

### Slide 38: GraphQL - Concept Introduction
- GraphQL is a query language and runtime for APIs, developed by Facebook (2012, open-sourced 2015)
  - Client specifies exactly what fields it needs; server returns exactly that
- Single endpoint (typically /graphql); one POST per query regardless of resources fetched
  - Replaces dozens of REST endpoints with one schema-driven entry point
- Strongly typed schema defines all queries, mutations, subscriptions
  - Schema is the contract; tools (GraphiQL, codegen) leverage it for great DX
- Solves over-fetching and under-fetching problems in REST
  - REST: one endpoint returns 50 fields when you need 3 (over-fetching) or you call 5 endpoints to assemble a screen (under-fetching)
- Exists because mobile clients have varied data needs and bandwidth constraints
  - Facebook's mobile teams built it to ship features without backend coupling
[Visual suggestion: GraphQL query alongside its precise JSON response, contrasted with REST returning a bloated payload]

---

### Slide 39: GraphQL vs REST - Trade-offs
- GraphQL flexibility: client-driven queries, no versioning needed (deprecate fields, add new ones)
  - Mobile teams can iterate without waiting for backend endpoint changes
- REST simplicity: HTTP caching just works; CDN-friendly; debuggable
  - GraphQL needs custom caching (Apollo, Relay) since all queries POST to one URL
- GraphQL complexity costs: N+1 query problem, complex authorization, harder to rate limit
  - DataLoader pattern, query depth limits, persisted queries help but add overhead
- REST excels for cacheable resource-oriented APIs; GraphQL excels for complex client UIs
  - Facebook, Shopify, GitHub (v4) ship GraphQL; Stripe, AWS still REST-first
- Choose GraphQL when client data needs vary widely; REST when resources are stable and cacheable
  - Hybrid is common: REST for public API, GraphQL for internal app backend
[Visual suggestion: Decision matrix - "Many clients with different needs?" GraphQL; "Public API with caching?" REST]

---

### Slide 40: GraphQL Real Examples and When to Use
- GitHub API v4: full GraphQL replacement for REST v3
  - One query fetches repo + issues + PRs + comments in a single round trip
- Shopify Storefront API: GraphQL for theme/storefront customization
  - Frontend devs assemble exactly the product data they need
- Facebook, Instagram, Twitter (partially): GraphQL powers mobile apps
  - Bandwidth-constrained mobile clients benefit most from precise queries
- Use GraphQL when: many client types, evolving UIs, complex relationships, mobile bandwidth concerns
  - Avoid when: simple CRUD, public API needing HTTP caching, small team without GraphQL experience
- Subscriptions provide real-time updates over WebSocket
  - GraphQL becomes a unified query/mutation/streaming layer
[Visual suggestion: GitHub GraphQL example - one query fetching repo metadata, last 10 issues, and authors' avatars]

---

### Slide 41: GraphQL Diagram - Query Resolution Flow
- Client sends POST /graphql with query string and variables
  - Single endpoint; query body describes the desired shape of the response
- Server parses query, validates against schema, generates execution plan
  - Type-checks every field, argument, fragment before any resolver runs
- Resolvers fetch each field, often in parallel; DataLoader batches DB calls to avoid N+1
  - getUser resolver triggers, getOrders resolver runs in parallel, etc.
- Server assembles result tree matching query shape; returns JSON
  - Errors are partial: you can get 200 OK with some fields populated and some null with errors[]
- Client merges into normalized cache (Apollo/Relay) for fast subsequent renders
  - Cache invalidation is fine-grained per object/field, not per URL
[Visual suggestion: Flow chart - query -> parse -> validate -> plan -> resolvers (parallel) -> assemble -> JSON]

---

### Slide 42: Section Key Takeaways
- Protocol choice is a system design lever, not a default
  - TCP for reliability, UDP for speed, HTTP/2 or 3 for web, gRPC for microservices, WebSocket for real-time, GraphQL for flexible queries
- Understand L4 vs L7 - it shapes load balancers, proxies, and security tooling
  - "Where do I terminate TLS?" and "Can I route by URL?" both hinge on this
- Idempotency is non-negotiable for reliable distributed systems
  - GET/PUT/DELETE safe to retry; POST needs idempotency keys
- HTTP versions matter: each generation removed a class of latency problem
  - 1.1 -> 2 (multiplexing) -> 3 (no TCP HoL blocking)
- Real-time apps need persistent connections (WebSocket/SSE) - not polling
  - Polling worked in 2005; in 2026 it's a code smell unless data is genuinely low-frequency
[Visual suggestion: One-page cheat sheet with protocol -> use case mapping]

---

### Slide 43: Section Interview Tips
- Always justify protocol choice with concrete trade-offs
  - "I'd use UDP because frame loss is acceptable but 50ms latency is not" beats "UDP is faster"
- Mention HTTP/2 or HTTP/3 when discussing modern web architecture
  - Shows you're current; especially relevant for high-throughput services
- For real-time features, walk the polling -> long polling -> SSE -> WebSocket evolution
  - Demonstrates depth; lets you choose the simplest option that meets the requirements
- Discuss idempotency and retries when designing payment, order, or messaging systems
  - Interviewers love hearing "idempotency key in the request" for POST endpoints
- Know when to NOT use a protocol: GraphQL for simple CRUD, gRPC for browser, WebSocket for low-frequency updates
  - Showing where things break is as valuable as knowing where they shine
[Visual suggestion: Interview script template - "Requirement -> Constraint -> Protocol -> Trade-off acknowledged"]

---

### Slide 44: Section Common Pitfalls
- Defaulting to REST for everything ignoring streaming or low-latency needs
  - "We just polled the API every 500ms" - now your server is melting
- Ignoring TCP head-of-line blocking when discussing HTTP/2 performance
  - HTTP/2 doesn't fully solve HoL; HTTP/3 does (interview gotcha)
- Treating remote calls as local (RPC fallacy)
  - Network failures, partial failures, timeouts must be designed for explicitly
- Using WebSockets when SSE or long polling would suffice
  - Persistent bidirectional connections are expensive; use them when you actually need bidi
- Forgetting authentication, rate limiting, and observability at the protocol layer
  - Every protocol needs auth (Bearer tokens, mTLS), throttling (429s, leaky buckets), and tracing (X-Request-ID)
- Not versioning APIs from day one
  - "We'll add /v1 later" usually means breaking every existing client when "later" arrives
[Visual suggestion: "Avoid these traps" warning signs with each pitfall and its consequence]
