#!/usr/bin/env python3
"""Convert OpenSIPS module DocBook XML docs to README.md files.

Reads opensips/modules/<name>/doc/*.xml and writes a single README.md per
module with Starlight-compatible YAML frontmatter.

Usage:
    python3 pmwiki-mdx/docbook_to_md.py            # convert all 193 modules
    python3 pmwiki-mdx/docbook_to_md.py acc dialog  # convert specific modules
"""

import re
import shutil
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "opensips" / "modules"
ENTITIES_FILE = REPO_ROOT / "opensips" / "doc" / "entities.xml"

# Standard XML character entities — handled by the parser; never substituted
# by our pre-processor so they aren't lost before ET.fromstring() runs.
XML_ENTITIES = {"lt", "gt", "amp", "quot", "apos"}

# Legacy OpenSIPS website module-doc URLs. Both the current and the older
# /html/docs/ path, with or without the .html suffix:
#   opensips.org/docs/modules/<ver>.x/<mod>.html[#anchor]
#   www.opensips.org/html/docs/modules/<ver>.x/<mod>[#anchor]
_MOD_DOC_RE = re.compile(
    r"https?://(?:www\.)?opensips\.org/(?:html/)?docs/modules/[^/]+/([\w.\-]+?)(?:\.html)?(#\S*)?$",
    re.IGNORECASE,
)


def _module_doc_rel(url: str):
    """A legacy website module-doc URL → a relative sibling link (../<mod>), or
    None if it isn't one. Drops the pinned <ver>.x so the link follows the
    current page's version; keeps any #anchor. Works on github.com (sibling
    module README) and on the website (/docs/modules/<ver>/<mod>)."""
    m = _MOD_DOC_RE.match(url or "")
    if not m:
        return None
    return f"../{m.group(1)}{m.group(2) or ''}"


# ---------------------------------------------------------------------------
# Manual-page links (old version-suffix URLs → /docs/manual/<ver>/<page>)
# ---------------------------------------------------------------------------

SITE_URL = "https://web.opensips.org"
_LATEST_MANUAL_VER = "4-1"
_MANUAL_PAGES: set[str] = set()

_DOC_URL_RE = re.compile(
    r"https?://(?:www\.)?opensips\.org/(?:html/)?Documentation/([^#?\s]+)(#\S*)?$",
    re.IGNORECASE,
)


def _load_manual_pages() -> None:
    man_root = REPO_ROOT / "src" / "content" / "docs" / "docs" / "manual"
    if not man_root.exists():
        return
    for p in man_root.rglob("*.md"):
        s = p.stem.lower()
        if s != "index":
            _MANUAL_PAGES.add(s)


_load_manual_pages()

# ---------------------------------------------------------------------------
# Flat-doc links (opensips.org/Documentation/Tutorials-Foo → /docs/tutorials-foo)
# ---------------------------------------------------------------------------

_FLAT_DOC_PAGES: set[str] = set()


def _load_flat_doc_pages() -> None:
    flat_root = REPO_ROOT / "src" / "content" / "docs" / "docs"
    if not flat_root.exists():
        return
    for p in flat_root.glob("*.md"):
        _FLAT_DOC_PAGES.add(p.stem.lower())


_load_flat_doc_pages()


def _flat_doc_web(url: str):
    """A legacy website Documentation URL (opensips.org/Documentation/Tutorials-Foo)
    → an absolute website URL https://web.opensips.org/docs/tutorials-foo, or None.
    Absolute so it works on github.com; generate-module-docs.py strips the origin
    for the on-site build (same pattern as _manual_doc_web)."""
    m = _DOC_URL_RE.match(url or "")
    if not m:
        return None
    slug = m.group(1).rstrip("/").lower()
    if slug not in _FLAT_DOC_PAGES:
        return None
    return f"{SITE_URL}/docs/{slug}{m.group(2) or ''}"


def _manual_page_ref(seg: str):
    """'Script-CoreVar-3-6' → (page, slug) when de-versioned name is a known
    manual page, else None. 4-1 → devel."""
    m = re.match(r"^(.*?)-(\d+)-(\d+)$", seg)
    if not m:
        return None
    page = m.group(1).lower()
    if page not in _MANUAL_PAGES:
        return None
    ver = f"{m.group(2)}-{m.group(3)}"
    return page, ("devel" if ver == _LATEST_MANUAL_VER else ver)


