import { createElement } from 'react';
import { config, fields, collection, singleton, component } from '@keystatic/core';

const e = createElement;

const variantOptions = [
  { label: 'Note', value: 'note' },
  { label: 'Tip', value: 'tip' },
  { label: 'Caution', value: 'caution' },
  { label: 'Danger', value: 'danger' },
] as const;

const mdxComponents = {
  Badge: component({
    label: 'Badge',
    schema: {
      text: fields.text({ label: 'Text' }),
      variant: fields.select({
        label: 'Variant',
        options: variantOptions,
        defaultValue: 'note',
      }),
    },
    preview: ({ fields: f }: any) =>
      e('span', {
        style: { display: 'inline-block', padding: '1px 6px', borderRadius: 4, fontSize: '0.75rem', fontWeight: 600, background: '#555', color: '#fff' },
      }, f.text.value),
  }),

  Aside: component({
    label: 'Aside',
    schema: {
      type: fields.select({
        label: 'Type',
        options: variantOptions,
        defaultValue: 'note',
      }),
      children: fields.child({ kind: 'inline', placeholder: 'Content…' }),
    },
    preview: ({ fields: f }: any) =>
      e('div', {
        style: { borderLeft: '4px solid #888', paddingLeft: 12, margin: '8px 0', opacity: 0.85 },
      }, f.children.element),
  }),
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
