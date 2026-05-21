#!/usr/bin/env python3
"""Convert PMwiki page files to MDX with YAML frontmatter.

Targets the Astro + Starlight + Keystatic stack. The output uses only
constructs Keystatic's MDX editor can round-trip:
  - vanilla Markdown for all prose/lists/headings/links/tables/code
  - Markdown blockquotes for caution/observation notes
  - @@color|text@@ markers for colored inline text
  - inline code (backticks) for anything containing braces, angle brackets,
    or other MDX-unsafe characters — no \\{ escapes, no &lt; entities
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote


# ---------------------------------------------------------------------------
# PMwiki file I/O
# ---------------------------------------------------------------------------

def parse_pmwiki_file(path: Path) -> dict:
    meta = {}
    with open(path, encoding="latin-1") as f:
        for line in f:
            line = line.rstrip("\n")
            m = re.match(r'^(\w+)=(.*)$', line)
            if m:
                key, val = m.group(1), m.group(2)
                if key not in meta:  # keep first occurrence (current revision)
                    meta[key] = val
    return meta


def decode_pmwiki_text(text: str) -> str:
    return unquote(text, encoding="latin-1")


# ---------------------------------------------------------------------------
# Pre-processing
# ---------------------------------------------------------------------------

def strip_false_conditionals(text: str) -> str:
    return re.sub(r'\(:if false:\).*?\(:ifend:\)', '', text, flags=re.DOTALL)


def strip_nav_header(text: str) -> str:
    """Drop the PMwiki page header (breadcrumb, title directive, prev/next nav)."""
    lines = text.lstrip("\n").split("\n")
    i = 0

    def is_skippable(line: str) -> bool:
        s = line.strip()
        return (
            s == ""
            or s == "\\\\"
            or bool(re.match(r'^-{4,}$', s))
            or bool(re.match(r'^\(:.*:\)$', s))
            or (s.startswith("||") and ("Prev" in s or "Next" in s or bool(re.search(r'\+.*\+', s))))
        )

    if lines and lines[0].startswith("!!!!!"):
        i = 1
    while i < len(lines) and is_skippable(lines[i]):
        i += 1
    return "\n".join(lines[i:])


# ---------------------------------------------------------------------------
# Color span → Keystatic-safe Markdown
# ---------------------------------------------------------------------------

ASIDE_PHRASES = re.compile(r'TO BECOME OBSOLETE|DEPRECATED|OBSOLETE', re.IGNORECASE)

SUPPORTED_COLORS = {"red", "green", "blue", "orange", "yellow"}


def html_inline_to_md(text: str) -> str:
    """Convert inline HTML back to Markdown so we don't leak raw tags."""
    text = re.sub(r'<strong>(.+?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<em>(.+?)</em>', r'*\1*', text, flags=re.DOTALL)
    return text


def code_color_markup_to_markers(text: str) -> str:
    """Preserve PMWiki color spans inside code-like snippets.

    The returned string is meant to live inside Markdown code. The remark
    plugin later turns the markers into colored spans inside <code>.
    """
    out: list[str] = []
    color: str | None = None

    for token in re.split(r'(%%|%[a-zA-Z]+%)', text):
        if not token:
            continue
        if token == "%%":
            color = None
            continue

        marker = re.fullmatch(r'%([a-zA-Z]+)%', token)
        if marker:
            next_color = marker.group(1).lower()
            color = next_color if next_color in SUPPORTED_COLORS else None
            continue

        content = token.replace("'''", "").replace("''", "")
        if color:
            out.append(f"@@{color}|{content}@@")
        else:
            out.append(content)

    return "".join(out)


def code_variable_tokens(text: str) -> str:
    """Wrap OpenSIPS variable-looking tokens in inline code.

    Existing inline code and color markers are left untouched. Headings call
    convert_inline(..., code_variables=False), so their variable names stay as
    plain heading text.
    """
    segments = re.split(r'(`[^`]*`|@@(?:red|green|blue|orange|yellow)\|.*?@@)', text)
    return "".join(_code_variable_tokens_segment(seg) for seg in segments if seg)


def _code_variable_tokens_segment(text: str) -> str:
    if (text.startswith("`") and text.endswith("`")) or re.match(r'@@(?:red|green|blue|orange|yellow)\|', text):
        return text

    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i] != "$":
            out.append(text[i])
            i += 1
            continue

        end = _scan_variable_token(text, i)
        if end == i:
            out.append(text[i])
            i += 1
            continue

        out.append(f"`{text[i:end]}`")
        i = end

    coded = "".join(out)
    coded = re.sub(r'\*\*(`[^`]+`)\*\*', r'\1', coded)
    return coded


