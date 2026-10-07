# JavaScript and TypeScript (npm registry)

## Lookup

```bash
python scripts/stable_version.py npm:next npm:react npm:@types/node@24
```

- Scoped names work as written (`npm:@prisma/client`).
- `@<line>` restricts the answer to one release line. Use it for packages that must match something else, such as `@types/node` matching the Node major, or a new dependency that must fit an older installed framework.
- A `WARNING: the 'latest' tag points at pre-release` line means a bare `npm install <pkg>` would fetch that pre-release. Install the version the script printed, by number.
- The `peers:` line lists companions that must be installed and must fall in those ranges. Look them up in the same call.
- Packages that ship together (for example a CLI and its client library) take the same version.

By hand, if Python is unavailable:

```bash
npm view <pkg> dist-tags --json     # every tag, not only latest
npm view <pkg> time --json          # publish time of every version
npm view <pkg>@<ver> deprecated peerDependencies engines
```

## Resolve without installing

Use the cutoff timestamp from the script's first output line so transitive packages obey the same wait:

```bash
npm install --save-exact --package-lock-only --before=<cutoff> <pkg>@<ver> <pkg>@<ver>
npm install --save-exact --save-dev --package-lock-only --before=<cutoff> <pkg>@<ver>
```

- `--save-exact` matters: without it npm writes a `^` range and the pin is lost.
- `--package-lock-only` writes `package.json` and `package-lock.json` and installs nothing.
- An `ERESOLVE` error names the two packages in conflict. Move the newer one down a line (`npm:<pkg>@<line>`) and resolve again.
- With pnpm, set `minimumReleaseAge: 10080` (minutes) in `pnpm-workspace.yaml` and run `pnpm install --lockfile-only`.

## Advisories

```bash
npm audit --package-lock-only
```

Read which top-level package each finding arrives through. If a different stable version of that package clears it, switch and resolve again. A finding in a code path the project never uses (a database driver for a database it does not have) is still reported, with that context.

## Keep the rule after setup

Add `"engines": {"node": ">=<chosen version> <<next major>"}` to `package.json`. To make later installs wait as well, set `min-release-age=7` in the project `.npmrc` if the installed npm supports it (`npm config get min-release-age` prints `null` when it does, `undefined` when it does not).
