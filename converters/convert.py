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

import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# Module-level redirect map: populated by load_redirects(wiki_dir).
# Maps PMwiki page names (e.g. "Resources.DocsTsStart") to their targets
# (e.g. "Documentation.TroubleShooting-DoesNotStart").
_REDIRECTS: dict[str, str] = {}

# Slug map: populated by load_slug_map(content_dir).
# Maps normalized filename stem (lowercase, no hyphens) to the actual site slug.
# e.g. "troubleshootingdoesnotstart" -> "/documentation/troubleshooting/troubleshooting-doesnotstart"
_SLUG_MAP: dict[str, str] = {}

# Manual link map: populated by convert_manual.py when converting a single
# version manual into a flat repo docs/ directory. Maps normalized page stem
# (see _manual_link_key) to a sibling relative filename, e.g.
# "installdownload41" -> "Install-Download.md". When non-empty, page_to_slug
# resolves in-manual references to these relative .md links instead of website
# slugs, keeping the converted manual self-contained.
_MANUAL_LINKS: dict[str, str] = {}


# Legacy OpenSIPS website module-doc URLs — current and older /html/docs/ path,
# with or without the .html suffix — capturing (version dir, module, anchor):
#   opensips.org/docs/modules/<ver>.x/<mod>.html[#anchor]
#   www.opensips.org/html/docs/modules/<ver>.x/<mod>[#anchor]
_MOD_DOC_RE = re.compile(
    r"https?://(?:www\.)?opensips\.org/(?:html/)?docs/modules/([^/]+)/([\w.\-]+?)(?:\.html)?(#\S*)?$",
    re.IGNORECASE,
)
# The module version whose website slug is "devel" (the master/dev branch).
_LATEST_MOD_VER = "4.1"

# Canonical website origin. Used to make manual links to website-only "flat"
# pages (migration/tutorials/… — not in the fork) absolute, so they work on
# github.com too. generate-manual-docs.adapt_links strips this back to a
# root-relative path for the on-site build.
SITE_URL = "https://web.opensips.org"

# Manual page set (de-versioned stems, lowercased) — populated by
# load_manual_pages() / convert_manual(). Old manual URLs used a version SUFFIX
# (Script-CoreVar-3-6); the manual now lives at /docs/manual/<ver>/<page>.
_MANUAL_PAGES: set[str] = set()
# The manual version whose website slug is "devel" (master/dev branch).
_LATEST_MANUAL_VER = "4-1"


def _manual_page_ref(seg: str):
    """A version-suffixed manual page name ('Script-CoreVar-3-6') → (page, slug)
    when the de-versioned name is a known manual page, else None. 4-1 → devel."""
    m = re.match(r"^(.*?)-(\d+)-(\d+)$", seg)
    if not m:
        return None
    page = m.group(1).lower()
    if page not in _MANUAL_PAGES:
        return None
    ver = f"{m.group(2)}-{m.group(3)}"
    return page, ("devel" if ver == _LATEST_MANUAL_VER else ver)


def load_manual_pages(content_dir: Path) -> None:
    """Populate _MANUAL_PAGES from the website manual content
    (content_dir/docs/manual/<ver>/<page>.md), unioned across versions."""
    man_root = content_dir / "docs" / "manual"
    if not man_root.exists():
        return
    for p in man_root.rglob("*.md"):
        s = p.stem.lower()
        if s != "index":
            _MANUAL_PAGES.add(s)


def _modver_to_slug(verdir: str) -> str:
    """A module-doc version dir ('3.5.x', '4.1.x', 'devel', …) → its website
    slug ('3-5', 'devel', …). The latest release dir maps to 'devel'."""
    v = verdir.strip().lower()
    if v in ("devel", "latest"):
        return "devel"
    m = re.match(r"(\d+)\.(\d+)", v)
    if not m:
        return v
    mm = f"{m.group(1)}.{m.group(2)}"
    return "devel" if mm == _LATEST_MOD_VER else f"{m.group(1)}-{m.group(2)}"


def _module_doc_web(url: str):
    """A legacy website module-doc URL → an internal website route
    /docs/modules/<slug>/<mod>[#anchor], or None if it isn't one. The pinned
    <ver>.x is mapped to its slug so the link keeps pointing at that version."""
    m = _MOD_DOC_RE.match(url or "")
    if not m:
        return None
    return f"/docs/modules/{_modver_to_slug(m.group(1))}/{m.group(2)}{m.group(3) or ''}"


# ---------------------------------------------------------------------------
# PMwiki file I/O
# ---------------------------------------------------------------------------

def parse_pmwiki_file(path: Path) -> dict:
    meta = {}
    with open(path, encoding="cp1252", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            m = re.match(r'^(\w+)=(.*)$', line)
            if m:
                key, val = m.group(1), m.group(2)
                if key not in meta:  # keep first occurrence (current revision)
                    meta[key] = val
    return meta


def decode_pmwiki_text(text: str) -> str:
    text = unquote(text, encoding="cp1252", errors="replace")
    # <pre>...</pre> blocks (GeSHi syntax-highlighted HTML) → strip tags, keep text.
    # Must run BEFORE html.unescape so that &lt;tag&gt; inside <pre> blocks is not
    # unescaped to <tag> and then accidentally stripped by the tag-stripping regex.
    def pre_to_plain(m):
        inner = m.group(1)
        inner = re.sub(r'<br\s*/?>', '\n', inner, flags=re.IGNORECASE)  # <br> → newline
        inner = re.sub(r'<[^>]+>', '', inner)
        inner = inner.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ').replace('&quot;', '"')
        return f'[@\n{inner.strip()}\n@]'
    text = re.sub(r'<pre>(.*?)</pre>', pre_to_plain, text, flags=re.DOTALL)
    # Decode remaining HTML character entities in prose (e.g. &#539; → ț, &mdash; → —).
    text = html.unescape(text)
    # Transliterate Romanian/diacritic characters to plain ASCII.
    text = text.translate(str.maketrans(
        'țțșșăâî'
        'ȚȚȘȘĂÂÎ',
        'ttssaai'
        'TTSSAAI',
    ))
    return text


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
            # PMwiki page-variable artifacts in the header, e.g.
            # "This page has been visited {$PageCount} times." — otherwise this
            # non-skippable line halts the loop before the prev/next nav below it.
            or bool(re.search(r'\{\$\w+\}', s))
            or (s.startswith("||") and ("Prev" in s or "Next" in s or bool(re.search(r'\+.*\+', s))))
        )

    if lines and re.match(r'^!{4,5}', lines[0]) and '->' in lines[0]:
        i = 1
    while i < len(lines) and is_skippable(lines[i]):
        i += 1
    return "\n".join(lines[i:])


# ---------------------------------------------------------------------------
# Color span → Keystatic-safe Markdown
# ---------------------------------------------------------------------------

ASIDE_PHRASES = re.compile(r'TO BECOME OBSOLETE|DEPRECATED|OBSOLETE')

SUPPORTED_COLORS = {"red", "green", "blue", "orange", "yellow"}

# Module-listing maturity badges. On the Modules manual page each module bullet
# ends with a maturity status; instead of colored text we render a colored-dot
# emoji + bold label (simpler, plugin-free Markdown). Anchored to the trailing
# status and gated on a module-doc link so prose is never touched.
_MODULE_LINK_RE = re.compile(r"\((?:\.\./|/docs/)modules/")
_MODULE_STATUS_BADGES = (
    (re.compile(r"\s*,\s*@@green\|stable@@\s*$"), " — 🟢 **stable**"),
    (re.compile(r"\s*,\s*@@red\|NEW@@\s*$"), " — 🔵 **NEW**"),
    (re.compile(r"\s*,\s*beta\s*$"), " — 🟡 **beta**"),
)


