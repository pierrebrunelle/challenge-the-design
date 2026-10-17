---
description: Review each PR as an ensemble, challenge the problem and design, identify what code to delete while preserving all functionality, and check the implementation.
argument-hint: "[PR URL(s), diff, design document, or disputed decision]"
---

Review the proposed change from first principles.

Arguments: `$ARGUMENTS`

Read [SKILL.md](../skills/challenge-the-design/SKILL.md) and follow it. Use the
supplied PR, PR set, diff, or design as the scope. When none is supplied, inspect
the workspace for the proposed change; ask for a target only when it cannot be
identified. Review each PR as an ensemble with its surrounding callers, state, and
tests. Lead with the ensemble design assessment and what code you would delete,
inline, or collapse while maintaining and preserving all functionality and
guarantees; support objections with evidence, compare alternatives under the same
guarantees, and then report implementation findings. Keep unverified concerns as
questions. Respect any required output schema. Review does not authorize product
edits or posting feedback externally.
