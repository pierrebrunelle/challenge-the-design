# Repository instructions

This is the Challenge the Design plugin: one portable skill and one review command.

- The canonical review instructions are `skills/challenge-the-design/SKILL.md`.
  Commands and README examples point there; do not create competing procedure copies.
- Keep the skill generic and self-contained. Preserve its design-first review,
  evidence requirements, viable-alternative checks, and protection against
  contrarian findings that discard necessary guarantees.
- Keep the skill under 500 lines. Use references only when conditional detail
  warrants them; do not add modes, agents, dependencies, or automation speculatively.
- Keep plugin identity and version fields aligned across the manifests, marketplaces,
  package metadata, and the skill's `metadata.version`.
- Validate with `python3 scripts/validate_plugin.py` and
  `python3 -m unittest discover -s tests -v`. Installer/discovery checks do not
  establish how well an agent performs a design review.
