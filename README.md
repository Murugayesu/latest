# latest

An agent skill that makes a coding agent check the live registry before it names or pins a version, and pick the newest release that is safe to commit to rather than the newest one that exists.

Models recall version numbers from training data, and that data is always behind the registry. The result is versions that are old, deprecated, or that never existed. Looking up "the latest" is not enough either: the newest release may be a pre-release, hours old, or carry an open advisory.

## What it does

When the agent is about to name a version in a plan, a manifest, a Dockerfile, a CI workflow or an install command, the skill has it:

1. Keep what the project already decided (`STACK.md`, then the lockfile). Nothing is upgraded unless asked.
2. Look up everything else in one call to a bundled script.
3. Take the newest release that is final, not deprecated or yanked, at least 7 days old, and on a supported line.
4. Resolve the whole set together with the project's package manager, applying the same 7-day cutoff to transitive packages.
5. Check advisories on the resolved set.
6. Record the result in `STACK.md` and check every file it wrote against that record.

The lookup script covers npm, PyPI, crates.io, Go modules, GitHub releases, Docker Hub tags and endoflife.date:

```console
$ python scripts/stable_version.py eol:nodejs npm:next npm:prisma pypi:fastapi gh:actions/checkout
checked 2026-10-07 20:39 UTC | minimum age 7 days | cutoff 2026-09-30T20:35:17Z
eol:nodejs  ->  24.21.0  (line 24; use this exact version everywhere)
    26       latest 26.10.0      released 2026-09-22   LTS from 2026-10-28 end of life 2029-04-30
    24       latest 24.21.0      released 2026-09-08   LTS              end of life 2028-04-30
npm:next  ->  16.3.8  (published 2026-09-30, 7.2 days old; only just past the wait)
    skipped as too new: 16.4.0 (1.1 days)
npm:prisma  ->  7.10.0  (published 2026-08-25, 43.3 days old)
    WARNING: the 'latest' tag points at pre-release 8.0.0-rc.21; a bare install would fetch it
pypi:fastapi  ->  0.142.2  (published 2026-09-30, 7.4 days old; only just past the wait)
    skipped as too new: 0.142.3 (0.1 days)
gh:actions/checkout  ->  v7.0.1  (published 2026-07-20, 79.2 days old)
    commit: 3d3c42e5aac5ba805825da76410c181273ba90b1
```

(Output shortened. The versions shown are from the day it was run and will be different today, which is the point.)

## Install

**Claude Code, as a plugin**

```bash
claude plugin marketplace add Murugayesu/latest
claude plugin install latest@murugayesu
```

Updates are manual for third-party marketplaces: run `claude plugin update latest@murugayesu`.

**Any agent that supports Agent Skills**

```bash
npx skills add Murugayesu/latest
```

**By hand**

Copy `skills/latest/` into your agent's skills directory, for example `~/.claude/skills/latest/`.

### Make it apply every time

A skill loads when the agent judges it relevant, so it can be skipped. To make it reliable in a project, add this line to `CLAUDE.md` or `AGENTS.md`:

```markdown
Before naming a version of any runtime, framework, library, SDK or tool in a plan, manifest or install command, use the `latest` skill. If STACK.md exists, its versions are authoritative.
```

## Requirements

- Python 3.8 or later (standard library only; tested on 3.13)
- A shell
- Network access to the registries being queried

## What it sends and where

The script makes read-only HTTPS requests to public endpoints: `registry.npmjs.org`, `pypi.org`, `crates.io`, `proxy.golang.org`, `api.github.com`, `hub.docker.com` and `endoflife.date`. The names of the packages you look up are part of those requests. If `GITHUB_TOKEN` or `GH_TOKEN` is set, it is sent to `api.github.com` only, to raise the rate limit. There is no telemetry.

## Test results

These come from development runs on 2026-10-07 and 2026-10-08. Each case was run once with the skill and once without, so treat single-package differences as noise. Projects that involved code were installed and built or tested afterwards.

| Case | Model | Without the skill | With the skill |
|---|---|---|---|
| Choose packages for 11 needs | Haiku 4.5 | All from memory: 1 version that does not exist, 2 deprecated, 7 a major or more behind | All looked up, all exist, exact pins, lockfile, advisory check |
| Plan a new Python service | Haiku 4.5 | Versions taken from search results; at least 10 stale | All package versions current and at least 7 days old |
| Plan a new Python service | Opus 5.5 | All looked up live; 5 picks under 7 days old; no advisory check | No pick under 7 days; advisory check; `STACK.md` |
| Add libraries to a Next 14 app | Opus 5.5 | Nothing upgraded; one pick 5 days old | Nothing upgraded; no young pick; advisories traced |
| Write a new Next.js app | Opus 5.5 | Builds first time | Builds first time |
| Write a new Python service | Opus 5.5 | 25 of 25 tests pass | 25 of 25 tests pass |

What this shows:

- The skill matters most on smaller models, which otherwise answer from memory or from stale search results.
- On a strong model that already checks registries, it adds the 7-day wait, the advisory check and the record.
- It does not make generated code more correct for a version. In these tests the strong model already got that right without it.

What has not been tested:

- How often an agent loads the skill without being told to.
- Agents other than Claude Code.
- Ecosystems beyond npm and PyPI in a full run (crates.io, Go, GitHub and Docker lookups are covered by the script's own checks only).

The test prompts and fixtures are in [`evals/`](evals/).

## Limits

- A full run costs more steps than answering from memory: roughly 12 to 23 tool calls for a stack plan in testing.
- The 7-day wait delays security fixes in libraries by up to a week. The skill reports what it skipped so you can overrule it.
- "No release for over a year" is flagged for a human to look at; the script cannot tell a finished package from an abandoned one.
- Registries not built into the script (NuGet, Maven Central, RubyGems, Packagist) are handled by written instructions only.

## Layout

```
skills/latest/
├── SKILL.md              workflow the agent follows
├── scripts/
│   └── stable_version.py registry lookups
└── references/
    ├── npm.md            JavaScript and TypeScript
    ├── python.md         Python
    └── platforms.md      runtimes, images, CI actions, Go, Rust
evals/                    test prompts and fixtures
.claude-plugin/           Claude Code plugin and marketplace manifests
```

## Contributing

Issues and pull requests are welcome, especially a registry that returns a wrong answer or a case where the skill picked a bad version. Include the script output and the date.

## License

[MIT](LICENSE)
