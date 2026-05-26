import { createElement } from 'react';
import { config } from '@keystatic/core';

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

  collections: {},
  singletons: {},
});
