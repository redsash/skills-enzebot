#!/usr/bin/env python3
"""
Audits code files or directories for fundamental software design smells.
Flags violations of Single Responsibility, KISS, Law of Demeter,
Don't Make Me Think, and Information Hiding.

Output: Structured JSON or Markdown summary.
Non-interactive CLI utility.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java",
    ".c", ".cpp", ".cc", ".h", ".hpp", ".rs", ".rb", ".php", ".cs"
}

KEYWORDS = {"if", "while", "for", "switch", "catch", "return", "throw", "sizeof", "elif"}

TRAIN_WRECK_PATTERN = re.compile(
    r"([a-zA-Z0-9_]+(?:\(\))?\.[a-zA-Z0-9_]+(?:\(\))?\.[a-zA-Z0-9_]+(?:\(\))?\.[a-zA-Z0-9_]+)"
)

SWALLOW_PATTERN = re.compile(
    r"(?:except(?:\s+Exception)?\s*:\s*(?:pass|\.\.\.)|catch\s*\([^\)]*\)\s*\{\s*\})"
)

FLUENT_METHODS = {
    "filter", "map", "flatMap", "reduce", "then", "catch", "pipe", "join", "select", "where"
}


def is_comment_or_empty(line: str) -> bool:
    """Returns True if the line is blank or starts with comment tokens."""
    stripped = line.strip()
    return not stripped or stripped.startswith(("//", "#", "/*", "*"))


def extract_function_name(line: str, ext: str) -> Optional[str]:
    """Detects function declarations tailored to language extension, avoiding keyword confusion."""
    stripped = line.strip()

    if ext == ".py":
        match = re.match(r"^(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(", stripped)
        return match.group(1) if match else None

    if ext in {".js", ".ts", ".jsx", ".tsx"}:
        match = re.match(r"^(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\(", stripped)
        if match:
            return match.group(1)
        match_arrow = re.match(r"^(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(", stripped)
        return match_arrow.group(1) if match_arrow else None

    if ext == ".go":
        match = re.match(r"^func\s+(?:\([a-zA-Z0-9_ *]+\)\s+)?([a-zA-Z0-9_]+)\s*\(", stripped)
        return match.group(1) if match else None

    # C, C++, Java, C# style: Type Name(...)
    match_c = re.match(r"^(?:(?:public|private|protected|static|virtual|override|async)\s+)*([a-zA-Z0-9_<>,\[\]]+)\s+([a-zA-Z0-9_]+)\s*\(", stripped)
    if match_c:
        ret_type, func_name = match_c.group(1), match_c.group(2)
        if ret_type not in KEYWORDS:
            return func_name

    return None


def check_swallowed_exception(line: str, line_no: int) -> Optional[Dict[str, Any]]:
    """Flags empty or broad error swallowing while ignoring pattern and report strings."""
    if any(k in line for k in ["re.compile", "SWALLOW_PATTERN", '"smell":', "'smell':"]):
        return None
    if not SWALLOW_PATTERN.search(line):
        return None
    return {
        "line": line_no,
        "principle": "Principle of Least Astonishment / Maintainability",
        "smell": "Silent exception swallowing (broad catch without handling)",
        "severity": "high",
        "suggestion": "Handle error explicitly, log diagnostic context, or re-raise."
    }


def check_train_wreck(line: str, line_no: int) -> Optional[Dict[str, Any]]:
    """Flags Law of Demeter violations while excluding fluent pipelines and logging."""
    if not TRAIN_WRECK_PATTERN.search(line):
        return None
    if any(token in line for token in ["console.log", "logger", "builder", "stream", "SELECT"]):
        return None
    for method in FLUENT_METHODS:
        if f".{method}(" in line:
            return None

    return {
        "line": line_no,
        "principle": "Law of Demeter (Least Knowledge)",
        "smell": f"Deep navigation chain / train wreck: `{line.strip()[:80]}`",
        "severity": "low",
        "suggestion": "Delegate to direct collaborator rather than traversing internal object graph."
    }


def check_nesting_depth(raw_line: str, line_no: int, max_depth: int) -> Optional[Dict[str, Any]]:
    """Flags excessive indentation depth indicating complex control flow."""
    match = re.match(r"^(\s*)", raw_line)
    if not match:
        return None
    indent_spaces = len(match.group(1).replace("\t", "    "))
    depth = indent_spaces // 4
    if depth <= max_depth:
        return None

    return {
        "line": line_no,
        "principle": "KISS / Don't Make Me Think",
        "smell": f"Excessive nesting depth ({depth} levels > {max_depth})",
        "severity": "medium",
        "suggestion": "Use guard clauses, early returns, or extract helper functions."
    }


def evaluate_function_length(
    func_name: str,
    start_line: int,
    end_line: int,
    max_lines: int
) -> Optional[Dict[str, Any]]:
    """Flags functions exceeding the maximum length threshold."""
    length = end_line - start_line
    if length <= max_lines:
        return None
    return {
        "line": start_line,
        "principle": "Single Responsibility Principle / KISS",
        "smell": f"Excessive function length in `{func_name}` ({length} lines > {max_lines})",
        "severity": "high",
        "suggestion": "Decompose into smaller, single-responsibility functions."
    }


def scan_code_lines(lines: List[str], ext: str, max_lines: int, max_depth: int) -> List[Dict[str, Any]]:
    """Iterates through lines to flag exceptions, train wrecks, nesting, and function lengths."""
    findings: List[Dict[str, Any]] = []
    in_func = False
    func_name = ""
    func_start_line = 0

    for idx, raw_line in enumerate(lines, start=1):
        if is_comment_or_empty(raw_line):
            continue

        for check_fn in (check_swallowed_exception, check_train_wreck):
            smell = check_fn(raw_line, idx)
            if smell:
                findings.append(smell)

        depth_smell = check_nesting_depth(raw_line, idx, max_depth)
        if depth_smell:
            findings.append(depth_smell)

        detected_func = extract_function_name(raw_line, ext)
        if not detected_func:
            continue

        if in_func:
            length_smell = evaluate_function_length(func_name, func_start_line, idx, max_lines)
            if length_smell:
                findings.append(length_smell)

        func_name = detected_func
        func_start_line = idx
        in_func = True

    if in_func:
        final_smell = evaluate_function_length(func_name, func_start_line, len(lines), max_lines)
        if final_smell:
            findings.append(final_smell)

    return findings


def deduplicate_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Prunes repetitive consecutive depth warnings to reduce noise."""
    deduped: List[Dict[str, Any]] = []
    last_depth_line = -10
    for f in findings:
        if "nesting depth" in f["smell"]:
            if f["line"] == last_depth_line + 1:
                last_depth_line = f["line"]
                continue
            last_depth_line = f["line"]
        deduped.append(f)
    return deduped


