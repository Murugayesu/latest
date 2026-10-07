#!/usr/bin/env python3
"""Look up the newest stable, aged release of each item from its live registry.

Usage:
    python stable_version.py [--min-age-days N] SPEC [SPEC ...]

SPEC forms:
    npm:<package>            pypi:<package>         crates:<crate>
    go:<module path>         gh:<owner>/<repo>      eol:<endoflife.date product>
    docker:<image>:<tag>     (checks that the tag exists on Docker Hub)

Append @<line> to an npm, pypi or crates spec to stay inside one release line,
for example npm:@types/node@24 or pypi:django@5.2.

Standard library only. All lookups run in parallel; one failure does not stop the rest.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

# Most malicious or broken releases are pulled within days of publication,
# so a week of age filters them out while costing little freshness.
DEFAULT_MIN_AGE_DAYS = 7
# Registries answer in well under this; a longer wait usually means no network.
TIMEOUT_SECONDS = 30
NOW = datetime.now(timezone.utc)


def fetch(url, accept="application/json"):
    headers = {"User-Agent": "latest-skill-version-check", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=TIMEOUT_SECONDS) as r:
        return json.loads(r.read().decode("utf-8"))


def when(text):
    stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def age_days(stamp):
    return (NOW - stamp).total_seconds() / 86400


def order(version):
    return tuple(int(n) for n in re.findall(r"\d+", version))


def split_line(name):
    """'pkg@5.2' -> ('pkg', '5.2'); a leading @ (npm scope) is not a separator."""
    cut = name.rfind("@")
    return (name[:cut], name[cut + 1:]) if cut > 0 else (name, None)


def in_line(version, line):
    return line is None or version == line or version.startswith(line + ".")


def choose(releases, min_age, ceiling=None):
    """releases: {version: publish datetime}, stable versions only.

    Returns (pick, skipped): the highest version old enough, and the higher ones passed over.
    The highest number wins rather than the most recent upload, because patches to
    older lines are often published after the current line.
    """
    ranked = sorted(releases, key=order, reverse=True)
    if ceiling:
        ranked = [v for v in ranked if order(v) <= order(ceiling)]
    skipped = []
    for version in ranked:
        if age_days(releases[version]) >= min_age:
            return version, skipped
        skipped.append(version)
    return None, skipped


def describe(spec, releases, pick, skipped, notes):
    lines = []
    if pick:
        lines.append("%s  ->  %s  (published %s, %.1f days old)" % (
            spec, pick, releases[pick].date().isoformat(), age_days(releases[pick])))
    elif skipped:
        lines.append("%s  ->  NO stable release is old enough; decide with the user" % spec)
    else:
        lines.append("%s  ->  NO usable stable release (none published, or all deprecated or yanked)" % spec)
    if skipped:
        lines.append("    skipped as too new: " + ", ".join(
            "%s (%.1f days)" % (v, age_days(releases[v])) for v in skipped[:6]))
    lines.extend("    " + n for n in notes if n)
    return "\n".join(lines)


def npm(name, min_age):
    name, line = split_line(name)
    doc = fetch("https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@"))
    times, versions = doc.get("time", {}), doc.get("versions", {})
    stable = {v: when(times[v]) for v in versions
              if re.fullmatch(r"\d+\.\d+\.\d+", v) and v in times and not versions[v].get("deprecated")
              and in_line(v, line)}
    tag = doc.get("dist-tags", {}).get("latest", "")
    notes = []
    tag_is_stable = bool(re.fullmatch(r"\d+\.\d+\.\d+", tag))
    if not tag_is_stable:
        notes.append("WARNING: the 'latest' tag points at pre-release %s; a bare install would fetch it" % tag)
    elif versions.get(tag, {}).get("deprecated"):
        notes.append("WARNING: 'latest' (%s) is DEPRECATED: %s" % (tag, versions[tag]["deprecated"]))
    # Maintainers sometimes publish a higher number without moving 'latest'; respect their tag.
    pick, skipped = choose(stable, min_age, ceiling=tag if tag_is_stable and not line else None)
    other_tags = {k: v for k, v in doc.get("dist-tags", {}).items() if k != "latest"}
    if pick:
        meta = versions[pick]
        if meta.get("engines"):
            notes.append("engines: " + json.dumps(meta["engines"]))
        if meta.get("peerDependencies"):
            notes.append("peers: " + json.dumps(meta["peerDependencies"]))
    if other_tags:
        notes.append("other tags: " + ", ".join("%s=%s" % kv for kv in list(other_tags.items())[:5]))
    return describe("npm:" + name + ("@" + line if line else ""), stable, pick, skipped, notes)


def pypi(name, min_age):
    name, line = split_line(name)
    doc = fetch("https://pypi.org/pypi/%s/json" % name)
    stable, requires = {}, {}
    for version, files in doc.get("releases", {}).items():
        live = [f for f in files if not f.get("yanked")]
        if live and re.fullmatch(r"\d+(\.\d+)*(\.post\d+)?", version) and in_line(version, line):
            stable[version] = min(when(f["upload_time_iso_8601"]) for f in live)
            requires[version] = live[0].get("requires_python")
    pick, skipped = choose(stable, min_age)
    notes = ["requires-python: %s" % requires[pick]] if pick and requires.get(pick) else []
    return describe("pypi:" + name + ("@" + line if line else ""), stable, pick, skipped, notes)


def crates(name, min_age):
    name, line = split_line(name)
    doc = fetch("https://crates.io/api/v1/crates/%s/versions" % name)
    stable = {v["num"]: when(v["created_at"]) for v in doc.get("versions", [])
              if not v.get("yanked") and re.fullmatch(r"\d+\.\d+\.\d+", v["num"]) and in_line(v["num"], line)}
    pick, skipped = choose(stable, min_age)
    return describe("crates:" + name + ("@" + line if line else ""), stable, pick, skipped, [])


def go(module, min_age):
    escaped = re.sub(r"[A-Z]", lambda m: "!" + m.group().lower(), module)
    base = "https://proxy.golang.org/%s/@v/" % escaped
    with urllib.request.urlopen(base + "list", timeout=TIMEOUT_SECONDS) as r:
        listed = [v for v in r.read().decode().split() if re.fullmatch(r"v\d+\.\d+\.\d+(\+incompatible)?", v)]
    stable = {}
    for version in sorted(listed, key=order, reverse=True)[:8]:
        stable[version] = when(fetch(base + version + ".info")["Time"])
        if age_days(stable[version]) >= min_age:
            break
    pick, skipped = choose(stable, min_age)
    return describe("go:" + module, stable, pick, skipped, [])


def gh(repo, min_age):
    doc = fetch("https://api.github.com/repos/%s/releases?per_page=30" % repo)
    stable = {r["tag_name"]: when(r["published_at"]) for r in doc
              if not r.get("prerelease") and not r.get("draft") and r.get("published_at")}
    pick, skipped = choose(stable, min_age)
    return describe("gh:" + repo, stable, pick, skipped, [])


def eol(product, min_age):
    cycles = fetch("https://endoflife.date/api/%s.json" % product)
    today = NOW.date().isoformat()

    def supported(c):
        return c.get("eol") is False or (isinstance(c.get("eol"), str) and c["eol"] > today)

    def lts_now(c):
        # 'lts' is true, false, or the date the line BECOMES long-term support.
        return c.get("lts") is True or (isinstance(c.get("lts"), str) and c["lts"] <= today)

    live = [c for c in cycles if supported(c)]
    has_lts = any(c.get("lts") for c in cycles)
    preferred = next((c for c in live if lts_now(c)), None) if has_lts else (live[0] if live else None)
    lines = ["eol:%s  ->  %s" % (product, "line %s, newest patch %s" % (preferred["cycle"], preferred.get("latest"))
                                  if preferred else "NO supported line found")]
    for c in live:
        status = "LTS" if lts_now(c) else ("LTS from %s" % c["lts"] if isinstance(c.get("lts"), str) else
                                           ("not LTS" if has_lts else "supported"))
        active = c.get("support")
        fixes = "" if active in (None, True) else (
            "   security fixes only" if active is False or active <= today else "   bug fixes until %s" % active)
        lines.append("    %-8s latest %-12s released %s   %-16s end of life %s%s" % (
            c["cycle"], c.get("latest"), c.get("latestReleaseDate"), status, c.get("eol") or "not announced", fixes))
    return "\n".join(lines)


def docker(ref, min_age):
    image, _, tag = ref.partition(":")
    repo = image if "/" in image else "library/" + image
    try:
        doc = fetch("https://hub.docker.com/v2/repositories/%s/tags/%s" % (repo, tag))
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return "docker:%s  ->  TAG DOES NOT EXIST on Docker Hub" % ref
        raise
    return "docker:%s  ->  tag exists (image last pushed %s)" % (ref, (doc.get("last_updated") or "")[:10])


SOURCES = {"npm": npm, "pypi": pypi, "crates": crates, "go": go, "gh": gh, "eol": eol, "docker": docker}


def lookup(spec, min_age):
    kind, _, name = spec.partition(":")
    if kind not in SOURCES or not name:
        return "%s  ->  ERROR: unknown spec; use one of %s" % (spec, ", ".join(k + ":" for k in SOURCES))
    try:
        return SOURCES[kind](name, min_age)
    except urllib.error.HTTPError as err:
        hint = "name not found in this registry" if err.code == 404 else "HTTP %d" % err.code
        return "%s  ->  ERROR: %s. Check the name, or look it up by hand; do not fall back to memory." % (spec, hint)
    except Exception as err:  # network down, unexpected payload: report and keep going
        return "%s  ->  ERROR: %s. Look it up by hand or mark it unverified." % (spec, err)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("specs", nargs="+", metavar="SPEC")
    parser.add_argument("--min-age-days", type=float, default=DEFAULT_MIN_AGE_DAYS)
    args = parser.parse_args()
    cutoff = (NOW - timedelta(days=args.min_age_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("checked %s UTC | minimum age %g days | cutoff %s" % (
        NOW.strftime("%Y-%m-%d %H:%M"), args.min_age_days, cutoff))
    with ThreadPoolExecutor(max_workers=8) as pool:
        for block in pool.map(lambda s: lookup(s, args.min_age_days), args.specs):
            print(block)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None
    main()
