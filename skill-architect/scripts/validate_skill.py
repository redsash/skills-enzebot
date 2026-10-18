#!/usr/bin/env python3
"""
Validates an Agent Skill directory against the Open Skills Specification and Antigravity guidelines.

Usage:
    python3 scripts/validate_skill.py [OPTIONS] <skill-directory>

Options:
    --json       Output report as structured JSON to stdout
    --help, -h   Show this help message and exit

Checks:
    - SKILL.md exists and contains valid YAML frontmatter
    - 'name' conforms to 1-64 chars, [a-z0-9-], no consecutive hyphens, matches directory name
    - 'description' exists, non-empty, and <= 1024 characters
    - Optional fields: 'compatibility' <= 500 chars, 'metadata' is string-to-string mapping
    - SKILL.md body line count <= 500 lines (progressive disclosure recommendation)
    - Relative links in markdown reference files that exist on disk
"""

import sys
import os
import re
import argparse
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
KEBAB_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

VALID_PHASES = {"explore", "deliberate", "author", "critique", "maintain", "meta"}
VALID_MODALITIES = {"lens", "spec", "runbook", "harness"}
VALID_INTERACTIONS = {"interactive", "autonomous"}


def parse_frontmatter(content: str):
    """Extract and parse YAML frontmatter from markdown content."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, content, ["SKILL.md must begin with '---' YAML frontmatter delimiter."]

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return None, content, ["Frontmatter delimiter '---' was never closed."]

    raw_yaml = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:])

    if yaml:
        try:
            data = yaml.safe_load(raw_yaml)
            if not isinstance(data, dict):
                return None, body, ["Frontmatter must be a YAML dictionary / mapping."]
            return data, body, []
        except Exception as e:
            return None, body, [f"YAML parsing error: {e}"]
    else:
        # Fallback structured parser for frontmatter with mappings, lists, and folded scalars
        data = {}
        yaml_lines = raw_yaml.splitlines()
        stack = [(-1, data)]
        i = 0
        while i < len(yaml_lines):
            line = yaml_lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            indent = len(line) - len(line.lstrip(" "))
            while len(stack) > 1 and indent <= stack[-1][0]:
                stack.pop()

            cur = stack[-1][1]

            if stripped.startswith("- "):
                val = stripped[2:].strip().strip("'\"")
                if isinstance(cur, list):
                    cur.append(val)
                i += 1
                continue

            if ":" in stripped:
                k, v = stripped.split(":", 1)
                k = k.strip()
                v = v.strip()

                if v in (">-", ">", "|", "|-", ""):
                    # Look ahead for indentation
                    next_indent = None
                    for j in range(i + 1, len(yaml_lines)):
                        if yaml_lines[j].strip() and not yaml_lines[j].strip().startswith("#"):
                            next_indent = len(yaml_lines[j]) - len(yaml_lines[j].lstrip(" "))
                            break

                    if next_indent is not None and next_indent > indent:
                        next_stripped = yaml_lines[j].strip()
                        if v in (">-", ">", "|", "|-"):
                            block_lines = []
                            i += 1
                            while i < len(yaml_lines):
                                curr_line = yaml_lines[i]
                                if not curr_line.strip():
                                    block_lines.append("")
                                    i += 1
                                    continue
                                line_indent = len(curr_line) - len(curr_line.lstrip(" "))
                                if line_indent < next_indent:
                                    break
                                block_lines.append(curr_line.strip())
                                i += 1
                            cur[k] = " ".join(block_lines) if ">" in v else "\n".join(block_lines)
                            continue
                        elif next_stripped.startswith("- "):
                            new_list = []
                            cur[k] = new_list
                            stack.append((indent, new_list))
                        else:
                            new_dict = {}
                            cur[k] = new_dict
                            stack.append((indent, new_dict))
                    else:
                        cur[k] = ""
                elif v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                    cur[k] = items
                else:
                    cur[k] = v.strip("'\"")
            i += 1
        return data, body, []


def validate_skill(skill_dir_path: Path):
    errors = []
    warnings = []
    details = {}

    skill_dir = skill_dir_path.resolve()
    if not skill_dir.is_dir():
        errors.append(f"Directory not found: {skill_dir}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    dir_name = skill_dir.name
    details["dir_name"] = dir_name

    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        errors.append(f"Missing required SKILL.md file in {skill_dir}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Could not read SKILL.md: {e}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    frontmatter, body, fm_errors = parse_frontmatter(content)
    if fm_errors:
        errors.extend(fm_errors)
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    # Validate name
    name = frontmatter.get("name")
    details["name"] = name
    if not name or not isinstance(name, str):
        errors.append("Frontmatter 'name' is required and must be a string.")
    else:
        if len(name) < 1 or len(name) > 64:
            errors.append(f"Skill name '{name}' must be between 1 and 64 characters (current: {len(name)}).")
        if not NAME_PATTERN.match(name):
            errors.append(f"Skill name '{name}' invalid: must be lowercase alphanumeric with hyphens, cannot start/end with hyphen or have '--'.")
        if name != dir_name:
            errors.append(f"Skill name '{name}' must match parent directory name '{dir_name}'.")

    # Validate description
    desc = frontmatter.get("description")
    details["description_length"] = len(desc) if desc else 0
    if not desc or not isinstance(desc, str) or not desc.strip():
        errors.append("Frontmatter 'description' is required and must be a non-empty string.")
    else:
        desc_len = len(desc.strip())
        if desc_len > 1024:
            errors.append(f"Description length ({desc_len} chars) exceeds maximum allowed 1024 characters.")
        if desc_len < 30:
            warnings.append(f"Description is very brief ({desc_len} chars). Consider adding triggers and context.")

    # Validate compatibility (optional)
    compat = frontmatter.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            errors.append("Optional 'compatibility' must be a string.")
        elif len(compat) > 500:
            errors.append(f"Compatibility field length ({len(compat)}) exceeds maximum allowed 500 characters.")

    # Validate metadata (optional)
    meta = frontmatter.get("metadata")
    if meta is not None:
        if not isinstance(meta, dict):
            errors.append("Optional 'metadata' must be a key-value dictionary mapping string keys to string values.")
        else:
            for k, v in meta.items():
                if not isinstance(k, str) or not isinstance(v, str):
                    errors.append(f"Metadata entries must be string-to-string. Invalid pair: {k}={v}")

    # Validate taxonomy (recommended)
    taxonomy = frontmatter.get("taxonomy")
    if taxonomy is None:
        warnings.append("Missing 'taxonomy' in frontmatter. Consider adding 'phase', 'modality', and 'domain' for cataloging and routing.")
    elif not isinstance(taxonomy, dict):
        errors.append("Field 'taxonomy' must be a dictionary / mapping.")
    else:
        tax_details = {}

        # 1. Phase (explore, deliberate, author, critique, maintain, meta)
        raw_phases = taxonomy.get("phase")
        if not raw_phases:
            errors.append("Taxonomy requires 'phase' (e.g. explore, deliberate, author, critique, maintain, meta).")
        else:
            phases = [raw_phases] if isinstance(raw_phases, str) else list(raw_phases) if isinstance(raw_phases, list) else None
            if phases is None:
                errors.append("Taxonomy 'phase' must be a string or list of strings.")
            else:
                invalid_phases = [p for p in phases if not isinstance(p, str) or p not in VALID_PHASES]
                if invalid_phases:
                    errors.append(f"Invalid taxonomy phase(s): {invalid_phases}. Allowed: {sorted(list(VALID_PHASES))}")
                if len(phases) > 1:
                    warnings.append(f"Skill defines multiple phases: {phases}. While supported (1..n), single-phase focus is recommended for modular agent routing.")
                tax_details["phase"] = phases

        # 2. Modality (lens, spec, runbook, harness)
        raw_modalities = taxonomy.get("modality")
        if not raw_modalities:
            errors.append("Taxonomy requires 'modality' (e.g. lens, spec, runbook, harness).")
        else:
            modalities = [raw_modalities] if isinstance(raw_modalities, str) else list(raw_modalities) if isinstance(raw_modalities, list) else None
            if modalities is None:
                errors.append("Taxonomy 'modality' must be a string or list of strings.")
            else:
                invalid_mods = [m for m in modalities if not isinstance(m, str) or m not in VALID_MODALITIES]
                if invalid_mods:
                    errors.append(f"Invalid taxonomy modality(s): {invalid_mods}. Allowed: {sorted(list(VALID_MODALITIES))}")
                tax_details["modality"] = modalities

        # 3. Domain
        raw_domains = taxonomy.get("domain")
        if not raw_domains:
            errors.append("Taxonomy requires 'domain' (e.g. architecture-strategy, software-engineering, operations-reliability).")
        else:
            domains = [raw_domains] if isinstance(raw_domains, str) else list(raw_domains) if isinstance(raw_domains, list) else None
            if domains is None:
                errors.append("Taxonomy 'domain' must be a string or list of strings.")
            else:
                invalid_doms = [d for d in domains if not isinstance(d, str) or not KEBAB_PATTERN.match(d)]
                if invalid_doms:
                    errors.append(f"Invalid taxonomy domain(s): {invalid_doms}. Must be lowercase kebab-case strings.")
                tax_details["domain"] = domains

        # 4. Interaction (optional)
        raw_interaction = taxonomy.get("interaction")
        if raw_interaction is not None:
            interactions = [raw_interaction] if isinstance(raw_interaction, str) else list(raw_interaction) if isinstance(raw_interaction, list) else None
            if interactions is None:
                errors.append("Taxonomy 'interaction' must be a string or list of strings.")
            else:
                invalid_ints = [i for i in interactions if not isinstance(i, str) or i not in VALID_INTERACTIONS]
                if invalid_ints:
                    errors.append(f"Invalid taxonomy interaction(s): {invalid_ints}. Allowed: {sorted(list(VALID_INTERACTIONS))}")
                tax_details["interaction"] = interactions

        details["taxonomy"] = tax_details

    # Validate line count for progressive disclosure
    total_lines = len(content.splitlines())
    details["total_lines"] = total_lines
    if total_lines > 500:
        warnings.append(f"SKILL.md has {total_lines} lines (>500 lines recommended). Consider moving reference sections into references/.")

    # Validate internal relative links
    for match in MARKDOWN_LINK_PATTERN.finditer(body):
        link_target = match.group(2).strip()
        # Ignore web URLs, anchors, mailto
        if link_target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        # Split anchor if present
        clean_target = link_target.split("#")[0]
        if not clean_target:
            continue

        target_path = (skill_dir / clean_target).resolve()
        try:
            # Prevent directory traversal attacks
            target_path.relative_to(skill_dir)
        except ValueError:
            warnings.append(f"Relative link '{link_target}' references a path outside the skill directory.")
            continue

        if not target_path.exists():
            errors.append(f"Broken relative link in SKILL.md: '{link_target}' -> file not found.")

    # Check executable bit on scripts
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        for script_file in scripts_dir.iterdir():
            if script_file.is_file() and script_file.suffix in (".sh", ".py", ".bash"):
                if not os.access(script_file, os.X_OK):
                    warnings.append(f"Script '{script_file.name}' is not marked executable (chmod +x).")

    # Validate Mermaid syntax in SKILL.md and references/
    md_files_to_check = [skill_file]
    ref_dir = skill_dir / "references"
    if ref_dir.is_dir():
        md_files_to_check.extend(list(ref_dir.glob("*.md")))

    try:
        sys.path.insert(0, str(Path(__file__).parent.resolve()))
        from lint_mermaid import lint_markdown_file
    except Exception:
        lint_markdown_file = None

    if lint_markdown_file:
        for md_f in md_files_to_check:
            m_res = lint_markdown_file(md_f)
            if m_res.get("total_diagrams", 0) > 0:
                details.setdefault("mermaid_diagrams_checked", 0)
                details["mermaid_diagrams_checked"] += m_res["total_diagrams"]
                rel_name = md_f.name if md_f == skill_file else f"references/{md_f.name}"
                for m_err in m_res.get("errors", []):
                    errors.append(f"Mermaid syntax error in {rel_name} (line {m_err['line']}): [{m_err['rule']}] {m_err['message']}")
                for m_maid in m_res.get("maid_errors", []):
                    errors.append(f"Mermaid parser error in {rel_name}: {m_maid}")
                for m_warn in m_res.get("warnings", []):
                    warnings.append(f"Mermaid warning in {rel_name} (line {m_warn['line']}): [{m_warn['rule']}] {m_warn['message']}")

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "details": details
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory against Open Skills and Antigravity specifications."
    )
    parser.add_argument("skill_dir", help="Path to the skill directory to validate")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    skill_path = Path(args.skill_dir)

    result = validate_skill(skill_path)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "PASSED" if result["valid"] else "FAILED"
        print(f"Validation Result: {status}")
        print(f"Skill Directory:   {skill_path.resolve()}")
        if result["details"].get("name"):
            print(f"Skill Name:        {result['details']['name']}")
        if result["details"].get("description_length"):
            print(f"Description Size:  {result['details']['description_length']} / 1024 characters")
        if result["details"].get("total_lines"):
            print(f"Line Count:        {result['details']['total_lines']} lines")
        if result["details"].get("taxonomy"):
            tax = result["details"]["taxonomy"]
            tax_parts = []
            if "phase" in tax:
                tax_parts.append(f"phase=[{', '.join(tax['phase'])}]")
            if "modality" in tax:
                tax_parts.append(f"modality=[{', '.join(tax['modality'])}]")
            if "domain" in tax:
                tax_parts.append(f"domain=[{', '.join(tax['domain'])}]")
            if "interaction" in tax:
                tax_parts.append(f"interaction=[{', '.join(tax['interaction'])}]")
            print(f"Taxonomy:          {', '.join(tax_parts)}")
        if result["details"].get("mermaid_diagrams_checked"):
            print(f"Mermaid Diagrams:  {result['details']['mermaid_diagrams_checked']} checked (syntax valid)")

        if result["errors"]:
            print("\nErrors:")
            for err in result["errors"]:
                print(f"  [ERROR] {err}")

        if result["warnings"]:
            print("\nWarnings:")
            for warn in result["warnings"]:
                print(f"  [WARN]  {warn}")

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
