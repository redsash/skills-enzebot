# Evaluating Skill Output Quality

Based on [Evaluating Skill Output Quality](https://agentskills.io/skill-creation/evaluating-skills.md).

---

## 1. Why Systematic Evaluation Matters

A skill that works on a single cherry-picked prompt may fail under variation, hallucinate on edge cases, or consume excessive tokens without improving baseline output. Structured evals establish reproducible verification and quantifiable improvement.

---

## 2. Test Suite Structure (`evals/evals.json`)

Define 2–5 representative test cases in `evals/evals.json`:

```json
{
  "skill_name": "markdown-to-pdf",
  "evals": [
    {
      "id": 1,
      "prompt": "Convert docs/architecture.md into a formatted PDF with syntax highlighting and page numbers.",
      "expected_output": "A styled PDF file matching the document structure with numbered pages.",
      "files": ["evals/files/architecture.md"],
      "assertions": [
        "The output file architecture.pdf exists",
        "The PDF contains page numbers in footer",
        "Code blocks are styled with syntax highlighting"
      ]
    }
  ]
}
```

### Test Prompt Design Rules
- **Realistic Context**: Include realistic file paths, parameters, and conversational framing.
- **Edge Cases**: Include at least one prompt testing malformed inputs, boundary lengths, or missing optional fields.
- **Varied Phrasing**: Mix terse direct commands with descriptive multi-sentence requests.

---

## 3. Eval Workspace & Baseline Isolation

Evaluate skills in an isolated workspace per iteration:

```text
evals-workspace/
└── iteration-1/
    ├── eval-1/
    │   ├── with_skill/
    │   │   ├── outputs/        # Generated artifacts
    │   │   ├── timing.json     # Token usage and runtime
    │   │   └── grading.json    # Graded assertions with evidence
    │   └── without_skill/      # Or old_skill/ for version comparison
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json          # Aggregate delta metrics
```

### Comparative Baselines
Always run test cases in two configurations:
1. **`with_skill`**: Agent provided the candidate skill.
2. **`without_skill` (or `old_skill`)**: Agent running with generic instructions or prior skill version.

---

## 4. Writing Objective Assertions

Assertions must be verifiable facts, not subjective opinions.

| Good Assertions (Objective) | Bad Assertions (Subjective/Brittle) |
| :--- | :--- |
| `"Output contains valid JSON matching schema/v1.json"` | `"The JSON looks good"` |
| `"File 'report.pdf' exists and size > 10KB"` | `"Generates a nice report"` |
| `"Contains at least 3 distinct mitigation points"` | `"Contains the exact text 'Solution A: ...'"` |
| `"All SQL statements use parameterized queries"` | `"Clean code"` |

---

## 5. Grading and Aggregate Benchmarking

### Assertion Grading (`grading.json`)
Every assertion is graded as `true` or `false` backed by concrete citation:
```json
{
  "assertion_results": [
    {
      "text": "File 'report.pdf' exists and size > 10KB",
      "passed": true,
      "evidence": "Found report.pdf (42,100 bytes) in outputs/"
    },
    {
      "text": "The PDF contains page numbers in footer",
      "passed": false,
      "evidence": "Page footer is blank; no page numbers detected."
    }
  ],
  "summary": { "passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5 }
}
```

### Aggregate Metrics (`benchmark.json`)
Measure what the skill costs vs. what it delivers:
```json
{
  "run_summary": {
    "with_skill": { "pass_rate": 0.90, "tokens": 4200, "time_seconds": 38 },
    "without_skill": { "pass_rate": 0.40, "tokens": 2800, "time_seconds": 26 },
    "delta": {
      "pass_rate_gain": "+0.50",
      "token_cost": "+1400",
      "time_cost": "+12s"
    }
  }
}
```

---

## 6. The Iterative Refinement Loop

1. **Review Failed Assertions**: Pinpoint missing instructions or ambiguous phrasing.
2. **Review Transcripts**: If the agent took circular or unproductive steps, streamline instructions or provide a bundled script.
3. **Prune Ineffective Rules**: If an assertion passes in both `with_skill` and `without_skill`, the agent already knows how to do it—delete unnecessary instructions to save context.
4. **Update & Re-run**: Increment to `iteration-<N+1>/` and evaluate the delta.
