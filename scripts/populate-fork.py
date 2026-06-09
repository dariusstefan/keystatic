#!/usr/bin/env python3
"""Populate the dariusstefan/opensips fork with generated README.md docs.

For each supported branch, checks out the branch in opensips/, runs the
DocBook → Markdown converter, commits the README.md files, and pushes to
the 'darius' remote.

Usage:
    python3 scripts/populate-fork.py              # all supported branches
    python3 scripts/populate-fork.py --branch 3.5 # single branch
    python3 scripts/populate-fork.py --dry-run    # show what would happen
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENSIPS_DIR = REPO_ROOT / "opensips"
CONVERTER = REPO_ROOT / "pmwiki-mdx" / "docbook_to_md.py"
MODULES_DIR = OPENSIPS_DIR / "modules"

BRANCHES = ["master", "4.0", "3.6", "3.5", "3.4", "3.3"]
REMOTE = "darius"


def run(cmd, cwd=None, check=True, capture=False):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        cmd, cwd=cwd,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE,  # always capture stderr for error reporting
        text=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() if result.stderr else ""
        print(f"  [ERROR] exit {result.returncode}: {stderr}")
        sys.exit(1)
    elif result.stderr and result.stderr.strip():
        # Print stderr even on success (git often uses stderr for progress)
        for line in result.stderr.strip().splitlines():
            print(f"  {line}")
    return result


def current_branch() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=OPENSIPS_DIR, capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def clear_readmes():
    """Remove generated README.md / samples.md / samples/ to get a clean slate."""
    removed = 0
    for f in MODULES_DIR.glob("*/README.md"):
        f.unlink()
        removed += 1
    for f in MODULES_DIR.glob("*/samples.md"):
        f.unlink()
    for d in MODULES_DIR.glob("*/samples"):
        if d.is_dir():
            shutil.rmtree(d)
    if removed:
        print(f"  Cleared {removed} existing README.md files (+ samples)")


def checkout_branch(branch: str):
    # Try existing local branch first, then create from origin
    r = subprocess.run(
        ["git", "checkout", branch],
        cwd=OPENSIPS_DIR, capture_output=True, text=True,
    )
    if r.returncode != 0:
        run(["git", "checkout", "-b", branch, f"origin/{branch}"], cwd=OPENSIPS_DIR)
    else:
        print(f"  Checked out {branch}")


def generate_readmes():
    print("  Generating README.md files...")
    result = subprocess.run(
        [sys.executable, str(CONVERTER)],
        cwd=REPO_ROOT,
        capture_output=True, text=True,
    )
    # Print any warnings
    for line in result.stderr.splitlines():
        if line.strip():
            print(f"    {line}")
    count = sum(1 for _ in MODULES_DIR.glob("*/README.md"))
    print(f"  Generated {count} README.md files")
    if result.returncode != 0:
        print(f"  [WARN] converter exited with code {result.returncode}")


def commit_and_push(branch: str, dry_run: bool):
    readmes = sorted(MODULES_DIR.glob("*/README.md"))
    if not readmes:
        print("  [WARN] No README.md files to commit")
        return

    rel_paths = [f"modules/{r.parent.name}/README.md" for r in readmes]
    # Also stage generated config-sample overviews and their .cfg folders.
    rel_paths += [f"modules/{s.parent.name}/samples.md"
                  for s in sorted(MODULES_DIR.glob("*/samples.md"))]
    rel_paths += [f"modules/{d.parent.name}/samples"
                  for d in sorted(MODULES_DIR.glob("*/samples")) if d.is_dir()]

    if dry_run:
        print(f"  [DRY RUN] Would git add {len(rel_paths)} paths, commit, and push to {REMOTE}/{branch}")
        return

    # Stage
    run(["git", "add"] + rel_paths, cwd=OPENSIPS_DIR)

    # Check if anything changed
    status = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=OPENSIPS_DIR,
    )
    if status.returncode == 0:
        print("  Nothing new to commit")
    else:
        run(
            ["git", "commit", "-m", "docs: add generated README.md files"],
            cwd=OPENSIPS_DIR,
        )

    # Fetch remote branch and rebase on top of it (handles fork being ahead of local)
    fetch_result = subprocess.run(
        ["git", "fetch", REMOTE, branch],
        cwd=OPENSIPS_DIR, capture_output=True, text=True,
    )
    if fetch_result.returncode == 0:
        # Check if remote branch exists and has commits we don't have
        behind = subprocess.run(
            ["git", "log", "--oneline", f"HEAD..{REMOTE}/{branch}"],
            cwd=OPENSIPS_DIR, capture_output=True, text=True,
        )
        if behind.stdout.strip():
            print(f"  Remote has {len(behind.stdout.strip().splitlines())} extra commits, rebasing...")
            run(["git", "rebase", f"{REMOTE}/{branch}"], cwd=OPENSIPS_DIR)

    run(["git", "push", REMOTE, f"HEAD:{branch}"], cwd=OPENSIPS_DIR)


def process_branch(branch: str, dry_run: bool):
    print(f"\n[{branch}]")
    clear_readmes()
    checkout_branch(branch)
    generate_readmes()
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

    branches = [args.branch] if args.branch else BRANCHES
    original_branch = current_branch()

    print(f"Populating {REMOTE} fork for branches: {', '.join(branches)}")
    print(f"Current branch: {original_branch}")

    try:
        for branch in branches:
            process_branch(branch, dry_run=args.dry_run)
    finally:
        print(f"\nRestoring branch {original_branch}...")
        subprocess.run(["git", "checkout", original_branch], cwd=OPENSIPS_DIR, capture_output=True)

    print("\nDone.")


if __name__ == "__main__":
    main()
