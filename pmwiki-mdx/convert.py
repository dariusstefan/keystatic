#!/usr/bin/env python3
"""Convert PMwiki page files to MDX with YAML frontmatter (Astro + Starlight)."""

import re
import sys
from pathlib import Path
from urllib.parse import unquote


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
    """Remove (:if false:) ... (:ifend:) disabled blocks."""
    return re.sub(r'\(:if false:\).*?\(:ifend:\)', '', text, flags=re.DOTALL)


def strip_nav_header(text: str) -> str:
    """Remove the boilerplate header block at the top of each PMwiki page.

    Typical structure:
        !!!!! Breadcrumb -> [[...]] -> Page Title   ← h1 nav, Starlight does this
        (:title Page Title:)                         ← directive
        ----                                         ← rule
        (:allVersions ...:)                          ← kept as <VersionNav> later
        (blank lines, \\, etc.)
        || Title banner row ||                       ← decorative, drop
        || [[Prev]] || [[Next]] ||                   ← nav, Starlight does this
        ----
        (:toc-float ...:)                            ← TOC, Starlight does this
    """
    lines = text.lstrip("\n").split("\n")
    i = 0

    def is_skippable(line: str) -> bool:
        s = line.strip()
        return (
            s == ""
            or s == "\\\\"
            or re.match(r'^-{4,}$', s)
            or re.match(r'^\(:.*:\)$', s)
            or (s.startswith("||") and ("Prev" in s or "Next" in s or re.search(r'\+.*\+', s)))
        )

    # Skip the h1 breadcrumb line
    if lines and lines[0].startswith("!!!!!"):
        i = 1

    # Skip all boilerplate lines until we hit real content
    while i < len(lines) and is_skippable(lines[i]):
        i += 1

    return "\n".join(lines[i:])


# ---------------------------------------------------------------------------
# Color → Badge/Aside mapping
# ---------------------------------------------------------------------------

CSS_COLOR = {
    "red":    "#e53e3e",
    "green":  "#2f855a",
    "blue":   "#2b6cb0",
    "orange": "#c05621",
}

# PMwiki color → Starlight Badge variant (for prose labels)
COLOR_BADGE = {
    "red":    "caution",
    "green":  "tip",
    "blue":   "note",
    "orange": "caution",
}

ASIDE_PHRASES = re.compile(
    r'TO BECOME OBSOLETE|DEPRECATED|OBSOLETE',
    re.IGNORECASE
)


