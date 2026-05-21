const COLOR_MARKER_RE = /@@(red|green|blue|orange|yellow)\|(.+?)@@/g;
const ANCHOR_MARKER_RE = /^@@anchor\|([A-Za-z0-9_.-]+)@@$/;
const LINK_ICON =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="m12.11 15.39-3.88 3.88a2.52 2.52 0 0 1-3.5 0 2.47 2.47 0 0 1 0-3.5l3.88-3.88a1 1 0 0 0-1.42-1.42l-3.88 3.89a4.48 4.48 0 0 0 6.33 6.33l3.89-3.88a1 1 0 1 0-1.42-1.42Zm8.58-12.08a4.49 4.49 0 0 0-6.33 0l-3.89 3.88a1 1 0 0 0 1.42 1.42l3.88-3.88a2.52 2.52 0 0 1 3.5 0 2.47 2.47 0 0 1 0 3.5l-3.88 3.88a1 1 0 1 0 1.42 1.42l3.88-3.89a4.49 4.49 0 0 0 0-6.33ZM8.83 15.17a1 1 0 0 0 1.1.22 1 1 0 0 0 .32-.22l4.92-4.92a1 1 0 0 0-1.42-1.42l-4.92 4.92a1 1 0 0 0 0 1.42Z"/></svg>';

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function colorMarkerToHtml(color, value) {
  return {
    type: 'html',
    value: `<span class="color-${color}">${escapeHtml(value)}</span>`,
  };
}

function colorMarkersToHtml(value) {
  const parts = [];
  let cursor = 0;

  COLOR_MARKER_RE.lastIndex = 0;
  for (const match of value.matchAll(COLOR_MARKER_RE)) {
    if (match.index > cursor) {
      parts.push(escapeHtml(value.slice(cursor, match.index)));
    }

    parts.push(`<span class="color-${match[1]}">${escapeHtml(match[2])}</span>`);
    cursor = match.index + match[0].length;
  }

  if (cursor < value.length) {
    parts.push(escapeHtml(value.slice(cursor)));
  }

  return parts.join('');
}

function splitColorMarkers(node, index, parent) {
  if (!parent || node.type !== 'text') return;

  const value = node.value;
  COLOR_MARKER_RE.lastIndex = 0;
  const matches = [...value.matchAll(COLOR_MARKER_RE)];
  if (!matches.length) return;

  const replacement = [];
  let cursor = 0;

  for (const match of matches) {
    if (match.index > cursor) {
      replacement.push({ type: 'text', value: value.slice(cursor, match.index) });
    }

    replacement.push(colorMarkerToHtml(match[1], match[2]));
    cursor = match.index + match[0].length;
  }

  if (cursor < value.length) {
    replacement.push({ type: 'text', value: value.slice(cursor) });
  }

  parent.children.splice(index, 1, ...replacement);
}

function getAnchorMarkerId(node) {
  if (node?.type !== 'paragraph' || node.children?.length !== 1) return null;

  const child = node.children[0];
  if (child.type !== 'text') return null;

  return child.value.trim().match(ANCHOR_MARKER_RE)?.[1] ?? null;
}

function getPlainText(node) {
  if (!node) return '';
  if (typeof node.value === 'string') return node.value;
  if (!Array.isArray(node.children)) return '';
  return node.children.map(getPlainText).join('');
}

function addHeadingLink(heading, anchorId) {
  if (heading.children?.some((child) => child.type === 'html' && child.value.includes('legacy-heading-link'))) {
    return;
  }

  const label = escapeHtml(getPlainText(heading).trim() || anchorId);
  heading.children.push({
    type: 'html',
    value: `<a class="legacy-heading-link" href="#${escapeHtml(anchorId)}" aria-label="Link to ${label}" data-pagefind-ignore="true">${LINK_ICON}</a>`,
  });
}

function attachAnchorMarkersToHeadings(node) {
  if (!node || !Array.isArray(node.children)) return;

  for (let index = node.children.length - 2; index >= 0; index -= 1) {
    const anchorId = getAnchorMarkerId(node.children[index]);
    const next = node.children[index + 1];

    if (!anchorId || next?.type !== 'heading') continue;

    next.data = next.data || {};
    next.data.hProperties = {
      ...(next.data.hProperties || {}),
      id: anchorId,
    };
    addHeadingLink(next, anchorId);
    node.children.splice(index, 1);
  }
}

function replaceAnchorParagraph(node, index, parent) {
  if (!parent) return;

  const anchorId = getAnchorMarkerId(node);
  if (!anchorId) return;
  parent.children.splice(index, 1, {
    type: 'html',
    value: `<span id="${escapeHtml(anchorId)}" class="legacy-anchor" aria-hidden="true"></span>`,
  });
}

function replaceInlineCodeMarkers(node, index, parent) {
  COLOR_MARKER_RE.lastIndex = 0;
  if (!parent || node.type !== 'inlineCode' || !COLOR_MARKER_RE.test(node.value)) return;
  COLOR_MARKER_RE.lastIndex = 0;

  parent.children.splice(index, 1, {
    type: 'html',
    value: `<code>${colorMarkersToHtml(node.value)}</code>`,
  });
}

function replaceCodeBlockMarkers(node, index, parent) {
  COLOR_MARKER_RE.lastIndex = 0;
  if (!parent || node.type !== 'code' || !COLOR_MARKER_RE.test(node.value)) return;
  COLOR_MARKER_RE.lastIndex = 0;

  const language = node.lang ? ` class="language-${escapeHtml(node.lang)}"` : '';
  parent.children.splice(index, 1, {
    type: 'html',
    value: `<pre><code${language}>${colorMarkersToHtml(node.value)}</code></pre>`,
  });
}

function visit(node, parent = null) {
  if (!node || !Array.isArray(node.children)) return;

  attachAnchorMarkersToHeadings(node);

  for (let index = node.children.length - 1; index >= 0; index -= 1) {
    const child = node.children[index];
    visit(child, node);
    replaceAnchorParagraph(child, index, node);
    replaceCodeBlockMarkers(child, index, node);
    replaceInlineCodeMarkers(child, index, node);
    splitColorMarkers(child, index, node);
  }
}

export default function remarkTextMarkers() {
  return (tree) => visit(tree);
}
