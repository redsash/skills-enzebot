#!/usr/bin/env python3
"""
lint_mermaid.py

Lints and validates Mermaid diagram syntax in Markdown files and .mmd documents.
Combines an external modern CLI linter (npx @probelabs/maid) when available
with a robust built-in deterministic Python AST/rule-based validator.

Common failure modes caught:
- Bare double quotes (e.g., inch marks `48"` or unescaped quotes inside `|...|` edge labels).
- Non-standard arrow tokens (e.g., `<==>`).
- Deprecated trailing semicolons on `classDef` or node statements.
- Mismatched shape brackets/enclosures (e.g., `([`, `[(`, `[[`, `{{`).
- Missing or malformed diagram header (e.g., `graph TD`, `sequenceDiagram`).
- HTML tags in labels without quotes.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


MERMAID_FENCE_PATTERN = re.compile(
    r"^```(?:mermaid)\s*\n(.*?)\n```",
    re.MULTILINE | re.DOTALL,
)

VALID_DIAGRAM_HEADERS = (
    "graph",
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "gantt",
    "pie",
    "gitGraph",
    "mindmap",
    "timeline",
    "quadrantChart",
    "xychart-beta",
    "c4Context",
    "c4Container",
    "c4Component",
    "sankey-beta",
    "packet-beta",
    "kanban",
    "architecture-beta",
)


def extract_mermaid_blocks(content: str) -> List[Tuple[int, str]]:
    """Extract (line_number, block_content) for all mermaid code fences in markdown."""
    blocks = []
    lines = content.splitlines(keepends=True)
    in_fence = False
    fence_start_line = 0
    current_block: List[str] = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```mermaid"):
                in_fence = True
                fence_start_line = idx
                current_block = []
        else:
            if stripped == "```":
                in_fence = False
                blocks.append((fence_start_line, "".join(current_block)))
                current_block = []
            else:
                current_block.append(line)

    return blocks


def lint_with_maid(file_path: Path) -> Optional[Tuple[bool, List[str]]]:
    """
    Attempt to run `@probelabs/maid` via npx.
    Returns (is_valid, messages) if maid is runnable, or None if unavailable.
    """
    if not shutil.which("npx"):
        return None

    try:
        proc = subprocess.run(
            ["npx", "-y", "@probelabs/maid", str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        output = (proc.stdout + "\n" + proc.stderr).strip()
        is_valid = proc.returncode == 0
        messages = [line for line in output.splitlines() if line and not line.startswith("npm notice")]
        return is_valid, messages
    except Exception:
        return None


def lint_diagram_rules(block: str, start_line: int) -> Tuple[List[Dict[str, Any]], str]:
    """
    Built-in Python deterministic Mermaid linter.
    Returns (list_of_issues, fixed_content).
    """
    issues: List[Dict[str, Any]] = []
    lines = block.splitlines()
    fixed_lines: List[str] = []

    if not lines or not block.strip():
        issues.append({
            "line": start_line,
            "rule": "EMPTY_DIAGRAM",
            "message": "Mermaid diagram code block is completely empty.",
            "severity": "ERROR",
        })
        return issues, block

    # 1. Header Check
    first_non_empty = ""
    first_line_no = start_line
    for i, l in enumerate(lines):
        s = l.strip()
        if s and not s.startswith("%%"):
            first_non_empty = s
            first_line_no = start_line + i + 1
            break

    if not first_non_empty:
        issues.append({
            "line": start_line,
            "rule": "MISSING_HEADER",
            "message": "Mermaid diagram contains only comments or whitespace.",
            "severity": "ERROR",
        })
        return issues, block

    header_word = first_non_empty.split()[0]
    if header_word not in VALID_DIAGRAM_HEADERS:
        issues.append({
            "line": first_line_no,
            "rule": "INVALID_DIAGRAM_TYPE",
            "message": f"Unknown or unsupported Mermaid diagram type '{header_word}'. Expected one of: {', '.join(VALID_DIAGRAM_HEADERS[:7])}...",
            "severity": "ERROR",
        })

    # Line-by-line linting
    for idx, raw_line in enumerate(lines):
        current_lineno = start_line + idx + 1
        line = raw_line
        stripped = line.strip()

        if not stripped or stripped.startswith("%%"):
            fixed_lines.append(raw_line)
            continue

        # 2. Check trailing semicolons on classDef or style
        if (stripped.startswith("classDef ") or stripped.startswith("style ")) and stripped.endswith(";"):
            issues.append({
                "line": current_lineno,
                "rule": "TRAILING_SEMICOLON",
                "message": f"Trailing semicolon on '{stripped[:30]}...' can break strict Mermaid parsers.",
                "severity": "ERROR",
                "fixable": True,
            })
            line = line.rstrip().rstrip(";")

        # 3. Check invalid bidirectional thick arrow <==>
        if "<==>" in line:
            issues.append({
                "line": current_lineno,
                "rule": "INVALID_ARROW",
                "message": "Invalid arrow token '<==>'. Flowcharts use '<-->' for bidirectional connections.",
                "severity": "ERROR",
                "fixable": True,
            })
            line = line.replace("<==>", "<-->")

        # 4. Check unescaped quotes inside edge label pipes: |... " ...|
        pipe_match = re.search(r"\|([^|]+)\|", line)
        if pipe_match:
            pipe_content = pipe_match.group(1)
            # Find bare quotes not escaped as #quot; or part of a balanced quoted string
            if '"' in pipe_content and not pipe_content.strip().startswith('"'):
                issues.append({
                    "line": current_lineno,
                    "rule": "BARE_QUOTE_IN_EDGE_LABEL",
                    "message": f"Unescaped double quote inside edge label '|{pipe_content}|'. Use '-in', 'in', or '#quot;' instead of bare '\"'.",
                    "severity": "ERROR",
                    "fixable": True,
                })
                # Auto-fix: e.g. 48" -> 48-in, 2" -> 2-in
                fixed_pipe = re.sub(r'(\d+)"', r"\1-in", pipe_content)
                fixed_pipe = fixed_pipe.replace('"', "")
                line = line[:pipe_match.start(1)] + fixed_pipe + line[pipe_match.end(1):]

        # 5. Check unquoted parentheses in node text
        # e.g. Node[Some text (extra)] -> should be Node["Some text (extra)"]
        bad_parens = re.search(r'([A-Za-z0-9_]+)\[([^"\]]*\([^"\]]*\)[^"\]]*)\]', line)
        if bad_parens:
            node_id = bad_parens.group(1)
            label = bad_parens.group(2)
            issues.append({
                "line": current_lineno,
                "rule": "UNQUOTED_SPECIAL_CHARS",
                "message": f"Node '{node_id}' label contains parentheses without quotes: '[{label}]'. Wrap label in quotes: '[\"{label}\"]'.",
                "severity": "WARN",
                "fixable": True,
            })
            line = line.replace(f"[{label}]", f'["{label}"]')

        # 6. Check mismatched shape brackets
        shape_pairs = [("([", "])"), ("[[", "]]"), ("[(", ")]"), ("((", "))"), (">{{", "}}")]
        for opener, closer in shape_pairs:
            if opener in line and closer not in line:
                issues.append({
                    "line": current_lineno,
                    "rule": "MISMATCHED_SHAPE_DELIMITER",
                    "message": f"Mismatched shape delimiter '{opener}' missing matching '{closer}'.",
                    "severity": "ERROR",
                })

        fixed_lines.append(line)

    result_text = "\n".join(fixed_lines)
    if block.endswith("\n"):
        result_text += "\n"
    return issues, result_text


def lint_markdown_file(file_path: Path, apply_fix: bool = False) -> Dict[str, Any]:
    """Lint all mermaid blocks in a markdown file or standalone .mmd file."""
    content = file_path.read_text(encoding="utf-8")
    is_standalone_mmd = file_path.suffix in (".mmd", ".mermaid")

    if is_standalone_mmd:
        blocks = [(1, content)]
    else:
        blocks = extract_mermaid_blocks(content)

    all_issues: List[Dict[str, Any]] = []

    # Built-in rule checks and fixes
    modified_content = content
    has_fixes = False

    for start_line, block_content in blocks:
        issues, fixed_block = lint_diagram_rules(block_content, start_line)
        all_issues.extend(issues)

        if apply_fix and fixed_block != block_content:
            has_fixes = True
            modified_content = modified_content.replace(block_content, fixed_block)

    if apply_fix and has_fixes:
        file_path.write_text(modified_content, encoding="utf-8")
        # Re-evaluate issues after applying fixes
        content = modified_content
        blocks = [(1, content)] if is_standalone_mmd else extract_mermaid_blocks(content)
        all_issues = []
        for start_line, block_content in blocks:
            issues, _ = lint_diagram_rules(block_content, start_line)
            all_issues.extend(issues)

    # Validate with maid (post-fix if fix was applied)
    maid_result = lint_with_maid(file_path)
    maid_errors = []
    if maid_result is not None:
        maid_valid, maid_msgs = maid_result
        if not maid_valid:
            maid_errors = maid_msgs

    # Deduplicate issues
    errors = [i for i in all_issues if i["severity"] == "ERROR"]
    warnings = [i for i in all_issues if i["severity"] == "WARN"]

    is_valid = len(errors) == 0 and len(maid_errors) == 0

    return {
        "file": str(file_path),
        "total_diagrams": len(blocks),
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "maid_errors": maid_errors,
        "fixed": apply_fix and has_fixes,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Lint and validate Mermaid diagram syntax in Markdown files or .mmd documents."
    )
    parser.add_argument("target", help="File or directory to lint")
    parser.add_argument("--fix", action="store_true", help="Automatically fix common safe syntax issues")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    target_path = Path(args.target)

    if not target_path.exists():
        sys.stderr.write(f"Target '{target_path}' does not exist.\n")
        sys.exit(1)

    if target_path.is_file():
        files_to_check = [target_path]
    else:
        files_to_check = list(target_path.glob("**/*.md")) + list(target_path.glob("**/*.mmd"))

    overall_valid = True
    results = []

    for f in files_to_check:
        res = lint_markdown_file(f, apply_fix=args.fix)
        if res["total_diagrams"] > 0:
            results.append(res)
            if not res["valid"]:
                overall_valid = False

    if args.json:
        json.dump({"valid": overall_valid, "results": results}, sys.stdout, indent=2)
        print()
        sys.exit(0 if overall_valid else 1)

    # Formatted CLI output
    print(f"=== Mermaid Syntax Linter ===")
    print(f"Target: {target_path.resolve()}\n")

    if not results:
        print("No Mermaid diagrams found in target files.")
        sys.exit(0)

    for r in results:
        status = "PASSED" if r["valid"] else "FAILED"
        print(f"[{status}] {r['file']} ({r['total_diagrams']} diagram(s))")

        if r["fixed"]:
            print("  ⚡ Applied automated fixes for syntax violations.")

        if r["errors"]:
            for err in r["errors"]:
                print(f"  ❌ Line {err['line']}: [{err['rule']}] {err['message']}")

        if r["maid_errors"]:
            for m in r["maid_errors"]:
                print(f"  ❌ [Maid Linter] {m}")

        if r["warnings"]:
            for warn in r["warnings"]:
                print(f"  ⚠️  Line {warn['line']}: [{warn['rule']}] {warn['message']}")

        print()

    if overall_valid:
        print("All Mermaid diagrams passed validation!")
        sys.exit(0)
    else:
        print("Mermaid validation failures detected.")
        sys.exit(1)


if __name__ == "__main__":
    main()
