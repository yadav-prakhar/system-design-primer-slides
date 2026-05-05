## Section 10: Security
## Section 11: Advanced Topics and Interview Framework

---

# SECTION 10: SECURITY

---

## Topic 1: Security Fundamentals

### Slide 1: Security Fundamentals - Concept Introduction
- Security is not a feature, it is a property of the entire system
  - Every component, layer, and human interaction can be an attack surface
- Three foundational pillars: principles, mechanisms, and defenses
  - Principles guide design, mechanisms enforce policy, defenses respond to attacks
- Goal: protect data, users, and infrastructure from unauthorized access or harm
  - While maintaining usability and performance for legitimate users
- Security is continuous, not one-time
  - Threats evolve; defenses must evolve with them
- Real example: Equifax 2017 breach exposed 147M records due to one unpatched library
  - A single weak link compromised the entire fortress

[Visual suggestion: Concentric castle walls labeled "Network → Host → Application → Data" with arrows showing attacks bouncing off multiple layers]

---

### Slide 2: Defense in Depth - Deep Explanation
- Defense in depth means layered security controls so no single failure is catastrophic
  - If one layer fails, others still protect the asset
- Layers typically include: perimeter (firewall, WAF), network (VPC, segmentation), host (OS hardening), application (input validation, authz), data (encryption)
  - Each layer is independent and uses different mechanisms
- Assume breach: design as if attackers will get past the outer wall
  - Internal services should still authenticate, authorize, and log
- Redundant controls: multiple firewalls, multiple authentication factors, multiple logging systems
  - Attacker must defeat every layer to succeed
- Real example: AWS uses VPC + Security Groups + NACLs + IAM + KMS as overlapping layers
  - Compromising one does not grant access to data

[Visual suggestion: Onion diagram with layers labeled outer-to-inner: WAF, Firewall, IDS, Auth, Encryption, Audit Logs]

---

### Slide 3: CIA Triad - The Three Pillars
- Confidentiality: only authorized parties can read data
  - Achieved via encryption, access control, authentication
- Integrity: data is not tampered with in transit or at rest
  - Achieved via hashing, digital signatures, checksums, version control
- Availability: legitimate users can access the system when needed
  - Achieved via redundancy, DDoS protection, rate limiting, failover
- Trade-offs exist between the three pillars
  - Heavy encryption can hurt availability; aggressive rate limiting can hurt availability for legitimate users
- Real example: Banking app must keep balance secret (C), unalterable (I), and accessible 24/7 (A)
  - Failure in any one pillar destroys trust

[Visual suggestion: Equilateral triangle with vertices labeled Confidentiality, Integrity, Availability; center labeled "Security"]

---

### Slide 4: Authentication vs Authorization - Example/Intuition
- Authentication (AuthN) answers: who are you?
  - Verifies identity using passwords, tokens, biometrics, certificates
- Authorization (AuthZ) answers: what are you allowed to do?
  - Determines permissions, roles, scopes, resource access
- Order matters: authenticate first, then authorize
  - Cannot grant permissions without knowing the identity
- Common mistake: conflating the two leads to security holes
  - A logged-in user is not automatically allowed to access every resource
- Real example: Boarding a plane - showing your ID is authentication, your ticket class is authorization
  - ID gets you in the airport; ticket determines which seat

[Visual suggestion: Two-step gate diagram. Gate 1: "Who are you?" with ID check. Gate 2: "What can you do?" with permission badge check]

---

### Slide 5: Principle of Least Privilege - Diagram
- Grant the minimum permissions needed to perform a task, nothing more
  - Reduces blast radius if credentials are compromised
- Apply to users, services, processes, and database accounts
  - Microservice X should not have DROP TABLE privilege if it only reads
- Time-bound access: temporary elevation when needed, revoked after
  - JIT (just-in-time) access for production debugging
- Role-based access control (RBAC) and attribute-based access control (ABAC) operationalize this principle
  - Roles bundle permissions; attributes add context (time, location, resource tag)
- Real example: AWS IAM roles for EC2 instances scoped to specific S3 buckets and actions
  - A compromised instance cannot enumerate or delete unrelated buckets

[Visual suggestion: Org chart where each role has a small key icon labeled with only the specific permissions it holds; CEO does NOT have all keys]

---

### Slide 6: Security Fundamentals - Trade-offs
- Security vs Usability: stronger controls add friction
  - 2FA improves security but slows login; balance per risk level
- Security vs Performance: encryption and validation cost CPU
  - TLS termination at edge; selective encryption of sensitive fields
- Security vs Cost: dedicated security teams, audits, tooling are expensive
  - Match investment to threat model and data sensitivity
- Security vs Developer Velocity: strict review gates slow shipping
  - Automate scans (SAST, DAST, dependency scanning) into CI/CD
- Real example: Google BeyondCorp replaced VPN with continuous device + user verification
  - Higher security with better UX, but multi-year investment

[Visual suggestion: Four-quadrant chart with security on Y-axis and usability/performance/cost/velocity on X-axis showing balance points]

---

## Topic 2: Encryption

### Slide 7: Encryption - Concept Introduction
- Encryption transforms readable data (plaintext) into unreadable ciphertext using a key
  - Only those with the right key can reverse it
- Two main families: symmetric (one shared key) and asymmetric (key pair)
  - Each has different strengths, costs, and use cases
- Encryption protects confidentiality; signing protects integrity and authenticity
  - Often combined in real protocols
- Encryption is mathematics, not obscurity
  - Algorithms are public; security depends on key secrecy
- Real example: WhatsApp E2EE uses Signal Protocol so even WhatsApp servers cannot read messages
  - Encryption shifts trust from servers to math

[Visual suggestion: "HELLO" + key icon → AES box → "8x#2K9z" with locked padlock icon]

---

### Slide 8: Symmetric Encryption (AES) - Deep Explanation
- Same key encrypts and decrypts; both parties must share it secretly
  - Fast, suitable for bulk data
- AES (Advanced Encryption Standard) is the modern default
  - 128-bit and 256-bit key sizes; hardware-accelerated on modern CPUs
- Modes matter: AES-GCM provides authenticated encryption (confidentiality + integrity)
  - Avoid ECB; use GCM or CBC with HMAC
- Key distribution is the hard problem
  - How do two parties agree on a shared key without anyone intercepting it?
- Real example: AWS S3 server-side encryption uses AES-256-GCM at rest
  - Throughput is gigabytes per second per core

[Visual suggestion: Alice and Bob each holding identical key icons, both encrypting/decrypting a shared lockbox]

---

### Slide 9: Asymmetric Encryption (RSA) - Deep Explanation
- Two mathematically linked keys: public (share freely) and private (keep secret)
  - Encrypt with public, decrypt with private; or sign with private, verify with public
- RSA, ECC (Elliptic Curve), Ed25519 are common asymmetric algorithms
  - ECC offers same security with smaller keys (256-bit ECC ≈ 3072-bit RSA)
- 100-1000x slower than symmetric; used for key exchange and signatures, not bulk data
  - Encrypt a symmetric session key with RSA, then use AES for the conversation
