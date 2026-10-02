---
name: programming-fundamentals
description: >-
  Applies foundational software engineering principles (DRY, KISS, YAGNI, Single Responsibility, Low Coupling, High Cohesion, Law of Demeter, Information Hiding, Principle of Least Astonishment, and Kent Beck's Embrace Change) along with functional programming reusability (Pure Functions, Immutability, Higher-Order Functions, Currying, and Composition) to design, review, refactor, and simplify code. Use when reviewing code, refactoring architectures, evaluating design trade-offs, simplifying over-engineered logic, or auditing code maintainability.
---

# Programming Fundamentals

A comprehensive framework and execution engine for applying timeless software engineering and design principles across code creation, architecture design, peer reviews, and refactoring.

---

## When to Use This Skill

- **Code Reviews & PR Audits**: Reviewing pull requests or existing modules for structural smells, maintainability risks, unexpected side effects, or excessive coupling.
- **Architectural Design & Scaffolding**: Establishing clean module boundaries, interface contracts, and responsibility allocations before writing code.
- **Simplification & De-engineering**: Refactoring bloated "god classes", untangling lasagna abstractions, and cutting speculative features down to the simplest working core.
- **Functional Reusability & State Control**: Refactoring brittle class inheritance trees into pure, composable higher-order pipelines and immutable dataflows.
- **Tension Arbitration**: Deciding between competing trade-offs (e.g., DRY vs. YAGNI, or OOP encapsulation vs. FP data/logic separation).
- **Automated Smells Auditing**: Running static checks for long methods, deep nesting, train wrecks, and argument mutations via `scripts/audit_code_smells.py`.
- **Do not use for**: Trivial single-character typo fixes, mechanical syntax translations without structural implications, or purely visual CSS styling adjustments.

---

## The Core Principles Taxonomy

The foundational principles are organized into six cohesive clusters:

```
                          SOFTWARE SYSTEM HEALTH
                                     ▲
  ┌──────────────────────────────────┼──────────────────────────────────┐
  │                                  │                                  │
[Simplicity & Frugality]      [Readability & Empathy]      [Architecture & Modularity]
• KISS                         • Don't Make Me Think        • Separation of Concerns
• YAGNI                        • Code for the Maintainer    • Single Responsibility (SRP)
• Simplest Thing That Works    • Least Astonishment (POLA)  • Low Coupling & High Cohesion
• Avoid Premature Optimization
  │                                  │                                  │
  └──────────────────────────────────┼──────────────────────────────────┘
                                     │
  ┌──────────────────────────────────┴──────────────────────────────────┐
  │                                                                     │
[Abstraction & Encapsulation]  [Evolutive Resilience]        [Functional Reusability]
• DRY & Abstraction Principle  • Open/Closed Principle (OCP) • Pure Functions (Stateless)
• Code Reuse is Good           • Embrace Change (Kent Beck)   • Parameterize Behavior (HOFs)
• Hide Implementation Details                                 • Currying & Partial Application
• Law of Demeter (Least Know)                                 • Function Composition
                                                              • Enforced Immutability
```

Deep definitions, canonical references, and historical attributions are cataloged in [Principles Catalog](references/principles-catalog.md). Trade-off heuristics are detailed in [Tension Resolution Matrix](references/tensions-and-heuristics.md).

---

## Object-Oriented vs. Functional Reusability

When designing for reuse, choose the appropriate paradigm based on domain needs:

| Dimension | Object-Oriented Programming (OOP) | Functional Programming (FP) | Fundamentals Impact |
| :--- | :--- | :--- | :--- |
| **Core Mechanism** | **Inheritance & Mixins** (Shared state & methods) | **Composition & HOFs** (Passing functions) | Composition avoids rigid, fragile inheritance trees. |
| **Data & Logic** | **Encapsulated together** inside classes | **Strictly separated** (Data structures + Pure fns) | Any pure function can operate on standard data formats. |
| **Scale of Reuse** | **Large, stateful class hierarchies** | **Small, stateless utility functions** | Small functions snap together cleanly like Lego bricks. |
| **Predictability** | **Risk of side effects** from shared mutable state | **Zero side effects** (Pure functions & immutability) | Maximizes Least Astonishment and eliminate temporal bugs. |

---

## Operational Workflows

Select the appropriate workflow for the task at hand:

### Workflow 1: Pre-Code & Architectural Boundary Design
Use when architecting a new feature, service, or module from scratch.

- [ ] **Step 1: The YAGNI & Simplest-Thing Gate**:
  - Ask: *"What is the simplest thing that could possibly work?"*
  - Strip speculative parameters, future-proofing plugin layers, and anticipatory database columns. Solve today's exact requirements first.
- [ ] **Step 2: Separation of Concerns & FCIS (Functional Core, Imperative Shell)**:
  - Keep domain calculations and business rules completely pure and stateless.
  - Push side effects (database I/O, network calls, filesystem access) to the outer imperative shell.
- [ ] **Step 3: Contract Design & Information Hiding**:
  - Expose only minimal, well-typed public contracts. Keep internal representations strictly private.
  - Enforce the **Law of Demeter**: ensure callers talk only to immediate collaborators, never traversing internal object graphs.
- [ ] **Step 4: Design for Change (OCP & Parameterized Behavior)**:
  - Identify vectors most likely to change. Use Higher-Order Functions (HOFs) or strategy interfaces so new capabilities can be passed without modifying tested core logic.

---

### Workflow 2: Code Review & Quality Audit
Use when inspecting PRs or assessing legacy source code.

- [ ] **Step 1: Automated Static Audit**:
  - Run the bundled smell detector across target files:
    ```bash
    python3 scripts/audit_code_smells.py <path-to-file-or-dir>
    ```
  - Note lines flagged for excessive function length (>50 lines), deep nesting (>4 levels), long argument lists, Demeter train wrecks, or in-place mutations.
- [ ] **Step 2: The "Don't Make Me Think" Readability Pass**:
  - Check variable naming, boolean conditions, and early returns.
  - Eliminate double negatives, unreadable nested ternaries, and magic literals.
- [ ] **Step 3: The Maintainer, Purity & Astonishment Audit**:
  - Inspect every public function: Does it do *strictly* what its name suggests?
  - Search for hidden side effects: Does a getter mutate internal state? Does a function mutate its input parameters? Are exceptions silently swallowed?
- [ ] **Step 4: Coupling & DRY Inspection**:
  - Count dependencies: Does this class import 12 other domain services?
  - Verify that critical business rules are not duplicated across multiple endpoints.

---

### Workflow 3: Simplification & De-Slop Refactoring
Use when simplifying bloated, over-engineered, or brittle code.

- [ ] **Step 1: Prune Speculative Abstractions (YAGNI & KISS)**:
  - Collapse single-implementation interfaces, empty adapter layers, and pass-through wrapper functions that add no logic.
- [ ] **Step 2: Break Apart God Classes into Composable Functions (SRP & Composition)**:
  - Extract stateless utility functions out of bloated classes. Snap them together using function composition pipelines.
- [ ] **Step 3: Enforce Immutability (Eliminate Temporal Coupling)**:
  - Replace in-place mutations (`list.sort()`, `delete obj[key]`) with pure returns of updated copies.
- [ ] **Step 4: Straighten Control Flow (Guard Clauses)**:
  - Replace deep nested `if/else` ladders with top-of-function guard clauses and early returns.
- [ ] **Step 5: Verify Non-Regression**:
  - Run existing test suites or write characterization tests to guarantee behavior invariance before and after simplification.

---

## Critical Heuristics & Principle Trade-offs

| Conflict | Tension Point | Practical Tie-Breaker Heuristic |
| :--- | :--- | :--- |
| **DRY vs. YAGNI** | Extracting shared logic vs. avoiding premature coupling. | **The Rule of Three (AHA)**: Duplication is cheaper than the wrong abstraction. Duplicate twice; abstract only on the 3rd genuine recurrence. |
| **OCP vs. KISS** | Complex plugin architectures vs. direct simple code. | **Parameterize Behavior**: Prefer passing a function callback (HOF) over creating an entire abstract class/factory hierarchy. |
| **SoC vs. Readability** | Spreading code into 6 layers vs. Locality of Behavior. | **Semantic Boundaries**: Separate IO from business logic (FCIS), but do not scatter tightly coupled 5-line operations across separate directories. |
| **Performance vs. Immutability** | Copying data structures vs. in-place mutations. | **Immutability by Default**: Mutate in-place only if profiling telemetry proves allocation overhead in the 3% hot path. Isolate inside a pure boundary. |
| **Law of Demeter vs. Fluent APIs** | Chained dot-calls (`a.b().c()`). | **Distinguish Navigation from Pipeline**: Deep object graph traversal across distinct identities violates Demeter; builder patterns and stream transformations do not. |
| **Point-Free Style vs. Krug** | Tacit composition vs. code readability. | **Explicit Over Clever**: Use point-free pipelines only when obvious. Introduce named arguments if tracing inputs requires mental gymnastics. |

---

## Gotchas & Anti-Patterns

- **The In-Place Mutation Trap**: Functions that silently mutate incoming objects or lists. Breaks "Write Code for the Maintainer" and causes spooky action-at-a-distance bugs.
- **The DRY Trap (Wrong Abstraction)**: Combining two blocks of code that look syntactically similar today but represent distinct business concepts. When one business requirement changes, the shared helper becomes polluted with flags.
- **Lasagna Code (The Over-Abstraction Smokescreen)**: Creating dozens of 2-line files (`Controller -> Service -> Manager -> Helper -> Handler -> Repo`) in the name of SRP. This destroys "Don't Make Me Think".
- **The "Clever Code" Ego Trap**: Writing dense, unreadable one-liners. Violates "Code for the Maintainer" and the "Principle of Least Astonishment".
- **Point-Free Obfuscation**: Chaining 10 combinators (`compose(curry, flip, bimap)`) to avoid naming arguments, destroying cognitive readability.
- **Mockist Coupling**: Writing unit tests that mock 10 internal private method calls instead of asserting public outputs. This couples tests to implementation details and prevents safe refactoring.

---

## Standard Review & Audit Output Template

When delivering a code review, architectural critique, or refactoring proposal, format the assessment using this structured template:

```markdown
# Programming Fundamentals Audit: [Module / PR Name]

## Executive Summary
- **Overall Maintainability Score**: [High / Moderate / At-Risk]
- **Core Strengths**: [1–2 principles well-respected]
- **Primary Bottlenecks**: [Top 2 principles violated]

## Principle Violation Analysis
| File & Line | Principle Violated | Observed Smell | Recommended Remediation |
| :--- | :--- | :--- | :--- |
| `src/order.ts:42` | **Law of Demeter** | Deep train wreck: `user.getAccount().getTier().apply()` | Delegate discount application to `user` or pass `tier` directly. |
| `src/billing.py:88` | **Least Astonishment** | Silent error suppression (`except Exception: pass`) | Log exception context and surface typed `PaymentFailedError`. |
| `src/cart.js:31` | **Immutability / Purity** | In-place parameter mutation (`items.sort()`) | Use `toSorted()` or slice copy to prevent mutating caller state. |
| `src/helper.go:12` | **KISS / YAGNI** | Unused generic plugin registry for single parser | Inline direct parser function; remove interface overhead. |

## Before / After Refactoring Snippets
### Problematic (Smell)
```[language]
// Before snippet showing violation
```

### Remediated (Fundamentals-Aligned)
```[language]
// After snippet demonstrating clean, readable, robust code
```

## Actionable Next Steps
1. [Highest ROI refactoring action]
2. [Simplification / deletion candidate]
```
