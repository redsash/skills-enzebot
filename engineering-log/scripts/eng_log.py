#!/usr/bin/env python3
"""
Engineering Log ("Knowledge & Thoroughness") CLI engine.

Pure Python 3.8+ stdlib-only core for capturing epistemic deltas, dead-end
signatures, typed graph links, and human-agent collaboration telemetry into
sharded append-only JSONL ledgers and portable Markdown entries.

Optional progressive enhancement when installed on PATH:
  - git: repo, branch, commit, diff stats, and recent commit harvesting
  - sem (Ataraxy Labs): entity-level semantic code diffs (`sem diff --format json`)
  - inspect (Ataraxy Labs): blast-radius & risk triage (`inspect diff --format json`)
  - duckdb: fast SQL analytics over `ledgers/**/*.jsonl`

Usage:
    python3 eng_log.py init [--dir DIR]
    python3 eng_log.py context [--dir DIR] [--cwd PATH] [--query TEXT] [--tech CSV] [--concepts CSV] [--top N]
    python3 eng_log.py write [--dir DIR] [--input FILE|-] [--stream ID] [--dry-run]
    python3 eng_log.py append --id ENTRY_ID [--dir DIR] [--input FILE|-] [--stream ID] [--dry-run]
    python3 eng_log.py rebuild-index [--dir DIR]
    python3 eng_log.py query [--dir DIR] [--project X] [--tech X] [--concept X] [--text X] [--limit N] [--format json|markdown]
    python3 eng_log.py stats [--dir DIR] [--project X] [--since YYYY-MM-DD] [--format json|markdown]
    python3 eng_log.py validate [--dir DIR]
    python3 eng_log.py hook --mode <agy-start|agy-nudge|session-end|pending-list> [--dir DIR] [--min-steps N]
"""

import argparse
import getpass
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SCHEMA_VERSION = 1

SESSION_SHAPES = (
    "breakthrough",
    "grind",
    "dead-end",
    "pivot",
    "diagnostic",
    "build",
    "brainstorm",
    "review",
)
OUTCOMES = ("resolved", "partial", "blocked", "abandoned", "exploratory")
CONFIDENCE_LEVELS = ("verified", "observed", "hypothesis")
SHELF_LIVES = ("evergreen", "version-bound", "ephemeral")
VISIBILITIES = ("private", "team", "org", "public")
VERIFICATIONS = ("none", "manual", "automated-test", "benchmark")
AGENT_IMPACTS = ("force-multiplier", "helpful", "neutral", "drag", "derailed")
AGENT_FAILURE_MODES = (
    "hallucinated-api",
    "unverified-assumption",
    "rabbit-hole",
    "context-drift",
    "ignored-constraint",
    "over-engineered",
    "tool-error",
    "env-blind",
    "scope-creep",
)
UNSTICKING_CATALYSTS = (
    "minimal-repro",
    "read-source",
    "model-switch",
    "human-insight",
    "fresh-context",
    "bisect",
    "spec-lookup",
    "tool-switch",
    "rubber-duck",
    "none",
)
LINK_RELS = (
    "builds_on",
    "supersedes",
    "contradicts",
    "same_root_cause",
    "spawns",
)

EXT_LANGUAGE_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".kt": "kotlin",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".sql": "sql",
    ".svelte": "svelte",
    ".vue": "vue",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".tf": "terraform",
    ".zig": "zig",
}

YAML_RESERVED = {
    "true",
    "false",
    "null",
    "yes",
    "no",
    "on",
    "off",
    "y",
    "n",
    "~",
}
SAFE_YAML_TOKEN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_/-]*$")

PLACEHOLDER_SECRET_PREFIXES = (
    "[redacted:",
    "changeme",
    "placeholder",
    "example",
    "your_",
    "your-",
    "<your",
    "xxxx",
    "****",
    "dummy",
    "redacted",
)

PEM_KEY_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"
)
GITHUB_TOKEN_RE = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{12,}\b|\bgithub_pat_[A-Za-z0-9_]{12,}\b"
)
API_PREFIX_TOKEN_RE = re.compile(
    r"\bsk-ant-[A-Za-z0-9_-]{12,}\b|\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{16,}\b"
)
GOOGLE_API_KEY_RE = re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")
AWS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
SLACK_TOKEN_RE = re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")
PACKAGE_TOKEN_RE = re.compile(r"\bglpat-[0-9A-Za-z_-]{12,}\b|\bnpm_[0-9A-Za-z]{12,}\b")
AUTH_HEADER_RE = re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)([^\s\"']+)")
BEARER_TOKEN_RE = re.compile(
    r"(?i)\b(Bearer\s+)([A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+|[A-Za-z0-9\-_.=]{16,})"
)
CREDENTIAL_URL_RE = re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://[^/\s:@]+:)([^/\s@]+)(@)")
INLINE_EQ_SECRET_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:API_KEY|SECRET_KEY|ACCESS_TOKEN|AUTH_TOKEN|PRIVATE_KEY|PASSWORD|PASSWD|CLIENT_SECRET|DB_PASS)\s*=\s*)([\"']?)([^\s\"'\n]{6,})(\2)"
)
INLINE_COLON_UPPER_SECRET_RE = re.compile(
    r"\b([A-Z0-9_]*(?:API_KEY|SECRET_KEY|ACCESS_TOKEN|AUTH_TOKEN|PRIVATE_KEY|PASSWORD|PASSWD|CLIENT_SECRET|DB_PASS)\s*:\s*)([\"']?)([^\s\"'\n,}{]{6,})(\2)"
)
INLINE_JSON_SECRET_RE = re.compile(
    r"(?i)(\"[A-Z0-9_]*(?:API_KEY|SECRET_KEY|ACCESS_TOKEN|AUTH_TOKEN|PRIVATE_KEY|PASSWORD|PASSWD|CLIENT_SECRET|DB_PASS)\"\s*:\s*\")([^\"\n]{6,})(\")"
)


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def resolve_store_dir(dir_arg: Optional[str]) -> Path:
    """Resolve engineering log store root via flag > env > default."""
    raw = dir_arg or os.environ.get("ENGINEERING_LOG_DIR") or "~/engineering-log"
    return Path(raw).expanduser().resolve()


def sanitize_slug(text: str, max_len: int = 60) -> str:
    """Convert arbitrary text to lowercase kebab-case slug."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip("-")
    return cleaned or "session"


def resolve_stream_id(stream_arg: Optional[str]) -> str:
    """Resolve append-only ledger shard identifier for this writer."""
    if stream_arg:
        return sanitize_slug(stream_arg, max_len=48)
    env_stream = os.environ.get("ENGINEERING_LOG_STREAM")
    if env_stream:
        return sanitize_slug(env_stream, max_len=48)
    user = getpass.getuser() or "user"
    host = socket.gethostname().split(".")[0] or "local"
    return sanitize_slug(f"{user}-{host}", max_len=48)


def write_text_atomic(path: Path, content: str) -> None:
    """Atomically write text file using temporary sibling + replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(3)}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def append_jsonl_line(path: Path, record: Dict[str, Any]) -> None:
    """Append a single compact JSON line to an append-only ledger shard."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _is_placeholder_secret(val: str) -> bool:
    low = val.strip().lower()
    if not low:
        return True
    return any(low.startswith(prefix) for prefix in PLACEHOLDER_SECRET_PREFIXES)


def scrub_text(text: str) -> Tuple[str, int]:
    """Redact common credential patterns deterministically, returning (cleaned, count)."""
    if not text:
        return text, 0
    count = 0

    def _sub_fixed(pattern: re.Pattern, tag: str, s: str) -> str:
        nonlocal count

        def _repl(match: re.Match) -> str:
            nonlocal count
            val = match.group(0)
            if val.lower().startswith("[redacted:"):
                return val
            count += 1
            return f"[REDACTED:{tag}]"

        return pattern.sub(_repl, s)

    out = text
    out = _sub_fixed(PEM_KEY_RE, "private_key", out)
    out = _sub_fixed(GITHUB_TOKEN_RE, "github_token", out)
    out = _sub_fixed(API_PREFIX_TOKEN_RE, "api_key", out)
    out = _sub_fixed(GOOGLE_API_KEY_RE, "google_api_key", out)
    out = _sub_fixed(AWS_KEY_RE, "aws_access_key", out)
    out = _sub_fixed(SLACK_TOKEN_RE, "slack_token", out)
    out = _sub_fixed(PACKAGE_TOKEN_RE, "package_token", out)

    def _repl_bearer(match: re.Match) -> str:
        nonlocal count
        token = match.group(2)
        if _is_placeholder_secret(token):
            return match.group(0)
        count += 1
        return f"{match.group(1)}[REDACTED:bearer_token]"

    out = AUTH_HEADER_RE.sub(_repl_bearer, out)
    out = BEARER_TOKEN_RE.sub(_repl_bearer, out)

    def _repl_url(match: re.Match) -> str:
        nonlocal count
        pwd = match.group(2)
        if _is_placeholder_secret(pwd):
            return match.group(0)
        count += 1
        return f"{match.group(1)}[REDACTED:url_password]{match.group(3)}"

    out = CREDENTIAL_URL_RE.sub(_repl_url, out)

    def _repl_inline(match: re.Match) -> str:
        nonlocal count
        val = match.group(3)
        if _is_placeholder_secret(val):
            return match.group(0)
        count += 1
        return f"{match.group(1)}{match.group(2)}[REDACTED:inline_secret]{match.group(2)}"

    def _repl_json_secret(match: re.Match) -> str:
        nonlocal count
        val = match.group(2)
        if _is_placeholder_secret(val):
            return match.group(0)
        count += 1
        return f"{match.group(1)}[REDACTED:inline_secret]{match.group(3)}"

    out = INLINE_EQ_SECRET_RE.sub(_repl_inline, out)
    out = INLINE_COLON_UPPER_SECRET_RE.sub(_repl_inline, out)
    out = INLINE_JSON_SECRET_RE.sub(_repl_json_secret, out)
    return out, count


def scrub_value(value: Any) -> Tuple[Any, int]:
    """Recursively scrub strings inside nested JSON-like structures."""
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, list):
        total = 0
        cleaned = []
        for item in value:
            c_item, n = scrub_value(item)
            cleaned.append(c_item)
            total += n
        return cleaned, total
    if isinstance(value, dict):
        total = 0
        cleaned_dict: Dict[str, Any] = {}
        for k, v in value.items():
            c_val, n = scrub_value(v)
            cleaned_dict[k] = c_val
            total += n
        return cleaned_dict, total
    return value, 0


def yaml_scalar(val: Any) -> str:
    """Format a Python primitive cleanly and safely as a YAML scalar."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    text = str(val)
    if (
        SAFE_YAML_TOKEN_RE.match(text)
        and text.lower() not in YAML_RESERVED
        and "\n" not in text
    ):
        return text
    return json.dumps(text, ensure_ascii=False)


def yaml_dump(obj: Any, indent: int = 0) -> List[str]:
    """Serialize dicts/lists/scalars to valid, PyYAML-compatible YAML lines."""
    pad = " " * indent
    lines: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_str = str(k)
            if isinstance(v, dict):
                if not v:
                    lines.append(f"{pad}{key_str}: {{}}")
                else:
                    lines.append(f"{pad}{key_str}:")
                    lines.extend(yaml_dump(v, indent + 2))
            elif isinstance(v, list):
                if not v:
                    lines.append(f"{pad}{key_str}: []")
                elif all(not isinstance(x, (dict, list)) for x in v):
                    inline = ", ".join(yaml_scalar(x) for x in v)
                    if len(pad) + len(key_str) + len(inline) + 4 <= 100:
                        lines.append(f"{pad}{key_str}: [{inline}]")
                    else:
                        lines.append(f"{pad}{key_str}:")
                        for x in v:
                            lines.append(f"{pad}  - {yaml_scalar(x)}")
                else:
                    lines.append(f"{pad}{key_str}:")
                    for item in v:
                        if isinstance(item, dict) and item:
                            first = True
                            for ik, iv in item.items():
                                prefix = f"{pad}  - " if first else f"{pad}    "
                                first = False
                                if isinstance(iv, (dict, list)) and iv:
                                    lines.append(f"{prefix}{ik}:")
                                    lines.extend(yaml_dump(iv, indent + 6))
                                else:
                                    lines.append(f"{prefix}{ik}: {yaml_scalar(iv)}")
                        else:
                            lines.append(f"{pad}  - {yaml_scalar(item)}")
            else:
                lines.append(f"{pad}{key_str}: {yaml_scalar(v)}")
    return lines


def detect_tools() -> Dict[str, bool]:
    """Detect optional enhancement CLIs on PATH."""
    return {
        tool: bool(shutil.which(tool))
        for tool in ("git", "sem", "inspect", "duckdb")
    }


def _run_cmd(args: List[str], cwd: Path, timeout: int = 5) -> Optional[str]:
    """Run external command safely, returning stripped stdout or None on failure."""
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout
    except Exception:
        return None


def _infer_languages(paths: List[str]) -> List[str]:
    langs: List[str] = []
    seen = set()
    for p in paths:
        ext = Path(p).suffix.lower()
        lang = EXT_LANGUAGE_MAP.get(ext)
        if lang and lang not in seen:
            seen.add(lang)
            langs.append(lang)
    return langs