def _manual_doc_web(url: str):
    """A legacy website manual URL (opensips.org/Documentation/Script-CoreVar-3-6)
    → an absolute website URL /docs/manual/<slug>/<page>, or None. Absolute so it
    works on github.com; generate-module-docs strips the origin for the site."""
    m = _DOC_URL_RE.match(url or "")
    if not m:
        return None
    mp = _manual_page_ref(m.group(1).split("/")[-1])
    if not mp:
        return None
    page, slug = mp
    return f"{SITE_URL}/docs/manual/{slug}/{page}{m.group(2) or ''}"


# ---------------------------------------------------------------------------
# Entity resolution
# ---------------------------------------------------------------------------

def _extract_text_entities(text: str) -> dict:
    """Return {name: value} for all <!ENTITY name "…"> declarations."""
    ents = {}
    for m in re.finditer(r'<!ENTITY\s+([\w.-]+)\s+"([^"]*)"', text):
        ents[m.group(1)] = m.group(2)
    for m in re.finditer(r"<!ENTITY\s+([\w.-]+)\s+'([^']*)'", text):
        ents[m.group(1)] = m.group(2)
    return ents


def _extract_system_entities(text: str) -> dict:
    """Return {name: filepath_str} for all <!ENTITY name SYSTEM "…"> decls."""
    ents = {}
    for m in re.finditer(r'<!ENTITY\s+([\w.-]+)\s+SYSTEM\s+"([^"]*)"', text):
        ents[m.group(1)] = m.group(2)
    return ents


def _subst(text: str, entities: dict, skip: set | None = None) -> str:
    """Replace &name; references with entity values, leaving `skip` names alone."""
    skip = skip or set()

    def replacer(m):
        name = m.group(1)
        if name in skip or name not in entities:
            return m.group(0)
        return entities[name]

    return re.sub(r"&([\w.-]+);", replacer, text)


def _resolve_values(entities: dict) -> None:
    """Iteratively resolve entity cross-references within entity values."""
    for _ in range(10):
        changed = False
        for name, value in list(entities.items()):
            new_val = _subst(value, entities, skip={name} | XML_ENTITIES)
            if new_val != value:
                entities[name] = new_val
                changed = True
        if not changed:
            break


def load_global_entities() -> dict:
    raw = ENTITIES_FILE.read_text("utf-8")
    ents = _extract_text_entities(raw)
    # Common HTML entities absent from entities.xml but used in some modules
    ents.setdefault("nbsp", " ")
    _resolve_values(ents)
    return ents


# ---------------------------------------------------------------------------
# Assemble one parseable XML string per module
# ---------------------------------------------------------------------------

def _strip_doctype(text: str) -> str:
    """Remove the <!DOCTYPE …> declaration (including its internal subset)."""
    i = text.find("<!DOCTYPE")
    if i < 0:
        return text
    j, depth = i, 0
    while j < len(text):
        c = text[j]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        elif c == ">" and depth == 0:
            return text[:i] + text[j + 1 :]
        j += 1
    return text[:i]


