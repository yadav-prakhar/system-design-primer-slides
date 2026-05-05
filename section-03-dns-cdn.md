## Section 3: DNS and CDN

---

### Slide 1: Section Overview - DNS and CDN
- **The two pillars of internet delivery**
  - DNS gets users to the right server; CDN delivers content from the closest server.
- **Why these matter together**
  - Before any HTTP request lands, DNS resolves the hostname; the resolved IP often points to a CDN edge.
- **What you will learn**
  - Resolution flow, record types, geo-routing, edge caching, push vs pull, real provider trade-offs.
- **Mental model**
  - DNS = phone book of the internet. CDN = warehouse network placed near customers.
- **Interview relevance**
  - Almost every system design (Netflix, Instagram, e-commerce) mentions DNS routing and CDN caching as first-class citizens.

[Visual suggestion: Split screen - left side shows a phone book with names mapping to numbers labeled "DNS"; right side shows a global map with warehouses near city clusters labeled "CDN".]

---

## PART A: DNS (Domain Name System)

---

### Slide 2: What is DNS? - Concept Introduction
- **DNS = Domain Name System**
  - A distributed, hierarchical database that translates human-friendly hostnames (google.com) into machine-friendly IP addresses (142.250.190.46).
- **The core problem it solves**
  - Humans remember names; computers route packets using IP addresses. DNS bridges this gap.
- **Distributed by design**
  - No single server owns the entire mapping; responsibility is split across root servers, TLD servers, and authoritative servers worldwide.
- **Effectively invisible infrastructure**
  - You never type an IP into a browser; DNS runs silently before every web request, API call, and email delivery.
- **A foundational dependency**
  - When DNS breaks (e.g., Facebook outage Oct 2021), the internet looks down even if servers are healthy.

[Visual suggestion: A user typing "google.com" into a browser, with an arrow labeled "DNS lookup" leading to "142.250.190.46", which then arrows to a server icon.]

---

### Slide 3: Why DNS Exists - The Phone Book Analogy
- **The pre-DNS era (HOSTS.TXT)**
  - In the 1970s ARPANET, every machine had a hosts.txt file mapping all known hostnames to IPs - manually updated and emailed around.
  - This did not scale beyond a few hundred machines.
- **DNS introduced in 1983 by Paul Mockapetris**
  - Replaced the flat file with a hierarchical, distributed system.
- **Phone book analogy**
  - You know "Alice's Pizza" but not the phone number. You look it up in the directory. DNS is that directory for the internet.
- **Why a flat lookup would not work today**
  - With ~360M+ registered domains, no single server can hold or update everything fast enough.
- **Hierarchy enables delegation**
  - .com TLD operator manages .com names; example.com owner manages subdomains. Each layer scales independently.

[Visual suggestion: Side-by-side - left shows a single huge phone book labeled "HOSTS.TXT (does not scale)"; right shows a tree with country directories -> city directories -> business listings labeled "DNS Hierarchy".]

---

### Slide 4: DNS Hierarchy - Deep Explanation
- **Root zone (.)**
  - 13 logical root server clusters (A through M) operated by 12 organizations; they know who runs each TLD.
- **TLD - Top-Level Domain (.com, .org, .io, .uk)**
  - Run by registries (e.g., Verisign runs .com). They know which authoritative nameserver to contact for each second-level domain.
- **Authoritative nameserver**
  - The source of truth for a specific domain (e.g., ns-1.amazon.com holds records for amazon.com).
- **Recursive resolver**
  - Usually run by your ISP, Google (8.8.8.8), Cloudflare (1.1.1.1). Does the legwork on behalf of clients.
- **Stub resolver**
  - The tiny client built into your OS or browser that asks the recursive resolver.

[Visual suggestion: Pyramid diagram - top labeled "Root (.)", below "TLD (.com, .org, .net)", below "Authoritative NS (example.com)", below "Subdomain records". Side annotation shows a laptop icon connecting to a "Recursive Resolver" cloud which traverses the pyramid.]

---

### Slide 5: How DNS Resolution Works - Step by Step
- **Step 1: Browser cache check**
  - Browsers cache recent lookups (Chrome holds them for ~60 seconds).
- **Step 2: OS cache check**
  - If browser misses, the OS resolver cache is checked next.
- **Step 3: Recursive resolver**
  - If still no hit, the OS asks the configured recursive resolver (ISP / 8.8.8.8 / 1.1.1.1).
