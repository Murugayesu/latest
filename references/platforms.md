# Runtimes, databases, images, CI actions and other registries

## Runtimes, databases, operating systems, major frameworks

```bash
python scripts/stable_version.py eol:nodejs eol:python eol:postgresql eol:redis
```

Product names are the slugs used by endoflife.date (`nodejs`, `python`, `postgresql`, `redis`, `mysql`, `go`, `ruby`, `php`, `dotnet`, `ubuntu`, `debian`, `nextjs`, `django`). A 404 means the slug is wrong or the product is not tracked; list them at `https://endoflife.date/api/all.json`.

Reading the output:

- The first line is the suggested line: the newest one that is LTS today, or the newest supported one for products without LTS.
- `LTS from <date>` means the line is not LTS yet. Do not choose it as the LTS line before that date. If the date is within a few weeks, mention the coming switch and let the user choose.
- `security fixes only` means the line still gets patches but no bug fixes; prefer a line still receiving bug fixes for a new project.
- Record the exact patch version, not just the line.

## Container images

Pin a full version tag, never `latest` or a bare major. Confirm the tag exists:

```bash
python scripts/stable_version.py docker:node:<version>-bookworm-slim docker:postgres:<version>
```

Default to the Debian `slim` variant unless the project already uses Alpine. The "last pushed" date is a rebuild of the same version and is not subject to the 7-day wait. Images outside Docker Hub (ghcr.io, quay.io) have to be checked on their own registry page.

## CI actions and tools released on GitHub

```bash
python scripts/stable_version.py gh:actions/checkout gh:astral-sh/setup-uv
```

Pre-releases and drafts are excluded. Follow the project's existing pinning style in workflow files; for a new project pin the commit with the tag as a comment, since tags can be moved:

```bash
git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>
```

Unauthenticated GitHub API calls are rate limited. The script uses `GITHUB_TOKEN` or `GH_TOKEN` when set.

Hosted runner labels (`ubuntu-24.04` and similar) are not covered by any of these sources. Check the provider's documentation or label them unverified.

## Go and Rust

```bash
python scripts/stable_version.py go:golang.org/x/text crates:serde crates:tokio@1
```

Resolve with `go mod tidy` or `cargo generate-lockfile`, then check advisories with `govulncheck ./...` or `cargo audit` when available.

## Any other registry

NuGet, Maven Central, RubyGems, Packagist and others are not built into the script. Query the registry's own API or CLI and apply the same filter by hand: final release, not deprecated or yanked, published at least 7 days ago, on a supported line.

## Advisories for anything

```bash
curl -s -d '{"package":{"name":"<name>","ecosystem":"<npm|PyPI|Go|crates.io|Maven|NuGet|RubyGems>"},"version":"<ver>"}' https://api.osv.dev/v1/query
```
