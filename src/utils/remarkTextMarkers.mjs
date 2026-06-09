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

function nodeToHtmlString(node) {
  if (node.type === 'text') return escapeHtml(node.value);
  if (node.type === 'strong') return `<strong>${(node.children || []).map(nodeToHtmlString).join('')}</strong>`;
  if (node.type === 'emphasis') return `<em>${(node.children || []).map(nodeToHtmlString).join('')}</em>`;
  if (node.type === 'inlineCode') return `<code>${escapeHtml(node.value)}</code>`;
  if (node.type === 'html') return node.value;
  if (node.type === 'link') {
    const href = escapeHtml(node.url || '');
    return `<a href="${href}">${(node.children || []).map(nodeToHtmlString).join('')}</a>`;
  }
  if (Array.isArray(node.children)) return node.children.map(nodeToHtmlString).join('');
  return escapeHtml(node.value || '');
}

// Handle @@color|...@@ spans that cross AST node boundaries (e.g. contain **bold** or *italic*).
function processColorSpansInParent(node) {
  if (!node || !Array.isArray(node.children)) return;
  const children = node.children;
  const OPEN_RE = /^([\s\S]*?)@@(red|green|blue|orange|yellow)\|([\s\S]*)$/;

  for (let i = 0; i < children.length; i++) {
    const child = children[i];
    if (child.type !== 'text') continue;

    const startMatch = child.value.match(OPEN_RE);
    if (!startMatch) continue;

    const [, beforeMarker, color, afterOpen] = startMatch;

    // If closing @@ is in the same text node, splitColorMarkers handles it
    if (afterOpen.includes('@@')) continue;

    // Find the closing @@ in a later sibling
    const innerNodes = [];
    if (afterOpen) innerNodes.push({ type: 'text', value: afterOpen });

    let j = i + 1;
    let closeFound = false;
    let afterClose = '';

    while (j < children.length) {
      const sibling = children[j];
      if (sibling.type === 'text') {
        const closeIdx = sibling.value.indexOf('@@');
        if (closeIdx !== -1) {
          const textBefore = sibling.value.slice(0, closeIdx);
          if (textBefore) innerNodes.push({ type: 'text', value: textBefore });
          afterClose = sibling.value.slice(closeIdx + 2);
          closeFound = true;
          break;
        }
      }
      innerNodes.push(sibling);
      j++;
    }

    if (!closeFound) continue;

    const innerHtml = innerNodes.map(nodeToHtmlString).join('');
    const replacement = [];
    if (beforeMarker) replacement.push({ type: 'text', value: beforeMarker });
    replacement.push({ type: 'html', value: `<span class="color-${color}">${innerHtml}</span>` });
    if (afterClose) replacement.push({ type: 'text', value: afterClose });

    children.splice(i, j - i + 1, ...replacement);
  }
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

  processColorSpansInParent(node);

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