def harvest_git_info(cwd: Path) -> Dict[str, Any]:
    """Harvest objective repository state from git without inventing metrics."""
    empty = {
        "is_git": False,
        "repo": None,
        "repo_root": None,
        "branch": None,
        "head_commit": None,
        "is_dirty": False,
        "files_changed": 0,
        "insertions": 0,
        "deletions": 0,
        "changed_files": [],
        "languages_touched": [],
        "recent_commits": [],
    }
    if not shutil.which("git") or not cwd.exists():
        return empty

    inside = _run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd)
    if not inside or inside.strip() != "true":
        return empty

    root_raw = _run_cmd(["git", "rev-parse", "--show-toplevel"], cwd)
    repo_root = root_raw.strip() if root_raw else str(cwd)
    repo_name = Path(repo_root).name

    branch_raw = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    branch = branch_raw.strip() if branch_raw else None

    head_raw = _run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd)
    head_commit = head_raw.strip() if head_raw else None

    status_raw = _run_cmd(["git", "status", "--porcelain"], cwd) or ""
    status_lines = [ln for ln in status_raw.splitlines() if ln.strip()]
    changed_files: List[str] = []
    seen_files = set()
    for ln in status_lines:
        path_part = ln[3:].strip()
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1].strip()
        path_part = path_part.strip('"')
        if path_part and path_part not in seen_files:
            seen_files.add(path_part)
            changed_files.append(path_part)

    insertions = 0
    deletions = 0
    numstat_args = (
        ["git", "diff", "--numstat", "HEAD"]
        if head_commit
        else ["git", "diff", "--cached", "--numstat"]
    )
    numstat_raw = _run_cmd(numstat_args, cwd) or ""
    for ln in numstat_raw.splitlines():
        parts = ln.split("\t")
        if len(parts) >= 3:
            ins_s, del_s, fpath = parts[0], parts[1], parts[2]
            if ins_s.isdigit():
                insertions += int(ins_s)
            if del_s.isdigit():
                deletions += int(del_s)
            if fpath not in seen_files:
                seen_files.add(fpath)
                changed_files.append(fpath)

    commits_raw = _run_cmd(
        ["git", "log", "-n", "5", "--since=12 hours ago", "--format=%h\t%cI\t%s"],
        cwd,
    )
    recent_commits = []
    if commits_raw:
        for ln in commits_raw.splitlines():
            parts = ln.split("\t", 2)
            if len(parts) == 3:
                recent_commits.append(
                    {"sha": parts[0], "committed_at": parts[1], "subject": parts[2]}
                )

    lang_source_files = list(changed_files)
    if not lang_source_files and head_commit:
        head_files = _run_cmd(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd
        )
        if head_files:
            lang_source_files = [x.strip() for x in head_files.splitlines() if x.strip()]

    return {
        "is_git": True,
        "repo": repo_name,
        "repo_root": repo_root,
        "branch": branch,
        "head_commit": head_commit,
        "is_dirty": len(status_lines) > 0,
        "files_changed": len(changed_files),
        "insertions": insertions,
        "deletions": deletions,
        "changed_files": changed_files[:50],
        "languages_touched": _infer_languages(lang_source_files),
        "recent_commits": recent_commits,
    }


def harvest_code_semantics(
    cwd: Path, git_info: Dict[str, Any], tools: Dict[str, bool]
) -> Optional[Dict[str, Any]]:
    """Invoke optional Ataraxy Labs sem/inspect CLIs if installed and inside git."""
    if not git_info.get("is_git"):
        return None
    semantics: Dict[str, Any] = {}

    if tools.get("sem"):
        sem_args = ["sem", "diff", "--format", "json"]
        if not git_info.get("is_dirty") and git_info.get("head_commit"):
            sem_args = ["sem", "diff", "--commit", "HEAD", "--format", "json"]
        raw = _run_cmd(sem_args, cwd, timeout=5)
        if raw:
            try:
                parsed = json.loads(raw)
                entities: List[Dict[str, Any]] = []
                for f_entry in parsed.get("files", []) if isinstance(parsed, dict) else []:
                    fpath = f_entry.get("path")
                    for ch in f_entry.get("changes", []):
                        entities.append(
                            {
                                "file": fpath,
                                "entity_type": ch.get("entity_type"),
                                "entity_name": ch.get("entity_name"),
                                "change_type": ch.get("change_type"),
                            }
                        )
                semantics["sem"] = {
                    "entities": entities[:40],
                    "summary": parsed.get("summary") if isinstance(parsed, dict) else None,
                }
            except Exception as exc:
                sys.stderr.write(f"Warning: failed to parse sem JSON output: {exc}\n")

    if tools.get("inspect"):
        inspect_args = ["inspect", "diff", "--format", "json"]
        if not git_info.get("is_dirty") and git_info.get("head_commit"):
            if _run_cmd(["git", "rev-parse", "--verify", "HEAD~1"], cwd):
                inspect_args = ["inspect", "diff", "HEAD~1", "--format", "json"]
        raw = _run_cmd(inspect_args, cwd, timeout=5)
        if raw:
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    semantics["inspect"] = {
                        "risk_tier": parsed.get("risk_tier") or parsed.get("max_risk"),
                        "blast_radius": parsed.get("blast_radius")
                        or parsed.get("total_dependents"),
                        "classifications": parsed.get("classifications")
                        or parsed.get("summary"),
                    }
            except Exception as exc:
                sys.stderr.write(f"Warning: failed to parse inspect JSON output: {exc}\n")

    return semantics or None


def harvest_actor_defaults(cwd: Path) -> Dict[str, str]:
    """Detect default author, machine, and stream_id."""
    author = None
    if shutil.which("git") and cwd.exists():
        author = _run_cmd(["git", "config", "user.name"], cwd)
        if author:
            author = author.strip()
    if not author:
        author = getpass.getuser() or "unknown"
    machine = socket.gethostname().split(".")[0] or "local"
    return {
        "author": author,
        "machine": machine,
        "stream_id": resolve_stream_id(None),
    }


def ensure_store_initialized(store_dir: Path) -> List[str]:
    """Idempotently initialize directory layout, .gitignore, and initial INDEX.md."""
    created: List[str] = []
    for sub in ("entries", "ledgers", "pending"):
        p = store_dir / sub
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(sub + "/")

    gitignore = store_dir / ".gitignore"
    if not gitignore.exists():
        write_text_atomic(
            gitignore,
            "*.tmp\n.*.tmp\n__pycache__/\npending/.nudged.json\n",
        )
        created.append(".gitignore")

    index_file = store_dir / "INDEX.md"
    if not index_file.exists():
        state = load_ledger_state(store_dir)
        write_text_atomic(index_file, compile_index_markdown(state))
        created.append("INDEX.md")

    return created


def _merge_unique_list(base: List[Any], extra: List[Any]) -> List[Any]:
    out = list(base)
    seen = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in out}
    for item in extra:
        sig = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if sig not in seen:
            seen.add(sig)
            out.append(item)
    return out


def load_ledger_state(store_dir: Path) -> Dict[str, Any]:
    """Load and fold all sharded JSONL ledgers into a unified graph state."""
    ledgers_dir = store_dir / "ledgers"
    entries_by_id: Dict[str, Dict[str, Any]] = {}
    addenda: List[Dict[str, Any]] = []
    parse_errors: List[Dict[str, Any]] = []
    ledger_files: List[Path] = []

    if ledgers_dir.is_dir():
        ledger_files = sorted(ledgers_dir.glob("**/*.jsonl"))
        for lf in ledger_files:
            rel_lf = lf.relative_to(store_dir).as_posix()
            try:
                raw_lines = lf.read_text(encoding="utf-8").splitlines()
            except Exception as exc:
                parse_errors.append({"file": rel_lf, "line": 0, "error": str(exc)})
                continue
            for idx, line in enumerate(raw_lines, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    rec = json.loads(stripped)
                except Exception as exc:
                    parse_errors.append({"file": rel_lf, "line": idx, "error": str(exc)})
                    continue
                if not isinstance(rec, dict):
                    parse_errors.append(
                        {"file": rel_lf, "line": idx, "error": "Record is not a JSON object"}
                    )
                    continue
                rtype = rec.get("record_type")
                if rtype == "entry":
                    eid = rec.get("id")
                    if not eid:
                        parse_errors.append(
                            {"file": rel_lf, "line": idx, "error": "Entry missing id"}
                        )
                        continue
                    folded = json.loads(json.dumps(rec))
                    folded["_ledger_file"] = rel_lf
                    folded["_addenda"] = []
                    entries_by_id[eid] = folded
                elif rtype == "addendum":
                    rec["_ledger_file"] = rel_lf
                    addenda.append(rec)
                else:
                    parse_errors.append(
                        {
                            "file": rel_lf,
                            "line": idx,
                            "error": f"Unknown record_type: {rtype!r}",
                        }
                    )

    # Fold addenda chronologically without mutating on-disk JSONL
    addenda.sort(key=lambda r: r.get("created_at", ""))
    orphan_addenda: List[Dict[str, Any]] = []
    for add in addenda:
        tid = add.get("target_id")
        if not tid or tid not in entries_by_id:
            orphan_addenda.append(add)
            continue
        ent = entries_by_id[tid]
        ent["_addenda"].append(add)
        for field in ("outcome", "verification", "confidence", "shelf_life"):
            if add.get(field):
                ent[field] = add[field]
        for list_field in (
            "links",
            "belief_revisions",
            "dead_ends",
            "findings",
            "rule_candidates",
        ):
            if add.get(list_field):
                ent[list_field] = _merge_unique_list(
                    ent.get(list_field, []), add[list_field]
                )
        closed = {c.strip().lower() for c in add.get("closed_threads", []) if isinstance(c, str)}
        if closed:
            ent["open_threads"] = [
                t for t in ent.get("open_threads", []) if str(t).strip().lower() not in closed
            ]
        if add.get("open_threads"):
            ent["open_threads"] = _merge_unique_list(
                ent.get("open_threads", []), add["open_threads"]
            )
        promoted = [
            p.strip().lower()
            for p in (add.get("promoted_rules") or [])
            if isinstance(p, str) and p.strip()
        ]
        if promoted and ent.get("rule_candidates"):
            kept_rules = []
            for rc in ent.get("rule_candidates", []):
                rule_txt = (
                    rc.get("rule", "") if isinstance(rc, dict) else str(rc)
                ).strip().lower()
                if any(p == rule_txt or p in rule_txt for p in promoted):
                    continue
                kept_rules.append(rc)
            ent["rule_candidates"] = kept_rules

    # Build incoming graph edges and supersession map
    cited_by: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    superseded_by: Dict[str, str] = {}
    ordered_entries = sorted(
        entries_by_id.values(), key=lambda e: e.get("created_at", "")
    )
    for ent in ordered_entries:
        src_id = ent["id"]
        for lnk in ent.get("links", []) or []:
            if not isinstance(lnk, dict):
                continue
            tgt = lnk.get("target_id")
            rel = lnk.get("rel")
            if tgt:
                cited_by[tgt].append({"source_id": src_id, "rel": rel or ""})
                if rel == "supersedes":
                    superseded_by[tgt] = src_id

    for eid, ent in entries_by_id.items():
        ent["_incoming_citations"] = len(cited_by.get(eid, []))
        ent["_superseded_by"] = superseded_by.get(eid)

    return {
        "entries_by_id": entries_by_id,
        "ordered_entries": list(reversed(ordered_entries)),  # newest first
        "addenda": addenda,
        "orphan_addenda": orphan_addenda,
        "cited_by": dict(cited_by),
        "superseded_by": superseded_by,
        "ledger_files": [lf.relative_to(store_dir).as_posix() for lf in ledger_files],
        "parse_errors": parse_errors,
    }


def _tokenize(text: str) -> List[str]:
    return [
        tok
        for tok in re.findall(r"[a-z0-9][a-z0-9_.-]{1,}", (text or "").lower())
        if len(tok) >= 2
    ]


def _entry_searchable_blob(ent: Dict[str, Any]) -> str:
    parts = [
        ent.get("title", ""),
        ent.get("summary", ""),
        ent.get("project", ""),
    ]
    for br in ent.get("belief_revisions", []) or []:
        if isinstance(br, dict):
            parts.extend(
                [br.get("assumed", ""), br.get("contradicted_by", ""), br.get("revised_model", "")]
            )
        else:
            parts.append(str(br))
    for de in ent.get("dead_ends", []) or []:
        if isinstance(de, dict):
            parts.extend(
                [de.get("hypothesis", ""), de.get("error_signature", ""), de.get("why_failed", "")]
            )
        else:
            parts.append(str(de))
    for fn in ent.get("findings", []) or []:
        if isinstance(fn, dict):
            parts.extend([fn.get("claim", ""), fn.get("evidence", "")])
        else:
            parts.append(str(fn))
    for rc in ent.get("rule_candidates", []) or []:
        if isinstance(rc, dict):
            parts.extend([rc.get("rule", ""), rc.get("rationale", "")])
        else:
            parts.append(str(rc))
    return " ".join(str(p) for p in parts if p).lower()


def find_related_entries(
    state: Dict[str, Any],
    project_hint: Optional[str] = None,
    tech_list: Optional[List[str]] = None,
    concept_list: Optional[List[str]] = None,
    query_text: Optional[str] = None,
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """Rank prior entries for typed graph edge discovery while context is hot."""
    tech_set = {t.strip().lower() for t in (tech_list or []) if t.strip()}
    concept_set = {c.strip().lower() for c in (concept_list or []) if c.strip()}
    query_tokens = set(_tokenize(query_text or ""))
    proj_low = (project_hint or "").strip().lower()

    scored: List[Tuple[float, Dict[str, Any], List[str]]] = []
    for ent in state.get("ordered_entries", []):
        score = 0.0
        matched_on: List[str] = []
        ctx = ent.get("context") or {}
        git_data = ent.get("git") or {}
        ent_proj = (ent.get("project") or "").lower()
        ent_repo = (git_data.get("repo") or "").lower()

        if proj_low and (proj_low == ent_proj or proj_low == ent_repo):
            score += 4.0
            matched_on.append(f"project:{proj_low}")

        ent_tech = {str(t).lower() for t in ctx.get("technologies", [])}
        tech_hits = sorted(tech_set & ent_tech)
        if tech_hits:
            score += 3.0 * len(tech_hits)
            matched_on.extend(f"tech:{t}" for t in tech_hits)

        ent_concepts = {str(c).lower() for c in ctx.get("concepts", [])} | {
            str(d).lower() for d in ctx.get("domains", [])
        }
        concept_hits = sorted(concept_set & ent_concepts)
        if concept_hits:
            score += 3.0 * len(concept_hits)
            matched_on.extend(f"concept:{c}" for c in concept_hits)

        blob = _entry_searchable_blob(ent)
        if query_tokens:
            token_hits = [tok for tok in sorted(query_tokens) if tok in blob]
            if token_hits:
                score += 1.5 * min(len(token_hits), 6)
                matched_on.extend(f"term:{t}" for t in token_hits[:4])

        if score > 0:
            if ent.get("shelf_life") == "evergreen":
                score += 1.5
            score += 0.5 * ent.get("_incoming_citations", 0)
            if ent.get("_superseded_by"):
                score -= 2.0
            scored.append((score, ent, matched_on))

    scored.sort(key=lambda item: (item[0], item[1].get("created_at", "")), reverse=True)
    results = []
    for score, ent, matched_on in scored[:top_n]:
        results.append(
            {
                "id": ent["id"],
                "title": ent.get("title"),
                "project": ent.get("project"),
                "summary": ent.get("summary"),
                "file_path": ent.get("file_path"),
                "shelf_life": ent.get("shelf_life"),
                "superseded_by": ent.get("_superseded_by"),
                "score": round(score, 2),
                "matched_on": matched_on,
            }
        )
    return results


def list_pending_stubs(store_dir: Path) -> List[Dict[str, Any]]:
    """Read unlogged session bookmark stubs from pending/."""
    pending_dir = store_dir / "pending"
    if not pending_dir.is_dir():
        return []
    stubs = []
    for p in sorted(pending_dir.glob("*.json"), reverse=True):
        if p.name.startswith("."):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["_stub_file"] = p.name
                stubs.append(data)
        except Exception:
            continue
    return stubs


def _generate_entry_id(existing_ids: set) -> str:
    stamp = utc_now().strftime("%Y%m%d-%H%M")
    for _ in range(16):
        candidate = f"{stamp}-{secrets.token_hex(2)}"
        if candidate not in existing_ids:
            return candidate
    return f"{stamp}-{secrets.token_hex(4)}"


def _validate_enum(val: Any, allowed: Tuple[str, ...], field: str, errors: List[str]) -> None:
    if val not in allowed:
        errors.append(f"Invalid '{field}': {val!r}. Allowed: {', '.join(allowed)}")


def _validate_rating(val: Any, field: str, errors: List[str]) -> Optional[int]:
    if val is None:
        return None
    if isinstance(val, bool) or not isinstance(val, int) or val < 1 or val > 5:
        errors.append(f"Metric '{field}' must be an integer 1..5 or null (got {val!r}).")
        return None
    return val


def _validate_nonempty_str(obj: Dict[str, Any], key: str, ctx: str, errors: List[str]) -> None:
    val = obj.get(key)
    if not isinstance(val, str) or not val.strip():
        errors.append(f"{ctx} missing required non-empty string '{key}'.")


def _validate_optional_str(obj: Dict[str, Any], key: str, ctx: str, errors: List[str]) -> None:
    val = obj.get(key)
    if val is not None and not isinstance(val, str):
        errors.append(f"{ctx}.{key} must be a string or null.")


def _validate_epistemic_lists(payload: Dict[str, Any], errors: List[str], include_closed: bool = False) -> None:
    """Validate nested schemas for belief_revisions, dead_ends, findings, rule_candidates, and threads."""
    list_keys = ("belief_revisions", "dead_ends", "findings", "rule_candidates", "open_threads")
    if include_closed:
        list_keys = list_keys + ("closed_threads", "promoted_rules")

    for list_name in list_keys:
        val = payload.get(list_name)
        if val is not None and not isinstance(val, list):
            errors.append(f"'{list_name}' must be a list.")

    brs = payload.get("belief_revisions")
    if isinstance(brs, list):
        for i, item in enumerate(brs):
            ctx = f"belief_revisions[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{ctx} must be an object.")
                continue
            for req in ("assumed", "contradicted_by", "revised_model"):
                _validate_nonempty_str(item, req, ctx, errors)

    des = payload.get("dead_ends")
    if isinstance(des, list):
        for i, item in enumerate(des):
            ctx = f"dead_ends[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{ctx} must be an object.")
                continue
            for req in ("hypothesis", "why_failed"):
                _validate_nonempty_str(item, req, ctx, errors)
            _validate_optional_str(item, "error_signature", ctx, errors)

    fns = payload.get("findings")
    if isinstance(fns, list):
        for i, item in enumerate(fns):
            ctx = f"findings[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{ctx} must be an object.")
                continue
            _validate_nonempty_str(item, "claim", ctx, errors)
            if item.get("confidence") is not None:
                _validate_enum(item["confidence"], CONFIDENCE_LEVELS, f"{ctx}.confidence", errors)
            if item.get("shelf_life") is not None:
                _validate_enum(item["shelf_life"], SHELF_LIVES, f"{ctx}.shelf_life", errors)
            _validate_optional_str(item, "evidence", ctx, errors)

    rcs = payload.get("rule_candidates")
    if isinstance(rcs, list):
        for i, item in enumerate(rcs):
            ctx = f"rule_candidates[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{ctx} must be an object.")
                continue
            for req in ("scope", "rule"):
                _validate_nonempty_str(item, req, ctx, errors)
            _validate_optional_str(item, "rationale", ctx, errors)

    thread_keys = ("open_threads", "closed_threads", "promoted_rules") if include_closed else ("open_threads",)
    for tkey in thread_keys:
        tlist = payload.get(tkey)
        if isinstance(tlist, list):
            for i, item in enumerate(tlist):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"{tkey}[{i}] must be a non-empty string.")