- Solves key distribution: anyone can send you encrypted data using your public key
  - Foundation of TLS, SSH, signed software updates
- Real example: GitHub SSH keys use Ed25519/RSA so you authenticate without sharing a password
  - Your private key never leaves your laptop

[Visual suggestion: Alice has lock + private key. Bob downloads Alice's open lock (public key), uses it to lock a box, sends it. Only Alice's private key opens it]

---

### Slide 10: TLS Handshake - Example/Intuition
- TLS combines asymmetric (for key exchange) and symmetric (for data) encryption
  - Best of both worlds: secure setup, fast bulk transfer
- Steps: ClientHello → ServerHello + certificate → key exchange (ECDHE) → Finished → encrypted application data
  - Modern TLS 1.3 reduces this to 1 round trip (1-RTT) or even 0-RTT for resumed sessions
- Server presents an X.509 certificate signed by a Certificate Authority (CA)
  - Browser validates the chain back to a trusted root CA
- Result: a shared symmetric session key both sides can use
  - Forward secrecy ensures past sessions stay safe even if long-term keys leak
- Real example: Browsing https://google.com triggers a full TLS 1.3 handshake in <100ms
  - Padlock icon means handshake succeeded and traffic is encrypted

[Visual suggestion: Sequence diagram: Client ↔ Server with arrows labeled ClientHello, ServerHello+Cert, KeyExchange, Finished, EncryptedData]

---

### Slide 11: End-to-End Encryption (E2EE) - Deep Explanation
- Only the communicating endpoints can read the data
  - Servers in the middle see only ciphertext
- Compare to transport encryption (TLS): server can decrypt and re-encrypt
  - With E2EE, even the service provider cannot read content
- Key management is the hard part: how do users verify each other's keys?
  - Safety numbers, QR code verification, key transparency logs
- Trade-offs: lose server-side features (search, content moderation, multi-device sync becomes complex)
  - Many features must move to client side
- Real example: Signal, WhatsApp, iMessage use E2EE; Gmail does not
  - Your iMessage cannot be subpoenaed from Apple's servers in readable form

[Visual suggestion: Alice → Server (lock icon, server cannot read) → Bob; vs TLS where server has a key icon and can read]

---

### Slide 12: At-Rest vs In-Transit Encryption - Diagram
- In-transit: protects data moving over networks
  - TLS for HTTP, SSH, database connections, service-to-service mTLS
- At-rest: protects data stored on disk, in databases, in backups
  - Disk encryption, database TDE, S3 SSE, encrypted backups
- In-use (emerging): protects data while being processed
  - Confidential computing with Intel SGX, AWS Nitro Enclaves
- Both are required; encrypting only one leaves the other exposed
  - HTTPS without disk encryption: stolen drive reveals everything
- Real example: HIPAA and PCI-DSS require both at-rest and in-transit encryption for sensitive data
  - Auditors check key rotation, algorithm, and scope

[Visual suggestion: Three-state diagram: Disk (lock) → Network pipe (lock) → Memory/CPU (lock with question mark for in-use)]

---

### Slide 13: Encryption - Trade-offs
- Symmetric: fast but key distribution is hard
  - Use for bulk data after key is established
- Asymmetric: solves distribution but slow
  - Use for key exchange, signatures, certificates
- Stronger keys (256 vs 128) cost more CPU; usually negligible on modern hardware
  - Choose 256-bit for long-lived sensitive data
- Key rotation: needed but operationally complex
  - Use envelope encryption: data keys encrypted by master keys (KMS pattern)
- Real example: AWS KMS, Google Cloud KMS, HashiCorp Vault provide managed key rotation and audit
  - Avoid rolling your own crypto; use vetted libraries (libsodium, BoringSSL)

[Visual suggestion: Comparison table - Symmetric vs Asymmetric across columns: Speed, Key Distribution, Use Case, Example Algorithm]

---

## Topic 3: Authentication Mechanisms

### Slide 14: Password Storage - Concept Introduction
- Never store plaintext passwords
  - A breach exposes every user account immediately
- Hash passwords with a slow, salted, adaptive function
  - bcrypt, scrypt, Argon2, PBKDF2 are designed to be slow on purpose
- Salt: random per-user value mixed into the hash
  - Prevents rainbow table attacks; identical passwords produce different hashes
- Pepper: server-side secret added to all hashes (extra defense)
  - Stored separately from the database
- Real example: LinkedIn 2012 breach leaked 117M unsalted SHA-1 password hashes; cracked within days
  - Modern bcrypt with cost factor 12 would have made this far harder

[Visual suggestion: Password "hunter2" + salt "x9k2" → bcrypt(cost=12) → "$2b$12$abc...xyz"; arrow to database row]

---

### Slide 15: Password Hashing - Deep Explanation
- bcrypt: Blowfish-based, configurable cost factor (work parameter)
  - Cost 12-14 typical in 2026; double work each time CPUs get faster
- Argon2: winner of Password Hashing Competition; memory-hard
  - Resists GPU/ASIC cracking better than bcrypt
- Time complexity: each password verification should take ~100-500ms
  - Slow enough to deter brute force, fast enough for UX
- Never use MD5, SHA-1, or fast hashes for passwords
  - GPUs can crack billions of fast hashes per second
- Real example: Dropbox uses bcrypt + AES wrapper; 1Password uses PBKDF2 with high iteration count
  - Defense layers compound

[Visual suggestion: Comparison bar chart - MD5 (1B/sec crack rate, RED), SHA-256 (100M/sec, ORANGE), bcrypt (10K/sec, YELLOW), Argon2 (1K/sec, GREEN)]

---

### Slide 16: JWT (JSON Web Tokens) - Deep Explanation
- Self-contained token: header.payload.signature, base64url encoded
  - Server signs; clients send back; server verifies signature
- Stateless authentication: no server-side session lookup needed
  - Scales horizontally; any server can validate
- Payload contains claims: sub (user id), exp (expiry), iat, custom roles
  - Visible to anyone who has the token; do not put secrets there
- Algorithms: HS256 (shared secret), RS256 (asymmetric, public verification)
  - Use RS256 when verifiers (microservices) should not be able to forge tokens
- Real example: Auth0, Firebase Auth, AWS Cognito issue JWTs for API access
  - Short expiry (15 min) + refresh token pattern is standard

[Visual suggestion: Three colored boxes - Header (red) . Payload (purple) . Signature (cyan) - with decoded JSON beneath each]

---

### Slide 17: OAuth 2.0 / OpenID Connect - Example/Intuition
- OAuth 2.0: authorization framework for delegated access
  - "Let App X access my Google Drive without giving X my Google password"
- OpenID Connect (OIDC): authentication layer on top of OAuth 2.0
  - Adds ID token (JWT) so apps can verify who the user is
- Common flows: Authorization Code (web apps), Authorization Code + PKCE (mobile/SPA), Client Credentials (service-to-service)
  - Implicit flow is deprecated; do not use
