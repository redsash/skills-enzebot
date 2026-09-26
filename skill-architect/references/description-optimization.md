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

1. **Use Imperative Phrasing**: 
   Tell the agent when to act.
   * *Good*: `"Extracts text and tables from PDF files... Use when working with PDF documents or when the user mentions forms, extraction, or PDF parsing."`
   * *Poor*: `"A skill that helps with PDFs."`
2. **Focus on User Intent, Not Implementation**:
   Agents match user prompts against what the user is trying to accomplish.
3. **Be Constructively Pushy**:
   Mention situations where the user does not use the exact jargon:
   * `"Use this skill when analyzing tabular data, even if the user does not explicitly say 'CSV' or 'analytics'."`
4. **Enforce the 1024-Character Limit**:
   Keep descriptions concise (typically 200–500 characters). Every character counts against startup context when dozens of skills are installed.

---

## 3. Trigger Eval Query Design

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
