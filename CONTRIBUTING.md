# Contributing

Keep one review procedure in `skills/challenge-the-design/SKILL.md`. Change it when
an observed review failure supports the change, and add or adjust a behavioral case
in `evals/evals.json` when useful. Avoid adding a rule for every imagined edge case.

Preserve both sides of the skill: challenge the author's framing, and challenge any
alternative that loses necessary guarantees. New modes, subagents and dependencies
need a concrete use. See `AGENTS.md` for layout and versioning rules.

Before opening a PR, run the validation commands in README.md. Native host checks
require the corresponding client; report any checks not run. Behavioral evaluations
need actual agent execution and evidence, not just passing package checks.

Contributions are licensed under the MIT License.