- Tokens: access token (short-lived, used in API calls), refresh token (long-lived, used to get new access tokens)
  - Refresh tokens require secure storage
- Real example: "Sign in with Google" on a third-party site uses OIDC + Authorization Code flow
  - You log into Google; site receives ID token + access token

[Visual suggestion: Sequence diagram - User → App → Auth Server → Resource Server with redirect arrows and token exchange]

---

### Slide 18: API Keys vs Session Tokens vs JWT - Diagram
- API Keys: long-lived, identify a client/app, often no user context
  - Best for server-to-server; rotate regularly; never expose in client code
- Session tokens: opaque random IDs stored server-side (Redis, DB)
  - Easy to revoke (delete the row); requires lookup per request
- JWT: signed self-contained tokens, stateless verification
  - Hard to revoke before expiry without a denylist
- Choose based on revocation needs, scale, and trust model
  - Session for sensitive apps with logout; JWT for high-scale stateless APIs
- Real example: Stripe uses API keys; banking apps use sessions; modern SaaS uses JWT + refresh
  - Hybrid: short JWT for API calls + opaque refresh token in HttpOnly cookie

[Visual suggestion: 3-column comparison table - API Key, Session Token, JWT - rows: Storage, Revocation, Stateless?, Use Case]

---

### Slide 19: Authentication - Trade-offs
- Stateless (JWT) vs Stateful (sessions)
  - Stateless scales easier; stateful revokes easier
- Short expiry vs UX friction
  - 15-min access tokens require refresh logic; 24-hour tokens are riskier if stolen
- Single sign-on (SSO) vs independent auth per app
  - SSO simpler for users, single point of failure for security
- MFA strength: SMS (weakest, SIM swap risk) → TOTP apps → Hardware keys (FIDO2/WebAuthn, strongest)
  - Hardware keys phishing-resistant by design
- Real example: GitHub now requires hardware-backed 2FA for contributors to popular repos
  - Phishing-resistant MFA mitigates the most common attack vector

[Visual suggestion: 2x2 matrix - Security strength vs User friction, with MFA methods plotted (SMS, TOTP, Push, Hardware Key)]

---

## Topic 4: Common Vulnerabilities (OWASP Top 10)

### Slide 20: OWASP Top 10 - Concept Introduction
- OWASP Top 10: industry-standard list of most critical web vulnerabilities
  - Updated every 3-4 years based on real breach data
- Categories include: Broken Access Control, Cryptographic Failures, Injection, Insecure Design, Security Misconfiguration
  - Most breaches map to one of these classes
- Defenses are well-known; problem is consistent application across teams and code
  - Automation (SAST, DAST, dependency scanning) catches most common issues
- Awareness is step one; secure-by-default frameworks are step two
  - Modern frameworks prevent many vulnerabilities if used as intended
- Real example: Capital One 2019 breach (100M records) was Broken Access Control via SSRF
  - One misconfigured WAF rule cascaded into a massive breach

[Visual suggestion: Top 10 list as a leaderboard with attack icons next to each, colored red-to-yellow by severity]

---

### Slide 21: SQL Injection - Deep Explanation
- Attacker injects SQL through user input that is concatenated into queries
  - Classic: ' OR '1'='1 in a login form bypasses authentication
- Defense: parameterized queries (prepared statements)
  - Database treats input as data, never as code
- ORMs and query builders use parameterization by default
  - Avoid raw query construction with string concatenation
- Defense in depth: input validation, least-privilege DB accounts, WAF, query allowlists
  - Read-only service should not have write DB credentials
- Real example: 2008 Heartland Payment Systems breach (130M cards) started with SQL injection
  - Parameterized queries would have prevented it entirely

[Visual suggestion: Two code snippets side-by-side - Bad (string concat with red X) vs Good (prepared statement with green check)]

---

### Slide 22: Cross-Site Scripting (XSS) - Deep Explanation
- Attacker injects malicious JavaScript into pages viewed by other users
  - Steals cookies, session tokens, performs actions as victim
- Three types: Stored (in DB), Reflected (in URL), DOM-based (client-side rendering)
  - All exploit insufficient output encoding
- Defense: contextual output encoding (HTML, JS, URL contexts each need different escaping)
  - Modern frameworks (React, Vue) escape by default; danger lies in dangerouslySetInnerHTML
- Content Security Policy (CSP) headers: restrict what scripts can run and where
  - Defense in depth even if encoding fails
- Real example: 2010 Twitter onMouseOver worm spread by self-retweeting via stored XSS
  - Took down Twitter for hours; CSP would have blocked it

[Visual suggestion: Attacker → injects <script> into comment → victim views page → script sends victim cookie to attacker server]

---

### Slide 23: CSRF - Deep Explanation
- Cross-Site Request Forgery: tricks an authenticated user's browser into making unwanted requests
  - Attacker site embeds <img src="https://bank.com/transfer?to=attacker&amount=1000"> while user is logged in
- Defense: CSRF tokens (random per-session value required in form submissions)
  - Server rejects requests missing the token
- Defense: SameSite cookies (Lax or Strict) prevent cross-origin cookie sending
  - Modern browsers default to Lax
- Defense: check Origin / Referer headers for state-changing requests
  - Defense in depth alongside CSRF tokens
- Real example: 2008 Gmail CSRF allowed attackers to add email forwarding rules silently
  - Now all major frameworks ship with CSRF protection by default

