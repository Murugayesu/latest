# Changelog

## 0.1.0 (unreleased)

First public version.

### Included

- A workflow for choosing versions: keep what the project decided, look up the rest, apply a 7-day release-age rule, resolve together, check advisories, record in `STACK.md`, and check written files against the record.
- A lookup script for npm, PyPI, crates.io, Go modules, GitHub releases, Docker Hub tags and endoflife.date.
- Reference files for JavaScript and TypeScript, Python, and runtimes, images and CI actions.
- Claude Code plugin and marketplace manifests, and a layout the Skills CLI can install from.
- Unit tests, three evaluation cases and a CI workflow.

### Known limitations

- Tested only in Claude Code, with Claude models.
- Full runs cover npm and PyPI only.
- Unprompted loading was checked with six prompts, one run each.
- A stack plan costs roughly 12 to 23 tool calls.
- The lockfile check and the quiet-package flag added late in development have not been re-run on the cases that prompted them.