def build_combined_xml(module_dir: Path, global_entities: dict) -> str | None:
    """Inline all XML fragments and return one well-formed XML string."""
    doc_dir = module_dir / "doc"
    if not doc_dir.exists():
        return None

    name = module_dir.name
    main_xml = doc_dir / f"{name}.xml"
    if not main_xml.exists():
        candidates = sorted(
            f for f in doc_dir.glob("*.xml")
            if not re.search(r"(_admin|_faq|_devel|contributors)", f.name)
        )
        if not candidates:
            return None
        main_xml = candidates[0]

    text = main_xml.read_text("utf-8", errors="replace")

    # Collect entity definitions: global → module text → SYSTEM files
    entities: dict = dict(global_entities)

    # Module-local text entities declared in the DOCTYPE
    local_text = _extract_text_entities(text)
    entities.update(local_text)
    _resolve_values(entities)

    # SYSTEM (file-inclusion) entities
    for ent_name, rel_path in _extract_system_entities(text).items():
        filepath = (doc_dir / rel_path).resolve()
        # Config-script samples (.cfg) are not inlined as a frozen code block.
        # Emit a <cfgsample> marker instead; the renderer extracts these into a
        # samples/ folder and references them via an include link (resolves to a
        # link on github.com, expands to the file's contents on the website).
        if rel_path.lower().endswith(".cfg"):
            entities[ent_name] = (
                f'<cfgsample src="{Path(rel_path).name}"/>' if filepath.exists() else ""
            )
            continue
        if filepath.exists():
            content = filepath.read_text("utf-8", errors="replace")
            # Strip leading XML comments that head every fragment file
            content = re.sub(r"^\s*<!--.*?-->\s*", "", content, flags=re.DOTALL)
            entities[ent_name] = content
        else:
            entities[ent_name] = ""

    # Strip XML declaration and DOCTYPE; they reference a network DTD we skip
    text = re.sub(r"<\?xml[^?]*\?>", "", text)
    text = _strip_doctype(text)

    # Iteratively substitute all custom entities
    for _ in range(10):
        new_text = _subst(text, entities, skip=XML_ENTITIES)
        if new_text == text:
            break
        text = new_text

    # Any entity references still unresolved are not standard XML — escape
    # the ampersand so the parser sees them as literal text (e.g. &and; → &amp;and;).
    def _escape_undefined(m):
        name = m.group(1)
        return m.group(0) if name in XML_ENTITIES else f"&amp;{name};"

    text = re.sub(r"&([\w.-]+);", _escape_undefined, text)

    # Strip XML comments (handles malformed nested-comment cases too)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    return f"<root>{text.strip()}</root>"


# ---------------------------------------------------------------------------
# Inline Markdown renderer  (handles text + child elements → one string)
# ---------------------------------------------------------------------------

def _inline(elem) -> str:
    """Return all text/markup inside `elem` as inline Markdown."""
    parts: list[str] = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        parts.append(_inline_child(child))
    return "".join(parts)


def _inline_child(elem) -> str:
    """Convert a single inline element (plus its tail) to Markdown."""
    tag = (elem.tag or "").lower()
    inner = _inline(elem)
    tail = elem.tail or ""

    if tag == "emphasis":
        role = (elem.get("role") or "").lower()
        result = f"**{inner.strip()}**" if "bold" in role else f"*{inner.strip()}*"
    elif tag in (
        "varname", "function", "literal", "command", "code",
        "option", "constant", "type", "classname", "envar",
        "parameter", "computeroutput", "filename", "userinput",
    ):
        result = f"`{inner}`"
    elif tag == "quote":
        result = f'"{inner}"'
    elif tag == "ulink":
        url = elem.get("url", "")
        txt = inner.strip() or url
        man = _manual_doc_web(url)
        flat = _flat_doc_web(url)
        rel = _module_doc_rel(url)
        if man is not None:
            url = man   # legacy version-suffix manual link → /docs/manual/<ver>/<page>
        elif flat is not None:
            url = flat  # legacy Documentation/Tutorials-* link → /docs/tutorials-*
        elif rel is not None:
            url = rel   # legacy website module-doc link → relative sibling module
        elif url and "://" not in url and "/" not in url and not url.startswith("#"):
            url = f"../{url}"  # step up from …/module/index.html to reach sibling
        result = f"[{txt}]({url})"
    elif tag == "xref":
        linkend = elem.get("linkend", "")
        txt = _linkend_label(linkend)
        result = f"[{txt}](#{linkend})"
    elif tag == "link":
        linkend = elem.get("linkend", "")
        url = elem.get("url", f"#{linkend}" if linkend else "")
        txt = inner.strip() or _linkend_label(linkend)
        result = f"[{txt}]({url})"
    elif tag == "superscript":
        result = f"<sup>{inner}</sup>"
    elif tag == "subscript":
        result = f"<sub>{inner}</sub>"
    elif tag in ("para", "simpara"):
        result = inner.strip()
    elif tag in ("programlisting", "screen"):
        result = f"\n```c\n{(elem.text or '').rstrip()}\n```\n"
    else:
        result = inner

    return result + tail


