# Guided project setup

Use this conversation the first time a user sets up quality gates for a project,
or when they ask to change that project's policy. Keep questions in chat; use the
runner's non-interactive mode rather than sending the user to a terminal wizard.

## Start with the project

The user can start with one plain request: "Install code-discipline here."
That request includes project setup. Read this guide before installation and
continue with the first setup question as soon as the installed copy is verified.
Do not stop with "Installed", ask "Want me to do setup next?", or require the
user to invoke the skill again. When installation is requested, handle its supported project-local steps; do not
make the normal user flow a list of terminal commands, symlink paths, JSON edits,
or metric names. Keep those implementation details in the agent's work. Report
an actual prerequisite or required session reload plainly if the environment
needs one. Do not claim installation or readiness before verifying it.

For a supplied local checkout, use its launcher; it selects a compatible Python
and calls the supported local installer without downloading the skill:

```bash
<checkout>/skills/code-discipline/scripts/quality --install --root <project>
```

This installs the local working tree for Codex and Claude Code, including
uncommitted edits, and verifies both. When retrying installation or replacing
an existing managed copy at the user's request, add `--update`; a retry does
not need another permission question. Never replace an unmanaged path.
Existing project policy and Git
metadata remain untouched by installation. After installation, read the
installed `SKILL.md` and this guide directly; agent discovery after restart is
separate from completing setup in this conversation. Keep this command and its
implementation details out of the normal user-facing flow.

Inspect the target root, manifests, existing check commands, and `.quality/`
files without running project code. Name the project; show its path only when
needed to distinguish the destination.
Reuse a policy with `setup.completed: true`. During installation, existing
settings without that marker are a starting recommendation, not proof that the
user completed this setup. Preserve their values and offer the two choices below.
If settings do not exist, say:

> I'll suggest checks and limits for this project. You can keep them or change
> them. I'll save your choices so we only need to do this once.

Ask about product or risk only when it changes a recommendation and cannot be
inferred from the repository. A library needs different runtime evidence from a
web app. Avoid an unrelated product questionnaire.

## Two choices for the normal setup

Prepare a complete recommended policy internally from project evidence and the
catalog below. Keep the user's experience short:

1. Show a short overview of the recommended checks, including what starts OFF
   and any material tooling, network, or runtime cost. Use everyday names such
   as "code checks", "tests", and "security checks", with a brief reason for
   each group. Ask: **"Use these checks, or customize them?"**
2. After the checks are chosen, show the suggested limits for them with plain
   explanations and units. For example, "90% test coverage means tests exercise
   at least 9 out of 10 executable lines in each function." State that errors
   must be fixed for enabled checks that require zero findings. Offer the full
   numeric summary as details, rather than making the user answer a long list
   of metric questions. Ask: **"Keep these limits, or adjust them?"**

Wait for the answers. Accepting the displayed recommendation explicitly accepts
that proposed group; it is not permission to apply unrelated defaults. Do not
ask separately about every gate and threshold on the recommended path. Do not
add another confirmation after both choices are complete. Save, verify, then
say: **"Saved for this project. Future work will use these settings."** Report
verification blockers instead of claiming readiness when checks cannot run.

If the user chooses customization, ask only about the settings they want to
change, one topic at a time. Every check remains individually switchable. Use
the detailed catalogs below for internal configuration and explanations on
request; do not show their JSON keys or full tables by default.

For ordinary coding, reuse existing settings without forced onboarding. During
installation, reuse a completed policy; otherwise finish the two setup choices
using existing settings as the starting recommendation. If the user asks to
review a completed policy, use the same two choices with that policy as the
starting recommendation.

## Choose gates, one topic at a time

Use this detailed path when the user chooses customization. For each topic,
explain what the checks catch, what evidence or tooling they
need, and the main time or maintenance cost. Recommend choices for this project,
then ask which checks to enable or disable. Offer a custom answer. Use one short
question at a time, or at most three closely related questions; do not present
the entire catalog as a form. Wait for each answer before moving to dependent
choices. Silence, a preselected option, and detection do not accept a policy.

Start with basic checks, then behavior, maintainability, architecture, security,
and extra test checks as needed. The groups below support the recommended policy
and individual customization. Every gate can be enabled or disabled for this
project. Offer individual choices within a group.

| Topic | Saved gate keys | Explain in plain language |
| --- | --- | --- |
| Basic checks | `format_lint`, `types`, `contracts` | Formatting, likely code mistakes, invalid types, and broken API or schema contracts. Use the project's existing tools where available. |
| Tests and behavior | `quality`, `test_execution`, `smoke`, `gherkin`, `test_integrity` | The `quality` gate combines tests, coverage, cyclomatic complexity, and CRAP. Test execution proves that tests really ran. Smoke checks exercise startup or a real flow. Gherkin adds readable acceptance scenarios. Integrity checks look for tests that replace the behavior they claim to prove. |
| Maintainability | `cognitive`, `duplication`, `file_loc`, `dead_code`, `error_handling` | Hard-to-follow decisions and nesting, repeated code, oversized files, unused code, and untested or silent error handling. |
| Architecture | `dependency_health`, `dependencies`, `extensibility`, `scope`, `hotspots` | Import cycles, module boundaries, extension contracts, omitted production files, and frequently changed complex code. Hotspots provide information rather than a numeric pass limit. |
| Security | `secrets`, `vulnerabilities` | Known credential formats and known vulnerable dependency versions. Vulnerability checks require advisory access; explain that network need before enabling them. |
| Extra test checks | `slow_tests`, `flaky`, `mutation` | Feedback time, inconsistent test results, and whether tests detect deliberate mistakes. Flaky and mutation checks repeat work and start OFF unless chosen. |

