import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from behave import given, then, when

LOOP = (
    Path(__file__).resolve().parents[3]
    / "skills/code-discipline/scripts/quality_loop.py"
)
SKILL = LOOP.parent.parent


@given("a temporary repository with {validity} Python")
def repository(context, validity):
    context.repository = tempfile.TemporaryDirectory()
    context.root = Path(context.repository.name)
    contents = {"valid": "answer = 42\n", "invalid": "answer =\n"}
    (context.root / "example.py").write_text(contents[validity])
    quality = context.root / ".quality"
    quality.mkdir()
    config = {
        "format_lint": {
            "enabled": True,
            "required": True,
            "commands": [[sys.executable, "-m", "py_compile", "example.py"]],
        },
        "tools": {"auto_install": False},
    }
    (quality / "quality-gate.json").write_text(json.dumps(config))


@when("I run its lint gate")
def run_lint(context):
    context.result = subprocess.run(
        [sys.executable, str(LOOP), "--root", str(context.root), "--lint"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


@given("the project enables {choice}")
def gate_choices(context, choice):
    path = context.root / ".quality/quality-gate.json"
    config = json.loads(path.read_text())
    keys = "format_lint types contracts quality test_execution cognitive duplication slow_tests error_handling test_integrity smoke gherkin file_loc dead_code flaky mutation dependency_health dependencies secrets vulnerabilities hotspots extensibility scope".split()
    config["gates"] = dict.fromkeys(keys, False)
    config["gates"]["format_lint"] = choice == "only lint"
    path.write_text(json.dumps(config))


@when("I run its complete project report")
def run_full(context):
    context.result = subprocess.run(
        [sys.executable, str(LOOP), "--root", str(context.root), "--no-install"],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


@then("disabled gates are reported as OFF")
def off_gates(context):
    state = json.loads((context.root / ".quality/quality-gate-state.json").read_text())
    rows = {row["key"]: row for row in state["gates"]}
    assert rows["gherkin"]["status"] == "off"
    assert rows["quality"]["status"] == "off"


@when("I install the local skill for both agents")
def local_install(context):
    context.original_config = (context.root / ".quality/quality-gate.json").read_bytes()
    context.result = subprocess.run(
        [str(SKILL / "scripts/quality"), "--install", "--root", str(context.root)],
        env={
            **os.environ,
            "QUALITY_PYTHON": sys.executable,
            "CODE_DISCIPLINE_INSTALL_REGISTRY": str(
                context.root / "install-registry.json"
            ),
        },
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


@then("both agents read the complete local skill")
def installed_skill(context):
    target = context.root / ".agents/skills/code-discipline"
    assert (
        context.root / ".claude/skills/code-discipline"
    ).resolve() == target.resolve()
    for relative in (
        "SKILL.md",
        "references/project-setup-chat.md",
        "scripts/install_local.py",
    ):
        assert (target / relative).read_bytes() == (SKILL / relative).read_bytes()


@then("installation directs the agent to continue setup in this chat")
def setup_handoff(context):
    assert "continue setup in this chat, before handoff" in context.result.stdout


@then("installation leaves project settings unchanged")
def preserved_project(context):
    assert (
        context.root / ".quality/quality-gate.json"
    ).read_bytes() == context.original_config
    assert not (context.root / ".quality/quality-thresholds.json").exists()
    assert not (context.root / ".git").exists()


@then("the command exits with {code:d}")
def command_exit(context, code):
    assert context.result.returncode == code, (
        context.result.stdout + context.result.stderr
    )


@then("the status is {status}")
def status_line(context, status):
    assert f"QUALITY_LOOP={status}\n" in context.result.stdout, context.result.stdout


@then("the report does not certify the repository")
def no_certification(context):
    state = json.loads((context.root / ".quality/quality-gate-state.json").read_text())
    assert state["certified"] is False
