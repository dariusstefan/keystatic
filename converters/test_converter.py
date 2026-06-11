"""Regression tests for convert.py.

Run with: python3 -m pytest test_converter.py -v
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from convert import convert_inline, pmwiki_to_mdx, normalize_heading_levels, extract_subtitle


# ---------------------------------------------------------------------------
# convert_inline
# ---------------------------------------------------------------------------

class TestBoldItalic:
    def test_bold(self):
        assert convert_inline("'''bold'''") == "**bold**"

    def test_italic(self):
        assert convert_inline("''italic''") == "*italic*"

    def test_bold_inside_sentence(self):
        assert convert_inline("use '''opensips-cli''' tool") == "use **opensips-cli** tool"

    def test_triple_double_quote_bold_typo(self):
        # """word""" is an author typo for PmWiki bold '''word'''
        assert convert_inline('"""Note""" that after forcing') == "**Note** that after forcing"

    def test_unclosed_bold_mismatched_quote(self):
        # '''word" typo — bold just the word
        assert convert_inline("the '''opensipsctlrc\" files") == "the **opensipsctlrc** files"

    def test_unclosed_bold_end_of_line(self):
        result = convert_inline("see '''note")
        assert result == "see **note**"


class TestMonospace:
    def test_double_at(self):
        assert convert_inline("@@code@@") == "`code`"

    def test_double_at_in_sentence(self):
        assert convert_inline("set @@xlog_level = 3@@ value") == "set `xlog_level = 3` value"

    def test_single_at_open_typo(self):
        # @word@@ — missing leading @
        result = convert_inline("@wss_tls_handshake_timeout@@")
        assert result == "`wss_tls_handshake_timeout`"

    def test_monospace_with_internal_at(self):
        # @@911@VSPdomain@@ — content has an internal single '@'; must not swallow
        # the rest of the line, and emphasis markers inside are dropped.
        result = convert_inline("R-URI: @@911@''VSPdomain''@@, then @@application/pidf@@ content")
        assert "`911@VSPdomain`" in result
        assert "`application/pidf`" in result
        assert ", then" in result  # text between spans not swallowed into code

    def test_single_at_monospace_typo(self):
        # @text@ (single @, typo for @@text@@) → code, but emails/911@ stay untouched
        assert "`application/pidf`" in convert_inline("in body with the @application/pidf@ content")
        assert "user@host.com" in convert_inline("contact user@host.com today")
        assert "`" not in convert_inline("contact user@host.com today")

    def test_inline_code_span(self):
        # [@code@] syntax
        assert convert_inline("[@some code@]") == "`some code`"

    def test_inline_code_span_no_match_double_at(self):
        # [@@label@@](url) must NOT be consumed by [@...@]
        result = convert_inline("[@@tls_method@@](https://example.com)")
        assert "`tls_method`" in result
        assert "example.com" in result
        assert result.startswith("[")  # still a link


class TestBraces:
    def test_empty_braces_inline_literal(self):
        # "authenticate{}" config marker — empty braces stay inline (escaped), not code
        result = pmwiki_to_mdx("both '''authenticate{}''' sections")
        assert r"**authenticate\{\}**" in result
        assert "`{}`" not in result

    def test_content_braces_become_code(self):
        result = pmwiki_to_mdx("use the {re.subst} transformation here")
        assert "`{re.subst}`" in result


class TestColorSpans:
    def test_red_span(self):
        result = convert_inline("%red%some warning%%")
        assert "@@red|some warning@@" in result

    def test_bold_preserved_inside_color_span(self):
        # bold inside color span must survive remark processing
        result = convert_inline("%red%set an '''xlog_level = 3''' value%%")
        assert "**xlog_level = 3**" in result
        assert "@@red|" in result

    def test_aside_uppercase_deprecated(self):
        result = convert_inline("%red%DEPRECATED%%")
        assert "@@green|Attention!@@" in result
        assert "@@red|" in result

    def test_aside_lowercase_no_banner(self):
        # lowercase "deprecated" must NOT produce Attention! banner
        result = convert_inline("%red%deprecated%%")
        assert "@@green|Attention!@@" not in result
        assert "@@red|deprecated@@" in result

    def test_color_span_does_not_corrupt_adjacent_span(self):
        # **@@green|Attention!@@** @@red|x@@ must not collapse into one span
        result = convert_inline("%red%DEPRECATED%% and %red%more%%")
        assert result.count("@@green|Attention!@@") == 1

    def test_printf_specifiers_preserved(self):
        # %e %t %s %p printf-style specifiers must NOT be eaten as wikistyles
        result = convert_inline("echo 'core.%e.%t.sig%s.%p'")
        assert result == "echo 'core.%e.%t.sig%s.%p'"

    def test_strftime_and_flags_preserved(self):
        assert "%Y" in convert_inline("date +%Y.%T")
        assert "%P -u%" in convert_inline("run %P -u% now") or "%P" in convert_inline("run %P -u% now")

    def test_block_wikistyle_stripped(self):
        assert convert_inline("%block text-align=right% **by X**").strip() == "**by X**"

    def test_attr_wikistyle_stripped(self):
        assert convert_inline("%width=500px% caption").strip() == "caption"

    def test_alignment_wikistyle_stripped(self):
        assert convert_inline("%center% middle").strip() == "middle"

    def test_inserted_markup_link_in_color_span(self):
        # {+[[url|label]]+} inside %red%...%% must become a clean colored link,
        # not code-wrapped (the braces/brackets must not read as "code-like").
        result = convert_inline("%red%see {+[[http://x.org/m.html|the docs]]+} now%%")
        assert result == "@@red|see [the docs](http://x.org/m.html) now@@"
        assert "`@@" not in result
        assert "{+" not in result

    def test_color_span_with_code_still_wraps(self):
        # genuine code ($var) inside a color span still gets code-wrapped
        result = convert_inline("%red%$ru value%%")
        assert result == "`@@red|$ru value@@`"

    def test_two_color_spans_no_corruption(self):
        # Regression: @@green|...@@** @@red|...@@ was being matched as @@** @@
        result = convert_inline(
            "marked as %red%DEPRECATED%% - still work"
        )
        assert "Attention!" in result
        assert "`** `" not in result


class TestWikiLinks:
    def test_bare_url_link_not_autolink(self):
        # [[http://x.org]] must become [url](url), NOT <url> (MDX breaks on <url>)
        result = convert_inline("available at [[http://msrprelay.org]]")
        assert "[http://msrprelay.org](http://msrprelay.org)" in result
        assert "<http" not in result

    def test_basic_link_with_label(self):
        result = convert_inline("[[https://example.com|click here]]")
        assert result == "[click here](https://example.com)"

    def test_triple_bracket_typo(self):
        # [[[url|label]] — extra leading [
        result = convert_inline("[[[https://example.com|label]]")
        assert result == "[label](https://example.com)"

    def test_quadruple_bracket_with_space(self):
        # [[[[ url|label]] — extra [[ and leading space
        result = convert_inline("[[[[ https://example.com|label]]")
        assert result == "[label](https://example.com)"

    def test_navigation_anchor_dropped(self):
        # [[<<]] — PmWiki back navigation, drop it
        result = convert_inline("text [[<<]] more")
        assert "<<" not in result
        assert result.strip() == "text  more".strip() or "<<" not in result

    def test_bare_section_anchor_dropped(self):
        # [[#Anchor]] — PmWiki anchor definition, must not render as a link
        result = convert_inline("Accounting in OpenSIPS [[#Accounting]]")
        assert "[Accounting]" not in result
        assert "#Accounting" not in result
        assert "Accounting in OpenSIPS" in result

    def test_monospace_link_label(self):
        # [[url|@@code@@]] — monospace label
        result = convert_inline("[[https://example.com|@@tls_method@@]]")
        assert "`tls_method`" in result
        assert "example.com" in result

    def test_citation_label_with_brackets(self):
        # [[url|[1] ]] — label contains a bracketed citation ref
        result = convert_inline("multimedia[[https://en.wikipedia.org/wiki/RCS|[1] ]].")
        assert "https://en.wikipedia.org/wiki/RCS" in result
        assert r"\[1\]" in result  # brackets escaped so they render literally
        assert "[[https" not in result  # no leftover raw wiki link

    def test_mismatched_at_in_link_label(self):
        # [[[url|@word@@]] — single @ open
        result = convert_inline(
            "[[[https://opensips.org/html#param|@wss_tls_handshake_timeout@@]]"
        )
        assert "`wss_tls_handshake_timeout`" in result
        assert "opensips.org" in result


class TestImages:
    def test_bare_image_url_becomes_local_image(self):
        result = convert_inline("%center% %width=500px%http://opensips.org/x/acc_event_success.png")
        assert "![acc event success](/images/docs/tutorials/acc_event_success.png)" in result

    def test_jpeg_image(self):
        result = convert_inline("http://www.opensips.org/images/top_hiding_schema.jpeg")
        assert result.strip() == "![top hiding schema](/images/docs/tutorials/top_hiding_schema.jpeg)"

    def test_image_url_as_link_target_not_converted(self):
        # a Markdown link whose target is an image URL must stay a link
        result = convert_inline("see [the doc](http://opensips.org/x.png) here")
        assert "![" not in result
        assert "[the doc](http://opensips.org/x.png)" in result


class TestArrows:
    def test_bidirectional_arrow(self):
        # <-> → ↔ (Unicode bidirectional arrow, plain text, no MDX issues)
        result = pmwiki_to_mdx("UAC<->OpenSIPS")
        assert "↔" in result
        assert "`<->`" not in result

    def test_left_arrow(self):
        # <- → ← (Unicode left arrow, plain text, no MDX issues)
        result = pmwiki_to_mdx("response<-server")
        assert "←" in result
        assert "`<-`" not in result


# ---------------------------------------------------------------------------
# pmwiki_to_mdx (block-level)
# ---------------------------------------------------------------------------

class TestHeadings:
    def test_three_bangs_is_h2(self):
        result = pmwiki_to_mdx("!!! DB migration\n!!! Script migration")
        assert "## DB migration" in result
        assert "## Script migration" in result

    def test_four_bangs_is_h3_under_h2(self):
        # !!! (h2) + !!!! (h3) — relative depth must be preserved
        result = pmwiki_to_mdx("!!! DB migration\n!!!! Global Parameters")
        assert "## DB migration" in result
        assert "### Global Parameters" in result

    def test_five_bangs_is_h4_under_h3(self):
        # !!!+!!!!+!!!!! hierarchy
        result = pmwiki_to_mdx("!!! Script\n!!!! Modules\n!!!!! DB_MYSQL module")
        assert "## Script" in result
        assert "### Modules" in result
        assert "#### DB_MYSQL module" in result

    def test_six_bangs_capped_no_leak(self):
        # !!!!!! must map to a heading with all bangs stripped (no stray '!')
        result = pmwiki_to_mdx("! Top\n!! Sub\n!!!!!! Deep heading")
        assert "Deep heading" in result
        assert "! Deep" not in result
        assert "###### Deep heading" in result or "#### Deep heading" in result

    def test_single_and_double_bang_hierarchy(self):
        # Pages using ! (top) and !! (sub) — fewer bangs = higher level.
        # ! must become h2 and !! must become h3 (not inverted).
        result = pmwiki_to_mdx("! Introduction\n! Managing\n!! Iterating")
        assert "## Introduction" in result
        assert "## Managing" in result
        assert "### Iterating" in result
        # the top-level ! sections must NOT be deeper than the !! subsection
        assert "### Introduction" not in result

    def test_title_strips_wiki_markup(self):
        from convert import extract_title
        t = ('!!!!! Documentation -> [[Documentation.Tutorials | Tutorials ]] -> '
             '[[ http://x.org/topology_hiding.html | {+Topology Hiding+} ]] with OpenSIPS')
        assert extract_title(t, 'fb') == "Topology Hiding with OpenSIPS"

    def test_title_link_extracted_for_subtitle(self):
        from convert import extract_title_link
        t = ('!!!!! Documentation -> [[Documentation.Tutorials | Tutorials ]] -> '
             '[[ http://x.org/topology_hiding.html | {+Topology Hiding+} ]] with OpenSIPS')
        label, url = extract_title_link(t)
        assert label == "Topology Hiding"
        assert url == "http://x.org/topology_hiding.html"

    def test_no_title_link_when_plain(self):
        from convert import extract_title_link
        assert extract_title_link("!!!!! Documentation -> Tutorials -> Plain Title") == (None, None)

    def test_breadcrumb_dropped(self):
        result = pmwiki_to_mdx("!!!!!Documentation -> Migration -> Title")
        assert "#" not in result

    def test_four_bang_breadcrumb_dropped(self):
        result = pmwiki_to_mdx("!!!!Documentation -> Section -> Title")
        assert "#" not in result


class TestNormalizeHeadings:
    def test_no_level_skip(self):
        text = "## Section\n### Sub\n#### Deep"
        assert normalize_heading_levels(text) == text

    def test_clamp_skip(self):
        # h2 → h4 should become h2 → h3
        text = "## Section\n#### Jumped"
        result = normalize_heading_levels(text)
        assert "### Jumped" in result

    def test_min_heading_shifted_to_h2(self):
        # If a doc has only h3 headings, they should be shifted to h2 so counters start at 1
        text = "### Topic One\n### Topic Two"
        result = normalize_heading_levels(text)
        lines = result.split("\n")
        heading_lines = [l for l in lines if re.match(r'^#+\s', l)]
        assert all(l.startswith("## ") for l in heading_lines), f"Expected all h2: {heading_lines}"

    def test_relative_depth_preserved_after_shift(self):
        # h3 (top) + h4 (sub) → h2 + h3 after shift
        text = "### Top\n#### Sub"
        result = normalize_heading_levels(text)
        assert "## Top" in result
        assert "### Sub" in result

    def test_migration_3_6_to_4_0_case(self):
        # MI naming logic (h4) directly under DB migration (h2) → h3
        text = "## DB migration\n#### MI naming logic\n## Script migration"
        result = normalize_heading_levels(text)
        assert "### MI naming logic" in result


class TestCodeBlocks:
    def test_block_code(self):
        text = "[@\n  some code\n@]"
        result = pmwiki_to_mdx(text)
        assert "```" in result
        assert "some code" in result

    def test_indented_block(self):
        text = " # opensips-cli command\n"
        result = pmwiki_to_mdx(text)
        assert "```" in result

    def test_indented_numbered_list_not_code(self):
        # Indented "N - text" prose is a numbered list, not a code block
        src = (" The values that this field can take are:\n"
               "        1 - the organization is a Source.\n"
               "        2 - the organization is a VPC.\n"
               "        3 - the organization is a VSP.")
        result = pmwiki_to_mdx(src)
        assert "```" not in result
        assert "1. the organization is a Source." in result
        assert "2. the organization is a VPC." in result

    def test_indented_prose_not_code(self):
        # Indented line with PmWiki markup → prose, not code block
        text = " '''[[https://example.com|link]]'''.\n"
        result = pmwiki_to_mdx(text)
        assert "```" not in result

    def test_lframe_block_becomes_code(self):
        # >>lframe ...<< ... >><< framed example → code fence; [[<<]] are line breaks,
        # [=...=] is a verbatim escape, _empty_line_ markers are dropped.
        src = (">>lframe black<<\n"
               ":b2b_trigger_scenario[=:=]fifo_reply[[<<]]\n"
               "marketing[[<<]]\n"
               "_empty_line_\n"
               ">><<")
        result = pmwiki_to_mdx(src)
        assert "```" in result
        assert ":b2b_trigger_scenario:fifo_reply" in result
        assert "[[<<]]" not in result
        assert "_empty_line_" not in result
        assert ">>" not in result

    def test_pre_br_becomes_newline(self):
        from convert import decode_pmwiki_text
        decoded = decode_pmwiki_text('<pre>if(x)<br>&nbsp; do_y();</pre>')
        assert "if(x)\n" in decoded

    def test_lframe_wrapping_pre_no_marker_leak(self):
        # >>lframe<< wrapping a <pre> (decoded to [@...@]) must not leak [@/@] markers
        src = '>>lframe<<\n<pre>if(x)<br>&nbsp; do_y();</pre>\n>><<'
        result = pmwiki_to_mdx(src)
        assert "[@" not in result and "@]" not in result
        assert "```" in result
        assert "if(x)" in result and "do_y();" in result

    def test_pre_html_stripped(self):
        text = "<pre><span style=\"color:red\">if(x)</span></pre>"
        from convert import decode_pmwiki_text
        decoded = decode_pmwiki_text(text)
        assert "<span" not in decoded
        assert "[@" in decoded
        assert "if(x)" in decoded


class TestTables:
    def test_basic_table(self):
        text = "|| A || B ||\n|| 1 || 2 ||"
        result = pmwiki_to_mdx(text)
        assert "| A | B |" in result
        assert "| --- |" in result

    def test_header_bang_stripped(self):
        text = "||! Module ||! Name ||\n|| core || add_rule ||"
        result = pmwiki_to_mdx(text)
        assert "| Module | Name |" in result
        assert "! Module" not in result

    def test_table_with_code_cell_becomes_list_items(self):
        # A table whose last column holds a multi-line [@...@] code example →
        # each row becomes a bullet list item with a nested fenced code block
        # (indented 2 spaces) that preserves the code's newlines/indentation.
        src = (
            "||Value source||Value type||Example||\n"
            "||Inline URI ||\"uri\" ||[@\n"
            "<destination>\n"
            "   sip:x\n"
            "</destination>\n"
            "@]||"
        )
        result = pmwiki_to_mdx(src)
        assert '* **Inline URI** — "uri"' in result
        # fence is nested (indented 2 spaces) under the list item
        assert "  ```" in result
        # multi-line code stays on multiple lines, indented to nest in the item
        assert "  <destination>\n     sip:x\n  </destination>" in result
        assert "[@" not in result and "@]" not in result
        assert "<table>" not in result
        assert "| Value source |" not in result  # not a broken GFM table

    def test_orange_table_caption_drops_prefix(self):
        # An orange "Table:" caption precedes labeled code blocks, not a real
        # table, so the "Table:" prefix is dropped and the caption itself is
        # colored orange.
        src = "%color=#ff7f00% Table: %black%'''Scenario init node examples'''"
        result = pmwiki_to_mdx(src)
        assert "@@orange|**Scenario init node examples**@@" in result
        assert "Table:" not in result

    def test_plain_table_prefix_before_colored_caption_dropped(self):
        # "Table:" as plain text before a colored bold caption is also dropped.
        src = "Table: %green%'''Scripting examples'''%%"
        result = pmwiki_to_mdx(src)
        assert "@@green|**Scripting examples**@@" in result
        assert "Table:" not in result

    def test_orange_ex_caption_keeps_prefix(self):
        # "Ex:" captions are left untouched — only "Table:" is dropped.
        src = "%color=#ff7f00% Ex: %black%'''Fifo MI command'''"
        result = pmwiki_to_mdx(src)
        assert "@@orange|Ex:@@" in result
        assert "Fifo MI command" in result

    def test_code_comparison_table_becomes_list_items(self):
        # A 2-column table whose cells hold multi-line [@...@] code becomes a
        # bullet list, one item per column (bold label + nested code) — not
        # headings, so the labels stay out of the TOC.
        text = (
            "||border=1\n"
            "|| '''With Helper''' || '''Classic''' ||\n"
            "||%block black% [@\nloadmodule \"a.so\"\n@]||[@\nloadmodule \"b.so\"\n@]||"
        )
        result = pmwiki_to_mdx(text)
        assert "* **With Helper**" in result and "* **Classic**" in result
        assert 'loadmodule "a.so"' in result
        assert 'loadmodule "b.so"' in result
        assert "[@" not in result and "@]" not in result
        assert "||" not in result
        # labels are not headings
        assert "###### With Helper" not in result
        assert result.count("```") == 4  # two fenced blocks (nested, indented)

    def test_table_attribute_line_dropped(self):
        text = "|| border=1 cellpadding=4\n|| A || B ||\n|| 1 || 2 ||"
        result = pmwiki_to_mdx(text)
        assert "border=1" not in result
        assert "| A | B |" in result

    def test_blank_line_after_table_before_caption(self):
        # A caption/marker line right after a table must be separated by a blank
        # line, else GFM parses it (it contains '|') as another table row.
        text = "|| A || B ||\n|| 1 || 2 ||\n%green%'''caption'''"
        result = pmwiki_to_mdx(text)
        lines = result.split("\n")
        caption_idx = next(i for i, l in enumerate(lines) if "caption" in l)
        assert lines[caption_idx - 1].strip() == "", f"no blank line before caption: {lines}"


class TestNoteBlock:
    def test_note_inline(self):
        result = pmwiki_to_mdx("NOTE: some text here")
        assert "> [!NOTE]" in result
        assert "> some text here" in result

    def test_note_standalone_with_bullets(self):
        text = "NOTE:\n* first item\n* second item"
        result = pmwiki_to_mdx(text)
        assert "> [!NOTE]" in result
        assert "> * first item" in result
        assert "> * second item" in result

    def test_bold_note_marker_becomes_note_alert(self):
        # a line opening with a bolded "Note" callout marker → Note alert
        result = pmwiki_to_mdx('"""Note""" that after forcing the SRS interface, restore it.')
        assert "> [!NOTE]" in result
        assert "> after forcing the SRS interface, restore it." in result

    def test_bold_note_colon_inside_markers(self):
        # '''NOTE:''' (colon inside the bold markers) at line start → Note alert
        result = pmwiki_to_mdx("'''NOTE:''' the default port for WSS is privileged.")
        assert "> [!NOTE]" in result
        assert "> the default port for WSS is privileged." in result

    def test_inline_note_stays_inline(self):
        # '''NOTE:''' mid-line (parenthetical) must NOT become a callout
        result = pmwiki_to_mdx("* @@-n@@: the port ('''NOTE:''' NG only)")
        assert "> [!NOTE]" not in result
        assert "**NOTE:**" in result

    def test_plain_note_prose_untouched(self):
        # ordinary "Note that ..." prose (no bold) must stay prose
        result = pmwiki_to_mdx("Note that this is just normal prose.")
        assert "> [!NOTE]" not in result
        assert "Note that this is just normal prose." in result

    def test_note_as_heading_becomes_alert(self):
        # !!NOTE: ... — authored misuse of heading syntax for a note
        result = pmwiki_to_mdx('!!NOTE: add promiscredir=yes to sip.conf')
        assert "> [!NOTE]" in result
        assert "> add promiscredir=yes to sip.conf" in result
        assert "## NOTE" not in result

    def test_note_standalone_no_bullets(self):
        result = pmwiki_to_mdx("NOTE:\n\nSome other paragraph")
        assert "> [!NOTE]" in result


class TestSubtitle:
    def test_heading_followed_by_author_is_subtitle(self):
        body = "## How to build Diameter requests\n **by Liviu Chircu**\n\n---\n\n## Setting up\n\ntext"
        subtitle, author, new_body = extract_subtitle(body)
        assert subtitle == "How to build Diameter requests"
        assert author == "by Liviu Chircu"
        # heading AND author line AND leftover hr removed from body
        assert "## How to build Diameter requests" not in new_body
        assert "by Liviu Chircu" not in new_body
        # body now starts at the first real section
        assert new_body.lstrip().startswith("## Setting up")

    def test_written_by_variant(self):
        body = "## Scaling registrations\n **written by Liviu Chircu**\n\n## Section"
        subtitle, author, new_body = extract_subtitle(body)
        assert subtitle == "Scaling registrations"
        assert author == "by Liviu Chircu"  # normalized

    def test_author_colon_form_with_email(self):
        # "Author: Name <email>" form must be detected and normalized to "by Name"
        body = "## Voice Transcoding\n **Author: Liviu Chircu `<liviu@opensips.org>`**\n\n## Section"
        subtitle, author, new_body = extract_subtitle(body)
        assert subtitle == "Voice Transcoding"
        assert author == "by Liviu Chircu"
        assert "Author:" not in new_body
        assert "liviu@opensips.org" not in new_body

    def test_no_author_no_subtitle(self):
        # ordinary page: first heading not followed by author → unchanged
        body = "## DB migration\n\nThis is prose.\n\n## Script migration"
        subtitle, author, new_body = extract_subtitle(body)
        assert subtitle is None
        assert author is None
        assert new_body == body

    def test_prose_first_no_subtitle(self):
        body = "This page contains info.\n\n## Section one"
        subtitle, author, new_body = extract_subtitle(body)
        assert subtitle is None
        assert new_body == body

    def test_bold_non_author_not_subtitle(self):
        # heading followed by bold text that isn't an author attribution
        body = "## Overview\n **Important** note here\n\n## Next"
        subtitle, author, new_body = extract_subtitle(body)
        assert subtitle is None
        assert new_body == body

    def test_subtitle_removal_renormalizes_headings(self):
        # After the subtitle heading is pulled out, the remaining body's shallowest
        # heading must be re-normalized to h2 (else it renders as "0.1").
        from convert import normalize_heading_levels
        body = "## Scaling registrations\n **by Liviu Chircu**\n\n#### Tutorial Overview\n\n##### Scenario"
        subtitle, author, new_body = extract_subtitle(body)
        new_body = normalize_heading_levels(new_body)
        assert "## Tutorial Overview" in new_body
        assert "### Scenario" in new_body

    def test_no_leading_hr_after_extraction(self):
        # the separator that followed the author must not be left dangling at the top
        body = "## Title Heading\n **by Someone**\n\n---\n\n## Real Section"
        _, _, new_body = extract_subtitle(body)
        assert not new_body.lstrip().startswith("---")


class TestListItems:
    def test_bullet_with_space(self):
        result = pmwiki_to_mdx("* item one")
        assert "* item one" in result

    def test_bullet_without_space(self):
        # *''italic'' — no space after bullet
        result = pmwiki_to_mdx("*''italic''")
        assert "* *italic*" in result

    def test_numbered_list(self):
        result = pmwiki_to_mdx("# first\n# second")
        assert "* first" in result

    def test_indented_bold_dash_definition(self):
        # "'''''- term: '''''desc" (indented) → nested list item, not a code block
        src = "              '''''- selectiveRoutingID: '''''The CLLI code."
        result = pmwiki_to_mdx(src)
        assert "* **selectiveRoutingID:** The CLLI code." in result
        assert "```" not in result
        assert "'''''" not in result

    def test_list_style_modifier_dash_stripped(self):
        # "#- item" — the dash is a PmWiki list-style modifier, not a nested bullet
        result = pmwiki_to_mdx("#- Installation of Red Hat")
        assert result.strip() == "* Installation of Red Hat"
        assert "* -" not in result

    def test_dash_content_preserved(self):
        # a dash that is real content (no following space) must survive
        result = pmwiki_to_mdx("* -5 dB threshold")
        assert "-5 dB threshold" in result


class TestModuleStatusBadge:
    """Module-listing maturity status → emoji badge (replaces colored text)."""

    def _item(self, line):
        from convert import convert_list_item
        return convert_list_item(line)

    def test_stable_green_marker_to_badge(self):
        out = self._item(
            "* [**DIALOG**](../modules/dialog/README.md) - Dialog support module , @@green|stable@@")
        assert out.endswith(" — 🟢 **stable**")
        assert "@@green" not in out

    def test_new_red_marker_to_badge(self):
        out = self._item("* [**X**](../modules/x/README.md) - Desc, @@red|NEW@@")
        assert out.endswith(" — 🔵 **NEW**")
        assert "@@red" not in out

    def test_beta_plain_word_to_badge(self):
        out = self._item("* [**HTTP2D**](../modules/http2d/README.md) - HTTP/2 Server, beta")
        assert out.endswith(" — 🟡 **beta**")

    def test_website_link_form_also_matches(self):
        out = self._item("* [**TM**](/docs/modules/devel/tm) - Transaction module , @@green|stable@@")
        assert out.endswith(" — 🟢 **stable**")

    def test_no_comma_separator(self):
        # status attached with only a space, no comma
        out = self._item("* [**SQLOPS**](../modules/sqlops/README.md) - SQL DB operations module @@green|stable@@")
        assert out.endswith(" — 🟢 **stable**")
        assert "@@green" not in out

    def test_trailing_dash_after_status(self):
        out = self._item("* [**STUN**](../modules/stun/README.md) - Built-in STUN server , @@green|stable@@ - ")
        assert out.endswith(" — 🟢 **stable**")
        assert out.count("-") == 0 or "stable** -" not in out

    def test_compound_alpha_new(self):
        out = self._item("* [**CONFIG**](../modules/config/README.md) - DB backed runtime configuration, alpha / @@red|NEW@@")
        assert out.endswith(" — 🔴 **alpha** / 🔵 **NEW**")
        assert "@@red" not in out

    def test_compound_alpha_new_no_comma(self):
        out = self._item("* [**OPENTELEMETRY**](../modules/opentelemetry/README.md) - tracing the routes they produce alpha / @@red|NEW@@")
        assert out.endswith(" — 🔴 **alpha** / 🔵 **NEW**")

    def test_non_module_bullet_beta_untouched(self):
        # "beta" in a non-module bullet must not become a badge
        out = self._item("* the next release is beta, beta")
        assert "🟡" not in out
        assert out.strip().endswith("beta, beta")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
