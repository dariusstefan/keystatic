import type { APIRoute } from 'astro';
// @ts-expect-error — plain .mjs config helper, no types
import { manualSidebarsAll } from '~/config/manual-sidebar.mjs';

// Static at build time: a { [versionSlug]: sidebarItems[] } map so the client
// can rebuild the Manual submenu for the active version (PageTitle.astro).
export const prerender = true;

export const GET: APIRoute = () =>
  new Response(JSON.stringify(manualSidebarsAll()), {
    headers: { 'content-type': 'application/json' },
  });
