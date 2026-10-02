# Comprehensive Principles Catalog

This catalog documents the core foundational principles of software engineering, their canonical origins, mechanisms, concrete patterns, and detection heuristics.

---

## 1. Simplicity & Scope Management

### KISS — Keep It Simple, Stupid!
- **Origin & Core Meaning**: Coined by Kelly Johnson at Lockheed Skunk Works. Simplicity is a key design goal and unnecessary complexity should be avoided.
- **Reference**: [Wikipedia: KISS principle](https://en.wikipedia.org/wiki/KISS_principle)
- **Primary Heuristic**: Simple code takes less time to write, has fewer bugs, is easier to comprehend, and is drastically cheaper to modify.
- **Violation Signs**: Over-abstracted helper chains, multi-step pipeline architectures for straightforward procedural transformations, esoteric language idioms where standard constructs suffice.
- **Litmus Test**: *"Can a mid-level engineer who joined yesterday understand this logic within 60 seconds without tracing through 4 files?"*

### YAGNI — You Aren't Gonna Need It
- **Origin & Core Meaning**: Extreme Programming (XP) tenet formulated by Ron Jeffries: *"Always implement things when you actually need them, never when you just foresee that you may need them."*
- **Reference**: [Wikipedia: YAGNI](https://en.wikipedia.org/wiki/YAGNI)
- **Primary Heuristic**: Speculative generality incurs guaranteed costs today (writing, debugging, testing, cognitive overhead) to hedge against speculative, uncertain future requirements.
- **Violation Signs**: Configuration switches with only one option implemented, unused hook interfaces, generic type parameters for types that only ever take a single concrete class, "future-proofing" abstractions.
- **Litmus Test**: *"Does current production require this flexibility right now? If no, delete it."*

### Do the Simplest Thing That Could Possibly Work
- **Origin & Core Meaning**: Ward Cunningham (C2 Wiki / XP). Focus design decisions on finding the least complex solution that satisfies the immediate automated test suite.
- **Reference**: [C2 Wiki: DoTheSimplestThingThatCouldPossiblyWork](http://c2.com/xp/DoTheSimplestThingThatCouldPossiblyWork.html)
- **Primary Heuristic**: Build the minimal direct implementation first. Refactor towards abstraction only when forced by real, existing pressure.
- **Violation Signs**: Reaching for external state management, microservices, or complex meta-programming before writing a plain in-memory loop or function.
- **Litmus Test**: *"What is the most direct, boring implementation that passes all requirements?"*

### Avoid Premature Optimization
- **Origin & Core Meaning**: Donald Knuth: *"We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. Yet we should not pass up our opportunities in that critical 3%."*
- **Reference**: [Wikipedia: Program optimization](https://en.wikipedia.org/wiki/Program_optimization)
- **Primary Heuristic**: Write clear, idiomatic, maintainable code first. Never distort algorithmic clarity or architecture for speculative speed without profiling evidence.
- **Violation Signs**: Manual loop unrolling, bit-twiddling, hand-rolled object pools, or convoluted caching mechanisms introduced without flamegraphs or production telemetry proving a bottleneck.
- **Litmus Test**: *"Do we have profiler data proving this exact line is a bottleneck in the hot path?"*

---

## 2. Readability & Maintainability

### Don't Make Me Think
- **Origin & Core Meaning**: Steve Krug's usability maxim applied to source code. Source code should be immediately readable and understood with minimal cognitive load.
- **Reference**: [Steve Krug: Don't Make Me Think](http://www.sensible.com/dmmt.html)
- **Primary Heuristic**: Code is read orders of magnitude more frequently than it is written. Any mental translation step (e.g., decoding double negatives, nested ternaries, ambiguous variable names) is cognitive friction.
- **Violation Signs**: Nested ternaries (`a ? b ? c : d : e`), complex boolean logic without named helper variables, variables named `data`, `item`, `res2`, `flag`.
- **Litmus Test**: *"Does the reader have to pause, hold state in their head, or calculate a truth table to follow the execution flow?"*

### Write Code for the Maintainer
- **Origin & Core Meaning**: John Woods / Martin Golding (C2 Wiki): *"Always code as if the person who ends up maintaining your code is a violent psychopath who knows where you live."*
- **Reference**: [C2 Wiki: CodeForTheMaintainer](http://c2.com/cgi/wiki?CodeForTheMaintainer)
- **Primary Heuristic**: In 6 months, the future maintainer is often you—with complete amnesia of current assumptions. Write with total empathy for the reader.
- **Violation Signs**: Clever hacks, undocumented side effects, magic numbers, implicit dependency chains, monkey-patching, cryptic abbreviations.
- **Litmus Test**: *"If I were paged at 3:00 AM on Sunday to debug an outage here, would this code guide me or trap me?"*

### Principle of Least Astonishment (POLA)
- **Origin & Core Meaning**: Mike Cowlishaw / UNIX philosophy. A component should behave in a way that minimizes surprise to users and callers.
- **Reference**: [Wikipedia: Principle of least astonishment](https://en.wikipedia.org/wiki/Principle_of_least_astonishment)
- **Primary Heuristic**: A function named `get_user_profile()` should not mutate billing state. Methods should adhere to naming conventions, fulfill contract expectations, and avoid unexpected global mutations.
- **Violation Signs**: Getters that mutate internal state, commands that return unexpected side values, standard library idioms repurposed for radically different semantics, surprising silent fallbacks.
- **Litmus Test**: *"Does this function do exactly and only what its name, parameters, and return type signify?"*

---

## 3. Modularity & Structural Architecture

### Separation of Concerns (SoC)
- **Origin & Core Meaning**: Edsger W. Dijkstra (1974). Complex systems are manageable only when distinct concerns (e.g., persistence, presentation, business rules, transport) are isolated in separate, non-overlapping boundaries.
- **Reference**: [Wikipedia: Separation of concerns](https://en.wikipedia.org/wiki/Separation_of_concerns)
- **Primary Heuristic**: Each module focuses on a single distinct concern. Changes to one concern (e.g. switching database engines) do not ripple into another (e.g. calculation logic).
- **Violation Signs**: SQL queries embedded inside UI templates, HTTP request parsing mixed directly inside core domain algorithms.
- **Litmus Test**: *"If we change our UI or database engine tomorrow, how many business logic lines must change?"*

### Single Responsibility Principle (SRP)
- **Origin & Core Meaning**: Robert C. Martin ("Uncle Bob"), grounded in Tom DeMarco's cohesion concepts: *"A class or module should have one, and only one, reason to change."*
- **Reference**: [Wikipedia: Single-responsibility principle](https://en.wikipedia.org/wiki/Single_responsibility_principle)
- **Primary Heuristic**: A module should be responsible to one actor or business domain role.
- **Violation Signs**: "God classes" (`UserManager`, `OrderControllerHelper`, `AppEngine`) that handle database queries, format emails, perform cryptographic validation, and render JSON.
- **Litmus Test**: *"How many different business stakeholders or feature requests could require modifying this file?"* (If > 1, responsibility is split).

### Minimize Coupling (Low Coupling)
- **Origin & Core Meaning**: Larry Constantine & Glenford Myers (1974). Coupling is the degree of interdependence between software modules. Low coupling minimizes ripple effects.
- **Reference**: [Wikipedia: Coupling](https://en.wikipedia.org/wiki/Coupling_%28computer_programming%29)
- **Primary Heuristic**: Code blocks, functions, and classes should depend on as few external modules as possible, and depend on contracts rather than concrete implementations. Shared global state is the worst form of coupling.
- **Violation Signs**: Extensive use of global variables, classes requiring 15 injected services, circular dependencies, modifying class A breaks class Z.
- **Litmus Test**: *"Can this module be tested in isolation with zero or minimal mock setup?"*

### Maximize Cohesion (High Cohesion)
- **Origin & Core Meaning**: Larry Constantine & Glenford Myers (1974). Cohesion measures how strongly-related and focused the internal responsibilities of a module are.
- **Reference**: [Wikipedia: Cohesion](https://en.wikipedia.org/wiki/Cohesion_%28computer_science%29)
- **Primary Heuristic**: Elements that change together, serve the same goal, or manipulate the same core domain data belong together in the same file or package.
- **Violation Signs**: Utility junk-drawers (`Utils.java`, `helpers.ts`, `common.py`) containing unrelated string manipulation, date math, network calls, and regex parsing.
- **Litmus Test**: *"Do all methods in this class operate on the same core internal state?"*

---

## 4. Abstraction, Encapsulation & Information Hiding

### DRY — Don't Repeat Yourself
- **Origin & Core Meaning**: Andy Hunt & Dave Thomas (*The Pragmatic Programmer*): *"Every piece of knowledge must have a single, unambiguous, authoritative representation within a system."*
- **Reference**: [Wikipedia: Don't repeat yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- **Primary Heuristic**: Avoid duplication of *knowledge* and *business logic*. Note: DRY is about domain knowledge, not incidental structural similarity.
- **Violation Signs**: Copy-pasted calculation blocks, duplicate validation rules spread across frontend and backend without a shared schema, copy-pasted regex patterns.
- **Litmus Test**: *"If the business rule changes, do I have to update code in more than one place?"*

### Abstraction Principle
- **Origin & Core Meaning**: Benjamin C. Pierce (*Types and Programming Languages*): *"Each significant piece of functionality in a program should be implemented in just one place in the source code."*
- **Reference**: [Wikipedia: Abstraction principle](https://en.wikipedia.org/wiki/Abstraction_principle_%28programming%29)
- **Primary Heuristic**: When identical or closely related logic occurs in multiple places, lift the invariant portion into an abstraction (function, class, or parameter).
- **Violation Signs**: Duplicated algorithms with hardcoded constant variations instead of parameterized abstractions.
- **Litmus Test**: *"Have we extracted the invariant mechanism away from the variant parameters?"*

### Code Reuse is Good
- **Origin & Core Meaning**: Foundational software engineering principle dating back to subroutine invention (Maurice Wilkes, 1951). Reusing proven code drastically reduces bugs and accelerates delivery.
- **Reference**: [Wikipedia: Code reuse](https://en.wikipedia.org/wiki/Code_reuse)
- **Primary Heuristic**: Leverage existing battle-tested libraries, internal primitives, and utility contracts instead of reinventing wheels.
- **Violation Signs**: Hand-rolling custom JSON parsers, custom cryptographic routines, or custom date/time math instead of using canonical standard libraries.
- **Litmus Test**: *"Has this problem been solved and debugged by millions of developers already?"*

### Hide Implementation Details (Information Hiding)
- **Origin & Core Meaning**: David Parnas (1972): *"Information hiding is the principle of segregating design decisions that are most likely to change, protecting other parts of the program from extensive modifications."*
- **Reference**: [Wikipedia: Information hiding](https://en.wikipedia.org/wiki/Information_Hiding)
- **Primary Heuristic**: Clients should depend only on public interfaces and contracts, never on internal data structures, storage mechanisms, or private fields.
- **Violation Signs**: Public mutable fields, external callers accessing raw database connection objects directly from a service, exposing internal list pointers that callers mutate.
- **Litmus Test**: *"Can we swap the internal storage representation (e.g. from an Array to a Hash Map or SQLite) without altering any caller code?"*

### Law of Demeter (Principle of Least Knowledge)
- **Origin & Core Meaning**: Ian Holland at Northeastern University (1987). A given object should assume as little as possible about the structure or properties of anything else: *"Only talk to your immediate friends."*
- **Reference**: [Wikipedia: Law of Demeter](https://en.wikipedia.org/wiki/Law_of_Demeter)
- **Primary Heuristic**: A method `m` of object `O` should only invoke methods of: `O` itself, parameters passed to `m`, objects created within `m`, or direct components of `O`. Avoid dot-chains ("train wrecks").
- **Violation Signs**: `order.getCustomer().getAddress().getZipCode().validate()`. If the internal structure of Customer or Address changes, Order breaks.
- **Litmus Test**: *"Are you navigating through someone else's internal object graph across more than one dot?"*

---

## 5. Evolutive Resilience & Change

### Open/Closed Principle (OCP)
- **Origin & Core Meaning**: Bertrand Meyer (1988) / Robert C. Martin: *"Software entities (classes, modules, functions) should be open for extension, but closed for modification."*
- **Reference**: [Wikipedia: Open/closed principle](https://en.wikipedia.org/wiki/Open_Closed_Principle)
- **Primary Heuristic**: You should be able to introduce new behavior or new data types without modifying existing, tested, deployed code. Use polymorphism, strategy patterns, or dependency injection.
- **Violation Signs**: Giant `switch` or `if/else if/else` statements inspecting type discriminators (`switch (shape.type) { case 'circle': ... case 'square': ... }`) whenever a new variant is introduced.
- **Litmus Test**: *"When adding a new feature or provider, do I modify 10 existing switch statements, or do I just write 1 new class/module implementing an interface?"*

### Embrace Change
- **Origin & Core Meaning**: Kent Beck (*Extreme Programming Explained: Embrace Change*). Change is the only constant in software development. Architecture must be optimized for adaptability rather than monumental static perfection.
- **Reference**: [Kent Beck: Extreme Programming Explained](http://www.amazon.com/gp/product/0321278658)
- **Primary Heuristic**: Make code cheap to change. Decoupled modules, clean test suites, short feedback loops, and reversible decisions are superior to rigid, predictive upfront specifications.
- **Violation Signs**: Heavy upfront speculative frameworks, architectures that require weeks of refactoring to support a slight business requirement shift, fear of modifying legacy code due to lack of tests.
- **Litmus Test**: *"How easily can this system accommodate the opposite of today's business requirement?"*

---

## 6. Functional Reusability & Predictability

Functional programming (FP) achieves reusability by composing small, stateless, and predictable functions rather than relying on deep object inheritance hierarchies. By separating data from behavior and ensuring functions have zero side effects, you create independent building blocks that can easily be combined to solve different problems.

### Build Around Pure Functions
- **Origin & Core Meaning**: Mathematical lambda calculus (Alonzo Church) applied to software engineering. A function is pure if it always returns the exact same output for the same input, and causes zero observable side effects (no mutation of external state, no console I/O, no network calls).
- **Primary Heuristic**: Pure functions are completely self-contained, stateless, and referentially transparent. You can safely copy, move, or import them into entirely new contexts without worrying about global state or ambient environment.
- **Violation Signs**: Functions reading or mutating global variables, methods that modify their input arguments, unexpected telemetry or logging buried inside business calculation functions.
- **Litmus Test**: *"Can I replace the function call `f(x)` with its return value in my tests without changing the program's behavior?"*

### Parameterize Behavior (Higher-Order Functions)
- **Origin & Core Meaning**: Functions as first-class citizens. A Higher-Order Function (HOF) accepts other functions as arguments or returns a function.
- **Primary Heuristic**: Instead of writing multiple functions that do almost the same thing, isolate the specific logic that changes and pass it in as a parameter. Standard iterators (`map`, `filter`, `reduce`) are classic examples where traversal logic is reused and transformation logic is parameterized.
- **Violation Signs**: Copy-pasting a loop with a slight modification to the filtering check or formatting logic, or creating bloated class inheritance trees to override a single inner step (Template Method antipattern).
- **Litmus Test**: *"Can we extract the structural loop or orchestration logic away from the domain transformation callback?"*

### Embrace Currying & Partial Application
- **Origin & Core Meaning**: Moses Schönfinkel & Haskell Curry. Currying translates a function of multiple arguments into a sequence of unary functions. Partial application binds a subset of arguments upfront, returning a specialized function.
- **Primary Heuristic**: Allows creating highly generic core utilities and spinning off specialized, pre-configured versions throughout an application without rewriting logic or passing ambient dependencies everywhere.
- **Violation Signs**: Threading configuration objects or API clients through 6 layers of function calls; repetitive boilerplate calling the same multi-argument utility with identical leading arguments.
- **Litmus Test**: *"Can we bind configuration or context once at bootstrap, passing a zero-argument or single-argument worker function to business callers?"*

### Rely on Function Composition
- **Origin & Core Meaning**: Mathematical category theory & Unix pipeline philosophy (`|`). Function composition pipes the output of one function directly into the input of the next ($h = g \circ f$).
- **Primary Heuristic**: Instead of building monolithic functions, write single-purpose utilities and snap them together like Lego bricks:
  `const processEmail = compose(validateEmail, sanitizeInput);`
- **Violation Signs**: Monolithic 80-line procedural routines where validation, normalization, calculation, and formatting are interleaved in an indivisible block.
- **Litmus Test**: *"Can this workflow be expressed as a linear pipeline of small, independently testable single-responsibility transformations?"*

### Enforce Immutability & Separate Data from Behavior
- **Origin & Core Meaning**: Pure FP data model. Data structures are treated as read-only values. Transformations return new copies, leaving the original data untouched.
- **Primary Heuristic**: When data is immutable, you eliminate accidental side effects and temporal coupling. Parallel processing, debugging, time-travel logging, and multi-threaded reuse become safe and predictable.
- **Violation Signs**: Calling `list.sort()` or `delete user.role` in-place on input objects; bugs where modifying state in module A silently breaks module B; complex defensive cloning scattered everywhere.
- **Litmus Test**: *"Does this function guarantee that caller data structures remain 100% byte-for-byte identical before and after invocation?"*
