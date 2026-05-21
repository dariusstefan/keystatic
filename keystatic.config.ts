import { createElement } from 'react';
import { config, fields, collection, singleton } from '@keystatic/core';

const e = createElement;

const mdxComponents = {
  // HTML elements used as raw JSX in MDX
  span:   ({ children, ...p }: any) => e('span', p, children),
  em:     ({ children }: any) => e('em', null, children),
  strong: ({ children }: any) => e('strong', null, children),
  // Starlight content components
  Aside: ({ type, children }: any) => e('div', { 'data-type': type ?? 'note' }, children),
  Badge: ({ text, variant }: any) => e('span', { 'data-variant': variant }, text),
};

const mdxContent = () =>
  fields.mdx({
    label: 'Body',
    options: {
      image: {
        directory: 'public/images/docs',
        publicPath: '/images/docs/',
      },
    },
    components: mdxComponents,
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
