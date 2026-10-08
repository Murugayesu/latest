# Runtimes, databases, images, CI actions and other registries

## Runtimes, databases, operating systems, major frameworks

```bash
python scripts/stable_version.py eol:nodejs eol:python eol:postgresql eol:redis
```

Product names are the slugs used by endoflife.date (`nodejs`, `python`, `postgresql`, `redis`, `mysql`, `go`, `ruby`, `php`, `dotnet`, `ubuntu`, `debian`, `nextjs`, `django`). A 404 means the slug is wrong or the product is not tracked; list them at `https://endoflife.date/api/all.json`.

Reading the output:

- The first line is the version to use: the newest patch of the newest line that is LTS today, or of the newest supported line for products without LTS. Use that exact version in every file that names the runtime. Choosing a different line is a decision to put to the user with the reason.
- `LTS from <date>` means the line is not LTS yet. If the date is within a few weeks, mention the coming switch and let the user choose.
- `security fixes only` means the line no longer gets bug fixes. It is not a more stable choice for a new project.
- `end of life not announced` on the suggested line is normal for the newest line of some products; say so rather than moving to an older line.
- A line that has just had its first release may not be listed yet. That is fine: a days-old runtime line is not the one to start a project on.
- The `NOTE` about a patch released inside the wait applies to runtimes only. Their patches are mostly security fixes, so taking the newest patch is normally right; mention it.

## Container images

Pin a full version tag (`python:3.14.8-slim-trixie`), never `latest`, a bare major, or a bare line. Confirm the tag in a second call once the runtime version is known:

```bash
python scripts/stable_version.py --cutoff <cutoff> docker:node:<version>-slim docker:postgres:<version>
```

If the tag does not exist, the output lists the tags that do exist for that version; choose from that list rather than guessing again. Default to the Debian `slim` variant unless the project already uses Alpine. The "last pushed" date is a rebuild of the same version and is not subject to the 7-day wait.

The script checks Docker Hub only. For an image published elsewhere (ghcr.io, quay.io), use its Docker Hub mirror if the project publishes one, otherwise take the version from the tool's own release (`pypi:` or `gh:`) and state that the image tag itself was not checked.

## CI actions and tools released on GitHub

```bash
python scripts/stable_version.py gh:actions/checkout gh:astral-sh/setup-uv
```

Pre-releases and drafts are excluded, and the output includes the commit the tag points at. Follow the project's existing pinning style in workflow files. For a new project pin the commit with the tag as a comment, since tags can be moved:

```yaml
- uses: actions/checkout@<commit>  # <tag>
```

Every `uses:` line in a workflow is a versioned dependency, including ones added for caching, coverage or image builds. Each needs its own lookup.

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
