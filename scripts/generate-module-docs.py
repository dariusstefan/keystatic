#!/usr/bin/env python3
"""Generate Starlight Markdown pages for all OpenSIPS modules.

Content layout:
  src/content/docs/modules/devel/<module>.md   ← master branch
  src/content/docs/modules/4-0/<module>.md     ← 4.0 branch
  src/content/docs/modules/3-6/<module>.md     ← 3.6 branch
  ... etc.

Redirect stubs (sidebar: hidden: true, empty title) are written for
version/module combinations that have no real content, pointing to the
nearest version that does.

Module names are discovered per-branch from the GitHub API, so modules
that were renamed or removed between versions are handled correctly.

Usage:
    python3 scripts/generate-module-docs.py                 # devel only
    python3 scripts/generate-module-docs.py --all-versions  # all versions
    python3 scripts/generate-module-docs.py --version 3.5   # one extra version
"""

import argparse
import json
import re
import shutil
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "opensips" / "modules"
CONTENT_DIR = REPO_ROOT / "src" / "content" / "docs" / "docs" / "modules"

FORK = "dariusstefan/opensips"
GITHUB_RAW = f"https://raw.githubusercontent.com/{FORK}"
GITHUB_API = f"https://api.github.com/repos/{FORK}"

VERSIONS = [
    {"branch": "master", "slug": "devel",  "label": "master (dev)", "is_latest": True},
    {"branch": "4.0",    "slug": "4-0",    "label": "4.0"},
    {"branch": "3.6",    "slug": "3-6",    "label": "3.6"},
    {"branch": "3.5",    "slug": "3-5",    "label": "3.5"},
    {"branch": "3.4",    "slug": "3-4",    "label": "3.4"},
    {"branch": "3.3",    "slug": "3-3",    "label": "3.3"},
]