def apply_module_status_badge(content: str) -> str:
    """Rewrite a module bullet's trailing maturity status to an emoji badge."""
    if not _MODULE_LINK_RE.search(content):
        return content
    for pattern, replacement in _MODULE_STATUS_BADGES:
        new = pattern.sub(replacement, content)
        if new != content:
            return new
    return content


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

        # Include any word-char prefix immediately before the $ so that tokens
        # like "passwd_$tu" become `passwd_$tu` rather than passwd_`$tu`.
        prefix = ""
        if out and re.match(r'\w', out[-1]):
            j = len(out) - 1
            while j > 0 and re.match(r'\w', out[j - 1]):
                j -= 1
            prefix = "".join(out[j:])
            out = out[:j]

        # Extend forward through path/extension characters so that tokens like
        # "$OPENSIPS_HOME/etc/tls/ca.conf" become one code span, not two.
        # Only enter path mode when the separator after the variable is followed
        # by a non-$ word char — this keeps "$pr/$proto" as two separate spans.
        def _is_path_start(pos: int) -> bool:
            """True if text[pos] looks like the start of a path component."""
            if pos >= len(text):
                return False
            c = text[pos]
            if c in '@:-' and pos + 1 < len(text) and re.match(r'[A-Za-z0-9_]', text[pos + 1]):
                return True
            if c == '/' and pos + 1 < len(text):
                nc = text[pos + 1]
                # /word  or  /.dotfile (hidden dir)
                if re.match(r'[A-Za-z0-9_]', nc):
                    return True
                if nc == '.' and pos + 2 < len(text) and re.match(r'[A-Za-z0-9_]', text[pos + 2]):
                    return True
            return False
        if _is_path_start(end):
            while end < len(text):
                c = text[end]
                if re.match(r'[A-Za-z0-9_@:-]', c):
                    end += 1
                elif c in '/.' and end + 1 < len(text) and re.match(r'[A-Za-z0-9_]', text[end + 1]):
                    end += 1
                elif c == '/' and end + 1 < len(text) and text[end + 1] == '.' and end + 2 < len(text) and re.match(r'[A-Za-z0-9_]', text[end + 2]):
                    end += 1  # /.dotfile
                else:
                    break

        out.append(f"`{prefix}{text[i:end]}`")
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
        return f'**@@green|Attention!@@** @@red|{strip_markup(content)}@@'

    color = color.lower()
    # A Markdown link [text](url) inside colored prose is not code — exclude its
    # brackets/parens from the code-like and MDX-unsafe heuristics below.
    probe = re.sub(r'\[[^\]]*\]\([^)]*\)', '', content)
    is_code_like = bool(re.search(r'[$\[\]<>{}]', probe))
    if color in SUPPORTED_COLORS and is_code_like:
        return f'`@@{color}|{content}@@`'

    is_mdx_unsafe = bool(re.search(r'[<>{}]', probe))
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

        # PMwiki "deleted" code block: {-[@ ... @]-} — a [@code@] block wrapped in
        # {-...-} deletion markup (migration notes striking out a deprecated
        # example). Emit a fenced block tagged for Expressive Code's `del` marker
        # so it renders as a struck-through code block (see global.css).
        if line.strip().startswith("{-[@"):
            code_lines = []
            rest = line.strip()[4:]
            if rest.endswith("@]-}"):
                code_lines = [rest[:-4]]
            else:
                if rest:
                    code_lines.append(rest)
                i += 1
                while i < len(lines) and not lines[i].rstrip().endswith("@]-}"):
                    code_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    code_lines.append(lines[i].rstrip()[:-4])
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            if code_lines:
                lang = detect_language(code_lines)
                # Prepend a comment so the deprecation is clear even where the
                # strikethrough isn't rendered (plain Markdown on github.com).
                # Strike only the code lines (2..N+1), leaving the comment legible.
                out.append(f"```{lang} del={{2-{len(code_lines) + 1}}}")
                out.append("# this is deprecated")
                out.extend(code_lines)
                out.append("```")
            i += 1
            continue

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
            lang = detect_language(code_lines)
            out.append(f"```{lang}")
            out.extend(code_lines)
            out.append("```")
            i += 1
            continue

        # PMwiki framed div block: >>lframe ...<< ... >><<  — a code-like boxed example
        # (e.g. a FIFO MI command). Render as a code fence; [[<<]] are line breaks.
        if re.match(r'^>>.*frame.*<<$', line.strip()):
            i += 1
            block: list[str] = []
            while i < len(lines) and lines[i].strip() != ">><<":
                block.append(lines[i])
                i += 1
            i += 1  # skip the >><< closing marker
            body_txt = "\n".join(block).replace("[[<<]]", "")
            body_txt = re.sub(r'\[=(.*?)=\]', r'\1', body_txt)  # PmWiki [=verbatim=] escape
            # A frame may already wrap a [@...@] code block (e.g. from a <pre>) — drop those markers.
            code_lines = [l for l in body_txt.split("\n")
                          if l.strip() not in ("_empty_line_", "[@", "@]")]
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            # A frame carrying PmWiki color spans (e.g. the pseudo-variable syntax
            # notation where green marks the optional fields) is formatted text, not
            # verbatim code — render the markup via the prose path instead of
            # fencing it, otherwise the %green%/'''/'' tokens show literally.
            if code_lines and re.search(
                r'%(?:red|green|blue|orange|yellow|black|white|purple|gr[ae]y)%',
                "\n".join(code_lines),
            ):
                for cl in code_lines:
                    if cl.strip():
                        out.append(convert_line(cl))
                        out.append("")
                continue
            if code_lines:
                out.append(f"```{detect_language(code_lines)}")
                out.extend(code_lines)
                out.append("```")
            continue

        # PMwiki comment div blocks: [[#commentN]]...>>message*<< ... >><<  — drop entirely
        if re.search(r'>>message', line, re.IGNORECASE) or re.match(r'^\[\[#comment\d+\]\]', line.strip()):
            while i < len(lines) and lines[i].strip() != ">><<":
                i += 1
            i += 1  # skip the >><<  closing marker too
            continue

        # PMwiki admonition div blocks: >>important<< / >>tip<< / >>warning<< ... >><<
        # Emit GitHub alert syntax (> [!TYPE]) — these render natively as callouts
        # on github.com (the fork manual), and a remark plugin turns them into
        # Starlight asides on the website (see remarkGithubAlerts.mjs).
        _ADMONITION = {"important": "IMPORTANT", "warning": "WARNING", "tip": "TIP",
                       "note": "NOTE", "caution": "CAUTION"}
        adm = re.match(r'^>>(\w+)<<$', line.strip())
        if adm and adm.group(1).lower() in _ADMONITION:
            gh_type = _ADMONITION[adm.group(1).lower()]
            i += 1
            block: list[str] = []
            while i < len(lines) and lines[i].strip() != ">><<":
                block.append(lines[i])
                i += 1
            i += 1  # skip the >><< closing marker
            while block and not block[0].strip():
                block.pop(0)
            while block and not block[-1].strip():
                block.pop()
            # A blockquote must be its own block — ensure a blank line before it.
            if out and out[-1].strip():
                out.append("")
            out.append(f"> [!{gh_type}]")
            for bl in block:
                converted = convert_line(bl)
                for sub in (converted.split("\n") if converted else [""]):
                    out.append(f"> {sub}" if sub.strip() else ">")
            out.append("")
            continue

        # Indented lines = preformatted in PMwiki (any leading space),
        # unless the line contains PmWiki inline markup (bold, links) — then it's prose continuation.
        # Also skip lines whose content (after stripping indent) is a PMwiki list item (* or #).
        if line and line[0] == ' ' and not re.search(r"'''|\[\[|''|@@", line) and not re.match(r'^\s+\*', line):
            code_lines: list[str] = []
            while i < len(lines) and lines[i] and lines[i][0] == ' ':
                code_lines.append(lines[i].lstrip(' '))
                i += 1
            # trim trailing blank lines inside the block
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            if code_lines:
                # Indented prose that's really a numbered list (e.g. "1 - description"),
                # not code — render as a Markdown list with any intro lines as prose.
                numbered = [l for l in code_lines if re.match(r'^\d+\s*[-–]\s+\S', l)]
                if len(numbered) >= 2:
                    for l in code_lines:
                        nm = re.match(r'^(\d+)\s*[-–]\s+(.*)$', l)
                        if nm:
                            out.append(f"{nm.group(1)}. {convert_inline(nm.group(2).strip())}")
                        elif l.strip():
                            out.append(convert_inline(l.strip()))
                        else:
                            out.append("")
                    out.append("")
                    continue
                lang = detect_language(code_lines)
                out.append(f"```{lang}")
                out.extend(code_lines)
                out.append("```")
            continue

        # PmWiki table attribute lines (|| attr=val ...) — no second ||, just drop
        if re.match(r'^\|\|\s*\w+=', line):
            i += 1
            continue

        # Code-comparison table: a header row (||a||b||) followed by a row whose
        # cells contain multi-line [@...@] code blocks. GFM tables can't hold those,
        # so render each column as a labeled section with its code block.
        if (line.strip().startswith("||") and "||" in line.strip()[2:]
                and i + 1 < len(lines)
                and re.match(r'^\|\|\s*(?:%[^%\n]+%\s*)?\[@\s*$', lines[i + 1].strip())):
            headers = [c for c in (
                cell.strip().strip("'").strip()
                for cell in line.strip().strip("|").split("||")
            ) if c]
            i += 1
            block: list[str] = []
            while i < len(lines):
                block.append(lines[i])
                if re.search(r'@\]\s*\|\|\s*$', lines[i]):  # row end
                    i += 1
                    break
                i += 1
            out.extend(render_code_comparison(headers, block))
            continue

        # Table block: collect consecutive ||...|| rows and render with separator
        if line.strip().startswith("||") and "||" in line.strip()[2:]:
            # Look ahead over the contiguous non-blank region: if a cell embeds a
            # multi-line [@...@] code block, GFM can't hold it — render row-by-row.
            region: list[str] = []
            j = i
            while j < len(lines) and lines[j].strip():
                region.append(lines[j])
                j += 1
            if any('[@' in r for r in region) and any('@]||' in r for r in region):
                out.extend(render_table_with_code(region))
                i = j
                if i < len(lines) and lines[i].strip():
                    out.append("")
                continue
            rows: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("||"):
                rows.append(lines[i])
                i += 1
            out.extend(render_table(rows))
            # Always separate a table from following content with a blank line, so a
            # caption/marker line (which may contain '|') isn't parsed as another row.
            if i < len(lines) and lines[i].strip():
                out.append("")
            continue

        # NOTE: on its own line followed by bullets — a Note callout with a list body.
        if re.match(r'^NOTE:\s*$', line.strip(), re.IGNORECASE):
            i += 1
            bullet_lines: list[str] = []
            while i < len(lines) and re.match(r'^[*#]', lines[i].strip()):
                bullet_lines.append(lines[i])
                i += 1
            if out and out[-1].strip():
                out.append("")
            out.append("> [!NOTE]")
            for bl in bullet_lines:
                item = convert_inline(re.sub(r'^[*#]+\s*', '', bl.strip()))
                out.append(f"> * {item}")
            out.append("")
            continue

        out.append(convert_line(line))
        i += 1

    result = "\n".join(out)
    return post_process(result)


