#!/usr/bin/env python3
"""Verify converter changes against every deployed MDX page.

For each MDX currently deployed under src/content/docs/documentation/, this finds
the originating PmWiki page in wiki/, reconverts it fresh into a temp dir, and
diffs the result against the deployed file. This catches the full blast radius of
any convert.py change without depending on (possibly stale) output/ contents.

Usage:
  python3 check_changes.py          # summary + list of changed files
  python3 check_changes.py -v       # also print a unified diff per changed file
"""
import contextlib
import difflib
import io
import os
import sys
import tempfile
from pathlib import Path

import convert

HERE = Path(__file__).parent
WIKI = (HERE / "../wiki").resolve()
CONTENT = (HERE / "../src/content/docs").resolve()
DEPLOYED = CONTENT / "docs"


def _load_resolver():
    """Import scripts/resolve-toc-anchors.py (hyphenated name → importlib)."""
    import importlib.util
    path = HERE / ".." / "scripts" / "resolve-toc-anchors.py"
    spec = importlib.util.spec_from_file_location("resolve_toc_anchors", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def converted_name(wiki_filename: str) -> str:
    """Reproduce convert.py's output-name rule: 'Documentation.Foo-Bar' -> 'foo-bar'."""
    parts = wiki_filename.split(".", 1)
    page = parts[1].lower().replace(".", "-") if len(parts) > 1 else wiki_filename.lower()
    return page


def main() -> int:
    verbose = "-v" in sys.argv

    convert.load_redirects(WIKI)
    convert.load_slug_map(CONTENT)
    convert.load_manual_pages(CONTENT)

    # The deployed pages carry the #toc anchors resolved by the build-time
    # post-pass (scripts/resolve-toc-anchors.py); a fresh conversion still has the
    # raw #tocN. To avoid flagging that as converter drift, apply the same
    # resolution (against the deployed tree's heading index) to the fresh output
    # before comparing, and report any purely-#toc difference under its own mark.
    toc = _load_resolver()
    toc_index = toc.build_index(DEPLOYED)

    # Map converted-name -> wiki source path (only Documentation.* pages).
    source_by_name: dict[str, Path] = {}
    for f in WIKI.iterdir():
        if f.is_file() and f.name.startswith("Documentation.") and "." in f.name:
            source_by_name[converted_name(f.name)] = f

    changed, unchanged, no_source = 0, 0, []
    changed_files = []
    toc_files = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        for deployed in sorted(DEPLOYED.glob("*.md")):
            stem = deployed.stem
            src = source_by_name.get(stem)
            if src is None:
                no_source.append(stem)
                continue
            out = tmp_dir / f"{stem}.md"
            with contextlib.redirect_stdout(io.StringIO()):
                convert.convert_file(src, out)
            new = out.read_text(encoding="utf-8")
            old = deployed.read_text(encoding="utf-8")
            if new == old:
                unchanged += 1
            elif toc.resolve_text(new, stem, toc_index) == old:
                # Only difference is the build-time #toc anchor resolution — not
                # converter drift. Track separately so it doesn't read as a regression.
                toc_files.append(stem)
            else:
                changed += 1
                changed_files.append(stem)
                if verbose:
                    print(f"===== {stem} =====")
                    sys.stdout.writelines(
                        difflib.unified_diff(
                            old.splitlines(keepends=True),
                            new.splitlines(keepends=True),
                            fromfile=f"deployed/{stem}.md",
                            tofile=f"converted/{stem}.md",
                        )
                    )

    print("\n── Summary ─────────────────────────────")
    print(f"  changed:     {changed}")
    print(f"  unchanged:   {unchanged}")
    print(f"  toc-resolved:{len(toc_files)} (only build-time #toc resolution differs; not drift)")
    print(f"  no source:   {len(no_source)} (renamed/hand-authored, not reconvertible)")
    if changed_files:
        print("────────────────────────────────────────")
        for s in changed_files:
            print(f"  DIFF  {s}")
    if toc_files:
        print("────────────────────────────────────────")
        for s in toc_files:
            print(f"  TOC   {s}")
    if no_source:
        print("────────────────────────────────────────")
        for s in no_source:
            print(f"  NOSRC {s}")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
