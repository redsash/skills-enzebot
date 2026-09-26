---
name: competing-hypothesis
description: >-
  Evaluates complex, ambiguous, or contradictory evidence against multiple mutually exclusive explanations using Richards Heuer's Analysis of Competing Hypotheses (ACH) methodology. Use when diagnosing elusive production bugs, investigating security incidents, evaluating intelligence/risk scenarios, or choosing among rival technical root causes while eliminating confirmation bias.
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

Progress:
- [ ] Step 1: Formulate the focal question and exhaust candidate hypotheses
- [ ] Step 2: Inventory evidence and isolate diagnostic items
- [ ] Step 3: Construct the ACH consistency matrix
- [ ] Step 4: Analyze inconsistencies and rank hypotheses
- [ ] Step 5: Perform sensitivity analysis and identify critical information gaps
- [ ] Step 6: Report leading conclusions, confidence level, and falsification triggers

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

## Output Format Template

```markdown
# Analysis of Competing Hypotheses: [Focal Question]

### 1. Focal Issue & Candidate Hypotheses
- **H1**: [Clear description of Hypothesis 1]
- **H2**: [Clear description of Hypothesis 2]
- **H3**: [Clear description of Hypothesis 3]

---

### 2. Evidence Assessment
- **E1**: [Observed fact, metric, or log] *(Credibility: High | Diagnosticity: High)*
- **E2**: [Observed fact, metric, or log] *(Credibility: Moderate | Diagnosticity: High)*
- **E3**: [Nondiagnostic background state] *(Diagnosticity: Low / Neutral)*

---

### 3. ACH Consistency Matrix

| Evidence Item | H1: [Name] | H2: [Name] | H3: [Name] | Notes / Context |
| :--- | :---: | :---: | :---: | :--- |
| **E1**: [Description] | `++` | `-` | `0` | [Why it conflicts with H2] |
| **E2**: [Description] | `+` | `--` | `+` | [Contradiction for H2] |
| **E3**: [Description] | `-` | `+` | `++` | [Inconsistency for H1] |

*(Legend: `++` Strongly Consistent, `+` Consistent, `0` Neutral, `-` Inconsistent, `--` Strongly Inconsistent)*

---

### 4. Hypothesis Ranking & Inconsistency Analysis
1. **Leading Hypothesis (H#)**: [Fewest critical inconsistencies; explanation of fit]
2. **Primary Alternative (H#)**: [Close runner-up; what prevents it from being #1]
3. **Eliminated Hypotheses (H#)**: [Disproved by explicit negative evidence]

---

### 5. Sensitivity Analysis & Diagnostic Gaps
- **Key Vulnerability**: [Which piece of evidence carries the most weight, and what happens if it is flawed?]
- **High-Value Next Probe**: [Specific log query, unit test, or metric probe that cleanly separates H1 and H2]

---

### 6. Assessment & Falsification Triggers
- **Confidence**: [Low | Moderate | High]
- **What Would Change This Assessment**: [Specific observation that would disprove the leading hypothesis]
```

---

## Gotchas & Failure Modes

- **The Confirmation Bias Trap**: Tallying `+` marks and picking the hypothesis with the most supporting evidence. Pluses do not prove a hypothesis; minuses eliminate them.
- **Correlated / Echo-Chamber Evidence**: Treating three distinct log messages produced by the same upstream error as three separate pieces of confirming data.
- **Nondiagnostic Evidence Bloat**: Filling the matrix with facts that are equally true under every hypothesis, obscuring the truly discriminating data.
- **Absence of Evidence vs. Evidence of Absence**: If a log does not show an error, verify whether the logging level was actually enabled before concluding the event never occurred.
- **Conflating Plausibility with Proof**: An intuitive, compelling narrative is not evidence. Require verifiable data points.