[Visual suggestion: Attacker site with hidden form auto-submits to bank.com using victim's logged-in session cookie]

---

### Slide 24: DDoS and MITM - Example/Intuition
- DDoS (Distributed Denial of Service): overwhelm capacity with traffic from many sources
  - Volumetric (bandwidth), protocol (SYN floods), application-layer (HTTP floods)
- DDoS defense: CDN absorption (Cloudflare, Akamai), rate limiting, scrubbing centers, anycast routing
  - Distribute and absorb at the edge before reaching origin
- MITM (Man-in-the-Middle): attacker intercepts/modifies traffic
  - Public WiFi, compromised routers, rogue CAs
- MITM defense: HTTPS everywhere, HSTS headers, certificate pinning for mobile apps
  - HSTS forces browsers to use HTTPS; pinning prevents rogue CA attacks
- Real example: Cloudflare absorbed 26M req/sec DDoS in 2022; GitHub absorbed 1.35 Tbps in 2018
  - Largest attacks now exceed terabits per second

[Visual suggestion: Left - thousands of bots → CDN edge (shield icon) → small filtered traffic → origin. Right - Alice → MITM attacker (eye icon) → Bob with HTTPS lock breaking attack]

---

### Slide 25: Vulnerabilities - Trade-offs
- WAF rules: too strict blocks legitimate users; too loose lets attacks through
  - Tune over time using blocked-request analysis
- Rate limiting: too aggressive impacts power users; too lenient allows abuse
  - Tiered limits per user class
- CSP: strict policy requires refactoring inline scripts/styles
  - Start in report-only mode; tighten incrementally
- Input sanitization vs output encoding: encode at output (context-aware) is safer
  - Sanitization can miss edge cases; encoding is provably safe per context
- Real example: Stripe's WAF was tuned over years using ML on legitimate traffic patterns
  - Continuous tuning is more important than initial config

[Visual suggestion: Risk-vs-friction chart for each defense, plotted as dots]

---

## Topic 5: Rate Limiting

### Slide 26: Rate Limiting - Concept Introduction
- Cap the number of requests a client can make in a time window
  - Protects against abuse, brute force, accidental DoS, runaway scripts
- Without it: a single buggy client can take down your service
  - Or attackers can scrape, enumerate, or exhaust resources
- Apply at multiple layers: edge (CDN, WAF), API gateway, service, database
  - Earlier layers are cheaper; later layers are more granular
- Returns HTTP 429 Too Many Requests with Retry-After header
  - Well-behaved clients back off
- Real example: GitHub API: 5000 req/hour authenticated, 60 req/hour unauthenticated
  - Twitter API rate limits forced developers to design with backoff from day one

[Visual suggestion: Funnel - many requests at top → rate limiter (filter icon) → smaller stream of allowed requests, with rejected ones bouncing off]

---

### Slide 27: Token Bucket Algorithm - Deep Explanation
- Bucket holds N tokens; each request consumes 1 token
  - Tokens refill at rate R per second up to bucket capacity
- Allows bursts up to bucket size, then sustained rate R
  - Friendly to bursty traffic patterns (e.g., page load with many assets)
- Stateless to implement with Redis: store {token_count, last_refill_timestamp}
  - On request: refill based on elapsed time, decrement, accept or reject
- Pros: simple, supports bursts, well-understood
  - Cons: can allow short bursts that overwhelm downstream
- Real example: AWS API Gateway uses token bucket per API key
  - Stripe API uses token bucket with burst + steady-state limits

[Visual suggestion: Bucket icon with falling drops (tokens) at rate R, requests on the right scooping tokens to enter the system]

---

### Slide 28: Leaky Bucket Algorithm - Deep Explanation
- Requests enter a queue (bucket); processed at constant rate R (drain rate)
  - If bucket overflows, new requests are dropped or rejected
- Smooths bursts into a steady stream
  - Output rate is always constant regardless of input pattern
- Stricter than token bucket: no burst allowance
  - Better for downstream systems that cannot tolerate spikes
- Trade-off: legitimate burst users (page loads, batch ops) get throttled
  - Less friendly to UX
- Real example: Network routers use leaky bucket for QoS shaping
  - Cellular carriers use leaky bucket variants for fair usage

[Visual suggestion: Bucket with hole at bottom, water dripping out at constant rate R, top inflow showing variable bursts that overflow when bucket fills]

---

### Slide 29: Fixed Window vs Sliding Window - Example/Intuition
- Fixed window: count requests in [00:00-00:59], reset at top of each minute
  - Simple but allows 2x burst at window boundary (59 reqs at 00:59 + 60 at 01:00)
- Sliding window log: track timestamp of each request, count in last 60 seconds
  - Accurate but expensive (memory grows with request volume)
- Sliding window counter: weighted blend of current and previous fixed windows
  - Approximates sliding log with constant memory
- Choose based on accuracy vs memory: fixed (cheapest), sliding counter (balanced), sliding log (most accurate)
  - Most APIs use sliding counter
- Real example: Cloudflare uses sliding window counters across global edge
  - Redis sorted sets implement sliding window log easily

[Visual suggestion: Three timeline bars - Fixed (clear minute boundaries), Sliding Log (every dot tracked), Sliding Counter (smooth gradient)]

---

### Slide 30: Rate Limiting - Where to Apply
- API gateway / reverse proxy: protect all backend services uniformly
  - Kong, Envoy, Nginx, AWS API Gateway, Cloudflare
- CDN edge: absorb global traffic before it reaches origin
  - Cheapest place to drop bad traffic
- Application layer: per-endpoint rules (e.g., login is stricter than search)
  - Per-feature granularity
- Distributed store: Redis with atomic INCR + EXPIRE for shared counters across nodes
  - Or local in-memory + gossip for low latency
- Real example: GitHub layers - Cloudflare → HAProxy → Rails app, each with different limits
  - Login endpoint: 10/min/IP; API: 5000/hour/token; webhooks: 1000/min

[Visual suggestion: Layered architecture - User → CDN (limit A) → Gateway (limit B) → Service (limit C) → DB]

---

### Slide 31: Per-User vs Per-IP vs Per-Endpoint - Diagram
- Per-IP: blocks abusive networks; problem with NAT, mobile carriers, corporate proxies
  - Many legitimate users behind one IP
- Per-user (authenticated): fair allocation per identity
  - Requires authentication; does not protect login itself
- Per-endpoint: tighter limits on sensitive ops (login, password reset, payment)
  - Defends against credential stuffing
- Per-API-key: B2B fairness across customers
  - Combine with quota for billing tiers
- Real example: Login endpoint - 5/min/IP + 10/hour/account combined
  - Password reset - 3/hour/account to prevent enumeration

[Visual suggestion: Multi-dimensional table with rows IP/User/Endpoint/Key and columns showing example limits and use cases]

---

### Slide 32: Rate Limiting - Trade-offs
- Strict limits: better protection, worse UX for power users
  - Provide tiered limits (free, paid, enterprise)
- Distributed counters (Redis) add latency vs local counters that are inconsistent
  - Approximate algorithms (count-min sketch) for high-scale eventual consistency
- Hard reject (429) vs queueing
  - Queue for short bursts; reject when sustained
- Synchronous vs asynchronous tracking
  - Async (post-request log + tally) faster but allows brief overage
- Real example: Discord uses Redis-backed sliding window with per-route limits and bucket sharing
  - Returns rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset) so clients self-throttle

[Visual suggestion: Trade-off scale - Accuracy vs Latency vs Cost with each algorithm placed]

---

## Section 10 Wrap-Up

### Slide 33: Security - Key Takeaways
- Defense in depth: layer controls so no single failure is catastrophic
  - Perimeter, network, host, application, data
- CIA triad guides every security decision
  - Confidentiality, Integrity, Availability
- Authentication ≠ Authorization: verify identity, then check permissions
  - Apply least privilege everywhere
- Use vetted crypto: AES-GCM for symmetric, RSA/Ed25519 for asymmetric, bcrypt/Argon2 for passwords
  - Never roll your own
- Rate limiting protects against abuse, brute force, and accidental overload
  - Apply at multiple layers with appropriate algorithms

[Visual suggestion: One-page cheat sheet with 5 quadrants - Principles, Encryption, Auth, Vulnerabilities, Rate Limiting]

---

### Slide 34: Security - Interview Tips
- Always ask: who can access this data? What if their credentials leak?
  - Threat modeling shows senior thinking
- Mention defense in depth even when asked about a single layer
  - "I would also add..." demonstrates breadth
- For auth questions, contrast JWT vs sessions explicitly with trade-offs
  - Revocation, scale, complexity
- For password storage, never accept "we hash with SHA-256"
  - Push for bcrypt/Argon2 with appropriate cost factor
