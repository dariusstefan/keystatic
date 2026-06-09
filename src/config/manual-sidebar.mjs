import fs from 'node:fs';
import path from 'node:path';

// Anchor to the project root (cwd at build time) rather than import.meta.url:
// this module gets bundled into the server build, where import.meta.url would
// point at the bundled output dir and the content reads below would all fail.
const CONTENT_ROOT = path.resolve(process.cwd(), 'src/content/docs/docs');
const MANUAL_DIR = new URL(`file://${CONTENT_ROOT}/manual/`);
const MODULES_DIR = new URL(`file://${CONTENT_ROOT}/modules/`);

// All modules of a version, as { stem, name, label }, keyed by repo stem — for
// the "Modules documentation" submenu. `stem` is the on-disk file stem (dots
// kept, e.g. rtp.io); `name` is the route slug (Astro strips dots → rtpio);
// `label` comes from each module's frontmatter title (minus a trailing
// " module"). Redirect stubs (sidebar.hidden) are skipped.
function moduleMap(slug) {
  const dir = new URL(`${slug}/`, MODULES_DIR);
  let files;
  try {
    files = fs.readdirSync(dir);
  } catch {
    return new Map();
  }
  const mods = new Map();
  for (const f of files) {
    if (!f.endsWith('.md')) continue;
    const stem = f.slice(0, -3);
    let title = stem;
    let hidden = false;
    try {
      const fm = fs.readFileSync(new URL(f, dir), 'utf8').match(/^---\n([\s\S]*?)\n---/);
      if (fm) {
        const t = fm[1].match(/^title:\s*["']?(.+?)["']?\s*$/m);
        if (t) title = t[1].trim();
        if (/hidden:\s*true/.test(fm[1])) hidden = true;
      }
    } catch {
      /* fall back to the file name */
    }
    if (hidden) continue;
    mods.set(stem, {
      stem,
      // Astro strips dots from the route slug (rtp.io.md → /…/rtpio), so match that.
      name: stem.replace(/\./g, ''),
      label: title.replace(/\s+module$/i, ''),
    });
  }
  return mods;
}

// Build the "Modules documentation" submenu for a version, grouped to mirror
// that version's Modules index page (manual/<slug>/modules.md): `##` headings
// are categories, `###` headings are subcategories, the bullet links are
// modules. Modules referenced in the index but with no page in this version are
// skipped (no dead links); any module not mentioned in the index is collected
// under "Other" so nothing reachable in the flat list disappears.
function groupedModuleItems(slug) {
  const byStem = moduleMap(slug);
  const item = (m) => ({ label: m.label, slug: `docs/modules/${slug}/${m.name}` });

  let md;
  try {
    md = fs.readFileSync(new URL(`${slug}/modules.md`, MANUAL_DIR), 'utf8');
  } catch {
    // No index page: fall back to a flat, alphabetised list.
    return [...byStem.values()].sort((a, b) => a.name.localeCompare(b.name)).map(item);
  }

  const linkRe = new RegExp(`^\\*\\s+\\[[^\\]]*\\]\\(/docs/modules/${slug}/([a-zA-Z0-9_.]+)\\)`);
  const categories = [];
  let cat = null;   // current `##` group
  let sub = null;   // current `###` group (within cat)
  const used = new Set();

  for (const line of md.split('\n')) {
    const h = line.match(/^(#{2,3})\s+(.+?)\s*$/);
    if (h) {
      if (h[1].length === 2) {
        cat = { label: h[2].trim(), collapsed: true, items: [] };
        categories.push(cat);
        sub = null;
      } else if (cat) {
        sub = { label: h[2].trim(), collapsed: true, items: [] };
        cat.items.push(sub);
      }
      continue;
    }
    const link = line.match(linkRe);
    if (link) {
      const mod = byStem.get(link[1]);
      const target = sub ?? cat;
      if (mod && target && !used.has(mod.stem)) {
        target.items.push(item(mod));
        used.add(mod.stem);
      }
    }
  }

  // Drop empty subcategories and categories left after skipping pageless modules.
  const groups = categories
    .map((c) => ({ ...c, items: c.items.filter((i) => !i.items || i.items.length) }))
    .filter((c) => c.items.length);

  // Modules never mentioned in the index → "Other".
  const leftovers = [...byStem.values()]
    .filter((m) => !used.has(m.stem))
    .sort((a, b) => a.name.localeCompare(b.name));
  if (leftovers.length) {
    groups.push({ label: 'Other', collapsed: true, items: leftovers.map(item) });
  }

  return groups;
}

// Build the Manual sidebar items for a single version from that version's index
// TOC (single source of truth), so the submenu mirrors the page's section
// grouping (Installation, Configuring, OpenSIPS scripting, …). The "Modules
// documentation" item becomes a submenu grouped like the Modules index page.
// Returns the array of items that sit directly under the "Manual" group. Falls
// back to a lone "Overview" link if the index can't be read.
export function manualSidebar(slug = 'devel') {
  const overview = { label: 'Overview', slug: `docs/manual/${slug}` };
  let md;
  try {
    md = fs.readFileSync(new URL(`${slug}/index.md`, MANUAL_DIR), 'utf8');
  } catch {
    return [overview];
  }

  const itemRe = new RegExp(`^\\s+\\*\\s+\\[(.+?)\\]\\((/docs/manual/${slug}/[^)#]+)\\)`);
  const modulesSlug = `docs/manual/${slug}/modules`;
  const groups = [];
  let current = null;
  for (const line of md.split('\n')) {
    const section = line.match(/^\*\s+\*\*(.+?)\*\*\s*$/);
    if (section) {
      current = { label: section[1].trim(), collapsed: true, items: [] };
      groups.push(current);
      continue;
    }
    const item = line.match(itemRe);
    if (item && current) {
      const label = item[1].trim();
      const itemSlug = item[2].replace(/^\//, '');
      if (itemSlug === modulesSlug) {
        // Expand "Modules documentation" into a submenu, grouped by category to
        // mirror the Modules index page, with an Overview link at the top.
        current.items.push({
          label,
          collapsed: true,
          items: [{ label: 'Overview', slug: itemSlug }, ...groupedModuleItems(slug)],
        });
      } else {
        current.items.push({ label, slug: itemSlug });
      }
    }
  }

  const nonEmpty = groups.filter((g) => g.items.length);
  return nonEmpty.length ? [overview, ...nonEmpty] : [overview];
}

// Every version slug that has manual content on disk (devel + the numbered
// versions), newest first by the order under the manual content dir.
export function manualVersionSlugs() {
  try {
    return fs
      .readdirSync(MANUAL_DIR, { withFileTypes: true })
      .filter((d) => d.isDirectory() && fs.existsSync(new URL(`${d.name}/index.md`, MANUAL_DIR)))
      .map((d) => d.name);
  } catch {
    return ['devel'];
  }
}

// Per-version Manual sidebars, as { [slug]: items[] } — consumed by the
// /manual-sidebar.json endpoint so the client can swap the Manual submenu to
// the active version (showing only that version's pages/modules, grouped per
// that version's own modules.md).
export function manualSidebarsAll() {
  const out = {};
  for (const slug of manualVersionSlugs()) out[slug] = manualSidebar(slug);
  return out;
}