def render_table_with_code(region: list[str]) -> list[str]:
    """Render a PMwiki table whose last cell holds a multi-line [@...@] code block.
    GFM tables can't hold multi-line code, so each row becomes a bullet list item:
    a bold label (the text cells joined with ' — ') followed by a nested fenced
    code block (indented 2 spaces so it belongs to the item). This keeps the code's
    newlines/indentation and stays editable in Keystatic's MDX editor."""
    def cells_to_label(cells: list[str]) -> str:
        label = f"**{convert_inline(cells[0])}**"
        if len(cells) > 1:
            label += " — " + " — ".join(convert_inline(c) for c in cells[1:])
        return label

    k = 0
    # Skip attribute lines (|| border=1 etc.) and the header row (first plain ||...|| row).
    while k < len(region) and re.match(r'^\|\|\s*\w+=', region[k].strip()):
        k += 1
    if k < len(region) and region[k].strip().startswith("||") and "[@" not in region[k]:
        k += 1  # header row — column meaning becomes implicit in the labels
    # Leading blank line so the list separates from any preceding caption line.
    out: list[str] = [""]
    while k < len(region):
        row = region[k]
        if not row.strip().startswith("||"):
            k += 1
            continue
        if "[@" in row:
            prefix = row.split("[@", 1)[0]
            cells = [c.strip() for c in prefix.strip().strip("|").split("||") if c.strip()]
            k += 1
            code_lines: list[str] = []
            while k < len(region) and "@]" not in region[k]:
                code_lines.append(region[k])
                k += 1
            k += 1  # skip @]|| line
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            if cells:
                out.append(f"* {cells_to_label(cells)}")
            else:
                out.append("* ")
            if code_lines:
                # Indent the fence + content 2 spaces so it nests under the bullet.
                out.append("")
                out.append(f"  ```{detect_language(code_lines)}")
                out.extend(f"  {cl}" if cl.strip() else "" for cl in code_lines)
                out.append("  ```")
            out.append("")
        else:
            # plain row without code — render as a bullet list item
            cells = [c.strip() for c in row.strip().strip("|").split("||") if c.strip()]
            if cells:
                out.append(f"* {cells_to_label(cells)}")
                out.append("")
            k += 1
    return out


def render_code_comparison(headers: list[str], block_lines: list[str]) -> list[str]:
    """Render a PMwiki side-by-side code-comparison table as a bullet list, one
    item per column: a bold label followed by a nested fenced code block. These
    are example captions, not document sections, so they stay out of the TOC and
    render consistently with render_table_with_code."""
    text = "\n".join(block_lines)
    cols = re.split(r'@\]\s*\|\|\s*\[@', text)
    out: list[str] = [""]
    for k, col in enumerate(cols):
        col = re.sub(r'^\s*\|\|\s*(?:%[^%\n]+%\s*)?\[@', '', col)
        col = re.sub(r'@\]\s*\|\|\s*$', '', col)
        col = re.sub(r'@\]\s*$', '', col)
        col = col.replace('@][@', '\n\n')
        code = col.strip('\n')
        if not code.strip():
            continue
        label = headers[k] if k < len(headers) else f"Column {k + 1}"
        lang = detect_language(code.split('\n'))
        out.append(f"* **{convert_inline(label)}**")
        out.append("")
        out.append(f"  ```{lang}")
        out.extend(f"  {cl}" if cl.strip() else "" for cl in code.split('\n'))
        out.append("  ```")
        out.append("")
    return out


def render_table(rows: list[str]) -> list[str]:
    """Render a block of PMwiki table rows as a GFM Markdown table."""
    parsed: list[list[str]] = []
    for raw in rows:
        s = raw.strip()
        if s.startswith("||"):
            s = s[2:]
        if s.endswith("||"):
            s = s[:-2]
        cells = [convert_inline(c.strip().lstrip("! ").strip()) for c in s.split("||")]
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


def gh_alert(gh_type: str, content: str) -> str:
    """Format a one-line callout as a GitHub alert blockquote (> [!TYPE] / > body).
    Wrapped in blank lines so the blockquote is its own block — renders as a native
    alert on github.com and (via remarkGithubAlerts) a Starlight aside on the site."""
    body = "\n".join(f"> {ln}" if ln.strip() else ">" for ln in content.strip().split("\n"))
    return f"\n> [!{gh_type}]\n{body}\n"


def convert_line(line: str) -> str:
    # Wiki comment signatures: !!!!![[~username]] or !!!![[~username]] → drop
    if re.match(r'^!{4,5}\s*\[\[~', line):
        return ""

    # Breadcrumb lines: !{4,5} ... -> ... → drop (page title goes in frontmatter)
    if re.match(r'^!{4,5}.*->', line):
        return ""

    # Headings: PmWiki uses fewer bangs = higher level. Count leading bangs and map
    # monotonically (! → h2, !! → h3, … capped at h6); normalize_heading_levels later
    # shifts the whole document so its shallowest heading becomes h2.
    hm = re.match(r'^(!+)\s*(.+)$', line)
    if hm:
        content = hm.group(2).strip()
        # A heading whose text is really a NOTE: is an authored misuse of heading
        # syntax — render it as a Note callout, not a section heading.
        if re.match(r'^NOTE:', content, re.IGNORECASE):
            note = content.split(":", 1)[1].strip()
            return gh_alert("NOTE", convert_inline(note))
        level = min(len(hm.group(1)) + 1, 6)
        return f"{'#' * level} {convert_inline(content, code_variables=False)}"

    if re.match(r'^-{4,}$', line.strip()):
        return "\n---\n"

    if re.match(r'^[*#]+(?!\s*$)', line):
        return convert_list_item(line)

    if line.strip().startswith("$(") and re.search(r'%[a-zA-Z]+%', line):
        return f"`{code_color_markup_to_markers(line.strip())}`"

    # Preserve standalone PMWiki anchors as source-friendly markers. The anchor
    # name is sometimes malformed: an alias pair ("memdump | mem_dump") or a name
    # with stray spaces (" event_route", "for each"). Keep the first alias and
    # turn spaces into underscores so these still yield a stable heading id.
    m = re.match(r'^\[\[#([^\]]+?)\]\]$', line.strip())
    if m:
        anchor_id = re.sub(r'\s+', '_', m.group(1).split('|')[0].strip())
        anchor_id = re.sub(r'[^\w.-]', '', anchor_id)
        if anchor_id:
            return f"@@anchor|{anchor_id}@@"
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
        return gh_alert("NOTE", convert_inline(note))
    # A line opening with a deliberately-bolded "Note" marker ('''Note''' / """Note""")
    # is a callout — render it as a Note alert.
    _q = r"(?:'''|\"\"\")"  # PmWiki bold ''' or its double-quote typo """
    # Matches '''Note''', '''NOTE:''' (colon inside bold), '''Note''':, """Note""", etc.
    nm = re.match(rf'^{_q}\s*Note\s*:?\s*{_q}\s*[:,]?\s*(.*)$', line.strip(), re.IGNORECASE)
    if nm:
        note = re.sub(r'^that\s+', '', nm.group(1).strip(), flags=re.IGNORECASE)
        return gh_alert("NOTE", convert_inline(note))
    # Indented bold-dash definition item: "'''''- term: '''''description"
    # (bold-italic wrapping a "- term:" lead-in). Render as a nested list item so
    # the surviving indentation doesn't get fenced as a code block.
    dm = re.match(r"^\s*'{4,5}\s*-\s*(.+?)\s*:\s*'{4,5}\s*(.*)$", line)
    if dm:
        return f"  * **{dm.group(1).strip()}:** {convert_inline(dm.group(2).strip())}"

    converted = convert_inline(line)
    if converted.startswith("**@@green|Attention!@@**"):
        # Obsolete/deprecated callout (from ASIDE_PHRASES) → a Warning alert.
        # Drop the "Attention!" label (the alert has its own header) and the
        # color tokens (which would render literally on github.com).
        rest = converted[len("**@@green|Attention!@@**"):].strip()
        rest = re.sub(r'@@\w+\|(.+?)@@', r'\1', rest).strip()
        return gh_alert("WARNING", rest or "This is obsolete.")
    return converted


