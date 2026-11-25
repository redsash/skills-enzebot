"""Persisted stdlib regression test suite for skills-enzebot."""

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_py(rel_script: str, args: list, stdin_text: str = None, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    """Execute a repository Python script and return its CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / rel_script)] + args,
        input=stdin_text,
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )


class TestRepoSkillsValidation(unittest.TestCase):
    def test_validate_all_skills_zero_warnings(self):
        proc = run_py("skill-architect/scripts/validate_skill.py", ["--all", ".", "--json"])
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        report = json.loads(proc.stdout)
        self.assertTrue(report["valid"])
        self.assertEqual(report["total_skills"], 11)
        for item in report["results"]:
            name = item["details"].get("name", item["path"])
            self.assertEqual(item["errors"], [], f"{name} errors: {item['errors']}")
            self.assertEqual(item["warnings"], [], f"{name} warnings: {item['warnings']}")

    def test_all_skills_have_evals_and_canonical_trigger_queries(self):
        skill_dirs = sorted(p.parent for p in REPO_ROOT.glob("*/SKILL.md"))
        self.assertEqual(len(skill_dirs), 11)
        for sdir in skill_dirs:
            evals_path = sdir / "evals" / "evals.json"
            tq_path = sdir / "evals" / "trigger_queries.json"
            self.assertTrue(evals_path.is_file(), f"Missing {evals_path}")
            self.assertTrue(tq_path.is_file(), f"Missing {tq_path}")
            tq_data = json.loads(tq_path.read_text(encoding="utf-8"))
            self.assertIsInstance(tq_data, list, f"{tq_path} must be a top-level array")
            self.assertTrue(any(q.get("should_trigger") is True for q in tq_data), str(tq_path))
            self.assertTrue(any(q.get("should_trigger") is False for q in tq_data), str(tq_path))

    def test_mermaid_diagrams_valid(self):
        for sdir in sorted(p.parent for p in REPO_ROOT.glob("*/SKILL.md")):
            proc = run_py("skill-architect/scripts/lint_mermaid.py", [str(sdir)])
            self.assertEqual(proc.returncode, 0, f"{sdir.name}: {proc.stdout}\n{proc.stderr}")

    def test_validate_skill_negative_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "test-bad-skill"
            (bad / "scripts").mkdir(parents=True)
            (bad / "evals").mkdir(parents=True)
            (bad / "SKILL.md").write_text(
                "---\n"
                "name: test-bad-skill\n"
                "description: >-\n"
                "  Audits widgets cleanly. Use when auditing widgets. Do not use for other things.\n"
                "taxonomy:\n"
                "  phase: [critique]\n"
                "  modality: [harness]\n"
                "  domain: [software-engineering]\n"
                "---\n\n# Bad Skill\nRun `python3 test-bad-skill/scripts/run.py --help`.\n",
                encoding="utf-8",
            )
            script_p = bad / "scripts" / "run.py"
            script_p.write_text("#!/usr/bin/env python3\nimport argparse\nP = '/home/realperson/foo'\n", encoding="utf-8")
            script_p.chmod(0o755)
            (bad / "evals" / "evals.json").write_text(
                json.dumps({"skill_name": "test-bad-skill", "evals": [{"id": 1, "prompt": "Test", "files": ["evals/files/missing.csv"], "assertions": ["Pass"]}]}),
                encoding="utf-8",
            )
            (bad / "evals" / "trigger_queries.json").write_text(
                json.dumps({"skill_name": "test-bad-skill", "queries": [{"query": "test", "should_trigger": True}]}),
                encoding="utf-8",
            )
            proc = run_py("skill-architect/scripts/validate_skill.py", ["--no-collisions", "--json", str(bad)])
            self.assertEqual(proc.returncode, 1)
            res = json.loads(proc.stdout)
            errs = "\n".join(res["errors"])
            warns = "\n".join(res["warnings"])
            self.assertIn("Hardcoded absolute home path", errs)
            self.assertIn("missing fixture file", errs)
            self.assertIn("Missing 'metadata'", warns)
            self.assertIn("Repo-prefixed script path", warns)
            self.assertIn("top-level JSON array", warns)


class TestEngineeringLog(unittest.TestCase):
    def test_end_to_end_lifecycle(self):
        script = "engineering-log/scripts/eng_log.py"
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store"
            self.assertEqual(run_py(script, ["init", "--dir", str(store)]).returncode, 0)

            base_payload = {
                "title": "Root OAuth setup",
                "summary": "A" * 200,
                "project": "auth-gw",
                "session_shape": "build",
                "outcome": "resolved",
                "shelf_life": "evergreen",
                "actor": {"conversation_id": "conv-1"},
                "context": {"technologies": ["python", "oauth2"], "concepts": ["pkce"]},
                "rule_candidates": [
                    {"scope": "repo", "rule": "Never bypass refreshSingleFlight()", "rationale": "Token rotation"},
                    {"scope": "global", "rule": "Keep timeout > retry delay", "rationale": "Avoid retry storms"},
                ],
            }

            dry = run_py(script, ["write", "--dir", str(store), "--cwd", ".", "--dry-run", "--input", "-"], json.dumps(base_payload))
            self.assertEqual(dry.returncode, 0, dry.stderr)
            d_dry = json.loads(dry.stdout)
            self.assertTrue(d_dry["auto_harvested_git"])
            self.assertNotIn("markdown_preview", d_dry)

            dry_v = run_py(script, ["write", "--dir", str(store), "--cwd", ".", "--dry-run", "--verbose", "--input", "-"], json.dumps(base_payload))
            self.assertEqual(dry_v.returncode, 0, dry_v.stderr)
            self.assertIn("markdown_preview", json.loads(dry_v.stdout))

            bad_payload = dict(base_payload, belief_revisions=[{"assumed": "x"}])
            bad_proc = run_py(script, ["write", "--dir", str(store), "--dry-run", "--input", "-"], json.dumps(bad_payload))
            self.assertEqual(bad_proc.returncode, 1)
            self.assertIn("belief_revisions[0]", bad_proc.stderr)

            w1 = run_py(script, ["write", "--dir", str(store), "--input", "-"], json.dumps(base_payload))
            self.assertEqual(w1.returncode, 0, w1.stderr)
            e1 = json.loads(w1.stdout)["id"]

            dup = run_py(script, ["write", "--dir", str(store), "--input", "-"], json.dumps(base_payload))
            self.assertEqual(dup.returncode, 1)
            self.assertIn("already exists for conversation_id", dup.stderr)

            dup_payload = dict(base_payload, title="Duplicate conv followup", rule_candidates=[])
            allow_dup = run_py(script, ["write", "--dir", str(store), "--allow-duplicate", "--input", "-"], json.dumps(dup_payload))
            self.assertEqual(allow_dup.returncode, 0, allow_dup.stderr)

            # agy-start must NOT leak auth-gw into unrelated repo skills-enzebot
            hk_default = run_py(script, ["hook", "--dir", str(store), "--mode", "agy-start"], json.dumps({"cwd": str(REPO_ROOT)}))
            self.assertEqual(json.loads(hk_default.stdout), {})

            hk_global = run_py(
                script,
                ["hook", "--dir", str(store), "--mode", "agy-start", "--include-global-rules"],
                json.dumps({"cwd": str(REPO_ROOT)}),
            )
            msg = json.loads(hk_global.stdout)["injectSteps"][0]["systemMessage"]["systemMessage"]
            self.assertIn("Global guardrails:", msg)
            self.assertIn("Keep timeout > retry delay", msg)
            self.assertNotIn("Never bypass refreshSingleFlight()", msg)

            # Linked entries for bidirectional depth-2 graph traversal
            e2 = json.loads(
                run_py(
                    script,
                    ["write", "--dir", str(store), "--input", "-"],
                    json.dumps({
                        "title": "Fix refresh race",
                        "summary": "Serialized token refreshes.",
                        "project": "auth-gw",
                        "session_shape": "diagnostic",
                        "outcome": "resolved",
                        "links": [{"rel": "builds_on", "target_id": e1}],
                    }),
                ).stdout
            )["id"]
            e3 = json.loads(
                run_py(
                    script,
                    ["write", "--dir", str(store), "--input", "-"],
                    json.dumps({
                        "title": "Mobile refresh fix",
                        "summary": "Same race in mobile client.",
                        "project": "mobile-app",
                        "session_shape": "diagnostic",
                        "outcome": "resolved",
                        "links": [{"rel": "same_root_cause", "target_id": e2}],
                    }),
                ).stdout
            )["id"]

            gr = json.loads(run_py(script, ["graph", "--dir", str(store), "--id", e1, "--depth", "2"]).stdout)
            hops = {n["id"]: n["hop"] for n in gr["nodes"]}
            self.assertEqual(hops, {e1: 0, e2: 1, e3: 2})

            # Graduate repo rule via append
            app = run_py(
                script,
                ["append", "--dir", str(store), "--id", e1, "--input", "-"],
                json.dumps({"promoted_rules": ["Never bypass refreshSingleFlight()"]}),
            )
            self.assertEqual(app.returncode, 0, app.stderr)
            idx_txt = (store / "INDEX.md").read_text(encoding="utf-8")
            self.assertIn("## Graph Hubs & Concept Map", idx_txt)
            self.assertNotIn("A" * 141, idx_txt)
            self.assertNotIn("Never bypass refreshSingleFlight()", idx_txt)

            # Secret redaction check
            sec = json.loads(
                run_py(
                    script,
                    ["write", "--dir", str(store), "--input", "-"],
                    json.dumps({
                        "title": "Secret scrubbing test",
                        "summary": "Token ghp_AbCdEfGhIjKlMnOpQrStUvWxYz123456 leaked",
                        "project": "sec-test",
                        "session_shape": "diagnostic",
                        "outcome": "resolved",
                    }),
                ).stdout
            )
            self.assertGreaterEqual(sec["redactions_applied"], 1)

            # Overflow > 50 entries builds indexes/by-project/
            for i in range(47):
                r = run_py(
                    script,
                    ["write", "--dir", str(store), "--input", "-"],
                    json.dumps({
                        "title": f"Bulk {i}",
                        "summary": f"Bulk summary {i}",
                        "project": "bulk-proj",
                        "session_shape": "build",
                        "outcome": "resolved",
                    }),
                )
                self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Showing latest 50 of", (store / "INDEX.md").read_text(encoding="utf-8"))
            self.assertTrue((store / "indexes" / "by-project" / "bulk-proj.md").is_file())

            val = run_py(script, ["validate", "--dir", str(store)])
            self.assertEqual(val.returncode, 0, val.stdout)


class TestResearchJournaler(unittest.TestCase):
    def test_dry_run_templates_and_scrubbing(self):
        script = "research-journaler/scripts/log_research.py"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            dry_init = json.loads(run_py(script, ["init-repo", "--base-dir", str(base), "--dry-run"]).stdout)
            self.assertTrue(dry_init["dry_run"])
            self.assertFalse((base / "docs").exists())

            run_py(script, ["init-repo", "--base-dir", str(base)])
            self.assertTrue((base / "docs" / "templates" / "prompt-library-template.json").is_file())
            self.assertFalse((base / "docs" / "templates" / "prompt-library-template.md").exists())

            dry_entry = json.loads(run_py(script, ["new-entry", "--base-dir", str(base), "--topic", "spike", "--dry-run"]).stdout)
            self.assertFalse((base / dry_entry["entry_path"]).exists())

            entry = json.loads(run_py(script, ["new-entry", "--base-dir", str(base), "--topic", "spike"]).stdout)
            dry_prompt = json.loads(
                run_py(script, ["add-prompt", "--base-dir", str(base), "--topic", "spike", "--prompt", "Dry ghp_1234567890abcdef123456", "--dry-run"]).stdout
            )
            self.assertEqual(dry_prompt["redactions_applied"], 1)
            self.assertEqual(len(json.loads((base / entry["prompts_path"]).read_text(encoding="utf-8"))["prompts"]), 0)

            real_prompt = json.loads(
                run_py(script, ["add-prompt", "--base-dir", str(base), "--topic", "spike", "--prompt", "Run ghp_1234567890abcdef123456"]).stdout
            )
            self.assertEqual(real_prompt["redactions_applied"], 1)
            prompts_txt = (base / entry["prompts_path"]).read_text(encoding="utf-8")
            self.assertNotIn("ghp_1234567890abcdef123456", prompts_txt)
            self.assertIn("[REDACTED:github_token]", prompts_txt)

            listed = json.loads(run_py(script, ["list", "--base-dir", str(base)]).stdout)
            self.assertEqual(len(listed["entries"]), 1)


class TestQuantEdgeAuditor(unittest.TestCase):
    def test_leakage_and_run_exit_propagation(self):
        fixture = "quant-edge-auditor/evals/files/sample_bets.csv"
        p_leak = run_py("quant-edge-auditor/scripts/asof_leakage_verifier.py", [fixture, "--json"])
        self.assertEqual(p_leak.returncode, 1)
        d_leak = json.loads(p_leak.stdout)
        self.assertEqual(d_leak["violation_count"], 2)
        self.assertFalse(d_leak["closing_odds_match_stats"]["retroactive_odds_leakage"])

        with tempfile.TemporaryDirectory() as tmp:
            retro = Path(tmp) / "retro.csv"
            with open(retro, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["game_id", "knowledge_time", "prediction_time", "event_start_time", "placed_odds", "closing_odds"])
                for i in range(6):
                    w.writerow([f"g{i}", "2026-09-10T12:00:00Z", "2026-09-10T14:00:00Z", "2026-09-10T20:00:00Z", "1.91", "1.91"])
            p_retro = run_py("quant-edge-auditor/scripts/asof_leakage_verifier.py", [str(retro), "--json"])
            self.assertEqual(p_retro.returncode, 1)
            self.assertTrue(json.loads(p_retro.stdout)["closing_odds_match_stats"]["retroactive_odds_leakage"])

        p_run = run_py("quant-edge-auditor/scripts/run.py", [fixture, "--trials", "25", "--odds", "-450", "+350", "--json"])
        self.assertEqual(p_run.returncode, 1)
        d_run = json.loads(p_run.stdout)
        self.assertFalse(d_run["overall_passed"])
        self.assertEqual(d_run["overall_verdict"], "REJECTED_LEAKAGE")

    def test_calibration_devig_and_bootstrap(self):
        fixture = "quant-edge-auditor/evals/files/sample_bets.csv"
        p_cal = run_py("quant-edge-auditor/scripts/brier_murphy_decomp.py", [fixture, "--json"])
        self.assertEqual(p_cal.returncode, 0, p_cal.stderr)
        self.assertIn("overall_brier_score", json.loads(p_cal.stdout))

        p_dev = run_py("quant-edge-auditor/scripts/devig_market.py", ["-450", "+350", "--method", "all", "--json"])
        self.assertEqual(p_dev.returncode, 0, p_dev.stderr)
        dev = json.loads(p_dev.stdout)["devigged"]
        for m in ("shin", "power", "log_odds", "proportional"):
            self.assertAlmostEqual(sum(dev[m]["true_probabilities"]), 1.0, places=3)
        self.assertGreater(dev["log_odds"]["true_probabilities"][0], dev["proportional"]["true_probabilities"][0])

        args = [fixture, "--trials", "25", "--sims", "150", "--seed", "42", "--json"]
        b1 = run_py("quant-edge-auditor/scripts/bootstrap_stress_test.py", args)
        b2 = run_py("quant-edge-auditor/scripts/bootstrap_stress_test.py", args)
        self.assertEqual(b1.returncode, 0, b1.stderr)
        self.assertEqual(b1.stdout, b2.stdout)
        overfit = json.loads(b1.stdout)["overfitting_and_significance"]
        self.assertIn("sample_skewness", overfit)
        self.assertIn("sample_kurtosis", overfit)


class TestDiscordWebhookValidator(unittest.TestCase):
    def test_ci_deploy_example_validation(self):
        md = (REPO_ROOT / "discord-webhook-script-writer" / "examples" / "ci-cd-deploy-notify.md").read_text(encoding="utf-8")
        match = re.search(r"```bash\n(.*?)\n```", md, re.S)
        self.assertIsNotNone(match)
        with tempfile.TemporaryDirectory() as tmp:
            sh_path = Path(tmp) / "ci-deploy-notify.sh"
            sh_path.write_text(match.group(1) + "\n", encoding="utf-8")
            proc = run_py(
                "discord-webhook-script-writer/scripts/validate_script.py",
                [str(sh_path), "--sample-args", "--status success", "--json"],
            )
            res = json.loads(proc.stdout)
            self.assertTrue(res["structure"]["passed"])
            self.assertEqual(res["dry_run"]["returncode"], 0)
            self.assertTrue(res["dry_run"]["schema_validation"]["valid"])
            if res["shellcheck"]["tool_available"]:
                self.assertEqual(proc.returncode, 0, proc.stdout)
                self.assertTrue(res["overall_passed"])


class TestCadFloorplanDesigner(unittest.TestCase):
    def test_unified_spec_across_scripts(self):
        cad_scripts_dir = str(REPO_ROOT / "cad-floorplan-designer" / "scripts")
        if cad_scripts_dir not in sys.path:
            sys.path.insert(0, cad_scripts_dir)
        from audit_spatial_ux import DEMO_LAYOUT
        from render_floorplan_svg import DEFAULT_LAYOUT_SPEC

        with tempfile.TemporaryDirectory() as tmp:
            for idx, layout in enumerate((DEMO_LAYOUT, DEFAULT_LAYOUT_SPEC)):
                spec_path = Path(tmp) / f"spec_{idx}.json"
                svg_path = Path(tmp) / f"plan_{idx}.svg"
                spec_path.write_text(json.dumps(layout), encoding="utf-8")

                p_aud = run_py("cad-floorplan-designer/scripts/audit_spatial_ux.py", ["--spec", str(spec_path), "--json"])
                self.assertEqual(p_aud.returncode, 0, p_aud.stderr)
                self.assertTrue(json.loads(p_aud.stdout)["is_valid"])

                p_cost = run_py("cad-floorplan-designer/scripts/estimate_construction_cost.py", ["--spec", str(spec_path), "--json"])
                self.assertEqual(p_cost.returncode, 0, p_cost.stderr)
                self.assertGreater(json.loads(p_cost.stdout)["confidence_range"]["expected_median_usd"], 0)

                p_svg = run_py("cad-floorplan-designer/scripts/render_floorplan_svg.py", ["--spec", str(spec_path), "-o", str(svg_path)])
                self.assertEqual(p_svg.returncode, 0, p_svg.stderr)
                svg_txt = svg_path.read_text(encoding="utf-8")
                self.assertIn("<svg", svg_txt)
                self.assertIn('<g id="circulation-paths">', svg_txt)

    def test_validate_cmu_grid_strict(self):
        bad = run_py("cad-floorplan-designer/scripts/validate_cmu_grid.py", ["--check-spans", "24' 5\"", "--strict", "--json"])
        self.assertEqual(bad.returncode, 1)
        good = run_py("cad-floorplan-designer/scripts/validate_cmu_grid.py", ["--check-spans", "24' 0\"", "--strict", "--json"])
        self.assertEqual(good.returncode, 0)


if __name__ == "__main__":
    unittest.main()
