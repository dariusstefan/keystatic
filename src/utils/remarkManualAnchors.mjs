import { visit } from 'unist-util-visit';

// Generate heading anchor ids for the Manual reference pages by rule, so their
// source carries no explicit {#id} (mirrors remarkModuleAnchors for modules).
//
// Unlike modules, the rule is keyed on the PAGE: each reference page lists a
// single kind of item (core parameters / pseudo-variables / transformations /
// core functions / MI commands), so the item type is known from the filename
// and no section tracking is needed. Pages without a rule are left to Astro's
// default github-slug.

// Sanitise a symbol name, preserving the chars that occur in OpenSIPS manual
// identifiers (`.` in $auth.resp / {s.len}, `-` in {sdp.stream-delete}).
function clean(s) {
  return s.replace(/[^A-Za-z0-9._-]+/g, '_').replace(/^_+|_+$/g, '');
}

// Lower-case underscore slug, for the few group/section headings on these pages.
function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
}

// page basename (no .md) → (heading text) → id | null
const PAGE_RULES = {
  // Each heading is a parameter name; group headings ("Core Keywords") fall back
  // to a slug.
  'script-coreparameters': (t) =>
    /^[A-Za-z_][\w.-]*$/.test(t.trim()) ? clean(t.trim()) : slug(t),

  // name(args) → name
  'script-corefunctions': (t) => clean(t.split('(')[0]) || null,

  // {s.substr,offset,length} → s.substr ; non-{} headings are sections → slug
  'script-tran': (t) => {
    t = t.trim();
    if (!t.startsWith('{')) return slug(t) || null;
    return clean(t.replace(/^\{|\}$/g, '').split(',')[0].trim()) || null;
  },

  // "Auth realm - $ar" → ar ; section headings (no $) → slug
  'script-corevar': (t) => {
    const m = t.match(/\$\(?\{?([A-Za-z0-9_.]+)/);
    return m ? clean(m[1]) : (slug(t) || null);
  },

  // "blacklists:list" → blacklists_list ; "log_level [level] [pid]" → log_level
  // Keep BOTH parts of a module:command, turning ":" into "_".
  'interface-coremi': (t) => {
    const cmd = t.trim().split(/[\s[]/)[0].replace(/:/g, '_');
    return clean(cmd) || null;
  },

  // Each heading is a statistic / route name; id == the name (hyphens kept).
  'interface-corestatistics': (t) => clean(t) || null,
  'script-routes': (t) => clean(t) || null,

  // The heading is a human description ("Threshold limit exceeded"); the anchor
  // is the event constant, which appears as "**Event**: E_CORE_…" just below.
  'interface-coreevents': (t, ctx) => {
    if (ctx && ctx.source && ctx.node && ctx.node.position) {
      const after = ctx.source.slice(
        ctx.node.position.end.offset,
        ctx.node.position.end.offset + 400,
      );
      const m = after.match(/\*\*Event\*\*:\s*([A-Za-z0-9_]+)/);
      if (m) return m[1];
    }
    return slug(t) || null;
  },
};

// Hand-curated per-page heading-text → forced id overrides, for headings whose
// auto-generated id is undesirable (kept in lock-step with manual_anchors.py).
const OVERRIDES = {
  'script-coreparameters': {
    'memdump | mem_dump': 'memdump',
    'memlog | mem_log': 'memlog',
  },
  'install-download': {
    'Packages download - preferred method': 'packages',
    'GIT download': 'git',
  },
  'script-async': {
    'Serial asynchronous operations, async()': 'async',
    'Parallel asynchronous operations, launch()': 'launch',
    'List of async functions': 'async_functions',
    'Limitations': 'async_limitations',
    'Allowed Routes': 'async_routes',
  },
};

// Visible heading text from RAW source via position offsets — never walk child
// nodes: Starlight's remark-directive turns "blacklists:list" into text
// "blacklists" + a directive, which would corrupt the id.
function headingText(node, source) {
  if (!node.position || source == null) {
    let out = '';
    visit(node, (n) => {
      if (n.type === 'text' || n.type === 'inlineCode') out += n.value;
    });
    return out.trim();
  }
  return source
    .slice(node.position.start.offset, node.position.end.offset)
    .replace(/^#{1,6}[ \t]+/, '')
    .replace(/[ \t]*\{#[^}]+\}[ \t]*$/, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[`*]/g, '')
    .trim();
}

export default function remarkManualAnchors() {
  return (tree, file) => {
    const path = file?.path || file?.history?.[0] || '';
    const m = path.match(/\/docs\/manual\/[^/]+\/([^/]+)\.md$/);
    if (!m) return;
    const rule = PAGE_RULES[m[1]];
    const overrides = OVERRIDES[m[1]];
    if (!rule && !overrides) return; // prose / unhandled page → Astro's default slug

    const source = typeof file?.value === 'string' ? file.value : String(file?.value ?? '');
    const used = new Set();

    visit(tree, 'heading', (node) => {
      const data = node.data || (node.data = {});
      const props = data.hProperties || (data.hProperties = {});
      if (typeof props.id === 'string' && props.id) {
        used.add(props.id);
        return; // explicit id pinned elsewhere — keep it
      }
      const text = headingText(node, source);
      if (!text) return;
      // A forced override wins; otherwise the page rule (if any). On an
      // override-only page, non-overridden headings fall through to Astro slugs.
      let id = overrides && overrides[text];
      if (!id) id = rule ? rule(text, { source, node }) : null;
      if (!id) return;
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

export { PAGE_RULES, clean, slug };