def convert_list_item(line: str) -> str:
    depth = 0
    while line and line[0] in ("*", "#"):
        depth += 1
        line = line[1:]
    # PmWiki list-style modifier right after the markers (e.g. "#- item") — drop the
    # dash only when a space follows, so real content like "-5 dB" is preserved.
    line = re.sub(r'^[-+](?=\s)', '', line, count=1)
    line = line.lstrip()
    indent = "  " * (depth - 1)
    content = convert_inline(line)
    content = apply_module_status_badge(content)
    # A list item whose content starts with '>' or '<' (e.g. the operator-reference
    # list "> - greater", "<= - less or equal") would be misread as a blockquote /
    # HTML tag inside the item — escape the leading operator char so it stays literal.
    if content[:1] in (">", "<"):
        content = "\\" + content
    return f"{indent}* {content}"


def convert_inline(text: str, code_variables: bool = True) -> str:
    # PmWiki ''''X'''' — EXACTLY four quotes (bold ''' + a literal apostrophe each
    # side), authored to quote a syntax delimiter like { } ( ). The bold/italic
    # passes below mis-parse it into "**'`{**'", so handle it first and render the
    # delimiter as inline code. The (?<!')/(?!') guards keep it from grabbing 4 of
    # a 5-quote bold-italic run ('''''X''''') — match exactly four, not five+.
    text = re.sub(r"(?<!')''''(?!')(.+?)(?<!')''''(?!')", r"`\1`", text)
    # Source typo: ''word''' — an italic word with a stray third closing quote
    # (e.g. "''ID'' or ''PID''' (optional)"). Without this, the trailing ''' gets
    # read as an unclosed bold and mangles the rest of the line. Restricted to a
    # single \w+ token, not preceded by another quote (so genuine '''bold''' is
    # untouched) and not followed by a word char or quote (so possessives like
    # ''m4'''s and 4+ quote runs are left for their own handling).
    text = re.sub(r"(?<!')''(\w+)'''(?![\w'])", r"*\1*", text)
    # Bold / italic — strip inner whitespace so e.g. "''' text'''" → "**text**"
    # (Markdown bold/italic can't start or end with whitespace).
    def _bold(m):
        inner = m.group(1)
        content = inner.strip()
        if not content:
            return ''
        # Move surrounding whitespace outside the markers so word boundaries are kept
        leading  = ' ' if inner[0]  == ' ' else ''
        trailing = ' ' if inner[-1] == ' ' else ''
        return f"{leading}**{content}**{trailing}"
    text = re.sub(r"'''(.+?)'''", _bold, text)
    # Common typo: """word""" (double quotes) instead of PmWiki bold '''word'''
    text = re.sub(r'"""(.+?)"""', _bold, text)
    # Unclosed ''' with mismatched closing " (typo: '''word" instead of '''word''')
    text = re.sub(r"'''(\w[^'\"]*?)\"", r'**\1**', text)
    # Unclosed ''' with no closing at all — grab to end of line
    text = re.sub(r"'''([^']+)$", r"**\1**", text)
    def _italic(m):
        inner = m.group(1)
        content = inner.strip()
        if not content:
            return ''
        leading  = ' ' if inner[0]  == ' ' else ''
        trailing = ' ' if inner[-1] == ' ' else ''
        return f"{leading}*{content}*{trailing}"
    text = re.sub(r"''(.+?)''", _italic, text)

    # Drop link-icon anchors and links to comment anchors (#commentN).
    # The chain glyph appears either as the entity (&#x1F517;) or — after
    # decode_pmwiki_text's html.unescape — as the literal emoji 🔗 (U+1F517).
    # The anchor segment may carry trailing spaces, stray wikistyle markup, or
    # even an inner '|' (e.g. "[[#listen %25red%25|...]]", "[[#memlog | mem_log|🔗]]"),
    # so match anything up to the LAST '|' before the icon.
    text = re.sub(r'\[\[#[^\]]*\|(?:&#x1F517;|\U0001F517|¶)\]\]', '', text)
    text = re.sub(r'\[\[#comment\d+\|[^\]]*\]\]', '', text)
    text = re.sub(r'\[comment\d+\]\(#comment\d+\)', '', text)  # already-converted form

    def wiki_link(m):
        page, label = m.group(1).strip(), m.group(2).strip()
        # Extra leading [ from typos like [[[url|label]] — strip them and any extra whitespace
        page = page.lstrip("[ ")
        # Fix mismatched @ monospace markers: @text@@ → @@text@@
        label = re.sub(r'^@([^@])', r'@@\1', label)
        # Escape brackets in citation-style labels (e.g. "[1]") so Markdown doesn't misparse them
        label = label.replace('[', r'\[').replace(']', r'\]')
        if page.startswith("#"):
            return f"[{label}]({page})"
        if page.startswith(("http://", "https://")):
            # Legacy module-doc links → internal. Two targets, one principle:
            #  - Manual mode: a fork-relative link to the same repo's module
            #    README (../modules/<mod>/README.md). The pinned <ver>.x is
            #    dropped so it follows the manual's own version; on github.com it
            #    resolves in-branch, and adapt_links rewrites it to the website
            #    /docs/modules/<ver>/<mod>.
            #  - Website mode (flat docs, no fork copy): the pinned <ver>.x is
            #    kept and mapped to its website slug → /docs/modules/<slug>/<mod>.
            mod_m = _MOD_DOC_RE.match(page)
            if mod_m:
                verdir, mod, anchor = mod_m.group(1), mod_m.group(2), mod_m.group(3) or ''
                if _MANUAL_LINKS:
                    return f"[{label}](../modules/{mod}/README.md{anchor})"
                return f"[{label}](/docs/modules/{_modver_to_slug(verdir)}/{mod}{anchor})"
            # opensips.org Documentation URLs → internal slugs, but only when the
            # target page actually exists locally (otherwise keep the working external URL).
            doc_m = re.match(r'https?://(?:www\.)?opensips\.org/Documentation/(.+)', page, re.IGNORECASE)
            if doc_m:
                tail = doc_m.group(1)
                # Strip PMwiki query params (e.g. ?action=edit) before processing
                tail = re.sub(r'\?[^#]*', '', tail)
                path_part, _, anchor = tail.partition('#')
                seg = path_part.rstrip('/').split('/')[-1]
                # Preserve any anchor (including PMwiki auto-generated #tocN). For
                # links that resolve to a real on-site page below, resolve-toc-anchors
                # rewrites #tocN to the target heading's id at build (out-of-range
                # anchors are dropped there). Keeping it matches the page-name handler.
                anchor_sfx = f"#{anchor}" if anchor else ''
                # Old version-suffixed manual page (…/Script-CoreVar-3-6) → the new
                # /docs/manual/<ver>/<page>. Manual mode (fork/github) uses the full
                # URL; adapt_links strips the origin for the on-site build.
                mp = _manual_page_ref(seg)
                if mp:
                    pg, slug = mp
                    url = f"/docs/manual/{slug}/{pg}{anchor_sfx}"
                    return f"[{label}]({SITE_URL + url if _MANUAL_LINKS else url})"
                # Bare manual page (…/Generating-Configs, …/Script-CoreFunctions):
                # the flat PmWiki copy is an empty stub, so route to the devel
                # manual. The old #tocN numbered the old page and does not match
                # devel's ordering, so drop it — land on the page, not a wrong
                # section.
                man_stem = seg.lower()
                if man_stem in _MANUAL_PAGES:
                    url = f"/docs/manual/devel/{man_stem}"
                    return f"[{label}]({SITE_URL + url if _MANUAL_LINKS else url})"
                stem = seg.lower().replace('-', '').replace('_', '')
                if stem in _SLUG_MAP:
                    slug = _SLUG_MAP[stem]
                    return f"[{label}]({(SITE_URL + slug if _MANUAL_LINKS else slug) + anchor_sfx})"
            return f"[{label}]({page})"
        return f"[{label}]({page_to_slug(page)})"
    # Label may contain single ']' (e.g. citation refs like "[1]"), just not "]]".
    text = re.sub(r'\[\[([^\]|]+)\|((?:[^\]]|\](?!\]))+)\]\]', wiki_link, text)

    def wiki_link_no_label(m):
        page = m.group(1).strip()
        # PmWiki navigation anchors and bare section anchors — drop
        if page in ("<<", ">>", "<"):
            return ""
        if page.startswith("#"):
            return ""
        if page.startswith(("http://", "https://")):
            # MDX doesn't support <url> autolinks (parsed as JSX) — use [url](url)
            return f"[{page}]({page})"
        return f"[{page}]({page_to_slug(page)})"
    text = re.sub(r'\[\[([^\]]+)\]\]', wiki_link_no_label, text)

    # PmWiki inserted/deleted markup {+text+} / {-text-} — unwrap, keep content.
    # Must run before color-span handling so the braces don't read as "code-like".
    text = re.sub(r'\{\+(.+?)\+\}', r'\1', text)
    text = re.sub(r'\{-(.+?)-\}', r'\1', text)

    # Inline [@...@] code spans (not [@@...@@] which is a link label with @@ monospace)
    text = re.sub(r'\[@(?!@)\s*(.*?)\s*@\]', lambda m: f'`{m.group(1)}`', text)

    # PMwiki @@text@@ monospace → backtick code — must run BEFORE color spans so
    # the @@color|...@@ markers emitted by color_span_to_mdx aren't accidentally matched.
    # Content may contain a single internal '@' (e.g. @@911@VSPdomain@@); match
    # non-greedily up to the next '@@', and strip emphasis markers left inside the code.
    def _mono(m):
        inner = re.sub(r'\*+(.+?)\*+', r'\1', m.group(1))  # drop **/* emphasis inside code
        return f'`{inner}`'
    text = re.sub(r'@@(?!(?:red|green|blue|orange|yellow)\|)((?:[^@]|@(?!@))+?)@@', _mono, text)
    # Also handle @text@@ (single @ open, typo) and @@text@ (single @ close, typo)
    text = re.sub(r'(?<![`@])@([^@\s`]+)@@', r'`\1`', text)
    text = re.sub(r'@@([^@\s`]+)@(?!@)', r'`\1`', text)
    # Single @text@ monospace (typo for @@text@@). Bounded by non-word chars so it
    # won't match emails (user@host) or "911@VSPdomain".
    text = re.sub(r'(?<![\w@`])@([^@\s`]+)@(?![\w@`])', r'`\1`', text)

    # Normalize hex color wikistyles to named colors before span processing.
    # e.g. %color=#ff7f00% → %orange%
    _HEX_TO_COLOR = {
        r'#ff7f00': 'orange', r'#ffa500': 'orange',
        r'#ff0000': 'red',
        r'#00[89a-f][0-9a-f]00': None,  # placeholder — handled below via regex
    }
    def _hex_color(m):
        h = m.group(1).lower()
        if h in ('#ff7f00', '#ffa500'):
            return '%orange%'
        if h in ('#ff0000', '#cc0000', '#dc143c'):
            return '%red%'
        if h in ('#0000ff', '#0000cc', '#00f'):
            return '%blue%'
        if h in ('#008000', '#006400', '#00cc00'):
            return '%green%'
        return ''  # unknown hex — strip the marker
    text = re.sub(r'%color=(#[0-9a-fA-F]{3,8})%', _hex_color, text)

    # Color spans %color%text%%
    def replace_color(m):
        return color_span_to_mdx(m.group(1), m.group(2))
    text = re.sub(r'%([a-zA-Z]+)%(.*?)%%', replace_color, text)

    # %color%text%black% — color reset via a second named-color marker (no %% closer).
    # e.g. "%orange% Ex: %black%'''bold text'''" → @@orange| Ex: @@'''bold text'''
    text = re.sub(r'%([a-zA-Z]+)%([^%\n]*)%(?:black|white|normal)%', replace_color, text)

    # Unclosed PMWiki color spans at the end of a line, e.g. "%green%$ru".
    text = re.sub(r'%([a-zA-Z]+)%([^%\n]+)$', replace_color, text, flags=re.MULTILINE)

    # PmWiki wikistyle directives — drop the wrapper. Matched precisely (known
    # keywords / attr=value / #hexcolor) so literal sequences like printf "%e.%t"
    # or strftime "%Y" or shell flags "%P -u%" are left untouched.
    _wikistyle = (
        r'%(?:'
        r'(?:red|green|blue|orange|yellow|black|white|purple|gr[ae]y)'   # color names
        r'|(?:block|center|right|left|item|list|rfloat|lfloat|rframe|lframe|frame|thumb)(?:\s[^%\n]*)?'  # layout/float
        r'|[a-zA-Z]+=[^%\n]+'                                            # attr=value
        r'|#[0-9a-fA-F]{3,8}'                                            # hex color
        r')%'
    )
    text = re.sub(_wikistyle + r'(.*?)%%', r'\1', text)
    text = re.sub(_wikistyle, '', text)
    text = re.sub(r'%%', '', text)

    # Bare image URLs → local Markdown images. Skip URLs that are already a
    # Markdown link target (preceded by '(' or ']'). Images are mirrored under
    # public/images/docs/tutorials/ keyed by basename (see download step).
    def _image(m):
        basename = m.group(0).rsplit('/', 1)[-1]
        alt = re.sub(r'[-_]+', ' ', basename.rsplit('.', 1)[0]).strip()
        return f"![{alt}](/images/docs/tutorials/{basename})"
    text = re.sub(r'(?<![(\[])https?://[^\s\]\)]+\.(?:png|jpe?g|gif)\b', _image, text, flags=re.I)

    # Strip a stray trailing single pipe left over from PMwiki float-cell layout
    # (e.g. "%rfloat width=400px % http://…png | ''' '''" → "…png |"). Skip lines
    # that start with a pipe (Markdown table rows) so table borders aren't touched.
    text = re.sub(r'(?m)^(?![ \t]*\|)(.*[^|\s])[ \t]+\|[ \t]*$', r'\1', text)

    # PmWiki page variables {$VarName} → drop (whole line if variable was primary content)
    text = re.sub(r'^[^{]*\{\$\w+\}[^{]*$', '', text)
    text = re.sub(r'\{\$\w+\}', '', text)

    # Inline PMwiki directives (:name:) or (:name args:) → drop
    text = re.sub(r'\(:[^:)]+:\)', '', text)
    # Inline CSS div markers >>class<< → drop
    text = re.sub(r'>>[^<]*<<', '', text)

    text = re.sub(r'\[\[#[\w.-]+\]\]', '', text)
    # PMwiki big-text markup: [+text+] (bigger) and [++text++] (biggest). Match
    # one-or-more '+' on each side so [++Function++] fully unwraps to "Function"
    # (not "+Function+").
    text = re.sub(r'\[\++(.+?)\++\]', r'\1', text)
    text = re.sub(r'\\\\$', '  ', text)
    if code_variables:
        text = code_variable_tokens(text)
    return text


