// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import tailwindcss from '@tailwindcss/vite';
import icon from 'astro-icon';
import react from '@astrojs/react';
import mdx from '@astrojs/mdx';
import keystatic from '@keystatic/astro';
import node from '@astrojs/node';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import remarkTextMarkers from './src/utils/remarkTextMarkers.mjs';
import remarkGithubAlerts from './src/utils/remarkGithubAlerts.mjs';
import remarkInclude from './src/utils/remarkInclude.mjs';
import { manualSidebar } from './src/config/manual-sidebar.mjs';
import remarkHeadingId from 'remark-heading-id';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  site: 'https://web.opensips.org',
  prefetch: false,
  adapter: node({ mode: 'standalone' }),
  markdown: {
    remarkPlugins: [remarkInclude, remarkGithubAlerts, remarkTextMarkers, remarkHeadingId],
  },
  security: {
    checkOrigin: false,
    allowedDomains: [{ hostname: 'web.opensips.org', protocol: 'https' }],
  },
  image: {
    service: { entrypoint: 'astro/assets/services/noop' },
  },
  integrations: [
    icon(),
    react(),
    keystatic(),
    starlight({
      pagefind: false,
      title: 'OpenSIPS',
      logo: { src: './src/assets/images/opensips.png', replacesTitle: true },
      customCss: ['./src/styles/global.css'],
      favicon: '/favicon.png',
      tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 4 },
      components: {
        Header: './src/components/overrides/Header.astro',
        Footer: './src/components/overrides/Footer.astro',
        ThemeSelect: './src/components/overrides/ThemeSelect.astro',
        PageTitle: './src/components/overrides/PageTitle.astro',
      },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/OpenSIPS/opensips' },
        { icon: 'linkedin', label: 'LinkedIn', href: 'https://www.linkedin.com/company/opensips/' },
        { icon: 'youtube', label: 'YouTube', href: 'https://www.youtube.com/@OpenSIPS' },
      ],
      sidebar: [
        {
          label: 'Documentation',
          collapsed: true,
          items: [
            {
              label: 'Manual',
              collapsed: true,
              items: manualSidebar(),
            },
            { label: 'Advanced Tutorials', slug: 'docs/tutorials' },
            { label: 'Tips & FAQ', slug: 'docs/tipsfaq' },
            {
              label: 'Version Migration',
              collapsed: true,
              items: [
                { label: 'Overview', slug: 'docs/migration' },
                { label: 'Upgrade from 4.0.0 to 4.1.0', slug: 'docs/migration-4-0-0-to-4-1-0' },
                { label: 'Upgrade from 3.6.0 to 4.0.0', slug: 'docs/migration-3-6-0-to-4-0-0' },
                { label: 'Upgrade from 3.5.0 to 3.6.0', slug: 'docs/migration-3-5-0-to-3-6-0' },
                { label: 'Upgrade from 3.4.0 to 3.5.0', slug: 'docs/migration-3-4-0-to-3-5-0' },
                { label: 'Upgrade from 3.3.0 to 3.4.0', slug: 'docs/migration-3-3-0-to-3-4-0' },
                { label: 'Upgrade from 3.2.0 to 3.3.0', slug: 'docs/migration-3-2-0-to-3-3-0' },
                { label: 'Upgrade from 3.1.0 to 3.2.0', slug: 'docs/migration-3-1-0-to-3-2-0' },
                { label: 'Upgrade from 3.0.0 to 3.1.0', slug: 'docs/migration-3-0-0-to-3-1-0' },
                { label: 'Upgrade from 2.4.0 to 3.0.0', slug: 'docs/migration-2-4-0-to-3-0-0' },
                { label: 'Upgrade from 2.3.0 to 2.4.0', slug: 'docs/migration-2-3-0-to-2-4-0' },
                { label: 'Upgrade from 2.2.0 to 2.3.0', slug: 'docs/migration-2-2-0-to-2-3-0' },
                { label: 'Upgrade from 2.1.0 to 2.2.0', slug: 'docs/migration-2-1-0-to-2-2-0' },
                { label: 'Upgrade from 1.11.0 to 2.1.0', slug: 'docs/migration-1-11-0-to-2-1-0' },
                { label: 'Upgrade from 1.10.0 to 1.11.0', slug: 'docs/migration-1-10-0-to-1-11-0' },
                { label: 'Upgrade from 1.9.0 to 1.10.0', slug: 'docs/migration-1-9-0-to-1-10-0' },
                { label: 'Upgrade from 1.8.0 to 1.9.0', slug: 'docs/migration-1-8-0-to-1-9-0' },
                { label: 'Upgrade from 1.7.0 to 1.8.0', slug: 'docs/migration-1-7-0-to-1-8-0' },
                { label: 'Upgrade from 1.6.4 to 1.7.0', slug: 'docs/migration-1-6-4-to-1-7-0' },
                { label: 'Upgrade from 1.6.3 to 1.6.4', slug: 'docs/migration-1-6-3-to-1-6-4' },
                { label: 'Upgrade from 1.6.2 to 1.6.3', slug: 'docs/migration-1-6-2-to-1-6-3' },
                { label: 'Upgrade from 1.5.x to 1.6.0/1/2', slug: 'docs/migration-1-5-to-1-6' },
                { label: 'Upgrade from 1.4.x to 1.5.x', slug: 'docs/migration-1-4-to-1-5' },
              ],
            },
            {
              label: 'Troubleshooting',
              collapsed: true,
              items: [
                { label: 'Overview', slug: 'docs/troubleshooting' },
                { label: 'OpenSIPS Does Not Start', slug: 'docs/troubleshooting-doesnotstart' },
                { label: 'OpenSIPS Crashes', slug: 'docs/troubleshooting-crash' },
                { label: 'Out Of Memory', slug: 'docs/troubleshooting-outofmem' },
                { label: 'Increasing Memory', slug: 'docs/troubleshooting-increasemem' },
              ],
            },
          ],
        },
      ],
    }),
    // Must come AFTER starlight() so astro-expressive-code (registered by Starlight) wraps MDX code blocks correctly.
    mdx({
      remarkPlugins: [remarkInclude, remarkGithubAlerts, remarkTextMarkers, remarkHeadingId],
    }),
  ],
  vite: {
    plugins: [tailwindcss()],
    resolve: {
      alias: {
        '~': path.resolve(__dirname, './src'),
      },
    },
    optimizeDeps: {
      include: ['react', 'react-dom', '@keystatic/core'],
    },
    build: {
      // keystatic-page chunk is 2.5 MB but only loads on /keystatic/* admin routes
      chunkSizeWarningLimit: 3000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return;
            if (id.includes('react-dom') || id.includes('react/')) return 'react-vendor';
            if (id.includes('@astrojs/starlight')) return 'starlight';
          },
        },
      },
    },
  },
});
