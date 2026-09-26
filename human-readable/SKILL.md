---
name: human-readable
description: >-
  Removes AI cliches, robotic mannerisms, staccato phrasing, and throat-clearing from written drafts to make them sound natural and human-authored. Use when a draft "sounds like AI", "reads like an LLM", or feels stilted, corporate, or formulaic across PR descriptions, proposals, documentation, announcements, commit messages, or blog posts.
---

# Make Fit for Human Consumption

Working prose optimizes for completeness; human-facing prose optimizes for a reader who wasn't there. This skill is the editing pass that takes a draft and works it over until it reads like a human engineer who cares wrote it.

---

## When to Use This Skill
- The user says a draft "sounds like AI", "reads like an LLM", or asks to "make this sound human".
- Any human-facing communication is being prepared for review: PR descriptions, proposals, project announcements, release notes, commit messages, or documentation.
- **Do not use for**: Code restructuring or technical logic changes; focus strictly on prose quality.

---

## Workflow / Procedure

Progress:
- [ ] Step 1: Strip throat-clearing preambles and corporate hype
- [ ] Step 2: Execute the de-LLM tic sweep
- [ ] Step 3: Enforce vocabulary discipline and causality
- [ ] Step 4: Conduct the read-aloud self-check

### Step 1: Strip Preambles & Hype
Delete empty introductions, sycophantic wrap-ups, and generic corporate puffery. Jump straight to the substance:
- Cut: *"In today's fast-paced environment...", "At its core...", "It is important to remember that..."*
- Cut: *"In conclusion, this unlocks unprecedented innovation..."*

### Step 2: The De-LLM Tic Sweep
Audit the text against this catalog of characteristic model habits:

| Tic Pattern | Before (Robotic / AI) | After (Natural Human) |
| :--- | :--- | :--- |
| **Elevated Cliches** (`delve`, `testament`, `foster`, `pivotal`, `beacon`, `game-changer`, `tapestry`) | "This PR delves into retry logic to foster fleet stability." | "This PR updates the retry logic to prevent fleet crashes." |
| **Intensifiers** (`real`, `whole`, `exactly`, `fully`, `genuine`, `crucial`) | "Processed with the real worker for genuine efficiency." | "Processed by the worker." |
| **Restatement Tail** (punchy fragment repeating the point) | "...and the retry logic fixes that too. The queue is the missing piece." | "...and the retry logic fixes that too." |
| **Antithesis Half** (`X — never Y`) | "Retries only when a handler is registered — never automatically after a deploy." | "Retries only when a handler is registered." |
| **Staccato Staging** (fake drama via fragmented sentences) | "No new API, no new flag. The job ID is the whole signal." | "The job ID gives the worker everything it needs, so there's no new API." |
| **Framing Moves** (`The insight:`, `The stakes are...`) | "The insight: the scheduler already knows the job status." | "The scheduler already knows the job status." |
| **Fake Humility / Balanced Hedge** (`While not a silver bullet...`) | "While not a silver bullet, it represents a pivotal step." | "This addresses the immediate bottleneck." |
| **Cute Headings** | "Receipts — what the spike surfaced beyond 'it works'" | "Spike findings" |
| **Punchy Anthropomorphism** | "The worker learns one fact." | "The worker gains one field." |
| **Em Dash Overuse (List)** | "The worker handles three cases — retries, timeouts, failures." | "The worker handles three cases: retries, timeouts, failures." |
| **Em Dash Overuse (Forced Clause)** | "Skipped retries stall the queue — add a handler before deploy." | "Skipped retries stall the queue, so add a handler before deploy." |

> [!TIP]
> Prefer explicit connectives (*"so"*, *"since"*, *"while"*, *"which"*) when clauses are causally linked. State the relationship directly instead of using em dashes that force the reader to guess causality.

### Step 3: Vocabulary Discipline
1. **One meaning per loaded term**: If a verb names a specific domain action (e.g. *retry* = the backoff job), do not use it colloquially. Producers *enqueue*, consumers *dequeue*, clients *poll*.
2. **Don't verb domain nouns**: *"A worker queues jobs"* collides with queue-the-noun. Use *"adds jobs to the queue"* or *"enqueues"*.
3. **Eliminate session shorthand**: Phrases coined during live debugging (*"wires the field"*, *"the red"*, *"probe"*) confuse outside readers. Describe the action (*"passes the job ID to the worker"*).
4. **Name the acting system**: *"The scheduler picks job priority"* rather than passive *"the priority is chosen"*.
5. **Scope countables precisely**: Instead of *"the first payload that arrives"*, write *"the job's first-arriving payload"*.

### Step 4: Read-Aloud Self-Check
Read the revised text aloud. If you stumble, if it sounds like a breathless LinkedIn post, or if it reads like a generic template, revise it:
- Compress by cutting redundant content, not by truncating sentences into telegraphic fragments.
- Ensure technical precision is preserved—never sacrifice architectural correctness for casualness.

---

## Gotchas & Failure Modes

- **The Over-Correction Trap**: Do not replace robotic AI prose with forced slang or sloppy colloquialisms. The goal is clear, quiet, confident professional prose, not conversational fluff.
- **Factual Drift**: When rewriting sentences, never alter technical semantics or invent capabilities the original draft did not claim.
- **The Synonym Swapper Trap**: Merely swapping words (e.g., changing *"delve"* to *"examine"*) while leaving the stilted sentence structure intact fails to solve the underlying problem. Restructure the sentence.

---

## Full Transformation Example

### Before (AI Draft):
> In this PR, we delve into our event dispatching architecture — a crucial milestone in our distributed journey. The insight: consumers were blindly polling empty queues. We eliminated redundant queries, streamlined batch processing, and fostered better partition isolation. No new services, no extra flags. The consumer offset is the whole signal. While not a silver bullet, it represents a testament to the team's relentless focus on performance.

### After (Human-Readable):
> This PR updates the event dispatcher so consumers stop polling empty queues. By using consumer offsets to track active partitions, we eliminated redundant polling queries without introducing new configuration flags or services.