- **Step 4: Iterative climb**
  - Recursive resolver asks Root -> TLD -> Authoritative, walking the hierarchy.
- **Step 5: Answer returned and cached**
  - The IP is sent back to the OS and browser; each layer caches it for the TTL duration.

[Visual suggestion: Numbered flow diagram. Browser -> OS -> Recursive Resolver. Then resolver branches to Root -> TLD -> Authoritative with arrows labeled 1-5. Final arrow returns IP to browser.]

---

### Slide 6: Recursive vs Iterative Queries
- **Recursive query (client to resolver)**
  - "Give me the final answer or fail." The resolver is responsible for doing all the work.
- **Iterative query (resolver to nameservers)**
  - "Tell me what you know, or who to ask next." The resolver climbs the tree.
- **Why this split exists**
  - Clients are simple; resolvers are smart and well-cached. Splitting work keeps end devices lightweight.
- **Performance implication**
  - The first lookup may take 20-120ms; subsequent lookups within the TTL window are sub-millisecond from cache.
- **Real example**
  - When you visit youtube.com, your laptop sends 1 recursive query; the resolver may send 3-4 iterative queries upstream.

[Visual suggestion: Two boxes side by side. Left "Recursive": single double-headed arrow between client and resolver labeled "Do everything". Right "Iterative": resolver shown with three sequential arrows to Root, TLD, Authoritative, each returning a partial answer.]

---

### Slide 7: DNS Resolution Diagram - End-to-End Flow
- **Components**
  - Stub resolver (OS), Recursive resolver, Root server, TLD server, Authoritative nameserver, Origin web server.
- **Arrow walkthrough**
  - 1: Stub -> Recursive ("What is www.example.com?")
  - 2: Recursive -> Root (".") returns "Ask .com TLD at 192.x.x.x"
  - 3: Recursive -> .com TLD returns "Ask ns1.example.com"
  - 4: Recursive -> ns1.example.com returns "93.184.216.34"
  - 5: Recursive -> Stub returns final IP; browser opens TCP to origin.
- **Caching at every hop**
  - Each layer (browser, OS, resolver) stores results until TTL expires.
- **Failure modes**
  - If any nameserver in the chain is down, resolution fails or falls back to a secondary NS.
- **Total time budget**
  - Cold cache: 50-200ms. Warm cache: <1ms.

[Visual suggestion: Horizontal flow with 6 boxes left-to-right: User -> Stub -> Recursive Resolver. From the Recursive Resolver, three vertical arrows go up to Root, TLD, Authoritative in sequence. Final arrow back down to user. Each arrow numbered 1-5. Cache icons at each box.]

---

### Slide 8: DNS Record Types - A and AAAA
- **A record (Address record)**
  - Maps a hostname to an IPv4 address. Example: example.com A 93.184.216.34.
- **AAAA record (quad-A)**
  - Maps a hostname to an IPv6 address. Example: example.com AAAA 2606:2800:220:1:248:1893:25c8:1946.
- **Why both exist**
  - The internet is mid-migration from IPv4 (4.3B addresses, exhausted) to IPv6 (340 undecillion addresses).
- **Dual-stack behavior**
  - Modern OSes prefer AAAA when available, fall back to A. Hence websites publish both.
- **Real-world example**
  - Run `dig google.com A` and `dig google.com AAAA` - you will see both populated.

[Visual suggestion: Two-column table. Column 1: "A Record" with sample row "example.com -> 93.184.216.34". Column 2: "AAAA Record" with sample row "example.com -> 2606:2800:220:1:248:...".]

---

### Slide 9: DNS Record Types - CNAME, MX, NS, TXT
- **CNAME (Canonical Name)**
  - An alias from one hostname to another. Example: www.example.com CNAME example.com.
  - Used heavily in CDNs: yourapp.com CNAME d123.cloudfront.net.
- **MX (Mail Exchange)**
  - Tells email senders which server handles mail for this domain. Has priority values.
  - Example: example.com MX 10 mail.example.com.
- **NS (Nameserver)**
  - Identifies which authoritative nameservers are responsible for the domain.
  - Example: example.com NS ns-1.awsdns-01.org.
- **TXT records**
  - Free-form text. Used for SPF, DKIM, domain ownership verification (Google Search Console).
