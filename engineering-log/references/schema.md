# Engineering Log Schema (`schema_version: 1`) & Analytics Reference

This specification defines the canonical `write` / `append` JSON payloads, controlled vocabularies, sharded ledger federation model, and ready-to-run DuckDB / Python analytics recipes.

---

## 1. Store Topology & Multi-Writer Federation

Default store root: `$ENGINEERING_LOG_DIR`, falling back to `~/engineering-log/` (override per command with `--dir PATH`).

```text
~/engineering-log/
├── .gitignore
├── INDEX.md                                   # Compiled deterministically from ledgers/**/*.jsonl
├── indexes/
│   └── by-project/<project>.md                # Compiled per-project overflow shards
├── entries/
│   └── YYYY/MM/<id>_<slug>.md                 # Portable Markdown entry with YAML frontmatter
├── ledgers/
│   └── <user>-<machine>.jsonl                 # Append-only shard per writer/machine (0 merge conflicts)
└── pending/                                   # Unlogged session bookmarks from SessionEnd hooks
```

Exact layout:
- `INDEX.md` & `indexes/by-project/<project>.md` — Deterministically compiled master index (latest 50 entries, bounded `<= 140`-char rows, and `## Graph Hubs & Concept Map`) plus full per-project overflow shards.
- `entries/YYYY/MM/<entry_id>_<slug>.md` — Portable Markdown with YAML frontmatter and standard relative links.
- `ledgers/<stream_id>.jsonl` — Append-only JSONL shard (`--stream` > `$ENGINEERING_LOG_STREAM` > `<user>-<hostname>`). Each machine or teammate writes only to its own shard so `git pull --rebase` never conflicts.
- `pending/<conv_id>.json` — Lightweight bookmarks written by `SessionEnd` hooks for sessions that closed before logging.

### Scaling Coordinates (`scope` + `visibility`)
- **Solo multi-machine / multi-harness**: Slice by `actor.machine`, `actor.harness`, `actor.model`, and `project`.
- **Team / Division / Company**: Populate optional `context.scope` (e.g. `"acme/platform/payments"`) and set `visibility`:
  - `private` (default): Personal debugging friction, candid dead ends, unpolished drafts.
  - `team`: Safe to share with immediate teammates or sync into a team log repo.
  - `org`: Curated cross-team findings and recurring traps.
  - `public`: Scrubbed technical writeups safe outside the organization.

---

## 2. Controlled Vocabularies

| Field | Allowed Values | Notes |
| :--- | :--- | :--- |
| `session_shape` | `breakthrough`, `grind`, `dead-end`, `pivot`, `diagnostic`, `build`, `brainstorm`, `review` | Dominant arc of the session |
| `outcome` | `resolved`, `partial`, `blocked`, `abandoned`, `exploratory` | Honest final state |
| `confidence` | `verified`, `observed`, `hypothesis` | Epistemic strength of conclusions |
| `shelf_life` | `evergreen`, `version-bound`, `ephemeral` | Decay horizon (prevents stale 2026 hacks poisoning 2028) |
| `visibility` | `private`, `team`, `org`, `public` | Federation & sharing boundary |
| `verification` | `none`, `manual`, `automated-test`, `benchmark` | How the outcome was verified |
| `telemetry.agent_impact` | `force-multiplier`, `helpful`, `neutral`, `drag`, `derailed` | Net human-agent collaboration impact |
| `telemetry.agent_failure_modes[]` | `hallucinated-api`, `unverified-assumption`, `rabbit-hole`, `context-drift`, `ignored-constraint`, `over-engineered`, `tool-error`, `env-blind`, `scope-creep` | Observed agent failure patterns |
| `telemetry.unsticking_catalyst` | `minimal-repro`, `read-source`, `model-switch`, `human-insight`, `fresh-context`, `bisect`, `spec-lookup`, `tool-switch`, `rubber-duck`, `none` | What broke the logjam |
| `links[].rel` | `builds_on`, `supersedes`, `contradicts`, `same_root_cause`, `spawns` | Typed directed graph edge |

---

## 3. Canonical `write` Payload (`schema_version: 1`)

Pass via `--input payload.json` or stdin (`--input -`). When `--cwd PATH` is passed to `write` (recommended), `git`, `code_semantics`, and `actor` defaults are auto-harvested if omitted—only supply epistemic deltas, telemetry, context tags, and graph links:

