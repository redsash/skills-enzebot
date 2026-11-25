# Worked Example: Expert Advisory Debate (Monolith vs. Event-Driven Split)

## Expert Panel Lineup
| Expert | Archetype & Perspective | Focus Area |
| :--- | :--- | :--- |
| **Elena Vance** | Aggressive Skeptic — Staff Reliability Engineer, Distributed State Machines | Partial failure modes, schema skew, and operational blast radius |
| **Marcus Chen** | Visionary — Principal Platform Architect | Domain autonomy, independent deploys, and 3-year scale ceiling |
| **Priya Nair** | Pragmatic Operator — VP Engineering (18-person org) | Staffing reality, on-call load, and migration sequencing |
| **David Park** | Domain Specialist — PostgreSQL Internals & Outbox Pattern Lead | Transactional boundaries and modular monolith extraction seams |

## Live Adversarial Cross-Debate

**Marcus**: "Our billing deploys get blocked twice a week by search index tests. Extracting billing and fulfillment into event-driven services removes cross-team coupling immediately."

**Elena**: "Marcus is trading CI coupling for distributed failure modes we have zero on-call muscle to debug. Right now, an order placement and ledger debit share one Postgres ACID transaction. Split them over Kafka and you inherit dual-write bugs, out-of-order replays, and split-brain refunds."

**Priya**: "Elena's right about staffing—we have three senior backend engineers total. Running two separate service pipelines plus dead-letter replay tooling will consume 40% of our sprint capacity for six months."

**David**: "Both Elena and Marcus are treating this as a binary jump. Separate CI test suites and enforce schema-level module boundaries inside the existing Postgres monolith using an in-DB transactional outbox first. That gives Marcus independent test velocity now without triggering Elena's distributed-transaction nightmare."

**Marcus**: "If we stay single-repo, how do we stop engineers from importing `billing` internals directly into `orders`?"

**David**: "Module boundary lint rules in CI plus separate Postgres schemas with explicit role grants—zero cross-schema joins allowed."

## Executive Synthesis & Recommendation

### 1. Critical Blind Spots Surfaced
- **CI Coupling vs. Runtime Coupling**: The immediate pain is slow CI coupling, not runtime scaling; extracting networked services solves the wrong bottleneck first.
- **Hidden On-Call Tax**: Moving from single-DB ACID transactions to async events imposes a continuous observability and dead-letter recovery tax on an 18-person team.

### 2. Go / No-Go Criteria
- **PROCEED WITH MODULAR MONOLITH SPLIT IF**: Cross-schema SQL boundaries + separate CI workflows cut deploy wait times by >= 50%.
- **RE-EVALUATE NETWORK EXTRACTION ONLY IF**: Independent scaling profiles (e.g., 10x burst on fulfillment) exceed single-primary Postgres vertical headroom.

### 3. Immediate Action Plan (Next 72 Hours)
1. Audit cross-module imports between `orders` and `billing` and split CI test targets.
2. Prototype schema-isolated Postgres permissions on staging before introducing any message broker.
