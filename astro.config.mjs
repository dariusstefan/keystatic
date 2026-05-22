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

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  site: 'https://www.opensips.org',
  adapter: node({ mode: 'standalone' }),
  markdown: {
    remarkPlugins: [remarkTextMarkers],
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
      title: 'OpenSIPS',
      logo: { src: './src/assets/images/opensips.png', replacesTitle: true },
      customCss: ['./src/styles/global.css'],
      favicon: '/favicon.png',
      components: {
        Header: './src/components/overrides/Header.astro',
        Footer: './src/components/overrides/Footer.astro',
        ThemeSelect: './src/components/overrides/ThemeSelect.astro',
      },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/OpenSIPS/opensips' },
        { icon: 'linkedin', label: 'LinkedIn', href: 'https://www.linkedin.com/company/opensips/' },
        { icon: 'youtube', label: 'YouTube', href: 'https://www.youtube.com/@OpenSIPS' },
      ],
      sidebar: [
        {
          label: 'About',
          items: [
            { label: 'About OpenSIPS', slug: 'about' },
            { label: "Who's using OpenSIPS", slug: 'about/whos-using' },
            { label: 'Features', slug: 'about/features' },
            { label: 'Versions', slug: 'about/versions' },
            { label: 'Related software', slug: 'about/related-software' },
            { label: 'Contact', slug: 'contact' },
            { label: 'Core Variables', slug: 'about/core-variables' },
          ],
        },
        {
          label: 'Downloads',
          items: [{ label: 'Get OpenSIPS', slug: 'downloads' }],
        },
        {
          label: 'Development',
          items: [{ label: 'Overview', slug: 'development' }],
          collapsed: true,
        },
        {
          label: 'Training',
          items: [{ label: 'Trainings', slug: 'training' }],
        },
      ],
    }),
    // Must come AFTER starlight() so astro-expressive-code (registered by Starlight) wraps MDX code blocks correctly.
    mdx({
      remarkPlugins: [remarkTextMarkers],
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
