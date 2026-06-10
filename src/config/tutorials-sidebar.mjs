import fs from 'node:fs';
import path from 'node:path';

// Anchor to the project root (cwd at build time) rather than import.meta.url —
// same reasoning as manual-sidebar.mjs (this gets bundled into the server build).
const TUTORIALS_INDEX = path.resolve(process.cwd(), 'src/content/docs/docs/tutorials.md');

/**
 * "Advanced Tutorials" submenu: the latest version of each tutorial, in the
 * order of the Tutorials index page. Built by reading the internal links of
 * tutorials.md (`## [Label](/docs/tutorials-...)`) — the index only ever links
 * the un-suffixed (latest) variant of each tutorial, and older versions are
 * cross-linked from within the pages themselves. External links are skipped.
 *
 * Falls back to a plain link to the index when the content isn't generated yet.
 */
export function tutorialsSidebar() {
  let md;
  try {
    md = fs.readFileSync(TUTORIALS_INDEX, 'utf8');
  } catch {
    return [{ label: 'Overview', slug: 'docs/tutorials' }];
  }

  const items = [{ label: 'Overview', slug: 'docs/tutorials' }];
  for (const m of md.matchAll(/^#{2,3}\s+\[([^\]]+)\]\((\/docs\/[^)\s]+)\)/gm)) {
    const label = m[1].trim();
    const slug = m[2].replace(/^\//, '').replace(/\/$/, '');
    items.push({ label, slug });
  }
  return items;
}
