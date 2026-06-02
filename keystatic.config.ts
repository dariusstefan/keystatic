import { createElement } from 'react';
import { config, collection, fields } from '@keystatic/core';

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
    tutorials: collection({
      label: 'Tutorials',
      slugField: 'title',
      path: 'src/content/docs/documentation/tutorials-*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: 'Title' } }),
        subtitle: fields.text({ label: 'Subtitle', validation: { isRequired: false } }),
        subtitleHref: fields.url({ label: 'Subtitle URL', validation: { isRequired: false } }),
        author: fields.text({ label: 'Author', validation: { isRequired: false } }),
        description: fields.text({ label: 'Description', multiline: true, validation: { isRequired: false } }),
        content: fields.mdx({ label: 'Content' }),
      },
    }),
  },
  singletons: {},
});
