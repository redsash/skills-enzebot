# Principle Tensions & Practical Resolution Heuristics

Software engineering principles are not absolute dogma; they are vectors of design tension that must be balanced against context. When two principles pull in opposite directions, use the heuristics below to break the tie.

---

## 1. DRY vs. YAGNI & KISS (The Wrong Abstraction Trap)

### The Conflict
- **DRY** encourages extracting duplicated logic into a shared abstraction.
- **YAGNI & KISS** warn against building abstractions before requirements stabilize.

### Sandi Metz's Rule of Abstraction
> *"Duplication is far cheaper than the wrong abstraction."*

When developers prematurely abstract two blocks of code that happen to look identical today, they couple two unrelated domain concepts. When Requirement A changes tomorrow but Requirement B does not, developers introduce conditional flags (`if (isTypeB)`) into the shared abstraction, producing an unmaintainable hydra.

### The Resolution Heuristic: The Rule of Three (AHA)
1. **1st Occurrence**: Write the simplest direct code (KISS).
2. **2nd Occurrence**: Duplicate the code. Notice the duplication, but do not abstract yet. The duplication may be accidental rather than semantic.
3. **3rd Occurrence**: Now that you have three concrete instances exhibiting genuine invariant behavior, extract a clean abstraction (DRY).
- **AHA (Avoid Hasty Abstractions)**: Prefer duplication over a speculative or leaky abstraction until the domain model stabilizes.

---

## 2. Open/Closed Principle (OCP) vs. KISS & YAGNI

### The Conflict
- **OCP** urges making modules open for extension (via interfaces, strategies, dependency injection, plugin registries).
- **KISS & YAGNI** urge keeping designs minimal without anticipatory scaffolding.

### The Resolution Heuristic: Extension on Demand
1. **Default to Direct Simplicity**: For the first 1–2 variants, use straightforward conditionals or match statements if the logic is concise (<15 lines).
2. **Pivot to OCP When**:
   - The set of variants is dynamic or unbounded (e.g. user plugins, payment gateways, file format exporters).
   - Modifying the existing switch statement frequently causes regressions in other variants.
   - Different teams or modules own different variants.
3. **Avoid Lasagna Code**: Do not create an `IUserValidatorFactoryProviderImpl` for a service with a single static rule.

---

## 3. Separation of Concerns (SoC) vs. Locality of Behavior (LoB)

### The Conflict
- **Separation of Concerns** separates distinct layers (e.g. database query, validation, serialization, presentation) across different files/modules.
- **Locality of Behavior** (and Krug's *Don't Make Me Think*) posits that code is easiest to understand when the behavior of a unit can be inspected in one place without jumping between 5 directories.

### The Resolution Heuristic: Semantic vs. Incidental Boundaries
- Separate concerns that have **different rates of change** or **different external dependencies** (e.g. database IO vs core domain math).
- **Do not separate** tightly coupled steps that always change together simply because they belong to different abstract categories.
- If understanding a 20-line feature requires opening 6 files (`Controller`, `Service`, `Repository`, `Entity`, `DTO`, `Mapper`), you have traded cognitive clarity for bureaucratic modularity.

---

## 4. Law of Demeter vs. Fluent APIs & Functional Pipelines

### The Conflict
- **Law of Demeter** forbids calling methods across multiple dots (`a.b().c().d()`).
- Modern fluent APIs, LINQ, functional streams, and builders rely heavily on chained method calls:
  `users.filter(u => u.isActive).map(u => u.email).toList()`.

### The Resolution Heuristic: Identity Navigation vs. Transformation Pipelines
- **Violation (Train Wreck)**: Navigating through distinct object ownership boundaries to reach an internal dependency:
  `order.getCustomer().getWallet().getPaymentMethod().charge()`.
  *(Order reaches into Customer, reaches into Wallet, reaches into PaymentMethod. If Wallet changes, Order breaks).*
- **Valid (Pipeline / Monad / Builder)**: Transformations where each step operates on the same underlying stream type or builds a single object:
  `QueryBuilder.select("*").from("users").where("id = ?", id).build()`.
  *This does not violate Demeter because no private collaborator object graphs are being traversed.*

---

## 5. Performance vs. Readability & Maintainability

### The Conflict
- Performance tuning often demands in-place mutations, unrolled loops, custom data packing, or caching.
- Maintainability demands immutability, standard abstractions, and clean intent-revealing code.

### The Resolution Heuristic: The 3-Step Performance Sequence
1. **Make it work**: Build the simplest, cleanest implementation satisfying all tests (KISS, Krug).
2. **Make it right**: Ensure contracts, error cases, and boundaries are robust (SRP, POLA).
3. **Make it fast (ONLY with profiler data)**:
   - Is there a measured SLA violation or flamegraph showing this code is in the 3% hot path?
   - If NO: Keep the clean, readable version.
   - If YES: Optimize the hot path, isolate the optimization behind a well-documented boundary (Information Hiding), and retain benchmarks in CI.
