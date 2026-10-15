# Challenge the Design

Review the problem and chosen mechanism before checking whether the code works.

The reviewer reconstructs the affected person's job, separates requirements from
assumptions, asks what can be removed, and compares the proposal with viable simpler
alternatives under the same guarantees. It then checks implementation correctness
and the evidence behind the tests.

A design objection needs a premise, consequence, and supporting evidence. The
reviewer also challenges its own alternative: what would it lose, and what evidence
would show the author is right? A sound design can survive the review unchanged.

## Install the skill

```bash
npx skills add pierrebrunelle/challenge-the-design
```

For Codex, invoke `$challenge-the-design` with a PR, diff, or design. Other skill
hosts can load the same folder:
[skills/challenge-the-design](skills/challenge-the-design).

From a cloned checkout, `./install.sh --platform codex-skill` installs the standalone
skill. The installer also supports `cursor-skill`, `claude-code`, and `antigravity`.
Use `--destination /path/to/skill` for an explicit location. Existing destinations
are left untouched; see `./install.sh --help`.

## Install the plugin

```bash
npx plugins add pierrebrunelle/challenge-the-design
```

The plugin adds the same skill and a `review-design` command. It bundles no MCP
server or subagents. Native marketplace options:

**Claude Code**

```text
/plugin marketplace add pierrebrunelle/challenge-the-design
/plugin install challenge-the-design@challenge-the-design
/challenge-the-design:review-design <PR URL or design>
```

**Codex**

```bash
codex plugin marketplace add pierrebrunelle/challenge-the-design --ref main
codex plugin add challenge-the-design@challenge-the-design
```

Start a new conversation after installation. These repository marketplaces provide
direct distribution; they do not publish the plugin to a public directory.

## Use it

```text
Use $challenge-the-design to review this PR.

Establish the problem and required guarantees before accepting the proposed
mechanism. Challenge consequential assumptions, look for scope to remove, and
compare viable alternatives under the same constraints. Name what would falsify
your recommendation. Then check correctness and verification of the implementation.
```

The review follows five questions:

1. Is the requirement supported by the caller's actual job and observable problem?
2. What can be deleted or reused while preserving the required behavior?
3. Which design best addresses the binding constraint and its failure modes?
4. What small check could settle the consequential uncertainty?
5. If automation is proposed, is the underlying work necessary and understood?

For a consequential dispute it uses a short decision note: doubt, unknowns,
explanation, options, constraints, risk, choice, falsifier, and verification.

## What comes back

- A brief design assessment: what is established, what is assumed, and whether the
  approach is justified.
- Supported design objections and implementation findings with locations,
  consequences, verification status, and suitable corrections or next checks.
- Maintenance suggestions and unresolved questions kept distinct from defects.
- Reviewed scope/revisions and the limits of execution, mocks, source evidence,
  and CI. An expanded file-by-file map is available when requested.

The review leaves product code unchanged unless fixes are separately authorized.
Repository and ticket access use tools and permissions supplied by the host;
posting feedback requires separate authorization. A proposal with no justified
objections is a valid outcome. Required review output schemas take precedence
over the prose format.

## What's inside

```text
skills/challenge-the-design/
  SKILL.md                  Complete review procedure
  agents/openai.yaml        Skill metadata
commands/review-design.md   Plugin command
evals/evals.json            Behavioral prompts and grading criteria
scripts/validate_plugin.py  Package structure checks
tests/test_install.py       Standalone installer checks
```

Portable, Codex, Claude Code, Cursor, and generic plugin manifests wrap the same
skill. The packaging follows [walk-the-job](https://github.com/pierrebrunelle/walk-the-job).

## Validate

```bash
python3 scripts/validate_plugin.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
npx plugins discover .
npx skills add . --list -y
```

The checks validate package structure, installation, and discovery. The cases in
`evals/evals.json` describe behavioral evaluations; they are not executed by these
structural checks and do not claim a model-quality score.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