LATEST = next(v for v in VERSIONS if v.get("is_latest"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_modules_remote(branch: str) -> list[str]:
    url = f"{GITHUB_API}/git/trees/{branch}?recursive=0"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            tree = json.loads(r.read())
        return sorted(
            item["path"].removeprefix("modules/")
            for item in tree.get("tree", [])
            if item["path"].startswith("modules/") and item["type"] == "tree"
            and item["path"].count("/") == 1
        )
    except Exception as exc:
        print(f"  [ERROR] Could not list modules for branch {branch!r}: {exc}")
        return []


def _fetch_readme(branch: str, module: str) -> str | None:
    url = f"{GITHUB_RAW}/{branch}/modules/{module}/README.md"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"  [WARN] HTTP {e.code} fetching {url}")
        return None
    except Exception as exc:
        print(f"  [WARN] {url}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Config-sample propagation
#
# A module README may include a samples.md overview via the portable link
# directive `[label](./samples.md "include")`. On the fork that link resolves
# to modules/<name>/samples.md (+ its samples/*.cfg); on the website all modules
# of a version live flat in one dir, so we copy each module's sample assets into
# a per-module, glob-ignored ".samples/<name>/" subdir and rewrite the link to
# point there. (Starlight's loader skips dot-prefixed dirs, so samples.md/.cfg
# are not treated as routable pages; the remark include plugin still reads them
# from disk at build time.)
# ---------------------------------------------------------------------------

SAMPLES_INCLUDE = '](./samples.md "include")'
_CFG_INCLUDE_RE = re.compile(r'\]\(\./samples/([^)"]+) "include"\)')


def _fetch_raw(branch: str, relpath: str) -> str | None:
    url = f"{GITHUB_RAW}/{branch}/{relpath}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _rewrite_samples_link(md: str, name: str) -> str:
    return md.replace(SAMPLES_INCLUDE, f'](./.samples/{name}/samples.md "include")')


def _strip_samples_link(md: str) -> str:
    """Drop the whole `[label](./samples.md "include")` line (sample assets unavailable)."""
    return re.sub(r'(?m)^\[[^\]]*\]\(\./samples\.md "include"\)\n?', '', md)


def _propagate_samples_local(name: str, md: str, out_dir: Path) -> str:
    if SAMPLES_INCLUDE not in md:
        return md
    src_md = MODULES_DIR / name / "samples.md"
    if not src_md.exists():
        return _strip_samples_link(md)
    dest = out_dir / ".samples" / name
    (dest / "samples").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_md, dest / "samples.md")
    src_dir = MODULES_DIR / name / "samples"
    if src_dir.is_dir():
        for f in src_dir.iterdir():
            if f.is_file():
                shutil.copyfile(f, dest / "samples" / f.name)
    return _rewrite_samples_link(md, name)


def _propagate_samples_remote(name: str, branch: str, md: str, out_dir: Path) -> str:
    if SAMPLES_INCLUDE not in md:
        return md
    samples_md = _fetch_raw(branch, f"modules/{name}/samples.md")
    if samples_md is None:
        return _strip_samples_link(md)
    dest = out_dir / ".samples" / name
    (dest / "samples").mkdir(parents=True, exist_ok=True)
    (dest / "samples.md").write_text(samples_md, "utf-8")
    for cfg in _CFG_INCLUDE_RE.findall(samples_md):
        body = _fetch_raw(branch, f"modules/{name}/samples/{cfg}")
        if body is not None:
            (dest / "samples" / cfg).write_text(body, "utf-8")
    return _rewrite_samples_link(md, name)


def _normalize_title(raw: str) -> str:
    t = raw.strip().strip('"\'').lower()
    if not re.search(r'\bmodule\b', t):
        t = t + ' module'
    return ' '.join(w if w == 'module' else w.upper() for w in t.split())


def _normalize_title_in_md(md: str) -> str:
    # Manual links are absolute (https://web.opensips.org/docs/manual/…) so they
    # work on github.com from the fork; strip the origin to a root-relative path
    # for the on-site build.
    md = md.replace("https://web.opensips.org/docs/", "/docs/")
    if not md.startswith("---"):
        return md
    try:
        end = md.index("---", 3)
    except ValueError:
        return md
    fm = md[:end + 3]
    rest = md[end + 3:]
    fm = re.sub(
        r'^(title:\s*)(.+)$',
        lambda m: m.group(1) + _normalize_title(m.group(2)),
        fm, flags=re.MULTILINE,
    )
    return fm + rest


def _add_sidebar_hidden(md: str) -> str:
    if not md.startswith("---"):
        return md
    end = md.index("---", 3)
    fm = md[:end].rstrip()
    rest = md[end + 3:]
    return fm + "\nsidebar:\n  hidden: true\n---" + rest


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_devel_local(module_names: list[str], verbose: bool) -> tuple[int, int]:
    out_dir = CONTENT_DIR / "devel"
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    for name in module_names:
        src = MODULES_DIR / name / "README.md"
        if not src.exists():
            failed += 1
            continue
        text = _normalize_title_in_md(src.read_text("utf-8"))
        text = _propagate_samples_local(name, text, out_dir)
        (out_dir / f"{name}.md").write_text(text, "utf-8")
        if verbose:
            print(f"  {name}")
        ok += 1
    return ok, failed


def generate_devel_remote(verbose: bool) -> tuple[int, int]:
    module_names = _list_modules_remote(LATEST["branch"])
    if not module_names:
        return 0, 0

    out_dir = CONTENT_DIR / "devel"
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = failed = 0

    def process(name: str) -> tuple[str, str | None]:
        return name, _fetch_readme(LATEST["branch"], name)

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(process, n): n for n in module_names}
        for fut in as_completed(futures):
            name, md = fut.result()
            if md is None:
                failed += 1
                continue
            text = _normalize_title_in_md(md)
            text = _propagate_samples_remote(name, LATEST["branch"], text, out_dir)
            (out_dir / f"{name}.md").write_text(text, "utf-8")
            ok += 1
            if verbose:
                print(f"  {name}")

    return ok, failed


