import { visit } from 'unist-util-visit';

// Generate heading anchor ids for module pages by rule, so the source README.md
// files need carry no explicit {#id}. The id of a heading is a pure function of
// its text and its structural context (the H2 "guide" and H3 "section" it sits
// under), which is why the section titles are first normalised to canonical
// spellings upstream in the converter.
//
// Scheme (see also the converter that drops the markers):
//   * Admin Guide
//       - items under an indexed section  → <prefix>_<name>
//         (param/func/afunc/mi/event/stat/pv/sr)
//       - every other heading             → snake-cased slug of its title
//   * Developer Guide (and other API guides) → dev_<slug>  (kept distinct from
//     Admin so e.g. a Developer "Overview" never collides with the Admin one)
//   * Frequently Asked Questions             → faq_<slug>
//
// Only headings without an id already set (by remark-heading-id, for the rare
// page that still pins one) are touched; ids are de-duplicated within a page.

// Canonical indexed-section title (lower-cased) → item prefix.
const SECTION_PREFIX = {
  'exported parameters': 'param',
  'exported functions': 'func',
  'exported asynchronous functions': 'afunc',
  'exported mi functions': 'mi',
  'exported events': 'event',
  'exported pseudo-variables': 'pv',
  'exported statistics': 'stat',
  'exported status/report identifiers': 'sr',
};

// Collapse every run of non-alphanumerics to a single underscore and trim.
// Underscores already present in a symbol name (avp_print, db_url) survive.
// Section/prose slugs are lower-cased; symbol names keep their case (e.g. the
// MI command rate_cacher:addClient → mi_addClient) so they match the real
// identifier — except events, which are canonicalised to lower-case.
function sanitize(text) {
  return text.replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

export function slug(text) {
  return sanitize(text).toLowerCase();
}

// Extract the bare symbol name from a typed item heading, per section kind.
export function itemName(text, prefix) {
  let s = text.trim();
  switch (prefix) {
    case 'func':
    case 'afunc':
    case 'param':
      // name(args)  or  name (type)  → take the part before the first "("
      s = s.split('(')[0];
      break;
    case 'mi':
      // module:command  → drop the module qualifier; then drop any "(args)"
      if (s.includes(':')) s = s.slice(s.lastIndexOf(':') + 1);
      s = s.split('(')[0];
      break;
    case 'pv':
      // $name / $(name(args)[idx]) / $tm.branch.uri[] → inner identifier path
      s = s.replace(/^\$\(?/, '').split(/[([]/)[0];
      break;
    // event / stat: the heading already is the bare name
  }
  s = sanitize(s);
  return prefix === 'event' ? s.toLowerCase() : s;
}

// Visible text of a heading, taken from the RAW source via position offsets.
//
// We must NOT walk the child nodes: Starlight enables remark-directive, which
// parses a heading like "dialog:list" into a text node "dialog" + a textDirective
// ":list" — so reading the children would yield just "dialog" and every MI
// command would collapse to mi_dialog. Slicing the source sidesteps every such
// inline transform. Markdown emphasis/code/link syntax is then stripped to match
// the converter's own heading-text normalisation.
function headingText(node, source) {
  if (!node.position || source == null) {
    // Fallback: best-effort from child text nodes.
    let out = '';
    visit(node, (n) => {
      if (n.type === 'text' || n.type === 'inlineCode') out += n.value;
    });
    return out.trim();
  }
  let raw = source.slice(node.position.start.offset, node.position.end.offset);
  raw = raw
    .replace(/^#{1,6}[ \t]+/, '')
    .replace(/[ \t]*\{#[^}]+\}[ \t]*$/, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[`*]/g, '');
  return raw.trim();
}

// Developer-Guide function sections: their items get a dev_ prefix so they read
// as the C/script API and never collide with Admin-Guide script functions.
const DEV_FUNCTION_SECTIONS = new Set(['available functions', 'api functions', 'functions']);

function isDeveloperGuide(guide) {
  return !!guide && /^developer('s)? guide$/i.test(guide.trim());
}

// Compute the id for one heading given the running guide + section context.
// Returns null when the heading carries no usable text.
//
// Admin-Guide leaf items under a canonical "Exported …" section get a typed
// prefix; Developer-Guide function items get dev_<name>; everything else is a
// plain slug (repeated prose titles are separated by the plugin's de-dup).
export function computeId(depth, text, ctx) {
  if (!text) return null;

  if (depth >= 4 && ctx.section) {
    const prefix = SECTION_PREFIX[ctx.section.toLowerCase()];
    if (prefix) {
      const name = itemName(text, prefix);
      return name ? `${prefix}_${name}` : null;
    }
    if (isDeveloperGuide(ctx.guide) && DEV_FUNCTION_SECTIONS.has(ctx.section.toLowerCase())) {
      const name = itemName(text, 'func');
      return name ? `dev_${name}` : null;
    }
  }

  return slug(text) || null;
}

export default function remarkModuleAnchors() {
  return (tree, file) => {
    const path = file?.path || file?.history?.[0] || '';
    if (!path.includes('/docs/modules/')) return;

    const source = typeof file?.value === 'string' ? file.value : String(file?.value ?? '');
    const ctx = { guide: null, section: null };
    const used = new Set();

    visit(tree, 'heading', (node) => {
      const depth = node.depth;
      const text = headingText(node, source);

      if (depth === 2) {
        ctx.guide = text;
        ctx.section = null;
      } else if (depth === 3) {
        ctx.section = text;
      }

      const data = node.data || (node.data = {});
      const props = data.hProperties || (data.hProperties = {});
      if (typeof props.id === 'string' && props.id) {
        used.add(props.id);
        return; // explicit id already set elsewhere — leave it
      }

      let id = computeId(depth, text, ctx);
      if (!id) return;

      // De-duplicate within the page (invalid HTML otherwise).
      if (used.has(id)) {
        let n = 2;
        while (used.has(`${id}_${n}`)) n++;
        id = `${id}_${n}`;
      }
      used.add(id);
      data.id = id;
      props.id = id;
    });
  };
}
