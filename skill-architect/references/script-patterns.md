# Engineering Scripts for Agent Skills

Based on [Using Scripts in Skills](https://agentskills.io/skill-creation/using-scripts.md).

---

## 1. When to Bundle a Script

Write a script into `scripts/` when:
1. An operation requires more than 2–3 piping commands or complex regex flags.
2. The agent repeatedly reinvents the same boilerplate across different runs.
3. Strict deterministic validation (schema check, lint, dry-run) is required.
4. Parsing or formatting output must be identical every time.

---

## 2. Hard Requirements for Agentic Scripts

### A. Non-Interactive Execution
Agents run in non-interactive subshells without a TTY.
- **NEVER** use interactive prompts (`input()`, `read -p`, confirmation dialogs). They hang the agent indefinitely.
- Accept all parameters via CLI flags, positional arguments, or environment variables.
- If required parameters are missing, exit immediately with a non-zero exit code and display clear usage instructions.

### B. Standardized `--help` Flags
The `--help` output is how the agent reads the tool's interface. Keep it concise, showing:
- One-line tool summary.
- Available flags, defaults, and allowed values.
- Concrete usage examples.

```text
Usage: python3 scripts/extract_metrics.py [OPTIONS] <input-file>

Extracts and aggregates telemetry metrics from CSV or JSON logs.

Options:
  --format {json,csv,text}  Output format (default: json)
  --dry-run                 Preview operations without modifying files
  --output FILE             Path to output file (default: stdout)

Examples:
  python3 scripts/extract_metrics.py data/telemetry.csv
  python3 scripts/extract_metrics.py --format json --output summary.json log.json
```

---

## 3. Clean Stream Segregation

Agents parse `stdout` programmatically, while using `stderr` for troubleshooting:
- **`stdout`**: Clean, structured machine-readable payload (JSON, CSV, TSV) or designated report output.
- **`stderr`**: Informational logs, progress messages, warnings, and error traces.

```python
import sys, json

# Diagnostics go to stderr
sys.stderr.write("Processing 450 items...\n")

# Structured payload goes to stdout
json.dump({"status": "success", "count": 450}, sys.stdout, indent=2)
```

---

## 4. Self-Contained Dependency Declarations

To ensure scripts run across machines without manual global installs:

### Python: PEP 723 Script Metadata
Include inline dependencies runnable via `uv run` or standard `python3`:
```python
# /// script
# dependencies = [
#   "pydantic>=2.0",
#   "rich",
# ]
# ///
import sys
from pydantic import BaseModel
```

### Node / Deno / Bun
- In Node: pin dependencies or use standard built-ins (`fs`, `path`, `readline`).
- In Deno: use explicit `npm:` or `jsr:` specifiers (e.g. `import * as cheerio from "npm:cheerio@1.0.0"`).

---

## 5. Resilience Heuristics

1. **Idempotence**: Scripts should be safe to run multiple times (`create_if_not_exists` rather than crashing on existing files).
2. **Predictable Output Size**: If a script can return thousands of records, default to a summary or implement `--limit` and `--offset`. Giant stdout dumps trigger agent output truncation.
3. **Distinct Exit Codes**:
   - `0`: Success
   - `1`: General validation / user input error
   - `2`: Resource not found
   - `3`: Upstream API / network failure