def _linkend_label(linkend: str) -> str:
    for prefix in ("func_", "param_", "event_", "pv_"):
        if linkend.startswith(prefix):
            return linkend[len(prefix):].replace("_", " ")
    return linkend.replace("_", " ").replace("-", " ")


# ---------------------------------------------------------------------------
# Block Markdown emitter
# ---------------------------------------------------------------------------

class _Emitter:
    def __init__(self):
        self._lines: list[str] = []
        # .cfg samples encountered, in document order: {"file", "title"}.
        self.samples: list[dict] = []
        self._samples_included = False

    # -- public API ----------------------------------------------------------

    def emit(self, root) -> str:
        for child in root:
            self._block(child, depth=1)
        return self._flush()

    # -- output helpers ------------------------------------------------------

    def _add(self, line: str) -> None:
        self._lines.append(line)

    def _flush(self) -> str:
        """Collapse consecutive blank lines to at most one."""
        out: list[str] = []
        prev_blank = False
        for line in self._lines:
            blank = not line.strip()
            if blank and prev_blank:
                continue
            out.append(line)
            prev_blank = blank
        return "\n".join(out).strip()

    # -- block dispatcher ----------------------------------------------------

    def _block(self, elem, depth: int) -> None:
        tag = (elem.tag or "").lower()

        if tag in ("toc", "index", "bookinfo", "title"):
            return
        elif tag == "anchor":
            anchor_id = elem.get("id", "")
            if anchor_id:
                self._add(f'<span id="{anchor_id}" class="legacy-anchor"></span>')
        elif tag == "book":
            for child in elem:
                self._block(child, depth)
        elif tag in ("chapter", "section", "refsect1", "refsect2", "refsect3"):
            if (elem.get('id') or '').lower() in ('contributors', 'documentation'):
                return
            self._section(elem, depth)
        elif tag in ("para", "simpara"):
            self._para(elem, depth)
        elif tag in ("programlisting", "screen", "literallayout"):
            self._code(elem)
        elif tag == "itemizedlist":
            self._ulist(elem, depth)
        elif tag == "orderedlist":
            self._olist(elem, depth)
        elif tag == "simplelist":
            self._simplelist(elem)
        elif tag == "variablelist":
            self._variablelist(elem, depth)
        elif tag in ("note", "tip", "caution", "important", "warning"):
            self._admonition(elem, tag.capitalize(), depth)
        elif tag == "example":
            self._example(elem, depth)
        elif tag == "qandaset":
            self._qandaset(elem, depth)
        elif tag in ("table", "informaltable"):
            self._table(elem)
        elif tag == "bridgehead":
            level = min(depth + 1, 6)
            txt = _inline(elem).strip()
            if txt:
                self._add(f'\n{"#" * level} {txt}\n')
        else:
            # Generic fallthrough: visit children
            for child in elem:
                self._block(child, depth)

    # -- block handlers ------------------------------------------------------

    def _section(self, elem, depth: int) -> None:
        section_id = elem.get("id", "")
        title_txt = self._get_title(elem)
        if title_txt:
            level = min(depth + 1, 6)
            id_suffix = f" {{#{section_id}}}" if section_id else ""
            # Normalize whitespace on the assembled line so the heading is always
            # single-line and single-spaced, regardless of nested-element quirks in
            # the DocBook <title> (e.g. a <function> child re-introducing spaces).
            heading = re.sub(r"\s+", " ", f'{"#" * level} {title_txt}{id_suffix}').strip()
            self._add(f'\n{heading}\n')
        for child in elem:
            if (child.tag or "").lower() != "title":
                self._block(child, depth + 1)

    def _get_title(self, elem) -> str:
        for child in elem:
            if (child.tag or "").lower() == "title":
                # Collapse ALL internal whitespace (newlines/tabs/runs of spaces)
                # to single spaces so the title stays on ONE line. DocBook titles
                # that document a pair of functions, or a signature that wraps,
                # span multiple lines; left as-is they produced a multi-line
                # Markdown heading whose trailing {#anchor} fell onto a
                # non-heading continuation line.
                return " ".join(_inline(child).split()).replace('`', '')
        return ""

    # Tags that, when found inside a <para>, must be emitted as blocks rather
    # than rendered inline (DocBook allows this "mixed content" pattern).
    _PARA_BLOCK_TAGS = frozenset({
        "itemizedlist", "orderedlist", "simplelist", "variablelist",
        "programlisting", "screen", "literallayout", "table", "informaltable",
        "example", "note", "warning", "important", "tip", "caution",
    })

    def _para(self, elem, depth: int = 2) -> None:
        has_block = any(
            (c.tag or "").lower() in self._PARA_BLOCK_TAGS for c in elem
        )
        if not has_block:
            text = _inline(elem).strip()
            if text:
                if "Documentation Copyrights" in text or text.startswith("©") or text.startswith("Copyright"):
                    return
                self._add(f"\n{text}\n")
            return

        # Mixed content: split on block-level children.
        # Accumulate inline fragments into `pending`; flush as a paragraph
        # before each block child, then continue after it.
        pending: list[str] = []

        def flush_pending() -> None:
            text = "".join(pending).strip()
            if text:
                self._add(f"\n{text}\n")
            pending.clear()

        if elem.text:
            pending.append(elem.text)

        for child in elem:
            ctag = (child.tag or "").lower()
            if ctag in self._PARA_BLOCK_TAGS:
                flush_pending()
                self._block(child, depth)
                if child.tail and child.tail.strip():
                    pending.append(child.tail)
            else:
                # Temporarily suppress the tail so _inline_child doesn't
                # double-emit it; we capture the tail as the next text run.
                saved, child.tail = child.tail, None
                pending.append(_inline_child(child))
                child.tail = saved
                if saved:
                    pending.append(saved)

        flush_pending()

    def _register_sample(self, filename: str, title: str) -> None:
        """Record a .cfg sample and emit a one-time include of samples.md.

        The README links to samples.md once (at the first sample); samples.md
        in turn includes each .cfg with its own heading. On github.com the link
        navigates to the file; the website expands it inline at build time.
        """
        if not filename:
            return
        title = " ".join(title.split())
        self.samples.append({"file": filename, "title": title})
        if not self._samples_included:
            self._add(f'\n[{title or "samples"}](./samples.md "include")\n')
            self._samples_included = True

    def _code(self, elem, title: str = "") -> None:
        sample = elem.find(".//cfgsample")
        if sample is not None:
            self._register_sample(sample.get("src", ""), title)
            return
        code = (elem.text or "").strip("\n")
        lang = "c"
        if title:
            safe = " ".join(title.split()).replace('"', "'")
            title_attr = f' title="{safe}"'
        else:
            title_attr = ""
        self._add(f"\n```{lang}{title_attr}\n{code}\n```\n")

    def _ulist(self, elem, depth: int) -> None:
        items = [
            f"- {self._listitem_text(c, depth)}"
            for c in elem
            if (c.tag or "").lower() == "listitem"
        ]
        if items:
            self._add("\n" + "\n".join(items) + "\n")

    def _olist(self, elem, depth: int) -> None:
        items = []
        n = 1
        for c in elem:
            if (c.tag or "").lower() == "listitem":
                items.append(f"{n}. {self._listitem_text(c, depth)}")
                n += 1
        if items:
            self._add("\n" + "\n".join(items) + "\n")

    def _listitem_text(self, elem, depth: int) -> str:
        parts: list[str] = []
        if elem.text and elem.text.strip():
            parts.append(elem.text.strip())
        for child in elem:
            ctag = (child.tag or "").lower()
            if ctag in ("para", "simpara"):
                txt = _inline(child).strip()
                if txt:
                    parts.append(txt)
            elif ctag in ("itemizedlist", "orderedlist"):
                sub = [
                    f"  - {self._listitem_text(s, depth + 1)}"
                    for s in child
                    if (s.tag or "").lower() == "listitem"
                ]
                if sub:
                    parts.append("\n" + "\n".join(sub))
            elif ctag in ("programlisting", "screen"):
                code = (child.text or "").strip("\n")
                indented = "\n".join("  " + l for l in code.splitlines())
                parts.append(f"\n  ```\n{indented}\n  ```")
            elif ctag in ("note", "tip", "warning", "important"):
                inner = " ".join(
                    _inline(p).strip()
                    for p in child
                    if (p.tag or "").lower() in ("para", "simpara")
                )
                parts.append(f"\n  > **{ctag.capitalize()}:** {inner}")
            else:
                txt = _inline(child).strip()
                if txt:
                    parts.append(txt)
        return "\n".join(p for p in parts if p)

    def _simplelist(self, elem) -> None:
        members = [_inline(c).strip() for c in elem if (c.tag or "").lower() == "member"]
        if not members:
            return
        if elem.get("type", "vert") == "inline":
            self._add(f"\n{', '.join(members)}\n")
        else:
            self._add("\n" + "\n".join(f"- {m}" for m in members) + "\n")

    def _variablelist(self, elem, depth: int) -> None:
        for entry in elem:
            if (entry.tag or "").lower() != "varlistentry":
                continue
            terms, listitem = [], None
            for child in entry:
                ctag = (child.tag or "").lower()
                if ctag == "term":
                    terms.append(_inline(child).strip())
                elif ctag == "listitem":
                    listitem = child
            if terms:
                self._add(f'\n**{", ".join(terms)}**\n')
            if listitem is not None:
                for child in listitem:
                    self._block(child, depth + 1)

    # DocBook admonition → GitHub alert type (renders as a native alert on
    # github.com and, via remarkGithubAlerts, a Starlight aside on the website).
    _GH_ALERT = {"note": "NOTE", "tip": "TIP", "important": "IMPORTANT",
                 "warning": "WARNING", "caution": "CAUTION"}

    def _admonition(self, elem, label: str, depth: int) -> None:
        parts = [
            _inline(c).strip()
            for c in elem
            if (c.tag or "").lower() in ("para", "simpara")
        ]
        text = " ".join(p for p in parts if p)
        if text:
            gh = self._GH_ALERT.get(label.lower(), "NOTE")
            self._add(f"\n> [!{gh}]\n> {text}\n")

    def _example(self, elem, depth: int) -> None:
        title_txt = self._get_title(elem)
        for child in elem:
            ctag = (child.tag or "").lower()
            if ctag == "title":
                continue
            if ctag in ("programlisting", "screen", "literallayout"):
                self._code(child, title=title_txt or "")
            else:
                self._block(child, depth)

    def _qandaset(self, elem, depth: int) -> None:
        for entry in elem:
            if (entry.tag or "").lower() != "qandaentry":
                continue
            q_text = a_parts = ""
            for sub in entry:
                stag = (sub.tag or "").lower()
                if stag == "question":
                    q_text = " ".join(
                        _inline(p).strip()
                        for p in sub
                        if (p.tag or "").lower() in ("para", "simpara")
                    )
                elif stag == "answer":
                    paras = [
                        _inline(p).strip()
                        for p in sub
                        if (p.tag or "").lower() in ("para", "simpara")
                    ]
                    a_parts = "\n\n".join(p for p in paras if p)
            if q_text:
                self._add(f"\n**Q: {q_text}**\n")
            if a_parts:
                self._add(f"\n{a_parts}\n")

    def _table(self, elem) -> None:
        title_txt = ""
        headers: list[str] = []
        rows: list[list[str]] = []

        def get_cells(row_elem) -> list[str]:
            return [
                _inline(e).strip().replace("|", "\\|")
                for e in row_elem
                if (e.tag or "").lower() == "entry"
            ]

        for child in elem:
            ctag = (child.tag or "").lower()
            if ctag == "title":
                title_txt = _inline(child).strip()
            elif ctag == "tgroup":
                for sub in child:
                    stag = (sub.tag or "").lower()
                    if stag == "thead":
                        for row in sub:
                            if (row.tag or "").lower() == "row":
                                headers = get_cells(row)
                    elif stag == "tbody":
                        for row in sub:
                            if (row.tag or "").lower() == "row":
                                rows.append(get_cells(row))

        if not (headers or rows):
            return

        if title_txt:
            self._add(f"\n**{title_txt}**\n")

        ncols = max(len(headers), max((len(r) for r in rows), default=0))
        if ncols == 0:
            return

        def pad(row, n):
            return row + [""] * (n - len(row))

        hdrs = pad(headers, ncols) if headers else [""] * ncols
        self._add("\n| " + " | ".join(hdrs) + " |")
        self._add("| " + " | ".join(["---"] * ncols) + " |")
        for row in rows:
            self._add("| " + " | ".join(pad(row, ncols)) + " |")
        self._add("")