def _scan_variable_token(text: str, start: int) -> int:
    i = start + 1
    if i >= len(text):
        return start

    if text[i] == "(":
        return _scan_balanced(text, start, "(", ")")

    if not re.match(r'[A-Za-z_]', text[i]):
        return start

    while i < len(text) and re.match(r'[A-Za-z0-9_.]', text[i]):
        i += 1

    if i < len(text) and text[i] == "(":
        i = _scan_balanced(text, i - 1, "(", ")")

    while i < len(text) and text[i] == "[":
        i = _scan_balanced(text, i - 1, "[", "]")

    return i


def _scan_balanced(text: str, before_open: int, open_char: str, close_char: str) -> int:
    i = before_open + 1
    depth = 0
    while i < len(text):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                return i + 1
        elif depth == 0 and text[i].isspace():
            return i
        i += 1
    return i


_EMPHASIS_TAGS = r'(?:em|strong|span|b|i|u|code|br|sub|sup|small|tt)'


def strip_markup(text: str) -> str:
    """Strip emphasis/color markup; preserve protocol-style <word> tokens as text."""
    # Only strip known emphasis HTML tags, not arbitrary <word> (which may be content like <context>)
    text = re.sub(rf'</?{_EMPHASIS_TAGS}(?:\s[^>]*)?>', '', text, flags=re.IGNORECASE)
    # Decode HTML entities
    text = (text.replace('&lt;', '<').replace('&gt;', '>')
                .replace('&amp;', '&').replace('&nbsp;', ' '))
    # Strip nested PMwiki color markers
    text = re.sub(r'%[a-zA-Z#=0-9]+%', '', text)
    text = text.replace('%%', '')
    # Unescape \{ \}
    text = re.sub(r'\\([{}])', r'\1', text)
    # Drop emphasis markers
    text = re.sub(r'\*+', '', text)
    text = re.sub(r"'{2,}", '', text)
    return text.strip()


def color_span_to_mdx(color: str, content: str) -> str:
    """Map a PMwiki %color%...%% span to Markdown-safe text.

    Rules:
      - 'TO BECOME OBSOLETE' / 'DEPRECATED' → Attention warning
      - supported colors                    → @@color[text]@@
      - everything else                     → plain Markdown (color dropped)
    """
    content = content.strip()
    if not content:
        return ""

    if ASIDE_PHRASES.search(content):
        return f'@@yellow|Attention!@@ @@red|{strip_markup(content)}@@'

    color = color.lower()
    content = strip_markup(content)
    is_code_like = bool(re.search(r'[$()\[\]<>{}]', content))
    if color in SUPPORTED_COLORS and is_code_like:
        return f'`@@{color}|{content}@@`'

    is_mdx_unsafe = bool(re.search(r'[<>{}]', content))
    if is_mdx_unsafe:
        return f'`{content}`'

    if color in SUPPORTED_COLORS:
        return f'@@{color}|{content}@@'

    # Default: color is decorative, drop it and keep prose as Markdown
    return html_inline_to_md(content)


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def pmwiki_to_mdx(text: str) -> str:
    text = strip_false_conditionals(text)
    text = strip_nav_header(text)

    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block: [@ ... @]
        if line.strip().startswith("[@"):
            code_lines: list[str] = []
            rest = line.strip()[2:]
            if rest.endswith("@]"):
                rest = rest[:-2]
            else:
                code_lines.append(rest)
                i += 1
                while i < len(lines) and not lines[i].rstrip().endswith("@]"):
                    code_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    last = lines[i].rstrip()
                    code_lines.append(last[:-2])
            if rest and not code_lines:
                code_lines = [rest]
            out.append("```c")
            out.extend(code_lines)
            out.append("```")
            i += 1
            continue

        # Table block: collect consecutive ||...|| rows and render with separator
        if line.strip().startswith("||") and "||" in line.strip()[2:]:
            rows: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("||"):
                rows.append(lines[i])
                i += 1
            out.extend(render_table(rows))
            continue

        out.append(convert_line(line))
        i += 1

    result = "\n".join(out)
    return post_process(result)


