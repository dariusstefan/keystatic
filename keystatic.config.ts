import { createElement } from 'react';
import { config, collection, fields } from '@keystatic/core';

export default config({
  storage: {
    kind: 'github',
    repo: { owner: 'dariusstefan', name: 'opensips-docs' },
  },

  collections: {
    docs: collection({
      label: 'Docs',
      slugField: 'title',
      path: 'docs/*',                          // ← matches opensips-docs/docs/<slug>.md
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: 'Title' } }),
        subtitle: fields.text({ label: 'Subtitle', validation: { isRequired: false } }),
        subtitleHref: fields.url({ label: 'Subtitle URL', validation: { isRequired: false } }),
        author: fields.text({ label: 'Author', validation: { isRequired: false } }),
        description: fields.text({ label: 'Description', multiline: true, validation: { isRequired: false } }),
        content: fields.mdx({ label: 'Content', extension: 'md' }),   // flat docs are .md
      },
    }),
  },
  singletons: {},
});
