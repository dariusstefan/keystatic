"""Resolve cross-page link anchors against the static anchor index.

The index (built once, committed as src/data/{module,manual}-anchors.json) maps,
per page, every legacy ``{#id}`` to the id the remark plugins / github-slugger
will generate. Rewriting a cross-page link's anchor is then a pure lookup — the
same operation regardless of which page it points at, because the map already
holds every page.

This runs in the manual converter, where links are still in their fork-relative
form (the website routes are applied later by generate-manual-docs):

  * same-version manual   ](Foo.md#ref)                       → <cur_slug>/foo
  * other-version manual  ](Foo-3-6.md#ref)                   → via page_ref()
  * module                ](../modules/<mod>/README.md#ref)   → <cur_slug>/<mod>

Same-page ``](#ref)`` links are resolved inline by the converter (they need the
page's own #tocN/legacy map), so they're not handled here.
"""
import json
import re
from pathlib import Path

_MANUAL = re.compile(r"(\]\(([\w.-]+)\.md#)([^)\s]+)(\))")
_MODULE = re.compile(r"(\]\(\.\./modules/([\w.-]+)/README\.md#)([^)\s]+)(\))")
# Route-form links (cross-version / website-origin), slug embedded in the URL.
_ROUTE = re.compile(r"(\]\([^)\s]*?/docs/(modules|manual)/([\w.-]+)/([\w.-]+)#)([^)\s]+)(\))")


def load_index(repo_root: Path) -> dict:
    """Return {"modules": {<slug>/<mod>: {ref: id}}, "manual": {...}}."""
    out: dict[str, dict] = {}
    for section, fn in (("modules", "module-anchors.json"), ("manual", "manual-anchors.json")):
        p = repo_root / "src" / "data" / fn
        try:
            out[section] = json.loads(p.read_text("utf-8")) if p.exists() else {}
        except Exception:
            out[section] = {}
    return out


def resolve_fork(md: str, index: dict, cur_slug: str, page_ref) -> str:
    """Rewrite fork-relative cross-page link anchors via ``index``.

    ``cur_slug`` is this conversion's version slug; ``page_ref(name)`` maps a
    version-suffixed manual page stem (e.g. 'Script-CoreVar-3-6') → (page, slug)
    or None (then it's treated as a same-version page)."""
    manual = index.get("manual", {})
    modules = index.get("modules", {})
    _TOC = re.compile(r"toc\d+$")

    def _apply(pmap, ref, open_, close) -> str | None:
        """None → leave link as-is; else the replacement (open_ + new_ref + close,
        with the anchor DROPPED for an out-of-range #tocN on a known page)."""
        if pmap is None:
            return None
        new = pmap.get(ref)
        if new and new != ref:
            return f"{open_}{new}{close}"
        if new is None and _TOC.match(ref):     # #tocN out of range → page top
            return f"{open_[:-1]}{close}"        # strip the trailing '#'
        return None

    def manual_link(m: re.Match) -> str:
        stem, ref = m.group(2), m.group(3)
        pr = page_ref(stem)
        key = f"{pr[1]}/{pr[0]}" if pr else f"{cur_slug}/{stem.lower()}"
        return _apply(manual.get(key), ref, m.group(1), m.group(4)) or m.group(0)

    def module_link(m: re.Match) -> str:
        mod, ref = m.group(2), m.group(3)
        return _apply(modules.get(f"{cur_slug}/{mod}"), ref, m.group(1), m.group(4)) or m.group(0)

    def route_link(m: re.Match) -> str:
        sec, slug, page, ref = m.group(2), m.group(3), m.group(4), m.group(5)
        return _apply(index.get(sec, {}).get(f"{slug}/{page}"), ref, m.group(1), m.group(6)) or m.group(0)

    md = _ROUTE.sub(route_link, md)
    md = _MANUAL.sub(manual_link, md)
    md = _MODULE.sub(module_link, md)
    return md
