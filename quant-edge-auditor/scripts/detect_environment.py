#!/usr/bin/env python3
"""
detect_environment.py - Runtime Discovery of Available Models and Skills.

Inspects the current runtime environment to determine:
1. Available agent skills (user config, builtin, workspace).
2. Available model tiers (reasoning, code, fast).
3. Recommended delegation configuration for each subagent stage.

Outputs clean JSON to stdout for agent orchestration.
"""

import argparse
import json
import os
import sys
from pathlib import Path


KNOWN_SKILL_DIRS = [
    Path.home() / ".gemini" / "config" / "skills",
    Path.home() / ".gemini" / "antigravity-cli" / "builtin" / "skills",
    Path("/home/orbiter/workspace/skills-enzebot"),
]

# Model Tier Classification Rules
TIER_RULES = {
    "tier1_deep_reasoning": [
        "pro", "deepthink", "opus", "gemini-1.5-pro", "gemini-2.5-pro",
        "gemini-3.8-pro", "claude-3-5-sonnet", "o1", "o3"
    ],
    "tier2_code_execution": [
        "flash", "medium", "inherit", "gemini-3.8-flash", "gemini-2.5-flash",
        "sonnet", "gpt-4o", "gpt-4o-mini"
    ],
    "tier3_fast_formatting": [
        "flash_lite", "flash-lite", "haiku", "gemini-1.5-flash-8b", "gemini-2.5-flash-lite"
    ]
}


def discover_skills():
    """Scan file system for available skills and extract metadata."""
    found_skills = {}
    for base_dir in KNOWN_SKILL_DIRS:
        if not base_dir.exists() or not base_dir.is_dir():
            continue
        for child in base_dir.iterdir():
            if child.is_dir():
                skill_md = child / "SKILL.md"
                if skill_md.exists() and child.name not in found_skills:
                    found_skills[child.name] = {
                        "name": child.name,
                        "path": str(child),
                        "skill_file": str(skill_md),
                    }
    return found_skills


def classify_model(model_name: str) -> str:
    """Classify a model name into tier1, tier2, or tier3."""
    clean = model_name.lower().strip()
    for tier, patterns in TIER_RULES.items():
        if any(p in clean for p in patterns):
            return tier
    return "tier2_code_execution"


def get_stage_recommendations(skills: dict, current_model: str):
    """Generate subagent assignments for each of the 4 audit stages."""
    has_competing_hypo = "competing-hypothesis" in skills
    has_planning = "planning-with-files" in skills
    has_human_readable = "human-readable" in skills

    return {
        "stage_1_forensic_integrity": {
            "name": "Forensic Causal Integrity & As-Of Verification",
            "recommended_model_tier": "tier2_code_execution",
            "recommended_skills": ["planning-with-files"] if has_planning else [],
            "bundled_script": "scripts/asof_leakage_verifier.py",
            "rationale": "High-fidelity script execution and schema validation."
        },
        "stage_2_statistical_calibration": {
            "name": "Probability Calibration & Murphy Decomposition",
            "recommended_model_tier": "tier2_code_execution",
            "recommended_skills": [],
            "bundled_script": "scripts/brier_murphy_decomp.py",
            "rationale": "Deterministic numerical decomposition and quantile calibration."
        },
        "stage_3_market_microstructure": {
            "name": "Market Microstructure & Shin De-vigging",
            "recommended_model_tier": "tier2_code_execution",
            "recommended_skills": [],
            "bundled_script": "scripts/devig_market.py",
            "rationale": "Root-finding Shin algorithm and benchmark CLV calculation."
        },
        "stage_4_adversarial_stress": {
            "name": "Adversarial Red-Teaming & Deflated Sharpe",
            "recommended_model_tier": "tier1_deep_reasoning",
            "recommended_skills": (
                (["competing-hypothesis"] if has_competing_hypo else []) +
                (["human-readable"] if has_human_readable else [])
            ),
            "bundled_script": "scripts/bootstrap_stress_test.py",
            "rationale": "Deep counter-factual reasoning, multi-hypothesis testing, and falsification."
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Detect runtime environment models, skills, and generate subagent assignment plans."
    )
    parser.add_argument(
        "--current-model",
        default=os.environ.get("ANTIGRAVITY_MODEL", "inherit"),
        help="Current model name or string identifier"
    )
    parser.add_argument(
        "--stage",
        type=int,
        choices=[1, 2, 3, 4],
        help="Filter output recommendations to a specific audit stage (1-4)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a human-readable summary instead of JSON"
    )
    args = parser.parse_args()

    skills = discover_skills()
    curr_tier = classify_model(args.current_model)
    stages = get_stage_recommendations(skills, args.current_model)

    output_data = {
        "runtime": {
            "current_model": args.current_model,
            "current_model_tier": curr_tier,
            "detected_skills_count": len(skills),
            "detected_skills": sorted(list(skills.keys())),
        },
        "stage_recommendations": stages if not args.stage else {
            f"stage_{args.stage}": list(stages.values())[args.stage - 1]
        }
    }

    if args.summary:
        print(f"Runtime Model: {args.current_model} (Tier: {curr_tier})")
        print(f"Detected Skills ({len(skills)}): {', '.join(sorted(skills.keys()))}\n")
        print("Stage Allocations:")
        for key, info in stages.items():
            print(f"  [{key}] {info['name']}")
            print(f"    - Tier: {info['recommended_model_tier']}")
            print(f"    - Script: {info['bundled_script']}")
            print(f"    - Recommended Skills: {info['recommended_skills'] or 'None'}")
    else:
        print(json.dumps(output_data, indent=2))


if __name__ == "__main__":
    main()