- Real example to drop: "Like the Capital One breach, SSRF + over-permissive IAM can cascade"
  - Anchors abstract advice in real consequences

[Visual suggestion: Interview Q&A flowchart - "How would you store passwords?" → answer + follow-up branches]

---

### Slide 35: Security - Common Pitfalls
- Storing JWTs in localStorage where XSS can steal them
  - Use HttpOnly cookies for sensitive tokens
- Forgetting to revoke refresh tokens on logout or password change
  - Maintain a revocation list keyed on jti
- Treating TLS as sufficient and skipping at-rest encryption
  - Both are required for sensitive data
- Logging passwords, tokens, or PII in plaintext
  - Redact before logging; review log pipelines for sensitive fields
- Hardcoding secrets in source code or config files
  - Use secret managers (Vault, AWS Secrets Manager) with rotation

[Visual suggestion: "Wall of shame" - 5 anti-patterns crossed out with red X marks, correct pattern next to each]

---

# SECTION 11: ADVANCED TOPICS AND INTERVIEW FRAMEWORK

---

## Topic 6: Consistent Hashing

### Slide 36: Consistent Hashing - Concept Introduction
- A hashing scheme where adding/removing nodes only remaps a small fraction of keys
  - Traditional hash(key) % N remaps almost all keys when N changes
- Maps both keys and nodes onto a circular hash ring (0 to 2^32-1)
  - Each key is owned by the next node clockwise on the ring
- Solves the rebalancing problem in distributed systems
  - When a node fails or scales out, only neighboring keys move
- Foundation for distributed caches, sharded databases, CDN routing
  - Critical for elastic scale without massive data movement
- Real example: Amazon DynamoDB partitions data using consistent hashing across thousands of nodes
  - Adding a node moves ~1/N of keys, not all of them

[Visual suggestion: Circle ring with 5 node icons placed around it; colored arcs showing the keyspace each node owns]

---

### Slide 37: Consistent Hashing - Deep Explanation
- Hash function maps both nodes (by IP/ID) and keys to points on the ring
  - Same hash function for both
- Each key is assigned to the first node found going clockwise from the key's position
  - O(log N) lookup using a sorted structure (TreeMap, skip list)
- When node N is added: only keys between previous node and N are remapped
  - Average 1/N of keys move
- When node N is removed: its keys redistribute to the next clockwise node
  - Hot spot risk if removed node had a large arc
- Real example: Memcached clients (ketama hashing) use consistent hashing across servers
  - Client-side decision; no server coordination needed

[Visual suggestion: Before/after ring diagrams. Before: 3 nodes with arcs A, B, C. After adding node D: only part of arc B is reassigned to D]

---

### Slide 38: Virtual Nodes (vnodes) - Example/Intuition
- Problem with naive consistent hashing: uneven distribution due to hash randomness
  - One node may own a much larger arc than others
- Solution: each physical node is represented by many virtual nodes (e.g., 100-200 per physical)
  - Each vnode is hashed independently to a position on the ring
- Result: arcs average out, distribution becomes near-uniform
  - Adding/removing a node spreads keys across many vnode boundaries
- Heterogeneous nodes: powerful nodes get more vnodes, weak nodes fewer
  - Weight by capacity
- Real example: Cassandra defaults to 256 vnodes per physical node
  - DynamoDB, Riak, ScyllaDB all use vnodes

[Visual suggestion: Two rings - Left: 3 nodes with uneven arcs (red highlights). Right: 3 nodes with 100 vnodes each, evenly distributed dots]

---

### Slide 39: Consistent Hashing - Diagram
- Ring layout with hash space 0 to 2^32-1
  - Wraps around; max value connects to 0
- Nodes placed at hash(node_id) positions
  - Clients compute hash(key) and walk clockwise to find owner
- Replication: store on next K nodes clockwise for fault tolerance
  - Quorum reads/writes across replicas
- Lookup data structure: sorted map of node positions
  - findCeiling(hash(key)) returns owning node
- Real example: CDN edge selection - hash(URL) → walk ring → nearest healthy edge
  - Removing a failed edge only affects its neighbors

[Visual suggestion: Detailed ring with hash positions labeled, key arrows pointing clockwise to their owning nodes, replication arrows to next 2 nodes]

---

### Slide 40: Consistent Hashing - Trade-offs
- vs Modulo hashing: minimal remapping when nodes change (huge win)
  - Modulo remaps ~all keys when N changes
- vs Range partitioning: better load balance for random keys
  - Range better for ordered scans
- Lookup is O(log N), slightly more expensive than O(1) modulo
  - Negligible at typical N
- Hot keys still possible: if one key gets 10x traffic, its node burns
  - Pair with caching or hot-key replication
- Real example: DynamoDB uses consistent hashing + adaptive capacity to handle hot partitions
  - Splits hot partitions automatically

[Visual suggestion: 3-column table - Modulo, Consistent Hashing, Consistent Hashing+vnodes - rows: Remap %, Distribution, Complexity]

---

## Topic 7: Bloom Filters

### Slide 41: Bloom Filters - Concept Introduction
- Probabilistic data structure for set membership testing
  - "Is X in this set?" with very small memory footprint
- No false negatives (if it says no, it really is not there)
  - Possible false positives (it may say yes when it is not)
- Trade space for certainty: ~10 bits per element for ~1% false positive rate
  - Compare to a hash set storing full elements (8 bytes each + overhead)
- Cannot enumerate elements or delete from a standard Bloom filter
  - Use Counting Bloom Filter for deletes
- Real example: Google Bigtable, Cassandra, RocksDB use Bloom filters to skip disk lookups
  - Saves expensive disk seeks for keys that definitely do not exist

[Visual suggestion: Bit array with hash functions H1, H2, H3 each setting bits; query "is X in set?" checking same bits]

---

### Slide 42: Bloom Filters - Deep Explanation
- Bit array of m bits + k independent hash functions
  - Insert: hash element with each function, set those k bit positions to 1
- Query: hash element, check all k positions
  - All 1 → "probably in set"; any 0 → "definitely not in set"
- False positive rate ≈ (1 - e^(-kn/m))^k
  - Optimize k = (m/n) * ln(2) for given m, n
- Tunable: choose m and k based on expected n and acceptable FP rate
  - 1% FP rate ≈ 9.6 bits per element with 7 hash functions
- Real example: Google Chrome's safe browsing uses Bloom filter of malicious URLs
  - 1MB filter checks billions of URLs locally before contacting Google

[Visual suggestion: Math formulas + bit array with 3 hashes mapping to positions, showing both insert and query]

---

### Slide 43: Bloom Filters - Use Cases
- Cache filters: "Is this URL cached?" before doing expensive lookup
  - Avoid wasted cache miss round trips
- Database read optimization: skip SSTable disk reads for absent keys
  - LevelDB, RocksDB, Cassandra, HBase
- Username/email availability check: fast pre-check before authoritative DB query
  - Filter rejects most negatives instantly
- Distributed systems: gossiping set membership without sending full sets
  - DHT, peer-to-peer networks