Example question:

> Coverage shows which code the tests exercised. Branch coverage also checks
> both outcomes of decisions, such as success and failure. Higher targets need
> more test work. Would you like the combined tests and coverage gate enabled
> for this project?

Use `gates` in `.quality/quality-gate.json` for explicit choices. Keys are the
runner's gate keys above, not CLI flag names. Numeric thresholds belong in the
threshold file. For example, after the user chooses these values:

```json
{"gates": {"quality": true, "gherkin": false, "mutation": false}}
```

Unspecified gates retain existing behavior. To make a first-time policy complete,
record a boolean for every key in the table, including choices accepted as a
group. An enabled gate requires real evidence; a missing adapter is not a reason
to silently turn it off. `quality` is one combined gate; do not promise separate
test, line-coverage, branch-coverage, complexity, or CRAP switches. Their limits
can be set separately. CLI check flags select a run; they do not enable a gate
saved as OFF. To re-enable it, change the project's saved choice.

## Set limits for enabled gates

For the recommended path, summarize the proposed limits together and ask one
keep-or-adjust question. For customization, explain each relevant limit before
asking for a value. Name the unit, whether
higher or lower is stricter, and what a failure means. Offer a project-specific
recommendation, the bundled value as a strict reference, and a custom value.
Bundled values are proposals, not accepted requirements. Let the user accept a
related group of recommendations in one answer after explaining its values.
Skip threshold questions for disabled gates and informational measurements.

| Limits | Meaning and units | Bundled reference |
| --- | --- | --- |
| `metrics.coverage_limit`, `metrics.branch_coverage_limit` | Minimum percent per function. A 90% line target permits 10% of executable lines to remain untested; branch coverage measures decision outcomes separately. Higher is stricter. | 100% each |
| `metrics.complexity_limit`, `metrics.crap_limit` | Maximum per function. Cyclomatic complexity counts independent paths. CRAP combines complexity with missing line coverage; lower limits are stricter. At 100% line coverage, CRAP equals complexity. | 6 each |
| `portable_analysis.max_cognitive_complexity`, `max_nesting_depth` | Maximum difficulty from control flow and maximum nested control levels. Lower is stricter. | 15 and 4 |
| `portable_analysis.max_duplication_percent`, `file_loc.max_lines` | Maximum repeated source percentage and physical lines per production file. Lower is stricter. | 5% and 600 lines |
| `slow_tests.max_test_seconds`, `max_suite_seconds` | Maximum seconds for one test and the complete suite. Choose limits that fit actual workloads; the suite limit differs from a process timeout. | 5 and 300 seconds |
| `test_execution.min_executed`, `max_skipped` | Minimum tests that actually execute (at least 1) and skipped tests (fixed at 0 when enabled). An empty suite provides no test evidence. | 1 and 0 |
| `error_handling.failure_path_coverage_limit`, `max_silent_handlers` | Minimum covered error-handler percentage and silent handlers (fixed at 0 when enabled). | 100% and 0 |
| `extensibility.contract_coverage_limit`, `max_core_to_extension_dependencies` | Minimum passing extension-scenario percentage and imports from stable core into replaceable extensions (fixed at 0 when enabled). | 100% and 0 |
| `format_lint.max_violations`, `types.max_errors`, `contracts.max_violations`, `metrics.max_test_failures`, `dead_code.max_findings`, `dependencies.max_violations` | Findings or failures are fixed at 0 when these gates are enabled; commands must also exit 0. Explain this rule rather than offering unsupported custom allowances. | 0 each |
| `portable_analysis.max_dependency_cycles`, `max_secret_findings`, `max_known_vulnerabilities` | Cycles, detected credentials, and known vulnerability findings are fixed at 0 when these gates are enabled. Users choose whether to enable each gate. | 0 each |
| `flaky_tests.runs`, `max_failures`, `mutation.max_surviving_mutants` | Number of repeated suites (at least 2); inconsistent failures and surviving deliberate mistakes are fixed at 0 when enabled. More repetitions cost more time. | 3 runs, 0 failures, 0 survivors |

For application performance without a chosen budget, report measurements only.
Do not invent a latency goal. Validate all proposed numeric values with the
runner's threshold validation before executing checks. Explain rejected values
and ask for a valid replacement rather than silently clamping them.

## Save and verify

Summarize the accepted ON/OFF choices and limits in a compact table. State which
checks a PASS will cover. After the user has supplied all needed decisions,
initialize missing files with the configuration-only entrypoint:

```bash
python3 <skill-directory>/scripts/repo_quality_gate.py --root PROJECT --init
```

Use a Python 3.10+ interpreter. This command creates configuration templates
without running checks and refuses to overwrite existing files. When files
already exist, edit only the requested project settings; do not initialize over
them. Save the chosen policy before running the first baseline with
`<skill-directory>/scripts/quality --root PROJECT --no-install`. Do not use the
loop's `--init` for chat onboarding: it runs a baseline before choices are saved.

Save only in the target project's `.quality/` folder. Preserve existing commands,
unrelated settings, and confirmed profile answers. Mark the completed conversation
with `setup.completed: true` in `quality-gate.json`; the agent uses this marker
to avoid repeating onboarding. Existing configurations without the marker remain
valid for coding tasks, but an install-and-setup request must finish the choices
and save the marker while preserving unrelated settings.

Run the enabled checks and explain any missing tools or evidence. Keep disabled
checks visibly OFF. If the user disables every gate, save that choice, explain
that there is no verification evidence, and do not claim certification. On later
tasks, reuse the project policy. Reopen only the affected setup topic when the
user requests a change or a new gate needs a decision; never tighten or loosen
policy automatically during repair.
