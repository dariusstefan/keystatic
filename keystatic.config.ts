import { config, fields, collection, singleton } from '@keystatic/core';

const mdxContent = () =>
  fields.mdx({
    label: 'Body',
    options: {
      image: {
        directory: 'public/images/docs',
        publicPath: '/images/docs/',
      },
    },
  });

export default config({
  storage: {
    kind: 'github',
    repo: { owner: 'dariusstefan', name: 'keystatic' },
  },

  ui: {
    brand: { name: 'opensips.org' },
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