def audit_file(
    file_path: Path,
    max_lines: int = 50,
    max_depth: int = 4,
    max_file_lines: int = 400
) -> Dict[str, Any]:
    """Audits a single file for fundamental smell indicators."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        sys.stderr.write(f"Warning: Could not read {file_path}: {e}\n")
        return {"file": str(file_path), "findings": []}

    lines = content.splitlines()
    total_lines = len(lines)
    ext = file_path.suffix.lower()
    findings: List[Dict[str, Any]] = []

    if total_lines > max_file_lines:
        findings.append({
            "line": 1,
            "principle": "Separation of Concerns / SRP",
            "smell": f"Excessive file size ({total_lines} lines > {max_file_lines} threshold)",
            "severity": "medium",
            "suggestion": "Decompose into smaller cohesive modules with distinct responsibilities."
        })

    findings.extend(scan_code_lines(lines, ext, max_lines, max_depth))
    return {
        "file": str(file_path),
        "total_lines": total_lines,
        "findings": deduplicate_findings(findings)
    }


def collect_target_files(target_path: Path) -> List[Path]:
    """Collects candidate files while pruning irrelevant directories."""
    if target_path.is_file():
        return [target_path]

    collected = []
    pruned_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in pruned_dirs]
        for file in files:
            p = Path(root) / file
            if p.suffix.lower() in EXTENSIONS:
                collected.append(p)
    return sorted(collected)


def print_markdown_report(files_count: int, results: List[Dict[str, Any]], total_smells: int):
    """Renders results as a GitHub-flavored markdown table."""
    print("# Programming Fundamentals Audit Report")
    print(f"- **Audited Files**: {files_count}")
    print(f"- **Files with Smells**: {len(results)}")
    print(f"- **Total Smells Detected**: {total_smells}\n")

    if not results:
        print("✅ No fundamental design smells detected across audited thresholds.")
        return

    for r in results:
        print(f"### File: `{r['file']}` ({r['total_lines']} lines)")
        print("| Line | Principle | Smell Detected | Severity | Suggestion |")
        print("| :--- | :--- | :--- | :--- | :--- |")
        for f in r["findings"]:
            print(f"| L{f['line']} | **{f['principle']}** | {f['smell']} | `{f['severity']}` | {f['suggestion']} |")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Audit source code files for fundamental design smells (SRP, KISS, Demeter, Krug, etc.)"
    )
    parser.add_argument("path", help="File or directory path to audit")
    parser.add_argument("--json", action="store_true", help="Output audit results as raw JSON")
    parser.add_argument("--max-lines", type=int, default=50, help="Max function length threshold (default: 50)")
    parser.add_argument("--max-depth", type=int, default=4, help="Max nesting depth threshold (default: 4)")
    parser.add_argument("--max-file-lines", type=int, default=400, help="Max file line threshold (default: 400)")

    args = parser.parse_args()
    target_path = Path(args.path)

    if not target_path.exists():
        sys.stderr.write(f"Error: Path '{args.path}' does not exist.\n")
        sys.exit(1)

    files_to_audit = collect_target_files(target_path)
    results = []
    total_smells = 0

    for file_path in files_to_audit:
        report = audit_file(
            file_path,
            max_lines=args.max_lines,
            max_depth=args.max_depth,
            max_file_lines=args.max_file_lines
        )
        if report["findings"]:
            results.append(report)
            total_smells += len(report["findings"])

    if args.json:
        output_payload = {
            "audited_files": len(files_to_audit),
            "files_with_smells": len(results),
            "total_smells": total_smells,
            "reports": results
        }
        json.dump(output_payload, sys.stdout, indent=2)
        print()
    else:
        print_markdown_report(len(files_to_audit), results, total_smells)


if __name__ == "__main__":
    main()
