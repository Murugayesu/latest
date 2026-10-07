# Python (PyPI)

## Lookup

```bash
python scripts/stable_version.py eol:python pypi:fastapi pypi:sqlalchemy pypi:django@5.2
```

- `@<line>` restricts the answer to one release line.
- Each result prints `requires-python` for the chosen version. Take the Python version from `eol:python`, then confirm every package accepts it.
- Yanked releases and pre-releases are already excluded.
- The newest Python line can be ahead of the wheels some packages publish. If resolution fails on a compiled package, step down one Python line rather than building from source, and say so.

By hand, if the script cannot run: `https://pypi.org/pypi/<pkg>/json`. `info.version` is only the newest upload; the `releases` map holds every version with per-file `upload_time_iso_8601`, `yanked` and `requires_python`.

## Where the Python version goes

One Python version for the whole project, written at two levels of precision:

- The line (`3.14`) in `requires-python` (`>=3.14,<3.15`) and `.python-version`. A local uv or pyenv that predates the newest patch cannot find an exact patch and fails.
- The exact patch (`3.14.8`) in the Dockerfile base image tag and the CI setup step.

## Resolve without installing

Use the cutoff timestamp from the script so transitive packages obey the same wait.

With uv, write the exact pins into `pyproject.toml` (in an empty directory, `uv init --bare` creates it first), add the cutoff, and lock:

```toml
[project]
requires-python = ">=<line>,<<next line>"
dependencies = ["fastapi==<ver>", "sqlalchemy[asyncio]==<ver>"]

[dependency-groups]
dev = ["pytest==<ver>", "ruff==<ver>"]

[tool.uv]
exclude-newer = "<cutoff>"
```

```bash
uv lock
```

`exclude-newer` stays in the file, so it has to be moved forward at each later upgrade. Note that in `STACK.md`. If the local uv is older than the uv version pinned for Docker and CI, note that too; the lockfile format is compatible across patch releases.

With pip: write the pins to `requirements.txt` and run `pip install --dry-run --ignore-installed -r requirements.txt`. With Poetry: `poetry add --lock "<pkg>==<ver>"`.

## Advisories

From a uv lockfile:

```bash
uv export --frozen --no-hashes --no-emit-project --all-groups -o requirements.lock.txt
uvx pip-audit -r requirements.lock.txt --no-deps --disable-pip
```

From a requirements file: `uvx pip-audit -r requirements.txt`. Without pip-audit, query OSV for the locked packages in one request:

```bash
curl -s -d '{"queries":[{"package":{"name":"<pkg>","ecosystem":"PyPI"},"version":"<ver>"}]}' https://api.osv.dev/v1/querybatch
```

An empty result object for a package means no known advisory. Check the whole lockfile, not only the packages named in the request.

## Tooling versions

uv, Ruff and similar tools are also published on PyPI; look them up like any other item (`pypi:uv`) and use the same version in the Dockerfile and CI.
