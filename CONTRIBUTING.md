# Contributing

Issues and pull requests are welcome. The most useful reports are a registry that returns a wrong answer and a case where the skill led an agent to a bad version.

## Before opening a pull request

Run the same checks as CI:

```bash
python tests/test_stable_version.py
pip install skills-ref && agentskills validate skills/latest
python skills/latest/scripts/stable_version.py npm:zod pypi:requests eol:nodejs
```

If you have Claude Code installed, also run `claude plugin validate --strict .`.

## Ground rules

- **The script stays standard-library only.** It has to run wherever an agent has Python.
- **`SKILL.md` stays short.** Ecosystem detail goes in `references/`, one level deep.
- **No version numbers in the skill's instructions.** They go stale; examples use placeholders.
- **Changes to the workflow need evidence.** Say which test case in `evals/` you ran, with and without the change, and what differed.
- **Claims in the README match what was tested.** Add the client, model and date when you report a result.

## Adding a registry

Add a function to `scripts/stable_version.py` that returns the newest final release at least the minimum age old, register it in `SOURCES`, add a unit test, and document the spec form in the matching file under `references/`.

## Releases

Each release bumps `version` in `.claude-plugin/plugin.json` and `metadata.version` in `skills/latest/SKILL.md` to the same value, and adds an entry to `CHANGELOG.md`.
