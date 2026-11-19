# Harness Hooks, Exit Prompts & Optional CLI Enhancers

Configure automatic recall, zero-token save nudges, unlogged session bookmarking on exit, and optional semantic code tools.

---

## 1. Antigravity (`agy`) Lifecycle Hooks

Antigravity discovers hooks in `~/.gemini/config/hooks.json` (global) or `.agents/hooks.json` (workspace). Update the path to `eng_log.py` to match your installed skill location.

- **`SessionStart` (`agy-start`)**: Injects up to 3 active `evergreen` or `version-bound` learnings matching the current repo/project, plus a notice if `pending/` holds unlogged session bookmarks.
- **`PostInvocation` (`agy-nudge`)**: Fires once a session reaches `--min-steps 15` (if not already logged). Uses `metadata.user_markdown` with an empty `systemMessage` (`""`) so the reminder renders inline for you at **zero LLM token cost**.

```json
{
  "engineering-log-recall": {
    "SessionStart": [
      {
        "type": "command",
        "command": "python3 ~/.gemini/skills/engineering-log/scripts/eng_log.py hook --mode agy-start",
        "timeout": 10
      }
    ]
  },
  "engineering-log-nudge": {
    "PostInvocation": [
      {
        "type": "command",
        "command": "python3 ~/.gemini/skills/engineering-log/scripts/eng_log.py hook --mode agy-nudge --min-steps 15",
        "timeout": 5
      }
    ]
  }
}
```

### Optional "Save Dialog" Shell Wrapper for `agy`
Antigravity does not currently expose a `SessionEnd` or `/quit` hook event. To get a lightweight save prompt whenever an interactive `agy` session exits, add a shell function to `~/.bashrc` or `~/.zshrc`:

```bash
agy-logged() {
  command agy "$@"
  local rc=$?
  printf "\nSave an /engineering-log entry for this session? [y/N] "
  read -r reply
  if [[ "$reply" =~ ^[Yy]$ ]]; then
    command agy -p "/engineering-log" --cwd "$PWD"
  fi
  return $rc
}
```

*(Or run `eng_log.py hook --mode session-end` directly when you want to bookmark an unlogged session into `~/engineering-log/pending/` for distillation later.)*

---

## 2. Gemini CLI & Claude Code (`SessionEnd` Bookmarking)

Harnesses that emit a `SessionEnd` event (such as **Gemini CLI** in `~/.gemini/settings.json`, triggered on `/quit`, `/clear`, or `Ctrl+D`, or **Claude Code** `SessionEnd`) can automatically bookmark unlogged sessions into `pending/` without blocking exit:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "name": "engineering-log-bookmark",
            "type": "command",
            "command": "python3 ~/.gemini/skills/engineering-log/scripts/eng_log.py hook --mode session-end",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

Whenever `eng_log.py context` or `agy-start` detects files in `pending/`, surface them so you can distill high-value sessions from their saved `transcript_path` or dismiss stale bookmarks.

---

## 3. Optional CLI Enhancers ("Batteries Included")

`eng_log.py` requires **only Python 3.8+ stdlib** and degrades cleanly in non-git or brainstorming directories (`git.is_git = false`, `code_semantics = null`). When installed on `PATH`, `context` and `stats` automatically activate extra capabilities:

| Tool | Purpose | Invocation Used | Install / Source |
| :--- | :--- | :--- | :--- |
| **`git`** | Repo, branch, commit SHA, diff stats, recent commits, inferred languages | `git status`, `git diff --numstat`, `git log` | System package manager |
| **`sem`** *(Ataraxy Labs)* | Tree-sitter entity-level semantic diff (functions, classes, methods changed) | `sem diff --format json` (or `--commit HEAD`) | [ataraxy-labs/sem](https://github.com/ataraxy-labs/sem) |
| **`inspect`** *(Ataraxy Labs)* | Structural risk scoring, change classification, transitive blast radius | `inspect diff --format json` | [Ataraxy-Labs/inspect](https://github.com/Ataraxy-Labs/inspect) |
| **`duckdb`** | Fast zero-ETL SQL analytics across `ledgers/**/*.jsonl` | `duckdb -dark-mode -c "..."` | [duckdb.org](https://duckdb.org) |

### Verifying Installed Enhancers
Run `context` against any workspace to inspect detected tools:
```bash
python3 engineering-log/scripts/eng_log.py context --cwd .
```
Check the `"tools"` map in the JSON output (`{"git": true, "sem": false, "inspect": false, "duckdb": true}`).