def render_table(rows: list[str]) -> list[str]:
    """Render a block of PMwiki table rows as a GFM Markdown table."""
    parsed: list[list[str]] = []
    for raw in rows:
        s = raw.strip()
        if s.startswith("||"):
            s = s[2:]
        if s.endswith("||"):
            s = s[:-2]
        cells = [convert_inline(c.strip()) for c in s.split("||")]
        # Drop fully-empty rows (PMwiki spacers)
        if any(c.strip() for c in cells):
            parsed.append(cells)
    if not parsed:
        return []
    width = max(len(r) for r in parsed)
    parsed = [r + [""] * (width - len(r)) for r in parsed]
    out = [
        "| " + " | ".join(parsed[0]) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in parsed[1:]:
        out.append("| " + " | ".join(row) + " |")
    return out


def convert_line(line: str) -> str:
    # Headings — PMwiki uses ! count for level (! = deepest, !!!!! = top breadcrumb)
    for bangs, level in [("!!!!!", 1), ("!!!!", 3), ("!!!", 2), ("!!", 3), ("!", 4)]:
        if line.startswith(bangs):
            content = line[len(bangs):].strip()
            return f"{'#' * level} {convert_inline(content, code_variables=False)}"

    if re.match(r'^-{4,}$', line.strip()):
        return "\n---\n"

    if re.match(r'^[*#]+\s', line):
        return convert_list_item(line)

    if line.strip().startswith("$(") and re.search(r'%[a-zA-Z]+%', line):
        return f"`{code_color_markup_to_markers(line.strip())}`"

    # Preserve standalone PMWiki anchors as source-friendly markers.
    m = re.match(r'^\[\[#([\w.-]+)\]\]$', line.strip())
    if m:
        return f"@@anchor|{m.group(1)}@@"
    if re.match(r'^>>[^<]*<<$', line.strip()) or line.strip() == ">><<":
        return ""

    # Directives — we drop everything except known ones. <VersionNav> is dropped
    # because there's no registered component for it.
    m = re.match(r'^\(:(\w+)\s*(.*?):\)$', line.strip())
    if m:
        return ""  # TOC, allVersions, etc.

    line = line.replace("\\\\", "  \n")
    if line.strip().lower().startswith("note:"):
        note = line.strip().split(":", 1)[1].strip()
        note = re.sub(r"'''(.+?)'''", r"\1", note)
        note = re.sub(r"''(.+?)''", r"\1", note)
        return f"> **Observation:** {convert_inline(note)}"
    converted = convert_inline(line)
    if converted.startswith("@@yellow|Attention!@@"):
        return f"> {converted}"
    return converted


def convert_list_item(line: str) -> str:
    depth = 0
    while line and line[0] in ("*", "#"):
        depth += 1
        line = line[1:]
    line = line.lstrip()
    indent = "  " * (depth - 1)
    return f"{indent}* {convert_inline(line)}"


def convert_inline(text: str, code_variables: bool = True) -> str:
    # Bold / italic
    text = re.sub(r"'''(.+?)'''", r"**\1**", text)
    text = re.sub(r"''(.+?)''", r"*\1*", text)

    # Drop link-icon anchors
    text = re.sub(r'\[\[#[\w.-]+\|&#x1F517;\]\]', '', text)

    def wiki_link(m):
        page, label = m.group(1).strip(), m.group(2).strip()
        if page.startswith("#"):
            return f"[{label}]({page})"
        if page.startswith(("http://", "https://")):
            return f"[{label}]({page})"
        return f"[{label}]({page_to_slug(page)})"
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', wiki_link, text)

    def wiki_link_no_label(m):
        page = m.group(1).strip()
        if page.startswith("#"):
            return f"[{page[1:]}]({page})"
        if page.startswith(("http://", "https://")):
            return f"<{page}>"
        return f"[{page}]({page_to_slug(page)})"
    text = re.sub(r'\[\[([^\]]+)\]\]', wiki_link_no_label, text)

    # Color spans %color%text%%
    def replace_color(m):
        return color_span_to_mdx(m.group(1), m.group(2))
    text = re.sub(r'%([a-zA-Z]+)%(.*?)%%', replace_color, text)

    # Unclosed PMWiki color spans at the end of a line, e.g. "%green%$ru".
    text = re.sub(r'%([a-zA-Z]+)%([^%\n]+)$', replace_color, text)

    # %key=value% directives (e.g. %color=#185662%) — drop wrapper, keep content
    text = re.sub(r'%[\w#=]+%(.*?)%%', r'\1', text)
    text = re.sub(r'%[\w#=]+%', '', text)
    text = re.sub(r'%%', '', text)

    text = re.sub(r'\[\[#[\w.-]+\]\]', '', text)
    text = re.sub(r'\[\+(.+?)\+\]', r'\1', text)
    text = re.sub(r'\\\\$', '  ', text)
    if code_variables:
        text = code_variable_tokens(text)
    return text


def page_to_slug(page: str) -> str:
    return "/" + page.replace(".", "/").lower()


# ---------------------------------------------------------------------------
# MDX safety pass — wrap dangerous chars in inline code instead of escaping
# ---------------------------------------------------------------------------

_SAFE_HTML_TAGS = {'span', 'strong', 'em', 'a', 'br', 'code', 'aside', 'badge'}


def post_process(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    return mdx_safety_pass(text).strip()


def mdx_safety_pass(text: str) -> str:
    """Detect indented-code blocks, fence them, then wrap unsafe chars in backticks
    in prose (outside any fenced block)."""
    lines = text.split("\n")
    fenced: list[str] = []
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^```', line):
            fenced.append(line)
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            fenced.append(line)
            i += 1
            continue
        if re.match(r'^    \S', line):
            block: list[str] = []
            while i < len(lines) and (re.match(r'^    ', lines[i]) or lines[i].strip() == ""):
                block.append(lines[i])
                i += 1
            trailing: list[str] = []
            while block and block[-1].strip() == "":
                trailing.insert(0, block.pop())
            if block:
                fenced.append("```c")
                for bl in block:
                    fenced.append(bl[4:])
                fenced.append("```")
            fenced.extend(trailing)
            continue
        fenced.append(line)
        i += 1

    out: list[str] = []
    in_fence = False
    for line in fenced:
        if re.match(r'^```', line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        out.append(escape_prose_line(line))
    return "\n".join(out)


def escape_prose_line(line: str) -> str:
    """Wrap MDX-unsafe substrings in inline code, keeping existing code spans
    and registered JSX components untouched. No backslash escapes, no &lt; entities."""
    result: list[str] = []
    # Split on inline code spans, color markers, and JSX components.
    segments = re.split(
        r'(`[^`]*`|@@(?:red|green|blue|orange|yellow)\|.*?@@|<[A-Z][A-Za-z0-9]*\s*/>|<[A-Z][A-Za-z0-9]*[^>]*?/>|<[A-Z][A-Za-z0-9]*[^>]*>|</[A-Z][A-Za-z0-9]*>)',
        line,
    )
    for seg in segments:
        if not seg:
            continue
        if (
            (seg.startswith("`") and seg.endswith("`"))
            or re.match(r'@@(?:red|green|blue|orange|yellow)\|', seg)
            or re.match(r'</?[A-Z]', seg)
        ):
            result.append(seg)
            continue

        # Matched {...} pairs → inline code
        seg = re.sub(r'\{([^{}]*)\}', r'`{\1}`', seg)
        # Any remaining lone braces are still MDX expression delimiters.
        seg = re.sub(r'(?<!`)([{}])(?!`)', r'`\1`', seg)

        # <…> patterns: leave Markdown autolinks (http/mailto) and known HTML tags;
        # wrap protocol-style or unknown bare tags in backticks.
        def wrap_lt(m):
            inner = m.group(1)
            stripped = inner.lstrip('/').split(' ')[0].split(':')[0]
            if re.match(r'/?(?:https?|mailto|ftp)$', inner.lstrip('/').split(':')[0], re.I):
                return m.group(0)
            if stripped.lower() in _SAFE_HTML_TAGS:
                return m.group(0)
            return f'`<{inner}>`'
        seg = re.sub(r'<(/?[A-Za-z][A-Za-z0-9_.:@/-]*)>', wrap_lt, seg)

        result.append(seg)
    return "".join(result)


# ---------------------------------------------------------------------------
# Description extraction + file output
# ---------------------------------------------------------------------------

def extract_description(body: str) -> str:
    """First real prose paragraph, markup-stripped, truncated to ~160 chars."""
    for para in re.split(r'\n\s*\n', body):
        para = para.strip()
        if not para:
            continue
        if para.startswith(('#', '```', '|', '<', '-', '*', '!', '>', '[')):
            continue
        plain = strip_markup(para)
        plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)
        plain = re.sub(r'`([^`]+)`', r'\1', plain)
        plain = re.sub(r'\s+', ' ', plain).strip()
        if not plain:
            continue
        if len(plain) > 160:
            plain = plain[:157].rstrip() + "..."
        return plain
    return ""


def yaml_quote(text: str) -> str:
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')


def convert_file(src: Path, dst: Path):
    meta = parse_pmwiki_file(src)
    raw_text = meta.get("text", "")
    decoded = decode_pmwiki_text(raw_text)
    body = pmwiki_to_mdx(decoded)

    title = meta.get("title", src.stem)
    description = extract_description(body)

    fm = [
        "---",
        f'title: "{yaml_quote(title)}"',
        f'description: "{yaml_quote(description)}"',
        "---",
    ]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(fm) + "\n\n" + body + "\n", encoding="utf-8")
    print(f"  {src.name} → {dst}")


def main():
    src_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    dst_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else src_dir / "output"

    files = [
        f for f in src_dir.iterdir()
        if f.is_file() and "." in f.name and f.suffix not in (".py", ".md", ".mdx")
    ]
    if not files:
        print("No PMwiki files found.")
        return

    print(f"Converting {len(files)} file(s) → {dst_dir}/")
    for f in sorted(files):
        parts = f.name.split(".", 1)
        group = parts[0].lower()
        page = parts[1].lower().replace(".", "-") if len(parts) > 1 else f.stem.lower()
        out_path = dst_dir / group / f"{page}.mdx"
        convert_file(f, out_path)


if __name__ == "__main__":
    main()
