# System Design Primer — Slides

> A comprehensive, structured collection of system design slides covering everything from fundamentals to advanced security — crafted for engineers preparing for system design interviews or leveling up their architecture knowledge.

---

## 📖 What's This?

This repo contains slide-style Markdown notes (and a downloadable PowerPoint) based on the popular [System Design Primer](https://github.com/donnemartin/system-design-primer). Each section is self-contained and follows a consistent format: concept → analogy → real-world example → trade-offs.

Perfect for:
- 🧑‍💻 Engineers preparing for system design interviews
- 📚 Self-learners who prefer structured, visual notes
- 🗣️ Technical educators looking for presentation-ready material

---

## 📂 Contents

| Section | Topic | File |
|---------|-------|------|
| 01 | Fundamentals — Scalability, Latency, Throughput, HA | [section-01-fundamentals.md](./section-01-fundamentals.md) |
| 02 | CAP Theorem, Consistency & Availability | [section-02-cap-consistency-availability.md](./section-02-cap-consistency-availability.md) |
| 03 | DNS & CDN | [section-03-dns-cdn.md](./section-03-dns-cdn.md) |
| 04 | Load Balancers & Reverse Proxy | [section-04-load-balancers-proxy.md](./section-04-load-balancers-proxy.md) |
| 05 | Application Layer & Microservices | [section-05-app-layer-microservices.md](./section-05-app-layer-microservices.md) |
| 06 | Databases — SQL, NoSQL, Replication, Sharding | [section-06-databases.md](./section-06-databases.md) |
| 07 | Caching — Strategies, Redis, Eviction Policies | [section-07-caching.md](./section-07-caching.md) |
| 08 | Asynchronism & Message Queues | [section-08-async-queues.md](./section-08-async-queues.md) |
| 09 | Communication — REST, gRPC, WebSockets, RPC | [section-09-communication.md](./section-09-communication.md) |
| 10 | Security & Advanced Topics | [section-10-security-advanced.md](./section-10-security-advanced.md) |

### 📦 All-in-One Files

- [`system-design-slides.md`](./system-design-slides.md) — All sections merged into a single Markdown file
- [`system-design-slides.pptx`](./system-design-slides.pptx) — PowerPoint version, ready to present

---

## 🗺️ Topics at a Glance

```
Fundamentals → CAP Theorem → DNS/CDN → Load Balancers
     ↓
App Layer & Microservices → Databases → Caching
     ↓
Async & Queues → Communication Protocols → Security
```

Key concepts covered:
- **Scalability**: Vertical vs horizontal scaling, stateless design
- **Consistency models**: Strong, eventual, causal consistency
- **Data storage**: RDBMS, NoSQL (document, key-value, column, graph), replication, sharding
- **Performance**: CDNs, caching layers, read/write optimization
- **Reliability**: Load balancing algorithms, circuit breakers, retries
- **Communication**: REST, GraphQL, gRPC, WebSockets, long polling
- **Security**: Auth (OAuth, JWT), encryption, rate limiting, OWASP top 10

---

## 🚀 How to Use

### Read Online
Browse individual section files directly on GitHub — they render cleanly as structured notes.

### Present
Download [`system-design-slides.pptx`](./system-design-slides.pptx) and open in PowerPoint / Google Slides / Keynote.

### Use with Marp (Markdown Slides)
If you have [Marp CLI](https://github.com/marp-team/marp-cli) installed:

```bash
# Install Marp CLI
npm install -g @marp-team/marp-cli

# Export a section to PDF
marp section-01-fundamentals.md --pdf

# Export all sections
marp system-design-slides.md --pdf
```

---

## 🤝 Contributing

Contributions are welcome! If you spot errors, want to add diagrams, or extend with new sections (e.g., system design case studies):

1. Fork the repo
2. Create a feature branch: `git checkout -b add/section-11-case-studies`
3. Submit a PR with a clear description

---

## ⭐ Acknowledgements

This project is a slide adaptation of the original **[System Design Primer](https://github.com/donnemartin/system-design-primer)** by **[Donne Martin](https://github.com/donnemartin)** — one of the most comprehensive and widely used system design resources, with over 270k stars on GitHub.

All core concepts, explanations, and structure are derived from Donne Martin’s work. This repo reformats that content into slide-friendly Markdown and PowerPoint presentations for easier studying and presenting. Full credit goes to the original author.

---

## 📄 License

This work is licensed under the **[Creative Commons Attribution 4.0 International License (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/)**.

[![CC BY 4.0](https://licensebuttons.net/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

You are free to:
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- **Attribution** — You must give appropriate credit to **Donne Martin** (original [System Design Primer](https://github.com/donnemartin/system-design-primer)) and **Prakhar Yadav** (this slides adaptation), provide a link to the license, and indicate if changes were made.
