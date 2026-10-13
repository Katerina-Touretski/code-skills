"""Project gate choices control execution and completion evidence."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_repo_quality_gate import gate


class ProjectGateChoicesTests(unittest.TestCase):
    def test_full_run_respects_saved_choices_without_running_disabled_commands(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "example.py").write_text("answer = 42\n")
            quality = root / ".quality"
            quality.mkdir()
            choices = dict.fromkeys(
                set(gate.SELECTABLE_CHECKS.values()) | {"scope"}, False
            )
            choices["format_lint"] = True
            config = {
                "gates": choices,
                "format_lint": {
                    "enabled": False,
                    "required": False,
                    "commands": [[sys.executable, "-m", "py_compile", "example.py"]],
                },
                "test": {
                    "command": [
                        sys.executable,
                        "-c",
                        "raise AssertionError('disabled test ran')",
                    ]
                },
                "tools": {"auto_install": False, "cache_dir": str(root / "tools")},
            }
            path = quality / "quality-gate.json"
            path.write_text(json.dumps(config))
            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        Path(__file__).resolve().parents[1]
                        / "skills/code-discipline/scripts/quality_loop.py"
                    ),
                    "--root",
                    str(root),
                    "--no-install",
                ],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("QUALITY_LOOP=PASS\n", result.stdout)
            state = json.loads((quality / "quality-gate-state.json").read_text())
            self.assertTrue(state["certified"])
            outcomes = {item["key"]: item for item in state["gates"]}
            self.assertEqual(outcomes["format_lint"]["status"], "pass")
            self.assertEqual(outcomes["gherkin"]["status"], "off")
            self.assertEqual(outcomes["quality"]["status"], "off")
            self.assertEqual(outcomes["vulnerabilities"]["status"], "off")

    def test_invalid_choices_fail_before_checks(self):
        for choices in (None, [], {"typo": True}, {"quality": "false"}, {"quality": 0}):
            with self.subTest(choices=choices), self.assertRaises(ValueError):
                gate.project_gate_choices({"gates": choices})
        self.assertEqual(gate.project_gate_choices({}), {})

    def test_disabled_gates_stay_off_in_focused_runs(self):
        selection = gate.project_gate_selection(
            {"format_lint": False}, gate.gate_selection(["lint"])
        )
        self.assertFalse(selection.wants("format_lint"))
        self.assertFalse(selection.wants("quality"))
        self.assertTrue(selection.partial)
        results = gate.project_gate_results(
            [gate.skipped_check("format_lint", "Lint")], selection
        )
        self.assertTrue(results[0].off)
        self.assertFalse(results[0].skipped)

    def test_enabled_gates_override_legacy_settings_without_mutating_config(self):
        config = gate.default_config()
        config["flaky_tests"]["enabled"] = False
        choices = {"flaky": True, "gherkin": False, "cognitive": True}
        configured = gate.project_gate_config(config, choices)
        self.assertTrue(configured["flaky_tests"]["enabled"])
        self.assertTrue(configured["flaky_tests"]["required"])
        self.assertFalse(config["flaky_tests"]["enabled"])
        self.assertEqual(configured["gherkin"], config["gherkin"])

    def test_all_off_report_cannot_certify_or_claim_selected_success(self):
        report = gate.AnalysisReport("", "", [], [], [], [], [], [], [])
        report.gates = [
            gate.GateResult(
                "quality", "Quality", True, "Off", applicable=False, off=True
            )
        ]
        self.assertFalse(report.passed)
        self.assertFalse(report.selected_passed)
        report.mode = "fast"
        self.assertFalse(report.ready_for_full)

    def test_choices_are_project_local_and_defaults_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "quality-gate.json"
            path.write_text(json.dumps({"gates": {"gherkin": False}}))
            chosen, _ = gate.load_config(path)
            other, _ = gate.load_config(None)
            self.assertFalse(
                gate.project_gate_selection(
                    gate.project_gate_choices(chosen), gate.GateSelection()
                ).wants("gherkin")
            )
            self.assertTrue(
                gate.project_gate_selection(
                    gate.project_gate_choices(other), gate.GateSelection()
                ).wants("gherkin")
            )

    def test_full_selection_accepts_enabled_gates(self):
        selected = gate.project_gate_selection(
            {"format_lint": True}, gate.GateSelection()
        )
        self.assertTrue(selected.wants("format_lint"))
        self.assertFalse(selected.partial)

    def test_configuration_only_initialization_does_not_run_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "example.py").write_text(
                "raise RuntimeError('do not run before choices')\n"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(gate.__file__)),
                    "--root",
                    str(root),
                    "--init",
                ],
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((root / ".quality/quality-gate.json").exists())
            self.assertTrue((root / ".quality/quality-thresholds.json").exists())
            self.assertFalse((root / ".quality/quality-gate-state.json").exists())
            self.assertFalse((root / ".quality/quality-gate-report.html").exists())


if __name__ == "__main__":
    unittest.main()
