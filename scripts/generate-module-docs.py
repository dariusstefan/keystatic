#!/usr/bin/env python3
"""Generate Starlight Markdown pages for all OpenSIPS modules.

Latest version (master): reads from local opensips/modules/*/README.md — instant.
Other versions:          fetches DocBook XML from GitHub and converts — ~1-2 min.

Usage:
    python3 scripts/generate-module-docs.py                 # latest only
    python3 scripts/generate-module-docs.py --all-versions  # all versions
    python3 scripts/generate-module-docs.py --version 3.5   # one extra version
"""

import argparse
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "pmwiki-mdx"))

import xml.etree.ElementTree as ET
from docbook_to_md import (
    MODULES_DIR,
    XML_ENTITIES,
    _Emitter,
    _extract_description,
    _extract_system_entities,
    _extract_text_entities,
    _inline,
    _resolve_values,
    _strip_doctype,
    _subst,
)

CONTENT_DIR = REPO_ROOT / "src" / "content" / "docs" / "modules"
GITHUB_RAW = "https://raw.githubusercontent.com/OpenSIPS/opensips"

VERSIONS = [
    {"branch": "master", "label": "master (dev)", "is_latest": True},
    {"branch": "4.0", "label": "4.0"},
    {"branch": "3.6", "label": "3.6"},
    {"branch": "3.5", "label": "3.5"},
    {"branch": "3.4", "label": "3.4"},
    {"branch": "3.3", "label": "3.3"},
]

LATEST_BRANCH = next(v["branch"] for v in VERSIONS if v.get("is_latest"))


# ---------------------------------------------------------------------------
# GitHub fetch helpers
# ---------------------------------------------------------------------------

def _fetch(branch: str, path: str) -> str | None:
    url = f"{GITHUB_RAW}/{branch}/{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError:
        return None
    except Exception as exc:
        print(f"  [WARN] fetch {url}: {exc}", file=sys.stderr)
        return None


def _fetch_global_entities(branch: str) -> dict:
    raw = _fetch(branch, "doc/entities.xml") or ""
    ents = _extract_text_entities(raw)
    ents.setdefault("nbsp", " ")
    _resolve_values(ents)
    return ents


def _fetch_combined_xml(module_name: str, branch: str, global_entities: dict) -> str | None:
    text = _fetch(branch, f"modules/{module_name}/doc/{module_name}.xml")
    if text is None:
        return None

    entities: dict = dict(global_entities)

    # Module-local text entities from the DOCTYPE
    entities.update(_extract_text_entities(text))
    _resolve_values(entities)

    # SYSTEM file entities — resolve paths relative to modules/<name>/doc/
    for ent_name, rel_path in _extract_system_entities(text).items():
        if rel_path.startswith("../../"):
            gh_path = f"modules/{rel_path[6:]}"
        elif rel_path.startswith("../"):
            gh_path = f"modules/{module_name}/{rel_path[3:]}"
        else:
            gh_path = f"modules/{module_name}/doc/{rel_path}"

        content = _fetch(branch, gh_path) or ""
        content = re.sub(r"^\s*<!--.*?-->\s*", "", content, flags=re.DOTALL)
        entities[ent_name] = content

    # Strip XML declaration + DOCTYPE
    text = re.sub(r"<\?xml[^?]*\?>", "", text)
    text = _strip_doctype(text)

    # Substitute custom entities iteratively
    for _ in range(10):
        new = _subst(text, entities, skip=XML_ENTITIES)
        if new == text:
            break
        text = new

    # Escape any remaining undefined entity references
    def _escape(m):
        n = m.group(1)
        return m.group(0) if n in XML_ENTITIES else f"&amp;{n};"

    text = re.sub(r"&([\w.-]+);", _escape, text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    return f"<root>{text.strip()}</root>"


def _convert_from_github(module_name: str, branch: str, global_entities: dict) -> str | None:
    xml_str = _fetch_combined_xml(module_name, branch, global_entities)
    if xml_str is None:
        return None

    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as exc:
        print(f"  [WARN] XML parse error {module_name}@{branch}: {exc}", file=sys.stderr)
        return None

    # Title from bookinfo
    title = module_name
    for elem in root.iter():
        if (elem.tag or "").lower() == "bookinfo":
            for child in elem:
                if (child.tag or "").lower() == "title":
                    title = _inline(child).strip()
                    break
            break

    description = re.sub(r"\s+", " ", _extract_description(root)).strip()
    body = _Emitter().emit(root)

    fm = f'---\ntitle: "{title.replace(chr(34), chr(92)+chr(34))}"\n'
    if description:
        fm += f'description: "{description.replace(chr(34), chr(92)+chr(34))}"\n'
    fm += "---\n"

    return fm + "\n" + body + "\n"


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def _add_sidebar_hidden(md: str) -> str:
    """Insert 'sidebar: {hidden: true}' into existing YAML frontmatter."""
    if not md.startswith("---"):
        return md
    end = md.index("---", 3)
    fm = md[:end].rstrip()
    rest = md[end + 3:]
    return fm + "\nsidebar:\n  hidden: true\n---" + rest


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_latest(module_names: list[str], verbose: bool = True) -> tuple[int, int]:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    ok = failed = 0
    for name in module_names:
        src = MODULES_DIR / name / "README.md"
        if not src.exists():
            failed += 1
            continue
        dst = CONTENT_DIR / f"{name}.md"
        dst.write_text(src.read_text("utf-8"), "utf-8")
        if verbose:
            print(f"  {name}")
        ok += 1
    return ok, failed


def generate_version(
    module_names: list[str], branch: str, verbose: bool = True
) -> tuple[int, int]:
    print(f"  Fetching entities.xml for {branch}...")
    global_ents = _fetch_global_entities(branch)

    ok = failed = 0

    def process(name: str) -> tuple[str, str | None]:
        md = _convert_from_github(name, branch, global_ents)
        if md is None:
            return name, None
        return name, _add_sidebar_hidden(md)

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(process, n): n for n in module_names}
        for fut in as_completed(futures):
            name, md = fut.result()
            if md is None:
                failed += 1
                continue
            out_dir = CONTENT_DIR / name
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{branch}.md").write_text(md, "utf-8")
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
    module_names = sorted(p.name for p in MODULES_DIR.iterdir() if p.is_dir())
    other_versions = [v for v in VERSIONS if not v.get("is_latest")]

    print(f"Generating docs for {len(module_names)} modules...")

    print(f"\n[{LATEST_BRANCH}] latest — from local files")
    ok, failed = generate_latest(module_names, verbose)
    print(f"  → {ok} OK, {failed} skipped")

    branches_to_fetch: list[str] = []
    if args.version:
        branches_to_fetch = [args.version]
    elif args.all_versions:
        branches_to_fetch = [v["branch"] for v in other_versions]

    for branch in branches_to_fetch:
        print(f"\n[{branch}] — from GitHub")
        ok, failed = generate_version(module_names, branch, verbose)
        print(f"  → {ok} OK, {failed} failed")

    print("\nDone.")


if __name__ == "__main__":
    main()
