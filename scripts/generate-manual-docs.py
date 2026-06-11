#!/usr/bin/env python3
"""Generate Starlight Markdown pages for the OpenSIPS Manual, per version.

Counterpart to generate-module-docs.py, but for the Manual. Copies the manual
docs/ that populate-fork-manual.py pushed to the fork into the website content
tree, and adapts the in-repo relative .md links into website URLs.

Content layout:
  src/content/docs/manual/devel/index.md      ← master branch (README.md)
  src/content/docs/manual/devel/<page>.md     ← master branch
  src/content/docs/manual/4-0/<page>.md        ← 4.0 branch
  ... etc.

Link adaptation (the build-time half of the link strategy — the repo keeps
GitHub-friendly relative .md links, the website gets slugs):
  [x](Script-CoreVar.md)        → [x](/manual/<slug>/script-corevar)
  [x](Script-CoreVar.md#anchor) → [x](/manual/<slug>/script-corevar#anchor)
  [x](README.md)                → [x](/manual/<slug>)

devel is read from the local opensips/docs/ working tree; older versions are
fetched from the fork on GitHub (same as the modules generator).

Usage:
    python3 scripts/generate-manual-docs.py                 # devel only
    python3 scripts/generate-manual-docs.py --all-versions  # all versions
    python3 scripts/generate-manual-docs.py --version 3.5   # one extra version
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENSIPS_DIR = REPO_ROOT / "opensips"
LOCAL_DOCS = REPO_ROOT / "opensips" / "docs"
CONTENT_DIR = REPO_ROOT / "src" / "content" / "docs" / "docs" / "manual"

FORK = "dariusstefan/opensips"
GITHUB_RAW = f"https://raw.githubusercontent.com/{FORK}"
GITHUB_API = f"https://api.github.com/repos/{FORK}"

VERSIONS = [
    {"branch": "master", "slug": "devel", "label": "master (dev)", "is_latest": True},
    {"branch": "4.0",    "slug": "4-0",   "label": "4.0"},
    {"branch": "3.6",    "slug": "3-6",   "label": "3.6"},
    {"branch": "3.5",    "slug": "3-5",   "label": "3.5"},
    {"branch": "3.4",    "slug": "3-4",   "label": "3.4"},
    {"branch": "3.3",    "slug": "3-3",   "label": "3.3"},
    {"branch": "3.2",    "slug": "3-2",   "label": "3.2"},
    {"branch": "3.1",    "slug": "3-1",   "label": "3.1"},
    {"branch": "3.0",    "slug": "3-0",   "label": "3.0"},
    {"branch": "2.4",    "slug": "2-4",   "label": "2.4"},
    {"branch": "2.3",    "slug": "2-3",   "label": "2.3"},
    {"branch": "2.2",    "slug": "2-2",   "label": "2.2"},
    {"branch": "2.1",    "slug": "2-1",   "label": "2.1"},
    {"branch": "1.11",   "slug": "1-11",  "label": "1.11"},
    {"branch": "1.10",   "slug": "1-10",  "label": "1.10"},
    {"branch": "1.9",    "slug": "1-9",   "label": "1.9"},
    {"branch": "1.8",    "slug": "1-8",   "label": "1.8"},
    {"branch": "1.7",    "slug": "1-7",   "label": "1.7"},
    {"branch": "1.6",    "slug": "1-6",   "label": "1.6"},
    {"branch": "1.5",    "slug": "1-5",   "label": "1.5"},
    {"branch": "1.4",    "slug": "1-4",   "label": "1.4"},
]
LATEST = next(v for v in VERSIONS if v.get("is_latest"))


# ---------------------------------------------------------------------------
# Filename <-> slug, and link adaptation
# ---------------------------------------------------------------------------

def content_filename(repo_name: str) -> str:
    """Repo docs filename → website content filename.
    README.md → index.md (section root); everything else lowercased."""
    if repo_name == "README.md":
        return "index.md"
    return repo_name.lower()


def adapt_links(md: str, slug: str) -> str:
    """Rewrite in-repo relative .md links to website URLs.
    - in-manual page  (Foo.md)                  → /docs/manual/<slug>/foo
    - the index       (README.md)               → /docs/manual/<slug>
    - module cross-link (../modules/<m>/README.md, Stage-2 of the manual Modules
      page) → /docs/modules/<slug>/<m>
    Leaves external (http) and absolute (/...) links untouched."""
    base = f"/docs/manual/{slug}"
    mod_base = f"/docs/modules/{slug}"

    def repl(m: re.Match) -> str:
        label, target = m.group(1), m.group(2)
        file, _, anchor = target.partition("#")
        mod = re.match(r"^\.\./modules/([\w.-]+)/README\.md$", file)
        if mod:
            url = f"{mod_base}/{mod.group(1)}"
        else:
            stem = file[:-3]  # strip .md
            url = base if stem == "README" else f"{base}/{stem.lower()}"
        if anchor:
            url += f"#{anchor}"
        return f"[{label}]({url})"

    # [label](relative.md) or [label](relative.md#anchor) — not http(s):, not /absolute
    md = re.sub(
        r"\[([^\]]*)\]\((?!https?:|/)([^)\s]+?\.md(?:#[^)\s]*)?)\)",
        repl, md,
    )
    # Manual links to website-only flat pages are absolute (https://web.opensips.org/docs/…)
    # so they work on github.com; strip the origin to a root-relative path for the site.
    md = md.replace("https://web.opensips.org/docs/", "/docs/")
    return md


# ---------------------------------------------------------------------------
# Sourcing pages (local working tree for devel, fork on GitHub for older)
# ---------------------------------------------------------------------------

def _list_docs_remote(branch: str) -> list[str]:
    url = f"{GITHUB_API}/git/trees/{branch}?recursive=0"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            tree = json.loads(r.read())
        return sorted(
            item["path"].removeprefix("docs/")
            for item in tree.get("tree", [])
            if item["path"].startswith("docs/") and item["type"] == "blob"
            and item["path"].endswith(".md") and item["path"].count("/") == 1
        )
    except Exception as exc:
        print(f"  [ERROR] Could not list docs for branch {branch!r}: {exc}")
        return []


def _fetch_doc_remote(branch: str, name: str) -> str | None:
    url = f"{GITHUB_RAW}/{branch}/docs/{name}"
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


# raw.githubusercontent caches ~5 min, so right after a fork push it serves
# STALE docs for older versions. When the branch is present in the local
# opensips/ checkout (e.g. just after populate-fork-manual), read from there
# instead — always fresh, no CDN lag. Falls back to the remote otherwise.
def _git_show(branch: str, path: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(OPENSIPS_DIR), "show", f"{branch}:{path}"],
            capture_output=True, text=True,
        )
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def _list_docs_local(branch: str) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(OPENSIPS_DIR), "ls-tree", "--name-only", f"{branch}:docs"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            return []
    except Exception:
        return []
    return sorted(
        n for n in r.stdout.splitlines() if n.endswith(".md")
    )


def generate_devel_local(verbose: bool) -> tuple[int, int]:
    slug = LATEST["slug"]
    out_dir = CONTENT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    for src in sorted(LOCAL_DOCS.glob("*.md")):
        md = adapt_links(src.read_text("utf-8"), slug)
        (out_dir / content_filename(src.name)).write_text(md, "utf-8")
        ok += 1
        if verbose:
            print(f"  {src.name} → {content_filename(src.name)}")
    if not ok:
        failed = 1
        print(f"  [WARN] No docs found in {LOCAL_DOCS} (is opensips/ on master?)")
    return ok, failed


def generate_version(slug: str, branch: str, verbose: bool) -> tuple[int, int]:
    use_local = bool(_list_docs_local(branch))
    names = _list_docs_local(branch) if use_local else _list_docs_remote(branch)
    if not names:
        return 0, 0
    if use_local and verbose:
        print(f"  (source: local opensips git {branch}:docs/)")
    out_dir = CONTENT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = failed = 0

    def process(name: str) -> tuple[str, str | None]:
        if use_local:
            return name, _git_show(branch, f"docs/{name}")
        return name, _fetch_doc_remote(branch, name)

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(process, n): n for n in names}
        for fut in as_completed(futures):
            name, md = fut.result()
            if md is None:
                failed += 1
                continue
            (out_dir / content_filename(name)).write_text(adapt_links(md, slug), "utf-8")
            ok += 1
            if verbose:
                print(f"  {name}@{branch}")
    return ok, failed


# ---------------------------------------------------------------------------
# Redirect stubs for pages missing from some versions
# ---------------------------------------------------------------------------

def generate_redirects(verbose: bool) -> int:
    """For each version folder, create hidden redirect .md files for pages that
    exist in other versions but not this one, pointing to the nearest version
    (by index in VERSIONS) that does have the page. Mirrors the modules
    generator so a version switch never 404s on a page absent from a version."""
    slugs = [v["slug"] for v in VERSIONS]

    version_pages: dict[str, set[str]] = {}
    for slug in slugs:
        d = CONTENT_DIR / slug
        if d.exists():
            # 'index' is the manual root (every version has it); never redirect it.
            version_pages[slug] = {p.stem for p in d.glob("*.md") if p.stem != "index"}

    if len(version_pages) < 2:
        return 0

    all_pages: set[str] = set().union(*version_pages.values())
    count = 0

    for i, slug in enumerate(slugs):
        if slug not in version_pages:
            continue
        for page in all_pages:
            if page in version_pages[slug]:
                continue  # already exists

            target: str | None = None
            for delta in range(1, len(slugs)):
                newer = i - delta
                older = i + delta
                if newer >= 0 and slugs[newer] in version_pages and page in version_pages[slugs[newer]]:
                    target = slugs[newer]
                    break
                if older < len(slugs) and slugs[older] in version_pages and page in version_pages[slugs[older]]:
                    target = slugs[older]
                    break

            if target:
                out = CONTENT_DIR / slug / f"{page}.md"
                out.write_text(
                    f"---\ntitle: ''\nhead:\n  - tag: meta\n    attrs:\n      http-equiv: refresh\n      content: '0; url=/docs/manual/{target}/{page}'\nsidebar:\n  hidden: true\n---\n",
                    "utf-8",
                )
                count += 1
                if verbose:
                    print(f"  {slug}/{page} → {target}/{page}")

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

    if CONTENT_DIR.exists():
        shutil.rmtree(CONTENT_DIR)
        print(f"Cleared {CONTENT_DIR}")

    # devel (latest) from the local working tree
    print(f"\n[devel] — from {LOCAL_DOCS}")
    ok, failed = generate_devel_local(verbose)
    print(f"  → {ok} OK, {failed} skipped")

    older = [v for v in VERSIONS if not v.get("is_latest")]
    if args.version:
        match = next((v for v in older if args.version in (v["branch"], v["slug"])), None)
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

    # The "DB schema" page is generated from db/schema/*.xml (the PmWiki converter
    # leaves it an empty stub). Run it now, for the same version set, so it fills
    # the stub before the redirect pass scans for missing pages.
    print("\n[install-dbschema] generating from db/schema/*.xml")
    db_cmd = [sys.executable, str(REPO_ROOT / "scripts" / "generate-dbschema.py")]
    if args.all_versions:
        db_cmd.append("--all-versions")
    elif args.version:
        db_cmd += ["--version", args.version]
    if args.quiet:
        db_cmd.append("--quiet")
    subprocess.run(db_cmd, check=False)

    if to_fetch:
        print("\n[redirects] generating stubs for pages missing from some versions")
        n = generate_redirects(verbose)
        print(f"  → {n} redirects created")

    print("\nDone.")


if __name__ == "__main__":
    main()
