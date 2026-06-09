import fs from 'node:fs';
import path from 'node:path';
import { visit, SKIP } from 'unist-util-visit';
import { fromMarkdown } from 'mdast-util-from-markdown';
import { gfm } from 'micromark-extension-gfm';
import { gfmFromMarkdown } from 'mdast-util-gfm';

// File-include directive that stays portable across GitHub and the website.
//
// In the committed markdown you write an ordinary link whose *title* is the
// word "include", e.g.:
//
//     [opensips.cfg](../examples/opensips.cfg "include")
//
// On github.com this renders as a normal link to the file (the title shows as
// a tooltip), so the source stays valid GitHub-flavored markdown. During the
// site build this plugin replaces that link with the linked file's contents:
//   * a markdown file (.md/.mdx/.markdown) is parsed and spliced in as real
//     block content, so it renders like any other section;
//   * any other file becomes a fenced code block (language inferred from the
//     extension — .cfg maps to `c`, matching the rest of the docs).
//
// Includes are recursive (an included .md may itself include other files) and
// each link resolves relative to the directory of the file that contains it,
// so chains like page.md → samples.md → samples/foo.cfg work regardless of how
// the files are laid out relative to each other. A cycle guard prevents a file
// that (transitively) includes itself from looping forever.
//
// The link must be the sole content of its paragraph (a block-level include);
// inline links with other text alongside them are left untouched.

const INCLUDE_TITLE = 'include';

// Extensions parsed as markdown rather than embedded as a code block.
const MARKDOWN_EXTS = new Set(['.md', '.mdx', '.markdown']);

// Map file extensions to a syntax-highlighting language for code-block includes.
const LANG_BY_EXT = {
  '.cfg': 'c',
  '.sql': 'sql',
  '.sh': 'bash',
  '.bash': 'bash',
  '.json': 'json',
  '.yaml': 'yaml',
  '.yml': 'yaml',
  '.py': 'python',
  '.c': 'c',
  '.h': 'c',
};

function includedDir(file) {
  // Astro/unified vfile: `path` is the absolute path of the file being rendered.
  const filePath = file?.path ?? file?.history?.[file.history.length - 1];
  if (!filePath) {
    throw new Error('remarkInclude: cannot resolve includes without a file path');
  }
  return path.dirname(filePath);
}

// Read `target` and return the mdast nodes that should replace the include link,
// fully expanding any nested includes (resolved relative to `target`'s own dir).
function expandTarget(target, seen) {
  let raw;
  try {
    raw = fs.readFileSync(target, 'utf8');
  } catch {
    throw new Error(`remarkInclude: cannot read included file (resolved to ${target})`);
  }

  const ext = path.extname(target).toLowerCase();
  if (!MARKDOWN_EXTS.has(ext)) {
    return [
      {
        type: 'code',
        lang: LANG_BY_EXT[ext] ?? null,
        meta: null,
        value: raw.replace(/\r?\n$/, ''),
      },
    ];
  }

  const sub = fromMarkdown(raw, {
    extensions: [gfm()],
    mdastExtensions: [gfmFromMarkdown()],
  });
  expandTree(sub, path.dirname(target), seen);
  return sub.children;
}

// Replace every block-level include link in `tree` with the included content,
// resolving each link relative to `baseDir`.
function expandTree(tree, baseDir, seen) {
  visit(tree, 'paragraph', (para, index, parent) => {
    if (!parent || index == null) return;
    if (para.children.length !== 1) return;

    const link = para.children[0];
    if (link.type !== 'link' || link.title !== INCLUDE_TITLE) return;

    const target = path.resolve(baseDir, link.url);
    if (seen.has(target)) {
      throw new Error(`remarkInclude: include cycle detected at ${target}`);
    }

    const replacement = expandTarget(target, new Set(seen).add(target));
    parent.children.splice(index, 1, ...replacement);
    // Content is already fully expanded; continue after the inserted nodes.
    return [SKIP, index + replacement.length];
  });
}

export default function remarkInclude() {
  return (tree, file) => {
    const filePath = file?.path ?? file?.history?.[file.history.length - 1];
    expandTree(tree, includedDir(file), new Set(filePath ? [filePath] : []));
  };
}
