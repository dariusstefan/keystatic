import { createElement } from 'react';
import { config, fields, collection, singleton } from '@keystatic/core';
const Aside = ({ type, children }: { type?: string; children?: unknown }) =>
  createElement('aside', { 'data-type': type ?? 'note' }, children as any);

const Badge = ({ text, variant }: { text?: string; variant?: string }) =>
  createElement('span', { 'data-variant': variant ?? 'default' }, text);

const mdxContent = () =>
  fields.mdx({
    label: 'Body',
    options: {
      image: {
        directory: 'public/images/docs',
        publicPath: '/images/docs/',
      },
    },
    components: { Aside, Badge },
  });

export default config({
  storage: {
    kind: 'github',
    repo: { owner: 'dariusstefan', name: 'keystatic' },
  },

  ui: {
    brand: {
      name: ' ',
      mark: ({ colorScheme }: { colorScheme: 'light' | 'dark' }) =>
        createElement('img', {
          src: colorScheme === 'dark' ? '/opensips-dark.png' : '/opensips-logo.png',
          alt: 'OpenSIPS',
          height: 24,
        }),
    },
  },

  collections: {
    about: collection({
      label: 'About Sub-pages',
      path: 'src/content/docs/about/*',
      format: { contentField: 'content', data: 'yaml' },
      entryLayout: 'content',
      slugField: 'title',
      schema: {
        title: fields.slug({
          name: { label: 'Title', validation: { length: { min: 1 } } },
        }),
        description: fields.text({ label: 'Description', multiline: true }),
        content: mdxContent(),
      },
    }),
  },

  singletons: {
    aboutPage: singleton({
      label: 'About',
      path: 'src/content/docs/about',
      format: { contentField: 'content', data: 'yaml' },
      entryLayout: 'content',
      schema: {
        title: fields.text({ label: 'Title', validation: { length: { min: 1 } } }),
        description: fields.text({ label: 'Description', multiline: true }),
        content: mdxContent(),
      },
    }),

    contact: singleton({
      label: 'Contact',
      path: 'src/content/docs/contact',
      format: { contentField: 'content', data: 'yaml' },
      entryLayout: 'content',
      schema: {
        title: fields.text({ label: 'Title', validation: { length: { min: 1 } } }),
        description: fields.text({ label: 'Description', multiline: true }),
        content: mdxContent(),
      },
    }),

    development: singleton({
      label: 'Development',
      path: 'src/content/docs/development',
      format: { contentField: 'content', data: 'yaml' },
      entryLayout: 'content',
      schema: {
        title: fields.text({ label: 'Title', validation: { length: { min: 1 } } }),
        description: fields.text({ label: 'Description', multiline: true }),
        content: mdxContent(),
      },
    }),

    downloads: singleton({
      label: 'Downloads',
      path: 'src/content/docs/downloads',
      format: { contentField: 'content', data: 'yaml' },
      entryLayout: 'content',
      schema: {
        title: fields.text({ label: 'Title', validation: { length: { min: 1 } } }),
        description: fields.text({ label: 'Description', multiline: true }),
        content: mdxContent(),
      },
    }),

    training: singleton({
      label: 'Training',
      path: 'src/content/docs/training',
      format: { contentField: 'content', data: 'yaml' },
      entryLayout: 'content',
      schema: {
        title: fields.text({ label: 'Title', validation: { length: { min: 1 } } }),
        description: fields.text({ label: 'Description', multiline: true }),
        content: mdxContent(),
      },
    }),
  },
});
