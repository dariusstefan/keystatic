"""Manual heading-anchor rules — Python mirror of src/utils/remarkManualAnchors.mjs.

The Manual reference pages drop their explicit {#id}; the remark plugin derives
the id at build time. The converter reproduces that derivation here ONLY to map
each heading's legacy id → the id that will be generated, so it can drop the
markers, rewrite same-page links, and emit a sidecar for cross-page links.

Pages WITH a rule use the rule below; every other manual page falls through to
Astro's github-slug (mirrored in `github_slug`). The two implementations must
stay in lock-step — see test_converter.py::TestManualAnchorRule.
"""
import re


def clean(s: str) -> str:
    """Keep chars that occur in OpenSIPS manual identifiers ('.', '-', '_')."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")


def section_slug(s: str) -> str:
    """Lower-case underscore slug for the few group/section headings."""
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# github-slugger, reduced to the ASCII behaviour our headings need: lower-case,
# keep [0-9a-z_-], drop other punctuation, spaces → '-'. (No hyphen collapsing.)
def _gh_base(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^0-9a-z \-_]", "", s)
    return s.replace(" ", "-")


def _event_from_body(body_after: str) -> str | None:
    m = re.search(r"\*\*Event\*\*:\s*([A-Za-z0-9_]+)", body_after or "")
    return m.group(1) if m else None


# page basename (lower-case, no .md) → callable(text, body_after) -> id | None
PAGE_RULES = {
    "script-coreparameters":
        lambda t, b: clean(t.strip()) if re.fullmatch(r"[A-Za-z_][\w.-]*", t.strip()) else (section_slug(t) or None),
    "script-corefunctions":
        lambda t, b: clean(t.split("(")[0]) or None,
    "script-tran":
        lambda t, b: (clean(t.strip().strip("{}").split(",")[0].strip()) or None) if t.strip().startswith("{") else (section_slug(t) or None),
    "script-corevar":
        lambda t, b: (lambda m: clean(m.group(1)) if m else (section_slug(t) or None))(re.search(r"\$\(?\{?([A-Za-z0-9_.]+)", t)),
    "interface-coremi":
        lambda t, b: clean(re.split(r"[\s\[]", t.strip())[0].replace(":", "_")) or None,
    "interface-corestatistics":
        lambda t, b: clean(t) or None,
    "script-routes":
        lambda t, b: clean(t) or None,
    "interface-coreevents":
        lambda t, b: _event_from_body(b) or section_slug(t) or None,
}

RULE_PAGES = frozenset(PAGE_RULES)


class ManualAnchorer:
    """Replays the build-time id assignment for one page so legacy ids can be
    mapped. Headings are fed in document order (the dedup depends on order)."""

    def __init__(self, page: str):
        self.page = page
        self.rule = PAGE_RULES.get(page)
        self._used: set[str] = set()          # rule-page dedup ('_N')
        self._occ: dict[str, int] = {}         # github dedup ('-N')

    def assign(self, heading_text: str, body_after: str = "") -> str | None:
        if self.rule:
            base = self.rule(heading_text, body_after)
            if not base:
                return None
            anchor = base
            if anchor in self._used:
                n = 2
                while f"{base}_{n}" in self._used:
                    n += 1
                anchor = f"{base}_{n}"
            self._used.add(anchor)
            return anchor
        # github-slugger path (non-rule pages)
        base = _gh_base(heading_text)
        if not base:
            return None
        anchor = base
        while anchor in self._occ:
            self._occ[base] += 1
            anchor = f"{base}-{self._occ[base]}"
        self._occ[anchor] = 0
        return anchor


# Convenience for one-shot use in tests.
def github_slug(s: str) -> str:
    return _gh_base(s)
