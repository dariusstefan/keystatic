#!/usr/bin/env python3
"""Generate the per-version "DB schema" manual page from db/schema/*.xml.

The OpenSIPS DB schema is described in XML (opensips/db/schema/opensips-*.xml,
each xi:include-ing per-table *.xml). The opensips build turns these into SQL
scripts and — via doc/dbschema/xsl/docbook.xsl → dbschema2docbook.xsl — into the
HTML shown at opensips.org/Documentation/Install-DBSchema-<ver>. The PmWiki →
Markdown manual converter can't capture that page (it was rendered dynamically),
so install-dbschema.md lands as an empty stub.

This script fills that stub directly in the website content tree, per version,
reproducing the dbschema2docbook.xsl rendering as GitHub-flavoured Markdown:

  ## <database/module name>
  ### Table "<name>"
  <description>
  | name | type | size | default | null | key | extra attributes | description |
  | name | type | links | description |   (per-table index table, if any)

Sources every version from the local opensips git (no checkout needed):
master → devel, and origin/<branch> for the release branches — matching the
slug map in generate-manual-docs.py. The generated page is written into
src/content/docs/docs/manual/<slug>/install-dbschema.md and is never committed
to a repo; it is regenerated from the schema on each website build.

Reuses docbook_to_md.py for entity resolution, DOCTYPE stripping, and inline
DocBook → Markdown (the <description> bodies use <db:para>, <ulink>, etc.).

Usage:
    python3 scripts/generate-dbschema.py                 # devel only
    python3 scripts/generate-dbschema.py --all-versions  # every version
    python3 scripts/generate-dbschema.py --version 4.0   # one extra version
"""

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPENSIPS_DIR = REPO_ROOT / "opensips"
SCHEMA_PATH = "db/schema"
CONTENT_DIR = REPO_ROOT / "src" / "content" / "docs" / "docs" / "manual"

# Reuse the DocBook converter's entity + inline-markup machinery.
sys.path.insert(0, str(REPO_ROOT / "converters"))
from docbook_to_md import (  # noqa: E402
    XML_ENTITIES,
    _extract_text_entities,
    _inline,
    _resolve_values,
    _strip_doctype,
    _subst,
)

# branch ↔ website slug, same set/order as generate-manual-docs.py
VERSIONS = [
    {"ref": "master",     "slug": "devel", "is_latest": True},
    {"ref": "origin/4.0", "slug": "4-0"},
    {"ref": "origin/3.6", "slug": "3-6"},
    {"ref": "origin/3.5", "slug": "3-5"},
    {"ref": "origin/3.4", "slug": "3-4"},
    {"ref": "origin/3.3", "slug": "3-3"},
    {"ref": "origin/3.2", "slug": "3-2"},
    {"ref": "origin/3.1", "slug": "3-1"},
    {"ref": "origin/3.0", "slug": "3-0"},
    {"ref": "origin/2.4", "slug": "2-4"},
    {"ref": "origin/2.3", "slug": "2-3"},
    {"ref": "origin/2.2", "slug": "2-2"},
    {"ref": "origin/2.1", "slug": "2-1"},
    {"ref": "origin/1.11", "slug": "1-11"},
    {"ref": "origin/1.10", "slug": "1-10"},
    {"ref": "origin/1.9", "slug": "1-9"},
    {"ref": "origin/1.8", "slug": "1-8"},
    {"ref": "origin/1.7", "slug": "1-7"},
    {"ref": "origin/1.6", "slug": "1-6"},
    {"ref": "origin/1.5", "slug": "1-5"},
    {"ref": "origin/1.4", "slug": "1-4"},
]
LATEST = next(v for v in VERSIONS if v.get("is_latest"))

# Page-scoped styling (injected via Starlight's `head`, so it only affects this
# page): the schema tables are wide with one long `description` column. Keep the
# short columns on one line, give the description room, and let the whole table
# scroll horizontally — so rows stay short instead of wrapping into many lines.
FRONTMATTER = """\
---
title: "DB schema"
description: ""
head:
  - tag: style
    content: |
      .sl-markdown-content table { display: block; overflow-x: auto; font-size: 0.8125rem; }
      .sl-markdown-content table :is(td, th) { padding: 0.25rem 0.6rem; line-height: 1.35; vertical-align: top; white-space: nowrap; }
      .sl-markdown-content table :is(td, th):nth-child(6) { white-space: normal; min-width: 26rem; }
---
"""