```json
{
  "schema_version": 1,
  "title": "Fix OAuth token refresh race under concurrent tabs",
  "summary": "Serialized refresh calls behind a single in-flight promise; root cause was stale closure reading pre-rotation refresh_token.",
  "project": "web-auth-gateway",
  "session_shape": "diagnostic",
  "outcome": "resolved",
  "confidence": "verified",
  "shelf_life": "evergreen",
  "visibility": "private",
  "verification": "automated-test",
  "actor": {
    "harness": "agy",
    "model": "gemini-4-neon",
    "models_used": ["gemini-4-hydrogen", "gemini-4-neon"],
    "skills_used": ["competing-hypothesis"],
    "conversation_id": "72477760-2f9e-44fa-abf6-11c4bce0be93"
  },
  "context": {
    "scope": "personal",
    "cwd": "/home/user/src/web-auth-gateway",
    "domains": ["auth", "concurrency"],
    "technologies": ["typescript", "oauth2"],
    "concepts": ["single-flight", "token-rotation"]
  },
  "metrics": {
    "friction": 4,
    "value": 5
  },
  "telemetry": {
    "agent_impact": "helpful",
    "agent_failure_modes": ["unverified-assumption"],
    "unsticking_catalyst": "minimal-repro",
    "notes": "Agent initially blamed Redis TTL until we reproduced locally with two parallel requests."
  },
  "belief_revisions": [
    {
      "assumed": "Redis session cache was evicting valid refresh tokens early",
      "contradicted_by": "Integration test showed second concurrent tab sent old refresh_token after single-use rotation",
      "revised_model": "Refresh token rotation invalidates prior token immediately; concurrent requests must share one in-flight promise"
    }
  ],
  "dead_ends": [
    {
      "hypothesis": "Increase Redis key TTL on session store",
      "error_signature": "invalid_grant: refresh_token already rotated",
      "why_failed": "Token was actively revoked by IdP on first use, not expired in cache"
    }
  ],
  "findings": [
    {
      "claim": "Single-use OAuth refresh rotation requires process-wide single-flight deduplication per user session.",
      "confidence": "verified",
      "shelf_life": "evergreen",
      "evidence": "All 6 concurrent-refresh tests pass after adding in-flight promise map."
    }
  ],
  "rule_candidates": [
    {
      "scope": "repo",
      "rule": "Never call /oauth/token refresh directly outside refreshSingleFlight()",
      "rationale": "IdP rotates refresh tokens on first use and revokes the family on reuse."
    }
  ],
  "open_threads": [
    "Verify multi-pod behavior when two tabs hit different backend replicas"
  ],
  "links": [
    {
      "rel": "builds_on",
      "target_id": "20261110-1420-9b1c",
      "note": "Initial OAuth PKCE setup"
    }
  ],
  "git": null,
  "code_semantics": null
}
```

### Canonical `append` Payload
Used with `eng_log.py append --id <entry_id> --input -` to attach follow-up findings without rewriting history:

```json
{
  "note": "Confirmed across 2 replicas via Redis distributed lock.",
  "outcome": "resolved",
  "verification": "automated-test",
  "findings": [
    {
      "claim": "Cross-pod refresh lock requires 5s lease + cached rotated access_token.",
      "confidence": "verified",
      "shelf_life": "evergreen"
    }
  ],
  "closed_threads": [
    "Verify multi-pod behavior when two tabs hit different backend replicas"
  ],
  "promoted_rules": [
    "Never call /oauth/token refresh directly outside refreshSingleFlight()"
  ],
  "links": [
    {
      "rel": "same_root_cause",
      "target_id": "20261112-0915-c302",
      "note": "Same single-flight issue in mobile client"
    }
  ]
}
```

---

## 4. DuckDB & Python Analytics Recipes

Because `ledgers/**/*.jsonl` stores clean, schema-versioned newline-delimited JSON, DuckDB and Polars/pandas can query across machines and teammates with zero ETL.

> **Note for DuckDB v2+ CLI:** Pass `-dark-mode` (or `-light-mode`) in non-TTY / agent shells to bypass terminal background-color probing.

### Model & Harness Benchmark Across Real Work
```sql
SELECT
  actor.harness,
  actor.model,
  COUNT(*) AS sessions,
  ROUND(AVG(metrics.friction), 2) AS avg_friction,
  ROUND(AVG(metrics.value), 2) AS avg_value,
  SUM(CASE WHEN outcome = 'resolved' THEN 1 ELSE 0 END) AS resolved
FROM read_json_auto('~/engineering-log/ledgers/**/*.jsonl', union_by_name=true)
WHERE record_type = 'entry'
GROUP BY 1, 2
ORDER BY sessions DESC;
```

### Top Agent Failure Modes & Unsticking Catalysts
```sql
SELECT
  failure_mode,
  COUNT(*) AS occurrences,
  ROUND(AVG(metrics.friction), 2) AS avg_friction
FROM read_json_auto('~/engineering-log/ledgers/**/*.jsonl', union_by_name=true),
     UNNEST(telemetry.agent_failure_modes) AS t(failure_mode)
WHERE record_type = 'entry'
GROUP BY 1
ORDER BY occurrences DESC;
```

### Querying `sem` Semantic Entities & `inspect` Blast Radius
```sql
SELECT
  id,
  project,
  ent.file,
  ent.entity_type,
  ent.entity_name,
  ent.change_type,
  code_semantics.inspect.risk_tier AS risk_tier
FROM read_json_auto('~/engineering-log/ledgers/**/*.jsonl', union_by_name=true),
     UNNEST(code_semantics.sem.entities) AS t(ent)
WHERE record_type = 'entry'
  AND code_semantics.sem IS NOT NULL
ORDER BY created_at DESC
LIMIT 25;
```

### Python / Polars Quick Load
```python
import glob, json
records = [
    json.loads(line)
    for path in glob.glob(os.path.expanduser("~/engineering-log/ledgers/**/*.jsonl"), recursive=True)
    for line in open(path, encoding="utf-8")
    if line.strip()
]
entries = [r for r in records if r.get("record_type") == "entry"]
```
