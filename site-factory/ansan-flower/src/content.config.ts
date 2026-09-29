import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    pageKey: z.string(),
    snapshotId: z.string(),
    sourceDraftKey: z.string(),
    sourceRecordId: z.string(),
    title: z.string(),
    description: z.string(),
    category: z.enum(['guide', 'places', 'occasions', 'flower-knowledge', 'order-help']),
    structureType: z.string(),
    region: z.string(),
    verifiedAt: z.coerce.date().optional(),
    sourceUrls: z.array(z.string().url()).default([]),
    draftStatus: z.enum(['approved', 'published']).default('approved'),
  }),
});

export const collections = { articles };