# Legacy module-doc URLs baked into the schema descriptions (entity
# OPENSIPS_MOD_DOC, always …/modules/devel/<mod>.html) → internal module pages
# on this site, versioned to match the page being generated.
_MOD_LINK_RE = re.compile(r"https?://opensips\.org/docs/modules/[\w.+-]+/([\w-]+)\.html")


def _rewrite_module_links(text: str, slug: str) -> str:
    return _MOD_LINK_RE.sub(
        lambda m: f"[{m.group(1)}](/docs/modules/{slug}/{m.group(1)})", text
    )


# ---------------------------------------------------------------------------
# Reading schema files out of the local opensips git (per branch, no checkout)
# ---------------------------------------------------------------------------

def _git_show(ref: str, rel: str) -> str | None:
    """Return the contents of <ref>:db/schema/<rel>, or None if it doesn't exist."""
    r = subprocess.run(
        ["git", "show", f"{ref}:{SCHEMA_PATH}/{rel}"],
        cwd=OPENSIPS_DIR, capture_output=True, text=True,
    )
    return r.stdout if r.returncode == 0 else None


def _list_modules(ref: str) -> list[str]:
    """Sorted opensips-*.xml module filenames present on `ref`."""
    r = subprocess.run(
        ["git", "ls-tree", "--name-only", ref, f"{SCHEMA_PATH}/"],
        cwd=OPENSIPS_DIR, capture_output=True, text=True,
    )
    if r.returncode != 0:
        return []
    names = [
        line.rsplit("/", 1)[-1]
        for line in r.stdout.splitlines()
        if re.search(r"/opensips-[\w.-]+\.xml$", line)
    ]
    return sorted(names)


def _load_entities(ref: str) -> dict:
    """Resolved entity map from db/schema/entities.xml on `ref`."""
    raw = _git_show(ref, "entities.xml") or ""
    ents = _extract_text_entities(raw)
    _resolve_values(ents)
    return ents


# ---------------------------------------------------------------------------
# XML → element tree (entities substituted, namespaces flattened)
# ---------------------------------------------------------------------------

