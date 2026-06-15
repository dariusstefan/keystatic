#!/usr/bin/env python3
"""Rewrite cross-page links that point at a module heading whose anchor id
changed when explicit {#id} markers were dropped from module READMEs.

Module heading anchors are now generated at build time by
src/utils/remarkModuleAnchors.mjs. Same-page links inside a module are already
remapped by the DocBook converter; this pass fixes links FROM other pages
(manual, flat docs) that target a module anchor by its legacy id.

Input:  src/data/module-anchors.json  — {"<slug>/<module>": {legacy_id: new_id}}
        (written by generate-module-docs.py)
Scope:  src/content/docs/docs/**/*.md  links of the form
        ](…/docs/modules/<slug>/<module>#<anchor>)

Idempotent: a link already pointing at a current id is left untouched.
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "src" / "content" / "docs" / "docs"

# (section, map file): cross-page links to module / manual pages, keyed by
# "<slug>/<page>" → {legacy_id: generated_id}.
SECTIONS = (
    ("modules", REPO_ROOT / "src" / "data" / "module-anchors.json"),
    ("manual", REPO_ROOT / "src" / "data" / "manual-anchors.json"),
)


def main() -> None:
    rewrites = 0
    files = set()

    for section, map_file in SECTIONS:
        if not map_file.exists():
            print(f"[resolve-module-links] no map at {map_file} — skipping {section}")
            continue
        anchor_map = json.loads(map_file.read_text("utf-8"))
        if not anchor_map:
            continue
        link_re = re.compile(
            rf"(\]\([^)]*?/docs/{section}/([\w.-]+)/([\w.-]+)#)([^)\s]+)(\))")

        def repl(m: re.Match) -> str:
            nonlocal rewrites
            slug, page, anchor = m.group(2), m.group(3), m.group(4)
            new = anchor_map.get(f"{slug}/{page}", {}).get(anchor)
            if new and new != anchor:
                rewrites += 1
                return f"{m.group(1)}{new}{m.group(5)}"
            return m.group(0)

        for md in CONTENT_DIR.rglob("*.md"):
            text = md.read_text("utf-8")
            new_text = link_re.sub(repl, text)
            if new_text != text:
                md.write_text(new_text, "utf-8")
                files.add(md)

    print(f"[resolve-module-links] rewrote {rewrites} cross-page anchors in {len(files)} files")


if __name__ == "__main__":
    main()
