const COLOR_MARKER_RE = /@@(red|green|blue|orange|yellow)\|(.+?)@@/g;

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

  for (let index = node.children.length - 1; index >= 0; index -= 1) {
    const child = node.children[index];
    visit(child, node);
    replaceCodeBlockMarkers(child, index, node);
    replaceInlineCodeMarkers(child, index, node);
    splitColorMarkers(child, index, node);
  }
}

export default function remarkTextMarkers() {
  return (tree) => visit(tree);
}