- **Other notable types**
  - PTR (reverse DNS), SRV (service discovery), CAA (certificate authority authorization), SOA (zone metadata).

[Visual suggestion: A table with columns "Type | Purpose | Example". Five rows: A, CNAME, MX, NS, TXT each filled with the example values from the bullets.]

---

### Slide 10: TTL - Time To Live
- **What TTL is**
  - A number (in seconds) attached to every DNS record telling resolvers how long they may cache the answer.
- **Common TTL values**
  - 60s (rapid failover scenarios), 300s (standard SaaS), 3600s (typical website), 86400s (rarely-changing infrastructure like NS records).
- **The trade-off**
  - Low TTL = faster propagation of changes, but more queries hit your authoritative server (cost + load).
  - High TTL = better cache hit ratio + lower cost, but slow to propagate changes during incidents.
- **Pre-migration practice**
  - Drop TTL to 60s a day before a planned IP change so old entries expire fast; raise it back afterward.
- **Real example**
  - Cloudflare uses ~300s by default; AWS Route 53 lets you set anything from 0 to 172800s.

[Visual suggestion: Slider graphic - left end "Low TTL (60s)" labeled "Fast change, high cost"; right end "High TTL (24h)" labeled "Slow change, low cost". A pointer in the middle shows "Sweet spot ~300s".]

---

### Slide 11: DNS Caching - Why It Saves the Internet
- **Caching happens at every layer**
  - Browser, OS, recursive resolver, sometimes corporate DNS proxies.
- **Cache hit ratio is enormous**
  - For popular domains like google.com, ~99% of lookups never reach the authoritative server.
- **Why this is essential**
  - Without caching, root servers would be flooded billions of times per second; the internet would buckle.
- **Negative caching**
  - "NXDOMAIN" (does not exist) responses are also cached, controlled by the SOA record's minimum TTL.
- **Cache poisoning risk**
  - Attackers historically injected fake records into resolver caches; mitigated by DNSSEC and source port randomization.

[Visual suggestion: Layered cake diagram. Bottom layer "Authoritative NS" (small slice). Above it "Recursive Resolver" (larger). Above "OS Cache" (larger). Top "Browser Cache" (largest). Annotation: "99% of queries served from upper layers".]

---

### Slide 12: Round Robin DNS - Load Balancing for Free
- **What it is**
  - Configure multiple A records for the same hostname. Resolvers rotate which IP they return.
  - Example: api.example.com -> 1.2.3.4, 1.2.3.5, 1.2.3.6 (rotates each query).
- **Why it works as a load balancer**
  - Different clients hit different servers, distributing load roughly evenly.
- **No infrastructure needed**
  - Pure DNS feature; no L4/L7 load balancer required.
- **Limitations**
  - No health checking - if a server is down, DNS still hands out its IP.
  - Caching defeats round-robin: a client may stick to the first IP for the TTL duration.
- **Real-world use**
  - Often used as a coarse first layer in front of actual load balancers (DNS round-robin -> regional ALB -> instances).

[Visual suggestion: One DNS server icon with three outgoing arrows to three web servers. Three client icons each receive a different IP, each connects to a different server. Label "Roughly 1/3 traffic to each".]

---

### Slide 13: GeoDNS and Latency-Based Routing
- **GeoDNS = answer based on requester's geography**
  - Same hostname returns different IPs depending on where you ask from.
  - Example: example.com from Mumbai -> 13.x.x.x (ap-south-1); from Frankfurt -> 18.x.x.x (eu-central-1).
- **How the resolver knows your location**
  - Source IP of the recursive resolver, or EDNS Client Subnet (ECS) which forwards a portion of the client IP.
- **Latency-based routing**
  - Service measures real-world latency from each region and returns the lowest-latency endpoint, not just the geographically closest.
- **Why "closest" is not always "fastest"**
  - Internet routing is messy; a peering link from Sydney to Singapore may beat Sydney to Tokyo even if Tokyo is closer.
- **Provider examples**
  - AWS Route 53 (geolocation, geoproximity, latency policies), Cloudflare Load Balancing, NS1, Google Cloud DNS.

[Visual suggestion: World map with three users (NYC, London, Tokyo). Arrows from each user to the nearest data center icon (Virginia, Ireland, Tokyo respectively). Label each arrow with the resolved IP.]

---