# ---------------------------------------------------------------------------
# Per-module conversion
# ---------------------------------------------------------------------------

def _extract_description(root) -> str:
    """Return a short description from the first Overview para."""
    for elem in root.iter():
        if (elem.tag or "").lower() != "section":
            continue
        for child in elem:
            if (child.tag or "").lower() == "title" and "overview" in _inline(child).lower():
                for sub in elem:
                    if (sub.tag or "").lower() in ("para", "simpara"):
                        desc = _inline(sub).strip()
                        return desc[:297] + "..." if len(desc) > 300 else desc
                break
    return ""


def convert_module(module_dir: Path, global_entities: dict) -> str | None:
    xml_str = build_combined_xml(module_dir, global_entities)
    if xml_str is None:
        return None

    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as exc:
        print(f"  [WARN] XML parse error in {module_dir.name}: {exc}", file=sys.stderr)
        return None

    # Extract module title from <bookinfo><title>
    module_title = module_dir.name
    for elem in root.iter():
        if (elem.tag or "").lower() == "bookinfo":
            for child in elem:
                if (child.tag or "").lower() == "title":
                    module_title = _inline(child).strip()
                    break
            break

    description = re.sub(r"\s+", " ", _extract_description(root)).strip()

    emitter = _Emitter()
    body = emitter.emit(root)

    safe_title = module_title.replace('"', '\\"')
    safe_desc = description.replace('"', '\\"')

    fm = f'---\ntitle: "{safe_title}"\n'
    if safe_desc:
        fm += f'description: "{safe_desc}"\n'
    fm += "---\n"

    license_section = (
        "\n### License\n\n"
        "All documentation files (i.e. .md extension) are licensed under the "
        "Creative Common License 4.0\n"
    )

    content = fm + "\n" + body + "\n<!-- CONTRIBUTORS -->\n" + license_section
    return content, emitter.samples


