import type { APIRoute, GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';
import { VERSIONS } from '~/config/module-versions';

export const prerender = true;

export const getStaticPaths: GetStaticPaths = () =>
  VERSIONS.filter((v) => !v.isLatest).map((v) => ({ params: { slug: v.slug } }));

export const GET: APIRoute = async ({ params }) => {
  const { slug } = params;
  const allDocs = await getCollection('docs');

  const modules = allDocs
    .filter((e) => {
      const p = e.id.split('/');
      return p[0] === 'modules' && p.length === 3 && p[1] === slug && !e.data.sidebar?.hidden;
    })
    .map((e) => ({ module: e.id.split('/')[2], title: e.data.title }))
    .sort((a, b) => a.module.localeCompare(b.module));

  return new Response(JSON.stringify(modules), {
    headers: { 'Content-Type': 'application/json' },
  });
};
