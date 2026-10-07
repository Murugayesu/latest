# JavaScript and TypeScript (npm registry)

## Lookup

```bash
python scripts/stable_version.py npm:next npm:react npm:@types/node@24
```

- Scoped names work as written (`npm:@prisma/client`).
- `@<line>` restricts the answer to one release line. Use it for packages that must match something else: `@types/node` matching the Node major, a type package matching its library's major, or a new dependency that must fit an older installed framework.
- A `WARNING: the 'latest' tag points at pre-release` line means a bare `npm install <pkg>` would fetch that pre-release. Install the version the script printed, by number.
- `required peers` must be installed and must fall in those ranges; look them up in the same call. `optional peers` are installed only if the project already uses them, but a version the project has must still fall in the printed range.
- `pre-release tags ahead of this` shows an upcoming major. If the product's name now refers to that generation, it is a case for the user to decide.
- Packages that ship together (a CLI and its client library) take the same version.

By hand, if Python is unavailable:

```bash
npm view <pkg> dist-tags --json     # every tag, not only latest
npm view <pkg> time --json          # publish time of every version
npm view <pkg>@<ver> deprecated peerDependencies peerDependenciesMeta engines
```

## Fitting a new package to an older installed one

When an installed package is behind the range a new package wants, find the newest line that still fits rather than upgrading what is installed:

```bash
npm view "<pkg>@>=<older major>.0.0" version peerDependencies.<installed pkg> --json
```

Pick the newest version whose range accepts the installed version, then confirm it with `npm:<pkg>@<line>`. Peer metadata is sometimes missing or too loose, so also read the package's release notes around that line for the installed package's name. If they say support for the installed major was dropped earlier than the peer range claims, go back to the last release before that. Say in the report that the newer line needs the installed package upgraded first.

## Resolve without installing

Use the cutoff timestamp from the script so transitive packages obey the same wait. Either let npm write the manifest:

```bash
npm install --save-exact --package-lock-only --before=<cutoff> <pkg>@<ver> <pkg>@<ver>
npm install --save-exact --save-dev --package-lock-only --before=<cutoff> <pkg>@<ver>
```

or write exact pins into `package.json` and run `npm install --package-lock-only --before=<cutoff>` once.

- `--save-exact` matters: without it npm writes a `^` range and the pin is lost.
- `--package-lock-only` writes `package.json` and `package-lock.json` and installs nothing.
- An `ERESOLVE` error names the two packages in conflict. Move the newer one down a line (`npm:<pkg>@<line>`) and resolve again.
- With pnpm, set `minimumReleaseAge: 10080` (minutes) in `pnpm-workspace.yaml` and run `pnpm install --lockfile-only`.

## Advisories

```bash
npm audit --package-lock-only
```

Read which top-level package each finding arrives through. For a package being added, switch to a stable version that clears it and resolve again. For a package that was already installed, report the finding and the version that fixes it, and leave the upgrade to the user. A finding in a code path the project never uses (a driver for a database it does not have) is still reported, with that context.

## Reading docs for an unfamiliar major

`npm view <pkg>@<ver> readme` prints the README of that exact version without installing anything.

## Keep the rule after setup (new projects)

- Set `"engines": {"node": ">=<major>.0.0 <<next major>.0.0"}` in `package.json`. The exact patch belongs in the Dockerfile and CI, so a developer on an earlier patch of the same line is not blocked.
- To make later installs wait as well, set `min-release-age=7` in the project `.npmrc` if the installed npm supports it (`npm config get min-release-age` prints `null` when it does, `undefined` when it does not).

For an existing project, leave `engines` and `.npmrc` as they are unless asked.
