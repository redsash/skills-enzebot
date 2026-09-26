#!/usr/bin/env python3
"""
Orchestration engine for the research-journaler skill.

Manages repository initialization, chronological entry scaffolding,
prompt logging, and environment metadata capture.

Usage:
    python3 scripts/log_research.py init-repo [OPTIONS]
    python3 scripts/log_research.py new-entry --topic <slug> [OPTIONS]
    python3 scripts/log_research.py add-prompt --topic <slug> --prompt <text> [OPTIONS]
    python3 scripts/log_research.py list [OPTIONS]
"""

import sys
import os
import re
import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


CATEGORIES = ["software-engineering", "data-analysis", "academic-research", "general"]


def slugify(text: str) -> str:
    """Convert text into a clean URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def get_git_info(base_dir: Path) -> dict:
    """Extract git branch and commit hash if inside a git repo."""
    info = {"is_git": False, "branch": None, "commit": None}
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=base_dir, stderr=subprocess.DEVNULL, text=True
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=base_dir, stderr=subprocess.DEVNULL, text=True
        ).strip()
        info.update({"is_git": True, "branch": branch, "commit": commit})
    except Exception:
        pass
    return info


def capture_environment_metadata(category: str, base_dir: Path) -> dict:
    """Capture environment context tailored to research category."""
    env = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "git": get_git_info(base_dir),
    }

    if category == "software-engineering":
        # Check node, virtualenv, active branch
        env["in_venv"] = sys.prefix != sys.base_prefix
        try:
            node_ver = subprocess.check_output(["node", "--version"], stderr=subprocess.DEVNULL, text=True).strip()
            env["node_version"] = node_ver
        except Exception:
            env["node_version"] = None

    elif category == "data-analysis":
        # Check available scientific packages without heavy imports
        installed = []
        for pkg in ["pandas", "numpy", "polars", "scipy", "duckdb"]:
            try:
                __import__(pkg)
                installed.append(pkg)
            except ImportError:
                pass
        env["data_libraries"] = installed

    elif category == "academic-research":
        env["sources_tracking"] = True

    return env


def init_repo(base_dir: Path, skill_dir: Path) -> dict:
    """Scaffold base journal repository structures and templates."""
    templates_dir = base_dir / "docs" / "templates"
    archives_dir = base_dir / "entries" / "archives"
    templates_dir.mkdir(parents=True, exist_ok=True)
    archives_dir.mkdir(parents=True, exist_ok=True)

    assets_templates = skill_dir / "assets" / "templates"
    created_files = []

    # Copy templates if not existing
    log_tmpl_src = assets_templates / "research-log-template.md"
    log_tmpl_dst = templates_dir / "research-log-template.md"
    if not log_tmpl_dst.exists() and log_tmpl_src.exists():
        shutil.copyfile(log_tmpl_src, log_tmpl_dst)
        created_files.append(str(log_tmpl_dst.relative_to(base_dir)))

    prompt_tmpl_src = assets_templates / "prompt-library-template.json"
    prompt_tmpl_dst = templates_dir / "prompt-library-template.md"
    if not prompt_tmpl_dst.exists() and prompt_tmpl_src.exists():
        shutil.copyfile(prompt_tmpl_src, prompt_tmpl_dst)
        created_files.append(str(prompt_tmpl_dst.relative_to(base_dir)))

    # .gitignore
    gitignore = base_dir / ".gitignore"
    gitignore_src = assets_templates / "gitignore-template.txt"
    if not gitignore.exists() and gitignore_src.exists():
        shutil.copyfile(gitignore_src, gitignore)
        created_files.append(".gitignore")

    # README.md
    readme = base_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Research Journal\n\n"
            "A structured, chronological repository of AI-assisted and empirical research sessions.\n\n"
            "## Structure\n"
            "- `entries/YYYY-MM/`: Monthly partitions of research sessions\n"
            "- `docs/templates/`: Blueprints for log files and prompt libraries\n"
            "- `entries/archives/`: Concluded or consolidated research collections\n",
            encoding="utf-8"
        )
        created_files.append("README.md")

    return {"status": "ok", "action": "init-repo", "created_files": created_files}


def find_entry_dir(base_dir: Path, topic_slug: str) -> Path:
    """Locate an existing entry directory for a topic slug across all months."""
    entries_root = base_dir / "entries"
    if not entries_root.exists():
        return None
    for month_dir in entries_root.iterdir():
        if month_dir.is_dir() and month_dir.name != "archives":
            for topic_dir in month_dir.iterdir():
                if topic_dir.is_dir() and topic_dir.name.endswith(f"_{topic_slug}"):
                    return topic_dir
    return None


def new_entry(base_dir: Path, skill_dir: Path, topic: str, category: str, title: str) -> dict:
    """Create a new chronological research entry directory."""
    slug = slugify(topic)
    if not slug:
        raise ValueError("Invalid topic: resulted in empty slug.")

    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    date_str = now.strftime("%Y-%m-%d")
    folder_name = f"{date_str}_{slug}"

    month_dir = base_dir / "entries" / month_str
    entry_dir = month_dir / folder_name

    outputs_dir = entry_dir / "outputs"
    sources_dir = entry_dir / "sources"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Touch .gitkeep so empty directories are preserved
    (outputs_dir / ".gitkeep").touch(exist_ok=True)
    (sources_dir / ".gitkeep").touch(exist_ok=True)

    # Prepare logs.md without clobbering existing content
    logs_file = entry_dir / "logs.md"
    created_log = False
    display_title = title if title else topic.replace("-", " ").title()

    if not logs_file.exists():
        assets_templates = skill_dir / "assets" / "templates"
        log_template_path = assets_templates / "research-log-template.md"
        if log_template_path.exists():
            tmpl_content = log_template_path.read_text(encoding="utf-8")
            log_content = tmpl_content.replace("[Topic Title]", display_title)
            log_content = log_content.replace("YYYY-MM-DD", date_str)
            log_content = log_content.replace("[software-engineering | data-analysis | academic-research]", category)
        else:
            log_content = f"# Research Log: {display_title}\n\n- **Date:** {date_str}\n- **Category:** {category}\n"

        logs_file.write_text(log_content, encoding="utf-8")
        created_log = True

    # Prepare prompts.json
    prompts_file = entry_dir / "prompts.json"
    created_prompts = False
    if not prompts_file.exists():
        env_meta = capture_environment_metadata(category, base_dir)
        prompts_data = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "topic": slug,
            "title": display_title,
            "date_created": date_str,
            "category": category,
            "environment": env_meta,
            "prompts": []
        }
        prompts_file.write_text(json.dumps(prompts_data, indent=2), encoding="utf-8")
        created_prompts = True

    return {
        "status": "ok",
        "action": "new-entry",
        "topic": slug,
        "entry_path": str(entry_dir.relative_to(base_dir)),
        "logs_path": str(logs_file.relative_to(base_dir)),
        "prompts_path": str(prompts_file.relative_to(base_dir)),
        "created_log": created_log,
        "created_prompts": created_prompts,
    }


def add_prompt(base_dir: Path, topic: str, user_prompt: str, model: str, response_summary: str, flags_json: str) -> dict:
    """Record an agent prompt iteration in prompts.json."""
    slug = slugify(topic)
    entry_dir = find_entry_dir(base_dir, slug)
    if not entry_dir:
        raise FileNotFoundError(f"No entry directory found for topic slug: {slug}")

    prompts_file = entry_dir / "prompts.json"
    if not prompts_file.exists():
        raise FileNotFoundError(f"prompts.json not found in {entry_dir}")

    with open(prompts_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    prompts_list = data.get("prompts", [])
    next_iteration = len(prompts_list) + 1

    parsed_flags = {}
    if flags_json:
        try:
            parsed_flags = json.loads(flags_json)
        except Exception:
            parsed_flags = {"raw": flags_json}

    new_record = {
        "iteration": next_iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model if model else "unspecified",
        "system_flags": parsed_flags,
        "user_prompt": user_prompt,
        "response_summary": response_summary if response_summary else "",
        "artifacts_generated": []
    }

    prompts_list.append(new_record)
    data["prompts"] = prompts_list

    # Atomic write
    temp_file = prompts_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    temp_file.replace(prompts_file)

    return {
        "status": "ok",
        "action": "add-prompt",
        "topic": slug,
        "iteration": next_iteration,
        "prompts_path": str(prompts_file.relative_to(base_dir))
    }


def list_entries(base_dir: Path) -> dict:
    """List all research journal entries in chronological order."""
    entries_root = base_dir / "entries"
    results = []
    if entries_root.exists():
        for month_dir in sorted(entries_root.iterdir()):
            if month_dir.is_dir() and month_dir.name != "archives":
                for entry_dir in sorted(month_dir.iterdir()):
                    if entry_dir.is_dir():
                        logs_exist = (entry_dir / "logs.md").exists()
                        prompts_exist = (entry_dir / "prompts.json").exists()
                        prompt_count = 0
                        if prompts_exist:
                            try:
                                with open(entry_dir / "prompts.json", "r", encoding="utf-8") as f:
                                    pdata = json.load(f)
                                    prompt_count = len(pdata.get("prompts", []))
                            except Exception:
                                pass
                        results.append({
                            "directory": str(entry_dir.relative_to(base_dir)),
                            "month": month_dir.name,
                            "folder": entry_dir.name,
                            "has_logs": logs_exist,
                            "prompt_iterations": prompt_count
                        })
    return {"status": "ok", "entries": results}


def main():
    parser = argparse.ArgumentParser(description="Research Journal automation and logging engine.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init-repo
    init_p = subparsers.add_parser("init-repo", help="Scaffold journal repository structures.")
    init_p.add_argument("--base-dir", default=".", help="Target workspace root")

    # new-entry
    new_p = subparsers.add_parser("new-entry", help="Scaffold a new research session entry.")
    new_p.add_argument("--topic", required=True, help="Topic slug or title")
    new_p.add_argument("--title", default=None, help="Human-readable title")
    new_p.add_argument("--category", choices=CATEGORIES, default="software-engineering", help="Research category")
    new_p.add_argument("--base-dir", default=".", help="Target workspace root")

    # add-prompt
    prompt_p = subparsers.add_parser("add-prompt", help="Append a prompt iteration to prompts.json.")
    prompt_p.add_argument("--topic", required=True, help="Topic slug")
    prompt_p.add_argument("--prompt", required=True, help="Prompt text")
    prompt_p.add_argument("--model", default="default", help="Model name or version")
    prompt_p.add_argument("--response-summary", default="", help="Summary of output or findings")
    prompt_p.add_argument("--flags", default=None, help="JSON string of system parameters/flags")
    prompt_p.add_argument("--base-dir", default=".", help="Target workspace root")

    # list
    list_p = subparsers.add_parser("list", help="List all chronological entries.")
    list_p.add_argument("--base-dir", default=".", help="Target workspace root")

    args = parser.parse_args()
    base_dir = Path(args.base_dir).resolve()
    skill_dir = Path(__file__).resolve().parent.parent

    try:
        if args.command == "init-repo":
            res = init_repo(base_dir, skill_dir)
        elif args.command == "new-entry":
            res = new_entry(base_dir, skill_dir, args.topic, args.category, args.title)
        elif args.command == "add-prompt":
            res = add_prompt(base_dir, args.topic, args.prompt, args.model, args.response_summary, args.flags)
        elif args.command == "list":
            res = list_entries(base_dir)
        else:
            parser.print_help()
            sys.exit(1)

        # Output structured result on stdout
        print(json.dumps(res, indent=2))
        sys.exit(0)

    except Exception as e:
        sys.stderr.write(f"Error in {args.command}: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
