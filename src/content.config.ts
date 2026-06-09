import { defineCollection } from 'astro:content';
import { z } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
	docs: defineCollection({
		loader: docsLoader(),
		schema: docsSchema({
			extend: z.object({
				// Optional descriptive subtitle shown under the page title.
				subtitle: z.string().optional(),
				// Optional URL — when set, the subtitle renders as a link to it.
				subtitleHref: z.string().optional(),
				// Optional author attribution shown under the title.
				author: z.string().optional(),
			}),
		}),
	}),
};
