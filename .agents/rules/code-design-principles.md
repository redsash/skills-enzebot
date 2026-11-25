# Code Design Principles

Always-on engineering heuristics distilled from `programming-fundamentals`. Prefer simple, direct, readable code over speculative abstractions.

## Design Tie-Breakers

1. **Rule of Three / AHA (DRY vs. YAGNI)**: Duplication is cheaper than the wrong abstraction. Keep similar logic separate twice; extract a shared abstraction only on the third genuine invariant recurrence.
2. **Functional Core, Imperative Shell (SoC / FP vs. OOP)**: Keep domain calculations pure and stateless; push database, network, and filesystem I/O to an outer imperative shell. Prefer function composition and higher-order callbacks over inheritance hierarchies.
3. **Immutability by Default**: Return new copies rather than mutating caller inputs (`toSorted()` / `sorted()` over in-place `.sort()`). Only mutate in-place when profiling identifies a verified hot-path bottleneck, and isolate it inside a pure boundary.
4. **Locality of Behavior vs. Lasagna Code**: Separate concerns with distinct rates of change or external dependencies, but collapse single-implementation interfaces, empty adapters, and multi-file pass-through chains that scatter a 20-line flow across six files.
5. **Law of Demeter vs. Fluent Pipelines**: Never navigate across distinct ownership boundaries (`order.getCustomer().getWallet().charge()`); homogeneous builder or stream chains (`items.filter(...).map(...)`) are fine.
6. **Explicit Over Point-Free**: Use tacit pipelines only when trivially readable; introduce named arguments whenever argument plumbing requires mental tracing.

## Anti-Pattern Guards

- **No Silent Error Swallowing**: Never write bare `except: pass` or empty `catch {}` blocks; handle, log with context, or rethrow typed errors.
- **No Hidden Input/Global Mutations**: Functions whose names imply reads (`get_*`, `compute_*`) must never mutate caller parameters or global state (Principle of Least Astonishment).
- **Composition Over Inheritance**: Parameterize varying steps with functions or strategy callbacks instead of multi-level class inheritance trees.
- **Test Behavior, Not Internals**: Assert public inputs and outputs; avoid mocking private helper calls that couple tests to implementation details.
