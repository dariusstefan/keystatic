#!/usr/bin/env python3
"""Generate Starlight Markdown pages for all OpenSIPS modules.

Latest version (master): reads from local opensips/modules/*/README.md — instant.
Other versions:          fetches README.md from the dariusstefan/opensips fork on GitHub.

Usage:
    python3 scripts/generate-module-docs.py                 # latest only
    python3 scripts/generate-module-docs.py --all-versions  # all versions
    python3 scripts/generate-module-docs.py --version 3.5   # one extra version
"""

import argparse
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "opensips" / "modules"
CONTENT_DIR = REPO_ROOT / "src" / "content" / "docs" / "modules"

FORK = "dariusstefan/opensips"
GITHUB_RAW = f"https://raw.githubusercontent.com/{FORK}"

VERSIONS = [
    {"branch": "master", "label": "master (dev)", "is_latest": True},
    {"branch": "4.0",    "label": "4.0"},
    {"branch": "3.6",    "label": "3.6"},
    {"branch": "3.5",    "label": "3.5"},
    {"branch": "3.4",    "label": "3.4"},
    {"branch": "3.3",    "label": "3.3"},
]

LATEST_BRANCH = next(v["branch"] for v in VERSIONS if v.get("is_latest"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _normalize_title(raw: str) -> str:
    """Normalize a module doc title to consistent lowercase 'name module' format."""
    t = raw.strip().strip('"\'').lower()
    if not re.search(r'\bmodule\b', t):
        t = t + ' module'
    return t


def _normalize_title_in_md(md: str) -> str:
    """Rewrite the title field in YAML frontmatter using _normalize_title."""
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
    """Insert sidebar.hidden into existing YAML frontmatter."""
    if not md.startswith("---"):
        return md
    end = md.index("---", 3)
    fm = md[:end].rstrip()
    rest = md[end + 3:]
    return fm + "\nsidebar:\n  hidden: true\n---" + rest


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_latest_local(module_names: list[str], verbose: bool) -> tuple[int, int]:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    for name in module_names:
        src = MODULES_DIR / name / "README.md"
        if not src.exists():
            failed += 1
            continue
        (CONTENT_DIR / f"{name}.md").write_text(_normalize_title_in_md(src.read_text("utf-8")), "utf-8")
        if verbose:
            print(f"  {name}")
        ok += 1
    return ok, failed


def generate_latest_remote(verbose: bool) -> tuple[int, int]:
    """Fetch master README.md files from the fork (used when no local clone)."""
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    ok = failed = 0

    # Discover module names from the GitHub API tree
    api_url = f"https://api.github.com/repos/{FORK}/git/trees/{LATEST_BRANCH}?recursive=0"
    try:
        with urllib.request.urlopen(api_url, timeout=30) as r:
            import json
            tree = json.loads(r.read())
        module_names = sorted(
            item["path"].removeprefix("modules/")
            for item in tree.get("tree", [])
            if item["path"].startswith("modules/") and item["type"] == "tree"
            and item["path"].count("/") == 1
        )
    except Exception as exc:
        print(f"  [ERROR] Could not list modules from GitHub: {exc}")
        return 0, 0

    def process(name: str) -> tuple[str, str | None]:
        return name, _fetch_readme(LATEST_BRANCH, name)

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(process, n): n for n in module_names}
        for fut in as_completed(futures):
            name, md = fut.result()
            if md is None:
                failed += 1
                continue
            (CONTENT_DIR / f"{name}.md").write_text(_normalize_title_in_md(md), "utf-8")
            ok += 1
            if verbose:
                print(f"  {name}")

    return ok, failed


def generate_version(module_names: list[str], branch: str, verbose: bool) -> tuple[int, int]:
    ok = failed = 0

    def process(name: str) -> tuple[str, str | None]:
        md = _fetch_readme(branch, name)
        if md is None:
            return name, None
        return name, _normalize_title_in_md(_add_sidebar_hidden(md))

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(process, n): n for n in module_names}
        for fut in as_completed(futures):
            name, md = fut.result()
            if md is None:
                failed += 1
                continue
            out_dir = CONTENT_DIR / name
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{branch.replace('.', '-')}.md").write_text(md, "utf-8")
            ok += 1
            if verbose:
                print(f"  {name}@{branch}")

    return ok, failed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-versions", action="store_true")
    ap.add_argument("--version", metavar="BRANCH")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    verbose = not args.quiet
    other_versions = [v for v in VERSIONS if not v.get("is_latest")]

    if MODULES_DIR.exists():
        module_names = sorted(p.name for p in MODULES_DIR.iterdir() if p.is_dir())
        print(f"Generating docs for {len(module_names)} modules...")
        print(f"\n[{LATEST_BRANCH}] latest — from local files")
        ok, failed = generate_latest_local(module_names, verbose)
        print(f"  → {ok} OK, {failed} skipped")
    else:
        print(f"No local opensips/ clone found — fetching from {FORK} on GitHub")
        print(f"\n[{LATEST_BRANCH}] latest — from {FORK} on GitHub")
        ok, failed = generate_latest_remote(verbose)
        module_names = sorted(p.stem for p in CONTENT_DIR.glob("*.md"))
        print(f"  → {ok} OK, {failed} missing")

    branches_to_fetch: list[str] = []
    if args.version:
        branches_to_fetch = [args.version]
    elif args.all_versions:
        branches_to_fetch = [v["branch"] for v in other_versions]

    for branch in branches_to_fetch:
        print(f"\n[{branch}] — from {FORK} on GitHub")
        ok, failed = generate_version(module_names, branch, verbose)
        print(f"  → {ok} OK, {failed} missing")

    print("\nDone.")


if __name__ == "__main__":
    main()
