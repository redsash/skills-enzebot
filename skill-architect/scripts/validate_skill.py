#!/usr/bin/env python3
"""
Validates an Agent Skill directory (or an entire skills repository with --all)
against the Open Skills Specification, Antigravity layering standards, and
repo taxonomy/collision rules.

Usage:
    python3 scripts/validate_skill.py [OPTIONS] <skill-or-repo-dir>

Options:
    --all                  Audit every skill under <dir> (and build collision matrix)
    --siblings-dir DIR     Override directory scanned for cross-skill collision checks
    --no-collisions        Skip cross-skill collision checks
    --json                 Output structured JSON report to stdout
    --help, -h             Show this help message and exit

Examples:
    python3 scripts/validate_skill.py skill-architect
    python3 scripts/validate_skill.py --all .
    python3 scripts/validate_skill.py --json engineering-log

Exit Codes:
    0  Validation passed (warnings allowed)
    1  Validation failed (one or more errors)
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml
except ImportError:
    yaml = None


NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEBAB_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FENCED_CODE_BLOCK_PATTERN = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

VALID_PHASES = {"explore", "deliberate", "author", "critique", "maintain", "meta"}
VALID_MODALITIES = {"lens", "spec", "runbook", "harness"}
VALID_INTERACTIONS = {"interactive", "autonomous"}

VALID_MODEL_TIERS = {"fast", "standard", "deep", "orchestrator"}
VALID_EFFORTS = {"low", "medium", "high"}
VALID_INVOCATIONS = {"auto", "manual", "hybrid"}

BODY_LINES_WARN = 250
BODY_LINES_ERROR = 500
CODE_BLOCK_WARN_LINES = 45
DESC_SOFT_MAX = 600

NON_THIRD_PERSON_RE = re.compile(
    r"^(i\s+|i'm\s+|we\s+|this skill\b|a skill (that|to|for)\b|helps you\b|an agent skill\b)",
    re.IGNORECASE,
)
TRIGGER_PHRASE_RE = re.compile(
    r"\b(use when|use for|use on|use whenever|use only|use this skill|activates? (when|whenever|on)|triggers? (when|on)|invoke[d]? (when|on|via))\b",
    re.IGNORECASE,
)
NON_TRIGGER_PHRASE_RE = re.compile(
    r"\b(do not use|don't use|not for|not intended for|avoid using|skip when|instead of|rather than)\b",
    re.IGNORECASE,
)
SCRIPT_HELP_MARKERS_RE = re.compile(
    r"(argparse|optparse|click|typer|getopts|--help|-h\b|usage\s*\(|Usage:)",
    re.IGNORECASE,
)
HOME_PATH_RE = re.compile(r"/(?:home|Users)/([A-Za-z0-9._-]+)/")
BENIGN_HOME_USERS = {"user", "username", "youruser", "yourname", "dev", "alice", "bob", "runner", "me"}
REQUIRED_META_HINTS = ("model-tier", "effort", "invocation")

STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for",
    "from", "has", "have", "in", "into", "is", "it", "its", "not", "of", "on",
    "or", "over", "that", "the", "their", "this", "to", "use", "used", "user",
    "using", "when", "whenever", "where", "which", "while", "with", "without",
    "skill", "agent", "asks", "asked", "task", "tasks", "work", "working",
    "activates", "triggers", "explicitly", "only", "also", "such", "other",
}


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
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

    # Fallback structured parser for frontmatter with mappings, lists, and folded scalars
    data: Dict[str, Any] = {}
    yaml_lines = raw_yaml.splitlines()
    stack: List[Tuple[int, Any]] = [(-1, data)]
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
                next_indent = None
                next_stripped = ""
                for j in range(i + 1, len(yaml_lines)):
                    if yaml_lines[j].strip() and not yaml_lines[j].strip().startswith("#"):
                        next_indent = len(yaml_lines[j]) - len(yaml_lines[j].lstrip(" "))
                        next_stripped = yaml_lines[j].strip()
                        break

                if next_indent is not None and next_indent > indent:
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
                        new_list: List[Any] = []
                        cur[k] = new_list
                        stack.append((indent, new_list))
                    else:
                        new_dict: Dict[str, Any] = {}
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


def _to_str_list(raw: Any) -> Optional[List[str]]:
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return list(raw)
    return None


def _tokenize_description(text: str) -> Tuple[List[str], Counter]:
    """Return stopword-filtered unigrams and a unigram+bigram frequency counter."""
    # Ignore explicit non-trigger clause when measuring positive trigger overlap
    split_match = NON_TRIGGER_PHRASE_RE.search(text)
    positive_text = text[:split_match.start()] if split_match else text
    raw_words = re.findall(r"[a-z0-9][a-z0-9\-/]*", positive_text.lower())
    unigrams = [w.strip("-/") for w in raw_words if len(w.strip("-/")) > 2 and w.strip("-/") not in STOPWORDS]
    bigrams = [f"{unigrams[i]} {unigrams[i + 1]}" for i in range(len(unigrams) - 1)]
    return unigrams, Counter(unigrams + bigrams)


def _cosine_similarity(c1: Counter, c2: Counter) -> float:
    if not c1 or not c2:
        return 0.0
    common = set(c1.keys()) & set(c2.keys())
    dot = sum(c1[k] * c2[k] for k in common)
    norm1 = math.sqrt(sum(v * v for v in c1.values()))
    norm2 = math.sqrt(sum(v * v for v in c2.values()))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def _jaccard_similarity(s1: Set[str], s2: Set[str]) -> float:
    if not s1 or not s2:
        return 0.0
    union = s1 | s2
    return len(s1 & s2) / len(union) if union else 0.0


def discover_skill_dirs(root_dir: Path) -> List[Path]:
    """Discover skill directories under root_dir (immediate children and .agents/skills/*)."""
    found: List[Path] = []
    seen: Set[Path] = set()
    root = root_dir.resolve()
    search_bases = [root]
    for sub in (".agents/skills", ".agent/skills"):
        candidate = root / sub
        if candidate.is_dir():
            search_bases.append(candidate)

    for base in search_bases:
        if not base.is_dir():
            continue
        for entry in sorted(base.iterdir()):
            if entry.is_dir() and not entry.name.startswith(".") and (entry / "SKILL.md").is_file():
                resolved = entry.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    found.append(resolved)
    return found


def _load_sibling_summary(skill_dir: Path) -> Optional[Dict[str, Any]]:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return None
    try:
        content = skill_file.read_text(encoding="utf-8")
    except Exception:
        return None
    fm, _, errs = parse_frontmatter(content)
    if errs or not fm:
        return None
    tax = fm.get("taxonomy") if isinstance(fm.get("taxonomy"), dict) else {}
    phases = _to_str_list(tax.get("phase")) or []
    modalities = _to_str_list(tax.get("modality")) or []
    domains = _to_str_list(tax.get("domain")) or []
    desc = fm.get("description") if isinstance(fm.get("description"), str) else ""
    return {
        "dir": skill_dir,
        "name": fm.get("name") or skill_dir.name,
        "description": desc.strip(),
        "phases": set(p for p in phases if isinstance(p, str)),
        "modalities": set(m for m in modalities if isinstance(m, str)),
        "domains": set(d for d in domains if isinstance(d, str)),
    }


def check_collisions(
    skill_dir: Path,
    name: Optional[str],
    desc: str,
    phases: Set[str],
    modalities: Set[str],
    domains: Set[str],
    siblings_dir: Optional[Path],
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Check for duplicate names, taxonomy neighbors, and lexical trigger overlap."""
    errors: List[str] = []
    warnings: List[str] = []
    collisions: List[Dict[str, Any]] = []

    scan_root = siblings_dir.resolve() if siblings_dir else skill_dir.parent.resolve()
    if not scan_root.is_dir():
        return errors, warnings, collisions

    sibling_dirs = [d for d in discover_skill_dirs(scan_root) if d != skill_dir]
    if not sibling_dirs:
        return errors, warnings, collisions

    my_unigrams, my_counter = _tokenize_description(desc)
    my_unigram_set = set(my_unigrams)
    my_desc_lower = desc.lower()

    for sib_dir in sibling_dirs:
        sib = _load_sibling_summary(sib_dir)
        if not sib:
            continue

        sib_name = str(sib["name"])
        if name and sib_name == name:
            errors.append(f"Duplicate skill name '{name}' collides with sibling at {sib_dir}.")
            collisions.append({"sibling": sib_name, "type": "duplicate_name"})
            continue

        sib_desc = sib["description"]
        sib_unigrams, sib_counter = _tokenize_description(sib_desc)
        sib_unigram_set = set(sib_unigrams)

        cosine = round(_cosine_similarity(my_counter, sib_counter), 3)
        jaccard = round(_jaccard_similarity(my_unigram_set, sib_unigram_set), 3)
        shared_terms = sorted(my_unigram_set & sib_unigram_set)[:8]

        shared_phases = sorted(phases & sib["phases"])
        shared_modalities = sorted(modalities & sib["modalities"])
        shared_domains = sorted(domains & sib["domains"])
        is_tax_neighbor = bool(shared_phases and shared_domains and (shared_modalities or cosine >= 0.02))

        mutually_disambiguated = (
            sib_name.lower() in my_desc_lower
            or (name and name.lower() in sib_desc.lower())
        )

        if cosine >= 0.35 or jaccard >= 0.25:
            warnings.append(
                f"High description overlap with sibling '{sib_name}' "
                f"(cosine={cosine}, jaccard={jaccard}, shared={shared_terms[:5]}). "
                f"Add explicit 'Do not use for...' disambiguation."
            )
            collisions.append({
                "sibling": sib_name,
                "type": "lexical_overlap",
                "cosine": cosine,
                "jaccard": jaccard,
                "shared_terms": shared_terms,
                "shared_phases": shared_phases,
                "shared_domains": shared_domains,
            })
        elif is_tax_neighbor and not mutually_disambiguated:
            warnings.append(
                f"Taxonomy neighbor '{sib_name}' shares phase={shared_phases} and domain={shared_domains} "
                f"(cosine={cosine}) without explicit cross-reference disambiguation in description."
            )
            collisions.append({
                "sibling": sib_name,
                "type": "taxonomy_neighbor",
                "cosine": cosine,
                "jaccard": jaccard,
                "shared_terms": shared_terms,
                "shared_phases": shared_phases,
                "shared_domains": shared_domains,
            })

    return errors, warnings, collisions


def validate_skill(
    skill_dir_path: Path,
    siblings_dir: Optional[Path] = None,
    check_sibling_collisions: bool = True,
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}

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
    if fm_errors or frontmatter is None:
        errors.extend(fm_errors)
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    # 1. Validate name
    name = frontmatter.get("name")
    details["name"] = name
    if not name or not isinstance(name, str):
        errors.append("Frontmatter 'name' is required and must be a string.")
    else:
        if len(name) < 1 or len(name) > 64:
            errors.append(f"Skill name '{name}' must be between 1 and 64 characters (current: {len(name)}).")
        if not NAME_PATTERN.match(name):
            errors.append(
                f"Skill name '{name}' invalid: must be lowercase alphanumeric with hyphens, "
                "cannot start/end with hyphen or have '--'."
            )
        if name != dir_name:
            errors.append(f"Skill name '{name}' must match parent directory name '{dir_name}'.")

    # 2. Validate description
    desc = frontmatter.get("description")
    desc_clean = desc.strip() if isinstance(desc, str) else ""
    details["description_length"] = len(desc_clean)
    if not desc_clean:
        errors.append("Frontmatter 'description' is required and must be a non-empty string.")
    else:
        desc_len = len(desc_clean)
        if desc_len > 1024:
            errors.append(f"Description length ({desc_len} chars) exceeds maximum allowed 1024 characters.")
        elif desc_len > DESC_SOFT_MAX:
            warnings.append(
                f"Description is long ({desc_len} chars; target 200-{DESC_SOFT_MAX}). "
                "Tighten for startup context economy."
            )
        if desc_len < 30:
            warnings.append(f"Description is very brief ({desc_len} chars). Add triggers and scope boundaries.")
        if NON_THIRD_PERSON_RE.match(desc_clean):
            warnings.append(
                "Description should open in crisp third-person (e.g. 'Audits...', 'Designs...') "
                "rather than first-person or meta phrasing ('This skill...', 'A skill that...')."
            )
        if not TRIGGER_PHRASE_RE.search(desc_clean) and not (name and f"/{name}" in desc_clean):
            warnings.append(
                "Description lacks an explicit trigger clause (e.g. 'Use when...', 'Activates when...', or '/skill-name')."
            )
        if not NON_TRIGGER_PHRASE_RE.search(desc_clean):
            warnings.append(
                "Description lacks an explicit non-trigger boundary ('Do not use for...'). "
                "Adding exclusions prevents false-positive routing."
            )

    # 3. Validate compatibility (optional)
    compat = frontmatter.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            errors.append("Optional 'compatibility' must be a string.")
        elif len(compat) > 500:
            errors.append(f"Compatibility field length ({len(compat)}) exceeds maximum allowed 500 characters.")

    # 4. Validate metadata (recommended, Open Skills string-to-string map + execution hints)
    meta = frontmatter.get("metadata")
    if meta is None:
        warnings.append("Missing 'metadata' execution hints (model-tier, effort, invocation).")
    elif not isinstance(meta, dict):
        errors.append("Optional 'metadata' must be a key-value dictionary mapping string keys to string values.")
    else:
        meta_hints: Dict[str, str] = {}
        for k, v in meta.items():
            if not isinstance(k, str) or not isinstance(v, str):
                errors.append(f"Metadata entries must be string-to-string. Invalid pair: {k}={v}")
                continue
            if k == "model-tier":
                if v not in VALID_MODEL_TIERS:
                    errors.append(f"Invalid metadata.model-tier '{v}'. Allowed: {sorted(VALID_MODEL_TIERS)}")
                else:
                    meta_hints[k] = v
            elif k == "effort":
                if v not in VALID_EFFORTS:
                    errors.append(f"Invalid metadata.effort '{v}'. Allowed: {sorted(VALID_EFFORTS)}")
                else:
                    meta_hints[k] = v
            elif k == "invocation":
                if v not in VALID_INVOCATIONS:
                    errors.append(f"Invalid metadata.invocation '{v}'. Allowed: {sorted(VALID_INVOCATIONS)}")
                else:
                    meta_hints[k] = v
                    if v == "manual" and name and f"/{name}" not in desc_clean and "explicit" not in desc_clean.lower():
                        warnings.append(
                            f"metadata.invocation is 'manual', but description does not mention '/{name}' or explicit invocation."
                        )
        missing_hints = [k for k in REQUIRED_META_HINTS if k not in meta]
        if missing_hints:
            warnings.append(f"metadata missing recommended execution hint(s): {missing_hints}.")
        if meta_hints:
            details["metadata_hints"] = meta_hints

    # 5. Validate taxonomy (recommended)
    taxonomy = frontmatter.get("taxonomy")
    parsed_phases: Set[str] = set()
    parsed_modalities: Set[str] = set()
    parsed_domains: Set[str] = set()
    if taxonomy is None:
        warnings.append("Missing 'taxonomy' in frontmatter. Add 'phase', 'modality', and 'domain' for cataloging and routing.")
    elif not isinstance(taxonomy, dict):
        errors.append("Field 'taxonomy' must be a dictionary / mapping.")
    else:
        tax_details: Dict[str, Any] = {}

        raw_phases = taxonomy.get("phase")
        if not raw_phases:
            errors.append("Taxonomy requires 'phase' (e.g. explore, deliberate, author, critique, maintain, meta).")
        else:
            phases = _to_str_list(raw_phases)
            if phases is None:
                errors.append("Taxonomy 'phase' must be a string or list of strings.")
            else:
                invalid_phases = [p for p in phases if not isinstance(p, str) or p not in VALID_PHASES]
                if invalid_phases:
                    errors.append(f"Invalid taxonomy phase(s): {invalid_phases}. Allowed: {sorted(VALID_PHASES)}")
                elif len(phases) >= 3:
                    warnings.append(
                        f"Skill spans {len(phases)} phases ({phases}) — megaskill candidate. "
                        "Consider decomposing into single-phase composable skills."
                    )
                elif len(phases) == 2:
                    warnings.append(
                        f"Skill defines multiple phases: {phases}. Single-phase focus is preferred for modular routing."
                    )
                parsed_phases = set(p for p in phases if isinstance(p, str))
                tax_details["phase"] = phases

        raw_modalities = taxonomy.get("modality")
        if not raw_modalities:
            errors.append("Taxonomy requires 'modality' (e.g. lens, spec, runbook, harness).")
        else:
            modalities = _to_str_list(raw_modalities)
            if modalities is None:
                errors.append("Taxonomy 'modality' must be a string or list of strings.")
            else:
                invalid_mods = [m for m in modalities if not isinstance(m, str) or m not in VALID_MODALITIES]
                if invalid_mods:
                    errors.append(f"Invalid taxonomy modality(s): {invalid_mods}. Allowed: {sorted(VALID_MODALITIES)}")
                parsed_modalities = set(m for m in modalities if isinstance(m, str))
                tax_details["modality"] = modalities

        raw_domains = taxonomy.get("domain")
        if not raw_domains:
            errors.append("Taxonomy requires 'domain' (e.g. architecture-strategy, software-engineering, operations-reliability).")
        else:
            domains = _to_str_list(raw_domains)
            if domains is None:
                errors.append("Taxonomy 'domain' must be a string or list of strings.")
            else:
                invalid_doms = [d for d in domains if not isinstance(d, str) or not KEBAB_PATTERN.match(d)]
                if invalid_doms:
                    errors.append(f"Invalid taxonomy domain(s): {invalid_doms}. Must be lowercase kebab-case strings.")
                parsed_domains = set(d for d in domains if isinstance(d, str))
                tax_details["domain"] = domains

        raw_interaction = taxonomy.get("interaction")
        if raw_interaction is not None:
            interactions = _to_str_list(raw_interaction)
            if interactions is None:
                errors.append("Taxonomy 'interaction' must be a string or list of strings.")
            else:
                invalid_ints = [i for i in interactions if not isinstance(i, str) or i not in VALID_INTERACTIONS]
                if invalid_ints:
                    errors.append(f"Invalid taxonomy interaction(s): {invalid_ints}. Allowed: {sorted(VALID_INTERACTIONS)}")
                tax_details["interaction"] = interactions

        details["taxonomy"] = tax_details

    # 6. Context economy & progressive disclosure checks
    total_lines = len(content.splitlines())
    body_lines = len(body.splitlines())
    details["total_lines"] = total_lines
    details["body_lines"] = body_lines

    if body_lines > BODY_LINES_ERROR:
        errors.append(
            f"SKILL.md body has {body_lines} lines (exceeds hard ceiling of {BODY_LINES_ERROR} lines). "
            "Offload schemas, tables, and examples into references/ or examples/."
        )
    elif body_lines > BODY_LINES_WARN:
        warnings.append(
            f"SKILL.md body has {body_lines} lines (target <= {BODY_LINES_WARN}). "
            "Consider offloading bulky sections to references/ or examples/."
        )

    for block_match in FENCED_CODE_BLOCK_PATTERN.finditer(body):
        block_line_count = len(block_match.group(1).splitlines())
        if block_line_count > CODE_BLOCK_WARN_LINES:
            warnings.append(
                f"Large inline code/template block ({block_line_count} lines > {CODE_BLOCK_WARN_LINES}) in SKILL.md. "
                "Offload large templates/examples into examples/ or references/."
            )

    # 7. Validate internal relative links (strip fenced code blocks first to prevent false positives)
    body_no_code = FENCED_CODE_BLOCK_PATTERN.sub("", body)
    for match in MARKDOWN_LINK_PATTERN.finditer(body_no_code):
        link_target = match.group(2).strip()
        if link_target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean_target = link_target.split("#")[0]
        if not clean_target:
            continue

        target_path = (skill_dir / clean_target).resolve()
        try:
            target_path.relative_to(skill_dir)
        except ValueError:
            warnings.append(f"Relative link '{link_target}' references a path outside the skill directory.")
            continue

        if not target_path.exists():
            errors.append(f"Broken relative link in SKILL.md: '{link_target}' -> file not found.")

    # 8. Orphaned bundled resource detection
    for subdir_name in ("references", "examples", "assets", "scripts"):
        subdir = skill_dir / subdir_name
        if not subdir.is_dir():
            continue
        for item in sorted(subdir.iterdir()):
            if item.name.startswith(".") or item.name == "__pycache__" or item.suffix == ".pyc":
                continue
            rel_ref = f"{subdir_name}/{item.name}"
            if rel_ref not in body and item.name not in body:
                warnings.append(
                    f"Orphaned bundled resource '{rel_ref}' is not referenced in SKILL.md."
                )

    # 9. Black-box script checks
    scripts_dir = skill_dir / "scripts"
    executable_scripts: List[Path] = []
    if scripts_dir.is_dir():
        for script_file in sorted(scripts_dir.iterdir()):
            if script_file.is_file() and script_file.suffix in (".sh", ".py", ".bash"):
                executable_scripts.append(script_file)
                if not os.access(script_file, os.X_OK):
                    warnings.append(f"Script 'scripts/{script_file.name}' is not marked executable (chmod +x).")
                try:
                    src = script_file.read_text(encoding="utf-8", errors="ignore")
                    if not SCRIPT_HELP_MARKERS_RE.search(src):
                        warnings.append(
                            f"Script 'scripts/{script_file.name}' does not appear to expose a --help / CLI usage interface."
                        )
                except Exception:
                    pass

    if executable_scripts and "--help" not in body:
        warnings.append(
            "Skill bundles scripts/ but SKILL.md does not instruct agents to run '--help' first (black-box script pattern)."
        )

    # 9b. Portability checks: hardcoded home paths & repo-prefixed script paths
    for script_file in executable_scripts:
        try:
            src = script_file.read_text(encoding="utf-8", errors="ignore")
            for hm in HOME_PATH_RE.finditer(src):
                uname = hm.group(1)
                if uname.lower() in BENIGN_HOME_USERS or uname.startswith("<"):
                    continue
                errors.append(
                    f"Hardcoded absolute home path '{hm.group(0)}' in scripts/{script_file.name}; "
                    "use Path.home() or env vars for portability."
                )
        except Exception:
            pass

    doc_files_to_check = [skill_file]
    for doc_subdir in ("references", "examples"):
        d = skill_dir / doc_subdir
        if d.is_dir():
            doc_files_to_check.extend(sorted(d.glob("*.md")))

    for doc_f in doc_files_to_check:
        try:
            doc_txt = doc_f.read_text(encoding="utf-8", errors="ignore")
            rel_doc = str(doc_f.relative_to(skill_dir))
            for hm in HOME_PATH_RE.finditer(doc_txt):
                uname = hm.group(1)
                if uname.lower() in BENIGN_HOME_USERS or uname.startswith("<"):
                    continue
                warnings.append(
                    f"Hardcoded absolute home path '{hm.group(0)}' in {rel_doc}; use '~/' or relative paths for portability."
                )
            if scripts_dir.is_dir() and doc_f.parent.name != "examples":
                prefixed = f"{dir_name}/scripts/"
                if prefixed in doc_txt:
                    warnings.append(
                        f"Repo-prefixed script path '{prefixed}...' in {rel_doc}; "
                        "use relative 'scripts/...' for standalone install portability."
                    )
        except Exception:
            pass

    # 9c. Validate evals/ integrity if present
    evals_dir = skill_dir / "evals"
    evals_json = evals_dir / "evals.json"
    if evals_json.is_file():
        try:
            ev_data = json.loads(evals_json.read_text(encoding="utf-8"))
            if not isinstance(ev_data, dict) or not isinstance(ev_data.get("evals"), list) or not ev_data["evals"]:
                errors.append("evals/evals.json must be a JSON object with a non-empty 'evals' list.")
            else:
                for idx, ev_item in enumerate(ev_data["evals"]):
                    if not isinstance(ev_item, dict):
                        errors.append(f"evals/evals.json evals[{idx}] must be an object.")
                        continue
                    if not isinstance(ev_item.get("prompt"), str) or not ev_item["prompt"].strip():
                        errors.append(f"evals/evals.json evals[{idx}] missing non-empty 'prompt'.")
                    if not isinstance(ev_item.get("assertions"), list) or not ev_item["assertions"]:
                        errors.append(f"evals/evals.json evals[{idx}] missing non-empty 'assertions' list.")
                    for fpath in ev_item.get("files") or []:
                        if not isinstance(fpath, str) or not (skill_dir / fpath).exists():
                            errors.append(f"evals/evals.json references missing fixture file: '{fpath}'")
        except Exception as e:
            errors.append(f"Invalid JSON in evals/evals.json: {e}")

    tq_json = evals_dir / "trigger_queries.json"
    if tq_json.is_file():
        try:
            tq_data = json.loads(tq_json.read_text(encoding="utf-8"))
            if isinstance(tq_data, dict):
                warnings.append(
                    "evals/trigger_queries.json should be a top-level JSON array [...], not an object wrapper."
                )
            elif not isinstance(tq_data, list):
                errors.append("evals/trigger_queries.json must be a JSON array.")
            else:
                has_pos = False
                has_neg = False
                for idx, q_item in enumerate(tq_data):
                    if not isinstance(q_item, dict):
                        errors.append(f"evals/trigger_queries.json[{idx}] must be an object.")
                        continue
                    if not isinstance(q_item.get("query"), str) or not q_item["query"].strip():
                        errors.append(f"evals/trigger_queries.json[{idx}] missing non-empty 'query'.")
                    st = q_item.get("should_trigger")
                    if not isinstance(st, bool):
                        errors.append(f"evals/trigger_queries.json[{idx}].should_trigger must be a boolean.")
                    elif st is True:
                        has_pos = True
                    else:
                        has_neg = True
                if not has_pos or not has_neg:
                    warnings.append(
                        "evals/trigger_queries.json should include both should_trigger=true and should_trigger=false queries."
                    )
        except Exception as e:
            errors.append(f"Invalid JSON in evals/trigger_queries.json: {e}")

    # 10. Validate Mermaid syntax in SKILL.md, references/, and examples/
    md_files_to_check = [skill_file]
    for doc_subdir in ("references", "examples"):
        d = skill_dir / doc_subdir
        if d.is_dir():
            md_files_to_check.extend(sorted(d.glob("*.md")))

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
                rel_name = str(md_f.relative_to(skill_dir))
                for m_err in m_res.get("errors", []):
                    errors.append(
                        f"Mermaid syntax error in {rel_name} (line {m_err['line']}): [{m_err['rule']}] {m_err['message']}"
                    )
                for m_maid in m_res.get("maid_errors", []):
                    errors.append(f"Mermaid parser error in {rel_name}: {m_maid}")
                for m_warn in m_res.get("warnings", []):
                    warnings.append(
                        f"Mermaid warning in {rel_name} (line {m_warn['line']}): [{m_warn['rule']}] {m_warn['message']}"
                    )

    # 11. Cross-skill collision gate
    if check_sibling_collisions:
        c_errs, c_warns, collisions = check_collisions(
            skill_dir=skill_dir,
            name=name if isinstance(name, str) else None,
            desc=desc_clean,
            phases=parsed_phases,
            modalities=parsed_modalities,
            domains=parsed_domains,
            siblings_dir=siblings_dir,
        )
        errors.extend(c_errs)
        warnings.extend(c_warns)
        if collisions:
            details["collisions"] = collisions

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "details": details,
    }


def _print_human_report(skill_path: Path, result: Dict[str, Any]) -> None:
    status = "PASSED" if result["valid"] else "FAILED"
    print(f"Validation Result: {status}")
    print(f"Skill Directory:   {skill_path.resolve()}")
    d = result["details"]
    if d.get("name"):
        print(f"Skill Name:        {d['name']}")
    if d.get("description_length") is not None:
        print(f"Description Size:  {d['description_length']} / 1024 characters")
    if d.get("body_lines") is not None:
        print(f"Line Count:        {d['body_lines']} body lines ({d['total_lines']} total)")
    if d.get("taxonomy"):
        tax = d["taxonomy"]
        tax_parts = [f"{k}=[{', '.join(tax[k])}]" for k in ("phase", "modality", "domain", "interaction") if k in tax]
        print(f"Taxonomy:          {', '.join(tax_parts)}")
    if d.get("metadata_hints"):
        hints = ", ".join(f"{k}={v}" for k, v in d["metadata_hints"].items())
        print(f"Execution Hints:   {hints}")
    if d.get("mermaid_diagrams_checked"):
        print(f"Mermaid Diagrams:  {d['mermaid_diagrams_checked']} checked")
    if d.get("collisions"):
        print(f"Collision Alerts:  {len(d['collisions'])} sibling overlap(s)")

    if result["errors"]:
        print("\nErrors:")
        for err in result["errors"]:
            print(f"  [ERROR] {err}")

    if result["warnings"]:
        print("\nWarnings:")
        for warn in result["warnings"]:
            print(f"  [WARN]  {warn}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Agent Skill(s) against Open Skills, Antigravity layering, context economy, and collision gates."
    )
    parser.add_argument("target", help="Path to a skill directory, or a repository root when used with --all")
    parser.add_argument("--all", action="store_true", help="Audit all skills under target directory")
    parser.add_argument("--siblings-dir", type=Path, default=None, help="Directory containing sibling skills for collision checks")
    parser.add_argument("--no-collisions", action="store_true", help="Skip cross-skill collision checks")
    parser.add_argument("--json", action="store_true", help="Output structured JSON report to stdout")

    args = parser.parse_args()
    target_path = Path(args.target)

    if args.all:
        skill_dirs = discover_skill_dirs(target_path)
        if not skill_dirs:
            sys.stderr.write(f"No skill directories (containing SKILL.md) found under {target_path}\n")
            sys.exit(1)

        results = []
        all_valid = True
        for sdir in skill_dirs:
            res = validate_skill(
                sdir,
                siblings_dir=args.siblings_dir or target_path,
                check_sibling_collisions=not args.no_collisions,
            )
            if not res["valid"]:
                all_valid = False
            results.append({"path": str(sdir), **res})

        if args.json:
            print(json.dumps({"valid": all_valid, "total_skills": len(results), "results": results}, indent=2))
        else:
            passed = sum(1 for r in results if r["valid"])
            total_errs = sum(len(r["errors"]) for r in results)
            total_warns = sum(len(r["warnings"]) for r in results)
            print(f"Repository Skill Audit: {passed}/{len(results)} PASSED ({total_errs} errors, {total_warns} warnings)\n")
            for r in results:
                tag = "PASS" if r["valid"] else "FAIL"
                name = r["details"].get("name") or Path(r["path"]).name
                blines = r["details"].get("body_lines", "?")
                print(f"[{tag}] {name} (body={blines}L, errors={len(r['errors'])}, warnings={len(r['warnings'])})")
                for err in r["errors"]:
                    print(f"    [ERROR] {err}")
                for warn in r["warnings"]:
                    print(f"    [WARN]  {warn}")
        sys.exit(0 if all_valid else 1)

    result = validate_skill(
        target_path,
        siblings_dir=args.siblings_dir,
        check_sibling_collisions=not args.no_collisions,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_human_report(target_path, result)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