- Real example: Bitcoin SPV nodes use Bloom filters to ask peers for relevant transactions
  - Keeps wallet privacy reasonable while reducing bandwidth

[Visual suggestion: 4-quadrant grid with use cases as icons - Cache, Database, Username, P2P]

---

### Slide 44: Bloom Filters - Example/Intuition
- Imagine a small library with 1M books and a "do we have this book?" desk
  - A naive search of the catalog takes seconds
- Bloom filter is a compact summary: a 1.2 MB bit array answers in microseconds
  - "Definitely not in library" → save the user a wasted catalog search
  - "Probably in library" → check catalog to confirm
- ~1% of "yes" answers are wrong, but no "no" answer is ever wrong
  - Acceptable when false positive cost is low (an extra DB call)
- Memory savings: 1M book titles × 100 bytes ≈ 100MB; Bloom filter ≈ 1.2MB
  - 80x reduction
- Real example: Akamai uses Bloom filters at edge to filter "one-hit-wonder" URLs from cache
  - Only cache items requested 2+ times; saves cache space dramatically

[Visual suggestion: Library counter - "yes" stamp (green with small "1% FP" footnote), "no" stamp (red, 100% accurate)]

---

### Slide 45: Bloom Filters - Trade-offs
- Pros: tiny memory, fast O(k) operations, no full element storage
  - Excellent for negative lookups
- Cons: false positives, no deletion, fixed size at creation
  - Cannot enumerate elements
- Variants: Counting Bloom Filter (deletes via counters), Scalable Bloom Filter (grows dynamically)
  - Cuckoo filter offers similar features with deletion support
- Sizing matters: too small → high FP rate; too large → wastes memory
  - Plan for target n carefully
- Real example: Cassandra rebuilds Bloom filters per SSTable on compaction
  - Tuned per-table based on workload

[Visual suggestion: Comparison bar - Hash Set vs Bloom Filter vs Cuckoo Filter on memory, lookup speed, supports delete]

---

## Topic 8: Circuit Breaker Pattern

### Slide 46: Circuit Breaker - Concept Introduction
- Protects a service from repeatedly calling a failing downstream dependency
  - Inspired by electrical circuit breakers that trip on overload
- Without it: failed dependency causes thread pool exhaustion, cascading failures, total outage
  - One slow service brings down the entire system
- Tracks failure rate; "trips open" when threshold exceeded
  - Subsequent calls fail fast, freeing resources
- Periodically allows test calls to detect recovery
  - Self-healing without manual intervention
- Real example: Netflix Hystrix protected video streaming during downstream API failures
  - One failing recommendation service did not block playback start

[Visual suggestion: Electrical breaker icon next to a microservice diagram, with breaker tripping when failure rate spikes]

---

### Slide 47: Circuit Breaker States - Deep Explanation
- Closed (normal): all calls go through; failures counted
  - If failures exceed threshold (e.g., 50% over 20 calls), trip to Open
- Open (tripped): all calls fail immediately without contacting downstream
  - Returns cached value, default response, or error - fast fail
  - After cooldown period (e.g., 30s), transition to Half-Open
- Half-Open (testing): allow limited number of test calls through
  - If they succeed, go back to Closed; if they fail, return to Open
- Metrics tracked: failure rate, latency, slow call rate
  - Slow calls counted as failures (otherwise hangs cascade)
- Real example: Resilience4j tracks rolling window of last N calls for failure rate
  - Configurable thresholds per dependency

[Visual suggestion: State machine diagram - Closed (green) → Open (red) → Half-Open (yellow) with arrows labeled "threshold exceeded", "cooldown elapsed", "test succeeded/failed"]

---

### Slide 48: Circuit Breaker - Example/Intuition
- Service A calls Service B for user preferences
  - B starts timing out (DB issue downstream)
- Without circuit breaker: A's threads pile up waiting on B
  - A's thread pool exhausts; A starts failing all requests, including unrelated ones
- With circuit breaker: A detects 60% B-call failures, trips breaker
  - A immediately returns cached preferences or default values
  - A's thread pool stays healthy; other features work fine
- After 30 seconds, breaker tries one call to B
  - If success → close breaker; if failure → wait another 30s
- Real example: Amazon Prime Video uses circuit breakers between recommendation, billing, and playback services
  - User can still watch even if recommendations fail

[Visual suggestion: Two scenarios side-by-side - Without breaker (cascading red across all services) vs With breaker (failure isolated to one)]

---

### Slide 49: Circuit Breaker + Retry + Timeout - Diagram
- Three patterns work together: timeout, retry, circuit breaker
  - Timeout: per-call deadline (e.g., 1s)
  - Retry: a few retries with exponential backoff and jitter
  - Circuit breaker: gives up entirely when system is clearly down
- Without timeout: retries hang forever; circuit breaker cannot detect failures fast
  - Always set tight, sensible timeouts first
- Without retry: transient blips cause unnecessary breaker trips
  - Retry handles momentary glitches; breaker handles sustained outages
- Order: caller → retry wrapper → circuit breaker → timeout → downstream
  - Each layer addresses a different failure pattern
- Real example: Netflix Hystrix combines all three; Resilience4j and Polly do the same
  - gRPC interceptors and Istio service mesh provide these out of the box

[Visual suggestion: Layered onion - outer: caller, middle layers: retry → breaker → timeout, inner: downstream service]

---

### Slide 50: Circuit Breaker - Trade-offs
- Fail-fast vs trying harder: fast failure improves overall system health
  - But individual user requests fail sooner
- Threshold tuning is critical: too sensitive trips on noise; too lax fails to protect
  - Start with 50% failure rate over 20-call window; adjust with data
- Cooldown duration: too short → flapping; too long → slow recovery
  - 10-60s typical; tune per service
- Fallback strategy required: cached value, default response, degraded mode
  - "Sorry, we cannot show recommendations right now" beats a 30s timeout
- Real example: Netflix Hystrix dashboard surfaced breaker state across hundreds of services
  - Operators see cascading risk before it spreads

[Visual suggestion: Trade-off triangle - Sensitivity vs Recovery time vs User impact]

---

## Topic 9: Back-of-the-envelope Estimation

### Slide 51: Estimation - Concept Introduction
- Quick math to size a system: requests/sec, storage, bandwidth, server count
  - Within ~10x correctness; goal is sanity-check, not precision
- Demonstrates engineering judgment in interviews and design reviews
  - "Will this fit on one server or do we need 100?"
- Foundation: powers of 2, latency numbers, rule-of-thumb assumptions
  - Memorize these; do not derive from scratch each time
- Approach: state assumptions clearly, do math out loud, sanity-check at end
  - Explicit reasoning matters more than the final number
- Real example: Twitter's original "140 chars × 500M tweets/day" math justified storage choices
  - Same math justifies sharding strategy

[Visual suggestion: Napkin sketch with handwritten math: 1B users × 10 req/day / 86400 sec ≈ 116K req/sec]

---