def detect_language(lines: list[str]) -> str:
    content = "\n".join(lines)
    first = next((l.strip() for l in lines if l.strip()), "")

    # Shebang
    if first.startswith("#!"):
        if any(x in first for x in ("bash", "/sh")):
            return "bash"
        if "python" in first:
            return "python"
        if "perl" in first:
            return "perl"
        if "php" in first:
            return "php"

    # PHP open tag
    if first.startswith("<?php") or "<?php" in content:
        return "php"

    # SQL — DML/DDL keyword followed by a SQL-typical token (not just any word)
    if re.search(r'^\s*(SELECT\s+[\w*]|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|CREATE\s+(TABLE|DATABASE|INDEX)|DROP\s+(TABLE|DATABASE)|ALTER\s+TABLE|GRANT\s+\w)', content, re.IGNORECASE | re.MULTILINE):
        return "sql"

    # C — include or type-heavy signatures
    if re.search(r'^#include\s*[<"]', content, re.MULTILINE):
        return "c"
    if re.search(r'\b(typedef|struct|enum)\s+\w+', content):
        return "c"

    # OpenSIPS script/config — routing keywords or global config params
    if re.search(r'\b(loadmodule|modparam|request_route|onreply_route|failure_route|branch_route|local_route|startup_route|timer_route|route\s*[\[{])\b', content):
        return "c"  # closest Shiki grammar for OpenSIPS syntax
    if re.search(r'^(listen|children|fork|debug|log_stderror|disable_core_dump|auto_aliases|mpath)\s*=', content, re.MULTILINE):
        return "c"

    # Perl
    if re.search(r'\b(use\s+strict|use\s+warnings|sub\s+\w+\s*\{|my\s+\$\w+)', content):
        return "perl"

    # Shell — prompt lines, common CLI tools, or shell constructs
    if re.search(r'^(\$\s|\#\s)', content, re.MULTILINE):
        return "bash"
    if re.search(r'\b(grep|awk|sed|curl|wget|chmod|chown|systemctl|apt-get|yum|make|cmake|ngrep|tshark|tcpdump|opensips-cli|opensipsctl)\b', content):
        return "bash"
    if re.search(r'^(if|for|while|case|function)\s', content, re.MULTILINE):
        return "bash"

    return "text"


def load_slug_map(content_dir: Path) -> None:
    """Scan content_dir for doc pages and map normalized stem → actual slug.

    Indexes both .md and .mdx (the /documentation pages are .md), but skips the
    modules/ and manual/ subtrees — those use their own per-version link schemes
    and would otherwise pollute the documentation stem namespace."""
    for path in content_dir.rglob("*"):
        if path.suffix not in (".md", ".mdx"):
            continue
        rel = path.relative_to(content_dir)
        # Skip the modules/ and manual/ subtrees (any depth) — they use their own
        # per-version link schemes and would pollute the documentation namespace.
        if "modules" in rel.parts or "manual" in rel.parts:
            continue
        slug = "/" + str(rel.with_suffix("")).replace("\\", "/")
        stem_norm = path.stem.lower().replace("-", "").replace("_", "")
        _SLUG_MAP[stem_norm] = slug