def md_to_html_inline(text: str) -> str:
    """Convert already-processed markdown inline markup to HTML for use inside HTML spans."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*\n]+?)\*', r'<em>\1</em>', text)
    return text


def color_span_to_mdx(color: str, content: str, decorative: bool = False) -> str:
    content = content.strip()
    if ASIDE_PHRASES.search(content):
        return f"\n\n<Aside type=\"caution\">{content}</Aside>\n\n"
    if decorative:
        # Use a CSS class (e.g. .color-green) — avoids JSX curly-brace syntax.
        # Inner markdown converted to HTML since markdown doesn't render inside JSX.
        css_class = f"color-{color.lower()}"
        inner = md_to_html_inline(content)
        return f'<span class="{css_class}">{inner}</span>'
    variant = COLOR_BADGE.get(color.lower())
    if not variant:
        return content
    return f'<Badge text="{content}" variant="{variant}" />'


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def pmwiki_to_mdx(text: str) -> str:
    text = strip_false_conditionals(text)
    text = strip_nav_header(text)

    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Code block: [@ ... @]  (may span multiple lines)
        if line.strip().startswith("[@"):
            code_lines = []
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
                    code_lines.append(last[:-2])  # strip trailing @]
            if rest and not code_lines:
                code_lines = [rest]
            out.append("```c")
            out.extend(code_lines)
            out.append("```")
            i += 1
            continue

        line = convert_line(line)
        out.append(line)
        i += 1

    result = "\n".join(out)
    result = post_process(result)
    return result


def convert_line(line: str) -> str:
    # PMwiki heading convention: more ! = deeper/smaller heading
    # !!!!! = breadcrumb (stripped by strip_nav_header, map to h1 as fallback)
    # !!!  = top-level page sections → h2
    # !!!! = entries within sections → h3
    # !!   = sub-sections → h3
    # !    = deep sub-sub-sections → h4
    for bangs, level in [("!!!!!", 1), ("!!!!", 3), ("!!!", 2), ("!!", 3), ("!", 4)]:
        if line.startswith(bangs):
            content = line[len(bangs):].strip()
            content = convert_inline(content)
            return f"{'#' * level} {content}"

    # Horizontal rule
    if re.match(r'^-{4,}$', line.strip()):
        return "---"

    # Table rows  || cell || cell ||
    if line.strip().startswith("||"):
        return convert_table_row(line)

    # Bullet/numbered list (*, **, ***, #, ##, etc.)
    if re.match(r'^[*#]+\s', line):
        return convert_list_item(line)

    # Standalone anchor lines [[#name]] — drop
    if re.match(r'^\[\[#[\w.-]+\]\]$', line.strip()):
        return ""

    # PMwiki block divs >>...<< — drop
    if re.match(r'^>>[^<]*<<$', line.strip()):
        return ""
    if line.strip() in (">><<",):
        return ""

    # Directives (:...:) — handle known ones, drop the rest
    m = re.match(r'^\(:(\w+)\s*(.*?):\)$', line.strip())
    if m:
        directive, args = m.group(1), m.group(2).strip()
        if directive == "allVersions":
            # e.g. (:allVersions Script-CoreVar 4.1:)
            parts = args.split()
            page = parts[0] if parts else ""
            version = parts[1] if len(parts) > 1 else ""
            return f'<VersionNav page="{page}" version="{version}" />'
        if directive == "toc" or directive.startswith("toc"):
            return ""  # Starlight generates TOC automatically
        return ""

    # Line break \\ at end → MD line break (two trailing spaces)
    line = line.replace("\\\\", "  \n")

    return convert_inline(line)


def convert_list_item(line: str) -> str:
    depth = 0
    while line and line[0] in ("*", "#"):
        depth += 1
        line = line[1:]
    line = line.lstrip()
    indent = "  " * (depth - 1)
    return f"{indent}- {convert_inline(line)}"


def convert_table_row(line: str) -> str:
    line = line.strip()
    if line.startswith("||") and line.endswith("||"):
        line = line[2:-2]
    cells = line.split("||")
    cells = [convert_inline(c.strip()) for c in cells]
    return "| " + " | ".join(cells) + " |"


def convert_inline(text: str) -> str:
    # Bold: '''text''' → **text**
    text = re.sub(r"'''(.+?)'''", r"**\1**", text)
    # Italic: ''text'' → *text*
    text = re.sub(r"''(.+?)''", r"*\1*", text)

    # Anchor link icons [[#name|&#x1F517;]] — drop the icon, keep nothing
    text = re.sub(r'\[\[#[\w.-]+\|&#x1F517;\]\]', '', text)

    # Wiki links with label: [[Page.Name|Label]] or [[#anchor|Label]]
    def wiki_link(m):
        page, label = m.group(1).strip(), m.group(2).strip()
        if page.startswith("#"):
            return f"[{label}]({page})"
        if page.startswith("http://") or page.startswith("https://"):
            return f"[{label}]({page})"
        return f"[{label}]({page_to_slug(page)})"
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', wiki_link, text)

    # Wiki links without label
    def wiki_link_no_label(m):
        page = m.group(1).strip()
        if page.startswith("#"):
            return f"[{page[1:]}]({page})"
        if page.startswith("http://") or page.startswith("https://"):
            return f"<{page}>"
        return f"[{page}]({page_to_slug(page)})"
    text = re.sub(r'\[\[([^\]]+)\]\]', wiki_link_no_label, text)

    # Color spans %color%text%% → Badge or Aside
    # But if the span is inside a code-like context (contains $ or starts with $)
    # or is a single short token, just strip the color — it's decorative syntax markup.
    def replace_color(m):
        color, content = m.group(1), m.group(2)
        stripped = content.strip()
        is_decorative = (
            not ASIDE_PHRASES.search(stripped)
            and (
                any(c in stripped for c in ("$", "''", "'''", "*<", "[+"))
                or (len(stripped) < 30 and not re.search(r'\b(is|are|was|It)\b', stripped))
            )
        )
        return color_span_to_mdx(color, stripped, decorative=is_decorative)
    text = re.sub(r'%([\w]+)%(.*?)%%', replace_color, text)
    # Handle %key=value% form (e.g. %color=#185662%) — just strip
    text = re.sub(r'%[\w#=]+%(.*?)%%', r'\1', text)
    # Leftover lone % markers
    text = re.sub(r'%[\w#=]+%', '', text)
    text = re.sub(r'%%', '', text)

    # Standalone anchor refs [[#name]] → drop
    text = re.sub(r'\[\[#[\w.-]+\]\]', '', text)

    # Superscript [+text+] → text
    text = re.sub(r'\[\+(.+?)\+\]', r'\1', text)

    # Trailing \\ line break → two spaces
    text = re.sub(r'\\\\$', '  ', text)

    return text


def page_to_slug(page: str) -> str:
    return "/" + page.replace(".", "/").lower()


def escape_mdx_prose(text: str) -> str:
    """Escape characters that MDX's acorn parser misreads in prose content.

    MDX 2+ treats { } as JS expressions and <word> as JSX tags outside of
    fenced code blocks. We also detect 4-space-indented blocks (which MDX does
    NOT treat as code, unlike CommonMark) and wrap them in fences.
    """
    lines = text.split("\n")
    out = []
    in_fence = False
    fence_marker = ""

    # First pass: detect indented-only code blocks and fence them.
    # A run of lines all indented by 4+ spaces, surrounded by blank lines,
    # and not already inside a fence → wrap with ```c ... ```.
    fenced_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Track fences
        if re.match(r'^```', line):
            fenced_lines.append(line)
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            fenced_lines.append(line)
            i += 1
            continue

        # Detect a block of 4-space-indented lines
        if re.match(r'^    \S', line):
            block = []
            while i < len(lines) and (re.match(r'^    ', lines[i]) or lines[i].strip() == ""):
                block.append(lines[i])
                i += 1
            # Strip trailing blank lines from block
            while block and block[-1].strip() == "":
                fenced_lines.append(block.pop())
            if block:
                fenced_lines.append("```c")
                for bl in block:
                    fenced_lines.append(bl[4:])  # dedent
                fenced_lines.append("```")
            continue  # i was already advanced by the while above
        fenced_lines.append(line)
        i += 1

    lines = fenced_lines

    # Second pass: escape { } and bare <tag> in prose (outside fenced blocks).
    in_fence = False
    for line in lines:
        if re.match(r'^```', line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue

        # Don't escape inside inline code spans (`...`)
        # Split on backtick pairs and only process outside them
        line = escape_prose_line(line)
        out.append(line)

    return "\n".join(out)


# HTML tags we generate ourselves — don't escape these
_SAFE_HTML_TAGS = {'span', 'strong', 'em', 'a', 'br', 'code', 'aside', 'badge'}


def escape_prose_line(line: str) -> str:
    """Escape MDX-unsafe characters in a single prose line, skipping inline code and our own HTML."""
    result = []
    # Split on backtick code spans AND on our generated HTML tags/JSX components
    # so we don't double-escape them.
    # Pattern: backtick spans | opening tags with attrs | closing tags
    segments = re.split(r'(`[^`]*`|<[A-Z][^>]*/>|<[A-Z][^>]*>|</[A-Z][^>]*>)', line)
    for seg in segments:
        # Leave backtick code and JSX components (uppercase) untouched
        if (seg.startswith("`") and seg.endswith("`")) or re.match(r'</?[A-Z]', seg):
            result.append(seg)
            continue
        # Escape { and }
        seg = seg.replace("{", r"\{").replace("}", r"\}")
        # Escape bare <tag> / </tag> that look like SIP/protocol tags (NOT known HTML)
        def escape_tag(m):
            slash, tag = m.group(1), m.group(2)
            if tag.lower() in _SAFE_HTML_TAGS:
                return m.group(0)  # keep our HTML
            return f'&lt;{slash}{tag}&gt;'
        seg = re.sub(r'<(/?)([a-zA-Z][a-zA-Z0-9_.-]*)>', escape_tag, seg)
        result.append(seg)
    return "".join(result)


def post_process(text: str) -> str:
    # Collapse more than 2 consecutive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = escape_mdx_prose(text)
    return text.strip()


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------

def convert_file(src: Path, dst: Path):
    meta = parse_pmwiki_file(src)

    raw_text = meta.get("text", "")
    decoded = decode_pmwiki_text(raw_text)
    body = pmwiki_to_mdx(decoded)

    title = meta.get("title", src.stem)
    author = meta.get("author", "")
    ctime = meta.get("ctime", "")
    rev = meta.get("rev", "")

    fm = ["---", f'title: "{title}"']
    if author:
        fm.append(f"author: {author}")
    if ctime:
        fm.append(f"ctime: {ctime}")
    if rev:
        fm.append(f"revision: {rev}")
    fm.append("---")

    # No import statements — components are registered globally in Keystatic config
    # and as MDX components in astro.config.mjs for the Astro build.
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