### Slide 14: DNS-Based Load Balancing - Intuition and Analogy
- **Pizza chain analogy**
  - Call 1-800-PIZZA from NYC, you reach the NYC store; call from LA, you reach the LA store. Same number, different store, based on where you called from.
- **DNS = the call routing system**
  - It does the geographic dispatch; the actual order/cooking happens at the local store (origin server).
- **Combined strategy**
  - Production stacks usually layer: GeoDNS -> Regional Load Balancer -> Service Mesh -> Pod.
- **Why DNS is a coarse tool**
  - Granularity is "per resolver" not "per request". Real fine-grained balancing happens at L4/L7 LBs.
- **Failover via DNS**
  - Health-checking DNS providers (Route 53, NS1) remove unhealthy IPs from rotation, but propagation depends on TTL.

[Visual suggestion: A user calling a phone with a speech bubble "1-800-PIZZA". Three branching arrows to NYC, LA, Chicago store icons. Caption "Same number, location-aware routing". Below it, parallel diagram with "example.com" and three regional servers.]

---

### Slide 15: DNS Trade-offs and Pitfalls
- **TTL vs agility**
  - You cannot fail over faster than the smallest TTL clients are honoring.
- **Caching is mostly out of your control**
  - Misbehaving resolvers and browsers may ignore your TTL.
- **DNS is UDP-first (port 53)**
  - Default 512-byte limit; larger responses fall back to TCP or use EDNS0.
- **Single point of failure if mismanaged**
  - The 2016 Dyn DDoS took down Twitter, Reddit, GitHub. Use multiple DNS providers (multi-NS strategy).
- **Security concerns**
  - DNS hijacking, cache poisoning, DNS-over-cleartext eavesdropping. Mitigations: DNSSEC, DNS-over-HTTPS (DoH), DNS-over-TLS (DoT).

[Visual suggestion: A table with columns "Concern | Symptom | Mitigation". Rows: TTL too high (slow failover -> drop pre-change), TTL too low (cost spike -> raise post-change), Single provider (full outage -> multi-provider), Cleartext (eavesdrop -> DoH/DoT).]

---

## PART B: CDN (Content Delivery Network)

---

### Slide 16: What is a CDN? - Concept Introduction
- **CDN = Content Delivery Network**
  - A globally distributed network of servers that cache and serve content from locations physically near end users.
- **The core problem it solves**
  - Speed of light is fixed (~200,000 km/s in fiber). Sydney to Virginia round-trip is ~250ms minimum.
  - Serving a Sydney user from Sydney instead of Virginia turns 250ms into 5ms.
- **What CDNs serve**
  - Static assets (images, CSS, JS, video segments), dynamic content (with smart caching), and increasingly compute (edge functions).
- **Warehouse analogy**
  - Amazon does not ship every order from Seattle; they place warehouses near population centers. CDNs do the same for bytes.
- **Origin protected by edges**
  - The origin server (your real backend) only sees a fraction of traffic - the cache misses.

[Visual suggestion: Globe with a single "Origin" server icon centered, surrounded by ~15 smaller "Edge" server icons distributed across continents. Users connect to the nearest edge icon with short arrows; edges connect to the origin with longer arrows labeled "cache miss only".]

---

### Slide 17: Why CDNs Exist - The Latency Problem
- **Physics has a hard floor**
  - A packet from London to Sydney crosses ~17,000 km. At light-speed-in-fiber, that is ~85ms one-way, ~170ms RTT - before any compute.
- **TCP and TLS amplify it**
  - TCP handshake (1 RTT) + TLS handshake (1-2 RTTs) + HTTP request/response (1 RTT) = 4-5 RTTs before first byte.
- **Bandwidth alone does not save you**
  - You can have 1 Gbps and still wait 200ms because latency is independent of bandwidth.
- **Real impact on UX and business**
  - Amazon found 100ms of latency cost them 1% in sales. Google saw 20% drop in traffic with 500ms slower search.
- **CDN compresses the distance**
  - By moving content close to users, you cut RTTs from hundreds of ms to single digits.

[Visual suggestion: World map with two scenarios. Top: User in Sydney, line to Virginia origin labeled "250ms RTT, 4 RTTs = 1 second". Bottom: same user, line to Sydney edge labeled "5ms RTT, 4 RTTs = 20ms". Bold caption: "50x faster".]

---

