# Optimizing Skill Descriptions & Trigger Accuracy

Based on [Optimizing Skill Descriptions](https://agentskills.io/skill-creation/optimizing-descriptions.md).

---

## 1. The Trigger Mechanism

In Antigravity and Open Skills ecosystems, an agent's startup context only includes each skill's `name` and `description`. 
The `description` carries the complete burden of triggering:
- If it is too narrow or timid, the agent handles the task with generic knowledge and never activates the skill.
- If it is too broad or keyword-stuffed, the skill activates falsely on unrelated tasks, wasting context and tokens.

---

## 2. Rules for High-Accuracy Descriptions

Use the canonical 3-part pattern: **`[Third-person capability] + [Explicit trigger clause] + [Explicit non-trigger boundary]`**.

1. **Use Crisp Third-Person Phrasing**:
   Open with a third-person present-tense action verb describing what the skill accomplishes (avoid `"I help..."`, `"This skill..."`, or `"A skill that..."`).
   * *Good*: `"Extracts structured tables and form fields from PDF documents. Use when parsing PDFs, extracting invoices, or inspecting form schemas. Do not use for generating PDFs from Markdown or OCR-only image scans."`
   * *Poor*: `"A skill that helps with PDFs."`
2. **Focus on User Intent & Domain Keywords, Not Implementation**:
   Agents match user prompts against what the user is trying to accomplish, plus concrete domain artifacts (file extensions, protocols, slash commands).
3. **Declare Explicit Non-Triggers (Prevent Routing Collisions)**:
   Do **not** write "pushy" or catch-all descriptions (`"use anytime the user mentions data"`). On frontier models with dozens of installed skills, broad wording causes false activations. Always add a `Do not use for...` clause naming adjacent skills or native workflows (e.g., `"Do not use for repo-local prompt journals (use research-journaler) or CHANGELOGs."`).
4. **Match Invocation Posture (`auto` vs. `manual` vs. `hybrid`)**:
   - **`auto`**: Include crisp ambient triggers + non-triggers.
   - **`manual`**: Explicitly narrow activation (`"Use only on /<skill-name> or when the user explicitly requests..."`) so heavy frameworks or destructive workflows do not hijack routine turns.
   - **`hybrid`**: Name `/<skill-name>` plus narrow, unmistakable triggers.
5. **Respect Context Economy (Target 200–550 chars; Hard Max 1024)**:
   Every character sits in startup context across every turn. Keep descriptions dense and high-signal.

---

## 3. Cross-Skill Collision Checking & Trigger Eval Design

Before writing trigger evals, run the repo-wide collision check to identify sibling skills sharing the same `phase` + `domain` or high lexical overlap:
```bash
python3 skill-architect/scripts/validate_skill.py --all .
```
Every colliding sibling skill must become a **negative near-miss** in `evals/trigger_queries.json` and be explicitly disambiguated in both skills' descriptions.

To validate triggering, construct a test suite of ~20 queries in `evals/trigger_queries.json`:

```json
[
  {
    "query": "I have an export of last month's telemetry in ~/logs/dump.csv, can you summarize average error rate by region?",
    "should_trigger": true
  },
  {
    "query": "Can you write a script to upload rows from this file into Postgres?",
    "should_trigger": false
  }
]
```

### Should-Trigger Queries (8–10 queries)
Vary along 4 dimensions:
- **Formality / Slang**: Formal technical prompts vs. casual conversational prompts with abbreviations or typos.
- **Explicitness**: Some mention the domain directly; others state the task without naming the domain.
- **Detail**: Short 1-line queries vs. multi-paragraph context-heavy requests with paths and parameters.
- **Nesting**: The skill task is part of a larger multi-step goal.

### Should-Not-Trigger Near-Misses (8–10 queries)
Do not use trivial negatives (e.g. `"What is the capital of France?"`). Use **near-misses** that share keywords or concepts but require different tools:
- For a `csv-analyzer`: Negative test = `"Update the formulas in my Excel spreadsheet budget"`.
- For a `git-commit-helper`: Negative test = `"Show git diff between main and feature branch"`.

---

## 4. Train / Validation Splits

To prevent overfitting to specific phrasing:
1. Split queries **60% Train** and **40% Validation**.
2. Both sets must have an equal ratio of positive and negative queries.
3. Revise description based **only on Train failures**.
4. Test against Validation to verify generalization.

---

## 5. Optimization Loop

1. **Baseline**: Run 3 trials per query across train & validation sets. Calculate `trigger_rate = invocations / trials`.
2. **Diagnose**:
   - False negatives (should-trigger failed): Description lacks user-intent keywords or is too restrictive.
   - False positives (should-not-trigger invoked): Description lacks boundary constraints. Clarify what the skill does *not* do.
3. **Refine**: Generalize concepts rather than copy-pasting exact failed query keywords.
4. **Validate**: Check validation set pass rate. Stop when validation rate peaks.