### Slide 52: Powers of 2 Reference - Deep Explanation
- 2^10 = 1,024 ≈ 1 thousand → 1 KB
- 2^20 = 1,048,576 ≈ 1 million → 1 MB
- 2^30 ≈ 1 billion → 1 GB
- 2^32 ≈ 4 billion → 4 GB (also IPv4 address space)
- 2^40 ≈ 1 trillion → 1 TB
- 2^50 ≈ 1 quadrillion → 1 PB
  - Memorize so you can convert quickly
- ASCII char = 1 byte; UTF-8 ≈ 1-4 bytes; UUID = 16 bytes; timestamp = 8 bytes
  - Use for record-size estimates
- Real example: 1B users × 1KB profile = 1 TB - fits on a single server's SSD
  - Same data with images = 1 PB - needs distributed storage

[Visual suggestion: Reference table - power of 2, exact value, approximate label, common system context]

---

### Slide 53: Latency Numbers Every Engineer Should Know
- L1 cache reference: 0.5 ns
- Branch mispredict: 5 ns
- L2 cache reference: 7 ns
- Mutex lock/unlock: 25 ns
- Main memory reference: 100 ns
- Compress 1KB with Zippy: 3,000 ns (3 μs)
- Send 1KB over 1 Gbps network: 10,000 ns (10 μs)
- Read 4KB random from SSD: 150,000 ns (150 μs)
- Read 1MB sequentially from memory: 250,000 ns (250 μs)
- Round trip within same datacenter: 500,000 ns (500 μs)
- Read 1MB sequentially from SSD: 1,000,000 ns (1 ms)
- Disk seek (HDD): 10,000,000 ns (10 ms)
- Read 1MB sequentially from HDD: 30,000,000 ns (30 ms)
- Send packet US → Europe → US: 150,000,000 ns (150 ms)
  - Memory is ~100,000x faster than HDD; SSD is ~10x faster than HDD seek

[Visual suggestion: Logarithmic scale bar chart showing each operation as a horizontal bar, color-coded by category (cache, memory, network, disk)]

---

### Slide 54: Traffic and Storage Estimates - Example/Intuition
- Traffic example: 1B daily active users, each makes 10 reads + 1 write per day
  - Reads: 10B/day = 10B / 86400 ≈ 116K reads/sec average
  - Peak (3x average): ~350K reads/sec
- Storage example: 1B users × 1KB profile = 1 TB; with 5-year retention and 10% growth = ~5 TB
  - Replication factor 3 → 15 TB raw capacity
- Bandwidth example: 1M concurrent video streams × 5 Mbps = 5 Tbps
  - Requires major CDN; not single-DC
- Always state: peak vs average, read:write ratio, retention period
  - These assumptions drive the architecture
- Real example: YouTube uploads ~500 hours/min of video; average 50MB/min storage = 25TB/min raw
  - Justifies massive distributed object storage (Bigtable + Colossus)

[Visual suggestion: Calculation worksheet showing assumptions on left, math in middle, results on right]

---

### Slide 55: Estimation - Trade-offs
- Precision vs speed: 5-minute estimate guides the next 5 hours of design
  - Aim for order-of-magnitude correct
- Average vs peak: design for peak; size capacity at 2-3x average
  - Black Friday, viral content, time zones cause spikes
- Read-heavy vs write-heavy assumption changes architecture
  - Caches help reads; sharding helps writes
- Round numbers aggressively: 86400 ≈ 100K seconds/day
  - Speeds mental math without losing accuracy
- Real example: System design interviews score on reasoning, not the final number
  - "1 in 100K precision is wrong but 1 in 10 is fine"

[Visual suggestion: Quick-reference card with daily seconds (86,400 ≈ 100K), monthly seconds (~2.5M), QPS conversions]

---

## Topic 10: System Design Interview Framework

### Slide 56: Interview Framework - Concept Introduction
- A structured 5-step approach to handle any system design question
  - Avoid jumping to solutions; demonstrate disciplined thinking
- Steps: Clarify → Estimate → High-level design → Deep dive → Bottlenecks
  - Allocate roughly: 5min, 5min, 10min, 15min, 10min in a 45-min interview
- The framework is the answer
  - Interviewers grade structure as much as the technical content
- Communicate trade-offs explicitly at every step
  - "I'd choose X because Y, accepting trade-off Z"
- Real example: Asked "Design Twitter" - clarify scope (timelines? DMs? search?), estimate, sketch, deep dive on fanout, address hot users
  - Same framework applies to URL shortener, ride share, chat app

[Visual suggestion: 5-step horizontal flow with time allocations and sample questions at each stage]

---

### Slide 57: Step 1 - Clarify Requirements
- Functional requirements: what the system does (features)
  - "Users can post tweets, follow others, see a timeline"
- Non-functional requirements: how well it does it (qualities)
  - Latency, availability, consistency, scalability, durability
- Constraints: scale (1M vs 1B users), region (single vs global), budget
  - These shape every design choice that follows
- Out-of-scope items: explicitly call them out
  - "I'll skip search and DMs to focus on core posting + timeline"
- Real example: Designing Uber - confirm: ride-hailing only? matching? payment? maps? surge pricing?
  - Scope determines whether the answer covers 5 services or 50

[Visual suggestion: Two columns - Functional (feature checklist) vs Non-functional (latency budget, 99.99% SLA, etc.) with an "Out-of-scope" section below]

---

### Slide 58: Step 2 - Estimate Scale
- Calculate: DAU, requests/sec (avg + peak), storage/year, bandwidth
  - Use rule-of-thumb assumptions and powers of 2
- Read:write ratio shapes architecture
  - 100:1 read-heavy → cache aggressively; 1:1 → focus on write throughput
- Storage: bytes per record × records per second × retention
  - Multiply by replication factor for raw capacity
- Bandwidth: requests/sec × payload size, both ingress and egress
  - Egress dominates for video, downloads, social feeds
- Real example: Designing Instagram - 500M DAU × 5 photos viewed = 2.5B reads/day, ~30K reads/sec average, ~100K peak
  - Justifies CDN + read replicas

[Visual suggestion: Estimation worksheet with placeholder math: DAU ___, RPS ___, Storage/year ___, Bandwidth ___]

---

### Slide 59: Step 3 - High-Level Design
- Draw boxes and arrows: client, load balancer, app servers, cache, DB, queue, workers
  - 5-10 boxes; do not over-detail yet
- Identify the major data flows: read path, write path, async jobs
  - One arrow per flow; label with key operation
- Choose major technologies with brief justification: SQL vs NoSQL, Redis vs Memcached, Kafka vs SQS
  - Trade-offs in one sentence each
- Add CDN, API gateway, monitoring as supporting infrastructure
  - Mention but do not dive in yet
- Real example: URL shortener high-level: Client → CDN → API Gateway → App Server → Redis cache → MySQL (sharded by hash)
  - Add Kafka for analytics events

[Visual suggestion: Box-and-arrow architecture diagram with 7-8 components, color-coded by tier (edge, app, data)]

---

### Slide 60: Step 4 - Deep Dive into Components
- Pick 1-2 critical components based on interviewer interest
  - Usually data model, hot path, or unique scaling challenge
