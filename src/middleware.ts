import { defineMiddleware } from 'astro:middleware';
import { getCollection } from 'astro:content';
import { VERSIONS } from './config/module-versions';

export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();

  if (response.status !== 404) return response;

  const parts = context.url.pathname.split('/').filter(Boolean);
  if (parts[0] !== 'modules' || parts.length !== 3) return response;

  const moduleName = parts[2];

  const allDocs = await getCollection('docs');
  const availableSlugs = new Set(
    allDocs
      .filter((e) => {
        const p = e.id.split('/');
        return p[0] === 'modules' && p.length === 3 && p[2] === moduleName;
      })
      .map((e) => e.id.split('/')[1])
  );

  const target = VERSIONS.find((v) => availableSlugs.has(v.slug));
  if (target) {
    return context.redirect(`/modules/${target.slug}/${moduleName}`, 302);
  }

  return response;
});