### Slide 18: How CDNs Work - Architecture Deep Dive
- **PoP (Point of Presence)**
  - A physical location (data center, ISP rack) hosting CDN edge servers. Cloudflare has 300+ PoPs globally.
- **Edge server**
  - The cache node a user actually connects to. Holds copies of frequently-requested content.
- **Origin server**
  - Your application's source of truth - the backend the CDN pulls from on a cache miss.
- **Mid-tier / shield cache**
  - An intermediate caching layer between edges and origin to reduce origin load further (Fastly's "shielding", Cloudflare's "Tiered Cache").
- **Anycast routing**
  - The same IP advertised from many PoPs; BGP routes the user to the topologically nearest one automatically.

[Visual suggestion: Three-layer pyramid. Top: "Origin (1 location)". Middle: "Shield/Mid-tier (5-10 locations)". Bottom: "Edge PoPs (100s of locations)". Users connect at the bottom; arrows climb only on cache miss.]

---

### Slide 19: CDN Request Flow - Step by Step
- **Step 1: User DNS lookup**
  - assets.example.com resolves to a CDN-managed IP via CNAME or ALIAS.
- **Step 2: Anycast routes to nearest edge**
  - User's TCP/TLS connection terminates at the closest PoP - often within 10-30ms.
- **Step 3: Edge cache lookup**
  - Edge checks its cache using the URL + headers as the cache key.
- **Step 4a: Cache hit (the common case)**
  - Content served from RAM/SSD on the edge in single-digit ms.
- **Step 4b: Cache miss**
  - Edge fetches from origin (possibly through shield), stores it locally, returns to user. Subsequent requests hit cache.

[Visual suggestion: Horizontal flow: User -> Edge PoP. From Edge, two paths: green path "HIT - return cached" (loops back to user), red path "MISS - fetch from origin" (goes to Origin and back). Each step labeled with typical latency.]

---

### Slide 20: Push CDN vs Pull CDN
- **Pull CDN (lazy, default)**
  - Edge fetches content from origin on first request, caches it, serves subsequent requests.
  - First user pays the latency cost; everyone after benefits.
  - Used by: most web assets, blog images, JS bundles. CloudFront, Cloudflare default behavior.
- **Push CDN (eager, manual)**
  - You upload content directly to the CDN; nothing is fetched from origin on demand.
  - You control exactly what is on the edge and when.
  - Used by: very large files, video downloads, software releases, infrequently-changed assets.
- **When to choose pull**
  - High-volume, frequently-updated, or unpredictable content. Lower operational overhead.
- **When to choose push**
  - Large files (multi-GB game patches), low-traffic but business-critical assets (you do not want the first user to wait), strict cache control.
- **Hybrid is common**
  - Big platforms push the "must be hot" content and let everything else pull on demand.

[Visual suggestion: Two side-by-side diagrams. Left "Pull": user requests -> edge -> miss -> origin (arrow on demand). Right "Push": developer uploads -> CDN API -> edges (arrow before any user request). Below each: bullet list "Pros / Cons".]

---

### Slide 21: CDN Caching Mechanics
- **Cache key**
  - Usually URL + selected headers (Vary: Accept-Encoding etc). Two URLs differing by query string may or may not share a key.
- **Cache-Control headers drive behavior**
  - max-age, s-maxage, public/private, no-cache, no-store, stale-while-revalidate.
- **TTL on the edge**
  - How long the edge serves a copy before checking origin again. Independent from browser's max-age.
- **Cache invalidation**
  - Purge by URL, by tag (Fastly surrogate keys), or by wildcard. CloudFront invalidations cost money beyond a free quota.
- **Cache hit ratio is the key metric**
  - 90%+ is typical for well-tuned static content; below 70% means you are mostly proxying, not caching.

[Visual suggestion: A cache entry box with fields "Key: /img/logo.png", "Value: <bytes>", "TTL: 86400s", "Tags: [logo, branding]". Arrows show "purge by tag", "purge by URL", "expire by TTL".]

---

### Slide 22: CDN Benefits - Why Everyone Uses Them
- **Reduced latency**
  - Single-digit ms TTFB versus hundreds of ms to a far origin. Massive UX win.
- **Reduced origin load**
  - 95%+ of requests served from edges; your origin handles only the long tail and writes.
- **Bandwidth cost reduction**
  - CDN egress is often cheaper per GB than cloud-origin egress, especially at scale.
