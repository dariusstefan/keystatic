#!/usr/bin/env python3
"""Resolve legacy PmWiki ``#tocN`` anchors to real heading anchors.

PmWiki auto-numbered every heading sequentially (across all levels) and exposed
them as ``#toc1``, ``#toc2``, … table-of-contents anchors. Those numeric anchors
do not exist in the rendered Starlight pages (which use ``{#id}`` anchors, or a
github-slugger fallback for headings without one), so every ``#tocN`` link is a
dead anchor.

This pass scans the assembled content tree, builds a per-page ordered list of
heading ids, and rewrites each ``[label](/docs/<page>#tocN)`` (or same-page
``#tocN``) to ``…#<id-of-the-Nth-heading>``.

Resolution outcomes:
  * target exists & N within range  → rewrite to the real ``#id``
  * target exists & N out of range   → drop the anchor (link to page top)
  * target empty / missing           → left untouched and reported (the link
                                        points at the wrong page; needs a manual
                                        repoint, not just an anchor)
  * external (http) ``#toc``          → never touched

Idempotent: once a link is resolved it no longer contains ``#tocN``.

Run standalone, or it runs automatically via the ``prebuild`` npm hook and
``deploy.sh`` before every ``astro build``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "src" / "content" / "docs" / "docs"

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_EXPLICIT_ID = re.compile(r"\{#([^}]+)\}\s*$")
# [label](<base>#tocN<trailing>) — base has no whitespace/paren/hash
_TOC_LINK = re.compile(r"(\]\()([^)\s#]*)#toc(\d+)([^)]*)(\))")


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def _github_slug(text: str, occurrences: dict[str, int]) -> str:
    """Replicate github-slugger (the slugger Starlight/rehype-slug use) closely
    enough for our heading text: render markdown emphasis/code/links to plain
    text, lowercase, drop everything but [a-z0-9 _-], spaces → hyphens, and
    de-duplicate with a numeric suffix."""
    s = re.sub(r"`([^`]*)`", r"\1", text)                 # `code` → code
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)         # [t](u) → t
    s = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", s)    # **bold** / _em_ → text
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]", "", s)
    s = s.replace(" ", "-")
    base = s
    n = occurrences.get(base, 0)
    if n:
        while f"{base}-{n}" in occurrences:
            n += 1
        s = f"{base}-{n}"
    occurrences[base] = n + 1
    occurrences.setdefault(s, occurrences.get(s, 0))
    return s


def heading_ids(path: Path) -> list[str]:
    """Ordered list of the rendered anchor ids for a page's headings.

    Explicit ``{#id}`` wins (remark-heading-id); otherwise the github-slugger
    fallback is used. Only fallback-generated ids participate in de-duplication,
    matching rehype-slug (it skips headings that already carry an id)."""
    ids: list[str] = []
    occurrences: dict[str, int] = {}
    for line in _strip_frontmatter(path.read_text(encoding="utf-8", errors="replace")).splitlines():
        m = _HEADING.match(line)
        if not m:
            continue
        text = m.group(2)
        idm = _EXPLICIT_ID.search(text)
        if idm:
            ids.append(idm.group(1))
        else:
            ids.append(_github_slug(text, occurrences))
    return ids


def _route(path: Path) -> str:
    return _route_in(path, DOCS)


def _route_in(path: Path, root: Path) -> str:
    return str(path.relative_to(root).with_suffix("")).replace("\\", "/")


def build_index(root: Path = DOCS) -> dict[str, list[str]]:
    """Map every page route (path under ``root``, no extension) → its ordered
    list of rendered heading ids. Reusable by other tooling (e.g. check_changes)
    to detect or apply #toc resolution."""
    return {
        _route_in(p, root): heading_ids(p)
        for p in root.rglob("*")
        if p.suffix in (".md", ".mdx")
    }


def resolve_text(text: str, page_route: str, index: dict[str, list[str]],
                 stats: dict | None = None) -> str:
    """Return ``text`` with every internal ``#tocN`` anchor resolved against
    ``index`` (the Nth heading's id), out-of-range anchors dropped, and external
    / unresolvable ones left untouched. Optional ``stats`` dict is updated with
    ``resolved`` / ``dropped`` counts and ``empty-stub`` / ``missing`` link lists."""
    def repl(m: re.Match) -> str:
        open_, base, num, trailing, close = m.groups()
        if trailing:  # malformed; leave alone
            return m.group(0)
        n = int(num)
        if base.startswith(("http://", "https://")):
            return m.group(0)  # external — never touch (category D)
        if base.startswith("/docs/"):
            route = base[len("/docs/"):]
        elif base == "":
            route = page_route  # same-page anchor
        else:
            return m.group(0)  # relative/other — skip

        ids = index.get(route)
        if ids is None:
            if stats is not None:
                stats.setdefault("missing", []).append((page_route, f"{base}#toc{n}"))
            return m.group(0)
        if not ids:
            if stats is not None:
                stats.setdefault("empty-stub", []).append((page_route, f"{base}#toc{n}"))
            return m.group(0)
        if n > len(ids):
            if stats is not None:
                stats["dropped"] = stats.get("dropped", 0) + 1
            return f"{open_}{base}{close}"  # out of range → drop anchor
        if stats is not None:
            stats["resolved"] = stats.get("resolved", 0) + 1
        return f"{open_}{base}#{ids[n - 1]}{close}"

    return _TOC_LINK.sub(repl, text)


def main() -> int:
    report_only = "--report-only" in sys.argv

    pages = sorted(p for p in DOCS.rglob("*") if p.suffix in (".md", ".mdx"))
    index = build_index(DOCS)

    stats: dict = {"resolved": 0, "dropped": 0}
    changed_files = 0

    for path in pages:
        text = path.read_text(encoding="utf-8", errors="replace")
        new = resolve_text(text, _route_in(path, DOCS), index, stats)
        if new != text and not report_only:
            path.write_text(new, encoding="utf-8")
            changed_files += 1

    resolved = stats.get("resolved", 0)
    dropped = stats.get("dropped", 0)
    unresolved = {
        "empty-stub": stats.get("empty-stub", []),
        "missing": stats.get("missing", []),
    }

    print("── #toc anchor resolution ─────────────────")
    print(f"  resolved to real anchor: {resolved}")
    print(f"  dropped (out of range):  {dropped}")
    print(f"  files changed:           {changed_files}")
    for kind, items in unresolved.items():
        if items:
            print(f"\n  UNRESOLVED [{kind}]: {len(items)} (target page is {kind}; needs repoint)")
            seen = set()
            for src, link in items:
                if link in seen:
                    continue
                seen.add(link)
                print(f"    {link:55s} (e.g. in {src})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
