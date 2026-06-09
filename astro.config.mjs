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
              label: 'Version Migration', slug: 'docs/migration'
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
            { label: 'OpenSIPS Tools', slug: 'docs/tools' },
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