- **DDoS absorption and WAF**
  - CDNs absorb volumetric attacks across their global capacity (Cloudflare's network is multiple Tbps). Built-in WAFs filter malicious requests.
- **TLS termination and modern protocols**
  - CDNs handle HTTP/2, HTTP/3, QUIC, and modern TLS for you; your origin can stay on HTTP/1.1 if you want.

[Visual suggestion: Five-icon row: stopwatch (latency), shield (DDoS), down-arrow (origin load), dollar sign (cost), padlock (TLS). Each labeled with a one-line benefit.]

---

### Slide 23: CDN Trade-offs and Limitations
- **Stale content risk**
  - Aggressive caching can serve outdated content; need careful invalidation strategy.
- **Cache invalidation complexity**
  - "There are only two hard things in CS: cache invalidation and naming." CDNs make this real.
- **Cost at scale**
  - For small sites, CDNs are cheap or free. At petabyte scale, CDN bills become significant - bandwidth, requests, and feature pricing.
- **Limited dynamic content acceleration**
  - Personalized or rapidly-changing data is harder to cache; needs ESI, edge compute, or smart cache keys.
- **Vendor lock-in and debugging complexity**
  - CDN-specific features (workers, surrogate keys) tie you to one provider. An extra layer between users and your code makes debugging harder (mystery 5xx from edge, regional cache poisoning).

[Visual suggestion: Balance scale icon. Left pan heavy with "Speed, Scale, Security". Right pan also non-trivial with "Staleness, Cost, Complexity, Lock-in". Caption: "CDNs are not free wins - they are trade-offs."]

---

### Slide 24: CDN Architecture Diagram - Global Picture
- **Components labeled**
  - Origin (1 region), Shield PoP (regional), Edge PoPs (global), Anycast IP, Authoritative DNS.
- **Arrow walkthrough**
  - User -> DNS -> Anycast IP -> nearest Edge PoP.
  - Edge -> (on miss) Shield PoP -> (on miss) Origin.
  - Origin -> Shield -> Edge -> User. Cached at every layer on the way back.
- **Labels to include**
  - "Cache hit ratio 95%+", "Anycast BGP routing", "TLS terminated at edge", "Origin sees only ~5% of requests".
- **Failure isolation**
  - If one PoP fails, BGP withdraws the route; users automatically reroute to the next-closest PoP.
- **Real-world scale**
  - Cloudflare: 300+ cities, 13,000+ networks. Akamai: 4,000+ PoPs in 130+ countries.

[Visual suggestion: World map. Single origin pin in us-east-1. Five shield pins (one per continent). 30+ small edge dots scattered globally. Sample user in Tokyo with arrow to Tokyo edge (green, "HIT"). Second user in Lagos with arrow to Lagos edge -> EU shield -> origin (red, "MISS - fill cache").]

---

### Slide 25: Real-World CDN Providers
- **Amazon CloudFront**
  - Tightly integrated with AWS (S3, ALB, Lambda@Edge). Pay-per-use, 450+ PoPs. Good default for AWS shops.
- **Cloudflare**
  - Massive free tier, security-first (WAF, bot mitigation, DDoS), Workers for edge compute, very developer-friendly.
- **Akamai**
  - The original CDN (1998). Enterprise-grade, deepest PoP coverage, expensive, used by banks, airlines, governments.
- **Fastly**
  - Programmable VCL config, instant purge (sub-150ms globally), favored by news sites, GitHub, Shopify, Stripe.
- **Others worth knowing**
  - Google Cloud CDN, Azure Front Door, Bunny.net (low-cost), KeyCDN, StackPath.

[Visual suggestion: Logo collage of CloudFront, Cloudflare, Akamai, Fastly, Google Cloud CDN, Azure Front Door. Each logo annotated with a one-line strength: "AWS-native", "Free tier + security", "Enterprise depth", "Programmable + fast purge", "GCP-native", "Azure-native".]

---

### Slide 26: When NOT to Use a CDN
- **Internal-only services**
  - VPN-protected admin tools have no need for global edges; just adds cost and complexity.
- **Highly personalized, uncacheable responses**
  - If every response varies per user (private dashboards), only the connection acceleration helps; content caching does not.
- **Compliance / data residency restrictions**
  - Some regulations (GDPR for sensitive data, certain government data) require data to stay in-region; global CDN may complicate this.
- **Tiny scale and tight budget**
  - For a hobby blog with 100 visitors/day, CDN setup may not be worth the operational overhead - though free tiers (Cloudflare) often make this moot.
- **WebSockets / long-lived connections**
  - Some CDNs support them, some do not. Validate before assuming.

[Visual suggestion: Red "X" icons next to four scenarios: laptop labeled "internal admin", user with personalized dashboard, lock-in-region icon, tiny website icon. Caption: "Match the tool to the workload."]

---

## PART C: Section Wrap-Up

---

### Slide 27: Key Takeaways
- **DNS is the internet's phone book**
  - Hierarchical, distributed, cache-heavy. TTL controls the agility/cost trade-off.
- **DNS doubles as a coarse load balancer**
  - Round-robin, GeoDNS, and latency-based routing steer users before any HTTP request.
- **CDNs eliminate distance**
  - Edge PoPs near users turn cross-continent latency into local-loop speed.
- **Pull CDN is the default; push for big-or-critical**
  - Pull is lazy and easy. Push is deliberate and pre-warmed.
- **Both are infrastructure leverage**
  - Set them up once, get speed, scale, security, and cost wins for the lifetime of the service.

[Visual suggestion: 5-point checklist with green checkmarks. Each point in one short line. At bottom, two icons: phone book (DNS) + warehouse network (CDN), connected by an "=" sign to a happy globe icon labeled "Fast, scalable, resilient".]

---

### Slide 28: Interview Tips - DNS and CDN
- **Always mention DNS in your design**
  - "Users hit our domain via DNS, which routes them via GeoDNS to the nearest region." Sets the stage.
- **Pair CDN with static assets early**
  - As soon as your design has images, JS, or video, propose a CDN. Interviewers expect it.
- **Speak in record types**
  - Drop "A record", "CNAME", "TTL" naturally. Shows depth without being pretentious.
- **Discuss TTL trade-offs concretely**
  - "I would use a 60s TTL for failover-critical records and 1 hour for stable assets."
- **Know one provider deeply**
  - Pick CloudFront, Cloudflare, or Fastly. Be able to discuss its quirks (CloudFront invalidation cost, Cloudflare Workers cold-start absence, Fastly instant purge).

[Visual suggestion: Numbered list 1-5 styled as an interview cheat-sheet card. Optional: speech bubble with the phrase "users hit our domain via DNS..." at the top.]

---

### Slide 29: Common Pitfalls
- **Setting TTL too high before a migration**
  - You announce a new IP but old IP is cached for hours; users see outages. Lower TTL ahead of time.
- **Forgetting that browsers and resolvers may ignore TTL**
  - Some browsers cap at 60s; some resolvers extend silently. Plan for it - do not assume strict TTL adherence.
- **Treating round-robin DNS as a real load balancer**
  - No health checks, sticky caching - traffic is not even, and dead servers stay in rotation. Use a proper LB.
- **Caching authenticated content publicly**
  - Setting Cache-Control: public on a logged-in user's page leaks data to other users. Always scope cache keys correctly.
- **Forgetting cache invalidation strategy**
  - "Just cache forever" works until you ship a bad CSS file. Plan purge by URL, tag, or version-in-path (logo.v23.png).
- **Single DNS provider risk**
  - 2016 Dyn outage took down half the internet. Use secondary DNS (Route 53 + NS1, or Cloudflare + Dyn).

[Visual suggestion: Six warning-sign icons in a 2x3 grid. Each annotated with a one-line pitfall. Bold red border. Title: "Avoid these in your design and in production."]

---

### Slide 30: Section Summary - DNS + CDN as a Team
- **Together they form the front door of every modern app**
  - DNS picks the right region; CDN serves bytes from the closest edge. Origin handles only the rare/unique work.
- **They are the cheapest performance wins available**
  - No code changes, just configuration. ROI is enormous.
- **They are also the most common single points of failure**
  - Lose your DNS or your CDN, lose your service. Plan redundancy.
- **They unlock global scale**
  - A two-engineer startup can serve users in 100 countries with the same tooling Netflix uses.
- **Up next**
  - Section 4: Load Balancers - how requests are distributed once they arrive in your data center.

[Visual suggestion: Two icons (phone book + warehouse) merging into a single shield icon labeled "Front door of the internet". Arrow pointing forward to a teaser thumbnail "Section 4: Load Balancers".]