def generate_version(slug: str, branch: str, verbose: bool) -> tuple[int, int]:
    module_names = _list_modules_remote(branch)
    if not module_names:
        return 0, 0

    out_dir = CONTENT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = failed = 0

    def process(name: str) -> tuple[str, str | None]:
        md = _fetch_readme(branch, name)
        if md is None:
            return name, None
        return name, _normalize_title_in_md(md)

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(process, n): n for n in module_names}
        for fut in as_completed(futures):
            name, md = fut.result()
            if md is None:
                failed += 1
                continue
            md = _propagate_samples_remote(name, branch, md, out_dir)
            (out_dir / f"{name}.md").write_text(md, "utf-8")
            ok += 1
            if verbose:
                print(f"  {name}@{branch}")

    return ok, failed


# ---------------------------------------------------------------------------
# Redirect stubs for missing version/module combinations
# ---------------------------------------------------------------------------

def generate_redirects(verbose: bool) -> int:
    """For each version folder, create redirect .md files for modules that
    exist in other versions but not this one, pointing to the nearest version
    (by index in VERSIONS) that does have the module."""

    slugs = [v["slug"] for v in VERSIONS]

    # Build a map of slug → set of module names actually generated
    version_modules: dict[str, set[str]] = {}
    for slug in slugs:
        d = CONTENT_DIR / slug
        if d.exists():
            version_modules[slug] = {p.stem for p in d.glob("*.md")}

    if len(version_modules) < 2:
        return 0  # nothing to cross-reference

    all_modules: set[str] = set().union(*version_modules.values())
    count = 0

    for i, slug in enumerate(slugs):
        if slug not in version_modules:
            continue
        for module in all_modules:
            if module in version_modules[slug]:
                continue  # already exists

            # Find the nearest version (by index distance) that has the module
            target: str | None = None
            for delta in range(1, len(slugs)):
                newer = i - delta
                older = i + delta
                if newer >= 0 and slugs[newer] in version_modules and module in version_modules[slugs[newer]]:
                    target = slugs[newer]
                    break
                if older < len(slugs) and slugs[older] in version_modules and module in version_modules[slugs[older]]:
                    target = slugs[older]
                    break

            if target:
                out = CONTENT_DIR / slug / f"{module}.md"
                out.write_text(
                    f"---\ntitle: ''\nhead:\n  - tag: meta\n    attrs:\n      http-equiv: refresh\n      content: '0; url=/docs/modules/{target}/{module}'\nsidebar:\n  hidden: true\n---\n",
                    "utf-8",
                )
                count += 1
                if verbose:
                    print(f"  {slug}/{module} → {target}/{module}")

    return count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-versions", action="store_true")
    ap.add_argument("--version", metavar="BRANCH_OR_SLUG")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    verbose = not args.quiet

    import shutil
    if CONTENT_DIR.exists():
        shutil.rmtree(CONTENT_DIR)
        print(f"Cleared {CONTENT_DIR}")

    # --- devel (latest) ---
    if MODULES_DIR.exists():
        module_names = sorted(p.name for p in MODULES_DIR.iterdir() if p.is_dir())
        print(f"\n[devel] — {len(module_names)} modules from local files")
        ok, failed = generate_devel_local(module_names, verbose)
    else:
        print(f"\n[devel] — from {FORK}/{LATEST['branch']} on GitHub")
        ok, failed = generate_devel_remote(verbose)
    print(f"  → {ok} OK, {failed} skipped")

    # --- older versions ---
    older = [v for v in VERSIONS if not v.get("is_latest")]

    if args.version:
        match = next(
            (v for v in older if v["branch"] == args.version or v["slug"] == args.version),
            None,
        )
        to_fetch = [match] if match else []
        if not match:
            print(f"[WARN] Unknown version: {args.version!r}")
    elif args.all_versions:
        to_fetch = older
    else:
        to_fetch = []

    for v in to_fetch:
        print(f"\n[{v['slug']}] — from {FORK}/{v['branch']} on GitHub")
        ok, failed = generate_version(v["slug"], v["branch"], verbose)
        print(f"  → {ok} OK, {failed} missing")

    if to_fetch:
        print("\n[redirects] generating stubs for missing version/module combinations")
        n = generate_redirects(verbose)
        print(f"  → {n} redirects created")

    print("\nDone.")


if __name__ == "__main__":
    main()
