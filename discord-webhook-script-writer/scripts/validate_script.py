#!/usr/bin/env python3
"""
Discord Webhook Bash Script Validator.

Performs static analysis, ShellCheck linting, dry-run execution, and Discord API
payload schema validation on generated bash webhook scripts.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def check_shellcheck(script_path: Path) -> dict:
    """Run ShellCheck on the target script."""
    shellcheck_bin = shutil.which("shellcheck")
    if not shellcheck_bin:
        # Check standard local paths
        candidates = [
            Path("/home/orbiter/.gemini/antigravity-cli/bin/shellcheck"),
            Path.home() / ".local/bin/shellcheck",
            Path("/usr/local/bin/shellcheck"),
            Path("/usr/bin/shellcheck"),
        ]
        for c in candidates:
            if c.is_file() and os.access(c, os.X_OK):
                shellcheck_bin = str(c)
                break

    if not shellcheck_bin:
        return {
            "passed": False,
            "tool_available": False,
            "error": "shellcheck binary not found in PATH or standard candidate locations.",
            "comments": [],
        }

    try:
        proc = subprocess.run(
            [shellcheck_bin, "-s", "bash", "-f", "json", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        comments = []
        if proc.stdout.strip():
            try:
                comments = json.loads(proc.stdout)
            except json.JSONDecodeError:
                comments = [{"message": proc.stdout.strip()}]

        passed = (proc.returncode == 0) and (len(comments) == 0)
        return {
            "passed": passed,
            "tool_available": True,
            "returncode": proc.returncode,
            "comments": comments,
        }
    except Exception as e:
        return {
            "passed": False,
            "tool_available": True,
            "error": f"Failed running shellcheck: {e}",
            "comments": [],
        }


def check_script_structure(content: str) -> dict:
    """Validate structural bash standards."""
    checks = {
        "shebang": bool(re.search(r"^#!\s*/(usr/bin/env\s+bash|bin/bash)", content, re.MULTILINE)),
        "strict_mode": bool(re.search(r"set\s+-[a-zA-Z0-9]*e[a-zA-Z0-9]*", content) and "pipefail" in content),
        "ifs_safety": "IFS=" in content,
        "main_function": bool(re.search(r"\bmain\s*\(\s*\)", content) and re.search(r'main\s+"\$@"', content)),
        "help_flag": bool("-h" in content or "--help" in content),
        "dry_run_flag": "--dry-run" in content,
        "webhook_url_handling": bool(
            "DISCORD_WEBHOOK_URL" in content and ("--webhook-url" in content or "-w" in content)
        ),
        "safe_conditionals": not bool(re.search(r"^\s*if\s+\[\s+[^\[]", content, re.MULTILINE)),
    }

    all_passed = all(checks.values())
    return {
        "passed": all_passed,
        "details": checks,
    }


def validate_discord_payload(payload: dict) -> dict:
    """Validate Discord Webhook payload constraints."""
    errors = []
    warnings = []

    # Content length limit: 2000 chars
    content = payload.get("content")
    if content is not None:
        if not isinstance(content, str):
            errors.append(f"'content' must be a string, got {type(content).__name__}")
        elif len(content) > 2000:
            errors.append(f"'content' exceeds Discord 2000-character limit ({len(content)} chars)")

    # Username length limit: 80 chars
    username = payload.get("username")
    if username is not None:
        if not isinstance(username, str) or len(username) > 80:
            errors.append(f"'username' must be string <= 80 characters, got {len(str(username))} chars")

    # Embeds
    embeds = payload.get("embeds", [])
    if embeds:
        if not isinstance(embeds, list):
            errors.append("'embeds' must be an array")
        elif len(embeds) > 10:
            errors.append(f"'embeds' array exceeds 10 items limit ({len(embeds)} embeds)")
        else:
            total_embed_chars = 0
            for i, emb in enumerate(embeds):
                if not isinstance(emb, dict):
                    errors.append(f"embeds[{i}] must be an object")
                    continue

                title = emb.get("title", "")
                if title:
                    if len(title) > 256:
                        errors.append(f"embeds[{i}].title exceeds 256 characters ({len(title)} chars)")
                    total_embed_chars += len(title)

                description = emb.get("description", "")
                if description:
                    if len(description) > 4096:
                        errors.append(f"embeds[{i}].description exceeds 4096 characters ({len(description)} chars)")
                    total_embed_chars += len(description)

                color = emb.get("color")
                if color is not None:
                    if not isinstance(color, int) or not (0 <= color <= 16777215):
                        errors.append(
                            f"embeds[{i}].color must be an integer between 0 and 16777215 (got {color})"
                        )

                footer = emb.get("footer")
                if isinstance(footer, dict):
                    f_text = footer.get("text", "")
                    if len(f_text) > 2048:
                        errors.append(f"embeds[{i}].footer.text exceeds 2048 characters ({len(f_text)} chars)")
                    total_embed_chars += len(f_text)

                author = emb.get("author")
                if isinstance(author, dict):
                    a_name = author.get("name", "")
                    if len(a_name) > 256:
                        errors.append(f"embeds[{i}].author.name exceeds 256 characters ({len(a_name)} chars)")
                    total_embed_chars += len(a_name)

                fields = emb.get("fields", [])
                if fields:
                    if not isinstance(fields, list):
                        errors.append(f"embeds[{i}].fields must be an array")
                    elif len(fields) > 25:
                        errors.append(f"embeds[{i}].fields exceeds 25 fields ({len(fields)} fields)")
                    else:
                        for fi, f in enumerate(fields):
                            if not isinstance(f, dict):
                                errors.append(f"embeds[{i}].fields[{fi}] must be an object")
                                continue
                            fname = f.get("name", "")
                            fval = f.get("value", "")
                            if not fname:
                                errors.append(f"embeds[{i}].fields[{fi}].name cannot be empty")
                            elif len(fname) > 256:
                                errors.append(
                                    f"embeds[{i}].fields[{fi}].name exceeds 256 characters ({len(fname)} chars)"
                                )
                            if not fval:
                                errors.append(f"embeds[{i}].fields[{fi}].value cannot be empty")
                            elif len(fval) > 1024:
                                errors.append(
                                    f"embeds[{i}].fields[{fi}].value exceeds 1024 characters ({len(fval)} chars)"
                                )
                            total_embed_chars += len(fname) + len(fval)

                timestamp = emb.get("timestamp")
                if timestamp:
                    # Validate ISO 8601 UTC
                    try:
                        clean_ts = timestamp.replace("Z", "+00:00")
                        datetime.fromisoformat(clean_ts)
                    except ValueError:
                        warnings.append(
                            f"embeds[{i}].timestamp '{timestamp}' may not strictly follow ISO 8601 format"
                        )

            if total_embed_chars > 6000:
                errors.append(
                    f"Total characters across all embeds exceeds 6000 limit ({total_embed_chars} chars)"
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def check_dry_run_execution(script_path: Path, sample_args: list) -> dict:
    """Execute script with --dry-run and capture payload."""
    env = os.environ.copy()
    if "DISCORD_WEBHOOK_URL" not in env:
        env["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/000000000000000000/mock-token-for-dry-run"

    # Tokenize arguments properly whether passed as single string or list of tokens
    expanded_args = []
    if sample_args:
        raw_combined = " ".join(sample_args)
        try:
            expanded_args = shlex.split(raw_combined)
        except ValueError:
            expanded_args = sample_args

    cmd = ["bash", str(script_path), "--dry-run"] + expanded_args
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            check=False,
            timeout=10,
        )

        output = proc.stdout
        # Extract json object from output
        json_payload = None
        # Try full output as JSON
        trimmed = output.strip()
        if trimmed.startswith("{") and trimmed.endswith("}"):
            try:
                json_payload = json.loads(trimmed)
            except json.JSONDecodeError:
                pass

        if json_payload is None:
            # Extract JSON by scanning for outermost balanced curly brackets
            start_idx = output.find("{")
            while start_idx != -1:
                depth = 0
                in_string = False
                escape = False
                end_idx = -1
                for idx in range(start_idx, len(output)):
                    char = output[idx]
                    if escape:
                        escape = False
                        continue
                    if char == "\\":
                        escape = True
                        continue
                    if char == '"':
                        in_string = not in_string
                        continue
                    if not in_string:
                        if char == "{":
                            depth += 1
                        elif char == "}":
                            depth -= 1
                            if depth == 0:
                                end_idx = idx
                                break
                if end_idx != -1:
                    candidate = output[start_idx : end_idx + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, dict) and ("embeds" in parsed or "content" in parsed):
                            json_payload = parsed
                            break
                    except json.JSONDecodeError:
                        pass
                start_idx = output.find("{", start_idx + 1)

        schema_result = None
        if json_payload is not None:
            schema_result = validate_discord_payload(json_payload)

        return {
            "executed": True,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "extracted_json": json_payload,
            "schema_validation": schema_result,
        }
    except subprocess.TimeoutExpired:
        return {
            "executed": False,
            "returncode": -1,
            "error": "Execution timed out after 10 seconds",
        }
    except Exception as e:
        return {
            "executed": False,
            "returncode": -1,
            "error": f"Failed running dry-run: {e}",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Validate a generated Bash Discord webhook script against ShellCheck, structure standards, and Discord API payload schema."
    )
    parser.add_argument("script_path", help="Path to the .sh script to validate")
    parser.add_argument(
        "--sample-args",
        nargs="*",
        default=[],
        help="Optional arguments to pass to the script alongside --dry-run",
    )
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    script_path = Path(args.script_path).resolve()

    if not script_path.is_file():
        sys.stderr.write(f"Error: Script file not found: {script_path}\n")
        sys.exit(1)

    content = script_path.read_text(encoding="utf-8")

    # 1. ShellCheck
    sc_result = check_shellcheck(script_path)

    # 2. Structure Standards
    struct_result = check_script_structure(content)

    # 3. Dry-run execution
    dry_run_result = check_dry_run_execution(script_path, args.sample_args)

    overall_passed = (
        sc_result.get("passed", False)
        and struct_result.get("passed", False)
        and dry_run_result.get("executed", False)
        and (dry_run_result.get("returncode") == 0)
    )

    if dry_run_result.get("schema_validation"):
        if not dry_run_result["schema_validation"]["valid"]:
            overall_passed = False

    result_report = {
        "script": str(script_path),
        "overall_passed": overall_passed,
        "shellcheck": sc_result,
        "structure": struct_result,
        "dry_run": dry_run_result,
    }

    if args.json:
        print(json.dumps(result_report, indent=2))
    else:
        status_label = "PASSED" if overall_passed else "FAILED"
        print(f"=== Script Validation: {status_label} ===")
        print(f"Script: {script_path}")
        print()

        # ShellCheck output
        sc_ok = sc_result.get("passed", False)
        print(f"ShellCheck: {'PASS' if sc_ok else 'FAIL'}")
        if not sc_ok:
            for comment in sc_result.get("comments", []):
                line = comment.get("line", "?")
                code = f"SC{comment.get('code', '')}"
                msg = comment.get("message", "")
                print(f"  - Line {line} [{code}]: {msg}")
            if sc_result.get("error"):
                print(f"  - Error: {sc_result['error']}")

        # Structure output
        st_ok = struct_result.get("passed", False)
        print(f"Structure & Best Practices: {'PASS' if st_ok else 'FAIL'}")
        for check_name, passed in struct_result.get("details", {}).items():
            mark = "✓" if passed else "✗"
            print(f"  [{mark}] {check_name}")

        # Dry Run
        dr_ok = (dry_run_result.get("returncode") == 0) and dry_run_result.get("executed", False)
        print(f"Dry-run Execution: {'PASS' if dr_ok else 'FAIL'}")
        if not dr_ok:
            if dry_run_result.get("error"):
                print(f"  - Error: {dry_run_result['error']}")
            if dry_run_result.get("stderr"):
                print(f"  - stderr: {dry_run_result['stderr'].strip()}")

        # Schema Validation
        sv = dry_run_result.get("schema_validation")
        if sv:
            sv_ok = sv.get("valid", False)
            print(f"Discord Payload Schema: {'PASS' if sv_ok else 'FAIL'}")
            for err in sv.get("errors", []):
                print(f"  - [ERROR] {err}")
            for warn in sv.get("warnings", []):
                print(f"  - [WARN] {warn}")
        elif dry_run_result.get("extracted_json") is None:
            print("Discord Payload Schema: SKIPPED (No JSON payload extracted from stdout)")

        print("=" * 40)

    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