- Data model: tables/documents, indexes, partition key, access patterns
  - Justify schema choices; show query examples
- Caching strategy: cache key, TTL, invalidation, hit ratio target
  - Address thundering herd, stampede mitigation
- Sharding/partitioning: key choice, hot partition handling, rebalancing
  - Use consistent hashing, range, or composite keys
- Real example: Twitter timeline - deep dive on fanout-on-write vs fanout-on-read, hybrid for celebrities
  - Justify with celebrity follower count math (millions of fans)

[Visual suggestion: Zoom-in lens icon on one component from high-level diagram, exploding into detailed sub-architecture]

---

### Slide 61: Step 5 - Identify and Address Bottlenecks
- Walk through the design asking: where does this break at 10x scale?
  - Single DB → shard or replicate; one cache → distributed cache; one region → multi-region
- Common bottlenecks: hot keys, single point of failure, sync replication latency, expensive joins
  - Prepare a mitigation for each
- Discuss trade-offs explicitly: stronger consistency vs lower latency, cost vs reliability
  - Show you understand there is no free lunch
- Add observability: metrics, logs, traces, alerts on SLO breaches
  - "How would I know this is failing?"
- Real example: Designing chat app - identify hot rooms (1M users in one room) → shard by sub-room or use pub/sub fanout
  - Each bottleneck has a known pattern

[Visual suggestion: Bottleneck heatmap on the architecture diagram with red dots, each annotated with mitigation]

---

### Slide 62: Common Follow-Up Questions
- "How would you handle 10x more traffic?"
  - Horizontal scaling, caching layers, async processing, sharding
- "What if region X goes down?"
  - Multi-region active-active or active-passive, data replication, DNS failover
- "How do you ensure data consistency?"
  - Choose CP or AP per use case; transactions where needed; eventual consistency where acceptable
- "How would you monitor this?"
  - RED metrics (Rate, Errors, Duration), USE method, dashboards, alerts on SLO
- "What if a celebrity user has 100M followers?"
  - Hybrid fanout, special-casing, async pre-computation
- Real example: "Design Slack" follow-ups always include - presence, search, mobile push, file storage
  - Anticipate them; have a 2-sentence answer ready for each

[Visual suggestion: Q&A flashcards layout - question on top, 2-3 bullet answer below, in a grid]

---

### Slide 63: Interview Framework - Trade-offs
- Time vs depth: spending too long clarifying leaves no time for design
  - Stick to budget; politely ask "let me move forward"
- Breadth vs depth: covering many components shallowly vs few components deeply
  - Cover breadth in high-level, depth in 1-2 components
- Buzzwords vs reasoning: name-dropping Kafka without justification looks weak
  - Always pair tech choice with one-sentence "because X"
- Generic vs tailored: applying the same template to every problem is robotic
  - Adapt - some problems are write-heavy, some are real-time, some are storage-heavy
- Real example: Strong candidates often draw a quick scaling roadmap: "v1 single server → v2 add cache → v3 shard → v4 multi-region"
  - Shows evolutionary thinking

[Visual suggestion: Time budget pie chart - Clarify 10%, Estimate 10%, High-level 25%, Deep dive 35%, Bottlenecks 20%]

---

## Section 11 Wrap-Up

### Slide 64: Advanced Topics - Key Takeaways
- Consistent hashing minimizes remapping when nodes change
  - Vnodes provide even distribution and weighted nodes
- Bloom filters trade certainty for space
  - No false negatives; perfect for cache and DB skip-lookups
- Circuit breakers prevent cascading failures
  - Closed → Open → Half-Open with proper thresholds and fallbacks
- Estimation skills guide architecture in 5 minutes
  - Memorize powers of 2 and latency numbers
- Interview framework provides structure: Clarify, Estimate, Design, Deep dive, Bottlenecks
  - The framework itself is half the answer

[Visual suggestion: 5-icon summary - ring, bit array, breaker, calculator, framework arrow]

---

### Slide 65: Interview Tips - Final
- Always start by clarifying scope; do not jump to a solution
  - 30 seconds of clarification saves 30 minutes of wrong design
- Think out loud: interviewer follows your reasoning, not just the diagram
  - Even when stuck, narrate options and trade-offs
- Use real-world examples to anchor abstract claims
  - "Like how Cassandra uses vnodes" or "Netflix's Hystrix pattern"
- When asked about a specific tech, give 1-line definition + 2-line trade-offs
  - Shows you know the tech and where it fits
- Wrap up with a recap and explicitly call out things you would do given more time
  - Demonstrates self-awareness and prioritization

[Visual suggestion: Interview "do's and don'ts" list, color-coded green and red]

---

### Slide 66: Common Pitfalls - Final
- Designing for a billion users when the problem is for a thousand
  - Overengineering wastes time and money; start simple, evolve
- Forgetting non-functional requirements: latency, availability, durability
  - These often drive design more than features
- Picking technologies without justifying fit
  - "I'd use Cassandra because it's web-scale" is a red flag
- Ignoring failure modes: what happens when a node, region, or dependency fails?
  - Senior engineers always have a "what if it breaks" answer
- Skipping monitoring and observability
  - Production systems must answer "is it working?" "what is broken?" "how do I know?"
- Real example: Premature sharding adds operational pain without scale benefit
  - Many systems run for years on a single beefy DB

[Visual suggestion: "Anti-pattern wall" - 6 common mistakes crossed out with red X, correct approach below each]

---

### Slide 67: Closing - From Theory to Practice
- System design is iterative: ship simple, measure, evolve
  - No design survives contact with real traffic unchanged
- Read engineering blogs: Netflix, Uber, Stripe, Discord, Cloudflare publish real war stories
  - Pattern-match production decisions to interview frameworks
- Build small projects end-to-end: deploy, monitor, scale, fail, recover
  - Theory + practice compounds faster than either alone
- Master fundamentals: consistency, partitioning, replication, caching, queues
  - Every advanced system is a recombination of these primitives
- Real example: Discord scaled to 200M users by repeatedly applying Cassandra + Rust + careful sharding
  - No magic; just disciplined application of fundamentals

[Visual suggestion: Spiral diagram - ship → measure → learn → evolve, with each loop labeled with a concept from the deck]

---

### Slide 68: Resources for Further Study
- Books: "Designing Data-Intensive Applications" by Martin Kleppmann (essential)
  - "System Design Interview" by Alex Xu (interview-focused)
- Engineering blogs: Netflix Tech Blog, Uber Engineering, High Scalability, AWS Architecture Blog
  - Real systems at real scale
- Papers: Dynamo (Amazon), Bigtable (Google), Spanner (Google), Kafka, Raft
  - Foundational reading; many modern systems trace back to these
- Practice: Pramp, interviewing.io, design problems on LeetCode
  - Mock interviews build the muscle memory
- Communities: r/ExperiencedDevs, HackerNews, Discord communities, local meetups
  - Learning compounds in good company

[Visual suggestion: Resource library shelf - books, papers, blogs, podcasts as icons]
