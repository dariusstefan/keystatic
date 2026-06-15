#!/usr/bin/env python3
"""Populate the dariusstefan/opensips fork with the generated manual docs/.

Mirrors populate-fork.py (which does the module READMEs), but for the OpenSIPS
Manual: for each supported branch, checks out the branch in opensips/, runs the
PmWiki → Markdown manual converter for that branch's version into opensips/docs/,
commits the docs/ files, and pushes to the 'darius' remote.

Each branch carries only its own version's manual, so the converter drops the
-X-Y suffix and writes a flat docs/ (README.md index + sibling .md pages) with
relative .md links between them.

Usage:
    python3 scripts/populate-fork-manual.py              # all supported branches
    python3 scripts/populate-fork-manual.py --branch 4.0 # single branch
    python3 scripts/populate-fork-manual.py --dry-run    # show what would happen
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENSIPS_DIR = REPO_ROOT / "opensips"
CONVERTER = REPO_ROOT / "converters" / "convert.py"
WIKI_DIR = REPO_ROOT / "wiki"
DOCS_DIR = OPENSIPS_DIR / "docs"

# Aggregate anchor map (legacy id → generated id), keyed by "<slug>/<page>".
# Built from the converter's per-page sidecars; the sidecars are NEVER pushed.
ANCHOR_MAP: dict[str, dict] = {}
ANCHOR_MAP_FILE = REPO_ROOT / "src" / "data" / "manual-anchors.json"


def _slug(branch: str) -> str:
    return "devel" if branch == "master" else branch.replace(".", "-")


def collect_anchors(branch: str) -> None:
    slug = _slug(branch)
    for sc in DOCS_DIR.glob("*.anchors.json"):
        try:
            data = json.loads(sc.read_text("utf-8"))
        except Exception:
            continue
        if data:
            ANCHOR_MAP[f"{slug}/{sc.name[:-len('.anchors.json')].lower()}"] = data


def write_anchor_map() -> None:
    if not ANCHOR_MAP:
        return
    existing = {}
    if ANCHOR_MAP_FILE.exists():
        try:
            existing = json.loads(ANCHOR_MAP_FILE.read_text("utf-8"))
        except Exception:
            existing = {}
    existing.update(ANCHOR_MAP)
    ANCHOR_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    ANCHOR_MAP_FILE.write_text(json.dumps(existing, indent=0, sort_keys=True), "utf-8")
    print(f"  → anchor map: {len(ANCHOR_MAP)} pages this run, {len(existing)} total")

# Branch -> manual version in the wiki dump. 'master' tracks the latest (devel)
# manual; release branches map to their matching version.
BRANCH_VERSION = {
    "master": "4-1",
    "4.0": "4-0",
    "3.6": "3-6",
    "3.5": "3-5",
    "3.4": "3-4",
    "3.3": "3-3",
    "3.2": "3-2",
    "3.1": "3-1",
    "3.0": "3-0",
    "2.4": "2-4",
    "2.3": "2-3",
    "2.2": "2-2",
    "2.1": "2-1",
    "1.11": "1-11",
    "1.10": "1-10",
    "1.9": "1-9",
    "1.8": "1-8",
    "1.7": "1-7",
    "1.6": "1-6",
    "1.5": "1-5",
    "1.4": "1-4",
}
BRANCHES = list(BRANCH_VERSION.keys())
REMOTE = "darius"


def run(cmd, cwd=None, check=True, capture=False):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        cmd, cwd=cwd,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else ""
        print(f"  [ERROR] exit {result.returncode}: {stderr}")
        sys.exit(1)
    elif result.stderr and result.stderr.strip():
        for line in result.stderr.strip().splitlines():
            print(f"  {line}")
    return result


def current_branch() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=OPENSIPS_DIR, capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def clear_docs():
    """Remove generated manual files so each run starts from a clean slate."""
    if not DOCS_DIR.exists():
        return
    removed = 0
    for f in DOCS_DIR.glob("*.md"):
        f.unlink()
        removed += 1
    for f in DOCS_DIR.glob("*.anchors.json"):
        f.unlink()
    if removed:
        print(f"  Cleared {removed} existing docs/*.md files")


def checkout_branch(branch: str):
    r = subprocess.run(
        ["git", "checkout", branch],
        cwd=OPENSIPS_DIR, capture_output=True, text=True,
    )
    if r.returncode != 0:
        run(["git", "checkout", "-b", branch, f"origin/{branch}"], cwd=OPENSIPS_DIR)
    else:
        print(f"  Checked out {branch}")


def generate_docs(version: str, devel: bool = False):
    print(f"  Generating manual {version} → docs/ ...")
    cmd = [sys.executable, str(CONVERTER),
           "--manual", version, "--wiki", str(WIKI_DIR), "--out", str(DOCS_DIR)]
    if devel:
        cmd.append("--devel")
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    for line in result.stderr.splitlines():
        if line.strip():
            print(f"    {line}")
    count = sum(1 for _ in DOCS_DIR.glob("*.md"))
    print(f"  Generated {count} docs/*.md files")
    if result.returncode != 0:
        print(f"  [WARN] converter exited with code {result.returncode}")
        print(f"    {result.stdout.strip().splitlines()[-1] if result.stdout else ''}")


def commit_and_push(branch: str, dry_run: bool):
    docs = sorted(DOCS_DIR.glob("*.md"))
    if not docs:
        print("  [WARN] No docs/*.md files to commit")
        return
    rel_paths = [f"docs/{d.name}" for d in docs]
    # Anchor sidecars are aggregated locally (collect_anchors) and NOT pushed.
    # Untrack any that earlier runs committed, then drop the local copies.
    subprocess.run("git ls-files -z 'docs/*.anchors.json' | xargs -0 -r git rm -q --cached",
                   cwd=OPENSIPS_DIR, shell=True, capture_output=True)
    for sc in DOCS_DIR.glob("*.anchors.json"):
        sc.unlink()

    if dry_run:
        print(f"  [DRY RUN] Would git add {len(rel_paths)} files, commit, and push to {REMOTE}/{branch}")
        return

    run(["git", "add"] + rel_paths, cwd=OPENSIPS_DIR)

    status = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=OPENSIPS_DIR)
    if status.returncode == 0:
        print("  Nothing new to commit")
    else:
        run(["git", "commit", "-m", "docs: add generated manual"], cwd=OPENSIPS_DIR)

    fetch_result = subprocess.run(
        ["git", "fetch", REMOTE, branch],
        cwd=OPENSIPS_DIR, capture_output=True, text=True,
    )
    if fetch_result.returncode == 0:
        behind = subprocess.run(
            ["git", "log", "--oneline", f"HEAD..{REMOTE}/{branch}"],
            cwd=OPENSIPS_DIR, capture_output=True, text=True,
        )
        if behind.stdout.strip():
            print(f"  Remote has {len(behind.stdout.strip().splitlines())} extra commits, rebasing...")
            run(["git", "rebase", f"{REMOTE}/{branch}"], cwd=OPENSIPS_DIR)

    run(["git", "push", REMOTE, f"HEAD:{branch}"], cwd=OPENSIPS_DIR)


def process_branch(branch: str, dry_run: bool):
    version = BRANCH_VERSION[branch]
    print(f"\n[{branch}]  (manual {version})")
    clear_docs()
    checkout_branch(branch)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    generate_docs(version, devel=(branch == "master"))
    collect_anchors(branch)  # read sidecars before commit_and_push drops them
    commit_and_push(branch, dry_run)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--branch", metavar="BRANCH", help="Process a single branch instead of all")
    ap.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
    args = ap.parse_args()

    if not OPENSIPS_DIR.exists():
        print(f"Error: {OPENSIPS_DIR} does not exist")
        sys.exit(1)
    if not CONVERTER.exists():
        print(f"Error: {CONVERTER} does not exist")
        sys.exit(1)
    if args.branch and args.branch not in BRANCH_VERSION:
        print(f"Error: unknown branch '{args.branch}'. Known: {', '.join(BRANCHES)}")
        sys.exit(1)

    branches = [args.branch] if args.branch else BRANCHES
    original_branch = current_branch()

    print(f"Populating {REMOTE} fork (manual) for branches: {', '.join(branches)}")
    print(f"Current branch: {original_branch}")

    try:
        for branch in branches:
            process_branch(branch, dry_run=args.dry_run)
    finally:
        print(f"\nRestoring branch {original_branch}...")
        subprocess.run(["git", "checkout", original_branch], cwd=OPENSIPS_DIR, capture_output=True)

    if not args.dry_run:
        write_anchor_map()

    print("\nDone.")


if __name__ == "__main__":
    main()