def load_redirects(wiki_dir: Path) -> None:
    """Scan wiki_dir for (:redirect Target:) pages and populate _REDIRECTS."""
    for f in wiki_dir.iterdir():
        if not f.is_file() or "." not in f.name:
            continue
        meta = parse_pmwiki_file(f)
        text = decode_pmwiki_text(meta.get("text", ""))
        m = re.match(r'\(:redirect\s+(\S+?)[\s:]', text)
        if m:
            target = m.group(1).replace("/", ".")
            _REDIRECTS[f.name.lower().replace("_", "")] = target


def _manual_link_key(page: str) -> str:
    """Normalize a wiki link target to the key used in _MANUAL_LINKS:
    last path/namespace segment, lowercased, hyphens/underscores removed.
    e.g. 'Documentation/Install-Download-4-1' -> 'installdownload41'."""
    base = page.partition("#")[0].strip()
    seg = re.split(r"[./]", base)[-1]
    return seg.lower().replace("-", "").replace("_", "")


def page_to_slug(page: str) -> str:
    # Manual mode: in-manual references resolve to sibling .md files (relative
    # links), so the converted manual is self-contained inside the repo docs/.
    if _MANUAL_LINKS:
        key = _manual_link_key(page)
        if key in _MANUAL_LINKS:
            anchor = page.partition("#")[2]
            return _MANUAL_LINKS[key] + (f"#{anchor}" if anchor else "")
    page = _REDIRECTS.get(page.lower().replace("_", ""), page)
    # Old manual URLs used a version suffix (Documentation.Script-CoreVar-3-6);
    # the manual now lives at /docs/manual/3-6/script-corevar. Route such refs
    # there. Manual mode (fork/github) emits the full URL; adapt_links strips the
    # origin for the on-site build.
    base, _, anchor = page.partition("#")
    # The legacy Documentation hub page (Documentation.Index / the namespace root)
    # was removed; the manual root now serves as the documentation landing. Route
    # any reference to it — dropping the old #tocN section anchor, which has no
    # equivalent there — to the devel manual.
    if base.lower() in ("documentation.index", "documentation",
                        "documentation.documentation", "documentation.homepage"):
        result = "/docs/manual/devel"
        return SITE_URL + result if _MANUAL_LINKS else result
    mp = _manual_page_ref(re.split(r"[./]", base)[-1])
    if mp:
        pg, slug = mp
        result = f"/docs/manual/{slug}/{pg}" + (f"#{anchor}" if anchor else "")
        return SITE_URL + result if _MANUAL_LINKS else result
    # A bare (un-versioned) reference whose page is a manual page — e.g.
    # Documentation.Script-CoreFunctions. The old flat PmWiki copies of these are
    # empty stubs; the canonical content lives in the manual, so route to the
    # devel (latest) manual. The old #tocN anchor numbered the *old* page's
    # headings and does not correspond to devel's ordering, so it is dropped —
    # the link lands on the correct page rather than a possibly-wrong section.
    man_stem = re.split(r"[./]", base)[-1].lower()
    if man_stem in _MANUAL_PAGES:
        result = f"/docs/manual/devel/{man_stem}"
        return SITE_URL + result if _MANUAL_LINKS else result
    # Derive the stem from the page name (strip namespace, normalize)
    stem = page.split(".")[-1].lower().replace("-", "").replace("_", "")
    if stem in _SLUG_MAP:
        result = _SLUG_MAP[stem]
    else:
        # Fallback for pages not found locally. The Documentation namespace now
        # lives flat under /docs/, so map Documentation.X / Documentation/X →
        # /docs/x (these are usually broken cross-refs either way).
        parts = re.split(r"[./]", page, 1)
        if parts[0].lower() == "documentation" and len(parts) > 1:
            result = "/docs/" + parts[1].lower()
        else:
            # Other namespaces (About, Resources, …) only ever existed on the old
            # PMwiki website — keep them as external opensips.org links (case
            # preserved), don't fabricate an internal /about/… route.
            return "https://www.opensips.org/" + page.replace(".", "/")
    # `result` is a root-relative flat-page route (/docs/…). In the MANUAL — which
    # also renders on github.com from the fork, where these flat pages don't exist
    # — make it absolute so the link works there too. adapt_links strips the
    # origin back off for the on-site build.
    if _MANUAL_LINKS and result.startswith("/"):
        return SITE_URL + result
    return result


# ---------------------------------------------------------------------------
# MDX safety pass — wrap dangerous chars in inline code instead of escaping
# ---------------------------------------------------------------------------

_SAFE_HTML_TAGS = {'span', 'strong', 'em', 'a', 'br', 'code', 'aside', 'badge'}


def normalize_heading_levels(text: str) -> str:
    """Ensure no heading skips more than one level down, and shift all headings
    up so the minimum heading level in the document is always h2."""
    lines = text.split('\n')
    in_fence_scan = False
    levels = []
    for line in lines:
        if line.lstrip().startswith('```'):
            in_fence_scan = not in_fence_scan
        if in_fence_scan:
            continue
        m = re.match(r'^(#{2,6})\s+', line)
        if m:
            levels.append(len(m.group(1)))
    if not levels:
        return text
    min_level = min(levels)
    # Shift: if min heading is h3 or deeper, promote all headings so min → h2
    shift = min_level - 2
    out = []
    current = 1
    in_fence = False
    for line in lines:
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
        if in_fence:
            out.append(line)
            continue
        m = re.match(r'^(#{2,6})\s+(.+)', line)
        if m:
            level = len(m.group(1)) - shift
            level = max(level, 2)  # never go above h2
            if level > current + 1:
                level = current + 1
            current = level
            out.append('#' * level + ' ' + m.group(2))
        else:
            out.append(line)
    return '\n'.join(out)


