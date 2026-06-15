#!/usr/bin/env python3
"""Fetch the flat documentation pages from the opensips-docs repo.

Counterpart to generate-module-docs.py / generate-manual-docs.py, but for the
"flat" docs (migration guides, tutorials, troubleshooting, etc.). Unlike the
manual and modules, these pages are not versioned: there is a single set,
maintained in its own repo, and copied verbatim into the website content tree.

The pages already carry website-ready links (root-relative /docs/... URLs
produced by the PmWiki converter), so no link adaptation is needed here.

Content layout:
  src/content/docs/docs/<page>.md   ← flat page (top level, beside manual/ & modules/)

devel/older has no meaning here, so there are no flags — it always fetches the
full set from the repo on GitHub.

Usage:
    python3 scripts/generate-flat-docs.py
    python3 scripts/generate-flat-docs.py --quiet
"""

import argparse
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "src" / "content" / "docs" / "docs"

REPO = "dariusstefan/opensips-docs"
BRANCH = "master"
GITHUB_RAW = f"https://raw.githubusercontent.com/{REPO}"
GITHUB_API = f"https://api.github.com/repos/{REPO}"

# Prefer a sibling checkout (../opensips-docs) when present: it's always fresh,
# avoiding the ~5 min raw.githubusercontent CDN lag after a push (mirrors the
# local-first behaviour of the module/manual generators).
LOCAL_DOCS = REPO_ROOT.parent / "opensips-docs" / "docs"


def _list_docs_local() -> list[str] | None:
    if not LOCAL_DOCS.is_dir():
        return None
    return sorted(p.name for p in LOCAL_DOCS.glob("*.md"))


def _fetch_doc_local(name: str) -> str | None:
    p = LOCAL_DOCS / name
    return p.read_text("utf-8", errors="replace") if p.is_file() else None


def _list_docs_remote() -> list[str]:
    """Top-level docs/*.md page names on the repo's default branch."""
    url = f"{GITHUB_API}/git/trees/{BRANCH}?recursive=1"
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
        print(f"  [ERROR] Could not list docs from {REPO}: {exc}")
        return []


def _fetch_doc_remote(name: str) -> str | None:
    url = f"{GITHUB_RAW}/{BRANCH}/docs/{name}"
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    verbose = not args.quiet

    use_local = _list_docs_local()
    names = use_local if use_local else _list_docs_remote()
    if not names:
        print("[ERROR] No flat docs found — aborting (leaving existing files in place).")
        raise SystemExit(1)

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Clear out any previously-fetched flat pages (top level only; never touch
    # the manual/ and modules/ subdirectories, which other generators own).
    removed = 0
    for f in CONTENT_DIR.glob("*.md"):
        f.unlink()
        removed += 1
    if removed:
        print(f"Cleared {removed} existing flat docs/*.md files")

    src = f"local {LOCAL_DOCS}" if use_local else f"{REPO}/{BRANCH} on GitHub"
    print(f"\n[flat docs] — from {src}")
    ok = failed = 0

    def process(name: str) -> tuple[str, str | None]:
        text = _fetch_doc_local(name) if use_local else _fetch_doc_remote(name)
        return name, text

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(process, n): n for n in names}
        for fut in as_completed(futures):
            name, md = fut.result()
            if md is None:
                failed += 1
                continue
            (CONTENT_DIR / name).write_text(md, "utf-8")
            ok += 1
            if verbose:
                print(f"  {name}")

    print(f"  → {ok} OK, {failed} missing")
    print("\nDone.")


if __name__ == "__main__":
    main()
