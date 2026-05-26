#!/usr/bin/env python3
"""Convert OpenSIPS module DocBook XML docs to README.md files.

Reads opensips/modules/<name>/doc/*.xml and writes a single README.md per
module with Starlight-compatible YAML frontmatter.

Usage:
    python3 pmwiki-mdx/docbook_to_md.py            # convert all 193 modules
    python3 pmwiki-mdx/docbook_to_md.py acc dialog  # convert specific modules
"""

import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "opensips" / "modules"
ENTITIES_FILE = REPO_ROOT / "opensips" / "doc" / "entities.xml"

# Standard XML character entities — handled by the parser; never substituted
# by our pre-processor so they aren't lost before ET.fromstring() runs.
XML_ENTITIES = {"lt", "gt", "amp", "quot", "apos"}


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
        result = f"^{inner}^"
    elif tag == "subscript":
        result = f"~{inner}~"
    elif tag in ("para", "simpara"):
        result = inner.strip()
    elif tag in ("programlisting", "screen"):
        result = f"\n```\n{(elem.text or '').rstrip()}\n```\n"
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
        elif tag == "book":
            for child in elem:
                self._block(child, depth)
        elif tag in ("chapter", "section", "refsect1", "refsect2", "refsect3"):
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
        title_txt = self._get_title(elem)
        if title_txt:
            level = min(depth + 1, 6)
            self._add(f'\n{"#" * level} {title_txt}\n')
        for child in elem:
            if (child.tag or "").lower() != "title":
                self._block(child, depth + 1)

    def _get_title(self, elem) -> str:
        for child in elem:
            if (child.tag or "").lower() == "title":
                return _inline(child).strip().replace('`', '')
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

    def _code(self, elem) -> None:
        code = (elem.text or "").strip("\n")
        lang = ""
        if any(kw in code for kw in (
            "loadmodule", "modparam", "route {", "route{",
            "is_method(", "xlog(", "t_relay(", "sl_send_reply(",
        )):
            lang = "opensips"
        self._add(f"\n```{lang}\n{code}\n```\n")

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

    def _admonition(self, elem, label: str, depth: int) -> None:
        parts = [
            _inline(c).strip()
            for c in elem
            if (c.tag or "").lower() in ("para", "simpara")
        ]
        text = " ".join(p for p in parts if p)
        if text:
            self._add(f"\n> **{label}:** {text}\n")

    def _example(self, elem, depth: int) -> None:
        title_txt = self._get_title(elem)
        if title_txt:
            self._add(f"\n**Example: {title_txt}**\n")
        for child in elem:
            if (child.tag or "").lower() != "title":
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

    body = _Emitter().emit(root)

    safe_title = module_title.replace('"', '\\"')
    safe_desc = description.replace('"', '\\"')

    fm = f'---\ntitle: "{safe_title}"\n'
    if safe_desc:
        fm += f'description: "{safe_desc}"\n'
    fm += "---\n"

    return fm + "\n" + body + "\n"


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
            content = convert_module(module_dir, global_entities)
            if content is None:
                print("SKIPPED (no main XML)")
                skipped += 1
                continue

            out = module_dir / "README.md"
            out.write_text(content, encoding="utf-8")
            print(f"OK → {out.relative_to(REPO_ROOT)}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            import traceback
            print(f"ERROR: {exc}", file=sys.stderr)
            traceback.print_exc()
            failed += 1

    print(f"\nDone: {ok} converted, {failed} failed, {skipped} skipped.")


if __name__ == "__main__":
    main()
