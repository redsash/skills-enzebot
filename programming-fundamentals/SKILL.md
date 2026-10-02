---
name: programming-fundamentals
description: >-
  Applies foundational software engineering principles (DRY, KISS, YAGNI, Single Responsibility, Low Coupling, High Cohesion, Law of Demeter, Information Hiding, Principle of Least Astonishment, and Kent Beck's Embrace Change) to design, review, refactor, and simplify code. Use when reviewing code, refactoring architectures, evaluating design trade-offs, simplifying over-engineered logic, or auditing code maintainability.
---

# Programming Fundamentals

A comprehensive framework and execution engine for applying timeless software engineering and design principles across code creation, architecture design, peer reviews, and refactoring.

---

## When to Use This Skill

- **Code Reviews & PR Audits**: Reviewing pull requests or existing modules for structural smells, maintainability risks, unexpected side effects, or excessive coupling.
- **Architectural Design & Scaffolding**: Establishing clean module boundaries, interface contracts, and responsibility allocations before writing code.
- **Simplification & De-engineering**: Refactoring bloated "god classes", untangling lasagna abstractions, and cutting speculative features down to the simplest working core.
- **Tension Arbitration**: Deciding between competing trade-offs (e.g., when DRY clashes with YAGNI, or when decoupling threatens cognitive clarity).
- **Automated Smells Auditing**: Running static checks for long methods, deep nesting, and train wrecks via `scripts/audit_code_smells.py`.
- **Do not use for**: Trivial single-character typo fixes, mechanical syntax translations without structural implications, or purely visual CSS styling adjustments.

---

## The Core Principles Taxonomy

The 18 foundational principles are organized into five cohesive clusters:

```
                      SOFTWARE SYSTEM HEALTH
                                 ▲
  ┌──────────────────────────────┼──────────────────────────────┐
  │                              │                              │
[Simplicity & Frugality]  [Readability & Empathy]   [Architecture & Modularity]
• KISS                     • Don't Make Me Think    • Separation of Concerns
• YAGNI                    • Code for the Maintainer• Single Responsibility (SRP)
• Simplest Thing That Works• Least Astonishment     • Low Coupling & High Cohesion
• Avoid Premature Optimize
  │                              │
  └──────────────────────────────┴──────────────────────────────┘
                                 │
  ┌──────────────────────────────┴──────────────────────────────┐
  │                                                             │
[Abstraction & Encapsulation]                       [Evolutive Resilience]
• DRY & Abstraction Principle                       • Open/Closed Principle (OCP)
• Code Reuse is Good                                • Embrace Change (Kent Beck)
• Hide Implementation Details
• Law of Demeter (Least Knowledge)
```

Deep definitions, canonical references, and historical attributions are cataloged in [Principles Catalog](references/principles-catalog.md). Trade-off heuristics are detailed in [Tension Resolution Matrix](references/tensions-and-heuristics.md).

---

## Operational Workflows

Select the appropriate workflow for the task at hand:

### Workflow 1: Pre-Code & Architectural Boundary Design
Use when architecting a new feature, service, or module from scratch.

- [ ] **Step 1: The YAGNI & Simplest-Thing Gate**:
  - Ask: *"What is the simplest thing that could possibly work?"*
  - Strip speculative parameters, future-proofing plugin layers, and anticipatory database columns. Solve today's exact requirements first.
- [ ] **Step 2: Separation of Concerns & Cohesion**:
  - Partition boundaries along distinct axes of change: domain business math, persistence/IO, network transport, and presentation.
  - Group functions that manipulate the same core domain data into cohesive modules.
- [ ] **Step 3: Contract Design & Information Hiding**:
  - Expose only minimal, well-typed public contracts. Keep internal data representations strictly private.
  - Enforce the **Law of Demeter**: ensure callers talk only to immediate collaborators, never traversing internal object graphs.
- [ ] **Step 4: Design for Change (OCP & Modularity)**:
  - Identify the 1 or 2 vectors most likely to change (e.g. payment providers, export formats). Use polymorphism or strategy interfaces so new capabilities can be added without modifying tested core logic.

---

### Workflow 2: Code Review & Quality Audit
Use when inspecting PRs or assessing legacy source code.

- [ ] **Step 1: Automated Static Audit**:
  - Run the bundled smell detector across target files:
    ```bash
    python3 scripts/audit_code_smells.py <path-to-file-or-dir>
    ```
  - Note lines flagged for excessive function length (>50 lines), deep nesting (>4 levels), long argument lists, or Demeter train wrecks.
- [ ] **Step 2: The "Don't Make Me Think" Readability Pass**:
  - Check variable naming, boolean conditions, and early returns.
  - Eliminate double negatives, unreadable nested ternaries, and magic literals.
- [ ] **Step 3: The Maintainer & Astonishment Audit**:
  - Inspect every public function: Does it do *strictly* what its name suggests?
  - Search for hidden side effects (e.g. a getter that mutates global state, or silently swallowed exceptions like `except: pass`).
- [ ] **Step 4: Coupling & DRY Inspection**:
  - Count dependencies: Does this class import 12 other domain services?
  - Verify that critical business rules are not duplicated across multiple endpoints.

---

### Workflow 3: Simplification & De-Slop Refactoring
Use when simplifying bloated, over-engineered, or brittle code.

- [ ] **Step 1: Prune Speculative Abstractions (YAGNI & KISS)**:
  - Collapse single-implementation interfaces, empty adapter layers, and pass-through wrapper functions that add no logic.
- [ ] **Step 2: Break Apart God Classes (SRP & SoC)**:
  - If a file has multiple reasons to change (e.g. database schema changes AND UI layout changes require editing it), extract sub-components.
- [ ] **Step 3: Straighten Control Flow (Guard Clauses)**:
  - Replace deep nested `if/else` ladders with top-of-function guard clauses and early returns.
- [ ] **Step 4: Verify Non-Regression**:
  - Run existing test suites or write characterization tests to guarantee behavior invariance before and after simplification.

---

## Critical Heuristics & Principle Trade-offs

| Conflict | Tension Point | Practical Tie-Breaker Heuristic |
| :--- | :--- | :--- |
| **DRY vs. YAGNI** | Extracting shared logic vs. avoiding premature coupling. | **The Rule of Three (AHA)**: Duplication is cheaper than the wrong abstraction. Duplicate twice; abstract only on the 3rd genuine recurrence. |
| **OCP vs. KISS** | Complex plugin architectures vs. direct simple code. | **Extension on Demand**: Start with direct conditionals. Introduce polymorphism/interfaces only when variants exceed 2 or cross module boundaries. |
| **SoC vs. Readability** | Spreading code into 6 layers vs. Locality of Behavior. | **Semantic Boundaries**: Separate IO from business logic, but do not scatter tightly coupled 5-line operations across separate directories. |
| **Performance vs. Maintainability** | Bitwise/manual micro-optimizations vs. clean readable code. | **Empirical Proof Only**: Avoid premature optimization 97% of the time. Optimize only with flamegraph evidence from hot production paths. |
| **Law of Demeter vs. Fluent APIs** | Chained dot-calls (`a.b().c()`). | **Distinguish Navigation from Pipeline**: Deep object graph traversal across distinct identities violates Demeter; builder patterns and stream transformations do not. |

---

## Gotchas & Anti-Patterns

- **The DRY Trap (Wrong Abstraction)**: Combining two blocks of code that look syntactically similar today but represent distinct business concepts. When one business requirement changes, the shared helper becomes polluted with flags.
- **Lasagna Code (The Over-Abstraction Smokescreen)**: Creating dozens of 2-line files (`Controller -> Service -> Manager -> Helper -> Handler -> Repo`) in the name of SRP. This destroys "Don't Make Me Think".
- **The "Clever Code" Ego Trap**: Writing dense, unreadable one-liners. Violates "Code for the Maintainer" and the "Principle of Least Astonishment".
- **Cargo-Cult Demeter Getters**: Adding a hundred wrapper getters (`getZipCode() { return address.getZipCode(); }`) to an enclosing class instead of passing the required dependency directly.
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
