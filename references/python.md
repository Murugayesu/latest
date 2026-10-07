# Python (PyPI)

## Lookup

```bash
python scripts/stable_version.py eol:python pypi:fastapi pypi:sqlalchemy pypi:django@5.2
```

- `@<line>` restricts the answer to one release line.
- Each result prints `requires-python` for the chosen version. Pick the Python line first (from `eol:python`), then confirm every package accepts it.
- Yanked releases and pre-releases are already excluded.
- The newest Python line can be ahead of the wheels some packages publish. If resolution fails on a compiled package, step down one Python line rather than building from source.

By hand, if the script cannot run: `https://pypi.org/pypi/<pkg>/json`. `info.version` is only the newest upload; the `releases` map holds every version with per-file `upload_time_iso_8601`, `yanked` and `requires_python`.

## Resolve without installing

Use the cutoff timestamp from the script's first output line so transitive packages obey the same wait.

With uv:

```toml
# pyproject.toml
[tool.uv]
exclude-newer = "<cutoff>"
```

```bash
uv add --no-sync "fastapi==<ver>" "sqlalchemy==<ver>"
uv add --no-sync --dev "pytest==<ver>"
uv lock
```

`exclude-newer` stays in the file, so it has to be moved forward at each later upgrade. Say so in `STACK.md`.

With pip: write the pins to `requirements.txt` and run `pip install --dry-run --ignore-installed -r requirements.txt`. With Poetry: `poetry add --lock "<pkg>==<ver>"`.

## Advisories

Run `pip-audit` against the lockfile or requirements file if it is installed (`uvx pip-audit -r requirements.txt` works without installing it). Otherwise query OSV for the locked packages in one request:

```bash
curl -s -d '{"queries":[{"package":{"name":"<pkg>","ecosystem":"PyPI"},"version":"<ver>"}]}' https://api.osv.dev/v1/querybatch
```

An empty result object for a package means no known advisory.

## Tooling versions

uv, Ruff and similar tools are also published on PyPI and GitHub; look them up like any other item (`pypi:uv` or `gh:astral-sh/uv`) and pin the same version in the Dockerfile and CI.