def post_process(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    # "Table:" captions precede labeled code blocks / lists, not real tables, so
    # drop the "Table:" prefix and color the descriptive caption itself instead.
    #   @@orange|Table:@@**caption**     →  @@orange|**caption**@@
    text = re.sub(
        r'@@(red|green|blue|orange|yellow)\|\s*Table:\s*@@\s*(\*\*.+?\*\*)',
        r'@@\1|\2@@',
        text,
    )
    #   Table: @@green|**caption**@@     →  @@green|**caption**@@   (plain prefix)
    text = re.sub(
        r'^[ \t]*Table:\s*(@@(?:red|green|blue|orange|yellow)\|\*\*.+?\*\*@@)[ \t]*$',
        r'\1',
        text,
        flags=re.MULTILINE,
    )
    text = normalize_heading_levels(text)
    text = mdx_safety_pass(text).strip()
    # Resolve anchors AFTER the MDX-safety pass so the heading-id '{#id}' suffix
    # (and folded anchors) aren't wrapped in backticks as "unsafe" braces.
    text = resolve_anchors(text)
    text = infer_missing_heading_anchors(text)
    # Drop a leading horizontal rule (PmWiki '----' separator under the breadcrumb)
    text = re.sub(r'^-{3,}\s*\n+', '', text)
    # Drop a trailing empty Comments section (PMwiki user comments are stripped but
    # the heading survives). Optionally preceded by a horizontal rule.
    text = re.sub(r'(\n---\n)?\n#{1,6} Comments\s*$', '', text)
    # Drop trailing horizontal rules left over from PMwiki page-footer separators.
    text = re.sub(r'\n+---\s*$', '', text)
    return text.strip()


def plain_markdown_text(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'@@(?:red|green|blue|orange|yellow)\|(.+?)@@', r'\1', text)
    text = re.sub(r'[*_~]+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalized_heading_key(text: str) -> str:
    text = plain_markdown_text(text).lower()
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def resolve_anchors(text: str) -> str:
    """Resolve standalone PMWiki anchor markers into the modules-style anchor
    format (matching docbook_to_md.py):

      - '@@anchor|id@@' immediately before a heading  → '{#id}' suffix on that
        heading (rendered as the heading id by remark-heading-id).
      - any other standalone '@@anchor|id@@'          → dropped entirely
        (no <span> is emitted).
    """
    lines = text.split('\n')
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = re.match(r'^@@anchor\|([\w.-]+)@@$', lines[i].strip())
        if m:
            anchor_id = m.group(1)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            hm = re.match(r'^(#{2,6})\s+(.+?)\s*$', lines[j]) if j < len(lines) else None
            if hm and '{#' not in lines[j]:
                lines[j] = f"{hm.group(1)} {hm.group(2)} {{#{anchor_id}}}"
            # Drop the marker line either way (folded into the heading, or discarded).
            i += 1
            continue
        out.append(lines[i])
        i += 1
    return '\n'.join(out)


def infer_missing_heading_anchors(text: str) -> str:
    """Attach old anchor ids when a page links to a matching heading.

    Some PMWiki pages link to an anchor in prose (for example #varesc) but
    don't include a standalone [[#varesc]] marker before the actual heading.
    Matching the link label to a later heading preserves those old URLs without
    requiring hand edits in the generated MDX.
    """
    lines = text.split("\n")
    link_targets: dict[str, str | None] = {}
    in_fence = False

    for line in lines:
        if re.match(r'^\s*```', line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for label, anchor_id in re.findall(r'\[([^\]]+)\]\(#([\w.-]+)\)', line):
            key = normalized_heading_key(label)
            if not key:
                continue
            if key in link_targets and link_targets[key] != anchor_id:
                link_targets[key] = None
            else:
                link_targets[key] = anchor_id

    out: list[str] = []
    in_fence = False
    for line in lines:
        if re.match(r'^\s*```', line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue

        heading = re.match(r'^(#{2,6})\s+(.+?)\s*$', line)
        if heading and '{#' not in line:
            key = normalized_heading_key(heading.group(2))
            anchor_id = link_targets.get(key)
            if anchor_id:
                out.append(f"{heading.group(1)} {heading.group(2)} {{#{anchor_id}}}")
                continue

        out.append(line)

    return "\n".join(out)


def mdx_safety_pass(text: str) -> str:
    """Detect indented-code blocks, fence them, then wrap unsafe chars in backticks
    in prose (outside any fenced block)."""
    lines = text.split("\n")
    fenced: list[str] = []
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^\s*```', line):
            fenced.append(line)
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            fenced.append(line)
            i += 1
            continue
        if line.startswith('    ') and line.strip() and not re.match(r'^\s*[-*]|\s*\d+\.', line):
            block: list[str] = []
            while i < len(lines) and (re.match(r'^    ', lines[i]) or lines[i].strip() == ""):
                block.append(lines[i])
                i += 1
            trailing: list[str] = []
            while block and block[-1].strip() == "":
                trailing.insert(0, block.pop())
            if block:
                stripped = [bl[4:] for bl in block]
                lang = detect_language(stripped)
                fenced.append(f"```{lang}")
                fenced.extend(stripped)
                fenced.append("```")
            fenced.extend(trailing)
            continue
        fenced.append(line)
        i += 1

    out: list[str] = []
    in_fence = False
    for line in fenced:
        if re.match(r'^\s*```', line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        # Don't wrap heading text in inline code — headings shouldn't render as
        # code (e.g. transformation names like "### {s.len}"). The output is
        # Markdown (.md), so braces/angles in a heading are literal and safe.
        if re.match(r'^#{1,6}\s', line):
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

        # Matched {...} pairs. Empty braces (e.g. config markers like "authenticate{}")
        # are prose — escape them as literal so they stay inline with surrounding text.
        # Braces with content are code-like → wrap in inline code.
        def _brace(m):
            inner = m.group(1)
            return r'\{\}' if inner.strip() == '' else f'`{{{inner}}}`'
        seg = re.sub(r'\{([^{}]*)\}', _brace, seg)
        # Any remaining lone braces are still MDX expression delimiters (skip \-escaped).
        seg = re.sub(r'(?<![`\\])([{}])(?!`)', r'`\1`', seg)

        # <…> patterns: leave Markdown autolinks (http/mailto) and known HTML tags;
        # wrap protocol-style or unknown bare tags in backticks.
        def wrap_lt(m):
            inner = m.group(1)
            stripped = inner.lstrip('/').split(' ')[0].split(':')[0]
            # <url> autolinks: MDX parses these as JSX and fails — emit [url](url)
            if re.match(r'(?:https?|ftp)://', inner, re.I):
                return f'[{inner}]({inner})'
            if re.match(r'mailto:', inner, re.I):
                return f'[{inner[7:]}]({inner})'
            if stripped.lower() in _SAFE_HTML_TAGS:
                return m.group(0)
            return f'`<{inner}>`'
        seg = re.sub(r'<(/?[A-Za-z][A-Za-z0-9_.:@/-]*)>', wrap_lt, seg)
        # Tags with attributes (e.g. <value type="uri">) — wrap in backticks
        seg = re.sub(r'<([A-Za-z][A-Za-z0-9_]*)\s+[^>]+>', lambda m: f'`{m.group(0)}`', seg)
        # <-text navigation patterns in link labels — drop (e.g. [<-Back](url))
        seg = re.sub(r'\[<-[^\]]*\]\([^)]*\)', '', seg)
        # <-> and <- contain a raw < that triggers JSX parsing in MDX.
        # Replace with Unicode arrow characters so they render as plain text.
        seg = seg.replace('<->', '↔')
        seg = re.sub(r'<-(?!>)', '←', seg)
        # <> and </> are MDX fragment syntax — wrap in backticks
        seg = re.sub(r'</?>', lambda m: f'`{m.group(0)}`', seg)

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
        if para.startswith(('#', '```', '|', '<', '-', '*', '!', '>', '[', '`', ':')):
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


# Author attribution line, e.g. " **by Liviu Chircu**", "**written by ...**", or
# "**Author: Liviu Chircu <liviu@opensips.org>**" (the leading "%block ...%" wikistyle
# is already stripped during conversion).
_AUTHOR_LINE_RE = re.compile(r'^\s*\*\*\s*(?:author:.*|(?:written\s+)?by\b.*)\*\*\s*$', re.IGNORECASE)


def _normalize_author(line: str) -> str:
    """Turn a raw author attribution line into a consistent 'by <name>' string."""
    text = line.strip().strip('*').strip()
    text = text.replace('`', '')                 # drop inline-code backticks
    text = re.sub(r'<[^>]*>', '', text)           # drop <email> addresses
    text = re.sub(r'^(?:author:\s*|written\s+by\s+|by\s+)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text).strip()
    return f"by {text}" if text else ""


def extract_subtitle(body: str):
    """Detect the PmWiki tutorial pattern where the page opens with a descriptive
    heading immediately followed by an author attribution line. Returns
    (subtitle_text, author_text, body) with the heading, author line, and any
    immediately-following horizontal rule stripped from the body. Returns
    (None, None, body) when the pattern is not matched.

    Only the very first content heading qualifies, and only when the next
    non-blank line is an author attribution — so ordinary pages are untouched.
    """
    lines = body.split('\n')
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return None, None, body
    m = re.match(r'^#{2,6}\s+(.+)$', lines[i])
    if not m:
        return None, None, body
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    if j >= len(lines) or not _AUTHOR_LINE_RE.match(lines[j]):
        return None, None, body
    subtitle = m.group(1).strip()
    author = _normalize_author(lines[j])  # consistent "by <name>"
    # Drop the heading + author lines, then any leading blank lines and one
    # leftover horizontal-rule separator that used to sit under the author.
    rest = lines[:i] + lines[j + 1:]
    k = 0
    while k < len(rest) and not rest[k].strip():
        k += 1
    if k < len(rest) and re.match(r'^-{3,}$', rest[k].strip()):
        k += 1
        while k < len(rest) and not rest[k].strip():
            k += 1
    rest = rest[k:]
    return subtitle, author, '\n'.join(rest)


def strip_redundant_title_heading(body: str, title: str) -> str:
    """Drop a leading body heading that merely repeats the page title (optionally
    with an 'OpenSIPS ' prefix), e.g. title 'Presence' with a body opening
    '## OpenSIPS Presence'. Such a heading just duplicates the rendered page
    title sitting right above it. Returns the body unchanged when no such
    heading is present. Only the very first content heading is considered.
    """
    lines = body.split('\n')
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return body
    m = re.match(r'^#{2,6}\s+(.+)$', lines[i])
    if not m:
        return body
    heading = m.group(1).strip().lower()
    tl = title.strip().lower()
    if heading not in (tl, 'opensips ' + tl):
        return body
    rest = lines[i + 1:]
    k = 0
    while k < len(rest) and not rest[k].strip():
        k += 1
    return '\n'.join(rest[k:])


def yaml_quote(text: str) -> str:
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')


def extract_title(decoded_text: str, fallback: str) -> str:
    """Pull the page title from the first !!!! or !!!!! breadcrumb line.

    Breadcrumb format: '!!!! Documentation -> Subsection -> Page Title'
    Uses rsplit so nested paths return only the final segment.
    Ignores wiki comment signatures like '!!!!![[~username]] &mdash; ...'
    """
    for line in decoded_text.lstrip("\n").split("\n"):
        if re.match(r'^!{4,5}', line):
            text = re.sub(r'^!+', '', line).strip()
            if "->" in text:
                return _clean_title(text.rsplit("->", 1)[1].strip())
    return fallback


def _clean_title(text: str) -> str:
    """Strip wiki markup from a breadcrumb title segment, leaving plain text."""
    text = re.sub(r'\[\[[^\]|]*\|\s*([^\]]+?)\s*\]\]', r'\1', text)  # [[url|label]] → label
    text = re.sub(r'\[\[\s*([^\]]+?)\s*\]\]', r'\1', text)           # [[label]] → label
    text = re.sub(r'\{[+-](.+?)[+-]\}', r'\1', text)                 # {+ins+}/{-del-} → text
    text = text.replace("'''", "").replace("''", "")                # bold/italic markers
    return re.sub(r'\s+', ' ', text).strip()


def extract_title_link(decoded_text: str):
    """If the breadcrumb's title segment embeds an external link, return
    (label, url) so it can be preserved as a clickable subtitle. Else (None, None)."""
    for line in decoded_text.lstrip("\n").split("\n"):
        if re.match(r'^!{4,5}', line):
            text = re.sub(r'^!+', '', line).strip()
            if "->" not in text:
                return None, None
            seg = text.rsplit("->", 1)[1].strip()
            m = re.search(r'\[\[\s*([^\]|]+?)\s*\|\s*(.+?)\s*\]\]', seg)
            if m and m.group(1).strip().startswith(("http://", "https://")):
                url = m.group(1).strip()
                label = re.sub(r'\{[+-](.+?)[+-]\}', r'\1', m.group(2))
                label = label.replace("'''", "").replace("''", "").strip()
                return label, url
            return None, None
    return None, None


def convert_file(src: Path, dst: Path):
    meta = parse_pmwiki_file(src)
    raw_text = meta.get("text", "")
    decoded = decode_pmwiki_text(raw_text)
    body = pmwiki_to_mdx(decoded)

    title = extract_title(decoded, src.stem)
    subtitle, author, body = extract_subtitle(body)
    # Re-normalize: removing the subtitle heading — or a redundant leading heading
    # that just repeats the title — can leave the body's shallowest heading at h3,
    # which would render as "0.1". Re-shift so it starts at h2.
    if subtitle is not None:
        body = normalize_heading_levels(body)
    else:
        stripped = strip_redundant_title_heading(body, title)
        if stripped != body:
            body = normalize_heading_levels(stripped)
    description = extract_description(body)

    fm = ["---", f'title: "{yaml_quote(title)}"']
    # Emit subtitle only when it adds information beyond the title.
    if subtitle and subtitle.strip().lower() != title.strip().lower():
        fm.append(f'subtitle: "{yaml_quote(subtitle)}"')
    elif not subtitle:
        # No author subtitle — if the breadcrumb title embedded a link, keep it
        # as a clickable subtitle so the module-doc reference isn't lost.
        link_label, link_url = extract_title_link(decoded)
        if link_label and link_url:
            # A legacy module-doc URL here → internal website route, like body links.
            link_url = _module_doc_web(link_url) or link_url
            fm.append(f'subtitle: "{yaml_quote(link_label)}"')
            fm.append(f'subtitleHref: "{yaml_quote(link_url)}"')
    if author:
        fm.append(f'author: "{yaml_quote(author)}"')
    fm.append(f'description: "{yaml_quote(description)}"')
    fm.append("---")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(fm) + "\n\n" + body + "\n", encoding="utf-8")
    print(f"  {src.name} → {dst}")


def manual_filename(wiki_name: str, ver: str) -> str:
    """'Documentation.Install-Download-4-1' → 'Install-Download.md'. The version
    suffix is dropped because each opensips branch carries only its own manual."""
    n = wiki_name
    if n.startswith("Documentation."):
        n = n[len("Documentation."):]
    if n.endswith("-" + ver):
        n = n[: -(len(ver) + 1)]
    return n + ".md"


def manual_subpages(wiki_dir: Path, ver: str) -> list[str]:
    """Ordered list of existing wiki page names linked from the manual index.
    Unqualified links default to the 'Documentation' group (PmWiki semantics)."""
    meta = parse_pmwiki_file(wiki_dir / f"Documentation.Manual-{ver}")
    text = decode_pmwiki_text(meta.get("text", ""))
    pages: list[str] = []
    for raw in re.findall(r"\[\[\s*([A-Za-z0-9._/ -]+?)(?:\s*\|[^\]]+)?\]\]", text):
        name = raw.strip().replace("/", ".").rstrip(".")
        if "." not in name:
            name = "Documentation." + name
        if name.startswith("Documentation.Manuals"):
            continue  # breadcrumb back-link to the all-versions index
        if name != f"Documentation.Manual-{ver}" and name not in pages \
                and (wiki_dir / name).exists():
            pages.append(name)
    return pages


def convert_manual(ver: str, wiki_dir: Path, out_dir: Path, devel: bool = False):
    """Convert one version manual into a flat docs/ directory: the index becomes
    README.md and every linked page a sibling <Name>.md, with in-manual links
    rewritten to relative .md paths (resolved via _MANUAL_LINKS in page_to_slug).

    devel=True (the master branch) appends " / devel" to the index title, e.g.
    "Manual 4.1" → "Manual 4.1 / devel"."""
    index_name = f"Documentation.Manual-{ver}"
    if not (wiki_dir / index_name).exists():
        raise SystemExit(f"Manual index not found: {index_name}")
    subpages = manual_subpages(wiki_dir, ver)

    # Redirects let cross-references to moved pages still resolve to in-manual files.
    load_redirects(wiki_dir)
    _MANUAL_LINKS.clear()

    def register(wiki_name: str, fname: str) -> None:
        # Key on the versioned stem and a version-less alias, so cross-references
        # resolve whether or not they carry the -X-Y suffix (both forms occur).
        _MANUAL_LINKS[_manual_link_key(wiki_name)] = fname
        _MANUAL_LINKS[fname[:-3].lower().replace("-", "").replace("_", "")] = fname

    register(index_name, "README.md")
    for name in subpages:
        register(name, manual_filename(name, ver))

    # Manual page set (de-versioned, e.g. 'script-corevar') so cross-version
    # manual references (Script-CoreVar-3-6 from a 4-1 page) resolve to
    # /docs/manual/<ver>/<page> instead of a broken flat link.
    _MANUAL_PAGES.clear()
    for name in subpages:
        _MANUAL_PAGES.add(manual_filename(name, ver)[:-3].lower())

    print(f"Converting manual {ver}: 1 index + {len(subpages)} subpages → {out_dir}/")
    readme = out_dir / "README.md"
    convert_file(wiki_dir / index_name, readme)
    if devel:
        # Master is the development branch — mark the index title accordingly.
        txt = readme.read_text(encoding="utf-8")
        txt = re.sub(r'^(title:\s*"[^"\n]*?)(")', r'\1 / devel\2', txt, count=1, flags=re.M)
        readme.write_text(txt, encoding="utf-8")
    for name in subpages:
        convert_file(wiki_dir / name, out_dir / manual_filename(name, ver))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("src_dir", nargs="?", default="input", type=Path)
    parser.add_argument("dst_dir", nargs="?", default=None, type=Path)
    parser.add_argument("--wiki", metavar="WIKI_DIR", type=Path, help="Full wiki directory for resolving redirects")
    parser.add_argument("--content-dir", metavar="CONTENT_DIR", type=Path, help="Astro content/docs directory for resolving actual page slugs")
    parser.add_argument("--manual", metavar="VERSION", help="Convert one version manual (e.g. 4-1) from --wiki into a flat docs/ dir with relative .md links")
    parser.add_argument("--out", metavar="OUT_DIR", type=Path, help="Output directory for --manual mode (default ../output/manual/VERSION)")
    parser.add_argument("--devel", action="store_true", help="Mark this manual as the development branch (appends ' / devel' to the index title)")
    args = parser.parse_args()

    if args.manual:
        wiki = (args.wiki or Path("../wiki")).resolve()
        out = (args.out or args.dst_dir or Path(f"../output/manual/{args.manual}")).resolve()
        convert_manual(args.manual, wiki, out, devel=args.devel)
        return

    src_dir = args.src_dir
    dst_dir = args.dst_dir or Path("../output/documentation")

    if args.wiki:
        load_redirects(args.wiki)
    if args.content_dir:
        load_slug_map(args.content_dir)
        load_manual_pages(args.content_dir)

    files = [
        f for f in src_dir.iterdir()
        if f.is_file() and "." in f.name and f.suffix not in (".py", ".md", ".mdx") and not f.name.startswith(".")
    ]
    if not files:
        print("No PMwiki files found.")
        return

    # Group files by category (first word of page name, lowercased)
    # e.g. Documentation.Migration-* → migration/, Documentation.Tutorials-* → tutorials/
    def category_for(filename: str) -> str:
        parts = filename.split(".", 1)
        if len(parts) < 2:
            return ""
        page_part = parts[1]  # e.g. "Migration-1-4-to-1-5" or "Tutorials-WebSocket"
        return page_part.split("-")[0].lower()

    print(f"Converting {len(files)} file(s) → {dst_dir}/")
    for f in sorted(files):
        parts = f.name.split(".", 1)
        page = parts[1].lower().replace(".", "-") if len(parts) > 1 else f.stem.lower()
        category = category_for(f.name)
        out_path = (dst_dir / category / f"{page}.mdx") if category else (dst_dir / f"{page}.mdx")
        convert_file(f, out_path)


if __name__ == "__main__":
    main()