def validate_write_payload(payload: Any) -> Tuple[Dict[str, Any], List[str]]:
    """Validate and normalize a write payload against schema_version 1."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {}, ["Input payload must be a JSON object."]

    sv = payload.get("schema_version", SCHEMA_VERSION)
    if sv != SCHEMA_VERSION:
        errors.append(f"Unsupported schema_version: {sv!r} (expected {SCHEMA_VERSION}).")

    for req in ("title", "summary", "project", "session_shape", "outcome"):
        if not payload.get(req) or not isinstance(payload.get(req), str):
            errors.append(f"Required non-empty string field '{req}' is missing or invalid.")

    shape = payload.get("session_shape", "build")
    outcome = payload.get("outcome", "resolved")
    confidence = payload.get("confidence", "observed")
    shelf_life = payload.get("shelf_life", "version-bound")
    visibility = payload.get("visibility", "private")
    verification = payload.get("verification", "none")

    if "session_shape" in payload:
        _validate_enum(shape, SESSION_SHAPES, "session_shape", errors)
    if "outcome" in payload:
        _validate_enum(outcome, OUTCOMES, "outcome", errors)
    _validate_enum(confidence, CONFIDENCE_LEVELS, "confidence", errors)
    _validate_enum(shelf_life, SHELF_LIVES, "shelf_life", errors)
    _validate_enum(visibility, VISIBILITIES, "visibility", errors)
    _validate_enum(verification, VERIFICATIONS, "verification", errors)

    telemetry = payload.get("telemetry") or {}
    if not isinstance(telemetry, dict):
        errors.append("'telemetry' must be an object.")
        telemetry = {}

    agent_impact = telemetry.get("agent_impact", "helpful")
    _validate_enum(agent_impact, AGENT_IMPACTS, "telemetry.agent_impact", errors)

    failure_modes = telemetry.get("agent_failure_modes") or []
    if not isinstance(failure_modes, list):
        errors.append("'telemetry.agent_failure_modes' must be a list.")
        failure_modes = []
    else:
        for fm in failure_modes:
            _validate_enum(fm, AGENT_FAILURE_MODES, "telemetry.agent_failure_modes[]", errors)

    catalyst = telemetry.get("unsticking_catalyst", "none")
    _validate_enum(catalyst, UNSTICKING_CATALYSTS, "telemetry.unsticking_catalyst", errors)

    metrics_in = payload.get("metrics") or {}
    if not isinstance(metrics_in, dict):
        errors.append("'metrics' must be an object.")
        metrics_in = {}
    friction = _validate_rating(metrics_in.get("friction"), "metrics.friction", errors)
    value = _validate_rating(metrics_in.get("value"), "metrics.value", errors)

    links = payload.get("links") or []
    if not isinstance(links, list):
        errors.append("'links' must be a list.")
        links = []
    else:
        for i, lnk in enumerate(links):
            if not isinstance(lnk, dict):
                errors.append(f"links[{i}] must be an object.")
                continue
            _validate_enum(lnk.get("rel"), LINK_RELS, f"links[{i}].rel", errors)
            if not lnk.get("target_id") or not isinstance(lnk.get("target_id"), str):
                errors.append(f"links[{i}].target_id must be a non-empty string.")

    if payload.get("actor") is not None and not isinstance(payload.get("actor"), dict):
        errors.append("'actor' must be an object.")
    if payload.get("context") is not None and not isinstance(payload.get("context"), dict):
        errors.append("'context' must be an object.")

    _validate_epistemic_lists(payload, errors, include_closed=False)

    if errors:
        return payload, errors

    actor_in = payload.get("actor") or {}
    cwd_path = Path((payload.get("context") or {}).get("cwd") or ".").expanduser()
    actor_defaults = harvest_actor_defaults(cwd_path if cwd_path.exists() else Path("."))
    actor = {
        "author": actor_in.get("author") or actor_defaults["author"],
        "machine": actor_in.get("machine") or actor_defaults["machine"],
        "harness": actor_in.get("harness") or "unknown",
        "model": actor_in.get("model") or "unknown",
        "models_used": actor_in.get("models_used")
        or ([actor_in["model"]] if actor_in.get("model") else []),
        "skills_used": actor_in.get("skills_used") or [],
        "conversation_id": actor_in.get("conversation_id"),
    }

    ctx_in = payload.get("context") or {}
    context = {
        "scope": ctx_in.get("scope"),
        "cwd": ctx_in.get("cwd"),
        "domains": [str(x) for x in (ctx_in.get("domains") or [])],
        "technologies": [str(x) for x in (ctx_in.get("technologies") or [])],
        "concepts": [str(x) for x in (ctx_in.get("concepts") or [])],
    }

    belief_revisions = payload.get("belief_revisions") or []
    dead_ends = payload.get("dead_ends") or []
    findings = payload.get("findings") or []
    rule_candidates = payload.get("rule_candidates") or []
    open_threads = [str(t) for t in (payload.get("open_threads") or []) if str(t).strip()]

    git_in = payload.get("git")
    derived_metrics = {
        "friction": friction,
        "value": value,
        "dead_ends_count": len(dead_ends),
        "belief_revisions_count": len(belief_revisions),
        "rule_candidates_count": len(rule_candidates),
        "findings_count": len(findings),
        "open_threads_count": len(open_threads),
        "links_count": len(links),
        "files_changed": git_in.get("files_changed") if isinstance(git_in, dict) else None,
        "insertions": git_in.get("insertions") if isinstance(git_in, dict) else None,
        "deletions": git_in.get("deletions") if isinstance(git_in, dict) else None,
    }

    normalized = {
        "schema_version": SCHEMA_VERSION,
        "title": payload["title"].strip(),
        "summary": payload["summary"].strip(),
        "project": sanitize_slug(payload["project"], max_len=64),
        "session_shape": shape,
        "outcome": outcome,
        "confidence": confidence,
        "shelf_life": shelf_life,
        "visibility": visibility,
        "verification": verification,
        "actor": actor,
        "context": context,
        "telemetry": {
            "agent_impact": agent_impact,
            "agent_failure_modes": failure_modes,
            "unsticking_catalyst": catalyst,
            "notes": telemetry.get("notes"),
        },
        "metrics": derived_metrics,
        "belief_revisions": belief_revisions,
        "dead_ends": dead_ends,
        "findings": findings,
        "rule_candidates": rule_candidates,
        "open_threads": open_threads,
        "links": links,
        "git": git_in if isinstance(git_in, dict) else None,
        "code_semantics": payload.get("code_semantics")
        if isinstance(payload.get("code_semantics"), dict)
        else None,
    }
    return normalized, []


def _resolve_links_for_markdown(
    links: List[Dict[str, Any]],
    entry_file_abs: Path,
    store_dir: Path,
    state: Dict[str, Any],
) -> List[Dict[str, Any]]:
    resolved = []
    entries = state.get("entries_by_id", {})
    for lnk in links:
        tid = lnk.get("target_id", "")
        rel = lnk.get("rel", "")
        note = lnk.get("note", "")
        target_ent = entries.get(tid)
        if target_ent and target_ent.get("file_path"):
            target_abs = store_dir / target_ent["file_path"]
            rel_link = os.path.relpath(target_abs, entry_file_abs.parent).replace(os.sep, "/")
            resolved.append(
                {
                    "rel": rel,
                    "target_id": tid,
                    "target_title": target_ent.get("title") or tid,
                    "rel_path": rel_link,
                    "note": note,
                    "resolved": True,
                }
            )
        else:
            sys.stderr.write(
                f"Warning: graph link target_id {tid!r} not found in existing ledgers.\n"
            )
            resolved.append(
                {
                    "rel": rel,
                    "target_id": tid,
                    "target_title": tid,
                    "rel_path": None,
                    "note": note,
                    "resolved": False,
                }
            )
    return resolved


def render_entry_markdown(
    record: Dict[str, Any], resolved_links: List[Dict[str, Any]]
) -> str:
    """Render portable YAML frontmatter + structured Knowledge & Thoroughness Markdown."""
    fm = {
        "id": record["id"],
        "schema_version": record["schema_version"],
        "created_at": record["created_at"],
        "title": record["title"],
        "project": record["project"],
        "scope": record["context"].get("scope"),
        "visibility": record["visibility"],
        "session_shape": record["session_shape"],
        "outcome": record["outcome"],
        "confidence": record["confidence"],
        "shelf_life": record["shelf_life"],
        "verification": record["verification"],
        "actor": record["actor"],
        "domains": record["context"].get("domains", []),
        "technologies": record["context"].get("technologies", []),
        "concepts": record["context"].get("concepts", []),
        "metrics": record["metrics"],
        "telemetry": {
            "agent_impact": record["telemetry"].get("agent_impact"),
            "agent_failure_modes": record["telemetry"].get("agent_failure_modes", []),
            "unsticking_catalyst": record["telemetry"].get("unsticking_catalyst"),
        },
        "links": record["links"],
    }

    lines = ["---"]
    lines.extend(yaml_dump(fm))
    lines.append("---")
    lines.append("")
    lines.append(f"# {record['title']}")
    lines.append("")
    lines.append(f"> **Highlight:** {record['summary']}")
    lines.append("")

    m = record["metrics"]
    friction_s = f"{m['friction']}/5" if m.get("friction") is not None else "n/a"
    value_s = f"{m['value']}/5" if m.get("value") is not None else "n/a"
    actor = record["actor"]
    lines.append(
        f"- **ID:** `{record['id']}` | **Date:** {record['created_at'][:10]} | "
        f"**Project:** `{record['project']}`"
    )
    lines.append(
        f"- **Shape:** `{record['session_shape']}` | **Outcome:** `{record['outcome']}` | "
        f"**Verification:** `{record['verification']}`"
    )
    lines.append(
        f"- **Friction:** {friction_s} | **Value:** {value_s} | "
        f"**Confidence:** `{record['confidence']}` | **Shelf Life:** `{record['shelf_life']}`"
    )
    lines.append(
        f"- **Harness / Model:** `{actor.get('harness')}` / `{actor.get('model')}` | "
        f"**Machine:** `{actor.get('machine')}` | **Visibility:** `{record['visibility']}`"
    )
    lines.append("")

    lines.append("## Belief Revisions")
    if record["belief_revisions"]:
        for br in record["belief_revisions"]:
            if isinstance(br, dict):
                lines.append(
                    f"- **Assumed:** {br.get('assumed', '')}  \n"
                    f"  **Contradicted by:** {br.get('contradicted_by', '')}  \n"
                    f"  **Revised model:** {br.get('revised_model', '')}"
                )
            else:
                lines.append(f"- {br}")
    else:
        lines.append("- None recorded.")
    lines.append("")

    lines.append("## Dead Ends, Roadblocks & Exact Signatures")
    if record["dead_ends"]:
        for de in record["dead_ends"]:
            if isinstance(de, dict):
                hyp = de.get("hypothesis", "")
                sig = de.get("error_signature", "")
                why = de.get("why_failed", "")
                sig_str = f" (`{sig}`)" if sig else ""
                lines.append(f"- **{hyp}**{sig_str}: {why}")
            else:
                lines.append(f"- {de}")
    else:
        lines.append("- None recorded.")
    lines.append("")

    lines.append("## Breakthroughs & Validated Findings")
    if record["findings"]:
        for fn in record["findings"]:
            if isinstance(fn, dict):
                claim = fn.get("claim", "")
                conf = fn.get("confidence", record["confidence"])
                sl = fn.get("shelf_life", record["shelf_life"])
                ev = fn.get("evidence", "")
                ev_str = f" — *Evidence:* {ev}" if ev else ""
                lines.append(f"- [{conf} | {sl}] {claim}{ev_str}")
            else:
                lines.append(f"- {fn}")
    else:
        lines.append("- None recorded.")
    lines.append("")

    tel = record["telemetry"]
    lines.append("## Human–Agent Loop")
    lines.append(f"- **Agent Impact:** `{tel.get('agent_impact')}`")
    modes = ", ".join(f"`{x}`" for x in tel.get("agent_failure_modes", [])) or "none"
    lines.append(f"- **Failure Modes:** {modes}")
    lines.append(f"- **Unsticking Catalyst:** `{tel.get('unsticking_catalyst')}`")
    if tel.get("notes"):
        lines.append(f"- **Loop Notes:** {tel['notes']}")
    lines.append("")

    lines.append("## Rule Candidates")
    if record["rule_candidates"]:
        for rc in record["rule_candidates"]:
            if isinstance(rc, dict):
                scope = rc.get("scope", "general")
                rule = rc.get("rule", "")
                rat = rc.get("rationale", "")
                rat_s = f" ({rat})" if rat else ""
                lines.append(f"- [`{scope}`] {rule}{rat_s}")
            else:
                lines.append(f"- {rc}")
    else:
        lines.append("- None recorded.")
    lines.append("")

    lines.append("## Open Threads")
    if record["open_threads"]:
        for th in record["open_threads"]:
            lines.append(f"- [ ] {th}")
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## Graph Connections")
    if resolved_links:
        for lnk in resolved_links:
            note_s = f" — {lnk['note']}" if lnk.get("note") else ""
            if lnk["resolved"]:
                lines.append(
                    f"- `{lnk['rel']}` → [{lnk['target_title']}]({lnk['rel_path']}) "
                    f"(`{lnk['target_id']}`){note_s}"
                )
            else:
                lines.append(
                    f"- `{lnk['rel']}` → `{lnk['target_id']}` *(unresolved target)*{note_s}"
                )
    else:
        lines.append("- None yet.")
    lines.append("")

    lines.append("## Ground Truth Snapshot")
    git_data = record.get("git")
    if isinstance(git_data, dict) and git_data.get("is_git"):
        lines.append(
            f"- **Repo:** `{git_data.get('repo')}` | **Branch:** `{git_data.get('branch')}` | "
            f"**HEAD:** `{git_data.get('head_commit')}` | **Dirty:** `{git_data.get('is_dirty')}`"
        )
        lines.append(
            f"- **Diff Stat:** {git_data.get('files_changed', 0)} files, "
            f"+{git_data.get('insertions', 0)} / -{git_data.get('deletions', 0)}"
        )
        if git_data.get("languages_touched"):
            lines.append(
                "- **Languages:** "
                + ", ".join(f"`{x}`" for x in git_data["languages_touched"])
            )
    else:
        lines.append("- Non-git workspace or no repository context.")

    sem_data = record.get("code_semantics")
    if isinstance(sem_data, dict):
        if sem_data.get("sem"):
            ents = sem_data["sem"].get("entities", [])
            ent_preview = ", ".join(
                f"`{e.get('entity_name')}` ({e.get('change_type')})"
                for e in ents[:8]
                if e.get("entity_name")
            )
            lines.append(
                f"- **Semantic Entities (`sem`):** {len(ents)} captured"
                + (f" — {ent_preview}" if ent_preview else "")
            )
        if sem_data.get("inspect"):
            ins = sem_data["inspect"]
            lines.append(
                f"- **Blast Radius (`inspect`):** risk=`{ins.get('risk_tier')}`, "
                f"dependents=`{ins.get('blast_radius')}`"
            )
    lines.append("")
    return "\n".join(lines)


def _mean(nums: List[float]) -> Optional[float]:
    return round(sum(nums) / len(nums), 2) if nums else None


def _truncate_text(text: str, max_len: int = 140) -> str:
    """Truncate text cleanly to max_len characters."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def compile_project_index_markdown(project: str, entries: List[Dict[str, Any]]) -> str:
    """Deterministically compile a per-project overflow shard under indexes/by-project/."""
    total = len(entries)
    resolved_cnt = sum(1 for e in entries if e.get("outcome") == "resolved")
    lines = [
        f"# Engineering Log Project Index: `{project}`",
        "",
        f"> Auto-compiled from `ledgers/**/*.jsonl`. Entries: {total} | Resolved: {resolved_cnt}",
        "",
        "| Date | ID | Title | Summary | Outcome | Shape | F/V | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for ent in entries:
        date_s = (ent.get("created_at") or "")[:10]
        eid = ent["id"]
        title = (ent.get("title") or eid).replace("|", "\\|")
        summary = _truncate_text(ent.get("summary") or "", 140).replace("|", "\\|")
        fpath = (ent.get("file_path") or "").replace("\\", "/")
        link_md = f"[{title}](../../{fpath})" if fpath else title
        m = ent.get("metrics") or {}
        fv = f"{m.get('friction') or '-'}/{m.get('value') or '-'}"
        sup = ent.get("_superseded_by")
        status = f"superseded by `{sup}`" if sup else (ent.get("shelf_life") or "active")
        lines.append(
            f"| {date_s} | `{eid}` | {link_md} | {summary} | `{ent.get('outcome')}` | "
            f"`{ent.get('session_shape')}` | {fv} | {status} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_compiled_indexes(store_dir: Path, state: Dict[str, Any]) -> None:
    """Write deterministic INDEX.md and overflow project shards when > 50 entries."""
    write_text_atomic(store_dir / "INDEX.md", compile_index_markdown(state))
    entries = state.get("ordered_entries", [])
    by_proj_dir = store_dir / "indexes" / "by-project"
    if len(entries) > 50:
        by_proj_dir.mkdir(parents=True, exist_ok=True)
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for ent in entries:
            grouped[ent.get("project", "general")].append(ent)
        active_files = set()
        for proj, p_ents in sorted(grouped.items()):
            fname = f"{sanitize_slug(proj, max_len=64)}.md"
            active_files.add(fname)
            write_text_atomic(by_proj_dir / fname, compile_project_index_markdown(proj, p_ents))
        for existing in by_proj_dir.glob("*.md"):
            if existing.name not in active_files:
                existing.unlink(missing_ok=True)
    elif by_proj_dir.is_dir():
        for existing in by_proj_dir.glob("*.md"):
            existing.unlink(missing_ok=True)


def compile_index_markdown(state: Dict[str, Any]) -> str:
    """Deterministically compile bounded, graph-aware INDEX.md from folded ledger state."""
    entries = state.get("ordered_entries", [])
    entries_by_id = state.get("entries_by_id", {})
    cited_by = state.get("cited_by", {})
    superseded_by = state.get("superseded_by", {})
    total = len(entries)
    resolved_cnt = sum(1 for e in entries if e.get("outcome") == "resolved")
    frictions = [
        e["metrics"]["friction"]
        for e in entries
        if isinstance(e.get("metrics"), dict) and e["metrics"].get("friction") is not None
    ]
    values = [
        e["metrics"]["value"]
        for e in entries
        if isinstance(e.get("metrics"), dict) and e["metrics"].get("value") is not None
    ]

    active_threads: List[Tuple[str, str, str, str]] = []
    evergreen_rules: List[Tuple[str, str, str, str, str]] = []
    failure_counts: Counter = Counter()
    catalyst_counts: Counter = Counter()
    tag_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for ent in entries:
        for th in ent.get("open_threads", []) or []:
            active_threads.append(
                (ent.get("project", "general"), th, ent["id"], ent.get("file_path", ""))
            )
        if not ent.get("_superseded_by"):
            for rc in ent.get("rule_candidates", []) or []:
                if isinstance(rc, dict):
                    evergreen_rules.append(
                        (
                            rc.get("scope", "general"),
                            rc.get("rule", ""),
                            ent.get("project", "general"),
                            ent["id"],
                            ent.get("file_path", ""),
                        )
                    )
                else:
                    evergreen_rules.append(
                        (
                            "general",
                            str(rc),
                            ent.get("project", "general"),
                            ent["id"],
                            ent.get("file_path", ""),
                        )
                    )
            ctx = ent.get("context") or {}
            seen_terms = set()
            for raw_term in list(ctx.get("concepts") or []) + list(ctx.get("technologies") or []):
                term = str(raw_term).strip().lower()
                if term and term not in seen_terms:
                    seen_terms.add(term)
                    tag_index[term].append(ent)
        tel = ent.get("telemetry") or {}
        for fm in tel.get("agent_failure_modes", []) or []:
            failure_counts[fm] += 1
        cat = tel.get("unsticking_catalyst")
        if cat and cat != "none":
            catalyst_counts[cat] += 1

    top_fm = failure_counts.most_common(1)[0] if failure_counts else None
    top_cat = catalyst_counts.most_common(1)[0] if catalyst_counts else None

    lines = [
        "# Engineering Log Index",
        "",
        "> Auto-compiled deterministically from `ledgers/**/*.jsonl` by `eng_log.py`. Do not hand-edit.",
        "",
        "## Summary KPIs",
        "",
        f"- **Total Sessions:** {total} | **Resolved:** {resolved_cnt} | "
        f"**Mean Friction:** {_mean(frictions) if frictions else 'n/a'} | "
        f"**Mean Value:** {_mean(values) if values else 'n/a'}",
        f"- **Active Open Threads:** {len(active_threads)} | **Rule Candidates:** {len(evergreen_rules)}",
        f"- **Top Agent Failure Mode:** `{top_fm[0]}` ({top_fm[1]})" if top_fm else "- **Top Agent Failure Mode:** none",
        f"- **Top Unsticking Catalyst:** `{top_cat[0]}` ({top_cat[1]})" if top_cat else "- **Top Unsticking Catalyst:** none",
        "",
        "## Session Highlights (Reverse-Chronological)",
        "",
    ]

    if entries:
        recent_entries = entries[:50]
        if total > 50:
            lines.append(
                f"_Showing latest 50 of {total} entries; see `indexes/by-project/` or run `eng_log.py query`._"
            )
            lines.append("")
        lines.append(
            "| Date | ID | Project | Highlight | Outcome | Shape | F/V | Status |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for ent in recent_entries:
            date_s = (ent.get("created_at") or "")[:10]
            eid = ent["id"]
            proj = ent.get("project", "general")
            title = (ent.get("title") or eid).replace("|", "\\|")
            summary = _truncate_text(ent.get("summary") or "", 140).replace("|", "\\|")
            fpath = (ent.get("file_path") or "").replace("\\", "/")
            link_md = f"[{title}]({fpath})" if fpath else title
            highlight = f"{link_md} — {summary}" if summary else link_md
            m = ent.get("metrics") or {}
            fv = f"{m.get('friction') or '-'}/{m.get('value') or '-'}"
            sup = ent.get("_superseded_by")
            status = f"superseded by `{sup}`" if sup else (ent.get("shelf_life") or "active")
            lines.append(
                f"| {date_s} | `{eid}` | `{proj}` | {highlight} | `{ent.get('outcome')}` | "
                f"`{ent.get('session_shape')}` | {fv} | {status} |"
            )
    else:
        lines.append("_No entries logged yet._")
    lines.append("")

    lines.append("## Graph Hubs & Concept Map")
    lines.append("")
    hubs = []
    for ent in entries:
        inc = ent.get("_incoming_citations", 0)
        out = len(ent.get("links") or [])
        if inc + out > 0:
            hubs.append((inc + out, inc, ent.get("created_at", ""), ent, out))
    hubs.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)

    same_root_clusters: List[Tuple[str, List[str]]] = []
    for anchor_id in sorted(cited_by):
        srcs = [r["source_id"] for r in cited_by[anchor_id] if r.get("rel") == "same_root_cause"]
        if srcs:
            same_root_clusters.append((anchor_id, srcs))

    sup_chains: List[Tuple[str, str]] = sorted(
        ((new_id, old_id) for old_id, new_id in superseded_by.items()),
        reverse=True,
    )

    if hubs or same_root_clusters or sup_chains or tag_index:
        if hubs:
            lines.append("### Connected Hubs")
            for _, inc, _, ent, out in hubs[:10]:
                fpath = (ent.get("file_path") or "").replace("\\", "/")
                title = ent.get("title") or ent["id"]
                link_md = f"[{title}]({fpath})" if fpath else title
                sup_s = f" *(superseded by `{ent['_superseded_by']}`)*" if ent.get("_superseded_by") else ""
                lines.append(
                    f"- `{ent['id']}` {link_md} (`{ent.get('project', 'general')}`) — "
                    f"in={inc} / out={out}{sup_s}"
                )
            lines.append("")

        if same_root_clusters or sup_chains:
            lines.append("### Typed Clusters & Chains")
            for anchor_id, srcs in same_root_clusters[:10]:
                cluster_ids = [anchor_id] + srcs
                refs = []
                for cid in cluster_ids:
                    c_ent = entries_by_id.get(cid)
                    if c_ent and c_ent.get("file_path"):
                        refs.append(f"[`{cid}`]({c_ent['file_path'].replace(chr(92), '/')})")
                    else:
                        refs.append(f"`{cid}`")
                lines.append(f"- `same_root_cause`: " + ", ".join(refs))
            for new_id, old_id in sup_chains[:10]:
                n_ent = entries_by_id.get(new_id)
                o_ent = entries_by_id.get(old_id)
                n_ref = f"[`{new_id}`]({n_ent['file_path'].replace(chr(92), '/')})" if n_ent and n_ent.get("file_path") else f"`{new_id}`"
                o_ref = f"[`{old_id}`]({o_ent['file_path'].replace(chr(92), '/')})" if o_ent and o_ent.get("file_path") else f"`{old_id}`"
                lines.append(f"- `supersedes`: {n_ref} → {o_ref}")
            lines.append("")

        if tag_index:
            lines.append("### Concept & Tech Index")
            top_terms = sorted(tag_index.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:20]
            for term, term_ents in top_terms:
                refs = []
                for te in term_ents[:5]:
                    fpath = (te.get("file_path") or "").replace("\\", "/")
                    refs.append(f"[`{te['id']}`]({fpath})" if fpath else f"`{te['id']}`")
                lines.append(f"- **`{term}`** ({len(term_ents)}): " + ", ".join(refs))
            lines.append("")
    else:
        lines.append("_No graph links or concept tags recorded yet._")
        lines.append("")

    lines.append("## Active Open Threads")
    lines.append("")
    if active_threads:
        for proj, th, eid, fpath in active_threads[:50]:
            ref = f"[`{eid}`]({fpath.replace(chr(92), '/')})" if fpath else f"`{eid}`"
            lines.append(f"- [ ] **[{proj}]** {th} ({ref})")
    else:
        lines.append("_No open threads._")
    lines.append("")

    lines.append("## Promotable Rule Candidates")
    lines.append("")
    if evergreen_rules:
        for scope, rule, proj, eid, fpath in evergreen_rules[:50]:
            ref = f"[`{eid}`]({fpath.replace(chr(92), '/')})" if fpath else f"`{eid}`"
            lines.append(f"- [`{scope}` | `{proj}`] {rule} ({ref})")
    else:
        lines.append("_No rule candidates recorded yet._")
    lines.append("")

    lines.append("## Projects Breakdown")
    lines.append("")
    if entries:
        by_proj: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for ent in entries:
            by_proj[ent.get("project", "general")].append(ent)
        lines.append("| Project | Entries | Resolved | Mean Friction | Mean Value | Last Logged |")
        lines.append("| :--- | ---: | ---: | ---: | ---: | :--- |")
        for proj in sorted(by_proj):
            p_ents = by_proj[proj]
            p_res = sum(1 for e in p_ents if e.get("outcome") == "resolved")
            p_f = [
                e["metrics"]["friction"]
                for e in p_ents
                if isinstance(e.get("metrics"), dict) and e["metrics"].get("friction") is not None
            ]
            p_v = [
                e["metrics"]["value"]
                for e in p_ents
                if isinstance(e.get("metrics"), dict) and e["metrics"].get("value") is not None
            ]
            last_dt = max((e.get("created_at") or "")[:10] for e in p_ents)
            lines.append(
                f"| `{proj}` | {len(p_ents)} | {p_res} | "
                f"{_mean(p_f) if p_f else '-'} | {_mean(p_v) if p_v else '-'} | {last_dt} |"
            )
    else:
        lines.append("_No projects recorded yet._")
    lines.append("")
    return "\n".join(lines)


def _read_json_input(input_arg: Optional[str]) -> Any:
    if not input_arg or input_arg == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(input_arg).read_text(encoding="utf-8")
    if not raw.strip():
        raise ValueError("Empty JSON input.")
    return json.loads(raw)


def _clean_matching_pending_stub(store_dir: Path, conv_id: Optional[str]) -> None:
    if not conv_id:
        return
    pending_dir = store_dir / "pending"
    if not pending_dir.is_dir():
        return
    for p in pending_dir.glob("*.json"):
        if p.name.startswith("."):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("conversation_id") == conv_id:
                p.unlink(missing_ok=True)
        except Exception:
            continue


def cmd_init(args: argparse.Namespace) -> Dict[str, Any]:
    store_dir = resolve_store_dir(args.dir)
    created = ensure_store_initialized(store_dir)
    return {
        "status": "ok",
        "action": "init",
        "store_dir": str(store_dir),
        "created": created,
    }


def cmd_context(args: argparse.Namespace) -> Dict[str, Any]:
    store_dir = resolve_store_dir(args.dir)
    cwd = Path(args.cwd).expanduser().resolve()
    tools = detect_tools()
    actor_defaults = harvest_actor_defaults(cwd)
    git_info = harvest_git_info(cwd)
    code_semantics = harvest_code_semantics(cwd, git_info, tools)

    state = load_ledger_state(store_dir) if store_dir.exists() else {"ordered_entries": []}
    tech_list = [x.strip() for x in (args.tech or "").split(",") if x.strip()]
    tech_list.extend(git_info.get("languages_touched", []))
    concept_list = [x.strip() for x in (args.concepts or "").split(",") if x.strip()]
    project_hint = git_info.get("repo") or (cwd.name if cwd.exists() else None)
    query_parts = [args.query or ""] + [
        Path(p).stem for p in git_info.get("changed_files", [])[:10]
    ]
    related = find_related_entries(
        state,
        project_hint=project_hint,
        tech_list=tech_list,
        concept_list=concept_list,
        query_text=" ".join(query_parts),
        top_n=args.top,
    )
    pending = list_pending_stubs(store_dir) if store_dir.exists() else []

    return {
        "status": "ok",
        "action": "context",
        "store_dir": str(store_dir),
        "store_initialized": store_dir.exists(),
        "cwd": str(cwd),
        "tools": tools,
        "actor_defaults": actor_defaults,
        "git": git_info,
        "code_semantics": code_semantics,
        "related_entries": related,
        "pending_stubs": pending,
    }


def _auto_harvest_write_context(
    raw_payload: Any, cwd_arg: Optional[str], no_auto_harvest: bool
) -> Tuple[bool, bool]:
    """Deterministically attach git and code_semantics when omitted on write."""
    if no_auto_harvest or not isinstance(raw_payload, dict):
        return False, False

    ctx_in = raw_payload.get("context")
    if ctx_in is not None and not isinstance(ctx_in, dict):
        return False, False

    cwd_str = cwd_arg or (ctx_in.get("cwd") if isinstance(ctx_in, dict) else None)
    if not cwd_str:
        return False, False

    cwd_path = Path(cwd_str).expanduser().resolve()
    if ctx_in is None:
        raw_payload["context"] = {"cwd": str(cwd_path)}
    elif not ctx_in.get("cwd"):
        ctx_in["cwd"] = str(cwd_path)

    auto_git = False
    auto_sem = False
    git_info = raw_payload.get("git")
    if "git" not in raw_payload or git_info is None:
        harvested_git = harvest_git_info(cwd_path)
        if harvested_git.get("is_git"):
            raw_payload["git"] = harvested_git
            git_info = harvested_git
            auto_git = True
        else:
            raw_payload["git"] = None
            git_info = None

    if (
        ("code_semantics" not in raw_payload or raw_payload.get("code_semantics") is None)
        and isinstance(git_info, dict)
        and git_info.get("is_git")
    ):
        sem_info = harvest_code_semantics(cwd_path, git_info, detect_tools())
        if sem_info:
            raw_payload["code_semantics"] = sem_info
            auto_sem = True

    return auto_git, auto_sem


def cmd_write(args: argparse.Namespace) -> Dict[str, Any]:
    store_dir = resolve_store_dir(args.dir)
    raw_payload = _read_json_input(args.input)
    auto_git, auto_sem = _auto_harvest_write_context(
        raw_payload, getattr(args, "cwd", None), getattr(args, "no_auto_harvest", False)
    )
    normalized, val_errors = validate_write_payload(raw_payload)
    if val_errors:
        raise ValueError("Payload validation failed:\n- " + "\n- ".join(val_errors))

    scrubbed, redactions = scrub_value(normalized)
    if redactions > 0:
        sys.stderr.write(f"Secret scrubber redacted {redactions} sensitive token(s).\n")

    state = load_ledger_state(store_dir) if store_dir.exists() else {"entries_by_id": {}, "ordered_entries": []}
    conv_id = scrubbed["actor"].get("conversation_id")
    if conv_id and not getattr(args, "allow_duplicate", False):
        for existing_id, existing_ent in state.get("entries_by_id", {}).items():
            if (existing_ent.get("actor") or {}).get("conversation_id") == conv_id:
                raise ValueError(
                    f"Entry {existing_id!r} already exists for conversation_id {conv_id!r}. "
                    f"Use 'eng_log.py append --id {existing_id}' for follow-ups or pass --allow-duplicate."
                )

    existing_ids = set(state.get("entries_by_id", {}).keys())
    now = utc_now()
    entry_id = _generate_entry_id(existing_ids)
    slug = sanitize_slug(scrubbed["title"], max_len=60)
    rel_file_path = f"entries/{now.strftime('%Y')}/{now.strftime('%m')}/{entry_id}_{slug}.md"
    entry_abs = store_dir / rel_file_path

    record = {
        "record_type": "entry",
        "id": entry_id,
        "created_at": now.isoformat(),
        "file_path": rel_file_path,
        **scrubbed,
    }

    resolved_links = _resolve_links_for_markdown(
        record.get("links", []), entry_abs, store_dir, state
    )
    markdown_content = render_entry_markdown(record, resolved_links)
    stream_id = resolve_stream_id(args.stream)
    ledger_rel = f"ledgers/{stream_id}.jsonl"
    links_resolved_count = sum(1 for lnk in resolved_links if lnk["resolved"])
    unresolved_links = [lnk["target_id"] for lnk in resolved_links if not lnk["resolved"]]

    if args.dry_run:
        out: Dict[str, Any] = {
            "status": "ok",
            "action": "write",
            "dry_run": True,
            "id": entry_id,
            "file_path": rel_file_path,
            "ledger_path": ledger_rel,
            "redactions_applied": redactions,
            "links_resolved": links_resolved_count,
            "unresolved_links": unresolved_links,
            "auto_harvested_git": auto_git,
            "auto_harvested_semantics": auto_sem,
        }
        if getattr(args, "verbose", False):
            out["markdown_preview"] = markdown_content
            out["ledger_record"] = record
        return out

    ensure_store_initialized(store_dir)
    write_text_atomic(entry_abs, markdown_content)
    append_jsonl_line(store_dir / ledger_rel, record)
    _clean_matching_pending_stub(store_dir, record["actor"].get("conversation_id"))
    new_state = load_ledger_state(store_dir)
    write_compiled_indexes(store_dir, new_state)

    return {
        "status": "ok",
        "action": "write",
        "dry_run": False,
        "id": entry_id,
        "store_dir": str(store_dir),
        "file_path": rel_file_path,
        "ledger_path": ledger_rel,
        "redactions_applied": redactions,
        "links_resolved": links_resolved_count,
        "auto_harvested_git": auto_git,
        "auto_harvested_semantics": auto_sem,
    }


def _validate_addendum_payload(payload: Any) -> Tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {}, ["Addendum payload must be a JSON object."]

    has_content = any(
        bool(payload.get(k))
        for k in (
            "note",
            "summary",
            "belief_revisions",
            "dead_ends",
            "findings",
            "rule_candidates",
            "open_threads",
            "closed_threads",
            "promoted_rules",
            "links",
        )
    )
    if not has_content:
        errors.append(
            "Addendum must contain at least one update (note, findings, dead_ends, belief_revisions, rule_candidates, open_threads, closed_threads, promoted_rules, or links)."
        )

    if payload.get("outcome") is not None:
        _validate_enum(payload["outcome"], OUTCOMES, "outcome", errors)
    if payload.get("verification") is not None:
        _validate_enum(payload["verification"], VERIFICATIONS, "verification", errors)
    if payload.get("confidence") is not None:
        _validate_enum(payload["confidence"], CONFIDENCE_LEVELS, "confidence", errors)
    if payload.get("shelf_life") is not None:
        _validate_enum(payload["shelf_life"], SHELF_LIVES, "shelf_life", errors)

    links = payload.get("links") or []
    if not isinstance(links, list):
        errors.append("'links' must be a list.")
    else:
        for i, lnk in enumerate(links):
            if not isinstance(lnk, dict):
                errors.append(f"links[{i}] must be an object.")
                continue
            _validate_enum(lnk.get("rel"), LINK_RELS, f"links[{i}].rel", errors)
            if not lnk.get("target_id") or not isinstance(lnk.get("target_id"), str):
                errors.append(f"links[{i}].target_id must be a non-empty string.")

    _validate_epistemic_lists(payload, errors, include_closed=True)

    if errors:
        return payload, errors
    return payload, []


def _render_addendum_markdown(
    add_record: Dict[str, Any], resolved_links: List[Dict[str, Any]]
) -> str:
    stamp = add_record["created_at"][:16].replace("T", " ") + " UTC"
    lines = ["", f"## Addendum — {stamp} (`{add_record['id']}`)", ""]
    if add_record.get("note"):
        lines.append(add_record["note"])
        lines.append("")
    status_bits = []
    for fld in ("outcome", "verification", "confidence", "shelf_life"):
        if add_record.get(fld):
            status_bits.append(f"**{fld.replace('_', ' ').title()}:** `{add_record[fld]}`")
    if status_bits:
        lines.append("- " + " | ".join(status_bits))
    for br in add_record.get("belief_revisions") or []:
        if isinstance(br, dict):
            lines.append(
                f"- **Belief Revision:** Assumed *{br.get('assumed', '')}* → "
                f"Contradicted by *{br.get('contradicted_by', '')}* → "
                f"Revised: *{br.get('revised_model', '')}*"
            )
        else:
            lines.append(f"- **Belief Revision:** {br}")
    for de in add_record.get("dead_ends") or []:
        if isinstance(de, dict):
            sig = f" (`{de['error_signature']}`)" if de.get("error_signature") else ""
            lines.append(f"- **Dead End:** {de.get('hypothesis', '')}{sig}: {de.get('why_failed', '')}")
        else:
            lines.append(f"- **Dead End:** {de}")
    for fn in add_record.get("findings") or []:
        if isinstance(fn, dict):
            lines.append(f"- **Finding:** {fn.get('claim', '')}")
        else:
            lines.append(f"- **Finding:** {fn}")
    for rc in add_record.get("rule_candidates") or []:
        if isinstance(rc, dict):
            lines.append(f"- **Rule Candidate [`{rc.get('scope', 'general')}`]:** {rc.get('rule', '')}")
        else:
            lines.append(f"- **Rule Candidate:** {rc}")
    for ct in add_record.get("closed_threads") or []:
        lines.append(f"- [x] Closed thread: {ct}")
    for pr in add_record.get("promoted_rules") or []:
        lines.append(f"- [x] Promoted rule: {pr}")
    for ot in add_record.get("open_threads") or []:
        lines.append(f"- [ ] {ot}")
    for lnk in resolved_links:
        if lnk["resolved"]:
            lines.append(
                f"- **Link (`{lnk['rel']}`):** [{lnk['target_title']}]({lnk['rel_path']}) (`{lnk['target_id']}`)"
            )
        else:
            lines.append(f"- **Link (`{lnk['rel']}`):** `{lnk['target_id']}` *(unresolved)*")
    lines.append("")
    return "\n".join(lines)


def cmd_append(args: argparse.Namespace) -> Dict[str, Any]:
    store_dir = resolve_store_dir(args.dir)
    state = load_ledger_state(store_dir)
    target = state["entries_by_id"].get(args.id)
    if not target:
        raise FileNotFoundError(f"Entry ID {args.id!r} not found in {store_dir / 'ledgers'}")

    entry_abs = store_dir / target["file_path"]
    if not entry_abs.is_file():
        raise FileNotFoundError(f"Target Markdown file missing: {entry_abs}")

    raw_payload = _read_json_input(args.input)
    validated, val_errors = _validate_addendum_payload(raw_payload)
    if val_errors:
        raise ValueError("Addendum validation failed:\n- " + "\n- ".join(val_errors))

    scrubbed, redactions = scrub_value(validated)
    if redactions > 0:
        sys.stderr.write(f"Secret scrubber redacted {redactions} sensitive token(s).\n")

    now = utc_now()
    add_id = _generate_entry_id(set(state["entries_by_id"].keys()))
    add_record = {
        "record_type": "addendum",
        "schema_version": SCHEMA_VERSION,
        "id": add_id,
        "target_id": args.id,
        "created_at": now.isoformat(),
        "note": scrubbed.get("note") or scrubbed.get("summary"),
        "outcome": scrubbed.get("outcome"),
        "verification": scrubbed.get("verification"),
        "confidence": scrubbed.get("confidence"),
        "shelf_life": scrubbed.get("shelf_life"),
        "belief_revisions": scrubbed.get("belief_revisions") or [],
        "dead_ends": scrubbed.get("dead_ends") or [],
        "findings": scrubbed.get("findings") or [],
        "rule_candidates": scrubbed.get("rule_candidates") or [],
        "open_threads": scrubbed.get("open_threads") or [],
        "closed_threads": scrubbed.get("closed_threads") or [],
        "promoted_rules": scrubbed.get("promoted_rules") or [],
        "links": scrubbed.get("links") or [],
    }

    resolved_links = _resolve_links_for_markdown(
        add_record["links"], entry_abs, store_dir, state
    )
    addendum_md = _render_addendum_markdown(add_record, resolved_links)
    stream_id = resolve_stream_id(args.stream)
    ledger_rel = f"ledgers/{stream_id}.jsonl"
    links_resolved_count = sum(1 for lnk in resolved_links if lnk["resolved"])
    unresolved_links = [lnk["target_id"] for lnk in resolved_links if not lnk["resolved"]]

    if args.dry_run:
        out: Dict[str, Any] = {
            "status": "ok",
            "action": "append",
            "dry_run": True,
            "addendum_id": add_id,
            "target_id": args.id,
            "redactions_applied": redactions,
            "links_resolved": links_resolved_count,
            "unresolved_links": unresolved_links,
        }
        if getattr(args, "verbose", False):
            out["markdown_addition"] = addendum_md
            out["ledger_record"] = add_record
        return out

    existing_md = entry_abs.read_text(encoding="utf-8").rstrip() + "\n"
    write_text_atomic(entry_abs, existing_md + addendum_md)
    append_jsonl_line(store_dir / ledger_rel, add_record)
    new_state = load_ledger_state(store_dir)
    write_compiled_indexes(store_dir, new_state)

    return {
        "status": "ok",
        "action": "append",
        "dry_run": False,
        "addendum_id": add_id,
        "target_id": args.id,
        "file_path": target["file_path"],
        "ledger_path": ledger_rel,
        "redactions_applied": redactions,
    }


def cmd_rebuild_index(args: argparse.Namespace) -> Dict[str, Any]:
    store_dir = resolve_store_dir(args.dir)
    ensure_store_initialized(store_dir)
    state = load_ledger_state(store_dir)
    write_compiled_indexes(store_dir, state)
    return {
        "status": "ok",
        "action": "rebuild-index",
        "store_dir": str(store_dir),
        "entries_indexed": len(state["ordered_entries"]),
        "addenda_folded": len(state["addenda"]),
    }


def cmd_graph(args: argparse.Namespace) -> Any:
    """Traverse bidirectional graph links (outgoing + incoming) from an entry up to N hops."""
    store_dir = resolve_store_dir(args.dir)
    state = load_ledger_state(store_dir) if store_dir.exists() else {"entries_by_id": {}, "cited_by": {}}
    entries_by_id = state.get("entries_by_id", {})
    cited_by = state.get("cited_by", {})

    anchor_id = args.id
    if anchor_id not in entries_by_id:
        raise FileNotFoundError(f"Entry ID {anchor_id!r} not found in {store_dir / 'ledgers'}")

    depth = max(1, min(4, int(args.depth)))
    visited_hop: Dict[str, int] = {anchor_id: 0}
    queue: deque = deque([(anchor_id, 0)])
    edges_seen: set = set()
    edges: List[Dict[str, Any]] = []

    def _add_edge(src_id: str, rel: str, tgt_id: str, note: str = "") -> None:
        key = (src_id, rel, tgt_id)
        if key in edges_seen:
            return
        edges_seen.add(key)
        edges.append({"source_id": src_id, "rel": rel, "target_id": tgt_id, "note": note})

    while queue:
        curr_id, hop = queue.popleft()
        curr_ent = entries_by_id.get(curr_id)
        if not curr_ent or hop >= depth:
            continue

        for lnk in curr_ent.get("links") or []:
            if not isinstance(lnk, dict):
                continue
            tgt = lnk.get("target_id")
            rel = lnk.get("rel") or ""
            note = lnk.get("note") or ""
            if not tgt:
                continue
            _add_edge(curr_id, rel, tgt, note)
            if tgt in entries_by_id and tgt not in visited_hop:
                visited_hop[tgt] = hop + 1
                queue.append((tgt, hop + 1))

        for ref in cited_by.get(curr_id, []):
            src_id = ref.get("source_id")
            rel = ref.get("rel") or ""
            if not src_id:
                continue
            note = ""
            src_ent = entries_by_id.get(src_id)
            if src_ent:
                for slnk in src_ent.get("links") or []:
                    if isinstance(slnk, dict) and slnk.get("target_id") == curr_id and slnk.get("rel") == rel:
                        note = slnk.get("note") or ""
                        break
            _add_edge(src_id, rel, curr_id, note)
            if src_id in entries_by_id and src_id not in visited_hop:
                visited_hop[src_id] = hop + 1
                queue.append((src_id, hop + 1))

    nodes: List[Dict[str, Any]] = []
    for eid, hop in sorted(visited_hop.items(), key=lambda item: (item[1], item[0])):
        ent = entries_by_id[eid]
        nodes.append(
            {
                "id": eid,
                "hop": hop,
                "title": ent.get("title"),
                "project": ent.get("project"),
                "file_path": ent.get("file_path"),
                "shelf_life": ent.get("shelf_life"),
                "superseded_by": ent.get("_superseded_by"),
                "summary": _truncate_text(ent.get("summary") or "", 180),
            }
        )

    if args.format == "markdown":
        anchor_ent = entries_by_id[anchor_id]
        lines = [
            f"### Graph Neighborhood for `{anchor_id}` ({anchor_ent.get('title')}) [depth={depth}]",
            "",
            f"- **Nodes:** {len(nodes)} | **Edges:** {len(edges)}",
            "",
            "#### Nodes",
        ]
        for n in nodes:
            sup = f" *(superseded by `{n['superseded_by']}`)*" if n.get("superseded_by") else ""
            fpath = n.get("file_path") or ""
            link_md = f"[{n['title']}]({fpath})" if fpath else n["title"]
            lines.append(
                f"- [hop {n['hop']}] `{n['id']}` (`{n['project']}`, `{n['shelf_life']}`) "
                f"{link_md}{sup}: {n['summary']}"
            )
        lines.append("")
        lines.append("#### Edges")
        if edges:
            for ed in edges:
                note_s = f" — {ed['note']}" if ed.get("note") else ""
                lines.append(f"- `{ed['source_id']}` --[`{ed['rel']}`]--> `{ed['target_id']}`{note_s}")
        else:
            lines.append("- None.")
        return "\n".join(lines) + "\n"

    return {
        "status": "ok",
        "action": "graph",
        "anchor_id": anchor_id,
        "depth": depth,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def cmd_query(args: argparse.Namespace) -> Any:
    store_dir = resolve_store_dir(args.dir)
    state = load_ledger_state(store_dir) if store_dir.exists() else {"ordered_entries": []}
    query_tokens = _tokenize(args.text or "")

    matches: List[Tuple[float, Dict[str, Any]]] = []
    for ent in state.get("ordered_entries", []):
        if args.exclude_superseded and ent.get("_superseded_by"):
            continue
        if args.project and (ent.get("project") or "").lower() != args.project.lower():
            continue
        ctx = ent.get("context") or {}
        if args.tech and args.tech.lower() not in {t.lower() for t in ctx.get("technologies", [])}:
            continue
        if args.concept and args.concept.lower() not in {c.lower() for c in ctx.get("concepts", [])}:
            continue
        if args.domain and args.domain.lower() not in {d.lower() for d in ctx.get("domains", [])}:
            continue
        if args.outcome and ent.get("outcome") != args.outcome:
            continue
        if args.shape and ent.get("session_shape") != args.shape:
            continue
        if args.shelf_life and ent.get("shelf_life") != args.shelf_life:
            continue
        m = ent.get("metrics") or {}
        if args.min_friction is not None:
            fr = m.get("friction")
            if fr is None or fr < args.min_friction:
                continue

        score = 1.0 + 0.5 * ent.get("_incoming_citations", 0)
        if ent.get("shelf_life") == "evergreen":
            score += 1.0
        if query_tokens:
            blob = _entry_searchable_blob(ent)
            hits = sum(1 for t in query_tokens if t in blob)
            if hits == 0:
                continue
            score += 2.0 * hits
        matches.append((score, ent))

    matches.sort(key=lambda item: (item[0], item[1].get("created_at", "")), reverse=True)
    selected = [ent for _, ent in matches[: args.limit]]

    if args.format == "markdown":
        if not selected:
            return "_No matching engineering log entries found._\n"
        lines = [f"### Engineering Log Recall ({len(selected)} match(es))", ""]
        for ent in selected:
            sup = f" *(superseded by `{ent['_superseded_by']}`)*" if ent.get("_superseded_by") else ""
            lines.append(
                f"- **`{ent['id']}`** [{ent.get('project')}] [{ent.get('title')}]({ent.get('file_path')}) "
                f"(`{ent.get('outcome')}`, `{ent.get('shelf_life')}`){sup}: {ent.get('summary')}"
            )
        return "\n".join(lines) + "\n"

    clean_results = []
    for ent in selected:
        clean_results.append(
            {
                "id": ent["id"],
                "created_at": ent.get("created_at"),
                "project": ent.get("project"),
                "title": ent.get("title"),
                "summary": ent.get("summary"),
                "file_path": ent.get("file_path"),
                "outcome": ent.get("outcome"),
                "session_shape": ent.get("session_shape"),
                "shelf_life": ent.get("shelf_life"),
                "superseded_by": ent.get("_superseded_by"),
                "incoming_citations": ent.get("_incoming_citations", 0),
                "friction": (ent.get("metrics") or {}).get("friction"),
                "value": (ent.get("metrics") or {}).get("value"),
            }
        )
    return {"status": "ok", "action": "query", "count": len(clean_results), "results": clean_results}


def _group_stats(entries: List[Dict[str, Any]], key_fn) -> Dict[str, Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ent in entries:
        buckets[str(key_fn(ent) or "unspecified")].append(ent)
    out = {}
    for k in sorted(buckets):
        items = buckets[k]
        fr = [
            e["metrics"]["friction"]
            for e in items
            if isinstance(e.get("metrics"), dict) and e["metrics"].get("friction") is not None
        ]
        vl = [
            e["metrics"]["value"]
            for e in items
            if isinstance(e.get("metrics"), dict) and e["metrics"].get("value") is not None
        ]
        out[k] = {
            "count": len(items),
            "mean_friction": _mean(fr),
            "mean_value": _mean(vl),
        }
    return out


def cmd_stats(args: argparse.Namespace) -> Any:
    store_dir = resolve_store_dir(args.dir)
    state = load_ledger_state(store_dir) if store_dir.exists() else {"ordered_entries": [], "addenda": []}
    tools = detect_tools()

    entries = list(state.get("ordered_entries", []))
    if args.project:
        entries = [e for e in entries if (e.get("project") or "").lower() == args.project.lower()]
    if args.since:
        entries = [e for e in entries if (e.get("created_at") or "")[:10] >= args.since]

    total = len(entries)
    frictions = [
        e["metrics"]["friction"]
        for e in entries
        if isinstance(e.get("metrics"), dict) and e["metrics"].get("friction") is not None
    ]
    values = [
        e["metrics"]["value"]
        for e in entries
        if isinstance(e.get("metrics"), dict) and e["metrics"].get("value") is not None
    ]

    fm_counter: Counter = Counter()
    cat_frictions: Dict[str, List[int]] = defaultdict(list)
    cat_counts: Counter = Counter()
    error_sig_entries: Dict[str, List[str]] = defaultdict(list)
    high_friction_tech: Dict[str, List[str]] = defaultdict(list)
    sem_entity_types: Counter = Counter()
    inspect_risks: Counter = Counter()

    for ent in entries:
        tel = ent.get("telemetry") or {}
        for fm in tel.get("agent_failure_modes", []) or []:
            fm_counter[fm] += 1
        cat = tel.get("unsticking_catalyst") or "none"
        cat_counts[cat] += 1
        fr_val = (ent.get("metrics") or {}).get("friction")
        if fr_val is not None:
            cat_frictions[cat].append(fr_val)
            if fr_val >= 4:
                for t in (ent.get("context") or {}).get("technologies", []):
                    high_friction_tech[t.lower()].append(ent["id"])
        for de in ent.get("dead_ends", []) or []:
            if isinstance(de, dict) and de.get("error_signature"):
                sig = de["error_signature"].strip()
                if sig:
                    error_sig_entries[sig].append(ent["id"])
        sem_info = ent.get("code_semantics") or {}
        if isinstance(sem_info, dict):
            for e_item in (sem_info.get("sem") or {}).get("entities", []) or []:
                if isinstance(e_item, dict) and e_item.get("entity_type"):
                    sem_entity_types[e_item["entity_type"]] += 1
            ins_info = sem_info.get("inspect") or {}
            if isinstance(ins_info, dict) and ins_info.get("risk_tier"):
                inspect_risks[str(ins_info["risk_tier"])] += 1

    # Graph-emergent metrics
    most_cited = sorted(
        [
            {
                "id": e["id"],
                "title": e.get("title"),
                "project": e.get("project"),
                "incoming_citations": e.get("_incoming_citations", 0),
                "superseded_by": e.get("_superseded_by"),
            }
            for e in entries
            if e.get("_incoming_citations", 0) > 0
        ],
        key=lambda x: x["incoming_citations"],
        reverse=True,
    )[:5]

    same_root_clusters = []
    for eid, refs in (state.get("cited_by") or {}).items():
        sr_sources = [r["source_id"] for r in refs if r.get("rel") == "same_root_cause"]
        if sr_sources:
            same_root_clusters.append(
                {"anchor_id": eid, "linked_entries": [eid] + sr_sources, "count": 1 + len(sr_sources)}
            )

    deja_vu = {
        "same_root_cause_clusters": same_root_clusters,
        "repeated_error_signatures": [
            {"signature": sig, "count": len(ids), "entry_ids": ids}
            for sig, ids in sorted(error_sig_entries.items(), key=lambda kv: len(kv[1]), reverse=True)
            if len(ids) >= 2
        ],
        "high_friction_technologies": [
            {"technology": tech, "count": len(ids), "entry_ids": ids}
            for tech, ids in sorted(high_friction_tech.items(), key=lambda kv: len(kv[1]), reverse=True)
            if len(ids) >= 2
        ],
    }

    supersedes_total = sum(
        1
        for e in entries
        for lnk in (e.get("links") or [])
        if isinstance(lnk, dict) and lnk.get("rel") == "supersedes"
    )

    duckdb_sql = (
        f"duckdb -dark-mode -c \"SELECT id, project, outcome, session_shape, "
        f"metrics.friction, metrics.value FROM read_json_auto('{store_dir}/ledgers/**/*.jsonl') "
        f"WHERE record_type = 'entry';\""
    )

    report = {
        "status": "ok",
        "action": "stats",
        "store_dir": str(store_dir),
        "overview": {
            "total_entries": total,
            "total_addenda": len(state.get("addenda", [])),
            "projects_count": len({e.get("project") for e in entries if e.get("project")}),
            "mean_friction": _mean(frictions),
            "mean_value": _mean(values),
            "total_belief_revisions": sum(
                len(e.get("belief_revisions") or []) for e in entries
            ),
            "total_dead_ends": sum(len(e.get("dead_ends") or []) for e in entries),
            "total_rule_candidates": sum(len(e.get("rule_candidates") or []) for e in entries),
            "unresolved_open_threads": sum(len(e.get("open_threads") or []) for e in entries),
        },
        "distributions": {
            "by_outcome": _group_stats(entries, lambda e: e.get("outcome")),
            "by_session_shape": _group_stats(entries, lambda e: e.get("session_shape")),
            "by_verification": _group_stats(entries, lambda e: e.get("verification")),
            "by_agent_impact": _group_stats(
                entries, lambda e: (e.get("telemetry") or {}).get("agent_impact")
            ),
            "by_model": _group_stats(
                entries, lambda e: (e.get("actor") or {}).get("model")
            ),
            "by_harness": _group_stats(
                entries, lambda e: (e.get("actor") or {}).get("harness")
            ),
            "by_project": _group_stats(entries, lambda e: e.get("project")),
            "by_shelf_life": _group_stats(entries, lambda e: e.get("shelf_life")),
        },
        "top_failure_modes": [
            {
                "mode": m,
                "count": c,
                "pct": round(100.0 * c / total, 1) if total else 0.0,
            }
            for m, c in fm_counter.most_common()
        ],
        "top_catalysts": [
            {
                "catalyst": cat,
                "count": c,
                "mean_friction": _mean(cat_frictions[cat]),
            }
            for cat, c in cat_counts.most_common()
        ],
        "graph_metrics": {
            "most_cited": most_cited,
            "knowledge_churn": {"supersedes_edges": supersedes_total},
            "deja_vu_clusters": deja_vu,
        },
        "code_semantics_summary": {
            "sem_entity_types": dict(sem_entity_types),
            "inspect_risk_tiers": dict(inspect_risks),
        },
        "tools": tools,
        "duckdb_query": duckdb_sql if tools.get("duckdb") else None,
    }

    if args.format == "markdown":
        ov = report["overview"]
        lines = [
            f"# Engineering Log Stats ({ov['total_entries']} entries across {ov['projects_count']} projects)",
            "",
            f"- **Mean Friction:** {ov['mean_friction']} | **Mean Value:** {ov['mean_value']}",
            f"- **Belief Revisions:** {ov['total_belief_revisions']} | **Dead Ends:** {ov['total_dead_ends']} | "
            f"**Rule Candidates:** {ov['total_rule_candidates']} | **Open Threads:** {ov['unresolved_open_threads']}",
            "",
            "## Outcomes & Shapes",
        ]
        for k, v in report["distributions"]["by_outcome"].items():
            lines.append(
                f"- Outcome `{k}`: {v['count']} (friction={v['mean_friction']}, value={v['mean_value']})"
            )
        lines.append("")
        lines.append("## Agent Failure Modes & Unsticking Catalysts")
        if report["top_failure_modes"]:
            for fm in report["top_failure_modes"]:
                lines.append(f"- Failure `{fm['mode']}`: {fm['count']} ({fm['pct']}%)")
        else:
            lines.append("- Failure modes: none recorded")
        for cat in report["top_catalysts"]:
            lines.append(
                f"- Catalyst `{cat['catalyst']}`: {cat['count']} (mean_friction={cat['mean_friction']})"
            )
        lines.append("")
        lines.append("## Graph & Déjà Vu Signals")
        if most_cited:
            for mc in most_cited:
                lines.append(
                    f"- Most Cited: `{mc['id']}` ({mc['title']}) — {mc['incoming_citations']} citation(s)"
                )
        else:
            lines.append("- Most Cited: none yet")
        lines.append(f"- Knowledge Churn (`supersedes` edges): {supersedes_total}")
        lines.append(
            f"- Déjà Vu: {len(same_root_clusters)} `same_root_cause` clusters, "
            f"{len(deja_vu['repeated_error_signatures'])} repeated error signatures, "
            f"{len(deja_vu['high_friction_technologies'])} high-friction recurring techs"
        )
        if report["duckdb_query"]:
            lines.extend(["", "## DuckDB One-Liner", f"```bash\n{report['duckdb_query']}\n```"])
        return "\n".join(lines) + "\n"

    return report


def cmd_validate(args: argparse.Namespace) -> Tuple[Dict[str, Any], int]:
    store_dir = resolve_store_dir(args.dir)
    errors: List[str] = []
    warnings: List[str] = []

    if not store_dir.is_dir():
        return (
            {"valid": False, "errors": [f"Store directory not found: {store_dir}"], "warnings": []},
            1,
        )

    state = load_ledger_state(store_dir)
    for perr in state["parse_errors"]:
        errors.append(f"{perr['file']}:{perr['line']}: {perr['error']}")

    for orph in state["orphan_addenda"]:
        errors.append(
            f"Orphan addendum {orph.get('id')} references missing entry {orph.get('target_id')!r}."
        )

    all_ids = set(state["entries_by_id"].keys())
    for eid, ent in state["entries_by_id"].items():
        if ent.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"Entry {eid} has invalid schema_version: {ent.get('schema_version')!r}")
        _validate_enum(ent.get("outcome"), OUTCOMES, f"{eid}.outcome", errors)
        _validate_enum(ent.get("session_shape"), SESSION_SHAPES, f"{eid}.session_shape", errors)
        _validate_enum(ent.get("confidence"), CONFIDENCE_LEVELS, f"{eid}.confidence", errors)
        _validate_enum(ent.get("shelf_life"), SHELF_LIVES, f"{eid}.shelf_life", errors)
        _validate_enum(ent.get("visibility"), VISIBILITIES, f"{eid}.visibility", errors)
        _validate_enum(ent.get("verification"), VERIFICATIONS, f"{eid}.verification", errors)

        fpath = ent.get("file_path")
        if not fpath or not (store_dir / fpath).is_file():
            errors.append(f"Entry {eid} missing Markdown file: {fpath}")
        else:
            md_text = (store_dir / fpath).read_text(encoding="utf-8")
            _, leaks = scrub_text(md_text)
            if leaks > 0:
                errors.append(f"Potential unredacted secret detected in {fpath} ({leaks} match(es)).")

        _, rec_leaks = scrub_value(ent)
        if rec_leaks > 0:
            errors.append(f"Potential unredacted secret detected in JSONL record {eid} ({rec_leaks} match(es)).")

        for lnk in ent.get("links", []) or []:
            if isinstance(lnk, dict):
                tid = lnk.get("target_id")
                if tid and tid not in all_ids:
                    warnings.append(f"Entry {eid} has unresolved graph link target_id={tid!r}.")

    index_path = store_dir / "INDEX.md"
    if not index_path.is_file():
        errors.append("Missing INDEX.md in store root.")
    else:
        expected_index = compile_index_markdown(state)
        if index_path.read_text(encoding="utf-8") != expected_index:
            errors.append("INDEX.md is out of sync with ledgers. Run rebuild-index.")

    valid = len(errors) == 0
    return (
        {
            "valid": valid,
            "store_dir": str(store_dir),
            "entries_checked": len(all_ids),
            "ledger_files": state["ledger_files"],
            "errors": errors,
            "warnings": warnings,
        },
        0 if valid else 1,
    )


def _read_hook_stdin() -> Dict[str, Any]:
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def cmd_hook(args: argparse.Namespace) -> Dict[str, Any]:
    store_dir = resolve_store_dir(args.dir)
    payload = _read_hook_stdin()

    if args.mode == "pending-list":
        stubs = list_pending_stubs(store_dir) if store_dir.exists() else []
        return {"status": "ok", "count": len(stubs), "pending": stubs}

    if args.mode == "agy-start":
        if not store_dir.exists():
            return {}
        cwd_raw = payload.get("cwd") or (
            payload.get("workspacePaths", [None])[0]
            if isinstance(payload.get("workspacePaths"), list) and payload.get("workspacePaths")
            else None
        )
        cwd = Path(cwd_raw).expanduser().resolve() if cwd_raw else Path.cwd()
        git_info = harvest_git_info(cwd)
        proj_hint = git_info.get("repo") or cwd.name
        state = load_ledger_state(store_dir)
        proj_low = (proj_hint or "").strip().lower()
        active: List[Dict[str, Any]] = []
        if proj_low:
            for ent in state.get("ordered_entries", []):
                if ent.get("_superseded_by"):
                    continue
                if ent.get("shelf_life") not in ("evergreen", "version-bound"):
                    continue
                ent_proj = (ent.get("project") or "").strip().lower()
                ent_repo = ((ent.get("git") or {}).get("repo") or "").strip().lower()
                if proj_low == ent_proj or proj_low == ent_repo:
                    active.append(ent)
                    if len(active) >= 3:
                        break
        pending = list_pending_stubs(store_dir)
        global_rules: List[Tuple[str, str]] = []
        if getattr(args, "include_global_rules", False):
            seen_rules = set()
            for ent in state.get("ordered_entries", []):
                if ent.get("_superseded_by"):
                    continue
                for rc in ent.get("rule_candidates") or []:
                    if isinstance(rc, dict):
                        scope = str(rc.get("scope") or "").strip().lower()
                        rule_txt = str(rc.get("rule") or "").strip()
                    else:
                        continue
                    if scope == "global" and rule_txt:
                        key = rule_txt.lower()
                        if key not in seen_rules:
                            seen_rules.add(key)
                            global_rules.append((ent["id"], rule_txt))
                            if len(global_rules) >= 3:
                                break
                if len(global_rules) >= 3:
                    break

        if not active and not pending and not global_rules:
            return {}

        parts = []
        if active:
            parts.append(f"[engineering-log] Prior learnings for `{proj_hint}`:")
            for c in active:
                parts.append(f"- [{c['id']}] ({c['shelf_life']}) {c['title']}: {c['summary']}")
        if global_rules:
            parts.append("[engineering-log] Global guardrails:")
            for eid, rtxt in global_rules:
                parts.append(f"- [{eid}] {rtxt}")
        if pending:
            parts.append(
                f"[engineering-log] {len(pending)} unlogged session bookmark(s) in pending/. "
                f"Run `/engineering-log` or `eng_log.py hook --mode pending-list` if worth capturing."
            )
        msg = "\n".join(parts)[:1450]
        return {"injectSteps": [{"systemMessage": {"systemMessage": msg}}]}

    if args.mode == "agy-nudge":
        conv_id = str(payload.get("conversationId") or "").strip()
        steps_raw = payload.get("initialNumSteps")
        if steps_raw is None:
            steps_raw = payload.get("invocationNum", 0)
        try:
            steps = int(steps_raw)
        except Exception:
            steps = 0

        if not conv_id or steps < args.min_steps:
            return {}

        if store_dir.exists():
            state = load_ledger_state(store_dir)
            for ent in state.get("ordered_entries", []):
                if (ent.get("actor") or {}).get("conversation_id") == conv_id:
                    return {}

        nudged_file = store_dir / "pending" / ".nudged.json"
        nudged_ids: List[str] = []
        if nudged_file.is_file():
            try:
                loaded = json.loads(nudged_file.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    nudged_ids = [str(x) for x in loaded]
            except Exception:
                nudged_ids = []

        if conv_id in nudged_ids:
            return {}

        nudged_ids.append(conv_id)
        write_text_atomic(nudged_file, json.dumps(nudged_ids[-200:], indent=2))
        reminder = (
            f"**Engineering Log Reminder:** Session reached {steps} steps. "
            f"Run `/engineering-log` before ending to preserve dead ends, breakthroughs, and lessons learned."
        )
        return {
            "injectSteps": [
                {
                    "systemMessage": {
                        "systemMessage": "",
                        "metadata": {"user_markdown": reminder},
                    }
                }
            ],
            "terminationBehavior": "",
        }

    if args.mode == "session-end":
        conv_id = str(
            payload.get("conversationId")
            or payload.get("session_id")
            or f"session-{utc_now().strftime('%Y%m%d-%H%M')}-{secrets.token_hex(2)}"
        )
        if store_dir.exists():
            state = load_ledger_state(store_dir)
            for ent in state.get("ordered_entries", []):
                if (ent.get("actor") or {}).get("conversation_id") == conv_id:
                    return {}

        ensure_store_initialized(store_dir)
        cwd_raw = payload.get("cwd") or (
            payload.get("workspacePaths", [None])[0]
            if isinstance(payload.get("workspacePaths"), list) and payload.get("workspacePaths")
            else None
        )
        cwd = Path(cwd_raw).expanduser().resolve() if cwd_raw else Path.cwd()
        git_info = harvest_git_info(cwd)
        stub = {
            "conversation_id": conv_id,
            "created_at": utc_now().isoformat(),
            "cwd": str(cwd),
            "repo": git_info.get("repo"),
            "branch": git_info.get("branch"),
            "head_commit": git_info.get("head_commit"),
            "transcript_path": payload.get("transcriptPath") or payload.get("transcript_path"),
            "model": payload.get("modelName") or payload.get("model"),
            "last_user_input": payload.get("lastUserInput") or payload.get("prompt"),
        }
        scrubbed_stub, _ = scrub_value(stub)
        stub_name = sanitize_slug(conv_id, max_len=64) + ".json"
        write_text_atomic(
            store_dir / "pending" / stub_name,
            json.dumps(scrubbed_stub, indent=2, ensure_ascii=False),
        )
        return {}

    raise ValueError(f"Unknown hook mode: {args.mode}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Engineering Log CLI — epistemic flight recorder & second-brain ledger.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/eng_log.py context --cwd . --query \"oauth race\" --tech typescript\n"
            "  python3 scripts/eng_log.py write --cwd . --dry-run --input payload.json\n"
            "  python3 scripts/eng_log.py query --project my-app --exclude-superseded --format markdown\n"
            "  python3 scripts/eng_log.py stats --format markdown"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Idempotently initialize engineering log store.")
    p_init.add_argument("--dir", default=None, help="Override store root (default: $ENGINEERING_LOG_DIR or ~/engineering-log)")

    p_ctx = sub.add_parser(
        "context",
        help="Harvest workspace git/semantic context and find related entries.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 scripts/eng_log.py context --cwd . --query \"timeout\" --tech python,redis",
    )
    p_ctx.add_argument("--dir", default=None, help="Override store root")
    p_ctx.add_argument("--cwd", default=".", help="Workspace directory to inspect")
    p_ctx.add_argument("--query", default="", help="Free-text topic or error keywords")
    p_ctx.add_argument("--tech", default="", help="Comma-separated technologies")
    p_ctx.add_argument("--concepts", default="", help="Comma-separated concepts")
    p_ctx.add_argument("--top", type=int, default=5, help="Max related entries to return")

    p_wr = sub.add_parser(
        "write",
        help="Validate, scrub secrets, write Markdown entry, and append JSONL ledger.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 scripts/eng_log.py write --cwd . --dry-run --input -\n"
            "  python3 scripts/eng_log.py write --cwd . --input payload.json"
        ),
    )
    p_wr.add_argument("--dir", default=None, help="Override store root")
    p_wr.add_argument("--input", default="-", help="JSON payload file path or '-' for stdin")
    p_wr.add_argument("--cwd", default=None, help="Workspace path for auto-harvesting git/code_semantics when omitted from JSON")
    p_wr.add_argument("--no-auto-harvest", action="store_true", help="Disable deterministic git/code_semantics harvesting in write")
    p_wr.add_argument("--stream", default=None, help="Override ledger shard ID")
    p_wr.add_argument("--allow-duplicate", action="store_true", help="Allow multiple entries for the same actor.conversation_id")
    p_wr.add_argument("--dry-run", action="store_true", help="Validate and preview without modifying disk")
    p_wr.add_argument("--verbose", action="store_true", help="Include markdown_preview and ledger_record in --dry-run output")

    p_app = sub.add_parser(
        "append",
        help="Append an immutable addendum to an existing entry.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 scripts/eng_log.py append --id 20261122-1906-1a11 --dry-run --input addendum.json",
    )
    p_app.add_argument("--id", required=True, help="Target entry ID")
    p_app.add_argument("--dir", default=None, help="Override store root")
    p_app.add_argument("--input", default="-", help="Addendum JSON payload path or '-' for stdin")
    p_app.add_argument("--stream", default=None, help="Override ledger shard ID")
    p_app.add_argument("--dry-run", action="store_true", help="Validate and preview without modifying disk")
    p_app.add_argument("--verbose", action="store_true", help="Include markdown_addition and ledger_record in --dry-run output")

    p_idx = sub.add_parser("rebuild-index", help="Deterministically recompile INDEX.md from all ledger shards.")
    p_idx.add_argument("--dir", default=None, help="Override store root")

    p_gr = sub.add_parser(
        "graph",
        help="Traverse bidirectional graph links around an entry up to N hops.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 scripts/eng_log.py graph --id 20261122-1807-a1a6 --depth 2 --format markdown",
    )
    p_gr.add_argument("--id", required=True, help="Anchor entry ID")
    p_gr.add_argument("--depth", type=int, default=2, help="Traversal hop depth 1..4 (default: 2)")
    p_gr.add_argument("--dir", default=None, help="Override store root")
    p_gr.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")

    p_q = sub.add_parser(
        "query",
        help="Search and filter entries across sharded ledgers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 scripts/eng_log.py query --tech pihole --exclude-superseded --format markdown",
    )
    p_q.add_argument("--dir", default=None, help="Override store root")
    p_q.add_argument("--project", default=None, help="Filter by project slug")
    p_q.add_argument("--tech", default=None, help="Filter by technology")
    p_q.add_argument("--concept", default=None, help="Filter by concept")
    p_q.add_argument("--domain", default=None, help="Filter by domain")
    p_q.add_argument("--outcome", choices=OUTCOMES, default=None, help="Filter by outcome")
    p_q.add_argument("--shape", choices=SESSION_SHAPES, default=None, help="Filter by session shape")
    p_q.add_argument("--min-friction", type=int, default=None, help="Filter friction >= N")
    p_q.add_argument("--shelf-life", choices=SHELF_LIVES, default=None, help="Filter by shelf life")
    p_q.add_argument("--text", default=None, help="Free-text search terms")
    p_q.add_argument("--exclude-superseded", action="store_true", help="Exclude entries superseded by newer entries")
    p_q.add_argument("--limit", type=int, default=10, help="Max results")
    p_q.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")

    p_st = sub.add_parser(
        "stats",
        help="Compute cross-project metrics, telemetry, and graph insights.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 scripts/eng_log.py stats --since 2026-11-01 --format markdown",
    )
    p_st.add_argument("--dir", default=None, help="Override store root")
    p_st.add_argument("--project", default=None, help="Filter by project slug")
    p_st.add_argument("--since", default=None, help="Filter created_at >= YYYY-MM-DD")
    p_st.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")

    p_val = sub.add_parser("validate", help="Audit ledgers, links, secrets, and INDEX.md integrity.")
    p_val.add_argument("--dir", default=None, help="Override store root")

    p_hk = sub.add_parser("hook", help="Execute lifecycle hook mode (reads stdin JSON, writes stdout JSON).")
    p_hk.add_argument("--dir", default=None, help="Override store root")
    p_hk.add_argument(
        "--mode",
        required=True,
        choices=("agy-start", "agy-nudge", "session-end", "pending-list"),
        help="Hook execution mode",
    )
    p_hk.add_argument("--min-steps", type=int, default=15, help="Minimum step count for agy-nudge")
    p_hk.add_argument("--include-global-rules", action="store_true", help="Also inject up to 3 active scope=global rule_candidates in agy-start")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "init":
            res = cmd_init(args)
        elif args.command == "context":
            res = cmd_context(args)
        elif args.command == "write":
            res = cmd_write(args)
        elif args.command == "append":
            res = cmd_append(args)
        elif args.command == "rebuild-index":
            res = cmd_rebuild_index(args)
        elif args.command == "graph":
            res = cmd_graph(args)
        elif args.command == "query":
            res = cmd_query(args)
        elif args.command == "stats":
            res = cmd_stats(args)
        elif args.command == "validate":
            res, exit_code = cmd_validate(args)
            print(json.dumps(res, indent=2, ensure_ascii=False))
            sys.exit(exit_code)
        elif args.command == "hook":
            res = cmd_hook(args)
        else:
            parser.print_help()
            sys.exit(1)

        if isinstance(res, str):
            sys.stdout.write(res)
        else:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        sys.exit(0)

    except Exception as exc:
        sys.stderr.write(f"Error ({args.command}): {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
