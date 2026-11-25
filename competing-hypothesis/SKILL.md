---
name: competing-hypothesis
description: >-
  Evaluates ambiguous or contradictory evidence against mutually exclusive explanations using Richards Heuer's Analysis of Competing Hypotheses (ACH). Use on /competing-hypothesis or when diagnosing elusive bugs, investigating incidents, or choosing among rival root causes. Do not use for deterministic stack-trace bugs, multi-persona advisory debates (perspectives), or integral/AQAL strategic framing (strategic-thinking-5d).
taxonomy:
  phase: [deliberate]
  modality: [lens]
  domain: [architecture-strategy, operations-reliability]
  interaction: interactive
metadata:
  model-tier: "deep"
  effort: "high"
  invocation: "hybrid"
---

# Analysis of Competing Hypotheses (ACH)

A rigorous methodology developed by Richards Heuer at the CIA to evaluate multiple competing explanations for ambiguous, incomplete, or contradictory observations. Unlike intuitive troubleshooting—which typically latches onto an early favorite hypothesis and seeks confirming data—ACH systematically works to **disprove and eliminate** hypotheses by focusing on inconsistencies.

---

## When to Use This Skill
- **Elusive Production Incidents**: Intermittent distributed failures, performance regressions, or memory leaks where multiple root-cause theories exist.
- **Security & Forensic Investigations**: Anomalous network traffic, unauthorized access events, or suspected breaches with conflicting artifacts.
- **Strategic Risk & Intelligence Scenarios**: High-stakes decisions where confirmation bias or premature cognitive closure poses severe risks.
- **Do not use for**: Deterministic, single-cause bugs where an explicit stack trace or compiler error directly pinpoints the defect.

---

## Workflow / Procedure

### Step 1: Hypotheses Generation
1. State the focal question in a specific, testable form (e.g., *"What is causing the 504 timeouts on the checkout service?"*).
2. Generate an exhaustive set of mutually exclusive hypotheses ($H_1, H_2, \dots, H_n$):
   - Include non-obvious alternatives (e.g., upstream network provider throttling, DNS resolution stalls).
   - Prevent "favorite hypothesis" bias: treat all hypotheses with equal initial agnosticism.

### Step 2: Diagnostic Evidence Inventory
Catalog all observed evidence, telemetry, logs, and absences of expected behavior ($E_1, E_2, \dots, E_m$):
- **Diagnostic Evidence**: Data points that help distinguish one hypothesis from another.
- **Nondiagnostic Evidence**: Data points that are true under all hypotheses (e.g., "CPU is at 40%"). Note them, but do not assign them discriminative weight.
- **Independence Check**: Do not double-count correlated symptoms as independent evidence (e.g., 3 separate alerts triggered by the exact same dropped TCP connection).

### Step 3: Build the ACH Matrix
Cross-tabulate every piece of evidence against every hypothesis using standard ACH consistency ratings:
- `++` : Strongly consistent (expected if hypothesis is true, rare otherwise)
- `+`  : Consistent
- `0`  : Neutral, irrelevant, or nondiagnostic
- `-`  : Inconsistent (unlikely if hypothesis is true)
- `--` : Strongly inconsistent (contradicts the hypothesis; near-fatal)

### Step 4: Analyze Inconsistencies & Rank Contenders
> [!IMPORTANT]
> **The Core Rule of ACH**: Rank hypotheses by the **fewest significant inconsistencies (`-` and `--`)**, NOT by the highest number of pluses. Supporting evidence can often be explained by multiple theories, whereas hard contradictory evidence eliminates a theory.

### Step 5: Sensitivity Analysis & Diagnostic Gaps
1. **Sensitivity Check**: If the single most critical or fragile piece of evidence were wrong (e.g., a misconfigured metric or flawed timestamp), would the leading hypothesis change?
2. **Identify Information Gaps**: What single new probe, trace flag, or log inspection would definitively discriminate between the top remaining contenders?

### Step 6: Diagnostic Report & Falsification Conditions
Deliver a clear summary naming the leading hypothesis, the primary alternative, remaining uncertainties, and the exact trigger conditions that would falsify the leading explanation.

---

## Output Contract

Keep ACH reports concise and falsification-driven (see [Worked Example: Payment 504 Incident](examples/incident-ach-example.md)):

```markdown
# Analysis of Competing Hypotheses: [Focal Question]
1. **Candidate Hypotheses**: H1..Hn (mutually exclusive, including non-obvious defaults)
2. **Diagnostic Evidence Inventory**: E1..Em (tag credibility & diagnosticity; exclude correlated dupes)
3. **ACH Consistency Matrix**: Table mapping `E_i` x `H_j` with `++ | + | 0 | - | --`
4. **Inconsistency Ranking**: Rank by fewest `-` / `--` contradictions (never count `+` marks)
5. **Sensitivity & Next Probe**: Single most fragile assumption + highest-leverage discriminating test
6. **Confidence & Falsification Trigger**: `[Low|Moderate|High]` + exact observation disproving leader
```

---

## Gotchas & Failure Modes

- **The Confirmation Bias Trap**: Tallying `+` marks and picking the hypothesis with the most supporting evidence. Pluses do not prove a hypothesis; minuses eliminate them.
- **Correlated / Echo-Chamber Evidence**: Treating three distinct log messages produced by the same upstream error as three separate pieces of confirming data.
- **Nondiagnostic Evidence Bloat**: Filling the matrix with facts that are equally true under every hypothesis, obscuring the truly discriminating data.
- **Absence of Evidence vs. Evidence of Absence**: If a log does not show an error, verify whether the logging level was actually enabled before concluding the event never occurred.
- **Conflating Plausibility with Proof**: An intuitive, compelling narrative is not evidence. Require verifiable data points.