def _write_samples(module_dir: Path, samples: list[dict]) -> None:
    """Copy referenced .cfg files into <module>/samples/ and write samples.md.

    samples.md is a frontmatter-less fragment: it is included into the module
    README (and, on the website, spliced inline), so it holds only the per-sample
    headings and the include links to ./samples/<file>.
    """
    doc_dir = module_dir / "doc"
    samples_dir = module_dir / "samples"
    samples_dir.mkdir(exist_ok=True)

    blocks: list[str] = []
    for s in samples:
        fname = s["file"]
        src = doc_dir / fname
        if not src.exists():
            continue
        shutil.copyfile(src, samples_dir / fname)
        heading = s["title"] or "Sample configuration"
        blocks.append(f'## {heading}\n\n[{fname}](./samples/{fname} "include")\n')

    if blocks:
        (module_dir / "samples.md").write_text("\n".join(blocks) + "\n", "utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    global_entities = load_global_entities()

    if len(sys.argv) > 1:
        module_names = sys.argv[1:]
    else:
        module_names = sorted(p.name for p in MODULES_DIR.iterdir() if p.is_dir())

    ok = failed = skipped = 0

    for name in module_names:
        module_dir = MODULES_DIR / name
        if not module_dir.is_dir():
            print(f"Not a directory: {module_dir}", file=sys.stderr)
            continue

        if not (module_dir / "doc").exists():
            skipped += 1
            continue

        print(f"Converting {name} ...", end=" ", flush=True)
        try:
            result = convert_module(module_dir, global_entities)
            if result is None:
                print("SKIPPED (no main XML)")
                skipped += 1
                continue
            content, samples = result

            out = module_dir / "README.md"
            out.write_text(content, encoding="utf-8")
            if samples:
                _write_samples(module_dir, samples)
            print(f"OK → {out.relative_to(REPO_ROOT)}"
                  + (f" (+{len(samples)} sample)" if samples else ""))
            ok += 1
        except Exception as exc:  # noqa: BLE001
            import traceback
            print(f"ERROR: {exc}", file=sys.stderr)
            traceback.print_exc()
            failed += 1

    print(f"\nDone: {ok} converted, {failed} failed, {skipped} skipped.")


if __name__ == "__main__":
    main()