def _parse_table(raw: str, entities: dict) -> ET.Element | None:
    """Parse one table/*.xml fragment into an element tree.

    Strips the XML declaration + DOCTYPE, substitutes the schema entities
    (&user_len; → 64, &OPENSIPS_MOD_DOC; → https://…, …), and drops namespace
    prefixes/declarations so <db:para> becomes a plain <para> the inline
    renderer understands."""
    text = re.sub(r"<\?xml[^?]*\?>", "", raw)
    text = _strip_doctype(text)

    for _ in range(10):
        new = _subst(text, entities, skip=XML_ENTITIES)
        if new == text:
            break
        text = new

    # Any leftover non-XML entity refs: escape the & so the parser tolerates them.
    text = re.sub(
        r"&([\w.-]+);",
        lambda m: m.group(0) if m.group(1) in XML_ENTITIES else f"&amp;{m.group(1)};",
        text,
    )

    # Flatten namespaces: drop xmlns:* declarations and tag/attr prefixes (db:, xi:).
    text = re.sub(r'\s+xmlns(:\w+)?="[^"]*"', "", text)
    text = re.sub(r"(</?)\w+:", r"\1", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        print(f"  [WARN] parse error: {exc}")
        return None


def _module_meta(raw: str) -> tuple[str, list[str]]:
    """(database name, ordered list of included table filenames) from a module file."""
    name_m = re.search(r"<name>(.*?)</name>", raw, re.DOTALL)
    name = name_m.group(1).strip() if name_m else ""
    hrefs = re.findall(r'<xi:include\s+href="([^"]+)"', raw)
    return name, hrefs


# ---------------------------------------------------------------------------
# Rendering a table (mirrors dbschema2docbook.xsl)
# ---------------------------------------------------------------------------

def _text(elem: ET.Element | None) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def _desc(parent: ET.Element, oneline: bool = True) -> str:
    """Render a <description> body to inline Markdown (collapsed whitespace)."""
    d = parent.find("description")
    if d is None:
        return ""
    out = re.sub(r"\s+", " ", _inline(d)).strip()
    return out.replace("|", "\\|") if oneline else out


def _fmt_default(col: ET.Element) -> str:
    d = col.find("default")
    if d is None:
        return "default"
    if d.find("null") is not None:
        return "NULL"
    val = _text(d)
    try:
        float(val)            # plain number → no quotes
        return val
    except ValueError:
        return f"'{val}'"     # string (incl. empty → '') → quoted


def _columns_table(table: ET.Element) -> list[str]:
    # NOTE: description is column 6 — kept in sync with the nth-child(6) rule in
    # the page-scoped CSS (FRONTMATTER) that widens/wraps the description column.
    lines = [
        "| name | type | size | default | null | description | key | extra attributes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for col in table.findall("column"):
        name = _text(col.find("name"))
        ctype = _text(col.find("type"))
        size = _text(col.find("size")) or "not specified"
        default = _fmt_default(col)
        null = "yes" if col.find("null") is not None else "no"
        key = "primary" if col.find("primary") is not None else ""
        extra = "autoincrement" if col.find("autoincrement") is not None else ""
        desc = _desc(col)
        cells = [f"`{name}`", f"`{ctype}`", size, default, null, desc, key, extra]
        lines.append("| " + " | ".join(c.strip() for c in cells) + " |")
    return lines


def _index_table(table: ET.Element) -> list[str]:
    indexes = table.findall("index")
    if not indexes:
        return []
    # column @id → name, to resolve <colref linkend="…"/>
    id_to_name = {
        col.get("id"): _text(col.find("name"))
        for col in table.findall("column")
        if col.get("id")
    }
    lines = [
        "",
        '**Indexes**',
        "",
        "| name | type | links | description |",
        "| --- | --- | --- | --- |",
    ]
    for idx in indexes:
        name = _text(idx.find("name"))
        if idx.find("unique") is not None:
            itype = "unique"
        elif idx.find("primary") is not None:
            itype = "primary"
        else:
            itype = "default"
        links = ", ".join(
            id_to_name.get(c.get("linkend"), c.get("linkend") or "")
            for c in idx.findall("colref")
        )
        desc = _desc(idx)
        lines.append(f"| `{name}` | {itype} | {links} | {desc} |")
    return lines


def _render_table(table: ET.Element) -> list[str]:
    name = _text(table.find("name"))
    out = [f'### Table "{name}"', ""]
    desc = _desc(table, oneline=False)
    if desc:
        out += [desc, ""]
    out += _columns_table(table)
    out += _index_table(table)
    out.append("")
    return out


# ---------------------------------------------------------------------------
# Per-version page assembly
# ---------------------------------------------------------------------------

def build_page(ref: str, slug: str, verbose: bool) -> str | None:
    modules = _list_modules(ref)
    if not modules:
        return None
    entities = _load_entities(ref)

    body: list[str] = [FRONTMATTER]
    n_tables = 0
    for mod_file in modules:
        raw = _git_show(ref, mod_file)
        if raw is None:
            continue
        db_name, hrefs = _module_meta(raw)
        if not hrefs:
            continue
        body += [f"## {db_name}", ""]
        for href in hrefs:
            table_raw = _git_show(ref, href)
            if table_raw is None:
                print(f"  [WARN] {ref}: missing {href} (from {mod_file})")
                continue
            table = _parse_table(table_raw, entities)
            if table is None or table.tag != "table":
                continue
            body += _render_table(table)
            n_tables += 1
        if verbose:
            print(f"  {mod_file}: {db_name} ({len(hrefs)} tables)")

    if verbose:
        print(f"  → {len(modules)} modules, {n_tables} tables")
    return _rewrite_module_links("\n".join(body).rstrip() + "\n", slug)


def generate(versions: list[dict], verbose: bool) -> int:
    written = 0
    for v in versions:
        print(f"\n[{v['slug']}] — from {v['ref']} (db/schema)")
        page = build_page(v["ref"], v["slug"], verbose)
        if page is None:
            print("  [WARN] no schema found; skipped")
            continue
        out_dir = CONTENT_DIR / v["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "install-dbschema.md").write_text(page, "utf-8")
        written += 1
    return written


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-versions", action="store_true")
    ap.add_argument("--version", metavar="REF_OR_SLUG")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    verbose = not args.quiet

    older = [v for v in VERSIONS if not v.get("is_latest")]
    if args.version:
        match = next(
            (v for v in older
             if args.version in (v["slug"], v["ref"], v["ref"].removeprefix("origin/"))),
            None,
        )
        if not match:
            print(f"[WARN] Unknown version: {args.version!r}")
        versions = [LATEST] + ([match] if match else [])
    elif args.all_versions:
        versions = VERSIONS
    else:
        versions = [LATEST]

    n = generate(versions, verbose)
    print(f"\nDone. {n} install-dbschema.md page(s) written.")


if __name__ == "__main__":
    main()
