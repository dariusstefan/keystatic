const COLOR_MARKER_RE = /@@(red|green|blue|orange)\|(.+?)@@/g;

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

function splitColorMarkers(node, index, parent) {
  if (!parent || node.type !== 'text') return;

  const value = node.value;
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

function visit(node, parent = null) {
  if (!node || !Array.isArray(node.children)) return;

  for (let index = node.children.length - 1; index >= 0; index -= 1) {
    const child = node.children[index];
    visit(child, node);
    splitColorMarkers(child, index, node);
  }
}

export default function remarkTextMarkers() {
  return (tree) => visit(tree);
}
