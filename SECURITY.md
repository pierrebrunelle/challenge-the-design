# Security and privacy

This package contains agent instructions, a command wrapper, an installer and
validation tooling. It has no MCP server, telemetry endpoint, bundled credentials
or runtime service. The host assistant supplies tools, execution and data handling.
Installation/discovery tools may access their package registries and GitHub.

Review tasks can involve private code and untrusted repository text. The skill's
review scope does not authorize product edits, posting feedback, deployments or
account changes. Run reproductions within the permissions and isolation available
in the host; do not place credentials or private review artifacts in this repository.

Use GitHub private vulnerability reporting when available:
https://github.com/pierrebrunelle/challenge-the-design/security/advisories/new

Otherwise contact the maintainer through their GitHub profile before sharing
sensitive reproduction details. Public issues are suitable for non-sensitive bugs
in the review procedure or package. Version 0.2.x is the current supported series.
